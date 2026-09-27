---
name: J1–J5 parent-consistency review
sitting: architecture-QMX-UI-BACKEND-2026-09-24
lens: parent / kit / QMA / UI-candidate inherited law
against: architecture-QMX-2026-09-18; architecture-QMX-2026-09-23 (kit); architecture-QMA-2026-08-28 (especially conventions _ref law and ten named exceptions); architecture-QMX-UI-2026-09-23 AD-18/19/21/22/23; PARENT-AMENDMENT-MAP.md AM-01..AM-16
date: 2026-09-24
reviewer: Grok 4.6 independent parent-consistency (J1–J5 amendment)
status: return-for-amendment
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
tests: unexecuted
---

# Reviewer gate — LENS: J1–J5 parent / kit / QMA consistency

**Subject:** live J1–J5 amendment of `architecture-QMX-UI-BACKEND-2026-09-24` (`ARCHITECTURE-SPINE.md` local AD-1..AD-17, `PARENT-AMENDMENT-MAP.md` AM-01..AM-16, `CLOSURE-J1-J5.md`, companions) plus reconciled UI candidate `architecture-QMX-UI-2026-09-23` AD-18 / AD-19 / AD-21 / AD-22 / AD-23.
**Question this lens answers:** does the J1–J5 amendment silently rewrite inherited law? Is every conflict a named row in `PARENT-AMENDMENT-MAP.md` (AM-01..AM-16)? Any exception-list widening?
**Especially checked:** Epic 60 `copilot_profile` stays sibling; credential-broker allowlist not widened; QMA AD-24 authenticate-before-protocol with AM-01 as the wire carve-out only; Epic 46.4 mailbox delivery owner; JobHandle states unchanged; parent AD-30 enable is compile identity; QMA conventions `_ref` law and the ten named exceptions.
**Out of scope:** implementation; Documentation Factory; epic rewrite; editing historical first-pass files under `reviews/`.

**Verdict: RETURN-FOR-AMENDMENT.**

The J1–J5 pass names the large previously missing rows (AM-12..AM-16) and does **not** move `PluginManifest.copilot_profile`, widen the broker allowlist, change JobHandle states, relabel mailbox delivery as Epic 41, treat publish as compile identity, or add names to the ten `_ref` exceptions. Those holds are real.

Two inherited closed lists still admit two factory products from the live J1–J5 text:

1. **J1 mints a durable operator-principal journal projection that AM-03 does not name.** Spine conventions list “operator principal” beside pairing / mailbox / draft head / transfer tickets. Story 42.2 / parent AD-16 / QMA AD-6 still refuse a store outside the closed list. AM-15 names the host-control **channel**, not the sqlite/fold add.
2. **Local AD-7 is stronger than named AM-02 and silently collides with QMA AD-20.** UI `CHAT-AND-HISTORY.md` already preserves Quant delivery: daemon-originated rows that are not in a product conversation **omit** `product_session_ref`. Backend AD-7 says **each accepted Envelope persists** the field and that `send_message` / `list_mailbox` admit only when the connection’s **operator** principal equals the session principal. That can make seed `send_message` operator-only and required-psess for the agent bus. AM-02 only names an additive Envelope field.

Until those two are named (or the local sentences are narrowed to the UI chat path / existing AM-03 projections), the map’s opening claim (“nothing silently overrides”) is still false for the J1–J5 amendment.

---

## Method

Read live law only (historical `reviews/review-parent-consistency.md` is prior evidence, not current text):

