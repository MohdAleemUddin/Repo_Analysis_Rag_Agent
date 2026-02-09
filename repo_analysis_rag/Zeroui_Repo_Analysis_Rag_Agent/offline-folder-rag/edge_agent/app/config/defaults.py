from __future__ import annotations

import os
from pathlib import Path


def default_index_dir() -> Path:
    """
    Default index directory.

    Uses %USERPROFILE%/.offline_rag_index on Windows (or Path.home() fallback).
    """
    user_profile = os.environ.get("USERPROFILE", "")
    base = Path(user_profile) if user_profile else Path.home()
    return base / ".offline_rag_index"


DEFAULT_INDEX_DIR: Path = default_index_dir()
