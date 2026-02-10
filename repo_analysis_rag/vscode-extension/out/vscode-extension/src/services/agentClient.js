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
exports.DEFAULT_AGENT_BASE_URL = void 0;
exports.isComposerMode = isComposerMode;
exports.getTokenFilePath = getTokenFilePath;
exports.readAgentToken = readAgentToken;
exports.readComposerMode = readComposerMode;
exports.writeComposerMode = writeComposerMode;
exports.authenticatedFetch = authenticatedFetch;
exports.getIndexReport = getIndexReport;
exports.triggerIndex = triggerIndex;
exports.fetchHealth = fetchHealth;
exports.startHealthPolling = startHealthPolling;
exports.stopHealthPolling = stopHealthPolling;
exports.sendMessageToAgent = sendMessageToAgent;
exports.ask = ask;
exports.overview = overview;
exports.askWithOverride = askWithOverride;
exports.search = search;
exports.trackConfluenceUsage = trackConfluenceUsage;
const fs = __importStar(require("fs"));
const os = __importStar(require("os"));
const path = __importStar(require("path"));
const url_1 = require("url");
const TOKEN_FILENAME = "agent_token.txt";
const MODE_STATE_FILENAME = "composer_mode.json";
const COMPOSER_MODES = ["auto", "rag", "tools"];
exports.DEFAULT_AGENT_BASE_URL = (process.env.OFFLINE_RAG_AGENT_URL?.trim() || "http://127.0.0.1:8000");
function buildAgentUrl(endpoint) {
    return new url_1.URL(endpoint, exports.DEFAULT_AGENT_BASE_URL).toString();
}
function getIndexDir() {
    const envDir = process.env.RAG_INDEX_DIR;
    if (envDir && envDir.trim()) {
        return envDir;
    }
    const userProfile = process.env.USERPROFILE || os.homedir();
    return path.join(userProfile, ".offline_rag_index");
}
function getModeStateFilePath() {
    return path.join(getIndexDir(), MODE_STATE_FILENAME);
}
function isComposerMode(value) {
    return (typeof value === "string" &&
        COMPOSER_MODES.includes(value));
}
function getTokenFilePath() {
    return path.join(getIndexDir(), TOKEN_FILENAME);
}
function readAgentToken() {
    const tokenPath = getTokenFilePath();
    try {
        const token = fs.readFileSync(tokenPath, "utf8").trim();
        return token.length ? token : null;
    }
    catch {
        return null;
    }
}
function readComposerMode() {
    const statePath = getModeStateFilePath();
    try {
        const contents = fs.readFileSync(statePath, "utf8");
        const parsed = JSON.parse(contents);
        if (isComposerMode(parsed?.mode)) {
            return parsed.mode;
        }
    }
    catch {
        // ignore missing file or parse errors
    }
    return null;
}
function writeComposerMode(mode) {
    const statePath = getModeStateFilePath();
    try {
        fs.mkdirSync(path.dirname(statePath), { recursive: true });
        fs.writeFileSync(statePath, JSON.stringify({ mode }), "utf8");
    }
    catch {
        // best effort persistence only
    }
}
async function authenticatedFetch(url, options = {}) {
    const token = readAgentToken();
    const headers = new Headers(options.headers);
    if (token) {
        headers.set("X-LOCAL-TOKEN", token);
    }
    return fetch(url, {
        ...options,
        headers,
    });
}
async function getIndexReport(baseUrl, rootPath) {
    const response = await authenticatedFetch(`${baseUrl}/index_report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ root_path: rootPath }),
    });
    if (!response.ok) {
        throw new Error(`Failed to fetch index report: ${response.statusText}`);
    }
    return await response.json();
}
async function triggerIndex(baseUrl, mode, rootPath) {
    const response = await authenticatedFetch(`${baseUrl}/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode }),
    });
    if (!response.ok) {
        throw new Error(`Indexing failed: ${response.statusText}`);
    }
    const result = await response.json();
    if (result.status === 'started' || result.status === 'in_progress') {
        return result;
    }
    if (!rootPath) {
        throw new Error('rootPath required to fetch index report');
    }
    return await getIndexReport(baseUrl, rootPath);
}
async function fetchHealth(baseUrl) {
    try {
        const response = await authenticatedFetch(`${baseUrl}/health`);
        if (!response.ok) {
            return null;
        }
        return await response.json();
    }
    catch {
        return null;
    }
}
let healthPollingInterval;
function startHealthPolling(baseUrl, onUpdate, onError) {
    if (healthPollingInterval) {
        return;
    }
    const poll = async () => {
        try {
            const response = await authenticatedFetch(`${baseUrl}/health`);
            if (!response.ok) {
                throw new Error(`Health check failed: ${response.statusText}`);
            }
            const health = await response.json();
            onUpdate(health);
            if (!health.indexing) {
                stopHealthPolling();
            }
        }
        catch (error) {
            onError(error);
            stopHealthPolling();
        }
    };
    poll();
    healthPollingInterval = setInterval(poll, 2000);
}
function stopHealthPolling() {
    if (healthPollingInterval) {
        clearInterval(healthPollingInterval);
        healthPollingInterval = undefined;
    }
}
async function sendMessageToAgent(message) {
    // US-14: Never log message content to avoid credential or sensitive data leakage
    // Implementation for sending message to agent
}
function buildQueryPayload(question, extraContext) {
    const payload = {
        query: question,
        extra_context: extraContext,
    };
    const rootPath = extraContext?.root_path ?? extraContext?.rootPath;
    if (typeof rootPath === "string" && rootPath.trim()) {
        payload.root_path = path.resolve(rootPath);
    }
    return payload;
}
function ask(question, extraContext) {
    return authenticatedFetch(buildAgentUrl("/ask"), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildQueryPayload(question, extraContext)),
    });
}
function overview(question, extraContext) {
    return authenticatedFetch(buildAgentUrl("/overview"), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildQueryPayload(question, extraContext)),
    });
}
function askWithOverride(question, modeOverride, extraContext) {
    const payload = buildQueryPayload(question, extraContext);
    payload.mode_override = modeOverride;
    return authenticatedFetch(buildAgentUrl("/ask"), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(payload),
    });
}
function search(question, extraContext) {
    return authenticatedFetch(buildAgentUrl("/search"), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(buildQueryPayload(question, extraContext)),
    });
}
async function trackConfluenceUsage(baseUrl, payload) {
    const url = new url_1.URL("/confluence/track-usage", baseUrl).toString();
    const body = {
        userId: payload.userId ?? os.hostname?.() ?? "default",
        feature: payload.feature,
        workspace: payload.workspace ?? "default",
    };
    const response = await authenticatedFetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    });
    if (!response.ok) {
        return { usageCount: 0, showAdvanced: false };
    }
    return (await response.json());
}
