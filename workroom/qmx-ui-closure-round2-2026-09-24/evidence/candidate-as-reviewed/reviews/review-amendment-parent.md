# Reviewer gate — LENS: parent / kit consistency of local AD-18..AD-24

**Subject:** `architecture-QMX-UI-2026-09-23` local AD-18..AD-24 and companions (`CHAT-AND-HISTORY.md`, `BOOTSTRAP-AND-AUTH.md`, `VIEW-AND-PACK-CONTRACT.md`, `AUTHORING-AND-ML.md`, `TRACE-MATRIX.md`, `LIBRARY-AND-ATTACHMENTS.md`). Candidate defaults, not operator-accepted.
**Against:** parent `architecture-QMX-2026-09-18` AD-8, AD-9, AD-17, AD-21, AD-24, AD-26, AD-29, AD-30 (and AD-3 / AD-4 / AD-16 where those ADs are the actual bind); kit `architecture-QMX-2026-09-23` AD-1..AD-9; research `06-parent-invariants-for-ui.md`; inspect `integration@34c148b`.
**Question this lens answers:** do the post-Codex R1–R9 amendments weaken or silently override inherited parent/kit law? Especially: `send_message` without `InvocationEnvelope`; `cancel_job` without `InvocationEnvelope`; QMB host CLI; `ActionContext` vs session grant bag; draft Run refuse.
**Date:** 2026-09-24. Reviewer: independent parent-amendment seat. No rewrite. No implementation. Companions scored with the spine.

**Verdict: PASS with Medium findings.**

Local AD-18..AD-24 do **not** mint a sixth COMP, a second grant store, a `qma`/`qmn` operator CLI, a third `ProductSessionProfile`, a `ui_view` contribution point, or a live-graph compile in the Svelte process. Envelope `instance_id` stays required on **invoke**. Home chat without an instance is not sold as invoke. Widgets still do not own invoke. Draft Run is refused until a registered immutable Graph Template exists. `qmb host *` is process supervision under the existing QMB operator CLI, not a substitute for envelope invoke.

What this lens will not bless as already-true parent law: cancel authority from mere observation; daemon-owned editor draft/revision as a new sqlite class; reading spine AD-20 as a replacement for parent AD-9; reading local AD-23 as forbidding kit AD-4 nested `cancel` as an AD-3 invoke; treating local `AD-18` / `AD-21` / `AD-24` as the parent ids of the same numbers.

This seat does **not** rewrite the candidate.

---

## Method

Parents bind read-only. A local rule that would make json-render or MCP Apps identity/grant, union nested grants, let app-use apply a change-request, persist layout on `product_session`, cancel durable work on panel dispose, replay unacked intent, or skip envelope `instance_id` on a public AD-3 call is a **conflict**.

Inspect honesty used: `WireCommand.SEND_MESSAGE` exists; live dispatch does not. `InvocationEnvelope` exists without `caller_kind`. `JobHandle.cancel` is the coordinated cancel writer (`FR-W36`); `ui_widget` is an unauthorized writer. `cancel_job`, `list_mailbox`, `stage_artifact`, and `qmb host start|status|stop|pair` are **absent** at `34c148b`. `DaemonProcess` still discards TCP bytes.

---

## Especially checked

### 1. `send_message` without `InvocationEnvelope` (local AD-18)

**Parent / kit bind.** Parent AD-3 / AD-24: every **public AD-3 call** carries `InvocationEnvelope`; `instance_id` is required on every invoke; the envelope is request context, not authority. Kit AD-1: InvocationEnvelope is the only **invoke**. Kit AD-3 / DEC-0463: authoring with absent `app_instance_id` **may not invoke** until exactly one `selected_refs` kind `instance_id` is present; envelope `instance_id` remains required. Parent AD-8: `product_session` durable fields are grants/refs/profile — not messages. Parent AD-9: tools = published ContributionHits ∩ host grants ∩ session GrantRecords ∩ health.

**What the amendment does.** Local AD-18: `ConversationPane.send` issues CT-40 `send_message`; it does not call `dispatchInvoke`; no `instance_id` is required; granted tool calls remain `dispatchInvoke`. Companion `CHAT-AND-HISTORY.md` refuses Team B (chat as envelope invoke), forbids a synthetic Home instance, keys durable history on the existing QMA mailbox indexed by `psess:`, and names addable query `list_mailbox` (COMP-QMA-WIRE). Sequence diagram in the spine now splits Home chat from widget Run.

