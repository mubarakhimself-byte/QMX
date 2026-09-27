---
lens: rubric-walker
target: ARCHITECTURE-SPINE.md AD-1..AD-17 plus J1–J5 amendment (architecture-QMX-UI-BACKEND-2026-09-24)
altitude: feature
paradigm: Privileged-door daemon with named pairing bootstrap
reviewer_gate: good-spine checklist (references/reviewer-gate.md)
date: 2026-09-24
sitting_status: draft candidate after joint-review J1–J5 amendment — not operator-accepted
parent: architecture-QMX-2026-09-18 AD-1..AD-31
kit: architecture-QMX-2026-09-23 AD-1..AD-9
qma: architecture-QMA-2026-08-28
ui: architecture-QMX-UI-2026-09-23 AD-1..AD-24 (reconciled in place)
inspected: integration@34c148be404a375cbfd79fd4ce6997452e4f1d20 via .worktrees/integration-inspect
lint: sitting and operator report 0 findings on both spines; this walker did not re-run lint_spine.py
tests: unexecuted
historical_reviews: not rewritten (review-rubric.md, review-adversarial.md, and siblings remain first-pass evidence)
---

# Rubric walker — J1–J5 amendment of QMX UI backend-delta

Verdict: **fail**. The amendment closes the joint-review holes it was asked to close *as topics*: first-operator trust root (J1), bearer vs row identity (J2), daemon-issued `editor_draft_id` (J3), named `publish_editor_draft` (J4), and loopback-unreachable transfer with dest-authored `transfer_complete` (J5). Small reconciliations (shell ≠ provider, `get_pack_ui_request`, mailbox principal equality, optional `originating_product_session_ref`, `_ref` naming) are uniquely bound across both packets. R2 Origin-only issuance stays closed. First-pass H-1/H-2/H-3 are largely spent (CORS OPTIONS carve-out widened; `sessionStorage` home + `localStorage` forbidden; TTL refuse-until-set; `artifact_transfer_ticket` on AM-03).

It does not pass the uniqueness bar. Two live J2 lifecycle clauses still admit incompatible builders: (1) origin-revoke of **confirmed-but-unconsumed** pendings vs “unclaimed pendings”; (2) cloned-tab **reconnect-or-renew** occupancy of one `pairing_proof`. Pairing TTL’s write path is not exclusive of QMA AD-26 `variable.set`, so a paired browser can fork session lifetime after J1 bootstrap. Those three let the level below diverge on whether a privileged confirm still issues after origin revoke, whether clone rotates the first tab off the wire, and who may change TTL. Named tech is inherited and current. Brownfield is ratified, not copied. Candidate ≠ operator acceptance. No Documentation Factory, no epic rewrite, no implementation in this sitting.

Altitude: feature (keeps epics). Parents inherited by original ids (`parent AD-n` / `kit AD-n` / `QMA AD-n` / `UI AD-n`). Local AD-1..AD-17 each have Binds/Prevents/Rule. No template comments. Companions and the reconciled UI packet are coverage context; this walk judges live law, not historical `reviews/*.md`.

## Checklist

