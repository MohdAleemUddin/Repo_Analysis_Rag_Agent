# Confluence config API: test-connection, spaces, validate, defaults (PRD §9.1)
from __future__ import annotations

import logging
from typing import Any

from app.config.confluence_config import (
    get_available_spaces,
    get_intelligent_defaults,
    test_connection,
)
from app.config.confluence_schema import ConfluenceCredentials, ConfluenceConfigValidate

logger = logging.getLogger(__name__)

MASK = "***"


def _mask_token(msg: str) -> str:
    """Replace any api_token-like content with *** for logging."""
    return msg.replace("api_token", "api_token=***") if msg else msg


# POST /confluence/config/test-connection
def test_connection_handler(body: dict[str, Any]) -> dict[str, Any]:
    """Validate credentials with schema; call test_connection; never log token."""
    if not body or not isinstance(body, dict):
        return {"ok": False, "error": "Request body must be JSON with url, email, api_token", "latency_ms": 0}
    try:
        creds = ConfluenceCredentials(
            url=str(body.get("url", "")).strip(),
            email=str(body.get("email", "")).strip(),
            api_token=str(body.get("api_token", "")).strip(),
        )
    except Exception as e:
        logger.info("Config test-connection validation failed: %s", _mask_token(str(e)))
        return {"ok": False, "error": str(e).replace("api_token", "api_token (masked)"), "latency_ms": 0}
    result = test_connection(creds.url, creds.email, creds.api_token)
    return result


# POST /confluence/config/spaces (credentials in body for consistency)
def spaces_handler(body: dict[str, Any]) -> dict[str, Any]:
    """Return list of spaces; credentials in body. Never log token."""
    if not body or not isinstance(body, dict):
        return {"spaces": [], "error": "Request body must be JSON with url, email, api_token"}
    try:
        creds = ConfluenceCredentials(
            url=str(body.get("url", "")).strip(),
            email=str(body.get("email", "")).strip(),
            api_token=str(body.get("api_token", "")).strip(),
        )
    except Exception as e:
        logger.info("Config spaces validation failed: %s", _mask_token(str(e)))
        return {"spaces": [], "error": str(e).replace("api_token", "api_token (masked)")}
    spaces = get_available_spaces(creds.url, creds.email, creds.api_token)
    return {"spaces": spaces}


# POST /confluence/config/validate
def validate_handler(body: dict[str, Any]) -> dict[str, Any]:
    """Run Pydantic validation on full or partial config; return valid and optional errors."""
    if body is None:
        body = {}
    if not isinstance(body, dict):
        return {"valid": False, "errors": ["Request body must be a JSON object"]}
    try:
        ConfluenceConfigValidate.model_validate(body)
        return {"valid": True}
    except Exception as e:
        errs = []
        if hasattr(e, "errors"):
            err_list = getattr(e, "errors", None)
            if callable(err_list):
                err_list = err_list()
            if err_list:
                for err in err_list:
                    loc = err.get("loc", ())
                    msg = err.get("msg", str(err))
                    errs.append(f"{'.'.join(str(x) for x in loc)}: {msg}")
        if not errs:
            errs = [str(e).replace("api_token", "api_token (masked)")]
        return {"valid": False, "errors": errs}


# GET /confluence/config/defaults?url=...
def defaults_handler(url: str | None = None) -> dict[str, Any]:
    """Return intelligent defaults; optional url for edition-based rate limit."""
    return get_intelligent_defaults(url)


def register_config_routes(router: Any) -> None:
    """Register Confluence config endpoints on the given router (FastAPI/Flask-style)."""
    try:
        from fastapi import Body, Query
    except (ImportError, AttributeError):
        Body = None
        Query = None

    if hasattr(router, "post") and hasattr(router, "get"):
        if Body is not None and Query is not None:
            def test_route(body: dict = Body(default=None)):
                return test_connection_handler(body or {})

            def spaces_route(body: dict = Body(default=None)):
                return spaces_handler(body or {})

            def validate_route(body: dict = Body(default=None)):
                return validate_handler(body or {})

            def defaults_route(url: str | None = Query(default=None)):
                return defaults_handler(url)

            router.post("/confluence/config/test-connection")(test_route)
            router.post("/confluence/config/spaces")(spaces_route)
            router.post("/confluence/config/validate")(validate_route)
            router.get("/confluence/config/defaults")(defaults_route)
        else:
            def test_route(request: Any = None):
                body = getattr(request, "json", lambda: {})() if request is not None else {}
                return test_connection_handler(body or {})

            def spaces_route(request: Any = None):
                body = getattr(request, "json", lambda: {})() if request is not None else {}
                return spaces_handler(body or {})

            def validate_route(request: Any = None):
                body = getattr(request, "json", lambda: {})() if request is not None else {}
                return validate_handler(body or {})

            def defaults_route(request: Any = None):
                url = None
                if request is not None and getattr(request, "query_params", None):
                    url = request.query_params.get("url")
                return defaults_handler(url)

            router.post("/confluence/config/test-connection")(test_route)
            router.post("/confluence/config/spaces")(spaces_route)
            router.post("/confluence/config/validate")(validate_route)
            router.get("/confluence/config/defaults")(defaults_route)
    else:
        router.config_handlers = {
            "test_connection": lambda body: test_connection_handler(body or {}),
            "spaces": lambda body: spaces_handler(body or {}),
            "validate": lambda body: validate_handler(body or {}),
            "defaults": lambda url=None: defaults_handler(url),
        }
