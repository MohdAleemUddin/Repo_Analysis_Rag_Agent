"""Tests for MCP server: task_queue, orchestrator, confluence_tasks. Raise coverage for edge_agent/app/mcp_server."""

# pyright: reportMissingImports=false

import sys
from pathlib import Path
from unittest.mock import patch

# Ensure app is importable (conftest adds edge_agent; app is under edge_agent)
_root = Path(__file__).resolve().parent.parent
_edge = _root / "repo_analysis_rag" / "backend_confluence"
if str(_edge) not in sys.path:
    sys.path.insert(0, str(_edge))


# --- task_queue ---
def test_task_queue_constants():
    from app.mcp_server.task_queue import (
        RAG_QUERY,
        CONFLUENCE_INTELLIGENT_ANALYZE,
        RAG_TASK_TYPES,
        CONFLUENCE_TASK_TYPES,
        ALL_TASK_TYPES,
    )

    assert RAG_QUERY == "rag_query"
    assert CONFLUENCE_INTELLIGENT_ANALYZE == "confluence_intelligent_analyze"
    assert len(RAG_TASK_TYPES) == 4
    assert len(CONFLUENCE_TASK_TYPES) == 5
    assert RAG_TASK_TYPES | CONFLUENCE_TASK_TYPES == ALL_TASK_TYPES


def test_failure_type_enum():
    from app.mcp_server.task_queue import FailureType

    assert FailureType.TRANSIENT.value == "transient"
    assert FailureType.NON_TRANSIENT.value == "non_transient"


def test_mcp_task_is_rag_is_confluence():
    from app.mcp_server.task_queue import (
        MCPTask,
        RAG_QUERY,
        CONFLUENCE_INTELLIGENT_ANALYZE,
    )

    rag = MCPTask(task_id="1", task_type=RAG_QUERY)
    assert rag.is_rag() is True
    assert rag.is_confluence() is False
    cf = MCPTask(task_id="2", task_type=CONFLUENCE_INTELLIGENT_ANALYZE)
    assert cf.is_rag() is False
    assert cf.is_confluence() is True


def test_enqueue_dequeue_rag_first_then_confluence():
    from app.mcp_server.task_queue import (
        MCPTask,
        RAG_QUERY,
        CONFLUENCE_INTELLIGENT_ANALYZE,
        enqueue,
        dequeue,
        is_empty,
    )

    # Empty
    assert is_empty() is True
    assert dequeue() is None
    # Enqueue Confluence then RAG; dequeue should give RAG first
    enqueue(MCPTask(task_id="c1", task_type=CONFLUENCE_INTELLIGENT_ANALYZE))
    enqueue(MCPTask(task_id="r1", task_type=RAG_QUERY))
    assert is_empty() is False
    t = dequeue()
    assert t is not None and t.task_type == RAG_QUERY and t.task_id == "r1"
    t2 = dequeue()
    assert (
        t2 is not None
        and t2.task_type == CONFLUENCE_INTELLIGENT_ANALYZE
        and t2.task_id == "c1"
    )
    assert is_empty() is True
    assert dequeue() is None


def test_enqueue_confluence_high_priority_before_normal():
    from app.mcp_server.task_queue import (
        MCPTask,
        CONFLUENCE_INTELLIGENT_ANALYZE,
        enqueue,
        dequeue,
        is_empty,
    )

    enqueue(
        MCPTask(
            task_id="n1", task_type=CONFLUENCE_INTELLIGENT_ANALYZE, high_priority=False
        )
    )
    enqueue(
        MCPTask(
            task_id="h1", task_type=CONFLUENCE_INTELLIGENT_ANALYZE, high_priority=True
        )
    )
    t1 = dequeue()
    assert t1 is not None and t1.task_id == "h1" and t1.high_priority is True
    t2 = dequeue()
    assert t2 is not None and t2.task_id == "n1"
    assert is_empty() is True


def test_enqueue_ignores_unknown_task_type():
    from app.mcp_server.task_queue import MCPTask, enqueue, is_empty, dequeue

    enqueue(MCPTask(task_id="x", task_type="unknown_type"))
    assert is_empty() is True
    assert dequeue() is None


