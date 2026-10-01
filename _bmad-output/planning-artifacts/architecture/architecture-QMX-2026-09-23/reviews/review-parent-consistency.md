# Reviewer gate — LENS: parent / sibling consistency

**Subject:** `architecture-QMX-2026-09-23/ARCHITECTURE-SPINE.md` (local AD-1..AD-8, pack-and-grant kit, status draft)
**Against:** parent `architecture-QMX-2026-09-18/ARCHITECTURE-SPINE.md` AD-1..AD-31 (especially AD-8, AD-10, AD-17, AD-24, AD-29); parent `CONTRACTS.md`; SCN-0019; SCN-0021.
**Question this lens answers:** does any local AD weaken or silently override an inherited parent AD? Proposed parent amendments must be tagged, not copied into the Inherited table as already-true parent text.
**Especially checked:** named AD-8 `app_instance_id` amendment; AD-10 composition; AD-17 adapters; AD-24 retry; AD-29 change-request.
**Date:** 2026-09-23. Reviewer: parent-consistency seat (grok-4.6).

**Verdict: PASS with Medium findings.**

No inherited identity, grant, composition-mode, adapter-authority, effect-class, or change-request apply law is contradicted or silently rewritten. The one parent field change this sitting needs (`product_session.app_instance_id` optional on `authoring`) is listed as a **named parent amendment** and is not restated in the Inherited table as already-true parent AD-8 text. Nested invoke still does not union grants. JSON Render / MCP Apps stay presentation adapters. App-use still cannot apply a change-request. Effect-class retry still follows parent AD-24 (including no blind `external-egress`).

What this lens will not bless as already-true parent law: local AD-4’s required `caller_kind` on the parent InvocationEnvelope (untagged AD-24 schema mint), and local AD-6 “retry on by default for every pack” if read as dropping envelope `reconcile_policy` (`never-retry` \| `unknown-manual`) or auto-retrying AD-25 `unknown-blocked`.

---

## Especially checked

### 1. Named AD-8 `app_instance_id` amendment

**Parent (Workflows AD-8):** `product_session` is a journal-projected overlay, not a QMA `Session`. `ProductSessionProfile` is the closed enum `{authoring, app-use}`, immutable at create. Durable fields include `app_instance_id` (pointer to plugin-install instance row) with no MAY-absent. Installation/upgrade MUST NOT mutate `granted_ops` or retarget `app_instance_id`. Packs ship a copilot integration profile as a **request**, not a grant.

**Child:** Inherited table restates profiles and grant-not-prose only. After the table: **Named parent amendment:** for `profile=authoring` `app_instance_id` MAY be absent (main/home, nothing selected); for `profile=app-use` it remains required; no third profile. CONTRACTS §3 repeats the tag. COPILOT-AND-APPS delta table matches. Envelope `instance_id` and GrantRecord `instance_id` are not made optional.

**Ruling: not a silent override.** The required-looking parent field is declared as an amendment. App-use still needs an instance. No third `ProductSessionProfile`. Invoke of another app still carries that app’s instance on the envelope (J-KIT-03 selects B, then invokes B). Parent “MUST NOT retarget `app_instance_id`” still binds when the field is present.

**Residual (F-3):** local AD-8 is “Presentation adapters stay unpinned.” Named amendment is also “AD-8.” A skimming epic can apply optionality to the wrong AD-8.

### 2. AD-10 composition

**Parent:** Four modes, none compulsory: consume saved artifact; invoke exported AD-3 op; coordinate via Graph Template; composite as instance graph (not a Library kind). Nested invocation does **not** union permissions or propagate caller tools. Composite authority is host-granted **intersection**. Bounded invocation cycles need a recursion budget; template topology remains a DAG (AD-6). Partial failure does not silently substitute provider or account.

**Child AD-4:** Restates the four modes. Widgets bind or display ops; they do not mint a fifth mode. Nested invoke still does not union grants. Recursion budget remains. Workflow-to-workflow is **nested Mission** (`start` / `query-state` / `cancel` / `await` of template `(qualified_id, version)`). Authoring may **include** a subgraph into a new versioned template. Merging two live Task Graphs is refused.

**Ruling: holds.** Nested Mission is parent AD-3 lifecycle on a Graph Template (mode 2/3), not a new mesh and not a splice of two live Task Graphs (parent AD-4/AD-7: one compile → one Mission → one Task Graph). Live-merge refusal tightens parent AD-4; it does not weaken it. No union of nested grants.

### 3. AD-17 adapters

**Parent:** Host is a client of qma-wire / QMB / QMN. JSON Render and MCP Apps are **presentation adapters** — not identity, persistence, runtime, or authority. json-render catalog MUST name an existing AD-3 `op_id` and MUST NOT add/remove fields. MCP App HTML MUST NOT grant tools; host intercepts. UI mount/dispose must not start/kill durable work. Do not pin `@json-render/*`. Chrome stays GAP-0081.

