"""
This module provides functionality to safely parse deeply nested, untrusted
FHIR-style patient resource payloads into a structured Patient data model.
"""

import logging
from typing import Any, Dict, List, Optional
from models import Patient

# Configure logger
logger = logging.getLogger(__name__)


def parse_fhir_patient(data: dict) -> Patient:
    """
    Safely parse a deeply nested FHIR-style patient JSON payload.

    This function navigates messy, untrusted healthcare data structures,
    ensuring that no KeyError or TypeError propagates out. If any field
    extraction fails, it logs the exact field that failed and defaults
    to None or an empty list.

    Args:
        data (dict): The dictionary representation of the incoming JSON payload.

    Returns:
        Patient: An instantiated and populated Patient Pydantic model.
    """
    # Time Complexity: # O(N) where N is the length/size of the JSON payload.
    # Space Complexity: # O(N) to store the returned Patient object and its properties.

    # 1. Base input validation: ensure the input data is a dictionary
    if not isinstance(data, dict):
        logger.error(
            "Payload root is not a dictionary. Got type: %s",
            type(data).__name__
        )
        return Patient()

    # In FHIR, the resource could be at the root or nested inside a "resource" object (bundle entry)
    # Let's inspect if there is a nested resource block
    resource_payload = data.get("resource")
    patient_source = resource_payload if isinstance(resource_payload, dict) else data

    # Safe parsing of patient_id
    patient_id: Optional[str] = None
    try:
        raw_id = patient_source.get("id")
        if raw_id is not None and isinstance(raw_id, (str, int, float)):
            patient_id = str(raw_id).strip()
    except Exception as exception_info:
        logger.error(
            "Failed to parse patient_id from payload. Error details: %s",
            str(exception_info)
        )

    # Safe parsing of name
    name_string: Optional[str] = None
    try:
        name_list = patient_source.get("name")
        if isinstance(name_list, list) and len(name_list) > 0:
            first_name_entry = name_list[0]
            if isinstance(first_name_entry, dict):
                # 1. Try to use "text" field if present as a non-empty string
                text_name = first_name_entry.get("text")
                if isinstance(text_name, str) and text_name.strip():
                    name_string = text_name.strip()
                else:
                    # 2. Otherwise build from given and family
                    name_parts: List[str] = []
                    given_names = first_name_entry.get("given")
                    if isinstance(given_names, list):
                        for given_name in given_names:
                            if isinstance(given_name, str) and given_name.strip():
                                name_parts.append(given_name.strip())

                    family_name = first_name_entry.get("family")
                    if isinstance(family_name, str) and family_name.strip():
                        name_parts.append(family_name.strip())

                    if name_parts:
                        name_string = " ".join(name_parts)
    except Exception as exception_info:
        logger.error(
            "Failed to parse name from payload. Error details: %s",
            str(exception_info)
        )

    # Safe parsing of diagnoses
    diagnoses_list: List[str] = []
    try:
        # Check standard fields or extensions
        raw_diagnoses = patient_source.get("diagnoses")
        if raw_diagnoses is None:
            # Check custom / condition field
            raw_diagnoses = patient_source.get("conditions") or patient_source.get("diagnoses_list")

        if isinstance(raw_diagnoses, list):
            for diagnosis in raw_diagnoses:
                if isinstance(diagnosis, str) and diagnosis.strip():
                    diagnoses_list.append(diagnosis.strip())
                elif isinstance(diagnosis, dict):
                    # Maybe Codeable Concept display/text
                    display = diagnosis.get("display") or diagnosis.get("text")
                    if isinstance(display, str) and display.strip():
                        diagnoses_list.append(display.strip())
    except Exception as exception_info:
        logger.error(
            "Failed to parse diagnoses from payload. Error details: %s",
            str(exception_info)
        )

    # Safe parsing of medications
    medications_list: List[str] = []
    try:
        raw_medications = patient_source.get("medications")
        if raw_medications is None:
            raw_medications = patient_source.get("medication_list")

        if isinstance(raw_medications, list):
            for medication in raw_medications:
                if isinstance(medication, str) and medication.strip():
                    medications_list.append(medication.strip())
                elif isinstance(medication, dict):
                    display = medication.get("display") or medication.get("text")
                    if isinstance(display, str) and display.strip():
                        medications_list.append(display.strip())
    except Exception as exception_info:
        logger.error(
            "Failed to parse medications from payload. Error details: %s",
            str(exception_info)
        )

    # Safe parsing of insurance_id
    insurance_id: Optional[str] = None
    try:
        raw_insurance_id = patient_source.get("insurance_id")
        if raw_insurance_id is None:
            # Check list structure if insurance is nested
            raw_insurance_list = patient_source.get("insurance")
            if isinstance(raw_insurance_list, list) and len(raw_insurance_list) > 0:
                first_insurance = raw_insurance_list[0]
                if isinstance(first_insurance, dict):
                    raw_insurance_id = first_insurance.get("id") or first_insurance.get("reference")

        if raw_insurance_id is not None and isinstance(raw_insurance_id, (str, int, float)):
            insurance_id = str(raw_insurance_id).strip()
    except Exception as exception_info:
        logger.error(
            "Failed to parse insurance_id from payload. Error details: %s",
            str(exception_info)
        )

    return Patient(
        patient_id=patient_id,
        name=name_string,
        diagnoses=diagnoses_list,
        medications=medications_list,
        insurance_id=insurance_id
    )
