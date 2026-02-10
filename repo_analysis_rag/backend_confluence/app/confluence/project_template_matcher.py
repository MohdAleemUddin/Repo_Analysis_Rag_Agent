"""
Project template matcher for US-16: match ProjectAnalysis to project templates.
Uses project_examples and rule-based matching; fallback when confidence < 70%.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.confluence.project_analyzer import ProjectAnalysis

FALLBACK_TEMPLATE = "Mixed Project Intelligence Template"
CONFIDENCE_THRESHOLD = 0.70  # Fallback when below 70%


@dataclass
class ProjectTemplateMatch:
    """Result of project template matching."""

    template_name: str
    template_id: str
    confidence: float  # 0-100
    match_count: int
    ai_reasoning: str


_PROJECT_TYPE_TO_TEMPLATE: dict[str, tuple[str, str]] = {
    "web app": ("react_webapp_template", "React Web Application Template"),
    "API": ("python_fastapi_template", "Python FastAPI Project Template"),
    "library": ("library_template", "Library Project Template"),
    "database": ("database_template", "Database Project Template"),
    "testing": ("testing_template", "Testing Project Template"),
    "mixed": ("mixed_project_template", "Mixed Project Intelligence Template"),
}


def _load_project_examples() -> list[dict[str, Any]]:
    """Load project_examples.json from confluence_data/examples."""
    try:
        # __file__ is .../backend_confluence/app/confluence/project_template_matcher.py
        # parents[2] = backend_confluence; its parents[1] = repo root (where confluence_data lives)
        edge_root = Path(__file__).resolve().parents[2]
        repo_root = edge_root.parents[1]
        path = repo_root / "confluence_data" / "examples" / "project_examples.json"
        if not path.is_file():
            return []
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("examples", [])
    except (OSError, json.JSONDecodeError):
        return []


def _count_matching_examples(
    analysis: ProjectAnalysis,
    examples: list[dict[str, Any]],
) -> int:
    """Count examples that match project_type or patterns."""
    count = 0
    pt = analysis.project_type.lower()
    patterns = {p.lower() for p in analysis.patterns}
    for ex in examples:
        cp = ex.get("content_profile") or {}
        ex_pt = (cp.get("project_type") or "").lower()
        ex_patterns = set()
        for k in ["detected_patterns", "content_types"]:
            for x in cp.get(k, []):
                ex_patterns.add(str(x).lower())
        if ex_pt == pt:
            count += 1
        elif patterns & ex_patterns:
            count += 1
    return count


def match_project_template(analysis: ProjectAnalysis) -> ProjectTemplateMatch:
    """
    Match ProjectAnalysis to project template.
    Returns template name, confidence (0-100), match count.
    Fallback to Mixed Project Intelligence Template when confidence < 70%.
    """
    examples = _load_project_examples()
    match_count = _count_matching_examples(analysis, examples)

    pt = analysis.project_type.lower()
    patterns_lower = {p.lower() for p in analysis.patterns}
    patterns_str = " ".join(patterns_lower)
    # Pattern overrides for specific frameworks
    if "django" in patterns_str:
        entry = ("python_django_template", "Python Django Project Template")
    elif "spring" in patterns_str:
        entry = ("java_spring_template", "Java Spring Project Template")
    else:
        entry = _PROJECT_TYPE_TO_TEMPLATE.get(pt)
    if not entry:
        entry = _PROJECT_TYPE_TO_TEMPLATE["mixed"]

    template_id, template_name = entry

    # Base confidence from project type match
    confidence = 0.75
    if match_count > 0:
        confidence = min(0.95, 0.70 + 0.05 * min(match_count, 5))
    elif analysis.source_file_count <= 2:
        confidence = 0.65  # Low signal: allow fallback when few files and no examples
    if analysis.source_file_count > 10:
        confidence = min(0.95, confidence + 0.05)

    if confidence < CONFIDENCE_THRESHOLD:
        template_name = FALLBACK_TEMPLATE
        template_id = "mixed_project_template"
        confidence = 0.65
        ai_reasoning = (
            f"Low confidence ({confidence:.0%}); using general documentation template."
        )
    else:
        ai_reasoning = (
            f"Matched {analysis.project_type} project; {match_count} similar examples."
        )

    return ProjectTemplateMatch(
        template_name=template_name,
        template_id=template_id,
        confidence=confidence * 100,
        match_count=match_count,
        ai_reasoning=ai_reasoning,
    )
