from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, Any, List

SKIP_REASON_CHUNK_LIMIT = "CHUNK_LIMIT"
_FILES_KEY = "files"

class ManifestStore:
    """
    Handles persistence of indexing metadata (manifest.json).
    """
    
    # Skip reason constants
    EXCLUDED_DIR = "EXCLUDED_DIR"
    EXCLUDED_EXT = "EXCLUDED_EXT"
    SYMLINK = "SYMLINK"
    SIZE_CAP = "SIZE_CAP"
    BINARY = "BINARY"
    ENCODING_ERROR = "ENCODING_ERROR"
    CHUNK_LIMIT = SKIP_REASON_CHUNK_LIMIT
    OTHER = "OTHER"

    def __init__(self, manifest_path: str):
        self.manifest_path = Path(manifest_path)
        self.entries: List[Dict[str, Any]] = []

    def add_entry(self, path: str, status: str, skip_reason: str = None, encoding: str = None, mtime_epoch_ms: int = None, indexed_at_epoch_ms: int = None):
        """Add a record to the manifest."""
        entry = {
            "path": path,
            "status": status
        }
        if skip_reason:
            entry["skip_reason"] = skip_reason
        if encoding:
            entry["encoding"] = encoding
        if mtime_epoch_ms is not None:
            entry["mtime_epoch_ms"] = mtime_epoch_ms
        if indexed_at_epoch_ms is not None:
            entry["indexed_at_epoch_ms"] = indexed_at_epoch_ms
        self.entries.append(entry)

    def add_or_update_entry(self, path: str, status: str, skip_reason: str = None, encoding: str = None, mtime_epoch_ms: int = None, indexed_at_epoch_ms: int = None):
        """Add or update a record in the manifest."""
        for entry in self.entries:
            if entry["path"] == path:
                entry["status"] = status
                if skip_reason:
                    entry["skip_reason"] = skip_reason
                else:
                    entry.pop("skip_reason", None)
                if encoding:
                    entry["encoding"] = encoding
                if mtime_epoch_ms is not None:
                    entry["mtime_epoch_ms"] = mtime_epoch_ms
                if indexed_at_epoch_ms is not None:
                    entry["indexed_at_epoch_ms"] = indexed_at_epoch_ms
                return
        
        self.add_entry(path, status, skip_reason, encoding, mtime_epoch_ms, indexed_at_epoch_ms)

    def add_symlink_entry(self, path: str):
        """Record a skipped symlink entry."""
        self.add_entry(path, status="SKIPPED", skip_reason=self.SYMLINK)

    def save(self):
        """Save entries to manifest.json."""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        # Load existing manifest to merge if needed, or just overwrite if that's the current behavior
        # The current ManifestStore.save() overwrites. Let's keep it consistent but add a way to merge chunk limit info.
        data = {"entries": self.entries}
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)


def _ensure_files_section(data: dict[str, Any]) -> dict[str, Any]:
    if _FILES_KEY not in data or not isinstance(data[_FILES_KEY], dict):
        data[_FILES_KEY] = {}
    return data


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {_FILES_KEY: {}}
    return _ensure_files_section(data)


