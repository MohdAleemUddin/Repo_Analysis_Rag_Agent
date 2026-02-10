"""Run Confluence API server. Port from CONFLUENCE_PORT env (default 8000)."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
import uvicorn

from app.api import register_confluence_routes

router = APIRouter()
register_confluence_routes(router)
app = FastAPI()


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "confluence-edge-agent"}


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)

if __name__ == "__main__":
    port = int(os.environ.get("CONFLUENCE_PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
