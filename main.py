"""
This module provides a CLI runner to load, parse, validate, and summarize
deeply nested FHIR-style patient JSON files.
"""

import argparse
import json
import logging
import sys
from typing import Any, Dict, List
from models import Patient
from parser import parse_fhir_patient
from validator import validate_patient
from security import hash_sensitive_field

# Configure clean logging to standard error
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr
)
logger = logging.getLogger(__name__)


def load_json_file(file_path: str) -> dict:
    """
    Safely load and parse a JSON file.

    Handles FileNotFoundError and JSONDecodeError gracefully by logging
    and returning an empty dictionary to prevent system crashes.

    Args:
        file_path (str): The absolute or relative path to the JSON file.

    Returns:
        dict: The parsed JSON dictionary, or an empty dictionary if loading failed.
    """
    # Time Complexity: # O(F) where F is the size of the file.
    # Space Complexity: # O(F) to load file contents into memory.
    try:
        with open(file_path, "r", encoding="utf-8") as file_handle:
            parsed_data = json.load(file_handle)
            if isinstance(parsed_data, dict):
                return parsed_data
            else:
                logger.error(
                    "JSON root element in file %s is not a dictionary. Got type: %s",
                    file_path,
                    type(parsed_data).__name__
                )
                return {}
    except FileNotFoundError as file_not_found_error:
        logger.error(
            "The specified file was not found: %s. Error: %s",
            file_path,
            str(file_not_found_error)
        )
        return {}
    except json.JSONDecodeError as decode_error:
        logger.error(
            "Failed to decode JSON from file: %s. Error: %s",
            file_path,
            str(decode_error)
        )
        return {}
    except Exception as general_exception:
        logger.error(
            "An unexpected error occurred while reading file %s: %s",
            file_path,
            str(general_exception)
        )
        return {}


def print_patient_summary(patient: Patient, is_valid: bool, errors: List[str]) -> None:
    """
    Print a beautifully formatted console summary of the Patient data and validation status.

    Args:
        patient (Patient): The populated Patient model instance.
        is_valid (bool): Validation status.
        errors (List[str]): List of identified validation errors.
    """
    # Time Complexity: # O(D + M + E) where D is diagnoses, M is medications, E is validation errors.
    # Space Complexity: # O(1) as it prints directly to standard output.

    print("\n" + "=" * 50)
    print("           PATIENT INGESTION PIPELINE REPORT")
    print("=" * 50)

    # Replace PII fields with their hashed versions for protection
    patient_id_hashed = hash_sensitive_field(patient.patient_id)
    insurance_id_hashed = hash_sensitive_field(patient.insurance_id)

    print(f"Patient ID:    {patient_id_hashed or 'N/A'} [PROTECTED]")
    print(f"Full Name:     {patient.name or 'N/A'}")
    print(f"Insurance ID:  {insurance_id_hashed or 'N/A'} [PROTECTED]")

    print("\n--- Diagnoses ---")
    if patient.diagnoses:
        for index, diagnosis in enumerate(patient.diagnoses, 1):
            print(f"  {index}. {diagnosis}")
    else:
        print("  (None)")

    print("\n--- Medications ---")
    if patient.medications:
        for index, medication in enumerate(patient.medications, 1):
            print(f"  {index}. {medication}")
    else:
        print("  (None)")

    print("\n" + "-" * 50)
    if is_valid:
        print("STATUS: VALID")
    else:
        print(f"STATUS: INVALID ({len(errors)} validation errors discovered)")
        for index, error in enumerate(errors, 1):
            print(f"  [Error {index}] {error}")

    print("=" * 50 + "\n")


def main() -> None:
    """
    Main entry point for CLI argument parsing and pipeline execution.
    """
    parser = argparse.ArgumentParser(
        description="Ingest, parse, and validate deeply nested FHIR patient JSON payloads."
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the patient JSON file to ingest."
    )

    arguments = parser.parse_args()

    # 1. Ingest/Load raw data
    logger.info("Ingesting file: %s", arguments.file_path)
    raw_data = load_json_file(arguments.file_path)

    # 2. Parse raw dictionary to Patient Pydantic model
    logger.info("Parsing patient resource payload...")
    patient = parse_fhir_patient(raw_data)

    # 3. Validate parsed model
    logger.info("Running patient data quality validations...")
    is_valid, validation_errors = validate_patient(patient)

    # 4. Print report
    print_patient_summary(patient, is_valid, validation_errors)


if __name__ == "__main__":
    main()
