---
name: Dependency map against existing planned stories
sitting: architecture-QMX-UI-BACKEND-2026-09-24
status: candidate — not an epic backlog
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
---

# Dependency map

Full supplement inventory (`BACKEND-INTAKE-SUPPLEMENT.md`), not only the short UI `BACKEND-DEPENDENCIES.md` list. Classes: **reuse** / **already planned** / **adoption gap** / **proposed amendment**.

Inspect evidence is at `34c148be`. Planned stories are obligations, not delivery.

## How to read a row

| Column | Meaning |
| --- | --- |
| Class | reuse existing types/verbs; already planned by a named epic; adoption gap (planned, not wired at inspect); proposed amendment (new name or inherited conflict) |
| Owner | COMP that mutates the durable record |
| Wire/API | schema or verb effect |
| Stories | existing planned work to extend or hold — **not** a new epic number |

## 1. Pack-and-grant Epics 60–65 (do not duplicate)

| Need | Class | Owner | Durable record | Wire/API | AuthZ | Compat | Failure/recovery | Placement | Stories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Optional `PluginManifest.copilot_profile` | already planned; **adoption gap** (0 hits in inspect Python) | COMP-QMA-CORE | manifest field; not a grant | none new beyond enable payload | enable is not grant | additive optional | omit = valid headless | local enable | Epic 60 Story 60.1 |
| Authoring `app_instance_id` optional; `selected_refs.instance_id` | already planned; adoption gap | COMP-QMA-DAEMON + WIRE | `product_session` row | envelope still requires `instance_id` on invoke | GrantRecords of that instance | additive kind | zero/many refs → `INVALID_INPUT` | n/a | Epic 60 Story 60.2 |
| `caller_kind` `user\|agent\|workflow` | already planned; adoption gap | COMP-QMA-CORE + WIRE | envelope field | additive format mint | no `widget` | until present UI refuses pack invoke | typed `caller_kind_unsupported` | n/a | Epic 60 Story 60.3 |
| Daemon JSON-lines / `failure_class` | already planned | COMP-QMA-DAEMON | telemetry store (not evidence) | log lines | n/a | additive | missing logs ≠ missing journals | local daemon | Epic 61 |
| Host retry `none`/`read` | already planned | COMP-QMA-DAEMON | invocation journal | no new command | must not loosen parent AD-24 | registry retry ceiling later | never retry unknown-blocked / external-egress blind | n/a | Epic 62 |
| Nested Mission JobHandle | already planned | COMP-QMA-DAEMON | task_graph_state + child handle | invoke `start` of callee | nested grants do not union | additive occupancy | crash of A does not splice B | n/a | Epic 63; needs Epic 57 |
| Instance `health()` / listing axes | already planned | COMP-QMA-DAEMON | listing overlay + instance row | queries | observation only | additive | unhealthy ≠ unauthorized | n/a | Epic 64 |
| Thin kit proofs | already planned | tests | fixtures | n/a | n/a | not UI e2e | n/a | n/a | Epic 65 |
| PackUiRequest ingest / nav `view_ids` / `GRANT_AMBIGUOUS` | **proposed amendment** beside Epic 60 (do not nest copilot_profile) | COMP-QMA-DAEMON ingest at enable; WIRE DTO | field on existing plugin-install / instance row (parent AD-16 item 3) | request document `qmx.ui.pack_ui_request.v1`; read-back `get_pack_ui_request` by `instance_id`+`availability_revision` | not a grant | unknown schema → ignore chrome, ops still enable | invalid nav item dropped | enable on that daemon | **new stories after Epic 60**; Story 60.1 unchanged |

## 2. Browser admission and live transport

