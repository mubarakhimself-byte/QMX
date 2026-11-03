# G9: runtime brakes, market isolation and live-drift evidence

Grounding for the risk-core session, 3 Nov 2026. Read-only. Facts from code at the stack tip, with my own reading marked **[judgment]**. It builds on G6 (Book and BMS levels, paper) and G7 (unit inputs, MIS, instruments). G6 read shipped code on `engine/base`. G7 read branch tips on 1 Nov, when most C slices were not built. Section 8 lists what the stack changed in both.

His words this file answers to: `RC/seeds/operator-words-2026-11-03.md:15` (circuit breaker at unit and BMS level, isolating a market class on risk-off days or news, the kill switch handling news, SQS as a sensor, evidence before isolation) and `:13` (live results drifting from backtests: "You're meant to size down, I think, but not quickly").

**Paths.**

- `T` = `D:\QMX-worktrees\bld-us-c13`, branch `build/us-c13` at d02af358, the stack tip (75 PRs, `D:\QMX-worktrees\unit-ship\STACK-LIST.md`).
- `C12D` = branch `build/us-c12d` at 317352b6, one PR above the tip, read with `git show`. The branches `build/us-c25`, `us-c26` and `us-c27` touch agent grants, app installs and manifest secrets only, so nothing here.
- `UP` = `D:\QMX-worktrees\unit-plan\tracker\risk-sizing`. `L0` = `UP/architecture/level-0/ARCHITECTURE-SPINE.md`. `PH` = `UP/build/RISK-SIZING-PLACEHOLDERS.md`.
- `TPL` = `T/qmx-agents/packages/qmx-engine/src/qmx_engine/templates`. `KINDS` = `T/qmx-agents/packages/qmx-library/src/qmx_library/kinds`.
- `RC` = `D:\QMX-worktrees\risk-plan\tracker\risk-core`.

**Two words used throughout.** "On the trading path" means the new unit node (`T/qmn/src/qmn/app/`) calls it before or after an order. "Built, off the path" means the code exists, but only the old Book-era node shell uses it. Part C plans to delete that shell after demo trading (`UP/architecture/funnel/solutions/node.md:40-56`; slice C-20 is not on the stack).

---

## 0. Short answers

1. **One brake is truly on the path for risk: the kill switch.** Only he can raise it, at four scopes: all, account, deployment and instrument (`T/qmn/src/qmn/app/operations.py:152-172`; `T/qmx-agents/packages/qmx-host/src/qmx_host/node_link.py:429-438`). Every other brake on the path is a health check.
2. **The risk-stop pipe is built, but nothing feeds it.** A risk stop holds a unit on one market, survives restarts and waits for his resume (`T/qmn/src/qmn/app/stand_down.py:550-595`). No production code calls it. Only tests do. The compiler refuses any unit that declares a halt (`T/qml/src/qml/compile/compiler.py:498-499`).
3. **No circuit breaker, daily stop, budget door, bench, kill line, news window or SQS gate runs on the unit path.** The kill line, bench, news windows and SQS are built, off the path.
4. **News is parked.** "News trading is out for now" (`UP/architecture/00-ledger.md:50`). A daily calendar workflow exists. It only informs.
5. **Paper is now a simulation inside the node**, not a demo account. It fills at the last closed bar's bid or ask, with zero slippage (`T/qmn/src/qmn/app/paper_lane.py:92-111`). Live money cannot be bound yet. A "live" lane today means real orders on a demo account (`T/qmn/src/qmn/app/runtime.py:2285`).
6. **Slippage can be measured now**, from the node's own order rows on demo, though no script does it yet (section 3.4).
7. **Market-class isolation has no hook today.** No class scope exists anywhere: not in the kill switch, the stand-downs, the board read or the MIS board.
8. **Costs by hour exist as a shape with no producer.** QMB reads a cost profile per market for each of the 168 hours of the week. Nothing writes one. The instrument record still has no commission key.
9. **Units on one account do not know about each other.** Each unit sizes from the whole account's equity at its start, plus its own results (`T/qmb/src/qmb/host/unit_handler.py:344-346`). The cross-unit hook passes every order.
10. **A drift detector has real inputs.** It has a frozen backtest cone per unit, live and paper trades in R, a nightly decay check and a live-day replay diff. All of them only inform. Nothing sizes down.

---

## 1. Every brake at the tip

### 1.1 The table

Level means the scope a brake stops. "Resets" says who or what clears it.

