# Reviewer gate — LENS: parent / kit consistency

**Subject:** `architecture-QMX-UI-2026-09-23/ARCHITECTURE-SPINE.md` (local AD-1..AD-16, UI host, status draft)
**Against:** parent `architecture-QMX-2026-09-18/ARCHITECTURE-SPINE.md` AD-8, AD-9, AD-10, AD-15, AD-16, AD-17, AD-18, AD-21, AD-24, AD-26, AD-29, AD-30; kit `architecture-QMX-2026-09-23/ARCHITECTURE-SPINE.md` AD-1..AD-9; research `06-parent-invariants-for-ui.md`.
**Question this lens answers:** does any local AD weaken or silently override inherited parent/kit law? Do local `AD-n` numbers collide with parent `AD-n` / kit `AD-n` as if they were the same rule?
**Especially checked:** three-way AD-8 numbering; parent AD-8 / DEC-0463 sessions; parent AD-17 mount/dispose and adapters; parent AD-24/AD-29 envelope, retry, reconnect, change-request; kit AD-1..AD-8 pack-and-grant, widgets, diagnosis, retry, unpinned adapters.
**Date:** 2026-09-23. Reviewer: parent-consistency seat (independent). Spine only. No companions re-scored. No implementation.

**Verdict: PASS with Medium findings.**

No local AD mints a sixth COMP, treats json-render or MCP Apps as identity or grant, unions nested grants, persists layout on `product_session`, or says app-use may Apply. The Inherited section names those moves as **conflicts**. Envelope `instance_id` stays required. `caller_kind` is inherited as kit law and marked **absent** at `34c148b`. `view:*` stays a wire DTO. JobHandle vocabulary is the parent closed set. Native panes stay first.

What this lens will not bless as already-true parent law: local AD-12 window-close stopping a host-owned sidecar; local AD-11 reconnect as `producer_id` + `since_seq`; local AD-4 “instance selected” as a substitute for the authoring invoke gate; a UI Retry control that is a second invoke. Numbering is a factory hazard (F-1): local AD-8 is widgets, parent AD-8 is `psess:`, kit AD-8 is unpinned adapters.

---

## Numbering collisions

Research `06` binds: cite `architecture-QMX-2026-09-18` as **parent AD-n**; cite `architecture-QMX-2026-09-23` as **kit AD-n**; local UI ADs must not reuse those numbers as if they were parents. Factory prose must say `parent AD-8`.

The spine **states** that convention (`Local AD-n never means a parent or kit id`; Consistency Conventions; Capability map often prefixes `local`). It then **reuses** 1..16 anyway, which is unavoidable if the child numbers from AD-1, and it **drops the prefix** in Inherited compound cells and after the first id in the Capability map.

| Local UI | Parent 09-18 | Kit 09-23 | Factory misread if prefix dropped |
| --- | --- | --- | --- |
| AD-1 client, not COMP | AD-1 no sixth COMP | AD-1 pack-and-grant SDK | Least bad: local AD-1 aligns with parent AD-1/AD-17 |
| AD-2 host stack seed | AD-2 four discovery rails | AD-2 kit nouns; widgets never own invoke | Stack pin mistaken for Library-hit law |
| AD-3 one rail, three interiors | AD-3 Capability Operation Interface | AD-3 one copilot; many `psess:` | Layout mistaken for `input_schema` / copilot seats |
| AD-4 surface ≠ session | AD-4 Board ≠ graph ≠ Task Graph | AD-4 `caller_kind`; no live-graph merge | Tab law mistaken for MissionCompiler law |
| AD-5 independent dimensions | AD-5 mapping; no silent Cartesian | AD-5 host diagnosis | Headless chrome mistaken for join algebra |
| AD-6 three lanes; json-render seed | AD-6 DAG topology | AD-6 default host retry `none`/`read` | Adapter pin mistaken for retry matrix (or DAG) |
| AD-7 composer / `selected_refs` | AD-7 QMA procedure runtime | AD-7 weak models through schemas | Composer mistaken for Mission compile |
| **AD-8 widgets bind; host invokes** | **AD-8 `psess:` / profiles / layout** | **AD-8 adapters unpinned** | **Named three-way collision** |
| AD-9 graph / code / detail | AD-9 copilot; prose is not a grant | AD-9 graduation to pack | Graph chrome mistaken for grant intersection |
| AD-10 Library typed hits | AD-10 four composition modes | — | Library chrome mistaken for nested-grant law |
| AD-11 first-run / reconnect | AD-11 dummy Book forbidden | — | Splash chrome mistaken for ATC/dummy law |
| AD-12 daemon vs Tauri | AD-12 recipes; provider ≠ venue | — | Sidecar mistaken for recipe identity |
| AD-13 close / stop / cancel / unknown | AD-13 identities stay separate | — | JobHandle chrome mistaken for fp1/`instance_id` split |
| AD-14 ops chrome observes fencing | AD-14 sequential handover; no fill rollback | — | Dashboard mistaken for the fencing **machine** |
| **AD-15 `view:*` stays DTO** | **AD-15 five listing axes** | — | **View DTO mistaken for placement preflight** |
| **AD-16 ui-integration sibling** | **AD-16 store split; logs ≠ evidence; closed sqlite** | — | **Git stream mistaken for a UI sqlite / fourth store** |

