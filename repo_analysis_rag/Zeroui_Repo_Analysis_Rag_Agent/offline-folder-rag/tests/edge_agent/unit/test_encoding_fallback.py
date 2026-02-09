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

class TestEncodingFallback(unittest.TestCase):
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

    def test_encoding_fallback_cases(self):
        """Verify encoding fallback and utf-8-replace tagging."""
        
        # 1. Valid UTF-8 file
        valid_utf8 = os.path.join(self.test_dir, "valid_utf8.txt")
        with open(valid_utf8, "w", encoding="utf-8") as f:
            f.write("This is a valid UTF-8 file.")

        # 2. Invalid UTF-8 file (contains invalid sequence \xff)
        invalid_utf8 = os.path.join(self.test_dir, "invalid_utf8.txt")
        with open(invalid_utf8, "wb") as f:
            f.write(b"Invalid sequence: \xff")

        # 3. Mixed valid/invalid content
        mixed_content = os.path.join(self.test_dir, "mixed_content.txt")
        with open(mixed_content, "wb") as f:
            f.write("Valid start ".encode("utf-8") + b"\xfe\xff" + " Valid end".encode("utf-8"))

        # 4. Empty file
        empty_file = os.path.join(self.test_dir, "empty.txt")
        with open(empty_file, "wb") as f:
            pass

        results = perform_indexing_scan(self.test_dir, self.repo_id)

        # All 4 files should be indexed (none skipped due to encoding)
        self.assertEqual(results["indexed_files"], 4)
        self.assertEqual(results["skipped_files"], 0)

        # Verify manifest
        m_path = results["manifest_path"]
        with open(m_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        
        entries = manifest_data.get("entries", [])
        
        # Helper to find entry by filename
        def get_entry(full_path):
            norm_path = normalize_root_path(full_path)
            return next((e for e in entries if e["path"] == norm_path), None)

        # Verify valid_utf8.txt
        entry_valid = get_entry(valid_utf8)
        self.assertIsNotNone(entry_valid)
        self.assertEqual(entry_valid["status"], "INDEXED")
        self.assertIn("mtime_epoch_ms", entry_valid)
        self.assertIn("indexed_at_epoch_ms", entry_valid)
        # Should have no encoding tag or encoding="utf-8"
        encoding = entry_valid.get("encoding")
        self.assertTrue(encoding is None or encoding == "utf-8")

        # Verify invalid_utf8.txt
        entry_invalid = get_entry(invalid_utf8)
        self.assertIsNotNone(entry_invalid)
        self.assertEqual(entry_invalid["status"], "INDEXED")
        self.assertEqual(entry_invalid.get("encoding"), "utf-8-replace")
        self.assertIn("mtime_epoch_ms", entry_invalid)
        self.assertIn("indexed_at_epoch_ms", entry_invalid)

        # Verify mixed_content.txt
        entry_mixed = get_entry(mixed_content)
        self.assertIsNotNone(entry_mixed)
        self.assertEqual(entry_mixed["status"], "INDEXED")
        self.assertEqual(entry_mixed.get("encoding"), "utf-8-replace")
        self.assertIn("mtime_epoch_ms", entry_mixed)
        self.assertIn("indexed_at_epoch_ms", entry_mixed)

        # Verify empty.txt
        entry_empty = get_entry(empty_file)
        self.assertIsNotNone(entry_empty)
        self.assertEqual(entry_empty["status"], "INDEXED")
        self.assertIn("mtime_epoch_ms", entry_empty)
        self.assertIn("indexed_at_epoch_ms", entry_empty)

if __name__ == "__main__":
    unittest.main()
