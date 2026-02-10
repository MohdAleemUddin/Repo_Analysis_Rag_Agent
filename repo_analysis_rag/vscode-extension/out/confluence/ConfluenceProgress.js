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
exports.ConfluenceProgress = void 0;
const React = __importStar(require("react"));
const simple_language_json_1 = __importDefault(require("./simple-language.json"));
const ConfluenceProgress = ({ steps, estimatedSeconds, percent, onCancel }) => {
    return (React.createElement("div", { className: "confluence-card progress", style: {
            border: '1px solid var(--vscode-widget-border)',
            borderRadius: '4px',
            padding: '12px',
            backgroundColor: 'var(--vscode-editor-background)',
            maxWidth: '400px'
        } },
        React.createElement("h3", { style: { margin: '0 0 12px 0', fontSize: '14px' } },
            "\u23F3 ",
            simple_language_json_1.default.phrases.firstInteraction.progress),
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
