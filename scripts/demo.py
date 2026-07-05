#!/usr/bin/env python3
"""One-shot demo seeder: analyze AXIOM's own code and print everything you need.

Prereq: the API server is already running (see printed steps). Run:
    .venv\\Scripts\\python.exe scripts/demo.py
It creates a project for AXIOM itself, runs a full analysis over HTTP, then prints
a ready dashboard link (token embedded), the project id, and sample curl calls.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import httpx

# Make `axiom` importable when run from the repo root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from axiom.core.security import create_access_token  # noqa: E402

API = "http://localhost:8000"
DASHBOARD = "http://localhost:3000"
ROOT = str(Path(__file__).resolve().parent.parent / "axiom")  # analyze AXIOM itself


def main() -> int:
    token, _ = create_access_token("user:demo", {"username": "demo", "roles": ["admin"]})
    headers = {"Authorization": f"Bearer {token}"}
    client = httpx.Client(base_url=API, headers=headers, timeout=180)

    try:
        client.get("/health").raise_for_status()
    except Exception:
        print(f"!! API not reachable at {API}. Start it first:")
        print("   .venv\\Scripts\\python.exe -m uvicorn axiom.main:app --port 8000")
        return 1

    project = client.post(
        "/api/v1/projects",
        json={"name": "AXIOM (self)", "root_path": ROOT, "languages": ["python"]},
    ).json()
    pid = project["id"]
    print(f"Created project {pid} -> {ROOT}")

    client.post(f"/api/v1/analyze/workspace?project_id={pid}")
    print("Analyzing", end="", flush=True)
    graph = {}
    for _ in range(60):
        time.sleep(1)
        resp = client.get(f"/api/v1/graph/{pid}")
        if resp.status_code == 200 and resp.json().get("total_nodes"):
            graph = resp.json()
            break
        print(".", end="", flush=True)
    print()

    if not graph:
        print("!! Analysis did not finish in time.")
        return 1

    health = client.get(f"/api/v1/graph/{pid}/health").json()
    top = sorted(graph["nodes"], key=lambda n: -n["risk_score"])[:5]

    bar = "=" * 62
    print(f"\n{bar}\nAXIOM analysis of its own backend\n{bar}")
    print(f"functions: {graph['total_nodes']}   edges: {len(graph['edges'])}")
    print(
        f"health: {health['current_score']}   "
        f"high: {health['high_risk_count']}  med: {health['medium_risk_count']}  low: {health['low_risk_count']}"
    )
    print("\ntop risk:")
    for n in top:
        fname = Path(n["file_path"]).name
        print(f"  {n['risk_score']:.2f}  {n['label']:24} {fname}:{n['start_line']}")

    print(f"\n{bar}\nOPEN THE DASHBOARD (token + project preloaded):\n{bar}")
    print(f"  {DASHBOARD}/graph?token={token}&project={pid}")
    print("\nVS Code extension: run 'AXIOM: Set API Token' then 'AXIOM: Set Project Id':")
    print(f"  token:   {token}")
    print(f"  project: {pid}")
    print(f"\nRaw API example:")
    print(f'  curl -H "Authorization: Bearer <token>" {API}/api/v1/graph/{pid}/health')
    return 0


if __name__ == "__main__":
    sys.exit(main())
