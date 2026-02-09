import importlib
import importlib.util
import sys
import threading
from pathlib import Path

from fastapi.testclient import TestClient

import pytest

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

def _load_indexer_module():
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    _log("H1", "test_indexer_state.py:_load_indexer_module", "sys.path updated", {"repo_root": str(repo_root), "sys_path": sys.path})
    import edge_agent.app.indexing.indexer as module  # type: ignore
    _log("H1", "test_indexer_state.py:_load_indexer_module", "imported indexer", {"module": str(module)})
    return module


def _load_edge_agent_app_modules():
    repo_root = Path(__file__).resolve().parents[2]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    _log("H1", "test_indexer_state.py:_load_edge_agent_app_modules", "sys.path updated", {"repo_root": str(repo_root), "sys_path": sys.path})
    app_main = importlib.import_module("edge_agent.app.main")
    routes_module = importlib.import_module("edge_agent.app.api.routes")
    security_module = importlib.import_module("edge_agent.app.security")
    scan_rules_module = importlib.import_module("edge_agent.app.indexing.scan_rules")
    _log(
        "H1",
        "test_indexer_state.py:_load_edge_agent_app_modules",
        "imports loaded",
        {
            "app_main": str(app_main),
            "routes_module": str(routes_module),
            "security_module": str(security_module),
            "scan_rules_module": str(scan_rules_module),
        },
    )
    return app_main, routes_module, security_module, scan_rules_module


def test_indexer_state_transitions_isolated():
    indexer = _load_indexer_module()
    repo_a = "repo-a"
    repo_b = "repo-b"

    with indexer.acquire_indexing_lock(repo_a):
        assert indexer.is_indexing_in_progress(repo_a)
        assert not indexer.is_indexing_in_progress(repo_b)
    assert not indexer.is_indexing_in_progress(repo_a)

    indexer.mark_indexing_started(repo_b)
    assert indexer.is_indexing_in_progress(repo_b)
    indexer.mark_indexing_finished(repo_b)
    assert not indexer.is_indexing_in_progress(repo_b)

    indexer.mark_indexing_finished("unknown-repo")
    assert not indexer.is_indexing_in_progress("unknown-repo")


def test_indexing_lock_blocks_concurrent_access():
    indexer = _load_indexer_module()
    repo_id = "blocking-repo"
    lock_requested = threading.Event()
    lock_acquired = threading.Event()
    release_first = threading.Event()

    def first_owner():
        with indexer.acquire_indexing_lock(repo_id):
            lock_requested.set()
            release_first.wait(timeout=2)

    def second_owner():
        lock_requested.wait(timeout=1)
        with indexer.acquire_indexing_lock(repo_id):
            lock_acquired.set()

    first_thread = threading.Thread(target=first_owner, daemon=True)
    second_thread = threading.Thread(target=second_owner, daemon=True)

    first_thread.start()
    assert lock_requested.wait(timeout=1)

    second_thread.start()
    assert not lock_acquired.wait(timeout=0.1)

    release_first.set()
    first_thread.join(timeout=2)
    second_thread.join(timeout=2)

    assert lock_acquired.is_set()


def test_indexing_lock_released_on_exception():
    indexer = _load_indexer_module()
    repo_id = "exception-repo"

    with pytest.raises(RuntimeError):
        with indexer.acquire_indexing_lock(repo_id):
            raise RuntimeError("fail indexing")

    assert not indexer.is_indexing_in_progress(repo_id)
    with indexer.acquire_indexing_lock(repo_id):
        assert indexer.is_indexing_in_progress(repo_id)
    assert not indexer.is_indexing_in_progress(repo_id)


def test_indexing_locks_isolated_by_repo():
    indexer = _load_indexer_module()
    repo_a = "repo-a"
    repo_b = "repo-b"
    repo_b_acquired = threading.Event()
    repo_b_released = threading.Event()

    def run_repo_b():
        with indexer.acquire_indexing_lock(repo_b):
            repo_b_acquired.set()
            repo_b_released.wait(timeout=2)

    thread_b = threading.Thread(target=run_repo_b, daemon=True)
    with indexer.acquire_indexing_lock(repo_a):
        thread_b.start()
        assert repo_b_acquired.wait(timeout=1)
    repo_b_released.set()
    thread_b.join(timeout=2)


