# The backup program: what is built, what it costs in disk, and what it overlaps

Read on 2026-10-28 from branch `build/br4` at `1e9f695a` (backup PRs 1 to 4). Nothing was run. No real QMX folder, server or key store was opened.

Where the references point:

- Code paths are inside `D:/QMX-worktrees/bld-br4/`. Short names: `home/backup/` is `qmx-agents/packages/qmx-home/src/qmx_home/backup/`, `host/` is `qmx-agents/packages/qmx-host/src/qmx_host/`, `control/` is `qmx-agents/packages/qmx-control/src/qmx_control/`.
- `plan:` is `D:/QMX-worktrees/agent-system/tracker/qma-v2/BACKUP-RESTORE-PLAN.md`.
- `design:` is `D:/QMX-worktrees/agent-system/tracker/qma-v2/research/methodology/62-local-first-design.md`.

## 1. Settings: what you can change today

The screen saves backup settings through one call, `PUT /api/settings/backup` (`control/service.py:796-800`). Before it saves, it checks the whole section with the backup program's own reader and refuses a bad row by name (`control/service.py:872-882`, `:285-297`). The host reads the settings again every minute, so a change applies within a minute (`host/backups.py:74`, `:261-262`).

**What you can change through that call:**

- **How long the quick undo keeps copies.** It keeps the newest 48 hours and then one copy a day for 7 days. Both numbers can be changed (`home/backup/plan.py:82`, `:139-141`).
- **Each backup place.** Each place has a name, a folder path, how often (every hour, day or week), what time (such as 03:00), keep counts (daily, weekly, monthly; 14, 8 and 12 by default) and an on/off switch (`home/backup/plan.py:64`, `:86-94`, `:149-194`).
- **What to leave out.** A list of paths inside your data, such as `exports/**` (`home/backup/plan.py:225-236`).
- **The monthly test restore (the "drill").** You can set how often it runs and how many files it checks (`home/backup/plan.py:239-248`). The setting is saved, but nothing runs the drill yet. The host service never calls it (`host/backups.py` has no drill; the code waits in `home/backup/restore.py:427`). Running it on a schedule is backup PR 5 (plan:299).
- **Accepting the suggested second drive.** This is one button that calls `POST /api/backups/targets/default/accept`. It writes one place row (`host/backups.py:531-566`, `:654-656`).
- **The free space QMX always leaves on the drive.** This is `disk.floor_gb` in the engine settings (`host/disk.py:26`, `:55-62`, read at `host/host.py:752`).

**What is fixed in code:**

- **The quick undo runs every hour and cannot be turned off.** The hourly timing is written into the code (`host/backups.py:273`). Its settings allow only `hours` and `days`, with no on/off switch and no interval (`home/backup/plan.py:140`). The plan calls it "always on" on purpose (plan:513). So there is no master switch: turning every place off still leaves the hourly copy running.
- **The quick undo's folder** is always `backups/quick` inside the QMX folder (`home/backup/round.py:39`).
- **Retry and warning timing.** A refused place is tried again after 1 hour (`host/backups.py:77`). An unplugged disk raises a warning after 7 missed intervals (`host/backups.py:79`).
- **Copies taken before an upgrade, and each store's own pre-change copy,** are held until a copy to another drive is 30 days old (`home/backup/keep.py:16`).
- **Free-space minimums.** At least 1 GB always stays free (`qmx-home/src/qmx_home/versions.py:39`). The suggested drive must keep a tenth of itself free (`home/backup/plan.py:56`).
- **The drill's timing** can only be weekly or monthly (`home/backup/plan.py:244`).

**What breaks your rule that anything configurable is editable in the screen:**

- The quick undo's hourly timing and its on/off.
- The 1-hour retry, the 7-interval warning and the 30-day hold.
- Default values the screen cannot see. The defaults live only in code. `GET /api/backups` sends each place's timing and on/off but not its keep counts, leave-out list or drill settings (`host/backups.py:666-690`). Until a row is saved, the settings file holds nothing, so the screen has to repeat the defaults (48/7 and 14/8/12) or show blanks.

## 2. Disk space

**Each file is stored once, by its fingerprint (its hash).** Each place keeps a "pool" that holds each file once by its hash, plus a list for each copy (`home/backup/repository.py:1-7`). A file whose size and save time have not changed is not read again (`home/backup/snapshot.py:9-12`). A round where nothing changed writes nothing new to the quick undo (`home/backup/round.py:265-268`).

**The quick undo does not copy your big files.** Files that are written once and never changed stay where they are, and the copy only names them. These are Library objects, saved files and finished price months (`home/backup/snapshot.py:81-89`, `:177-180`). Only files that change go into the quick undo's pool: the databases, the logs and the current price month.

**But a changed database is copied whole every time.** A database that changed is saved again in full (`home/backup/snapshot.py:9-10`). A log that grew is also saved again in full. Copying only the new part is not built (plan:485). So the quick undo grows by the size of the databases that changed each hour, up to about 55 kept copies (48 hourly plus 7 daily).

