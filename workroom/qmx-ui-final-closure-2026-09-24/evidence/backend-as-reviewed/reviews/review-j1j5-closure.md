---
name: Independent J1–J5 closure review
sitting: architecture-QMX-UI-BACKEND-2026-09-24
against: workroom/qmx-ui-backend-joint-review-2026-09-24/REVIEW.md J1–J5 + GROK-FOLLOWUP.md small reconciliations
date: 2026-09-24
reviewer: Grok 4.6 independent closure
status: closed as candidate — no remaining High
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
tests: unexecuted
---

# Independent J1–J5 closure review

Do not implement. Historical first-pass files under `reviews/` were not edited. This file is the closure pass over the **live** backend-delta packet and the **reconciled** UI candidate.

**Packets**

- Backend-delta: `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/`
- UI candidate: `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/`
- Joint review: `workroom/qmx-ui-backend-joint-review-2026-09-24/REVIEW.md`
- Follow-up: `workroom/qmx-ui-backend-joint-review-2026-09-24/GROK-FOLLOWUP.md`

**Verdict:** J1–J5 **closed as candidate**. Small reconciliations **closed as candidate**. Remaining High: **none**. Origin-only issuance remains closed. Layouts, Svelte/TypeScript, headless/visual, and Epics 60–65 were not reopened. Candidate ≠ operator acceptance. No live daemon, no executed tests, no Documentation Factory.

| ID | Finding | Verdict | Remaining High |
| --- | --- | --- | --- |
| J1 | First operator on a clean install | **closed** | none |
| J2 | Pairing bearer custody and lifecycle | **closed** | none |
| J3 | One durable draft-id issuer | **closed** | none |
| J4 | Validated publication | **closed** | none |
| J5 | Reachable artifact transfer | **closed** | none |

Live-field scan (UI law files, excluding `reviews/` and old `.memlog.md` lines): **no** live `pairing_session_id`, **no** live `originating_psess`, **no** live `Envelope.product_session_id`. Envelope pointer is `product_session_ref`. ProductSession **own** identity remains `product_session_id`. Pairing proof is `pairing_proof`; journal row is `pairing_record_id`. Cancel pointer is `originating_product_session_ref`.

---

## Method and preserve checks

Reviewed live sentences in backend AD-1..AD-17, companions, `PARENT-AMENDMENT-MAP.md` AM-01..AM-16, `DEPENDENCY-MAP.md`, `TRACE-MATRIX.md`, `CLOSURE-J1-J5.md`, and reconciled UI AD-15/18/19/21/22/23 plus `BOOTSTRAP-AND-AUTH.md`, `CHAT-AND-HISTORY.md`, `AUTHORING-AND-ML.md`, `VIEW-AND-PACK-CONTRACT.md`, `LIBRARY-AND-ATTACHMENTS.md`, `TRACE-MATRIX.md`. Historical `reviews/` and memlog decisions are evidence of prior state, not current law.

| Preserve check | Result |
| --- | --- |
| Origin-only issuance still closed | **Hold.** Backend AD-3: “A remembered Origin **never** authorizes issuance of a new pairing proof.” UI AD-19: “a remembered Origin never authorizes a new `pairing_proof`.” T-BE-01 / T-P-01 / BOOTSTRAP second-tab row refuse Origin-only auto-approve. |
| Layouts not reopened | **Hold.** UI AD-3 still names Home / Copilot / Library / Authoring above the divider. `EXPERIENCE-AND-LAYOUT.md` was not part of the J1–J5 edit set (`UI-CANDIDATE-CHANGELOG.md`). |
| Svelte/TypeScript not reopened | **Hold.** UI AD-2 seed unchanged (Svelte 5.57.1 + SvelteKit 2.70.3 + TypeScript 5.9). |
| Headless not reopened | **Hold.** UI AD-5; TRACE headless CLI invoke; cancel field **omitted** on headless so Story 36.5 remains the abort door. |
| Epics 60–65 not rewritten | **Hold.** `DEPENDENCY-MAP.md` §1 reuse/adoption-gap. `PluginManifest.copilot_profile` stays Epic 60 sibling. AM-16 adds `get_pack_ui_request` **beside** Epic 60. |

Honesty limits (not defects): inspect SHA still `34c148be`; `DaemonProcess` still discards TCP bytes; pairing HTTP, `qmb host`, `list_mailbox`, `publish_editor_draft`, `transfer_complete` remain **absent in code**. Planned epics are requirements, not delivery.

---

## J1 — First operator bootstrap — **closed**

**Joint-review required result.** One initial trust root; clean root → establish operator identity → configure required pairing policy → confirm pending browser → initialize. Name owner, proof verification, provisioning, recovery. A well-shaped ref is not proof. Name QMA/Story 41.4 amendment. Preserve QMB as operator door and daemon as sole writer.

