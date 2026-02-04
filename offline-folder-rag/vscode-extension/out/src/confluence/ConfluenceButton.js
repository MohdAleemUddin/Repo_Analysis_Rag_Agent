"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ConfluenceButton = void 0;
const React = require("react");
const ConfluenceButton = ({ onClick, disabled }) => {
    return (React.createElement("button", { className: "confluence-save-button", onClick: onClick, disabled: disabled, title: "Save to Confluence", style: {
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '4px 8px',
            backgroundColor: 'var(--vscode-button-secondaryBackground)',
            color: 'var(--vscode-button-secondaryForeground)',
            border: 'none',
            borderRadius: '2px',
            cursor: disabled ? 'not-allowed' : 'pointer',
            opacity: disabled ? 0.5 : 1,
            marginLeft: '4px'
        } },
        React.createElement("span", { style: { marginRight: '4px' } }, "\uD83D\uDCBE"),
        "Save to Confluence"));
};
exports.ConfluenceButton = ConfluenceButton;