| Bar | Result |
| --- | --- |
| Fixes the real divergence points for the level below and misses none | **Fail** — J3/J4 unique. J1 trust root unique. J5 refusal class unique. J2 bearer/hash/confirm-once/rotate/expiry-closes-WS unique *except* origin-revoke of confirmed-unconsumed pendings and proof occupancy across connections. Misses exclusive TTL writer vs QMA AD-26. First-pass CORS/storage/ticket-fold mostly spent. PUT cap still unnamed on the spine Deferred table |
| Every AD's Rule is enforceable and actually prevents its stated divergence | **Fail** — AD-1/AD-2/AD-3/AD-7/AD-8/AD-10/AD-11/AD-12/AD-16 Prevents hold. AD-4 hash-only + confirm-once hold. AD-5 OPTIONS-never-issues holds, but “routes that declare CORS” is not a closed catalogue. AD-6 revoke argv is now one string. AD-9 `source_unreachable` holds. AD-14 forbids `localStorage` and cookies, not IndexedDB. AD-17 proof-of-operator holds; it does not uniquely freeze host-control transport or TTL’s only writer |
| Nothing under Deferred could let two units diverge | **Pass with Medium residual** — numeric pairing TTL now has a holding rule (unset → refuse issue). Proof entropy has a holding rule (unguessable, WS-token-safe). TLS-origin UX deferred with refusal class bound. Tauri / partial PUT / QR / envelope crypto / ASGI class hold. `registry:artifact.stage_max_bytes` and pending-code duration are still not on the spine Deferred table with a holding rule (DEPENDENCY-MAP names the cap, “no number here”) |
| Named tech is verified-current | **Pass with Low wording** — CPython **3.14** inherited; python.org Latest is **3.14.7** (2026-09-24). Spine “observed 3.14.6 at parent freeze” is inspect-honest, not a pin. RFC 6750 §1.2 bearer model matches AD-4. RFC 9110 §14.5 Partial PUT still refused. RFC 6455 Origin spoofing by non-browsers still holds. WHATWG WebSockets still selects one echoed subprotocol. HTML Web storage living standard snapshot **2026-09-22** still copied into auxiliary contexts. No new frontend pin. ASGI/`websockets` class correctly unpinned |
| Ratifies rather than contradicts brownfield | **Pass** — `DaemonProcess._handle_client` still discards TCP bytes at `34c148be`. `send_message` in `WireCommand`. `list_mailbox` / `cancel_job` / `publish_editor_draft` / `/pair/*` / `qmb host` / `host_control` / `pairing_proof` **absent** (0 hits under inspect). Envelope required fields unchanged; `ENVELOPE_FP1_EXCLUDED_FIELDS` is still `{correlation_id, causation_id}` only. JobHandle has `later_commands`, no originating session pointer. `COMMAND_GROUPS` has no `host`. Broker allowlist still `cred://models\|inference\|compute\|sandbox\|corpus\|knowledge\|telemetry/`. `AuthenticatedWireSession` still requires `credential_ref` — AM-11 is the named type change, not a silent pretend-it-exists. DEC-0286 / AD-2 hold |
| Inherited parents not weakened | **Partial** — no local AD mints a sixth COMP, new CT, UI grant store, cookie session, `ui_view` point, or nested `copilot_profile`. AM-01..AM-16 name the real conflicts, including AM-03 transfer tickets, AM-12 journal-lifetime mailbox collision, AM-14 `_ref`, AM-15 host-control, AM-16 `get_pack_ui_request`. AM-10/AD-6 do **not** uniquely close QMA AD-26’s `variable.set` write path for `registry:pairing.session_ttl`. QMA AD-24 “never offers an unauthenticated bind” is named (AM-01/AM-15), not silently overridden. QMA AD-22 stays one RefinementProposal type (AM-07). Broker allowlist not widened |
| Every owned dimension decided, deferred, or open — especially ops envelope | **Partial** — first operator, bearer custody table, draft issuer, publication command, transfer refusal class, shell vs provider, pack-UI read-back, mailbox principal, cancel optional field, `_ref` names are placed. Host-control **transport encoding**, proof **occupancy**, origin-revoke of **confirmed-unconsumed** pendings, exclusive TTL writer, PUT cap holding, pending-code duration, IndexedDB, and confirm-request identity are neither uniquely frozen nor held in Deferred/Open questions. Open questions still says “None blocking” |

## Joint-finding scorecard

