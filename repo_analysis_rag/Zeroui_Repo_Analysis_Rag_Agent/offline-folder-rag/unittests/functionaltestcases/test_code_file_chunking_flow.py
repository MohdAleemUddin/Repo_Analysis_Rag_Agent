from edge_agent.app.indexing.chunking import chunker


def test_functional_code_chunking_flow(monkeypatch):
    calls = {"markdown": 0, "code": 0, "line": 0}

    def markdown_chunk_stub(*args, **kwargs):
        calls["markdown"] += 1
        raise AssertionError("Markdown chunker should not run for code files.")

    def code_chunk_stub(file_path, **kwargs):
        calls["code"] += 1
        return [
            {
                "path": "src/service.js",
                "chunk_id": "c1",
                "line_start": 1,
                "line_end": 6,
                "line_count": 6,
                "file_type": "code",
                "mtime_epoch_ms": 6,
                "sha256": "pqr",
                "truncated": False,
            }
        ]

    def line_chunk_stub(*args, **kwargs):
        calls["line"] += 1
        raise AssertionError("Line chunker should not run for code files.")

    monkeypatch.setattr(chunker, "markdown_chunk", markdown_chunk_stub)
    monkeypatch.setattr(chunker, "code_chunk", code_chunk_stub)
    monkeypatch.setattr(chunker, "line_chunk", line_chunk_stub)

    result = chunker.chunk_file("src/service.js", file_type="code")

    assert calls["code"] == 1
    assert calls["markdown"] == 0
    assert calls["line"] == 0
    assert result[0]["file_type"] == "code"
