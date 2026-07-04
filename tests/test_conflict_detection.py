from utils import load_rules, make_condition_tokens, severity_to_score
from agents import RuleEngineAgent, PatientAgent
from model import HealthcareModel
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent


def test_hypertension_ibuprofen_conflict():
    model = HealthcareModel(data_dir=DATA_DIR)
    rule_engine = model.rule_engine
    prescription = ["Lisinopril", "Ibuprofen"]
    conditions = ["Hypertension"]
    allergies = []
    conflicts = rule_engine.check_conflicts(prescription, conditions, allergies)
    # Expect a drug-condition conflict Hypertension+Ibuprofen
    assert any(c['item_a'] == 'Hypertension' and c['item_b'] == 'Ibuprofen' and c['severity'] == 'Moderate' for c in conflicts), conflicts


def test_severity_scores_ordering():
    # Construct artificial rules to ensure ordering
    model = HealthcareModel(data_dir=DATA_DIR)
    rule_engine = model.rule_engine
    prescription = ["Warfarin", "Aspirin"]  # Major interaction
    conditions = []
    conflicts = rule_engine.check_conflicts(prescription, conditions, [])
    # Warfarin-Aspirin should have severity Major, score 3
    target = next((c for c in conflicts if c['item_a'] in ['Aspirin', 'Warfarin'] and c['item_b'] in ['Aspirin', 'Warfarin']), None)
    assert target is not None
    assert target['severity'] == 'Major'
    assert target['score'] == 3
