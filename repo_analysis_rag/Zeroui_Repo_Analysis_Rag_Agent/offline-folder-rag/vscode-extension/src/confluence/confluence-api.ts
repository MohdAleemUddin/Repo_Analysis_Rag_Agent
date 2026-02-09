/**
 * Confluence API: POST /confluence/intelligent-analyze and POST /confluence/intelligent-create.
 * Base URL from config/settings; no secrets in logs.
 * US-13: Auto-retry with exponential backoff for network/429 errors.
 * US-14: Never log request body or auth.
 */

import type { AnalyzeResponse, IntelligenceErrorResponse, IntelligenceStatusResponse } from './types';

export interface ConfluenceApiConfig {
  baseUrl: string;
  /** Confluence instance URL for create (HTTPS); from credentials.url */
  confluenceInstanceUrl?: string;
  auth?: [string, string] | null;
}

const NETWORK_RETRIES = 3;
const RATE_LIMIT_WAIT_MS = 30000;
const BACKOFF_BASE_MS = 1000;

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isNetworkError(e: unknown): boolean {
  const msg = String(e instanceof Error ? e.message : e).toLowerCase();
  return (
    e instanceof TypeError ||
    msg.includes('fetch') ||
    msg.includes('network') ||
    msg.includes('connection') ||
    msg.includes('econnrefused') ||
    msg.includes('enotfound') ||
    msg.includes('timeout') ||
    msg.includes('failed to fetch')
  );
}

function isRetryableStatus(status: number): boolean {
  return status === 429;
}

function isNonRetryableStatus(status: number): boolean {
  return status === 401 || status === 403 || status === 404;
}

async function checkBackendHealth(baseUrl: string): Promise<boolean> {
  try {
    const url = `${baseUrl.replace(/\/$/, '')}/health`;
    const res = await fetch(url, { method: 'GET' });
    return res.ok;
  } catch {
    return false;
  }
}

async function postJsonWithRetry<T>(
  url: string,
  body: unknown,
  auth?: [string, string] | null
): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (auth && auth.length >= 2) {
    const [email, token] = auth;
    const encoded = Buffer.from(`${email}:${token}`).toString('base64');
    headers['Authorization'] = `Basic ${encoded}`;
  }

  let lastError: Error | null = null;
  let backoff = BACKOFF_BASE_MS;

  for (let attempt = 0; attempt <= NETWORK_RETRIES; attempt++) {
    try {
      const res = await fetch(url, {
        method: 'POST',
        headers,
        body: JSON.stringify(body),
      });

      const text = await res.text();
      let data: T & { error?: string; message?: string };
      try {
        data = JSON.parse(text) as T & { error?: string; message?: string };
      } catch {
        throw new Error(
          `Backend returned non-JSON. Is the Confluence server running at ${url}? (Status: ${res.status})`
        );
      }

      if (res.status === 429 && attempt < NETWORK_RETRIES) {
        await sleep(RATE_LIMIT_WAIT_MS);
        continue;
      }

      if (isNonRetryableStatus(res.status)) {
        throw new Error(data.message || res.statusText || 'Request failed');
      }

      if (!res.ok) {
        if (isRetryableStatus(res.status) && attempt < NETWORK_RETRIES) {
          await sleep(RATE_LIMIT_WAIT_MS);
          continue;
        }
        throw new Error(data.message || res.statusText || 'Request failed');
      }

      return data as T;
    } catch (e) {
      lastError = e instanceof Error ? e : new Error(String(e));
      if (isNetworkError(e) && attempt < NETWORK_RETRIES) {
        await sleep(backoff);
        backoff *= 2;
        continue;
      }
      throw lastError;
    }
  }

  throw lastError ?? new Error('Request failed after retries');
}

export interface ChatContextPayload {
  messages?: Array<{ content?: string; text?: string; message?: string }>;
  selected_text?: string;
  selection?: string;
  workspace_path?: string;
  workspacePath?: string;
}

