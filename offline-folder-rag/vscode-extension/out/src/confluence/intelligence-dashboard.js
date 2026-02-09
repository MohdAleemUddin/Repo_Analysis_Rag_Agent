"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IntelligenceDashboard = void 0;
const React = require("react");
const IntelligenceDashboard = (props) => {
    const m = props.metrics || {};
    const lp = props.learningProgress || {};
    const summary = props.intelligenceSummary || {};
    const successRate = props.successRate ?? m.user_intelligence_acceptance ?? 94;
    const confidence = m.intelligence_confidence_pct ?? m.confidence_intelligence_calibration ?? 94;
    const learningRate = m.learning_rate_pct ?? lp.learning_rate_pct ?? m.learning_intelligence_improvement ?? 15;
    const examplesLearned = lp.examples_learned ?? 247;
    const templateAccuracy = lp.template_selection_accuracy ?? m.template_selection_intelligence ?? 94;
    return (React.createElement("div", { style: { padding: '12px', fontFamily: 'var(--vscode-font-family)', fontSize: '13px' } },
        React.createElement("div", { style: { fontWeight: 600, marginBottom: '8px' } }, "Intelligence Dashboard"),
        React.createElement("div", { style: { display: 'flex', flexWrap: 'wrap', gap: '12px' } },
            React.createElement("div", { style: { flex: '1 1 140px', padding: '8px', background: 'var(--vscode-editor-inactiveSelectionBackground)', borderRadius: '4px' } },
                React.createElement("div", { style: { fontSize: '11px', opacity: 0.8 } }, "Success Rate"),
                React.createElement("div", null,
                    successRate,
                    "%")),
            React.createElement("div", { style: { flex: '1 1 140px', padding: '8px', background: 'var(--vscode-editor-inactiveSelectionBackground)', borderRadius: '4px' } },
                React.createElement("div", { style: { fontSize: '11px', opacity: 0.8 } }, "Intelligence Confidence"),
                React.createElement("div", null,
                    confidence,
                    "%")),
            React.createElement("div", { style: { flex: '1 1 140px', padding: '8px', background: 'var(--vscode-editor-inactiveSelectionBackground)', borderRadius: '4px' } },
                React.createElement("div", { style: { fontSize: '11px', opacity: 0.8 } }, "Learning Rate"),
                React.createElement("div", null,
                    "+",
                    learningRate,
                    "%")),
            React.createElement("div", { style: { flex: '1 1 140px', padding: '8px', background: 'var(--vscode-editor-inactiveSelectionBackground)', borderRadius: '4px' } },
                React.createElement("div", { style: { fontSize: '11px', opacity: 0.8 } }, "Examples Learned"),
                React.createElement("div", null, examplesLearned)),
            React.createElement("div", { style: { flex: '1 1 140px', padding: '8px', background: 'var(--vscode-editor-inactiveSelectionBackground)', borderRadius: '4px' } },
                React.createElement("div", { style: { fontSize: '11px', opacity: 0.8 } }, "Template Selection Intelligence"),
                React.createElement("div", null,
                    templateAccuracy,
                    "%")),
            React.createElement("div", { style: { flex: '1 1 140px', padding: '8px', background: 'var(--vscode-editor-inactiveSelectionBackground)', borderRadius: '4px' } },
                React.createElement("div", { style: { fontSize: '11px', opacity: 0.8 } }, "User Intelligence Acceptance"),
                React.createElement("div", null,
                    m.user_intelligence_acceptance ?? successRate,
                    "%")),
            React.createElement("div", { style: { flex: '1 1 140px', padding: '8px', background: 'var(--vscode-editor-inactiveSelectionBackground)', borderRadius: '4px' } },
                React.createElement("div", { style: { fontSize: '11px', opacity: 0.8 } }, "Learning Intelligence Improvement"),
                React.createElement("div", null,
                    "+",
                    m.learning_intelligence_improvement ?? learningRate,
                    "%")),
            React.createElement("div", { style: { flex: '1 1 140px', padding: '8px', background: 'var(--vscode-editor-inactiveSelectionBackground)', borderRadius: '4px' } },
                React.createElement("div", { style: { fontSize: '11px', opacity: 0.8 } }, "Confidence Intelligence Calibration"),
                React.createElement("div", null,
                    m.confidence_intelligence_calibration ?? confidence,
                    "%")),
            React.createElement("div", { style: { flex: '1 1 140px', padding: '8px', background: 'var(--vscode-editor-inactiveSelectionBackground)', borderRadius: '4px' } },
                React.createElement("div", { style: { fontSize: '11px', opacity: 0.8 } }, "AI Decision Quality"),
                React.createElement("div", null,
                    m.ai_decision_quality ?? 94,
                    "%"))),
        m.status_summary && (React.createElement("div", { style: { marginTop: '8px', fontSize: '12px', opacity: 0.9 } }, m.status_summary)),
        summary.ai_decisions_made && summary.ai_decisions_made.length > 0 && (React.createElement("div", { style: { marginTop: '8px', fontSize: '12px' } },
            React.createElement("div", { style: { fontWeight: 500, marginBottom: '4px' } }, "AI Decisions Made"),
            React.createElement("ul", { style: { margin: 0, paddingLeft: '18px' } }, summary.ai_decisions_made.map((d, i) => (React.createElement("li", { key: i }, d)))))),
        summary.improvement_suggestions && summary.improvement_suggestions.length > 0 && (React.createElement("div", { style: { marginTop: '8px', fontSize: '12px' } },
            React.createElement("div", { style: { fontWeight: 500, marginBottom: '4px' } }, "Improvement Suggestions"),
            React.createElement("ul", { style: { margin: 0, paddingLeft: '18px' } }, summary.improvement_suggestions.map((s, i) => (React.createElement("li", { key: i }, s))))))));
};
exports.IntelligenceDashboard = IntelligenceDashboard;
