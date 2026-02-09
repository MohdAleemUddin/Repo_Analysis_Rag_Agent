from pathlib import Path

from edge_agent.app.indexing.chunking import code_chunker


def test_code_boundary_detection_python(tmp_path: Path):
    content = "\n".join(
        [
            "def a():",
            "    pass",
            "",
            "class B:",
            "    def method(self):",
            "        pass",
        ]
    )
    f = tmp_path / "sample.py"
    f.write_text(content, encoding="utf-8")

    chunks = code_chunker.chunk(f)

    assert len(chunks) == 2
    # boundaries only at def a and class B
    assert chunks[0]["line_start"] == 1 and chunks[0]["line_end"] == 2
    assert chunks[1]["line_start"] == 4 and chunks[1]["line_end"] == 6


def test_code_boundary_detection_js(tmp_path: Path):
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


def test_code_boundary_detection_java_like(tmp_path: Path):
    content = "\n".join(
        [
            "public class Main {",
            "  private void helper() {}",
            "}",
        ]
    )
    f = tmp_path / "Sample.java"
    f.write_text(content, encoding="utf-8")

    chunks = code_chunker.chunk(f)

    assert len(chunks) == 2
    assert chunks[0]["line_start"] == 1 and chunks[0]["line_end"] == 1
    assert chunks[1]["line_start"] == 2 and chunks[1]["line_end"] == 2
