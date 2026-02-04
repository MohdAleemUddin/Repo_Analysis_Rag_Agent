"""Formatting agent: formats content for Confluence; uses content in memory."""

from typing import Any


def format_content(content: str, template: dict[str, Any] | None = None) -> str:
    """
    Format content for Confluence storage. Uses provided content (no reload).
    For streamed/chunked content, caller should pass aggregated content.
    """
    if not content:
        return ""
    # Placeholder: wrap in basic storage format
    return f"<p>{content[:5000]}</p>" if len(content) > 5000 else f"<p>{content}</p>"
