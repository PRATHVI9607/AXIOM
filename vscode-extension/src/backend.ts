// backend.ts — detect / auto-start a local AXIOM backend for the extension.
import { spawn, type ChildProcess } from "child_process";
import * as fs from "fs";
import * as path from "path";
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

interface Cmd {
  cmd: string;
  args: string[];
  cwd?: string;
}

/** Candidate commands to launch a local backend, tried in order. */
function candidates(): Cmd[] {
  const p = port();
  const win = process.platform === "win32";
  const bin = win ? "Scripts" : "bin";
  const exe = (n: string) => (win ? `${n}.exe` : n);
  const list: Cmd[] = [];

  const configured = cfg().get<string>("backendCommand", "").trim();
  if (configured) {
    const parts = configured.split(/\s+/);
    list.push({ cmd: parts[0], args: [...parts.slice(1), "--port", p] });
  }

  // A python interpreter the user pointed us at (must have `axiom` installed).
  const pyPath = cfg().get<string>("pythonPath", "").trim();
  if (pyPath) list.push({ cmd: pyPath, args: ["-m", "axiom.cli", "serve", "--port", p] });

  // Walk up from each workspace folder looking for a .venv with axiom in it.
  for (const folder of vscode.workspace.workspaceFolders ?? []) {
    let dir = folder.uri.fsPath;
    for (let up = 0; up < 4; up++) {
      const venv = path.join(dir, ".venv", bin);
      const axiomExe = path.join(venv, exe("axiom"));
      const pythonExe = path.join(venv, exe("python"));
      if (fs.existsSync(axiomExe)) list.push({ cmd: axiomExe, args: ["serve", "--port", p], cwd: dir });
      else if (fs.existsSync(pythonExe))
        list.push({ cmd: pythonExe, args: ["-m", "axiom.cli", "serve", "--port", p], cwd: dir });
      const parent = path.dirname(dir);
      if (parent === dir) break;
      dir = parent;
    }
  }

  // Installed via `pip install axiom` — the console script on PATH (shell resolves it).
  list.push({ cmd: exe("axiom"), args: ["serve", "--port", p] });
  list.push({ cmd: "python", args: ["-m", "axiom.cli", "serve", "--port", p] });
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
      const tried = candidates();
      log().appendLine(`Looking for a backend (${tried.length} candidates)…`);
      for (const { cmd, args, cwd } of tried) {
        try {
          log().appendLine(`  spawn: ${cmd} ${args.join(" ")}${cwd ? `  (cwd ${cwd})` : ""}`);
          const child = spawn(cmd, args, { env, cwd, shell: false });
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
      log().appendLine("No backend could be started. Install `axiom` (pip install axiom) or set axiom.pythonPath / axiom.serverUrl.");
      log().show(true);
      void vscode.window
        .showErrorMessage(
          "AXIOM: could not start a backend. Install `axiom` or set axiom.pythonPath.",
          "Show log"
        )
        .then((c) => c === "Show log" && log().show(true));
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
