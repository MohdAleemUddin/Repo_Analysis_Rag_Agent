import json
import sys
from pathlib import Path


def _setup_path():
    repo_root = Path(__file__).resolve().parents[4]
    project_root = repo_root / "offline-folder-rag"
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))


_setup_path()

from edge_agent.app.indexing.chunking import chunker
from edge_agent.app.indexing.manifest_store import SKIP_REASON_CHUNK_LIMIT


def _write_large_code_file(path: Path, definitions: int) -> None:
    lines: list[str] = []
    for idx in range(definitions):
        lines.append(f"def func_{idx}():")
        lines.append("    pass")
        lines.append("")
    path.write_text("\n".join(lines).strip(), encoding="utf-8")


def test_chunking_workflow_truncates_large_files(tmp_path):
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    large_file = repo_dir / "large_module.py"
    total_defs = chunker.MAX_CHUNKS_PER_FILE + 60
    _write_large_code_file(large_file, total_defs)

    manifest_path = tmp_path / "manifest.json"
    chunks = chunker.chunk_file(
        large_file,
        file_type="code",
        manifest_path=str(manifest_path),
    )

    assert len(chunks) == chunker.MAX_CHUNKS_PER_FILE
    assert all(chunk["truncated"] for chunk in chunks)

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    file_entry = manifest_data["files"][str(large_file)]
    assert file_entry["truncated"] is True
    assert file_entry["skip_reason"] == SKIP_REASON_CHUNK_LIMIT
