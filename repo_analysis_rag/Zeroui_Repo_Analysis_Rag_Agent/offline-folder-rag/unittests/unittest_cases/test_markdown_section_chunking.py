import textwrap
from pathlib import Path

from edge_agent.app.indexing.chunking import markdown_chunker


def test_markdown_section_chunking(tmp_path: Path):
    section_lines = 230
    content = "# Title\n" + "\n".join(f"line {i}" for i in range(section_lines))
    md_file = tmp_path / "long.md"
    md_file.write_text(content, encoding="utf-8")

    chunks = markdown_chunker.chunk(md_file)

    assert len(chunks) == 2
    first, second = chunks

    assert first["line_count"] == 200
    assert second["line_count"] == 51
    assert first["line_end"] - 19 == second["line_start"]
    assert second["line_end"] == section_lines + 1
