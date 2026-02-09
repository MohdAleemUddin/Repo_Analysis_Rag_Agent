"""Unit tests cover the hybrid retrieval helpers used by the /ask endpoint."""

from typing import Any

import pytest

from edge_agent.app.retrieval import ask


def _citation(file_path: str, line_start: int, line_end: int) -> dict[str, Any]:
    return {
        "file_path": file_path,
        "path": file_path,
        "line_start": line_start,
        "line_end": line_end,
        "snippet": f"snippet {file_path}:{line_start}",
    }


def test_merge_citations_deduplicates_and_limits():
    code_hits = [
        _citation("repo/a.py", 1, 1),
        _citation("repo/b.py", 2, 2),
    ]
    doc_hits = [
        _citation("repo/a.py", 1, 1),  # duplicate entry for repo/a.py
        _citation("repo/c.py", 3, 3),
    ]

    merged, truncated = ask.merge_citations(code_hits, doc_hits, max_chunks=2)
    assert truncated is True
    assert len(merged) == 2
    paths = {entry["path"] for entry in merged}
    assert paths == {"repo/a.py", "repo/b.py"}


def test_retrieve_vector_results_combines_sources(monkeypatch):
    code_hits = [
        _citation("repo/code1.py", 5, 7),
        _citation("repo/code2.py", 10, 12),
    ]
    doc_hits = [
        _citation("repo/doc1.md", 1, 1),
    ]
    rg_matches = [
        {"path": "repo/code2.py", "line_number": 10, "line_text": "code2 snippet"},
        {"path": "repo/extra.py", "line_number": 3, "line_text": "extra snippet"},
    ]
    seen: dict[str, Any] = {}

    def fake_query(_client, collection: str, query_text: str, top_k: int):
        assert query_text == "find"
        assert top_k == 3
        return code_hits if collection == ask.DEFAULT_CODE_COLLECTION else doc_hits

    def fake_execute(root: str, query: str, limit: int):
        seen["limit"] = limit
        seen["query"] = query
        seen["root"] = root
        return rg_matches

    monkeypatch.setattr(ask, "_build_client", lambda persist_directory=None: object())
    monkeypatch.setattr(ask, "_query_collection", fake_query)
    monkeypatch.setattr(ask, "execute_ask_query", fake_execute)

    result = ask.retrieve_vector_results(
        "find",
        top_k=3,
        search_root="/repo",
        ripgrep_limit=5,
        max_context_chunks=3,
    )

    assert seen["limit"] == 5
    assert seen["root"] == "/repo"
    assert isinstance(result["code"], list)
    assert isinstance(result["docs"], list)
    assert result["truncated"] is True
    citations = result["merged"]
    assert len(citations) == 3
    paths = {c["path"] for c in citations}
    # Because max_context_chunks=3 caps results, the first three unique citations
    # in input order are kept (code1, code2, doc1).
    assert paths == {"repo/code1.py", "repo/code2.py", "repo/doc1.md"}


def test_retrieve_vector_results_handles_empty_sources(monkeypatch):
    monkeypatch.setattr(ask, "_build_client", lambda persist_directory=None: object())
    monkeypatch.setattr(ask, "_query_collection", lambda *_: [])
    monkeypatch.setattr(ask, "execute_ask_query", lambda *_: [])

    result = ask.retrieve_vector_results("missing", top_k=1, search_root=None)

    assert result["merged"] == []
    assert result["truncated"] is False
    assert result["code"] == []
    assert result["docs"] == []
