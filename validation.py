"""
Input Validation and Sanitization Module

Provides comprehensive validation and sanitization functions for:
- CSV data validation (drugs, patients, rules)
- User input sanitization (XSS, SQL injection prevention)
- Data type and range validation
- Security checks for file uploads and data processing
"""

import re
from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import pandas as pd
from pydantic import BaseModel, Field, field_validator, ValidationError


# ===========================
# Data Models for Validation
# ===========================

class DrugValidator(BaseModel):
    """Validation model for drug data"""
    drug_id: int = Field(gt=0, description="Must be positive integer")
    drug_name: str = Field(min_length=1, max_length=100, description="Drug name")
    category: str = Field(min_length=1, max_length=50, description="Drug category")
    
    @field_validator('drug_name', 'category')
    @classmethod
    def sanitize_string(cls, v: str) -> str:
        """Remove potentially harmful characters"""
        if not v or not isinstance(v, str):
            raise ValueError("Must be a non-empty string")
        # Remove special characters that could be used for injection
        sanitized = re.sub(r'[<>\"\'%;()&+]', '', v)
        return sanitized.strip()


class PatientValidator(BaseModel):
    """Validation model for patient data"""
    patient_id: int = Field(gt=0, description="Must be positive integer")
    name: str = Field(min_length=1, max_length=100, description="Patient name")
    age: int = Field(ge=0, le=150, description="Age must be between 0 and 150")
    conditions: str = Field(min_length=0, max_length=500, description="Medical conditions")
    medications: str = Field(min_length=0, max_length=1000, description="Current medications")
    
    @field_validator('name')
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Sanitize patient name"""
        if not v or not isinstance(v, str):
            raise ValueError("Name must be a non-empty string")
        # Allow only letters, spaces, hyphens, and apostrophes
        sanitized = re.sub(r'[^a-zA-Z\s\-\']', '', v)
        return sanitized.strip()
    
    @field_validator('conditions', 'medications')
    @classmethod
    def sanitize_medical_text(cls, v: str) -> str:
        """Sanitize medical text fields"""
        if not isinstance(v, str):
            return ""
        # Remove HTML/script tags and special characters
        sanitized = re.sub(r'<[^>]+>', '', v)
        sanitized = re.sub(r'[<>\"\'%;()&+]', '', sanitized)
        return sanitized.strip()


class RuleValidator(BaseModel):
    """Validation model for conflict rules"""
    rule_id: int = Field(gt=0, description="Must be positive integer")
    drug1: str = Field(min_length=1, max_length=100, description="First drug")
    drug2: str = Field(min_length=1, max_length=100, description="Second drug")
    severity: str = Field(pattern=r'^(Minor|Moderate|Major)$', description="Severity level")
    description: str = Field(min_length=1, max_length=500, description="Conflict description")
    
    @field_validator('drug1', 'drug2')
    @classmethod
    def sanitize_drug_name(cls, v: str) -> str:
        """Sanitize drug names in rules"""
        if not v or not isinstance(v, str):
            raise ValueError("Drug name must be a non-empty string")
        sanitized = re.sub(r'[<>\"\'%;()&+]', '', v)
        return sanitized.strip()
    
    @field_validator('description')
    @classmethod
    def sanitize_description(cls, v: str) -> str:
        """Sanitize rule description"""
        if not v or not isinstance(v, str):
            raise ValueError("Description must be a non-empty string")
        # Remove HTML/script tags
        sanitized = re.sub(r'<[^>]+>', '', v)
        sanitized = re.sub(r'[<>\"\'%;()&+]', '', sanitized)
        return sanitized.strip()


# ===========================
# CSV Validation Functions
# ===========================

def validate_drugs_csv(df: pd.DataFrame) -> tuple[bool, List[str]]:
    """
    Validate drugs CSV data
    
    Args:
        df: DataFrame containing drug data
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required columns
    required_cols = ['drug_id', 'drug_name', 'category']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return False, errors
    
    # Validate each row
    for idx, row in df.iterrows():
        try:
            DrugValidator(
                drug_id=int(row['drug_id']),
                drug_name=str(row['drug_name']),
                category=str(row['category'])
            )
        except (ValidationError, ValueError) as e:
            errors.append(f"Row {idx + 2}: {str(e)}")
    
    # Check for duplicate drug IDs
    if df['drug_id'].duplicated().any():
        duplicate_ids = df[df['drug_id'].duplicated()]['drug_id'].tolist()
        errors.append(f"Duplicate drug IDs found: {duplicate_ids}")
    
    return len(errors) == 0, errors


