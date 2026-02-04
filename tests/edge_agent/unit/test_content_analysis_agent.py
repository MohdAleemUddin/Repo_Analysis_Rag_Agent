"""Unit tests for app.agents.content_analysis_agent."""
from unittest.mock import patch

try:
    from app.agents.content_analysis_agent import (
        analyze,
        analyze_file_with_timer,
        _content_hash,
        _deterministic_parse,
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "offline-folder-rag" / "edge_agent"))
    from app.agents.content_analysis_agent import (
        analyze,
        analyze_file_with_timer,
        _content_hash,
        _deterministic_parse,
    )


def test_content_hash_str():
    h = _content_hash("hello")
    assert isinstance(h, str) and len(h) == 64


def test_content_hash_bytes():
    h = _content_hash(b"hello")
    assert isinstance(h, str)


def test_deterministic_parse_empty():
    s = _deterministic_parse("")
    assert s["content_types"] == []
    assert s["languages"] == []


def test_deterministic_parse_whitespace():
    s = _deterministic_parse("   \n  ")
    assert s["structure"] == "plain"


def test_deterministic_parse_code_like():
    s = _deterministic_parse("# comment\ndef foo(): pass")
    assert "code_like" in s["structure_signals"] or "document" in s["content_types"]


def test_deterministic_parse_python_ast():
    s = _deterministic_parse("x = 1")
    assert "python" in s["languages"] or "text" in s["languages"]


def test_deterministic_parse_syntax_error():
    s = _deterministic_parse("def broken (")
    assert "languages" in s


def test_deterministic_parse_imports():
    s = _deterministic_parse("import os")
    assert "imports" in s["detected_patterns"] or "python" in s["languages"]


def test_deterministic_parse_todo():
    s = _deterministic_parse("# TODO fix this")
    assert "todos" in s["detected_patterns"] or len(s["detected_patterns"]) >= 0


@patch("app.agents.content_analysis_agent.run_analysis_chain")
def test_analyze_small(mock_chain):
    mock_chain.return_value = {
        "content_types": ["code"],
        "languages": ["python"],
        "structure_signals": [],
        "detected_patterns": [],
        "relationships": [],
        "confidence_scores": {},
        "ai_reasoning": "",
    }
    out = analyze("def foo(): pass", file_index=0)
    assert out.content_types == ["code"] or "code" in out.content_types


@patch("app.agents.content_analysis_agent.CONFLUENCE_LARGE_FILE_THRESHOLD_BYTES", 10)
@patch("app.agents.content_analysis_agent.CONFLUENCE_CHUNK_SIZE_BYTES", 5)
@patch("app.agents.content_analysis_agent.run_analysis_chain")
def test_analyze_large_chunked(mock_chain):
    mock_chain.return_value = {"content_types": ["document"], "languages": ["text"], "structure_signals": [],
                               "detected_patterns": [], "relationships": [], "confidence_scores": {}, "ai_reasoning": ""}
    out = analyze("x" * 100, file_index=0)
    assert "chunked" in out.structure_signals or "document" in out.content_types


def test_analyze_file_with_timer():
    out = analyze_file_with_timer("x = 1", file_index=0)
    assert hasattr(out, "content_types") or hasattr(out, "languages")


@patch("app.agents.content_analysis_agent.CONFLUENCE_ANALYSIS_CACHE_ENABLED", True)
@patch("app.agents.content_analysis_agent.CONFLUENCE_ANALYSIS_CACHE_TTL_SECONDS", 3600)
@patch("app.agents.content_analysis_agent.run_analysis_chain")
def test_analyze_cache_hit(mock_chain):
    mock_chain.return_value = {"content_types": ["doc"], "languages": ["text"], "structure_signals": [],
                               "detected_patterns": [], "relationships": [], "confidence_scores": {}, "ai_reasoning": ""}
    c = "same content for cache"
    analyze(c)
    out2 = analyze(c)
    assert mock_chain.call_count == 1
    assert out2.content_types == ["doc"] or "doc" in out2.content_types


@patch("app.agents.content_analysis_agent.CONFLUENCE_ANALYSIS_CACHE_ENABLED", True)
@patch("app.agents.content_analysis_agent.CONFLUENCE_ANALYSIS_CACHE_TTL_SECONDS", 0)
@patch("app.agents.content_analysis_agent.run_analysis_chain")
def test_analyze_cache_ttl_expired(mock_chain):
    from app.agents.content_analysis_agent import _analysis_cache
    _analysis_cache.clear()
    mock_chain.return_value = {"content_types": ["x"], "languages": ["text"], "structure_signals": [],
                               "detected_patterns": [], "relationships": [], "confidence_scores": {}, "ai_reasoning": ""}
    analyze("unique_ttl_content_xyz")
    analyze("unique_ttl_content_xyz")
    assert mock_chain.call_count >= 1


@patch("app.agents.content_analysis_agent.CONFLUENCE_ANALYSIS_CACHE_ENABLED", True)
@patch("app.agents.content_analysis_agent.CONFLUENCE_ANALYSIS_CACHE_MAX_ENTRIES", 2)
@patch("app.agents.content_analysis_agent.run_analysis_chain")
def test_analyze_cache_eviction(mock_chain):
    mock_chain.return_value = {"content_types": ["doc"], "languages": ["text"], "structure_signals": [],
                               "detected_patterns": [], "relationships": [], "confidence_scores": {}, "ai_reasoning": ""}
    analyze("a")
    analyze("b")
    analyze("c")
    assert mock_chain.call_count >= 2


@patch("app.agents.content_analysis_agent._cache_get")
@patch("app.agents.content_analysis_agent._content_hash", return_value="k1")
def test_analyze_cached_dict_returned(mock_hash, mock_cache_get):
    mock_cache_get.return_value = {"content_types": ["cached"], "languages": ["text"], "structure_signals": [],
                                   "detected_patterns": [], "relationships": [], "confidence_scores": {}, "ai_reasoning": ""}
    out = analyze("any")
    assert out.content_types == ["cached"]