| Brake | Trips on | Level | Records or says | Resets | Numbers live | On the path? |
| --- | --- | --- | --- | --- | --- | --- |
| Kill switch | His `kill` change only; no automatic trigger | all, account, deployment, instrument (`operations.py:152-172`) | One `kill_level` row when a level rises (`runtime.py:2082-2091`); entry refusal text "the kill switch is at {level} for {scope}" (`runtime.py:2137-2141`) | His `resume` at that scope; `resume all` clears every scope (`operations.py:238-245`) | Effects per level are code constants marked placeholder: YELLOW stops entries, ORANGE also cancels resting entries, RED also closes the scope's positions, BLACK closes all and pauses (`T/qmn/src/qmn/protection/effect_matrix.py:136-146`) | Yes |
| Pause | His `pause` change | same four scopes | refusal "paused at {scope}" (`runtime.py:2142-2149`) | His `resume` | none | Yes |
| Flatten | His `flatten` change | same four scopes | answers `positions: 0` (`operations.py:379-380`) | n/a | none | **Accepted, does nothing.** `Target.fold` has no flatten branch (`operations.py:227-251`). The runtime never reads it (no "flatten" in `runtime.py`) |
| Withdraw | His park or retire click (`promote.py:449-452`) | deployment | "the deployment is withdrawn" (`runtime.py:2150-2151`) | a new deploy | none | Yes |
| Stale feed | a market's last quote is older than 120 s | instrument | `stand_down` start and clear rows; text "stood down, stale feed" (`stand_down.py:130-139`) | itself, after 60 s fresh | code constants (`stand_down.py:61-66`) | Yes |
| Clock band | clock offset past 500 ms | all | same rows (`stand_down.py:140-149`) | itself, after 5 min inside 100 ms | code constants, "labelled placeholders" (`stand_down.py:67-74`) | Yes |
| Disk | free space below 2 GB | all | same rows (`stand_down.py:150-158`) | itself, above 3 GB | code constants (`stand_down.py:75-79`) | Yes |
| Venue not ready | session drops or fails re-verification | account | same rows (`stand_down.py:159-167`) | itself | as built | Yes |
| Repeated fault | 5 restarts in 10 min | all | same rows, plus a phone push (`stand_down.py:168-176`; `T/qmn/src/qmn/app/alarms.py:262-263`) | his resume | code constants (`stand_down.py:80-84`) | Yes |
| Spec change | a broker changes lot step, margin, digits, leverage or mode | instrument | row defined (`stand_down.py:177-186`) | his click on the change card | none | **Row only.** No code raises it (grep `SPEC_CHANGE`, `spec_change` over `qmn`, `qmx-agents`, `packages`) |
| Risk stop | "a risk rule fires" | one unit on one market, `unit:{deployment}:{market}` (`stand_down.py:558`) | one `lifecycle` row `by: risk_rule`, unit moves to `stopped`; a `stand_down` row; a phone push only if trades are open (`stand_down.py:550-595`; `alarms.py:250-252`) | his resume at any covering scope: all, deployment, account or instrument (`runtime.py:2221-2226`; `stand_down.py:612-638`) | none | **Pipe only.** `Runtime.risk_stop` is called only from `qmn/tests/test_app_stand_down.py` and `test_app_healing.py` (grep `.risk_stop(`) |
| Unknown order answer | the venue's answer to an order is unknown | that market | "venue answer unknown" (`runtime.py:926-929`, `:1026-1029`) | the reconciler reads the venue | none | Yes |
| Reconcile hold | no reconcile yet for this venue session | account | reconciler's reason (`runtime.py:2161-2165`) | the reconcile run | none | Yes |
| Orphan position | one of our positions open that no unit holds | that market | "a position of ours that no unit holds" (`runtime.py:2166-2171`) | the position closes or is adopted | none | Yes |
| Protection escalation | the venue does not show the stop after 3 tries | that position | closes it reduce-only; `protection` row; phone push any hour (`runtime.py:1036-1061`; `alarms.py:123`) | n/a | `PROTECT_RETRY_MAX`, marked placeholder (`runtime.py:34-37`; PH row 19) | Yes |
| Board placement read | a fresh MIS board reads a word the deployment does not favour | one market of one deployment | refusal "the board does not favour {market} now" (`runtime.py:2152-2156`) | the board's word changes; stale or missing boards fall back to trading (`runtime.py:323-328`) | the deployment document (`runtime.py:294-320`) | Yes in code. Not fed in practice (section 4.3) |
| Cross-unit hook | never | account | "the cross-unit hook refused the order" | n/a | none | Passes every order (`runtime.py:1010-1013`; PH row 6) |
| Halt blocks: account daily loss, equity drawdown, losing days, session fills, session loss in R | their inputs (section 1.3) | account or unit (`block.py` files) | a `Halt` with action and reason (`T/qml/src/qml/blocks/api.py:167-185`) | per block | block parameters | **No.** "No host runs halts yet" (`api.py:181-183`); the compiler refuses halts (`compiler.py:498-499`) |
| Kill line | marked equity below a money floor per binding | binding | flatten, stand down, paper (`T/qmn/src/qmn/capital/kill_line.py:1-9`) | his signature | registry key | Built, off the path. Its verb waits for C-20 (PH row 20) |
| Loss bench | a run of qualifying losses | Book seat | routes the seat to demo (`T/qmn/src/qmn/capital/bench_fold.py:1-10`) | next open | registry | Built, off the path |
| News windows and dead zones | a news blackout, `daily_dead_zone`, `session_handover_buffer` | instrument by currency exposure | Book-door veto (`T/qmn/src/qmn/protection/windows.py:1-10`) | the window ends | registry widths, blank | Built, off the path |
| SQS | baseline spread ÷ live spread | instrument | a labeler output (`T/packages/qmf-readings/src/qmf/readings/labelers.py:1-6`) | n/a | baseline artifact | Built, off the path. Not in any MIS pack (`T/qmx-agents/apps/mis/packs.json`). The node runs no reading |
| Spread against the unit's cost target | planned local guard (`L0:383`) | instrument | n/a | n/a | n/a | Not built (no spread check in `runtime.py:919-1007`, `qml/protocol/unit.py` or `qmb/host/unit_handler.py`) |
| Budget door, daily stop, circuit breaker | n/a | n/a | n/a | n/a | n/a | Not found. Searched `budget`, `daily_loss`, `day_start`, `losing_day`, `open_risk` over the unit path; "circuit breaker" appears only in two halt blocks' aliases (`account-daily-loss-halt/1/entry.json:8`, `equity-drawdown-halt/1/entry.json:9`) |

