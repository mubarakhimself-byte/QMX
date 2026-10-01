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

QMB domain execution goes through `BacktestingService.invoke` and `CliQmbDoorTransport`, never QMA importing qmb. Preserve ATC optimization in QMB and governed evidence/ticket checks. Stage 0 graph is never executable ATC. Real-model unavailable is a visible bounded refusal; deterministic model doubles are explicit acceptance fixtures and cannot establish provider functionality. OpenCodexDeployment without a handler currently returns synthetic text and must not count as provider success.

## Required acceptance views

Browser reload and daemon restart restore drafts/publications/results without generating a new run. Show empty/stale/denied/failed/success distinctly. Acknowledgement is acceptance, not execution completion. Reconnect reattaches accepted jobs and artifacts. Cancel is command_id-idempotent, terminal cancellation is a recorded no-op. Missing deployment does not disable unrelated local apps. No-copilot apps work without a model.

Windows desktop mini-app acceptance is separate from QMN: current ratified node placement remains Ubuntu systemd/unix powers. Single-machine QMN placement GAP-0058 is open. Do not present unverified Windows node controls as ready.

Useful test references: tests/test_product_session_grants.py, test_product_session_chrome.py, test_nested_mission.py, test_nested_mission_widget.py, test_editor_draft.py, test_epic72_pack_ui.py, test_mailbox_lost_ack.py, test_pairing_listener.py, test_qmb_backtesting_door.py under qmx-agents/packages/qma-daemon.

## Backend additive wire contract (2026-10-01)

The daemon now exposes the ratified operator ProductSession lifecycle over the authenticated CT-40 connection. These are addable `qma-wire` commands; they do not add a grant authority or let a caller name a principal, contribution revision, config revision, effect class, or host executor.

`open_product_session` accepts `{instance_id, qualified_id, package_version}`. The daemon requires an authenticated `operator`, resolves that exact enabled contribution on the exact enabled instance, and resolves that instance's owner/environment/config revision from the operator-owned `qmb_bindings` row. It creates an `app-use` `ProductSession` whose principal is derived from the connection, whose instance and selected ref are that instance, and returns the durable session payload including `product_session_id` and `context_revision`. Repeating the same open after reload or a lost reply returns the same session and grant IDs; a different contribution/config binding on an already-open instance is refused.

`grant_product_session` accepts `{product_session_ref, expected_revision, op_id, op_version, parameter_ceiling: {allow_keys: [...]}, expires_at}`. The daemon requires an authenticated operator and operator-owned session, compares `expected_revision` with the current session context revision, resolves the versioned published operation descriptor, bounds every ceiling key by its declared required/optional input keys, and derives contribution, instance, config revision, principal, audience, and effect class from that durable session and descriptor before calling the existing ProductSessionService host-grant path. Only operation adapters declared for that enabled contribution point are grantable. A successful new grant appends the grant id and advances `context_revision`; a stale retry refuses. The response includes the immutable `GrantRecord` and updated `context_revision` so clients can safely issue the next CAS.

`get_product_session` is an operator-only query accepting `{product_session_ref}`. It returns the durable session snapshot plus host-resolved `grant_records`. Use it after a lost grant reply to match by exact `op_id`, `op_version`, parameter ceiling, and grant ID; the client must not infer that the newest grant is the intended one when multiple grants exist. Unknown query fields are refused.

`start_mission` and `launch_task` continue to take `{product_session_ref, envelope, payload}`. The envelope's caller session must equal the supplied session reference; its contribution, instance, config revision, operation version, effect class, input hash, and grant id are checked against the live enabled roster, descriptor, and durable GrantRecord before the trusted host adapter runs. For QMB replay, `run_fp1` resolves an already registered CT-47 `ExperimentSpec`; CT-47 `data_ref` remains the split/source identity and is not treated as a request-file reference. QMB request execution is unavailable until the separate durable request envelope and its source pins are resolved through the QMB adapter. Owner/environment are resolved only from the matching operator binding. A compiled Task Graph or accepted JobHandle remains distinct from actual task completion evidence.
