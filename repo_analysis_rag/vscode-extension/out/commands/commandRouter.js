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
exports.CommandRouter = void 0;
exports.parseSlashCommand = parseSlashCommand;
exports.handleToolsSlashCommand = handleToolsSlashCommand;
const vscode = __importStar(require("vscode"));
const slashCommands_1 = require("./slashCommands");
const agentClient_1 = require("../services/agentClient");
const indexGate_1 = require("../services/indexGate");
const slashCommands_2 = require("./slashCommands");
const storage_1 = require("../services/storage");
function describeCommand(command) {
    switch (command.kind) {
        case "index":
            return `Indexing started: ${command.mode} scan`;
        case "overview":
            return "Overview: Folder structure and key files...";
        case "search":
            return `Searching for ${command.query}`;
        case "doctor":
            return "Running system checks...";
        case "autoindex":
            return command.enabled ? "Auto-indexing enabled" : "Auto-indexing disabled";
        case "ask":
            return `Asking the system: ${command.question}`;
        case "confluenceDocumentProject":
            return "Intelligently scanning project for documentation...";
        default:
            return "INVALID_COMMAND";
    }
}
/**
 * Parses and executes a slash command from the user input.
 * Uses a deterministic, registry-based approach.
 * @param input The raw input string starting with /
 * @param context VSCode extension context
 * @returns The result message or modal trigger
 */
