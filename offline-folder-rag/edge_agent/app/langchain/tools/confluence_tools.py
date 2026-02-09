"""Confluence API tool wrapper. All Integration Agent Confluence calls go through this module."""

from __future__ import annotations

import time
from typing import Any

from app.logging.logger import get_logger

logger = get_logger(__name__)

RATE_LIMIT_WAIT_SECONDS = 30
MAX_RETRIES = 3


def _get_client() -> Any:
    from app.confluence.client import get_client
    return get_client()


def confluence_create_page(
    base_url: str,
    space_key: str,
    title: str,
    body_storage_value: str,
    auth: tuple[str, str] | None = None,
) -> dict[str, Any]:
    """
    Create a Confluence page. LangChain-tool-compatible: invocable with args dict.
    Wraps app.confluence.client.create_page with retries and rate-limit handling.
    """
    from app.confluence.client import create_page as _create_page
    last_exc: BaseException | None = None
    backoff = 1.0
    for attempt in range(MAX_RETRIES + 1):
        try:
            result = _create_page(
                base_url=base_url,
                space_key=space_key,
                title=title,
                body_storage_value=body_storage_value,
                auth=auth,
            )
            return result
        except Exception as e:
            last_exc = e
            resp = getattr(e, "response", None)
            if resp is not None and getattr(resp, "status_code", None) == 429:
                logger.warning("Rate limit (429); waiting %s s.", RATE_LIMIT_WAIT_SECONDS)
                time.sleep(RATE_LIMIT_WAIT_SECONDS)
                continue
            if attempt < MAX_RETRIES:
                time.sleep(backoff)
                backoff *= 2
                continue
            raise
    if last_exc:
        raise last_exc
    raise RuntimeError("Create page failed after retries")


def confluence_get_page(
    base_url: str,
    page_id: str,
    auth: tuple[str, str] | None = None,
) -> dict[str, Any]:
    """
    Get a Confluence page by id. For verification after create.
    Wraps HTTP GET; returns page dict or raises.
    """
    client = _get_client()
    if client is None:
        raise RuntimeError("HTTP client not available")
    url = f"{base_url.rstrip('/')}/rest/api/content/{page_id}"
    kwargs: dict[str, Any] = {"timeout": 15}
    if auth:
        kwargs["auth"] = auth
    resp = client.get(url, **kwargs)
    resp.raise_for_status()
    return resp.json()


def invoke_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    """
    Invoke a Confluence tool by name with an args dict (LangChain-tool-compatible).
    Supported: create_page, get_page.
    """
    if name == "create_page":
        return confluence_create_page(
            base_url=args.get("base_url", ""),
            space_key=args.get("space_key", ""),
            title=args.get("title", ""),
            body_storage_value=args.get("body_storage_value", ""),
            auth=args.get("auth"),
        )
    if name == "get_page":
        return confluence_get_page(
            base_url=args.get("base_url", ""),
            page_id=args.get("page_id", ""),
            auth=args.get("auth"),
        )
    raise ValueError(f"Unknown tool: {name}")
