# AXIOM Code Intelligence — VS Code Extension

Inline semantic failure-risk scoring and blast-radius prediction, powered by an
AXIOM backend.

## Features
- Risk gutter dots per function (green / amber / red)
- Hover cards with the risk score
- High-risk functions in the Problems panel
- Status-bar backend indicator
- Analyze current file on save

## Setup
1. Start the AXIOM backend (`uvicorn axiom.main:app`) and analyze a project.
2. Command Palette → **AXIOM: Set API Token**, then **AXIOM: Set Project Id**.
3. Open a source file to see inline risk.

Configure the server URL via `axiom.serverUrl` (default `http://localhost:8000`).

See the repo's `SETUP.md` for the full guide.
