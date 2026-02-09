import unittest
import os
import sys
from pathlib import Path

# Add the project root to sys.path to allow imports from edge_agent
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from edge_agent.app.indexing.scan_rules import should_skip_path

class TestScanRulesExclusion(unittest.TestCase):
    def setUp(self):
        self.root_path = os.path.abspath("/mock/root")

    def test_boundary_check_inside(self):
        # Path inside root should not be skipped by boundary check
        file_path = os.path.join(self.root_path, "src", "main.py")
        self.assertFalse(should_skip_path(self.root_path, file_path, is_dir=False))

    def test_boundary_check_outside(self):
        # Path outside root should be skipped
        file_path = os.path.abspath("/mock/other/file.py")
        self.assertTrue(should_skip_path(self.root_path, file_path, is_dir=False))

    def test_directory_exclusion(self):
        # Excluded directories should be skipped
        excluded_dirs = [".git", "node_modules", ".venv", "venv", "dist", "build", ".pytest_cache", ".mypy_cache", ".idea", ".vscode"]
        for d in excluded_dirs:
            file_path = os.path.join(self.root_path, d)
            self.assertTrue(should_skip_path(self.root_path, file_path, is_dir=True), f"Directory {d} should be skipped")

    def test_directory_exclusion_case_insensitive(self):
        # Directory exclusion should be case-insensitive
        file_path = os.path.join(self.root_path, ".GIT")
        self.assertTrue(should_skip_path(self.root_path, file_path, is_dir=True))
        
        file_path = os.path.join(self.root_path, "NODE_MODULES")
        self.assertTrue(should_skip_path(self.root_path, file_path, is_dir=True))

    def test_file_extension_exclusion(self):
        # Excluded extensions should be skipped
        excluded_exts = [
            ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".ico",
            ".mp4", ".mov", ".avi", ".mkv", ".mp3", ".wav",
            ".zip", ".7z", ".rar", ".tar", ".gz",
            ".exe", ".dll", ".so", ".dylib",
            ".db", ".sqlite", ".sqlite3"
        ]
        for ext in excluded_exts:
            file_path = os.path.join(self.root_path, f"file{ext}")
            self.assertTrue(should_skip_path(self.root_path, file_path, is_dir=False), f"Extension {ext} should be skipped")

    def test_file_extension_exclusion_case_insensitive(self):
        # Extension exclusion should be case-insensitive
        file_path = os.path.join(self.root_path, "image.JPG")
        self.assertTrue(should_skip_path(self.root_path, file_path, is_dir=False))
        
        file_path = os.path.join(self.root_path, "archive.ZIP")
        self.assertTrue(should_skip_path(self.root_path, file_path, is_dir=False))

    def test_default_allowed(self):
        # Normal files and directories should not be skipped
        self.assertFalse(should_skip_path(self.root_path, os.path.join(self.root_path, "src"), is_dir=True))
        self.assertFalse(should_skip_path(self.root_path, os.path.join(self.root_path, "README.md"), is_dir=False))
        self.assertFalse(should_skip_path(self.root_path, os.path.join(self.root_path, "main.py"), is_dir=False))

if __name__ == "__main__":
    unittest.main()
