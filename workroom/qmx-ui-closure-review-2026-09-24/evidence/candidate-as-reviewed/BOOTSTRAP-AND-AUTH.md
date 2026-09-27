---
name: Bootstrap and authentication
sitting: architecture-QMX-UI-2026-09-23
inspect: integration@34c148be404a375cbfd79fd4ce6997452e4f1d20
closes: Codex REVIEW.md R2
status: sitting-candidate — not operator-accepted
tests: unexecuted
---

# Bootstrap and authentication (v1)

Architecture only. No implementation. This companion names **one** v1 bootstrap owner and the browser authentication bridge. It does not mint a sixth COMP, a QMA/QMN operator CLI, a UI BFF, or a second orchestrator.

**Provenance:** sitting candidate default for Codex R2. Not user-accepted. Parent and kit ADs stay read-only. Research notes (`research/14`, `research/17`) are evidence, not law.

**Codex R2 answer — one v1 bootstrap owner:** **COMP-QMB**, via the existing QMB operator CLI (parent AD-21). Named backend add: `qmb host start|status|stop`. That group **does not exist** at `integration@34c148b`. Until it ships, the UI “Start local” control is a **setup screen** with the documented `python -m qma.daemon` recipe. It is **not** a spawn.

## 1. Locked defaults (candidate)

| Lock | Rule |
| --- | --- |
| Delivery | v1 is a **browser SPA** on a **static origin** (SvelteKit dev server or static file server). Never served from daemon port **8765**. |
| Runtime | `qma-daemon` must **already be running** or be started by the **QMB CLI**. Browser JavaScript **must not** spawn Python. |
| Privileged owner | COMP-QMB / `qmb` (parent AD-21). No `qma-cli`. No tray/service COMP. |
| Named add | `qmb host start\|status\|stop` (absent at inspect). |
| Until that add | UI “Start local” = setup copy + recipe. Not `child_process`, not Tauri `plugin-shell`, not a hidden helper. |
| Data root | Env `QMA_DAEMON_ROOT` = **stable per-user directory**. Not launch cwd. |
| Single instance | Lock file under that root refuses a second daemon. |
| Discover | Default **`127.0.0.1:8765`**. A recorded remote is operator-entered. Remote failure **never** retargets to local. |
| Pre-protocol auth | CT-40 `authenticate_before_protocol(credential_ref, principal_class)` with `operator` \| `machine` **before protocol bytes**. Secrets never on the wire. |
| How the browser gets the ref | **Loopback pairing.** First visit from an unpaired origin shows a pairing code. Operator confirms in QMB (daemon stores the bind). Daemon binds that **browser origin** to the **operator** principal and issues the connection `credential_ref`. |
| Not operator proof | Possession of an arbitrary `cred://…` string is **not** proof of the operator. Provider refs (`cred://models\|inference\|…`) stay Credential-Broker material, not a login. |
| Queries and commands | HTTP GET queries and WebSocket commands require the **same** authenticated session. |
| Origins | Allowed origin = the static origin that completed pairing. CORS **refuses** others. |
| Close browser | `wire.detach` only. Never cancel `JobHandle`s. Never stop the daemon. |
| Stop local runtime | `qmb host stop` only. Does not cancel QMN or other remote work. |
| Second tab | Same origin, same daemon, **new** `producer_id`, **same** `psess:` if selected. |
| Remote | `wss://` + HTTPS; pairing recorded against that host; disconnect stays disconnected. |
| Tauri | Later. When it ships it may call the **same** QMB host verbs as a sidecar **caller**. It is not a second owner and not required for v1. |

## 2. Why this owner (and what was refused)

Codex R2: a launcher, a per-user service, and a manually started daemon all fitted the earlier prose and disagreed on lifetime, port/root, credentials, and Stop. The sitting must choose one.