def test_index_route_blocks_when_repo_busy(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path))
    main_module, routes_module, security_module, scan_rules_module = _load_edge_agent_app_modules()
    indexer = _load_indexer_module()
    client = TestClient(main_module.app)

    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    normalized = scan_rules_module.normalize_root_path(str(repo_path))
    repo_id = scan_rules_module.compute_repo_id(normalized)
    
    lock_acquired = threading.Event()
    release_lock = threading.Event()

    def hold_repo_lock():
        with indexer.acquire_indexing_lock(repo_id):
            lock_acquired.set()
            release_lock.wait(timeout=2)

    holder_thread = threading.Thread(target=hold_repo_lock, daemon=True)
    holder_thread.start()
    assert lock_acquired.wait(timeout=2)

    response = client.post(
        "/index",
        json={"root_path": str(repo_path)},
        headers={security_module.TOKEN_HEADER: security_module.get_or_create_token()},
    )
    assert response.status_code == 409
    payload = response.json()
    assert payload["error_code"] == "INDEX_IN_PROGRESS"
    assert payload["message"] == "Indexing already in progress for this repo."
    assert payload["remediation"] == "Wait for the active indexing run to finish before retrying."

    release_lock.set()
    holder_thread.join(timeout=2)


def test_index_route_allows_distinct_repos(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path))
    main_module, routes_module, security_module, scan_rules_module = _load_edge_agent_app_modules()
    indexer = _load_indexer_module()
    client = TestClient(main_module.app)

    repo_a_path = tmp_path / "repo-a"
    repo_b_path = tmp_path / "repo-b"
    repo_a_path.mkdir()
    repo_b_path.mkdir()
    
    normalized_a = scan_rules_module.normalize_root_path(str(repo_a_path))
    repo_a_id = scan_rules_module.compute_repo_id(normalized_a)

    lock_acquired = threading.Event()
    release_lock = threading.Event()

    def hold_repo_lock():
        with indexer.acquire_indexing_lock(repo_a_id):
            lock_acquired.set()
            release_lock.wait(timeout=2)

    holder_thread = threading.Thread(target=hold_repo_lock, daemon=True)
    holder_thread.start()
    assert lock_acquired.wait(timeout=2)

    response = client.post(
        "/index",
        json={"root_path": str(repo_b_path)},
        headers={security_module.TOKEN_HEADER: security_module.get_or_create_token()},
    )
    assert response.status_code == 200

    release_lock.set()
    holder_thread.join(timeout=2)


def test_health_reflects_indexing_state(tmp_path, monkeypatch):
    monkeypatch.setenv("RAG_INDEX_DIR", str(tmp_path))
    main_module, routes_module, security_module, scan_rules_module = _load_edge_agent_app_modules()
    indexer = _load_indexer_module()
    
    # Reset state to ensure clean test
    indexer.reset_indexing_stats()
    
    client = TestClient(main_module.app)

    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    normalized = scan_rules_module.normalize_root_path(str(repo_path))
    repo_id = scan_rules_module.compute_repo_id(normalized)
    token = security_module.get_or_create_token()

    indexer.mark_indexing_started(repo_id)
    try:
        response = client.get(
            "/health",
            headers={security_module.TOKEN_HEADER: token},
        )
        assert response.status_code == 200
        assert response.json()["indexing"] is True
    finally:
        indexer.mark_indexing_finished(repo_id)

    response = client.get(
        "/health",
        headers={security_module.TOKEN_HEADER: token},
    )
    assert response.status_code == 200
    assert response.json()["indexing"] is False


def test_read_only_indexing_state_accessor():
    indexer = _load_indexer_module()
    repo_id = "read-only-repo"

    assert not indexer.is_indexing_in_progress(repo_id)

    indexer.mark_indexing_started(repo_id)
    assert indexer.is_indexing_in_progress(repo_id)

    indexer.mark_indexing_finished(repo_id)
    assert not indexer.is_indexing_in_progress(repo_id)
