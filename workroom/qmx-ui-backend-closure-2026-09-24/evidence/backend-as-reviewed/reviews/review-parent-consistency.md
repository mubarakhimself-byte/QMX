# Reviewer gate — LENS: parent / kit / QMA consistency

**Subject:** `architecture-QMX-UI-BACKEND-2026-09-24/ARCHITECTURE-SPINE.md` (local AD-1..AD-16, backend-delta, status draft) plus `PARENT-AMENDMENT-MAP.md` and load-bearing companions (`PAIRING-AND-ADMISSION.md`, `MAILBOX-AND-DELIVERY.md`, `CANCEL-AND-HANDLES.md`, `ARTIFACTS-AND-TRANSFER.md`, `PACK-UI-AND-AUTHORING.md`, `HOST-LIFECYCLE.md`, `DEPENDENCY-MAP.md`).
**Against:** QMA `architecture-QMA-2026-08-28` AD-5, AD-6, AD-17, AD-20, AD-21, AD-22, AD-24, AD-27; parent `architecture-QMX-2026-09-18` AD-8, AD-17, AD-21, AD-24, AD-26, AD-29, AD-30 (and AD-16 where the closed sqlite list binds); kit `architecture-QMX-2026-09-23` AD-1..AD-9; UI candidate `architecture-QMX-UI-2026-09-23` AD-1..AD-24; `epics-QMA-2026-08-29` Story 41.4 and Story 46.4; `epics-PACK-AND-GRANT-2026-09-23` Story 60.1; `epics-WORKFLOWS-2026-09-19` Story 57.3; `epics-QMA-2026-08-29` Story 41.1 / 41.3 / 42.2 as closed-and-addable owners.
**Question this lens answers:** does any local AD weaken an inherited invariant without a named amendment? Is any named amendment actually a silent override (wrong ID, missing owner, JobHandle state change, `copilot_profile` move)?
**Especially checked:** unauthenticated bind (QMA AD-5 / AD-24 / Story 41.4); closed store/projection list (QMA AD-6 / AD-8 / FR-Q23 / Story 42.2 / parent AD-16); JobHandle states (QMA AD-17 / parent AD-26 / Story 57.3); mailbox Envelope (QMA AD-20 / Story 46.4); plugin manifest / `copilot_profile` (QMA AD-21 / kit AD-1 / Story 60.1); staging one-type (QMA AD-22); secret/principal custody (QMA AD-24); backup/migration (QMA AD-27); QMB-only CLI (parent AD-21); envelope `instance_id` (parent AD-24); reconnect (parent AD-29); pack enable (parent AD-30).
**Date:** 2026-09-24. Reviewer: parent-consistency seat. No implementation.

**Verdict: RETURN-FOR-AMENDMENT.**

The sitting names the large conflicts and does **not** change JobHandle states or move `PluginManifest.copilot_profile` into `PackUiRequest`. Envelope `instance_id` stays required. No sixth COMP. No new CT. MessageKind / DeliveryState stay closed. Those holds are real.

Two inherited closed lists are still not honestly owned, so two factory units can both “obey” and ship different products:

1. **AM-01’s unauthenticated path list is narrower than this sitting’s own HTTP surface.** CORS preflight for `/pair/renew`, snapshot GET, and `PUT /artifacts/stage` is unauthenticated `OPTIONS` on paths AM-01 does not name. Authenticated `POST /pair/renew` is a mutating HTTP command outside Story 41.1’s three families and outside AM-05 (PUT-only). `DEPENDENCY-MAP.md` already calls renew a proposed amendment and gives it **no AM-id**.
2. **AM-03 amends “not a new sqlite class” while omitting the owners of the closed projection list.** Parent 09-18 AD-16’s v1 daemon additions are a **complete list**. Story 42.2’s declaration validator **refuses a store outside that list**. Neither is an Inherited-contract cell on AM-03.

Until those two amendments name the real parents and the real extra paths/projections, the map’s opening claim (“nothing silently overrides”) is false.

---

## Numbering collisions

The spine states the right convention: local `AD-n` never means parent, kit, QMA, or UI. Factory prose that drops the prefix still collides.

