"""Tests for app.confluence.client: HTTPS, token validation, get_client, create_page paths."""
from unittest.mock import MagicMock, patch

import pytest


def test_https_required_raises_for_http():
    from app.confluence.client import create_page

    with pytest.raises(ValueError, match="base_url must use HTTPS"):
        create_page("http://wiki.example.com", "DOC", "T", "<p>x</p>", None)


def test_https_required_raises_for_empty_after_strip():
    from app.confluence.client import create_page

    with pytest.raises(ValueError, match="base_url must use HTTPS"):
        create_page("  ftp://x  ", "DOC", "T", "<p>x</p>", None)


def test_validate_token_rejects_none():
    from app.confluence.client import _validate_token

    with pytest.raises(ValueError, match="non-empty string"):
        _validate_token(None)


def test_validate_token_rejects_non_string():
    from app.confluence.client import _validate_token

    with pytest.raises(ValueError, match="non-empty string"):
        _validate_token(123)


def test_validate_token_rejects_empty_string():
    from app.confluence.client import _validate_token

    with pytest.raises(ValueError, match="non-empty string"):
        _validate_token("")


def test_validate_token_rejects_whitespace_only():
    from app.confluence.client import _validate_token

    with pytest.raises(ValueError, match="non-empty string"):
        _validate_token("   \t  ")


def test_validate_token_accepts_non_empty():
    from app.confluence.client import _validate_token

    _validate_token("valid-token")


def test_create_page_validates_auth_token_empty_tuple():
    from app.confluence.client import create_page

    with patch("app.confluence.client.get_client") as g:
        g.return_value = MagicMock()
        with pytest.raises(ValueError, match="non-empty string"):
            create_page("https://x", "DOC", "T", "<p>x</p>", ("user",))


def test_create_page_validates_auth_token_single_element():
    from app.confluence.client import create_page

    with patch("app.confluence.client.get_client") as g:
        g.return_value = MagicMock()
        with pytest.raises(ValueError, match="non-empty string"):
            create_page("https://x", "DOC", "T", "<p>x</p>", ("only_user",))


def test_get_client_returns_session():
    from app.confluence.client import get_client

    c = get_client()
    assert c is not None


def test_create_page_raises_when_client_unavailable():
    from app.confluence.client import create_page

    with patch("app.confluence.client.get_client", return_value=None):
        with pytest.raises(RuntimeError, match="HTTP client not available"):
            create_page("https://x", "DOC", "T", "<p>x</p>", None)


def test_create_page_429_then_success():
    from app.confluence.client import create_page, RATE_LIMIT_WAIT_SECONDS

    with patch("app.confluence.client.get_client") as g:
        sess = MagicMock()
        g.return_value = sess
        r429 = MagicMock()
        r429.status_code = 429
        r200 = MagicMock()
        r200.status_code = 200
        r200.json.return_value = {"id": "1"}
        sess.post.side_effect = [r429, r200]
        with patch("time.sleep"):
            out = create_page("https://x", "DOC", "T", "<p>x</p>", None)
        assert out == {"id": "1"}
        assert sess.post.call_count >= 2


def test_create_page_401_raises():
    from app.confluence.client import create_page
    import requests

    with patch("app.confluence.client.get_client") as g:
        sess = MagicMock()
        g.return_value = sess
        r401 = MagicMock()
        r401.status_code = 401
        resp_exc = requests.exceptions.HTTPError()
        resp_exc.response = r401
        sess.post.side_effect = resp_exc
        with pytest.raises(requests.exceptions.HTTPError):
            create_page("https://x", "DOC", "T", "<p>x</p>", ("u", "t"))


def test_create_page_403_raises():
    from app.confluence.client import create_page
    import requests

    with patch("app.confluence.client.get_client") as g:
        sess = MagicMock()
        g.return_value = sess
        r403 = MagicMock()
        r403.status_code = 403
        resp_exc = requests.exceptions.HTTPError()
        resp_exc.response = r403
        sess.post.side_effect = resp_exc
        with pytest.raises(requests.exceptions.HTTPError):
            create_page("https://x", "DOC", "T", "<p>x</p>", ("u", "t"))


