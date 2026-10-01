---
name: Independent C1/C2 closure review
sitting: architecture-QMX-UI-BACKEND-2026-09-24
against: workroom/qmx-ui-backend-closure-2026-09-24/REVIEW.md remaining corrections C1 and C2 only
date: 2026-09-24
reviewer: Grok 4.6 independent closure
status: closed as candidate — no remaining High
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
tests: unexecuted
---

# Independent C1/C2 closure review

Do not implement. Historical first-pass files under `reviews/` were not edited. This file is the focused closure pass over the **live** backend-delta packet and the **reconciled** UI candidate, against remaining corrections **C1** and **C2** only.

**Packets**

- Backend-delta: `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-BACKEND-2026-09-24/`
- UI candidate: `_bmad-output/planning-artifacts/architecture/architecture-QMX-UI-2026-09-23/`
- Remaining corrections: `workroom/qmx-ui-backend-closure-2026-09-24/REVIEW.md` (C1, C2)
- Live law cited by the launch: backend AD-4, AD-6, AD-17; `HOST-LIFECYCLE.md`; `PAIRING-AND-ADMISSION.md`; `CLOSURE-C1-C2.md`; `TRACE-MATRIX.md` T-BE-27..31; UI `BOOTSTRAP-AND-AUTH.md` §12

**Verdict:** C1 and C2 **closed as candidate**. Remaining High: **none**. J3, J4, and J5 are **not reopened**. Origin-only issuance remains closed. Layouts, Svelte/TypeScript, headless/visual, and Epics 60–65 were not reopened. Candidate ≠ operator acceptance. No live daemon, no executed tests, no Documentation Factory.

| ID | Finding | Verdict | Remaining High |
| --- | --- | --- | --- |
| C1 | Lost `host_control` recovery required the lost token | **closed** | none |
| C2 | Origin-revoke discarded if renew committed first | **closed** | none |
| J3 | One durable draft-id issuer | **preserved closed** | none |
| J4 | Validated publication | **preserved closed** | none |
| J5 | Reachable artifact transfer | **preserved closed** | none |

---

## Method and preserve checks

Reviewed live sentences in backend AD-4, AD-6, AD-17; `HOST-LIFECYCLE.md`; `PAIRING-AND-ADMISSION.md`; `CLOSURE-C1-C2.md`; `PARENT-AMENDMENT-MAP.md` AM-03/AM-10/AM-15; `DEPENDENCY-MAP.md` §3; `TRACE-MATRIX.md` T-BE-27..31; `CLOSURE-J1-J5.md`; `CLOSURE-EVIDENCE.md`; `UI-CANDIDATE-CHANGELOG.md` Round 3; UI `BOOTSTRAP-AND-AUTH.md` §12 (and locked defaults / AD-19 for verb-list consistency); and the J3/J4/J5 owners (`PACK-UI-AND-AUTHORING.md`, `ARTIFACTS-AND-TRANSFER.md`, backend AD-9/AD-11, UI AD-21/AD-22). Historical `reviews/` and memlog decisions are evidence of prior state, not current law.

| Preserve check | Result |
| --- | --- |
| J3 not reopened | **Hold.** Backend AD-11: “**Daemon** is the sole durable `editor_draft_id` issuer. First `save_editor_draft` **omits** `editor_draft_id`.” `PACK-UI-AND-AUTHORING.md` Draft identity table and T-BE-17 unchanged in substance. UI AD-21 same issuer. C1/C2 files do not retarget draft identity. |
| J4 not reopened | **Hold.** AD-11: addable `publish_editor_draft` “checks draft ownership, `expected_revision`, **reruns** validation against that immutable fp1 … Parent AD-30 **enable** remains compile identity.” PACK-UI Publication section and T-BE-18 unchanged. UI AD-21 same. |
| J5 not reopened | **Hold.** AD-9: ticket only when “the **source daemon origin is recorded reachable TLS**”; default loopback is typed `source_unreachable`; dest-authored `transfer_complete`; invoke refuses until complete. `ARTIFACTS-AND-TRANSFER.md` still requires a **registered authenticated destination control connection** plus a reachable allowed source. No inter-daemon discovery. UI AD-22 same. |
| Origin-only issuance still closed | **Hold.** Backend AD-3: “A remembered Origin **never** authorizes issuance of a new pairing proof.” UI AD-19: “a remembered Origin never authorizes a new `pairing_proof`.” T-BE-01 / T-P-01 unchanged. |
| Small reconciliations still closed | **Hold.** Provider vs shell, `get_pack_ui_request`, mailbox principal equality when `product_session_ref` is present, cancel/headless omit, `_ref` naming, AM-17 `get_editor_draft_head` are not rewritten by C1/C2. |
| Layouts / Svelte / headless / Epics 60–65 | **Hold.** `UI-CANDIDATE-CHANGELOG.md` Round 3 edits only `BOOTSTRAP-AND-AUTH.md` §12. `EXPERIENCE-AND-LAYOUT.md` not edited. `PluginManifest.copilot_profile` stays Epic 60 sibling. |