def test_re_enqueue_max_retries():
    from app.mcp_server.task_queue import (
        MCPTask,
        RAG_QUERY,
        enqueue,
        dequeue,
        re_enqueue,
        max_retries,
    )

    assert max_retries() == 3
    t = MCPTask(task_id="r", task_type=RAG_QUERY, retry_count=0)
    enqueue(t)
    t2 = dequeue()
    assert t2 is not None and t2.retry_count == 0
    re_enqueue(t2)
    t3 = dequeue()
    assert t3 is not None and t3.retry_count == 1


# --- confluence_tasks ---
def test_run_confluence_task_analyze():
    from app.mcp_server.confluence_tasks import run_confluence_task
    from app.mcp_server.task_queue import MCPTask, CONFLUENCE_INTELLIGENT_ANALYZE

    task = MCPTask(task_id="a1", task_type=CONFLUENCE_INTELLIGENT_ANALYZE, params={})
    out = run_confluence_task(task)
    assert out["status"] == "success"
    assert out.get("result", {}).get("analyzed") is True


def test_run_confluence_task_match_format_create():
    from app.mcp_server.confluence_tasks import run_confluence_task
    from app.mcp_server.task_queue import (
        MCPTask,
        CONFLUENCE_INTELLIGENT_MATCH,
        CONFLUENCE_INTELLIGENT_FORMAT,
        CONFLUENCE_INTELLIGENT_CREATE,
    )

    for task_type in (
        CONFLUENCE_INTELLIGENT_MATCH,
        CONFLUENCE_INTELLIGENT_FORMAT,
        CONFLUENCE_INTELLIGENT_CREATE,
    ):
        task = MCPTask(task_id="x", task_type=task_type, params={})
        out = run_confluence_task(task)
        assert out["status"] == "success"
    task_create = MCPTask(
        task_id="c1", task_type=CONFLUENCE_INTELLIGENT_CREATE, params={}
    )
    out_create = run_confluence_task(task_create)
    assert out_create.get("learning_trigger") is True


def test_run_confluence_task_with_progress_and_cancel():
    from app.mcp_server.confluence_tasks import run_confluence_task
    from app.mcp_server.task_queue import MCPTask, CONFLUENCE_INTELLIGENT_ANALYZE

    progress_log = []

    def progress_cb(phase: str, value: float):
        progress_log.append((phase, value))

    task = MCPTask(task_id="a1", task_type=CONFLUENCE_INTELLIGENT_ANALYZE, params={})
    out = run_confluence_task(
        task, progress_callback=progress_cb, cancel_check=lambda: False
    )
    assert out["status"] == "success"
    assert len(progress_log) >= 1
    out_cancel = run_confluence_task(
        task, progress_callback=None, cancel_check=lambda: True
    )
    assert out_cancel["status"] == "cancelled"


def test_run_confluence_task_unknown_type():
    from app.mcp_server.confluence_tasks import run_confluence_task
    from app.mcp_server.task_queue import MCPTask

    task = MCPTask(task_id="u1", task_type="confluence_unknown_type", params={})
    out = run_confluence_task(task)
    assert out["status"] == "error"
    assert out.get("message") == "unknown_confluence_task"


def test_run_confluence_task_cancel_in_match_format_create():
    from app.mcp_server.confluence_tasks import (
        confluence_intelligent_match,
        confluence_intelligent_format,
        confluence_intelligent_create,
    )
    from app.mcp_server.task_queue import (
        MCPTask,
        CONFLUENCE_INTELLIGENT_MATCH,
        CONFLUENCE_INTELLIGENT_FORMAT,
        CONFLUENCE_INTELLIGENT_CREATE,
    )

    for fn, tt in [
        (confluence_intelligent_match, CONFLUENCE_INTELLIGENT_MATCH),
        (confluence_intelligent_format, CONFLUENCE_INTELLIGENT_FORMAT),
        (confluence_intelligent_create, CONFLUENCE_INTELLIGENT_CREATE),
    ]:
        t = MCPTask(task_id="c", task_type=tt, params={})
        r = fn(t, cancel_check=lambda: True)
        assert r["status"] == "cancelled"


