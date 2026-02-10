# Context analyzer for RAG chat: mentioned files, related files, project type (US-2).
# No vector/Chroma usage; Chroma only for template matching per PRD §4.3.4.

from __future__ import annotations

import os
import re
from typing import Any

# Last 5 messages max for analysis
MAX_CHAT_MESSAGES = 5

# Patterns for file paths and function names in chat text
FILE_PATH_PATTERN = re.compile(
    r"(?:^|[\s\(\"\'\]])"
    r"([a-zA-Z0-9_][a-zA-Z0-9_./\\-]*\.(?:py|ts|tsx|js|jsx|java|go|rs|rb|md|json|yaml|yml|txt|cpp|h|c|hpp))"
    r"(?:[\s\)\"\'\]]|$)"
)
RELATIVE_PATH_PATTERN = re.compile(
    r"(?:from\s+[\w.]+\s+import|import\s+[\w.]+|include\s+[\"<]|require\s*\(\s*[\"\'])([a-zA-Z0-9_./\\-]+)"
)
FUNCTION_PATTERN = re.compile(r"\b(def|function|func|fn)\s+([a-zA-Z_][a-zA-Z0-9_]*)")
MODULE_PATTERN = re.compile(
    r"(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_.]*)\s+(?:import|$)"
)

# Project type labels by detected patterns
PROJECT_TYPE_LABELS: dict[str, str] = {
    "python_fastapi": "Python FastAPI code",
    "python_api": "Python API code",
    "python": "Python code",
    "typescript": "TypeScript code",
    "javascript": "JavaScript code",
    "react": "React frontend code",
    "web_app": "Web application code",
    "docs": "Documentation",
    "config": "Configuration",
    "mixed": "Mixed project",
}


def _extract_file_paths(text: str) -> list[str]:
    """Extract file paths and path-like tokens from text."""
    seen: set[str] = set()
    out: list[str] = []
    for m in FILE_PATH_PATTERN.finditer(text):
        p = m.group(1).strip()
        if p and p not in seen and len(p) < 256:
            seen.add(p)
            out.append(p)
    for m in RELATIVE_PATH_PATTERN.finditer(text):
        p = m.group(1).strip().strip("'\"").strip()
        if p and p not in seen and len(p) < 256:
            seen.add(p)
            out.append(p)
    return out


def _extract_functions(text: str) -> list[str]:
    """Extract function names mentioned in text."""
    return [m.group(2) for m in FUNCTION_PATTERN.finditer(text)]


def _extract_modules(text: str) -> list[str]:
    """Extract module names from import/from lines."""
    return [m.group(1).strip() for m in MODULE_PATTERN.finditer(text)]


def _resolve_related_files(
    mentioned: list[str],
    workspace_path: str,
) -> list[str]:
    """Resolve related files: same directory, common extensions. No filesystem crawl if not available."""
    related: list[str] = []
    if not workspace_path or not os.path.isdir(workspace_path):
        return related
    try:
        for base in mentioned[:20]:
            dir_part = os.path.dirname(base)
            if not dir_part:
                dir_part = "."
            abs_dir = os.path.normpath(os.path.join(workspace_path, dir_part))
            if not os.path.isdir(abs_dir):
                continue
            try:
                for name in os.listdir(abs_dir)[:50]:
                    if name.startswith("."):
                        continue
                    full = os.path.join(dir_part, name) if dir_part != "." else name
                    if full not in mentioned and full not in related:
                        if any(
                            full.endswith(ext)
                            for ext in (
                                ".py",
                                ".ts",
                                ".tsx",
                                ".js",
                                ".jsx",
                                ".md",
                                ".json",
                            )
                        ):
                            related.append(full)
            except OSError:
                continue
    except Exception:
        pass
    return related[:30]


def _detect_project_type(messages: list[dict[str, Any]], selected_text: str) -> str:
    """Infer project type from chat and selection for badge (e.g. Python FastAPI code)."""
    combined = selected_text or ""
    for m in messages:
        if isinstance(m, dict):
            combined += " " + (
                m.get("content") or m.get("text") or str(m.get("message", ""))
            )
        else:
            combined += " " + str(m)
    combined = (combined or "").lower()
    if "fastapi" in combined or "uvicorn" in combined and "python" in combined:
        return PROJECT_TYPE_LABELS["python_fastapi"]
    if "from fastapi" in combined or "import fastapi" in combined:
        return PROJECT_TYPE_LABELS["python_fastapi"]
    if ".py" in combined and ("def " in combined or "import " in combined):
        return PROJECT_TYPE_LABELS["python_api"]
    if "react" in combined or ".tsx" in combined or ".jsx" in combined:
        return PROJECT_TYPE_LABELS["react"]
    if "typescript" in combined or ".ts" in combined:
        return PROJECT_TYPE_LABELS["typescript"]
    if "readme" in combined and not any(
        x in combined for x in ["def ", "import ", ".py"]
    ):
        return PROJECT_TYPE_LABELS["docs"]
    return PROJECT_TYPE_LABELS["mixed"]


