---
name: reconcile-inputs
sitting: architecture-QMX-UI-BACKEND-2026-09-24
created: 2026-09-24
status: independent-review
scope: round-2 REVIEW.md + BACKEND-INTAKE-SUPPLEMENT.md + UI BACKEND-DEPENDENCIES.md vs backend-delta spine/maps/companions
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
not_law: [research/]
---

# Reconcile — load-bearing intake vs backend-delta spine

Independent document review. Does not implement. Does not amend the spine. Does not run Documentation Factory.

**How this lens scores.** A supplement contract group is **landed** only when a local AD, a named companion, and a `DEPENDENCY-MAP.md` row bind the required behavior (class, owner, durable record, wire/API, stories). Coverage that lives only in `research/` or in the UI candidate without a backend owner is **not** a landing. A named residual inside a landed group is **missed** (obligation), not a failed group.

**Headline.** All ten supplement contract groups landed as architecture law. Round-2 remaining R2 issuance and reload/cold-start wording landed and were reconciled into the UI candidate. Quiet requirements were honored. Five load-bearing obligations inside those groups did **not** land: authenticated-HTTP CORS OPTIONS vs AM-01; PackUiRequest read-back query; draft mutate/validate wire verbs; draft validation-binding record; CLI-proxy / ModelDeployment classification.

---

## Sources checked

| Input | Role |
| --- | --- |
| `workroom/qmx-ui-closure-round2-2026-09-24/REVIEW.md` | Remaining R2 High; sessionStorage wording; mailbox plan-anchor; backend inventory note |
| `workroom/qmx-ui-closure-round2-2026-09-24/BACKEND-INTAKE-SUPPLEMENT.md` | Ten contract groups + required sitting outputs |
| `architecture-QMX-UI-2026-09-23/BACKEND-DEPENDENCIES.md` | Short already-planned + proposed-amendment list |
| `architecture-QMX-UI-BACKEND-2026-09-24/ARCHITECTURE-SPINE.md` | Local AD-1..AD-16 |
| `architecture-QMX-UI-BACKEND-2026-09-24/DEPENDENCY-MAP.md` | Full inventory classification |
| `architecture-QMX-UI-BACKEND-2026-09-24/PARENT-AMENDMENT-MAP.md` | AM-01..AM-11 |
| Companions, `TRACE-MATRIX.md`, `CLOSURE-EVIDENCE.md`, `UI-CANDIDATE-CHANGELOG.md`, `START-HERE.md` | Bindings and honesty |
| Reconciled UI candidate files named in the changelog | R2 / recovery / 46.4 back-write |

`CLOSURE-EVIDENCE.md` claims mechanical spine lint and independent reviewers under `reviews/`. That directory was empty at this reconcile. Not a supplement contract miss. The claim is unsupported.

---

## Round-2 remaining conditions

| Condition | Score | Where | Residual |
| --- | --- | --- | --- |
| R2 — remembered Origin never issues `pairing_session_id` | **landed** | Backend AD-3, AD-5, `PAIRING-AND-ADMISSION.md`; UI `BOOTSTRAP-AND-AUTH.md` locked defaults / §5.3 / §5.5 / failure matrix / `qmb host pair` contract / tests; UI AD-19; `CLOSURE-MAP.md` | Traces unexecuted (honest). Candidate ≠ operator acceptance. |
| Reload vs cold start / cloned tab | **landed** | Backend AD-14; `PAIRING-AND-ADMISSION.md` §6; `MAILBOX-AND-DELIVERY.md` recovery; UI `CHAT-AND-HISTORY.md` T-CH-06; UI `TRACE-MATRIX.md` Home row | — |
| Mailbox plan anchor Epic 46 / Story 46.4 | **landed** | Backend AD-2, AD-7; `MAILBOX-AND-DELIVERY.md` owners table; `DEPENDENCY-MAP.md` §4; UI `BACKEND-DEPENDENCIES.md`; UI `CLOSURE-MAP.md` | “Epic 41 mailbox” label corrected. Do not regress. |
| Backend inventory not only the short API list | **landed as groups** | `DEPENDENCY-MAP.md` §1–§9 covers all ten supplement rows | See missed obligations below. |

