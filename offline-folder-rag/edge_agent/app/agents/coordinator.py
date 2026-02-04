"""Coordinator: deterministic 4-agent pipeline, pipeline state, fail-closed errors."""

from __future__ import annotations

import logging
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
from app.agents.formatting_agent import format_content
from app.agents.integration_agent import create_page as integration_create_page
from app.agents.integration_agent import schedule_learning_after_create
from app.agents.pattern_matching_agent import match

logger = logging.getLogger(__name__)

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


def run_analyze(file_contents: list[str]) -> dict[str, Any]:
    """
    Sequential pipeline: 1) Content Analysis (per file), 2) Pattern Matching.
    Returns {"analyses": [dict, ...], "template": dict} for API compatibility.
    """
    global _pipeline_state, _last_coordinator_error
    start_operation()
    _set_state(PipelineState.Idle)
    analyses_out: list[dict[str, Any]] = []
    template_out: dict[str, Any] = {}

    try:
        _set_state(PipelineState.Analyzing)
        if not file_contents:
            _set_state(PipelineState.Failed, CoordinatorError(error_code="analysis_failed", message="No file contents", stage="Analyzing"))
            raise ValueError("No file contents")
        profiles: list[Any] = []
        for idx, content in enumerate(file_contents):
            if not check_memory_before_step():
                _set_state(PipelineState.Failed, CoordinatorError(error_code="resource_limit", message="Memory limit", stage="Analyzing"))
                raise RuntimeError("Memory limit reached")
            prof = analyze_file_with_timer(content, file_index=idx)
            profiles.append(prof)
        analyses_out = [p.model_dump() if hasattr(p, "model_dump") else p for p in profiles]

        _set_state(PipelineState.Matching)
        combined = "\n".join(str(p) for p in profiles)
        template_decision = match(combined, analysis=profiles[0] if profiles else None)
        template_out = template_decision.model_dump() if hasattr(template_decision, "model_dump") else template_decision

        _set_state(PipelineState.Completed)
        return {"analyses": analyses_out, "template": template_out}
    except Exception as e:
        _set_state(PipelineState.Failed, CoordinatorError(
            error_code="analysis_failed",
            message=str(e)[:500] if e else "Pipeline failed",
            stage=_pipeline_state.value,
        ))
        raise


def run_create(
    base_url: str,
    space_key: str,
    title: str,
    body_content: str,
    auth: tuple[str, str] | None = None,
    feedback_for_learning: str = "",
) -> dict[str, Any]:
    """
    Sequential pipeline: Analysis → Matching → Formatting → Integration.
    Returns API-compatible dict (id, title, space, etc.) for confluence_routes.
    """
    global _pipeline_state, _last_coordinator_error
    start_operation()
    _set_state(PipelineState.Idle)

    try:
        _set_state(PipelineState.Analyzing)
        if not check_memory_before_step():
            _set_state(PipelineState.Failed, CoordinatorError(error_code="resource_limit", message="Memory limit", stage="Analyzing"))
            raise RuntimeError("Memory limit reached")
        profile = analyze_file_with_timer(body_content, file_index=0)

        _set_state(PipelineState.Matching)
        template_decision = match(body_content, analysis=profile)

        _set_state(PipelineState.Formatting)
        payload = format_content(body_content, template=template_decision)
        body_html = payload.confluence_storage_format if hasattr(payload, "confluence_storage_format") else str(payload.get("confluence_storage_format", ""))

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
            api_dict = result if isinstance(result, dict) else {"id": "", "title": title, "space": space_key}

        _set_state(PipelineState.Completed)
        if feedback_for_learning:
            schedule_learning_after_create(feedback_for_learning, api_dict)
        return api_dict
    except Exception as e:
        _set_state(PipelineState.Failed, CoordinatorError(
            error_code="create_failed",
            message=str(e)[:500] if e else "Create failed",
            stage=_pipeline_state.value,
        ))
        raise


def get_operation_record() -> Any:
    """Return current performance record for the active operation."""
    return get_current_record()
