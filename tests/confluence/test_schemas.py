"""Tests for app.api.schemas (Pydantic models)."""
import pytest
from pydantic import ValidationError

try:
    from app.api.schemas import (
        AnalyzeRequest,
        CreateRequest,
        FeedbackRequest,
        ConfidenceBreakdown,
        IntelligenceAnalysis,
        IntelligentRecommendation,
        AnalyzeResponse,
        IntelligenceConfidenceSummary,
        IntelligenceSummary,
        IntelligentPage,
        CreateResponse,
        IntelligenceMetrics,
        StatusResponse,
        FeedbackResponse,
        IntelligenceErrorResponse,
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "offline-folder-rag" / "edge_agent"))
    from app.api.schemas import (
        AnalyzeRequest,
        CreateRequest,
        FeedbackRequest,
        ConfidenceBreakdown,
        IntelligenceAnalysis,
        IntelligentRecommendation,
        AnalyzeResponse,
        IntelligenceConfidenceSummary,
        IntelligenceSummary,
        IntelligentPage,
        CreateResponse,
        IntelligenceMetrics,
        StatusResponse,
        FeedbackResponse,
        IntelligenceErrorResponse,
    )


def test_analyze_request_valid():
    r = AnalyzeRequest(files=["a.py"], context=None)
    assert r.files == ["a.py"]
    r2 = AnalyzeRequest(files=["x"], context="ctx")
    assert r2.context == "ctx"


def test_analyze_request_min_length():
    with pytest.raises(ValidationError):
        AnalyzeRequest(files=[], context=None)


def test_create_request_valid():
    r = CreateRequest(
        files=["a.py"],
        intelligent_mode=True,
        auto_title=False,
        space="DOC",
        intelligence_context={},
    )
    assert r.space == "DOC"


def test_feedback_request_valid():
    r = FeedbackRequest(creation_id="a" * 36, intelligence_score=3, feedback="ok")
    assert r.intelligence_score == 3


def test_feedback_request_score_bounds():
    with pytest.raises(ValidationError):
        FeedbackRequest(creation_id="x", intelligence_score=0, feedback="")
    with pytest.raises(ValidationError):
        FeedbackRequest(creation_id="x", intelligence_score=6, feedback="")


def test_confidence_breakdown():
    c = ConfidenceBreakdown(content_match=0.5, structure_match=0.5, context_match=0.5)
    assert c.content_match == 0.5


def test_intelligence_analysis():
    a = IntelligenceAnalysis(intelligence_confidence=0.8)
    assert a.intelligence_confidence == 0.8
    assert a.content_types == []
    assert a.ai_reasoning == ""


def test_intelligent_recommendation():
    cb = ConfidenceBreakdown(content_match=0.5, structure_match=0.5, context_match=0.5)
    r = IntelligentRecommendation(confidence_breakdown=cb)
    assert r.template_id == ""


def test_analyze_response():
    ia = IntelligenceAnalysis(intelligence_confidence=0.7)
    cb = ConfidenceBreakdown(content_match=0.5, structure_match=0.5, context_match=0.5)
    ir = IntelligentRecommendation(confidence_breakdown=cb)
    r = AnalyzeResponse(intelligence_analysis=ia, intelligent_recommendation=ir)
    assert r.intelligence_analysis.intelligence_confidence == 0.7


def test_intelligence_confidence_summary():
    s = IntelligenceConfidenceSummary(
        content_detection=0.5,
        template_intelligence=0.5,
        formatting_intelligence=0.5,
        overall_intelligence=0.5,
    )
    assert s.overall_intelligence == 0.5


def test_intelligence_summary():
    ics = IntelligenceConfidenceSummary(
        content_detection=0.5, template_intelligence=0.5,
        formatting_intelligence=0.5, overall_intelligence=0.5,
    )
    s = IntelligenceSummary(intelligence_confidence=ics)
    assert s.ai_learning_applied is False


def test_intelligent_page():
    p = IntelligentPage(url="https://x", id="1", title="T", space="DOC")
    assert p.intelligence_tag == "AI-Formatted"


def test_create_response():
    ics = IntelligenceConfidenceSummary(
        content_detection=0.5, template_intelligence=0.5,
        formatting_intelligence=0.5, overall_intelligence=0.5,
    )
    isum = IntelligenceSummary(intelligence_confidence=ics)
    ip = IntelligentPage()
    r = CreateResponse(success=True, intelligence_summary=isum, intelligent_page=ip)
    assert r.success is True


def test_intelligence_metrics():
    m = IntelligenceMetrics(
        template_selection_accuracy=0.8,
        user_acceptance_rate=0.9,
        learning_rate=0.7,
    )
    assert m.template_selection_accuracy == 0.8


def test_status_response():
    im = IntelligenceMetrics(
        template_selection_accuracy=0.8, user_acceptance_rate=0.9, learning_rate=0.7,
    )
    r = StatusResponse(intelligence_metrics=im, learning_progress={}, improvement_rates={})
    assert r.improvement_rates == {}


def test_feedback_response():
    im = IntelligenceMetrics(
        template_selection_accuracy=0.8, user_acceptance_rate=0.9, learning_rate=0.7,
    )
    sr = StatusResponse(intelligence_metrics=im)
    r = FeedbackResponse(message="ok", metrics_updated=True, learning_applied=True, updated_status=sr)
    assert r.learning_applied is True


def test_intelligence_error_response():
    r = IntelligenceErrorResponse(
        message="err",
        intelligence_suggestion="sugg",
        fallback_available=True,
        intelligence_confidence=0.0,
    )
    assert r.error == "intelligence_error"
