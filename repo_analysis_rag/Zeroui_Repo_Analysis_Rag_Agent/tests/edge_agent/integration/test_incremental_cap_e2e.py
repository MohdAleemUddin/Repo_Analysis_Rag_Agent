import json
import os
import shutil
import time
import pytest
from fastapi.testclient import TestClient
from edge_agent.app.main import app
from edge_agent.app.indexing.scan_rules import normalize_root_path, compute_repo_id
from edge_agent.app.indexing import indexer

client = TestClient(app)

@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Set up a clean test environment with mocked index directory."""
    # 1. Setup temporary directories
    rag_index_dir = tmp_path / "rag_index"
    rag_index_dir.mkdir()
    repo_root = tmp_path / "test_repo"
    repo_root.mkdir()

    # 2. Mock index_dir to use our temporary directory
    monkeypatch.setattr("edge_agent.app.indexing.scan_rules.index_dir", lambda: rag_index_dir)
    monkeypatch.setattr("edge_agent.app.indexing.indexer.scan_rules.index_dir", lambda: rag_index_dir)
    monkeypatch.setattr("edge_agent.app.security.token_store.index_dir", lambda: rag_index_dir)
    
    # Mock token verification for API calls
    from edge_agent.app.security import require_token
    app.dependency_overrides[require_token] = lambda: "valid_token"

    yield repo_root, rag_index_dir

    # Cleanup
    app.dependency_overrides.clear()
    indexer.reset_indexer_state()

def test_incremental_cap_e2e_workflow(test_env, monkeypatch):
    """
    E2E test for the incremental indexing cap workflow:
    Full workflow: config -> indexer -> manifest -> API response
    """
    repo_root, rag_index_dir = test_env
    
    # 1. Generate 2500+ test files
    num_files = 2500
    file_paths = []
    for i in range(num_files):
        # Use leading zeros for deterministic lexicographical sorting
        f_name = f"file_{i:04d}.txt"
        f_path = repo_root / f_name
        f_path.write_text(f"Initial content for {f_name}")
        file_paths.append(str(f_path))
    
    normalized_root = normalize_root_path(str(repo_root))
    repo_id = compute_repo_id(normalized_root)

    # 2. Perform initial full index to establish baseline
    # We call the API directly to simulate full workflow
    response = client.post(
        "/index",
        json={"root_path": str(repo_root), "mode": "full"},
        headers={"X-Access-Token": "valid_token"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["indexed_files"] == num_files
    assert data["mode"] == "full"

    # 3. Modify all 2500+ files to trigger incremental indexing
    # We'll just append some text to each file
    for i in range(num_files):
        f_path = repo_root / f"file_{i:04d}.txt"
        f_path.write_text(f"Updated content for file_{i:04d}.txt")

    # 4. Mock the changed_files detection for the incremental run
    # In routes.py, we have a placeholder `changed_files = []`.
    # We need to mock scan_repository to receive these files.
    import edge_agent.app.api.routes as routes
    
    # We want to use the REAL scan_repository but with our file list
    from edge_agent.app.indexing.scan_rules import scan_repository
    
    def mocked_scan_repository(path, mode="full", changed_files=None):
        if mode == "incremental":
            # Pass our 2500 modified files
            return scan_repository(path, mode=mode, changed_files=file_paths)
        return scan_repository(path, mode=mode, changed_files=changed_files)

    monkeypatch.setattr(routes, "scan_repository", mocked_scan_repository)

    # 5. Call /index with mode=incremental
    # Default cap is 2000
    start_time = time.time()
    response = client.post(
        "/index",
        json={"root_path": str(repo_root), "mode": "incremental"},
        headers={"X-Access-Token": "valid_token"}
    )
    duration_ms = int((time.time() - start_time) * 1000)

    # 6. Assertions on API Response
    assert response.status_code == 200
    data = response.json()
    assert data["repo_id"] == repo_id
    assert data["mode"] == "incremental"
    assert data["indexed_files"] == 2000  # Exact cap
    assert data["skipped_files"] == 500   # Remainder (2500 - 2000)
    assert data["duration_ms"] <= duration_ms

    # 7. Assertions on Manifest Content
    manifest_path = rag_index_dir / repo_id / "manifest.json"
    assert manifest_path.exists()
    
    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)
    
    entries = manifest_data["entries"]
    assert len(entries) == num_files
    
    # Verify lexicographical sorting and status
    # Files are file_0000.txt to file_2499.txt
    # First 2000 (0000 to 1999) should be INDEXED
    # Last 500 (2000 to 2499) should be SKIPPED with reason OTHER
    
    # Sort entries by path to verify sequence
    entries.sort(key=lambda x: x["path"])
    
    for i in range(2000):
        expected_path = normalize_root_path(str(repo_root / f"file_{i:04d}.txt"))
        assert entries[i]["path"] == expected_path
        assert entries[i]["status"] == "INDEXED"
        assert "skip_reason" not in entries[i]

    for i in range(2000, 2500):
        expected_path = normalize_root_path(str(repo_root / f"file_{i:04d}.txt"))
        assert entries[i]["path"] == expected_path
        assert entries[i]["status"] == "SKIPPED"
        assert entries[i]["skip_reason"] == "OTHER"

    # 8. Verify /health (optional but good for E2E)
    health_response = client.get("/health", headers={"X-Access-Token": "valid_token"})
    assert health_response.status_code == 200
    health_data = health_response.json()
    assert health_data["indexing"] is False
