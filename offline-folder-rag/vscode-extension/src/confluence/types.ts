export interface IntelligenceAnalysis {
  content_types: string[];
  detected_patterns: string[];
  intelligent_title: string;
  intelligence_confidence: number;
  ai_reasoning: string;
}

export interface IntelligentRecommendation {
  template_id: string;
  template_name: string;
  intelligence_reason: string;
  confidence_breakdown: {
    content_match: number;
    structure_match: number;
    context_match: number;
  };
}

export interface AnalyzeResponse {
  intelligence_analysis: IntelligenceAnalysis;
  intelligent_recommendation: IntelligentRecommendation;
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
  fallback_available: boolean;
  intelligence_confidence: number;
}

export interface ProgressUpdate {
  step: string;
  completed: boolean;
  percent: number;
  estimated_seconds: number;
}
