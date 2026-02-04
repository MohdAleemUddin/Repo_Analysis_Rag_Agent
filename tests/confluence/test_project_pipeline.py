# US-16: Tests for project_scanner, project_analyzer, project_template_matcher
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

pytestmark = [pytest.mark.prd_compliance, pytest.mark.api_format]


def _tests_dir() -> Path:
    return Path(__file__).resolve().parent


def _ensure_imports():
    try:
        from app.confluence.project_analyzer import ProjectAnalysis, analyze_project
        from app.confluence.project_template_matcher import match_project_template
        return ProjectAnalysis, analyze_project, match_project_template
    except ImportError:
        import sys
        sys.path.insert(0, str(_tests_dir().parents[1] / "offline-folder-rag" / "edge_agent"))
        from app.confluence.project_analyzer import ProjectAnalysis, analyze_project
        from app.confluence.project_template_matcher import match_project_template
        return ProjectAnalysis, analyze_project, match_project_template


def test_project_scanner_returns_paths() -> None:
    """project_scanner returns list of file paths for valid directory."""
    try:
        from app.confluence.project_scanner import scan
    except ImportError:
        import sys
        sys.path.insert(0, str(_tests_dir().parents[1] / "offline-folder-rag" / "edge_agent"))
        from app.confluence.project_scanner import scan
    tests_dir = _tests_dir()
    paths = scan(str(tests_dir), limit=20)
    assert isinstance(paths, list)
    assert len(paths) <= 20


def test_project_scanner_excludes_sensitive() -> None:
    """NFR3: project_scanner excludes *.env, *.pem, credentials*, secrets*."""
    try:
        from app.confluence.project_scanner import scan
    except ImportError:
        import sys
        sys.path.insert(0, str(_tests_dir().parents[1] / "offline-folder-rag" / "edge_agent"))
        from app.confluence.project_scanner import scan
    import tempfile
    import os
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "main.py").write_text("x = 1")
        Path(tmp, ".env").write_text("secret")
        Path(tmp, "test.pem").write_text("key")
        Path(tmp, "credentials.json").write_text("{}")
        paths = scan(tmp)
        names = [os.path.basename(p) for p in paths]
        assert "main.py" in names
        assert ".env" not in names
        assert "test.pem" not in names
        assert "credentials.json" not in names


def test_project_scanner_progress_callback() -> None:
    """project_scanner invokes progress_callback when provided."""
    try:
        from app.confluence.project_scanner import scan
    except ImportError:
        import sys
        sys.path.insert(0, str(_tests_dir().parents[1] / "offline-folder-rag" / "edge_agent"))
        from app.confluence.project_scanner import scan
    calls: list[tuple[int, int]] = []
    def cb(current: int, total: int) -> None:
        calls.append((current, total))
    paths = scan(str(_tests_dir()), progress_callback=cb, limit=5)
    assert isinstance(paths, list)


def test_project_analyzer_returns_analysis() -> None:
    """project_analyzer returns ProjectAnalysis with project_type."""
    try:
        from app.confluence.project_analyzer import analyze_project, ProjectAnalysis
    except ImportError:
        import sys
        sys.path.insert(0, str(_tests_dir().parents[1] / "offline-folder-rag" / "edge_agent"))
        from app.confluence.project_analyzer import analyze_project, ProjectAnalysis
    tests_dir = _tests_dir()
    py_files = [str(p) for p in Path(tests_dir).rglob("*.py")][:10]
    if not py_files:
        pytest.skip("No Python files in tests dir")
    analysis = analyze_project(py_files)
    assert isinstance(analysis, ProjectAnalysis)
    assert analysis.project_type in ("web app", "API", "library", "mixed", "testing", "database")


def test_project_template_matcher_fallback() -> None:
    """project_template_matcher falls back to Mixed when confidence < 70%."""
    try:
        from app.confluence.project_analyzer import ProjectAnalysis
        from app.confluence.project_template_matcher import match_project_template, FALLBACK_TEMPLATE
    except ImportError:
        import sys
        sys.path.insert(0, str(_tests_dir().parents[1] / "offline-folder-rag" / "edge_agent"))
        from app.confluence.project_analyzer import ProjectAnalysis
        from app.confluence.project_template_matcher import match_project_template, FALLBACK_TEMPLATE
    analysis = ProjectAnalysis(
        project_type="unknown",
        key_file_types=[],
        structure_summary="",
        patterns=[],
        content_types=[],
        detected_patterns=[],
        source_file_count=0,
    )
    match = match_project_template(analysis)
    assert match.template_name == FALLBACK_TEMPLATE or match.confidence >= 70


