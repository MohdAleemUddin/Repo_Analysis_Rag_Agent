"""Unit tests for app.agents.pattern_matching_agent."""
from unittest.mock import patch

try:
    from app.agents.pattern_matching_agent import match, FALLBACK_TEMPLATE_ID, MIN_SCORE_THRESHOLD
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "offline-folder-rag" / "edge_agent"))
    from app.agents.pattern_matching_agent import match, FALLBACK_TEMPLATE_ID, MIN_SCORE_THRESHOLD


@patch("app.agents.pattern_matching_agent.run_matching")
def test_match_normal(mock_run):
    mock_run.return_value = {
        "template_id": "t1",
        "template_name": "T1",
        "intelligence_score": 0.9,
        "confidence_breakdown": {"content_match": 0.9, "structure_match": 0.9, "context_match": 0.9},
        "ai_reasoning": "match",
    }
    out = match("content", analysis=None)
    assert out.template_id == "t1"
    assert out.intelligence_score == 0.9


@patch("app.agents.pattern_matching_agent.run_matching")
def test_match_low_score_fallback(mock_run):
    mock_run.return_value = {
        "template_id": "x",
        "template_name": "X",
        "intelligence_score": 0.1,
        "confidence_breakdown": {},
        "ai_reasoning": "",
    }
    out = match("content", analysis=None)
    assert out.template_id == FALLBACK_TEMPLATE_ID
    assert out.intelligence_score == 0.5