| Candidate | Verdict |
| --- | --- |
| Browser JS starts `python -m qma.daemon` | **Refused.** A page cannot spawn the privileged process (research/17: a normal browser does not get shell/fs/credential APIs). |
| New launcher COMP / tray binary as product owner | **Refused.** Parent AD-1: no sixth COMP. Parent AD-21: QMB is the only operator CLI. |
| Tauri sidecar owns the Python child | **Refused for v1.** Research/17: official v2 has spawn/kill, no supervisor. Window-kill of a child daemon would make close ≈ stop, which local AD-12 / parent AD-17 forbid. Tauri may later **call** `qmb host *`. |
| Externally running daemon with no named door | Incomplete. Operator still needs one start/status/stop path; that path is QMB. |
| **QMB `qmb host *` supervises `python -m qma.daemon`** | **Chosen.** Same CLI already used for headless ops. Daemon stays the runtime. UI stays a CT-40 client. |

`python -m qma.daemon` remains the **process entry** (DEC-0336: not an operator CLI). QMB is the operator-facing supervisor. The daemon never `import qmb`.

## 3. Process topology (v1)

```text
  [static origin]                    never port 8765
    Vite / adapter-static / file server
           |
           |  browser SPA (ssr=false)
           |  Origin: e.g. http://127.0.0.1:5173
           v
  CT-40: pre-protocol auth → initialize → HTTP GET + JSON-RPC WS
           |
           v
  qma-daemon  127.0.0.1:8765     QMA_DAEMON_ROOT + .daemon_writer
           ^
           |  start | status | stop | pair-confirm
  qmb host (COMP-QMB CLI)   ← only privileged door
           |
           +-- does not import into the UI process
           +-- does not become a second Mission orchestrator
```

No UI-owned scheduler, grant store, or wire bus. Packs, grants, envelopes, and JobHandles stay in existing COMPs.

## 4. Static origin, discovery, data root, lock

### 4.1 Who serves the SPA

The SPA is `apps/qmx-ui` (future; absent at inspect) with `@sveltejs/adapter-static` and `ssr = false` (local AD-2). Fallback is `200.html` on a static host.

**Forbidden:** daemon listener serving chrome, a REST BFF, or any new protocol family on 8765. Port 8765 remains initialize + the three CT-40 families (commands JSON-RPC WebSocket, queries HTTP GET, events durable stream via `wire.attach`).

### 4.2 Discover

| Target | How it is known | Probe |
| --- | --- | --- |
| Local default | Built-in | `127.0.0.1:8765` (`DEFAULT_BIND_PORT` at inspect) |
| Local override | Operator-recorded bind (same machine) | That host:port; still loopback unless recorded non-loopback |
| Remote | Operator-entered recorded config | `wss://` + HTTPS only. **No** silent fallback to loopback |

Probe states for chrome: `none` / `starting` (QMB reported) / `loopback-live` / `remote-recorded` / `refused`. Closing splash without a daemon still opens the shell **disconnected** (local AD-11). Headless `qmb` remains usable without the UI.

### 4.3 Stable data root

`qmb host start` **must** set `QMA_DAEMON_ROOT` before spawn. Candidate per-user paths:

| OS | Directory |
| --- | --- |
| Windows | `%LOCALAPPDATA%\QMX\qma-daemon` |
| Linux | `${XDG_STATE_HOME:-$HOME/.local/state}/qmx/qma-daemon` |

At inspect, `__main__.py` defaults to cwd-relative `"qma-daemon-data"`. Two launches from two folders would be two sqlite/journal trees fighting the lock. The cwd default is **not** the shipped product root. The interim recipe below exports the per-user path explicitly.

### 4.4 Single instance

Reuse inspect lock: `DaemonWriterLock` file **`.daemon_writer`** under the persistence root (`qma-daemon/src/qma/daemon/persistence/lock.py`). `O_CREAT|O_EXCL`; a distinct writer is `policy_rejection` (`FR-Q22`). Bind collision on `8765` is a separate `OSError` from `asyncio.start_server`.

`qmb host start` when the lock is already held by a live pid: report **already running** (status), do not spawn a second process. Stale lock with a dead pid is a QMB/daemon recovery concern, not a UI rewrite of the lock.

## 5. Authentication and pairing

### 5.1 What already exists (shape only)

CT-40 `qma-wire/src/qma/wire/auth.py`:

- Every client authenticates with a Credential-Broker **reference** before protocol bytes.
- Connection carries exactly one principal class: `operator` or `machine` (`AuthenticatedWireSession`).
- `authenticate_before_protocol` parses `credential_ref` via `parse_credential_ref` and `principal_class`. It **does not** call the broker. It **does not** prove the caller is the operator.
- `assert_no_secret_on_wire_surface` refuses keys such as `api_key`, `token`, `password`, `bearer`, `secret`, and inline `secret=` / `token=` / `bearer ` prefixes.

