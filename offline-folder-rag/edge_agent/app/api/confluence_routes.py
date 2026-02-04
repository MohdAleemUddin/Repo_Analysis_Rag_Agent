<<<<<<< HEAD
# PRD endpoints and export/import for Confluence intelligence
from typing import Any, Tuple

from ..confluence.db_adapter import (
    db_execute as _db_execute,
    db_fetch_examples,
    db_fetch_intelligence_metrics,
    db_ensure_creation_for_feedback,
    db_get_creation_template_id,
    db_update_template_confidence,
)
from ..confluence.export_import import export_examples, import_examples
from ..confluence.status_manager import get_intelligence_status
from ..agents.learning_agent import learn_from_feedback


def _get_query_param(request: Any, name: str) -> Any:
    if hasattr(request, "args") and getattr(request, "args", None):
        return request.args.get(name)
    if hasattr(request, "query_params") and getattr(request, "query_params", None):
        return request.query_params.get(name)
    return None


def _get_json_body(request: Any) -> Any:
    if hasattr(request, "get_json") and callable(getattr(request, "get_json")):
        return request.get_json(silent=True) or {}
    if hasattr(request, "json") and callable(getattr(request, "json")):
        try:
            return request.json()
        except Exception:
            return None
    if hasattr(request, "body"):
        try:
            import json as _json
            return _json.loads(getattr(request.body, "decode", lambda x: x)(request.body if callable(getattr(request.body, "decode", None)) else request.body))
        except Exception:
            return None
    return None


# GET /confluence/examples/export
def examples_export_handler(request: Any) -> Tuple[Any, int]:
    project_path = _get_query_param(request, "project_path")
    from_date = _get_query_param(request, "from_date")
    to_date = _get_query_param(request, "to_date")
    template_type = _get_query_param(request, "template_type")
    json_str = export_examples(
        project_path=project_path,
        from_date=from_date,
        to_date=to_date,
        template_type=template_type,
        db_fetch=db_fetch_examples,
    )
    return json_str, 200


# POST /confluence/examples/import
def examples_import_handler(request: Any) -> Tuple[Any, int]:
    body = _get_json_body(request)
    if body is None:
        payload = None
        if hasattr(request, "get_data") and callable(getattr(request, "get_data")):
            try:
                import json as _json
                payload = request.get_data(as_text=True)
                if payload:
                    body = _json.loads(payload)
            except Exception:
                pass
        if body is None and hasattr(request, "body"):
            try:
                import json as _json
                raw = request.body
                payload = raw.decode("utf-8") if hasattr(raw, "decode") else raw
                body = _json.loads(payload) if isinstance(payload, str) else payload
            except Exception:
                pass
    if body is None:
        return {
            "error": "Invalid format",
            "message": "Request body must be valid JSON. See confluence_data/examples/export_format.json.",
        }, 400
    imported_count, message = import_examples(
        body if isinstance(body, dict) else str(body),
        db_execute=_db_execute,
    )
    if imported_count == 0 and not message.startswith("Intelligence"):
        return {"error": "Validation error", "message": message}, 400
    return {"message": message, "imported_count": imported_count}, 200
=======
# PRD Confluence: analyze, create, status, feedback; PRD §9.2 error format.

import logging
from typing import Any
>>>>>>> 5fa35e2b268e4b9240b01b3b6ca998d64d057f27

try:
    from fastapi import Body, HTTPException
except ImportError:
    Body = None
    HTTPException = None

from app.config.config import CONFLUENCE_MEMORY_LIMIT_MB
from app.confluence.error_handler import (
    get_actions_for_category,
    get_reliability_metrics,
    handle_error,
    prd_error_response,
)
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
        intelligence_suggestion=(
            f"Reduce files or size. Memory limit {CONFLUENCE_MEMORY_LIMIT_MB} MB."
        ),
        fallback_available=True,
        intelligence_confidence=0.0,
        category="resource_limit",
    )
    r["actions"] = get_actions_for_category("resource_limit")
    return r


