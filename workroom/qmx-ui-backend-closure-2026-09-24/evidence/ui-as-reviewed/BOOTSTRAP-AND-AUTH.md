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

**Codex R2 answer — one v1 proof (browser-realizable):** **`pairing_proof`** (bearer credential). Nonsecret row identity is **`pairing_record_id`**. Unauthenticated bootstrap is HTTP POST `/pair/start` and `/pair/confirm` only. Authenticated HTTP GET sends `Authorization: Bearer pairing:<proof>`. Authenticated WebSocket offers WHATWG subprotocols `qmx.ct40.v1` and `qmx.pair.<proof>`. Cookies are refused. The browser does not present an arbitrary `cred://` as login. Matches local AD-19 and backend-delta AD-3/AD-4.

## 1. Locked defaults (candidate)

| Lock | Rule |
| --- | --- |
| Delivery | v1 is a **browser SPA** on a **static origin** (SvelteKit dev server or static file server). Never served from daemon port **8765**. SPA origin ≠ daemon origin. |
| Runtime | `qma-daemon` must **already be running** or be started by the **QMB CLI**. Browser JavaScript **must not** spawn Python. |
| Privileged owner | COMP-QMB / `qmb` (parent AD-21). No `qma-cli`. No tray/service COMP. |
| Named add | `qmb host start\|status\|stop\|pair\|configure` via **local host-control** (absent at inspect). First operator is that path (backend-delta AD-17). |
| Until that add | UI “Start local” = setup copy + recipe. Not `child_process`, not Tauri `plugin-shell`, not a hidden helper. Pair confirm = QMB-visible pending-pair until the verb exists. |
| Data root | Env `QMA_DAEMON_ROOT` = **stable per-user directory**. Not launch cwd. |
| Single instance | Lock file under that root refuses a second daemon. |
| Discover | Default **`127.0.0.1:8765`**. A recorded remote is operator-entered. Remote failure **never** retargets to local. |
| Unauthenticated bootstrap | HTTP POST **`/pair/start`** and **`/pair/confirm`** on the daemon origin only, plus CORS **`OPTIONS`** on named daemon HTTP routes (OPTIONS never issues a proof, never upgrades WS, never returns bytes). No CT-40 `initialize`, commands, or queries until pairing succeeds. Pairing HTTP **must not** open the authenticated wire. |
| One proof | **`pairing_proof`** (bearer). Issued **once** after `qmb host pair <code>` (local host-control) then POST `/pair/confirm`. Journal stores `pairing_record_id` + `proof_fp1`, never the raw proof. |
| Browser storage | **Memory + `sessionStorage` for that tab.** Not `localStorage`. Not IndexedDB. Not a cookie. Not a provider `cred://`. |
| Authenticated HTTP GET | Header `Authorization: Bearer pairing:<proof>` **plus** `Origin`. CORS **exact** paired static origin. |
| Authenticated WebSocket | WHATWG `new WebSocket(url, ["qmx.ct40.v1", "qmx.pair.<proof>"])`. Browsers **cannot** set `Authorization` on `WebSocket`. Documented below; not a second proof. |
| Cookies | **Refused** as the v1 proof. No `Set-Cookie` on `/pair/*`. No header-or-cookie fork. |
| Daemon mapping | Daemon matches Origin + `proof_fp1` to `pairing_record_id` and the **operator principal** minted at host-control bootstrap. Browser-paired sessions do **not** carry a broker `credential_ref`. Browser never sends an arbitrary `cred://` as login. |
| Second tab | New `producer_id`. Typed-URL tab POSTs `/pair/start` and needs **fresh QMB confirm**. A remembered Origin **never** issues a proof. Cloned tab that copied `sessionStorage` already holds `pairing_proof` and **reconnects**. `/pair/renew` is an explicit rotate, not the clone path. New `producer_id` if the old is live. |
| Same-tab restart | `sessionStorage` restores `pairing_proof`; reconnect until expiry. Expiry **closes** the WS. |
| Remote | HTTPS + `wss://`; pairing recorded on **that** host; disconnect does **not** become local. |
| Close browser | `wire.detach` only. Never cancel `JobHandle`s. Never stop the daemon. |
| Stop local runtime | `qmb host stop` only. Does not cancel QMN or other remote work. |
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

Pairing proof (same sitting, not a second owner):

| Candidate | Verdict |
| --- | --- |
| Unauthenticated CT-40 / family-wire pairing challenge (WS frame, then `initialize`) | **Refused.** Pairing must not open the authenticated wire. |
| Cookie (`SameSite=Strict` or otherwise) as the session | **Refused.** No header-or-cookie fork. Cookies are not the v1 proof. |
| `localStorage` of a `cred://` or session id | **Refused.** Not tab-scoped; not operator proof. |
| Browser sends an arbitrary `cred://` / `credential_ref` as login | **Refused.** Possession of a ref is not the operator. |
| HTTP `Authorization: Bearer pairing:<proof>` + WS subprotocol `qmx.pair.<proof>` | **Chosen.** One proof, two transports, both browser-realizable. `pairing_record_id` is the nonsecret journal identity. |

