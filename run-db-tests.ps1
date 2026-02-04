# Run Confluence DB integration tests (TC-IT-002, TC-IT-008). Set CONFLUENCE_DATABASE_URL to your PostgreSQL URL.
# Prerequisite: alembic upgrade head (with same URL) so schema exists.
param(
    [string]$DbUrl = $env:CONFLUENCE_DATABASE_URL
)
if ($DbUrl) {
    $env:CONFLUENCE_DATABASE_URL = $DbUrl
    python -m pytest tests/confluence/test_db_integration.py -v --tb=short
} else {
    Write-Host "Set CONFLUENCE_DATABASE_URL or pass -DbUrl 'postgresql://user:pass@host:5432/db'"
    python -m pytest tests/confluence/test_db_integration.py -v --tb=short
}
