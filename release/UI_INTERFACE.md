# UI / daemon integration map

Read-only source exploration at backend a0e8769772e469bf54bd312cc1e27e7995e16c3b + UI f6ffaddf3f78c6c14d32daa136fadf15e7748c14. This maps existing APIs and missing composition; it is not a claim that added runtime handlers exist.

## Existing browser transport

`qma.wire.listener`: localhost daemon default port 8765; POST `/pair/start`, `/pair/confirm`, `/pair/renew`; snapshots under `/q/`; POST `/artifacts/stage`. WebSocket offers `qmx.ct40.v1` and `qmx.pair.<pairing_proof>`. Origin is checked; pairing proof is bearer authentication, pairing_record_id is journal identity. Origin cannot create a proof. Browser does not spawn Python or receive host_control. Launcher/QMB privileged local host-control door bootstraps the daemon and pairing.

JSON-RPC initialize negotiates capability families and unique `producer_id`. Preserve IDs across retry of accepted commands. Typed refusal is a real failure, never a recorded successful call. Track producer/id, product_session_ref, instance/revision/config/grant, operation, correlation and job/run/attempt/artifact identity.

Existing `DaemonProcess._dispatch_paired_ct40` handlers: initialize, save_editor_draft, publish_editor_draft, get_editor_draft_head, get_pack_ui_request, transfer_artifact, transfer_complete, cancel_job, send_message. Drafts require authenticated operator and negotiated capabilities. Immutable publication is distinct from enabled instance and grant. Draft CAS conflict must be visible and recoverable. `send_message` produces durable mailbox acknowledgement, not model completion. Closing a tab does not cancel work.

## Source gaps requiring backend composition

`start_mission` and `launch_task` currently pass only the artifact gate and then return method-not-found. A generic `invoke_operation` handler is not currently mounted. Do not invent assumed success or a browser-only execution authority.

Existing host/library APIs to expose through the same authenticated wire authority: ProductSessionService open/bind/reconnect/grant/dispatch_public_call; daemon mount_pack_ui_view/press_pack_ui_action/unmount_pack_ui_view; roster enable/disable published authoring contributions. Root implementation must provide the real trusted executor callback. Agree final additive method names and payloads with backend owner before frontend binding.

## Minimal trusted runtime reuse

Reuse `DeskPluginRoster.compiler` and `.templates`, `DaemonProcess.task_graphs`, `.product_sessions`, `.variables`, authoritative journal and sole SQLite writer. Bind TaskGraphDispatcher(durable=task_graphs, shared environments/router/ledgers) and NestedMissionHost(compiler=roster.compiler, graphs=task_graphs, shared jobs/variables). Terminal Task transitions require actual JobHandle evidence. ProductSessionService.dispatch_public_call(execute=trusted callback) evaluates grants at dispatch. Pack chrome delegates there. Key adapters by instance and contribution revision plus op_id; two instances sharing op_id must remain distinct.

QMB domain execution goes through `BacktestingService.invoke` and `CliQmbDoorTransport`, never QMA importing qmb. Preserve ATC optimization in QMB and governed evidence/ticket checks. Stage 0 graph is never executable ATC. Real-model unavailable is a visible bounded refusal; deterministic model doubles are explicit acceptance fixtures and cannot establish provider functionality. OpenCodexDeployment without a handler currently returns synthetic text and must not count as provider success.

## Required acceptance views

Browser reload and daemon restart restore drafts/publications/results without generating a new run. Show empty/stale/denied/failed/success distinctly. Acknowledgement is acceptance, not execution completion. Reconnect reattaches accepted jobs and artifacts. Cancel is command_id-idempotent, terminal cancellation is a recorded no-op. Missing deployment does not disable unrelated local apps. No-copilot apps work without a model.

Windows desktop mini-app acceptance is separate from QMN: current ratified node placement remains Ubuntu systemd/unix powers. Single-machine QMN placement GAP-0058 is open. Do not present unverified Windows node controls as ready.

Useful test references: tests/test_product_session_grants.py, test_product_session_chrome.py, test_nested_mission.py, test_nested_mission_widget.py, test_editor_draft.py, test_epic72_pack_ui.py, test_mailbox_lost_ack.py, test_pairing_listener.py, test_qmb_backtesting_door.py under qmx-agents/packages/qma-daemon.
