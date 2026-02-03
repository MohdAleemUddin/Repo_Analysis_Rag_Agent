"""Content analysis agent: analyzes content with cache by file hash, per-file timer, and chunked processing for large files."""

import hashlib
import logging
from typing import Any

from app.config.config import (
    CONFLUENCE_ANALYSIS_CACHE_ENABLED,
    CONFLUENCE_ANALYSIS_CACHE_MAX_ENTRIES,
    CONFLUENCE_ANALYSIS_CACHE_TTL_SECONDS,
    CONFLUENCE_CHUNK_SIZE_BYTES,
    CONFLUENCE_LARGE_FILE_THRESHOLD_BYTES,
)
from app.confluence.prd_monitor import timer_per_file_analysis

logger = logging.getLogger(__name__)

# In-memory cache: hash -> (result, timestamp)
_analysis_cache: dict[str, tuple[Any, float]] = {}


def _content_hash(content: str | bytes) -> str:
    if isinstance(content, str):
        content = content.encode("utf-8", errors="replace")
    return hashlib.sha256(content).hexdigest()


def _cache_get(key: str) -> Any | None:
    if not CONFLUENCE_ANALYSIS_CACHE_ENABLED:
        return None
    import time

    entry = _analysis_cache.get(key)
    if not entry:
        return None
    result, ts = entry
    if (
        CONFLUENCE_ANALYSIS_CACHE_TTL_SECONDS > 0
        and (time.time() - ts) > CONFLUENCE_ANALYSIS_CACHE_TTL_SECONDS
    ):
        _analysis_cache.pop(key, None)
        return None
    return result


def _cache_set(key: str, value: Any) -> None:
    if not CONFLUENCE_ANALYSIS_CACHE_ENABLED:
        return
    import time

    while (
        len(_analysis_cache) >= CONFLUENCE_ANALYSIS_CACHE_MAX_ENTRIES
        and _analysis_cache
    ):
        oldest_key = min(_analysis_cache, key=lambda k: _analysis_cache[k][1])
        del _analysis_cache[oldest_key]
    _analysis_cache[key] = (value, time.time())


def _analyze_chunk(chunk: str) -> dict[str, Any]:
    """Analyze a single chunk; returns a small profile. Override for real logic."""
    return {"language": "text", "size_chars": len(chunk), "chunk": True}


def _analyze_small(content: str) -> dict[str, Any]:
    """Full content analysis for small content."""
    return {
        "language": "text",
        "structure": "plain",
        "size_chars": len(content),
        "patterns": [],
    }


def analyze(content: str, file_index: int = 0) -> dict[str, Any]:
    """
    Analyze content. Uses cache keyed by content hash. For large content, processes in chunks.
    Wrapped with per-file timer by caller (coordinator) via timer_per_file_analysis.
    """
    key = _content_hash(content)
    cached = _cache_get(key)
    if cached is not None:
        return cached

    content_bytes = content.encode("utf-8", errors="replace")
    if len(content_bytes) > CONFLUENCE_LARGE_FILE_THRESHOLD_BYTES:
        # Process in chunks to bound memory
        results: list[dict[str, Any]] = []
        start = 0
        while start < len(content_bytes):
            chunk_bytes = content_bytes[start : start + CONFLUENCE_CHUNK_SIZE_BYTES]
            chunk = chunk_bytes.decode("utf-8", errors="replace")
            results.append(_analyze_chunk(chunk))
            start += CONFLUENCE_CHUNK_SIZE_BYTES
        merged = {
            "language": "text",
            "structure": "chunked",
            "size_chars": len(content),
            "chunks_analyzed": len(results),
        }
        _cache_set(key, merged)
        return merged

    result = _analyze_small(content)
    _cache_set(key, result)
    return result


def analyze_file_with_timer(content: str, file_index: int = 0) -> dict[str, Any]:
    """
    Analyze one file with PRD per-file timer. Call this from coordinator for each file.
    """
    with timer_per_file_analysis(file_index=file_index):
        return analyze(content, file_index)
