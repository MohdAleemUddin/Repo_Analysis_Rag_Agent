"""Pattern matching agent: selects template with PRD timer (< 2s)."""

from typing import Any

from app.confluence.prd_monitor import timer_template_selection


def match(content: str | None, analysis: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Select template based on content/analysis. Must complete in < 2s (wrapped by timer).
    Returns e.g. {"template_id": "...", "confidence": 0.9}.
    """
    with timer_template_selection():
        # Placeholder: return a default template; real impl would use vector search / learned examples
        return {
            "template_id": "default",
            "confidence": 0.9,
            "reason": "pattern match",
        }
