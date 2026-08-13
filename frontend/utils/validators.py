import re
from typing import Optional


def validate_phone(phone: str) -> Optional[str]:
    """Validate Egyptian phone number. Returns error message or None."""
    cleaned = phone.strip().replace(" ", "").replace("-", "")
    if not re.match(r"^(010|011|012|015)\d{8}$", cleaned):
        return "Phone must be a valid Egyptian mobile number (e.g. 01012345678)"
    return None


def validate_email(email: str) -> Optional[str]:
    """Validate email address. Returns error message or None."""
    if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()):
        return "Please enter a valid email address"
    return None


def validate_required(value: str, field_name: str) -> Optional[str]:
    """Check that a required field is not empty."""
    if not value or not str(value).strip():
        return f"{field_name} is required"
    return None


def validate_min_length(value: str, field_name: str, min_len: int) -> Optional[str]:
    if len(value.strip()) < min_len:
        return f"{field_name} must be at least {min_len} characters"
    return None
