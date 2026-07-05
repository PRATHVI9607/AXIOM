"""Intent-graph endpoints (PRD §8.2) — nodes, edges, and codebase health."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from axiom.core.security import CurrentUser, get_current_user
from axiom.models.api_models import (
    GraphEdge,
    GraphNode,
    GraphResponse,
    HealthScoreResponse,
)
from axiom.workers.analysis_worker import get_worker

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/{project_id}", response_model=GraphResponse)
async def get_graph(
    project_id: str,
    page: int = 1,
    page_size: int = 1000,
    risk_min: float = 0.0,
    risk_max: float = 1.0,
    current: CurrentUser = Depends(get_current_user),
) -> GraphResponse:
    """Return the intent graph (paginated, risk-filtered) for visualization."""
    graph = get_worker().get_graph(project_id)
    if graph is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No graph — run analysis first")

    nodes = [
        GraphNode(
            id=n.id,
            label=n.label,
            risk_score=n.risk_score,
            language=n.language,
            file_path=n.file_path,
            start_line=n.start_line,
            end_line=n.end_line,
        )
        for n in graph.nodes.values()
        if risk_min <= n.risk_score <= risk_max
    ]
    start = (page - 1) * page_size
    page_nodes = nodes[start : start + page_size]
    node_ids = {n.id for n in page_nodes}
    edges = [
        GraphEdge(source=e.source, target=e.target, type=e.type, weight=e.weight)
        for e in graph.edges
        if e.source in node_ids or e.target in node_ids
    ]
    return GraphResponse(nodes=page_nodes, edges=edges, total_nodes=len(nodes), page=page)


@router.get("/{project_id}/health", response_model=HealthScoreResponse)
async def graph_health(
    project_id: str,
    current: CurrentUser = Depends(get_current_user),
) -> HealthScoreResponse:
    """Return codebase health score and risk-bucket counts."""
    worker = get_worker()
    graph = worker.get_graph(project_id)
    if graph is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No graph — run analysis first")
    high = sum(1 for n in graph.nodes.values() if n.risk_score >= 0.6)
    medium = sum(1 for n in graph.nodes.values() if 0.3 <= n.risk_score < 0.6)
    low = sum(1 for n in graph.nodes.values() if n.risk_score < 0.3)
    return HealthScoreResponse(
        current_score=worker.gnn.codebase_health(graph),
        high_risk_count=high,
        medium_risk_count=medium,
        low_risk_count=low,
    )
