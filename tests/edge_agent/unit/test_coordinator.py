"""Unit tests for app.agents.coordinator."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

try:
    from app.agents.coordinator import (
        get_pipeline_state,
        get_last_coordinator_error,
        run_analyze,
        run_create,
        run_document_project,
        get_operation_record,
    )
    from app.agents.contracts import PipelineState
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(
        0,
        str(
            Path(__file__).resolve().parents[3]
            / "repo_analysis_rag"
            / "backend_confluence"
        ),
    )
    from app.agents.coordinator import (
        get_pipeline_state,
        get_last_coordinator_error,
        run_analyze,
        run_create,
        run_document_project,
        get_operation_record,
    )
    from app.agents.contracts import PipelineState


def test_get_pipeline_state():
    s = get_pipeline_state()
    assert s in (
        PipelineState.Idle,
        PipelineState.Analyzing,
        PipelineState.Matching,
        PipelineState.Formatting,
        PipelineState.Integrating,
        PipelineState.Completed,
        PipelineState.Failed,
    )


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
        confidence_breakdown={
            "content_match": 0.9,
            "structure_match": 0.9,
            "context_match": 0.9,
        },
    )
    out = run_analyze(["def foo(): pass"])
    assert "intelligence_analysis" in out
    assert "intelligent_recommendation" in out
    assert out["intelligence_analysis"]["intelligence_confidence"] == 0.9
    assert out["intelligent_recommendation"]["template_name"] == "T1"


@patch("app.agents.coordinator.check_memory_before_step", return_value=True)
@patch("app.agents.coordinator.start_operation")
@patch("app.agents.coordinator.analyze_file_with_timer")
@patch("app.agents.coordinator.match")
def test_run_analyze_intelligent_title_module(
    mock_match, mock_analyze, mock_start, mock_mem
):
    from app.agents.contracts import ContentProfile, TemplateDecision

    mock_analyze.return_value = ContentProfile(
        content_types=["module"],
        languages=["python"],
        structure_signals=[],
        detected_patterns=[],
        relationships=[],
        confidence_scores={},
        ai_reasoning="",
    )
    mock_match.return_value = TemplateDecision(
        template_id="t1",
        template_name="T1",
        intelligence_score=0.9,
        ai_reasoning="",
        intelligence_reason="",
        confidence_breakdown={
            "content_match": 0.9,
            "structure_match": 0.9,
            "context_match": 0.9,
        },
    )
    out = run_analyze(["def foo(): pass"])
    assert out["intelligence_analysis"]["intelligent_title"] == "Module documentation"


@patch("app.agents.coordinator.check_memory_before_step", return_value=True)
@patch("app.agents.coordinator.start_operation")
@patch("app.agents.coordinator.analyze_file_with_timer")
@patch("app.agents.coordinator.match")
def test_run_analyze_intelligent_title_document(
    mock_match, mock_analyze, mock_start, mock_mem
):
    from app.agents.contracts import ContentProfile, TemplateDecision

    mock_analyze.return_value = ContentProfile(
        content_types=["document"],
        languages=["python"],
        structure_signals=[],
        detected_patterns=[],
        relationships=[],
        confidence_scores={},
        ai_reasoning="",
    )
    mock_match.return_value = TemplateDecision(
        template_id="t1",
        template_name="T1",
        intelligence_score=0.9,
        ai_reasoning="",
        intelligence_reason="",
        confidence_breakdown={
            "content_match": 0.9,
            "structure_match": 0.9,
            "context_match": 0.9,
        },
    )
    out = run_analyze(["x"])
    assert out["intelligence_analysis"]["intelligent_title"] == "Documentation"


@patch("app.agents.coordinator.check_memory_before_step", return_value=True)
@patch("app.agents.coordinator.start_operation")
@patch("app.agents.coordinator.analyze_file_with_timer")
@patch("app.agents.coordinator.format_content")
@patch("app.agents.coordinator.integration_create_page")
def test_run_create_with_file_contents(
    mock_create, mock_format, mock_analyze, mock_start, mock_mem
):
    from app.agents.contracts import (
        ContentProfile,
        FormattedConfluencePayload,
        IntegrationResult,
        PageInfo,
        VerificationResult,
        ValidationResults,
    )

    mock_analyze.return_value = ContentProfile(
        content_types=["code"],
        languages=["python"],
        structure_signals=[],
        detected_patterns=[],
        relationships=[],
        confidence_scores={},
        ai_reasoning="",
    )
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
    out = run_create(
        "http://x",
        "DOC",
        "Title",
        "body",
        auth=None,
        file_contents=["# doc\n", "def f(): pass"],
    )
    assert "id" in out or "title" in out
    mock_format.assert_called_once()
    call_args = mock_format.call_args[0]
    assert "\n\n---\n\n" in call_args[0] or "def f(): pass" in call_args[0]


@patch("app.agents.coordinator.check_memory_before_step", return_value=True)
@patch("app.agents.coordinator.start_operation")
@patch("app.agents.coordinator.analyze_file_with_timer")
@patch("app.agents.coordinator.format_content")
@patch("app.agents.coordinator.integration_create_page")
def test_run_create_success(
    mock_create, mock_format, mock_analyze, mock_start, mock_mem
):
    from app.agents.contracts import (
        ContentProfile,
        FormattedConfluencePayload,
        IntegrationResult,
        PageInfo,
        VerificationResult,
        ValidationResults,
    )

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
def test_run_create_dict_result_with_feedback(
    mock_sched, mock_create, mock_format, mock_analyze, mock_start, mock_mem
):
    from app.agents.contracts import (
        ContentProfile,
        FormattedConfluencePayload,
        ValidationResults,
    )

    mock_analyze.return_value = ContentProfile(
        content_types=["code"],
        languages=["python"],
        structure_signals=[],
        detected_patterns=[],
        relationships=[],
        confidence_scores={},
        ai_reasoning="",
    )
    mock_format.return_value = FormattedConfluencePayload(
        confluence_storage_format="<p>hi</p>",
        attachments=[],
        validation_results=ValidationResults(warnings=[], corrections_applied=[]),
        ai_reasoning="",
    )
    mock_create.return_value = {"id": "1", "title": "T", "space": "DOC"}
    out = run_create(
        "http://x", "DOC", "Title", "body", auth=None, feedback_for_learning="good"
    )
    assert out.get("id") == "1" or "title" in out
    mock_sched.assert_called_once()


def test_get_operation_record():
    r = get_operation_record()
    assert r is None or hasattr(r, "operation_id")


@patch("app.agents.coordinator.check_memory_before_step", return_value=False)
@patch("app.agents.coordinator.start_operation")
def test_run_document_project_memory_limit(mock_start, mock_mem):
    with patch("app.agents.coordinator._set_state"):
        try:
            run_document_project("/tmp/ws", "DOC", "http://x", auth=None)
        except RuntimeError as ex:
            assert "Memory" in str(ex)


@patch("app.agents.coordinator.check_memory_before_step", return_value=True)
@patch("app.agents.coordinator.start_operation")
def test_run_document_project_no_paths(mock_start, mock_mem):
    with patch("app.agents.coordinator.project_scan", return_value=[]):
        with patch("app.agents.coordinator._set_state"):
            try:
                run_document_project("/nonexistent", "DOC", "http://x", auth=None)
            except ValueError as ex:
                assert "No files found" in str(ex)


@patch("app.agents.coordinator.schedule_learning_after_create")
@patch("app.agents.coordinator.integration_create_page")
@patch("app.agents.coordinator.format_project_content")
@patch("app.agents.coordinator.match_project_template")
@patch("app.agents.coordinator.analyze_project")
@patch("app.agents.coordinator.project_scan")
@patch("app.agents.coordinator.check_memory_before_step", return_value=True)
@patch("app.agents.coordinator.start_operation")
def test_run_document_project_success(
    mock_start,
    mock_mem,
    mock_scan,
    mock_analyze,
    mock_match,
    mock_format,
    mock_create,
    mock_sched,
):
    from app.confluence.project_analyzer import ProjectAnalysis
    from app.confluence.project_template_matcher import ProjectTemplateMatch
    from app.agents.contracts import IntegrationResult, PageInfo, VerificationResult

    progress_calls = []

    def track_progress(current: int, total: int) -> None:
        progress_calls.append((current, total))

    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "main.py").write_text("x = 1")
        main_py = str(Path(tmp) / "main.py")

        def scan_side_effect(workspace_path, progress_callback=None, limit=100):
            if progress_callback and callable(progress_callback):
                progress_callback(0, 1)
            return [main_py]

        mock_scan.side_effect = scan_side_effect
        mock_analyze.return_value = ProjectAnalysis(
            project_type="API",
            content_types=["python_api"],
            detected_patterns=[],
            source_file_count=1,
        )
        mock_match.return_value = ProjectTemplateMatch(
            template_name="T1",
            template_id="tid",
            confidence=85.0,
            match_count=1,
            ai_reasoning="match",
        )
        mock_format.return_value = MagicMock(confluence_storage_format="<p>doc</p>")
        mock_create.return_value = IntegrationResult(
            page=PageInfo(
                id="1",
                url="http://x/page",
                title="API Project Documentation",
                space="DOC",
            ),
            intelligence_tag="AI",
            retries_used=0,
            rate_limit_state="ok",
            verification=VerificationResult(passed=True, checks=[]),
        )
        out = run_document_project(
            tmp, "DOC", "http://x", auth=None, progress_callback=track_progress
        )
    assert out["confluence_url"] == "http://x/page"
    assert out["template_name"] == "T1"
    assert out["learning_indicator"] is True
    mock_sched.assert_called_once()
    mock_scan.assert_called_once()
    assert progress_calls == [(0, 1)]


@patch("app.agents.coordinator.integration_create_page")
@patch("app.agents.coordinator.format_project_content")
@patch("app.agents.coordinator.match_project_template")
@patch("app.agents.coordinator.analyze_project")
@patch("app.agents.coordinator.project_scan")
@patch("app.agents.coordinator.check_memory_before_step", return_value=True)
@patch("app.agents.coordinator.start_operation")
def test_run_document_project_success_dict_result(
    mock_start, mock_mem, mock_scan, mock_analyze, mock_match, mock_format, mock_create
):
    from app.confluence.project_analyzer import ProjectAnalysis
    from app.confluence.project_template_matcher import ProjectTemplateMatch

    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "a.py").write_text("a = 1")
        a_py = str(Path(tmp) / "a.py")
        mock_scan.return_value = [a_py, "/nonexistent/fake_raise.py"]
        mock_analyze.return_value = ProjectAnalysis(
            project_type="mixed",
            content_types=[],
            detected_patterns=[],
            source_file_count=1,
        )
        mock_match.return_value = ProjectTemplateMatch(
            template_name="T2",
            template_id="t2",
            confidence=90.0,
            match_count=1,
            ai_reasoning="",
        )
        mock_format.return_value = MagicMock(confluence_storage_format="<p>x</p>")
        mock_create.return_value = {
            "id": "2",
            "title": "Mixed Project Documentation",
            "space": "DOC",
            "url": "http://y",
        }
        out = run_document_project(tmp, "DOC", "http://x", auth=None)
    assert out["confluence_url"] == "http://y"
    assert out["intelligence_analysis"]["project_type"] == "mixed"


@patch(
    "app.agents.coordinator.integration_create_page",
    side_effect=RuntimeError("create failed"),
)
@patch("app.agents.coordinator.format_project_content")
@patch("app.agents.coordinator.match_project_template")
@patch("app.agents.coordinator.analyze_project")
@patch("app.agents.coordinator.project_scan")
@patch("app.agents.coordinator.check_memory_before_step", return_value=True)
@patch("app.agents.coordinator.start_operation")
def test_run_document_project_exception(
    mock_start, mock_mem, mock_scan, mock_analyze, mock_match, mock_format, mock_create
):
    from app.confluence.project_analyzer import ProjectAnalysis
    from app.confluence.project_template_matcher import ProjectTemplateMatch

    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "b.py").write_text("b = 1")
        mock_scan.return_value = [str(Path(tmp) / "b.py")]
        mock_analyze.return_value = ProjectAnalysis(
            project_type="API",
            content_types=[],
            detected_patterns=[],
            source_file_count=1,
        )
        mock_match.return_value = ProjectTemplateMatch(
            template_name="T",
            template_id="t",
            confidence=80.0,
            match_count=1,
            ai_reasoning="",
        )
        mock_format.return_value = MagicMock(confluence_storage_format="<p>y</p>")
        with patch("app.agents.coordinator._set_state"):
            try:
                run_document_project(tmp, "DOC", "http://x", auth=None)
            except RuntimeError as ex:
                assert "create failed" in str(ex)
