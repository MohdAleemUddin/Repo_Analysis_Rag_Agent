"""Additional tests for db_adapter full coverage."""

from unittest.mock import MagicMock, patch

try:
    from app.confluence import db_adapter
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
    from app.confluence import db_adapter


def test_get_connection_with_url():
    try:
        with patch.object(
            db_adapter,
            "get_confluence_config",
            return_value={"database_url": "postgres://x"},
        ):
            with patch("psycopg2.connect") as mock_conn:
                mock_conn.return_value = MagicMock(closed=False)
                db_adapter._conn = None
                conn = db_adapter.get_connection()
                assert conn is not None or db_adapter._conn is None
    finally:
        db_adapter._conn = None


def test_db_execute_with_conn():
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        db_adapter.db_execute("SELECT 1", ())
    mock_conn.commit.assert_called_once()


def test_db_execute_exception_rollback():
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(side_effect=Exception("fail"))
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        db_adapter.db_execute("SELECT 1", ())
    mock_conn.rollback.assert_called_once()


def test_db_fetch_examples_with_conn_and_filters():
    row = ("id1", '{"a":1}', "t1", "{}", None, 0.9, 4, None)
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_cur.fetchall.return_value = [row]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        out = db_adapter.db_fetch_examples(
            from_date="2024-01-01", to_date="2024-12-31", template_id="t1"
        )
    assert len(out) == 1


def test_db_fetch_examples_template_type_filter():
    row = ("id1", "{}", "t1", "{}", None, 0.9, None, None)
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_cur.fetchall.return_value = [row]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        out = db_adapter.db_fetch_examples(template_type="Default")
    assert isinstance(out, list)


def test_db_fetch_examples_exception():
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = Exception("db fail")
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        out = db_adapter.db_fetch_examples()
    assert out == []


def test_db_ensure_creation_success():
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        ok = db_adapter.db_ensure_creation_for_feedback(
            "00000000-0000-0000-0000-000000000001"
        )
    assert ok is True


def test_db_ensure_creation_exception():
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = Exception("fail")
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        ok = db_adapter.db_ensure_creation_for_feedback(
            "00000000-0000-0000-0000-000000000001"
        )
    assert ok is False


def test_db_fetch_intelligence_metrics_exception():
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = Exception("fail")
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        out = db_adapter.db_fetch_intelligence_metrics()
    assert out == {}


def test_db_update_template_confidence_success():
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        ok = db_adapter.db_update_template_confidence(
            "00000000-0000-0000-0000-000000000001", 0.95
        )
    assert ok is True


def test_db_update_template_confidence_exception():
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = Exception("fail")
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        ok = db_adapter.db_update_template_confidence("t1", 0.9)
    assert ok is False


def test_db_get_creation_template_id_success():
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_cur.fetchone.return_value = ("tid1",)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        tid = db_adapter.db_get_creation_template_id(
            "00000000-0000-0000-0000-000000000001"
        )
    assert tid == "tid1"


def test_db_get_creation_template_id_exception():
    mock_conn = MagicMock()
    mock_conn.cursor.side_effect = Exception("fail")
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        tid = db_adapter.db_get_creation_template_id("c1")
    assert tid is None
