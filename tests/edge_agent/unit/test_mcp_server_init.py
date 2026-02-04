"""Unit test to load app.mcp_server __init__ for coverage (exports)."""
try:
    from app.mcp_server import (
        RAG_QUERY,
        CONFLUENCE_INTELLIGENT_ANALYZE,
        MCPTask,
        enqueue,
        dequeue,
        is_empty,
        set_progress_callback,
        set_cancel_check,
        LIFECYCLE_QUEUED,
        LIFECYCLE_SUCCESS,
        confluence_tasks,
    )
except ImportError:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "offline-folder-rag" / "edge_agent"))
    from app.mcp_server import (
        RAG_QUERY,
        CONFLUENCE_INTELLIGENT_ANALYZE,
        MCPTask,
        enqueue,
        dequeue,
        is_empty,
        set_progress_callback,
        set_cancel_check,
        LIFECYCLE_QUEUED,
        LIFECYCLE_SUCCESS,
        confluence_tasks,
    )


def test_mcp_server_init_exports():
    """Importing app.mcp_server loads __init__ and exposes expected symbols."""
    assert RAG_QUERY == "rag_query"
    assert CONFLUENCE_INTELLIGENT_ANALYZE == "confluence_intelligent_analyze"
    assert MCPTask(task_id="i", task_type=RAG_QUERY).is_rag()
    set_progress_callback(None)
    set_cancel_check(None)
    assert LIFECYCLE_QUEUED == "queued"
    assert LIFECYCLE_SUCCESS == "success"
    assert hasattr(confluence_tasks, "run_confluence_task")
    enqueue(MCPTask(task_id="t", task_type=RAG_QUERY))
    assert not is_empty()
    dequeue()
