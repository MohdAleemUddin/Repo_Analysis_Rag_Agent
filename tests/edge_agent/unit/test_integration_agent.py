"""Unit tests for app.agents.integration_agent."""

from unittest.mock import patch

try:
    from app.agents.integration_agent import (
        create_page,
        _verify_page,
        schedule_learning_after_create,
    )
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(
        0,
        str(
            Path(__file__).resolve().parents[3]
            / "repo_analysis_rag"
            / "backend_confluence"
        ),
    )
    from app.agents.integration_agent import (
        create_page,
        _verify_page,
        schedule_learning_after_create,
    )


def test_verify_page_success():
    with patch("app.agents.integration_agent.confluence_get_page") as mock_get:
        mock_get.return_value = {"id": "123", "title": "T", "space": {"key": "DOC"}}
        v = _verify_page("http://x", "123", ("u", "p"), "T", "DOC")
    assert v.passed is True


def test_verify_page_exception():
    with patch("app.agents.integration_agent.confluence_get_page") as mock_get:
        mock_get.side_effect = Exception("fail")
        v = _verify_page("http://x", "123", None, "T", "DOC")
    assert v.passed is False
    assert "verification_error" in v.checks


@patch("app.agents.integration_agent.confluence_create_page")
@patch("app.agents.integration_agent.record_success")
@patch("app.agents.integration_agent.confluence_get_page")
def test_create_page_success(mock_get, mock_record, mock_create):
    mock_create.return_value = {
        "id": "1",
        "title": "T",
        "space": {"key": "DOC"},
        "_links": {"webui": "/pages/1"},
    }
    mock_get.return_value = {"id": "1", "title": "T", "space": {"key": "DOC"}}
    out = create_page("http://x", "DOC", "T", "<p>body</p>", auth=None)
    assert out.page.id == "1"
    assert out.page.title == "T"


@patch("app.agents.integration_agent.confluence_create_page")
@patch("app.agents.integration_agent.record_failure")
def test_create_page_exception(mock_record, mock_create):
    mock_create.side_effect = Exception("api fail")
    try:
        create_page("http://x", "DOC", "T", "<p>body</p>", auth=None)
    except Exception:
        pass
    mock_record.assert_called_once()


def test_schedule_learning_after_create():
    schedule_learning_after_create("feedback", {"id": "1"})


@patch("app.agents.integration_agent._learning_executor")
def test_schedule_learning_learn_raises(mock_exec):
    def run_now(fn):
        fn()

    mock_exec.submit = run_now
    with patch(
        "app.agents.integration_agent.learn", side_effect=ValueError("learn fail")
    ):
        schedule_learning_after_create("feedback", {"id": "1"})