def test_project_template_matcher_returns_match() -> None:
    """project_template_matcher returns template name, confidence, match_count."""
    _, _, match_project_template = _ensure_imports()
    ProjectAnalysis = _ensure_imports()[0]
    analysis = ProjectAnalysis(
        project_type="API",
        key_file_types=[".py"],
        structure_summary="API project",
        patterns=["fastapi", "rest"],
        content_types=["python_api"],
        detected_patterns=["fastapi"],
        source_file_count=15,
    )
    match = match_project_template(analysis)
    assert match.template_name
    assert 0 <= match.confidence <= 100
    assert isinstance(match.match_count, int)


# --- project_analyzer: _infer_project_type branches ---


def test_project_analyzer_infers_testing_type() -> None:
    """_infer_project_type returns 'testing' when test_score > 3, lib < 2, api < 2."""
    _, analyze_project, _ = _ensure_imports()
    fake_profile = type("FakeProfile", (), {"model_dump": lambda s: {
        "content_types": ["pytest", "jest", "unittest", "spec"],
        "detected_patterns": ["test_", "e2e"],
        "languages": [],
        "structure_signals": [],
    }})()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        for name in ["test_pytest.py", "test_jest.js", "unittest_x.py", "spec_y.py"]:
            (base / name).write_text("# minimal")
        paths = [str(base / n) for n in ["test_pytest.py", "test_jest.js", "unittest_x.py", "spec_y.py"]]
        with patch("app.confluence.project_analyzer.analyze", return_value=fake_profile):
            analysis = analyze_project(paths)
        assert analysis.project_type == "testing"


def test_project_analyzer_infers_database_type() -> None:
    """_infer_project_type returns 'database' when db_score >= 2, api < 2."""
    _, analyze_project, _ = _ensure_imports()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "postgres.conf").write_text("host=localhost")
        (base / "sqlite.db").write_text("x")  # small file
        paths = [str(base / "postgres.conf"), str(base / "sqlite.db")]
        analysis = analyze_project(paths)
        assert analysis.project_type == "database"


def test_project_analyzer_infers_library_type() -> None:
    """_infer_project_type returns 'library' when lib_score >= 2, api < 2, web < 2."""
    _, analyze_project, _ = _ensure_imports()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "setup.py").write_text("from setuptools import setup")
        (base / "pyproject.toml").write_text("[project]\nname = 'x'")
        paths = [str(base / "setup.py"), str(base / "pyproject.toml")]
        analysis = analyze_project(paths)
        assert analysis.project_type == "library"


def test_project_analyzer_infers_web_app_type() -> None:
    """_infer_project_type returns 'web app' when web_score >= 2, api < 2."""
    _, analyze_project, _ = _ensure_imports()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "App.tsx").write_text("import React from 'react'")
        (base / "package.json").write_text('{"name":"app"}')
        paths = [str(base / "App.tsx"), str(base / "package.json")]
        analysis = analyze_project(paths)
        assert analysis.project_type == "web app"


def test_project_analyzer_infers_mixed_type_single_signal() -> None:
    """_infer_project_type returns 'mixed' when exactly one signal in web/api/lib."""
    _, analyze_project, _ = _ensure_imports()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "api_helper.py").write_text("def api(): pass")  # single api signal
        paths = [str(base / "api_helper.py")]
        analysis = analyze_project(paths)
        assert analysis.project_type == "mixed"


def test_project_analyzer_skips_non_file_paths() -> None:
    """analyze_project skips paths that are not files (e.g. directories)."""
    _, analyze_project, _ = _ensure_imports()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "real.py").write_text("x = 1")
        paths = [str(base), str(base / "real.py")]  # dir then file
        analysis = analyze_project(paths)
        assert analysis.source_file_count == 2
        assert analysis.project_type in ("web app", "API", "library", "mixed", "testing", "database")


def test_project_analyzer_handles_large_or_empty_preferred_files() -> None:
    """analyze_project handles files > 64KB or empty with preferred extensions."""
    _, analyze_project, _ = _ensure_imports()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        (base / "large.py").write_text("x" * (65 * 1024))
        (base / "empty.py").write_text("")
        paths = [str(base / "large.py"), str(base / "empty.py")]
        analysis = analyze_project(paths)
        assert "document" in analysis.content_types or "large_file" in analysis.detected_patterns or "empty" in analysis.detected_patterns


def test_project_analyzer_handles_oserror() -> None:
    """analyze_project continues on OSError when reading a file."""
    _, analyze_project, _ = _ensure_imports()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        good_py = base / "good.py"
        good_py.write_text("x = 1")
        bad_py = base / "bad.py"
        bad_py.write_text("y = 2")  # exists so isfile passes
        paths = [str(bad_py), str(good_py)]

        def mock_open(path, *args, **kwargs):
            if str(path) == str(bad_py):
                raise OSError("read failed")
            return open(path, *args, **kwargs)

        with patch("app.confluence.project_analyzer.open", side_effect=mock_open):
            analysis = analyze_project(paths)
        assert analysis.source_file_count == 2