### Choice (live)

Trust root is the **OS user who owns `QMA_DAEMON_ROOT`** plus a daemon-minted **`host_control` token** (owner-only ACL) on a **loopback host-control channel**. That channel is not CT-40, not `/pair/*`, and not a provider `cred://`. Broker allowlist is not widened.

### Evidence in both packets

| Claim | Backend | UI |
| --- | --- | --- |
| Trust root / empty-root mint / TTL before issue | `HOST-LIFECYCLE.md` §Trust root; spine **AD-17**, **AD-6** | `BOOTSTRAP-AND-AUTH.md` locked defaults; §5.3; §12 verbs; UI **AD-19** |
| Allowlist not an operator-login family | spine **AD-12**; `PROVIDER-AND-COMPAT.md` | BOOTSTRAP §5.2 two credential planes |
| QMB door, daemon sole writer | AD-6: “QMB never writes daemon sqlite.” HOST-LIFECYCLE verbs | BOOTSTRAP §10 owners; §12 “Does not: … issue a pairing proof” |

**Quoted backend AD-17:** “Trust root is the **OS user who owns `QMA_DAEMON_ROOT`** plus a daemon-minted **`host_control` token** stored under that root with owner-only ACL. The channel is loopback-only and is **not** the CT-40 listener … Proof verification: QMB must present the current `host_control` token from that root; a forged `credential_ref` / caller-selected `principal_class` is not proof; a remote caller without that token is refused; a different OS user who cannot read the token is refused.”

**Quoted UI AD-19:** “First operator is that local control path (backend-delta AD-17), not a provider `cred://`.”

**Quoted UI BOOTSTRAP §5.3:** “Pairing HTTP refuses issue until first operator exists and pairing TTL is set (backend-delta AD-17).” “First operator is minted on `qmb host start` of an empty `QMA_DAEMON_ROOT` (backend-delta AD-17), before any pairing HTTP.”

**Quoted UI BOOTSTRAP §12:** “`qmb host start` … on empty root mint first operator principal + `host_control`” / “Does not: … issue a pairing proof”. “`qmb host configure pairing-ttl` … Required before first issue”. “`qmb host status` … pairing pending/bound **record ids** (never proofs)”.

### Named inherited amendments

| ID | What it names |
| --- | --- |
| **AM-15** | Local host-control under `QMA_DAEMON_ROOT` is **outside** the wire listener. First operator + TTL + pair confirm use that channel. Story 41.4 / QMA AD-24 still authenticate CT-40 before protocol. Broker allowlist **not** widened. |
| **AM-10** | QMB group `host`: `start`, `status`, `stop`, `configure pairing-ttl`, `pair <code>`, `pair revoke`, `rotate-control`. |
| **AM-01** (context, not the trust root) | Unauthenticated HTTP remains only `/pair/start`, `/pair/confirm`, CORS OPTIONS. |

### Positive trace

Empty per-user root → `qmb host start` (operator principal + `host_control`) → `qmb host configure pairing-ttl` → POST `/pair/start` → `qmb host pair <code>` → POST `/pair/confirm` → `pairing_proof` **once** → `initialize`.

- Backend: `HOST-LIFECYCLE.md` Clean-install trace steps 1–6; T-BE-21; T-BE-23.
- UI: BOOTSTRAP §5.3 steps 1–8 plus §12 configure verb. Sequence after confirm is Bearer + WS subprotocols then `initialize`.

### Negative traces

| Caller | Result | Where |
| --- | --- | --- |
| Forged `cred://models/…` / `cred://telemetry/…` as login | refuse / `CredentialOutOfScope`. Allowlist not widened | HOST-LIFECYCLE negatives; T-P-08; T-BE-23; BOOTSTRAP §5.2 / failure “Arbitrary `cred://` pasted” |
| Unauthorized local OS user (cannot read `host_control`) | refuse pair/configure | HOST-LIFECYCLE; AD-17 |
| Remote caller without host-control | refuse. “The laptop browser never bootstraps a remote operator.” SSH-there | HOST-LIFECYCLE; T-P-09; AD-17 |
| `/pair/confirm` before TTL set | refuse issue | HOST-LIFECYCLE; AD-4 / AD-17; BOOTSTRAP §5.3 |

### Deferrals (honest, not J1 holes)