| Need | Class | Owner | Durable record | Wire/API | AuthZ | Compat | Failure/recovery | Placement | Stories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Live JSON-RPC WS + HTTP GET + events | already planned; **adoption gap** (bytes discarded) | COMP-QMA-DAEMON + WIRE | journal | CT-40 three families | authenticate before protocol | Epic 41.2 additive | mismatch → J-UI-13 | loopback or recorded TLS | Epic 41, 42 |
| Listener loopback / TLS non-loopback | already planned; types exist | COMP-QMA-WIRE listener | config | bind rules | hard startup refusal if plaintext non-loopback | n/a | no warning fallback | local vs recorded remote | Story 41.4 |
| Pairing HTTP `/pair/*` + `pairing_proof` / `pairing_record_id` | **proposed amendment** AM-01, AM-11 | DAEMON projection + QMB host-control confirm | record id + `proof_fp1` (never raw proof) | POST start/confirm; Bearer `pairing:<proof>`; WS `qmx.pair.<proof>` | operator after local pair | additive; cookies forbidden | Origin-only → refuse; confirm once; lost confirm → re-pair | same daemon origin | **new**; after live server **and** AD-17 bootstrap |
| Authenticated `/pair/renew` | **proposed amendment** (AD-3 path 2) | DAEMON | new pairing_session row | POST `/pair/renew` Bearer | existing valid proof + Origin | additive | revoked/expired refuse | same origin | same pairing stories |
| CORS exact origin | **proposed amendment** (needed by SPA origin ≠ 8765) | DAEMON HTTP | paired Origin on the row | ACAO exact; credentials omit | n/a | authenticated routes never `*` | preflight fail is not retarget | SPA static origin | pairing stories |
| Revocation / TTL | **proposed amendment** | DAEMON + `qmb host pair revoke` | `revoked_at`; `registry:pairing.session_ttl` (unset → refuse issue) | status shows presence only | operator | n/a | revoke closes that WS; dead id dropped client-side | local sqlite | pairing stories; number later |

## 3. QMB host / process lifecycle

| Need | Class | Owner | Durable record | Wire/API | AuthZ | Compat | Failure/recovery | Placement | Stories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `python -m qma.daemon` process entry | reuse | COMP-QMA-DAEMON | process | none | n/a | cwd default is **not** product root | n/a | workstation | exists |
| `.daemon_writer` lock | reuse | DAEMON | lock file under root | n/a | n/a | n/a | second start reports already-running | `QMA_DAEMON_ROOT` | Story 42.1 |
| `qmb host start\|status\|stop` | **proposed amendment** AM-10 | COMP-QMB | none (supervises daemon) | CLI | operator OS user | n/a | stale lock = QMB/daemon recovery, not UI | local only | **new QMB stories** |
| First operator + host-control | **proposed amendment** AM-15 | COMP-QMB + DAEMON | `local_operator` + `host_control` token | local loopback control | OS user + token (running); OS owner of stopped root for `recover-control` | n/a | forged ref / remote without token refuse; lost file → `recover-control` (C1) | `QMA_DAEMON_ROOT` | **new**; before pairing issue |
| `qmb host pair` / `pair revoke` / `configure pairing-ttl` / `rotate-control` / `recover-control` | **proposed amendment** AM-10 | COMP-QMB host-control | pairing projection / registry / `host_control_fp1` | CLI local control | host_control (running); OS-owner stopped root (`recover-control`) | n/a | `--origin` barrier (C2); unknown code → typed refuse | same host as daemon | pairing stories |
| Stable per-user root | **proposed amendment** of `__main__.py` cwd default | QMB start sets env | directory | env `QMA_DAEMON_ROOT` | n/a | existing cwd trees stay dev-only | two folders = two trees | Windows `%LOCALAPPDATA%\QMX\qma-daemon` | host stories |

## 4. Conversation routing, history, recovery

