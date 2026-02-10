# US-16 Smart Project Documentation - Coverage script
# Run: .\run_us16_coverage.ps1
# Uses module names (app.xxx) for --cov so coverage matches imported modules.
Set-Location $PSScriptRoot
$env:PYTHONPATH = "$PSScriptRoot;${PSScriptRoot}\repo_analysis_rag\backend_confluence;${PSScriptRoot}\repo_analysis_rag\backend_rag"
python -m pytest tests/confluence/ -v --tb=short `
  --cov=app.confluence.project_scanner `
  --cov=app.confluence.project_analyzer `
  --cov=app.confluence.project_template_matcher `
  --cov=app.mcp_server.task_queue `
  --cov=app.mcp_server.confluence_tasks `
  --cov-report=term-missing `
  --cov-report=html:htmlcov_us16 `
  --cov-fail-under=0
