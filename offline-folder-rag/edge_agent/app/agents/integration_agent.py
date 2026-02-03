"""Integration agent: Confluence API create with e2e timer; triggers background learning only on success. Error recovery: no partial create; no learning on failure."""

import concurrent.futures
import logging
from typing import Any

from app.confluence.client import create_page as confluence_create_page
from app.confluence.error_handler import record_failure, record_success
from app.confluence.prd_monitor import timer_create_e2e

from app.agents.learning_agent import learn

logger = logging.getLogger(__name__)

_learning_executor = concurrent.futures.ThreadPoolExecutor(max_workers=1, thread_name_prefix="confluence_learn")


def create_page(
    base_url: str,
    space_key: str,
    title: str,
    body_html: str,
    auth: tuple[str, str] | None = None,
) -> dict[str, Any]:
    """
    Create Confluence page; wrapped with e2e timer. Client performs network retries (3x backoff) and rate-limit wait+retry.
    On success: record_success, return result. On failure: record_failure, re-raise (no partial page, no learning).
    """
    with timer_create_e2e():
        try:
            result = confluence_create_page(
                base_url=base_url,
                space_key=space_key,
                title=title,
                body_storage_value=body_html,
                auth=auth,
            )
            record_success()
            return result
        except Exception as e:
            record_failure(auto_recovered=False, user_intervention=False)
            raise


def schedule_learning_after_create(feedback: str, creation_metadata: dict[str, Any] | None = None) -> None:
    """Schedule learning in background. Call only after successful create; no learning on failure."""
    def _run() -> None:
        try:
            learn(feedback, creation_metadata)
        except Exception as e:
            logger.exception("Background learning failed: %s", e)

    _learning_executor.submit(_run)
