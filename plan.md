# Implementation Plan: Chat-to-Confluence (Final)

## 1. Overview and goals

**Keep:** Existing "Save to Confluence" flow (browse files → select → Let AI decide → Create perfect page).

**Add:** Chat-driven flow:

1. User asks in chat: *"Analyze this codebase and give its summary."*
2. System uses the **current opened folder** (workspace where the extension runs), ensures it is **indexed**, uses **RAG** (vector DB + chunks + embeddings + LLM) to produce a **codebase summary**, and shows the summary **in the chat**.
3. User replies: *"Save this summary in a Confluence page"* (or similar).
4. System creates a **Confluence page** with that summary (no file picker).

**Requirements:** LLM ✅, Indexing ✅, Embeddings ✅, Vector DB ✅, Analyze any folder ✅, Chunks ✅ (all via existing RAG + small extension changes).

---

## 2. Current state (what already exists)

| Component | Location | What it does |
|-----------|----------|--------------|
| **RAG indexing** | `backend_rag`: `scan_rules`, `indexer`, `chunking` | Scans folder, chunks files, stores in ChromaDB per `repo_id`. |
| **RAG /ask** | `backend_rag/app/api/routes.py`, `retrieval/ask.py`, `llm/openai_client.py` | Vector search + optional ripgrep + OpenAI; accepts `root_path`. |
| **Confluence create** | `backend_confluence`: `intelligent-create` | Accepts `content`/`body_content` or `files`; format → create page. |
| **Chat UI** | `ChatPanelViewProvider.ts`, `chatPanelHtml.ts` | Single panel; user types → `dispatch` → RAG or slash. |
| **Chat → RAG** | `buildExtraContext()` → `askWithOverride(text, "rag", extraContext)` | Sends `root_path: getEffectiveRootPath()` to `/ask`. |
| **Index gate** | `indexGate.ts`, slash `/ask` / `/overview` / `/search` | For gated commands, checks index exists; can show "index first" modal. |
| **Confluence create from UI** | `handleConfluenceCreate()` | Uses `confluenceState.fileContents` (from file picker); calls `intelligentCreate` with `files`. |

**Gaps to implement:**

1. Ensure index before "analyze/summary" (trigger index or show index modal), then call RAG with a summary-style query.
2. (Optional) Summary-optimized backend path: dedicated prompt or `POST /summarize`.
3. Store last RAG summary as **plain text** for "save to Confluence."
4. Detect **"save summary to Confluence"** in chat and run Confluence create instead of RAG.
5. Create Confluence page from last summary via `intelligent-create` with `content` only.
6. **Intent order:** In the same handler, check **Save intent first**, then **Summary intent**, then default RAG.
7. **Cleanup:** Clear `lastRagSummaryPlainText` on successful Confluence save and when the user sends a new non–save message (so "last summary" is never stale).
8. **Errors:** Use existing `commandResult` pattern (and Confluence error HTML where appropriate) for failed Confluence create in chat.

---

## 3. Step-by-step implementation

### Phase A: Backend (RAG)

**A1. Index and /ask already support "any folder"**  
No change. Use `root_path` = workspace path for index and ask.

**A2. (Optional) Dedicated "codebase summary" behavior**  
- **Option A:** Use `/ask` only with a fixed summary prompt and `root_path` (recommended first).  
- **Option B:** Add `POST /summarize` with a summary-specific system prompt and higher `top_k` if you want a dedicated contract.

---

### Phase B: Extension – index guarantee and summary in chat

**B1. Ensure workspace is indexed before summary**

- When the message will be handled as "codebase summary" (see B2):
  - Resolve folder: `getEffectiveRootPath()`.
  - If no folder: show "Open a folder first."
  - If folder exists: use `checkIndexExists` (from `indexGate.ts`).
  - If no index: show existing index modal or auto-trigger `handleIndexAndReport('full')` and wait until indexing completes, then proceed.
