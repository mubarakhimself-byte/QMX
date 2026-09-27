---
review: adversarial-c1c2
target: architecture-QMX-UI-BACKEND-2026-09-24
amended_spine: AD-4, AD-6, AD-17 plus HOST-LIFECYCLE / PAIRING-AND-ADMISSION / CLOSURE-C1-C2
reconciled_ui: architecture-QMX-UI-2026-09-23 BOOTSTRAP-AND-AUTH.md §12
date: 2026-09-24
inspect: integration@34c148be404a375cbfd79fd4ce6997452e4f1d20
lens: 'Two factory units, every live AD to the letter, still incompatible on recover vs rotate vs empty-start, stopped-daemon predicate, OS-owner vs token, and origin-revoke barrier vs leftover cutoff. Attack C1 and C2 only. Historical reviews/ are evidence, not law. OS API / stale-PID supervisor mechanics the prior review allowed to stay a story stay a story.'
status: sitting-candidate — not operator-accepted
tests: unexecuted
---

# Adversarial review — C1/C2 correction

## Method

Build **two factory units** one level down from this sitting (stories / builders). Both obey every **live** local AD (backend AD-1..AD-17), the companions those ADs name (`HOST-LIFECYCLE.md`, `PAIRING-AND-ADMISSION.md`), named amendments AM-03 / AM-10 / AM-15, UI `BOOTSTRAP-AND-AUTH.md` §12, traces T-H-01..04 and T-BE-27..31 / T-P-11..13, and inherited QMA sole-writer / journal-fold law the spine already binds. They still cannot share a daemon, a `host_control` file, or a pairing fold.

A pair is a hole only when **both readings are literal**. Historical first-pass and J1–J5 reviews (`reviews/review-adversarial.md`, `reviews/review-j1j5-*.md`) and the 2026-09-24 as-reviewed packet that still named `issued_at`/`created_at` ≤ cutoff are **not** current law. They are cited only where live companions still carry the leftover joint. Inspect types at `34c148be` are substrate, not delivery.

**Out of this gate (already allowed to stay a story):** host-control IPC encoding (HTTP vs named pipe vs file drop); token entropy / RFC 6455 charset; numeric pairing TTL; ordinary supervisor **signal / timeout / stale-PID** mechanics for `qmb host start|stop` so a crashed daemon can be started again (HOST-LIFECYCLE data-root paragraph; `CLOSURE-J1-J5.md` remaining deferrals; DEPENDENCY-MAP “stale lock = QMB/daemon recovery, not UI”); the OS API used to *read* directory owner once the refuse is unique (Windows `GetNamedSecurityInfo` vs POSIX `st_uid`). Those do not license a second mutation path for recover or origin-revoke.

J3/J4/J5 and the completed small reconciliations are **not reopened**. Origin-only issuance stays closed.

## Verdict

**Return remaining High holes. Do not treat C1/C2 as factory-unambiguous.**

The correction **did** bind the slogans Codex C1/C2 demanded:

| Axis | Slogan closed? | Remaining High joint |
| --- | --- | --- |
| C1 lost-token recovery | **Yes** as a path name (`recover-control` while stopped, no lost token, `local_operator` + journals preserved; `rotate-control` while held) | Empty root vs missing token vs missing principal; recover journal writer vs QMA sole-writer; T-H-03 live daemon without a token cannot reach recover if `stop` needs `host_control`; “daemon stopped” vs `.daemon_writer` present; OS-owner vs Administrators/root |
| C2 origin-revoke vs renew | **Yes** as sequential orderings (renew then `--origin` kills the new proof; `--origin` then renew refuses; `--session` is that `pairing_record_id` only; origin-revoke is not a CAS loser) | `journal_seq` < R vs leftover `issued`/`recorded_at` cutoff; after R, `/pair/confirm` cannot issue vs “all tabs re-pair”; `--origin` has no Origin operand; concurrent two `--origin` (second no-op vs second barrier R2) reopens the in-flight-renew window |

Tests remain unexecuted. Inspect SHA is unchanged. Candidate ≠ operator acceptance. Documentation Factory still waits.

---

## Closures that hold (do not reopen)

Live law, not the as-reviewed packet that required the lost token and discarded a later origin-revoke:

