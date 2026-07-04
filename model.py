from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from mesa import Model
from mesa.time import BaseScheduler

from agents import PatientAgent, DoctorAgent, PharmacistAgent, RuleEngineAgent
from utils import load_patients, load_drugs, load_rules, logger, conflicts_to_frame


class HealthcareModel(Model):
    def __init__(self, data_dir: Path | str, doctor_mode: str = "smart"):
        super().__init__()
        self.data_dir = Path(data_dir)
        self.doctor_mode = doctor_mode  # "smart" or "conflict-prone"
        
        # Load data
        self.patients_rows = load_patients(self.data_dir / "patients.csv")
        self.drugs_rows = load_drugs(self.data_dir / "drugs.csv")
        self.rules_rows = load_rules(self.data_dir / "rules.csv")

        # Scheduler (not heavily used in this simple orchestrated loop)
        self.schedule = BaseScheduler(self)

        # Agents
        self.rule_engine = RuleEngineAgent(self, self.rules_rows)
        self.doctor = DoctorAgent(self, self.drugs_rows, mode=doctor_mode)
        self.pharmacist = PharmacistAgent(self, self.rule_engine)

        self.schedule.add(self.rule_engine)
        self.schedule.add(self.doctor)
        self.schedule.add(self.pharmacist)

        # Create patients
        self.patients: List[PatientAgent] = []
        for row in self.patients_rows:
            pid = str(row.get("id"))
            name = str(row.get("name", f"Patient-{pid}"))
            conditions = row.get("conditions", []) or []
            allergies = row.get("allergies", []) or []
            pa = PatientAgent(model=self, patient_id=pid, name=name, conditions=conditions, allergies=allergies)
            self.patients.append(pa)
            self.schedule.add(pa)

        # Logs
        self.total_prescriptions = 0
        self.conflict_logs: List[Dict[str, Any]] = []

    def step(self):
        # Orchestrate interactions per patient
        for patient in self.patients:
            rx = self.doctor.prescribe(patient)
            patient.prescription = rx
            self.total_prescriptions += 1

            conflicts = self.pharmacist.validate(patient, rx)
            for c in conflicts:
                entry = {
                    "patient_id": patient.patient_id,
                    "patient_name": patient.name,
                    "prescription": ";".join(patient.prescription),
                    **c,
                }
                self.conflict_logs.append(entry)

        # Advance scheduler (no-op for now)
        self.schedule.step()

    def run(self, steps: int = 1):
        for _ in range(steps):
            self.step()

    def conflicts_dataframe(self) -> pd.DataFrame:
        if not self.conflict_logs:
            return pd.DataFrame(columns=[
                "patient_id", "patient_name", "prescription", "type", "item_a", "item_b", "severity", "score", "recommendation"
            ])
        return pd.DataFrame(self.conflict_logs)

    def save_conflicts_csv(self, out_path: Path | str):
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df = self.conflicts_dataframe()
        df.to_csv(out_path, index=False)
        logger.info(f"Saved conflicts to {out_path}")
