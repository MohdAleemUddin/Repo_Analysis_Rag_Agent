export type ConfluencePlaceholder = unknown;

/** PRD §9.1 analyze response */
export interface ConfidenceBreakdown {
  content_match: number;
  structure_match: number;
  context_match: number;
}

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

/** US-2: Context suggestions from chat */
export interface ContextSuggestions {
  mentioned_files: string[];
  related_files: string[];
  project_type_label: string;
  detected_language?: string;
  should_suggest_readme?: boolean;
}

export interface AnalyzeResponse {
  intelligence_analysis?: IntelligenceAnalysis;
  intelligent_recommendation?: IntelligentRecommendation;
  performance?: Record<string, unknown>;
  optimization_suggestions?: unknown[];
  context_suggestions?: ContextSuggestions;
}

/** PRD §9.1 create request; template from analysis so create uses same format */
export interface IntelligenceContext {
  title_override?: string;
  suggested_title?: string;
  template_id?: string;
  template_name?: string;
}

export interface CreateRequest {
  files: string[] | Array<{ content: string }>;
  intelligent_mode: boolean;
  auto_title: boolean;
  space: string;
  intelligence_context?: IntelligenceContext;
  base_url?: string;
  auth?: [string, string];
  suggested_title?: string;
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

/** PRD §9.2 error contract */
export interface IntelligenceErrorResponse {
  error: 'intelligence_error';
  message: string;
  intelligence_suggestion: string;
  fallback_available: boolean;
  intelligence_confidence?: number;
}

export interface ErrorResponse {
  error: string;
  message: string;
  intelligence_suggestion: string;
  fallback_available: boolean;
  intelligence_confidence: number;
}

export interface ProgressUpdate {
  step: string;
  completed: boolean;
  percent: number;
  estimated_seconds: number;
}
