"""Cascading failure predictor via personalized PageRank on the intent graph (PRD §7.5)."""
from __future__ import annotations

import logging
from typing import Any

from axiom.services.gnn_service import GNNEngine, IntentGraph

logger = logging.getLogger(__name__)


class FailurePredictor:
    """Computes the predicted blast radius for a target function."""

    def predict_blast_radius(
        self,
        graph: IntentGraph,
        target_id: str,
        risk_threshold: float = 0.35,
        top_k: int = 10,
        alpha: float = 0.15,
    ) -> list[dict[str, Any]]:
        """Rank downstream functions by personalized PageRank × node risk.

        The combined score is 0.5·pagerank + 0.5·node_risk; propagated nodes peak
        around 0.5, so the default threshold (0.35) surfaces a useful cascade
        rather than the empty list a 0.6 gate produces on real codebases.
        """
        if target_id not in graph.nodes:
            return []
        scores = self._personalized_pagerank(graph, target_id, alpha)
        results: list[dict[str, Any]] = []
        for node_id, pr in scores.items():
            if node_id == target_id:
                continue
            node = graph.nodes[node_id]
            combined = round(pr * 0.5 + node.risk_score * 0.5, 4)
            if combined < risk_threshold:
                continue
            results.append(
                {
                    "function_id": node_id,
                    "function_name": node.label,
                    "file_path": node.file_path,
                    "risk_score": combined,
                    "failure_path": self._path(graph, target_id, node_id),
                    "failure_reason": self._reason(node),
                }
            )
        results.sort(key=lambda r: r["risk_score"], reverse=True)
        return results[:top_k]

    def _personalized_pagerank(
        self, graph: IntentGraph, source: str, alpha: float, max_iter: int = 100, eps: float = 1e-6
    ) -> dict[str, float]:
        nodes = list(graph.nodes)
        n = len(nodes)
        if n == 0:
            return {}
        rank = {node: (1.0 if node == source else 0.0) for node in nodes}
        out_edges: dict[str, list[tuple[str, float]]] = {node: [] for node in nodes}
        for edge in graph.edges:
            if edge.source in out_edges and edge.target in graph.nodes:
                out_edges[edge.source].append((edge.target, max(edge.weight, 0.01)))

        for _ in range(max_iter):
            new_rank = {node: alpha * (1.0 if node == source else 0.0) for node in nodes}
            for node in nodes:
                neighbors = out_edges[node]
                if not neighbors:
                    continue
                total_w = sum(w for _, w in neighbors)
                share = (1 - alpha) * rank[node]
                for target, w in neighbors:
                    new_rank[target] += share * (w / total_w)
            delta = sum(abs(new_rank[node] - rank[node]) for node in nodes)
            rank = new_rank
            if delta < eps:
                break
        return rank

    @staticmethod
    def _path(graph: IntentGraph, source: str, target: str, max_depth: int = 6) -> list[str]:
        """BFS shortest CALLS path from source to target, as function labels."""
        from collections import deque

        queue: deque[list[str]] = deque([[source]])
        seen = {source}
        while queue:
            path = queue.popleft()
            if len(path) > max_depth:
                continue
            last = path[-1]
            if last == target:
                return [graph.nodes[n].label for n in path if n in graph.nodes]
            for nxt, _ in graph.neighbors(last):
                if nxt not in seen:
                    seen.add(nxt)
                    queue.append(path + [nxt])
        # No static path found — report endpoints only.
        return [graph.nodes[source].label, graph.nodes[target].label]

    @staticmethod
    def _reason(node: Any) -> str:
        r = node.risk_score
        if r >= 0.8:
            return "High semantic risk pattern with downstream reachability"
        if r >= 0.6:
            return "Elevated risk propagating through call graph"
        return "Moderate risk via shared dependencies"


_predictor: FailurePredictor | None = None


def get_predictor() -> FailurePredictor:
    global _predictor
    if _predictor is None:
        _predictor = FailurePredictor()
    return _predictor