| ID | Joint required result | Live law | Unique? |
| --- | --- | --- | --- |
| J1 | One trust root; clean-install trace; negatives for forged ref / unauthorized local / remote without proof; allowlist not widened | AD-17 + HOST: OS user of `QMA_DAEMON_ROOT` + owner-only `host_control` file; empty-root mint; TTL before issue; recovery same OS user/root; remote is SSH-there; T-BE-21/23 | **Mostly.** Remaining: TTL writer vs `variable.set` (H-2); host-control IPC encoding (M-6); operator-principal fold not on AM-03 (M-7) |
| J2 | Separate proof vs record id; hash-only journal; redaction; confirm once / lost confirm → re-pair; renew rotate; expiry closes WS; origin revoke cutoff; UI wording matches | AD-4/AD-3/AD-14 + PAIRING T-P-01..10; UI BOOTSTRAP 5.3–5.6; `pairing_proof` bearer; `pairing_record_id` nonsecret; `already_issued`; rolling renew TTL | **No.** Origin-revoke “unclaimed pendings” vs confirmed-unconsumed; cloned tab “reconnects **or** `/pair/renew`” (H-1) |
| J3 | One durable issuer; first save / lost ack / subsequent CAS / stale head | AD-11 + PACK-UI + UI AD-21: daemon issues on first save omitting id; `client_draft_correlation`; `expected_revision` = head fp1 | **Yes** at the issuer. Residual: client-supplied id on first save is “not the issuer path” without a typed refuse (M-3) |
| J4 | Named publication transition; owner; expected head; revalidate immutable fp1; local-pack write; enable remains compile identity; unsaved preview/validate legal | AD-11 `publish_editor_draft`; AM-09; UI AUTHORING 2.0 steps 4–8; T-BE-18; `draft_not_runnable` | **Yes** |
| J5 | One reachable route or typed refuse; ticket bound to dest identity + placement revision + machine audience; dest completion ack; invoke until complete; no silent loopback / local fallback | AD-9 + ARTIFACTS T-X-01..05; `source_unreachable` on loopback; dest `transfer_complete`; ticket projection on AM-03 | **Mostly.** Refusal class unique. Residual: command blocking vs `issued`→`notified` when dest control is down (M-5 class) |
| Small: provider vs shell | Distinguish clean-machine shell from provider readiness | AD-12/AD-13; PROVIDER table; UI TRACE first-run row | **Yes** |
| Small: PackUiRequest read-back | Named snapshot query + instance/availability key | AD-10 `get_pack_ui_request`; AM-16; UI AD-15; VIEW §3 | **Yes** |
| Small: mailbox send principal | Same principal check on send as on list | AD-7; MAILBOX; UI AD-18 / CHAT §1.1 | **Yes** |
| Small: cancel / headless | Optional originating field; omit on headless; exact handle/run/attempt | AD-8; CANCEL; UI AD-23 | **Yes** |
| Small: `_ref` naming | Name exception **or** rename; do not fight the validator | AM-14 `product_session_ref` / `originating_product_session_ref`; ProductSession own id stays `product_session_id`; exception list unchanged | **Yes** |

## What works

Paradigm is unchanged and still a real contract: **privileged-door daemon with named pairing bootstrap**, not a sixth COMP, not a UI BFF, not REST invoke, not Origin-as-identity.

- **J1 trust root is a choice, not a slogan.** Empty per-user root → `qmb host start` mints operator principal + `host_control` → `qmb host configure pairing-ttl` → pair → initialize. Forged `cred://models/…` as login refuses. Unauthorized OS user cannot read the token. Remote caller without the token refuses. `/pair/confirm` before TTL set refuses issue. Broker allowlist prefixes unchanged. Shape of a ref is not proof. That is the joint-required clean-install trace.
- **J2 custody table exists.** `pairing_proof` is RFC 6750 bearer; `pairing_record_id` is the journal identity; raw proof is not stored after issue; confirm returns proof **once**; retry is `already_issued`; lost confirm → re-pair; renew rotates and closes old WS; TTL elapsed closes WS; origin revoke is a journal-ordered cutoff; restart reloads hashes not raw proofs. UI BOOTSTRAP locked defaults, §5.3–5.6, failure matrix, and tests match those names. AM-11 value-class surface scan is named.
- **J3/J4 no longer disagree with the UI packet.** UI AD-21 and AUTHORING 2.0/2.1a omit durable id on first save; daemon returns `{editor_draft_id, editor_revision=fp1}`; `publish_editor_draft` then parent AD-30 enable then grant then select `instance_id` then `dispatchInvoke`. Enable is compile identity. Publish is not. Draft Run stays `draft_not_runnable`. QMA AD-22 untouched (AM-07).
- **J5 loopback hole is typed.** Default source is not a remote route. Ticket binds dest environment identity + placement revision + exact machine `credential_ref`. Dest authors `transfer_complete`. Invoke on that placement refuses until `complete`. AM-03 now names `artifact_transfer_ticket` (first-pass H-3 fold miss is spent).
- **First-pass enforceability holes mostly spent.** AD-5 unauthenticated list includes CORS OPTIONS on routes that declare CORS, and OPTIONS never issues a session / never upgrades WS / never returns artifact bytes. AD-6 revoke is `qmb host pair revoke --session|--origin`, not a sibling `pair-revoke`. AD-5/AD-12 pairing is **not** a `CredentialRef` and is not passed to `parse_credential_ref`. AD-7 excludes `product_session_ref` from Envelope fp1. AD-8 `handle_id` **is** `job_id`. AM-12 names the journal-lifetime mailbox collision.
- **Small list is actually small and closed.** Shell launch is not provider-ready. `get_pack_ui_request` is the read contract. Send and list share principal equality. Headless admits omit the cancel field. New pointers use `_ref`.
- **Brownfield honesty matches inspect `34c148be`.** Live CT-40 server absent; vocabulary has `send_message` among seed names only; QMB has no `host` group; Envelope has no product-session pointer; JobHandle has no originating-session pointer.

