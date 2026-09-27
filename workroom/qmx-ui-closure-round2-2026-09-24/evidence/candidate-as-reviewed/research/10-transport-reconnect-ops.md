# Transport, reconnect, and the real command/query path

Research only. Not architecture. Not an implementation brief. Do not invent a UI middleware service or a fourth store.

**Inspect SHA:** `integration@34c148b` (`34c148be404a375cbfd79fd4ce6997452e4f1d20`, `story 59.5: grant refuses the wrong instance or config revision`) at `C:/Users/Mubarak/Desktop/QMX/.worktrees/integration-inspect`.

**Parent freeze for ADR-0024 original Decision:** `270e992` (DEC-0450). Types at `34c148b` are CONNECT, not e2e (DEC-0286, DEC-0465).

**XR-01..XR-08** in `workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/interaction-runtime-draft.md` are **proposals**, not accepted sitting law. They are used here only as intent labels to map onto existing contracts.

---

## 0. Verdict in one paragraph

The UI is a **client of `qma-wire` (CT-40) talking to `qma-daemon`**. Commands mutate over JSON-RPC 2.0 WebSocket and ack immediately; queries read durable snapshots over HTTP GET; progress rides a durable event stream via `wire.attach(scope, since_seq)`. Snapshots are truth; events are not. Closing a tab is `wire.detach` / client attachment drop — it never calls `JobHandle.cancel`. Durable work is a `JobHandle` (QMA AD-17 restated by parent AD-26). Product context is a daemon journal projection `psess:` (`product_session`), not a QMA `sess:` and not a tab. Public invoke carries `InvocationEnvelope` on every hop; the host compares it to GrantRecord + descriptor before execution. Reconnect is a **query** (`producer_id` stable, `since_seq` / `(resume_cursor, cursor_generation)`, then `JobHandle.reattach`). Never replay unacked intent. Never blind-retry `external-egress`. Logs are not journals. There is already a QMN localhost HTTP evidence door; do not clone it as a second QMA REST bus. At `34c148b` these are **types, schemas, and in-process fixtures**. `DaemonProcess.bind()` is a loopback TCP byte-eater, not a live JSON-RPC/HTTP server. Class existence is not e2e.

---

## 1. Sources read

| Kind | Path |
|---|---|
| Parent contracts | `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-18/CONTRACTS.md` §§1b, 3, 6, 14, 15 |
| Parent UI host | `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-18/UI-HOST.md` |
| Parent spine | same sitting `ARCHITECTURE-SPINE.md` AD-16, AD-17, AD-21, AD-24, AD-26 |
| Pack-and-grant contracts | `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-23/CONTRACTS.md` |
| XR proposals | `workroom/qmx-ui-architecture-handoff-2026-09-23/evidence/session/interaction-runtime-draft.md` |
| Experience §6 | `workroom/qmx-ui-architecture-handoff-2026-09-23/03-EXPERIENCE-SCOPE.md` §6 |
| Ratified wire | `docs/components/qma-wire.md`, `docs/contracts/ct-40-qma-wire-envelope.yaml` |
| Ratified daemon | `docs/components/qma-daemon.md`, `docs/contracts/ct-46-qma-execution-environment-job.yaml` |
| Logs vs evidence | `docs/lenses/observability/logging-spec.md`; parent AD-16; SCN-0027 |
| Code @ 34c148b | `qmx-agents/packages/qma-wire/src/qma/wire/{envelope,families,vocabulary,initialize,attach,auth,idempotency,listener,outbox,invocation_envelope,contribution_listing,view_presentation,host_request,correlation}.py` |
| Code @ 34c148b | `qmx-agents/packages/qma-daemon/src/qma/daemon/{process,sessions/product_session,sessions/chrome,envs/jobs,discovery/listing,proxy/broker}.py` |
| Code @ 34c148b | `qmx-agents/packages/qma-core/src/qma/core/{ports/jobs,ports/cancel_authority,operations/{descriptor,doors,effects}}.py` |
| QMN evidence HTTP | `qmn/src/qmn/doors/http/evidence.py`, `qmn/src/qmn/observability/health.py` |
| Kit honesty | `docs/scenarios/SCN-0026-host-retry.md`, `SCN-0027-diagnosis-json-lines.md`; DEC-0465 |

---

## 2. The only command/query path (no new middleware)