The order of the entry checks is fixed in `runtime.py:2136-2180`. They run kill level, BLACK pause, pause, withdraw, board read, venue ready, reconcile hold, orphans and stand-downs. Then come the order-path checks: unknown answers, stop side, the cross-unit hook and the venue stop form (`runtime.py:919-971`). Exits, broker stops and kill closes skip the stand-downs (`stand_down.py:3-6`).

### 1.2 What happens on a restart (C-13)

- A runtime fault heals with back-off, starting at 1 s and capped at 60 s. A stuck pass (30 s) exits the process, and the app supervisor restarts it (`T/qmn/src/qmn/app/healing.py:1-18`, `:57-69`).
- The kill level comes back from his stored changes on every pass (`healing.py:15-17`).
- The stand-downs that wait for him are rebuilt from the journals at start (`stand_down.py:351-374`; `runtime.py:1792-1801`). A journal that cannot be read holds a repeated-fault stand-down at `all` (`runtime.py:1794-1800`).
- Since commit b7ca9c0f, a restart adopts the unit's own open positions, and the start re-checks the crash-loop count (`git show b7ca9c0f`).

### 1.3 The halt blocks A13d wrote (code exists, nothing runs them)

| Block | Input it needs | Action, scope | Released by |
| --- | --- | --- | --- |
| `account-daily-loss-halt@1` | `equity`, `day_start_equity`; trips at `equity/day_start − 1 ≤ −limit` | flatten, account | a new day's start equity (`T/qml/src/qml/blocks/stdlib/account-daily-loss-halt/1/block.py:1-11`, `:39-49`) |
| `equity-drawdown-halt@1` | `equity`; base is the first value, or the peak when trailing | flatten, account; holds | "releasing it is his call" (`equity-drawdown-halt/1/block.py:1-12`) |
| `losing-days-halt@1` | `losing_day_streak` | flatten, unit | the streak dropping (`losing-days-halt/1/block.py:1-9`) |
| `session-fill-limit-halt@1` | `session_fills` | flatten, unit | the host resetting at session start (`session-fill-limit-halt/1/block.py:1-10`) |
| `session-loss-limit-halt@1` | `session_loss_r` (R this session) | flatten, unit | the host resetting at session start (`session-loss-limit-halt/1/block.py:1-10`) |

Two more halts are dictionary entries without code. `stoploss-guard-halt` stops entries for a time after N stop-outs within a lookback (`T/qml/catalogue-seed/wave-1/exits-and-halts/stoploss-guard-halt.json:15`, freqtrade). `low-profit-lock-halt` locks one market after weak recent trades (`low-profit-lock-halt.json:12`).

No host computes `day_start_equity`, `losing_day_streak`, `session_fills` or `session_loss_r` (grep over `qmn`, `qmb`, `qml` source). Every halt in code says `flatten`. The slot contract also allows `no_new_entries` (`api.py:167-169`; PH "What the slots accept").

### 1.4 Small findings that matter for brakes

- **A risk stop is filed as a kill switch.** A risk stop blocks with text that contains "kill switch" (`stand_down.py:194-195`). QMB's journal maps reason text to codes, first match wins, and "kill switch" maps to `kill_switch` (`T/qmb/src/qmb/results/journal.py:46-68`, `:81-85`). No text maps to `risk_stop`, though that code exists (`T/packages/qmf-data/src/qmf/data/journal_kinds/unit.py:62`). **[judgment]** Anything that counts brake firings from decision rows would mix the two up.
- **The "named settings" are code constants.** The docstrings name keys such as `[node] feed_stale_after_s`, but no config file or reader uses them (grep over `qmn` and `apps/trading-node`). The kill effects are constants too. **[judgment]** This sits against his rule that anything configurable is UI-editable.
- **A risk rule can only stop.** The lifecycle table lets `risk_rule` move paper or live to `stopped` and nothing else. Leaving `stopped` for paper or live is his click (`T/qml/src/qml/lifecycle/machine.py:104-122`). Promote refuses a stopped market until he resumes it on the node (`T/qmx-agents/packages/qmx-host/src/qmx_host/promote.py:342-347`). No automatic demote to paper and no automatic size cut exist.

