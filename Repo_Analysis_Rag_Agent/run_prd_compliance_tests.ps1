# Stub: when cwd is Repo_Analysis_Rag_Agent, .\Repo_Analysis_Rag_Agent\run_prd_compliance_tests.ps1 runs this; invoke the script one level up.
& (Join-Path (Split-Path $PSScriptRoot -Parent) "run_prd_compliance_tests.ps1") @args
