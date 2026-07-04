from __future__ import annotations

import heapq
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple, Any, Set
from functools import lru_cache

import pandas as pd
from data_models import PatientModel, DrugModel, RuleModel, validate_rows
from validation import sanitize_string, check_xss_attempt, check_sql_injection, validate_input_safe

# -----------------
# Logging utilities
# -----------------

def get_logger(name: str = "drug_conflict_detection") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler()
        fmt = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")
        ch.setFormatter(fmt)
        logger.addHandler(ch)
    return logger

logger = get_logger()

# -----------------
# Data utilities
# -----------------

def _read_raw(path: Path | str) -> List[dict]:
    """Read CSV file - sanitization not needed for trusted CSV files"""
    df = pd.read_csv(Path(path))
    return df.to_dict(orient="records")

def load_patients(path: Path | str) -> List[dict]:
    raw = _read_raw(path)
    validated, errors = validate_rows(raw, PatientModel)
    if errors:
        for idx, err in errors:
            logger.warning(f"Patient row {idx} failed validation: {err}")
    return [m.model_dump() for m in validated]

def load_drugs(path: Path | str) -> List[dict]:
    raw = _read_raw(path)
    validated, errors = validate_rows(raw, DrugModel)
    if errors:
        for idx, err in errors:
            logger.warning(f"Drug row {idx} failed validation: {err}")
    return [m.model_dump() for m in validated]

def load_rules(path: Path | str) -> List[dict]:
    raw = _read_raw(path)
    validated, errors = validate_rows(raw, RuleModel)
    if errors:
        for idx, err in errors:
            logger.warning(f"Rule row {idx} failed validation: {err}")
    return [m.model_dump() for m in validated]

# -----------------
# Severity utilities
# -----------------

SEVERITY_SCORES = {
    "Major": 3,
    "Moderate": 2,
    "Minor": 1,
}

def severity_to_score(severity: str) -> int:
    return SEVERITY_SCORES.get(str(severity).title(), 0)

# -----------------
# Knowledge base
# -----------------

def _normalize_key(*parts: str) -> Tuple[str, ...]:
    return tuple(p.strip().lower() for p in parts)

@dataclass(frozen=True)
class Rule:
    rtype: str  # 'drug-drug' | 'drug-condition'
    item_a: str
    item_b: str
    severity: str
    recommendation: str
    notes: str | None = None

    @property
    def key(self) -> Tuple[str, str, str]:
        if self.rtype == "drug-drug":
            a, b = sorted([self.item_a, self.item_b], key=lambda s: s.lower())
            return (self.rtype, a.lower(), b.lower())
        else:
            # Keep condition first for drug-condition
            return (self.rtype, self.item_a.lower(), self.item_b.lower())


def build_rules_kb(rules_rows: Iterable[dict]) -> Dict[Tuple[str, str, str], Rule]:
    kb: Dict[Tuple[str, str, str], Rule] = {}
    for r in rules_rows:
        rule = Rule(
            rtype=str(r.get("type", "")).strip(),
            item_a=str(r.get("item_a", "")).strip(),
            item_b=str(r.get("item_b", "")).strip(),
            severity=str(r.get("severity", "")).strip().title(),
            recommendation=str(r.get("recommendation", "")).strip(),
            notes=str(r.get("notes", "")).strip() or None,
        )
        kb[rule.key] = rule
    return kb

# -----------------
# Best-First Search (BFS) / A* Conflict Detection (optimized)
# -----------------

@dataclass
class Conflict:
    rtype: str
    item_a: str
    item_b: str
    severity: str
    recommendation: str
    score: int


@dataclass(frozen=True)
class SearchState:
    """Represents a state in the conflict search space.
    
    State = set of active conflicts detected so far in the prescription.
    """
    prescription: frozenset[str]  # drugs in prescription
    conditions: frozenset[str]    # patient conditions/allergies
    detected_conflicts: frozenset[Tuple[str, str, str]]  # rule keys already found
    
    def __lt__(self, other):
        # Tie-breaking for heapq (not priority, just stable ordering)
        return len(self.detected_conflicts) < len(other.detected_conflicts)


