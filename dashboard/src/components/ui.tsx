// ui.tsx — small dark-theme primitives shared across pages.
import type { ReactNode } from "react";

// ── Risk helpers ─────────────────────────────────────────
export function riskBand(score: number): "low" | "med" | "high" {
  if (score >= 0.6) return "high";
  if (score >= 0.3) return "med";
  return "low";
}
const RISK_HEX = { low: "#34d399", med: "#fbbf24", high: "#f87171" } as const;

export function RiskBadge({ score }: { score: number }) {
  const band = riskBand(score);
  return (
    <span
      className="inline-flex items-center gap-1.5 rounded px-2 py-0.5 font-mono text-xs font-medium"
      style={{ color: RISK_HEX[band], background: `${RISK_HEX[band]}18` }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: RISK_HEX[band] }} />
      {score.toFixed(2)}
    </span>
  );
}

// ── Radial health gauge ──────────────────────────────────
export function Gauge({ value, label }: { value: number; label: string }) {
  const pct = Math.max(0, Math.min(1, value));
  const r = 52;
  const c = 2 * Math.PI * r;
  const color = pct >= 0.66 ? RISK_HEX.low : pct >= 0.4 ? RISK_HEX.med : RISK_HEX.high;
  return (
    <div className="flex flex-col items-center">
      <svg width="140" height="140" viewBox="0 0 140 140" className="-rotate-90">
        <circle cx="70" cy="70" r={r} fill="none" stroke="#232937" strokeWidth="10" />
        <circle
          cx="70"
          cy="70"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={c * (1 - pct)}
          style={{ transition: "stroke-dashoffset 900ms cubic-bezier(0.16,1,0.3,1)" }}
        />
      </svg>
      <div className="-mt-24 flex flex-col items-center">
        <span className="font-mono text-3xl font-semibold" style={{ color }}>
          {Math.round(pct * 100)}
        </span>
        <span className="text-xs text-slate-500">{label}</span>
      </div>
      <div className="mt-14" />
    </div>
  );
}

// ── Stat tile ────────────────────────────────────────────
export function StatTile({
  label,
  value,
  hint,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  hint?: string;
  tone?: "default" | "good" | "bad";
}) {
  const toneCls =
    tone === "good" ? "text-risk-low" : tone === "bad" ? "text-risk-high" : "text-slate-100";
  return (
    <div className="rounded-lg border border-line bg-ink-900 p-4 shadow-panel">
      <div className="text-[11px] uppercase tracking-wider text-slate-500">{label}</div>
      <div className={`mt-1.5 font-mono text-xl font-medium ${toneCls}`}>{value}</div>
      {hint && <div className="mt-0.5 text-xs text-slate-500">{hint}</div>}
    </div>
  );
}

// ── Status dot (real connection state) ───────────────────
export function StatusDot({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className="inline-flex items-center gap-2 text-xs text-slate-400">
      <span
        className="h-2 w-2 rounded-full"
        style={{ background: ok ? RISK_HEX.low : RISK_HEX.high, boxShadow: `0 0 8px ${ok ? RISK_HEX.low : RISK_HEX.high}66` }}
      />
      {label}
    </span>
  );
}

// ── Skeleton + empty state ───────────────────────────────
export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton rounded ${className}`} />;
}

export function EmptyState({ icon, title, hint }: { icon: ReactNode; title: string; hint?: string }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-line bg-ink-900/50 px-6 py-16 text-center">
      <div className="text-slate-600">{icon}</div>
      <div className="mt-3 text-sm font-medium text-slate-300">{title}</div>
      {hint && <div className="mt-1 max-w-sm text-xs text-slate-500">{hint}</div>}
    </div>
  );
}
