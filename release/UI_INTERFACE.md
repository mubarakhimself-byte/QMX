# UI / daemon integration map

Source exploration began at backend a0e8769772e469bf54bd312cc1e27e7995e16c3b + UI f6ffaddf3f78c6c14d32daa136fadf15e7748c14. The current additive CT-40 handlers and payloads are documented below.

## Existing browser transport

`qma.wire.listener`: localhost daemon default port 8765; POST `/pair/start`, `/pair/confirm`, `/pair/renew`; snapshots under `/q/`; POST `/artifacts/stage`. WebSocket offers `qmx.ct40.v1` and `qmx.pair.<pairing_proof>`. Origin is checked; pairing proof is bearer authentication, pairing_record_id is journal identity. Origin cannot create a proof. Browser does not spawn Python or receive host_control. Launcher/QMB privileged local host-control door bootstraps the daemon and pairing.

JSON-RPC initialize negotiates capability families and unique `producer_id`. Preserve IDs across retry of accepted commands. Typed refusal is a real failure, never a recorded successful call. Track producer/id, product_session_ref, instance/revision/config/grant, operation, correlation and job/run/attempt/artifact identity.

`DaemonProcess._dispatch_paired_ct40` handlers include initialize, save_editor_draft, publish_editor_draft, get_editor_draft_head, get_pack_ui_request, transfer_artifact, transfer_complete, cancel_job, send_message, open_product_session, grant_product_session, start_mission, and launch_task. Drafts require authenticated operator and negotiated capabilities. Immutable publication is distinct from enabled instance and grant. Draft CAS conflict must be visible and recoverable. `send_message` produces durable mailbox acknowledgement, not model completion. Closing a tab does not cancel work.

## Source gaps requiring backend composition

The public invocation handlers use ProductSessionService dispatch and the trusted daemon adapter; no generic `invoke_operation` method is mounted.

The authenticated lifecycle uses ProductSessionService open/reconnect/grant/dispatch_public_call and derives grants from live session and roster state. Pack chrome continues to use mount_pack_ui_view/press_pack_ui_action/unmount_pack_ui_view APIs.

## Minimal trusted runtime reuse

Reuse `DeskPluginRoster.compiler` and `.templates`, `DaemonProcess.task_graphs`, `.product_sessions`, `.variables`, authoritative journal and sole SQLite writer. Bind TaskGraphDispatcher(durable=task_graphs, shared environments/router/ledgers) and NestedMissionHost(compiler=roster.compiler, graphs=task_graphs, shared jobs/variables). Terminal Task transitions require actual JobHandle evidence. ProductSessionService.dispatch_public_call(execute=trusted callback) evaluates grants at dispatch. Pack chrome delegates there. Key adapters by instance and contribution revision plus op_id; two instances sharing op_id must remain distinct.

QMB domain execution goes through `BacktestingService.invoke` and `CliQmbDoorTransport`, never QMA importing qmb. Preserve ATC optimization in QMB and governed evidence/ticket checks. Stage 0 graph is never executable ATC. Real-model unavailable is a visible bounded refusal; deterministic model doubles are explicit acceptance fixtures and cannot establish provider functionality. OpenCodexDeployment without a configured transport or explicit test handler returns a typed unavailable refusal; it cannot count as provider success.

## Required acceptance views

Browser reload and daemon restart restore drafts/publications/results without generating a new run. Show empty/stale/denied/failed/success distinctly. Acknowledgement is acceptance, not execution completion. Reconnect reattaches accepted jobs and artifacts. Cancel is command_id-idempotent, terminal cancellation is a recorded no-op. Missing deployment does not disable unrelated local apps. No-copilot apps work without a model.

Windows desktop mini-app acceptance is separate from QMN: current ratified node placement remains Ubuntu systemd/unix powers. Single-machine QMN placement GAP-0058 is open. Do not present unverified Windows node controls as ready.

Useful test references: tests/test_product_session_grants.py, test_product_session_chrome.py, test_nested_mission.py, test_nested_mission_widget.py, test_editor_draft.py, test_epic72_pack_ui.py, test_mailbox_lost_ack.py, test_pairing_listener.py, test_qmb_backtesting_door.py under qmx-agents/packages/qma-daemon.

