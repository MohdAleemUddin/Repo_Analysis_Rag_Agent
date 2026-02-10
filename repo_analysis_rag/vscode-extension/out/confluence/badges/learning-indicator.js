"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.getLearningIndicatorHtml = getLearningIndicatorHtml;
function getLearningIndicatorHtml(options) {
    const base = "Intelligence Learning: System learned from this successful creation";
    const sub = options?.examplesCount != null
        ? `Added to ${options.examplesCount} similar examples for future matching`
        : "Added to similar examples for future matching";
    return `<div style="font-size:12px;margin-bottom:16px;padding:10px;background:var(--vscode-textBlockQuote-background);border-radius:6px;border-left:3px solid var(--vscode-testing-iconPassed);">
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
      <span>🎓</span>
      <strong>${base}</strong>
    </div>
    <div style="font-size:11px;color:var(--vscode-descriptionForeground);">${sub}</div>
  </div>`;
}