**Ruling: holds.** `send_message` is a seed CT-40 **command** (`WireCommand.SEND_MESSAGE`, same family as `approve_hook_action` / `update_configuration`), not a pack `op_id`. Parent AD-24 binds public AD-3 calls, not every wire frame. Routing Home Send through `InvocationEnvelope` would be the weakening: it would force a synthetic `instance_id` and contradict kit AD-3 / parent AD-8 (Home authoring may omit `app_instance_id`; chat without invoke is legal). Keeping transcript off `product_session` / `private_notes` is parent AD-8. `list_mailbox` is a closed-and-addable CT-40 query, not a new CT and not a sixth store.

**Residual (F-3):** spine AD-18 is four sentences. The load-bearing fence — “a later copilot tool call is `dispatchInvoke`, waits for one `instance_id`, and is not a second `send_message`” — lives in the companion. A unit that only reads the spine can still treat mailbox send as implicit agent `start` (effect class, grant, envelope skipped). Research/10’s “same effect-class matrix as invoke” row is correctly dropped **only if** `send_message` remains mailbox append.

### 2. `cancel_job` without `InvocationEnvelope` (local AD-23)

**Parent / kit bind.** Parent AD-26 / QMA AD-17: coordinated cancel is `JobHandle.cancel`; first durable terminal wins; cancelled display is not proof of stop; `unknown` is not cancellable. Seed `FR-W36`: writer token is `JobHandle.cancel`; `plugin` / `routine` / `worker` / `ui_widget` cannot take that path; tab-close / `wire.detach` cancel nothing. Parent AD-3 descriptors list lifecycle verb `cancel` among `start | query-state | cancel | await`. Kit AD-4: workflow-to-workflow **runtime** is parent-AD-3 invoke of the callee template’s those verbs (envelope, one nested Mission / Task Graph / JobHandle). Parent AD-9 / AD-24: grant intersection and hop-compare on public calls. Codex R7 required one host function, one CT-40 method, a statement of envelope-or-not, and **existing principal/grant checks** — not a second cancel dialect, not seed `stop_run`.

**What the amendment does.** Unique issuer `dispatchCancel`. Addable CT-40 command `cancel_job` (absent at inspect). Fields: `handle_id`, `logical_run_id`, `attempt_id`, `command_id`, expected state. Repeat uses the same `command_id`. **Not** an `InvocationEnvelope` invoke. TRACE-MATRIX principal rule: operator of the `psess:` that **started** the job **or can observe it**. `machine` cannot take this path. Adapters never import the wire client.

**Ruling: JobHandle axis holds; grant/principal text does not.** Skipping `InvocationEnvelope` on **UI operator cancel of an existing handle** is the parent AD-26 / `FR-W36` path, not a new public AD-3 invoke. That is the correct Team A vs Team B close: cancel is not a second `dispatchInvoke`. Seed `stop_run` is forbidden. First-terminal-wins and `unknown` non-cancellable hold.

Two weakenings remain:

1. **Observation as cancel authority (F-1).** “or can observe it” lets Home attention (local AD-14, query-only) cancel a handle that belongs to another `psess:` / instance merely because the operator can see the badge. Parent AD-8/AD-9: listing and observation are not grant. Codex R7 asked for existing **principal/grant** checks. Observation is not that check.
2. **Absolute “not an InvocationEnvelope invoke” (F-2).** Kit AD-4 nested template `cancel` remains an AD-3 public call **with** envelope (`caller_kind=workflow`). Local AD-23’s sentence has no carve-out. A unit can route nested cancel through `cancel_job` and drop envelope `call_depth` / parent id / GrantRecord compare.

### 3. QMB host CLI (local AD-19)

**Parent / kit bind.** Parent AD-21: QMB is the **only** operator CLI; QMA and QMN ship none; unsupported door → `unsupported_door`; a log/progress panel is not a general shell. Parent AD-17: host is a client of qma-wire, QMB API/CLI, QMN doors; mount/dispose must not start/kill durable work. Parent AD-1: no sixth COMP; allowed processes remain `qma-daemon`, `qmn`, QMB process-per-run children. DEC-0336: `python -m qma.daemon` is process entry, not an operator CLI.