## Findings

### Critical

None. No local Rule authorizes a sixth COMP, `qma-cli`, COMP-UI, a new CT, a UI-owned scheduler or grant store, REST invoke, cookies as login, Origin-only auto-approval, nested grant union, `ui_view` as a contribution point, json-render as authority, or widening the broker allowlist with `cred://operator/`.

### High

#### H-1 — J2 lifecycle is still two implementations: origin-revoke of confirmed-unconsumed pendings, and one proof on many connections

**Where:** PAIRING lifecycle “`pair revoke --origin` … all sessions and **unclaimed pendings**”; T-P-06 “unclaimed pendings dead”; UI BOOTSTRAP locked defaults “Cloned tab … reconnects **(or `/pair/renew`)**”; AD-14 cloned tab “existing proof; new live `producer_id`”; AD-3 path 2 renew **rotates** (new proof, old revoked, old WS closed). Joint J2 required that origin revocation not leave **unclaimed approvals** able to issue again, and a compact table for renew vs an already-open socket.

**Two conforming units (origin revoke)**

- **Unit A — cutoff includes confirmed-unconsumed.** After `qmb host pair <code>` the pending has `confirmed_at` but is not yet HTTP-consumed. Origin revoke deletes that pending. `/pair/confirm` cannot issue. Matches joint “unclaimed **approvals**.”
- **Unit B — “unclaimed” means never QMB-paired.** Confirmed-unconsumed is “claimed” by the operator. Origin revoke kills live sessions and start-only pendings. A still-valid `POST /pair/confirm` mints a `pairing_proof` after the operator revoked that Origin. T-P-06 passes under Unit B’s dictionary. This is the original J2 hole with a word shift (`approvals` → `pendings`).

**Two conforming units (occupancy / clone)**

- **Unit A — reconnect.** Copied `sessionStorage` is existing proof. Both tabs present the same `pairing_proof` on two WebSockets with two `producer_id`s. Renew is optional. First tab stays live.
- **Unit B — renew on clone.** Reads the UI “or `/pair/renew`” and AD-3 rotate literally. Clone renews → old proof revoked → **first tab’s WS closes**. Clone is a denial of service on the tab the operator was using. A third unit forbids a second live presentation of the same proof without renew, and then cannot implement AD-14 “existing proof.”

J2’s job was one coherent issuance/recovery design. Hash-only + confirm-once + expiry-closes-WS are unique. These two remaining clauses are the live forks.

**Action:** autofix.

1. Origin revoke (`--origin`) is a journal-ordered cutoff of **all** pairing_session rows **and every pairing_pending** for that Origin with `created_at`/`confirmed_at`/`issued_at` ≤ cutoff, including **confirmed-unconsumed**. After cutoff, `/pair/confirm` cannot issue. Say “pendings (including confirmed-unconsumed)” once on AD-4 and in the PAIRING table; drop the adjective “unclaimed” or define it as “not yet HTTP-consumed.”
2. One `pairing_proof` **may** be presented on multiple connections for that Origin until expiry/revoke/rotate. Cloned tab **reconnects** with the copied proof and takes a new `producer_id` if the old is live (AD-14 / UI AD-24). `/pair/renew` is **not** the clone path; it is an explicit rotate that closes sockets on the old proof. Strike “or `/pair/renew`” from UI locked defaults.

#### H-2 — `registry:pairing.session_ttl` still has two writers (J1 bootstrap vs QMA AD-26)

**Where:** AD-4 / AD-6 / AD-17: TTL is `registry:pairing.session_ttl`, set on **local host-control** before first issue; missing row refuses issue. QMA AD-26: a **registry-homed** value is set only by an `operator`-principal **wire** command recording `variable.set`. AM-10 adds `qmb host configure pairing-ttl` as host-control, not CT-40, and does **not** say `variable.set` naming that key is refused. After J1, a browser-paired session **is** `principal_class=operator`.

