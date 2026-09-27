---
name: QMB host lifecycle
sitting: architecture-QMX-UI-BACKEND-2026-09-24
inspect: 34c148be
status: candidate
---

# QMB host lifecycle

COMP-QMB is the privileged process door (parent AD-21, UI AD-19, local AD-6). Absent at inspect: `COMMAND_GROUPS` has no `host`.

## Verbs

| Verb | Does | Does not |
| --- | --- | --- |
| `qmb host start` | Set `QMA_DAEMON_ROOT` to the per-user path; spawn `python -m qma.daemon` if `.daemon_writer` free; wait until bind or already-running | Orchestrate Missions; grant; start QMN; spawn from the browser |
| `qmb host status` | Lock, pid, bind, pairing pending/bound origins (id presence only) | Enumerate Credential Manager; paint SPA `starting` |
| `qmb host stop` | Stop the **local** daemon; release lock | Cancel QMN/remote; `JobHandle.cancel` for every job (local handles may become `unknown`) |
| `qmb host pair <code>` | Operator-principal addable command `confirm_pair` (existing wire + operator `credential_ref`). Copies that ref onto the pending row. Page still POSTs `/pair/confirm` to collect the token. | Write daemon sqlite from QMB; issue the browser token; accept a provider secret; auto-approve a second tab |
| `qmb host pair revoke --session <id>` / `--origin <origin>` | Operator-principal `revoke_pair`; set `revoked_at`; close WS bound to that id | Delete journal history |

Until these exist, UI Start local is the documented recipe:

```text
set QMA_DAEMON_ROOT=%LOCALAPPDATA%\QMX\qma-daemon
python -m qma.daemon
```

That recipe is operator setup, not a product CLI, and not a browser action.

## Data root and lock

| OS | `QMA_DAEMON_ROOT` |
| --- | --- |
| Windows | `%LOCALAPPDATA%\QMX\qma-daemon` |
| Linux | `${XDG_STATE_HOME:-$HOME/.local/state}/qmx/qma-daemon` |
| macOS | `~/Library/Application Support/QMX/qma-daemon` |

Inspect `__main__.py` cwd-relative `"qma-daemon-data"` is **not** the shipped product root. Reuse `DaemonWriterLock` `.daemon_writer` (`O_CREAT|O_EXCL`). Stale lock with a dead pid is QMB/daemon recovery.

## Failure

| Case | Result |
| --- | --- |
| Second start, live pid | status already-running; no second sqlite writer |
| Bind collision 8765 | typed OSError, distinct from lock refusal |
| Stop while jobs run | local handles may go `unknown`; operator resolves; remote/QMN continue |
| Laptop sleep | no lid-closed continuation promise (GAP-0062) |

## Placement

v1 local workstation. Recorded remote is a different daemon origin (HTTPS/WSS) with **its own** pairing table. Local stop does not stop remote. Remote failure never retargets loopback.

Tauri later **calls** these verbs. It is not a second owner.
