"""OpenAI client for RAG answer generation. Uses OPENAI_API_KEY from environment."""

from __future__ import annotations

import os
from typing import Any

from ..logging.logger import logger

# Model and base URL from env; no API key in code
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL")  # optional, for compatibility


def _format_citations_as_context(citations: list[dict[str, Any]]) -> str:
    """Turn citation list into a single context string for the LLM."""
    parts = []
    for i, c in enumerate(citations, 1):
        path = c.get("file_path") or c.get("path") or ""
        line = c.get("line_number") or c.get("line_start") or ""
        snippet = (c.get("snippet") or "").strip()
        parts.append(f"[{i}] {path}:{line}\n{snippet}")
    return "\n\n".join(parts) if parts else ""


def generate_answer_if_configured(
    query: str,
    citations: list[dict[str, Any]],
) -> str | None:
    """
    If OPENAI_API_KEY is set, call OpenAI Chat Completions with query and optional
    citations. Returns generated answer or None (caller uses fallback).
    """
    if not OPENAI_API_KEY or not OPENAI_API_KEY.strip():
        return None

    context = _format_citations_as_context(citations) if citations else ""

    try:
        from openai import OpenAI

        client_kw: dict[str, Any] = {"api_key": OPENAI_API_KEY.strip()}
        if OPENAI_BASE_URL and OPENAI_BASE_URL.strip():
            client_kw["base_url"] = OPENAI_BASE_URL.strip()
        client = OpenAI(**client_kw)

        if context.strip():
            user_content = (
                f"Context from the codebase:\n\n{context}\n\nQuestion: {query.strip()}"
            )
            system_content = (
                "Answer using only the provided code or documentation excerpts. Use plain, crisp English: short sentences, no filler or repetition. "
                "Synthesize into a clear summary; do not list or dump code or excerpts. Cite file paths and line numbers only when they add value. "
                "If the context does not contain the answer, say so in one sentence."
            )
        else:
            user_content = query.strip() or "Hello"
            system_content = (
                "Answer in plain, crisp English. Be brief. If no codebase context was provided, say so and answer generally in one or two sentences."
            )

        response = client.chat.completions.create(
            model=OPENAI_MODEL.strip(),
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            max_tokens=1024,
        )
        choice = response.choices[0] if response.choices else None
        if choice and choice.message and getattr(choice.message, "content", None):
            return (choice.message.content or "").strip()
        return None
    except Exception as exc:
        logger.warning("OpenAI answer generation failed: %s", exc)
        return None
