from pathlib import Path

from edge_agent.app.indexing.chunking import chunker


def test_code_chunking_flow(tmp_path: Path):
    brace_body = "\n".join(["  stmt;"] * 378)  # total: 380 lines with header+footer
    brace_file = tmp_path / "brace.js"
    brace_file.write_text("\n".join(["function foo() {", brace_body, "}"]), encoding="utf-8")

    py_body = "\n".join(["    x = 1"] * 405)
    py_file = tmp_path / "sample.py"
    py_file.write_text(
        "\n".join(
            [
                "def outer():",
                py_body,
                "def next_def():",
                "    pass",
            ]
        ),
        encoding="utf-8",
    )

    fallback_file = tmp_path / "plain.js"
    fallback_file.write_text("\n".join(["// no defs", "let x = 1;", "x += 2;"]), encoding="utf-8")

    brace_chunks = chunker.chunk_file(brace_file, file_type="code")
    assert brace_chunks[0]["line_start"] == 1
    assert brace_chunks[0]["line_end"] == 200
    assert brace_chunks[1]["line_start"] == 181
    assert brace_chunks[-1]["line_end"] == 380
    assert brace_chunks[-1]["line_start"] == 181

    py_chunks = chunker.chunk_file(py_file, file_type="code")
    assert py_chunks[0]["line_start"] == 1
    assert py_chunks[0]["line_count"] == 400
    assert py_chunks[1]["line_start"] == py_chunks[0]["line_end"] + 1

    fb_chunks = chunker.chunk_file(fallback_file, file_type="code")
    assert len(fb_chunks) == 1
    fb = fb_chunks[0]
    assert fb["line_start"] == 1 and fb["line_end"] == 3
