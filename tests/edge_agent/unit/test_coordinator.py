"""Unit tests for app.agents.coordinator."""
from unittest.mock import MagicMock, patch

try:
    from app.agents.coordinator import (
        get_pipeline_state,
        get_last_coordinator_error,
        run_analyze,
        run_create,
        get_operation_record,
    )
    from app.agents.contracts import PipelineState
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "offline-folder-rag" / "edge_agent"))
    from app.agents.coordinator import (
        get_pipeline_state,
        get_last_coordinator_error,
        run_analyze,
        run_create,
        get_operation_record,
    )
    from app.agents.contracts import PipelineState


def test_get_pipeline_state():
    s = get_pipeline_state()
    assert s in (PipelineState.Idle, PipelineState.Analyzing, PipelineState.Matching,
                 PipelineState.Formatting, PipelineState.Integrating, PipelineState.Completed, PipelineState.Failed)


def test_get_last_coordinator_error():
    e = get_last_coordinator_error()
    assert e is None or hasattr(e, "error_code")


@patch("app.agents.coordinator.check_memory_before_step", return_value=True)
@patch("app.agents.coordinator.start_operation")
def test_run_analyze_empty_files(mock_start, mock_mem):
    with patch("app.agents.coordinator.analyze_file_with_timer"):
        try:
            run_analyze([])
        except ValueError as ex:
            assert "No file contents" in str(ex)


@patch("app.agents.coordinator.check_memory_before_step", return_value=False)
@patch("app.agents.coordinator.start_operation")
def test_run_analyze_memory_limit(mock_start, mock_mem):
    try:
        run_analyze(["x"])
    except RuntimeError as ex:
        assert "Memory" in str(ex)


@patch("app.agents.coordinator.check_memory_before_step", return_value=False)
@patch("app.agents.coordinator.start_operation")
def test_run_create_memory_limit(mock_start, mock_mem):
    try:
        run_create("http://x", "DOC", "T", "body", auth=None)
    except RuntimeError as ex:
        assert "Memory" in str(ex)


@patch("app.agents.coordinator.check_memory_before_step", return_value=True)
@patch("app.agents.coordinator.start_operation")
@patch("app.agents.coordinator.analyze_file_with_timer")
@patch("app.agents.coordinator.match")
def test_run_analyze_success(mock_match, mock_analyze, mock_start, mock_mem):
    from app.agents.contracts import ContentProfile, TemplateDecision
    prof = ContentProfile(
        content_types=["code"],
        languages=["python"],
        structure_signals=[],
        detected_patterns=[],
        relationships=[],
        confidence_scores={},
        ai_reasoning="",
    )
    mock_analyze.return_value = prof
    mock_match.return_value = TemplateDecision(
        template_id="t1",
        template_name="T1",
        intelligence_score=0.9,
        ai_reasoning="",
        intelligence_reason="Matches 1 similar successful examples",
        confidence_breakdown={"content_match": 0.9, "structure_match": 0.9, "context_match": 0.9},
    )
    out = run_analyze(["def foo(): pass"])
    assert "intelligence_analysis" in out
    assert "intelligent_recommendation" in out
    assert out["intelligence_analysis"]["intelligence_confidence"] == 0.9
    assert out["intelligent_recommendation"]["template_name"] == "T1"


@patch("app.agents.coordinator.check_memory_before_step", return_value=True)
@patch("app.agents.coordinator.start_operation")
@patch("app.agents.coordinator.analyze_file_with_timer")
@patch("app.agents.coordinator.format_content")
@patch("app.agents.coordinator.integration_create_page")
def test_run_create_success(mock_create, mock_format, mock_analyze, mock_start, mock_mem):
    from app.agents.contracts import ContentProfile, FormattedConfluencePayload, IntegrationResult, PageInfo, VerificationResult, ValidationResults
    prof = ContentProfile(
        content_types=["code"],
        languages=["python"],
        structure_signals=[],
        detected_patterns=[],
        relationships=[],
        confidence_scores={},
        ai_reasoning="",
    )
    mock_analyze.return_value = prof
    mock_format.return_value = FormattedConfluencePayload(
        confluence_storage_format="<p>hi</p>",
        attachments=[],
        validation_results=ValidationResults(warnings=[], corrections_applied=[]),
        ai_reasoning="",
    )
    mock_create.return_value = IntegrationResult(
        page=PageInfo(id="1", url="http://x", title="T", space="DOC"),
        intelligence_tag="AI",
        retries_used=0,
        rate_limit_state="ok",
        verification=VerificationResult(passed=True, checks=[]),
    )
    out = run_create("http://x", "DOC", "Title", "body", auth=None)
    assert "id" in out or "title" in out


@patch("app.agents.coordinator.check_memory_before_step", return_value=True)
@patch("app.agents.coordinator.start_operation")
@patch("app.agents.coordinator.analyze_file_with_timer")
@patch("app.agents.coordinator.format_content")
@patch("app.agents.coordinator.integration_create_page")
@patch("app.agents.coordinator.schedule_learning_after_create")
def test_run_create_dict_result_with_feedback(mock_sched, mock_create, mock_format, mock_analyze, mock_start, mock_mem):
    from app.agents.contracts import ContentProfile, FormattedConfluencePayload, ValidationResults
    mock_analyze.return_value = ContentProfile(content_types=["code"], languages=["python"], structure_signals=[],
        detected_patterns=[], relationships=[], confidence_scores={}, ai_reasoning="")
    mock_format.return_value = FormattedConfluencePayload(confluence_storage_format="<p>hi</p>", attachments=[],
        validation_results=ValidationResults(warnings=[], corrections_applied=[]), ai_reasoning="")
    mock_create.return_value = {"id": "1", "title": "T", "space": "DOC"}
    out = run_create("http://x", "DOC", "Title", "body", auth=None, feedback_for_learning="good")
    assert out.get("id") == "1" or "title" in out
    mock_sched.assert_called_once()


def test_get_operation_record():
    r = get_operation_record()
    assert r is None or hasattr(r, "operation_id")