- Reuse `handleIndexAndReport` and health polling.

**B2. Intent detection order (single place in `dispatch` handler)**

- In the **same** `dispatch` handler, evaluate intents in this order (no double RAG call, no conflict):
  1. **Save-to-Confluence intent** (see C1) → if matched, run `handleSaveLastSummaryToConfluence()` and **return** (do not call RAG).
  2. **Codebase-summary intent** (see below) → if matched, ensure index (B1), send summary query to RAG, store plain-text answer (B3), render reply, **return**.
  3. **Default** → existing RAG/slash/auto behavior as today.

- **Summary intent:** Normalize message (lowercase, trim); match phrases such as "analyze this codebase", "codebase summary", "summarize this project", "project summary", "give me a summary of this code", "what is this project about". If matched:
  - Ensure index (B1).
  - Build summary query (e.g. fixed prompt from A2) and call `askWithOverride(summaryQuery, "rag", buildExtraContext())`.
  - On success, set `lastRagSummaryPlainText = result.answer` (B3) and render answer + citations as today.

**B3. Store last RAG summary (plain text)**

- Add `lastRagSummaryPlainText: string | undefined` (or equivalent) on `ChatPanelViewProvider`.
- When a RAG response is treated as a "summary" (response to summary intent in B2), set `lastRagSummaryPlainText = result.answer`.
- **Cleanup (stale prevention):**
  - **Clear on successful Confluence save:** In `handleSaveLastSummaryToConfluence()`, after Confluence create succeeds, set `lastRagSummaryPlainText = undefined`.
  - **Clear on new non–save user message:** When the user sends a message that is **not** "save to Confluence" intent (i.e. we are about to run RAG or another command), clear `lastRagSummaryPlainText` so that the next time we set it (after a new summary response), it is always the most recent summary. Optionally you can clear only when the new message is a "summary" intent (then set again after the new summary); either way, avoid reusing an old summary for "save."

---

### Phase C: Extension – "save this summary to Confluence"

**C1. Detect "save to Confluence" intent (checked first in handler)**

- In the same `dispatch` handler, **before** checking summary intent or calling RAG, check if the message is "save summary to Confluence."
- Heuristic: phrases like "save this to Confluence", "save this summary in a Confluence page", "create a Confluence page with this", "put this in Confluence", "publish this to Confluence."
- If matched:
  - If `lastRagSummaryPlainText` is missing: reply in chat with a `commandResult`: "No summary to save. Ask for a codebase summary first (e.g. 'Analyze this codebase and give its summary'), then say 'Save this summary to Confluence'."
  - If present: call `handleSaveLastSummaryToConfluence()` and **return** (do not call RAG).

**C2. Create Confluence page from summary text**

- Implement `handleSaveLastSummaryToConfluence()`:
  - Get Confluence config; if no auth, show same "configure Confluence" error as elsewhere (use existing error HTML / `commandResult`).
  - Title: e.g. `"Codebase Summary – " + (workspace folder name or "Workspace")`.
  - Space: `getSpacePreference(this.getEffectiveRootPath())` or `getPreferredSpace(config.baseUrl, this.getEffectiveRootPath())`.
  - Call `intelligentCreate(config, { content: lastRagSummaryPlainText, ... })` with no `files` (or empty), plus `intelligent_mode`, `auto_title: false`, `space`, `intelligence_context`, `base_url`, `auth`.
  - **On success:** Show success in chat (e.g. `commandResult` with text + optional link); **clear** `lastRagSummaryPlainText`.
  - **On failure:** Show error in chat using the **existing `commandResult` pattern** and, where appropriate, the same Confluence error HTML snippet used elsewhere (same structure as `getConfluenceErrorHtml` for message, suggestion, actions) so Confluence failures in chat look consistent with the rest of the extension. Do not leave the user without feedback.

---

### Phase D: Backend Confluence

**D1. Verify content-only create**

