# QMX backend map for running "mini apps" safely (read-only survey, 2026-10-04)

Labels used throughout:
- COMMITTED = in git history on a branch (most of it on `origin/integration`, tip a0e87697, 2026-09-30).
- UNCOMMITTED = sitting in a working tree, not in any commit.
- DOCS-ONLY = ratified in `docs/` or `_bmad-output/` but no code exists.

Paths starting `qmx-agents/`, `qmb/`, `qmn/`, `.github/` are code. In the main checkout (`main`, c3e8ec5e) they are NOT present as the latest version: main holds docs and tooling. The code lives on the `integration` line. Note the local branch `integration` (worktree `.worktrees/integration-inspect`, fdc76703) is STALE. The real tip is `origin/integration` a0e87697, which already contains Epics 70 to 73 (per `_bmad-output/implementation-artifacts/session-epics-70-73.md`). I read that tip with `git show` and `git grep`, not by checking anything out.

---

## 0. Worktrees and branches that matter

| Where | Branch / tip | Uncommitted |
|---|---|---|
| `C:\Users\Mubarak\Desktop\QMX` | `main` c3e8ec5e "record backend-first pause and reviewer study" | `.serena/project.yml` modified; untracked `_bmad-output/implementation-artifacts/` (Epic 70 to 73 specs and context), `workroom/backend-assurance-2026-09-27/` (audit plan, CI-door NEXT.md), `workroom/ui-review-2026-10-01/` (UI screenshots) |
| `QMX-worktrees\epic-072-pack-ui-action-context` | `epic/072-pack-ui-action-context` 478489ba | UNCOMMITTED: `qmx-agents/packages/qma-daemon/src/qma/daemon/plugins/pack_ui.py`, `.../plugins/pins.py`, `qma-wire/src/qma/wire/action_context.py`, `initialize.py`, `schemas.py`, `vocabulary.py`, `__init__.py`, `qma-wire/schemas/pack_ui_request.v1.schema.json`. This is an earlier PARALLEL attempt at Epic 72. The sequential rerun of the same epic shipped (branch `epic/072-pack-ui-action-context-sequential`, merged as PR #18). So this is a stale duplicate, not new capability. |
| `QMX-worktrees\epic-071-editor-drafts` | `epic/071-editor-drafts` 478489ba | UNCOMMITTED: `qma-wire/.../vocabulary.py` modified, `qma-wire/.../editor_draft.py` new. Same story: the sequential Epic 71 shipped (PR #17); this is a leftover. |
| `.codex\worktrees\epic-072-pack-ui\QMX` | `epic/073-origin-cancel-sequential` 111117b1 | clean (Epic 73 candidate, shipped as PR #19) |
| `.codex\worktrees\factory-enforcement-{backend,test,ui}\QMX`, `reticle-unattended\QMX` | `codex/factory-enforcement-*`, `codex/reticle-unattended` | clean. CI hardening, factory receipts, unattended browser verification (Reticle). |
| `QMX-worktrees\ui-review-repair` | `ui-review/repair` 557da44b (docs say HEAD 9aadfc76 in the backlog file) | clean. The rebuilt Svelte UI `apps/qmx-ui`. |
| `QMX-worktrees\backend-assurance-7b65732f` | `deployment/fmt-check` de4ed64c | clean. Mock-data scanner, QMB hang-loop abort fix. |
| `QMX-worktrees\epic-049..052`, `chunk-skylos-*`, `epic-070..073`, `ui-factory`, `ui-epic-066-shell`, `pre-miniapps-270e992` | assorted epic/chunk branches | all clean. QML research work (epics 49 to 52), code-quality chunk repairs, UI shell epic 66. |
| `.worktrees\mql5-library` | `research/mql5-article-library` | untracked `research/` (MQL5 article library for the UI demo) |
| `.worktrees\ui` | `ui` af662888 (23 epics, 131 stories over the PRD) | clean |

Finding: there is no uncommitted LangChain or LangGraph code in any worktree. The only hits for those words are docs and the UI backlog (section 2).

---

## 1. Mini apps, packs, views

**What a mini-app is (DOCS + COMMITTED).** `docs/glossary.md` line 699: "An installed instance of a pack, keyed by `instance_id` != `plugin_id`". A pack is the bundle. The ratified model is "pack-and-grant": a pack REQUESTS operations, optional views, a copilot profile and capabilities; the host GRANTS them into a product session. Install is not a grant, enable is not a grant (`docs/decisions/ADR-0025-pack-and-grant-kit.md`, kit AD-1, DEC-0452). Headless packs (no UI) are first-class.

**Pack manifest (COMMITTED).** `qmx-agents/plugins/analysis-backtest/manifest.json` is the shape: `id`, `version`, `qma_api`, `entrypoint: "daemon.plugin:activate"`, `contributions` (list of `{point, local_id}`), `permissions`, `migrations`. Five first-party packs exist as folders under `qmx-agents/plugins/`: analysis-backtest, dev-factory, pm-coordination, research-corpus, trading-readonly. Each has `daemon/`, `graphs/`, `migrations/`, `skills/`, `ui/`, `worker/` directories (`ui/` and `worker/` are empty in analysis-backtest).
- Manifest and contribution code: `qmx-agents/packages/qma-core/src/qma/core/plugins/{manifest,contributes,pack_sdk,packs}.py`.
- Closed set of eight things a pack can contribute: `tool, tool_adapter, hook, skill, graph_template, model_deployment, toolset, worker_template` (stated in `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/VIEW-AND-PACK-CONTRACT.md` section 1; enforced in `qma-core/.../ports/cardinality.py`).
- Optional `copilot_profile` parsed in `pack_sdk.py` (Story 60.1). `requested_capabilities` is just the old `permissions` field renamed.

**Install / enable / publish flow (COMMITTED).**
- Loader: `qmx-agents/packages/qma-daemon/src/qma/daemon/plugins/loader.py` (1,246 lines). Order: manifest validation, API compatibility, permissions, dependencies, migrations, topological activation, publication. Reload is an explicit operator command; no file watcher, no hot reload (docstring).
- Instance and listing: `daemon/discovery/{listing,instance_health,federated,research_surface}.py`. Instance `health()` is separate from "published" (Story 64.2).
- Authoring to publish (Epic 71, COMMITTED on integration): `qma-daemon/.../staging/editor_draft.py`, `qma-wire/.../editor_draft.py`. Daemon issues `editor_draft_id`, saves with compare-and-swap on `editor_revision`, `publish_editor_draft` writes a graph template into a local authoring pack, then the normal enable, grant, instance, invoke path. A draft cannot be run (`draft_not_runnable`). Source: `_bmad-output/implementation-artifacts/spec-epic-71-editor-drafts.md` and `.../architecture-QMX-UI-BACKEND-2026-09-24/PACK-UI-AND-AUTHORING.md`.
- Artifact upload (Epic 70, COMMITTED): `qma-daemon/.../artifacts/{stage,store,ticket}.py`, authenticated `PUT /artifacts/stage`, transfer tickets.

**Views and the canvas-widget slot (COMMITTED, wire level only).**
- `PackUiRequest` v1: `qmx-agents/packages/qma-wire/src/qma/wire/pack_ui_request.py`, schema `qma-wire/schemas/pack_ui_request.v1.schema.json`, daemon side `qma-daemon/.../plugins/pack_ui.py`, tests `qma-daemon/tests/test_epic72_pack_ui.py`, `qma-wire/tests/test_pack_ui_request.py` (all at `origin/integration`).
- At enable the daemon ingests at most one PackUiRequest and stores it on the existing install row. UI problems never roll back the operations roster. Read back with the authenticated `get_pack_ui_request` keyed by `instance_id` + `availability_revision`. Source: `_bmad-output/implementation-artifacts/spec-epic-72-pack-ui-action-context.md` (status: done).
- Closed slot set: `app-nav, canvas-widget, detail, copilot-panel, preview-tab` (epic-72-context.md). Closed renderer set: `native | json-render | mcp-app` (VIEW-AND-PACK-CONTRACT.md section 2).
- `ActionContext` (`qma-wire/.../action_context.py`): the host, never the pack or the browser, mints an immutable context per mount. Zero matching grants: paint but cannot act. One: bound. Two or more: typed `GRANT_AMBIGUOUS`. The renderer may only send `{action, input}`; authority fields are ignored.
- The word "widget" here means a view of an operation; "Widgets never own invoke" (ADR-0025 kit AD-2). Three browser-side issuers only: `dispatchChat`, `dispatchInvoke`, `dispatchCancel` (ADR-0026; `apps/qmx-ui/BACKEND-REQUIREMENTS.md` on `ui-review/repair`).

**json-render and MCP Apps (DOCS-ONLY).** Both are named as optional presentation adapters, deliberately "unpinned": no dependency, no code (ADR-0025 kit AD-8, DEC-0459). MCP Apps = sandboxed iframe with host-proxied tool calls (`ARCHITECTURE-SPINE.md` line 144 of `architecture-QMX-2026-09-23`). The UI-side backlog on `ui-review/repair` (`apps/qmx-ui/UI-BACKLOG.md`) lists "MCP Apps renderer, if the mini-app SDK chooses it" and says the mini-app SDK's UI part is undecided.

**Not built in the pack runtime:** a registry of installable/community packs, signing, versioned distribution, a "components contract" for how mini apps and the copilot put screens into QMX. The backlog says this contract is "still to be written".

---

## 2. Agent runtime

**QMA daemon (COMMITTED).** One long-running asyncio process: `qmx-agents/packages/qma-daemon/src/qma/daemon/process.py`. It composes the CT-40 loopback listener (default port 8765), a single sqlite writer, the experiment ledger, and the five desk packs. Three Python packages: `qma-core` (definitions only, import-checked by `qma-core/.../plugins/boundaries.py`), `qma-wire` (message types), `qma-daemon` (the runtime). Layout of subsystems under `qma-daemon/src/qma/daemon/`: `sessions/` (product sessions, copilot, grant binding), `taskgraph/` (compiler, dispatcher, nested missions, outbox), `scheduler/` (cron, routines, wake, continuation), `bus/mailbox.py`, `tools/registry.py`, `hooks/`, `capabilities/` (enforcer, spawn), `proxy/` (model proxy, broker, egress), `memory/`, `knowledge/`, `ledgers/`, `journal/`, `persistence/`, `staging/` (change requests, proposals), `envs/` (execution environments, jobs, router), `telemetry/`.

**Wire / UI link (COMMITTED).** CT-40 (`docs/contracts/ct-40-qma-wire-envelope.yaml`) is a WebSocket JSON-RPC plus HTTP GET snapshot surface. Pairing (`daemon/http_pair.py`, `pairing.py`, Epic 68), a separate token-gated host-control channel (`daemon/host_control/channel.py`, Epic 67), mailbox-based chat (`send_message` then `list_mailbox`, Epic 69), `cancel_job` (Epic 73). The UI is a Svelte 5 app `apps/qmx-ui` on branch `ui-review/repair`; it has no transport bound yet ("Every daemon-backed control is visibly disabled", `apps/qmx-ui/BACKEND-REQUIREMENTS.md`). One known gap: `start_mission` / `launch_task` JSON-RPC returns method-not-found (`_bmad-output/implementation-artifacts/deferred-work.md`, third entry), so a mission cannot yet be launched over the wire.

**Approvals and permissions (COMMITTED).** Hook-enforced policy: `capabilities/enforcer.py` ("a deny binds under every permissive mode"), narrowing at spawn: `capabilities/spawn.py`. Grants are `GrantRecord`s inside a product session (`sessions/grant_binding.py`). A money-path barrier exists in code: `qma-core/.../barriers/money_path.py` lists acts including `arm_kill_switch`, `set_capital_floor`; agents are denied these.

**Scheduled jobs (COMMITTED).** `daemon/scheduler/{cron,routines,wake,continuation}.py`, contract CT-49 (`docs/contracts/ct-49-qma-routine.yaml`), "laptop-off continuation" (`envs/continuation_host.py`).

**LangChain / LangGraph: NO CODE ANYWHERE.** Searched `origin/integration` (all Python and config), plus the UI branches. Only mentions:
- `apps/qmx-ui/BACKEND-REQUIREMENTS.md` and `UI-BACKLOG.md` on `ui-review/repair`, dated 2026-10-04: "The agentic layer moved to LangChain and LangGraph; the own agent SDK is dropped" and "anything below that assumes the QMA daemon's own agent SDK needs re-checking". Also "Two SDKs: the agent SDK and the mini-app SDK".
- `docs/decisions/ADR-0020-qma-agentic-system.md` line 31: hosting LangGraph loops was REJECTED earlier ("QMA owns its runtime bottom-up", DEC-0360). That ruling is now contradicted by the operator's 2026-10-04 direction and needs a new decision record.
Consequence: the entire `qma-daemon` agent loop, sessions, task graph, hooks, tool registry (about 160 Python modules, 5,200+ tests per the Epic 73 note) was built around the dropped agent SDK. Which parts survive (pack/grant/journal/wire, probably) versus get replaced (dialogue runtime, task graph, `envs/runtime.py`) is undecided and undocumented.

---

## 3. Isolation: what exists

**Docker / containers: declarations and refusals only, no launcher (COMMITTED).**
- `ExecutionEnvironment` has a closed `kind`: `local | docker | remote_container | remote_host | browser | desktop`; "docker-per-worker, ephemeral, is the default" (`docs/contracts/ct-46-qma-execution-environment-job.yaml`, DEC-0316). Fields: image, mounts, environment-variable allowlist, a REQUIRED `network` field, lifecycle, concurrency cap `max_in_flight` (default 1; `docs/registry/variables.yaml` line 1868).
- Code that validates those declarations: `qma-daemon/.../envs/registry.py` (refuses missing network posture, deny-listed host, forbidden image, dirty shared filesystem, control-channel env allowlist), `envs/boundary.py` (remote side must dial out, never open an inbound port; trading-node hosts refused by identity), `qma-core/.../barriers/reachability.py`.
- Placement: `envs/router.py` (agents declare a ComputeRequirement; the router is the only placer; unsatisfiable gives `NoEnvironment`), job lifecycle `envs/jobs.py` (durable JobHandle: submit, attach, wait, reattach, cancel, stream).
- I found NO code that actually starts a container (`git grep` for docker in the daemon finds only these declaration/validation files; no `docker run`, no docker SDK). `envs/runtime.py` describes a Python interpreter "inside the worker Docker container" but that is a contract, not a launcher.
- Real Docker use that exists: `qmn/deploy/observability/compose.yml` (Prometheus, Grafana, Loki, Promtail, pinned tags, host networking bound to 127.0.0.1, own user and storage quota). It is the only containerised thing and by ruling "Containers permitted HERE ONLY" (file header; ADR-0019).

**Process isolation for backtests (COMMITTED).** `qmb/src/qmb/orchestrator/spawn.py`: one OS process per run, separate output directory per run id, per-run time and memory limits (`qmb_run_time_limit`, `qmb_run_memory_limit`), a cancel token, and a resource governor; a breach kills only that process. Related: `qmb/src/qmb/orchestrator/watch.py`, `qmb/src/qmb/host/runner.py`. This is the nearest existing thing to a per-job sandbox, and it is not a container.

**In-process pack code (COMMITTED, important).** `qma-daemon/.../plugins/packs.py` function `load_pack_activator` loads the pack's `daemon/plugin.py` with `importlib.util.spec_from_file_location` + `exec_module` INSIDE the daemon process. There is no process or container boundary around pack Python today. Guard rails are static only: `qma-core/.../plugins/boundaries.py` bans `subprocess`, `socket`, `asyncio`, `urllib.request`, `pathlib`, file `open` etc. in `qma-core`, and the daemon refuses forbidden model adapters and reach tokens at registration. Those scans cover first-party code; they would not contain a hostile or sloppy generated pack.

**Secrets (COMMITTED).** `daemon/proxy/broker.py`: credential references, never values; Windows Credential Manager is the sole v1 backend; no enumeration of the store. `daemon/proxy/egress.py`: a resolved secret exists only inside an egress frame. Env-var allowlist per environment (CT-46). Node side: `qmn/src/qmn/secrets`, `qmn/deploy/{creds,secrets_provision}.py`.

**Network egress rules (COMMITTED for the trading node only).** `qmn/deploy/network.py`: inbound default-deny, exhaustive outbound allow-list by class, loopback/unix-socket doors. For QMA environments the rule is only "network field required and not empty".

**Compute vendors (DOCS-ONLY, with a conflict).** GAP-0075 (`docs/gap-report.md` line 297): "Modal, Daytona and E2B are rejected outright on cost and fit"; sandbox exists "for backtesting fan-out first". Remote GPU/cloud (the operator's Colab/AWS/GPU wish) is listed as a UI-side ask in `apps/qmx-ui/BACKEND-REQUIREMENTS.md` ("Lab" section) and needs a ruling; B-9 says only the controlled machine sees governed data.

---

## 4. Safety and operations

- **Circuit breakers: none as a mechanism.** The phrase appears only in research and recovery notes (`workroom/research/*`, `archive/recovery/*`). The nearest real things: the KSA protection fold and effect matrix (below), retry ceilings (`daemon/retry.py`), `max_in_flight` caps, and per-run resource limits in QMB.
- **Kill switch / KSA (COMMITTED, trading node only).** `qmn/src/qmn/protection/{ksa,effect_matrix,dispatch,windows}.py`: five levels GREEN to BLACK, scoped per venue and account, monotone, operator-only `resume`. Money-path acts for agents are denied in `qma-core/.../barriers/money_path.py`. There is NO per-mini-app kill switch. Matrix VALUES are an open operator ratification (GAP-0050).
- **Retry (COMMITTED).** `daemon/retry.py`: default host retry only for effect classes `none` and `read`; never blind retry of external sends; ceiling is a registry row (value not minted).
- **Rate limits.** Only data-intake adapters (`packages/qmf-data/src/qmf/data/{ingest,dukascopy,calendar_feed}.py`) and venue capability descriptions. None per pack.
- **Health (COMMITTED).** Instance `health()` query (`daemon/discovery/instance_health.py`); five readiness axes shown by the UI plan. QMN has its own health states (`qmn/src/qmn/observability`).
- **Logging (COMMITTED).** `daemon/operator_log.py`: stdlib JSON-lines with `ts, level, event, correlation_id`, plus `instance_id, op_id, logical_invocation_id, graph_run_id` when known. Rule: logs are not evidence and not journals (`daemon/observability_boundary.py`).
- **Diagnosis (COMMITTED).** `daemon/diagnosis.py`: failure class is a closed set `grant | workflow | view | dependency | host` plus JobHandle plus correlation id (Story 61.2). Nothing here is per-container.
- **Metrics / tracing (COMMITTED, partial).** `daemon/telemetry/store.py`: harness-authored trace/metric store (a model-authored hook that writes telemetry is refused). `daemon/telemetry/export.py`: an export PORT where an OpenTelemetry-shaped adapter may be plugged in at composition time; "never imports the OpenTelemetry SDK into the daemon core". So no actual OpenTelemetry wiring yet.
- **Dashboards and alerts (COMMITTED, node only).** `qmn/deploy/observability/` Prometheus + Grafana + Loki with alert seeds, scraping `127.0.0.1:8787/metrics` of the node. A closed alert allow-list for the node (DEC-0257). Nothing aimed at mini apps.
- **Ruling to respect:** "Do not mint a fourth observability product" and "Do not extend `qmn/FAILURES.md`" (ADR-0025 kit AD-5, DEC-0456; `daemon/observability_boundary.py`). Per-mini-app dashboards would need to sit inside these rules or amend them.

---

## 5. Testing and promotion gates reusable for mini apps

**Bot pipeline (COMMITTED for the node, DOCS for the rest).**
- Research and registry: QML research Stage 0 (`qml/` research types, epics 49 to 52 on separate branches, unmerged branches `epic/050`, `epic/051`, `epic/052`), registry lineage and gate evidence (`docs/contracts/ct-06`, `ct-08`, `ct-11`, ADR-0015).
- Paper: Book-level paper mode only, routed to a paired demo account (`qmn/src/qmn/paper/{transition,routing,demotion,first_deployment,fx_claim}.py`, ADR-0009). Ruling DEC-0261: no per-bot paper lane on the node. Bots arrive "backtested, paper-tested outside the node and operator-approved" (`qmn/src/qmn/paper/lane.py`). So there is NO paper stage for a thing that is not a trading bot.
- Promote and activate: `qmn/src/qmn/promotion/{battery,lifecycle,hub,passive_hub,journal}.py`. Human click, a silent precondition battery, activation a separate act taking effect at the next day boundary; artifacts with `provenance = sandbox` are refused at publish and at pull (`promotion/hub.py`). That is a ready-made pattern for "proven before live", but it is specific to bots and the trading node.
- Soak: one unattended week on the demo account, tracked by the separate observability stack (DEC-0194, DEC-0212). Replay as a separate process (`qmn/src/qmn/replay`).

**CI (COMMITTED).** `.github/workflows/{battery,skylos,qmn-ubuntu-24.04}.yml`. Required checks (per `session-epics-70-73.md`): `skylos`, `check`, `vulture`, `agents`, `qmn-ubuntu-24.04`. `battery.yml` runs `uv run poe check` (formatting, lint, types, tests, coverage, four scanners), a Vulture dead-code gate, and a nightly mutation-testing job (mutmut) on node money-path modules. `qmx-agents` has its own gate. Factory enforcement work (Codex branches `codex/factory-enforcement-*`) hardens receipts and CI isolation. Reticle (`apps/qmx-ui/.reticle`) drives the real UI for user-facing changes.
- Last full-gate figure: 5,218 application tests and 348 tooling tests passed on Epic 73 (`session-epics-70-73.md`).

**Reusable ideas, in plain terms:** (a) the "sandbox provenance is refused at promotion" idea; (b) the silent precondition battery; (c) promote-then-activate as two human acts; (d) the three-layer review plus deterministic gate used by the factory (blind defect, edge case, verification gap). None of these exist as a generic "promote a mini app" workflow.

---

## 6. Data access

- External sources: contract CT-15 (`docs/contracts/ct-15-external-source-adapter.yaml`) owned by `qmf-data` ingest; active providers are Dukascopy and the Forex Factory calendar feed; cTrader is "intended". Code: `packages/qmf-data/src/qmf/data/{ingest,dukascopy,calendar_feed}.py`. Scheduling, retries and supervision belong to applications, not the library.
- Venue and live data: `packages/qmf-venue` (CT-18 to CT-21) and `qmn/src/qmn/venue`; the node records live data and runs a news recorder (`recorder/`).
- Storage: SQLite (daemon: single sole-writer sqlite, `daemon/persistence/`; registry), DuckDB/pyarrow via `qmf-data`, JSONL run logs in QMB, content-addressed `fp1` artifacts. `qma-core/.../barriers/dependencies.py` and reachability barrier restrict what agents can touch.
- A mini app with its OWN database or its OWN external API is not covered: the closed contribution set has no "storage" or "connector" point, and pack migrations (`plugins/migrations.py`) act on daemon-owned stores.
- UI-side asks not yet in docs (flagged "needs a ruling" in `apps/qmx-ui/BACKEND-REQUIREMENTS.md`): news feed, RSS/API source subscriptions, live exchange streams for charts (spot crypto only), ML model as a first-class object with slots.

---

## 7. Gaps: what does NOT exist for a mini-app runtime

1. No container launcher or sandbox runner (only declarations, validators and a router). No image build or pin pipeline for packs.
2. Pack Python runs in the daemon process (`exec_module`); no process, container or permission boundary around generated code.
3. No per-app resource budget (CPU, memory, disk, tokens, spend) beyond QMB per-run limits and `max_in_flight`.
4. No per-app egress allow-list enforcement for QMA environments (field required, content unchecked beyond refusals); no proxy for outbound calls from a pack.
5. No circuit breaker, no per-app kill switch, no automatic quarantine on repeated failure.
6. No per-app metrics, traces or dashboards; OpenTelemetry is only an unwired port; the "no fourth observability product" ruling constrains this.
7. No "prove before live" workflow for mini apps: no mini-app test harness, no shadow/replay for app behaviour, no paper stage for non-bot apps, no promote/activate states for packs.
8. No inter-app data feed contract ("feed each other"): packs talk only via operations through the host; no app-to-app subscription, shared schema registry or widget data contract.
9. No pack registry, signing, versioned distribution, rollback of a pack version (only reload), or dependency approval.
10. No ML artifact entity (the UI shows model slots; docs lack the entity).
11. Agent runtime replacement: no LangChain/LangGraph code, no decision record, ADR-0020's rejection still stands on paper; copilot "builds an app overnight" needs a build-agent seat, a draft-to-pack path beyond graph templates (Epic 71 only publishes `graph_template`), and overnight scheduling that survives laptop-off (the continuation host exists as a contract; the UI backlog asks for a server).
12. Wire gaps: `start_mission`/`launch_task` not implemented; UI has no live transport.
13. `view:` and `mcp-app` rendering exist only as request fields; no sandboxed iframe host, no json-render catalog code in the backend.

---

## 8. Conflicts with the sandbox / container idea (rulings that would need amending)

- ADR-0019 / DEC-0200 / DEC-0201: containers only for the observability stack on the VPS; the node must never need Docker. Single-machine placement variant (GAP-0058, DEC-0262) IS allowed containers, but its design is "owed" and not written. Mini-app containers belong on the workstation/single-machine side, never on the node VPS.
- GAP-0075 / DEC-0316: Modal, Daytona and E2B are rejected outright; "local Docker" and own remote container/host are the sanctioned kinds. "Agent sandboxes" as a hosted service contradict this unless re-ruled.
- Desktop (Windows) environment kind is unprovisioned (GAP-0070); Docker on this Windows workstation is the stated default but nothing has been run against it.
- `qmn/FAILURES.md` must not be extended; mini-app failure ids live in the owning package (`daemon/observability_boundary.py`).
- Logs are never evidence (DEC-0456): a "proof" of a mini app cannot be its logs; it must be journaled evidence or test results.
- Money path: agents and packs cannot reach venue/broker (`barriers/money_path.py`, `daemon/envs/boundary.py` refuses trading-node hosts); any mini app that wants to trade must go through the bot pipeline.
- ADR-0020 rejected hosting LangGraph loops; the 2026-10-04 operator direction reverses it. Needs a new ADR and a review of which QMA subsystems stay.
- UI rule "the browser never spawns Python and never holds credentials" and "widgets never call the wire" (ADR-0026): any mini-app UI must be rendered through the host issuers, which limits iframe/MCP-App design.
