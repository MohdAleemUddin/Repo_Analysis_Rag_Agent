"""Integration agent: Confluence API create with e2e timer; triggers background learning after result."""

import concurrent.futures
import logging
from typing import Any

from app.confluence.client import create_page as confluence_create_page
from app.confluence.prd_monitor import timer_create_e2e

from app.agents.learning_agent import learn

logger = logging.getLogger(__name__)

# Background executor for learning (fire-and-forget)
_learning_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="confluence_learn"
)


def create_page(
    base_url: str,
    space_key: str,
    title: str,
    body_html: str,
    auth: tuple[str, str] | None = None,
) -> dict[str, Any]:
    """
    Create Confluence page; wrapped with e2e timer (< 15s including API).
    Returns API response dict.
    """
    with timer_create_e2e():
        return confluence_create_page(
            base_url=base_url,
            space_key=space_key,
            title=title,
            body_storage_value=body_html,
            auth=auth,
        )


def schedule_learning_after_create(
    feedback: str, creation_metadata: dict[str, Any] | None = None
) -> None:
    """
    Schedule learning to run in background. Does not block; call after create result is returned to client.
    """

    def _run() -> None:
        try:
            learn(feedback, creation_metadata)
        except Exception as e:
            logger.exception("Background learning failed: %s", e)

    _learning_executor.submit(_run)
