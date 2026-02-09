"""Tests for Confluence settings integration: config_routes, config, confluence_config, confluence_schema (100% coverage)."""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

try:
    from app.api.config_routes import (
        _mask_token,
        test_connection_handler as config_test_connection_handler,
        spaces_handler,
        validate_handler,
        defaults_handler,
        preferred_space_handler,
        register_config_routes,
    )
    from app.config.config import (
        _merge_confluence_settings_from_env,
        _validate_confluence_url,
        get_confluence_config,
    )
    from app.config.confluence_config import (
        detect_edition,
        get_intelligent_defaults,
        test_connection as confluence_test_connection,
        get_available_spaces,
        get_default_space_for_project_type,
        get_preferred_space,
        _confluence_request,
    )
    from app.config.confluence_schema import (
        ConfluenceCredentials,
        ConfluenceConfigValidate,
        _no_path_traversal,
        get_rate_limit_for_edition,
        get_intelligent_defaults_model,
        PerformanceTimeouts,
        PerformanceCache,
        LoggingConfig,
        LearningConfig,
        AdvancedConfig,
        TemplatesOverrides,
        IntelligenceConfig,
        RisksConfig,
        SpaceMappingDefault,
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "offline-folder-rag" / "edge_agent"))
    from app.api.config_routes import (
        _mask_token,
        test_connection_handler as config_test_connection_handler,
        spaces_handler,
        validate_handler,
        defaults_handler,
        preferred_space_handler,
        register_config_routes,
    )
    from app.config.config import (
        _merge_confluence_settings_from_env,
        _validate_confluence_url,
        get_confluence_config,
    )
    from app.config.confluence_config import (
        detect_edition,
        get_intelligent_defaults,
        test_connection as confluence_test_connection,
        get_available_spaces,
        get_default_space_for_project_type,
        get_preferred_space,
        _confluence_request,
    )
    from app.config.confluence_schema import (
        ConfluenceCredentials,
        ConfluenceConfigValidate,
        _no_path_traversal,
        get_rate_limit_for_edition,
        get_intelligent_defaults_model,
        PerformanceTimeouts,
        PerformanceCache,
        LoggingConfig,
        LearningConfig,
        AdvancedConfig,
        TemplatesOverrides,
        IntelligenceConfig,
        RisksConfig,
        SpaceMappingDefault,
    )


# ---- config_routes ----
def test_mask_token_empty():
    assert _mask_token("") == ""


def test_mask_token_replaces_api_token():
    assert "api_token=***" in _mask_token("api_token=secret")


def test_test_connection_handler_no_body():
    out = config_test_connection_handler(None)
    assert out["ok"] is False
    assert "latency_ms" in out


def test_test_connection_handler_body_not_dict():
    out = config_test_connection_handler([])
    assert out["ok"] is False


def test_test_connection_handler_validation_fails():
    out = config_test_connection_handler({"url": "not-a-url", "email": "x", "api_token": "t"})
    assert out["ok"] is False
    assert "error" in out


@patch("app.api.config_routes.test_connection")
def test_test_connection_handler_success(mock_tc):
    mock_tc.return_value = {"ok": True, "latency_ms": 100, "spaces": [{"key": "DOC", "name": "Docs"}]}
    out = config_test_connection_handler({
        "url": "https://example.atlassian.net",
        "email": "u@example.com",
        "api_token": "tok",
    })
    assert out["ok"] is True
    assert out["latency_ms"] == 100
    assert out["spaces"] == [{"key": "DOC", "name": "Docs"}]


def test_spaces_handler_no_body():
    out = spaces_handler(None)
    assert out["spaces"] == []
    assert "error" in out


def test_spaces_handler_body_not_dict():
    out = spaces_handler("x")
    assert out["spaces"] == []


def test_spaces_handler_validation_fails():
    out = spaces_handler({"url": "", "email": "a@b.com", "api_token": "t"})
    assert out["spaces"] == []
    assert "error" in out


@patch("app.api.config_routes.get_available_spaces")
def test_spaces_handler_success(mock_spaces):
    mock_spaces.return_value = [{"key": "DEV"}]
    out = spaces_handler({
        "url": "https://x.atlassian.net",
        "email": "u@x.com",
        "api_token": "t",
    })
    assert out["spaces"] == [{"key": "DEV"}]


