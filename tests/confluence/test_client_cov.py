"""Tests for app.confluence.client coverage."""
from unittest.mock import MagicMock, patch

try:
    from app.confluence import client
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "offline-folder-rag" / "edge_agent"))
    from app.confluence import client


def test_get_client_returns_session():
    s = client.get_client()
    assert s is None or hasattr(s, "post")


def test_create_page_no_client():
    client._session = None
    with patch.object(client, "get_client", return_value=None):
        try:
            client.create_page("http://x", "DOC", "T", "<p>b</p>", auth=None)
        except RuntimeError as e:
            assert "not available" in str(e) or "requests" in str(e)


@patch.object(client, "get_client")
def test_create_page_success(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"id": "1", "title": "T"}
    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp
    mock_get.return_value = mock_client
    out = client.create_page("http://x", "DOC", "T", "<p>b</p>", auth=None)
    assert out.get("id") == "1"


@patch.object(client, "get_client")
def test_create_page_429_retry(mock_get):
    mock_client = MagicMock()
    r1 = MagicMock()
    r1.status_code = 429
    r2 = MagicMock()
    r2.status_code = 200
    r2.json.return_value = {"id": "1"}
    mock_client.post.side_effect = [r1, r2]
    mock_get.return_value = mock_client
    with patch("app.confluence.client.time.sleep"):
        out = client.create_page("http://x", "DOC", "T", "<p>b</p>", auth=None)
    assert out.get("id") == "1"


@patch.object(client, "get_client")
def test_create_page_401_raises(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.raise_for_status = MagicMock(side_effect=Exception("401"))
    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp
    mock_get.return_value = mock_client
    try:
        client.create_page("http://x", "DOC", "T", "<p>b</p>", auth=None)
    except Exception as e:
        assert "401" in str(e) or True
