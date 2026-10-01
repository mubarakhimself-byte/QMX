---
name: R2 remaining-condition closure review
sitting: architecture-QMX-UI-BACKEND-2026-09-24
against: remaining UI R2 issuance rule (remembered Origin never issues pairing_session_id)
inspect: integration@34c148be404a375cbfd79fd4ce6997452e4f1d20
date: 2026-09-24
status: independent review — not operator-accepted
scope: live candidate law only; historical reviews/ are not law
tests: unexecuted
---

# Review — remaining UI R2 condition (pairing issuance)

**Question.** Is the remaining UI R2 condition actually closed in the reconciled UI candidate **and** the backend-delta spine?

**Required rule (this review’s gate).** A remembered Origin alone must never authorize issuance of a new `pairing_session_id`. Every new id requires **exactly one** of:

1. Fresh privileged QMB confirmation of **that** pending request, or
2. Explicitly authenticated renewal using existing valid proof.

Transport already closed by the earlier UI sitting (Bearer + WS subprotocols; cookies refused) is out of scope except where it would re-open issuance.

**Not in scope.** Implementation. Documentation Factory. Epic rewrite. Historical `architecture-QMX-UI-2026-09-23/reviews/` files (prior evidence, not live law). Code absence at inspect is honesty, not a remaining auto-approve path.

## Verdict

**CLOSED AS CANDIDATE.**

The remaining R2 issuance condition is closed in both live packets. Origin is required and never sufficient. Typed-URL second tab and Origin-known-without-proof both refuse a session. Same-tab reload reconnects with stored proof (not a new issuance). Cold start / closed tab has empty `sessionStorage` and must take the QMB path. Cloned/auxiliary tab with copied `sessionStorage` is existing proof, not Origin-only issuance.

Candidate ≠ operator acceptance. Tests unexecuted. Pairing HTTP is absent at `34c148be`. Those limits do not reopen Origin-only auto-approve.

## Disposition vs the gate

| Gate clause | Live law | Result |
| --- | --- | --- |
| Remembered Origin alone never issues a new `pairing_session_id` | UI AD-19; UI `BOOTSTRAP-AND-AUTH.md` locked defaults / §5.3 / §5.5 / failure matrix / `qmb host pair` contract; backend AD-3; `PAIRING-AND-ADMISSION.md` §1–§3 | **Met** |
| Path 1: fresh QMB confirm of **that** pending request | `POST /pair/start` → `qmb host pair <code>` → `POST /pair/confirm` returns `{pairing_session_id}` only if **that** `pending_id` is confirmed and Origin matches | **Met** |
| Path 2: authenticated renewal with existing valid proof | `POST /pair/renew` with `Authorization: Bearer pairing:<id>` + matching Origin; row unexpired unrevoked | **Met** |
| Negative trace | Backend AD-3; T-BE-01; T-P-01; T-P-09 | **Present** |
| Positive traces | T-BE-02 / T-P-02 (confirm); T-BE-03 / T-P-03 (renew); T-BE-04 / T-P-04 (revoked/expired refuse) | **Present** |
| Reload ≠ cold start | Backend AD-14; `PAIRING-AND-ADMISSION.md` §6; UI T-CH-06; UI TRACE-MATRIX Home recovery | **Met** |
| Remaining auto-approve path in live files | All live `auto-approve` / `Origin-only` sentences **refuse** the path | **None found** |

## 1. Required rule vs live spines

### 1.1 Backend-delta spine (law)

`architecture-QMX-UI-BACKEND-2026-09-24/ARCHITECTURE-SPINE.md` **AD-3 [USER]** is the issuance lock:

> A remembered Origin **never** authorizes issuance of a new `pairing_session_id`. Every new id requires **exactly one** of: (1) fresh privileged QMB confirmation of **that** pending request (`qmb host pair <code>` then POST `/pair/confirm`); or (2) an authenticated renewal that presents an existing **unexpired unrevoked** `pairing_session_id` matching that Origin (`POST /pair/renew` with `Authorization: Bearer pairing:<id>`). Origin match remains required and is never sufficient.

AD-3 also names the traces in the rule body: negative (Origin known, no valid proof, no fresh QMB confirm → no session, no CT-40); positive (newly confirmed pending → token; valid authenticated renewal → token; revoked or expired proof alone → refusal).

Companion `PAIRING-AND-ADMISSION.md` §1 restates the same two paths. The caller table is the operational form:

