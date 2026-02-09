from edge_agent.app.indexing.chunking import chunker


def test_functional_markdown_chunking_flow(monkeypatch):
    invoked = {"markdown": 0}

    def markdown_chunk_stub(file_path, **kwargs):
        invoked["markdown"] += 1
        return [
            {
                "path": "notes/readme.md",
                "chunk_id": "c1",
                "line_start": 1,
                "line_end": 4,
                "line_count": 4,
                "file_type": "markdown",
                "mtime_epoch_ms": 5,
                "sha256": "mno",
                "truncated": False,
            }
        ]

    def forbidden_chunk(*args, **kwargs):
        raise AssertionError("Code or line chunker should not run for markdown files.")

    monkeypatch.setattr(chunker, "markdown_chunk", markdown_chunk_stub)
    monkeypatch.setattr(chunker, "code_chunk", forbidden_chunk)
    monkeypatch.setattr(chunker, "line_chunk", forbidden_chunk)

    result = chunker.chunk_file("notes/readme.md", file_type="code")
    assert invoked["markdown"] == 1
    assert result[0]["file_type"] == "markdown"
