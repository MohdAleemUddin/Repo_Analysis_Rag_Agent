import importlib
import os
import sys
from pathlib import Path

import pytest
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


def _load_app(tmp_path):
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    _log("H1", "test_token_enforcement.py:_load_app", "sys.path updated", {"repo_root": str(repo_root), "sys_path": sys.path})

    app_module = importlib.import_module("edge_agent.app.main")
    _log("H1", "test_token_enforcement.py:_load_app", "imported main", {"main": str(app_module)})

    os.environ["RAG_INDEX_DIR"] = str(tmp_path)
    return app_module.app


@pytest.fixture
def client(tmp_path):
    return TestClient(_load_app(tmp_path))


_EXPECTED_ERROR = {
    "error_code": "INVALID_TOKEN",
    "message": "The provided token is missing or invalid.",
    "remediation": "Please provide a valid X-LOCAL-TOKEN in the request headers.",
}


def test_health_endpoint_invalid_token(client):
    response = client.get("/health")
    assert response.status_code == 401
    assert response.json() == _EXPECTED_ERROR


def test_ask_endpoint_invalid_token(client):
    response = client.post("/ask", json={"query": "What is the repo status?"})
    assert response.status_code == 401
    assert response.json() == _EXPECTED_ERROR
