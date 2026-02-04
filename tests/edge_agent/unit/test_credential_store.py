"""Unit tests for app.auth.credential_store (coverage for ValueError branches)."""
import os
from unittest.mock import patch

try:
    from app.auth.credential_store import get_workspace_credentials
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "offline-folder-rag" / "edge_agent"))
    from app.auth.credential_store import get_workspace_credentials


def test_get_workspace_credentials_unknown_service_raises():
    with patch.dict(os.environ, {}, clear=False):
        try:
            get_workspace_credentials(service="other")
        except ValueError as e:
            assert "Unknown service" in str(e) or "other" in str(e)
            return
    raise AssertionError("Expected ValueError for unknown service")


def test_get_workspace_credentials_missing_base_url_raises():
    with patch.dict(os.environ, {"CONFLUENCE_EMAIL": "a@b.com", "CONFLUENCE_API_TOKEN": "t"}, clear=False):
        orig_base = os.environ.pop("CONFLUENCE_BASE_URL", None)
        try:
            get_workspace_credentials(service="confluence")
        except ValueError as e:
            assert "base_url" in str(e).lower()
            return
        finally:
            if orig_base is not None:
                os.environ["CONFLUENCE_BASE_URL"] = orig_base
    raise AssertionError("Expected ValueError for missing base_url")


def test_get_workspace_credentials_missing_email_raises():
    with patch.dict(os.environ, {"CONFLUENCE_BASE_URL": "https://wiki.example.com", "CONFLUENCE_API_TOKEN": "t"}, clear=False):
        orig_email = os.environ.pop("CONFLUENCE_EMAIL", None)
        try:
            get_workspace_credentials(service="confluence")
        except ValueError as e:
            assert "email" in str(e).lower()
            return
        finally:
            if orig_email is not None:
                os.environ["CONFLUENCE_EMAIL"] = orig_email
    raise AssertionError("Expected ValueError for missing email")


def test_get_workspace_credentials_missing_api_token_raises():
    with patch.dict(os.environ, {"CONFLUENCE_BASE_URL": "https://wiki.example.com", "CONFLUENCE_EMAIL": "a@b.com"}, clear=False):
        orig_token = os.environ.pop("CONFLUENCE_API_TOKEN", None)
        try:
            get_workspace_credentials(service="confluence")
        except ValueError as e:
            assert "api_token" in str(e).lower()
            return
        finally:
            if orig_token is not None:
                os.environ["CONFLUENCE_API_TOKEN"] = orig_token
    raise AssertionError("Expected ValueError for missing api_token")
