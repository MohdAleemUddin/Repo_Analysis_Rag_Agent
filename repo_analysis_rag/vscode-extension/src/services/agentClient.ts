import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { URL } from "url";
import * as vscode from "vscode";

const TOKEN_FILENAME = "agent_token.txt";
const MODE_STATE_FILENAME = "composer_mode.json";

const COMPOSER_MODES = ["auto", "rag", "tools"] as const;

/** Chat/RAG requests use RAG backend; default port 8001. */
const RAG_CHAT_BASE_URL = "http://localhost:8001";

/** RAG/Agent API base URL (chat, index, search, doctor). Default 8001. */
export const DEFAULT_AGENT_BASE_URL = RAG_CHAT_BASE_URL;

/** Base URL for RAG backend. Uses rag.agentBaseUrl from settings when available. */
export function getRagBaseUrl(): string {
    try {
        const cfg = vscode.workspace.getConfiguration("rag");
        const url = cfg.get<string>("agentBaseUrl");
        if (url && typeof url === "string" && url.trim()) return url.trim().replace(/\/$/, "");
    } catch {
        // ignore when vscode not available (e.g. tests)
    }
    return RAG_CHAT_BASE_URL;
}

function buildAgentUrl(endpoint: string): string {
    return new URL(endpoint, getRagBaseUrl()).toString();
}

function getIndexDir(): string {
    const envDir = process.env.RAG_INDEX_DIR;
    if (envDir && envDir.trim()) {
        return envDir;
    }

    const userProfile = process.env.USERPROFILE || os.homedir();
    return path.join(userProfile, ".offline_rag_index");
}

function getModeStateFilePath(): string {
    return path.join(getIndexDir(), MODE_STATE_FILENAME);
}

export type ComposerMode = (typeof COMPOSER_MODES)[number];

export function isComposerMode(value: unknown): value is ComposerMode {
    return (
        typeof value === "string" &&
        (COMPOSER_MODES as readonly string[]).includes(value)
    );
}

export function getTokenFilePath(): string {
    return path.join(getIndexDir(), TOKEN_FILENAME);
}

export function readAgentToken(): string | null {
    const tokenPath = getTokenFilePath();
    try {
        const token = fs.readFileSync(tokenPath, "utf8").trim();
        return token.length ? token : null;
    } catch {
        return null;
    }
}

export function readComposerMode(): ComposerMode | null {
    const statePath = getModeStateFilePath();
    try {
        const contents = fs.readFileSync(statePath, "utf8");
        const parsed = JSON.parse(contents);
        if (isComposerMode(parsed?.mode)) {
            return parsed.mode;
        }
    } catch {
        // ignore missing file or parse errors
    }

    return null;
}

export function writeComposerMode(mode: ComposerMode): void {
    const statePath = getModeStateFilePath();
    try {
        fs.mkdirSync(path.dirname(statePath), { recursive: true });
        fs.writeFileSync(statePath, JSON.stringify({ mode }), "utf8");
    } catch {
        // best effort persistence only
    }
}

export interface HealthResponse {
    indexing: boolean;
    indexed_files_so_far: number;
    estimated_total_files: number;
    last_index_completed_epoch_ms: number;
    ollama_ok: boolean;
    ripgrep_ok: boolean;
    chroma_ok: boolean;
}

export interface IndexReport {
    indexed_files: string[];
    skipped_files: { path: string; reason: string }[];
    top_skip_reasons: { reason: string; count: number }[];
}

export async function authenticatedFetch(url: string, options: RequestInit = {}): Promise<Response> {
    const token = readAgentToken();
    const headers = new Headers(options.headers);

    if (token) {
        headers.set("X-LOCAL-TOKEN", token);
    }

    // Diagnostic: log request (no body/token content) to Debug Console when extension runs
    const method = (options.method || "GET").toUpperCase();
    const tokenPresent = !!token;
    console.log(`[RAG] Request: ${method} ${url} token_present=${tokenPresent}`);

    return fetch(url, {
        ...options,
        headers,
    });
}

export async function getIndexReport(baseUrl: string, rootPath: string): Promise<IndexReport> {
    const response = await authenticatedFetch(`${baseUrl}/index_report`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ root_path: rootPath }),
    });
    if (!response.ok) {
        throw new Error(`Failed to fetch index report: ${response.statusText}`);
    }
    return await response.json() as IndexReport;
}

export async function triggerIndex(baseUrl: string, mode: 'full' | 'incremental', rootPath?: string): Promise<IndexReport | { status: string }> {
    const body: { mode: string; root_path?: string } = { mode };
    if (typeof rootPath === "string" && rootPath.trim()) {
        body.root_path = path.resolve(rootPath);
    }
    const response = await authenticatedFetch(`${baseUrl}/index`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
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

export async function fetchHealth(baseUrl: string): Promise<HealthResponse | null> {
    try {
        const response = await authenticatedFetch(`${baseUrl}/health`);
        if (!response.ok) {
            return null;
        }
        return await response.json() as HealthResponse;
    } catch {
        return null;
    }
}

let healthPollingInterval: NodeJS.Timeout | undefined;

export function startHealthPolling(
    baseUrl: string,
    onUpdate: (health: HealthResponse) => void,
    onError: (error: any) => void
) {
    if (healthPollingInterval) {
        return;
  }

    const poll = async () => {
        try {
            const response = await authenticatedFetch(`${baseUrl}/health`);
            if (!response.ok) {
                throw new Error(`Health check failed: ${response.statusText}`);
            }
            const health = await response.json() as HealthResponse;
            onUpdate(health);
            if (!health.indexing) {
                stopHealthPolling();
            }
        } catch (error) {
            onError(error);
            stopHealthPolling();
        }
    };

    poll();
    healthPollingInterval = setInterval(poll, 2000);
}

export function stopHealthPolling() {
    if (healthPollingInterval) {
        clearInterval(healthPollingInterval);
        healthPollingInterval = undefined;
    }
}

export async function sendMessageToAgent(message: string): Promise<void> {
    // US-14: Never log message content to avoid credential or sensitive data leakage
    // Implementation for sending message to agent
}

function buildQueryPayload(question: string, extraContext?: any) {
  const payload: Record<string, any> = {
    query: question,
    extra_context: extraContext,
  };

  const rootPath = extraContext?.root_path ?? extraContext?.rootPath;
  if (typeof rootPath === "string" && rootPath.trim()) {
    payload.root_path = path.resolve(rootPath);
  }

  return payload;
}

export function ask(question: string, extraContext?: any) {
  return authenticatedFetch(buildAgentUrl("/ask"), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildQueryPayload(question, extraContext)),
  });
}

export function overview(question: string, extraContext?: any) {
  return authenticatedFetch(buildAgentUrl("/overview"), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildQueryPayload(question, extraContext)),
  });
}

export function askWithOverride(question: string, modeOverride: string, extraContext?: any) {
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

export function search(question: string, extraContext?: any) {
  return authenticatedFetch(buildAgentUrl("/search"), {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(buildQueryPayload(question, extraContext)),
  });
}

export interface TrackConfluenceUsagePayload {
  userId?: string;
  feature: string;
  workspace?: string;
}

export interface TrackConfluenceUsageResponse {
  usageCount: number;
  showAdvanced?: boolean;
  learning?: boolean;
  messages?: Record<string, string>;
}

export async function trackConfluenceUsage(
  baseUrl: string,
  payload: TrackConfluenceUsagePayload
): Promise<TrackConfluenceUsageResponse> {
  const url = new URL("/confluence/track-usage", baseUrl).toString();
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
  return (await response.json()) as TrackConfluenceUsageResponse;
}
