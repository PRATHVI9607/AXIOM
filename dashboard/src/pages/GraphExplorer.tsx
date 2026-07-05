// GraphExplorer.tsx — force-directed intent graph; click a node to see its blast radius.
import { useState } from "react";
import ForceGraph from "../components/ForceGraph";
import { api, type FunctionAnalysis, type GraphResponse } from "../api";

export default function GraphExplorer() {
  const [projectId, setProjectId] = useState("");
  const [graph, setGraph] = useState<GraphResponse | null>(null);
  const [selected, setSelected] = useState<FunctionAnalysis | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setError(null);
    setSelected(null);
    try {
      setGraph(await api.graph(projectId));
    } catch (e) {
      setError((e as Error).message);
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
    <div>
      <h1 className="text-2xl font-semibold mb-6">Intent Graph Explorer</h1>
      <div className="flex gap-2 mb-6">
        <input
          value={projectId}
          onChange={(e) => setProjectId(e.target.value)}
          placeholder="project id"
          className="rounded bg-axiom-panel border border-slate-700 px-3 py-2 text-sm w-80"
        />
        <button onClick={load} className="rounded bg-axiom-accent px-4 py-2 text-sm font-medium text-white">
          Load graph
        </button>
      </div>
      {error && <div className="text-risk-high mb-4">{error}</div>}

      {graph && (
        <div className="grid grid-cols-3 gap-4">
          <div className="col-span-2">
            <div className="mb-2 text-sm text-slate-400">
              {graph.total_nodes} functions · {graph.edges.length} edges · click a node
            </div>
            <ForceGraph nodes={graph.nodes} edges={graph.edges} onSelect={selectNode} />
          </div>
          <aside className="rounded-lg bg-axiom-panel border border-slate-800 p-4">
            {!selected && <div className="text-slate-500 text-sm">Select a node to see its blast radius.</div>}
            {selected && (
              <div>
                <div className="font-mono text-lg">{selected.function_name}</div>
                <div className="text-sm text-slate-400 mb-3">
                  risk {selected.risk_score.toFixed(2)} · {selected.analysis_time_ms}ms
                </div>
                <div className="text-xs uppercase text-slate-500 mb-1">Blast radius</div>
                <ul className="space-y-2">
                  {selected.blast_radius.map((b) => (
                    <li key={b.function_id} className="text-sm border-l-2 border-risk-high pl-2">
                      <div className="font-mono">{b.function_name}</div>
                      <div className="text-slate-500">{b.failure_reason}</div>
                      <div className="text-slate-600 text-xs">{b.failure_path.join(" → ")}</div>
                    </li>
                  ))}
                  {selected.blast_radius.length === 0 && (
                    <li className="text-slate-500 text-sm">No high-risk downstream functions.</li>
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