Required R2 traces exist as architecture: T-BE-01 (negative Origin-only), T-BE-02 (fresh confirm), T-BE-03 (authenticated renew), T-BE-04 (revoked/expired). UI auto-approve rows are gone.

---

## Supplement contract groups

Legend: **landed** = AD + companion + map row bind the group; **missed** = supplement obligation with no factory-ingestible binding.

### 1. Pack-and-grant Epics 60–65 — **landed**

`DEPENDENCY-MAP.md` §1. Spine AD-2 / inherited Epic 60–65. No duplicate feature set.

| Need | Class | Binding |
| --- | --- | --- |
| `PluginManifest.copilot_profile` | already planned; adoption gap (0 inspect hits) | Story 60.1; **no** move into PackUiRequest (AD-10, AM non-amendment) |
| Authoring `app_instance_id` optional; `selected_refs.instance_id` | already planned; adoption gap | Story 60.2; envelope `instance_id` still required on invoke |
| `caller_kind` `user\|agent\|workflow` | already planned; adoption gap | Story 60.3; until present UI refuses pack invoke |
| JSON-lines / `failure_class` | already planned | Epic 61 |
| Host retry `none`/`read` | already planned | Epic 62 |
| Nested Mission JobHandle | already planned | Epic 63; needs Epic 57 |
| Instance `health()` / listing | already planned | Epic 64 |
| Thin kit proofs | already planned | Epic 65; not UI e2e |

PackUiRequest is additional beside Epic 60, not a rewrite. Story 60.1 is **not** held.

### 2. Browser admission and live transport — **landed** (one obligation missed)

`PAIRING-AND-ADMISSION.md`, AD-3/AD-4/AD-5/AD-14, `DEPENDENCY-MAP.md` §2, AM-01/AM-03/AM-11.

Landed: live CT-40 as Epic 41–42 adoption gap (bytes discarded at inspect); loopback vs recorded TLS; pairing HTTP `/pair/start|confirm` + authenticated `/pair/renew`; Bearer `pairing:<id>` + WS `qmx.ct40.v1` / `qmx.pair.<id>`; cookies refused; pairing table as journal projection; TTL registry row with **no number**; revoke; CORS exact Origin + `credentials:'omit'`; WS upgrade inspects offered list and echoes one protocol; credential-safe diagnostics (AM-11: pairing is not a CredentialRef; traces use key `pairing_session_id`, not `bearer`); R2 issuance.

**Missed — CORS OPTIONS on authenticated HTTP vs AM-01.** AM-01 / AD-5 allow unauthenticated HTTP **only** on `POST /pair/start`, `POST /pair/confirm`, and **their** `OPTIONS`. Browser CORS preflight for `POST /pair/renew`, authenticated GET snapshots, and `PUT /artifacts/stage` is unauthenticated OPTIONS on those paths. Pairing §5 names ACAO / Allow-Headers for authenticated HTTP but does not carve OPTIONS. A factory following AM-01 literally would refuse those preflights and the SPA could not PUT or renew. This is a named conflict, not an implementation detail.

### 3. QMB host verbs (start / status / stop / pair, not pairing-only) — **landed**

`HOST-LIFECYCLE.md`, AD-6, AM-10, `DEPENDENCY-MAP.md` §3.

| Verb | Bound |
| --- | --- |
| `qmb host start` | `QMA_DAEMON_ROOT` per-user; spawn `python -m qma.daemon` if lock free; already-running |
| `qmb host status` | lock, pid, bind, pending/bound origins (id presence only) |
| `qmb host stop` | **local** daemon only; remote/QMN continue |
| `qmb host pair <code>` | confirm that pending; page still POSTs `/pair/confirm` |
| revoke | `qmb host pair revoke --session\|--origin` (HOST) / `pair-revoke` (AD-6, AM-10) |

