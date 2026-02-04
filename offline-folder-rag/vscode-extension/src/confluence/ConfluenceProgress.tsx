import * as React from 'react';

interface ProgressStep {
  label: string;
  status: 'pending' | 'active' | 'completed' | 'error';
}

interface ConfluenceProgressProps {
  steps: ProgressStep[];
  estimatedSeconds: number;
  percent: number;
  onCancel?: () => void;
}

export const ConfluenceProgress: React.FC<ConfluenceProgressProps> = ({ 
  steps, 
  estimatedSeconds, 
  percent,
  onCancel 
}) => {
  return (
    <div className="confluence-card progress" style={{
      border: '1px solid var(--vscode-widget-border)',
      borderRadius: '4px',
      padding: '12px',
      backgroundColor: 'var(--vscode-editor-background)',
      maxWidth: '400px'
    }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '14px' }}>⏳ Creating Intelligent Documentation...</h3>
      
      <div style={{ marginBottom: '16px' }}>
        {steps.map((step, i) => (
          <div key={i} style={{ display: 'flex', alignItems: 'center', marginBottom: '4px', fontSize: '12px' }}>
            <span style={{ marginRight: '8px' }}>
              {step.status === 'completed' ? '✓' : 
               step.status === 'active' ? '●' : 
               step.status === 'error' ? '❌' : '○'}
            </span>
            <span style={{ 
              color: step.status === 'pending' ? 'var(--vscode-descriptionForeground)' : 'inherit',
              fontWeight: step.status === 'active' ? 'bold' : 'normal'
            }}>
              {step.label}
            </span>
            {step.status === 'active' && <span style={{ marginLeft: '8px' }}>███</span>}
            {step.status === 'pending' && <span style={{ marginLeft: '8px' }}>▓▓▓</span>}
          </div>
        ))}
      </div>

      <div style={{ marginBottom: '8px' }}>
        <div style={{ 
          height: '4px', 
          width: '100%', 
          backgroundColor: 'var(--vscode-progressBar-background)', 
          borderRadius: '2px',
          overflow: 'hidden'
        }}>
          <div style={{ 
            height: '100%', 
            width: `${percent}%`, 
            backgroundColor: 'var(--vscode-progressBar-foreground)',
            transition: 'width 0.3s ease'
          }} />
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginTop: '4px', opacity: 0.8 }}>
          <span>{percent}%</span>
          <span>Estimated: {estimatedSeconds} seconds</span>
        </div>
      </div>

      {onCancel && (
        <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
          <button onClick={onCancel} style={{ padding: '2px 8px', fontSize: '11px', cursor: 'pointer' }}>Cancel</button>
        </div>
      )}
    </div>
  );
};
