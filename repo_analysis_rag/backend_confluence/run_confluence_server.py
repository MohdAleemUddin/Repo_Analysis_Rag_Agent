"""Run Confluence API server on port 8000. Use from repo root or edge_agent dir."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
import uvicorn

# Run from offline-folder-rag/edge_agent so "app" is the local package
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
