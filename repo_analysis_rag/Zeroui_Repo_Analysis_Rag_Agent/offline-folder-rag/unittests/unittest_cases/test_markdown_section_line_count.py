import textwrap
from pathlib import Path

from edge_agent.app.indexing.chunking import markdown_chunker


def test_markdown_section_line_count(tmp_path: Path):
    content = textwrap.dedent(
        """\
        # Title
        intro line

        ## Section A
        a1
        a2

        ## Section B
        b1
        """
    )
    md_file = tmp_path / "sample.md"
    md_file.write_text(content, encoding="utf-8")

    chunks = markdown_chunker.chunk(md_file)

    assert len(chunks) == 3
    # Expected line ranges: (1-2), (4-6), (8-9)
    expected = [
        (1, 2, 2),
        (4, 6, 3),
        (8, 9, 2),
    ]

    for chunk, (start, end, count) in zip(chunks, expected):
        assert chunk["line_start"] == start
        assert chunk["line_end"] == end
        assert chunk["line_count"] == count
        assert chunk["file_type"] == "markdown"
