"""
Confluence request validation (PRD §3.2, TC-DV-001, TC-DV-006).
Title: 1–255 chars; confidence: [0.0, 1.0].
"""

from __future__ import annotations

TITLE_MIN_LEN = 1
TITLE_MAX_LEN = 255
CONFIDENCE_MIN = 0.0
CONFIDENCE_MAX = 1.0


def validate_title(title: str | None) -> tuple[bool, str]:
    """
    Validate page title for Confluence. TC-DV-001: 0 invalid, 1 and 255 valid, 256 invalid.
    Returns (ok, error_message).
    """
    if title is None:
        return False, "Title required"
    n = len(title)
    if n == 0:
        return False, "Title required"
    if n > TITLE_MAX_LEN:
        return False, "Title too long"
    return True, ""


def validate_confidence(score: float | None) -> tuple[bool, str]:
    """
    Validate confidence score. TC-DV-006: 0.0, 0.5, 1.0 valid; 1.5 invalid (range [0.0, 1.0]).
    Returns (ok, error_message).
    """
    if score is None:
        return True, ""
    if not isinstance(score, (int, float)):
        return False, "Confidence must be a number"
    if score < CONFIDENCE_MIN or score > CONFIDENCE_MAX:
        return False, "Confidence must be between 0.0 and 1.0"
    return True, ""
