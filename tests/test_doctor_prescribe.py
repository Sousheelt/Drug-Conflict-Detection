from model import HealthcareModel
from agents import DoctorAgent, PatientAgent
from utils import load_patients, load_drugs, load_rules
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent


def _make_model():
    return HealthcareModel(data_dir=DATA_DIR)


def test_analgesic_added_only_for_pain():
    model = _make_model()
    doctor = model.doctor
    # Patient without Pain (John Doe id=1)
    p1_row = next(r for r in model.patients_rows if r['id'] == '1')
    p1 = PatientAgent(model, p1_row['id'], p1_row['name'], p1_row['conditions'], p1_row['allergies'])
    rx1 = doctor.prescribe(p1)
    analgesics = {"Paracetamol", "Ibuprofen", "Naproxen", "Aspirin"}
    assert not any(a in rx1 for a in analgesics), f"No analgesic should be added: {rx1}"


def test_low_risk_analgesic_chosen_for_pain_and_anticoagulation():
    model = _make_model()
    doctor = model.doctor
    # Patient with Anticoagulation and Pain (id=10)
    p10_row = next(r for r in model.patients_rows if r['id'] == '10')
    p10 = PatientAgent(model, p10_row['id'], p10_row['name'], p10_row['conditions'], p10_row['allergies'])
    rx10 = doctor.prescribe(p10)
    # Paracetamol should be chosen because NSAIDs + Warfarin have major interactions; allergies include Ibuprofen
    assert "Paracetamol" in rx10, f"Expected Paracetamol in prescription, got {rx10}"
    # Ensure no high-risk NSAID chosen
    for risky in ["Ibuprofen", "Aspirin", "Naproxen"]:
        assert risky not in rx10, f"Did not expect high-risk analgesic {risky} in {rx10}"
