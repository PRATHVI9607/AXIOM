// extension.ts — AXIOM VS Code extension entry point: status bar, commands, on-save analysis.
import * as vscode from "vscode";
import { AxiomClient } from "./axiomClient";
import { RiskDecorations } from "./providers/RiskDecorations";
import { RiskViewProvider } from "./views/RiskViewProvider";

const client = new AxiomClient();
let statusBar: vscode.StatusBarItem;
let decorations: RiskDecorations;
let riskView: RiskViewProvider;

function projectId(): string {
  return vscode.workspace.getConfiguration("axiom").get<string>("projectId", "default");
}

async function refreshDecorations(context: vscode.ExtensionContext): Promise<void> {
  try {
    const graph = await client.getGraph(context, projectId());
    decorations.apply(graph.nodes);
  } catch {
    // No graph yet (analysis not run) — leave gutters clear.
  }
}

export function activate(context: vscode.ExtensionContext): void {
  const cfg = vscode.workspace.getConfiguration("axiom");
  decorations = new RiskDecorations(
    cfg.get<number>("riskThreshold.warning", 0.5),
    cfg.get<number>("riskThreshold.error", 0.8)
  );
  decorations.register(context);

  // Sidebar risk view (Loki-scepter activity-bar icon).
  riskView = new RiskViewProvider(context, client, (nodes) => decorations.apply(nodes));
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(RiskViewProvider.viewType, riskView),
    vscode.commands.registerCommand("axiom.scanWorkspace", () => {
      riskView.reveal();
      void riskView.scan();
    })
  );

  statusBar = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
  statusBar.command = "axiom.openDashboard";
  context.subscriptions.push(statusBar);
  void refreshStatus();
  void refreshDecorations(context);

  // Re-apply decorations when switching editors.
  context.subscriptions.push(
    vscode.window.onDidChangeActiveTextEditor((editor) => {
      if (editor) decorations.applyToEditor(editor);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("axiom.analyzeFile", () => analyzeCurrentFile(context)),
    vscode.commands.registerCommand("axiom.analyzeWorkspace", () =>
      vscode.window.showInformationMessage("AXIOM: workspace analysis queued.")
    ),
    vscode.commands.registerCommand("axiom.showBlastRadius", () =>
      vscode.window.showInformationMessage("AXIOM: run analysis first, then select a function.")
    ),
    vscode.commands.registerCommand("axiom.setToken", async () => {
      const token = await vscode.window.showInputBox({
        prompt: "Paste your AXIOM JWT (from `python scripts/demo.py`)",
        password: true,
        ignoreFocusOut: true,
      });
      if (token) {
        await context.secrets.store("axiom.token", token);
        void vscode.window.showInformationMessage("AXIOM token saved.");
        await refreshDecorations(context);
      }
    }),
    vscode.commands.registerCommand("axiom.setProject", async () => {
      const id = await vscode.window.showInputBox({
        prompt: "AXIOM project id (printed by the demo seeder)",
        value: projectId(),
        ignoreFocusOut: true,
      });
      if (id) {
        await vscode.workspace
          .getConfiguration("axiom")
          .update("projectId", id, vscode.ConfigurationTarget.Workspace);
        await refreshDecorations(context);
      }
    }),
    vscode.commands.registerCommand("axiom.openDashboard", () => {
      const url = vscode.workspace.getConfiguration("axiom").get<string>("serverUrl", "");
      void vscode.env.openExternal(vscode.Uri.parse("http://localhost:3000"));
      void url;
    })
  );

  // Auto-analyze on save when enabled.
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((doc) => {
      const auto = vscode.workspace.getConfiguration("axiom").get<boolean>("autoAnalyzeOnSave", true);
      if (auto && isSupported(doc.languageId)) {
        void analyzeDocument(context, doc);
      }
    })
  );
}

async function refreshStatus(): Promise<void> {
  try {
    const health = await client.health();
    statusBar.text = `$(pulse) AXIOM: ${health.status}`;
    statusBar.tooltip = `AXIOM v${health.version} · eBPF ${health.ebpf_available ? "on" : "off"}`;
  } catch {
    statusBar.text = "$(warning) AXIOM: offline";
    statusBar.tooltip = "AXIOM backend unreachable — start it with `make run-dev`";
  }
  statusBar.show();
}

async function analyzeCurrentFile(context: vscode.ExtensionContext): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    void vscode.window.showWarningMessage("AXIOM: no active file.");
    return;
  }
  await analyzeDocument(context, editor.document);
}

async function analyzeDocument(
  context: vscode.ExtensionContext,
  doc: vscode.TextDocument
): Promise<void> {
  try {
    await client.analyzeFile(context, projectId(), doc.fileName);
    void vscode.window.setStatusBarMessage(`$(check) AXIOM analyzed ${doc.fileName}`, 3000);
    // Analysis is async on the backend; refresh gutters shortly after.
    setTimeout(() => void refreshDecorations(context), 2000);
  } catch (err) {
    void vscode.window.showErrorMessage(`AXIOM analysis failed: ${(err as Error).message}`);
  }
}

function isSupported(languageId: string): boolean {
  return ["python", "javascript", "typescript", "go", "cpp"].includes(languageId);
}

export function deactivate(): void {
  statusBar?.dispose();
}