def test_create_page_network_retry_then_success():
    from app.confluence.client import create_page

    with patch("app.confluence.client.get_client") as g:
        sess = MagicMock()
        g.return_value = sess
        sess.post.side_effect = [ConnectionError("net"), MagicMock(status_code=200, json=lambda: {"id": "1"})]
        with patch("time.sleep"):
            out = create_page("https://x", "DOC", "T", "<p>x</p>", None)
        assert out == {"id": "1"}


def test_create_page_network_exhausted_raises_last_exc():
    from app.confluence.client import create_page, NETWORK_RETRIES

    with patch("app.confluence.client.get_client") as g:
        sess = MagicMock()
        g.return_value = sess
        sess.post.side_effect = ConnectionError("net")
        with patch("time.sleep"):
            with pytest.raises(ConnectionError, match="net"):
                create_page("https://x", "DOC", "T", "<p>x</p>", None)
        assert sess.post.call_count == NETWORK_RETRIES + 1


def test_create_page_429_in_exception_retries():
    from app.confluence.client import create_page
    import requests

    with patch("app.confluence.client.get_client") as g:
        sess = MagicMock()
        g.return_value = sess
        r429 = MagicMock()
        r429.status_code = 429
        exc = requests.exceptions.HTTPError()
        exc.response = r429
        r200 = MagicMock()
        r200.status_code = 200
        r200.json.return_value = {"id": "1"}
        sess.post.side_effect = [exc, r200]
        with patch("time.sleep"):
            out = create_page("https://x", "DOC", "T", "<p>x</p>", None)
        assert out == {"id": "1"}


def test_create_page_429_then_non_ok_raises():
    """Second post after 429 returns e.g. 500; raise_for_status at line 90 raises."""
    from app.confluence.client import create_page
    import requests

    with patch("app.confluence.client.get_client") as g:
        sess = MagicMock()
        g.return_value = sess
        r429 = MagicMock()
        r429.status_code = 429
        r500 = MagicMock()
        r500.status_code = 500
        r500.raise_for_status.side_effect = requests.exceptions.HTTPError()
        call_count = [0]

        def post_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return r429
            return r500

        sess.post.side_effect = post_effect
        with patch("time.sleep"):
            with pytest.raises(requests.exceptions.HTTPError):
                create_page("https://x", "DOC", "T", "<p>x</p>", None)


def test_create_page_exhaust_429_continues_then_raises_last_exc():
    """Four 429s with response on exception hit continue each time; exit loop and raise last_exc (124-126)."""
    from app.confluence.client import create_page
    import requests

    with patch("app.confluence.client.get_client") as g:
        sess = MagicMock()
        g.return_value = sess
        r429 = MagicMock()
        r429.status_code = 429
        exc = requests.exceptions.HTTPError()
        exc.response = r429
        sess.post.side_effect = [exc, exc, exc, exc]
        with patch("time.sleep"):
            with pytest.raises(requests.exceptions.HTTPError):
                create_page("https://x", "DOC", "T", "<p>x</p>", None)
        assert sess.post.call_count == 4


def test_create_page_import_error_requests_exceptions_path():
    """When import requests.exceptions fails, use fallback is_network (114-115)."""
    from app.confluence.client import create_page
    import builtins

    class MyTimeoutError(Exception):
        pass

    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "requests.exceptions":
            raise ImportError("no requests.exceptions")
        return orig_import(name, *args, **kwargs)

    with patch("app.confluence.client.get_client") as g:
        sess = MagicMock()
        g.return_value = sess
        sess.post.side_effect = MyTimeoutError("timed out")
        with patch.object(builtins, "__import__", side_effect=fake_import):
            with patch("time.sleep"):
                with pytest.raises(MyTimeoutError):
                    create_page("https://x", "DOC", "T", "<p>x</p>", None)


def test_get_session_import_error_path():
    import builtins
    import app.confluence.client as client

    client._session = None
    orig_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "requests":
            raise ImportError("no requests")
        return orig_import(name, *args, **kwargs)

    with patch.object(builtins, "__import__", side_effect=fake_import):
        c = client.get_client()
    assert c is None
    client._session = None
    client.get_client()
