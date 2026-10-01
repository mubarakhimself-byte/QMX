---
lens: rubric-walker
target: ARCHITECTURE-SPINE.md (architecture-QMX-UI-BACKEND-2026-09-24, status draft)
altitude: feature
paradigm: Privileged-door daemon with named pairing bootstrap
reviewer_gate: good-spine checklist (references/reviewer-gate.md)
date: 2026-09-24
parent: architecture-QMX-2026-09-18 AD-1..AD-31
kit: architecture-QMX-2026-09-23 AD-1..AD-9
qma: architecture-QMA-2026-08-28
ui: architecture-QMX-UI-2026-09-23 AD-1..AD-24
inspected: integration@34c148be404a375cbfd79fd4ce6997452e4f1d20 via .worktrees/integration-inspect
lint: not re-run by this walker; local AD-1..AD-16 each carry Binds/Prevents/Rule and a provenance tag ([USER]/[CANDIDATE]/[INHERITED]); no template placeholders observed
---

# Rubric walker — QMX UI backend-delta

Verdict: **fail**. The sitting names the right paradigm and closes the forks that would have minted a sixth COMP, a new CT, a UI BFF, REST invoke, Origin-only session issuance, cookies as login, or `copilot_profile` nested in PackUiRequest. Assignment coverage is present as *topics* (pairing, QMB host door, mailbox delivery owner, cancel, PUT+pull transfer, pack-UI ingest, drafts, credentials, compat). It does not pass the enforceability bar: AD-5’s unauthenticated “only” list uniquely forbids the CORS OPTIONS a cross-origin SPA needs for AD-9 PUT and `/pair/renew`; AD-14 cold-start uniqueness is not bound against durable browser stores plus AD-3 path-2 renew; pairing/artifact numbers and the transfer-ticket fold this sitting owns are either Deferred without a holding rule or missing from the spine. Those three let the next layer fork on browser admission, whether closed-tab requires QMB, and pairing/upload persistence. Named tech is inherited with inspect honesty (CPython 3.14; RFC-9110/RFC-6455/WHATWG citations real). Brownfield is ratified, not copied. Named parent amendments AM-01..AM-10 are the right *form*; AM-03 is incomplete for transfer tickets. Operator has not accepted.

Altitude: feature (keeps epics). Parents inherited by original ids (`parent AD-n` / `kit AD-n` / `QMA AD-n` / `UI AD-n`). Local AD-1..AD-16 each have Binds/Prevents/Rule. No template comments. Companions are coverage context only; this walk judges `ARCHITECTURE-SPINE.md`.

## Checklist