- Exact TTL duration is operator-supplied; this sitting mints no number (AD-4, HOST-LIFECYCLE, Deferred table).
- Stale-PID lock recovery is an implementation story (HOST-LIFECYCLE Data root and lock).
- Exact host-control IPC class (loopback HTTP vs socket vs file drop) is not frozen; token + loopback + “not CT-40” is frozen.
- UI BOOTSTRAP §6 mermaid / step list still jumps from `qmb host start` to `/pair/start` and does not draw `configure pairing-ttl`. **Not High:** §5.3 and §12 bind the refuse-until-set rule, and the backend clean-install trace includes the step. Documentation Factory should insert the missing step in that diagram.

---

## J2 — Pairing credential custody and lifecycle — **closed**

**Joint-review required result.** Separate nonsecret record identity from secret proof. Bind generation/encoding, protected custody, journal representation, redaction of Authorization and `qmx.pair.*`, safe diagnostics. Hash + lifecycle metadata in the journal; do not retrieve a raw proof the server no longer stores. Compact state table for confirm retries/lost responses, renewal, expiry on an active connection, session revoke, origin revoke, restart, concurrent renew/revoke. Synchronize UI. Do not require OAuth/cookies/new identity platform.

### Choice (live)

`pairing_proof` is an RFC 6750 bearer. `pairing_record_id` is the nonsecret row. Journal stores `proof_fp1` only. Confirm returns the proof **once**. Retry is `already_issued`. Lost confirm → re-pair. Renew **rotates** (new proof, old revoked, old WS **closed**). Expiry **closes** WS. Origin revoke is a journal-ordered cutoff.

### Evidence in both packets

| Claim | Backend | UI |
| --- | --- | --- |
| Two names; hash-only journal; redaction | `PAIRING-AND-ADMISSION.md` §§1–4; spine **AD-4**, **AD-5**, **AD-14** | BOOTSTRAP locked defaults; §5.3–5.6; failure matrix; tests; UI **AD-19** |
| Lifecycle table | PAIRING §4 rows T-P-01..10 | BOOTSTRAP failure rows: confirm-once, `already_issued`, lost confirm, expiry closes WS, Origin-only refuse |
| Expiry closes active socket (prior UI/backend fork) | AD-4: “Expiry **closes** sockets that presented that proof.” PAIRING: “Record expired; **close** WS on that proof” | BOOTSTRAP locked default: “Expiry **closes** the WS.” Failure “Expired / revoked pairing”: “Expiry **closes** the WS.” |

**Quoted backend AD-4:** “`pairing_proof` is a **bearer credential** (RFC 6750 §1.2): possession authorizes. `pairing_record_id` is the nonsecret row identity. Journal projections `pairing_pending` and `pairing_session` (**AM-03**) store `pairing_record_id`, Origin, operator principal, `proof_fp1` (hash of the proof), issued/expires/revoked, pending lineage — **never** the raw proof. … Access logs, traces, diagnostics, crash reports, and `qmb host status` redact Authorization and `qmx.pair.*`.”

**Quoted PAIRING §1:** “The daemon **does not store** the raw proof after issue. Lost confirm response → re-pair (new pending). Do not retrieve a raw proof from the journal.” “Surface scan refuses raw proof values, not only keys named `token`/`bearer`.”

**Quoted UI BOOTSTRAP §5.3:** “`pairing_proof` is a bearer credential (RFC 6750 §1.2): possession authorizes. It is **not** a nonsecret label. Do not put it in journals, traces, diagnostics, or query strings. … Confirm returns the proof **once**; a lost response requires re-pair.” “After confirm: JSON `{pairing_record_id, pairing_proof, expires_at}` **once**. Retry of the same pending is `already_issued`. … Renew **rotates**: new proof, old proof revoked, old WS closed.”

**Quoted UI BOOTSTRAP failure “Lost confirm response”:** “Proof already minted and hashed; retry is `already_issued`. Client re-pairs (`/pair/start`). Must not: Retrieve raw proof from journal or status.”

The previous stay-until-detach vs expiry-drops-socket fork is gone from **live** law. Historical first-pass `review-adversarial.md` still describes the old sentence; that file is not law.

### Named inherited amendments

| ID | What it names |
| --- | --- |
| **AM-01** | Unauthenticated HTTP only POST `/pair/start`, POST `/pair/confirm`, CORS OPTIONS. `/pair/renew` is authenticated. |
| **AM-03** | Journal projections `pairing_pending`, `pairing_session` (plus draft/transfer) added to the closed sqlite-addition list. Still not a new sqlite **class**. |
| **AM-11** | Browser-paired session: `principal_class=operator` + `pairing_record_id`, **no** `credential_ref`. Proof is a bearer; journal stores `proof_fp1`. Surface scan by value class. |
| **AM-13** | Authenticated POST `/pair/renew` is pairing HTTP, not a CT-40 family. |

### Positive traces