```
UI host (chrome, json-render, MCP App HTML)
    │  never identity, never grant, never occupancy
    ▼
qma-wire CT-40
    commands  → JSON-RPC 2.0 WebSocket   (ack now; effects async)
    queries   → HTTP GET snapshots       (authoritative)
    events    → durable stream           (not authoritative)
    │
    ▼
qma-daemon  (sole writer of journal / sqlite / artifacts)
    │  InvocationEnvelope hop-compare → GrantRecord + descriptor
    │  JobHandle / Task Graph / product_session fold
    ▼
Owners of the op (per AD-3 descriptor doors)
    COMP-QMB  library / qmb CLI / CT-47 door
    COMP-QML  library (research)
    COMP-QMN  library / localhost HTTP evidence / unix-socket powers
    COMP-QMA  wire + library (no operator CLI)
```

**Refused inventions:** a UI BFF, a second daemon runtime, COMP-EXP HTTP experiment service (`HTTP_EXPERIMENT_SERVICE_MINTED = False` in `process.py`), a REST invoke API, a session database, a fourth observability product, merging QMB JSONL into daemon sqlite, treating json-render / MCP Apps as authority.

Parent AD-17 / UI-HOST: the host is a **client** of qma-wire, QMB API/CLI, and QMN three doors. Three presentation lanes (native pane, json-render, MCP App HTML) **none own identity or permission**. json-render `action` names an existing `op_id`. MCP `tools/call` is intercepted against the session GrantRecord (2026-09-23 CONTRACTS §7).

QMA and QMN ship **no operator CLI**. Unsupported door → typed `unsupported_door` (`qma.core.operations.doors`).

---

## 3. Wire envelope, families, RPC methods

### 3.1 Envelope frame (CT-40 / AD-5)

`WireEnvelope` fields: `v`, `type`, `id`, `producer_id`, `correlation_id`, `scope_path`, optional `seq`, `payload`. Canonical JSON per `fp1`. Null is prohibited; omit absent keys.

- `id` — unique per message, minted by producer. Second half of command idempotency.
- `producer_id` — stable client identity assigned at `initialize`, **unchanged across reconnects**. First half of idempotency.
- `seq` — per-scope projection index of the **last** `scope_path` segment. **Never** `journal_seq` (opaque; refused if placed on the wire).
- `scope_path` — ordered `{kind,id}`: desk → quant → mission → task → session → agent → subagent. Session sits between Task and Agent because a Task outlives the QMA run session. **`product_session` is not a scope_path segment** (`product_session.py` refuses adding it).
- Mailbox `Envelope` (CT-48) is a different record. Never write “envelope” bare.

### 3.2 Three families (`families.py`)

| Family | Transport kind | Mutates | Ack | Authority |
|---|---|---|---|---|
| command | `jsonrpc_websocket` | yes | immediate; effects async | yes (ack is not completion) |
| query | `http_get` | no | n/a | **snapshots are authoritative** |
| event | `durable_stream` | no | n/a | **progress is not authoritative** |

Client rebuilds truth from a query, never from an accumulated event tape (DEC-0304). `progress_is_authoritative()` returns `False`.

### 3.3 Seed vocabulary (`vocabulary.py`) — closed-and-addable, owned by `qma-wire`

**9 commands:** `start_mission`, `send_message`, `steer_agent`, `stop_run`, `approve_hook_action`, `install_enable_plugin`, `update_configuration`, `launch_task`, `retry_task`.

**11 queries (7 seed + addable):** `get_quant`, `list_missions`, `get_graph_state`, `inspect_ledger`, `inspect_trace`, `list_installed_plugins`, `get_provider_health`, plus `list_mission_hooks`, `plugin_install_preflight`, `facade_search`, `facade_get`.

**10 events (`noun.verb`):** `agent.started`, `message.delta`, `tool.started`, `task.completed`, `hook.blocked`, `ledger.updated`, `mission.updated`, `worker.detached`, `provider.cooldown`, `artifact.created`. Hook `before_*` / `after_*` names are **not** wire families.

There is **no** seed type `invoke_op`. Public pack/workflow invoke is AD-24 `InvocationEnvelope` on an existing public-call transport (`in-process | cli | wire | nested`), hop-compared by the host (`dispatch_public_call`). Additive CT-40; **not a new CT**.

`host_request` verbs ride as command/query types (RLM kernel only; not a second channel). Seed verbs map 1:1 onto daemon primitives (`subagent_spawn`, `env_create`, `message_send`, `tool`, `ledger_append`, `artifact_register`, `experiment_register`, `memory_write`, `graph_transition`). Unmapped → `UnknownHostRequest`. UI chrome must not speak `host_request`.

### 3.4 Handshake and “session headers”

Not HTTP `Authorization` headers on a REST bus. The connection gate is:

