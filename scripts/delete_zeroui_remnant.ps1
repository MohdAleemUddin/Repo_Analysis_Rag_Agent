# Run this script after closing Cursor (or any app using the Zeroui path) to remove the leftover folder.
# From repo root: .\scripts\delete_zeroui_remnant.ps1
$path = Join-Path $PSScriptRoot "..\repo_analysis_rag\Zeroui_Repo_Analysis_Rag_Agent"
if (-not (Test-Path $path)) {
    Write-Host "Zeroui_Repo_Analysis_Rag_Agent already removed."
    exit 0
}
try {
    Remove-Item -Path $path -Recurse -Force
    Write-Host "Removed Zeroui_Repo_Analysis_Rag_Agent."
} catch {
    Write-Host "Could not remove (folder in use). Close Cursor, then run this script again: $($_.Exception.Message)"
    exit 1
}
