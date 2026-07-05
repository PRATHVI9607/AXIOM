// backend.ts — detect / auto-start a local AXIOM backend for the extension.
import { spawn, type ChildProcess } from "child_process";
import * as vscode from "vscode";

let proc: ChildProcess | undefined;
let output: vscode.OutputChannel | undefined;

function log(): vscode.OutputChannel {
  if (!output) output = vscode.window.createOutputChannel("AXIOM Backend");
  return output;
}

function cfg() {
  return vscode.workspace.getConfiguration("axiom");
}

export function serverUrl(): string {
  return cfg().get<string>("serverUrl", "http://localhost:8000");
}

function port(): string {
  try {
    return new URL(serverUrl()).port || "8000";
  } catch {
    return "8000";
  }
}

export async function isBackendUp(timeoutMs = 1500): Promise<boolean> {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(`${serverUrl()}/health`, { signal: ctrl.signal });
    return res.ok;
  } catch {
    return false;
  } finally {
    clearTimeout(t);
  }
}

/** Candidate commands to launch a local backend, tried in order. */
function candidates(): { cmd: string; args: string[] }[] {
  const p = port();
  const configured = cfg().get<string>("backendCommand", "").trim();
  const list: { cmd: string; args: string[] }[] = [];
  if (configured) {
    const parts = configured.split(/\s+/);
    list.push({ cmd: parts[0], args: [...parts.slice(1), "--port", p] });
  }
  // Installed via `pip install axiom` — the console script on PATH.
  list.push({ cmd: process.platform === "win32" ? "axiom.exe" : "axiom", args: ["serve", "--port", p] });
  list.push({ cmd: "axiom", args: ["serve", "--port", p] });
  return list;
}

/** Ensure a backend is reachable; auto-start one if configured. Returns up/down. */
export async function ensureBackend(): Promise<boolean> {
  if (await isBackendUp()) return true;
  if (!cfg().get<boolean>("autoStartBackend", true)) return false;
  if (proc && !proc.killed) {
    return waitForHealth(30);
  }

  const env = { ...process.env };
  env.AXIOM_EMBED_PROVIDER = env.AXIOM_EMBED_PROVIDER || cfg().get<string>("embedProvider", "local");

  return vscode.window.withProgress(
    { location: vscode.ProgressLocation.Notification, title: "Starting AXIOM backend…" },
    async () => {
      for (const { cmd, args } of candidates()) {
        try {
          const child = spawn(cmd, args, { env, shell: false });
          proc = child;
          child.stdout?.on("data", (d) => log().append(String(d)));
          child.stderr?.on("data", (d) => log().append(String(d)));
          const spawned = await new Promise<boolean>((resolve) => {
            child.once("error", () => resolve(false)); // ENOENT — try next candidate
            setTimeout(() => resolve(true), 800);
          });
          if (!spawned) {
            proc = undefined;
            continue;
          }
          if (await waitForHealth(30)) return true;
        } catch {
          proc = undefined;
        }
      }
      void vscode.window.showErrorMessage(
        "AXIOM: could not start a backend. Install it (`pip install -e .`) or set `axiom.serverUrl` to a running server."
      );
      return false;
    }
  );
}

async function waitForHealth(seconds: number): Promise<boolean> {
  for (let i = 0; i < seconds; i++) {
    if (await isBackendUp(1000)) return true;
    await new Promise((r) => setTimeout(r, 1000));
  }
  return false;
}

export function stopBackend(): void {
  if (proc && !proc.killed) {
    proc.kill();
    proc = undefined;
  }
}
