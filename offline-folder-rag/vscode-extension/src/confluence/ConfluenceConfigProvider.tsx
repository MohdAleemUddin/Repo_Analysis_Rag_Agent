import * as React from 'react';

export interface TestConnectionResult {
  ok: boolean;
  spaces?: Array<{ key?: string; name?: string }>;
  latency_ms?: number;
  error?: string;
}

export interface ConfluenceConfigProviderProps {
  /** Edge agent base URL for config API calls */
  baseUrl: string;
  /** Last test-connection result (from extension after backend call) */
  testResult: TestConnectionResult | null;
  /** True while test-connection is in progress */
  testLoading: boolean;
  /** Called when user clicks Test connection; extension should read credentials and call backend */
  onTestConnection: () => void;
  /** Validation errors to display (URL, email, token) */
  validationErrors?: string[];
}

export const ConfluenceConfigProvider: React.FC<ConfluenceConfigProviderProps> = ({
  baseUrl,
  testResult,
  testLoading,
  onTestConnection,
  validationErrors = [],
}) => {
  return (
    <div
      className="confluence-config-provider"
      style={{
        fontFamily: 'var(--vscode-font-family)',
        fontSize: '13px',
        padding: '16px',
        maxWidth: '480px',
      }}
    >
      <h3 style={{ marginTop: 0, marginBottom: '12px' }}>Confluence configuration</h3>
      <p style={{ marginBottom: '12px', color: 'var(--vscode-descriptionForeground)' }}>
        Set Confluence URL and email in Settings, and store your API token securely. Then test the connection.
      </p>
      {validationErrors.length > 0 && (
        <div
          style={{
            marginBottom: '12px',
            padding: '8px',
            background: 'var(--vscode-inputValidation-errorBackground)',
            border: '1px solid var(--vscode-inputValidation-errorBorder)',
            borderRadius: '4px',
          }}
        >
          <ul style={{ margin: 0, paddingLeft: '20px' }}>
            {validationErrors.map((err, i) => (
              <li key={i}>{err}</li>
            ))}
          </ul>
        </div>
      )}
      <div style={{ marginBottom: '12px' }}>
        <button
          type="button"
          onClick={onTestConnection}
          disabled={testLoading}
          style={{
            padding: '6px 12px',
            background: 'var(--vscode-button-background)',
            color: 'var(--vscode-button-foreground)',
            border: 'none',
            borderRadius: '2px',
            cursor: testLoading ? 'not-allowed' : 'pointer',
            opacity: testLoading ? 0.7 : 1,
          }}
        >
          {testLoading ? 'Testing…' : 'Test connection'}
        </button>
      </div>
      {testResult && !testLoading && (
        <div
          style={{
            padding: '8px',
            borderRadius: '4px',
            background: testResult.ok
              ? 'var(--vscode-editor-inactiveSelectionBackground)'
              : 'var(--vscode-inputValidation-errorBackground)',
            border: `1px solid ${testResult.ok ? 'var(--vscode-widget-border)' : 'var(--vscode-inputValidation-errorBorder)'}`,
          }}
        >
          {testResult.ok ? (
            <>
              <p style={{ margin: '0 0 8px 0' }}>Connection successful.</p>
              {testResult.latency_ms != null && (
                <p style={{ margin: 0, fontSize: '12px', opacity: 0.9 }}>
                  Latency: {testResult.latency_ms} ms
                </p>
              )}
              {testResult.spaces && testResult.spaces.length > 0 && (
                <p style={{ margin: '8px 0 0 0', fontSize: '12px' }}>Spaces: {testResult.spaces.map((s) => s.key || s.name).filter(Boolean).join(', ')}</p>
              )}
            </>
          ) : (
            <p style={{ margin: 0 }}>{testResult.error || 'Connection failed'}</p>
          )}
        </div>
      )}
      <p style={{ marginTop: '12px', fontSize: '11px', color: 'var(--vscode-descriptionForeground)' }}>
        Edge agent: {baseUrl || '—'}
      </p>
    </div>
  );
};
