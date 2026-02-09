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
from edge_agent.app.indexing.manifest_store import ManifestStore

class TestBinaryDetection(unittest.TestCase):
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

    def test_binary_detection_cases(self):
        """Verify binary detection logic and skip_reason recording."""
        
        # 1. File with \x00 at position 0 → BINARY
        bin_pos0 = os.path.join(self.test_dir, "bin_pos0.dat")
        with open(bin_pos0, "wb") as f:
            f.write(b"\x00" + b"A" * 4095)

        # 2. File with \x00 at position 4095 → BINARY
        bin_pos4095 = os.path.join(self.test_dir, "bin_pos4095.dat")
        with open(bin_pos4095, "wb") as f:
            f.write(b"A" * 4095 + b"\x00")

        # 3. File with \x00 at position 4096 → NOT BINARY (outside first 4KB)
        not_bin_pos4096 = os.path.join(self.test_dir, "not_bin_pos4096.dat")
        with open(not_bin_pos4096, "wb") as f:
            f.write(b"A" * 4096 + b"\x00")

        # 4. File with no null bytes → NOT BINARY
        text_file = os.path.join(self.test_dir, "text_file.txt")
        with open(text_file, "w") as f:
            f.write("This is a normal text file with no null bytes.")

        results = perform_indexing_scan(self.test_dir, self.repo_id)

        # bin_pos0 and bin_pos4095 should be skipped (2 files)
        # not_bin_pos4096 and text_file should be indexed (2 files)
        self.assertEqual(results["skipped_files"], 2)
        self.assertEqual(results["indexed_files"], 2)

        # Verify manifest
        m_path = results["manifest_path"]
        with open(m_path, "r") as f:
            manifest_data = json.load(f)
        
        entries = manifest_data.get("entries", [])
        
        # Verify bin_pos0
        entry0 = next((e for e in entries if "bin_pos0.dat" in e["path"]), None)
        self.assertIsNotNone(entry0)
        self.assertEqual(entry0["status"], "SKIPPED")
        self.assertEqual(entry0["skip_reason"], ManifestStore.BINARY)

        # Verify bin_pos4095
        entry4095 = next((e for e in entries if "bin_pos4095.dat" in e["path"]), None)
        self.assertIsNotNone(entry4095)
        self.assertEqual(entry4095["status"], "SKIPPED")
        self.assertEqual(entry4095["skip_reason"], ManifestStore.BINARY)

        # Verify not_bin_pos4096 (should be INDEXED)
        entry4096 = next((e for e in entries if "not_bin_pos4096.dat" in e["path"]), None)
        self.assertIsNotNone(entry4096)
        self.assertEqual(entry4096["status"], "INDEXED")

        # Verify text_file (should be INDEXED)
        entry_text = next((e for e in entries if "text_file.txt" in e["path"]), None)
        self.assertIsNotNone(entry_text)
        self.assertEqual(entry_text["status"], "INDEXED")

if __name__ == "__main__":
    unittest.main()
