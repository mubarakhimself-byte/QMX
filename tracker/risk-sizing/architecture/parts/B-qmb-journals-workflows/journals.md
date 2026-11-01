# Journals and records

Part B, sub-area 3. Decisions: spine AD-208, AD-209, AD-210, AD-211. Shapes: `CONTRACTS.md` §4 to §6. Slices: `BUILD-SLICES.md` B8, B9, B13, B15, B16. Amended after R1 (`architecture/review/R1-FIXES-X1-B.md`).

**In plain words.** Every unit keeps one journal from the day it is made: in backtest and stress, on paper, on demo and live, on every market, broker, account, platform and node. Each line in it says which unit, market, account, machine and world it came from; what the line says depends on what happened (a trade, a signal it skipped and why, a number that moved, a move between draft, tested, paper and live). Beside it sit the market journal (costs and conditions per market and minute, written once), the node journal and the reading history. A node writes its own journal first; its machine files it into its own store every minute; the PC brings it home later, so a node never waits for the PC.

His words: "The journals have one simple row shape. I disagree." (T3:903); "The journal is very important, please." (T3:903); "there are times whereby a unit will go back to paper trading. That is known." (T3:903); "this is literally the DevOps layer for that unit" (T1:1574); "we need to separate the journal for the router" (T1:1574).

Ledger rows that bind: J-01, J-02, J-03, J-04, J-06, L-02, L-03, CC-12. J-07 ("most simple data schemas") is superseded by J-01.

## 1. Verdict: core

The envelope, the kinds, the writer library and the agents' read door are core; every app writes through them. A journal is his content and travels with his work (PR 231's save classes, `qmx_home/classes.py`, G4a §1.2).

## 2. What exists (CHECKED)

| Piece | Where |
| --- | --- |
| CT-13 events: seven types, int64 UTC nanoseconds, writer id, gapless sequence; addable, never redefined; decision outcome `authorized`, `refused-by-door`, `suppressed` | `packages/qmf-data/src/qmf/data/journal.py:1-40` |
| CT-13 store: one-writer JSONL streams per world, fsync, rotation, idempotent byte-identical re-append, a second writer refused, cross-world read refused | `packages/qmf-data/src/qmf/data/store/journal.py:1-60` |
| The store's reader rebuilds its index on every read and quarantines a torn last line by truncating the data file, even as an unlocked reader | `packages/qmf-data/src/qmf/data/store/engines/jsonl.py:363-398`, `:510-547`; shown by running `scratchpad/x1b/br_reader_truncates.py` (R1 fix round) |
| CT-25 logbooks (read-time projections), CT-29 exit records with `realized_r` | `qmf-data/logbooks.py`; `qmf-risk/exit_record.py` |
| Broker fills as partitions; `trade` items per round trip (29 fields, world enum `backtest, paper, demo, live, synthetic`) | `qmf-data/importers/journal.py:1-45`; `qmx_library/kinds/trade.schema.json` |
| The typed partition store: key `source/subject/kind/variant/year/month`, freeze per kind, numeric columns only; `t` read in epoch milliseconds; the open month is one `open.parquet` replaced on each commit | `qmf-data/src/qmf/data/series.py:1-20`, `:188-260`, `:663-697`; `store/engines/typed.py:56-92` |
| The door commits a staged partition from any folder and pins PC-born files until a fingerprint list clears them | `qmx_host/market_data.py:544-617` |
| The node's journal-before-dispatch gate, never run on a venue | `qmn/src/qmn/journal_dispatch.py:1-12` |
| Missing: a unit journal, a market journal, reading history homes, an agent read door | G1 §7 |

## 3. The envelope and the kinds

**The envelope** `qmx.journal.envelope/1` (every field in `CONTRACTS.md` §4): `record_id`, `stream`, `kind`, `schema_version`, `writer_id`, `seq`, `ts_venue`, `ts_recv`, `ts_write`, `clock_ok`, `clock_offset_ns`, `backfilled`, `world`, `unit_id`, `unit_version`, `market_id`, `venue`, `account`, `platform`, `machine`, `run_id`, `trace_id`, `build`, `links`.

