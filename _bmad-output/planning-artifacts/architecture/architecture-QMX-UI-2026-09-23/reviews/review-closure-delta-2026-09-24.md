---
name: Closure-delta review against Codex 2026-09-24 remaining corrections
sitting: architecture-QMX-UI-2026-09-23
against: workroom/qmx-ui-closure-review-2026-09-24/REVIEW.md R2–R7, R9
inspect: integration@34c148be404a375cbfd79fd4ce6997452e4f1d20
date: 2026-09-24
status: independent review — not operator-accepted
spine: not rewritten
---

# Closure-delta — Codex R2–R7 / R9

**Not ready for Documentation Factory.** The second amendment closed the original companion forks on bootstrap owner, chat-vs-invoke, Epic 60 `copilot_profile`, first-Run enable, local-then-transfer ingest, cancel authority, and the Node 22.12 floor. `CLOSURE-MAP.md` still over-closes. Codex’s remaining gate was *mutually consistent contracts and traces*. Three traces still admit a second legal host.

Scope: architecture-readiness of the amended candidate vs `workroom/qmx-ui-closure-review-2026-09-24/REVIEW.md` remaining corrections. Not an implementation audit. Missing backend code is not a closure failure. Spine was not edited.

R1 and R8 remain **closed**. They were not reopened.

## Disposition

| ID | Codex remaining (2026-09-24) | This review | CLOSURE-MAP |
| --- | --- | --- | --- |
| R1 | (already closed; preserve) | **closed** | closed (preserved) — agree |
| R2 | One browser-realizable proof on HTTP **and** WebSocket; reconcile spine, companion, traces | **still conflicting** | closed as candidate — **over-close** |
| R3 | Persist `psess:` on mailbox; identity known before ack; same id in payload, query, **and trace** | **still conflicting** | closed as candidate — **over-close** |
| R4 | Keep Epic 60 sibling `copilot_profile`; nav→view; unambiguous grant | **closed as candidate** | closed as candidate — agree |
| R5 | One empty-Authoring → enable → first Run path; CAS on saved drafts | **closed as candidate** | closed as candidate — agree |
| R6 | Possession vs placement; one resume **or** refuse rule; traces | **still conflicting** | closed as candidate — **over-close** |
| R7 | One cancel authority; `expected_state` races; originating session binding | **closed as candidate** | closed as candidate — agree (examples still thin) |
| R8 | (already closed; preserve CANDIDATE tags) | **closed** | closed (preserved) — agree |
| R9 | Explicit Node `>=22.12 <23` | **closed as candidate** | closed as candidate — agree |

## R1 — closed (preserved)

AD-3 `[USER]` still names independent rail destinations with zero opened apps: **Home**, **Copilot**, **Library**, **Authoring**. Home is work/attention/resume. Copilot is conversation. They may share components; they are not the same destination. `EXPERIENCE-AND-LAYOUT.md` still says “Home is not Copilot.” Geometry remains unfrozen. Do not reopen.

## R2 — still conflicting

Spine AD-19 and `BOOTSTRAP-AND-AUTH.md` now agree on one proof: `pairing_session_id`. Unauthenticated HTTP is `/pair/start` and `/pair/confirm` only. Authenticated HTTP GET is `Authorization: Bearer pairing:<id>`. Authenticated WebSocket is WHATWG `new WebSocket(url, ["qmx.ct40.v1", "qmx.pair.<id>"])`. Cookies refused. Browser does not present `cred://` as login. Daemon maps Origin + pairing session to an internal `credential_ref`. That **was** the original AD-19 vs companion fork. It is gone.

Codex remaining: *reconcile spine, companion, examples and traces.* Traces and the chat reconnect list were not reconciled.

**Contradiction — browser proof on reconnect**

`BOOTSTRAP-AND-AUTH.md` (reconnect is a query path):

> same unexpired `pairing_session_id` for that tab, daemon re-maps to operator + `CredentialRef`

`CHAT-AND-HISTORY.md` §9 step 1:

> Re-auth `credential_ref`; `initialize` with the **same** `producer_id`

`TRACE-MATRIX.md` Reconnect row:

> (1) re-auth `credential_ref` (2) `initialize` same `producer_id`

`TRACE-MATRIX.md` vertical slice:

> Authenticated CT-40 (`credential_ref` before protocol bytes) to a **live** daemon.

A builder following AD-19 / bootstrap presents `pairing_session_id` (Bearer + WS subprotocol) and never sends `credential_ref`. A builder following the chat companion and trace matrix re-auths `credential_ref` as the client proof. That is the same two-proof fork Codex already named. Origin + pairing table still does not prove operator identity if the trace tells the client to send the mapped ref.