| ID | Intent |
| --- | --- |
| T-P-02 / T-BE-02 | Confirm after local pair → proof **once**; journal `proof_fp1` only; no Set-Cookie |
| T-P-04 / T-BE-03 | Renew → new proof; old proof refused; old WS closed |
| T-BE-05 | Same-tab sessionStorage proof reconnects until TTL |
| T-BE-07 | Cloned tab = copied existing proof + new `producer_id` if old live; not Origin-only |

UI BOOTSTRAP tests (unexecuted) match: confirm once / `already_issued`; WS without `qmx.pair.<proof>` refused; second tab Origin-only auto-approve refused; same-tab reload restores `pairing_proof`.

### Negative traces

| ID | Intent |
| --- | --- |
| T-P-01 / T-BE-01 | Origin known, no proof, no QMB confirm → no proof, WS refused |
| T-P-03 / T-BE-24 | Second confirm same pending → `already_issued` |
| T-P-05 / T-BE-04 | TTL elapsed → WS closed; Bearer refused |
| T-P-06 | Origin revoke → earlier sessions **and unclaimed pendings** dead |
| T-P-07 / T-BE-25 | Trace/status dump contains no raw proof / Authorization / `qmx.pair.` value |
| T-P-10 / T-BE-06 | Lost confirm → re-pair; no journal retrieval of proof |

PAIRING §4 also binds: concurrent renew vs revoke = first durable journal append wins; daemon restart reloads hashes (raw proofs not in sqlite); still-valid proofs work until TTL; rolling `expires_at` = now + configured TTL, bounded by revoke.

### Deferrals (honest, not J2 holes)

- Entropy/length of the proof token is an implementation story (must be unguessable and WS-token-safe). PAIRING §1 states the constraint.
- Numeric TTL remains operator-supplied.
- Projection **name** `pairing_session` is the journal fold, not the bearer field. Live bearer name is `pairing_proof`.
- UI BOOTSTRAP mermaid still says `Authorization Bearer pairing:id`. Shorthand, not the identifier `pairing_session_id`. Documentation Factory should say `pairing:<proof>`.
- Backend `research/00-inspect-and-sources.md` still says a cloned tab “may already hold `pairing_session_id`”. Research, not law. Live AD-14/BOOTSTRAP use `pairing_proof`.

---

## J3 — Draft creation and first-save identity — **closed**

**Joint-review required result.** One durable issuer. Define first-save input/result, subsequent saves, lost-response reconciliation, stale CAS. If the daemon issues the durable id, distinguish any client provisional correlation and return the durable id with `editor_revision`. Preserve fp1 revision identity and `expected_revision`. Reconcile both packets.

### Choice (live)

Daemon is the sole durable `editor_draft_id` issuer. First `save_editor_draft` **omits** the id. Optional `client_draft_correlation` recovers lost first-save ack. Subsequent saves require durable id + `expected_revision` = current head fp1.

### Evidence in both packets

| Claim | Backend | UI |
| --- | --- | --- |
| Sole durable issuer; first save omits id | spine **AD-11**; `PACK-UI-AND-AUTHORING.md` §Draft identity | UI **AD-21**; `AUTHORING-AND-ML.md` locked defaults; identities table; transitions Create / Save; §2.0; §2.1a |
| Lost-ack coalesces; stale CAS | PACK-UI table rows Lost first-save ack / Stale CAS | AUTHORING §2.1a two restored clients; §2.0 step 2 |

**Quoted backend AD-11:** “**Daemon** is the sole durable `editor_draft_id` issuer. First `save_editor_draft` **omits** `editor_draft_id`; `expected_revision` is empty; optional `client_draft_correlation` makes lost-ack retry return the same durable id. Result is `{editor_draft_id, editor_revision}`. Subsequent saves require durable id + `expected_revision` = current head fp1.”

**Quoted UI AD-21:** “The **daemon** is the sole durable `editor_draft_id` issuer. First save omits that id (optional `client_draft_correlation`); subsequent saves require durable id + `expected_revision`.”

**Quoted AUTHORING locked default:** “**Daemon** issues durable `editor_draft_id`. First save omits that id (optional `client_draft_correlation`). Subsequent saves + `publish_editor_draft` use CAS `expected_revision` = last known `editor_revision` hash (content fp1). Stale save → typed conflict. No last-writer-wins. Two restored clients: second save refuses until it reloads head.”

The prior fork (UI mints `editor_draft_id` before first save; backend mints on first save while requiring the id in that request) is gone.

### Named inherited amendments

| ID | What it names |
| --- | --- |
| **AM-03** | Journal projection `editor_draft_head`. |
| **AM-07** | **Non-amendment of QMA AD-22.** Drafts are artifact-store bytes + `editor_draft_head`. AD-22 stays one RefinementProposal type. |
| **AM-09** | Addable command `save_editor_draft` (with `publish_editor_draft`). |

