"""
Intelligent error recovery: PRD §9.2 error format, single classification map, reliability metrics.
Handler only returns response dicts; no writes. Clean-failure enforced in integration_agent and client.
"""

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Category -> (message, intelligence_suggestion, fallback_available, actions)
CLASSIFICATION: dict[str, tuple[str, str, bool, list[str]]] = {
    "network": (
        "Can't reach Confluence, check connection.",
        "Check your internet connection and Confluence URL.",
        True,
        ["Retry", "Cancel"],
    ),
    "auth": (
        "Invalid credentials, update in settings.",
        "Update your Confluence URL, email, and API token in settings.",
        False,
        ["Update Settings", "Cancel"],
    ),
    "rate_limit": (
        "Too many requests, retrying in 30 seconds.",
        "Wait for the retry or reduce request frequency.",
        True,
        ["Retry", "Cancel"],
    ),
    "content": (
        "AI could not determine optimal format.",
        "Try different files or simplify content.",
        True,
        ["Retry", "Cancel"],
    ),
    "not_found": (
        "Page or resource not found.",
        "Check the Confluence space and page ID.",
        False,
        ["Retry", "Cancel"],
    ),
    "permission_denied": (
        "Permission denied. Check access rights.",
        "Verify you have permission to create pages in this space.",
        False,
        ["Update Settings", "Cancel"],
    ),
    "disk_full": (
        "Storage issue. Operation could not complete.",
        "Free disk space and try again.",
        False,
        ["Retry", "Cancel"],
    ),
    "db_connection": (
        "Database connection lost. Reconnecting.",
        "The system will try to reconnect automatically.",
        True,
        ["Retry", "Cancel"],
    ),
    "encoding": (
        "File encoding issue. Use UTF-8 text.",
        "Save the file as UTF-8 and try again.",
        True,
        ["Retry", "Cancel"],
    ),
    "invalid_template": (
        "Invalid template format. Using default.",
        "A default template was applied.",
        True,
        ["Retry", "Cancel"],
    ),
    "intelligence_error": (
        "AI could not determine format.",
        "Try different content or retry.",
        True,
        ["Retry", "Cancel"],
    ),
    "template_matching": (
        "No suitable template found. Using fallback.",
        "Intelligent fallback was applied.",
        True,
        ["Retry", "Cancel"],
    ),
    "agent_coordination": (
        "A step failed. Operation did not complete.",
        "Retry the operation. If it persists, check settings.",
        True,
        ["Retry", "Cancel"],
    ),
    "resource_limit": (
        "Resource limit reached; try fewer or smaller files.",
        "Reduce the number or size of files.",
        True,
        ["Retry", "Cancel"],
    ),
    "other": (
        "Something went wrong.",
        "Check the message and try again or update settings.",
        False,
        ["Retry", "Update Settings", "Cancel"],
    ),
}


