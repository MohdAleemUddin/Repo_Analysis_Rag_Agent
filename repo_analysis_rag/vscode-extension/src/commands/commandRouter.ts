import * as vscode from 'vscode';
import { slashCommandRegistry } from './slashCommands';
import { overview, search, ask, askWithOverride } from '../services/agentClient';
import { checkIndexExists, isIndexing } from '../services/indexGate';
import { parseSlashCommandInstruction, SlashCommandInstruction } from "./slashCommands";
import { readRootPath, writeAutoIndex } from '../services/storage';

export interface CommandResultMessage {
    type: 'commandResult' | 'showIndexModal' | 'dismissIndexModal' | 'assistantResponse';
    payload?: any;
    isHtml?: boolean;
}

function describeCommand(command: SlashCommandInstruction): string {
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
export async function parseSlashCommand(
    input: string,
    context: vscode.ExtensionContext
): Promise<CommandResultMessage> {
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
            
            if (isIndexing(rootPath)) {
                return { type: 'commandResult', payload: 'Indexing in progress...' };
            }

            const exists = await checkIndexExists({ storageRoot }, rootPath);
            if (!exists) {
                return { type: 'showIndexModal' };
            }
        }
    }

    // Commands that support arguments
    const commandsWithArgs = ['/search', '/ask'];

    for (const commandKey of Object.keys(slashCommandRegistry)) {
        if (commandsWithArgs.includes(commandKey)) {
            // For /search and /ask, we match the prefix and treat the rest as args
            if (trimmedInput === commandKey || trimmedInput.startsWith(commandKey + ' ')) {
                const args = trimmedInput.slice(commandKey.length).trim();
                const result = slashCommandRegistry[commandKey](args);
                
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
        } else {
            // For all other commands, we require an exact match
            if (trimmedInput === commandKey) {
                if (commandKey === '/autoindex on' || commandKey === '/autoindex off') {
                    const rootPath = readRootPath(context);
                    if (!rootPath) {
                        return { type: 'commandResult', payload: 'Root path not selected.' };
                    }
                    const enabled = commandKey === '/autoindex on';
                    await writeAutoIndex(context, enabled);
                    return { type: 'commandResult', payload: enabled ? 'Auto-index enabled.' : 'Auto-index disabled.' };
                }

                const result = slashCommandRegistry[commandKey]('');
                
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

export function handleToolsSlashCommand(input: string): string {
    const parsed = parseSlashCommandInstruction(input);
    if (!parsed.success) {
        return "INVALID_COMMAND";
    }
    return describeCommand(parsed.command);
}

export class CommandRouter {
    constructor(
        private readonly context: vscode.ExtensionContext,
        private readonly onResult: (message: CommandResultMessage) => void
    ) {}

    private postResult(payload: string, isHtml: boolean = false) {
        this.onResult({ type: "commandResult", payload, isHtml });
    }

    public async handleCommand(input: string, extraContext?: any): Promise<void> {
        const trimmed = input.trim();
        if (trimmed.startsWith('/')) {
            const result = await parseSlashCommand(trimmed, this.context);
            if (result.type === 'commandResult' && result.payload === 'INVALID_COMMAND') {
                this.onResult({ type: 'commandResult', payload: 'INVALID_COMMAND' });
                return;
            }
            this.onResult(result);
        } else {
            await this.autoRouteInput(trimmed, extraContext);
        }
    }

    public async autoRouteInput(input: string, extraContext?: any): Promise<void> {
        const trimmed = input.trim();
        const overviewKeywords = ['overview', 'structure', 'languages'];
        const searchKeywords = ['search', 'find', 'where', 'locate'];

        let response: any;
        if (overviewKeywords.some(k => trimmed.toLowerCase().includes(k))) {
            response = await overview(trimmed, extraContext);
        } else if (searchKeywords.some(k => trimmed.toLowerCase().includes(k))) {
            response = await search(trimmed, extraContext);
        } else {
            response = await ask(trimmed, extraContext);
        }

        const result = await response.json() as any;
        this.onResult({
            type: "commandResult",
            payload: result.answer || JSON.stringify(result)
        });
    }

    public async handleIndexAction(action: string): Promise<void> {
        if (action === "full" || action === "cancel") {
            this.postResult(`Index action: ${action}`);
        }
    }

    public async route(options: { text: string; mode: string; extraContext?: any }): Promise<void> {
        const { text, mode, extraContext } = options;
        if (mode === "RAG" && !text.startsWith("/")) {
            try {
                const response = await askWithOverride(text, "rag", extraContext);
                const result = await response.json();
                this.onResult({
                    type: "commandResult",
                    payload: result.answer || JSON.stringify(result),
                });
            } catch (error) {
                this.onResult({
                    type: "commandResult",
                    payload: `Error: ${error instanceof Error ? error.message : String(error)}`,
                });
            }
        } else if (mode === "Auto" && !text.startsWith("/")) {
            await this.autoRouteInput(text, extraContext);
        } else {
            await this.handleCommand(text, extraContext);
        }
    }

    public handleToolsSlashCommand(input: string): string {
        return handleToolsSlashCommand(input);
    }
}
