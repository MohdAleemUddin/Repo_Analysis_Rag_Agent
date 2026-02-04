# MCP orchestrator: single worker pool, same queue, RAG-first, lifecycle, progress, cancel, retry.

import time
from typing import Any, Callable

from . import confluence_tasks
from .task_queue import (
    MCPTask,
    FailureType,
    RAG_TASK_TYPES,
    CONFLUENCE_TASK_TYPES,
    dequeue,
    enqueue,
    re_enqueue,
    max_retries,
    is_empty,
)

# Lifecycle states (TC-ST-010): Queued -> Processing -> Success|Failure -> Learning (if successful)
LIFECYCLE_QUEUED = "queued"
LIFECYCLE_PROCESSING = "processing"
LIFECYCLE_SUCCESS = "success"
LIFECYCLE_FAILURE = "failure"
LIFECYCLE_LEARNING = "learning"

# Progress callback: (status: str, progress: float) -> None; used by existing chat progress UI.
# Cancel check: () -> bool; existing cancellation path.
_progress_callback: Callable[[str, str, float], None] | None = None
_cancel_check: Callable[[str], bool] | None = None  # task_id -> cancelled


def set_progress_callback(cb: Callable[[str, str, float], None] | None) -> None:
    global _progress_callback
    _progress_callback = cb


def set_cancel_check(check: Callable[[str], bool] | None) -> None:
    global _cancel_check
    _cancel_check = check


def _progress(task_id: str, status: str, value: float) -> None:
    if _progress_callback:
        _progress_callback(task_id, status, value)


def _is_cancelled(task_id: str) -> bool:
    if _cancel_check:
        return _cancel_check(task_id)
    return False


def _run_rag_task(task: MCPTask) -> dict[str, Any]:
    """Dispatch to existing RAG handlers by task_type. Stub when no handlers wired."""
    # Wire to existing RAG handlers (rag_query, rag_search, rag_overview, rag_index) when available.
    if task.task_type not in RAG_TASK_TYPES:
        return {"status": "error", "message": "unknown_rag_task", "result": None}
    # Stub: same contract as Confluence (progress/cancel via orchestrator).
    return {"status": "success", "result": {}}


def _run_task(task: MCPTask) -> dict[str, Any]:
    if task.is_rag():
        return _run_rag_task(task)
    if task.is_confluence():
        def progress_cb(phase: str, value: float) -> None:
            _progress(task.task_id, phase, value)

        def cancel_cb() -> bool:
            return task.cancelled or _is_cancelled(task.task_id)

        return confluence_tasks.run_confluence_task(task, progress_cb, cancel_cb)
    return {"status": "error", "message": "unknown_task_type", "result": None}


def _is_transient(result: dict[str, Any]) -> bool:
    msg = (result.get("message") or "").lower()
    return "network" in msg or "timeout" in msg or "rate_limit" in msg or "rate limit" in msg


def _is_rate_limit(result: dict[str, Any]) -> bool:
    msg = (result.get("message") or "").lower()
    return "rate_limit" in msg or "rate limit" in msg


def _exponential_backoff(attempt: int) -> None:
    if attempt <= 0:
        return
    time.sleep(min(2 ** attempt, 60))


def orchestrate() -> None:
    """Single worker loop: dequeue (RAG first, then Confluence), dispatch, lifecycle, progress, cancel, retry."""
    while not is_empty():
        task = dequeue()
        if task is None:
            break
        if task.cancelled or _is_cancelled(task.task_id):
            _progress(task.task_id, LIFECYCLE_FAILURE, 0.0)
            continue
        _progress(task.task_id, LIFECYCLE_PROCESSING, 0.0)
        result = _run_task(task)
        status = result.get("status", "error")
        if status == "cancelled":
            _progress(task.task_id, LIFECYCLE_FAILURE, 0.0)
            continue
        if status == "success":
            _progress(task.task_id, LIFECYCLE_SUCCESS, 1.0)
            if result.get("learning_trigger"):
                _progress(task.task_id, LIFECYCLE_LEARNING, 1.0)
            continue
        # Failure path
        if _is_transient(result) and task.retry_count < max_retries():
            if _is_rate_limit(result):
                _exponential_backoff(task.retry_count + 1)
            task.last_failure_type = FailureType.TRANSIENT
            re_enqueue(task)
            _progress(task.task_id, LIFECYCLE_QUEUED, 0.0)
            continue
        # Non-transient or max retries: fail fast; recovery = Retry after fix / Cancel
        task.last_failure_type = FailureType.NON_TRANSIENT
        _progress(task.task_id, LIFECYCLE_FAILURE, 0.0)