# POST /confluence/intelligent-analyze
def intelligent_analyze_handler(body: dict[str, Any]) -> dict[str, Any]:
    """Analyze: check memory, run coordinator.run_analyze with timers, return result."""
    if not body or not isinstance(body, dict):
        body = {}
    files_or_contents = body.get("files") or body.get("file_contents") or []
    has_content = (
        body.get("content", "") != "" if body.get("content") is not None else False
    )
    if not files_or_contents and not has_content:
        err = prd_error_response(
            error_code="intelligence_error",
            message="Missing request: provide 'files', 'file_contents', or 'content'.",
            intelligence_suggestion="Send JSON with files or content (string).",
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
    if (
        isinstance(file_contents, list)
        and file_contents
        and not isinstance(file_contents[0], str)
    ):
        file_contents = [
            c.get("content", "") if isinstance(c, dict) else str(c)
            for c in file_contents
        ]
    if not file_contents:
        file_contents = [body.get("content", "") or ""]
    if not file_contents or (
        len(file_contents) == 1 and not (file_contents[0] or "").strip()
    ):
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
    """Create: check memory, run coordinator.run_create (e2e timed), then learning."""
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


def _error_response(message: str, intelligence_suggestion: str = "", fallback_available: bool = False) -> tuple:
    """PRD §9.2 exact error format."""
    return {
        "error": "intelligence_error",
        "message": message,
        "intelligence_suggestion": intelligence_suggestion or "Check request format and try again.",
        "fallback_available": fallback_available,
    }, 400


# GET /confluence/intelligence-status
<<<<<<< HEAD
def intelligence_status_handler(request: Any) -> Tuple[Any, int]:
    detail_level = _get_query_param(request, "detail_level") or "full"
    data = get_intelligence_status(
        detail_level=detail_level,
        db_fetch_metrics=db_fetch_intelligence_metrics,
    )
    resp = {
        "intelligence_metrics": data.get("intelligence_metrics", {}),
        "learning_progress": data.get("learning_progress", {}),
        "intelligence_summary": data.get("intelligence_summary", {}),
    }
    if "improvement_rates" in data:
        resp["improvement_rates"] = data["improvement_rates"]
    return resp, 200


# POST /confluence/intelligence-feedback
def intelligence_feedback_handler(request: Any) -> Tuple[Any, int]:
    body = _get_json_body(request)
    if body is None:
        if hasattr(request, "get_data") and callable(getattr(request, "get_data")):
            try:
                import json as _json
                payload = request.get_data(as_text=True)
                if payload:
                    body = _json.loads(payload)
            except Exception:
                pass
        if body is None and hasattr(request, "body"):
            try:
                import json as _json
                raw = request.body
                payload = raw.decode("utf-8") if hasattr(raw, "decode") else raw
                body = _json.loads(payload) if isinstance(payload, str) else payload
            except Exception:
                pass
    if not body or not isinstance(body, dict):
        return _error_response(
            "Request body must be valid JSON.",
            "Ensure JSON includes creation_id, intelligence_score (1-5), and optional feedback.",
            True,
        )
    creation_id = body.get("creation_id")
    intelligence_score = body.get("intelligence_score")
    feedback = body.get("feedback") or body.get("feedback_text")
    if not creation_id:
        return _error_response(
            "creation_id required.",
            "Provide the UUID of the creation you are rating.",
            False,
        )
    try:
        score = int(intelligence_score) if intelligence_score is not None else None
    except (TypeError, ValueError):
        score = None
    if score is None or not (1 <= score <= 5):
        return _error_response(
            "intelligence_score must be 1-5.",
            "Rate the AI formatting decision from 1 (poor) to 5 (excellent).",
            True,
        )
    learn_from_feedback(
        creation_id=str(creation_id),
        intelligence_score=score,
        feedback_text=str(feedback) if feedback else None,
        db_execute=_db_execute,
        db_ensure_creation=db_ensure_creation_for_feedback,
        db_get_template_id=db_get_creation_template_id,
        db_update_template=db_update_template_confidence,
    )
    data = get_intelligence_status(
        detail_level="full",
        db_fetch_metrics=db_fetch_intelligence_metrics,
    )
    return {
        "updated": True,
        "intelligence_metrics": data.get("intelligence_metrics", {}),
    }, 200


def register_confluence_routes(router: Any) -> None:
    """Register Confluence API routes including export/import (US6), status, feedback (US17)."""
    if hasattr(router, "get"):
        router.get("/confluence/examples/export")(examples_export_handler)
        router.get("/confluence/intelligence-status")(intelligence_status_handler)
    if hasattr(router, "post"):
        router.post("/confluence/examples/import")(examples_import_handler)
        router.post("/confluence/intelligence-feedback")(intelligence_feedback_handler)
    if hasattr(router, "route"):
        router.route("/confluence/examples/export", methods=["GET"])(examples_export_handler)
        router.route("/confluence/examples/import", methods=["POST"])(examples_import_handler)
        router.route("/confluence/intelligence-status", methods=["GET"])(intelligence_status_handler)
        router.route("/confluence/intelligence-feedback", methods=["POST"])(intelligence_feedback_handler)
=======
def intelligence_status_handler() -> dict[str, Any]:
    """Expose last N performance records / aggregates for monitoring."""
    records = get_last_records(20)
    if not records:
        empty_metrics = {
            "template_selection_accuracy": 0.0,
            **get_reliability_metrics(),
        }
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
        "template_selection_accuracy": reliability.get(
            "template_selection_accuracy", 0.0
        ),
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
    return {
        "status": "accepted",
        "message": "Feedback received.",
        "feedback_received": feedback,
    }


def register_confluence_routes(router: Any) -> None:
    """Register the four PRD endpoints on the given router (FastAPI/Flask-style)."""
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
                body = (
                    getattr(request, "json", lambda: {})()
                    if request is not None
                    else {}
                )
                return intelligent_analyze_handler(body)

            def create_route(request: Any = None):
                body = (
                    getattr(request, "json", lambda: {})()
                    if request is not None
                    else {}
                )
                return intelligent_create_handler(body)

            def feedback_route(request: Any = None):
                body = (
                    getattr(request, "json", lambda: {})()
                    if request is not None
                    else {}
                )
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
>>>>>>> 5fa35e2b268e4b9240b01b3b6ca998d64d057f27
