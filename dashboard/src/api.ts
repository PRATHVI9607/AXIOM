// api.ts — typed client for the AXIOM REST API (proxied to :8000 in dev).
export interface HealthResponse {
  status: string;
  version: string;
  database: boolean;
  ebpf_available: boolean;
  embed_provider: string;
  air_gapped: boolean;
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

export interface BlastEntry {
  function_id: string;
  function_name: string;
  file_path: string;
  risk_score: number;
  failure_path: string[];
  failure_reason: string;
}

export interface FunctionAnalysis {
  function_id: string;
  function_name: string;
  risk_score: number;
  blast_radius: BlastEntry[];
  analysis_time_ms: number;
}

export interface GraphEdge {
  source: string;
  target: string;
  type: string;
  weight: number;
}

export interface GraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  page: number;
}

export interface HealthScore {
  current_score: number;
  high_risk_count: number;
  medium_risk_count: number;
  low_risk_count: number;
}

const BASE = "/api/v1";

function authHeaders(): HeadersInit {
  const token = localStorage.getItem("axiom_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(path.startsWith("/health") ? path : `${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...authHeaders(), ...init.headers },
  });
  if (!res.ok) {
    throw new Error(`${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<HealthResponse>("/health"),
  graph: (projectId: string) => request<GraphResponse>(`/graph/${projectId}`),
  health_score: (projectId: string) => request<HealthScore>(`/graph/${projectId}/health`),
  analyzeFunction: (projectId: string, functionId: string) =>
    request<FunctionAnalysis>("/analyze/function", {
      method: "POST",
      body: JSON.stringify({ project_id: projectId, function_id: functionId }),
    }),
};
