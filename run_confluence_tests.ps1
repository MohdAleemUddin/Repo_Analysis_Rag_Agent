# Run all 42 Confluence tests (no -k filter; nothing deselected).
# Usage: .\run_confluence_tests.ps1
# For US13-only (18 tests): .\run_confluence_tests.ps1 -US13Only
param([switch]$US13Only)
Set-Location $PSScriptRoot
if ($US13Only) {
    python -m pytest tests/confluence/ -v -k "TC_NEG_004 or TC_NEG_007 or TC_NEG_003 or TC_ST_006 or TC_DT_007 or TC_EH_008 or TC_EH_007 or TC_EH_006 or TC_EH_005 or TC_EH_009 or TC_EH_010 or TC_EH_011 or TC_EH_012 or TC_EH_001 or TC_EH_002 or TC_EH_003 or TC_SC_004 or TC_NEG_014" --tb=short
} else {
    python -m pytest tests/confluence/ -v --tb=short
}
