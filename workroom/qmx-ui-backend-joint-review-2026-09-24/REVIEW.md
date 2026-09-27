# QMX joint UI/backend architecture review — 24 September 2026

**Verdict: ready after listed corrections. Do not start Documentation Factory yet.**

The previous R2 Origin-only issuance defect is corrected: a remembered Origin cannot issue a fresh browser credential; privileged confirmation or existing valid proof is required. The wider backend packet now names the wire, journal, mailbox, artifact and authoring owners and distinguishes existing plans from absent implementation. However, five contracts still allow incompatible or unsafe implementations. Resolve J1–J5 in the existing backend-delta session, reconcile their affected UI text, then return for focused closure review. This does not require another broad UI design cycle.

## Inputs and method

Reviewed together: `architecture-QMX-UI-BACKEND-2026-09-24` and the reconciled `architecture-QMX-UI-2026-09-23`. Preserved 24 backend files and 56 UI files with SHA-256 hashes before review. The prior UI snapshot is retained separately. Exactly nine UI files changed since that snapshot, matching the stated reconciliation; no UI files were removed. Layout, component, authoring, Library and QA companions were not changed in that reconciliation.

Main baseline: `92279dfe43922d60fabe38e29284ca52956ab75c`. Integration/inspect baseline: `34c148be404a375cbfd79fd4ce6997452e4f1d20`. Planned epics remain requirements, not proof of delivered behavior. Narrow code inspection corroborated authentication and credential-allowlist facts; this is not a broad backend code audit.

Three independent gpt-5.6-sol reviewers covered admission, state/data, authoring and technical currency. Root reviewed parent amendments, dependencies, scope, the actual UI delta and finding severity. Both structural spine lints pass with zero findings; that does not settle the semantic contracts below. See [verification](evidence/verification.json) for the final frozen/live input comparison.

## Required corrections

### J1 — High: establish the first operator without assuming an already authenticated operator

**Evidence:** backend [ARCHITECTURE-SPINE](evidence/backend-as-reviewed/ARCHITECTURE-SPINE.md), lines 104, 110 and 116; [HOST-LIFECYCLE](evidence/backend-as-reviewed/HOST-LIFECYCLE.md), line 19; [PROVIDER-AND-COMPAT](evidence/backend-as-reviewed/PROVIDER-AND-COMPAT.md), lines 10–20. UI [BOOTSTRAP-AND-AUTH](evidence/ui-as-reviewed/BOOTSTRAP-AND-AUTH.md), lines 141–154, already admits the current authentication helper is a shape gate.

`confirm_pair` must enter an operator-authenticated wire and copy an existing allowlisted operator-login CredentialRef. But the declared allowlist contains model/inference, compute/sandbox, corpus/knowledge and telemetry categories, not an operator-login category. No first-install provisioning or proof-verification path is supplied. A well-shaped reference and a caller-selected principal class do not establish operator identity. The pairing TTL is also mandatory before issuance, so its initial configuration needs that same defined privileged path.

**Required result:** choose one initial trust root and show clean root → establish operator identity → configure required pairing policy → confirm pending browser → initialize. It may use a protected local operator control path or an explicitly provisioned transport credential; name its owner, actual proof verification, provisioning and recovery. A provider reference must not become a dummy login. Name any QMA/Story 41.4 amendment explicitly. Preserve QMB as the operator door and the daemon as sole writer.

**Closure evidence:** a valid clean-install trace and negative traces for a forged reference/principal, an unauthorized local caller, and a remote caller without the required proof. No implementation is required at this gate.

### J2 — High: treat pairing proof as a credential and close its lifecycle

**Evidence:** backend [ARCHITECTURE-SPINE](evidence/backend-as-reviewed/ARCHITECTURE-SPINE.md), lines 104 and 187; [PAIRING-AND-ADMISSION](evidence/backend-as-reviewed/PAIRING-AND-ADMISSION.md), lines 46–79 and 100–106; [PARENT-AMENDMENT-MAP](evidence/backend-as-reviewed/PARENT-AMENDMENT-MAP.md), AM-11. UI [BOOTSTRAP-AND-AUTH](evidence/ui-as-reviewed/BOOTSTRAP-AND-AUTH.md), line 185 and the expired/revoked row near line 315.

