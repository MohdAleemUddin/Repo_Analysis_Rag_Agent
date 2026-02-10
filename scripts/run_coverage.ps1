# Code coverage for Confluence + RAG backends and tests
# Run from repo root: .\scripts\run_coverage.ps1
# Opens htmlcov/index.html when done (or htmlcov_us16 for US-16 focused).
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $repoRoot

$env:PYTHONPATH = "$repoRoot;$repoRoot\repo_analysis_rag\backend_confluence;$repoRoot\repo_analysis_rag\backend_rag"

# Full coverage: tests/confluence + tests/edge_agent, report on app (both backends)
python -m pytest tests/confluence/ tests/edge_agent/ `
  -v --tb=short `
  --cov=app `
  --cov-report=term-missing `
  --cov-report=html:htmlcov `
  --cov-fail-under=0

if ($LASTEXITCODE -eq 0) {
    Write-Host "`nCoverage report: htmlcov/index.html"
    if (Test-Path "htmlcov\index.html") {
        Start-Process "htmlcov\index.html"
    }
}

exit $LASTEXITCODE
