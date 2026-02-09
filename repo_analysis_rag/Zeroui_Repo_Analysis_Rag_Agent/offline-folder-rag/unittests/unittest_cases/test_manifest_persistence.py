import json
from pathlib import Path

from edge_agent.app.indexing import manifest_store


def test_manifest_entries_persist_and_reload(monkeypatch, tmp_path: Path):
    repo_id = "repo123"
    base = tmp_path / "index_dir"
    monkeypatch.setattr(manifest_store, "resolve_index_dir", lambda: base)

    e1 = manifest_store.create_indexed_entry(
        path="repo/file1.py",
        mtime_epoch_ms=1,
        sha256="aaa",
        indexed_at_epoch_ms=10,
    )
    e2 = manifest_store.create_skipped_entry(
        path="repo/file2.py",
        mtime_epoch_ms=2,
        sha256="bbb",
        indexed_at_epoch_ms=20,
        reason=manifest_store.SkipReason.EXCLUDED_EXT,
    )

    written_path = manifest_store.write_manifest_entries(repo_id, [e1, e2])

    expected_path = base / repo_id / "manifest.json"
    assert written_path == expected_path
    assert expected_path.exists()

    raw = json.loads(expected_path.read_text(encoding="utf-8"))
    assert raw == [e1, e2]

    reloaded = manifest_store.read_manifest_entries(repo_id)
    assert reloaded == [e1, e2]
