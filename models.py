"""
This module defines the Patient data model representing core patient information
extracted from messy, nested healthcare FHIR-style JSON payloads.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Patient(BaseModel):
    """
    Pydantic data model representing a Patient.

    All fields are strictly optional to accommodate highly variable
    and incomplete FHIR payloads.
    """
    patient_id: Optional[str] = Field(
        default=None,
        description="The unique identifier for the patient."
    )
    name: Optional[str] = Field(
        default=None,
        description="The full name of the patient."
    )
    diagnoses: List[str] = Field(
        default_factory=list,
        description="List of patient diagnoses."
    )
    medications: List[str] = Field(
        default_factory=list,
        description="List of active medications prescribed to the patient."
    )
    insurance_id: Optional[str] = Field(
        default=None,
        description="The insurance policy or member identifier."
    )
