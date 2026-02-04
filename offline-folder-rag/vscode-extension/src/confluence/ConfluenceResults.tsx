import * as React from 'react';
import { IntelligentDecisions } from './intelligent-decisions';
import type {
  AnalyzeResponse,
  IntelligenceErrorResponse,
  CreateRequest,
} from './types';

export interface ConfluenceResultsProps {
  analyzeResponse?: AnalyzeResponse | null;
  errorResponse?: IntelligenceErrorResponse | null;
  fileCount?: number;
  createSuccess?: {
    id?: string;
    title?: string;
    space?: string;
    url?: string;
  } | null;
  analyzeResponseForSuccess?: AnalyzeResponse | null;
  onCreate?: (request: CreateRequest) => void;
  onCreateFallback?: () => void;
  baseUrl?: string;
  space?: string;
  auth?: [string, string];
  files?: string[] | Array<{ content: string }>;
}

export const ConfluenceResults: React.FC<ConfluenceResultsProps> = (props) => {
  const {
    analyzeResponse,
    errorResponse,
    fileCount = 0,
    createSuccess,
    analyzeResponseForSuccess,
    onCreate,
    onCreateFallback,
    baseUrl,
    space,
    auth,
    files,
  } = props;

  const style = {
    fontFamily: 'var(--vscode-font-family)',
    fontSize: '13px',
    padding: '12px',
  } as const;

  if (createSuccess) {
    const analysis = analyzeResponseForSuccess?.intelligence_analysis;
    const recommendation = analyzeResponseForSuccess?.intelligent_recommendation;
    const confidencePct = analysis
      ? Math.round(analysis.intelligence_confidence * 100)
      : null;

    return (
      <div style={style}>
        <div style={{ fontWeight: 600, marginBottom: '8px' }}>Page created</div>
        <div style={{ marginBottom: '4px' }}>
          <strong>Title:</strong> {createSuccess.title ?? '—'}
        </div>
        {createSuccess.url && (
          <div style={{ marginBottom: '4px', fontSize: '12px' }}>
            <a href={createSuccess.url} target="_blank" rel="noopener noreferrer">
              Open in Confluence
            </a>
          </div>
        )}
        {confidencePct !== null && (
          <div style={{ marginTop: '8px' }}>
            <strong>Confidence:</strong> {confidencePct}%
          </div>
        )}
        {recommendation?.intelligence_reason && (
          <div style={{ marginTop: '8px' }}>
            <strong>What made this intelligent:</strong>
            <div style={{ marginTop: '4px', fontSize: '12px', opacity: 0.9 }}>
              {recommendation.intelligence_reason}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div style={style}>
      <IntelligentDecisions
        analyzeResponse={analyzeResponse}
        errorResponse={errorResponse}
        fileCount={fileCount}
        onCreate={onCreate}
        onCreateFallback={onCreateFallback}
        baseUrl={baseUrl}
        space={space}
        auth={auth}
        files={files}
      />
    </div>
  );
};
