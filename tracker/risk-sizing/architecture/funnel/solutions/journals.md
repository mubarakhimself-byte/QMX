# Journals: records across markets, brokers, accounts, platforms, nodes and worlds

**What this part is.** What QMX writes down while a unit lives: its trades, the trades it saw and did not take and why, how its numbers moved, its state changes and guard verdicts; the market journal of costs per broker and minute; the node's own journal; the readings history; and agents' notes. One envelope everyone can slice by, with records whose depth depends on their kind (weak spot 6).

**Verdict: core.** The record shapes, the one writer library and the agent door are core; every mini app writes through them. A journal is his content and travels with his work (PR 231's save classes).

## His words

- "The journals have one simple row shape. I disagree." (T3:903) "The journal is very important, please." (T3:903)
- "there are times whereby a unit will go back to paper trading. That is known." (T3:903)
- "this is literally the DevOps layer for that unit" (T1:1574)
- "we need to separate the journal for the router" (T1:1574)
- "we have a preview and a detailed view. So, design for both." (T1:1574)

## 1. What exists today

| Record | State | Where checked |
| --- | --- | --- |
| CT-13 journal events: seven types (decision, order, fill, risk transition, promotion, data quality, control action), int64 UTC nanoseconds, a writer id, a gapless sequence per writer; addable, never redefined; the decision event carries a closed outcome `authorized`, `refused-by-door`, `suppressed` | BUILT | read this session: `packages/qmf-data/src/qmf/data/journal.py` docstring |
| CT-25 logbooks: per-bot views as read-time projections | BUILT | G1 §7 |
| CT-29 exit records with frozen risk faces, fills, costs, `realized_r` | BUILT | G1 §7 |
| QMB ledger lines, one per trial | BUILT | G1 §7 |
| QMN journal-before-dispatch gate | BUILT, never run on a venue | G1 §7 |
| Broker fills as `<broker>/<account>/fill/<month>` partitions; `trade` items per round trip with `world`, `initial_risk`, `r`, swings | BUILT | G1 §7 |
| Every broker read stamped demo or live | BUILT (PR 215) | G2 §11 |
| A unit journal, a market journal, a readings history, an agent door to journals | MISSING | G1 §7; G2 §3 |
| Save classes: what travels by class; results include `data/backtests/**`; a reserved row for a node's state on This PC | BUILT (PR 231) | G4a §1.2 |

## 2. Harvest: solutions already on disk

| Solution | Where | Fits now? | Carried as |
| --- | --- | --- | --- |
| Five streams with one writer each (unit journal, market journal, reading history, node journal, notes) | research 43 F4 | Yes for the streams and the one-writer rule; **no** for "every row has the same shape", which followed his superseded "most simple data schemas" (ledger J-07, "missed" item 5) | §3, §4 |
| The stamped trade: money and R, excursions in R, a context receipt (references, not copies), tuned values in force, plus equity before, session, streak, account, so any sizing can be replayed later | research 43 F1; research 26 §6 | Yes | §4 trade kind |
| Keys from his 31 Oct list: unit, world (backtest, stress, paper, demo, live), phase, instrument, broker, account, platform, machine | research 53 §2 item 9; research 52 §4 Journals row | Yes | §3 envelope |
| Monthly Parquet partitions per stream with one Library card per partition; partition key unit, world and machine so a twin and the live copy never write one file | research 43 F4, §3.5 | Yes | §5 |
| Seen-but-not-taken rows with one reason from a closed, appendable list; missed trades computed afterwards by replay; events only by default; per-bar logging on request for a time box | research 43 §3.5 (`live-field.md` B067, B068) | Yes | §4, §6 |
| A separate market journal per broker, account type, instrument and minute (spread, fees, slippage, sessions), which fills QMB's cost models over time | ledger J-04; research 12; research 43 §4 L05-11 | Yes | §3 |
| Agents read through a journal door, a prebuilt trades-with-context table and a script-made daily digest | research 43 §3.5 | Yes | §7 |
| Recordings and journals on D: on his PC | research 43 F4 (research 33) | Yes | §5 |
| The trading server queues journals while the PC is off (new work) | research 43 F4 "New work" | Yes | §5 |

## 3. The shapes

### Shape A. One envelope, typed kinds, on CT-13 (recommended)

- **What.** Every record carries the same envelope of keys (§3.1); its body depends on its kind. CT-13's seven event types are the base vocabulary; the unit journal adds kinds (calibration, would-have, state) the CT-13 rule "addable, never redefined" already allows. One writer library writes every stream.
- **Hard cases.** A unit live on gold and on paper on EURUSD at once; the same unit on two nodes; a unit sent back to paper; a backtest and a live run of the same days compared; a sizing rule replayed months later: all are queries over the envelope.
- **Maintain.** One envelope schema, kind schemas versioned separately; old rows never migrate.
- **Explain.** "Every line in a journal says which unit, which market, which account, which machine and which world it came from. What the line says depends on what happened."

### Shape B. One wide row shape for everything

- **Why not.** It is what he disagreed with on 31 Oct. Either the row is too thin for a trade or too wide and mostly empty for a guard verdict.

### Shape C. A separate table per kind with no shared keys

- **Why not.** Slicing across kinds (why this unit did not trade on this market at this minute, with that spread) needs joins on keys that each table names differently.

**Pick: Shape A.**

### 3.1 The envelope

| Key | Meaning |
| --- | --- |
| `record_id`, `stream`, `kind`, `schema_version` | identity and shape |
| `writer_id`, `seq` | one writer, gapless sequence (CT-13) |
| `ts_venue`, `ts_recv`, `ts_write` | UTC nanoseconds; venue time where the venue gives one (cTrader gives none, G3 §2.1) |
| `clock_ok` | false when the writing machine could not prove its clock offset (`devops-and-clocks.md`) |
| `world` | backtest, stress, paper, demo, live, shadow, synthetic |
| `unit_id`, `unit_version` | which unit, which frozen version |
| `market` | instrument at venue |
| `account` | broker plus account id plus account type (netting or hedging) |
| `platform` | ctrader, ccxt:exchange, hyperliquid, and later futures routes |
| `machine` | the machine that wrote it (This PC, a named server) |
| `run_id` | the QMB run or the node session |
| `trace_id` | one id from source idea to trade; the client order id is the trade's trace id (research 43 §3.6) |
| `build` | the writer's build version |
| `links` | references to other records (the readings at entry, the market-journal minute, the calibration row in force) |

## 4. The kinds, by stream

| Stream | Writer | Kinds and what each body holds |
| --- | --- | --- |
| **Unit journal** | QMB for backtest and stress; the node for paper, demo and live | `signal` (taken, skipped with one reason code and the gate that said no, blocked by a guard) as CT-13 `decision` with outcome; `order` and `fill` (CT-19 command and CT-20 events); `trade` (round trip: entry and exit, money, R, MAE and MFE in R, costs split, the context receipt, tuned values in force, equity before, session and day, streak, sequence number); `calibration` (number, old and new, rule, rows read, statistic); `state` (lifecycle change per market, who moved it); `guard` (verdict); `risk_event` (placeholder kinds for the risk session); `would_have` (rows a stopped unit keeps writing) |
| **Market journal** (his journal for the router, ledger J-04) | the feed keeper on each machine | per venue, account type, instrument and minute: spread (min, median, max), quote count, gaps, fees, measured slippage of QMX's own fills, session flags, depth summary where offered, the order-budget gauge where a venue rations actions |
| **Node journal** | the node | start, stop, update, self-test passport, reconcile results, kill-switch levels, clock band changes, feed health, disk guard |
| **Reading history** | the MIS (and QMB for backtest stamps) | stamped readings: reading id, version, compute time, input receive times, value, percentile against usual, word, health (`mis.md`) |
| **Notes** | agents | analysis and proposals, each linked to the rows it annotates; agents write only here |

**What "why didn't it trade?" reads** (S087): the latest `signal` rows for that unit and market, the gate named in the skip reason, the market-journal minute it points at, and the readings in force. A script walks those links; a cheap model writes one line from what the script found.

**Missed trades** are never written live. They are computed afterwards by replaying the unit over the recorded minutes (research 43 §3.5).

## 5. Where journals live and how they cross machines

- **Partitions.** Monthly Parquet partitions keyed by stream, unit, world, machine and month, one Library card per partition, like the price partitions. One writer per partition (poteto-mode's separate-before-serializing principle): a practice twin on his PC and the live copy on a server never write the same file.
- **On his PC.** Under the QMX folder on D:, not the Linux layer's disk on C: (research 33 §4.1 via research 43 F4).
- **From a node to the PC (weak spot 6, across nodes).** The node always writes locally first, so trading never waits on the PC. A shipping job sends closed partitions and the live tail one way to the PC's Library when it is reachable, idempotent by writer id and sequence: a resend changes nothing. While the PC is away, partitions queue on the server's disk under the node's disk guard (journals outrank tick recordings, S098). This is the same link the MIS's history uses (`mis.md` §6), so it is built once.
- **Two nodes, one unit.** Each node writes its own partitions; a unit's view merges them by query. A failover takes a lease per unit and account before it writes (research 43 F4, review E01).
- **Worlds and going back to paper.** World is on every row and the unit's state machine runs per market (`unit.md` §5). Back to paper is a `state` row and then rows with world "paper" for that market, while other markets may stay live.

## 6. How much is written

- **Events by default:** every taken trade, every skip with its reason, every guard verdict, every calibration move, every state change.
- **Near misses always:** a signal that passed its trigger and was then refused by a gate is a `signal` row with outcome `suppressed`, so "why didn't it trade" always has an answer.
- **Per-bar decision traces** (every slot's output every bar) only on request, for a time box (party P8 clash; lead's call). Why: the near-miss rows answer the common question at a fraction of the volume; full traces are for debugging one unit. How to undo: set the default time box to the first N days of every new deployment.

## 7. How agents and he read journals

- **Agents:** a `journal_query` catalog row (read only; every query carries a time window, per research 29's window field), a prebuilt trades-with-context table so agents never write joins, and a daily digest per unit made by a script before any model reads it (research 43 §3.5). Agents write only in the notes stream.
- **His screens (notes for the UI agent):** a preview card per unit (state per market, today's trades, a one-line "why it didn't trade" when it skipped) and a detail page (the journal by world, lineage, markets, history, backtest results, the calibration dial). The UI is judged by running its design (UI-03).

## 8. Numbers (starting defaults, all editable)

| Number | Default | Why |
| --- | --- | --- |
| journal partition | one month | research 43 §5 (`live-field.md` B073) |
| per-bar trace time box when switched on | 1 day | research 43 §5 |
| shipping interval node to PC | every 5 minutes for the live tail; closed partitions at once | INFERRED; idempotent, so the interval only sets freshness |
| server disk guard | tick recording stops at 85% disk; journals stop last | journals are the record (research 43 §4 L14-10); the 85% is INFERRED |
| daily digest | once per unit per trading day, at the unit's session close | research 43 §5 session clocks |

## 9. Connection points

| From | To | What crosses |
| --- | --- | --- |
| QMB app | unit journal (backtest, stress) | records through the writer library |
| Node app | unit journal, node journal | records, written locally first |
| Feed keeper | market journal | per-minute rows |
| MIS | reading history | stamped readings |
| Node | PC Library | closed partitions and the live tail, one way |
| Agents | journals | `journal_query`, digests; notes written |
| Judge and decay check | unit journal | trades in R against the baseline card |

## 10. Open for the architecture step

1. The exact kind schemas and their reason-code list (closed, appendable).
2. Whether the trade kind extends the Library's `trade` kind or is a unit-journal kind that the `trade` kind is projected from.

## 11. Parked

- Portfolio optimisation from journals (a template for the risk session, ledger J-05).
- Performance-over-time studies by family and pair (the old WF3 shape) as a later workflow.
