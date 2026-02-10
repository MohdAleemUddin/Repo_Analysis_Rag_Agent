# Run PRD compliance tests from repo root.
# Usage: .\scripts\run_prd_compliance_tests.ps1
$repoRoot = Split-Path $PSScriptRoot -Parent
Set-Location $repoRoot
$env:PYTHONPATH = "$repoRoot;$repoRoot\repo_analysis_rag\backend_confluence;$repoRoot\repo_analysis_rag\backend_rag"
& python -m pytest tests/confluence/test_prd_compliance.py tests/confluence/test_api_prd_format.py tests/confluence/test_performance_targets.py tests/confluence/test_performance_regression.py tests/confluence/test_intelligence_learning.py -v --tb=short @args