| Bar | Result |
| --- | --- |
| Fixes the real divergence points for the level below and misses none | **Fail** — sixth COMP / new CT / Origin-only issuance / cookie login / REST invoke / mailbox “Epic 41 only” / `stop_run` as cancel / hash-as-possession / `ui_view` point are named. Misses this sitting’s own bridges: CORS OPTIONS vs AD-5 carve-out; pairing-proof storage home vs AD-3 renew; pairing HTTP JSON + `list_mailbox` GET path; TTL / stage cap / transfer-ticket fold |
| Every AD's Rule is enforceable and actually prevents its stated divergence | **Fail** — AD-1/AD-2/AD-7/AD-8/AD-10/AD-12/AD-16 Prevents hold. AD-3 Origin-never-sufficient holds. AD-5 “only start/confirm OPTIONS” prevents the preflight AD-9/AD-15 require. AD-14 cold-start does not uniquely refuse `localStorage` + `/pair/renew`. AD-9 has no max-bytes rule on the spine. AD-6 revoke CLI is not one string |
| Nothing under Deferred could let two units diverge | **Fail** — Tauri, partial PUT, QR, envelope crypto, ASGI class (with “must speak the named HTTP+WS contract”) hold. Numeric pairing TTL is Deferred with **no holding rule**, so two pairing stories pick 15m vs 7d vs revoke-only. `registry:artifact.stage_max_bytes` and pending-code expiry are not on the spine Deferred table at all |
| Named tech is verified-current | **Pass with Low wording** — CPython **3.14** inherited; python.org Latest is **3.14.7** (2026-09-24); spine’s “observed 3.14.6 at parent freeze” is inspect-honest, not a pin. RFC 9110 (June 2022) §14.5 is Partial PUT. RFC 6455 §10.1 Origin spoofing by non-browsers still holds. WHATWG WebSockets still selects one echoed subprotocol. HTML Web storage living standard snapshot **2026-09-22** matches the sources row. No new frontend pin. ASGI/`websockets` class correctly unpinned |
| Ratifies rather than contradicts brownfield | **Pass** — `DaemonProcess._handle_client` discards TCP bytes; `send_message` in `WireCommand`; `list_mailbox` / `cancel_job` / `transfer_artifact` / `/pair/*` / `qmb host` **absent**; Envelope has no `product_session_id`; JobHandle has `later_commands` and no `originating_psess`; `COMMAND_GROUPS` has no `host`; pairing table absent. Spine names those as connect/amend, not e2e (DEC-0286 / AD-2) |
| Covers the assignment (daemon, wire, QMB host, mailbox, cancel, artifact channel, pack-UI, drafts, credentials, compat) | **Partial** — each topic has an AD. Unique implementation of CORS/preflight, proof storage, pairing JSON, GET snapshot paths, TTL/cap, and transfer-ticket fold waits on H-1..H-3 |
| Inherited parents not weakened | **Partial** — no local AD claims a sixth COMP, new CT, UI grant store, cookie session, or `ui_view` point. AM-01..AM-10 name the real conflicts. AM-03 omits transfer tickets (companion-only fold vs QMA AD-6 “new fold is a spine amendment”). Internal pairing `CredentialRef` vs QMA AD-24 broker allowlist is mapped, not uniquely bound. AD-13 `stage_artifact` capability can be read as a JSON-RPC command AD-9/AD-15 forbid |
| Every owned dimension decided, deferred, or open — especially ops envelope | **Partial** — process lifetime (AD-6), loopback vs recorded TLS (inherit Story 41.4 + ops paragraph), backup (QMA AD-27), Tauri (Deferred), SPA origin ≠ 8765 (AD-15) are placed. Pairing TTL, PUT cap, pending-code expiry, Linux data-root on the spine, CORS OPTIONS, and proof-storage home are neither uniquely frozen nor held in Deferred/Open questions. Open questions says “None blocking” while those sit owned and unfrozen |

## What works

Paradigm is a real contract: **privileged-door daemon with named pairing bootstrap**, not a sixth COMP, not a UI BFF, not REST invoke, not Origin-as-identity.

- **Inherited table** binds parent AD-1..AD-31, kit AD-1..AD-9, QMA AD-5/6/8/17/20/21/24, UI AD-1..AD-24 read-only. Conflict examples (sixth COMP, new CT, UI grant store, cookies as login, Origin-only issuance) are named as conflicts. Kit/UI amendments (`caller_kind`, optional authoring `app_instance_id`, `selected_refs` kind `instance_id`, `PluginManifest.copilot_profile`) are reused, not re-authored.
- **AD-1 / AD-2 / AD-16** keep this sitting backend-delta only; planned stories are requirements; inspect types are not e2e; mailbox delivery is Epic 46.4; adds are closed-and-addable names on `qma-wire`, journal projections on `qma-daemon`, and QMB CLI verbs.
- **AD-3** uniquely refuses Origin-only issuance. Negative trace (known Origin, no proof, no QMB confirm → no token, no CT-40) and two positive paths (fresh QMB confirm; authenticated renew) are named. That is the remaining UI R2 condition, and the Rule itself holds.
- **AD-7** uniquely splits owners: `send_message` seed vocab (Epic 41), durable Envelope (Story 46.4), journal/fold (Epic 42), additive `product_session_id` (AM-02). Collision law (same pair + hash vs different hash) is unique. Missing query is `query_unavailable`, not empty chat.
- **AD-8** uniquely adds `cancel_job` fields and immutable `originating_psess` at admit; states stay closed; `queued`→`running` does not invalidate `command_id`; `unknown` is not cancellable; not `stop_run`.
- **AD-10 / AD-11** keep PackUiRequest a request DTO, `copilot_profile` an Epic 60 sibling, `GRANT_AMBIGUOUS` on ≥2, drafts out of QMA AD-22 staging, first Run through parent AD-30 enable.
- **AD-12** keeps secrets as refs, allowlist in `qma-core` source, v1 browser select-only, broker `_reader` an adoption gap not a new broker.
- **AD-15 / AM-05** correctly refuse a fourth message family and serving the SPA from 8765. PUT is a byte channel.
- **Deferred** is the right *park* for Tauri, QR, partial PUT, envelope crypto, and ASGI class — those have holding seams. TTL does not.
- **Brownfield honesty** matches inspect `34c148be`: live CT-40 server is absent; vocabulary has `send_message` only among the new names; QMB has no `host` group.

