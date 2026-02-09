import pytest
import os
import sys
import tempfile
import shutil
from pathlib import Path
from fastapi.testclient import TestClient

# Add the project root to sys.path to allow imports from edge_agent
repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from edge_agent.app.main import app
from edge_agent.app.security.token_store import get_or_create_token
from edge_agent.app.indexing.scan_rules import normalize_root_path, compute_repo_id
from edge_agent.app.indexing.indexer import reset_indexing_stats

client = TestClient(app)

@pytest.fixture
def auth_token():
    return get_or_create_token()

def test_root_path_boundary_enforcement(auth_token, monkeypatch):
    """
    Functional test to verify that indexing respects the root_path boundary.
    """
    # 1. Setup temporary directory structure
    with tempfile.TemporaryDirectory() as base_temp_dir:
        base_temp_path = Path(base_temp_dir).resolve()
        
        # Set RAG_INDEX_DIR to isolate indexing artifacts
        index_dir = base_temp_path / "index_storage"
        index_dir.mkdir()
        monkeypatch.setenv("RAG_INDEX_DIR", str(index_dir))
        
        # Re-fetch token because it depends on RAG_INDEX_DIR
        from edge_agent.app.security.token_store import get_or_create_token as get_token
        current_token = get_token()
        
        # Define root_path as a subdirectory
        root_path = base_temp_path / "test_repo"
        root_path.mkdir()
        
        # Create internal file
        internal_file = root_path / "internal.txt"
        internal_file.write_text("This is inside the boundary.", encoding="utf-8")
        
        # Create outside file (sibling to root_path)
        outside_file = base_temp_path / "outside.txt"
        outside_file.write_text("This is outside the boundary.", encoding="utf-8")
        
        # Reset indexing stats for a clean test
        reset_indexing_stats()
        
        # 2. Execution: Call POST /index
        response = client.post(
            "/index",
            json={"root_path": str(root_path), "mode": "full"},
            headers={"X-LOCAL-TOKEN": current_token}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify repo_id matches expectations
        normalized = normalize_root_path(str(root_path))
        expected_repo_id = compute_repo_id(normalized)
        assert data["repo_id"] == expected_repo_id
        
        # 3. Verification: Check indexed vs skipped counts
        # internal.txt should be indexed (1 file)
        # outside.txt should NOT be seen by the walk starting at root_path
        assert data["indexed_files"] == 1
        assert data["skipped_files"] == 0 # No files under root_path were skipped
        
        # Verify health endpoint reflects completion
        # Note: The /health endpoint in routes.py has complex logic for indexed_files_so_far
        # that depends on whether indexing is active or a pending_snapshot exists.
        health_response = client.get("/health", headers={"X-LOCAL-TOKEN": current_token})
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["indexing"] is False
        
        # Verify manifest path exists in response
        assert "manifest_path" in data
        assert expected_repo_id in data["manifest_path"]

if __name__ == "__main__":
    pytest.main([__file__])