**World** (glossary; R0-19): `backtest`, `stress` (QMB runs whose study purpose is stress), `paper` (a unit's paper lane on a demo account), `demo` (other demo-account work: setup self-tests, the demo pass mark), `live`, `shadow` (a unit computing decisions on live data with no orders), `synthetic`. QMB stamps it from the run; the node from the account the venue reader proved and the deployment's lane; the unit never stamps it (JR-05).

**Unit journal kinds** (writer: QMB in backtest and stress, the node in paper, demo, live and shadow; `lifecycle` as below):

| Kind | Body (main fields) |
| --- | --- |
| `signal` | Part A's decision row: one decision on one instant: outcome `taken`, `skipped`, `blocked`, `suppressed` or `refused_by_door` (CT-13's outcomes plus two); `reason` from the closed list; the gate or guard that said no; `readings`: for every reading the unit computed or read, its id, version, value, source (`unit`, `node`, `mis`) and age (MIS-10); the slot outputs only when per-bar tracing is on |
| `order` | the CT-19 command, client order id (the trace id tagged with the node id), size and protection |
| `fill` | the CT-20 event (JR-07) |
| `trade` | one round trip: entry and exit, money, R, MAE and MFE in R, costs split, the context receipt (links, not copies), tuned values in force, equity before, session and day, streak, placeholder blocks, `r_missing` when no initial risk is known (JR-15), `gap_through_stop` with the R as it fell (RS-13) |
| `calibration` | Part A's calibration row: one move of a calibrated number: old, new, rule, rows read, statistic, watermark (AD-22) |
| `lifecycle` | Part A's `qmx.lifecycle/1` move: from, to, by (`judge`, `his_click`, `risk_rule`, `system`, with the principal), reason, evidence, the stop it clears |
| `state` | Part A's runtime state events: `warming`, `ready`, `cold_start` with its reason, `seam_flag` with its stream and jump |
| `guard` | a local guard's verdict (spread, clock band, feed freshness, windows) |
| `risk_event` | placeholder kinds the risk session fills (labelled `origin: placeholder`) |
| `would_have` | what a stopped unit would have done, so data keeps flowing |
| `data_event` | a gap, a halt, a roll, a close-only switch, a spec change the unit saw (QB-18, QB-05) |

**Who writes `lifecycle`** (R1-B-06). This PC's host, through `qmx_host/lifecycle.py`, for his clicks (Part C's promote action calls it) and for the judge's draft-to-tested or draft-to-parked move, written when the verdict lands; the node, for its risk stops. Nothing else writes the kind. Part A's `fold` reads a unit's `lifecycle` rows across every world, machine and writer, orders them by `(at, writer, sequence)`, and refuses an illegal move; the host's writer checks a move against it before appending.

**Market journal kinds** (writer: the feed keeper on each machine, Part C wires it):

| Kind | Body |
| --- | --- |
| `minute` | per venue, account type and instrument and minute: spread min, median and max; quote count; gaps; fees; measured slippage of QMX's own fills; session flags; depth summary where offered; the order-budget gauge where a venue rations actions |
| `offset` | a cross-source offset for one market id: two sources, the median gap and its spread over the day (LD-12, EX-15) |

**Node journal kinds** (writer: the node, Part C): `node_lifecycle` (node starts and stops), `passport`, `reconcile`, `kill_level`, `clock_band`, `feed_health`, `disk_guard`, `gap` (a sleep or power loss of This PC during practice, TN-15), `stand_down`, `spec_change`. Part C may add kinds; none is redefined.

**Reading history.** Rows ride the same envelope and storage with kind `reading`; the body (`qmx.reading/1`, reading id, version, source `node` or `mis`, value, percentile against usual, word, health, input receive times, `stale_after`) is Part C's.

