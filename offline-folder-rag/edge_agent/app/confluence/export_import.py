"""
Export/import learned examples in PRD §7.2 format.
Export: content profiles, template refs, success metrics; exclude file contents and user info (NFR3).
Import: validate, merge/dedupe, refresh embeddings.
NFR1: Export <3s for 100 examples; Import <5s for 100.
"""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional

from .example_manager import (
    _content_profile_hash,
    _get_file_examples,
    get_examples,
    store_example,
    update_embeddings_for_examples,
)

# NFR3: keys never included in export (no file contents, no user info); anonymize for team sharing
_SENSITIVE_KEYS = frozenset({
    "file_contents", "user_id", "created_page_url", "raw_content", "file_paths",
    "user_info", "files_included", "content_raw", "body", "text_content",
    "feedback_text", "feedback_comment", "feedback", "project_path",
})

# Path to canonical schema (PRD §7.2)
_EDGE_AGENT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_REPO_ROOT = os.path.abspath(os.path.join(_EDGE_AGENT_ROOT, "..", ".."))
_SCHEMA_DIR = os.path.join(_REPO_ROOT, "confluence_data", "examples")
_EXPORT_FORMAT_PATH = os.path.join(_SCHEMA_DIR, "export_format.json")


def _strip_sensitive_data(obj: Any) -> Any:
    """Remove keys that must not appear in export (NFR3)."""
    if isinstance(obj, dict):
        return {k: _strip_sensitive_data(v) for k, v in obj.items() if k not in _SENSITIVE_KEYS}
    if isinstance(obj, list):
        return [_strip_sensitive_data(x) for x in obj]
    return obj


def _load_schema() -> dict[str, Any]:
    if os.path.isfile(_EXPORT_FORMAT_PATH):
        with open(_EXPORT_FORMAT_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"required": ["version", "exported_at", "examples"], "definitions": {}}


