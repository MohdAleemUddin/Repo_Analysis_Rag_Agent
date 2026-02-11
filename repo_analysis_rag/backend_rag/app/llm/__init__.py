"""LLM integration for RAG answer generation."""

from .openai_client import generate_answer_if_configured

__all__ = ["generate_answer_if_configured"]
