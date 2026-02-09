"""Tests for app.config.config: load_config, get_app_config, get_database_config, get_confluence_config."""
import pytest


def _import_config():
    from app.config.config import (
        load_config,
        get_app_config,
        get_database_config,
        get_confluence_config,
    )
    return load_config, get_app_config, get_database_config, get_confluence_config


def test_load_config_sets_global_and_app_config():
    load_config, get_app_config, _, _ = _import_config()
    load_config()
    cfg = get_app_config()
    assert isinstance(cfg, dict)


def test_get_app_config_returns_dict():
    _, get_app_config, _, _ = _import_config()
    assert isinstance(get_app_config(), dict)


def test_get_database_config_defaults(monkeypatch):
    _, _, get_database_config, _ = _import_config()
    monkeypatch.delenv("CONFLUENCE_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DB_POOL_MIN_SIZE", raising=False)
    monkeypatch.delenv("DB_POOL_MAX_SIZE", raising=False)
    monkeypatch.delenv("DB_POOL_TIMEOUT_SEC", raising=False)
    out = get_database_config()
    assert "database_url" in out
    assert "pool_min_size" in out and out["pool_min_size"] >= 1
    assert "pool_max_size" in out and out["pool_max_size"] >= 1
    assert "pool_timeout_sec" in out and out["pool_timeout_sec"] >= 5


def test_get_confluence_config_uses_env(monkeypatch):
    _, _, _, get_confluence_config = _import_config()
    monkeypatch.setenv("CONFLUENCE_TEAM_SHARING_OPT_IN", "false")
    out = get_confluence_config()
    assert "team_sharing_opt_in" in out
    assert "database_url" in out


def test_merge_confluence_settings_retry_invalid(monkeypatch):
    """Covers config.py lines 58-59: except ValueError in retry_attempts."""
    from app.config.config import _merge_confluence_settings_from_env
    out = {}
    monkeypatch.setenv("CONFLUENCE_RETRY_ATTEMPTS", "not_a_number")
    _merge_confluence_settings_from_env(out)
    assert "retry_attempts" not in out