Honesty limits (not defects): inspect SHA still `34c148be`; `DaemonProcess` still discards TCP bytes; `qmb host`, pairing HTTP, and `recover-control` remain **absent in code**. Planned epics are requirements, not delivery.

---

## C1 — Lost host_control recovery — **closed**

**Required result (REVIEW.md C1).** Recovery from lost `host_control` without requiring that lost token. Preserve `local_operator` and journals. Do not remint operator or delete the data root. Traces for lost-file plus restart, unauthorized local user, and normal rotation. Choose owner-verified offline replacement **or** protected-backup restore; do not silently remint. Exact OS API/signal mechanics may remain implementation detail.

### Choice (live)

Owner-verified **offline replacement** while the daemon is stopped. Not backup-restore (QMA AD-27 remains later). Not `rotate-control` (that still presents the current token).

**Quoted `CLOSURE-C1-C2.md`:** “Owner-verified **offline replacement** while the daemon is stopped. Not a backup-restore path (that remains a later ops story). Not `rotate-control` (that still needs the current token).”

| Path | When | Proof | Result |
| --- | --- | --- | --- |
| `rotate-control` | Token still held; daemon live | Current `host_control` | New file; old `host_control_fp1` dead; same `local_operator` |
| `recover-control` | File missing or unreadable; daemon **stopped** | OS user owns `QMA_DAEMON_ROOT`. **No** lost token | New owner-only file; old fingerprint dead; `local_operator` and journals **preserved** |

### Evidence in both packets

| Claim | Backend | UI |
| --- | --- | --- |
| Recovery does not present the lost token | spine **AD-17**, **AD-6**; `HOST-LIFECYCLE.md` Lost-token recovery row + verb `recover-control`; **AM-10** | `BOOTSTRAP-AND-AUTH.md` §12 `recover-control` |
| Preserve `local_operator` and journals; no remint; no wipe | AD-17; HOST Trust root / T-H-02 / verb Does-not; T-BE-27 | §12 Does-not: “remint principal; wipe the data root” |
| Rotation still requires the held token | AD-17 Rotation; HOST Rotation row; T-H-01; T-BE-29 | §12 `rotate-control` Does-not: “Recover a lost file” |
| Unauthorized OS user refused | AD-17; HOST T-H-04; T-BE-28 | §12 Does-not: “other OS user” |
| Lost-file + restart does not remint | HOST T-H-03 | (backend trace; UI §12 stop-then-recover) |

**Quoted backend AD-17:** “**Lost-token recovery** (file missing or unreadable): daemon **must be stopped**; the OS user who owns the root runs `qmb host recover-control`. That verb does not present the lost token. It verifies OS ownership of `QMA_DAEMON_ROOT`, mints a new owner-only `host_control` file, journals the new fingerprint and the invalidation of the previous one, and **preserves** `local_operator` and all journals. It does not remint a second principal. It does not delete the data root. If the daemon is live, recover-control refuses (stop first; use rotate-control if the token is still held). If another OS user, refuse. If the token file is still readable, refuse recover-control.”

**Quoted backend AD-6:** “Privileged verbs are `qmb host start|status|stop|pair|configure|rotate-control|recover-control` (COMP-QMB add). … `rotate-control` and `recover-control` are AD-17. QMB never writes daemon sqlite.”

**Quoted `HOST-LIFECYCLE.md` Lost-token recovery:** “File missing or unreadable. Daemon **stopped**. Owning OS user runs `qmb host recover-control` (**no** lost token presented). New owner-only file; previous fingerprint invalidated; `local_operator` and journals **preserved**. Does not remint a principal. Does not delete the data root. Live daemon → refuse (stop first). Other OS user → refuse. Readable token file still present → refuse (use rotate-control).”