| Local backend-delta | QMA 08-28 | Parent 09-18 | Kit 09-23 | UI 09-23 | Factory misread if prefix dropped |
| --- | --- | --- | --- | --- | --- |
| AD-5 unauthenticated pairing carve-out | **AD-5 wire contract; unauthenticated bind is hard startup refusal** | AD-5 mapping | AD-5 diagnosis | AD-5 headless/visual/mixed | **AM-01 applied to the wrong AD-5, or QMA AD-5 treated as already allowing pairing HTTP** |
| AD-6 `qmb host` process door | AD-6 one journal / closed stores | AD-6 DAG | AD-6 host retry | AD-6 presentation lanes | Host verbs mistaken for store-list law |
| AD-8 `originating_psess` on the handle **record** | AD-8 state ownership | **AD-8 `psess:`** | AD-8 unpinned adapters | AD-8 widgets | Additive handle field mistaken for product-session optionality (DEC-0463) |
| AD-10 PackUiRequest ingest | AD-10 hooks | AD-10 four modes | — | AD-10 Library | Request DTO mistaken for a contribution point |
| AD-16 no sixth COMP / no new CT | AD-16 tool registry | **AD-16 complete v1 sqlite additions** | AD-16 ui-integration (UI sitting) | AD-16 ui-integration | Local “no new CT” mistaken for parent AD-16’s closed sqlite list (see F-2) |

Bare ids still appear in Inherited compound cells (`parent AD-18 / AD-30`, `parent AD-24 / DEC-0464`). Body Rules mostly prefix (`QMA AD-24`, `parent AD-26`, `UI AD-18`). Keep the prefix on every factory sentence.

---

## Especially checked

### 1. QMA AD-5 / AD-24 / Story 41.4 — authenticate before protocol; no unauthenticated bind

**Parents:** QMA AD-5 transport posture: loopback default; non-loopback needs TLS plus recorded operator config; **every client authenticates with a Credential-Broker-resolved credential before protocol bytes**; **an unauthenticated bind is a hard startup refusal**. QMA AD-15 repeats: the daemon’s own listener is never unauthenticated. QMA AD-24 transport custody: authenticate before protocol; client credential is a broker-resolved reference. Story 41.4 AC: plaintext non-loopback or unauthenticated bind → hard startup refusal; credential_ref authenticates first; daemon never dials in.

**Child:** AM-01 / local AD-5: unauthenticated HTTP **only** on `POST /pair/start`, `POST /pair/confirm`, and **their** `OPTIONS`. All other HTTP and all WebSocket still authenticate first. Browser proof is `pairing_session_id`; daemon maps to `AuthenticatedWireSession`. Machine clients still use `credential_ref`. AM-11: pairing id is not a CredentialRef; traces use key `pairing_session_id`. AM-06: destination **pulls**; daemon remains the single inbound listener.

**Ruling: the bind carve-out and the browser-proof substitution are named, not silent.** Story 41.4’s unauthenticated-bind sentence is correctly on the hold list in `DEPENDENCY-MAP.md`. Dial-out law is not inverted.

**Residual (F-1, F-4):** AM-01’s inherited-contract cell omits QMA AD-5 (the wire AD that *is* the unauthenticated-bind rule) and QMA AD-15’s “listener is never unauthenticated.” The path list does not cover this sitting’s HTTP surface (renew POST; OPTIONS on authenticated routes). See Findings.

### 2. QMA AD-6 / AD-8 / FR-Q23 / Story 42.2 / parent AD-16 — closed stores

**Parents:** QMA AD-6: a store not on the closed list may not be created; v1 folds are an exact list; **a new fold is a spine amendment** and must declare a fold contract. QMA AD-8: ownership table is that same closed list. FR-Q23 / Story 42.2 AC: the declaration validator accepts **only** the listed projections plus five independent stores **and refuses a store outside that list**. Parent 09-18 AD-16: **v1 daemon additions (complete list)** = `product_session`, persist `task_graph_state`+outbox, mini-app instance rows, GrantRecord rows; **no other new sqlite**. Kit AD-2: closed QMA store classes stay closed.

**Child:** AM-03 / local AD-4 / AD-11: add journal projections `pairing_pending`, `pairing_session`, `editor_draft_head`, `artifact_transfer_ticket`. Still not a new sqlite **class**. Migrations follow QMA AD-27. Local Inherited table cites QMA AD-5 / AD-6 / AD-8 and does **not** cite parent AD-16.