def validate_patients_csv(df: pd.DataFrame) -> tuple[bool, List[str]]:
    """
    Validate patients CSV data
    
    Args:
        df: DataFrame containing patient data
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required columns
    required_cols = ['patient_id', 'name', 'age', 'conditions', 'medications']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return False, errors
    
    # Validate each row
    for idx, row in df.iterrows():
        try:
            PatientValidator(
                patient_id=int(row['patient_id']),
                name=str(row['name']),
                age=int(row['age']),
                conditions=str(row.get('conditions', '')),
                medications=str(row.get('medications', ''))
            )
        except (ValidationError, ValueError) as e:
            errors.append(f"Row {idx + 2}: {str(e)}")
    
    # Check for duplicate patient IDs
    if df['patient_id'].duplicated().any():
        duplicate_ids = df[df['patient_id'].duplicated()]['patient_id'].tolist()
        errors.append(f"Duplicate patient IDs found: {duplicate_ids}")
    
    return len(errors) == 0, errors


def validate_rules_csv(df: pd.DataFrame) -> tuple[bool, List[str]]:
    """
    Validate rules CSV data
    
    Args:
        df: DataFrame containing conflict rules
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    # Check required columns
    required_cols = ['rule_id', 'drug1', 'drug2', 'severity', 'description']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {', '.join(missing_cols)}")
        return False, errors
    
    # Validate each row
    for idx, row in df.iterrows():
        try:
            RuleValidator(
                rule_id=int(row['rule_id']),
                drug1=str(row['drug1']),
                drug2=str(row['drug2']),
                severity=str(row['severity']),
                description=str(row['description'])
            )
        except (ValidationError, ValueError) as e:
            errors.append(f"Row {idx + 2}: {str(e)}")
    
    # Check for duplicate rule IDs
    if df['rule_id'].duplicated().any():
        duplicate_ids = df[df['rule_id'].duplicated()]['rule_id'].tolist()
        errors.append(f"Duplicate rule IDs found: {duplicate_ids}")
    
    return len(errors) == 0, errors


# ===========================
# Input Sanitization Functions
# ===========================