**What thins it:** after each new copy, the keep rule drops old copies. Then a sweep removes pool files that no kept copy names (`home/backup/round.py:252-254`, `:536-555`).

**What stops it filling the drive:** a copy refuses before writing anything if it would leave the drive with less than a minimum of free space (`home/backup/snapshot.py:188-195`). That minimum is the larger of 1 GB and the host's minimum (`home/backup/round.py:229`). The host's minimum is one twentieth of the free space when the host started, unless you set `disk.floor_gb` (`host/disk.py:55-62`). On D: with 58 GB free, that is about 2.9 GB. The host measures it again at each start, so it shrinks as D: fills up. There is no size limit on the quick undo itself.

**A rough estimate for a QMX folder of a few GB:**

- The first quick copy holds the files that change, perhaps 0.1 to 0.5 GB.
- After that, the worst case is about 55 times the size of the databases that change every hour.
  - Busy databases of 50 MB make about 3 GB.
  - Busy databases of 200 MB make about 11 GB.
- An hour with no work adds nothing.
- Without a second drive, every copy taken before an upgrade, and every store's pre-change copy, is kept forever. They are only released 30 days after a copy to another drive (`home/backup/keep.py:57-61`, `home/backup/round.py:545-548`, `:561-579`).
- A second drive's first copy is the whole folder (a few GB). After that it adds only the files that changed, once a day, with up to 34 copies kept.

**About C: as the second drive:**

- QMX will not suggest C:. It needs the free space left after the copy to be at least a tenth of the drive, which is 32 GB on C:, and C: has 17 GB free (`home/backup/plan.py:318-321`).
- You can still name C: yourself. A named place has no free-space minimum. The copy only checks that it fits (`home/backup/round.py:348-355`), so it could fill your system drive.

## 3. The server

It cannot be a backup place yet. Today the only kind of place is a folder (`home/backup/plan.py:45-48`), and any other kind is refused (`:161-163`). The design lists a server as an optional off-site place (design:243, design:283). The plan sends off-site copies through rclone in backup PR 6, which is not built (plan:351-353). rclone can reach a server over SSH, so the server becomes a place once PR 6 lands. Off-site copies do not check free space; the server's own 100 GB is the only limit (plan:353).

There is one workaround, not tested: a folder place accepts any full path whose drive exists (`home/backup/round.py:320-324`). If Windows had the server mounted as a network drive, it might work, but nothing builds, plans or tests that. Backing up a QMX folder that lives on the server is out of scope (plan:487).

## 4. Overlap with other backup pieces

| Piece | What it does | Overlap |
|---|---|---|
| Weekly GitHub snapshot (`control/backup.py:1`, `:25-33`, `:60-198`; template `qmx-engine/.../templates/backup-weekly/README.md`) | Every Monday, copies the small databases and the Library's files to a private Git repository. | Yes. Everything it copies is also in the new program's copies. The plan keeps it as it is for now and logs its reshape for later (plan:484). It becomes the "GitHub weekly" off-site place in the design (design:243). |
| Mini-app volume backup (`qmx-apps/.../backup.py:26-39`, `:122-165`; `backup_schedule.py:27-41`) | Copies each mini app's data to an rclone remote, nightly by default. | Yes. The new program also copies the mini apps' data folders. It leaves out only heartbeats and temporary files (`home/backup/snapshot.py:52-53`). Both use the same `[backup]` settings section (`home/backup/plan.py:49-53`). Once PR 6 lands, there are two rclone paths. Merge them then. One gap: copying an app's data while holding the app's lock is only logged for later (plan:485). |
| Litestream for container apps (`qmx-apps/.../docker.py:280-307`, `control/service.py:1603-1605`) | Copies container apps' databases continuously, as live replicas, for the server's app tier. | No. It is a live copy on another tier, not a dated copy you can go back to. |
| Pre-change copy before an upgrade (`qmx-home/src/qmx_home/versions.py:235-302`) | Copies the one database an upgrade changes. | Joined in. The new program now thins these copies (`home/backup/round.py:561-579`). |
| Library migration freeze (`qmx-library/.../migrate/snapshot.py:1-8`) | A one-off copy before an import. | No. |
| Library sync to the server (`host/host.py:813-815`) | Sync between the PC and the server. | No. Sync is not a backup, and the design lists the server copy separately (design:243). |
| Trading node nightly backup (`qmn/src/qmn/data/backup_run.py:1-7`, `:88-96`; timer `qmn/deploy/systemd/templates/qmn-backup.timer`; full and sample restore timers) | Runs on the trading server. Sends the trading node's own records, encrypted, through rclone to a Backblaze bucket. The real bucket is still turned off (`qmn/src/qmn/data/backup.py:95`). | No. It covers another machine and other data. The only shared part is the method (rclone, test restores). |
| QMF backup building block (`packages/qmf-data/src/qmf/data/backup.py:1-25`) | The encrypted copy and restore code the trading node builds on. | No. The new program does not use it and needs only Python's built-in library (`home/backup/__init__.py:1-2`). |
| Database dumps | No dump exists in the code. A dump of the memory database is only logged for later (plan:485). The memory database is left out of copies and rebuilt (`home/backup/snapshot.py:40`). Backup PR 5, not built, does the rebuild (plan:299). Until then, a restore would leave memory recall empty. | — |

