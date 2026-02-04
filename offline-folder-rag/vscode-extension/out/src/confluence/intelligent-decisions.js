"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.IntelligentDecisions = void 0;
const React = require("react");
const TITLE_MAX_LENGTH = 255;
const LOW_CONFIDENCE_THRESHOLD = 0.7;
function parseMatchesCount(reason) {
    if (!reason)
        return null;
    const m = reason.match(/Matches\s+(\d+)\s+similar/);
    return m ? parseInt(m[1], 10) : null;
}
const IntelligentDecisions = (props) => {
    const { analyzeResponse, errorResponse, fileCount = 0, onCreate, onCreateFallback, baseUrl = '', space = 'DOC', auth, files = [], } = props;
    const [titleEditMode, setTitleEditMode] = React.useState(false);
    const [editedTitle, setEditedTitle] = React.useState('');
    const [explainExpanded, setExplainExpanded] = React.useState(false);
    const analysis = analyzeResponse?.intelligence_analysis;
    const recommendation = analyzeResponse?.intelligent_recommendation;
    const suggestedTitle = analysis?.intelligent_title ?? '';
    const displayTitle = titleEditMode ? editedTitle : suggestedTitle;
    const confidence = analysis?.intelligence_confidence ?? 0;
    const confidencePct = Math.round(confidence * 100);
    const isLowConfidence = confidence < LOW_CONFIDENCE_THRESHOLD;
    const isNoMatch = errorResponse?.error === 'intelligence_error' && errorResponse?.fallback_available === true;
    React.useEffect(() => {
        if (!titleEditMode)
            setEditedTitle(suggestedTitle);
    }, [suggestedTitle, titleEditMode]);
    const handleEditTitle = () => {
        setEditedTitle(suggestedTitle);
        setTitleEditMode(true);
    };
    const handleTitleChange = (e) => {
        const v = e.target.value;
        if (v.length <= TITLE_MAX_LENGTH)
            setEditedTitle(v);
    };
    const handleCreate = () => {
        if (!onCreate)
            return;
        const titleToUse = titleEditMode ? editedTitle : suggestedTitle;
        const wasEdited = titleEditMode && editedTitle !== suggestedTitle;
        const fileList = Array.isArray(files)
            ? files.map((f) => (typeof f === 'string' ? f : f.content))
            : [];
        onCreate({
            files: fileList.length ? fileList : [],
            intelligent_mode: true,
            auto_title: !wasEdited,
            space,
            intelligence_context: wasEdited ? { title_override: titleToUse } : { suggested_title: titleToUse },
            base_url: baseUrl,
            auth,
        });
    };
    const matchesCount = recommendation ? parseMatchesCount(recommendation.intelligence_reason) : null;
    const style = {
        fontFamily: 'var(--vscode-font-family)',
        fontSize: '13px',
        padding: '12px',
    };
    if (isNoMatch && errorResponse) {
        return (React.createElement("div", { style: style },
            React.createElement("div", { style: { fontWeight: 600, marginBottom: '8px' } }, "No template match found"),
            React.createElement("p", { style: { margin: '8px 0', opacity: 0.9 } }, errorResponse.message),
            React.createElement("button", { type: "button", onClick: onCreateFallback, style: {
                    padding: '8px 12px',
                    marginTop: '8px',
                    cursor: 'pointer',
                } }, "Use Intelligent Fallback Template")));
    }
    if (!analysis || !recommendation) {
        return (React.createElement("div", { style: style },
            React.createElement("div", { style: { opacity: 0.8 } }, "Run analysis to see intelligent decisions.")));
    }
    const cb = recommendation.confidence_breakdown;
    const contentTypes = analysis.content_types ?? [];
    const detectedPatterns = analysis.detected_patterns ?? [];
    return (React.createElement("div", { style: style },
        React.createElement("div", { style: { fontWeight: 600, marginBottom: '8px' } }, "Let AI Decide"),
        fileCount > 1 && (React.createElement("p", { style: { margin: '4px 0', fontSize: '12px', opacity: 0.9 } },
            "Intelligently combining ",
            fileCount,
            " files as comprehensive documentation")),
        contentTypes.length > 0 && (React.createElement("div", { style: { marginBottom: '8px', fontSize: '12px' } },
            React.createElement("span", { style: { opacity: 0.8 } }, "Detected: "),
            contentTypes.join(', '),
            detectedPatterns.length > 0 && ` · ${detectedPatterns.join(', ')}`)),
        React.createElement("div", { style: { marginBottom: '8px' } },
            React.createElement("strong", null, "Intelligent Format Selected:"),
            " \"",
            recommendation.template_name,
            "\" template"),
        matchesCount !== null && (React.createElement("div", { style: { marginBottom: '8px', fontSize: '12px', opacity: 0.9 } },
            "(Matches ",
            matchesCount,
            " similar successful examples)")),
        React.createElement("div", { style: { marginBottom: '8px' } },
            React.createElement("strong", null, "Suggested Title:"),
            ' ',
            !titleEditMode ? (React.createElement(React.Fragment, null,
                "[",
                displayTitle || '—',
                "]",
                React.createElement("button", { type: "button", onClick: handleEditTitle, style: { marginLeft: '8px', padding: '2px 8px', cursor: 'pointer' } }, "Edit Title"))) : (React.createElement(React.Fragment, null,
                React.createElement("input", { type: "text", value: editedTitle, onChange: handleTitleChange, maxLength: TITLE_MAX_LENGTH, style: { width: '100%', maxWidth: '400px', padding: '4px' }, "aria-label": "Title" }),
                React.createElement("span", { style: { marginLeft: '8px', fontSize: '11px', opacity: 0.8 } },
                    editedTitle.length,
                    "/",
                    TITLE_MAX_LENGTH)))),
        React.createElement("div", { style: { marginBottom: '8px' } },
            React.createElement("strong", null, "Confidence:"),
            " ",
            confidencePct,
            "%"),
        cb && (React.createElement("div", { style: { marginBottom: '8px', fontSize: '12px' } },
            "Content: ",
            Math.round((cb.content_match ?? 0) * 100),
            "% \u00B7 Structure:",
            ' ',
            Math.round((cb.structure_match ?? 0) * 100),
            "% \u00B7 Context:",
            ' ',
            Math.round((cb.context_match ?? 0) * 100),
            "%")),
        isLowConfidence && (React.createElement("div", { style: { marginBottom: '8px', padding: '8px', background: 'var(--vscode-inputValidation-warningBackground)', borderLeft: '4px solid var(--vscode-inputValidation-warningBorder)' } },
            React.createElement("strong", null, "Intelligence Confidence Low"),
            React.createElement("br", null),
            React.createElement("button", { type: "button", onClick: onCreateFallback, style: { marginTop: '4px', padding: '4px 8px', cursor: 'pointer' } }, "Use Intelligent Fallback Template"))),
        React.createElement("div", { style: { marginBottom: '8px' } },
            React.createElement("button", { type: "button", onClick: () => setExplainExpanded(!explainExpanded), style: { padding: '4px 8px', cursor: 'pointer', marginBottom: '4px' } }, explainExpanded ? 'Hide' : 'Explain AI Choice'),
            explainExpanded && (React.createElement("div", { style: { padding: '8px', background: 'var(--vscode-editor-inactiveSelectionBackground)', borderRadius: '4px', fontSize: '12px' } },
                React.createElement("div", { style: { marginBottom: '4px' } }, recommendation.intelligence_reason),
                analysis.ai_reasoning && (React.createElement("div", { style: { opacity: 0.9 } }, analysis.ai_reasoning))))),
        React.createElement("div", { style: { marginTop: '12px' } },
            React.createElement("strong", null, "What made this intelligent:"),
            React.createElement("div", { style: { marginTop: '4px', fontSize: '12px', opacity: 0.9 } }, recommendation.intelligence_reason)),
        React.createElement("button", { type: "button", onClick: handleCreate, disabled: !onCreate, style: { marginTop: '12px', padding: '8px 16px', cursor: onCreate ? 'pointer' : 'default' } }, "Create Perfect Page")));
};
exports.IntelligentDecisions = IntelligentDecisions;
