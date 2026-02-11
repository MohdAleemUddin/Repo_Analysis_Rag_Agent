"""Run RAG API server. Port from RAG_PORT env (default 8001)."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from backend_rag so OPENAI_API_KEY is available before app imports
_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("RAG_PORT", "8001"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
