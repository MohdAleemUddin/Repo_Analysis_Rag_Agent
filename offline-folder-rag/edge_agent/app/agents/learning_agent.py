"""Learning agent: learns from feedback. Invoked only after main create completes (non-blocking)."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def learn(feedback: str, creation_metadata: dict[str, Any] | None = None) -> None:
    """
    Record feedback / store example for future template matching.
    Must not block the create response; called from background after create returns.
    """
    logger.info("Learning from feedback (background): %s", feedback[:200] if feedback else "")
