# P11: `qmx-control`, one service layer with a REST door and an MCP door

## Goal
One Python service layer that both the UI (REST/SSE) and the Copilot (MCP) call. New work uses it instead of the hand-written HTTP/WebSocket server.

## Read first
- `rebuild/DESIGN.md` §8
- `C:\Users\Mubarak\Desktop\QMX-session-for-Codex\BACKEND-REQUIREMENTS.md` (what the UI needs)
- `rebuild/research/ui-model-and-baseline-audit.md` §1.9

## Build (package `qmx_control`)
- **Service layer:** plain Python functions for:
  - apps: list, get, create, update, versions, test, publish, start, stop, logs, evidence
  - workflows: get, put, validate, run
  - runs and jobs: list, cancel
  - library: search, save
  - settings: get and put for providers, MCP servers, budgets and the memory provider
  - copilot sessions: create, list, append, stream
- **REST door:** FastAPI routes for each function, plus an SSE stream for run, job and session events. The OpenAPI document is generated and used by the UI.
- **MCP door:** a FastMCP server exposing the same functions as tools. Destructive tools are flagged for `interrupt_on`.
- **Auth:**
  - A local bearer token is created on first run and stored in Credential Manager as `qmx/control-token`.
  - CORS is limited to the UI origin.
- Until P12–P14 exist, app and workflow functions return an honest `not_implemented` error, never a fake success.

## Tests
- REST and MCP give identical results for the same call.
- Auth is required.
- SSE delivers events.
- `not_implemented` shows up clearly to the caller.
