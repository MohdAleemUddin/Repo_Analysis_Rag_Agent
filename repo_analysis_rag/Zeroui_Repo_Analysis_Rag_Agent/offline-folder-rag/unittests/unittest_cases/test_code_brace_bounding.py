from pathlib import Path

from edge_agent.app.indexing.chunking import code_chunker


def test_brace_chunk_balance(tmp_path: Path):
    content = "\n".join(
        [
            "function foo() {",
            "  return 1;",
            "}",
            "",
            "class Bar {",
            "  method() { return 2; }",
            "}",
        ]
    )
    f = tmp_path / "sample.js"
    f.write_text(content, encoding="utf-8")

    chunks = code_chunker.chunk(f)

    assert len(chunks) == 2
    assert chunks[0]["line_start"] == 1 and chunks[0]["line_end"] == 3
    assert chunks[1]["line_start"] == 5 and chunks[1]["line_end"] == 7


def test_brace_chunk_caps_at_400_lines(tmp_path: Path):
    body = ["  statement;"] * 410
    content = "\n".join(["function long() {"] + body + ["}"])
    f = tmp_path / "long.js"
    f.write_text(content, encoding="utf-8")

    chunks = code_chunker.chunk(f)

    assert any(chunk["line_end"] == 400 for chunk in chunks)
    assert chunks[-1]["line_start"] == 401
