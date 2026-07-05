# AXIOM — Setup & Usage Guide

Everything to run AXIOM, analyze a project, and read the results. Windows + WSL2.

---

## 0. Prerequisites (one-time)

- Python 3.11+ (3.14 works)
- Node.js 18+
- WSL2 with Ubuntu (only for live eBPF; everything else runs without it)

```powershell
cd c:\Workspace\AXIOM
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e ".[dev]"
copy .env.example .env          # SQLite default works out of the box
.venv\Scripts\alembic.exe upgrade head
```

Optional heavier features:
```powershell
.venv\Scripts\python.exe -m pip install tree-sitter tree-sitter-python tree-sitter-javascript tree-sitter-typescript tree-sitter-go tree-sitter-cpp chromadb
.venv\Scripts\python.exe scripts\gen_gnn_weights.py      # bundle the GNN model
```

---

## 1. Start the backend

```powershell
cd c:\Workspace\AXIOM
.venv\Scripts\python.exe -m uvicorn axiom.main:app --port 8000
```
Verify: http://localhost:8000/health · interactive API at http://localhost:8000/docs

---

## 2. Analyze a project

Analyze AXIOM itself (seeds a project, runs analysis, prints a ready link):
```powershell
.venv\Scripts\python.exe scripts\demo.py
```
Analyze YOUR project: create it via the API with a **Windows path**, then trigger a workspace scan.
`/tmp/...` (Git Bash) paths are invisible to the Windows API process — always use `C:/...`.

Tip: if no Ollama server is running, set `AXIOM_EMBED_PROVIDER=local` before starting the
server for instant embeddings (GNN risk uses lexical/structural features, so scores are unchanged).

---

## 3. Dashboard

```powershell
cd c:\Workspace\AXIOM\dashboard
npm install        # first time only
npm run dev        # http://localhost:3000
```
Open the link printed by `demo.py` (token + project baked in). Two tabs:
- **Overview** — health gauge, risk buckets, highest-risk functions, system status
- **Intent Graph** — force-directed graph (red = risky); click a node for its blast radius

---

## 4. VS Code extension (inline risk while you code)

**Install the packaged extension (permanent):**
```powershell
code --install-extension c:\Workspace\AXIOM\vscode-extension\axiom-intelligence-1.0.0.vsix
```
Then reload VS Code. Or, for development, open `vscode-extension/` and press **F5**.

**Configure once (Command Palette, `Ctrl+Shift+P`):**
1. `AXIOM: Set API Token` — paste the token from `demo.py`
2. `AXIOM: Set Project Id` — paste the project id

Open a source file → red/amber/green gutter dots per function, hover for the score,
high-risk functions appear in the **Problems** panel. Status bar bottom-right shows backend state.

---

## 5. Live eBPF runtime tracing (optional, WSL)

```powershell
make setup-ebpf     # one-time: installs BCC in WSL
make trace          # starts the privileged tracer daemon (sudo, inside WSL)
```
The API auto-reads events from `127.0.0.1:8770`. Without it, AXIOM runs static-only.

---

## 6. Reading the output

| Output | Means | Use it to |
|---|---|---|
| **Health score** 0–1 | codebase-wide risk (1 = clean) | track drift over time |
| **Risk score** per function 0–1 | how dangerous one function is | 🔴 ≥0.6 review, 🟡 0.3–0.6 watch, 🟢 <0.3 fine |
| **Blast radius** | functions that break if this one does | test the whole cascade before merging |
| **failure_path** | the call chain a failure travels | find the real root cause |

---

## 7. Tests

```powershell
.venv\Scripts\python.exe -m pytest tests\ -q      # 50 tests
```

---

## 8. Troubleshooting

- **Graph 404 / empty** — analysis not finished or wrong `root_path` (must be a Windows path). Re-run the workspace scan and wait a few seconds.
- **Analysis slow** — no Ollama running; set `AXIOM_EMBED_PROVIDER=local`.
- **Dashboard 401** — token missing/expired; re-run `demo.py` for a fresh link.
- **eBPF unavailable** — expected off WSL; the platform degrades to static-only by design.
