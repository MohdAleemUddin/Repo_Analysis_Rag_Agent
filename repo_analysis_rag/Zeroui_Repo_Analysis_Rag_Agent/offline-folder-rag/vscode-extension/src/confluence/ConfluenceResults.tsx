import * as React from 'react';
import { AnalyzeResponse, CreateResponse, ErrorResponse } from './types';
import messages from './simple-language.json';
import { AiFormattedBadge, LearningIndicator, getConfidenceColor } from './intelligence-indicators';

interface ConfluenceResultsProps {
  data: AnalyzeResponse | CreateResponse | ErrorResponse;
  usageCount?: number;
  onEditTitle?: (newTitle: string) => void;
  onCreatePage?: () => void;
  onOpenInBrowser?: (url: string) => void;
  onCopyLink?: (url: string) => void;
  onRetry?: () => void;
  onCancel?: () => void;
  onUpdateSettings?: () => void;
}

export const ConfluenceResults: React.FC<ConfluenceResultsProps> = ({
  data,
  usageCount = 0,
  onEditTitle,
  onCreatePage,
  onOpenInBrowser,
  onCopyLink,
  onRetry,
  onCancel,
  onUpdateSettings,
}) => {
  const isAuthError = 'error' in data && (data.error === 'auth' || (data.message && /credential|invalid.*token|unauthorized/i.test(data.message)));

  if ('error' in data) {
    return (
      <div className="confluence-card error" style={{
        border: '1px solid var(--vscode-errorForeground)',
        borderRadius: '4px',
        padding: '12px',
        backgroundColor: 'var(--vscode-editor-background)',
        maxWidth: '400px'
      }}>
        <h3 style={{ margin: '0 0 8px 0', fontSize: '14px', color: 'var(--vscode-errorForeground)' }}>❌ Intelligence Error</h3>
        <div style={{ fontSize: '12px', marginBottom: '8px' }}>
          <strong>Message:</strong> {isAuthError ? messages.phrases.errors.auth : data.message}
        </div>
        <div style={{ fontSize: '12px', marginBottom: '12px', padding: '8px', backgroundColor: 'var(--vscode-textBlockQuote-background)', borderRadius: '2px' }}>
          <strong>💡 Suggestion:</strong> {data.intelligence_suggestion}
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          {onCancel && <button onClick={onCancel} style={{ padding: '4px 12px', cursor: 'pointer' }}>Cancel</button>}
          {isAuthError && onUpdateSettings && <button onClick={onUpdateSettings} style={{ padding: '4px 12px', cursor: 'pointer', backgroundColor: 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', border: 'none' }}>{messages.buttons.updateSettings}</button>}
          {onRetry && <button onClick={onRetry} style={{ padding: '4px 12px', cursor: 'pointer', backgroundColor: 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', border: 'none' }}>Retry</button>}
        </div>
      </div>
    );
  }

  if ('success' in data) {
    const confidencePct = Math.round((data.intelligence_summary.intelligence_confidence?.overall_intelligence ?? 0) * 100);
    const templateLabel = data.intelligence_summary.ai_decisions_made?.[1] ?? data.intelligence_summary.ai_decisions_made?.[0] ?? 'Intelligent format';
    const showConfidence = usageCount >= 1 && confidencePct > 70;
    const showExplainChoice = usageCount >= 2 && data.intelligence_summary.ai_decisions_made?.length;
    const learning = (data as CreateResponse & { learning?: boolean }).learning;

    return (
      <div className="confluence-card success" style={{
        border: '1px solid #4CAF50',
        borderRadius: '4px',
        padding: '12px',
        backgroundColor: 'var(--vscode-editor-background)',
        maxWidth: '400px'
      }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#4CAF50', display: 'flex', alignItems: 'center' }}>{messages.phrases.firstInteraction.success} <AiFormattedBadge /></h3>
        {usageCount >= 1 && (
          <div className="success-encouragement" style={{ marginTop: '10px', fontStyle: 'italic', color: '#2E7D32', fontSize: '12px' }}>
            {messages.phrases.encouragement[0]}
          </div>
        )}
        <div style={{ fontSize: '12px', marginBottom: '4px' }}><strong>Title:</strong> {data.intelligent_page.title}</div>
        <div style={{ fontSize: '12px', marginBottom: '4px' }}><strong>Space:</strong> {data.intelligent_page.space}</div>
        <div style={{ fontSize: '12px', marginBottom: '4px' }}><strong>Intelligent Format:</strong> {templateLabel}</div>
        {showConfidence && <div style={{ fontSize: '12px', marginBottom: '12px', color: getConfidenceColor(confidencePct) }} title={(messages.phrases as { confidenceTooltip?: string }).confidenceTooltip ?? 'Intelligence Confidence: How sure AI is about this decision'}><strong>{messages.phrases.confidence}:</strong> {confidencePct}%</div>}

        <div style={{ marginBottom: '12px' }}>
          <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '4px' }}>🔗 Page Link:</div>
          <div style={{ fontSize: '11px', color: 'var(--vscode-textLink-foreground)', wordBreak: 'break-all' }}>{data.intelligent_page.url}</div>
        </div>

        {showExplainChoice && (
          <details style={{ fontSize: '12px', marginBottom: '12px' }} className="explain-choice">
            <summary>{messages.phrases.explainChoice}</summary>
            <ul style={{ margin: '4px 0 0', paddingLeft: '16px' }}>
              {data.intelligence_summary.ai_decisions_made.map((decision, i) => (
                <li key={i}>{decision}</li>
              ))}
            </ul>
          </details>
        )}

        {learning && <LearningIndicator examplesCount={(data.intelligence_summary as { examples_learned?: number }).examples_learned} />}

        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => onOpenInBrowser?.(data.intelligent_page.url)} style={{ flex: 1, padding: '4px', cursor: 'pointer', backgroundColor: 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', border: 'none' }}>{messages.buttons.viewPage}</button>
          <button onClick={() => onCopyLink?.(data.intelligent_page.url)} style={{ flex: 1, padding: '4px', cursor: 'pointer' }}>{messages.buttons.copyLink}</button>
        </div>
      </div>
    );
  }

  // Otherwise it's an analysis response (AnalyzeResponse)
  return (
    <div className="confluence-card analysis" style={{
      border: '1px solid var(--vscode-widget-border)',
      borderRadius: '4px',
      padding: '12px',
      backgroundColor: 'var(--vscode-editor-background)',
      maxWidth: '400px'
    }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '14px' }}>🤖 Intelligent Analysis Complete</h3>
      <div style={{ fontSize: '12px', marginBottom: '8px' }}>
        <strong>Files:</strong> {data.intelligence_analysis.content_types.join(', ')}
      </div>
      
      <div style={{ fontSize: '12px', marginBottom: '12px' }}>
        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>🧠 AI Detected:</div>
        <ul style={{ margin: '0', paddingLeft: '16px' }}>
          {data.intelligence_analysis.detected_patterns.map((pattern, i) => (
            <li key={i}>{pattern}</li>
          ))}
        </ul>
      </div>

      <div style={{ fontSize: '12px', marginBottom: '12px', padding: '8px', backgroundColor: 'var(--vscode-textBlockQuote-background)', borderRadius: '2px' }}>
        <div style={{ fontWeight: 'bold', color: 'var(--vscode-textLink-foreground)' }}>🎯 Intelligent Format Selected:</div>
        <div>"{data.intelligent_recommendation.template_name}"</div>
        <div style={{ fontSize: '11px', opacity: 0.8 }}>({data.intelligent_recommendation.intelligence_reason})</div>
      </div>

      <div style={{ fontSize: '12px', marginBottom: '12px' }}>
        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>📝 Suggested Title:</div>
        <div style={{ padding: '4px', border: '1px solid var(--vscode-input-border)', borderRadius: '2px' }}>
          {data.intelligence_analysis.intelligent_title}
        </div>
      </div>

      <div style={{ fontSize: '12px', marginBottom: '16px' }}>
        <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>📍 Confluence Space:</div>
        <select style={{ width: '100%', padding: '2px', backgroundColor: 'var(--vscode-select-background)', color: 'var(--vscode-select-foreground)', border: '1px solid var(--vscode-select-border)' }}>
          <option>DEV</option>
          <option>DOCS</option>
        </select>
      </div>

      <div style={{ display: 'flex', gap: '8px' }}>
        <button 
          onClick={() => {
            const newTitle = prompt('Edit Title', data.intelligence_analysis.intelligent_title);
            if (newTitle) onEditTitle?.(newTitle);
          }} 
          style={{ flex: 1, padding: '4px', cursor: 'pointer' }}
        >
          Edit Title
        </button>
        <button 
          onClick={onCreatePage} 
          style={{ flex: 1, padding: '4px', cursor: 'pointer', backgroundColor: 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', border: 'none' }}
        >
          Create Perfect Page
        </button>
      </div>
    </div>
  );
};
