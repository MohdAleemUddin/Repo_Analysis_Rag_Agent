import json
from pathlib import Path

from edge_agent.app.indexing import manifest_store


def test_manifest_tracking_flow(monkeypatch, tmp_path: Path):
    repo_id = "repo456"
    base = tmp_path / "index_dir"
    monkeypatch.setattr(manifest_store, "resolve_index_dir", lambda: base)

    indexed = manifest_store.create_indexed_entry(
        path="repo/file_ok.py",
        mtime_epoch_ms=1,
        sha256="hash1",
        indexed_at_epoch_ms=11,
    )
    skipped = manifest_store.create_skipped_entry(
        path="repo/file_skip.bin",
        mtime_epoch_ms=2,
        sha256="hash2",
        indexed_at_epoch_ms=22,
        reason=manifest_store.SkipReason.BINARY,
    )

    manifest_store.write_manifest_entries(repo_id, [indexed, skipped])

    manifest_path = base / repo_id / "manifest.json"
    assert manifest_path.exists()

    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert raw == [indexed, skipped]

    reloaded = manifest_store.read_manifest_entries(repo_id)
    assert reloaded == [indexed, skipped]

    statuses = {entry["status"] for entry in reloaded}
    assert manifest_store.ManifestStatus.INDEXED.value in statuses
    assert manifest_store.ManifestStatus.SKIPPED.value in statuses

    for entry in reloaded:
        status = entry["status"]
        if status == manifest_store.ManifestStatus.SKIPPED.value:
            assert set(entry.keys()) == manifest_store.manifest_entry_keys(include_skip_reason=True)
            assert entry["skip_reason"] in [r.value for r in manifest_store.SkipReason]
        else:
            assert set(entry.keys()) == manifest_store.manifest_entry_keys()
            assert manifest_store.SKIP_REASON_FIELD not in entry
