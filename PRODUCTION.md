# AXIOM — Production Readiness Guide

AXIOM defaults to a zero-setup **local single-user** tool. To run it for a team /
in production, work through this checklist. Items are ordered by priority.

---

## 1. Turn auth ON (required before exposing beyond localhost)

```bash
# .env on the server
AXIOM_AUTH_REQUIRED=true
AXIOM_AUTH_PROVIDER=github
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
# RS256 signing keys (generate, keep private key secret):
#   openssl genrsa -out private.pem 2048
#   openssl rsa -in private.pem -pubout -out public.pem
AXIOM_JWT_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
AXIOM_JWT_PUBLIC_KEY="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
```
With auth on, the dashboard uses the GitHub OAuth flow and CI uses API keys
(`POST /api/v1/auth/apikeys`). The VS Code extension points at the server via
`axiom.serverUrl` + `AXIOM: Set API Token`.

## 2. Use PostgreSQL, not SQLite

SQLite is the local default. In production:
```bash
DATABASE_URL=postgresql+asyncpg://axiom:STRONGPASS@postgres:5432/axiom
```
Run migrations on deploy: `alembic upgrade head` (the Docker/Helm entrypoints do this).
Never use `create_all` in production — always Alembic.

## 3. Deploy with Docker Compose or Kubernetes

**Compose (single host):**
```bash
docker compose up --build -d      # api + postgres + chromadb, health-checked
```
**Kubernetes (Helm):**
```bash
helm install axiom k8s/helm/axiom \
  --set image.repository=ghcr.io/PRATHVI9607/axiom --set image.tag=1.0.0 \
  --set env.AXIOM_AUTH_REQUIRED=true --set ingress.enabled=true --set ingress.host=axiom.yourco.com
```
Put the DB password and JWT keys in a Kubernetes Secret, not `values.yaml`.

## 4. TLS / networking

- Terminate HTTPS at the ingress / load balancer (TLS 1.3).
- Lock CORS to your dashboard origin (`AXIOM_FRONTEND_URL`); the app already reads it.
- Do not expose Postgres / ChromaDB ports publicly.

## 5. eBPF runtime tracing (Linux hosts only)

Run the tracer as a **separate privileged process/sidecar**, never in the API pod
(Critical Rule #2). On a node: `sudo python3 -m axiom.workers.ebpf_worker --port 8770`
with `CAP_BPF` + `CAP_PERFMON`. In k8s, a privileged DaemonSet. Off Linux, AXIOM
runs static-only automatically.

## 6. Models

- The bundled numpy GNN (`axiom/models/gnn_v1.npz`) ships for CPU inference — no torch needed.
- For the learned torch-geometric model: `pip install ".[ml]"`, train, and drop weights in.
- ChromaDB persists embeddings; back up its volume.

## 7. CI/CD

- `.github/workflows/test.yml` runs the backend + frontend suites on every PR.
- `.github/workflows/axiom.yml` + `axiom-action/` gate PRs on risk (set repo secrets
  `AXIOM_SERVER_URL`, `AXIOM_API_TOKEN`, `AXIOM_PROJECT_ID`).

## 8. Secrets & ops hygiene

- All secrets via env / secret manager. `.env`, `*.pem` are gitignored — keep it that way.
- Rotate the JWT signing key ~every 90 days and API keys as needed.
- Ship logs to your aggregator (`AXIOM_LOG_LEVEL=INFO`); `/metrics` is a stub to wire to Prometheus.

## 9. Distributing the VS Code extension

- Internal: share `vscode-extension/axiom-intelligence-1.0.0.vsix` (`code --install-extension …`).
- Public: `vsce publish` to the Marketplace (needs a publisher + token).
- Set `axiom.serverUrl` to the hosted backend in the shared settings so teammates just install and go.

---

## Production checklist (tick before go-live)
- [ ] `AXIOM_AUTH_REQUIRED=true` + OAuth + RS256 keys set
- [ ] PostgreSQL, migrations applied via Alembic
- [ ] HTTPS at the edge, CORS locked, datastores private
- [ ] Secrets in a secret manager, not files/`values.yaml`
- [ ] eBPF tracer runs privileged + isolated (if used)
- [ ] CI green; risk gate wired on PRs
- [ ] Backups for Postgres + ChromaDB volumes
- [ ] Extension `serverUrl` points at the hosted backend
