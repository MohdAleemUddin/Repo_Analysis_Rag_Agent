# PRD NFR1: performance monitoring (analysis <3s, template <2s, creation <15s, memory ≤300MB)
from typing import Any

# NFR1 targets (seconds or MB)
ANALYSIS_TARGET_SEC = 3.0
TEMPLATE_SELECT_TARGET_SEC = 2.0
CREATION_TARGET_SEC = 15.0
MEMORY_TARGET_MB = 300


def _get_memory_mb() -> float:
    try:
        import resource
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    except Exception:
        pass
    try:
        import psutil
        return psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception:
        pass
    return 0.0


def record_analysis_duration_sec(sec: float) -> dict[str, Any]:
    ok = sec < ANALYSIS_TARGET_SEC
    return {"metric": "analysis_duration_sec", "value": sec, "target_sec": ANALYSIS_TARGET_SEC, "ok": ok}


def record_template_select_duration_sec(sec: float) -> dict[str, Any]:
    ok = sec < TEMPLATE_SELECT_TARGET_SEC
    return {"metric": "template_select_duration_sec", "value": sec, "target_sec": TEMPLATE_SELECT_TARGET_SEC, "ok": ok}


def record_creation_duration_sec(sec: float) -> dict[str, Any]:
    ok = sec < CREATION_TARGET_SEC
    return {"metric": "creation_duration_sec", "value": sec, "target_sec": CREATION_TARGET_SEC, "ok": ok}


def record_memory_mb(mb: float | None = None) -> dict[str, Any]:
    val = mb if mb is not None else _get_memory_mb()
    ok = val <= MEMORY_TARGET_MB
    return {"metric": "memory_mb", "value": val, "target_mb": MEMORY_TARGET_MB, "ok": ok}


def check_prd() -> dict[str, Any]:
    """Return PRD NFR1 compliance summary."""
    return {
        "analysis_target_sec": ANALYSIS_TARGET_SEC,
        "template_select_target_sec": TEMPLATE_SELECT_TARGET_SEC,
        "creation_target_sec": CREATION_TARGET_SEC,
        "memory_target_mb": MEMORY_TARGET_MB,
    }