def test_confluence_intelligent_entry_points():
    from app.mcp_server.confluence_tasks import (
        confluence_intelligent_analyze,
        confluence_intelligent_match,
        confluence_intelligent_format,
        confluence_intelligent_create,
    )
    from app.mcp_server.task_queue import (
        MCPTask,
        CONFLUENCE_INTELLIGENT_ANALYZE,
        CONFLUENCE_INTELLIGENT_MATCH,
        CONFLUENCE_INTELLIGENT_FORMAT,
        CONFLUENCE_INTELLIGENT_CREATE,
    )

    for fn, tt in [
        (confluence_intelligent_analyze, CONFLUENCE_INTELLIGENT_ANALYZE),
        (confluence_intelligent_match, CONFLUENCE_INTELLIGENT_MATCH),
        (confluence_intelligent_format, CONFLUENCE_INTELLIGENT_FORMAT),
        (confluence_intelligent_create, CONFLUENCE_INTELLIGENT_CREATE),
    ]:
        t = MCPTask(task_id="e", task_type=tt, params={})
        r = fn(t)
        assert r["status"] == "success"


# --- orchestrator ---
def test_orchestrator_lifecycle_success():
    from app.mcp_server.task_queue import (
        MCPTask,
        CONFLUENCE_INTELLIGENT_ANALYZE,
        enqueue,
        is_empty,
    )
    from app.mcp_server.orchestrator import (
        orchestrate,
        set_progress_callback,
        set_cancel_check,
        LIFECYCLE_PROCESSING,
        LIFECYCLE_SUCCESS,
    )

    progress_log = []
    set_progress_callback(
        lambda tid, status, value: progress_log.append((tid, status, value))
    )
    set_cancel_check(lambda _: False)
    enqueue(MCPTask(task_id="o1", task_type=CONFLUENCE_INTELLIGENT_ANALYZE, params={}))
    orchestrate()
    statuses = [p[1] for p in progress_log]
    assert LIFECYCLE_PROCESSING in statuses
    assert LIFECYCLE_SUCCESS in statuses
    assert is_empty() is True


def test_orchestrator_lifecycle_learning_trigger():
    from app.mcp_server.task_queue import (
        MCPTask,
        CONFLUENCE_INTELLIGENT_CREATE,
        enqueue,
    )
    from app.mcp_server.orchestrator import (
        orchestrate,
        set_progress_callback,
        set_cancel_check,
        LIFECYCLE_LEARNING,
    )

    progress_log = []
    set_progress_callback(
        lambda tid, status, value: progress_log.append((tid, status, value))
    )
    set_cancel_check(lambda _: False)
    enqueue(
        MCPTask(task_id="learn1", task_type=CONFLUENCE_INTELLIGENT_CREATE, params={})
    )
    orchestrate()
    statuses = [p[1] for p in progress_log]
    assert LIFECYCLE_LEARNING in statuses


def test_orchestrator_cancelled_task():
    from app.mcp_server.task_queue import (
        MCPTask,
        CONFLUENCE_INTELLIGENT_ANALYZE,
        enqueue,
        is_empty,
    )
    from app.mcp_server.orchestrator import (
        orchestrate,
        set_progress_callback,
        set_cancel_check,
        LIFECYCLE_FAILURE,
    )

    progress_log = []
    set_progress_callback(
        lambda tid, status, value: progress_log.append((tid, status, value))
    )
    set_cancel_check(lambda tid: tid == "cancel1")
    enqueue(
        MCPTask(task_id="cancel1", task_type=CONFLUENCE_INTELLIGENT_ANALYZE, params={})
    )
    orchestrate()
    statuses = [p[1] for p in progress_log]
    assert LIFECYCLE_FAILURE in statuses
    assert is_empty() is True


def test_orchestrator_rag_task_stub():
    from app.mcp_server.task_queue import MCPTask, RAG_QUERY, enqueue
    from app.mcp_server.orchestrator import (
        orchestrate,
        set_progress_callback,
        set_cancel_check,
        LIFECYCLE_SUCCESS,
    )

    progress_log = []
    set_progress_callback(
        lambda tid, status, value: progress_log.append((tid, status, value))
    )
    set_cancel_check(lambda _: False)
    enqueue(MCPTask(task_id="rag1", task_type=RAG_QUERY, params={}))
    orchestrate()
    statuses = [p[1] for p in progress_log]
    assert LIFECYCLE_SUCCESS in statuses


