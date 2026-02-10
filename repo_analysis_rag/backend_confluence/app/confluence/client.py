"""
Confluence API client. Reuses a single HTTP session for all Confluence API calls.
No new connection pool: one client/session per app context.
Ollama is shared with RAG; this module does not spawn a second Ollama instance.
Network: 3 retries with exponential backoff. Rate limit (429): wait 30s then retry.
"""

import time
from typing import Any

from app.logging.logger import get_logger

logger = get_logger(__name__)

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


def _validate_token(token: str | None) -> None:
    """Validate token when auth is provided (TC-DV-004). Raises ValueError if invalid or empty."""
    if token is None or not isinstance(token, str):
        raise ValueError("API token must be a non-empty string when auth is provided")
    t = token.strip()
    if not t:
        raise ValueError("API token must be a non-empty string when auth is provided")


def create_page(
    base_url: str,
    space_key: str,
    title: str,
    body_storage_value: str,
    auth: tuple[str, str] | None = None,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a Confluence page via REST API. Uses shared session.
    Confluence operations use workspace-scoped credentials for project isolation when
    workspace_id is provided (credentials from get_confluence_config(workspace_id)).
    Network: 3 retries (1s, 2s, 4s backoff). Rate limit (429): wait 30s then retry.
    Auth/403/404: no retry; raise so routes return PRD error.
    """
    if workspace_id is not None:
        from app.config.config import get_confluence_config

        cfg = get_confluence_config(workspace_id=workspace_id)
        base_url = cfg["base_url"]
        auth = cfg.get("auth")
    base = base_url.strip().lower()
    if not base.startswith("https://"):
        raise ValueError("Confluence base_url must use HTTPS")
    if auth is not None:
        _validate_token(auth[1] if len(auth) > 1 else None)
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
                logger.warning(
                    "Rate limit (429); waiting %s s then retry.",
                    RATE_LIMIT_WAIT_SECONDS,
                )
                time.sleep(RATE_LIMIT_WAIT_SECONDS)
                resp = client.post(url, **kwargs)
            if resp.status_code == 400:
                try:
                    body = getattr(resp, "text", None) or (
                        resp.content[:1000].decode("utf-8", errors="replace")
                        if getattr(resp, "content", None)
                        else "no body"
                    )
                    logger.warning(
                        "Confluence 400 Bad Request response: %s",
                        (body or "no body")[:1000],
                    )
                except Exception:
                    pass
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

                is_network = isinstance(
                    e,
                    (
                        req_exc.ConnectionError,
                        req_exc.Timeout,
                        ConnectionError,
                        OSError,
                    ),
                )
            except ImportError:
                is_network = (
                    isinstance(e, (ConnectionError, OSError))
                    or "timeout" in type(e).__name__.lower()
                )
            if is_network and attempt < NETWORK_RETRIES:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
    if last_exc:
        raise last_exc
    raise RuntimeError("Create page failed after retries")