export async function intelligentAnalyze(
  config: ConfluenceApiConfig,
  payload: {
    files?: string[];
    file_contents?: string[];
    content?: string;
    chat_context?: ChatContextPayload;
  }
): Promise<AnalyzeResponse | IntelligenceErrorResponse> {
  const isHealthy = await checkBackendHealth(config.baseUrl);
  if (!isHealthy) {
    throw new Error(
      `Backend not reachable at ${config.baseUrl}. Please ensure the Confluence edge agent is running.`
    );
  }
  const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/intelligent-analyze`;
  return postJsonWithRetry<AnalyzeResponse | IntelligenceErrorResponse>(url, payload, config.auth);
}

export async function intelligentCreate(
  config: ConfluenceApiConfig,
  payload: {
    files?: string[] | Array<{ content: string }>;
    intelligent_mode: boolean;
    auto_title: boolean;
    space: string;
    intelligence_context?: { title_override?: string; suggested_title?: string };
    base_url?: string;
    auth?: [string, string];
    suggested_title?: string;
    content?: string;
    body_content?: string;
    feedback_for_learning?: string;
  }
): Promise<
  | { id?: string; title?: string; space?: string; url?: string; ai_learning_applied?: boolean }
  | IntelligenceErrorResponse
> {
  const isHealthy = await checkBackendHealth(config.baseUrl);
  if (!isHealthy) {
    throw new Error(
      `Backend not reachable at ${config.baseUrl}. Please ensure the Confluence edge agent is running.`
    );
  }
  const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/intelligent-create`;
  const body: Record<string, unknown> = {
    intelligent_mode: payload.intelligent_mode,
    auto_title: payload.auto_title,
    space: payload.space,
    intelligence_context: payload.intelligence_context ?? {},
    base_url: payload.base_url ?? config.confluenceInstanceUrl ?? config.baseUrl,
    auth: payload.auth ?? config.auth,
  };
  if (payload.files?.length) {
    body.files = payload.files.map((f) => (typeof f === 'string' ? f : f.content));
  }
  if (payload.suggested_title) {
    (body.intelligence_context as Record<string, string>).suggested_title = payload.suggested_title;
  }
  if (payload.content !== undefined) body.content = payload.content;
  if (payload.body_content !== undefined) body.body_content = payload.body_content;
  if (payload.feedback_for_learning !== undefined) body.feedback_for_learning = payload.feedback_for_learning;
  const data = await postJsonWithRetry<Record<string, unknown>>(url, body, config.auth);

  if (data?.error) {
    return data as unknown as IntelligenceErrorResponse;
  }

  const page = data?.intelligent_page as { url?: string; id?: string; title?: string; space?: string } | undefined;
  const summary = data?.intelligence_summary as { ai_learning_applied?: boolean } | undefined;
  const creationId = data?.creation_id as string | undefined;
  return {
    id: creationId ?? page?.id ?? (data?.id as string | undefined),
    title: page?.title ?? (data?.title as string | undefined),
    space: page?.space ?? (data?.space as string | undefined),
    url: page?.url ?? (data?.url as string | undefined),
    ai_learning_applied: summary?.ai_learning_applied ?? (data?.ai_learning_applied as boolean | undefined),
  };
}

/** US-17: Fetch intelligence status from GET /confluence/intelligence-status (with auth when provided). */
export async function getIntelligenceStatus(
  config: ConfluenceApiConfig,
  detailLevel?: string
): Promise<IntelligenceStatusResponse> {
  const base = config.baseUrl.replace(/\/$/, '');
  const u = new URL(
    '/confluence/intelligence-status',
    base.startsWith('http') ? base : `http://${base}`
  );
  u.searchParams.set('detail_level', detailLevel || 'full');
  const headers: Record<string, string> = {};
  if (config.auth && config.auth.length >= 2) {
    const [email, token] = config.auth;
    headers['Authorization'] = `Basic ${Buffer.from(`${email}:${token}`).toString('base64')}`;
  }
  const res = await fetch(u.toString(), { headers });
  if (!res.ok) throw new Error(res.statusText || 'Failed to fetch intelligence status');
  return (await res.json()) as IntelligenceStatusResponse;
}

