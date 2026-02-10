# MCP task queue: single queue, RAG-first, Confluence FIFO / high-priority jump.

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any

# RAG task types (unchanged)
RAG_QUERY = "rag_query"
RAG_SEARCH = "rag_search"
RAG_OVERVIEW = "rag_overview"
RAG_INDEX = "rag_index"

# Confluence task types
CONFLUENCE_INTELLIGENT_ANALYZE = "confluence_intelligent_analyze"
CONFLUENCE_INTELLIGENT_MATCH = "confluence_intelligent_match"
CONFLUENCE_INTELLIGENT_FORMAT = "confluence_intelligent_format"
CONFLUENCE_INTELLIGENT_CREATE = "confluence_intelligent_create"
CONFLUENCE_DOCUMENT_PROJECT = "confluence_document_project"

RAG_TASK_TYPES = frozenset({RAG_QUERY, RAG_SEARCH, RAG_OVERVIEW, RAG_INDEX})
CONFLUENCE_TASK_TYPES = frozenset(
    {
        CONFLUENCE_INTELLIGENT_ANALYZE,
        CONFLUENCE_INTELLIGENT_MATCH,
        CONFLUENCE_INTELLIGENT_FORMAT,
        CONFLUENCE_INTELLIGENT_CREATE,
        CONFLUENCE_DOCUMENT_PROJECT,
    }
)
ALL_TASK_TYPES = RAG_TASK_TYPES | CONFLUENCE_TASK_TYPES


class FailureType(str, Enum):
    TRANSIENT = "transient"  # network, rate limit
    NON_TRANSIENT = "non_transient"  # auth, validation, content


@dataclass
class MCPTask:
    task_id: str
    task_type: str
    params: dict[str, Any] = field(default_factory=dict)
    high_priority: bool = False
    retry_count: int = 0
    last_failure_type: FailureType | None = None
    cancelled: bool = False

    def is_rag(self) -> bool:
        return self.task_type in RAG_TASK_TYPES

    def is_confluence(self) -> bool:
        return self.task_type in CONFLUENCE_TASK_TYPES


# Two-tier: RAG deque first, then Confluence (FIFO; high-priority Confluence ahead of normal Confluence)
_rag_queue: deque[MCPTask] = deque()
_confluence_high: deque[MCPTask] = deque()
_confluence_normal: deque[MCPTask] = deque()
_lock = Lock()
_MAX_RETRIES = 3


def enqueue(task: MCPTask) -> None:
    if task.task_type not in ALL_TASK_TYPES:
        return
    with _lock:
        if task.is_rag():
            _rag_queue.append(task)
        elif task.is_confluence():
            if task.high_priority:
                _confluence_high.append(task)
            else:
                _confluence_normal.append(task)


def dequeue() -> MCPTask | None:
    with _lock:
        if _rag_queue:
            return _rag_queue.popleft()
        if _confluence_high:
            return _confluence_high.popleft()
        if _confluence_normal:
            return _confluence_normal.popleft()
        return None


def re_enqueue(task: MCPTask) -> None:
    """Re-queue a task (e.g. after transient failure for retry)."""
    task.retry_count += 1
    enqueue(task)


def max_retries() -> int:
    return _MAX_RETRIES


def is_empty() -> bool:
    with _lock:
        return not (_rag_queue or _confluence_high or _confluence_normal)
