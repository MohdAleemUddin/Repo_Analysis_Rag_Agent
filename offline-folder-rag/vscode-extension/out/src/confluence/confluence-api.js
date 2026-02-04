"use strict";
/**
 * Confluence API: POST /confluence/intelligent-analyze and POST /confluence/intelligent-create.
 * Base URL from config/settings; no secrets in logs.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.intelligentAnalyze = intelligentAnalyze;
exports.intelligentCreate = intelligentCreate;
async function postJson(url, body, auth) {
    const headers = {
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
    const data = (await res.json());
    if (!res.ok) {
        throw new Error(data.message || res.statusText || 'Request failed');
    }
    return data;
}
async function intelligentAnalyze(config, payload) {
    const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/intelligent-analyze`;
    return postJson(url, payload, config.auth);
}
async function intelligentCreate(config, payload) {
    const url = `${config.baseUrl.replace(/\/$/, '')}/confluence/intelligent-create`;
    const body = {
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
        body.intelligence_context.suggested_title = payload.suggested_title;
    }
    if (payload.content !== undefined)
        body.content = payload.content;
    if (payload.body_content !== undefined)
        body.body_content = payload.body_content;
    if (payload.feedback_for_learning !== undefined)
        body.feedback_for_learning = payload.feedback_for_learning;
    return postJson(url, body, config.auth);
}
