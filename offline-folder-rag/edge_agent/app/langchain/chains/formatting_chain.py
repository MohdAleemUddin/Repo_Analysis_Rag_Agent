"""Formatting chain: raw content + template decision -> Confluence storage-format string."""

from __future__ import annotations

import html
from typing import Any


def _default_storage(content: str) -> str:
    """Current behavior: escape and wrap each line in p. Fallback when template formatting is not used."""
    if not content:
        return "<p></p>"
    escaped = html.escape(content[:50000])
    lines = escaped.split("\n")
    blocks = []
    for line in lines:
        if line.strip():
            blocks.append(f"<p>{line}</p>")
        else:
            blocks.append("<p></p>")
    return "\n".join(blocks) if blocks else "<p></p>"


def _format_single_type(content: str) -> str:
    """Structured layout: Overview, Code or Content, Conclusion. Single-type template."""
    if not content:
        return "<p></p>"
    escaped = html.escape(content[:50000])
    strip = content.strip()
    lines = escaped.split("\n")
    code_signals = ("def ", "class ", "import ", "from ", "function ", "=>", "const ", "let ", "{", "}")
    is_code_like = any(s in strip for s in code_signals) or (strip.count("\n") > 5 and "  " in strip)
    if is_code_like:
        overview_p = "<p>Code module or script below.</p>"
        first_comment = next((ln.strip() for ln in content.split("\n") if ln.strip().startswith("#")), None)
        if first_comment:
            overview_p = f"<p>{html.escape(first_comment)}</p>"
        code_block = f"<pre><code>{escaped}</code></pre>"
        conclusion = "<p>End of module.</p>"
        return f"<h2>Overview</h2>\n{overview_p}\n<h2>Code</h2>\n{code_block}\n<h2>Conclusion</h2>\n{conclusion}"
    overview_p = "<p>Documentation content below.</p>"
    if lines and lines[0].strip():
        overview_p = f"<p>{lines[0]}</p>"
    blocks = [f"<p>{line}</p>" if line.strip() else "<p></p>" for line in lines]
    body = "\n".join(blocks) if blocks else "<p></p>"
    conclusion = "<p>End of document.</p>"
    return f"<h2>Overview</h2>\n{overview_p}\n<h2>Content</h2>\n{body}\n<h2>Conclusion</h2>\n{conclusion}"


def _format_mixed_content(content: str) -> str:
    """Overview + Code/Details + Conclusion. Mixed-content template with headings."""
    if not content:
        return "<p></p>"
    escaped = html.escape(content[:50000])
    lines = escaped.split("\n")
    overview_lines = []
    rest_lines = []
    count = 0
    for line in lines:
        if count < 5 and line.strip():
            overview_lines.append(line)
            count += 1
        else:
            rest_lines.append(line)
    overview_html = "\n".join(f"<p>{line}</p>" if line.strip() else "<p></p>" for line in overview_lines) if overview_lines else "<p>Content overview.</p>"
    rest_html = "\n".join(f"<p>{line}</p>" if line.strip() else "<p></p>" for line in rest_lines) if rest_lines else ""
    conclusion = "<p>End of document.</p>"
    if rest_html:
        return f"<h2>Overview</h2>\n{overview_html}\n<h2>Code / Details</h2>\n{rest_html}\n<h2>Conclusion</h2>\n{conclusion}"
    return f"<h2>Overview</h2>\n{overview_html}\n<h2>Conclusion</h2>\n{conclusion}"


def run_formatting(
    content: str,
    template_decision: dict[str, Any] | None = None,
) -> str:
    """
    Produce Confluence storage-format string from raw content and optional template decision.
    When template_id is single_type or mixed_content, uses template layout; else uses default (escape + p per line).
    Fallback: on any error or unknown template, returns default storage (no breaking change).
    """
    template_decision = template_decision or {}
    if not content:
        return "<p></p>"

    template_id = (template_decision.get("template_id") or "").strip()

    try:
        if template_id == "single_type":
            return _format_single_type(content)
        if template_id == "mixed_content":
            return _format_mixed_content(content)
    except Exception:
        pass

    return _default_storage(content)
