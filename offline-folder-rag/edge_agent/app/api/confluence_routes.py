# PRD Confluence endpoints: analyze, create, status, feedback with performance monitoring and PRD §9.2 error format.

import logging
from typing import Any

try:
    from fastapi import Body, HTTPException
except ImportError:
    Body = None
    HTTPException = None

from app.config.config import CONFLUENCE_MEMORY_LIMIT_MB
from app.confluence.error_handler import get_actions_for_category, get_reliability_metrics, handle_error, prd_error_response
from app.confluence.optimizer import get_optimization_suggestions
from app.confluence.prd_monitor import (
    append_record,
    check_memory_before_step,
    get_last_records,
    get_peak_memory_mb,
    record_confluence_operation,
    start_operation,
)

from app.agents.coordinator import get_operation_record, run_analyze, run_create

logger = logging.getLogger(__name__)


def _memory_limit_response() -> dict[str, Any]:
    r = prd_error_response(
        error_code="resource_limit",
        message="Resource limit reached; try fewer or smaller files.",
        intelligence_suggestion=f"Reduce files or size. Memory limit {CONFLUENCE_MEMORY_LIMIT_MB} MB.",
        fallback_available=True,
        intelligence_confidence=0.0,
        category="resource_limit",
    )
    r["actions"] = get_actions_for_category("resource_limit")
    return r


# POST /confluence/intelligent-analyze
def intelligent_analyze_handler(body: dict[str, Any]) -> dict[str, Any]:
    """
    Analyze files: check memory first, run coordinator.run_analyze with timers, return result + performance summary.
    """
    if not body or not isinstance(body, dict):
        body = {}
    files_or_contents = body.get("files") or body.get("file_contents") or []
    has_content = body.get("content", "") != "" if body.get("content") is not None else False
    if not files_or_contents and not has_content:
        err = prd_error_response(
            error_code="intelligence_error",
            message="Missing or invalid request: provide 'files', 'file_contents', or 'content'.",
            intelligence_suggestion="Send a JSON body with files (list of strings) or content (string).",
            fallback_available=False,
            intelligence_confidence=0.0,
        )
        if HTTPException is not None:
            raise HTTPException(status_code=422, detail=err)
        return err

    if not check_memory_before_step():
        return _memory_limit_response()

    start_operation()
    file_contents = files_or_contents
    if isinstance(file_contents, list) and file_contents and not isinstance(file_contents[0], str):
        file_contents = [c.get("content", "") if isinstance(c, dict) else str(c) for c in file_contents]
    if not file_contents:
        file_contents = [body.get("content", "") or ""]
    if not file_contents or (len(file_contents) == 1 and not (file_contents[0] or "").strip()):
        err = prd_error_response(
            error_code="intelligence_error",
            message="No content to analyze.",
            intelligence_suggestion="Provide non-empty files or content.",
            fallback_available=False,
            intelligence_confidence=0.0,
        )
        if HTTPException is not None:
            raise HTTPException(status_code=422, detail=err)
        return err

    try:
        result = run_analyze(file_contents)
    except Exception as e:
        logger.exception("intelligent-analyze failed: %s", e)
        return handle_error(e, error_code="analysis_failed")

    record = get_operation_record()
    peak_mb = get_peak_memory_mb()
    if record:
        perf = record_confluence_operation(
            operation_id=record.operation_id,
            per_file_analysis_ms=record.per_file_analysis_ms,
            template_selection_ms=record.template_selection_ms,
            create_e2e_ms=record.create_e2e_ms,
            peak_memory_mb=peak_mb,
        )
        append_record(perf)
        result["performance"] = {
            "operation_id": perf.operation_id,
            "analysis_timings_ms": perf.per_file_analysis_ms,
            "template_selection_ms": perf.template_selection_ms,
            "peak_memory_mb": perf.peak_memory_mb,
            "targets_met": perf.targets_met,
        }
        if not all(perf.targets_met.values()):
            result["optimization_suggestions"] = get_optimization_suggestions(perf)
    return result