- Parents: QMA 08-28 AD-5, AD-6, AD-8, AD-15, AD-17, AD-20, AD-21, AD-22, AD-24, AD-26, AD-27 and Conventions `_ref` whitelist; parent 09-18 AD-16, AD-21, AD-24, AD-26, AD-30; kit 09-23 AD-1 / AD-2; UI 09-23 AD-18/19/21/22/23 and the reconciled companions (`CHAT-AND-HISTORY.md`, `BOOTSTRAP-AND-AUTH.md`, `AUTHORING-AND-ML.md`, `LIBRARY-AND-ATTACHMENTS.md`, `VIEW-AND-PACK-CONTRACT.md`).
- Child: backend AD-1..AD-17, AM-01..AM-16, `HOST-LIFECYCLE.md`, `PAIRING-AND-ADMISSION.md`, `MAILBOX-AND-DELIVERY.md`, `CANCEL-AND-HANDLES.md`, `ARTIFACTS-AND-TRANSFER.md`, `PACK-UI-AND-AUTHORING.md`, `PROVIDER-AND-COMPAT.md`, `DEPENDENCY-MAP.md`, `CLOSURE-J1-J5.md`.

A local rule that weakens a parent without an AM-id is a silent override. A named AM whose proposed text is narrower than the local AD is also a silent override (the map does not cover the extra law).

---

## Numbering collisions (unchanged caution)

Local backend-delta `AD-n` still collides with QMA / parent / UI ids if a factory sentence drops the prefix. Worst pairs for this amendment: local **AD-5** (pairing carve-out) vs **QMA AD-5** (unauthenticated bind is hard startup refusal); local **AD-16** (no sixth COMP) vs **parent AD-16** (complete v1 sqlite additions); local **AD-8** (cancel field) vs **parent AD-8** (`psess:`). Keep `QMA AD-n` / `parent AD-n` / `UI AD-n` / `local AD-n` on every factory sentence.

---

## Especially checked (required holds)

### 1. Epic 60 `copilot_profile` stays sibling — HOLD

**Parents:** kit AD-1 / Story 60.1: optional `copilot_profile` is a request blob on the pack, not a contribution point and not a grant.

**Child:** local AD-10; `PACK-UI-AND-AUTHORING.md`; map section B; UI AD-15; `VIEW-AND-PACK-CONTRACT.md` §1–§2. Host ingests at most one `qmx.ui.pack_ui_request.v1` at enable. **No parent amendment to nest `copilot_profile`.** T-BE-16 forbids the nest. Epic 60.1 is **do not hold**.

**Ruling:** J1–J5 did not move the field. PackUiRequest remains additional chrome request.

### 2. Credential-broker allowlist not widened — HOLD

**Parents:** QMA AD-24: allowlist is `qma-core` code (models/inference/compute/sandbox/corpus/knowledge/telemetry). Never settings, never a plugin, never a Mission. Venue/broker/exchange stay out of namespace.

**Child:** local AD-12; AM-15 “Broker allowlist **not** widened”; map section C `no cred://operator/`; `PROVIDER-AND-COMPAT.md`; `HOST-LIFECYCLE.md` negatives (forged `cred://models/…` / `cred://telemetry/…` as login refuse). Browser-paired sessions carry `principal_class=operator` + `pairing_record_id` and **do not** populate `credential_ref` (AM-11). Machine clients still present `credential_ref` (Story 41.4).

**Ruling:** J1 did not mint `cred://operator/` or a pairing family. Trust root is OS user + `host_control` file, named as **not** a provider ref.

### 3. QMA AD-24 authenticate before protocol; AM-01 carve-out only (wire) — HOLD on the wire; host-control is the separate named AM-15

**Parents:** QMA AD-5 / AD-15 / AD-24 / Story 41.4: every client authenticates with a broker-resolved credential before protocol bytes; unauthenticated bind is a hard startup refusal; daemon never dials in; daemon listener is the single inbound port.

**Child:**