Bare ids still in the spine:

- Inherited: `parent AD-15, AD-16` and `parent AD-18, AD-21, AD-24 / DEC-0464, AD-26, AD-29, AD-30` — every id after the first is unprefixed next to local AD-16 / AD-8 / AD-15.
- Capability map: `local AD-3, AD-4, AD-11`; `local AD-8, AD-6`; `local AD-11, AD-12` — `AD-8` here is widgets, not `psess:`.
- Section titles `### AD-8`, `### AD-15`, `### AD-16` are local. Body cites of parents are mostly prefixed (`parent AD-17`, `kit AD-8`, `parent AD-26`). That is the right pattern; the table/map are not.

SCN-0024 in the Capability map is a **cite** of the existing kit scenario (headless; panel cannot apply), not a new UI journey id. That is not a collision with `J-UI-01`..`J-UI-12`.

---

## Especially checked

### 1. Parent AD-8 / DEC-0463 — product sessions

**Parent 09-18 AD-8:** `psess:` ≠ `sess:`; closed immutable `{authoring, app-use}`; durable fields listed; layout / tab attachment **not** durable; closed `selected_refs` (no `instance_id` in the 09-18 list); install/upgrade MUST NOT mutate `granted_ops` or retarget `app_instance_id`; app-use mints change-request, must not edit source/grants/accounts.

**Kit named amendment (DEC-0463), inherited as kit law:** authoring MAY omit `app_instance_id`; app-use still requires it; `selected_refs` **gains** `instance_id`; no third profile; envelope / GrantRecord `instance_id` remain required.

**Child:** Conflict sentence includes persist-layout. Inherited row is `parent AD-8 / DEC-0463` from `09-18 + 09-23` (Home may omit instance; no third profile; layout not durable). Named-amendments paragraph restates the invoke gate (exactly one `selected_refs` kind `instance_id`). Local AD-4: tabs are chrome; no third profile; Home/main is authoring with instance absent until selected; in-app is optional `app-use`. Local AD-7 closed kinds include `instance_id` and forbid widget/layout/json-render trees. Conventions: layout JSON forbidden on `psess:`; client-local rail/widgets/tabs allowed.

**Ruling: holds on profiles, layout-not-durable, and no third seat.** DEC-0463 is tagged, not copied as original 09-18 text without the DEC. Envelope `instance_id` is not optionalized.

**Residual (F-4):** local AD-4 never restates the invoke gate, and “until an instance is selected” can be implemented as writing `app_instance_id` (or as invoking with zero/many `instance_id` refs). “Two tabs of one product share one `psess:`” is one word away from merging Home authoring with in-app `app-use` (profile is immutable at create). App-use must-not-Apply lives only in the conflict sentence, not in AD-4.

### 2. Parent AD-9 — grants not prose

**Parent:** tools = published ContributionHits ∩ host grants ∩ session GrantRecords ∩ health. Skills describe; they do not grant.

**Child:** Inherited row restates the intersection. Local AD-7: tool enablement **does not grant**. Local AD-6: MCP HTML cannot add tools; host intercepts `tools/call`. Local AD-1: no UI grant store. Local AD-10: a hit is not a grant.

**Ruling: holds.** Residual: composer “tool enablement” must remain a view over GrantRecords, not a mute grant mutation (parent AD-8 grant commands are named CAS ops).

### 3. Parent AD-10 — four modes; nested invoke does not union

**Parent:** consume artifact / invoke op / Graph Template / composite instance graph. Nested invoke does not union permissions. Partial failure does not silently substitute instance, version, or account.

**Child:** Conflict sentence includes union nested grants. Inherited row restates four modes + no union. Local AD-4: app switch does not merge transcripts or union grants. Local AD-8: no fifth composition mode; no `caller_kind=widget`; shared filters stay inside one instance. Local AD-9: live Task Graph merge refused; run is `MissionCompiler` of an already-registered template. Local AD-11: never silently retarget remote failure onto local.

**Ruling: holds.** No widget-to-widget runtime. No fifth mode.

### 4. Parent AD-15 / AD-16 — listing axes; logs ≠ evidence; closed sqlite

**Parent AD-15 Rule text:** `available` / configured / authorized / reachable / healthy. Training ≠ inference ≠ trading deployment.

**Parent AD-2 pointing at AD-15:** `published` / configured / **granted** / reachable / healthy.