**Ruling: intending a named closed-list amendment is correct; the IDs are wrong/incomplete, so the closed list can still be silently widened.** “Not a new class” satisfies kit AD-2 and does **not** satisfy Story 42.2 or parent AD-16. Fold contracts for the new projections are not declared. Local AD column on AM-03 is AD-4, AD-11 — transfer ticket is local AD-9.

### 3. QMA AD-17 / parent AD-26 / Story 57.3 — JobHandle states

**Parents:** States exactly `queued` \| `running` \| `done` \| `failed` \| `cancelled` \| `aborted` \| `unknown`. Never `succeeded`. `awaiting_approval` is a Mission/Task gate. Terminal = `done`/`failed`/`cancelled`/`aborted`. `unknown` is non-terminal and holds `environment_lease`. Timeout / lost supervisor → `unknown`, never `failed`/`aborted`. First durable terminal wins; later commands are no-ops. Story 57.3: vocabulary **exactly**.

**Child:** AM-04 / local AD-8 / conventions / section C: additive immutable `originating_psess` at admit; **states unchanged**. Nested Epic 63 children store their own field. `unknown` is not cancellable (`unknown.resolve` only). `qmb host stop` may leave local handles `unknown` (lost supervisor), not a new state. `stop_run` stays a different verb.

**Ruling: not a silent override of JobHandle states.** Additive field on the **record**, not a seventh state, not `succeeded`, not `awaiting_approval`. Treating cancel-of-unknown as forbidden **upholds** QMA AD-17 (no invented terminal).

**Residual (F-5):** AM-04 inherited-contract cell is QMA AD-17 + parent AD-26. `DEPENDENCY-MAP.md` says **amend Epic 57 handle record**. Story 57.3 is the owner of “vocabulary exactly” and is missing from the AM-04 cell.

### 4. QMA AD-20 / Story 46.4 — mailbox Envelope

**Parents:** Envelope members are the Story 46.4 / QMA AD-20 list (msg id, from, to, kind, optional mission/task, `correlation_id`, optional `reply_to_ref`/`causation_id`, body, artifact refs, priority, creation time). MessageKind and DeliveryState are closed. Bus is non-authoritative. Mailbox is a projection over `message.*`. Delivery owner is Story 46.4, not Epic 41.

**Child:** AM-02 / local AD-7: additive `product_session_id`; replies inherit and refuse retarget; Story 46.4 remains delivery owner. AM-08: addable query `list_mailbox`. Section C: MessageKind / DeliveryState unchanged. Chat uses a subset of kinds; `approval_request` is still gate-raised.

**Ruling: the Envelope field add is named. Delivery owner is not relabelled “Epic 41 mailbox.” Closed kind/state sets are not opened.**

**Residual (F-3):** local AD-7 also persists `(producer_id, wire_id)` + payload hash and **refuses a different hash for journal lifetime**, “stricter than `registry:wire.dedup_window`.” That is Story 41.3 / QMA AD-5 / QMA AD-26 cursor-window law. `DEPENDENCY-MAP.md` §4 row “Wire pair + payload hash on journal” is classed **proposed amendment** and has **no AM-id**. AM-02’s proposed text only names `product_session_id`.

### 5. QMA AD-21 / kit AD-1 / Story 60.1 — plugin manifest and `copilot_profile`

**Parents:** PluginManifest is the load/enable surface; reversible load; contributions through scoped context. Kit AD-1 / Story 60.1: optional `copilot_profile` is a **request blob on the pack**, not a contribution point and not a grant. Install/enable is not a grant. `view:*` is a wire DTO, not a `ui_view` point.

**Child:** local AD-10 / `PACK-UI-AND-AUTHORING.md` / map section B: host ingests at most one `qmx.ui.pack_ui_request.v1` at enable; **not** a contribution point; **`PluginManifest.copilot_profile` stays Epic 60 Story 60.1**; **no parent amendment to nest it**. Nav items bind `view_ids`. Zero/one/≥2 GrantRecords as already UI-closed. `DEPENDENCY-MAP.md`: Epic 60.1 **do not hold**.