| Path | Auth | Named? |
| --- | --- | --- |
| `POST /pair/start`, `POST /pair/confirm` | unauthenticated HTTP | AM-01 |
| CORS `OPTIONS` on daemon HTTP routes that declare CORS | unauthenticated; never issues a session, never upgrades WS, never returns bytes | AM-01 (widened vs first-pass POST-only OPTIONS) |
| `POST /pair/renew` | authenticated Bearer proof | AM-13 |
| JSON-RPC WS, snapshot GET, PUT `/artifacts/stage`, GET `/artifacts/<fp1>` | authenticated | AM-05 / AM-13; not a fourth invoke family |
| Local host-control under `QMA_DAEMON_ROOT` | token-gated, **not** port-8765, **not** CT-40 | AM-15 |

**Ruling:** the wire unauthenticated set is the AM-01 list. Renew is not a second unauth POST. Host-control is not smuggled into AM-01; it is AM-15. Residual: AM-15’s inherited-contract cell cites Story 41.4 / QMA AD-24 and does **not** cite QMA AD-5’s “single inbound port” sentence (F-4). The row exists; the ID is incomplete.

### 4. Epic 46.4 mailbox delivery owner — HOLD

**Parents:** QMA AD-20 Envelope members; MessageKind / DeliveryState closed; mailbox is a projection over `message.*`; delivery owner is Story 46.4, not Epic 41.

**Child:** AM-02 additive `product_session_ref`, excluded from Envelope fp1; Story 46.4 remains delivery owner; AM-08 addable `list_mailbox`; AM-12 journal-lifetime collision for `send_message` only; map section C MessageKind / DeliveryState unchanged; `MAILBOX-AND-DELIVERY.md` owner table splits Epic 41.1 vocab / 46.4 delivery / Epic 42 fold.

**Ruling:** delivery owner is not relabelled “Epic 41 mailbox.” Closed kind/state sets are not opened. The **field add** is named. The **admit rule** on `send_message` is the hole (F-2).

### 5. JobHandle states unchanged — HOLD

**Parents:** QMA AD-17 / parent AD-26 / Story 57.3: `queued` \| `running` \| `done` \| `failed` \| `cancelled` \| `aborted` \| `unknown`. Never `succeeded`. `awaiting_approval` is a Mission/Task gate. First durable terminal wins.

**Child:** AM-04 optional immutable `originating_product_session_ref` at UI admit; omitted on headless; `handle_id` **is** `job_id`; states unchanged; `unknown` not cancellable; Story 36.5 remains the headless abort door; `stop_run` stays distinct. UI AD-23 matches. Map section C repeats the closed states.

**Ruling:** additive record field, not a seventh state. Cancel-of-unknown still upholds L35 / QMA AD-17.

### 6. Parent AD-30 enable is compile identity — HOLD

**Parents:** parent AD-4 / AD-30: compile identity is `(qualified_id, version)` at enable; enabled bytes immutable; install ≠ enable ≠ grant.

**Child:** J4 `publish_editor_draft` authorizes, CAS-checks, revalidates immutable fp1, writes the local authoring-pack contribution. **Then** enable (parent AD-30) is compile identity. T-BE-18: “Treat publish as compile identity → forbidden.” UI `AUTHORING-AND-ML.md` locked defaults and transition table: in-place overwrite of an enabled version is forbidden; enable mints `(qualified_id, version)`.

**Ruling:** J4 did not mint a second enable machine. Publish is not compile. Residual: backend `PACK-UI-AND-AUTHORING.md` does not restated parent AD-4 immutability as loudly as the UI companion; first-Run path is still publish-then-enable.

### 7. QMA `_ref` law and ten named exceptions — HOLD (not widened)

**Parents:** QMA Conventions: a record’s **own** identity is `id` or `_id`; every pointer at a record owned by **another** store is `_ref`, with exactly ten exceptions: `correlation_id`, `causation_id`, `producer_id`, `attempt_of`, `approval_route`, `scope_path`, `from`, `to`, `authored_by`, `proposer`.

**Child:** AM-14 uses `product_session_ref` and `originating_product_session_ref`. Explicitly **do not** add `product_session_id` / `originating_psess` to the exception list. ProductSession **own** identity stays `product_session_id` (parent AD-8). UI AD-18 / CHAT identities match. Pairing own identity is `pairing_record_id`. Draft own identity is `editor_draft_id`. Ticket own identity is `ticket_id`.

