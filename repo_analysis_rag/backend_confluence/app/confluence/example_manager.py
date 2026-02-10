"""
Example manager: CRUD for learned examples, store success as examples,
trigger embedding updates, and learning indicator trigger.
PRD §7.2 Example-Based Intelligence; §8.1 intelligence_examples, intelligence_learning.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Callable, Optional
from uuid import uuid4

# Default path for file-based fallback (no DB): repo_root/confluence_data/examples
_EDGE_AGENT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
_REPO_ROOT = os.path.abspath(os.path.join(_EDGE_AGENT_ROOT, "..", ".."))
_DEFAULT_EXAMPLES_DIR = os.path.join(_REPO_ROOT, "confluence_data", "examples")


def _examples_file_path(base_dir: Optional[str] = None) -> str:
    d = base_dir or _DEFAULT_EXAMPLES_DIR
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "learned_examples.json")


def _content_profile_hash(content_profile: dict[str, Any]) -> str:
    canonical = json.dumps(content_profile, sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _get_file_examples(base_dir: Optional[str] = None) -> list[dict[str, Any]]:
    path = _examples_file_path(base_dir)
    if not os.path.isfile(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("examples", [])


def _save_file_examples(
    examples: list[dict[str, Any]], base_dir: Optional[str] = None
) -> None:
    path = _examples_file_path(base_dir)
    data = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "examples": examples,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _embedding_to_db(emb: Optional[list[float]]) -> Optional[str]:
    """Format 1536-dim list for PostgreSQL vector type."""
    if not emb or len(emb) != 1536:
        return None
    return "[" + ",".join(str(float(x)) for x in emb) + "]"


def store_example(
    content_profile: dict[str, Any],
    template_id: str,
    template_name: str,
    confidence_score: Optional[float] = None,
    intelligence_metrics: Optional[dict[str, Any]] = None,
    project_path: Optional[str] = None,
    creation_id: Optional[str] = None,
    db_execute: Optional[Callable[..., Any]] = None,
    examples_base_dir: Optional[str] = None,
    intelligence_embedding: Optional[list[float]] = None,
    user_feedback: Optional[int] = None,
) -> tuple[str, bool]:
    """
    Store a successful creation as an example. Updates embeddings via callback if provided.
    intelligence_embedding: VECTOR(1536). user_feedback: 1-5 scale.
    Returns (example_id, learning_occurred) for Learning Indicator.
    """
    profile_hash = _content_profile_hash(content_profile)
    learned_at = datetime.now(timezone.utc).isoformat()
    example_id = str(uuid4())
    emb_db = _embedding_to_db(intelligence_embedding)

    if db_execute:
        try:
            db_execute(
                """
                INSERT INTO intelligence_examples
                (id, content_profile, template_used, intelligence_metrics, learned_at, confidence_score, improvement_suggestions, intelligence_embedding, user_feedback)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector, %s)
                """,
                (
                    example_id,
                    json.dumps(content_profile),
                    template_id,
                    json.dumps(intelligence_metrics or {}),
                    learned_at,
                    (
                        round(confidence_score, 2)
                        if confidence_score is not None
                        else None
                    ),
                    [],
                    emb_db,
                    user_feedback,
                ),
            )
            if creation_id:
                db_execute(
                    """
                    INSERT INTO intelligence_learning
                    (id, learning_type, after_score, learned_from, learned_at, learning_confidence)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        str(uuid4()),
                        "template",
                        confidence_score or 0.0,
                        creation_id,
                        learned_at,
                        confidence_score or 0.0,
                    ),
                )
            return example_id, True
        except Exception:
            pass

    examples = _get_file_examples(examples_base_dir)
    for ex in examples:
        if ex.get("content_profile_hash") == profile_hash:
            return ex.get("id", example_id), False
    record = {
        "id": example_id,
        "content_profile": content_profile,
        "template_ref": {"template_id": template_id, "template_name": template_name},
        "intelligence_metrics": intelligence_metrics or {},
        "learned_at": learned_at,
        "content_profile_hash": profile_hash,
        "confidence_score": (
            round(confidence_score, 2) if confidence_score is not None else None
        ),
        "project_path": project_path,
        "intelligence_embedding": (
            intelligence_embedding
            if intelligence_embedding and len(intelligence_embedding) == 1536
            else None
        ),
        "user_feedback": (
            user_feedback
            if user_feedback is not None and 1 <= user_feedback <= 5
            else None
        ),
    }
    if record["intelligence_metrics"] and confidence_score is not None:
        record["intelligence_metrics"].setdefault("confidence_score", confidence_score)
    examples.append(record)
    _save_file_examples(examples, examples_base_dir)
    return example_id, True


