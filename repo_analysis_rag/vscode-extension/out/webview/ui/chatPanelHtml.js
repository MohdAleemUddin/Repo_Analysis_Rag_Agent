"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.getChatPanelHtml = getChatPanelHtml;
const simple_language_json_1 = __importDefault(require("../../confluence/simple-language.json"));
const PLACEHOLDER_TEXT = "Plan · @ for context · / for commands";
/** Escape string for embedding inside a JavaScript double-quoted string (avoid XSS and broken script). */
function escapeForJs(s) {
    return s.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
}
function getNonce() {
    const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    let text = "";
    for (let i = 0; i < 16; i++) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}
function getChatPanelHtml(extensionUri, placeholderText = PLACEHOLDER_TEXT, panelNonce) {
    const nonce = panelNonce ?? getNonce();
    const firstTimeTooltipJs = escapeForJs(simple_language_json_1.default.phrases.firstInteraction.buttonTooltip);
    const saveToConfluenceLabelJs = escapeForJs(simple_language_json_1.default.buttons.saveToConfluence);
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'nonce-${nonce}'; style-src 'unsafe-inline';" />
    <title>Offline Folder RAG</title>
    <style>
        :root {
            color-scheme: light dark;
            --bg: #f4f4f5;
            --panel-bg: #ffffff;
            --surface: #f0f0f3;
            --border: #d0d0db;
            --muted: #6c6e77;
            --text: #111;
            --accent: #0e639c;
        }

        @media (prefers-color-scheme: dark) {
            :root {
                --bg: #0b0c10;
                --panel-bg: #16181c;
                --surface: #1e2027;
                --border: #3a3d46;
                --muted: #9ea4b9;
                --text: #f5f6f8;
                --accent: #2ea3ff;
            }
        }

        body {
            margin: 0;
            background: var(--bg);
            font-family: "Segoe UI", system-ui, sans-serif;
            color: var(--text);
        }

        #chat-panel-container {
            display: flex;
            flex-direction: column;
            height: 100vh;
            padding: 16px;
            box-sizing: border-box;
            gap: 16px;
            position: relative;
        }

        #confluence-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: var(--bg);
            z-index: 1000;
            display: none;
            flex-direction: column;
            padding: 20px;
            overflow-y: auto;
        }

        #confluence-overlay.visible {
            display: flex;
        }

        #chat-panel-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--border);
        }

        #header-titles h1 {
            margin: 0;
            font-size: 1.1rem;
            font-weight: 600;
        }

        #header-titles p {
            margin: 2px 0 0;
            color: var(--muted);
            font-size: 0.85rem;
        }

        #header-actions {
            display: flex;
            gap: 8px;
        }

        #header-actions button {
            border: 1px solid var(--border);
            border-radius: 8px;
            width: 36px;
            height: 36px;
            font-size: 1.25rem;
            background: var(--surface);
            color: var(--text);
            cursor: pointer;
        }

        #header-actions button:hover,
        #header-actions button:focus-visible {
            border-color: var(--accent);
            outline: none;
            box-shadow: 0 0 0 2px rgba(14, 99, 156, 0.2);
        }

        #confluence-button {
            font-size: 1.2rem !important;
        }

        .confluence-card {
            margin-top: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        #conversation {
            flex: 1;
            overflow-y: auto;
            background: var(--panel-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 16px;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .conversation-empty {
            color: var(--muted);
            font-size: 0.95rem;
        }

        .conversation-message {
            padding: 10px 14px;
            border-radius: 10px;
            max-width: 90%;
            line-height: 1.4;
            word-break: break-word;
            box-sizing: border-box;
        }

        .conversation-message.user {
            align-self: flex-end;
            background: rgba(14, 99, 156, 0.12);
            border: 1px solid rgba(14, 99, 156, 0.3);
        }

        .conversation-message.assistant {
            align-self: flex-start;
            background: var(--surface);
            border: 1px solid var(--border);
            width: 100%;
            max-width: 100%;
        }

        #composer-card {
            background: var(--panel-bg);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 18px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.05);
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        #composer-form {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        #composer-form label {
            font-weight: 600;
            font-size: 0.95rem;
        }

        #composer-input {
            width: 100%;
            min-height: 120px;
            border-radius: 12px;
            border: 1px solid var(--border);
            padding: 12px;
            background: var(--surface);
            color: var(--text);
            font-size: 1rem;
            resize: vertical;
        }

        #composer-input:focus-visible {
            outline: 2px solid var(--accent);
            border-color: transparent;
        }

        .composer-hint {
            margin: 0;
            font-size: 0.85rem;
            color: var(--muted);
        }

        .assistant-response {
            border-left: 2px solid #0e639c;
            padding-left: 12px;
            margin-bottom: 16px;
        }

        .chips-row {
            display: flex;
            gap: 8px;
            margin-bottom: 8px;
        }

        .chip {
            font-size: 10px;
            font-weight: bold;
            padding: 2px 6px;
            border-radius: 4px;
            text-transform: uppercase;
        }

        .confidence-found { background: #28a745; color: white; }
        .confidence-partial { background: #ffc107; color: black; }
        .confidence-not_found { background: #dc3545; color: white; }

        .mode-rag { background: #6f42c1; color: white; }
        .mode-tools { background: #fd7e14; color: white; }
        .mode-hybrid { background: #007bff; color: white; }

        .answer-text {
            line-height: 1.5;
            margin-bottom: 12px;
        }

        .citations-list {
            font-size: 12px;
            color: #aaa;
        }

        .citations-list ul {
            list-style: none;
            padding: 0;
            margin: 4px 0;
        }

        .citation-link {
            color: #3794ff;
            text-decoration: none;
        }

        .citation-link:hover {
            text-decoration: underline;
        }

        #composer-bottom-row {
            display: flex;
            align-items: center;
            gap: 12px;
            flex-wrap: wrap;
        }

        .composer-dropdown {
            display: flex;
            flex-direction: column;
            font-size: 0.75rem;
            color: var(--muted);
        }

        .composer-dropdown label {
            font-size: 0.9rem;
            margin-bottom: 4px;
            font-weight: 500;
        }

        .composer-dropdown select {
            border-radius: 8px;
            border: 1px solid var(--border);
            background: var(--surface);
            padding: 6px 10px;
            font-size: 0.95rem;
            color: var(--text);
            min-width: 120px;
        }

        #composer-bottom-row button {
            border: 1px solid var(--border);
            border-radius: 10px;
            background: var(--surface);
            width: 40px;
            height: 40px;
            font-size: 1.4rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        #composer-bottom-row button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            border-color: var(--border);
        }

        #composer-bottom-row button:hover,
        #composer-bottom-row button:focus-visible {
            border-color: var(--accent);
            outline: none;
            box-shadow: 0 0 0 2px rgba(14, 99, 156, 0.2);
        }

        .composer-send-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }

        .send-button {
            border: none;
            border-radius: 999px;
            padding: 10px 26px;
            background: var(--accent);
            color: #fff;
            font-weight: 600;
            cursor: pointer;
        }

        .send-button:focus-visible {
            outline: 2px solid rgba(46, 163, 255, 0.6);
        }

        .send-hint {
            color: var(--muted);
            font-size: 0.85rem;
        }

        .context-attachments {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            min-height: 28px;
        }

        .context-attachments.hidden {
            display: none;
        }

        .context-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 999px;
            border: 1px solid var(--border);
            background: var(--surface);
            font-size: 0.85rem;
        }

        .context-chip button {
            border: none;
            background: transparent;
            color: var(--muted);
            cursor: pointer;
            font-size: 1rem;
            line-height: 1;
        }

        #context-menu {
            position: absolute;
            bottom: 100%;
            left: 16px;
            width: 180px;
            background: var(--panel-bg);
            border: 1px solid var(--border);
            border-radius: 12px;
            box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);
            padding: 8px 0;
            display: none;
            flex-direction: column;
            z-index: 2;
            margin-bottom: 8px;
        }

        #context-menu.visible {
            display: flex;
        }

        #context-menu button {
            border: none;
            background: none;
            text-align: left;
            padding: 8px 16px;
            width: 100%;
            cursor: pointer;
            color: var(--text);
        }

        #context-menu button:hover,
        #context-menu button:focus-visible {
            background: var(--surface);
            outline: none;
        }

        #local-row {
            display: flex;
            align-items: center;
            gap: 12px;
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 8px 14px;
            background: var(--surface);
        }

        #local-row label {
            font-weight: 600;
        }

        #local-row select {
            border-radius: 8px;
            border: 1px solid var(--border);
            padding: 6px 10px;
            background: var(--panel-bg);
            color: var(--text);
            font-size: 0.9rem;
        }

        .modal-backdrop {
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.6);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 10;
        }

        .modal-backdrop.visible {
            display: flex;
        }

        .modal {
            background: var(--panel-bg);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            width: min(320px, 80%);
            text-align: center;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .modal-actions {
            display: flex;
            justify-content: center;
            gap: 10px;
        }

        .modal-actions button {
            padding: 8px 16px;
            border-radius: 8px;
            border: 1px solid var(--border);
            background: var(--surface);
            cursor: pointer;
        }

        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
    </style>
</head>
<body>
    <div id="chat-panel-container">
        <div id="confluence-overlay"></div>
        <header id="chat-panel-header">
            <div id="header-titles">
                <h1>Chat</h1>
                <p>Offline Folder RAG</p>
            </div>
            <div id="header-actions" role="toolbar" aria-label="Chat header actions">
                <button type="button" aria-label="Start a new conversation" title="Start new chat">+</button>
                <button type="button" aria-label="View more options" title="More options">…</button>
            </div>
        </header>

        <section id="conversation" role="log" aria-live="polite">
            <div id="empty-state" class="conversation-empty">No conversation yet.</div>
        </section>

        <section id="composer-card" aria-label="Chat composer">
            <form id="composer-form">
                <label for="composer-input">Message</label>
                <textarea
                    id="composer-input"
                    placeholder="${placeholderText}"
                    aria-label="Message input"
                    autocomplete="off"
                ></textarea>
                <p class="composer-hint">${placeholderText}</p>

                <div id="context-attachments" class="context-attachments hidden" aria-live="polite"></div>

                <div id="context-menu" role="menu" aria-label="@ context menu">
                    <button type="button" data-action="folder">@folder</button>
                    <button type="button" data-action="selection">@selection</button>
                    <button type="button" data-action="file">@file</button>
                </div>

                <div id="composer-bottom-row" aria-label="Composer quick controls">
                    <div class="composer-dropdown">
                        <label for="infinity-dropdown">∞</label>
                        <select id="infinity-dropdown" aria-label="Infinity dropdown">
                            <option value="local" selected>Local</option>
                            <option value="future-1" disabled>Future entry 1</option>
                            <option value="future-2" disabled>Future entry 2</option>
                        </select>
                    </div>
                    <div class="composer-dropdown">
                        <label for="mode-select">Mode</label>
                        <select id="mode-select" aria-label="Composer mode">
                            <option value="auto">Auto</option>
                            <option value="rag">RAG</option>
                            <option value="tools">Tools</option>
                        </select>
                    </div>
                    <button id="attachment-button" type="button" aria-label="Attach file" title="Attach file">📎</button>
                    <button id="microphone-button" type="button" aria-label="Record voice" title="Not available" disabled>🎤</button>
                    <button id="confluence-button" type="button" aria-label="Save to Confluence" title="Save to Confluence">💾</button>
                </div>

                <div class="composer-send-row">
                    <button type="submit" class="send-button" aria-label="Send message" title="Send message">Send</button>
                    <span class="send-hint">Press Ctrl+Enter to send</span>
                </div>
            </form>
        </section>

        <div id="local-row">
            <label for="local-dropdown">Local</label>
            <select id="local-dropdown" aria-label="Local data source selector">
                <option value="__select_folder__">Select Folder…</option>
            </select>
        </div>
    </div>

    <div class="modal-backdrop" id="indexModal" role="dialog" aria-modal="true" aria-labelledby="indexModalTitle">
        <div class="modal">
            <p id="indexModalTitle"><strong>Index required</strong></p>
            <p>Run a full index to use gated commands.</p>
            <div class="modal-actions">
                <button id="indexFull" type="button" aria-label="Index full workspace" title="Index full workspace">Index Full</button>
                <button id="indexCancel" type="button" aria-label="Cancel indexing" title="Cancel indexing">Cancel</button>
            </div>
        </div>
    </div>

    <script nonce="${nonce}">
        (function () {
            const vscode = acquireVsCodeApi();
            window.vscode = vscode;
            const composerForm = document.getElementById("composer-form");
            const composerInput = document.getElementById("composer-input");
            const conversation = document.getElementById("conversation");
            const emptyState = document.getElementById("empty-state");
            const contextAttachments = document.getElementById("context-attachments");
            const contextMenu = document.getElementById("context-menu");
            const modeSelect = document.getElementById("mode-select");
            const indexModal = document.getElementById("indexModal");
            const indexFullButton = document.getElementById("indexFull");
            const indexCancelButton = document.getElementById("indexCancel");
            const infinityDropdown = document.getElementById("infinity-dropdown");
            const attachmentButton = document.getElementById("attachment-button");
            const microphoneButton = document.getElementById("microphone-button");
            const confluenceButton = document.getElementById("confluence-button");
            const localDropdown = document.getElementById("local-dropdown");

            const COMPOSER_MODES = ["auto", "rag", "tools"];
            const LOCAL_SELECT_VALUE = "__select_folder__";

            let currentMode = "auto";
            let lastLocalSelection = LOCAL_SELECT_VALUE;
            let onboardingTooltipShown = 0;
            let onboardingUsageCount = 0;
            const FIRST_TIME_TOOLTIP = "${firstTimeTooltipJs}";
            const SAVE_TO_CONFLUENCE_LABEL = "${saveToConfluenceLabelJs}";

            function updateConfluenceButtonTitle() {
                if (confluenceButton) {
                    confluenceButton.title = onboardingUsageCount === 0 ? FIRST_TIME_TOOLTIP : SAVE_TO_CONFLUENCE_LABEL;
                    confluenceButton.setAttribute("aria-label", confluenceButton.title);
                }
            }

            const attachedContext = {
                root_path: null,
                selection_text: null,
                active_file_paths: [],
            };

            function generateContextId() {
                return \`ctx-\${Date.now()}-\${Math.random().toString(16).slice(2)}\`;
            }

            function applyMode(newMode, notify = false) {
                if (!COMPOSER_MODES.includes(newMode)) {
                    return;
                }

                currentMode = newMode;
                if (modeSelect) {
                    modeSelect.value = newMode;
                }

                if (notify) {
                    vscode.postMessage({ type: "setMode", mode: newMode });
                }
            }

            if (modeSelect) {
                modeSelect.addEventListener("change", () => applyMode(modeSelect.value, true));
            }

            function renderLocalOptions(state) {
                if (!localDropdown) {
                    return;
                }

                localDropdown.innerHTML = \`<option value="\${LOCAL_SELECT_VALUE}">Select Folder…</option>\`;

                const seen = new Set();
                const rootPath = state?.rootPath;
                const recent = Array.isArray(state?.recentFolders) ? state.recentFolders : [];
                const additions = [];

                if (rootPath) {
                    seen.add(rootPath);
                    additions.push(rootPath);
                }

                for (const folder of recent) {
                    if (additions.length >= 10) {
                        break;
                    }

                    if (seen.has(folder)) {
                        continue;
                    }

                    seen.add(folder);
                    additions.push(folder);
                }

                for (const folder of additions) {
                    const option = document.createElement("option");
                    option.value = folder;
                    option.textContent = folder;
                    localDropdown.appendChild(option);
                }

                const targetValue = rootPath && seen.has(rootPath) ? rootPath : lastLocalSelection;

                if (targetValue && Array.from(localDropdown.options).some((opt) => opt.value === targetValue)) {
                    localDropdown.value = targetValue;
                    lastLocalSelection = targetValue;
                } else {
                    localDropdown.value = LOCAL_SELECT_VALUE;
                    lastLocalSelection = LOCAL_SELECT_VALUE;
                }
            }

            if (localDropdown) {
                localDropdown.addEventListener("change", () => {
                    const value = localDropdown.value;

                    if (value === LOCAL_SELECT_VALUE) {
                        vscode.postMessage({ type: "localPick" });
                        localDropdown.value = lastLocalSelection;
                        return;
                    }

                    lastLocalSelection = value;
                    vscode.postMessage({ type: "localSelect", folder: value });
                });
            }

            function appendMessage(text, role, isHtml = false) {
                if (!conversation || !text) return;

                if (emptyState) {
                    emptyState.remove();
                }

                const entry = document.createElement("div");
                entry.className = \`conversation-message \${role}\`;
                if (isHtml) {
                    entry.innerHTML = text;
                } else {
                    entry.textContent = text;
                }
                conversation.appendChild(entry);
                conversation.scrollTop = conversation.scrollHeight;
            }

            function createChip(label, value, type, id) {
                const chip = document.createElement("div");
                chip.className = "context-chip";

                const text = document.createElement("span");
                text.textContent = \`\${label}: \${value}\`;
                text.title = value;
                chip.appendChild(text);

                const removeButton = document.createElement("button");
                removeButton.setAttribute("type", "button");
                removeButton.dataset.removeType = type;
                if (id) {
                    removeButton.dataset.removeId = id;
                }
                removeButton.textContent = "×";
                removeButton.ariaLabel = \`Remove \${label} context\`;
                chip.appendChild(removeButton);

                return chip;
            }

            function renderAttachments() {
                if (!contextAttachments) {
                    return;
                }

                contextAttachments.innerHTML = "";

                if (attachedContext.root_path) {
                    contextAttachments.appendChild(createChip("Folder", attachedContext.root_path, "folder"));
                }

                if (attachedContext.selection_text) {
                    contextAttachments.appendChild(createChip("Selection", attachedContext.selection_text, "selection"));
                }

                if (attachedContext.active_file_paths && attachedContext.active_file_paths.length) {
                    attachedContext.active_file_paths.forEach(file => {
                        contextAttachments.appendChild(createChip("File", file.path, "file", file.id));
                    });
                }

                contextAttachments.classList.toggle("hidden", contextAttachments.children.length === 0);
            }

            function buildExtraContext() {
                const extra = {};

                if (attachedContext.root_path) {
                    extra.root_path = attachedContext.root_path;
                }

                if (attachedContext.selection_text) {
                    extra.selection_text = attachedContext.selection_text;
                }

                if (attachedContext.active_file_paths && attachedContext.active_file_paths.length) {
                    extra.active_file_path = attachedContext.active_file_paths[0].path;
                }

                return Object.keys(extra).length ? extra : undefined;
            }

            function clearContext() {
                attachedContext.root_path = null;
                attachedContext.selection_text = null;
                attachedContext.active_file_paths = [];
                renderAttachments();
            }

            function showContextMenu() {
                contextMenu?.classList.add("visible");
            }

            function hideContextMenu() {
                contextMenu?.classList.remove("visible");
            }

            function sendMessage() {
                if (!composerInput) return;
                const text = composerInput.value.trim();
                if (!text) return;

                appendMessage(text, "user");
                const mode = modeSelect?.value || "auto";
                const extraContext = buildExtraContext();

                vscode.postMessage({
                    type: "dispatch",
                    text,
                    mode,
                    extraContext,
                });

                composerInput.value = "";
                composerInput.focus();
                clearContext();
            }

            composerForm?.addEventListener("submit", (event) => {
                event.preventDefault();
                sendMessage();
            });

            composerInput?.addEventListener("keydown", (event) => {
                if (event.key === "@") {
                    showContextMenu();
                }

                if (event.key === "Enter" && !event.shiftKey) {
                    event.preventDefault();
                    sendMessage();
                }
            });

            composerInput?.addEventListener("input", () => {
                if (composerInput.value.endsWith("@")) {
                    showContextMenu();
                }
            });

            modeSelect?.addEventListener("change", () => {
                const mode = modeSelect.value;
                vscode.postMessage({ type: "modeChange", mode });
            });

            if (infinityDropdown) {
                infinityDropdown.addEventListener("change", () => {
                    if (infinityDropdown.value !== "local") {
                        infinityDropdown.value = "local";
                    }
                });
            }

            contextMenu?.addEventListener("click", (event) => {
                const target = event.target;
                if (!(target instanceof HTMLElement)) return;
                const action = target.dataset.action;
                if (!action) return;

                vscode.postMessage({ type: "contextRequest", action });
                hideContextMenu();
                composerInput?.focus();
            });

            contextAttachments?.addEventListener("click", (event) => {
                const button = (event.target instanceof HTMLElement) ? event.target.closest("button[data-remove-type]") : null;
                if (!(button instanceof HTMLElement)) {
                    return;
                }

                const type = button.dataset.removeType;
                const id = button.dataset.removeId;

                if (type === "folder") {
                    attachedContext.root_path = null;
                } else if (type === "selection") {
                    attachedContext.selection_text = null;
                } else if (type === "file" && id) {
                    attachedContext.active_file_paths = attachedContext.active_file_paths.filter(f => f.id !== id);
                }

                renderAttachments();
            });

            document.addEventListener("click", (event) => {
                if (!contextMenu || !composerInput) {
                    return;
                }

                if (contextMenu.contains(event.target)) {
                    return;
                }

                if (event.target === composerInput) {
                    return;
                }

                hideContextMenu();
            });

            indexFullButton?.addEventListener("click", () => {
                vscode.postMessage({ type: "indexAction", action: "full" });
            });

            indexCancelButton?.addEventListener("click", () => {
                vscode.postMessage({ type: "indexAction", action: "cancel" });
            });

            if (attachmentButton) {
                attachmentButton.addEventListener("click", () => {
                    vscode.postMessage({ type: "attachmentPick" });
                });
            }

            if (confluenceButton) {
                updateConfluenceButtonTitle();
                confluenceButton.addEventListener("click", () => {
                    vscode.postMessage({ type: "confluenceSave" });
                });
                confluenceButton.addEventListener("mouseenter", () => {
                    if (onboardingTooltipShown < 3) {
                        vscode.postMessage({ type: "confluenceOnboardingTooltipShown" });
                    }
                });
                confluenceButton.addEventListener("focus", () => {
                    if (onboardingTooltipShown < 3) {
                        vscode.postMessage({ type: "confluenceOnboardingTooltipShown" });
                    }
                });
            }

            function updateConfluenceSelectionUIForCard(card) {
                if (!card) return;
                const list = card.querySelector('.confluence-file-list');
                if (!list) return;
                const countEl = card.querySelector('.confluence-selection-count');
                const nextBtn = card.querySelector('.confluence-next-button');
                if (!countEl || !nextBtn) return;
                const checkboxes = list.querySelectorAll('input[type="checkbox"]:checked');
                const n = checkboxes.length;
                countEl.textContent = 'Selected: ' + n + ' files';
                nextBtn.disabled = n === 0;
                nextBtn.style.cursor = n === 0 ? 'not-allowed' : 'pointer';
                nextBtn.style.opacity = n === 0 ? '0.5' : '1';
            }
            document.addEventListener('change', function(event) {
                const target = event.target;
                if (!(target instanceof HTMLInputElement) || target.type !== 'checkbox') return;
                const list = target.closest('.confluence-file-list');
                if (!list) return;
                const card = list.closest('.confluence-file-selector-card');
                updateConfluenceSelectionUIForCard(card);
            });
            document.addEventListener('click', function(event) {
                const btn = event.target instanceof HTMLElement ? event.target.closest('button[data-action]') : null;
                if (!btn) return;
                const action = btn.getAttribute('data-action');
                if (action === 'confluenceBrowse') {
                    event.preventDefault();
                    vscode.postMessage({ type: 'confluenceBrowse' });
                    return;
                }
                if (action === 'confluenceCancel') {
                    event.preventDefault();
                    vscode.postMessage({ type: 'confluenceCancel' });
                    return;
                }
                if (action === 'confluenceNext') {
                    event.preventDefault();
                    if (btn.hasAttribute('disabled')) return;
                    const card = btn.closest('.confluence-file-selector-card');
                    const list = card?.querySelector('.confluence-file-list');
                    if (!list) return;
                    const checkboxes = list.querySelectorAll('input[type="checkbox"]:checked');
                    const files = Array.from(checkboxes).map(function(cb) { return cb.value; });
                    if (files.length > 0) vscode.postMessage({ type: 'confluenceNext', files: files });
                    return;
                }
                if (action === 'confluenceAddRelatedFiles') {
                    event.preventDefault();
                    const card = btn.closest('.confluence-file-selector-card');
                    const list = card?.querySelector('.confluence-file-list');
                    const currentFiles = list ? Array.from(list.querySelectorAll('input[type="checkbox"]:checked')).map(function(cb) { return cb.value; }) : [];
                    vscode.postMessage({ type: 'confluenceAddRelatedFiles', currentFiles: currentFiles });
                    return;
                }
                if (action === 'confluenceCreate') {
                    event.preventDefault();
                    const card = btn.closest('.confluence-analysis-card');
                    if (!card) return;
                    const titleEl = card.querySelector('.confluence-title-display') || card.querySelector('#confluence-title-display');
                    const spaceEl = card.querySelector('.confluence-space-select') || card.querySelector('#confluence-space-select');
                    const rawTitle = (titleEl && titleEl.textContent ? titleEl.textContent.trim() : '') || 'Documentation';
                    const title = rawTitle.slice(0, 255);
                    const space = (spaceEl && spaceEl.value) ? spaceEl.value : 'DEV';
                    vscode.postMessage({ type: 'confluenceCreate', title: title, space: space });
                    return;
                }
                if (action === 'confluenceDone') {
                    event.preventDefault();
                    vscode.postMessage({ type: 'confluenceDone' });
                    return;
                }
                if (action === 'openUrl') {
                    event.preventDefault();
                    const url = btn.getAttribute('data-url');
                    if (url) vscode.postMessage({ type: 'openUrl', url: url });
                    return;
                }
                if (action === 'copyToClipboard') {
                    event.preventDefault();
                    const text = btn.getAttribute('data-text');
                    if (text) vscode.postMessage({ type: 'copyToClipboard', text: text });
                    return;
                }
            });

            document.addEventListener('click', (event) => {
                const target = event.target;
                if (target && target instanceof HTMLElement && target.classList.contains('citation-link')) {
                    event.preventDefault();
                    const path = target.getAttribute('data-path');
                    const start = parseInt(target.getAttribute('data-start') || "0");
                    const end = parseInt(target.getAttribute('data-end') || "0");
                    vscode.postMessage({ type: 'openCitation', path, start, end });
                }
            });

            window.addEventListener("message", (event) => {
                const message = event.data;
                if (!message) return;

                if (message.type === "insertText" && typeof message.text === "string") {
                    if (composerInput) {
                        const start = composerInput.selectionStart;
                        const end = composerInput.selectionEnd;
                        const val = composerInput.value;
                        composerInput.value = val.substring(0, start) + message.text + val.substring(end);
                        composerInput.selectionStart = composerInput.selectionEnd = start + message.text.length;
                        composerInput.focus();
                    }
                    return;
                }

                if (message.type === "modeState" && typeof message.mode === "string") {
                    applyMode(message.mode);
                    return;
                }

                if (message.type === "localState") {
                    renderLocalOptions({
                        rootPath: message.rootPath,
                        recentFolders: message.recentFolders,
                    });
                    return;
                }

                if (message.type === "onboardingState") {
                    onboardingTooltipShown = typeof message.tooltipShown === "number" ? message.tooltipShown : 0;
                    onboardingUsageCount = typeof message.usageCount === "number" ? message.usageCount : 0;
                    updateConfluenceButtonTitle();
                    return;
                }

                if (message.type === "contextResponse") {
                    if (message.error) {
                        appendMessage(message.error, "assistant");
                        return;
                    }

                    const ctx = message.context ?? {};
                    if (message.action === "folder" && ctx.root_path) {
                        attachedContext.root_path = ctx.root_path;
                    }
                    if (message.action === "selection" && ctx.selection_text) {
                        attachedContext.selection_text = ctx.selection_text;
                    }
                    if (message.action === "file" && ctx.active_file_path) {
                        if (!attachedContext.active_file_paths) attachedContext.active_file_paths = [];
                        attachedContext.active_file_paths.push({
                            id: generateContextId(),
                            path: ctx.active_file_path
                        });
                    }

                    renderAttachments();
                    return;
                }

                if (message.type === "showIndexModal" && indexModal) {
                    indexModal.classList.add("visible");
                    return;
                }

                if (message.type === "dismissIndexModal" && indexModal) {
                    indexModal.classList.remove("visible");
                    return;
                }

                if (message.type === "updateConfluenceMessage" && message.id && message.html) {
                    const el = conversation?.querySelector('[data-confluence-id="' + message.id + '"]');
                    if (el) {
                        el.innerHTML = message.html;
                        const scripts = el.querySelectorAll('script');
                        scripts.forEach(oldScript => {
                            const newScript = document.createElement('script');
                            Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                            newScript.appendChild(document.createTextNode(oldScript.innerHTML));
                            oldScript.parentNode.replaceChild(newScript, oldScript);
                        });
                        conversation.scrollTop = conversation.scrollHeight;
                    }
                    return;
                }

                if (message.type === "commandResult" && message.payload) {
                    if (message.isConfluence) {
                        if (message.updateId) {
                            const el = conversation?.querySelector('[data-confluence-id="' + message.updateId + '"]');
                            if (el) {
                                el.innerHTML = message.payload;
                                const scripts = el.querySelectorAll('script');
                                scripts.forEach(oldScript => {
                                    const newScript = document.createElement('script');
                                    Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                                    newScript.appendChild(document.createTextNode(oldScript.innerHTML));
                                    oldScript.parentNode.replaceChild(newScript, oldScript);
                                });
                                conversation.scrollTop = conversation.scrollHeight;
                            }
                        } else {
                            appendMessage(message.payload, "assistant", true);
                            const lastMessage = conversation?.lastElementChild;
                            if (lastMessage) {
                                const scripts = lastMessage.querySelectorAll('script');
                                scripts.forEach(oldScript => {
                                    const newScript = document.createElement('script');
                                    Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                                    newScript.appendChild(document.createTextNode(oldScript.innerHTML));
                                    oldScript.parentNode.replaceChild(newScript, oldScript);
                                });
                            }
                            conversation.scrollTop = conversation.scrollHeight;
                        }
                        return;
                    }

                    appendMessage(message.payload, "assistant", Boolean(message.isHtml));
                    
                    // Re-run scripts in the appended HTML
                    const lastMessage = conversation.lastElementChild;
                    if (lastMessage && message.isHtml) {
                        const scripts = lastMessage.querySelectorAll('script');
                        scripts.forEach(oldScript => {
                            const newScript = document.createElement('script');
                            Array.from(oldScript.attributes).forEach(attr => newScript.setAttribute(attr.name, attr.value));
                            newScript.appendChild(document.createTextNode(oldScript.innerHTML));
                            oldScript.parentNode.replaceChild(newScript, oldScript);
                        });
                    }
                    return;
                }
            });

            renderAttachments();
        })();
    </script>
</body>
</html>`;
}