Stable root, `.daemon_writer`, stale-lock recovery, bind collision, stop-while-jobs, laptop-sleep non-promise, until-exists setup recipe: bound.

Internal naming is not unified (`pair-revoke` vs `qmb host pair revoke`). Both names exist; this is not a missing verb.

**Not a group miss:** Darwin `QMA_DAEMON_ROOT` is unnamed (Windows + Linux only). Recorded under installed-product residual.

### 4. Conversation / mailbox including Epic 46.4 — **landed**

`MAILBOX-AND-DELIVERY.md`, AD-7, AM-02/AM-08, `DEPENDENCY-MAP.md` §4.

Owners are explicit: `send_message` vocab = Epic 41.1 reuse (socket dispatch = adoption gap); `list_mailbox` name = Epic 41 addable; durable Envelope + delivery = **Epic 46 / Story 46.4**; journal/fold = Epic 42; `product_session_id` = AM-02 at accept, inherit on reply/question, refuse retarget; originating `(producer_id, wire_id)` + payload hash on the journal row; collision same-pair+same-hash returns prior, different hash refuses for journal lifetime; missing query = `query_unavailable` not empty chat; pending triple is client-local `sessionStorage`; recovery AD-14.

History retention is inherited journal-forever (QMA AD-6/AD-8 in spine inherited table). Rebuild is fold-by-field, not body parse. Compacted-delivery resync stays UI `CHAT-AND-HISTORY.md`.

`list_mailbox` as CT-40 HTTP GET snapshot matches the UI family. Not a miss.

### 5. Cancel — **landed**

`CANCEL-AND-HANDLES.md`, AD-8, AM-04/AM-09, `DEPENDENCY-MAP.md` §5.

`cancel_job` addable; fields `handle_id`, `logical_run_id`, `attempt_id`, `command_id`, `expected_state`; immutable `originating_psess` at admit; operator of that session only; observation is not authority; nested Epic 63 children store **their own** field at child admit; `queued`→`running` keeps the same `command_id`; terminal recorded no-op on `later_commands`; `unknown` not cancellable; replay same `command_id`; first durable terminal wins; not `stop_run`. In-memory `JobHandleStore` vs sqlite is an adoption gap of Epic 42/57.

### 6. Artifacts — **landed**

`ARTIFACTS-AND-TRANSFER.md`, AD-9/AD-15, AM-05/AM-06, `DEPENDENCY-MAP.md` §6.

Authenticated `PUT /artifacts/stage`; `Content-Length` required; completeness = daemon fp1 + byte count; interrupt deletes incomplete; no RFC 9110 §14.5 partial; `registry:artifact.stage_max_bytes` named, **no number** (explicit deferral); reuse `before_artifact_register`; `transfer_artifact` ticket; destination **pulls** as `machine`; daemon never dials out; dest verifies hash+count; failure leaves local-complete fp1; no silent local fallback. Transfer ticket is AM-03 projection `artifact_transfer_ticket`.

`initialize` capability name `stage_artifact` flags the PUT channel. It is not a JSON-RPC byte body.

### 7. PackUiRequest — **landed** (one obligation missed)

AD-10, `PACK-UI-AND-AUTHORING.md`, `DEPENDENCY-MAP.md` §1 last row. Schema reused from UI `VIEW-AND-PACK-CONTRACT.md`.

Landed: ingest at enable; versioned request DTO not a contribution point and not a grant; at most one document; unknown schema → ignore chrome, ops still enable; nav binds `view_ids`; invalid nav item dropped; `copilot_profile` stays Epic 60 sibling; 0/1/≥2 GrantRecords including `GRANT_AMBIGUOUS`; ActionContext host-minted immutable; durable pack metadata projection beside plugin-install row.