### Positive traces

- Create → unsaved buffer + optional `client_draft_correlation`; **no** durable id (AUTHORING Create row; §2.0 step 1).
- First save: PUT bytes, `save_editor_draft` **without** `editor_draft_id` → `{editor_draft_id, editor_revision=fp1}` (PACK-UI; AUTHORING §2.0 step 2; T-BE-17).
- Lost first-save ack: retry same `client_draft_correlation` + same bytes → same durable id; no second working copy (PACK-UI; T-BE-17 must-not “two working copies”).
- Subsequent save: durable id + `expected_revision` = current head fp1 + new bytes → new head fp1.

### Negative traces

- First save that **supplies** a client-minted durable id is not the issuer path (T-BE-17 must-not “UI-minted durable id”).
- Stale CAS: expected hash ≠ head → typed conflict; head unchanged (PACK-UI; AUTHORING §2.1a).
- Two restored clients both at `R1`: first save → `R2`; second with `expected_revision=R1` refuses until reload (AUTHORING §2.1a). Required J3 closure evidence is present.

### Deferrals (honest, not J3 holes)

- AUTHORING **Edit** row still starts “From: `editor_draft_id`”. Unsaved-buffer edits live on the Create row until first save. Awkward table, not a second issuer.
- Implementation-level DTO field lists beyond named commands remain later (CLOSURE-J1-J5 remaining deferrals).
- `initialize` capability list (AD-13 / PROVIDER-AND-COMPAT) names `publish_editor_draft` and not `save_editor_draft`. Residual advertisement gap, not an identity-owner fork.

---

## J4 — Validated-revision-to-local-pack publication — **closed**

**Joint-review required result.** Name the backend publication transition, owner, draft authority, expected head, immutable fp1, validation, and local-pack write/result. Revalidation at publication is acceptable; a new durable validation record is not mandatory. Keep preview/validate legal before enable, including unsaved-buffer mode. Parent AD-30 enable remains compile identity. Do not invent a second enable machine.

### Choice (live)

Addable **`publish_editor_draft`** checks ownership, `expected_revision`, **reruns validation against that immutable fp1**, and writes the local authoring-pack contribution. No mandatory extra validation record. Unsaved preview/validate stay legal. Parent AD-30 **enable** remains compile identity.

### Evidence in both packets

| Claim | Backend | UI |
| --- | --- | --- |
| Named command + steps | `PACK-UI-AND-AUTHORING.md` §Publication; spine **AD-11** | UI **AD-21**; AUTHORING publish row; §2.0 steps 4–8; §2.1 refused table |
| Enable is compile identity | AD-11; PACK-UI “Then **enable** that local pack (parent AD-30)” | AUTHORING locked default “Compile identity”; Enable row; §2.1 “Treat publish as compile identity → forbidden” |
| Unsaved preview/validate legal | AD-11; PACK-UI | AUTHORING transitions Validate; §2.1 preview/validate allowed |

**Quoted backend AD-11:** “Addable **`publish_editor_draft`** checks draft ownership, `expected_revision`, reruns validation against that immutable fp1, and writes the local authoring-pack contribution. Preview/validate of unsaved buffer or a named revision stay legal and mint no JobHandle. Parent AD-30 **enable** remains compile identity.”

**Quoted UI AD-21:** “Addable `publish_editor_draft` authorizes the draft, checks `expected_revision`, revalidates the immutable fp1, and writes the local authoring-pack contribution. … First Run: `publish_editor_draft` **into the local authoring pack**, **enable that pack** (parent AD-30 compile-at-enable), grant, select that instance, then `dispatchInvoke`.”

**Quoted PACK-UI negatives:** “Invalid bytes, changed hash, stale expected_revision, or unauthorized draft → refuse.”

### Named inherited amendments

| ID | What it names |
| --- | --- |
| **AM-09** | Addable `publish_editor_draft` (and `save_editor_draft`). |
| **AM-07** | Drafts are not QMA AD-22 staging. |

No second enable machine. Export remains later parent AD-18 (AUTHORING Pack export row; PACK-UI; CLOSURE-J1-J5 deferral).

### Positive traces

T-BE-18: `publish_editor_draft` then AD-30 enable — validates immutable fp1; enable is compile identity. AUTHORING §2.0 complete first-Run path steps 4–8: publish → enable → grant → select instance → `dispatchInvoke`. TRACE-MATRIX ML compare: “Run = `dispatchInvoke` of template `start` **after local pack enable**. Publish-into-pack is not enough.”

### Negative traces

