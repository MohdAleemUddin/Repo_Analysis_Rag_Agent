"""Tests for app.confluence.db_adapter (coverage with mocked connection)."""

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


def test_get_connection_none_when_no_url():
    with patch.object(
        db_adapter, "get_confluence_config", return_value={"database_url": None}
    ):
        db_adapter._conn = None
        conn = db_adapter.get_connection()
    assert conn is None


def test_db_execute_no_conn():
    with patch.object(db_adapter, "get_connection", return_value=None):
        db_adapter.db_execute("SELECT 1", ())


def test_db_fetch_examples_no_conn():
    with patch.object(db_adapter, "get_connection", return_value=None):
        out = db_adapter.db_fetch_examples()
    assert out == []


def test_db_fetch_examples_count_no_conn():
    with patch.object(db_adapter, "get_connection", return_value=None):
        n = db_adapter.db_fetch_examples_count()
    assert n == 0


def test_db_ensure_creation_no_conn():
    with patch.object(db_adapter, "get_connection", return_value=None):
        ok = db_adapter.db_ensure_creation_for_feedback(
            "00000000-0000-0000-0000-000000000001"
        )
    assert ok is False


def test_db_fetch_intelligence_metrics_no_conn():
    with patch.object(db_adapter, "get_connection", return_value=None):
        out = db_adapter.db_fetch_intelligence_metrics()
    assert out == {}


def test_db_update_template_confidence_no_conn():
    with patch.object(db_adapter, "get_connection", return_value=None):
        ok = db_adapter.db_update_template_confidence("t1", 0.9)
    assert ok is False


def test_db_get_creation_template_id_no_conn():
    with patch.object(db_adapter, "get_connection", return_value=None):
        tid = db_adapter.db_get_creation_template_id(
            "00000000-0000-0000-0000-000000000001"
        )
    assert tid is None


def test_db_fetch_examples_with_mock_conn():
    row = ("id1", '{"a":1}', "t1", "{}", None, 0.9, 4, None)
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_cur.fetchall.return_value = [row]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        out = db_adapter.db_fetch_examples()
    assert len(out) == 1
    assert out[0]["id"] == "id1"


def test_db_fetch_examples_count_with_mock_conn():
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_cur.fetchone.return_value = (5,)
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        n = db_adapter.db_fetch_examples_count()
    assert n == 5


def test_db_fetch_intelligence_metrics_with_mock_conn():
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)
    mock_cur.fetchone.side_effect = [
        (10,),
        (20,),
        (0.94,),
        (4.7,),
        (0.15,),
        (0.94,),
        (4.7,),
    ]
    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cur
    with patch.object(db_adapter, "get_connection", return_value=mock_conn):
        out = db_adapter.db_fetch_intelligence_metrics()
    assert "examples_learned" in out or "template_selection_accuracy" in out
