# Journals and records

Part B, sub-area 3. Decisions: spine AD-208, AD-209, AD-210, AD-211. Shapes: `CONTRACTS.md` §4 to §6. Slices: `BUILD-SLICES.md` B7, B8, B15.

**In plain words.** Every unit keeps one journal from the day it is made: in backtest and stress, on paper, on demo and live, on every market, broker, account, platform and node. Each line in it says which unit, market, account, machine and world it came from; what the line says depends on what happened (a trade, a signal it skipped and why, a number that moved, a state change). Beside it sit the market journal (costs and conditions per market and minute, written once), the node journal and the reading history. A node writes its own journal first and the PC brings it home later, so a node never waits for the PC.

His words: "The journals have one simple row shape. I disagree." (T3:903); "The journal is very important, please." (T3:903); "there are times whereby a unit will go back to paper trading. That is known." (T3:903); "this is literally the DevOps layer for that unit" (T1:1574); "we need to separate the journal for the router" (T1:1574).

Ledger rows that bind: J-01, J-02, J-03, J-04, J-06, L-02, L-03, CC-12. J-07 ("most simple data schemas") is superseded by J-01.

## 1. Verdict: core

The envelope, the kinds, the writer library and the agents' read door are core; every app writes through them. A journal is his content and travels with his work (PR 231's save classes, `qmx_home/classes.py`, G4a §1.2).

## 2. What exists (CHECKED)

| Piece | Where |
| --- | --- |
| CT-13 events: seven types, int64 UTC nanoseconds, writer id, gapless sequence; addable, never redefined; decision outcome `authorized`, `refused-by-door`, `suppressed` | `packages/qmf-data/src/qmf/data/journal.py:1-40` |
| CT-13 store: one-writer JSONL streams per world, fsync, rotation, idempotent byte-identical re-append, a second writer refused, cross-world read refused | `packages/qmf-data/src/qmf/data/store/journal.py:1-60` |
| CT-25 logbooks (read-time projections), CT-29 exit records with `realized_r` | `qmf-data/logbooks.py`; `qmf-risk/exit_record.py` |
| Broker fills as partitions; `trade` items per round trip (29 fields, world enum `backtest, paper, demo, live, synthetic`) | `qmf-data/importers/journal.py:1-45`; `qmx_library/kinds/trade.schema.json` |
| The typed partition store: key `source/subject/kind/variant/year/month`, freeze per kind, numeric columns only; `t` read in epoch milliseconds | `qmf-data/src/qmf/data/series.py:188-260`, `:663-697`; `store/engines/typed.py:56-92` |
| The node's journal-before-dispatch gate, never run on a venue | `qmn/src/qmn/journal_dispatch.py:1-12` |
| Missing: a unit journal, a market journal, reading history homes, an agent read door | G1 §7 |

## 3. The envelope and the kinds

**The envelope** `qmx.journal.envelope/1` (every field in `CONTRACTS.md` §4): `record_id`, `stream`, `kind`, `schema_version`, `writer_id`, `seq`, `ts_venue`, `ts_recv`, `ts_write`, `clock_ok`, `clock_offset_ns`, `backfilled`, `world`, `unit_id`, `unit_version`, `market_id`, `venue`, `account`, `platform`, `machine`, `run_id`, `trace_id`, `build`, `links`.

