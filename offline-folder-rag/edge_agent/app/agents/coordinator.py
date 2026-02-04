"""Coordinator: parallel analysis, memory checks, CPU throttling."""

import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from app.config.config import (
    CONFLUENCE_CPU_THROTTLE_ENABLED,
    CONFLUENCE_MAX_PARALLEL_FILES,
)
from app.confluence.prd_monitor import (
    check_memory_before_step,
    get_current_record,
    start_operation,
)

from app.agents.content_analysis_agent import analyze_file_with_timer
from app.agents.formatting_agent import format_content
from app.agents.integration_agent import create_page as integration_create_page
from app.agents.integration_agent import schedule_learning_after_create
from app.agents.pattern_matching_agent import match

logger = logging.getLogger(__name__)


def run_analyze(file_contents: list[str]) -> dict[str, Any]:
    """
    Analyze multiple files in parallel (up to CONFLUENCE_MAX_PARALLEL_FILES).
    Checks memory before each batch; yields to avoid starving UI (CPU throttle).
    Returns {"analyses": [...], "template": {...}}.
    """
    start_operation()
    analyses: list[dict[str, Any]] = []
    max_workers = min(CONFLUENCE_MAX_PARALLEL_FILES, len(file_contents)) or 1

    def analyze_one(idx: int, content: str) -> tuple[int, dict[str, Any]]:
        if not check_memory_before_step():
            return idx, {"error": "memory_limit", "skipped": True}
        return idx, analyze_file_with_timer(content, file_index=idx)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(analyze_one, i, c): i for i, c in enumerate(file_contents)
        }
        for future in as_completed(futures):
            if CONFLUENCE_CPU_THROTTLE_ENABLED:
                time.sleep(0)  # yield to other threads
            idx, result = future.result()
            if result.get("skipped"):
                continue
            analyses.append((idx, result))

    analyses.sort(key=lambda x: x[0])
    analysis_list = [a[1] for a in analyses]

    # Template selection (single call, already timed inside match())
    combined = "\n".join(str(a) for a in analysis_list)
    template_result = match(
        combined, analysis=analysis_list[0] if analysis_list else None
    )

    return {
        "analyses": analysis_list,
        "template": template_result,
    }


def run_create(
    base_url: str,
    space_key: str,
    title: str,
    body_content: str,
    auth: tuple[str, str] | None = None,
    feedback_for_learning: str = "",
) -> dict[str, Any]:
    """
    Create page (e2e timed in integration_agent), then schedule learning in background.
    Returns Confluence API response; learning runs after return.
    """
    start_operation()
    body_html = format_content(body_content)
    result = integration_create_page(
        base_url=base_url,
        space_key=space_key,
        title=title,
        body_html=body_html,
        auth=auth,
    )
    # Fire-and-forget learning; do not await
    if feedback_for_learning:
        schedule_learning_after_create(feedback_for_learning, result)
    return result


def get_operation_record() -> Any:
    """Return current performance record for the active operation."""
    return get_current_record()
