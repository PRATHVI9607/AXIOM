#!/usr/bin/env python3
"""Analyze ANY project with AXIOM.

Usage (backend must be running on :8000):
    .venv\\Scripts\\python.exe scripts\\analyze.py "C:\\path\\to\\your\\project"

Creates a project, runs a full analysis over HTTP, then prints a ready dashboard
link (token + project embedded) plus the token/project for the VS Code extension.
Point it at a Windows path — WSL/Git-Bash `/tmp` paths are invisible to the API.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from axiom.core.security import create_access_token  # noqa: E402

API = "http://localhost:8000"
DASHBOARD = "http://localhost:3000"


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze any project with AXIOM")
    ap.add_argument("path", help="Absolute path to the project root (Windows path)")
    ap.add_argument("--name", default=None, help="Project name (defaults to folder name)")
    ap.add_argument("--api", default=API, help="AXIOM backend URL")
    args = ap.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"!! Path does not exist: {root}")
        return 1
    name = args.name or root.name

    token, _ = create_access_token("user:cli", {"username": "cli", "roles": ["admin"]})
    client = httpx.Client(base_url=args.api, headers={"Authorization": f"Bearer {token}"}, timeout=600)

    try:
        client.get("/health").raise_for_status()
    except Exception:
        print(f"!! Backend not reachable at {args.api}. Start it first:")
        print("   .venv\\Scripts\\python.exe -m uvicorn axiom.main:app --port 8000")
        return 1

    pid = client.post(
        "/api/v1/projects",
        json={"name": name, "root_path": str(root).replace("\\", "/"), "languages": []},
    ).json()["id"]
    print(f"Project '{name}' -> {pid}\nAnalyzing {root}", end="", flush=True)

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
        print("!! No source files found or analysis timed out. Is the path a code project?")
        return 1

    health = client.get(f"/api/v1/graph/{pid}/health").json()
    top = sorted(graph["nodes"], key=lambda n: -n["risk_score"])[:8]

    bar = "=" * 64
    print(f"\n{bar}\n{name}\n{bar}")
    print(f"functions: {graph['total_nodes']}   edges: {len(graph['edges'])}")
    print(
        f"health: {health['current_score']}   "
        f"high: {health['high_risk_count']}  med: {health['medium_risk_count']}  low: {health['low_risk_count']}\n"
    )
    for n in top:
        fname = Path(n["file_path"]).name
        print(f"  {n['risk_score']:.2f}  {n['label']:26} {fname}:{n['start_line']}")

    print(f"\n{bar}\nDASHBOARD (token + project preloaded):\n{bar}")
    print(f"  {DASHBOARD}/graph?token={token}&project={pid}")
    print("\nVS Code extension: 'AXIOM: Set API Token' + 'AXIOM: Set Project Id':")
    print(f"  token:   {token}")
    print(f"  project: {pid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
