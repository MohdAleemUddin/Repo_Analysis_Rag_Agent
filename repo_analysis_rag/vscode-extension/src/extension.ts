import * as vscode from "vscode";

import { getConfluenceCredentialsFromSettings, getStoredToken, setStoredToken, validateConfluenceUrl } from "./confluence/confluence-settings";
import { ChatPanelViewProvider } from "./webview/ChatPanelViewProvider";

/** US-10: Test Confluence connection via command (no webview panel). */
async function runTestConnection(context: vscode.ExtensionContext): Promise<void> {
    const cfg = vscode.workspace.getConfiguration('confluence');
    const baseUrl = (cfg.get<string>('apiBaseUrl') ?? 'http://127.0.0.1:8000').replace(/\/$/, '');
    const { url, email } = getConfluenceCredentialsFromSettings();
    const token = await getStoredToken(context);
    const validationErrors: string[] = [];
    if (!url || !url.trim()) validationErrors.push('Confluence URL is required.');
    if (!email || !email.trim()) validationErrors.push('Email is required.');
    if (!token || !token.trim()) validationErrors.push('API token is required. Store it in Confluence settings.');
    if (validationErrors.length > 0) {
        vscode.window.showErrorMessage(`Confluence: ${validationErrors.join(' ')}`);
        return;
    }
    const urlValidation = validateConfluenceUrl(url);
    if (!urlValidation.valid) {
        vscode.window.showErrorMessage(`Confluence: ${urlValidation.error}`);
        return;
    }
    try {
        const res = await fetch(`${baseUrl}/confluence/config/test-connection`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url.trim(), email: email.trim(), api_token: token.trim() }),
        });
        const data = (await res.json()) as { ok?: boolean; error?: string; latency_ms?: number; spaces?: Array<{ key?: string; name?: string }> };
        if (!res.ok) {
            vscode.window.showErrorMessage(`Confluence: ${(data as { error?: string }).error || res.statusText}`);
            return;
        }
        if (data.ok) {
            const spaces = data.spaces || [];
            await context.globalState.update('confluence.cachedSpaces', spaces);
            const edition = url.trim().toLowerCase().includes('.atlassian.net') ? 'Cloud' : 'Server';
            const extra: string[] = [`Detected: ${edition}`];
            if (data.latency_ms != null) extra.push(`Latency: ${data.latency_ms} ms`);
            if (spaces.length) extra.push(`Spaces: ${spaces.map((s) => s.key || s.name).filter(Boolean).join(', ')}`);
            vscode.window.showInformationMessage(`Confluence: Connection successful. ${extra.join('. ')}`);
        } else {
            vscode.window.showErrorMessage(`Confluence: ${data.error || 'Connection failed'}`);
        }
    } catch (e) {
        vscode.window.showErrorMessage(`Confluence: ${String(e)}`);
    }
}

