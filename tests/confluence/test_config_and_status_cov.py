"""Tests for config and status_manager coverage."""
from unittest.mock import MagicMock, patch

try:
    from app.config import config
    from app.confluence import status_manager
    from app.confluence import error_handler
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "offline-folder-rag" / "edge_agent"))
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
    out = status_manager.get_intelligence_status(detail_level="full", db_fetch_metrics=None)
    assert "intelligence_metrics" in out
    assert "learning_progress" in out


def test_status_manager_get_intelligence_status_with_db():
    mock_metrics = MagicMock(return_value={"examples_learned": 10, "template_selection_accuracy": 90})
    out = status_manager.get_intelligence_status(db_fetch_metrics=mock_metrics)
    assert out["intelligence_metrics"]["template_selection_intelligence"] == 90


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