What I would merge: fold the mini-app volume backup into the new program's off-site places when PR 6 lands. Turn the GitHub snapshot into a GitHub place, as the design says. Leave the trading node's backup alone.

## 5. Trading node, QMF and the "open" layer

- **The trading node (QMN)** is the trading server's main program, with no command line (`qmn/pyproject.toml:4`). It has its own nightly backup and restore tests (section 4). The backup work changed no file in it (`git diff --stat 6260fe1d 1e9f695a`).
- **QMF** is a set of base packages: money and time types, data rooms, the holdout seal, journals and backup building blocks (`packages/qmf-data/pyproject.toml:4`, `packages/qmf-core/pyproject.toml:4`). Backup PR 3 changed one QMF file, the price store. A save in the price store now retries a file rename while a backup is reading that file. It waits at most about 1.3 seconds in all before reporting a storage failure (`packages/qmf-data/src/qmf/data/series.py:107-108`, `:166-178`; commit `3950ce59`). This file is not in the plan's file list for PR 3 (plan:192-198). The risk is a slow read of a large current price month taking longer than that wait, which would make a price save fail. Nobody has measured it.
- **The "open" layer is OpenObserve plus OpenTelemetry.** None of OpenTofu, OpenBao or OpenSearch appears in the code.
  - OpenObserve stores the deep logs. On the server it keeps its data in `/srv/qmx/monitoring/openobserve`, outside the QMX folder. It keeps a short window, and the Library keeps every run's trace and logs, so the viewer can be rebuilt (`qmx-host/deploy/openobserve.service:3-7`, `:30`).
  - The OpenTelemetry collector on the server keeps a disk queue so no record is lost while OpenObserve restarts (`qmx-host/deploy/otelcol.service:3-5`, `otelcol.yaml:58-59`).
  - On this PC, monitoring is off by default (`qma-harness/src/qma/telemetry.py:1-6`). The plan puts a PC copy of OpenObserve in `cache/`, not in your data (design:347). The backup copies only your data folder, so OpenObserve's data is never copied.
  - The trading node has its own monitoring stack (Prometheus, Loki, Grafana) that keeps 15 days of metrics in `/var/lib/qmx-observability` (`qmn/deploy/observability/compose.yml:1-5`, `:26-27`).
- **Does monitoring need a backup?** No plan backs it up, and by design none is needed: it is a viewer of records the Library already keeps (design:347; `openobserve.service:3-5`). The backup program does not touch it and does not copy it.

## 6. Was seven PRs the right size?

What PRs 1 to 4 changed:

| PR | What it does, in plain words | Code | Tests |
|---|---|---|---|
| 1 | Copies of the folder on this PC and on a second drive. Settings reader, keep rule, pool, one round. Moved the copy helpers into a shared file. | 11 files, +2,377 / −146 | 7 files, +1,120 |
| 2 | Restore: list copies, show what a restore replaces, build it to the side, swap it in, survive a crash mid-way, the drill. | 3 files, +1,284 (`restore.py` alone is 1,262 lines) | 3 files, +1,055 |
| 3 | The host makes copies by itself every minute it checks. Warnings, a health row, web routes, `python -m qmx_host backup`, the settings check, and the price-store retry. | 5 files, +861 | 4 files, +827 |
| 4 | Restore from the start screen and from `python -m qmx_host restore`. A copy before each upgrade. | 4 files, +612 / −66 | 5 files, +806 |

Line counts come from `git diff --shortstat` between `6260fe1d`, `7b046b8a`, `0579a45e`, `db9cea7f`, `0ee50e42` and `1e9f695a`. Altogether that is 35 files, +8,935 / −236.

Not built yet:

- PR 5: restore from Settings, a safe first start after a restore, and the scheduled drill (plan:297-301).
- PR 6: off-site copies through rclone. One new module plus a settings change (plan:351-361).
- PR 7: lock your keys into the copies with a passphrase (plan:405-418).

My view: the four built PRs are each 600 to 2,400 lines of code, which is already large. Splitting them further would not have helped. PRs 5 to 7 could be fewer:

- PR 5 changes the same two files as PR 3 (plan:498-499).
- PR 7 changes the same files as PRs 4 and 5 (plan:502-503).
- PR 6 is small and stands alone.

A five-PR cut would have done: copies, restore, host plus start screen, restore from Settings plus keys, off-site. The bigger cost per PR is checking it, not its size: every PR needs ten live test lanes plus a speed check (plan:100-122).