**What the amendment does.** v1 requires an already-running daemon. Privileged owner is COMP-QMB `qmb host start|status|stop` (backend add; companion also names `pair`). Until it exists, UI Start local is a **setup instruction**, not a spawn. Browser JS must not spawn Python. Closing the browser is `wire.detach` and never stops the daemon. `qmb host stop` is the Stop-local-runtime door; local handles may become `unknown`; QMN/remote work continues. Spine: must not spawn `qmb` as a substitute for envelope invoke; QMB CLI may supervise the daemon.

**Ruling: holds.** This is parent AD-21 ownership, not a new `qma-cli` and not a second orchestrator. Process supervision of the already-allowed `qma-daemon` is not a sixth COMP. Window-close ≠ stop (closes the previous local AD-12 hole). Interim `python -m qma.daemon` is tagged as process entry / setup, not product CLI.

**Residual (F-6):** until `caller_kind` exists, the host **refuses pack invoke** and “qmb CLI remains the headless door.” That is inspect capability mismatch (J-UI-13), not UI-only op semantics — **provided** the UI does not shell out to `qmb` to “just invoke.” Spine already forbids that substitute. xterm.js stays preview (parent AD-21). `qmb host pair` is an extra verb in the companion; still QMB.

### 4. `ActionContext` vs session grant bag (local AD-20)

**Parent / kit bind.** Parent AD-9: tools = published ∩ host grants ∩ session GrantRecords ∩ health; prose/HTML do not grant. Parent AD-17: json-render and MCP Apps are presentation adapters, not authority; catalog names an existing AD-3 `op_id` and must not add/remove fields; host intercepts `tools/call`. Parent AD-24: host resolves GrantRecord from stores and hop-compares every bound field; `instance_id` required on invoke; upgrade cannot widen a grant. Kit AD-2: widgets never own invoke. Kit AD-5: `failure_class=view` is mount/stale/unhealthy, not invoke. Codex R4: a renderer must not pick “any grant in this `psess:` whose `op_id` matches.”

**What the amendment does.** Host mints one immutable `ActionContext` per mount (`psess`, `view_id`, contribution tuple, `instance_id`, `config_revision`, `grant_id`, `allowed_op_ids`, account scope, snapshot cursor). Untrusted specs/frames supply only action name + schema-valid input. Foreign authority fields are **ignored**, not copied. `dispatchInvoke` builds the envelope from the mint context, then daemon `compare_envelope_to_grant` plus parent AD-9. Two instances with the same `op_id` stay isolated by `instance_id` + `grant_id`. Empty `allowed_op_ids` means **this view** cannot press; CLI/native of the same `op_id` still can (parent AD-17 catalog-miss law). Dispose drops the context and does not cancel jobs. MCP profile `2026-01-26`; QMX declines extra app tools and unintercepted `tools/call`.

**Ruling: holds; this is a tightening, not a second grant system.** `ActionContext` is not a GrantRecord (companion states three records: `PackUiRequest`, `ViewPresentation`, `ActionContext`). EXAMPLES I1/I5 name host refuse of cross-instance and iframe-supplied `instance_id`. That is the Codex R4 close of session-bag Adapter B.

**Residual (F-4):** spine AD-20 says only “intersects that context with the matching GrantRecord.” A unit that never reads `VIEW-AND-PACK-CONTRACT.md` §6 can treat `allowed_op_ids` as authority and skip published ∩ host grants ∩ health. Remount-on-revoke is in the companion, not the spine Rule.

### 5. Draft Run refuse (local AD-21)

**Parent / kit bind.** Parent AD-4: Graph Template ≠ Task Graph ≠ Board ≠ Stage 0 `graph`; enabled `(qualified_id, version)` bytes are immutable; selected-subgraph execution is `MissionCompiler` of an **already-registered** template, not a live scribble; Board layout writes nothing. Parent AD-13: identities stay separate. Parent AD-17: UI is a client; do not compile templates in the UI process. Parent AD-29 / AD-8: app-use mints `change_request`; authoring + operator apply; v1 stays pinned. Parent AD-16: v1 daemon sqlite additions are a **closed** list (product_session, task_graph_state, mini-app instance rows, GrantRecord rows) — **no other new sqlite**. Parent AD-30: pin/invoke revalidates; disable/uninstall → `unavailable`/`tombstone`. Kit AD-4: no live Task Graph merge. Kit AD-9: yap → Graph Template → runs → pack export after validate (run still needs envelope + instance).