export function activate(context: vscode.ExtensionContext) {
    const log = vscode.window.createOutputChannel("Offline Folder RAG");
    context.subscriptions.push(log);
    const confluenceOutput = vscode.window.createOutputChannel("Confluence");
    context.subscriptions.push(confluenceOutput);
    confluenceOutput.appendLine("[Confluence] Output channel ready. Confluence flow logs will appear here.");
    confluenceOutput.show(true);
    try {
        log.appendLine("[Offline RAG] Activating...");
        log.appendLine("[Offline RAG] RAG request/response logs will appear here when you send messages.");
        const provider = new ChatPanelViewProvider(context, context.extensionUri, confluenceOutput, log);
        const command = vscode.commands.registerCommand("offlineFolderRag.openChat", () => {
            provider.show();
        });

        context.subscriptions.push(command);

        // Run full index in background when extension loads (if workspace folder open and rag.indexOnLoad is true)
        const indexOnLoadDelayMs = 2000;
        const indexOnLoadTimer = setTimeout(() => {
            void provider.runInitialFullIndex();
        }, indexOnLoadDelayMs);
        context.subscriptions.push({ dispose: () => clearTimeout(indexOnLoadTimer) });

        const analyzeCommand = vscode.commands.registerCommand("offlineFolderRag.analyzeFolder", () => {
            vscode.window.showInformationMessage('Analyzing folder...');
        });
        context.subscriptions.push(analyzeCommand);

        const saveToIntelligentCommand = vscode.commands.registerCommand('confluence.saveToIntelligent', () => {
            provider.show();
            void provider.triggerConfluenceSave();
        });
        context.subscriptions.push(saveToIntelligentCommand);

        const saveSelectionCommand = vscode.commands.registerCommand('confluence.saveSelection', () => {
            const editor = vscode.window.activeTextEditor;
            const selection = editor?.selection;
            const text = selection && !selection.isEmpty && editor ? editor.document.getText(selection) : '';
            context.globalState.update('rag-confluence.preloadedSelection', text || undefined);
            provider.show();
            void provider.triggerConfluenceSave();
        });
        context.subscriptions.push(saveSelectionCommand);

        const documentProjectCommand = vscode.commands.registerCommand('confluence.documentProject', () => {
            provider.show();
            void provider.triggerDocumentProject();
        });
        context.subscriptions.push(documentProjectCommand);

        const viewCreationsCommand = vscode.commands.registerCommand('confluence.viewCreations', () => {
            provider.show();
            void provider.triggerViewCreations();
        });
        context.subscriptions.push(viewCreationsCommand);

        const exportExamplesCommand = vscode.commands.registerCommand('confluence.exportExamples', () => {
            provider.show();
            void provider.triggerExportExamples();
        });
        context.subscriptions.push(exportExamplesCommand);

        const importExamplesCommand = vscode.commands.registerCommand('confluence.importExamples', () => {
            provider.show();
            void provider.triggerImportExamples();
        });
        context.subscriptions.push(importExamplesCommand);

        const configureSettingsCommand = vscode.commands.registerCommand('confluence.configureSettings', () => {
            vscode.commands.executeCommand('workbench.action.openSettings', 'confluence');
        });
        context.subscriptions.push(configureSettingsCommand);

        const configureProjectSettingsCommand = vscode.commands.registerCommand('confluence.configureProjectSettings', () => {
            vscode.commands.executeCommand('workbench.action.openSettings', 'confluence');
        });
        context.subscriptions.push(configureProjectSettingsCommand);

        const testConnectionCommand = vscode.commands.registerCommand('confluence.testConnection', async () => {
            await runTestConnection(context);
        });
        context.subscriptions.push(testConnectionCommand);

        const storeApiTokenCommand = vscode.commands.registerCommand('confluence.storeApiToken', async () => {
            const value = await vscode.window.showInputBox({
                prompt: 'Enter your Confluence API token (from id.atlassian.com/manage-profile/security/api-tokens)',
                password: true,
                ignoreFocusOut: true,
            });
            if (value !== undefined && value.trim().length > 0) {
                await setStoredToken(context, value.trim());
                vscode.window.showInformationMessage('Confluence API token stored.');
            }
        });
        context.subscriptions.push(storeApiTokenCommand);

        const citationCommand = vscode.commands.registerCommand('citation.open', async (args) => {
            const doc = await vscode.workspace.openTextDocument(args.path);
            const editor = await vscode.window.showTextDocument(doc);
            const start = new vscode.Position(args.startLine - 1, 0);  // Zero-based index
            const end = new vscode.Position(args.endLine - 1, 0);  // Zero-based index
            editor.selection = new vscode.Selection(start, end);
            editor.revealRange(new vscode.Range(start, end));  // Highlight the range
        });
        context.subscriptions.push(citationCommand);

        log.appendLine("[Offline RAG] Activated successfully.");
    } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        log.appendLine(`[Offline RAG] ACTIVATION FAILED: ${msg}`);
        if (err instanceof Error && err.stack) {
            log.appendLine(err.stack);
        }
        vscode.window.showErrorMessage(`Offline RAG activation failed: ${msg}`);
    }
}

export function deactivate() {
    return undefined;
}