**Missed — host query / read-back after enable.** Supplement asked for ingestion **and** querying. UI already says the daemon records the request and the Svelte host later **loads** it when an instance is opened. This sitting names no query/snapshot verb (or an explicit reuse of an existing plugin/pack query) for that load. Factory ingesting only the backend map cannot tell how chrome rehydrates PackUiRequest after reconnect.

### 8. Drafts / CAS — **landed** (two obligations missed)

AD-11, AM-03/AM-07, `PACK-UI-AND-AUTHORING.md`, `DEPENDENCY-MAP.md` §7.

Landed: artifact-store bytes + `editor_draft_head` (`editor_draft_id`, head hash, owner principal, optional `psess:`); CAS `expected_revision`; stale typed conflict; two restored clients: second save refuses; unsaved buffer client-local; **not** QMA AD-22 RefinementProposal; first Run = publish into local authoring pack → enable (parent AD-30) → grant → select `instance_id` → `dispatchInvoke`; no second enable machine; distributable export later parent AD-18; draft Run refused. UI AUTHORING “staging” wording is correctly overridden (AM-07).

**Missed — mutate/publish wire verbs.** Map says only “mutate with `expected_revision`”. No addable command/query names for create/save/reload-head/publish. Supplement + REVIEW.md note 2 asked for saved-draft/CAS **APIs**.

**Missed — validation binding.** UI `AUTHORING-AND-ML.md` lists “Validate-named-hash; invalidate on byte change” as a daemon add; publish requires a currently valid validation of that hash. Supplement listed validation binding. This sitting has no validation-verdict record, owner, or invalidation rule.

### 9. Provider setup — **landed** (one obligation missed)

AD-12, `PROVIDER-AND-COMPAT.md`, `DEPENDENCY-MAP.md` §8.

Landed: broker exact-ref reuse; `_reader` uninjected = adoption gap not a new broker; allowlist stays `qma-core` code (`cred://models|inference|compute|sandbox|corpus|knowledge|telemetry/`); secrets never on wire/pairing/traces; v1 browser **selects refs only**; host write-to-OS-store **deferred** with revisit (“when v1 browser cannot complete first-run without a write path”); `update_configuration` / `get_provider_health` reuse Epic 41 seed; reconnect does not resubmit a secret.

**Missed — CLI-proxy / ModelDeployment classification.** Supplement: check CLI-proxy integration against already-planned owners. UI research seats the mentioned CLI proxy on the **model** plane (OpenCodex-shaped local proxy behind Deployment), not QMB and not the Credential Broker. This sitting never classifies that surface (reuse vs adoption gap vs defer). A factory can collapse “CLI proxy” into QMB or into broker writes.

### 10. Client / core / installed-product — **landed**

AD-13, `PROVIDER-AND-COMPAT.md`, `DEPENDENCY-MAP.md` §9, J-UI-13/14 traces T-BE-20/21.

Landed: additive same-major; `initialize` advertises `pairing`, `list_mailbox`, `cancel_job`, `caller_kind`, `stage_artifact`, `transfer_artifact`, `pack_ui_request`; missing cap → typed mismatch, shell usable for other surfaces; no silent downgrade; older clients ignore unknown fields; client bits ≠ journals; clean-machine = `QMA_DAEMON_ROOT` + `qmb host start` + pair + initialize; local vs recorded remote, never retarget; Tauri deferred (UI AD-12); no native-performance or build-success claim.

**Residual, not a group fail:** Darwin data-root path unnamed. Windows and Linux only in `HOST-LIFECYCLE.md`.

---

## Required sitting outputs (supplement)

