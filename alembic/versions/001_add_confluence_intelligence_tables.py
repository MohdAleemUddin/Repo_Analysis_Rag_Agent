"""Add Confluence intelligence tables (PRD §8.1) and seed data (§8.2).

Revision ID: 001_confluence
Revises: (none)
Create Date: Confluence 4-table extension, same PostgreSQL as RAG.

Up: runs migrations/004_confluence_tables.sql (tables + seed).
Down: drops 4 tables, then vector extension. Rollback <30s.
"""
from pathlib import Path

from alembic import op
from sqlalchemy import text

# revision identifiers
revision = "001_confluence"
down_revision = None
branch_labels = None
depends_on = None


def _repo_root() -> Path:
    """Repo root (parent of alembic/)."""
    return Path(__file__).resolve().parent.parent.parent


def _run_sql_file(connection, filename: str) -> None:
    """Execute SQL file. Splits by semicolon-newline for multi-statement."""
    path = _repo_root() / "migrations" / filename
    if not path.exists():
        return
    content = path.read_text().replace("\r\n", "\n")
    # Split into statements (semicolon followed by newline)
    raw = content.split(";\n")
    for block in raw:
        stmt = block.strip()
        # Skip empty and comment-only blocks
        if not stmt or all(l.strip().startswith("--") or not l.strip() for l in stmt.splitlines()):
            continue
        if not stmt.endswith(";"):
            stmt += ";"
        connection.execute(text(stmt))


def upgrade() -> None:
    conn = op.get_bind()
    _run_sql_file(conn, "004_confluence_tables.sql")


def downgrade() -> None:
    # Reverse dependency order; rollback <30s (PRD).
    op.execute(text("DROP TABLE IF EXISTS intelligence_learning CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS intelligent_creations CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS intelligence_examples CASCADE"))
    op.execute(text("DROP TABLE IF EXISTS intelligent_templates CASCADE"))
    op.execute(text("DROP EXTENSION IF EXISTS vector"))