**Kit AD-1:** `published` / configured / **authorized** / reachable / healthy, and `authorized` is **not** a session GrantRecord.

**Parent AD-16:** v1 daemon sqlite additions are a closed list; logs are not evidence; no second evidence DB.

**Child:** Inherited: five listing axes; logs are not evidence. Local AD-11 uses the **kit** five (`published`…`authorized`). Local AD-14 consumes those axes; logs are not evidence; no fourth observability product; do not extend `qmn/FAILURES.md`. Local AD-1: no UI identity store. No UI sqlite is minted.

**Ruling: store split and logs-not-evidence hold.** Axes follow kit/research `06`, not the parent AD-15 word `available` and not parent AD-2 `granted`. That is inherited kit drift, not a new UI dialect — provided `authorized` is never painted as `granted_ops` (F-9).

### 5. Parent AD-17 / kit AD-8 — client, adapters, mount/dispose, pin

**Parent AD-17:** host is a client of qma-wire / QMB / QMN; json-render and MCP Apps are presentation adapters, not identity, persistence, runtime, or authority; catalog names an existing AD-3 `op_id` and must not add/remove fields; catalog miss still allows native/CLI; MCP HTML must not grant; mount/dispose must not start/kill durable work; stale snapshot refuses invoke; native panes first; do not pin `@json-render/*` **in the 09-18 sitting**.

**Kit AD-8:** same adapter law; do not pin `@json-render/*` or MCP Apps **in the kit**; chrome is GAP-0081.

**Research `06`:** this UI sitting **may** pin **host** adapter versions as seed, with justification; must not pin them in Python core; must not make them identity/runtime.

**Child:** Paradigm + local AD-1: client, not `COMP-UI`. Local AD-6: three lanes, native first, catalog/`tools/call` law, frontend **may** depend on `@json-render/*` 0.21.0 as **optional** adapters, Python core must not. MCP Apps described, not version-pinned. Local AD-8: widget paints; shell issues the envelope; stale refuses; dispose must not start work. Local AD-13: close = `wire.detach`, not cancel. Local AD-15: no `ui_view` contribution point this sitting.

**Ruling: adapter-authority holds. Host seed pin is in the allowed class.** Residual: justification vs research `06` (Svelte compatibility, sandbox, failure/fallback) is thin (F-7). **Local AD-12 is the mount/dispose hole** (F-2): closing the desktop shell **may** stop a host-owned sidecar. That is dispose killing the local daemon — parent AD-17 Prevents “tab-close cancelling jobs”, QMA AD-5 / DEC-0304 “closing a client never stops an agent.”

### 6. Parent AD-18 / AD-30 — pack lifecycle; install ≠ grant

**Parent:** `downloaded → installed → validated → enabled ⇄ disabled → uninstalled`; install/enable is not grant; missing dep fails closed; disable/uninstall → `unavailable`/`tombstone`, never another version; export scanner is the oracle.

**Child:** Inherited blob: pack lifecycle; install is not grant. Local AD-10: unavailable/deleted → `unavailable`/`tombstone`. Local AD-15: published still does not grant. Local AD-5: headless pack with no `view:*` / no `copilot_profile` is invokable without navigation.

**Ruling: holds** where restated. Upgrade/rollback chrome “must not silently retarget a running instance or widen `granted_ops`” is not a local Rule (parent AD-8/AD-30 still bind via Inherited).

### 7. Parent AD-21 — door parity; no general shell

**Parent:** deep behaviour identical across that `op_id`’s supported doors; unsupported → `unsupported_door`; QMB is the only operator CLI; a log/progress panel is not a general shell.

**Child:** Local AD-5: equivalent operations must not depend on simulated clicks (cites parent AD-21); unsupported mixes refuse with a typed reason. Headless via `qmb` CLI / future wire. Local AD-12: may call `qmb` as a subprocess door the daemon already owns; must not `import qmb` / `qml` / `qmn`.

**Ruling: door parity holds if CLI means QMB.** Residual (F-10): local AD-3 “Hermes/Codex/Cowork family” and “tabbed preview/work area” can be built as a privileged general terminal.

### 8. Parent AD-24 / DEC-0464 / kit AD-4 / kit AD-6 — envelope, caller_kind, retry

**Parent AD-24:** envelope is signed/bound request context, not authority; `instance_id` required; GrantRecord immutable; `none`/`read` **may** retry; `external-egress` MUST NOT blind-retry; `reconcile_policy` is `query-then-decide` \| `unknown-manual` \| `never-retry`.

**Kit:** closed `caller_kind` `user | agent | workflow`; widgets never own invoke; default host retry on for `none`/`read` only; envelope `reconcile_policy` remains authoritative; `unknown-blocked` and CAS `conflict` are not retried.