/** US-17: Submit intelligence feedback via POST /confluence/intelligence-feedback. */
export async function postIntelligenceFeedback(
  config: ConfluenceApiConfig,
  payload: { creation_id: string; intelligence_score: number; feedback?: string }
): Promise<IntelligenceStatusResponse & { updated?: boolean }> {
  const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/intelligence-feedback`;
  return postJsonWithRetry<IntelligenceStatusResponse & { updated?: boolean }>(url, payload, config.auth);
}

/** US-16: Document entire project via POST /confluence/document-project. */
export interface DocumentProjectResponse {
  confluence_url?: string;
  intelligence_analysis?: {
    project_type?: string;
    content_types?: string[];
    detected_patterns?: string[];
    source_file_count?: number;
  };
  intelligent_recommendation?: { template_name?: string; intelligence_reason?: string };
  confidence?: number;
  template_name?: string;
  learning_indicator?: boolean;
  error?: string;
  message?: string;
}

export async function documentProject(
  config: ConfluenceApiConfig,
  payload: { workspace_path: string; space?: string }
): Promise<DocumentProjectResponse> {
  const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/document-project`;
  const body = {
    workspace_path: payload.workspace_path,
    space: payload.space ?? 'DOC',
    base_url: config.baseUrl,
    auth: config.auth,
  };
  return postJsonWithRetry<DocumentProjectResponse>(url, body, config.auth);
}

/** US-10: Get preferred Confluence space for project (from intelligent_creations or default by type). */
export async function getPreferredSpace(baseUrl: string, projectPath: string): Promise<string> {
  const base = baseUrl.replace(/\/$/, '');
  const u = new URL('/confluence/config/preferred-space', base.startsWith('http') ? base : `http://${base}`);
  u.searchParams.set('project_path', projectPath);
  try {
    const res = await fetch(u.toString());
    const data = (await res.json()) as { preferred_space?: string };
    return data.preferred_space ?? 'DEV';
  } catch {
    return 'DEV';
  }
}

/** US-6: Export learned examples as JSON via GET /confluence/examples/export. */
export interface ExportExamplesOptions {
  project_path?: string;
  from_date?: string;
  to_date?: string;
  template_type?: string;
}

export async function exportExamples(
  config: ConfluenceApiConfig,
  options?: ExportExamplesOptions
): Promise<string> {
  const base = config.baseUrl.replace(/\/$/, '');
  const u = new URL('/confluence/examples/export', base.startsWith('http') ? base : `http://${base}`);
  if (options?.project_path) u.searchParams.set('project_path', options.project_path);
  if (options?.from_date) u.searchParams.set('from_date', options.from_date);
  if (options?.to_date) u.searchParams.set('to_date', options.to_date);
  if (options?.template_type) u.searchParams.set('template_type', options.template_type);
  const headers: Record<string, string> = {};
  if (config.auth && config.auth.length >= 2) {
    const [email, token] = config.auth;
    headers['Authorization'] = `Basic ${Buffer.from(`${email}:${token}`).toString('base64')}`;
  }
  const res = await fetch(u.toString(), { headers });
  if (!res.ok) throw new Error(res.statusText || 'Failed to export examples');
  return res.text();
}

/** US-6: Import learned examples via POST /confluence/examples/import. */
export interface ImportExamplesResponse {
  message: string;
  importedCount: number;
}

export async function importExamples(
  config: ConfluenceApiConfig,
  jsonPayload: object
): Promise<ImportExamplesResponse> {
  const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/examples/import`;
  const data = await postJsonWithRetry<{ message?: string; imported_count?: number }>(
    url,
    jsonPayload,
    config.auth
  );
  return {
    message: data.message ?? 'Import complete.',
    importedCount: data.imported_count ?? 0,
  };
}