---

## 2. News

- **The unit plan parked news.** "News trading is out for now" (`UP/architecture/00-ledger.md:50`, CC-21, 31 Oct). The node plan keeps intake but "park[s] the news calendar" (`UP/architecture/funnel/solutions/node.md:47`). The MIS parks news states (`UP/architecture/funnel/solutions/mis.md:85`, `:162`). Ruling R-12 says the guards, the news kill switch included, "work independently of the router" (`00-ledger.md:306`). **[judgment]** CC-21 is worded as news *trading*, but the plan also parked news *protection*.
- **The kill switch does not handle news on the unit path.** Its only trigger is his `kill` change (section 1.1). The old trigger classes `scheduled_news`, `black_swan`, `connectivity` and `unknown_state` exist only in the Book-era fold (`T/qmn/src/qmn/protection/ksa.py:1-9`, `:78-85`), and the app runtime imports only the level names (`runtime.py:130-131`).
- **Built, off the path.** There is a Forex Factory weekly calendar ingest that fails entries closed when stale (`T/qmn/src/qmn/data/news_calendar.py:1-9`). There are pair-scoped blackouts through currency-exposure records, with no live skip (`windows.py:1-10`). Events keep the provider's impact label and its currency or country token verbatim. QMX mints no severity scale (`T/packages/qmf-data/src/qmf/data/calendar_feed.py:262-274`, `:451-462`).
- **A workflow that informs.** `t3-news-calendar-watch` runs at 00:05 UTC. It builds a strip of the day's releases with blackouts 30 minutes either side of each high-impact one, and flags surprises (`TPL/t3-news-calendar-watch/README.md:3`, `:8`). Its watchlist is fixed at EURUSD and USDJPY "until the trading node exists" (`:15`). The free source has no actuals, so live runs find no surprises (`:23`).
- **Tagging by region, session or instrument.**
  - Instrument: every record has `class` (9 values), the quote `currency`, `calendar_ref` and `zone` (`KINDS/instrument.schema.json:50-53`, `:93-94`). There is no base-currency or currency-exposure field. **[judgment]** For FX the base lives only in the symbol.
  - Region: a venue record has a free-text `region` (`KINDS/venue.schema.json:54`). Calendars carry zones per market: `jp-index-cfd` is Asia/Tokyo, `uk-index-cfd` Europe/London, `de-index-cfd` Europe/Berlin, NYSE America/New_York, CME America/Chicago, crypto UTC (`T/extensions/qmf-calendar-*/src/qmf/*/calendars/*.json`, line 5 of each).
  - Session: calendars list real exchange sessions. Osaka, for example, has a day and a night session (`jp-index-cfd@1.json:9-50`). Forex has no Tokyo, London or New York sessions; its day ends at the 17:00 New York rollover (`T/extensions/qmf-calendar-forex/src/qmf/calendar_forex/_provider.py:38-39`). A unit's own `sessions` windows are checked against a calendar (`T/qml/src/qml/check/layers.py:508-513`). **[judgment]** I found no runtime gate on them (no `.sessions` read in `qml/protocol`, `qmb/host` or `qmn/app`).

---

## 3. Paper and live

### 3.1 The paper lane (C-12c)

- A paper deployment takes the same order path as live up to the last step. Then a `PaperAccount` fills the ticket and nothing reaches the venue (`paper_lane.py:1-12`).
- An entry fills at the last closed bar's ask for a long, or bid for a short. The stop fires on bar data, at the open on a gap (`paper_lane.py:42-51`, `:74-86`, `:92-111`). So paper has **zero slippage, no partial fills and no rejections**, except "paper-no-price" (`:95-96`).
- Paper equity is the bound account's equity (`paper_lane.py:71-72`). **[judgment]** A paper unit on a $10,000 demo account sizes from $10,000, whatever share of the $500 seed it will get live.
- It starts from the unit's defaults (`promote.py:245-246`) and journals world `paper` (`runtime.py:2285`).
- **Correction to G6 §5.1.** Node-paper is no longer routing to a paired demo account. The Book-era `qmn/paper/*` is marked "replace" (`node.md:50`).

### 3.2 Promotion on his click (C-23)

- `POST /api/units/promote` answers only to the operator principal. No agent tool reaches it (`promote.py:1-19`).
- A live move from paper carries the paper lane's last calibrated value of each number and the newest watermark. Any number nothing moved keeps its default (`promote.py:237-253`).
- A live-world account refuses a host outside the trading profile, refuses a unit with more than one market, and needs his tick on placeholders (`promote.py:359-381`).
- A second deployment of the same unit version on another market is refused, because "the node runs every market of a unit" (`promote.py:422-447`).
- The paper judge scores each lane by its R and a sequential score. A lane is fresh after 30 trades and 14 days, and ready for his card after 30 trades and 28 days (`T/qmx-agents/packages/qmx-judge/src/qmx_judge/paper.py:1-16`, `:54-59`). **[judgment]** He called 7 days doable and 14 too long (`RC/STATE.md:76`).

