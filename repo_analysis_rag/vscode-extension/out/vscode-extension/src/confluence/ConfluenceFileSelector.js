"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfluenceFileSelector = void 0;
const React = __importStar(require("react"));
const simple_language_json_1 = __importDefault(require("./simple-language.json"));
const ConfluenceFileSelector = ({ onCancel, onNext, usageCount = 0 }) => {
    const [selectedFiles, setSelectedFiles] = React.useState([]);
    const [availableFiles, setAvailableFiles] = React.useState(['api.py', 'config.yaml', 'README.md', 'utils.py']);
    const showIntelligentBadge = usageCount >= 1;
    const showAddRelated = usageCount >= 2;
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
        React.createElement("h3", { style: { margin: '0 0 12px 0', fontSize: '14px' } }, simple_language_json_1.default.phrases.firstInteraction.fileSelector),
        showIntelligentBadge && (React.createElement("div", { style: { fontSize: '11px', marginBottom: '8px', padding: '2px 6px', backgroundColor: 'var(--vscode-badge-background)', color: 'var(--vscode-badge-foreground)', borderRadius: '4px', display: 'inline-block' } }, "Intelligent suggestions")),
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
        showAddRelated && (React.createElement("div", { style: { marginBottom: '12px' } },
            React.createElement("button", { type: "button", style: { fontSize: '12px', padding: '4px 8px', cursor: 'pointer', border: '1px solid var(--vscode-button-border)', borderRadius: '2px', background: 'transparent' } }, "Add related files"))),
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