Residual (not a second owner, still unbound): `pairing_session_id` issuance/storage are named; **TTL and revocation owner/command are not**. Second-tab auto-approve is `may`. Those are missing bindings. They are not the quoted contradiction.

## R3 — still conflicting

`CHAT-AND-HISTORY.md` and AD-18 now do what Codex asked of the companion:

- Mailbox Envelope persists `product_session_id` at write; replies/questions inherit.
- Pre-ack identity is the wire pair `(producer_id, id)`, minted before send, held in `sessionStorage`.
- `list_mailbox` lookup by that pair; lost-ack recovery must not wait for `msg_id`.
- Rebuild example (four journal rows) and T-CH-06 (lost ack then browser restart, no resend).
- Product-session `command_id` is **forbidden** as the chat send identity.

Codex remaining: *use that identifier consistently in payload, query and trace.* The trace matrix was not updated.

**Contradiction — chat send identity**

`CHAT-AND-HISTORY.md` §1.1 / identities / forbidden:

> It does **not** use product-session `command_id` (that namespace is parent AD-29 mutate / cancel / invoke — not mailbox append).
>
> Using product-session `command_id` as the chat send identity. *(forbidden)*

`TRACE-MATRIX.md` **Home send, no instance** Identity column:

> `psess:`; `producer_id` (this tab); `command_id` unique per `psess:`. **No** `instance_id`.

Same file, **Lost ack** (covers send/invoke/cancel):

> Preserve original `producer_id`, wire `id`, `command_id`

Same file, **Duplicate submit** (Run / **Send** / Cancel):

> Same `command_id` and (invoke) same `idempotency_key` + `input_hash`.

Recovery on the Home-send row correctly queries `list_mailbox` by `(producer_id, wire id)` not `msg_id`. Identity and duplicate-submit still mint or preserve a session `command_id` for Send. Two hosts can both claim AD-18 and disagree on whether a chat send has a product-session `command_id`. That is the remaining Codex sentence: *the trace matrix adds a durable session `command_id`, but the chat payload and dedup table specify only the wire pair.*

## R4 — closed as candidate

Codex remaining: keep Epic 60 `PluginManifest.copilot_profile`; bind nav to views; refuse ambiguous grants; do not silently rewrite factory inputs.

- AD-15 / `VIEW-AND-PACK-CONTRACT.md`: optional **`PluginManifest.copilot_profile`** stays the sibling field. PackUiRequest **references** it and must not nest it as a replacement. **No parent amendment.** Epic 60.1 remains owner.
- Nav items are `{id, title, slot, view_ids}`. Unknown `view_id` → ignore that nav item; empty `view_ids` invalid (ignore item); enable of ops still succeeds.
- Matching GrantRecords: 0 → `grant_id` null (paint, invoke refuses); 1 → that record; ≥2 → typed `GRANT_AMBIGUOUS` (no first-wins, no merge, no order pick).
- `EXAMPLES.md` A/B put `copilot_profile` on the manifest, `view_ids` on nav, and I6 in the refuse table.
- `BACKEND-DEPENDENCIES.md`: **No** parent amendment to move `copilot_profile` inside `pack_ui_request`.

Residual: I6 is a one-line refuse table, not a worked two-grant JSON. A nav item may list **multiple** `view_ids`; click/mount selection for that array is unspecified. Neither reopens the Epic 60 schema fork.

## R5 — closed as candidate

Codex remaining: one complete empty-Authoring → package/enable registration → grant → first Run; distinguish local enable from later export; CAS on concurrent saved drafts.

`AUTHORING-AND-ML.md` §0 / §2.0 / T-R5-00:

empty Authoring → save revision → validate → **publish into the local authoring pack** → **enable that local pack** (parent AD-30 compile-at-enable) → grant → select `instance_id` → `dispatchInvoke`.

Local authoring pack is this machine’s unpublished roster. Distributable export is a later copy. Publish-into-pack is **not** registration. Enable **is** compile identity. Draft Run remains `draft_not_runnable`.

CAS: `expected_revision` = last known `editor_revision` hash. T-R5-07: two restored clients at `R1`; second stale save refuses until reload.

AD-21 matches the companion.

Residual: `TRACE-MATRIX.md` ML row still says `dispatchInvoke` of registered template `start` **after publish**. Read against T-R5-00, “registered” means after enable. It is sloppy, not a second first-Run machine. Do not treat it as permission to Run at publish.

