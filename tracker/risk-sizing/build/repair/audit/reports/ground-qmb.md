# Grounding: QMB, the Library's data, the market store and the judge
Commit `50c83a4e`. My proof scripts and their output folders are in `D:/Temp/audit/ground-qmb/`: `bridge.py`, `records.py`, `delta.py`, `holes.py`, `reach.py`, `ov.py`. Levels are the ladder in the system prompt. Every "ran" below was run by me at this commit.

## 1. What this area is and how it really works
A backtest starts at one of two doors, the copilot's `backtest_run` row or a workflow's `app_op`, and both reach the supervisor's `run_job`. The host's `QmbRun` is the lander on that path. It compiles the unit from the Library, checks that bars exist, and calls `qmx_judge.Lander.open`, which runs the behaviour check first if this compiled unit has no G report, mints the run id and lands the `opened` try. `QmbRun._lay_out` then writes `in/` in the app's volume: the request, unit, blocks, records and two bar CSVs per market. The QMB app is a child process that only reads that folder. Its job calls `qmb.host.unit_runner`, which compiles again, scans for holes, and drives one shared handler (`unit_handler.py`, the same file the node runs) through the older `runloop.run_slice`. The job leaves a bundle, the lander checks every file, lands the `backtest-result` and closes the try. The judge (`qmx-judge`) reads landed results, applies its chain, shrinks each market toward the unit's whole result, and the host's lifecycle writer turns the verdict into draft to tested or parked. Beside this sits the market store: one door (`MarketDoor`, built before this plan) that downloads commit to and readers read from, with holdouts and fingerprints. **The new run path never touches that door.** Under all of it sit about 96,000 lines of older QMB. A proved copy needs about 39,000 of them (section 3, Old door).

## 2. What must not break
- The handler and its money rules: `qmb/tests/test_unit_handler.py` and `test_unit_runner.py` (15 passed, ran), `test_realism.py`, `test_fidelity.py`, `test_futures_rolls.py`, `test_windowed_reader.py`. The node imports the same handler, so **a change to how `r` is computed changes the node's calibration too**.
- The tester reads only its run folder, and the core mints the run id. A refused run lands no try. Pins: `test_qmb_app.py`, `test_landers.py`, `qmx-judge/tests`.
- `[qmb] bars` keeps working. `test_qmb_app.py` and `test_qmb_run_kinds.py` run on it, and the 29-trade owner month came from it.
- `gather`'s fixture fallback and its exact warning text: `test_unit_library.py:195`, `test_market_kinds.py:280,313`.
- The door: a full read refuses a sealed month, a commit is the only write, and fingerprints verify. Pins: `qmx-host/tests/test_market_data*.py`. `materialise` into a folder is also used by the Lab (`qmx_control/lab.py:451`), `d6-ml-training-run` and `data-quality`.
- `bar-m1` readers: the MIS (`apps/mis/mis_core.py:475`) and `download-ccxt`.
- The judge's rules: `test_judge_verdicts.py`, `test_lifecycle.py`. Its numbers come from `t["r"]` (`judge.py:259`).
- Workflow engine and mini-app core: nothing below needs an engine edit, and only one item goes near the supervisor's queue (p0b-14).

## 3. The problems
### A run on his facts: seams-2, p0b-1, p0b-2, p6-2 (records part), p5d-5. One cause, plus two neighbours.
**Real cause.** `_lay_out` copies a QML test fixture chosen by venue and symbol (`host.py:1829-1838`, `:1949-1952`), though `gather` has just read the Library's item (`gather.py:154-160`). Confirmed (ran, `records.py`). With a C-34 record on main, the host compiled against the item and the folder got the fixture. A GBPUSD unit compiles on the host, `records laid []`, and the tester refuses `no instrument record was given for fx.gbpusd`.

