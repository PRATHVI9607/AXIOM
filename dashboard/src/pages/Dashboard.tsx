// Dashboard.tsx — codebase health overview: gauge, risk buckets, top-risk functions.
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { CpuIcon, DatabaseIcon, GraphIcon, WarningIcon } from "@phosphor-icons/react";
import { api, type GraphResponse, type HealthResponse, type HealthScore } from "../api";
import { EmptyState, Gauge, RiskBadge, Skeleton, StatTile } from "../components/ui";

export default function Dashboard() {
  const [sys, setSys] = useState<HealthResponse | null>(null);
  const [score, setScore] = useState<HealthScore | null>(null);
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const project = localStorage.getItem("axiom_project");

  useEffect(() => {
    api.health().then(setSys).catch((e: Error) => setError(e.message));
    if (!project) {
      setLoading(false);
      return;
    }
    Promise.all([api.health_score(project), api.graph(project)])
      .then(([s, g]) => {
        setScore(s);
        setGraph(g);
      })
      .catch(() => void 0)
      .finally(() => setLoading(false));
  }, [project]);

  const topRisk = graph
    ? [...graph.nodes].sort((a, b) => b.risk_score - a.risk_score).slice(0, 8)
    : [];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Codebase Health</h1>
        <p className="mt-1 text-sm text-slate-500">
          Semantic risk across the analyzed project, fused with runtime behavior.
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded border border-risk-high/30 bg-risk-high/10 px-4 py-3 text-sm text-risk-high">
          <WarningIcon size={18} weight="bold" /> Backend unreachable: {error}
        </div>
      )}

      {/* System status row */}
      {sys && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <StatTile label="Backend" value={sys.status} tone={sys.status === "ok" ? "good" : "bad"} />
          <StatTile label="Version" value={sys.version} />
          <StatTile label="Database" value={sys.database ? "connected" : "down"} tone={sys.database ? "good" : "bad"} />
          <StatTile label="eBPF" value={sys.ebpf_available ? "live" : "static-only"} />
        </div>
      )}

      {!project ? (
        <EmptyState
          icon={<GraphIcon size={40} weight="thin" />}
          title="No project loaded"
          hint="Run `python scripts/demo.py`, then open the dashboard link it prints (token + project preloaded)."
        />
      ) : loading ? (
        <div className="grid gap-4 lg:grid-cols-3">
          <Skeleton className="h-56 lg:col-span-1" />
          <Skeleton className="h-56 lg:col-span-2" />
        </div>
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          {/* Health gauge + buckets */}
          <div className="rounded-lg border border-line bg-ink-900 p-6 shadow-panel">
            <div className="mb-2 text-[11px] uppercase tracking-wider text-slate-500">
              Health score
            </div>
            {score && <Gauge value={score.current_score} label="healthy" />}
            <div className="mt-4 grid grid-cols-3 gap-2 text-center">
              <Bucket n={score?.high_risk_count ?? 0} label="high" color="#f87171" />
              <Bucket n={score?.medium_risk_count ?? 0} label="med" color="#fbbf24" />
              <Bucket n={score?.low_risk_count ?? 0} label="low" color="#34d399" />
            </div>
          </div>

          {/* Top-risk functions */}
          <div className="rounded-lg border border-line bg-ink-900 shadow-panel lg:col-span-2">
            <div className="flex items-center justify-between border-b border-line px-5 py-3">
              <span className="text-sm font-medium text-slate-200">Highest-risk functions</span>
              <Link to="/graph" className="flex items-center gap-1 text-xs text-accent hover:underline">
                <GraphIcon size={14} weight="bold" /> open graph
              </Link>
            </div>
            {topRisk.length === 0 ? (
              <div className="p-5 text-sm text-slate-500">No functions analyzed yet.</div>
            ) : (
              <ul className="divide-y divide-line">
                {topRisk.map((n) => (
                  <li key={n.id} className="flex items-center justify-between px-5 py-2.5">
                    <div className="min-w-0">
                      <div className="truncate font-mono text-sm text-slate-200">{n.label}</div>
                      <div className="truncate text-xs text-slate-500">
                        {n.file_path.replace(/\\/g, "/").split("/").pop()}:{n.start_line}
                      </div>
                    </div>
                    <RiskBadge score={n.risk_score} />
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {sys && (
        <div className="flex flex-wrap gap-x-6 gap-y-1 text-xs text-slate-600">
          <span className="inline-flex items-center gap-1.5">
            <CpuIcon size={14} /> embed: {sys.embed_provider}
          </span>
          <span className="inline-flex items-center gap-1.5">
            <DatabaseIcon size={14} /> air-gapped: {sys.air_gapped ? "yes" : "no"}
          </span>
        </div>
      )}
    </div>
  );
}

function Bucket({ n, label, color }: { n: number; label: string; color: string }) {
  return (
    <div className="rounded border border-line bg-ink-850 py-2">
      <div className="font-mono text-lg font-semibold" style={{ color }}>
        {n}
      </div>
      <div className="text-[10px] uppercase tracking-wide text-slate-500">{label}</div>
    </div>
  );
}