**Quoted AM-10:** “Add group `host`: `start`, `status`, `stop`, `configure pairing-ttl`, `pair <code>`, `pair revoke --session|--origin`, `rotate-control`, **`recover-control`**. … `recover-control` is OS-owner of a **stopped** root and does not present the lost token.”

**Quoted UI `BOOTSTRAP-AND-AUTH.md` §12:** “`qmb host recover-control` | Daemon **stopped**; OS owner of `QMA_DAEMON_ROOT`; lost/unreadable token file; mint a new file **without** presenting the lost token; preserve `local_operator` and journals | Live daemon; other OS user; remint principal; wipe the data root.”

**Quoted UI §12 rotate:** “`qmb host rotate-control` | New `host_control` while the current token is held | Recover a lost file; change `local_operator`.”

The prior HOST/AD-17 sentence that a lost `host_control` file “refuses until rotate-control presents a still-valid token” is gone from **live** law. Rotation and recovery are now two verbs.

### Required traces

| Required | Live row | Must | Must not |
| --- | --- | --- | --- |
| Normal rotation | T-H-01; T-BE-29 | Token held, `rotate-control` → new file; old `host_control_fp1` dead; same `local_operator`; journals intact | `recover-control` on a live daemon; change principal |
| Lost-file + recover | T-H-02; T-BE-27 | Stopped daemon; OS owner; `recover-control` → new token; same `local_operator`; journals intact; old fingerprint dead; then `start` | Require the lost token; remint principal; wipe root |
| Lost-file + restart | T-H-03 | File deleted; daemon restarted (lock free) **without** recover → host-control verbs refuse until `recover-control`; pairing proofs still valid until TTL; **no second principal** | Treat missing file as empty-root bootstrap |
| Unauthorized local user | T-H-04; T-BE-28; HOST negative “Other OS user + `recover-control`” | Refuse; data root untouched; `local_operator` and journals unchanged | Steal operator by file create |

Additional HOST negatives bind the remaining refuse matrix: lost file + live daemon + `rotate-control` refuses (no token to present; stop then `recover-control`); `recover-control` while daemon live refuses; `recover-control` while the token file is still readable refuses (use `rotate-control`).

T-H-03 is the required **lost-file plus restart** trace. It lives on the host companion rather than `TRACE-MATRIX.md` T-BE-27..31. That is table placement, not a missing outcome: restart without recover must not remint, and host-control stays refused until `recover-control`.

### Named inherited amendments

| ID | What it names |
| --- | --- |
| **AM-10** | QMB group `host` includes `rotate-control` and **`recover-control`**. Running-daemon verbs stay `host_control`. Recover is OS-owner of a stopped root and does not present the lost token. |
| **AM-15** | Local host-control under `QMA_DAEMON_ROOT` is outside port 8765. Trust root remains OS user + token. Broker allowlist **not** widened. |
| **AM-03** | Journal projection `local_operator`; live shape includes current `host_control_fp1`. |

### Deferrals (honest, not C1 holes)

- Exact OS API, signal, timeout, and stale-PID lock mechanics remain implementation stories (`HOST-LIFECYCLE.md` Data root and lock; C1 allowed this).
- Host-control IPC encoding (loopback HTTP vs named pipe vs file drop) stays deferred; token + loopback + “not CT-40” is frozen.
- Backup/restore remains QMA AD-27. C1 explicitly did **not** choose that path.
- Who **folds** the new `host_control_fp1` while the daemon is stopped is not a second recovery design. AD-6 still says “QMB never writes daemon sqlite.” HOST `configure pairing-ttl` already writes “via daemon (sole writer).” Unique reading that preserves both sentences: `recover-control` replaces the owner-only **file** under the stopped root; the journal fold of the new fingerprint is daemon-authored on the next `start` (T-H-02 ends “then `start`”) or a one-shot daemon writer QMB invokes without binding CT-40. QMB sqlite is forbidden. Documentation Factory should say that once, not invent a second writer.

C1’s required outcomes are uniquely specified. **Closed as candidate.**

---

## C2 — Origin-revoke vs renew — **closed**

**Required result (REVIEW.md C2).** Renew first then origin-revoke must revoke the newly issued proof. Origin-revoke first makes renewal refuse. `--session` scope distinct from `--origin`. Both orderings traced. Journal first-append-wins must **not** discard a later origin-revoke.

### Choice (live)

