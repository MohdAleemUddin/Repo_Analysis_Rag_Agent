# Repository Folder Structure Cleanup – Full Plan

**Document version:** 2.5  
**Created:** 2026-02-06  
**Updated:** 2026-02-06 (v2.5 – env vars, pitfalls, optional enhancements, git mv, health check, extension config snippet, conftest target)  
**Purpose:** Single source of truth for cleaning the repo: move the entire project into `repo_analysis_rag/`, keep two separate backends (Confluence + Zeroui RAG), one shared frontend, and one command that starts both servers on two ports for clear development debugging.

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Decisions Summary (What We Agreed)](#2-decisions-summary-what-we-agreed)
3. [Current State – Full Inventory](#3-current-state--full-inventory)
4. [Target Structure (Gold Standard)](#4-target-structure-gold-standard)
5. [Runtime Model: One Launcher, Two Ports (Option B)](#5-runtime-model-one-launcher-two-ports-option-b)
6. [Implementation Phases (Step-by-Step)](#6-implementation-phases-step-by-step)
7. [Reference Update Checklist](#7-reference-update-checklist)
8. [Verification and Rollback](#8-verification-and-rollback)
9. [Commands to run servers and extension](#9-commands-to-run-servers-and-extension-after-restructuring)
10. [Critical path and behavior fixes](#10-critical-path-and-behavior-fixes-no-functionality-break)
11. [Triple Validation (strict)](#11-triple-validation-strict)
12. [Environment Variables](#12-environment-variables)
13. [Potential Pitfalls and Mitigations](#13-potential-pitfalls-and-mitigations)
14. [Optional Enhancements](#14-optional-enhancements)
15. [Appendix A – File Path Reference](#appendix-a--file-path-reference)
16. [Appendix B – CI/CD Reference](#appendix-b--cicd-reference)
17. [Appendix C – Extension Two-URL Config](#appendix-c--extension-two-url-config)
18. [Expected Repo Structure after changes](#expected-repo-structure-after-changes)
19. [Document History](#document-history)

---

## 1. Executive Summary

### 1.1 What’s Wrong Today

- **Two `offline-folder-rag` trees:** One at repo root (used by CI and root tests); one nested under `repo_analysis_rag/Zeroui_Repo_Analysis_Rag_Agent/`. Root has the full Confluence backend and an older extension; Zeroui has a RAG-only backend and the newer Chat + Confluence extension. They are out of sync.
- **Project scattered:** Backends and extension live at root and inside Zeroui; no single “project root” for the product.
- **Duplicate test locations:** Root `tests/`, root `offline-folder-rag/unittests/`, and Zeroui’s `tests/`, `testcases/`, `unittests/` create confusion.
- **Naming confusion:** `Repo_Analysis_Rag_Agent/` (root), `repo_analysis_rag/`, and `Zeroui_Repo_Analysis_Rag_Agent` are easily mixed up.

### 1.2 What We Want

- **Project inside `repo_analysis_rag/`:** The entire product (both backends + frontend) lives under `repo_analysis_rag/`. This folder becomes the canonical project root for the application.
- **Two backends, code separate:** Confluence backend and Zeroui RAG backend as **separate** codebases/folders (e.g. `backend_confluence/`, `backend_rag/`) so responsibilities are clear.
- **One frontend:** A single VS Code extension (Chat + Confluence) that talks to **both** backends via two configurable base URLs.
- **One command, two ports (Option B):** A single launcher (e.g. `run_servers.py`) starts **both** servers: Confluence on one port (e.g. 8000), RAG on another (e.g. 8001). During development this makes it easy to read each backend’s responses and logs separately—no confusion about which server has an issue when something breaks.

### 1.3 Strategy in One Sentence

Move and reorganize everything under `repo_analysis_rag/`: two separate backend folders (Confluence + RAG), one merged extension, one launcher that starts both servers on two ports; update CI, tests, and .vscode to point at `repo_analysis_rag/` paths.

---

## 2. Decisions Summary (What We Agreed)

| Topic | Decision |
|-------|----------|
| **Project location** | Bring the **entire project** inside `repo_analysis_rag/` (both backends + frontend). |
| **Backend count** | **Two** backends: one for Confluence, one for the old Zeroui RAG agent. Code is **separate** (different folders). |
| **Frontend** | **One** shared VS Code extension for both; Confluence features use Confluence backend, RAG features use RAG backend. |
| **How both backends run** | **Option B:** One launcher command starts **two servers on two ports** (e.g. Confluence 8000, RAG 8001). Reason: in development it’s easier to read each server’s responses and logs; with one port, breakage would be confusing. |
| **Extension config** | Extension needs **two base URL** settings: Confluence API base URL (e.g. `http://localhost:8000`) and RAG/agent base URL (e.g. `http://localhost:8001`). |

---

## 3. Current State – Full Inventory

### 3.1 Root-Level Directories

| Path | Purpose | Used By |
|------|---------|---------|
| `.github/workflows/ci.yml` | CI/CD pipeline | GitHub Actions |
| `.vscode/launch.json` | Debug extension | Points to **Zeroui** extension path |
| `.vscode/tasks.json` | Build task (compile-rag) | Points to **Zeroui** extension path |
| `alembic/` | DB migrations (Confluence) | Backend |
| `confluence_data/` | Confluence config, examples, templates | Backend |
| `docker/` | Dockerfiles (Confluence, MCP) | Docker build |
| `migrations/` | SQL migrations (Confluence) | Backend |
| `offline-folder-rag/` | **PRIMARY** backend + extension at root | CI, run-local-cicd, root tests |
| `repo_analysis_rag/` | Contains only `Zeroui_Repo_Analysis_Rag_Agent/` | Vendored; launch/tasks use its extension |
| `Repo_Analysis_Rag_Agent/` | Single script `run_prd_compliance_tests.ps1` | Manual runs |
| `tests/` | Confluence + edge_agent unit/integration | pytest, CI |
| `requirements.txt`, `confluence_requirements.txt` | Python deps | CI, local |
| `pytest.ini` | Pytest config | pytest |
| `run-local-cicd.ps1`, `run_confluence_tests.ps1` | Local scripts | Tests, CI |

### 3.2 Root `offline-folder-rag/` (Confluence backend + older extension)

| Path | Content | Notes |
|------|---------|------|
| `edge_agent/` | Full **Confluence** backend (RAG + Confluence) | agents, api/confluence_routes, config, confluence/, mcp_server, etc. |
| `edge_agent/run_confluence_server.py` | Confluence server entrypoint | Single server today |
| `vscode-extension/` | Confluence-focused extension | Older; no ChatPanelViewProvider, no commandRouter, no services/ |
| `scripts/` | Confluence scripts | backup, log_cleanup, seed, setup_confluence |
| `unittests/` | Confluence unittests | Overlaps with root tests/ |
| `requirements.txt` | Dependencies | Used by CI |

### 3.3 Zeroui `repo_analysis_rag/Zeroui_Repo_Analysis_Rag_Agent/offline-folder-rag/` (RAG backend + full extension)

| Path | Content | Notes |
|------|---------|------|
| `edge_agent/` | **RAG-only** backend | indexing, retrieval, tools, api/routes.py; no Confluence routes |
| `vscode-extension/` | **Full** Chat + Confluence extension | webview/ChatPanelViewProvider, confluenceHtml, commandRouter, services/, fetchSpaces |
| `tests/`, `testcases/`, `unittests/` | RAG + extension tests | Not in root CI |

### 3.4 Extension Comparison (Root vs Zeroui)

| Feature | Root extension | Zeroui extension |
|---------|----------------|------------------|
| Chat panel (webview) | No | Yes (ChatPanelViewProvider, chatPanelHtml, confluenceHtml) |
| fetchSpaces (live spaces) | No | Yes |
| commands/commandRouter, services/ | No | Yes |
| **Use for merged frontend** | No | **Yes** – this is the one to keep as the single frontend |

---

## 4. Target Structure (Gold Standard)

All product code lives under **`repo_analysis_rag/`**. Repo root keeps only CI, global tests, and shared infra (or tests can move under repo_analysis_rag as needed).

### 4.1 Target Layout Under `repo_analysis_rag/`

```
repo_analysis_rag1/
├── .github/                    # CI stays at repo root (paths updated to repo_analysis_rag/...)
├── .vscode/                    # launch/tasks point to repo_analysis_rag/.../vscode-extension
├── alembic/                     # Can stay at root or move under repo_analysis_rag (Confluence)
├── confluence_data/             # Can stay at root or move under repo_analysis_rag (Confluence)
├── migrations/                  # Same
├── repo_analysis_rag/          ← PROJECT ROOT (everything below is the product)
│   ├── backend_confluence/     ← Confluence backend (from root offline-folder-rag/edge_agent)
│   │   ├── app/
│   │   │   ├── agents/
│   │   │   ├── api/            # confluence_routes, config_routes
│   │   │   ├── confluence/
│   │   │   ├── mcp_server/
│   │   │   └── ...
│   │   ├── run_server.py       # Starts Confluence API on port 8000 (or configurable)
│   │   └── requirements.txt
│   ├── backend_rag/            ← Zeroui RAG backend (from Zeroui offline-folder-rag/edge_agent)
│   │   ├── app/
│   │   │   ├── api/            # routes.py (RAG endpoints)
│   │   │   ├── indexing/
│   │   │   ├── retrieval/
│   │   │   ├── tools/
│   │   │   └── ...
│   │   ├── run_server.py       # Starts RAG API on port 8001 (or configurable)
│   │   └── requirements.txt
│   ├── run_servers.py          ← ONE COMMAND: starts both backend_confluence + backend_rag (two ports)
│   ├── vscode-extension/       ← Single frontend (merged from Zeroui; Chat + Confluence)
│   │   ├── src/
│   │   ├── package.json
│   │   └── ...
│   ├── confluence_data/        # Optional: copy or symlink if kept at repo root
│   ├── scripts/                # Confluence + any shared scripts
│   ├── tests/                  # Unified tests (confluence + rag + extension)
│   └── README.md               # Project readme: how to run run_servers.py, two URLs for extension
├── tests/                      # Or move under repo_analysis_rag/tests (see Phase 2)
├── requirements.txt
├── confluence_requirements.txt
└── pytest.ini
```

### 4.2 Naming Conventions

- **backend_confluence:** Confluence API server (intelligent create, spaces, config, PRD, etc.). Port **8000** (default).
- **backend_rag:** Zeroui RAG agent (search, index, ask, doctor, etc.). Port **8001** (default).
- **vscode-extension:** One extension; uses Confluence base URL for Confluence features and RAG base URL for RAG features.
- **run_servers.py:** Single entrypoint at `repo_analysis_rag/run_servers.py` that starts both servers (e.g. subprocess or two threads).

### 4.3 What Stays at Repo Root (Optional)

- `.github/`, `.vscode/` (with paths updated to `repo_analysis_rag/...`).
- `alembic/`, `confluence_data/`, `migrations/` can stay at root and be referenced by `backend_confluence` via env or config; or move under `repo_analysis_rag/` for a fully self-contained project.
- Root `tests/` can stay at root and reference `repo_analysis_rag/backend_confluence` and `repo_analysis_rag/backend_rag` in conftest/paths; or tests can move under `repo_analysis_rag/tests/`.

---

## 5. Runtime Model: One Launcher, Two Ports (Option B)

### 5.1 Why Two Ports

- **Development clarity:** When something breaks, you see which server’s logs and responses (Confluence vs RAG). With one port and combined routes, it’s harder to tell which backend failed.
- **Simple separation:** Each backend is a separate process; no need to merge route trees or share a single app.

### 5.2 Launcher Behavior

- **Command:** e.g. `python repo_analysis_rag/run_servers.py` (from repo root) or `python run_servers.py` (from repo_analysis_rag/).
- **Behavior:**
  1. Start Confluence server (backend_confluence) on port **8000** (or from env/config).
  2. Start RAG server (backend_rag) on port **8001** (or from env/config).
  3. Print to console something like:  
     `Confluence: http://localhost:8000`  
     `RAG:       http://localhost:8001`  
     `Press Ctrl+C to stop both.`
- **Implementation options:** (a) Launcher spawns two subprocesses (e.g. `subprocess.Popen` for each server’s run_server.py), or (b) launcher runs two threads each starting a server. Subprocesses give separate stdout/stderr per backend.

### 5.3 Extension Configuration (Two Base URLs)

The VS Code extension must have **two** configurable base URLs (or base URL + second URL, or two settings):

| Setting (example names) | Purpose | Default (dev) |
|-------------------------|---------|----------------|
| **Confluence API base URL** (e.g. `confluence.apiBaseUrl`) | Confluence endpoints (analyze, create, spaces, config) | `http://localhost:8000` |
| **RAG / Agent base URL** (e.g. `rag.agentBaseUrl` or existing agent URL) | RAG endpoints (search, index, ask, health) | `http://localhost:8001` |

- Confluence API calls (fetchSpaces, intelligent-analyze, intelligent-create, test-connection, etc.) → Confluence base URL.
- RAG/agent calls (chat, index, search, doctor) → RAG base URL.
- Extension reads both from workspace settings or a single config object with two URLs.

### 5.4 Launcher: health check before ready (recommended)

- Before printing "Press Ctrl+C to stop both", the launcher can **wait for both backends to be ready** by polling `/health` on each port (e.g. every 1s, timeout 30s). This makes it clear when both servers are up.
- Example behavior: start both subprocesses, then in a loop request `http://localhost:8000/health` and `http://localhost:8001/health` until both return 200 or timeout; then print the URLs and "Press Ctrl+C to stop both."

---

## 6. Implementation Phases (Step-by-Step)

### Phase 1 – Create Structure Under repo_analysis_rag and Move Backends

**Goal:** Create `repo_analysis_rag/backend_confluence/`, `repo_analysis_rag/backend_rag/`, and populate them from current code; no deletion of root/Zeroui yet (backup in place).

#### Step 1.1 – Backup and branch

- Create branch `cleanup/repo-structure-v2`.
- Zip or tag: root `offline-folder-rag/`, `repo_analysis_rag/Zeroui_Repo_Analysis_Rag_Agent/offline-folder-rag/`.
- **Git history:** Prefer **`git mv`** where you move a single tree (e.g. root `offline-folder-rag/edge_agent` → `repo_analysis_rag/backend_confluence`) so history is preserved. See Section 14.2 (Optional Enhancements) for details.

#### Step 1.2 – Create backend_confluence

- Create folder `repo_analysis_rag/backend_confluence/`.
- **Option A (recommended for history):** `git mv offline-folder-rag/edge_agent repo_analysis_rag/backend_confluence` (from repo root). Then add/rename `run_server.py` and `requirements.txt` in place.
- **Option B:** Copy **root** `offline-folder-rag/edge_agent/` contents into `repo_analysis_rag/backend_confluence/` (so you have `backend_confluence/app/`, etc.).
- Add or rename entrypoint: `backend_confluence/run_server.py` that starts the Confluence app on port **8000** (read from env `CONFLUENCE_PORT` or default 8000). Reuse existing run_confluence_server.py logic.
- Add `backend_confluence/requirements.txt` (from root offline-folder-rag/requirements.txt + confluence deps as needed).

#### Step 1.3 – Create backend_rag

- Create folder `repo_analysis_rag/backend_rag/`.
- **Option A (history):** `git mv repo_analysis_rag/Zeroui_Repo_Analysis_Rag_Agent/offline-folder-rag/edge_agent repo_analysis_rag/backend_rag` (from repo root). Then add `run_server.py` and ensure `requirements.txt` is in place.
- **Option B:** Copy **Zeroui** `repo_analysis_rag/Zeroui_Repo_Analysis_Rag_Agent/offline-folder-rag/edge_agent/` contents into `repo_analysis_rag/backend_rag/` (so you have `backend_rag/app/` with api, indexing, retrieval, tools, etc.).
- Add `backend_rag/run_server.py` that starts the RAG app on port **8001** (env `RAG_PORT` or default 8001) if not using Option A.
- Add or keep `backend_rag/requirements.txt`.

#### Step 1.4 – Create run_servers.py launcher

- Create `repo_analysis_rag/run_servers.py` at repo_analysis_rag root.
- Script should:
  - Start Confluence server (subprocess or thread) on port 8000 (or from env).
  - Start RAG server (subprocess or thread) on port 8001 (or from env).
  - **Optional but recommended:** Poll `http://localhost:8000/health` and `http://localhost:8001/health` until both return 200 (timeout e.g. 30s), then print "ready."
  - Print both URLs; wait for Ctrl+C and then terminate both.
- Document in script or README: run from repo root with `python repo_analysis_rag/run_servers.py` or from repo_analysis_rag with `python run_servers.py`.

#### Step 1.5 – Confluence data and migrations

- Either keep `confluence_data/` and `migrations/` at repo root and set env or config in backend_confluence to point at them (e.g. `CONFLUENCE_DATA_DIR=../../confluence_data`), or copy/move them under `repo_analysis_rag/` (e.g. `repo_analysis_rag/confluence_data/`) and point backend_confluence there. Same for alembic if used by Confluence.

---

### Phase 2 – Unify Frontend and Put Under repo_analysis_rag

**Goal:** One extension under `repo_analysis_rag/vscode-extension/` (Zeroui’s full version), with two base URL settings.

#### Step 2.1 – Create repo_analysis_rag/vscode-extension from Zeroui

- Copy entire **Zeroui** `repo_analysis_rag/Zeroui_Repo_Analysis_Rag_Agent/offline-folder-rag/vscode-extension/` to `repo_analysis_rag/vscode-extension/` (overwrite or create). This is the single frontend (Chat + Confluence, fetchSpaces, commandRouter, services).

#### Step 2.2 – Align package.json and tsconfig

- Ensure `package.json` and `tsconfig.json` produce a single `main` entry (e.g. `./out/extension.js` or `./out/src/extension.js`). Fix paths so `npm run compile` / `npm run build` works from `repo_analysis_rag/vscode-extension/`.

#### Step 2.3 – Add two base URL settings to extension

- In extension settings (package.json `contributes.configuration`), add or document:
  - **Confluence API base URL** (e.g. `confluence.apiBaseUrl`) – default `http://localhost:8000`.
  - **RAG / Agent base URL** (e.g. `rag.agentBaseUrl` or existing key) – default `http://localhost:8001`.
- In code: Confluence API client uses Confluence base URL; RAG/agent client uses RAG base URL. Update any single-URL assumptions to use the correct setting per feature.

---

### Phase 3 – Point All References to repo_analysis_rag

**Goal:** CI, tests, .vscode, and scripts use paths under `repo_analysis_rag/`.

#### Step 3.1 – .vscode

- **launch.json:** `extensionDevelopmentPath` → `${workspaceFolder}/repo_analysis_rag/vscode-extension`.
- **tasks.json:** compile-rag task `cwd` → `${workspaceFolder}/repo_analysis_rag/vscode-extension`.
- **outFiles** in launch.json → path under `repo_analysis_rag/vscode-extension/out/`.

#### Step 3.2 – tests/conftest.py and test paths

- conftest.py: Add to `sys.path` the Confluence app path, e.g. `root / "repo_analysis_rag" / "backend_confluence"` (so `from app.xxx` works for Confluence tests). For RAG-only tests, add `repo_analysis_rag/backend_rag` if needed.
- All tests under `tests/confluence/` that currently use `offline-folder-rag/edge_agent`: change to `repo_analysis_rag/backend_confluence`.
- All tests under `tests/edge_agent/` that target Confluence backend: same. If any tests target RAG backend only, point them at `repo_analysis_rag/backend_rag`.
- `tests/confluence/pyrightconfig.json` and `tests/pyrightconfig.json`: update `extraPaths` to `repo_analysis_rag/backend_confluence` (and optionally backend_rag).

#### Step 3.3 – CI (ci.yml)

- Replace every `offline-folder-rag` path with `repo_analysis_rag/backend_confluence` or `repo_analysis_rag/backend_rag` as appropriate (e.g. lint both backends, install both requirements).
- TypeScript/extension: `working-directory: repo_analysis_rag/vscode-extension`.
- PYTHONPATH: include `repo_analysis_rag/backend_confluence` (and `repo_analysis_rag/backend_rag` if tests need it).
- Cache key: include `repo_analysis_rag/backend_confluence/requirements.txt`, `repo_analysis_rag/backend_rag/requirements.txt` if you use separate requirement files.

#### Step 3.4 – run-local-cicd.ps1 and other scripts

- Update paths from `offline-folder-rag/edge_agent` to `repo_analysis_rag/backend_confluence` (and add backend_rag where relevant).
- run_confluence_tests.ps1: ensure pytest discovers tests and backend path is correct (conftest or env).

#### Step 3.5 – test_ui_compliance.py

- If it references extension path, change to `repo_analysis_rag/vscode-extension/src/extension.ts` (or equivalent).

---

### Phase 4 – Clean Up and Optional Removal of Old Trees

**Goal:** Remove duplication; single source of truth under repo_analysis_rag.

#### Step 4.1 – Remove or archive root offline-folder-rag

- After CI and manual verification pass with new paths, delete or archive root `offline-folder-rag/` (or keep as _archive/offline-folder-rag-root).

#### Step 4.2 – Remove or archive Zeroui offline-folder-rag

- Delete or archive `repo_analysis_rag/Zeroui_Repo_Analysis_Rag_Agent/offline-folder-rag/`. If you keep `Zeroui_Repo_Analysis_Rag_Agent/` for other reasons, leave a README there: "Product code moved to repo_analysis_rag/ (backend_confluence, backend_rag, vscode-extension)."

#### Step 4.3 – Repo_Analysis_Rag_Agent (root)

- Move `Repo_Analysis_Rag_Agent/run_prd_compliance_tests.ps1` to `scripts/run_prd_compliance_tests.ps1` at repo root (or under repo_analysis_rag/scripts). Delete the empty folder.

#### Step 4.4 – Test folders

- Keep a single test suite: either root `tests/` (pointing at repo_analysis_rag backends) or move tests under `repo_analysis_rag/tests/` and update pytest.ini `testpaths`. Remove or archive root `offline-folder-rag/unittests/` and Zeroui test folders once migrated.

---

## 7. Reference Update Checklist

| Item | Current | After plan |
|------|---------|------------|
| `.vscode/launch.json` extensionDevelopmentPath | Zeroui path | `repo_analysis_rag/vscode-extension` |
| `.vscode/tasks.json` compile-rag cwd | Zeroui path | `repo_analysis_rag/vscode-extension` |
| `tests/conftest.py` | root/offline-folder-rag/edge_agent | root/repo_analysis_rag/backend_confluence (and backend_rag if needed) |
| `tests/confluence/*.py` path inserts | offline-folder-rag/edge_agent | repo_analysis_rag/backend_confluence |
| `tests/edge_agent/*.py` path inserts | offline-folder-rag/edge_agent | repo_analysis_rag/backend_confluence or backend_rag as appropriate |
| `tests/confluence/pyrightconfig.json` extraPaths | ../../offline-folder-rag/edge_agent | ../../repo_analysis_rag/backend_confluence |
| `tests/pyrightconfig.json` extraPaths | ../offline-folder-rag/edge_agent | ../repo_analysis_rag/backend_confluence |
| `.github/workflows/ci.yml` – pip, black, ruff, paths | offline-folder-rag/ | repo_analysis_rag/backend_confluence/, repo_analysis_rag/backend_rag/ |
| `.github/workflows/ci.yml` – TypeScript | offline-folder-rag/vscode-extension | repo_analysis_rag/vscode-extension |
| `.github/workflows/ci.yml` – PYTHONPATH | offline-folder-rag | repo_analysis_rag/backend_confluence, repo_analysis_rag/backend_rag |
| `run-local-cicd.ps1` | offline-folder-rag/edge_agent, repo_analysis_rag/ | repo_analysis_rag/backend_confluence, repo_analysis_rag/backend_rag |
| Extension settings | Single apiBaseUrl (or similar) | Two: Confluence API base URL (8000), RAG base URL (8001) |
| Server start | run_confluence_server.py only | run_servers.py (starts both on 8000 and 8001) |

**Target state for tests/conftest.py** (path inserts so `from app...` works for both backends):

```python
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
backend_confluence = root / "repo_analysis_rag" / "backend_confluence"
backend_rag = root / "repo_analysis_rag" / "backend_rag"
for path in (backend_confluence, backend_rag):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))
# ... error_log_config import and pytest hooks unchanged ...
```

---

## 8. Verification and Rollback

### 8.1 Verification After Full Migration

- [ ] `python repo_analysis_rag/run_servers.py` starts both servers; console shows Confluence on 8000 and RAG on 8001.
- [ ] Confluence endpoints respond on port 8000 (e.g. health, /confluence/config/spaces).
- [ ] RAG endpoints respond on port 8001 (e.g. health, search/index if applicable).
- [ ] Extension launches from VS Code (launch config points to repo_analysis_rag/vscode-extension).
- [ ] Extension Confluence features use port 8000 (e.g. fetchSpaces, create page).
- [ ] Extension RAG features use port 8001 (chat, index, etc.).
- [ ] `pytest tests/confluence/ tests/edge_agent/` passes (paths point at repo_analysis_rag backends).
- [ ] CI workflow passes with updated paths.

### 8.2 Rollback

- Restore from backup branch or zips of root `offline-folder-rag/` and Zeroui `offline-folder-rag/`.
- Revert .vscode, tests/conftest, tests/*/pyrightconfig, ci.yml, run-local-cicd.ps1 to original paths.
- Re-run tests and CI to confirm previous state.

---

## 9. Commands to run servers and extension (after restructuring)

All commands assume repo root is the current directory (e.g. `d:\repo_analysis_rag1_final\repo_analysis_rag1` or `repo_analysis_rag1`).

### 9.1 Start both backends (one command)

From **repo root**:

```powershell
# Windows PowerShell
python repo_analysis_rag/run_servers.py
```

Or from **repo_analysis_rag**:

```powershell
cd repo_analysis_rag
python run_servers.py
```

Expected console output (or similar):

- `Confluence: http://localhost:8000`
- `RAG:       http://localhost:8001`
- `Press Ctrl+C to stop both.`

Then:

- Confluence API: http://localhost:8000 (e.g. http://localhost:8000/health, http://localhost:8000/confluence/config/spaces).
- RAG API: http://localhost:8001 (e.g. http://localhost:8001/health, http://localhost:8001/index_report).

### 9.2 Start only Confluence backend

The Confluence app is built in **run_server.py** (from the original run_confluence_server.py); there is no `app.main:app`. Use **only** the script below.

From repo root:

```powershell
cd repo_analysis_rag/backend_confluence
python run_server.py
```

Do **not** use `uvicorn app.main:app` for Confluence—the FastAPI app is created inside run_server.py, not in app.main.

### 9.3 Start only RAG backend

From repo root:

```powershell
cd repo_analysis_rag/backend_rag
python run_server.py
```

Or (with working directory `repo_analysis_rag/backend_rag`):

```powershell
cd repo_analysis_rag/backend_rag
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

### 9.4 Build and run the VS Code extension

From repo root:

```powershell
# Install dependencies (first time)
cd repo_analysis_rag/vscode-extension
npm install

# Build (compile TypeScript)
npm run compile
# or
npm run build
```

Then in VS Code:

1. Open the repo as workspace (root = repo_analysis_rag1).
2. Ensure `.vscode/launch.json` has `extensionDevelopmentPath` pointing to `repo_analysis_rag/vscode-extension`.
3. Run **Run and Debug** → **Run Offline RAG Extension** (or the configured launch task).

Extension will use:

- **Confluence API base URL** (e.g. `confluence.apiBaseUrl` or `apiBaseUrl`): default `http://localhost:8000`.
- **RAG / Agent base URL** (e.g. `rag.agentBaseUrl`): default `http://localhost:8001`.

### 9.5 Full dev workflow (servers + extension)

1. Terminal 1 (from repo root): `python repo_analysis_rag/run_servers.py`
2. Terminal 2 (optional): `cd repo_analysis_rag/vscode-extension && npm run compile`
3. In VS Code: F5 or **Run Offline RAG Extension**
4. Use the extension (Confluence and RAG features); Confluence hits 8000, RAG hits 8001.

---

## 10. Critical path and behavior fixes (no functionality break)

Apply these so that no file is missed and no functionality breaks after the move.

### 10.1 backend_confluence: repo root for confluence_data

- **Files:** `app/confluence/export_import.py`, `app/confluence/example_manager.py`, `app/confluence/project_template_matcher.py` resolve `confluence_data` relative to "repo root".
- **export_import.py and example_manager.py:** They use `_EDGE_AGENT_ROOT` (dir containing `app`) and `_REPO_ROOT = _EDGE_AGENT_ROOT + "../.."`. After moving to `backend_confluence`, `_EDGE_AGENT_ROOT` becomes `backend_confluence`, so `_REPO_ROOT` is still repo root. **No change.**
- **project_template_matcher.py:** It uses `edge_root = Path(__file__).resolve().parents[2]` and `repo_root = edge_root.parents[1]`. After move, `edge_root` = `backend_confluence`, so `parents[1]` = `repo_analysis_rag`, which is wrong. **Change to:** `repo_root = edge_root.parents[2]` so `repo_root` is repo root and `repo_root / "confluence_data" / "examples"` is correct when `confluence_data` stays at repo root.

### 10.2 backend_rag: create run_server.py

- Zeroui `edge_agent` has no server entrypoint; it only has `app/main.py` with `create_app()` and `app = create_app()`.
- **Add** `repo_analysis_rag/backend_rag/run_server.py` that:
  - Runs with cwd = `backend_rag` (or sets sys.path so `app` is importable).
  - Starts uvicorn: e.g. `uvicorn app.main:app --host 0.0.0.0 --port 8001` (port from env `RAG_PORT` if desired).
- So `backend_rag/run_server.py` is **created**, not copied.

### 10.3 run_servers.py working directory

- When launching Confluence and RAG as subprocesses, set **cwd** (or equivalent) so each backend sees its own `app`:
  - Confluence: cwd = `repo_analysis_rag/backend_confluence`.
  - RAG: cwd = `repo_analysis_rag/backend_rag`.
- Otherwise imports like `from app.main import app` or `app.main:app` will fail.

### 10.4 error_log_config.py at repo root

- **tests/conftest.py** does `from error_log_config import setup_error_log, append_error_line, ERROR_LOG_PATH`.
- **error_log_config.py** must remain at **repo root** (same level as `tests/`) so that when pytest runs from repo root, the import works. Do **not** move it under `repo_analysis_rag/`. Add it to the "Expected Repo Structure" tree at root.

### 10.5 Extension: two base URLs

- Confluence endpoints already use a base URL (e.g. `apiBaseUrl`, default 8000). Keep that for Confluence.
- RAG/agent endpoints (index_report, index, health, etc.) must use a **second** base URL defaulting to **8001** (e.g. `rag.agentBaseUrl` or existing agent URL). Update extension code so that:
  - Confluence API client uses Confluence base URL (8000).
  - RAG/agent client (e.g. agentClient, ChatPanelViewProvider) uses RAG base URL (8001), not the same as Confluence.
- Document the two settings in extension README or package.json `contributes.configuration`.

---

## 11. Triple Validation (strict)

This section records the strict triple validation of the plan: (1) every file in the right place in the expected tree, (2) no broken behavior or missing references, and (3) CI/config and critical paths explicitly covered. Use it during implementation to ensure nothing is missed.

### 11.1 Root-level files: coverage vs expected tree

| Current root file/folder | In expected tree? | Action / note |
|--------------------------|-------------------|----------------|
| `.github/` | Yes | Paths in ci.yml updated per Appendix B. |
| `.vscode/` | Yes | launch.json, tasks.json, settings.json. |
| `.cursor/`, `.specstory/` | Yes | Listed. |
| `.gitignore`, `.cursorindexingignore` | Yes | |
| `.coveragerc`, `.coveragerc.prd` | Yes (see notes) | Keep at root; used by coverage. Listed in "Root files to keep" below. |
| `alembic/`, `alembic.ini` | Yes | |
| `confluence_data/`, `docker/`, `migrations/` | Yes | Full subtrees. |
| `repo_analysis_rag/`, `tests/` | Yes | |
| `pyrightconfig.json`, `pytest.ini` | Yes | |
| `requirements.txt`, `confluence_requirements.txt` | Yes | |
| `docker-compose.yml`, `docker-compose.test.yml` | Yes | |
| `REPO_STRUCTURE_PLAN.md` | Yes | |
| `run_confluence_tests.ps1`, `run-db-tests.ps1`, `run_us16_coverage.ps1` | Yes | |
| **run-local-cicd.ps1** | Yes | **Exact name:** `run-local-cicd.ps1` (hyphen, not underscore). |
| `error_log_config.py`, `venv/` | Yes | error_log_config required by tests/conftest.py. |
| **scripts/** | Yes | Contains `run_prd_compliance_tests.ps1` (moved from Repo_Analysis_Rag_Agent). |
| **CURRENT_REPO_TREE.md**, **REPO_SNAPSHOT.md** | Optional | Keep at root as optional docs or remove; document decision. |
| **resolve_log_conflict.py** | Optional | Keep at root or remove; document decision. |
| **errors.log** | Generated | At root; often gitignored. Remains at root (generated by tests). |
| **Repo_Analysis_Rag_Agent/** | Removed | Script moved to `scripts/`; folder deleted. |

### 11.2 repo_analysis_rag/ contents: current vs after plan

| Item | In plan? | Note |
|------|----------|------|
| `backend_confluence/`, `backend_rag/`, `run_servers.py` | Yes | Created/copied per Phases 1–2. |
| `vscode-extension/`, `scripts/`, `README.md` | Yes | Extension from Zeroui; scripts from root offline-folder-rag. |
| **.cursorindexingignore** (under repo_analysis_rag) | Optional | When creating repo_analysis_rag from Zeroui: keep or drop; document. |
| **README_SUBMODULE.md** | Replace | Remove or replace by new `README.md`. |
| **functionality_break.log** | Optional | Keep or remove; document. |
| **Zeroui_Repo_Analysis_Rag_Agent/** | Removed | Replaced by backend_rag + vscode-extension; folder removed or reduced to README. |

### 11.3 Backend entrypoints

- **backend_confluence:** App is built in **run_server.py** (from run_confluence_server.py). There is no `app.main:app`. Use **only** `python run_server.py` to start Confluence (Section 9.2).
- **backend_rag:** Has `app/main.py` with `create_app()`. Start with `python run_server.py` or `uvicorn app.main:app --port 8001`.

### 11.4 Tests and paths

- **conftest.py:** Switch path from `offline-folder-rag/edge_agent` to `repo_analysis_rag/backend_confluence` (and `backend_rag` if needed).
- **tests/confluence/** and **tests/edge_agent/:** All references to `offline-folder-rag/edge_agent` → `repo_analysis_rag/backend_confluence` (or backend_rag where appropriate).
- **pyrightconfig.json** (tests/ and tests/confluence/): Update extraPaths per Section 7.

### 11.5 CI (ci.yml) – exact edits

See **Appendix B** for the exact cache key, pip install commands, lint/type-check paths, PYTHONPATH, and extension working-directory. Every occurrence of `offline-folder-rag` in ci.yml must be replaced with the appropriate `repo_analysis_rag/backend_confluence` or `repo_analysis_rag/backend_rag` (or `repo_analysis_rag/vscode-extension` for the extension job).

### 11.6 Critical path checklist

| Check | Status |
|-------|--------|
| Every root file/folder in expected tree or explicitly decided | Done (see 11.1 and notes below tree). |
| Correct root script name: run-**local**-cicd.ps1 (hyphen) | Done. |
| repo_analysis_rag extras (.cursorindexingignore, README_SUBMODULE, functionality_break.log) | Documented in 11.2. |
| Confluence entrypoint: use only run_server.py (no uvicorn app.main:app) | Done (Section 9.2). |
| CI exact cache key and path list | Done (Appendix B). |
| backend_confluence / backend_rag file sets | In expected tree. |
| run_servers.py and both run_server.py | In plan. |
| error_log_config at root; project_template_matcher repo_root fix | In Section 10. |
| Extension two URLs; Zeroui as single frontend | In plan. |

### 11.7 Current path → After path (key files)

| Current path | After path |
|--------------|------------|
| `offline-folder-rag/edge_agent/` | `repo_analysis_rag/backend_confluence/` |
| `offline-folder-rag/edge_agent/run_confluence_server.py` | `repo_analysis_rag/backend_confluence/run_server.py` (rename/copy) |
| `repo_analysis_rag/Zeroui_.../offline-folder-rag/edge_agent/` | `repo_analysis_rag/backend_rag/` |
| `repo_analysis_rag/Zeroui_.../offline-folder-rag/vscode-extension/` | `repo_analysis_rag/vscode-extension/` (copy as single frontend) |
| `tests/conftest.py` path insert | `root / "repo_analysis_rag" / "backend_confluence"` (and backend_rag if needed) |
| `.github/workflows/ci.yml` all offline-folder-rag refs | `repo_analysis_rag/backend_confluence`, `repo_analysis_rag/backend_rag`, `repo_analysis_rag/vscode-extension` |
| `.vscode/launch.json` extensionDevelopmentPath | `repo_analysis_rag/vscode-extension` |
| `Repo_Analysis_Rag_Agent/run_prd_compliance_tests.ps1` | `scripts/run_prd_compliance_tests.ps1` |
| `error_log_config.py` | Stays at repo root (do not move). |
| `app/confluence/project_template_matcher.py` repo_root | `repo_root = edge_root.parents[2]` |

### 11.8 Strict triple validation report (file-level)

This subsection is the **strict** pass: every current file/location is accounted for and each required code change is listed so nothing is missed during implementation.

#### 11.8.1 Root and infra

| Location | Status | Note |
|----------|--------|------|
| **alembic.ini** | In tree at root | Present in repo; keep. |
| **.specstory/** | Tree shows `history/` only | Current repo also has `.specstory/.gitignore`; preserved (optional to list in tree). |
| **confluence_data/** | Full subtree in tree | config/, examples/ (4 files + successful_creations/example_001.json), templates/ (all JSON including project_templates/). Matches current repo. |
| **migrations/** | 002–007 in tree | Matches current. |
| **tests/confluence/data/** | Tree shows api/, baselines/, content/ | Exact files preserved: api/ (6 JSON), baselines/ (2 JSON), content/ (multiple .md, .txt). No file listed by name in tree; subdirs only—keep all existing files when restructuring. |

#### 11.8.2 Test files that must be updated (path or import)

Every file below references `offline-folder-rag/edge_agent` or `offline-folder-rag/vscode-extension`. Each must be updated per Section 7 (and 11.4) so paths point at `repo_analysis_rag/backend_confluence` or `repo_analysis_rag/backend_rag` or `repo_analysis_rag/vscode-extension`.

| File | What to change |
|------|----------------|
| **tests/conftest.py** | `root / "offline-folder-rag" / "edge_agent"` → `root / "repo_analysis_rag" / "backend_confluence"` (and add backend_rag to path if RAG tests need it). |
| **tests/confluence/test_config_settings_cov.py** | sys.path insert: `offline-folder-rag/edge_agent` → `repo_analysis_rag/backend_confluence`. |
| **tests/confluence/test_ui_compliance.py** | **Extension path:** `offline-folder-rag/vscode-extension/src/extension.ts` → `repo_analysis_rag/vscode-extension/src/extension.ts`. |
| **tests/confluence/test_performance_targets.py** | Imports and sys.path: `offline_folder_rag.edge_agent` / `offline-folder-rag/edge_agent` → `repo_analysis_rag/backend_confluence`. |
| **tests/confluence/test_prd_monitor_cov.py** | sys.path: `offline-folder-rag/edge_agent` → `repo_analysis_rag/backend_confluence`. |
| **tests/confluence/test_performance_regression.py** | Imports and sys.path: same as above. |
| **tests/test_mcp_server.py** | `_root / "offline-folder-rag" / "edge_agent"` → `_root / "repo_analysis_rag" / "backend_confluence"`. |
| **tests/confluence/test_project_pipeline.py** | All sys.path inserts: `offline-folder-rag/edge_agent` → `repo_analysis_rag/backend_confluence`. |
| **tests/confluence/test_db_integration.py** | Imports and sys.path: same. |
| **tests/confluence/test_api_prd_format.py** | Imports and sys.path: same. |
| **tests/confluence/test_prd_compliance.py** | Imports and sys.path: same. |
| **tests/confluence/test_intelligence_learning.py** | Imports and sys.path: same. |
| **tests/confluence/test_optimizer_cov.py** | sys.path: same. |
| **tests/confluence/test_export_import.py** | sys.path: same. |
| **tests/confluence/test_example_manager_cov.py** | sys.path: same. |
| **tests/confluence/test_db_adapter_full_cov.py** | sys.path: same. |
| **tests/confluence/test_data_validation.py** | Imports and sys.path: same. |
| **tests/confluence/test_confluence_routes_cov.py** | sys.path: same. |
| **tests/confluence/test_config_and_status_cov.py** | sys.path: same. |
| **tests/confluence/test_client_cov.py** | sys.path: same. |
| **tests/confluence/test_schemas.py** | sys.path: same. |
| **tests/confluence/test_routes_export_import_cov.py** | sys.path: same. |
| **tests/confluence/test_e2e_workflows.py** | Imports and sys.path: same. |
| **tests/confluence/test_db_adapter_cov.py** | sys.path: same. |
| **tests/edge_agent/unit/test_coordinator.py** | sys.path: `parents[3] / "offline-folder-rag" / "edge_agent"` → `parents[3] / "repo_analysis_rag" / "backend_confluence"`. |
| **tests/edge_agent/unit/test_credential_store.py** | Same. |
| **tests/edge_agent/unit/test_mcp_server_init.py** | Same. |
| **tests/edge_agent/unit/test_pattern_matching_agent.py** | Same. |
| **tests/edge_agent/unit/test_learning_agent.py** | Same. |
| **tests/edge_agent/unit/test_integration_agent.py** | Same. |
| **tests/edge_agent/unit/test_formatting_agent.py** | Same. |
| **tests/edge_agent/unit/test_content_analysis_agent.py** | Same. |

**Import form:** Some tests use `from offline_folder_rag.edge_agent.app...`. After the move there is no `offline_folder_rag` package. They must either (a) use sys.path to `repo_analysis_rag/backend_confluence` and `from app....` only, or (b) add a path so `repo_analysis_rag.backend_confluence.app` is importable and change to `from repo_analysis_rag.backend_confluence.app...`. Recommended: (a)—keep `from app.xxx` and set sys.path to `repo_analysis_rag/backend_confluence` (as conftest will do).

#### 11.8.3 Backend_confluence (source: root offline-folder-rag/edge_agent)

| Current path | In expected tree? |
|--------------|-------------------|
| edge_agent/__init__.py | backend_confluence/__init__.py |
| edge_agent/app/ (agents, api, auth, config, confluence, indexing, langchain, logging, main.py, mcp_server, retrieval, security, tools) | backend_confluence/app/ with same structure; every file listed in expected tree. |
| edge_agent/run_confluence_server.py | backend_confluence/run_server.py (rename/copy) |
| offline-folder-rag/requirements.txt | backend_confluence/requirements.txt |

All listed in plan tree; no file missing.

#### 11.8.4 Backend_rag (source: Zeroui offline-folder-rag/edge_agent)

| Current path | In expected tree? |
|--------------|-------------------|
| Zeroui edge_agent/app/ (api, config, indexing, retrieval, logging, main, security, tools) | backend_rag/app/ with same structure; every file listed. |
| (no run_server) | backend_rag/run_server.py **created** (Section 10.2). |
| Zeroui requirements.txt | backend_rag/requirements.txt |

All listed; run_server.py is new.

#### 11.8.5 Zeroui-only items (removed; not in expected tree)

| Item | Disposition |
|------|-------------|
| Zeroui **scripts/checkModule.js** | Removed with Zeroui tree. |
| Zeroui **temp_b.js**, **temp_long.js**, **temp.java** | Removed. |
| Zeroui **testcases/** | Removed. |
| Zeroui **unittests/** | Removed. |
| Zeroui **tests/** (edge_agent, indexGate.test.ts, vscode_extension) | Removed. **Optional:** migrate RAG unit/integration tests to root `tests/edge_agent/` or `tests/rag/` before deletion if you want them in CI. |
| Zeroui **package-lock.json**, **pytest.ini**, **requirements.txt** (at Zeroui_Repo_Analysis_Rag_Agent/) | Removed; backend_rag has its own requirements.txt. |

#### 11.8.6 Root offline-folder-rag (removed)

| Item | Disposition |
|------|-------------|
| **unittests/** | Removed (plan: archive or remove; root tests/ is canonical). |
| **vscode-extension/** (root) | Replaced by Zeroui copy at repo_analysis_rag/vscode-extension; root extension not kept. |
| **EXTENSION_TESTING.md** (root extension) | Not in expected tree; discarded when using Zeroui extension. |

#### 11.8.7 Final checklist (nothing missed)

| Check | Done |
|-------|------|
| Every root file/folder in tree or explicitly decided | Yes (11.1, tree, notes). |
| tests/conftest.py and all test files with path/import in 11.8.2 updated | Yes—table lists every file. |
| test_ui_compliance.py extension path → repo_analysis_rag/vscode-extension | Yes—called out in 11.8.2. |
| backend_confluence and backend_rag file sets match sources | Yes (11.8.3, 11.8.4). |
| Zeroui-only and root offline-folder-rag disposition clear | Yes (11.8.5, 11.8.6). |
| tests/confluence/data/ exact files preserved | Note in 11.8.1. |
| .specstory/.gitignore | Optional; preserved. |

---

## 12. Environment Variables

Use a consistent set of environment variables for ports and paths so backends and the launcher behave correctly in dev and CI.

| Variable | Purpose | Default (dev) |
|----------|---------|----------------|
| **CONFLUENCE_PORT** | Port for Confluence backend | `8000` |
| **RAG_PORT** | Port for RAG backend | `8001` |
| **CONFLUENCE_API_URL** | Full Confluence API base URL (extension or clients) | `http://localhost:8000` |
| **RAG_API_URL** | Full RAG/agent API base URL | `http://localhost:8001` |
| **CONFLUENCE_DATA_DIR** | Path to `confluence_data` (relative to repo root or absolute) | e.g. `../../confluence_data` when run from `backend_confluence` with data at root |

- Backends: read port from env in `run_server.py` (e.g. `int(os.environ.get("CONFLUENCE_PORT", "8000"))`).
- Launcher: pass or set env so each subprocess uses the correct port.
- Extension: defaults in package.json match above; users can override in VS Code settings.

---

## 13. Potential Pitfalls and Mitigations

| Pitfall | Mitigation |
|---------|------------|
| **Path resolution in backends** | Section 10.1: `project_template_matcher.py` must use `repo_root = edge_root.parents[2]` after move. Test thoroughly that `confluence_data` is found at repo root. |
| **Extension hardcoded ports or single backend** | Extension must use two configurable base URLs (Appendix C). No hardcoded port or assumption of one backend. |
| **Database / SQLite relative paths** | If backends use SQLite or DB paths relative to cwd, ensure `run_server.py` and launcher set cwd to the backend directory (Section 10.3). Verify DB paths after move. |
| **CI cache invalidation** | New cache key (Appendix B.1) will invalidate old cache on first run; CI may be slower once. Acceptable; optional: use a key that includes both old and new paths temporarily, then remove old paths. |
| **VS Code workspace** | If developers open only one backend, add a `.code-workspace` file (optional, Section 14) for multi-root workspace. |

---

## 14. Optional Enhancements

These are **not required** for the restructure but make the plan more complete and the repo easier to use.

### 14.1 Docker Compose for both backends (dev)

If you want to run both backends in containers during development:

```yaml
# docker-compose.dev.yml (optional, at repo root or under repo_analysis_rag)
services:
  confluence_backend:
    build: ./repo_analysis_rag/backend_confluence
    ports: ["8000:8000"]
    environment:
      - CONFLUENCE_PORT=8000
      - CONFLUENCE_DATA_DIR=/app/confluence_data
    volumes:
      - ./confluence_data:/app/confluence_data  # if data at root

  rag_backend:
    build: ./repo_analysis_rag/backend_rag
    ports: ["8001:8001"]
    environment:
      - RAG_PORT=8001
```

Add Dockerfiles under each backend if not present; document in README.

### 14.2 Git history preservation

- Prefer **`git mv`** when moving a single tree (Phase 1 Steps 1.2 and 1.3). Example: `git mv offline-folder-rag/edge_agent repo_analysis_rag/backend_confluence` from repo root. Then add or rename `run_server.py` in place.
- For Zeroui: `git mv repo_analysis_rag/Zeroui_Repo_Analysis_Rag_Agent/offline-folder-rag/edge_agent repo_analysis_rag/backend_rag`. History for the moved files is preserved.

### 14.3 Dependency conflicts (requirements-base.txt)

- If `backend_confluence` and `backend_rag` share many dependencies and you hit version conflicts, consider a **shared** `repo_analysis_rag/requirements-base.txt` and have each backend’s `requirements.txt` include it (e.g. `-r ../requirements-base.txt` or a path under repo_analysis_rag). Only do this if needed; otherwise two separate requirement files are simpler.

### 14.4 Development convenience scripts

- **dev-start.ps1** (optional): Start launcher and optionally VS Code, e.g. `Start-Process python -ArgumentList "repo_analysis_rag/run_servers.py"` and `Start-Process code -ArgumentList "."`. Document in README.

### 14.5 VS Code multi-root workspace

- Add **`.code-workspace`** at repo root if developers often work on backends or extension independently, e.g. roots for `repo_analysis_rag/backend_confluence`, `repo_analysis_rag/backend_rag`, `repo_analysis_rag/vscode-extension`. Optional.

---

## Appendix A – File Path Reference

### A.1 Target Layout (After Plan)

```
repo_analysis_rag1/
├── .github/workflows/ci.yml          # Paths → repo_analysis_rag/...
├── .vscode/launch.json               # → repo_analysis_rag/vscode-extension
├── .vscode/tasks.json                # → repo_analysis_rag/vscode-extension
├── alembic/
├── confluence_data/
├── migrations/
├── repo_analysis_rag/
│   ├── backend_confluence/
│   │   ├── app/
│   │   ├── run_server.py             # Port 8000
│   │   └── requirements.txt
│   ├── backend_rag/
│   │   ├── app/
│   │   ├── run_server.py             # Port 8001
│   │   └── requirements.txt
│   ├── run_servers.py                # Starts both
│   ├── vscode-extension/
│   ├── scripts/
│   └── tests/                        # Optional: move root tests here
├── tests/                            # Or keep at root
├── requirements.txt
├── confluence_requirements.txt
├── pytest.ini
└── scripts/
```

---

## Appendix B – CI/CD Reference

Use these exact values when updating `.github/workflows/ci.yml`. Replace **every** occurrence of `offline-folder-rag` with the appropriate path below.

### B.1 Cache key (pip)

**Current (example):**
```yaml
key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt', 'confluence_requirements.txt', 'offline-folder-rag/requirements.txt') }}
```

**After plan:**
```yaml
key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt', 'confluence_requirements.txt', 'repo_analysis_rag/backend_confluence/requirements.txt', 'repo_analysis_rag/backend_rag/requirements.txt') }}
```

### B.2 Pip install

- `pip install -r requirements.txt`
- `pip install -r confluence_requirements.txt || true`
- `pip install -r repo_analysis_rag/backend_confluence/requirements.txt || true`
- `pip install -r repo_analysis_rag/backend_rag/requirements.txt || true`

(Apply in each job that currently installs from `offline-folder-rag/requirements.txt`.)

### B.3 Lint and type-check paths

| Tool | Paths to use (replace offline-folder-rag) |
|------|------------------------------------------|
| **black** | `repo_analysis_rag/backend_confluence/`, `repo_analysis_rag/backend_rag/`, `repo_analysis_rag/`, `tests/` |
| **ruff** | Same as black |
| **mypy** | `repo_analysis_rag`, `repo_analysis_rag/backend_confluence`, `repo_analysis_rag/backend_rag` (or as needed) |
| **pylint** | Same dirs; PYTHONPATH must include both backends (see B.4). |
| **flake8** | `repo_analysis_rag/backend_confluence/`, `repo_analysis_rag/backend_rag/`, `repo_analysis_rag/`, `tests/` |
| **bandit** | `repo_analysis_rag/backend_confluence/`, `repo_analysis_rag/backend_rag/`, `repo_analysis_rag/` (exclude tests if desired) |

### B.4 PYTHONPATH (test and lint jobs)

**Current (example):** `${{ github.workspace }}:${{ github.workspace }}/offline-folder-rag/edge_agent`

**After plan:**  
`${{ github.workspace }}:${{ github.workspace }}/repo_analysis_rag/backend_confluence:${{ github.workspace }}/repo_analysis_rag/backend_rag`

So `from app...` resolves for both backends when running tests or lint.

### B.5 TypeScript / extension job

- **working-directory:** `repo_analysis_rag/vscode-extension`
- Steps: `npm install`, `npm run build` (or `npm run compile` as in package.json).

### B.6 Unit / PRD tests

- pytest with `tests/confluence/`, `tests/edge_agent/` (or equivalent).
- conftest and path inserts must use `repo_analysis_rag/backend_confluence` (and `repo_analysis_rag/backend_rag` if needed).
- PYTHONPATH as in B.4.

---

## Appendix C – Extension Two-URL Config

- **Confluence API base URL:** Used for all Confluence endpoints (analyze, create, spaces, test-connection, config). Default `http://localhost:8000`.
- **RAG / Agent base URL:** Used for RAG/chat/index/doctor endpoints. Default `http://localhost:8001`.
- Implementation: two workspace settings; extension code passes the correct base URL to each client (Confluence API client vs RAG/agent client).

**Extension package.json – add to `contributes.configuration`** (for migration and clarity):

```json
"contributes": {
  "configuration": {
    "confluence.apiBaseUrl": {
      "type": "string",
      "default": "http://localhost:8000",
      "description": "Confluence API base URL (analyze, create, spaces, config)"
    },
    "rag.agentBaseUrl": {
      "type": "string",
      "default": "http://localhost:8001",
      "description": "RAG / Agent API base URL (chat, index, search, doctor)"
    }
  }
}
```

Ensure extension code reads these settings and uses `confluence.apiBaseUrl` for Confluence API calls and `rag.agentBaseUrl` for RAG/agent calls. Document in extension README how to migrate existing single-URL settings to the two URLs.

---

## Expected Repo Structure after changes

Below is the full expected repository tree after the plan is applied. The product lives under `repo_analysis_rag/` with two backends and one frontend; root keeps CI, shared config, tests, and infra. Old trees (`offline-folder-rag/`, `Zeroui_Repo_Analysis_Rag_Agent/offline-folder-rag/`, `Repo_Analysis_Rag_Agent/`) are removed or replaced.

```
repo_analysis_rag1/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .vscode/
│   ├── launch.json
│   ├── settings.json
│   └── tasks.json
├── .cursor/
├── .specstory/
│   └── history/
├── .gitignore
├── .cursorindexingignore
├── alembic/
│   ├── env.py
│   └── versions/
│       ├── 001_add_confluence_intelligence_tables.py
│       └── README.md
├── alembic.ini
├── confluence_data/
│   ├── config/
│   │   ├── default_config.json
│   │   ├── rate_limits.json
│   │   └── spaces_config.json
│   ├── examples/
│   │   ├── export_format.json
│   │   ├── learned_examples.json
│   │   ├── project_examples.json
│   │   └── successful_creations/
│   │       └── example_001.json
│   └── templates/
│       ├── config_template.json
│       ├── database_template.json
│       ├── library_template.json
│       ├── mixed_content_template.json
│       ├── mixed_project_template.json
│       ├── project_templates/
│       │   ├── database_template.json
│       │   ├── java_spring_template.json
│       │   ├── library_template.json
│       │   ├── python_django_template.json
│       │   ├── python_fastapi_template.json
│       │   ├── react_webapp_template.json
│       │   └── testing_template.json
│       ├── python_api_template.json
│       ├── single_type_template.json
│       ├── testing_template.json
│       └── web_app_template.json
├── docker/
│   ├── Dockerfile.confluence
│   └── Dockerfile.mcp
├── migrations/
│   ├── 002_confluence_tables.sql
│   ├── 003_intelligence_extension.sql
│   ├── 004_confluence_tables.sql
│   ├── 005_project_type.sql
│   ├── 006_confluence_config.sql
│   └── 007_space_key.sql
├── repo_analysis_rag/
│   ├── backend_confluence/
│   │   ├── __init__.py
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── agents/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── content_analysis_agent.py
│   │   │   │   ├── contracts.py
│   │   │   │   ├── coordinator.py
│   │   │   │   ├── formatting_agent.py
│   │   │   │   ├── integration_agent.py
│   │   │   │   ├── learning_agent.py
│   │   │   │   └── pattern_matching_agent.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config_routes.py
│   │   │   │   ├── confluence_routes.py
│   │   │   │   ├── routes.py
│   │   │   │   └── schemas.py
│   │   │   ├── auth/
│   │   │   │   ├── __init__.py
│   │   │   │   └── credential_store.py
│   │   │   ├── config/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── config.py
│   │   │   │   ├── confluence_config.py
│   │   │   │   ├── confluence_schema.py
│   │   │   │   └── defaults.py
│   │   │   ├── confluence/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── client.py
│   │   │   │   ├── context_analyzer.py
│   │   │   │   ├── db_adapter.py
│   │   │   │   ├── error_handler.py
│   │   │   │   ├── example_manager.py
│   │   │   │   ├── export_import.py
│   │   │   │   ├── formatter.py
│   │   │   │   ├── optimizer.py
│   │   │   │   ├── page_tracker.py
│   │   │   │   ├── prd_monitor.py
│   │   │   │   ├── project_analyzer.py
│   │   │   │   ├── project_scanner.py
│   │   │   │   ├── project_template_matcher.py
│   │   │   │   ├── space_manager.py
│   │   │   │   ├── state_machine.py
│   │   │   │   ├── status_manager.py
│   │   │   │   ├── templates.py
│   │   │   │   ├── utils.py
│   │   │   │   ├── validation.py
│   │   │   │   └── verification.py
│   │   │   ├── indexing/
│   │   │   │   └── README.md
│   │   │   ├── langchain/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chains/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── analysis_chain.py
│   │   │   │   │   ├── formatting_chain.py
│   │   │   │   │   └── matching_chain.py
│   │   │   │   ├── tools/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   └── confluence_tools.py
│   │   │   │   └── vector_stores.py
│   │   │   ├── logging/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── confluence_logger.py
│   │   │   │   └── logger.py
│   │   │   ├── main.py
│   │   │   ├── mcp_server/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── confluence_tasks.py
│   │   │   │   ├── health_monitor.py
│   │   │   │   ├── orchestrator.py
│   │   │   │   ├── state_tracker.py
│   │   │   │   └── task_queue.py
│   │   │   ├── retrieval/
│   │   │   │   └── README.md
│   │   │   ├── security/
│   │   │   │   └── README.md
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── doctor.py
│   │   │       └── search.py
│   │   ├── run_server.py
│   │   └── requirements.txt
│   ├── backend_rag/
│   │   ├── __init__.py
│   │   ├── app/
│   │   │   ├── __init__.py
│   │   │   ├── api/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── routes.py
│   │   │   │   └── schemas.py
│   │   │   ├── config/
│   │   │   │   ├── __init__.py
│   │   │   │   └── defaults.py
│   │   │   ├── indexing/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── chunking/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── chunker.py
│   │   │   │   │   ├── code_chunker.py
│   │   │   │   │   ├── line_chunker.py
│   │   │   │   │   └── markdown_chunker.py
│   │   │   │   ├── config_store.py
│   │   │   │   ├── index_dir.py
│   │   │   │   ├── indexer.py
│   │   │   │   ├── manifest_store.py
│   │   │   │   └── scan_rules.py
│   │   │   ├── logging/
│   │   │   │   └── logger.py
│   │   │   ├── main.py
│   │   │   ├── retrieval/
│   │   │   │   ├── __init__.py
│   │   │   │   └── ask.py
│   │   │   ├── security/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── token_guard.py
│   │   │   │   └── token_store.py
│   │   │   └── tools/
│   │   │       ├── __init__.py
│   │   │       ├── doctor.py
│   │   │       └── search.py
│   │   ├── run_server.py
│   │   └── requirements.txt
│   ├── run_servers.py
│   ├── vscode-extension/
│   │   ├── src/
│   │   │   ├── commands/
│   │   │   │   ├── commandRouter.ts
│   │   │   │   └── slashCommands.ts
│   │   │   ├── confluence/
│   │   │   │   ├── badges/
│   │   │   │   │   ├── ai-formatted-badge.ts
│   │   │   │   │   ├── confidence-color.ts
│   │   │   │   │   ├── index.ts
│   │   │   │   │   └── learning-indicator.ts
│   │   │   │   ├── commands.ts
│   │   │   │   ├── confluence-api.ts
│   │   │   │   ├── confluence-settings.ts
│   │   │   │   ├── ConfluenceAnalytics.tsx
│   │   │   │   ├── ConfluenceButton.tsx
│   │   │   │   ├── ConfluenceContextMenu.tsx
│   │   │   │   ├── ConfluenceFeedback.tsx
│   │   │   │   ├── ConfluenceFileSelector.tsx
│   │   │   │   ├── ConfluenceProgress.tsx
│   │   │   │   ├── ConfluenceResults.tsx
│   │   │   │   ├── confluenceSpacePreferences.ts
│   │   │   │   ├── context-menu.ts
│   │   │   │   ├── error-messages.tsx
│   │   │   │   ├── intelligence-dashboard.tsx
│   │   │   │   ├── intelligence-indicators.tsx
│   │   │   │   ├── intelligent-decisions.tsx
│   │   │   │   ├── onboarding.tsx
│   │   │   │   ├── simple-language.json
│   │   │   │   └── types.ts
│   │   │   ├── extension.ts
│   │   │   ├── services/
│   │   │   │   ├── agentClient.ts
│   │   │   │   ├── autoIndexScheduler.ts
│   │   │   │   ├── indexGate.ts
│   │   │   │   ├── indexingState.ts
│   │   │   │   └── storage.ts
│   │   │   ├── utils/
│   │   │   │   └── pathNormalize.ts
│   │   │   └── webview/
│   │   │       ├── ChatPanelViewProvider.ts
│   │   │       └── ui/
│   │   │           ├── chatPanelHtml.ts
│   │   │           └── confluenceHtml.ts
│   │   ├── out/
│   │   ├── package.json
│   │   ├── package-lock.json
│   │   └── tsconfig.json
│   ├── scripts/
│   │   ├── backup_confluence_data.py
│   │   ├── log_cleanup.py
│   │   ├── seed_confluence_intelligence.py
│   │   └── setup_confluence.py
│   └── README.md
├── tests/
│   ├── conftest.py
│   ├── pyrightconfig.json
│   ├── confluence/
│   │   ├── __init__.py
│   │   ├── data/
│   │   │   ├── api/
│   │   │   ├── baselines/
│   │   │   └── content/
│   │   ├── pyrightconfig.json
│   │   ├── RUN_TESTS.md
│   │   ├── test_api_prd_format.py
│   │   ├── test_api_router.py
│   │   ├── test_business_rules.py
│   │   ├── test_client_auth.py
│   │   ├── test_client_cov.py
│   │   ├── test_config_and_status_cov.py
│   │   ├── test_config_settings_cov.py
│   │   ├── test_config.py
│   │   ├── test_confluence_routes_cov.py
│   │   ├── test_data_validation.py
│   │   ├── test_db_adapter_cov.py
│   │   ├── test_db_adapter_full_cov.py
│   │   ├── test_db_integration.py
│   │   ├── test_e2e_workflows.py
│   │   ├── test_error_recovery.py
│   │   ├── test_example_manager_cov.py
│   │   ├── test_export_import.py
│   │   ├── test_imports.py
│   │   ├── test_intelligence_learning.py
│   │   ├── test_logger.py
│   │   ├── test_optimizer_cov.py
│   │   ├── test_page_tracker.py
│   │   ├── test_performance_regression.py
│   │   ├── test_performance_targets.py
│   │   ├── test_prd_compliance.py
│   │   ├── test_prd_monitor_cov.py
│   │   ├── test_project_pipeline.py
│   │   ├── test_reliability.py
│   │   ├── test_routes_export_import_cov.py
│   │   ├── test_schemas.py
│   │   ├── test_security_compliance.py
│   │   ├── test_state_machine.py
│   │   ├── test_templates.py
│   │   └── test_ui_compliance.py
│   ├── edge_agent/
│   │   ├── integration/
│   │   │   └── README.md
│   │   └── unit/
│   │       ├── README.md
│   │       ├── test_content_analysis_agent.py
│   │       ├── test_coordinator.py
│   │       ├── test_credential_store.py
│   │       ├── test_formatting_agent.py
│   │       ├── test_integration_agent.py
│   │       ├── test_learning_agent.py
│   │       ├── test_mcp_server_init.py
│   │       └── test_pattern_matching_agent.py
│   └── test_mcp_server.py
├── scripts/
│   └── run_prd_compliance_tests.ps1
├── pyrightconfig.json
├── pytest.ini
├── requirements.txt
├── confluence_requirements.txt
├── docker-compose.yml
├── docker-compose.test.yml
├── REPO_STRUCTURE_PLAN.md
├── run_confluence_tests.ps1
├── run-local-cicd.ps1          # hyphen, not underscore
├── run_us16_coverage.ps1
├── run-db-tests.ps1
├── error_log_config.py
├── .coveragerc                 # coverage config; keep at root
├── .coveragerc.prd             # PRD coverage config; keep at root
├── errors.log                  # (generated by tests; often gitignored)
├── CURRENT_REPO_TREE.md        # optional; keep or remove
├── REPO_SNAPSHOT.md            # optional; keep or remove
├── resolve_log_conflict.py     # optional; keep or remove
└── venv/
```

**Notes on this tree:**

- **Removed:** `offline-folder-rag/` (root), `repo_analysis_rag/Zeroui_Repo_Analysis_Rag_Agent/` (or reduced to a README), `Repo_Analysis_Rag_Agent/` (script moved to `scripts/`).
- **repo_analysis_rag/** is the product root: `backend_confluence` (port 8000), `backend_rag` (port 8001), `run_servers.py` (starts both), `vscode-extension` (single frontend), `scripts/`, `README.md`. When creating repo_analysis_rag: decide on `.cursorindexingignore`, `README_SUBMODULE.md`, and `functionality_break.log` (keep or remove).
- **Root** keeps: CI (`.github`), workspace (`.vscode`), Confluence data and DB (`confluence_data/`, `alembic/`, `migrations/`), `docker/`, shared **tests/** (pointing at `repo_analysis_rag/backend_confluence` and `backend_rag`), root requirements and pytest config, **scripts/** (including `run_prd_compliance_tests.ps1`), **error_log_config.py** (required by tests/conftest.py; do not move), **.coveragerc** and **.coveragerc.prd** (coverage). Optional at root: CURRENT_REPO_TREE.md, REPO_SNAPSHOT.md, resolve_log_conflict.py. **errors.log** is generated at root by tests.
- **vscode-extension** may also contain optional files: `.gitignore`, `.cursorindexingignore`, `tests/` (e.g. mockVscode.js, setup-vscode.js), `CONFLUENCE_PATH1_IMPLEMENTATION_CHECKLIST.md`.
- **.specstory/** may contain a `.gitignore` in addition to `history/`; preserved at root.

---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-02-06 | Initial plan: single backend at root, merge extension. |
| 2.0 | 2026-02-06 | Project under repo_analysis_rag; two backends (Confluence + RAG) separate; one frontend; Option B (one launcher, two ports); extension two base URLs; full phase and checklist updates. |
| 2.1 | 2026-02-06 | Added "Expected Repo Structure after changes" with full repo tree snapshot. |
| 2.2 | 2026-02-06 | Triple validation; added Commands to run servers and extension (Section 9); Critical path and behavior fixes (Section 10); error_log_config in tree and notes; project_template_matcher repo_root fix. |
| 2.3 | 2026-02-06 | Section 11 Triple Validation (strict): root files table, repo_analysis_rag extras, backend entrypoints, tests/paths, CI exact edits reference, critical path checklist, Current→After path table. Fixed Section 9.2 (Confluence: use only run_server.py, no uvicorn app.main:app). Expected tree: run-local-cicd.ps1 (hyphen), .coveragerc, .coveragerc.prd, optional root files, vscode-extension optional files note. Appendix B expanded with exact cache key (B.1), pip install (B.2), lint paths (B.3), PYTHONPATH (B.4), extension working-directory (B.5), pytest (B.6). |
| 2.4 | 2026-02-06 | Strict triple validation (11.8): file-level report—root/alembic/.specstory/confluence_data/migrations/tests/data (11.8.1); full list of test files requiring path/import updates with exact change (11.8.2); backend_confluence and backend_rag source vs tree (11.8.3–11.8.4); Zeroui-only and root offline-folder-rag disposition (11.8.5–11.8.6); final checklist (11.8.7). Note on .specstory/.gitignore and tests/confluence/data exact files preserved. |
| 2.5 | 2026-02-06 | Validator feedback integrated: Section 5.4 launcher health check; Phase 1 git mv options (1.1–1.3) and health check in 1.4; Section 7 conftest target snippet; Section 12 Environment Variables; Section 13 Potential Pitfalls and Mitigations; Section 14 Optional Enhancements (Docker Compose, git history, requirements-base.txt, dev scripts, .code-workspace); Appendix C extension package.json contributes.configuration snippet. TOC renumbered. |
