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


def test_metadata_integrity_flow(monkeypatch):
    markdown_chunk = {
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
    code_chunk = {
        "path": "src/app.py",
        "chunk_id": "c1",
        "line_start": 1,
        "line_end": 20,
        "line_count": 20,
        "file_type": "code",
        "mtime_epoch_ms": 11,
        "sha256": "codehash",
        "truncated": False,
    }
    other_chunk = {
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

    monkeypatch.setattr(chunker, "markdown_chunk", lambda *a, **k: [markdown_chunk])
    monkeypatch.setattr(chunker, "code_chunk", lambda *a, **k: [code_chunk])
    monkeypatch.setattr(chunker, "line_chunk", lambda *a, **k: [other_chunk])

    md_result = chunker.chunk_file("docs/readme.md", file_type="markdown")
    code_result = chunker.chunk_file("src/app.py", file_type="code")
    other_result = chunker.chunk_file("notes/todo.txt", file_type="text")

    assert md_result == [markdown_chunk]
    assert code_result == [code_chunk]
    assert other_result == [other_chunk]

    for chunk in (md_result[0], code_result[0], other_result[0]):
        assert set(chunk.keys()) == REQUIRED_KEYS