Two revoke scopes. `--origin` is an administrative **barrier** at `journal_seq` R, not a CAS loser against an earlier renew.

| Verb | Scope |
| --- | --- |
| `pair revoke --session <pairing_record_id>` | That record only. After a renew, `--session` of the **old** id is a recorded no-op; the **new** proof stays live |
| `pair revoke --origin` | Barrier at `journal_seq` R: every `pairing_session` and `pairing_pending` for that Origin with `journal_seq` < R is revoked, including confirmed-unconsumed pendings **and a renew that committed earlier**. Never discarded because a renew appended first |

Serialized outcomes (journal order):

1. Renew first, then `--origin` → new proof revoked.
2. `--origin` first, then `/pair/renew` with the old proof → refuse.

**Quoted `CLOSURE-C1-C2.md`:** “Journal order still serializes appends. Origin-revoke is not a CAS loser.”

### Evidence in both packets

| Claim | Backend | UI |
| --- | --- | --- |
| `--origin` barrier includes an earlier renew | spine **AD-4**; `PAIRING-AND-ADMISSION.md` lifecycle rows; HOST verb `--origin` | BOOTSTRAP §12 `--origin` |
| Renew then `--origin` kills the **new** proof | PAIRING “Renew then origin-revoke”; T-P-11; T-BE-30 | §12 Does-not: “Discard the revoke because a renew appended first” |
| `--origin` then renew refuses | PAIRING “Origin-revoke then renew”; T-P-12; T-BE-31 | implied by barrier + AD-3 unrevoked-proof renew; explicit refuse is backend |
| `--session` is that record only | AD-4; PAIRING `--session` row + “`--session` after that id already renewed”; T-P-13 | §12 `--session` Does-not: “Origin-wide cutoff” |
| First-append-wins does not drop later `--origin` | AD-4 “Origin-revoke is never discarded because a renew appended first.” | §12 Does-not discard |

**Quoted backend AD-4:** “**`--session`** revokes that `pairing_record_id` only. **`--origin`** is an administrative barrier: when that event is durable at `journal_seq` R, every `pairing_session` and `pairing_pending` for that Origin with `journal_seq` < R is revoked (including **confirmed-unconsumed** pendings and a **renew that committed earlier**). Origin-revoke is never discarded because a renew appended first. After R, `/pair/renew` with any proof for that Origin refuses; `/pair/confirm` cannot issue. Close matching WS.”

**Quoted `PAIRING-AND-ADMISSION.md` §4:**

- “`pair revoke --session <pairing_record_id>` … **That record only** revoked; close its WS. Does not revoke a later renew’s new `pairing_record_id`.”
- “`pair revoke --origin` … **Barrier** at `journal_seq` R: every `pairing_session` and `pairing_pending` for that Origin with `journal_seq` < R is revoked, including **confirmed-unconsumed** pendings **and a renew that committed earlier**. … Origin-revoke is never a no-op loser” (renew-then-revoke row).
- “Renew then origin-revoke | Renew durable first (seq < R), then `--origin` | New proof **revoked**. Origin-revoke is never a no-op loser.”
- “Origin-revoke then renew | `--origin` durable first, then `/pair/renew` with the old proof | Typed refuse. Old proof already revoked.”
- “`--session` after that id already renewed | … Old row already rotated; `--session` of the old id is a recorded no-op; **new** proof stays live | Use `--origin` to kill the new proof.”

**Quoted HOST `--origin` Does-not:** “Discard the revoke because a renew appended first; delete journal history.”

**Quoted UI `BOOTSTRAP-AND-AUTH.md` §12:**

- “`qmb host pair revoke --session <pairing_record_id>` | Revoke **that** record only; close its WS | Origin-wide cutoff; delete journal history”
- “`qmb host pair revoke --origin` | Barrier: every session and pending for that Origin with `journal_seq` before the revoke, including a renew that committed earlier; close matching WS | Discard the revoke because a renew appended first”

The prior PAIRING sentence that concurrent renew versus revoke is first-append-wins and “the loser may be a no-op or refusal” is gone from **live** PAIRING. First-append-wins remains **only** for two concurrent `/pair/confirm` on the **same** pending (consume-once). That is a different race and does not authorize discarding a later `--origin`.

### Required traces