def sanitize_string(input_str: str, max_length: int = 1000) -> str:
    """
    Sanitize general string input
    
    Args:
        input_str: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not input_str or not isinstance(input_str, str):
        return ""
    
    # Truncate to max length
    sanitized = input_str[:max_length]
    
    # Remove HTML/script tags
    sanitized = re.sub(r'<[^>]+>', '', sanitized)
    
    # Remove only the most dangerous characters (XSS/injection)
    # Keep parentheses, semicolons (for CSV lists), and common punctuation
    sanitized = re.sub(r'[<>\"\'%&]', '', sanitized)
    
    # Remove SQL keywords only if they appear in suspicious patterns
    # Don't remove from normal text (e.g., "select medication")
    sanitized = re.sub(r'\b(DROP|DELETE|INSERT|UPDATE)\s+(TABLE|FROM|INTO)', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'UNION\s+SELECT', '', sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r'--\s*$', '', sanitized)  # SQL comments at end of line
    
    return sanitized.strip()


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    if not filename or not isinstance(filename, str):
        return "unnamed_file"
    
    # Remove path traversal attempts
    filename = filename.replace('..', '').replace('/', '').replace('\\', '')
    
    # Keep only alphanumeric, dots, underscores, and hyphens
    sanitized = re.sub(r'[^\w\-\.]', '_', filename)
    
    # Limit length
    sanitized = sanitized[:255]
    
    return sanitized


def validate_integer(value: Any, min_val: Optional[int] = None, 
                     max_val: Optional[int] = None) -> tuple[bool, Optional[int]]:
    """
    Validate and convert to integer
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Tuple of (is_valid, converted_value)
    """
    try:
        int_val = int(value)
        
        if min_val is not None and int_val < min_val:
            return False, None
        
        if max_val is not None and int_val > max_val:
            return False, None
        
        return True, int_val
    except (ValueError, TypeError):
        return False, None


def validate_float(value: Any, min_val: Optional[float] = None,
                   max_val: Optional[float] = None) -> tuple[bool, Optional[float]]:
    """
    Validate and convert to float
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        Tuple of (is_valid, converted_value)
    """
    try:
        float_val = float(value)
        
        if min_val is not None and float_val < min_val:
            return False, None
        
        if max_val is not None and float_val > max_val:
            return False, None
        
        return True, float_val
    except (ValueError, TypeError):
        return False, None


def validate_severity(severity: str) -> bool:
    """
    Validate severity level
    
    Args:
        severity: Severity string to validate
        
    Returns:
        True if valid severity level
    """
    valid_severities = ['Minor', 'Moderate', 'Major']
    return severity in valid_severities


def validate_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email string to validate
        
    Returns:
        True if valid email format
    """
    if not email or not isinstance(email, str):
        return False
    
    # Basic email regex pattern
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_password_strength(password: str) -> tuple[bool, List[str]]:
    """
    Validate password strength
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    if len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    return len(errors) == 0, errors


# ===========================
# Security Validation Functions
# ===========================

def check_xss_attempt(input_str: str) -> bool:
    """
    Check if input contains potential XSS attack patterns
    
    Args:
        input_str: Input string to check
        
    Returns:
        True if potential XSS detected
    """
    if not input_str or not isinstance(input_str, str):
        return False
    
    xss_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+\s*=',
        r'<iframe',
        r'<object',
        r'<embed',
    ]
    
    for pattern in xss_patterns:
        if re.search(pattern, input_str, re.IGNORECASE):
            return True
    
    return False


def check_sql_injection(input_str: str) -> bool:
    """
    Check if input contains potential SQL injection patterns
    
    Args:
        input_str: Input string to check
        
    Returns:
        True if potential SQL injection detected
    """
    if not input_str or not isinstance(input_str, str):
        return False
    
    sql_patterns = [
        r"(\bOR\b|\bAND\b)\s+['\"]?\d+['\"]?\s*=\s*['\"]?\d+['\"]?",
        r";\s*(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER)",
        r"UNION\s+SELECT",
        r"--",
        r"/\*.*\*/",
        r"xp_cmdshell",
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, input_str, re.IGNORECASE):
            return True
    
    return False


def check_path_traversal(path: str) -> bool:
    """
    Check if path contains path traversal attempts
    
    Args:
        path: File path to check
        
    Returns:
        True if path traversal detected
    """
    if not path or not isinstance(path, str):
        return False
    
    dangerous_patterns = ['../', '..\\', '%2e%2e', '%252e%252e']
    
    for pattern in dangerous_patterns:
        if pattern in path.lower():
            return True
    
    return False


def validate_input_safe(input_str: str) -> tuple[bool, List[str]]:
    """
    Comprehensive security validation for user input
    
    Args:
        input_str: Input string to validate
        
    Returns:
        Tuple of (is_safe, warning_messages)
    """
    warnings = []
    
    if check_xss_attempt(input_str):
        warnings.append("Potential XSS attack detected")
    
    if check_sql_injection(input_str):
        warnings.append("Potential SQL injection detected")
    
    if check_path_traversal(input_str):
        warnings.append("Path traversal attempt detected")
    
    return len(warnings) == 0, warnings
