from edge_agent.app.indexing.chunking import chunker


def test_functional_fallback_chunking_flow(monkeypatch):
    calls = {"markdown": 0, "code": 0, "line": 0}

    def markdown_chunk_stub(*args, **kwargs):
        calls["markdown"] += 1
        raise AssertionError("Markdown chunker should not run for fallback files.")

    def code_chunk_stub(*args, **kwargs):
        calls["code"] += 1
        raise AssertionError("Code chunker should not run for fallback files.")

    def line_chunk_stub(file_path, **kwargs):
        calls["line"] += 1
        return [
            {
                "path": "notes/notes.txt",
                "chunk_id": "c1",
                "line_start": 1,
                "line_end": 3,
                "line_count": 3,
                "file_type": "other",
                "mtime_epoch_ms": 7,
                "sha256": "stu",
                "truncated": False,
            }
        ]

    monkeypatch.setattr(chunker, "markdown_chunk", markdown_chunk_stub)
    monkeypatch.setattr(chunker, "code_chunk", code_chunk_stub)
    monkeypatch.setattr(chunker, "line_chunk", line_chunk_stub)

    result = chunker.chunk_file("notes/notes.txt", file_type="text")

    assert calls["line"] == 1
    assert calls["markdown"] == 0
    assert calls["code"] == 0
    assert result[0]["file_type"] == "other"
