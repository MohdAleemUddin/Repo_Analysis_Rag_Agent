"""Run RAG API server. Port from RAG_PORT env (default 8001)."""

import os
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("RAG_PORT", "8001"))
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )
