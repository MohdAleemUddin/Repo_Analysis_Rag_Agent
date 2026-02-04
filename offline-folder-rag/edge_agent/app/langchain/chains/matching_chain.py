"""Matching chain: vector similarity (when available) and rule/statistical matching. Output for TemplateDecision."""

from __future__ import annotations

from typing import Any


def run_matching(
    content: str,
    profile: dict[str, Any] | None = None,
    vector_store: Any = None,
) -> dict[str, Any]:
    """
    Select template via vector similarity (when vector_store/examples available) and/or rules.
    Returns: template_id, template_name, intelligence_score, ai_reasoning,
    confidence_breakdown { content_match, structure_match, context_match }.
    Caller (Pattern Matching Agent) handles fallback when no match.
    """
    profile = profile or {}
    result: dict[str, Any] = {
        "template_id": "",
        "template_name": "",
        "intelligence_score": 0.0,
        "ai_reasoning": "",
        "confidence_breakdown": {
            "content_match": 0.0,
            "structure_match": 0.0,
            "context_match": 0.0,
        },
    }

    # Rule/statistical matching from profile
    content_match = 0.5
    structure_match = 0.5
    context_match = 0.5
    if profile.get("detected_patterns"):
        content_match = min(0.95, 0.5 + 0.1 * len(profile.get("detected_patterns", [])))
    if profile.get("structure_signals"):
        structure_match = 0.7
    result["confidence_breakdown"] = {
        "content_match": content_match,
        "structure_match": structure_match,
        "context_match": context_match,
    }
    result["intelligence_score"] = (
        content_match + structure_match + context_match
    ) / 3.0
    result["ai_reasoning"] = "Rule-based match from content and structure signals."

    # Vector similarity when store available (placeholder: no store = use default)
    if vector_store is not None and hasattr(vector_store, "similarity_search"):
        try:
            docs = vector_store.similarity_search(content, k=1)
            if docs:
                first = docs[0]
                tid = getattr(first, "metadata", {}) or {}
                if isinstance(first, dict):
                    tid = first.get("metadata", first)
                template_id = tid.get("template_id", "default") if isinstance(tid, dict) else "default"
                result["template_id"] = template_id
                result["template_name"] = tid.get("template_name", template_id) if isinstance(tid, dict) else template_id
                result["intelligence_score"] = max(result["intelligence_score"], 0.75)
                result["ai_reasoning"] = "Vector similarity match with rule augmentation."
        except Exception:
            pass

    if not result["template_id"]:
        result["template_id"] = "default"
        result["template_name"] = "Default"
    return result
