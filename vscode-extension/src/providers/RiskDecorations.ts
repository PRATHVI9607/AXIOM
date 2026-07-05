// RiskDecorations.ts — gutter risk dots, hover cards, and Problems-panel diagnostics.
import * as vscode from "vscode";
import type { GraphNode } from "../axiomClient";

// Reuse three colored circle decorations by risk band.
function dot(color: string): vscode.TextEditorDecorationType {
  return vscode.window.createTextEditorDecorationType({
    gutterIconPath: vscode.Uri.parse(
      "data:image/svg+xml;base64," +
        Buffer.from(
          `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14"><circle cx="7" cy="7" r="5" fill="${color}"/></svg>`
        ).toString("base64")
    ),
    gutterIconSize: "contain",
  });
}

export class RiskDecorations {
  private readonly low = dot("#22c55e");
  private readonly med = dot("#eab308");
  private readonly high = dot("#ef4444");
  private readonly diagnostics = vscode.languages.createDiagnosticCollection("axiom");
  // file_path -> nodes, used by the hover provider.
  private byFile = new Map<string, GraphNode[]>();

  constructor(private readonly warn: number, private readonly err: number) {}

  register(context: vscode.ExtensionContext): void {
    context.subscriptions.push(
      this.diagnostics,
      this.low,
      this.med,
      this.high,
      vscode.languages.registerHoverProvider("*", {
        provideHover: (doc, pos) => this.hover(doc, pos),
      })
    );
  }

  /** Update decorations for whichever open editor matches each node's file. */
  apply(nodes: GraphNode[]): void {
    this.byFile.clear();
    for (const n of nodes) {
      const key = n.file_path.replace(/\\/g, "/");
      (this.byFile.get(key) ?? this.byFile.set(key, []).get(key)!).push(n);
    }
    for (const editor of vscode.window.visibleTextEditors) {
      this.applyToEditor(editor);
    }
  }

  applyToEditor(editor: vscode.TextEditor): void {
    const key = editor.document.fileName.replace(/\\/g, "/");
    const nodes = this.matchNodes(key);
    const low: vscode.Range[] = [];
    const med: vscode.Range[] = [];
    const high: vscode.Range[] = [];
    const diags: vscode.Diagnostic[] = [];

    for (const n of nodes) {
      const line = Math.max(0, n.start_line - 1);
      const range = new vscode.Range(line, 0, line, 0);
      if (n.risk_score >= 0.6) high.push(range);
      else if (n.risk_score >= 0.3) med.push(range);
      else low.push(range);

      if (n.risk_score >= this.warn) {
        const sev =
          n.risk_score >= this.err
            ? vscode.DiagnosticSeverity.Error
            : vscode.DiagnosticSeverity.Warning;
        diags.push(
          new vscode.Diagnostic(range, `AXIOM risk ${n.risk_score.toFixed(2)}: ${n.label}`, sev)
        );
      }
    }
    editor.setDecorations(this.low, low);
    editor.setDecorations(this.med, med);
    editor.setDecorations(this.high, high);
    this.diagnostics.set(editor.document.uri, diags);
  }

  private matchNodes(fileKey: string): GraphNode[] {
    // Match by suffix so absolute-vs-relative paths still line up.
    for (const [key, nodes] of this.byFile) {
      if (fileKey.endsWith(key) || key.endsWith(fileKey)) return nodes;
    }
    return [];
  }

  private hover(doc: vscode.TextDocument, pos: vscode.Position): vscode.Hover | undefined {
    const nodes = this.matchNodes(doc.fileName.replace(/\\/g, "/"));
    const hit = nodes.find((n) => pos.line + 1 >= n.start_line && pos.line + 1 <= n.end_line);
    if (!hit) return undefined;
    const md = new vscode.MarkdownString(
      `**AXIOM** \`${hit.label}\`\n\nRisk score: **${hit.risk_score.toFixed(2)}**`
    );
    return new vscode.Hover(md);
  }
}