**Ruling:** J1–J5 closed the joint-review “Durable reference naming” item by renaming, not by punching an 11th exception. Live UI law files no longer use Envelope `product_session_id` or `originating_psess` as pointers.

---

## AM-01..AM-16 tagging audit (J1–J5 live map)

| ID | Inherited cell | Covers the live local rule? | Silent override? |
| --- | --- | --- | --- |
| AM-01 | QMA AD-5, AD-15, AD-24; Story 41.4; credential_ref before protocol | Yes for unauth `POST /pair/start` \| `POST /pair/confirm` \| CORS OPTIONS. Renew is authenticated (AM-13). | No on the wire list. |
| AM-02 | QMA AD-20; Story 46.4 Envelope members | Yes for additive `product_session_ref` excluded from fp1. **No** for AD-7’s “each accepted Envelope persists” + operator-principal admit. | **Yes if AD-7 is shipped as written** (F-2). |
| AM-03 | QMA AD-6 / AD-8 / FR-Q23 / Story 42.2; parent AD-16 | Names `pairing_pending`, `pairing_session`, `editor_draft_head`, `artifact_transfer_ticket`. Fold text is a sketch, not the parent four-part contract. **Omits operator principal.** | **Yes for the J1 principal fold** (F-1). Fold-contract quality is F-3. |
| AM-04 | QMA AD-17; parent AD-26; Story 57.3 | Optional `originating_product_session_ref`; states closed; `handle_id` is `job_id`. | No. |
| AM-05 | QMA AD-5 / UI AD-12 three families | PUT `/artifacts/stage` is a byte channel. | No. |
| AM-06 | Story 41.4 daemon never dials in | Dest pulls recorded TLS; `source_unreachable` on loopback; dest-authored `transfer_complete`. | No. Dest daemon dials **out**; source remains the inbound listener. |
| AM-07 | QMA AD-22 one type | Non-amendment of AD-22; drafts use AM-03. Section C already lists this. | Not an AD-22 override. Still a noisy AM-id (F-5). |
| AM-08 | Epic 41.1 addable queries | `list_mailbox`. | No. |
| AM-09 | Epic 41.1 addable commands | `cancel_job`, `transfer_artifact`, `transfer_complete`, `save_editor_draft`, `publish_editor_draft`. No JSON-RPC `stage_artifact`. | No. Pair/revoke/TTL stay host-control. |
| AM-10 | parent AD-21 `COMMAND_GROUPS`; QMA AD-24 human-gate list | `qmb host` group; operator-only via `host_control`, not CT-40. | Named channel change, not a new CLI. |
| AM-11 | `authenticate_before_protocol` / secret-surface keys | Browser session: operator + `pairing_record_id`, **no** `credential_ref`; journal `proof_fp1` only; value-class redaction. | No. Implements J2 without widening the broker. |
| AM-12 | Story 41.3 `registry:wire.dedup_window` | `send_message` only; journal lifetime. Other commands keep 41.3. | Named. Closes first-pass F-3. |
| AM-13 | QMA AD-5 three families; AM-05 PUT-only | Authenticated `POST /pair/renew`; authenticated `GET /artifacts/<fp1>` + ticket. | Named. Closes first-pass F-1 remainder. |
| AM-14 | QMA `_ref` ten exceptions | Pointers use `_ref`; own ids stay `_id`; exception list unchanged. | Named. Closes joint-review naming item. |
| AM-15 | Story 41.4 / QMA AD-24 never unauthenticated bind; human-gate | Host-control outside the wire; first operator + TTL + pair confirm; allowlist not widened. | Channel is named. **Operator-principal projection is not** (F-1). QMA AD-5 single-port citation missing (F-4). |
| AM-16 | Epic 41.1 addable queries | `get_pack_ui_request` by `instance_id` + `availability_revision`. | Query is named. Durable home of the ingested DTO is not (F-5). |