| Need | Class | Owner | Durable record | Wire/API | AuthZ | Compat | Failure/recovery | Placement | Stories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `send_message` name | reuse vocab; adoption gap (no socket dispatch) | WIRE + DAEMON | mailbox Envelope | command | connection principal **equals** session principal; **not** a GrantRecord | seed command | lost ack → query, no new id | daemon mailbox | Epic 41.1 + 46.4 |
| Envelope `product_session_ref` | **proposed amendment** AM-02, AM-14 | DAEMON bus/journal | Envelope + `message.*` | payload field on send | same principal check as query | additive `_ref`; old folds ignore unknown | rebuild by field, never body parse | same daemon | **amend Story 46.4**; do not replace it |
| `list_mailbox` | **proposed amendment** AM-08 | WIRE vocab + DAEMON fold | delivery projection | query snapshot + pair lookup | same principal as send | addable query | absent query → `query_unavailable`, not empty chat | local daemon | Epic 41 addable + 46.4 fold |
| Wire pair + payload hash on journal | **proposed amendment** (needed for pre-ack lookup) | DAEMON journal | `message.*` extra keys | not a second identity | n/a | additive | collision different hash refuses journal-lifetime | n/a | 46.4 + 41.3 dedup |
| Pending client triple | UI client-local `sessionStorage` | UI host | none durable | n/a | n/a | lost on cold start | AD-14 | browser tab | UI sitting; backend supplies lookup |
| Journal/fold infrastructure | already planned | DAEMON | journal | n/a | n/a | n/a | fold rebuild | `QMA_DAEMON_ROOT` | Epic 42 |

## 5. Cancel authorization and handle lifecycle

| Need | Class | Owner | Durable record | Wire/API | AuthZ | Compat | Failure/recovery | Placement | Stories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| JobHandle vocab / `later_commands` | reuse types; adoption gap (in-memory store vs sqlite) | DAEMON | handle row | attach/reattach/cancel ops exist in-process | QMA AD-17 | states closed | first terminal wins | env lease | Epic 57.3; Story 42 persistence |
| `originating_product_session_ref` | **proposed amendment** AM-04, AM-14 | DAEMON at admit | optional handle field | snapshots | UI operator of that session; omitted if headless | additive `_ref` | missing field → UI cancel unavailable; QMB Story 36.5 remains | n/a | **amend Epic 57 handle record**; Epic 63 children |
| `cancel_job` command | **proposed amendment** AM-09 | WIRE + DAEMON | handle + later_commands | command | exact handle/run/attempt; originating operator | addable; not `stop_run` | queued→running same command_id; terminal no-op; unknown not cancellable | n/a | new wire story; uses Epic 57 |
| Nested child cancel | already planned occupancy + this originating field | DAEMON | child handle | same `cancel_job` | child ref or omitted if headless | n/a | cancel child ≠ splice graphs | n/a | Epic 63.1 |

## 6. Artifact possession and transfer

| Need | Class | Owner | Durable record | Wire/API | AuthZ | Compat | Failure/recovery | Placement | Stories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `before_artifact_register` / fp1 | reuse (cite path) | DAEMON | artifact store | hook | n/a | n/a | n/a | daemon artifact store | QMA AD-19 cite; Epic 42 artifact store |
| HTTP PUT `/artifacts/stage` | **proposed amendment** AM-05 | DAEMON | artifact bytes + fp1 | PUT + Content-Length + Bearer | pairing operator; not a pack op | not REST invoke | interrupt → delete incomplete; oversize → refuse | **local** daemon first | **new**; reuse register hook |
| `registry:artifact.stage_max_bytes` | **proposed amendment** (QMA AD-26 row) | registry | registry row | n/a | operator `variable.set` | n/a | missing length → refuse | n/a | new registry row; no number here |
| `transfer_artifact` + reachable pull | **proposed amendment** AM-06 | DAEMON ticket + dest pull + `transfer_complete` | local fp1 stays; dest copy | command_id + machine GET + dest ack | dest audience credential; recorded TLS source | additive | `source_unreachable` on loopback; invoke refuses until complete | dest must dial recorded source HTTPS | **new** |
| Knowledge cite | reuse | DAEMON knowledge | cite-copy artifact | CT-44 | granted retrieval | n/a | StaleSnapshot | n/a | QMA AD-19 |

## 7. Saved drafts and authoring publication

