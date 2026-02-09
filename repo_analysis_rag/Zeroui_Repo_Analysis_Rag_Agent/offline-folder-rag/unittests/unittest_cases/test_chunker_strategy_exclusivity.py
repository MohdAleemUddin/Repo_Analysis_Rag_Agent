from edge_agent.app.indexing.chunking import chunker


def test_strategy_exclusivity_per_classification(monkeypatch):
    calls = {"md": 0, "code": 0, "line": 0}

    def md_stub(*args, **kwargs):
        calls["md"] += 1
        return [
            {
                "path": "docs/readme.md",
                "chunk_id": "m1",
                "line_start": 1,
                "line_end": 5,
                "line_count": 5,
                "file_type": "markdown",
                "mtime_epoch_ms": 10,
                "sha256": "mdhash",
                "truncated": False,
            }
        ]

    def code_stub(*args, **kwargs):
        calls["code"] += 1
        return [
            {
                "path": "src/app.py",
                "chunk_id": "c1",
                "line_start": 1,
                "line_end": 8,
                "line_count": 8,
                "file_type": "code",
                "mtime_epoch_ms": 11,
                "sha256": "codehash",
                "truncated": False,
            }
        ]

    def line_stub(*args, **kwargs):
        calls["line"] += 1
        return [
            {
                "path": "notes/todo.txt",
                "chunk_id": "o1",
                "line_start": 1,
                "line_end": 3,
                "line_count": 3,
                "file_type": "other",
                "mtime_epoch_ms": 12,
                "sha256": "otherhash",
                "truncated": False,
            }
        ]

    monkeypatch.setattr(chunker, "markdown_chunk", md_stub)
    monkeypatch.setattr(chunker, "code_chunk", code_stub)
    monkeypatch.setattr(chunker, "line_chunk", line_stub)

    md_result = chunker.chunk_file("docs/readme.md", file_type="markdown")
    code_result = chunker.chunk_file("src/app.py", file_type="code")
    other_result = chunker.chunk_file("notes/todo.txt", file_type="text")

    assert calls == {"md": 1, "code": 1, "line": 1}
    assert md_result[0]["file_type"] == "markdown"
    assert code_result[0]["file_type"] == "code"
    assert other_result[0]["file_type"] == "other"