- Ensure `intelligent-create` works when only `content`/`body_content` is set and `files` is empty (format single body → create page). Add a content-only branch if the pipeline currently assumes non-empty `file_contents`. No new endpoint.

---

### Phase E: UX and edge cases

**E1. Index modal for first-time summary**  
Reuse existing index-required modal when summary intent is detected and index is missing; or auto-index and "Indexing… try again in a minute."

**E2. Cleanup**  
Covered in B3 and C2: clear on successful save and on new non–save user message (or only update when a new summary is set).

**E3. Optional "Save to Confluence" chip**  
After rendering a summary, optional chip that triggers `handleSaveLastSummaryToConfluence()`.

---

## 4. Prioritization and order

| Priority | Step | Delivers |
|----------|------|----------|
| P0 | B1 – Index guarantee for summary | Index exists (or modal) before summary. |
| P0 | B2 – Intent order (Save → Summary → Default) + summary query | Correct routing; summary in chat. |
| P0 | B3 – Store last summary + cleanup triggers | Last summary available; no stale reuse. |
| P0 | C1 – Save intent (checked first) | Chat recognizes "save this to Confluence." |
| P0 | C2 – handleSaveLastSummaryToConfluence (success + error via commandResult) | Page created; errors shown in chat. |
| P1 | D1 – Content-only create | Backend supports content-only. |
| P1 | E1 – Index modal for summary | Clear UX when index missing. |
| P2 | E3 – "Save to Confluence" chip | Faster UX after summary. |

---

## 5. Verification (acceptance criteria)

- **B1:** No folder → "Open a folder first." No index → modal or auto-index; after index, summary request sends RAG with `root_path`.
- **B2:** "analyze this codebase and give its summary" → one RAG request, summary in chat; "save this summary in a Confluence page" → no RAG, Confluence flow. Order: save intent checked before summary intent.
- **B3:** After summary, `lastRagSummaryPlainText` is set; after successful save or new non–save message, it is cleared as specified.
- **C1:** With prior summary → "save this to Confluence" runs C2; without prior summary → chat message asking user to request a summary first.
- **C2:** With auth, create succeeds and success + link shown in chat, `lastRagSummaryPlainText` cleared; on failure, error shown in chat via `commandResult` (and Confluence error HTML where used).
- **D1:** `POST /confluence/intelligent-create` with only `content` + title + space + auth → page created.
- **Existing flow:** "Save to Confluence" button flow unchanged.

---

## 6. Files to touch

- **Extension:** `ChatPanelViewProvider.ts`: intent order (Save → Summary → Default), B1, B2, B3 with cleanup, C1, C2 with success/error handling; optional small `intent.ts` for "isSaveToConfluenceIntent" / "isSummaryIntent".
- **Backend RAG:** Optional `POST /summarize` (A2 Option B).
- **Backend Confluence:** Ensure content-only path in `intelligent-create` (D1).

---

## 7. Risks and notes

- Large repos: index time and "index in progress" messaging (or modal).
- LLM context: keep summary prompt "concise"; reduce `top_k`/`max_context_chunks` for summary if needed.
- Intent heuristics: start small; add `/save-summary` slash as explicit alternative if desired.
- Confluence content-only: formatting branch for plain text (e.g. wrap in `<p>`).

---

## 8. Summary

- **Intent order:** In one place: (1) Save-to-Confluence → handleSaveLastSummaryToConfluence and return; (2) Codebase-summary → index + RAG + set last summary and return; (3) Default → existing RAG/slash/auto.
- **Cleanup:** Clear `lastRagSummaryPlainText` on successful Confluence save and when the user sends a new message that is not "save to Confluence" (so we don't reuse an old summary).
- **Errors:** Use existing `commandResult` pattern and Confluence error HTML for failed Confluence create in chat.
- **Existing:** RAG (index, chunks, embeddings, Chroma, OpenAI), Confluence (intelligent-create), chat with `root_path`; "Save to Confluence" button unchanged.
