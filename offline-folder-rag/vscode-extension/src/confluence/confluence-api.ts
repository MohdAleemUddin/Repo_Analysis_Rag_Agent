/**
 * Confluence API: POST /confluence/intelligent-analyze and POST /confluence/intelligent-create.
 * Base URL from config/settings; no secrets in logs.
 */

import type { AnalyzeResponse, IntelligenceErrorResponse, CreateRequest } from './types';

export interface ConfluenceApiConfig {
  baseUrl: string;
  auth?: [string, string] | null;
}

async function postJson<T>(url: string, body: unknown, auth?: [string, string] | null): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (auth && auth.length >= 2) {
    const [email, token] = auth;
    const encoded = Buffer.from(`${email}:${token}`).toString('base64');
    headers['Authorization'] = `Basic ${encoded}`;
  }
  const res = await fetch(url, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });
  const data = (await res.json()) as T & { error?: string };
  if (!res.ok) {
    throw new Error((data as { message?: string }).message || res.statusText || 'Request failed');
  }
  return data as T;
}

export async function intelligentAnalyze(
  config: ConfluenceApiConfig,
  payload: { files?: string[]; file_contents?: string[]; content?: string }
): Promise<AnalyzeResponse | IntelligenceErrorResponse> {
  const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/intelligent-analyze`;
  return postJson<AnalyzeResponse | IntelligenceErrorResponse>(url, payload, config.auth);
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
): Promise<{ id?: string; title?: string; space?: string; url?: string }> {
  const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/intelligent-create`;
  const body: Record<string, unknown> = {
    intelligent_mode: payload.intelligent_mode,
    auto_title: payload.auto_title,
    space: payload.space,
    intelligence_context: payload.intelligence_context ?? {},
    base_url: payload.base_url ?? config.baseUrl,
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
  return postJson(url, body, config.auth);
}
