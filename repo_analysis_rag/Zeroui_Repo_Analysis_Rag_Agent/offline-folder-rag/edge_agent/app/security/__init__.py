from __future__ import annotations

"""Security utilities shared by the FastAPI app."""

from fastapi import HTTPException, Header

from .token_store import get_or_create_token

TOKEN_HEADER = "X-LOCAL-TOKEN"


def verify_token(token: str | None) -> None:
    expected = get_or_create_token()
    if not token or token != expected:
        raise HTTPException(
            status_code=401,
            detail={
                "error_code": "INVALID_TOKEN",
                "message": "The provided token is missing or invalid.",
                "remediation": "Please provide a valid X-LOCAL-TOKEN in the request headers.",
            },
        )


def require_token(x_local_token: str | None = Header(default=None, alias=TOKEN_HEADER)) -> str:
    verify_token(x_local_token)
    return x_local_token or ""