1. **Before protocol bytes:** `authenticate_before_protocol(credential_ref, principal_class)` (`auth.py`). Wire carries a Credential-Broker **reference** (`cred://…`). Secret keys (`api_key`, `token`, `password`, `bearer`, …) are forbidden on any wire surface.
2. **Exactly one principal class** per connection: `operator` | `machine`. Immutable for the connection life. Human-gate commands from `machine` → `OperatorPrincipalRequired`.
3. **`initialize` JSON-RPC 2.0** (`initialize.py`, schema `initialize.v1.schema.json`): client sends `protocolVersion` (semver), optional `capabilities`, optional `producer_id` hint, `credential_ref`. Server returns negotiated `protocolVersion`, capabilities, assigned `producer_id`. `WIRE_PROTOCOL_VERSION = "1.0.0"`. Family messages before initialize → policy refusal.
4. **Then** command/query/event families. Queries are specified as HTTP GET; commands/events as JSON-RPC over WebSocket.

`product_session` is **not** a connection header. It is a daemon journal projection (`psess:`). `InvocationEnvelope.caller_session_ref` / `callee_session_ref` when present are `psess:` — `sess:` is refused.

### 3.5 Listener posture (`listener.py` + `process.py`)

- Default bind `127.0.0.1`. Loopback may use `ws://` + `http://`.
- Non-loopback requires `wss://` **and** HTTPS queries **and** explicit recorded operator config. Else hard startup refusal.
- Unauthenticated bind is a hard startup refusal.
- Remote workers **dial out**; daemon never dials in. Single inbound listener.
- Default port `8765`. `DaemonProcess.start_http_experiment_service()` is refused.

**Honesty @ 34c148b:** `DaemonProcess.bind()` uses `asyncio.start_server`. `_handle_client` reads chunks until EOF and **does not parse JSON-RPC, WebSocket upgrade, or HTTP GET**. Transport kinds are contract + tests, not a live protocol stack. Do not tell the UI sitting that “the daemon already serves WS/HTTP.”

---

## 4. Attach, reconnect, `producer_id`

### 4.1 `wire.attach` / `wire.detach` (client state)

`attach.py`:

- `wire.attach(scope, since_seq)` subscribes the **client** to that scope’s durable event stream from `since_seq`.
- `since_seq=0` is **read-only replay**.
- Cursor is valid only for the issuing scope. Cross-scope cursor → `CursorScopeMismatch` (never silent rebase).
- `wire.detach` drops the client subscription.
- `ClientDetachOutcome` literals: `job_handle_state_unchanged=True`, `invokes_job_handle_cancel=False`, `stops_quant_work=False`. Tab-close same.
- Attachment never changes Quant identity. Closing a client never stops an overnight agent (DEC-0304; FR-W36; UX-DR5).

`JobHandle.attach` / `JobHandle.reattach` are a **different axis** (CT-46). Do not confuse with `wire.attach`.

QMA Session attachment (`attached`/`detached`) is client state, never persisted — that is what makes closing a client harmless (DEC-0313). Distinct from `product_session`.

### 4.2 Command idempotency vs invocation idempotency

| Layer | Key | Window | Replay |
|---|---|---|---|
| Wire command (CT-40) | `(producer_id, id)` | `registry:wire.dedup_window` | duplicate dropped / prior ack |
| Public invoke (AD-24) | caller-issued `idempotency_key`; uniqueness `(principal, op_id, op_version, instance_id, config_revision, grant_id, target, canonical_input_hash)` | ≥ journal lifetime of the invocation | same key + same hash → prior result; hash collision → typed refusal |

Host never mints `idempotency_key` (`HOST_MINTS_IDEMPOTENCY_KEY = False`).

### 4.3 `correlation_id`

Three mint origins only: originating operator command, scheduled trigger, daemon-internal lifecycle act. Copied **verbatim** onto every downstream command, event, JobHandle, ledger append, memory candidate, telemetry span. Recipients never regenerate or truncate. Missing on a non-evidence record → refuse. Evidence append missing → daemon-minted lifecycle id annotated `correlation_missing` (L39). Join key for UI diagnosis; **never** `fp1` identity; **never** causal `enacts` (those are typed lineage edges).

### 4.4 Remote worker outbox (laptop-off / partition)

`outbox.py`: ordered, fsynced, **not a journal**. Replay in order on reconnect; daemon dedups `(producer_id, id)`. Exhaustion blocks new dispatch rather than dropping evidence; telemetry discarded first. Lost env with non-empty outbox → Task ledger `unknown_tail` at last acked `id`. Laptop-off continuation is `qma-daemon` + reachable **remote** ExecutionEnvironment + this outbox (`continuation_host.py`). If daemon and every env live only on the sleeping laptop → `LaptopOffContinuationRefused`. Always-on host remains operator config (GAP-0062). UI must not promise continuation it does not own.

### 4.5 `product_session` reconnect (AD-8 / Story 55.3)

