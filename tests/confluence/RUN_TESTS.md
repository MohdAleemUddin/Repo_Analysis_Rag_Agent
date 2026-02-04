# Confluence tests

- **42 total** tests under `tests/confluence/`.
- **18 tests** have names containing US13 TC IDs (e.g. `TC_NEG_004`, `TC_EH_008`). The rest do not.

**Why 24 are deselected when using `-k "TC_NEG_004 or ..."`**  
The `-k` expression matches only those 18 test names. The other 24 (performance, placeholders, etc.) do not contain those strings, so pytest deselects them. This is expected when running US13-only.

**Run all 42 Confluence tests (no filter):**
```powershell
cd D:\Downloads\Confluence_Agent\Repo_Analysis_Rag_Agent
python -m pytest tests/confluence/ -v --tb=short
```

**Run only the 18 US13 error-recovery tests:**
```powershell
python -m pytest tests/confluence/ -v -k "TC_NEG_004 or TC_NEG_007 or TC_NEG_003 or TC_ST_006 or TC_DT_007 or TC_EH_008 or TC_EH_007 or TC_EH_006 or TC_EH_005 or TC_EH_009 or TC_EH_010 or TC_EH_011 or TC_EH_012 or TC_EH_001 or TC_EH_002 or TC_EH_003 or TC_SC_004 or TC_NEG_014" --tb=short
```
