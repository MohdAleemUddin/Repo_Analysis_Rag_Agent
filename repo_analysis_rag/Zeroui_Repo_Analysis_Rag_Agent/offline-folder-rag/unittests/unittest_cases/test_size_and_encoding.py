import os
import tempfile


def scan_file(file_path):
    if os.path.getsize(file_path) > 5 * 1024 * 1024:
        return "SIZE_EXCEEDED"

    try:
        with open(file_path, "r", encoding="utf-8", errors="strict") as f:
            f.read()
    except UnicodeDecodeError:
        return "ENCODING_ERROR"

    return "INCLUDED"


def test_skip_large_file():
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"a" * (6 * 1024 * 1024))
        temp_file_path = temp_file.name
    try:
        result = scan_file(temp_file_path)
        assert result == "SIZE_EXCEEDED"
    finally:
        os.remove(temp_file_path)


def test_encoding_error():
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"\x80\x81\x82")
        temp_file_path = temp_file.name
    try:
        result = scan_file(temp_file_path)
        assert result == "ENCODING_ERROR"
    finally:
        os.remove(temp_file_path)


def test_valid_utf8_file():
    with tempfile.NamedTemporaryFile(delete=False, mode="w", encoding="utf-8") as temp_file:
        temp_file.write("Valid UTF-8 content.")
        temp_file_path = temp_file.name
    try:
        result = scan_file(temp_file_path)
        assert result == "INCLUDED"
    finally:
        os.remove(temp_file_path)
import pytest
import os
import tempfile
from pathlib import Path

# Mock function to simulate scanning a file and checking its size and encoding
def scan_file(file_path):
    if os.path.getsize(file_path) > 5 * 1024 * 1024:  # File size > 5MB
        return 'SIZE_EXCEEDED'

    try:
        Path(file_path).read_bytes().decode('utf-8')
    except UnicodeDecodeError:
        return 'ENCODING_ERROR'

    return 'INCLUDED'

# Test Case 1: Skip file exceeding size limit (e.g., 6MB)
def test_skip_large_file():
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b'a' * (6 * 1024 * 1024))  # Write 6MB of data
        temp_file_path = temp_file.name
        temp_file.flush()
        result = scan_file(temp_file_path)
    assert result == 'SIZE_EXCEEDED'
    os.remove(temp_file_path)

# Test Case 2: Handle malformed UTF-8 encoding gracefully
def test_encoding_error():
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b'\x80\x81\x82')  # Invalid UTF-8 sequence
        temp_file_path = temp_file.name
        temp_file.flush()
        result = scan_file(temp_file_path)
    assert result == 'ENCODING_ERROR'
    os.remove(temp_file_path)

# Test Case 3: Valid UTF-8 file should be included
def test_valid_utf8_file():
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
        temp_file.write("Valid UTF-8 content.")
        temp_file_path = temp_file.name
        temp_file.flush()
        result = scan_file(temp_file_path)
    assert result == 'INCLUDED'
    os.remove(temp_file_path)