**Two conforming units**

- **Unit A — exclusive host-control.** Only `qmb host configure pairing-ttl` (daemon sole writer, host-control authenticated by `host_control`) may create or change the row. CT-40 `variable.set` naming `registry:pairing.session_ttl` refuses. Lunch-break TTL cannot be extended from the SPA.
- **Unit B — AD-26 literal.** Host-control is how the **first** value is written (AD-17). Afterwards any operator wire `variable.set` is legal. A paired SPA sets TTL to 10 years, or a second story registers a 15-minute default to satisfy AD-26 “every registered variable declares a default.” J1’s “operator supplies the duration on the privileged door” becomes a slogan about first issue.

This sitting owns pairing session lifetime. Refuse-until-set closed first-pass “invent 15m vs 7d at issue.” It did not close **who may change it later**.

**Action:** autofix. One closed clause under AD-4/AD-17 and AM-10 (pick one and write it; recommended):

1. `registry:pairing.session_ttl` is **record-homed** on the host-control configuration (or an explicit host-control-only write path). CT-40 `variable.set` naming that key refuses.
2. Host-control configure remains the only mutation. Daemon still records the journal event (QMB never writes sqlite).
3. Keep the holding rule: unset → refuse pairing issue. Do not mint a number in this sitting.

### Medium

#### M-1 — AD-5 “OPTIONS on daemon HTTP routes that declare CORS” is not a closed catalogue

**Where:** AD-5 unauthenticated “only” list now includes CORS OPTIONS on routes that declare CORS; OPTIONS never returns a proof, never upgrades WS, never returns artifact bytes. AD-15 lists the HTTP surfaces (pairing POST, GET snapshots, PUT stage, GET artifacts, POST renew). UI 5.3: start/confirm reflect Origin; authenticated routes exact paired Origin; credentials omit.

First-pass H-1 (OPTIONS uniquely forbidden) is **spent** as a High: preflight of PUT/renew/GET is now legal. Remaining fork: which routes “declare CORS.”

**Two units:** OPTIONS only on the AD-15 named HTTP routes; or OPTIONS on every path on 8765 (including a mistaken HTTP `initialize`). OPTIONS-never-issues bounds the damage; ACAO `*` on an authenticated route is still a spec miss UI 5.4 already forbids.

**Action:** autofix. Closed OPTIONS set = the AD-15 HTTP routes only (`/pair/start`, `/pair/confirm`, `/pair/renew`, `PUT /artifacts/stage`, GET snapshot family, `GET /artifacts/<fp1>`). Never on WebSocket upgrade. Authenticated ACAO exact paired Origin; start/confirm may reflect the requesting Origin; credentials omit; never `*`.

#### M-2 — AD-14 cold-start uniqueness still omits IndexedDB (and any other durable browser store)

**Where:** AD-14 / PAIRING §6 / UI 5.5: memory + `sessionStorage`; `localStorage` forbidden; cookies forbidden. WHATWG: IndexedDB survives process quit. Joint J2 required protected custody. First-pass H-2 (`localStorage` + path-2 renew) is **spent** for `localStorage`.

**Two units:** sessionStorage is the only browser home (cold start ⇒ QMB); or persist `pairing_proof` in IndexedDB and `/pair/renew` after quit, which makes AD-14’s cold-start branch a slogan about `sessionStorage`.

**Action:** autofix. Browser home for `pairing_proof` / `pairing_record_id` / pending chat triple is **memory + `sessionStorage` only**. `localStorage`, cookies, IndexedDB, and any other durable web store are forbidden for the proof.

#### M-3 — J3 first-save is unique unless the client supplies an id (and unless bytes ride JSON-RPC)

**Where:** AD-11 Rule: first `save_editor_draft` **omits** `editor_draft_id`; CLOSURE-J1-J5 negative: “First save that *supplies* a client-minted durable id is **not the issuer path**.” PACK-UI: PUT bytes, then save without id. Spine AD-11 does not say PUT-then-save and does not typed-refuse a supplied id.

**Two units:** refuse a first-save that includes `editor_draft_id` (and refuse JSON-RPC bodies of draft bytes; PUT `/artifacts/stage` then save naming fp1); or accept a client-minted id / byte body and reopen J3.

