"""Analysis endpoints (PRD §8.1) — trigger and retrieve code intelligence."""
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from axiom.core.database import get_db
from axiom.core.security import CurrentUser, get_current_user
from axiom.models.api_models import (
    AnalyzeFileRequest,
    AnalyzeFunctionRequest,
    BlastRadiusEntry,
    FunctionAnalysis,
    JobResponse,
)
from axiom.models.db_models import Project
from axiom.workers.analysis_worker import get_worker

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["analysis"])


@router.post("/file", response_model=JobResponse)
async def analyze_file(
    body: AnalyzeFileRequest,
    background: BackgroundTasks,
    current: CurrentUser = Depends(get_current_user),
) -> JobResponse:
    """Kick off analysis of a single file off the request path (Critical Rule #3)."""
    worker = get_worker()
    background.add_task(worker.analyze_paths, body.project_id, [body.file_path])
    return JobResponse(job_id=f"job-{abs(hash(body.file_path)) % 10**8}", status="queued")


@router.post("/workspace", response_model=JobResponse)
async def analyze_workspace(
    project_id: str,
    background: BackgroundTasks,
    current: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JobResponse:
    """Full workspace scan for a project."""
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    worker = get_worker()
    files = worker.collect_source_files(project.root_path, project.languages)
    background.add_task(worker.analyze_paths, project_id, files)
    return JobResponse(
        job_id=f"job-{project_id[:8]}", status="queued", estimated_seconds=max(5, len(files) // 10)
    )


@router.post("/function", response_model=FunctionAnalysis)
async def analyze_function(
    body: AnalyzeFunctionRequest,
    current: CurrentUser = Depends(get_current_user),
) -> FunctionAnalysis:
    """Return the blast radius for a function from the project's cached graph."""
    worker = get_worker()
    graph = worker.get_graph(body.project_id)
    if graph is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "No analysis yet — run /analyze/workspace first"
        )
    result = await worker.analyze_function(body.project_id, graph, body.function_id)
    return FunctionAnalysis(
        function_id=result["function_id"],
        function_name=result["function_name"],
        risk_score=result["risk_score"],
        blast_radius=[BlastRadiusEntry(**b) for b in result["blast_radius"]],
        analysis_time_ms=result["analysis_time_ms"],
    )
