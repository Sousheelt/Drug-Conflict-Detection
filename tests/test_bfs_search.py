"""
Tests for the Best-First Search conflict detection algorithm.

Verifies that the search:
1. Discovers all conflicts systematically
2. Prioritizes high-severity conflicts
3. Handles state space exploration correctly
4. Maintains visited state tracking
"""

import pytest
from utils import bfs_conflicts, Rule


def test_bfs_discovers_all_conflicts():
    """BFS should discover all possible conflicts in a multi-drug prescription."""
    kb = {
        ("drug-drug", "aspirin", "warfarin"): Rule(
            rtype="drug-drug",
            item_a="Aspirin",
            item_b="Warfarin",
            severity="Major",
            recommendation="Avoid combination - bleeding risk"
        ),
        ("drug-drug", "aspirin", "ibuprofen"): Rule(
            rtype="drug-drug",
            item_a="Aspirin",
            item_b="Ibuprofen",
            severity="Moderate",
            recommendation="Reduce NSAID effectiveness"
        ),
        ("drug-condition", "hypertension", "ibuprofen"): Rule(
            rtype="drug-condition",
            item_a="Hypertension",
            item_b="Ibuprofen",
            severity="Major",
            recommendation="Can elevate blood pressure"
        ),
    }
    
    prescription = ["Aspirin", "Warfarin", "Ibuprofen"]
    conditions = ["Hypertension"]
    
    conflicts = bfs_conflicts(prescription, conditions, kb)
    
    # Should find all 3 conflicts
    assert len(conflicts) == 3
    
    # Extract conflict identifiers
    conflict_keys = {(c.rtype, c.item_a.lower(), c.item_b.lower()) for c in conflicts}
    
    assert ("drug-drug", "aspirin", "warfarin") in conflict_keys
    assert ("drug-drug", "aspirin", "ibuprofen") in conflict_keys
    assert ("drug-condition", "hypertension", "ibuprofen") in conflict_keys


def test_bfs_prioritizes_major_severity():
    """BFS should report Major conflicts before Minor ones."""
    kb = {
        ("drug-drug", "a", "b"): Rule(
            rtype="drug-drug",
            item_a="A",
            item_b="B",
            severity="Minor",
            recommendation="Monitor"
        ),
        ("drug-drug", "c", "d"): Rule(
            rtype="drug-drug",
            item_a="C",
            item_b="D",
            severity="Major",
            recommendation="Contraindicated"
        ),
        ("drug-drug", "e", "f"): Rule(
            rtype="drug-drug",
            item_a="E",
            item_b="F",
            severity="Moderate",
            recommendation="Use caution"
        ),
    }
    
    prescription = ["A", "B", "C", "D", "E", "F"]
    conditions = []
    
    conflicts = bfs_conflicts(prescription, conditions, kb)
    
    # Should find all 3
    assert len(conflicts) == 3
    
    # Major should appear first
    assert conflicts[0].severity == "Major"
    assert conflicts[0].item_a.lower() == "c"
    assert conflicts[0].item_b.lower() == "d"
    
    # Moderate second
    assert conflicts[1].severity == "Moderate"
    
    # Minor last
    assert conflicts[2].severity == "Minor"


def test_bfs_handles_no_conflicts():
    """BFS should return empty list when no conflicts exist."""
    kb = {
        ("drug-drug", "x", "y"): Rule(
            rtype="drug-drug",
            item_a="X",
            item_b="Y",
            severity="Major",
            recommendation="Don't combine"
        ),
    }
    
    prescription = ["A", "B", "C"]  # No conflict rules for these
    conditions = []
    
    conflicts = bfs_conflicts(prescription, conditions, kb)
    assert len(conflicts) == 0


def test_bfs_handles_empty_prescription():
    """BFS should return empty list for empty prescription."""
    kb = {
        ("drug-drug", "a", "b"): Rule(
            rtype="drug-drug",
            item_a="A",
            item_b="B",
            severity="Major",
            recommendation="Avoid"
        ),
    }
    
    conflicts = bfs_conflicts([], [], kb)
    assert len(conflicts) == 0


def test_bfs_state_space_exploration():
    """BFS should explore state space without revisiting conflict sets."""
    # Setup: 4 drugs with 2 pairs creating conflicts
    kb = {
        ("drug-drug", "a", "b"): Rule(
            rtype="drug-drug",
            item_a="A",
            item_b="B",
            severity="Major",
            recommendation="R1"
        ),
        ("drug-drug", "c", "d"): Rule(
            rtype="drug-drug",
            item_a="C",
            item_b="D",
            severity="Moderate",
            recommendation="R2"
        ),
    }
    
    prescription = ["A", "B", "C", "D"]
    conditions = []
    
    conflicts = bfs_conflicts(prescription, conditions, kb)
    
    # Should find exactly 2 conflicts (both pairs)
    assert len(conflicts) == 2
    assert conflicts[0].severity == "Major"  # A-B explored first
    assert conflicts[1].severity == "Moderate"  # C-D explored second


def test_bfs_with_allergies_as_conditions():
    """BFS should detect drug-condition conflicts for allergies."""
    kb = {
        ("drug-condition", "penicillinallergy", "amoxicillin"): Rule(
            rtype="drug-condition",
            item_a="PenicillinAllergy",
            item_b="Amoxicillin",
            severity="Major",
            recommendation="Contraindicated - cross-reactivity"
        ),
    }
    
    prescription = ["Amoxicillin"]
    # Note: make_condition_tokens in utils.py handles appending "Allergy"
    conditions = ["PenicillinAllergy"]  # Already formatted
    
    conflicts = bfs_conflicts(prescription, conditions, kb)
    
    assert len(conflicts) == 1
    assert conflicts[0].severity == "Major"
    assert "amoxicillin" in conflicts[0].item_b.lower()


def test_bfs_case_insensitive_matching():
    """BFS should match drugs/conditions case-insensitively."""
    kb = {
        ("drug-drug", "aspirin", "warfarin"): Rule(
            rtype="drug-drug",
            item_a="Aspirin",
            item_b="Warfarin",
            severity="Major",
            recommendation="Bleeding risk"
        ),
    }
    
    # Mix cases in prescription
    prescription = ["ASPIRIN", "warfarin"]
    conditions = []
    
    conflicts = bfs_conflicts(prescription, conditions, kb)
    
    assert len(conflicts) == 1
    assert conflicts[0].severity == "Major"
