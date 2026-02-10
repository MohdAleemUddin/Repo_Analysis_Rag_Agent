"""Coordinator: deterministic 4-agent pipeline, pipeline state, fail-closed errors."""

from __future__ import annotations

from typing import Any

from app.agents.contracts import (
    CoordinatorError,
    PipelineState,
)
from app.confluence.prd_monitor import (
    check_memory_before_step,
    get_current_record,
    start_operation,
)
from app.agents.content_analysis_agent import analyze_file_with_timer
from app.agents.formatting_agent import format_content, format_project_content
from app.agents.integration_agent import create_page as integration_create_page
from app.agents.integration_agent import schedule_learning_after_create
from app.agents.pattern_matching_agent import match
from app.confluence.project_analyzer import analyze_project
from app.confluence.project_scanner import scan as project_scan
from app.confluence.project_template_matcher import (
    match_project_template,
)
from app.logging.logger import get_logger

logger = get_logger(__name__)

_pipeline_state: PipelineState = PipelineState.Idle
_last_coordinator_error: CoordinatorError | None = None


def get_pipeline_state() -> PipelineState:
    """Expose current pipeline state for TC-ST-009 and diagnosability."""
    return _pipeline_state


def get_last_coordinator_error() -> CoordinatorError | None:
    """Return last CoordinatorError when state is Failed."""
    return _last_coordinator_error


def _set_state(state: PipelineState, err: CoordinatorError | None = None) -> None:
    global _pipeline_state, _last_coordinator_error
    _pipeline_state = state
    _last_coordinator_error = err


def _order_file_contents(file_contents: list[str]) -> list[str]:
    """Order contents: code before documentation, main first, related grouped."""

    def _code_like(c: str) -> bool:
        s = (c or "").strip()
        return bool(
            s.startswith("#")
            or "def " in c
            or "class " in c
            or "import " in c
            or "from " in c
        )

    code_first = [c for c in file_contents if _code_like(c)]
    rest = [c for c in file_contents if not _code_like(c)]
    return code_first + rest


def run_analyze(file_contents: list[str]) -> dict[str, Any]:
    """
    Sequential pipeline: 1) Content Analysis (per file), 2) Pattern Matching.
    Returns PRD §9.1 shape: intelligence_analysis, intelligent_recommendation.
    """
    global _pipeline_state, _last_coordinator_error
    start_operation()
    _set_state(PipelineState.Idle)

    try:
        _set_state(PipelineState.Analyzing)
        if not file_contents:
            _set_state(
                PipelineState.Failed,
                CoordinatorError(
                    error_code="analysis_failed",
                    message="No file contents",
                    stage="Analyzing",
                ),
            )
            raise ValueError("No file contents")
        profiles: list[Any] = []
        for idx, content in enumerate(file_contents):
            if not check_memory_before_step():
                _set_state(
                    PipelineState.Failed,
                    CoordinatorError(
                        error_code="resource_limit",
                        message="Memory limit",
                        stage="Analyzing",
                    ),
                )
                raise RuntimeError("Memory limit reached")
            prof = analyze_file_with_timer(content, file_index=idx)
            profiles.append(prof)

        _set_state(PipelineState.Matching)
        combined = "\n".join(str(p) for p in profiles)
        # Content-type for template selection: code vs text (additive; no breaking change)
        content_types_for_template: list[str] = []
        for p in profiles:
            prof = (
                p.model_dump()
                if hasattr(p, "model_dump")
                else (p if isinstance(p, dict) else {})
            )
            ctypes = prof.get("content_types") or []
            signals = prof.get("structure_signals") or []
            langs = prof.get("languages") or []
            if (
                "module" in ctypes
                or "document" in ctypes
                or "code_like" in signals
                or "python_ast" in signals
                or any("python" in str(l) for l in langs)
            ):
                content_types_for_template.append("code")
            else:
                content_types_for_template.append("text")
        content_types_for_template = list(dict.fromkeys(content_types_for_template))
        is_single_type = len(content_types_for_template) <= 1
        template_decision = match(
            combined,
            analysis=profiles[0] if profiles else None,
            content_types_for_template=content_types_for_template,
            is_single_type=is_single_type,
        )
        td = (
            template_decision.model_dump()
            if hasattr(template_decision, "model_dump")
            else template_decision
        )

        first_profile = profiles[0] if profiles else None
        first_d = (
            first_profile.model_dump()
            if first_profile and hasattr(first_profile, "model_dump")
            else {}
        )
        ai_reasoning = first_d.get("ai_reasoning", "")
        content_types = first_d.get("content_types", [])
        detected_patterns = first_d.get("detected_patterns", [])
        intelligent_title = "Documentation"
        if content_types and isinstance(content_types, list) and len(content_types) > 0:
            if "module" in content_types:
                intelligent_title = "Module documentation"
            elif "document" in content_types:
                intelligent_title = "Documentation"

        intelligence_analysis = {
            "content_types": content_types or [],
            "detected_patterns": detected_patterns or [],
            "intelligent_title": intelligent_title,
            "intelligence_confidence": float(td.get("intelligence_score", 0.5)),
            "ai_reasoning": ai_reasoning,
        }
        cb = td.get("confidence_breakdown") or {}
        intelligent_recommendation = {
            "template_id": td.get("template_id", ""),
            "template_name": td.get("template_name", ""),
            "intelligence_reason": td.get(
                "intelligence_reason", td.get("ai_reasoning", "")
            ),
            "confidence_breakdown": {
                "content_match": float(cb.get("content_match", 0.5)),
                "structure_match": float(cb.get("structure_match", 0.5)),
                "context_match": float(cb.get("context_match", 0.5)),
            },
        }

        _set_state(PipelineState.Completed)
        return {
            "intelligence_analysis": intelligence_analysis,
            "intelligent_recommendation": intelligent_recommendation,
        }
    except Exception as e:
        _set_state(
            PipelineState.Failed,
            CoordinatorError(
                error_code="analysis_failed",
                message=str(e)[:500] if e else "Pipeline failed",
                stage=_pipeline_state.value,
            ),
        )
        raise


