# Repo core baseline — live inspect (2026-09-23)

Read-only inspect of the live trees. Not architecture. Not a stack pin. Not a claim that types are a product UI.

This report answers: **what can a future UI actually talk to today**, versus what is specified on `main` dirt, versus what is a fixture.

## Pins verified

| Tree | Path | HEAD | Match |
|---|---|---|---|
| integration inspect | `C:/Users/Mubarak/Desktop/QMX/.worktrees/integration-inspect` | `34c148be404a375cbfd79fd4ce6997452e4f1d20` (`34c148b story 59.5: grant refuses the wrong instance or config revision`) | **yes** — clean, `integration...origin/integration` |
| main (dirty; not modified here) | `C:/Users/Mubarak/Desktop/QMX` | `92279dfe43922d60fabe38e29284ca52956ab75c` (`92279df main apps`) | **yes** — dirty docs/planning checkout |
| ui worktree | `C:/Users/Mubarak/Desktop/QMX/.worktrees/ui` | `af6628888fb8901bf9e877cbd07e438dbb0f39b4` (`af66288 Epics and stories: 23 epics, 131 stories…`) | **yes** — old planning SHA; **no** `qmx-agents` / `qmb` / `qml` / `packages` |

Evidence paths below are relative to **integration-inspect** unless tagged `main-dirty` or `ui-worktree`. Other worktrees (epic-049 etc.) were not touched.

## Honesty (do not skip)

1. **Types at `34c148b` are not e2e** (DEC-0286, DEC-0465). Class + pytest existence is in-process proof, not a live JSON-RPC session, not a browser, not a sidecar.
2. **Do not invent a UI SDK.** `stack.md` “QMA SDK” means `qma-core` + `qma-wire` + `qma-daemon` (`qma.*`). Pack-and-grant as “the SDK” is **sitting law on uncommitted ADR-0025**, not a package at `34c148b`. `qma-ui-contract` is a deferred stub (`STUB.md` only).
3. **Do not use `270e992` for “envelope/grant/product_session types are missing.”** Those types exist at `34c148b`. `270e992` remains the parent freeze for **ADR-0024 original Decision text** only.
4. **Nothing in this report is `runtime-observed`.** The daemon was not started. The TCP listener, if bound, swallows bytes and does not speak JSON-RPC or WebSocket.
5. **ADR-0024 is not on integration HEAD.** ADR-0025, the pack-and-grant rider, and SCN-0024 are **uncommitted on main**.

## Classification legend

A capability may carry more than one tag. Tags are not a ladder that turns a fixture into a product.

| Tag | Meaning here |
|---|---|
| **implemented** | Importable Python types/services exist and construct in-process |
| **specified** | Docs / CT-40 annotation / ADR / SCN describe intended behavior |
| **stubbed/fixture** | Explicit stub, in-memory overlay, named fixture, or a bind that does not implement the protocol |
| **tested** | pytest (and often `examples/*_usage.py`) round-trips the types in-process |
| **runtime-observed** | A live process was seen serving the contract — **none** |
| **absent** | No identifier in integration Python at `34c148b` |

## Docs vs inspect SHA

| Artifact | Where | Git state |
|---|---|---|
| `docs/architecture/stack.md` | integration HEAD | present; QMA stack rows (JSON-RPC 2.0, websockets 17.1, MCP adapter surface). **No UI layer.** “QMA ships no command line.” |
| `_docwork/riders/pack-and-grant-kit-2026-09-23.md` | **main-dirty only** | untracked; **absent** on integration HEAD |
| `docs/decisions/ADR-0024-workflows-construction-kit.md` | **main** @ `92279df` + local `M` | **absent** on integration HEAD. Working tree adds DEC-0461..0465 follow-ups. Original Decision freeze remains `270e992` (DEC-0450) |
| `docs/decisions/ADR-0025-pack-and-grant-kit.md` | **main-dirty only** | untracked (`??`); **not in** `92279df`; **absent** on integration |
| `workroom/…/SCN-0024-optional-copilot-headless.md` | main-dirty workroom + `docs/scenarios/` untracked | specification of intended behavior; **explicitly not executed proof** at `34c148b` |
| `architecture-QMX-2026-09-23/IMPLEMENTATION-SEQUENCE.md` | main-dirty planning | planning only. Step 0: treat `34c148b` fixtures as connect/amend, not e2e. UI chrome (GAP-0081) is **not** this epic set |