## 3. Process topology (v1)

```text
  [static origin]                    never port 8765
    Vite / adapter-static / file server
           |
           |  browser SPA (ssr=false)
           |  Origin: e.g. http://127.0.0.1:5173
           |
           |  (1) unauth HTTP POST /pair/start and /pair/confirm
           |  (2) auth HTTP GET  Authorization: Bearer pairing:<proof>
           |  (3) auth WS        subprotocols qmx.ct40.v1 + qmx.pair.<proof>
           v
  qma-daemon  127.0.0.1:8765     QMA_DAEMON_ROOT + .daemon_writer
           ^
           |  start | status | stop | pair | configure  (host-control, not CT-40)
  qmb host (COMP-QMB CLI)   ← only privileged door
           |
           +-- does not import into the UI process
           +-- does not become a second Mission orchestrator
           +-- maps Origin + proof_fp1 → operator principal + pairing_record_id
           +-- browser session has no credential_ref
```

No UI-owned scheduler, grant store, or wire bus. Packs, grants, envelopes, and JobHandles stay in existing COMPs.

## 4. Static origin, discovery, data root, lock

### 4.1 Who serves the SPA

The SPA is `apps/qmx-ui` (future; absent at inspect) with `@sveltejs/adapter-static` and `ssr = false` (local AD-2). Fallback is `200.html` on a static host.

**Forbidden:** daemon listener serving chrome, a REST BFF, or any new protocol family on 8765.

Port 8765 carries:

1. **Unauthenticated bootstrap (not a CT-40 family):** HTTP POST `/pair/start` and `/pair/confirm` only. These two paths must not accept `initialize`, commands, or queries, and must not upgrade to an authenticated WebSocket.
2. **Authenticated CT-40 (local AD-12):** JSON-RPC 2.0 WebSocket commands, HTTP GET snapshot queries (authoritative), `wire.attach` events (not authoritative), after pairing succeeds.

Pairing HTTP is bootstrap, not a fourth CT-40 family.

### 4.2 Discover

| Target | How it is known | Probe |
| --- | --- | --- |
| Local default | Built-in | `127.0.0.1:8765` (`DEFAULT_BIND_PORT` at inspect) |
| Local override | Operator-recorded bind (same machine) | That host:port; still loopback unless recorded non-loopback |
| Remote | Operator-entered recorded config | `wss://` + HTTPS only. **No** silent fallback to loopback |

UI probe is **HTTP reachability** of the daemon origin (loopback or recorded HTTPS). It is not an unauthenticated CT-40 session and not a pairing proof. Browser-painted states: `none` / `loopback-live` / `remote-recorded` / `refused`. The browser has **no door to QMB**, so it must not paint `starting`. `starting` is QMB CLI status only (`qmb host status`), never a SPA guess.

Closing splash without a daemon still opens the shell **disconnected** (local AD-11). Headless `qmb` remains usable without the UI.

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

**Honesty:** those modules are types + tests. `DaemonProcess._handle_client` reads TCP chunks and discards them. No live pairing table, CORS, HTTP `/pair/*`, `pairing_proof`, or CT-40 server exists at `34c148b`. Cookies are **not** planned and **must not** be added as a second proof.

**Sitting adapter (candidate):** the **browser** proof is `pairing_proof`, not a client-sent `credential_ref`. After Origin + `proof_fp1` match, the daemon builds `AuthenticatedWireSession` with `principal_class=operator` and `pairing_record_id`. Browser-paired sessions **do not** populate `credential_ref` and do not pass the proof to `parse_credential_ref`. Machine clients still present `credential_ref` (Story 41.4). The browser never calls `authenticate_before_protocol` with a pasted ref.

### 5.2 Two credential planes (do not mix)

| Plane | What | Who proves it | Browser |
| --- | --- | --- | --- |
| **Connection (v1 proof)** | `pairing_proof` bound to Origin + operator principal | Pairing table after local-control confirm (`proof_fp1`) | HTTP `Authorization: Bearer pairing:<proof>`; WS subprotocol `qmx.pair.<proof>`; stored in memory + `sessionStorage` |
| **Daemon-internal bind** | `principal_class=operator` + `pairing_record_id` (no `credential_ref` on browser sessions) | Daemon only, after table match | **Never sent** as login. Not stored in the page. Journal identity is `pairing_record_id`. |
| **Provider / adapter** | Allowlisted `cred://models\|inference\|compute\|sandbox\|corpus\|knowledge\|telemetry/` | Credential Broker exact-ref resolve (adapter layer only) | Never a login. UI may later collect a value into OS store as a **ref**; daemon never sees the secret |