**Action:** autofix. First save that includes `editor_draft_id` → typed refuse (not the issuer path). Draft bytes use the AD-9 PUT channel; `save_editor_draft` names the local-complete fp1. Same `client_draft_correlation` + different bytes hash → refuse (no second working copy).

#### M-4 — AD-13 still advertises `stage_artifact` as if it were a JSON-RPC command, and omits `save_editor_draft` / `transfer_complete`

**Where:** AD-13 / PROVIDER capability list includes `stage_artifact`; ARTIFACTS / AM-09: **no** JSON-RPC `stage_artifact`. AM-09 addable commands include `save_editor_draft` and `transfer_complete`, absent from the advertised set.

**Two units:** capability means PUT exists (first-pass reconcile note); or a builder mints `WireCommand.STAGE_ARTIFACT` because initialize listed it. Clients cannot share a feature-detect for J3 save or J5 complete.

**Action:** autofix. `stage_artifact` capability **means authenticated PUT `/artifacts/stage` exists** — not a `WireCommand`. Add `save_editor_draft` and `transfer_complete` to the advertised set (or state they ride `publish_editor_draft` / `transfer_artifact` — don’t leave them unnamed).

#### M-5 — PUT cap and pending-code duration are owned numbers without a spine holding rule

**Where:** DEPENDENCY-MAP `registry:artifact.stage_max_bytes` “no number here”; UI LIBRARY oversize refuses; AD-9 requires Content-Length and names no cap. PAIRING pending rows have `expires_at` with no registry key and no Deferred row. Joint review: TTL and byte limits need explicit **preconditions** before first use; do not invent performance numbers. Session TTL now has refuse-until-set. PUT/pending do not.

**Two units:** missing `stage_max_bytes` → refuse PUT (precondition) vs unlimited vs invented 8 MiB; pending codes live 2 minutes vs until session TTL vs forever until confirm.

**Action:** autofix. Put both on Deferred **with a holding rule** (recommended: missing `registry:artifact.stage_max_bytes` → refuse PUT; pending codes expire at a closed default **or** refuse `/pair/start` until a pending-ttl row is set). Do not mint a performance number if the operator still does not want one — mint the **refuse** instead.

Related J5 residual (not a second High): ticket states include `issued` \| `notified`. `transfer_artifact` may return a ticket still `issued` while dest control is down, or block until `notified`. Invoke-until-`complete` still holds. Bind: command returns `ticket_id`; dest is notified on the already-authenticated control connection **when that connection is live**; if it is not, ticket stays `issued` until reconnect then `notified`; dest then pulls. Do not refuse topology that J5 already allows; do not wait forever inside the command.

#### M-6 — Host-control transport encoding is unnamed (J1 residual)

**Where:** AD-17 / AD-15: loopback-only channel, **not** CT-40, **not** `/pair/*`, “not port-8765 pairing HTTP,” token file under `QMA_DAEMON_ROOT`. HOST: QMB presents the current token. Joint J1 required owner + proof verification (named) — not HTTP vs named pipe vs drop-file.

**Two units:** privileged HTTP on `127.0.0.1` another port; same :8765 `/host/*` (not pairing HTTP, so AD-15 literal allows it); Windows named pipe / Unix socket under the root; drop-file IPC (first-pass adversarial Unit A). QMB stories and daemon stories can miss each other.

**Action:** discuss then freeze one encoding on AD-17 (recommended: loopback HTTP **not** on 8765, `Authorization: Bearer host:<token>`, no CORS, no browser). Proof verification stays “present current `host_control`.” Stale-PID lock recovery stays the deferred implementation story.

#### M-7 — J1 durable operator principal is not an AM-03 named projection

**Where:** AD-17 “mint the first operator principal (journal)”; AM-03 list = `pairing_pending`, `pairing_session`, `editor_draft_head`, `artifact_transfer_ticket`. QMA AD-6: a new fold is a spine amendment.

**Two units:** fold into an existing identity/Quant row; a new `host_operator` projection; or “empty root” = missing `host_control` file even when a principal already exists (second mint). Recovery “same OS user, same root, start — principal remains” fights Unit C.

**Action:** autofix. Name the fold (or name the existing row) on AM-03. Empty root = no operator principal in journal, not “token file missing.” Lost `host_control` file: refuse until `qmb host rotate-control` from a still-valid token **or** a named recovery (do not remint a second principal). Rotate-control recovery-without-token may stay implementation if the refuse is unique.