def test_validate_handler_none_body():
    out = validate_handler(None)
    assert out["valid"] is True


def test_validate_handler_body_not_dict():
    out = validate_handler("not a dict")
    assert out["valid"] is False
    assert "errors" in out


def test_validate_handler_validation_fails_with_errors():
    out = validate_handler({"credentials": {"url": "http://bad.atlassian.net", "email": "a@b.com", "api_token": "t"}})
    assert out["valid"] is False
    assert "errors" in out and len(out["errors"]) >= 0


def test_validate_handler_validation_fails_generic_exception():
    with patch("app.api.config_routes.ConfluenceConfigValidate") as m:
        m.model_validate.side_effect = RuntimeError("api_token leaked")
        out = validate_handler({})
    assert out["valid"] is False
    assert "errors" in out
    assert "api_token (masked)" in out["errors"][0]


def test_validate_handler_success():
    out = validate_handler({})
    assert out["valid"] is True


def test_defaults_handler_no_url():
    out = defaults_handler(None)
    assert "edition" in out
    assert out["edition"] == "cloud"


def test_defaults_handler_with_url():
    out = defaults_handler("https://custom.confluence.com")
    assert out["edition"] == "server"


def test_register_config_routes_fastapi():
    router = MagicMock()
    router.post = MagicMock()
    router.get = MagicMock()
    register_config_routes(router)
    assert router.post.call_count >= 3
    assert router.get.called


def test_register_config_routes_no_fastapi():
    router = MagicMock()
    router.post = MagicMock()
    router.get = MagicMock()
    class FakeFastAPI:
        pass
    fake_fastapi = FakeFastAPI()  # no Body/Query so "from fastapi import Body" raises AttributeError
    with patch.dict("sys.modules", {"fastapi": fake_fastapi}):
        import importlib
        import app.api.config_routes as cr
        importlib.reload(cr)
        cr.register_config_routes(router)
    assert router.post.called
    assert router.get.called


def test_config_routes_via_fastapi_test_client():
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from fastapi import APIRouter
    app = FastAPI()
    router = APIRouter()
    register_config_routes(router)
    app.include_router(router)
    client = TestClient(app)
    r = client.post("/confluence/config/test-connection", json={})
    assert r.status_code == 200
    data = r.json()
    assert "ok" in data and data["ok"] is False
    r2 = client.post("/confluence/config/validate", json={})
    assert r2.status_code == 200
    assert r2.json()["valid"] is True
    r3 = client.get("/confluence/config/defaults")
    assert r3.status_code == 200
    assert "edition" in r3.json()
    r4 = client.post("/confluence/config/spaces", json={})
    assert r4.status_code == 200
    assert "spaces" in r4.json()
    r5 = client.get("/confluence/config/preferred-space?project_path=/my/project")
    assert r5.status_code == 200
    assert "preferred_space" in r5.json()


def test_config_routes_request_style_handlers_invoked():
    class NoPostGet:
        pass
    router = NoPostGet()
    register_config_routes(router)
    out = router.config_handlers["test_connection"](None)
    assert out["ok"] is False
    out2 = router.config_handlers["validate"]({})
    assert out2["valid"] is True
    out3 = router.config_handlers["defaults"](None)
    assert "edition" in out3
    out4 = router.config_handlers["spaces"](None)
    assert out4["spaces"] == []


def test_config_routes_request_style_via_test_client():
    import types
    from fastapi import FastAPI, APIRouter
    from fastapi.testclient import TestClient
    fake_fastapi = types.ModuleType("fastapi")
    fake_fastapi.Body = None
    fake_fastapi.Query = None
    with patch.dict("sys.modules", {"fastapi": fake_fastapi}):
        router = APIRouter()
        register_config_routes(router)
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        r = client.post("/confluence/config/test-connection", json={})
        assert r.status_code == 200
        assert r.json().get("ok") is False
        r2 = client.get("/confluence/config/defaults")
        assert r2.status_code == 200
        r3 = client.post("/confluence/config/validate", json={})
        assert r3.json().get("valid") is True
        r4 = client.post("/confluence/config/spaces", json={})
        assert "spaces" in r4.json()
        r5 = client.get("/confluence/config/preferred-space?project_path=/foo/bar")
        assert r5.status_code == 200
        assert "preferred_space" in r5.json()


