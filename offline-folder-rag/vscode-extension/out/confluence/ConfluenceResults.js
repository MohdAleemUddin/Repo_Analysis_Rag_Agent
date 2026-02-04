"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfluenceResults = void 0;
const React = require("react");
const ConfluenceResults = ({ data, onEditTitle, onCreatePage, onOpenInBrowser, onCopyLink, onRetry, onCancel }) => {
    // Check if it's an error response
    if ('error' in data) {
        return (React.createElement("div", { className: "confluence-card error", style: {
                border: '1px solid var(--vscode-errorForeground)',
                borderRadius: '4px',
                padding: '12px',
                backgroundColor: 'var(--vscode-editor-background)',
                maxWidth: '400px'
            } },
            React.createElement("h3", { style: { margin: '0 0 8px 0', fontSize: '14px', color: 'var(--vscode-errorForeground)' } }, "\u274C Intelligence Error"),
            React.createElement("div", { style: { fontSize: '12px', marginBottom: '8px' } },
                React.createElement("strong", null, "Error:"),
                " ",
                data.error),
            React.createElement("div", { style: { fontSize: '12px', marginBottom: '8px' } },
                React.createElement("strong", null, "Message:"),
                " ",
                data.message),
            React.createElement("div", { style: { fontSize: '12px', marginBottom: '12px', padding: '8px', backgroundColor: 'var(--vscode-textBlockQuote-background)', borderRadius: '2px' } },
                React.createElement("strong", null, "\uD83D\uDCA1 AI Suggestion:"),
                " ",
                data.intelligence_suggestion),
            React.createElement("div", { style: { display: 'flex', justifyContent: 'flex-end', gap: '8px' } },
                onCancel && React.createElement("button", { onClick: onCancel, style: { padding: '4px 12px', cursor: 'pointer' } }, "Cancel"),
                onRetry && React.createElement("button", { onClick: onRetry, style: { padding: '4px 12px', cursor: 'pointer', backgroundColor: 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', border: 'none' } }, "Retry"))));
    }
    // Check if it's a success response (CreateResponse)
    if ('success' in data) {
        return (React.createElement("div", { className: "confluence-card success", style: {
                border: '1px solid #4CAF50',
                borderRadius: '4px',
                padding: '12px',
                backgroundColor: 'var(--vscode-editor-background)',
                maxWidth: '400px'
            } },
            React.createElement("h3", { style: { margin: '0 0 12px 0', fontSize: '14px', color: '#4CAF50' } }, "\u2705 Intelligent Documentation Created!"),
            React.createElement("div", { style: { fontSize: '12px', marginBottom: '4px' } },
                React.createElement("strong", null, "Title:"),
                " ",
                data.intelligent_page.title),
            React.createElement("div", { style: { fontSize: '12px', marginBottom: '4px' } },
                React.createElement("strong", null, "Space:"),
                " ",
                data.intelligent_page.space),
            React.createElement("div", { style: { fontSize: '12px', marginBottom: '4px' } },
                React.createElement("strong", null, "Intelligent Format:"),
                " ",
                data.intelligence_summary.ai_decisions_made[1]),
            React.createElement("div", { style: { fontSize: '12px', marginBottom: '12px' } },
                React.createElement("strong", null, "Confidence:"),
                " ",
                Math.round(data.intelligence_summary.intelligence_confidence.overall_intelligence * 100),
                "%"),
            React.createElement("div", { style: { marginBottom: '12px' } },
                React.createElement("div", { style: { fontSize: '12px', fontWeight: 'bold', marginBottom: '4px' } }, "\uD83D\uDD17 Page Link:"),
                React.createElement("div", { style: { fontSize: '11px', color: 'var(--vscode-textLink-foreground)', wordBreak: 'break-all' } }, data.intelligent_page.url)),
            React.createElement("div", { style: { fontSize: '12px', marginBottom: '12px' } },
                React.createElement("div", { style: { fontWeight: 'bold', marginBottom: '4px' } }, "\uD83D\uDCCA What made this intelligent:"),
                React.createElement("ul", { style: { margin: '0', paddingLeft: '16px' } }, data.intelligence_summary.ai_decisions_made.map((decision, i) => (React.createElement("li", { key: i }, decision))))),
            React.createElement("div", { style: { display: 'flex', gap: '8px' } },
                React.createElement("button", { onClick: () => onOpenInBrowser?.(data.intelligent_page.url), style: { flex: 1, padding: '4px', cursor: 'pointer', backgroundColor: 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', border: 'none' } }, "Open in Browser"),
                React.createElement("button", { onClick: () => onCopyLink?.(data.intelligent_page.url), style: { flex: 1, padding: '4px', cursor: 'pointer' } }, "Copy Link"))));
    }
    // Otherwise it's an analysis response (AnalyzeResponse)
    return (React.createElement("div", { className: "confluence-card analysis", style: {
            border: '1px solid var(--vscode-widget-border)',
            borderRadius: '4px',
            padding: '12px',
            backgroundColor: 'var(--vscode-editor-background)',
            maxWidth: '400px'
        } },
        React.createElement("h3", { style: { margin: '0 0 12px 0', fontSize: '14px' } }, "\uD83E\uDD16 Intelligent Analysis Complete"),
        React.createElement("div", { style: { fontSize: '12px', marginBottom: '8px' } },
            React.createElement("strong", null, "Files:"),
            " ",
            data.intelligence_analysis.content_types.join(', ')),
        React.createElement("div", { style: { fontSize: '12px', marginBottom: '12px' } },
            React.createElement("div", { style: { fontWeight: 'bold', marginBottom: '4px' } }, "\uD83E\uDDE0 AI Detected:"),
            React.createElement("ul", { style: { margin: '0', paddingLeft: '16px' } }, data.intelligence_analysis.detected_patterns.map((pattern, i) => (React.createElement("li", { key: i }, pattern))))),
        React.createElement("div", { style: { fontSize: '12px', marginBottom: '12px', padding: '8px', backgroundColor: 'var(--vscode-textBlockQuote-background)', borderRadius: '2px' } },
            React.createElement("div", { style: { fontWeight: 'bold', color: 'var(--vscode-textLink-foreground)' } }, "\uD83C\uDFAF Intelligent Format Selected:"),
            React.createElement("div", null,
                "\"",
                data.intelligent_recommendation.template_name,
                "\""),
            React.createElement("div", { style: { fontSize: '11px', opacity: 0.8 } },
                "(",
                data.intelligent_recommendation.intelligence_reason,
                ")")),
        React.createElement("div", { style: { fontSize: '12px', marginBottom: '12px' } },
            React.createElement("div", { style: { fontWeight: 'bold', marginBottom: '4px' } }, "\uD83D\uDCDD Suggested Title:"),
            React.createElement("div", { style: { padding: '4px', border: '1px solid var(--vscode-input-border)', borderRadius: '2px' } }, data.intelligence_analysis.intelligent_title)),
        React.createElement("div", { style: { fontSize: '12px', marginBottom: '16px' } },
            React.createElement("div", { style: { fontWeight: 'bold', marginBottom: '4px' } }, "\uD83D\uDCCD Confluence Space:"),
            React.createElement("select", { style: { width: '100%', padding: '2px', backgroundColor: 'var(--vscode-select-background)', color: 'var(--vscode-select-foreground)', border: '1px solid var(--vscode-select-border)' } },
                React.createElement("option", null, "DEV"),
                React.createElement("option", null, "DOCS"))),
        React.createElement("div", { style: { display: 'flex', gap: '8px' } },
            React.createElement("button", { onClick: () => {
                    const newTitle = prompt('Edit Title', data.intelligence_analysis.intelligent_title);
                    if (newTitle)
                        onEditTitle?.(newTitle);
                }, style: { flex: 1, padding: '4px', cursor: 'pointer' } }, "Edit Title"),
            React.createElement("button", { onClick: onCreatePage, style: { flex: 1, padding: '4px', cursor: 'pointer', backgroundColor: 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', border: 'none' } }, "Create Perfect Page"))));
};
exports.ConfluenceResults = ConfluenceResults;
