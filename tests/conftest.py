"""Pytest configuration. Add edge_agent to path so app package is importable."""

import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
edge_agent = root / "offline-folder-rag" / "edge_agent"
if str(edge_agent) not in sys.path:
    sys.path.insert(0, str(edge_agent))