**Ruling: not a silent move of `copilot_profile`.** PackUiRequest is additional chrome request, not a replacement of Story 60.1.

### 6. QMA AD-22 — staging is one RefinementProposal type

**Parents:** staging store has exactly one record type, RefinementProposal. Nothing agent-produced becomes runtime state by itself.

**Child:** AM-07 claims this contract. Proposed amendment: drafts use artifact-store bytes + `editor_draft_head` (AM-03) and **do not enter AD-22 staging**. Section C repeats AD-22 still one type. Local AD-11: QMA AD-22 staging remains one record type; first Run is parent AD-30 enable, not a second enable machine.

**Ruling: AD-22 is not weakened.** AM-07 is **mis-ID’d** (it is a non-amendment of AD-22 plus reuse of AM-03), not a silent second staging type.

### 7. QMA AD-24 principals and secrets / parent AD-21 door

**Parents:** principal class `operator` \| `machine`; human-gate command list is **closed-and-addable and the sole authority**, extended only by a spine amendment. Secrets are refs; allowlist is code. Parent AD-21: QMB is the only operator CLI.

**Child:** AM-10 / local AD-6: add QMB group `host` with `start|status|stop|pair|pair-revoke`. Not a sixth COMP. Not a second orchestrator. Pair confirm is operator principal + internal CredentialRef. Local AD-12: allowlist stays `qma-core` code; browser selects an already-resolvable ref; no secret on the wire.

**Ruling: no new CLI, no allowlist widening, no venue keys in QMA.** `pair` / `pair-revoke` as daemon writes are not named against the QMA AD-24 human-gate list (F-4).

### 8. QMA AD-27 / parent AD-18 / AD-30 / AD-29 / AD-8 / AD-17 / AD-24 envelope

**Parents:** migrations follow five-step backup-first order; unknown store version refuses. Pack lifecycle downloaded→…→enabled; compile-at-enable; install is not grant. Reconnect is a query; no intent replay. Authoring `app_instance_id` optional is already DEC-0463 / Epic 60 (reuse). Envelope `instance_id` required; `caller_kind` already DEC-0464 / Epic 60 (reuse). UI is a client; mount does not kill work.

**Child:** AM-03 cites QMA AD-27 for migrations. Local AD-11 first Run = publish into local authoring pack → enable (parent AD-30) → grant → select `instance_id` → `dispatchInvoke`. Local AD-14 / AD-7: reload queries; cold start never auto-resends. Local AD-16: no sixth COMP, no new CT, envelope `instance_id` stays required. Map section B reuses Epic 60 amendments and does not re-author them.

**Ruling: holds.** Backup/restore is not replaced. Enable machine is not forked. Reconnect is not replay. `caller_kind` / authoring optionality are tagged reuse, not Inherited-table rewrites of 09-18 text.

### 9. Kit AD-1..AD-9 / UI AD-12 families / Story 41.1 seed counts

**Kit:** pack-and-grant SDK; widgets never own invoke; one copilot identity; `caller_kind` on one envelope; diagnosis; host retry; weak models through schemas; adapters unpinned; tested work graduates to a pack.

**Child:** widgets must not import the wire client (CANCEL companion). Invoke remains envelope + GrantRecord. PUT is named AM-05 as a **byte channel**, not a fourth message family, not REST invoke, not a BFF. AM-08 / AM-09 name the seed seven queries / nine commands as closed-and-addable and add `list_mailbox`, `cancel_job`, `transfer_artifact`. `stop_run` stays distinct.

**Ruling: seed-count adds are the legal closed-and-addable path and are named.** PUT vs three families is named (AM-05). Pairing HTTP POST / authenticated renew is **not** covered by AM-05 (F-1).

---

## Proposed parent amendments — tagging audit