**Child:** Named amendments: envelope `instance_id` required; `caller_kind` specified, absent at `34c148b`. Local AD-8: host issues envelope; `caller_kind=user` on operator press; no `caller_kind=widget`. Sequence: daemon compares GrantRecord. Local AD-13: duplicate submit coalesces on `idempotency_key` / envelope identity; `none`/`read` may follow kit default retry; UI Retry must not blind-retry `external-egress`, `unknown-blocked`, or CAS conflict.

**Ruling: effect matrix and required `instance_id` hold.** Residual (F-5): UI Retry is not bound to the same `logical_invocation_id` / `attempt_id` / `reconcile_policy`. Residual: “only the shell host” + `caller_kind=user` can drop `agent` (copilot tool call) and `workflow` (nested template `start`).

### 9. Parent AD-26 — JobHandle vocabulary

**Parent:** `queued` \| `running` \| `done` \| `failed` \| `cancelled` \| `aborted` \| `unknown`. Never `succeeded` or `awaiting_approval`. `unknown` is non-terminal. First durable terminal wins. Cancelled display is not proof of stop.

**Child:** Conventions list the parent set and the two forbidden words. Local AD-13: cancel = `JobHandle.cancel` only; `unknown` is non-terminal; first durable terminal wins; cancelled display is not proof of stop. Local AD-5: a renderer or open tab does not own JobHandle lifetime.

**Ruling: holds** unless AD-12 sidecar-stop is read as an implicit cancel of local handles (F-2).

### 10. Parent AD-29 — CAS reconnect; change-request completeness

**Parent / CONTRACTS §3:** mutate is CAS on `expected_revision` + `command_id`; reconnect is a **query** from `(resume_cursor, cursor_generation)`; never re-issues unacked intent without the original `command_id`; compacted history → snapshot/resync + new cursor generation. Change path is three records; app-use mints; authoring + operator apply; `promote` is L17.

**Parent UI-HOST.md (wire layer):** reconnect = `producer_id` + attach/`since_seq`; must not cancel jobs; must not replay intent.

**Child:** Conflict sentence includes replay unacked intent. Inherited AD-29 restated as **CAS reconnect** only. Local AD-11: reconnect is a query (`producer_id` + `since_seq` / product-session cursor); restores durable `psess:` fields; does not replay intent or imply approval. No local AD names the three change-request records or mint vs validate vs apply vs L17.

**Ruling: no-replay intent is stated. Reconnect **identity** is not parent AD-29.** Wire attach and `psess:` query are collapsed (F-3). Change-request apply-law is not a local Rule (F-4).

### 11. Kit AD-1..AD-9 (remainder)

| Kit | Child | Status |
| --- | --- | --- |
| AD-1 pack-and-grant SDK; `view:*` DTO; `copilot_profile` request blob; install ≠ grant; headless first-class | AD-5, AD-15, Inherited | Hold |
| AD-2 widgets never own invoke; COMP on the descriptor owns execution | AD-1, AD-8 | Hold |
| AD-3 one copilot; many sessions; in-app optional; authoring invoke gate; context transfer = `selected_refs` or `change_request` | AD-4, AD-7; gate only in Named-amendments paragraph | Hold with F-4 |
| AD-4 `caller_kind`; nested Mission not graph splice | AD-8, AD-9 | Hold (F-5 `user`-only reading) |
| AD-5 diagnosis; `failure_class=view` ≠ invoke; MUST expose `health()` | AD-8, AD-14 (`health()` **when it exists**) | Hold with F-8 |
| AD-6 default retry `none`/`read`; HMR dead | AD-13 | Hold matrix; F-5 Retry control |
| AD-7 weak models through schemas | AD-15 generated output is not an untracked path | Hold |
| AD-8 adapters unpinned **in kit** | AD-6 host seed pin, Python forbidden | Hold (allowed by research `06`; F-7) |
| AD-9 graduation to pack | not reopened | Hold (not contradicted) |

Workbench AD-12 rung 4: this sitting takes chrome (local AD-3) and **declines** to mint `ui_view` (local AD-15). That is a legal GAP-0081 decision, not a skip of host-grant law.

---

## Proposed parent / kit amendments — tagging audit

