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
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfluenceFeedback = void 0;
const React = __importStar(require("react"));
const ConfluenceFeedback = ({ importedCount = null, onExport, onImport, }) => {
    const showImportSuccess = typeof importedCount === 'number' && importedCount >= 0;
    return (React.createElement("div", { style: { marginTop: 12, padding: 12, border: '1px solid var(--vscode-widget-border)', borderRadius: 8 } },
        React.createElement("div", { style: { fontWeight: 600, fontSize: 13, marginBottom: 8 } }, "Export/Import Examples"),
        React.createElement("div", { style: { display: 'flex', gap: 8 } },
            onExport && (React.createElement("button", { type: "button", onClick: onExport, style: {
                    padding: '6px 12px',
                    fontSize: 12,
                    cursor: 'pointer',
                    border: '1px solid var(--vscode-button-border)',
                    borderRadius: 4,
                    background: 'var(--vscode-button-secondaryBackground)',
                    color: 'var(--vscode-button-secondaryForeground)',
                } }, "Export Examples")),
            onImport && (React.createElement("button", { type: "button", onClick: onImport, style: {
                    padding: '6px 12px',
                    fontSize: 12,
                    cursor: 'pointer',
                    border: '1px solid var(--vscode-button-border)',
                    borderRadius: 4,
                    background: 'var(--vscode-button-secondaryBackground)',
                    color: 'var(--vscode-button-secondaryForeground)',
                } }, "Import Examples"))),
        showImportSuccess && (React.createElement("div", { style: { marginTop: 8, fontSize: 12, color: 'var(--vscode-testing-iconPassed)' } },
            "Intelligence Examples Imported: ",
            importedCount,
            " new examples learned"))));
};
exports.ConfluenceFeedback = ConfluenceFeedback;
