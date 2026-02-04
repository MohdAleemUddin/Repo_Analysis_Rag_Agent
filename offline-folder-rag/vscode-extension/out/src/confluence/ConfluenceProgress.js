"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfluenceProgress = void 0;
const React = require("react");
const ConfluenceProgress = ({ steps, estimatedSeconds, percent, onCancel }) => {
    return (React.createElement("div", { className: "confluence-card progress", style: {
            border: '1px solid var(--vscode-widget-border)',
            borderRadius: '4px',
            padding: '12px',
            backgroundColor: 'var(--vscode-editor-background)',
            maxWidth: '400px'
        } },
        React.createElement("h3", { style: { margin: '0 0 12px 0', fontSize: '14px' } }, "\u23F3 Creating Intelligent Documentation..."),
        React.createElement("div", { style: { marginBottom: '16px' } }, steps.map((step, i) => (React.createElement("div", { key: i, style: { display: 'flex', alignItems: 'center', marginBottom: '4px', fontSize: '12px' } },
            React.createElement("span", { style: { marginRight: '8px' } }, step.status === 'completed' ? '✓' :
                step.status === 'active' ? '●' :
                    step.status === 'error' ? '❌' : '○'),
            React.createElement("span", { style: {
                    color: step.status === 'pending' ? 'var(--vscode-descriptionForeground)' : 'inherit',
                    fontWeight: step.status === 'active' ? 'bold' : 'normal'
                } }, step.label),
            step.status === 'active' && React.createElement("span", { style: { marginLeft: '8px' } }, "\u2588\u2588\u2588"),
            step.status === 'pending' && React.createElement("span", { style: { marginLeft: '8px' } }, "\u2593\u2593\u2593"))))),
        React.createElement("div", { style: { marginBottom: '8px' } },
            React.createElement("div", { style: {
                    height: '4px',
                    width: '100%',
                    backgroundColor: 'var(--vscode-progressBar-background)',
                    borderRadius: '2px',
                    overflow: 'hidden'
                } },
                React.createElement("div", { style: {
                        height: '100%',
                        width: `${percent}%`,
                        backgroundColor: 'var(--vscode-progressBar-foreground)',
                        transition: 'width 0.3s ease'
                    } })),
            React.createElement("div", { style: { display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginTop: '4px', opacity: 0.8 } },
                React.createElement("span", null,
                    percent,
                    "%"),
                React.createElement("span", null,
                    "Estimated: ",
                    estimatedSeconds,
                    " seconds"))),
        onCancel && (React.createElement("div", { style: { display: 'flex', justifyContent: 'flex-end' } },
            React.createElement("button", { onClick: onCancel, style: { padding: '2px 8px', fontSize: '11px', cursor: 'pointer' } }, "Cancel")))));
};
exports.ConfluenceProgress = ConfluenceProgress;