ADR-0025 wiring honesty @ `34c148b` (DEC-0465) matches this inspect:

- **CONNECT (types/fixtures, not e2e):** InvocationEnvelope, GrantRecord, `product_session` / `ProductSessionProfile`, effect-class + `reconcile_policy`, `call_depth` / `parent_logical_invocation_id`, Workflows 53–59 fixtures.
- **AMEND still needed:** `ProductSession.app_instance_id` is required `str`; `SELECTED_REF_KINDS` lacks `instance_id`; envelope has **no** `caller_kind`.
- **ABSENT as product surface:** pack `copilot_profile`; daemon stdlib JSON-lines; kit `failure_class`; default host retry loop; nested Mission invoke as first-class; CheckpointManifest.

## Capability table

| Name | Owner COMP | Evidence path:line | Classification | UI consequence |
|---|---|---|---|---|
| `ProductSessionProfile` `{authoring, app-use}` | COMP-QMA-DAEMON | `qmx-agents/packages/qma-daemon/src/qma/daemon/sessions/product_session.py:271` | implemented + tested (not e2e) | Two seats only. Home/main with no app is **specified** as authoring-with-absent-instance (ADR-0025 / SCN-0024); **code still requires** `app_instance_id`. No third profile. |
| `product_session` (`psess:`) journal projection | COMP-QMA-DAEMON | `…/product_session.py:733` (`ProductSession`); sqlite table `:261`; service `:1156` | implemented + tested; **not composed into `DaemonProcess`** | Session owns grants/context; tabs do not. UI must not treat a tab id as `psess:`. Two tabs of one product share one row (tests). Closing a tab writes nothing. |
| `AUTHORING` / `APP_USE` | COMP-QMA-DAEMON | `…/product_session.py:277`; change-request fixture `…/staging/change_request.py:703` | implemented + tested (fixture for apply path) | App-use may mint `change_request`; must not apply. Authoring + operator principal applies. Panel cannot be an apply door. |
| `app_instance_id` required `str` | COMP-QMA-DAEMON | `…/product_session.py:741`, parse `:1096` | implemented (required) — **named amend not applied** | Authoring-without-instance (kit AD-3 / DEC-0463) is **specified, absent in code**. UI home cannot omit instance until FEAT-0058-class work. |
| `selected_refs` kinds | COMP-QMA-DAEMON | `…/product_session.py:219` | implemented; **no `instance_id` kind** | Cannot pick an instance via `selected_refs` today. Kit law wants that kind for authoring invoke. |
| `GrantRecord` immutable | COMP-QMA-WIRE (DTO) + COMP-QMA-DAEMON (sqlite beside session) | `qma-wire/…/invocation_envelope.py:474`; `grant_record.py:1`; daemon `…/sessions/grant_binding.py:201` | implemented + tested (not e2e) | Host grants, manifests request. UI must show grant ids, never treat enablement as a grant. |
| `GrantRevocation` append-only | COMP-QMA-WIRE + COMP-QMA-DAEMON | `qma-wire/…/grant_record.py:233` | implemented + tested | Revoke does not mutate minted bytes. UI must not expect `revoked_at` on the GrantRecord. New dispatch refuses; already-accepted work may finish. |
| `InvocationEnvelope` | COMP-QMA-WIRE | `…/invocation_envelope.py:109` (fields), `:647` (class) | implemented + tested (not e2e); **not on the live TCP listener** | Every public call must carry it. `instance_id` **required** on invoke (stays required after kit). Crypto algorithm still `GAP-DESK-ENVELOPE-CRYPTO`. |
| `caller_kind` `user\|agent\|workflow` | COMP-QMA-CORE + COMP-QMA-WIRE (specified) | grep over integration `*.py` / `*.yaml`: **0 hits**; ADR-0025 kit AD-4 | specified; **absent** at `34c148b` | UI/agent/workflow callers are indistinguishable on the envelope. Do not emit `caller_kind` until the named amend lands. |
| `ContributionHit` | COMP-QMA-WIRE | `…/federated_discovery.py:642` | implemented + tested (not e2e) | Third federated class. Identity is live `published_contributions()` tuple, never fp1. Hit ≠ grant. |
| `view:*` presentation DTO | COMP-QMA-WIRE | `…/view_presentation.py:1`; schema `schemas/view_presentation.v1.schema.json:5` | implemented as DTO + tested; **not a contribution point** | Chrome may mount a DTO. Mount/dispose must not start/kill work. Not a ContributionHit. GAP-0081 chrome unfilled. |
| `copilot_profile` | COMP-QMA-CORE + COMP-QMA-DAEMON (specified) | grep integration: **0 hits**; `PluginManifest` `…/manifest.py:73` has no such field; SCN-0024:19 | specified; **absent** | Headless packs (omit profile) are valid in kit law, not encoded. Do not require a copilot panel to ship or invoke. |
| qma-wire JSON-RPC method vocabulary | COMP-QMA-WIRE | `…/vocabulary.py:53` commands, `:71` queries, `:95` events | implemented as closed enums + schemas + tested | Commands (9): `start_mission` `send_message` `steer_agent` `stop_run` `approve_hook_action` `install_enable_plugin` `update_configuration` `launch_task` `retry_task`. Queries (11): seed 7 + `list_mission_hooks` `plugin_install_preflight` `facade_search` `facade_get`. Events (10) `noun.verb`. **Daemon does not dispatch these over the socket.** |
| JSON-RPC 2.0 `initialize` handshake | COMP-QMA-WIRE | `…/initialize.py:1`, `JSONRPC_VERSION` `:46` | implemented as types + tested | MCP-style handshake types exist. No live server uses them. |
| Family transports (spec) | COMP-QMA-WIRE | `…/families.py:29` | specified in types | Commands claim `jsonrpc_websocket`; queries `http_get`; events `durable_stream`. **No `websockets` import anywhere in integration Python.** `qma-wire` pyproject: “No client implementation.” `qma-daemon` has no websocket/http extra. |
| `wire.attach` / `since_seq` / detach | COMP-QMA-WIRE | `…/attach.py:104` (`AttachRequest`), `:291` (`ClientAttachmentState.attach`) | implemented as **client-state types** + tested | Attach is client subscription only. `since_seq=0` is read-only replay. Detach / tab-close must not cancel JobHandles. Not wired through `DaemonProcess._handle_client`. |
| `JobHandle` (QMA AD-17 vocab) | COMP-QMA-CORE (def) + COMP-QMA-DAEMON (service) | `qma-core/…/ports/jobs.py:264`; states `…/vocabulary/enums.py:169`; daemon `…/envs/jobs.py:177` | implemented + tested (in-memory store + dispatcher tests) | States: `queued\|running\|done\|failed\|cancelled\|aborted\|unknown`. Never `succeeded` / `awaiting_approval`. UI cancel = `JobHandle.cancel` only. Store is a **dict**, not a wire RPC. |
| QMA Session (`sess:`) vs `psess:` | COMP-QMA-CORE ontology + COMP-QMA-DAEMON | `product_session.py:132` prefixes; envelope forbids `sess:` as session ref (`invocation_envelope.py:142`) | implemented as distinct ids | Engine run ≠ product session ≠ tab. Copilot chat must not rename `sess:` into a third profile. |
| Task Graph durable projection | COMP-QMA-DAEMON | `…/taskgraph/projection.py:1`; bound in `process.py:223` | implemented + tested; composed into `DaemonProcess` | Edges/outbox/join live in daemon sqlite when the process is composed. UI observes via queries/events **once a protocol server exists**. |
| `DaemonProcess` listener | COMP-QMA-DAEMON | `…/process.py:106`, bind `:358`, `_handle_client` `:418` | **stubbed** TCP bind + tested compose/bind | Binds loopback (`127.0.0.1:8765` default). `_handle_client` reads chunks and discards them. **Not JSON-RPC, not WebSocket, not CT-40 dispatch.** UI cannot attach to this as a wire client today. |
| `get_provider_health` query name | COMP-QMA-WIRE | `vocabulary.py:88` | specified as enum member only | Name exists. **No daemon method.** Not pack instance `health()`. |
| Listing axis `healthy` | COMP-QMA-DAEMON | `…/discovery/listing.py:155` (`_healthy` set), `:184` `note_healthy` | stubbed/fixture + tested | In-memory overlay, operator-noted. Independent of published/configured/granted/reachable. **Not** instance `health()`. |
| Pack / instance `health()` | COMP-QMA-DAEMON (specified) | grep `def health(` in qma-daemon: **none**; kit AD-5 | specified; **absent** | Copilot/CLI diagnosis cannot call instance health yet. Do not confuse with QMN `IndependentHealthReport.health()` (`qmn/src/qmn/observability/health.py:143`) — that is the trading node, not a pack. |
| Daemon JSON-lines / `failure_class` | COMP-QMA-DAEMON + COMP-QMA-WIRE (specified) | grep `failure_class` / JSON-lines in qma-*: **0 hits** | specified; **absent** | UI/copilot cannot join operator logs to invocations on a daemon logger. QMN has its own JSON-lines plane; do not extend `qmn/FAILURES.md`. |
| json-render / MCP Apps | COMP-QMA-WIRE DTO law | `research_surface.py:90`; `view_presentation.py:7` | specified as adapters; **absent** as packages | Constants force `json_render_stores/executes = false`, same for MCP Apps. Do not pin `@json-render/*` or `@modelcontextprotocol/ext-apps` into core. Optional UI adapter later. |
| Svelte / Tauri / React / Vite | (none in repo) | `git ls-files` `package.json` `Cargo.toml` `*.svelte` `tauri.conf`: **empty** on integration HEAD | **absent** | No frontend workspace. `15-stack-currency-orchestrator.md` is a **proposed seed**, not installed. ui-worktree `af66288` is BMad epics, not an app. |
| `qma-ui-contract` | COMP-QMA-WIRE / GAP-0081 | `qmx-agents/packages/qma-ui-contract/STUB.md:1`; not a uv workspace member (`qmx-agents/pyproject.toml:22`) | stubbed | No UI SDK, no `ui_view` contribution point. GAP-0081 remains the chrome hole. |
| `facade_search` / `facade_get` | COMP-QMA-WIRE (names) + COMP-QMA-DAEMON (`FederatedDiscoveryService`) | `vocabulary.py:91`; `…/discovery/federated.py:379` | implemented as in-process concatenate + tested; **not in `DaemonProcess`** | Concatenates CT-44 knowledge + injected `library.search` + `published_contributions()`. Occupancy none. Ranked/semantic/hybrid = unsupported (GAP-0073). Hypotheses refused here. |
| QMB `library.search` | COMP-QMB | `qmb/src/qmb/registryread/search.py:122` (`command: library.search`); CLI tree `qmb/src/qmb/doors/cli/tree.py` | implemented + tested | Real library API over registry-as-of + ledger merge + experiment ledger. Daemon must inject a port; **never `import qmb`**. UI library rail = this command / ArtifactHit, not a fourth store. |
| `qml.research` Stage 0 | COMP-QML | `qml/src/qml/research/__init__.py:1`; `stage0.py:1` | implemented + tested | Hypotheses / mill live here, **off** the federated facade. Descriptor catalog lists `qml.research.browse` (`qma-core/…/operations/catalog.py:188`) as an op_id — library door, not a QMA wire method. |
| Operator CLI | COMP-QMB | `qmb/pyproject.toml:20` `qmb = "qmb.doors.cli:main"`; QMA `__main__.py:3` “Not an operator command line” | implemented (qmb); **absent** (qma/qmn CLIs) | UI must not mint `qma-cli` / `qmn-cli`. Headless invoke path in SCN-0024 is CLI/wire — CLI means **qmb** plus future wire, not a new binary. |
| QMB door from daemon (`CliQmbDoorTransport`) | COMP-QMA-DAEMON | `…/backtest/cli.py:1`; composed in `test_daemon_process.py:70` | implemented + tested (process spawn / test double) | Agent → backtest tool → subprocess `qmb`. Daemon never imports `qmb`. Cancel maps to QMB abort in this transport (changelog still notes older gaps — treat as story-scoped). |
| Local-proxy / OpenCodex + Credential Broker | COMP-QMA-DAEMON | `…/proxy/local_proxy.py:1`; `…/proxy/broker.py:1` | implemented + tested (memory backend; WinCred protocol) | Provider credentials stay **outside** QMA. Local proxy: loopback + `auth_mode: none` + no `credential_ref`. Wire auth carries `credential_ref` strings only. UI must never inline secrets. |
| Frontend package (`apps/`, `ui/`, `web/`) | — | integration `ls-tree` top-level: no `apps`/`ui`/`web`; main HEAD same (docs checkout) | **absent** | UI sitting starts from zero application package. Do not treat `archive/ui-ux-before-2026-09-23` (main-dirty untracked) or ui-worktree planning HTML as the product. |
| Nested Mission invoke (workflow→workflow) | COMP-QMA-DAEMON (specified) | `start_mission` is a **wire type name** only; no nested-Mission first-class verb in daemon | specified; **absent** as product surface | Envelope has `call_depth` / `parent_logical_invocation_id` types. Merging live Task Graphs stays refused. UI must not draw two graphs as one run. |
| Default host retry (`none`/`read`) | COMP-QMA-CORE effects + COMP-QMA-DAEMON (specified) | `retry_task` command name; join `plan_partial_retry`; restart fixture blind-retry refusals — **no host retry loop** | specified; **absent** as kit loop | UI must not invent per-pack retry. `retry_task` is a seed wire command type, not the kit default loop. Ceiling number not minted (GAP-0108). |

