import * as React from 'react';

interface ConfluenceFileSelectorProps {
  onCancel: () => void;
  onNext: (selectedFiles: string[]) => void;
  onBrowseFiles?: () => Promise<string[]>;
}

export const ConfluenceFileSelector: React.FC<ConfluenceFileSelectorProps> = ({ onCancel, onNext, onBrowseFiles }) => {
  const [selectedFiles, setSelectedFiles] = React.useState<string[]>([]);
  const [availableFiles, setAvailableFiles] = React.useState<string[]>(['api.py', 'config.yaml', 'README.md', 'utils.py']);

  const handleBrowseFiles = React.useCallback(async () => {
    if (onBrowseFiles) {
      const paths = await onBrowseFiles();
      if (paths?.length) {
        setAvailableFiles(prev => [...new Set([...prev, ...paths])]);
        setSelectedFiles(prev => [...new Set([...prev, ...paths])]);
      }
      return;
    }
    if (typeof (window as any).acquireVsCodeApi === 'function') {
      (window as any).acquireVsCodeApi().postMessage({ type: 'browseFiles' });
    }
  }, [onBrowseFiles]);

  React.useEffect(() => {
    if (typeof (window as any).acquireVsCodeApi !== 'function' || onBrowseFiles) return;
    const handler = (e: MessageEvent) => {
      if (e.data?.type === 'browseFilesResult' && Array.isArray(e.data.paths)) {
        setAvailableFiles(prev => [...new Set([...prev, ...e.data.paths])]);
        setSelectedFiles(prev => [...new Set([...prev, ...e.data.paths])]);
      }
    };
    window.addEventListener('message', handler);
    return () => window.removeEventListener('message', handler);
  }, [onBrowseFiles]);

  const toggleFile = (file: string) => {
    setSelectedFiles(prev => 
      prev.includes(file) ? prev.filter(f => f !== file) : [...prev, file]
    );
  };

  return (
    <div className="confluence-card" style={{
      border: '1px solid var(--vscode-widget-border)',
      borderRadius: '4px',
      padding: '12px',
      backgroundColor: 'var(--vscode-editor-background)',
      maxWidth: '400px'
    }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '14px' }}>Select files for intelligent formatting</h3>
      
      <div style={{ marginBottom: '12px' }}>
        <button 
          onClick={handleBrowseFiles}
          style={{
            padding: '4px 8px',
            backgroundColor: 'var(--vscode-button-background)',
            color: 'var(--vscode-button-foreground)',
            border: 'none',
            borderRadius: '2px',
            cursor: 'pointer',
            fontSize: '12px'
          }}
        >
          📁 Browse Files...
        </button>
      </div>

      <div style={{ maxHeight: '150px', overflowY: 'auto', marginBottom: '12px', border: '1px solid var(--vscode-input-border)', padding: '4px' }}>
        {availableFiles.map(file => (
          <div key={file} style={{ display: 'flex', alignItems: 'center', padding: '2px 0' }}>
            <input 
              type="checkbox" 
              id={file} 
              checked={selectedFiles.includes(file)} 
              onChange={() => toggleFile(file)}
              style={{ marginRight: '8px' }}
            />
            <label htmlFor={file} style={{ fontSize: '12px' }}>{file}</label>
          </div>
        ))}
      </div>

      <div style={{ fontSize: '12px', marginBottom: '12px', color: 'var(--vscode-descriptionForeground)' }}>
        Selected: {selectedFiles.length} files
        <ul style={{ margin: '4px 0 0 0', paddingLeft: '16px' }}>
          <li>Automatically analyzed</li>
          <li>Intelligently formatted</li>
          <li>Perfectly organized</li>
        </ul>
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
        <button 
          onClick={onCancel}
          style={{
            padding: '4px 12px',
            backgroundColor: 'transparent',
            color: 'var(--vscode-button-foreground)',
            border: '1px solid var(--vscode-button-border)',
            borderRadius: '2px',
            cursor: 'pointer'
          }}
        >
          Cancel
        </button>
        <button 
          onClick={() => onNext(selectedFiles)}
          disabled={selectedFiles.length === 0}
          style={{
            padding: '4px 12px',
            backgroundColor: selectedFiles.length === 0 ? 'var(--vscode-button-secondaryBackground)' : 'var(--vscode-button-background)',
            color: 'var(--vscode-button-foreground)',
            border: 'none',
            borderRadius: '2px',
            cursor: selectedFiles.length === 0 ? 'not-allowed' : 'pointer',
            opacity: selectedFiles.length === 0 ? 0.5 : 1
          }}
        >
          Next: Let AI Decide
        </button>
      </div>
    </div>
  );
};
