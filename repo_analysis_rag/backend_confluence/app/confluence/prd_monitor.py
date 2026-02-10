"""
PRD performance monitor for Confluence.
Measures per-file analysis, template selection, e2e create; memory limit; emits records.
"""

import time
import uuid
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Generator

from app.config.config import (
    ANALYSIS_MAX_SECONDS_PER_FILE,
    CONFLUENCE_MEMORY_LIMIT_MB,
    CREATE_E2E_MAX_SECONDS,
    TEMPLATE_SELECTION_MAX_SECONDS,
)
from app.logging.logger import get_logger

logger = get_logger(__name__)

# Re-export config constants for backward compatibility (single source of truth: config)
ANALYSIS_TARGET_SEC = float(ANALYSIS_MAX_SECONDS_PER_FILE)
TEMPLATE_SELECT_TARGET_SEC = float(TEMPLATE_SELECTION_MAX_SECONDS)
CREATION_TARGET_SEC = float(CREATE_E2E_MAX_SECONDS)
MEMORY_TARGET_MB = float(CONFLUENCE_MEMORY_LIMIT_MB)
# US-16 project documentation targets (not in config)
PROJECT_SCAN_TARGET_SEC = 10.0
PROJECT_FULL_TARGET_SEC = 30.0


def record_analysis_duration_sec(sec: float) -> dict[str, Any]:
    ok = sec < ANALYSIS_MAX_SECONDS_PER_FILE
    return {
        "metric": "analysis_duration_sec",
        "value": sec,
        "target_sec": ANALYSIS_MAX_SECONDS_PER_FILE,
        "ok": ok,
    }


def record_template_select_duration_sec(sec: float) -> dict[str, Any]:
    ok = sec < TEMPLATE_SELECTION_MAX_SECONDS
    return {
        "metric": "template_select_duration_sec",
        "value": sec,
        "target_sec": TEMPLATE_SELECTION_MAX_SECONDS,
        "ok": ok,
    }


def record_creation_duration_sec(sec: float) -> dict[str, Any]:
    ok = sec < CREATE_E2E_MAX_SECONDS
    return {
        "metric": "creation_duration_sec",
        "value": sec,
        "target_sec": CREATE_E2E_MAX_SECONDS,
        "ok": ok,
    }


def record_memory_mb(mb: float | None = None) -> dict[str, Any]:
    val = mb if mb is not None else _get_process_memory_mb()
    ok = val <= CONFLUENCE_MEMORY_LIMIT_MB
    return {
        "metric": "memory_mb",
        "value": val,
        "target_mb": CONFLUENCE_MEMORY_LIMIT_MB,
        "ok": ok,
    }


def check_prd() -> dict[str, Any]:
    """Return PRD NFR1 compliance summary (single source: config)."""
    return {
        "analysis_target_sec": ANALYSIS_MAX_SECONDS_PER_FILE,
        "template_select_target_sec": TEMPLATE_SELECTION_MAX_SECONDS,
        "creation_target_sec": CREATE_E2E_MAX_SECONDS,
        "memory_target_mb": CONFLUENCE_MEMORY_LIMIT_MB,
        "project_scan_target_sec": PROJECT_SCAN_TARGET_SEC,
        "project_full_target_sec": PROJECT_FULL_TARGET_SEC,
    }


try:
    import psutil

    _PSUTIL_AVAILABLE = True
except ImportError:
    _PSUTIL_AVAILABLE = False
    psutil = None  # type: ignore


@dataclass
class PerformanceRecord:
    """Single performance record per Confluence operation."""

    operation_id: str
    per_file_analysis_ms: list[float] = field(default_factory=list)
    template_selection_ms: float = 0.0
    create_e2e_ms: float = 0.0
    peak_memory_mb: float = 0.0
    targets_met: dict[str, bool] = field(
        default_factory=dict
    )  # e.g. analysis_per_file, template, create_e2e, memory
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        return {
            "operation_id": self.operation_id,
            "per_file_analysis_ms": self.per_file_analysis_ms,
            "template_selection_ms": self.template_selection_ms,
            "create_e2e_ms": self.create_e2e_ms,
            "peak_memory_mb": self.peak_memory_mb,
            "targets_met": self.targets_met,
            "timestamp": self.timestamp,
        }


# --- In-operation state (one active operation per thread/process) ---
_current_operation_id: str | None = None
_current_peak_memory_mb: float = 0.0
_current_record: PerformanceRecord | None = None


def _get_process_memory_mb() -> float:
    if _PSUTIL_AVAILABLE and psutil is not None:
        try:
            return psutil.Process().memory_info().rss / (1024 * 1024)
        except Exception:
            return 0.0
    return 0.0


def _update_peak() -> float:
    global _current_peak_memory_mb
    mb = _get_process_memory_mb()
    if mb > _current_peak_memory_mb:
        _current_peak_memory_mb = mb
    return mb


def check_memory_before_step() -> bool:
    """
    Check if memory is below limit. Call before each heavy step.
    Returns True if safe, False if at/over limit (caller should abort or degrade).
    """
    mb = _update_peak()
    ok = mb < CONFLUENCE_MEMORY_LIMIT_MB
    if not ok:
        logger.warning(
            "PRD memory check failed: current %.1f MB >= limit %s MB",
            mb,
            CONFLUENCE_MEMORY_LIMIT_MB,
        )
    return ok


def start_operation(operation_id: str | None = None) -> str:
    """Start a new Confluence operation; returns operation_id. Resets peak memory."""
    global _current_operation_id, _current_peak_memory_mb, _current_record
    _current_operation_id = operation_id or str(uuid.uuid4())
    _current_peak_memory_mb = _get_process_memory_mb()
    _current_record = PerformanceRecord(
        operation_id=_current_operation_id,
        targets_met={
            "analysis_per_file": True,
            "template_selection": True,
            "create_e2e": True,
            "memory": True,
        },
    )
    return _current_operation_id


