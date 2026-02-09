from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional

class ErrorResponse(BaseModel):
    error_code: str
    message: str
    remediation: str

class IndexRequest(BaseModel):
    root_path: str

class IndexResponse(BaseModel):
    repo_id: str
    mode: str
    indexed_files: int
    skipped_files: int
    chunks_added: int
    duration_ms: int
    manifest_path: Optional[str] = None
    collections: Optional[List[str]] = None

    model_config = ConfigDict(extra="ignore")

class HealthResponse(BaseModel):
    indexing: bool
    indexed_files_so_far: int
    estimated_total_files: int
    last_index_completed_epoch_ms: int
    ollama_ok: bool
    ripgrep_ok: bool
    chroma_ok: bool

class Citation(BaseModel):
    file_path: str
    path: str
    line_number: int
    line_start: int
    start_line: int
    line_end: int
    end_line: int
    snippet: str

class ToolResponse(BaseModel):
    mode: str
    confidence: str
    answer: str
    citations: List[Citation]
    truncated: bool = False

class AskRequest(BaseModel):
    query: str
    root_path: str | None = None
    top_k: int | None = Field(
        default=None,
        gt=0,
        description="Optional override for the number of vector hits returned per category.",
    )
    max_context_chunks: int | None = Field(
        default=None,
        gt=0,
        description="Optional upper bound on the number of chunks returned in the response.",
    )

class OverviewRequest(BaseModel):
    root_path: str

class SearchRequest(BaseModel):
    query: str

class DoctorRequest(BaseModel):
    root_path: str

class IndexReportRequest(BaseModel):
    root_path: str
