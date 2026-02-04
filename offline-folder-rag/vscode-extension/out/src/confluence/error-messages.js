"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ErrorMessages = void 0;
const React = require("react");
const ErrorMessages = ({ error, helpLink, onUpdateSettings, onRetry, onCancel, }) => {
    const actions = error.actions ?? ['Retry', 'Cancel'];
    return (React.createElement("div", { className: "confluence-error-messages" },
        React.createElement("div", { className: "confluence-error-message" }, error.message),
        React.createElement("div", { className: "confluence-error-suggestion" }, error.intelligence_suggestion),
        error.fallback_available && (React.createElement("div", { className: "confluence-error-fallback" }, "Fallback available.")),
        React.createElement("div", { className: "confluence-error-actions" },
            actions.includes('Update Settings') && (React.createElement("button", { type: "button", onClick: onUpdateSettings }, "Update Settings")),
            actions.includes('Retry') && (React.createElement("button", { type: "button", onClick: onRetry }, "Retry")),
            actions.includes('Cancel') && (React.createElement("button", { type: "button", onClick: onCancel }, "Cancel"))),
        helpLink && (React.createElement("a", { href: helpLink, target: "_blank", rel: "noopener noreferrer", className: "confluence-error-help" }, "Help"))));
};
exports.ErrorMessages = ErrorMessages;
