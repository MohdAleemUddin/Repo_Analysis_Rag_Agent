import pytest
import os
import tempfile
from pathlib import Path
from edge_agent.app.indexing.scan_rules import should_skip_path

@pytest.fixture
def test_root():
    """Fixture to provide a consistent absolute root path."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield os.path.abspath(tmp_dir)

def test_root_path_boundary_violation(test_root):
    """Test Rule 1: Boundary check."""
    # File path outside root_path
    outside_path = os.path.abspath(os.path.join(test_root, "..", "outside.txt"))
    assert should_skip_path(test_root, outside_path, is_dir=False) is True

@pytest.mark.parametrize("dir_name", [
    ".git", "node_modules", ".venv", "venv", "dist", "build", 
    ".pytest_cache", ".mypy_cache", ".idea", ".vscode"
])
def test_prd_excluded_directories(test_root, dir_name):
    """Test Rule 2: Directory exclusion."""
    dir_path = os.path.join(test_root, dir_name)
    assert should_skip_path(test_root, dir_path, is_dir=True) is True

@pytest.mark.parametrize("dir_name", [".GIT", ".VENV", "NODE_MODULES"])
def test_case_insensitive_directory_matching(test_root, dir_name):
    """Test Rule 2: Case-insensitive directory matching."""
    dir_path = os.path.join(test_root, dir_name)
    assert should_skip_path(test_root, dir_path, is_dir=True) is True

@pytest.mark.parametrize("extension", [
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico",
    # Media
    ".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav",
    # Archives
    ".zip", ".7z", ".rar", ".tar", ".gz",
    # Executables
    ".exe", ".dll", ".so", ".dylib",
    # DB
    ".db", ".sqlite", ".sqlite3"
])
def test_prd_excluded_extensions(test_root, extension):
    """Test Rule 3: File extension exclusion."""
    file_path = os.path.join(test_root, f"test_file{extension}")
    assert should_skip_path(test_root, file_path, is_dir=False) is True

@pytest.mark.parametrize("extension", [".JPG", ".MP4", ".ZIP", ".EXE", ".DB"])
def test_case_insensitive_extension_matching(test_root, extension):
    """Test Rule 3: Case-insensitive extension matching."""
    file_path = os.path.join(test_root, f"test_file{extension}")
    assert should_skip_path(test_root, file_path, is_dir=False) is True

@pytest.mark.parametrize("item, is_dir", [
    ("main.py", False),
    ("README.md", False),
    ("notes.txt", False),
    ("config.json", False),
    ("app.js", False),
    ("src", True),
    ("utils", True)
])
def test_non_excluded_items(test_root, item, is_dir):
    """Test Rule 4: Default behavior (negative tests)."""
    path = os.path.join(test_root, item)
    assert should_skip_path(test_root, path, is_dir=is_dir) is False

def test_nested_excluded_directory(test_root):
    """Test case for a nested excluded directory."""
    # Test path: "/project/src/utils/node_modules/package.json"
    # When checking the 'node_modules' directory component itself
    nested_dir = os.path.join(test_root, "src", "utils", "node_modules")
    assert should_skip_path(test_root, nested_dir, is_dir=True) is True
    
    # When checking a file inside that nested excluded directory (it should also be skipped by extension rule if applicable, 
    # but here we check if should_skip_path handles it correctly if called on the file path)
    nested_file = os.path.join(nested_dir, "package.json")
    # Note: should_skip_path only checks the basename if is_dir=True or extension if is_dir=False.
    # It doesn't walk up the parents. The traversal logic in indexer.py is responsible for skipping the whole tree.
    # However, Rule 1 (Boundary) still applies.
    assert should_skip_path(test_root, nested_file, is_dir=False) is False # package.json is not an excluded extension
