import os
import sys
import json
import shutil
import tempfile
import subprocess
from pathlib import Path
import pytest

# Add the project root to sys.path to allow imports from edge_agent
repo_root = Path(__file__).resolve().parents[3]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from edge_agent.app.indexing.indexer import perform_indexing_scan, reset_indexing_stats
from edge_agent.app.indexing.scan_rules import normalize_root_path, compute_repo_id

@pytest.fixture
def e2e_env():
    """Fixture to set up and tear down an e2e test environment."""
    test_dir = tempfile.mkdtemp()
    index_dir = tempfile.mkdtemp()
    os.environ["RAG_INDEX_DIR"] = index_dir
    
    root_path = normalize_root_path(test_dir)
    repo_id = compute_repo_id(root_path)
    reset_indexing_stats()
    
    yield {
        "test_dir": test_dir,
        "index_dir": index_dir,
        "root_path": root_path,
        "repo_id": repo_id
    }
    
    shutil.rmtree(test_dir)
    shutil.rmtree(index_dir)
    if "RAG_INDEX_DIR" in os.environ:
        del os.environ["RAG_INDEX_DIR"]

def create_symlink(target, link_path, target_is_directory=False):
    """Helper to create symlinks/junctions cross-platform."""
    try:
        os.symlink(target, link_path, target_is_directory=target_is_directory)
        return True
    except (AttributeError, OSError):
        if sys.platform == "win32":
            # Fallback for Windows if os.symlink fails (e.g. no admin)
            cmd = ['mklink']
            if target_is_directory:
                cmd.append('/J') # Junction
            cmd.extend([link_path, target])
            result = subprocess.run(cmd, shell=True, capture_output=True)
            return result.returncode == 0
        return False

def test_symlink_skip_full_index_e2e(e2e_env):
    """End-to-end test for a full indexing scenario with symlinks."""
    test_dir = e2e_env["test_dir"]
    repo_id = e2e_env["repo_id"]
    
    # 1. Create a real directory structure
    src_dir = os.path.join(test_dir, "src")
    os.makedirs(src_dir)
    main_file = os.path.join(src_dir, "main.py")
    Path(main_file).touch()
    
    docs_dir = os.path.join(test_dir, "docs")
    os.makedirs(docs_dir)
    readme_file = os.path.join(docs_dir, "README.md")
    Path(readme_file).touch()
    
    # 2. Create symlinks
    # File symlink
    link_to_main = os.path.join(test_dir, "link_to_main.py")
    created_file_link = create_symlink(main_file, link_to_main)
    
    # Directory symlink
    link_to_docs = os.path.join(test_dir, "link_to_docs")
    created_dir_link = create_symlink(docs_dir, link_to_docs, target_is_directory=True)
    
    # Broken symlink
    broken_link = os.path.join(test_dir, "broken_link")
    created_broken_link = create_symlink(os.path.join(test_dir, "non_existent"), broken_link)
    
    # 3. Perform full indexing scan
    results = perform_indexing_scan(test_dir, repo_id)
    
    # 4. Verify indexing results
    # Should index: src/main.py, docs/README.md (2 files)
    assert results["indexed_files"] == 2
    
    # 5. Verify manifest records
    manifest_path = results.get("manifest_path")
    assert manifest_path and os.path.exists(manifest_path)
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
        
    entries = manifest_data.get("entries", [])
    symlink_entries = [e for e in entries if e.get("skip_reason") == "SYMLINK"]
    
    # Verify each successfully created link is in the manifest
    if created_file_link:
        assert any(e["path"] == normalize_root_path(link_to_main) for e in symlink_entries)
    if created_dir_link:
        assert any(e["path"] == normalize_root_path(link_to_docs) for e in symlink_entries)
    if created_broken_link:
        assert any(e["path"] == normalize_root_path(broken_link) for e in symlink_entries)
    
    assert all(e["status"] == "SKIPPED" for e in symlink_entries)
