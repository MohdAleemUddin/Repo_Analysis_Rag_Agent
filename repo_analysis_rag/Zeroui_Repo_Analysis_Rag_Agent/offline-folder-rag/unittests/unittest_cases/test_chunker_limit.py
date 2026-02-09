import json

from edge_agent.app.indexing import manifest_store
from edge_agent.app.indexing.chunking import chunker


def _build_chunk(path: str, index: int) -> dict[str, object]:
    return {
        "path": path,
        "chunk_id": f"c{index}",
        "line_start": index,
        "line_end": index,
        "line_count": 1,
        "file_type": "code",
        "mtime_epoch_ms": index,
        "sha256": f"hash-{index}",
        "truncated": False,
    }


def test_chunk_limit_records_manifest_entry(tmp_path, monkeypatch):
    file_path = "src/app.py"
    manifest_path = tmp_path / "manifest.json"

    def code_chunk_stub(*args, **kwargs):
        return [_build_chunk(file_path, idx) for idx in range(1, chunker.MAX_CHUNKS_PER_FILE + 25)]

    monkeypatch.setattr(chunker, "code_chunk", code_chunk_stub)
    monkeypatch.setattr(chunker, "markdown_chunk", lambda *args, **kwargs: [])
    monkeypatch.setattr(chunker, "line_chunk", lambda *args, **kwargs: [])

    chunks = chunker.chunk_file(file_path, file_type="code", manifest_path=str(manifest_path))

    assert len(chunks) == chunker.MAX_CHUNKS_PER_FILE
    assert all(chunk["truncated"] for chunk in chunks)

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest_data["files"][file_path]
    assert entry["truncated"] is True
    assert entry["skip_reason"] == manifest_store.SKIP_REASON_CHUNK_LIMIT
