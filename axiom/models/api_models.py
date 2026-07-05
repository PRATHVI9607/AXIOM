"""Pydantic request/response schemas for the AXIOM REST + WebSocket API (PRD §8)."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Health ───────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    database: bool
    ebpf_available: bool
    embed_provider: str
    air_gapped: bool


# ── Auth ─────────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserOut(BaseModel):
    id: str
    username: str
    email: str
    role: str


class LocalLoginRequest(BaseModel):
    email: str
    password: str


class ApiKeyCreateRequest(BaseModel):
    name: str
    project_id: str | None = None


class ApiKeyCreateResponse(BaseModel):
    id: str
    name: str
    api_key: str  # plaintext, shown only once


# ── Projects ─────────────────────────────────────────────
class ProjectCreateRequest(BaseModel):
    name: str
    root_path: str
    languages: list[str] = Field(default_factory=list)


class ProjectOut(BaseModel):
    id: str
    name: str
    root_path: str
    languages: list[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Analysis ─────────────────────────────────────────────
class AnalyzeFileRequest(BaseModel):
    project_id: str
    file_path: str
    force_reembed: bool = False


class AnalyzeFunctionRequest(BaseModel):
    project_id: str
    function_id: str


class JobResponse(BaseModel):
    job_id: str
    status: str
    estimated_seconds: int = 15


class BlastRadiusEntry(BaseModel):
    function_id: str
    function_name: str
    file_path: str = ""
    risk_score: float
    failure_path: list[str] = Field(default_factory=list)
    failure_reason: str = ""


class FunctionAnalysis(BaseModel):
    function_id: str
    function_name: str
    risk_score: float
    blast_radius: list[BlastRadiusEntry] = Field(default_factory=list)
    runtime_events: list[dict[str, Any]] = Field(default_factory=list)
    analysis_time_ms: int


# ── Graph ────────────────────────────────────────────────
class GraphNode(BaseModel):
    id: str
    label: str
    risk_score: float
    language: str
    file_path: str
    start_line: int = 0
    end_line: int = 0
    x: float = 0.0
    y: float = 0.0


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    weight: float = 1.0


class GraphResponse(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    total_nodes: int
    page: int = 1


class HealthScoreResponse(BaseModel):
    current_score: float
    trend_7d: float = 0.0
    trend_30d: float = 0.0
    high_risk_count: int = 0
    medium_risk_count: int = 0
    low_risk_count: int = 0


# ── Patches ──────────────────────────────────────────────
class PatchOut(BaseModel):
    patch_id: str
    function_id: str | None
    pattern: str
    confidence: float
    original: str
    patched: str
    verified: bool
    test_results: dict[str, Any] = Field(default_factory=dict)
