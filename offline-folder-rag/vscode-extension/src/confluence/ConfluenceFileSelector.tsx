import * as React from 'react';

export interface ContextSuggestions {
  mentioned_files: string[];
  related_files: string[];
  project_type_label: string;
  should_suggest_readme?: boolean;
}

interface ConfluenceFileSelectorProps {
  onCancel: () => void;
  onNext: (selectedFiles: string[]) => void;
  onBrowseFiles?: () => Promise<string[]>;
  /** Pre-selected files and related files from chat context (US-2). */
  contextSuggestions?: ContextSuggestions;
  /** Pre-loaded content from right-click selection. */
  preloadedContent?: string;
  /** Preferred Confluence space for this project (e.g. "DEV"). */
  preferredSpace?: string;
  /** Available spaces for dropdown. */
  spaces?: Array<{ key: string; name?: string }>;
  /** Called when user changes space (one-click). */
  onSpaceChange?: (spaceKey: string) => void;
}

export const ConfluenceFileSelector: React.FC<ConfluenceFileSelectorProps> = ({
  onCancel,
  onNext,
  onBrowseFiles,
  contextSuggestions,
  preloadedContent,
  preferredSpace,
  spaces = [],
  onSpaceChange,
}) => {
  const mentioned = contextSuggestions?.mentioned_files ?? [];
  const related = contextSuggestions?.related_files ?? [];
  const projectTypeLabel = contextSuggestions?.project_type_label ?? '';
  const shouldSuggestReadme = contextSuggestions?.should_suggest_readme ?? false;

  const [selectedFiles, setSelectedFiles] = React.useState<string[]>(() => {
    const initial = [...mentioned];
    if (initial.length === 0) return ['api.py', 'config.yaml', 'README.md', 'utils.py'];
    return initial;
  });
  const [availableFiles, setAvailableFiles] = React.useState<string[]>(() => {
    const all = [...new Set([...mentioned, ...related, 'api.py', 'config.yaml', 'README.md', 'utils.py'])];
    return all.length > 0 ? all : ['api.py', 'config.yaml', 'README.md', 'utils.py'];
  });
  const [selectedSpace, setSelectedSpace] = React.useState<string>(preferredSpace ?? 'DOCS');

  React.useEffect(() => {
    if (preferredSpace) setSelectedSpace(preferredSpace);
  }, [preferredSpace]);

  React.useEffect(() => {
    if (mentioned.length > 0 || related.length > 0) {
      setAvailableFiles(prev => [...new Set([...prev, ...mentioned, ...related])]);
      if (mentioned.length > 0) {
        setSelectedFiles(prev => [...new Set([...mentioned, ...prev])]);
      }
    }
  }, [mentioned.length, related.length]);

  const handleAddRelatedFiles = React.useCallback(() => {
    if (related.length === 0) return;
    setAvailableFiles(prev => [...new Set([...prev, ...related])]);
    setSelectedFiles(prev => [...new Set([...prev, ...related])]);
  }, [related]);

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

  const isCodeOnly = selectedFiles.length > 0 && selectedFiles.every(
    f => /\.(py|ts|tsx|js|jsx|java|go|rs|c|cpp|rb)$/i.test(f)
  );
  const spaceOptions = spaces.length > 0 ? spaces : [{ key: selectedSpace, name: selectedSpace }];

  return (
    <div className="confluence-card" style={{
      border: '1px solid var(--vscode-widget-border)',
      borderRadius: '4px',
      padding: '12px',
      backgroundColor: 'var(--vscode-editor-background)',
      maxWidth: '400px'
    }}>
      <h3 style={{ margin: '0 0 12px 0', fontSize: '14px' }}>Select files for intelligent formatting</h3>

      {preferredSpace && (
        <div style={{ marginBottom: '8px', fontSize: '11px', color: 'var(--vscode-descriptionForeground)' }}>
          Previously used: <strong>{preferredSpace}</strong>
        </div>
      )}
      {(spaces.length > 0 || onSpaceChange) && (
        <div style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <label style={{ fontSize: '12px' }}>Space:</label>
          <select
            value={selectedSpace}
            onChange={(e) => {
              const k = e.target.value;
              setSelectedSpace(k);
              onSpaceChange?.(k);
            }}
            style={{
              fontSize: '12px',
              padding: '2px 6px',
              backgroundColor: 'var(--vscode-input-background)',
              color: 'var(--vscode-input-foreground)',
              border: '1px solid var(--vscode-input-border)',
              borderRadius: '2px',
            }}
          >
            {spaceOptions.map(s => (
              <option key={s.key} value={s.key}>{s.name ?? s.key}</option>
            ))}
          </select>
        </div>
      )}

      {projectTypeLabel && (
        <div style={{
          marginBottom: '8px',
          fontSize: '11px',
          padding: '4px 8px',
          backgroundColor: 'var(--vscode-badge-background)',
          color: 'var(--vscode-badge-foreground)',
          borderRadius: '2px',
          display: 'inline-block',
        }}>
          Intelligently detected: {projectTypeLabel}
        </div>
      )}
      {preloadedContent && (
        <div style={{ marginBottom: '8px', fontSize: '11px', color: 'var(--vscode-descriptionForeground)' }}>
          Selection pre-loaded ({preloadedContent.length} chars)
        </div>
      )}

      <div style={{ marginBottom: '8px', display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
        <button
          type="button"
          onClick={handleBrowseFiles}
          style={{
            padding: '4px 8px',
            backgroundColor: 'var(--vscode-button-background)',
            color: 'var(--vscode-button-foreground)',
            border: 'none',
            borderRadius: '2px',
            cursor: 'pointer',
            fontSize: '12px',
          }}
        >
          📁 Browse Files...
        </button>
        {related.length > 0 && (
          <button
            type="button"
            onClick={handleAddRelatedFiles}
            style={{
              padding: '4px 8px',
              backgroundColor: 'var(--vscode-button-secondaryBackground)',
              color: 'var(--vscode-button-secondaryForeground)',
              border: '1px solid var(--vscode-button-border)',
              borderRadius: '2px',
              cursor: 'pointer',
              fontSize: '12px',
            }}
          >
            Add related files
          </button>
        )}
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
            <label htmlFor={file} style={{ fontSize: '12px' }}>
              {file}
              {mentioned.includes(file) && (
                <span style={{ marginLeft: '6px', fontSize: '10px', color: 'var(--vscode-descriptionForeground)' }}>
                  Based on your conversation
                </span>
              )}
            </label>
          </div>
        ))}
      </div>

      {(isCodeOnly || shouldSuggestReadme) && (
        <div style={{ fontSize: '11px', marginBottom: '8px', color: 'var(--vscode-descriptionForeground)' }}>
          Consider adding README or docs for context.
        </div>
      )}

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
          type="button"
          onClick={onCancel}
          style={{
            padding: '4px 12px',
            backgroundColor: 'transparent',
            color: 'var(--vscode-button-foreground)',
            border: '1px solid var(--vscode-button-border)',
            borderRadius: '2px',
            cursor: 'pointer',
          }}
        >
          Cancel
        </button>
        <button
          type="button"
          onClick={() => onNext(selectedFiles)}
          disabled={selectedFiles.length === 0}
          style={{
            padding: '4px 12px',
            backgroundColor: selectedFiles.length === 0 ? 'var(--vscode-button-secondaryBackground)' : 'var(--vscode-button-background)',
            color: 'var(--vscode-button-foreground)',
            border: 'none',
            borderRadius: '2px',
            cursor: selectedFiles.length === 0 ? 'not-allowed' : 'pointer',
            opacity: selectedFiles.length === 0 ? 0.5 : 1,
          }}
        >
          Next: Let AI Decide
        </button>
      </div>
    </div>
  );
};
