"""Analysis orchestrator: AST → embed → GNN graph → blast-radius prediction.

Runs off the request path (Critical Rule #3): heavy CPU work is dispatched to a
thread pool and results are broadcast over WebSocket. This is the glue that turns
the individual services into an end-to-end analysis.
"""
from __future__ import annotations

import asyncio
import logging
import time
from pathlib import Path
from typing import Any

from axiom.core.websocket import manager
from axiom.services.ast_service import ParsedFunction, detect_language, get_parser
from axiom.services.ebpf_service import get_tracer
from axiom.services.embed_service import get_embedder
from axiom.services.gnn_service import GNNEngine, IntentGraph, get_gnn
from axiom.services.predict_service import get_predictor
from axiom.services.vector_store import get_vector_store

logger = logging.getLogger(__name__)


class AnalysisWorker:
    """Coordinates a full analysis pass for a file or workspace."""

    def __init__(self) -> None:
        self.parser = get_parser()
        self.embedder = get_embedder()
        self.gnn: GNNEngine = get_gnn()
        self.predictor = get_predictor()
        self.store = get_vector_store()
        self.tracer = get_tracer()
        # Most-recent intent graph per project (in-memory working set).
        self._graphs: dict[str, IntentGraph] = {}

    def get_graph(self, project_id: str) -> IntentGraph | None:
        return self._graphs.get(project_id)

    def cache_graph(self, project_id: str, graph: IntentGraph) -> None:
        self._graphs[project_id] = graph

    async def analyze_paths(
        self, project_id: str, paths: list[str]
    ) -> tuple[IntentGraph, list[ParsedFunction]]:
        """Parse, embed, fuse runtime data, and score a set of source paths."""
        start = time.perf_counter()
        loop = asyncio.get_running_loop()

        # 1) Parse (CPU-bound → thread pool).
        functions: list[ParsedFunction] = []
        for path in paths:
            parsed = await loop.run_in_executor(None, self.parser.parse_file, path)
            functions.extend(parsed)
        logger.info("Parsed %d functions from %d paths", len(functions), len(paths))

        # 2) Embed each function; only vectors leave the machine (Critical Rule #1).
        for fn in functions:
            prompt = self.embedder.build_prompt(fn.source_text, fn.file_path, fn.language, fn.called_by)
            vector = await self.embedder.embed_text(prompt)
            await loop.run_in_executor(
                None, self.store.upsert, fn.id, vector, {**fn.to_dict(), "project_id": project_id}
            )

        # 3) Fuse live runtime features from the eBPF tracer (empty if daemon down).
        runtime_by_comm = await self.tracer.summarize()

        # 4) Build the intent graph and score risk (CPU-bound → thread pool).
        graph = await loop.run_in_executor(
            None, self.gnn.build_graph, functions, self._map_runtime(functions, runtime_by_comm)
        )

        self.cache_graph(project_id, graph)
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        await manager.broadcast(
            project_id,
            {
                "type": "health_update",
                "score": self.gnn.codebase_health(graph),
                "functions": len(functions),
                "elapsed_ms": elapsed_ms,
            },
        )
        return graph, functions

    async def analyze_function(
        self, project_id: str, graph: IntentGraph, function_id: str
    ) -> dict[str, Any]:
        """Compute the blast radius for one function and broadcast it."""
        start = time.perf_counter()
        blast = self.predictor.predict_blast_radius(graph, function_id)
        node = graph.nodes.get(function_id)
        result = {
            "function_id": function_id,
            "function_name": node.label if node else "unknown",
            "risk_score": node.risk_score if node else 0.0,
            "blast_radius": blast,
            "analysis_time_ms": int((time.perf_counter() - start) * 1000),
        }
        await manager.broadcast(project_id, {"type": "blast_radius", "target": function_id, "results": blast})
        return result

    @staticmethod
    def _map_runtime(
        functions: list[ParsedFunction], runtime_by_comm: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Coarse PID→function mapping: attribute a process's runtime features to
        functions whose file stem matches the traced command name. Refined with
        DWARF stack resolution in Phase 1C."""
        mapping: dict[str, dict[str, Any]] = {}
        for fn in functions:
            stem = Path(fn.file_path).stem
            for comm, features in runtime_by_comm.items():
                if comm and (comm in stem or stem in comm):
                    mapping[fn.id] = features
        return mapping

    @staticmethod
    def collect_source_files(root: str, languages: list[str] | None = None) -> list[str]:
        """Walk a project root and return all supported source files."""
        root_path = Path(root)
        if not root_path.exists():
            return []
        files: list[str] = []
        for path in root_path.rglob("*"):
            if path.is_file() and detect_language(str(path)):
                if any(part in {".git", "node_modules", ".venv", "__pycache__"} for part in path.parts):
                    continue
                files.append(str(path))
        return files


_worker: AnalysisWorker | None = None


def get_worker() -> AnalysisWorker:
    global _worker
    if _worker is None:
        _worker = AnalysisWorker()
    return _worker
