import sys
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch

def _setup_path():
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

_setup_path()

from edge_agent.app.main import create_app
from edge_agent.app.security import token_store

@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path))
    app = create_app()
    return TestClient(app)

@pytest.fixture
def auth_header(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path))
    token = token_store.get_or_create_token()
    return {"X-LOCAL-TOKEN": token}

def test_health_endpoint_fields_and_types(client, auth_header):
    """Test GET /health returns all 7 required fields with correct types."""
    response = client.get("/health", headers=auth_header)
    assert response.status_code == 200
    data = response.json()
    
    expected_fields = {
        "indexing": bool,
        "indexed_files_so_far": int,
        "estimated_total_files": int,
        "last_index_completed_epoch_ms": int,
        "ollama_ok": bool,
        "ripgrep_ok": bool,
        "chroma_ok": bool
    }
    
    for field, expected_type in expected_fields.items():
        assert field in data, f"Missing field: {field}"
        assert isinstance(data[field], expected_type), f"Field {field} has wrong type: expected {expected_type}, got {type(data[field])}"

def test_health_token_enforcement(client):
    """Test token enforcement (INVALID_TOKEN without header)."""
    response = client.get("/health")
    assert response.status_code == 401
    data = response.json()
    assert data["error_code"] == "INVALID_TOKEN"

@patch("edge_agent.app.api.routes.check_ollama")
@patch("edge_agent.app.api.routes.check_ripgrep")
@patch("edge_agent.app.api.routes.check_chroma")
def test_health_component_check_values(mock_chroma, mock_ripgrep, mock_ollama, client, auth_header):
    """Test component check boolean values reflect the status of the components."""
    # Test all OK
    mock_ollama.return_value = True
    mock_ripgrep.return_value = True
    mock_chroma.return_value = True
    
    response = client.get("/health", headers=auth_header)
    data = response.json()
    assert data["ollama_ok"] is True
    assert data["ripgrep_ok"] is True
    assert data["chroma_ok"] is True
    
    # Test some failing
    mock_ollama.return_value = False
    mock_ripgrep.return_value = False
    mock_chroma.return_value = True
    
    response = client.get("/health", headers=auth_header)
    data = response.json()
    assert data["ollama_ok"] is False
    assert data["ripgrep_ok"] is False
    assert data["chroma_ok"] is True
