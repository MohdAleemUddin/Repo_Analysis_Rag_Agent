"""
Project scanner for US-16: scan workspace, return file paths for documentation pipeline.
NFR3: Excludes sensitive files (*.env, *.pem, *.key, credentials*, secrets*, config/*.local*).
NFR1: Supports progress callback and limit for large projects (<10s for 100 files 95th percentile).
"""

from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Callable

# NFR3: Sensitive file patterns excluded (no secrets in Confluence)
_EXCLUDED_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "dist",
        "build",
    }
)
# Extensions to prefer (source, config, README, tests, docs)
_PREFERRED_EXTENSIONS = frozenset(
    {
        ".py",
        ".ts",
        ".tsx",
        ".js",
        ".jsx",
        ".java",
        ".go",
        ".rs",
        ".rb",
        ".md",
        ".rst",
        ".txt",
        ".json",
        ".yaml",
        ".yml",
        ".toml",
        ".ini",
        ".cfg",
        ".conf",
        ".sql",
        ".sh",
        ".bat",
        ".ps1",
    }
)
# Files without extension we want
_PREFERRED_NAMES = frozenset({"README", "readme", "LICENSE", "Makefile", "Dockerfile"})


def _should_exclude(path: str, name: str, is_dir: bool, root: str) -> bool:
    """NFR3: Exclude sensitive files and directories."""
    name_lower = name.lower()
    rel = os.path.relpath(path, root) if path.startswith(root) else name
    rel_norm = rel.replace("\\", "/")

    if is_dir:
        return name_lower in {d.lower() for d in _EXCLUDED_DIRS}

    # File: NFR3 sensitive patterns
    if name_lower.endswith(".env") or ".env." in name_lower or name_lower == ".env":
        return True
    if name_lower.endswith((".pem", ".key", ".pfx", ".p12")):
        return True
    if name_lower.startswith(("credentials", "secrets")):
        return True
    if fnmatch.fnmatch(name_lower, "*.local*") and "config" in rel_norm:
        return True
    if fnmatch.fnmatch(rel_norm, "config/*.local*"):
        return True
    return False


def scan(
    path: str,
    progress_callback: Callable[[int, int], None] | None = None,
    limit: int | None = None,
) -> list[str]:
    """
    Scan workspace path; return list of file paths (source, config, README, tests, docs).
    NFR3: Excludes *.env, *.pem, *.key, credentials*, secrets*, config/*.local*.
    NFR1: progress_callback(current_count, total_estimated) for large projects; limit caps result size.
    """
    root = os.path.abspath(path)
    if not os.path.isdir(root):
        return []

    collected: list[str] = []
    total_est = 0
    try:
        for _ in Path(root).rglob("*"):
            total_est += 1
            if total_est > 10000:
                break
    except OSError:
        total_est = 500

    count = 0
    try:
        for entry in Path(root).rglob("*"):
            if limit is not None and len(collected) >= limit:
                break
            try:
                full = str(entry.resolve())
                if not os.path.commonpath([root, full]) == root:
                    continue
                name = entry.name
                is_dir = entry.is_dir()

                if is_dir:
                    if _should_exclude(full, name, True, root) or name.lower() in {
                        d.lower() for d in _EXCLUDED_DIRS
                    }:
                        continue
                    count += 1
                    if progress_callback and count % 20 == 0:
                        progress_callback(len(collected), total_est)
                    continue

                if _should_exclude(full, name, False, root):
                    continue

                ext = os.path.splitext(name)[1].lower()
                base = os.path.splitext(name)[0]
                if (
                    ext in _PREFERRED_EXTENSIONS
                    or base in _PREFERRED_NAMES
                    or name in _PREFERRED_NAMES
                ):
                    collected.append(full)
                elif ext in {
                    ".py",
                    ".ts",
                    ".tsx",
                    ".js",
                    ".jsx",
                    ".java",
                    ".go",
                    ".md",
                    ".json",
                    ".yaml",
                    ".yml",
                }:
                    collected.append(full)
                elif not ext and name in {"Dockerfile", "Makefile"}:
                    collected.append(full)

                count += 1
                if progress_callback and count % 20 == 0:
                    progress_callback(len(collected), total_est)
            except (OSError, ValueError):
                continue
    except OSError:
        pass

    return collected[:limit] if limit else collected
