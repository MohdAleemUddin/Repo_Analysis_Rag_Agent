# API package: Confluence and RAG route registration

from .config_routes import register_config_routes
from .confluence_routes import register_confluence_routes
from .routes import register_rag_routes

__all__ = [
    "register_config_routes",
    "register_confluence_routes",
    "register_rag_routes",
]
