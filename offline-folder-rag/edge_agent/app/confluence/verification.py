"""
Verification of Confluence security requirements (User Story 14).
Checks HTTPS enforcement, token masking, and credential store usage.
"""
from __future__ import annotations


def verify_confluence_security() -> dict[str, bool]:
    """
    Verify that Confluence security requirements are met.
    Returns a dict with keys https_enforcement, token_masking, uses_credential_store
    and boolean values indicating whether each check passed.
    """
    results: dict[str, bool] = {
        "https_enforcement": False,
        "token_masking": False,
        "uses_credential_store": False,
    }
    # HTTPS enforcement: non-HTTPS base_url must raise ValueError with "must use HTTPS"
    try:
        from app.confluence.client import create_page

        create_page("http://example.com", "DOC", "T", "<p>x</p>", None)
    except ValueError as e:
        if "must use HTTPS" in str(e):
            results["https_enforcement"] = True
    except Exception:
        pass
    # Token masking: mask_tokens must hide Bearer, token=, Basic auth, JSON api_token
    try:
        from app.logging.logger import mask_tokens

        raw1 = "Authorization: Bearer sk-secret-123 and token=abc.xyz"
        masked1 = mask_tokens(raw1)
        basic_raw = "Authorization: Basic dXNlcjp0b2tlbg=="
        basic_masked = mask_tokens(basic_raw)
        json_raw = '{"api_token": "sk-abc123"}'
        json_masked = mask_tokens(json_raw)
        if (
            "sk-secret-123" not in masked1
            and "abc.xyz" not in masked1
            and "***" in masked1
            and "dXNlcjp0b2tlbg==" not in basic_masked
            and "***" in basic_masked
            and "sk-abc123" not in json_masked
            and "***" in json_masked
        ):
            results["token_masking"] = True
    except Exception:
        pass
    # Credential store usage: get_confluence_config(workspace_id) must use the store and expose is_encrypted
    try:
        import os

        from app.config.config import get_confluence_config

        # Use a distinct workspace id so we don't rely on default env
        ws = "_verify_ws_"
        os.environ["CONFLUENCE_WS__VERIFY_WS__BASE_URL"] = "https://wiki.example.com"
        os.environ["CONFLUENCE_WS__VERIFY_WS__EMAIL"] = "u@example.com"
        os.environ["CONFLUENCE_WS__VERIFY_WS__API_TOKEN"] = "secret-token"
        try:
            cfg = get_confluence_config(workspace_id=ws)
            if cfg.get("is_encrypted") and cfg.get("base_url") and cfg.get("auth"):
                results["uses_credential_store"] = True
        finally:
            os.environ.pop("CONFLUENCE_WS__VERIFY_WS__BASE_URL", None)
            os.environ.pop("CONFLUENCE_WS__VERIFY_WS__EMAIL", None)
            os.environ.pop("CONFLUENCE_WS__VERIFY_WS__API_TOKEN", None)
    except Exception:
        pass
    return results
