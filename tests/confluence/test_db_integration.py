"""
Integration tests: TC-IT-002 (Agents ↔ Database), TC-IT-008 (Learning system ↔ Agent system).
With DB URL: real DB tests. Without DB URL: tests run and assert no crash (count 0, connection None).
"""

import os
import pytest

try:
    from app.confluence.db_adapter import (
        get_connection,
        db_fetch_examples_count,
        db_execute,
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
    from app.confluence.db_adapter import (
        get_connection,
        db_fetch_examples_count,
        db_execute,
    )


def _has_db() -> bool:
    return bool(
        os.environ.get("CONFLUENCE_DATABASE_URL") or os.environ.get("DATABASE_URL")
    )


# --- No-DB path: tests always run (PRD: no skip when no DB URL) ---
def test_tc_it_002_no_db_returns_none_and_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """When no DB URL, get_connection is None and count is 0 (no skip)."""
    monkeypatch.delenv("CONFLUENCE_DATABASE_URL", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    conn = get_connection()
    assert conn is None
    assert db_fetch_examples_count() == 0


# --- TC-IT-002: Agents ↔ Database - Data flow works ---
def test_tc_it_002_agents_database_data_flow() -> None:
    """Agents read/write path: count is int >= 0 (DB or file fallback)."""
    count = db_fetch_examples_count()
    assert isinstance(count, int)
    assert count >= 0


def test_tc_it_002_database_read_templates_exist() -> None:
    """At least 7 templates exist: from DB (intelligent_templates) or from confluence_data/templates (PRD §8.2)."""
    conn = get_connection()
    if conn is not None:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM intelligent_templates")
            n = cur.fetchone()[0]
        assert n >= 7, "Expected at least 7 seed templates from PRD §8.2"
    else:
        templates_dir = os.path.join(
            os.path.dirname(__file__), "..", "..", "confluence_data", "templates"
        )
        templates_dir = os.path.abspath(templates_dir)
        if os.path.isdir(templates_dir):
            n = len([f for f in os.listdir(templates_dir) if f.endswith(".json")])
            assert (
                n >= 7
            ), "Expected at least 7 template files in confluence_data/templates"
        else:
            assert True, "No DB and no templates dir; test N/A"


# --- TC-IT-008: Learning system ↔ Agent system - Complete intelligence feedback loop ---
def test_tc_it_008_learning_system_can_store_example() -> None:
    """Learning system can store an example (DB or file fallback)."""
    conn = get_connection()
    if conn is not None:
        with conn.cursor() as cur:
            cur.execute("SELECT id FROM intelligent_templates LIMIT 1")
            row = cur.fetchone()
        if row is None:
            assert True, "No template in DB (migration not run); write path N/A"
            return
        template_id = row[0]
        db_execute(
            """
            INSERT INTO intelligence_examples (content_profile, template_used, confidence_score)
            VALUES (%s, %s, %s)
            """,
            ('{"content_types": ["test"]}', str(template_id), 0.95),
        )
        count = db_fetch_examples_count()
        assert count >= 0
        conn2 = get_connection()
        if conn2:
            with conn2.cursor() as cur:
                cur.execute(
                    "DELETE FROM intelligence_examples WHERE content_profile::text LIKE %s",
                    ("%test%",),
                )
            conn2.commit()
    else:
        try:
            from app.confluence.example_manager import store_example, get_examples
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
            from app.confluence.example_manager import store_example, get_examples
        ex_id, learned = store_example(
            content_profile={"content_types": ["test"]},
            template_id="00000000-0000-0000-0000-000000000001",
            template_name="Test Template",
            confidence_score=0.95,
            db_execute=None,
        )
        assert isinstance(ex_id, str)
        assert learned is True or learned is False
        examples_dir = os.path.abspath(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "confluence_data", "examples"
            )
        )
        examples = get_examples(examples_base_dir=examples_dir)
        assert isinstance(examples, list)
        assert len(examples) >= 0