def _validate_export_payload(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    """Validate export payload; return list of error messages."""
    errs: list[str] = []
    for key in schema.get("required", ["version", "exported_at", "examples"]):
        if key not in data:
            errs.append(f"Missing required field: '{key}'.")
    if "examples" in data:
        if not isinstance(data["examples"], list):
            errs.append("'examples' must be an array.")
        else:
            defn = (schema.get("definitions") or {}).get("example") or {}
            req = defn.get("required", ["content_profile", "template_ref", "intelligence_metrics"])
            for i, ex in enumerate(data["examples"]):
                if not isinstance(ex, dict):
                    errs.append(f"examples[{i}] must be an object.")
                    continue
                for r in req:
                    if r not in ex:
                        errs.append(f"examples[{i}] missing required field: '{r}'.")
                if "template_ref" in ex and isinstance(ex["template_ref"], dict):
                    if "template_id" not in ex["template_ref"] or "template_name" not in ex["template_ref"]:
                        errs.append(f"examples[{i}].template_ref must have template_id and template_name.")
    return errs


def export_examples(
    project_path: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    template_type: Optional[str] = None,
    db_fetch: Optional[Any] = None,
    examples_base_dir: Optional[str] = None,
) -> str:
    """
    Export learned examples as JSON string matching PRD §7.2.
    Excludes sensitive data (file contents, user info). NFR1: <3s for 100 examples.
    """
    t0 = time.perf_counter()
    examples = get_examples(
        project_path=project_path,
        from_date=from_date,
        to_date=to_date,
        template_type=template_type,
        db_fetch=db_fetch,
        examples_base_dir=examples_base_dir,
    )
    out: list[dict[str, Any]] = []
    for ex in examples:
        content_profile = _strip_sensitive_data(ex.get("content_profile") or {})
        template_ref = ex.get("template_ref") or {}
        metrics = ex.get("intelligence_metrics") or {}
        if isinstance(metrics, dict) and "confidence_score" not in metrics and ex.get("confidence_score") is not None:
            metrics = {**metrics, "confidence_score": ex["confidence_score"]}
        conf = ex.get("confidence_score")
        if conf is not None:
            conf = round(float(conf), 2)
        emb = ex.get("intelligence_embedding")
        if emb is not None and hasattr(emb, "__len__") and len(emb) != 1536:
            emb = None
        out.append({
            "content_profile": content_profile,
            "template_ref": {
                "template_id": template_ref.get("template_id", ""),
                "template_name": template_ref.get("template_name", ""),
            },
            "intelligence_metrics": metrics,
            "confidence_score": conf,
            "user_feedback": ex.get("user_feedback") if isinstance(ex.get("user_feedback"), (int, type(None))) else None,
            "intelligence_embedding": emb,
            "learned_at": ex.get("learned_at"),
            "content_profile_hash": ex.get("content_profile_hash"),
        })
    payload = {
        "version": 1,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "template_type_filter": template_type,
        "project_path_filter": project_path,
        "examples": out,
    }
    elapsed = time.perf_counter() - t0
    if len(examples) >= 100 and elapsed > 3.0:
        import logging
        logging.warning("NFR1: export took %.2fs for %d examples (target <3s)", elapsed, len(examples))
    return json.dumps(payload, indent=2)


def validate_import_payload(payload: str | dict[str, Any]) -> tuple[bool, Optional[list[dict[str, Any]]], Optional[str]]:
    """
    Validate import JSON. Returns (ok, examples_list, error_message).
    TC-NEG-006, TC-NEG-015: clear error with format guidance on failure.
    """
    schema = _load_schema()
    if isinstance(payload, str):
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as e:
            return False, None, (
                f"Invalid format: JSON could not be parsed. {e!s} "
                "Ensure the file matches the PRD §7.2 export format. See confluence_data/examples/export_format.json."
            )
    else:
        data = payload
    if not isinstance(data, dict):
        return False, None, (
            "Invalid format: root must be an object with 'version', 'exported_at', and 'examples'. "
            "See confluence_data/examples/export_format.json for the exact schema."
        )
    errs = _validate_export_payload(data, schema)
    if errs:
        return False, None, (
            "Validation error: " + " ".join(errs) +
            " Import file must match PRD §7.2 export format. See confluence_data/examples/export_format.json."
        )
    return True, data.get("examples", []), None


def import_examples(
    payload: str | dict[str, Any],
    merge: bool = True,
    db_execute: Optional[Any] = None,
    vector_store_upsert: Optional[Any] = None,
    examples_base_dir: Optional[str] = None,
) -> tuple[int, str]:
    """
    Import JSON examples: validate, merge/dedupe, persist, refresh embeddings.
    Returns (imported_count, message). NFR1: <5s for 100 examples.
    TC-POS-008: valid import -> examples imported.
    """
    ok, examples_list, err = validate_import_payload(payload)
    if not ok or err:
        return 0, err or "Invalid format."
    if not examples_list:
        return 0, "Intelligence Examples Imported: 0 new examples learned"

    t0 = time.perf_counter()
    existing_hashes: set[str] = set()
    try:
        existing = _get_file_examples(examples_base_dir)
        for ex in existing:
            h = ex.get("content_profile_hash")
            if h:
                existing_hashes.add(h)
    except Exception:
        pass

    imported = 0
    for ex in examples_list:
        content_profile = _strip_sensitive_data(ex.get("content_profile") or {})
        template_ref = ex.get("template_ref") or {}
        template_id = template_ref.get("template_id") or ""
        template_name = template_ref.get("template_name") or ""
        metrics = ex.get("intelligence_metrics") or {}
        profile_hash = ex.get("content_profile_hash") or _content_profile_hash(content_profile)
        if merge and profile_hash in existing_hashes:
            continue
        existing_hashes.add(profile_hash)
        emb = ex.get("intelligence_embedding")
        if emb is not None and (not hasattr(emb, "__len__") or len(emb) != 1536):
            emb = None
        uf = ex.get("user_feedback")
        if uf is not None and (uf < 1 or uf > 5):
            uf = None
        eid, _ = store_example(
            content_profile=content_profile,
            template_id=template_id,
            template_name=template_name,
            confidence_score=metrics.get("confidence_score") if isinstance(metrics, dict) else None,
            intelligence_metrics=metrics if isinstance(metrics, dict) else {},
            project_path=None,
            db_execute=db_execute,
            examples_base_dir=examples_base_dir,
            intelligence_embedding=emb,
            user_feedback=uf,
        )
        imported += 1

    update_embeddings_for_examples(
        vector_store_upsert=vector_store_upsert,
        examples_base_dir=examples_base_dir,
    )
    elapsed = time.perf_counter() - t0
    if len(examples_list) >= 100 and elapsed > 5.0:
        import logging
        logging.warning("NFR1: import took %.2fs for %d examples (target <5s)", elapsed, len(examples_list))
    msg = f"Intelligence Examples Imported: {imported} new examples learned"
    return imported, msg


def export(data: object) -> str:
    """Legacy entrypoint; delegates to export_examples with no filters."""
    return export_examples()