**What the amendment does.** Distinct ids: `editor_draft_id`, `editor_revision`, Graph Template `(qualified_id, version)`, pack instance, JobHandle. Validate/preview may use a saved revision. **Run refuses** until a new immutable template version is registered (`draft_not_runnable`). Graph Run is `dispatchInvoke` of that template’s `start` op — not seed `start_mission`, not in-process `MissionCompiler`, not a live Board scribble. Temporary/hidden “dev version” and in-place overwrite of enabled bytes are unsupported. Change-request is the three parent records; app-use must not apply; running instance bytes stay pinned. Expand retains typed refs, not one `draft/version` string.

**Ruling: refuse holds.** This is parent AD-4/AD-13, not a weakening. Team B (throwaway runnable draft) is the parent conflict; the sitting closed it.

**Residual (F-5):** `AUTHORING-AND-ML.md` then **persists** `editor_draft_id` / `editor_revision` as COMP-QMA-DAEMON content-addressed staging (“daemon persists id on first save”) while claiming no new sqlite class. CHANGE-IMPACT also says no new sqlite class. Parent AD-16 has no editor-draft projection. `change_request` is the wrong record. `private_notes` is the wrong column. Artifact fp1 would mint a Library kind the companion forbids. Codex R5 allowed daemon staging **only for supported draft test-runs**; this sitting refused those runs and still invented the store. Two units:

- Unit A: unsaved buffer is client-local; save/publish is pack/plugin enable (parent AD-4/AD-30) or a named existing staging kind; Run still refused until registered `(qualified_id, version)` ∩ grant ∩ health ∩ envelope `instance_id`.
- Unit B: new daemon table for drafts; reconnect restores mutable bytes; factory treats that as v1 sqlite add #5.

Unit B silently overrides parent AD-16. The linear flowchart (publish → pack export → install → enable → grant → Run) is stricter than kit AD-9’s daily path but is **not** a parent weakening if publish/register already yields an enabled contribution and invoke still requires `instance_id`.

---

## Other local AD-18..AD-24 vs named parents

| Local | Parent / kit | Status |
| --- | --- | --- |
| AD-18 mailbox keyed by `psess:`; reconnect adds `list_mailbox` | parent AD-8 (no messages on the row); parent AD-29 reconnect is a query, no intent replay | Hold (F-3 fence) |
| AD-19 pairing `credential_ref` + origin; cred string is not operator proof | parent AD-21; CT-40 `authenticate_before_protocol` | Hold |
| AD-20 no `ui_view` point; PackUiRequest is request DTO | parent AD-17 / kit AD-1; install ≠ grant (parent AD-18/AD-30) | Hold |
| AD-21 CR three records; app-use must not apply | parent AD-29 / AD-8 | Hold |
| AD-22 `stage_artifact` then artifact fp1; no `local_path` / `upload_bytes` | parent AD-8 closed `selected_refs`; parent AD-3 durable file = fp1; existing artifact register path, **no** new sqlite | Hold (host command, not pack invoke; later Run still envelopes) |
| AD-23 first terminal wins; not `stop_run` | parent AD-26 | Hold axis (F-1, F-2) |
| AD-24 `producer_id` per tab; `command_id` unique per `psess:` across tabs; invoke `idempotency_key` is a third identity | parent AD-29 namespace `(product_session_id, principal, command_id)`; wire pair `(producer_id, id)` | Hold if TRACE namespace (includes principal) is used; spine Rule drops `principal` (F-7) |
| Headless pack still invokable without `view:*` | parent AD-17 / kit AD-1 | Hold |
| Tombstone / no silent other version on disabled contribution | parent AD-30 | Hold (EXAMPLES I3) |

---

## Numbering collisions introduced by this amendment

Research `06` already named local vs parent vs kit `AD-n`. The new rules reuse the **exact parent numbers this lens is asked to protect**:

