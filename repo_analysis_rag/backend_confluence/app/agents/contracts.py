"""Internal contracts between coordinator and agents (stable, testable). Not API schemas."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PipelineState(str, Enum):
    """Deterministic pipeline stage for TC-ST-009 and diagnosability."""

    Idle = "Idle"
    Analyzing = "Analyzing"
    Matching = "Matching"
    Formatting = "Formatting"
    Integrating = "Integrating"
    Completed = "Completed"
    Failed = "Failed"


class ContentProfile(BaseModel):
    """Output of Content Analysis Agent (AC-A3)."""

    content_types: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    structure_signals: list[str] = Field(default_factory=list)
    detected_patterns: list[str] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    confidence_scores: dict[str, float] = Field(default_factory=dict)
    ai_reasoning: str = Field(default="")


class ConfidenceBreakdown(BaseModel):
    """Confidence breakdown for template decision."""

    content_match: float = Field(default=0.0, ge=0, le=1)
    structure_match: float = Field(default=0.0, ge=0, le=1)
    context_match: float = Field(default=0.0, ge=0, le=1)


class TemplateDecision(BaseModel):
    """Output of Pattern Matching Agent (AC-B2)."""

    template_id: str = Field(default="")
    template_name: str = Field(default="")
    intelligence_score: float = Field(default=0.0, ge=0, le=1)
    ai_reasoning: str = Field(default="")
    intelligence_reason: str = Field(default="")
    confidence_breakdown: ConfidenceBreakdown = Field(
        default_factory=ConfidenceBreakdown
    )


class ValidationResults(BaseModel):
    """Validation outcome for formatting."""

    warnings: list[str] = Field(default_factory=list)
    corrections_applied: list[str] = Field(default_factory=list)


class FormattedConfluencePayload(BaseModel):
    """Output of Formatting Agent (AC-C3)."""

    confluence_storage_format: str = Field(default="")
    attachments: list[dict[str, Any]] = Field(default_factory=list)
    validation_results: ValidationResults = Field(default_factory=ValidationResults)
    ai_reasoning: str = Field(default="")


class PageInfo(BaseModel):
    """Page metadata from Confluence."""

    id: str = Field(default="")
    url: str = Field(default="")
    title: str = Field(default="")
    space: str = Field(default="")


class VerificationResult(BaseModel):
    """Post-creation verification (AC-D3)."""

    passed: bool = Field(default=False)
    checks: list[str] = Field(default_factory=list)


class IntegrationResult(BaseModel):
    """Output of Integration Agent (AC-D3)."""

    page: PageInfo = Field(default_factory=PageInfo)
    intelligence_tag: str = Field(default="AI-Formatted")
    retries_used: int = Field(default=0, ge=0)
    rate_limit_state: str = Field(default="")  # e.g. "ok", "waited", "backoff"
    verification: VerificationResult = Field(default_factory=VerificationResult)


class CoordinatorError(BaseModel):
    """Fail-closed error for API translation (AC-CO-4). No secrets, no raw traces."""

    error_code: str = Field(default="pipeline_error")
    message: str = Field(default="")
    stage: str = Field(default="")
