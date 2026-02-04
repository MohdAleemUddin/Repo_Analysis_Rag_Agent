"""
Learning agent: learn from successful creations and feedback.
Calls example_manager to store examples, update embeddings, record learning.
TC-POS-010, TC-UC-004: feedback accepted and applied.
TC-E2E-004, TC-E2E-006: learning improvement cycle and measurable improvement.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from ..confluence.example_manager import (
    apply_feedback,
    get_collective_count,
    record_learning,
    store_example,
    update_embeddings_for_examples,
)


def on_creation_success(
    creation_id: str,
    content_profile: dict[str, Any],
    template_id: str,
    template_name: str,
    confidence_score: Optional[float] = None,
    intelligence_metrics: Optional[dict[str, Any]] = None,
    project_path: Optional[str] = None,
    db_execute: Optional[Any] = None,
    vector_store_upsert: Optional[Any] = None,
    examples_base_dir: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Called after a successful Confluence page creation.
    Stores the creation as an example, updates embeddings, records learning.
    Returns (learning_occurred, message) for Learning Indicator.
    """
    example_id, learning_occurred = store_example(
        content_profile=content_profile,
        template_id=template_id,
        template_name=template_name,
        confidence_score=confidence_score,
        intelligence_metrics=intelligence_metrics,
        project_path=project_path,
        creation_id=creation_id,
        db_execute=db_execute,
        examples_base_dir=examples_base_dir,
    )
    update_embeddings_for_examples(
        example_ids=[example_id],
        vector_store_upsert=vector_store_upsert,
        examples_base_dir=examples_base_dir,
    )
    if learning_occurred:
        record_learning(
            creation_id=creation_id,
            before_score=confidence_score or 0.0,
            after_score=confidence_score or 0.0,
            learning_type="template",
            db_execute=db_execute,
        )
    message = (
        "🎓 Intelligence Learning: System learned from this successful creation"
        if learning_occurred
        else ""
    )
    return learning_occurred, message


def learn_from_feedback(
    creation_id: str,
    intelligence_score: int,
    feedback_text: Optional[str] = None,
    db_execute: Optional[Any] = None,
    examples_base_dir: Optional[str] = None,
    db_ensure_creation: Optional[Callable[[str], bool]] = None,
    db_get_template_id: Optional[Callable[[str], Optional[str]]] = None,
    db_update_template: Optional[Callable[[str, float], bool]] = None,
) -> None:
    """
    Apply user feedback to improve AI (TC-POS-010, TC-UC-004).
    Updates metrics and applies improvements to template matching.
    """
    apply_feedback(
        creation_id=creation_id,
        intelligence_score=intelligence_score,
        feedback_text=feedback_text,
        db_execute=db_execute,
        examples_base_dir=examples_base_dir,
        db_ensure_creation=db_ensure_creation,
    )
    after_score = min(1.0, max(0.0, intelligence_score / 5.0))
    record_learning(
        creation_id=creation_id,
        before_score=0.0,
        after_score=after_score,
        learning_type="matching",
        db_execute=db_execute,
    )
    if db_get_template_id and db_update_template:
        try:
            template_id = db_get_template_id(creation_id)
            if template_id:
                db_update_template(template_id, after_score)
        except Exception:
            pass


def get_learning_indicator_message(learning_occurred: bool) -> str:
    """Message for UI: Learning Indicator (PRD §6.4)."""
    if learning_occurred:
        return "🎓 Intelligence Learning: System learned from this successful creation"
    return ""


def get_collective_intelligence_count(
    db_fetch_count: Optional[Any] = None,
    examples_base_dir: Optional[str] = None,
    team_sharing_opt_in: bool = True,
) -> int:
    """Count for 'Collective Intelligence: X examples from team'."""
    return get_collective_count(db_fetch_count=db_fetch_count, examples_base_dir=examples_base_dir, team_sharing_opt_in=team_sharing_opt_in)


def learn(feedback: str) -> None:
    """Legacy entrypoint; use learn_from_feedback with creation_id and score for full flow."""
    pass
