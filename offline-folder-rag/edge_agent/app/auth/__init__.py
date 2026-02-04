# Auth: credential store for workspace-scoped credentials (encrypted at rest per NFR3)
from app.auth.credential_store import get_workspace_credentials

__all__ = ["get_workspace_credentials"]
