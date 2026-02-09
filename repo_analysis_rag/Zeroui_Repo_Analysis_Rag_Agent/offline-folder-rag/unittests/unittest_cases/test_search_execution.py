"""Unit tests covering deterministic search execution guardrails using `rg`."""

import json
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired
from unittest.mock import patch

import pytest

from edge_agent.app.tools.search import execute_search


def _rg_match_line(path: Path, line_number: int, text: str) -> str:
    return json.dumps(
        {
            "type": "match",
            "data": {
                "path": {"text": str(path)},
                "line_number": line_number,
                "lines": {"text": text},
            },
        }
    )


def test_execute_search_with_exact_literal_generates_rg_command(tmp_path):
    payload = {"exact_literal": "FindMe"}
    match_line = _rg_match_line(tmp_path / "file.txt", 2, "FindMe\n")
    completed = CompletedProcess(args=[], returncode=0, stdout=match_line, stderr="")

    with patch("edge_agent.app.tools.search.subprocess.run", return_value=completed) as mocked_run:
        result = execute_search(tmp_path, payload)

    assert result["error_code"] is None
    assert result["results"][0]["path"] == str(tmp_path / "file.txt")
    command = mocked_run.call_args[0][0]
    assert "--fixed-strings" in command
    assert "--ignore-case" in command
    assert "FindMe" in command


def test_execute_search_with_tokens_executes_multiple_patterns(tmp_path):
    payload = {"tokens": ["alpha", "beta"]}
    match_line = _rg_match_line(tmp_path / "file.txt", 1, "alpha beta\n")
    completed = CompletedProcess(args=[], returncode=0, stdout=match_line, stderr="")

    with patch("edge_agent.app.tools.search.subprocess.run", return_value=completed) as mocked_run:
        execute_search(tmp_path, payload)

    command = mocked_run.call_args[0][0]
    assert command.count("-e") == 2
    assert "alpha" in command
    assert "beta" in command


def test_execute_search_preserves_case_insensitive_flag(tmp_path):
    payload = {"tokens": ["case"]}
    match_line = _rg_match_line(tmp_path / "file.txt", 3, "CASE\n")
    completed = CompletedProcess(args=[], returncode=0, stdout=match_line, stderr="")

    with patch("edge_agent.app.tools.search.subprocess.run", return_value=completed) as mocked_run:
        execute_search(tmp_path, payload)

    assert "--ignore-case" in mocked_run.call_args[0][0]


def test_execute_search_never_returns_more_than_limit(tmp_path):
    payload = {"tokens": ["token"]}
    lines = [
        _rg_match_line(tmp_path / f"file_{i}.txt", i + 1, f"line {i}\n")
        for i in range(220)
    ]
    completed = CompletedProcess(
        args=[],
        returncode=0,
        stdout="\n".join(lines),
        stderr="",
    )

    with patch("edge_agent.app.tools.search.subprocess.run", return_value=completed):
        result = execute_search(tmp_path, payload)

    assert len(result["results"]) == 200


def test_execute_search_handles_timeout(tmp_path):
    payload = {"tokens": ["timeout"]}

    with patch(
        "edge_agent.app.tools.search.subprocess.run",
        side_effect=TimeoutExpired(cmd="rg", timeout=5),
    ):
        result = execute_search(tmp_path, payload)

    assert result["error_code"] == "SEARCH_FAILURE"
    assert result["results"] == []