| Caller | Result |
| --- | --- |
| Known Origin, no valid proof, no QMB confirm | **No** `pairing_session_id`. **No** CT-40. `/pair/confirm` stays pending. WS upgrade refused. |
| Pending confirmed by QMB | Token issued. |
| Valid unexpired unrevoked Bearer on `/pair/renew` + matching Origin | New token issued. |
| Expired or revoked proof alone | Refusal. Client drops the id and starts `/pair/start` again. |
| Valid id from a **different** Origin | Refusal. |
| Arbitrary `cred://` as login | Refusal. |

§1 also binds the typed-URL second tab: empty `sessionStorage` → path 1. It does **not** auto-approve.

§2 states why Origin is not identity (RFC 6455 §10.1 Origin spoofing; WHATWG `sessionStorage` is per-tab). Auto-approving because “this Origin paired before” would issue an operator session to whoever can name that Origin. That sentence is a **refusal**, not a path.

§3 HTTP table: `/pair/confirm` **Does not: Auto-approve on Origin.** `/pair/start` does not issue a session. `/pair/renew` is on the **authenticated** table (Bearer required). Unauthenticated carve-out is start, confirm, OPTIONS only (backend AD-5 / AM-01). Renew is not in that carve-out.

### 1.2 Reconciled UI candidate (law)

`architecture-QMX-UI-2026-09-23/ARCHITECTURE-SPINE.md` **AD-19** now carries the same issuance sentence and cites backend-delta AD-3:

> **Issuance:** a remembered Origin never authorizes a new `pairing_session_id`; require fresh QMB confirm of that pending request or authenticated `/pair/renew` with an existing valid proof (backend-delta AD-3).

`BOOTSTRAP-AND-AUTH.md` is aligned, not a second dialect:

- Locked defaults — second tab: typed-URL tab POSTs `/pair/start` and needs **fresh QMB confirm of that pending request**. “A remembered Origin **never** issues a `pairing_session_id`.” Cloned/auxiliary tab that **copied** `sessionStorage` already holds proof and reconnects (or `/pair/renew`).
- §5.3 step 6 — issuance rule copied from backend AD-3. `/pair/confirm` before QMB confirm: pending, no session, no CT-40.
- §5.5 — typed-URL second tab: Origin **does not** auto-approve and **does not** issue a session. Cloned tab is existing proof, not the Origin-only path.
- Failure matrix **Second tab** Must not: Origin-only auto-approve.
- `qmb host pair` contract: a second tab on the same Origin still needs its own pending code and this confirm. Authenticated `POST /pair/renew` is the other issuance path. Origin-only auto-approve is refused. Does not: issue a session because Origin was remembered.
- Tests: Origin-only auto-approve refused; cloned tab with copied id reconnects.

`CHAT-AND-HISTORY.md` reconnect step 1 re-auths with the same `pairing_session_id` (Bearer + WS subprotocol) and maps internally to `credential_ref`. That is reuse of existing proof, not Origin-only issuance. The earlier two-proof fork (client-sent `credential_ref` vs `pairing_session_id`) is gone from this live reconnect list.

`TRACE-MATRIX.md` Reconnect (J-UI-06) matches: re-auth with same `pairing_session_id`; daemon maps internally to `credential_ref`.

`CHANGE-IMPACT.md` pairing row: Origin-only auto-approve **refused** (backend-delta AD-3).

`BACKEND-DEPENDENCIES.md` pairing row: Origin never sufficient; QMB confirm or authenticated `/pair/renew`. Unauthenticated carve-out does not extend past `/pair/start|confirm`.

`DECISIONS-AND-OPEN.md` C-BOOTSTRAP: “Origin never issues a pairing session.”

`CLOSURE-MAP.md` R2: issuance closed as candidate via backend-delta AD-3. Remaining risk is “pairing HTTP not in code” — inspect honesty, not a competing issuance rule.

## 2. Traces

### 2.1 Negative traces (Origin-only must fail)

These exist in live law:

