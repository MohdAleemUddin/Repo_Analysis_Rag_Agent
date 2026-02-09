from pathlib import Path
import re
from typing import Iterable, List, Dict, Any, Tuple


BOUNDARY_PATTERNS: Dict[str, List[re.Pattern[str]]] = {
    "python": [re.compile(r"(?m)^(?:def|class)\b")],
    "brace": [
        re.compile(r"(?m)^\s*(?:function\b|class\b)"),
        re.compile(r"(?m)^\s*(?:public|private|protected)\b"),
    ],
}

EXTENSION_HINTS = {
    ".py": "python",
    ".js": "brace",
    ".ts": "brace",
    ".tsx": "brace",
    ".jsx": "brace",
    ".java": "brace",
    ".cs": "brace",
    ".c": "brace",
    ".cpp": "brace",
    ".cc": "brace",
    ".cxx": "brace",
    ".h": "brace",
    ".hpp": "brace",
}


def _line_no_for_pos(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _chunk_metadata(path: Path | str, chunk_id: int, line_start: int, line_end: int) -> Dict[str, Any]:
    return {
        "path": str(path),
        "chunk_id": f"c{chunk_id}",
        "line_start": line_start,
        "line_end": line_end,
        "line_count": line_end - line_start + 1,
        "file_type": "code",
        "mtime_epoch_ms": 0,
        "sha256": "",
        "truncated": False,
    }


def _language_hint_for_path(path: Path | str) -> str | None:
    suffix = Path(path).suffix.lower()
    return EXTENSION_HINTS.get(suffix)


def _line_start_offsets(lines_with_endings: List[str]) -> List[int]:
    offsets: List[int] = []
    cursor = 0
    for line in lines_with_endings:
        offsets.append(cursor)
        cursor += len(line)
    offsets.append(cursor)
    return offsets


def _find_boundaries(text: str, lines: List[str], hint: str | None) -> List[Tuple[int, int, str]]:
    candidates: List[Tuple[int, int, str]] = []
    seen_lines: set[int] = set()
    pattern_sources = [(hint, BOUNDARY_PATTERNS[hint])] if hint and hint in BOUNDARY_PATTERNS else BOUNDARY_PATTERNS.items()

    for kind, patterns in pattern_sources:
        for pattern in patterns:
            for match in pattern.finditer(text):
                raw = match.group(0)
                non_ws_offset = match.start() + (len(raw) - len(raw.lstrip()))
                if non_ws_offset >= len(text):
                    continue
                line_no = _line_no_for_pos(text, non_ws_offset)
                if line_no > len(lines) or line_no in seen_lines:
                    continue
                if kind == "python":
                    line = lines[line_no - 1]
                    if line and (line[0] == " " or line[0] == "\t"):
                        continue
                seen_lines.add(line_no)
                candidates.append((line_no, non_ws_offset, kind))

    return sorted(candidates, key=lambda item: item[1])


def chunk(file_path: Path | str, *args, **kwargs) -> Iterable[Dict[str, Any]]:
    MAX_LINES = 400
    path_obj = Path(file_path)
    text = path_obj.read_text(encoding="utf-8")
    lines_all = text.splitlines()
    lines_with_endings = text.splitlines(keepends=True)
    total_lines = len(lines_all)
    if total_lines == 0:
        return []

    line_offsets = _line_start_offsets(lines_with_endings)
    language_hint = _language_hint_for_path(file_path)
    boundaries = _find_boundaries(text, lines_all, language_hint)
    chunks: List[Dict[str, Any]] = []
    chunk_id = 1

    if not boundaries:
        from . import line_chunker

        return line_chunker.chunk(file_path, *args, **kwargs)

    def emit(ls: int, le: int):
        nonlocal chunk_id
        chunks.append(_chunk_metadata(file_path, chunk_id, ls, le))
        chunk_id += 1

    seen_lines = {line for line, _, _ in boundaries}
    idx = 0

    while idx < len(boundaries):
        boundary_line, _, kind = boundaries[idx]
        next_boundary_line = boundaries[idx + 1][0] if idx + 1 < len(boundaries) else total_lines + 1
        natural_end_line = min(next_boundary_line - 1, total_lines)
        if natural_end_line < boundary_line:
            natural_end_line = total_lines
        while natural_end_line > boundary_line and natural_end_line <= total_lines and not lines_all[natural_end_line - 1].strip():
            natural_end_line -= 1
        max_line = min(boundary_line + MAX_LINES - 1, natural_end_line)

        if kind == "python":
            base_idx = boundary_line - 1
            base_indent = len(lines_all[base_idx]) - len(lines_all[base_idx].lstrip(" "))
            end_line = boundary_line
            for ln in range(boundary_line + 1, natural_end_line + 1):
                line_text = lines_all[ln - 1]
                stripped = line_text.lstrip()
                indent = len(line_text) - len(stripped)

                if ln > max_line:
                    end_line = max_line
                    break

                if stripped == "" or stripped.startswith("@"):
                    end_line = ln
                    continue

                if indent <= base_indent:
                    end_line = ln - 1
                    break

                end_line = ln
            emit(boundary_line, end_line)

            if end_line == max_line and max_line < natural_end_line:
                remainder_line = max_line + 1
                if remainder_line <= total_lines and remainder_line not in seen_lines:
                    pos = line_offsets[remainder_line - 1] if remainder_line - 1 < len(line_offsets) else line_offsets[-1]
                    boundaries.insert(idx + 1, (remainder_line, pos, kind))
                    seen_lines.add(remainder_line)
        else:
            end_line = boundary_line
            brace_level = 0
            block_started = False
            for ln in range(boundary_line, natural_end_line + 1):
                line_text = lines_all[ln - 1]
                for ch in line_text:
                    if ch == "{":
                        brace_level += 1
                        block_started = True
                    elif ch == "}" and block_started:
                        brace_level -= 1
                end_line = ln
                if block_started and brace_level <= 0:
                    break
                if ln >= max_line:
                    break
            if end_line < boundary_line:
                end_line = boundary_line
            block_start = boundary_line
            block_end = end_line
            while block_start <= block_end:
                segment_end = min(block_start + 200 - 1, block_end)
                emit(block_start, segment_end)
                if segment_end >= block_end:
                    break
                block_start = segment_end - 20 + 1
            if end_line == max_line and max_line < natural_end_line:
                remainder_line = max_line + 1
                if remainder_line <= total_lines and remainder_line not in seen_lines:
                    pos = line_offsets[remainder_line - 1] if remainder_line - 1 < len(line_offsets) else line_offsets[-1]
                    boundaries.insert(idx + 1, (remainder_line, pos, kind))
                    seen_lines.add(remainder_line)

        idx += 1

    return chunks
