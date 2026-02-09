import pytest
import os
import sys
import tempfile
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

def test_exclusion_rules_enforcement(auth_token, monkeypatch):
    """
    Functional test to verify that indexing respects directory and extension exclusions.
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
        
        # Create excluded directories and files inside them
        excluded_dirs = [
            ".git", "node_modules", ".venv", "venv", "dist", "build",
            ".pytest_cache", ".mypy_cache", ".idea", ".vscode"
        ]
        for d in excluded_dirs:
            d_path = root_path / d
            d_path.mkdir()
            (d_path / "dummy.txt").write_text("should be skipped", encoding="utf-8")
            
        # Create files with excluded extensions
        excluded_extensions = [
            "image.png", "video.mp4", "archive.zip", "binary.exe", "data.db"
        ]
        for f in excluded_extensions:
            (root_path / f).write_text("should be skipped", encoding="utf-8")
            
        # Create valid files (should be indexed)
        valid_files = ["main.py", "README.md", "notes.txt"]
        for f in valid_files:
            (root_path / f).write_text("should be indexed", encoding="utf-8")
            
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
        
        # 3. Verification: Check indexed vs skipped counts
        # Valid files: 3
        # Excluded directories: 10
        # Excluded extensions: 5
        # Total skipped = 10 (dirs) + 5 (files) = 15
        assert data["indexed_files"] == 3
        assert data["skipped_files"] == 15
        
        # Verify repo_id matches expectations
        normalized = normalize_root_path(str(root_path))
        expected_repo_id = compute_repo_id(normalized)
        assert data["repo_id"] == expected_repo_id
        
        # Verify health endpoint reflects completion
        health_response = client.get("/health", headers={"X-LOCAL-TOKEN": current_token})
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data["indexing"] is False

if __name__ == "__main__":
    pytest.main([__file__])