Allowlist is code in `qma-core` (L34 / DEC-0323). UI must not offer `cred://venue|broker|exchange|trading-node|platform-registry/`. Pasting a provider ref into the wire as if it were operator proof is refused.

Browser UI authenticates as **`operator` only**. `machine` is for workers / dial-out. A page presenting `principal_class=machine` is `POLICY_REJECTION`.

### 5.3 Unauthenticated pairing HTTP (how the browser obtains the proof)

Browser JavaScript cannot read Windows Credential Manager and must not paste secrets. Pairing is the v1 bridge. It is **HTTP POST on the daemon origin**, not a CT-40 family, and not an unauthenticated WebSocket.

1. Operator opens the SPA on its **static origin** (dev or file server), not on `:8765`.
2. SPA probes daemon-origin reachability (`127.0.0.1:8765` or the recorded HTTPS remote). If the daemon is down → disconnected setup (section 8). Probe does not open CT-40.
3. If this tab has no unexpired `pairing_proof` in memory/`sessionStorage`, SPA `fetch` **POST `/pair/start`** with `credentials: 'omit'`. The browser sends `Origin` (the static origin). Daemon records a pending pair (short code + expiry) for that Origin. Response is JSON `{code, expires_at, pending_id}` — not a session, not a `Set-Cookie`, not a `credential_ref`. Pairing HTTP refuses issue until first operator exists and pairing TTL is set (backend-delta AD-17).
4. UI shows the code (setup chrome, not a secret form).
5. Operator confirms the code on the privileged door: **`qmb host pair <code>`** (same host group as start/status/stop; also **absent** at inspect). Interim until that verb exists: confirm in the daemon’s operator-visible pending-pair record **through QMB host-control**, never by typing a secret into the browser. QMB confirm **stores** the bind (Origin → operator principal); QMB does not become a second grant store. Confirm does **not** open the authenticated wire and does **not** issue the browser proof.
6. SPA **POST `/pair/confirm`** (`credentials: 'omit'`, same Origin, `pending_id`). Before QMB confirm: pending, no proof, no CT-40. After confirm: JSON `{pairing_record_id, pairing_proof, expires_at}` **once**. Retry of the same pending is `already_issued`. **Issuance rule (backend-delta AD-3):** a remembered Origin never issues a session. New proofs require this QMB-confirmed pending path **or** authenticated `POST /pair/renew`. Renew **rotates**: new proof, old proof revoked, old WS closed.
7. Browser stores `pairing_proof` (and may store `pairing_record_id`) in **memory and `sessionStorage` for that tab**. It does not store a `credential_ref`. It does not write `localStorage`. It does not accept a cookie.
8. Then authenticated CT-40 (section 5.4): HTTP GET with Bearer, WebSocket with subprotocols, then `initialize` (section 6).

**CORS on `/pair/start` and `/pair/confirm`:** reflect the requesting `Origin` so the SPA can POST (cross-origin; static origin ≠ daemon origin). Methods POST (+ OPTIONS preflight). `Access-Control-Allow-Credentials` is **false**. `Authorization` is not required on these two paths. Authenticated routes (section 5.4) do **not** use this open reflect: they allow **only** the paired origin.

**Possession of an arbitrary `cred://…` ref is not operator proof.** A stolen or guessed provider ref, or a ref copied from docs, does not bind an origin and is not a `pairing_proof`. Confirmation is a human act on the QMB host-control door. First operator is minted on `qmb host start` of an empty `QMA_DAEMON_ROOT` (backend-delta AD-17), before any pairing HTTP.