The Inherited table still does **not** copy AM text in as already-true parent law. That half of the tagging rule holds.

---

## J1–J5 vs parents (per finding)

### J1 — First operator / host-control

**Required by joint review:** name the QMA / Story 41.4 amendment; no dummy provider login; QMB remains the door; daemon remains sole writer.

**Landed:** AM-15 + AM-10 + local AD-17 / AD-6. OS user of `QMA_DAEMON_ROOT` + daemon-minted `host_control` (owner-only ACL). Empty start mints operator principal (journal) + token; pairing issue refuses until `qmb host configure pairing-ttl`. QMB presents the token; forged `credential_ref` is not proof. Recovery: same OS user, same root; `rotate-control` replaces the token, not the principal. Remote: SSH there and run `qmb host` there.

**Parent conflicts named:** unauthenticated-bind / human-gate channel (AM-15); QMB `host` group (AM-10); broker not widened (AM-15 / AD-12).

**Unnamed:** the **durable operator-principal projection** that pairing HTTP requires to already exist (`PAIRING` start precondition; spine conventions “operator principal are journal projections”). That is a Story 42.2 / parent AD-16 / QMA AD-6 add. AM-03’s four names do not include it. `host_control` as a file under the root is named in AM-15 and is analogous to `.daemon_writer` (not a 42.2 store). The principal **row** is not analogous.

### J2 — Pairing proof vs record

**Landed:** `pairing_proof` bearer vs `pairing_record_id` row vs `proof_fp1` at rest (AM-11). Confirm once / `already_issued` / lost confirm → re-pair / renew rotates and closes old WS / expiry closes WS / origin revoke is a cutoff. Cookies and `localStorage` still refused. UI `BOOTSTRAP-AND-AUTH.md` and UI AD-19 match.

**Parent:** AM-01 + AM-11 + AM-03 pairing projections. R2 Origin-only issuance remains closed (local AD-3). Not a silent rewrite of Story 41.4 machine `credential_ref`.

### J3 — Daemon `editor_draft_id` issuer

**Landed:** daemon sole durable issuer; first `save_editor_draft` omits the id; `client_draft_correlation` coalesces lost first-save; later saves CAS `expected_revision`. AM-03 `editor_draft_head`; AM-09 `save_editor_draft`. Own identity `_id` suffix obeys `_ref` law. QMA “id minted by its producer” is upheld (daemon produces the record).

**Parent:** not a QMA identity-law rewrite. Drafts stay out of AD-22 (AM-07 / section C).

### J4 — `publish_editor_draft` then AD-30 enable

**Landed:** addable command (AM-09); ownership + CAS + revalidate immutable fp1; write local authoring-pack contribution; enable remains compile identity. UI AD-21 / `AUTHORING-AND-ML.md` forbid in-place overwrite of an enabled `(qualified_id, version)`.

**Parent:** AD-30 / AD-4 hold. Not a second enable machine. Not AD-22 apply.

### J5 — Reachable transfer

**Landed:** AM-05 PUT; AM-06 pull + `source_unreachable`; AM-09 `transfer_artifact` / `transfer_complete`; AM-13 GET `/artifacts/<fp1>` with ticket + machine `credential_ref` audience. Dest daemon sole writer of dest store; source records the ack. Invoke refuses until ticket `complete`. No silent loopback expose. No local-invoke fallback. UI AD-22 matches.

**Parent:** Story 41.4 “daemon never dials in” is not inverted (dest dials out to recorded TLS source). Artifact store remains the independent store; ticket is the AM-03 projection.

### Small reconciliations