def _write_manifest(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def record_file_truncation(
    manifest_path: Path | str,
    file_path: Path | str,
    skip_reason: str = SKIP_REASON_CHUNK_LIMIT,
) -> None:
    if not manifest_path:
        return

    manifest_file = Path(manifest_path)
    manifest_data = _load_manifest(manifest_file)
    files = manifest_data.setdefault(_FILES_KEY, {})
    entry = files.get(str(file_path), {})
    entry.update({"truncated": True, "skip_reason": skip_reason})
    files[str(file_path)] = entry
    _write_manifest(manifest_file, manifest_data)


__all__ = [
    "ManifestStore",
    "SKIP_REASON_CHUNK_LIMIT",
    "record_file_truncation",
]
from enum import Enum
from pathlib import Path
from typing import Dict, List, Set

from .index_dir import resolve_index_dir

__all__ = [
    "ManifestStatus",
    "SkipReason",
    "REQUIRED_FIELDS",
    "SKIP_REASON_FIELD",
    "manifest_entry_keys",
    "create_manifest_entry",
    "create_indexed_entry",
    "create_skipped_entry",
    "is_skipped",
    "manifest_file_path",
    "write_manifest_entries",
    "read_manifest_entries",
    "append_manifest_entry",
]


class ManifestStatus(str, Enum):
    INDEXED = "INDEXED"
    SKIPPED = "SKIPPED"


class SkipReason(str, Enum):
    EXCLUDED_DIR = "EXCLUDED_DIR"
    EXCLUDED_EXT = "EXCLUDED_EXT"
    SIZE_CAP = "SIZE_CAP"
    BINARY = "BINARY"
    SYMLINK = "SYMLINK"
    DECODE_ERROR = "DECODE_ERROR"
    CHUNK_LIMIT = "CHUNK_LIMIT"
    OTHER = "OTHER"


REQUIRED_FIELDS = ("path", "mtime_epoch_ms", "sha256", "indexed_at_epoch_ms", "status")
SKIP_REASON_FIELD = "skip_reason"


def manifest_entry_keys(include_skip_reason: bool = False) -> Set[str]:
    """Return the expected key set for a manifest entry."""
    keys = set(REQUIRED_FIELDS)
    if include_skip_reason:
        keys.add(SKIP_REASON_FIELD)
    return keys


def is_skipped(entry: Dict[str, object]) -> bool:
    """Return True when the manifest entry is marked as skipped."""
    return str(entry.get("status")) == ManifestStatus.SKIPPED.value


def _normalize_status(status: str | ManifestStatus) -> ManifestStatus:
    if isinstance(status, ManifestStatus):
        return status
    try:
        return ManifestStatus(str(status))
    except ValueError:
        raise ValueError(f"Unsupported manifest status: {status!r}") from None


def _normalize_skip_reason(reason: str | SkipReason | None) -> SkipReason:
    if reason is None:
        raise ValueError("skip_reason is required for SKIPPED entries")
    if isinstance(reason, SkipReason):
        return reason
    try:
        return SkipReason(str(reason))
    except ValueError:
        raise ValueError(f"Unsupported skip_reason: {reason!r}") from None


def create_manifest_entry(
    path: str,
    mtime_epoch_ms: int,
    sha256: str,
    indexed_at_epoch_ms: int,
    status: str | ManifestStatus,
    *,
    skip_reason: str | None = None,
) -> Dict[str, object]:
    """
    Build a deterministic manifest entry.

    Fields:
    - path
    - mtime_epoch_ms
    - sha256
    - indexed_at_epoch_ms
    - status
    - skip_reason (only when status == SKIPPED)
    """
    normalized_status = _normalize_status(status)
    entry: Dict[str, object] = {
        "path": path,
        "mtime_epoch_ms": int(mtime_epoch_ms),
        "sha256": sha256,
        "indexed_at_epoch_ms": int(indexed_at_epoch_ms),
        "status": normalized_status.value,
    }
    if normalized_status is ManifestStatus.SKIPPED:
        entry[SKIP_REASON_FIELD] = _normalize_skip_reason(skip_reason).value
    return entry


def create_indexed_entry(
    path: str,
    mtime_epoch_ms: int,
    sha256: str,
    indexed_at_epoch_ms: int,
) -> Dict[str, object]:
    """Build a manifest entry for a successfully indexed file with status=INDEXED."""
    return create_manifest_entry(
        path=path,
        mtime_epoch_ms=mtime_epoch_ms,
        sha256=sha256,
        indexed_at_epoch_ms=indexed_at_epoch_ms,
        status=ManifestStatus.INDEXED,
        skip_reason=None,
    )


def create_skipped_entry(
    path: str,
    mtime_epoch_ms: int,
    sha256: str,
    indexed_at_epoch_ms: int,
    reason: str | SkipReason,
) -> Dict[str, object]:
    """Build a manifest entry for a skipped file with an enum reason."""
    return create_manifest_entry(
        path=path,
        mtime_epoch_ms=mtime_epoch_ms,
        sha256=sha256,
        indexed_at_epoch_ms=indexed_at_epoch_ms,
        status=ManifestStatus.SKIPPED,
        skip_reason=reason,
    )


def manifest_file_path(repo_id: str) -> Path:
    """Return the manifest.json path for the given repo_id."""
    base = resolve_index_dir()
    manifest_path = Path(base) / repo_id / "manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    return manifest_path


def write_manifest_entries(repo_id: str, entries: List[Dict[str, object]]) -> Path:
    """Persist manifest entries list to disk in deterministic JSON form."""
    path = manifest_file_path(repo_id)
    with path.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, sort_keys=True)
    return path


def read_manifest_entries(repo_id: str) -> List[Dict[str, object]]:
    """Load manifest entries list from disk; return [] if missing."""
    path = manifest_file_path(repo_id)
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Manifest content must be a list of entries")
    return data


def append_manifest_entry(repo_id: str, entry: Dict[str, object]) -> Path:
    """Append a manifest entry and persist the full list."""
    entries = read_manifest_entries(repo_id)
    entries.append(entry)
    return write_manifest_entries(repo_id, entries)
