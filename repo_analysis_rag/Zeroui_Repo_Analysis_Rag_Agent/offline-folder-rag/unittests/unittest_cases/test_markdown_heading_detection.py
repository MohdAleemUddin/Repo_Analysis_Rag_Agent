import textwrap
from pathlib import Path

from edge_agent.app.indexing.chunking import markdown_chunker


def test_markdown_heading_detection(tmp_path: Path):
    content = textwrap.dedent(
        """\
        # Title
        intro line

        ## Section A
        detail A1
        detail A2

        ### Sub A.1
        detail sub

        ## Section B
        detail B
        """
    )
    md_file = tmp_path / "sample.md"
    md_file.write_text(content, encoding="utf-8")

    chunks = markdown_chunker.chunk(md_file)

    assert len(chunks) == 4
    # Heading line numbers: 1, 4, 8, 11 (1-based)
    expected_bounds = [
        (1, 2),   # # Title block
        (4, 6),   # ## Section A block
        (8, 9),   # ### Sub A.1 block
        (11, 12), # ## Section B block
    ]

    for chunk, (start, end) in zip(chunks, expected_bounds):
        assert chunk["line_start"] == start
        assert chunk["line_end"] == end
        assert chunk["file_type"] == "markdown"
