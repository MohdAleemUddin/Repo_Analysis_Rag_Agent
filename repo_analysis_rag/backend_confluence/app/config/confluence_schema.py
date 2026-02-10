"""
Pydantic schemas for Confluence configuration validation (PRD §5.2 FR6, NFR3).
Validators: URL (HTTPS for Cloud), email, token; path traversal prevention; size limits.
"""

import re
from typing import Any

from pydantic import BaseModel, Field, field_validator

# Max lengths and limits (NFR3)
MAX_URL_LEN = 2048
MAX_EMAIL_LEN = 256
MAX_TOKEN_LEN = 1024
MAX_PATH_LEN = 2048
MAX_JSON_BODY_LEN = 2 * 1024 * 1024  # 2MB for import/validate
PATH_TRAVERSAL_PATTERN = re.compile(r"\.\.|/\.\.|\\\\|\0")


def _no_path_traversal(v: str) -> str:
    if not v or not isinstance(v, str):
        return v or ""
    if PATH_TRAVERSAL_PATTERN.search(v):
        raise ValueError("Path must not contain traversal sequences (e.g. ..)")
    if len(v) > MAX_PATH_LEN:
        raise ValueError(f"Path must be at most {MAX_PATH_LEN} characters")
    return v.strip()


# ----- Credentials (test-connection / validate) -----


class ConfluenceCredentials(BaseModel):
    """Credentials for test-connection and validation. Never log api_token."""

    url: str = Field(
        ..., min_length=1, max_length=MAX_URL_LEN, description="Confluence base URL"
    )
    email: str = Field(
        ..., min_length=1, max_length=MAX_EMAIL_LEN, description="User email"
    )
    api_token: str = Field(
        ..., min_length=1, max_length=MAX_TOKEN_LEN, description="API token"
    )

    @field_validator("url")
    @classmethod
    def url_https_for_cloud(cls, v: str) -> str:
        s = (v or "").strip().lower()
        if ".atlassian.net" in s and not s.startswith("https://"):
            raise ValueError("Confluence Cloud URLs must use HTTPS")
        if not s.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return (v or "").strip().rstrip("/")

    @field_validator("email")
    @classmethod
    def email_format(cls, v: str) -> str:
        s = (v or "").strip()
        if not s:
            raise ValueError("Email is required")
        if "@" not in s or "." not in s.split("@")[-1]:
            raise ValueError("Invalid email format")
        return s


# ----- Defaults -----


class SpaceMappingDefault(BaseModel):
    """Optional typed space mapping; in practice we accept dict[str, str] from JSON."""

    model_config = {"extra": "allow"}


# ----- Performance -----


class PerformanceTimeouts(BaseModel):
    analysis: int = Field(default=3000, ge=500, le=60000, description="ms")
    templateSelection: int = Field(default=2000, ge=500, le=30000, description="ms")
    pageCreation: int = Field(default=15000, ge=1000, le=120000, description="ms")
    connection: int = Field(default=5000, ge=1000, le=30000, description="ms")


class PerformanceCache(BaseModel):
    enabled: bool = True
    ttl: int = Field(default=300, ge=0, le=86400, description="seconds")
    maxSize: int = Field(default=100, ge=0, le=10000)


# ----- Logging -----


class LoggingConfig(BaseModel):
    level: str = Field(default="INFO", pattern="^(DEBUG|INFO|WARN|ERROR)$")
    includeSensitive: bool = False
    maxFileSize: str = Field(default="10MB", max_length=32)


# ----- Learning -----


class LearningConfig(BaseModel):
    enabled: bool = True
    retentionDays: int = Field(default=90, ge=1, le=3650)
    minConfidence: float = Field(default=0.7, ge=0.0, le=1.0)
    autoImprove: bool = True


# ----- Advanced -----


class AdvancedConfig(BaseModel):
    exportPath: str = Field(
        default="${workspaceFolder}/.confluence/examples", max_length=MAX_PATH_LEN
    )
    importPath: str = Field(default="", max_length=MAX_PATH_LEN)
    autoExport: bool = False

    @field_validator("exportPath", "importPath")
    @classmethod
    def path_no_traversal(cls, v: str) -> str:
        if not v:
            return v
        return _no_path_traversal(v)


# ----- Templates (PRD §5.2 FR6) -----


class TemplatesOverrides(BaseModel):
    disabledTemplates: list[str] = Field(default_factory=list, max_length=100)
    priorityOrder: list[str] = Field(default_factory=list, max_length=50)
    customTemplatesPath: str = Field(default="", max_length=MAX_PATH_LEN)

    @field_validator("customTemplatesPath")
    @classmethod
    def path_no_traversal(cls, v: str) -> str:
        if not v:
            return v
        return _no_path_traversal(v)


# ----- Intelligence (PRD §4.2.2) -----


class IntelligenceConfig(BaseModel):
    confidenceThreshold: float = Field(default=0.7, ge=0.0, le=1.0)
    autoTitle: bool = True
    autoSpace: bool = True
    explainDecisions: bool = True


# ----- Risks (PRD §13) -----


class RisksConfig(BaseModel):
    allowOverrides: bool = True
    showConfidence: bool = True
    fallbackTemplates: list[str] = Field(
        default_factory=lambda: ["mixed_project", "generic"], max_length=20
    )
    maxFileSize: str = Field(default="10MB", max_length=32)


# ----- Full config (for validate endpoint) -----


class ConfluenceConfigValidate(BaseModel):
    """Full or partial config for POST /confluence/config/validate."""

    credentials: ConfluenceCredentials | None = None
    defaults: dict[str, Any] | None = None
    performance: dict[str, Any] | None = None
    logging: dict[str, Any] | None = None
    learning: dict[str, Any] | None = None
    advanced: dict[str, Any] | None = None
    templates: dict[str, Any] | None = None
    intelligence: dict[str, Any] | None = None
    risks: dict[str, Any] | None = None

    model_config = {"extra": "ignore"}


# ----- Default value generators -----

RATE_LIMIT_CLOUD = 30
RATE_LIMIT_SERVER = 20


def get_rate_limit_for_edition(edition: str) -> int:
    return RATE_LIMIT_CLOUD if edition == "cloud" else RATE_LIMIT_SERVER


def get_intelligent_defaults_model(url: str | None = None) -> dict[str, Any]:
    """Return intelligent defaults (edition-based rate limit, learning on, etc.)."""
    edition = "cloud"
    if url:
        url_lower = url.strip().lower()
        if ".atlassian.net" in url_lower:
            edition = "cloud"
        else:
            edition = "server"
    return {
        "edition": edition,
        "performance": {
            "rateLimit": get_rate_limit_for_edition(edition),
            "burstLimit": 10,
            "retryAttempts": 3,
            "timeouts": {
                "analysis": 3000,
                "templateSelection": 2000,
                "pageCreation": 15000,
                "connection": 5000,
            },
            "cache": {"enabled": True, "ttl": 300, "maxSize": 100},
        },
        "learning": {
            "enabled": True,
            "retentionDays": 90,
            "minConfidence": 0.7,
            "autoImprove": True,
        },
        "intelligence": {
            "confidenceThreshold": 0.7,
            "autoTitle": True,
            "autoSpace": True,
            "explainDecisions": True,
        },
        "mode": {"intelligent": True},
    }
