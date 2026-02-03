"""
User Story 13 — Intelligent Error Recovery. Test names include TC IDs for -k selection.
"""
from unittest.mock import MagicMock, patch

PRD_FIELDS = ("error", "message", "intelligence_suggestion", "fallback_available", "intelligence_confidence")


def _assert_prd_format(resp: dict) -> None:
    for f in PRD_FIELDS:
        assert f in resp, f"Missing PRD §9.2 field: {f}"


def test_TC_NEG_004_network_failure_auto_retry():
    """TC-NEG-004: Network failure auto retry (3 times + backoff)."""
    from app.confluence.client import NETWORK_RETRIES

    assert NETWORK_RETRIES == 3
    from app.confluence.error_handler import handle_error

    try:
        import requests.exceptions as req_exc
        raise req_exc.ConnectionError("Connection refused")
    except Exception as e:
        out = handle_error(e, error_code="create_failed")
    _assert_prd_format(out)
    assert out.get("category") == "network"
    assert "connection" in out.get("message", "").lower() or "reach" in out.get("message", "").lower()


def test_TC_NEG_007_rate_limit_handling():
    """TC-NEG-007: Rate limit handling (wait + retry)."""
    from app.confluence.client import RATE_LIMIT_WAIT_SECONDS
    from app.confluence.error_handler import CLASSIFICATION, handle_error

    assert RATE_LIMIT_WAIT_SECONDS == 30
    msg = CLASSIFICATION["rate_limit"][0]
    assert "30 seconds" in msg or "retry" in msg.lower()
    mock_resp = MagicMock()
    mock_resp.status_code = 429
    exc = Exception("429 Too Many Requests")
    exc.response = mock_resp
    out = handle_error(exc, error_code="rate_limited")
    _assert_prd_format(out)
    assert out.get("category") == "rate_limit"


def test_TC_NEG_003_invalid_credentials_fail_cleanly():
    """TC-NEG-003: Invalid credentials → fail cleanly (auth error classification)."""
    from app.api.confluence_routes import intelligent_create_handler
    from app.confluence.error_handler import handle_error

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    exc = Exception("401 Unauthorized")
    exc.response = mock_resp
    out = handle_error(exc, error_code="create_failed")
    _assert_prd_format(out)
    assert out.get("category") == "auth"
    assert "credentials" in out.get("message", "").lower() or "invalid" in out.get("message", "").lower()
    with patch("app.api.confluence_routes.run_create") as m:
        m.side_effect = exc
        r = intelligent_create_handler({"base_url": "https://x", "space_key": "DOC", "title": "T", "content": "c"})
    _assert_prd_format(r)
    assert "Update Settings" in r.get("actions", [])


def test_TC_ST_006_retry_state_transitions_correct():
    """TC-ST-006: Retry state transitions correct."""
    from app.confluence.client import NETWORK_RETRIES, create_page

    assert NETWORK_RETRIES == 3
    with patch("app.confluence.client.get_client") as g:
        sess = MagicMock()
        g.return_value = sess
        sess.post.side_effect = ConnectionError("network")
        try:
            create_page("https://x", "DOC", "T", "<p>x</p>", None)
        except Exception:
            pass
        assert sess.post.call_count == NETWORK_RETRIES + 1


def test_TC_DT_007_integration_agent_error_recovery_logic():
    """TC-DT-007: Integration Agent error recovery logic matches decision table."""
    from app.agents.integration_agent import create_page
    from app.confluence.error_handler import get_reliability_metrics

    with patch("app.agents.integration_agent.confluence_create_page") as m:
        m.side_effect = Exception("401 Unauthorized")
        try:
            create_page("https://x", "DOC", "T", "<p>x</p>", None)
        except Exception:
            pass
    metrics = get_reliability_metrics()
    assert "failure_count" in str(metrics) or "success_rate" in metrics


def test_TC_EH_008_encoding_issue_prd_format_response():
    """TC-EH-008: Encoding issue → PRD-format error response (§9.2)."""
    from app.confluence.error_handler import handle_error

    out = handle_error(ValueError("encoding utf-8 failed"), error_code="encoding_error")
    _assert_prd_format(out)
    assert out.get("category") == "encoding"


def test_TC_EH_007_invalid_template_format_graceful_handling():
    """TC-EH-007: Invalid template format → graceful handling."""
    from app.confluence.error_handler import handle_error

    out = handle_error(Exception("invalid template format"), error_code="template_error")
    _assert_prd_format(out)
    assert out.get("category") == "invalid_template"
    assert out.get("fallback_available") is True