async function parseSlashCommand(input, context) {
    const trimmedInput = input.trim();
    if (!trimmedInput.startsWith('/')) {
        return { type: 'commandResult', payload: 'INVALID_COMMAND' };
    }
    const gatedCommands = ['/ask', '/overview', '/search', '/index report'];
    const isGated = gatedCommands.some(cmd => trimmedInput === cmd || trimmedInput.startsWith(cmd + ' '));
    if (isGated) {
        const workspaceFolders = vscode.workspace.workspaceFolders;
        if (workspaceFolders && workspaceFolders.length > 0) {
            const rootPath = workspaceFolders[0].uri.fsPath;
            const storageRoot = context.globalStorageUri.fsPath;
            if ((0, indexGate_1.isIndexing)(rootPath)) {
                return { type: 'commandResult', payload: 'Indexing in progress...' };
            }
            const exists = await (0, indexGate_1.checkIndexExists)({ storageRoot }, rootPath);
            if (!exists) {
                return { type: 'showIndexModal' };
            }
        }
    }
    // Commands that support arguments
    const commandsWithArgs = ['/search', '/ask'];
    for (const commandKey of Object.keys(slashCommands_1.slashCommandRegistry)) {
        if (commandsWithArgs.includes(commandKey)) {
            // For /search and /ask, we match the prefix and treat the rest as args
            if (trimmedInput === commandKey || trimmedInput.startsWith(commandKey + ' ')) {
                const args = trimmedInput.slice(commandKey.length).trim();
                const result = slashCommands_1.slashCommandRegistry[commandKey](args);
                // For /ask and /search, wrap in assistantResponse envelope for rendering
                if (commandKey === '/ask' || commandKey === '/search') {
                    return {
                        type: 'assistantResponse',
                        payload: {
                            mode: 'rag',
                            confidence: 'found',
                            answer: result,
                            citations: []
                        }
                    };
                }
                return { type: 'commandResult', payload: result };
            }
        }
        else {
            // For all other commands, we require an exact match
            if (trimmedInput === commandKey) {
                if (commandKey === '/autoindex on' || commandKey === '/autoindex off') {
                    const rootPath = (0, storage_1.readRootPath)(context);
                    if (!rootPath) {
                        return { type: 'commandResult', payload: 'Root path not selected.' };
                    }
                    const enabled = commandKey === '/autoindex on';
                    await (0, storage_1.writeAutoIndex)(context, enabled);
                    return { type: 'commandResult', payload: enabled ? 'Auto-index enabled.' : 'Auto-index disabled.' };
                }
                const result = slashCommands_1.slashCommandRegistry[commandKey]('');
                // For /overview and /index report, wrap in assistantResponse envelope
                if (commandKey === '/overview' || commandKey === '/index report' || commandKey === '/doctor') {
                    return {
                        type: 'assistantResponse',
                        payload: {
                            mode: commandKey === '/doctor' ? 'tools' : 'rag',
                            confidence: 'found',
                            answer: result,
                            citations: []
                        }
                    };
                }
                return { type: 'commandResult', payload: result };
            }
        }
    }
    return { type: 'commandResult', payload: 'INVALID_COMMAND' };
}
function handleToolsSlashCommand(input) {
    const parsed = (0, slashCommands_2.parseSlashCommandInstruction)(input);
    if (!parsed.success) {
        return "INVALID_COMMAND";
    }
    return describeCommand(parsed.command);
}
class CommandRouter {
    context;
    onResult;
    ragLog;
    constructor(context, onResult, ragLog) {
        this.context = context;
        this.onResult = onResult;
        this.ragLog = ragLog;
    }
    postResult(payload, isHtml = false) {
        this.onResult({ type: "commandResult", payload, isHtml });
    }
    async handleCommand(input, extraContext) {
        const trimmed = input.trim();
        if (trimmed.startsWith('/')) {
            const result = await parseSlashCommand(trimmed, this.context);
            if (result.type === 'commandResult' && result.payload === 'INVALID_COMMAND') {
                this.onResult({ type: 'commandResult', payload: 'INVALID_COMMAND' });
                return;
            }
            this.onResult(result);
        }
        else {
            await this.autoRouteInput(trimmed, extraContext);
        }
    }
    async autoRouteInput(input, extraContext) {
        const trimmed = input.trim();
        const overviewKeywords = ['overview', 'structure', 'languages'];
        const searchKeywords = ['search', 'find', 'where', 'locate'];
        const baseUrl = (0, agentClient_1.getRagBaseUrl)();
        let endpoint;
        let response;
        if (overviewKeywords.some(k => trimmed.toLowerCase().includes(k))) {
            endpoint = "/overview";
            this.ragLog?.appendLine(`[RAG] (Auto) Connected to server: ${baseUrl}`);
            this.ragLog?.appendLine(`[RAG] (Auto) Sending request: POST ${baseUrl}${endpoint}`);
            response = await (0, agentClient_1.overview)(trimmed, extraContext);
        }
        else if (searchKeywords.some(k => trimmed.toLowerCase().includes(k))) {
            endpoint = "/search";
            this.ragLog?.appendLine(`[RAG] (Auto) Connected to server: ${baseUrl}`);
            this.ragLog?.appendLine(`[RAG] (Auto) Sending request: POST ${baseUrl}${endpoint}`);
            response = await (0, agentClient_1.search)(trimmed, extraContext);
        }
        else {
            endpoint = "/ask";
            this.ragLog?.appendLine(`[RAG] (Auto) Connected to server: ${baseUrl}`);
            this.ragLog?.appendLine(`[RAG] (Auto) Sending request: POST ${baseUrl}${endpoint}`);
            response = await (0, agentClient_1.ask)(trimmed, extraContext);
        }
        this.ragLog?.appendLine(`[RAG] (Auto) Response status: ${response.status} ${response.statusText}`);
        try {
            const result = await response.json();
            if (!response.ok && (result?.error_code === "INVALID_TOKEN" || result?.error === "INVALID_TOKEN")) {
                this.ragLog?.appendLine("[RAG] (Auto) Error: INVALID_TOKEN (missing or invalid X-LOCAL-TOKEN).");
                this.onResult({
                    type: "commandResult",
                    payload: "Error: RAG token missing or invalid. Start the backend and ensure the token file exists, then retry.",
                });
                return;
            }
            if (!response.ok) {
                this.ragLog?.appendLine(`[RAG] (Auto) Server error: ${typeof result?.detail === "string" ? result.detail : JSON.stringify(result).slice(0, 300)}`);
            }
            else {
                this.ragLog?.appendLine(`[RAG] (Auto) Response OK: answer length=${String(result?.answer ?? "").length}, citations=${result?.citations?.length ?? 0}`);
            }
            this.onResult({
                type: "commandResult",
                payload: result.answer || JSON.stringify(result)
            });
        }
        catch (error) {
            const errMsg = error instanceof Error ? error.message : String(error);
            this.ragLog?.appendLine(`[RAG] (Auto) Request failed: ${errMsg}`);
            throw error;
        }
    }
    async handleIndexAction(action) {
        if (action === "full" || action === "cancel") {
            this.postResult(`Index action: ${action}`);
        }
    }
    async route(options) {
        const { text, mode, extraContext } = options;
        if (mode === "RAG" && !text.startsWith("/")) {
            try {
                const response = await (0, agentClient_1.askWithOverride)(text, "rag", extraContext);
                const result = await response.json();
                if (!response.ok && (result?.error_code === "INVALID_TOKEN" || result?.error === "INVALID_TOKEN")) {
                    this.onResult({
                        type: "commandResult",
                        payload: "Error: RAG token missing or invalid. Start the backend and ensure the token file exists, then retry.",
                    });
                    return;
                }
                this.onResult({
                    type: "commandResult",
                    payload: result.answer || JSON.stringify(result),
                });
            }
            catch (error) {
                this.onResult({
                    type: "commandResult",
                    payload: `Error: ${error instanceof Error ? error.message : String(error)}`,
                });
            }
        }
        else if (mode === "Auto" && !text.startsWith("/")) {
            await this.autoRouteInput(text, extraContext);
        }
        else {
            await this.handleCommand(text, extraContext);
        }
    }
    handleToolsSlashCommand(input) {
        return handleToolsSlashCommand(input);
    }
}
exports.CommandRouter = CommandRouter;