## Backend additive wire contract (2026-10-01)

The daemon now exposes the ratified operator ProductSession lifecycle over the authenticated CT-40 connection. These are addable `qma-wire` commands; they do not add a grant authority or let a caller name a principal, contribution revision, config revision, effect class, or host executor.

`open_product_session` accepts `{instance_id, qualified_id, package_version}`. The daemon requires an authenticated `operator`, resolves that exact enabled contribution on the exact enabled instance, and resolves that instance's owner/environment/config revision from the operator-owned `qmb_bindings` row. It creates an `app-use` `ProductSession` whose principal is derived from the connection, whose instance and selected ref are that instance, and returns the durable session payload including `product_session_id` and `context_revision`. Repeating the same open after reload or a lost reply returns the same session and grant IDs; a different contribution/config binding on an already-open instance is refused.

`grant_product_session` accepts `{product_session_ref, expected_revision, op_id, op_version, parameter_ceiling: {allow_keys: [...]}, expires_at}`. The daemon requires an authenticated operator and operator-owned session, compares `expected_revision` with the current session context revision, resolves the versioned published operation descriptor, bounds every ceiling key by its declared required/optional input keys, and derives contribution, instance, config revision, principal, audience, and effect class from that durable session and descriptor before calling the existing ProductSessionService host-grant path. Only operation adapters declared for that enabled contribution point are grantable. A successful new grant appends the grant id and advances `context_revision`; a stale retry refuses. The response includes the immutable `GrantRecord` and updated `context_revision` so clients can safely issue the next CAS.

`get_product_session` is an operator-only query accepting `{product_session_ref}`. It returns the durable session snapshot plus host-resolved `grant_records`. Use it after a lost grant reply to match by exact `op_id`, `op_version`, parameter ceiling, and grant ID; the client must not infer that the newest grant is the intended one when multiple grants exist. Unknown query fields are refused.

`get_job` is an operator-only query accepting `{handle_id, product_session_ref}`. It returns the durable JobHandle only when the supplied ProductSession is the exact origin recorded on that handle. Reopen the same product session after browser reload or daemon restart, then use the known handle id to recover state; a different session cannot inspect it. `UNKNOWN` means the daemon cannot prove the worker outcome and does not authorize cancellation or completion. Retry the same originating-session query to observe the same durable handle; do not mint a replacement job id.

`start_mission` currently acknowledges graph compilation with a durable `QUEUED` JobHandle. The daemon leaves it queued until a registered executor accepts the task and the ComputeRouter grants its environment lease; compilation alone does not mean a worker started or completed the task.

`start_mission` and `launch_task` continue to take `{product_session_ref, envelope, payload}`. The envelope's caller session must equal the supplied session reference; its contribution, instance, config revision, operation version, effect class, input hash, and grant id are checked against the live enabled roster, descriptor, and durable GrantRecord before the trusted host adapter runs. For QMB replay, `run_fp1` resolves an already registered CT-47 `ExperimentSpec`; CT-47 `data_ref` remains the split/source identity. `qmb.backtest.run` may separately accept `evidence_ref`, the fp1 of the persisted QMB replay-request envelope whose CT-12 split pin must equal that ExperimentSpec `data_ref`. The QMB CLI now selects a content-pinned operator composition by these trusted references, reloads registered Book/BMS/Bot records and recorded inputs, and refuses missing configuration. Actual delegated builder execution, daemon worker dispatch and connected installed acceptance remain under verification. Owner/environment are resolved only from the matching operator binding. A compiled Task Graph or accepted JobHandle remains distinct from actual task completion evidence.

## Alternative execution integration requirements

ATC remains in the full release scope. Its registered ingress and result consumer
are still being integrated; these requirements do not claim a completed wire
adapter. An alternative run carries explicit `composition_class: alternative`,
CT-07 PolicyPair and interpreter lineage. Book, BMS and Bot identities remain
absent. The UI must not manufacture those identities or a Book CT-32/R result.

