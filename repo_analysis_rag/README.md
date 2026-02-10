# Repo Analysis RAG – Project Root

This folder contains the full product: two backends and one VS Code extension.

## Run both backends (one command)

From **repo root**:

```powershell
python repo_analysis_rag/run_servers.py
```

Or from this folder (`repo_analysis_rag`):

```powershell
python run_servers.py
```

- **Confluence API:** http://localhost:8000 (analyze, create, spaces, config)
- **RAG API:** http://localhost:8001 (chat, index, search, doctor)

Press Ctrl+C to stop both.

## Run backends separately

- Confluence only: `cd repo_analysis_rag/backend_confluence && python run_server.py` (port 8000)
- RAG only: `cd repo_analysis_rag/backend_rag && python run_server.py` (port 8001)

## Extension (VS Code)

1. Open the repo as workspace in VS Code.
2. Build: `cd repo_analysis_rag/vscode-extension && npm install && npm run compile`
3. Run the extension via **Run and Debug** → **Run Offline RAG Extension**.

Configure in VS Code settings:

- **Confluence API base URL** (`confluence.apiBaseUrl`): default `http://localhost:8000`
- **RAG / Agent base URL** (`rag.agentBaseUrl`): default `http://localhost:8001`

Confluence features use the Confluence URL; RAG/chat features use the RAG URL.

## Tests and coverage

From **repo root**:

- **Local CI/CD (lint, security, tests, Docker):** `.\run-local-cicd.ps1`
- **Code coverage:** `.\scripts\run_coverage.ps1`  
  - Runs `tests/confluence/` and `tests/edge_agent/`, reports on `app`, prints term report and writes `htmlcov/`. Optionally opens `htmlcov/index.html`.
- **US-16–focused coverage:** `.\run_us16_coverage.ps1` (output in `htmlcov_us16/`).
