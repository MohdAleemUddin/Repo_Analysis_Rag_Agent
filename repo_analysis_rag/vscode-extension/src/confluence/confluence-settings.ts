/**
 * Confluence settings: SecretStorage for API token, async config for API calls.
 * Never log or persist API token in settings.json.
 */

import * as vscode from 'vscode';

const SECRET_KEY = 'confluence.apiToken';

export async function getStoredToken(context: vscode.ExtensionContext): Promise<string | undefined> {
  return context.secrets.get(SECRET_KEY);
}

export async function setStoredToken(context: vscode.ExtensionContext, token: string): Promise<void> {
  await context.secrets.store(SECRET_KEY, token);
}

export interface ConfluenceApiConfig {
  baseUrl: string;
  /** Confluence instance URL (e.g. https://yoursite.atlassian.net/wiki) for create; from credentials.url */
  confluenceInstanceUrl?: string;
  auth: [string, string] | null;
}

/**
 * Build config for Confluence API calls: edge agent base URL + credentials from settings and SecretStorage.
 * Confluence API base URL defaults to http://localhost:8000.
 */
export async function getConfluenceConfigAsync(context: vscode.ExtensionContext): Promise<ConfluenceApiConfig> {
  const cfg = vscode.workspace.getConfiguration('confluence');
  const baseUrl = (cfg.get<string>('apiBaseUrl') ?? 'http://localhost:8000').replace(/\/$/, '');
  const credUrl = (cfg.get<string>('credentials.url') ?? '').trim();
  const email = (cfg.get<string>('credentials.email') ?? '').trim();
  const token = await getStoredToken(context);
  const confluenceInstanceUrl = credUrl ? credUrl.replace(/\/$/, '') : '';
  if (credUrl && email && token && token.trim()) {
    return { baseUrl, confluenceInstanceUrl, auth: [email, token.trim()] };
  }
  return { baseUrl, confluenceInstanceUrl, auth: null };
}

/**
 * Validate Confluence URL. US-10: Cloud URLs must use HTTPS.
 */
export function validateConfluenceUrl(url: string): { valid: boolean; error?: string } {
  const s = (url || '').trim().toLowerCase();
  if (!s) return { valid: true };
  if (s.includes('.atlassian.net') && !s.startsWith('https://')) {
    return { valid: false, error: 'Confluence Cloud URLs must use HTTPS' };
  }
  if (!s.startsWith('http://') && !s.startsWith('https://')) {
    return { valid: false, error: 'URL must start with http:// or https://' };
  }
  return { valid: true };
}

/**
 * Get Confluence instance URL and email only (for test-connection UI). Token must be read separately.
 */
export function getConfluenceCredentialsFromSettings(): { url: string; email: string } {
  const cfg = vscode.workspace.getConfiguration('confluence');
  const url = (cfg.get<string>('credentials.url') ?? '').trim();
  const email = (cfg.get<string>('credentials.email') ?? '').trim();
  return { url, email };
}
