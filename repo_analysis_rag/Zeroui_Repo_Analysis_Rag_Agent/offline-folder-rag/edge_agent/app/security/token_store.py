import hashlib
import os
from pathlib import Path


TOKEN_FILENAME = "agent_token.txt"


def index_dir() -> Path:
    """
    Resolve the directory for the token file.

    Prefer RAG_INDEX_DIR when set; otherwise fallback to %USERPROFILE%/.offline_rag_index.
    """
    env_dir = os.environ.get("RAG_INDEX_DIR")
    if env_dir:
        return Path(env_dir)
    user_profile = os.environ.get("USERPROFILE", "")
    return Path(user_profile) / ".offline_rag_index"


def token_path() -> Path:
    return index_dir() / TOKEN_FILENAME


def get_or_create_token() -> str:
    """
    Return the existing token if present; otherwise create and persist a new one.
    """
    token_file = token_path()
    token_file.parent.mkdir(parents=True, exist_ok=True)
    if token_file.exists():
        return token_file.read_text(encoding="utf-8").strip()

    token = hashlib.sha256(os.urandom(32)).hexdigest()
    token_file.write_text(token, encoding="utf-8")
    return token
