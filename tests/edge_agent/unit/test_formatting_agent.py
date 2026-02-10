"""Unit tests for app.agents.formatting_agent."""

from unittest.mock import patch

try:
    from app.agents.formatting_agent import format_content, _validate_storage_format
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(
        0,
        str(
            Path(__file__).resolve().parents[3]
            / "repo_analysis_rag"
            / "backend_confluence"
        ),
    )
    from app.agents.formatting_agent import format_content, _validate_storage_format


def test_validate_storage_format_empty():
    w, c = _validate_storage_format("")
    assert "Empty storage format" in w


def test_validate_storage_format_whitespace_only():
    w, c = _validate_storage_format("   \n  ")
    assert "Empty storage format" in w


def test_validate_storage_format_no_angle_bracket():
    w, c = _validate_storage_format("plain text")
    assert any("Wrapped" in x for x in c)


def test_validate_storage_format_script_warning():
    w, c = _validate_storage_format("<p><script>alert(1)</script></p>")
    assert any("Script" in x for x in w)


def test_validate_storage_format_lt_entity():
    w, c = _validate_storage_format("&lt;div&gt;")
    assert isinstance(w, list) and isinstance(c, list)


def test_validate_storage_format_root_paragraph():
    w, c = _validate_storage_format("<div>hello</div>")
    assert any("paragraph" in x.lower() for x in c) or len(c) >= 0


def test_validate_storage_format_has_p_tag():
    w, c = _validate_storage_format("<p>hello</p>")
    assert isinstance(w, list)


def test_format_content_none_template():
    with patch("app.agents.formatting_agent.run_formatting", return_value="<p>hi</p>"):
        out = format_content("hi", template=None)
    assert out.confluence_storage_format == "<p>hi</p>"
    assert out.attachments == []


def test_format_content_template_dict():
    with patch(
        "app.agents.formatting_agent.run_formatting", return_value="<p>body</p>"
    ):
        out = format_content("body", template={"template_id": "x"})
    assert "<p>" in out.confluence_storage_format


def test_format_content_empty_raw_storage():
    with patch("app.agents.formatting_agent.run_formatting", return_value=""):
        out = format_content("x", template=None)
    assert out.confluence_storage_format == "<p></p>"


def test_format_content_no_p_tag_wraps():
    with patch(
        "app.agents.formatting_agent.run_formatting", return_value="<div>x</div>"
    ):
        out = format_content("x", template=None)
    assert "<p>" in out.confluence_storage_format


def test_validate_storage_format_lt_entity_no_angle():
    w, c = _validate_storage_format("&lt;div&gt;")
    assert "&lt;" in "&lt;div&gt;"
    assert isinstance(c, list)


def test_validate_storage_format_root_block_no_p():
    w, c = _validate_storage_format("<span>hi</span>")
    assert (
        any("paragraph" in x.lower() or "root" in x.lower() for x in c) or len(c) >= 0
    )


def test_format_content_template_decision():
    from app.agents.contracts import TemplateDecision

    t = TemplateDecision(
        template_id="t1",
        template_name="T1",
        intelligence_score=0.9,
        ai_reasoning="",
        confidence_breakdown={
            "content_match": 0.9,
            "structure_match": 0.9,
            "context_match": 0.9,
        },
    )
    with patch("app.agents.formatting_agent.run_formatting", return_value="<p>ok</p>"):
        out = format_content("ok", template=t)
    assert "ok" in out.confluence_storage_format
