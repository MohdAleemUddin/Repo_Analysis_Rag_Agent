# PRD endpoints and export/import for Confluence intelligence
import logging
from typing import Any, Tuple

from ..confluence.db_adapter import (
    db_execute as _db_execute,
    db_fetch_examples,
    db_fetch_examples_count,
    db_fetch_intelligence_metrics,
    db_ensure_creation_for_feedback,
    db_get_creation_template_id,
    db_record_creation as _db_record_creation,
    db_update_template_confidence,
)
from ..confluence.export_import import export_examples, import_examples
from ..confluence.status_manager import get_intelligence_status
from ..agents.learning_agent import learn_from_feedback, get_collective_intelligence_count
from ..config.confluence_config import get_confluence_config


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
# PRD Confluence: analyze, create, status, feedback; PRD §9.2 error format.

from typing import Any

try:
    from fastapi import Body, HTTPException, Request as FastAPIRequest
except ImportError:
    Body = None
    HTTPException = None
    FastAPIRequest = None

from app.config.config import CONFLUENCE_MEMORY_LIMIT_MB
from app.confluence.error_handler import (
    classify_exception,
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
    verify_targets_met,
)

from app.agents.coordinator import get_operation_record, run_analyze, run_create

logger = logging.getLogger(__name__)

# US11: In-memory usage tracking per user/workspace for progressive disclosure
_confluence_usage_store: dict[tuple[str, str], list[dict[str, Any]]] = {}


def _usage_key(user_id: str, workspace: str) -> tuple[str, str]:
    return (user_id or "default", workspace or "default")