## Findings

### Critical

None. No local Rule authorizes a sixth COMP, `qma-cli`, COMP-UI, a new CT, a UI-owned scheduler or grant store, REST invoke, cookies as login, Origin-only auto-approval, nested grant union, `ui_view` as a contribution point, or json-render as authority.

### High

#### H-1 — AD-5’s unauthenticated “only” list uniquely forbids the CORS OPTIONS (and leaves pairing HTTP JSON / GET paths unnamed) that AD-9 and AD-15 require

**Where:** AD-5 Rule (“unauthenticated HTTP **only** on `POST /pair/start`, `POST /pair/confirm`, and their `OPTIONS`”; “Every other HTTP path … still authenticates before protocol bytes”); AD-9 PUT `/artifacts/stage` with `Authorization: Bearer pairing:<id>`; AD-15 “SPA origin ≠ daemon origin”; AD-3 `POST /pair/renew` with Bearer; AD-7 `list_mailbox` as Epic 41 query; companion CORS (authenticated ACAO exact paired Origin; start/confirm reflect Origin). Fetch: PUT is not a CORS-safelisted method; a cross-origin PUT with `Authorization` always preflights; the preflight `OPTIONS` does not carry `Authorization`.

**Two conforming units (OPTIONS)**

- **Unit A — preflight works.** `OPTIONS` on `/pair/renew`, `PUT /artifacts/stage`, and authenticated GET snapshot paths is unauthenticated CORS (no session issuance, no family messages, no WS upgrade). Authenticated *methods* still require Bearer + paired Origin. Browser PUT and renew succeed.
- **Unit B — AD-5 literal.** Only start/confirm OPTIONS are unauthenticated. Preflight to PUT/renew/GET is 401/refuse. Unit B cannot implement AD-9 from the SPA AD-15 requires. A third unit widens the carve-out to “any OPTIONS on 8765” and accidentally accepts unauthenticated `initialize` or WS upgrade on a mistyped route.

**Two conforming units (pairing JSON / GET path)**

- **Unit A — closed catalogue.** `POST /pair/start` → `{pending_id, code, expires_at}`; `POST /pair/confirm` body `{pending_id}`; `POST /pair/renew` empty body + Bearer → `{pairing_session_id}`; `list_mailbox` is the addable **query name** on the existing CT-40 HTTP GET snapshot door (same pattern as `facade_search`), not a REST collection.
- **Unit B — invented wire.** Confirm requires `{code}` or `{pending_id, code}`; start puts Origin in the body; `list_mailbox` is only JSON-RPC on WS, or `GET /mailbox?psess=`. AD-14 reload lookup and J-UI-13 mismatch fork.

This sitting’s job is browser admission on the daemon origin. AD-3/AD-9/AD-15 cannot be implemented uniquely while AD-5’s “only” list and the unnamed HTTP catalogue remain.

**Action:** autofix. One closed clause under AD-5 and AD-15:

1. Unauthenticated HTTP is exactly: `POST /pair/start`, `POST /pair/confirm`, and `OPTIONS` on those two **plus** `OPTIONS` on `POST /pair/renew`, `PUT /artifacts/stage`, and the authenticated GET snapshot paths. OPTIONS never issues a session, never `Set-Cookie`, never upgrades, never accepts family messages.
2. Authenticated methods still require `Authorization: Bearer pairing:<id>` + exact paired Origin. Credentials omit. ACAO never `*`.
3. Pairing JSON (v1): start response `{pending_id, code, expires_at}`; confirm request `{pending_id}`; renew request empty body; success `{pairing_session_id}` (optional `expires_at`). No cookies.
4. `list_mailbox` is an addable **query** (AM-08) on the existing HTTP GET snapshot family (QMA AD-5 / UI AD-12). It is not a new REST collection and not a fourth family. WS JSON-RPC may carry the same query name; GET snapshot remains authoritative (companion already says this — promote it onto the Rule).

#### H-2 — AD-14 cold-start / AD-3 path-2 uniqueness is not bound to a proof-storage home

