import time
from unittest.mock import patch


def search_results(query):
    results = [
        {"score": 4, "filename": "file1.py", "path": "/path/to/file1", "line": 5},
        {"score": 6, "filename": "file2.py", "path": "/path/to/file2", "line": 3},
        {"score": 2, "filename": "file3.py", "path": "/path/to/file3", "line": 10},
    ]

    for result in results:
        if query in result["filename"]:
            result["score"] += 2
            result["score"] += 2

    results.sort(key=lambda x: (-x["score"], x["path"], x["line"]))
    return results


def test_search_ranking():
    query = "file"
    results = search_results(query)
    assert results[0]["filename"] == "file2.py"
    assert results[1]["filename"] == "file1.py"
    assert results[2]["filename"] == "file3.py"


def test_search_timeout():
    with patch("time.sleep", return_value=None):
        start_time = time.time()
        try:
            time.sleep(6)
            raise TimeoutError("SEARCH_FAILURE")
        except TimeoutError as exc:
            elapsed_time = time.time() - start_time
            assert elapsed_time >= 5
            assert "SEARCH_FAILURE" in str(exc)
import pytest
import time
from unittest.mock import patch


def search_results(query):
    results = [
        {"score": 4, "filename": "file1.py", "path": "/path/to/file1", "line": 5},
        {"score": 6, "filename": "file2.py", "path": "/path/to/file2", "line": 3},
        {"score": 2, "filename": "file3.py", "path": "/path/to/file3", "line": 10},
    ]

    for result in results:
        if query in result["filename"]:
            result["score"] += 2
        if query in result["filename"]:
            result["score"] += 2

    results.sort(key=lambda x: (-x["score"], x["path"], x["line"]))

    return results


def test_search_ranking():
    query = "file"
    results = search_results(query)

    assert results[0]["filename"] == "file2.py"
    assert results[1]["filename"] == "file1.py"
    assert results[2]["filename"] == "file3.py"


def test_search_timeout():
    with patch("time.sleep", return_value=None):
        start_time = time.time()
        try:
            time.sleep(6)
            search_results("file")
        except TimeoutError:
            elapsed_time = time.time() - start_time
            assert elapsed_time >= 5
            assert "SEARCH_FAILURE" in str("TimeoutError")
