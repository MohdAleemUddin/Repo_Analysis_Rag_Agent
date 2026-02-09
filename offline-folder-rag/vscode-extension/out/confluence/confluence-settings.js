"use strict";
/**
 * Confluence settings: SecretStorage for API token, async config for API calls.
 * Never log or persist API token in settings.json.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.getStoredToken = getStoredToken;
exports.setStoredToken = setStoredToken;
exports.getConfluenceConfigAsync = getConfluenceConfigAsync;
exports.validateConfluenceUrl = validateConfluenceUrl;
exports.getConfluenceCredentialsFromSettings = getConfluenceCredentialsFromSettings;
const vscode = require("vscode");
const SECRET_KEY = 'confluence.apiToken';
async function getStoredToken(context) {
    return context.secrets.get(SECRET_KEY);
}
async function setStoredToken(context, token) {
    await context.secrets.store(SECRET_KEY, token);
}
/**
 * Build config for Confluence API calls: edge agent base URL + credentials from settings and SecretStorage.
 * Use this for all Confluence API calls (analyze, create, document-project, config test-connection).
 */
async function getConfluenceConfigAsync(context) {
    const cfg = vscode.workspace.getConfiguration('confluence');
    const baseUrl = (cfg.get('apiBaseUrl') ?? 'http://localhost:8000').replace(/\/$/, '');
    const credUrl = (cfg.get('credentials.url') ?? '').trim();
    const email = (cfg.get('credentials.email') ?? '').trim();
    const token = await getStoredToken(context);
    if (credUrl && email && token && token.trim()) {
        return { baseUrl, auth: [email, token.trim()] };
    }
    return { baseUrl, auth: null };
}
/**
 * Validate Confluence URL. US-10: Cloud URLs must use HTTPS.
 */
function validateConfluenceUrl(url) {
    const s = (url || '').trim().toLowerCase();
    if (!s)
        return { valid: true };
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
function getConfluenceCredentialsFromSettings() {
    const cfg = vscode.workspace.getConfiguration('confluence');
    const url = (cfg.get('credentials.url') ?? '').trim();
    const email = (cfg.get('credentials.email') ?? '').trim();
    return { url, email };
}
