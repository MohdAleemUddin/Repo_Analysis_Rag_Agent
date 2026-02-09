# TC-BVA-011 through TC-BVA-014: Strict NFR1 performance regression tests.
# Regression: CI fails if NFR1 thresholds are violated. No buffers, no false positives.
"""Strict performance regression suite for US-8. Zero false positives."""

import pytest

pytestmark = [pytest.mark.performance, pytest.mark.performance_regression]

try:
    from offline_folder_rag.edge_agent.app.confluence.prd_monitor import (
        record_analysis_duration_sec,
        record_template_select_duration_sec,
        record_creation_duration_sec,
        record_memory_mb,
        record_confluence_operation,
        verify_targets_met,
        PerformanceRecord,
        check_prd,
    )
    from offline_folder_rag.edge_agent.app.config.config import (
        ANALYSIS_MAX_SECONDS_PER_FILE,
        TEMPLATE_SELECTION_MAX_SECONDS,
        CREATE_E2E_MAX_SECONDS,
        CONFLUENCE_MEMORY_LIMIT_MB,
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "offline-folder-rag" / "edge_agent"))
    from app.confluence.prd_monitor import (
        record_analysis_duration_sec,
        record_template_select_duration_sec,
        record_creation_duration_sec,
        record_memory_mb,
        record_confluence_operation,
        verify_targets_met,
        PerformanceRecord,
        check_prd,
    )
    from app.config.config import (
        ANALYSIS_MAX_SECONDS_PER_FILE,
        TEMPLATE_SELECTION_MAX_SECONDS,
        CREATE_E2E_MAX_SECONDS,
        CONFLUENCE_MEMORY_LIMIT_MB,
    )


def test_regression_analysis_target_strict() -> None:
    """TC-BVA-011: Strict boundary - 2.99s passes, 3.0s/3.01s fail."""
    out_pass = record_analysis_duration_sec(2.99)
    assert out_pass["ok"], "2.99s must pass"
    out_fail = record_analysis_duration_sec(3.0)
    assert not out_fail["ok"], "3.0s must fail (strict < 3s)"
    out_fail2 = record_analysis_duration_sec(3.01)
    assert not out_fail2["ok"], "3.01s must fail"


def test_regression_template_target_strict() -> None:
    """TC-BVA-012: Strict boundary - 1.99s passes, 2.0s/2.01s fail."""
    out_pass = record_template_select_duration_sec(1.99)
    assert out_pass["ok"], "1.99s must pass"
    out_fail = record_template_select_duration_sec(2.0)
    assert not out_fail["ok"], "2.0s must fail (strict < 2s)"
    out_fail2 = record_template_select_duration_sec(2.01)
    assert not out_fail2["ok"], "2.01s must fail"


def test_regression_creation_target_strict() -> None:
    """TC-BVA-013: Strict boundary - 14.99s passes, 15.0s/15.01s fail."""
    out_pass = record_creation_duration_sec(14.99)
    assert out_pass["ok"], "14.99s must pass"
    out_fail = record_creation_duration_sec(15.0)
    assert not out_fail["ok"], "15.0s must fail (strict < 15s)"
    out_fail2 = record_creation_duration_sec(15.01)
    assert not out_fail2["ok"], "15.01s must fail"


def test_regression_memory_target_strict() -> None:
    """TC-BVA-014: Strict boundary - 300.0 MB passes, 300.1 MB fails."""
    out_pass = record_memory_mb(300.0)
    assert out_pass["ok"], "300.0 MB must pass (<= 300)"
    out_fail = record_memory_mb(300.1)
    assert not out_fail["ok"], "300.1 MB must fail"


def test_regression_config_matches_prd() -> None:
    """Config values match PRD NFR1 exactly."""
    assert ANALYSIS_MAX_SECONDS_PER_FILE == 3
    assert TEMPLATE_SELECTION_MAX_SECONDS == 2
    assert CREATE_E2E_MAX_SECONDS == 15
    assert CONFLUENCE_MEMORY_LIMIT_MB == 300
    targets = check_prd()
    assert targets["analysis_target_sec"] == 3
    assert targets["template_select_target_sec"] == 2
    assert targets["creation_target_sec"] == 15
    assert targets["memory_target_mb"] == 300


def test_regression_verify_targets_met() -> None:
    """verify_targets_met returns True only when all targets met."""
    rec_ok = PerformanceRecord(
        operation_id="ok",
        per_file_analysis_ms=[100.0],
        template_selection_ms=500.0,
        create_e2e_ms=2000.0,
        peak_memory_mb=150.0,
        targets_met={
            "analysis_per_file": True,
            "template_selection": True,
            "create_e2e": True,
            "memory": True,
        },
    )
    assert verify_targets_met(rec_ok)

    rec_fail = PerformanceRecord(
        operation_id="fail",
        per_file_analysis_ms=[4000.0],
        template_selection_ms=500.0,
        create_e2e_ms=2000.0,
        peak_memory_mb=150.0,
        targets_met={
            "analysis_per_file": False,
            "template_selection": True,
            "create_e2e": True,
            "memory": True,
        },
    )
    assert not verify_targets_met(rec_fail)

    assert not verify_targets_met(None)


def test_regression_record_confluence_operation_targets() -> None:
    """record_confluence_operation sets targets_met correctly at boundaries."""
    # All within limits
    rec = record_confluence_operation(
        operation_id="boundary",
        per_file_analysis_ms=[2999.0],
        template_selection_ms=1999.0,
        create_e2e_ms=14999.0,
        peak_memory_mb=300.0,
    )
    assert rec.targets_met["analysis_per_file"]
    assert rec.targets_met["template_selection"]
    assert rec.targets_met["create_e2e"]
    assert rec.targets_met["memory"]

    # Analysis at 3000ms fails
    rec2 = record_confluence_operation(
        operation_id="over",
        per_file_analysis_ms=[3000.0],
        template_selection_ms=100.0,
        create_e2e_ms=100.0,
        peak_memory_mb=100.0,
    )
    assert not rec2.targets_met["analysis_per_file"]
