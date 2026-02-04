"""Integration agent: Confluence create via confluence_tools, retry, rate-limit, verification. Output: IntegrationResult."""

from __future__ import annotations

import concurrent.futures
import logging
from typing import Any

from app.agents.contracts import (
    IntegrationResult,
    PageInfo,
    VerificationResult,
)
from app.confluence.error_handler import record_failure, record_success
from app.confluence.prd_monitor import timer_create_e2e
from app.langchain.tools.confluence_tools import (
    confluence_create_page,
    confluence_get_page,
)

from app.agents.learning_agent import learn

logger = logging.getLogger(__name__)

_learning_executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=1, thread_name_prefix="confluence_learn"
)


def _verify_page(
    base_url: str,
    page_id: str,
    auth: tuple[str, str] | None,
    expected_title: str,
    expected_space: str,
) -> VerificationResult:
    """Verify created page: get page and check key fields."""
    checks: list[str] = []
    try:
        page = confluence_get_page(base_url=base_url, page_id=page_id, auth=auth)
        checks.append("get_page_ok")
        if str(page.get("id")) == str(page_id):
            checks.append("id_match")
        if expected_title and page.get("title") == expected_title:
            checks.append("title_match")
        if expected_space and page.get("space", {}).get("key") == expected_space:
            checks.append("space_match")
        passed = len(checks) >= 2
        return VerificationResult(passed=passed, checks=checks)
    except Exception as e:
        logger.warning("Verification failed: %s", e)
        return VerificationResult(passed=False, checks=["verification_error"])


def create_page(
    base_url: str,
    space_key: str,
    title: str,
    body_html: str,
    auth: tuple[str, str] | None = None,
) -> IntegrationResult:
    """
    Create page via confluence_tools only. E2E timer, retries and rate-limit in tools.
    Verifies after creation. Returns IntegrationResult.
    """
    with timer_create_e2e():
        retries_used = 0
        rate_limit_state = "ok"
        try:
            result = confluence_create_page(
                base_url=base_url,
                space_key=space_key,
                title=title,
                body_storage_value=body_html,
                auth=auth,
            )
            record_success()
        except Exception as e:
            record_failure(auto_recovered=False, user_intervention=False)
            raise

        page_id = str(result.get("id", ""))
        page_title = result.get("title", title)
        space_obj = result.get("space", {})
        space_key_result = space_obj.get("key", space_key) if isinstance(space_obj, dict) else space_key
        links = result.get("_links", {}) or {}
        webui = links.get("webui", "") if isinstance(links, dict) else ""
        base = base_url.rstrip("/")
        page_url = f"{base}{webui}" if webui else f"{base}/pages/viewpage.action?pageId={page_id}"

        verification = _verify_page(
            base_url=base_url,
            page_id=page_id,
            auth=auth,
            expected_title=page_title,
            expected_space=space_key_result,
        )

        return IntegrationResult(
            page=PageInfo(
                id=page_id,
                url=page_url,
                title=page_title,
                space=space_key_result,
            ),
            intelligence_tag="AI-Formatted",
            retries_used=retries_used,
            rate_limit_state=rate_limit_state,
            verification=verification,
        )


def schedule_learning_after_create(
    feedback: str, creation_metadata: dict[str, Any] | None = None
) -> None:
    """Schedule learning in background. Only after successful create. No token leakage."""

    def _run() -> None:
        try:
            learn(feedback, creation_metadata)
        except Exception as e:
            logger.exception("Background learning failed: %s", e)

    _learning_executor.submit(_run)
