"""
Confluence API client. Reuses a single HTTP session for all Confluence API calls.
No new connection pool: one client/session per app context.
Ollama is shared with RAG; this module does not spawn a second Ollama instance.
Network: 3 retries with exponential backoff. Rate limit (429): wait 30s then retry.
"""

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)

_session: Any = None
NETWORK_RETRIES = 3
RATE_LIMIT_WAIT_SECONDS = 30


def _get_session() -> Any:
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
    Network: 3 retries with exponential backoff (1s, 2s, 4s). Rate limit (429): wait 30s then retry.
    Auth/403/404: no retry; raise so routes return PRD error.
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

    last_exc: BaseException | None = None
    backoff = 1.0
    for attempt in range(NETWORK_RETRIES + 1):
        try:
            resp = client.post(url, **kwargs)
            if resp.status_code == 429:
                logger.warning("Rate limit (429); waiting %s s then retry.", RATE_LIMIT_WAIT_SECONDS)
                time.sleep(RATE_LIMIT_WAIT_SECONDS)
                resp = client.post(url, **kwargs)
            if resp.status_code in (401, 403, 404):
                resp.raise_for_status()
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            last_exc = e
            r = getattr(e, "response", None)
            if r is not None:
                if r.status_code == 429:
                    time.sleep(RATE_LIMIT_WAIT_SECONDS)
                    continue
                if r.status_code in (401, 403, 404):
                    raise
            try:
                import requests.exceptions as req_exc
                is_network = isinstance(e, (req_exc.ConnectionError, req_exc.Timeout, ConnectionError, OSError))
            except ImportError:
                is_network = isinstance(e, (ConnectionError, OSError)) or "timeout" in type(e).__name__.lower()
            if is_network and attempt < NETWORK_RETRIES:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
    if last_exc:
        raise last_exc
    raise RuntimeError("Create page failed after retries")
