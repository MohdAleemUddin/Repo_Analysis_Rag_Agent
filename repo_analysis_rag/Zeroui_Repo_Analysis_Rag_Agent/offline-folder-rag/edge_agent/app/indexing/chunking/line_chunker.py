from pathlib import Path
from typing import Iterable, Dict, Any


def chunk(file_path: Path | str, *args, **kwargs) -> Iterable[Dict[str, Any]]:
    """Fallback line-level chunker stub returning required metadata."""
    lines = Path(file_path).read_text(encoding="utf-8").splitlines()
    line_start = 1
    line_end = len(lines)
    line_count = line_end - line_start + 1 if line_end >= line_start else 0
    return [
        {
            "path": str(file_path),
            "chunk_id": "c1",
            "line_start": line_start,
            "line_end": line_end,
            "line_count": line_count,
            "file_type": "other",
            "mtime_epoch_ms": 0,
            "sha256": "",
            "truncated": False,
        }
    ]
