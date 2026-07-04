"""Tests for memoization & optimization layer.

Verifies that:
1. get_conflicts_cached returns identical results to bfs_conflicts
2. Subsequent identical calls register a cache hit
3. Changing KB invalidates cache (different id)
"""

from utils import build_rules_kb, get_conflicts_cached, bfs_conflicts, Rule, _MEMO_STATS


def _make_kb():
    rows = [
        {"type": "drug-drug", "item_a": "Aspirin", "item_b": "Warfarin", "severity": "Major", "recommendation": "Avoid"},
        {"type": "drug-condition", "item_a": "Hypertension", "item_b": "Ibuprofen", "severity": "Moderate", "recommendation": "Monitor"},
    ]
    return build_rules_kb(rows)


def test_cached_equals_raw():
    kb = _make_kb()
    prescription = ["Aspirin", "Warfarin", "Ibuprofen"]
    conditions = ["Hypertension"]

    raw = bfs_conflicts(prescription, conditions, kb)
    cached = get_conflicts_cached(prescription, conditions, kb)

    assert len(raw) == len(cached)
    # Compare sets of tuple identity
    raw_keys = {(c.rtype, c.item_a, c.item_b, c.severity) for c in raw}
    cached_keys = {(c.rtype, c.item_a, c.item_b, c.severity) for c in cached}
    assert raw_keys == cached_keys


def test_cache_hits_increment():
    kb = _make_kb()
    prescription = ["Aspirin", "Warfarin"]
    conditions = []

    # Miss expected first
    start_hits = _MEMO_STATS["hits"]
    start_misses = _MEMO_STATS["misses"]
    get_conflicts_cached(prescription, conditions, kb)
    assert _MEMO_STATS["misses"] == start_misses + 1

    # Hit expected second
    get_conflicts_cached(prescription, conditions, kb)
    assert _MEMO_STATS["hits"] == start_hits + 1


def test_kb_change_invalidates_cache():
    kb1 = _make_kb()
    kb2 = _make_kb()  # new object, different id(kb)
    prescription = ["Aspirin", "Warfarin"]
    conditions = []

    get_conflicts_cached(prescription, conditions, kb1)
    hits_before = _MEMO_STATS["hits"]
    get_conflicts_cached(prescription, conditions, kb2)  # should be miss due to kb id change
    assert _MEMO_STATS["hits"] == hits_before  # no new hit
