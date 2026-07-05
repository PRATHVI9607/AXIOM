// axiomClient.ts — thin HTTP client for the AXIOM backend used by the extension.
import * as vscode from "vscode";

export interface HealthResponse {
  status: string;
  version: string;
  database: boolean;
  ebpf_available: boolean;
}

export interface GraphNode {
  id: string;
  label: string;
  risk_score: number;
  language: string;
  file_path: string;
  start_line: number;
  end_line: number;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: unknown[];
  total_nodes: number;
}

export class AxiomClient {
  private get baseUrl(): string {
    return vscode.workspace.getConfiguration("axiom").get<string>("serverUrl", "http://localhost:8000");
  }

  private async token(context: vscode.ExtensionContext): Promise<string | undefined> {
    return context.secrets.get("axiom.token");
  }

  async health(): Promise<HealthResponse> {
    const res = await fetch(`${this.baseUrl}/health`);
    if (!res.ok) {
      throw new Error(`Health check failed: ${res.status}`);
    }
    return (await res.json()) as HealthResponse;
  }

  async analyzeFile(
    context: vscode.ExtensionContext,
    projectId: string,
    filePath: string
  ): Promise<void> {
    const token = await this.token(context);
    const res = await fetch(`${this.baseUrl}/api/v1/analyze/file`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ project_id: projectId, file_path: filePath, force_reembed: false }),
    });
    if (!res.ok) {
      throw new Error(`Analyze failed: ${res.status}`);
    }
  }

  async getGraph(context: vscode.ExtensionContext, projectId: string): Promise<GraphResponse> {
    const token = await this.token(context);
    const res = await fetch(`${this.baseUrl}/api/v1/graph/${projectId}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!res.ok) {
      throw new Error(`Graph fetch failed: ${res.status}`);
    }
    return (await res.json()) as GraphResponse;
  }
}
