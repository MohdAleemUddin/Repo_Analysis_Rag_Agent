# Confluence config: re-export from central config + edition, defaults, test-connection (User Story 10)
from __future__ import annotations

import time
from typing import Any

from .config import get_confluence_config
from .confluence_schema import ConfluenceCredentials, get_intelligent_defaults_model

__all__ = [
    "get_confluence_config",
    "detect_edition",
    "get_intelligent_defaults",
    "test_connection",
    "get_available_spaces",
    "get_preferred_space",
    "get_default_space_for_project_type",
]

CONNECTION_TEST_TIMEOUT_SEC = 5


def detect_edition(url: str) -> str:
    """Return 'cloud' for *.atlassian.net, else 'server'."""
    if not url or not isinstance(url, str):
        return "server"
    u = url.strip().lower()
    if ".atlassian.net" in u:
        return "cloud"
    return "server"


def get_intelligent_defaults(url: str | None = None) -> dict[str, Any]:
    """Return intelligent defaults (edition-based rate limit, learning on, etc.)."""
    return get_intelligent_defaults_model(url)


def _confluence_request(
    base_url: str,
    path: str,
    auth: tuple[str, str],
    timeout: int = CONNECTION_TEST_TIMEOUT_SEC,
    method: str = "GET",
) -> tuple[Any, float, int | None, bool]:
    """
    Perform a single Confluence REST request.
    Returns (response_json or None, latency_sec, status_code or None, parse_error).
    parse_error is True when status was 200 but response body was not valid JSON.
    """
    try:
        import requests
    except ImportError:
        return None, 0.0, None, False
    url = f"{base_url.rstrip('/')}{path}"
    start = time.perf_counter()
    status_code: int | None = None
    parse_error = False
    try:
        resp = requests.request(
            method,
            url,
            auth=auth,
            timeout=timeout,
            headers={"Accept": "application/json"},
        )
        elapsed = time.perf_counter() - start
        status_code = getattr(resp, "status_code", None)
        if resp.status_code == 200:
            try:
                return resp.json(), elapsed, 200, False
            except Exception:
                parse_error = True
                return None, elapsed, 200, True
        return None, elapsed, status_code, False
    except Exception as e:
        elapsed = time.perf_counter() - start
        resp = getattr(e, "response", None)
        if resp is not None:
            status_code = getattr(resp, "status_code", None)
        return None, elapsed, status_code, False


def test_connection(url: str, email: str, api_token: str) -> dict[str, Any]:
    """
    Test Confluence credentials. Calls /rest/api/user/current; optionally /rest/api/space.
    Returns dict with ok, spaces (if available), latency_ms, error (if not ok).
    Does not store credentials.
    """
    creds = ConfluenceCredentials(url=url, email=email, api_token=api_token)
    base_url = creds.url
    auth = (creds.email, creds.api_token)
    result: dict[str, Any] = {"ok": False, "latency_ms": 0, "error": ""}
    data, elapsed, status_code, parse_error = _confluence_request(
        base_url,
        "/rest/api/user/current",
        auth,
        timeout=CONNECTION_TEST_TIMEOUT_SEC,
    )
    result["latency_ms"] = round(elapsed * 1000)
    if data is None:
        if status_code == 401:
            result["error"] = "Confluence returned 401. Check email and API token."
        elif status_code == 403:
            result["error"] = "Confluence returned 403. Check permissions or space access."
        elif status_code == 404:
            result["error"] = "Confluence returned 404. Check Confluence URL (include /wiki)."
        elif status_code is not None:
            result["error"] = f"Confluence returned {status_code}."
        elif parse_error:
            result["error"] = "Confluence returned 200 but response was not JSON (login page or block?)."
        else:
            result["error"] = "Connection failed (timeout or network). Check URL and connectivity."
        return result
    result["ok"] = True
    result["error"] = ""
    # Optionally fetch spaces for convenience
    spaces_data, *_ = _confluence_request(
        base_url,
        "/rest/api/space?limit=50",
        auth,
        timeout=CONNECTION_TEST_TIMEOUT_SEC,
    )
    if spaces_data and isinstance(spaces_data, dict) and "results" in spaces_data:
        result["spaces"] = [
            {"key": s.get("key"), "name": s.get("name")}
            for s in spaces_data.get("results", [])
            if isinstance(s, dict) and s.get("key")
        ]
    else:
        result["spaces"] = []
    return result


def get_available_spaces(url: str, email: str, api_token: str) -> list[dict[str, Any]]:
    """Return list of {key, name} for Confluence spaces. Does not store credentials."""
    creds = ConfluenceCredentials(url=url, email=email, api_token=api_token)
    auth = (creds.email, creds.api_token)
    data, *_ = _confluence_request(
        creds.url,
        "/rest/api/space?limit=100",
        auth,
        timeout=CONNECTION_TEST_TIMEOUT_SEC,
    )
    if not data or not isinstance(data, dict) or "results" not in data:
        return []
    return [
        {"key": s.get("key"), "name": s.get("name")}
        for s in data.get("results", [])
        if isinstance(s, dict) and s.get("key")
    ]


def get_default_space_for_project_type(project_path: str) -> str:
    """
    Auto-select space by project type (US-2).
    Code projects -> DEV; Documentation projects -> DOCS; Mixed content -> DEV.
    """
    path = (project_path or "").strip().lower()
    if any(part in path for part in ("src", "app", "lib", "api", "packages")):
        return "DEV"
    if any(part in path for part in ("docs", "wiki", "doc")):
        return "DOCS"
    return "DEV"


def get_preferred_space(project_path: str | None) -> str:
    """
    Remember user's preferred Confluence space per project folder (US-2).
    1. Check database for previous space usage in this project
    2. Fallback to get_default_space_for_project_type()
    3. Stored in intelligent_creations.space_key column
    """
    if not project_path or not str(project_path).strip():
        return get_default_space_for_project_type("")
    from app.confluence.db_adapter import db_get_preferred_space
    stored = db_get_preferred_space(project_path.strip())
    return stored if stored else get_default_space_for_project_type(project_path)