| ID | Claimed inherited contract | Actually binds? | Silent override? |
| --- | --- | --- | --- |
| AM-01 | QMA AD-24; Story 41.4 unauthenticated bind; credential_ref before protocol | **Partial.** Real twins are **QMA AD-5** (and AD-15 listener sentence) + 41.4 + AD-24. Path list omits renew POST and OPTIONS on authenticated HTTP. | Incomplete ID + extra unauth/mutate paths unnamed. **Yes if shipped as written.** |
| AM-02 | QMA AD-20; Story 46.4 Envelope members | Yes for `product_session_id`. Extra journal keys + journal-lifetime collision live on local AD-7 / DEPENDENCY-MAP without an AM-id. | Envelope add is honest. Dedup tighten is unnamed (F-3). |
| AM-03 | QMA AD-6 / AD-8 / FR-Q23 | **Missing owners:** Story 42.2 validator list; **parent AD-16 complete v1 additions**. Conflict text omits transfer ticket; local AD column omits AD-9. No fold contracts. | **Yes as “not a new class” without amending the closed lists.** |
| AM-04 | QMA AD-17 record; parent AD-26 states stay closed | States hold. Missing owner **Story 57.3 / Epic 57**. | Not a state override. Missing owner. |
| AM-05 | QMA AD-5 / UI AD-12 three families | Honest for **PUT `/artifacts/stage`**. Does not cover pairing POST or renew. | Not silent for PUT. |
| AM-06 | Story 41.4 daemon never dials in | Honest: destination pulls as `machine`. | No. |
| AM-07 | QMA AD-22 one staging type | **Wrong ID.** Does not amend AD-22. Drafts are AM-03 + artifact store. Section C already lists this as a non-amendment. | Not an AD-22 override. Mis-tagged amendment. |
| AM-08 | Epic 41.1 seed seven queries | Honest addable query. Owner `qma-wire`. | No. |
| AM-09 | Epic 41.1 seed nine commands | Honest addable `cancel_job`, `transfer_artifact`. Does not mint `stage_artifact` as a command (capability flag only). | No. |
| AM-10 | QMB `COMMAND_GROUPS` / parent AD-21 | Honest as a QMB door add. **Missing QMA AD-24 human-gate list** for `pair` / `pair-revoke` daemon writes. | Missing owner on the gate list. |
| AM-11 | inspect `authenticate_before_protocol` / `FORBIDDEN_SECRET_SURFACE_KEYS` | Implementation-shape guard for AM-01. Not a parent AD by itself. | No. |
| — | `POST /pair/renew` | `DEPENDENCY-MAP.md` “proposed amendment (AD-3 path 2)” | **Unnamed in section A.** |
| — | Wire pair + hash / journal-lifetime refuse | `DEPENDENCY-MAP.md` “proposed amendment” citing 46.4 + 41.3 | **Unnamed in section A.** |
| — | CORS OPTIONS on authenticated HTTP | Needed by SPA origin ≠ 8765; called out in `reviews/reconcile-inputs.md` | **Unnamed widening of AM-01.** |
| — | PackUiRequest ingest | New DTO beside Epic 60; does not conflict if `copilot_profile` stays put | Not a parent conflict if AD-10 holds. |
| Epic 60 reuse | `app_instance_id` optional; `caller_kind`; `selected_refs` kind `instance_id`; `copilot_profile` | Section B. Not re-authored. | No. |

The Inherited table does **not** copy AM-01..AM-11 in as already-true parent text. That half of the tagging rule holds.

---

## Checked parents — hold / hole