**Where:** AD-3 Rule (new `pairing_session_id` = QMB confirm **or** authenticated `/pair/renew` with an existing unexpired unrevoked id); AD-14 Rule (same-tab reload may restore from `sessionStorage`; cold start / closed tab = empty `sessionStorage`, no pairing id, new pair requires QMB); Prevents (“promising browser-restart restoration from sessionStorage”); PARENT-AMENDMENT-MAP §C (`localStorage` still forbidden) — **not restated in a local Rule**; WHATWG sessionStorage is per tab and is copied into auxiliary contexts; `localStorage` / IndexedDB survive process quit.

**Two conforming units**

- **Unit A — sessionStorage is the only browser home.** Pairing proof is never written to `localStorage`, cookies, or IndexedDB. Closed tab / full quit empties the only store → cold start → QMB confirm (AD-3 path 1). Path 2 renew is only for a still-held unexpired id (reload, cloned tab, or another live tab). T-BE-06 holds.
- **Unit B — durable proof + path 2.** Reads AD-3 literally: any unexpired id may renew. Persists `pairing_session_id` in `localStorage`. Browser restart is then authenticated renew, not QMB. AD-14’s “cold start requires QMB” becomes a slogan about `sessionStorage` while the operator session survives quit. A third unit treats cloned-tab copy as “AD-3 path 2” (mint a *new* id) vs reconnect with the *same* id — spine AD-14 says “path 2 / reconnect” as if they were one thing.

This sitting exists to close R2 and the reload/cold-start wording. Origin-never-sufficient (AD-3 first sentence) holds. The recovery uniqueness AD-14 claims does not, because path 2 makes any surviving proof sufficient and the Rule never forbids a store that survives quit.

**Action:** autofix. One closed clause under AD-3 and AD-14:

1. Browser home for `pairing_session_id` and the pending chat triple is **`sessionStorage` only**. `localStorage`, cookies, and IndexedDB are forbidden for pairing proof (promote PARENT map §C onto the Rule).
2. **Reconnect** (same id, still unexpired unrevoked) is not issuance and is not path 2. Same-tab reload reconnects. Cloned tab with copied id reconnects (existing proof) and must not bind a `producer_id` already live (UI AD-24).
3. **Path 2 `/pair/renew`** mints a **new** id for the same operator+Origin when the client already holds a valid Bearer. It does not run on cold start.
4. **Cold start** = no pairing id in any browser store → path 1 only. Never auto-resend. `list_mailbox(product_session_id)` only if the operator selects a `psess:`.

#### H-3 — Pairing/artifact persistence this altitude owns is not unique: TTL Deferred with no holding rule, PUT cap absent from the spine, transfer tickets a fold AM-03 does not name

**Where:** Deferred “Numeric pairing TTL … this sitting mints **no number**”; AD-4 `registry:pairing.session_ttl`; QMA AD-26 (every registered variable declares a **default** at implementation); AD-9 PUT with `Content-Length` required and no max on the spine; companion `registry:artifact.stage_max_bytes` (not a spine Deferred row); ARTIFACTS companion “transfer ticket (journal-projected)”; AD-4 / AM-03 projections = `pairing_pending`, `pairing_session`, `editor_draft_head` only; QMA AD-6 “A store not on this list may not be created” / “a new fold is a spine amendment”; pending rows have `expires_at` with no registry key.

**Two conforming units (TTL)**

- **Unit A — refuse-or-hold.** Until the operator fills `registry:pairing.session_ttl`, pairing start refuses **or** sessions do not time-expire (revoke-only). No hardcoded 24h.
- **Unit B — invented default.** One epic ships 15 minutes, another 7 days, another process-lifetime. Reload vs lunch-break reconnect forks. QMA AD-26 then rubber-stamps whichever default the first story registered.

**Two conforming units (PUT cap / tickets)**

- **Unit A — named projection + cap.** `registry:artifact.stage_max_bytes` is a registered AD-26 row (default closed, or missing row → refuse PUT). Transfer tickets are journal projection `artifact_transfer_ticket` (AM-03 add), not a sixth store class, not in-memory-only.
- **Unit B — silent.** No max (OOM) or 8MB vs 2GB. Transfer tickets live in RAM and vanish on restart, or become a new sqlite class AD-4 Prevents. Companion and spine disagree, so both are “conforming.”

Pending-code `expires_at` is the same hole without even a Deferred row.

**Action:** autofix.