def make_condition_tokens(conditions: Iterable[str], allergies: Iterable[str] | None = None) -> List[str]:
    tokens = [str(c).strip() for c in conditions if str(c).strip()]
    if allergies:
        # Guard against scalar (float/str)
        if isinstance(allergies, (str, float, int)):
            allergies = [allergies]
        for a in allergies:
            a = str(a).strip()
            if a and a.lower() != "none":
                tokens.append(f"{a}Allergy")
    return tokens


def _compute_heuristic(state: SearchState, kb: Dict[Tuple[str, str, str], Rule]) -> int:
    """Heuristic: sum of severity scores of detected conflicts (higher = worse state)."""
    total = 0
    for key in state.detected_conflicts:
        rule = kb.get(key)
        if rule:
            total += severity_to_score(rule.severity)
    return total


def _precompute_candidate_keys(drugs_set: frozenset[str], cond_set: frozenset[str], kb: Dict[Tuple[str, str, str], Rule]) -> List[Tuple[str, str, str]]:
    """Precompute all possible conflict keys for this prescription/condition set once.

    This replaces repeated nested pair generation inside each expansion step.
    """
    drugs = list(drugs_set)
    conditions = list(cond_set)
    candidate: List[Tuple[str, str, str]] = []
    # drug-drug
    for i in range(len(drugs)):
        di = drugs[i]
        for j in range(i + 1, len(drugs)):
            dj = drugs[j]
            a, b = sorted([di, dj], key=lambda s: s.lower())
            key = ("drug-drug", a.lower(), b.lower())
            if key in kb:
                candidate.append(key)
    # drug-condition
    for c in conditions:
        for d in drugs:
            key = ("drug-condition", c.lower(), d.lower())
            if key in kb:
                candidate.append(key)
    return candidate


def _expand_neighbors(state: SearchState, all_candidate_keys: List[Tuple[str, str, str]], kb: Dict[Tuple[str, str, str], Rule]) -> List[Tuple[SearchState, Tuple[str, str, str], int]]:
    """Generate neighbor states by adding one yet-undiscovered conflict from precomputed candidates."""
    neighbors: List[Tuple[SearchState, Tuple[str, str, str], int]] = []
    remaining = [k for k in all_candidate_keys if k not in state.detected_conflicts]
    for key in remaining:
        rule = kb[key]
        score = severity_to_score(rule.severity)
        new_state = SearchState(
            prescription=state.prescription,
            conditions=state.conditions,
            detected_conflicts=state.detected_conflicts | {key}
        )
        neighbors.append((new_state, key, score))
    return neighbors


_MEMO_CACHE: Dict[Tuple[frozenset[str], frozenset[str], int], List[Conflict]] = {}
_MEMO_STATS = {"hits": 0, "misses": 0}


def get_conflicts_cached(prescription: List[str], conditions: List[str], kb: Dict[Tuple[str, str, str], Rule]) -> List[Conflict]:
    """Public wrapper providing memoized conflict detection.

    Cache key includes id(kb) so rebuilding the knowledge base invalidates entries.
    Returns a copy of cached list to avoid accidental mutation.
    """
    drugs_set = frozenset(d.strip() for d in prescription if d and str(d).strip())
    cond_set = frozenset(c.strip() for c in conditions if c and str(c).strip())
    key = (drugs_set, cond_set, id(kb))
    cached = _MEMO_CACHE.get(key)
    if cached is not None:
        _MEMO_STATS["hits"] += 1
        return [Conflict(**c.__dict__) for c in cached]
    _MEMO_STATS["misses"] += 1
    result = bfs_conflicts(prescription, conditions, kb)
    _MEMO_CACHE[key] = [Conflict(**c.__dict__) for c in result]
    return result


