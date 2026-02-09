from edge_agent.app.indexing.chunking import chunker


REQUIRED_KEYS = {
    "path",
    "chunk_id",
    "line_start",
    "line_end",
    "line_count",
    "file_type",
    "mtime_epoch_ms",
    "sha256",
    "truncated",
}


def test_metadata_propagation_no_mutation(monkeypatch):
    sample_chunk = {
        "path": "docs/readme.md",
        "chunk_id": "c1",
        "line_start": 1,
        "line_end": 4,
        "line_count": 4,
        "file_type": "markdown",
        "mtime_epoch_ms": 123,
        "sha256": "abc123",
        "truncated": False,
    }

    def markdown_chunk_stub(file_path, **kwargs):
        return [sample_chunk]

    monkeypatch.setattr(chunker, "markdown_chunk", markdown_chunk_stub)
    monkeypatch.setattr(chunker, "code_chunk", lambda *a, **k: [])
    monkeypatch.setattr(chunker, "line_chunk", lambda *a, **k: [])

    result = chunker.chunk_file("docs/readme.md", file_type="markdown")
    assert result == [sample_chunk]
    assert set(result[0].keys()) == REQUIRED_KEYS
