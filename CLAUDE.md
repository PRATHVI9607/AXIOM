# CLAUDE.md — AXIOM Build Instructions

> This file is the single source of truth for Claude when working on the AXIOM project.
> Read this file completely before writing a single line of code.

---

## ⚡ STEP 0 — MANDATORY: Install Skills Before Anything Else

**Do this FIRST. Do not skip. Do not start coding. Install all four skills:**

```bash
claude skills install graphify
claude skills install caveman
claude skills install ponytail
claude skills install claude-mem
```

After all four install successfully, **stop and tell the user exactly this:**

> "✅ All four skills installed: graphify, caveman, ponytail, claude-mem.
> Please reload the window now so the skills activate.
> — On VS Code: Cmd+Shift+P → Developer: Reload Window
> — On Claude Code desktop: close and reopen the project
> Come back after reloading and we'll start building."

**Do not proceed until the user confirms they have reloaded.**

---

## 🧠 Skills & How to Use Them

### `graphify`
Use for any graph-related visualization or structure generation:
- Visualizing the GNN intent graph (nodes, edges, risk scores)
- Rendering the AST parse trees for debugging
- Generating architecture diagrams as part of documentation
- Call it when building the `/api/v1/graph` endpoint and the dashboard's graph explorer page

### `caveman`
Use for debugging and deep inspection tasks:
- Debugging eBPF event capture (tracing which probes fire, what data comes back)
- Inspecting GNN inference outputs (activations, attention weights, risk score distributions)
- Diagnosing slow analysis jobs (profiling which step is the bottleneck)
- Any time something is mysteriously wrong with the runtime tracer — caveman it

### `ponytail`
Use for all frontend and UI work:
- Building the React web dashboard (all pages)
- Building the VS Code extension webview panels (blast radius panel, graph panel)
- Styling with Tailwind CSS
- All Vite config, component scaffolding, and UI state management

### `claude-mem`
Use throughout every session to maintain memory:
- At session start: read memory to remember what was last done
- During session: store important decisions (architecture choices, schema changes, bug discoveries)
- At session end: update memory before creating HANDOFF.md
- Key things to always remember:
  - Current project structure (what files exist)
  - Which components are complete vs in-progress
  - Any environment-specific issues discovered
  - User preferences for code style

---

## 📋 Project Overview

**AXIOM** is a Semantic Runtime Code Intelligence Platform.

Read `PRD.md` for the full specification. This is the one-line summary:

> AXIOM parses code into ASTs, embeds them semantically with LLMs, fuses them with live eBPF kernel traces into a GNN intent graph, and predicts cascading failure paths before deployment.

**GitHub:** https://github.com/PRATHVI9607/AXIOM  
**Owner:** Rakshak S  

---

## 🏗️ Architecture at a Glance

```
tree-sitter (AST) ──┐
                    ├──▶ GNN Intent Graph ──▶ Failure Predictor ──▶ Patch Generator
LLM Embedder ───────┤
                    │
eBPF Tracer ────────┘
                         │
                    FastAPI Backend + WebSocket
                         │
           ┌─────────────┼─────────────┐
        PostgreSQL    ChromaDB    React Dashboard
                                       │
                              VS Code Extension
```

**Core tech stack:**
- Backend: Python 3.11+, FastAPI, SQLAlchemy async, Alembic
- ML: PyTorch 2.3+, torch-geometric, sentence-transformers
- Parsing: tree-sitter (Python bindings)
- eBPF: BCC Python bindings (Linux only)
- Vector DB: ChromaDB 0.5+
- Relational DB: PostgreSQL 16
- Frontend: React 18, TypeScript, Vite, Tailwind CSS, shadcn/ui
- Extension: TypeScript, VS Code Extension API
- Auth: GitHub OAuth, RS256 JWT
- Deployment: Docker Compose (dev), Kubernetes Helm (prod)

---

## 📁 Project Structure

Build the project in this exact structure:

```
AXIOM/
├── axiom/                          # Python backend
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry
│   ├── api/
│   │   ├── __init__.py
│   │   ├── analysis.py
│   │   ├── graph.py
│   │   ├── patches.py
│   │   ├── projects.py
│   │   ├── health.py
│   │   └── auth.py
│   ├── services/
│   │   ├── ast_service.py
│   │   ├── embed_service.py
│   │   ├── ebpf_service.py
│   │   ├── gnn_service.py
│   │   ├── predict_service.py
│   │   └── patch_service.py
│   ├── models/
│   │   ├── db_models.py
│   │   ├── api_models.py
│   │   └── gnn_v1.pt              # Pre-trained weights (download script)
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   └── websocket.py
│   └── workers/
│       ├── analysis_worker.py
│       └── ebpf_worker.py
├── vscode-extension/
│   ├── src/
│   │   ├── extension.ts
│   │   ├── axiomClient.ts
│   │   ├── providers/
│   │   ├── views/
│   │   └── commands/
│   ├── package.json
│   └── tsconfig.json
├── dashboard/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── pages/
│   │   ├── components/
│   │   └── hooks/
│   ├── package.json
│   └── vite.config.ts
├── ebpf/
│   └── syscall_tracer.bpf.c
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── k8s/
│   └── helm/axiom/
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── pyproject.toml
├── PRD.md
├── CLAUDE.md
└── README.md
```

