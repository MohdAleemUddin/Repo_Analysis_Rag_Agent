# Configuration for edge agent and Confluence integration.
# Reuse existing DB pattern; reference connection/session from app context.

from typing import Any

# --- NFR1 Performance constants (PRD) ---
ANALYSIS_MAX_SECONDS_PER_FILE = 3
TEMPLATE_SELECTION_MAX_SECONDS = 2
CREATE_E2E_MAX_SECONDS = 15
CONFLUENCE_MEMORY_LIMIT_MB = 300

# --- Confluence tuning knobs ---
CONFLUENCE_ANALYSIS_CACHE_ENABLED = True
CONFLUENCE_MAX_PARALLEL_FILES = 4  # Stay within 300MB
CONFLUENCE_LARGE_FILE_THRESHOLD_BYTES = 512 * 1024  # 512KB
CONFLUENCE_CHUNK_SIZE_BYTES = 64 * 1024  # 64KB
CONFLUENCE_CPU_THROTTLE_ENABLED = True
CONFLUENCE_ANALYSIS_CACHE_MAX_ENTRIES = 500
CONFLUENCE_ANALYSIS_CACHE_TTL_SECONDS = 3600  # 1 hour

# --- App config (placeholder for existing load_config) ---
_app_config: dict[str, Any] = {}


def load_config() -> None:
    """Load application config. Reuse existing DB connection from app context."""
    global _app_config
    _app_config = {}


def get_app_config() -> dict[str, Any]:
    """Return current app config (e.g. for DB session reference)."""
    return _app_config
