---
label: wayfinder:map
title: Sync to my storage, and connect from the screen
created: 2026-10-28
charted_by: map agent for the wrap-up coordinator (charted and stand-in resolved in one session, per the coordinator's brief)
---

# Sync to my storage, and connect from the screen

## Destination

A small, decided design with nothing left to decide before an architect writes it and a planner cuts it into the fewest PRs the code needs. It covers four things:

1. "Sync to my storage": one switch, copies by class, packs with compression, a monthly re-pack and check as QMX's own maintenance, a sync before every update, any storage through rclone.
2. Connecting compute, storage and OpenObserve on any machine through one step-by-step dialog or the copilot.
3. The step sequences that install, first start and update show.
4. The UI-HANDOFF section 26 backend gaps that belong here.

It builds on backup PRs 225 to 229 and everything under them, and it subtracts first.

## Notes

- **Planning only.** Decisions, not code. Build PRs are not tickets.
- **Inputs.** `../research/sync/` 00 to 04 (his words tonight, the inventory, 123 primary sources, the alignment ledger) and rulings 105 to 145 in `../research/methodology/26-operator-rulings-and-alignment.md`, the latest winning. Also `../UI-HANDOFF.md` §26 and the last section of `D:/QMX-worktrees/qma-ship/wrapup/QUEUE.md`. The code is `build/br4` at `1e9f695a` (225 to 228) and `build/br5` at `1e5aaabd` (229); the evidence shorthand is in `README.md`.
- **Skills to consult.** `codebase-design` (deep modules: the class table, the `Repository` seam, the connect steps), `domain-modeling` (the words in `../research/sync/04-alignment-and-domain.md` §B), `principle-subtract-before-you-add` (the subtract list lands first), and `blast-radius` before the plan is cut (the QMF price-store retry, the first-start card, the `[engine]` settings readers).
- **His standing preferences.**
  - No QMX caps (R106); a floor that protects his drives is not a cap.
  - The PC is home, and servers substitute (R136, R140, R142).
  - Design for complexity, not a complex system (R115, R118).
  - Configurable means editable in the UI, with every default visible.
  - Plain words and no codenames in anything he reads.
- **Domain in one line.** QMX saves the recipe, not the cake: recipes, his own content and run results go to storage he connects; rebuildable things are fetched or rebuilt; secrets never leave the PC.
- **Stand-in rule.** Closed tickets were settled from the inputs by the map agent standing in for him; the coordinator checks them. Open tickets are his, each with a recommended answer he can accept with "yes".

## Decisions so far

### What is saved
- [What a sync sends, decided once by class](tickets/saved-set-by-class.md): one class table and `class_of`; recipes, content and results go; rebuildable, secret and scratch never do; Library objects are classed by kind; per-machine settings are marked.
- [Secrets never travel; a new PC asks for keys by name](tickets/secrets-stay-home.md): one secret list (it also fixes the attach guard); the sealed key copy is parked; copies carry key names; `rclone.conf` is encrypted from Credential Manager.
- [Packs and compression inside QMX's own pool](tickets/packs-and-compression.md): packs with one zstd frame per file, the sha256 name kept, one format for every storage; not restic (its encryption is mandatory), not rclone compress, sync or bisync.

### Where it goes
- [One storage seam and one rclone runner](tickets/one-rclone-runner.md): the built `Repository` protocol gains an rclone adapter; one PC runner that never echoes rclone's output; PR 6's checks kept, its hard-link tree dropped.
- [One place list for compute and storage](tickets/one-place-list.md): one list with `can` run or keep; `[remote]` goes; backup targets become place rows; sync policy keyed by place id.
- [Spread copies over several free Google accounts (E2)](tickets/spread-over-accounts.md): viable only if QMX places files itself; not built, since the set fits one account and `union` is unsafe; each storage holds a whole copy.
- [Several PCs and one storage](tickets/several-machines-one-storage.md): each home writes only its own folder, so no lock is needed; the fork guard stays; he picks among the newest copies, never QMX quietly.
- [One free-space floor, and full storage](tickets/one-free-space-floor.md): one local floor that also covers C:; a floor on any account that reports free space (2 GB or a tenth); a full storage stops alone with one incident.

### When it runs
- [The switch, what each storage gets, and when it syncs](tickets/sync-switch-and-timing.md): one main switch; four class switches per storage, all on; daily when changed, before updates and on "sync now"; dated copies, not a mirror; every default visible.
- [Copies on this PC: kept, smaller, switchable](tickets/copies-on-this-pc.md): on by default (R136), with an off switch and a cadence; the saved set only, packed and compressed.
- [Monthly re-pack and check as QMX's own maintenance](tickets/maintenance-repack-and-check.md): a host job per storage (re-pack past 5% unused, check a twelfth, the drill); one scheduler; a separate maintenance list; an optional agent through an event-triggered workflow.
- [Sync before every update](tickets/sync-before-update.md): `sync_now(why="before-update")`; Hermes's order with the sync first; the updater asks when the sync fails, and `serve` falls back to the local copy.

### Coming back
- [Restore from my storage, on a new PC and from Settings](tickets/restore-from-storage.md): the built restore with a storage source; sign in, pick a copy, see what it replaces, restore with counts, keys to fill in, carry on.

### Connecting from the screen
- [One step-by-step connect dialog for screen and copilot](tickets/connect-dialog.md): a kind is `(name, who, check, do)` steps on the built job runner; a rerun resumes it; his steps are cards; one backend serves the screen and the copilot; a write-only key route; the place row is written last.
- [Connect a storage](tickets/connect-storage.md): rclone's own question loop runs the dialog for any kind; QMX's own Google client (`drive.file`, PKCE, published); R2, SFTP and folder kinds; the test, then the first sync.
- [Connect a server, GPU or key-based compute](tickets/connect-compute.md): `qmx node setup` as checked steps, a Tailscale one-off key, the place row, the status ladder's first caller, a smoke test, recovery status; key compute through one test call.
- [Connect deep logs (OpenObserve) on any machine](tickets/connect-deep-logs.md): self-hosted, one per person; `send_to` checked on save; on this PC with safe defaults (no telemetry, a small cache, 30 days); a collector with a disk queue elsewhere; an agent login on its MCP door; no backup of its data.

### Install, first start, update, and the UI gaps
- [What install and first start show, step by step](tickets/install-and-first-start.md): per-user install with no admin; the card gains "restore from my storage" and one optional "Keep your work in your storage" card; nothing else on the first start; read-only stores named up front.
- [Which UI-HANDOFF section 26 gaps belong here](tickets/ui-gaps-that-belong.md): gaps 1, 3, 4, 5, 6, 7 and 8 are in; 2 (broker REST) and 9 (attach) are out.
- [What goes before anything is added](tickets/subtract-first.md): the weekly GitHub snapshot, the volume backup (after the lease copy), `[remote]`, the second rclone runner, three floors, the fixed hourly rule, the PR 6 and 7 plan text and the old installer go first.

### Waiting for him (open, each with a recommended answer)
- [Which storage do you connect first? (E1)](tickets/first-storage.md): recommended: Drive's free space for his work, and the old ticks to his server once it is connected.
- [What the screen calls it (E3)](tickets/screen-words.md): recommended: "Sync to my storage", "Storage", "Restore", "Maintenance", "Server link"; "backup" leaves the screen.
- [Lock copies on cloud storage with a passphrase? (E4)](tickets/lock-cloud-copies.md): recommended: locked on Drive and R2, unlocked on his server and plugged-in drives, with the passphrase in Windows' password safe.

Each open answer changes a default or a word, not the design's shape.

## Not yet specified

- **Defaults from his real folder.** His real folder was never read, so the size of the saved set, how fast the copies on this PC grow, and how big the changing stores are (`engine.sqlite` above all) are estimates. The first real start measures them. Revisit only if they are large: sending run results as appended records instead of whole stores, chunking, a compression dictionary, one chat format marked rebuildable, and spreading over several storages.
- **The QMF price-store retry** (about 1.3 s) against a large open price month: the build measures it.
- **OpenObserve without admin rights on Windows:** the build's first check. The dialog covers both outcomes.

## Out of scope

- **PC-started work running on a named place** (machines #14, "needs a ruling"): engine dispatch, for the stand-in round's own design (`design:` G, "Later"). The connect dialog proves a place answers and runs a test with its own engine.
- **The desktop installer and updater themselves:** the desktop session builds them. This map fixes their step lists and the backend calls.
- **Broker reads over REST** (UIH §26 gap 2): broker and connections work.
- **The attach route and `@file`** (UIH §26 gap 9): the parked attach plan. Its secret-list fix is in here.
- **PR 229's failing check and the Hub heartbeat `[engine]` wipe:** PR 229's own fix round, the coordinator's call.
- **The sealed key copy (planned PR 7):** parked in the backlog. He never asked for it (`words:29`).
- **A QMX-run account service with its own sign-in:** settled by his words. Each person connects their own storage (`words:185`).
- **The trading node's own backup and its Prometheus, Loki and Grafana stack:** the trading-node session's; node internals are not re-discussed here.
- **Exporting OpenObserve dashboards and alert rules into the sync:** none exist yet; backlog.
- **The server's own data push to a bucket (the Hub), and Litestream for container apps:** they stay as built.
- **Restore one mini app, undo a restore, and remove a set-aside folder on his click:** backlog (`align:` A4 row 52).