**Record ids** (R1-B-10). A slice that crashed half way is run again by the node (its cursor commits only after a whole slice, `qmn/src/qmn/loop/driver.py:66-73`, CHECKED), so a row the slice produced must keep its id: `signal` and `calibration` rows take Part A's `row_id` (fp1 over the scope id, the instant and the ordinal); `state` rows fp1 over the scope id, the instant and their ordinal in the step; `lifecycle` rows the move's `event_id`; `fill` rows `<venue>:<deal id>`; `trade` rows `<venue>:<closing deal id>`. Every other row takes `<writer_id>/<seq>`. The writer keeps the open month's ids, rebuilt from its own stream when it opens it, drops a repeat without spending a sequence number, and keeps out a repeat whose body differs, answering `determinism_break`, which the host logs. Rows that read the machine's state at the time (`guard`, `order`, `would_have`, `data_event`, `risk_event`) keep sequence ids, because a natural id would refuse a true second reading; their readers never sum them into R or trade counts (Deferred in the spine).

**Reason codes** for `skipped` and `blocked`, closed and appendable (a new code is added, none is redefined): `no_signal`, `outside_session`, `market_shut`, `spread_wide`, `feed_stale`, `clock_band`, `max_positions`, `cross_unit_hook`, `kill_switch`, `halt_slot`, `below_min_lot`, `margin`, `warming_up`, `data_gap`, `reading_absent`, `close_only`, `spec_change_pause`, `risk_stop`, `health_stop`, `placeholder_refusal_never` (reserved: placeholders never refuse, AD-15, so this code exists only to make a test fail loudly if one ever does).

**What "why didn't it trade?" reads.** The latest `signal` rows for that unit and market, the gate named by the reason code, the market journal minute it links to, and the readings in force. A script walks those links; a cheap model writes one line from what the script found.

**Missed trades** are never written live. They are computed afterwards by replaying the unit over the recorded minutes (`replay_check`).

## 4. Where journals live

