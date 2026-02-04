"""Analysis chain: augments deterministic analysis with optional reasoning. Output maps to ContentProfile."""

from __future__ import annotations

from typing import Any

def run_analysis(
    text: str,
    existing_signals: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Augment deterministic analysis. Input: text and optional structured signals.
    Output: dict with detected_patterns, ai_reasoning, and other fields mapping to ContentProfile.
    Does not replace deterministic parsing; used as augmenting step only.
    """
    existing_signals = existing_signals or {}
    detected_patterns: list[str] = list(existing_signals.get("detected_patterns", []))
    ai_reasoning = existing_signals.get("ai_reasoning", "")

    # Deterministic augmentation: infer patterns from content signals
    if existing_signals.get("structure") == "chunked":
        detected_patterns.append("large_content")
    if existing_signals.get("language"):
        lang = existing_signals.get("language", "text")
        if lang != "text":
            detected_patterns.append(f"language_{lang}")
    if not ai_reasoning and (detected_patterns or existing_signals):
        ai_reasoning = "Analysis augmented from structure and language signals."

    return {
        "detected_patterns": detected_patterns,
        "ai_reasoning": ai_reasoning,
        "content_types": existing_signals.get("content_types", []),
        "languages": existing_signals.get("languages", []),
        "structure_signals": existing_signals.get("structure_signals", []),
        "relationships": existing_signals.get("relationships", []),
        "confidence_scores": existing_signals.get("confidence_scores", {}),
    }
