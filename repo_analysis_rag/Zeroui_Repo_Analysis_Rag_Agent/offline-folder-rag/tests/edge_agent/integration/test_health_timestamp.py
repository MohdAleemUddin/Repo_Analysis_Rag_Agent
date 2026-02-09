import sys
import time
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

# Setup path to include the project root
def _setup_path():
    repo_root = Path(__file__).resolve().parents[4]
    project_root = repo_root / "offline-folder-rag"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

_setup_path()

from edge_agent.app.main import create_app
from edge_agent.app.security.token_store import get_or_create_token
from edge_agent.app.indexing import indexer

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path))
    app = create_app()
    return TestClient(app)

@pytest.fixture
def auth_header(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path))
    token = get_or_create_token()
    return {"X-LOCAL-TOKEN": token}

@pytest.fixture
def test_repo(tmp_path):
    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()
    (repo_dir / "file1.txt").write_text("content 1", encoding="utf-8")
    (repo_dir / "file2.md").write_text("# content 2", encoding="utf-8")
    return repo_dir

@patch("edge_agent.app.api.routes.check_ollama", return_value=True)
@patch("edge_agent.app.api.routes.check_ripgrep", return_value=True)
@patch("edge_agent.app.api.routes.check_chroma", return_value=True)
def test_health_timestamp_updates_after_indexing(
    mock_chroma, mock_ripgrep, mock_ollama, client, auth_header, test_repo
):
    """
    Integration test for US-19:
    1. Baseline health check.
    2. Start indexing.
    3. Verify indexing flag is True.
    4. Complete indexing.
    5. Verify timestamp increased and flag is False.
    """
    # 1. Baseline
    response = client.get("/health", headers=auth_header)
    assert response.status_code == 200
    baseline_data = response.json()
    baseline_ts = baseline_data["last_index_completed_epoch_ms"]
    assert baseline_data["indexing"] is False
    
    # 2. Start indexing (incremental)
    # We need to mock the actual indexing logic to be deterministic and update stats
    # Since the current /index route is a placeholder, we will simulate the indexer calls
    # that the real route would make.
    
    repo_path = str(test_repo)
    
    # Simulate what the indexer does during an operation
    with indexer.acquire_indexing_lock("test-repo-id"):
        # 3. Verify indexing flag is True during process
        response_mid = client.get("/health", headers=auth_header)
        assert response_mid.json()["indexing"] is True
        
        # Simulate processing files
        indexer.increment_indexed_files()
        indexer.increment_indexed_files()
        
        response_mid2 = client.get("/health", headers=auth_header)
        assert response_mid2.json()["indexed_files_so_far"] == 2

    # 4. After completion
    # Small sleep to ensure timestamp would be different if it was very fast
    time.sleep(0.01)
    
    # 5. Verify final state
    response_final = client.get("/health", headers=auth_header)
    assert response_final.status_code == 200
    final_data = response_final.json()
    
    assert final_data["indexing"] is False
    assert final_data["last_index_completed_epoch_ms"] > baseline_ts
    assert final_data["indexed_files_so_far"] == 2
    
    # Verify the timestamp is recent
    current_ms = int(time.time() * 1000)
    assert current_ms - final_data["last_index_completed_epoch_ms"] < 5000
