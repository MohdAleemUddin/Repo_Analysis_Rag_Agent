import sys
import time
from pathlib import Path
import pytest

def _setup_path():
    repo_root = Path(__file__).resolve().parents[3]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

_setup_path()

from edge_agent.app.indexing import indexer

@pytest.fixture(autouse=True)
def reset_indexer_state():
    """Reset the global indexer state before each test."""
    # Accessing private variables for testing purposes
    indexer._repo_indexing_state.clear()
    indexer._indexed_files_so_far = 0
    indexer._last_index_completed_epoch_ms = 0
    yield

def test_indexing_flag_changes():
    """Test indexing flag changes during operations."""
    repo_id = "test-repo"
    
    assert indexer.is_indexing_in_progress(repo_id) is False
    
    indexer.mark_indexing_started(repo_id)
    assert indexer.is_indexing_in_progress(repo_id) is True
    
    indexer.mark_indexing_finished(repo_id)
    assert indexer.is_indexing_in_progress(repo_id) is False

def test_indexed_files_increments():
    """Test indexed_files_so_far increments correctly."""
    repo_id = "test-repo"
    indexer.mark_indexing_started(repo_id)
    
    stats = indexer.get_health_stats()
    assert stats["indexed_files_so_far"] == 0
    
    indexer.increment_indexed_files()
    indexer.increment_indexed_files()
    
    stats = indexer.get_health_stats()
    assert stats["indexed_files_so_far"] == 2

def test_last_index_completed_updates():
    """Test last_index_completed_epoch_ms updates after completion."""
    repo_id = "test-repo"
    
    stats_before = indexer.get_health_stats()
    assert stats_before["last_index_completed_epoch_ms"] == 0
    
    # Small sleep to ensure time moves forward if we were to compare with current time
    time.sleep(0.001)
    
    indexer.mark_indexing_started(repo_id)
    indexer.mark_indexing_finished(repo_id)
    
    stats_after = indexer.get_health_stats()
    assert stats_after["last_index_completed_epoch_ms"] > 0
    # Ensure it's a recent timestamp (within last 5 seconds)
    current_ms = int(time.time() * 1000)
    assert current_ms - stats_after["last_index_completed_epoch_ms"] < 5000

def test_indexing_context_manager():
    """Test the RepoIndexingLock context manager."""
    repo_id = "test-repo-ctx"
    
    assert indexer.is_indexing_in_progress(repo_id) is False
    
    with indexer.acquire_indexing_lock(repo_id):
        assert indexer.is_indexing_in_progress(repo_id) is True
        indexer.increment_indexed_files()
        
    assert indexer.is_indexing_in_progress(repo_id) is False
    stats = indexer.get_health_stats()
    assert stats["indexed_files_so_far"] == 1
    assert stats["last_index_completed_epoch_ms"] > 0

def test_full_and_incremental_indexing_modes_logic():
    """
    Test indexing state logic for different scenarios.
    Note: The indexer.py currently doesn't store 'mode' in its health stats,
    but we test that the health tracking works regardless of the 'mode' 
    that would be passed to the indexer's higher level functions.
    """
    repo_id = "test-repo-mode"
    
    # Simulate Full Indexing
    with indexer.acquire_indexing_lock(repo_id):
        indexer.increment_indexed_files()
        indexer.increment_indexed_files()
    
    stats = indexer.get_health_stats()
    assert stats["indexed_files_so_far"] == 2
    last_completed = stats["last_index_completed_epoch_ms"]
    
    # Simulate Incremental Indexing
    time.sleep(0.001)
    with indexer.acquire_indexing_lock(repo_id):
        indexer.increment_indexed_files()
    
    stats = indexer.get_health_stats()
    assert stats["indexed_files_so_far"] == 1 # mark_indexing_started resets it to 0
    assert stats["last_index_completed_epoch_ms"] > last_completed
