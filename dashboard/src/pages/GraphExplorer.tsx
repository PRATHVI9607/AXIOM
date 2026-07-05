// GraphExplorer.tsx — force-directed intent graph; click a node for its blast radius.
import { useState } from "react";
import { ArrowsOutIcon, TargetIcon, TreeStructureIcon } from "@phosphor-icons/react";
import ForceGraph from "../components/ForceGraph";
import { api, type FunctionAnalysis, type GraphResponse } from "../api";
import { EmptyState, RiskBadge, Skeleton } from "../components/ui";

export default function GraphExplorer() {
  const [projectId, setProjectId] = useState(localStorage.getItem("axiom_project") ?? "");
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [selected, setSelected] = useState<FunctionAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setSelected(null);
    setLoading(true);
    try {
      setGraph(await api.graph(projectId));
      localStorage.setItem("axiom_project", projectId);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  }

  async function selectNode(id: string) {
    try {
      setSelected(await api.analyzeFunction(projectId, id));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight text-slate-100">Intent Graph</h1>
          <p className="mt-1 text-sm text-slate-500">
            Nodes are functions, colored by risk. Click one to trace its blast radius.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <input
            value={projectId}
            onChange={(e) => setProjectId(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load()}
            placeholder="project id"
            className="w-72 rounded border border-line bg-ink-850 px-3 py-2 font-mono text-xs text-slate-200 outline-none placeholder:text-slate-600 focus:border-accent"
          />
          <button
            onClick={load}
            className="flex items-center gap-1.5 rounded bg-accent px-3 py-2 text-xs font-medium text-accent-fg transition-transform active:scale-[0.98]"
          >
            <TreeStructureIcon size={15} weight="bold" /> Load
          </button>
        </div>
      </div>

      {error && (
        <div className="rounded border border-risk-high/30 bg-risk-high/10 px-4 py-2.5 text-sm text-risk-high">
          {error}
        </div>
      )}

      {loading ? (
        <Skeleton className="h-[600px]" />
      ) : !graph ? (
        <EmptyState
          icon={<ArrowsOutIcon size={40} weight="thin" />}
          title="No graph loaded"
          hint="Enter a project id and press Load — or open the link from scripts/demo.py."
        />
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <div className="mb-2 flex items-center gap-4 text-xs text-slate-500">
              <span>{graph.total_nodes} functions · {graph.edges.length} edges</span>
              <Legend />
            </div>
            <ForceGraph nodes={graph.nodes} edges={graph.edges} onSelect={selectNode} />
          </div>

          <aside className="rounded-lg border border-line bg-ink-900 p-4 shadow-panel">
            {!selected ? (
              <div className="flex h-full flex-col items-center justify-center py-16 text-center">
                <TargetIcon size={34} weight="thin" className="text-slate-600" />
                <div className="mt-3 text-sm text-slate-400">Select a node</div>
                <div className="mt-1 text-xs text-slate-600">Its cascade appears here.</div>
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-between">
                  <span className="font-mono text-sm text-slate-100">{selected.function_name}</span>
                  <RiskBadge score={selected.risk_score} />
                </div>
                <div className="mt-1 text-xs text-slate-500">
                  analyzed in {selected.analysis_time_ms}ms
                </div>
                <div className="mt-4 mb-2 text-[11px] uppercase tracking-wider text-slate-500">
                  Blast radius · {selected.blast_radius.length}
                </div>
                <ul className="space-y-2.5">
                  {selected.blast_radius.map((b) => (
                    <li key={b.function_id} className="rounded border border-line bg-ink-850 p-2.5">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs text-slate-200">{b.function_name}</span>
                        <RiskBadge score={b.risk_score} />
                      </div>
                      <div className="mt-1 text-[11px] text-slate-500">{b.failure_reason}</div>
                      {b.failure_path.length > 1 && (
                        <div className="mt-1 font-mono text-[10px] text-slate-600">
                          {b.failure_path.join(" › ")}
                        </div>
                      )}
                    </li>
                  ))}
                  {selected.blast_radius.length === 0 && (
                    <li className="text-xs text-slate-500">
                      No high-risk downstream functions found.
                    </li>
                  )}
                </ul>
              </div>
            )}
          </aside>
        </div>
      )}
    </div>
  );
}

function Legend() {
  const items = [
    ["#34d399", "low"],
    ["#fbbf24", "med"],
    ["#f87171", "high"],
  ] as const;
  return (
    <span className="flex items-center gap-3">
      {items.map(([c, l]) => (
        <span key={l} className="inline-flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full" style={{ background: c }} />
          {l}
        </span>
      ))}
    </span>
  );
}
