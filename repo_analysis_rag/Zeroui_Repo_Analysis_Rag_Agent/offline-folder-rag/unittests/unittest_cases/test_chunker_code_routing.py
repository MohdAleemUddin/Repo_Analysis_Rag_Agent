from edge_agent.app.indexing.chunking import chunker


def test_code_classification_routes_to_code_chunker(monkeypatch):
    calls = {"markdown": 0, "code": 0, "line": 0}

    def markdown_chunk_stub(*args, **kwargs):
        calls["markdown"] += 1
        raise AssertionError("Markdown chunker must not run for code files.")

    def code_chunk_stub(file_path, **kwargs):
        calls["code"] += 1
        return [
            {
                "path": "src/app.py",
                "chunk_id": "c1",
                "line_start": 1,
                "line_end": 10,
                "line_count": 10,
                "file_type": "code",
                "mtime_epoch_ms": 2,
                "sha256": "def",
                "truncated": False,
            }
        ]

    def line_chunk_stub(*args, **kwargs):
        calls["line"] += 1
        raise AssertionError("Line chunker must not run for code files.")

    monkeypatch.setattr(chunker, "markdown_chunk", markdown_chunk_stub)
    monkeypatch.setattr(chunker, "code_chunk", code_chunk_stub)
    monkeypatch.setattr(chunker, "line_chunk", line_chunk_stub)

    result = chunker.chunk_file("src/app.py", file_type="code")

    assert calls["code"] == 1
    assert calls["markdown"] == 0
    assert calls["line"] == 0
    assert result[0]["file_type"] == "code"