| Attempt | Result | Where |
| --- | --- | --- |
| Invalid bytes / changed hash / stale expected_revision / unauthorized draft | refuse | PACK-UI; CLOSURE-J1-J5; T-BE-18 must-not “client-only validation” |
| Run naming only `editor_draft_id` or `editor_revision` | `draft_not_runnable` | AUTHORING §2.1; T-BE-18 |
| Treat publish as compile identity | forbidden | AUTHORING §2.1; AD-11 |
| Gate first Run on parent AD-18 export | forbidden | AUTHORING §2.1 |

### Residual wording (not High)

AUTHORING **§2.2** still says: “Publish into the local authoring pack requires a **currently valid** validation of the hash being published. Re-validate is explicit.”

Joint-review J4 allowed **no** mandatory extra durable validation record and said publication **may rerun** validation against immutable bytes. Live AD-21 / publish row / PACK-UI all bind **revalidation inside `publish_editor_draft`**. §2.2 is readable as **chrome**: the operator’s prior Validate click is invalidated when bytes change, matching first-Run step 3 then step 4. It is **not** a second backend record. Documentation Factory should say that the durable gate is the command’s revalidation of the immutable fp1, and that §2.2 is client invalidation of a stale Validate label.

---

## J5 — Remote artifact transfer — **closed**

**Joint-review required result.** One supported source-to-destination route and its reachability condition, **or** explicit recorded reachable TLS plus typed refusal of unsupported topology. Never silently expose loopback or fall back to local execution. Bind ticket issuance/claim to authorized destination identity and placement revision. Explain how destination receives the work. Name how verified fp1/byte-count completion is durably reported and queried. Invoke refuses until that destination has verified complete bytes. Daemon sole-writer; source-local completeness on failure.

### Choice (live)

`transfer_artifact` issues a ticket **only** when the source daemon origin is **recorded reachable TLS** on the destination allowlist. Default loopback → typed `source_unreachable`. Ticket binds dest machine identity + placement revision + exact machine `credential_ref` audience. Dest authors `transfer_complete`. Invoke refuses until ticket `complete`. Never silently expose loopback. Never fall back to local invoke.

### Evidence in both packets

| Claim | Backend | UI |
| --- | --- | --- |
| Topology + typed refuse | `ARTIFACTS-AND-TRANSFER.md` Transfer topology; spine **AD-9** | UI **AD-22**; `LIBRARY-AND-ATTACHMENTS.md` §3.2 |
| Ticket audience + dest ack | ARTIFACTS Ticket / Completion; T-X-01..05 | LIBRARY §3.2 Ticket / Destination / Completion / Failure |
| Invoke waits | AD-9; ARTIFACTS “Invoke on that placement refuses until ticket `complete`.” | AD-22; LIBRARY Completion row; TRACE Local file, remote job |

**Quoted backend AD-9:** “`transfer_artifact` (operator, durable `command_id`) issues `artifact_transfer_ticket` only when the **source daemon origin is recorded reachable TLS** that the destination environment’s network allowlist can dial. Default loopback is **not** a remote route: typed `source_unreachable`. Never silently expose loopback. Never fall back to local invoke. Ticket binds `ticket_id`, source origin, fp1, byte count, operator/`product_session_ref`, destination environment identity + placement revision, and the **exact machine `credential_ref` audience**.”

**Quoted UI AD-22:** “Remote execution requires an **explicit transfer** to that placement: `transfer_artifact` issues a ticket only when the source daemon origin is **recorded reachable TLS** the destination can dial; default loopback is typed `source_unreachable`. Destination-authored `transfer_complete` is the verified completion ack. Invoke on that placement refuses until the ticket is `complete`.”

**Quoted LIBRARY §3.2:** “A remote environment **cannot** dial `127.0.0.1` on the laptop. `transfer_artifact` therefore **refuses** typed `source_unreachable` unless the source daemon origin is **recorded reachable TLS** on the destination environment’s network allowlist. Never silently expose loopback. Never fall back to local invoke.”

**How destination receives work (live):** “Notify the already-authenticated destination control connection (worker dial-out to **its** daemon; that daemon then pulls the recorded source origin). Only that audience may `GET /artifacts/<fp1>` with `X-QMX-Transfer-Ticket`.” (ARTIFACTS Ticket; LIBRARY Destination row.)

**Completion query/report (live):** dest authors addable `transfer_complete` `{ticket_id, fp1, byte_count}`; ticket states `issued | notified | claimed | complete | failed | expired`; lost ack retries the same ids; source returns prior complete (ARTIFACTS Completion; T-X-05).

### Named inherited amendments

