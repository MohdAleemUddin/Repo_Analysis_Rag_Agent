import * as vscode from 'vscode';
import * as fs from 'fs';
import { ConfluenceChatViewProvider, asDisposable, getAnalysisMessageHtml, getProgressMessageHtml, getSuccessMessageHtml, getErrorMessageHtml } from './confluence/ConfluenceChatViewProvider';
import { intelligentAnalyze, intelligentCreate } from './confluence/confluence-api';
import type { AnalyzeResponse, IntelligenceErrorResponse } from './confluence/types';

const PROGRESS_STEPS = [
  { label: 'Analyzing content structure...', status: 'pending' as const },
  { label: 'Selecting optimal template...', status: 'pending' as const },
  { label: 'Applying intelligent formatting...', status: 'pending' as const },
  { label: 'Uploading to Confluence...', status: 'pending' as const },
];

function getApiConfig(): { baseUrl: string } {
  const config = vscode.workspace.getConfiguration('confluence');
  const baseUrl = config.get<string>('apiBaseUrl') || 'http://localhost:8000';
  return { baseUrl };
}

export function activate(context: vscode.ExtensionContext): void {
  const provider = new ConfluenceChatViewProvider(context.extensionUri);

  let selectedFilePaths: string[] = [];
  let analyzeResult: AnalyzeResponse | null = null;
  let fileContents: string[] = [];

  provider.setMessageHandler(async (msg: unknown) => {
    const m = msg as { type: string; paths?: string[]; title?: string; space?: string; url?: string };
    if (!m || !m.type) return;

    if (m.type === 'confluenceSaveClicked') {
      provider.startFlow();
      return;
    }

    if (m.type === 'browseFiles') {
      const panel = provider.getOrCreatePanel();
      panel.reveal();
      const defaultUri = vscode.workspace.workspaceFolders?.[0]?.uri;
      const uris = await vscode.window.showOpenDialog({
        canSelectMany: true,
        openLabel: 'Select files',
        defaultUri,
        title: 'Select files for Confluence',
      });
      if (uris && uris.length) {
        const paths = uris.map((u) => u.fsPath);
        provider.postMessage({ type: 'browseFilesResult', paths });
      }
      return;
    }

    if (m.type === 'cancel') {
      provider.postMessage({ type: 'reset' });
      selectedFilePaths = [];
      analyzeResult = null;
      fileContents = [];
      return;
    }

    if (m.type === 'next' && Array.isArray(m.paths) && m.paths.length) {
      selectedFilePaths = m.paths;
      const config = getApiConfig();
      const progressId = 'msg-progress';

      try {
        fileContents = selectedFilePaths
          .filter((p) => fs.existsSync(p))
          .map((p) => fs.readFileSync(p, 'utf-8'));

        if (fileContents.length === 0) {
          provider.postMessage({
            type: 'append',
            id: 'msg-error',
            html: getErrorMessageHtml({
              message: 'No readable file content found.',
              suggestion: 'Ensure the selected files exist and are text files.',
            }),
          });
          return;
        }

        provider.postMessage({
          type: 'append',
          id: progressId,
          html: getProgressMessageHtml(
            PROGRESS_STEPS.map((s) => ({ ...s, status: s.label.includes('Analyzing') ? 'active' : 'pending' })),
            25,
            12
          ),
        });

        const result = await intelligentAnalyze(config, { file_contents: fileContents });
        const isError = result && 'error' in result;
        if (isError) {
          const err = result as IntelligenceErrorResponse;
          provider.postMessage({
            type: 'append',
            id: 'msg-error',
            html: getErrorMessageHtml({
              message: err.message || 'Analysis failed',
              suggestion: err.intelligence_suggestion || 'Try different files.',
            }),
          });
          return;
        }

        analyzeResult = result as AnalyzeResponse;
        const analysis = analyzeResult.intelligence_analysis;
        const rec = analyzeResult.intelligent_recommendation;

        provider.postMessage({ type: 'update', id: progressId, html: getProgressMessageHtml(PROGRESS_STEPS.map((s) => ({ ...s, status: 'completed' })), 100, 0) });
        provider.postMessage({
          type: 'append',
          id: 'msg-analysis',
          html: getAnalysisMessageHtml({
            content_types: analysis.content_types || [],
            detected_patterns: analysis.detected_patterns || [],
            intelligent_title: analysis.intelligent_title || 'Documentation',
            template_name: rec.template_name || '',
            intelligence_reason: rec.intelligence_reason || '',
          }),
        });
      } catch (e) {
        provider.postMessage({
          type: 'append',
          id: 'msg-error',
          html: getErrorMessageHtml({
            message: e instanceof Error ? e.message : 'Analysis failed',
            suggestion: 'Check the edge agent is running and try again.',
          }),
        });
      }
      return;
    }

    if (m.type === 'createPage' && m.title && analyzeResult && fileContents.length) {
      const createProgressId = 'msg-create-progress';
      provider.postMessage({
        type: 'append',
        id: createProgressId,
        html: getProgressMessageHtml(
          PROGRESS_STEPS.map((s, i) => ({
            label: s.label,
            status: i < 2 ? 'completed' : i === 2 ? 'active' : 'pending',
          })),
          75,
          5
        ),
      });

      const config = getApiConfig();
      const mergedContent = fileContents.join('\n\n---\n\n');
      const rec = analyzeResult.intelligent_recommendation;
      const intelligence_context: { suggested_title: string; title_override: string; template_id?: string; template_name?: string } = {
        suggested_title: m.title,
        title_override: m.title,
      };
      if (rec?.template_id) intelligence_context.template_id = rec.template_id;
      if (rec?.template_name) intelligence_context.template_name = rec.template_name;
      try {
        const createResult = await intelligentCreate(config, {
          content: mergedContent,
          intelligent_mode: true,
          auto_title: false,
          space: m.space || 'DEV',
          intelligence_context,
        });

        provider.postMessage({
          type: 'update',
          id: createProgressId,
          html: getProgressMessageHtml(
            PROGRESS_STEPS.map((s) => ({ ...s, status: 'completed' })),
            100,
            0
          ),
        });
        const analysis = analyzeResult.intelligence_analysis;
        const decisions = [
          rec?.intelligence_reason,
          analysis?.ai_reasoning,
          `Template: ${rec?.template_name || ''}`,
        ].filter(Boolean) as string[];

        provider.postMessage({
          type: 'append',
          id: 'msg-success',
          html: getSuccessMessageHtml({
            title: (createResult as { title?: string }).title || m.title,
            space: (createResult as { space?: string }).space || m.space || 'DEV',
            url: (createResult as { url?: string }).url || config.baseUrl,
            decisions,
          }),
        });
      } catch (e) {
        provider.postMessage({
          type: 'append',
          id: 'msg-error',
          html: getErrorMessageHtml({
            message: e instanceof Error ? e.message : 'Create failed',
            suggestion: 'Check Confluence URL and credentials.',
          }),
        });
      }
      return;
    }

    if (m.type === 'editTitle' && analyzeResult) {
      const current = analyzeResult.intelligence_analysis?.intelligent_title || 'Documentation';
      const newTitle = await vscode.window.showInputBox({
        prompt: 'Edit title',
        value: current,
      });
      if (newTitle) {
        analyzeResult.intelligence_analysis.intelligent_title = newTitle;
        const analysis = analyzeResult.intelligence_analysis;
        const rec = analyzeResult.intelligent_recommendation;
        provider.postMessage({
          type: 'update',
          id: 'msg-analysis',
          html: getAnalysisMessageHtml({
            content_types: analysis.content_types || [],
            detected_patterns: analysis.detected_patterns || [],
            intelligent_title: newTitle,
            template_name: rec.template_name || '',
            intelligence_reason: rec.intelligence_reason || '',
          }),
        });
      }
      return;
    }

    if (m.type === 'openInBrowser' && m.url) {
      vscode.env.openExternal(vscode.Uri.parse(m.url));
      return;
    }

    if (m.type === 'copyLink' && m.url) {
      vscode.env.clipboard.writeText(m.url);
      vscode.window.showInformationMessage('Link copied to clipboard.');
      return;
    }

    if (m.type === 'retry') {
      provider.postMessage({ type: 'reset' });
      provider.startFlow();
      selectedFilePaths = [];
      analyzeResult = null;
      fileContents = [];
      return;
    }
  });

  context.subscriptions.push(
    vscode.commands.registerCommand('confluence.saveToIntelligent', () => {
      provider.startFlow();
    }),
    vscode.commands.registerCommand('confluence.saveSelection', () => {
      const selection = vscode.window.activeTextEditor?.selection;
      if (selection && !selection.isEmpty) {
        provider.startFlow();
        vscode.window.showInformationMessage('Use file selector to add selection.');
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
    asDisposable(provider)
  );
}

export function deactivate(): void {}
