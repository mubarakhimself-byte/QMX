---
title: What goes before anything is added
type: grilling
mode: AFK
status: closed
blocked_by: [saved-set-by-class, one-rclone-runner, one-place-list]
claimed_by: ""
created: 2026-10-28
closed: 2026-10-28
resolved_by: map agent (stand-in)
---

## Question

What is removed or merged before the sync's additions land, and what keeps each removal safe?

## Resolution

Accept `align:` D items 1 to 9, in this order, before any addition. Line counts are at `1e9f695a`.

| # | Goes or merges | Safe because |
|---|---|---|
| 1 | **The weekly GitHub snapshot**: `QX/backup.py` (198 lines, confirmed), its command, route, template `backup-weekly/` and catalog row, and its test | Everything it copies is in the sync's saved set (`explore:` 4). It installs disabled and nothing runs it. An old `repository` key under the settings section is ignored, not refused |
| 2 | **The mini-app volume backup**: `PK/qmx-apps/src/qmx_apps/backup.py` (196) and `backup_schedule.py` (51, confirmed), their wiring and routes, `APP_KEYS` | App data is already in every copy (`BK/snapshot.py:52-53`). **First:** each app's `data/` is copied under the app's lease, as the volume backup does (`backup.py:135-142`). "Restore one app" goes to the backlog. Litestream for container apps stays |
| 3 | **`[remote]` and `RemoteSettings`** | No reader (searched this session: only `QX/service.py:842`). The settings writer keeps unknown sections word for word |
| 4 | **The node rebuild's own rclone runner** (`QX/node.py:470-475`), onto the one runner | Its callers read only the exit code |
| 5 | **Three free-space floors into one** | The 1 GiB minimum still guards a pre-change copy |
| 6 | **The fixed hourly copy** becomes a setting with an off switch | The doctor row says so when no copy exists anywhere |
| 7 | **Plan text for planned PRs 6 and 7** (`plan:351-459`), replaced by the sync design. PR 7 goes to the backlog | No built code depends on it. `BK/round.py`'s `sealed_keys` hook goes with it |
| 8 | **The designed `cache/backup-send/` hard-link tree** | Never built; packs replace it |
| 9 | **The old bundle installer** `release/install.py` (480) and `release/launcher.py` (26), which launch `qmb` | Nothing outside `release/` names them (`align:` D). The install sequence is redesigned, and these would mislead the installer's builder |

About 700 lines of code and templates and about 230 lines of tests go in items 1 to 6, plus 506 lines with item 9.

**Kept on purpose:**

- the second-drive proposal (now a suggestion in the storage dialog);
- the status ladder (it gets its first caller);
- the trading node's backup and QMF's backup block (another machine, another job);
- the Hub's bucket push (the server's own).

## Evidence

R118, the later ruling that wins over R115's "nothing built in merged code is removed": "Anything may be refactored, overhauled, or deleted and rebuilt ... as long as the result works". Principle subtract-before-you-add. His words: "efficiency, again, dude, we don't need eight PRs" (`words:219`).
