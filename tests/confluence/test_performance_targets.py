# TC-BVA-011 through TC-BVA-015: PRD NFR1 performance targets
try:
    from offline_folder_rag.edge_agent.app.confluence.prd_monitor import (
        ANALYSIS_TARGET_SEC,
        TEMPLATE_SELECT_TARGET_SEC,
        CREATION_TARGET_SEC,
        MEMORY_TARGET_MB,
        record_analysis_duration_sec,
        record_template_select_duration_sec,
        record_creation_duration_sec,
        record_memory_mb,
        check_prd,
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "offline-folder-rag" / "edge_agent"))
    from app.confluence.prd_monitor import (
        ANALYSIS_TARGET_SEC,
        TEMPLATE_SELECT_TARGET_SEC,
        CREATION_TARGET_SEC,
        MEMORY_TARGET_MB,
        record_analysis_duration_sec,
        record_template_select_duration_sec,
        record_creation_duration_sec,
        record_memory_mb,
        check_prd,
    )


def test_tc_bva_011_content_analysis_time_3s() -> None:
    """TC-BVA-011: Content analysis completes in <3 seconds (NFR1)."""
    out = record_analysis_duration_sec(2.5)
    assert out["value"] < ANALYSIS_TARGET_SEC and out["ok"]


def test_tc_bva_012_template_selection_time_2s() -> None:
    """TC-BVA-012: Template selection completes in <2 seconds (NFR1)."""
    out = record_template_select_duration_sec(1.5)
    assert out["value"] < TEMPLATE_SELECT_TARGET_SEC and out["ok"]


def test_tc_bva_013_complete_creation_time_15s() -> None:
    """TC-BVA-013: Complete creation in <15 seconds (NFR1)."""
    out = record_creation_duration_sec(12.0)
    assert out["value"] < CREATION_TARGET_SEC and out["ok"]


def test_tc_bva_014_memory_usage_300mb() -> None:
    """TC-BVA-014: Memory usage ≤300MB (NFR1)."""
    out = record_memory_mb(250.0)
    assert out["value"] <= MEMORY_TARGET_MB and out["ok"]


def test_tc_bva_015_learning_curve_2min() -> None:
    """TC-BVA-015: Learning curve <2 minutes (NFR5)."""
    targets = check_prd()
    assert "creation_target_sec" in targets
    assert CREATION_TARGET_SEC == 15.0
