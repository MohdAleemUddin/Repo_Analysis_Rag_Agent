"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfluenceConfigProvider = void 0;
const React = require("react");
const ConfluenceConfigProvider = ({ baseUrl, testResult, testLoading, onTestConnection, validationErrors = [], }) => {
    return (React.createElement("div", { className: "confluence-config-provider", style: {
            fontFamily: 'var(--vscode-font-family)',
            fontSize: '13px',
            padding: '16px',
            maxWidth: '480px',
        } },
        React.createElement("h3", { style: { marginTop: 0, marginBottom: '12px' } }, "Confluence configuration"),
        React.createElement("p", { style: { marginBottom: '12px', color: 'var(--vscode-descriptionForeground)' } }, "Set Confluence URL and email in Settings, and store your API token securely. Then test the connection."),
        validationErrors.length > 0 && (React.createElement("div", { style: {
                marginBottom: '12px',
                padding: '8px',
                background: 'var(--vscode-inputValidation-errorBackground)',
                border: '1px solid var(--vscode-inputValidation-errorBorder)',
                borderRadius: '4px',
            } },
            React.createElement("ul", { style: { margin: 0, paddingLeft: '20px' } }, validationErrors.map((err, i) => (React.createElement("li", { key: i }, err)))))),
        React.createElement("div", { style: { marginBottom: '12px' } },
            React.createElement("button", { type: "button", onClick: onTestConnection, disabled: testLoading, style: {
                    padding: '6px 12px',
                    background: 'var(--vscode-button-background)',
                    color: 'var(--vscode-button-foreground)',
                    border: 'none',
                    borderRadius: '2px',
                    cursor: testLoading ? 'not-allowed' : 'pointer',
                    opacity: testLoading ? 0.7 : 1,
                } }, testLoading ? 'Testing…' : 'Test connection')),
        testResult && !testLoading && (React.createElement("div", { style: {
                padding: '8px',
                borderRadius: '4px',
                background: testResult.ok
                    ? 'var(--vscode-editor-inactiveSelectionBackground)'
                    : 'var(--vscode-inputValidation-errorBackground)',
                border: `1px solid ${testResult.ok ? 'var(--vscode-widget-border)' : 'var(--vscode-inputValidation-errorBorder)'}`,
            } }, testResult.ok ? (React.createElement(React.Fragment, null,
            React.createElement("p", { style: { margin: '0 0 8px 0' } }, "Connection successful."),
            testResult.latency_ms != null && (React.createElement("p", { style: { margin: 0, fontSize: '12px', opacity: 0.9 } },
                "Latency: ",
                testResult.latency_ms,
                " ms")),
            testResult.spaces && testResult.spaces.length > 0 && (React.createElement("p", { style: { margin: '8px 0 0 0', fontSize: '12px' } },
                "Spaces: ",
                testResult.spaces.map((s) => s.key || s.name).filter(Boolean).join(', '))))) : (React.createElement("p", { style: { margin: 0 } }, testResult.error || 'Connection failed')))),
        React.createElement("p", { style: { marginTop: '12px', fontSize: '11px', color: 'var(--vscode-descriptionForeground)' } },
            "Edge agent: ",
            baseUrl || '—')));
};
exports.ConfluenceConfigProvider = ConfluenceConfigProvider;
