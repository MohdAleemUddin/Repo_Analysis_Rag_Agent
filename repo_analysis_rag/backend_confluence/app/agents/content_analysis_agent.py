"""Content analysis agent: cache by file hash, per-file timer, chunked processing. Output: ContentProfile."""

import ast
import hashlib
import time
from typing import Any

from app.agents.contracts import ContentProfile
from app.config.config import (
    CONFLUENCE_ANALYSIS_CACHE_ENABLED,
    CONFLUENCE_ANALYSIS_CACHE_MAX_ENTRIES,
    CONFLUENCE_ANALYSIS_CACHE_TTL_SECONDS,
    CONFLUENCE_CHUNK_SIZE_BYTES,
    CONFLUENCE_LARGE_FILE_THRESHOLD_BYTES,
)
from app.confluence.prd_monitor import timer_per_file_analysis
from app.langchain.chains.analysis_chain import run_analysis as run_analysis_chain
from app.logging.logger import get_logger

logger = get_logger(__name__)

_analysis_cache: dict[str, tuple[Any, float]] = {}


def _content_hash(content: str | bytes) -> str:
    if isinstance(content, str):
        content = content.encode("utf-8", errors="replace")
    return hashlib.sha256(content).hexdigest()


def _cache_get(key: str) -> Any | None:
    if not CONFLUENCE_ANALYSIS_CACHE_ENABLED:
        return None
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
    while (
        len(_analysis_cache) >= CONFLUENCE_ANALYSIS_CACHE_MAX_ENTRIES
        and _analysis_cache
    ):
        oldest_key = min(_analysis_cache, key=lambda k: _analysis_cache[k][1])
        del _analysis_cache[oldest_key]
    _analysis_cache[key] = (value, time.time())


def _deterministic_parse(content: str) -> dict[str, Any]:
    """Deterministic parsing first: AST where applicable, structure/size signals."""
    signals: dict[str, Any] = {
        "content_types": [],
        "languages": [],
        "structure_signals": [],
        "detected_patterns": [],
        "relationships": [],
        "confidence_scores": {},
        "structure": "plain",
        "language": "text",
        "size_chars": len(content),
    }
    strip = content.strip()
    if not strip:
        return signals
    if strip.startswith("#") or "def " in content or "class " in content:
        signals["structure_signals"].append("code_like")
        signals["content_types"].append("document")
    if "def " in content and "class " in content:
        signals["content_types"].append("module")
    try:
        ast.parse(content)
        signals["languages"].append("python")
        signals["structure_signals"].append("python_ast")
        signals["confidence_scores"]["ast"] = 1.0
    except SyntaxError:
        pass
    if not signals["languages"]:
        signals["languages"].append("text")
    if "import " in content or "from " in content:
        signals["detected_patterns"].append("imports")
    if "TODO" in content or "FIXME" in content:
        signals["detected_patterns"].append("todos")
    return signals


def _analyze_chunk(chunk: str) -> ContentProfile:
    """Analyze a single chunk; returns minimal ContentProfile."""
    signals = {"language": "text", "size_chars": len(chunk), "chunk": True}
    augmented = run_analysis_chain(chunk, existing_signals=signals)
    return ContentProfile(
        content_types=augmented.get("content_types", []),
        languages=augmented.get("languages", ["text"]),
        structure_signals=augmented.get("structure_signals", []),
        detected_patterns=augmented.get("detected_patterns", []),
        relationships=augmented.get("relationships", []),
        confidence_scores=augmented.get("confidence_scores", {}),
        ai_reasoning=augmented.get("ai_reasoning", ""),
    )


def _analyze_small(content: str) -> ContentProfile:
    """Full content analysis: deterministic parse then analysis_chain augment."""
    signals = _deterministic_parse(content)
    augmented = run_analysis_chain(content, existing_signals=signals)
    return ContentProfile(
        content_types=augmented.get("content_types", [])
        or signals.get("content_types", []),
        languages=augmented.get("languages", [])
        or (signals.get("languages") or ["text"]),
        structure_signals=augmented.get("structure_signals", [])
        or signals.get("structure_signals", []),
        detected_patterns=augmented.get("detected_patterns", [])
        or signals.get("detected_patterns", []),
        relationships=augmented.get("relationships", [])
        or signals.get("relationships", []),
        confidence_scores=augmented.get("confidence_scores", {})
        or signals.get("confidence_scores", {}),
        ai_reasoning=augmented.get("ai_reasoning", ""),
    )


def analyze(content: str, file_index: int = 0) -> ContentProfile:
    """
    Analyze content. Deterministic parsing first, then analysis_chain as augment.
    Uses cache keyed by content hash. For large content, chunks. Caller wraps with timer_per_file_analysis.
    """
    key = _content_hash(content)
    cached = _cache_get(key)
    if cached is not None:
        return (
            cached if isinstance(cached, ContentProfile) else ContentProfile(**cached)
        )

    content_bytes = content.encode("utf-8", errors="replace")
    if len(content_bytes) > CONFLUENCE_LARGE_FILE_THRESHOLD_BYTES:
        results: list[ContentProfile] = []
        start = 0
        while start < len(content_bytes):
            chunk_bytes = content_bytes[start : start + CONFLUENCE_CHUNK_SIZE_BYTES]
            chunk = chunk_bytes.decode("utf-8", errors="replace")
            results.append(_analyze_chunk(chunk))
            start += CONFLUENCE_CHUNK_SIZE_BYTES
        merged = ContentProfile(
            content_types=["document"],
            languages=["text"],
            structure_signals=["chunked"],
            detected_patterns=["large_content"],
            relationships=[],
            confidence_scores={"chunks_analyzed": float(len(results))},
            ai_reasoning="Chunked analysis of large content.",
        )
        _cache_set(key, merged)
        return merged

    result = _analyze_small(content)
    _cache_set(key, result)
    return result


def analyze_file_with_timer(content: str, file_index: int = 0) -> ContentProfile:
    """Analyze one file with PRD per-file timer. Returns ContentProfile."""
    with timer_per_file_analysis(file_index=file_index):
        return analyze(content, file_index)
