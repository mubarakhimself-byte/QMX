---
name: Closure evidence
sitting: architecture-QMX-UI-BACKEND-2026-09-24
date: 2026-09-24
status: candidate — Codex closure review next
---

# Closure evidence

## Round-2 remaining condition

| Finding | Before this sitting | After |
| --- | --- | --- |
| R2 issuance | Origin-only auto-approve of a new pairing proof permitted | **Closed as candidate (preserved).** AD-3: QMB confirm of that pending request **or** authenticated `/pair/renew` with existing valid proof. Origin required, never sufficient. |
| Reload vs cold start | T-CH-06 / Home trace said “browser restart” over sessionStorage | **Closed as wording (preserved).** Same-tab reload restores pending state when present. Cold start uses `list_mailbox(product_session_ref)` and never auto-resends. Cloned tab = copied proof + new live `producer_id`. |
| J1 first operator | Assumed existing authenticated operator CredentialRef | **Closed as candidate.** AD-17 host-control + empty-root mint. See `CLOSURE-J1-J5.md`. |
| J2 pairing custody | Pairing id treated as nonsecret journal key | **Closed as candidate.** `pairing_proof` vs `pairing_record_id`; hash-only; lifecycle table. |
| J3 draft issuer | UI and daemon both minted `editor_draft_id` | **Closed as candidate.** Daemon sole durable issuer. |
| J4 publication | Unnamed UI act | **Closed as candidate.** `publish_editor_draft`; AD-30 enable remains compile identity. |
| J5 transfer | Loopback pull from a VPS | **Closed as candidate.** Recorded TLS or `source_unreachable`; dest `transfer_complete`. |

## Preserved closed UI findings

R1 navigation, R3 chat/mailbox model, R4 pack/view, R5 authoring first Run, R6 PUT possession, R7 cancel starter-only, R8 candidate provenance, R9 Node pin — **intent preserved**. R3/R5/R6/R7 field names reconciled to `_ref` / daemon issuer / reachable transfer as in `CLOSURE-J1-J5.md`. Layouts, Svelte, Epics 60–65 unchanged.

## Backend sitting completeness vs supplement

| Supplement group | Companion | Class summary |
| --- | --- | --- |
| Epics 60–65 | DEPENDENCY-MAP §1 | already planned; PackUiRequest additional |
| Browser admission / transport | PAIRING-AND-ADMISSION | AM-01 issuance + carve-out; J2 custody |
| QMB host verbs | HOST-LIFECYCLE | AM-10/AM-15 including first operator + pair-revoke |
| Conversation / mailbox | MAILBOX-AND-DELIVERY | Epic 46.4 + AM-02/AM-08/AM-14 |
| Cancel | CANCEL-AND-HANDLES | AM-04/AM-09/AM-14 |
| Artifacts | ARTIFACTS-AND-TRANSFER | AM-05/AM-06 pull plane; J5 reachable TLS |
| PackUiRequest / drafts | PACK-UI-AND-AUTHORING | AM-03/AM-07/AM-16; J3/J4; no copilot_profile move |
| Provider setup | PROVIDER-AND-COMPAT | broker adoption gap; write helper deferred |
| Compat / installed product | PROVIDER-AND-COMPAT | AD-13/J-UI-13/14 |

## Limits

- Inspect SHA still `34c148be`. No live daemon, no tests executed, no installed-product run.
- Candidate ≠ operator acceptance.
- Documentation Factory, epic rewrite, and factory execution are **out of this sitting**.
- Mechanical spine lint and the J1–J5 reviewer gate are recorded under `reviews/` (`gate-j1j5-summary.md`). Historical first-pass reviews remain as prior evidence and were not rewritten.
