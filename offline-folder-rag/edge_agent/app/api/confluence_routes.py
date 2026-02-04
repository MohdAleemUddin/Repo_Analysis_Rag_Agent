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


# POST /confluence/intelligent-analyze
def intelligent_analyze_handler() -> Any:
    # TODO: implement
    pass


# POST /confluence/intelligent-create
def intelligent_create_handler() -> Any:
    # TODO: implement
    pass


def _error_response(message: str, intelligence_suggestion: str = "", fallback_available: bool = False) -> tuple:
    """PRD §9.2 exact error format."""
    return {
        "error": "intelligence_error",
        "message": message,
        "intelligence_suggestion": intelligence_suggestion or "Check request format and try again.",
        "fallback_available": fallback_available,
    }, 400


# GET /confluence/intelligence-status
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