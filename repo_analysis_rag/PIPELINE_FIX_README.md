# Chat → RAG pipeline fix (diagnostics)

## What was changed

1. **Extension (`agentClient.ts`)**
   - **RAG base URL:** `getRagBaseUrl()` now uses the **rag.agentBaseUrl** setting (default `http://localhost:8001`). Configure in VS Code: Settings → search "rag.agentBaseUrl".
   - **Request log:** Before every RAG request, the extension logs to the **Debug Console**: `[RAG] Request: METHOD URL token_present=true|false`. No body or token value is logged.

2. **RAG backend (`routes.py`)**
   - **POST /ask log:** At the start of the handler, the server logs: `POST /ask received query_len=N root_path=set|none`. So you can see if the request reached the server.

## How to diagnose "messages don't reach the server"

1. **Start RAG backend** (port 8001) and **run the extension** (Run and Debug → Run Offline RAG Extension).

2. **Extension side:** Open **Debug Console** (View → Debug Console). Send a message in the chat panel. You should see a line like:
   ```text
   [RAG] Request: POST http://localhost:8001/ask token_present=true
   ```
   - If **token_present=false**: create or copy the token. RAG writes it at first run to `%USERPROFILE%\.offline_rag_index\agent_token.txt`. Ensure the extension runs in an environment that can read that path.
   - If the URL is wrong (e.g. port 8000): set **rag.agentBaseUrl** in settings to `http://localhost:8001` (or your RAG URL).

3. **Server side:** Watch the terminal where the RAG backend is running. After sending a chat message you should see:
   ```text
   POST /ask received query_len=... root_path=set
   ```
   - If this **never appears**: the request is not reaching the server (wrong URL, RAG not running, or network/firewall).
   - If it appears but you get **401**: token mismatch. Ensure the extension is using the same token file the RAG server read at startup.

4. **Quick checks**
   - RAG health: open `http://localhost:8001/health` in a browser → 200.
   - Token file exists: `%USERPROFILE%\.offline_rag_index\agent_token.txt` (run RAG at least once so it creates the token).

## Next step

Once you see both the `[RAG] Request:` log in the Debug Console and the `POST /ask received` log on the server, and you get an answer in the chat, the pipeline is fixed. Then proceed with the plan (intent helpers, summary flow, save to Confluence).