def test_config_routes_request_style_defaults_with_query_params():
    """Covers config_routes line 134: defaults_route with request.query_params.get('url')."""
    import types
    from fastapi import APIRouter as RealAPIRouter
    fake_fastapi = types.ModuleType("fastapi")
    fake_fastapi.Body = None
    fake_fastapi.Query = None
    fake_fastapi.APIRouter = RealAPIRouter
    with patch.dict("sys.modules", {"fastapi": fake_fastapi}):
        import importlib
        import app.api.config_routes as cr
        importlib.reload(cr)
        router = RealAPIRouter()
        cr.register_config_routes(router)
        for r in router.routes:
            if getattr(r, "path", "") == "/confluence/config/defaults" and "GET" in getattr(r, "methods", set()):
                req = MagicMock()
                req.query_params = {"url": "https://x.atlassian.net"}
                out = r.endpoint(req)
                assert "edition" in out
                break
        else:
            pytest.fail("GET /confluence/config/defaults route not found")
        for r in router.routes:
            if getattr(r, "path", "") == "/confluence/config/preferred-space" and "GET" in getattr(r, "methods", set()):
                req = MagicMock()
                req.query_params = MagicMock()
                req.query_params.get = lambda k: "/my/proj" if k == "project_path" else None
                out = r.endpoint(req)
                assert "preferred_space" in out
                break
        else:
            pytest.fail("GET /confluence/config/preferred-space route not found")


def test_register_config_routes_handlers_dict():
    class NoPostGet:
        pass
    router = NoPostGet()
    register_config_routes(router)
    assert hasattr(router, "config_handlers")
    assert "test_connection" in router.config_handlers
    assert "spaces" in router.config_handlers
    assert "validate" in router.config_handlers
    assert "defaults" in router.config_handlers
    assert "preferred_space" in router.config_handlers
    out = router.config_handlers["preferred_space"]("/my/project")
    assert "preferred_space" in out
    assert out["preferred_space"] in ("DEV", "DOCS")


def test_preferred_space_handler_none():
    out = preferred_space_handler(None)
    assert out["preferred_space"] in ("DEV", "DOCS")


@patch("app.api.config_routes.get_preferred_space")
def test_preferred_space_handler_with_path(mock_get):
    mock_get.return_value = "DEV"
    out = preferred_space_handler("/some/project")
    assert out["preferred_space"] == "DEV"
    mock_get.assert_called_once_with("/some/project")


def test_get_default_space_for_project_type_code():
    assert get_default_space_for_project_type("/home/src/app") == "DEV"
    assert get_default_space_for_project_type("/api/service") == "DEV"


def test_get_default_space_for_project_type_docs():
    assert get_default_space_for_project_type("/home/docs") == "DOCS"
    assert get_default_space_for_project_type("/wiki/page") == "DOCS"


def test_get_default_space_for_project_type_default():
    assert get_default_space_for_project_type("") == "DEV"
    assert get_default_space_for_project_type("/other") == "DEV"


@patch("app.confluence.db_adapter.db_get_preferred_space")
def test_get_preferred_space_stored(mock_db):
    mock_db.return_value = "DEV"
    assert get_preferred_space("/my/project") == "DEV"
    mock_db.assert_called_once_with("/my/project")


@patch("app.confluence.db_adapter.db_get_preferred_space")
def test_get_preferred_space_fallback(mock_db):
    mock_db.return_value = None
    out = get_preferred_space("/docs/readme")
    assert out == "DOCS"


def test_get_preferred_space_empty():
    out = get_preferred_space(None)
    assert out in ("DEV", "DOCS")
    out2 = get_preferred_space("   ")
    assert out2 in ("DEV", "DOCS")


# ---- config.py ----
def test_merge_confluence_settings_rate_limit(monkeypatch):
    out = {}
    monkeypatch.setenv("CONFLUENCE_RATE_LIMIT", "50")
    _merge_confluence_settings_from_env(out)
    assert out["rate_limit"] == 50


def test_merge_confluence_settings_rate_limit_invalid(monkeypatch):
    out = {}
    monkeypatch.setenv("CONFLUENCE_RATE_LIMIT", "x")
    _merge_confluence_settings_from_env(out)
    assert "rate_limit" not in out


