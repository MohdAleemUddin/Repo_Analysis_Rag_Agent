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
exports.IntelligenceIndicators = exports.LearningIndicator = exports.AiFormattedBadge = exports.getConfidenceColor = exports.getLearningIndicatorHtml = exports.getAiFormattedBadgeHtml = void 0;
const React = __importStar(require("react"));
const badges_1 = require("./badges");
Object.defineProperty(exports, "getAiFormattedBadgeHtml", { enumerable: true, get: function () { return badges_1.getAiFormattedBadgeHtml; } });
Object.defineProperty(exports, "getLearningIndicatorHtml", { enumerable: true, get: function () { return badges_1.getLearningIndicatorHtml; } });
Object.defineProperty(exports, "getConfidenceColor", { enumerable: true, get: function () { return badges_1.getConfidenceColor; } });
const AiFormattedBadge = () => (React.createElement("span", { style: { background: '#4CAF50', color: 'white', fontSize: '10px', padding: '2px 6px', borderRadius: '3px', fontWeight: 'bold', marginLeft: '6px' } }, "AI-Formatted"));
exports.AiFormattedBadge = AiFormattedBadge;
const LearningIndicator = ({ examplesCount }) => (React.createElement("div", { style: { fontSize: '12px', marginBottom: '12px', padding: '10px', background: 'var(--vscode-textBlockQuote-background)', borderRadius: '6px', borderLeft: '3px solid var(--vscode-testing-iconPassed)' } },
    React.createElement("div", { style: { display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' } },
        React.createElement("span", null, "\uD83C\uDF93"),
        React.createElement("strong", null, "Intelligence Learning: System learned from this successful creation")),
    React.createElement("div", { style: { fontSize: '11px', color: 'var(--vscode-descriptionForeground)' } }, examplesCount != null ? `Added to ${examplesCount} similar examples for future matching` : 'Added to similar examples for future matching')));
exports.LearningIndicator = LearningIndicator;
const IntelligenceIndicators = () => null;
exports.IntelligenceIndicators = IntelligenceIndicators;