`WireConnection.authenticate` stores the ref + principal, immutable for the connection life. Family messages before authenticate+initialize are policy refusals. Listener posture: unauthenticated bind and plaintext non-loopback are **hard startup refusals** (`listener.py`).

**Honesty:** those modules are types + tests. `DaemonProcess._handle_client` reads TCP chunks and discards them. No live pairing, CORS, or session cookie exists at `34c148b`.

### 5.2 Two credential planes (do not mix)

| Plane | What | Who proves it | Browser |
| --- | --- | --- | --- |
| **Connection** | Pairing-issued `credential_ref` + `principal_class=operator` | Daemon pairing record: `(origin, credential_ref, principal)` | Obtained only by pairing |
| **Provider / adapter** | Allowlisted `cred://models\|inference\|compute\|sandbox\|corpus\|knowledge\|telemetry/` | Credential Broker exact-ref resolve (adapter layer only) | Never a login. UI may later collect a value into OS store as a **ref**; daemon never sees the secret |

Allowlist is code in `qma-core` (L34 / DEC-0323). UI must not offer `cred://venue|broker|exchange|trading-node|platform-registry/`. Pasting a provider ref into the wire as if it were operator proof is refused.

Browser UI authenticates as **`operator` only**. `machine` is for workers / dial-out. A page presenting `principal_class=machine` is `POLICY_REJECTION`.

### 5.3 Loopback pairing (how the browser obtains the ref)

Browser JavaScript cannot read Windows Credential Manager and must not paste secrets. Pairing is the v1 bridge.

1. Operator opens the SPA on its **static origin** (dev or file server), not on `:8765`.
2. SPA probes `127.0.0.1:8765` (or the recorded remote). If the daemon is down → disconnected setup (section 8).
3. SPA opens the wire **without** family messages. Unpaired `Origin` → daemon returns a **pairing challenge** (short code + expiry). This is not an unauthenticated protocol bind: no `initialize`, no commands, no queries succeed.
4. UI shows the code (setup chrome, not a secret form).
5. Operator confirms the code on the privileged door: **`qmb host pair <code>`** (same host group as start/status/stop; also **absent** at inspect). Interim until that verb exists: confirm in the daemon’s operator-visible pending-pair record **through QMB**, never by typing a secret into the browser. The daemon **stores** the bind; QMB does not become a second grant store.
6. On confirm, daemon:
   - binds **that browser origin** to **`principal_class=operator`**;
   - mints a pairing-issued connection `credential_ref` (CredentialRef shape; not a resolved secret; not a provider allowlist key);
   - records expiry / revocation.
7. Browser receives **only** that reference (and origin-bound session handle). It stores it as a **reference**, not a secret. Subsequent connections present `credential_ref` + `operator` **and** `Origin`. Daemon accepts iff the pairing table matches **all three**: origin, ref, principal.
8. Then `initialize` (section 6).

**Possession of an arbitrary `cred://…` ref is not operator proof.** A stolen or guessed provider ref, or a ref copied from docs, does not bind an origin. Confirmation is a human act on the QMB door.

**Secrets never on the wire.** Pairing code is a challenge identifier, not a password. Connection `credential_ref` is a reference. Provider values never appear in envelopes, query strings, traces, or diagnostics (`FORBIDDEN_SECRET_SURFACE_KEYS`).

Remote pairing: same steps against the recorded host over `wss`/`https`. The pairing record is **that** daemon’s origin bind. A loopback pairing does not authorize a remote host, and vice versa.

### 5.4 HTTP GET and WebSocket share the session

After pairing+authenticate+initialize:

| Family | Transport | Auth |
| --- | --- | --- |
| Commands / events | JSON-RPC 2.0 WebSocket (`ws://` loopback, `wss://` otherwise) | Same `AuthenticatedWireSession` |
| Queries | HTTP GET snapshots (authoritative) | Same session. Origin must be the paired origin. |

CORS: allow **only** the paired static origin. `Access-Control-Allow-Origin` is that exact origin (not `*`). Other origins: refuse. Preflight failure is not a retarget.