1. **Holding rule until numbers are filled (pick one and write it):** (recommended) pairing sessions **do not time-expire** until `registry:pairing.session_ttl` is operator-set; revoke still works; pending codes expire at a closed default (**10 minutes**). PUT refuses if `registry:artifact.stage_max_bytes` is unset **or** mint default **8388608** (8 MiB) as an `uneditable` recorded constant. Do not leave “no number” as two implementers’ homework.
2. AD-4 / AM-03 projection list **adds** `artifact_transfer_ticket` (fp1, destination_placement, state, journal events). Still not a new sqlite class. Fold contract: stream `transfer.*`, ordering `journal_seq`.
3. Pending and session TTL rows are QMA AD-26 registry-homed; this sitting at least names the holding behaviour above. Put `stage_max_bytes` and pending expiry on Deferred **with that holding rule**, or freeze the defaults on the Rule.

### Medium

#### M-1 — AD-6 revoke CLI is two names

**Where:** AD-6 Rule `qmb host start|status|stop|pair|pair-revoke`; AM-10 same; HOST-LIFECYCLE / PAIRING `qmb host pair revoke --session|--origin`.

Parent AD-21 door parity is the product face. Two stories will mint `pair-revoke` vs `pair revoke`.

**Action:** autofix. One argv: `qmb host pair <code>` and `qmb host pair revoke --session <id> | --origin <origin>` (recommended, matches companion). Spine AD-6 lists `pair` including revoke subcommand, not a sibling `pair-revoke`.

#### M-2 — Internal pairing `CredentialRef` vs QMA AD-24 broker allowlist is mapped, not unique

**Where:** AD-4 row includes internal `CredentialRef`; AM-01 “daemon maps to `AuthenticatedWireSession` internally”; AD-12 allowlist `cred://models|inference|compute|sandbox|corpus|knowledge|telemetry/`; inspect `credential_allowlist.py` has no pairing/operator family; `parse_credential_ref` is a shape gate (inspect `auth.py`); companion forbids passing `pairing_session_id` to `authenticate_before_protocol`.

**Two units:** extend the broker allowlist with `cred://pairing/` (silent AD-12 weaken); inject `cred://models/…` as a dummy; or attach, at `qmb host pair`, a real operator transport ref that is **not** broker-resolved for venue/secrets (inspect tests already use `cred://operator/ui` on the wire, outside the broker allowlist).

**Action:** autofix. Pairing proof is **not** a `CredentialRef` and is **not** an allowlist add. After table match, daemon constructs `AuthenticatedWireSession` from the **operator principal + internal ref QMB wrote on the pending confirm** (HOST-LIFECYCLE already says this). That ref is transport identity, never a secret, never `cred://venue|broker|exchange`. Do not call `authenticate_before_protocol(pairing_session_id)`.

#### M-3 — AD-13 advertises `stage_artifact` as if it were a JSON-RPC command

**Where:** AD-13 capability list includes `stage_artifact`; AD-9/AD-15 PUT is the byte channel; AM-09 addable commands are `cancel_job` and `transfer_artifact` only.

**Action:** autofix. `initialize` capability `stage_artifact` means **PUT `/artifacts/stage` exists**. It is not a `WireCommand`. Missing cap → typed mismatch for Library upload, not a silent RPC.

#### M-4 — First Run “grant” is one word against parent AD-18 install ≠ grant

**Where:** AD-11 “enable that pack (parent AD-30), grant, select `instance_id`, `dispatchInvoke`”; PACK companion “grant into authoring `psess:`”; parent AD-18 / AD-30.

**Action:** autofix. Enable is not grant. First Run requires an **operator grant** of that instance into the authoring `psess:` after enable (existing grant machine). No auto-grant, no second grant store.

#### M-5 — Linux data-root and remote bind live in the companion / inherited Story 41.4, not on the spine ops paragraph

**Where:** Stack/ops: Windows `%LOCALAPPDATA%\QMX\qma-daemon` and `127.0.0.1:8765`; HOST-LIFECYCLE Linux XDG path; AD-15 “Port 8765 carries”; QMA AD-5 non-loopback = TLS + recorded config; DEPENDENCY-MAP Story 41.4.

A spine-only reader ships Windows-only root and treats remote HTTPS as still port 8765.