## What `DaemonProcess` actually composes

`DaemonProcess.compose` (`process.py:133`) wires:

- persistence substrate + sole sqlite writer
- authoritative journal
- ExperimentSpec / Experiment Ledger sqlite
- `TaskGraphStateService` durable bind
- desk plugin roster + backtesting (`CliQmbDoorTransport`)
- loopback TCP listener

It does **not** compose: `ProductSessionService`, `GrantSqliteStore`, `FederatedDiscoveryService`, `ContributionListingService`, JSON-RPC dispatcher, HTTP query server, WebSocket, instance `health()`, JSON-lines logger.

So: several Workflows 53–59 modules are real Python with tests, and still **not** the process a UI would dial.

## Wire surface a UI would need (today vs specified)

**Today at `34c148b` (types you can import, not a socket):**

- Envelope frame + `scope_path` order desk→…→subagent (`envelope.py:39`) — **no `product_session` segment**
- Closed command/query/event names (`vocabulary.py`)
- `initialize` JSON-RPC 2.0 frames (`initialize.py`)
- `attach(scope, since_seq)` client-state (`attach.py`)
- Federated hit union KnowledgeHit | ArtifactHit | ContributionHit
- InvocationEnvelope / GrantRecord DTOs + JSON schemas under `qma-wire/schemas/`
- `view:*` DTO

