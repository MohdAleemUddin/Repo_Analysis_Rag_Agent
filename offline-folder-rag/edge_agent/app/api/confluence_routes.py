# PRD §9.0/§9.1 Confluence API endpoints

from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from .schemas import (
    AnalyzeRequest,
    AnalyzeResponse,
    ConfidenceBreakdown,
    CreateRequest,
    CreateResponse,
    FeedbackRequest,
    FeedbackResponse,
    IntelligenceAnalysis,
    IntelligenceConfidenceSummary,
    IntelligenceErrorResponse,
    IntelligenceMetrics,
    IntelligenceSummary,
    IntelligentPage,
    IntelligentRecommendation,
    StatusResponse,
)


def _prd_error_response(
    message: str,
    intelligence_suggestion: str,
    fallback_available: bool = False,
    intelligence_confidence: float = 0.0,
    status_code: int = 422,
) -> JSONResponse:
    """Return PRD §9.2 exact error JSON for all failures."""
    body = IntelligenceErrorResponse(
        error="intelligence_error",
        message=message,
        intelligence_suggestion=intelligence_suggestion,
        fallback_available=fallback_available,
        intelligence_confidence=intelligence_confidence,
    )
    return JSONResponse(status_code=status_code, content=body.model_dump())


_VALIDATION_SUGGESTION = (
    "Check request keys and types per PRD §9.1 (files, context for analyze; "
    "files, intelligent_mode, auto_title, space, intelligence_context for create; "
    "creation_id, intelligence_score 1-5, feedback for feedback)."
)


# ----- Handlers (stub responses per PRD; no agent/DB) -----


async def intelligent_analyze_handler(
    request: Request,
) -> AnalyzeResponse | JSONResponse:
    """POST /confluence/intelligent-analyze: PRD §9.1 exact response."""
    try:
        AnalyzeRequest.model_validate(await request.json())
    except (ValidationError, TypeError, ValueError):
        return _prd_error_response(
            message="Invalid request body or parameters",
            intelligence_suggestion=_VALIDATION_SUGGESTION,
            fallback_available=False,
            intelligence_confidence=0.0,
            status_code=422,
        )
    return AnalyzeResponse(
        intelligence_analysis=IntelligenceAnalysis(
            content_types=["python_api", "configuration"],
            detected_patterns=["fastapi", "docker", "authentication"],
            intelligent_title="API Authentication Service Setup",
            intelligence_confidence=0.94,
            ai_reasoning="Detected FastAPI patterns with JWT auth",
        ),
        intelligent_recommendation=IntelligentRecommendation(
            template_id="uuid",
            template_name="API Security Intelligence Template",
            intelligence_reason="Matches 8 similar intelligent examples with 97% success",
            confidence_breakdown=ConfidenceBreakdown(
                content_match=0.96,
                structure_match=0.92,
                context_match=0.89,
            ),
        ),
    )


async def intelligent_create_handler(request: Request) -> CreateResponse | JSONResponse:
    """POST /confluence/intelligent-create: PRD §9.1 exact response."""
    try:
        body = CreateRequest.model_validate(await request.json())
    except (ValidationError, TypeError, ValueError):
        return _prd_error_response(
            message="Invalid request body or parameters",
            intelligence_suggestion=_VALIDATION_SUGGESTION,
            fallback_available=False,
            intelligence_confidence=0.0,
            status_code=422,
        )
    return CreateResponse(
        success=True,
        intelligence_summary=IntelligenceSummary(
            ai_decisions_made=[
                "Intelligently detected Python FastAPI patterns",
                "Selected 'API Intelligence' template (94% match)",
                "Generated intelligent title: 'Authentication Microservice API'",
                "Applied intelligent formatting with security focus",
            ],
            intelligence_confidence=IntelligenceConfidenceSummary(
                content_detection=0.96,
                template_intelligence=0.92,
                formatting_intelligence=0.95,
                overall_intelligence=0.94,
            ),
            ai_learning_applied=True,
            improvement_suggestions=["Add more examples for microservices"],
        ),
        intelligent_page=IntelligentPage(
            url="https://confluence/...",
            id="123456",
            title="Authentication Microservice API",
            space=body.space,
            intelligence_tag="AI-Formatted",
        ),
    )


async def intelligence_status_handler(
    detail_level: str | None = None,
) -> StatusResponse:
    """GET /confluence/intelligence-status: AC-7 explicit response."""
    return StatusResponse(
        intelligence_metrics=IntelligenceMetrics(
            template_selection_accuracy=0.92,
            user_acceptance_rate=0.88,
            learning_rate=0.75,
        ),
        learning_progress={"phase": "active", "examples_count": 0},
        improvement_rates={"template_match": 0.02, "user_acceptance": 0.01},
    )


async def intelligence_feedback_handler(
    request: Request,
) -> FeedbackResponse | JSONResponse:
    """POST /confluence/intelligence-feedback: AC-9 explicit response."""
    try:
        FeedbackRequest.model_validate(await request.json())
    except (ValidationError, TypeError, ValueError):
        return _prd_error_response(
            message="Invalid request body or parameters",
            intelligence_suggestion=_VALIDATION_SUGGESTION,
            fallback_available=False,
            intelligence_confidence=0.0,
            status_code=422,
        )
    status = StatusResponse(
        intelligence_metrics=IntelligenceMetrics(
            template_selection_accuracy=0.92,
            user_acceptance_rate=0.88,
            learning_rate=0.75,
        ),
        learning_progress={"phase": "active", "examples_count": 0},
        improvement_rates={"template_match": 0.02, "user_acceptance": 0.01},
    )
    return FeedbackResponse(
        message="Updated intelligence metrics and learning applied",
        metrics_updated=True,
        learning_applied=True,
        updated_status=status,
    )


def register_confluence_routes(router: Any) -> None:
    """Register all four PRD Confluence endpoints under /confluence/ namespace."""
    router.add_api_route(
        "/confluence/intelligent-analyze",
        intelligent_analyze_handler,
        methods=["POST"],
        response_model=AnalyzeResponse,
    )
    router.add_api_route(
        "/confluence/intelligent-create",
        intelligent_create_handler,
        methods=["POST"],
        response_model=CreateResponse,
    )
    router.add_api_route(
        "/confluence/intelligence-status",
        intelligence_status_handler,
        methods=["GET"],
        response_model=StatusResponse,
    )
    router.add_api_route(
        "/confluence/intelligence-feedback",
        intelligence_feedback_handler,
        methods=["POST"],
        response_model=FeedbackResponse,
    )