Query credentials: the pairing-issued **reference** (header or cookie that is the ref, not a secret value). `SameSite=Strict`. Loopback may use `http://` (local AD-12). Non-loopback requires HTTPS. Do not put refs in query-string logs as if they were public ids of provider secrets — connection refs are still not operator-proof off that origin.

No REST `/invoke`. No UI BFF.

### 5.5 Reconnect vs re-pair

Reconnect (local AD-11 / parent AD-29) is a **query path**: same pairing (unexpired), `authenticate_before_protocol` again, `initialize` with the **same** `producer_id` for that tab, snapshot queries, `product_session.reconnect(resume_cursor, cursor_generation)`, `wire.attach(scope, since_seq)`, `JobHandle.reattach`. It does **not** replay intent, resubmit unacked commands, or imply approval.

Expired / revoked pairing → pairing challenge again. Do not reuse a dead ref. Do not fall back to unauthenticated loopback (`registry:proxy.allow_unauthenticated_loopback` is the **model proxy**, not the UI wire).

## 6. End-to-end sequence (no daemon → invoke)

Architecture sequence. **Unexecuted.** Live JSON-RPC/HTTP/event serving is a backend add (section 10).

```mermaid
sequenceDiagram
  participant U as Operator
  participant B as Browser SPA (static origin)
  participant Q as qmb host (COMP-QMB)
  participant D as qma-daemon
  participant C as Credential Broker
  participant O as Owner COMP

  U->>B: open SPA (not :8765)
  B->>B: probe 127.0.0.1:8765
  B-->>U: disconnected + Start local (setup)
  U->>Q: qmb host start<br/>(or interim python -m qma.daemon)
  Q->>D: set QMA_DAEMON_ROOT, spawn process entry
  D->>D: acquire .daemon_writer, bind 8765
  Q-->>U: status running
  B->>D: TCP/WS connect (no family bytes)
  D-->>B: pairing challenge (code)
  B-->>U: show code
  U->>Q: qmb host pair CODE
  Q->>D: confirm
  D->>D: bind Origin to operator + mint credential_ref
  D-->>B: credential_ref (reference only)
  Note over B,D: authenticate_before_protocol(ref, operator)
  Note over C: broker is not the login; pairing table is
  B->>D: initialize {protocolVersion, capabilities, producer_id?}
  D-->>B: protocolVersion, capabilities, producer_id
  B->>D: HTTP GET query (same session, paired Origin)
  D-->>B: snapshot
  B->>D: JSON-RPC command + InvocationEnvelope
  D->>D: GrantRecord compare
  D->>O: dispatch op
  O-->>D: JobHandle
  D-->>B: ack then events
  U->>B: close tab
  B->>D: wire.detach
  Note over D: JobHandles unchanged; daemon keeps running
```

### Step list

0. **No daemon.** Splash/status, then usable disconnected shell (J-UI-11). “Start local” is setup, not a spawn.
1. **Start.** Operator runs `qmb host start` (when it exists) **or** the interim recipe. QMB/recipe sets `QMA_DAEMON_ROOT`, starts `python -m qma.daemon`. Lock + bind succeed or typed refusal.
2. **Connect.** SPA discovers `127.0.0.1:8765` (or recorded remote). Does not retarget.
3. **Pair.** Challenge → operator confirms in QMB → origin bound to operator → browser holds connection `credential_ref`.
4. **Authenticate.** `authenticate_before_protocol(credential_ref, principal_class=operator)` before protocol bytes. Secrets absent.
5. **Initialize.** JSON-RPC `initialize` (`WIRE_PROTOCOL_VERSION = "1.0.0"`). Server assigns or echoes a stable per-tab `producer_id`.
6. **Query.** HTTP GET snapshots (listing, `product_session`, health cards). CORS = paired origin.
7. **Attach (optional).** `wire.attach(scope, since_seq)` for events. Events are not authoritative.
8. **Invoke.** Unique host issuer `dispatchInvoke` builds parent-AD-24 `InvocationEnvelope`. Until `caller_kind` exists on the daemon, pack invoke refuses `caller_kind_unsupported`; headless `qmb` remains the operator door (local AD-8). This companion does not change that refuse.