| Need | Class | Owner | Durable record | Wire/API | AuthZ | Compat | Failure/recovery | Placement | Stories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Graph Template at enable | reuse / already planned | DAEMON plugins | contribution at enable | install_enable_plugin | operator enable | parent AD-30 | failed enable restores last roster | local pack roster | parent AD-4/AD-30; Epic 53/58 |
| `editor_draft_head` + CAS | **proposed amendment** AM-03/AM-07 | DAEMON | draft head + artifact bytes | first save omits id; later CAS `expected_revision`; reload `get_editor_draft_head` (AM-17) | authoring operator | additive projection | lost first-save uses `client_draft_correlation`; supplied id on first save refuses | local daemon | **new**; must not use AD-22 staging |
| `publish_editor_draft` | **proposed amendment** AM-09 | DAEMON | local authoring pack contribution | command revalidates immutable fp1 then writes | draft owner | additive | invalid/stale/unauthorized refuse | this machine | **new**; then parent AD-30 enable |
| Local authoring pack enable as first Run | reuse parent AD-30 | DAEMON pack journal | pack instance | enable then dispatchInvoke | grant after enable | no second enable machine | draft Run refused | this machine | UI AD-21; no new enable stories |
| Distributable export | already planned later | pack export scanner | export report | parent AD-18 | n/a | later | n/a | other machines | parent AD-18; not first Run |

## 8. First-run provider setup

| Need | Class | Owner | Durable record | Wire/API | AuthZ | Compat | Failure/recovery | Placement | Stories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Credential Broker exact-ref | reuse types; **adoption gap** (`_reader` uninjected) | DAEMON proxy | OS store behind interface | never secret on wire | allowlist | n/a | `CredentialOutOfScope` | workstation OS store | QMA AD-24; Story 41.4 |
| Host write-to-OS-store | **deferred** later QMB/native helper | COMP-QMB later | OS cred | not CT-40 payload | operator | v1 shell does not require it; **provider use** does (external provision) | reconnect does not resubmit secret | local OS | revisit when v1 must write secrets without an external store |
| Local model-plane CLI proxy | **already planned** / adoption gap of QMA AD-15 ModelDeployment | DAEMON model plane | Deployment behind `cred://inference` | not pairing; not QMB host | operator of that ref | n/a | unhealthy card; shell still up | workstation | QMA AD-15; not a broker-allowlist add |
| `update_configuration` / `get_provider_health` | reuse vocab | WIRE + DAEMON | config CAS | seed command + query | operator | n/a | no replay of unacked secret | n/a | Epic 41 seed |

## 9. Client/core compatibility and installed-product

| Need | Class | Owner | Durable record | Wire/API | AuthZ | Compat | Failure/recovery | Placement | Stories |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `initialize` capabilities | reuse handshake; **amend** advertised set | WIRE | connection | JSON-RPC initialize | after pairing or cred-ref | additive caps | missing cap → typed mismatch | n/a | Epic 41.1 + J-UI-13 |
| Clean-machine launch | **proposed amendment** of data-root default | QMB host + daemon | `QMA_DAEMON_ROOT` tree | CLI | OS user | n/a | cwd-relative tree is not the product | workstation | host stories + J-UI-14 |
| Client update | UI stream | static origin | client bits ≠ sqlite | n/a | n/a | rollback client bits only | reconnect query | static host | UI AD-16; not this Python |
| Tauri packaging | deferred | later | n/a | calls same QMB verbs | n/a | not v1 | n/a | desktop | UI AD-12 |

## Hold vs continue

Independent planned epics **continue**. Hold only stories whose **contract** conflicts:

- Story 41.4 unauthenticated-bind sentence — hold for AM-01 wording.
- Story 46.4 Envelope field list — hold for AM-02 additive field.
- Epic 57 handle record — hold for optional `originating_product_session_ref` (states unchanged, so 57.3 vocab stories otherwise proceed).
- Epic 60.1 — **do not hold**; PackUiRequest is additional, not a replacement.

No predicted final epic count.
