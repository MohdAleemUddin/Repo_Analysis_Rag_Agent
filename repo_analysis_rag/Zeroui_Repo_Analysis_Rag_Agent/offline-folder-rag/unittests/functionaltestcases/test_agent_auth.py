import os
import sys
import importlib
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from edge_agent.app.main import app  # type: ignore
from edge_agent.app.security.token_store import get_or_create_token  # type: ignore
from edge_agent.app.indexing.indexer import reset_indexing_stats

repo_root = Path(__file__).resolve().parents[3]
project_root = repo_root / "offline-folder-rag"
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

_DEBUG_LOG = Path(r"c:\Users\FAZLEEN ANEESA\Desktop\Rag_Agent\.cursor\debug.log")
_SESSION = "debug-session"
_RUN = "run2"


def _log(hypothesis_id: str, location: str, message: str, data: dict):
    try:
        _DEBUG_LOG.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "sessionId": _SESSION,
            "runId": _RUN,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": __import__("time").time(),
        }
        with _DEBUG_LOG.open("a", encoding="utf-8") as f:
            import json

            f.write(json.dumps(payload) + "\n")
    except Exception:
        pass


def _fresh_client(tmp_path):
    os.environ["RAG_INDEX_DIR"] = str(tmp_path)
    _log("H1", "test_agent_auth.py:_fresh_client", "env set", {"RAG_INDEX_DIR": str(tmp_path), "sys_path": sys.path})
    import edge_agent.app.main as main
    import edge_agent.app.security.token_store as token_store

    importlib.reload(token_store)
    importlib.reload(main)
    _log("H1", "test_agent_auth.py:_fresh_client", "modules reloaded", {"main": str(main), "token_store": str(token_store)})
    app = main.create_app()
    return TestClient(app), token_store.get_or_create_token()


def test_health_endpoint_auth(tmp_path):
    client, auth_token = _fresh_client(tmp_path)

    # Reset state to ensure clean test
    reset_indexing_stats()

    # Valid token
    with patch("edge_agent.app.api.routes.check_ollama", return_value=True), \
         patch("edge_agent.app.api.routes.check_ripgrep", return_value=True), \
         patch("edge_agent.app.api.routes.check_chroma", return_value=True):
        response = client.get("/health", headers={"X-LOCAL-TOKEN": auth_token})
        assert response.status_code == 200
        assert response.json() == {
            "indexing": False,
            "indexed_files_so_far": 0,
            "estimated_total_files": 0,
            "last_index_completed_epoch_ms": 0,
            "ollama_ok": True,
            "ripgrep_ok": True,
            "chroma_ok": True,
        }

    response = client.get("/health", headers={"X-LOCAL-TOKEN": auth_token})
    assert response.status_code == 200
    body = response.json()
    assert body["indexing"] is False
    assert body["ollama_ok"] is True

    # Invalid token
    response = client.get("/health", headers={"X-LOCAL-TOKEN": "wrong_token"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"

    # Missing token
    response = client.get("/health")
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"

def test_index_endpoint_auth(tmp_path):
    client, auth_token = _fresh_client(tmp_path)
    root_path = tmp_path / "repo"
    root_path.mkdir(parents=True, exist_ok=True)

    response = client.post(
        "/index",
        headers={"X-LOCAL-TOKEN": auth_token},
        json={"root_path": str(root_path)},
    )
    assert response.status_code == 200

    data = response.json()
    assert "repo_id" in data
    assert len(data["repo_id"]) == 64
    assert data["mode"] == "full"
    assert data["indexed_files"] == 0

    # Invalid token
    response = client.post("/index", headers={"X-LOCAL-TOKEN": "wrong_token"})
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"
    
    # Clean up env
    del os.environ["RAG_INDEX_DIR"]


def test_ask_endpoint_auth(tmp_path):
    client, auth_token = _fresh_client(tmp_path)

    response = client.post(
        "/ask", 
        headers={"X-LOCAL-TOKEN": auth_token},
        json={"query": "test query"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "rag"
    assert payload["confidence"] in {"found", "partial", "not_found"}
    assert isinstance(payload.get("answer"), str)
    assert isinstance(payload.get("citations"), list)

    # Invalid token
    response = client.post(
        "/ask", 
        headers={"X-LOCAL-TOKEN": "wrong_token"},
        json={"query": "test query"}
    )
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"
