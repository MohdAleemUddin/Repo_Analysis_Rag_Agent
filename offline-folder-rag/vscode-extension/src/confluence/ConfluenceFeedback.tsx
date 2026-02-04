import * as React from 'react';

export interface ConfluenceFeedbackProps {
  /** Show Learning Indicator when system has just learned from a successful creation */
  learningIndicator?: boolean;
  /** After import: "Intelligence Examples Imported: X new examples learned" */
  importedCount?: number | null;
  /** "Collective Intelligence: X examples from team" */
  collectiveIntelligenceCount?: number | null;
  /** Callback to submit feedback (score 1–5, optional comment) for TC-POS-010, TC-UC-004 */
  onFeedbackSubmit?: (creationId: string, intelligenceScore: number, feedback?: string) => void;
  /** Optional creation id to attach feedback to */
  creationId?: string | null;
}

export const ConfluenceFeedback: React.FC<ConfluenceFeedbackProps> = ({
  learningIndicator = false,
  importedCount = null,
  collectiveIntelligenceCount = null,
  onFeedbackSubmit,
  creationId = null,
}) => {
  const [score, setScore] = React.useState<number | null>(null);
  const [comment, setComment] = React.useState('');
  const [submitted, setSubmitted] = React.useState(false);

  const handleSubmit = () => {
    if (score !== null && creationId && onFeedbackSubmit) {
      onFeedbackSubmit(creationId, score, comment || undefined);
      setSubmitted(true);
    }
  };

  return (
    <div className="confluence-feedback">
      {learningIndicator && (
        <div className="confluence-learning-indicator" role="status">
          🎓 Intelligence Learning: System learned from this successful creation
        </div>
      )}
      {importedCount !== null && importedCount !== undefined && (
        <div className="confluence-imported-count" role="status">
          Intelligence Examples Imported: {importedCount} new examples learned
        </div>
      )}
      {collectiveIntelligenceCount !== null && collectiveIntelligenceCount !== undefined && (
        <div className="confluence-collective-intelligence" role="status">
          Collective Intelligence: {collectiveIntelligenceCount} examples from team
        </div>
      )}
      {onFeedbackSubmit && creationId && (
        <div className="confluence-feedback-form">
          <label>Rate this creation (1–5)</label>
          <div className="confluence-feedback-stars">
            {[1, 2, 3, 4, 5].map((n) => (
              <button
                key={n}
                type="button"
                aria-label={`${n} star${n > 1 ? 's' : ''}`}
                onClick={() => setScore(n)}
                className={score === n ? 'selected' : ''}
              >
                {n}
              </button>
            ))}
          </div>
          <input
            type="text"
            placeholder="Optional feedback"
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            aria-label="Optional feedback"
          />
          <button type="button" onClick={handleSubmit} disabled={submitted || score === null}>
            {submitted ? 'Submitted' : 'Submit feedback'}
          </button>
        </div>
      )}
    </div>
  );
};
