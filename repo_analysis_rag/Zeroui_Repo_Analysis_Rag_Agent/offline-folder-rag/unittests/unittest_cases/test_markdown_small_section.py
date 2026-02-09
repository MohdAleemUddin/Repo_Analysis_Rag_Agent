from pathlib import Path

from edge_agent.app.indexing.chunking import markdown_chunker


def test_small_markdown_section_emits_single_chunk(tmp_path: Path):
    section_lines = 150
    content = "# Small Section\n" + "\n".join(f"line {i}" for i in range(section_lines))
    md_file = tmp_path / "small.md"
    md_file.write_text(content, encoding="utf-8")

    chunks = markdown_chunker.chunk(md_file)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk["line_count"] == section_lines + 1
    assert chunk["line_start"] == 1
    assert chunk["line_end"] == section_lines + 1
