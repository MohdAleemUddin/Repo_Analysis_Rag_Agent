import json
import os
import pytest
from pathlib import Path
from edge_agent.app.indexing.manifest_store import ManifestStore

def test_add_or_update_entry_skip_reason_other(tmp_path):
    """Verify that manifest can record SKIPPED with OTHER reason."""
    manifest_path = tmp_path / "manifest.json"
    store = ManifestStore(str(manifest_path))
    
    test_file = "path/to/file.py"
    store.add_or_update_entry(
        path=test_file,
        status="SKIPPED",
        skip_reason="OTHER"
    )
    store.save()
    
    with open(manifest_path, "r") as f:
        data = json.load(f)
    
    assert len(data["entries"]) == 1
    entry = data["entries"][0]
    assert entry["path"] == test_file
    assert entry["status"] == "SKIPPED"
    assert entry["skip_reason"] == "OTHER"

def test_add_or_update_entry_updates_existing(tmp_path):
    """Verify that add_or_update_entry updates an existing entry."""
    manifest_path = tmp_path / "manifest.json"
    store = ManifestStore(str(manifest_path))
    
    test_file = "path/to/file.py"
    # Add initial entry
    store.add_entry(path=test_file, status="INDEXED")
    
    # Update entry
    store.add_or_update_entry(
        path=test_file,
        status="SKIPPED",
        skip_reason="OTHER"
    )
    store.save()
    
    with open(manifest_path, "r") as f:
        data = json.load(f)
    
    assert len(data["entries"]) == 1
    entry = data["entries"][0]
    assert entry["path"] == test_file
    assert entry["status"] == "SKIPPED"
    assert entry["skip_reason"] == "OTHER"

def test_mixed_skip_reasons(tmp_path):
    """Verify that manifest can store mixed skip reasons."""
    manifest_path = tmp_path / "manifest.json"
    store = ManifestStore(str(manifest_path))
    
    store.add_or_update_entry(path="file1.py", status="SKIPPED", skip_reason="SIZE_CAP")
    store.add_or_update_entry(path="file2.py", status="SKIPPED", skip_reason="OTHER")
    store.add_or_update_entry(path="file3.py", status="INDEXED")
    store.add_or_update_entry(path="file4.py", status="SKIPPED", skip_reason="BINARY")
    
    store.save()
    
    with open(manifest_path, "r") as f:
        data = json.load(f)
    
    reasons = {e["path"]: e.get("skip_reason") for e in data["entries"]}
    statuses = {e["path"]: e["status"] for e in data["entries"]}
    
    assert statuses["file1.py"] == "SKIPPED"
    assert reasons["file1.py"] == "SIZE_CAP"
    
    assert statuses["file2.py"] == "SKIPPED"
    assert reasons["file2.py"] == "OTHER"
    
    assert statuses["file3.py"] == "INDEXED"
    assert reasons["file3.py"] is None
    
    assert statuses["file4.py"] == "SKIPPED"
    assert reasons["file4.py"] == "BINARY"
