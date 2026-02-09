"""Deterministic search ranking coverage aligned with PRD §15.3."""

from pathlib import Path
from subprocess import CompletedProcess

import pytest

from edge_agent.app.tools import search as search_module


def _normalized_match(path: str, line_text: str, line_number: int = 1) -> dict:
    return {
        "path": path,
        "basename": Path(path).name,
        "line_number": line_number,
        "line_text": line_text,
    }


def test_filename_match_scoring_only():
    match = _normalized_match("repo/other/token_file.py", "no match")
    score = search_module._compute_match_score(match, "token")
    assert score == search_module.FILENAME_MATCH_SCORE


def test_whole_word_line_scoring_only():
    match = _normalized_match("repo/other/file.py", "token is present")
    score = search_module._compute_match_score(match, "token")
    assert score == search_module.LINE_MATCH_SCORE


def test_path_keyword_scoring_only():
    match = _normalized_match("repo/src/file.py", "quiet line")
    score = search_module._compute_match_score(match, "token")
    assert score == search_module.PATH_KEYWORD_SCORE


def test_combined_scoring_adds_all_components():
    match = _normalized_match("repo/app/token_line.py", "token occurs here")
    score = search_module._compute_match_score(match, "token")
    expected = (
        search_module.FILENAME_MATCH_SCORE
        + search_module.LINE_MATCH_SCORE
        + search_module.PATH_KEYWORD_SCORE
    )
    assert score == expected


def _patch_run_and_parse(monkeypatch, matches):
    monkeypatch.setattr(
        search_module,
        "_parse_rg_output",
        lambda *_: [match.copy() for match in matches],
    )
    monkeypatch.setattr(
        search_module.subprocess,
        "run",
        lambda *args, **kwargs: CompletedProcess(args=args, returncode=0, stdout="", stderr=""),
    )


def test_deterministic_ordering_when_scores_tie(monkeypatch, tmp_path):
    matches = [
        _normalized_match("z/path/token_file.py", "token occurs twice", line_number=5),
        _normalized_match("a/path/token_file.py", "token occurs twice", line_number=2),
    ]
    _patch_run_and_parse(monkeypatch, matches)
    response = search_module.execute_search(
        tmp_path,
        {"tokens": ["token"]},
    )
    paths = [match["path"] for match in response["results"]]
    assert paths == ["a/path/token_file.py", "z/path/token_file.py"]


def test_truncates_at_result_cap(monkeypatch, tmp_path):
    matches = [
        _normalized_match(f"repo/file_{i}.py", "token", line_number=i)
        for i in range(search_module._RESULT_CAP + 1)
    ]
    _patch_run_and_parse(monkeypatch, matches)
    response = search_module.execute_search(tmp_path, {"tokens": ["token"]})
    assert len(response["results"]) == search_module._RESULT_CAP

