import json
import os
import tempfile
from pathlib import Path
from edge_agent.app.indexing.manifest_store import ManifestStore

def test_manifest_size_cap_serialization():
    """Verify that manifest entries correctly reflect skip_reason: 'SIZE_CAP'."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        manifest_path = os.path.join(tmp_dir, "manifest.json")
        store = ManifestStore(manifest_path)
        
        test_path = "test/large_file.py"
        store.add_entry(
            path=test_path,
            status="SKIPPED",
            skip_reason=ManifestStore.SIZE_CAP
        )
        store.save()
        
        # Verify file exists
        assert os.path.exists(manifest_path)
        
        # Read and verify content
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        assert "entries" in data
        assert len(data["entries"]) == 1
        entry = data["entries"][0]
        assert entry["path"] == test_path
        assert entry["status"] == "SKIPPED"
        assert entry["skip_reason"] == "SIZE_CAP"