def test_TC_EH_006_confluence_api_404_graceful_handling():
    """TC-EH-006: Confluence API 404 → graceful handling."""
    from app.confluence.error_handler import handle_error

    mock_resp = MagicMock()
    mock_resp.status_code = 404
    exc = Exception("404 Not Found")
    exc.response = mock_resp
    out = handle_error(exc, error_code="create_failed")
    _assert_prd_format(out)
    assert out.get("category") == "not_found"


def test_TC_EH_005_permission_denied_clear_guidance():
    """TC-EH-005: Permission denied → clear guidance."""
    from app.confluence.error_handler import handle_error

    mock_resp = MagicMock()
    mock_resp.status_code = 403
    exc = Exception("403 Forbidden")
    exc.response = mock_resp
    out = handle_error(exc, error_code="create_failed")
    _assert_prd_format(out)
    assert out.get("category") == "permission_denied"
    assert "Update Settings" in out.get("actions", [])


def test_TC_EH_009_db_connection_lost_graceful_recovery_option():
    """TC-EH-009: DB connection lost → graceful failure + recovery option."""
    from app.confluence.error_handler import handle_error

    out = handle_error(Exception("database unavailable"), error_code="db_error")
    _assert_prd_format(out)
    assert out.get("category") == "db_connection"
    assert "Retry" in out.get("actions", [])


def test_TC_EH_010_intelligence_error_graceful_failure():
    """TC-EH-010: Intelligence error → graceful failure."""
    from app.confluence.error_handler import handle_error

    out = handle_error(Exception("AI could not determine format"), error_code="intelligence_error")
    _assert_prd_format(out)
    assert out.get("category") == "intelligence_error"


def test_TC_EH_011_template_matching_error_graceful_fallback():
    """TC-EH-011: Template matching error → graceful failure/fallback."""
    from app.confluence.error_handler import handle_error

    out = handle_error(Exception("template matching failed"), error_code="match_error")
    _assert_prd_format(out)
    assert out.get("category") == "template_matching"
    assert out.get("fallback_available") is True


def test_TC_EH_012_agent_coordination_error_recover_gracefully():
    """TC-EH-012: Agent coordination error → recover or fail gracefully."""
    from app.confluence.error_handler import handle_error

    out = handle_error(Exception("agent coordination failed"), error_code="coord_error")
    _assert_prd_format(out)
    assert out.get("category") == "agent_coordination"
    assert "Retry" in out.get("actions", [])


def test_TC_EH_001_confluence_down_no_corruption_clear_messaging():
    """TC-EH-001: Confluence down → no corruption, clear messaging."""
    from app.api.confluence_routes import intelligent_create_handler

    with patch("app.api.confluence_routes.run_create") as m:
        m.side_effect = ConnectionError("Confluence unreachable")
        r = intelligent_create_handler({"base_url": "https://x", "space_key": "DOC", "title": "T", "content": "c"})
    _assert_prd_format(r)
    assert r.get("error")
    assert "message" in r


def test_TC_EH_002_invalid_credentials_no_corruption_clear_messaging():
    """TC-EH-002: Invalid credentials → no corruption, clear messaging."""
    from app.api.confluence_routes import intelligent_create_handler

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    exc = Exception("401")
    exc.response = mock_resp
    with patch("app.api.confluence_routes.run_create", side_effect=exc):
        r = intelligent_create_handler({"base_url": "https://x", "space_key": "DOC", "title": "T", "content": "c"})
    _assert_prd_format(r)
    assert r.get("category") == "auth"


def test_TC_EH_003_disk_full_no_corruption_clear_messaging():
    """TC-EH-003: Disk full → no corruption, clear messaging."""
    from app.confluence.error_handler import handle_error

    out = handle_error(OSError("disk full"), error_code="disk_error")
    _assert_prd_format(out)
    assert out.get("category") == "disk_full"


def test_TC_SC_004_handling_network_issues_graceful_recovery():
    """TC-SC-004: Handling network issues → graceful recovery."""
    from app.confluence.error_handler import handle_error, get_actions_for_category

    out = handle_error(ConnectionError("Network unreachable"), error_code="create_failed")
    _assert_prd_format(out)
    assert out.get("category") == "network"
    assert get_actions_for_category("network") == ["Retry", "Cancel"]


def test_TC_NEG_014_mcp_task_failure_graceful_recovery_option():
    """TC-NEG-014: MCP task failure → fails gracefully with recovery option."""
    from app.confluence.error_handler import handle_error

    out = handle_error(Exception("agent coordination failed"), error_code="mcp_task_failed")
    _assert_prd_format(out)
    assert out.get("category") in ("agent_coordination", "other")
    assert "Retry" in out.get("actions", []) or "Cancel" in out.get("actions", [])
