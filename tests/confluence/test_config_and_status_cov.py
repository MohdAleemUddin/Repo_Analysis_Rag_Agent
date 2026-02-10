"""Tests for config and status_manager coverage."""

from unittest.mock import MagicMock, patch

try:
    from app.config import config
    from app.confluence import status_manager
    from app.confluence import error_handler
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(
        0,
        str(
            Path(__file__).resolve().parents[2]
            / "repo_analysis_rag"
            / "backend_confluence"
        ),
    )
    from app.config import config
    from app.confluence import status_manager
    from app.confluence import error_handler


def test_config_load_config():
    config.load_config()
    assert config.get_app_config() == {}


def test_config_get_database_config():
    with patch.dict("os.environ", {}, clear=False):
        d = config.get_database_config()
    assert "database_url" in d
    assert "pool_min_size" in d


def test_config_get_confluence_config_opt_out():
    with patch.dict("os.environ", {"CONFLUENCE_TEAM_SHARING_OPT_IN": "0"}, clear=False):
        c = config.get_confluence_config()
    assert c.get("team_sharing_opt_in") is False


def test_status_manager_get_intelligence_status_no_db():
    out = status_manager.get_intelligence_status(
        detail_level="full", db_fetch_metrics=None
    )
    assert "intelligence_metrics" in out
    assert "learning_progress" in out


def test_status_manager_get_intelligence_status_with_db():
    mock_metrics = MagicMock(
        return_value={"examples_learned": 10, "template_selection_accuracy": 90}
    )
    out = status_manager.get_intelligence_status(db_fetch_metrics=mock_metrics)
    assert out["intelligence_metrics"]["template_selection_intelligence"] == 90


def test_status_manager_db_fetch_metrics_raises():
    failing = MagicMock(side_effect=RuntimeError("db fail"))
    out = status_manager.get_intelligence_status(db_fetch_metrics=failing)
    assert "intelligence_metrics" in out


def test_status_manager_get_intelligence_status_summary():
    out = status_manager.get_intelligence_status(detail_level="summary")
    assert "improvement_rates" not in out


def test_status_manager_get_status():
    s = status_manager.get_status()
    assert isinstance(s, str)


def test_error_handler_iter_leaf_exceptions():
    e = ValueError("x")
    leaves = list(error_handler._iter_leaf_exceptions(e))
    assert len(leaves) == 1 and leaves[0] is e


def test_error_handler_is_network_timeout():
    assert error_handler._is_network_error(TimeoutError()) is True


def test_error_handler_is_network_connection_refused():
    e = ConnectionRefusedError()
    assert error_handler._is_network_error(e) is True


def test_error_handler_classify_network():
    e = Exception("connection refused")
    assert error_handler._classify(e) == "network"


def test_error_handler_classify_auth():
    e = Exception("401 unauthorized")
    assert error_handler._classify(e) == "auth"


def test_error_handler_handle_error():
    out = error_handler.handle_error(ValueError("auth failed"), error_code="err")
    assert "error" in out
    assert "message" in out


def test_error_handler_prd_error_response():
    out = error_handler.prd_error_response("err", message="msg", category="auth")
    assert out["message"] == "msg"
    assert "actions" in out


def test_error_handler_get_actions_for_category():
    acts = error_handler.get_actions_for_category("auth")
    assert isinstance(acts, list)


def test_error_handler_reliability_metrics():
    error_handler.record_success()
    error_handler.record_failure(auto_recovered=True)
    m = error_handler.get_reliability_metrics()
    assert "success_rate" in m


def test_error_handler_iter_leaf_exception_group():
    try:
        raise ExceptionGroup("eg", [ValueError("a")])  # type: ignore
    except BaseException as e:
        leaves = list(error_handler._iter_leaf_exceptions(e))
    assert len(leaves) >= 1


def test_error_handler_is_network_gaierror():
    import socket

    assert error_handler._is_network_error(socket.gaierror(1, "err")) is True


def test_error_handler_is_network_oserror_errno():
    e = OSError()
    e.errno = 111
    assert error_handler._is_network_error(e) is True


def test_error_handler_classify_404():
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    exc = Exception("not found")
    exc.response = mock_resp
    assert error_handler._classify(exc) == "not_found"


def test_error_handler_classify_403():
    mock_resp = MagicMock()
    mock_resp.status_code = 403
    exc = Exception("forbidden")
    exc.response = mock_resp
    assert error_handler._classify(exc) == "permission_denied"


def test_error_handler_classify_disk():
    assert error_handler._classify(Exception("disk full")) == "disk_full"


def test_error_handler_classify_db_connection():
    assert error_handler._classify(Exception("connection lost")) == "db_connection"


def test_error_handler_classify_encoding():
    assert error_handler._classify(Exception("encoding error")) == "encoding"


def test_error_handler_classify_invalid_template():
    assert error_handler._classify(Exception("invalid template")) == "invalid_template"


def test_error_handler_classify_intelligence():
    assert (
        error_handler._classify(Exception("intelligence failed"))
        == "intelligence_error"
    )


def test_error_handler_classify_template_matching():
    assert (
        error_handler._classify(Exception("template match fail")) == "template_matching"
    )


def test_error_handler_classify_agent_coordination():
    assert (
        error_handler._classify(Exception("agent coordination")) == "agent_coordination"
    )


def test_error_handler_prd_error_response_with_message():
    out = error_handler.prd_error_response("e", message="custom", category="auth")
    assert out["message"] == "custom"


def test_error_handler_record_failure_user_intervention():
    error_handler.record_failure(auto_recovered=False, user_intervention=True)
    m = error_handler.get_reliability_metrics()
    assert "user_intervention_rate" in m
