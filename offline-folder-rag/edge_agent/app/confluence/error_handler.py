# PRD User Story 13: error classification, retries, user-facing messages (NFR2)
from typing import Any

# Error types per PRD §9.2
NETWORK = "network"
AUTH = "auth"
RATE_LIMIT = "rate_limit"
CONTENT = "content"
PERMISSION = "permission"
VALIDATION = "validation"

# Retry config (NFR2: 3x with backoff for network)
MAX_RETRIES = 3
INITIAL_BACKOFF_SEC = 1.0


def classify_error(e: Exception) -> str:
    """Classify exception into PRD error type."""
    msg = str(e).lower()
    if "connection" in msg or "timeout" in msg or "network" in msg or "unreachable" in msg:
        return NETWORK
    if "auth" in msg or "401" in msg or "unauthorized" in msg or "token" in msg or "credential" in msg:
        return AUTH
    if "429" in msg or "rate" in msg or "limit" in msg or "throttl" in msg:
        return RATE_LIMIT
    if "permission" in msg or "403" in msg or "forbidden" in msg:
        return PERMISSION
    if "format" in msg or "invalid" in msg or "validation" in msg:
        return VALIDATION
    return CONTENT


def user_message(error_type: str) -> str:
    """User-facing message per PRD §9.2."""
    if error_type == NETWORK:
        return "Can't reach Confluence, check connection"
    if error_type == AUTH:
        return "Invalid credentials, update in settings"
    if error_type == RATE_LIMIT:
        return "Too many requests, retrying in 30 seconds"
    if error_type == CONTENT:
        return "AI could not determine optimal format"
    if error_type == PERMISSION:
        return "Permission denied"
    if error_type == VALIDATION:
        return "Validation error"
    return "An error occurred"


def action_buttons(error_type: str) -> list[str]:
    """Suggested actions per PRD §9.2."""
    if error_type == AUTH:
        return ["Update Settings", "Cancel"]
    if error_type in (NETWORK, RATE_LIMIT):
        return ["Retry", "Cancel"]
    if error_type == CONTENT:
        return ["Retry", "Cancel"]
    return ["Retry", "Cancel"]


def handle_error(e: Exception) -> dict[str, Any]:
    """Return PRD §9.2 error format with type, message, and actions."""
    t = classify_error(e)
    return {
        "error": "intelligence_error",
        "error_type": t,
        "message": user_message(t),
        "intelligence_suggestion": "Try providing more context or different files" if t == CONTENT else "",
        "fallback_available": t in (CONTENT, VALIDATION),
        "actions": action_buttons(t),
    }


def backoff_sec(attempt: int) -> float:
    """Exponential backoff for retries (attempt 0-based)."""
    return INITIAL_BACKOFF_SEC * (2.0 ** attempt)
