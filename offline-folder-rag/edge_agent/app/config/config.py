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
    global _config_loaded, _app_config
    _config_loaded = True
    _app_config = {}


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


def _merge_confluence_settings_from_env(out: dict[str, Any]) -> None:
    """Merge Confluence settings from env into out (rate limits, timeouts, learning, etc.)."""
    rate = os.environ.get("CONFLUENCE_RATE_LIMIT")
    if rate is not None:
        try:
            out["rate_limit"] = max(1, min(int(rate), 200))
        except ValueError:
            pass
    burst = os.environ.get("CONFLUENCE_BURST_LIMIT")
    if burst is not None:
        try:
            out["burst_limit"] = max(1, min(int(burst), 50))
        except ValueError:
            pass
    retry = os.environ.get("CONFLUENCE_RETRY_ATTEMPTS")
    if retry is not None:
        try:
            out["retry_attempts"] = max(0, min(int(retry), 10))
        except ValueError:
            pass
    if os.environ.get("CONFLUENCE_LEARNING_ENABLED", "").strip().lower() in ("0", "false", "no"):
        out["learning_enabled"] = False
    if os.environ.get("CONFLUENCE_LEARNING_ENABLED", "").strip().lower() in ("1", "true", "yes"):
        out["learning_enabled"] = True


def _validate_confluence_url(url: str | None) -> bool:
    """Optional URL format check; does not fail if Confluence unused."""
    if not url or not isinstance(url, str):
        return True
    s = url.strip().lower()
    if ".atlassian.net" in s and not s.startswith("https://"):
        return False
    return s.startswith(("http://", "https://"))


def get_confluence_config(workspace_id: str | None = None) -> dict[str, Any]:
    """
    Confluence config (single source: this module). database_url same as RAG when unset.
    Confluence credentials must be read from the existing RAG credential store (same
    mechanism as RAG; encrypted at rest per NFR3). Confluence operations must be
    invoked with workspace-scoped credentials so that project isolation is preserved.
    When workspace_id is provided, credentials (base_url, auth) are obtained from the
    encrypted credential store only; raises if missing or not from the store.
    Merges in Confluence settings from env (rate limits, learning, etc.).
    """
    from app.auth.credential_store import get_workspace_credentials

    db = get_database_config()
    opt_in = os.environ.get("CONFLUENCE_TEAM_SHARING_OPT_IN", "").strip().lower()
    team_sharing_opt_in = opt_in not in ("0", "false", "no") if opt_in else _DEFAULT_TEAM_SHARING_OPT_IN
    out: dict[str, Any] = {
        "team_sharing_opt_in": team_sharing_opt_in,
        "database_url": db.get("database_url"),
    }
    if workspace_id is not None:
        creds = get_workspace_credentials(service="confluence", workspace_id=workspace_id)
        out["base_url"] = creds["base_url"]
        out["auth"] = (creds["email"], creds["api_token"])
        out["is_encrypted"] = creds.get("is_encrypted", True)
        if not _validate_confluence_url(out.get("base_url")):
            out["_url_validation_warning"] = "Confluence Cloud URLs should use HTTPS"
    _merge_confluence_settings_from_env(out)
    return out

# --- NFR1 Performance constants (PRD) ---
ANALYSIS_MAX_SECONDS_PER_FILE = 3
TEMPLATE_SELECTION_MAX_SECONDS = 2
CREATE_E2E_MAX_SECONDS = 15
CONFLUENCE_MEMORY_LIMIT_MB = 300

# --- Confluence tuning knobs ---
CONFLUENCE_ANALYSIS_CACHE_ENABLED = True
CONFLUENCE_MAX_PARALLEL_FILES = 4
CONFLUENCE_LARGE_FILE_THRESHOLD_BYTES = 512 * 1024
CONFLUENCE_CHUNK_SIZE_BYTES = 64 * 1024
CONFLUENCE_CPU_THROTTLE_ENABLED = True
CONFLUENCE_ANALYSIS_CACHE_MAX_ENTRIES = 500
CONFLUENCE_ANALYSIS_CACHE_TTL_SECONDS = 3600

_app_config: dict[str, Any] = {}


def get_app_config() -> dict[str, Any]:
    """Return current app config (e.g. for DB session reference)."""
    return _app_config