## R6 — still conflicting

Spine AD-22 and `LIBRARY-AND-ATTACHMENTS.md` now pick **one** design: initial possession on the authenticated **local** daemon via HTTP PUT `/artifacts/stage` (not a JSON-RPC body); completeness = daemon hash + byte count; Home may attach with no instance; v1 interrupted PUT is **refused** (delete incomplete object, no partial fp1, retry = new full PUT); remote execution needs explicit `transfer_artifact` + hash verify; silent local fallback refused. T-R6-01 and T-R6-07 exist. That **was** the companion’s possession-vs-placement fork. It is gone **inside** AD-22 / Library.

Codex remaining: traces must not keep the resume/refuse fork.

**Contradiction — interrupted transfer**

AD-22:

> Interrupted v1 uploads are **refused**; no resumable partial; no runnable incomplete ref. Remote execution requires an **explicit transfer** to that placement and a hash check.

`LIBRARY-AND-ATTACHMENTS.md` locked defaults:

> Interrupted v1 PUT: **Refuse.** No resume. No partial fp1.

`TRACE-MATRIX.md` **Local file, remote job** (J-UI-09):

> **Cmd** daemon `stage_artifact` … Remote placement stages or **refuses**.
>
> Partial transfer resumes or refuses.

`Cmd stage_artifact` plus “remote placement stages” is target-bound staging on a JSON-RPC command. “Resumes or refuses” is the exact unbound choice Codex told the sitting to pick. AD-22 already picked refuse + HTTP PUT + later `transfer_artifact`. The trace still allows both hosts. `JOURNEYS.md` J-UI-09 (“stage … or refuse”) is the same abbreviation.

## R7 — closed as candidate

Codex remaining: one authorization rule; observation is not cancel; fence handle/run/attempt; define queued→running vs already-terminal; `expected_state` effect; examples.

The **observer vs starter** contradiction is gone. AD-23 and `TRACE-MATRIX.md` cancel contract now say the same thing:

> Authority: operator of the JobHandle’s immutable `originating_psess` (admitted at start). Observation is not cancel authority.

`expected_state`: JobHandle state plus `attempt_id`. `queued`→`running` does **not** invalidate the same `command_id`. Already-terminal → recorded no-op. Same-command replay is idempotent. First durable terminal wins. Nested child handles use the same `dispatchCancel`. `originating_psess` is a named JobHandle amend, not a UI grant store.

Present traces: cancel-vs-complete (J-UI-08), lost-ack, duplicate submit. Residual: Codex also asked for starter-vs-observer, queued→running, and nested-child **worked examples**. Those are still sentences, not rows. That is thin evidence, not a second authority rule. Do not let Home attention “observe ⇒ cancel.”

## R8 — closed (preserved)

Spine provenance still defines USER / INHERITED / CANDIDATE / OBSERVED. `[CANDIDATE]` is not user approval. AD-2, AD-15, AD-18..AD-23 remain `[CANDIDATE]`. AD-3 remains `[USER]`. `DECISIONS-AND-OPEN.md` C-table is C, not P. Candidate status remains; this review is not operator acceptance of the defaults.

## R9 — closed as candidate

Codex remaining: state **`Node.js >=22.12 <23`** (or another explicit compatible range) on spine, stack, ledger, closure map.

Current law (same range):

- AD-2: `Node.js >=22.12.0 <23.0.0`
- Stack table: `>=22.12.0 <23.0.0`
- `DECISIONS-AND-OPEN.md` C-SPA: `>=22.12.0 <23.0.0`
- `CHANGE-IMPACT.md` and `CLOSURE-MAP.md`: same
- bits-ui **2.19.3**; pnpm; lockfile at isolated-scaffold gate (unexecuted, as allowed)

`.memlog.md` still has an earlier event “Node 22 LTS”. The later version event restates `>=22.12.0 <23.0.0`. Append-only history is not a live fork. Scaffold remains unexecuted.

## CLOSURE-MAP

`CLOSURE-MAP.md` status column is wrong for R2, R3, and R6. Those three still have two legal traces. R4, R5, R7, R9 may stay “closed as candidate.” R1/R8 stay closed. Backend adds named in `BACKEND-DEPENDENCIES.md` remain honest absences, not closure failures.

**Next gate:** make TRACE-MATRIX (and CHAT reconnect step 1) quote the same proof, the same chat pre-ack identity, and the same refuse-partial ingest as the companions. Then re-review that finite delta. Do not reopen R1/R8. Do not rewrite the spine for this residual. Do not start Documentation Factory.