**Child:** Inherited table restates that sentence. Local AD-8 / AD-7 / CONTRACTS §7 repeat: catalog `action` names existing `op_id`; `tools/call` is host-intercepted against GrantRecords; native panes first; do not pin `@json-render/*` or `@modelcontextprotocol/ext-apps`; chrome remains GAP-0081 / GAP-0100. Running work is not cancelled by panel dispose.

**Ruling: holds.** Child does not treat adapters as identity or grant. Pinning is still refused. GAP-0081 chrome stays deferred.

### 4. AD-24 retry

**Parent:** Envelope is signed/bound request context, not authority. Effect outcomes: `none`/`read` **may** retry; `append-evidence` dedupes; `mutate-config` is CAS; `place-run` uses `logical_invocation_id`; `external-egress` obtains a receipt or becomes `unknown` and MUST NOT blind-retry. `reconcile_policy` is `query-then-decide` \| `unknown-manual` \| `never-retry`. Nested calls carry parent id + depth. Ambiguous instance/config refuses.

**Child AD-6:** Host/SDK retry on by default for every pack. Effect classes “follow parent AD-24 / SCN-0021” with the same five-class matrix, including no blind `external-egress`. Pack may declare **tighter** retry, not looser. CONTRACTS §2: same `logical_invocation_id` / `attempt_id` / effect-class retry as parent. J-KIT-06: `read` flakes retry; `external-egress` without receipt → `unknown`.

**Ruling: effect matrix holds — not a silent rewrite of MUST-NOT-blind-retry.** “On by default” is a host policy over parent’s MAY for `none`/`read`, not a new effect class.

**Residual (F-1, F-2):** (a) `caller_kind` is a new required envelope field, not in parent AD-24’s closed list and not in the named-amendment list. (b) “On by default for every pack” can be implemented as ignoring `never-retry` / `unknown-manual`, or as retrying AD-25 `unknown-blocked` / AD-29 CAS `conflict`. SCN-0021 is outbox/JobHandle, not the retry matrix.

### 5. AD-29 change-request

**Parent / SCN-0019:** Three records: immutable `ChangeRequest` (paired `{target_ref, base_hash}`, `request_hash` over requester facts+patch only); separate `ChangeValidationRecord`; append-only `ChangeApplyRecord`. App-use mints only. Authoring **+ operator principal** applies. `promote` remains L17. v1 instance/grants/jobs stay. Reconnect is a query; it does not replay unacked intent. CAS on `expected_revision`.

**Child:** Conflict sentence: app-use applying a change-request is a **conflict**, not an override. AD-3/AD-6: app-use may mint; must not apply; authoring + operator apply. Alerts never authorize. HMR/hot-apply stay dead. Reconnect resumes queries/events; no replay of unacked intent. CONTRACTS: parent remains envelope/GrantRecord/JobHandle/pack-lifecycle authority.

**Ruling: holds on the load-bearing split.** Mint vs apply vs promote is not inverted. Three-record completeness is not replaced in the child CONTRACTS (parent file stays authority).

**Residual (F-4):** J-KIT-02 says “Operator mints a change-request; authoring applies v2” — drops validator record, `request_hash`/`base_hash`, and operator principal on apply.

---

## Proposed parent amendments — tagging audit

| # | Amendment | Tagged where | Treated as already true? |
| --- | --- | --- | --- |
| 1 | Parent AD-8: `app_instance_id` MAY be absent when `profile=authoring`; required when `app-use`; no third profile | Inherited section (“Named parent amendment”); CONTRACTS §3; Deferred “Third ProductSessionProfile” | **No** in Inherited table. **Yes** as this sitting’s local law (AD-3, COPILOT-AND-APPS, IMPLEMENTATION-SEQUENCE). Correct child-sitting shape. |
| — | Parent AD-24: required `caller_kind: user \| agent \| workflow` | Local AD-4 `[ADOPTED]`; CONTRACTS §2 “plus”; Structural Seed | **Not named.** Treated as filling silence. See F-1. |
| — | Pack may omit copilot profile / in-app panel | Local AD-1/AD-3; parent AD-17 already has headless packs without navigation; parent AD-8 profile is request-not-grant | **Not a parent-law rewrite.** Clarifies headless. |

Frontmatter `binds: [architecture-QMX-2026-09-18-AD-1-through-AD-31]` plus “Local ADs do not renumber them” is the right inheritance sentence.

---

## Checked parents — hold