Interim recipe (until `qmb host start`; Windows candidate):

```text
set QMA_DAEMON_ROOT=%LOCALAPPDATA%\QMX\qma-daemon
python -m qma.daemon
```

Document bind `127.0.0.1:8765`. This is operator setup, not a product CLI, and not a browser action.

## 7. Failure cases

| Case | What happens | Must not |
| --- | --- | --- |
| **Daemon down** | Probe `none`. Shell disconnected. Start local = setup / `qmb host start`. Headless `qmb` still works. | Spawn from JS. Block all chrome behind a modal forever. |
| **Second instance** | New process fails `.daemon_writer` (and/or port 8765). `qmb host start` reports already-running or typed lock refusal. UI stays on the live daemon if it can pair. | Two sqlite writers. UI “force start”. Delete the lock from the browser. |
| **Bad origin** | Origin not the paired static origin → CORS refuse and/or pairing mismatch. No initialize. | `Access-Control-Allow-Origin: *`. Serving the SPA from 8765 to “fix” CORS. |
| **Expired / revoked pairing** | Challenge again. Previous `credential_ref` refused. Queries and WS drop. | Treat leftover ref as operator. Unauthenticated loopback fallback. |
| **Remote disconnect** | Target stays the recorded remote. Chrome: reconnecting → unavailable. Jobs on that host unchanged by tab state. | Silently switch to `127.0.0.1:8765`. Invent local success. |
| **Remote never recorded** | Connect-remote is an explicit operator entry. Empty record ≠ local. | Implicit last-known-good local. |
| **Protocol / byte drain (today)** | At inspect the listener discards bytes. UI must show backend-incompatible / not-ready, not a blank “connected”. | Pretend initialize succeeded against the stub. |
| **Close browser** | `wire.detach`. JobHandles unchanged. Daemon keeps running. | Cancel, `qmb host stop`, QMN drain. |
| **`qmb host stop`** | Local daemon drain + lock release. Local env JobHandles may become `unknown` (operator resolves). QMN/remote work continues. | Call this on tab close. Paint `unknown` as `failed` or `cancelled`. |
| **Laptop sleep / GAP-0062** | Daemon on the laptop dies with the machine. Do not promise lid-closed continuation. | Splash copy that work continues offline. |
| **Arbitrary `cred://` pasted** | Not a pairing record → refuse. | Broker-resolve as login. |

## 8. Lifetime: close, stop, cancel, remote

| Act | Owner | Effect |
| --- | --- | --- |
| Close tab / window | UI | `wire.detach`. Chrome gone. |
| Stop local runtime | QMB `qmb host stop` | Stops host-supervised **local** daemon only. |
| Cancel work | `JobHandle.cancel` only (local AD-13) | Coordinated cancel; first durable terminal wins. |
| Stop QMN / remote | Node powers / that environment’s door | Never implied by UI close or local host stop. |

Docker workers on the workstation die with the local daemon. That is not QMN. Local proxy (model plane) is outside QMA; host stop does not stop it.

## 9. Second tab and `producer_id`

| Axis | Rule |
| --- | --- |
| Origin / daemon | Same paired origin, same daemon process. |
| Pairing | Shared. Second tab does not re-prove the operator if pairing is valid for that origin. |
| `producer_id` | **New** per UI process (browser tab / window). Stable across **that** tab’s reconnects. Initialize may hint; server assigns if empty. |
| `psess:` | Same row if the operator selected the same session. Two tabs of one `psess:` share the server row (local AD-4). Closing a tab writes nothing. |
| Wire `id` | Unique per `(producer_id, id)`. |
| Product-session `command_id` | Unique across all surfaces sharing `(psess, principal)` (parent AD-29). Distinct from wire `id` and invoke `idempotency_key`. |

This companion does not invent a cross-tab producer coordinator. New tab ⇒ new producer. Command ids stay globally unique at the session layer so two tabs cannot collide payloads.

## 10. Owners

