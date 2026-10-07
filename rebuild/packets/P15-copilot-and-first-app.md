# P15: Copilot agent and first end-to-end app

## Goal
The Copilot is a Deep Agent that builds, runs and inspects mini apps and workflows through `qmx-control`. One real app goes from description to Live.

## Read first
- `rebuild/DESIGN.md` §5.2, §7, §8
- `rebuild/research/research-harness.md` §F and §G
- `rebuild/research/ui-model-and-baseline-audit.md` §1.6 (session blocks the UI expects)

## Build
- **`agents/copilot.yaml`:**
  - model tier `reasoning_high` for planning, `workhorse` for execution
  - MCP: `qmx-control`, `qmx-data`, `qmx-backtest`, `qmx-research`, plus operator-added servers
  - skills: `build-mini-app`, `build-workflow`, `debug-app`. Write them as Agent Skills folders, short and practical.
  - sync sub-agents: `researcher`, `data-analyst` (Python sandbox backend, RLM-style prompt), `app-builder`
  - background task (DESIGN §12b): `overnight-builder`
  - interrupts: `publish_app`, `start_live`, global memory writes
  - memory scope: session, plus global (approval)
- **Session log:** the Copilot run is mapped onto the UI's typed block list (text, plan, agents, tool calls, artifact, question, permission, panel draft) and streamed via SSE from `qmx-control`.
- **First app, "Macro daily bias":**
  - an agent app with screens, on a schedule
  - reads data via `qmx-data`
  - an agent summarises the drivers
  - writes the bias plus a rationale to `app.db`
  - shows a tier-1 panel
  - goes Build → Live as a *shows things* app
- `scripts/live/copilot_build_app.py`: the operator runs this with real keys to watch the Copilot build the app from a one-paragraph description.

## Tests
- With fake models, a scripted Copilot run creates, tests and publishes the example app through `qmx-control` only (no back doors).
- Interrupts fire on publish.
- The session stream contains the expected block types.
