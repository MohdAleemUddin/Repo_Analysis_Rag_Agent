import unittest
import os
import sys
import tempfile
import shutil
import json
from pathlib import Path

# Add the project root to sys.path to allow imports from edge_agent
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from edge_agent.app.indexing.indexer import perform_indexing_scan, reset_indexing_stats
from edge_agent.app.indexing.scan_rules import normalize_root_path, compute_repo_id

class TestUTF8Fallback(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
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

    def test_utf8_fallback_tagging(self):
        """Verify that files with invalid UTF-8 are tagged with utf-8-replace."""
        # 1. Valid UTF-8 file
        valid_file = os.path.join(self.test_dir, "valid.txt")
        with open(valid_file, "w", encoding="utf-8") as f:
            f.write("This is valid UTF-8.")

        # 2. Invalid UTF-8 file (contains invalid sequence \xff)
        invalid_file = os.path.join(self.test_dir, "invalid.txt")
        with open(invalid_file, "wb") as f:
            f.write(b"Invalid UTF-8 sequence: \xff")

        results = perform_indexing_scan(self.test_dir, self.repo_id)

        # Both should be indexed
        self.assertEqual(results["indexed_files"], 2)

        # Verify manifest
        m_path = results["manifest_path"]
        with open(m_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        entries = manifest_data.get("entries", [])
        
        # Check valid file entry
        norm_valid = normalize_root_path(valid_file)
        valid_entry = next((e for e in entries if e["path"] == norm_valid), None)
        self.assertIsNotNone(valid_entry)
        self.assertEqual(valid_entry["status"], "INDEXED")
        self.assertNotIn("encoding", valid_entry) # Should not have encoding tag if valid
        self.assertIn("mtime_epoch_ms", valid_entry)
        self.assertIn("indexed_at_epoch_ms", valid_entry)

        # Check invalid file entry
        norm_invalid = normalize_root_path(invalid_file)
        invalid_entry = next((e for e in entries if e["path"] == norm_invalid), None)
        self.assertIsNotNone(invalid_entry)
        self.assertEqual(invalid_entry["status"], "INDEXED")
        self.assertEqual(invalid_entry.get("encoding"), "utf-8-replace")
        self.assertIn("mtime_epoch_ms", invalid_entry)
        self.assertIn("indexed_at_epoch_ms", invalid_entry)

if __name__ == "__main__":
    unittest.main()
