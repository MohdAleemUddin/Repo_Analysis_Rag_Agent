from edge_agent.app.indexing import manifest_store


def test_indexed_entry_has_required_fields_only():
    entry = manifest_store.create_manifest_entry(
        path="repo/file.py",
        mtime_epoch_ms=123,
        sha256="abc",
        indexed_at_epoch_ms=456,
        status=manifest_store.ManifestStatus.INDEXED,
        skip_reason="should_be_ignored",
    )

    assert set(entry.keys()) == manifest_store.manifest_entry_keys()
    assert manifest_store.SKIP_REASON_FIELD not in entry
    assert entry["status"] == manifest_store.ManifestStatus.INDEXED.value


def test_skipped_entry_includes_skip_reason_only_when_skipped():
    reason = manifest_store.SkipReason.EXCLUDED_DIR
    entry = manifest_store.create_manifest_entry(
        path="repo/file.py",
        mtime_epoch_ms=123,
        sha256="abc",
        indexed_at_epoch_ms=456,
        status=manifest_store.ManifestStatus.SKIPPED,
        skip_reason=reason,
    )

    assert set(entry.keys()) == manifest_store.manifest_entry_keys(include_skip_reason=True)
    assert manifest_store.SKIP_REASON_FIELD in entry
    assert entry["skip_reason"] == reason.value
    assert entry["status"] == manifest_store.ManifestStatus.SKIPPED.value
