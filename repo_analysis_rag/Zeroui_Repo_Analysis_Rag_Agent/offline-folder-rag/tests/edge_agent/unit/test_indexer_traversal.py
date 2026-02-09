import unittest
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Add the project root to sys.path to allow imports from edge_agent
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from edge_agent.app.indexing.indexer import perform_indexing_scan, reset_indexing_stats
from edge_agent.app.indexing.scan_rules import normalize_root_path, compute_repo_id

class TestIndexerTraversal(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Use a temporary directory for indexing to avoid permission issues in C:\Users\Hi
        self.index_dir = tempfile.mkdtemp()
        os.environ["RAG_INDEX_DIR"] = self.index_dir
        
        self.root_path = normalize_root_path(self.test_dir)
        self.repo_id = compute_repo_id(self.root_path)
        reset_indexing_stats()

    def tearDown(self):
        shutil.rmtree(self.test_dir)
        shutil.rmtree(self.index_dir)
        if "RAG_INDEX_DIR" in os.environ:
            del os.environ["RAG_INDEX_DIR"]

    def test_traversal_skips_excluded_directories(self):
        # Create a structure with allowed and excluded directories
        os.makedirs(os.path.join(self.test_dir, "src"))
        os.makedirs(os.path.join(self.test_dir, ".git"))
        os.makedirs(os.path.join(self.test_dir, "node_modules"))
        
        # Create files in each
        Path(os.path.join(self.test_dir, "src", "main.py")).touch()
        Path(os.path.join(self.test_dir, ".git", "config")).touch()
        Path(os.path.join(self.test_dir, "node_modules", "package.json")).touch()
        Path(os.path.join(self.test_dir, "README.md")).touch()

        results = perform_indexing_scan(self.test_dir, self.repo_id)
        
        # main.py and README.md should be indexed (2 files)
        # .git and node_modules should be skipped (2 directories)
        self.assertEqual(results["indexed_files"], 2)
        self.assertEqual(results["skipped_files"], 2)

    def test_traversal_skips_excluded_extensions(self):
        # Create allowed and excluded files
        Path(os.path.join(self.test_dir, "script.py")).touch()
        Path(os.path.join(self.test_dir, "image.png")).touch()
        Path(os.path.join(self.test_dir, "archive.zip")).touch()
        Path(os.path.join(self.test_dir, "notes.txt")).touch()

        results = perform_indexing_scan(self.test_dir, self.repo_id)
        
        # script.py and notes.txt should be indexed (2 files)
        # image.png and archive.zip should be skipped (2 files)
        self.assertEqual(results["indexed_files"], 2)
        self.assertEqual(results["skipped_files"], 2)

    def test_traversal_case_insensitivity(self):
        # Create directories and files with uppercase excluded names
        os.makedirs(os.path.join(self.test_dir, ".GIT"))
        Path(os.path.join(self.test_dir, "PHOTO.JPG")).touch()
        Path(os.path.join(self.test_dir, "allowed.py")).touch()

        results = perform_indexing_scan(self.test_dir, self.repo_id)
        
        # allowed.py should be indexed (1 file)
        # .GIT and PHOTO.JPG should be skipped (2 items)
        self.assertEqual(results["indexed_files"], 1)
        self.assertEqual(results["skipped_files"], 2)

    def test_symlink_manifest_recording(self):
        """Verify that symlinks are detected and skipped."""
        # Create a real file
        real_file = os.path.join(self.test_dir, "real.py")
        Path(real_file).touch()
    
        # Create a symlink to that file
        symlink_file = os.path.join(self.test_dir, "link.py")
        try:
            os.symlink(real_file, symlink_file)
        except (AttributeError, OSError):
            # Fallback for Windows if symlink creation fails without admin
            import subprocess
            subprocess.run(['mklink', symlink_file, real_file], shell=True)
    
        # Create a symlink directory
        real_dir = os.path.join(self.test_dir, "real_dir")
        os.makedirs(real_dir)
        symlink_dir = os.path.join(self.test_dir, "link_dir")
        try:
            os.symlink(real_dir, symlink_dir, target_is_directory=True)
        except (AttributeError, OSError):
            # Fallback for Windows junction
            import subprocess
            subprocess.run(['mklink', '/J', symlink_dir, real_dir], shell=True)
    
        results = perform_indexing_scan(self.test_dir, self.repo_id)
    
        # Only real.py should be indexed (1 file)
        self.assertEqual(results["indexed_files"], 1)
    
        # Verify manifest recording
        self.assertIn("manifest_path", results)
        m_path = results["manifest_path"]
        self.assertTrue(os.path.exists(m_path))
    
        import json
        with open(m_path, "r") as f:
            manifest_data = json.load(f)
    
        # Check for symlink entries in manifest
        entries = manifest_data.get("entries", [])
        symlink_entries = [e for e in entries if e.get("skip_reason") == "SYMLINK"]
    
        # On Windows without admin, symlink creation might fail but junction (/J) might succeed.
        # We check if at least one symlink/junction was recorded if any was successfully created.
        if os.path.islink(symlink_file) or os.path.islink(symlink_dir):
            self.assertGreater(len(symlink_entries), 0)
            for entry in symlink_entries:
                self.assertEqual(entry["status"], "SKIPPED")

if __name__ == "__main__":
    unittest.main()