| Inherited | Child binding | Status |
| --- | --- | --- |
| QMA AD-5 unauthenticated bind / three families / broker cred before protocol | AM-01 + AM-05 + AM-11 | **Hole** (F-1, F-4) |
| QMA AD-6 / AD-8 / FR-Q23 / Story 42.2 closed list | AM-03 | **Hole** (F-2) |
| Parent 09-18 AD-16 complete v1 sqlite additions | not cited | **Hole** (F-2) |
| QMA AD-17 / parent AD-26 / Story 57.3 JobHandle states | AM-04; section C | **Hold** (owner cell incomplete) |
| QMA AD-20 / Story 46.4 Envelope + closed kinds | AM-02; delivery stays 46.4 | **Hold** field add; **hole** on 41.3 window (F-3) |
| QMA AD-21 reversible plugin load | PackUiRequest ingest at enable | Hold |
| QMA AD-22 one RefinementProposal type | AD-11; section C; drafts out of staging | Hold (AM-07 mis-tagged) |
| QMA AD-24 principals, secrets, human-gate list | AD-12 allowlist; AM-10 QMB door | **Hold** allowlist; **hole** on gate list (F-4) |
| QMA AD-27 backup/migration | AM-03 “migrations follow AD-27” | Hold |
| Parent AD-8 / DEC-0463 authoring optionality | section B reuse Epic 60 | Hold |
| Parent AD-17 client host; adapters not authority; dispose ≠ kill | paradigm; no COMP-UI | Hold |
| Parent AD-21 QMB-only operator CLI | AM-10 adds a QMB group, not a new CLI | Hold |
| Parent AD-24 envelope `instance_id` required; `caller_kind` planned | local AD-16; section B | Hold |
| Parent AD-26 first terminal wins; `later_commands` | local AD-8; Epic 57 reuse | Hold |
| Parent AD-29 reconnect is query; no intent replay | local AD-14 / AD-7 | Hold |
| Parent AD-30 enable / compile-at-enable | local AD-11 first Run | Hold |
| Kit AD-1 `copilot_profile` on the pack | local AD-10; Story 60.1 **do not hold** | **Hold — not moved** |
| Kit AD-2 closed store **classes**; widgets never own invoke | AM-03 class sentence; cancel companion | Hold class; list still F-2 |
| Story 41.4 daemon never dials in | AM-06 pull | Hold |
| Story 41.1 seed 9/7/10 closed-and-addable | AM-08 / AM-09 | Hold |
| Story 41.3 `registry:wire.dedup_window` | local AD-7 journal lifetime | **Hole** (F-3) |

---

## Findings

### High

#### F-1 — AM-01 names a smaller unauthenticated/HTTP surface than the sitting ships

**Where:** AM-01; local AD-5; local AD-3 path 2; `PAIRING-AND-ADMISSION.md` §3 and §5; `ARTIFACTS-AND-TRANSFER.md` PUT; `DEPENDENCY-MAP.md` §2 renew row; `reviews/reconcile-inputs.md` OPTIONS note.

**Parents:** QMA AD-5 / AD-24 / Story 41.4: no unauthenticated bind; credential before protocol bytes. Story 41.1: commands mutate on JSON-RPC WebSocket; queries read on HTTP GET; events are the stream.

**What:** Two units can both “obey AM-01”:

- Unit A refuses every unauthenticated request except `POST /pair/start`, `POST /pair/confirm`, and those two `OPTIONS`. Browser CORS preflight for `POST /pair/renew`, GET snapshots, and `PUT /artifacts/stage` dies. SPA cannot renew or PUT.
- Unit B serves unauthenticated `OPTIONS` on those authenticated paths, and serves mutating `POST /pair/renew` as HTTP (not JSON-RPC). That is a **wider** unauthenticated bind and a **fourth command transport** than AM-01/AM-05 name.

`DEPENDENCY-MAP.md` already classifies authenticated `/pair/renew` as a **proposed amendment** with no AM-id. AM-05 covers PUT as a byte channel only. AM-01’s inherited-contract cell never cites **QMA AD-5**.

This is a local rule (AD-3 + AD-5 + PAIRING CORS) that weakens Story 41.4 / QMA AD-5 / Story 41.1 **beyond the named carve-out**.

**Action:** apply. Widen AM-01 (or add a sibling AM) so the named exception list is exactly: unauthenticated `POST /pair/start`, `POST /pair/confirm`, and **OPTIONS on every daemon HTTP path the SPA preflights** (start, confirm, renew, snapshot GET, PUT `/artifacts/stage`). Name `POST /pair/renew` as authenticated pairing HTTP, not a CT-40 family and not Origin-only issuance. Put **QMA AD-5** (and AD-15 listener sentence) in the inherited-contract cell beside Story 41.4 / QMA AD-24.

#### F-2 — AM-03 does not name the owners of the closed projection list

**Where:** AM-03; local AD-4; local AD-11; ARTIFACTS transfer ticket; Inherited table (QMA AD-6 / AD-8 only).

**Parents:** Story 42.2 / FR-Q23 / QMA AD-6: validator refuses a store outside the closed list. Parent 09-18 AD-16: v1 daemon additions are a **complete list**; no other new sqlite. QMA AD-6: a new fold is a spine amendment and must declare its fold contract.

