# AXIOM — Semantic Runtime Code Intelligence Platform

> Parses code into ASTs, embeds it semantically with LLMs, fuses it with live eBPF
> kernel traces into a GNN intent graph, and predicts cascading failure paths before deploy.

See [PRD.md](PRD.md) for the full spec and [CLAUDE.md](CLAUDE.md) for build rules.

## Status

Phase 1A–1D backend is **built and runnable**; frontend + extension are scaffolded.
See [HANDOFF.md](HANDOFF.md) for exactly what's done and what's next.

## Quick start (backend, local, no Docker)

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -e ".[dev]"
copy .env.example .env            # then edit as needed (SQLite works out of the box)
alembic upgrade head
uvicorn axiom.main:app --reload
```

Open http://localhost:8000/docs for the interactive API, http://localhost:8000/health for status.

## Full stack (Docker)

```bash
docker compose up --build         # Postgres + ChromaDB + API
```

## Real eBPF tracing via WSL (Windows)

eBPF needs a Linux kernel. On Windows we run the tracer inside WSL2 (kernel 6.6+):

```bash
make setup-ebpf        # one-time: installs BCC in WSL
make trace             # starts the privileged tracer daemon (sudo, inside WSL)
```

The API — on Windows or in WSL — reads events from the tracer at `127.0.0.1:8770`
(WSL2 forwards localhost). If the tracer is down, the platform runs static-only.

## Dashboard

```bash
cd dashboard && npm install && npm run dev     # http://localhost:3000
```

## VS Code extension

```bash
cd vscode-extension && npm install && npm run compile
# then press F5 in VS Code to launch an Extension Development Host
```

## Tests

```bash
pytest tests/ -v --cov=axiom --cov-report=term-missing
```

## Architecture

| Layer | Tech | Location |
|---|---|---|
| AST parser | tree-sitter (regex fallback) | `axiom/services/ast_service.py` |
| Embeddings | Ollama / OpenAI / hash fallback | `axiom/services/embed_service.py` |
| Vector store | ChromaDB (ephemeral fallback) | `axiom/services/vector_store.py` |
| eBPF tracer | BCC in WSL, TCP client | `ebpf/`, `axiom/workers/ebpf_worker.py`, `axiom/services/ebpf_service.py` |
| GNN | torch-geometric (heuristic fallback) | `axiom/services/gnn_service.py` |
| Predictor | personalized PageRank | `axiom/services/predict_service.py` |
| Patches | 7 pattern templates | `axiom/services/patch_service.py` |
| API | FastAPI + WebSocket | `axiom/main.py`, `axiom/api/` |
| Dashboard | React + Vite + Tailwind | `dashboard/` |
| Extension | TypeScript, VS Code API | `vscode-extension/` |

Heavy deps (torch, ChromaDB service, tree-sitter grammars, BCC) are **optional** —
every subsystem degrades to a working fallback so the platform boots anywhere.