- **C1 path name.** Lost `host_control` is `qmb host recover-control` on a **stopped** daemon by the OS owner of `QMA_DAEMON_ROOT`, **without** presenting the lost token. `local_operator` and journals are preserved. It does not remint a principal. It does not wipe the data root. Live daemon → refuse (stop first). Other OS user → refuse. Readable token file still present → refuse (use `rotate-control`). `rotate-control` remains the live-token path and presents the current token.
- **C1 traces exist.** T-H-01 / T-BE-29 rotate while held. T-H-02 / T-BE-27 lost file + stopped + owning user recover. T-H-03 start after lost file without recover → host-control verbs refuse; pairing proofs still valid until TTL; **no second principal**. T-H-04 / T-BE-28 other OS user refuse; root untouched.
- **C2 sequential orderings.** Renew durable first (`journal_seq` < R) then `--origin` → new proof revoked; origin-revoke is never a no-op loser of that race (T-P-11 / T-BE-30). `--origin` durable first then `/pair/renew` with the old proof → typed refuse (T-P-12 / T-BE-31). `--session` of an already-renewed old id is a recorded no-op; the **new** proof stays live (T-P-13). Confirmed-unconsumed pendings are inside the `--origin` barrier (AD-4).
- **R2 / AD-3.** A remembered Origin never issues. Path 1 is `qmb host pair <code>` then `POST /pair/confirm`. Path 2 is authenticated `POST /pair/renew`. Cookies refused.
- **J3/J4/J5, small reconciliations, Origin-only issuance.** Untouched by this attack.

Inspect honesty remains accurate: `/pair/*`, `qmb host`, `host_control`, `recover-control` are **absent** at `34c148be`. `DaemonWriterLock` is `O_CREAT|O_EXCL` with **no** stale-PID steal (`qma-daemon` `persistence/lock.py`). `DaemonProcess._handle_client` still discards TCP bytes.

---

## Live law (quoted)

Backend AD-17 (lost-token and rotation):

> Trust root is the **OS user who owns `QMA_DAEMON_ROOT`** plus a daemon-minted **`host_control` token** stored under that root with owner-only ACL. … `qmb host start` on an empty root: acquire lock, mint the first operator principal into journal projection **`local_operator`** (AM-03), mint `host_control` … Proof verification for a **running** daemon: QMB must present the current `host_control` token from that root … **Rotation** (token still held): `qmb host rotate-control` presents the current token; daemon mints a new file, journals the new `host_control_fp1`, invalidates the previous fingerprint; `local_operator` unchanged. **Lost-token recovery** (file missing or unreadable): daemon **must be stopped**; the OS user who owns the root runs `qmb host recover-control`. That verb does not present the lost token. It verifies OS ownership of `QMA_DAEMON_ROOT`, mints a new owner-only `host_control` file, journals the new fingerprint and the invalidation of the previous one, and **preserves** `local_operator` and all journals. It does not remint a second principal. It does not delete the data root. If the daemon is live, recover-control refuses (stop first; use rotate-control if the token is still held). If another OS user, refuse. If the token file is still readable, refuse recover-control.

Backend AD-6 (start / empty / sole writer / revoke argv):

> Privileged verbs are `qmb host start|status|stop|pair|configure|rotate-control|recover-control` … They speak the **local host-control** channel (AD-17). `start` sets `QMA_DAEMON_ROOT`, spawns `python -m qma.daemon` if the lock is free, and on an empty root runs first-operator bootstrap. … `qmb host pair revoke --session|--origin` revokes (AD-4). … `rotate-control` and `recover-control` are AD-17. **QMB never writes daemon sqlite.**

Backend AD-4 (barrier):

> **`--session`** revokes that `pairing_record_id` only. **`--origin`** is an administrative barrier: when that event is durable at `journal_seq` R, every `pairing_session` and `pairing_pending` for that Origin with `journal_seq` < R is revoked (including **confirmed-unconsumed** pendings and a **renew that committed earlier**). Origin-revoke is never discarded because a renew appended first. After R, `/pair/renew` with any proof for that Origin refuses; `/pair/confirm` cannot issue. Close matching WS.

HOST-LIFECYCLE recovery / T-H-03 / lock deferral:

> Lost-token recovery — File missing or unreadable. Daemon **stopped**. Owning OS user runs `qmb host recover-control` (**no** lost token presented). …
> T-H-03 — File deleted, daemon restarted (lock free) without recover → host-control verbs refuse until `recover-control`; pairing proofs still valid until TTL; no second principal.
> Reuse `.daemon_writer`. Signal/timeout/stale-PID mechanics are implementation stories; sole-writer and lock-release invariants hold.

PAIRING origin-revoke client column:

> After R, `/pair/renew` and `/pair/confirm` for that Origin refuse | All tabs on that Origin **re-pair**

AM-10:

