// RiskViewProvider.ts — AXIOM sidebar: scan the current workspace, show risk inline.
import * as vscode from "vscode";
import { AxiomClient, type GraphNode } from "../axiomClient";

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
    view.webview.html = this.shell("Click <b>Scan workspace</b> to analyze this folder.");

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
    const token = await this.context.secrets.get("axiom.token");
    if (!token) {
      this.post({ type: "needToken" });
      return;
    }

    this.post({ type: "status", message: "Analyzing workspace…" });
    try {
      const key = `axiom.project.${folder.uri.fsPath}`;
      let projectId = this.context.workspaceState.get<string>(key);
      if (!projectId) {
        projectId = await this.client.createProject(this.context, folder.name, folder.uri.fsPath);
        await this.context.workspaceState.update(key, projectId);
      }
      await this.client.analyzeWorkspace(this.context, projectId);

      // Poll until the graph is populated.
      let nodes: GraphNode[] = [];
      for (let i = 0; i < 60; i++) {
        await new Promise((r) => setTimeout(r, 1000));
        const graph = await this.client.getGraph(this.context, projectId);
        if (graph.total_nodes > 0) {
          nodes = graph.nodes;
          break;
        }
      }
      if (nodes.length === 0) {
        this.post({ type: "error", message: "No source files found in this workspace." });
        return;
      }
      const health = await this.client.getHealthScore(this.context, projectId);
      const top = [...nodes].sort((a, b) => b.risk_score - a.risk_score).slice(0, 40);
      this.post({ type: "results", health, nodes: top });
      this.onNodes(nodes); // feed gutter decorations too
    } catch (err) {
      this.post({ type: "error", message: (err as Error).message });
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

  private shell(intro: string): string {
    return /* html */ `<!doctype html><html><head><meta charset="utf-8"/>
<style>
  :root { color-scheme: dark; }
  body { font-family: var(--vscode-font-family); margin: 0; padding: 12px; color: var(--vscode-foreground); }
  h2 { font-size: 12px; text-transform: uppercase; letter-spacing: .08em; color: var(--vscode-descriptionForeground); margin: 0 0 10px; }
  button { width: 100%; padding: 8px; border: none; border-radius: 6px; cursor: pointer;
           background: var(--vscode-button-background); color: var(--vscode-button-foreground); font-size: 13px; }
  button:hover { background: var(--vscode-button-hoverBackground); }
  .intro { color: var(--vscode-descriptionForeground); font-size: 12px; margin: 12px 2px; line-height: 1.5; }
  .health { display:flex; align-items:baseline; gap:8px; margin: 14px 0 8px; }
  .score { font-size: 26px; font-weight: 600; font-variant-numeric: tabular-nums; }
  .buckets { display:flex; gap:6px; margin-bottom: 12px; }
  .chip { flex:1; text-align:center; border-radius:6px; padding:6px 0; font-size:11px; background: var(--vscode-editorWidget-background); }
  .chip b { display:block; font-size:15px; font-variant-numeric: tabular-nums; }
  ul { list-style:none; margin:0; padding:0; }
  li { display:flex; align-items:center; gap:8px; padding:6px 6px; border-radius:6px; cursor:pointer; }
  li:hover { background: var(--vscode-list-hoverBackground); }
  .dot { width:8px; height:8px; border-radius:50%; flex:none; }
  .fn { font-family: var(--vscode-editor-font-family); font-size:12px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .loc { color: var(--vscode-descriptionForeground); font-size:11px; }
  .risk { margin-left:auto; font-variant-numeric: tabular-nums; font-size:12px; font-family: var(--vscode-editor-font-family); }
  .err { color: var(--vscode-errorForeground); font-size:12px; margin: 10px 2px; }
</style></head><body>
  <h2>AXIOM — Workspace Risk</h2>
  <button id="scan">Scan workspace</button>
  <div id="content"><p class="intro">${intro}</p></div>
<script>
  const vscode = acquireVsCodeApi();
  const C = (s) => s >= 0.6 ? '#f87171' : s >= 0.3 ? '#fbbf24' : '#34d399';
  document.getElementById('scan').onclick = () => vscode.postMessage({ type: 'scan' });
  const content = document.getElementById('content');
  window.addEventListener('message', (e) => {
    const m = e.data;
    if (m.type === 'status') content.innerHTML = '<p class="intro">' + m.message + '</p>';
    else if (m.type === 'error') content.innerHTML = '<p class="err">' + m.message + '</p>';
    else if (m.type === 'needToken')
      content.innerHTML = '<p class="intro">No API token set.</p><button id="tok">Set API token</button>',
      document.getElementById('tok').onclick = () => vscode.postMessage({ type: 'setToken' });
    else if (m.type === 'results') render(m);
  });
  function render(m) {
    const h = m.health;
    const pct = Math.round(h.current_score * 100);
    let html = '<div class="health"><span class="score" style="color:' + (pct>=66?'#34d399':pct>=40?'#fbbf24':'#f87171') + '">' + pct + '</span><span class="loc">health</span></div>';
    html += '<div class="buckets">'
      + '<div class="chip" style="color:#f87171"><b>' + h.high_risk_count + '</b>high</div>'
      + '<div class="chip" style="color:#fbbf24"><b>' + h.medium_risk_count + '</b>med</div>'
      + '<div class="chip" style="color:#34d399"><b>' + h.low_risk_count + '</b>low</div></div>';
    html += '<ul>' + m.nodes.map(n => {
      const file = (n.file_path||'').replace(/\\\\/g,'/');
      const base = file.split('/').pop();
      return '<li data-p="' + file + '" data-l="' + n.start_line + '">'
        + '<span class="dot" style="background:' + C(n.risk_score) + '"></span>'
        + '<span><span class="fn">' + n.label + '</span> <span class="loc">' + base + ':' + n.start_line + '</span></span>'
        + '<span class="risk" style="color:' + C(n.risk_score) + '">' + n.risk_score.toFixed(2) + '</span></li>';
    }).join('') + '</ul>';
    content.innerHTML = html;
    content.querySelectorAll('li').forEach(li =>
      li.onclick = () => vscode.postMessage({ type: 'open', path: li.dataset.p, line: +li.dataset.l }));
  }
</script></body></html>`;
  }
}