| Amendment | Tagged where | Treated as already-true 09-18 text? |
| --- | --- | --- |
| Parent AD-8 / DEC-0463: authoring MAY omit `app_instance_id`; `selected_refs` gains `instance_id`; no third profile | Inherited row `parent AD-8 / DEC-0463`; Named-amendments paragraph; local AD-4, AD-7 | **No** as original 09-18. **Yes** as kit law this sitting inherits. Correct child shape. Local AD-4/AD-7 do not cite DEC-0463. |
| Parent AD-24 / DEC-0464: `caller_kind` | Named-amendments paragraph; inspect honesty at `34c148b`; local AD-8 | **No** as 09-18 field list. Inherited as kit law. Correct. |
| Host pin of `@json-render/*` 0.21.0 | local AD-6; Stack; cites kit AD-8 for Python-not | **Not a parent rewrite** if it stays optional host adapter (research `06`). Unjustifiable if it becomes required runtime or a core dep. |
| Window-close may stop sidecar | local AD-12 `[ADOPTED]` | **Untagged exception** to parent AD-17 / DEC-0304. See F-2. |
| Reconnect = `producer_id` + `since_seq` | local AD-11 `[ADOPTED]` | **Wrong layer** if used as the `psess:` query. See F-3. |
| Decline `ui_view` contribution point | local AD-15; Deferred | **Not a parent rewrite.** Parent AD-17 already left it to a named increment; this increment says no. |

Frontmatter `Inherits architecture-QMX-2026-09-18 AD-1..AD-31 and architecture-QMX-2026-09-23 kit ADs` plus “Local `AD-n` never means a parent or kit id” is the right inheritance sentence. Compound Inherited cells and the Capability map do not keep it.

---

## Checked parents — hold

| Inherited | Child binding | Status |
| --- | --- | --- |
| Parent AD-1 no sixth COMP / no extra process type | Paradigm; local AD-1 no `COMP-UI`; Tauri must not orchestrate | Hold (F-2 sidecar lifecycle) |
| Parent AD-2 typed hits; hit ≠ grant; `view:*` DTO; GAP-0073 | local AD-10, AD-15 | Hold |
| Parent AD-3 `input_schema` only; envelope; path ≠ id | local AD-6, AD-7 | Hold |
| Parent AD-4 Board writes nothing; layers; MissionCompiler | local AD-8 layout client-local; local AD-9 | Hold |
| Parent AD-5 typed mappings; no ambient globals | local AD-8 | Hold |
| Parent AD-8 / DEC-0463 sessions, profiles, layout | local AD-4, AD-7; Conventions | Hold (F-1 number; F-4 gate/tabs/Apply) |
| Parent AD-9 intersection; skills do not grant | Inherited; AD-7 | Hold |
| Parent AD-10 four modes; no nested union | Inherited; AD-4, AD-8, AD-9 | Hold |
| Parent AD-11 no dummy Book; ungoverned ML | local AD-9 | Hold (not an Inherited-table row) |
| Parent AD-15 five axes | local AD-11, AD-14 | Hold kit wording (F-9) |
| Parent AD-16 logs ≠ evidence; closed sqlite | AD-14; AD-1 no UI store | Hold (F-1 number vs local AD-16) |
| Parent AD-17 client; adapters; dispose ≠ kill; native first | AD-1, AD-6, AD-8, AD-13 | Hold adapters (F-2 dispose; F-7 pin) |
| Parent AD-18 / AD-30 lifecycle; install ≠ grant; tombstone | Inherited; AD-10, AD-15 | Hold |
| Parent AD-21 door parity; QMB-only operator CLI; no general shell | AD-5, AD-12 subprocess `qmb` | Hold if F-10 applied |
| Parent AD-24 envelope; `instance_id`; effect matrix | Named amendments; AD-8; AD-13 | Hold matrix (F-5 Retry) |
| Parent AD-25 fencing machine; `unknown-blocked` never auto-retry | AD-14 observation only; AD-13 no blind retry | Hold |
| Parent AD-26 JobHandle vocab | Conventions; AD-13 | Hold |
| Parent AD-29 CAS reconnect; three-record CR; app-use cannot apply | Conflict sentence; AD-11 no-replay | Hold no-replay (F-3 identity; F-4 Apply) |
| Kit AD-1..AD-9 as in §11 | AD-1..AD-15 | Hold with F-4, F-5, F-7, F-8 |
| DEC-0304 close client ≠ stop agent | AD-13 detach | Hold unless F-2 |
| DEC-0366 HMR dead | not restated locally; kit inherit | Hold (silence) |

---

## Findings

### High

None that fail the parent-law bar. The Medium items below are editor-applicable so a factory unit cannot treat local `AD-8` as `psess:` law, cannot stop `qma-daemon` on window dispose, cannot reconnect `psess:` with `since_seq`, and cannot Retry as a new invoke.

### Medium

#### F-1 — Local AD-8 / AD-15 / AD-16 numbers collide with parent and kit

**Where:** `### AD-8`, `### AD-15`, `### AD-16`; Inherited compound cells; Capability map `local AD-8, AD-6`.

**Parents / kit:** parent AD-8 = product sessions (DEC-0463 lives here). Kit AD-8 = presentation adapters unpinned. Parent AD-15 = listing axes. Parent AD-16 = store split / logs ≠ evidence.

**What:** Research `06` named this sitting’s collision. The spine’s convention is correct; its own tables do not always follow it. Two units can both “obey”:

