"""Deterministic query builder and execution helpers for edge agent search."""

from __future__ import annotations

import re
import json
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Set

FILENAME_MATCH_SCORE = 2
LINE_MATCH_SCORE = 2
PATH_KEYWORD_SCORE = 1

ALLOWED_PATH_KEYWORDS = ("src", "lib", "app", "core")  # Immutable list of permitted path keywords for scoring.

_MAX_TOKENS = 5
_TOKEN_PATTERN = re.compile(r"\b\w+\b", flags=re.UNICODE)
_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "as",
        "at",
        "by",
        "for",
        "from",
        "in",
        "of",
        "on",
        "or",
        "over",
        "the",
        "to",
        "with",
    }
)

_RESULT_CAP = 200
_RG_TIMEOUT_SECONDS = 5
_SEARCH_FAILURE_CODE = "SEARCH_FAILURE"
_ASK_PATTERN_LIMIT = 5


def _is_quoted(value: str) -> bool:
    """Return True when the trimmed value is wrapped in matching quotes."""
    return len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}


def _normalize_exact_literal(value: str) -> str:
    """Strip the surrounding quotes from a normalized literal match."""
    inner = value[1:-1]
    return inner.strip()


def _contains_whole_word(text: str, token: str) -> bool:
    """Check whether the token exists as a whole word inside the provided text."""
    if not token:
        return False
    pattern = re.compile(rf"\b{re.escape(token)}\b")
    return bool(pattern.search(text.lower()))


def _has_allowed_path_keyword(path: str) -> bool:
    """Return True if any allowed path keyword appears in the path (case-insensitive)."""
    path_lower = path.lower()
    for keyword in ALLOWED_PATH_KEYWORDS:
        if keyword in path_lower:
            return True
    return False


def _compute_match_score(match: Dict[str, Any], query_token: str | None) -> int:
    """Deterministically compute the score for a normalized match using PRD §15.3."""
    score = 0
    if query_token:
        token_lower = query_token.lower()
        basename_lower = match["basename"].lower()
        if token_lower in basename_lower:
            score += FILENAME_MATCH_SCORE
        if _contains_whole_word(match["line_text"], token_lower):
            score += LINE_MATCH_SCORE
    if _has_allowed_path_keyword(match["path"]):
        score += PATH_KEYWORD_SCORE
    return score


def _tokenize_query(value: str) -> List[str]:
    """Lowercase the query, remove stopwords, and cap the count."""
    if not value:
        return []
    tokens = [
        token
        for token in _TOKEN_PATTERN.findall(value.lower())
        if token not in _STOPWORDS
    ]
    return tokens[:_MAX_TOKENS]


def build_search_query(query: str | None) -> Dict[str, Any]:
    """Build the deterministic search payload for edge agent `/search`.

    The builder selects either `exact_literal` or `tokens`, never both, and
    guarantees normalization of the selected mode.
    """
    normalized = (query or "").strip()
    if _is_quoted(normalized):
        return {"exact_literal": _normalize_exact_literal(normalized)}
    return {"tokens": _tokenize_query(normalized)}


def _canonicalize_phrase(value: str) -> str:
    """Normalize whitespace when matching multi-word phrases."""
    return " ".join(value.split())


def build_ask_patterns(query: str, *, max_patterns: int | None = None) -> List[str]:
    """Normalize `/ask` queries into ripgrep-ready fixed-string patterns."""
    normalized = _canonicalize_phrase(query or "")
    if not normalized:
        return []
    max_patterns = max_patterns or _ASK_PATTERN_LIMIT
    tokens = _tokenize_query(normalized)

    patterns: List[str] = []
    seen: Set[str] = set()

    def add_pattern(pattern: str) -> None:
        key = pattern.lower()
        if key in seen:
            return
        seen.add(key)
        patterns.append(pattern)

    add_pattern(normalized)
    for token in tokens:
        if len(patterns) >= max_patterns:
            break
        add_pattern(token)

    return patterns


def _build_rg_command(root_path: Path, patterns: List[str], limit: int) -> List[str]:
    base_command = [
        "rg",
        "--json",
        "--fixed-strings",
        "--ignore-case",
        "--line-number",
        "--no-heading",
        "--color=never",
        f"--max-count={limit}",
    ]
    for pattern in patterns:
        base_command.extend(["-e", pattern])
    base_command.append(str(root_path))
    return base_command


def _parse_rg_output(output: str, limit: int) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    for line in output.splitlines():
        if len(results) >= limit:
            break
        if not line.strip():
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if payload.get("type") != "match":
            continue
        data = payload.get("data", {})
        path_text = data.get("path", {}).get("text", "")
        line_text = data.get("lines", {}).get("text", "").rstrip("\n")
        match = {
            "path": path_text,
            "basename": Path(path_text).name,
            "line_number": data.get("line_number"),
            "line_text": line_text,
        }
        results.append(match)
    return results


def execute_search(
    root_path: str | Path,
    query_payload: Dict[str, Any],
    timeout_seconds: float = _RG_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    """Execute the normalized search payload via `rg` with guardrails."""
    patterns: List[str] = []
    if "exact_literal" in query_payload:
        literal = query_payload["exact_literal"]
        if literal:
            patterns = [literal]
    elif tokens := query_payload.get("tokens"):
        # Tokens are produced once by `build_search_query` (already lowercased) and reused without re-tokenization.
        patterns = [token for token in tokens if token]

    if not patterns:
        return {"results": [], "error_code": None}

    command = _build_rg_command(Path(root_path), patterns, _RESULT_CAP)

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"results": [], "error_code": _SEARCH_FAILURE_CODE}

    results = _parse_rg_output(completed.stdout or "", _RESULT_CAP)
    query_token: str | None = None
    if "exact_literal" in query_payload:
        literal = query_payload["exact_literal"]
        if literal:
            query_token = literal.lower()
    elif tokens := query_payload.get("tokens"):
        query_token = tokens[0] if tokens else None
    for match in results:
        match["score"] = _compute_match_score(match, query_token)

    results.sort(
        key=lambda match: (-match["score"], match["path"], match["line_number"] or 0)
    )
    truncated_results = results[:_RESULT_CAP]
    return {"results": truncated_results, "error_code": None}


def execute_ask_query(
    root_path: str | Path,
    query: str,
    limit: int = _RESULT_CAP,
    timeout_seconds: float = _RG_TIMEOUT_SECONDS,
) -> List[Dict[str, Any]]:
    """Run ripgrep against `/ask` patterns and return raw match metadata."""
    patterns = build_ask_patterns(query)
    if not patterns:
        return []

    command = _build_rg_command(Path(root_path), patterns, limit)
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
        )
    except (subprocess.TimeoutExpired, subprocess.SubprocessError):
        return []

    return _parse_rg_output(completed.stdout or "", limit)


__all__ = ["build_search_query", "execute_search", "build_ask_patterns", "execute_ask_query"]
