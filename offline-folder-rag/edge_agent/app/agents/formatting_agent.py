"""Formatting agent: formats content for Confluence. Uses content already in memory (no reload)."""

from typing import Any


def format_content(content: str, template: dict[str, Any] | None = None) -> str:
    """
    Format content for Confluence storage. Does not load file again; uses provided content.
    For streamed/chunked content, caller should pass aggregated content.
    """
    if not content:
        return ""
    # Placeholder: wrap in basic storage format
    return f"<p>{content[:5000]}</p>" if len(content) > 5000 else f"<p>{content}</p>"
