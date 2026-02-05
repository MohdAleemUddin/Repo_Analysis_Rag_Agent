import * as React from 'react';

export interface ConfluenceContextMenuProps {
  /** Pre-loaded content from right-click selection; when set, this content is sent to Confluence flow. */
  preloadedContent: string;
  /** Callback when user continues: passes the selection for Confluence (e.g. open file selector with this content). */
  onContinue: (content: string) => void;
  onCancel?: () => void;
}

/**
 * Right-click context menu: rag-confluence.saveSelection triggers chat message flow (NO PANEL).
 * This component shows when selection was pre-loaded in the chat interface.
 */
export const ConfluenceContextMenu: React.FC<ConfluenceContextMenuProps> = ({
  preloadedContent,
  onContinue,
  onCancel,
}) => {
  const len = (preloadedContent || '').length;
  const preview = (preloadedContent || '').slice(0, 120);
  const hasMore = len > 120;

  return (
    <div
      className="confluence-context-menu"
      style={{
        border: '1px solid var(--vscode-widget-border)',
        borderRadius: '4px',
        padding: '12px',
        backgroundColor: 'var(--vscode-editor-background)',
        maxWidth: '400px',
      }}
    >
      <h3 style={{ margin: '0 0 12px 0', fontSize: '14px' }}>
        Selection will be included in Confluence
      </h3>
      <div
        style={{
          fontSize: '12px',
          color: 'var(--vscode-descriptionForeground)',
          marginBottom: '8px',
        }}
      >
        {len} character{len !== 1 ? 's' : ''} selected. This content will be pre-loaded for Confluence.
      </div>
      {preview && (
        <pre
          style={{
            margin: '0 0 12px 0',
            padding: '8px',
            fontSize: '11px',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            border: '1px solid var(--vscode-input-border)',
            borderRadius: '2px',
            maxHeight: '60px',
          }}
        >
          {preview}
          {hasMore ? '…' : ''}
        </pre>
      )}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            style={{
              padding: '4px 12px',
              backgroundColor: 'transparent',
              color: 'var(--vscode-button-foreground)',
              border: '1px solid var(--vscode-button-border)',
              borderRadius: '2px',
              cursor: 'pointer',
              fontSize: '12px',
            }}
          >
            Cancel
          </button>
        )}
        <button
          type="button"
          onClick={() => onContinue(preloadedContent)}
          style={{
            padding: '4px 12px',
            backgroundColor: 'var(--vscode-button-background)',
            color: 'var(--vscode-button-foreground)',
            border: 'none',
            borderRadius: '2px',
            cursor: 'pointer',
            fontSize: '12px',
          }}
        >
          Continue to Save to Confluence
        </button>
      </div>
    </div>
  );
};