def test_merge_confluence_settings_burst_limit(monkeypatch):
    out = {}
    monkeypatch.setenv("CONFLUENCE_BURST_LIMIT", "20")
    _merge_confluence_settings_from_env(out)
    assert out["burst_limit"] == 20


def test_merge_confluence_settings_burst_invalid(monkeypatch):
    out = {}
    monkeypatch.setenv("CONFLUENCE_BURST_LIMIT", "y")
    _merge_confluence_settings_from_env(out)
    assert "burst_limit" not in out


def test_merge_confluence_settings_retry_attempts(monkeypatch):
    out = {}
    monkeypatch.setenv("CONFLUENCE_RETRY_ATTEMPTS", "5")
    _merge_confluence_settings_from_env(out)
    assert out["retry_attempts"] == 5


def test_merge_confluence_settings_learning_disabled(monkeypatch):
    out = {}
    monkeypatch.setenv("CONFLUENCE_LEARNING_ENABLED", "no")
    _merge_confluence_settings_from_env(out)
    assert out["learning_enabled"] is False


def test_merge_confluence_settings_learning_enabled(monkeypatch):
    out = {}
    monkeypatch.setenv("CONFLUENCE_LEARNING_ENABLED", "true")
    _merge_confluence_settings_from_env(out)
    assert out["learning_enabled"] is True


def test_get_confluence_config_merge_learning_disabled(monkeypatch):
    monkeypatch.setenv("CONFLUENCE_LEARNING_ENABLED", "no")
    out = get_confluence_config()
    assert out.get("learning_enabled") is False


def test_get_confluence_config_merge_learning_enabled(monkeypatch):
    monkeypatch.setenv("CONFLUENCE_LEARNING_ENABLED", "yes")
    out = get_confluence_config()
    assert out.get("learning_enabled") is True


def test_validate_confluence_url_none():
    assert _validate_confluence_url(None) is True


def test_validate_confluence_url_empty():
    assert _validate_confluence_url("") is True


def test_validate_confluence_url_not_string():
    assert _validate_confluence_url(123) is True


def test_validate_confluence_url_atlassian_http():
    assert _validate_confluence_url("http://x.atlassian.net") is False


def test_validate_confluence_url_atlassian_https():
    assert _validate_confluence_url("https://x.atlassian.net") is True


def test_validate_confluence_url_http():
    assert _validate_confluence_url("http://confluence.local") is True


@patch("app.auth.credential_store.get_workspace_credentials")
def test_get_confluence_config_workspace_url_warning(mock_creds):
    mock_creds.return_value = {
        "base_url": "http://bad.atlassian.net",
        "email": "u@x.com",
        "api_token": "t",
        "is_encrypted": True,
    }
    out = get_confluence_config(workspace_id="ws1")
    assert "_url_validation_warning" in out
    assert "HTTPS" in out["_url_validation_warning"]


# ---- confluence_config.py ----
def test_detect_edition_empty():
    assert detect_edition("") == "server"


def test_detect_edition_none():
    assert detect_edition(None) == "server"


def test_detect_edition_not_string():
    assert detect_edition(123) == "server"


def test_detect_edition_cloud():
    assert detect_edition("https://x.atlassian.net") == "cloud"


def test_detect_edition_server():
    assert detect_edition("https://confluence.mycompany.com") == "server"


def test_get_intelligent_defaults_none():
    out = get_intelligent_defaults(None)
    assert "edition" in out


def test_get_intelligent_defaults_with_url():
    out = get_intelligent_defaults("https://c.example.com")
    assert out["edition"] == "server"


def test_confluence_request_no_requests():
    import builtins
    real_import = builtins.__import__
    def fake_import(name, *args, **kwargs):
        if name == "requests":
            raise ImportError("No module named 'requests'")
        return real_import(name, *args, **kwargs)
    with patch.object(builtins, "__import__", side_effect=fake_import):
        data, elapsed = _confluence_request("https://x.com", "/api", ("u", "t"))
    assert data is None
    assert elapsed == 0.0


def test_confluence_request_200_json():
    mock_requests = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"user": "me"}
    mock_requests.request.return_value = mock_resp
    with patch.dict("sys.modules", {"requests": mock_requests}):
        data, elapsed = _confluence_request("https://x.com", "/api", ("u", "t"))
    assert data == {"user": "me"}
    assert elapsed >= 0


