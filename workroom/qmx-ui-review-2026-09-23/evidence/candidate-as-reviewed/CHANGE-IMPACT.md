---
name: Change-impact map
sitting: architecture-QMX-UI-2026-09-23
inspect: integration@34c148b
---

# Change-impact map

Classification: **reuse** / **adapt** / **add** / **unresolved**. No screen-to-service invention. Types at `34c148b` are not e2e.

| Requirement | Current owner | Evidence | Class | UI / core change |
| --- | --- | --- | --- | --- |
| Invoke with envelope + grant | COMP-QMA-WIRE + DAEMON | `invocation_envelope.py`, `grant_record.py` | reuse types; **add** live JSON-RPC dispatch on `DaemonProcess` | UI host client; backend must stop swallowing TCP bytes |
| `product_session` two profiles | COMP-QMA-DAEMON | `product_session.py` | reuse; **adapt** optional `app_instance_id` for authoring | Home cannot omit instance until FEAT-0058-class amend |
| `caller_kind` | specified kit AD-4 | **0 hits** in inspect Python | **add** (backend) | UI must not emit the field until the amend lands |
| `view:*` DTO | COMP-QMA-WIRE | `view_presentation.py` | reuse DTO; **add** native mounts | No `ui_view` point (local AD-15) |
| `copilot_profile` | specified | absent | **add** (pack manifest, optional) | Headless remains valid without it |
| JobHandle cancel / unknown | COMP-QMA-CORE/DAEMON | `ports/jobs.py` | reuse vocab; **add** wire methods | Chrome must not invent states |
| `wire.attach` / reconnect | COMP-QMA-WIRE | `attach.py` types | reuse types; **add** server | UI reconnect = query |
| `facade_search` | COMP-QMA-DAEMON | concatenate service + tests | reuse in-process; **add** HTTP query door | Library chrome |
| QMB `library.search` | COMP-QMB | `qmb.registryread.search` | reuse | Artifact rail |
| `qml.research` | COMP-QML | module + host blob store | reuse; browse listing thin | Hypothesis off facade |
| Credential Broker | COMP-QMA-DAEMON | `proxy/broker.py` | reuse resolve; **add** host write-to-OS-store | First-run cards |
| QMN secrets / evidence HTTP | COMP-QMN | coded | reuse; UI later fronts refs | No laptop venue-key store |
| Listing axes | COMP-QMA-DAEMON | `listing.py` overlay | adapt (in-memory overlay today) | Do not collapse axes |
| instance `health()` | kit AD-5 | absent | **add** (backend, FEAT-0059-class) | Ops chrome consumes when present |
| Daemon JSON-lines / `failure_class` | specified | absent | **add** (backend) | UX-11 |
| Default host retry | specified | absent as loop | **add** (backend) | UI Retry follows matrix |
| Nested Mission invoke | specified | envelope parent/depth only | **add** (backend) | Graph must not splice live graphs |
| Svelte shell | none | no package.json in git | **add** | New `apps/qmx-ui` |
| Tauri 2 | none | | unresolved as required; **proposal** optional | local AD-12 |
| json-render / MCP host | adapter law | packages absent | **add** optional frontend adapters | Not in Python core |
| Live websocket `websockets` 17.1 | stack.md | **zero imports** | **add** (backend) | UI depends on it |
| `qma-ui-contract` | STUB.md | not a uv member | unresolved as a package | Chrome can ship against DTOs first |
| Financial chart lib | none | workflow 19: lightweight-charts 5.2.1 Apache-2.0 | **add** | LayerChart 2.5.0 is analytics only |
| MCP Apps host | adapter law | workflow 18: `@modelcontextprotocol/ext-apps` 2.0.0 | **add** optional frontend | Host intercepts `tools/call`; no catalog grant |
| Tauri sidecar supervisor | none | workflow 17: official v2 has spawn/kill, no health/restart API | unresolved for installer | v1 does not wait on Tauri |
| Envelope crypto | GAP-DESK-ENVELOPE-CRYPTO | | unresolved (backend) | UI still sends bound envelope |
| Performance budgets | none measured | | unresolved | Need a shell first |

Storage / migrations: no new sqlite class. Client layout prefs are local. Pack enable still uses parent AD-30 journal.

Ops: QMB remains the only operator CLI. UI must not mint `qma-cli`.