| ID | What it names |
| --- | --- |
| **AM-05** | Authenticated HTTP PUT `/artifacts/stage` is a byte channel, not invoke, not a fourth family, not a BFF. |
| **AM-06** | Ticket + dest-audience pull from **recorded reachable TLS**; `source_unreachable` on loopback-only; dest-authored `transfer_complete`. Daemon never dials in. |
| **AM-09** | Addable `transfer_artifact`, `transfer_complete`. |
| **AM-13** | Authenticated `GET /artifacts/<fp1>` with transfer ticket is the machine byte pull. |

### Positive traces

- T-X-01 / T-BE-15: recorded TLS source + matching dest audience → complete ack → invoke allowed.
- T-X-05: lost `transfer_complete` → retry same ids → one complete ticket.
- Same-daemon instance: no transfer (ARTIFACTS; LIBRARY last paragraph of §3.2).

### Negative traces

| ID | Intent |
| --- | --- |
| T-X-02 | Loopback-only source → `source_unreachable`; no local fallback invoke |
| T-X-03 | Wrong dest credential → GET refuse |
| T-X-04 | Hash mismatch / interrupt → dest incomplete deleted; invoke refuses |

Failure leaves source local-complete fp1 (AD-9; LIBRARY Failure row).

### Deferrals (honest, not J5 holes)

- How the operator **records** a non-loopback TLS origin (host config UX) is an implementation story; the refusal class is bound (CLOSURE-J1-J5).
- No separately named `get_artifact_transfer` query. Durable ticket projection + dest ack + invoke-until-complete is the bound report path. A snapshot query name can wait for stories.
- Dest-offline at `issued` (notification before worker reconnect) is not fully tabled. Claim remains audience-bound GET; ticket can expire. Residual, not a loopback-pull hole.

---

## Small reconciliations — **closed as candidate**

These were bounded contract clarifications in REVIEW.md / GROK-FOLLOWUP.md, not a new design cycle.

| Item | Binding | Backend evidence | UI evidence |
| --- | --- | --- | --- |
| Provider vs shell | Shell = host start + TTL + pair + initialize. Provider needs an already-stored allowlisted ref. Secrets stay off the page. | `PROVIDER-AND-COMPAT.md` Shell versus provider; AD-12; T-BE-21 must-not “provider implied ready” | TRACE first-run: “Shell launch (`qmb host start` + pair) is **not** provider readiness.” External provision prerequisite. |
| PackUiRequest read-back | Addable `get_pack_ui_request` by `instance_id` + `availability_revision` | AD-10; **AM-16**; PACK-UI §PackUiRequest | UI AD-15; VIEW-AND-PACK-CONTRACT §3 |
| Mailbox write authorization | `send_message` **and** `list_mailbox` require connection principal == session principal. No GrantRecord for ordinary chat. | AD-7; `MAILBOX-AND-DELIVERY.md` Admission; T-BE-08 | UI AD-18; CHAT §1.1 last paragraph; TRACE Home send |
| Stream demultiplexing | UI CHAT remains controlling; thread bound to `psess:`; no reroute on app switch | MAILBOX: “UI stream demultiplexing … remains UI CHAT law and is carried into wire stories.” | CHAT T-CH-03 / T-CH-04; identities thread derivation |
| Cancel / headless | `originating_product_session_ref` **optional**; omitted on headless; exact handle/run/attempt fences; Story 36.5 remains | AD-8; `CANCEL-AND-HANDLES.md`; **AM-04**, **AM-14**; T-BE-10..12 | UI AD-23; TRACE cancel contract |
| Durable-reference naming | Envelope/handle pointers use `_ref`. ProductSession own id stays `product_session_id`. Exception list **unchanged**. | **AM-14**; AD-7/AD-8; PARENT map §C | CHAT identities table: “Mailbox Envelope field is `product_session_ref` (AM-14). Own identity of this row stays `product_session_id`.” |
| Host stop/recovery mechanics | QMB owner, stable root, sole writer, close vs stop, local vs remote already fixed. Signal/timeout/PID-safe lock recovery → stories | HOST-LIFECYCLE Data root and lock; AD-6 | BOOTSTRAP §8 / §4.4 |
| Numeric policies / scaffold | TTL and byte limits need preconditions, not invented numbers | AD-4 no TTL number; DEPENDENCY-MAP artifact max-bytes row “no number here” | TRACE Performance budgets unfrozen |

**Quoted AM-14:** “Use **`product_session_ref`** and **`originating_product_session_ref`**. Do not add those old names to the exception list. ProductSession **own** identity stays `product_session_id`.”

QMA spine conventions (parent) keep exactly ten named `_ref`-law exceptions; this sitting does not widen them.

---

## Live-field scan (defect rule)

Rule given to this reviewer: if UI still says `pairing_session_id` or `originating_psess` or `Envelope.product_session_id` as the **live** field (excluding historical `reviews/` and old memlog lines), that is an open defect.

