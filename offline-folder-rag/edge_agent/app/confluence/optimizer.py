"""
Optimizer: produces optimization suggestions from Confluence performance records.
Does not perform throttling; CPU throttling is implemented in coordinator/agents.
"""

from typing import Any

from app.config.config import (
    ANALYSIS_MAX_SECONDS_PER_FILE,
    CONFLUENCE_MEMORY_LIMIT_MB,
    CREATE_E2E_MAX_SECONDS,
    TEMPLATE_SELECTION_MAX_SECONDS,
)

# Avoid circular import: use type hint string or dict
PerformanceRecordLike = Any  # PerformanceRecord from prd_monitor


def get_optimization_suggestions(record: PerformanceRecordLike) -> list[str]:
    """Return optimization suggestions from a performance record. Suggestions only."""
    suggestions: list[str] = []

    if hasattr(record, "per_file_analysis_ms"):
        per_file_ms = record.per_file_analysis_ms
        _ = getattr(record, "targets_met", {}) or {}  # reserved for future use
    else:
        per_file_ms = record.get("per_file_analysis_ms", [])
        _ = record.get("targets_met", {})  # reserved for future use

    # Per-file analysis exceeded 3s
    over = [ms for ms in per_file_ms if ms > ANALYSIS_MAX_SECONDS_PER_FILE * 1000]
    if over:
        n = len(over)
        suggestions.append(
            f"Analysis exceeded {ANALYSIS_MAX_SECONDS_PER_FILE}s for {n} file(s). "
            "Consider cache or reduce CONFLUENCE_MAX_PARALLEL_FILES."
        )

    # Template selection > 2s
    if hasattr(record, "template_selection_ms"):
        template_ms = record.template_selection_ms
    else:
        template_ms = record.get("template_selection_ms", 0)
    if template_ms > TEMPLATE_SELECTION_MAX_SECONDS * 1000:
        suggestions.append(
            f"Template selection {template_ms/1000:.2f}s "
            f"(limit {TEMPLATE_SELECTION_MAX_SECONDS}s). Cache template index."
        )

    # E2E create > 15s
    if hasattr(record, "create_e2e_ms"):
        create_ms = record.create_e2e_ms
    else:
        create_ms = record.get("create_e2e_ms", 0)
    if create_ms > CREATE_E2E_MAX_SECONDS * 1000:
        suggestions.append(
            f"E2E create {create_ms/1000:.2f}s "
            f"(limit {CREATE_E2E_MAX_SECONDS}s). Check network or reduce."
        )

    # Peak memory > 300MB
    if hasattr(record, "peak_memory_mb"):
        peak_mb = record.peak_memory_mb
    else:
        peak_mb = record.get("peak_memory_mb", 0)
    if peak_mb > CONFLUENCE_MEMORY_LIMIT_MB:
        suggestions.append(
            f"Peak memory {peak_mb:.1f} MB exceeded limit "
            f"{CONFLUENCE_MEMORY_LIMIT_MB} MB. "
            "Lower CONFLUENCE_MAX_PARALLEL_FILES or use smaller chunks."
        )

    return suggestions


def get_recommended_max_parallel(peak_memory_mb: float) -> int | None:
    """Suggest lower max parallel if memory was high. None if no change suggested."""
    if peak_memory_mb <= 0 or peak_memory_mb < CONFLUENCE_MEMORY_LIMIT_MB * 0.9:
        return None
    # Simple heuristic: if we're near limit, suggest 2
    if peak_memory_mb >= CONFLUENCE_MEMORY_LIMIT_MB:
        return 2
    return None
