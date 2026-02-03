import * as React from 'react';

export interface PRDErrorResponse {
  error: string;
  message: string;
  intelligence_suggestion: string;
  fallback_available: boolean;
  intelligence_confidence: number;
  actions?: string[];
  category?: string;
}

export interface ErrorMessagesProps {
  error: PRDErrorResponse;
  helpLink?: string;
  onUpdateSettings?: () => void;
  onRetry?: () => void;
  onCancel?: () => void;
}

export const ErrorMessages: React.FC<ErrorMessagesProps> = ({
  error,
  helpLink,
  onUpdateSettings,
  onRetry,
  onCancel,
}) => {
  const actions = error.actions ?? ['Retry', 'Cancel'];
  return (
    <div className="confluence-error-messages">
      <div className="confluence-error-message">{error.message}</div>
      <div className="confluence-error-suggestion">{error.intelligence_suggestion}</div>
      {error.fallback_available && (
        <div className="confluence-error-fallback">Fallback available.</div>
      )}
      <div className="confluence-error-actions">
        {actions.includes('Update Settings') && (
          <button type="button" onClick={onUpdateSettings}>Update Settings</button>
        )}
        {actions.includes('Retry') && (
          <button type="button" onClick={onRetry}>Retry</button>
        )}
        {actions.includes('Cancel') && (
          <button type="button" onClick={onCancel}>Cancel</button>
        )}
      </div>
      {helpLink && (
        <a href={helpLink} target="_blank" rel="noopener noreferrer" className="confluence-error-help">Help</a>
      )}
    </div>
  );
};
