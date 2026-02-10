"use strict";
/**
 * Confluence settings: SecretStorage for API token, async config for API calls.
 * Never log or persist API token in settings.json.
 */
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
exports.getStoredToken = getStoredToken;
exports.setStoredToken = setStoredToken;
exports.getConfluenceConfigAsync = getConfluenceConfigAsync;
exports.validateConfluenceUrl = validateConfluenceUrl;
exports.getConfluenceCredentialsFromSettings = getConfluenceCredentialsFromSettings;
const vscode = __importStar(require("vscode"));
const agentClient_1 = require("../services/agentClient");
const SECRET_KEY = 'confluence.apiToken';
async function getStoredToken(context) {
    return context.secrets.get(SECRET_KEY);
}
async function setStoredToken(context, token) {
    await context.secrets.store(SECRET_KEY, token);
}
/**
 * Build config for Confluence API calls: edge agent base URL + credentials from settings and SecretStorage.
 * Falls back to DEFAULT_AGENT_BASE_URL when Confluence config is not set.
 */
async function getConfluenceConfigAsync(context) {
    const cfg = vscode.workspace.getConfiguration('confluence');
    const baseUrl = (cfg.get('apiBaseUrl') ?? agentClient_1.DEFAULT_AGENT_BASE_URL).replace(/\/$/, '');
    const credUrl = (cfg.get('credentials.url') ?? '').trim();
    const email = (cfg.get('credentials.email') ?? '').trim();
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