> Human-gate: running-daemon verbs are operator-only via `host_control`. `recover-control` is OS-owner of a **stopped** root and does not present the lost token.

AM-03 fold contract (inherited QMA AD-6):

> Each fold: stream `noun.verb`, ordering `journal_seq`, knowledge-time `as_of` over `recorded_at`, equal-instant ascending `journal_seq`. Live shape: … single local operator principal plus current `host_control_fp1`.

QMA AD-6 / DEC-0305 (inherited, not amended for recover):

> No process other than the daemon writes the journal, the SQLite file or the artifact store. … `journal_seq` is the single total order in the system.

CLOSURE-C1-C2 rotate row:

> `rotate-control` — Token still held; **daemon live** — Current `host_control` — New file; old `host_control_fp1` dead; same `local_operator`

UI BOOTSTRAP §12 `--origin`:

> Barrier: every session and pending for that Origin with `journal_seq` **before** the revoke, including a renew that committed earlier

`CLOSURE-J1-J5.md` J2 choice (leftover wording, not rewritten in this correction):

> Origin revoke is a journal-ordered cutoff.

AD-4 projection fields still include **issued / expires / revoked**.

---

## C1 — recover-control vs rotate-control vs start-on-empty-root

### Two units

Shared, both units: empty per-user root → `qmb host start` mints `local_operator` + `host_control`; pairing HTTP refuses issue until TTL is configured over host-control; `rotate-control` presents the current token on a **live** daemon and does not change `local_operator`; `recover-control` does not present the lost token and does not wipe journals; T-H-03 start after a **deleted** token file does not remint a second principal; forged `cred://` is not host-control proof; QMB never `import`s the daemon package.

**Unit A — recover is offline file replace; empty = no `local_operator`; stopped = lock absent; stop needs the token; next start journals.**

- **Empty root.** No `local_operator` projection. Missing `host_control` with `local_operator` present is **not** empty: `start` acquires lock if free, does **not** bootstrap, host-control verbs refuse until `recover-control` (T-H-03). First principal is minted **only** by `start` on empty.
- **Rotate vs recover vs start.** Token held + daemon live → `rotate-control` (presents token). Token held + daemon stopped → `start` then `rotate-control` (recover refuses: file still readable). Token missing/unreadable + daemon stopped + `local_operator` present → `recover-control`. Token missing + daemon live → refuse recover; operator must `qmb host stop` (host-control) then recover. Token missing + no `local_operator` → `start` bootstraps (empty).
- **Stopped check.** `recover-control` treats `.daemon_writer` **present** as live and refuses. Inspect `DaemonWriterLock` is `O_CREAT|O_EXCL` with no PID steal; a crash that left the lock is “live.” Stale-PID steal is the deferred **start** story, not recover.
- **OS-owner vs token.** Recover verifies process user SID/uid **equals** directory owner. Administrators/root who can write the tree but do not own it are “other OS user” (T-H-04 / T-BE-28). Rotate/pair/configure still present `host_control` to a running daemon (AD-17 running-daemon proof).
- **Readable.** Any existing regular file named `host_control` is readable → recover refuses. Truncated/garbage/chmod-000-but-present: if `open` succeeds, refuse recover. Fingerprint need not match the journal.
- **Recover writer.** QMB, while the daemon is not running, writes a new owner-only file and a sidecar `host_control.recover-request`. It does **not** append sqlite (AD-6 “QMB never writes daemon sqlite”). The **next** `qmb host start` folds the sidecar, the daemon (sole writer) journals new `host_control_fp1` and invalidates the previous. Between recover and start, the file and the journal disagree; pairing proofs still work on start (T-H-03).
- **Second principal.** Never on recover. Never on T-H-03 start. Only on empty `start`. Two concurrent `start` on empty: lock first-wins (T-BE-22). Two concurrent `recover-control`: first creates the file; second sees readable file → refuse.

**Unit B — recover is a one-shot daemon writer; empty = no journal tree; stopped = lock absent or PID dead; OS-owner may stop without the token; recover mints a first principal if none exists.**