**Action:** autofix. One ops sentence: per-user root is Windows `%LOCALAPPDATA%\QMX\qma-daemon` and Linux `${XDG_STATE_HOME:-$HOME/.local/state}/qmx/qma-daemon`; loopback default `127.0.0.1:8765`; recorded remote is HTTPS/WSS on **its** origin (not 8765-by-law); plaintext non-loopback remains hard startup refusal (QMA AD-5 / Story 41.4). Local `qmb host stop` never stops remote; loopback pairing never authorizes a remote host (PROVIDER-AND-COMPAT already — promote).

#### M-6 — AD-4 “Values never appear in traces” vs Consistency “pairing ids are not secrets”

Ambiguous “values.” Companion allows naming `pairing_session_id` on diagnostics; forbids CredentialRef secrets and provider values.

**Action:** autofix. Traces may name `pairing_session_id` / Origin presence. They must not name pending `code` after expiry, internal `CredentialRef`, or provider secrets. Status shows id presence per origin, never refs.

### Low

#### L-1 — CPython citation is 3.14.6 (parent freeze); Latest is 3.14.7

Inherited, not a pin. CONNECT-style “3.14.7 exists and is not adopted here” would match kit L-1.

**Action:** ignore if a currency lens lands the Stack row; else one clause.

#### L-2 — Open questions “None blocking” while H-3 numbers are owned and unfrozen

Legal if H-3 lands on the Rule or Deferred-with-holding-rule. Otherwise TTL/cap belong under Open questions, not “none.”

**Action:** ignore if H-3 applied.

#### L-3 — AD-14 “AD-3 path 2 / reconnect” conflates issuance with reconnect

Companion already splits them. H-2 autofix clears it.

**Action:** ignore if H-2 applied.

#### L-4 — Local AD-n vs QMA/parent/UI AD-n

Body already says `parent AD-n` / `QMA AD-n` / `UI AD-n` when citing parents. Same citation hazard as every child sitting.

**Action:** ignore.

#### L-5 — `producer_id` on same-tab reload is implied by QMA AD-5 “unchanged across reconnects,” not restated

AD-14 restores pairing id + pending triple; pre-ack lookup uses `(producer_id, wire_id)`. If reload mints a new `producer_id` while the triple keeps the old one, lookup still works; subsequent sends use the new id. Clone already forbids a live duplicate. Not a R2 hole.

**Action:** optional one-liner under AD-14: same-tab reload may reuse the previous `producer_id` because the old connection is not live (QMA AD-5 reconnect). Clone must not.

## Dimensions owned at this altitude

| Dimension | Disposition |
| --- | --- |
| Sitting scope / no epic rewrite / no Docs Factory | AD-1 |
| Planned ≠ implemented; mailbox owner Epic 46.4 | AD-2, AD-7 |
| Pairing issuance (Origin never sufficient) | AD-3 (**H-2** storage home / path 2 vs reconnect) |
| Pairing table / projections | AD-4, AM-03 (**H-3** transfer ticket missing; **M-6** trace values) |
| Unauthenticated carve-out | AD-5, AM-01 (**H-1** OPTIONS / JSON / GET path) |
| Process lifetime / QMB host door | AD-6, AM-10 (**M-1** revoke argv; **M-5** Linux/remote) |
| Mailbox field + `list_mailbox` | AD-7, AM-02, AM-08 (**H-1** transport path) |
| Cancel + `originating_psess` | AD-8, AM-04, AM-09 |
| PUT + pull transfer | AD-9, AD-15, AM-05, AM-06 (**H-1** CORS; **H-3** cap + ticket fold) |
| PackUiRequest / GRANT_AMBIGUOUS | AD-10 |
| Draft head / first Run | AD-11, AM-07 (**M-4** grant) |
| Secrets / broker adoption | AD-12 (**M-2** internal ref) |
| Additive capabilities | AD-13 (**M-3** `stage_artifact` name) |
| Reload / clone / cold start | AD-14 (**H-2**) |
| Byte channel vs families / SPA origin | AD-15 (**H-1**) |
| No sixth COMP / no new CT | AD-16 |
| Numeric TTL / PUT cap / pending expiry | Deferred without holding rule (**H-3**) |
| Tauri sidecar | Deferred (UI AD-12) |
| Partial PUT resume | Deferred; v1 refuse holds |
| Cross-tab QR | Deferred; v1 QMB confirm holds |
| Envelope crypto | Deferred GAP |
| ASGI / `websockets` class | Deferred with contract holding rule |
| Backup / restore | inherit QMA AD-27 |
| Deployment local vs remote | ops paragraph + Story 41.4 (**M-5** spine completeness) |

