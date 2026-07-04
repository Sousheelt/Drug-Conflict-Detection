from data_models import PatientModel, RuleModel, DrugModel, validate_rows, ALLOWED_SEVERITIES
from pydantic import ValidationError


def test_patient_semicolon_parsing():
    row = {"id": "1", "name": "Test", "conditions": "Hypertension;Diabetes;None", "allergies": "Penicillin;None"}
    p = PatientModel(**row)
    assert p.conditions == ["Hypertension", "Diabetes"]
    assert p.allergies == ["Penicillin"]


def test_rule_invalid_severity():
    bad = {"type": "drug-drug", "item_a": "Aspirin", "item_b": "Warfarin", "severity": "Severe", "recommendation": "Avoid"}
    try:
        RuleModel(**bad)
    except ValidationError as e:
        assert any(err['loc'] == ('severity',) for err in e.errors())
    else:
        raise AssertionError("Expected ValidationError for invalid severity")


def test_drug_replacements_parsing():
    row = {"drug": "Lisinopril", "condition": "Hypertension", "category": "ACE", "replacements": "Losartan;None"}
    d = DrugModel(**row)
    assert d.replacements == ["Losartan"]
