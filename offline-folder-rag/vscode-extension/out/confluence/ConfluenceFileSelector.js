"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfluenceFileSelector = void 0;
const React = require("react");
const ConfluenceFileSelector = ({ onCancel, onNext }) => {
    const [selectedFiles, setSelectedFiles] = React.useState([]);
    const [availableFiles, setAvailableFiles] = React.useState(['api.py', 'config.yaml', 'README.md', 'utils.py']);
    const toggleFile = (file) => {
        setSelectedFiles(prev => prev.includes(file) ? prev.filter(f => f !== file) : [...prev, file]);
    };
    return (React.createElement("div", { className: "confluence-card", style: {
            border: '1px solid var(--vscode-widget-border)',
            borderRadius: '4px',
            padding: '12px',
            backgroundColor: 'var(--vscode-editor-background)',
            maxWidth: '400px'
        } },
        React.createElement("h3", { style: { margin: '0 0 12px 0', fontSize: '14px' } }, "Select files for intelligent formatting"),
        React.createElement("div", { style: { marginBottom: '12px' } },
            React.createElement("button", { onClick: () => { }, style: {
                    padding: '4px 8px',
                    backgroundColor: 'var(--vscode-button-background)',
                    color: 'var(--vscode-button-foreground)',
                    border: 'none',
                    borderRadius: '2px',
                    cursor: 'pointer',
                    fontSize: '12px'
                } }, "\uD83D\uDCC1 Browse Files...")),
        React.createElement("div", { style: { maxHeight: '150px', overflowY: 'auto', marginBottom: '12px', border: '1px solid var(--vscode-input-border)', padding: '4px' } }, availableFiles.map(file => (React.createElement("div", { key: file, style: { display: 'flex', alignItems: 'center', padding: '2px 0' } },
            React.createElement("input", { type: "checkbox", id: file, checked: selectedFiles.includes(file), onChange: () => toggleFile(file), style: { marginRight: '8px' } }),
            React.createElement("label", { htmlFor: file, style: { fontSize: '12px' } }, file))))),
        React.createElement("div", { style: { fontSize: '12px', marginBottom: '12px', color: 'var(--vscode-descriptionForeground)' } },
            "Selected: ",
            selectedFiles.length,
            " files",
            React.createElement("ul", { style: { margin: '4px 0 0 0', paddingLeft: '16px' } },
                React.createElement("li", null, "Automatically analyzed"),
                React.createElement("li", null, "Intelligently formatted"),
                React.createElement("li", null, "Perfectly organized"))),
        React.createElement("div", { style: { display: 'flex', justifyContent: 'flex-end', gap: '8px' } },
            React.createElement("button", { onClick: onCancel, style: {
                    padding: '4px 12px',
                    backgroundColor: 'transparent',
                    color: 'var(--vscode-button-foreground)',
                    border: '1px solid var(--vscode-button-border)',
                    borderRadius: '2px',
                    cursor: 'pointer'
                } }, "Cancel"),
            React.createElement("button", { onClick: () => onNext(selectedFiles), disabled: selectedFiles.length === 0, style: {
                    padding: '4px 12px',
                    backgroundColor: selectedFiles.length === 0 ? 'var(--vscode-button-secondaryBackground)' : 'var(--vscode-button-background)',
                    color: 'var(--vscode-button-foreground)',
                    border: 'none',
                    borderRadius: '2px',
                    cursor: selectedFiles.length === 0 ? 'not-allowed' : 'pointer',
                    opacity: selectedFiles.length === 0 ? 0.5 : 1
                } }, "Next: Let AI Decide"))));
};
exports.ConfluenceFileSelector = ConfluenceFileSelector;