def test_confluence_request_200_bad_json():
    mock_requests = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.side_effect = ValueError()
    mock_requests.request.return_value = mock_resp
    with patch.dict("sys.modules", {"requests": mock_requests}):
        data, elapsed = _confluence_request("https://x.com", "/api", ("u", "t"))
    assert data is None


def test_confluence_request_non_200():
    mock_requests = MagicMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_requests.request.return_value = mock_resp
    with patch.dict("sys.modules", {"requests": mock_requests}):
        data, _ = _confluence_request("https://x.com", "/api", ("u", "t"))
    assert data is None


def test_confluence_request_exception():
    mock_requests = MagicMock()
    mock_requests.request.side_effect = OSError()
    with patch.dict("sys.modules", {"requests": mock_requests}):
        data, elapsed = _confluence_request("https://x.com", "/api", ("u", "t"))
    assert data is None
    assert elapsed >= 0


@patch("app.config.confluence_config._confluence_request")
def test_test_connection_success_with_spaces(mock_req):
    mock_req.side_effect = [
        ({"type": "user"}, 0.1),
        ({"results": [{"key": "DOC", "name": "Documentation"}]}, 0.05),
    ]
    out = confluence_test_connection("https://x.atlassian.net", "u@x.com", "tok")
    assert out["ok"] is True
    assert out["spaces"] == [{"key": "DOC", "name": "Documentation"}]
    assert out["latency_ms"] == 100


@patch("app.config.confluence_config._confluence_request")
def test_test_connection_success_no_spaces(mock_req):
    mock_req.side_effect = [({"type": "user"}, 0.1), (None, 0.0)]
    out = confluence_test_connection("https://x.atlassian.net", "u@x.com", "tok")
    assert out["ok"] is True
    assert out["spaces"] == []


@patch("app.config.confluence_config._confluence_request")
def test_test_connection_failure(mock_req):
    mock_req.return_value = (None, 0.2)
    out = confluence_test_connection("https://x.atlassian.net", "u@x.com", "tok")
    assert out["ok"] is False
    assert "error" in out


@patch("app.config.confluence_config._confluence_request")
def test_get_available_spaces_success(mock_req):
    mock_req.return_value = ({"results": [{"key": "DEV", "name": "Development"}]}, 0.1)
    out = get_available_spaces("https://x.atlassian.net", "u@x.com", "tok")
    assert out == [{"key": "DEV", "name": "Development"}]


@patch("app.config.confluence_config._confluence_request")
def test_get_available_spaces_no_data(mock_req):
    mock_req.return_value = (None, 0.0)
    out = get_available_spaces("https://x.atlassian.net", "u@x.com", "tok")
    assert out == []


@patch("app.config.confluence_config._confluence_request")
def test_get_available_spaces_no_results_key(mock_req):
    mock_req.return_value = ({"other": []}, 0.0)
    out = get_available_spaces("https://x.atlassian.net", "u@x.com", "tok")
    assert out == []


# ---- confluence_schema.py ----
def test_no_path_traversal_empty():
    assert _no_path_traversal("") == ""


def test_no_path_traversal_none():
    assert _no_path_traversal(None) == ""


def test_no_path_traversal_traversal():
    with pytest.raises(ValueError, match="traversal"):
        _no_path_traversal("/foo/../bar")


def test_no_path_traversal_too_long():
    with pytest.raises(ValueError, match="at most"):
        _no_path_traversal("x" * 3000)


def test_no_path_traversal_valid():
    assert _no_path_traversal("  /valid/path  ") == "/valid/path"


def test_credentials_url_cloud_http():
    with pytest.raises(ValueError, match="HTTPS"):
        ConfluenceCredentials(url="http://x.atlassian.net", email="u@x.com", api_token="t")


def test_credentials_url_no_scheme():
    with pytest.raises(ValueError, match="http"):
        ConfluenceCredentials(url="x.atlassian.net", email="u@x.com", api_token="t")


def test_credentials_email_empty():
    with pytest.raises((ValueError, Exception), match="required|at least 1"):
        ConfluenceCredentials(url="https://x.com", email="", api_token="t")


def test_credentials_email_empty_whitespace():
    """Covers confluence_schema line 54-55: empty/whitespace email raise."""
    with pytest.raises(ValueError, match="Email is required"):
        ConfluenceCredentials(url="https://x.com", email="   ", api_token="t")


