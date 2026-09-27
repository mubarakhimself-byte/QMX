---
name: Closure evidence
sitting: architecture-QMX-UI-BACKEND-2026-09-24
date: 2026-09-24
status: candidate — joint review next
---

# Closure evidence

## Round-2 remaining condition

| Finding | Before this sitting | After |
| --- | --- | --- |
| R2 issuance | Origin-only auto-approve of a new `pairing_session_id` permitted | **Closed as candidate.** AD-3: QMB confirm of that pending request **or** authenticated `/pair/renew` with existing valid proof. Origin required, never sufficient. Negative/positive traces named. Repeated UI rows reconciled (`UI-CANDIDATE-CHANGELOG.md`). |
| Reload vs cold start | T-CH-06 / Home trace said “browser restart” over sessionStorage | **Closed as wording.** Same-tab reload restores pending state when present. Cold start uses `list_mailbox(product_session_id)` and never auto-resends. Cloned tab = copied proof + new live `producer_id`. |

## Preserved closed UI findings

R1 navigation, R3 chat/mailbox model, R4 pack/view, R5 authoring first Run, R6 PUT possession, R7 cancel starter-only, R8 candidate provenance, R9 Node pin — **unchanged** except the R2/recovery wording above.

## Backend sitting completeness vs supplement

| Supplement group | Companion | Class summary |
| --- | --- | --- |
| Epics 60–65 | DEPENDENCY-MAP §1 | already planned; PackUiRequest additional |
| Browser admission / transport | PAIRING-AND-ADMISSION | AM-01 issuance + carve-out |
| QMB host verbs | HOST-LIFECYCLE | AM-10 including pair-revoke |
| Conversation / mailbox | MAILBOX-AND-DELIVERY | Epic 46.4 + AM-02/AM-08 |
| Cancel | CANCEL-AND-HANDLES | AM-04/AM-09 |
| Artifacts | ARTIFACTS-AND-TRANSFER | AM-05/AM-06 pull plane |
| PackUiRequest / drafts | PACK-UI-AND-AUTHORING | AM-03/AM-07; no copilot_profile move |
| Provider setup | PROVIDER-AND-COMPAT | broker adoption gap; write helper deferred |
| Compat / installed product | PROVIDER-AND-COMPAT | AD-13/J-UI-13/14 |

## Limits

- Inspect SHA still `34c148be`. No live daemon, no tests executed, no installed-product run.
- Candidate ≠ operator acceptance.
- Documentation Factory, epic rewrite, and factory execution are **out of this sitting**.
- Mechanical spine lint is clean. Independent reviewers are under `reviews/` (`gate-summary.md`). Gate fixes for CORS OPTIONS, pairing join key, handle_id, transfer pull, and closed-list AM-ids were applied in this sitting.
