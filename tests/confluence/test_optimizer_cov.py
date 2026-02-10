"""Tests for optimizer coverage."""

from unittest.mock import MagicMock

try:
    from app.confluence.optimizer import (
        get_optimization_suggestions,
        get_recommended_max_parallel,
    )
except ImportError:
    import sys
    from pathlib import Path

    sys.path.insert(
        0,
        str(
            Path(__file__).resolve().parents[2]
            / "repo_analysis_rag"
            / "backend_confluence"
        ),
    )
    from app.confluence.optimizer import (
        get_optimization_suggestions,
        get_recommended_max_parallel,
    )


def test_get_optimization_suggestions_analysis_over():
    rec = MagicMock()
    rec.per_file_analysis_ms = [4000]
    rec.targets_met = {}
    rec.template_selection_ms = 0
    rec.create_e2e_ms = 0
    rec.peak_memory_mb = 0
    out = get_optimization_suggestions(rec)
    assert any("Analysis" in s or "analysis" in s for s in out)


def test_get_optimization_suggestions_template_over():
    rec = MagicMock()
    rec.per_file_analysis_ms = []
    rec.template_selection_ms = 3000
    rec.create_e2e_ms = 0
    rec.peak_memory_mb = 0
    rec.targets_met = {}
    out = get_optimization_suggestions(rec)
    assert any("Template" in s or "template" in s for s in out)


def test_get_optimization_suggestions_create_over():
    rec = MagicMock()
    rec.per_file_analysis_ms = []
    rec.template_selection_ms = 0
    rec.create_e2e_ms = 20000
    rec.peak_memory_mb = 0
    rec.targets_met = {}
    out = get_optimization_suggestions(rec)
    assert any("E2E" in s or "create" in s for s in out)


def test_get_optimization_suggestions_memory_over():
    rec = MagicMock()
    rec.per_file_analysis_ms = []
    rec.template_selection_ms = 0
    rec.create_e2e_ms = 0
    rec.peak_memory_mb = 350
    rec.targets_met = {}
    out = get_optimization_suggestions(rec)
    assert any("memory" in s.lower() or "Memory" in s for s in out)


def test_get_optimization_suggestions_dict():
    rec = {
        "per_file_analysis_ms": [4000],
        "template_selection_ms": 0,
        "create_e2e_ms": 0,
        "peak_memory_mb": 0,
        "targets_met": {},
    }
    out = get_optimization_suggestions(rec)
    assert isinstance(out, list)


def test_get_recommended_max_parallel_near_limit():
    n = get_recommended_max_parallel(299)
    assert n is None or n == 2


def test_get_recommended_max_parallel_over_limit():
    n = get_recommended_max_parallel(350)
    assert n == 2