`ProductSessionService.reconnect(product_session_id, resume_cursor, cursor_generation)`:

- Is a **query**. Extra keys `command_id`, `payload`, `payload_hash`, `expected_revision`, `unacked`, `intent` → `refuse_reconnect_replays_intent`.
- Compacted history past the cursor, or stale `cursor_generation` → `snapshot/resync` with bumped generation (never silent empty replay).
- Two tabs of one `app_instance_id` share one `psess:`. Closing a tab writes nothing. A new tab does not mint.
- Tab/window/view ids are refused as session ids (`chrome.py`, `view_presentation.py`).

Parent CONTRACTS §3 also specifies CAS mutate `{expected_revision, command_id, payload, payload_hash}` with results `ok | conflict | duplicate | in_progress`. At `34c148b` those keys exist only as **reconnect-intent refusal tokens** — no CAS mutate method on `ProductSessionService`. Treat CAS mutate as parent law not yet a product surface.

Durable fields: `product_session_id`, `profile` (`authoring | app-use`, immutable at create), `principal`, `context_revision`, `app_instance_id`, `granted_ops` (grant_ids), `selected_refs`, `account_scope` (omitted unless granted), `resume_cursor`, `cursor_generation`. Occupancy stays `none` until live-adjacent.

**Honesty:** `ProductSession.app_instance_id` is a required `str` at `34c148b`. Pack-and-grant named amendment (authoring may omit until invoke; envelope `instance_id` still required) is **sitting law, not wired** (DEC-0465). `SELECTED_REF_KINDS` lacks `instance_id`. `caller_kind` is absent on `InvocationEnvelope`.

---

## 5. JobHandle vocabulary (parent AD-17 / AD-26)

QMA AD-17 restated. Never `succeeded`. `awaiting_approval` is a Mission/Task gate, not a handle state.

| Field (code @ 34c148b) | Parent CONTRACTS §6 |
|---|---|
| `job_id` | `job_id` |
| `logical_run_id` | `logical_run_id` (invoke identity) |
| `attempt_id` | `attempt_id` (≥ 1) |
| `state` | closed: `queued \| running \| done \| failed \| cancelled \| aborted \| unknown` |
| `task_id`, `owner`, `wake_mailbox` | daemon mapping / wake |
| `artifacts[]` `{fp1, completeness}` | `complete \| partial \| missing \| expired` |
| `correlation_id` | join |
| `holds_environment_lease` | `unknown` holds the slot |
| `later_commands` | first durable terminal wins; later cmds recorded as no-ops |

CONTRACTS §6 also names `occupying`, `environment_ref`, `cancelable`, `result_ref`, `receipt`. Code payload uses `is_terminal`, `mapped_task_state`, `wake_armed`, `abort_reason`, `unknown_trigger`, `recorded_resolution`. UI should render parent states, not invent `succeeded`.

**Operations** (`JOB_HANDLE_OPERATIONS`): `submit`, `attach`, `wait`, `reattach`, `wake`, `cancel`, `stream`.

| Op | Meaning for UI |
|---|---|
| `submit` | queues; returns immediately; same `(task_id, job_id)` is idempotent |
| `attach` | live **view** of durable state; identity unchanged |
| `wait` | change **signal**; durable store is truth (`sleep_is_truth=False`) |
| `reattach` | restore after detach/restart; in-flight + lost supervisor/env/daemon restart → `unknown` |
| `wake` | Quant mailbox stored at submit |
| `cancel` | **only** coordinated cancel authority (`COORDINATED_CANCEL_AUTHORITY`). Plugin / Routine / worker / **UI widget** cannot take this path |
| `stream` | harness **telemetry** lines; `ledger=False`. Not evidence |

Terminal: `done`, `failed`, `cancelled`, `aborted`. Non-terminal: `queued`, `running`, `unknown`. `cancelled` = explicit cancel. `aborted` = known env/supervisor non-completion (OOM, container stop, image/mount failure). Timeout / lost supervisor / unreachable env / daemon restart → `unknown`, **never** `failed` or `aborted`. `unknown` holds `max_in_flight` until operator-principal `unknown.resolve`. No component retries or invents terminal state (L35).

Task mapping (daemon-applied): queued/running → Task `running`; done → done; failed → failed; aborted → failed (reason recorded); cancelled → cancelled; unknown → unknown. `aborted` never becomes `cancelled`.

QMB door: production `CliQmbDoorTransport`. `JobHandle.cancel` enters QMA `cancelled`; production door maps to QMB abort so QMB ledger writes `aborted`. Ungoverned `qmb.run()` death writes nothing.

