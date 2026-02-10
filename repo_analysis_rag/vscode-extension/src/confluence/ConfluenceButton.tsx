import * as React from 'react';

interface ConfluenceButtonProps {
  onClick: () => void;
  disabled?: boolean;
}

export const ConfluenceButton: React.FC<ConfluenceButtonProps> = ({ onClick, disabled }) => {
  return (
    <button
      className="confluence-save-button"
      onClick={onClick}
      disabled={disabled}
      title="Save to Confluence"
      style={{
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
      }}
    >
      <span style={{ marginRight: '4px' }}>💾</span>
      Save to Confluence
    </button>
  );
};
