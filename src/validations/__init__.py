"""Validation utilities."""
from ..types import ValidationResponse, ValidationResult


def has_failed_validation(responses: list[ValidationResponse]) -> bool:
    """Check if any validation has failed."""
    return any(r.result == ValidationResult.FAILED for r in responses)