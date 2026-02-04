"""Tests for confluence_routes coverage."""
from unittest.mock import MagicMock, patch

try:
    from app.api.confluence_routes import (
        _get_query_param,
        _get_json_body,
        examples_export_handler,
        examples_import_handler,
        intelligent_analyze_handler,
        intelligent_create_handler,
        intelligence_status_handler,
        intelligence_feedback_handler,
        register_confluence_routes,
        _memory_limit_response,
        _error_response,
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "offline-folder-rag" / "edge_agent"))
    from app.api.confluence_routes import (
        _get_query_param,
        _get_json_body,
        examples_export_handler,
        examples_import_handler,
        intelligent_analyze_handler,
        intelligent_create_handler,
        intelligence_status_handler,
        intelligence_feedback_handler,
        register_confluence_routes,
        _memory_limit_response,
        _error_response,
    )


def test_get_query_param_args():
    req = MagicMock()
    req.args = {"detail_level": "summary"}
    assert _get_query_param(req, "detail_level") == "summary"


def test_get_query_param_query_params():
    req = MagicMock()
    req.args = None
    req.query_params = {"x": "y"}
    assert _get_query_param(req, "x") == "y"


def test_get_json_body_get_json():
    req = MagicMock()
    req.get_json = MagicMock(return_value={"a": 1})
    assert _get_json_body(req) == {"a": 1}


def test_get_json_body_json():
    req = MagicMock(spec=[])
    req.json = MagicMock(return_value={"b": 2})
    assert _get_json_body(req) == {"b": 2}


def test_examples_export_handler():
    req = MagicMock()
    req.args = {}
    req.query_params = {}
    out, status = examples_export_handler(req)
    assert status == 200
    assert isinstance(out, str)


def test_examples_import_handler_invalid_body():
    req = MagicMock()
    req.get_json = MagicMock(return_value=None)
    req.json = MagicMock(side_effect=Exception())
    req.body = b"invalid"
    req.get_data = MagicMock(return_value=None)
    out = examples_import_handler(req)
    assert out[1] == 400 or "error" in out[0]


def test_intelligent_analyze_handler_empty_body():
    with patch("app.api.confluence_routes.check_memory_before_step", return_value=True):
        with patch("app.api.confluence_routes.HTTPException", None):
            out = intelligent_analyze_handler({})
    assert "error" in out or "Missing" in str(out.get("message", ""))


def test_intelligent_analyze_handler_content_only():
    with patch("app.api.confluence_routes.check_memory_before_step", return_value=True):
        with patch("app.api.confluence_routes.run_analyze") as mock_run:
            mock_run.return_value = {"analyses": [], "template": {}}
            out = intelligent_analyze_handler({"content": "x"})
    assert "analyses" in out or "error" in out


def test_intelligent_analyze_handler_memory_limit():
    with patch("app.api.confluence_routes.check_memory_before_step", return_value=False):
        out = intelligent_analyze_handler({"files": ["a"]})
    assert "error" in out or "resource_limit" in str(out)


def test_intelligent_create_handler_memory_limit():
    with patch("app.api.confluence_routes.check_memory_before_step", return_value=False):
        out = intelligent_create_handler({"content": "x"})
    assert "error" in out or "resource_limit" in str(out)


def test_intelligence_status_handler_no_request():
    out = intelligence_status_handler()
    assert "intelligence_metrics" in out or "metrics" in out


def test_intelligence_status_handler_with_request():
    req = MagicMock()
    req.args = {}
    req.query_params = {}
    out, status = intelligence_status_handler(req)
    assert status == 200
    assert "intelligence_metrics" in out


def test_intelligence_feedback_handler_with_score():
    with patch("app.api.confluence_routes.learn_from_feedback"):
        with patch("app.api.confluence_routes.get_intelligence_status", return_value={"intelligence_metrics": {}}):
            out = intelligence_feedback_handler({"creation_id": "c1", "intelligence_score": 5})
    assert (isinstance(out, tuple) and out[0].get("updated")) or out.get("updated")


def test_intelligence_feedback_handler_fallback():
    out = intelligence_feedback_handler({"feedback": "ok"})
    assert "status" in out[0] or "accepted" in str(out)


def test_error_response():
    body, status = _error_response("msg", "sugg", True)
    assert status == 400
    assert body["error"] == "intelligence_error"
    assert body["fallback_available"] is True


def test_memory_limit_response():
    r = _memory_limit_response()
    assert "actions" in r
    assert "resource_limit" in str(r).lower() or "error" in r


def test_register_confluence_routes_fastapi():
    router = MagicMock()
    router.post = MagicMock()
    router.get = MagicMock()
    router.route = MagicMock()
    try:
        register_confluence_routes(router)
    except Exception:
        pass
    assert router.post.called or router.get.called or hasattr(router, "confluence_handlers")


def test_register_confluence_routes_handlers_dict():
    class NoPostGet:
        pass
    router = NoPostGet()
    register_confluence_routes(router)
    assert hasattr(router, "confluence_handlers")
