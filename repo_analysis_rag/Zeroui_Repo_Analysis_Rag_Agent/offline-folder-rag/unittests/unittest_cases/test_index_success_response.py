import importlib
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from edge_agent.app.security import TOKEN_HEADER, get_or_create_token


def _load_fastapi_app():
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    module = importlib.import_module("edge_agent.app.main")
    return module.app


def test_index_success_response_contract(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path))
    app = _load_fastapi_app()
    client = TestClient(app)

    repo_path = tmp_path / "repo"
    repo_path.mkdir()

    token = get_or_create_token()

    response = client.post(
        "/index",
        json={"root_path": str(repo_path)},
        headers={TOKEN_HEADER: token},
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/json")

    payload = response.json()
    expected_fields = {
        "repo_id", "mode", "indexed_files", "skipped_files", 
        "chunks_added", "duration_ms", "manifest_path", "collections"
    }
    assert set(payload.keys()) == expected_fields
    assert isinstance(payload["repo_id"], str)
    assert isinstance(payload["mode"], str)
    for numeric_field in {"indexed_files", "skipped_files", "chunks_added", "duration_ms"}:
        assert isinstance(payload[numeric_field], int)
