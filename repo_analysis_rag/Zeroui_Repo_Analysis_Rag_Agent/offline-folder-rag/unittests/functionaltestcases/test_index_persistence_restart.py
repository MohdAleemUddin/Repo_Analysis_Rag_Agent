from pathlib import Path

from edge_agent.app.indexing import indexer


class _FakeCollection:
    def __init__(self, name: str):
        self.name = name


class _FakeClient:
    def __init__(self, fail_on_missing: bool, created: list[str], gets: list[str], existing: dict[str, _FakeCollection]):
        self._fail_on_missing = fail_on_missing
        self._created = created
        self._gets = gets
        self._existing = existing

    def get_collection(self, name: str):
        self._gets.append(name)
        if name in self._existing:
            return self._existing[name]
        if self._fail_on_missing:
            raise Exception("missing")
        coll = _FakeCollection(name)
        self._existing[name] = coll
        return coll

    def create_collection(self, name: str):
        self._created.append(name)
        coll = _FakeCollection(name)
        self._existing[name] = coll
        return coll


def test_collections_reused_across_restart(monkeypatch, tmp_path: Path):
    repo_id = "repo123"
    base_dir = tmp_path / "persist"
    created: list[str] = []
    gets: list[str] = []
    built_dirs: list[Path] = []
    existing_by_dir: dict[Path, dict[str, _FakeCollection]] = {}
    clients_by_dir: dict[Path, _FakeClient] = {}

    def _builder(persist_directory: Path | str):
        built_dirs.append(Path(persist_directory))
        path = Path(persist_directory)
        existing = existing_by_dir.setdefault(path, {})
        client = clients_by_dir.get(path)
        if client is None:
            fail_on_missing = len(clients_by_dir) == 0
            client = _FakeClient(
                fail_on_missing=fail_on_missing,
                created=created,
                gets=gets,
                existing=existing,
            )
            clients_by_dir[path] = client
        return client

    monkeypatch.setattr(indexer, "resolve_index_dir", lambda: base_dir)
    monkeypatch.setattr(indexer, "_build_chroma_client", _builder)

    indexer.reset_chroma_state()
    indexer.ensure_repo_collections(repo_id)

    assert set(created) == {f"{repo_id}_code_chunks", f"{repo_id}_doc_chunks"}
    assert built_dirs[0] == base_dir / repo_id
    assert len(gets) == 2  # code + doc attempts

    created.clear()
    gets.clear()
    indexer.reset_chroma_state()
    clients_by_dir.clear()
    indexer.ensure_repo_collections(repo_id)

    # On restart we should reuse existing collections: no create calls
    assert created == []
    assert len(gets) == 2
    assert built_dirs[1] == base_dir / repo_id