| Item | Named? | Parent risk |
| --- | --- | --- |
| Shell ≠ provider readiness | local AD-12 / PROVIDER; not a parent conflict | None. |
| `get_pack_ui_request` | AM-16 | Query named. Durable record home unnamed (F-5). |
| Mailbox principal equality | local AD-7 / MAILBOX; **no AM** | F-2. Joint review called this a narrow UI-chat clarification. Backend AD-7 wrote it as seed-command law. |
| Cancel optional field + exact fences | AM-04 | Hold. |
| `_ref` naming | AM-14 | Hold. |

---

## UI candidate AD-18 / 19 / 21 / 22 / 23

Reconciled in place for J1–J5. They do not rewrite parent 09-18 / QMA law on their own if backend AD-7 is narrowed:

| UI AD | Live rule | Parent hold | Drift vs backend |
| --- | --- | --- | --- |
| AD-18 | `dispatchChat` → `send_message`; `product_session_ref`; principal equality; CHAT §3 Quant rows **omit** the field | Mailbox kinds/states; Epic 46.4 | **UI is the parent-safer text.** Backend AD-7 dropped the omit sentence. |
| AD-19 | QMB host-control; unauth `/pair/start` + `/pair/confirm`; `pairing_proof`; Origin never issues | AM-01 / AM-15 | UI AD-19 unauth list omits CORS OPTIONS that AM-01 names. Sibling tightness, not a parent rewrite. |
| AD-21 | Daemon `editor_draft_id`; `publish_editor_draft`; enable = compile | parent AD-30 / AD-4 | Matches J3/J4. |
| AD-22 | PUT then reachable TLS transfer; dest `transfer_complete` | AM-05/06/09/13 | Matches J5. |
| AD-23 | `originating_product_session_ref` optional; exact handle/run/attempt; not `stop_run` | AM-04; JobHandle states | Matches. |

---

## Findings

### High

#### F-1 — J1 operator-principal fold is not on AM-03 (reopens Story 42.2 / parent AD-16)

**Where:** local AD-17; spine Consistency Conventions “operator principal are journal projections”; `HOST-LIFECYCLE.md` “mint operator principal (journal)”; `PAIRING-AND-ADMISSION.md` start precondition “operator principal exists”; AM-03; AM-15.

**Parents:** QMA AD-6 / AD-8: a store not on the closed list may not be created; a new fold is a spine amendment and must declare its fold contract (stream, ordering key `journal_seq`, knowledge-time bound, equal-instant disposition). Story 42.2 / FR-Q23: declaration validator **refuses a store outside that list**. Parent 09-18 AD-16: v1 daemon additions are a **complete list**; no other new sqlite.

**What:** AM-03 names four projections: `pairing_pending`, `pairing_session`, `editor_draft_head`, `artifact_transfer_ticket`. Pairing rows may **carry** an operator-principal field, but first operator is minted on **empty start**, before any pairing row exists. Three conforming units:

- Unit A adds a fifth projection / definition-store member (`host_operator` / `operator_principal`) and amends Story 42.2 + parent AD-16.
- Unit B stuffs the principal only onto `pairing_session` and cannot satisfy `/pair/start` on a clean install that has not paired.
- Unit C uses an AD-26 registry string and skips 42.2.

AM-15 names the **channel** (outside the wire, allowlist not widened). It does not extend the closed projection list. That is the same class of hole the first parent review returned on, now for a J1-introduced name.

**Action:** apply. Either (1) add the operator-principal fold to AM-03 (inherited cell already has Story 42.2 / parent AD-16) with a real four-part fold contract, or (2) bind it as a field of an **existing** named projection that exists before pairing (and show the start-precondition trace). Do not leave “journal projection” in the conventions table without an AM-03 name.

#### F-2 — Local AD-7 exceeds AM-02 and can silently rewrite QMA AD-20 / AD-24 send authority

**Where:** backend AD-7 Rule; `MAILBOX-AND-DELIVERY.md` Admission; UI `CHAT-AND-HISTORY.md` §3 (omit-field sentence); AM-02.

