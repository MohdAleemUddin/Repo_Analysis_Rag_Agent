import * as React from 'react';
import {
  IntelligenceDashboard,
  IntelligenceMetrics,
  LearningProgress,
  IntelligenceSummary,
} from './intelligence-dashboard';

export interface ConfluenceAnalyticsProps {
  metrics?: IntelligenceMetrics;
  learningProgress?: LearningProgress;
  intelligenceSummary?: IntelligenceSummary;
  successRate?: number;
}

export const ConfluenceAnalytics: React.FC<ConfluenceAnalyticsProps> = (props) => {
  return (
    <IntelligenceDashboard
      metrics={props.metrics}
      learningProgress={props.learningProgress}
      intelligenceSummary={props.intelligenceSummary}
      successRate={props.successRate}
    />
  );
};