UI-facing: a cancelled **display** is not proof computation stopped until the handle is terminal `cancelled` (or raced to `done`). Connection loss must not paint the job `failed` (XR-02 proposal matches parent law here).

---

## 6. Invoke, effect class, retry (no blind side-effect retry)

`InvocationEnvelope` required fields (additive CT-40; `invocation_envelope.py`): `logical_invocation_id`, `attempt_id`, `op_id`, `op_version`, `contribution {qualified_id, package_version}`, `instance_id`, `config_revision`, `grant_id`, `effect_class`, `idempotency_key`, `reconcile_policy`, `input_hash`, `call_depth`. Optional: `caller_session_ref`, `callee_session_ref`, `parent_logical_invocation_id`. Envelope is **signed/bound request context, not authority**. Crypto algorithm remains GAP-DESK-ENVELOPE-CRYPTO; mismatch refuse still required.

Pack-and-grant named amendment: `caller_kind: user | agent | workflow` — **absent at 34c148b** (DEC-0464/0465). Envelope `instance_id` stays required on invoke.

`effect_class` retry matrix (`effects.py`; parent AD-24; SCN-0026):

| effect_class | Retry kind | UI recovery |
|---|---|---|
| `none` / `read` | may retry | Host retry until success, `retryability=NO`, or registry ceiling (GAP-0108: sitting mints **no number**). Pack may set attempts to 0; must not exceed host ceiling. Loop **absent** at 34c148b |
| `append-evidence` | dedupe on key | Replay returns prior append |
| `mutate-config` | CAS on `config_revision` | Conflict is **not** a retry; stale → `StaleObservation` |
| `place-run` | `logical_invocation_id` is run identity | Query JobHandle; do not mint a second run |
| `external-egress` | receipt or `unknown` | **MUST NOT** blind-retry. `BlindRetryRefused` on second send without receipt |

`reconcile_policy`: `query-then-decide | unknown-manual | never-retry`. `blind-retry` is not a member.

Descriptor lifecycle verbs (AD-3): `start | query-state | cancel | await`. Nested workflow: callee is Graph Template `(qualified_id, version)`; result is a JobHandle; **no merge of live Task Graphs**.

Ack vs completion: command ack is transport. Outcome unknown ≠ failed. First durable JobHandle terminal wins a cancel/complete race.

---

## 7. Logs vs evidence (parent AD-16) and health / listing axes

### 7.1 Parent AD-16 (2026-09-18)

Persistence owners stay split. **Logs are not evidence.** Do not invent a second evidence database. v1 daemon additions are a closed list: `product_session` projection; persist existing `task_graph_state` + AD-26 outbox; mini-app instance rows on **existing** plugin-install projection; GrantRecord rows beside `product_session` on the **same** sqlite. No sixth store class.

QMF logging-spec (DEC-0112): operator logs render UTC ISO-8601 `Z`; journals store int64 UTC ns + `WriterId` + sequence. `correlation_id` is a linking annotation excluded from `fp1`.

QMA telemetry store: harness-authored, announcement-exempt, no `journal_seq`, ordered by `recorded_at` then `correlation_id`. Agents must not write it. OTel is export-port only.

Pack-and-grant CONTRACTS §6 / SCN-0027: daemon JSON-lines stdlib logging. Required: `ts`, `level`, `event`, `correlation_id`. When known: `instance_id`, `op_id`, `logical_invocation_id`, `graph_run_id`. Never secrets. Never a journal. **Absent at 34c148b.** Mini-app failures must not land on `qmn/FAILURES.md`.

UI ops screens consume these contracts (UX-11). `inspect_trace` is the seed query for harness telemetry. `JobHandle.stream` is the same class of display, not a ledger.

### 7.2 `health()` and listing axes

| Surface | Axes | Owner | At 34c148b |
|---|---|---|---|
| ContributionListing | independent booleans `published \| configured \| granted \| reachable \| healthy`; `authorizes_invoke` const false; occupancy `none` | COMP-QMA-DAEMON overlay over `published_contributions()`; DTO COMP-QMA-WIRE | types/fixtures; listing is not a door run |
| Component `health()` | no-arg typed report (DEC-0112) | every resource owner | QMF streaming/venue/QMB log sink implement; QMA listing `healthy` is an overlay set, not a census of every COMP |
| Kit diagnosis (2026-09-23 §5) | `failure_class`: `grant \| workflow \| view \| dependency \| host`; plus `job_handle`, `correlation_id`, `healthy` | host query | **absent** (SCN-0027) |
| Seed query `get_provider_health` | provider/model health | COMP-QMA-DAEMON | **name only** in vocabulary/schema; no handler module |
| QMN `/health` | seven independent states: safety, execution_readiness, connection, reconciliation, data_freshness, lifecycle, sync; never one colour | COMP-QMN evidence HTTP GET | implemented as door library + HTTP adapter |

