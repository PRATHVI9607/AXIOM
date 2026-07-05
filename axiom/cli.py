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
    """Analyze a project against a running backend."""
    import time

    import httpx

    from axiom.core.security import create_access_token

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"!! Path does not exist: {root}")
        return 1

    headers = {}
    if args.token:
        headers["Authorization"] = f"Bearer {args.token}"
    else:
        # Works whether the server has auth off (ignored) or on (local dev token).
        token, _ = create_access_token("user:cli", {"roles": ["admin"]})
        headers["Authorization"] = f"Bearer {token}"

    client = httpx.Client(base_url=args.server, headers=headers, timeout=600)
    try:
        client.get("/health").raise_for_status()
    except Exception:
        print(f"!! Backend not reachable at {args.server}. Run `axiom serve` first.")
        return 1

    pid = client.post(
        "/api/v1/projects",
        json={"name": root.name, "root_path": str(root).replace("\\", "/"), "languages": []},
    ).json()["id"]
    print(f"Analyzing {root} …", end="", flush=True)
    client.post(f"/api/v1/analyze/workspace?project_id={pid}")
    graph = {}
    for _ in range(120):
        time.sleep(1)
        r = client.get(f"/api/v1/graph/{pid}")
        if r.status_code == 200 and r.json().get("total_nodes"):
            graph = r.json()
            break
        print(".", end="", flush=True)
    print()
    if not graph:
        print("!! No source files found or analysis timed out.")
        return 1

    health = client.get(f"/api/v1/graph/{pid}/health").json()
    print(f"\n{root.name}: {graph['total_nodes']} functions · health {health['current_score']} "
          f"· {health['high_risk_count']} high-risk")
    for n in sorted(graph["nodes"], key=lambda x: -x["risk_score"])[:8]:
        print(f"  {n['risk_score']:.2f}  {n['label']}  ({Path(n['file_path']).name}:{n['start_line']})")
    print(f"\nproject id: {pid}")
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

    p_an = sub.add_parser("analyze", help="Analyze a project")
    p_an.add_argument("path")
    p_an.add_argument("--server", default="http://localhost:8000")
    p_an.add_argument("--token", default="")
    p_an.set_defaults(func=cmd_analyze)

    p_ver = sub.add_parser("version", help="Print version")
    p_ver.set_defaults(func=lambda _a: (print(f"AXIOM {__version__}"), 0)[1])

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