### 3.3 Demo and live: does a unit trade the same?

- **The same code.** One compiled unit, one handler (QMB's), one order path and one journal format, in every lane (`runtime.py:16-33`).
- **What differs:**
  - Lane `paper` ends at the simulator. Lane `live` sends real orders and journals world `demo` (`runtime.py:2285`). No world `live` is journalled anywhere yet.
  - The node trades only `("ctrader", "demo")` and `("hyperliquid", "testnet")` (`operations.py:69`). C-12d's cTrader binding "is demo only" and refuses a live host and account (`C12D:qmn/src/qmn/venue/ctrader_account.py:20-21`). Binding live money is C-21, which is not on the stack (`UP/build/UNIT-PLAN.md:4079`).
  - The starting numbers differ (defaults against calibrated values, section 3.2).
  - **On C-12d, cTrader equity is the balance read once at sign-in.** It never refreshes and holds no open profit or loss (`C12D:ctrader_account.py:640-641`, `:718`). PH row 17 says balance plus unrealised. CCXT equity is the USDC total, or 0 when it cannot be read (`T/qmn/src/qmn/venue/ccxt_client.py:597-605`).
- **[judgment]** His "split QMX into demo and live" (`RC/STATE.md:105`) is nearly the built shape already: one code path, with the account deciding the world. The gaps are a live binding, equity that refreshes, and paper that is a simulation rather than demo fills.

### 3.4 Is slippage measured?

- **The data is there, for demo orders.** Each entry's `send` row in the node journal carries the stop and its distance from the reference ask or bid at send (`runtime.py:932-936`, `:982-998`). Its `filled` row carries the venue's price (`runtime.py:1020`). Fill minus (stop ± distance) is the slippage per entry.
- The reconciler also writes `slippage = venue entry price − node price` for each of our open positions (`T/qmn/src/qmn/app/reconciler.py:16-19`, `:301-323`). It runs only once per venue session and after a reconnect or an unknown answer (`reconciler.py:3-6`), so it misses trades opened and closed between runs.
- **No script uses it.** The demo monitor says it cannot measure slippage, because "the fill rows the node writes carry the price filled, not the price asked" (`TPL/dm-demo-monitor/README.md:18`). **[judgment]** That reads the unit journal's `fill` rows. The asked price is in the node journal's `order` rows.
- On Hyperliquid, market orders carry a 5 % worst-price cap. That is a protection, not a measurement (`ccxt_client.py:92-95`).
- **[judgment]** Demo fills come from the broker's demo server, so they are a weak stand-in for live fills. Paper is zero by construction.

---

## 4. MIS, and whether it could drive market-class isolation

### 4.1 What is built now

- **C-08.** The reading code moved to `T/packages/qmf-readings/src/qmf/readings/`, which holds labelers, SQS, liquidity and the regime pipeline.
- **C-09.** The MIS app runs QML statistic blocks and one labeler from per-class packs (`T/qmx-agents/apps/mis/mis_core.py:1-17`). Every class gets the same five readings: CUSUM change point, efficiency ratio, variance ratio and Hurst on H1 bars, plus `spread_state` (`T/qmx-agents/apps/mis/packs.json`). The instrument class only picks the pack (`mis_core.py:643-657`). No cross-market reading exists: no dispersion, herding, currency strength or risk-off measure (grep `cross`, `dispersion`, `strength` in `mis_core.py`). The board lists each market's words and freshness by tier, with no grouping by class (`mis_core.py:880-905`).
- **C-24.** Agents read reading history through `readings_query` and instrument records through `instrument_get` (`T/qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py:1235-1252`, `:1022-1031`).
- **C-22.** The node's board read is per deployment. It names one tier, one reading, the favoured words and `stale_after`. A fresh board with a word not favoured holds new entries on that market (`runtime.py:294-320`, `:423-448`).

### 4.2 The readings a unit gets

The compiler refuses any unit with a `reads` list: "compiler format 1 reads no readings" (`compiler.py:496-497`). A unit can still bind a statistic block into its own logic (the RVOL agent's report, `RC/seeds/operator-words-2026-11-03.md:54`).

### 4.3 Why the board path does not run in practice

- The host's feed relay (`T/qmx-agents/packages/qmx-host/src/qmx_host/feed_relay.py:55`, `:70`) is never started. Its only callers are tests (grep `feed_relay`, `relay(` over `qmx-agents`).
- Promote never writes a `placement` into a deployment (grep `placement` in `promote.py`). Only a hand-written deployment document can carry one.
- A stale, missing or withheld board means "trade every admitted market" (`runtime.py:323-328`). It fails open, by design: "The board is optional to every unit" (`feed_relay.py:10-12`).

### 4.4 Could it drive class isolation?

**[judgment]** Not as built. Four pieces are missing:

1. **A class or region scope.** The kill switch takes only all, account, deployment and instrument, and an instrument must be one a deployment trades (`operations.py:152-172`). Stand-down scopes are `all`, `account:`, `instrument:` and `unit:` (`runtime.py:2172-2179`).
2. **A reading that senses a risk-off move across markets.** None is built (section 4.1). Dispersion, herding counts and currency strength are planned for This PC's MIS (`L0:389`, `:723`).
3. **A trigger that is not his hand.** Only the operator changes a node (`node_link.py:429-438`). The stand-down table's only automatic risk row has no producer (section 1.1).
4. **A fail-closed choice.** The placement read fails open, and isolation needs the other way round.

What is there to build on: every instrument carries its class, calendar and zone. The board carries per-market words. An agent can read reading history and every journal (section 7).

---

## 5. Costs and instruments

### 5.1 What a record holds (C-02)

Instrument fields (`KINDS/instrument.schema.json:42-146`): venue, symbol, market_id, class, quote currency, digits, tick_size, pip, contract_size, value_per_point, value_conversion with a cross-check, lot step, min and max lot, calendar_ref, zone, day_boundary, server_zone, data_levels, expiry fields, roll fields, funding_interval and funding_source, leverage tiers, margin (intraday and overnight), liquidation_rule, swap (long, short, triple day), financing, events, `measured` (an open object) and status.

- **Still no commission key** (0 hits for "commission" in the file).
- The cTrader side reads no commission or swap from the broker (grep `commission`, `swap` in `qmn/src/qmn/venue`, `qmx_host/records.py`, `venue_session.py`).
- The CCXT refresh writes funding clocks and data levels, but no maker or taker fees (`TPL/refresh-ccxt-records/scripts/refresh.py:1-12`).

### 5.2 What QMB can use (B10)

- **A cost profile per market**, keyed by broker, account type and market id. It holds slippage in price points and commission per lot for each of the 168 hours of the week, with the count of our own fills it was measured from (`T/qmb/src/qmb/execution/cost.py:10-13`, `:815-850`). Too few fills labels the run `costs_uncalibrated`.
- QMB reads it from `costs/<market_id>.json` in the run folder (`T/qmb/src/qmb/host/unit_runner.py:11`, `:315-321`). **No code writes one.** The only reader is QMB (grep `parse_cost_profile`, `cost-profile/1`).
- Backtests read bid and ask bars, so the spread is in every run (`unit_runner.py:8-10`). Synthetic spread for trade-only bars is keyed by instrument, hour and session, with no rates set (`T/qmb/src/qmb/execution/spread.py:1-9`).
- Swaps, financing, funding and dividends are cash events from the record (`unit_runner.py:24-30`).

### 5.3 Measured cost data that exists today

- The node writes market `bar` rows with bid and ask OHLC per market (`T/qmn/src/qmn/app/feed_keeper.py:205-216`). Spread by hour can be derived from them.
- Slippage per demo entry can be derived from node `order` rows (section 3.4).
- The market `minute` kind is defined (`T/packages/qmf-data/src/qmf/data/journal_kinds/node.py`, the `MARKET` specs). I found no writer in source; `journal_query` reads it for context (`T/qmx-agents/packages/qmx-tools/src/qmx_tools/journals.py:268-277`).

### 5.4 What could feed sizing

**[judgment]**

- **Per market and instrument:** the record's contract facts, swap and margin. Measured spread and slippage by hour of week, once a script writes the cost profile from bar and order rows.
- **Per time of day:** the cost profile's 168 hourly buckets. Calendars give session opens in each market's own zone.
- **Per timeframe:** no field exists, because the bar size belongs to the unit version (G7 §5.3). Cost divided by stop distance would carry the timeframe into sizing, since a shorter timeframe means a smaller stop, so the same cost weighs more in R.
- **The sizer itself sees none of it.** It receives equity, entry, stop, the record and its own parameters (`T/qml/src/qml/protocol/unit.py:754-764`). Its account facts are equity only (`unit.py:140-142`). The slot contract also lists balance, open risk and the unit's own record in R (PH "What the slots accept"); none of these is passed.

---

## 6. Many units on one account

- **No allocator.** The `bms`, `pod` and `book` Library kinds are empty shells (`KINDS/bms.schema.json` has `"properties": {}`; `pod.schema.json` has only `slots`). The Book and BMS code in `T/packages/qmf-risk/src/qmf/risk/` serves the Book replay (`T/qmb/src/qmb/host/book_handler.py:1-7`), not the unit path.
- **Equity per unit.** A unit starts from the venue's equity (`runtime.py:2307`). After that, its equity is that start value plus its own closed trades and cash (`unit_handler.py:344-346`). **[judgment]** Two units on one $500 account each size from $500, and neither sees the other's losses.
- **No open-risk sum.** `open_risk` is computed nowhere (grep over `qml`, `qmb`, `qmn` source).
- **No same-bet check.** The cross-unit hook passes every order (`runtime.py:1010-1013`). A workflow for it exists as a draft: `rk2-correlation-drift` turns positions into currency legs in R and trips on correlation drift, effective bets or a currency limit. It "waits for the trading node" and installs only as a draft (`TPL/rk2-correlation-drift/README.md:3-10`; `TPL/catalog.py:197-204`).
- **No netting check.** PH row 21 says two units on one symbol of a netting account are refused at deploy. I found no such check (grep `netting`, `hedging`, `position_mode` over `qmn/app` and `qmx_host`). Promote refuses only a second deployment of the same unit version (`promote.py:422-447`).
- **Portfolio study.** `p1-portfolio-combination` would compare equal weight, inverse volatility, risk parity and HRP. It needs `trading-node` and `risk-session` (`TPL/p1-portfolio-combination/README.md:3-9`; `catalog.py:226-231`).

---

## 7. Evidence a live-drift detector could read today

### 7.1 Records

| Record | Holds | Where |
| --- | --- | --- |
| Baseline card, frozen when a unit passes (B13) | `record_r` (trades, total, mean), a Monte Carlo cone of summed R at 25, 50, 100 and N trades (p5, p50, p95), `trade_rate.per_week` | `T/qmx-agents/packages/qmx-judge/src/qmx_judge/judge.py:829-874` |
| Unit journal `trade` rows | entry, exit, stop, quantity, exit kind, money, R, `gap_through_stop` | `qmb/results/journal.py:397-418` |
| Unit journal `fill`, `guard`, `signal` rows | fill price and size, residue in R; every blocked decision with its reason code | `journal.py:352-395`; reason codes `journal_kinds/unit.py:42-71` |
| Unit journal `calibration` rows | each number's old and new value, with its watermark | `journal.py:322-337` |
| Unit journal `lifecycle` rows | paper, live, stopped, resume | `stand_down.py:642-658` |
| Node journal | `order` (send, filled, unknown, rejected), `reconcile` (with slippage), `stand_down`, `kill_level`, `protection`, `node_lifecycle`, `passport` | `journal_kinds/node.py:30-53` |
| Market journal `bar` rows | bid and ask bars per market | `feed_keeper.py:205-216` |
| Reading history | MIS words and values per market | `readings_query`, `functions.py:1235` |
| Library `trade` items and `paper-run` items | trades projected per world; paper lanes scored | `T/qmx-agents/packages/qmx-host/src/qmx_host/records.py:23-26`, `:562-618` |

**A gap in the trade records.** The Library `trade` kind has `session`, `streak`, `equity_before`, `costs` and `mae_r` (`KINDS/trade.schema.json:142-170`). The journal row that feeds it carries none of them (`journal.py:402-418`), so the projection stores nothing there (`records.py:601-609`). PH row 29 says trade rows carry them; at the tip they do not. Nothing writes `would_have` or `risk_event` rows on the unit path (grep).

### 7.2 Workflows that already watch

All of them inform only.

| Workflow | What it does | Source |
| --- | --- | --- |
| `dc-decay-and-limit-report` (B20) | nightly at 00:30 UTC. Compares the last 20 trades with the unit's own earlier record. Alarm at recent expectancy ≤ 0 R while the record is above it, or at 8 losses in a row. Watch at 0.25 R below the record, or at 5 losses in a row. Lands tighten-only cards. Cannot read the baseline card | `TPL/dc-decay-and-limit-report/README.md:3`, `:9`, `:15-17`, `:21` |
| `s5-live-day-replay` (B14) | replays a live day on QMB and diffs decisions. Under a 0.80 match it lands a `bench` card | `TPL/s5-live-day-replay/README.md:3`, `:9`, `:16` |
| `dm-demo-monitor` | fills, residue and gap stops per demo unit | `TPL/dm-demo-monitor/README.md:3`, `:18-19` |
| `s2-tag-units-to-markets` | R per market under each reading word; proposes `drop_market` | `TPL/s2-tag-units-to-markets/README.md:7`, `:11` |
| `gw-guard-watchdogs` (B21) | every 5 min, gives each node a word: Alarm, Watch or Well | `TPL/gw-guard-watchdogs/README.md:10-11` |
| C-18 phone wake | ntfy pushes for protection, risk stop with open trades, broker link, clock halt and healing; Healthchecks liveness | `alarms.py:1-20`, `:120-128` |

### 7.3 What it adds up to

**[judgment]**

- The pieces for "is live inside what the backtest promised" exist: the baseline cone, live and paper R, the trade rate, and per-word records.
- They are not joined. The decay check uses the unit's own past, not the cone. Its README says scripts cannot read Library items.
- Every output is a card for his click. Nothing can size a unit down, and the one automatic move, the risk stop, can only stop.

---

## 8. Where the stack changed G6 and G7

1. **G6 §3.2-3.5 and §5.5.** Door, windows, SQS, bench and kill line were "built" in shipped code. They still exist, but the new unit node imports none of them (`runtime.py:111-131`).
2. **G6 §5.1.** Node-paper as demo routing is replaced by a simulated paper lane (section 3.1).
3. **G6 §5.4 "nobody measures slippage".** It is now measurable from node rows, and partly written in reconcile rows (section 3.4).
4. **G6 §3.5 kill switch "four trigger classes".** On the unit path it is his hand only, with placeholder effects (section 1.1).
5. **G6 §6 restart rules.** The stand-down table now decides restarts: four rows clear by themselves and three wait for him, risk stops among them (section 1.2).
6. **G7 §1.1.** B13's verdict, baseline card and proposal card are built (`judge.py:829-874`).
7. **G7 §2.6.** C-08, C-09, C-22 and C-24 are on the stack, with the gaps in section 4.
8. **G7 §2.4.** The `reads` model exists, but the compiler refuses it (`compiler.py:496-497`).
9. **G7 §4.3.** The cost ports now have a per-hour cost profile shape (section 5.2), with no producer and still no commission key.
10. **G7 §1.1 `trade` v2.** The Library kind has the fields; the journal rows behind it do not (section 7.1).

---

## What his brake and isolation ideas could hang on

**[judgment]** throughout, but every anchor is cited above.

- **A unit circuit breaker** (his "2 full stop losses, you stop trading"). The anchors:
  - the risk-stop pipe: a journalled event, survives restarts, waits for his resume (`stand_down.py:550-595`);
  - the halt slot and its contract, `none`, `no_new_entries` or `flatten` (`api.py:167-185`);
  - the halt blocks, with `stoploss-guard-halt` the closest match to "N stop-outs in a lookback" (`stoploss-guard-halt.json:15`);
  - the old rule for comparison: 2 hits a day, then paper (`RC/grounding/G3-old-system.md:184-187`).
  - Two hosts must feed the halt inputs: the node and QMB, so backtests match live.
- **Alpha decay from breaker density** (old WF3). Every `stand_down` start row and every `lifecycle` row by `risk_rule` is journalled and comes home, so a fire count per unit, market and week can be read. The decay check is the natural home (`TPL/dc-decay-and-limit-report/README.md:3`), once the risk-stop reason code is fixed (section 1.4).
- **"Size down, but not quickly."** Numbers can already move slowly. Calibrated numbers move one step at a time, inside a range, after a minimum count (`L0:257`), and every move is a `calibration` row. A sizer number could follow the drift evidence the same way. Today a risk rule can only stop (`machine.py:104-122`).
- **A BMS breaker that switches everything off.** The kill switch at `all` (BLACK closes all and pauses) and the `all` stand-down scope already exist. What is missing is an automatic trigger and an account or portfolio statistic (section 6).
- **Isolating a market class** (crypto, indices, FX).
  - Instruments already carry `class`, `calendar_ref` and `zone`, and calendars carry regions.
  - A new scope key such as `class:` beside `instrument:` would fit both the kill switch (`operations.py:152-172`) and the stand-down table (`runtime.py:2172-2179`).
  - The evidence could come from MIS cross-market readings (planned, `L0:389`) or from per-class SQS and spread states.
  - An agent can already read readings and journals and land a proposal card (C-24, the slow lane), which matches "it should kick in with evidence".
- **News by instrument and region.** A fail-closed calendar ingest, currency-exposure blackouts and provider impact labels are built (section 2), but parked. The t3 strip already makes ±30-minute blackouts per currency.
- **The same unit on demo and live.** It is already one code path, with the world set by the account (section 3.3). Slippage evidence on demo can be read from node order rows.

## What is missing

1. Any producer of a risk stop: no halt is compiled or hosted, and no rule calls `risk_stop` (`compiler.py:498-499`; `api.py:181-183`).
2. Host-side halt inputs: day-start equity, losing-day streak, session fills and session loss in R.
3. Any automatic or agent trigger of a kill level or stand-down. Today it is operator-only (`node_link.py:429-438`).
4. A class, region or session scope in the kill switch, the stand-downs or the board read.
5. Cross-market readings in the MIS: dispersion, herding, currency strength, any risk-off sense. SQS and volatility state are not in any pack.
6. The board relay wired, and a fail-closed placement option.
7. News on the unit path: calendar, windows, impact-to-instrument mapping. All parked.
8. A spread-against-cost guard before each order (`L0:383`).
9. A flatten that works (`operations.py:379-380`).
10. The spec-change stand-down raised by a record change.
11. Config and UI keys for every stand-down and kill-effect number. Today they are code constants.
12. An account view across units: open risk, a share of equity per unit, correlation or same-bet checks, a netting refusal. Equity that refreshes on cTrader (C-12d).
13. A commission key on the instrument record, a writer of cost profiles from bar and order rows, and cost inputs to the sizer.
14. Trade rows carrying session, streak, equity before and costs.
15. A slippage script over node order rows. A paper lane that models slippage.
16. A drift check that reads the baseline cone. Any action after a drift alarm other than a card: no automatic demote to paper, no size step-down.
17. A live-money binding (C-21) and journal world `live`.

## Not covered

- I ran no code and no tests. Branch facts come from reading files at the tip and `git show` on C-12d.
- I did not read QMB's `replay_check` job, the template scripts past their READMEs, or the old host modules beyond their headers.
- I did not re-check the old system's circuit breaker beyond G3's summary.
- I did not check whether cTrader's API offers commission or swap per symbol. **[judgment]** It likely does, but that needs a primary source.
