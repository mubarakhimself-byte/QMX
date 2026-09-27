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
| Recovery | Same OS user, same root, start: `local_operator` remains. Lost `host_control` file refuses until `qmb host rotate-control` from a still-valid token (do not remint a second principal) |
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

## Verbs

| Verb | Does | Does not |
| --- | --- | --- |
| `qmb host start` | Set `QMA_DAEMON_ROOT`; spawn if lock free; bootstrap if empty | Orchestrate Missions; grant; start QMN; spawn from the browser |
| `qmb host status` | Lock, pid, bind, operator-established, TTL set/unset, pending/bound **record ids** | Print proofs, codes, host_control, Credential Manager secrets |
| `qmb host stop` | Stop **local** daemon; release lock | Cancel QMN/remote |
| `qmb host configure pairing-ttl` | Write registry row via daemon (sole writer) | Invent a duration |
| `qmb host pair <code>` | Confirm that pending over host-control | Issue the browser proof; write sqlite from QMB |
| `qmb host pair revoke --session <pairing_record_id>` / `--origin` | `revoke_pair` via host-control; close WS | Delete journal history |
| `qmb host rotate-control` | New host_control token | Change operator principal |

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