def get_examples(
    project_path: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    template_type: Optional[str] = None,
    template_id: Optional[str] = None,
    db_fetch: Optional[Callable[..., list[dict[str, Any]]]] = None,
    examples_base_dir: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Get examples for export; filters by project, date range, template type."""
    if db_fetch:
        try:
            return db_fetch(
                project_path=project_path,
                from_date=from_date,
                to_date=to_date,
                template_type=template_type,
                template_id=template_id,
            )
        except Exception:
            pass

    examples = _get_file_examples(examples_base_dir)
    if project_path:
        examples = [e for e in examples if e.get("project_path") == project_path]
    if from_date:
        examples = [e for e in examples if (e.get("learned_at") or "") >= from_date]
    if to_date:
        examples = [e for e in examples if (e.get("learned_at") or "") <= to_date]
    if template_type or template_id:
        if template_id:
            examples = [
                e
                for e in examples
                if (e.get("template_ref") or {}).get("template_id") == template_id
            ]
        if template_type:
            name = (template_type or "").lower()
            examples = [
                e
                for e in examples
                if name
                in ((e.get("template_ref") or {}).get("template_name") or "").lower()
            ]
    return examples


def update_embeddings_for_examples(
    example_ids: Optional[list[str]] = None,
    vector_store_upsert: Optional[Callable[..., None]] = None,
    examples_base_dir: Optional[str] = None,
) -> None:
    """Refresh vector embeddings after import or after storing new examples."""
    if vector_store_upsert:
        try:
            vector_store_upsert(example_ids=example_ids)
        except Exception:
            pass


def record_learning(
    creation_id: str,
    before_score: float,
    after_score: float,
    learning_type: str = "matching",
    db_execute: Optional[Callable[..., Any]] = None,
) -> None:
    """Record learning progress in intelligence_learning."""
    improvement = after_score - before_score
    if db_execute:
        try:
            db_execute(
                """
                INSERT INTO intelligence_learning
                (id, learning_type, before_score, after_score, improvement, learned_from, learned_at, learning_confidence)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    str(uuid4()),
                    learning_type,
                    before_score,
                    after_score,
                    improvement,
                    creation_id,
                    datetime.now(timezone.utc).isoformat(),
                    after_score,
                ),
            )
        except Exception:
            pass


def _feedback_file_path(base_dir: Optional[str] = None) -> str:
    d = base_dir or _DEFAULT_EXAMPLES_DIR
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "feedback_store.json")


def _get_file_feedback(base_dir: Optional[str] = None) -> list[dict[str, Any]]:
    path = _feedback_file_path(base_dir)
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("feedback", [])
    except Exception:
        return []


def _save_file_feedback(
    items: list[dict[str, Any]], base_dir: Optional[str] = None
) -> None:
    path = _feedback_file_path(base_dir)
    data = {
        "version": 1,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "feedback": items,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def apply_feedback(
    creation_id: str,
    intelligence_score: int,
    feedback_text: Optional[str] = None,
    db_execute: Optional[Callable[..., Any]] = None,
    examples_base_dir: Optional[str] = None,
    db_ensure_creation: Optional[Callable[[str], bool]] = None,
) -> None:
    """Apply user feedback to a creation; updates metrics for learning (TC-POS-010, TC-UC-004)."""
    if db_ensure_creation:
        try:
            db_ensure_creation(creation_id)
        except Exception:
            pass
    if db_execute:
        try:
            db_execute(
                "UPDATE intelligent_creations SET user_satisfaction = %s WHERE id = %s",
                (intelligence_score, creation_id),
            )
        except Exception:
            pass
    items = _get_file_feedback(examples_base_dir)
    items.append(
        {
            "creation_id": creation_id,
            "intelligence_score": intelligence_score,
            "learned_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    _save_file_feedback(items, examples_base_dir)


def get_collective_count(
    db_fetch_count: Optional[Callable[[], int]] = None,
    examples_base_dir: Optional[str] = None,
    team_sharing_opt_in: bool = True,
) -> int:
    """Return count of examples (for 'Collective Intelligence: X examples from team'). When team_sharing_opt_in is False, returns 0."""
    if not team_sharing_opt_in:
        return 0
    if db_fetch_count:
        try:
            return db_fetch_count()
        except Exception:
            pass
    return len(_get_file_examples(examples_base_dir))


def load_example(name: str) -> None:
    """Legacy placeholder; no-op."""
    pass
