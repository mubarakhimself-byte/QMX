---
name: J1–J5 closure map
sitting: architecture-QMX-UI-BACKEND-2026-09-24
date: 2026-09-24
status: candidate — Codex closure review next
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
---

# J1–J5 closure map

Joint-review findings from `workroom/qmx-ui-backend-joint-review-2026-09-24/REVIEW.md`. Origin-only issuance (R2) stays closed. Layouts, Svelte/TypeScript, visual/headless, and Epics 60–65 stay. Tests unexecuted. Inspect SHA unchanged.

## Verdicts

| ID | Finding | Binding | Status |
| --- | --- | --- | --- |
| J1 | First operator on a clean install | Local host-control under OS user + `QMA_DAEMON_ROOT`; daemon mints operator principal on empty start; TTL required before issue | **closed as candidate** |
| J2 | Pairing bearer custody and lifecycle | `pairing_proof` vs `pairing_record_id`; hash-only persistence; confirm once; rotate/expiry/revoke/recovery | **closed as candidate** |
| J3 | One durable draft-id issuer | Daemon issues `editor_draft_id` on first save; UI `client_draft_correlation` only | **closed as candidate** |
| J4 | Validated publication | Addable `publish_editor_draft`; AD-30 enable remains compile identity | **closed as candidate** |
| J5 | Reachable artifact transfer | Recorded TLS source or `source_unreachable`; dest-authored `transfer_complete`; invoke waits | **closed as candidate** |

## J1 — First operator bootstrap

**Choice.** Trust root is the OS user that owns `QMA_DAEMON_ROOT` plus a daemon-minted `host_control` token (owner-only ACL) on a **loopback host-control channel**. That channel is not CT-40, not `/pair/*`, and not a provider `cred://`. Shape of a ref is not proof.

**Evidence**

| Claim | File / section |
| --- | --- |
| Trust root, empty-root mint, TTL before issue, recovery, remote SSH-there | `HOST-LIFECYCLE.md` §Trust root; clean-install trace; negatives |
| AD | backend `ARCHITECTURE-SPINE.md` AD-17, AD-6 |
| Amendment | `PARENT-AMENDMENT-MAP.md` AM-15 |
| UI wording | UI `BOOTSTRAP-AND-AUTH.md` locked defaults, §5.3, §12 verbs; UI AD-19 |
| Allowlist not widened | `PROVIDER-AND-COMPAT.md`; AM hold on `qma-core` prefixes |

**Positive trace.** Empty per-user root → `qmb host start` (operator principal + `host_control`) → `qmb host configure pairing-ttl` → `/pair/start` → `qmb host pair <code>` → `/pair/confirm` → `pairing_proof` once → `initialize`. T-BE-23.

**Negative traces.** Forged `cred://models/…` as login → refuse. Unauthorized OS user (cannot read `host_control`) → refuse. Remote caller without host-control → refuse. `/pair/confirm` before TTL set → refuse issue.

**Deferral.** Exact TTL duration is operator-supplied; this sitting mints no number. Stale-PID lock recovery is an implementation story.

## J2 — Pairing credential custody

**Choice.** `pairing_proof` is an RFC 6750 bearer. `pairing_record_id` is the nonsecret row. Journal stores `proof_fp1` only. Confirm returns the proof **once**. Retry is `already_issued`. Lost confirm → re-pair. Renew rotates (new proof, old revoked, old WS closed). Expiry closes WS. Origin revoke is a journal-ordered cutoff.

**Evidence**

| Claim | File / section |
| --- | --- |
| Two names, redaction, lifecycle table T-P-01..10 | `PAIRING-AND-ADMISSION.md` §§1–4 |
| AD | backend AD-3 (issuance preserved), AD-4, AD-5, AD-14 |
| Amendment | AM-01, AM-03, AM-11 |
| UI wording | UI `BOOTSTRAP-AND-AUTH.md` locked defaults, §5.3–5.6, failure matrix, tests; UI AD-19 |

**Positive traces.** T-P-02 confirm once; T-P-04 renew rotate; T-BE-02 / T-BE-24.

**Negative traces.** T-P-01 Origin-only; T-P-03 second confirm; T-P-05 TTL; T-P-06 origin revoke; T-P-07 / T-BE-25 journal leak; T-P-10 lost confirm.

**Deferral.** Entropy/length of the proof token is an implementation story (must be unguessable and WS-token-safe).

## J3 — Draft identity

**Choice.** Daemon is the sole durable `editor_draft_id` issuer. First `save_editor_draft` omits the id. Optional `client_draft_correlation` recovers lost first-save ack. Subsequent saves require durable id + `expected_revision` = current head fp1.

**Evidence**

| Claim | File / section |
| --- | --- |
| Issuer table | `PACK-UI-AND-AUTHORING.md` §Draft identity |
| AD | backend AD-11 |
| UI wording | UI AD-21; `AUTHORING-AND-ML.md` locked defaults, identities, transitions 2.0 / 2.1a |