**Specified, not in this process:**

- Live `jsonrpc_websocket` + `http_get` + durable event stream (stack.md QMA rows; `families.py`)
- `websockets` 17.1 (stack.md:200) — **unpinned in code; zero imports**
- MCP 2026-07-28 as ToolAdapter surface (stack.md:202) — adapter law, not a UI Apps host
- `caller_kind`, optional authoring instance, `copilot_profile`, diagnosis `failure_class`, instance `health()`

**Forbidden to treat as UI identity:** json-render catalog, MCP App HTML, board layout, tab ids.

## Library / search rails (UI discovery)

Four rails already bound in types (ADR-0024 AD-2 / DEC-0415), with code at `34c148b` as concatenate + refusals:

1. **KnowledgeHit** — daemon `KnowledgeService` (CT-44 / plain-file research seed).
2. **ArtifactHit** — QMB `library.search` (fp1 / kind).
3. **ContributionHit** — live `published_contributions()` tuple.
4. **Hypotheses** — `qml.research` only; federated search **refuses** them.

UI search is a client of `facade_search` / `facade_get` **once dispatched**. Until then, QMB CLI `library.search` is the only operator-reachable library door.

## CLI, proxy, credentials

- **Single operator CLI:** `qmb` (click 8.4.2). QMA `__main__` is a process entry (`QMA_DAEMON_ROOT` / bind port), not a product CLI.
- **QMA→QMB:** subprocess door, no `import qmb`, occupancy one run per ExecutionEnvironment.
- **Model proxy:** OpenCodex-shaped local proxy; credentials not in QMA namespace; Credential Broker is exact-ref OS store (Windows Credential Manager v1; memory backend in tests).
- **Wire auth:** `credential_ref` before protocol bytes (`qma-wire/auth.py`). Secrets on a wire surface refuse.