def run_create(
    base_url: str,
    space_key: str,
    title: str,
    body_content: str,
    auth: tuple[str, str] | None = None,
    feedback_for_learning: str = "",
    file_contents: list[str] | None = None,
    template_decision_from_analyze: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Sequential pipeline: Analysis → Matching → Formatting → Integration.
    If file_contents is provided, order (code before docs, main first) and merge into body.
    When template_decision_from_analyze is provided (from intelligence_context), use it
    for formatting instead of calling match(); otherwise run match() as before (backward compatible).
    Returns API-compatible dict (id, title, space, etc.) for confluence_routes.
    """
    global _pipeline_state, _last_coordinator_error
    if file_contents:
        ordered = _order_file_contents(file_contents)
        body_content = "\n\n---\n\n".join(ordered)
    start_operation()
    _set_state(PipelineState.Idle)

    try:
        _set_state(PipelineState.Analyzing)
        if not check_memory_before_step():
            _set_state(
                PipelineState.Failed,
                CoordinatorError(
                    error_code="resource_limit",
                    message="Memory limit",
                    stage="Analyzing",
                ),
            )
            raise RuntimeError("Memory limit reached")
        profile = analyze_file_with_timer(body_content, file_index=0)

        _set_state(PipelineState.Matching)
        if template_decision_from_analyze and template_decision_from_analyze.get(
            "template_id"
        ):
            template_decision = template_decision_from_analyze
        else:
            template_decision = match(body_content, analysis=profile)

        _set_state(PipelineState.Formatting)
        payload = format_content(body_content, template=template_decision)
        body_html = (
            payload.confluence_storage_format
            if hasattr(payload, "confluence_storage_format")
            else str(payload.get("confluence_storage_format", ""))
        )

        _set_state(PipelineState.Integrating)
        result = integration_create_page(
            base_url=base_url,
            space_key=space_key,
            title=title,
            body_html=body_html,
            auth=auth,
        )
        ir = result
        if hasattr(ir, "page"):
            page = ir.page
            api_dict = {
                "id": page.id,
                "title": page.title,
                "space": page.space,
                "url": page.url,
            }
        else:
            api_dict = (
                result
                if isinstance(result, dict)
                else {"id": "", "title": title, "space": space_key}
            )

        _set_state(PipelineState.Completed)
        if feedback_for_learning:
            schedule_learning_after_create(feedback_for_learning, api_dict)
        return api_dict
    except Exception as e:
        _set_state(
            PipelineState.Failed,
            CoordinatorError(
                error_code="create_failed",
                message=str(e)[:500] if e else "Create failed",
                stage=_pipeline_state.value,
            ),
        )
        raise


def run_document_project(
    workspace_path: str,
    space_key: str,
    base_url: str,
    auth: tuple[str, str] | None = None,
    progress_callback: Any = None,
) -> dict[str, Any]:
    """
    US-16: Full project documentation pipeline.
    Scan -> Analyze -> Template Match -> Format (project) -> Create.
    Returns PRD §9.1 shape: confluence_url, intelligence_analysis, intelligent_recommendation,
    confidence, template name, learning indicator.
    """
    global _pipeline_state, _last_coordinator_error
    start_operation()
    _set_state(PipelineState.Idle)

    def _progress(current: int, total: int) -> None:
        if progress_callback and callable(progress_callback):
            progress_callback(current, total)

    try:
        _set_state(PipelineState.Analyzing)
        if not check_memory_before_step():
            _set_state(
                PipelineState.Failed,
                CoordinatorError(
                    error_code="resource_limit",
                    message="Memory limit",
                    stage="Analyzing",
                ),
            )
            raise RuntimeError("Memory limit reached")

        paths = project_scan(workspace_path, progress_callback=_progress, limit=100)
        if not paths:
            _set_state(
                PipelineState.Failed,
                CoordinatorError(
                    error_code="analysis_failed",
                    message="No files found in project",
                    stage="Analyzing",
                ),
            )
            raise ValueError("No files found in project")

        analysis = analyze_project(paths)
        _set_state(PipelineState.Matching)
        template_match = match_project_template(analysis)

        _set_state(PipelineState.Formatting)
        file_contents: list[str] = []
        for fp in paths[:30]:
            try:
                with open(fp, "r", encoding="utf-8", errors="replace") as f:
                    file_contents.append(f.read(8192))
            except (OSError, UnicodeDecodeError):
                continue
        merged = "\n\n---\n\n".join(file_contents)

        payload = format_project_content(
            project_analysis=analysis,
            template_name=template_match.template_name,
            template_match=template_match,
            file_contents_merged=merged,
        )
        body_html = (
            payload.confluence_storage_format
            if hasattr(payload, "confluence_storage_format")
            else str(getattr(payload, "confluence_storage_format", ""))
        )

        title = f"{analysis.project_type.title()} Project Documentation"
        _set_state(PipelineState.Integrating)
        result = integration_create_page(
            base_url=base_url,
            space_key=space_key,
            title=title,
            body_html=body_html,
            auth=auth,
        )

        ir = result
        if hasattr(ir, "page"):
            page = ir.page
            api_dict = {
                "id": page.id,
                "title": page.title,
                "space": page.space,
                "url": page.url,
            }
        else:
            api_dict = (
                result
                if isinstance(result, dict)
                else {"id": "", "title": title, "space": space_key, "url": ""}
            )

        _set_state(PipelineState.Completed)
        schedule_learning_after_create(
            f"Project documentation: {analysis.project_type}", api_dict
        )

        intelligence_analysis = {
            "content_types": analysis.content_types or [],
            "detected_patterns": analysis.detected_patterns or [],
            "intelligent_title": title,
            "intelligence_confidence": template_match.confidence / 100.0,
            "ai_reasoning": template_match.ai_reasoning,
            "project_type": analysis.project_type,
            "source_file_count": analysis.source_file_count,
        }
        intelligent_recommendation = {
            "template_id": template_match.template_id,
            "template_name": template_match.template_name,
            "intelligence_reason": template_match.ai_reasoning,
            "confidence_breakdown": {
                "content_match": template_match.confidence / 100.0,
                "structure_match": template_match.confidence / 100.0,
                "context_match": template_match.confidence / 100.0,
            },
        }

        return {
            "confluence_url": api_dict.get("url", ""),
            "intelligence_analysis": intelligence_analysis,
            "intelligent_recommendation": intelligent_recommendation,
            "confidence": template_match.confidence,
            "template_name": template_match.template_name,
            "learning_indicator": True,
        }
    except Exception as e:
        _set_state(
            PipelineState.Failed,
            CoordinatorError(
                error_code="document_project_failed",
                message=str(e)[:500] if e else "Document project failed",
                stage=_pipeline_state.value,
            ),
        )
        raise


def get_operation_record() -> Any:
    """Return current performance record for the active operation."""
    return get_current_record()