| Local UI | Parent 09-18 | Kit 09-23 | Factory misread if prefix dropped |
| --- | --- | --- | --- |
| **AD-18 chat is mailbox** | **AD-18 pack export / no secrets** | — | Chat law mistaken for pack lifecycle |
| AD-19 QMB host bootstrap | AD-19 mutation testing | — | Least bad |
| AD-20 host ActionContext | AD-20 defaults/templates | — | Context mistaken for first-slice defaults |
| **AD-21 draft not runnable** | **AD-21 headless door parity; QMB-only CLI** | — | Draft refuse mistaken for door parity; or door parity dropped because “AD-21 is drafts” |
| AD-22 `stage_artifact` | AD-22 Portfolio Manager label | — | Ingest mistaken for Role rename |
| AD-23 `dispatchCancel` | AD-23 ATC complete second system | — | Cancel chrome mistaken for ATC |
| **AD-24 producer/command identity** | **AD-24 InvocationEnvelope + GrantRecord** | — | Multi-tab ids mistaken for envelope law (or envelope optionalized because “AD-24 is producer_id”) |

Capability map now prefixes many cells `local`. Inherited table still has compound cells. Section titles `### AD-18` … `### AD-24` are local. Body cites of parents are mostly prefixed. That is the right pattern; factory prose that says bare `AD-24` is now worse than before this amendment.

---

## Findings

### High

None that fail the parent-law bar as an untagged override. The Mediums below are editor-applicable so a factory unit cannot cancel from observation, cannot add sqlite class #5 for drafts, and cannot read spine AD-18/AD-20/AD-23 as dropping envelope/grant law.

### Medium

#### F-1 — `cancel_job` principal “or can observe” weakens parent AD-8 / AD-9 / AD-24

**Where:** `TRACE-MATRIX.md` Cancel contract; local AD-23 Rule is silent on grant.

**Parents:** AD-9 intersection; AD-8 session-scoped `granted_ops`; AD-24 hop-compare on public work; Codex R7 “existing principal/grant checks.” Home attention is observation (local AD-14).

**What:** Two units:

- Unit A: `dispatchCancel` is `JobHandle.cancel` for the operator principal of the **starting** `psess:`, and only if that session still holds (or held at accept) the GrantRecord that accepted the start. Other sessions may **query** the handle. Repeat uses the same `command_id`. Nested template `cancel` stays kit AD-4 envelope invoke.
- Unit B: any chrome that can list the JobHandle (Home attention, another `psess:` that “can observe”) may `cancel_job` with no `grant_id` and no starting-session check.

Unit B is cancel-from-listing.

**Action:** apply. Replace “or can observe it” with starting-`psess:` operator principal plus the grant that accepted the start (or a named occupancy/lease check already in parent JobHandle law). Observation remains query.

#### F-2 — Local AD-23 “Not an InvocationEnvelope invoke” can swallow kit AD-4 nested cancel

**Where:** local AD-23 Rule; TRACE-MATRIX “Not a new `InvocationEnvelope` invoke.”

**Parents / kit:** kit AD-4 / parent AD-3 lifecycle verb `cancel` as a public call with envelope (`caller_kind=workflow`, parent id, `call_depth`).

**What:** UI operator cancel of a handle is the JobHandle command (holds). Workflow-to-workflow `cancel` is still an AD-3 invoke. An absolute sentence lets a unit implement all cancel as `cancel_job`.

**Action:** apply. One clause: `dispatchCancel` / `cancel_job` is the UI mapping to `JobHandle.cancel` only. Nested template `cancel` remains `dispatchInvoke` of that verb with envelope. Do not map either path to `stop_run`.

#### F-3 — Spine AD-18 does not fence the agent turn that follows mailbox send

**Where:** local AD-18 vs `CHAT-AND-HISTORY.md` §1.2 / T-CH-02.

**Parents:** AD-3/AD-24 every public AD-3 call carries envelope + `instance_id`; AD-9 tools do not self-grant.

**What:** Companion holds. Spine does not say that daemon-side tool use after `send_message` is still `dispatchInvoke` (or a daemon-minted `caller_kind=agent` envelope) and still refuses without exactly one `instance_id`. Home `send_message` proceeding while pack invoke is `caller_kind_unsupported` is correct **only** because chat is not pack invoke.

**Action:** apply. One sentence on local AD-18: mailbox send never starts a granted op; any public call that follows is `dispatchInvoke` under parent AD-24 / kit AD-3.

