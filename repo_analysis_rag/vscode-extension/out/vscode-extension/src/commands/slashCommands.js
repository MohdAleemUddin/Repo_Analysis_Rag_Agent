"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.slashCommandRegistry = void 0;
exports.parseSlashCommandInstruction = parseSlashCommandInstruction;
/**
 * Deterministic registry of supported slash commands.
 * ONLY supported commands are included here.
 */
exports.slashCommandRegistry = {
    '/index full': (args) => {
        return 'Indexing started: full scan';
    },
    '/index incremental': (args) => {
        return 'Indexing started: incremental scan';
    },
    '/index report': (args) => {
        return 'Generating index report...';
    },
    '/overview': (args) => {
        return 'Overview: Folder structure and key files...';
    },
    '/search': (args) => {
        return `Searching for ${args}`;
    },
    '/doctor': (args) => {
        return 'Running system checks...';
    },
    '/autoindex on': (args) => {
        return 'Auto-index enabled.';
    },
    '/autoindex off': (args) => {
        return 'Auto-index disabled.';
    },
    '/ask': (args) => {
        return `Asking the system: ${args}`;
    },
    '/confluence document-project': (args) => {
        return 'CONFLUENCE_DOCUMENT_PROJECT';
    },
};
function parseSlashCommandInstruction(input) {
    const trimmed = input.trim();
    if (!trimmed.startsWith("/")) {
        return { success: false, reason: "INVALID_COMMAND" };
    }
    const commandsWithArgs = ["/search", "/ask"];
    for (const commandKey of Object.keys(exports.slashCommandRegistry)) {
        if (commandsWithArgs.includes(commandKey)) {
            if (trimmed === commandKey || trimmed.startsWith(commandKey + " ")) {
                const args = trimmed.slice(commandKey.length).trim();
                if (commandKey === "/search" && !args)
                    continue;
                if (commandKey === "/ask" && !args)
                    continue;
                return {
                    success: true,
                    command: commandKey === "/search"
                        ? { kind: "search", query: args }
                        : { kind: "ask", question: args }
                };
            }
        }
        else if (trimmed === commandKey) {
            if (commandKey === "/overview")
                return { success: true, command: { kind: "overview" } };
            if (commandKey === "/doctor")
                return { success: true, command: { kind: "doctor" } };
            if (commandKey === "/index full")
                return { success: true, command: { kind: "index", mode: "full" } };
            if (commandKey === "/index incremental")
                return { success: true, command: { kind: "index", mode: "incremental" } };
            if (commandKey === "/index report")
                return { success: true, command: { kind: "index", mode: "report" } };
            if (commandKey === "/autoindex on")
                return { success: true, command: { kind: "autoindex", enabled: true } };
            if (commandKey === "/autoindex off")
                return { success: true, command: { kind: "autoindex", enabled: false } };
            if (commandKey === "/confluence document-project")
                return { success: true, command: { kind: "confluenceDocumentProject" } };
        }
    }
    return { success: false, reason: "INVALID_COMMAND" };
}
