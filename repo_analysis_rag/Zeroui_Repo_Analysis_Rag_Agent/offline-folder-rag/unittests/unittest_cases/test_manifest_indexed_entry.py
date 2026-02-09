from edge_agent.app.indexing import manifest_store


def test_indexed_entry_has_indexed_status_and_no_skip_reason():
    entry = manifest_store.create_indexed_entry(
        path="repo/file.py",
        mtime_epoch_ms=111,
        sha256="deadbeef",
        indexed_at_epoch_ms=222,
    )

    assert set(entry.keys()) == manifest_store.manifest_entry_keys()
    assert entry["status"] == manifest_store.ManifestStatus.INDEXED.value
    assert manifest_store.SKIP_REASON_FIELD not in entry
