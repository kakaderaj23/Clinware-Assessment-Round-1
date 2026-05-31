"""
This module provides validation logic for the instantiated Patient Pydantic model
to check for missing, empty, or incomplete data attributes.
"""

from typing import List, Tuple
from models import Patient
from security import hash_sensitive_field


def validate_patient(patient: Patient) -> Tuple[bool, List[str]]:
    """
    Evaluates the instantiated Patient model and checks for data completeness issues.

    Checks if vital fields such as patient_id, name, diagnoses, medications,
    and insurance_id are missing, null, or empty, and compiles a comprehensive
    list of validation errors.

    Args:
        patient (Patient): The populated Patient model instance to validate.

    Returns:
        Tuple[bool, List[str]]: A tuple containing:
            - A boolean status (True if no errors, False otherwise).
            - A list of specific validation error messages.
    """
    # Time Complexity: # O(1) as the checks are key/field lookups on fixed fields.
    # Space Complexity: # O(E) where E is the number of errors discovered.

    # PII fields are hashed before validation to prevent plaintext exposure in logs or outputs.
    patient.patient_id = hash_sensitive_field(patient.patient_id)
    patient.insurance_id = hash_sensitive_field(patient.insurance_id)

    validation_errors: List[str] = []

    # 1. Check patient_id
    if patient.patient_id is None or str(patient.patient_id).strip() == "":
        validation_errors.append("missing patient_id")

    # 2. Check name
    if patient.name is None or str(patient.name).strip() == "":
        validation_errors.append("missing name")

    # 3. Check diagnoses
    if not patient.diagnoses:
        validation_errors.append("empty diagnoses list")

    # 4. Check medications
    if not patient.medications:
        validation_errors.append("empty medications list")

    # 5. Check insurance_id
    if patient.insurance_id is None or str(patient.insurance_id).strip() == "":
        validation_errors.append("missing insurance_id")

    # Return status and compiled error list
    is_valid = len(validation_errors) == 0
    return is_valid, validation_errors