- **Empty root.** No journal / sqlite tree at all. A tree with journals but no `local_operator` is **not** empty, so `start` does not bootstrap. `recover-control` **mints the first** `local_operator` in that case: zero principals exist, so this is not “a second principal.” First principal has two issuers (`start` on a missing tree; `recover-control` on a tree without `local_operator`).
- **Rotate vs recover vs start.** Token held + daemon live → `rotate-control`. Token held + daemon stopped → offline rotate: QMB hashes the file against journaled `host_control_fp1` and the one-shot writer replaces it (CLOSURE “daemon live” is read as “must present the token,” not “8765 must be up”). Token missing + `local_operator` present → `recover-control` whether or not `.daemon_writer` names a dead PID. Token missing + daemon live (T-H-03) → OS owner runs `qmb host stop` **without** presenting `host_control` (token unreadable is the recover trust root; stop is process lifetime, not pair/configure). Then recover. AM-10 “running-daemon verbs are operator-only via `host_control`” is pair/configure/rotate/revoke, not stop-when-token-lost.
- **Stopped check.** Lock absent **or** lock present with `WriterLockToken.pid` not running → stopped. Recover may unlink a stale lock so the one-shot writer can acquire. That is the same predicate the deferred start stale-PID story will need, applied to recover.
- **OS-owner vs token.** Recover succeeds if the process can `open` the root for write (effective access). Windows Administrators / POSIX root can write `%LOCALAPPDATA%\…` / `$HOME/…`. They are not “other OS user.” New `host_control` is owner-only ACL of **the recovering process**. Original user can no longer read the token. Principal is preserved (no second principal). T-BE-28 “steal operator by file create” is read as a stranger **without** write access, not an admin of the box.
- **Readable.** `open` succeeds **and** bytes hash to the current journaled `host_control_fp1`. Truncated, zeros, or mismatch = unreadable → recover allowed even if a file exists. Rotate remains the path only when the hash matches and the daemon is willing to take the presented token.
- **Recover writer.** `qmb host recover-control` spawns `python -m qma.daemon` in a recover mode: acquire `.daemon_writer`, append `host_control.recovered`, write the file, exit. Does not bind 8765, so it is not a “live” daemon for the recover-while-live refuse. QMA AD-6 sole writer is satisfied (the daemon process wrote). Local AD-6 “QMB never writes sqlite” is satisfied. During the one-shot, a concurrent `qmb host start` is a second writer on the same lock.
- **Second principal.** Recover will mint `local_operator` when the fold is empty. A crash after `start` wrote `host_control` but before the `local_operator` append committed: recover sees a readable matching file (or mismatch) and either rotates offline or remints a principal the interrupted `start` was about to mint. T-H-03 does not fire (the file was never “deleted”; the principal was never durable).

### Why both are literal

- **Empty root is unnamed.** AD-6 / AD-17 / HOST say “empty root” and “bootstrap if empty.” AM-03 live shape is “single local operator principal plus current `host_control_fp1`.” T-H-03 forbids reminting when the **file** is deleted and the principal **exists**. None of those sentences say whether empty is “no `local_operator`,” “no `host_control` file,” or “no journal tree.” Unit A takes the AM-03 row. Unit B takes the tree. J1–J5 rubric M-7 already required “Empty root = no operator principal in journal, not token file missing” — that sentence is **not** on AD-17 or HOST. It is a prior review action, not live law.
- **Stopped is unnamed.** AD-17: daemon **must be stopped**. HOST: live daemon → refuse. Inspect lock has no PID check. HOST explicitly parks stale-PID as an implementation story for **start/stop**. It does not say recover uses the same predicate, and it does not say recover uses a different one. Unit A’s lock-absent test is the inspect lock as written. Unit B’s dead-PID test is the deferred supervisor story applied to the recover refuse.
- **Stop-without-token is unnamed, and T-H-03 creates the state.** T-H-03 **requires** that `start` after lost file is legal (daemon live, host-control dead, pairing still valid). Recover then requires stopped. AD-17 running-daemon proof and AM-10 human-gate require `host_control` for running-daemon verbs. `stop` is a running-daemon verb in AD-6. Unit A cannot stop. Unit B carves `stop` out when the token is unreadable, using the same OS-owner trust root recover already uses. Both cite live law. Neither unit remints a principal.
- **Who journals recover while the daemon must be stopped.** AD-17: recover “journals the new fingerprint.” AD-6: QMB never writes daemon sqlite. QMA AD-6: only the daemon writes the journal. CLOSURE-C1-C2: “offline replacement while the daemon is stopped.” All four sentences are live. Unit A delays the journal append until the next start. Unit B runs a one-shot daemon that is not “live” on 8765. A third illegal unit (QMB writes sqlite) is refused by AD-6; these two are not.
- **OS owner vs token are two roots.** AD-17 trust root is **both** OS user **and** token. Running-daemon proof is the token. Recover proof is OS ownership, no token. “Other OS user” is not “user who cannot write” and is not “user whose SID ≠ directory owner.” T-BE-28 forbids steal-by-file-create and does not name Administrators/root. Unit A and Unit B both refuse a random other login; they disagree on the box administrator.
- **Readable is unnamed.** HOST: “File missing or unreadable” / “Readable token file still present → refuse.” Unreadable is the recover path. Readable is the rotate path. Whether “readable” is `open(2)` or “bytes match `host_control_fp1`” is not bound. Corrupt file + stopped daemon: Unit A is stuck (recover refuses, rotate needs a live daemon and a presentable token). Unit B recovers.

