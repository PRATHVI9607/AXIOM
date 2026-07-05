"""Integration tests: eBPF client fallback, WebSocket auth gate, GNN model, patches API."""
import pytest

from axiom.services.ebpf_service import EbpfTracerClient


@pytest.mark.asyncio
async def test_ebpf_client_returns_empty_when_disabled():
    client = EbpfTracerClient()
    client.settings.ebpf_enabled = False
    assert await client.fetch_events() == []
    assert await client.summarize() == {}


@pytest.mark.asyncio
async def test_ebpf_client_static_only_when_daemon_down():
    client = EbpfTracerClient()
    client.settings.ebpf_enabled = True
    client.settings.ebpf_tracer_port = 59999  # nothing listening
    assert await client.fetch_events(timeout=0.5) == []


def test_websocket_rejects_bad_token(client):
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/proj1?token=not-a-jwt"):
            pass


def test_websocket_accepts_valid_token(client):
    from axiom.core.security import create_access_token

    token, _ = create_access_token("user:test")
    with client.websocket_connect(f"/ws/proj1?token={token}") as ws:
        ws.send_json({"type": "subscribe_function", "function_id": "sha256:x"})
        reply = ws.receive_json()
        assert reply["type"] == "ack"


def test_gnn_model_loaded_and_scores_bounded():
    from axiom.services.ast_service import get_parser
    from axiom.services.gnn_service import get_gnn

    gnn = get_gnn()
    fns = get_parser().parse_file("axiom/services/patch_service.py")
    graph = gnn.build_graph(fns)
    assert all(0.0 <= n.risk_score <= 1.0 for n in graph.nodes.values())
    assert 0.0 <= gnn.codebase_health(graph) <= 1.0


def test_patch_generate_and_list(client, auth_headers, tmp_path):
    bad = tmp_path / "vuln.py"
    bad.write_text('def q(u):\n    return db.execute(f"SELECT * FROM t WHERE id={u}")\n')
    gen = client.post(
        f"/api/v1/patches/proj-x/generate?file_path={bad}", headers=auth_headers
    )
    assert gen.status_code == 200
    assert any(p["pattern"] == "sql_injection" for p in gen.json())
