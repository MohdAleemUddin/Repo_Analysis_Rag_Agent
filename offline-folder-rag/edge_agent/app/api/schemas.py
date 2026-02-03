# Pydantic models for PRD §9.0/§9.1/§9.2 Confluence API endpoints

from typing import Any, Literal

from pydantic import BaseModel, Field


# ----- Request schemas (PRD §9.1) -----


class AnalyzeRequest(BaseModel):
    """POST /confluence/intelligent-analyze request."""

    files: list[str] = Field(..., min_length=1, description="At least one file path")
    context: str | None = Field(default=None, description="Current project intelligence")


class CreateRequest(BaseModel):
    """POST /confluence/intelligent-create request."""

    files: list[str] = Field(..., min_length=1, description="File paths")
    intelligent_mode: bool = Field(..., description="Full AI intelligence")
    auto_title: bool = Field(..., description="AI decides title intelligently")
    space: str = Field(..., min_length=1, description="Confluence space key")
    intelligence_context: dict[str, Any] = Field(default_factory=dict, description="Context object")


class FeedbackRequest(BaseModel):
    """POST /confluence/intelligence-feedback request."""

    creation_id: str = Field(..., min_length=1, description="UUID of the creation")
    intelligence_score: int = Field(..., ge=1, le=5, description="Score 1-5")
    feedback: str = Field(..., description="User feedback text")


# ----- Analyze response (PRD §9.1) -----


class ConfidenceBreakdown(BaseModel):
    content_match: float = Field(..., ge=0, le=1)
    structure_match: float = Field(..., ge=0, le=1)
    context_match: float = Field(..., ge=0, le=1)


class IntelligenceAnalysis(BaseModel):
    content_types: list[str] = Field(default_factory=list)
    detected_patterns: list[str] = Field(default_factory=list)
    intelligent_title: str = Field(default="")
    intelligence_confidence: float = Field(..., ge=0, le=1)
    ai_reasoning: str = Field(default="")


class IntelligentRecommendation(BaseModel):
    template_id: str = Field(default="")
    template_name: str = Field(default="")
    intelligence_reason: str = Field(default="")
    confidence_breakdown: ConfidenceBreakdown = Field(...)


class AnalyzeResponse(BaseModel):
    intelligence_analysis: IntelligenceAnalysis = Field(...)
    intelligent_recommendation: IntelligentRecommendation = Field(...)


# ----- Create response (PRD §9.1) -----


class IntelligenceConfidenceSummary(BaseModel):
    content_detection: float = Field(..., ge=0, le=1)
    template_intelligence: float = Field(..., ge=0, le=1)
    formatting_intelligence: float = Field(..., ge=0, le=1)
    overall_intelligence: float = Field(..., ge=0, le=1)


class IntelligenceSummary(BaseModel):
    ai_decisions_made: list[str] = Field(default_factory=list)
    intelligence_confidence: IntelligenceConfidenceSummary = Field(...)
    ai_learning_applied: bool = Field(default=False)
    improvement_suggestions: list[str] = Field(default_factory=list)


class IntelligentPage(BaseModel):
    url: str = Field(default="")
    id: str = Field(default="")
    title: str = Field(default="")
    space: str = Field(default="")
    intelligence_tag: str = Field(default="AI-Formatted")


class CreateResponse(BaseModel):
    success: bool = Field(...)
    intelligence_summary: IntelligenceSummary = Field(...)
    intelligent_page: IntelligentPage = Field(...)


# ----- Status response (AC-7 explicit) -----


class IntelligenceMetrics(BaseModel):
    template_selection_accuracy: float = Field(..., ge=0, le=1)
    user_acceptance_rate: float = Field(..., ge=0, le=1)
    learning_rate: float = Field(..., ge=0, le=1)


class StatusResponse(BaseModel):
    intelligence_metrics: IntelligenceMetrics = Field(...)
    learning_progress: dict[str, Any] = Field(default_factory=dict)
    improvement_rates: dict[str, Any] = Field(default_factory=dict)


# ----- Feedback response (AC-9 explicit) -----


class FeedbackResponse(BaseModel):
    message: str = Field(...)
    metrics_updated: bool = Field(...)
    learning_applied: bool = Field(...)
    updated_status: StatusResponse = Field(...)


# ----- Error response (PRD §9.2) -----


class IntelligenceErrorResponse(BaseModel):
    error: Literal["intelligence_error"] = Field(default="intelligence_error")
    message: str = Field(...)
    intelligence_suggestion: str = Field(...)
    fallback_available: bool = Field(...)
    intelligence_confidence: float = Field(..., ge=0, le=1)
