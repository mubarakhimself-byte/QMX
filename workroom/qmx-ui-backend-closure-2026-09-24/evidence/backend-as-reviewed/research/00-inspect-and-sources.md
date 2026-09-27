# Inspect SHA and primary sources

Sitting: architecture-QMX-UI-BACKEND-2026-09-24. Evidence, not law.

## Git pins (2026-09-24)

| Ref | SHA |
| --- | --- |
| `main` (workspace HEAD) | `92279dfe43922d60fabe38e29284ca52956ab75c` |
| `integration` | `34c148be404a375cbfd79fd4ce6997452e4f1d20` |
| inspect worktree | `.worktrees/integration-inspect` at the same integration SHA |

Working-tree edits outside those refs are not treated as delivered.

## Code facts at `34c148b`

| Surface | Evidence |
| --- | --- |
| Daemon listener | `qma-daemon/src/qma/daemon/process.py` `DEFAULT_BIND_PORT = 8765`; `_handle_client` reads and discards bytes |
| Pre-protocol auth | `qma-wire/src/qma/wire/auth.py` `authenticate_before_protocol` parses `credential_ref` + `principal_class`; does not call the broker; `FORBIDDEN_SECRET_SURFACE_KEYS` includes `token`/`bearer` |
| Wire vocab | Seed commands include `send_message`, `stop_run`. Queries: seven seed + `list_mission_hooks`, `plugin_install_preflight`, `facade_search`, `facade_get`. **No** `list_mailbox`, `cancel_job` |
| Mailbox Envelope | `qma-core/src/qma/core/ports/mailbox.py` fields: `msg_id`, from/to, `kind`, `correlation_id`, `body`, `priority`, `created_at`, optional mission/task/reply/causation/artifact_refs. **No** `product_session_id` |
| JobHandle | `qma-core/src/qma/core/ports/jobs.py` + daemon `envs/jobs.py`. States closed. `logical_run_id`, `attempt_id`, `later_commands`. **No** `originating_psess`. Store is in-memory dict |
| ProductSession | `sessions/product_session.py` profiles AUTHORING/APP_USE; `app_instance_id` field present as string; reconnect snapshot `replays_unacked_intent=False` |
| PluginManifest | `permissions` tuple exists. **No** `copilot_profile` |
| QMB CLI | `COMMAND_GROUPS` = backtest, data, optimize, sweep, robustness, ledger, library, analysis, config. **No** `host` |
| Artifact cite | Knowledge `cite` copies through `before_artifact_register` into an in-memory artifact map |
| Credential broker | `proxy/broker.py` `_reader` mapping; UI sitting recorded WinCred reader uninjected in `DaemonProcess.compose` |

## Planned anchors (not implementation)

- Epic 41: wire families, initialize, compatibility, listener auth (credential_ref before protocol), principal classes
- Epic 42: sole-writer journal, sqlite, mailbox projection, staging, artifacts
- Epic 46 Story 46.4: durable Quant Mailbox Envelope (CT-48 / FR-Q60)
- Epic 57: task_graph_state, outbox, JobHandle vocabulary, later-command no-ops
- Epic 60–65 / FEAT-0058–0063: copilot_profile, caller_kind, optional authoring instance, diagnosis, retry, nested Mission, health/listing, kit proofs

## Primary sources checked 2026-09-24

| Source | Observed fact used here |
| --- | --- |
| [RFC 6455 §10.1](https://datatracker.ietf.org/doc/html/rfc6455#section-10.1) | Non-browser clients can send fake Origin; servers must not assume Origin identifies the operator |
| [RFC 6455 §1.3 / handshake](https://datatracker.ietf.org/doc/html/rfc6455) | Server echoes **one** selected `Sec-WebSocket-Protocol` |
| [WHATWG WebSockets](https://websockets.spec.whatwg.org/) | `new WebSocket(url, protocols)`; connection established only if the server selects one offered subprotocol; browsers do not expose an Authorization header on the constructor |
| [HTML Web storage](https://html.spec.whatwg.org/multipage/webstorage.html) Living Standard 2026-09-22 | `sessionStorage` is per window/tab; a new window has its own copy; **after creating a new auxiliary browsing context, session storage is copied over** |
| [Fetch CORS](https://fetch.spec.whatwg.org/) | `credentials: 'omit'` + exact `Access-Control-Allow-Origin`; `*` is incompatible with credentialed include; Authorization is a request header that still needs `Access-Control-Allow-Headers` |
| [RFC 9110 PUT](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.3.4) | PUT is idempotent; §14.5 defines partial PUT — v1 QMX does not use it |
| [RFC 9110 §8.6 Content-Length](https://www.rfc-editor.org/rfc/rfc9110.html#section-8.6) | Content-Length describes the request content; incomplete body is not a completed PUT |

## Additional consequence from the HTML spec

A **cloned / auxiliary** tab copies `sessionStorage`. That tab may already hold `pairing_session_id`. Treating that as Origin-only issuance would be wrong. It is existing proof. `producer_id` still must not be shared with a live sibling connection (UI local AD-24).
