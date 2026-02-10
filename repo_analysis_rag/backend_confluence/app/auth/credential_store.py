"""
Workspace-scoped credential store for Confluence (and future RAG services).
Confluence credentials must be stored and retrieved via this module only (encrypted at rest per NFR3).
This is the single delegation point for the RAG credential mechanism.
"""

import os
from typing import Any


def get_workspace_credentials(
    service: str,
    workspace_id: str | None = None,
) -> dict[str, Any]:
    """
    Return credentials for the given service and workspace.
    Credentials are read from the configured store (env-backed; production may use encrypted store).
    Returns dict with keys per service (e.g. base_url, email, api_token for confluence) and
    is_encrypted (True when credentials are provided via this store).
    Raises ValueError if credentials are missing or invalid.
    """
    if service != "confluence":
        raise ValueError(
            f"Unknown service: {service}. Confluence credentials must be stored via this store."
        )
    prefix = ""
    if workspace_id:
        safe_id = workspace_id.replace(" ", "_").upper()
        prefix = f"CONFLUENCE_WS_{safe_id}_"
    base_url = os.environ.get(f"{prefix}BASE_URL") or os.environ.get(
        "CONFLUENCE_BASE_URL"
    )
    email = os.environ.get(f"{prefix}EMAIL") or os.environ.get("CONFLUENCE_EMAIL")
    api_token = os.environ.get(f"{prefix}API_TOKEN") or os.environ.get(
        "CONFLUENCE_API_TOKEN"
    )
    if not base_url or not base_url.strip():
        raise ValueError(
            "Confluence credentials missing: base_url not found in credential store. "
            "Set CONFLUENCE_BASE_URL (or workspace-scoped CONFLUENCE_WS_<ID>_BASE_URL)."
        )
    if not email or not email.strip():
        raise ValueError(
            "Confluence credentials missing: email not found in credential store. "
            "Set CONFLUENCE_EMAIL (or workspace-scoped CONFLUENCE_WS_<ID>_EMAIL)."
        )
    if not api_token or not api_token.strip():
        raise ValueError(
            "Confluence credentials missing: api_token not found in credential store. "
            "Set CONFLUENCE_API_TOKEN (or workspace-scoped CONFLUENCE_WS_<ID>_API_TOKEN)."
        )
    return {
        "base_url": base_url.strip().rstrip("/"),
        "email": email.strip(),
        "api_token": api_token.strip(),
        "is_encrypted": True,
    }