**What:** AM-03’s proposed text is “still not a new sqlite **class**.” That is kit AD-2. It is **not** Story 42.2 and **not** parent AD-16.

- Unit A adds `pairing_pending` / `pairing_session` / `editor_draft_head` / `artifact_transfer_ticket` inside existing sqlite and leaves Story 42.2’s accepted-list fixture unchanged. 42.2 must refuse those names.
- Unit B amends Story 42.2 and parent AD-16 to include the four projections and writes fold contracts.

Local AD-16 is “no sixth COMP / no new CT.” Parent AD-16 is the sqlite complete list. Dropping the prefix makes F-2 worse.

Transfer ticket is in AM-03’s proposed list but not in the conflict column and not in the local-AD column (should include local AD-9).

**Action:** apply. AM-03 inherited contract = **QMA AD-6 / AD-8 / FR-Q23 / Story 42.2 / parent AD-16**. Proposed text: extend those closed **projection/fold** lists with the four named projections; still not a sixth store class; each fold declares stream / ordering key `journal_seq` / knowledge-time bound / equal-instant disposition; migrations remain QMA AD-27 five-step. Local ADs: AD-4, AD-9, AD-11.

### Medium

#### F-3 — Mailbox collision “journal lifetime” silently overrides Story 41.3

**Where:** local AD-7; `MAILBOX-AND-DELIVERY.md`; `DEPENDENCY-MAP.md` §4 “Wire pair + payload hash on journal”.

**Parents:** Story 41.3 / QMA AD-5: wire command idempotency is `(producer_id, id)` **within** `registry:wire.dedup_window`. QMA AD-26: that window is a registered variable. Parent AD-29 journal-lifetime retention is the **product-session `command_id`** namespace, a different identity (UI AD-24 already splits them).

**What:** The sitting keeps the stricter rule and calls it a proposed amendment in the dependency map, then **does not give it an AM-id**. AM-02 only names Envelope `product_session_id`. Two units:

- Unit A honours `registry:wire.dedup_window` for `send_message`.
- Unit B refuses a different hash of the same pair for **journal lifetime**.

Not a weakening of uniqueness (it tightens), but it **is** an unnamed override of 41.3’s window. The map’s “every conflict is named here” sentence fails.

**Action:** apply. Either add AM-12 (mailbox wire-pair identity retains for journal lifetime; 41.3 window remains the default for other seed commands) or drop the “stricter than” sentence and keep 41.3.

#### F-4 — AM-10 / AM-01 missing QMA AD-24 human-gate ownership

**Where:** AM-10; `HOST-LIFECYCLE.md` `qmb host pair` / `pair-revoke`; QMA AD-24 closed human-gate list.

**Parents:** QMA AD-24: the human-gate list is closed-and-addable and is **the sole authority** on which commands require `operator`; extended only by a spine amendment. `OperatorPrincipalRequired` otherwise.

**What:** AM-10 names a QMB `COMMAND_GROUPS` add (parent AD-21). `pair` / `pair-revoke` write daemon pairing rows as operator principal. Without a named add to the AD-24 list:

- Unit A treats pair/revoke as QMB-only OS actions; the daemon accepts the write from any authenticated principal that can reach the projection.
- Unit B adds pair/revoke to the human-gate list and refuses `machine`.

That is how a missing owner becomes a silent weaken of the gate list.

**Action:** apply. AM-10 inherited contract += QMA AD-24 human-gate list. Add `pair.confirm` and `pair.revoke` (names as the sitting prefers) as operator-only daemon commands. Keep `start|status|stop` as process supervision, not wire gates.

#### F-5 — AM-04 missing Story 57.3 owner; AM-07 is the wrong ID

**Where:** AM-04; AM-07; section C; `DEPENDENCY-MAP.md` Epic 57 hold.

**What:** AM-04 does **not** change JobHandle states (hold). It still omits Story 57.3, whose AC is “vocabulary exactly” plus the recorded field set (`logical_run_id`, `attempt_id`, artifact completeness). Additive `originating_psess` must be a named 57.3 record amendment, states still closed.

AM-07 lists QMA AD-22 as the inherited contract and then **does not change AD-22**. Section C already says AD-22 stays one RefinementProposal type. That is a non-amendment wearing an AM-id. Harmless to AD-22, noisy for the factory (someone will “amend staging” because the map said so).

