"use strict";
/**
 * ConfluenceChatViewProvider: Single webview for Confluence flow as chat messages.
 * No new tabs: reuses one panel. All UI renders as message cards.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfluenceChatViewProvider = void 0;
exports.getFileSelectorMessageHtml = getFileSelectorMessageHtml;
exports.getProgressMessageHtml = getProgressMessageHtml;
exports.getAnalysisMessageHtml = getAnalysisMessageHtml;
exports.getSuccessMessageHtml = getSuccessMessageHtml;
exports.getErrorMessageHtml = getErrorMessageHtml;
exports.asDisposable = asDisposable;
const vscode = require("vscode");
function escapeHtml(s) {
    return s
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}
function getChatViewHtml(webview) {
    const nonce = getNonce();
    return `<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'nonce-${nonce}'; style-src 'unsafe-inline';">
</head>
<body style="margin:0;font-family:var(--vscode-font-family);background:var(--vscode-editor-background);color:var(--vscode-editor-foreground);display:flex;flex-direction:column;height:100vh;">
  <div id="confluence-message-list" style="flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:12px;"></div>
  <div id="confluence-input-row" style="padding:12px;border-top:1px solid var(--vscode-widget-border);display:flex;align-items:center;gap:8px;">
    <input type="text" placeholder="Type your question..." disabled style="flex:1;padding:6px 12px;background:var(--vscode-input-background);color:var(--vscode-input-foreground);border:1px solid var(--vscode-input-border);border-radius:2px;">
    <button id="confluence-save-btn" style="padding:6px 12px;background:var(--vscode-button-background);color:var(--vscode-button-foreground);border:none;border-radius:2px;cursor:pointer;">💾 Save to Confluence</button>
  </div>
  <script nonce="${nonce}">
    const vscode = acquireVsCodeApi();
    const list = document.getElementById('confluence-message-list');
    let fileSelectorFiles = [];
    let fileSelectorSelected = [];

    document.getElementById('confluence-save-btn').onclick = () => vscode.postMessage({ type: 'confluenceSaveClicked' });

    function renderFileList(card) {
      if (!card) return;
      const fileList = card.querySelector('.confluence-file-list');
      const countEl = card.querySelector('.confluence-selected-count');
      const nextBtn = card.querySelector('.confluence-next');
      if (!fileList || !countEl || !nextBtn) return;
      fileList.innerHTML = fileSelectorFiles.map((f, i) => '<div style="display:flex;align-items:center;padding:2px 0;"><input type="checkbox" class="confluence-file-chk" data-path="' + f.replace(/"/g, '&quot;') + '" ' + (fileSelectorSelected.includes(f) ? 'checked' : '') + ' style="margin-right:8px;"><label style="font-size:12px;">' + f.replace(/</g, '&lt;') + '</label></div>').join('');
      fileList.querySelectorAll('.confluence-file-chk').forEach(cb => {
        cb.addEventListener('change', () => {
          const p = cb.getAttribute('data-path');
          fileSelectorSelected = fileSelectorSelected.includes(p) ? fileSelectorSelected.filter(x => x !== p) : fileSelectorSelected.concat(p);
          countEl.textContent = fileSelectorSelected.length;
          nextBtn.disabled = fileSelectorSelected.length === 0;
          nextBtn.style.opacity = fileSelectorSelected.length === 0 ? '0.5' : '1';
        });
      });
      countEl.textContent = fileSelectorSelected.length;
      nextBtn.disabled = fileSelectorSelected.length === 0;
      nextBtn.style.opacity = fileSelectorSelected.length === 0 ? '0.5' : '1';
    }

    list.addEventListener('click', e => {
      const btn = e.target.closest('button');
      if (!btn) return;
      if (btn.classList.contains('confluence-browse-files')) {
        vscode.postMessage({ type: 'browseFiles' });
      } else if (btn.classList.contains('confluence-cancel') && btn.getAttribute('data-msg-type') === 'file_selector') {
        vscode.postMessage({ type: 'cancel' });
      } else if (btn.classList.contains('confluence-next') && btn.getAttribute('data-msg-type') === 'file_selector') {
        vscode.postMessage({ type: 'next', paths: fileSelectorSelected });
      } else if (btn.classList.contains('confluence-create-page')) {
        vscode.postMessage({ type: 'createPage', title: (btn.closest('.confluence-analysis-card')?.querySelector('.confluence-title-display')?.textContent || '').trim(), space: (btn.closest('.confluence-analysis-card')?.querySelector('.confluence-space-select')?.value || 'DEV') });
      } else if (btn.classList.contains('confluence-edit-title')) {
        vscode.postMessage({ type: 'editTitle' });
      } else if (btn.id === 'open-browser' || btn.classList.contains('confluence-open-browser')) {
        const url = btn.getAttribute('data-url') || btn.closest('.confluence-card')?.querySelector('[data-page-url]')?.getAttribute('data-page-url');
        if (url) vscode.postMessage({ type: 'openInBrowser', url });
      } else if (btn.id === 'copy-link' || btn.classList.contains('confluence-copy-link')) {
        const url = btn.getAttribute('data-url') || btn.closest('.confluence-card')?.querySelector('[data-page-url]')?.getAttribute('data-page-url');
        if (url) vscode.postMessage({ type: 'copyLink', url });
      } else if (btn.id === 'retry' || btn.classList.contains('confluence-retry')) {
        vscode.postMessage({ type: 'retry' });
      } else if (btn.id === 'cancel' && btn.closest('.confluence-card.error')) {
        vscode.postMessage({ type: 'cancel' });
      }
    });

    window.addEventListener('message', e => {
      const m = e.data;
      if (!m || !m.type) return;
      if (m.type === 'append') {
        const div = document.createElement('div');
        div.className = 'confluence-msg';
        div.id = m.id || ('msg-' + Date.now());
        div.innerHTML = m.html;
        list.appendChild(div);
        if (m.id === 'msg-file-selector') { fileSelectorFiles = []; fileSelectorSelected = []; }
        list.scrollTop = list.scrollHeight;
      } else if (m.type === 'update') {
        const el = document.getElementById(m.id);
        if (el) { el.innerHTML = m.html; list.scrollTop = list.scrollHeight; }
      } else if (m.type === 'reset') {
        list.innerHTML = '';
        fileSelectorFiles = [];
        fileSelectorSelected = [];
      } else if (m.type === 'browseFilesResult' && Array.isArray(m.paths)) {
        fileSelectorFiles = [...new Set(fileSelectorFiles.concat(m.paths))];
        fileSelectorSelected = [...new Set(fileSelectorSelected.concat(m.paths))];
        const card = document.querySelector('.confluence-file-selector');
        renderFileList(card);
      }
    });
  </script>
</body>
</html>`;
}
function getNonce() {
    let t = '';
    const p = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    for (let i = 0; i < 16; i++)
        t += p.charAt(Math.floor(Math.random() * p.length));
    return t;
}
function getFileSelectorMessageHtml() {
    return `<div class="confluence-card confluence-file-selector" data-msg-type="file_selector" style="border:1px solid var(--vscode-widget-border);border-radius:4px;padding:12px;background:var(--vscode-editor-background);max-width:400px;">
  <h3 style="margin:0 0 12px 0;font-size:14px;">Select files for intelligent formatting</h3>
  <div style="margin-bottom:12px;">
    <button class="confluence-browse-files" type="button" style="padding:4px 8px;background:var(--vscode-button-background);color:var(--vscode-button-foreground);border:none;border-radius:2px;cursor:pointer;font-size:12px;">📁 Browse Files...</button>
  </div>
  <div class="confluence-file-list" style="max-height:150px;overflow-y:auto;margin-bottom:12px;border:1px solid var(--vscode-input-border);padding:4px;"></div>
  <div style="font-size:12px;margin-bottom:12px;color:var(--vscode-descriptionForeground);">Selected: <span class="confluence-selected-count">0</span> files</div>
  <div style="display:flex;justify-content:flex-end;gap:8px;">
    <button class="confluence-cancel" data-msg-type="file_selector" style="padding:4px 12px;background:transparent;color:var(--vscode-button-foreground);border:1px solid var(--vscode-button-border);border-radius:2px;cursor:pointer;">Cancel</button>
    <button class="confluence-next" data-msg-type="file_selector" style="padding:4px 12px;background:var(--vscode-button-secondaryBackground);color:var(--vscode-button-foreground);border:none;border-radius:2px;cursor:pointer;opacity:0.5;">Next: Let AI Decide</button>
  </div>
</div>`;
}
function getProgressMessageHtml(steps, percent, estimatedSeconds) {
    const items = steps.map(s => `<div style="display:flex;align-items:center;margin-bottom:4px;font-size:12px;"><span style="margin-right:8px;">${s.status === 'completed' ? '✓' : s.status === 'active' ? '●' : '○'}</span><span>${escapeHtml(s.label)}</span></div>`).join('');
    return `<div class="confluence-card" style="border:1px solid var(--vscode-widget-border);border-radius:4px;padding:12px;background:var(--vscode-editor-background);max-width:400px;">
  <h3 style="margin:0 0 12px 0;font-size:14px;">⏳ Creating Intelligent Documentation...</h3>
  <div style="margin-bottom:16px;">${items}</div>
  <div style="height:4px;width:100%;background:var(--vscode-progressBar-background);border-radius:2px;overflow:hidden;"><div style="height:100%;width:${percent}%;background:var(--vscode-progressBar-foreground);"></div></div>
  <div style="font-size:11px;margin-top:4px;">${percent}% — Estimated: ${estimatedSeconds}s</div>
</div>`;
}
function getAnalysisMessageHtml(data) {
    const ct = (data.content_types || []).join(', ') || '—';
    const pats = (data.detected_patterns || []).map(p => `<li>${escapeHtml(p)}</li>`).join('') || '<li>—</li>';
    const title = escapeHtml(data.intelligent_title || '');
    return `<div class="confluence-card confluence-analysis-card" data-suggested-title="${title}" style="border:1px solid var(--vscode-widget-border);border-radius:4px;padding:12px;background:var(--vscode-editor-background);max-width:400px;">
  <h3 style="margin:0 0 12px 0;font-size:14px;">🤖 Intelligent Analysis Complete</h3>
  <div style="font-size:12px;margin-bottom:8px;"><strong>Files:</strong> ${escapeHtml(ct)}</div>
  <div style="font-size:12px;margin-bottom:12px;"><strong>🧠 AI Detected:</strong><ul style="margin:4px 0 0 16px;">${pats}</ul></div>
  <div style="font-size:12px;margin-bottom:12px;padding:8px;background:var(--vscode-textBlockQuote-background);border-radius:2px;">
    <strong>🎯 Intelligent Format Selected:</strong> "${escapeHtml(data.template_name || '')}"
    <div style="font-size:11px;">(${escapeHtml(data.intelligence_reason || '')})</div>
  </div>
  <div style="font-size:12px;margin-bottom:12px;"><strong>📝 Suggested Title:</strong><div class="confluence-title-display" style="padding:4px;border:1px solid var(--vscode-input-border);border-radius:2px;">${title}</div></div>
  <div style="font-size:12px;margin-bottom:16px;"><strong>📍 Confluence Space:</strong><select class="confluence-space-select" style="width:100%;padding:2px;"><option>DEV</option><option>DOCS</option></select></div>
  <div style="display:flex;gap:8px;">
    <button class="confluence-edit-title" style="flex:1;padding:4px;cursor:pointer;">Edit Title</button>
    <button class="confluence-create-page" style="flex:1;padding:4px;cursor:pointer;background:var(--vscode-button-background);color:var(--vscode-button-foreground);border:none;">Create Perfect Page</button>
  </div>
</div>`;
}
function getSuccessMessageHtml(data) {
    const decisions = (data.decisions || []).map(d => `<li>${escapeHtml(d)}</li>`).join('') || '';
    const url = escapeHtml(data.url || '');
    return `<div class="confluence-card" data-page-url="${url}" style="border:1px solid #4CAF50;border-radius:4px;padding:12px;background:var(--vscode-editor-background);max-width:400px;">
  <h3 style="margin:0 0 12px 0;font-size:14px;color:#4CAF50;">✅ Intelligent Documentation Created!</h3>
  <div style="font-size:12px;"><strong>Title:</strong> ${escapeHtml(data.title || '')}</div>
  <div style="font-size:12px;"><strong>Space:</strong> ${escapeHtml(data.space || '')}</div>
  <div style="margin:12px 0;"><strong>🔗 Page Link:</strong><div style="font-size:11px;word-break:break-all;color:var(--vscode-textLink-foreground);">${url}</div></div>
  <div style="font-size:12px;margin-bottom:12px;"><strong>📊 What made this intelligent:</strong><ul style="margin:4px 0 0 16px;">${decisions}</ul></div>
  <div style="display:flex;gap:8px;">
    <button class="confluence-open-browser" data-url="${url}" style="flex:1;padding:4px;cursor:pointer;background:var(--vscode-button-background);color:var(--vscode-button-foreground);border:none;">Open in Browser</button>
    <button class="confluence-copy-link" data-url="${url}" style="flex:1;padding:4px;cursor:pointer;">Copy Link</button>
  </div>
</div>`;
}
function getErrorMessageHtml(data) {
    return `<div class="confluence-card error" style="border:1px solid var(--vscode-errorForeground);border-radius:4px;padding:12px;background:var(--vscode-editor-background);max-width:400px;">
  <h3 style="margin:0 0 8px 0;font-size:14px;color:var(--vscode-errorForeground);">❌ Intelligence Error</h3>
  <div style="font-size:12px;margin-bottom:8px;"><strong>Message:</strong> ${escapeHtml(data.message || '')}</div>
  <div style="font-size:12px;margin-bottom:12px;padding:8px;background:var(--vscode-textBlockQuote-background);"><strong>💡 AI Suggestion:</strong> ${escapeHtml(data.suggestion || '')}</div>
  <div style="display:flex;gap:8px;">
    <button class="confluence-retry" style="padding:4px 12px;cursor:pointer;background:var(--vscode-button-background);color:var(--vscode-button-foreground);border:none;">Retry</button>
    <button id="cancel" style="padding:4px 12px;cursor:pointer;">Cancel</button>
  </div>
</div>`;
}
class ConfluenceChatViewProvider {
    constructor(_extensionUri) {
        this._extensionUri = _extensionUri;
        this._disposables = [];
    }
    getOrCreatePanel() {
        if (this._panel) {
            return this._panel;
        }
        this._panel = vscode.window.createWebviewPanel('confluenceChat', 'Confluence - Intelligent Mode', vscode.ViewColumn.One, { enableScripts: true, retainContextWhenHidden: true });
        this._panel.webview.html = getChatViewHtml(this._panel.webview);
        this._panel.onDidDispose(() => {
            this._panel = undefined;
            for (const d of this._disposables)
                d.dispose();
            this._disposables = [];
        });
        this._disposables.push(this._panel.webview.onDidReceiveMessage((msg) => {
            this._messageHandler?.(msg);
        }));
        return this._panel;
    }
    setMessageHandler(handler) {
        this._messageHandler = handler;
    }
    startFlow() {
        const panel = this.getOrCreatePanel();
        panel.reveal();
        this.postMessage({ type: 'reset' });
        this.postMessage({
            type: 'append',
            id: 'msg-file-selector',
            html: getFileSelectorMessageHtml(),
        });
    }
    postMessage(msg) {
        this._panel?.webview.postMessage(msg);
    }
    dispose() {
        this._panel?.dispose();
        this._panel = undefined;
        for (const d of this._disposables)
            d.dispose();
    }
}
exports.ConfluenceChatViewProvider = ConfluenceChatViewProvider;
function asDisposable(provider) {
    return { dispose: () => provider.dispose() };
}