| Inherited | Child binding | Status |
| --- | --- | --- |
| Parent AD-1 no sixth COMP / no extra process | Paradigm; AD-2 named connect/extend; Must-not sixth COMP | Hold |
| Parent AD-2 ContributionHit ≠ grant; `view:*` is DTO | AD-1 request/grant; AD-7 ContributionHit ≠ grant | Hold |
| Parent AD-3 descriptor + envelope | AD-1; nested Mission uses parent lifecycle verbs | Hold |
| Parent AD-4/AD-6/AD-7 layers; DAG; one compile → one Mission | AD-4 nested Mission; live-graph merge refused | Hold |
| Parent AD-8 product_session / closed profiles | Named amendment only on `app_instance_id` optionality; no third profile | Hold (F-3 number collision) |
| Parent AD-9 skills do not grant | AD-7 | Hold |
| Parent AD-10 four modes; no nested union | AD-4 | Hold |
| Parent AD-15 five listing axes | AD-5 including `healthy` | Hold |
| Parent AD-16 logs ≠ evidence; closed v1 sqlite list | AD-5; no new store | Hold |
| Parent AD-17 adapters; no pin; dispose ≠ cancel | Local AD-8; AD-3 | Hold |
| Parent AD-18/AD-30 pack lifecycle; install ≠ grant | AD-1 | Hold |
| Parent AD-21 headless parity; QMB is the only operator CLI | AD-5 headless diagnosis | Hold (F-6 CLI wording) |
| Parent AD-24 envelope + effect matrix + GrantRecord immutable | AD-6 matrix; CONTRACTS defers | Hold matrix (F-1 field mint; F-2 default-on) |
| Parent AD-25 `unknown-blocked` never auto-retry | Inherit, do not re-elicit | Hold if F-2 applied |
| Parent AD-26 JobHandle = QMA AD-17 vocab | AD-5 | Hold |
| Parent AD-29 three-record CR; app-use cannot apply; CAS reconnect | AD-3/AD-6 | Hold (F-4 companion) |
| DEC-0366 HMR dead | AD-6 | Hold |

---

## Findings

### High

None that fail the parent-law bar.

### Medium

#### F-1 — `caller_kind` is an untagged parent AD-24 envelope mint

**Where:** local AD-4 `[ADOPTED]` “parent AD-24 InvocationEnvelope plus a closed `caller_kind`”; CONTRACTS §2; Consistency Conventions “Caller”; Structural Seed `qma-core` “envelope caller_kind”; IMPLEMENTATION-SEQUENCE step 1.

**Parent (AD-24 / CONTRACTS §1b):** closed envelope fields are `logical_invocation_id`, `attempt_id`, `op_id`/`op_version`, contribution tuple, `instance_id`, `config_revision`, optional caller/callee `psess:` refs, `grant_id`, `effect_class`, `idempotency_key`, `reconcile_policy`, `input_hash`, optional `parent_logical_invocation_id`, `call_depth`. Caller identity on the envelope is `psess:`, not `user|agent|workflow`.

**What:** Adding a required field to that list is a parent schema amendment. The child names only AD-8 `app_instance_id`. CONTRACTS §0 (“only adds what that sitting left silent”) treats `caller_kind` as silence-fill. Two units can both “obey”:

- Unit A ships parent envelope unchanged; caller is the `psess:` + GrantRecord principal.
- Unit B refuses every public call lacking `caller_kind`.

That is how an additive mint becomes a silent parent override in the factory.

**Action:** apply. Put `caller_kind` on the named-parent-amendment list (AD-24 envelope additive, closed enum, does not replace `psess:` refs or GrantRecord principal). Keep it out of the Inherited table as already-true parent text.

#### F-2 — “Retry on by default for every pack” can drop `never-retry` / fencing / CAS conflict

**Where:** local AD-6; REQUIREMENTS-ADDENDUM “Ordinary failures retry in the host by default”; IMPLEMENTATION-SEQUENCE step 3; J-KIT-06.

**Parents:** AD-24 `none`/`read` **may** retry; `reconcile_policy` includes `never-retry` and `unknown-manual`; `external-egress` MUST NOT blind-retry. AD-25 `unknown-blocked` is a terminal branch; operator reconcile mints a new attempt — never automatic retry. AD-29 `conflict(current_revision)` is not an ordinary flake.

**What:** The five-class matrix in AD-6 is correct. The slogan is not. A host that retries every failed public call “by default” will retry `never-retry` envelopes, `unknown-manual` egress, fencing `unknown-blocked`, and session CAS conflicts. Child memlog already lists those as illegal if called self-heal; the spine Rule does not.

