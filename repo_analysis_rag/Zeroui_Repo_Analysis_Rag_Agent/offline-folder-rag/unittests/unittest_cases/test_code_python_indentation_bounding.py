from pathlib import Path

from edge_agent.app.indexing.chunking import code_chunker


def test_python_indentation_bounding_caps_at_400(tmp_path: Path):
    body = "\n".join(["    x = 1"] * 405)  # force cap >400
    content = "\n".join(
        [
            "def outer():",
            body,
            "def next_def():",
            "    pass",
        ]
    )
    f = tmp_path / "sample_cap.py"
    f.write_text(content, encoding="utf-8")

    chunks = code_chunker.chunk(f)

    outer = chunks[0]
    assert outer["line_start"] == 1
    assert outer["line_count"] == 400

    next_def = chunks[1]
    assert next_def["line_start"] == outer["line_end"] + 1
    assert next_def["line_count"] >= 1


def test_python_indentation_stops_on_indent_drop(tmp_path: Path):
    content = "\n".join(
        [
            "def outer():",
            "    @decorator",
            "    def inner():",
            "        pass",
            "",
            "    # still outer scope",
            "    x = 1",
            "",
            "def after():",
            "    pass",
        ]
    )
    f = tmp_path / "sample_indent.py"
    f.write_text(content, encoding="utf-8")

    chunks = code_chunker.chunk(f)

    assert len(chunks) == 2
    outer = chunks[0]
    assert outer["line_start"] == 1
    assert outer["line_end"] == 7

    after = chunks[1]
    assert after["line_start"] == 9
    assert after["line_end"] == 10