| Required ordering | Live row | Must | Must not |
| --- | --- | --- | --- |
| Renew first, then `--origin` | T-P-11; T-BE-30 | **New** proof revoked; its WS closed | Discard the revoke as first-append loser |
| `--origin` first, then `/pair/renew` | T-P-12; T-BE-31 | Typed refuse | New proof after explicit origin revoke |
| `--session` ≠ `--origin` | T-P-13 | Renew then `--session` of the **old** id → new proof still live | Treat `--session` as origin-wide cutoff |

T-P-06 remains the earlier-sessions / confirmed-unconsumed cutoff. C2 adds the renew-vs-barrier orderings rather than replacing T-P-06.

### Named inherited amendments

| ID | What it names |
| --- | --- |
| **AM-10** | `pair revoke --session|--origin` on the host group. |
| **AM-03** | Projections `pairing_pending` / `pairing_session`; fold ordering `journal_seq`. The barrier is defined on that sequence. |
| **AM-11** | Bearer vs record id; journal stores `proof_fp1` only (unchanged by C2). |

AD-3 issuance is preserved: a new proof still requires QMB confirm of **that** pending or authenticated renew of an **unexpired unrevoked** proof. After `--origin`, path (2) refuses. Path (1) for a **new** pending is the re-pair the PAIRING client column names (“All tabs on that Origin re-pair”).

### Residual wording (not High)

AD-4 / CLOSURE-C1-C2 / PAIRING say “After R, `/pair/renew` and `/pair/confirm` for that Origin refuse.” Read against the barrier definition (`journal_seq` < R) and AD-3, **confirm cannot issue** applies to pre-R pendings (including confirmed-unconsumed). A new `/pair/start` after R creates a pending with `journal_seq` > R; fresh `qmb host pair` then `/pair/confirm` is the re-pair path the client column requires. A builder who treats `--origin` as a permanent Origin ban would contradict AD-3 and “re-pair.” Documentation Factory should qualify “cannot issue” as **pre-R pendings and renew of pre-R proofs**, not a lifetime Origin kill. That qualification is cleanup, not a missing C2 outcome: both required orderings are unique without it.

`--origin` argv does not yet spell `<origin>`. Semantic scope is origin-wide versus `--session` of one `pairing_record_id`. Stories may freeze `--origin <origin-url>` (one Origin) versus host-wide all Origins. v1’s single SPA origin makes the product outcome the same until a second static origin exists. Not a C2 reopen.

C2’s required outcomes are uniquely specified. **Closed as candidate.**

---

## Residuals for Documentation Factory (not High, not C1/C2 holes)

- Fold of `host_control_fp1` on recover: daemon-authored (next `start` or one-shot writer). QMB still must not write sqlite (AD-6).
- Qualify “After R, `/pair/confirm` cannot issue” to pre-R rows; new start + QMB pair + confirm remains re-pair.
- Freeze `--origin` argv (`--origin <origin>` vs host-wide).
- Promote HOST T-H-03 onto `TRACE-MATRIX.md` if the acceptance table should hold lost-file+restart in one place. Outcome already bound.
- UI AD-19 and BOOTSTRAP locked-defaults “Named add” still list `qmb host start|status|stop|pair|configure` without `rotate-control` / `recover-control`. §12 has the verbs. Insert them at DF.
- UI BOOTSTRAP §5.5 still says cloned tabs “reconnect or renew.” Locked defaults and backend AD-14 already bind: clone **reconnects**; `/pair/renew` is **not** the clone path. Pre-existing leftover, not a C2 miss.
- UI `CLOSURE-MAP.md` still points at `CLOSURE-J1-J5.md` only. Backend `CLOSURE-C1-C2.md` is the C1/C2 map. Add a pointer at DF.
- `CLOSURE-EVIDENCE.md` cites `reviews/gate-c1c2-summary.md`, which is **not** in the tree. Hygiene only.
- Historical `reviews/` and memlog still describe pre-C1 rotate-only recovery and pre-C2 first-append-wins renew/revoke. Leave them; they are not law.

---

## Honesty

No live daemon. Tests unexecuted (T-H-01..04, T-P-11..13, T-BE-27..31). Candidate ≠ operator acceptance. No implementation, Documentation Factory, epic rewrite, or factory control occurred in this review.

---

## Closure decision

C1 and C2 are **closed as candidate** in both packets. J3, J4, and J5 remain closed. Origin-only issuance remains closed. No remaining High.

Recommended next stage (unchanged): **one integrated Documentation Factory pass → coordinated epic/story amendments and additions → software-factory execution**. This sitting still starts none of those.