## Tech currency (this walker)

Checked 2026-09-24 against primary sources. This walk does not re-pin anything.

- **CPython 3.14** — inherited. python.org “Latest: Python 3.14.7” (release notes for 3.14.6 say superseded by 3.14.7; 3.14.7 dated 2026-08-05 on the downloads index). Spine “observed 3.14.6 at parent freeze” is honest. 3.15 not adopted. No new runtime from this sitting.
- **RFC 9110** — current HTTP semantics (June 2022, STD 97). §14.5 is Partial PUT; v1 unused is a real citation, not a ghost section.
- **RFC 6455 §10.1** — Origin header is not proof of a browser; non-browser clients can send a fake Origin. Citation still holds.
- **WHATWG WebSockets** — server selects **one** subprotocol from the offered list; inspecting the offered list for `qmx.ct40.v1` and `qmx.pair.<id>` is the right reading.
- **HTML Web storage** — living standard; developer edition snapshot **2026-09-22** matches `sources`. Auxiliary browsing context copies sessionStorage; `localStorage` is the other, longer-lived store (H-2).
- **Svelte 5.57.1 / SvelteKit 2.70.3** — UI AD-2 pins, out of scope here; this sitting adds no frontend pin.
- **Default bind `127.0.0.1:8765`** — inherited QMA loopback default, still the inspect bind.

No invented library, protocol, or vanished pin. No required runtime added. ASGI class correctly unpinned.

## Brownfield

Ratified, not contradicted, against `integration@34c148be` (inspected via `.worktrees/integration-inspect`):

- `qma-daemon` `DaemonProcess._handle_client` reads and discards TCP chunks; no HTTP/WS protocol. AD-5/AD-15/AD-13 are connects of a live server, not claims it exists.
- `qma-wire` `WireCommand` includes `send_message` and `stop_run`. `WireQuery` has the seed seven plus `list_mission_hooks`, `plugin_install_preflight`, `facade_search`, `facade_get`. **No** `list_mailbox`, `cancel_job`, `transfer_artifact`. AM-08/AM-09 are real addable-registry connects (DEC-0286).
- `qma.core.ports.mailbox.Envelope` required fields match the companion honesty list; **no** `product_session_id`. AM-02 is a real field add.
- `qma.core.ports.jobs.JobHandle` has `later_commands` and **no** `originating_psess`. In-memory `JobHandleStore` exists. AM-04 is a real record add; states stay closed.
- `qmb.doors.cli` `COMMAND_GROUPS` = `backtest, data, optimize, sweep, robustness, ledger, library, analysis, config`. **No** `host`. AM-10 is a real door add, not a sixth COMP.
- `/pair/*`, pairing table, Bearer `pairing:`, WS subprotocols: **absent**. `authenticate_before_protocol` + `AuthenticatedWireSession` exist as a `credential_ref` shape gate. AM-01 is a real transport-custody amendment.
- Broker allowlist in `credential_allowlist.py` is the seven families AD-12 restates. `_reader` injection as an adoption gap is the right class (not re-verified line-by-line in `DaemonProcess.compose` by this walker; START-HERE / PROVIDER honesty is consistent with the allowlist code).
- `FORBIDDEN_SECRET_SURFACE_KEYS` includes `token` / `bearer`. Pairing ids must not be stuffed under those keys (companion). Honest.

## Spec / assignment coverage

Driving assignment: backend-delta for the reviewed UI candidate — daemon, qma-wire, QMB host door, mailbox delivery, cancel, artifact byte channel, pack-UI ingest, draft publication, credential setup, client/core compatibility. No chrome redesign. No sixth COMP. No new CT.