The value of `pairing_session_id` is the bearer proof for HTTP and WebSocket access, yet the packet explicitly calls it nonsecret, persists it as a journal join key, and allows it in traces. Renaming a credential to avoid the forbidden JSON keys `token` or `bearer` does not protect it. A disclosure of the live value can convey the authority of the session. This follows the bearer model described by [RFC 6750](https://datatracker.ietf.org/doc/html/rfc6750#section-1.2); [OWASP logging guidance](https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html#data-to-exclude) likewise excludes raw session/access credentials from logs.

The same contract also leaves confirmation replay and renew/revoke ordering unresolved. Backend prose lets an already-open socket remain until detach or revoke, whereas the UI says expiry drops it. Builders can disagree about whether renew rolls expiry, whether an approved pending request can issue repeatedly, and whether origin revocation leaves unclaimed approvals able to issue again.

**Required result:** separate a nonsecret record identity from the secret proof. Bind proof generation/encoding, protected custody, journal representation, redaction of Authorization and `qmx.pair.*`, and safe diagnostics. A verifier/hash plus lifecycle metadata in the journal is a suitable approach; choose a coherent issuance/recovery design rather than requiring retrieval of a raw proof the server no longer stores. Add a compact state table for confirm retries/lost responses, renewal, expiry on an active connection, session revoke, origin revoke, restart and concurrent renew/revoke. Explicit re-pair after an unrecoverable lost issuance is acceptable if stated consistently. Do not require OAuth, a cookie alternative or a new identity platform.

**Closure evidence:** no reusable proof in logs/journal/diagnostics; expired or revoked proof cannot continue issuing commands on an existing socket; replay and renew/revoke traces have one outcome. Cross-check the UI prose and AM-11 rather than fixing only the spine.

### J3 — High: reconcile draft creation and first-save identity

**Evidence:** UI [AUTHORING-AND-ML](evidence/ui-as-reviewed/AUTHORING-AND-ML.md), lines 108–111; backend [ARCHITECTURE-SPINE](evidence/backend-as-reviewed/ARCHITECTURE-SPINE.md), line 146; [PACK-UI-AND-AUTHORING](evidence/backend-as-reviewed/PACK-UI-AND-AUTHORING.md), line 33.

The UI mints `editor_draft_id` before first save; the backend mints it on first save. The backend's only named save request already includes that id. Neither packet defines a provisional-to-durable mapping or a create form. These are incompatible identity owners, not an implementation preference.

**Required result:** choose one durable issuer and define first-save input/result, subsequent saves, lost-response reconciliation and stale CAS. If the daemon issues the durable id, distinguish any client provisional correlation and return the durable id with `editor_revision`. Preserve fp1 revision identity and `expected_revision`; changing bytes must create a new saved revision. Reconcile both candidate packages.

**Closure evidence:** create → first save → lost ack/recovery → subsequent save, plus two restored clients saving against the same old head. No duplicate working copy from a routine retry.

### J4 — High: bind the validated-revision-to-local-pack publication transition

**Evidence:** UI [AUTHORING-AND-ML](evidence/ui-as-reviewed/AUTHORING-AND-ML.md), lines 110–113 and 162–178; backend [PACK-UI-AND-AUTHORING](evidence/backend-as-reviewed/PACK-UI-AND-AUTHORING.md), lines 33–43; [PARENT-AMENDMENT-MAP](evidence/backend-as-reviewed/PARENT-AMENDMENT-MAP.md), AM-09; [DEPENDENCY-MAP](evidence/backend-as-reviewed/DEPENDENCY-MAP.md), authoring rows.

The UI requires a valid verdict for the exact revision hash and CAS at publication. The backend names draft save and then reuses pack enable, but never binds the mutation that checks those conditions and writes the contribution into the local authoring pack. A browser builder can rely on client validation while a backend builder only validates later at enable. Both miss the agreed publication gate.

**Required result:** name the existing or addable backend publication transition, its owner, draft authority, expected head, immutable fp1, validation and local-pack write/result. A separate durable validation record is not mandatory: publication can rerun validation against immutable bytes. Keep preview/validate legal before enable, including the agreed unsaved-buffer mode. Keep parent AD-30 enable as compile identity; do not invent a second enable machine.

**Closure evidence:** invalid bytes, changed hash, stale publication, and an unauthorized draft refuse; a valid saved revision publishes, enables, receives a grant, selects one instance and invokes. Export to another machine remains later.

### J5 — High: make remote artifact transfer reachable, authorized and observable

**Evidence:** backend [ARTIFACTS-AND-TRANSFER](evidence/backend-as-reviewed/ARTIFACTS-AND-TRANSFER.md), lines 29–43; [ARCHITECTURE-SPINE](evidence/backend-as-reviewed/ARCHITECTURE-SPINE.md), line 134 and its operational envelope; [HOST-LIFECYCLE](evidence/backend-as-reviewed/HOST-LIFECYCLE.md), placement section. The UI's local-first staging and explicit remote transfer remain binding.

The default source is the workstation's loopback daemon, but the remote destination must pull directly from it. A VPS cannot reach the laptop through its own `127.0.0.1`. The inherited rule allows a deliberately configured TLS listener; it does not supply a tunnel or relay. The ticket is bound to fp1 and placement in prose, but the receiving machine's authenticated identity is not explicitly checked against that placement. No destination notification/claim or authoritative completion acknowledgement connects the transfer to the later remote-possession gate.

**Required result:** specify one supported source-to-destination route and its reachability condition. Either name an existing secure route or explicitly require a recorded reachable TLS source and refuse unsupported topology; never silently expose loopback or fall back to local execution. Bind ticket issuance/claim to the authorized destination identity and placement revision, explain how the destination receives the work, and name how verified fp1/byte-count completion is durably reported and queried. Preserve daemon sole-writer ownership and source-local completeness on failure.

**Closure evidence:** reachable successful transfer; unreachable laptop source; wrong destination credential; interrupted or hash-mismatched transfer; lost completion acknowledgement/restart; invoke refusing until the selected placement is verifiably complete. These may be architecture traces, not executed tests.

## Small reconciliations and reviewer adjudication

These do not justify a new design session. Resolve the small documentation ambiguities while amending J1–J5; carry mechanical details into the integrated Documentation Factory pass.

| Topic | Consolidated disposition |
| --- | --- |
| Provider first use | Reviewer opinions differ on gating. Partial shell readiness is already allowed, so lack of a browser secret writer is not itself a blocker. Explicitly distinguish clean-machine shell launch from provider readiness and name external credential provisioning as a prerequisite, or include a v1 privileged setup path. Keep secrets out of the page. |
| PackUiRequest read-back | Ingestion, sibling copilot_profile and grant ambiguity are coherent. Identify the existing or addable snapshot query and enabled-instance/availability-revision lookup so frontend and backend reference the same read contract. Do not turn it into a new contribution point. |
| Mailbox admission | Durable psess membership, replies, lookup and dedup improved. State the same authenticated-principal/session check for initial send as for history reads. No invoke GrantRecord is required for ordinary chat. This is a narrow admission clarification, not a chat redesign. |
| Stream demultiplexing | UI CHAT already binds the derived thread to psess and forbids rerouting deltas on app switch; inherited UI remains controlling. Its absence from the short backend companion is not alone a new blocker. Carry that invariant into wire stories. |
| Cancel and headless work | Preserve immutable handle/run/attempt checks and distinguish UI-originated handles from legacy/headless admissions without psess. The new field must not make headless QMB work impossible. Existing UI R7's race/no-op/cancel owner remains binding; missing repeated prose alone does not reopen it. |
| Durable reference naming | AM-02/AM-04 introduce product-session pointers named `product_session_id` and `originating_psess`. QMA's inherited cross-store reference convention has a closed exception list. Name the necessary exception amendment or reconcile the field names across both packets; do not leave a parent validator and the new record contract disagreeing. This is a small parent-map correction, not a new subsystem. |
| Host stop/recovery mechanics | QMB owner, stable root, sole writer, close versus stop and local versus remote are fixed. Signal choice, timeouts and PID-safe lock recovery belong in implementation stories, not a new architecture gate. |
| Numeric policies/scaffold | TTL and byte limits require explicit preconditions before first use; no need to invent performance numbers in this review. Unexecuted scaffold and runtime work are later proof obligations, not evidence of architecture failure. |

## Coverage and prior closure

| Dimension | Result |
| --- | --- |
| Original layout and purpose | Preserved: independent platform destinations; app-specific top navigation/widget space; optional right copilot; visual, headless and mixed capabilities. No adoption of rejected study 03 or LSE layout. |
| Prior UI R2 Origin-only finding | Closed specifically. J1/J2 concern newly elaborated backend authentication and lifecycle contracts. |
| Prior UI R1/R4/R8/R9 | Preserved: layout, manifest copilot_profile, honest provenance and build seed. |
| Prior UI R3/R7 | Core closure preserved, with narrow admission/headless clarifications above. No blanket re-opening. |
| Prior UI R5/R6 | Backend reconciliation still required by J3–J5; prior UI intent is the baseline, not evidence that the new backend realizes it. |
| Parent/planned epics | Correctly names proposed amendments and avoids duplicating Epics 60–65. Amend affected existing contracts and add only absent capabilities later. Planned work is not implementation proof. |
| Data and lifecycle ownership | Daemon ownership is generally clear; initial operator bootstrap, proof custody, publication and transfer still fail convergence. |
| Operational envelope | Local and recorded remote are explicit; transfer reachability needs J5. Tauri remains later, with no unsupported speed/build claim. |
| Technical currency | Browser CORS/HTTP choices are feasible per current Fetch/RFC sources. Existing frontend pins are unchanged and were reviewed earlier; no package-upgrade exercise was introduced. |
| Mechanical lint | Both pass, zero findings. |
| Runtime/clean-install testing | Unexecuted; no production-readiness or Reticle pass claimed. |

## Next gate

Send [GROK-FOLLOWUP](GROK-FOLLOWUP.md) to the existing backend-delta Grok session. Return both reconciled candidate packets with a J1–J5 closure map and explicit parent/dependency changes. After independent closure passes, the recommended route remains **one integrated Documentation Factory pass → coordinated epic/story amendments and additions → software-factory execution**. No downstream stage was started here and no active factory inputs were altered.
