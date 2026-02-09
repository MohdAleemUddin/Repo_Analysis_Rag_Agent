from edge_agent.app.indexing.chunking.chunker import classify_file_type


def test_markdown_extension_precedence():
    result = classify_file_type("docs/summary.md", "code")
    assert result == "markdown"


def test_code_type_when_not_markdown():
    result = classify_file_type("src/app.py", "code")
    assert result == "code"


def test_other_when_not_code_and_not_markdown():
    result = classify_file_type("data/config.json", "other")
    assert result == "other"
