from __future__ import annotations

import os
from pathlib import Path

from ..config.defaults import DEFAULT_INDEX_DIR


def resolve_index_dir() -> Path:
    """Return RAG_INDEX_DIR when set; otherwise the default index directory."""
    env_dir = os.environ.get("RAG_INDEX_DIR")
    if env_dir:
        return Path(env_dir)
    return DEFAULT_INDEX_DIR