def test_orchestrator_transient_retry_then_fail():
    from app.mcp_server.task_queue import (
        MCPTask,
        CONFLUENCE_INTELLIGENT_ANALYZE,
        enqueue,
    )
    from app.mcp_server.orchestrator import (
        orchestrate,
        set_progress_callback,
        set_cancel_check,
    )

    progress_log = []
    set_progress_callback(
        lambda tid, status, value: progress_log.append((tid, status, value))
    )
    set_cancel_check(lambda _: False)
    call_count = [0]

    def failing_task(t, progress_cb=None, cancel_check=None):
        call_count[0] += 1
        if call_count[0] <= 2:
            return {"status": "error", "message": "network timeout", "result": None}
        return {"status": "success", "result": {}}

    with patch(
        "app.mcp_server.orchestrator.confluence_tasks.run_confluence_task",
        side_effect=failing_task,
    ):
        enqueue(
            MCPTask(
                task_id="retry1", task_type=CONFLUENCE_INTELLIGENT_ANALYZE, params={}
            )
        )
        with patch("app.mcp_server.orchestrator._exponential_backoff"):  # avoid sleep
            orchestrate()
    assert call_count[0] >= 2


def test_orchestrator_non_transient_fail_fast():
    from app.mcp_server.task_queue import (
        MCPTask,
        CONFLUENCE_INTELLIGENT_ANALYZE,
        enqueue,
        is_empty,
    )
    from app.mcp_server.orchestrator import (
        orchestrate,
        set_progress_callback,
        set_cancel_check,
        LIFECYCLE_FAILURE,
    )

    progress_log = []
    set_progress_callback(
        lambda tid, status, value: progress_log.append((tid, status, value))
    )
    set_cancel_check(lambda _: False)

    def auth_fail(*args, **kwargs):
        return {"status": "error", "message": "auth invalid", "result": None}

    with patch(
        "app.mcp_server.orchestrator.confluence_tasks.run_confluence_task",
        side_effect=auth_fail,
    ):
        enqueue(
            MCPTask(
                task_id="auth1", task_type=CONFLUENCE_INTELLIGENT_ANALYZE, params={}
            )
        )
        orchestrate()
    statuses = [p[1] for p in progress_log]
    assert LIFECYCLE_FAILURE in statuses
    assert is_empty() is True


def test_orchestrator_rate_limit_backoff():
    from app.mcp_server.task_queue import (
        MCPTask,
        CONFLUENCE_INTELLIGENT_ANALYZE,
        enqueue,
    )
    from app.mcp_server.orchestrator import (
        orchestrate,
        set_progress_callback,
        set_cancel_check,
    )

    set_progress_callback(None)
    set_cancel_check(lambda _: False)
    call_count = [0]

    def rate_limit_then_ok(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            return {"status": "error", "message": "rate_limit exceeded", "result": None}
        return {"status": "success", "result": {}}

    with patch(
        "app.mcp_server.orchestrator.confluence_tasks.run_confluence_task",
        side_effect=rate_limit_then_ok,
    ):
        with patch("app.mcp_server.orchestrator._exponential_backoff") as mock_backoff:
            enqueue(
                MCPTask(
                    task_id="rl1", task_type=CONFLUENCE_INTELLIGENT_ANALYZE, params={}
                )
            )
            orchestrate()
            mock_backoff.assert_called()


# --- main.py ---
def test_main_runs_mcp_flow(capsys):
    app_dir = str(_edge / "app")
    if app_dir not in sys.path:
        sys.path.insert(1, app_dir)
    from app.main import main

    main()
    out = capsys.readouterr().out
    assert "Edge agent: MCP run complete" in out
    assert "processing" in out or "success" in out or "analyzing" in out


# --- mcp_server __init__ ---
def test_mcp_server_init_exports():
    from app.mcp_server import (
        RAG_QUERY,
        CONFLUENCE_INTELLIGENT_ANALYZE,
        MCPTask,
        set_progress_callback,
        set_cancel_check,
        LIFECYCLE_QUEUED,
        confluence_tasks,
    )

    assert RAG_QUERY == "rag_query"
    assert CONFLUENCE_INTELLIGENT_ANALYZE == "confluence_intelligent_analyze"
    assert MCPTask(task_id="i", task_type=RAG_QUERY).is_rag()
    set_progress_callback(None)
    set_cancel_check(None)
    assert LIFECYCLE_QUEUED == "queued"
    assert hasattr(confluence_tasks, "run_confluence_task")