`view` failure_class means the **wire DTO** failed to mount, was stale, or unhealthy — it is not an invoke (SCN-0027). Stale `ViewPresentation.snapshot_cursor` refuses invoke (AD-17).

---

## 8. HTTP vs JSON-RPC vs WebSocket — keep the seams

| Door | Protocol | Who | May act? |
|---|---|---|---|
| qma-wire commands + events | JSON-RPC 2.0 over WebSocket (`ws` loopback / `wss` otherwise) | UI, workers, plugins | yes (commands), after initialize + principal gate |
| qma-wire queries | HTTP GET (`http` loopback / `https` otherwise) | same clients | **read only** |
| QMN evidence | localhost HTTP GET `/status`, `/health`, `/projections`, `/config/explain`, `/metrics`, `/failures/{id}` | UI / observability | **publish-never-act**; POST refused |
| QMN powers | AF_UNIX + `SO_PEERCRED` | operator vs ops | acts; not a browser fetch |
| QMB | library + `qmb` CLI (+ CT-47 from daemon) | operators / daemon door | QMB-owned ops |
| json-render / MCP App | host-intercepted `action` / `tools/call` | presentation | only if GrantRecord allows the named `op_id` |

Do not route invoke through QMN evidence HTTP. Do not add a QMA `/invoke` REST. Do not treat WebSocket progress as a snapshot.

---

## 9. UI intent → path table

XR-01..08 remain proposals. Rows below map **intents** onto existing owners. “Component state” is UI chrome state, never backend truth.

| UI intent | Component (chrome) state | Wire method / event | Backend owner | Progress / result | Recovery after loss | Retry constraints |
|---|---|---|---|---|---|---|
| **Open app** | View `mounted`; tab is not a session; occupancy none | Query `facade_get` / listing overlay; `product_session` mint or `session_for_instance`; GrantRecord ids in `granted_ops`; optional `view:*` DTO | COMP-QMA-DAEMON (listing + `psess:` fold); COMP-QMA-WIRE DTOs; op owner is the pack COMP | Listing axes independent; hit ≠ grant; `healthy` false is not invoke | Reconnect query restores same `psess:` for the instance; do not mint a second session per tab | Read-only; retry listing/query freely |
| **Invoke op** | Command: awaiting-ack → acknowledged \| rejected \| **outcome unknown** (XR-02 proposal; matches AD-24) | Public call + `InvocationEnvelope` on wire transport; descriptor `start`; command ack is not completion; events `tool.started` / `task.completed` / `artifact.created` are progress | Host hop-compare (daemon) then AD-3 owner (QMB/QML/QMA/QMN). Envelope not authority | `output_shape` `value \| artifact_ref \| job_handle \| event \| stream`. Place-run / long op → JobHandle. Snapshots via query | Query JobHandle / `query-state` **before** any resubmit. `logical_invocation_id` is run identity for `place-run` | Caller `idempotency_key`. `none`/`read` may host-retry. `mutate-config` CAS. `append-evidence` dedupe. `external-egress` receipt or `unknown` — **no blind retry**. Stale snapshot/cursor refuses |
| **Cancel** | UI: cancellation **requested** until handle terminal (XR-04 proposal = parent law) | Coordinated path is `JobHandle.cancel` only. Seed `stop_run` is the **agent/mission** stop (`agent_stop` hook) — do not use it as widget Stop for a placed job. Tab-close / `wire.detach` **must not** cancel | COMP-QMA-DAEMON JobHandleService; QMB abort only via production door | First durable terminal wins. Race with `done` shows completed result. `unknown` cannot be cancelled — operator `unknown.resolve` | If ack of cancel is lost: show requested + unknown; reattach; do not claim cancelled | Do not retry cancel as a new invoke. Later commands against a terminal handle are recorded no-ops |
| **Expand widget** | Detail tab focused; source widget identity + filter retained (XR-05 proposal) | `ViewPresentation` DTO `mount=mounted`; **no** command. Mount/dispose must not start/kill durable work (`refuse_view_durable_work`) | COMP-QMA-WIRE DTO only. GAP-0081 chrome unfilled. Not a ContributionHit, not a `psess:` | Detail renders last snapshot (`snapshot_cursor`). Stale → refuse invoke from that view | Closing detail is local chrome. Job underneath unchanged | None. Re-expand focuses existing detail; not a side effect |
| **Send copilot message** | Conversation scoped to `psess:` (authoring vs app-use). Drafts are client until ack. XR-07 proposal: do not merge histories | Seed command `send_message` (agent mailbox / `message.delta` events) **or** granted op invoke via envelope (`caller_kind=user` when that field exists). MCP tool call intercepted | COMP-QMA-DAEMON mailbox + hooks; granted ops per GrantRecord ∩ listing ∩ health. Copilot cannot self-grant. App-use cannot apply (`change_request` only) | Stream `message.delta` is **not** authoritative. Result links are artifact/job refs. Questions are mailbox `approval_request` / `question` | Reattach stream from `since_seq`; query mailbox / job. Unsent draft stays local. Do not redirect an in-flight answer when switching apps | Same effect-class matrix as invoke. Do not double-submit the same `idempotency_key` with a different hash |
| **First-run provider save** | Splash/status: partial readiness; one missing provider must not block all work (UX-01) | Human-gate command `update_configuration` (operator principal). Secrets **never** on wire — Credential Broker exact-ref into Windows Credential Manager (`broker.py`). Then query `get_provider_health` + listing `healthy` | COMP-QMA-DAEMON Credential Broker + variable registry; COMP-QMN `/health` for node; providers behind allowlisted `credential_ref` | Saved = ref stored; resolved value never leaves adapter egress frame. Unavailable ref → `UNAVAILABLE_DEPENDENCY` with ref id only | Reconnect does not resubmit the secret. Query health. Missing dep is enable-time hard error (Hermes warning-and-continue refused) | Config mutate is CAS. Do not retry a save that may have applied. Collision / different payload hash refuses |
| **Reconnect after sleep** | Connection: connected → reconnecting → unavailable. Job state **unchanged** by transport (XR-02) | 1) re-auth `credential_ref` 2) `initialize` **same** `producer_id` 3) query snapshots 4) `product_session.reconnect(resume_cursor, cursor_generation)` 5) `wire.attach(scope, since_seq)` 6) `JobHandle.reattach` for in-flight ids | COMP-QMA-WIRE + COMP-QMA-DAEMON. Laptop-off work only if remote env + daemon not on the sleeping laptop | Snapshot/resync if cursor compacted. In-flight + unreachable → JobHandle `unknown` (not failed). Events after snapshot must not overwrite a terminal | Reconcile authoritative status **before** replaying intent. Empty replay forbidden | **Never** re-issue unacked commands. Wire dedup may hide a duplicate `(producer_id,id)` inside the window — that is not permission to resubmit a new `id` for a side-effecting op. `external-egress` stays unknown until receipt/operator |