**Why C-02 did not switch it (you asked).** It could not. C-02 and B6 were built side by side, each on its own older base. C-02 was built on A7 (`unit-ship/decisions.tsv:113`). B6 was dispatched at 01:00 on A8's first head, which held no C-02 (`:126`, A8 itself on A7). So B6's builder really did see fixture-only `gather`, and it wrote "until C-02" truthfully. C-02 landed below B6 only at the later rebase (`:130`, `:132`, `:134`), and that check looked at text conflicts ("range-diff shows only one import line"). So the sentence was already false the moment B6 joined the stack, and nobody was left to act on it. Four things let it through:
1. The plan never made B6 depend on C-02, and C-02's Files block names only `gather.py`, because `_record_file` did not exist when the plan was written.
2. B6's note went to `evidence/b6/findings-backlog.md:4`, and C-02 was finished by then.
3. C-02 kept the stale warning on purpose (`FIXTURE_WARNING`, its owner-decisions row, because a test outside its files pins the text), so the code still told readers C-02 had not landed.
4. `LanderLibrary._compiled` throws `gather`'s warnings away (`.context` only, in `host.py`), so a run on a fixture says nothing.

**Does it repeat?** The literal form does not. A search of the build's source and every `findings-backlog.md` for "until <section>" finds only this one line plus the warning text. The shape does repeat, as **a promise in a comment or backlog with no owner**. Named here: script steps' `library/instruments` and `library/cards` files never become items (c02 backlog line 1, which is the root of p0b-8 below), `[node] record_markets` (p5d-5), `[qmb] default_tester` (p2-7), and `market_minute` with no writer (p34-5). Planner's take-away: chained builds need one check at stack time, "does anything below me make my stop-gap false?"

**What is around it.** Only `_lay_out` calls `_record_file`. `load_unit_folder` already reads each record file's raw JSON for carry terms (`unit_runner.py:340-346`), so the raw Library item is the shape it wants. Gold's and GBPUSD's keys all parsed (ran).

**The one safety fact, level 4.** The compiled fingerprint holds no records, so swapping the record file keeps the pin and the G report valid. Ran: repaired folder "same compiled fp as host True". With no item on main, the fallback path stays the fixture, so the shipped suite is unaffected (level 3, by `gather.py:161-164`; the long test run below confirms it). A planted gold lot step of 0.10 moved the real-month result from 29 trades, +22.84 to 21 trades, -169.04, so this is not cosmetic. The numbers are from my planted record, not from his broker.

**Trap the repair must take (new, level 4).** `LanderLibrary.unit` caches per pin "because an object never changes" (`host.py`, above `_compiled`). But the records it gathered do change. Ran: the record moved on main to min lot 0.05, the same host still answered 0.01 version 1, and a new host answered 0.05 version 2.

**Repair shape.** One place, `gather`. `Gathered` also hands over each market's raw record document (the item's fields with `record_version`, or the fixture's). `RunUnit` keeps it. `_lay_out` writes it. Delete `_record_file` and its import. Key the cache on the pin plus the record versions, or re-gather on each open. Carry a fixture warning into the request and into the result's labels.
- **p5d-5.** Read `[node] record_markets` and `records_refresh_s` at the two build sites (`host.py:1129`, `connect_node.py:725`). `Market` already holds what a setting row needs. Without this a real GBPUSD record never exists, so the first fix only helps markets C-34 lands.
- **p6-2, records part.** `check.py:32` (two copies, `_shared` and `b-build-and-prove`) calls `checked(None, …)`, because a script may not open the Library. The lander compiles the same pin with the Library before any try lands, so the child adds no safety on these points. Shape: in a Library-less check, `no_record` and an unfound pinned block become "not checked here" rather than errors, and `ready.py` stops treating them as fatal. `test_templates.py:1064` pins today's words. The engine is not touched. Unproven; `D:/Temp/audit/p6/gate_proof.py` is the before-and-after.

