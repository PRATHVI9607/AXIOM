"""Health and metrics endpoints (PRD §8, unauthenticated)."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from axiom import __version__
from axiom.core import database
from axiom.core.config import Settings, get_settings
from axiom.models.api_models import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """Report liveness and the status of key subsystems."""
    db_ok = await database.ping()
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        version=__version__,
        database=db_ok,
        ebpf_available=settings.ebpf_available,
        embed_provider=settings.embed_provider,
        air_gapped=settings.air_gapped,
    )


@router.get("/metrics")
async def metrics() -> dict[str, str]:
    """Minimal Prometheus-style text placeholder (expand in Phase 2)."""
    return {"axiom_up": "1"}
