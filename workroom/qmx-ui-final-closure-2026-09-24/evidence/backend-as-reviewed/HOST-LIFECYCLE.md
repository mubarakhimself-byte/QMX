---
name: QMB host lifecycle
sitting: architecture-QMX-UI-BACKEND-2026-09-24
inspect: 34c148be
status: candidate
closes: joint-review J1
---

# QMB host lifecycle

COMP-QMB is the privileged process door (parent AD-21). Local **host-control** is the first-operator trust root (AD-17). Absent at inspect: no `host` group.

## Trust root (J1)

| Piece | Rule |
| --- | --- |
| Owner | OS user of `QMA_DAEMON_ROOT` |
| Token | Daemon-minted `host_control` file under that root, owner-only ACL |
| Channel | Loopback only. **Not** CT-40. **Not** `/pair/*`. **Not** a provider `cred://` |
| Verification | QMB presents the current token. Shape of a `credential_ref` or a caller-chosen `principal_class` is **not** proof |
| First start (empty root) | Spawn daemon, acquire `.daemon_writer`, mint operator principal into journal projection **`local_operator`** (AM-03), mint `host_control`. `/pair/start` and `/pair/confirm` refuse until TTL is configured |
| Configure TTL | `qmb host configure pairing-ttl <duration>` over host-control. **Only** this verb may write `registry:pairing.session_ttl`. CT-40 `variable.set` of that key refuses. Operator supplies the duration. No number minted here |
| Rotation | Token still held. `qmb host rotate-control` presents the current token. New file; previous `host_control_fp1` invalidated; `local_operator` unchanged |
| Lost-token recovery | File missing or unreadable. Daemon **stopped** (no live pid holding `.daemon_writer`). Owning OS user runs `qmb host recover-control` (**no** lost token presented). QMB does not write sqlite: a one-shot daemon recover entry acquires the lock, appends `host_control_fp1`, exits without binding 8765. New owner-only file; previous fingerprint invalidated; `local_operator` and journals **preserved**. Does not remint a principal. Does not delete the data root. Live daemon → OS owner may `stop` without the token (file missing), then recover. Other OS user → refuse. Readable token file still present → refuse (use rotate-control). Missing token + existing `local_operator` is **not** empty-root bootstrap |
| Remote host | SSH (or equivalent) to that machine and run `qmb host` **there**. The laptop browser never bootstraps a remote operator |

### Clean-install trace

1. `qmb host start` (empty per-user root) → operator principal + host_control.
2. `qmb host configure pairing-ttl` → registry row set.
3. Browser POST `/pair/start` → code.
4. `qmb host pair <code>` (host-control) → pending confirmed.
5. Browser POST `/pair/confirm` → `pairing_proof` once.
6. `initialize`.

### Negative traces

| Caller | Result |
| --- | --- |
| Forged `cred://models/…` / `cred://telemetry/…` as operator login | `CredentialOutOfScope` / refuse. Allowlist not widened |
| Unauthorized local user (cannot read `host_control`) | refuse pair/configure |
| Remote caller without host_control | refuse |
| `/pair/confirm` before TTL set | refuse issue |
| Lost `host_control` + live daemon + `rotate-control` | refuse (no token to present). OS owner `stop` (file missing), then `recover-control` |
| Lost `host_control` + `recover-control` while daemon live | refuse. Stop first |
| Other OS user + `recover-control` on stopped daemon | refuse. `local_operator` and journals unchanged |
| `recover-control` while token file still readable | refuse. Use `rotate-control` |

### Recovery traces (unexecuted)

| ID | Intent |
| --- | --- |
| T-H-01 | Token held, `rotate-control` → new file, old `host_control_fp1` dead, same `local_operator`, journals intact |
| T-H-02 | File deleted, daemon stopped, owning OS user `recover-control` → new file, old fingerprint dead, same `local_operator`, journals intact; then `start` |
| T-H-03 | File deleted, daemon restarted (lock free) without recover → host-control verbs refuse until `recover-control`; pairing proofs still valid until TTL; no second principal |
| T-H-04 | Other OS user `recover-control` → refuse; data root untouched |

## Verbs

| Verb | Does | Does not |
| --- | --- | --- |
| `qmb host start` | Set `QMA_DAEMON_ROOT`; spawn if lock free; bootstrap **only** if no `local_operator` row | Orchestrate Missions; grant; start QMN; spawn from the browser; remint principal when token is missing |
| `qmb host status` | Lock, pid, bind, operator-established, TTL set/unset, pending/bound **record ids** | Print proofs, codes, host_control, Credential Manager secrets |
| `qmb host stop` | Stop **local** daemon; release lock. Auth: current token **or** (file missing/unreadable **and** OS owner of the root) | Cancel QMN/remote |
| `qmb host configure pairing-ttl` | Write registry row via daemon (sole writer) | Invent a duration |
| `qmb host pair <code>` | Confirm that pending over host-control | Issue the browser proof; write sqlite from QMB |
| `qmb host pair revoke --session <pairing_record_id>` | Revoke that record only; close its WS | Origin-wide cutoff; delete journal history |
| `qmb host pair revoke --origin <origin>` | Origin barrier (AD-4) for that static Origin: revoke every session and pending with `journal_seq` < R, including a renew that committed earlier | Discard the revoke because a renew appended first; revoke every Origin; delete journal history |
| `qmb host rotate-control` | New `host_control` while token is held | Change `local_operator`; recover a lost file |
| `qmb host recover-control` | Stopped daemon; OS owner of the root; lost/unreadable file; one-shot daemon journal write; new token without presenting the old one | Run against a live daemon; remint principal; wipe journals; QMB sqlite write; bind 8765 |

Until these exist, UI Start local is the documented recipe (still not a browser spawn). Pairing cannot complete until a product `qmb host` or an equivalent local-control implementation exists — the UI must not fake a paired session.

## Data root and lock

| OS | `QMA_DAEMON_ROOT` |
| --- | --- |
| Windows | `%LOCALAPPDATA%\QMX\qma-daemon` |
| Linux | `${XDG_STATE_HOME:-$HOME/.local/state}/qmx/qma-daemon` |
| macOS | `~/Library/Application Support/QMX/qma-daemon` |

Inspect cwd-relative `"qma-daemon-data"` is not the product root. Reuse `.daemon_writer`. Signal/timeout/stale-PID mechanics are implementation stories; sole-writer and lock-release invariants hold.

## Placement

v1 local workstation. Recorded remote is a different daemon origin (HTTPS/WSS) with **its own** operator principal and pairing table, bootstrapped by `qmb host` **on that host**. Local stop does not stop remote. Remote failure never retargets loopback.
