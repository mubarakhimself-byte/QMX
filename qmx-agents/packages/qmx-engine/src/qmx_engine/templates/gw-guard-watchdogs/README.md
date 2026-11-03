# Watch each trading node and say when it is unwell

The node watcher's gauge (STATE midday ruling 44, Part B `workflows.md` section 3). Every 5 minutes a script reads each trading node's health from what This PC already holds, and when a node's health changes it lands one note saying which node is unwell and why. It never touches a node: it has no step that asks a node anything, no model and no tool, and everything it lands is a proposal for him on the run's own ref.

Built from cards R1 and R6 in `research/methodology/16-templates-trader-risk.md`, with its old read script replaced: it no longer waits for the trading node, because the node journal comes home (B15's harvester on This PC, B16's pull from servers) and the heartbeat log holds the node's beat.

## Steps

1. `Read each node's health` (a `monitor` over `scripts/read.py`) reads the node journal's `stand_down`, `kill_level`, `protection` and `node_lifecycle` rows through `journal_query`, each server node's newest rows in This PC's tail file, and the heartbeat log's newest rows. It gives each node a word:
   - **Alarm** while a stand-down that waits for his resume is held, when the kill switch rose or the venue did not hold a stop inside the lookback, and when the node's heartbeat is late.
   - **Watch** while a stand-down that clears itself is held (a stale feed, the clock band, the disk guard, a venue not ready), and when the runtime healed inside the lookback.
   - **Well** otherwise.
   Every time it prints is a row's own, so the same health prints the same output, and the monitor ends the run there at zero cost.
2. `Land the gauge` (`scripts/gauge.py`) runs only when the health changed. It lands the gauge as one `node-watch` artifact.
3. `Land the note as a proposal` (the slow lane's `scripts/land.py`) lands one `note`, marked `proposal: true`, written by the script.

Text the node took from outside (a stand-down's cause, a heal's error) is quoted in the note and marked `qmx.marked/1` in the gauge, so an instruction in it is read as data.

## Settings

- `here`: this machine's place name, `pc` on This PC. A node on this machine is heard by the trading node app's own heartbeat row. A node elsewhere is heard by the Hub's row of its host, when This PC holds the Hub.
- `lookback_h` (24): how far back kill rises, protection alarms and heals count.
- `stand_down_days` (30): how far back a stand-down still held is found.
- `heartbeat_stale_after_s` (120): when a node's heartbeat is late. The host beats every 30 s.
- `nodes`: the node machines to watch; every node seen by default.

The cron runs every 5 minutes in UTC. Missed runs follow the trigger's catch-up setting; the gauge needs none, because the next run reads the same journal.

## Left out, and why

- The node's live `status` through the host route (`apps.ask status`). A workflow script cannot reach the host's node link, and `app_op` runs app jobs only, so the watcher reads the rows the node journals on every change that `status` shows. A server node's rows count from the records job's tail file, at most one records round late (`[records] interval_s`, 300 s).
- The kill level now. The node journals a kill switch rise but not his resume that lowers it, so the gauge names each rise inside the lookback rather than the level held now.
- The kill-line distance and the tighten-only profile check of cards R1 and R6: equity, the kill line, the daily loss budget and signed risk profiles are the risk session's, and no node row carries them yet.
- Proposal cards. Every card the Library's `proposal-card` kind can ask (paper, live, admit or drop a market, tighten, bench) changes what trades, and none follows from a node's health alone. The watcher's note is its proposal.
- A node with no journal rows in either window and no heartbeat read here is not listed.
