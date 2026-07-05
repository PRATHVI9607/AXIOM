"""Integration tests for API endpoints: health, auth guards, project lifecycle."""


def test_health_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["version"] == "1.0.0"
    assert body["status"] in {"ok", "degraded"}


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["name"] == "AXIOM"


def test_projects_require_auth(client):
    assert client.get("/api/v1/projects").status_code == 401


def test_bad_token_rejected(client):
    r = client.get("/api/v1/projects", headers={"Authorization": "Bearer not-a-jwt"})
    assert r.status_code == 401


def test_project_crud_roundtrip(client, auth_headers):
    created = client.post(
        "/api/v1/projects",
        json={"name": "demo", "root_path": "./axiom", "languages": ["python"]},
        headers=auth_headers,
    )
    assert created.status_code == 201
    pid = created.json()["id"]

    listed = client.get("/api/v1/projects", headers=auth_headers)
    assert listed.status_code == 200
    assert any(p["id"] == pid for p in listed.json())

    got = client.get(f"/api/v1/projects/{pid}", headers=auth_headers)
    assert got.status_code == 200 and got.json()["name"] == "demo"


def test_graph_before_analysis_404(client, auth_headers):
    r = client.get("/api/v1/graph/nonexistent", headers=auth_headers)
    assert r.status_code == 404


def test_analyze_function_without_graph_conflicts(client, auth_headers):
    r = client.post(
        "/api/v1/analyze/function",
        json={"project_id": "nope", "function_id": "sha256:abc"},
        headers=auth_headers,
    )
    assert r.status_code == 409