- Unit A implements local AD-8 as widget-bind / host-invoke (the Rule).
- Unit B skims “AD-8” and optionalizes `app_instance_id` on widgets, or unpins json-render because “AD-8 says adapters stay unpinned,” or adds a UI sqlite because “AD-16 is the integration stream.”

**Action:** apply. In every Inherited cell and Capability-map cell, prefix **every** id (`parent AD-18, parent AD-21, …`; `local AD-8, local AD-6`). Once under Consistency Conventions: “local AD-8 is widgets (parent AD-17 / kit AD-2); parent AD-8 is `psess:`; kit AD-8 is unpinned adapters. local AD-15 is `view:*` DTO (parent AD-17); parent AD-15 is listing axes. local AD-16 is the git sibling stream; parent AD-16 is stores/logs.” Do not retitle local ADs in this sitting unless the operator wants a `UI-AD-n` scheme.

#### F-2 — Local AD-12 lets window-close stop the sidecar (untagged parent AD-17 / DEC-0304 exception)

**Where:** Invariants prose “spawn or attach a local daemon”; local AD-12 “host-supervised local daemon”; “Closing a desktop shell **may** stop a **host-owned sidecar** only when the operator chose ‘stop local runtime’.”

**Parents:** AD-17 mount/dispose must not start/kill durable backend work. QMA AD-5 / DEC-0304: closing a client never stops an agent. AD-26: cancel is a JobHandle verb; cancelled display is not proof of stop. AD-1: `qma-daemon` is an allowed process — the UI is not its owner that dies with a window.

**What:** Start-local as an **explicit** first-run command (AD-11) is compatible. Coupling daemon lifetime to shell dispose is not. Two units:

- Unit A: browser/Tauri is a client; `wire.detach` never stops `qma-daemon` or QMB children; Stop Runtime is a separate granted op.
- Unit B: sticky “stop local runtime” + window close kills the sidecar; local JobHandles vanish without `JobHandle.cancel`; remote/QMN work is the only work that survives.

Unit B is a silent override of parent AD-17. “Must not cancel work already on QMN or a remote environment” does not save local durable work.

**Action:** apply. One clause on AD-12: closing a tab, browser, or desktop window is `wire.detach` only (local AD-13). It never stops `qma-daemon`, QMB process-per-run children, or QMN. “Stop local runtime” is an explicit operator command, distinct from dispose, and still must not cancel in-flight handles (cancel remains AD-13 / parent AD-26). Spawn/attach of a local daemon is first-run / settings, not view mount.

#### F-3 — Local AD-11 reconnect identity is not parent AD-29

**Where:** local AD-11 “Reconnect is a query (`producer_id` + `since_seq` / product-session cursor).”

**Parents:** AD-29 / CONTRACTS §3: `psess:` reconnect is a query from `(resume_cursor, cursor_generation)`; snapshot/resync on compacted history; never re-issues unacked intent without the original `command_id`. Wire attach (`producer_id`, `since_seq`) is QMA AD-5 / UI-HOST.md — a **different** layer that also must not replay intent.

**What:** The slash collapses two queries. A unit that `attach(since_seq=0)` to “restore durable `psess:` fields” will replay the session journal, including unacked commands — the conflict sentence this spine already forbids. Parent names are `resume_cursor` and `cursor_generation`, not “product-session cursor.”

**Action:** apply. Split the sentence: (1) wire reattach is `initialize` / `wire.attach` with `producer_id` + `since_seq` and does not stop agents; (2) `psess:` restore is a query from `(resume_cursor, cursor_generation)` then snapshot/resync; (3) neither replays unacked intent; (4) reconcile authoritative snapshot before any new command (research `06`).

#### F-4 — Local AD-4/AD-7 omit the authoring invoke gate, mint-vs-Apply, and tab cardinality

**Where:** local AD-4 “Two tabs of one product share one `psess:`”; “`app_instance_id` absent until an instance is selected”; local AD-7 lists `instance_id` as a `selected_refs` kind; Capability map cites SCN-0024 only for headless invoke.

**Parents / kit:** kit AD-3 / DEC-0463: authoring with absent instance **may not invoke** until exactly one `selected_refs` kind `instance_id` is present; zero or many → `INVALID_INPUT`; envelope `instance_id` still required. Parent AD-8: profile immutable at create — authoring and app-use cannot share a row. Parent AD-29 / SCN-0019 / SCN-0024: app-use mints `change_request`; must not apply; three records; L17 `promote` is not this path. Research `06` topic 16: mint / validate / apply / L17 as distinct chrome.

**What:** Named-amendments paragraph has the invoke gate; local ADOPTED rules do not. Two units:

