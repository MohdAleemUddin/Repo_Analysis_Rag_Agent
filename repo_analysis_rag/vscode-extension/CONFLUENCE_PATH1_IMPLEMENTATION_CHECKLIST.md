# Path 1 Implementation Checklist – Zeroui Confluence Flow

**Plan:** Path 1 Implementation Plan (Zeroui Extension Confluence Flow)  
**Scope:** `repo_analysis_rag/Zeroui_Repo_Analysis_Rag_Agent/offline-folder-rag/vscode-extension/`  
**Backend:** No changes (unchanged).

---

## 1. Code changes implemented

| Phase | Item | File | Change | Status |
|-------|------|------|--------|--------|
| 1.1 | Add related files – send only checked files | [src/webview/ui/chatPanelHtml.ts](src/webview/ui/chatPanelHtml.ts) | `querySelectorAll('input[type="checkbox"]')` → `querySelectorAll('input[type="checkbox"]:checked')` in `confluenceAddRelatedFiles` branch so `currentFiles` contains only selected paths. | Done |
| 1.2 | Clear Confluence state on Done/Cancel | [src/webview/ChatPanelViewProvider.ts](src/webview/ChatPanelViewProvider.ts) | In `message.type === "confluenceDone" \|\| message.type === "confluenceCancel"` branch: added `this.confluenceState = {}` before the existing comment. | Done |
| 2.2 | Analysis card – comment and defensive vscode | [src/webview/ui/confluenceHtml.ts](src/webview/ui/confluenceHtml.ts) | (1) Comment added: script must run when card is appended so Create Perfect Page works. (2) In `submitConfluenceCreate`, added `if (!window.vscode && typeof acquireVsCodeApi === 'function') { window.vscode = acquireVsCodeApi(); }` before the existing readiness check. | Done |
| 1.3 | Error card Retry (create) | N/A | No code change; `handleConfluenceCreate` already uses `this.confluenceState.lastTitle` / `lastSpace` when message has no title/space. Documented for verification only. | N/A |

---

## 2. Wiring verification (no dead or disconnected code)

| Flow / button | Message / handler | Connection |
|---------------|-------------------|------------|
| Save to Confluence | `confluenceSave` → `handleConfluenceSaveWithContext([])` | ChatPanelViewProvider.ts message handler. |
| Browse Files | `confluenceBrowse` → open dialog → `handleConfluenceSaveWithContext(fullPaths)` | Same; chatPanelHtml.ts click delegate for `data-action="confluenceBrowse"`. |
| Next: Let AI Decide | `confluenceNext` + `files` → `handleConfluenceNext(message.files)` | Same; chatPanelHtml gets checked checkboxes, posts `confluenceNext`; handler calls `intelligentAnalyze` then posts analysis HTML. |
| Add related files | `confluenceAddRelatedFiles` + `currentFiles` → `handleConfluenceAddRelatedFiles(message.currentFiles)` | Same; after fix, `currentFiles` = only checked checkboxes; handler merges with context and new picks, then `handleConfluenceSaveWithContext(merged, true)`. |
| Cancel (file selector) | `confluenceCancel` → clear state (new) + no-op | Handler clears `confluenceState`; cards remain in chat. |
| Edit Title (analysis) | No message; contenteditable + `editConfluenceTitle()` focus | Inline script in getConfluenceAnalysisHtml; no handler needed. |
| Create Perfect Page | `confluenceCreate` + `title`, `space` → `handleConfluenceCreate(message.title, message.space)` | Inline `submitConfluenceCreate()` reads DOM, posts `confluenceCreate`; handler uses `intelligentCreate`; progress then success/error via `updateId`. |
| Open in Browser / View Page | `openUrl` + `url` → `vscode.env.openExternal` | ChatPanelViewProvider handles `openUrl`; success/document-project HTML use inline `openConfluenceUrl`/postMessage. |
| Copy Link | `copyToClipboard` + `text` → `vscode.env.clipboard.writeText` + toast | Same; success/document-project HTML use inline `copyConfluenceLink`/postMessage. |
| Done | `confluenceDone` → clear state (new) + no-op | Handler clears `confluenceState`; cards remain. |
| Cancel (progress/error) | `confluenceCancel` → clear state (new) + no-op | Same as Done. |
| Retry (error) | `confluenceRetryAnalyze` + `files` or `confluenceCreate` (no args) | Handlers: `handleConfluenceNext(message.files)` or `handleConfluenceCreate('','DEV')` using `lastTitle`/`lastSpace`. |
| Update Settings | `confluenceSettings` → `workbench.action.openSettings`, `confluence` | ChatPanelViewProvider handles `confluenceSettings`. |
| Progress replace | `updateId` + payload → replace element `[data-confluence-id="…"]` | chatPanelHtml.ts commandResult handler replaces innerHTML and re-runs scripts. |

All of the above are live code paths; no handler or button is left disconnected or dead.

---

## 3. E2E verification checklist (manual)

Run with backend at `confluence.apiBaseUrl` and Confluence credentials set.

- [ ] 1. Open chat; click Save to Confluence (or command). File selector card appears in chat.
- [ ] 2. Click Browse Files; select one or more files. List updates; Next: Let AI Decide enabled when at least one selected.
- [ ] 3. Click Next: Let AI Decide. Analysis card appears (template, title, space, Edit Title, Create Perfect Page).
- [ ] 4. Optionally edit title and/or change space. Values visible.
- [ ] 5. Click Create Perfect Page. Progress card appears; then success card (with link) or error card.
- [ ] 6. On success: View Page / Open in Browser opens Confluence page.
- [ ] 7. On success: Copy Link copies URL and shows toast.
- [ ] 8. On success: Done clears state; no error (re-run flow to confirm fresh state).
- [ ] 9. On error: Retry retries create with same title/space.
- [ ] 10. On error: Update Settings opens Confluence settings.
- [ ] 11. On error: Cancel clears state; no error.
- [ ] 12. File selector: select some files; Add related files. Dialog opens; merged list = selected + new picks (and context if any).
- [ ] 13. Progress card: Cancel. No crash.

---

## 4. PRD/US compliance (Path 1)

- [ ] Single interface; no new tabs (PRD 4.2.1; US1): all Confluence UI is chat messages.
- [ ] 3-click flow: Save → Select files → Create (PRD UR3; US1): steps 1–5 above.
- [ ] Edit Title only via analysis card (US3): contenteditable + Edit Title button; no separate modal.
- [ ] Progress as single updating message (US1): progress card posted with `updateId`; replaced by success/error.
- [ ] Success: Open in Browser, Copy Link (PRD 6.1): steps 6–7.
- [ ] Error: Retry, Cancel, Update Settings (US13): steps 9–11.
- [ ] No dummy/dead buttons: every Confluence button triggers the correct message and handler (or explicit no-op for Done/Cancel).

---

## 5. Summary

- **Phase 1.1:** Add related files sends only checked file paths; wired to `handleConfluenceAddRelatedFiles`.
- **Phase 1.2:** Done/Cancel clear `confluenceState`; wired in same handler branch.
- **Phase 2.2:** Analysis card has comment and defensive `window.vscode` in `submitConfluenceCreate`; Create Perfect Page remains wired to `handleConfluenceCreate` via `confluenceCreate`.
- **Phase 1.3:** Retry (create) verified as no code change; relies on existing `lastTitle`/`lastSpace`.
- No backend changes; no React Confluence UI changes. Path 1 HTML flow is the only Confluence flow; all referenced buttons and handlers are connected and in use.