def _detect_language(mentioned: list[str], selected_text: str) -> str:
    """Detect primary language from file extensions and selection."""
    exts: dict[str, int] = {}
    for p in mentioned:
        if "." in p:
            ext = p.rsplit(".", 1)[-1].lower()
            exts[ext] = exts.get(ext, 0) + 1
    if (selected_text or "").strip():
        for ext, label in [
            ("py", "Python"),
            ("ts", "TypeScript"),
            ("tsx", "TypeScript"),
            ("js", "JavaScript"),
            ("jsx", "JavaScript"),
            ("go", "Go"),
            ("rs", "Rust"),
            ("rb", "Ruby"),
            ("java", "Java"),
        ]:
            if (
                f".{ext}" in (selected_text or "").lower()
                or "def " in (selected_text or "")
                or "import " in (selected_text or "")
            ):
                if ext == "py":
                    return "Python"
                if ext in ("ts", "tsx"):
                    return "TypeScript"
                if ext in ("js", "jsx"):
                    return "JavaScript"
    if exts.get("py", 0) >= max(exts.values(), default=0):
        return "Python"
    if exts.get("ts", 0) + exts.get("tsx", 0) >= max(exts.values(), default=0):
        return "TypeScript"
    if exts.get("js", 0) + exts.get("jsx", 0) >= max(exts.values(), default=0):
        return "JavaScript"
    if exts.get("go", 0):
        return "Go"
    if exts.get("rs", 0):
        return "Rust"
    return "Mixed"


def _should_suggest_readme(mentioned: list[str]) -> bool:
    """True when code files are present and no README in mentioned."""
    code_ext = (".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java")
    has_code = any(p.lower().endswith(code_ext) for p in mentioned)
    has_readme = any(
        p.lower().endswith(("readme.md", "readme.txt"))
        or p.lower().replace("\\", "/").rstrip("/").endswith("/readme")
        for p in mentioned
    )
    return bool(has_code and not has_readme)


def analyze_chat_context(
    messages: list[dict[str, Any]],
    selected_text: str | None = None,
    workspace_path: str | None = None,
) -> dict[str, Any]:
    """
    Analyze last 5 chat messages and optional selected text.
    Returns mentioned_files (prioritized from recent chat), related_files (imports/same module),
    project_type_label for badge. Completes in <1s; no vector store.
    """
    selected_text = (selected_text or "").strip()
    workspace_path = (workspace_path or "").strip()
    last_n = (
        messages[-MAX_CHAT_MESSAGES:] if len(messages) > MAX_CHAT_MESSAGES else messages
    )

    mentioned: list[str] = []
    for m in last_n:
        if not isinstance(m, dict):
            continue
        content = m.get("content") or m.get("text") or m.get("message") or ""
        mentioned.extend(_extract_file_paths(str(content)))
    mentioned.extend(_extract_file_paths(selected_text))

    # Deduplicate, preserve order (recent first)
    seen: set[str] = set()
    mentioned_dedup: list[str] = []
    for p in reversed(mentioned):
        n = p.replace("\\", "/")
        if n not in seen:
            seen.add(n)
            mentioned_dedup.append(p)
    mentioned_dedup.reverse()

    related = (
        _resolve_related_files(mentioned_dedup[:20], workspace_path)
        if workspace_path
        else []
    )
    project_type_label = _detect_project_type(last_n, selected_text)
    detected_language = _detect_language(mentioned_dedup, selected_text)
    should_suggest_readme = _should_suggest_readme(mentioned_dedup)

    return {
        "mentioned_files": mentioned_dedup[:50],
        "related_files": related[:30],
        "project_type_label": project_type_label,
        "detected_language": detected_language,
        "should_suggest_readme": should_suggest_readme,
    }


def analyze_context(text: str) -> dict[str, Any]:
    """Legacy entry: analyze a single text blob (e.g. selected text only)."""
    return analyze_chat_context(messages=[], selected_text=text, workspace_path=None)
