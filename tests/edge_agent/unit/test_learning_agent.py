"""Unit tests for app.agents.learning_agent."""

from unittest.mock import patch

try:
    from app.agents.learning_agent import (
        on_creation_success,
        learn_from_feedback,
        get_learning_indicator_message,
        get_collective_intelligence_count,
        learn,
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
    from app.agents.learning_agent import (
        on_creation_success,
        learn_from_feedback,
        get_learning_indicator_message,
        get_collective_intelligence_count,
        learn,
    )


@patch("app.agents.learning_agent.store_example")
@patch("app.agents.learning_agent.update_embeddings_for_examples")
@patch("app.agents.learning_agent.record_learning")
def test_on_creation_success_learning(mock_record, mock_update, mock_store):
    mock_store.return_value = ("ex1", True)
    occurred, msg = on_creation_success(
        "c1",
        {"types": ["code"]},
        "t1",
        "T1",
        confidence_score=0.9,
        db_execute=None,
        examples_base_dir=None,
    )
    assert occurred is True
    assert "Learning" in msg or msg == ""


@patch("app.agents.learning_agent.store_example")
@patch("app.agents.learning_agent.update_embeddings_for_examples")
@patch("app.agents.learning_agent.record_learning")
def test_on_creation_success_no_learning(mock_record, mock_update, mock_store):
    mock_store.return_value = ("ex1", False)
    occurred, msg = on_creation_success(
        "c1",
        {"types": ["code"]},
        "t1",
        "T1",
        confidence_score=0.9,
        db_execute=None,
        examples_base_dir=None,
    )
    assert occurred is False


@patch("app.agents.learning_agent.apply_feedback")
@patch("app.agents.learning_agent.record_learning")
def test_learn_from_feedback(mock_record, mock_apply):
    learn_from_feedback("c1", 5, feedback_text="Great!", db_execute=None)
    mock_apply.assert_called_once()
    mock_record.assert_called_once()


@patch("app.agents.learning_agent.apply_feedback")
@patch("app.agents.learning_agent.record_learning")
def test_learn_from_feedback_with_template_update(mock_record, mock_apply):
    def db_get(_):
        return "t1"

    def db_update(_, __):
        return True

    learn_from_feedback(
        "c1", 4, db_get_template_id=db_get, db_update_template=db_update
    )


@patch("app.agents.learning_agent.apply_feedback")
@patch("app.agents.learning_agent.record_learning")
def test_learn_from_feedback_template_update_exception(mock_record, mock_apply):
    def db_get(_):
        return "t1"

    def db_update(_, __):
        raise RuntimeError("db fail")

    learn_from_feedback(
        "c1", 4, db_get_template_id=db_get, db_update_template=db_update
    )
    mock_apply.assert_called_once()


def test_get_learning_indicator_message_true():
    m = get_learning_indicator_message(True)
    assert "Learning" in m


def test_get_learning_indicator_message_false():
    m = get_learning_indicator_message(False)
    assert m == ""


@patch("app.agents.learning_agent.get_collective_count", return_value=10)
def test_get_collective_intelligence_count(mock_get):
    n = get_collective_intelligence_count(db_fetch_count=mock_get)
    assert n == 10


def test_get_collective_intelligence_count_opt_out():
    n = get_collective_intelligence_count(team_sharing_opt_in=False)
    assert n == 0


def test_learn():
    learn("feedback text")
    learn("feedback", creation_metadata={"id": "1"})
