---
name: C1/C2 closure map
sitting: architecture-QMX-UI-BACKEND-2026-09-24
date: 2026-09-24
status: candidate — focused Codex closure
inspect: 34c148be404a375cbfd79fd4ce6997452e4f1d20
---

# C1/C2 closure map

From `workroom/qmx-ui-backend-closure-2026-09-24/REVIEW.md`. J3/J4/J5 and the completed small reconciliations stay. Origin-only issuance stays closed.

| ID | Finding | Binding | Status |
| --- | --- | --- | --- |
| C1 | Lost `host_control` recovery required the lost token | Stopped daemon; OS owner of `QMA_DAEMON_ROOT` runs `qmb host recover-control` without presenting the lost token; `local_operator` and journals preserved | **closed as candidate** |
| C2 | Origin-revoke discarded if renew committed first | `--origin` is a barrier at `journal_seq` R; renew-then-revoke kills the new proof; revoke-then-renew refuses. `--session` is that record only | **closed as candidate** |

## C1 — Lost host_control recovery

**Choice.** Owner-verified **offline replacement** while the daemon is stopped. Not a backup-restore path (that remains a later ops story). Not `rotate-control` (that still needs the current token).

| Path | When | Proof | Result |
| --- | --- | --- | --- |
| `rotate-control` | Token still held; daemon live | Current `host_control` | New file; old `host_control_fp1` dead; same `local_operator` |
| `recover-control` | File missing or unreadable; daemon **stopped** | OS user owns `QMA_DAEMON_ROOT`. **No** lost token. One-shot daemon recover entry writes the journal (QMB never writes sqlite; no 8765 bind) | New owner-only file; old fingerprint dead; `local_operator` and journals **preserved** |

Does not remint a second principal. Does not delete the data root. Empty root = no `local_operator` (first-start bootstrap). Missing token + existing `local_operator` is not empty. Live daemon with missing file: OS owner may `stop` without the token, then recover. Other OS user → refuse. Readable token file still present → refuse (use rotate-control).

**Evidence**

| Claim | File / section |
| --- | --- |
| AD | backend AD-17, AD-6 |
| Companion | `HOST-LIFECYCLE.md` Recovery / Rotation rows, T-H-01..04, verbs |
| Amendment | AM-10 adds `recover-control` |
| UI | `BOOTSTRAP-AND-AUTH.md` §12 verbs |

**Positive traces.** T-H-01 rotate while held. T-H-02 lost file + stopped daemon + owning user `recover-control` → new file, same principal, journals intact, then start. T-BE-27.

**Negative traces.** T-H-03 start after lost file without recover → host-control verbs refuse; no second principal. T-H-04 / T-BE-28 other OS user. Recover while live. Recover while file still readable.

## C2 — Origin-revoke vs renew

**Choice.** Two revoke scopes.

| Verb | Scope |
| --- | --- |
| `pair revoke --session <pairing_record_id>` | That record only. After a renew, the old id is already rotated; `--session` of the old id is a recorded no-op; the **new** proof stays live |
| `pair revoke --origin <origin>` | Administrative **barrier** for that static Origin. Durable at `journal_seq` R: every `pairing_session` and `pairing_pending` for that Origin with `journal_seq` < R is revoked, including confirmed-unconsumed pendings **and a renew that committed earlier**. Never discarded because a renew appended first. After R: `/pair/renew` / `/pair/confirm` of pre-R rows refuse. **New** `/pair/start` after R is legal (re-pair). Close matching WS |

Serialized outcomes:

1. Renew first, then `--origin` → new proof revoked.
2. `--origin` first, then `/pair/renew` with the old proof → refuse.

Journal order still serializes appends. Origin-revoke is not a CAS loser.

**Evidence**

| Claim | File / section |
| --- | --- |
| AD | backend AD-4 |
| Companion | `PAIRING-AND-ADMISSION.md` lifecycle rows + T-P-11..13 |
| UI | `BOOTSTRAP-AND-AUTH.md` §12 revoke verbs |
| Traces | T-BE-30, T-BE-31 |

## Preserved

J3 daemon draft issuer, J4 `publish_editor_draft`, J5 reachable TLS + dest `transfer_complete`, small reconciliations, Origin-only issuance, layouts, Svelte, Epics 60–65.

J5 stays a registered authenticated destination control connection plus a reachable allowed source. No arbitrary inter-daemon discovery.

## Honesty

No live daemon. Tests unexecuted. Candidate ≠ operator acceptance. Documentation Factory still waits on focused closure.