**Positive traces.** First save returns `{editor_draft_id, editor_revision=fp1}`; lost-ack retry with same correlation returns the same id. T-BE-17.

**Negative traces.** First save that *supplies* a client-minted durable id is not the issuer path. Stale CAS → typed conflict. T-BE-17.

## J4 — Validated publication

**Choice.** Addable `publish_editor_draft` checks ownership, `expected_revision`, revalidates the immutable fp1, and writes the local authoring-pack contribution. No mandatory extra validation record. Unsaved preview/validate stay legal. Parent AD-30 **enable** remains compile identity.

**Evidence**

| Claim | File / section |
| --- | --- |
| Command steps | `PACK-UI-AND-AUTHORING.md` §Publication |
| AD | backend AD-11 |
| Amendment | AM-09 |
| UI wording | UI AD-21; `AUTHORING-AND-ML.md` publish row + first-Run path |

**Positive traces.** T-BE-18 publish then enable.

**Negative traces.** Invalid bytes / stale hash / unauthorized draft → refuse. Run naming only `editor_draft_id` → `draft_not_runnable`. Treat publish as compile identity → forbidden.

## J5 — Artifact transfer

**Choice.** `transfer_artifact` issues a ticket only when the source daemon origin is recorded reachable TLS on the destination allowlist. Default loopback → typed `source_unreachable`. Ticket binds dest machine identity + placement revision + exact machine `credential_ref` audience. Dest authors `transfer_complete`. Invoke refuses until ticket `complete`. Never silently expose loopback. Never fall back to local invoke.

**Evidence**

| Claim | File / section |
| --- | --- |
| Topology, ticket, completion, T-X-01..05 | `ARTIFACTS-AND-TRANSFER.md` |
| AD | backend AD-9 |
| Amendment | AM-05, AM-06, AM-09 |
| UI wording | UI AD-22; `LIBRARY-AND-ATTACHMENTS.md` §3.2 |

**Positive traces.** T-X-01 recorded TLS + matching audience → complete ack → invoke allowed. T-X-05 lost ack retry.

**Negative traces.** T-X-02 loopback `source_unreachable`; T-X-03 wrong dest credential; T-X-04 hash mismatch / interrupt.

**Deferral.** How the operator records a non-loopback TLS origin (host config UX) is an implementation story; the refusal class is bound.

## Small reconciliations

| Item | Binding | Evidence |
| --- | --- | --- |
| Provider vs shell | Shell = host start + TTL + pair + initialize. Provider needs an already-stored allowlisted ref | `PROVIDER-AND-COMPAT.md`; UI TRACE first-run row |
| PackUiRequest read-back | `get_pack_ui_request` by `instance_id` + `availability_revision` | backend AD-10; AM-16; UI AD-15; `VIEW-AND-PACK-CONTRACT.md` §3 |
| Mailbox write authorization | `send_message` and `list_mailbox` require principal == session principal | backend AD-7; `MAILBOX-AND-DELIVERY.md`; UI AD-18; `CHAT-AND-HISTORY.md` §1.1 |
| Cancel / headless | `originating_product_session_ref` optional; omitted on headless; exact handle/run/attempt fences | backend AD-8; `CANCEL-AND-HANDLES.md`; UI AD-23 |
| Durable-reference naming | Envelope/handle pointers use `_ref`; ProductSession own id stays `product_session_id`; exception list unchanged | AM-14; UI CHAT identities; backend AD-7/AD-8 |

## Preserved

- Origin-only issuance closed (backend AD-3; UI AD-19).
- Storyboard layouts, Svelte/TypeScript, visual and headless capabilities.
- Epics 60–65 not rewritten. `PluginManifest.copilot_profile` stays Epic 60 sibling.
- Credential-broker allowlist prefixes unchanged.

## Gate fixes applied after independent review (same sitting)

Origin-revoke includes confirmed-unconsumed pendings. Cloned tab reconnects (renew is not the clone path). Pairing TTL is host-control exclusive. `local_operator` is on AM-03. Mailbox principal check runs only when `product_session_ref` is present. IndexedDB forbidden for the proof. First save that supplies `editor_draft_id` refuses. `get_editor_draft_head` named (AM-17). `initialize` advertises `save_editor_draft` / `transfer_complete`; `stage_artifact` means PUT. Missing `stage_max_bytes` refuses PUT. OPTIONS catalogue is the AD-15 HTTP routes. UI AUTHORING §2.2 chrome label vs command revalidation.

## Remaining deferrals (not J1–J5 holes)

- Pairing TTL duration number; proof-token entropy; host-control IPC encoding.
- Ordinary supervisor PID/signal mechanics.
- Native/QMB write-once helper for provider secrets.
- Distributable pack export (parent AD-18 later).
- Implementation-level DTO field lists beyond named commands.

## Honesty

No live daemon, no executed tests, no installed-product run. Candidate ≠ operator acceptance. Documentation Factory, epic rewrite, and factory execution are out of this sitting.
