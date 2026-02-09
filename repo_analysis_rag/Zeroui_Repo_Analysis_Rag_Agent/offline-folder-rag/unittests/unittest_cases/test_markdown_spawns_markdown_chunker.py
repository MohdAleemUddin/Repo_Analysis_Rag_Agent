from edge_agent.app.indexing.chunking import chunker


def test_markdown_files_use_markdown_chunker(monkeypatch):
    called = {"markdown": 0}

    def markdown_chunk_stub(path, **kwargs):
        called["markdown"] += 1
        return [
            {
                "path": "docs/overview.md",
                "chunk_id": "c1",
                "line_start": 1,
                "line_end": 2,
                "line_count": 2,
                "file_type": "markdown",
                "mtime_epoch_ms": 4,
                "sha256": "jkl",
                "truncated": False,
            }
        ]

    def forbidden_chunk(*args, **kwargs):
        raise AssertionError("Should not invoke non-markdown chunker for markdown files.")

    monkeypatch.setattr(chunker, "markdown_chunk", markdown_chunk_stub)
    monkeypatch.setattr(chunker, "code_chunk", forbidden_chunk)
    monkeypatch.setattr(chunker, "line_chunk", forbidden_chunk)

    result = chunker.chunk_file("docs/overview.md", file_type="code")
    assert called["markdown"] == 1
    assert result[0]["file_type"] == "markdown"
