// Layout.tsx — sidebar nav + topbar with live backend connection status.
import { useEffect, useState } from "react";
import { NavLink } from "react-router-dom";
import { GaugeIcon, GraphIcon, HexagonIcon, PulseIcon } from "@phosphor-icons/react";
import { api } from "../api";
import { StatusDot } from "./ui";

const NAV = [
  { to: "/", label: "Overview", end: true, icon: GaugeIcon },
  { to: "/graph", label: "Intent Graph", end: false, icon: GraphIcon },
];

export default function Layout({ children }: { children: React.ReactNode }) {
  const [online, setOnline] = useState<boolean | null>(null);
  const project = localStorage.getItem("axiom_project");

  useEffect(() => {
    let alive = true;
    const ping = () =>
      api
        .health()
        .then(() => alive && setOnline(true))
        .catch(() => alive && setOnline(false));
    ping();
    const id = setInterval(ping, 8000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  return (
    <div className="flex min-h-[100dvh]">
      <aside className="flex w-56 flex-col border-r border-line bg-ink-900">
        <div className="flex items-center gap-2 px-5 py-5">
          <HexagonIcon size={22} weight="fill" className="text-accent" />
          <span className="text-[15px] font-semibold tracking-tight text-slate-100">AXIOM</span>
        </div>
        <nav className="flex-1 space-y-0.5 px-3">
          {NAV.map(({ to, label, end, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                `flex items-center gap-3 rounded px-3 py-2 text-sm transition-colors ${
                  isActive
                    ? "bg-accent-soft text-accent"
                    : "text-slate-400 hover:bg-ink-850 hover:text-slate-200"
                }`
              }
            >
              <Icon size={18} weight="bold" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-line px-5 py-4 text-[11px] text-slate-600">
          Semantic Runtime
          <br />
          Code Intelligence
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-14 items-center justify-between border-b border-line bg-ink-900/60 px-6 backdrop-blur">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <PulseIcon size={16} weight="bold" className="text-accent" />
            {project ? (
              <span className="font-mono text-xs text-slate-400">project {project.slice(0, 8)}</span>
            ) : (
              <span className="text-xs">no project loaded</span>
            )}
          </div>
          <StatusDot
            ok={online === true}
            label={online === null ? "connecting…" : online ? "backend online" : "backend offline"}
          />
        </header>
        <main className="flex-1 overflow-y-auto px-8 py-7">
          <div className="mx-auto max-w-[1200px]">{children}</div>
        </main>
      </div>
    </div>
  );
}