**Parents:** QMA AD-20: Quant-owned mailboxes; Envelope `from`/`to` are ActorId (named `_ref` exceptions); agent bus `send_message` is not an operator-only human-gate command. QMA AD-24: principal class `operator` \| `machine`; machine workers send non-gate commands. QMA AD-5 compatibility: additive-only within a major. AM-02 proposed text: **additive** `product_session_ref`; Story 46.4 remains delivery owner.

**What:** UI CHAT is the parent-preserving split: copy `product_session_ref` from an admitted UI `send_message` payload; Quant `from`/`to` stay bus addressing; **“Daemon-originated mailbox rows that are not in a product conversation omit the field; Quant delivery is unchanged.”**

Backend AD-7 says **each accepted Envelope persists** `product_session_ref` and that `send_message` **and** `list_mailbox` admit only when the connection’s **operator** principal equals that session’s principal. Joint review asked only for the same principal check on UI send as on history reads.

Two units:

- Unit A implements UI CHAT: field optional; machine/agent Envelopes without a product conversation omit it; operator-principal check runs only when `product_session_ref` is present.
- Unit B implements backend AD-7 letter: every Envelope accept requires the field; seed `send_message` is operator-only; Quant/machine bus dies or is forced through a `psess:`.

AM-02 does not name that admit rule. Map sentence “every conflict is named here” fails.

**Action:** apply. Narrow local AD-7 (and MAILBOX Admission) to the UI CHAT split, **or** add an AM row: `product_session_ref` required on operator chat path; omitted on Quant/machine rows with no product conversation; `send_message` remains legal for `machine` when the field is absent. Do not convert seed `send_message` into an AD-24 human-gate command.

### Medium

#### F-3 — AM-03 still does not declare parent-shaped fold contracts

**Where:** AM-03 proposed text “Each declares a fold contract (live unrevoked rows / head pointer / open tickets).”

**Parents:** QMA AD-6 / Conventions: every fold declares stream, ordering key, knowledge-time bound, equal-instant disposition. v1 folds take `journal_seq`, `as_of` over `recorded_at`, equal instants by ascending `journal_seq`.

**What:** the sketch is not that contract. Two units can both “obey AM-03” with different streams, clocks, and equal-instant rules. First-pass F-2 asked for the four-part declaration; J1–J5 did not land it.

**Action:** apply. For each AM-03 name (and F-1’s principal fold if added): stream `noun.verb`, ordering `journal_seq`, knowledge-time `as_of`/`recorded_at`, equal-instant ascending `journal_seq`. Migrations remain QMA AD-27 five-step.

#### F-4 — AM-15 inherited cell omits QMA AD-5 single inbound port

**Where:** AM-15; local AD-15 “separate loopback channel”; local AD-17; QMA AD-5 “the daemon’s own listener is the single inbound port.”

**What:** host-control as a second loopback channel **is** the named AM-15 amendment. The inherited-contract cell lists Story 41.4 / QMA AD-24 and not QMA AD-5 / AD-15 listener sentences. A 41.4-only reader can treat a second listen socket as already-legal.

**Action:** apply if cheap. AM-15 inherited += QMA AD-5 single-inbound-port / AD-15 “daemon listener is never unauthenticated.” Keep the path token-gated and off port 8765.

### Low

#### F-5 — PackUiRequest durable home; AM-07 still wearing an AM-id; `stage_artifact` capability name

- `DEPENDENCY-MAP.md` §1 “pack metadata projection” is **not** an AM-03 name. UI `VIEW-AND-PACK-CONTRACT.md` §3 records the request on the enable path. Bind it as a field on the existing plugin-install / instance row (parent AD-16 item 3) in AM-16, or add it to AM-03. Do not let a fifth sqlite name appear at implementation.
- AM-07 remains in section A as “Non-amendment of AD-22.” Section C already says AD-22 stays one type. Demote AM-07 to C (first-pass F-5). Harmless to AD-22, noisy for the factory.
- `initialize` still advertises `stage_artifact` (`PROVIDER-AND-COMPAT.md`, local AD-13) while ARTIFACTS forbids JSON-RPC `stage_artifact`. Name the capability as “PUT `/artifacts/stage` supported.” Not a parent weaken until someone mints the verb.