| Spec / bind | Spine |
| --- | --- |
| R2 Origin never issues a new pairing id | AD-3 (**H-2** storage/path-2) |
| Reload vs cold start vs clone | AD-14 (**H-2**) |
| Mailbox delivery owner Epic 46.4 | AD-2, AD-7 |
| Unauthenticated bind vs QMA AD-24 | AD-5, AM-01 (**H-1**) |
| QMB process door | AD-6, AM-10 (**M-1**, **M-5**) |
| `product_session_id` + `list_mailbox` | AD-7, AM-02, AM-08 (**H-1** path) |
| `cancel_job` + `originating_psess` | AD-8 |
| PUT `/artifacts/stage` + pull transfer | AD-9, AD-15 (**H-1**, **H-3**) |
| PackUiRequest; no `copilot_profile` move | AD-10 |
| Draft head ≠ AD-22 staging; first Run enable | AD-11 (**M-4**) |
| Secrets off the wire | AD-12 (**M-2**) |
| Additive `initialize` caps; J-UI-13/14 | AD-13 (**M-3**) |
| No sixth COMP / no new CT | AD-16 |
| DEPENDENCY-MAP inventory classes | companion; spine AD-2 requires the classification |

No bound assignment *topic* is missing an AD. Browser HTTP admission, proof-storage home, and pairing/artifact persistence numbers/folds are the ones that will fork without H-1..H-3.

## Inherited parents (this walk)

| Parent | Child | Status |
| --- | --- | --- |
| QMA AD-24 / AD-5 never unauthenticated bind; credential before protocol | AD-5, AM-01 | **Named amendment** — hold if H-1 does not widen OPTIONS into family messages |
| QMA AD-24 broker allowlist; secrets as refs | AD-12, AD-4 internal ref | **M-2** must not extend allowlist |
| QMA AD-20 Envelope field list | AD-7, AM-02 | Named additive field; MessageKind/DeliveryState closed — hold |
| QMA AD-6 / AD-8 closed store + new fold = amendment | AD-4, AM-03 | **H-3** transfer ticket not in the named list |
| QMA AD-17 / parent AD-26 JobHandle states | AD-8, AM-04 | Additive field; states unchanged — hold |
| QMA AD-22 staging singleton | AD-11, AM-07 | Named non-entry — hold |
| QMA AD-5 three families; HTTP GET queries; no fourth family | AD-15, AM-05 | PUT named as byte channel — hold if H-1/M-3 do not mint REST/RPC `stage_artifact` |
| QMA AD-5 daemon never dials in | AD-9, AM-06 | Destination pulls — hold |
| QMA AD-5 `producer_id` unchanged across reconnects | AD-14 clone new id if live | Clone is a new initialize, not reconnect — hold if H-2 splits reconnect vs renew |
| QMA AD-26 registry numbers need defaults | Deferred TTL; companion PUT cap | **H-3** |
| parent AD-21 QMB only operator CLI; door parity | AD-6, AM-10 | Named `host` group — hold if M-1 one argv |
| parent AD-18 / AD-30 install ≠ grant; compile-at-enable | AD-11 | **M-4** grant word |
| parent AD-24 envelope `instance_id` required | AD-16; reuse Epic 60 | Hold — no silent null |
| kit AD-1..AD-9 pack-and-grant; no `ui_view` point | AD-10 | Hold |
| UI AD-18 chat = mailbox; UI AD-22 PUT; UI AD-23 cancel; UI AD-19 issuance | AD-7, AD-9, AD-8, AD-3 | Restate, do not reopen R1/R3–R9 |
| UI AD-12 three families; Tauri not v1 owner | AD-15; Tauri Deferred | Hold |
| Epic 60 `copilot_profile` sibling | AD-10 | Hold — no nest |

## Gate action

Do **not** freeze pairing, live CT-40 HTTP, QMB `host`, mailbox delivery amendments, artifact PUT, or draft-head epics on this text.

1. Apply **H-1**, **H-2**, **H-3** on the spine (editor-applicable; no new sitting). That also clears CORS vs AD-5, cold-start vs renew, TTL/cap/transfer-ticket uniqueness, and the pairing HTTP catalogue this altitude owns.
2. Apply **M-1**, **M-2**, **M-3** in the same pass (cheap; stops a CLI fork, an allowlist widen, and a phantom `stage_artifact` command).
3. **M-4..M-6** as one-liners.
4. L-1..L-5 optional; L-1 belongs on the Stack row if touched.

Status remains **draft** — internally reviewed candidate, not operator-accepted. Documentation Factory must not fold this sitting as ratified architecture until the Highs land and the operator accepts.

Joint-review launch in `REVIEW-LAUNCH.txt` still applies after this repair: confirm R2 traces, reload/cold-start wording, mailbox owner Epic 46.4, named amendments, DEPENDENCY-MAP inventory, preserved UI R1/R3–R9, and no implementation in these trees.
