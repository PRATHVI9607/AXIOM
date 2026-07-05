"""FastAPI application entry point — wires routers, CORS, WebSocket, lifespan (PRD §7.7)."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import jwt
from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from axiom import __version__
from axiom.api import analysis, auth, graph, health, patches, projects
from axiom.core.config import get_settings
from axiom.core.security import decode_token
from axiom.core.websocket import manager

settings = get_settings()
logging.basicConfig(level=settings.log_level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("axiom")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown hooks (PRD §7.7 startup sequence)."""
    logger.info("AXIOM v%s starting — embed=%s eBPF=%s air_gapped=%s auth=%s",
                __version__, settings.embed_provider, settings.ebpf_available, settings.air_gapped,
                "required" if settings.auth_required else "OFF (local mode)")
    if not settings.auth_required:
        logger.warning(
            "Auth is OFF — every request is a local admin. Fine for localhost; "
            "set AXIOM_AUTH_REQUIRED=true before exposing AXIOM to a network."
        )
    # Warm the analysis worker (loads parser, GNN weights if present).
    from axiom.workers.analysis_worker import get_worker

    get_worker()
    if settings.ebpf_available:
        logger.info("eBPF enabled — API will pull events from tracer at %s:%d",
                    settings.ebpf_tracer_host, settings.ebpf_tracer_port)
    yield
    logger.info("AXIOM shutting down.")


app = FastAPI(
    title="AXIOM",
    description="Semantic Runtime Code Intelligence Platform",
    version=__version__,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── REST routers ─────────────────────────────────────────
app.include_router(health.router)                       # /health, /metrics
API = "/api/v1"
app.include_router(auth.router, prefix=API)              # /api/v1/auth/*
app.include_router(projects.router, prefix=API)          # /api/v1/projects/*
app.include_router(analysis.router, prefix=API)          # /api/v1/analyze/*
app.include_router(graph.router, prefix=API)             # /api/v1/graph/*
app.include_router(patches.router, prefix=API)           # /api/v1/patches/*


@app.get("/")
async def root() -> dict[str, str]:
    return {"name": "AXIOM", "version": __version__, "docs": "/docs"}


# ── WebSocket (PRD §7.8) ─────────────────────────────────
@app.websocket("/ws/{project_id}")
async def websocket_endpoint(
    websocket: WebSocket, project_id: str, token: str = Query(default="")
) -> None:
    """Real-time channel. Requires a valid JWT as the `token` query param
    unless auth is disabled (local single-user mode)."""
    if settings.auth_required:
        try:
            decode_token(token)
        except jwt.InvalidTokenError:
            await websocket.close(code=1008)  # policy violation
            return
    await manager.connect(project_id, websocket)
    try:
        while True:
            msg = await websocket.receive_json()
            # Echo subscribe/analyze acks; full command handling in Phase 1D+.
            await websocket.send_json({"type": "ack", "received": msg.get("type", "unknown")})
    except WebSocketDisconnect:
        await manager.disconnect(project_id, websocket)
