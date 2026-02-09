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
from edge_agent.app.indexing.scan_rules import normalize_root_path, compute_repo_id, is_symlink_entry

@pytest.fixture
def test_env():
    """Fixture to set up and tear down a test environment."""
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

def test_is_symlink_entry_detection(test_env):
    """Verify detection of files, directories, and symlinks."""
    test_dir = test_env["test_dir"]
    
    # 1. Real file
    real_file = os.path.join(test_dir, "real_file.txt")
    Path(real_file).touch()
    assert is_symlink_entry(real_file) is False
    
    # 2. Real directory
    real_dir = os.path.join(test_dir, "real_dir")
    os.makedirs(real_dir)
    assert is_symlink_entry(real_dir) is False
    
    # 3. File symlink
    link_file = os.path.join(test_dir, "link_file.txt")
    if create_symlink(real_file, link_file):
        assert is_symlink_entry(link_file) is True
        
    # 4. Directory symlink/junction
    link_dir = os.path.join(test_dir, "link_dir")
    if create_symlink(real_dir, link_dir, target_is_directory=True):
        assert is_symlink_entry(link_dir) is True

def test_is_symlink_entry_broken_link(test_env):
    """Verify that broken symlinks are detected without exceptions."""
    test_dir = test_env["test_dir"]
    
    target = os.path.join(test_dir, "non_existent.txt")
    link_path = os.path.join(test_dir, "broken_link.txt")
    
    if create_symlink(target, link_path):
        assert is_symlink_entry(link_path) is True
        # Ensure it doesn't exist but is a link
        assert os.path.exists(link_path) is False

def test_indexer_skips_symlinks(test_env):
    """Verify perform_indexing_scan does not index or follow symlinks."""
    test_dir = test_env["test_dir"]
    repo_id = test_env["repo_id"]
    
    # Create real structure
    real_file = os.path.join(test_dir, "real.py")
    Path(real_file).touch()
    
    # Create symlink file
    link_file = os.path.join(test_dir, "link.py")
    create_symlink(real_file, link_file)
    
    # Create symlink directory containing a file
    real_dir = os.path.join(test_dir, "real_dir")
    os.makedirs(real_dir)
    Path(os.path.join(real_dir, "inside.py")).touch()
    
    link_dir = os.path.join(test_dir, "link_dir")
    create_symlink(real_dir, link_dir, target_is_directory=True)
    
    results = perform_indexing_scan(test_dir, repo_id)
    
    # Should only index: real.py, real_dir/inside.py (2 files)
    # Should NOT index: link.py, link_dir/ (and anything inside link_dir/)
    assert results["indexed_files"] == 2

def test_manifest_records_symlink_skip(test_env):
    """Verify manifest.json contains SYMLINK skip records."""
    test_dir = test_env["test_dir"]
    repo_id = test_env["repo_id"]
    
    real_file = os.path.join(test_dir, "real.txt")
    Path(real_file).touch()
    
    link_file = os.path.join(test_dir, "link.txt")
    created = create_symlink(real_file, link_file)
    
    results = perform_indexing_scan(test_dir, repo_id)
    
    manifest_path = results.get("manifest_path")
    assert manifest_path and os.path.exists(manifest_path)
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
        
    entries = manifest_data.get("entries", [])
    symlink_entries = [e for e in entries if e.get("skip_reason") == "SYMLINK"]
    
    if created:
        assert len(symlink_entries) >= 1
        assert any(e["path"] == normalize_root_path(link_file) for e in symlink_entries)
        assert all(e["status"] == "SKIPPED" for e in symlink_entries)

def test_symlink_precedence(test_env):
    """Verify symlink skip takes precedence over other exclusion rules."""
    test_dir = test_env["test_dir"]
    repo_id = test_env["repo_id"]
    
    # Create a directory that would normally be excluded (e.g., .git)
    # But we create a symlink TO it with a different name
    git_dir = os.path.join(test_dir, ".git")
    os.makedirs(git_dir)
    
    # Add a file inside .git to see if it gets indexed (it shouldn't)
    Path(os.path.join(git_dir, "config")).touch()
    
    link_to_git = os.path.join(test_dir, "my_git_link")
    created = create_symlink(git_dir, link_to_git, target_is_directory=True)
    
    results = perform_indexing_scan(test_dir, repo_id)
    
    # .git/config should NOT be indexed because .git is excluded
    # my_git_link should NOT be indexed because it's a symlink
    assert results["indexed_files"] == 0
    
    with open(results["manifest_path"], "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
        
    entries = manifest_data.get("entries", [])
    
    # The link_to_git should be skipped with SYMLINK because symlink check is first.
    symlink_entries = [e for e in entries if e.get("skip_reason") == "SYMLINK"]
    
    if created:
        # Normalize paths for comparison
        norm_link_path = normalize_root_path(link_to_git)
        assert any(e["path"] == norm_link_path for e in symlink_entries)
