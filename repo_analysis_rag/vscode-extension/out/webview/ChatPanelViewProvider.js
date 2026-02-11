"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChatPanelViewProvider = void 0;
// @ts-nocheck
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const vscode = __importStar(require("vscode"));
const commandRouter_1 = require("../commands/commandRouter");
const confluence_api_1 = require("../confluence/confluence-api");
const confluence_settings_1 = require("../confluence/confluence-settings");
const chatPanelHtml_1 = require("./ui/chatPanelHtml");
const confluenceHtml_1 = require("./ui/confluenceHtml");
const indexGate_1 = require("../services/indexGate");
/** Renders RAG assistant payload as HTML (answer + optional confidence + citations). */
function renderAssistantResponse(payload) {
    if (!payload || typeof payload !== "object")
        return "";
    const escape = (s) => String(s ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    const answer = escape(payload.answer ?? "");
    const confidence = payload.confidence ?? "found";
    const citations = Array.isArray(payload.citations) ? payload.citations : [];
    let html = `<div class="rag-response"><div class="rag-answer">${answer.replace(/\n/g, "<br>")}</div>`;
    if (confidence !== "found") {
        html += `<div class="rag-confidence" data-confidence="${escape(confidence)}">${escape(confidence)}</div>`;
    }
    if (citations.length > 0) {
        html += `<div class="rag-citations"><strong>Citations</strong><ul>`;
        for (const c of citations) {
            const path = escape((c.file_path ?? c.path ?? "").toString());
            const line = (c.line_number ?? c.line_start ?? "").toString();
            const snippet = escape((c.snippet ?? "").toString().slice(0, 300));
            html += `<li><code>${path}${line ? `:${line}` : ""}</code>${snippet ? `<br><pre>${snippet}</pre>` : ""}</li>`;
        }
        html += `</ul></div>`;
    }
    html += `</div>`;
    return html;
}
const agentClient_1 = require("../services/agentClient");
const storage_1 = require("../services/storage");
const autoIndexScheduler_1 = require("../services/autoIndexScheduler");
const onboarding_1 = require("../confluence/onboarding");
const confluenceSpacePreferences_1 = require("../confluence/confluenceSpacePreferences");
const COMPOSER_PLACEHOLDER = "Plan · @ for context · / for commands";
const SUMMARY_PROMPT = "Summarize this codebase. What is this project about? List the main components, technologies, and purpose in a few paragraphs. Use only the provided code and documentation excerpts.";
class ModeState {
    mode;
    constructor() {
        this.mode = (0, agentClient_1.readComposerMode)() ?? "auto";
    }
    getMode() {
        return this.mode;
    }
    setMode(mode) {
        this.mode = mode;
        (0, agentClient_1.writeComposerMode)(mode);
    }
}
const MAX_CONVERSATION_HISTORY = 5;
const DEBUG_LOG_ENDPOINT = 'http://127.0.0.1:7243/ingest/be5e723f-4f73-46b4-bfeb-c2d4f3314dbc';
const DEBUG_LOG_PATH = '.cursor/debug.log';
function debugLog(payload) {
    const full = { ...payload, timestamp: Date.now(), sessionId: 'debug-session' };
    const line = JSON.stringify(full) + '\n';
    fetch(DEBUG_LOG_ENDPOINT, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: line }).catch(() => { });
    try {
        const w = vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath;
        if (w)
            fs.appendFileSync(path.join(w, DEBUG_LOG_PATH), line);
    }
    catch (_) { }
}
class ChatPanelViewProvider {
    extensionContext;
    extensionUri;
    panel;
    panelNonce;
    router;
    modeState;
    agentBaseUrl = agentClient_1.DEFAULT_AGENT_BASE_URL; // Default agent URL
    scheduler;
    confluenceState = {};
    conversationHistory = [];
    confluenceOutput;
    ragLog;
    lastRagSummaryPlainText = undefined;
    constructor(extensionContext, extensionUri, confluenceOutput, ragLog) {
        this.extensionContext = extensionContext;
        this.extensionUri = extensionUri;
        this.confluenceOutput = confluenceOutput;
        this.ragLog = ragLog;
        this.router = new commandRouter_1.CommandRouter(extensionContext, (message) => this.postMessage(message), ragLog);
        this.modeState = new ModeState();
        this.scheduler = new autoIndexScheduler_1.AutoIndexScheduler({
            triggerIndex: () => this.handleIndexAndReport('incremental'),
            getRootPath: () => this.getEffectiveRootPath(),
            agentBaseUrl: this.agentBaseUrl
        });
        // Listen for file saves to trigger auto-indexing
        vscode.workspace.onDidSaveTextDocument((doc) => {
            const rootPath = this.getEffectiveRootPath();
            if (rootPath && (0, indexGate_1.isPathInsideRoot)(rootPath, doc.uri.fsPath)) {
                if ((0, storage_1.readAutoIndex)(this.extensionContext)) {
                    this.scheduler.requestIndex();
                }
            }
        });
    }
    /**
     * Run a full index once in the background (e.g. when extension loads).
     * Does not post to chat; logs to ragLog. Manual /index full and Index button still work.
     */
    async runInitialFullIndex() {
        const rootPath = this.getWorkspaceRootPath();
        if (!rootPath || !rootPath.trim())
            return;
        const indexOnLoad = vscode.workspace.getConfiguration("rag").get("indexOnLoad", true);
        if (!indexOnLoad)
            return;
        this.ragLog?.appendLine("[Offline RAG] Index on load: starting full index in background.");
        (0, indexGate_1.setIndexing)(rootPath);
        try {
            await (0, agentClient_1.triggerIndex)((0, agentClient_1.getRagBaseUrl)(), "full", rootPath);
            await (0, indexGate_1.triggerFullIndex)({ storageRoot: this.extensionContext.globalStorageUri.fsPath }, rootPath, (msg) => this.ragLog?.appendLine(msg));
            this.ragLog?.appendLine("[Offline RAG] Index on load: completed.");
        }
        catch (error) {
            const errMsg = error instanceof Error ? error.message : String(error);
            this.ragLog?.appendLine(`[Offline RAG] Index on load failed: ${errMsg}`);
        }
        finally {
            (0, indexGate_1.clearIndexing)(rootPath);
        }
    }
    pushToConversationHistory(content) {
        if (!content || typeof content !== 'string')
            return;
        this.conversationHistory.push({ content });
        this.conversationHistory = this.conversationHistory.slice(-MAX_CONVERSATION_HISTORY);
    }
    getPreloadedSelection() {
        return this.extensionContext.globalState.get('rag-confluence.preloadedSelection');
    }
    async triggerConfluenceSave() {
        if (!this.panel)
            return;
        await this.handleConfluenceSaveWithContext([]);
    }
    async triggerDocumentProject() {
        if (!this.panel)
            return;
        const rootPath = this.getEffectiveRootPath();
        if (!rootPath || !rootPath.trim()) {
            this.postMessage({ type: 'commandResult', payload: 'Please open a project folder first.', isConfluence: true });
            return;
        }
        this.postMessage({
            type: 'commandResult',
            payload: (0, confluenceHtml_1.getConfluenceDocumentProjectProgressHtml)(this.getConfluenceNonce()),
            isHtml: true,
            isConfluence: true,
        });
        try {
            const config = await (0, confluence_settings_1.getConfluenceConfigAsync)(this.extensionContext);
            const space = (0, confluenceSpacePreferences_1.getSpacePreference)(this.extensionContext, rootPath) ?? 'DOC';
            const result = await (0, confluence_api_1.documentProject)(config, { workspace_path: rootPath, space });
            if (result.error) {
                const html = (0, confluenceHtml_1.getConfluenceErrorHtml)({
                    error: result.error,
                    message: result.message ?? 'Document project failed.',
                    suggestion: 'Check Confluence settings and workspace path. Ensure the agent backend is running.',
                    confidence: 0.5,
                    fallbackAvailable: false,
                    actions: ['Retry', 'Update Settings', 'Cancel'],
                    retryContext: 'create',
                    nonce: this.getConfluenceNonce(),
                });
                this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
                return;
            }
            const html = (0, confluenceHtml_1.getConfluenceDocumentProjectSuccessHtml)(result, this.getConfluenceNonce());
            this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
            if (result.confluence_url) {
                const title = result.intelligence_analysis ? `${(result.intelligence_analysis.project_type ?? 'Project').replace(/^\w/, c => c.toUpperCase())} Project Documentation` : 'Project Documentation';
                const newCreation = { url: result.confluence_url, title, space: space, createdAt: Date.now() };
                const existing = this.extensionContext.globalState.get('confluence.intelligentCreations') ?? [];
                const updated = [newCreation, ...existing].slice(0, 50);
                await this.extensionContext.globalState.update('confluence.intelligentCreations', updated);
            }
        }
        catch (e) {
            const msg = e instanceof Error ? e.message : String(e);
            const html = (0, confluenceHtml_1.getConfluenceErrorHtml)({
                error: 'document_project_failed',
                message: msg,
                suggestion: 'Check Confluence settings and ensure the agent backend is running.',
                confidence: 0.5,
                fallbackAvailable: false,
                actions: ['Retry', 'Update Settings', 'Cancel'],
                retryContext: 'create',
                nonce: this.getConfluenceNonce(),
            });
            this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
        }
    }
    async triggerExportExamples() {
        if (!this.panel)
            return;
        await this.handleConfluenceExportExamples();
    }
    async triggerImportExamples() {
        if (!this.panel)
            return;
        await this.handleConfluenceImportExamples();
    }
    async triggerViewCreations() {
        if (!this.panel)
            return;
        let metrics = null;
        try {
            const config = await (0, confluence_settings_1.getConfluenceConfigAsync)(this.extensionContext);
            const status = await (0, confluence_api_1.getIntelligenceStatus)(config);
            const im = status.intelligence_metrics;
            const lp = status.learning_progress;
            const ir = status.improvement_rates;
            const m = status.metrics;
            metrics = {
                templateSelectionAccuracy: im?.template_selection_accuracy ?? im?.template_selection_intelligence ?? lp?.template_selection_accuracy ?? m?.template_selection_accuracy,
                examplesLearned: lp?.examples_learned,
                intelligenceConfidencePct: im?.intelligence_confidence_pct,
                learningRatePct: im?.learning_rate_pct ?? ir?.learning_rate_pct ?? lp?.learning_rate_pct,
                statusSummary: im?.status_summary,
                successRate: m?.success_rate,
                collectiveIntelligenceCount: im?.team_examples_count ?? lp?.team_examples_count,
            };
        }
        catch {
            metrics = null;
        }
        const creations = this.extensionContext.globalState.get('confluence.intelligentCreations') ?? [];
        const html = (0, confluenceHtml_1.getIntelligenceDashboardHtml)({ metrics, creations, nonce: this.getConfluenceNonce() });
        this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
    }
    async handleConfluenceSaveWithContext(existingFiles = [], skipApiCall) {
        const usageCount = (0, onboarding_1.getOnboardingState)(this.extensionContext).usageCount;
        const rootPath = this.getEffectiveRootPath();
        const chat_context = {
            messages: this.conversationHistory,
            selected_text: this.getPreloadedSelection() ?? undefined,
            workspace_path: rootPath ?? undefined,
        };
        const hasContext = !!(chat_context.messages?.length || chat_context.selected_text);
        let availableFiles = [...existingFiles];
        let options = {};
        if (!skipApiCall && hasContext) {
            try {
                const config = await (0, confluence_settings_1.getConfluenceConfigAsync)(this.extensionContext);
                const result = await (0, confluence_api_1.intelligentAnalyze)(config, { chat_context });
                const ctx = result.context_suggestions;
                if (ctx) {
                    this.confluenceState.contextSuggestions = ctx;
                    options = {
                        contextSuggestions: ctx.project_type_label ? { projectTypeLabel: ctx.project_type_label } : undefined,
                        hasPreloadedSelection: !!chat_context.selected_text,
                        shouldSuggestReadme: !!ctx.should_suggest_readme,
                    };
                    const mentioned = ctx.mentioned_files ?? [];
                    const related = ctx.related_files ?? [];
                    const allRelative = [...new Set([...mentioned, ...related])];
                    if (rootPath && allRelative.length > 0) {
                        const resolved = allRelative
                            .map((p) => path.join(rootPath, p.replace(/\\/g, path.sep)))
                            .filter((p) => { try {
                            return fs.existsSync(p);
                        }
                        catch {
                            return false;
                        } });
                        availableFiles = [...new Set([...existingFiles, ...resolved])];
                    }
                    if (ctx.should_suggest_readme && rootPath) {
                        const readmeNames = ["README.md", "README.txt", "readme.md", "readme.txt"];
                        for (const name of readmeNames) {
                            const readmePath = path.join(rootPath, name);
                            try {
                                if (fs.existsSync(readmePath) && !availableFiles.includes(readmePath)) {
                                    availableFiles = [readmePath, ...availableFiles];
                                    break;
                                }
                            }
                            catch { /* ignore */ }
                        }
                    }
                }
            }
            catch {
                // Fall through to default
            }
        }
        else if (skipApiCall && this.confluenceState.contextSuggestions) {
            const ctx = this.confluenceState.contextSuggestions;
            options = {
                contextSuggestions: ctx.project_type_label ? { projectTypeLabel: ctx.project_type_label } : undefined,
                hasPreloadedSelection: !!chat_context.selected_text,
                shouldSuggestReadme: !!ctx.should_suggest_readme,
            };
        }
        const html = (0, confluenceHtml_1.getConfluenceFileSelectorHtml)(availableFiles, usageCount, this.getConfluenceNonce(), options);
        this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
        if (chat_context.selected_text) {
            await this.extensionContext.globalState.update('rag-confluence.preloadedSelection', undefined);
        }
    }
    async handleConfluenceAddRelatedFiles(currentFiles) {
        const ctx = this.confluenceState.contextSuggestions;
        const rootPath = this.getEffectiveRootPath();
        let merged = [...currentFiles];
        if (ctx?.related_files && rootPath) {
            const resolved = ctx.related_files
                .map((p) => path.join(rootPath, p.replace(/\\/g, path.sep)))
                .filter((p) => { try {
                return fs.existsSync(p);
            }
            catch {
                return false;
            } });
            merged = [...new Set([...currentFiles, ...resolved])];
        }
        const additional = await vscode.window.showOpenDialog({
            canSelectMany: true,
            canSelectFolders: false,
            canSelectFiles: true,
            defaultUri: rootPath ? vscode.Uri.file(rootPath) : undefined,
            filters: { 'Code and Text': ['txt', 'py', 'js', 'ts', 'tsx', 'json', 'md', 'html', 'css', 'yml', 'yaml'] },
            openLabel: "Add Related Files",
        });
        if (additional && additional.length > 0) {
            merged = [...new Set([...merged, ...additional.map((f) => f.fsPath)])];
        }
        await this.handleConfluenceSaveWithContext(merged, true);
    }
    show() {
        if (this.panel) {
            this.panel.reveal(vscode.ViewColumn.One);
            return;
        }
        this.panel = vscode.window.createWebviewPanel("offlineFolderRag.chat", "Offline Folder RAG", vscode.ViewColumn.One, {
            enableScripts: true,
            enableCommandUris: true,
        });
        this.panel.onDidDispose(() => {
            this.panel = undefined;
            (0, agentClient_1.stopHealthPolling)();
        });
        this.panelNonce = this.getNonce();
        this.panel.webview.html = (0, chatPanelHtml_1.getChatPanelHtml)(this.extensionUri, COMPOSER_PLACEHOLDER, this.panelNonce);
        this.panel.webview.onDidReceiveMessage(async (message) => {
            const confluenceTypes = ['confluenceDone', 'confluenceCancel', 'openUrl', 'copyToClipboard', 'confluenceCreate', 'confluenceScriptReady', 'confluenceSave', 'confluenceBrowse', 'confluenceNext', 'confluenceRetryAnalyze', 'confluenceSettings', 'confluenceViewCreations', 'confluenceExportExamples', 'confluenceImportExamples', 'confluenceIntelligenceFeedback', 'confluenceAddRelatedFiles', 'confluenceOnboardingTooltipShown'];
            if (message?.type && confluenceTypes.includes(message.type)) {
                this.confluenceOutput?.appendLine('[Confluence] Webview message: type=' + message.type);
            }
            // #region agent log
            if (message.type === 'confluenceScriptReady') {
                debugLog({ location: 'ChatPanelViewProvider.ts:onDidReceiveMessage', message: 'Confluence analysis script ran', data: {}, hypothesisId: 'H1' });
            }
            if (message.type === 'confluenceCreate') {
                this.confluenceOutput?.appendLine(`[Confluence] Webview message received: type=confluenceCreate title=${message.title ?? '(none)'} space=${message.space ?? '(none)'}`);
                debugLog({ location: 'ChatPanelViewProvider.ts:onDidReceiveMessage', message: 'confluenceCreate received', data: { title: message.title, space: message.space }, hypothesisId: 'H2' });
                vscode.window.showInformationMessage('Creating Confluence page…', { modal: false });
            }
            // #endregion
            await this.handleWebviewMessage(message);
            if (message.type === "dispatch") {
                const { text, mode } = message;
                const normalizedMode = (0, agentClient_1.isComposerMode)(mode) ? mode : this.modeState.getMode();
                this.ragLog?.appendLine(`[RAG] Message received: type=dispatch mode=${String(mode)} normalizedMode=${normalizedMode} text=${(text?.length ?? 0) > 60 ? (String(text).slice(0, 60) + "...") : String(text)}`);
                this.pushToConversationHistory(text);
                if (text.startsWith("/")) {
                    const result = await (0, commandRouter_1.parseSlashCommand)(text, this.extensionContext);
                    if (result.type === 'assistantResponse') {
                        const html = renderAssistantResponse(result.payload);
                        this.postMessage({ type: 'commandResult', payload: html, isHtml: true });
                    }
                    else if (result.type === 'commandResult' && result.payload === 'Indexing started: full scan') {
                        this.postMessage(result);
                        this.handleIndexAndReport('full');
                    }
                    else if (result.type === 'commandResult' && result.payload === 'Indexing started: incremental scan') {
                        this.postMessage(result);
                        this.handleIndexAndReport('incremental');
                    }
                    else if (result.type === 'commandResult' && result.payload === 'Auto-index disabled.') {
                        this.scheduler.stop();
                        this.postMessage(result);
                    }
                    else if (result.type === 'commandResult' && result.payload === 'CONFLUENCE_DOCUMENT_PROJECT') {
                        await this.triggerDocumentProject();
                    }
                    else {
                        this.postMessage(result);
                    }
                }
                else {
                    const normalized = (text || "").toLowerCase().trim();
                    if (!this.isSaveToConfluenceIntent(normalized)) {
                        this.lastRagSummaryPlainText = undefined;
                    }
                    if (this.isSaveToConfluenceIntent(normalized)) {
                        if (!this.lastRagSummaryPlainText) {
                            this.postMessage({ type: "commandResult", payload: "No summary to save. Ask for a codebase summary first (e.g. 'Analyze this codebase and give its summary'), then say 'Save this summary to Confluence'.", isHtml: false });
                            return;
                        }
                        await this.handleSaveLastSummaryToConfluence();
                        return;
                    }
                    if (this.isSummaryIntent(normalized)) {
                        const rootPath = this.getEffectiveRootPath();
                        if (!rootPath) {
                            this.postMessage({ type: "commandResult", payload: "Please open a project folder first.", isHtml: false });
                            return;
                        }
                        const storageRoot = this.extensionContext.globalStorageUri.fsPath;
                        const exists = await (0, indexGate_1.checkIndexExists)({ storageRoot }, rootPath);
                        if (!exists) {
                            this.postMessage({ type: "showIndexModal" });
                            return;
                        }
                        const extraContextSummary = this.buildExtraContext();
                        if (!extraContextSummary) {
                            this.postMessage({ type: "commandResult", payload: "Please open a project folder first.", isHtml: false });
                            return;
                        }
                        try {
                            const response = await (0, agentClient_1.askWithOverride)(SUMMARY_PROMPT, "rag", extraContextSummary);
                            this.ragLog?.appendLine(`[RAG] Response status: ${response.status} ${response.statusText}`);
                            const result = await response.json();
                            const invalidToken = result?.error_code === "INVALID_TOKEN" || result?.error === "INVALID_TOKEN";
                            if (invalidToken || (response.status === 401 && result?.error_code)) {
                                this.ragLog?.appendLine("[RAG] Error: INVALID_TOKEN (missing or invalid X-LOCAL-TOKEN).");
                                this.postMessage({ type: "commandResult", payload: "Error: RAG server requires a valid token. Ensure the backend has been started at least once so the token file exists, then reload the extension. Token file: " + (0, agentClient_1.getTokenFilePath)() });
                                return;
                            }
                            if (!response.ok) {
                                const errPayload = result?.message || result?.remediation || JSON.stringify(result).slice(0, 300);
                                this.postMessage({ type: "commandResult", payload: `Error: ${errPayload}` });
                                return;
                            }
                            this.lastRagSummaryPlainText = result.answer;
                            const assistantResponseHtml = renderAssistantResponse({
                                mode: "rag",
                                confidence: result.confidence || "found",
                                answer: result.answer || JSON.stringify(result),
                                citations: result.citations || []
                            });
                            this.postMessage({ type: "commandResult", payload: assistantResponseHtml, isHtml: true });
                            return;
                        }
                        catch (error) {
                            const errMsg = error instanceof Error ? error.message : String(error);
                            this.ragLog?.appendLine(`[RAG] Request failed: ${errMsg}`);
                            this.postMessage({ type: "commandResult", payload: `Error: ${errMsg}` });
                            return;
                        }
                    }
                    const extraContext = this.buildExtraContext();
                    if (normalizedMode === "rag") {
                        const baseUrl = (0, agentClient_1.getRagBaseUrl)();
                        const askUrl = `${baseUrl}/ask`;
                        this.ragLog?.appendLine(`[RAG] Target: POST ${askUrl}`);
                        this.ragLog?.appendLine(`[RAG] Sending request: POST ${askUrl}`);
                        this.ragLog?.appendLine(`[RAG] Query: ${text.length > 80 ? text.slice(0, 80) + "..." : text}`);
                        try {
                            const response = await (0, agentClient_1.askWithOverride)(text, "rag", extraContext);
                            this.ragLog?.appendLine(`[RAG] Response status: ${response.status} ${response.statusText}`);
                            const result = await response.json();
                            const invalidToken = result?.error_code === "INVALID_TOKEN" || result?.error === "INVALID_TOKEN";
                            if (invalidToken || (response.status === 401 && result?.error_code)) {
                                this.ragLog?.appendLine("[RAG] Error: INVALID_TOKEN (missing or invalid X-LOCAL-TOKEN).");
                                this.ragLog?.appendLine(`[RAG] Token file: ${(0, agentClient_1.getTokenFilePath)()}`);
                                this.postMessage({
                                    type: "commandResult",
                                    payload: "Error: RAG server requires a valid token. Ensure the backend has been started at least once so the token file exists, then reload the extension. Token file: " + (0, agentClient_1.getTokenFilePath)(),
                                });
                                return;
                            }
                            if (!response.ok) {
                                this.ragLog?.appendLine(`[RAG] Server error response: ${typeof result?.detail === "string" ? result.detail : JSON.stringify(result).slice(0, 300)}`);
                                const errPayload = result?.message || result?.remediation || JSON.stringify(result).slice(0, 300);
                                this.postMessage({ type: "commandResult", payload: `Error: ${errPayload}` });
                                return;
                            }
                            this.ragLog?.appendLine(`[RAG] Response OK: answer length=${String(result?.answer ?? "").length}, citations=${result?.citations?.length ?? 0}, confidence=${result?.confidence ?? "—"}`);
                            let payload = result.answer || JSON.stringify(result);
                            const assistantResponseHtml = renderAssistantResponse({
                                mode: "rag",
                                confidence: result.confidence || "found",
                                answer: payload,
                                citations: result.citations || []
                            });
                            this.postMessage({
                                type: "commandResult",
                                payload: assistantResponseHtml,
                                isHtml: true
                            });
                        }
                        catch (error) {
                            const errMsg = error instanceof Error ? error.message : String(error);
                            this.ragLog?.appendLine(`[RAG] Request failed: ${errMsg}`);
                            this.postMessage({
                                type: "commandResult",
                                payload: `Error: ${errMsg}`,
                            });
                        }
                    }
                    else if (normalizedMode === "auto") {
                        this.ragLog?.appendLine(`[RAG] Routing to auto (overview/search/ask).`);
                        try {
                            await this.router.autoRouteInput(text, extraContext);
                        }
                        catch (error) {
                            this.ragLog?.appendLine(`[RAG] Auto route failed: ${error instanceof Error ? error.message : String(error)}`);
                            this.postMessage({
                                type: "commandResult",
                                payload: `Error: ${error instanceof Error ? error.message : String(error)}`,
                            });
                        }
                    }
                    else {
                        this.ragLog?.appendLine(`[RAG] Routing to tools (no /ask).`);
                        await this.router.handleCommand(text, extraContext);
                    }
                }
            }
            else if (message.type === "indexAction") {
                const workspaceFolders = vscode.workspace.workspaceFolders;
                if (!workspaceFolders || workspaceFolders.length === 0)
                    return;
                const rootPath = workspaceFolders[0].uri.fsPath;
                if (message.action === "full") {
                    this.postMessage({ type: "dismissIndexModal" });
                    this.handleIndexAndReport('full');
                }
                else if (message.action === "cancel") {
                    this.postMessage({ type: "dismissIndexModal" });
                    this.postMessage({ type: "commandResult", payload: "Index not available; cannot answer" });
                }
            }
            else if (message.type === "openCitation") {
                const { path: filePath, start, end } = message;
                const workspaceFolders = vscode.workspace.workspaceFolders;
                if (workspaceFolders && workspaceFolders.length > 0) {
                    const fullPath = vscode.Uri.joinPath(workspaceFolders[0].uri, filePath);
                    const doc = await vscode.workspace.openTextDocument(fullPath);
                    const editor = await vscode.window.showTextDocument(doc);
                    const range = new vscode.Range(start - 1, 0, end - 1, 0);
                    editor.selection = new vscode.Selection(range.start, range.end);
                    editor.revealRange(range, vscode.TextEditorRevealType.InCenter);
                }
            }
            else if (message.type === "modeChange" && (0, agentClient_1.isComposerMode)(message.mode)) {
                this.modeState.setMode(message.mode);
                this.postModeState();
            }
            else if (message.type === "confluenceOnboardingTooltipShown") {
                (0, onboarding_1.markTooltipShown)(this.extensionContext);
                this.postOnboardingState();
            }
            else if (message.type === "confluenceSave") {
                await this.handleConfluenceSaveWithContext([]);
            }
            else if (message.type === "contextRequest") {
                this.handleContextRequest(message.action);
            }
            else if (message.type === "attachmentPick") {
                await this.handleAttachmentRequest();
            }
            else if (message.type === "localSelect" && typeof message.folder === "string") {
                await (0, storage_1.writeRootPath)(this.extensionContext, message.folder);
                this.postLocalState();
            }
            else if (message.type === "localPick") {
                const folder = await vscode.window.showOpenDialog({
                    canSelectMany: false,
                    canSelectFolders: true,
                    canSelectFiles: false,
                    openLabel: "Select Folder",
                });
                if (folder && folder.length > 0) {
                    await (0, storage_1.writeRootPath)(this.extensionContext, folder[0].fsPath);
                    this.postLocalState();
                }
            }
            else if (message.type === "confluenceBrowse") {
                const files = await vscode.window.showOpenDialog({
                    canSelectMany: true,
                    canSelectFolders: false,
                    canSelectFiles: true,
                    filters: {
                        'Code and Text': ['txt', 'py', 'js', 'ts', 'tsx', 'json', 'md', 'html', 'css', 'yml', 'yaml']
                    },
                    openLabel: "Select Files for Confluence",
                });
                if (files && files.length > 0) {
                    const fullPaths = files.map(f => f.fsPath);
                    await this.handleConfluenceSaveWithContext(fullPaths);
                }
            }
            else if (message.type === "confluenceAddRelatedFiles") {
                await this.handleConfluenceAddRelatedFiles(message.currentFiles || []);
            }
            else if (message.type === "confluenceNext") {
                await this.handleConfluenceNext(message.files || []);
            }
            else if (message.type === "confluenceRetryAnalyze") {
                await this.handleConfluenceNext(message.files || []);
            }
            else if (message.type === "confluenceCreate") {
                await this.handleConfluenceCreate(message.title || '', message.space || 'DEV');
            }
            else if (message.type === "confluenceDone" || message.type === "confluenceCancel") {
                this.confluenceOutput?.appendLine('[Confluence] Success card: Done/Cancel received.');
                this.confluenceState = {};
                // Cards remain in conversation as history; no action needed
            }
            else if (message.type === "openUrl" && message.url) {
                this.confluenceOutput?.appendLine('[Confluence] Success card: View page requested: ' + (message.url ?? ''));
                try {
                    await vscode.env.openExternal(vscode.Uri.parse(message.url));
                }
                catch (e) {
                    this.confluenceOutput?.appendLine('[Confluence] openExternal error: ' + (e instanceof Error ? e.message : String(e)));
                    vscode.window.showErrorMessage('Confluence: Could not open link. ' + (e instanceof Error ? e.message : String(e)));
                }
            }
            else if (message.type === "copyToClipboard" && message.text) {
                this.confluenceOutput?.appendLine('[Confluence] Success card: Copy link requested (length ' + (message.text?.length ?? 0) + ').');
                try {
                    await vscode.env.clipboard.writeText(message.text);
                    vscode.window.showInformationMessage('Link copied to clipboard!');
                }
                catch (e) {
                    this.confluenceOutput?.appendLine('[Confluence] clipboard error: ' + (e instanceof Error ? e.message : String(e)));
                    vscode.window.showErrorMessage('Confluence: Could not copy link. ' + (e instanceof Error ? e.message : String(e)));
                }
            }
            else if (message.type === "confluenceSettings") {
                vscode.commands.executeCommand('workbench.action.openSettings', 'confluence');
            }
            else if (message.type === "confluenceViewCreations") {
                await this.triggerViewCreations();
            }
            else if (message.type === "confluenceExportExamples") {
                await this.handleConfluenceExportExamples();
            }
            else if (message.type === "confluenceImportExamples") {
                await this.handleConfluenceImportExamples();
            }
            else if (message.type === "confluenceIntelligenceFeedback") {
                await this.handleConfluenceIntelligenceFeedback(message.creationId, message.intelligenceScore, message.feedback);
            }
        });
        this.postModeState();
        this.postLocalState();
        this.postOnboardingState();
    }
    async handleWebviewMessage(message) {
        // dispatch is handled only in onDidReceiveMessage (single path: logging, token/response checks, renderAssistantResponse)
        if (message.type === "indexAction") {
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (!workspaceFolders || workspaceFolders.length === 0)
                return;
            const rootPath = workspaceFolders[0].uri.fsPath;
            if (message.action === "full") {
                this.postMessage({ type: "dismissIndexModal" });
                (0, indexGate_1.setIndexing)(rootPath);
                try {
                    await (0, agentClient_1.triggerIndex)((0, agentClient_1.getRagBaseUrl)(), "full", rootPath);
                    await (0, indexGate_1.triggerFullIndex)({ storageRoot: this.extensionContext.globalStorageUri.fsPath }, rootPath, (msg) => this.postMessage({ type: "commandResult", payload: msg }));
                }
                catch (error) {
                    this.postMessage({
                        type: "commandResult",
                        payload: `Indexing failed: ${error instanceof Error ? error.message : String(error)}`
                    });
                    return;
                }
                finally {
                    (0, indexGate_1.clearIndexing)(rootPath);
                }
            }
            else if (message.action === "cancel") {
                this.postMessage({ type: "dismissIndexModal" });
                this.postMessage({ type: "commandResult", payload: "Index not available; cannot answer" });
            }
        }
        else if (message.type === "openCitation") {
            const { path: filePath, start, end } = message;
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (workspaceFolders && workspaceFolders.length > 0) {
                const fullPath = vscode.Uri.joinPath(workspaceFolders[0].uri, filePath);
                const doc = await vscode.workspace.openTextDocument(fullPath);
                const editor = await vscode.window.showTextDocument(doc);
                const range = new vscode.Range(start - 1, 0, end - 1, 0);
                editor.selection = new vscode.Selection(range.start, range.end);
                editor.revealRange(range, vscode.TextEditorRevealType.InCenter);
            }
        }
        else if (message.type === "modeChange" && (0, agentClient_1.isComposerMode)(message.mode)) {
            this.modeState.setMode(message.mode);
            this.postModeState();
        }
        else if (message.type === "contextRequest") {
            this.handleContextRequest(message.action);
        }
        else if (message.type === "attachmentPick") {
            await this.handleAttachmentRequest();
        }
        else if (message.type === "localSelect" && typeof message.folder === "string") {
            await (0, storage_1.writeRootPath)(this.extensionContext, message.folder);
            this.postLocalState();
        }
        else if (message.type === "localPick") {
            const folder = await vscode.window.showOpenDialog({
                canSelectMany: false,
                canSelectFolders: true,
                canSelectFiles: false,
                openLabel: "Select Folder",
            });
            if (folder && folder.length > 0) {
                await (0, storage_1.writeRootPath)(this.extensionContext, folder[0].fsPath);
                this.postLocalState();
            }
            else {
                // Cancellation: post current state to ensure UI reflects unchanged rootPath
                this.postLocalState();
            }
        }
    }
    async handleIndexAndReport(mode) {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (!workspaceFolders || workspaceFolders.length === 0)
            return;
        const rootPath = workspaceFolders[0].uri.fsPath;
        (0, indexGate_1.setIndexing)(rootPath);
        try {
            await (0, agentClient_1.triggerIndex)((0, agentClient_1.getRagBaseUrl)(), mode, rootPath);
            await (0, indexGate_1.triggerFullIndex)({ storageRoot: this.extensionContext.globalStorageUri.fsPath }, rootPath, (msg) => this.postMessage({ type: "commandResult", payload: msg }));
            const report = await (0, agentClient_1.getIndexReport)(this.agentBaseUrl, rootPath);
            const reportHtml = this.renderIndexReport(report);
            this.postMessage({
                type: "commandResult",
                payload: reportHtml,
                isHtml: true
            });
        }
        catch (error) {
            this.postMessage({
                type: "commandResult",
                payload: `Indexing failed: ${error instanceof Error ? error.message : String(error)}`
            });
        }
        finally {
            (0, indexGate_1.clearIndexing)(rootPath);
        }
    }
    renderIndexReport(report) {
        const indexedCount = report.indexed_files?.length || 0;
        const skippedCount = report.skipped_files?.length || 0;
        const topReasons = report.top_skip_reasons?.slice(0, 3)
            .map((r) => `${r.reason} (${r.count})`)
            .join(', ') || 'None';
        return `
            <div class="index-report">
                <h3>Index Summary</h3>
                <p><b>Indexed:</b> ${indexedCount} files</p>
                <p><b>Skipped:</b> ${skippedCount} files</p>
                <p><b>Top Skip Reasons:</b> ${topReasons}</p>
            </div>
        `;
    }
    async handleAttachmentRequest() {
        if (!this.panel)
            return;
        const options = {
            canSelectMany: false,
            canSelectFiles: true,
            openLabel: "Insert reference",
        };
        const rootPath = this.getEffectiveRootPath();
        if (rootPath)
            options.defaultUri = vscode.Uri.file(rootPath);
        const selection = await vscode.window.showOpenDialog(options);
        if (selection && selection.length > 0) {
            const filePath = selection[0].fsPath;
            if (rootPath && !(0, indexGate_1.isPathInsideRoot)(rootPath, filePath)) {
                vscode.window.showErrorMessage("Select a file inside the chosen folder.");
                return;
            }
            this.postMessage({
                type: "insertText",
                text: `@file:${filePath}`,
            });
        }
    }
    renderCitation(citation) {
        const commandUri = vscode.Uri.parse(`command:citation.open?${encodeURIComponent(JSON.stringify({
            path: citation.path,
            startLine: citation.start_line,
            endLine: citation.end_line
        }))}`);
        return `<a href="${commandUri}">${citation.path} : ${citation.start_line}–${citation.end_line}</a>`;
    }
    handleContextRequest(action) {
        if (!this.panel)
            return;
        switch (action) {
            case "folder": {
                const rootPath = this.getEffectiveRootPath();
                if (!rootPath) {
                    this.postMessage({ type: "commandResult", payload: "Workspace root not available for context." });
                    this.postContextResponse(action, undefined, "no_workspace");
                    return;
                }
                this.postContextResponse(action, { root_path: rootPath });
                return;
            }
            case "selection": {
                const editor = vscode.window.activeTextEditor;
                const selection = editor?.selection;
                const selectedText = selection ? editor.document.getText(selection).trim() : "";
                if (!selectedText) {
                    this.postMessage({ type: "commandResult", payload: "INVALID_COMMAND: Select text in the editor and try again." });
                    this.postContextResponse(action, undefined, "no_selection");
                    return;
                }
                this.postContextResponse(action, { selection_text: selectedText });
                return;
            }
            case "file": {
                const editor = vscode.window.activeTextEditor;
                const filePath = editor?.document.uri.fsPath;
                if (!filePath) {
                    this.postContextResponse(action, undefined, "no_file");
                    return;
                }
                this.postContextResponse(action, { active_file_path: filePath });
                return;
            }
            default:
                return;
        }
    }
    postContextResponse(action, context, error) {
        if (!this.panel)
            return;
        this.panel.webview.postMessage({
            type: "contextResponse",
            action,
            context,
            error,
        });
    }
    async handleConfluenceNext(files) {
        if (!files.length)
            return;
        const validPaths = files.filter((p) => {
            try {
                return fs.existsSync(p);
            }
            catch {
                return false;
            }
        });
        if (validPaths.length === 0) {
            this.postMessage({ type: 'commandResult', payload: 'No valid files selected.', isConfluence: true });
            return;
        }
        let fileContents;
        try {
            fileContents = validPaths.map((p) => fs.readFileSync(p, 'utf-8'));
        }
        catch (e) {
            this.postMessage({
                type: 'commandResult',
                payload: `Failed to read files: ${e instanceof Error ? e.message : String(e)}`,
                isConfluence: true,
            });
            return;
        }
        try {
            const config = await (0, confluence_settings_1.getConfluenceConfigAsync)(this.extensionContext);
            const chat_context = {
                messages: this.conversationHistory,
                selected_text: this.getPreloadedSelection() ?? undefined,
                workspace_path: this.getEffectiveRootPath() ?? undefined,
            };
            const hasContext = !!(chat_context.messages?.length || chat_context.selected_text);
            const result = await (0, confluence_api_1.intelligentAnalyze)(config, {
                file_contents: fileContents,
                chat_context: hasContext ? chat_context : undefined,
            });
            if ('error' in result && result.error) {
                const err = result;
                const html = (0, confluenceHtml_1.getConfluenceErrorHtml)({
                    error: err.error,
                    message: err.message,
                    suggestion: err.intelligence_suggestion ?? 'Try different files or content.',
                    confidence: err.intelligence_confidence ?? 0.5,
                    fallbackAvailable: err.fallback_available ?? true,
                    actions: err.actions ?? ['Retry', 'Cancel', 'Update Settings'],
                    suggestedFiles: err.suggested_files ?? [],
                    retryContext: 'analyze',
                    retryFiles: validPaths,
                    nonce: this.getConfluenceNonce(),
                });
                this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
                return;
            }
            const analyze = result;
            const ctxSuggestions = analyze.context_suggestions;
            this.confluenceState = {
                analyzeResult: analyze,
                fileContents,
                selectedPaths: validPaths,
                contextSuggestions: ctxSuggestions ?? this.confluenceState.contextSuggestions,
            };
            const analysis = analyze.intelligence_analysis ?? {};
            const rec = analyze.intelligent_recommendation ?? {};
            const cachedSpaces = this.extensionContext.globalState.get('confluence.cachedSpaces') ?? [];
            let spacesList = await (0, confluence_api_1.fetchSpaces)(config);
            if (spacesList.length === 0) {
                spacesList = cachedSpaces
                    .filter((s) => !!s?.key)
                    .map(s => ({ key: s.key, name: s.name ?? s.key }));
                this.confluenceOutput?.appendLine("[Confluence] Using cached spaces (fetch failed or no credentials).");
            }
            else {
                await this.extensionContext.globalState.update('confluence.cachedSpaces', spacesList);
            }
            let preferredSpace = (0, confluenceSpacePreferences_1.getSpacePreference)(this.extensionContext, this.getEffectiveRootPath());
            if (!preferredSpace) {
                try {
                    preferredSpace = await (0, confluence_api_1.getPreferredSpace)(config.baseUrl, this.getEffectiveRootPath() ?? '');
                }
                catch {
                    preferredSpace = undefined;
                }
            }
            preferredSpace = preferredSpace
                ?? (0, confluenceSpacePreferences_1.getSuggestedSpaceFromProjectType)(ctxSuggestions?.project_type_label)
                ?? (spacesList[0]?.key)
                ?? "DEV";
            const spaces = spacesList
                .filter((s) => !!s?.key)
                .map(s => ({ key: s.key, name: s.name ?? s.key }));
            const cb = rec.confidence_breakdown;
            const cbVals = cb ? [cb.content_match, cb.structure_match, cb.context_match].filter((n) => typeof n === 'number') : [];
            const avgConf = cbVals.length > 0 ? cbVals.reduce((a, b) => a + b, 0) / cbVals.length : undefined;
            const analysisData = {
                content_types: analysis.content_types,
                detected_patterns: analysis.detected_patterns,
                intelligent_title: analysis.intelligent_title ?? rec.template_name ?? 'Documentation',
                template_name: rec.template_name ?? 'Documentation',
                intelligence_reason: rec.intelligence_reason ?? analysis.ai_reasoning ?? '(Matches similar successful examples)',
                intelligence_confidence: analysis.intelligence_confidence ?? avgConf,
                confidence_breakdown: rec.confidence_breakdown,
                ai_reasoning: analysis.ai_reasoning ?? rec.intelligence_reason,
                file_count: validPaths.length,
            };
            const usageCount = (0, onboarding_1.getOnboardingState)(this.extensionContext).usageCount;
            const html = (0, confluenceHtml_1.getConfluenceAnalysisHtml)(validPaths, analysisData, this.getConfluenceNonce(), usageCount, {
                preferredSpace,
                spaces: spaces.length > 0 ? spaces : undefined,
            });
            this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
        }
        catch (e) {
            const msg = e instanceof Error ? e.message : String(e);
            const html = (0, confluenceHtml_1.getConfluenceErrorHtml)({
                error: 'analysis_failed',
                message: msg,
                suggestion: 'Check backend is running and Confluence settings are configured.',
                confidence: 0.5,
                fallbackAvailable: true,
                actions: ['Retry', 'Update Settings', 'Cancel'],
                retryContext: 'analyze',
                retryFiles: validPaths,
                nonce: this.getConfluenceNonce(),
            });
            this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
        }
    }
    async handleConfluenceCreate(title, space) {
        const effectiveTitle = (title && title.trim()) || this.confluenceState.lastTitle || 'Documentation';
        const effectiveSpace = (space && space.trim()) || this.confluenceState.lastSpace || 'DEV';
        this.confluenceOutput?.appendLine(`[Confluence] handleConfluenceCreate entered: title="${effectiveTitle}" space="${effectiveSpace}"`);
        // #region agent log
        debugLog({ location: 'ChatPanelViewProvider.ts:handleConfluenceCreate', message: 'handler entered', data: { title, space }, hypothesisId: 'H3' });
        // #endregion
        this.confluenceState.lastTitle = effectiveTitle;
        this.confluenceState.lastSpace = effectiveSpace;
        let { fileContents } = this.confluenceState;
        if (!fileContents?.length && this.confluenceState.selectedPaths?.length) {
            try {
                const validPaths = this.confluenceState.selectedPaths.filter((p) => {
                    try {
                        return fs.existsSync(p);
                    }
                    catch {
                        return false;
                    }
                });
                if (validPaths.length) {
                    fileContents = validPaths.map((p) => fs.readFileSync(p, 'utf-8'));
                    this.confluenceState.fileContents = fileContents;
                }
            }
            catch {
                // ignore re-read errors
            }
        }
        if (!fileContents?.length) {
            const html = (0, confluenceHtml_1.getConfluenceErrorHtml)({
                error: 'no_analysis_data',
                message: 'No file content to publish.',
                suggestion: 'Click "Save to Confluence", select files, then click Next to analyze. After that, click Create Perfect Page.',
                confidence: 0,
                fallbackAvailable: true,
                actions: ['Cancel'],
                retryContext: 'create',
                nonce: this.getConfluenceNonce(),
            });
            this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
            return;
        }
        const progressUpdateId = 'msg-progress-' + Date.now();
        const progressHtml = (0, confluenceHtml_1.getConfluenceProgressHtml)(this.getConfluenceNonce()).replace('data-confluence-id="msg-progress"', 'data-confluence-id="' + progressUpdateId + '"');
        this.postMessage({ type: 'commandResult', payload: progressHtml, isHtml: true, isConfluence: true });
        try {
            const config = await (0, confluence_settings_1.getConfluenceConfigAsync)(this.extensionContext);
            if (!config.auth || config.auth.length < 2) {
                const html = (0, confluenceHtml_1.getConfluenceErrorHtml)({
                    error: 'missing_credentials',
                    message: 'Confluence credentials not set.',
                    suggestion: 'Open Settings (Confluence: Configure Settings), set Confluence URL, email, and store your API token.',
                    confidence: 0,
                    fallbackAvailable: false,
                    actions: ['Update Settings', 'Cancel'],
                    retryContext: 'create',
                    nonce: this.getConfluenceNonce(),
                });
                this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true, updateId: progressUpdateId });
                return;
            }
            this.confluenceOutput?.appendLine('[Confluence] Calling intelligentCreate API');
            const rec = this.confluenceState.analyzeResult?.intelligent_recommendation;
            const intelligence_context = {
                suggested_title: effectiveTitle,
                title_override: effectiveTitle,
            };
            if (rec?.template_id)
                intelligence_context.template_id = rec.template_id;
            if (rec?.template_name)
                intelligence_context.template_name = rec.template_name;
            const result = await (0, confluence_api_1.intelligentCreate)(config, {
                files: fileContents,
                intelligent_mode: true,
                auto_title: false,
                space: effectiveSpace,
                intelligence_context,
                base_url: config.confluenceInstanceUrl || undefined,
                auth: config.auth ?? undefined,
            });
            if ('error' in result && result.error) {
                const err = result;
                this.confluenceOutput?.appendLine(`[Confluence] intelligentCreate error (API): ${err.message ?? err.error}`);
                vscode.window.showErrorMessage(`Confluence: Create failed — ${err.message ?? err.error}`);
                const html = (0, confluenceHtml_1.getConfluenceErrorHtml)({
                    error: err.error,
                    message: err.message,
                    suggestion: err.intelligence_suggestion ?? 'Check Confluence settings, network, and credentials.',
                    confidence: err.intelligence_confidence ?? 0.5,
                    fallbackAvailable: err.fallback_available ?? true,
                    actions: err.actions ?? ['Retry', 'Cancel', 'Update Settings'],
                    retryContext: 'create',
                    nonce: this.getConfluenceNonce(),
                });
                this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true, updateId: progressUpdateId });
                return;
            }
            this.confluenceOutput?.appendLine('[Confluence] intelligentCreate success');
            vscode.window.showInformationMessage(`Confluence: Page "${result.title ?? effectiveTitle}" created.`);
            (0, onboarding_1.incrementUsage)(this.extensionContext);
            this.postOnboardingState();
            const workspace = this.getEffectiveRootPath() ?? 'default';
            (0, agentClient_1.trackConfluenceUsage)(this.agentBaseUrl, { feature: 'create_success', workspace }).catch(() => { });
            const usageCount = (0, onboarding_1.getOnboardingState)(this.extensionContext).usageCount;
            await (0, confluenceSpacePreferences_1.setSpacePreference)(this.extensionContext, this.getEffectiveRootPath(), effectiveSpace);
            const successHtml = (0, confluenceHtml_1.getConfluenceSuccessHtml)(usageCount, {
                pageUrl: result.url,
                title: result.title ?? effectiveTitle,
                space: result.space ?? effectiveSpace,
                learning: result.ai_learning_applied ?? false,
                examplesCount: result.examples_count,
            }, this.getConfluenceNonce());
            this.postMessage({ type: 'commandResult', payload: successHtml, isHtml: true, isConfluence: true, updateId: progressUpdateId });
            const newCreation = { url: result.url, title: result.title ?? effectiveTitle, space: result.space ?? effectiveSpace, creationId: result.id, createdAt: Date.now() };
            const existing = this.extensionContext.globalState.get('confluence.intelligentCreations') ?? [];
            const updated = [newCreation, ...existing].slice(0, 50);
            await this.extensionContext.globalState.update('confluence.intelligentCreations', updated);
            // #region agent log
            debugLog({ location: 'ChatPanelViewProvider.ts:handleConfluenceCreate', message: 'handler success', data: {}, hypothesisId: 'H3' });
            // #endregion
        }
        catch (e) {
            const msg = e instanceof Error ? e.message : String(e);
            this.confluenceOutput?.appendLine(`[Confluence] intelligentCreate error: ${msg}`);
            vscode.window.showErrorMessage(`Confluence: Create failed — ${msg}`);
            // #region agent log
            debugLog({ location: 'ChatPanelViewProvider.ts:handleConfluenceCreate', message: 'handler error', data: { error: msg }, hypothesisId: 'H3' });
            // #endregion
            const html = (0, confluenceHtml_1.getConfluenceErrorHtml)({
                error: 'create_failed',
                message: msg,
                suggestion: 'Check Confluence settings, network, and credentials.',
                confidence: 0.5,
                fallbackAvailable: true,
                actions: ['Retry', 'Update Settings', 'Cancel'],
                retryContext: 'create',
                nonce: this.getConfluenceNonce(),
            });
            this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true, updateId: progressUpdateId });
        }
    }
    async handleSaveLastSummaryToConfluence() {
        if (!this.lastRagSummaryPlainText) {
            this.postMessage({ type: "commandResult", payload: "No summary to save. Ask for a codebase summary first (e.g. 'Analyze this codebase and give its summary'), then say 'Save this summary to Confluence'.", isHtml: false });
            return;
        }
        try {
            const config = await (0, confluence_settings_1.getConfluenceConfigAsync)(this.extensionContext);
            if (!config.auth || config.auth.length < 2) {
                const html = (0, confluenceHtml_1.getConfluenceErrorHtml)({
                    error: 'missing_credentials',
                    message: 'Confluence credentials not set.',
                    suggestion: 'Open Settings (Confluence: Configure Settings), set Confluence URL, email, and store your API token.',
                    confidence: 0,
                    fallbackAvailable: false,
                    actions: ['Update Settings', 'Cancel'],
                    retryContext: 'create',
                    nonce: this.getConfluenceNonce(),
                });
                this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
                return;
            }
            const folderName = this.getEffectiveRootPath() ? path.basename(this.getEffectiveRootPath()) : "Workspace";
            const title = "Codebase Summary – " + folderName;
            let space = (0, confluenceSpacePreferences_1.getSpacePreference)(this.extensionContext, this.getEffectiveRootPath());
            if (!space) {
                space = await (0, confluence_api_1.getPreferredSpace)(config.baseUrl, this.getEffectiveRootPath() ?? "");
            }
            const result = await (0, confluence_api_1.intelligentCreate)(config, {
                content: this.lastRagSummaryPlainText,
                intelligent_mode: true,
                auto_title: false,
                space,
                intelligence_context: { suggested_title: title, title_override: title },
                base_url: config.confluenceInstanceUrl || undefined,
                auth: config.auth ?? undefined,
            });
            if ('error' in result && result.error) {
                const err = result;
                const html = (0, confluenceHtml_1.getConfluenceErrorHtml)({
                    error: err.error,
                    message: err.message,
                    suggestion: err.intelligence_suggestion ?? 'Check Confluence settings, network, and credentials.',
                    confidence: err.intelligence_confidence ?? 0.5,
                    fallbackAvailable: err.fallback_available ?? true,
                    actions: err.actions ?? ['Retry', 'Cancel', 'Update Settings'],
                    retryContext: 'create',
                    nonce: this.getConfluenceNonce(),
                });
                this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
                return;
            }
            this.lastRagSummaryPlainText = undefined;
            const pageUrl = result.url;
            const pageTitle = result.title ?? title;
            const successPayload = pageUrl
                ? `Confluence page created: <a href="${pageUrl}" data-href="${pageUrl}">${pageTitle}</a>`
                : "Confluence page created: " + pageTitle;
            this.postMessage({ type: "commandResult", payload: successPayload, isHtml: true });
        }
        catch (e) {
            const msg = e instanceof Error ? e.message : String(e);
            const html = (0, confluenceHtml_1.getConfluenceErrorHtml)({
                error: 'create_failed',
                message: msg,
                suggestion: 'Check Confluence settings, network, and credentials.',
                confidence: 0.5,
                fallbackAvailable: true,
                actions: ['Retry', 'Update Settings', 'Cancel'],
                retryContext: 'create',
                nonce: this.getConfluenceNonce(),
            });
            this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
        }
    }
    async handleConfluenceIntelligenceFeedback(creationId, intelligenceScore, feedback) {
        if (!this.panel || !creationId || typeof intelligenceScore !== 'number' || intelligenceScore < 1 || intelligenceScore > 5)
            return;
        try {
            const config = await (0, confluence_settings_1.getConfluenceConfigAsync)(this.extensionContext);
            const result = await (0, confluence_api_1.postIntelligenceFeedback)(config, {
                creation_id: creationId,
                intelligence_score: intelligenceScore,
                feedback: feedback || undefined,
            });
            const im = result.intelligence_metrics;
            const acc = im?.template_selection_accuracy ?? im?.template_selection_intelligence;
            const improvedMsg = typeof acc === 'number'
                ? `Intelligence Improved: Template matching accuracy increased to ${acc}%`
                : 'Intelligence Improved: Thank you for your feedback.';
            const html = `<div class="confluence-card" style="border: 1px solid var(--vscode-testing-iconPassed); border-radius: 8px; padding: 12px 16px; background: var(--vscode-editor-background); max-width: 400px;"><div style="display: flex; align-items: center; gap: 8px;"><span style="font-size: 18px;">🎓</span><strong>${improvedMsg}</strong></div></div>`;
            this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
            await this.triggerViewCreations();
        }
        catch {
            this.postMessage({ type: 'commandResult', payload: 'Feedback could not be submitted. Please try again.', isConfluence: true });
        }
    }
    async handleConfluenceExportExamples() {
        if (!this.panel)
            return;
        try {
            const config = await (0, confluence_settings_1.getConfluenceConfigAsync)(this.extensionContext);
            const projectPath = this.getEffectiveRootPath() ?? undefined;
            const jsonStr = await (0, confluence_api_1.exportExamples)(config, { project_path: projectPath });
            const dateStr = new Date().toISOString().slice(0, 10);
            const defaultUri = projectPath ? vscode.Uri.file(path.join(projectPath, `intelligence-examples-${dateStr}.json`)) : undefined;
            const saveUri = await vscode.window.showSaveDialog({
                defaultUri,
                filters: [{ name: 'JSON', extensions: ['json'] }],
                saveLabel: 'Export Examples',
            });
            if (!saveUri)
                return;
            fs.writeFileSync(saveUri.fsPath, jsonStr, 'utf-8');
            const msg = `Export complete. Saved to ${saveUri.fsPath}`;
            const html = `<div class="confluence-card" style="border: 1px solid var(--vscode-testing-iconPassed); border-radius: 8px; padding: 12px 16px; background: var(--vscode-editor-background); max-width: 400px;"><div style="display: flex; align-items: center; gap: 8px;"><span style="font-size: 18px;">📦</span><strong>${msg.replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;')}</strong></div></div>`;
            this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
        }
        catch (e) {
            const errMsg = e instanceof Error ? e.message : String(e);
            const html = (0, confluenceHtml_1.getConfluenceErrorHtml)({
                error: 'export_failed',
                message: errMsg,
                suggestion: 'Check Confluence settings and ensure the agent backend is running.',
                confidence: 0.5,
                fallbackAvailable: false,
                actions: ['Retry', 'Update Settings', 'Cancel'],
                retryContext: 'create',
                nonce: this.getConfluenceNonce(),
            });
            this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
        }
    }
    async handleConfluenceImportExamples() {
        if (!this.panel)
            return;
        const files = await vscode.window.showOpenDialog({
            canSelectMany: false,
            canSelectFolders: false,
            canSelectFiles: true,
            filters: [{ name: 'JSON', extensions: ['json'] }],
            openLabel: 'Import Intelligence Examples',
        });
        if (!files || files.length === 0)
            return;
        try {
            const raw = fs.readFileSync(files[0].fsPath, 'utf-8');
            const parsed = JSON.parse(raw);
            const config = await (0, confluence_settings_1.getConfluenceConfigAsync)(this.extensionContext);
            const result = await (0, confluence_api_1.importExamples)(config, parsed);
            const msg = `Intelligence Examples Imported: ${result.importedCount} new examples learned`;
            const html = `<div class="confluence-card" style="border: 1px solid var(--vscode-testing-iconPassed); border-radius: 8px; padding: 12px 16px; background: var(--vscode-editor-background); max-width: 400px;"><div style="display: flex; align-items: center; gap: 8px;"><span style="font-size: 18px;">📦</span><strong>${msg}</strong></div></div>`;
            this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
        }
        catch (e) {
            const errMsg = e instanceof Error ? e.message : String(e);
            const html = (0, confluenceHtml_1.getConfluenceErrorHtml)({
                error: 'import_failed',
                message: errMsg,
                suggestion: 'Ensure the file matches the PRD export format. See confluence_data/examples/export_format.json.',
                confidence: 0.5,
                fallbackAvailable: false,
                actions: ['Retry', 'Update Settings', 'Cancel'],
                retryContext: 'create',
                nonce: this.getConfluenceNonce(),
            });
            this.postMessage({ type: 'commandResult', payload: html, isHtml: true, isConfluence: true });
        }
    }
    getEffectiveRootPath() {
        return (0, storage_1.readRootPath)(this.extensionContext) ?? this.getWorkspaceRootPath();
    }
    getWorkspaceRootPath() {
        const folders = vscode.workspace.workspaceFolders;
        if (folders && folders.length > 0)
            return folders[0].uri.fsPath;
        if (vscode.workspace.workspaceFile)
            return path.dirname(vscode.workspace.workspaceFile.fsPath);
        return undefined;
    }
    postMessage(message) {
        if (!this.panel)
            return;
        if (message.type === 'commandResult' && message.payload && !message.isConfluence) {
            const payload = typeof message.payload === 'string' ? message.payload : JSON.stringify(message.payload);
            this.pushToConversationHistory(payload);
        }
        this.panel.webview.postMessage(message);
    }
    postModeState() {
        if (!this.panel)
            return;
        this.panel.webview.postMessage({
            type: "modeState",
            mode: this.modeState.getMode(),
        });
    }
    postLocalState() {
        if (!this.panel)
            return;
        this.panel.webview.postMessage({
            type: "localState",
            rootPath: this.getEffectiveRootPath(),
            recentFolders: (0, storage_1.readRecentFolders)(this.extensionContext),
        });
    }
    postOnboardingState() {
        if (!this.panel)
            return;
        const state = (0, onboarding_1.getOnboardingState)(this.extensionContext);
        this.panel.webview.postMessage({
            type: "onboardingState",
            tooltipShown: state.tooltipShown,
            usageCount: state.usageCount,
        });
    }
    getNonce() {
        const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
        let text = "";
        for (let i = 0; i < 16; i++) {
            text += possible.charAt(Math.floor(Math.random() * possible.length));
        }
        return text;
    }
    /** Nonce used in Confluence HTML must match panel CSP; use panel nonce when available. */
    getConfluenceNonce() {
        return this.panelNonce ?? this.getNonce();
    }
    isSaveToConfluenceIntent(normalized) {
        const phrases = [
            "save this to confluence",
            "save this summary",
            "save this summary in a confluence page",
            "create a confluence page with this",
            "put this in confluence",
            "publish this to confluence",
        ];
        return phrases.some((phrase) => normalized.includes(phrase));
    }
    isSummaryIntent(normalized) {
        const phrases = [
            "analyze this codebase",
            "codebase summary",
            "summarize this project",
            "project summary",
            "give me a summary of this code",
            "what is this project about",
        ];
        return phrases.some((phrase) => normalized.includes(phrase));
    }
    buildExtraContext() {
        const rootPath = this.getEffectiveRootPath();
        if (!rootPath) {
            return undefined;
        }
        return { root_path: rootPath };
    }
}
exports.ChatPanelViewProvider = ChatPanelViewProvider;
