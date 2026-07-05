"""AXIOM command-line entry point. Installed as `axiom` (see pyproject scripts).

    axiom serve [--host H] [--port P]     start the backend (ensures schema first)
    axiom analyze <path> [--server URL]   analyze a project and print a summary
    axiom version
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from axiom import __version__

logger = logging.getLogger("axiom.cli")


def _ensure_schema() -> None:
    """Bring the database schema up to date.

    Prefers Alembic migrations when the repo's alembic/ is present (dev/prod).
    Falls back to create_all for a fresh local SQLite DB so `pip install axiom`
    users get a working backend with zero setup (local single-user convenience).
    """
    repo_root = Path(__file__).resolve().parent.parent
    alembic_ini = repo_root / "alembic.ini"
    if alembic_ini.exists():
        try:
            from alembic import command
            from alembic.config import Config

            cfg = Config(str(alembic_ini))
            cfg.set_main_option("script_location", str(repo_root / "alembic"))
            command.upgrade(cfg, "head")
            return
        except Exception as exc:  # noqa: BLE001 - fall through to create_all
            logger.warning("Alembic migration failed (%s); creating tables directly.", exc)

    import asyncio

    from axiom.core.database import Base, engine
    from axiom.models import db_models  # noqa: F401 - register tables

    async def _create() -> None:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    asyncio.run(_create())
    logger.info("Database schema ready (create_all).")


def cmd_serve(args: argparse.Namespace) -> int:
    """Start the FastAPI backend with uvicorn."""
    import uvicorn

    _ensure_schema()
    print(f"AXIOM {__version__} serving on http://{args.host}:{args.port}  (docs at /docs)")
    uvicorn.run(
        "axiom.main:app",
        host=args.host,
        port=args.port,
        log_level=args.log_level,
        reload=args.reload,
    )
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Analyze a project directly, in-process — no running server required."""
    import asyncio
    import os

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"!! Path does not exist: {root}")
        return 1

    # Local hash embeddings by default so the CLI is fast with no Ollama/OpenAI.
    os.environ.setdefault("AXIOM_EMBED_PROVIDER", "local")

    from axiom.services.gnn_service import get_gnn
    from axiom.workers.analysis_worker import get_worker

    worker = get_worker()
    files = worker.collect_source_files(str(root))
    if not files:
        print(f"!! No supported source files under {root}")
        return 1

    print(f"Analyzing {len(files)} files under {root} …")
    graph, _ = asyncio.run(worker.analyze_paths("cli", files))

    gnn = get_gnn()
    nodes = sorted(graph.nodes.values(), key=lambda n: n.risk_score, reverse=True)
    high = sum(1 for n in nodes if n.risk_score >= 0.6)
    med = sum(1 for n in nodes if 0.3 <= n.risk_score < 0.6)
    low = len(nodes) - high - med

    print(f"\n{root.name}: {len(nodes)} functions · health {gnn.codebase_health(graph)} "
          f"· {high} high / {med} med / {low} low\n")
    for n in nodes[: args.top]:
        print(f"  {n.risk_score:.2f}  {n.label:28} {Path(n.file_path).name}:{n.start_line}")
    if args.json:
        import json

        Path(args.json).write_text(
            json.dumps(
                {
                    "health": gnn.codebase_health(graph),
                    "functions": [
                        {"name": n.label, "file": n.file_path, "line": n.start_line, "risk": n.risk_score}
                        for n in nodes
                    ],
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"\nWrote {args.json}")
    return 0


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level="INFO", format="%(message)s")
    parser = argparse.ArgumentParser(prog="axiom", description="AXIOM code intelligence")
    sub = parser.add_subparsers(dest="command", required=True)

    p_serve = sub.add_parser("serve", help="Start the backend server")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--log-level", default="info")
    p_serve.add_argument("--reload", action="store_true", help="Auto-reload (development)")
    p_serve.set_defaults(func=cmd_serve)

    p_an = sub.add_parser("analyze", help="Analyze a project in-process (no server)")
    p_an.add_argument("path", help="Path to the project root")
    p_an.add_argument("--top", type=int, default=15, help="How many top-risk functions to print")
    p_an.add_argument("--json", default="", help="Also write full results to this JSON file")
    p_an.set_defaults(func=cmd_analyze)

    p_ver = sub.add_parser("version", help="Print version")
    p_ver.set_defaults(func=lambda _a: (print(f"AXIOM {__version__}"), 0)[1])

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
