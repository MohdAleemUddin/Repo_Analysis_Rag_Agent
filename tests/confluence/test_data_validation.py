"""
Data validation tests: TC-DV-001 (title), TC-DV-006 (confidence), TC-DV-010 (intelligence metrics).
"""
import pytest

# Import from edge_agent; path may vary by run context
try:
    from offline_folder_rag.edge_agent.app.confluence.validation import (
        validate_title,
        validate_confidence,
        TITLE_MAX_LEN,
        CONFIDENCE_MIN,
        CONFIDENCE_MAX,
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "offline-folder-rag" / "edge_agent"))
    from app.confluence.validation import (
        validate_title,
        validate_confidence,
        TITLE_MAX_LEN,
        CONFIDENCE_MIN,
        CONFIDENCE_MAX,
    )


# --- TC-DV-001: Title field validation (0, 1, 255, 256 chars) ---
def test_tc_dv_001_title_0_chars_rejected() -> None:
    ok, msg = validate_title("")
    assert not ok
    assert "Title" in msg or "required" in msg.lower()


def test_tc_dv_001_title_none_rejected() -> None:
    ok, _ = validate_title(None)
    assert not ok


def test_tc_dv_001_title_1_char_accepted() -> None:
    ok, msg = validate_title("A")
    assert ok, msg
    assert msg == ""


def test_tc_dv_001_title_255_chars_accepted() -> None:
    title = "x" * TITLE_MAX_LEN
    ok, msg = validate_title(title)
    assert ok, msg
    assert msg == ""


def test_tc_dv_001_title_256_chars_rejected() -> None:
    title = "x" * (TITLE_MAX_LEN + 1)
    ok, msg = validate_title(title)
    assert not ok
    assert "long" in msg.lower() or "255" in msg


# --- TC-DV-006: Confidence scores validation (0.0, 0.5, 1.0, 1.5) ---
def test_tc_dv_006_confidence_0_accepted() -> None:
    ok, msg = validate_confidence(0.0)
    assert ok, msg


def test_tc_dv_006_confidence_0_5_accepted() -> None:
    ok, msg = validate_confidence(0.5)
    assert ok, msg


def test_tc_dv_006_confidence_1_0_accepted() -> None:
    ok, msg = validate_confidence(1.0)
    assert ok, msg


def test_tc_dv_006_confidence_1_5_rejected() -> None:
    ok, msg = validate_confidence(1.5)
    assert not ok
    assert "0" in msg and "1" in msg or "between" in msg.lower()


def test_tc_dv_006_confidence_negative_rejected() -> None:
    ok, _ = validate_confidence(-0.1)
    assert not ok


def test_tc_dv_006_confidence_none_accepted() -> None:
    ok, msg = validate_confidence(None)
    assert ok
    assert msg == ""


def test_tc_dv_006_confidence_non_number_rejected() -> None:
    ok, msg = validate_confidence("not a number")
    assert not ok
    assert "number" in msg.lower()


# --- TC-DV-010: Intelligence metrics validation - all intelligence fields valid ---
def test_tc_dv_010_confidence_bounds_constants() -> None:
    """Schema and validation use consistent bounds; DECIMAL(3,2) allows 0.00-9.99, we enforce [0,1]."""
    assert CONFIDENCE_MIN == 0.0
    assert CONFIDENCE_MAX == 1.0


def test_tc_dv_010_title_max_length_constant() -> None:
    """Title max 255 for DB VARCHAR(255) and API validation."""
    assert TITLE_MAX_LEN == 255


def test_tc_dv_010_intelligence_fields_valid_mid_range() -> None:
    """Valid confidence in mid range and valid title; both pass."""
    ok1, _ = validate_confidence(0.94)
    ok2, _ = validate_title("API Service Setup & Configuration")
    assert ok1 and ok2
