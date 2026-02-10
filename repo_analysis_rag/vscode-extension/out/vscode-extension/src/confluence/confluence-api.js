"use strict";
/**
 * Confluence API: POST /confluence/intelligent-analyze and POST /confluence/intelligent-create.
 * Base URL from config/settings; no secrets in logs.
 * US-13: Auto-retry with exponential backoff for network/429 errors.
 * US-14: Never log request body or auth.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.intelligentAnalyze = intelligentAnalyze;
exports.intelligentCreate = intelligentCreate;
exports.getIntelligenceStatus = getIntelligenceStatus;
exports.postIntelligenceFeedback = postIntelligenceFeedback;
exports.documentProject = documentProject;
exports.getPreferredSpace = getPreferredSpace;
exports.fetchSpaces = fetchSpaces;
exports.exportExamples = exportExamples;
exports.importExamples = importExamples;
const NETWORK_RETRIES = 3;
const RATE_LIMIT_WAIT_MS = 30000;
const BACKOFF_BASE_MS = 1000;
function sleep(ms) {
    return new Promise((resolve) => setTimeout(resolve, ms));
}
function isNetworkError(e) {
    const msg = String(e instanceof Error ? e.message : e).toLowerCase();
    return (e instanceof TypeError ||
        msg.includes('fetch') ||
        msg.includes('network') ||
        msg.includes('connection') ||
        msg.includes('econnrefused') ||
        msg.includes('enotfound') ||
        msg.includes('timeout') ||
        msg.includes('failed to fetch'));
}
function isRetryableStatus(status) {
    return status === 429;
}
function isNonRetryableStatus(status) {
    return status === 401 || status === 403 || status === 404;
}
async function checkBackendHealth(baseUrl) {
    try {
        const url = `${baseUrl.replace(/\/$/, '')}/health`;
        const res = await fetch(url, { method: 'GET' });
        return res.ok;
    }
    catch {
        return false;
    }
}
async function postJsonWithRetry(url, body, auth) {
    const headers = {
        'Content-Type': 'application/json',
    };
    if (auth && auth.length >= 2) {
        const [email, token] = auth;
        const encoded = Buffer.from(`${email}:${token}`).toString('base64');
        headers['Authorization'] = `Basic ${encoded}`;
    }
    let lastError = null;
    let backoff = BACKOFF_BASE_MS;
    for (let attempt = 0; attempt <= NETWORK_RETRIES; attempt++) {
        try {
            const res = await fetch(url, {
                method: 'POST',
                headers,
                body: JSON.stringify(body),
            });
            const text = await res.text();
            let data;
            try {
                data = JSON.parse(text);
            }
            catch {
                throw new Error(`Backend returned non-JSON. Is the Confluence server running at ${url}? (Status: ${res.status})`);
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
            return data;
        }
        catch (e) {
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
async function intelligentAnalyze(config, payload) {
    const isHealthy = await checkBackendHealth(config.baseUrl);
    if (!isHealthy) {
        throw new Error(`Backend not reachable at ${config.baseUrl}. Please ensure the Confluence edge agent is running.`);
    }
    const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/intelligent-analyze`;
    return postJsonWithRetry(url, payload, config.auth);
}
async function intelligentCreate(config, payload) {
    const isHealthy = await checkBackendHealth(config.baseUrl);
    if (!isHealthy) {
        throw new Error(`Backend not reachable at ${config.baseUrl}. Please ensure the Confluence edge agent is running.`);
    }
    const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/intelligent-create`;
    const body = {
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
        body.intelligence_context.suggested_title = payload.suggested_title;
    }
    if (payload.content !== undefined)
        body.content = payload.content;
    if (payload.body_content !== undefined)
        body.body_content = payload.body_content;
    if (payload.feedback_for_learning !== undefined)
        body.feedback_for_learning = payload.feedback_for_learning;
    const data = await postJsonWithRetry(url, body, config.auth);
    if (data?.error) {
        return data;
    }
    const page = data?.intelligent_page;
    const summary = data?.intelligence_summary;
    const creationId = data?.creation_id;
    return {
        id: creationId ?? page?.id ?? data?.id,
        title: page?.title ?? data?.title,
        space: page?.space ?? data?.space,
        url: page?.url ?? data?.url,
        ai_learning_applied: summary?.ai_learning_applied ?? data?.ai_learning_applied,
    };
}
/** US-17: Fetch intelligence status from GET /confluence/intelligence-status (with auth when provided). */
async function getIntelligenceStatus(config, detailLevel) {
    const base = config.baseUrl.replace(/\/$/, '');
    const u = new URL('/confluence/intelligence-status', base.startsWith('http') ? base : `http://${base}`);
    u.searchParams.set('detail_level', detailLevel || 'full');
    const headers = {};
    if (config.auth && config.auth.length >= 2) {
        const [email, token] = config.auth;
        headers['Authorization'] = `Basic ${Buffer.from(`${email}:${token}`).toString('base64')}`;
    }
    const res = await fetch(u.toString(), { headers });
    if (!res.ok)
        throw new Error(res.statusText || 'Failed to fetch intelligence status');
    return (await res.json());
}
/** US-17: Submit intelligence feedback via POST /confluence/intelligence-feedback. */
async function postIntelligenceFeedback(config, payload) {
    const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/intelligence-feedback`;
    return postJsonWithRetry(url, payload, config.auth);
}
async function documentProject(config, payload) {
    const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/document-project`;
    const body = {
        workspace_path: payload.workspace_path,
        space: payload.space ?? 'DOC',
        base_url: config.baseUrl,
        auth: config.auth,
    };
    return postJsonWithRetry(url, body, config.auth);
}
/** US-10: Get preferred Confluence space for project (from intelligent_creations or default by type). */
async function getPreferredSpace(baseUrl, projectPath) {
    const base = baseUrl.replace(/\/$/, '');
    const u = new URL('/confluence/config/preferred-space', base.startsWith('http') ? base : `http://${base}`);
    u.searchParams.set('project_path', projectPath);
    try {
        const res = await fetch(u.toString());
        const data = (await res.json());
        return data.preferred_space ?? 'DEV';
    }
    catch {
        return 'DEV';
    }
}
/** Fetch current Confluence spaces from backend. Used when showing space dropdown. */
async function fetchSpaces(config) {
    if (!config.auth || config.auth.length < 2 || !config.auth[0] || !config.auth[1]) {
        return [];
    }
    const base = config.baseUrl.replace(/\/$/, '');
    const url = `${base.startsWith('http') ? base : `http://${base}`}/confluence/config/spaces`;
    try {
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                url: config.confluenceInstanceUrl ?? '',
                email: config.auth[0],
                api_token: config.auth[1],
            }),
        });
        if (!res.ok)
            return [];
        const data = (await res.json());
        const list = data.spaces ?? [];
        return list
            .filter((s) => !!s?.key)
            .map((s) => ({ key: s.key, name: s.name ?? s.key }));
    }
    catch {
        return [];
    }
}
async function exportExamples(config, options) {
    const base = config.baseUrl.replace(/\/$/, '');
    const u = new URL('/confluence/examples/export', base.startsWith('http') ? base : `http://${base}`);
    if (options?.project_path)
        u.searchParams.set('project_path', options.project_path);
    if (options?.from_date)
        u.searchParams.set('from_date', options.from_date);
    if (options?.to_date)
        u.searchParams.set('to_date', options.to_date);
    if (options?.template_type)
        u.searchParams.set('template_type', options.template_type);
    const headers = {};
    if (config.auth && config.auth.length >= 2) {
        const [email, token] = config.auth;
        headers['Authorization'] = `Basic ${Buffer.from(`${email}:${token}`).toString('base64')}`;
    }
    const res = await fetch(u.toString(), { headers });
    if (!res.ok)
        throw new Error(res.statusText || 'Failed to export examples');
    return res.text();
}
async function importExamples(config, jsonPayload) {
    const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/examples/import`;
    const data = await postJsonWithRetry(url, jsonPayload, config.auth);
    return {
        message: data.message ?? 'Import complete.',
        importedCount: data.imported_count ?? 0,
    };
}
