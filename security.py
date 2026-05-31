"""
This module provides PII data security utilities, specifically hashing routines
to support HIPAA-adjacent data protection of sensitive patient details.
"""

import hashlib
from typing import Optional


def hash_sensitive_field(value: Optional[str]) -> Optional[str]:
    """
    Hash a sensitive string value using standard SHA-256 for HIPAA-adjacent PII protection.

    If the value is None, empty, or contains only whitespace, returns None safely.
    Includes built-in idempotency to prevent double hashing if called sequentially.

    Args:
        value (Optional[str]): The sensitive data field value to protect.

    Returns:
        Optional[str]: The 64-character SHA-256 hex digest, or None if input is blank.
    """
    # Time Complexity: # O(N) where N is the length of the input value.
    # Space Complexity: # O(1) auxiliary space (returns a constant-sized 64-char string).

    if value is None:
        return None

    value_str = str(value).strip()
    if value_str == "":
        return None

    # Idempotency check: if the value is already a valid 64-character SHA-256 hex string, do not re-hash
    if len(value_str) == 64 and all(char in "0123456789abcdefABCDEF" for char in value_str):
        return value_str

    return hashlib.sha256(value_str.encode("utf-8")).hexdigest()