def bfs_conflicts(prescription: List[str], conditions: List[str], kb: Dict[Tuple[str, str, str], Rule]) -> List[Conflict]:
    """
    True Best-First Search (A*-style) over conflict discovery space.
    
    Goal: explore the prescription systematically, prioritizing discovery of high-severity conflicts first.
    State: set of conflicts detected so far
    Heuristic: cumulative severity score (higher = more critical state to explore)
    Neighbors: adding one more detectable conflict to current state
    
    This ensures Major conflicts are surfaced and reported before Minor ones.
    """
    drugs_set = frozenset(d.strip() for d in prescription if d and str(d).strip())
    cond_set = frozenset(c.strip() for c in conditions if c and str(c).strip())
    
    if not drugs_set:
        return []
    
    # Precompute candidate keys for optimization
    candidate_keys = _precompute_candidate_keys(drugs_set, cond_set, kb)

    # Initial state: no conflicts detected yet
    initial = SearchState(prescription=drugs_set, conditions=cond_set, detected_conflicts=frozenset())
    
    # Priority queue: (priority, counter, state, path_score)
    # Priority = -(heuristic + path_cost) for max-heap behavior (explore worst states first)
    heap: List[Tuple[int, int, SearchState]] = []
    visited: set[frozenset[Tuple[str, str, str]]] = set()
    counter = 0
    
    heapq.heappush(heap, (0, counter, initial))
    counter += 1
    
    all_conflicts: Dict[Tuple[str, str, str], Rule] = {}
    
    while heap:
        _, _, state = heapq.heappop(heap)
        
        # Skip if we've seen this conflict set
        if state.detected_conflicts in visited:
            continue
        visited.add(state.detected_conflicts)
        
        # Record conflicts from this state
        for key in state.detected_conflicts:
            if key not in all_conflicts:
                all_conflicts[key] = kb[key]
        
        # Expand neighbors using precomputed candidate keys
        neighbors = _expand_neighbors(state, candidate_keys, kb)
        
        for new_state, new_key, conflict_score in neighbors:
            if new_state.detected_conflicts not in visited:
                # Priority: negative heuristic (explore high-severity paths first)
                h = _compute_heuristic(new_state, kb)
                heapq.heappush(heap, (-h, counter, new_state))
                counter += 1
    
    # Convert to conflict list sorted by severity
    results: List[Conflict] = []
    for key, rule in all_conflicts.items():
        results.append(
            Conflict(
                rtype=rule.rtype,
                item_a=rule.item_a,
                item_b=rule.item_b,
                severity=rule.severity,
                recommendation=rule.recommendation,
                score=severity_to_score(rule.severity),
            )
        )
    
    # Sort by severity descending (Major first)
    results.sort(key=lambda c: (-c.score, c.item_a, c.item_b))
    
    return results


def conflicts_to_frame(conflicts: List[dict | Conflict]) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for c in conflicts:
        if isinstance(c, Conflict):
            rows.append({
                "type": c.rtype,
                "item_a": c.item_a,
                "item_b": c.item_b,
                "severity": c.severity,
                "score": c.score,
                "recommendation": c.recommendation,
            })
        else:
            rows.append(dict(c))
    return pd.DataFrame(rows)

# -----------------
# Optional plotting
# -----------------

def plot_severity_distribution(conflicts_df: pd.DataFrame):
    """Plot a simple severity distribution bar chart.

    Optional helper migrated from visualization.py to keep code centralized.
    Uses lazy imports so normal simulation runs avoid importing heavy libs.
    """
    if conflicts_df.empty:
        print("No conflicts to plot.")
        return
    try:
        import matplotlib.pyplot as plt  # type: ignore
        import seaborn as sns  # type: ignore
    except ImportError as e:
        print(f"Plot dependencies missing: {e}. Install matplotlib and seaborn.")
        return
    order = ["Major", "Moderate", "Minor"]
    counts = conflicts_df["severity"].value_counts()
    data = pd.DataFrame({"severity": counts.index, "count": counts.values})
    data = data.set_index("severity").reindex(order).fillna(0).reset_index()
    plt.figure(figsize=(6, 4))
    sns.barplot(x="severity", y="count", data=data, order=order, palette="Reds")
    plt.title("Conflict Severity Distribution")
    plt.xlabel("Severity")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.show()
