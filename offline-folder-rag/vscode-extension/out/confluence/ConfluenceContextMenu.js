"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfluenceContextMenu = void 0;
const React = require("react");
/**
 * Right-click context menu: rag-confluence.saveSelection triggers chat message flow (NO PANEL).
 * This component shows when selection was pre-loaded in the chat interface.
 */
const ConfluenceContextMenu = ({ preloadedContent, onContinue, onCancel, }) => {
    const len = (preloadedContent || '').length;
    const preview = (preloadedContent || '').slice(0, 120);
    const hasMore = len > 120;
    return (React.createElement("div", { className: "confluence-context-menu", style: {
            border: '1px solid var(--vscode-widget-border)',
            borderRadius: '4px',
            padding: '12px',
            backgroundColor: 'var(--vscode-editor-background)',
            maxWidth: '400px',
        } },
        React.createElement("h3", { style: { margin: '0 0 12px 0', fontSize: '14px' } }, "Selection will be included in Confluence"),
        React.createElement("div", { style: {
                fontSize: '12px',
                color: 'var(--vscode-descriptionForeground)',
                marginBottom: '8px',
            } },
            len,
            " character",
            len !== 1 ? 's' : '',
            " selected. This content will be pre-loaded for Confluence."),
        preview && (React.createElement("pre", { style: {
                margin: '0 0 12px 0',
                padding: '8px',
                fontSize: '11px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
                border: '1px solid var(--vscode-input-border)',
                borderRadius: '2px',
                maxHeight: '60px',
            } },
            preview,
            hasMore ? '…' : '')),
        React.createElement("div", { style: { display: 'flex', justifyContent: 'flex-end', gap: '8px' } },
            onCancel && (React.createElement("button", { type: "button", onClick: onCancel, style: {
                    padding: '4px 12px',
                    backgroundColor: 'transparent',
                    color: 'var(--vscode-button-foreground)',
                    border: '1px solid var(--vscode-button-border)',
                    borderRadius: '2px',
                    cursor: 'pointer',
                    fontSize: '12px',
                } }, "Cancel")),
            React.createElement("button", { type: "button", onClick: () => onContinue(preloadedContent), style: {
                    padding: '4px 12px',
                    backgroundColor: 'var(--vscode-button-background)',
                    color: 'var(--vscode-button-foreground)',
                    border: 'none',
                    borderRadius: '2px',
                    cursor: 'pointer',
                    fontSize: '12px',
                } }, "Continue to Save to Confluence"))));
};
exports.ConfluenceContextMenu = ConfluenceContextMenu;
