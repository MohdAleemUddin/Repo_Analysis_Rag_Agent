import * as vscode from 'vscode';
import { ConfluenceButton } from './confluence/ConfluenceButton';
import { ConfluenceFileSelector } from './confluence/ConfluenceFileSelector';
import { ConfluenceResults } from './confluence/ConfluenceResults';
import { ConfluenceProgress } from './confluence/ConfluenceProgress';
import { getConfluenceConfigAsync, getConfluenceCredentialsFromSettings, getStoredToken } from './confluence/confluence-settings';

function getConfluenceConfigPanelHtml(webview: vscode.Webview, baseUrl: string): string {
  return `<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline';"></head>
<body style="font-family: var(--vscode-font-family); font-size: 13px; padding: 16px; max-width: 480px;">
  <h3 style="margin-top:0">Confluence configuration</h3>
  <p style="color: var(--vscode-descriptionForeground);">Set URL and email in Settings, then store your API token. Click Test connection to verify.</p>
  <div id="validation-errors" style="display:none; margin-bottom: 12px; padding: 8px; background: var(--vscode-inputValidation-errorBackground); border-radius: 4px;"></div>
  <button id="test-btn" type="button" style="padding: 6px 12px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 2px; cursor: pointer;">Test connection</button>
  <div id="result" style="margin-top: 12px; padding: 8px; border-radius: 4px; display: none;"></div>
  <p style="margin-top: 12px; font-size: 11px; color: var(--vscode-descriptionForeground);">Edge agent: ${escapeHtml(baseUrl)}</p>
  <script>
    const vscode = acquireVsCodeApi();
    const testBtn = document.getElementById('test-btn');
    const resultEl = document.getElementById('result');
    const errEl = document.getElementById('validation-errors');
    testBtn.onclick = function() {
      testBtn.disabled = true;
      testBtn.textContent = 'Testing…';
      resultEl.style.display = 'none';
      errEl.style.display = 'none';
      vscode.postMessage({ type: 'confluenceTestConnection' });
    };
    window.addEventListener('message', function(e) {
      const msg = e.data;
      if (msg.type === 'confluenceTestConnectionResult') {
        testBtn.disabled = false;
        testBtn.textContent = 'Test connection';
        resultEl.style.display = 'block';
        if (msg.error) {
          resultEl.style.background = 'var(--vscode-inputValidation-errorBackground)';
          resultEl.style.border = '1px solid var(--vscode-inputValidation-errorBorder)';
          resultEl.textContent = msg.error;
        } else {
          resultEl.style.background = 'var(--vscode-editor-inactiveSelectionBackground)';
          resultEl.style.border = '1px solid var(--vscode-widget-border)';
          resultEl.innerHTML = 'Connection successful.' + (msg.latency_ms != null ? '<br><small>Latency: ' + msg.latency_ms + ' ms</small>' : '') + (msg.spaces && msg.spaces.length ? '<br><small>Spaces: ' + msg.spaces.map(function(s){ return s.key || s.name; }).join(', ') + '</small>' : '');
        }
      }
      if (msg.type === 'confluenceValidationErrors' && msg.errors && msg.errors.length) {
        errEl.style.display = 'block';
        errEl.innerHTML = '<ul style="margin:0;padding-left:20px">' + msg.errors.map(function(e){ return '<li>' + e.replace(/</g,'&lt;') + '</li>'; }).join('') + '</ul>';
      }
    });
  </script>
</body>
</html>`;
}

