from edge_agent.app.indexing.chunking import chunker


def test_markdown_classification_routes_to_markdown_chunker(monkeypatch):
    calls = {"markdown": 0, "code": 0, "line": 0}

    def markdown_chunk_stub(file_path, **kwargs):
        calls["markdown"] += 1
        return [
            {
                "path": "docs/readme.md",
                "chunk_id": "c1",
                "line_start": 1,
                "line_end": 5,
                "line_count": 5,
                "file_type": "markdown",
                "mtime_epoch_ms": 1,
                "sha256": "abc",
                "truncated": False,
            }
        ]

    def code_chunk_stub(*args, **kwargs):
        calls["code"] += 1
        raise AssertionError("Code chunker must not run for markdown files.")

    def line_chunk_stub(*args, **kwargs):
        calls["line"] += 1
        raise AssertionError("Line chunker must not run for markdown files.")

    monkeypatch.setattr(chunker, "markdown_chunk", markdown_chunk_stub)
    monkeypatch.setattr(chunker, "code_chunk", code_chunk_stub)
    monkeypatch.setattr(chunker, "line_chunk", line_chunk_stub)

    result = chunker.chunk_file("docs/readme.md", file_type="code")

    assert calls["markdown"] == 1
    assert calls["code"] == 0
    assert calls["line"] == 0
    assert result[0]["path"] == "docs/readme.md"
