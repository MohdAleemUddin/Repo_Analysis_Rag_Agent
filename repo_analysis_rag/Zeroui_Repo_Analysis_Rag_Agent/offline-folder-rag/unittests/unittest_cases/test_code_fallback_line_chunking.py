from pathlib import Path

from edge_agent.app.indexing.chunking import code_chunker


def test_code_fallback_line_chunking(tmp_path: Path):
    content = "\n".join(
        [
            "// no functions or classes here",
            "let x = 1;",
            "x += 2;",
        ]
    )
    f = tmp_path / "nofunc.js"
    f.write_text(content, encoding="utf-8")

    chunks = code_chunker.chunk(f)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk["line_start"] == 1
    assert chunk["line_end"] == 3
    assert chunk["line_count"] == 3
