import importlib.util
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

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

def _load_main_module():
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    _log("H1", "test_health_token.py:_load_main_module", "sys.path updated", {"repo_root": str(repo_root), "sys_path": sys.path})
    import edge_agent.app.main as module  # type: ignore
    _log("H1", "test_health_token.py:_load_main_module", "imported main", {"module": str(module)})
    return module


def _load_token_store():
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    _log("H1", "test_health_token.py:_load_token_store", "sys.path updated", {"repo_root": str(repo_root), "sys_path": sys.path})
    import edge_agent.app.security.token_store as module  # type: ignore
    _log("H1", "test_health_token.py:_load_token_store", "imported token_store", {"module": str(module)})
    return module


def test_health_requires_token(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path))
    module = _load_main_module()
    
    # Reset state to ensure clean test
    import edge_agent.app.indexing.indexer as indexer_mod
    indexer_mod.reset_indexing_stats()
    
    app = module.create_app()
    client = TestClient(app)

    response = client.get("/health")
    assert response.status_code == 401
    assert response.json()["error_code"] == "INVALID_TOKEN"

    token_file = tmp_path / "agent_token.txt"
    token = token_file.read_text(encoding="utf-8").strip()
    from unittest.mock import patch
    with patch("edge_agent.app.api.routes.check_ollama", return_value=True), \
         patch("edge_agent.app.api.routes.check_ripgrep", return_value=True), \
         patch("edge_agent.app.api.routes.check_chroma", return_value=True):
        response_ok = client.get("/health", headers={"X-LOCAL-TOKEN": token})
        assert response_ok.status_code == 200
        body = response_ok.json()
        assert body["error_code"] if "error_code" in body else "ok" != "INVALID_TOKEN"
        assert body.get("indexing") is False
        assert body.get("ollama_ok") is True


def test_token_creation_and_reuse(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path))
    token_store = _load_token_store()

    # First creation writes a new token
    first_token = token_store.get_or_create_token()
    token_file = tmp_path / "agent_token.txt"
    assert token_file.exists()
    assert token_file.read_text(encoding="utf-8").strip() == first_token

    # Existing token is reused without regeneration
    second_token = token_store.get_or_create_token()
    assert second_token == first_token


def test_token_path_defaults_to_user_profile(tmp_path, monkeypatch):
    monkeypatch.delenv("RAG_INDEX_DIR", raising=False)
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    token_store = _load_token_store()

    token = token_store.get_or_create_token()
    token_file = tmp_path / ".offline_rag_index" / "agent_token.txt"
    assert token_file.exists()
    assert token_file.read_text(encoding="utf-8").strip() == token
