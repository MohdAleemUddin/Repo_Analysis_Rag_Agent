import * as React from 'react';
import type {
  AnalyzeResponse,
  IntelligenceAnalysis,
  IntelligentRecommendation,
  IntelligenceErrorResponse,
  CreateRequest,
} from './types';

const TITLE_MAX_LENGTH = 255;
const LOW_CONFIDENCE_THRESHOLD = 0.7;

function parseMatchesCount(reason: string): number | null {
  if (!reason) return null;
  const m = reason.match(/Matches\s+(\d+)\s+similar/);
  return m ? parseInt(m[1], 10) : null;
}

export interface IntelligentDecisionsProps {
  analyzeResponse?: AnalyzeResponse | null;
  errorResponse?: IntelligenceErrorResponse | null;
  fileCount?: number;
  onCreate?: (request: CreateRequest) => void;
  onCreateFallback?: () => void;
  baseUrl?: string;
  space?: string;
  auth?: [string, string];
  files?: string[] | Array<{ content: string }>;
}

export const IntelligentDecisions: React.FC<IntelligentDecisionsProps> = (props) => {
  const {
    analyzeResponse,
    errorResponse,
    fileCount = 0,
    onCreate,
    onCreateFallback,
    baseUrl = '',
    space = 'DOC',
    auth,
    files = [],
  } = props;

  const [titleEditMode, setTitleEditMode] = React.useState(false);
  const [editedTitle, setEditedTitle] = React.useState('');
  const [explainExpanded, setExplainExpanded] = React.useState(false);

  const analysis: IntelligenceAnalysis | undefined = analyzeResponse?.intelligence_analysis;
  const recommendation: IntelligentRecommendation | undefined =
    analyzeResponse?.intelligent_recommendation;

  const suggestedTitle = analysis?.intelligent_title ?? '';
  const displayTitle = titleEditMode ? editedTitle : suggestedTitle;
  const confidence = analysis?.intelligence_confidence ?? 0;
  const confidencePct = Math.round(confidence * 100);
  const isLowConfidence = confidence < LOW_CONFIDENCE_THRESHOLD;
  const isNoMatch =
    errorResponse?.error === 'intelligence_error' && errorResponse?.fallback_available === true;

  React.useEffect(() => {
    if (!titleEditMode) setEditedTitle(suggestedTitle);
  }, [suggestedTitle, titleEditMode]);

  const handleEditTitle = () => {
    setEditedTitle(suggestedTitle);
    setTitleEditMode(true);
  };

  const handleTitleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const v = e.target.value;
    if (v.length <= TITLE_MAX_LENGTH) setEditedTitle(v);
  };

  const handleCreate = () => {
    if (!onCreate) return;
    const titleToUse = titleEditMode ? editedTitle : suggestedTitle;
    const wasEdited = titleEditMode && editedTitle !== suggestedTitle;
    const fileList = Array.isArray(files)
      ? files.map((f) => (typeof f === 'string' ? f : (f as { content: string }).content))
      : [];
    onCreate({
      files: fileList.length ? fileList : [],
      intelligent_mode: true,
      auto_title: !wasEdited,
      space,
      intelligence_context: wasEdited ? { title_override: titleToUse } : { suggested_title: titleToUse },
      base_url: baseUrl,
      auth,
    });
  };

  const matchesCount = recommendation ? parseMatchesCount(recommendation.intelligence_reason) : null;
  const style = {
    fontFamily: 'var(--vscode-font-family)',
    fontSize: '13px',
    padding: '12px',
  } as const;

  if (isNoMatch && errorResponse) {
    return (
      <div style={style}>
        <div style={{ fontWeight: 600, marginBottom: '8px' }}>No template match found</div>
        <p style={{ margin: '8px 0', opacity: 0.9 }}>{errorResponse.message}</p>
        <button
          type="button"
          onClick={onCreateFallback}
          style={{
            padding: '8px 12px',
            marginTop: '8px',
            cursor: 'pointer',
          }}
        >
          Use Intelligent Fallback Template
        </button>
      </div>
    );
  }

  if (!analysis || !recommendation) {
    return (
      <div style={style}>
        <div style={{ opacity: 0.8 }}>Run analysis to see intelligent decisions.</div>
      </div>
    );
  }

  const cb = recommendation.confidence_breakdown;
  const contentTypes = analysis.content_types ?? [];
  const detectedPatterns = analysis.detected_patterns ?? [];

  return (
    <div style={style}>
      <div style={{ fontWeight: 600, marginBottom: '8px' }}>Let AI Decide</div>

      {fileCount > 1 && (
        <p style={{ margin: '4px 0', fontSize: '12px', opacity: 0.9 }}>
          Intelligently combining {fileCount} files as comprehensive documentation
        </p>
      )}

      {contentTypes.length > 0 && (
        <div style={{ marginBottom: '8px', fontSize: '12px' }}>
          <span style={{ opacity: 0.8 }}>Detected: </span>
          {contentTypes.join(', ')}
          {detectedPatterns.length > 0 && ` · ${detectedPatterns.join(', ')}`}
        </div>
      )}

      <div style={{ marginBottom: '8px' }}>
        <strong>Intelligent Format Selected:</strong> &quot;{recommendation.template_name}&quot; template
      </div>
      {matchesCount !== null && (
        <div style={{ marginBottom: '8px', fontSize: '12px', opacity: 0.9 }}>
          (Matches {matchesCount} similar successful examples)
        </div>
      )}

      <div style={{ marginBottom: '8px' }}>
        <strong>Suggested Title:</strong>{' '}
        {!titleEditMode ? (
          <>
            [{displayTitle || '—'}]
            <button
              type="button"
              onClick={handleEditTitle}
              style={{ marginLeft: '8px', padding: '2px 8px', cursor: 'pointer' }}
            >
              Edit Title
            </button>
          </>
        ) : (
          <>
            <input
              type="text"
              value={editedTitle}
              onChange={handleTitleChange}
              maxLength={TITLE_MAX_LENGTH}
              style={{ width: '100%', maxWidth: '400px', padding: '4px' }}
              aria-label="Title"
            />
            <span style={{ marginLeft: '8px', fontSize: '11px', opacity: 0.8 }}>
              {editedTitle.length}/{TITLE_MAX_LENGTH}
            </span>
          </>
        )}
      </div>

      <div style={{ marginBottom: '8px' }}>
        <strong>Confidence:</strong> {confidencePct}%
      </div>
      {cb && (
        <div style={{ marginBottom: '8px', fontSize: '12px' }}>
          Content: {Math.round((cb.content_match ?? 0) * 100)}% · Structure:{' '}
          {Math.round((cb.structure_match ?? 0) * 100)}% · Context:{' '}
          {Math.round((cb.context_match ?? 0) * 100)}%
        </div>
      )}

      {isLowConfidence && (
        <div style={{ marginBottom: '8px', padding: '8px', background: 'var(--vscode-inputValidation-warningBackground)', borderLeft: '4px solid var(--vscode-inputValidation-warningBorder)' }}>
          <strong>Intelligence Confidence Low</strong>
          <br />
          <button
            type="button"
            onClick={onCreateFallback}
            style={{ marginTop: '4px', padding: '4px 8px', cursor: 'pointer' }}
          >
            Use Intelligent Fallback Template
          </button>
        </div>
      )}

      <div style={{ marginBottom: '8px' }}>
        <button
          type="button"
          onClick={() => setExplainExpanded(!explainExpanded)}
          style={{ padding: '4px 8px', cursor: 'pointer', marginBottom: '4px' }}
        >
          {explainExpanded ? 'Hide' : 'Explain AI Choice'}
        </button>
        {explainExpanded && (
          <div style={{ padding: '8px', background: 'var(--vscode-editor-inactiveSelectionBackground)', borderRadius: '4px', fontSize: '12px' }}>
            <div style={{ marginBottom: '4px' }}>{recommendation.intelligence_reason}</div>
            {analysis.ai_reasoning && (
              <div style={{ opacity: 0.9 }}>{analysis.ai_reasoning}</div>
            )}
          </div>
        )}
      </div>

      <div style={{ marginTop: '12px' }}>
        <strong>What made this intelligent:</strong>
        <div style={{ marginTop: '4px', fontSize: '12px', opacity: 0.9 }}>
          {recommendation.intelligence_reason}
        </div>
      </div>

      <button
        type="button"
        onClick={handleCreate}
        disabled={!onCreate}
        style={{ marginTop: '12px', padding: '8px 16px', cursor: onCreate ? 'pointer' : 'default' }}
      >
        Create Perfect Page
      </button>
    </div>
  );
};