---

## 🔧 Build Order (Follow This Exactly)

Build components in this order — each one depends on the previous:

### Phase 1A: Foundation (Do First)
1. Project scaffold — pyproject.toml, Dockerfile, docker-compose.yml, Makefile
2. Core config — `axiom/core/config.py` (pydantic-settings, all env vars)
3. Database — `axiom/core/database.py` + `axiom/models/db_models.py` + Alembic migrations
4. FastAPI app — `axiom/main.py` with health endpoint only
5. Auth — `axiom/api/auth.py` + `axiom/core/security.py`

### Phase 1B: Parsing & Embedding
6. AST Parser — `axiom/services/ast_service.py` (tree-sitter, all 5 languages)
7. File watcher — using watchdog, triggers incremental re-parse
8. LLM Embedder — `axiom/services/embed_service.py` (Ollama + OpenAI + fallback)
9. ChromaDB integration — store and retrieve embeddings by function_id

### Phase 1C: eBPF & GNN
10. eBPF tracer — `axiom/services/ebpf_service.py` + `ebpf/syscall_tracer.bpf.c`
11. GNN graph construction — `axiom/services/gnn_service.py`
12. Failure predictor — `axiom/services/predict_service.py`

### Phase 1D: API & Real-Time
13. Analysis endpoints — `axiom/api/analysis.py`
14. Graph endpoints — `axiom/api/graph.py`
15. WebSocket server — `axiom/core/websocket.py`
16. Background workers — `axiom/workers/analysis_worker.py`

### Phase 1E: Frontend
17. React dashboard scaffold — (use ponytail skill here)
18. Dashboard pages — health, graph explorer, function detail
19. VS Code extension — (use ponytail skill here)

### Phase 1F: Patch Generator
20. Patch generator — `axiom/services/patch_service.py`
21. Patch endpoints — `axiom/api/patches.py`
22. Formal verifier — property-based tests using hypothesis

### Phase 1G: Deployment
23. Docker Compose — full stack, one command startup
24. CI/CD plugin — GitHub Actions axiom-action
25. Tests — unit + integration + e2e

---

## 🧑‍💻 Coding Standards

### Python
- Python 3.11+ minimum
- Use `async/await` everywhere (asyncio throughout)
- Type hints on every function signature
- Pydantic models for all API request/response schemas
- SQLAlchemy 2.0 async style (`async with AsyncSession()`)
- Docstrings on all public functions
- Black formatting, isort imports
- Never use bare `except` — always catch specific exceptions
- Log every background task start/end/error with `logging.getLogger(__name__)`

### TypeScript (Extension + Dashboard)
- Strict mode always on
- No `any` types — use proper interfaces
- React functional components only, hooks-based
- All async operations wrapped in try/catch with user-facing error display
- Tailwind for all styling — no inline styles

### General
- Every file starts with a one-line comment explaining what it does
- Environment variables accessed only through `config.py` — never `os.environ` directly in business logic
- Secrets never hardcoded — always from env
- Docker Compose services depend_on with health checks

---

## ⚙️ Environment Setup

Create `.env.example` with these variables (user fills in secrets):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://axiom:axiom@localhost:5432/axiom

# ChromaDB
CHROMA_URL=http://localhost:8001

# Embedding (choose one)
AXIOM_EMBED_PROVIDER=ollama
AXIOM_OLLAMA_URL=http://localhost:11434
AXIOM_OLLAMA_MODEL=nomic-embed-text
OPENAI_API_KEY=                     # Only if using OpenAI

# Auth
AXIOM_JWT_PRIVATE_KEY=              # RS256 PEM private key
AXIOM_JWT_PUBLIC_KEY=               # RS256 PEM public key
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
AXIOM_AUTH_PROVIDER=github

# eBPF
AXIOM_EBPF_ENABLED=true

