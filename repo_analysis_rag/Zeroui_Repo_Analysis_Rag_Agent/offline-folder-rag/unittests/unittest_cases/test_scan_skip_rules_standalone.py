import os
import tempfile
import pytest


def scan_file(file_path):
    if file_path.endswith(".git") or "/.git/" in file_path:
        return "EXCLUDED_DIR"
    if file_path.endswith(".log"):
        return "EXCLUDED_EXT"
    if os.path.islink(file_path):
        return "SYMLINK"
    with open(file_path, "rb") as file:
        chunk = file.read(4096)
        if b"\x00" in chunk:
            return "BINARY"
    return "INCLUDED"


def test_excluded_dir():
    file_path = "/path/to/.git/file"
    result = scan_file(file_path)
    assert result == "EXCLUDED_DIR"


def test_excluded_ext():
    file_path = "/path/to/file.log"
    result = scan_file(file_path)
    assert result == "EXCLUDED_EXT"


def test_symlink(mocker):
    # Mock os.path.islink to return True for a dummy path
    file_path = "/path/to/symlink"
    mocker.patch("os.path.islink", return_value=True)
    result = scan_file(file_path)
    assert result == "SYMLINK"


def test_binary_file():
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"\x00" * 100)
        temp_file_path = temp_file.name

    try:
        result = scan_file(temp_file_path)
        assert result == "BINARY"
    finally:
        os.remove(temp_file_path)