#### M-8 — Confirm request identity is unique in the UI packet, not on the backend Rule

**Where:** UI BOOTSTRAP 5.3: start response `{code, expires_at, pending_id}`; confirm body `pending_id`. PAIRING §3 names confirm **response** `{pairing_record_id, pairing_proof, expires_at}` once, not the request. AD-3 does not name JSON. Joint review deferred “implementation-level DTO field lists beyond named commands” — but multiple live pendings per Origin (second tab) make confirm identity a **command** contract, not a field-list.

**Two units:** confirm `{pending_id}` (UI); confirm `{code}` (status-bar paste); confirm `{pending_id, code}`. Second-tab issuance forks.

**Action:** autofix. Promote the UI JSON onto AD-5 / PAIRING §3: start → `{pending_id, code, expires_at}`; confirm request `{pending_id}` (Origin header binds); renew empty body + Bearer → `{pairing_record_id, pairing_proof, expires_at}` once. Code is never the confirm key.

### Low

#### L-1 — CPython citation is 3.14.6 (parent freeze); Latest is 3.14.7

Inherited, not a pin. CONNECT-style “3.14.7 exists and is not adopted here” would match kit currency notes.

**Action:** ignore if a currency lens lands the Stack row; else one clause.

#### L-2 — Linux/macOS data-root live on HOST, Windows-only on the spine ops paragraph

Spine operational envelope names `%LOCALAPPDATA%\QMX\qma-daemon` on Windows. HOST-LIFECYCLE also names Linux XDG and macOS Application Support. UI BOOTSTRAP 4.3 omits macOS. A spine-only reader still ships Windows-only root.

**Action:** one ops sentence listing all three HOST paths; UI 4.3 add macOS.

#### L-3 — Open questions “None blocking” while H-1/H-2 remain owned and unfrozen

Legal only after H-1/H-2 land on the Rule. Otherwise occupancy, origin-revoke confirmed-unconsumed, and TTL writer belong under Open questions, not “none.”

**Action:** ignore if H-1/H-2 applied; else move those three to Open questions.

#### L-4 — Lost `host_control` token without a still-valid token

HOST recovery is rotate-control (needs the current token) or same-user restart (principal remains). Stolen-or-deleted file with no remaining token is unnamed. Joint review parked ordinary supervisor PID/signal mechanics as implementation. Treat lost-token as the same class **once M-7 refuses reminting a second principal**.

**Action:** defer with holding refuse (M-7).

#### L-5 — CLOSURE-EVIDENCE points at `reviews/gate-j1j5-summary.md`, which this sitting has not written

Documentation pointer, not a builder fork. Historical first-pass reviews were correctly left in place.

**Action:** ignore for this walker (not a spine Rule).

## Dimensions owned at this altitude

| Dimension | Disposition |
| --- | --- |
| Sitting scope / no Docs Factory / no epic rewrite | AD-1 |
| Planned ≠ implemented; mailbox owner Epic 46.4 | AD-2, AD-7 |
| Pairing issuance (Origin never sufficient) | AD-3 — **holds** |
| Pairing proof vs record / hash-only / confirm-once / rotate / expiry-closes-WS | AD-4, AM-03, AM-11 — **H-1** occupancy + origin-revoke confirmed-unconsumed |
| Unauthenticated carve-out | AD-5, AM-01 — **M-1** OPTIONS catalogue; **M-8** confirm JSON |
| First operator / host-control | AD-17, AD-6, AM-15 — **H-2** TTL writer; **M-6** IPC; **M-7** operator fold |
| Process lifetime / QMB host door | AD-6, AM-10 — revoke argv unique |
| Mailbox field + principal equality + `list_mailbox` | AD-7, AM-02, AM-08, AM-12, AM-14 |
| Cancel + optional originating `_ref` | AD-8, AM-04, AM-09, AM-14 |
| PUT + reachable transfer + dest complete | AD-9, AD-15, AM-05, AM-06, AM-03 ticket — J5 refusal unique; **M-5** cap / dest `issued`→`notified` |
| PackUiRequest / `get_pack_ui_request` / GRANT_AMBIGUOUS | AD-10, AM-16 |
| Draft issuer + `publish_editor_draft` + AD-30 enable | AD-11, AM-07, AM-09 — J3/J4 unique; **M-3** supplied-id refuse |
| Secrets / broker / shell ≠ provider | AD-12 |
| Additive capabilities | AD-13 — **M-4** `stage_artifact` name |
| Reload / clone / cold start | AD-14 — **H-1** clone or-renew; **M-2** IndexedDB |
| Byte channel vs families / SPA origin ≠ 8765 | AD-15 |
| No sixth COMP / no new CT | AD-16 |
| Numeric pairing TTL | Deferred **with** refuse-until-set; **H-2** later writer |
| Proof-token entropy | Deferred with unguessable + WS-token-safe holding |
| TLS-origin recording UX | Deferred; refusal class bound |
| PUT cap / pending-code duration | Owned, not on spine Deferred — **M-5** |
| Stale-PID lock recovery | Deferred (joint: implementation) |
| Native/QMB secret writer | Deferred; provider use needs external provision |
| Distributable pack export | Deferred parent AD-18 |
| Implementation DTO field lists | Deferred — except confirm identity (**M-8**) |
| Tauri sidecar | Deferred UI AD-12 |
| Partial PUT resume | Deferred; v1 refuse holds |
| Cross-tab QR | Deferred; v1 QMB confirm holds |
| Envelope crypto | Deferred GAP |
| ASGI / `websockets` class | Deferred with named HTTP+WS contract holding |
| Backup / restore | inherit QMA AD-27 |

