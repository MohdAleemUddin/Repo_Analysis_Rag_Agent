import json
import os
import pytest
from pathlib import Path
from edge_agent.app.indexing.config_store import RepoConfigStore

def test_get_max_files_default(monkeypatch, tmp_path):
    """Test default value when config is missing."""
    monkeypatch.setattr("edge_agent.app.indexing.config_store.index_dir", lambda: tmp_path)
    store = RepoConfigStore()
    assert store.get_max_files_per_incremental_run("test_repo") == 2000

def test_get_max_files_valid_config(monkeypatch, tmp_path):
    """Test valid config value."""
    repo_id = "test_repo"
    repo_dir = tmp_path / repo_id
    repo_dir.mkdir(parents=True)
    config_path = repo_dir / "config.json"
    with open(config_path, "w") as f:
        json.dump({"max_files_per_incremental_run": 500}, f)
    
    monkeypatch.setattr("edge_agent.app.indexing.config_store.index_dir", lambda: tmp_path)
    store = RepoConfigStore()
    assert store.get_max_files_per_incremental_run(repo_id) == 500

def test_get_max_files_invalid_config(monkeypatch, tmp_path):
    """Test invalid config value (negative, zero, non-int, float)."""
    repo_id = "test_repo"
    repo_dir = tmp_path / repo_id
    repo_dir.mkdir(parents=True)
    config_path = repo_dir / "config.json"
    
    monkeypatch.setattr("edge_agent.app.indexing.config_store.index_dir", lambda: tmp_path)
    store = RepoConfigStore()

    # Negative
    with open(config_path, "w") as f:
        json.dump({"max_files_per_incremental_run": -1}, f)
    assert store.get_max_files_per_incremental_run(repo_id) == 2000

    # Zero
    with open(config_path, "w") as f:
        json.dump({"max_files_per_incremental_run": 0}, f)
    assert store.get_max_files_per_incremental_run(repo_id) == 2000

    # Non-int string
    with open(config_path, "w") as f:
        json.dump({"max_files_per_incremental_run": "abc"}, f)
    assert store.get_max_files_per_incremental_run(repo_id) == 2000

    # Float
    with open(config_path, "w") as f:
        json.dump({"max_files_per_incremental_run": 3.14}, f)
    assert store.get_max_files_per_incremental_run(repo_id) == 2000

def test_get_max_files_malformed_json(monkeypatch, tmp_path):
    """Test malformed JSON in config file."""
    repo_id = "test_repo"
    repo_dir = tmp_path / repo_id
    repo_dir.mkdir(parents=True)
    config_path = repo_dir / "config.json"
    
    with open(config_path, "w") as f:
        f.write("{ invalid json")
    
    monkeypatch.setattr("edge_agent.app.indexing.config_store.index_dir", lambda: tmp_path)
    store = RepoConfigStore()
    assert store.get_max_files_per_incremental_run(repo_id) == 2000

def test_get_max_files_missing_field(monkeypatch, tmp_path):
    """Test config file missing the required field."""
    repo_id = "test_repo"
    repo_dir = tmp_path / repo_id
    repo_dir.mkdir(parents=True)
    config_path = repo_dir / "config.json"
    
    with open(config_path, "w") as f:
        json.dump({"other_field": 123}, f)
    
    monkeypatch.setattr("edge_agent.app.indexing.config_store.index_dir", lambda: tmp_path)
    store = RepoConfigStore()
    assert store.get_max_files_per_incremental_run(repo_id) == 2000

def test_get_max_files_valid_boundary_values(monkeypatch, tmp_path):
    """Test valid boundary values (1, 1000, 2000)."""
    repo_id = "test_repo"
    repo_dir = tmp_path / repo_id
    repo_dir.mkdir(parents=True)
    config_path = repo_dir / "config.json"
    
    monkeypatch.setattr("edge_agent.app.indexing.config_store.index_dir", lambda: tmp_path)
    store = RepoConfigStore()

    for val in [1, 1000, 2000]:
        with open(config_path, "w") as f:
            json.dump({"max_files_per_incremental_run": val}, f)
        assert store.get_max_files_per_incremental_run(repo_id) == val
