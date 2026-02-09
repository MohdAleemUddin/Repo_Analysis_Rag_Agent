"""
Project analyzer for US-16: analyze project structure and infer project type.
Integrates content_analysis_agent for per-file analysis; aggregates to project-level.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.agents.content_analysis_agent import analyze


@dataclass
class ProjectAnalysis:
    """Result of project-level analysis."""

    project_type: str  # "web app" | "API" | "library" | "mixed"
    key_file_types: list[str] = field(default_factory=list)
    structure_summary: str = ""
    patterns: list[str] = field(default_factory=list)
    content_types: list[str] = field(default_factory=list)
    detected_patterns: list[str] = field(default_factory=list)
    source_file_count: int = 0


# File patterns that indicate project type
_WEB_APP_PATTERNS = frozenset({
    "react", "vue", "angular", "svelte", "next", "nuxt",
    "package.json", "webpack", "vite", "tailwind", "component",
    ".tsx", ".jsx", ".vue", ".svelte",
})
_API_PATTERNS = frozenset({
    "fastapi", "flask", "django", "spring", "express",
    "uvicorn", "gunicorn", "rest", "api", "endpoint",
    "openapi", "swagger", "graphql",
})
_LIBRARY_PATTERNS = frozenset({
    "setup.py", "pyproject.toml", "package.json",
    "library", "sdk", "plugin", "middleware", "exports",
})
_DATABASE_PATTERNS = frozenset({
    "postgres", "mysql", "sqlite", "mongodb", "redis",
    "sqlalchemy", "migrations", "schema",
})
_TESTING_PATTERNS = frozenset({
    "pytest", "jest", "unittest", "mocha", "vitest",
    "test_", "_test", ".test.", "spec.", "e2e",
})


def _infer_project_type(
    content_types: list[str],
    patterns: list[str],
    key_file_types: list[str],
    path_hints: list[str],
) -> str:
    """Infer project_type from aggregated signals."""
    all_signals = set()
    for x in content_types:
        all_signals.add(x.lower())
    for p in patterns:
        all_signals.add(p.lower())
    for k in key_file_types:
        all_signals.add(k.lower())
    for h in path_hints:
        all_signals.add(h.lower())

    web_score = sum(1 for s in all_signals if any(w in s for w in _WEB_APP_PATTERNS))
    api_score = sum(1 for s in all_signals if any(a in s for a in _API_PATTERNS))
    lib_score = sum(1 for s in all_signals if any(l in s for l in _LIBRARY_PATTERNS))
    db_score = sum(1 for s in all_signals if any(d in s for d in _DATABASE_PATTERNS))
    test_score = sum(1 for s in all_signals if any(t in s for t in _TESTING_PATTERNS))

    if test_score > 3 and lib_score < 2 and api_score < 2:
        return "testing"
    if db_score >= 2 and api_score < 2:
        return "database"
    if lib_score >= 2 and api_score < 2 and web_score < 2:
        return "library"
    if web_score >= 2 and api_score < 2:
        return "web app"
    if api_score >= 2:
        return "API"
    if web_score >= 1 or api_score >= 1 or lib_score >= 1:
        return "mixed"
    return "mixed"


def analyze_project(paths: list[str]) -> ProjectAnalysis:
    """
    Analyze project from list of file paths.
    Reads file contents (with size limit), runs per-file analysis, aggregates to ProjectAnalysis.
    """
    content_types: list[str] = []
    detected_patterns: list[str] = []
    key_file_types: list[str] = []
    path_hints: list[str] = []
    max_bytes = 64 * 1024  # 64KB per file max for analysis

    for fp in paths[:50]:  # Cap at 50 files for NFR1
        try:
            ext = os.path.splitext(fp)[1].lower()
            name = os.path.basename(fp)
            key_file_types.append(ext or name)
            path_hints.append(name)
            path_hints.append(ext)

            if not os.path.isfile(fp):
                continue
            size = os.path.getsize(fp)
            if size > max_bytes or size == 0:
                if ext in {".py", ".ts", ".tsx", ".js", ".jsx", ".java", ".md"}:
                    content_types.append("document")
                    detected_patterns.append("large_file" if size > max_bytes else "empty")
                continue

            with open(fp, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            profile = analyze(content, file_index=0)
            pd = profile.model_dump() if hasattr(profile, "model_dump") else {}
            content_types.extend(pd.get("content_types", []))
            detected_patterns.extend(pd.get("detected_patterns", []))
            for lang in pd.get("languages", []):
                detected_patterns.append(lang)
            for sig in pd.get("structure_signals", []):
                detected_patterns.append(sig)
        except (OSError, UnicodeDecodeError):
            continue

    # Deduplicate
    content_types = list(dict.fromkeys(str(x) for x in content_types))
    detected_patterns = list(dict.fromkeys(str(p) for p in detected_patterns))
    key_file_types = list(dict.fromkeys(k for k in key_file_types if k))

    project_type = _infer_project_type(
        content_types, detected_patterns, key_file_types, path_hints
    )
    structure_summary = f"{project_type} project with {len(paths)} scanned files"
    return ProjectAnalysis(
        project_type=project_type,
        key_file_types=key_file_types[:20],
        structure_summary=structure_summary,
        patterns=detected_patterns[:30],
        content_types=content_types,
        detected_patterns=detected_patterns,
        source_file_count=len(paths),
    )
