import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch

repo_root = Path(__file__).resolve().parents[3]
project_root = repo_root / "offline-folder-rag"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from edge_agent.app.security.token_store import index_dir, get_or_create_token  # type: ignore

def test_index_dir_rag_env(monkeypatch):
    monkeypatch.setenv("RAG_INDEX_DIR", "/tmp/rag_index")
    # Use Path to handle OS-specific separators in comparison
    assert Path(index_dir()) == Path("/tmp/rag_index")

def test_index_dir_userprofile_fallback(monkeypatch):
    monkeypatch.delenv("RAG_INDEX_DIR", raising=False)
    monkeypatch.setenv("USERPROFILE", "/home/user")
    assert str(index_dir()) == str(Path("/home/user") / ".offline_rag_index")

def test_get_or_create_token_existing(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path))
    token_file = tmp_path / "agent_token.txt"
    token_file.write_text("existing_token")
    assert get_or_create_token() == "existing_token"

def test_get_or_create_token_new(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path))
    # Ensure file doesn't exist
    token_file = tmp_path / "agent_token.txt"
    if token_file.exists():
        token_file.unlink()
    token = get_or_create_token()
    assert len(token) == 64 # sha256 hex
    assert token_file.exists()
    assert token_file.read_text().strip() == token

