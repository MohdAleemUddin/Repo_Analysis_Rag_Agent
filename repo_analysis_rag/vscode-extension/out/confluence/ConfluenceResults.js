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
exports.ConfluenceResults = void 0;
const React = __importStar(require("react"));
const simple_language_json_1 = __importDefault(require("./simple-language.json"));
const intelligence_indicators_1 = require("./intelligence-indicators");
const ConfluenceResults = ({ data, usageCount = 0, onEditTitle, onCreatePage, onOpenInBrowser, onCopyLink, onRetry, onCancel, onUpdateSettings, }) => {
    const isAuthError = 'error' in data && (data.error === 'auth' || (data.message && /credential|invalid.*token|unauthorized/i.test(data.message)));
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
                React.createElement("strong", null, "Message:"),
                " ",
                isAuthError ? simple_language_json_1.default.phrases.errors.auth : data.message),
            React.createElement("div", { style: { fontSize: '12px', marginBottom: '12px', padding: '8px', backgroundColor: 'var(--vscode-textBlockQuote-background)', borderRadius: '2px' } },
                React.createElement("strong", null, "\uD83D\uDCA1 Suggestion:"),
                " ",
                data.intelligence_suggestion),
            React.createElement("div", { style: { display: 'flex', justifyContent: 'flex-end', gap: '8px' } },
                onCancel && React.createElement("button", { onClick: onCancel, style: { padding: '4px 12px', cursor: 'pointer' } }, "Cancel"),
                isAuthError && onUpdateSettings && React.createElement("button", { onClick: onUpdateSettings, style: { padding: '4px 12px', cursor: 'pointer', backgroundColor: 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', border: 'none' } }, simple_language_json_1.default.buttons.updateSettings),
                onRetry && React.createElement("button", { onClick: onRetry, style: { padding: '4px 12px', cursor: 'pointer', backgroundColor: 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', border: 'none' } }, "Retry"))));
    }
    if ('success' in data) {
        const confidencePct = Math.round((data.intelligence_summary.intelligence_confidence?.overall_intelligence ?? 0) * 100);
        const templateLabel = data.intelligence_summary.ai_decisions_made?.[1] ?? data.intelligence_summary.ai_decisions_made?.[0] ?? 'Intelligent format';
        const showConfidence = usageCount >= 1 && confidencePct > 70;
        const showExplainChoice = usageCount >= 2 && data.intelligence_summary.ai_decisions_made?.length;
        const learning = data.learning;
        return (React.createElement("div", { className: "confluence-card success", style: {
                border: '1px solid #4CAF50',
                borderRadius: '4px',
                padding: '12px',
                backgroundColor: 'var(--vscode-editor-background)',
                maxWidth: '400px'
            } },
            React.createElement("h3", { style: { margin: '0 0 12px 0', fontSize: '14px', color: '#4CAF50', display: 'flex', alignItems: 'center' } },
                simple_language_json_1.default.phrases.firstInteraction.success,
                " ",
                React.createElement(intelligence_indicators_1.AiFormattedBadge, null)),
            usageCount >= 1 && (React.createElement("div", { className: "success-encouragement", style: { marginTop: '10px', fontStyle: 'italic', color: '#2E7D32', fontSize: '12px' } }, simple_language_json_1.default.phrases.encouragement[0])),
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
                templateLabel),
            showConfidence && React.createElement("div", { style: { fontSize: '12px', marginBottom: '12px', color: (0, intelligence_indicators_1.getConfidenceColor)(confidencePct) }, title: simple_language_json_1.default.phrases.confidenceTooltip ?? 'Intelligence Confidence: How sure AI is about this decision' },
                React.createElement("strong", null,
                    simple_language_json_1.default.phrases.confidence,
                    ":"),
                " ",
                confidencePct,
                "%"),
            React.createElement("div", { style: { marginBottom: '12px' } },
                React.createElement("div", { style: { fontSize: '12px', fontWeight: 'bold', marginBottom: '4px' } }, "\uD83D\uDD17 Page Link:"),
                React.createElement("div", { style: { fontSize: '11px', color: 'var(--vscode-textLink-foreground)', wordBreak: 'break-all' } }, data.intelligent_page.url)),
            showExplainChoice && (React.createElement("details", { style: { fontSize: '12px', marginBottom: '12px' }, className: "explain-choice" },
                React.createElement("summary", null, simple_language_json_1.default.phrases.explainChoice),
                React.createElement("ul", { style: { margin: '4px 0 0', paddingLeft: '16px' } }, data.intelligence_summary.ai_decisions_made.map((decision, i) => (React.createElement("li", { key: i }, decision)))))),
            learning && React.createElement(intelligence_indicators_1.LearningIndicator, { examplesCount: data.intelligence_summary.examples_learned }),
            React.createElement("div", { style: { display: 'flex', gap: '8px' } },
                React.createElement("button", { onClick: () => onOpenInBrowser?.(data.intelligent_page.url), style: { flex: 1, padding: '4px', cursor: 'pointer', backgroundColor: 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', border: 'none' } }, simple_language_json_1.default.buttons.viewPage),
                React.createElement("button", { onClick: () => onCopyLink?.(data.intelligent_page.url), style: { flex: 1, padding: '4px', cursor: 'pointer' } }, simple_language_json_1.default.buttons.copyLink))));
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
