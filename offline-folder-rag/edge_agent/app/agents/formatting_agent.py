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
    if "<p>" not in raw_storage and "<p " not in raw_storage:
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