Experience §6 pins the same distinctions: not-acked ≠ failed; cancelled display ≠ stopped; after reconnect reconcile before replay; local path ≠ VPS access; remote failure must not silently retarget locally; closing a view ≠ stop if a durable service owns the job.

---

## 10. Connect sequence (what the UI actually does)

```
authenticate(credential_ref, principal=operator)     # before protocol bytes
initialize {protocolVersion, capabilities, producer_id?}
    ← {protocolVersion, capabilities, producer_id}   # stable across reconnects
HTTP GET queries: facade_get / list_installed_plugins / get_graph_state / …
optional: product_session mint or lookup by app_instance_id
wire.attach(scope, since_seq)                        # client subscription
JSON-RPC command with WireEnvelope + InvocationEnvelope on public invoke
    ← immediate ack
JobHandle | value | artifact_ref
follow events from since_seq; rebuild from queries
on drop: do not cancel; on wake: initialize(same producer_id) → query → reconnect → attach → reattach
```

---

## 11. Dependency classification

Legend: **reuse** = bind as-is; **adapt** = same owner, named amendment or UI-facing mapping; **add** = sitting may specify UI chrome/behavior but not a new COMP/CT/store; **unresolved** = inspect cannot close it.

| Dependency | Class | Evidence |
|---|---|---|
| CT-40 envelope, families, initialize, `producer_id`, attach/detach, principal classes | **reuse** | `qma-wire` modules + CT-40; seed 26 nouns + addable queries |
| JSON-RPC WS + HTTP GET split | **reuse** (contract) / **unresolved** (live stack) | `families.py` vs `DaemonProcess._handle_client` byte drain |
| Loopback TLS/auth posture | **reuse** | `listener.py` startup refusals |
| `InvocationEnvelope` + GrantRecord hop-compare | **reuse** types; **adapt** `caller_kind` | types @ 34c148b; `caller_kind` absent (DEC-0465); crypto GAP |
| Effect-class retry matrix | **reuse** types; **adapt** host retry loop | `effects.py` present; SCN-0026 loop absent; GAP-0108 no ceiling number |
| JobHandle AD-17/AD-26 | **reuse** | `qma.core.ports.jobs` + `JobHandleService`; cancel authority module |
| `wire.attach` ≠ `JobHandle.attach` | **reuse** | two modules; UI-HOST “must not cancel jobs; must not replay intent” |
| `product_session` `psess:` fold | **reuse** types; **adapt** authoring-optional instance + `selected_refs.instance_id` | mint requires instance string today; reconnect query exists; CAS mutate **not** implemented |
| ContributionListing five axes | **reuse** | `contribution_listing.py` / `listing.py`; hit ≠ grant |
| `view:*` presentation DTO | **reuse** DTO; **add** chrome (GAP-0081 later) | mount/dispose cannot start/kill work; `qma-ui-contract` is a stub |
| Federated `facade_search` / `facade_get` | **reuse** | concatenate CT-44 + QMB library.search + contributions; no fourth store |
| Credential Broker / first-run keys | **reuse** | `broker.py` Windows Credential Manager exact-ref; secrets forbidden on wire |
| QMN evidence HTTP + `/health` | **reuse** (node ops, not invoke) | `qmn/doors/http/evidence.py`; seven independent states |
| QMB CLI / CT-47 door | **reuse** | only operator CLI; occupancy query vs run |
| Daemon JSON-lines + `failure_class` diagnosis | **add** (kit law FEAT observability; no new COMP) | SCN-0027 / 2026-09-23 CONTRACTS §§5–6; **absent** @ 34c148b |
| Host retry loop for `none`/`read` | **add** (host/SDK behavior) | SCN-0026; fixtures exist; loop absent |
| Nested Mission invoke as first-class | **adapt** (parent verbs exist; kit names nested Mission) | 2026-09-23 CONTRACTS §4; not first-class @ 34c148b |
| Live WS/HTTP protocol implementation | **unresolved** | TCP bind only; schemas exist; no e2e |
| `get_provider_health` handler | **unresolved** | enum + JSON Schema only |
| AD-8 CAS `command_id` mutate | **unresolved** as product surface | specified in parent CONTRACTS §3; code refuses those keys on reconnect only |
| Laptop-off always-on host | **unresolved** (GAP-0062) | gate exists; machine not named |
| Envelope crypto algorithm | **unresolved** (GAP-DESK-ENVELOPE-CRYPTO) | mismatch refuse still required |
| GAP-0081 / GAP-0100 UI chrome | **out of scope** for kit; UI sitting may specify presentation later | stub + `VIEW_FILLS_GAP_0081_CHROME = False` |
| New middleware / new DB / sixth COMP / new CT | **refused** | parent AD-16; process.py flags; DEC-0465 |