UI first-run must not become a secret form that bypasses the broker.

## Frontend / chrome

| Question | Answer at live inspect |
|---|---|
| Is there an `apps/`, `ui/`, `web/`, Svelte, Tauri, or `package.json`? | **No** on integration HEAD. **No** on ui-worktree `af66288`. |
| Is `qma-ui-contract` a package? | **No** — `STUB.md` only, excluded from uv members. |
| Is GAP-0081 filled? | **No** (`GAP_0081_CHROME_FILLED = False`; gap-report `:211`). |
| Are json-render / MCP Apps installed? | **No**. Honesty constants say they do not store or execute. |
| May the UI sitting pin those SDKs into Python core? | **No** (ADR-0024 AD-17; ADR-0025 kit AD-8; rider). |

Proposed Svelte/Tauri versions live in `research/15-stack-currency-orchestrator.md` as **orchestrator web check**, not as repo baseline.

## SCN-0024 vs code

SCN-0024 (workroom + uncommitted `docs/scenarios/`) says: omit `copilot_profile` is valid; headless invoke via CLI/wire; optional panel cannot apply; tab close does not cancel; **do not claim `copilot_profile` exists at `34c148b`**.

Code agrees on the last point (absent). Change-request apply law exists as **`ChangeRequestFixture`** (`change_request.py:1`) over `ProductSessionService`, not as a wire method.