- Unit A: Home stays authoring-with-absent-instance; invoke only after a single `selected_refs` `instance_id`; in-app is a different `app-use` row; Apply is authoring + operator.
- Unit B: selecting an instance writes `app_instance_id` onto the Home row and invokes; two chrome tabs of “the product” share one row across Home and a mini-app (union grants / mixed profiles); in-app panel has Apply because AD-4 never forbids it.

**Action:** apply. On AD-4: (1) two **chrome** tabs of one `{profile, app_instance_id-or-absent, principal}` share one `psess:` — Home authoring and in-app `app-use` are different rows; (2) authoring invoke gate copied from kit AD-3; (3) in-app may mint `change_request` and must not apply. On AD-7: cite DEC-0463 for the `instance_id` kind.

#### F-5 — Local AD-13 UI Retry can be a second invoke

**Where:** local AD-13 “Duplicate submit … coalesces on `idempotency_key` / envelope identity; `none`/`read` may follow kit default retry. UI Retry must not blind-retry `external-egress`, `unknown-blocked`, or CAS conflict.”

**Parents / kit:** AD-24 effect matrix + `reconcile_policy`. Kit AD-6: default-on is host retry of `none`/`read` until success, `retryability=NO`, or the host ceiling; `never-retry` / `unknown-manual` win; not a new dispatch.

**What:** The forbidden list is correct and incomplete. A UI Retry button that mints a new `logical_invocation_id` is a second effect even on `read`. A button that retries `never-retry` envelopes, `append-evidence`, `mutate-config`, or `place-run` as “the user asked again” drops parent AD-24. Host default-on plus a UI Retry loop double-retries `none`/`read`.

**Action:** apply. UI Retry **is** the host retry surface: same `logical_invocation_id`, incremented `attempt_id`, envelope `reconcile_policy` authoritative. No Retry control on `external-egress`, `unknown-blocked`, `never-retry`, `unknown-manual`, or CAS `conflict`. Copilot / nested template envelopes use `caller_kind=agent` / `workflow` (do not freeze AD-8 at `user`).

#### F-6 — Structural Seed `src/lib/host/ … grants` vs local AD-1 query-only

**Where:** Structural Seed `src/lib/host/ # qma-wire client, grants, JobHandle`; local AD-1 `ProductSessionChrome` “stay query-only.”

**Parents:** AD-24 host resolves GrantRecord from authoritative stores; the UI does not. AD-9 intersection. AD-16 no extra sqlite.

**What:** A folder named `grants` in the UI package will be implemented as a client grant cache that mints or widens `granted_ops`. AD-1 already says query-only; the seed invites the opposite.

**Action:** apply. Rename the seed to query helpers (`grant_id` display, listing axes, JobHandle). `ProductSessionChrome` mounts `view:*` on an existing `psess:` and writes no grant, occupancy, or layout into the session (research `11` already had this; the spine should say it).

### Low

#### F-7 — `@json-render/*` 0.21.0 seed lacks the research-`06` evidence clause

Allowed as **optional host** adapter (not identity, not Python core, catalog miss still invokes). Research `06` still wanted Svelte compatibility, sandboxing, host messaging, failure/fallback, and grant interception **evidenced** before the pin. MCP Apps stay unpinned (fine).

**Action:** apply if cheap. One sentence on AD-6: pin is host-seed, optional, fallback-to-native on catalog/load failure; intercept every `tools/call`; re-verify 0.21.0 at scaffold.

#### F-8 — Local AD-14 `health() when it exists` can drop kit AD-5

Kit AD-5: host **MUST** expose instance `health()` headless. Inspect-SHA absence is wiring honesty (DEC-0465), not an optional contract.

**Action:** apply if cheap. Consume `health()` as a required host query; at `34c148b` the live server/field may be missing — that is inspect honesty, not a pack opt-out.

#### F-9 — Listing axes: `published`/`authorized` vs parent AD-15 `available` vs parent AD-2 `granted`

Local AD-11 copies kit AD-1. Do not paint provider `authorized` as session `granted_ops`, and do not drop `available` if a unit is tracing parent AD-15 literally.

**Action:** ignore if AD-11 cites kit AD-1 and says `authorized` ≠ GrantRecord; else one parent-AD-15 alias sentence.

#### F-10 — Local AD-3 “Cowork/Hermes” interiors vs parent AD-21 no general shell

Tabbed preview is chrome. A privileged shell that is a second operator CLI, or that makes equivalent ops require simulated clicks, is parent AD-21.

**Action:** apply if cheap. Preview/terminal hosts are specialized surfaces; QMB remains the only operator CLI; dispose/keyboard follow local AD-13.

#### F-11 — Inherited AD-29 restated as “CAS reconnect” only

Drops three-record change-request completeness (F-4 covers the apply split).

**Action:** ignore if F-4 lands.

#### F-12 — Local AD-5 “typed reason” vs `unsupported_door`

**Action:** ignore if the typed reason is parent AD-21 `unsupported_door` when the mix is a door; else name it.

