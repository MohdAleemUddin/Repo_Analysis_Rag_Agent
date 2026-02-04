"""Tests for prd_monitor coverage."""
from unittest.mock import MagicMock, patch

try:
    from app.confluence import prd_monitor
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "offline-folder-rag" / "edge_agent"))
    from app.confluence import prd_monitor


def test_record_analysis_duration():
    out = prd_monitor.record_analysis_duration_sec(1.0)
    assert out["ok"] is True


def test_record_template_select_duration():
    out = prd_monitor.record_template_select_duration_sec(1.0)
    assert out["ok"] is True


def test_record_creation_duration():
    out = prd_monitor.record_creation_duration_sec(5.0)
    assert out["ok"] is True


def test_record_memory_mb():
    out = prd_monitor.record_memory_mb(100)
    assert "value" in out


def test_check_prd():
    out = prd_monitor.check_prd()
    assert "analysis_target_sec" in out


def test_start_operation():
    op_id = prd_monitor.start_operation()
    assert op_id is not None


def test_get_current_record():
    rec = prd_monitor.get_current_record()
    assert rec is None or hasattr(rec, "operation_id")


def test_record_confluence_operation_missed_targets():
    rec = prd_monitor.record_confluence_operation(
        "op1", [4000], 3000, 20000, 350
    )
    assert rec.targets_met["analysis_per_file"] is False or rec.targets_met["template_selection"] is False


def test_append_record():
    rec = prd_monitor.PerformanceRecord(operation_id="x")
    prd_monitor.append_record(rec)
    records = prd_monitor.get_last_records(5)
    assert len(records) >= 1


def test_timer_per_file_analysis():
    with prd_monitor.timer_per_file_analysis(file_index=0):
        pass


def test_timer_template_selection():
    prd_monitor.start_operation()
    with prd_monitor.timer_template_selection():
        pass


def test_timer_create_e2e():
    prd_monitor.start_operation()
    with prd_monitor.timer_create_e2e():
        pass
