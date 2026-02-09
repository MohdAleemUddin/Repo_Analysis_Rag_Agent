import * as React from 'react';
import { getAiFormattedBadgeHtml, getLearningIndicatorHtml, getConfidenceColor } from './badges';

export { getAiFormattedBadgeHtml, getLearningIndicatorHtml, getConfidenceColor };

export const AiFormattedBadge: React.FC = () => (
    <span style={{ background: '#4CAF50', color: 'white', fontSize: '10px', padding: '2px 6px', borderRadius: '3px', fontWeight: 'bold', marginLeft: '6px' }}>
        AI-Formatted
    </span>
);

export const LearningIndicator: React.FC<{ examplesCount?: number }> = ({ examplesCount }) => (
    <div style={{ fontSize: '12px', marginBottom: '12px', padding: '10px', background: 'var(--vscode-textBlockQuote-background)', borderRadius: '6px', borderLeft: '3px solid var(--vscode-testing-iconPassed)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
            <span>🎓</span>
            <strong>Intelligence Learning: System learned from this successful creation</strong>
        </div>
        <div style={{ fontSize: '11px', color: 'var(--vscode-descriptionForeground)' }}>
            {examplesCount != null ? `Added to ${examplesCount} similar examples for future matching` : 'Added to similar examples for future matching'}
        </div>
    </div>
);

export const IntelligenceIndicators: React.FC = () => null;
