import * as React from 'react';
import { AnalyzeResponse, CreateResponse, ErrorResponse } from './types';

interface ConfluenceResultsProps {
  data: AnalyzeResponse | CreateResponse | ErrorResponse;
  onEditTitle?: (newTitle: string) => void;
  onCreatePage?: () => void;
  onOpenInBrowser?: (url: string) => void;
  onCopyLink?: (url: string) => void;
  onRetry?: () => void;
  onCancel?: () => void;
}

export const ConfluenceResults: React.FC<ConfluenceResultsProps> = ({ 
  data, 
  onEditTitle, 
  onCreatePage,
  onOpenInBrowser,
  onCopyLink,
  onRetry,
  onCancel
}) => {
  // Check if it's an error response
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
          <strong>Error:</strong> {data.error}
        </div>
        <div style={{ fontSize: '12px', marginBottom: '8px' }}>
          <strong>Message:</strong> {data.message}
        </div>
        <div style={{ fontSize: '12px', marginBottom: '12px', padding: '8px', backgroundColor: 'var(--vscode-textBlockQuote-background)', borderRadius: '2px' }}>
          <strong>💡 AI Suggestion:</strong> {data.intelligence_suggestion}
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
          {onCancel && <button onClick={onCancel} style={{ padding: '4px 12px', cursor: 'pointer' }}>Cancel</button>}
          {onRetry && <button onClick={onRetry} style={{ padding: '4px 12px', cursor: 'pointer', backgroundColor: 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', border: 'none' }}>Retry</button>}
        </div>
      </div>
    );
  }

  // Check if it's a success response (CreateResponse)
  if ('success' in data) {
    return (
      <div className="confluence-card success" style={{
        border: '1px solid #4CAF50',
        borderRadius: '4px',
        padding: '12px',
        backgroundColor: 'var(--vscode-editor-background)',
        maxWidth: '400px'
      }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#4CAF50' }}>✅ Intelligent Documentation Created!</h3>
        <div style={{ fontSize: '12px', marginBottom: '4px' }}><strong>Title:</strong> {data.intelligent_page.title}</div>
        <div style={{ fontSize: '12px', marginBottom: '4px' }}><strong>Space:</strong> {data.intelligent_page.space}</div>
        <div style={{ fontSize: '12px', marginBottom: '4px' }}><strong>Intelligent Format:</strong> {data.intelligence_summary.ai_decisions_made[1]}</div>
        <div style={{ fontSize: '12px', marginBottom: '12px' }}><strong>Confidence:</strong> {Math.round(data.intelligence_summary.intelligence_confidence.overall_intelligence * 100)}%</div>
        
        <div style={{ marginBottom: '12px' }}>
          <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '4px' }}>🔗 Page Link:</div>
          <div style={{ fontSize: '11px', color: 'var(--vscode-textLink-foreground)', wordBreak: 'break-all' }}>{data.intelligent_page.url}</div>
        </div>

        <div style={{ fontSize: '12px', marginBottom: '12px' }}>
          <div style={{ fontWeight: 'bold', marginBottom: '4px' }}>📊 What made this intelligent:</div>
          <ul style={{ margin: '0', paddingLeft: '16px' }}>
            {data.intelligence_summary.ai_decisions_made.map((decision, i) => (
              <li key={i}>{decision}</li>
            ))}
          </ul>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button onClick={() => onOpenInBrowser?.(data.intelligent_page.url)} style={{ flex: 1, padding: '4px', cursor: 'pointer', backgroundColor: 'var(--vscode-button-background)', color: 'var(--vscode-button-foreground)', border: 'none' }}>Open in Browser</button>
          <button onClick={() => onCopyLink?.(data.intelligent_page.url)} style={{ flex: 1, padding: '4px', cursor: 'pointer' }}>Copy Link</button>
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
