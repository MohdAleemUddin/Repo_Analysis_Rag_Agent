import * as path from "path";
import messages from "../../confluence/simple-language.json";
import type { IntelligenceMetrics } from "../../confluence/types";
import type { DocumentProjectResponse } from "../../confluence/confluence-api";
import { getAiFormattedBadgeHtml, getLearningIndicatorHtml, getConfidenceColor } from "../../confluence/badges";

function esc(s: string): string {
    return String(s)
        .replace(/\\/g, "\\\\")
        .replace(/"/g, "\\\"")
        .replace(/'/g, "\\'");
}

export interface ConfluenceFileSelectorOptions {
    contextSuggestions?: { projectTypeLabel?: string };
    hasPreloadedSelection?: boolean;
    shouldSuggestReadme?: boolean;
}

export function getConfluenceFileSelectorHtml(
    availableFiles: string[] = [],
    usageCountOrNonce: number | string = 0,
    nonceParam?: string,
    options?: ConfluenceFileSelectorOptions
): string {
    const usageCount = typeof usageCountOrNonce === 'number' ? usageCountOrNonce : 0;
    const nonce = typeof usageCountOrNonce === 'string' ? usageCountOrNonce : (nonceParam ?? '');
    const safeId = (f: string) => f.replace(/[^a-zA-Z0-9._-]/g, '_').slice(-40);
    const htmlAttr = (s: string) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const fileListHtml = availableFiles.map(file => {
        const displayName = path.basename(file);
        const id = 'file-' + safeId(file);
        return `
        <div style="display: flex; align-items: center; padding: 4px 0; border-bottom: 1px solid var(--vscode-widget-border);">
            <input type="checkbox" id="${id}" value="${htmlAttr(file)}" style="margin-right: 10px; cursor: pointer;">
            <label for="${id}" style="font-size: 13px; cursor: pointer; flex: 1;">${htmlAttr(displayName)}</label>
        </div>
    `;
    }).join('');
    const showIntelligentBadge = usageCount >= 1;
    const showAddRelated = usageCount >= 2;
    const projectLabel = options?.contextSuggestions?.projectTypeLabel;
    const hasPreloaded = options?.hasPreloadedSelection;
    const contextBadges: string[] = [];
    if (projectLabel) contextBadges.push(`Intelligently detected: ${htmlAttr(projectLabel)}`);
    if (hasPreloaded) contextBadges.push('Based on your conversation');
    if (options?.shouldSuggestReadme) contextBadges.push('README suggested');
    const contextBadgesHtml = contextBadges.length > 0
        ? contextBadges.map(b => `<div style="font-size: 11px; margin-bottom: 8px; padding: 2px 6px; background: var(--vscode-badge-background); color: var(--vscode-badge-foreground); border-radius: 4px; display: inline-block;">${b}</div>`).join(' ')
        : '';

    return `
        <div data-confluence-id="file-selector" class="confluence-card confluence-file-selector-card" style="border: 1px solid var(--vscode-widget-border); border-radius: 8px; padding: 16px; background-color: var(--vscode-editor-background); width: 100%; box-sizing: border-box; box-shadow: 0 4px 12px rgba(0,0,0,0.2); margin: 10px 0;">
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <span style="font-size: 18px; margin-right: 8px;">💾</span>
                <h3 style="margin: 0; font-size: 15px; font-weight: 600;">Save to Confluence - Intelligent Mode</h3>
            </div>
            ${showIntelligentBadge ? '<div style="font-size: 11px; margin-bottom: 8px; padding: 2px 6px; background: var(--vscode-badge-background); color: var(--vscode-badge-foreground); border-radius: 4px; display: inline-block;">Intelligent suggestions</div> ' : ''}${contextBadgesHtml}
            
            <p style="margin: 0 0 12px 0; font-size: 13px; color: var(--vscode-foreground);">${esc(messages.phrases.firstInteraction.fileSelector)}</p>
            
            <div style="margin-bottom: 16px;">
                <button type="button" data-action="confluenceBrowse" style="width: 100%; padding: 8px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); border: 1px solid var(--vscode-button-border); border-radius: 4px; cursor: pointer; font-size: 13px; display: flex; align-items: center; justify-content: center; gap: 8px;">
                    <span>📁</span> Browse Files...
                </button>
            </div>

            <div id="confluence-file-list" class="confluence-file-list" style="max-height: 200px; overflow-y: auto; margin-bottom: 16px; border: 1px solid var(--vscode-input-border); border-radius: 4px; padding: 4px 8px; background: var(--vscode-input-background);">
                ${fileListHtml}
            </div>

            ${showAddRelated ? '<div style="margin-bottom: 12px;"><button type="button" data-action="confluenceAddRelatedFiles" style="font-size: 12px; padding: 4px 8px; cursor: pointer; border: 1px solid var(--vscode-button-border); border-radius: 2px; background: transparent;">Add related files</button></div>' : ''}

            <div style="font-size: 13px; margin-bottom: 20px; padding: 12px; background: var(--vscode-textBlockQuote-background); border-radius: 6px; border-left: 3px solid var(--vscode-accent);">
                <div id="confluence-selection-count" class="confluence-selection-count" style="font-weight: 600; margin-bottom: 8px;">Selected: 0 files</div>
                <div style="color: var(--vscode-descriptionForeground); font-size: 12px;">Selected files will be:</div>
                <ul style="margin: 4px 0 0 0; padding-left: 20px; color: var(--vscode-descriptionForeground); font-size: 12px; line-height: 1.6;">
                    <li>Automatically analyzed</li>
                    <li>Intelligently formatted</li>
                    <li>Perfectly organized</li>
                </ul>
            </div>

            <div style="display: flex; justify-content: flex-end; gap: 10px;">
                <button type="button" data-action="confluenceCancel" style="padding: 8px 16px; background: transparent; color: var(--vscode-foreground); border: 1px solid var(--vscode-button-border); border-radius: 4px; cursor: pointer; font-size: 13px;">
                    Cancel
                </button>
                <button id="confluence-next-button" class="confluence-next-button" type="button" data-action="confluenceNext" disabled style="padding: 8px 16px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 4px; cursor: not-allowed; opacity: 0.5; font-size: 13px; font-weight: 600;">
                    Next: Let AI Decide
                </button>
            </div>
            <script ${nonce ? `nonce="${nonce}"` : ''}>
                const vscode = acquireVsCodeApi();
                window.vscode = vscode;

                window.handleConfluenceBrowse = function() {
                    vscode.postMessage({ type: 'confluenceBrowse' });
                };

                const updateSelection = function() {
                    const checkboxes = document.querySelectorAll('#confluence-file-list input[type="checkbox"]');
                    const selected = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
                    const countEl = document.getElementById('confluence-selection-count');
                    if (countEl) countEl.textContent = 'Selected: ' + selected.length + ' files';
                    const nextButton = document.getElementById('confluence-next-button');
                    if (nextButton) {
                        nextButton.disabled = selected.length === 0;
                        nextButton.style.cursor = selected.length === 0 ? 'not-allowed' : 'pointer';
                        nextButton.style.opacity = selected.length === 0 ? 0.5 : 1;
                    }
                };

                window.updateConfluenceSelection = updateSelection;

                window.submitConfluenceSelection = function() {
                    const checkboxes = document.querySelectorAll('#confluence-file-list input[type="checkbox"]');
                    const selected = Array.from(checkboxes).filter(cb => cb.checked).map(cb => cb.value);
                    vscode.postMessage({ type: 'confluenceNext', files: selected });
                };

                updateSelection();
            </script>
        </div>
    `;
}

function htmlEsc(s: string): string {
    return String(s)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

export interface ConfluenceAnalysisData {
    content_types?: string[];
    detected_patterns?: string[];
    intelligent_title?: string;
    template_name?: string;
    intelligence_reason?: string;
    intelligence_confidence?: number;
    confidence_breakdown?: { content_match?: number; structure_match?: number; context_match?: number };
    ai_reasoning?: string;
    file_count?: number;
}

export interface ConfluenceAnalysisOptions {
    preferredSpace?: string;
    spaces?: Array<{ key: string; name?: string }>;
}

export function getConfluenceAnalysisHtml(
    files: string[] = [],
    analysis: ConfluenceAnalysisData = {},
    nonce: string = '',
    usageCount: number = 0,
    options?: ConfluenceAnalysisOptions
): string {
    const fileList = files.length > 0 ? files.map(f => path.basename(f)).join(', ') : 'No files selected';
    const spaces = options?.spaces && options.spaces.length > 0
        ? options.spaces
        : [{ key: 'DEV', name: 'DEV' }, { key: 'DOCS', name: 'DOCS' }];
    const preferredVal = options?.preferredSpace && spaces.some(s => (s.key || '').toUpperCase() === (options.preferredSpace || '').toUpperCase())
        ? options.preferredSpace
        : (spaces[0]?.key || 'DEV');
    const spaceOptionsHtml = spaces.map(s => {
        const k = s.key || s.name || 'DEV';
        const selected = (k.toUpperCase() === preferredVal.toUpperCase()) ? ' selected' : '';
        return `<option value="${esc(k)}"${selected}>${esc(s.name || k)}</option>`;
    }).join('');
    const contentTypes = analysis.content_types || [];
    const patterns = analysis.detected_patterns || [];
    const detectedList = patterns.length > 0
        ? patterns.map(p => `<li>${esc(p)}</li>`).join('')
        : (contentTypes.length > 0 ? contentTypes.map(c => `<li>${esc(c)}</li>`).join('') : '<li>Mixed content</li>');
    const templateName = analysis.template_name || 'API Project Documentation';
    const intelligenceReason = analysis.intelligence_reason || '(Matches similar successful examples)';
    const suggestedTitle = analysis.intelligent_title || 'API Service Setup & Configuration';
    const fileCount = analysis.file_count ?? files.length;
    const cb = analysis.confidence_breakdown;
    const cbVals = cb ? [cb.content_match, cb.structure_match, cb.context_match].filter((n): n is number => typeof n === 'number') : [];
    const overallConf = analysis.intelligence_confidence ?? (cbVals.length > 0 ? cbVals.reduce((a, b) => a + b, 0) / cbVals.length : undefined);
    const isLowConfidence = typeof overallConf === 'number' && overallConf < 0.7;
    const explainContent = htmlEsc(analysis.ai_reasoning || intelligenceReason);
    const showConfidence = usageCount >= 1 && typeof overallConf === 'number';
    const showLowConfidence = usageCount >= 1 && isLowConfidence;
    const showExplainChoice = usageCount >= 2;
    const confPct = typeof overallConf === 'number' ? Math.round(overallConf * 100) : 0;
    const confColor = getConfidenceColor(confPct);

    return `
        <div class="confluence-card confluence-analysis-card" style="border: 1px solid var(--vscode-widget-border); border-radius: 8px; padding: 16px; background-color: var(--vscode-editor-background); max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
            <script ${nonce ? `nonce="${nonce}"` : ''}>
                const vscode = acquireVsCodeApi();
                window.vscode = vscode;
            </script>
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <span style="font-size: 18px; margin-right: 8px;">🤖</span>
                <h3 style="margin: 0; font-size: 15px; font-weight: 600;">Intelligent Analysis Complete</h3>
            </div>

            ${fileCount > 1 ? `<div style="font-size: 12px; margin-bottom: 8px; color: var(--vscode-descriptionForeground);">Intelligently combining ${fileCount} files as comprehensive documentation</div>` : ''}
            <div style="font-size: 13px; margin-bottom: 12px; color: var(--vscode-foreground);">
                <strong>Files:</strong> ${esc(fileList)}
            </div>
            
            <div style="font-size: 13px; margin-bottom: 16px;">
                <div style="font-weight: 600; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                    <span>🧠</span> AI Detected:
                </div>
                <ul style="margin: 0; padding-left: 24px; line-height: 1.6;">${detectedList}</ul>
            </div>

            <div style="font-size: 13px; margin-bottom: 16px; padding: 12px; background: var(--vscode-textBlockQuote-background); border-radius: 6px; border-left: 3px solid var(--vscode-button-background);">
                <div style="font-weight: 600; color: var(--vscode-textLink-foreground); margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    <span>🎯</span> Intelligent Format Selected:
                </div>
                <div style="font-weight: 500;">"${esc(templateName)}" template</div>
                <div style="font-size: 11px; opacity: 0.8; margin-top: 2px;">(${esc(intelligenceReason)})</div>
                ${showExplainChoice ? `
                <details style="margin-top: 8px; font-size: 12px;">
                    <summary style="cursor: pointer;">Explain AI Choice</summary>
                    <p style="margin: 6px 0 0 0; color: var(--vscode-foreground);">${explainContent}</p>
                </details>
                ` : ''}
            </div>

            ${showConfidence ? `
            <div style="font-size: 12px; margin-bottom: 16px; padding: 10px; background: var(--vscode-editor-inactiveSelectionBackground); border-radius: 4px;" title="${esc((messages.phrases as { confidenceTooltip?: string }).confidenceTooltip || 'Intelligence Confidence: How sure AI is about this decision')}">
                <div style="font-weight: 600; margin-bottom: 4px;">Confidence: <span style="color: ${confColor};">${confPct}%</span></div>
                ${cb && (cb.content_match !== undefined || cb.structure_match !== undefined || cb.context_match !== undefined) ? `
                <div style="font-size: 11px; color: var(--vscode-descriptionForeground);">
                    ${cb.content_match !== undefined ? `Content: ${Math.round(cb.content_match * 100)}%` : ''}${cb.content_match !== undefined && (cb.structure_match !== undefined || cb.context_match !== undefined) ? ' · ' : ''}${cb.structure_match !== undefined ? `Structure: ${Math.round(cb.structure_match * 100)}%` : ''}${cb.structure_match !== undefined && cb.context_match !== undefined ? ' · ' : ''}${cb.context_match !== undefined ? `Context: ${Math.round(cb.context_match * 100)}%` : ''}
                </div>
                ` : ''}
            </div>
            ` : ''}

            ${showLowConfidence ? `
            <div style="font-size: 12px; margin-bottom: 16px; padding: 10px; background: var(--vscode-inputValidation-warningBackground); border: 1px solid var(--vscode-inputValidation-warningBorder); border-radius: 4px;">
                <div style="font-weight: 600; color: var(--vscode-editorWarning-foreground); margin-bottom: 4px;">Intelligence Confidence Low</div>
                <div style="font-size: 11px; color: var(--vscode-foreground); margin-bottom: 8px;">Consider reviewing the suggested template. You can still proceed or try different files.</div>
                <button type="button" data-action="confluenceCancel" style="font-size: 12px; padding: 4px 8px; cursor: pointer; border: 1px solid var(--vscode-button-border); border-radius: 2px; background: transparent;">Try with different files</button>
            </div>
            ` : ''}

            <div style="font-size: 13px; margin-bottom: 16px;">
                <div style="font-weight: 600; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                    <span>📝</span> Suggested Title:
                    <span style="font-size: 10px; padding: 2px 6px; background: var(--vscode-badge-background); color: var(--vscode-badge-foreground); border-radius: 4px;">AI Suggested</span>
                </div>
                <div id="confluence-title-display" class="confluence-title-display" contenteditable="true" role="textbox" aria-label="Page title" style="padding: 8px 12px; border: 1px solid var(--vscode-input-border); border-radius: 4px; background: var(--vscode-input-background); font-family: monospace; min-height: 1.2em; outline: none;">${htmlEsc(suggestedTitle)}</div>
                <div id="confluence-title-counter" style="font-size: 11px; color: var(--vscode-descriptionForeground); margin-top: 4px;"><span id="confluence-title-count">${suggestedTitle.length}</span> / 255</div>
            </div>

            <div style="font-size: 13px; margin-bottom: 20px;">
                <div style="font-weight: 600; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                    <span>📍</span> Confluence Space:
                </div>
                ${options?.preferredSpace ? `<div style="font-size: 11px; margin-bottom: 4px; color: var(--vscode-descriptionForeground);">Previously used: ${esc(options.preferredSpace)}</div>` : ''}
                <select id="confluence-space-select" class="confluence-space-select" style="width: 100%; padding: 8px; background: var(--vscode-select-background); color: var(--vscode-select-foreground); border: 1px solid var(--vscode-select-border); border-radius: 4px; cursor: pointer;">
                    ${spaceOptionsHtml}
                </select>
            </div>

            <div style="display: flex; gap: 10px;">
                <button type="button" onclick="window.editConfluenceTitle()" style="flex: 1; padding: 8px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); border: 1px solid var(--vscode-button-border); border-radius: 4px; cursor: pointer; font-size: 13px;">
                    Edit Title
                </button>
                <button type="button" data-action="confluenceCreate" style="flex: 1; padding: 8px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: 600;">
                    Create Perfect Page
                </button>
            </div>
            <div id="confluence-create-status" style="display: none; font-size: 12px; margin-top: 8px; color: var(--vscode-errorForeground);"></div>
            <script ${nonce ? `nonce="${nonce}"` : ''}>
                (function() {
                    // Must run when card is appended so Create Perfect Page can postMessage (Path 1 plan Phase 2.2).
                    if (typeof acquireVsCodeApi !== 'undefined' && !window.vscode) { window.vscode = acquireVsCodeApi(); }
                    const vscode = window.vscode;

                    window.updateConfluenceTitleCounter = function() {
                        const display = document.getElementById('confluence-title-display');
                        const countEl = document.getElementById('confluence-title-count');
                        if (display && countEl) countEl.textContent = String((display.textContent || '').length);
                    };

                    window.editConfluenceTitle = function() {
                        const display = document.getElementById('confluence-title-display');
                        if (!display) return;
                        display.focus();
                        var sel = window.getSelection();
                        if (sel) {
                            sel.selectAllChildren(display);
                        }
                    };

                    (function setupTitleEdit() {
                        var display = document.getElementById('confluence-title-display');
                        if (!display) return;
                        display.addEventListener('input', function() {
                            var text = (display.textContent || '').trim();
                            if (text.length > 255) {
                                display.textContent = text.slice(0, 255);
                            }
                            window.updateConfluenceTitleCounter && window.updateConfluenceTitleCounter();
                        });
                        display.addEventListener('paste', function(e) {
                            e.preventDefault();
                            var pasted = (e.clipboardData || window.clipboardData).getData('text').slice(0, 255);
                            display.textContent = (display.textContent || '').trim().slice(0, 255 - pasted.length) + pasted;
                            window.updateConfluenceTitleCounter && window.updateConfluenceTitleCounter();
                        });
                    })();

                    window.updateConfluenceTitleCounter && window.updateConfluenceTitleCounter();

                    window.submitConfluenceCreate = function() {
                        var statusEl = document.getElementById('confluence-create-status');
                        if (statusEl) { statusEl.style.display = 'none'; statusEl.textContent = ''; }
                        if (!window.vscode && typeof acquireVsCodeApi === 'function') { window.vscode = acquireVsCodeApi(); }
                        if (!window.vscode || !window.vscode.postMessage) {
                            if (statusEl) {
                                statusEl.textContent = 'Extension not ready. Try again or reload the window.';
                                statusEl.style.display = 'block';
                            }
                            return;
                        }
                        const titleEl = document.getElementById('confluence-title-display');
                        const spaceEl = document.getElementById('confluence-space-select');
                        const rawTitle = (titleEl && titleEl.textContent ? titleEl.textContent.trim() : '') || '';
                        const title = (rawTitle || 'Documentation').slice(0, 255);
                        const space = (spaceEl && spaceEl.value) ? spaceEl.value : 'DEV';
                        window.vscode.postMessage({ type: 'confluenceCreate', title, space });
                    };
                    if (window.vscode && window.vscode.postMessage) window.vscode.postMessage({ type: 'confluenceScriptReady' });
                })();
            </script>
        </div>
    `;
}

export function getConfluenceProgressHtml(nonce: string = ''): string {
    return `
        <div data-confluence-id="msg-progress" class="confluence-card" style="border: 1px solid var(--vscode-widget-border); border-radius: 8px; padding: 16px; background-color: var(--vscode-editor-background); max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
            <script ${nonce ? `nonce="${nonce}"` : ''}>
                const vscode = acquireVsCodeApi();
                window.vscode = vscode;
            </script>
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <span style="font-size: 18px; margin-right: 8px;">⏳</span>
                <h3 style="margin: 0; font-size: 15px; font-weight: 600;">${esc(messages.phrases.firstInteraction.progress)}</h3>
            </div>
            
            <div style="margin-bottom: 20px;">
                <div style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                    <span style="margin-right: 12px; color: #4CAF50; font-weight: bold;">✓</span>
                    <span>Analyzing content structure...</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                    <span style="margin-right: 12px; color: #4CAF50; font-weight: bold;">✓</span>
                    <span>Selecting optimal template...</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                    <span style="margin-right: 12px; color: var(--vscode-progressBar-foreground); animation: pulse 1.5s infinite;">●</span>
                    <span style="font-weight: 600;">Applying intelligent formatting...</span>
                    <span style="margin-left: auto; font-family: monospace; color: var(--vscode-descriptionForeground);">███</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                    <span style="margin-right: 12px; color: var(--vscode-descriptionForeground);">○</span>
                    <span style="color: var(--vscode-descriptionForeground);">Uploading to Confluence...</span>
                    <span style="margin-left: auto; font-family: monospace; color: var(--vscode-descriptionForeground); opacity: 0.3;">▓▓▓</span>
                </div>
            </div>

            <div style="margin-bottom: 12px;">
                <div style="height: 6px; width: 100%; background-color: var(--vscode-progressBar-background); border-radius: 3px; overflow: hidden;">
                    <div style="height: 100%; width: 75%; background-color: var(--vscode-progressBar-foreground); transition: width 0.5s ease;"></div>
                </div>
                <div style="display: flex; justify-content: space-between; font-size: 11px; margin-top: 6px; opacity: 0.8; font-weight: 500;">
                    <span>75%</span>
                    <span>Estimated: 12 seconds</span>
                </div>
            </div>

            <div style="display: flex; justify-content: flex-end;">
                <button type="button" onclick="window.vscode && window.vscode.postMessage({ type: 'confluenceCancel' })" style="padding: 4px 12px; background: transparent; color: var(--vscode-foreground); border: 1px solid var(--vscode-button-border); border-radius: 4px; cursor: pointer; font-size: 12px;">
                    Cancel
                </button>
            </div>
            <style>
                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.4; }
                    100% { opacity: 1; }
                }
            </style>
        </div>
    `;
}

/** US-16: Document project progress card */
export function getConfluenceDocumentProjectProgressHtml(nonce: string = ''): string {
    return `
        <div class="confluence-card" style="border: 1px solid var(--vscode-widget-border); border-radius: 8px; padding: 16px; background-color: var(--vscode-editor-background); max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
            <script ${nonce ? `nonce="${nonce}"` : ''}>
                const vscode = acquireVsCodeApi();
                window.vscode = vscode;
            </script>
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <span style="font-size: 18px; margin-right: 8px;">📂</span>
                <h3 style="margin: 0; font-size: 15px; font-weight: 600;">Intelligently scanning project for documentation...</h3>
            </div>
            <div style="margin-bottom: 16px;">
                <div style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                    <span style="margin-right: 12px; color: var(--vscode-progressBar-foreground); animation: pulse 1.5s infinite;">●</span>
                    <span>Analyzing project structure...</span>
                </div>
                <div style="display: flex; align-items: center; margin-bottom: 8px; font-size: 13px;">
                    <span style="margin-right: 12px; color: var(--vscode-descriptionForeground);">○</span>
                    <span style="color: var(--vscode-descriptionForeground);">Detecting key files...</span>
                </div>
            </div>
            <style>
                @keyframes pulse {
                    0% { opacity: 1; }
                    50% { opacity: 0.4; }
                    100% { opacity: 1; }
                }
            </style>
        </div>
    `;
}

/** US-16: Document project success card */
export function getConfluenceDocumentProjectSuccessHtml(result: DocumentProjectResponse, nonce: string = ''): string {
    const htmlAttr = (s: string) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const pageUrl = result.confluence_url ?? '';
    const projectType = result.intelligence_analysis?.project_type ?? 'project';
    const templateName = result.template_name ?? result.intelligent_recommendation?.template_name ?? 'Project Documentation';
    const sourceCount = result.intelligence_analysis?.source_file_count ?? 0;
    const detected = sourceCount > 0 ? `Detected: ${projectType} project with ${sourceCount} source files` : `Detected: ${projectType} project`;
    const pageUrlAttr = htmlAttr(pageUrl);

    return `
        <div class="confluence-card" style="border: 1px solid #4CAF50; border-radius: 8px; padding: 16px; background-color: var(--vscode-editor-background); max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
            <script ${nonce ? `nonce="${nonce}"` : ''}>
                const vscode = acquireVsCodeApi();
                window.vscode = vscode;
            </script>
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <span style="font-size: 18px; margin-right: 8px;">✅</span>
                <h3 style="margin: 0; font-size: 15px; font-weight: 600; color: #4CAF50; display: flex; align-items: center;">Intelligent Project Documentation Created! ${getAiFormattedBadgeHtml()}</h3>
            </div>
            <div style="font-size: 12px; margin-bottom: 12px; color: var(--vscode-descriptionForeground);">${htmlAttr(detected)}</div>
            <div style="font-size: 12px; margin-bottom: 12px;">Selected '${htmlAttr(templateName)}' (Matches examples)</div>
            ${(result.learning_indicator ?? false) ? getLearningIndicatorHtml({ examplesCount: result.intelligence_analysis?.source_file_count }) : ''}
            ${pageUrl ? `
            <div style="margin-bottom: 16px; padding: 12px; background: var(--vscode-textBlockQuote-background); border-radius: 6px;">
                <div style="font-size: 12px; font-weight: 600; margin-bottom: 6px;">Page Link:</div>
                <div style="font-size: 11px; color: var(--vscode-textLink-foreground); word-break: break-all;">${htmlAttr(pageUrl)}</div>
            </div>
            <div style="display: flex; gap: 10px;">
                <button type="button" data-action="openUrl" data-url="${pageUrlAttr}" style="flex: 1; padding: 8px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); border: 1px solid var(--vscode-button-border); border-radius: 4px; cursor: pointer; font-size: 13px;">${esc(messages.buttons.viewPage)}</button>
                <button type="button" data-action="copyToClipboard" data-text="${pageUrlAttr}" style="flex: 1; padding: 8px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); border: 1px solid var(--vscode-button-border); border-radius: 4px; cursor: pointer; font-size: 13px;">${esc(messages.buttons.copyLink)}</button>
                <button type="button" data-action="confluenceDone" style="flex: 1; padding: 8px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: 600;">Done</button>
            </div>
            ` : '<div style="font-size: 12px; color: var(--vscode-descriptionForeground);">Page created. Link not available.</div>'}
        </div>
    `;
}

export function getConfluenceSuccessHtml(
    usageCount: number = 0,
    data?: { pageUrl?: string; title?: string; space?: string; confidence?: number; learning?: boolean; reasoning?: string[]; examplesCount?: number },
    nonce: string = ''
): string {
    const pageUrl = data?.pageUrl ?? 'https://confluence.example.com/page/123';
    const title = data?.title ?? 'API Service Setup & Configuration';
    const space = data?.space ?? 'DEV';
    const confidence = data?.confidence ?? 94;
    const learning = data?.learning ?? false;
    const reasoning = data?.reasoning ?? ['Detected FastAPI patterns', 'Used proven API template', 'Organized logically'];
    const showConfidence = usageCount >= 1 && confidence > 70;
    const showExplainChoice = usageCount >= 2 && reasoning.length > 0;
    const showEncouragement = usageCount >= 1;
    const htmlAttr = (s: string) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const pageUrlAttr = htmlAttr(pageUrl);

    return `
        <div class="confluence-card" style="border: 1px solid #4CAF50; border-radius: 8px; padding: 16px; background-color: var(--vscode-editor-background); max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <span style="font-size: 18px; margin-right: 8px;">✅</span>
                <h3 style="margin: 0; font-size: 15px; font-weight: 600; color: #4CAF50; display: flex; align-items: center;">${esc(messages.phrases.firstInteraction.success)} ${getAiFormattedBadgeHtml()}</h3>
            </div>
            ${showEncouragement ? `<div class="success-encouragement" style="margin-top: 8px; font-style: italic; color: #2E7D32; font-size: 13px;">${esc(messages.phrases.encouragement[0])}</div>` : ''}

            <div style="display: grid; grid-template-columns: auto 1fr; gap: 8px 12px; font-size: 13px; margin-bottom: 16px;">
                <span style="font-weight: 600; color: var(--vscode-descriptionForeground);">Title:</span>
                <span>${title}</span>
                
                <span style="font-weight: 600; color: var(--vscode-descriptionForeground);">Space:</span>
                <span>${space}</span>
                
                <span style="font-weight: 600; color: var(--vscode-descriptionForeground);">Format:</span>
                <span style="display: flex; align-items: center; gap: 6px;">
                    API Project Docs
                    <span style="background: #4CAF50; color: white; font-size: 9px; padding: 1px 4px; border-radius: 3px; font-weight: bold;">AI-FORMATTED</span>
                </span>
                ${showConfidence ? `<span style="font-weight: 600; color: var(--vscode-descriptionForeground);">${esc(messages.phrases.confidence)}:</span>
                <span style="color: ${getConfidenceColor(confidence)}; font-weight: bold;" title="${esc((messages.phrases as { confidenceTooltip?: string }).confidenceTooltip || 'Intelligence Confidence: How sure AI is about this decision')}">${confidence}%</span>` : ''}
            </div>
            
            <div style="margin-bottom: 16px; padding: 12px; background: var(--vscode-textBlockQuote-background); border-radius: 6px;">
                <div style="font-size: 12px; font-weight: 600; margin-bottom: 6px; display: flex; align-items: center; gap: 6px;">
                    <span>🔗</span> Page Link:
                </div>
                <div style="font-size: 11px; color: var(--vscode-textLink-foreground); word-break: break-all; font-family: monospace;">
                    ${pageUrl}
                </div>
            </div>

            ${showExplainChoice ? `<details style="font-size: 13px; margin-bottom: 16px;" class="explain-choice">
                <summary>${esc(messages.phrases.explainChoice)}</summary>
                <ul style="margin: 4px 0 0; padding-left: 24px; line-height: 1.6; color: var(--vscode-descriptionForeground); font-size: 12px;">
                    ${reasoning.map(r => `<li>${esc(r)}</li>`).join('')}
                </ul>
            </details>` : ''}

            ${learning ? getLearningIndicatorHtml({ examplesCount: data?.examplesCount }) : ''}

            <div style="display: flex; gap: 10px;">
                <button type="button" data-action="confluenceDone" style="flex: 1; padding: 8px; background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; border-radius: 4px; cursor: pointer; font-size: 13px; font-weight: 600;">
                    Done
                </button>
                <button type="button" data-action="openUrl" data-url="${pageUrlAttr}" style="flex: 1; padding: 8px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); border: 1px solid var(--vscode-button-border); border-radius: 4px; cursor: pointer; font-size: 13px;">
                    ${esc(messages.buttons.viewPage)}
                </button>
                <button type="button" data-action="copyToClipboard" data-text="${pageUrlAttr}" style="flex: 1; padding: 8px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); border: 1px solid var(--vscode-button-border); border-radius: 4px; cursor: pointer; font-size: 13px;">
                    ${esc(messages.buttons.copyLink)}
                </button>
            </div>
        </div>
    `;
}

export interface ConfluenceErrorHtmlOpts {
    error: string;
    message: string;
    suggestion: string;
    confidence: number;
    fallbackAvailable?: boolean;
    actions?: string[];
    suggestedFiles?: string[];
    helpLink?: string;
    retryContext?: 'analyze' | 'create';
    retryFiles?: string[];
    nonce?: string;
}

export function getConfluenceErrorHtml(opts: ConfluenceErrorHtmlOpts): string;
export function getConfluenceErrorHtml(error: string, message: string, suggestion: string, confidence: number, nonce?: string): string;
export function getConfluenceErrorHtml(
    optsOrError: ConfluenceErrorHtmlOpts | string,
    message?: string,
    suggestion?: string,
    confidence?: number,
    nonceParam?: string
): string {
    const opts: ConfluenceErrorHtmlOpts =
        typeof optsOrError === 'object'
            ? optsOrError
            : {
                  error: optsOrError,
                  message: message ?? '',
                  suggestion: suggestion ?? '',
                  confidence: confidence ?? 0.5,
                  nonce: nonceParam ?? '',
              };

    const msgRecord = messages as Record<string, unknown>;
    const {
        error,
        message: msg,
        suggestion: sugg,
        confidence: conf,
        fallbackAvailable = true,
        actions = ['Retry', 'Cancel', 'Update Settings'],
        suggestedFiles = [],
        helpLink = typeof msgRecord.helpUrl === 'string' ? msgRecord.helpUrl : undefined,
        retryContext = 'create',
        retryFiles = [],
        nonce = '',
    } = opts;

    const retryFilesJson = JSON.stringify(retryFiles);

    const htmlAttr = (s: string) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const buttonHtml = (action: string): string => {
        const baseStyle = 'flex: 1; padding: 8px; border-radius: 4px; cursor: pointer; font-size: 13px;';
        if (action === 'Retry') {
            const isAnalyze = retryContext === 'analyze';
            const onclick = isAnalyze
                ? `window.vscode.postMessage({ type: 'confluenceRetryAnalyze', files: ${retryFilesJson} })`
                : "window.vscode.postMessage({ type: 'confluenceCreate' })";
            return `<button type="button" onclick="${htmlAttr(onclick)}" style="${baseStyle} background: var(--vscode-button-background); color: var(--vscode-button-foreground); border: none; font-weight: 600;">Retry</button>`;
        }
        if (action === 'Cancel') {
            return `<button type="button" onclick="window.vscode && window.vscode.postMessage({ type: 'confluenceCancel' })" style="${baseStyle} background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); border: 1px solid var(--vscode-button-border);">Cancel</button>`;
        }
        if (action === 'Update Settings') {
            return `<button type="button" onclick="window.vscode && window.vscode.postMessage({ type: 'confluenceSettings' })" style="${baseStyle} background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground); border: 1px solid var(--vscode-button-border);">Update Settings</button>`;
        }
        return '';
    };

    const actionsHtml = actions.map((a) => buttonHtml(a)).filter(Boolean).join('\n                ');

    const suggestedFilesHtml =
        suggestedFiles.length > 0
            ? `
            <div style="font-size: 13px; margin-bottom: 16px;">
                <div style="font-weight: 600; margin-bottom: 8px;">Try these files instead:</div>
                <ul style="margin: 0; padding-left: 20px; line-height: 1.6;">
                    ${suggestedFiles
                        .slice(0, 5)
                        .map((f) => {
                            const onClick = `window.vscode && window.vscode.postMessage({ type: 'confluenceRetryAnalyze', files: ${JSON.stringify([f])} })`;
                            const label = (f.split(/[/\\]/).pop() ?? f);
                            return `<li><button type="button" onclick="${htmlAttr(onClick)}" style="background: none; border: none; cursor: pointer; color: var(--vscode-textLink-foreground); text-decoration: underline; font-size: 12px; padding: 0;">${esc(label)}</button></li>`;
                        })
                        .join('')}
                </ul>
            </div>`
            : '';

    const helpLinkHtml = helpLink
        ? (() => {
              const onClick = `window.vscode && window.vscode.postMessage({ type: 'openUrl', url: ${JSON.stringify(helpLink)} }); return false;`;
              return `<a href="#" onclick="${htmlAttr(onClick)}" style="font-size: 12px; color: var(--vscode-textLink-foreground);">Help</a>`;
          })()
        : '';

    return `
        <div class="confluence-card" style="border: 1px solid var(--vscode-errorForeground); border-radius: 8px; padding: 16px; background-color: var(--vscode-editor-background); max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
            <script ${nonce ? `nonce="${nonce}"` : ''}>
                const vscode = acquireVsCodeApi();
                window.vscode = vscode;
            </script>
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <span style="font-size: 18px; margin-right: 8px;">❌</span>
                <h3 style="margin: 0; font-size: 15px; font-weight: 600; color: var(--vscode-errorForeground);">Intelligent Creation Failed</h3>
            </div>

            <div style="font-size: 13px; margin-bottom: 16px; line-height: 1.5;">
                <div style="margin-bottom: 4px;"><strong>Error:</strong> <span style="font-family: monospace;">${esc(error)}</span></div>
                <div><strong>Message:</strong> ${esc(msg)}</div>
            </div>

            <div style="font-size: 13px; margin-bottom: 16px; padding: 12px; background: var(--vscode-textBlockQuote-background); border-radius: 6px; border-left: 3px solid var(--vscode-errorForeground);">
                <div style="font-weight: 600; margin-bottom: 4px; display: flex; align-items: center; gap: 6px;">
                    <span>💡</span> AI Suggestion:
                </div>
                <div>${esc(sugg)}</div>
            </div>
            ${suggestedFilesHtml}

            <div style="font-size: 13px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <span><strong>Fallback available:</strong> ${fallbackAvailable ? 'Yes' : 'No'}</span>
                <span><strong>Confidence:</strong> <span style="color: var(--vscode-errorForeground); font-weight: bold;">${Math.round((conf ?? 0) * 100)}%</span></span>
                ${helpLinkHtml ? `<span>${helpLinkHtml}</span>` : ''}
            </div>

            <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                ${actionsHtml}
            </div>
        </div>
    `;
}

export function getConfluenceViewCreationsHtml(
    creations: Array<{ url?: string; title?: string; space?: string }> = [],
    nonce: string = ''
): string {
    const htmlAttr = (s: string) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const listItems = creations
        .filter((c) => c.url)
        .map((c) => {
            const url = c.url ?? '';
            const title = esc(c.title ?? 'Untitled');
            const space = esc(c.space ?? '');
            const urlJson = JSON.stringify(url);
            const viewOnclick = `window.vscode&&window.vscode.postMessage({type:'openUrl',url:${urlJson}})`;
            const copyOnclick = `window.vscode&&window.vscode.postMessage({type:'copyToClipboard',text:${urlJson}})`;
            return `
            <div style="display: flex; align-items: center; justify-content: space-between; padding: 8px 0; border-bottom: 1px solid var(--vscode-widget-border); gap: 8px;">
                <div style="flex: 1; min-width: 0;">
                    <div style="font-weight: 600; font-size: 13px; overflow: hidden; text-overflow: ellipsis;">${title}</div>
                    ${space ? `<div style="font-size: 11px; color: var(--vscode-descriptionForeground);">${space}</div>` : ''}
                </div>
                <div style="display: flex; gap: 6px; flex-shrink: 0;">
                    <button type="button" onclick="${htmlAttr(viewOnclick)}" style="padding: 4px 8px; font-size: 11px; cursor: pointer; border: 1px solid var(--vscode-button-border); border-radius: 4px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground);">${esc(messages.buttons.viewPage)}</button>
                    <button type="button" onclick="${htmlAttr(copyOnclick)}" style="padding: 4px 8px; font-size: 11px; cursor: pointer; border: 1px solid var(--vscode-button-border); border-radius: 4px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground);">${esc(messages.buttons.copyLink)}</button>
                </div>
            </div>`;
        })
        .join('');
    const emptyState = creations.length === 0
        ? '<div style="padding: 24px; text-align: center; color: var(--vscode-descriptionForeground); font-size: 13px;">No intelligent creations yet. Use "Save to Confluence" to create your first page.</div>'
        : '';

    return `
        <div class="confluence-card" style="border: 1px solid var(--vscode-widget-border); border-radius: 8px; padding: 16px; background-color: var(--vscode-editor-background); max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
            <div style="display: flex; align-items: center; margin-bottom: 16px;">
                <span style="font-size: 18px; margin-right: 8px;">📄</span>
                <h3 style="margin: 0; font-size: 15px; font-weight: 600;">Intelligent Creations</h3>
            </div>
            ${emptyState || `<div style="max-height: 300px; overflow-y: auto;">${listItems}</div>`}
        </div>
    `;
}

/** US-17: Intelligence dashboard with metrics, creations list, and feedback form */
export function getIntelligenceDashboardHtml(opts: {
    metrics: IntelligenceMetrics | null | undefined;
    creations: Array<{ url?: string; title?: string; space?: string; creationId?: string }>;
    nonce?: string;
}): string {
    const { metrics, creations, nonce = '' } = opts;
    const htmlAttr = (s: string) => String(s).replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    const hasMetrics = metrics && (typeof metrics.templateSelectionAccuracy === 'number' || typeof metrics.examplesLearned === 'number' || !!metrics.statusSummary);
    const acc = typeof metrics?.templateSelectionAccuracy === 'number' ? metrics.templateSelectionAccuracy : '—';
    const examples = typeof metrics?.examplesLearned === 'number' ? metrics.examplesLearned : '—';
    const conf = typeof metrics?.intelligenceConfidencePct === 'number' ? metrics.intelligenceConfidencePct : '—';
    const rate = typeof metrics?.learningRatePct === 'number' ? metrics.learningRatePct : '—';
    const summary = metrics?.statusSummary ?? (hasMetrics ? `Intelligence Status: ${acc}% accuracy, ${examples} examples learned` : '');
    const successRate = metrics?.successRate;
    const collectiveCount = metrics?.collectiveIntelligenceCount;

    const listItems = creations
        .filter((c) => c.url)
        .map((c, idx) => {
            const url = c.url ?? '';
            const title = esc(c.title ?? 'Untitled');
            const space = esc(c.space ?? '');
            const creationId = c.creationId ?? '';
            const urlJson = JSON.stringify(url);
            const creationIdJson = JSON.stringify(creationId);
            const viewOnclick = `window.vscode&&window.vscode.postMessage({type:'openUrl',url:${urlJson}})`;
            const copyOnclick = `window.vscode&&window.vscode.postMessage({type:'copyToClipboard',text:${urlJson}})`;
            const fbId = 'fb-' + idx + '-' + (creationId || '').replace(/[^a-zA-Z0-9]/g, '_').slice(0, 20);
            const commentId = 'comment-' + fbId;
            const feedbackFormHtml = creationId
                ? `
                <div id="${htmlAttr(fbId)}" data-creation-id="${htmlAttr(creationId)}" style="display: none; margin-top: 8px; padding: 8px; background: var(--vscode-input-background); border-radius: 4px; border: 1px solid var(--vscode-widget-border);">
                    <div style="font-size: 11px; margin-bottom: 4px;">Rate this creation (1–5):</div>
                    <div style="display: flex; gap: 4px; margin-bottom: 6px;">
                        ${[1, 2, 3, 4, 5].map(n => `<button type="button" data-score="${n}" style="padding: 2px 8px; font-size: 12px; cursor: pointer; border: 1px solid var(--vscode-button-border); border-radius: 4px; background: var(--vscode-button-secondaryBackground);">${n}</button>`).join('')}
                    </div>
                    <input type="text" id="${htmlAttr(commentId)}" placeholder="Optional feedback" style="width: 100%; padding: 4px 8px; font-size: 12px; margin-bottom: 6px; border: 1px solid var(--vscode-input-border); border-radius: 4px;" />
                    <button type="button" data-submit style="padding: 4px 10px; font-size: 11px; cursor: pointer; border: 1px solid var(--vscode-button-border); border-radius: 4px; background: var(--vscode-button-background); color: var(--vscode-button-foreground);">Submit feedback</button>
                </div>`
                : '';
            const rateOnclick = creationId
                ? `var e=document.getElementById('${htmlAttr(fbId)}');e.style.display=e.style.display==='none'?'block':'none';`
                : '';
            const rateBtn = creationId ? `<button type="button" onclick="${htmlAttr(rateOnclick)}" style="padding: 4px 8px; font-size: 11px; cursor: pointer; border: 1px solid var(--vscode-button-border); border-radius: 4px; background: var(--vscode-button-secondaryBackground);">Rate</button>` : '';
            return `
            <div style="padding: 8px 0; border-bottom: 1px solid var(--vscode-widget-border);">
                <div style="display: flex; align-items: center; justify-content: space-between; gap: 8px;">
                    <div style="flex: 1; min-width: 0;">
                        <div style="font-weight: 600; font-size: 13px; overflow: hidden; text-overflow: ellipsis; display: flex; align-items: center; gap: 6px;">${title} ${getAiFormattedBadgeHtml()}</div>
                        ${space ? `<div style="font-size: 11px; color: var(--vscode-descriptionForeground);">${space}</div>` : ''}
                    </div>
                    <div style="display: flex; gap: 6px; flex-shrink: 0;">
                        <button type="button" onclick="${htmlAttr(viewOnclick)}" style="padding: 4px 8px; font-size: 11px; cursor: pointer; border: 1px solid var(--vscode-button-border); border-radius: 4px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground);">${esc(messages.buttons.viewPage)}</button>
                        <button type="button" onclick="${htmlAttr(copyOnclick)}" style="padding: 4px 8px; font-size: 11px; cursor: pointer; border: 1px solid var(--vscode-button-border); border-radius: 4px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground);">${esc(messages.buttons.copyLink)}</button>
                        ${rateBtn}
                    </div>
                </div>
                ${feedbackFormHtml}
            </div>`;
        })
        .join('');
    const emptyCreations = creations.length === 0
        ? '<div style="padding: 16px; text-align: center; color: var(--vscode-descriptionForeground); font-size: 13px;">No intelligent creations yet. Use "Save to Confluence" to create your first page.</div>'
        : `<div style="max-height: 300px; overflow-y: auto;">${listItems}</div>`;

    const metricsSectionHtml = hasMetrics
        ? `
        <div style="font-size: 13px; margin-bottom: 16px; padding: 12px; background: var(--vscode-textBlockQuote-background); border-radius: 6px; border-left: 3px solid var(--vscode-accent);">
            <div style="font-weight: 600; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                <span>🧠</span> Intelligence Status
            </div>
            <div style="line-height: 1.6;">
                ${summary ? `<div style="margin-bottom: 4px;">${esc(summary)}</div>` : ''}
                <div style="display: flex; flex-wrap: wrap; gap: 12px 16px; font-size: 12px;">
                    <span><strong>Intelligence Confidence:</strong> ${typeof conf === 'number' ? conf + '%' : conf}</span>
                    <span><strong>Learning Rate:</strong> ${typeof rate === 'number' ? '+' + rate + '%' : rate}</span>
                    ${typeof successRate === 'number' ? `<span><strong>Success Rate:</strong> ${successRate}%</span>` : ''}
                    ${typeof collectiveCount === 'number' ? `<span><strong>Collective Intelligence:</strong> ${collectiveCount} examples from team</span>` : ''}
                </div>
            </div>
        </div>`
        : '<div style="font-size: 12px; margin-bottom: 16px; padding: 10px; color: var(--vscode-descriptionForeground);">Metrics unavailable. Ensure the agent backend is running.</div>';

    return `
        <div class="confluence-card" style="border: 1px solid var(--vscode-widget-border); border-radius: 8px; padding: 16px; background-color: var(--vscode-editor-background); max-width: 400px; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
            <script ${nonce ? `nonce="${nonce}"` : ''}>
                const vscode = acquireVsCodeApi();
                window.vscode = vscode;
            </script>
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 18px; margin-right: 8px;">📊</span>
                    <h3 style="margin: 0; font-size: 15px; font-weight: 600;">Intelligence Dashboard</h3>
                </div>
                <button type="button" data-action="confluenceViewCreations" style="padding: 4px 10px; font-size: 12px; cursor: pointer; border: 1px solid var(--vscode-button-border); border-radius: 4px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground);">Refresh</button>
            </div>
            ${metricsSectionHtml}
            <div style="margin-bottom: 16px;">
                <div style="font-weight: 600; font-size: 13px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                    <span>📦</span> ${esc((messages as { exportImport?: { sectionTitle?: string } }).exportImport?.sectionTitle ?? 'Export/Import Examples')}
                </div>
                <div style="display: flex; gap: 8px;">
                    <button type="button" data-action="confluenceExportExamples" style="padding: 6px 12px; font-size: 12px; cursor: pointer; border: 1px solid var(--vscode-button-border); border-radius: 4px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground);">${esc((messages as { exportImport?: { exportButton?: string } }).exportImport?.exportButton ?? 'Export Examples')}</button>
                    <button type="button" data-action="confluenceImportExamples" style="padding: 6px 12px; font-size: 12px; cursor: pointer; border: 1px solid var(--vscode-button-border); border-radius: 4px; background: var(--vscode-button-secondaryBackground); color: var(--vscode-button-secondaryForeground);">${esc((messages as { exportImport?: { importButton?: string } }).exportImport?.importButton ?? 'Import Examples')}</button>
                </div>
            </div>
            <div style="margin-bottom: 8px;">
                <div style="font-weight: 600; font-size: 13px; margin-bottom: 8px; display: flex; align-items: center; gap: 6px;">
                    <span>📄</span> Intelligent Creations
                </div>
                ${emptyCreations}
            </div>
            <script ${nonce ? `nonce="${nonce}"` : ''}>
                (function() {
                    const vscode = window.vscode;
                    const refreshBtn = document.querySelector('[data-action="confluenceViewCreations"]');
                    if (refreshBtn) refreshBtn.addEventListener('click', function() { vscode && vscode.postMessage({ type: 'confluenceViewCreations' }); });
                    const exportBtn = document.querySelector('[data-action="confluenceExportExamples"]');
                    if (exportBtn) exportBtn.addEventListener('click', function() { vscode && vscode.postMessage({ type: 'confluenceExportExamples' }); });
                    const importBtn = document.querySelector('[data-action="confluenceImportExamples"]');
                    if (importBtn) importBtn.addEventListener('click', function() { vscode && vscode.postMessage({ type: 'confluenceImportExamples' }); });
                    document.querySelectorAll('[id^="fb-"] [data-score]').forEach(function(starBtn) {
                        starBtn.addEventListener('click', function() {
                            const form = this.closest('[id^="fb-"]');
                            if (form) form.setAttribute('data-score-selected', this.getAttribute('data-score') || '0');
                        });
                    });
                    document.querySelectorAll('[data-submit]').forEach(function(btn) {
                        btn.addEventListener('click', function() {
                            const form = this.closest('[id^="fb-"]');
                            if (!form || !vscode) return;
                            const creationId = form.getAttribute('data-creation-id');
                            const score = parseInt(form.getAttribute('data-score-selected') || '0', 10);
                            const commentEl = form.querySelector('input[type="text"]');
                            const feedback = commentEl ? commentEl.value.trim() : '';
                            if (creationId && score >= 1 && score <= 5) {
                                vscode.postMessage({ type: 'confluenceIntelligenceFeedback', creationId: creationId, intelligenceScore: score, feedback: feedback || undefined });
                            }
                        });
                    });
                })();
            </script>
        </div>
    `;
}