def _classify(exc: BaseException) -> str:
    t = type(exc).__name__
    msg = str(exc).lower()
    # Network: by type name or message first (robust in CI when requests import context may differ)
    if "ConnectionError" in t or "Timeout" in t or "ConnectTimeout" in t or "ReadTimeout" in t:
        return "network"
    if "connection" in msg or "timeout" in msg or "network" in msg or "refused" in msg or "reach" in msg:
        return "network"
    if isinstance(exc, OSError) and (
        "connection" in msg or "timeout" in msg or "refused" in msg or "reach" in msg
    ):
        return "network"
    try:
        import requests.exceptions as req_exc
        if isinstance(exc, (req_exc.ConnectionError, req_exc.Timeout)):
            return "network"
    except ImportError:
        pass
    resp = getattr(exc, "response", None)
    if resp is not None and getattr(resp, "status_code", None) is not None:
        sc = resp.status_code
        if sc == 401:
            return "auth"
        if sc == 429:
            return "rate_limit"
        if sc == 404:
            return "not_found"
        if sc == 403:
            return "permission_denied"
    if "401" in msg or "unauthorized" in msg or "auth" in msg or "credential" in msg:
        return "auth"
    if "429" in msg or "rate" in msg or "too many" in msg:
        return "rate_limit"
    if "404" in msg or "not found" in msg:
        return "not_found"
    if "403" in msg or "permission" in msg or "forbidden" in msg:
        return "permission_denied"
    if "disk" in msg or "storage" in msg or ("write" in msg and "fail" in msg):
        return "disk_full"
    if "database" in msg or "db" in msg or ("connection" in msg and "lost" in msg):
        return "db_connection"
    if "encoding" in msg or "utf" in msg or "decode" in msg:
        return "encoding"
    if "template" in msg and "invalid" in msg:
        return "invalid_template"
    if "intelligence" in msg or ("format" in msg and "determine" in msg):
        return "intelligence_error"
    if "template" in msg and "match" in msg:
        return "template_matching"
    if "agent" in msg or "coordination" in msg:
        return "agent_coordination"
    if "resource" in msg or "memory" in msg:
        return "resource_limit"
    return "other"


def prd_error_response(
    error_code: str,
    message: str | None = None,
    intelligence_suggestion: str | None = None,
    fallback_available: bool = False,
    intelligence_confidence: float = 0.0,
    category: str | None = None,
) -> dict[str, Any]:
    """Build PRD §9.2 error response. If category given, fill from CLASSIFICATION."""
    if category and category in CLASSIFICATION:
        msg, sugg, fallback, acts = CLASSIFICATION[category]
        out = {
            "error": error_code,
            "message": message or msg,
            "intelligence_suggestion": intelligence_suggestion or sugg,
            "fallback_available": fallback if message is None else fallback_available,
            "intelligence_confidence": intelligence_confidence,
        }
        out["actions"] = acts
        out["category"] = category
        return out
    return {
        "error": error_code,
        "message": message or "Something went wrong.",
        "intelligence_suggestion": intelligence_suggestion or "Check the message and try again.",
        "fallback_available": fallback_available,
        "intelligence_confidence": intelligence_confidence,
        "actions": ["Retry", "Update Settings", "Cancel"],
        "category": "other",
    }


def handle_error(exc: BaseException, error_code: str = "error") -> dict[str, Any]:
    """Classify exception and return PRD §9.2 error response. No corruption; clean failure."""
    category = _classify(exc)
    return prd_error_response(error_code=error_code, intelligence_confidence=0.0, category=category)


def get_actions_for_category(category: str) -> list[str]:
    if category in CLASSIFICATION:
        return list(CLASSIFICATION[category][3])
    return ["Retry", "Update Settings", "Cancel"]


@dataclass
class ReliabilityMetrics:
    success_count: int = 0
    failure_count: int = 0
    auto_recovery_count: int = 0
    user_intervention_count: int = 0

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return (self.success_count / total * 100.0) if total else 0.0

    @property
    def auto_recovery_rate(self) -> float:
        return (self.auto_recovery_count / self.failure_count * 100.0) if self.failure_count else 0.0

    @property
    def user_intervention_rate(self) -> float:
        total = self.success_count + self.failure_count
        return (self.user_intervention_count / total * 100.0) if total else 0.0


_metrics = ReliabilityMetrics()


def record_success() -> None:
    _metrics.success_count += 1


def record_failure(auto_recovered: bool = False, user_intervention: bool = False) -> None:
    _metrics.failure_count += 1
    if auto_recovered:
        _metrics.auto_recovery_count += 1
    if user_intervention:
        _metrics.user_intervention_count += 1


def get_reliability_metrics() -> dict[str, Any]:
    return {
        "success_rate": _metrics.success_rate,
        "auto_recovery_rate": _metrics.auto_recovery_rate,
        "user_intervention_rate": _metrics.user_intervention_rate,
    }
