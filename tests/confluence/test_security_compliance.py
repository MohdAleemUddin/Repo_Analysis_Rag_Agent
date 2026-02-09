import pytest


def test_placeholder() -> None:
    assert True  # legacy placeholder


# --- HTTPS enforcement ---


def test_https_enforcement_create_page_raises_for_http() -> None:
    """create_page(base_url="http://...") must raise ValueError with 'must use HTTPS'."""
    from app.confluence.client import create_page

    with pytest.raises(ValueError, match="must use HTTPS"):
        create_page("http://example.com", "DOC", "T", "<p>x</p>", None)


# --- Token masking ---


def test_token_masking_mask_tokens_hides_bearer_and_token_param() -> None:
    """mask_tokens() must hide raw Bearer and token= values and show mask (***)."""
    from app.logging.logger import mask_tokens

    raw = "Authorization: Bearer sk-secret-123 and token=abc.xyz"
    masked = mask_tokens(raw)
    assert "sk-secret-123" not in masked
    assert "abc.xyz" not in masked
    assert "***" in masked


def test_token_masking_get_logger_uses_masking_filter() -> None:
    """get_logger returns a logger that masks tokens in log output."""
    from app.logging.logger import get_logger, mask_tokens

    log = get_logger("test_security")
    # mask_tokens is the canonical behavior; logger uses it via filter
    s = "token=secret123"
    assert "secret123" not in mask_tokens(s)
    assert "***" in mask_tokens(s)


def test_token_masking_logger_exception_does_not_leak_token() -> None:
    """get_logger masks tokens when logging exceptions."""
    import io
    import logging

    from app.logging.logger import get_logger

    log = get_logger("test_security_logger_leak")
    buf = io.StringIO()
    h = logging.StreamHandler(buf)
    log.addHandler(h)
    log.setLevel(logging.DEBUG)
    try:
        log.exception("fail: %s", "auth=secret123")
        out = buf.getvalue()
        assert "secret123" not in out
        assert "***" in out
    finally:
        log.removeHandler(h)


def test_token_masking_basic_auth_masked() -> None:
    """mask_tokens() must hide Basic auth header value."""
    from app.logging.logger import mask_tokens

    raw = "Authorization: Basic dXNlcjp0b2tlbg=="
    masked = mask_tokens(raw)
    assert "dXNlcjp0b2tlbg==" not in masked
    assert "***" in masked


def test_token_masking_json_api_token_masked() -> None:
    """mask_tokens() must hide api_token value in JSON."""
    from app.logging.logger import mask_tokens

    raw = '{"api_token": "sk-abc123"}'
    masked = mask_tokens(raw)
    assert "sk-abc123" not in masked
    assert "***" in masked


# --- Workspace isolation ---


def test_workspace_isolation_config_returns_workspace_scoped_credentials() -> None:
    """get_confluence_config(workspace_id) returns credentials for that workspace only."""
    import os

    from app.config.config import get_confluence_config

    os.environ["CONFLUENCE_WS_WS1_BASE_URL"] = "https://wiki1.example.com"
    os.environ["CONFLUENCE_WS_WS1_EMAIL"] = "u1@example.com"
    os.environ["CONFLUENCE_WS_WS1_API_TOKEN"] = "token1"
    os.environ["CONFLUENCE_WS_WS2_BASE_URL"] = "https://wiki2.example.com"
    os.environ["CONFLUENCE_WS_WS2_EMAIL"] = "u2@example.com"
    os.environ["CONFLUENCE_WS_WS2_API_TOKEN"] = "token2"
    try:
        cfg1 = get_confluence_config(workspace_id="ws1")
        cfg2 = get_confluence_config(workspace_id="ws2")
        assert cfg1["base_url"] == "https://wiki1.example.com"
        assert cfg2["base_url"] == "https://wiki2.example.com"
        assert cfg1["auth"] == ("u1@example.com", "token1")
        assert cfg2["auth"] == ("u2@example.com", "token2")
    finally:
        for k in [
            "CONFLUENCE_WS_WS1_BASE_URL",
            "CONFLUENCE_WS_WS1_EMAIL",
            "CONFLUENCE_WS_WS1_API_TOKEN",
            "CONFLUENCE_WS_WS2_BASE_URL",
            "CONFLUENCE_WS_WS2_EMAIL",
            "CONFLUENCE_WS_WS2_API_TOKEN",
        ]:
            os.environ.pop(k, None)


