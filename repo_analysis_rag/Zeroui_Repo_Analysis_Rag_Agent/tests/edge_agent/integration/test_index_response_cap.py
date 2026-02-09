import json
import os
import pytest
from fastapi.testclient import TestClient
from edge_agent.app.main import app
from edge_agent.app.indexing.scan_rules import normalize_root_path, compute_repo_id
from edge_agent.app.security.token_store import index_dir

client = TestClient(app)

@pytest.fixture
def mock_token(monkeypatch):
    # Mock the dependency in FastAPI
    from edge_agent.app.security import require_token
    app.dependency_overrides[require_token] = lambda: "valid_token"
    yield
    app.dependency_overrides.clear()

def test_index_incremental_cap_response(mock_token, tmp_path, monkeypatch):
    """
    Integration test for /index API with incremental mode and file cap.
    """
    # 1. Setup test folder with > 2000 files
    root_path = tmp_path / "test_repo"
    root_path.mkdir()
    
    # Create 2100 dummy files
    file_paths = []
    for i in range(2100):
        f_path = root_path / f"file_{i:04d}.py"
        f_path.write_text(f"print({i})")
        file_paths.append(str(f_path))
    
    # Mock index_dir to use tmp_path
    monkeypatch.setattr("edge_agent.app.indexing.scan_rules.index_dir", lambda: tmp_path)
    monkeypatch.setattr("edge_agent.app.indexing.indexer.scan_rules.index_dir", lambda: tmp_path)
    monkeypatch.setattr("edge_agent.app.api.routes.normalize_root_path", lambda x: str(x).lower())
    
    # We need to ensure routes.py uses the same repo_id
    normalized_root = str(root_path).lower()
    repo_id = compute_repo_id(normalized_root)
    
    # 2. Call /index with mode=incremental
    # We need to mock the changed_files logic in routes.py or pass them.
    # Since I added changed_files = [] in routes.py as a placeholder, 
    # I should mock it to return our 2100 files.
    
    import edge_agent.app.api.routes as routes
    monkeypatch.setattr(routes, "scan_repository", 
                        lambda path, mode, changed_files: 
                        app.state.scan_repository_mock(path, mode, file_paths if mode == "incremental" else None))
    
    from edge_agent.app.indexing.scan_rules import scan_repository
    app.state.scan_repository_mock = scan_repository

    response = client.post(
        "/index",
        json={"root_path": str(root_path), "mode": "incremental"},
        headers={"X-Access-Token": "valid_token"}
    )
    
    # 3. Assert response includes correct skipped_files count
    assert response.status_code == 200
    data = response.json()
    assert data["repo_id"] == repo_id
    assert data["mode"] == "incremental"
    assert data["indexed_files"] == 2000
    assert data["skipped_files"] == 100
    
    # 4. Verifies skipped files appear in manifest with skip_reason='OTHER'
    manifest_path = tmp_path / repo_id / "manifest.json"
    assert manifest_path.exists()
    
    with open(manifest_path, "r") as f:
        manifest_data = json.load(f)
    
    skipped_entries = [e for e in manifest_data["entries"] if e["status"] == "SKIPPED" and e["skip_reason"] == "OTHER"]
    assert len(skipped_entries) == 100
    
    # Verify lexicographical sorting (first 2000 indexed, last 100 skipped)
    # file_0000 to file_1999 should be indexed, file_2000 to file_2099 should be skipped
    indexed_paths = [e["path"] for e in manifest_data["entries"] if e["status"] == "INDEXED"]
    assert len(indexed_paths) == 2000
    assert normalize_root_path(str(root_path / "file_0000.py")) in indexed_paths
    assert normalize_root_path(str(root_path / "file_1999.py")) in indexed_paths
    assert normalize_root_path(str(root_path / "file_2000.py")) not in indexed_paths
    
    skipped_paths = [e["path"] for e in skipped_entries]
    assert normalize_root_path(str(root_path / "file_2000.py")) in skipped_paths
    assert normalize_root_path(str(root_path / "file_2099.py")) in skipped_paths
