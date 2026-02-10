# Confluence tasks: four intelligent task runners, same queue/orchestrator.

from typing import Any, Callable

from .task_queue import (
    CONFLUENCE_INTELLIGENT_ANALYZE,
    CONFLUENCE_INTELLIGENT_MATCH,
    CONFLUENCE_INTELLIGENT_FORMAT,
    CONFLUENCE_INTELLIGENT_CREATE,
    CONFLUENCE_DOCUMENT_PROJECT,
    MCPTask,
)


def _run_confluence_task(
    task: MCPTask,
    progress_callback: Callable[[str, float], None] | None,
    cancel_check: Callable[[], bool] | None,
) -> dict[str, Any]:
    """Unified runner: runs the appropriate Confluence task by type. No tokens in logs; HTTPS/TLS via existing auth."""
    if cancel_check and cancel_check():
        return {"status": "cancelled", "result": None}
    if progress_callback:
        progress_callback("processing", 0.0)
    task_type = task.task_type
    params = task.params
    if task_type == CONFLUENCE_INTELLIGENT_ANALYZE:
        return _confluence_intelligent_analyze(params, progress_callback, cancel_check)
    if task_type == CONFLUENCE_INTELLIGENT_MATCH:
        return _confluence_intelligent_match(params, progress_callback, cancel_check)
    if task_type == CONFLUENCE_INTELLIGENT_FORMAT:
        return _confluence_intelligent_format(params, progress_callback, cancel_check)
    if task_type == CONFLUENCE_INTELLIGENT_CREATE:
        return _confluence_intelligent_create(params, progress_callback, cancel_check)
    if task_type == CONFLUENCE_DOCUMENT_PROJECT:
        return _confluence_document_project(params, progress_callback, cancel_check)
    return {"status": "error", "message": "unknown_confluence_task", "result": None}


def confluence_intelligent_analyze(
    task: MCPTask,
    progress_callback: Callable[[str, float], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Analyse content with AI. Same payload/callbacks as other Confluence tasks."""
    return _run_confluence_task(task, progress_callback, cancel_check)


def confluence_intelligent_match(
    task: MCPTask,
    progress_callback: Callable[[str, float], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Find best template intelligently."""
    return _run_confluence_task(task, progress_callback, cancel_check)


def confluence_intelligent_format(
    task: MCPTask,
    progress_callback: Callable[[str, float], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Apply formatting intelligently."""
    return _run_confluence_task(task, progress_callback, cancel_check)


def confluence_intelligent_create(
    task: MCPTask,
    progress_callback: Callable[[str, float], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Create page with intelligence. Downstream learning hook may be triggered on success."""
    return _run_confluence_task(task, progress_callback, cancel_check)


def confluence_document_project(
    task: MCPTask,
    progress_callback: Callable[[str, float], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """US-16: Document project via full pipeline (scan, analyze, match, format, create)."""
    return _run_confluence_task(task, progress_callback, cancel_check)


def run_confluence_task(
    task: MCPTask,
    progress_callback: Callable[[str, float], None] | None = None,
    cancel_check: Callable[[], bool] | None = None,
) -> dict[str, Any]:
    """Single entry for orchestrator: dispatch by task_type to the four Confluence runners."""
    return _run_confluence_task(task, progress_callback, cancel_check)


# Stub implementations: call agents when wired; no tokens in logs; project isolation from task.params.
def _confluence_intelligent_analyze(
    params: dict[str, Any],
    progress_callback: Callable[[str, float], None] | None,
    cancel_check: Callable[[], bool] | None,
) -> dict[str, Any]:
    if cancel_check and cancel_check():
        return {"status": "cancelled", "result": None}
    if progress_callback:
        progress_callback("analyzing", 0.5)
    # Stub: agent call here; use params for project/content; existing auth, HTTPS/TLS.
    return {"status": "success", "result": {"analyzed": True}}


def _confluence_intelligent_match(
    params: dict[str, Any],
    progress_callback: Callable[[str, float], None] | None,
    cancel_check: Callable[[], bool] | None,
) -> dict[str, Any]:
    if cancel_check and cancel_check():
        return {"status": "cancelled", "result": None}
    if progress_callback:
        progress_callback("matching", 0.5)
    return {"status": "success", "result": {"template_matched": True}}


def _confluence_intelligent_format(
    params: dict[str, Any],
    progress_callback: Callable[[str, float], None] | None,
    cancel_check: Callable[[], bool] | None,
) -> dict[str, Any]:
    if cancel_check and cancel_check():
        return {"status": "cancelled", "result": None}
    if progress_callback:
        progress_callback("formatting", 0.5)
    return {"status": "success", "result": {"formatted": True}}


def _confluence_intelligent_create(
    params: dict[str, Any],
    progress_callback: Callable[[str, float], None] | None,
    cancel_check: Callable[[], bool] | None,
) -> dict[str, Any]:
    if cancel_check and cancel_check():
        return {"status": "cancelled", "result": None}
    if progress_callback:
        progress_callback("creating", 0.5)
    # On success, downstream may emit Learning state; no new learning subsystem here.
    return {"status": "success", "result": {"created": True}, "learning_trigger": True}


def _confluence_document_project(
    params: dict[str, Any],
    progress_callback: Callable[[str, float], None] | None,
    cancel_check: Callable[[], bool] | None,
) -> dict[str, Any]:
    """US-16: Run document-project pipeline (scan, analyze, match, format, create)."""
    if cancel_check and cancel_check():
        return {"status": "cancelled", "result": None}
    try:
        from app.agents.coordinator import run_document_project

        workspace_path = (
            params.get("workspace_path") or params.get("workspacePath") or ""
        )
        space_key = params.get("space") or params.get("space_key", "DOC")
        base_url = params.get("base_url", "")
        auth = params.get("auth")
        if isinstance(auth, list) and len(auth) >= 2:
            auth = (auth[0], auth[1])
        else:
            auth = None
        if not workspace_path:
            return {
                "status": "error",
                "message": "workspace_path required",
                "result": None,
            }
        result = run_document_project(
            workspace_path=workspace_path,
            space_key=space_key,
            base_url=base_url,
            auth=auth,
        )
        return {"status": "success", "result": result, "learning_trigger": True}
    except Exception as e:
        return {"status": "error", "message": str(e)[:200], "result": None}