### Holes

**H-C1-EMPTY — first principal has two issuers; partial bootstrap is two products.** Unit A’s empty is no `local_operator`; Unit B’s empty is no tree, and recover may mint the first principal. Crash window (`host_control` written, `local_operator` not committed, or the reverse) is start-bootstrap on Unit A and recover-mint on Unit B. T-H-03 only covers “file deleted, principal exists.” The original C1 defect (second operator identity) returns as “first principal minted by recover.”

**H-C1-STOP — T-H-03 is a deadlock on Unit A and an OS-owner stop on Unit B.** Lost token + live daemon is a **specified** state (T-H-03). Recover needs stopped. If `stop` needs `host_control`, QMB cannot reach recover without an unnamed OS kill. If `stop` does not need `host_control` when the file is gone, OS-owner of a **live** root can halt the daemon — a second privileged door next to recover. Both are AD-legal. They do not share a host lifecycle.

**H-C1-WRITER — two owners of the recover journal event.** Unit A: sidecar + next start (file and `host_control_fp1` diverge until start; a T-H-03 start without seeing the sidecar leaves the new file unverified against the old fingerprint). Unit B: one-shot daemon writer (lock held, 8765 down; concurrent `start` is a second writer). Rotate journals through the live daemon (bound). Recover does not.

**H-C1-OWNER — Administrators/root either steal the door or cannot recover a workstation they administer.** Unit A refuses admin recover (directory owner only). Unit B allows it and may rewrite ACL so the original user cannot present `host_control` afterwards — stolen door, same `local_operator`, pairing proofs still valid until TTL (T-H-03 pairing sentence). That is C1’s lost-token problem in another costume: the operator who owned the root no longer holds the token, and rotate is impossible.

**H-C1-READABLE — corrupt `host_control` is stuck or recoverable.** Unit A: any file present → recover refuses. Unit B: hash mismatch → recover. Combined with H-C1-STOP, Unit A’s corrupt+live and corrupt+stopped paths have no named verb.

### Not a High fork (implementation OS API / supervisor story)

Leave as stories, with a **holding refuse** so they cannot become a second product:

| Deferred item | Holding refuse that keeps it a story |
| --- | --- |
| How to *read* directory owner (Windows owner SID vs POSIX `st_uid` vs macOS) | Outcome must be Unit-A-or-bound: recovering process **is** the directory owner, not “can write.” API choice may stay a story. |
| Signal, timeout, and stale-PID steal of `.daemon_writer` for **`qmb host start` / `stop`** after a crash | Sole-writer invariant: at most one live `python -m qma.daemon` per root. Recover **must not** invent a second steal rule; if recover needs the lock gone, `stop` (or a named stale-lock status) is the path. PID reuse / `ESRCH` / Windows `OpenProcess` detail stays a story. |
| Host-control IPC encoding | Token + loopback + not port 8765 + not CT-40. HTTP vs pipe vs drop is already Deferred on the spine. |
| Owner-only ACL encoding (`icacls` / `chmod 600` / macOS) | File is unreadable to other OS users. Exact ACL bytes are a story. |
| Token entropy | Unguessable + RFC 6455 token-safe. Length is a story. |

**Stale lock is a High fork when it is recover’s “daemon stopped” predicate** (H-C1-STOP / Unit A lock-absent vs Unit B PID-dead). It is a story when it is only how `start` reports already-running vs crashed-holder so the operator can start again **after** recover. Do not collapse those.

### Required bind (one sentence each)