| ID | Where | Intent | Must | Must not |
| --- | --- | --- | --- | --- |
| (unnamed in AD-3 body) | Backend AD-3 Rule | Origin known, no valid proof, no fresh QMB confirm | no `pairing_session_id`, no CT-40 | — |
| T-BE-01 | Backend `TRACE-MATRIX.md` | Origin-only issuance | pending, no `pairing_session_id`, WS refused | auto-approve because Origin is remembered |
| T-P-01 | `PAIRING-AND-ADMISSION.md` §8 | Origin known, no proof, no QMB confirm | no `pairing_session_id`, WS refused | — |
| T-P-09 | same | Non-browser client forging Origin without proof | same as T-P-01 | — |
| T-BE-07 Must-not | Backend `TRACE-MATRIX.md` | Cloned tab | treat copied id as proof; new `producer_id` if old live | Origin-only branch |
| UI bootstrap test “Second tab” | `BOOTSTRAP-AND-AUTH.md` §14 | Empty `sessionStorage` | `/pair/start` → QMB confirm → `/pair/confirm` yields id | Origin-only auto-approve refused |
| UI failure matrix **Second tab** | `BOOTSTRAP-AND-AUTH.md` §7 | Empty storage | fresh QMB confirm of **that** pending request | Origin-only auto-approve |

A builder following live law cannot mint a session from Origin match alone.

### 2.2 Positive traces (the two legal issuance paths, plus refusal of dead proof)

| ID | Where | Intent | Must | Must not |
| --- | --- | --- | --- | --- |
| T-BE-02 | Backend TRACE-MATRIX | Fresh confirm | token; no Set-Cookie | cookie or `cred://` login |
| T-P-02 | PAIRING §8 | QMB confirm then `/pair/confirm` | token; no Set-Cookie | — |
| T-BE-03 | Backend TRACE-MATRIX | Authenticated renew | new token same operator+Origin | renew without Bearer |
| T-P-03 | PAIRING §8 | Bearer renew + matching Origin | new token | — |
| T-BE-04 | Backend TRACE-MATRIX | Revoked/expired proof | refuse CT-40 | leftover id as operator |
| T-P-04 | PAIRING §8 | Revoked/expired | refuse; no CT-40 | — |
| T-P-05 | PAIRING §8 | Valid id, wrong Origin | refuse | — |
| T-BE-05 / T-P-06 | both | Same-tab reload | reconnect until TTL; no second pending code | force new pair |
| T-BE-06 / T-P-07 | both | Cold start empty storage | QMB path for new id; mailbox snapshot if `psess:` selected | auto-resend / auto session |
| T-BE-07 / T-P-08 | both | Cloned tab copied id | treat as proof; new `producer_id` if old live | Origin-only branch |

UI `BOOTSTRAP-AND-AUTH.md` §14 adds the same intents (bootstrap HTTP before/after QMB confirm; second tab; same-tab reload). UI `TRACE-MATRIX.md` does **not** duplicate Origin-only pairing rows; the backend packet owns those acceptance rows and says so (“UI `TRACE-MATRIX.md` remains the chrome/issuer matrix”). That split is not a second legal host.

## 3. Reload vs cold-start wording

The prior residual was T-CH-06 / Home trace promising “browser restart” restoration from `sessionStorage`. HTML `sessionStorage` does not survive a closed tab / full browser quit.

Live wording now splits three recoveries:

| Event | `sessionStorage` | Pairing | Chat pending |
| --- | --- | --- | --- |
| Same-tab **reload** (same page session) | Survives | Reconnect with stored `pairing_session_id` until expiry. **Not a new issuance.** | Pair lookup; do not resend |
| **Closed tab** / cold start / full quit | **Gone** | New pair requires QMB confirm (path 1) unless some other tab still holds proof | `list_mailbox(product_session_id)` if `psess:` selected; never auto-resend; pre-ack correlation unavailable |
| **Auxiliary / cloned** tab | **Copied** (WHATWG) | Copied id **is existing proof**. Reconnect or `/pair/renew`. Not Origin-only issuance | Copied pending triple is a hint; do not keep a live sibling `producer_id` |

Bindings:

- Backend **AD-14 [USER]** — the three recoveries above. Prevents “promising browser-restart restoration from sessionStorage.”
- `PAIRING-AND-ADMISSION.md` §6 — same table.
- `MAILBOX-AND-DELIVERY.md` Recovery (AD-14) — reload = pair lookup, no resend; empty storage = full snapshot only, no auto `send_message`.
- UI `CHAT-AND-HISTORY.md` **T-CH-06** title is now “Lost ack, then same-tab reload / restored page session (no resend).” Step 2 names **Cold start / closed tab:** empty storage — skip to empty-storage branch; do not claim the pending triple survived. Forbidden list: no resend after lost ack, same-tab reload, **or cold start**.
- UI `TRACE-MATRIX.md` Home-send recovery: “**Same-tab reload / restored page session** restores pending triple from sessionStorage when present. **Cold start / closed tab:** empty storage; `list_mailbox(product_session_id)` only; never auto-resend.”