Alternative completion requires the actual checked CT-13 execution chain and a
durable terminal artifact bound to its source, split, policy and final state.
Reopening results must read that artifact and journal evidence. Optimization
consumes an explicitly registered, unit-kinded policy objective and the same
generation barrier/reopen discipline; an unavailable objective is a typed
refusal. No default financial score, fraction, leverage basis or cost convention
may be inferred from an example policy name. Both composition classes require
actual worker acceptance under the current dispatcher Task lease, terminal
evidence, cancellation and restart/reconnect checks, and second-pack reuse of
the common host runtime. The accepted dispatched outbox must match the current
Task, mission, owner and TaskLedger attempt. Public invocation identity is
independent of Task identity. For `qmb.backtest.run`, QMB owns the compute leg;
QMA records no EnvironmentLease for that leg. Historical registration provenance
is retained but cannot substitute for current dispatch authority.

## Published UI baseline evidence boundary

Read-only dependency audit of the frozen published baseline found `@sveltejs/kit > cookie@0.6.0`, low-severity GHSA-pxg6-pf52-xh8x; fixed versions start at 0.7.0. The reviewed UI contribution needs a compatible dependency repair or documented, evidence-based disposition, followed by its actual lock audit and shell/connected checks. Exact trace is recorded in `release/evidence/dependency-security.md`. Codex made no UI or lock edits.

Published `ui-epic/066-shell@f6ffaddf3f78c6c14d32daa136fadf15e7748c14` has Playwright shell tests under `apps/qmx-ui/tests`; loading, reconnecting, error, selected references, opened visual/headless apps and missing capabilities are driven by labelled factory fixtures. Those tests can prove shell behavior, but do not prove a connected daemon job, provider completion, cancellation, restart or saved result. Backend acceptance must additionally exercise authenticated transport with the actual installed daemon and QMB child, preserve command/session/job identity through reload and restart, reopen durable economic artifacts, and demonstrate a second pack reusing the same host runtime. The separate Claude contribution remains pending; Codex does not modify `apps/qmx-ui` in this pass.

Read-only source confirmation of that boundary: `src/lib/host/wireClient.ts` sets `LIVE_CT40_SERVER_AT_INSPECT = false` and defaults `createWireClient` to `recordingTransport`; its acknowledgment records an in-memory call. `src/lib/bootstrap.ts` explicitly describes populated state as a `FACTORY-TEST` pairing fixture and says the host does not issue a pairing proof. This published baseline cannot supply real browser execution evidence merely by pointing its shell at an installed daemon. The reviewed UI contribution must replace that transport/pairing boundary and exercise the actual host operations before connected browser acceptance can pass. These observations are interface requirements, not authorization for Codex to edit the separately owned UI.


## Optimization and retry integration requirements

The reviewed core descriptor now names the existing documented `qmb.optimize.run` separately from `qmb.backtest.run`. Public input stays reference-only: `run_fp1`, with descriptor-declared optional `as_of` and `evidence_ref`; space, seed, objective, unit/currency, generation budget and composition belong to pinned owner artifacts. Descriptor membership does not yet prove executable availability: the CLI/worker/expected-artifact route is still being integrated. Render a typed unavailable/refusal truthfully until the actual supported route is verified.

Both Book and Alternative optimization require the checked complete Study history, durable result and producer occurrence under the originating job/attempt. The generic sensitivity report describes exact objective distributions, parameter slices and neighbourhood stability as data; it adds no financial default or search-quality verdict. Alternative results keep their declared objective units and absent Book/BMS/Bot/CT32 identities. A completed cached history may be read under a new invocation only with its own checked producer occurrence; old trial labels must remain unchanged. Reserved, started/UNKNOWN, partial, cancelled and complete are distinct recovery facts.

The host owns monotonic retry progression for supported READ/NONE operations. Preserve logical/idempotency identity and the complete validated input; a changed payload is new work and must not inherit accepted-work authority after grant revocation or restart. PLACE_RUN is not blindly resubmitted, and a missing accepted-binding/predecessor proof is a refusal. Current retry review remains open at the shared reopened-session dispatch boundary. No UI code changes or connected-browser acceptance are implied by these requirements.