`DEPENDENCY-MAP.md` §2 `/pair/renew` and §4 “Wire pair + payload hash” still omit AM-13 / AM-12 in those rows. Hygiene; the map section A has the IDs.

UI AD-19 unauth bootstrap sentence still omits OPTIONS. Backend AM-01 has OPTIONS. Align UI AD-19 if touching that file anyway.

---

## Non-conflicts (do not treat as silent overrides)

- **JobHandle states** `queued` / `running` / `done` / `failed` / `cancelled` / `aborted` / `unknown`. AM-04; UI AD-23; `unknown` not cancellable.
- **`PluginManifest.copilot_profile`:** Epic 60 Story 60.1 sibling; AD-10 forbids nesting; UI AD-15.
- **Broker allowlist prefixes unchanged.** No `cred://operator/`. Allowlist still code. J1 negatives refuse forged provider refs as login.
- **Envelope `instance_id` required on invoke.** Local AD-16; chat still does not require an instance (UI AD-18).
- **No sixth COMP / no new CT / no `qma-cli` / no COMP-UI / no `ui_view` point.**
- **QMB remains the only operator CLI.** `host` is a new **group** (AM-10), not a new COMP.
- **Story 41.4 dial-out.** AM-06 dest pull; daemon never dials in.
- **Story 46.4 delivery owner.** AM-02 field add; Epic 41 owns query name only (AM-08).
- **MessageKind / DeliveryState closed sets.**
- **Cookies / `localStorage` refused** for pairing proof; `sessionStorage` is tab-local and is not operator identity (AD-14).
- **Parent AD-30 enable / compile-at-enable.** J4 publish then enable; T-BE-18 forbids treating publish as compile.
- **QMA AD-22 one RefinementProposal type.** Drafts are artifact bytes + `editor_draft_head`.
- **AM-01 wire carve-out.** Unauth HTTP is start / confirm / CORS OPTIONS only. Renew authenticated (AM-13). Host-control is AM-15, not a third unauth 8765 path.
- **AM-12** journal-lifetime mailbox collision is named; other commands keep Story 41.3.
- **AM-14** does not widen the ten `_ref` exceptions.
- **Reconnect does not auto-resend.** Parent AD-29; local AD-14.
- **Widgets never own invoke.** Kit AD-2; UI AD-8.

---

## What this lens will not bless until F-1 and F-2 land

- AM-03 as a complete closed-store amendment for **J1**.
- AM-02 as a complete QMA AD-20 amendment for mailbox admit.
- The map sentence “every conflict with inherited contracts is named here.”

JobHandle state vocabulary, `copilot_profile` placement, broker allowlist, parent AD-30 compile-at-enable, Epic 46.4 delivery owner, and the ten `_ref` exceptions are already blessable.

---

## Reviewer action for the sitting

Return the amendment map (and local AD-7 / AD-17 cells) with:

1. AM-03 += the J1 operator-principal fold (or an explicit bind onto an existing pre-pairing projection) plus parent-shaped fold contracts for every named projection.
2. Local AD-7 / MAILBOX Admission aligned with UI CHAT Quant-omit, **or** a new AM-id that scopes `product_session_ref` + operator-principal checks to the UI chat path and leaves machine/Quant `send_message` legal.
3. Cheap: AM-15 inherited += QMA AD-5 single inbound port; AM-16 bind PackUiRequest onto plugin-install/instance; demote AM-07 to section C; `stage_artifact` capability = PUT.

Do not implement. Do not run Documentation Factory. Do not rewrite Epic 60.1. Do not widen the `_ref` exception list. Do not widen the broker allowlist.
