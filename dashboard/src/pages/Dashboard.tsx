// Dashboard.tsx — codebase health overview; pings backend /health on load.
import { useEffect, useState } from "react";
import { api, type HealthResponse } from "../api";

export default function Dashboard() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .health()
      .then(setHealth)
      .catch((e: Error) => setError(e.message));
  }, []);

  return (
    <div>
      <h1 className="text-2xl font-semibold mb-6">Codebase Health</h1>
      {error && <div className="text-risk-high">Backend unreachable: {error}</div>}
      {!health && !error && <div className="text-slate-400">Connecting to AXIOM backend…</div>}
      {health && (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <Card label="Status" value={health.status} good={health.status === "ok"} />
          <Card label="Version" value={health.version} />
          <Card label="Database" value={health.database ? "connected" : "down"} good={health.database} />
          <Card
            label="eBPF"
            value={health.ebpf_available ? "available" : "static-only"}
            good={health.ebpf_available}
          />
          <Card label="Embed provider" value={health.embed_provider} />
          <Card label="Air-gapped" value={health.air_gapped ? "yes" : "no"} />
        </div>
      )}
    </div>
  );
}

function Card({ label, value, good }: { label: string; value: string; good?: boolean }) {
  return (
    <div className="rounded-lg bg-axiom-panel border border-slate-800 p-4">
      <div className="text-xs uppercase tracking-wide text-slate-500">{label}</div>
      <div className={`mt-1 text-lg font-medium ${good === false ? "text-risk-high" : ""}`}>
        {value}
      </div>
    </div>
  );
}