# POST /confluence/intelligent-create
def intelligent_create_handler(body: dict[str, Any]) -> dict[str, Any]:
    """
    Create page: check memory, run coordinator.run_create (e2e timed), return result then trigger background learning.
    """
    if not check_memory_before_step():
        return _memory_limit_response()

    start_operation()
    base_url = body.get("base_url", "")
    space_key = body.get("space_key", "DOC")
    title = body.get("title", "Untitled")
    content = body.get("content", "") or body.get("body_content", "")
    auth = body.get("auth")  # (email, api_token) or None
    feedback = body.get("feedback_for_learning", "")

    try:
        result = run_create(
            base_url=base_url,
            space_key=space_key,
            title=title,
            body_content=content,
            auth=auth,
            feedback_for_learning=feedback,
        )
    except Exception as e:
        logger.exception("intelligent-create failed: %s", e)
        return handle_error(e, error_code="create_failed")

    record = get_operation_record()
    peak_mb = get_peak_memory_mb()
    if record:
        perf = record_confluence_operation(
            operation_id=record.operation_id,
            per_file_analysis_ms=record.per_file_analysis_ms,
            template_selection_ms=record.template_selection_ms,
            create_e2e_ms=record.create_e2e_ms,
            peak_memory_mb=peak_mb,
        )
        append_record(perf)
        result["performance"] = {
            "operation_id": perf.operation_id,
            "create_e2e_ms": perf.create_e2e_ms,
            "peak_memory_mb": perf.peak_memory_mb,
            "targets_met": perf.targets_met,
        }
        if not all(perf.targets_met.values()):
            result["optimization_suggestions"] = get_optimization_suggestions(perf)

    return result


# GET /confluence/intelligence-status
def intelligence_status_handler() -> dict[str, Any]:
    """Expose last N performance records / aggregates for monitoring."""
    records = get_last_records(20)
    if not records:
        empty_metrics = {"template_selection_accuracy": 0.0, **get_reliability_metrics()}
        return {
            "metrics": empty_metrics,
            "intelligence_metrics": empty_metrics,
            "learning_progress": {},
            "improvement_rates": {},
            "recent_records": [],
        }

    analysis_times = []
    create_times = []
    memory_peaks = []
    for r in records:
        analysis_times.extend(r.per_file_analysis_ms)
        create_times.append(r.create_e2e_ms)
        memory_peaks.append(r.peak_memory_mb)

    def p95(vals: list[float]) -> float:
        if not vals:
            return 0.0
        s = sorted(vals)
        i = int(len(s) * 0.95) or 0
        return s[min(i, len(s) - 1)]

    reliability = get_reliability_metrics()
    metrics = {
        "p95_analysis_ms": p95(analysis_times),
        "p95_create_ms": p95(create_times),
        "max_memory_mb": max(memory_peaks) if memory_peaks else 0,
        "template_selection_accuracy": reliability.get("template_selection_accuracy", 0.0),
        **reliability,
    }
    recent = [r.to_dict() for r in records[-5:]]
    return {
        "metrics": metrics,
        "intelligence_metrics": metrics,
        "learning_progress": {},
        "improvement_rates": {},
        "recent_records": recent,
    }


# POST /confluence/intelligence-feedback
def intelligence_feedback_handler(body: dict[str, Any]) -> dict[str, Any]:
    """Accept feedback; process quickly or async so request does not block."""
    feedback = body.get("feedback", "") or body.get("message", "")
    return {"status": "accepted", "message": "Feedback received."}


def register_confluence_routes(router: Any) -> None:
    """Register the four PRD endpoints on the given router (FastAPI or Flask-style)."""
    if hasattr(router, "post") and hasattr(router, "get"):
        if Body is not None:
            def analyze_route(body: dict = Body(default=None)):
                return intelligent_analyze_handler(body or {})

            def create_route(body: dict = Body(default=None)):
                return intelligent_create_handler(body or {})

            def feedback_route(body: dict = Body(default=None)):
                return intelligence_feedback_handler(body or {})
        else:
            def analyze_route(request: Any = None):
                body = getattr(request, "json", lambda: {})() if request is not None else {}
                return intelligent_analyze_handler(body)

            def create_route(request: Any = None):
                body = getattr(request, "json", lambda: {})() if request is not None else {}
                return intelligent_create_handler(body)

            def feedback_route(request: Any = None):
                body = getattr(request, "json", lambda: {})() if request is not None else {}
                return intelligence_feedback_handler(body)

        def status_route():
            return intelligence_status_handler()

        router.post("/confluence/intelligent-analyze")(analyze_route)
        router.post("/confluence/intelligent-create")(create_route)
        router.get("/confluence/intelligence-status")(status_route)
        router.post("/confluence/intelligence-feedback")(feedback_route)
    else:
        router.confluence_handlers = {
            "intelligent_analyze": lambda body: intelligent_analyze_handler(body),
            "intelligent_create": lambda body: intelligent_create_handler(body),
            "intelligence_status": lambda: intelligence_status_handler(),
            "intelligence_feedback": lambda body: intelligence_feedback_handler(body),
        }
