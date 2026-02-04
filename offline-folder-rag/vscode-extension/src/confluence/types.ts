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
  intelligent_title: string;
  intelligence_confidence: number;
  ai_reasoning?: string;
}

export interface IntelligentRecommendation {
  template_id?: string;
  template_name: string;
  intelligence_reason: string;
  confidence_breakdown: ConfidenceBreakdown;
}

export interface AnalyzeResponse {
  intelligence_analysis: IntelligenceAnalysis;
  intelligent_recommendation: IntelligentRecommendation;
  performance?: Record<string, unknown>;
  optimization_suggestions?: unknown[];
}

/** PRD §9.1 create request */
export interface IntelligenceContext {
  title_override?: string;
  suggested_title?: string;
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

/** PRD §9.2 error contract */
export interface IntelligenceErrorResponse {
  error: 'intelligence_error';
  message: string;
  intelligence_suggestion: string;
  fallback_available: boolean;
  intelligence_confidence?: number;
}
