"""
Confluence API client. Reuses a single HTTP session for all Confluence API calls.
No new connection pool: one client/session per app context.
Ollama is shared with RAG; this module does not spawn a second Ollama instance.
Rate limiting/retries should not block the event loop for long so UI stays responsive.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# One session per process; lazy-created
_session: Any = None


def _get_session() -> Any:
    """Lazy-create a single requests Session for Confluence API calls."""
    global _session
    if _session is None:
        try:
            import requests
            _session = requests.Session()
        except ImportError:
            logger.warning("requests not installed; Confluence API calls will fail")
            _session = None
    return _session


def get_client() -> Any:
    """
    Return the shared Confluence HTTP client (Session).
    Use this for all Confluence API calls so RAG and other flows do not create competing connections.
    """
    return _get_session()


def create_page(
    base_url: str,
    space_key: str,
    title: str,
    body_storage_value: str,
    auth: tuple[str, str] | None = None,
) -> dict[str, Any]:
    """
    Create a Confluence page via REST API. Uses shared session.
    auth: (email, api_token) for Basic auth.
    Returns response JSON or raises on error.
    """
    client = get_client()
    if client is None:
        raise RuntimeError("HTTP client not available (requests not installed?)")
    url = f"{base_url.rstrip('/')}/rest/api/content"
    payload = {
        "type": "page",
        "title": title,
        "space": {"key": space_key},
        "body": {"storage": {"value": body_storage_value, "representation": "storage"}},
    }
    kwargs: dict[str, Any] = {"json": payload, "timeout": 30}
    if auth:
        kwargs["auth"] = auth
    resp = client.post(url, **kwargs)
    resp.raise_for_status()
    return resp.json()