**Proof.** Add an instrument item to the real store in `test_qmb_app.py`, whose store today holds none, which is why this stayed green. Assert the run folder's record equals the item, and that a fill uses its lot step. It fails today. `records.py` is the fast form.
**Order** first. **Files** `gather.py`, `host.py`, `venue_records.py`, `connect_node.py`, two `check.py`, `ready.py`. **Size** about 80 added, 130 removed (p6-2's own count). **Whose** ours.

### A run on his data: p0b-3, p2-4, p2-2, p2-3, p0b-9, p0b-17, p5d-4, triage-2, p2-13, p2-9
**The three shapes, side by side (ran, `bridge.py`).**

| | What the download template writes | What the market door serves | What QMB's real run reads |
| --- | --- | --- | --- |
| Where | `<home>/market/series/dukascopy/<SYMBOL>/ticks/-/<YYYY-MM>/` | the same files, by series or by fingerprint | `in/bars/<market_id>/bid.csv` and `ask.csv` in the run folder |
| Unit | one month, one file (`open.parquet` or `<fp>.parquet`) | `read`: rows, or a JSONL handle past 5,000 rows. `materialise`: a verified copy `<fp>.parquet` | one file per side for the exact window. `_bars` needs the file name to hold that exact start and end |
| Columns | `t` (ms), `bid`, `ask` (whole numbers), `bid_volume`, `ask_volume` | the same. `card()` adds months, fingerprints and gaps, and **no price scale** | `timestamp` (ms), `open`, `high`, `low`, `close` as decimal text |
| Grain | every tick, both sides in one row | as stored | closed bars of the unit's stream only |
| Price scale | whole numbers at the scale the source names. The scale is written only to a run artifact `library/cards/<series>.json`, which never becomes a `dataset` item (only `scripts/data/import_old_ticks.py` calls `write_card`, and its card has no scale) | not known to the door | already decimal |
| Holdout | none | `read` refuses a sealed month. **`materialise` into a folder copies it** (new, below) | none: whatever is in the folder |

Other sources: `download-ccxt` writes one-sided `bar-m1`, and `import_old_ticks` writes `risk-lab/<symbol>/bar-m1/<bid|ask>` pairs. Nothing reads either for a run.

**The smallest bridge.** QMB already turns ticks into bars. `replay_feed(_QUOTES, rows, BarBuilder)` takes `Tick` and `BarPair` rows, and its `BarFeed` is just "something that yields bars", so nothing past the feed changes.

**The one safety fact, level 4.** Ran on the real March 2025 EURUSD and XAUUSD files, through the real door: commit, `materialise`, feed. "csv bars 2028, tick-built bars 2028, identical True" and 1940 for gold. The full run gave "29 trades, net 22.84, R 0.9847" on both paths, "same trades True". Limit of this proof: my ticks were cut from those bars (four per bar), so it proves the path, not that Dukascopy's real ticks agree with dukascopy-node's bars.

**Shape.**
- `QmbRun` gets the door (the host already builds it, `host.py:1627`).
- `_bars` looks first at a named `[qmb] bars` folder (test and hand-saved route stays). Otherwise it asks the door for the market's series and months and refuses by naming each missing month and `download-dukascopy` (LD-06), dropping the stale dukascopy-node wording.
- `_lay_out` copies the partitions to `in/data/<market>/` with a small `card.json` (series, scale, fidelity, window).
- `load_unit_folder` picks `_BarFiles` or a new tick or pair feed of about 25 lines that clips to the window. `until_ns` comes from the window, so the last bar closes.
- The scale: one line in `download.py` beside its existing `ClockLedger` write (`download.py:385,414`, per-series file under `<root>/.clocks`), read through the door. A series with no stated scale is refused by name. That makes C-31's plan line "a QMB backtest over it is refused" true (p5d-4), and his old imported months need one `check` or re-download.
- The same `_lay_out` lands the `dataset` card with `write_card`, which is idempotent, and records its object id. That gives p0b-8 its `consumed` edge with no template or engine change.

**How long it takes (measured, synthetic prices).** 800,000 ticks: verified copy 13.1 s, ticks to bars 80,581 a second. A real EURUSD month at about 3.5M ticks (my guess) means about a minute to copy and about 45 s per read, per market, and a first run reads three times (check, hole scan, run). A year of two markets is then over an hour (24 market-months at about 3 minutes each, resting on that guess). `BarPair` rows fold at 156,012 a second with the same bar count, and a month is about 30,000 of them. So: **PR one reads ticks and pairs. PR two adds a derived step that writes `bar-m1` bid and ask next to the ticks** (the door's docstring names "a derived-data step"; the MIS wants these too). The reader does not change. Do not tie the bridge to ticks alone.

**The rest of this group.**
- **p0b-9, easier than graded.** Ran: `run_loaded` with only EURUSD's feed gave "14 trades, ['fx.eurusd']" and no error. `load_unit_folder` needs to skip feeds the request does not name, and `_bars` needs to stop refusing. Compiled fingerprint unchanged. Size S, not M. The result must name its markets, because the judge reads `r.markets`.
- **p0b-17.** Cut B4's entry (650 product, about 547 test). The bridge does not use it. It reads one partition at a time and builds whole-history frames. Its removal also ends p5d-4's read half, the hard-coded scale 5 (`replay.py:105,908`), which only that entry reaches.
- **p2-2.** Wire `Bar` rows (one-sided, with a declared spread) when a one-sided source first needs a run. Change the label now: every job says `fidelity: bars` while the run is quotes (`backtest.py:218`).
- **p2-3.** Keep the 230 lines, wire later. No futures data route exists yet, and it harms nothing while idle. `stream.py` stays with it (Old door below).
- **p2-13.** A month with one empty open hour freezes silently. The run's hole scan catches it later (one m15 hour is 4 bars, past the limit of 3), but the fix then needs a correction. Make `calendar` default from the source in all three templates. S.
- **p2-9 and triage-2 must land together (found by running).** A check at the window's ends looks one line long, but on real January data it would fail. Ran: real EURUSD Jan to Mar has 88 "missing" open bars before its first bar, because the calendar reads 1 Jan 2025 and 25 Dec 2024 as open, and it reads 25 Dec 2026 as shut. Shape: label `data_short` first and refuse only once past closures exist as data. Past dates in a calendar file cannot change a live decision, because the node asks only about now (level 3).
- **Correction to triage-2 (ran, `holes.py`).** Real EURUSD Jan to Mar 2025 has **0** holes past the limit, so "stops most long runs" is not shown. Mid-window Christmas is still untested; see Needs a long run.

**Trap: the door's holdout (new, level 4).** Ran: `read` refused the sealed month, and `materialise(into=…)` with the same holdout "COPIED 1 file(s)". That is by its docstring, for a final look's attempt folder. So laying a run out through `materialise` alone would open the very leak p0b-11 is about. Add a small door method that answers which months are sealed for a holdout and run, and call it before copying. Do not change `materialise` itself, because the Lab, d6 and data-quality use it.

**Proof.** Fresh home, GBPUSD record on main, ticks committed through the door, real app under a real supervisor: lands a finished result with a `consumed` edge. Today it refuses at `_bars`. **Order** after the facts PR. **Files** `host.py`, `market_data.py`, `unit_runner.py`, `replay.py`, `backtest.py` and sibling job labels, `download.py`. **Size** about 150 added, 650 removed. Derived bars about 50 more. **Whose** ours.

### Costs: seams-9, p2-8, seams-10, p0b-13, p2-6, plan-check-3, p34-5
**Real causes, three layers.**
1. `_lay_out` copies no `costs/` or `funding/` (`host.py:1920-1956`).
2. Nothing makes a profile. `minute` rows have no writer (`feed_keeper.py` writes only `bar`; `journals.py:285` reads an empty answer).
3. `r` is price money over risk (`unit_handler.py:630-635`), and cash goes only to `net_money` (`unit_runner.py:486-488`).

The node's `records` answer holds no swap or commission (`server.py:904-924`, and a search of `ctrader_account.py` finds neither word).

**The one safety fact, level 4.** The runner already does all of this given files, with no code change. Ran: commission 3.50 a lot moved net from -169.04 to -249.91 with **R unchanged at -4.3841**, 42 cash rows, and the label stayed `costs_uncalibrated`. Swap on the record gave a swap row and net -171.59 with R unchanged. After the facts PR, a swap on the Library item reaches the run by itself. Its `triple_day` is a full weekday name ("wednesday"; "wed" is refused).

**What can be done without deciding how R treats costs.**
- Copy a stated profile in `_lay_out` when the study's `cost_rule` or the request names one (`CONTRACTS.md` §2 allows a Library pin). It stays uncalibrated, which is honest. S.
- Per trade, add the trade's cash and a second number beside `r`, keyed by the cash event's `position_id`. Leave `r`, `total_r`, `r_after_costs` and the judge exactly as they are. Put the judge's read behind one named function so the risk session can flip one line.
- Show `costs_uncalibrated` in the verdict (p2-12 below).
- Node side, later: swap and commission from cTrader's symbol, and a `minute` row once a minute in the feed keeper, then a host step that turns rows and fills into `qmx.qmb.cost-profile/1`. The hot path is Part C's. Do it after the journal repair (seams-3), and only C-15's demo can say what cTrader's fields mean.

**Hand to the risk session.** Whether R includes costs (RC:322, RC:342), and the misleading name `r_after_costs`, which is in Part A's contract. Not ours to rename alone.
**Proof.** A run with a stated profile shows net changed and R the same, from a real app run. **Order** after the facts PR. **Files** `host.py`, `backtest.py`, `unit_handler.py` (adds only). **Size** about 60 now; the node part about 150, later.

### Study rules: p0b-10, p2-10, p0b-11, triage-6, p2-5, p2-11
- **p0b-10 and p2-10 (same line).** Ran: "study False, chat True, run reads True". `host.py:1934-1935`: when a named study states `allow_gaps`, it goes after `**ticket.request`. With no study, or a study that does not state it, the chat still decides, because `test_qmb_run_kinds.py:56` and `test_qmb_app.py:57` send the chat's value. A search of `allow_gaps` in tests finds none that pins the chat beating a study; the long run confirms. A few lines, his decided ruling [TR:57]. Do it first.
- **p0b-11.** Understated. Beyond the copied bars, three things are in the way: the sealed-copy trap above; the study's `holdout` is typed as a plain string (`study-spec.schema.json:99`), while the door takes only `"off"` or `{boundary, months}`, so any real value refuses; and the door's holdout must be passed with `run=` so one run stays one seal. Build it inside the data PR, because `_lay_out` is the one place. Harmless while holdouts stay off, the default.
- **triage-6.** `journals.py` reads the store directly. Apply the door's Settings default holdout to the rows it serves, or refuse with its reason. An agent read has no study, so a per-study seal cannot apply there (LD-08's "optional study"). S.
- **p2-5.** Two gaps: `land_spec_edit` looks only at earlier versions of the same item (`host.py:888`), and `judge` lets the spec narrow the market list (`judge.py:706-709`), against judge.md's "none is dropped for looking bad". Shape, one place in `judge_run`: a written study first made after any of the results' tries lands a counted `spec_edit`, and the shrink always uses every market the results traded. `quick_spec` must stay exempt, since it is written late by design. Reuses the existing try kind. Unproven until `p2/p3/shrink.py` flips.
- **p2-11.** `_evidence` takes the first result's whole-run number (`judge.py:496-497`). Real fix is per-market evidence from `unit_battery`. M. Do after the running-well group, because it rewrites the same loop as p2-14.

**Order** one line first; holdout with the data PR; judge items in their own PR. **Whose** ours; the judge is not a guarded part.

### Backtest against live: seams-7, seams-8
- **seams-7.** Not re-run; the seams proof (`seams/wick.py`, +2.00R against -0.55R on one wicked bar) stands. This is an exit rule, so it goes to the risk session. No repair here. Do not change QMB's fill to match in the meantime, because the dummy's numbers rest on it.
- **seams-8.** Two faults.
  - `route.py:32` filters world `live`, while the node writes demo and paper (`runtime.py:2420`, read). Fix: ask for each lane's worlds. S, template only.
  - The recorded bars. The node's `bar` rows hold full bid and ask OHLC and `knowable_at` (`feed_keeper.py:208-213`). They reach the store as `journal-market` partitions with a JSON `record` column. Shape: for `replay_check`, `_bars` reads those rows through the door and writes the same `bid.csv` and `ask.csv`, so QMB changes nothing, and a day's bars are few enough to convert in the host.

  It needs seams-5 first (the node records only 15-minute bars), and a day's warm-up reaching back 921 bars. Level 2 on the row shape; the end-to-end needs a recorded day.

### Running well

| Finding | Real cause, confirmed unless said | Repair shape | Size |
| --- | --- | --- | --- |
| p2-1, p2-16 | `_preflight` builds a list (`unit_runner.py:508-513`), while `find_holes` takes any iterable | A generator that stops on a refusal; point the memory test at `run_loaded` | S |
| p0b-7, p2-14 | `check_behaviour` holds all bars (`behaviour.py:70`); it needs only `needed` bars | The check takes the first `needed` bars. The behaviour half never gates a run, only safety does. `robustness.py:58` truly reads random spans (`unit_battery.py:107`), so it needs compact arrays, not a slice | S + M |
| p0b-5 | `landing.py:480` passes `motion: both` into the check | Force `on` for the check; add `both` to the row (`functions.py:195`) | S |
| p0b-6 | `service.py:307-317` catches only `ControlError`; the run id exists only after the check | Catch everything in the worker. A slow first run answers `checking` with the check's run id, and a poll on it names the run once opened. Service only | S |
| p0b-8 | The tester names no `consumed`; **no `dataset` item exists to link** | Comes with the data PR, core-side in `QmbRun.close`; hash `request.json` for `request_fp` | S |
| p0b-12, p2-12 | `compiled.placeholders` is dropped at the job's labels; `functions.py:350` passes none | Add to labels; pass them to `land_judgement`; put `costs_uncalibrated` in the verdict's words | S |
| p0b-14 | Confirmed; the waiter thread dies with the host; `bootstrap.py:226` then runs any leftover request with nobody to close it | At host start, before apps start: each `opened` try on this machine with no close gets `fail("host restarted")`, and its request file is removed. Host only, supervisor untouched | M |
| p0b-15 | `backtest.py:101-113` lists six measures. `results/measures.py` (981 lines, the 27 money measures the contract names) has no caller on this path | Reuse it for money. Track MAE, MFE and drawdown in R in the handler, adds only. M | M |
| p0b-16 | Nothing guards `run_loaded`; a raise counts toward the breaker | Catch in `_run`; land `failed` with the type and message. The node's path is untouched | S |
| p2-7 | Nothing but tests calls `run_conformance`; `_check_default_tester` (`service.py:1152`) can refuse forever; `service.py:310` always runs `qmb` | **Leave for now.** Nothing hurts until a second tester exists. Then: a job door and one read of the setting | leave |
| p2-15 | `host.py:1956` copies; nothing cleans | In `QmbRun.close` and `fail`: remove `in/bars` and `in/data` after landing. Tests read `in/request.json`, so keep it. Supervisor untouched | S |

**The one safety fact.** The feed is opened fresh on each read (`LoadedUnit` docstring, level 2), and `motion = both` already relies on that, so none of these changes what the unit sees. p2-1's measurement stands (`p2/p1/mem.py`). **Files** `unit_runner.py`, `behaviour.py`, `landing.py`, `service.py`, `functions.py`, `backtest.py`, `host.py`. **Size** about 250. **Whose** ours; `landing.py` is in `qmx-judge`, not a guarded part.

### The old QMB door
**Measured, not by graph alone (`ov.py`, on the deletion auditor's copy that loaded all 9 jobs and passed the runner tests).** Kept 38,871 of 95,987 lines, gone 57,116. Deletion's 63,840 is its by-name graph claim. Use 57,116, the proved one.

| Sub-package | All | Kept | Gone |
| --- | --- | --- | --- |
| host | 15,047 | 2,852 | 12,195 |
| data | 11,181 | 1,698 | 9,483 |
| analysis | 4,662 | 264 | 4,398 |
| optimize | 8,255 | 3,615 | 4,640 |
| execution | 11,614 | 6,833 | 4,781 |
| orchestrator | 4,635 | 220 | 4,415 |
| robustness | 6,967 | 2,724 | 4,243 |
| top (the re-export sheet) | 3,508 | 319 | 3,189 |
| sweep, doors, registryread, config, results, runloop, ledger | 30,118 | 20,346 | 9,772 |

**Old modules used by the new path:** everything in the kept column, chiefly `runloop/loop.py`, `runloop/bars.py`, `execution/fill.py`, `financing.py`, `cost.py`, `data/gap_check.py`, `results/journal.py`, `robustness/walkforward.py`, `optimize/sampler.py`, `sweep/axes.py`.

**Gone, but a living test needs them:** `data/generate.py` 2,132 (`test_realism.py:28`, two functions) and `runloop/stream.py` 853 (`test_futures_rolls.py:29`, two functions). `replay_execution` 939, `replay_request` 980, `execution/binder` 588, `orchestrator/ledger` 586 and `book_handler` 2,858 serve `test_replay_execution.py` and `test_typed_execution.py`. Old-node tests use four more (`config/alternative`, `orchestrator/watch`, `worker`, `replay_request`) and go with C-20.

**What a design wanted kept.**
- The Book path (`qmb.md` §7, "stays for the risk session"): the five files just above, 5,951 lines.
- `generate.py`: the design's synthetic row and QB-16 want it extended. The `synthetic-data` template does not import it.
- `stream.py`: futures, row in `qmb.md`.
- Methods with no job yet, under "keep, wrap as jobs": robustness, optimize, sweep and analysis gone-lines, 15,484 in all, such as `perturbation`, `significance`, `sensitivity`, `project`, `variants`. Read before cutting.
- `results/measures.py` is kept and should get a caller (p0b-15).

**Honest number.** 57,116 proved, less 2,985 (generate, stream), less 5,951 (Book path) gives **about 48,200 that can go**. Of those, **about 32,700 is plain old door** (CLI, orchestrator, old data download and catalogue, old host door, the re-export sheet), and **about 15,500 are methods to read first**. Plus the 14,305 of examples. Arithmetic on line counts, labelled as such. Nothing here goes before the demo evidence and his word. Repoint the two tests only if those modules are cut. **The one safety fact:** the copy's run, level 4 for what it ran, `SPOT-CHECKS.md:56` for the two collection errors.

## 4. Corrections to the audit
- **p0b-1, p0b-2** "C-02 landed and this line was not moved": the order was the other way round. See the C-02 block.
- **p0b-3, p2-4** lean on "dukascopy-node fetches nothing". The README says so, from an old probe, but the build's own real months came from it on 1 and 2 November (`unit-ship/data/dukascopy-node`, `decisions.tsv:144`). The refusal's advice works for one exact window. The finding stands because the template it also names writes ticks, and months do not add up.
- **p0b-8** understated: there is no `dataset` item to link for a downloaded month.
- **p0b-9** size: S, not M (ran).
- **p0b-11** understated: three more obstacles (ran, schema).
- **triage-2** overstated as written: 0 holes on three real months; Christmas untested. Keep it, unproven.
- **p5d-4** the read half is reachable only from B4's dead entry; it goes with the cut.
- **p2-7** real but `leave` for now, not `should`.
- **p2-9** the one-line fix is unsafe alone (88 bars on real January).
- My own proof envs do not hold `qmf-calendar-cme`, so gold reads `holes_unchecked` there. The QMB app's own `pyproject.toml` lists it. Not a defect.

## 5. What "works" means here
Each is a real run across a real connection, and each fails today unless marked. Cases from the catalogue.

1. A fresh home with a market that has only a Library record and ticks in the door: the app lands a finished result that links its dataset card and uses that record's lot step (LD-06, QB-08).
2. The same home with no month: refused before any try, naming the month and the template (LD-06).
3. The same month through a CSV and through the door lands the same `trade_list_fp` (QB-21). The path passes in `bridge.py`; the app run does not exist yet.
4. A record moved on main shows in the next run, with no host restart (LD-05 in spirit).
5. A study forbidding gaps beats a chat allowing them, and a hole fails the run (QB-18, TR:57).
6. A study sealing a month: the run is refused with its reason, and no sealed file sits in any run folder (LD-08).
7. A stated cost profile and swap on a Wednesday hold: net changes, triple swap books, raw R stays, and the verdict says `costs_uncalibrated` (QB-03, QB-04).
8. A 200,000-step real run stays flat in memory through `run_loaded` (QB-01).

Later, needing a recorded demo day: replay of that day matches (QB-23).
## 6. PR clusters, in order
1. **Facts.** `allow_gaps` line, records through `gather`, cached records, `record_markets`, Library-less gate words. About 80 added, 130 removed.
2. **Data.** Door into `QmbRun`, tick and pair feed, scale, card landing and `consumed`, sealed-month guard and study holdout, one market, labels; cut B4. About 150 added plus the guard, 650 removed.
3. **Derived `bar-m1`,** past closures, `data_short`, default calendar. About 100.
4. **Running well.** The table above except p2-7. About 250.
5. **Costs plumbing.** About 60. Then hand the R question to the risk session.
6. **Judge honesty.** p2-5, p2-11, p2-12's verdict words. About 150.
7. **Replay.** After cluster 3 of `REPAIR-SCOPE.md` (seams-5, seams-3): world filter, recorded bars to CSV. About 60.
8. **Later, on his word.** Node's cost data after C-15; the old door after the demo evidence.

## 7. New defects
- **`materialise` copies a sealed month into any folder it is given.** Level 4. Ran: "COPIED 1 file(s)". `d6-ml-training-run/scripts/dataset.py:85` calls it with a folder, so training reaches sealed months once a holdout is on. Harm only when he turns holdouts on.
- **A host keeps the first records it compiled against for its whole life.** Level 4. Ran: 0.01 version 1 after the record moved to 0.05 version 2.
- **A study's `holdout` cannot name a real holdout.** Level 2. Schema string against the door's shape.
- **Every job labels `fidelity: bars` while the run replays quotes.** Level 2. `backtest.py:218`; `apps/qmb/server.py:80` lists `FIDELITIES`, per p2-2 only bars.
- **A run on a fixture says nothing,** though the module's rule is that every read says so. Level 2. `gather`'s warnings dropped in `LanderLibrary._compiled`.
## 8. Set aside for him
- Does the old QMB door go after the demo? Default assumed: yes for the 32,700 plain lines; the 15,500 of methods get read first; the Book path and the two test-used modules stay. Same question the audit already holds; these are its better numbers. The planner's note says later, with evidence. Futures: assumed keep and wire later (his "design for futures" stands), not a question now.

## 9. Needs a long run
Prefix each with `source D:/QMX-worktrees/audit-ship/tools/env.sh && `.

- Baseline of the app suite before any repair. Fixture path must stay green: `cd D:/QMX-worktrees/audit-head/qmx-agents && timeout 1500 "$AUDIT_AGENTS_ENV" -m pytest apps/qmb/tests/test_qmb_app.py -q -x -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/ground-qmb/l1`
- The door's own tests: `cd D:/QMX-worktrees/audit-head/qmx-agents/packages/qmx-host && timeout 600 "$AUDIT_AGENTS_ENV" -m pytest tests/test_market_data*.py -q -x -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/ground-qmb/l2`
- Whether Christmas reads as a hole, and the real tick rate. Needs network, so the orchestrator decides. Fetch EURUSD for December 2024 at m15 with the tool that made `unit-ship/data/dukascopy-node` (its command is in `unit-ship/evidence/b9/owner-lanes.md`), then point `D:/Temp/audit/ground-qmb/holes.py` at the file with `$AUDIT_AGENTS_ENV`. Pass if holes are listed with their dates. For speed, land one real month through `download-dukascopy` in a scratch home and time `TickFiles` from `bridge.py`.

## 10. Not reached
- Real Dukascopy ticks against dukascopy-node bars (the bridge's proof used ticks cut from bars).
- A real run of the p6-2, p2-5, p0b-14 and p2-11 shapes. They rest on reading.
- `test_conformance.py`, still owed from `reports/p2.md`. `BUILD-SLICES.md` and `RISK-SIZING-POINTS.md` for Part B: not named in my brief, not read.
- One of my read-only searches ran past 120 seconds and the harness moved it to the background. It finished on its own. I used shorter searches after that. My first wide `git grep` pathspec for `qmx-agents/packages/*/src` silently matched nothing, so I re-ran those searches with ripgrep and used only its answers.