**`pairing_proof` is a bearer credential** ([RFC 6750 §1.2](https://datatracker.ietf.org/doc/html/rfc6750#section-1.2)): possession authorizes. It is **not** a nonsecret label. Do not put it in journals, traces, diagnostics, or query strings. Pairing code is a challenge identifier. Provider values never appear on those surfaces. Confirm returns the proof **once**; a lost response requires re-pair.

**Must not:** open a WebSocket to deliver the pairing code; send family messages (`initialize`, commands, queries, `wire.attach`) on an unpaired connection; treat `/pair/*` success as `initialize`; `Set-Cookie`.

Remote pairing: same HTTP POSTs against the recorded host over HTTPS. The pairing record is **that** daemon’s origin bind. A loopback pairing does not authorize a remote host, and vice versa. After pairing, that host is spoken as `https://` + `wss://` only.

### 5.4 One proof, two transports (cookies refused)

After `/pair/confirm` returns `{pairing_record_id, pairing_proof, expires_at}` once, every authenticated call presents **that same `pairing_proof`**. HTTP and WebSocket are different TCP connections. There is **no** shared cookie jar and **no** requirement that they share one in-memory `AuthenticatedWireSession` object across transports. Each request/connection proves the proof; the daemon maps Origin + `proof_fp1` to the operator principal + `pairing_record_id`.

| Family | Transport | Proof (v1) |
| --- | --- | --- |
| Queries | HTTP GET snapshots (authoritative) | Request header `Authorization: Bearer pairing:<proof>` **and** `Origin` equal to the paired static origin |
| Commands / events | JSON-RPC 2.0 WebSocket (`ws://` loopback, `wss://` otherwise) | WHATWG `new WebSocket(url, ["qmx.ct40.v1", "qmx.pair.<proof>"])` |

**HTTP GET.** CORS: `Access-Control-Allow-Origin` is the **exact** paired static origin (not `*`, not a reflect-any after pair). `Access-Control-Allow-Headers` includes `Authorization`. `Access-Control-Allow-Credentials` is false. Fetch uses `credentials: 'omit'`. Other origins: refuse. Preflight failure is not a retarget. Loopback may use `http://` (local AD-12). Non-loopback requires HTTPS. Do not put `pairing_proof` in the query string.

**WebSocket.** Browsers **cannot** set an `Authorization` header on `WebSocket`. That is why the proof is a subprotocol, not a header-or-cookie fork.

```js
const ws = new WebSocket(url, ["qmx.ct40.v1", "qmx.pair." + pairingProof]);
```

Client offers **both** tokens. WHATWG lets the server echo **one** selected protocol. The daemon **inspects the offered list**, requires `qmx.ct40.v1` and a `qmx.pair.<proof>` whose proof matches the pairing table **together with the `Origin`**, then echoes `qmx.ct40.v1`. Missing, malformed, expired, or origin-mismatched `qmx.pair.<proof>` → **refuse the upgrade**. No CT-40 bytes, no `initialize`. Access logs and traces redact `qmx.pair.*` values.

**Cookies are refused.** Daemon must not `Set-Cookie` on `/pair/start`, `/pair/confirm`, queries, or the WebSocket handshake. A `Cookie` header is **not** operator proof. Implementations must not accept “header or cookie.”

**Origin + `proof_fp1` must match the pairing table.** A valid proof presented from a different Origin is refused. A guessed Bearer without a table row is refused. A provider `cred://` in `Authorization` is refused.

No REST `/invoke`. No UI BFF.

### 5.5 Tab storage, second tab, same-tab restart

| Store | v1 |
| --- | --- |
| Memory | Live tab holds `pairing_proof` (and may hold `pairing_record_id`; plus that tab’s `producer_id` after `initialize`). |
| `sessionStorage` | Same tab: survives reload of **that** tab. Restores `pairing_proof` (and `producer_id` if already assigned). |
| `localStorage` | **Forbidden** for this proof. |
| IndexedDB / other durable web stores | **Forbidden** for this proof. |
| Cookie | **Forbidden** for this proof. |
| Provider `cred://` | **Forbidden** as login. |

`sessionStorage` is **per-tab**. A second tab on the same static origin does **not** see the first tab’s id. The operator does not paste the id.

**Second tab (typed URL / empty `sessionStorage`):** POST `/pair/start` again (new `producer_id` always). Show a code and require `qmb host pair` as in 5.3. A remembered Origin **does not** auto-approve and **does not** issue a `pairing_proof`. Backend-delta AD-3: issuance is fresh QMB confirm of **that** pending request, or `POST /pair/renew` presenting an existing unexpired unrevoked proof. Cloned/auxiliary tabs that copied `sessionStorage` already have proof; they reconnect or renew; they do not use the Origin-only path.

**Same-tab restart (reload):** `sessionStorage` restores `pairing_proof`. Skip `/pair/start`. Reconnect with Bearer + WS subprotocols until expiry. Expiry **closes** the WS. Reuse that tab’s `producer_id` from `sessionStorage` (local AD-11 / AD-24). New tab ⇒ empty `sessionStorage` ⇒ new `producer_id` at `initialize`.

Expired / revoked id in `sessionStorage`: drop it, then `/pair/start` again. Do not reuse a dead id. Do not fall back to unauthenticated loopback (`registry:proxy.allow_unauthenticated_loopback` is the **model proxy**, not the UI wire).

### 5.6 Reconnect vs re-pair

Reconnect (local AD-11 / parent AD-29) is a **query path**: same unexpired `pairing_proof` for that tab, daemon re-maps Origin + `proof_fp1` to operator principal + `pairing_record_id`, `initialize` with the **same** `producer_id` for that tab, snapshot queries (Bearer), `product_session.reconnect(resume_cursor, cursor_generation)`, `wire.attach(scope, since_seq)`, `JobHandle.reattach`. It does **not** replay intent, resubmit unacked commands, or imply approval.

Expired / revoked pairing → POST `/pair/start` again. Do not reopen an unauthenticated family wire.

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
  B->>D: probe HTTP reachability
  B-->>U: disconnected + Start local (setup)
  U->>Q: qmb host start<br/>(or interim python -m qma.daemon)
  Q->>D: set QMA_DAEMON_ROOT, spawn process entry
  D->>D: acquire .daemon_writer, bind 8765; empty root mints operator + host_control
  Q-->>U: status running
  U->>Q: qmb host configure pairing-ttl
  Q->>D: host-control writes registry:pairing.session_ttl
  B->>D: POST /pair/start (Origin, credentials omit)
  D-->>B: code + pending_id (no session, no cookie)
  B-->>U: show code
  U->>Q: qmb host pair CODE
  Q->>D: confirm pending over host-control (Origin → operator principal)
  B->>D: POST /pair/confirm
  D-->>B: pairing_record_id + pairing_proof once
  B->>B: memory + sessionStorage of proof (not localStorage, not cookie)
  Note over D: map Origin + proof_fp1 → operator principal + pairing_record_id
  Note over C: broker is not the login; pairing table is
  B->>D: WebSocket(url, ["qmx.ct40.v1", "qmx.pair.<proof>"])
  D-->>B: upgrade (echo qmx.ct40.v1) or refuse
  B->>D: initialize {protocolVersion, capabilities, producer_id?}
  D-->>B: protocolVersion, capabilities, producer_id
  B->>D: HTTP GET Authorization Bearer pairing:<proof> + Origin
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
1. **Start.** Operator runs `qmb host start` (when it exists) **or** the interim recipe. QMB/recipe sets `QMA_DAEMON_ROOT`, starts `python -m qma.daemon`. Empty root mints first operator principal + `host_control`. Lock + bind succeed or typed refusal.
2. **Connect.** SPA discovers `127.0.0.1:8765` (or recorded remote) by HTTP reachability. Does not retarget. Does not open CT-40 yet. Pairing HTTP still refuses issue until TTL is set.
2a. **Configure TTL.** Operator runs `qmb host configure pairing-ttl` over host-control. Missing TTL refuses `/pair/confirm` issue.
3. **Pair.** POST `/pair/start` → operator confirms in QMB (`qmb host pair`) → POST `/pair/confirm` → `pairing_proof` in memory + `sessionStorage` (once). No family-wire challenge. No cookie. No `cred://` login.
4. **Authenticate.** Each HTTP GET and each WebSocket presents that proof. Daemon maps Origin + `proof_fp1` to operator principal + `pairing_record_id` **before** protocol bytes. Secrets absent. Arbitrary `cred://` refused.
5. **Initialize.** JSON-RPC `initialize` (`WIRE_PROTOCOL_VERSION = "1.0.0"`) on the authenticated WebSocket. Server assigns or echoes a stable per-tab `producer_id`. Store it in that tab’s `sessionStorage`.
6. **Query.** HTTP GET snapshots (listing, `product_session`, health cards) with `Authorization: Bearer pairing:<proof>` and paired `Origin`. CORS = that exact origin.
7. **Attach (optional).** `wire.attach(scope, since_seq)` for events on the authenticated WS. Events are not authoritative.
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
| **Daemon down** | Probe `none`. Shell disconnected. Start local = setup / `qmb host start`. Headless `qmb` still works. | Spawn from JS. Block all chrome behind a modal forever. Paint `starting`. |
| **Second instance** | New process fails `.daemon_writer` (and/or port 8765). `qmb host start` reports already-running or typed lock refusal. UI stays on the live daemon if it can pair. | Two sqlite writers. UI “force start”. Delete the lock from the browser. |
| **Bad origin** | Origin not the paired static origin → CORS refuse and/or pairing-table mismatch. No initialize. | `Access-Control-Allow-Origin: *` on authenticated routes. Serving the SPA from 8765 to “fix” CORS. |
| **Pairing before confirm** | POST `/pair/confirm` stays pending. No `pairing_proof`. WS upgrade without `qmx.pair.<proof>` refused. | Pairing challenge on a WebSocket. Unauthenticated `initialize`. |
| **Expired / revoked pairing** | Drop `sessionStorage` proof. POST `/pair/start` again. Queries and WS drop. Expiry **closes** the WS. | Treat leftover proof as operator. Cookie fallback. Unauthenticated loopback fallback. |
| **Second tab** | Empty `sessionStorage`. POST `/pair/start`. Fresh QMB confirm of that pending request before any `pairing_proof`. New `producer_id`. | Origin-only auto-approve. Inherit first tab’s proof via `localStorage` or cookie. Paste the proof. Share a **live** `producer_id`. |
| **Same-tab reload** | `sessionStorage` restores `pairing_proof` (and `producer_id`). Reconnect until expiry. | Force a new pair on every reload while unexpired. Persist the proof in `localStorage`. |
| **Lost confirm response** | Proof already minted and hashed; retry is `already_issued`. Client re-pairs (`/pair/start`). | Retrieve raw proof from journal or status. |
| **Cookie presented** | Ignore as proof. If daemon ever `Set-Cookie` on `/pair/*`, that is a spec miss — refuse to treat it as login. | Header-or-cookie fork. `SameSite` session cookie. |
| **Arbitrary `cred://` pasted** | Not a pairing table row → refuse. | Broker-resolve as login. `Authorization: Bearer cred://…`. |
| **Remote disconnect** | Target stays the recorded remote. Chrome: reconnecting → unavailable. Jobs on that host unchanged by tab state. | Silently switch to `127.0.0.1:8765`. Invent local success. |
| **Remote never recorded** | Connect-remote is an explicit operator entry. Empty record ≠ local. | Implicit last-known-good local. |
| **Protocol / byte drain (today)** | At inspect the listener discards bytes. UI must show backend-incompatible / not-ready, not a blank “connected”. | Pretend initialize succeeded against the stub. |
| **Close browser** | `wire.detach`. JobHandles unchanged. Daemon keeps running. Tab `sessionStorage` is gone with the tab. | Cancel, `qmb host stop`, QMN drain. |
| **`qmb host stop`** | Local daemon drain + lock release. Local env JobHandles may become `unknown` (operator resolves). QMN/remote work continues. Pairing table dies with that process unless persisted by the daemon. | Call this on tab close. Paint `unknown` as `failed` or `cancelled`. |
| **Laptop sleep / GAP-0062** | Daemon on the laptop dies with the machine. Do not promise lid-closed continuation. | Splash copy that work continues offline. |

## 8. Lifetime: close, stop, cancel, remote

| Act | Owner | Effect |
| --- | --- | --- |
| Close tab / window | UI | `wire.detach`. Chrome gone. That tab’s `sessionStorage` gone. |
| Stop local runtime | QMB `qmb host stop` | Stops host-supervised **local** daemon only. |
| Cancel work | `JobHandle.cancel` only (local AD-13) | Coordinated cancel; first durable terminal wins. |
| Stop QMN / remote | Node powers / that environment’s door | Never implied by UI close or local host stop. |

Docker workers on the workstation die with the local daemon. That is not QMN. Local proxy (model plane) is outside QMA; host stop does not stop it.

## 9. Second tab and `producer_id`

| Axis | Rule |
| --- | --- |
| Origin / daemon | Same static origin, same daemon process. SPA origin ≠ daemon origin. |
| Pairing | **Not inherited via `sessionStorage` on a typed-URL tab.** That tab POSTs `/pair/start` and needs fresh QMB confirm. Origin match is required and never sufficient. A cloned tab that copied `sessionStorage` already holds proof. Operator pastes nothing. |
| `producer_id` | **New** per UI process (browser tab / window). Stable across **that** tab’s reloads and reconnects via `sessionStorage`. Initialize may hint; server assigns if empty. Sharing one `producer_id` across tabs is forbidden (local AD-24). |
| `psess:` | Same row if the operator selected the same session. Two tabs of one `psess:` share the server row (local AD-4). Closing a tab writes nothing. |
| Wire `id` | Unique per `(producer_id, id)`. |
| Product-session `command_id` | Unique across all surfaces sharing `(psess, principal)` (parent AD-29). Distinct from wire `id` and invoke `idempotency_key`. |

This companion does not invent a cross-tab producer coordinator and does not use cookies or `localStorage` to share pairing. New tab ⇒ new producer. Command ids stay globally unique at the session layer so two tabs cannot collide payloads.

## 10. Owners

| Concern | UI (`apps/qmx-ui`) | QMB CLI | qma-daemon | Credential Broker |
| --- | --- | --- | --- | --- |
| Serve SPA | Consumes static origin | No | **No** (not on 8765) | No |
| Start / status / stop local daemon | Setup screen only; never spawn | **`qmb host *` (add)** | Process entry `python -m qma.daemon` | No |
| `QMA_DAEMON_ROOT` | Must not pick a cwd root | Sets on start | Reads env; opens substrate | No |
| Sole-writer lock | No | Surface refusal on start | **`.daemon_writer`** | No |
| Pairing bootstrap | POST `/pair/start` + `/pair/confirm`; shows code; stores `pairing_proof` in memory + `sessionStorage` | **`qmb host pair` (add, host-control)** | Stores Origin↔operator bind + issues `pairing_proof` **once**; journals `pairing_record_id` + `proof_fp1`; **no cookie** | No |
| Authenticated HTTP GET | `Authorization: Bearer pairing:<proof>` + Origin; `credentials: 'omit'` | No | Pairing-table check; CORS exact paired origin (**add**); redact Authorization in logs | No |
| Authenticated WebSocket | `new WebSocket(url, ["qmx.ct40.v1", "qmx.pair.<proof>"])` | No | Inspect offered subprotocols; echo `qmx.ct40.v1`; refuse bad pair; redact `qmx.pair.*` | No |
| `credential_ref` / `authenticate_before_protocol` | **Does not send** a ref as login | No | Browser session: operator + `pairing_record_id`, **no** `credential_ref`. Machine clients still present a ref. | Shape is CredentialRef for machines; **not** browser login |
| Provider secrets | Write-once OS helper is a later native/QMB path; v1 browser does not hold values | Operator CLI for host, not a secret form | Never receives values | Exact-ref resolve, adapter layer only |
| `initialize` / `producer_id` | One producer per tab; persist in `sessionStorage` | No | Assigns / echoes | No |
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
| `authenticate_before_protocol` | Shape gate; does **not** call broker; not on the listener | reuse types; **add** wire-up that maps Origin + `proof_fp1` then fills operator + `pairing_record_id` | COMP-QMA-WIRE + DAEMON |
| Credential Broker | Exact-ref; WinCred `_reader` **uninjected** in `DaemonProcess.compose` | reuse types; **hole** OS read | COMP-QMA-DAEMON |
| `initialize` / families | Types + schemas; `websockets` **zero imports** | reuse contract; **add** JSON-RPC WS + HTTP GET server | COMP-QMA-WIRE + DAEMON |
| HTTP POST `/pair/start`, `/pair/confirm` | **Absent** | **add** (unauthenticated bootstrap only) | COMP-QMA-DAEMON |
| CORS / origin allowlist | **Absent** | **add** | COMP-QMA-DAEMON |
| Pairing table (`proof_fp1` → Origin + operator principal + `pairing_record_id`) | **Absent** | **add** | COMP-QMA-DAEMON (store) + COMP-QMB (host-control confirm) |
| `Authorization: Bearer pairing:<proof>` | **Absent** | **add** | COMP-QMA-DAEMON |
| WS subprotocols `qmx.ct40.v1` + `qmx.pair.<proof>` | **Absent** | **add** | COMP-QMA-WIRE + DAEMON |
| Cookie session | **Must not ship** | forbidden | — |
| `qmb host start\|status\|stop\|pair` | CLI groups: `backtest`, `data`, `optimize`, `sweep`, `robustness`, `ledger`, `library`, `analysis`, `config`. **No `host`.** | **add** | COMP-QMB |
| SPA / `apps/qmx-ui` | **Absent** | **add** (UI stream) | this sitting’s host, later |
| Tauri sidecar supervisor | **Absent**; official v2 has no health/restart API (research/17) | deferred | later desktop; still calls QMB verbs |
| Serving UI from 8765 | Must not ship | forbidden | — |
| Sixth COMP / second orchestrator | Forbidden | forbidden | — |
| Unauthenticated family-wire pairing challenge | Must not ship | forbidden | — |

Live CT-40 server remains a **backend prerequisite** (CHANGE-IMPACT, local AD-16). This companion does not claim it shipped.

## 12. `qmb host` contract (named add)

Absent at inspect. When added, thin QMB door over daemon process lifetime — not a new runtime, not `import qma.daemon` into every QMB run.

| Verb | Does | Does not |
| --- | --- | --- |
| `qmb host start` | Set `QMA_DAEMON_ROOT` to the per-user path; spawn `python -m qma.daemon` if lock free; wait until bind or already-running; on empty root mint first operator principal + `host_control` | Orchestrate Missions; grant ops; start QMN; issue a pairing proof |
| `qmb host status` | Lock, pid, bind, operator-established, TTL set/unset, pairing pending/bound **record ids** (never proofs) | Enumerate Credential Manager; paint SPA `starting`; print `pairing_proof` |
| `qmb host stop` | Stop the local daemon; release lock | Cancel QMN/remote; `JobHandle.cancel` for every job (local handles may go `unknown`) |
| `qmb host configure pairing-ttl` | Write `registry:pairing.session_ttl` over host-control. Required before first issue | Invent a duration in this sitting |
| `qmb host pair <code>` | Confirm pending `/pair/start` for that Origin over host-control. After this, POST `/pair/confirm` returns `{pairing_record_id, pairing_proof, expires_at}` **once**. A second tab on the same Origin still needs its own pending code and this confirm. Authenticated `POST /pair/renew` (existing valid Bearer) is the other issuance path; Origin-only auto-approve is refused. | Accept a provider secret; bind a non-matching origin; set a cookie; open CT-40 for the browser; issue a session because Origin was remembered; return a second proof on retry |
| `qmb host pair revoke --session\|--origin` | Revoke that record or that Origin’s earlier sessions and unclaimed pendings; close matching WS | Delete journal history |

Until these verbs exist, status is operator-visible via OS process list + the setup screen’s probe, and pair confirm has **no** product door — the UI must not fake a paired session.

## 13. Tauri (later, not v1)

v1 does not wait on Tauri (local AD-12). Research/17: Tauri 2.11.6 can wrap the same static SPA and spawn a sidecar, but has no official daemon supervisor; Rust command IPC is **not** qma-wire.

When a desktop shell ships:

- Same SPA origin rules inside the webview (or the webview origin is the paired origin).
- Privileged start/stop **calls `qmb host start|status|stop`** (or equivalent QMB library door). Sidecar spawn is a **caller** of that door, not a second owner.
- Pairing proof stays `pairing_proof` (Bearer + WS subprotocols). Not a cookie. Not a Tauri-injected `cred://`. Journal identity is `pairing_record_id`.
- Close window = detach, same as the browser, unless the operator chose Stop local runtime.
- Do not make the daemon a child of the window job object such that close kills workstation work by default.

## 14. Tests (all **unexecuted**)

Intended classes only. None were run in this sitting. Reticle `unknown` is not a pass. Installed-product proof is not Reticle-only.

| Class | Intent |
| --- | --- |
| Contract | Pairing table matches Origin + `proof_fp1` → operator principal + `pairing_record_id`; arbitrary `cred://` refused; cookies ignored; secrets and raw proofs on surfaces refused (`auth.py` already unit-tests shape). |
| Bootstrap HTTP | Unpaired POST `/pair/start` does not authenticate CT-40; `/pair/confirm` before QMB confirm returns pending; after confirm returns `pairing_proof` once and no `Set-Cookie`; retry is `already_issued`. |
| Transports | HTTP GET without `Authorization: Bearer pairing:<proof>` refused; WS without `qmx.pair.<proof>` in the offered list refused; WS constructor is subprotocols, not an Authorization header. |
| Process | Second `python -m qma.daemon` on the same `QMA_DAEMON_ROOT` hits `.daemon_writer`; `qmb host start` is idempotent when live. |
| Browser | SPA origin ≠ 8765; CORS denies a second origin on authenticated GET; storage is `sessionStorage` not `localStorage`; close tab does not emit cancel. |
| Second tab | Empty `sessionStorage` → `/pair/start` → QMB confirm → `/pair/confirm` yields a `pairing_proof`; Origin-only auto-approve refused; new `producer_id`. Cloned tab with copied proof reconnects; new `producer_id` if the old is live. |
| Same-tab reload | Restored `pairing_proof` reconnects until expiry; `producer_id` reused. |
| Failure | Daemon down → disconnected; remote drop does not probe loopback as success; expired pairing re-starts `/pair/start`. |
| Installed product | Launch outside checkout with `QMA_DAEMON_ROOT` set; recipe/QMB start; pairing; initialize. **Unexecuted.** |

## 15. Citations

- Parent AD-21 — headless door parity; QMB is the only operator CLI; a log/progress panel is not a general shell. `_bmad-output/planning-artifacts/architecture/architecture-QMX-2026-09-18/ARCHITECTURE-SPINE.md`
- Local AD-19 — QMB host owner; unauthenticated `/pair/start` + `/pair/confirm`; one proof `pairing_proof`; HTTP Bearer; WS subprotocols; cookies not the proof; daemon maps to operator principal + `pairing_record_id`. `ARCHITECTURE-SPINE.md` in this sitting
- CT-40 `auth.py` — `authenticate_before_protocol`, `AuthenticatedWireSession`, `FORBIDDEN_SECRET_SURFACE_KEYS`. `.worktrees/integration-inspect/qmx-agents/packages/qma-wire/src/qma/wire/auth.py`
- `listener.py` — loopback default; unauthenticated / plaintext non-loopback hard refusal. Same inspect tree.
- `initialize.py` — JSON-RPC `initialize`, `WIRE_PROTOCOL_VERSION = "1.0.0"`, `producer_id`. Same inspect tree.
- `__main__.py` / `process.py` / `persistence/lock.py` — process entry, bind 8765, byte drain, `.daemon_writer`.
- QMB CLI tree — no `host` group. `.worktrees/integration-inspect/qmb/src/qmb/doors/cli/tree.py` `COMMAND_GROUPS`
- WHATWG WebSocket — `new WebSocket(url, protocols)`; browsers cannot set `Authorization` on the handshake; server selects one echoed subprotocol
- research/14 — first-run, `QMA_DAEMON_ROOT`, close≠stop, Option A/C lifetime, CredRead hole
- research/17 — browser lacks native spawn/fs/secrets; Tauri sidecar is not a supervisor; QMX does not require Tauri
- Codex `workroom/qmx-ui-review-2026-09-23/REVIEW.md` **R2** — name one v1 bootstrap owner; sequence; owners; backend changes; do not force Tauri or a second orchestrator
- Local AD-2, AD-11, AD-12, AD-13, AD-16, AD-24 — static origin, probe, Python runtime, close/stop/cancel, backend add for live protocol, one `producer_id` per tab

## 16. What this file does not do

- Spine AD-19 is the matching law; this companion details it. It does not re-open layouts or mint a sixth COMP.
- Does not implement pairing, `qmb host`, or a live wire server.
- Does not choose OpenCodex as a vendor login.
- Does not promise GAP-0062 always-on, GAP-0058 single-machine node, or GAP-0070 computer-use.
- Does not treat inspect types as e2e.
- Does not accept cookies, `localStorage`, or a pasted `cred://` as the v1 proof.
