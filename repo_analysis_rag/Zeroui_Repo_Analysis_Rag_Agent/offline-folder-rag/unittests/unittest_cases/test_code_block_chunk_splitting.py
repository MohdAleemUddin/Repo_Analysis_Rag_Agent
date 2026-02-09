from pathlib import Path

from edge_agent.app.indexing.chunking import code_chunker


def test_brace_block_splits_with_overlap(tmp_path: Path):
    body = "\n".join(["  stmt;"] * 378)  # header + 378 + closing = 380 lines
    content = "\n".join(["function foo() {", body, "}"])
    f = tmp_path / "sample.js"
    f.write_text(content, encoding="utf-8")

    chunks = code_chunker.chunk(f)

    assert len(chunks) == 2

    first, second = chunks
    assert first["line_start"] == 1
    assert first["line_end"] == 200
    assert first["line_count"] == 200

    assert second["line_start"] == 181
    assert second["line_end"] == 380
    assert second["line_count"] == 200

    assert first["line_end"] - second["line_start"] + 1 == 20
