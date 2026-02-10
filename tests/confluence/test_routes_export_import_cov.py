"""Tests for confluence_routes export/import handlers and request helpers."""

from unittest.mock import MagicMock, patch

try:
    from app.api.confluence_routes import (
        _get_query_param,
        _get_json_body,
        examples_export_handler,
        examples_import_handler,
    )
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
    from app.api.confluence_routes import (
        _get_query_param,
        _get_json_body,
        examples_export_handler,
        examples_import_handler,
    )


def test_get_query_param_args():
    req = MagicMock()
    req.args = {"detail_level": "full"}
    assert _get_query_param(req, "detail_level") == "full"


def test_get_query_param_query_params():
    req = MagicMock(spec=[])
    req.args = None
    req.query_params = {"project_path": "/proj"}
    assert _get_query_param(req, "project_path") == "/proj"


def test_get_json_body_get_json():
    req = MagicMock()
    req.get_json = MagicMock(return_value={"examples": []})
    assert _get_json_body(req) == {"examples": []}


def test_get_json_body_json_method():
    req = MagicMock()
    req.get_json = None
    req.json = MagicMock(return_value={"version": 1})
    assert _get_json_body(req) == {"version": 1}


def test_get_json_body_body_decode():
    req = MagicMock()
    req.get_json = None
    req.json = None
    mock_body = MagicMock()
    mock_body.decode.return_value = '{"x": 1}'
    req.body = mock_body
    assert _get_json_body(req) == {"x": 1}


def test_examples_export_handler():
    req = MagicMock()
    req.args = {}
    req.query_params = {}
    with patch(
        "app.api.confluence_routes.export_examples",
        return_value='{"version":1,"examples":[]}',
    ) as m:
        body, code = examples_export_handler(req)
    m.assert_called_once()
    assert code == 200
    assert "version" in body or "examples" in body


def test_examples_import_handler_valid():
    req = MagicMock()
    req.get_json = MagicMock(
        return_value={
            "version": 1,
            "exported_at": "2020-01-01T00:00:00",
            "examples": [
                {
                    "content_profile": {},
                    "template_ref": {"template_id": "t", "template_name": "T"},
                    "intelligence_metrics": {},
                }
            ],
        }
    )
    with patch(
        "app.api.confluence_routes.import_examples",
        return_value=(1, "Intelligence Examples Imported: 1 new examples learned"),
    ):
        out, code = examples_import_handler(req)
    assert code == 200
    assert out.get("imported_count") == 1


def test_examples_import_handler_no_body():
    req = MagicMock()
    req.get_json = None
    req.get_data = None
    req.body = None
    out, code = examples_import_handler(req)
    assert code == 400
    assert "error" in out


def test_examples_import_handler_validation_error():
    req = MagicMock()
    req.get_json = MagicMock(return_value={"invalid": "payload"})
    with patch(
        "app.api.confluence_routes.import_examples",
        return_value=(0, "Missing required field"),
    ):
        out, code = examples_import_handler(req)
    assert code == 400


def test_intelligence_status_handler_with_request():
    try:
        from app.api.confluence_routes import intelligence_status_handler
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
        from app.api.confluence_routes import intelligence_status_handler
    req = MagicMock()
    req.args = None
    req.query_params = {"detail_level": "full"}
    with patch(
        "app.api.confluence_routes.get_intelligence_status",
        return_value={
            "intelligence_metrics": {},
            "learning_progress": {},
            "intelligence_summary": {},
            "improvement_rates": {},
        },
    ):
        out = intelligence_status_handler(req)
    resp, code = out if isinstance(out, tuple) else (out, 200)
    assert code == 200
    assert "intelligence_metrics" in resp


def test_intelligence_feedback_handler_learn_path():
    try:
        from app.api.confluence_routes import intelligence_feedback_handler
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
        from app.api.confluence_routes import intelligence_feedback_handler
    with patch("app.api.confluence_routes.learn_from_feedback"), patch(
        "app.api.confluence_routes.get_intelligence_status",
        return_value={"intelligence_metrics": {}},
    ):
        out = intelligence_feedback_handler(
            {
                "creation_id": "00000000-0000-0000-0000-000000000001",
                "intelligence_score": 5,
            }
        )
    resp, code = out if isinstance(out, tuple) else (out, 200)
    assert code == 200
    assert resp.get("updated") is True


def test_register_confluence_routes_dict_style():
    try:
        from app.api.confluence_routes import register_confluence_routes
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
        from app.api.confluence_routes import register_confluence_routes

    class SimpleRouter:
        pass

    router = SimpleRouter()
    register_confluence_routes(router)
    assert hasattr(router, "confluence_handlers")
    assert "examples_export" in router.confluence_handlers
