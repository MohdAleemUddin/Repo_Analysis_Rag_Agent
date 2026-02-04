"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfluenceFeedback = void 0;
const React = require("react");
const ConfluenceFeedback = ({ learningIndicator = false, importedCount = null, collectiveIntelligenceCount = null, onFeedbackSubmit, creationId = null, }) => {
    const [score, setScore] = React.useState(null);
    const [comment, setComment] = React.useState('');
    const [submitted, setSubmitted] = React.useState(false);
    const handleSubmit = () => {
        if (score !== null && creationId && onFeedbackSubmit) {
            onFeedbackSubmit(creationId, score, comment || undefined);
            setSubmitted(true);
        }
    };
    return (React.createElement("div", { className: "confluence-feedback" },
        learningIndicator && (React.createElement("div", { className: "confluence-learning-indicator", role: "status" }, "\uD83C\uDF93 Intelligence Learning: System learned from this successful creation")),
        importedCount !== null && importedCount !== undefined && (React.createElement("div", { className: "confluence-imported-count", role: "status" },
            "Intelligence Examples Imported: ",
            importedCount,
            " new examples learned")),
        collectiveIntelligenceCount !== null && collectiveIntelligenceCount !== undefined && (React.createElement("div", { className: "confluence-collective-intelligence", role: "status" },
            "Collective Intelligence: ",
            collectiveIntelligenceCount,
            " examples from team")),
        onFeedbackSubmit && creationId && (React.createElement("div", { className: "confluence-feedback-form" },
            React.createElement("label", null, "Rate this creation (1\u20135)"),
            React.createElement("div", { className: "confluence-feedback-stars" }, [1, 2, 3, 4, 5].map((n) => (React.createElement("button", { key: n, type: "button", "aria-label": `${n} star${n > 1 ? 's' : ''}`, onClick: () => setScore(n), className: score === n ? 'selected' : '' }, n)))),
            React.createElement("input", { type: "text", placeholder: "Optional feedback", value: comment, onChange: (e) => setComment(e.target.value), "aria-label": "Optional feedback" }),
            React.createElement("button", { type: "button", onClick: handleSubmit, disabled: submitted || score === null }, submitted ? 'Submitted' : 'Submit feedback')))));
};
exports.ConfluenceFeedback = ConfluenceFeedback;
