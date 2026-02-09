export interface IntelligenceAnalysis {
  content_types?: string[];
  detected_patterns?: string[];
  intelligent_title?: string;
  intelligence_confidence?: number;
  ai_reasoning?: string;
}

export interface IntelligentRecommendation {
  template_id?: string;
  template_name?: string;
  intelligence_reason?: string;
  confidence_breakdown?: {
    content_match?: number;
    structure_match?: number;
    context_match?: number;
  };
}

export interface AnalyzeResponse {
  intelligence_analysis?: IntelligenceAnalysis;
  intelligent_recommendation?: IntelligentRecommendation;
}

/** PRD §9.2 error contract (any error_code from backend) */
export interface IntelligenceErrorResponse {
  error: string;
  message: string;
  intelligence_suggestion: string;
  fallback_available?: boolean;
  intelligence_confidence?: number;
  actions?: string[];
  category?: string;
  suggested_files?: string[];
}

export interface IntelligenceSummary {
  ai_decisions_made: string[];
  intelligence_confidence: {
    content_detection: number;
    template_intelligence: number;
    formatting_intelligence: number;
    overall_intelligence: number;
  };
  ai_learning_applied: boolean;
  improvement_suggestions: string[];
}

export interface IntelligentPage {
  url: string;
  id: string;
  title: string;
  space: string;
  intelligence_tag: string;
}

export interface CreateResponse {
  success: boolean;
  intelligence_summary: IntelligenceSummary;
  intelligent_page: IntelligentPage;
}

export interface ErrorResponse {
  error: string;
  message: string;
  intelligence_suggestion: string;
  fallback_available?: boolean;
  intelligence_confidence?: number;
  actions?: string[];
  category?: string;
  suggested_files?: string[];
}

export interface ProgressUpdate {
  step: string;
  completed: boolean;
  percent: number;
  estimated_seconds: number;
}

/** US-17: Intelligence status dashboard response from GET /confluence/intelligence-status */
export interface IntelligenceStatusResponse {
  intelligence_metrics?: {
    template_selection_accuracy?: number;
    template_selection_intelligence?: number; // backend alias
    status_summary?: string;
    intelligence_confidence_pct?: number;
    learning_rate_pct?: number;
    team_examples_count?: number;
  };
  learning_progress?: {
    examples_learned?: number;
    template_selection_accuracy?: number;
    learning_rate_pct?: number;
    team_examples_count?: number;
  };
  improvement_rates?: { learning_rate_pct?: number };
  metrics?: { template_selection_accuracy?: number; success_rate?: number };
}

/** US-17: Flattened metrics for dashboard display */
export interface IntelligenceMetrics {
  templateSelectionAccuracy?: number;
  examplesLearned?: number;
  intelligenceConfidencePct?: number;
  learningRatePct?: number;
  statusSummary?: string;
  successRate?: number;
  collectiveIntelligenceCount?: number;
}
