# P12: Mini-app definition, volume and T1 supervisor

## Goal
Mini apps work like Docker on the operator's laptop:
- definition = image
- instance = container
- data folder = volume

Every app is an MCP server.

## Read first
- `rebuild/DESIGN.md` §7.1, §7.3, §7.5, §7.7
- `rebuild/research/research-memory-storage.md` §E
- `rebuild/research/miniapp-concept.md` §A
- `rebuild/research/ui-model-and-baseline-audit.md` §1.4–1.5 (what the Apps screen shows)

## Build (package `qmx_apps`)
1. **`manifest`**: the `app.toml` schema (pydantic). It declares:
   - id, name, version
   - risk class: shows | runs | money
   - kind: screens | headless | both
   - entrypoints: `mcp` (the tools module), optional `jobs`, optional `agents/*.yaml`, optional `workflows/*.json`, optional `ui/`
   - capabilities: network allow-list, secrets, data it reads
   - schedule, budget, circuit-breaker rule
   - provides and feeds: output and input artifact JSON Schemas

   Definitions are content-hashed and versioned.
2. **`volume`**: creates and opens `<qmx_home>/apps/<id>/` containing `app.db`, `memory.db` (only if the app has agents), `data/`, `blobs/`, `logs/`.
3. **`supervisor`** (T1):
   - `install(definition)`: builds a per-app `uv` venv from the app's lock.
   - `start` / `stop` / `restart` / `status`.
   - Each instance runs as a subprocess with:
     - the volume as its working directory and only writable root
     - an environment scrubbed down to the declared secrets
     - Windows Job Object limits for memory and CPU (use `pywin32` or `psutil`; document the fallback on Linux)
   - Heartbeat, structured JSONL logs in `logs/`, metrics (runs, errors, budget used), and a circuit breaker that stops the instance on a rule breach and records why.
   - Egress: declared and logged in T1. It is enforced in T2 (P17).
4. **MCP:** the instance serves its tools over stdio (local) or streamable HTTP. The supervisor keeps a registry of running app servers. `qmx-control` (P11) exposes it, and the Copilot connects to it.
5. **App to app:** outputs are written as artifacts in the producing app's `blobs/` and registered in an artifact index. The returned reference is checked against the declared `provides` schema. Consumers take references, never live connections.
6. Fill in the P11 `apps.*` functions with real implementations.

## Example apps (in `examples/apps/`)
- `exchange-status`: a tool/data app with screens, no agents.
- `weekend-watcher`: a headless agent app that summarises and writes an artifact.

## Tests
- manifest validation
- install/start/stop on Windows
- the breaker trips on a budget breach
- the environment does not leak undeclared secrets
- writes outside the volume are refused (supervisor check)
- an MCP tool call works through the supervisor registry
- an artifact reference passes from app A to app B