function escapeHtml(s: string): string {
  return String(s)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function openConfluenceConfigPanel(context: vscode.ExtensionContext): void {
  const cfg = vscode.workspace.getConfiguration('confluence');
  const baseUrl = (cfg.get<string>('apiBaseUrl') ?? 'http://localhost:8000').replace(/\/$/, '');
  const panel = vscode.window.createWebviewPanel(
    'confluenceConfig',
    'Confluence configuration',
    vscode.ViewColumn.One,
    { enableScripts: true }
  );
  panel.webview.html = getConfluenceConfigPanelHtml(panel.webview, baseUrl);
  panel.webview.onDidReceiveMessage(async (msg) => {
    if (msg.type === 'confluenceTestConnection') {
      const { url, email } = getConfluenceCredentialsFromSettings();
      const token = await getStoredToken(context);
      const validationErrors: string[] = [];
      if (!url || !url.trim()) validationErrors.push('Confluence URL is required.');
      if (!email || !email.trim()) validationErrors.push('Email is required.');
      if (!token || !token.trim()) validationErrors.push('API token is required. Store it in Confluence settings.');
      if (validationErrors.length > 0) {
        panel.webview.postMessage({ type: 'confluenceValidationErrors', errors: validationErrors });
        panel.webview.postMessage({ type: 'confluenceTestConnectionResult', error: validationErrors.join(' ') });
        return;
      }
      try {
        const res = await fetch(`${baseUrl}/confluence/config/test-connection`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: url.trim(), email: email.trim(), api_token: token.trim() }),
        });
        const data = await res.json() as { ok?: boolean; error?: string; latency_ms?: number; spaces?: Array<{ key?: string; name?: string }> };
        if (!res.ok) {
          panel.webview.postMessage({ type: 'confluenceTestConnectionResult', error: (data as { error?: string }).error || res.statusText });
          return;
        }
        panel.webview.postMessage({
          type: 'confluenceTestConnectionResult',
          ...data,
          error: data.ok ? undefined : (data.error || 'Connection failed'),
        });
      } catch (e) {
        panel.webview.postMessage({ type: 'confluenceTestConnectionResult', error: String(e) });
      }
    }
  });
}

function getConfluenceFileSelectorWebviewHtml(webview: vscode.Webview): string {
  return `<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline' var(--vscode-font-family);"></head>
<body>
<div class="confluence-card" style="border:1px solid var(--vscode-widget-border);border-radius:4px;padding:12px;background:var(--vscode-editor-background);max-width:400px;">
  <h3 style="margin:0 0 12px 0;font-size:14px;">Select files for intelligent formatting</h3>
  <div style="margin-bottom:12px;">
    <button id="browse-files" type="button" style="padding:4px 8px;background:var(--vscode-button-background);color:var(--vscode-button-foreground);border:none;border-radius:2px;cursor:pointer;font-size:12px;">📁 Browse Files...</button>
  </div>
  <div id="file-list" style="max-height:150px;overflow-y:auto;margin-bottom:12px;border:1px solid var(--vscode-input-border);padding:4px;"></div>
  <div style="font-size:12px;margin-bottom:12px;color:var(--vscode-descriptionForeground);">Selected: <span id="selected-count">0</span> files</div>
  <div style="display:flex;justify-content:flex-end;gap:8px;">
    <button id="cancel" style="padding:4px 12px;background:transparent;color:var(--vscode-button-foreground);border:1px solid var(--vscode-button-border);border-radius:2px;cursor:pointer;">Cancel</button>
    <button id="next" disabled style="padding:4px 12px;background:var(--vscode-button-secondaryBackground);color:var(--vscode-button-foreground);border:none;border-radius:2px;cursor:pointer;opacity:0.5;">Next: Let AI Decide</button>
  </div>
</div>
<script>
(function() {
  const vscode = acquireVsCodeApi();
  let availableFiles = [];
  let selectedFiles = [];
  function render() {
    const list = document.getElementById('file-list');
    const countEl = document.getElementById('selected-count');
    const nextBtn = document.getElementById('next');
    list.innerHTML = availableFiles.map(f => '<div style="display:flex;align-items:center;padding:2px 0;"><input type="checkbox" id="chk-' + f.replace(/[^a-zA-Z0-9.-]/g, '_') + '" ' + (selectedFiles.includes(f) ? 'checked' : '') + ' style="margin-right:8px;"><label style="font-size:12px;">' + (f.replace(/</g, '&lt;')) + '</label></div>').join('');
    list.querySelectorAll('input[type=checkbox]').forEach((cb, i) => {
      cb.addEventListener('change', () => {
        const path = availableFiles[i];
        selectedFiles = selectedFiles.includes(path) ? selectedFiles.filter(x => x !== path) : selectedFiles.concat(path);
        countEl.textContent = selectedFiles.length;
        nextBtn.disabled = selectedFiles.length === 0;
        nextBtn.style.opacity = selectedFiles.length === 0 ? '0.5' : '1';
        nextBtn.style.backgroundColor = selectedFiles.length === 0 ? 'var(--vscode-button-secondaryBackground)' : 'var(--vscode-button-background)';
      });
    });
    countEl.textContent = selectedFiles.length;
    nextBtn.disabled = selectedFiles.length === 0;
    nextBtn.style.opacity = selectedFiles.length === 0 ? '0.5' : '1';
    nextBtn.style.backgroundColor = selectedFiles.length === 0 ? 'var(--vscode-button-secondaryBackground)' : 'var(--vscode-button-background)';
  }
  window.addEventListener('message', function(e) {
    if (e.data && e.data.type === 'browseFilesResult' && Array.isArray(e.data.paths)) {
      availableFiles = [...new Set(availableFiles.concat(e.data.paths))];
      selectedFiles = [...new Set(selectedFiles.concat(e.data.paths))];
      render();
    }
  });
  document.getElementById('browse-files').onclick = function() { vscode.postMessage({ type: 'browseFiles' }); };
  document.getElementById('cancel').onclick = function() { vscode.postMessage({ type: 'cancel' }); };
  document.getElementById('next').onclick = function() { vscode.postMessage({ type: 'next', paths: selectedFiles }); };
  render();
})();
</script>
</body>
</html>`;
}

