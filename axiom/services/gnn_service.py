"""GNN intent-graph engine (PRD §7.4).

Builds a graph of functions (nodes) with typed edges and scores per-node risk.
If torch/torch-geometric are installed and weights exist, uses the trained GNN;
otherwise falls back to a deterministic heuristic scorer so predictions still
flow end-to-end without the heavy ML stack (Critical Rule #3, #7).
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np

from axiom.services.ast_service import ParsedFunction

logger = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
WEIGHTS_PATH = MODELS_DIR / "gnn_v1.pt"      # optional torch weights
NPZ_WEIGHTS_PATH = MODELS_DIR / "gnn_v1.npz"  # bundled numpy weights (default)

FEATURE_DIM = 8

# Lexical signals that correlate with the vulnerability patterns AXIOM targets.
_RISK_SIGNALS: dict[str, float] = {
    "eval": 0.35, "exec": 0.35, "system": 0.3, "popen": 0.3, "subprocess": 0.2,
    "pickle": 0.3, "yaml.load": 0.3, "os.path.join": 0.1, "open": 0.1,
    "query": 0.15, "execute": 0.15, "format": 0.1, "request": 0.1,
    "password": 0.2, "secret": 0.2, "token": 0.15, "md5": 0.2, "sha1": 0.15,
    "..": 0.15, "shell=true": 0.4,
}


@dataclass
class GraphNode:
    id: str
    label: str
    language: str
    file_path: str
    start_line: int = 0
    end_line: int = 0
    risk_score: float = 0.0
    features: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    type: str
    weight: float = 1.0


@dataclass
class IntentGraph:
    nodes: dict[str, GraphNode] = field(default_factory=dict)
    edges: list[GraphEdge] = field(default_factory=list)

    def neighbors(self, node_id: str) -> list[tuple[str, float]]:
        return [(e.target, e.weight) for e in self.edges if e.source == node_id]


class GNNEngine:
    """Constructs intent graphs and produces node risk scores."""

    def __init__(self) -> None:
        self._weights: dict[str, Any] | None = None
        self._model_ready = self._try_load_model()

    def _try_load_model(self) -> bool:
        """Load bundled numpy GNN weights. Falls back to the heuristic scorer if absent."""
        if not NPZ_WEIGHTS_PATH.exists():
            logger.info("GNN weights %s missing — heuristic scorer.", NPZ_WEIGHTS_PATH.name)
            return False
        try:
            data = np.load(NPZ_WEIGHTS_PATH)
            self._weights = {k: data[k] for k in ("w1", "b1", "w2", "b2")}
            logger.info("Loaded numpy GNN weights from %s", NPZ_WEIGHTS_PATH.name)
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("Failed to load GNN weights, heuristic fallback: %s", exc)
            return False

    def build_graph(
        self,
        functions: list[ParsedFunction],
        runtime: dict[str, dict[str, Any]] | None = None,
    ) -> IntentGraph:
        """Build nodes + CALLS/SEMANTIC edges from parsed functions."""
        runtime = runtime or {}
        graph = IntentGraph()
        name_to_id: dict[str, str] = {f.function_name: f.id for f in functions}

        for fn in functions:
            graph.nodes[fn.id] = GraphNode(
                id=fn.id,
                label=fn.function_name,
                language=fn.language,
                file_path=fn.file_path,
                start_line=fn.start_line,
                end_line=fn.end_line,
                features={"loc": fn.end_line - fn.start_line + 1, **runtime.get(fn.id, {})},
            )
        # CALLS edges (static) from resolved call names.
        for fn in functions:
            for callee in fn.calls:
                target = name_to_id.get(callee)
                if target and target != fn.id:
                    graph.edges.append(GraphEdge(fn.id, target, "CALLS", 1.0))

        self.score_nodes(graph, functions)
        return graph

    def score_nodes(self, graph: IntentGraph, functions: list[ParsedFunction]) -> None:
        """Assign a risk score in [0,1] to every node."""
        if self._model_ready:
            try:
                self._score_with_model(graph, functions)
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning("GNN inference failed, heuristic fallback: %s", exc)
        for fn in functions:
            graph.nodes[fn.id].risk_score = self._heuristic_score(fn, graph)

    def node_features(self, fn: ParsedFunction, graph: IntentGraph) -> np.ndarray:
        """8-dim feature vector for a function node (lexical + structural + runtime)."""
        text = fn.source_text.lower()
        signal = sum(w for s, w in _RISK_SIGNALS.items() if s in text)
        fan_in = sum(1 for e in graph.edges if e.target == fn.id)
        fan_out = sum(1 for e in graph.edges if e.source == fn.id)
        rt = graph.nodes[fn.id].features
        return np.array(
            [
                min(signal, 2.0) / 2.0,
                min((fn.end_line - fn.start_line + 1) / 100.0, 1.0),
                min(fan_in / 10.0, 1.0),
                min(fan_out / 10.0, 1.0),
                min(rt.get("file_access_count", 0) / 10.0, 1.0),
                min(rt.get("net_connect_count", 0) / 10.0, 1.0),
                min(rt.get("spawn_count", 0) / 5.0, 1.0),
                min(rt.get("priv_esc_count", 0) / 3.0, 1.0),
            ],
            dtype=np.float32,
        )

    def _score_with_model(self, graph: IntentGraph, functions: list[ParsedFunction]) -> None:
        """GraphSAGE-style forward pass in numpy: mean-aggregate 1-hop neighbors → MLP."""
        assert self._weights is not None
        feats = {fn.id: self.node_features(fn, graph) for fn in functions}
        # Adjacency (undirected for aggregation).
        neighbors: dict[str, list[str]] = {fn.id: [] for fn in functions}
        for e in graph.edges:
            if e.source in neighbors and e.target in feats:
                neighbors[e.source].append(e.target)
                neighbors[e.target].append(e.source)

        w1, b1, w2, b2 = (self._weights[k] for k in ("w1", "b1", "w2", "b2"))
        for fn in functions:
            self_f = feats[fn.id]
            nbrs = neighbors[fn.id]
            agg = np.mean([feats[n] for n in nbrs], axis=0) if nbrs else np.zeros(FEATURE_DIM, np.float32)
            x = np.concatenate([self_f, agg])
            h = np.maximum(x @ w1 + b1, 0.0)  # ReLU
            logit = float((h @ w2 + b2).reshape(-1)[0])
            graph.nodes[fn.id].risk_score = round(1.0 / (1.0 + math.exp(-logit)), 4)

    def _heuristic_score(self, fn: ParsedFunction, graph: IntentGraph) -> float:
        text = fn.source_text.lower()
        score = 0.0
        for signal, weight in _RISK_SIGNALS.items():
            if signal in text:
                score += weight
        # Fan-in raises blast potential.
        fan_in = sum(1 for e in graph.edges if e.target == fn.id)
        score += min(fan_in * 0.03, 0.2)
        # Squash to [0,1] with a logistic curve.
        return round(1 / (1 + math.exp(-3 * (score - 0.5))), 4)

    @staticmethod
    def codebase_health(graph: IntentGraph) -> float:
        """Overall health = 1 - mean(risk). Higher is healthier."""
        if not graph.nodes:
            return 1.0
        mean_risk = sum(n.risk_score for n in graph.nodes.values()) / len(graph.nodes)
        return round(1 - mean_risk, 4)


_engine: GNNEngine | None = None


def get_gnn() -> GNNEngine:
    global _engine
    if _engine is None:
        _engine = GNNEngine()
    return _engine
