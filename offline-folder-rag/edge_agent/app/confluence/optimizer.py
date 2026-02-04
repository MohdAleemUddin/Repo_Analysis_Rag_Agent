# PRD User Story 8: performance optimization (caching, parallelization, <5% overhead)
import hashlib
from typing import Any

# In-memory cache by file hash for analysis results (NFR1)
_cache: dict[str, Any] = {}
_CACHE_MAX = 500


def _file_hash(path: str) -> str:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return hashlib.sha256(path.encode()).hexdigest()


def get_cached_analysis(path: str) -> Any | None:
    key = _file_hash(path)
    return _cache.get(key)


def set_cached_analysis(path: str, result: Any) -> None:
    key = _file_hash(path)
    if len(_cache) >= _CACHE_MAX:
        # Evict oldest (simple: drop first half)
        keys = list(_cache.keys())[: _CACHE_MAX // 2]
        for k in keys:
            _cache.pop(k, None)
    _cache[key] = result


def optimize() -> dict[str, Any]:
    """Return optimizer status (cache size, etc.)."""
    return {"cache_size": len(_cache), "cache_max": _CACHE_MAX}
