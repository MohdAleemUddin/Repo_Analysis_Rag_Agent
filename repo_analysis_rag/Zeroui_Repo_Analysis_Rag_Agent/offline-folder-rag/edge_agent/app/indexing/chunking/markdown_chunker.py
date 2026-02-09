import re
from pathlib import Path
from typing import Iterable, Dict, Any


HEADING_RE = re.compile(r"^#{1,6}\s+")


def chunk(file_path: Path | str, *args, **kwargs) -> Iterable[Dict[str, Any]]:
    r"""
    Split markdown into sections starting at lines that match ^#{1,6}\s+.
    Returns chunks with required metadata; headings define boundaries.
    """
    lines = Path(file_path).read_text(encoding="utf-8").splitlines()

    sections: list[tuple[int, int]] = []
    start = 0
    def _trim_end(s: int, e: int) -> tuple[int, int]:
        while e >= s and lines[e].strip() == "":
            e -= 1
        return s, max(e, s)

    for idx, line in enumerate(lines):
        if idx == 0:
            continue
        if HEADING_RE.match(line):
            s, e = _trim_end(start, idx - 1)
            sections.append((s, e))
            start = idx
    s, e = _trim_end(start, len(lines) - 1)
    sections.append((s, e))

    chunks: list[Dict[str, Any]] = []
    chunk_counter = 1
    MAX_LINES = 200
    OVERLAP = 20

    def emit_chunk(start_idx: int, end_idx: int):
        nonlocal chunk_counter
        line_start = start_idx + 1
        line_end = end_idx + 1
        chunks.append(
            {
                "path": str(file_path),
                "chunk_id": f"c{chunk_counter}",
                "line_start": line_start,
                "line_end": line_end,
                "line_count": line_end - line_start + 1,
                "file_type": "markdown",
                "mtime_epoch_ms": 0,
                "sha256": "",
                "truncated": False,
            }
        )
        chunk_counter += 1

    for s, e in sections:
        current = s
        while current <= e:
            end_idx = min(current + MAX_LINES - 1, e)
            emit_chunk(current, end_idx)
            if end_idx == e:
                break
            current = end_idx - (OVERLAP - 1)
            if current <= end_idx:
                current = end_idx - OVERLAP + 1
    return chunks