## Tech currency (this walker)

Checked 2026-09-24 against primary sources. This walk does not re-pin anything.

| Named | Check |
| --- | --- |
| CPython 3.14 (observed 3.14.6 at parent freeze) | python.org Latest **3.14.7** (release notes 2026-08-05; downloads page still “Latest: Python 3.14.7” on 2026-09-24). Inherited major. Not a backend pin |
| RFC 6750 §1.2 | Bearer = possession authorizes. AD-4/UI 5.3 cite correctly |
| RFC 9110 §14.5 Partial PUT | v1 refuse still matches the spec section |
| RFC 6455 §10.1 | Non-browser Origin spoofing; Origin never operator identity. Holds |
| WHATWG WebSockets | Server echoes **one** selected subprotocol; browsers cannot set `Authorization` on `WebSocket`. UI 5.4 still correct |
| HTML Web storage 2026-09-22 | `sessionStorage` per tab; auxiliary browsing context **copies** it. AD-14 clone branch depends on this and is still right |
| Fetch CORS | PUT + `Authorization` preflights; OPTIONS does not carry Authorization. AD-5 OPTIONS carve-out is the right spec move; catalogue still M-1 |
| Inspect `34c148be` | `_handle_client` discards bytes; no pairing/host/mailbox-query/cancel/publish symbols; allowlist prefixes unchanged |

## Autofix / discuss / defer

| ID | Bucket | Why |
| --- | --- | --- |
| H-1 origin-revoke confirmed-unconsumed; clone occupancy | **autofix** | Word-level uniqueness on a table this sitting already owns |
| H-2 exclusive TTL writer | **autofix** | One AM-10/AD-26 sentence; otherwise J1’s privileged door is not the only door |
| M-1 OPTIONS catalogue | **autofix** | Promote AD-15 list onto AD-5 |
| M-2 IndexedDB | **autofix** | One forbidden-store clause |
| M-3 first-save refuse + PUT-then-save | **autofix** | Closes J3 residual |
| M-4 capability names | **autofix** | Cheap; prevents a forbidden `WireCommand` |
| M-5 PUT cap / pending ttl holding; dest `issued`→`notified` | **autofix** | Holding refuse, not a performance number |
| M-6 host-control encoding | **discuss** then freeze | J1 residual; more than PID mechanics; cheaper than another joint round if one encoding is named |
| M-7 operator-principal fold | **autofix** | AM-03 add or cite existing row |
| M-8 confirm `{pending_id}` | **autofix** | Already in UI 5.3; promote onto backend Rule |
| L-1..L-5 | **defer / ignore** | Currency wording, ops completeness, open-questions sentence |

Do not implement. Do not run Documentation Factory. Do not rewrite first-pass `reviews/review-rubric.md` (or siblings). After H-1 and H-2 (and the cheap M-autofixes) land, this J1–J5 amendment is ready for the Codex closure pass the sitting already scheduled — still candidate, still not operator-accepted.