`browser restart` as a restoration promise is **gone from live law**. The only remaining live hit is backend `CLOSURE-EVIDENCE.md` describing the **old** wording as closed. UI `reviews/review-closure-delta-2026-09-24.md` still says “lost ack then browser restart”; that file is historical evidence, not live law (see §5).

UI `BOOTSTRAP-AND-AUTH.md` locked defaults still say **“Same-tab restart”**; §5.5 glosses it as **“Same-tab restart (reload)”**. Close-browser is a separate failure row (`sessionStorage` gone with the tab). That synonym is not a competing “browser restart restores pairing” rule. Backend AD-14 is the tighter name.

## 4. Auto-approve hunt (live files only)

Grep of both sitting trees for `auto-approve`, `auto-approval`, `remembered Origin`, `/pair/renew`, `browser restart`, `sessionStorage`.

**Every live `auto-approve` / `Origin-only` sentence refuses the path.** None permit it.

Live refuse sentences (not exhaustive; all same polarity):

- UI BOOTSTRAP locked defaults: remembered Origin **never** issues a `pairing_session_id`.
- UI BOOTSTRAP §5.5: Origin **does not** auto-approve and **does not** issue.
- UI BOOTSTRAP §7 Must-not: Origin-only auto-approve.
- UI BOOTSTRAP §12 `qmb host pair`: Origin-only auto-approve is refused; does not issue a session because Origin was remembered.
- UI BOOTSTRAP §14 tests: Origin-only auto-approve refused.
- UI CHANGE-IMPACT: Origin-only auto-approve **refused**.
- Backend AD-3 Prevents: Origin-only auto-approval.
- Backend consistency: Origin-only issuance is `POLICY_REJECTION`.
- Backend PAIRING §1: typed-URL second tab does **not** auto-approve. `/pair/confirm` Does not: Auto-approve on Origin.
- Backend HOST-LIFECYCLE `qmb host pair` Does not: auto-approve a second tab (confirming tab A’s code does not mint a session for tab B).
- Backend T-BE-01 Must-not: auto-approve because Origin is remembered.

**`/pair/renew` is not an Origin-only path.** It requires an existing unexpired unrevoked Bearer plus matching Origin. T-BE-03 Must-not: renew without Bearer. AM-01 / AD-5 do not put renew on the unauthenticated carve-out.

**Cloned tab is not an Origin-only path.** WHATWG copies `sessionStorage`; that is existing proof (reconnect or path 2). T-BE-07 Must-not: Origin-only branch. `producer_id` still must not be shared with a live sibling (UI AD-24).

**CORS reflect on `/pair/start` and `/pair/confirm` is not issuance.** Those paths return `{code, pending_id}` or stay pending until QMB confirms **that** `pending_id`. Authenticated routes use the exact paired Origin, not reflect-any.

**Stored Origin→operator bind after QMB confirm is not a license to mint later sessions.** BOOTSTRAP §5.3 step 5 stores the bind for the issued session’s internal map. AD-3 and the second-tab rows still require a **fresh** confirm of **that** pending request. A remembered Origin row does not make `/pair/confirm` succeed for a new `pending_id`.

No live file offers Origin-only auto-approve as a `may`, a default, or an alternate builder path.

## 5. Historical `reviews/` are not live law

Do **not** treat these as the candidate:

- `architecture-QMX-UI-2026-09-23/reviews/review-closure-delta-2026-09-24.md` — residual “Second-tab auto-approve is `may`”; T-CH-06 “browser restart.” That was the **pre-reconciliation** finding this sitting claims to close. Live BOOTSTRAP / AD-19 / AD-3 / AD-14 supersede it.
- Other UI `reviews/*` (gate-amendment-summary, review-amendment-adversarial, review-amendment-rubric) describe the earlier R2 owner/proof work, not this issuance gate.

`UI-CANDIDATE-CHANGELOG.md` records the reconciliations and states: “Historical `reviews/` left as prior evidence.”

## 6. Residuals that do **not** reopen R2 issuance

