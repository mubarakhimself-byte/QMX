---
label: qma-v2:h3-code-map
created: 2026-10-13
source: origin/rebuild/base @ 4eac8f69 (PR #70, last P16c PR), read in the detached worktree D:/QMX-worktrees/harness-survey (left in place)
ui-source: local branch ui-review/repair @ 1cc66208 (worktree C:/Users/Mubarak/Desktop/QMX-worktrees/ui-review-repair)
method: one agent, no sub-agents. Code read plus targeted runs: an import probe, the native-session tests, the qmx-control suite, scripts/dev/qma_callers.py, PyPI metadata. No full `just ci`.
verifies: HOW-WHY.md :12-29 and :401-452, research/24, BACKLOG B1-B7, ARCHITECTURE §2.0-2.6, §2.12, §5
---

# H3: code map for the QMA v2 harness

## Summary

1. Two uv workspaces on Python 3.14: the root (QMF, QML, QMB, QMN) and the nested `qmx-agents/` workspace (old QMA, LangChain core, platform packages). The harness belongs in the nested one.
2. `qmb host start` already runs `qmx-control`, not the old daemon. The daemon is not started by any live command path. Only QMB tests, one QMN example and the daemon's own tests still import or spawn it.
3. `qmx-control` serves 52 operations on REST and MCP, plus SSE, sign and health. Sessions and typed blocks work. There is no turn route and no approvals route. Workflows answer 501. Cancel answers 501 after a restart.
4. B1 is real and worse than written. Every call opens a fresh SQLite connection. The `qmx-tools` MCP children also open their own `ControlService` on the same home, so two processes write `control.db`. SQLite is 3.50.4 (checked).
5. The UI on `ui-review/repair` calls no backend at all. It runs on a demo store, and its block names differ from the backend's in 4 of 14 kinds. The branch was never pushed.
6. The LangChain core (`qmx_agents`, 4,090 lines) never ran against a real model. `qmx-apps` and `qmx-remote` import it, so `import qmx_apps` loads LangChain and Deep Agents (checked).
7. Old QMA is 113,347 source lines plus 69,721 test lines. Its suite takes 579 s of the ~29 min `just ci` (PR #70 table).
8. The only Claude SDK recipe is `native_claude.py`. Keep its preflight, isolation and event loop. Drop its lockdown.
9. Correction to F10: `claude-agent-sdk==0.2.163` is pinned in the qmx-agents workspace dev group (`qmx-agents/pyproject.toml:54`), not by the daemon. Deleting the daemon does not drop it. `openai-agents` is in no lockfile.
10. New trap: 0.2.163 has no Windows wheel, so no bundled CLI. The SDK runs whatever `claude` is on PATH (2.1.296 here), not the 2.1.286 it was reviewed with.
11. New trap: inside a Claude Code session `ANTHROPIC_BASE_URL` is set. 31 of 60 native-session tests fail with it set and all 60 pass without it (checked).
12. Delete nothing in the scaffold packet. Run three deletion PRs after their replacements land (§4). D1 and D3 need the operator's go.

## 1. Workspace layout

Python 3.14 (`.python-version`; 3.14.6 installed). uv 0.12.9 locally; CI pins uv 0.12.6 (`.github/workflows/battery.yml`). just 1.58.0.

**Root workspace** `pyproject.toml:92` members `packages/*, extensions/*, qml, qmb, qmn`. The lock holds no agent SDKs.

| Package | Purpose (its own description) | src lines | test lines |
|---|---|---:|---:|
| packages/qmf-core | money/time primitives, refusals, serializer | 4,594 | 3,654 |
| packages/qmf-data | data roles, journals, sources, backup | 15,678 | 10,823 |
| packages/qmf-indicators | indicator protocol over TA-Lib | 7,352 | 5,420 |
| packages/qmf-registry | records, ids, lineage, promotion | 3,844 | 3,239 |
| packages/qmf-risk | Book, BMS, exits, risk arithmetic | 17,704 | 9,836 |
| packages/qmf-structure | chart-object families | 5,044 | 3,904 |
| packages/qmf-venue | venue seam, cTrader translation | 10,963 | 7,871 |
| extensions/qmf-calendar-forex | market-hours calendar | 793 | 508 |
| qml | bot-authoring library | 16,485 | 12,229 |
| qmb | backtesting library plus `qmb` CLI | 92,255 | 48,130 |
| qmn | trading node | 98,063 | 42,222 |

**Nested workspace** `qmx-agents/pyproject.toml:17` (9 members, its own `uv.lock`, path edges into root packages at `:32-43`). Default groups are `dev` and `qma-runtime` (`:14`, `:64`).

| Package | Purpose | src | tests | Fate |
|---|---|---:|---:|---|
| qma-core | old QMA ontology, ports | 23,808 | 7,791 | delete (D1) |
| qma-wire | old wire envelope, schemas | 15,435 | 7,224 | delete (D1) |
| qma-daemon | old runtime, native SDK drivers | 74,104 | 54,706 | delete (D1) after copying the recipe |
| qmx-agents | LangChain/LangGraph/Deep Agents core | 4,090 | 3,279 | move neutral guards, then delete (D2) |
| qmx-tools | 13 domain functions, 4 FastMCP servers | 591 | 275 | keep; drop LangChain wrapper |
| qmx-control | REST + MCP service, host CLI | 2,138 | 1,597 | keep; harness plugs in here |
| qmx-apps | mini-app supervisor, road to live | 3,054 | 1,875 | keep; fix 4 imports |
| qmx-broker | broker reads, order proposals | 846 | 594 | keep |
| qmx-remote | remote runs, results store | 1,369 | 488 | keep; replace worker executors |

Other trees: `apps/qmx-ui` on rebuild/base is the old UI wired to the dead CT-40 wire (`src/lib/host/wireClient.ts:12` `LIVE_CT40_SERVER_AT_INSPECT = false`). `qmx-agents/plugins/` holds 5 old desk packs. `examples/apps/` holds 4 mini apps. `adws/` holds the SSSF factory.

**`just ci`** = `uv run python tools/ci.py` (`justfile:208-209`). Steps (`tools/ci.py:23-38`):
1. `uv sync --frozen` at the root, then `uv sync --frozen --all-packages --all-groups` in `qmx-agents`.
2. `fmt-check`, `lint` and `types` via `python -m poethepoet` in 8 workspaces: root, qmx-agents root, qmx-agents, qmx-control, qmx-tools, qmx-apps, qmx-broker, qmx-remote.
3. `money-path-scan` and `secret-scan` at the root.
4. `tools/test_all.py`.

**Tests.** Every package has its own `tests/`. `tools/test_all.py:57-127` runs these suites in their owning env: QMF/QML/QMB/QMN, tools, adws, QMA (`qmx-agents: pytest packages tests`), qmx-agents, qmx-tools, qmx-control, qmx-apps, qmx-broker, qmx-remote, QA gates and `qa/tests/epic_*`. Each runs `-n 2 -m "not serial"`, then the `serial` tests alone (`:133-149`). `qa/integration/` is not run by CI. Lint and types: ruff (root 0.16.3, qmx-agents 0.16.5) and pyright 1.1.411 strict with platform Windows. The adws gate uses mypy. Root `poe check` and the qmx-agents `poe test` both enforce 80 % coverage. The qmx-agents gate covers only `qma-*` (`qmx-agents/pyproject.toml:137`).

## 2. Integration surface

Path key: `ctl/` = `qmx-agents/packages/qmx-control/src/qmx_control/`.

**Start-up chain.**
1. `qmb host start|status|stop` (`qmb/src/qmb/doors/cli/__init__.py:1691-1721`) calls `control_host` (`qmb/src/qmb/doors/cli/host.py:1785-1836`).
2. That runs `uv run --project qmx-agents/packages/qmx-control --package qmx-control --frozen python -m qmx_control start --port 8766`.
3. `ctl/__main__.py:47-109` spawns `python -m qmx_control serve` detached with `CREATE_NO_WINDOW` and logs to `~/.qmx/control.log`.
4. It polls `/api/health` with the bearer token, checks that the pid belongs to it, and writes `~/.qmx/control-process.json`.
5. `serve` runs uvicorn on 127.0.0.1:8766 with CORS for `http://127.0.0.1:5173` (`:39-45`, `ctl/server.py:239-251`).

The token lives in the keyring as `qmx/control-token` (`server.py:84-90`). The T2 node has its own entry point, `qmx = qmx_control.node:main`, with its own `control.db`.

**Routes.** `OPERATIONS` (`server.py:28-81`) has 52 rows. Each row is wired to both REST (`:206-213`) and MCP (`:120-129`); `destructiveHint` maps to `interrupt_on`. REST-only extras: `POST /api/apps/{id}/sign` (operator door, `:184-196`), `GET /api/events/{topic}` SSE (`:215-228`) and `GET /api/health` (`:230-232`). MCP is mounted at `/mcp`. `BearerGate` protects everything (`:93-117`).

| Area | Status |
|---|---|
| sessions_create, sessions_list, sessions_append, sessions_stream | work (`ctl/service.py:300-342`) |
| turns (run an agent turn) | missing; no route and no caller |
| approvals (list, answer) | missing; `permission` blocks exist but nothing reads an answer |
| workflows get, put, validate, run | 501 `not_implemented` (`service.py:880-894` via `_unavailable` at `:643-647`) |
| runs_cancel, jobs_cancel | 501 when no in-memory canceller exists, e.g. after a restart (`:621-623`, `_cancellers` at `:106`) |
| apps_*, library_*, runs_*, jobs_*, backup, settings, portfolio | work |

**Databases** under `home` (default `~/.qmx`, `server.py:255-256`):

| File | Tables | Code |
|---|---|---|
| control.db (WAL) | sessions, blocks, work, events | `service.py:118-149` |
| runs.db (WAL) | runs, journals | `ctl/runs.py:20-28` |
| library.db (WAL) | the Library | `ctl/library.py:27-64` |
| apps/<id>/app.db | per-app volumes | qmx-apps |

There is no migration framework.

**B1, verified.** SQLite 3.50.4 runs under CPython 3.14.6 (probe). Writers come from three places:
- Every method opens a new connection (`service.py:151-154`, `runs.py:31`, `:143`, `library.py:63-64`). `_aggregate_counts` opens `runs.db` inside a `control.db` transaction (`service.py:416-429`).
- FastAPI runs sync endpoints on its thread pool, and the lifespan loop calls `runs_list` and `backup_weekly` from a thread every 60 s (`server.py:152-165`). `self._lock` covers only some writes.
- Each `qmx-tools` FastMCP child builds its own `ControlService` on the same home (`qmx-tools/src/qmx_tools/service.py:126-128`, root from `QMX_TOOLS_ROOT` or `~/.qmx` at `:257`). That is a second writer process. The architecture's single writer per file (§2.2) must also own the tools children, or they must call back over MCP or HTTP.

**Event protocol today.** Each durable event is a row in `events(seq, topic, subject, data)`. Topics are `runs, jobs, sessions, apps, library, settings, aggregates` (`service.py:43`). A block append emits `{"type":"block","block":{seq,type,content}}` on `sessions` with subject = session id (`:324-335`). Runs, jobs, apps and Library changes also emit an `aggregates` row (`:164-169`). SSE sends `event=<topic>`, `id=<seq>`, `data=<json>`, resumes from `Last-Event-ID` or `after`, and polls every 50 ms (`service.py:187-198`). Block types are a closed list of 14 (`:54-71`). Sessions carry `id, title, origin (default "copilot"), parent_id` and no status (`:47-51`).

**What the UI expects (`ui-review/repair`).** Nothing from the backend yet.
- The copilot uses an in-memory demo store (`apps/qmx-ui/src/lib/copilot/store.svelte.ts:1-20`), which says the daemon "(LangGraph) streams the same block shapes once wired".
- The only `fetch` calls read demo JSON and a Vite dev path `/__demo/mql5/{id}` (`src/lib/qmx/article.ts:29`).
- Its vocabulary (`src/lib/copilot/demo.ts:11-94`) differs from the backend: kinds `tools, changes, cards, ask` against `tool, changed, entity, question`. The UI has no `needs_you`. Session `status: running|waiting|done` has no backend field. `origin: Main|Lab|Portfolio|Library|Mini apps` against `"copilot"`.
- The planned envelope is research 32 §B3.1 (`ARCHITECTURE.md` §2.1 `QmaEvent`).
- B12 (UI wiring) must bridge these names. The branch exists only on this laptop: `git branch -a` shows no remote.

## 3. Existing agent code

**qmx-agents (LangChain, P06-P24).** Path key: `agents/` = `qmx-agents/packages/qmx-agents/src/qmx_agents/`. Live callers are `qmx-apps` (`supervisor.py:29`, `road/__init__.py:11`, `road/history.py:13`, `road/validation.py:12`), `qmx-remote` (`models.py:11`, `runs.py:16`, `worker.py:29-32`), `qmx-control/tests/test_remote.py:9`, the two example apps and `scripts/live/*.py`. No `qmx-control` route calls the copilot. `build_copilot` and `stream_turn` are reached only from `scripts/live/copilot_build_app.py`. Importing `agents/guards/journal.py` runs `guards/__init__.py`, which imports `admission` (Deep Agents) and `money_path` (LangChain). That is why `import qmx_apps` loads both.

Reuse rather than rebuild:

| What | Where | Neutral? |
|---|---|---|
| `RunJournal`, `encoded`, `fingerprint` | `agents/guards/journal.py:17-127` | yes; apps and remote need it |
| `match_money_path_act`, `check_descriptor` | `agents/guards/money_path.py:141-162`, `:247-279` | yes, except the `BaseTool` classes at `:181-245` |
| `is_parent_surface_permitted`, `ExperimentLedger` | `guards/parent_surfaces.py`, `guards/experiments.py` | yes |
| `AdmissionGate`, `valid_path` (content + hash rule) | `guards/admission.py:34-113` | yes; the backend at `:114+` is Deep Agents |
| `watch_breakers` (P20 hooks) | `guards/hooks.py:153-179` | yes; `AppHooksMiddleware` (`:22`) is bound |
| MemoryProvider protocol, `Scope`, `MemoryRecord` (P07) | `agents/memory.py:53-131` | yes, except `tools() -> list[BaseTool]` (`:130`) |
| `model_selector`, `RouterConfig`, `credential()`, `RunContext` (P06) | `agents/router.py:40-52`, `:74-123`, `:126-143` | yes; `Provider` Literal (`:30`) and CLIProxy calls (`:280-303`) go |
| `AgentSpec` fields, `load_spec`, `mcp_configuration` | `agents/spec.py:108-143`, `:197-245` | yes; `_build` (`:246+`) and `guards()` (`:401`) are bound |
| block mapping from engine events | `agents/copilot.py:98-213` (`stream_turn`) | logic is the reference for `BlockProjector`; code is bound |
| four task verbs | `agents/tasks.py:31-89` | the verbs; the code is bound |
| `workflow.v1` models and schema | `agents/workflows/models.py`, `workflow.v1.schema.json` | yes; `compiler.py` and `runs.py` are bound |

No usage, ledger or account code exists to reuse. `router.accounts()` and `quotas()` only call CLIProxy. The nearest prior art for usage accumulation is `adws/adw_modules/agent_pi.py:189-200`, `:369-378`, and it is not reusable as is.

**Old QMA runtime** (`qma-core`, `qma-wire`, `qma-daemon`, 113k lines after P16c). Nothing in production imports it. `scripts/dev/qma_callers.py` at 4eac8f69 lists every caller outside its own packages:
- Protected: `qmb/src/qmb/doors/cli/host.py` (string `DAEMON_SPAWN_MODULE = "qma.daemon"` at `:104`, used only by the `invoke_host_*` helpers, which no CLI command calls) and `qmn/examples/spot_paper_journey.py:15-17` (run by `tools/spot-paper-check.ps1:29-52`).
- Tests: `qmb/tests/test_cli_host.py`, `qmb/tests/test_operator_study_cli.py:21-30`, `qa/integration/test_qma_*.py` (not in CI) and `qmx-agents/tests/test_workspace_scaffold.py`.
- Other: `qmx-agents/examples/*.py`, the five `qmx-agents/plugins/*/daemon/plugin.py` and `tools/backend-source-provenance.py:18-20`.
- Config and tooling: root `pyproject.toml:228-230` and `:360-362` put the qma `src` dirs on the pytest and pyright paths. Also `tools/nested_coverage_report.py:13`, `tools/release_gate.py:27-29`, `:197`, `:206`, `tools/build_release.py:266`, `tools/secret_scan.py:65`, `tools/tests/test_release_install.py:33-35` and `tools/tests/test_runtime_wheel_closure.py:28`.
- The daemon loads `qmx-agents/plugins/` itself (`qma/daemon/plugins/packs.py:3`), so the packs go with the daemon, not before it.
- `qmb/src/qmb/analysis/variants.py:64-107` only holds `"qma"` strings and needs no change.

**Native drivers** (`qma-daemon/src/qma/daemon/request_runtime/`). These are the only Claude Agent SDK code.

From `native_claude.py` (435 lines), keep:
- Preflight (`:97-160`). It reads env names only, checks the SDK and CLI versions, and runs `claude auth status` under `CLAUDE_CONFIG_DIR=<dedicated home>`. It then requires `loggedIn`, `authMethod == "claude.ai"`, a first-party provider and a matching `configDirectory`. That is the subscription check.
- The in-process MCP server built from `tool()` and `create_sdk_mcp_server` (`:191-220`, `:268`), whose error handling never leaks host exceptions.
- The `PreToolUse` hook plus a `can_use_tool` callback as two layers (`:222-237`, `:265-267`).
- The isolation env (`:274-279`), with `setting_sources=[]` and `strict_mcp_config` (`:261-262`).
- The event loop (`:289-345`). The init message gives the session id and the advertised tools. Resume refuses a different session id. `ResultMessage` maps to completed, failed or interrupted (`aborted_*` means interrupted). Cancel calls `client.interrupt()` (`:347-350`).

Drop the lockdown: `tools=[]`, `skills=[]`, `agents={}`, the disallowed built-ins, `max_turns=8`, and the refusal of sub-agent and `task_*` output (`:245-260`, `:309-345`). The exact CLI pin at `:114` would refuse this laptop (2.1.296); a minimum version is the right check.

From `native_boundary.py` (123 lines), keep `call_blocking` (`:16-41`), the env deny list `check_environment` (`:44-75`), `check_directories` (`:78-96`) and the managed-policy probe `check_claude_managed_policy` (`:99-123`).

`native_codex.py` (553 lines) drives the Codex app server through `openai-codex`. It is not the chosen OpenAI engine. Only its `DISABLED_FEATURES` list (`:36-60`) is worth reading.

`native_sessions.py` (446 lines) has a `SessionBackend` protocol (`:39-63`: `start`, `resume`, `events`, `cancel`, `close`) that already has the `EngineAdapter` port's shape. The rest is daemon glue.

The fake-client tests (`qma-daemon/tests/test_native_sessions.py`, `test_native_codex_bridge.py`) show a working `client_factory` fake pattern. Copy them with the recipe.

**Mini apps.** `examples/apps/weekend-watcher/server.py:10-52` and `macro-daily-bias/macro_bias.py:15-122` build a Deep Agent in-process from `qmx_agents.spec` and `router`, using a fake or recorded model. Their `qmx-agents` dependency is a GitHub git pin to an old commit (`weekend-watcher/pyproject.toml`, `rev = 697b5a09…`; macro `rev = e27a5136…`). Deleting the package in the repo does not break them; they keep running old LangChain until a new version goes through the road. `qmx-apps/tests/test_apps.py:358-392` installs weekend-watcher with `uv sync`, so that test needs network access or a warm uv cache. Two manifests carry `qmx/control-token`: `macro-daily-bias/app.toml:21` (`QMX_DATA_TOKEN`) and `mql5-articles/app.toml:16` (`QMX_CONTROL_TOKEN`). §2.12 says to drop the first; the second also needs a decision.

**qmx-tools.** It has 13 functions in 4 groups (`registry.py:26-272`), served as stdio FastMCP (`servers.py:9-38`, scripts `qmx-mcp-data|backtest|research|node`). The LangChain wrapper is `registry.py:274-281` and pulls `langchain-core` into its dependencies. Its dependencies include `qmb, qml, qmn, qmf-data, qmx-control`, so importing it pulls in the quant core. Reach it over MCP, never by import (F18 holds).

## 4. Deletion sequence

The old packet 0a deleted before replacing. This sequence puts every deletion after the replacement it depends on, and makes each one a separate PR with a mechanical check. The scaffold packet only moves code (the guards) and copies code (the recipe). It deletes nothing.

| Body of code | What keeps it alive (file:line) | What replaces it | Earliest safe point | Operator's say? |
|---|---|---|---|---|
| qma-core/wire/daemon + `qmx-agents/plugins/`, `qmx-agents/examples/`, `qmx-agents/tests/test_workspace_scaffold.py` | QMB tests and dead helpers (`host.py:104`, `invoke_host_*`; `qmb/tests/test_cli_host.py`, `test_operator_study_cli.py:21-30`); `qmn/examples/spot_paper_journey.py:15-28`; root `pyproject.toml:228-230`, `:360-362`; qmx-agents `pyproject.toml:17`, `:14`, `:64`, `:70-82`, `:112-124`, `:137`; tools listed in §3 | Nothing live. The native recipe → `qma2.engine.claude` | After the recipe is copied (scaffold) and the ClaudeAdapter passes its fake tests and one live turn (Claude engine unit). It could go right after the scaffold if CI time matters more. | Yes: QMB src and tests (B7). QMN example likely too. |
| `qmx-agents/packages/qmx-agents` (LangChain core) + `scripts/live/{copilot_build_app,smoke_agent,smoke_firecrawl}.py` + `qmx-tools` LangChain wrapper | `qmx_apps` 4 imports (above); `qmx_remote/models.py:11`, `runs.py:16`, `worker.py:29-32` (`execute_agent` `:184-209`, `execute_workflow` `:137-170`, `run_router` `:171-182`); `qmx-control/tests/test_remote.py:9`; `tools/ci.py:17`, `:27`; `tools/test_all.py:72-77`; `qmx-tools/registry.py:274-281` | guards → `qma2.journal`, `qma2.policy`; copilot → turn host + engines; workflows → graph runner; worker executors → `TurnHost.headless`; router → `qma2.router` | After the guard move (scaffold), turn route, both engines, graph runner and remote executors land. Earlier only if `execute_agent` and `execute_workflow` are first turned into `not_implemented`. | No (qmx-* packages). Tell him remote agent and workflow runs go dark if done early. |
| Old UI `apps/qmx-ui` on rebuild/base (CT-40 wire client) | `tools/build_release.py:75`; nothing at runtime | `apps/qmx-ui` from `ui-review/repair` | When B12 lands the new UI on rebuild/base. First push `ui-review/repair` to origin; it is the only copy. | Yes (UI lane is his) |

**D1: Retire old QMA (one PR, ~183k lines with tests).**
- Delete `qmx-agents/packages/qma-core`, `qma-wire` and `qma-daemon`, plus `qmx-agents/plugins/`, `qmx-agents/examples/`, `qmx-agents/tests/test_workspace_scaffold.py`, `qa/integration/test_qma_authenticated_study.py` and `test_qma_registered_replay.py`.
- Edit:
  - `qmx-agents/pyproject.toml`: members, `qma-runtime` (keep `qmx-control`), pytest `pythonpath`, pyright `extraPaths` and `include` (drop `examples`, `plugins`), the poe paths and the `test` coverage targets.
  - Root `pyproject.toml:228-230`, `:341`, `:360-362`.
  - `tools/nested_coverage_report.py`, `release_gate.py`, `build_release.py`, `backend-source-provenance.py`, `secret_scan.py:65` and the two `tools/tests` release tests.
- QMB, with his go: delete the `invoke_host_*` helpers and the daemon-path code in `host.py` (`:104-1783`; keep `control_host` and the `HOST_*` command tuples). Then delete the daemon tests in `test_cli_host.py` and either delete or rewrite `test_operator_study_cli.py`.
- QMN: rewrite `spot_paper_journey.py` without `qma.*`, or retire it together with `tools/spot-paper-check.ps1`.
- Delete `scripts/dev/qma_callers.py` and `tools/tests/test_qma_callers.py` last, in the same PR.
- **Proof:**
  - Before deleting, `qma_callers.py` shows no protected or test callers outside the deletion set.
  - Afterwards, `git grep -n -E "qma\.(core|daemon|wire)|qma-(core|daemon|wire)" -- . ':!*.md' ':!archive/**'` prints nothing, and `uv lock --check` passes at the root and in `qmx-agents`.
  - `qmb host start/status/stop` still works.
  - `just ci` is green with the QMA suite gone (expect about 10 minutes less).
  - `python -c "import qma.daemon"` fails on purpose.

**D2: Remove the LangChain core (one PR).**
- Delete `qmx-agents/packages/qmx-agents`, the three `scripts/live` files above, the `langchain-core` dependency and `registry.py:274-281` in `qmx-tools`, and the bound executors in `qmx_remote/worker.py`.
- Edit `qmx-agents/pyproject.toml` (members, sources, ruff and pyright excludes), `qmx-apps` and `qmx-remote` pyprojects (drop `qmx-agents`), `tools/ci.py:17`, `:27` and `tools/test_all.py:72-77` in the same PR (F19).
- **Proof:**
  - `git grep -i -E "langchain|langgraph|deepagents" -- . ':!*.lock' ':!archive/**' ':!examples/apps/**'` prints nothing.
  - `uv lock` in `qmx-agents` lists none of the three.
  - `python -c "import qmx_apps, qmx_remote, qmx_control; import sys; assert 'langchain_core' not in sys.modules"` passes.
  - The qmx-apps weekend-watcher test still passes, because of its git pin.
  - `just ci` is green.
- The example apps get new versions through the road, outside this PR.

**D3: Old UI.** Delete `apps/qmx-ui` (old) when the new UI lands there, and fix `tools/build_release.py:75`. Proof: `pnpm -C apps/qmx-ui build`, plus the release tool test. This needs his go.

Ordering: D1 and D2 are independent. D1 first shrinks CI and the qmx-agents root config the harness edits. Do not run either in the same PR as harness code.

## 5. Package location, name, pins

- **Location:** `qmx-agents/packages/qma-v2/`, distribution `qma-v2`, import name `qma2`, as in ARCHITECTURE §2.0. It belongs in the nested workspace because `qmx-control` and the apps live there and it must lock against them.
- **Name conflicts:** none. `git ls-files` has no `qma2` or `qma-v2`. The old `qma` is a PEP 420 namespace (`qma.core|wire|daemon`), and `qma2` is a separate top-level name. `qma_callers.py`'s regex (`\bqma\.(core|daemon|wire)`) does not match `qma2.`. One watch item: `openai-agents` imports as `agents`. No first-party top-level `agents` package sits on the qmx-agents path. The `agents/` folders in example apps are plain data directories and cannot shadow it, and `adws/adw_modules/agents.py` lives only in the root env. Do not add a regular `agents` package at a `sys.path` root.
- **Auto-sweep trap:** a new directory under `qmx-agents/packages/` is collected by the old QMA suite (`testpaths` `:69`, the `--ignore` list at `:67`), linted by the workspace ruff (`:86`) and type-checked by its pyright (`:110-111`), unless it is added to those excludes. Give it its own row in `tools/ci.py:23-31` and `tools/test_all.py`.
- **Pins today:**
  - `claude-agent-sdk==0.2.163` (dev group, `qmx-agents/pyproject.toml:54`; lock `uv.lock:444`; PyPI upload 2026-09-30; expects CLI 2.1.286 per `_cli_version.py`).
  - `openai-codex==0.160.0` (`:55`), not needed by the new engine.
  - `openai 3.28.0` and `anthropic 1.11.0`, transitive through LangChain.
  - `mcp 2.3.0`, `fastmcp 4.0.11`, `starlette 1.7.0`, `pydantic 2.13.4`.
  - `openai-agents` is absent.
- **Pin for qma-v2** (runtime dependencies of `qma-v2`, not the dev group):
  - `openai-agents==0.23.1` (latest, 2026-10-02). It requires `openai>=3,<4`, `mcp>=1.19,<3`, `starlette>=1.3.1`, `websockets>=15,<17`, `httpx2>=2.12`, `griffelib>=2,<3`; all are met by the current lock.
  - `claude-agent-sdk`: keep `0.2.163` or move to `0.2.165` (2026-10-08). Only 0.2.165 ships a `win_amd64` wheel with a bundled CLI; it is 5 days old against the two-week rule, so that is the operator's call.
  - Pin `openai` explicitly too, because D2 removes the LangChain path that brings it in today.

## 6. Traps

1. **Inherited Claude env.** Builders run inside Claude Code, which sets `ANTHROPIC_BASE_URL`, `CLAUDECODE`, `CLAUDE_CODE_SESSION_ID`, `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_CODE_OAUTH_SCOPES`, `CLAUDE_CODE_MESSAGING_SOCKET`, `CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH` and more (names checked, values not read).
   - The old daemon refuses any `ANTHROPIC_*` (`native_claude.py:99-102`, `native_boundary.py:72`). With it set, 31 of 60 native-session tests fail; without it, all 60 pass.
   - The new ClaudeAdapter must build the child env from an allow list. The SDK merges `os.environ` into the child, so a builder's nested session would otherwise inherit the host session.
2. **No bundled Claude CLI on Windows** with 0.2.163. The SDK falls back to `shutil.which("claude")` (`claude_agent_sdk/_internal/transport/subprocess_cli.py:258-280`). Here that is `C:\Users\Mubarak\.local\bin\claude.exe`, 2.1.296. Pass `cli_path` explicitly and record the version in the journal.
3. **rclone is not on PATH.** `qmx-control/tests/test_backup.py:19` and `qmx-apps/tests/test_storage.py:38` assert that rclone exists. The qmx-control suite here gave 43 passed, 1 failed for that reason only. CI installs rclone v1.75.1 (`battery.yml`).
4. **The CI lock** `D:\QMX-worktrees\.ci-lock` is absent now. Take it with `File.Open(..., 'CreateNew')` exactly as in ORCHESTRATOR-PROMPT §4. `just ci` takes about 29 minutes; the slowest suites are QMA 579 s, QMF/QML/QMB/QMN 504 s and qmx-apps 155 s + 130 s serial.
5. **GitHub Actions has never run.** `gh run list` is empty and `gh pr checks 70` reports none. Every "green" is a local `just ci` (B2).
6. **App Control blocks `poe.exe`** in the nested venv (`qmx-agents/pyproject.toml:134-135`). Use `python -m poethepoet` and `python -m pyright`, as `tools/ci.py` does.
7. **C: paths.** `default_home()` is `~/.qmx` (`server.py:255-256`). `QMX_TOOLS_ROOT` defaults to the same place. The old daemon root is `%LOCALAPPDATA%\QMX\qma-daemon` (`host.py:157-179`). Put test homes, `--basetemp`, `TMP` and the uv cache on D:.
8. **SQLite writers** (B1, §2): fresh connections per call, a maintenance thread, and a second writer process (the tools children). SQLite 3.50.4 carries the WAL-reset bug.
9. **`import qmx_apps` loads LangChain and Deep Agents.** Until the guards move, any harness test that imports `qmx_apps` pulls them in. The import-linter is not in any dev group yet.
10. **Root `ruff` 0.16.3 against qmx-agents 0.16.5.** Format the package with its own workspace's ruff.
11. **Deleting paths named in a poe task** (`examples`, `plugins`) makes ruff fail with E902 on the missing path. Edit the task strings in the same PR.
12. **Mini-app tool calls time out at 20 s and stop the app** (`qmx-apps/src/qmx_apps/supervisor.py:676`, `:721-726`). T1 refuses agent trust (`:139-144`). Trust is a caller argument on `apps_create` (`service.py:657-659`). All three are as HOW-WHY F1, F2 and F12 describe.
13. **Pytest settings.** Never raise above `-n 2`. qmx-agents `addopts` says `-n auto` (`:67`), so pass `-n 2` explicitly. Mark tests that use shared resources `serial`.

## Builder quick-reference

```text
Worktree      git -C D:/QMX-worktrees/agent-system worktree add -b qma2/<id> D:/QMX-worktrees/qma2-<id> origin/rebuild/base
Env (pwsh)    $env:TMP='D:\Temp'; $env:TEMP='D:\Temp'; $env:UV_CACHE_DIR='D:\Caches\uv'
              Get-ChildItem Env: | ? Name -like 'ANTHROPIC_*' | % { Remove-Item "Env:$($_.Name)" }
Sync          uv sync --frozen                                   (root)
              uv sync --frozen --all-packages --all-groups        (in qmx-agents/)
Python        qmx-agents/.venv/Scripts/python.exe  (3.14.6, sqlite 3.50.4)
Host          uv run qmb host start|status|stop                   (root; port 8766, home ~/.qmx)
              uv run --project qmx-agents/packages/qmx-control python -m qmx_control serve --home D:/Temp/qmx-home
Token         keyring "qmx/control-token"; every route needs  Authorization: Bearer <token>
SSE           GET /api/events/sessions?after=<seq>&subject=<session_id>   (Last-Event-ID honoured)
Sessions      POST /api/sessions {title, origin, parent_id}; POST /api/sessions/{id}/blocks {type, content}
MCP           /mcp (FastMCP over HTTP, same 52 operations); in-process: qmx_control.server.create_mcp(service)
Domain tools  stdio: qmx-mcp-data | qmx-mcp-backtest | qmx-mcp-research | qmx-mcp-node  (QMX_TOOLS_ROOT)
One suite     cd qmx-agents/packages/qmx-control; ../../.venv/Scripts/python.exe -m pytest tests -q -n 2 --basetemp D:/Temp/pytest-<id>
Lint/types    uv run --no-sync python -m poethepoet fmt-check|lint|types   (inside the package dir)
Full gate     just ci  (only under D:\QMX-worktrees\.ci-lock; ~29 min; rclone on PATH)
Callers       qmx-agents/.venv/Scripts/python.exe scripts/dev/qma_callers.py [--json]
New package   qmx-agents/packages/qma-v2/src/qma2/ ; add to qmx-agents pyproject members, sources,
              ruff extend-exclude, pyright exclude, pytest --ignore; add rows to tools/ci.py and tools/test_all.py
Conventions   pyright strict (Windows platform); ruff line 100; files near 400 lines; pydantic extra="forbid";
              errors as ControlError(code, message, status).document(); secrets only as qmx/* credential refs
              (settings_put rejects key/token/password/secret keys, service.py:79-91); tests marked serial
              when they share state; each package carries its own fmt-check/lint/types poe tasks
Never         edit qmb/ without his go; import qmx_tools, qmx_control or qma.* from qma2; set ANTHROPIC_*;
              raise pytest workers above 2; delete a .ci-lock you did not create
```

## Corrections to the prior maps

- **F10 / B3.** The SDK pin sits in the qmx-agents dev group, not in `qma-daemon` (whose dependencies are langchain, langgraph and deepagents). Deleting the daemon keeps it. It should still move to `qma-v2`'s runtime dependencies.
- **B4 / D2 "kept alive by `host.py:104`".** True only for tests. `:104` is a string used by `invoke_host_*`, which no CLI command calls since PR #49. The live keep-alives are QMB tests, the QMN example, and the path config.
- **HOW-WHY P6, `tools/service.py:126-136`.** The `ControlService` construction is at `:126-128`, and it runs in every MCP child (§2), which makes B1 a multi-process problem.
- **Everything else re-checked holds at 4eac8f69:** P1, P2, P11, P12, F1-F4, F12, F17 and F19, and the 501 lines at `service.py:880-894`.
- **New:** the UI has no backend calls and different block names. The UI branch has no remote. The example apps depend on a git-pinned `qmx-agents`. 0.2.163 ships no Windows wheel. The SDK picks up the Claude Code env.