**Action:** apply. One clause on AD-6: default-on applies only where parent AD-24 permits (`none`/`read`, and idempotent replay of the same `logical_invocation_id` for the other classes). Envelope `reconcile_policy` remains authoritative. AD-25 `unknown-blocked` and AD-29 `conflict`/`duplicate` are not host-retried. Cite parent AD-24 (and SCN-0021 only for outbox/JobHandle identity), not SCN-0021 as the retry matrix.

#### F-3 — Local AD-8 number collides with the named parent AD-8 amendment

**Where:** Inherited “Named parent amendment: **AD-8 `app_instance_id`**”; local `### AD-8 — Presentation adapters stay unpinned`.

**Parent:** AD-8 is product sessions. AD-17 is UI host / adapters.

**What:** Local ids “do not renumber” parents, but the amendment citation is bare `AD-8`. Factory prose can optionalize `app_instance_id` on the adapter AD, or treat local AD-8 as rewriting product sessions.

**Action:** apply. Write **parent AD-8** on the named amendment (already used in AD-3 body). Local presentation rule should cite **parent AD-17**, which it already does in the Capability map.

### Low

#### F-4 — J-KIT-02 abbreviates AD-29 / SCN-0019

“Operator mints; authoring applies v2; v1 stays” omits app-use-as-minter, `ChangeValidationRecord`, `request_hash` / base hashes, and operator principal on apply. Spine AD-6 still has authoring + operator.

**Action:** apply if cheap. Align J-KIT-02 with SCN-0019: app-use mints → authoring validates → authoring + operator applies; three records; v1 untouched.

#### F-5 — SCN-0021 is the wrong retry oracle

SCN-0021 pins outbox successor dispatch and QMA AD-17 JobHandle vocab. Effect-class retry is parent AD-24 / CONTRACTS §1b (and AF-02 / `never-retry` tests in CHALLENGE-RECONCILIATION).

**Action:** ignore if F-2’s cite fix lands.

#### F-6 — AD-5 “CLI” vs parent AD-21 QMB-only operator CLI

Parent: QMA/QMN ship no operator CLI; unsupported door → `unsupported_door`. Child AD-5 Binds includes CLI; IMPLEMENTATION-SEQUENCE “copilot/CLI”.

**Action:** ignore if CLI means QMB-owned doors over the same diagnosis query; else one word: no new `qma`/`qmn` CLI.

---

## Non-conflicts (do not amend parents as if already true)

- **Authoring-with-absent-instance** vs parent durable `app_instance_id`: named amendment, not Inherited-table rewrite. Envelope/GrantRecord `instance_id` stay required at invoke.
- **Pack may omit copilot profile:** parent AD-17 headless packs; parent AD-8 profile is a request. Not a must-ship-one law.
- **Widget never owns invoke:** tightening of parent AD-10/AD-17 invoke authority (`AD-9 ∩ GrantRecord`). J-KIT-04 caller is `user`/`agent` on the envelope.
- **JSON Render / MCP Apps unpinned:** restates parent AD-17; extra MCP pin-ban is additive.
- **No sixth COMP / no QMB-QML core fork / no live-money kit examples:** inherits AD-1/AD-11/AD-23; does not reopen ATC.
- **Reconnect does not replay unacked intent:** parent AD-8/AD-29.
- **Install/enable ≠ grant:** parent AD-13/AD-18/AD-30.

---

## What would be a real conflict (do not do)

| Move | Conflicts |
| --- | --- |
| Treat `app_instance_id` optional as already-true parent AD-8 without the named tag | Parent AD-8 durable field list |
| Mint a third `ProductSessionProfile` for home/general | Parent AD-8 closed enum |
| Make envelope/GrantRecord `instance_id` optional because the session has no primary instance | Parent AD-24 ambiguous-instance refusal |
| Union nested grants or propagate caller tools | Parent AD-10 |
| Fifth composition mode (widget runtime, live Task Graph merge) | Parent AD-4/AD-10 |
| Pin `@json-render/*` or MCP Apps as identity/runtime/grant | Parent AD-17 |
| App-use applies `change_request`; skip validation record; treat apply as `promote` | Parent AD-29 / SCN-0019 |
| Blind-retry `external-egress`; auto-retry AD-25 `unknown-blocked` | Parent AD-24/AD-25 |
| Sixth COMP; QMA `import qmb`; dummy Book | Parent AD-1/AD-11 |

---

## Summary

Parent law holds. The sitting names the AD-8 `app_instance_id` amendment, keeps AD-10’s four modes and no-union rule, keeps AD-17 adapters unpinned and non-authoritative, keeps AD-24’s effect matrix (including no blind egress retry), and keeps AD-29’s mint-vs-apply split. Apply F-1..F-3 so `caller_kind` is a named AD-24 amendment rather than silence-fill, so default-on retry cannot override `never-retry`/fencing/CAS, and so local AD-8 cannot be read as the product-session AD.