#### F-4 — Spine AD-20 intersection can be read as replacing parent AD-9

**Where:** local AD-20 Rule vs `VIEW-AND-PACK-CONTRACT.md` §6.

**Parents:** AD-9 four-way intersection; AD-24 daemon hop-compare is authority.

**What:** Companion lists published ∩ host grants ∩ session GrantRecords ∩ health after envelope build. Spine only “intersects that context with the matching GrantRecord.” `allowed_op_ids` then looks like a client grant list.

**Action:** apply. Spine: `ActionContext` is host-minted invoke **binding**, not a GrantRecord; `dispatchInvoke` still hop-compares parent AD-9; renderer-supplied grant/instance/caller are ignored.

#### F-5 — Daemon editor draft/revision staging vs parent AD-16 closed sqlite

**Where:** `AUTHORING-AND-ML.md` §1 / §2 Create draft / Save revision; CHANGE-IMPACT “no new sqlite class.”

**Parents:** AD-16 closed v1 daemon additions; AD-4 Board/layout writes nothing; Codex R5 daemon staging only if draft **test-run** is supported (it is not).

**What:** Run-refuse holds. Persistence of `editor_draft_id` / `editor_revision` as COMP-QMA-DAEMON staging does not name an existing projection. That is an untagged sqlite add, or a misuse of `change_request` / `private_notes` / artifact fp1 (all forbidden by this sitting’s own tables).

**Action:** apply. Either (a) drafts remain client-local until publish/enable on the parent AD-4/AD-30 path, crash may lose unsaved buffer (companion §2.3 already allows that), or (b) tag a named parent amendment that names the existing store. Do not mint sqlite class #5 in a UI sitting.

#### F-6 — Numbering: local AD-18 / AD-21 / AD-24 collide with the parents under review

**Where:** `### AD-18`, `### AD-21`, `### AD-24`; capability map is better prefixed than the previous sitting, section titles are not.

**What:** Same factory hazard as the AD-1..AD-16 parent-consistency review, now on the ids this amendment is supposed to protect. Bare “AD-24” in a story can optionalize `InvocationEnvelope` because local AD-24 is producer/command identity.

**Action:** apply. Consistency Conventions already say cite `parent` / `kit` / `local`. Repeat once: local AD-18 is mailbox send (parent AD-8 history-not-on-row); parent AD-18 is pack export. Local AD-21 is draft ≠ template; parent AD-21 is door parity / QMB-only CLI. Local AD-24 is producer/`command_id`; parent AD-24 is envelope + GrantRecord. Do not retitle unless the operator wants `UI-AD-n`.

### Low

#### F-7 — Spine AD-24 drops `principal` from the parent AD-29 `command_id` namespace

TRACE-MATRIX has `(product_session_id, principal, command_id)` and UUIDv7. Spine Rule says “unique per `psess:` across tabs.” Product sessions have one principal today, so this is cheap. Cite the parent triple on the spine Rule.

#### F-8 — `CHAT-AND-HISTORY.md` §6 vs local AD-24 on `producer_id` per tab

Chat companion: two chrome tabs of one `psess:` “must not mint a second `producer_id` per tab if they are one UI process.” Local AD-24 / BOOTSTRAP / TRACE: each tab/process mints its own `producer_id`; `command_id` uniqueness is the session-layer guard. Parent wire dedupe is `(producer_id, id)`. Shared producer across tabs plus per-tab `id` counters is the collision Codex R7 described.

**Action:** chat companion must yield to local AD-24 (one `producer_id` per tab/process).

#### F-9 — `ChangeValidation-class` wording on graph validate vs parent AD-29 CR records

`AUTHORING-AND-ML.md` validate of an `editor_revision` uses “`ChangeValidation`-class verdict.” Parent `ChangeValidationRecord` is the change-request path. Cheap rename: topology/schema verdict vs CR `ChangeValidationRecord`.

#### F-10 — CHANGE-IMPACT still says “do not emit `caller_kind` until the amend lands”

Spine / local AD-8 now **refuse** pack invoke with `caller_kind_unsupported` until the daemon accepts the field (then emit closed `user|agent|workflow`). CHANGE-IMPACT line is the pre-amend omit-field instruction. Not a parent weaken if J-UI-13 capability mismatch is the live rule. Align the impact row with refuse-not-omit.

