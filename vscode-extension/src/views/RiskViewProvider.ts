// RiskViewProvider.ts — AXIOM sidebar: scan the current workspace, show risk inline.
import * as vscode from "vscode";
import { AxiomClient, type GraphNode } from "../axiomClient";
import { ensureBackend } from "../backend";

export class RiskViewProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "axiom.riskView";
  private view?: vscode.WebviewView;

  constructor(
    private readonly context: vscode.ExtensionContext,
    private readonly client: AxiomClient,
    private readonly onNodes: (nodes: GraphNode[]) => void
  ) {}

  resolveWebviewView(view: vscode.WebviewView): void {
    this.view = view;
    view.webview.options = { enableScripts: true };
    view.webview.html = this.shell();

    view.webview.onDidReceiveMessage(async (msg) => {
      if (msg.type === "scan") await this.scan();
      else if (msg.type === "setToken") await vscode.commands.executeCommand("axiom.setToken");
      else if (msg.type === "open") this.openFile(msg.path, msg.line);
    });
  }

  reveal(): void {
    this.view?.show?.(true);
  }

  async scan(): Promise<void> {
    const folder = vscode.workspace.workspaceFolders?.[0];
    if (!folder) {
      this.post({ type: "error", message: "Open a folder first." });
      return;
    }

    this.post({ type: "status", message: "Starting backend…" });
    if (!(await ensureBackend())) {
      this.post({ type: "error", message: "No AXIOM backend. Install it or set axiom.serverUrl." });
      return;
    }

    this.post({ type: "status", message: "Analyzing workspace…" });
    try {
      const key = `axiom.project.${folder.uri.fsPath}`;
      let projectId = this.context.workspaceState.get<string>(key);

      // Create (or recreate a stale) project, then kick off analysis.
      const startAnalysis = async (): Promise<string> => {
        if (!projectId) {
          projectId = await this.client.createProject(this.context, folder.name, folder.uri.fsPath);
          await this.context.workspaceState.update(key, projectId);
        }
        try {
          await this.client.analyzeWorkspace(this.context, projectId);
        } catch (e) {
          // Cached id points at a project this backend/DB doesn't have — recreate once.
          if ((e as Error).message.includes("404")) {
            projectId = await this.client.createProject(this.context, folder.name, folder.uri.fsPath);
            await this.context.workspaceState.update(key, projectId);
            await this.client.analyzeWorkspace(this.context, projectId);
          } else {
            throw e;
          }
        }
        return projectId;
      };
      const pid = await startAnalysis();

      // Poll until the graph is populated. The graph endpoint 404s until analysis
      // finishes, so tolerate errors and keep waiting.
      let nodes: GraphNode[] = [];
      for (let i = 0; i < 90; i++) {
        await new Promise((r) => setTimeout(r, 1000));
        try {
          const graph = await this.client.getGraph(this.context, pid);
          if (graph.total_nodes > 0) {
            nodes = graph.nodes;
            break;
          }
        } catch {
          /* not ready yet — keep polling */
        }
        if (i % 3 === 0) this.post({ type: "status", message: `Analyzing workspace… (${i}s)` });
      }
      if (nodes.length === 0) {
        this.post({
          type: "error",
          message: "No results — the folder may have no supported source files, or analysis is still running. Try again.",
        });
        return;
      }
      const health = await this.client.getHealthScore(this.context, pid);
      const top = [...nodes].sort((a, b) => b.risk_score - a.risk_score).slice(0, 40);
      this.post({ type: "results", health, nodes: top });
      this.onNodes(nodes); // feed gutter decorations too
    } catch (err) {
      const message = (err as Error).message;
      if (message.includes("401")) {
        // Backend has auth enabled — ask for a token.
        this.post({ type: "needToken" });
      } else {
        this.post({ type: "error", message });
      }
    }
  }

  private openFile(path: string, line: number): void {
    vscode.workspace.openTextDocument(vscode.Uri.file(path)).then((doc) => {
      vscode.window.showTextDocument(doc).then((editor) => {
        const pos = new vscode.Position(Math.max(0, line - 1), 0);
        editor.selection = new vscode.Selection(pos, pos);
        editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
      });
    });
  }

  private post(msg: unknown): void {
    this.view?.webview.postMessage(msg);
  }

  private shell(): string {
    return /* html */ `<!doctype html><html><head><meta charset="utf-8"/>
<style>
  :root { color-scheme: dark; --r:#f87171; --y:#fbbf24; --g:#34d399; }
  * { box-sizing: border-box; }
  body { font-family: var(--vscode-font-family); margin: 0; padding: 12px 12px 20px; color: var(--vscode-foreground); font-size: 13px; }
  .bar { display:flex; gap:8px; margin-bottom: 12px; }
  button.scan { flex:1; display:flex; align-items:center; justify-content:center; gap:7px;
    padding:7px 10px; border:none; border-radius:6px; cursor:pointer; font-size:13px; font-weight:500;
    background: var(--vscode-button-background); color: var(--vscode-button-foreground); }
  button.scan:hover { background: var(--vscode-button-hoverBackground); }
  button.scan:active { transform: translateY(1px); }
  button.scan svg { width:14px; height:14px; }
  button.ghost { background:transparent; border:1px solid var(--vscode-input-border,#3a3a3a);
    color:var(--vscode-foreground); border-radius:6px; padding:6px 10px; cursor:pointer; font-size:12px; }
  button.ghost:hover { background: var(--vscode-list-hoverBackground); }

  .empty { text-align:center; color: var(--vscode-descriptionForeground); padding: 34px 8px; }
  .empty svg { opacity:.4; margin-bottom:10px; }
  .empty .t { font-size:13px; color: var(--vscode-foreground); margin-bottom:4px; }
  .empty .h { font-size:11.5px; line-height:1.5; }
  .status { display:flex; align-items:center; gap:8px; color: var(--vscode-descriptionForeground); font-size:12px; padding: 20px 4px; }
  .spinner { width:12px; height:12px; border:2px solid var(--vscode-descriptionForeground); border-top-color:transparent; border-radius:50%; animation:spin .8s linear infinite; }
  @keyframes spin { to { transform: rotate(360deg); } }
  .err { color: var(--vscode-errorForeground); font-size:12px; padding: 14px 4px; line-height:1.5; }

  .health { display:flex; align-items:baseline; gap:8px; margin: 4px 2px 10px; }
  .score { font-size: 30px; font-weight: 600; font-variant-numeric: tabular-nums; line-height:1; }
  .sub { color: var(--vscode-descriptionForeground); font-size:11px; }
  .buckets { display:flex; gap:6px; margin-bottom: 14px; }
  .chip { flex:1; text-align:center; border-radius:6px; padding:7px 0; background: var(--vscode-editorWidget-background,#1e1e1e); }
  .chip b { display:block; font-size:16px; font-variant-numeric: tabular-nums; line-height:1.1; }
  .chip span { font-size:10px; text-transform:uppercase; letter-spacing:.06em; color: var(--vscode-descriptionForeground); }
  .listhead { font-size:10.5px; text-transform:uppercase; letter-spacing:.07em; color: var(--vscode-descriptionForeground); margin: 2px 2px 6px; }
  ul { list-style:none; margin:0; padding:0; }
  li { display:flex; align-items:center; gap:9px; padding:6px 7px; border-radius:6px; cursor:pointer; }
  li:hover { background: var(--vscode-list-hoverBackground); }
  .dot { width:7px; height:7px; border-radius:50%; flex:none; }
  .meta { min-width:0; flex:1; }
  .fn { font-family: var(--vscode-editor-font-family); font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .loc { color: var(--vscode-descriptionForeground); font-size:10.5px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .risk { margin-left:auto; font-variant-numeric: tabular-nums; font-size:12px; font-family: var(--vscode-editor-font-family); }
</style></head><body>
  <div class="bar">
    <button class="scan" id="scan">
      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="7" cy="7" r="4.5"/><path d="M10.5 10.5 L14 14" stroke-linecap="round"/></svg>
      Scan workspace
    </button>
  </div>
  <div id="content"></div>
<script>
  const vscode = acquireVsCodeApi();
  const C = (s) => s >= 0.6 ? 'var(--r)' : s >= 0.3 ? 'var(--y)' : 'var(--g)';
  const esc = (s) => String(s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const content = document.getElementById('content');
  document.getElementById('scan').onclick = () => vscode.postMessage({ type: 'scan' });

  const scepter = '<svg width="34" height="34" viewBox="0 0 24 24" fill="currentColor"><path d="M12 1.5 L15.2 5.5 L12 11 L8.8 5.5 Z"/><rect x="7.5" y="10.4" width="9" height="1.7" rx="0.8"/><rect x="11.1" y="12" width="1.8" height="10.5" rx="0.9"/><circle cx="12" cy="22.6" r="1.2"/></svg>';
  const intro = () => '<div class="empty">' + scepter + '<div class="t">Scan this workspace</div><div class="h">Analyzes the open folder and ranks every function by failure risk. The backend starts automatically.</div></div>';
  content.innerHTML = intro();

  window.addEventListener('message', (e) => {
    const m = e.data;
    if (m.type === 'status') content.innerHTML = '<div class="status"><span class="spinner"></span>' + esc(m.message) + '</div>';
    else if (m.type === 'error') content.innerHTML = '<div class="err">' + esc(m.message) + '</div>';
    else if (m.type === 'needToken') {
      content.innerHTML = '<div class="empty"><div class="t">API token needed</div><div class="h">This server requires authentication.</div><br><button class="ghost" id="tok">Set API token</button></div>';
      document.getElementById('tok').onclick = () => vscode.postMessage({ type: 'setToken' });
    } else if (m.type === 'results') render(m);
  });

  function render(m) {
    const h = m.health, pct = Math.round(h.current_score * 100);
    const col = pct>=66?'var(--g)':pct>=40?'var(--y)':'var(--r)';
    let html = '<div class="health"><span class="score" style="color:'+col+'">'+pct+'</span><span class="sub">/ 100 health</span></div>';
    html += '<div class="buckets">'
      + '<div class="chip"><b style="color:var(--r)">'+h.high_risk_count+'</b><span>high</span></div>'
      + '<div class="chip"><b style="color:var(--y)">'+h.medium_risk_count+'</b><span>med</span></div>'
      + '<div class="chip"><b style="color:var(--g)">'+h.low_risk_count+'</b><span>low</span></div></div>';
    html += '<div class="listhead">Highest risk · '+m.nodes.length+'</div><ul>' + m.nodes.map(n => {
      const file = (n.file_path||'').replace(/\\\\/g,'/'), base = file.split('/').pop();
      return '<li data-p="'+esc(file)+'" data-l="'+n.start_line+'">'
        + '<span class="dot" style="background:'+C(n.risk_score)+'"></span>'
        + '<span class="meta"><div class="fn">'+esc(n.label)+'</div><div class="loc">'+esc(base)+':'+n.start_line+'</div></span>'
        + '<span class="risk" style="color:'+C(n.risk_score)+'">'+n.risk_score.toFixed(2)+'</span></li>';
    }).join('') + '</ul>';
    content.innerHTML = html;
    content.querySelectorAll('li').forEach(li =>
      li.onclick = () => vscode.postMessage({ type: 'open', path: li.dataset.p, line: +li.dataset.l }));
  }
</script></body></html>`;
  }
}
