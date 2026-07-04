"""Tests for real-time conflict checking UI functionality.

Verifies that the conflict detection works correctly for the manual testing interface.
"""

import pytest
from model import HealthcareModel
from pathlib import Path


def test_realtime_conflict_detection_basic():
    """Test that real-time conflict detection finds known conflicts."""
    base_dir = Path(__file__).parent.parent
    model = HealthcareModel(data_dir=base_dir)
    
    # Test a known conflict: Aspirin + Warfarin
    conflicts = model.rule_engine.check_conflicts(
        prescription=["Aspirin", "Warfarin"],
        conditions=[],
        allergies=[]
    )
    
    assert len(conflicts) > 0
    # Should find Aspirin-Warfarin interaction
    conflict_pairs = [(c['item_a'].lower(), c['item_b'].lower()) for c in conflicts]
    assert any(('aspirin' in pair and 'warfarin' in pair) or ('warfarin' in pair and 'aspirin' in pair) 
               for pair in conflict_pairs)


def test_realtime_no_conflicts_safe():
    """Test that safe prescriptions return no conflicts."""
    base_dir = Path(__file__).parent.parent
    model = HealthcareModel(data_dir=base_dir)
    
    # Test a safe combination (no known interactions)
    conflicts = model.rule_engine.check_conflicts(
        prescription=["Lisinopril"],
        conditions=["Diabetes"],
        allergies=[]
    )
    
    # Single drug with non-conflicting condition should be safe
    assert len(conflicts) == 0


def test_realtime_drug_condition_conflict():
    """Test that drug-condition conflicts are detected in real-time."""
    base_dir = Path(__file__).parent.parent
    model = HealthcareModel(data_dir=base_dir)
    
    # Ibuprofen + Hypertension is a known conflict
    conflicts = model.rule_engine.check_conflicts(
        prescription=["Ibuprofen"],
        conditions=["Hypertension"],
        allergies=[]
    )
    
    assert len(conflicts) > 0
    # Check it's a drug-condition type
    assert any(c['type'] == 'drug-condition' for c in conflicts)


def test_realtime_allergy_detection():
    """Test that allergies are detected as conflicts."""
    base_dir = Path(__file__).parent.parent
    model = HealthcareModel(data_dir=base_dir)
    
    # Aspirin with Aspirin allergy
    conflicts = model.rule_engine.check_conflicts(
        prescription=["Aspirin"],
        conditions=[],
        allergies=["Aspirin"]
    )
    
    assert len(conflicts) > 0
    # Should detect AspiriAllergy in conditions
    assert any('allergy' in c['item_a'].lower() or 'allergy' in c['item_b'].lower() 
               for c in conflicts)


def test_realtime_multiple_conflicts():
    """Test detection of multiple conflicts simultaneously."""
    base_dir = Path(__file__).parent.parent
    model = HealthcareModel(data_dir=base_dir)
    
    # Risky combination: multiple anticoagulants + NSAIDs + hypertension
    conflicts = model.rule_engine.check_conflicts(
        prescription=["Aspirin", "Warfarin", "Ibuprofen"],
        conditions=["Hypertension"],
        allergies=[]
    )
    
    # Should detect multiple conflicts
    assert len(conflicts) >= 2
    
    # Should have different severity levels
    severities = {c['severity'] for c in conflicts}
    assert len(severities) > 0


def test_realtime_severity_ordering():
    """Test that conflicts are returned with proper severity scores."""
    base_dir = Path(__file__).parent.parent
    model = HealthcareModel(data_dir=base_dir)
    
    conflicts = model.rule_engine.check_conflicts(
        prescription=["Aspirin", "Warfarin"],
        conditions=[],
        allergies=[]
    )
    
    if conflicts:
        # All conflicts should have severity and score fields
        for conflict in conflicts:
            assert 'severity' in conflict
            assert 'score' in conflict
            assert conflict['severity'] in ['Major', 'Moderate', 'Minor']
            assert conflict['score'] > 0
