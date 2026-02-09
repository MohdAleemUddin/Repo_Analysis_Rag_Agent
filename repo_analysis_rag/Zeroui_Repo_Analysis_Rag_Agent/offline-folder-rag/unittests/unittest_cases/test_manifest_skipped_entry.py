import pytest

from edge_agent.app.indexing import manifest_store


def test_skipped_entry_has_status_and_enum_reason():
    entry = manifest_store.create_skipped_entry(
        path="repo/file.py",
        mtime_epoch_ms=123,
        sha256="abc",
        indexed_at_epoch_ms=456,
        reason=manifest_store.SkipReason.EXCLUDED_DIR,
    )

    assert set(entry.keys()) == manifest_store.manifest_entry_keys(include_skip_reason=True)
    assert entry["status"] == manifest_store.ManifestStatus.SKIPPED.value
    assert entry["skip_reason"] == manifest_store.SkipReason.EXCLUDED_DIR.value
    assert entry["skip_reason"] in [r.value for r in manifest_store.SkipReason]


def test_invalid_skip_reason_raises():
    with pytest.raises(ValueError):
        manifest_store.create_skipped_entry(
            path="repo/file.py",
            mtime_epoch_ms=123,
            sha256="abc",
            indexed_at_epoch_ms=456,
            reason="NOT_ALLOWED",
        )