1. **Empty root** = no `local_operator` projection (not “token file missing,” not “directory exists”). `start` bootstraps only then. Recover never mints `local_operator`.
2. **T-H-03 exit:** `qmb host stop` on a live daemon with missing/unreadable `host_control` is OS-owner of the root (same trust root as recover), **or** `start` with missing token refuses to spawn so the state cannot occur. Pick one. Today both the state and the stop-needs-token reading are live.
3. **Recover writer:** the daemon process is the sole journal writer; recover may start a one-shot **non-listening** daemon that acquires `.daemon_writer`, appends `host_control.recovered`, writes the file, exits — **or** recover is refused until a named `qmb host start --recover` that does the same. QMB does not write sqlite. Sidecar-until-next-start is forbidden (two sources of `host_control_fp1`).
4. **Stopped** for recover = no live daemon process **and** recover is not itself the listener. `.daemon_writer` present with a dead PID is the start/stop stale-PID **story**, which must run **before** recover if recover requires the lock absent. Recover does not steal the lock while a live PID holds it.
5. **OS owner** = directory owner identity, not effective write. Administrators/root who are not that owner refuse (T-H-04). How to read that identity stays a story.
6. **Readable** = file exists and hashes to current `host_control_fp1`. Missing, unreadable ACL, or hash mismatch → recover (daemon stopped). Hash match → rotate (daemon live) or start-then-rotate (daemon stopped). Never stuck.

---

## C2 — `journal_seq` R barrier vs leftover cutoff; `--session` vs `--origin`; concurrent two origin-revokes

### Two units

Shared, both units: `--session <pairing_record_id>` revokes that record only and does not kill a later renew’s new id (T-P-13). Sequential renew-then-`--origin` revokes the new proof (T-P-11 / T-BE-30). Sequential `--origin`-then-renew with the old proof refuses (T-P-12 / T-BE-31). Confirmed-unconsumed pendings die with `--origin`. Origin-revoke of one race against one renew is not discarded as a first-append loser. Journals never store the raw proof. `--session` never deletes journal history.

**Unit A — mint-seq barrier; Origin permanently barred after R; `--origin` takes one Origin; second `--origin` is a recorded no-op.**

- **What `journal_seq` means on a row.** `pairing_pending` / `pairing_session` store the `journal_seq` of the event that **created** that row (start or renew mint). Fold: revoke every such row for that Origin with create-seq < R. A renew that committed at N < R is revoked. Equal-instant with the revoke is impossible (monotonic `journal_seq`). `issued` / `expires` / `revoked` are display fields; they are **not** the cutoff.
- **After R.** `/pair/start` may still append a pending (PAIRING start preconditions do not mention the barrier). `qmb host pair` may still set `confirmed_at`. `/pair/confirm` **cannot issue** (AD-4 letter, T-P-06). `/pair/renew` with any proof for that Origin refuses. “All tabs re-pair” means drop proofs and use a **different** SPA Origin, or wipe. Same Origin never gets another proof. T-BE-31 “no new proof after explicit origin revoke” is read as Origin-wide, not old-proof-only.
- **`--origin` operand.** `qmb host pair revoke --origin <origin>` (the argv first-pass rubric already recommended). Missing operand is typed refuse. One Origin per event. Origin B is untouched.
- **`--session` vs `--origin`.** `--session` of the new id after renew kills that proof (one record). `--session` of a confirmed-unconsumed pending is typed refuse (no `pairing_record_id` yet). Only `--origin` kills pendings.
- **Concurrent two `--origin` (same Origin).** First append is R1. Second sees Origin already barred → **recorded no-op** (no R2). An in-flight `/pair/renew` that already passed admit and appends at S with R1 < S < (would-have-been R2) is **not** < R1, so the first barrier misses it; the second revoke was discarded; the new proof **lives**. That is the original C2 race against the **second** revoke.
- **Concurrent two `--origin` (two Origins).** Two independent R values. Fine.
- **Leftover `issued_at`.** Ignored. Knowledge-time `as_of` over `recorded_at` (AM-03) is how a reader names a fold instant; the barrier predicate is still create-seq < R, not `issued <= as_of`.

**Unit B — knowledge-time cutoff; after R the Origin can re-pair; `--origin` with no operand is all Origins; every `--origin` appends a new R.**

