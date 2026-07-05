// App.tsx — top-level layout with sidebar navigation and routed pages.
import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import GraphExplorer from "./pages/GraphExplorer";

const nav = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/graph", label: "Intent Graph" },
];

export default function App() {
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 bg-axiom-panel border-r border-slate-800 p-4">
        <div className="text-xl font-bold text-axiom-accent mb-6">◆ AXIOM</div>
        <nav className="space-y-1">
          {nav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `block rounded px-3 py-2 text-sm ${
                  isActive ? "bg-axiom-accent/20 text-axiom-accent" : "hover:bg-slate-800"
                }`
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/graph" element={<GraphExplorer />} />
        </Routes>
      </main>
    </div>
  );
}
