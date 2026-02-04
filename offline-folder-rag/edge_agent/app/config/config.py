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
