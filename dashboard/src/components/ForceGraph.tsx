// ForceGraph.tsx — dependency-free force-directed graph on a canvas.
// Node color = risk, node size = fan-in. Click a node to select it.
import { useEffect, useRef } from "react";
import type { GraphEdge, GraphNode } from "../api";

interface Sim {
  id: string;
  label: string;
  risk: number;
  x: number;
  y: number;
  vx: number;
  vy: number;
  deg: number;
}

function riskRGB(score: number): string {
  if (score >= 0.6) return "#ef4444";
  if (score >= 0.3) return "#eab308";
  return "#22c55e";
}

export default function ForceGraph({
  nodes,
  edges,
  onSelect,
}: {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onSelect?: (id: string) => void;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = (canvas.width = canvas.clientWidth);
    const H = (canvas.height = 600);

    const deg: Record<string, number> = {};
    edges.forEach((e) => {
      deg[e.target] = (deg[e.target] ?? 0) + 1;
      deg[e.source] = (deg[e.source] ?? 0) + 1;
    });

    const sims: Sim[] = nodes.map((n) => ({
      id: n.id,
      label: n.label,
      risk: n.risk_score,
      x: Math.random() * W,
      y: Math.random() * H,
      vx: 0,
      vy: 0,
      deg: deg[n.id] ?? 0,
    }));
    const byId = new Map(sims.map((s) => [s.id, s]));
    const links = edges
      .map((e) => ({ s: byId.get(e.source), t: byId.get(e.target) }))
      .filter((l): l is { s: Sim; t: Sim } => !!l.s && !!l.t);

    let raf = 0;
    let alpha = 1;

    function tick() {
      alpha *= 0.985;
      // Repulsion (O(n^2) — fine for a page of nodes).
      for (let i = 0; i < sims.length; i++) {
        for (let j = i + 1; j < sims.length; j++) {
          const a = sims[i];
          const b = sims[j];
          let dx = a.x - b.x;
          let dy = a.y - b.y;
          let d2 = dx * dx + dy * dy || 0.01;
          const f = (2000 * alpha) / d2;
          const d = Math.sqrt(d2);
          dx /= d;
          dy /= d;
          a.vx += dx * f;
          a.vy += dy * f;
          b.vx -= dx * f;
          b.vy -= dy * f;
        }
      }
      // Spring on links.
      for (const l of links) {
        let dx = l.t.x - l.s.x;
        let dy = l.t.y - l.s.y;
        const d = Math.sqrt(dx * dx + dy * dy) || 0.01;
        const f = (d - 90) * 0.02 * alpha;
        dx /= d;
        dy /= d;
        l.s.vx += dx * f;
        l.s.vy += dy * f;
        l.t.vx -= dx * f;
        l.t.vy -= dy * f;
      }
      // Integrate + center pull + damping.
      for (const s of sims) {
        s.vx += (W / 2 - s.x) * 0.0015;
        s.vy += (H / 2 - s.y) * 0.0015;
        s.x += (s.vx *= 0.85);
        s.y += (s.vy *= 0.85);
      }
      draw();
      if (alpha > 0.02) raf = requestAnimationFrame(tick);
    }

    function draw() {
      if (!ctx) return;
      ctx.clearRect(0, 0, W, H);
      ctx.strokeStyle = "rgba(148,163,184,0.25)";
      ctx.lineWidth = 1;
      for (const l of links) {
        ctx.beginPath();
        ctx.moveTo(l.s.x, l.s.y);
        ctx.lineTo(l.t.x, l.t.y);
        ctx.stroke();
      }
      for (const s of sims) {
        const r = 4 + Math.min(s.deg, 10);
        ctx.beginPath();
        ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
        ctx.fillStyle = riskRGB(s.risk);
        ctx.fill();
        if (s.deg > 2) {
          ctx.fillStyle = "#cbd5e1";
          ctx.font = "10px sans-serif";
          ctx.fillText(s.label, s.x + r + 2, s.y + 3);
        }
      }
    }

    function pick(mx: number, my: number): Sim | undefined {
      return sims.find((s) => (s.x - mx) ** 2 + (s.y - my) ** 2 < 144);
    }
    const onClick = (ev: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const hit = pick(ev.clientX - rect.left, ev.clientY - rect.top);
      if (hit && onSelect) onSelect(hit.id);
    };
    canvas.addEventListener("click", onClick);

    tick();
    return () => {
      cancelAnimationFrame(raf);
      canvas.removeEventListener("click", onClick);
    };
  }, [nodes, edges, onSelect]);

  return <canvas ref={canvasRef} className="w-full rounded-lg border border-line bg-ink-900" />;
}