---

## 12. Honesty pins for the rest of this sitting

1. **Do not invent a middleware service.** The UI talks CT-40 to `qma-daemon`, QMB doors, and QMN three doors.
2. **Do not invent a database.** `product_session` and GrantRecords are journal-derived projections on existing daemon sqlite.
3. **Types ≠ e2e.** Envelope, GrantRecord, product_session, JobHandle, attach, listing: CONNECT at `34c148b`. Live JSON-RPC/HTTP, `caller_kind`, diagnosis `failure_class`, daemon JSON-lines, host retry loop, optional authoring `app_instance_id`: ABSENT as product surface.
4. **Snapshots > events.** After sleep, query then attach; never reconstruct job success from `message.delta`.
5. **Tab ≠ session ≠ job.** Three lifetimes (XR-01 proposal matches AD-8/AD-17/AD-26 here).
6. **Cancel is a request** until `JobHandle.state=cancelled` (or raced `done`).
7. **No blind side-effect retry.** Especially `external-egress` and any money-adjacent QMN power.
8. **Logs are display.** Journals and JobHandle/ledger are evidence. Copilot diagnosis joins on `correlation_id`.
9. **XR-01..08 are proposals** until this architecture sitting accepts them. Where they already restate parent AD-8/16/17/24/26, prefer the parent spelling.
10. **Parent AD-16** in this sitting’s numbering is persistence-split + “logs are not evidence”, not QMA’s Tool Registry AD-16.

---

## 13. What a vertical slice can bind without new owners

A UI slice that is honest at `34c148b`:

- In-process (or future WS) `initialize` + `producer_id`.
- Query listing / `facade_get` (fixture concatenate).
- Mint or restore `psess:` (fixture journal fold).
- Dispatch one `read` or `none` op with `InvocationEnvelope` (fixture hop-compare).
- Show JobHandle states including `unknown`.
- Tab close does not cancel.
- Reconnect path: query + `reconnect(resume_cursor, cursor_generation)` + `reattach`; refuse intent replay.

Anything that needs a real WebSocket/HTTP GET server, JSON-lines logger, `failure_class` query, or host retry loop is **kit/factory work already named**, not a new UI backend.