- **What `journal_seq` means.** AM-03: ordering `journal_seq`, knowledge-time `as_of` over `recorded_at`, equal-instant ascending `journal_seq`. The barrier is a cutoff **instant**. Live pairing rows carry **issued / expires / revoked** (AD-4). `CLOSURE-J1-J5.md` still says “journal-ordered cutoff.” Unit B revokes every `pairing_session` / `pairing_pending` for that Origin with `issued`/`recorded_at` ≤ the revoke event’s `recorded_at`, disposing equal instants by `journal_seq`. A renew that committed first (seq < R) but whose `issued` is 1 ns after the revoke’s `recorded_at` (host-control `recorded_at` stamped at CLI parse, renew `issued` stamped at mint) **survives**. The sequential traces T-P-11/12 still pass on a single-threaded test clock.
- **After R.** Barrier is cutoff of the **past**. PAIRING client: “All tabs on that Origin **re-pair**.” Re-pair is `/pair/start` + `qmb host pair` + `/pair/confirm` of a **new** pending with seq > R. AD-4 “After R, `/pair/confirm` cannot issue” is read as “cannot issue **for rows with journal_seq < R**” (the previous sentence’s scope). T-P-06 “`/pair/confirm` cannot issue” is the confirmed-unconsumed-at-R case, not a permanent Origin death. T-BE-31 is old-proof renew, not a new start.
- **`--origin` operand.** Live argv is `qmb host pair revoke --origin` with **no** Origin (HOST, AM-10, AD-6, UI §12). No operand → every Origin on this daemon. One administrative event, one R, all pairing rows with issued/seq < R die. A second SPA origin on the same daemon dies too.
- **`--session` vs `--origin`.** Same sequential table. `--origin` without an Origin is the only way to kill “this browser” if the operator cannot name the Origin string the daemon stored.
- **Concurrent two `--origin`.** Both append (R1 then R2). Anything minted at S with R1 < S < R2 dies at R2. In-flight renew after the first barrier is killed by the second. A **legal** re-pair that Unit B allowed after R1 is also killed by R2. Two shells, two products: operator who waited for both sees no proof; operator who paired between them briefly had a live proof.
- **Leftover `issued_at`.** This **is** the cutoff. `journal_seq` R is the revoke event’s identity so traces can name R; the **predicate** on rows is issued/recorded_at, because that is what the projection stores and what AM-03 knowledge-time folds.

### Why both are literal

- **AD-4 writes both a seq predicate and an after-R confirm refuse, and PAIRING tells the client to re-pair.** “every … with `journal_seq` < R is revoked” is a cutoff of past rows. “After R, `/pair/confirm` cannot issue” is a future refuse with no “until a new start.” PAIRING client column: “All tabs on that Origin re-pair.” Re-pair **is** `/pair/confirm` after a new start (AD-3 path 1). Unit A takes the refuse. Unit B takes re-pair and scopes the refuse to seq < R. T-P-06 and T-BE-31 do not name a new pending with seq > R.
- **`journal_seq` is not a column on the pairing row.** AM-03 puts `journal_seq` on **events**. AD-4 pairing projections store `pairing_record_id`, Origin, operator principal, `proof_fp1`, **issued/expires/revoked**, pending lineage — not `journal_seq`. “Rows with `journal_seq` < R” is therefore either (Unit A) the create-event seq the fold remembers, or (Unit B) leftover issued/recorded_at cutoff dressed in AM-03 knowledge-time. `CLOSURE-J1-J5.md` was not rewritten in this correction and still says “journal-ordered cutoff.” Historical J1–J5 adversarial Unit A used `issued_at ≤ now`. That is not live law, but the **fields it used are still on the live row**.
- **`--origin` has no Origin in live argv.** HOST / AM-10 / AD-6 / UI §12: `pair revoke --session|--origin`. `--session` takes `<pairing_record_id>`. `--origin` takes nothing. AD-4 / PAIRING speak of “that Origin.” First-pass rubric recommended `--origin <origin>` and was **not** applied to the argv. Unit A adds the operand (only way “that Origin” is identified). Unit B treats the flag as origin-wide for **all** Origins (only way the live argv is complete).
- **Second `--origin` is unspecified.** Sequential C2 only names one revoke vs one renew. “Origin-revoke is never discarded because a renew appended first” does not say a **second** origin-revoke is never discarded because the Origin is already barred. Recorded no-op is how `--session` of an already-rotated id works (PAIRING). Unit A copies that pattern. Unit B always appends a barrier (the C2 slogan “never a no-op loser”). An in-flight renew admitted before R1 and appended after R1 is the original C2 bug unless R2 exists.

### Sequential slogans that do **not** fork

These are unique in live law. Do not spend the gate on them:

| Ordering | Outcome | Evidence |
| --- | --- | --- |
| Renew commits, then one `--origin` | New proof revoked; WS closed | AD-4; PAIRING; T-P-11; T-BE-30 |
| One `--origin` commits, then `/pair/renew` with the **old** proof | Typed refuse | PAIRING; T-P-12; T-BE-31 |
| Renew, then `--session` of the **old** id | New proof stays live | PAIRING; T-P-13 |
| `--session` of a live id | That record only; its WS closed | AD-4; HOST |

### Holes