| Concern | UI (`apps/qmx-ui`) | QMB CLI | qma-daemon | Credential Broker |
| --- | --- | --- | --- | --- |
| Serve SPA | Consumes static origin | No | **No** (not on 8765) | No |
| Start / status / stop local daemon | Setup screen only; never spawn | **`qmb host *` (add)** | Process entry `python -m qma.daemon` | No |
| `QMA_DAEMON_ROOT` | Must not pick a cwd root | Sets on start | Reads env; opens substrate | No |
| Sole-writer lock | No | Surface refusal on start | **`.daemon_writer`** | No |
| Pairing challenge UI | Shows code; stores issued **ref** | **`qmb host pair` (add)** | Stores origin↔operator bind | No |
| `authenticate_before_protocol` | Presents ref + `operator` | No | Enforces before protocol bytes | Shape is CredentialRef; **not** login |
| Provider secrets | Write-once OS helper is a later native/QMB path; v1 browser does not hold values | Operator CLI for host, not a secret form | Never receives values | Exact-ref resolve, adapter layer only |
| HTTP GET / WS / CORS | Speaks CT-40 as client | No | Listener + origin allowlist (**add**) | No |
| `initialize` / `producer_id` | One producer per tab | No | Assigns / echoes | No |
| Invoke / grants / JobHandles | `dispatchInvoke` client | Headless door (parent AD-21) | Host compare + dispatch | No |
| Close tab | detach | No | Subscription drop only | No |
| Stop local runtime | Settings action → tell operator to run QMB (or call status) | **`qmb host stop`** | Drain + release lock | No |
| Remote record | Connect-remote form; no silent local fallback | May record via host config later | Non-loopback needs recorded config + TLS | No |
| Tauri (later) | Same SPA | Same verbs | Unchanged | Unchanged |

QMB host is **process supervision**, not Mission orchestration, not a second grant store, and not a substitute for envelope invoke.

## 11. Backend adds — honesty at `integration@34c148b`

Class: **reuse** / **adapt** / **add** / **absent**. Types and in-process tests are not e2e. **No test in this sitting was executed against a live browser or installed product.**

| Item | Inspect fact | Class | Owner |
| --- | --- | --- | --- |
| `python -m qma.daemon` | Exists. Not an operator CLI. Default root cwd-relative `"qma-daemon-data"`. | reuse process entry; **adapt** root via env | COMP-QMA-DAEMON |
| Bind `127.0.0.1:8765` | `DEFAULT_BIND_PORT = 8765`. `_handle_client` **discards bytes**. | reuse bind; **add** live protocol | COMP-QMA-DAEMON |
| `.daemon_writer` | `DaemonWriterLock` coded + tested | reuse | COMP-QMA-DAEMON |
| `authenticate_before_protocol` | Shape gate; does **not** call broker; not on the listener | reuse types; **add** wire-up + pairing check | COMP-QMA-WIRE + DAEMON |
| Credential Broker | Exact-ref; WinCred `_reader` **uninjected** in `DaemonProcess.compose` | reuse types; **hole** OS read | COMP-QMA-DAEMON |
| `initialize` / families | Types + schemas; `websockets` **zero imports** | reuse contract; **add** JSON-RPC WS + HTTP GET server | COMP-QMA-WIRE + DAEMON |
| CORS / origin allowlist | **Absent** | **add** | COMP-QMA-DAEMON |
| Loopback pairing table | **Absent** | **add** | COMP-QMA-DAEMON (store) + COMP-QMB (confirm) |
| `qmb host start\|status\|stop\|pair` | CLI groups: `backtest`, `data`, `optimize`, `sweep`, `robustness`, `ledger`, `library`, `analysis`, `config`. **No `host`.** | **add** | COMP-QMB |
| SPA / `apps/qmx-ui` | **Absent** | **add** (UI stream) | this sitting’s host, later |
| Tauri sidecar supervisor | **Absent**; official v2 has no health/restart API (research/17) | deferred | later desktop; still calls QMB verbs |
| Serving UI from 8765 | Must not ship | forbidden | — |
| Sixth COMP / second orchestrator | Forbidden | forbidden | — |

Live CT-40 server remains a **backend prerequisite** (CHANGE-IMPACT, local AD-16). This companion does not claim it shipped.

## 12. `qmb host` contract (named add)

Absent at inspect. When added, thin QMB door over daemon process lifetime — not a new runtime, not `import qma.daemon` into every QMB run.