export function activate(context: vscode.ExtensionContext): void {
  // Invalidate any config cache when Confluence settings change
  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration('confluence')) {
        // Config is read fresh in getConfluenceConfigAsync; cache invalidation can be added there if needed
      }
    })
  );

  // Optional: warn once if credentials are missing (e.g. URL set but no token)
  const { url, email } = getConfluenceCredentialsFromSettings();
  if (url && email) {
    getConfluenceConfigAsync(context).then((config) => {
      if (!config.auth && url) {
        vscode.window.showInformationMessage(
          'Confluence: Add and store your API token in Confluence settings to enable publishing.'
        );
      }
    });
  }

  // Register commands
  context.subscriptions.push(
    vscode.commands.registerCommand('confluence.saveToIntelligent', () => {
      const panel = vscode.window.createWebviewPanel('confluenceSave', 'Save to Confluence - Intelligent Mode', vscode.ViewColumn.One, { enableScripts: true });
      panel.webview.html = getConfluenceFileSelectorWebviewHtml(panel.webview);
      panel.webview.onDidReceiveMessage(async (msg) => {
        if (msg.type === 'browseFiles') {
          panel.reveal();
          const defaultUri = vscode.workspace.workspaceFolders?.[0]?.uri;
          const uris = await vscode.window.showOpenDialog({
            canSelectMany: true,
            openLabel: 'Select files',
            defaultUri,
            title: 'Open'
          });
          if (uris && uris.length) {
            panel.webview.postMessage({ type: 'browseFilesResult', paths: uris.map(u => u.fsPath) });
          }
        } else if (msg.type === 'cancel') {
          panel.dispose();
        } else if (msg.type === 'next' && Array.isArray(msg.paths)) {
          panel.dispose();
          vscode.window.showInformationMessage('Selected ' + msg.paths.length + ' file(s).');
        }
      });
    }),
    vscode.commands.registerCommand('confluence.saveSelection', () => {
      const selection = vscode.window.activeTextEditor?.selection;
      if (selection && !selection.isEmpty) {
        vscode.window.showInformationMessage('Saving selection to Confluence...');
      }
    }),
    vscode.commands.registerCommand('confluence.documentProject', () => {
      vscode.window.showInformationMessage('Documenting project intelligently...');
    }),
    vscode.commands.registerCommand('confluence.viewCreations', () => {
      vscode.window.showInformationMessage('Opening Intelligent Creations dashboard...');
    }),
    vscode.commands.registerCommand('confluence.configureSettings', () => {
      vscode.commands.executeCommand('workbench.action.openSettings', 'confluence');
    }),
    vscode.commands.registerCommand('confluence.configureProjectSettings', () => {
      openConfluenceConfigPanel(context);
    })
  );

  console.log('Confluence Chat-Only Integration activated');
}

export function deactivate(): void {}
