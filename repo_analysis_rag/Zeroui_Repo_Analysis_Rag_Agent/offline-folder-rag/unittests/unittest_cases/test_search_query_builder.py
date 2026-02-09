"""Unit tests for the deterministic search query builder."""

from edge_agent.app.retrieval.ask import merge_citations
from edge_agent.app.tools.search import build_ask_patterns, build_search_query


def test_quoted_input_returns_only_exact_literal():
    result = build_search_query('"Find the exact phrase"')
    assert result == {"exact_literal": "Find the exact phrase"}


def test_unquoted_input_filters_stopwords_and_limits_tokens():
    query = "The quick brown fox jumps over the lazy dog"
    result = build_search_query(query)

    assert "exact_literal" not in result
    assert result["tokens"] == ["quick", "brown", "fox", "jumps", "lazy"]


def test_builder_never_populates_both_modes():
    candidates = ['"literal match"', "unquoted query", ""]
    for candidate in candidates:
        result = build_search_query(candidate)
        assert ("exact_literal" in result) != ("tokens" in result)


def test_build_ask_patterns_includes_phrase_and_tokens():
    patterns = build_ask_patterns("How to install FastAPI")
    assert "How to install FastAPI" in patterns
    assert "how" in patterns
    assert "install" in patterns
    assert "fastapi" in patterns


def test_build_ask_patterns_is_case_insensitive():
    patterns = build_ask_patterns("FASTAPI SERVICE")
    assert "fastapi" in patterns
    assert "service" in patterns


def test_build_ask_patterns_handles_empty_input():
    assert build_ask_patterns("") == []


def test_build_ask_patterns_normalizes_whitespace():
    patterns = build_ask_patterns("  spaced    phrase  ")
    assert "spaced phrase" in patterns


def test_merge_citations_deduplicates_by_path_and_range():
    vector_hits = [
        {
            "file_path": "repo/file.py",
            "line_number": 10,
            "line_start": 10,
            "line_end": 12,
            "snippet": "def foo():",
        }
    ]
    rg_hits = [
        {
            "file_path": "repo/file.py",
            "line_number": 10,
            "line_start": 10,
            "line_end": 12,
            "snippet": "def foo():  # from rg",
        },
        {
            "file_path": "repo/other.py",
            "line_number": 5,
            "line_start": 5,
            "line_end": 5,
            "snippet": "other snippet",
        },
    ]

    merged, truncated = merge_citations(vector_hits, rg_hits)
    assert len(merged) == 2
    assert merged[0]["snippet"] == "def foo():"
    assert merged[1]["file_path"] == "repo/other.py"
    assert truncated is False


def test_merge_citations_preserves_unique_entries():
    vector_hits = [
        {"file_path": "a.py", "line_number": 1, "line_start": 1, "line_end": 1, "snippet": "A"},
    ]
    rg_hits = [
        {"file_path": "a.py", "line_number": 2, "line_start": 2, "line_end": 2, "snippet": "B"},
    ]
    merged, truncated = merge_citations(vector_hits, rg_hits)
    assert len(merged) == 2
    assert truncated is False
