"""Formatting agent: Confluence storage format, validation, auto-correction. Output: FormattedConfluencePayload."""

import re
from typing import Any

from app.agents.contracts import (
    FormattedConfluencePayload,
    TemplateDecision,
    ValidationResults,
)
from app.langchain.chains.formatting_chain import run_formatting


def _validate_storage_format(raw: str) -> tuple[list[str], list[str]]:
    """Validate Confluence storage format; return (warnings, corrections_applied)."""
    warnings: list[str] = []
    corrections_applied: list[str] = []

    if not raw or not raw.strip():
        warnings.append("Empty storage format")
        return warnings, corrections_applied

    if not raw.strip().startswith("<"):
        corrections_applied.append("Wrapped content in paragraph")
    if "<script" in raw.lower():
        warnings.append("Script tag detected; consider sanitizing")
    if "&lt;" in raw and "<" not in raw:
        pass
    elif re.search(r"<[^/][^>]*>", raw) and not re.search(r"</p>", raw):
        if "<p>" in raw or "<p " in raw:
            pass
        else:
            corrections_applied.append("Ensured root block is paragraph")
    return warnings, corrections_applied


def format_content(
    content: str,
    template: TemplateDecision | dict[str, Any] | None = None,
) -> FormattedConfluencePayload:
    """
    Format content for Confluence storage. Uses formatting_chain then validates and corrects.
    Returns FormattedConfluencePayload (confluence_storage_format, attachments, validation_results, ai_reasoning).
    """
    template_decision: dict[str, Any] = {}
    if template is not None:
        if isinstance(template, TemplateDecision):
            template_decision = template.model_dump()
        else:
            template_decision = template

    raw_storage = run_formatting(content, template_decision=template_decision)
    warnings, corrections_applied = _validate_storage_format(raw_storage)
    if not raw_storage.strip():
        raw_storage = "<p></p>"
        corrections_applied.append("Set empty payload to minimal paragraph")
    # Do not wrap in <p> when content already has block structure (h2, pre, code); would break headings
    has_block_structure = any(
        tag in raw_storage for tag in ("<h2>", "<h3>", "<h4>", "<pre>", "<code>")
    )
    if (
        not has_block_structure
        and "<p>" not in raw_storage
        and "<p " not in raw_storage
    ):
        raw_storage = f"<p>{raw_storage}</p>" if raw_storage else "<p></p>"
        corrections_applied.append("Wrapped in paragraph tag")

    return FormattedConfluencePayload(
        confluence_storage_format=raw_storage,
        attachments=[],
        validation_results=ValidationResults(
            warnings=warnings,
            corrections_applied=corrections_applied,
        ),
        ai_reasoning="Formatted with template and validated for Confluence storage.",
    )


def format_project_content(
    project_analysis: Any,
    template_name: str,
    template_match: Any,
    file_contents_merged: str = "",
) -> FormattedConfluencePayload:
    """
    Format project documentation for Confluence (US-16).
    Sections: Overview, Architecture, Setup, API Endpoints, Configuration, Testing.
    """
    pa = project_analysis
    pt = getattr(pa, "project_type", "mixed")
    patterns = getattr(pa, "patterns", []) or getattr(pa, "detected_patterns", [])
    key_files = getattr(pa, "key_file_types", [])
    summary = getattr(pa, "structure_summary", "")

    overview = f"<p><strong>Project Type:</strong> {pt}</p><p>{summary}</p>"
    if patterns:
        overview += (
            "<p><strong>Detected patterns:</strong> "
            + ", ".join(str(p) for p in patterns[:15])
            + "</p>"
        )
    if key_files:
        overview += (
            "<p><strong>Key file types:</strong> "
            + ", ".join(str(k) for k in key_files[:10])
            + "</p>"
        )

    arch = "<p>Architecture and structure derived from project scan.</p>"
    if file_contents_merged:
        preview = file_contents_merged[:2000].replace("<", "&lt;").replace(">", "&gt;")
        arch += f"<h4>Content Preview</h4><pre>{preview}</pre>"

    html = (
        "<h2>Overview</h2>"
        + overview
        + "<h2>Architecture</h2>"
        + arch
        + "<h2>Setup</h2><p>Setup instructions based on project type.</p>"
        + "<h2>API Endpoints</h2><p>API endpoints if applicable.</p>"
        + "<h2>Configuration</h2><p>Configuration options.</p>"
        + "<h2>Testing</h2><p>Testing approach and commands.</p>"
    )

    return FormattedConfluencePayload(
        confluence_storage_format=html,
        attachments=[],
        validation_results=ValidationResults(warnings=[], corrections_applied=[]),
        ai_reasoning=f"Project documentation formatted with template: {template_name}.",
    )
