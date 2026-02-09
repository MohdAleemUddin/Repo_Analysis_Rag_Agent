from edge_agent.app.indexing.chunking import chunker


def test_fallback_classification_routes_to_line_chunker(monkeypatch):
    calls = {"markdown": 0, "code": 0, "line": 0}

    def markdown_chunk_stub(*args, **kwargs):
        calls["markdown"] += 1
        raise AssertionError("Markdown chunker must not run for fallback files.")

    def code_chunk_stub(*args, **kwargs):
        calls["code"] += 1
        raise AssertionError("Code chunker must not run for fallback files.")

    def line_chunk_stub(file_path, **kwargs):
        calls["line"] += 1
        return [
            {
                "path": "notes/todo.txt",
                "chunk_id": "c1",
                "line_start": 1,
                "line_end": 3,
                "line_count": 3,
                "file_type": "other",
                "mtime_epoch_ms": 3,
                "sha256": "ghi",
                "truncated": False,
            }
        ]

    monkeypatch.setattr(chunker, "markdown_chunk", markdown_chunk_stub)
    monkeypatch.setattr(chunker, "code_chunk", code_chunk_stub)
    monkeypatch.setattr(chunker, "line_chunk", line_chunk_stub)

    result = chunker.chunk_file("notes/todo.txt", file_type="text")

    assert calls["line"] == 1
    assert calls["markdown"] == 0
    assert calls["code"] == 0
    assert result[0]["path"] == "notes/todo.txt"
