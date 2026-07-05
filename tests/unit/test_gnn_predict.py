"""Unit + property tests for GNN scoring and the failure predictor (PRD §7.4/§7.5)."""
from hypothesis import given, settings
from hypothesis import strategies as st

from axiom.services.ast_service import ParsedFunction, function_id
from axiom.services.gnn_service import get_gnn
from axiom.services.predict_service import get_predictor


def _fn(name: str, src: str, calls: list[str] | None = None) -> ParsedFunction:
    return ParsedFunction(
        id=function_id("f.py", name, 1),
        file_path="f.py",
        language="python",
        function_name=name,
        start_line=1,
        end_line=10,
        source_text=src,
        calls=calls or [],
    )


def _sample_graph():
    functions = [
        _fn("entry", "return validate(x)", calls=["validate"]),
        _fn("validate", "os.system(cmd)", calls=["run"]),  # risky
        _fn("run", "return 1"),
    ]
    return get_gnn().build_graph(functions), functions


def test_risk_scores_in_unit_interval():
    graph, _ = _sample_graph()
    for node in graph.nodes.values():
        assert 0.0 <= node.risk_score <= 1.0


def test_risky_function_scores_higher():
    graph, _ = _sample_graph()
    scores = {n.label: n.risk_score for n in graph.nodes.values()}
    assert scores["validate"] > scores["run"]


def test_codebase_health_in_range():
    graph, _ = _sample_graph()
    assert 0.0 <= get_gnn().codebase_health(graph) <= 1.0


def test_blast_radius_sorted_descending():
    graph, functions = _sample_graph()
    target = functions[0].id
    blast = get_predictor().predict_blast_radius(graph, target, risk_threshold=0.0)
    risks = [b["risk_score"] for b in blast]
    assert risks == sorted(risks, reverse=True)


@settings(max_examples=25, deadline=None)
@given(st.text(min_size=0, max_size=200))
def test_heuristic_score_bounded_for_arbitrary_source(src):
    graph = get_gnn().build_graph([_fn("f", src)])
    node = next(iter(graph.nodes.values()))
    assert 0.0 <= node.risk_score <= 1.0