def get_current_operation_id() -> str | None:
    return _current_operation_id


def get_current_record() -> PerformanceRecord | None:
    return _current_record


def record_confluence_operation(
    operation_id: str,
    per_file_analysis_ms: list[float],
    template_selection_ms: float,
    create_e2e_ms: float,
    peak_memory_mb: float | None = None,
) -> PerformanceRecord:
    """
    Build and finalize a performance record for a Confluence operation.
    Evaluates targets_met and logs alerts if missed.
    """
    if peak_memory_mb is None:
        peak_memory_mb = _current_peak_memory_mb
    analysis_ok = all(
        ms < ANALYSIS_MAX_SECONDS_PER_FILE * 1000 for ms in per_file_analysis_ms
    )
    template_ok = template_selection_ms < TEMPLATE_SELECTION_MAX_SECONDS * 1000
    create_ok = create_e2e_ms < CREATE_E2E_MAX_SECONDS * 1000
    memory_ok = peak_memory_mb <= CONFLUENCE_MEMORY_LIMIT_MB

    record = PerformanceRecord(
        operation_id=operation_id,
        per_file_analysis_ms=per_file_analysis_ms,
        template_selection_ms=template_selection_ms,
        create_e2e_ms=create_e2e_ms,
        peak_memory_mb=peak_memory_mb,
        targets_met={
            "analysis_per_file": analysis_ok,
            "template_selection": template_ok,
            "create_e2e": create_ok,
            "memory": memory_ok,
        },
    )

    # Alerts
    if not analysis_ok:
        for i, ms in enumerate(per_file_analysis_ms):
            if ms >= ANALYSIS_MAX_SECONDS_PER_FILE * 1000:
                logger.warning(
                    "PRD target missed: analysis %.2f s for file index %s (limit %s s)",
                    ms / 1000,
                    i,
                    ANALYSIS_MAX_SECONDS_PER_FILE,
                )
    if not template_ok:
        logger.warning(
            "PRD target missed: template selection %.2f s (limit %s s)",
            template_selection_ms / 1000,
            TEMPLATE_SELECTION_MAX_SECONDS,
        )
    if not create_ok:
        logger.warning(
            "PRD target missed: create e2e %.2f s (limit %s s)",
            create_e2e_ms / 1000,
            CREATE_E2E_MAX_SECONDS,
        )
    if not memory_ok:
        logger.warning(
            "PRD target missed: peak memory %.1f MB (limit %s MB)",
            peak_memory_mb,
            CONFLUENCE_MEMORY_LIMIT_MB,
        )

    logger.info(
        "Confluence op %s: analysis_ok=%s template_ok=%s create_ok=%s memory_ok=%s",
        operation_id,
        analysis_ok,
        template_ok,
        create_ok,
        memory_ok,
    )
    return record


# --- Timers (context managers) ---


@contextmanager
def timer_per_file_analysis(file_index: int = 0) -> Generator[None, None, None]:
    """Context manager to measure per-file analysis time (target < 3s per file)."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        _update_peak()
        if _current_record is not None:
            _current_record.per_file_analysis_ms.append(elapsed_ms)
            if elapsed_ms >= ANALYSIS_MAX_SECONDS_PER_FILE * 1000:
                _current_record.targets_met["analysis_per_file"] = False
                logger.warning(
                    "PRD target missed: analysis %.2f s for file index %s (limit %s s)",
                    elapsed_ms / 1000,
                    file_index,
                    ANALYSIS_MAX_SECONDS_PER_FILE,
                )


@contextmanager
def timer_template_selection() -> Generator[None, None, None]:
    """Context manager to measure template selection time (< 2s)."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        _update_peak()
        if _current_record is not None:
            _current_record.template_selection_ms = elapsed_ms
            if elapsed_ms >= TEMPLATE_SELECTION_MAX_SECONDS * 1000:
                _current_record.targets_met["template_selection"] = False
                logger.warning(
                    "PRD target missed: template selection %.2f s (limit %s s)",
                    elapsed_ms / 1000,
                    TEMPLATE_SELECTION_MAX_SECONDS,
                )


@contextmanager
def timer_create_e2e() -> Generator[None, None, None]:
    """Context manager to measure end-to-end create time including API (< 15s)."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        _update_peak()
        if _current_record is not None:
            _current_record.create_e2e_ms = elapsed_ms
            if elapsed_ms >= CREATE_E2E_MAX_SECONDS * 1000:
                _current_record.targets_met["create_e2e"] = False
                logger.warning(
                    "PRD target missed: create e2e %.2f s (limit %s s)",
                    elapsed_ms / 1000,
                    CREATE_E2E_MAX_SECONDS,
                )


def get_peak_memory_mb() -> float:
    """Return current tracked peak memory for the active operation."""
    return _current_peak_memory_mb


# --- Optional: store last N records for intelligence-status ---
_last_records: list[PerformanceRecord] = []
_LAST_RECORDS_MAX = 100


def append_record(record: PerformanceRecord) -> None:
    global _last_records
    _last_records.append(record)
    if len(_last_records) > _LAST_RECORDS_MAX:
        _last_records = _last_records[-_LAST_RECORDS_MAX:]


def get_last_records(n: int = 20) -> list[PerformanceRecord]:
    return _last_records[-n:] if _last_records else []


def verify_targets_met(record: PerformanceRecord | None) -> bool:
    """Return True iff all NFR1 targets are met. For regression tests and CI."""
    if record is None:
        return False
    return all(record.targets_met.values())