**World** (glossary; R0-19): `backtest`, `stress` (QMB runs whose study purpose is stress), `paper` (a unit's paper lane on a demo account), `demo` (other demo-account work: setup self-tests, the demo pass mark), `live`, `shadow` (a unit computing decisions on live data with no orders), `synthetic`. QMB stamps it from the run; the node from the account the venue reader proved and the deployment's lane; the unit never stamps it (JR-05).

**Unit journal kinds** (writer: QMB in backtest and stress, the node in paper, demo, live and shadow):

| Kind | Body (main fields) |
| --- | --- |
| `signal` | one decision on one instant: outcome `taken`, `skipped`, `blocked`, `suppressed` or `refused_by_door` (CT-13's outcomes plus two); `reason` from the closed list; the gate or guard that said no; `readings`: for every reading the unit computed or read, its id, version, value, source (`unit`, `node`, `mis`) and age (MIS-10); the slot outputs only when per-bar tracing is on |
| `order` | the CT-19 command, client order id (the trace id tagged with the node id), size and protection |
| `fill` | the CT-20 event; `record_id` is `<venue>:<deal id>`, so a replayed fill appends nothing and two venues never collide (JR-07) |
| `trade` | one round trip: entry and exit, money, R, MAE and MFE in R, costs split, the context receipt (links, not copies), tuned values in force, equity before, session and day, streak, placeholder blocks, `r_missing` when no initial risk is known (JR-15), `gap_through_stop` with the R as it fell (RS-13) |
| `calibration` | one move of a calibrated number: old, new, rule, rows read, statistic, watermark (AD-22) |
| `state` | a lifecycle change per market, who moved it (his click, a risk rule) |
| `guard` | a local guard's verdict (spread, clock band, feed freshness, windows) |
| `risk_event` | placeholder kinds the risk session fills (labelled `origin: placeholder`) |
| `would_have` | what a stopped unit would have done, so data keeps flowing |
| `data_event` | a gap, a halt, a roll, a close-only switch, a spec change the unit saw (QB-18, QB-05) |

**Market journal kinds** (writer: the feed keeper on each machine, Part C wires it):

| Kind | Body |
| --- | --- |
| `minute` | per venue, account type and instrument and minute: spread min, median and max; quote count; gaps; fees; measured slippage of QMX's own fills; session flags; depth summary where offered; the order-budget gauge where a venue rations actions |
| `offset` | a cross-source offset for one market id: two sources, the median gap and its spread over the day (LD-12, EX-15) |

**Node journal kinds** (writer: the node, Part C): `lifecycle`, `passport`, `reconcile`, `kill_level`, `clock_band`, `feed_health`, `disk_guard`, `gap` (a sleep or power loss of This PC during practice, TN-15), `stand_down`, `spec_change`. Part C may add kinds; none is redefined.

**Reading history.** Rows ride the same envelope and storage; the body (`qmx.reading/1`, reading id, version, source, value, percentile against usual, word, health, input receive times, `stale_after`) is Part C's.

**Reason codes** for `skipped` and `blocked`, closed and appendable (a new code is added, none is redefined): `no_signal`, `outside_session`, `market_shut`, `spread_wide`, `feed_stale`, `clock_band`, `max_positions`, `cross_unit_hook`, `kill_switch`, `halt_slot`, `below_min_lot`, `margin`, `warming_up`, `data_gap`, `reading_absent`, `close_only`, `spec_change_pause`, `risk_stop`, `health_stop`, `placeholder_refusal_never` (reserved: placeholders never refuse, AD-15, so this code exists only to make a test fail loudly if one ever does).

**What "why didn't it trade?" reads.** The latest `signal` rows for that unit and market, the gate named by the reason code, the market journal minute it links to, and the readings in force. A script walks those links; a cheap model writes one line from what the script found.

**Missed trades** are never written live. They are computed afterwards by replaying the unit over the recorded minutes (`replay_check`).

## 4. Where journals live

**Hot path.** The writer library opens one CT-13 stream per `(stream, subject, world, machine)` with one `WriterId`, always in the CT-13 store's `live` room (the store's worlds are `live`, `replay` and `simulated`, and paper and demo are `live` there, `qmf-core/src/qmf/core/fingerprint.py:412-424`); the envelope's `world` carries paper, demo, live or shadow. It appends envelope plus body as one canonical JSON line with fsync, and refuses a second writer (built). On the node this is in process, so the host is never a step before a send (AD-12). An append that cannot be written returns a refusal, never a silent drop (JR-13); the node's gate turns that refusal into "no new entries" while exits and broker stops still go (JR-02, Part C's).

**Closed months.** At a month's end plus `[journals] settle_days` (default 1), the writer library rolls the month's lines into one journal partition file in its own volume; the machine's host commits it through that machine's market-data door (the records job's local half), so an app never opens the door. A row's month is the month of its `t`:

| Key part | Value |
| --- | --- |
| `source` | `journal-unit`, `journal-market`, `journal-node`, `journal-readings` |
| `subject` | unit id, market id, node identity, or reading series |
| `kind` | the record kind (`signal`, `minute`, ...) |
| `variant` | `<world>.<machine>` (tokens of letters, digits, dot, dash, plus, underscore, `series.py:106`) |
| year, month | the month |

Columns: `t` (the writer's monotonic epoch-millisecond stamp: the write time, never lower than the row before, because the store refuses time going backwards and reads `t` in milliseconds), `seq`, `record` (the canonical JSON). The rule for `journal-*` sources freezes the month at its end plus one settlement day, like fill months. One writer per partition holds because the machine is in the key (JR-01).

**QMB's run journal.** In backtest and stress the same kinds are written by the writer library's bundle mode into the run's output folder as partition files of the same layout, and land as the `backtest-result`'s `journal/*` blobs: a run's journal is one Library record (Level 0 AD-27, LC-A0-11).

**Library `trade` items.** The records host job projects each closed paper, demo and live round trip into one `trade` item (identity: account, position id, world), adding the new fields of `CONTRACTS.md` §5 additively; a re-projection lands nothing new. Backtest trades stay in the result's blobs.

## 5. Homecoming: the records host job

`qmx-agents/packages/qmx-host/src/qmx_host/records.py` (NEW), following `backups.py`: the host reads `[records]` every minute and, when a round is due (`[records] interval_s`, default 300), runs one round as a `records` job on its own thread, so a round never holds a request; it is listed on the maintenance list with its off switch `[records] on` (default true) and lands one `maintenance-result` per round (`qmx_host/maintenance.py:1-15`).

Its local half runs on every machine, servers included, and commits each sealed month from the apps' volumes through that machine's door. Its remote half runs on This PC: a round, per node This PC can reach (the node list is Part C's: deployments and homes):
1. `data.list(after = watermark)` through AD-46: closed partitions in that node's market-data store newer than the watermark (journals, reading history, and the quotes and bars its feed keeper recorded for its live units' markets, ticks only where a unit's data card names ticks, LC-X0-16);
2. `data.fetch` each, verify its fingerprint, commit it through This PC's door; a resend changes nothing (idempotent by fingerprint and key);
3. advance the watermark only past partitions that committed; the next `data.list` with that watermark tells the node those are safely home, and the node deletes them after `[records] node_retention_days` (default 30) under its disk guard;
4. `apps.ask journal_tail` for the open month's newest rows, written into This PC's own tail stream for that node; closed months replace the tail;
5. project closed round trips into `trade` items;
6. land the round's `maintenance-result`: nodes reached, partitions fetched, bytes, refusals, the oldest unshipped month per node.

A node unreachable for a round is skipped and named; a week offline loses nothing (JR-16).

## 6. Blast radius of the storage change (CHECKED by running)

The typed store gains one text column (`record`) and one rule (sources starting `journal-`). The fact it is safe because of: every existing kind keeps its columns and freeze rule, because the new rule matches only `journal-*` sources and the text column only the name `record`.

- `scratchpad/l1b/patch_journal.py` applied the change to an overlay copy of `qmf.data` (two files, `store/engines/typed.py`, `series.py`); the shipped `packages/qmf-data/tests` suite ran with the overlay first on pytest's path: **584 passed, 3 skipped**. `scratchpad/l1b/tests/test_journal_partition.py` (a journal month committed, re-committed idempotently, read back record by record, frozen after its month and settlement day, ticks unchanged): **1 passed**.
- **Found while proving it, in shipped code:** on Windows, a refused row inside `SeriesStore.commit` raises `PermissionError` (WinError 32) instead of returning a typed refusal, because the staging writer still holds `.incoming.parquet` when the commit unlinks it (`series.py:418-446`). Reproduced on the unpatched store by `scratchpad/l1b/refused_row_windows.py`. The journal slice fixes it (the typed writer closes its file before the unlink), because a malformed journal record must come back as a refusal (JR-13).

## 7. Numbers (starting defaults, all editable)

| Setting | Default | Origin |
| --- | --- | --- |
| `[journals] settle_days` | 1 | late rows from a machine whose clock was off |
| `[journals] per_bar_trace` | off; when on, for 1 day | funnel lead's call (party P8): near-miss rows answer the common question |
| `[journals] journal_floor_gb` | 2 | journals stop last; ticks stop first (LD-09) |
| `[records] interval_s` | 300 | LC-A0-21's 5-minute tail |
| `[records] node_retention_days` | 30 | a node keeps a month of shipped records |
| `[journals] digest_at` | each market's session close; 00:00 UTC for 24/7 markets | WF-04 |

## 8. How agents and he read journals

`journal_query` (core toolset `research`, read): arguments `stream`, `window` (required), filters by any envelope field, `view` (`rows`, `trades_with_context`, `digest`), `format` (`concise`, `detailed`). It answers from closed partitions plus the tail; past the data it says where the data stops; live statistics exclude `backfilled` rows unless `include_backfilled` is set (JR-08). The daily digest per unit is made by a script at the unit's session close before any model reads it. Agents write only `note` items through `notes_write` (AD-211).

## 9. What must not break

CT-13's seven event types and their meanings; the JSONL store's one-writer rule; every price kind's columns and freeze rule (proven above); `trade` items already landed (the kind's new fields are optional; its `world` enum is unchanged).

## 10. Growth seams

A new kind is a schema under the envelope plus a reason code if it skips. A typed column set for a hot kind is a new rule keyed by `journal-<stream>` and kind, added when a query proves slow. A new stream is a new `journal-<name>` source.
