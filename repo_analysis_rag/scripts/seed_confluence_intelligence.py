"""
PRD §8.2: Seed 7 templates + 50+ initial intelligence examples.
Populates confluence_data/examples/learned_examples.json when empty.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

_EDGE_AGENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
_REPO_ROOT = os.path.abspath(os.path.join(_EDGE_AGENT_ROOT, ".."))
_EXAMPLES_DIR = os.path.join(_REPO_ROOT, "confluence_data", "examples")
_LEARNED_PATH = os.path.join(_EXAMPLES_DIR, "learned_examples.json")

TEMPLATE_NAMES = [
    "Python API Intelligence Template",
    "Web Application Intelligence Template",
    "Configuration Intelligence Template",
    "Database Intelligence Template",
    "Mixed Project Intelligence Template",
    "Library Intelligence Template",
    "Testing Intelligence Template",
]


def _content_profile_hash(cp: dict) -> str:
    import hashlib

    return hashlib.sha256(json.dumps(cp, sort_keys=True).encode()).hexdigest()


def main() -> int:
    os.makedirs(_EXAMPLES_DIR, exist_ok=True)
    if os.path.isfile(_LEARNED_PATH):
        with open(_LEARNED_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if len(data.get("examples", [])) >= 50:
            return 0
    examples = []
    for i in range(52):
        t = TEMPLATE_NAMES[i % len(TEMPLATE_NAMES)]
        tid = str(uuid4())
        cp = {
            "content_types": [
                "python_api",
                "configuration",
                "database",
                "mixed",
                "library",
                "testing",
                "web_app",
            ][i % 7],
            "detected_patterns": [
                "fastapi",
                "react",
                "config",
                "schema",
                "project",
                "package",
                "pytest",
            ][i % 7],
            "language": (
                "python" if i % 3 == 0 else "javascript" if i % 3 == 1 else None
            ),
            "structure_summary": f"Example structure {i+1}",
        }
        examples.append(
            {
                "id": str(uuid4()),
                "content_profile": cp,
                "template_ref": {"template_id": tid, "template_name": t},
                "intelligence_metrics": {
                    "confidence_score": 0.85 + (i % 15) / 100,
                    "success_rate": 0.9 + (i % 10) / 100,
                    "intelligence_score": 0.88,
                },
                "learned_at": datetime.now(timezone.utc).isoformat(),
                "content_profile_hash": _content_profile_hash(cp),
                "confidence_score": round(0.85 + (i % 15) / 100, 2),
                "project_path": None,
                "user_feedback": (i % 5) + 1,
                "intelligence_embedding": None,
            }
        )
    data = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "examples": examples,
    }
    with open(_LEARNED_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