| Verb | Does | Does not |
| --- | --- | --- |
| `qmb host start` | Set `QMA_DAEMON_ROOT` to the per-user path; spawn `python -m qma.daemon` if lock free; wait until bind or already-running | Orchestrate Missions; grant ops; start QMN |
| `qmb host status` | Lock, pid, bind, pairing pending/bound origins (refs only) | Enumerate Credential Manager |
| `qmb host stop` | Stop the local daemon; release lock | Cancel QMN/remote; `JobHandle.cancel` for every job (local handles may go `unknown`) |
| `qmb host pair <code>` | Confirm pairing challenge | Accept a provider secret; bind a non-matching origin |

Until these verbs exist, status is operator-visible via OS process list + the setup screen’s probe, and pair confirm has **no** product door — the UI must not fake a paired session.

## 13. Tauri (later, not v1)

v1 does not wait on Tauri (local AD-12). Research/17: Tauri 2.11.6 can wrap the same static SPA and spawn a sidecar, but has no official daemon supervisor; Rust command IPC is **not** qma-wire.

When a desktop shell ships:

- Same SPA origin rules inside the webview (or the webview origin is the paired origin).
- Privileged start/stop **calls `qmb host start|status|stop`** (or equivalent QMB library door). Sidecar spawn is a **caller** of that door, not a second owner.
- Close window = detach, same as the browser, unless the operator chose Stop local runtime.
- Do not make the daemon a child of the window job object such that close kills workstation work by default.

## 14. Tests (all **unexecuted**)

Intended classes only. None were run in this sitting. Reticle `unknown` is not a pass. Installed-product proof is not Reticle-only.

| Class | Intent |
| --- | --- |
| Contract | Pairing record matches origin+ref+principal; arbitrary `cred://` refused; secrets on surfaces refused (`auth.py` already unit-tests shape). |
| Process | Second `python -m qma.daemon` on the same `QMA_DAEMON_ROOT` hits `.daemon_writer`; `qmb host start` is idempotent when live. |
| Browser | SPA origin ≠ 8765; CORS denies a second origin; close tab does not emit cancel. |
| Failure | Daemon down → disconnected; remote drop does not probe loopback as success; expired pairing re-challenges. |
| Installed product | Launch outside checkout with `QMA_DAEMON_ROOT` set; recipe/QMB start; pairing; initialize. **Unexecuted.** |

## 15. Citations

- Parent AD-21 — headless door parity; QMB is the only operator CLI; a log/progress panel is not a general shell. `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-18/ARCHITECTURE-SPINE.md`
- CT-40 `auth.py` — `authenticate_before_protocol`, `AuthenticatedWireSession`, `FORBIDDEN_SECRET_SURFACE_KEYS`. `.worktrees/integration-inspect/qmx-agents/packages/qma-wire/src/qma/wire/auth.py`
- `listener.py` — loopback default; unauthenticated / plaintext non-loopback hard refusal. Same inspect tree.
- `initialize.py` — JSON-RPC `initialize`, `WIRE_PROTOCOL_VERSION = "1.0.0"`, `producer_id`. Same inspect tree.
- `__main__.py` / `process.py` / `persistence/lock.py` — process entry, bind 8765, byte drain, `.daemon_writer`.
- QMB CLI tree — no `host` group. `.worktrees/integration-inspect/qmb/src/qmb/doors/cli/tree.py` `COMMAND_GROUPS`
- research/14 — first-run, `QMA_DAEMON_ROOT`, close≠stop, Option A/C lifetime, CredRead hole
- research/17 — browser lacks native spawn/fs/secrets; Tauri sidecar is not a supervisor; QMX does not require Tauri
- Codex `workroom/qmx-ui-review-2026-09-23/REVIEW.md` **R2** — name one v1 bootstrap owner; sequence; owners; backend changes; do not force Tauri or a second orchestrator
- Local AD-2, AD-11, AD-12, AD-13, AD-16 — static origin, probe, Python runtime, close/stop/cancel, backend add for live protocol

## 16. What this file does not do

- Does not edit `ARCHITECTURE-SPINE.md`.
- Does not implement pairing, `qmb host`, or a live wire server.
- Does not choose OpenCodex as a vendor login.
- Does not promise GAP-0062 always-on, GAP-0058 single-machine node, or GAP-0070 computer-use.
- Does not treat inspect types as e2e.