## Implementation sequence (planning, not a gate)

From `architecture-QMX-2026-09-23/IMPLEMENTATION-SEQUENCE.md`:

0. Honesty: `34c148b` fixtures = connect/amend, not e2e.  
1. Host SDK: optional `copilot_profile`; optional authoring `app_instance_id`; `caller_kind`.  
2. Daemon JSON-lines + diagnosis query.  
3. Default retry on existing effect-class matrix.  
4. Nested Mission invoke.  
5. Listing axes + instance health.  
6. **UI chrome (GAP-0081) consumes the same queries. Not this epic set.**

This UI architecture sitting consumes (5) and (6) as **contracts to design against**, not as shipped APIs.

## UI sitting implications (plain)

- There is **no app to inspect**. Design against **qma-wire types + qmb CLI + qml.research**, and against **specified holes**.
- Do not build chrome that assumes `caller_kind`, optional home instance, `copilot_profile`, instance `health()`, or a JSON-RPC WebSocket server already run.
- Do not treat listing `healthy` or QMN `/health` as pack health.
- Do not make widgets invoke. Views are DTOs. Grants live on `psess:`.
- Do not start a sixth COMP or a new CT. Additive CT-40 only.
- Headless must remain first-class (SCN-0024). A copilot panel is optional chrome over app-use, not the product.

## What this inspect did not do

- Did not run pytest, the daemon, or qmb.
- Did not modify any tree except this report.
- Did not treat handoff historical inventories as truth; every capability row was grepped/read at `34c148b`.
- Did not interrupt other worktrees.