# POST /confluence/track-usage
def track_usage_handler(body: dict[str, Any]) -> dict[str, Any]:
    """Track user interaction; return usageCount and showAdvanced for progressive disclosure."""
    if not body or not isinstance(body, dict):
        body = {}
    user_id = body.get("userId") or body.get("user_id") or "default"
    feature = body.get("feature") or "unknown"
    workspace = body.get("workspace") or body.get("workspace_path") or "default"
    key = _usage_key(user_id, workspace)
    if key not in _confluence_usage_store:
        _confluence_usage_store[key] = []
    _confluence_usage_store[key].append({"feature": feature, "timestamp": __import__("time").time()})
    usage_count = len(_confluence_usage_store[key])
    show_advanced = usage_count >= 2
    return {
        "usageCount": usage_count,
        "showAdvanced": show_advanced,
        "learning": False,
        "messages": {},
    }


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
    """Analyze: check memory, run coordinator.run_analyze with timers, return result. Optional chat_context (US-2)."""
    if not body or not isinstance(body, dict):
        body = {}
    chat_context = body.get("chat_context")
    context_result: dict[str, Any] = {}
    if chat_context and isinstance(chat_context, dict):
        messages = chat_context.get("messages") or chat_context.get("last_messages") or []
        selected_text = chat_context.get("selected_text") or chat_context.get("selection") or ""
        workspace_path = chat_context.get("workspace_path") or chat_context.get("workspacePath") or ""
        try:
            context_result = analyze_chat_context(
                messages=messages,
                selected_text=selected_text,
                workspace_path=workspace_path,
            )
        except Exception as e:
            logger.debug("Context analysis skipped: %s", e)

    files_or_contents = body.get("files") or body.get("file_contents") or []
    has_content = (
        body.get("content", "") != "" if body.get("content") is not None else False
    )
    if not files_or_contents and not has_content:
        if context_result:
            return {
                "context_suggestions": {
                    "mentioned_files": context_result.get("mentioned_files", []),
                    "related_files": context_result.get("related_files", []),
                    "project_type_label": context_result.get("project_type_label", "Mixed project"),
                    "detected_language": context_result.get("detected_language", "Mixed"),
                    "should_suggest_readme": context_result.get("should_suggest_readme", False),
                },
            }
        err = prd_error_response(
            error_code="intelligence_error",
            message="Missing request: provide 'files', 'file_contents', 'content', or 'chat_context'.",
            intelligence_suggestion="Send JSON with files or content (string) or chat_context.",
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
        cat = classify_exception(e)
        suggested: list[str] = []
        if cat in ("content", "intelligence_error") and context_result:
            related = context_result.get("related_files") or []
            mentioned = context_result.get("mentioned_files") or []
            suggested = list(dict.fromkeys(related + mentioned))
        return handle_error(
            e, error_code="analysis_failed", suggested_files=suggested or None
        )

    if context_result:
        result["context_suggestions"] = {
            "mentioned_files": context_result.get("mentioned_files", []),
            "related_files": context_result.get("related_files", []),
            "project_type_label": context_result.get("project_type_label", "Mixed project"),
            "detected_language": context_result.get("detected_language", "Mixed"),
            "should_suggest_readme": context_result.get("should_suggest_readme", False),
        }

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


# POST /confluence/intelligent-create (PRD §9.1: files, intelligent_mode, auto_title, space, intelligence_context)
def intelligent_create_handler(body: dict[str, Any]) -> dict[str, Any]:
    """Create: check memory, resolve title from auto_title/title_override, run coordinator.run_create."""
    logger.info("intelligent-create request received")
    if not check_memory_before_step():
        return _memory_limit_response()

    start_operation()
    base_url = body.get("base_url", "")
    space_key = body.get("space") or body.get("space_key", "DOC")
    auth = body.get("auth")  # (email, api_token) or None; JSON sends list
    if isinstance(auth, list) and len(auth) >= 2:
        auth = (auth[0], auth[1])
    elif not isinstance(auth, tuple):
        auth = None
    feedback = body.get("feedback_for_learning", "")
    intelligence_context = body.get("intelligence_context") or {}
    auto_title = body.get("auto_title", True)
    if auto_title:
        title = (
            intelligence_context.get("suggested_title")
            or body.get("suggested_title")
            or body.get("title", "Untitled")
        )
    else:
        title = (
            intelligence_context.get("title_override")
            or body.get("title", "Untitled")
        )
    title = (title or "Untitled").strip() or "Untitled"

    # Template from analysis so create uses same format (PRD full AI intelligence)
    template_decision_from_analyze = None
    rec = intelligence_context.get("intelligent_recommendation") or {}
    tid = (intelligence_context.get("template_id") or rec.get("template_id") or "").strip()
    if tid:
        tname = (intelligence_context.get("template_name") or rec.get("template_name") or tid) or ""
        template_decision_from_analyze = {"template_id": tid, "template_name": tname}

    files = body.get("files") or []
    if isinstance(files, list) and files and not isinstance(files[0], str):
        file_contents = [
            c.get("content", "") if isinstance(c, dict) else str(c)
            for c in files
        ]
    else:
        file_contents = [c for c in files if isinstance(c, str)] if files else []
    content = body.get("content", "") or body.get("body_content", "")

    logger.info("intelligent-create calling run_create")
    try:
        result = run_create(
            base_url=base_url,
            space_key=space_key,
            title=title,
            body_content=content if not file_contents else "",
            auth=auth,
            feedback_for_learning=feedback,
            file_contents=file_contents if file_contents else None,
            template_decision_from_analyze=template_decision_from_analyze,
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

    # US11: Learning indicator when intelligence learned from this creation
    if result.get("success") and isinstance(result.get("intelligence_summary"), dict):
        if result["intelligence_summary"].get("ai_learning_applied"):
            result["learning"] = True
            result["message"] = "Intelligence learning from your successful creation"

    return result


def _error_response(
    message: str,
    intelligence_suggestion: str = "",
    fallback_available: bool = False,
    intelligence_confidence: float = 0.0,
) -> tuple:
    """PRD §9.2 exact error format."""
    return {
        "error": "intelligence_error",
        "message": message,
        "intelligence_suggestion": intelligence_suggestion or "Check request format and try again.",
        "fallback_available": fallback_available,
        "intelligence_confidence": intelligence_confidence,
    }, 400


# GET /confluence/intelligence-status
def intelligence_status_handler(request: Any = None) -> Tuple[Any, int] | dict[str, Any]:
    """Status: use get_intelligence_status when request provided (DB metrics), else last records."""
    if request is not None:
        detail_level = _get_query_param(request, "detail_level") or "full"
        data = get_intelligence_status(
            detail_level=detail_level,
            db_fetch_metrics=db_fetch_intelligence_metrics,
        )
        recs = get_last_records(1)
        last_rec = recs[-1] if recs else None
        resp = {
            "intelligence_metrics": data.get("intelligence_metrics", {}),
            "learning_progress": data.get("learning_progress", {}),
            "intelligence_summary": data.get("intelligence_summary", {}),
            "last_operation_targets_met": verify_targets_met(last_rec),
        }
        if "improvement_rates" in data:
            resp["improvement_rates"] = data["improvement_rates"]
        team_count = get_collective_intelligence_count(
            db_fetch_count=db_fetch_examples_count,
            team_sharing_opt_in=get_confluence_config().get("team_sharing_opt_in", True),
        )
        resp["intelligence_metrics"]["team_examples_count"] = team_count
        resp["learning_progress"]["team_examples_count"] = team_count
        return resp, 200
    records = get_last_records(20)
    if not records:
        empty_metrics = {"template_selection_accuracy": 0.0, **get_reliability_metrics()}
        return {
            "metrics": empty_metrics,
            "intelligence_metrics": empty_metrics,
            "learning_progress": {},
            "improvement_rates": {},
            "recent_records": [],
            "last_operation_targets_met": False,
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
    last_rec = records[-1] if records else None
    return {
        "metrics": metrics,
        "intelligence_metrics": metrics,
        "learning_progress": {},
        "improvement_rates": {},
        "recent_records": [r.to_dict() for r in records[-5:]],
        "last_operation_targets_met": verify_targets_met(last_rec),
    }


# POST /confluence/document-project (US-16)
def document_project_handler(body: dict[str, Any]) -> dict[str, Any]:
    """Document project: scan, analyze, template match, format, create. PRD §9.1/§9.2."""
    if not check_memory_before_step():
        return _memory_limit_response()

    workspace_path = body.get("workspace_path") or body.get("workspacePath") or ""
    space_key = body.get("space") or body.get("space_key", "DOC")
    base_url = body.get("base_url", "")
    auth = body.get("auth")
    if isinstance(auth, list) and len(auth) >= 2:
        auth = (auth[0], auth[1])
    elif not isinstance(auth, tuple):
        auth = None

    if not workspace_path or not workspace_path.strip():
        err = prd_error_response(
            error_code="intelligence_error",
            message="Please open a project folder first.",
            intelligence_suggestion="Open a workspace folder in VS Code and try again.",
            fallback_available=False,
            intelligence_confidence=0.0,
        )
        if HTTPException is not None:
            raise HTTPException(status_code=400, detail=err)
        return err

    start_operation()
    try:
        result = run_document_project(
            workspace_path=workspace_path.strip(),
            space_key=space_key,
            base_url=base_url,
            auth=auth,
        )
    except Exception as e:
        logger.exception("document-project failed: %s", e)
        return handle_error(e, error_code="document_project_failed")

    record = get_operation_record()
    peak_mb = get_peak_memory_mb()
    if record:
        from app.confluence.prd_monitor import append_record, record_confluence_operation
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
    return result


# POST /confluence/intelligence-feedback
def intelligence_feedback_handler(body: dict[str, Any], request: Any = None) -> dict[str, Any] | Tuple[Any, int]:
    """Accept feedback; when creation_id and intelligence_score 1-5, call learn_from_feedback."""
    if body is not None and not isinstance(body, dict):
        request = body
        body = _get_json_body(request) or {}
    elif body is None and request is not None:
        body = _get_json_body(request) or {}
    body = body or {}
    creation_id = body.get("creation_id")
    intelligence_score = body.get("intelligence_score")
    feedback = body.get("feedback") or body.get("feedback_text")
    if creation_id is not None and intelligence_score is not None:
        try:
            score = int(intelligence_score)
        except (TypeError, ValueError):
            score = None
        if score is not None and 1 <= score <= 5:
            learn_from_feedback(
                creation_id=str(creation_id),
                intelligence_score=score,
                feedback_text=str(feedback) if feedback else None,
                db_execute=_db_execute,
                db_ensure_creation=db_ensure_creation_for_feedback,
                db_get_template_id=db_get_creation_template_id,
                db_update_template=db_update_template_confidence,
            )
            data = get_intelligence_status(detail_level="full", db_fetch_metrics=db_fetch_intelligence_metrics)
            return ({"updated": True, "intelligence_metrics": data.get("intelligence_metrics", {})}, 200)
    feedback_text = body.get("feedback", "") or body.get("message", "")
    return ({"status": "accepted", "message": "Feedback received.", "feedback_received": feedback_text}, 200)


def register_confluence_routes(router: Any) -> None:
    """Register PRD endpoints and US6 export/import on the given router (FastAPI/Flask-style)."""
    if hasattr(router, "post") and hasattr(router, "get"):
        if Body is not None:
            def analyze_route(body: dict = Body(default=None)):
                return intelligent_analyze_handler(body or {})

            def create_route(body: dict = Body(default=None)):
                return intelligent_create_handler(body or {})

            def feedback_route(body: dict = Body(default=None)):
                out = intelligence_feedback_handler(body or {})
                return out[0] if isinstance(out, tuple) else out

            def track_usage_route(body: dict = Body(default=None)):
                return track_usage_handler(body or {})

            def document_project_route(body: dict = Body(default=None)):
                return document_project_handler(body or {})

            def status_route(request: Any = None):
                out = intelligence_status_handler(request)
                return out[0] if isinstance(out, tuple) else out

            router.post("/confluence/intelligent-analyze")(analyze_route)
            router.post("/confluence/intelligent-analyz")(analyze_route)  # alias for client typo
            router.get("/confluence/intelligent-analyz")(status_route)  # GET typo -> status
            router.post("/confluence/intelligent-create")(create_route)
            router.post("/confluence/document-project")(document_project_route)
            router.get("/confluence/intelligence-status")(status_route)
            router.post("/confluence/intelligence-feedback")(feedback_route)
            router.post("/confluence/track-usage")(track_usage_route)
            if FastAPIRequest is not None:
                def export_route(request: FastAPIRequest):
                    out = examples_export_handler(request)
                    from fastapi.responses import Response
                    return Response(content=out[0], media_type="application/json", status_code=out[1])
                def import_route(request: FastAPIRequest):
                    out = examples_import_handler(request)
                    from fastapi.responses import JSONResponse
                    body, status = out if isinstance(out, tuple) else (out, 200)
                    return JSONResponse(content=body if isinstance(body, dict) else {}, status_code=status)
                router.get("/confluence/examples/export")(export_route)
                router.post("/confluence/examples/import")(import_route)
        else:
            def analyze_route(request: Any = None):
                body = getattr(request, "json", lambda: {})() if request is not None else {}
                return intelligent_analyze_handler(body)

            def create_route(request: Any = None):
                body = getattr(request, "json", lambda: {})() if request is not None else {}
                return intelligent_create_handler(body)

            def document_project_route(request: Any = None):
                body = getattr(request, "json", lambda: {})() if request is not None else {}
                return document_project_handler(body)

            def feedback_route(request: Any = None):
                body = getattr(request, "json", lambda: {})() if request is not None else {}
                out = intelligence_feedback_handler(body, request)
                return out[0] if isinstance(out, tuple) else out

            def track_usage_route(request: Any = None):
                body = getattr(request, "json", lambda: {})() if request is not None else {}
                return track_usage_handler(body)

            def status_route(request: Any = None):
                out = intelligence_status_handler(request)
                return out[0] if isinstance(out, tuple) else out

            router.post("/confluence/intelligent-analyze")(analyze_route)
            router.post("/confluence/intelligent-analyz")(analyze_route)  # alias for client typo
            router.get("/confluence/intelligent-analyz")(status_route)  # GET typo -> status
            router.post("/confluence/intelligent-create")(create_route)
            router.post("/confluence/document-project")(document_project_route)
            router.get("/confluence/intelligence-status")(status_route)
            router.post("/confluence/intelligence-feedback")(feedback_route)
            router.post("/confluence/track-usage")(track_usage_route)
            router.route("/confluence/examples/export", methods=["GET"])(examples_export_handler)
            router.route("/confluence/examples/import", methods=["POST"])(examples_import_handler)
    else:
        router.confluence_handlers = {
            "intelligent_analyze": lambda body: intelligent_analyze_handler(body),
            "intelligent_create": lambda body: intelligent_create_handler(body),
            "document_project": lambda body: document_project_handler(body),
            "intelligence_status": lambda: intelligence_status_handler(),
            "intelligence_feedback": lambda body: intelligence_feedback_handler(body),
            "track_usage": track_usage_handler,
            "examples_export": examples_export_handler,
            "examples_import": examples_import_handler,
        }

    # Register Confluence config endpoints (test-connection, spaces, validate, defaults)
    from app.api.config_routes import register_config_routes

    register_config_routes(router)
