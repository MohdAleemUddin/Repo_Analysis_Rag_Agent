from pathlib import Path

import os

from edge_agent.app.indexing import indexer
from edge_agent.app.config.defaults import DEFAULT_INDEX_DIR


def test_index_dir_uses_env(monkeypatch, tmp_path):
    env_dir = tmp_path / "custom_index"
    monkeypatch.setenv("RAG_INDEX_DIR", str(env_dir))

    resolved = indexer.resolve_index_dir()

    assert resolved == env_dir


def test_index_dir_uses_default_when_env_missing(monkeypatch):
    monkeypatch.delenv("RAG_INDEX_DIR", raising=False)

    resolved = indexer.resolve_index_dir()

    assert resolved == DEFAULT_INDEX_DIR
    assert isinstance(resolved, Path)