| Output | Score |
| --- | --- |
| Per-item class reuse / already planned / adoption gap / proposed amendment | **landed** (`DEPENDENCY-MAP.md`) |
| Owning COMP + durable record | **landed** |
| Wire / API / schema effect | **partial** — drafts and PackUiRequest read-back unnamed (missed list) |
| AuthZ | **landed** |
| Compatibility / migration | **landed** (additive; hold list for 41.4 / 46.4 / Epic 57 record / not 60.1) |
| Dependency on existing planned stories | **landed**; no predicted epic count |
| Acceptance / failure traces | **landed** (`TRACE-MATRIX.md` T-BE-01..22) |
| Explicit deferral + revisit | **landed** where used (TTL number, partial PUT, Tauri, OS-store write helper) |
| Parent-amendment map | **landed** AM-01..AM-11; non-amendments explicit |
| Frontend / backend dependency map | **landed** as `DEPENDENCY-MAP.md` (UI vs COMP owners + Placement). Not a second file. |
| Inspect evidence at `34c148be`; planned ≠ implemented | **landed** (`START-HERE.md` honesty; each companion; `research/00`) |
| R2 + recovery reconciled into UI candidate + changelog | **landed** (`UI-CANDIDATE-CHANGELOG.md`; files edited as listed) |

Hold vs continue is named: Story 41.4 unauthenticated-bind sentence; Story 46.4 Envelope field list; Epic 57 handle **record** (states proceed); Epic 60.1 not held.

---

## Quiet requirements

| Requirement | Score | Evidence |
| --- | --- | --- |
| Preserve storyboard / Svelte | **honored** | AD-1; `START-HERE.md`; changelog did not edit `EXPERIENCE-AND-LAYOUT.md`, `DESIGN.md`, `COMPONENT-CONTRACTS.md`, `JOURNEYS.md` |
| No UX redesign | **honored** | AD-1 Prevents “a second UI-design session”; rail Home / Copilot / Library / Authoring preserved |
| Existing epics as planned, not implemented | **honored** | AD-2; inspect honesty tables; DEC-0286 restated |
| No Documentation Factory | **honored** | AD-1; `START-HERE.md`; `REVIEW-LAUNCH.txt`; `PARENT-AMENDMENT-MAP.md` §E. This sitting starts none of Factory / epic rewrite / factory control |

No application-branch claim was verified in git for this review. Sitting law forbids it.

---

## Conflicts / precision (not group failures)

| Id | Clash | Residual |
| --- | --- | --- |
| C1 | AM-01 unauthenticated OPTIONS only on `/pair/start\|confirm` vs browser CORS preflight for renew / GET / PUT | **Missed obligation** (browser admission) |
| C2 | AD-6 / AM-10 verb `pair-revoke` vs HOST/PAIRING `qmb host pair revoke` | Same door, two spellings. Unify before epics. |
| C3 | UI AUTHORING “staging” vs AM-07 “not AD-22 staging” | Backend wins; drafts use artifact store + `editor_draft_head`. Do not re-open AD-22. |
| C4 | `CLOSURE-EVIDENCE.md` “reviews/” lint | Unsupported at this reconcile. |

---

## What did not land

These are the supplement obligations with no factory-ingestible binding. Groups themselves landed.

1. **CORS OPTIONS for authenticated HTTP** (`/pair/renew`, GET snapshots, `PUT /artifacts/stage`) vs AM-01 carve-out limited to `/pair/start` and `/pair/confirm`.
2. **PackUiRequest load/query** after enable / reconnect (ingest landed; read-back unnamed).
3. **Draft save / reload-head / publish wire verbs** (CAS semantics landed; APIs unnamed).
4. **Draft validation-binding** (named-hash verdict, invalidate on byte change, publish requires currently valid validation).
5. **CLI-proxy / ModelDeployment** classification against already-planned owners (broker + OS-store write deferral landed; model-plane proxy not classified).

Not missed: Epics 60–65 reuse; R2 issuance; start/status/stop/pair; Epic 46.4 mailbox ownership; cancel `originating_psess`; PUT + pull transfer; PackUiRequest ingest and `GRANT_AMBIGUOUS`; draft head + CAS + first Run; secrets off the wire; initialize capabilities; quiet Svelte/storyboard / no UX redesign / planned≠implemented / no Documentation Factory.

---

## Limits

- Inspect SHA still `34c148be`. No live daemon. Traces unexecuted.
- Candidate ≠ operator acceptance.
- This file is not joint-review closure and not a spine amendment.
