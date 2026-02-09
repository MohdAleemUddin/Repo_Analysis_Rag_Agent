"""Vector retrieval helpers used by the /ask endpoint."""

from __future__ import annotations

from itertools import chain, zip_longest
from pathlib import Path
from typing import Any, Mapping

try:
    from chromadb import Client
    from chromadb.config import Settings
except ImportError:  # pragma: no cover - optional dependency
    Client = None
    Settings = None

from ..logging.logger import logger
from ..tools.search import execute_ask_query

DEFAULT_TOP_K = 5
DEFAULT_CODE_COLLECTION = "code_chunks"
DEFAULT_DOC_COLLECTION = "doc_chunks"
DEFAULT_PERSIST_DIRECTORY = Path(__file__).resolve().parents[2] / ".chromadb"
DEFAULT_SEARCH_ROOT = Path(__file__).resolve().parents[3]


def _normalize_top_k(top_k: int | None) -> int:
    if top_k is None or top_k <= 0:
        return DEFAULT_TOP_K
    return top_k


def _build_client(persist_directory: Path | str | None) -> Client:
    directory = Path(persist_directory) if persist_directory else DEFAULT_PERSIST_DIRECTORY
    if Client is None or Settings is None:
        raise RuntimeError(
            "Chromadb dependency is missing. Install it via `pip install chromadb` to use vector retrieval."
        )
    return Client(
        Settings(
            persist_directory=str(directory),
            chroma_db_impl="duckdb+parquet",
            anonymized_telemetry=False,
        )
    )


def _coerce_line_number(value: Any) -> int:
    if value is None:
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _normalize_citation(citation: Mapping[str, Any] | None) -> dict[str, Any]:
    if not citation:
        citation = {}
    file_path = (
        str(citation.get("file_path") or citation.get("path") or citation.get("source") or "")
    )
    line_start = _coerce_line_number(
        citation.get("line_start") or citation.get("line_number") or citation.get("line")
    )
    line_end = _coerce_line_number(
        citation.get("line_end")
        or citation.get("line_start")
        or citation.get("line_number")
        or line_start
    )
    if line_end < line_start:
        line_end = line_start
    line_number = _coerce_line_number(citation.get("line_number") or line_start)
    snippet = (citation.get("snippet") or citation.get("line_text") or citation.get("document") or "")
    return {
        "file_path": file_path,
        "path": file_path,
        "line_number": line_number,
        "line_start": line_start,
        "line_end": line_end,
        "start_line": line_start,
        "end_line": line_end,
        "snippet": snippet,
    }


def _map_to_citation(metadata: Mapping[str, Any] | None, document: str | None) -> dict[str, Any]:
    data = dict(metadata or {})
    snippet = data.get("snippet") or (document or "")
    citation = {
        **data,
        "snippet": snippet,
    }
    return _normalize_citation(citation)


def _query_collection(
    client: Client,
    collection_name: str,
    query_text: str,
    top_k: int,
) -> list[dict[str, Any]]:
    try:
        collection = client.get_collection(collection_name)
    except Exception as exc:
        logger.warning("Chroma collection %s missing: %s", collection_name, exc)
        return []

    if top_k < 1:
        return []

    try:
        response = collection.query(
            query_texts=[query_text],
            n_results=top_k,
            include=["metadatas", "documents"],
        )
    except Exception as exc:  # pragma: no cover - best effort retrieval
        logger.warning("Chroma query failed for %s: %s", collection_name, exc)
        return []

    metadatas = response.get("metadatas", [[]])[0]
    documents = response.get("documents", [[]])[0]

    citations: list[dict[str, Any]] = []
    for metadata, document in zip_longest(metadatas, documents, fillvalue=None):
        citations.append(_map_to_citation(metadata, document))

    return citations


def _map_rg_match_to_citation(match: Mapping[str, Any]) -> dict[str, Any]:
    citation = {
        "path": match.get("path", ""),
        "line_number": match.get("line_number"),
        "line_start": match.get("line_number"),
        "line_end": match.get("line_number"),
        "snippet": (match.get("line_text") or "").strip(),
    }
    return _normalize_citation(citation)


def _dedupe_key(citation: Mapping[str, Any]) -> tuple[str, int, int]:
    file_path = str(citation.get("file_path") or citation.get("path") or "")

    raw_line_start = citation.get("line_start")
    if raw_line_start is None:
        raw_line_start = citation.get("line_number") or citation.get("line")
    line_start = _coerce_line_number(raw_line_start)

    raw_line_end = citation.get("line_end")
    if raw_line_end is None:
        raw_line_end = citation.get("line_start") or citation.get("line_number") or line_start
    line_end = _coerce_line_number(raw_line_end)

    if line_end < line_start:
        line_end = line_start

    return (file_path, line_start, line_end)


def merge_citations(
    *sources: list[dict[str, Any]],
    max_chunks: int | None = None,
) -> tuple[list[dict[str, Any]], bool]:
    seen: set[tuple[str, int, int]] = set()
    merged: list[dict[str, Any]] = []
    truncated = False
    limit = int(max_chunks) if isinstance(max_chunks, int) and max_chunks > 0 else None
    for citation in chain.from_iterable(sources):
        key = _dedupe_key(citation)
        if key in seen:
            continue
        if limit is not None and len(merged) >= limit:
            truncated = True
            break
        seen.add(key)
        merged.append(citation)
    return merged, truncated


def retrieve_vector_results(
    query: str,
    top_k: int | None = None,
    persist_directory: Path | str | None = None,
    code_collection: str = DEFAULT_CODE_COLLECTION,
    doc_collection: str = DEFAULT_DOC_COLLECTION,
    search_root: Path | str | None = DEFAULT_SEARCH_ROOT,
    ripgrep_limit: int = 200,
    max_context_chunks: int | None = None,
) -> dict[str, Any]:
    normalized_query = (query or "").strip()
    if not normalized_query:
        logger.info("Empty query received for vector retrieval.")
        return {"code": [], "docs": [], "merged": [], "truncated": False}

    effective_top_k = _normalize_top_k(top_k)
    client = _build_client(persist_directory)

    code_hits = _query_collection(client, code_collection, normalized_query, effective_top_k)
    doc_hits = _query_collection(client, doc_collection, normalized_query, effective_top_k)

    rg_hits: list[dict[str, Any]] = []
    if search_root:
        try:
            raw_matches = execute_ask_query(search_root, normalized_query, limit=ripgrep_limit)
            rg_hits = [_map_rg_match_to_citation(match) for match in raw_matches]
        except Exception as exc:
            logger.warning("Ripgrep query failed for %s: %s", normalized_query, exc)

    merged, truncated = merge_citations(
        code_hits, doc_hits, rg_hits, max_chunks=max_context_chunks
    )
    return {
        "code": code_hits,
        "docs": doc_hits,
        "merged": merged,
        "truncated": truncated,
    }
