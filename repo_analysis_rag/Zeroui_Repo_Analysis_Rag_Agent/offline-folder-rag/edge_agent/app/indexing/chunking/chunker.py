from pathlib import Path

from ..manifest_store import SKIP_REASON_CHUNK_LIMIT, record_file_truncation
from .code_chunker import chunk as code_chunk
from .line_chunker import chunk as line_chunk
from .markdown_chunker import chunk as markdown_chunk

MAX_CHUNKS_PER_FILE = 200

REQUIRED_METADATA_KEYS = (
    "path",
    "chunk_id",
    "line_start",
    "line_end",
    "line_count",
    "file_type",
    "mtime_epoch_ms",
    "sha256",
    "truncated",
)
_REQUIRED_KEYS_SET = set(REQUIRED_METADATA_KEYS)


def classify_file_type(file_path: Path | str, file_type: str | None) -> str:
    input_path = Path(file_path)
    extension = input_path.suffix.lower()
    if extension == ".md":
        return "markdown"

    normalized_type = (file_type or "").strip().lower()
    if normalized_type == "code":
        return "code"

    return "other"


def chunk_file(file_path: Path | str, file_type: str | None = None, **kwargs):
    manifest_path = kwargs.get("manifest_path")
    classification = classify_file_type(file_path, file_type)
    if classification == "markdown":
        chunks = markdown_chunk(file_path, **kwargs)
    elif classification == "code":
        chunks = code_chunk(file_path, **kwargs)
    else:
        chunks = line_chunk(file_path, **kwargs)

    chunks = _enforce_chunk_limit(chunks, file_path, manifest_path)
    _validate_metadata(chunks)
    return chunks


def _validate_metadata(chunks):
    for chunk in chunks:
        if not isinstance(chunk, dict):
            raise ValueError("Chunk must be a dict containing required metadata.")
        keys = set(chunk.keys())
        if keys != _REQUIRED_KEYS_SET:
            raise ValueError("Chunk metadata keys must match required set exactly.")


def _enforce_chunk_limit(chunks, file_path: Path | str, manifest_path: Path | str | None):
    if len(chunks) <= MAX_CHUNKS_PER_FILE:
        return chunks

    limited_chunks = chunks[:MAX_CHUNKS_PER_FILE]
    for chunk in limited_chunks:
        chunk["truncated"] = True

    if manifest_path:
        record_file_truncation(manifest_path, file_path, SKIP_REASON_CHUNK_LIMIT)

    return limited_chunks
