import unittest
import os
import sys
import hashlib
import tempfile
import shutil

# Add current directory to path to allow imports from edge_agent
sys.path.append(os.getcwd())

from edge_agent.app.indexing.scan_rules import normalize_root_path, compute_repo_id, scan_repository

class TestPathNormalizeRepoId(unittest.TestCase):
    def setUp(self):
        self.index_dir = tempfile.mkdtemp()
        os.environ["RAG_INDEX_DIR"] = self.index_dir

    def tearDown(self):
        shutil.rmtree(self.index_dir)
        if "RAG_INDEX_DIR" in os.environ:
            del os.environ["RAG_INDEX_DIR"]

    def test_normalize_root_path_basic(self):
        # Basic normalization
        path = "C:/test/../test"
        # os.path.abspath will make it absolute based on current CWD, 
        # but the logic should handle the relative parts and slashes.
        normalized = normalize_root_path(path)
        self.assertTrue(normalized.endswith("test"))
        self.assertNotIn("/", normalized)
        self.assertEqual(normalized, normalized.lower())

    def test_normalize_root_path_slashes(self):
        # Forward slashes to backslashes
        path = "C:/users/test/folder/"
        normalized = normalize_root_path(path)
        self.assertIn("\\", normalized)
        self.assertFalse(normalized.endswith("\\"))
        self.assertEqual(normalized, normalized.lower())

    def test_normalize_root_path_drive_root(self):
        # Drive root should keep backslash
        path = "C:/"
        normalized = normalize_root_path(path)
        self.assertEqual(normalized, "c:\\")

    def test_normalize_root_path_empty(self):
        # Empty input validation
        with self.assertRaises(ValueError) as cm:
            normalize_root_path("")
        self.assertEqual(str(cm.exception), "Invalid root path: path cannot be empty")
        
        with self.assertRaises(ValueError) as cm:
            normalize_root_path(None)
        self.assertEqual(str(cm.exception), "Invalid root path: path cannot be empty")

    def test_compute_repo_id_consistency(self):
        # SHA256 consistency
        path = "c:\\test\\path"
        repo_id1 = compute_repo_id(path)
        repo_id2 = compute_repo_id(path)
        
        expected_hash = hashlib.sha256(path.encode('utf-8')).hexdigest().lower()
        self.assertEqual(repo_id1, expected_hash)
        self.assertEqual(repo_id1, repo_id2)

    def test_compute_repo_id_lowercase(self):
        path = "c:\\test\\path"
        repo_id = compute_repo_id(path)
        self.assertEqual(repo_id, repo_id.lower())

    def test_scan_repository_repo_id_structure(self):
        # Verify that scan_repository creates correct repo_id structure
        root_path = "C:/test_repo"
        results = scan_repository(root_path)
        
        normalized = normalize_root_path(root_path)
        expected_repo_id = compute_repo_id(normalized)
        
        self.assertEqual(results["repo_id"], expected_repo_id)
        self.assertIn(expected_repo_id, results["manifest_path"])
        self.assertTrue(results["manifest_path"].endswith("manifest.json"))
        
        for collection in results["collections"]:
            self.assertTrue(collection.startswith(expected_repo_id))
            self.assertTrue(collection.endswith("_chunks"))

if __name__ == "__main__":
    unittest.main()