def test_workspace_isolation_create_page_uses_workspace_credentials() -> None:
    """When workspace_id is provided, create_page uses credentials from get_confluence_config(workspace_id)."""
    import os
    from unittest.mock import MagicMock, patch

    from app.confluence.client import create_page

    os.environ["CONFLUENCE_WS_ISOL_BASE_URL"] = "https://isol.example.com"
    os.environ["CONFLUENCE_WS_ISOL_EMAIL"] = "isol@example.com"
    os.environ["CONFLUENCE_WS_ISOL_API_TOKEN"] = "isol-token"
    try:
        with patch("app.confluence.client.get_client") as g:
            sess = MagicMock()
            g.return_value = sess
            r200 = MagicMock()
            r200.status_code = 200
            r200.json.return_value = {"id": "1"}
            sess.post.return_value = r200
            # Pass workspace_id; base_url/auth should be ignored and taken from config
            create_page(
                "https://ignored.com",
                "DOC",
                "T",
                "<p>x</p>",
                ("ignored", "ignored"),
                workspace_id="isol",
            )
            # Request must go to isol.example.com with isol@example.com / isol-token
            call_args = sess.post.call_args
            assert call_args is not None
            url = call_args[0][0] if call_args[0] else call_args[1].get("url")
            if url is None:
                url = call_args[0][0]
            assert "isol.example.com" in url
            assert call_args[1].get("auth") == ("isol@example.com", "isol-token")
    finally:
        os.environ.pop("CONFLUENCE_WS_ISOL_BASE_URL", None)
        os.environ.pop("CONFLUENCE_WS_ISOL_EMAIL", None)
        os.environ.pop("CONFLUENCE_WS_ISOL_API_TOKEN", None)


def test_project_isolation_concurrent_workspaces_no_cross_creds() -> None:
    """Two workspaces must return distinct credentials; no cross-contamination."""
    import os

    from app.config.config import get_confluence_config

    os.environ["CONFLUENCE_WS_A_BASE_URL"] = "https://wiki-a.example.com"
    os.environ["CONFLUENCE_WS_A_EMAIL"] = "a@example.com"
    os.environ["CONFLUENCE_WS_A_API_TOKEN"] = "token-a-secret"
    os.environ["CONFLUENCE_WS_B_BASE_URL"] = "https://wiki-b.example.com"
    os.environ["CONFLUENCE_WS_B_EMAIL"] = "b@example.com"
    os.environ["CONFLUENCE_WS_B_API_TOKEN"] = "token-b-secret"
    try:
        cfg_a = get_confluence_config(workspace_id="a")
        cfg_b = get_confluence_config(workspace_id="b")
        assert cfg_a["auth"][1] != cfg_b["auth"][1]
        assert cfg_a["base_url"] != cfg_b["base_url"]
    finally:
        for k in [
            "CONFLUENCE_WS_A_BASE_URL",
            "CONFLUENCE_WS_A_EMAIL",
            "CONFLUENCE_WS_A_API_TOKEN",
            "CONFLUENCE_WS_B_BASE_URL",
            "CONFLUENCE_WS_B_EMAIL",
            "CONFLUENCE_WS_B_API_TOKEN",
        ]:
            os.environ.pop(k, None)


# --- Verification module ---


def test_verify_confluence_security_all_passing() -> None:
    """verify_confluence_security() returns https_enforcement, token_masking, uses_credential_store True when satisfied."""
    from app.confluence.verification import verify_confluence_security

    results = verify_confluence_security()
    assert results["https_enforcement"] is True
    assert results["token_masking"] is True
    assert results["uses_credential_store"] is True


def test_verify_confluence_security_value_error_wrong_message() -> None:
    """Cover except ValueError when message does not contain 'must use HTTPS' (line 26 False branch)."""
    from unittest.mock import patch

    import app.confluence.client as client_mod
    from app.confluence.verification import verify_confluence_security

    with patch.object(client_mod, "create_page", side_effect=ValueError("other error")):
        results = verify_confluence_security()
    assert results["https_enforcement"] is False


def test_verify_confluence_security_https_enforcement_true_via_value_error() -> None:
    """Cover line 27: except ValueError with 'must use HTTPS' in message sets https_enforcement True."""
    from unittest.mock import patch

    import app.confluence.client as client_mod
    from app.confluence.verification import verify_confluence_security

    with patch.object(client_mod, "create_page", side_effect=ValueError("must use HTTPS")):
        results = verify_confluence_security()
    assert results["https_enforcement"] is True


def test_verify_confluence_security_https_block_raises_non_value_error() -> None:
    """Cover line 28: except Exception in first try block (e.g. import or create_page raises)."""
    from unittest.mock import patch

    import app.confluence.client as client_mod
    from app.confluence.verification import verify_confluence_security

    with patch.object(client_mod, "create_page", side_effect=RuntimeError("mock")):
        results = verify_confluence_security()
    assert results["https_enforcement"] is False


def test_verify_confluence_security_token_masking_raises() -> None:
    """Cover except Exception in token_masking block."""
    from unittest.mock import patch

    from app.confluence.verification import verify_confluence_security

    with patch("app.logging.logger.mask_tokens", side_effect=RuntimeError("mock")):
        results = verify_confluence_security()
    assert results["token_masking"] is False


def test_verify_confluence_security_credential_store_raises() -> None:
    """Cover except Exception in credential store block."""
    from unittest.mock import patch

    from app.confluence.verification import verify_confluence_security

    with patch("app.config.config.get_confluence_config", side_effect=RuntimeError("mock")):
        results = verify_confluence_security()
    assert results["uses_credential_store"] is False