| Identifier | Live UI law files | Verdict |
| --- | --- | --- |
| `pairing_session_id` | Only `.memlog.md` (old R2 decision) and `reviews/` | **not live** |
| `originating_psess` | Only `.memlog.md` (old R7 decision) and `reviews/` | **not live** |
| `Envelope.product_session_id` | Live CHAT: “Mailbox Envelope field is `product_session_ref` (AM-14).” “Key for product chat: `Envelope.product_session_ref`.” | **not live** |
| `product_session_id` as ProductSession **own** id | CHAT identities; TRACE command_id namespace `(product_session_id, principal, command_id)`; VIEW forbidden keys on PackUiRequest DTO | **correct own-identity use**, not an Envelope field |

Backend live law matches. Old names appear in AM-14 as the **conflict being renamed**, in `research/00` inspect notes, and in historical `reviews/` — not as current field names.

---

## Amendments inventory (no silent parent rewrite)

Every inherited conflict is named. AM-01..AM-16 in `PARENT-AMENDMENT-MAP.md`. Hold vs continue in `DEPENDENCY-MAP.md` does not renumber Epics 60–65.

| AM | Inherited conflict | Local ADs |
| --- | --- | --- |
| AM-01 | QMA AD-5/15/24; Story 41.4 unauthenticated bind | AD-5 |
| AM-02 | QMA AD-20 Envelope members | AD-7 |
| AM-03 | QMA AD-6/8; Story 42.2 closed projection list | AD-4, AD-9, AD-11 |
| AM-04 | QMA AD-17 / parent AD-26 / Story 57.3 handle **record** (states closed) | AD-8 |
| AM-05 | Three CT-40 families vs PUT bytes | AD-9, AD-15 |
| AM-06 | Story 41.4 never-dials-in vs remote pull | AD-9 |
| AM-07 | QMA AD-22 one RefinementProposal — **non-amendment** | AD-11 |
| AM-08 | Epic 41.1 addable query `list_mailbox` | AD-7 |
| AM-09 | Addable commands cancel/transfer/save/publish/complete | AD-8, AD-9, AD-11 |
| AM-10 | QMB `COMMAND_GROUPS` host verbs | AD-6, AD-17 |
| AM-11 | `credential_ref` authenticate-before-protocol vs browser pairing | AD-4, AD-5 |
| AM-12 | Mailbox send collision journal-lifetime | AD-7 |
| AM-13 | Authenticated renew + artifact GET families | AD-5, AD-9, AD-15 |
| AM-14 | QMA `_ref` law vs Envelope/handle pointer names | AD-7, AD-8 |
| AM-15 | First operator host-control outside the wire | AD-17 |
| AM-16 | Addable `get_pack_ui_request` | AD-10 |

Section B reuses kit/UI named amends (optional `app_instance_id`, `caller_kind`, `copilot_profile`) without re-authoring. Section C explicit non-amendments include: no sixth COMP, no new CT, no `ui_view` contribution point, Envelope `instance_id` still required on invoke, JobHandle states unchanged, cookie session refused, broker allowlist prefixes unchanged, `_ref` exception list unchanged.

---

## Remaining deferrals (not High, not J1–J5 holes)

From live CLOSURE-J1-J5 + this pass:

- Pairing TTL duration number; proof-token entropy.
- Ordinary supervisor PID/signal mechanics.
- Native/QMB write-once helper for provider secrets.
- Distributable pack export (parent AD-18 later).
- Implementation-level DTO field lists beyond named commands.
- How the operator records a non-loopback TLS origin (UX); refusal class is bound.
- UI BOOTSTRAP §6 sequence diagram omits `configure pairing-ttl` (bound elsewhere).
- AUTHORING §2.2 “currently valid validation” chrome sentence vs command revalidation (bound in AD-21 / PACK-UI).
- No named transfer-ticket snapshot query (ticket projection + dest ack + invoke gate are bound).
- `initialize` capability advertisement omits `save_editor_draft` / `transfer_complete`.
- Historical `reviews/` and memlog still use pre-amendment field names — leave them; they are not law.
- `CLOSURE-EVIDENCE.md` cites `reviews/gate-j1j5-summary.md`, which is **not** in the tree. Hygiene only.
- Tests unexecuted. No Reticle pass. No installed-product run.

---

## Closure decision

J1–J5 are **closed as candidate** in both packets. Small reconciliations are bound. Origin-only issuance remains closed. Layouts, Svelte/TypeScript, headless/visual, and Epics 60–65 were not reopened. No remaining High.

Recommended next stage (unchanged from the joint review): **one integrated Documentation Factory pass → coordinated epic/story amendments and additions → software-factory execution**. This sitting still starts none of those.