def test_credentials_email_invalid():
    with pytest.raises(ValueError, match="Invalid"):
        ConfluenceCredentials(url="https://x.com", email="no-at", api_token="t")


def test_credentials_email_no_dot_in_domain():
    with pytest.raises(ValueError, match="Invalid"):
        ConfluenceCredentials(url="https://x.com", email="u@nodot", api_token="t")


def test_credentials_email_domain_no_dot_second_branch():
    """Covers confluence_schema email validator: '@' in s but '.' not in s.split('@')[-1]."""
    with pytest.raises(ValueError, match="Invalid"):
        ConfluenceCredentials(url="https://x.com", email="a@b", api_token="t")


def test_credentials_email_has_at_no_dot_after():
    with pytest.raises(ValueError, match="Invalid"):
        ConfluenceCredentials(url="https://x.com", email="user@domainnodot", api_token="t")


def test_credentials_valid():
    c = ConfluenceCredentials(url="https://x.atlassian.net", email="u@x.com", api_token="t")
    assert c.url == "https://x.atlassian.net"
    assert c.email == "u@x.com"


def test_get_rate_limit_cloud():
    assert get_rate_limit_for_edition("cloud") == 30


def test_get_rate_limit_server():
    assert get_rate_limit_for_edition("server") == 20


def test_get_intelligent_defaults_model_none():
    out = get_intelligent_defaults_model(None)
    assert out["edition"] == "cloud"


def test_get_intelligent_defaults_model_cloud():
    out = get_intelligent_defaults_model("https://x.atlassian.net")
    assert out["edition"] == "cloud"


def test_get_intelligent_defaults_model_server():
    out = get_intelligent_defaults_model("https://confluence.local")
    assert out["edition"] == "server"
    assert out["performance"]["rateLimit"] == 20


def test_space_mapping_default():
    SpaceMappingDefault()


def test_performance_timeouts():
    p = PerformanceTimeouts()
    assert p.analysis == 3000
    assert p.connection == 5000


def test_performance_cache():
    p = PerformanceCache()
    assert p.enabled is True
    assert p.maxSize == 100


def test_logging_config():
    LoggingConfig(level="DEBUG")


def test_learning_config():
    LearningConfig(retentionDays=30)


def test_advanced_config_path_traversal():
    with pytest.raises(ValueError, match="traversal"):
        AdvancedConfig(exportPath="/foo/../bar")


def test_advanced_config_export_path_valid():
    a = AdvancedConfig(exportPath="/valid/path", importPath="")
    assert a.exportPath == "/valid/path"


def test_advanced_config_import_path_traversal():
    with pytest.raises(ValueError, match="traversal"):
        AdvancedConfig(importPath="..\\secret")


def test_templates_overrides_path_traversal():
    with pytest.raises(ValueError, match="traversal"):
        TemplatesOverrides(customTemplatesPath="/a/../b")


def test_templates_overrides_custom_path_valid():
    t = TemplatesOverrides(customTemplatesPath="/valid/templates")
    assert t.customTemplatesPath == "/valid/templates"


def test_templates_overrides_path_no_traversal_non_empty():
    """Covers confluence_schema path_no_traversal return branch (non-empty v)."""
    t = TemplatesOverrides(customTemplatesPath="/app/templates")
    assert t.customTemplatesPath == "/app/templates"


def test_templates_overrides_empty_path():
    """Covers confluence_schema line 132-133: path_no_traversal when v is empty."""
    t = TemplatesOverrides()
    assert t.customTemplatesPath == ""


def test_templates_overrides_empty_path_explicit():
    """Covers confluence_schema line 133: return v in path_no_traversal when v is empty."""
    t = TemplatesOverrides(customTemplatesPath="")
    assert t.customTemplatesPath == ""


def test_intelligence_config():
    IntelligenceConfig(confidenceThreshold=0.8)


def test_risks_config():
    RisksConfig(fallbackTemplates=["generic"])


def test_confluence_config_validate_valid():
    ConfluenceConfigValidate()


def test_confluence_config_validate_invalid_credentials():
    with pytest.raises(Exception):
        ConfluenceConfigValidate(credentials={"url": "http://bad.atlassian.net", "email": "x", "api_token": "t"})
