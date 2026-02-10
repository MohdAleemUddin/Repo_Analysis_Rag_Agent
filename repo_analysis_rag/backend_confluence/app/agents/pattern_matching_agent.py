"""Pattern matching agent: template selection with vector/rule matching, fallback template. Output: TemplateDecision."""

from typing import Any

from app.agents.contracts import (
    ConfidenceBreakdown,
    ContentProfile,
    TemplateDecision,
)
from app.confluence.prd_monitor import timer_template_selection
from app.langchain.chains.matching_chain import run_matching

FALLBACK_TEMPLATE_ID = "default"
FALLBACK_TEMPLATE_NAME = "Default"
MIN_SCORE_THRESHOLD = 0.3


def match(
    content: str | None,
    analysis: ContentProfile | dict[str, Any] | None = None,
    vector_store: Any = None,
    content_types_for_template: list[str] | None = None,
    is_single_type: bool | None = None,
) -> TemplateDecision:
    """
    Select template via matching_chain (vector + rules). Must complete in <2s (timer).
    If no template match found, returns deterministic fallback template (TC-NEG-013).
    When content_types_for_template and is_single_type are provided, selects single_type or mixed_content (additive).
    """
    with timer_template_selection():
        profile_dict: dict[str, Any] = {}
        if analysis is not None:
            if isinstance(analysis, ContentProfile):
                profile_dict = analysis.model_dump()
            else:
                profile_dict = analysis

        raw = run_matching(
            content or "",
            profile=profile_dict,
            vector_store=vector_store,
            content_types_for_template=content_types_for_template,
            is_single_type=is_single_type,
        )
        template_id = raw.get("template_id") or FALLBACK_TEMPLATE_ID
        template_name = raw.get("template_name") or FALLBACK_TEMPLATE_NAME
        intelligence_score = float(raw.get("intelligence_score", 0.5))
        cb = raw.get("confidence_breakdown") or {}
        confidence_breakdown = ConfidenceBreakdown(
            content_match=float(cb.get("content_match", 0.5)),
            structure_match=float(cb.get("structure_match", 0.5)),
            context_match=float(cb.get("context_match", 0.5)),
        )
        if intelligence_score < MIN_SCORE_THRESHOLD:
            template_id = FALLBACK_TEMPLATE_ID
            template_name = FALLBACK_TEMPLATE_NAME
            intelligence_score = 0.5
            raw["ai_reasoning"] = (
                raw.get("ai_reasoning", "")
                or "No template match; using fallback template."
            )
            raw["intelligence_reason"] = (
                raw.get("intelligence_reason", "")
                or "No template match; using fallback template."
            )
        return TemplateDecision(
            template_id=template_id,
            template_name=template_name,
            intelligence_score=intelligence_score,
            ai_reasoning=raw.get("ai_reasoning", ""),
            intelligence_reason=raw.get(
                "intelligence_reason", raw.get("ai_reasoning", "")
            ),
            confidence_breakdown=confidence_breakdown,
        )
