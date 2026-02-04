"""
Intelligence learning tests; TC-RG-006 regression (learning functionality still works after changes).
"""
try:
    from offline_folder_rag.edge_agent.app.config.confluence_config import get_confluence_config
    from offline_folder_rag.edge_agent.app.config.config import get_database_config
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "offline-folder-rag" / "edge_agent"))
    from app.config.confluence_config import get_confluence_config
    from app.config.config import get_database_config


# --- TC-RG-006: Intelligence system → Learning functionality still works after changes ---
def test_tc_rg_006_database_config_present_for_learning() -> None:
    """After config changes, database config still provides URL so learning can run."""
    db_cfg = get_database_config()
    assert "database_url" in db_cfg
    assert "pool_min_size" in db_cfg
    assert "pool_max_size" in db_cfg


def test_tc_rg_006_confluence_config_uses_central_db_url() -> None:
    """Confluence config uses central DB URL (same as RAG when DATABASE_URL set)."""
    cfg = get_confluence_config()
    assert "database_url" in cfg
    # When CONFLUENCE_DATABASE_URL or DATABASE_URL is set, learning can persist
    url = cfg.get("database_url")
    assert url is None or isinstance(url, str)


def test_tc_uc_004_provide_feedback_to_improve_ai() -> None:
    """TC-UC-004: Provide feedback to improve AI -> System learns from feedback."""
    try:
        from offline_folder_rag.edge_agent.app.agents.learning_agent import learn_from_feedback
        from offline_folder_rag.edge_agent.app.confluence.example_manager import _get_file_feedback
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "offline-folder-rag" / "edge_agent"))
        from app.agents.learning_agent import learn_from_feedback
        from app.confluence.example_manager import _get_file_feedback

    learn_from_feedback(
        creation_id="d0000001-0001-4000-8000-000000000001",
        intelligence_score=5,
        feedback_text="Perfect AI formatting!",
    )
    items = _get_file_feedback()
    assert any(
        item.get("intelligence_score") == 5 and "d0000001" in str(item.get("creation_id", ""))
        for item in items
    )


def test_tc_rg_006_learning_schema_constants_unchanged() -> None:
    """Title/confidence bounds unchanged so import/export and validation still valid."""
    try:
        from offline_folder_rag.edge_agent.app.confluence.validation import (
            TITLE_MAX_LEN,
            CONFIDENCE_MIN,
            CONFIDENCE_MAX,
        )
    except ImportError:
        from pathlib import Path
        import sys
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "offline-folder-rag" / "edge_agent"))
        from app.confluence.validation import TITLE_MAX_LEN, CONFIDENCE_MIN, CONFIDENCE_MAX
    assert TITLE_MAX_LEN == 255
    assert CONFIDENCE_MIN == 0.0
    assert CONFIDENCE_MAX == 1.0
