"""Formatting chain: raw content + template decision -> Confluence storage-format string."""

from __future__ import annotations

import html
from typing import Any


def run_formatting(
    content: str,
    template_decision: dict[str, Any] | None = None,
) -> str:
    """
    Produce Confluence storage-format string from raw content and optional template decision.
    Used by Formatting Agent; validation/correction applied in the agent.
    """
    template_decision = template_decision or {}
    if not content:
        return ""

    # Confluence storage format: escape and wrap in safe blocks
    escaped = html.escape(content[:50000])
    lines = escaped.split("\n")
    blocks = []
    for line in lines:
        if line.strip():
            blocks.append(f"<p>{line}</p>")
        else:
            blocks.append("<p></p>")
    storage = "\n".join(blocks) if blocks else "<p></p>"
    return storage
