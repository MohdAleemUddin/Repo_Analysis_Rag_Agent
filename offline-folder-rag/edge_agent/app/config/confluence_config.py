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
) -> tuple[Any, float]:
    """Perform a single Confluence REST request. Returns (response_json or None, latency_sec)."""
    try:
        import requests
    except ImportError:
        return None, 0.0
    url = f"{base_url.rstrip('/')}{path}"
    start = time.perf_counter()
    try:
        resp = requests.request(
            method,
            url,
            auth=auth,
            timeout=timeout,
            headers={"Accept": "application/json"},
        )
        elapsed = time.perf_counter() - start
        if resp.status_code == 200:
            try:
                return resp.json(), elapsed
            except Exception:
                return None, elapsed
        return None, elapsed
    except Exception:
        elapsed = time.perf_counter() - start
        return None, elapsed


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
    data, elapsed = _confluence_request(
        base_url,
        "/rest/api/user/current",
        auth,
        timeout=CONNECTION_TEST_TIMEOUT_SEC,
    )
    result["latency_ms"] = round(elapsed * 1000)
    if data is None:
        result["error"] = "Connection failed or invalid response (check URL and credentials)"
        return result
    result["ok"] = True
    result["error"] = ""
    # Optionally fetch spaces for convenience
    spaces_data, _ = _confluence_request(
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
    data, _ = _confluence_request(
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
