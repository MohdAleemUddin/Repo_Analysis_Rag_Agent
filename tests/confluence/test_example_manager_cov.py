"""Tests for app.confluence.example_manager (coverage)."""
import json
import os
import tempfile
from unittest.mock import MagicMock

import pytest

try:
    from app.confluence import example_manager
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "offline-folder-rag" / "edge_agent"))
    from app.confluence import example_manager


def test_content_profile_hash():
    h = example_manager._content_profile_hash({"a": 1})
    assert isinstance(h, str) and len(h) == 64


def test_get_file_examples_missing_file():
    with tempfile.TemporaryDirectory() as tmp:
        examples = example_manager._get_file_examples(base_dir=tmp)
    assert examples == []


def test_get_file_examples_with_data():
    with tempfile.TemporaryDirectory() as tmp:
        path = example_manager._examples_file_path(tmp)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"version": 1, "examples": [{"id": "x", "content_profile_hash": "h"}]}, f)
        examples = example_manager._get_file_examples(base_dir=tmp)
    assert len(examples) == 1
    assert examples[0]["id"] == "x"


def test_store_example_file_fallback():
    with tempfile.TemporaryDirectory() as tmp:
        eid, learned = example_manager.store_example(
            content_profile={"lang": "py"},
            template_id="t1",
            template_name="T1",
            confidence_score=0.9,
            examples_base_dir=tmp,
        )
    assert learned is True
    assert isinstance(eid, str)


def test_store_example_db_path():
    mock_execute = MagicMock()
    eid, learned = example_manager.store_example(
        content_profile={"x": 1},
        template_id="t",
        template_name="T",
        db_execute=mock_execute,
    )
    assert learned is True
    mock_execute.assert_called()


def test_get_examples_file_based():
    with tempfile.TemporaryDirectory() as tmp:
        example_manager.store_example({"a": 1}, "t", "T", examples_base_dir=tmp)
        examples = example_manager.get_examples(examples_base_dir=tmp)
    assert len(examples) >= 1


def test_get_examples_filters():
    with tempfile.TemporaryDirectory() as tmp:
        examples = example_manager.get_examples(project_path="/none", from_date="2020-01-01", to_date="2025-01-01", examples_base_dir=tmp)
    assert isinstance(examples, list)


def test_get_examples_db_fetch():
    mock_fetch = MagicMock(return_value=[{"content_profile": {}, "template_ref": {"template_id": "t"}, "learned_at": "2020-01-01"}])
    examples = example_manager.get_examples(db_fetch=mock_fetch)
    assert len(examples) == 1
    mock_fetch.assert_called_once()


def test_update_embeddings_no_op():
    example_manager.update_embeddings_for_examples()


def test_update_embeddings_with_callback():
    mock_upsert = MagicMock()
    example_manager.update_embeddings_for_examples(vector_store_upsert=mock_upsert)
    mock_upsert.assert_called_once()


def test_record_learning():
    example_manager.record_learning("c1", 0.5, 0.8, db_execute=None)


def test_record_learning_with_db():
    mock_execute = MagicMock()
    example_manager.record_learning("c1", 0.5, 0.8, db_execute=mock_execute)
    mock_execute.assert_called_once()


def test_apply_feedback_file():
    with tempfile.TemporaryDirectory() as tmp:
        example_manager.apply_feedback("c1", 4, feedback_text="ok", examples_base_dir=tmp)
        path = example_manager._feedback_file_path(tmp)
        assert os.path.isfile(path)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        feedback = data.get("feedback", [])
    assert len(feedback) == 1
    assert feedback[0]["intelligence_score"] == 4


def test_get_collective_count_zero_when_opt_out():
    assert example_manager.get_collective_count(team_sharing_opt_in=False) == 0


def test_get_collective_count_file():
    with tempfile.TemporaryDirectory() as tmp:
        n = example_manager.get_collective_count(examples_base_dir=tmp)
    assert n >= 0


def test_get_collective_count_db():
    mock_count = MagicMock(return_value=10)
    assert example_manager.get_collective_count(db_fetch_count=mock_count) == 10


def test_load_example_no_op():
    example_manager.load_example("x")


def test_embedding_to_db_invalid():
    assert example_manager._embedding_to_db([0.1] * 100) is None
    assert example_manager._embedding_to_db(None) is None


def test_embedding_to_db_valid():
    emb = [0.1] * 1536
    s = example_manager._embedding_to_db(emb)
    assert s is not None and "0.1" in s


def test_store_example_db_exception():
    def fail(*a, **k):
        raise RuntimeError("db")
    with tempfile.TemporaryDirectory() as tmp:
        eid, learned = example_manager.store_example({"a": 1, "unique": "db_ex"}, "t", "T", db_execute=fail, examples_base_dir=tmp)
    assert learned is True


def test_get_examples_db_fetch_exception():
    def fail(*a, **k):
        raise RuntimeError("db")
    with tempfile.TemporaryDirectory() as tmp:
        examples = example_manager.get_examples(db_fetch=fail, examples_base_dir=tmp)
    assert isinstance(examples, list)


def test_update_embeddings_exception():
    def fail(*a, **k):
        raise RuntimeError("upsert fail")
    example_manager.update_embeddings_for_examples(vector_store_upsert=fail)


def test_apply_feedback_db_ensure():
    with tempfile.TemporaryDirectory() as tmp:
        mock_ensure = MagicMock()
        example_manager.apply_feedback("c1", 5, db_ensure_creation=mock_ensure, examples_base_dir=tmp)
    mock_ensure.assert_called_once_with("c1")


def test_get_collective_count_db_exception():
    def fail():
        raise RuntimeError("db")
    with tempfile.TemporaryDirectory() as tmp:
        n = example_manager.get_collective_count(db_fetch_count=fail, examples_base_dir=tmp)
    assert n >= 0
