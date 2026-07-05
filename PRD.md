# AXIOM — Semantic Runtime Code Intelligence Platform
## Product Requirements Document (PRD)

**Version:** 1.0.0  
**Author:** Rakshak S  
**GitHub:** github.com/PRATHVI9607/AXIOM  
**Date:** July 2026  
**Status:** Active Development  
**Classification:** Internal Engineering Document

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement & Market Gap](#2-problem-statement--market-gap)
3. [Vision, Mission & Core Philosophy](#3-vision-mission--core-philosophy)
4. [Goals, Non-Goals & Success Metrics](#4-goals-non-goals--success-metrics)
5. [User Personas & Use Cases](#5-user-personas--use-cases)
6. [System Architecture Overview](#6-system-architecture-overview)
7. [Component Deep Dives](#7-component-deep-dives)
   - 7.1 Multi-Language AST Parser
   - 7.2 LLM Semantic Embedding Engine
   - 7.3 eBPF Runtime Tracer
   - 7.4 GNN Intent Graph Engine
   - 7.5 Cascading Failure Predictor
   - 7.6 Patch Generator & Formal Verifier
   - 7.7 FastAPI Backend
   - 7.8 WebSocket Real-Time Server
   - 7.9 VS Code Extension
   - 7.10 Web Dashboard
   - 7.11 CI/CD Plugin
   - 7.12 Database Layer
   - 7.13 Authentication & Authorization
   - 7.14 Air-Gapped Mode
8. [API Specifications](#8-api-specifications)
9. [Database Schema](#9-database-schema)
10. [Security Architecture](#10-security-architecture)
11. [Performance Requirements & SLAs](#11-performance-requirements--slas)
12. [Testing Strategy](#12-testing-strategy)
13. [Deployment Architecture](#13-deployment-architecture)
14. [Phased Roadmap](#14-phased-roadmap)
15. [Risk Assessment & Mitigations](#15-risk-assessment--mitigations)
16. [Appendix](#16-appendix)

---

## 1. Executive Summary

AXIOM is the world's first **Semantic Runtime Code Intelligence Platform** — a developer tool that understands what your code *means*, watches what it *does* at the OS level, and predicts what will *break* before it breaks.

Existing tools (SonarQube, Snyk, GitHub Copilot, Datadog) each solve one slice of the problem: static analysis, security scanning, code generation, or runtime monitoring. None of them combine all three layers — **static semantic understanding + runtime OS-level behaviour + graph-based failure prediction** — into a single unified developer experience.

AXIOM closes this gap by:

- Parsing codebases in **5 languages** using tree-sitter to extract Abstract Syntax Trees
- Embedding every function's **semantic meaning** into a high-dimensional vector space using local or API-based LLMs
- Fusing those embeddings with **live eBPF syscall traces** from the kernel into a GNN-based **intent graph**
- Using that intent graph to **predict cascading failure paths** and security vulnerabilities before deployment
- **Auto-generating formally verified patches** for detected issues
- Exposing everything through a **VS Code extension**, a **web dashboard**, and a **Kubernetes-native CI/CD plugin**

AXIOM is designed to be **laptop-runnable** (no GPU training required), **air-gappable**, and **production-ready** from day one.

---

## 2. Problem Statement & Market Gap

### 2.1 The Core Problem

Software bugs and security vulnerabilities cost the global economy an estimated **$6 trillion per year**. The average production incident costs **$5,600 per minute**. Despite decades of tooling, three fundamental problems remain unsolved:

**Problem 1: Syntax-only analysis**  
Every major static analysis tool (ESLint, Pylint, SonarQube, Semgrep) operates on syntax trees. They understand *what the code says*, not *what the code means*. A function named `processPayment()` that silently deletes records looks perfectly fine to a linter.

**Problem 2: Runtime blindness at the static analysis stage**  
Static analysis tools have zero knowledge of what code does at runtime — which syscalls it invokes, which files it touches, which network connections it opens. Runtime tools (Datadog, Dynatrace, Prometheus) see behaviour but cannot link it back to specific functions in source code.

**Problem 3: The missing causal link**  
When a failure cascades across a distributed system, engineers spend hours bisecting logs to find the root cause. No existing tool can pre-emptively map the *causal chain* — "if function A's behaviour changes, functions B, C, and F will likely fail downstream."

### 2.2 The Competitive Landscape

| Tool | Static Analysis | Semantic Understanding | Runtime Tracing | Failure Prediction | Patch Generation |
|---|---|---|---|---|---|
| SonarQube | ✅ Syntax | ❌ | ❌ | ❌ | ❌ |
| Snyk | ✅ Partial | ❌ | ❌ | ❌ | Partial |
| GitHub Copilot | ❌ | Partial | ❌ | ❌ | ✅ Generation only |
| Datadog | ❌ | ❌ | ✅ | ❌ | ❌ |
| DeepCode | ✅ ML-based | Partial | ❌ | ❌ | ❌ |
| **AXIOM** | **✅ Semantic** | **✅ Full LLM** | **✅ eBPF** | **✅ GNN-based** | **✅ Verified** |

### 2.3 The Market Opportunity

- 30M+ developers worldwide, all of whom ship code with hidden failure paths
- $85B developer tooling market (2026)
- Zero existing tools at the intersection of semantic analysis + runtime tracing + GNN-based prediction

---

## 3. Vision, Mission & Core Philosophy

### 3.1 Vision

A world where software never silently breaks — because AXIOM tells you exactly what will fail, why it will fail, and how to fix it, before a single user is affected.

### 3.2 Mission

To give every developer a senior engineer's intuition about their codebase, powered by the full stack of computer science: compilers, operating systems, machine learning, distributed systems, formal methods, and human-computer interaction.

### 3.3 Core Philosophy

**1. Understand meaning, not syntax.**  
AXIOM reads code the way a human expert would — understanding intent, not just structure.

**2. Trust the kernel, not the application.**  
Runtime behaviour is captured at the OS level via eBPF. Applications cannot lie to the kernel.

**3. Predict, don't just detect.**  
After a bug is in production, detection is too late. AXIOM predicts failure paths before deployment.

**4. Never phone home.**  
All analysis can run fully local. No code ever leaves the developer's machine unless they explicitly choose cloud embedding APIs.

**5. Usable in 5 minutes.**  
Install the VS Code extension, run one command, and get your first insight within 5 minutes.

---

## 4. Goals, Non-Goals & Success Metrics

### 4.1 Goals (Phase 1 — MVP)

- Parse Python, JavaScript, TypeScript, Go, and C++ codebases up to 500K LOC
- Embed function-level semantic meaning using local Ollama (nomic-embed or similar) or OpenAI API
- Capture eBPF syscall traces on Linux (Ubuntu 20.04+, kernel 5.4+)
- Build a GNN intent graph from combined static + runtime data
- Predict top-5 cascading failure paths for any changed function
- Generate patch suggestions for top-3 vulnerability patterns
- VS Code extension showing inline failure risk scores
- Web dashboard with graph visualization and alert management
- FastAPI backend with full REST API
- PostgreSQL for structured data, ChromaDB for vector embeddings
- OAuth 2.0 authentication (GitHub OAuth preferred)
- Docker Compose single-command deployment

### 4.2 Goals (Phase 2 — Production)

- Kubernetes-native deployment with Helm chart
- CI/CD plugin for GitHub Actions and GitLab CI
- Lightweight formal invariant verification on generated patches
- Support for Java and Rust (bringing total to 7 languages)
- Air-gapped zero-egress deployment mode
- Multi-user workspace support with RBAC
- ONNX export of GNN model for edge deployment
- Real-time collaborative analysis sessions via WebSocket

### 4.3 Non-Goals

- AXIOM will **not** train LLMs from scratch. It uses existing embedding models.
- AXIOM will **not** be a code editor or IDE replacement.
- AXIOM will **not** replace runtime APM tools (Datadog, New Relic) for production monitoring.
- AXIOM will **not** analyze mobile (iOS/Android) native binaries initially.
- AXIOM will **not** support Windows kernel tracing in Phase 1 (Linux only for eBPF).

### 4.4 Success Metrics

| Metric | Phase 1 Target | Phase 2 Target |
|---|---|---|
| Time to first insight (install → analysis) | < 5 minutes | < 2 minutes |
| False positive rate on failure prediction | < 25% | < 10% |
| Patch acceptance rate by developers | > 40% | > 65% |
| Max codebase size supported | 500K LOC | 5M LOC |
| Analysis latency (incremental, on change) | < 30 seconds | < 5 seconds |
| P99 API response time | < 500ms | < 100ms |
| Test coverage | > 70% | > 85% |

---

## 5. User Personas & Use Cases

### 5.1 Persona A — The Solo Developer (Primary)

**Name:** Priya  
**Role:** Full-stack developer at a 5-person startup  
**Tech Stack:** Python + TypeScript, running on Linux  
**Pain Point:** "I push code and things break in ways I didn't expect. I don't have time to read every function before every deploy."  
**AXIOM Use Case:** Installs the VS Code extension. Before every `git push`, AXIOM shows her a risk score on every changed function and highlights the top-3 downstream functions that might break. She fixes the real issue, not the symptom.

### 5.2 Persona B — The Platform Engineer (Secondary)

**Name:** Arjun  
**Role:** Senior SRE at a 500-person fintech company  
**Tech Stack:** Go microservices on Kubernetes  
**Pain Point:** "A deploy goes bad and I spend 3 hours bisecting logs to find which service caused it."  
**AXIOM Use Case:** Integrates AXIOM into the CI/CD pipeline. Every pull request gets a AXIOM report showing the predicted failure blast radius. The team blocks deploys where the predicted failure probability exceeds 0.7.

### 5.3 Persona C — The Security Researcher (Tertiary)

**Name:** Zara  
**Role:** AppSec engineer doing code reviews  
**Tech Stack:** C++ and Python, air-gapped environment  
**Pain Point:** "I need to audit third-party code without sending it to any cloud service."  
**AXIOM Use Case:** Deploys AXIOM in zero-egress mode with a local Ollama embedding model. Runs full semantic security analysis on the codebase without any data leaving the network.

### 5.4 Key Use Cases

**UC-001: Pre-commit Risk Assessment**  
Developer changes a function. AXIOM immediately re-analyzes the local intent graph and shows a diff of how the failure risk landscape changed. Takes < 30 seconds.

**UC-002: Pull Request Blast Radius Report**  
CI/CD plugin posts an AXIOM report to every PR showing: predicted failure paths, semantic similarity to known vulnerability patterns, and auto-generated patch suggestions.

**UC-003: Codebase Health Dashboard**  
Team opens the web dashboard to see: overall codebase health score, top-10 highest-risk functions, recent changes that increased risk, and trend over time.

**UC-004: Security Audit Mode**  
Security engineer runs a full semantic security scan. AXIOM maps all taint flows, privilege escalations, and unsafe deserialization patterns using the GNN intent graph.

**UC-005: Incident Root Cause Analysis**  
After a production incident, engineer inputs the failing function. AXIOM traces back through the intent graph to show the exact chain of semantic dependencies that led to the failure.

---

## 6. System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEVELOPER MACHINE                        │
│                                                                 │
│  ┌──────────────┐    ┌──────────────────────────────────────┐  │
│  │  VS Code Ext │    │           AXIOM CLI / Agent          │  │
│  └──────┬───────┘    └──────────────────┬───────────────────┘  │
│         │                               │                       │
│         └──────────────┬────────────────┘                       │
│                        │                                        │
│            ┌───────────▼────────────┐                           │
│            │    AXIOM Core Engine   │                           │
│            │                        │                           │
│  ┌─────────┴──────┐  ┌──────────────┴──────┐                   │
│  │  AST Parser    │  │   eBPF Tracer        │                   │
│  │  (tree-sitter) │  │   (kernel probes)    │                   │
│  └─────────┬──────┘  └──────────────┬──────┘                   │
│            │                        │                           │
│  ┌─────────▼──────┐  ┌──────────────▼──────┐                   │
│  │  LLM Embedder  │  │  Runtime Event DB    │                   │
│  │  (Ollama/OAI)  │  │  (SQLite/ring buf)   │                   │
│  └─────────┬──────┘  └──────────────┬──────┘                   │
│            │                        │                           │
│            └────────────┬───────────┘                           │
│                         │                                       │
│            ┌────────────▼───────────┐                           │
│            │    GNN Intent Graph    │                           │
│            │  (torch-geometric)     │                           │
│            └────────────┬───────────┘                           │
│                         │                                       │
│            ┌────────────▼───────────┐                           │
│            │  Failure Predictor &   │                           │
│            │  Patch Generator       │                           │
│            └────────────┬───────────┘                           │
│                         │                                       │
└─────────────────────────┼───────────────────────────────────────┘
                          │
              ┌───────────▼───────────┐
              │   FastAPI Backend     │
              │   + WebSocket Server  │
              └───────────┬───────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
  ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼────────┐
  │  PostgreSQL  │ │  ChromaDB   │ │  Web Dashboard│
  │  (metadata)  │ │ (embeddings)│ │  (React/Vite) │
  └──────────────┘ └─────────────┘ └──────────────┘
```

### 6.1 Data Flow Summary

1. Developer saves a file → VS Code extension triggers incremental analysis
2. AST Parser extracts function-level ASTs from changed files
3. LLM Embedder generates 768-dim semantic vectors for each function
4. eBPF Tracer (background daemon) captures syscall events for running processes
5. GNN Engine fuses embeddings + runtime events into the intent graph
6. Failure Predictor runs graph inference to score each function's blast radius
7. Results streamed to VS Code extension via WebSocket
8. All data persisted to PostgreSQL + ChromaDB for historical analysis
9. Web Dashboard reads from FastAPI backend for aggregate views

---

## 7. Component Deep Dives

### 7.1 Multi-Language AST Parser

**Purpose:** Convert source code files into structured Abstract Syntax Trees that can be processed into semantic embeddings.

**Technology:** tree-sitter (Rust-based, extremely fast, incremental re-parsing)

**Supported Languages (Phase 1):**
- Python (`tree-sitter-python`)
- JavaScript (`tree-sitter-javascript`)
- TypeScript (`tree-sitter-typescript`)
- Go (`tree-sitter-go`)
- C++ (`tree-sitter-cpp`)

**Key Responsibilities:**
- Watch file system for changes (using `watchdog` on Python side)
- Parse changed files incrementally (only re-parse modified subtrees)
- Extract function/method/class boundaries with their full source text
- Resolve import/require/use statements to build inter-file dependency graph
- Handle parse errors gracefully (partial AST is better than no AST)

**Output Data Structure:**
```python
@dataclass
class ParsedFunction:
    id: str                    # SHA256(file_path + function_name + start_line)
    file_path: str
    language: str
    function_name: str
    start_line: int
    end_line: int
    source_text: str           # Raw source of the function
    calls: List[str]           # List of function IDs this function calls
    called_by: List[str]       # List of function IDs that call this function
    imports: List[str]         # External dependencies imported in scope
    ast_node: Any              # tree-sitter node object
    last_modified: datetime
    content_hash: str          # SHA256(source_text) for change detection
```

**Implementation Notes:**
- Use Python bindings for tree-sitter (`pip install tree-sitter`)
- Maintain a persistent AST cache on disk (SQLite) to avoid re-parsing unchanged files
- Implement a `FileWatcher` class using `watchdog` that triggers incremental updates
- Cross-file reference resolution: maintain a global symbol table mapping function names to their IDs

**Performance Targets:**
- Initial full parse of 100K LOC: < 10 seconds
- Incremental re-parse on file change: < 500ms
- Memory footprint for 500K LOC codebase: < 512MB

---

### 7.2 LLM Semantic Embedding Engine

**Purpose:** Convert each function's source code into a high-dimensional semantic vector that captures its *meaning*, not just its syntax.

**Technology:** 
- **Local (default):** Ollama with `nomic-embed-text` (768 dimensions, runs on CPU)
- **Cloud (optional):** OpenAI `text-embedding-3-small` (1536 dimensions)
- **Fallback:** sentence-transformers `all-MiniLM-L6-v2` (384 dimensions, fully offline)

**Input Prompt Template:**
```
You are analyzing source code. Describe the semantic purpose and behavior of this function in terms of:
1. What it does (inputs → outputs)
2. What external systems it interacts with (files, network, databases, OS)
3. What invariants it assumes (preconditions)
4. What invariants it guarantees (postconditions)

Function source:
{source_text}

File context: {file_path} ({language})
Called by: {caller_names}
```

**Key Responsibilities:**
- Batch embed functions (batch size 32, configurable)
- Cache embeddings in ChromaDB (keyed by `content_hash`)
- Detect when a function changes and invalidate its embedding
- Support both sync and async embedding (streaming during active dev session)
- Respect rate limits for cloud embedding APIs (exponential backoff)

**Embedding Strategy:**
- For short functions (< 50 lines): embed the full source text
- For long functions (> 50 lines): embed a structured summary (docstring + signature + call sites)
- For classes: embed each method independently, then embed the class-level summary

**Storage:**
- ChromaDB collection: `axiom_function_embeddings`
- Metadata stored alongside embedding: function_id, file_path, language, content_hash, embed_model, embed_time

**Performance Targets:**
- Embedding latency per function (local Ollama): < 200ms
- Embedding latency per function (OpenAI API): < 100ms
- Cache hit rate after initial analysis: > 95%

---

### 7.3 eBPF Runtime Tracer

**Purpose:** Capture ground-truth runtime behaviour of the application by hooking into the Linux kernel — seeing exactly which syscalls each function triggers, which files it opens, which network connections it makes, without modifying the application.

**Technology:**
- BCC (BPF Compiler Collection) Python bindings
- `bpftrace` for rapid prototype-level tracing
- Kernel requirements: Linux 5.4+ (Ubuntu 20.04+, Debian Bullseye+)

**Traced Events:**

| Event Type | Kernel Probe | Data Captured |
|---|---|---|
| File access | `sys_openat`, `sys_read`, `sys_write` | path, flags, pid, timestamp |
| Network | `sys_connect`, `sys_sendto`, `sys_recvfrom` | ip, port, bytes, pid |
| Process spawn | `sys_execve`, `sys_fork` | command, args, parent_pid |
| Memory | `sys_mmap`, `sys_brk` | size, protection flags |
| Privilege | `sys_setuid`, `sys_capset` | new_uid, capabilities |
| IPC | `sys_pipe`, `sys_socket` | fd, type |

**Architecture:**
```
Kernel Space                          User Space
┌────────────────┐                   ┌─────────────────┐
│  eBPF Program  │ ─── perf ring ──▶ │ BCC Python Agent │
│  (C, verified) │      buffer        │                  │
│                │                   │  Event Parser    │
│  kprobe on     │                   │  PID → Function  │
│  sys_openat    │                   │  Resolver        │
│  sys_connect   │                   │  Ring Buffer     │
│  etc.          │                   │  Writer          │
└────────────────┘                   └────────┬─────────┘
                                              │
                                    ┌─────────▼─────────┐
                                    │  Runtime Event DB  │
                                    │  (SQLite, ring     │
                                    │   buffer, 10K ev)  │
                                    └───────────────────-┘
```

**PID → Function Resolution:**
- Use `/proc/{pid}/maps` to map memory addresses to library regions
- Use DWARF debug symbols when available to resolve stack frames to function names
- Fallback to function-level granularity when symbol resolution fails

**Key Data Structure:**
```python
@dataclass
class RuntimeEvent:
    event_type: str          # "file_open", "net_connect", etc.
    pid: int
    tid: int
    timestamp_ns: int        # nanosecond precision
    function_stack: List[str]  # call stack at time of event
    args: Dict[str, Any]     # event-specific arguments
    resolved_function_id: Optional[str]  # linked to ParsedFunction.id
```

**Safety & Performance:**
- eBPF programs are verified by the kernel — they cannot crash the system
- Ring buffer prevents memory exhaustion — oldest events dropped when full
- Sampling mode available for high-frequency syscalls (sample 1-in-N)
- Tracer runs as a background daemon, not in the hot path of analysis

**Requires:**
- Root privileges (or `CAP_BPF` + `CAP_PERFMON` capabilities)
- `linux-headers` package installed
- `bcc-tools` or `bpfcc-tools` package

---

### 7.4 GNN Intent Graph Engine

**Purpose:** Build a graph where each node is a function (with its semantic embedding) and edges represent relationships. Run Graph Neural Network inference to learn patterns and score risk.

**Graph Definition:**

**Nodes:** Each `ParsedFunction` is a node with:
- 768-dimensional semantic embedding vector (from LLM Embedder)
- Scalar runtime features: [syscall_count, file_access_count, net_connect_count, spawn_count, priv_esc_count]
- Metadata: language, LOC, cyclomatic_complexity, last_modified_days

**Edge Types:**
1. `CALLS` — function A directly calls function B (static, from AST)
2. `SHARES_SYSCALL_PATTERN` — A and B trigger similar kernel events at runtime (dynamic, cosine similarity > 0.8)
3. `SEMANTICALLY_SIMILAR` — A and B have embedding cosine similarity > 0.9
4. `TOUCHES_SAME_FILE` — A and B both open/write the same file path at runtime
5. `DATA_FLOWS_TO` — output of A feeds into B (taint analysis approximation)

**GNN Architecture:**
```
Input: Node features (768 + 5 + 3 = 776-dim), edge type
       
Layer 1: GraphSAGE (776 → 512, ReLU, Dropout 0.3)
         [aggregates 1-hop neighborhood]
         
Layer 2: GraphSAGE (512 → 256, ReLU, Dropout 0.3)  
         [aggregates 2-hop neighborhood]
         
Layer 3: GAT (256 → 128, 4 attention heads, concat)
         [attends to important neighbors]
         
Output Head 1 (Node): Linear (128 → 1, Sigmoid)
             → Failure risk score ∈ [0, 1]
             
Output Head 2 (Edge): Linear (256 → 1, Sigmoid)  
             → Failure propagation probability ∈ [0, 1]
             
Output Head 3 (Graph): Mean pooling → Linear (128 → 1)
             → Overall codebase health score ∈ [0, 1]
```

**Training Data:**
- Use synthetic graphs generated from known CVE-affected codebases (open source)
- Label functions as high-risk if they appear in commit messages mentioning CVE/bugfix/security
- Data augmentation: random edge dropout, feature noise injection
- Pre-trained weights bundled with AXIOM (not trained on user code)

**Inference (Prediction) Mode:**
- User code never leaves the machine (only the graph structure + embeddings are processed)
- Pre-trained GNN weights are loaded from `axiom/models/gnn_v1.pt`
- Inference on a 10K-node graph: < 2 seconds on CPU, < 200ms on GPU

**Technology:** PyTorch + torch-geometric

---

### 7.5 Cascading Failure Predictor

**Purpose:** Given a changed or suspect function, compute the predicted blast radius — which other functions are likely to fail if this function misbehaves.

**Algorithm:**

```
INPUT: target_function_id, risk_threshold (default: 0.6)

1. Retrieve target node embedding and current risk score from GNN
2. Run personalized PageRank on the intent graph starting at target node
   - Edge weights = GNN-predicted failure propagation probabilities
   - Teleport probability α = 0.15
   - Iterations: until convergence (ε = 1e-6)
3. Rank all nodes by personalized PageRank score
4. Filter to nodes where score > risk_threshold
5. Trace minimum spanning paths from target to each high-risk node
6. Return: OrderedList[(function_id, risk_score, failure_path)]

OUTPUT: Top-K (default K=10) functions ranked by failure risk, 
        each with the predicted propagation path
```

**Output Format:**
```json
{
  "target": "sha256:abc123",
  "analysis_timestamp": "2026-07-05T10:30:00Z",
  "codebase_health": 0.73,
  "blast_radius": [
    {
      "function_id": "sha256:def456",
      "function_name": "processPayment",
      "file_path": "src/payments/processor.py",
      "risk_score": 0.89,
      "failure_path": ["src/auth/validator.py:validate", "src/payments/processor.py:processPayment"],
      "failure_reason": "Semantic similarity to known SQL injection pattern + shares database file handle"
    }
  ]
}
```

---

### 7.6 Patch Generator & Formal Verifier

**Purpose:** For high-risk functions, auto-generate a candidate patch and verify it preserves the function's stated invariants.

**Patch Generation:**

Uses a code-focused LLM (via Ollama or API) to generate patches guided by:
1. The detected vulnerability pattern (from GNN classification)
2. The function's semantic description (from embeddings)
3. Language-specific safe coding templates
4. Examples from similar CVE fixes in training data

**Prompt Template:**
```
You are a security-focused code reviewer. This function has been flagged with risk pattern: {pattern_name}.

Original function:
{source_text}

Language: {language}
Risk reasons: {risk_reasons}

Generate a minimal, safe patch that addresses the risk while preserving the function's behavior.
Return ONLY the patched function body, no explanation.
```

**Formal Verifier (Lightweight):**

Rather than full formal verification (which is computationally expensive), AXIOM uses **invariant checking**:

1. Extract pre/postcondition comments if present (Hoare-style)
2. Generate simple property-based tests using `hypothesis` (Python) or `fast-check` (TypeScript)
3. Run the generated tests against both original and patched function
4. Patch is accepted only if: all original tests pass + all new property tests pass + risk score decreases

**Supported Patch Patterns:**
- SQL injection → parameterized queries
- Path traversal → path sanitization
- Deserialization → safe deserializer
- Command injection → subprocess with shell=False
- Hardcoded credentials → environment variable references
- Unchecked null → null guards
- Race condition → mutex/lock insertion

---

### 7.7 FastAPI Backend

**Purpose:** The central API server that coordinates all components and exposes data to the VS Code extension, web dashboard, and CI/CD plugin.

**Framework:** FastAPI (Python 3.11+)  
**ASGI Server:** Uvicorn with Gunicorn for production  
**Process Model:** Single master + multiple workers (4 workers default)

**Application Structure:**
```
axiom/
├── main.py                 # FastAPI app, CORS, startup hooks
├── api/
│   ├── analysis.py         # /api/v1/analyze/* endpoints
│   ├── graph.py            # /api/v1/graph/* endpoints
│   ├── patches.py          # /api/v1/patches/* endpoints
│   ├── projects.py         # /api/v1/projects/* endpoints
│   ├── health.py           # /health, /metrics endpoints
│   └── auth.py             # /auth/login, /auth/callback, /auth/refresh
├── services/
│   ├── ast_service.py      # Wraps AST parser
│   ├── embed_service.py    # Wraps LLM embedder
│   ├── ebpf_service.py     # Wraps eBPF tracer daemon
│   ├── gnn_service.py      # Wraps GNN engine
│   ├── predict_service.py  # Wraps failure predictor
│   └── patch_service.py    # Wraps patch generator
├── models/
│   ├── db_models.py        # SQLAlchemy models
│   └── api_models.py       # Pydantic request/response schemas
├── core/
│   ├── config.py           # Settings (pydantic-settings)
│   ├── database.py         # DB session management
│   ├── security.py         # JWT, OAuth helpers
│   └── websocket.py        # WebSocket connection manager
└── workers/
    ├── analysis_worker.py  # Background analysis tasks (Celery or asyncio)
    └── ebpf_worker.py      # eBPF daemon manager
```

**Startup Sequence:**
1. Load config from `.env`
2. Initialize PostgreSQL connection pool
3. Initialize ChromaDB client
4. Load GNN model weights into memory
5. Start eBPF daemon (if running on Linux with required capabilities)
6. Register all routers
7. Start background heartbeat + analysis queue

---

### 7.8 WebSocket Real-Time Server

**Purpose:** Push analysis results, risk score updates, and eBPF events to connected clients (VS Code extension, web dashboard) in real time.

**Technology:** FastAPI WebSocket (built-in), asyncio-based connection manager

**WebSocket Endpoint:** `ws://localhost:8000/ws/{project_id}?token={jwt}`

**Message Types (Server → Client):**

```typescript
// Analysis started
{ "type": "analysis_started", "function_id": "sha256:abc", "timestamp": 1234567890 }

// Partial result (streaming)
{ "type": "risk_update", "function_id": "sha256:abc", "risk_score": 0.73, "partial": true }

// Full blast radius result
{ "type": "blast_radius", "target": "sha256:abc", "results": [...], "partial": false }

// eBPF event (real-time)
{ "type": "runtime_event", "event_type": "file_open", "function_id": "sha256:def", "path": "/etc/passwd" }

// Codebase health update
{ "type": "health_update", "score": 0.68, "delta": -0.05, "trending": "down" }

// Patch ready
{ "type": "patch_ready", "function_id": "sha256:abc", "patch_id": "patch-001", "confidence": 0.82 }
```

**Message Types (Client → Server):**
```typescript
// Subscribe to specific function updates
{ "type": "subscribe_function", "function_id": "sha256:abc" }

// Request analysis of specific file
{ "type": "analyze_file", "file_path": "/workspace/src/auth/validator.py" }

// Accept a patch
{ "type": "accept_patch", "patch_id": "patch-001" }
```

**Connection Manager:**
- Maintains a dictionary of `{project_id: Set[WebSocket]}`
- Broadcasts to all subscribers of a project on any update
- Handles disconnects gracefully with cleanup
- Heartbeat ping every 30 seconds

---

### 7.9 VS Code Extension

**Purpose:** Inline risk scoring and failure prediction directly in the developer's editor, zero workflow disruption.

**Technology:** TypeScript, VS Code Extension API

**Extension ID:** `axiom.axiom-intelligence`

**Activation Events:**
- `onStartupFinished` (activate on VS Code start)
- `onLanguage:python`, `onLanguage:javascript`, `onLanguage:typescript`, `onLanguage:go`, `onLanguage:cpp`
- `workspaceContains:**/.axiom` (detect AXIOM projects)

**Features:**

**1. Inline Risk Gutter Icons**
- A colored circle in the editor gutter for each function
- 🟢 Low risk (0–0.3), 🟡 Medium (0.3–0.6), 🔴 High (0.6–1.0)
- Click to expand: shows blast radius, failure reason, suggested patch

**2. Hover Cards**
- Hover over any function name → shows risk score, top-3 affected downstream functions
- Includes one-click "Show full analysis" and "View patch" buttons

**3. Status Bar Item**
- Bottom-right: "AXIOM: 🟡 Codebase 0.73" — click to open dashboard
- Animates during active analysis

**4. Diagnostics Integration**
- High-risk functions appear in VS Code's Problems panel
- Severity: Error (>0.8), Warning (>0.5), Info (>0.3)

**5. Commands (Command Palette):**
- `AXIOM: Analyze Current File`
- `AXIOM: Analyze Workspace`
- `AXIOM: Show Blast Radius for Function`
- `AXIOM: Accept Patch for Function`
- `AXIOM: Open Dashboard`
- `AXIOM: Toggle eBPF Tracing`
- `AXIOM: Show Intent Graph`

**6. Settings (`settings.json`):**
```json
{
  "axiom.serverUrl": "http://localhost:8000",
  "axiom.embeddingProvider": "ollama",
  "axiom.ollamaModel": "nomic-embed-text",
  "axiom.riskThreshold.warning": 0.5,
  "axiom.riskThreshold.error": 0.8,
  "axiom.enableEbpf": true,
  "axiom.autoAnalyzeOnSave": true,
  "axiom.showInlineDecorations": true
}
```

**Extension Directory Structure:**
```
vscode-extension/
├── package.json
├── tsconfig.json
├── src/
│   ├── extension.ts          # Activation entry point
│   ├── axiomClient.ts        # HTTP + WebSocket client
│   ├── providers/
│   │   ├── GutterDecorator.ts
│   │   ├── HoverProvider.ts
│   │   └── DiagnosticsProvider.ts
│   ├── views/
│   │   ├── BlastRadiusPanel.ts   # Webview panel
│   │   └── GraphPanel.ts         # Intent graph webview
│   └── commands/
│       └── index.ts
└── media/
    ├── icons/
    └── webview/              # Bundled React app for webview panels
```

---

### 7.10 Web Dashboard

**Purpose:** A full-featured web interface for aggregate codebase health monitoring, graph exploration, and team-level analysis.

**Technology:** React 18 + TypeScript, Vite bundler, Tailwind CSS, shadcn/ui components

**Pages:**

**1. Dashboard (Home)**
- Codebase health score gauge (animated)
- Risk trend chart (last 30 days)
- Top-10 highest-risk functions list
- Recent changes heat map
- Active eBPF alerts feed

**2. Intent Graph Explorer**
- Interactive force-directed graph visualization using D3.js or Sigma.js
- Node color = risk score (green → red)
- Node size = number of callers (betweenness centrality)
- Edge thickness = failure propagation probability
- Click node → highlight blast radius
- Filter by language, risk level, file path
- Export graph as PNG or JSON

**3. Function Detail View**
- Full source code with risk annotations
- Side-by-side diff with suggested patch
- Runtime event timeline (eBPF events for this function)
- Similar functions by semantic similarity
- Historical risk trend

**4. CI/CD Reports**
- List of all PR analysis reports
- Filter by branch, author, date
- Drill down into per-commit risk delta

**5. Settings**
- Configure embedding provider (Ollama vs OpenAI)
- Manage API keys
- RBAC: manage team members and permissions
- Notification settings (email, Slack webhook)

**API Integration:**
- All data from FastAPI REST endpoints
- Real-time updates via WebSocket
- JWT stored in `localStorage` (with XSS mitigation via Content-Security-Policy)

---

### 7.11 CI/CD Plugin

**Purpose:** Block or warn on high-risk pull requests before they merge, without any human having to manually run AXIOM.

**GitHub Actions Integration (`axiom-action`):**

```yaml
# .github/workflows/axiom.yml
name: AXIOM Risk Analysis
on: [pull_request]

jobs:
  axiom-analysis:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history for diff analysis
          
      - uses: PRATHVI9607/axiom-action@v1
        with:
          axiom-server: ${{ secrets.AXIOM_SERVER_URL }}
          axiom-token: ${{ secrets.AXIOM_API_TOKEN }}
          risk-threshold: 0.7
          block-on-high-risk: true
          post-pr-comment: true
          
      - name: Upload AXIOM Report
        uses: actions/upload-artifact@v4
        with:
          name: axiom-report
          path: axiom-report.json
```

**PR Comment Template:**
```markdown
## 🔬 AXIOM Code Intelligence Report

**Overall Risk Delta:** +0.12 (↑ increased risk)
**Functions Changed:** 7
**High-Risk Functions:** 2
**Predicted Blast Radius:** 14 functions

### High-Risk Functions

| Function | File | Risk Score | Key Concern |
|----------|------|------------|-------------|
| `validate_token()` | `auth/validator.py:42` | 🔴 0.87 | Semantic match to JWT bypass pattern |
| `process_upload()` | `api/files.py:118` | 🔴 0.81 | Unchecked file path + syscall: openat("/etc") |

### Suggested Patches Available
[View patches →](https://axiom-server/patches/pr-1234)

---
*Analysis by [AXIOM](https://github.com/PRATHVI9607/AXIOM) — Semantic Runtime Code Intelligence*
```

**GitLab CI Integration:** Similar to GitHub Actions, exposed as a `.gitlab-ci.yml` template.

---

### 7.12 Database Layer

**PostgreSQL (Structured Data):**

Used for: projects, users, sessions, analysis results metadata, patches, CI/CD reports

Connection: SQLAlchemy async with `asyncpg` driver  
Migrations: Alembic

**ChromaDB (Vector Embeddings):**

Used for: function semantic embeddings, similarity search, clustering

Collections:
- `axiom_embeddings`: function embeddings (one per function, keyed by `function_id`)
- `axiom_patterns`: known vulnerability pattern embeddings (loaded from pre-trained dataset)

Similarity search: cosine distance, top-K retrieval for "find semantically similar vulnerable functions"

**SQLite (Local Cache):**

Used for: AST parse cache, eBPF ring buffer persistence, offline mode  
Location: `~/.axiom/cache.db`  
Max size: 1GB (LRU eviction)

---

### 7.13 Authentication & Authorization

**Auth Flow:**
1. User visits web dashboard → redirects to GitHub OAuth
2. GitHub returns authorization code → backend exchanges for access token
3. Backend fetches GitHub user info → creates or retrieves user record
4. Backend issues AXIOM JWT (RS256, 24-hour expiry, 7-day refresh)
5. JWT stored in HttpOnly cookie (web dashboard) or extension SecretStorage (VS Code)

**JWT Payload:**
```json
{
  "sub": "github:12345678",
  "username": "PRATHVI9607",
  "email": "rakshaksujith@gmail.com",
  "roles": ["admin"],
  "project_ids": ["proj-abc", "proj-def"],
  "iat": 1234567890,
  "exp": 1234654290
}
```

**RBAC Roles:**
- `admin`: Full access, manage users, view all projects
- `developer`: Analyze code, view results, accept patches in own projects
- `viewer`: Read-only access to dashboards and reports
- `ci`: API-key only, restricted to analysis endpoints (for CI/CD bots)

**API Key Auth (for CI/CD):**
- SHA-256 hashed in DB
- Scoped to specific projects
- Never expire (rotated manually via dashboard)
- Rate limited: 100 req/min per key

---

### 7.14 Air-Gapped Mode

**Purpose:** Full functionality with zero external network calls — for security-sensitive or classified environments.

**What changes in air-gapped mode:**
- LLM Embedder uses local Ollama exclusively (no OpenAI API calls)
- OAuth disabled — local password auth only (bcrypt)
- ChromaDB runs fully local (it always does, no change needed)
- No telemetry, no update checks, no CDN assets
- Pre-trained GNN weights bundled in the Docker image
- VS Code extension served from local AXIOM server (not VS Code Marketplace)

**Activation:**
```bash
# In .env
AXIOM_AIR_GAPPED=true
AXIOM_EMBED_PROVIDER=ollama
AXIOM_OLLAMA_URL=http://localhost:11434
AXIOM_AUTH_PROVIDER=local
```

**Air-gapped Docker image includes:**
- Ollama with `nomic-embed-text` model pre-pulled
- All Python dependencies vendored
- Pre-trained GNN weights
- Full Postgres + ChromaDB stack

---

## 8. API Specifications

### Base URL
`http://localhost:8000/api/v1`

### Authentication
All endpoints (except `/auth/*` and `/health`) require:
`Authorization: Bearer {jwt_token}`

---

### 8.1 Analysis Endpoints

**POST `/analyze/file`**  
Trigger analysis of a specific file.

Request:
```json
{
  "project_id": "proj-abc123",
  "file_path": "/workspace/src/auth/validator.py",
  "force_reembed": false
}
```
Response:
```json
{
  "job_id": "job-xyz789",
  "status": "queued",
  "estimated_seconds": 15
}
```

**POST `/analyze/function`**  
Analyze a specific function and return its blast radius.

Request:
```json
{
  "project_id": "proj-abc123",
  "function_id": "sha256:abc123def456"
}
```
Response:
```json
{
  "function_id": "sha256:abc123def456",
  "function_name": "validate_token",
  "risk_score": 0.87,
  "blast_radius": [
    {
      "function_id": "sha256:def456",
      "function_name": "process_request",
      "risk_score": 0.73,
      "failure_path": ["validate_token", "authenticate_user", "process_request"],
      "failure_reason": "JWT bypass propagates to all authenticated routes"
    }
  ],
  "runtime_events": [
    {"type": "file_open", "path": "/etc/ssl/certs", "count": 47}
  ],
  "analysis_time_ms": 280
}
```

**GET `/analyze/status/{job_id}`**  
Poll job status.

Response:
```json
{
  "job_id": "job-xyz789",
  "status": "complete",
  "progress": 1.0,
  "result_url": "/api/v1/analyze/results/job-xyz789"
}
```

**GET `/analyze/history/{project_id}`**  
Get analysis history for a project.

Query params: `?limit=20&offset=0&since=2026-07-01`

---

### 8.2 Graph Endpoints

**GET `/graph/{project_id}`**  
Get the full intent graph (paginated, for large codebases).

Query params: `?page=1&page_size=1000&risk_min=0.0&risk_max=1.0`

Response:
```json
{
  "nodes": [
    {
      "id": "sha256:abc123",
      "label": "validate_token",
      "risk_score": 0.87,
      "language": "python",
      "file_path": "src/auth/validator.py",
      "x": 0.45, "y": 0.32
    }
  ],
  "edges": [
    {
      "source": "sha256:abc123",
      "target": "sha256:def456",
      "type": "CALLS",
      "weight": 0.73
    }
  ],
  "total_nodes": 2847,
  "page": 1
}
```

**GET `/graph/{project_id}/health`**  
Get codebase health score and trend.

Response:
```json
{
  "current_score": 0.73,
  "trend_7d": -0.05,
  "trend_30d": +0.12,
  "high_risk_count": 23,
  "medium_risk_count": 147,
  "low_risk_count": 2677
}
```

---

### 8.3 Patch Endpoints

**GET `/patches/{project_id}`**  
List available patches.

**GET `/patches/{project_id}/{patch_id}`**  
Get a specific patch with diff.

Response:
```json
{
  "patch_id": "patch-001",
  "function_id": "sha256:abc123",
  "pattern": "sql_injection",
  "confidence": 0.82,
  "original": "def get_user(username):\n    query = f'SELECT * FROM users WHERE username={username}'\n    return db.execute(query)",
  "patched": "def get_user(username: str):\n    query = 'SELECT * FROM users WHERE username = ?'\n    return db.execute(query, (username,))",
  "verified": true,
  "test_results": {"passed": 12, "failed": 0}
}
```

**POST `/patches/{project_id}/{patch_id}/accept`**  
Apply a patch to the actual file.

**POST `/patches/{project_id}/{patch_id}/reject`**  
Mark a patch as rejected (feedback for model improvement).

---

### 8.4 Project Endpoints

**POST `/projects`** — Create project  
**GET `/projects`** — List projects  
**GET `/projects/{project_id}`** — Get project details  
**DELETE `/projects/{project_id}`** — Delete project  
**POST `/projects/{project_id}/rescan`** — Full rescan from scratch  

---

### 8.5 Auth Endpoints

**GET `/auth/login`** — Redirect to GitHub OAuth  
**GET `/auth/callback`** — OAuth callback, returns JWT  
**POST `/auth/refresh`** — Refresh JWT  
**POST `/auth/logout`** — Invalidate session  
**POST `/auth/apikeys`** — Create API key for CI/CD  

---

## 9. Database Schema

### PostgreSQL Schema

```sql
-- Projects
CREATE TABLE projects (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name        TEXT NOT NULL,
    root_path   TEXT NOT NULL,
    languages   TEXT[] NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    owner_id    UUID REFERENCES users(id) ON DELETE CASCADE,
    settings    JSONB DEFAULT '{}'
);

-- Users
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    github_id       TEXT UNIQUE,
    username        TEXT NOT NULL,
    email           TEXT UNIQUE NOT NULL,
    password_hash   TEXT,              -- NULL for OAuth users
    role            TEXT DEFAULT 'developer',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    last_login      TIMESTAMPTZ
);

-- Functions (mirror of parsed AST, for query purposes)
CREATE TABLE functions (
    id              TEXT PRIMARY KEY,  -- SHA256 hash
    project_id      UUID REFERENCES projects(id) ON DELETE CASCADE,
    file_path       TEXT NOT NULL,
    function_name   TEXT NOT NULL,
    language        TEXT NOT NULL,
    start_line      INT NOT NULL,
    end_line        INT NOT NULL,
    content_hash    TEXT NOT NULL,
    last_analyzed   TIMESTAMPTZ,
    current_risk    FLOAT DEFAULT 0.0,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_functions_project ON functions(project_id);
CREATE INDEX idx_functions_risk ON functions(current_risk DESC);

-- Analysis Jobs
CREATE TABLE analysis_jobs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  UUID REFERENCES projects(id),
    type        TEXT NOT NULL,  -- 'file', 'function', 'full'
    status      TEXT DEFAULT 'queued',  -- queued, running, complete, failed
    target      TEXT,           -- file_path or function_id
    result      JSONB,
    error       TEXT,
    started_at  TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Patches
CREATE TABLE patches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    function_id     TEXT REFERENCES functions(id),
    project_id      UUID REFERENCES projects(id),
    pattern         TEXT NOT NULL,
    original_code   TEXT NOT NULL,
    patched_code    TEXT NOT NULL,
    confidence      FLOAT NOT NULL,
    verified        BOOLEAN DEFAULT FALSE,
    test_results    JSONB,
    status          TEXT DEFAULT 'pending',  -- pending, accepted, rejected
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Runtime Events (summary, not raw)
CREATE TABLE runtime_event_summaries (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    function_id     TEXT REFERENCES functions(id),
    project_id      UUID REFERENCES projects(id),
    session_start   TIMESTAMPTZ NOT NULL,
    session_end     TIMESTAMPTZ NOT NULL,
    file_opens      INT DEFAULT 0,
    net_connects    INT DEFAULT 0,
    proc_spawns     INT DEFAULT 0,
    priv_changes    INT DEFAULT 0,
    top_paths       TEXT[],  -- top-5 file paths accessed
    top_hosts       TEXT[],  -- top-5 network hosts
    raw_sample      JSONB    -- small sample of raw events
);

-- CI Reports
CREATE TABLE ci_reports (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      UUID REFERENCES projects(id),
    pr_number       INT,
    branch          TEXT,
    commit_sha      TEXT NOT NULL,
    overall_delta   FLOAT,
    high_risk_count INT,
    report_json     JSONB NOT NULL,
    blocked         BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- API Keys
CREATE TABLE api_keys (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    project_id      UUID REFERENCES projects(id),
    key_hash        TEXT UNIQUE NOT NULL,  -- SHA-256
    name            TEXT NOT NULL,
    last_used       TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 10. Security Architecture

### 10.1 Threat Model

| Threat | Vector | Mitigation |
|---|---|---|
| Code exfiltration | Embedding API calls | Air-gapped mode, local Ollama, no code in prompts (only embeddings) |
| JWT forgery | RS256 private key compromise | Key stored in environment, rotated every 90 days |
| SQL injection | API inputs | SQLAlchemy parameterized queries, Pydantic validation |
| Path traversal | File path inputs | `pathlib.resolve()` + project root validation |
| eBPF privilege abuse | CAP_BPF escalation | Drop capabilities after eBPF program load, seccomp filter on worker |
| Dependency confusion | pip/npm supply chain | Lock files, hash verification, private mirror in enterprise mode |
| XSS in dashboard | Reflected inputs | CSP headers, React auto-escaping, HttpOnly cookies |
| CSRF | Cookie-based auth | SameSite=Strict, CSRF token for mutations |

### 10.2 eBPF Security

eBPF programs are **verified by the Linux kernel** before loading — they cannot:
- Access arbitrary kernel memory
- Execute infinite loops
- Call unsafe kernel functions

AXIOM's eBPF programs are loaded with minimal capabilities:
```bash
# Only these capabilities needed:
CAP_BPF         # Load eBPF programs
CAP_PERFMON     # Access perf events
CAP_SYS_PTRACE  # Read /proc/{pid}/maps for symbol resolution
```

### 10.3 Data Privacy

- **Code never sent to cloud services by default** — only embedding vectors (which are not reversible to source code with current models)
- Users explicitly opt-in to cloud embedding with a clear warning
- All data stored locally by default (PostgreSQL + ChromaDB on localhost)
- In enterprise/SaaS mode: data encrypted at rest (AES-256) and in transit (TLS 1.3)

---

## 11. Performance Requirements & SLAs

| Operation | P50 | P95 | P99 | Max |
|---|---|---|---|---|
| Incremental file analysis (on save) | 5s | 20s | 30s | 60s |
| Full workspace initial scan (100K LOC) | 2min | 5min | 8min | 15min |
| Blast radius prediction (single function) | 200ms | 500ms | 1s | 3s |
| Patch generation | 3s | 8s | 15s | 30s |
| API response (non-analysis) | 20ms | 80ms | 150ms | 500ms |
| WebSocket event delivery | 10ms | 50ms | 100ms | 500ms |
| GNN inference (10K node graph) | 500ms | 1.5s | 2s | 5s |

**System Requirements (Minimum):**
- CPU: 4-core (Intel/AMD x86-64 or Apple Silicon)
- RAM: 8GB (16GB recommended for large codebases)
- Disk: 10GB free (for models, cache, databases)
- OS: Ubuntu 20.04+, Debian 11+, macOS 12+ (eBPF only on Linux)
- Python: 3.11+
- Node.js: 18+

---

## 12. Testing Strategy

### 12.1 Unit Tests (pytest)

**Target coverage: 80%**

Key test modules:
- `tests/test_ast_parser.py`: Parse each language, edge cases (empty file, syntax errors, nested functions)
- `tests/test_embedder.py`: Mock Ollama API, test batching, cache hits/misses
- `tests/test_gnn.py`: Graph construction, inference output shapes, edge case (isolated nodes)
- `tests/test_predictor.py`: PageRank convergence, risk score bounds [0,1]
- `tests/test_patch_gen.py`: SQL injection pattern detection, patch correctness
- `tests/test_api.py`: All endpoints, auth flows, error responses (FastAPI TestClient)
- `tests/test_auth.py`: JWT encode/decode, expiry, OAuth flow mock

### 12.2 Integration Tests

- End-to-end: parse a real Python file → embed → build graph → predict → check output shape
- WebSocket: connect client, trigger analysis, verify events received in order
- Database: write analysis result → query → verify round-trip
- ChromaDB: insert embedding → similarity search → verify top result

### 12.3 E2E Tests (Playwright for Dashboard)

- Login flow (mocked OAuth)
- Dashboard loads with health score
- Click on function → blast radius panel opens
- Accept patch → file updated on disk

### 12.4 Property-Based Tests (Hypothesis)

- Risk scores always in [0.0, 1.0]
- Blast radius list always sorted by descending risk
- GNN output dimension always matches expected shape
- API never returns 500 for valid input

### 12.5 eBPF Tests

- Run against known test program that opens `/tmp/test.txt`
- Verify event captured with correct path and PID
- Verify function resolution maps to correct function name

### 12.6 CI Pipeline

```yaml
# .github/workflows/test.yml
jobs:
  test:
    runs-on: ubuntu-22.04
    services:
      postgres:
        image: postgres:16
      chromadb:
        image: chromadb/chroma:latest
    steps:
      - pytest --cov=axiom --cov-report=xml -v
      - playwright test
      - Upload coverage to Codecov
```

---

## 13. Deployment Architecture

### 13.1 Local Development (Docker Compose)

```yaml
# docker-compose.yml
version: '3.9'
services:
  axiom-backend:
    build: .
    ports: ["8000:8000"]
    environment:
      DATABASE_URL: postgresql://axiom:axiom@postgres:5432/axiom
      CHROMA_URL: http://chromadb:8001
      OLLAMA_URL: http://ollama:11434
    volumes:
      - ./workspace:/workspace
    depends_on: [postgres, chromadb, ollama]
    privileged: true  # Required for eBPF

  axiom-frontend:
    build: ./dashboard
    ports: ["3000:3000"]
    environment:
      VITE_API_URL: http://localhost:8000

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: axiom
      POSTGRES_USER: axiom
      POSTGRES_PASSWORD: axiom
    volumes: [pgdata:/var/lib/postgresql/data]

  chromadb:
    image: chromadb/chroma:0.5.0
    ports: ["8001:8001"]
    volumes: [chromadata:/chroma/chroma]

  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes: [ollamadata:/root/.ollama]
    entrypoint: ["/bin/sh", "-c", "ollama serve & sleep 5 && ollama pull nomic-embed-text && tail -f /dev/null"]

volumes: [pgdata, chromadata, ollamadata]
```

### 13.2 Production Kubernetes (Helm Chart)

Key resources:
- `Deployment/axiom-backend`: 2 replicas, resource limits (2CPU, 4Gi RAM)
- `Deployment/axiom-frontend`: 2 replicas, resource limits (500m, 512Mi)
- `StatefulSet/postgres`: 1 replica, PVC 50Gi
- `StatefulSet/chromadb`: 1 replica, PVC 20Gi
- `DaemonSet/axiom-ebpf-agent`: 1 per node (hostPID: true, privileged: true, CAP_BPF)
- `Ingress`: nginx ingress with TLS
- `HorizontalPodAutoscaler`: scale backend 2–10 replicas on CPU > 70%

### 13.3 Directory Structure (Full Project)

```
AXIOM/
├── axiom/                      # Python backend
│   ├── main.py
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── core/
│   ├── workers/
│   └── models/gnn_v1.pt        # Pre-trained GNN weights
├── vscode-extension/           # TypeScript VS Code extension
│   ├── src/
│   └── package.json
├── dashboard/                  # React web dashboard
│   ├── src/
│   └── package.json
├── ebpf/                       # BPF programs (C)
│   ├── syscall_tracer.bpf.c
│   └── Makefile
├── k8s/                        # Kubernetes manifests
│   └── helm/axiom/
├── tests/                      # All tests
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── PRD.md
├── CLAUDE.md
└── README.md
```

---

## 14. Phased Roadmap

### Phase 1 — MVP (Weeks 1–8)

**Week 1–2: Core Parser & Embedder**
- [ ] tree-sitter integration for Python + TypeScript
- [ ] Ollama embedding integration
- [ ] ChromaDB storage
- [ ] SQLite AST cache

**Week 3–4: eBPF Tracer + GNN**
- [ ] BCC Python eBPF program for syscall tracing
- [ ] GNN graph construction (torch-geometric)
- [ ] Pre-training on CVE dataset
- [ ] Failure prediction algorithm

**Week 5–6: Backend + WebSocket**
- [ ] FastAPI application scaffold
- [ ] All API endpoints
- [ ] WebSocket server
- [ ] PostgreSQL schema + Alembic migrations
- [ ] GitHub OAuth

**Week 7: VS Code Extension**
- [ ] Extension scaffold
- [ ] Gutter decorations
- [ ] Hover cards
- [ ] Command palette commands
- [ ] WebSocket client

**Week 8: Dashboard + Docker**
- [ ] React dashboard scaffold
- [ ] Health score page
- [ ] Intent graph visualization
- [ ] Docker Compose deployment
- [ ] README + quick start guide

### Phase 2 — Production (Weeks 9–16)

- [ ] Go + C++ + Java language support
- [ ] Patch generator + formal verifier
- [ ] GitHub Actions CI/CD plugin
- [ ] Kubernetes Helm chart
- [ ] Air-gapped deployment mode
- [ ] RBAC multi-user support
- [ ] Comprehensive test suite (>80% coverage)
- [ ] Performance optimization (incremental GNN update)

### Phase 3 — Scale (Post Week 16)

- [ ] SaaS cloud offering
- [ ] Rust language support
- [ ] ONNX model export + edge deployment
- [ ] Collaborative real-time sessions
- [ ] IDE plugins for JetBrains + Neovim
- [ ] LLM fine-tuning on accepted patches (federated, privacy-preserving)

---

## 15. Risk Assessment & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| eBPF not available (macOS, older kernel) | High | Medium | Graceful degradation: disable runtime features, static-only mode |
| LLM embedding quality insufficient | Medium | High | Fallback to TF-IDF + code2vec if embeddings don't cluster meaningfully |
| GNN overfits to training CVE dataset | Medium | High | Cross-validate on held-out CVE dataset, regularization, diverse training data |
| High false positive rate alienates users | High | High | Conservative thresholds by default, user feedback loop to improve model |
| Performance too slow for large codebases | Medium | Medium | Incremental analysis, background processing, async everything |
| ChromaDB memory limits | Low | Medium | Embedding quantization (INT8), regular pruning of stale embeddings |
| eBPF symbol resolution fails | Medium | Low | Fall back to PID-level attribution if DWARF symbols unavailable |
| GitHub OAuth scope changes | Low | Medium | Fallback to local password auth always available |

---

## 16. Appendix

### 16.1 Glossary

| Term | Definition |
|---|---|
| AST | Abstract Syntax Tree — tree representation of source code structure |
| eBPF | Extended Berkeley Packet Filter — Linux kernel technology for safe in-kernel programs |
| GNN | Graph Neural Network — neural network that operates on graph-structured data |
| Intent Graph | AXIOM's graph combining semantic + runtime data to model code behavior |
| Blast Radius | Set of functions predicted to fail if a target function misbehaves |
| Embedding | High-dimensional vector representing the semantic meaning of a function |
| Invariant | A property of code that must always hold (precondition or postcondition) |

### 16.2 Key Dependencies

| Package | Version | Purpose |
|---|---|---|
| `fastapi` | 0.111+ | Web framework |
| `tree-sitter` | 0.22+ | Multi-language AST parsing |
| `torch` | 2.3+ | PyTorch for GNN |
| `torch-geometric` | 2.5+ | GNN layers (GraphSAGE, GAT) |
| `chromadb` | 0.5+ | Vector embedding storage |
| `sqlalchemy` | 2.0+ | ORM for PostgreSQL |
| `bcc` | 0.30+ | eBPF Python bindings |
| `sentence-transformers` | 3.0+ | Fallback embeddings |
| `hypothesis` | 6.0+ | Property-based testing |
| `alembic` | 1.13+ | Database migrations |
| `pydantic-settings` | 2.0+ | Config management |

### 16.3 Environment Variables Reference

```bash
# Database
DATABASE_URL=postgresql+asyncpg://axiom:axiom@localhost:5432/axiom

# ChromaDB
CHROMA_URL=http://localhost:8001
CHROMA_AUTH_TOKEN=                  # Optional, for secured ChromaDB

# Embedding
AXIOM_EMBED_PROVIDER=ollama         # ollama | openai | local
AXIOM_OLLAMA_URL=http://localhost:11434
AXIOM_OLLAMA_MODEL=nomic-embed-text
OPENAI_API_KEY=                     # Only if EMBED_PROVIDER=openai

# Auth
AXIOM_JWT_PRIVATE_KEY=              # RS256 private key (PEM)
AXIOM_JWT_PUBLIC_KEY=               # RS256 public key (PEM)
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
AXIOM_AUTH_PROVIDER=github          # github | local

# Deployment
AXIOM_AIR_GAPPED=false
AXIOM_BASE_URL=http://localhost:8000
AXIOM_FRONTEND_URL=http://localhost:3000
AXIOM_LOG_LEVEL=INFO

# eBPF
AXIOM_EBPF_ENABLED=true
AXIOM_EBPF_RING_BUFFER_SIZE=10000  # Events before oldest dropped
AXIOM_EBPF_SAMPLE_RATE=1           # 1 = every event, 10 = 1-in-10
```

---

*End of AXIOM PRD v1.0.0*  
*Last updated: July 2026*  
*Author: Rakshak S — github.com/PRATHVI9607*