---

## Checked parents — hold (with findings)

| Inherited | Child binding | Status |
| --- | --- | --- |
| Parent AD-8 / DEC-0463 `psess:`, no third profile, layout not durable, Home may omit instance, closed `selected_refs` | AD-18 history not on the row; AD-4/AD-7/AD-22 kinds; Home chat without invoke | Hold |
| Parent AD-9 grant intersection; skills/HTML do not grant | AD-20 ActionContext + companion §6; AD-18 tool calls still invoke | Hold (F-3, F-4) |
| Parent AD-17 client; adapters not authority; dispose ≠ kill; native first | AD-19/AD-12 close=detach; AD-20 intercept; AD-23 cancel ≠ unmount | Hold |
| Parent AD-21 door parity; QMB-only operator CLI; no general shell | AD-19 `qmb host *`; no `qma-cli`; xterm preview; no qmb-as-invoke | Hold (F-6 numbering vs local AD-21) |
| Parent AD-24 envelope; `instance_id` on invoke; GrantRecord hop-compare | AD-18 not an invoke; AD-8/AD-20 invoke path; AD-21 Graph Run is `start` envelope | Hold on invoke (F-1 cancel grant; F-3 agent turn) |
| Parent AD-26 JobHandle vocab; `JobHandle.cancel`; first terminal wins | AD-23 / TRACE; not `stop_run`; `unknown` not cancellable | Hold axis (F-1) |
| Parent AD-29 CAS reconnect; three-record CR; no intent replay | AD-18 `list_mailbox` query; AD-21 CR path; AD-24 `command_id` | Hold (F-7) |
| Parent AD-30 lifecycle; install ≠ grant; tombstone | AD-20/AD-21 enable vs grant; EXAMPLES I3 | Hold |
| Parent AD-16 closed sqlite | AD-22 existing artifact path | Hold ingest; **F-5 drafts** |
| Parent AD-3/AD-4 template immutability; every public AD-3 call enveloped | AD-18 mailbox vs invoke split; AD-21 refuse | Hold (F-2 nested cancel) |
| Kit AD-1..AD-9 pack-and-grant, widgets, caller_kind, diagnosis, retry, unpinned adapters | AD-18..AD-24 + VIEW contract | Hold with F-2, F-4 |

---

## Proposed parent / kit amendments — tagging audit

| Move | Tagged? | Treated as already-true 09-18 text? |
| --- | --- | --- |
| Chat send is mailbox `send_message`, no envelope, no instance | local AD-18 `[CANDIDATE]`; companion R3 | **No.** Correct child shape. Does not rewrite parent AD-24 field list. |
| `list_mailbox` query | companion; CHANGE-IMPACT **add** | **No.** Additive CT-40. |
| `cancel_job` wire mapping to `JobHandle.cancel`, no envelope | local AD-23 `[CANDIDATE]` | **No** as envelope rewrite. **Untagged weaken** if “or can observe” ships (F-1). |
| `qmb host start\|status\|stop\|pair` | local AD-19 `[CANDIDATE]`; BOOTSTRAP | **No.** Parent AD-21 owner; named backend add. |
| Host-minted `ActionContext` | local AD-20 `[CANDIDATE]` | **No.** Tightening of parent AD-9/AD-17, not a new grant type. |
| Draft Run refused until registered template | local AD-21 `[CANDIDATE]` | **No.** Restates parent AD-4. |
| Daemon editor draft/revision store | AUTHORING companion only | **Untagged** vs parent AD-16 (F-5). |
| `stage_artifact` | local AD-22; existing artifact register | **No** if it stays that path. |
| `caller_kind` refuse until daemon accepts | named inspect honesty; kit AD-4 | **No** as 09-18 field. Inherited as kit law. Correct. |

---

## Gate disposition

Do **not** rewrite in this seat. Findings are apply-or-ignore for the sitting editor.

Blocking for a factory unit that only reads the spine: **F-1** (cancel-from-observe), **F-5** (draft sqlite), **F-6** (bare AD-24). F-2/F-3/F-4 are the same class if companions are treated as optional.

Documentation Factory and epics remain out of scope until the operator accepts the candidate.
