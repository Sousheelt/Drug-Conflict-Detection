from __future__ import annotations

from typing import List, Dict, Any, Tuple
import random

from mesa import Agent

from utils import bfs_conflicts, build_rules_kb, make_condition_tokens, severity_to_score, logger


class PatientAgent(Agent):
    def __init__(self, model, patient_id: str, name: str, conditions: List[str], allergies: List[str]):
        super().__init__(patient_id, model)
        self.patient_id = patient_id
        self.name = name
        self.conditions = conditions
        self.allergies = allergies
        self.prescription: List[str] = []

    def step(self):
        # Patients do not act independently in this simple simulation.
        pass


class DoctorAgent(Agent):
    def __init__(self, model, drugs_catalog: List[Dict[str, Any]], mode: str = "smart"):
        super().__init__("doctor", model)
        self.drugs_catalog = drugs_catalog
        self.mode = mode  # "smart" or "conflict-prone"

    def prescribe(self, patient: PatientAgent) -> List[str]:
        if self.mode == "smart":
            return self._prescribe_smart(patient)
        else:
            return self._prescribe_conflict_prone(patient)

    def _prescribe_smart(self, patient: PatientAgent) -> List[str]:
        """Smart prescribing: avoid conflicts, use replacements, check allergies"""
        chosen: List[str] = []
        condition_tokens = make_condition_tokens(patient.conditions, patient.allergies)
        
        def has_conflict(drug: str, current_rx: List[str]) -> Tuple[bool, int]:
            """Check if drug creates conflicts and return risk score"""
            risk = 0
            dl = drug.lower()
            kb = self.model.rule_engine.kb
            
            # Check drug-drug conflicts
            for existing in current_rx:
                a, b = sorted([existing.lower(), dl])
                key = ("drug-drug", a, b)
                rule = kb.get(key)
                if rule:
                    risk += severity_to_score(rule.severity)
            
            # Check drug-condition conflicts
            for ct in condition_tokens:
                key = ("drug-condition", ct.lower(), dl)
                rule = kb.get(key)
                if rule:
                    risk += severity_to_score(rule.severity)
            
            return risk > 0, risk
        
        def is_allergic(drug: str) -> bool:
            """Check if patient is allergic to drug"""
            drug_lower = drug.lower()
            return any(
                drug_lower in str(a).lower() or str(a).lower() in drug_lower
                for a in patient.allergies
                if str(a).lower() not in ['none', 'nan', '']
            )
        
        # Prescribe for each condition
        for cond in patient.conditions:
            candidates = [
                r for r in self.drugs_catalog 
                if str(r.get("condition", "")).strip().lower() == str(cond).strip().lower()
            ]
            
            if not candidates:
                continue
            
            # Try to find a conflict-free drug
            best_drug = None
            best_row = None
            
            # First pass: try drugs without conflicts
            for row in candidates:
                drug = str(row.get("drug", "")).strip()
                if not drug or drug in chosen:
                    continue
                
                # Skip if allergic
                if is_allergic(drug):
                    continue
                
                has_conf, risk = has_conflict(drug, chosen)
                
                if not has_conf:
                    best_drug = drug
                    best_row = row
                    break
            
            # Second pass: if all drugs have conflicts, try replacements
            if best_drug is None:
                for row in candidates:
                    drug = str(row.get("drug", "")).strip()
                    if not drug or drug in chosen or is_allergic(drug):
                        continue
                    
                    # Check if this drug has conflict-free replacements
                    replacements = row.get("replacements", [])
                    if replacements and isinstance(replacements, list):
                        for replacement in replacements:
                            replacement = str(replacement).strip()
                            if not replacement or replacement in chosen:
                                continue
                            
                            if is_allergic(replacement):
                                continue
                            
                            has_conf, _ = has_conflict(replacement, chosen)
                            if not has_conf:
                                best_drug = replacement
                                best_row = row
                                break
                    
                    if best_drug:
                        break
            
            # Third pass: if still no conflict-free drug, SKIP this condition
            # Smart doctor will NOT prescribe anything that creates conflicts
            if best_drug is None:
                logger.warning(f"Smart Doctor: No conflict-free drug found for {patient.name}'s {cond}. Skipping this condition.")
                continue
            
            chosen.append(best_drug)
        
        logger.info(f"Smart Doctor prescribed for {patient.name}: {chosen} (conflict-free)")
        return chosen
    
    def _prescribe_conflict_prone(self, patient: PatientAgent) -> List[str]:
        """Conflict-prone prescribing: intentionally creates conflicts for demonstration"""
        chosen: List[str] = []
        condition_tokens = make_condition_tokens(patient.conditions, patient.allergies)

        def predicted_risk(drug: str, current_rx: List[str]) -> int:
            risk = 0
            dl = drug.lower()
            kb = self.model.rule_engine.kb
            for existing in current_rx:
                a, b = sorted([existing.lower(), dl])
                key = ("drug-drug", a, b)
                rule = kb.get(key)
                if rule:
                    risk += severity_to_score(rule.severity)
            for ct in condition_tokens:
                key = ("drug-condition", ct.lower(), dl)
                rule = kb.get(key)
                if rule:
                    risk += severity_to_score(rule.severity)
            return risk

        # Choose drugs that CREATE conflicts (for demonstration purposes)
        for cond in patient.conditions:
            candidates = [r for r in self.drugs_catalog if str(r.get("condition", "")).strip().lower() == str(cond).strip().lower()]
            scored: List[Tuple[int, str, Dict[str, Any]]] = []
            for row in candidates:
                drug = str(row.get("drug", "")).strip()
                if not drug or drug in chosen:
                    continue
                risk = predicted_risk(drug, chosen)
                scored.append((risk, drug, row))
            if not scored:
                continue
            
            # Pick the HIGHEST risk drug (creates conflicts for demonstration)
            scored.sort(key=lambda t: (-t[0], t[1].lower()))  # Sort descending by risk
            best_drug = scored[0][1]
            chosen.append(best_drug)

        logger.info(f"Conflict-Prone Doctor prescribed for {patient.name}: {chosen} (with conflicts)")
        return chosen

    def step(self):
        pass


class RuleEngineAgent(Agent):
    def __init__(self, model, rules_rows: List[Dict[str, Any]]):
        super().__init__("rule_engine", model)
        self.kb = build_rules_kb(rules_rows)

    def check_conflicts(self, prescription: List[str], conditions: List[str], allergies: List[str]) -> List[Dict[str, Any]]:
        condition_tokens = make_condition_tokens(conditions, allergies)
        conflicts = bfs_conflicts(prescription, condition_tokens, self.kb)
        return [
            {
                "type": c.rtype,
                "item_a": c.item_a,
                "item_b": c.item_b,
                "severity": c.severity,
                "score": c.score,
                "recommendation": c.recommendation,
            }
            for c in conflicts
        ]

    def step(self):
        pass


class PharmacistAgent(Agent):
    def __init__(self, model, rule_engine: RuleEngineAgent):
        super().__init__("pharmacist", model)
        self.rule_engine = rule_engine

    def validate(self, patient: PatientAgent, prescription: List[str]) -> List[Dict[str, Any]]:
        conflicts = self.rule_engine.check_conflicts(prescription, patient.conditions, patient.allergies)
        logger.info(
            f"Pharmacist validated {patient.name}: {len(conflicts)} conflict(s) detected"
        )
        
        return conflicts

    def step(self):
        pass