# Deployment
AXIOM_BASE_URL=http://localhost:8000
AXIOM_FRONTEND_URL=http://localhost:3000
AXIOM_LOG_LEVEL=INFO
AXIOM_AIR_GAPPED=false
```

The Makefile should have:
```makefile
install:        ## Install all dependencies
run:            ## Start full stack with Docker Compose
run-dev:        ## Start backend in hot-reload mode
test:           ## Run all tests
migrate:        ## Run Alembic migrations
lint:           ## Run black + isort + mypy
build-ext:      ## Build VS Code extension
build-dash:     ## Build React dashboard
```

---

## 🧪 Testing Requirements

Every component must have tests before moving to the next phase.

Minimum test coverage gates:
- Phase 1A (Foundation): 90% coverage on core/
- Phase 1B (Parser/Embedder): 80% on services/ast_service.py, services/embed_service.py
- Phase 1C (eBPF/GNN): 70% (eBPF is hard to unit test fully)
- Phase 1D (API): All endpoints have at least happy path + auth failure + bad input tests
- Phase 1F (Patches): All 7 patch patterns have unit tests

Run tests with:
```bash
pytest tests/ -v --cov=axiom --cov-report=term-missing
```

---

## 🚨 Critical Rules — Never Violate These

1. **Never send raw source code to external APIs.** Only embeddings (vectors) go out. Source text stays local.
2. **Never drop eBPF privileges.** The tracer runs as a separate process with minimum capabilities. Never merge it into the main API process.
3. **Never block the FastAPI event loop.** All heavy computation (GNN inference, embedding) goes to background workers or thread pools (`run_in_executor`).
4. **Never store secrets in the codebase.** Not in config files, not in comments, not in tests. Use `.env` and environment variables only.
5. **Never skip migrations.** Every schema change goes through Alembic. Never `create_all()` in production code.
6. **Never use synchronous SQLAlchemy in async contexts.** Use `asyncpg` + async SQLAlchemy 2.0 throughout.
7. **eBPF features must degrade gracefully.** If eBPF is unavailable (macOS, old kernel), the app runs in static-only mode without crashing.

---

## 📝 HANDOFF.md — Session Protocol

**At the END of every coding session, before closing:**

Create or update `HANDOFF.md` in the project root with this exact structure:

```markdown
# AXIOM Session Handoff

## Session Date
{date and time}

## What Was Accomplished This Session
{bullet list of every file created/modified and what it does}

## Current State of the Build
- Phase: {which phase from the build order above}
- Last completed step: {step number and name}
- Next step to start: {step number and name}
- Estimated steps remaining in current phase: {N}

## Files Created/Modified
{list every file touched, with one line explaining its current state}

## How to Run What's Been Built So Far
```bash
{exact commands to start whatever is working right now}
```

## Tests Passing
{list which test files pass, which are skipped, any known failures}

## Blockers & Known Issues
{anything that's broken, stuck, needs user input, or needs research}

## Decisions Made This Session
{any architecture or design decisions made, with reasoning}

## Environment Notes
{anything specific about the user's environment discovered this session}

## What to Do at the Start of Next Session
{exact first 3 steps for Claude to take next session}
```

**Before creating HANDOFF.md, use `claude-mem` to save the session state to memory.**

This ensures continuity even if the handoff file gets lost.

---

## 🔄 How to Start a New Session (After a Handoff)

When starting a new session on this project:

1. Use `claude-mem` to recall the last session state
2. Read `HANDOFF.md` for the detailed context
3. Read this `CLAUDE.md` to refresh build rules
4. Tell the user: "I'm picking up from {last step}. Here's what we'll do today: {next 3 steps}."
5. Confirm with user before starting
6. Begin from exactly where the handoff says

---

## 📎 Quick Reference

| Component | Language | Key Files |
|---|---|---|
| AST Parser | Python | `axiom/services/ast_service.py` |
| LLM Embedder | Python | `axiom/services/embed_service.py` |
| eBPF Tracer | Python + C | `axiom/services/ebpf_service.py`, `ebpf/syscall_tracer.bpf.c` |
| GNN Engine | Python | `axiom/services/gnn_service.py` |
| Failure Predictor | Python | `axiom/services/predict_service.py` |
| Patch Generator | Python | `axiom/services/patch_service.py` |
| API Backend | Python | `axiom/main.py`, `axiom/api/` |
| WebSocket | Python | `axiom/core/websocket.py` |
| Web Dashboard | TypeScript/React | `dashboard/src/` |
| VS Code Extension | TypeScript | `vscode-extension/src/` |
| CI/CD Plugin | YAML + TypeScript | `axiom-action/` |
| Deployment | YAML | `docker-compose.yml`, `k8s/` |

---

*CLAUDE.md for AXIOM v1.0.0 — Rakshak S*