**Hot path.** The writer library opens one CT-13 stream per `(stream, subject, world, machine)` with one `WriterId`, always in the CT-13 store's `live` room (the store's worlds are `live`, `replay` and `simulated`, and paper and demo are `live` there, `qmf-core/src/qmf/core/fingerprint.py:412-424`); the envelope's `world` carries paper, demo, live or shadow. It appends envelope plus body as one canonical JSON line with fsync, and refuses a second writer (built). On the node this is in process, so the host is never a step before a send (AD-12). An append that cannot be written returns a refusal, never a silent drop (JR-13); the node's gate turns that refusal into "no new entries" while exits and broker stops still go (JR-02, Part C's). The writer library also appends **series rows**: a store kind's own typed row (`bar-*`, `ticks`) under its series key, so Part C's recorder writes the bars and ticks it records the same way.

**One reader rule.** Only the writer's own append path touches a live stream's files. Every other reader (the host's harvester, `journal_query`, a node's `journal_tail`) uses the writer library's committed reader, which reads LF-terminated lines across the rotation files and never writes. The shipped reader cannot be used for this: its index rebuild moves a torn last line into a `.torn` sidecar and truncates the data file, so a reader that met a line in flight would cut it from the writer's stream (§2; the proof script printed "before=96 during=126 after_read=96").

**The harvester** (the records job's local half, AD-209, R1-B-02). The host on each machine, This PC and servers alike, is the one harvester of every app's append streams there. Each round it reads the streams with the committed reader, stages partitions in the door's own staging layout (`<source>/<subject>/<kind>/<variant>/<YYYY-MM>.parquet`) in its own folder, and commits them through its own door with `born_on = node`; an app never opens the door. What it commits, and how often:

| What | When |
| --- | --- |
| a closed month of any stream (its end plus `[journals] settle_days`, default 1) | once, as soon as it closes; the store freezes it |
| the open month of reading history and of bars | every `[records] open_harvest_s` (60), as the one `open.parquet` the store replaces on each commit (`series.py:6-9`) |
| the open month of journals | on This PC only, every `[records] open_harvest_s`, because `journal_query` reads it there; a server's open journal months reach This PC by the tail |
| the open month of ticks | every `[records] tick_harvest_s` (3,600) |

A stream with nothing new since its last commit is skipped by its own fingerprint, because the store reports `idempotent = False` when the same rows are committed again (`series.py:429-430`; found by R1). The host's own tail stream (below) is never harvested.

**Partitions.** A row's month is the month of its `t`:

| Key part | Value |
| --- | --- |
| `source` | `journal-unit`, `journal-market`, `journal-node`, `journal-readings` |
| `subject` | unit id, market id or node identity; for `journal-readings`, `<source>.<market id>`, so the node's tick-tier rows and the MIS app's bar-tier rows never share a partition (R1-B-07) |
| `kind` | the record kind (`signal`, `minute`, ...) |
| `variant` | `<world>.<machine>`; for `lifecycle`, `<world>.<machine>.<role>` with role `host` or `node` |
| year, month | the month |

Every key part is a store token (letters, digits, dot, dash, plus, underscore, at most 64, `series.py:106`); the writer library maps any other id by one rule: `@` and `/` become `+`, any other character `_`, and past 64 characters the token keeps its first 51 characters, a dash and a 12-character fingerprint of the whole id. Columns: `t` (the writer's monotonic epoch-millisecond stamp: the write time, never lower than the row before, because the store refuses time going backwards and reads `t` in milliseconds), `seq`, `record` (the canonical JSON). The rule for `journal-*` sources freezes the month at its end plus one settlement day, like fill months. One writer per partition holds because the machine, and for `lifecycle` the role, is in the key (JR-01).

**QMB's run journal.** In backtest and stress the same kinds are written by the writer library's bundle mode into the run's output folder as partition files of the same layout, and land as the `backtest-result`'s `journal/*` blobs: a run's journal is one Library record (Level 0 AD-27, LC-A0-11).

**Library `trade` items.** The records host job projects each closed paper, demo and live round trip into one `trade` item (identity: account, position id, world), adding the new fields of `CONTRACTS.md` §5 additively; a re-projection lands nothing new. Backtest trades stay in the result's blobs.

## 5. Homecoming: the records host job

`qmx-agents/packages/qmx-host/src/qmx_host/records.py` (NEW), following `backups.py`: the host reads `[records]` every minute and runs the harvester on its cadences and, on This PC, a pull round every `[records] interval_s` (default 300), each on its own thread, so a round never holds a request; it is listed on the maintenance list with its off switch `[records] on` (default true) and lands one `maintenance-result` per pull round, with the harvester's counts since the last one (`qmx_host/maintenance.py:1-15`).

Its local half is the harvester of §4. Its remote half runs on This PC: a round, per node This PC can reach (the node list is Part C's: deployments and homes):
1. `data.list(after = watermark, confirmed = [...])` through AD-46: the partitions committed in that node's market-data store since the watermark (journals, reading history, and the bars and ticks its feed keeper recorded for its live units' markets, ticks only where a unit's data card names ticks, LC-X0-16), each with `frozen`; `confirmed` lists the fingerprints of the frozen partitions the last round committed (Part C's change, R1 CF-5);
2. `data.fetch` every frozen partition listed, and every open one whose fingerprint changed once its class is due (bars and reading history every `[records] open_pull_s`, default 3,600; ticks every `[records] tick_pull_s`, default 86,400; a growing month is fetched whole, so the defaults keep a home connection light); verify each fingerprint and commit it through This PC's door with `born_on = node`, where an open month replaces This PC's copy and its frozen month later replaces that; a resend changes nothing (idempotent by fingerprint and key);
3. advance the watermark past every partition that committed or was an open one not yet due (it is listed again after its next harvest), never past a frozen one that failed; remember the frozen fingerprints to confirm next round;
4. on the server, the door pins every `node`-born partition until This PC confirms it (a door whose placement is not `pc` pins them, as every door pins PC-born files today, `qmx_host/market_data.py:599-600`), and the built `verify` clears the pin by fingerprint (`:603-617`); This PC never confirms an open partition; **nothing prunes a node's store in this build**: a confirmed partition is unpinned and kept, and a later prune slice adds a retention setting (Deferred);
5. `apps.ask journal_tail` for the open month's newest journal rows of a server's node, written into This PC's own tail stream for that node, marked `backfilled = false`; `journal_query` reads it directly; the closed month replaces it;
6. project closed round trips into `trade` items;
7. land the round's `maintenance-result`: nodes reached, partitions fetched, open months fetched, bytes, fingerprints confirmed, partitions still pinned, refusals, the oldest unshipped month per node.

A node unreachable for a round is skipped and named; a week offline loses nothing (JR-16).

## 6. Blast radius of the storage changes (CHECKED by running)

The typed store gains one text column (`record`) and one rule (sources starting `journal-`). The fact it is safe because of: every existing kind keeps its columns and freeze rule, because the new rule matches only `journal-*` sources and the text column only the name `record`.

- `scratchpad/l1b/patch_journal.py` applied the change to an overlay copy of `qmf.data` (two files, `store/engines/typed.py`, `series.py`); the shipped `packages/qmf-data/tests` suite ran with the overlay first on pytest's path: **584 passed, 3 skipped**. `scratchpad/l1b/tests/test_journal_partition.py` (a journal month committed, re-committed idempotently, read back record by record, frozen after its month and settlement day, ticks unchanged): **1 passed**.
- **Found while proving it, in shipped code:** on Windows, a refused row inside `SeriesStore.commit` raises `PermissionError` (WinError 32) instead of returning a typed refusal, because the staging writer still holds `.incoming.parquet` when the commit unlinks it (`series.py:418-446`). Reproduced on the unpatched store by `scratchpad/l1b/refused_row_windows.py`. The journal slice fixes it (the typed writer closes its file before the unlink), because a malformed journal record must come back as a refusal (JR-13).
- **The open month harvested every minute** (R1, step 4): `r1/br_open_month.py` committed 60, 120 and 180 rows of one open `bar-m1` month; each landed as the same `open.parquet`, `frozen = False`.
- **Found in the R1 fix round, in shipped code:** a reader in another process truncates a writer's line in flight (§2, §4's reader rule). `scratchpad/x1b/br_reader_truncates.py` holds a stream as the app, writes a line without its LF, then reads from a second process with `JournalStore.read_stream`: the data file went from 126 bytes back to 96 and a `000000.jsonl.torn` sidecar appeared. B8's committed reader is tested on the same setup and must leave the file unchanged.

## 7. Numbers (starting defaults, all editable)

| Setting | Default | Origin |
| --- | --- | --- |
| `[journals] settle_days` | 1 | late rows from a machine whose clock was off |
| `[journals] per_bar_trace` | off; when on, for 1 day | funnel lead's call (party P8): near-miss rows answer the common question |
| `[journals] journal_floor_gb` | 2 | journals stop last; ticks stop first (LD-09) |
| `[records] interval_s` | 300 | LC-A0-21's 5-minute tail |
| `[records] open_harvest_s` | 60 | R1-B-02; Part C's MIS app reads bars a minute late at most (LC-C-16) |
| `[records] tick_harvest_s` | 3,600 | R1-B-02; a month of ticks is the largest file a harvest rewrites |
| `[records] open_pull_s` | 3,600 | INFERRED: the slow lane reads readings within the hour, and a growing month is fetched whole |
| `[records] tick_pull_s` | 86,400 | INFERRED: the nightly replay needs the day's ticks once |
| `[journals] digest_at` | each market's session close; 00:00 UTC for 24/7 markets | WF-04 |

## 8. How agents and he read journals

`journal_query` (core toolset `research`, read): arguments `stream`, `window` (required), filters by any envelope field, `view` (`rows`, `trades_with_context`, `digest`), `format` (`concise`, `detailed`). It answers from This PC's partitions (closed and open) plus the tail streams, with the committed reader for the tail; past the data it says where the data stops; live statistics exclude `backfilled` rows unless `include_backfilled` is set (JR-08). The daily digest per unit is made by a script at the unit's session close before any model reads it. Agents write only `note` items through `notes_write` (AD-211).

## 9. What must not break

CT-13's seven event types and their meanings; the JSONL store's one-writer rule; every price kind's columns and freeze rule (proven above); the door's PC-born pin and `verify` (unchanged; only `node`-born partitions on a non-PC door are added); `trade` items already landed (the kind's new fields are optional; its `world` enum is unchanged).

## 10. Growth seams

A new kind is a schema under the envelope plus a reason code if it skips. A typed column set for a hot kind is a new rule keyed by `journal-<stream>` and kind, added when a query proves slow. A new stream is a new `journal-<name>` source. A new harvested class (a new store kind an app records) is one row in §4's cadence table.
