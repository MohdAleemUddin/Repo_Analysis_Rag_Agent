"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = require("vscode");
function getConfluenceFileSelectorWebviewHtml(webview) {
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
function activate(context) {
    // Register commands
    context.subscriptions.push(vscode.commands.registerCommand('confluence.saveToIntelligent', () => {
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
            }
            else if (msg.type === 'cancel') {
                panel.dispose();
            }
            else if (msg.type === 'next' && Array.isArray(msg.paths)) {
                panel.dispose();
                vscode.window.showInformationMessage('Selected ' + msg.paths.length + ' file(s).');
            }
        });
    }), vscode.commands.registerCommand('confluence.saveSelection', () => {
        const selection = vscode.window.activeTextEditor?.selection;
        if (selection && !selection.isEmpty) {
            vscode.window.showInformationMessage('Saving selection to Confluence...');
        }
    }), vscode.commands.registerCommand('confluence.documentProject', () => {
        vscode.window.showInformationMessage('Documenting project intelligently...');
    }), vscode.commands.registerCommand('confluence.viewCreations', () => {
        vscode.window.showInformationMessage('Opening Intelligent Creations dashboard...');
    }), vscode.commands.registerCommand('confluence.configureSettings', () => {
        vscode.commands.executeCommand('workbench.action.openSettings', 'confluence');
    }));
    // Placeholder for chat-only UI integration
    // In the real RAG extension, this would be where we hook into the chat input area
    console.log('Confluence Chat-Only Integration activated');
}
function deactivate() { }