These are wording or inventory nits. They do not create a second legal issuance host.

1. **J-UI-14 is slightly looser than AD-14.** `JOURNEYS.md` J-UI-14: a deployed client “starts against a running daemon, pairs, and restores mailbox plus JobHandles.” UI TRACE-MATRIX Gherkin: “pairing and snapshot restore” on launch/update/recovery; “`producer_id` persists across client restart of the same surface **if stored**.” “Pairs” does not say Origin auto-approves. A careless builder could read launch as silent pairing. AD-14 / PAIRING §6 / T-BE-06 are the controlling cold-start rule: empty storage → QMB path. **Not an auto-approve path.** Optional follow-up: one sentence on J-UI-14 pointing at AD-14.

2. **UI TRACE-MATRIX has no dedicated Origin-only pairing row.** Backend TRACE-MATRIX and PAIRING T-P-* own issuance acceptance. UI TRACE-MATRIX Home/Reconnect rows are chat recovery and re-auth with an existing id. Division of labor is declared. **Not a competing dialect.**

3. **BOOTSTRAP §10 owners and §11 backend-adds tables omit `/pair/renew` as a named HTTP add.** Issuance prose, second-tab lock, and `qmb host pair` contract name it. Backend PAIRING / AD-3 / DEPENDENCY-MAP name it. Inventory incompleteness in the UI companion tables, not a third issuance path.

4. **BOOTSTRAP mermaid happy path** shows QMB pair then `/pair/confirm`. It does not draw `/pair/renew`. Companion text does. Fine.

5. **v1 renew does not revoke the old id** (two live ids until TTL or `qmb host pair revoke`). Documented. Not Origin-only.

6. **TTL number is unbound** (`registry:pairing.session_ttl`; sitting mints no number). Revoke command is named. Historical “TTL/revocation unbound” is closed as ownership, not as a numeric default. Unrelated to Origin-only issuance.

7. **Inspect honesty.** `/pair/*`, pairing table, Bearer, WS subprotocols, CORS, `qmb host *`: **absent** at `34c148be`. `CLOSURE-MAP.md` remaining risk is that absence. Missing code is not a remaining auto-approve rule.

8. **Candidate tags.** UI AD-19 is `[CANDIDATE]`. Backend AD-3 and AD-14 are `[USER]` for this backend sitting (operator-direction captured in the delta, still not product-accepted). Whole packets remain sitting-candidate, not operator-accepted. That is provenance, not a fork.

## 7. File-by-file (requested reads)

| File | R2 issuance | Reload / cold start | Auto-approve |
| --- | --- | --- | --- |
| UI `BOOTSTRAP-AND-AUTH.md` | Closed. Two legal paths. Remembered Origin never issues. | Same-tab restart glossed as reload; close-browser storage gone | All mentions refuse |
| UI `ARCHITECTURE-SPINE.md` AD-19 | Closed. Cites backend AD-3 | (reload detail in companion / backend AD-14) | “never authorizes” |
| UI `CHAT-AND-HISTORY.md` | Reconnect uses same `pairing_session_id`; internal map to `credential_ref` | T-CH-06 renamed; cold-start empty-storage branch; no resend | None permitting |
| UI `TRACE-MATRIX.md` | Reconnect re-auths pairing id; no Origin-only row (backend owns it) | Home recovery: reload vs cold start | None permitting |
| Backend `PAIRING-AND-ADMISSION.md` | AD-3 operational form; RFC 6455 rationale | §6 three recoveries | Confirm does not auto-approve on Origin |
| Backend `ARCHITECTURE-SPINE.md` | AD-3 [USER] is the lock; AD-5 keeps renew authenticated | AD-14 [USER] | Prevents Origin-only auto-approval; `POLICY_REJECTION` |

## 8. What this review does not claim

- Operator acceptance.
- Executed tests or Reticle proof.
- Live pairing HTTP at inspect.
- That J-UI-14 wording is perfect (it is slightly loose; it does not authorize Origin-only issuance).
- That historical UI `reviews/` were rewritten (they were not; they are not law).

## 9. Bottom line

The remaining UI R2 condition — remembered Origin must not authorize a new `pairing_session_id` — is **closed as candidate** in the reconciled UI packet and the backend-delta spine. Negative and positive traces exist. Reload vs cold-start is split in live law. No live auto-approve path remains except sentences that refuse it.