---

## Non-conflicts (do not amend parents as if already true)

- **DEC-0463 authoring-with-absent-instance** and **DEC-0464 `caller_kind`:** inherited as kit law, tagged, inspect-honest at `34c148b`. Envelope/GrantRecord `instance_id` stay required.
- **Declining `ui_view` as a contribution point (local AD-15):** parent AD-17 already left the increment unnamed; this sitting may take chrome without minting the plugin point. Packs still contribute operations only. Published ≠ grant.
- **Host seed pin of `@json-render/*` 0.21.0 as optional frontend adapters:** research `06` explicitly allows this class; kit AD-8’s “do not pin **here**” is the kit sitting. Unjustifiable only if it becomes identity/runtime or a `qma-core`/`qma-daemon` dep (it does not, as written).
- **Svelte 5 + SvelteKit 2 + shadcn-svelte + Svelte Flow; Qt out; paid kits out:** GAP-0081 host-stack choice. Not a parent COMP rewrite.
- **Client-local rail / widget positions / open tabs:** parent AD-4/AD-8 “layout not durable **on `psess:` / sqlite**.” Research `06` already allows client-local prefs.
- **Three interiors (main copilot / mini-app / authoring-ML) plus headless packs:** local AD-5 keeps presentation independent of execution. Not a requirement that every pack ship a canvas.
- **Library one chrome over typed hits; hypothesis off facade; GAP-0073 stays:** parent AD-2.
- **Non-trading ML without Book / universal paper gate:** parent AD-11 class 3.
- **Cutover readiness as observation (local AD-14):** parent AD-25 remains the machine; GAP-0100 chrome may exist as a surface.
- **`qma-ui-contract` remains stub:** honest vs Workbench AD-12 rung 4; not a sixth COMP.
- **ui-integration sibling cut from `integration@34c148b`:** delivery, not a parent AD-16 store mint, if F-1/F-6 keep grants/sqlite out of the UI package.
- **Citing SCN-0024 for headless invoke:** existing kit scenario, not a reused UI journey id.

---

## What would be a real conflict (do not do)

| Move | Conflicts |
| --- | --- |
| Mint `COMP-UI` or a UI sqlite / grant store / scheduler | Parent AD-1, AD-16, AD-24 |
| Third `ProductSessionProfile` named home/platform | Parent AD-8 |
| Persist rail/widget/Board/json-render trees on `psess:` | Parent AD-4, AD-8 |
| Invoke from authoring with zero/many `selected_refs` `instance_id`, or optionalize envelope `instance_id` | Kit AD-3, parent AD-24, DEC-0463 |
| App-use Apply; skip `ChangeValidationRecord`; treat apply as L17 `promote` | Parent AD-29, SCN-0019, SCN-0024 |
| Union nested grants; fifth composition mode; widget-owned invoke; `caller_kind=widget` | Parent AD-10, kit AD-2/AD-4 |
| json-render / MCP Apps as identity, grant, persistence, or Python-core runtime | Parent AD-17, kit AD-8 |
| Catalog miss = cannot invoke | Parent AD-17 |
| Tab/window dispose cancels JobHandles or stops `qma-daemon` | Parent AD-17, AD-26, DEC-0304 |
| Replay unacked intent on `attach(since_seq=0)` | Parent AD-29 |
| Blind-retry `external-egress` / `unknown-blocked` / CAS `conflict` | Parent AD-24, AD-25, kit AD-6 |
| Paint `unknown` as `failed`; `succeeded` / `awaiting_approval` on a handle | Parent AD-26 |
| Collapse Artifact/Knowledge/Contribution; treat a hit as a grant | Parent AD-2, AD-9 |
| Silent retarget of instance/version/account; tombstone → another version | Parent AD-10, AD-30 |
| Dummy Book on data-ML; hot-swap live; dashboard filter as command target | Parent AD-11, AD-14, AD-8, AD-23 |
| Privileged general shell / new `qma`/`qmn` CLI | Parent AD-21 |
| `failure_class=view` as an invoke failure | Kit AD-5 |
| HMR / hot-apply of implementation | Kit AD-6, DEC-0366 |

---

## Summary

Parent and kit law hold on the load-bearing bars this sitting was forbidden to weaken: no sixth COMP, adapters are not authority, nested grants do not union, layout is not a `psess:` field, JobHandle vocabulary is closed, envelope `instance_id` stays required, app-use Apply is named as a conflict, `view:*` stays a DTO.

Amend F-1..F-6 so factory prose cannot confuse local AD-8 with parent AD-8 or kit AD-8, cannot kill the daemon on window dispose, cannot reconnect `psess:` with `since_seq`, cannot skip the authoring invoke gate or mint-vs-Apply split, cannot Retry as a new invoke, and cannot put a grant store in `apps/qmx-ui`.
