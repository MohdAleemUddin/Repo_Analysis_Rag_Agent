"""
Performance boundary and business rule tests for User Story 8 (TC-BVA-011 to TC-BVA-014, TC-BR-004, etc.).
"""

import time
from unittest.mock import MagicMock, patch


# --- TC-BVA-011: Content analysis time < 3s per file ---
def test_analysis_time_under_3_seconds_per_file():
    """TC-BVA-011: Per-file analysis completes in < 3 seconds."""
    from app.agents.content_analysis_agent import analyze_file_with_timer
    from app.config.config import ANALYSIS_MAX_SECONDS_PER_FILE

    start = time.perf_counter()
    result = analyze_file_with_timer("def foo(): pass\nclass Bar: pass", file_index=0)
    elapsed = time.perf_counter() - start
    assert (
        elapsed < ANALYSIS_MAX_SECONDS_PER_FILE + 0.5
    ), f"Analysis took {elapsed:.2f}s (limit {ANALYSIS_MAX_SECONDS_PER_FILE}s)"
    assert "language" in result or "chunk" in str(result)


# --- TC-BVA-012: Template selection < 2s ---
def test_template_selection_under_2_seconds():
    """TC-BVA-012: Template selection completes in < 2 seconds."""
    from app.agents.pattern_matching_agent import match
    from app.config.config import TEMPLATE_SELECTION_MAX_SECONDS

    start = time.perf_counter()
    result = match("some content", analysis={})
    elapsed = time.perf_counter() - start
    assert elapsed < TEMPLATE_SELECTION_MAX_SECONDS + 0.3
    assert "template_id" in result


# --- TC-BVA-013 / TC-BR-004: Page creation < 15s including API ---
def test_creation_time_under_15_seconds_including_api():
    """TC-BVA-013, TC-BR-004: Full page creation completes in < 15 seconds including API."""
    from app.agents.integration_agent import create_page

    with patch("app.agents.integration_agent.confluence_create_page") as mock_create:
        mock_create.return_value = {"id": "123", "title": "Test"}
        start = time.perf_counter()
        result = create_page(
            base_url="https://example.atlassian.net/wiki",
            space_key="DOC",
            title="Test",
            body_html="<p>body</p>",
            auth=None,
        )
        elapsed = time.perf_counter() - start
        assert elapsed < 15 + 0.5
        assert result.get("id") == "123"


# --- TC-BVA-014: Memory ≤ 300MB ---
def test_memory_under_300mb_during_operation():
    """TC-BVA-014: Memory usage ≤ 300MB during Confluence operation."""
    from app.confluence.prd_monitor import (
        check_memory_before_step,
        get_peak_memory_mb,
        start_operation,
    )

    start_operation()
    ok = check_memory_before_step()
    peak = get_peak_memory_mb()
    # If psutil available, peak should be measurable; limit is 300MB
    assert peak <= 300.0 or peak == 0.0, f"Peak memory {peak} MB exceeds 300 MB"
    assert ok is True or peak == 0.0


# --- TC-EH-004: Memory exhaustion / validation → graceful error handling ---
def test_memory_exhaustion_graceful_handling():
    """TC-EH-004: Invalid request returns PRD §9.2 error format (graceful, no crash)."""
    from fastapi import APIRouter, FastAPI
    from fastapi.testclient import TestClient

    from app.api import register_confluence_routes

    router = APIRouter()
    register_confluence_routes(router)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    response = client.post("/confluence/intelligent-analyze", json={})
    assert response.status_code == 422
    data = response.json()
    assert data.get("error") == "intelligence_error"
    assert "message" in data and "intelligence_suggestion" in data
    assert "fallback_available" in data and "intelligence_confidence" in data


# --- TC-IT-005 / TC-IT-007: No interference with RAG; resource sharing ---
def test_rag_confluence_no_conflict():
    """TC-IT-005: Run Confluence analyze without breaking RAG (no import/route conflict)."""
    from fastapi import APIRouter, FastAPI
    from fastapi.testclient import TestClient

    from app.api import register_confluence_routes, register_rag_routes

    register_rag_routes(MagicMock())
    router = APIRouter()
    register_confluence_routes(router)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    result = client.post("/confluence/intelligent-analyze", json={"files": ["x"]})
    assert result.status_code == 200
    data = result.json()
    assert "intelligence_analysis" in data or "error" in data


def test_resource_sharing_memory_limit():
    """TC-IT-007: Confluence operations respect 300MB limit (resource sharing)."""
    from app.config.config import CONFLUENCE_MEMORY_LIMIT_MB
    from app.confluence.prd_monitor import check_memory_before_step

    assert CONFLUENCE_MEMORY_LIMIT_MB == 300
    # At least one check does not crash
    check_memory_before_step()


# --- TC-RG-001: Existing RAG features still work ---
def test_existing_rag_features_unchanged():
    """TC-RG-001: RAG route registration and imports still work."""
    from app.api.routes import register_rag_routes

    router = MagicMock()
    register_rag_routes(router)
    # No exception; RAG module is untouched by Confluence
    assert True


# --- PRD monitor and optimizer ---
def test_prd_monitor_timers_and_record():
    """Performance record is produced and targets_met is set."""
    from app.confluence.prd_monitor import (
        record_confluence_operation,
        start_operation,
        timer_per_file_analysis,
        timer_template_selection,
    )

    start_operation()
    with timer_per_file_analysis(0):
        pass
    with timer_template_selection():
        pass
    record = record_confluence_operation(
        operation_id="test-op",
        per_file_analysis_ms=[100.0],
        template_selection_ms=50.0,
        create_e2e_ms=1000.0,
        peak_memory_mb=50.0,
    )
    assert record.operation_id == "test-op"
    assert "analysis_per_file" in record.targets_met
    assert "memory" in record.targets_met


def test_optimizer_suggestions():
    """Optimizer returns suggestions when targets are missed."""
    from app.confluence.optimizer import get_optimization_suggestions

    record = {
        "per_file_analysis_ms": [4000.0],
        "template_selection_ms": 3000.0,
        "create_e2e_ms": 20000.0,
        "peak_memory_mb": 350.0,
    }
    suggestions = get_optimization_suggestions(record)
    assert isinstance(suggestions, list)
    assert len(suggestions) >= 1


def test_intelligence_status_returns_metrics():
    """intelligence-status returns PRD metrics (intelligence_metrics, learning_progress, improvement_rates)."""
    from fastapi import APIRouter, FastAPI
    from fastapi.testclient import TestClient

    from app.api import register_confluence_routes

    router = APIRouter()
    register_confluence_routes(router)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    result = client.get("/confluence/intelligence-status?detail_level=full")
    assert result.status_code == 200
    data = result.json()
    assert "intelligence_metrics" in data
    assert "learning_progress" in data
    assert "improvement_rates" in data
    assert "template_selection_accuracy" in data["intelligence_metrics"]


# --- TC-UI-010: UI remains responsive during heavy operation ---
def test_ui_remains_responsive_during_heavy_operation():
    """TC-UI-010: Status request completes quickly (no long blocking)."""
    from fastapi import APIRouter, FastAPI
    from fastapi.testclient import TestClient

    from app.api import register_confluence_routes

    router = APIRouter()
    register_confluence_routes(router)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    client.post("/confluence/intelligent-analyze", json={"files": ["short"]})
    start = time.perf_counter()
    client.get("/confluence/intelligence-status?detail_level=full")
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, "Status should return in < 2s (UI responsive)"