**H-C2-AFTER-R — same Origin either never pairs again or re-pairs on a new pending.** Unit A: `/pair/confirm` after R is a permanent refuse; PAIRING “re-pair” is a different Origin or a wipe. Unit B: new start+confirm after R is the re-pair path. A factory that ships both cannot share a pairing table: one treats post-R confirm as `POLICY_REJECTION`, the other mints a proof. This is the remaining C2 product fork. The sequential renew/revoke traces do not touch it.

**H-C2-PRED — barrier predicate is create-seq < R or leftover issued/`recorded_at` ≤ cutoff.** AD-4 names `journal_seq` < R but does not store `journal_seq` on the row; it **does** store `issued`. AM-03 knowledge-time and the unrewritten CLOSURE-J1-J5 “cutoff” sentence license Unit B. A renew that committed first can survive Unit B under clock skew between CLI `recorded_at` and mint `issued` — the exact C2 failure mode, now on timestamps instead of first-append-wins. Unit A is immune. Equal-instant disposition (AM-03) only helps Unit B when `recorded_at` is **equal**; it does not help when issued is **after**.

**H-C2-ARGV — `--origin` either names one Origin or kills every Origin.** Live argv has no operand. “That Origin” is unbound. Unit A’s daemon and Unit B’s daemon disagree on whether a second SPA origin (second tab on a different static port is a different Origin; AD-3 still requires a fresh QMB confirm) survives an origin-revoke aimed at the first.

**H-C2-R2 — concurrent two origin-revokes reopen the in-flight renew window on Unit A.** First barrier R1. Second discarded as already-barred. Renew admitted before R1, appended at S > R1: not revoked. Unit B’s R2 kills it. C2’s slogan “never discarded because a renew appended first” is about **one** revoke losing to **one** renew. Two revokes were not traced. T-BE-30 is sequential.

### Not a High fork

- `--session` vs `--origin` **scope slogans** (one record vs Origin barrier; old id after renew is no-op). Closed.
- Confirm-once / `already_issued` / lost confirm → re-pair. Closed under J2; not C2.
- WS close on expiry/revoke/rotate. Closed.
- Proof entropy; whether `already_issued` JSON includes `pairing_record_id`.
- How Origin **string** is canonicalized (trailing slash, default port) **once** `--origin` takes a single Origin operand. Canonicalization is a story; missing operand is High (H-C2-ARGV).

### Required bind (one sentence each)

1. **Predicate:** origin-revoke at event seq R revokes pairing rows for that Origin whose **create/renew event** `journal_seq` < R. Do not cut on `issued` / `recorded_at`. Store that create-seq on the projection or fold it from the stream; do not leave “row.journal_seq” unnamed next to an `issued` field.
2. **After R:** either (i) that Origin is barred until a named `qmb host pair unbar --origin` (or wipe), and PAIRING “re-pair” is rewritten to “drop proofs; new Origin or unbar,” **or** (ii) a **new** `/pair/start` after R is a new pending with seq > R and `/pair/confirm` **may** issue after a fresh QMB pair, and AD-4 “After R, `/pair/confirm` cannot issue” is rewritten to “cannot issue for rows with seq < R.” Pick one. Today both sentences are live.
3. **`--origin` argv:** `qmb host pair revoke --origin <origin>` (one Origin). Missing operand refuses. Not all-Origins.
4. **Second `--origin`:** always appends a new barrier R2 (never a no-op). In-flight renew/confirm with R1 < seq < R2 dies. Same as C2’s “never discarded” slogan applied to the later revoke.
5. **Traces:** add T-P-14 / T-BE-32 concurrent two `--origin` plus in-flight renew; T-P-15 / T-BE-33 `/pair/start` + confirm **after** R on the **same** Origin (issue or refuse, matching bind 2).

---

## Cross-cuts the correction did close (credit)

- Lost `host_control` no longer requires presenting the lost token. Rotate and recover are **named** as different verbs. That is the C1 slogan Codex asked for.
- Sequential renew vs one origin-revoke is no longer “no-op or typed refuse.” That is the C2 slogan Codex asked for.
- `--session` is not an Origin cutoff. Confirmed-unconsumed pendings are in the `--origin` set. `local_operator` is on AM-03. Pairing TTL remains host-control exclusive.

Those slogans are not enough for two stories to share a daemon.

---

## Honesty

No live daemon. Tests unexecuted. Inspect `DaemonWriterLock` still has no stale-PID steal. Candidate ≠ operator acceptance. This file does not edit historical `reviews/`. It does not implement. It does not run Documentation Factory or rewrite epics.
