<<<<<<< HEAD
# Central config: database + Confluence (PRD §5.2 FR6, User Story 10)
# Same PostgreSQL connection; connection overhead <5% over RAG baseline.
import os
from typing import Any

# Connection pool settings: keep overhead <5% over RAG baseline
_DEFAULT_POOL_MIN_SIZE = 1
_DEFAULT_POOL_MAX_SIZE = 5
_DEFAULT_POOL_TIMEOUT_SEC = 30
_DEFAULT_TEAM_SHARING_OPT_IN = True

_config_loaded = False


def load_config() -> None:
    """Load central config (env). Called at startup."""
    global _config_loaded
    _config_loaded = True


def get_database_config() -> dict[str, Any]:
    """
    Database config for Confluence and RAG (same instance).
    database_url: CONFLUENCE_DATABASE_URL or DATABASE_URL for same PostgreSQL.
    Pool settings tuned for <5% connection overhead.
    """
    url = os.environ.get("CONFLUENCE_DATABASE_URL") or os.environ.get("DATABASE_URL")
    min_size = int(os.environ.get("DB_POOL_MIN_SIZE", _DEFAULT_POOL_MIN_SIZE))
    max_size = int(os.environ.get("DB_POOL_MAX_SIZE", _DEFAULT_POOL_MAX_SIZE))
    timeout = int(os.environ.get("DB_POOL_TIMEOUT_SEC", _DEFAULT_POOL_TIMEOUT_SEC))
    return {
        "database_url": url,
        "pool_min_size": max(1, min(min_size, 20)),
        "pool_max_size": max(1, min(max_size, 20)),
        "pool_timeout_sec": max(5, min(timeout, 120)),
    }


def get_confluence_config() -> dict[str, Any]:
    """Confluence config (single source: this module). database_url same as RAG when unset."""
    db = get_database_config()
    opt_in = os.environ.get("CONFLUENCE_TEAM_SHARING_OPT_IN", "").strip().lower()
    team_sharing_opt_in = opt_in not in ("0", "false", "no") if opt_in else _DEFAULT_TEAM_SHARING_OPT_IN
    return {
        "team_sharing_opt_in": team_sharing_opt_in,
        "database_url": db.get("database_url"),
    }
=======
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
>>>>>>> 5fa35e2b268e4b9240b01b3b6ca998d64d057f27
