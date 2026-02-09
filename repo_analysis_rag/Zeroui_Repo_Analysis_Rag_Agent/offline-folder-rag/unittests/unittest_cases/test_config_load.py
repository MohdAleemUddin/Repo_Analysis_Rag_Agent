import pytest
from edge_agent.app.indexing.config_store import ConfigStore

def test_config_defaults():
    """Test that default configuration values are correctly set."""
    config = ConfigStore()
    assert config.max_file_size_mb == 5
    assert config.chunk_size == 1000
    assert config.chunk_overlap == 200

def test_config_override():
    """Test that configuration values can be overridden."""
    custom_config = {"max_file_size_mb": 10}
    config = ConfigStore(custom_config)
    assert config.max_file_size_mb == 10
    assert config.chunk_size == 1000  # Should remain default

def test_config_max_file_size_mb_equals_5_when_unspecified():
    """Assert that config.max_file_size_mb equals 5 when unspecified by user config."""
    config = ConfigStore({})
    assert config.max_file_size_mb == 5

def test_config_allowed_max_file_size_mb():
    """Test that only 5, 10, and 20 are allowed for max_file_size_mb."""
    for val in [5, 10, 20]:
        config = ConfigStore({"max_file_size_mb": val})
        assert config.max_file_size_mb == val
    
    with pytest.raises(ValueError, match=r"max_file_size_mb must be one of"):
        ConfigStore({"max_file_size_mb": 15})

def test_scan_rules_enforces_max_file_size():
    """Assert that scanning uses configured value."""
    import tempfile
    import os
    from edge_agent.app.indexing.scan_rules import should_skip_path_with_reason
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as tmp:
        tmp.write(b"a" * (7 * 1024 * 1024)) # 7MB
        tmp_path = tmp.name
    
    try:
        root = os.path.dirname(tmp_path)
        # Should skip if max is 5
        skip, reason = should_skip_path_with_reason(root, tmp_path, is_dir=False, max_file_size_mb=5)
        assert skip is True
        assert reason == "SIZE_CAP"
        # Should NOT skip if max is 10
        skip, reason = should_skip_path_with_reason(root, tmp_path, is_dir=False, max_file_size_mb=10)
        assert skip is False
    finally:
        os.remove(tmp_path)

def test_code_file_fixed_5mb_cap():
    """Verify that code/other file size uses fixed 5MB cap regardless of config."""
    import tempfile
    import os
    from edge_agent.app.indexing.scan_rules import should_skip_path_with_reason
    
    # .py file is "code"
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as tmp:
        tmp.write(b"a" * (7 * 1024 * 1024)) # 7MB
        tmp_path = tmp.name
    
    try:
        root = os.path.dirname(tmp_path)
        # Should skip even if max_file_size_mb is 10 (because code is fixed at 5MB)
        skip, reason = should_skip_path_with_reason(root, tmp_path, is_dir=False, max_file_size_mb=10)
        assert skip is True
        assert reason == "SIZE_CAP"
    finally:
        os.remove(tmp_path)

def test_manifest_size_cap_reason(monkeypatch):
    """Assert manifest entry has skip_reason exactly 'SIZE_CAP'."""
    import tempfile
    import os
    import json
    from pathlib import Path
    from edge_agent.app.indexing.indexer import perform_indexing_scan
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Mock index_dir to use a temporary directory
        mock_index = Path(tmp_dir) / "index"
        monkeypatch.setattr("edge_agent.app.indexing.scan_rules.index_dir", lambda: mock_index)
        
        # Create a large file
        large_file = os.path.join(tmp_dir, "large.py")
        with open(large_file, "wb") as f:
            f.write(b"a" * (6 * 1024 * 1024))
        
        repo_id = "test_repo"
        results = perform_indexing_scan(tmp_dir, repo_id)
        manifest_path = results["manifest_path"]
        
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
            
        found = False
        for entry in manifest["entries"]:
            if entry["path"].endswith("large.py"):
                assert entry["status"] == "SKIPPED"
                assert entry["skip_reason"] == "SIZE_CAP"
                found = True
                break
        assert found, "Large file not found in manifest"
