from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, field_validator, ValidationError

ALLOWED_SEVERITIES = {"Major", "Moderate", "Minor"}
ALLOWED_RULE_TYPES = {"drug-drug", "drug-condition"}

class PatientModel(BaseModel):
    id: str
    name: str
    conditions: List[str] = []
    allergies: List[str] = []

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id_to_str(cls, v):
        return str(v) if v is not None else ""

    @field_validator("conditions", "allergies", mode="before")
    @classmethod
    def split_semicolon(cls, v):
        if v is None:
            return []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip() and str(x).strip().lower() != "none"]
        if isinstance(v, str):
            parts = [p.strip() for p in v.split(";") if p.strip()]
            return [p for p in parts if p.lower() != "none"]
        return [str(v)]

class DrugModel(BaseModel):
    drug: str
    condition: str
    category: Optional[str] = None
    replacements: List[str] = []

    @field_validator("replacements", mode="before")
    @classmethod
    def split_replacements(cls, v):
        if v is None or (isinstance(v, float) and v != v):  # NaN
            return []
        if isinstance(v, list):
            return [str(x).strip() for x in v if str(x).strip()]
        if isinstance(v, str):
            if ";" in v:
                return [p.strip() for p in v.split(";") if p.strip() and p.strip().lower() != "none"]
            if v.strip():
                return [v.strip()]
        return []

class RuleModel(BaseModel):
    type: str
    item_a: str
    item_b: str
    severity: str
    recommendation: str
    notes: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v):
        v = str(v).strip().lower()
        if v not in ALLOWED_RULE_TYPES:
            raise ValueError(f"type must be one of {ALLOWED_RULE_TYPES}, got '{v}'")
        return v

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v):
        v = str(v).strip().title()
        if v not in ALLOWED_SEVERITIES:
            raise ValueError(f"severity must be one of {ALLOWED_SEVERITIES}, got '{v}'")
        return v

    @field_validator("item_a", "item_b")
    @classmethod
    def non_empty(cls, v):
        v = str(v).strip()
        if not v:
            raise ValueError("value cannot be empty")
        return v

    @field_validator("recommendation")
    @classmethod
    def normalize_recommendation(cls, v):
        v = str(v).strip()
        return v


def validate_rows(rows, model_cls):
    """Validate list[dict] rows with the given model class.
    Returns (valid_models, errors) where errors is list of (index, error_message).
    """
    valid = []
    errors = []
    for idx, row in enumerate(rows):
        try:
            obj = model_cls(**row)
            valid.append(obj)
        except ValidationError as e:
            errors.append((idx, e.errors()))
    return valid, errors
