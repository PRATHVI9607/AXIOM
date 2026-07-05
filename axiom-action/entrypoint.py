#!/usr/bin/env python3
"""AXIOM Action entrypoint — triggers analysis, gates on risk, writes PR report (PRD §7.11)."""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request


def _get(env: str, default: str = "") -> str:
    return os.environ.get(env, default)


def _api(method: str, path: str, token: str, body: dict | None = None) -> dict:
    url = f"{_get('AXIOM_SERVER').rstrip('/')}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as resp:  # noqa: S310 - trusted server
        return json.loads(resp.read().decode())


def _set_output(name: str, value: str) -> None:
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"{name}={value}\n")


def main() -> int:
    server = _get("AXIOM_SERVER")
    token = _get("AXIOM_TOKEN")
    project = _get("AXIOM_PROJECT")
    threshold = float(_get("RISK_THRESHOLD", "0.7"))
    block = _get("BLOCK", "true").lower() == "true"

    if not (server and token and project):
        print("::error::axiom-server, axiom-token, and project-id are required")
        return 1

    print(f"AXIOM: analyzing project {project} at {server}")
    try:
        _api("POST", f"/api/v1/analyze/workspace?project_id={project}", token, {})
        time.sleep(5)  # let background analysis populate the graph
        graph = _api("GET", f"/api/v1/graph/{project}", token)
        health = _api("GET", f"/api/v1/graph/{project}/health", token)
    except urllib.error.URLError as exc:
        print(f"::error::AXIOM request failed: {exc}")
        return 1

    nodes = graph.get("nodes", [])
    high = [n for n in nodes if n.get("risk_score", 0) >= threshold]
    max_risk = max((n.get("risk_score", 0) for n in nodes), default=0.0)

    report = {"project": project, "health": health, "high_risk": high, "max_risk": max_risk}
    with open("axiom-report.json", "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)

    with open("axiom-report.md", "w", encoding="utf-8") as fh:
        fh.write("## 🔬 AXIOM Code Intelligence Report\n\n")
        fh.write(f"**Codebase health:** {health.get('current_score', 'n/a')}\n")
        fh.write(f"**Functions analyzed:** {len(nodes)}\n")
        fh.write(f"**High-risk (≥ {threshold}):** {len(high)}\n\n")
        if high:
            fh.write("| Function | File | Risk |\n|---|---|---|\n")
            for n in sorted(high, key=lambda x: -x["risk_score"])[:20]:
                fh.write(f"| `{n['label']}` | {n['file_path']}:{n.get('start_line',0)} | 🔴 {n['risk_score']:.2f} |\n")
        fh.write("\n---\n*Analysis by AXIOM — Semantic Runtime Code Intelligence*\n")

    _set_output("report-path", "axiom-report.json")
    _set_output("max-risk", f"{max_risk:.4f}")

    print(f"AXIOM: max risk {max_risk:.2f}, {len(high)} high-risk functions")
    if high and block:
        print(f"::error::AXIOM gate failed: {len(high)} functions exceed risk {threshold}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
