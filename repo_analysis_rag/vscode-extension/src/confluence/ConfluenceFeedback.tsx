import * as React from 'react';

export interface ConfluenceFeedbackProps {
    /** Number of examples imported; when set, shows success message */
    importedCount?: number | null;
    /** Callback when user clicks Export Examples */
    onExport?: () => void;
    /** Callback when user clicks Import Examples */
    onImport?: () => void;
}

export const ConfluenceFeedback: React.FC<ConfluenceFeedbackProps> = ({
    importedCount = null,
    onExport,
    onImport,
}) => {
    const showImportSuccess = typeof importedCount === 'number' && importedCount >= 0;
    return (
        <div style={{ marginTop: 12, padding: 12, border: '1px solid var(--vscode-widget-border)', borderRadius: 8 }}>
            <div style={{ fontWeight: 600, fontSize: 13, marginBottom: 8 }}>Export/Import Examples</div>
            <div style={{ display: 'flex', gap: 8 }}>
                {onExport && (
                    <button
                        type="button"
                        onClick={onExport}
                        style={{
                            padding: '6px 12px',
                            fontSize: 12,
                            cursor: 'pointer',
                            border: '1px solid var(--vscode-button-border)',
                            borderRadius: 4,
                            background: 'var(--vscode-button-secondaryBackground)',
                            color: 'var(--vscode-button-secondaryForeground)',
                        }}
                    >
                        Export Examples
                    </button>
                )}
                {onImport && (
                    <button
                        type="button"
                        onClick={onImport}
                        style={{
                            padding: '6px 12px',
                            fontSize: 12,
                            cursor: 'pointer',
                            border: '1px solid var(--vscode-button-border)',
                            borderRadius: 4,
                            background: 'var(--vscode-button-secondaryBackground)',
                            color: 'var(--vscode-button-secondaryForeground)',
                        }}
                    >
                        Import Examples
                    </button>
                )}
            </div>
            {showImportSuccess && (
                <div style={{ marginTop: 8, fontSize: 12, color: 'var(--vscode-testing-iconPassed)' }}>
                    Intelligence Examples Imported: {importedCount} new examples learned
                </div>
            )}
        </div>
    );
};