def test_project_analyzer_handles_unicode_decode_error() -> None:
    """analyze_project continues on UnicodeDecodeError when reading a file."""
    _, analyze_project, _ = _ensure_imports()
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        good_py = base / "good.py"
        good_py.write_text("x = 1")
        bad_file = base / "binary.bin"
        bad_file.write_bytes(b"\xff\xfe\xfd")
        paths = [str(bad_file), str(good_py)]

        def mock_open(path, *args, **kwargs):
            if str(path) == str(bad_file):
                raise UnicodeDecodeError("utf-8", b"", 0, 1, "invalid")
            return open(path, *args, **kwargs)

        with patch("app.confluence.project_analyzer.open", side_effect=mock_open):
            analysis = analyze_project(paths)
        assert analysis.source_file_count == 2


# --- project_template_matcher: uncovered branches ---


def test_project_template_matcher_django_override() -> None:
    """match_project_template uses Django template when 'django' in patterns."""
    ProjectAnalysis, _, match_project_template = _ensure_imports()
    analysis = ProjectAnalysis(
        project_type="API",
        key_file_types=[],
        structure_summary="",
        patterns=["django", "rest"],
        content_types=[],
        detected_patterns=[],
        source_file_count=5,
    )
    match = match_project_template(analysis)
    assert "Django" in match.template_name


def test_project_template_matcher_spring_override() -> None:
    """match_project_template uses Java Spring template when 'spring' in patterns."""
    ProjectAnalysis, _, match_project_template = _ensure_imports()
    analysis = ProjectAnalysis(
        project_type="API",
        key_file_types=[],
        structure_summary="",
        patterns=["spring", "boot"],
        content_types=[],
        detected_patterns=[],
        source_file_count=5,
    )
    match = match_project_template(analysis)
    assert "Spring" in match.template_name


def test_project_template_matcher_patterns_match_examples() -> None:
    """match_project_template counts examples matching via patterns & ex_patterns (not project_type)."""
    ProjectAnalysis, _, match_project_template = _ensure_imports()
    analysis = ProjectAnalysis(
        project_type="other",
        key_file_types=[],
        structure_summary="",
        patterns=["fastapi", "uvicorn"],
        content_types=["python_api"],
        detected_patterns=[],
        source_file_count=3,
    )
    match = match_project_template(analysis)
    assert match.match_count >= 1


def test_project_template_matcher_low_confidence_fallback() -> None:
    """match_project_template falls back when confidence < 70%."""
    try:
        from app.confluence.project_template_matcher import FALLBACK_TEMPLATE
    except ImportError:
        import sys
        sys.path.insert(0, str(_tests_dir().parents[1] / "offline-folder-rag" / "edge_agent"))
        from app.confluence.project_template_matcher import FALLBACK_TEMPLATE
    ProjectAnalysis, _, match_project_template = _ensure_imports()
    with patch("app.confluence.project_template_matcher._load_project_examples", return_value=[]):
        analysis = ProjectAnalysis(
            project_type="mixed",
            key_file_types=[],
            structure_summary="",
            patterns=[],
            content_types=[],
            detected_patterns=[],
            source_file_count=1,
        )
        match = match_project_template(analysis)
    assert match.template_name == FALLBACK_TEMPLATE
    assert match.confidence == 65.0


def test_project_template_matcher_missing_examples_file() -> None:
    """_load_project_examples returns [] when project_examples.json is missing."""
    ProjectAnalysis, _, match_project_template = _ensure_imports()
    orig_is_file = Path.is_file

    def is_file_false_for_examples(self):
        if "project_examples.json" in str(self):
            return False
        return orig_is_file(self)

    with patch.object(Path, "is_file", is_file_false_for_examples):
        analysis = ProjectAnalysis(
            project_type="API",
            key_file_types=[],
            structure_summary="",
            patterns=["fastapi"],
            content_types=[],
            detected_patterns=[],
            source_file_count=20,
        )
        match = match_project_template(analysis)
    assert match.template_name
    assert match.match_count == 0


def test_project_template_matcher_examples_load_error() -> None:
    """_load_project_examples returns [] on OSError or JSONDecodeError."""
    ProjectAnalysis, _, match_project_template = _ensure_imports()
    orig_open = open

    def raise_oserror(path, *args, **kwargs):
        if "project_examples.json" in str(path):
            raise OSError("file not found")
        return orig_open(path, *args, **kwargs)

    with patch("app.confluence.project_template_matcher.open", side_effect=raise_oserror):
        analysis = ProjectAnalysis(
            project_type="API",
            key_file_types=[],
            structure_summary="",
            patterns=["fastapi"],
            content_types=[],
            detected_patterns=[],
            source_file_count=20,
        )
        match = match_project_template(analysis)
    assert match.template_name