**Action:** apply. AM-04 inherited contract += Story 57.3 / Epic 57 handle **record** (states remain QMA AD-17). Move AM-07’s row into section C, or rewrite it as “explicit non-amendment of AD-22; drafts are AM-03.”

### Low

#### F-6 — Local AD-5 / AD-8 / AD-16 numbers collide with the parents they amend

Covered in Numbering collisions. AM-01 is “the AD-5 carve-out” next to QMA AD-5. AM-04 is local AD-8 next to parent AD-8 `psess:`. Local AD-16 next to parent AD-16 sqlite list (F-2).

**Action:** apply if cheap. Every AM inherited-contract cell and every factory sentence uses `QMA AD-n` / `parent AD-n` / `local AD-n`.

#### F-7 — `initialize` capability `stage_artifact` vs PUT-only ingest

**Where:** local AD-13 capability list; AM-09 command adds (`cancel_job`, `transfer_artifact` only).

**What:** A builder can mint a JSON-RPC `stage_artifact` command because it was advertised, which AM-05 forbids (PUT is the byte channel). Not a parent weaken yet; name the capability as “PUT stage supported,” not a tenth seed command.

**Action:** apply if cheap. AD-13 / PROVIDER-AND-COMPAT: `stage_artifact` means authenticated PUT `/artifacts/stage` is available, not a JSON-RPC verb.

---

## Non-conflicts (do not treat as silent overrides)

- **JobHandle states** `queued`/`running`/`done`/`failed`/`cancelled`/`aborted`/`unknown`: named AM-04 says unchanged; companions obey; `unknown` not cancellable upholds QMA AD-17.
- **`PluginManifest.copilot_profile`:** stays Story 60.1 sibling; AD-10 forbids nesting in PackUiRequest; Epic 60.1 is not held.
- **Envelope `instance_id` required on invoke:** local AD-16; section C; DEC-0464 reused, not rewritten.
- **No sixth COMP / no new CT / no `qma-cli` / no COMP-UI.**
- **QMB remains the only operator CLI:** `host` is a new **group**, not a new COMP.
- **Story 41.4 dial-out:** AM-06 destination pull; daemon never dials in.
- **Story 46.4 delivery owner:** not relabelled Epic 41; AM-02 is additive field.
- **MessageKind / DeliveryState closed sets.**
- **Cookies / `localStorage` still refused** for pairing proof; `sessionStorage` is UI-local and is not operator identity.
- **Grant intersection / GRANT_AMBIGUOUS:** does not replace parent AD-9; no first-wins.
- **First Run = local authoring pack enable then `dispatchInvoke`:** parent AD-30 reuse, not a second enable machine.
- **caller_kind / authoring `app_instance_id` optional / `selected_refs` kind `instance_id`:** section B reuse of Epic 60; not copied into the Inherited table as original 09-18 text.
- **QMA AD-22 one staging type:** actually preserved (AM-07 is mis-tagged, not a second record type).
- **Credential allowlist stays code.**
- **Reconnect does not auto-resend.**
- **Widgets never own invoke.**

---

## What this lens will not bless until F-1 and F-2 land

- AM-01 as a complete Story 41.4 / QMA AD-5 exception.
- AM-03 as a complete closed-store amendment.
- The map sentence “every conflict with inherited contracts is named here.”

JobHandle state vocabulary and `copilot_profile` placement are already blessable.

---

## Reviewer action for the sitting

Return the amendment map (and local AD-3/AD-5/AD-7/AD-4 cells as needed) with:

1. AM-01 path list = actual unauthenticated HTTP the SPA needs, plus QMA AD-5 in the inherited cell, plus named `POST /pair/renew`.
2. AM-03 owners = Story 42.2 + parent AD-16 + fold contracts; local AD-9 on the transfer ticket.
3. One AM-id for journal-lifetime mailbox identity **or** drop it back to Story 41.3.
4. AM-10 += QMA AD-24 human-gate names; AM-04 += Story 57.3; AM-07 demoted to section C.

Do not implement. Do not run Documentation Factory. Do not rewrite Epic 60.1.
