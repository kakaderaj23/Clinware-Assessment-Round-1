"""
Unit tests for verifying parser and validator behavior under various scenarios,
including happy paths, missing fields, nulls, and malformed structures.
"""

import unittest
from typing import Any, Dict
from models import Patient
from parser import parse_fhir_patient
from validator import validate_patient
from security import hash_sensitive_field


class TestPatientIngestionPipeline(unittest.TestCase):
    """
    Test suite containing test cases to evaluate the robustness
    of the FHIR patient data parser and validator.
    """

    def test_happy_path_direct_resource(self) -> None:
        """
        Test parsing and validation with a complete, valid Patient resource payload at root level.
        """
        payload: Dict[str, Any] = {
            "id": "PT-99482",
            "name": [
                {
                    "use": "official",
                    "given": ["Jane", "Marie"],
                    "family": "Doe",
                    "text": "Jane Marie Doe"
                }
            ],
            "diagnoses": ["Essential hypertension", "Type 2 diabetes mellitus"],
            "medications": ["Lisinopril 10mg", "Metformin 500mg"],
            "insurance_id": "INS-77621-A"
        }

        # Parsing
        patient = parse_fhir_patient(payload)
        self.assertEqual(patient.patient_id, "PT-99482")
        self.assertEqual(patient.name, "Jane Marie Doe")
        self.assertEqual(patient.diagnoses, ["Essential hypertension", "Type 2 diabetes mellitus"])
        self.assertEqual(patient.medications, ["Lisinopril 10mg", "Metformin 500mg"])
        self.assertEqual(patient.insurance_id, "INS-77621-A")

        # Validation
        is_valid, errors = validate_patient(patient)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_happy_path_nested_resource(self) -> None:
        """
        Test parsing of nested resource payloads (standard FHIR Bundle Entry format).
        """
        payload: Dict[str, Any] = {
            "fullUrl": "urn:uuid:88a7c-473d",
            "resource": {
                "id": "PT-nested-88",
                "name": [
                    {
                        "given": ["Robert"],
                        "family": "Johnson"
                    }
                ],
                "diagnoses": ["Acute sinusitis"],
                "medications": ["Amoxicillin"],
                "insurance": [
                    {
                        "id": "INS-NESTED-99"
                    }
                ]
            }
        }

        # Parsing
        patient = parse_fhir_patient(payload)
        self.assertEqual(patient.patient_id, "PT-nested-88")
        self.assertEqual(patient.name, "Robert Johnson")
        self.assertEqual(patient.diagnoses, ["Acute sinusitis"])
        self.assertEqual(patient.medications, ["Amoxicillin"])
        self.assertEqual(patient.insurance_id, "INS-NESTED-99")

        # Validation
        is_valid, errors = validate_patient(patient)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_missing_name_field(self) -> None:
        """
        Test parsing when the 'name' field is missing or an empty array.
        """
        payload: Dict[str, Any] = {
            "id": "PT-30302",
            "diagnoses": ["Hypertension"],
            "medications": ["Lisinopril"],
            "insurance_id": "INS-44"
        }

        # Parser should extract everything else, name defaults to None
        patient = parse_fhir_patient(payload)
        self.assertEqual(patient.patient_id, "PT-30302")
        self.assertIsNone(patient.name)

        # Validator should catch the missing name
        is_valid, errors = validate_patient(patient)
        self.assertFalse(is_valid)
        self.assertIn("missing name", errors)

    def test_empty_diagnoses_array(self) -> None:
        """
        Test parsing and validation when the diagnoses list is present but empty.
        """
        payload: Dict[str, Any] = {
            "id": "PT-30302",
            "name": [{"text": "Alice Smith"}],
            "diagnoses": [],
            "medications": ["Metformin"],
            "insurance_id": "INS-44"
        }

        # Parsing
        patient = parse_fhir_patient(payload)
        self.assertEqual(patient.diagnoses, [])

        # Validator should report empty diagnoses
        is_valid, errors = validate_patient(patient)
        self.assertFalse(is_valid)
        self.assertIn("empty diagnoses list", errors)

    def test_completely_empty_dict(self) -> None:
        """
        Test resilience to a completely empty dictionary payload.
        """
        payload: Dict[str, Any] = {}

        # Parsing should run smoothly and return a Patient with None and empty list defaults
        patient = parse_fhir_patient(payload)
        self.assertIsNone(patient.patient_id)
        self.assertIsNone(patient.name)
        self.assertEqual(patient.diagnoses, [])
        self.assertEqual(patient.medications, [])
        self.assertIsNone(patient.insurance_id)

        # Validator should capture all missing fields
        is_valid, errors = validate_patient(patient)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 5)
        self.assertIn("missing patient_id", errors)
        self.assertIn("missing name", errors)
        self.assertIn("empty diagnoses list", errors)
        self.assertIn("empty medications list", errors)
        self.assertIn("missing insurance_id", errors)

    def test_null_fields(self) -> None:
        """
        Test parsing when key fields contain explicit null (None) values.
        """
        payload: Dict[str, Any] = {
            "id": None,
            "name": None,
            "diagnoses": None,
            "medications": None,
            "insurance_id": None
        }

        # Parsing should handle nulls without crashing
        patient = parse_fhir_patient(payload)
        self.assertIsNone(patient.patient_id)
        self.assertIsNone(patient.name)
        self.assertEqual(patient.diagnoses, [])
        self.assertEqual(patient.medications, [])
        self.assertIsNone(patient.insurance_id)

        # Validator should raise all 5 errors
        is_valid, errors = validate_patient(patient)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 5)

    def test_malformed_input_types(self) -> None:
        """
        Test parsing when the root payload or nested structures have malformed types.
        """
        # 1. Payload itself is not a dictionary but a string
        patient_from_string = parse_fhir_patient("not-a-dict")  # type: ignore
        self.assertIsNone(patient_from_string.patient_id)

        # 2. Payload with name field as string instead of a list of human names
        payload_malformed_name: Dict[str, Any] = {
            "id": "PT-99",
            "name": "Jane Doe",  # malformed, FHIR name must be an array
            "diagnoses": "Hypertension",  # malformed, must be an array
            "medications": 12345,  # malformed, must be an array
            "insurance_id": ["INS-99"]  # malformed, must be a string
        }

        patient = parse_fhir_patient(payload_malformed_name)
        # Should gracefully fail extraction and fall back to defaults
        self.assertEqual(patient.patient_id, "PT-99")
        self.assertIsNone(patient.name)
        self.assertEqual(patient.diagnoses, [])
        self.assertEqual(patient.medications, [])
        self.assertIsNone(patient.insurance_id)

    def test_hash_sensitive_field_valid_input(self) -> None:
        """
        Verify that hash_sensitive_field returns a valid 64-character SHA-256 hex string for normal input.
        """
        raw_value = "PT-12345"
        hashed = hash_sensitive_field(raw_value)
        self.assertIsNotNone(hashed)
        self.assertEqual(len(hashed), 64)
        # Check that it consists of valid lowercase hexadecimal characters
        self.assertTrue(all(char in "0123456789abcdef" for char in hashed))
        # Known SHA-256 digest for "PT-12345"
        import hashlib
        expected = hashlib.sha256(raw_value.encode("utf-8")).hexdigest()
        self.assertEqual(hashed, expected)

    def test_hash_sensitive_field_empty_input(self) -> None:
        """
        Verify that hash_sensitive_field returns None when passed None or an empty string.
        """
        self.assertIsNone(hash_sensitive_field(None))
        self.assertIsNone(hash_sensitive_field(""))
        self.assertIsNone(hash_sensitive_field("   "))


if __name__ == "__main__":
    unittest.main()
