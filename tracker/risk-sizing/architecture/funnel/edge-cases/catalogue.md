# Edge-case catalogue: the hard cases the QMX foundation must handle

Written 2026-10-31 by agent E1 of the midday program (step 2b of `architecture/00-workflow-and-skills.md`). It designs nothing. It gives the architecture versions the hard cases they must handle, and a numbered checklist of foundation properties to score them against (the last section).

His words that set this job, verbatim:
- "Design for complexity means design a system that can handle very hard edge cases" (T1:1177)
- "edge case working is very important" (T1:651)
- "edge cases build a very solid and core foundation" (T3:1338)
- "Okay, think of Shopify." (T3:1338) and "these platforms have solid foundations" (T3:1338)
- "QMX is meant to be extensible by design" (T3:1383) and "Most things can actually become mini apps." (T3:1383)
- "we have to make sure there are no false positives" (T3:1264)

T1, T2 and T3 are `operator/transcript-2026-10-20-to-28.md`, `-29-to-30.md` and `-30-to-31.md`. Every quote of his was checked by a script against the cited line (section 21).

## The short answer

1. **The catalogue holds 267 cases across 15 parts, plus 18 for the risk session.** 212 of the 267 cite an earlier file, ruling or code fact (marked with its file and section). The other 55 are new: from a trader's and an operator's view, from the edge-case lens run over the ledger and the grounding files (section 19), and from a pre-mortem and a red team (section 18). Counts are by script (section 21).
2. **Most hard cases fall into a few families.** Something is unknown (an order outcome, a stale reading, a data hole, a clock), something has two owners (two nodes, two journal writers, two grants, two registries), something changed under a running thing (a unit version, a block fix, a broker spec, a schema, a QMB variant), and something means different things on different venues (digits, contract size, volume, sessions, the trading day).
3. **Each family is handled by one property of the core, not by special code per case.** Twenty properties cover all 267 cases (the checklist at the end). The architecture that holds those twenty with the fewest parts wins.
4. **Five cases are the costliest if missed:** an orphan or doubled position after a crash or reconnect (TN-01, TN-02); two machines trading one unit or refreshing one cTrader grant (TN-04, TN-05); a unit that passes every check and still trades nonsense, because today's checks prove safety and not trading (UT-01); a number whose unit differs by broker or digits (QML-05, QML-06); and protection that depends on something that can be down (TN-03, TN-08, TN-09).
5. **Many cases are already handled in shipped code**, mostly inside the never-run node (UNKNOWN outcomes, reconcile, journal-before-dispatch, clock bands, one refresher per credential) and in QML (look-ahead refusal by `knowable_at`). The gaps are mostly at the seams between parts, not inside them.
6. **The white-label platforms agree on a short list**: versioned contracts with an overlap window, extension points with defaults, owned names, declared inputs with deterministic runs, at-least-once events with ids and a reconcile job, unknown outcomes kept as a state, and the same code in research and live. Section 22 has the sources.
7. **Two of his own rules decide many rows.** They are "only the node sends orders" (ruling 27) and "units stand alone" (standing order 10). Any design where protection, the kill switch or a unit's next decision waits on the PC, the MIS, the router, telemetry or an agent fails a whole family of cases.

---

## How to read this

**Columns in every part table.**
- **What happens.** The case, from a trader's or an operator's view.
- **Odds, harm.** How likely in daily use, and how bad. Odds are **H** (expect it within a month), **M** (a few times a year) or **L** (rare). Harm is **Money** (can lose money or trade wrongly), **Silent** (corrupts evidence or judging without anyone noticing), **Stop** (blocks work and is visible) or **Friction** (wastes time or confuses). These scales are a lead's call (section 20).
- **Owner.** The part that must handle it.
- **Today.** What exists on `origin/engine/base` `c93407ca` that handles it, with the path. "none" means nothing found.
- **Property.** The foundation property (F1 to F20, last section) that handles it without special code.
- **Proof.** The check that would show it is handled.
- **Source.** Where the case came from (codes below).

**Evidence labels.** A path in "Today" was checked on `c93407ca` by the grounding agent named beside it (G1 to G4b, each marks its own CHECKED and INFERRED), or by me today where marked "(here)". Claims of my own without a path are INFERRED. No cost, price or venue fact here is new; they come from the cited research files.

**Source codes.**

| Code | File and section | What it gave |
| --- | --- | --- |
| T1-682 | `operator/transcript-2026-10-20-to-28.md` line 682 onward (the 24 Oct money-path list) | funding flips, expiry mid-trade, weekend gaps, partial fills and minimum sizes, stale feeds and outages, a unit in the wrong market, correlation spikes, self-tuning toward more risk, look-ahead in proof |
| M10b | memory `planning-workflow-that-worked.md` step 10b (22 Oct resilience list) | retries, rate limits, load balancing, abrupt offline, caching, database corruption, backups, reconnects |
| R44-Exx, Vxx, Axx | `research/44-review-of-convergence.md` lenses 1 to 3 | 15 edge-case, 7 verification-gap and selected adversarial findings |
| R08 | `research/08-old-qmx-testing-and-decay.md` §1.4, §2.3 | what old QMX tested, the decay check |
| R21 | `research/21-old-system-loose-ends.md` §3 | cTrader tick and depth limits |
| R29-Fx | `research/29-agent-failure-modes.md` §3 | 17 agent failure modes |
| R31 | `research/31-live-path.md` §1, §6.2 | node gaps per part, WSL behaviour |
| R33 | `research/33-data-depth-and-terms.md` §2 | per-feed quality failures |
| R38 | `research/38-venue-connectivity.md` §3.1, §3.8, §7 | cTrader, Hyperliquid and venue safety facts |
| R10, R39, R40, R41 | the Hermes files (`research/10`, `39`, `40`, `41`) | silent overwrite, honest entry price, failure history, limbo, capped memory deleting rules |
| FR-n | `D:\QMX-worktrees\engine-base-read\qmn\FAILURES.md` (79 designed failures) | the node's own failure register |
| HP | `tracker/qma-v2/HARDENING-PLAN.md` (BUG1, TRG2a, ADOPT, LIB4, SEC1A) and `BACKLOG.md` | catch-up after downtime, adopting a run whose home died, deduped deliveries, SQLite corruption |
| G1 to G4b | `architecture/grounding/*.md`, their trap lists | code facts and traps |
| R54 | `research/54-futures-platforms-languages-clocks.md` | futures, order flow, clocks |
| Brief | the starters in my brief | as listed there |
| Lens | the `bmad-review` edge-case lens run in this file (section 19) | unhandled paths in the ledger and grounding |
| PM, RT | the pre-mortem and red team in section 18 | failure stories and attacks |
| New | my own, from a trader's or an operator's view | |

**"The 192 things a site must handle".** The memory names this list as his phrase for the 22 Oct resilience pass. No file holds a numbered list of 192. The resilience cases it stands for are in M10b and in the hardening packets of HP; I harvested them from there (CHECKED by `grep -rln "192 thing"` over `tracker/qma-v2/`, which finds nothing; the hardening plan's section list has no such list either).

---

## 1. QML and the dictionary

QML is priority one ("a small mistake in there is very costly", T3:1264). These are the cases where a unit says one thing and means another.

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QML-01 | A block uses future data inside its own maths (centred window, a later bar, a repainting value) and stamps the result as known now | H, Silent | QML | `knowable_at` refuses samples after the instant (`qml/src/qml/protocol/evidence.py:588-596`, G1 §1.4); it cannot see future data used inside a producer. No cut-versus-full check in QML; one is designed in `bc-build-a-component` (G1 §2.4) | F5, F12 | Every block ships a cut-versus-full golden test: the value at t from data cut at t equals the value at t from full data | T1-682, G1 §1.5, Brief |
| QML-02 | A swing point or pattern is only confirmed k bars later, but the block stamps it on the bar it points at | H, Silent | QML | one swing-point family (`packages/qmf-structure/src/qmf/structure/families.py:1-8`, G1 §2.3); timing not modelled | F5 | The block declares its confirmation lag; the golden test above catches a missing one | New |
| QML-03 | A recursive indicator (EMA, ATR with smoothing) gives a different value after 200 bars of warm-up than after 5 years, so backtest and live disagree | H, Silent | QML | `derive_horizon` computes warm-up from the producer chain (`qml/src/qml/footprint/horizon.py:1-6`), and QMB does not use it (G1 §1.9) | F11, F6 | A recursive check like freqtrade's: compute with several warm-up lengths, compare the last values, record the length where they settle | New (freqtrade recursive-analysis, section 22) |
| QML-04 | A streaming indicator recomputes all history on every update, so a live unit slows a little more each hour | M, Stop | QML | streaming recomputes through the batch kernel (`qmf-indicators/streaming.py:17-23`, G1 §2.3) | F11, F6 | Time per update stays flat over a week of replayed ticks | G1 §2.3 |
| QML-05 | A stop of "20" means 20 pips on EURUSD (5 digits), 2 dollars on gold, and nonsense on a JPY pair or an index | H, Money | QML | parameters carry a `unit_kind` (G1 §1.3); the example bot hard-codes `_PRICE_SCALE = 5` (G1 §1.6) | F19 | The checker refuses a price-distance number with no kind; a test runs one unit on EURUSD, USDJPY, XAUUSD and an index and compares distances in ATR | Brief, G1 §1.6 |
| QML-06 | The same symbol has different digits, contract size or money per point at two brokers (gold 100 oz against 1 oz; US500 at 1 or 10 dollars a point) | H, Money | QML, Venues | `ValueFactor` is a type only; no stored per-broker instrument record (G1 §5) | F19 | The same unit on two brokers' records yields the same risk in R | Brief |
| QML-07 | A dictionary entry is used in a role it was not meant for, because the entries carry 154 free-text role strings and CT-34 accepts four | H, Stop | QML | parser reads all 239 with zero refusals; roles not normalised (G1 §2.2) | F3, F12 | The checker refuses an unknown role and names the nearest known one | G1 §2.2 |
| QML-08 | A unit cites an entry with no code behind it (ATR, MACD, Bollinger, VWAP are named, six indicators run), so nothing runs, or the agent hand-rolls it in Python with a bug | H, Silent | QML | six TA-Lib wrappers (`qmf-indicators/wrappers.py:146-193`, G1 §2.3) | F12, F3 | Each entry's status (has spec, has code, has golden test, used by a unit) is computed by script, never stored; the checker refuses a cite with no code and points at the block template | G1 §2.3, R44-A26 |
| QML-09 | One word means different things across classes. Volume is a tick count on cTrader and exchange volume on CME; "session", "the open", "gap", "funding" and "swap" differ | H, Silent | QML | none; research 45 §4 lists twelve such words (G1 §2.5) | F19, F5 | Each block declares the data level it needs; placing a real-volume block on a tick-count feed is refused unless the block is declared a proxy | G1 §2.5 |
| QML-10 | An entry written "crypto spot only" is used on perps or futures | M, Silent | QML | several entries say so (G1 §2.5) | F19 | Transfer notes become data the checker reads | G1 §2.5 |
| QML-11 | A dictionary entry's meaning is edited while units cite it, so those units now mean something else | M, Silent | QML | none | F10, F1 | Units pin the entry version; an edit makes a successor and lists the units that cite the old one | Lens |
| QML-12 | A shared block gets a bug fix, and every unit using it changes behaviour, live ones included | M, Money | QML | none | F10, F16 | A block fix mints new versions of the units that use it and queues their re-test; live units keep the pinned version until he promotes | R44-E11 |
| QML-13 | A learned block (a model) is retrained. Is that calibration or a new version? And the scan denies file reads, so weights cannot load | M, Silent | QML | file I/O denied (`qml/src/qml/conformance/scan.py:39-56`, G1 §1.6); no host injects weights | F10, F5 | A block declared "learned" with bounds retrains as calibration; weights arrive through a declared read surface with a fingerprint | R44-E11, G1 §1.6 |
| QML-14 | Undeclared randomness (`numpy.random` is not in the deny list) makes a replay differ from the first run | L, Silent | QML | Layer 2 runs the golden slice twice (`conformance/contract.py:32-39`, G1 §1.5) on 3 instants | F5 | Determinism run on real recorded bars, not only on three instants | G1 §1.6 |
| QML-15 | Code evades the scan (`exec`, `importlib`, `__import__` are not denied) to read a file or the clock | L, Silent | QML | "evasion is out of scope" (`scan.py:1-6`); only QMB's child process really isolates (`qmb/src/qmb/host/runner.py:72-85`, G1 §1.5) | F14 | The real wall is the child process with declared rights; the in-process "isolated" stamp (`layer2.py:321`) is not proof | G1 §1.6, G1 trap 2 |
| QML-16 | A threshold lives as a literal in the Python logic, so tuning, the UI and the checker cannot see it | H, Silent | QML | nothing checks that logic reads only declared parameters (G1 §1.6) | F5, F12 | A scan warns (never refuses) on numeric literals in comparisons inside unit logic | G1 §1.6 |
| QML-17 | Long and short rules are silently mirrored when the source made them different | M, Silent | QML | the Hermes graph rule says they must not be (`research/10` line 97) | F5 | The unit document states each side; the checker refuses an implicit mirror | R10 |
| QML-18 | A confirmation that comes after the trigger moves the honest entry price, but the test fills at the trigger bar | H, Silent | QML, QMB | `knowable_at` per sample (G1 §1.4); no timing model for confirmations | F5, F6 | Entry price is the first price after the last required input became knowable | R39-D5 |
| QML-19 | A plain-Python unit reads the forming bar as if it had closed (cTrader's OnBar against OnBarClosed) | H, Silent | QML | forming bars are never visible or actionable in QMB and QMN (`qmn/src/qmn/loop/driver.py:4-5`, G1 §4.3) | F6, F5 | The runtime only hands closed bars to a unit unless it declares tick input | New |
| QML-20 | A 1-minute unit reads the 1-hour close before the hour has closed; or the daily bar ends at 17:00 New York at one broker and 00:00 UTC in the history | H, Silent | QML, Clocks | bar specs per stream (G1 §1.3); the daily boundary is measured per broker in CT-18 (`packages/qmf-venue/src/qmf/venue/capabilities.py:1-40`, G3 §3.2) | F5, F17 | Higher-timeframe values are knowable only at their bar's close in the venue's day boundary | New |
| QML-21 | A weighted-vote combiner ties, or every input is absent at start, and the rule's default branch is undefined | M, Silent | QML | none | F2 | Every combiner has an explicit "no signal" result | New |
| QML-22 | A unit reads another unit's live output ("a mini scalper for an indicator"), so one failing unit stops another | M, Money | QML | not carried (G1 §8.2) | F15 | Composition happens at build time into one unit; a live unit-to-unit read is refused | R39-C5 |
| QML-23 | Refusal functions and `GAP_*` constants from old rulings read as live law, and a builder refuses the placeholders he asked for | H, Stop | QML | about a third of the public names (`generation/gaps.py`, `research/projection.py`, G1 §1.2) | F1 | Old law is subtracted or marked retired in one place | G1 trap 4 |
| QML-24 | Two registries hold "bots" (qmf-registry through QMB, and the Library's empty `unit` and `bot` kinds), so an edit in one is missing in the other | H, Silent | QML, Library | G1 §3.1 | F3 | One home of record for a unit; the other is derived | G1 trap 16 |
| QML-25 | QML needs Python 3.14 exactly; a newcomer or a server image with another version cannot import it | M, Stop | QML, DevOps | `qml/pyproject.toml:1-13` (G1 §1.1) | F2, F13 | The app ships its own interpreter; a first-run check names a wrong one | New |
| QML-26 | A venue or plain-Python code passes binary floats into exact money and prices | M, Silent | QML | exact types refuse floats (`packages/qmf-core/src/qmf/core/exact.py:970-1000`); cTrader execution prices arrive as doubles at a named boundary (G3 §2.1) | F19 | Conversion happens once at the venue boundary; a float past it is a type error | New |

---

## 2. The unit template and its checker

A unit is one complete algorithm (U-01). These cases are about what the template must carry and what its checker must catch.

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| UT-01 | An agent's unit passes every check and still trades nonsense: always long, an exit that never fires, entries no better than a coin | H, Silent | Unit, QMB | Layer 2's golden slice is 3 instants valued 1, 2, 3 (`qml/src/qml/conformance/slice.py:36`, `:104`, G1 §0 item 2); it proves safety, not trading | F12, F5 | A "does it trade" check on recorded bars (trades happen, exits fire, the signal is not constant) and a negative control (a shuffled day should find nothing); the judge's numbers decide, the check only reports | Brief, R29 check 9 |
| UT-02 | A checker false positive blocks good work: an `os.path` helper flagged by the import scan; a constants table flagged as hidden numbers | H, Stop | Unit | the scan refuses by import (`scan.py:36-138`) | F12 | A check refuses only a proven violation; heuristics warn; each refusal has an id, a reason, a fix and a recorded override; a false positive becomes a check change | Brief, Q-06 |
| UT-03 | The checker changes and a unit that passed yesterday fails today, or the reverse | M, Stop | Unit | none | F1, F13 | Each verdict records the checker version; an upgrade re-checks and labels old verdicts; a live unit never flips silently | Lens |
| UT-04 | A unit's version changes while a trade is open, and the new logic's exits do not match the old entry | H, Money | Unit, Node | CT-29 attributes the whole trade to the opening bot (`packages/qmf-risk/src/qmf/risk/exit_record.py:1-14`, G1 §7) | F10, F11, F18 | A position belongs to the version that opened it; that version keeps managing its exits until flat, unless he hands it over | Brief |
| UT-05 | A self-tuned number swings back and forth on too few trades | H, Money | Unit | numbers carry bounds and step (G1 §1.3); no motion rule; live seats run defaults only (`declaration/bot.py:618-628`, G1 §1.4) | F5, F10 | Every movable number declares its motion: inputs, minimum sample, step limit, cool-down, bounds from QMB; each move is a journal row | Brief, R43 F3 |
| UT-06 | Self-tuning drifts toward more risk over months | M, Money | Unit | none | F16 | Tuning never leaves the tested range; the risk-side rule goes to the risk session (RS-02) | T1-682 |
| UT-07 | A placeholder sizer or exit reaches a live account without anyone replacing it | M, Money | Unit, Node | none; placeholders are ruled (U-04) | F13, F16 | Placeholders are labelled data; promotion shows the label; every trade carries it in the journal | Lens |
| UT-08 | A unit's invalidation is a condition, not a price, so R is undefined | M, Silent | Unit | R lives in CT-29 exit records (G1 §4.4) | F19 | Goes to the risk session (RS-06) | R44-E03 |
| UT-09 | Unit state (calibration, counters, an armed setup) is lost on restart, or state saved by version N is loaded into version N+1 | H, Money | Unit | `export_state` and `import_state`, a state bound, a restore-equivalence check (G1 §1.4) | F11, F1 | State carries the unit version and a schema version; a mismatch starts from a declared cold state, logged | New |
| UT-10 | The node restarts mid-session and a unit needs 200 bars before it can decide | H, Money | Unit, Node | `derive_horizon` (G1 §1.9); DEC-0261 says "no per-bot warm-up" (STATE "Conflicts") | F11, F15 | The unit warms from the node's own recording, then broker history; it places no trade while warming; warming shows as a state | Brief |
| UT-11 | Warm-up history comes from another source than the live feed (Dukascopy against cTrader), so values jump at the seam | M, Silent | Unit, Library | the node refuses a silent sibling-feed failover (FR-45) | F5, F13 | The warm-up's source is recorded; a cross-source gap above a number is flagged | FR-45 |
| UT-12 | A unit needs depth or a trades tape, and the market or machine has none (cTrader has no tape; Hyperliquid gives 20 levels) | H, Silent | Unit | none | F19, F12 | The unit declares data levels; placement on a market that lacks them is refused unless a proxy is declared | R54 §3.3 |
| UT-13 | A unit built for FX hours is placed on a 24/7 crypto perp, or on an index with its own breaks, and its session profile means nothing there | H, Silent | Unit, Clocks | one market-hours calendar, `forex-17NY` (`extensions/qmf-calendar-forex/`, G3 §1.1) | F17, F19 | Session rules name the market's zone and calendar; a placement with no calendar is refused | New |
| UT-14 | Two units trade one symbol on a netting account, and one unit's close closes the other's position | H, Money | Unit, Node | the node keeps virtual positions per Book binding (`qmn/src/qmn/ledger/`, G4a §2.2) | F18, F19 | The account record says netting or hedging; the node keeps a virtual position per unit and nets at the venue | R44-E04 |
| UT-15 | A unit signals twice on consecutive bars and pyramids without meaning to | H, Money | Unit | none | F2 | Each unit declares how many positions it may hold per instrument, default one | New |
| UT-16 | A unit emits an exit and an entry on the same instant, or opposite entries from two of its timeframes | M, Money | Unit | the old Intent Aggregator resolved opposite trades (research 19) | F5 | One ordering rule in the core: exits first, then entries; opposite entries from one unit are refused and logged | New |
| UT-17 | An edit is wrongly called a new unit, a new version or a calibration, so two different units share a record, or one unit's record splits | H, Silent | Unit, Library | the version graph with human-signed `continues-performance` (`qml/src/qml/declaration/versioning.py:1-8`, G1 §1.9) | F10 | The type of edit decides, by one table in code | R10, R39-G1 to G8, R44-E11 |
| UT-18 | A unit has no exit that is sure to fire, and holds through a weekend, an expiry or forever | M, Money | Unit | none | F2, F12 | The checker refuses a unit with no terminating exit; the placeholder exit set includes a time stop | New |
| UT-19 | The unit template moves to schema version 2 and stored units must still load | M, Stop | Unit, Library | stores open, upgrade after a copy, or refuse by name (PR 213, G2 §6) | F1 | An upgrader per schema version; a test loads every older shape | New |
| UT-20 | A plain-Python unit (always allowed, CC-08) wants to trade, and the node's seats accept only QML-conformant bots | M, Stop | Unit, Node | "plain Python cannot bypass" a seat (`qmn/src/qmn/seats/admission.py`, G3 §1.1) | F3, F2 | The runtime contract is small enough for plain Python to meet: the callback shape, declared inputs, declared state | Lens |
| UT-21 | A unit is saved without the source it came from (a video, a chat, an article) | M, Silent | Unit, Library | Library lineage edges and the `source` kind (G1 §8.2) | F10 | A unit cannot be saved without a source link, even "hand-made" | U-15 |
| UT-22 | The PC is off for a week; where does a unit's slow recalibration run? | M, Money | Unit, Node | none | F15 | Recalibration runs where the unit runs, from its local journal | R44-E09 |
| UT-23 | A unit's general settings and its market version (U-13) are both admitted for one market; which one trades? | M, Money | Unit | none | F10, F16 | One admitted version per unit and market at a time; his click picks it | Lens |

---

## 3. QMB backtests

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| QB-01 | A long backtest dies on memory because every replay step copies all history | H, Stop | QMB | cumulative frames (`qmb/src/qmb/host/replay.py:560-572`, `qml/.../evidence.py:875-885`, `replay_execution.py:815-829`, G1 §4.3) | F6, F14 | A 20-year run on 1-minute bars uses memory proportional to the declared horizon | G1 §4.3, R12 |
| QB-02 | Futures trades, crypto trade prints and perps tape cannot replay; the reader needs bid and ask pairs | H, Stop | QMB | "Half a pair is refused" (`replay.py:608-626`, G1 §4.3) | F3, F19 | The replay takes trades, quotes or bars as declared by the data card | G1 trap 9 |
| QB-03 | The test uses one spread, but live spreads at the 17:00 New York rollover widen several times, and the scalper dies | H, Money | QMB, Journal | cost calibration empty (GAP-0048); no market journal (G1 §7) | F19, F6 | Costs per broker and hour come from the market journal; an uncalibrated run is labelled | R12, R08 |
| QB-04 | Triple swap on Wednesday (FX), Friday financing (index CFDs), hourly perps funding are missing or wrong | H, Silent | QMB | financing ports exist; perps funding as a carry cost is missing (G1 §4.4) | F19 | Carry per instrument record, replayed at its venue time | G1 §4.4 |
| QB-05 | A futures continuous series is back-adjusted, so a unit tuned on it sees price levels that never traded | M, Silent | QMB, Library | none | F19, F10 | The data card records the stitching and roll dates; QMB replays contract by contract with the roll as an event | T1-682, R54 §3.1 |
| QB-06 | An IC futures CFD expires and is never rolled, forcing a close at an unplanned price | M, Money | QMB, Venues | none | F19 | The instrument record carries the at-expiry action; QMB replays it | R44-E06 |
| QB-07 | A weekend gap jumps through the stop, and the test fills at the stop price | H, Silent | QMB | fill ports exist (G1 §4.4); gap behaviour not checked | F6 | The fill model fills a gapped stop at the first tradable price | T1-682 |
| QB-08 | The computed size is under the minimum lot, so it rounds to zero or up to the minimum, doubling the risk on a small account | H, Money | QMB, Unit | lot step in the Book admission context (G1 §3.3) | F19 | One declared rounding rule (down by default, skip under the minimum), journaled; the risk numbers go to RS-01 | T1-682 |
| QB-09 | An agent scores variants in a script without passing QMB's door, so tries go uncounted and luck comes back | H, Silent | QMB, Agents | template scripts open the market door themselves (`TPL/download-dukascopy/scripts/download.py:41`, via R44-V01) | F12, F13 | The judge refuses any result without a door-issued run id; the data door counts reads per family | R44-V01 |
| QB-10 | The best-looking of 20 markets is picked, and its edge was luck | H, Silent | QMB | none (settled; the fix sits in the judge, ledger "settled") | F12 | Every market judged by one rule and pulled toward the unit's overall result | R24 |
| QB-11 | An agent-built unit is tested on years the model remembers, so it picks what worked | M, Silent | QMB, Agents | none | F13 | The run records the model and its training cutoff; a window after the cutoff is offered | R29 §0 item 4 |
| QB-12 | A template brings back a default holdout lock (60/20/20 split), against ruling 137 | H, Stop | QMB, Workflows | `TPL/b-build-and-prove/scripts/spec.py:1-11`, `:18-19` (G2 §4) | F2 | Holdouts are off unless a study names one | G2 trap 9 |
| QB-13 | Two QMB variants (he wants new versions and variants, T3:1383) give different numbers for the same unit and data | M, Silent | QMB, Mini apps | none | F1, F13, F10 | Every result records which QMB variant and version made it; the judge compares like with like | Lens |
| QB-14 | The same run twice gives two results (thread order, dictionary order, floats) | L, Silent | QMB | run fingerprints (G1 §4.4) | F5 | A rerun of a fingerprinted config matches exactly | New |
| QB-15 | A run that placed no trades is read as a finished backtest | H, Silent | QMB | PR 204's only runner is `silent` (`origin/build/wu4:qmb/src/qmb/host/backtest_door.py:60`, G1 §4.2) | F12, F13 | A result with zero trades is labelled, never a pass | G1 §4.2 |
| QB-16 | Synthetic data for crypto or futures comes from a forex-CFD generator | M, Silent | QMB | forex-CFD only (`qmb/src/qmb/data/generate.py:175`, G1 §4.4) | F19 | The generator takes the instrument record's class | G1 §4.4 |
| QB-17 | A long backtest on the PC competes with the live recorder or a node rehearsal for CPU and disk | M, Stop | QMB, DevOps | engine Job objects on Windows (G2 §10) | F9, F15 | Live paths have priority over research on a shared machine | New |
| QB-18 | A data hole is replayed as a flat market, and indicators bridge a three-day gap | H, Silent | QMB, Library | none | F13, F5 | A data preflight counts missing minutes per read and refuses or flags; a gap is an event the unit sees | R29 check P |
| QB-19 | Results are money only, so units on different instruments and account sizes cannot be compared | H, Silent | QMB | 27 money measures (`qmb/src/qmb/results/measures.py:58-86`); R sits in CT-29 records (G1 §4.4) | F19 | R beside money in every result | G1 §4.4 |
| QB-20 | The backtest child is killed by the OS; on Windows the memory limit does not apply | M, Stop | QMB | the door answers only on a clean exit with a full report; memory limit POSIX only (G4a §2.4) | F11, F13 | A killed run lands as "failed, killed", never as a partial result | G4a §2.4 |
| QB-21 | Daily bars in the history are UTC while the broker's day ends at 17:00 New York, so daily indicators differ | H, Silent | QMB, Clocks | daily boundary measured per broker (G3 §3.2) | F17 | Bars built from ticks in the venue's day boundary | R54 §4 |
| QB-22 | What-if filters that improve results are not counted as tries | M, Silent | QMB | QMB's What-If (research 03) | F12 | Filters that can only worsen results stay views; improving ones become counted reruns | R26 |
| QB-23 | Live trades differ from what the backtest would have done on the same day | H, Silent | QMB, Node | the node loop drives QMB's `run_slice` unforked (`qmn/src/qmn/loop/driver.py:1-6`, G1 §3.5) | F6 | A nightly replay of the live day through QMB compares decisions, per unit | R08 D4, R44-V04 |
| QB-24 | An agent edits the test tool or its output to get a pass | L, Silent | QMB, Agents | read-only hashed code zones (research 18 §1.1 via R29) | F14, F13 | Results are hashed and written only by QMB | R29-F10 |

---

## 4. The Library's data, as units and backtests see it

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| LD-01 | A Dukascopy hour comes back empty with no error after the bot wall | H, Silent | Library | QMX's own bi5 fetcher (`templates/download-dukascopy/scripts/download.py:1-19`, G1 §5) | F13, F8 | An empty trading hour is a fetch failure until a retry and a second source agree | R33 §2, R12 |
| LD-02 | Weekend and holiday bars: present for crypto, absent for FX, partial for index CFDs | H, Silent | Library, Clocks | one FX calendar (G3 §1.1) | F17, F19 | Completeness is judged against each instrument's own calendar | New |
| LD-03 | A source changes its timestamp unit (Binance moved from milliseconds to microseconds on 1 Jan 2025) | M, Silent | Library | none | F5, F10 | A per-file stamp check; the seam is on the data card | R33 §2 |
| LD-04 | A source changes its cadence (Hyperliquid's book snapshots changed on 2026-06-17), so statistics across the seam mean different things | M, Silent | Library | none | F10, F13 | Seams are recorded on the card and named in any result that crosses one | R33 §2 |
| LD-05 | An upstream archive file is replaced, so an old backtest can no longer be reproduced | M, Silent | Library | partition digests on the `dataset` kind (G1 §5) | F10 | A new checksum is a new card version; results pin the version they read | R33 §2 |
| LD-06 | His Library is empty in the new layout (no bring-in has run), so the first backtest finds nothing | H, Stop | Library, Operator | the first-start card (PRs 214, 219, 234); no new-layout folder exists (G4a §2.1) | F13, F2 | A backtest with no data says which data and how to download it | G4a §2.1 |
| LD-07 | The Library is down or on an unreachable server while the node trades, so the instrument record and calibrated numbers are missing | M, Money | Library, Node | none | F15 | The trading machine holds a snapshot of every record its units use, refreshed on change | R44-E08 |
| LD-08 | An agent's tool call cannot pass a holdout or a run id, so reads are not tied to a study | M, Silent | Library, Agents | PR 207 departures (G2 §3) | F13 | Every read carries its run id | G2 §3 |
| LD-09 | Recording ticks fills the disk (D: about 57 GB free, C: 16 GB) | M, Stop | Library, DevOps | none | F9, F13 | The recorder reports disk; a full disk stops recording loudly and never touches trading | R33 §4, R44-V06 |
| LD-10 | A source's terms limit use (Dukascopy, Binance Vision) | L, Friction | Library | `dataset` kind carries `licence` (G1 §5) | F13 | Recorded on the card only; settled, never raised with him (ledger "settled") | R33 §3 |
| LD-11 | A backup reading the price store makes the live recorder wait (about 1.3 s seen) | M, Stop | Library, DevOps | G4a §1.3 | F9 | Backups never block a live writer | G4a §1.3 |
| LD-12 | The same instrument from two sources (Dukascopy gold against IC gold) differs by an offset; a unit tuned on one trades the other | H, Silent | Library, QMB | none | F19, F13 | A cross-source check; the market journal measures the gap | R12 check 15 |
| LD-13 | Index CFD dividend cash adjustments are missing from price series, so P&L does not match | M, Silent | Library, QMB | none | F19 | Dividend events per instrument record | R54 §3.3 |
| LD-14 | Two agents edit the same Library item | M, Silent | Library | branch and merge for agents (PR 195, G2 §11) | F10, F18 | Both versions kept; merge is explicit | BACKLOG B36 |
| LD-15 | The bundled SQLite has a write-ahead-log reset bug; two writers can corrupt a store | L, Silent | Library | the host is the one Library writer (`HO/host.py:1-20`, G2 §7) | F18 | One writer per database file | HP BACKLOG B1, M10b |
| LD-16 | History is stamped in UTC, the broker in GMT+2 or +3, and someone labels it wrong | H, Silent | Library, Clocks | `Instant` is UTC nanoseconds (`packages/qmf-core/src/qmf/core/chrono.py:1-16`, G2 §9) | F17 | Every card states its source clock; conversion happens once | New |
| LD-17 | A save made while the server Library is away is replayed twice, or lost | M, Silent | Library | the PC's write outbox replays once (`LIB/outbox.py:1-2`, via R44-V05) | F8 | Every save has an id; a replay is idempotent | HP LIB4, R44-V05 |

---

## 5. The MIS

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MIS-01 | The MIS is down or slow, and units must keep trading | M, Money | MIS, Unit | the MIS lives only inside QMN and publishes only to the Book door and the kill switch (`qmn/src/qmn/mis/signal_snapshot.py:1-4`, G1 §6.1) | F15, F9 | Readings are library code a unit can run itself; a unit with the MIS cut off still trades its admitted markets | CC-12 ("why should the unit stop trading?", T1:1574) |
| MIS-02 | A stale reading is used as if it were fresh | H, Silent | MIS | `stale_after` exists on mini-app contracts (`APPS/manifest.py:148-167`, G2 §5.1) | F8, F13 | Every reading carries its time, version and freshness; a stale reading reads as absent | New |
| MIS-03 | "Regime" means volatility in the code and trend or mean reversion in his words | H, Silent | MIS | `qmn/src/qmn/mis/regime_design.py:72-78` (G1 §6.1) | F1, F20 | One versioned vocabulary; each word has one measure | R29-F7 |
| MIS-04 | The same reading computed in QMB, the MIS and a unit gives three values | H, Silent | MIS, QMB | QMB imports nothing from QMN (G1 §6.1) | F6 | A golden replay runs one recorded day through all three and compares them per reading id and version | R44-V04 |
| MIS-05 | A retrained model relabels the past, so a backtest sees new labels at old times | M, Silent | MIS, QMB | none | F10, F5 | Readings are stored with time and version and never rewritten; QMB asks what the MIS said at that time | R39-I8, funnel5 |
| MIS-06 | Bid-ask bounce makes a price-only mean-reversion sensor raise false alarms (2 to 130 times) | H, Silent | MIS | none | F19 | Each sensor declares its data input; mid or trade prices where bounce matters | R22 |
| MIS-07 | A trend or mean-reversion label takes hours to show, and a scalper uses it per trade as if it were fast | H, Silent | MIS | none | F5 | Each reading declares its clock (tick, bar, session, day) and its time base | R22, funnel5 |
| MIS-08 | A corpus built on three FX sessions is applied to 24/7 crypto | H, Silent | MIS | `regime_design.py:80-86` (G1 §6.1) | F19, F17 | Sessions come from each instrument's calendar | G1 §6.1 |
| MIS-09 | The slow-lane shortlist does not arrive before a session (a workflow failed at night) | M, Money | MIS, Workflows | none | F15, F2 | The unit trades its admitted envelope on its own conditions (settled, CC-12) | New |
| MIS-10 | The unit computed a reading while the MIS was down, but only the MIS writes reading history | M, Silent | MIS, Journal | none | F13 | The unit journal keeps what the unit computed | R44-E02 |
| MIS-11 | The shuffled-readings proof passes by construction, because units compute their own inputs | M, Silent | MIS, QMB | none | F12 | Each proof states what it can and cannot fail on | R44-V03 |
| MIS-12 | A new sensor is approved, and older records were labelled without it | M, Silent | MIS | none | F10, F1 | New vocabulary is a new version; old records keep theirs | M-10 |
| MIS-13 | Templates wait to read MIS logs that never reach the PC, because no node-to-PC link exists | H, Stop | MIS, Contracts | templates with `needs: trading-node` (`TPL/db-desk-brief/README.md:24`, G4b §0 item 6) | F8 | Readings land in one of the four Library homes that exist (G4b Q6) | G4b Q6 |
| MIS-14 | A market's data level changes (a venue drops depth), and a sensor silently falls back | M, Silent | MIS | none | F13, F19 | Fallback steps per reading are declared and every fallback is logged | funnel5 |

---

## 6. Journals and records

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| JR-01 | Two writers land on one unit journal: a demo twin on the PC and live on the server, or a failover server | M, Silent | Journal | CT-13 streams are writer-scoped (`packages/qmf-data/src/qmf/data/journal.py:1-26`, G1 §7) | F18 | The stream key is unit plus world plus machine; one lease per unit and account during a failover | R44-E01 |
| JR-02 | The journal cannot be written before an order goes out (disk full, write error) | M, Money | Journal, Node | with journal-before-dispatch, the effect does not dispatch, entries block, and exits and protection still go (`qmn/src/qmn/journal_dispatch.py:1-12`; FR-33) | F9 | A test fills the journal disk and shows entries blocked and a stop still amended | FR-33 |
| JR-03 | A unit in an error loop logs every tick, and the log flood fills the disk the journal needs | M, Money | Journal, DevOps | the engine exporter batches in memory and counts drops (`ENG/telemetry.py:1-20`, G2 §8) | F9, F13 | Logs and journals have separate disk budgets; logs are rate-limited per source with a dropped-lines count; a disk alarm fires before full | Brief |
| JR-04 | Signals seen but not taken, and missed trades, are not recorded | H, Silent | Journal | CT-13 decision outcomes include suppressed and refused-by-door (G1 §7) | F13 | Every decision a unit makes is a row, taken or not | J-03 |
| JR-05 | A trade's world (backtest, paper, demo, live) is labelled wrongly | M, Silent | Journal | every broker read says demo or live (PR 215, G2 §11) | F13 | The world is stamped by the venue reader, never by the unit | G4a §1.2 |
| JR-06 | A unit goes back to paper, and paper trades mix into its live figures | H, Silent | Journal | none | F13 | Every row carries its stage (backtest, stress, paper, live); figures are computed per stage | R-11, R08 §2.3 |
| JR-07 | Fills replayed after a reconnect land twice | H, Silent | Journal, Node | the cTrader deal id is the fill key (G3 §2.6); gap replay (`qmn/src/qmn/venue/reconnect.py`) | F8 | Appending the same fill twice leaves one row | New |
| JR-08 | Backfilled rows mix with live rows, so a live statistic includes history | M, Silent | Journal, Library | none | F13 | Backfilled rows are marked | R33 §2 |
| JR-09 | Rows from two machines with drifting clocks sort in the wrong order | M, Silent | Journal, Clocks | cTrader stamps only receive time (`ctrader.py:14-17`, G3 §2.1) | F17 | Rows carry venue time and receive time and the machine's clock band | New |
| JR-10 | Market facts (spread, fees, slippage) are copied into every unit journal and the volume explodes | H, Stop | Journal | none | F3, F18 | One market journal per broker, account type and instrument; unit rows link to it | J-04 |
| JR-11 | An agent's analysis written into a journal is later read as a record | H, Silent | Journal, Agents | none | F13 | Agent rows are a separate kind and carry receipts | R29-F1 |
| JR-12 | The journal row shape changes partway through a unit's life | M, Stop | Journal | Library kinds carry `schema_version` (G2 §6) | F1 | Old rows stay readable under their version | New |
| JR-13 | A capped memory or journal silently drops old rows to stay under a limit | M, Silent | Journal, Agents | Hermes memory edits deleted six rules to fit 1,375 characters (`research/41` §2.6) | F14 | Nothing is dropped silently; a provider limit shows as an error | R41 item 8 |
| JR-14 | An artifact sits in a tool folder, outside the Library, and an agent later pulls it in without knowing its origin | M, Silent | Journal, Library | none | F10, F3 | Draft or published, never orphaned | R41 item 1 |
| JR-15 | Imported broker fills carry no initial risk, so R is missing for those trades | H, Silent | Journal | the `trade` kind has `initial_risk` and `r`; imported fills leave them empty (G1 §7) | F19 | Trades without R are flagged, never averaged in as zero | G1 §7 |
| JR-16 | Journals made on the node must reach the PC; the one-way pull was never built, and a copy may fail its check | H, Stop | Journal, Contracts | sealed-archive copy with verification (FR-50); PC side missing (G3 §1.3) | F8, F15 | The node keeps journals until the PC confirms a verified copy; a week offline loses nothing | FR-50, G3 §1.3 |
| JR-17 | A failed effect is retried silently and lands twice, or is retried after its moment has passed | M, Money | Journal, Node | "the act is re-decided, never blindly retried" (FR-33) | F7 | A failed effect is re-decided from current state | FR-33 |

---

## 7. The copilot and agents writing units

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AG-01 | An agent never calls the unit checker | H, Silent | Agents | no catalog row lints a unit (G1 §1.7); the Library kind check returns only the first schema problem (`LIB/kinds/__init__.py:46-55`, here) | F12, F3 | The same check runs at the Library door for the unit kind, so no path skips it, and it returns every problem | G2 §2.2 option D |
| AG-02 | An agent writes a unit with `python -c`, past a hook bound to Write and Edit | H, Silent | Agents | chats keep a shell (G2 trap 4) | F12 | The check sits at the door the unit must pass to be saved or run, not at the editor | G2 trap 4 |
| AG-03 | A slow check inside the 10 s guard blocks the tool call | M, Stop | Agents | guard timeout 10 s (`HAR/launch.py:436-438`, G2 §2.1) | F12, F13 | Fast lint in the loop; slow checks run as a job with a handle | G2 trap 6 |
| AG-04 | A hook added mid-session only applies at the next launch | M, Friction | Agents | the ConfigChange hook blocks reloads (`HAR/home.py:428-439`, G2 §2.1) | F13 | The checker is a tool row, so it reaches chats already running | G2 trap 5 |
| AG-05 | Workflow agent steps cannot write files, so a unit authored inside a workflow has nowhere to go | H, Stop | Agents, Workflows | the read-only policy (`ENG/policy.py:15-31`); AGW skipped after a probe (G4b Q1) | F3 | Units are written as a step's JSON output or a Library save, then checked by a script step | G4b Q1 |
| AG-06 | An agent grades its own unit, agrees with him, or several agents agree and it is taken as proof | H, Silent | Agents | none | F12 | Verdicts come from scripts and QMB numbers; agreement counts for nothing | R29-F8, F9, F16 |
| AG-07 | A source (a video description, a forum post) carries instructions the agent follows | M, Silent | Agents | the guard covers tools, not text (R29-F11) | F14, F13 | Sources enter as marked data; numbers come from tools | R29-F11 |
| AG-08 | A cheap model uses a dictionary word wrongly | H, Silent | Agents, QML | none | F12, F20 | The checker's error names the right entry | D-03 |
| AG-09 | Unit tools placed inside a mini app do not reach the default copilot | M, Stop | Agents, Mini apps | the copilot preset is core toolsets only (`HAR/surface.py:484-489`, G2 §1.4); a settings line closes it (G4b Q3) | F3 | Unit tools are core catalog rows | G2 §1.4 |
| AG-10 | Two agents edit the same unit at once | M, Silent | Agents | branch and merge (PR 195) | F10, F18 | Both kept; a merge is explicit | BACKLOG B36 |
| AG-11 | An agent loops on the checker (fix, new error, fix) for hours | M, Friction | Agents | a stuck detector, no caps (`ENG/nodes/agent.py:8-12`, G2 §1.1) | F12 | The same problem set twice counts as no progress | New |
| AG-12 | An agent states a market value from its training memory | M, Silent | Agents | none | F13 | Every number in an agent's output cites a tool receipt | R29-F12 |
| AG-13 | An agent proposes a promotion while he is away, and it is treated as approved | M, Money | Agents | governed kinds land as drafts awaiting his yes (`LIB/landing.py:1-18`, G2 §3) | F16 | A promotion without his act is impossible by type | CC-11 |
| AG-14 | The model provider is down overnight, and the slow lane fails | M, Stop | Agents | provider rows and relays (G2 §1.1) | F15, F9 | Nothing in the fast lane waits on an agent | ruling 44 |
| AG-15 | A tool answer over 20,000 characters spills to the Library; the agent reads head and tail and misses the failing problem | M, Silent | Agents | spill at 20,000 characters (`CTL/catalog.py:86-89`, G2 §1.3) | F12 | The checker's answer leads with the count and the refusals | New |
| AG-16 | Copilot and workflow agents see different tools for the same job | M, Friction | Agents | parity holds by construction for core rows; no test pins it (G4b Q3) | F3 | A test that every agent-visible core row is on the default copilot surface | G2 §1.4 |

---

## 8. Workflows and templates

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| WF-01 | A template needs a door that does not exist yet, installs as a draft, and a newcomer sees 23 drafts with no reason given | H, Friction | Workflows | `meta.needs` drafts (G2 §4) | F13, F2 | Each draft says which door it waits for | G2 §4 |
| WF-02 | The `market_open` check holds crypto runs on Saturdays | H, Stop | Workflows, Clocks | weekend and holiday rule in the trigger's zone (`ENG/triggers/preflight.py:14-16`, here) | F17, F19 | Open or shut comes from each instrument's calendar | G2 §9 |
| WF-03 | Zone defaults disagree (templates London, the build skill Berlin, three host paths the machine's zone), so reviews run at the wrong hour | H, Friction | Workflows, Clocks | G2 trap 11 | F17 | One default zone setting; every trigger states its zone | G2 trap 11 |
| WF-04 | A 24/7 market has no end of day, so "the nightly review" has no time | H, Friction | Workflows | none | F17 | Reviews key on each market's session close or a named UTC hour | T-02 ("We are literally trading 24/7, my days.", T2:325) |
| WF-05 | An event-trigger chain loops: a template lands an item that fires the template again | M, Friction | Workflows | event triggers from the Library ref log (PR 160) | F8, F13 | Each trigger carries its cause id; a chain that re-fires itself is caught | New |
| WF-06 | A run pass minted on the PC fails at the server's door while the PC sleeps | M, Stop | Workflows, Contracts | backlog row "Cross-machine run passes" (G2 §6) | F1 | One pass format on every host | G2 §6 |
| WF-07 | An agent step idles on a long tool and its cache expires | M, Friction | Workflows | idea logged (G4b §1.3) | F11 | Long work runs as a script step or a background job with a handle | G4b §1.3 |
| WF-08 | The `library` node kind is marked available but has no executor | M, Stop | Workflows | `ENG/definition/registry.py:94` (G2 §4) | F12 | Validation refuses a kind with no executor | G2 §4 |
| WF-09 | A QMX update ships a newer template and overwrites the one he edited | M, Friction | Workflows | templates are Library items (G2 §4) | F10 | An update makes a new version beside his | Lens |
| WF-10 | A webhook trigger has no sender signature check | L, Silent | Workflows, Contracts | `HO/host.py:1370-1393`; backlog row (G2 §6) | F14 | Deliveries are signed and deduplicated by id | G2 §6, HP TRG2a |
| WF-11 | An analyst workflow marks its own forecasts | H, Silent | Workflows | none | F12 | Calls are written with a date and scored later by a script against the market | R29 §4 |
| WF-12 | The shared judge step is edited, and every past verdict changes meaning | M, Silent | Workflows, QMB | none | F10, F1 | Verdicts record the judge version | New |
| WF-13 | A run's home machine dies mid-run | M, Stop | Workflows | another machine adopts a run whose home died, refused while the home's heartbeat is fresh (HP ADOPT) | F7, F18 | A run is adopted once; the old home never resumes it | HP ADOPT |
| WF-14 | The PC was off for two days and missed scheduled runs | H, Friction | Workflows | catch-up after downtime (HP BUG1) | F11 | Missed runs either catch up once or are marked skipped, by a setting per trigger | HP BUG1 |

---

## 9. Mini apps holding units

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MA-01 | A unit lives in a mini app, and the app's breaker stops it after 3 errors, which is a process stop, not a risk stop | M, Money | Mini apps | `max_errors` default 3, `heartbeat_timeout` 10 s (`APPS/manifest.py:104-110`, here) | F16, F9 | Only the node sends orders; a mini app holding a unit is research only, and its breaker stops research, never protection | G2 trap 8, G4b Q5 |
| MA-02 | The machine an app lives on dies; a move is a snapshot plus a lease handover, with no remote restore | M, Stop | Mini apps | `APPS/supervisor.py:527-533`, `:1064` (G2 §5.1) | F18, F10 | The app's state of record lives in the Library, so a new home can start from it | G2 §5.1 |
| MA-03 | A newcomer installs an example app that imports deleted code and crashes | H, Friction | Mini apps | two of four examples import the deleted runtime (G4b §1.7) | F13 | Examples are built and tested in CI | G4b §1.7 |
| MA-04 | An app's `provides` contract changes shape and its consumers break | M, Stop | Mini apps, Contracts | `provides` and `feeds` as JSON Schemas (`APPS/manifest.py:148-167`) | F1 | Contract versions with an overlap window | New |
| MA-05 | The trading node as a mini app is a `money` app, which needs his signature to start; does every restart need it? | M, Stop | Mini apps, Node | `APPS/supervisor.py:542-547` (G2 §5.1) | F16, F11 | His signature binds a version, not a restart | Lens |
| MA-06 | `app_op {app: qmb}` fails because no app named `qmb` runs | H, Stop | Mini apps, QMB | `ENG/nodes/app_op.py:1-25` (G4b Q4) | F3 | QMB answers through the `app_op` route whether it runs as a host door or as a mini app | G4b Q4 |
| MA-07 | Several QMB variants are installed; which one does `backtest_run` call? | M, Silent | Mini apps, QMB | none | F2, F13 | A default named in settings; every result records which variant ran | Lens |
| MA-08 | A long backtest in an app needs more memory than he set | L, Stop | Mini apps | memory unlimited unless he sets a number (G4b Q5) | F14 | A limit hit is logged with the number that was set | G4b §3 row 8 |
| MA-09 | A mini app reads another app's output while that app is offline | M, Stop | Mini apps | reading an app's latest output is a Library read that works offline (HP APP2b) | F8, F15 | Outputs are Library artifacts with `stale_after` | HP APP2b |
| MA-10 | Two mini apps, or two QMB variants, publish under the same `provides` name, and a consumer reads the wrong one | M, Silent | Mini apps | `[provides]` names per manifest (`APPS/manifest.py:148-167`) | F4, F1 | Published names carry the app's own namespace; a collision is refused at install | New |

---

## 10. Contracts and APIs

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CA-01 | Routes carry no version and the API title is fixed at 0.1.0, so a UI or outside agent built today breaks silently on a change | H, Stop | Contracts | `CTL/server.py:415` (G2 §6) | F1 | A version on every seam, an overlap window, a deprecation notice that names the replacement | G2 §6 |
| CA-02 | The `unit` kind has an empty schema, so anything lands as a unit | H, Silent | Contracts, Library | `LIB/kinds/unit.schema.json:7-10` (G2 §3) | F12 | A real schema with every problem returned | G2 §3 |
| CA-03 | "The bot may not size" is in four layers; a half-done change leaves one layer sizing or refusing | H, Money | Contracts | `qml/src/qml/protocol/intents.py:1-7`, `qmf-risk/door.py:7-10`, QMB admission context, `qmn/src/qmn/seats/dispatch.py` (G1 §0 item 4) | F1 | All four layers move in one wave; a test sends a sized intent end to end | G1 §0 item 4 |
| CA-04 | Adding a venue means editing a closed enum in the node's law | H, Stop | Contracts, Venues | `VenueClientKind` is `ctrader`, `replay`, `conformance` (`qmn/src/qmn/venue/port.py:40-45`, here) | F3 | A new venue is a capability declaration plus an adapter behind the port | G3 §5 |
| CA-05 | Errors come in different shapes: tools give code, message and next step; the Library gives the first problem only | M, Friction | Contracts | `HAR/tools.py:188-213`; `LIB/kinds/__init__.py:46-55` (here) | F12 | One error shape with every problem | New |
| CA-06 | The PC and the node run different contract versions after an update on one side | H, Stop | Contracts, Node | none | F1, F15 | Both sides state their contract version on connect; the node keeps trading what it has and refuses new deploys until they match | Lens |
| CA-07 | The risk socket is built now and the risk session's design does not fit it | M, Stop | Contracts | none; the socket is a designed placeholder (C-06) | F2, F1 | The placeholder implements the same typed contract the risk session will fill | C-06, Lens |
| CA-08 | A unit's logic fingerprint does not match its stored source | M, Stop | Contracts, QML | Layer 2 refuses source that differs from the manifest (`conformance/layer2.py:292-302`, G1 §1.5) | F10 | Source and fingerprint travel together | G1 §1.5 |
| CA-09 | The same capability exists through two doors with different rules | M, Silent | Contracts | one catalog row per capability, every door derived from it (`CTL/catalog.py:1-10`, G2 §1.2) | F3 | New unit doors are catalog rows only | G2 §1.2 |
| CA-10 | An outside agent's observer token outlives its purpose | L, Friction | Contracts | tokens last 30 days (`CTL/service.py:89`, G2 §6) | F14 | Expiry shown; renewals are his | G2 §6 |
| CA-11 | A browser client cannot resume a stream, because EventSource cannot set the auth header | L, Friction | Contracts | fetch stream with an Authorization header (G2 §6) | F8 | Resume by `Last-Event-ID` | G2 §6 |
| CA-12 | A copilot-made pack, app or Library kind takes a name the core uses (a tool, a kind, a template id) | M, Stop | Contracts | tools are `mcp__qmx_<toolset>__<op>`; packs never carry hooks (`HAR/tools.py:1-12`, `HAR/packs.py:44`, G2 §1.2) | F4 | Core names are reserved; an extension's names carry its prefix | New |

---

## 11. The trading node

The node is the only part that sends orders (ruling 27). Its cases carry most of the money risk. Much of the safety already exists in QMN code that has never traded (G4a §2.2).

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| TN-01 | A reply is lost after an order went out; a resend opens the position twice | M, Money | Node | four outcomes with UNKNOWN as a state; nothing retries on UNKNOWN (`packages/qmf-venue/src/qmf/venue/commands.py:184-240`); the live client never retries after hand-off (`qmn/src/qmn/venue/live.py:1-35`, G3) | F7, F8 | A demo drill cuts the network after send and shows one position | Brief, R44-V02 |
| TN-02 | The node crashes after a fill and before journaling it, leaving an orphan position | M, Money | Node | reconcile with four verdicts, fixtures only (`qmn/src/qmn/reconcile/`, G3 §1.1) | F7, F9 | At start, reconcile against the venue before any unit runs; a position with no owner is put under protection and flagged, never adopted silently; a missing report is never "flat" | Brief |
| TN-03 | He presses the kill switch while the node is offline or unreachable | M, Money | Node, Contracts | venue-resident stop on every placement (`qmn/src/qmn/order/protection.py`); kill switch five levels (G3 §1.1); `qmx-recover` on servers (G4a §3 row 12) | F9, F15 | Every open position already has a stop at the broker; the kill reaches the node by more than one path; the last resort is the broker's own app, written down for him | Brief |
| TN-04 | Two nodes run the same unit: a restored server image, or a PC rehearsal and a server on one account | M, Money | Node | QMN pins the operator's machine (`qmn/src/qmn/host/configured_runtime.py:278-280`, G3 §1.1) | F18 | One lease per unit and account; a second claimant is refused and alerts | Brief |
| TN-05 | A token expires at night, or a refresh on one machine logs out every other copy of the same cTrader grant | H, Money | Node, Venues | access token about 30 days, refresh never expires; one refresher per credential; store before discard (`qmn/src/qmn/secrets/rotation.py`; FR-40; G3 §2.1) | F18, F13 | One grant per machine; expiry dates shown and warned ahead; a refresh test on demo | Brief, R38 §3.1 |
| TN-06 | The broker's weekend maintenance cuts the Open API and everyone reconnects at once on Sunday | H, Stop | Node, Venues | reconnect with gap replay (`qmn/src/qmn/venue/reconnect.py`) | F11, F17 | Maintenance windows in the venue calendar; reconnect with back-off; no entries until capabilities are re-verified; exits stay allowed | Brief, M10b |
| TN-07 | An exchange halts or hits a price limit; orders are rejected and stops do not fill | L, Money | Node, Venues | none | F19, F9 | The halt is a market event every unit sees; no entries during it; the journal records it | Brief, R54 §3.1 |
| TN-08 | The node dies and cTrader has no dead man's switch, so only resting stops protect | M, Money | Node | venue-resident stop rule (`order/protection.py`, G3 trap 3) | F9 | No order is placed without its stop at the broker | R38 §3.1 |
| TN-09 | Hyperliquid's dead man's switch cancels all open orders, stops included | M, Money | Node, Venues | none (no Hyperliquid code) | F9 | Use it only with stops re-placed after it fires, or not at all | R38 §7, R44-E05 |
| TN-10 | The node looks finished but cannot trade. Its only host profile is offline replay, and seven boot values and the kill-switch matrix are blank | H, Stop | Node | `qmn/src/qmn/host/configured_live_resources.py:38-58`; boot values (research 31 §1); matrix blank (GAP-0050) | F2 | Every number ships a starting default; the first real demo run is an early packet | G3 §1.1 |
| TN-11 | The one-click server setup fails halfway (an expired Tailscale key, a firewall step) | H, Stop | Node, DevOps | the connect dialog's rerun-safe steps, one row written last (`qmx_host/connect_compute.py:229-238`, G3 §1.4) | F11, F8 | Every step can be rerun; the dialog says which step failed and why | M10b |
| TN-12 | Self-healing loops: crash, restart, crash | M, Money | Node | crash-loop fold into stand-down-alive; restart never clears stand-down (FR-17) | F9, F13 | Restarts with back-off for faults; a repeated fault stands down entries and keeps exits; see the lead's call on healing (section 20) | FR-17, ruling 35 |
| TN-13 | The VPS provider reboots the server at 03:00 | H, Stop | Node | supervision under systemd (`qmn/src/qmn/host/_supervision.py`) | F11, F7 | After boot, the node reconciles, warms up, then trades; nothing trades before both | New |
| TN-14 | The WSL fallback shuts itself down when idle, its clock is unsynced, and its disk is on C: | H, Money | Node | WSL facts (research 31 §6.2) | F17, F13 | The node refuses to trade on an unsynced clock (QMN waits for sync, FR-8); idle timeouts set by the installer | R31 §6.2 |
| TN-15 | The laptop sleeps or loses power during a rehearsal on the PC | H, Stop | Node | none | F15, F13 | Rehearsal on the PC is for demo; a sleep is logged as a gap and the node reconciles on wake | N-08 |
| TN-16 | Deploying one new unit restarts the node and every other unit | H, Money | Node | none | F3, F11 | Units are added and removed one at a time; a node restart is only for node code | Lens |
| TN-17 | The PC and the server run different QMX builds, so a rehearsal proves nothing about the server | M, Silent | Node, DevOps | none | F13 | The connect self-test records the image digest; journal rows carry their writer's version | R44-V07 |
| TN-18 | The node's disk fills and journal-before-dispatch blocks entries | M, Stop | Node | FR-33 | F9, F13 | Disk alarms before full; exits still go | FR-33 |
| TN-19 | The socket to the broker stays open but delivers nothing (a dropped NAT path); the node shows "connected" | H, Money | Node, Venues | a 10 s heartbeat bound for cTrader (`packages/qmf-venue/src/qmf/venue/ctrader.py:123-145`) | F13, F9 | Heartbeat timeout forces a reconnect; "connected" is not "ready" until authenticated and subscribed | Nautilus (section 22) |
| TN-20 | A feed goes stale, and stale alarms flood every weekend | H, Money | Node | none | F17, F13 | A symbol is stale only inside its open calendar | T1-682, R44-E15 |
| TN-21 | Units outnumber what one connection allows (cTrader 50 requests a second; Hyperliquid 10 websockets and 1,000 subscriptions per IP) | M, Stop | Node, Venues | QMN's accumulator is one first writer per stream (`qmn/loop/accumulator.py`, R31 §1) | F18, F14 | One feed keeper per connection fans out to every unit on the machine | R12, R31 §2 |
| TN-22 | A quoting unit spends Hyperliquid's address action budget and then cannot cancel | M, Money | Node, Venues | a pacer with a protective reserve (`qmn/src/qmn/order/pacer.py`) | F14, F9 | Venue limits are data a unit reads; a share of the budget is kept for cancels and stops | R38 §3.8 |
| TN-23 | A partial fill: 1.3 lots of 2 fill, and the stop is set for 2 | M, Money | Node | `amend_protection` exists (`commands.py:600-616`) | F7 | Protection follows the filled quantity; the unit sees the real position | Brief, T1-682 |
| TN-24 | The broker rejects a stop as too close, or the market is closed, and the unit retries every tick | H, Stop | Node, Unit | typed outcomes and an error map; an unmapped code is UNKNOWN plus an alarm (`capabilities.py:1-40`, G3 §3.2) | F7, F12 | A typed rejection reaches the unit, which backs off | New |
| TN-25 | The broker changes a symbol's lot step, margin or digits without notice | M, Money | Node, Venues | verify-or-refuse at connect (`qmn/src/qmn/venue/verify.py`) | F19, F10 | A spec change is an event and a new instrument-record version; units on that symbol pause until it is accepted | New |
| TN-26 | The venue switches a symbol to close only (cTrader trading-mode change on futures-style CFDs) | L, Money | Node, Venues | none | F19 | The mode change is a market event: no entries, exits allowed | R54 §3.2 |
| TN-27 | Proof-campaign and readiness machinery (about 11,900 lines) refuses to let the node start | H, Stop | Node | `qmn/src/qmn/host/golden_scenarios.py` and siblings (G4a §2.2) | F2 | Subtract first | G4a §2.2 |
| TN-28 | The observability stack is down, and trading must go on | M, Stop | Node, DevOps | the engine exporter drops and counts, the four records stay the source of truth (`ENG/telemetry.py:1-20`, G2 §8) | F9, F13 | Telemetry is fire-and-forget; a test stops OpenObserve and shows units still trading | Brief |
| TN-29 | An automatic escalation fires falsely (a bad time source trips the clock halt) during a good session | M, Money | Node | four clock bands, halt at 250 ms (`qmn/src/qmn/time/discipline.py:1-7`, R54 §4.1) | F13, F16 | The reason is journaled; resuming after a risk stop is his; false fires are reviewed and the number tuned | New |
| TN-30 | The node on his PC needs a live key, and the QMX host refuses to store one anywhere | H, Stop | Node | `can_trade_live` refusal (`qmx_broker/adapters.py:137-146`, here); `venue_session.py:1-16` | F18, F15 | The node process owns its own key store on whichever machine it runs | G3 trap 10 |
| TN-31 | A new trading server needs its own cTrader app, and Spotware takes about a day to approve it | M, Stop | Node, Venues | "one app per trading server" (G3 §1.6) | F13 | Setup starts the app request on day one and shows it as a waiting step | R38 §3.1, funnel6 |
| TN-32 | The node runs in a region far from the broker's servers | M, Money | Node | measured 156-167 ms TCP connect from his PC to cTrader (R38 §3.1) | F13 | The setup measures round trip and shows it | R31 §3 |
| TN-33 | A clock step or pause on the host corrupts every timing until resync | L, Silent | Node, Clocks | wall-versus-monotonic suspect window, no entries until a stopped-node resync (FR-12) | F17, F9 | Exactly FR-12 | FR-12 |
| TN-34 | An "unused" module is deleted in the cut, and it was the one placing stops | L, Money | Node | blast radius is run before any cut (workflow step 4) | F12 | A test proves every order has a stop, before and after the cut | RT |

---

## 12. External connections: cTrader, Hyperliquid, CCXT and futures feeds

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| EX-01 | A cTrader spot event carries only the bid or only the ask | H, Silent | Venues | none on the PC host; QMN live client kinds (G3 §2.1) | F5 | Keep the last value per side | R33 §2 |
| EX-02 | cTrader depth is differential with no snapshot message, so after a reconnect the book is wrong | H, Silent | Venues | none | F11 | Rebuild the book after every reconnect before any unit reads it | R33 §2, R21 §3 |
| EX-03 | cTrader gives no trades tape, real volume or open interest, and a unit asks for volume | H, Silent | Venues, Unit | not offered (G3 §2.1) | F19 | Data levels declared per venue; a tick count is never labelled volume | R21 §3, R38 §3.1 |
| EX-04 | cTrader history comes one side per request, one week per request, five requests a second, and retention is unknown | M, Stop | Venues | `tick_span_within_cap` (`packages/qmf-venue/src/qmf/venue/ctrader.py:591-618`, R21 §3) | F14 | Page by the venue's own limits; measure retention once on demo | R21 §3 |
| EX-05 | The broker switches the Open API off for his account | L, Stop | Venues | none | F13 | Shown as a venue state with its reason | R38 §3.1 |
| EX-06 | CCXT symbols differ per exchange, and QMX's adapter refuses every contract market | H, Stop | Venues | spot-only filter (`qmx_broker/adapters.py:330-339`, here) | F3, F19 | Instruments named by one QMX id mapped to each venue's symbol | G4a §2.6 |
| EX-07 | A CCXT unified method is missing on one exchange, or the exchange has no sandbox (54 in 4.5.85) | H, Stop | Venues | demo rows refused where no sandbox exists (PR 224) | F3, F12 | The capability declaration is measured per venue, and a unit needing a missing capability is refused there | G4a §2.6 |
| EX-08 | A CCXT upgrade changes an exchange's behaviour | M, Silent | Venues | pinned 4.5.85 (`qmx-broker/pyproject.toml:6`) | F1 | Pin plus re-verification of capabilities on upgrade | New |
| EX-09 | Hyperliquid keeps only the last 5,000 candles, so history must be recorded by QMX | H, Stop | Venues, Library | none | F15 | The recorder starts with the venue link | R38 §3.8 |
| EX-10 | Hyperliquid's nonce window, one agent per process and agent wallets that expire within 180 days | M, Stop | Venues, Node | none | F18, F17 | One signer per process; expiry dates shown and warned ahead | R38 §3.8 |
| EX-11 | Above 1,000 open orders on Hyperliquid, new reduce-only and trigger orders are rejected, stops included | L, Money | Venues | none | F9, F14 | The node counts open orders and keeps room for protection | R38 §3.8 |
| EX-12 | Real futures order flow needs a paid feed, and whether a personal licence covers an algorithm is unconfirmed | M, Stop | Venues | Databento is a key check only (`providers/databento.py:1-59`, G3 §2.5) | F2, F3 | A ready seam with a placeholder; nothing in the core assumes a feed | R54 F-02 |
| EX-13 | A futures unit's contract changes at the roll (ES.c.0 rolls by calendar, volume or open interest) | M, Silent | Venues, Library | none | F19, F10 | The unit names a root and a roll rule; each trade names its contract | R54 §3.1 |
| EX-14 | A futures-style CFD on cTrader has no expiry field and turns close-only through an event | M, Money | Venues | none | F19 | The instrument record carries the at-expiry rule, and the event is mapped | R54 §3.2 |
| EX-15 | A CFD unit reads futures order flow as a proxy, and the price gap between the two moves | M, Silent | Venues, MIS | none | F19, F17 | Both series on one clock; the gap measured and stored | R54 §1.5 |
| EX-16 | IBKR needs a manual login each week; TopstepX bans orders from servers | L, Stop | Venues | none | F13 | The capability record states it and setup refuses an unattended node there | R54 §1.2 |
| EX-17 | A rate limit (HTTP 429) or a ban after bursts | H, Stop | Venues | cTrader limits encoded (`ctrader.py:123-145`) | F14 | Limits are the venue's own, read as data, with back-off | M10b |
| EX-18 | A venue outage or a stale feed while units hold positions | M, Money | Venues, Node | none beyond resting stops | F9 | Protection is at the venue before the outage starts | T1-682 |
| EX-19 | Demo behaves differently from live (fills, spreads, liquidity), so demo proof overstates | H, Silent | Venues, QMB | demo and live are separate endpoints (R38 §3.1) | F13 | Journals keep demo and live apart; costs are calibrated per world | New |
| EX-20 | Perps funding flips sign, and a unit holds through the funding time | H, Money | Venues, Unit | none | F19 | Funding is an event, a reading and a cost (research 23) | T1-682 |
| EX-21 | MT5 forces Windows and a running terminal per account | M, Stop | Venues | declaration only (`adapters.py:59-72`, G3 §2.4) | F3 | A venue that needs a desktop app runs on a machine that has it; the capability record says so | G3 trap 9 |
| EX-22 | A crypto exchange lists a new contract, or delists one a unit holds | L, Money | Venues | none | F19 | Listing changes are instrument-record events | New |

---

## 13. DevOps

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DO-01 | Two monitoring stacks: the node's Grafana, Loki and Prometheus, and QMX's OpenObserve | H, Friction | DevOps | `qmn/deploy/observability/` (831 lines); OpenObserve pinned (G4a §0) | F3 | One home for logs | G2 trap 10 |
| DO-02 | Monitoring is off by default, no target is named, and he believes it is on | H, Silent | DevOps | `[telemetry] send_to` defaults to `off` (`qma-harness/src/qma/telemetry.py:25-29`, G2 §8) | F13 | Off shows as off on his screen | New |
| DO-03 | OpenObserve has never run on real telemetry | H, Stop | DevOps | v1.1.2 downloaded and pinned (G4a §3 row 10) | F13 | An early packet starts it with real events | G4a |
| DO-04 | Known monitoring gaps: incidents not exported, a copy age always empty, two log files absent, an outside note stored unredacted | M, Silent | DevOps | backlog rows (G2 §8) | F13 | Each gap closed or listed | G2 §8 |
| DO-05 | A restore drill or a restored backup cuts over automatically into a running node | L, Money | DevOps, Node | automatic cutover refused (FR-63) | F16 | Cutover is his act | FR-63 |
| DO-06 | A restore brings back an old unit version and its old state | M, Silent | DevOps | secrets never travel (PR 231, G2 §11) | F10, F16 | A restored unit lands as a draft, never live | New |
| DO-07 | QMX on the PC updates while the node is trading | M, Stop | DevOps | sync before update (PR 234) | F1, F15 | The node keeps trading on its version; the PC talks to it by contract version | New |
| DO-08 | The node's CI lane and the whole GitHub battery do not run on PRs into `engine/base` | H, Silent | DevOps | `.github/workflows/qmn-ubuntu-24.04.yml:9-14`, `battery.yml:4-8` (G3, G4a §3) | F12 | The node's tests run on every build branch; `just ci` locally covers them today | G3 §1.1 |
| DO-09 | Credentials from old Hermes logs get copied into the repo | M, Money | DevOps | `tools/secret_scan.py` (G2 §2.1) | F14 | The secret scan runs on every commit | R10 §6, standing order 12 |
| DO-10 | A health check checks the wrong thing, so the process is up while the loop is stuck | H, Money | DevOps, Node | seven health states and a liveness heartbeat (`qmn/src/qmn/observability/liveness.py`, G3 §1.1) | F13 | Health is progress: last decision per unit, last quote per symbol, last journal write | Nautilus (section 22) |
| DO-11 | Alert fatigue from weekend and holiday alarms, so a real alarm is ignored | H, Friction | DevOps | none | F17, F13 | Alarms only inside open calendars, and grouped | R44-E15 |
| DO-12 | The server firewall step locks him out | L, Stop | DevOps | five-minute undo and `qmx-recover` (G4a §3 row 12) | F11 | The undo window and the recovery script | G4a |
| DO-13 | A store opens at a newer version than the code understands, after a rollback | M, Stop | DevOps | stores open, upgrade after a copy, or refuse by name (PR 213) | F1 | Refuse by name, never guess | G2 §6 |
| DO-14 | Secrets leak onto a public surface (logs, a served page) | L, Money | DevOps | one redaction seam (HP SEC1A); a secret on a public surface is refused (FR-39) | F14 | Exactly those | HP SEC1A, FR-39 |

---

## 14. Clocks

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CK-01 | His PC's clock drifts: Windows Time is stopped, start type Manual, and cTrader stamps everything with the receive time | H, Silent | Clocks | QMN checks its own clock; the QMX host has no clock check (G3 §0 item 6) | F17, F13 | Every machine reports its offset; data recorded unsynced is marked | Brief, G3 trap 6 |
| CK-02 | The DST mismatch weeks: London and New York are 4 hours apart instead of 5 (8 to 29 Mar 2026; 25 Oct to 1 Nov 2026) | H, Money | Clocks | IANA zones with cron's DST rules (`ENG/triggers/cron.py:1-7`) | F17 | Session rules in the market's own zone; a test across both mismatch weeks | Brief, R54 §4.1 |
| CK-03 | A Singapore node and a London node keep different local times, and a rule reads the node's local time | H, Money | Clocks, Node | local time only for display, always labelled (`chrono.py:940-1055`, G2 §9) | F17 | The node's own zone never enters a rule; both nodes compute the same session from the same instant | T-01 ("the trading node is perhaps a firm", T3:903) |
| CK-04 | The time-zone database is pinned two IANA years old (2025.2 against 2026.6) | M, Silent | Clocks | `uv.lock:2002-2003` (G3 §5) | F1, F13 | The pin's age is shown and flagged past a number | G3 §5 |
| CK-05 | The broker's server runs at GMT+2 or +3, the history is UTC, and the daily bar boundary differs | H, Silent | Clocks, QMB | daily boundary measured per broker (G3 §3.2) | F17 | One conversion at the venue boundary | R54 §4.1 |
| CK-06 | Smeared and non-smeared time sources are mixed around a leap second | L, Silent | Clocks | QMN rule "no smearing sources" (R54 §4.1) | F17 | One source kind per machine | R54 §4.1 |
| CK-07 | Backups, first start and the host's command line use the machine's local zone | M, Friction | Clocks | `HO/host.py:788`, `HO/first_start.py:1512`, `HO/__main__.py:195` (G2 §9) | F17 | UTC inside; local only on screen | G2 §9 |
| CK-08 | WSL's clock is unsynchronised | H, Silent | Clocks | research 31 §6.1 | F17 | The node waits for sync before trading (FR-8) | R31 |
| CK-09 | Hyperliquid rejects signed actions whose nonce falls outside its window, so a drifting clock stops trading | M, Stop | Clocks, Venues | none | F17 | Clock band checked before signing | R38 §3.8, R54 §4.1 |
| CK-10 | A "same minute of the week over the last 20 weeks" baseline breaks for weeks after each DST change | M, Silent | Clocks, MIS | none | F17 | Baselines in venue session time; a short history shows as thin | R44-E07 |
| CK-11 | A cron time is skipped or repeated at a DST change | L, Friction | Clocks | with cronsim, a skipped time runs once after and a repeated time runs once (G2 §9) | F17 | Already handled | G2 §9 |
| CK-12 | Exchange calendars lag (an open-source CME break still shown as 4:15-4:35 New York) | M, Silent | Clocks | none | F10, F17 | Calendars versioned with a maximum age before they count as suspect | R54 §4.1 |
| CK-13 | "Five trading days" means nothing for a 24/7 unit | M, Friction | Clocks | none | F17 | Durations in calendar time or closed trades for 24/7 markets | R44-E13 |

---

## 15. The operator, install and first run

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OP-01 | A newcomer's first install fails silently (wrong Python, `uv` missing, a blocked download, the first-start card never shows) | H, Stop | Operator, DevOps | "the host names what did not open" (PR 222); a 77-check first-start run on a blank profile (G4a §2.1) | F13, F2 | A first-run checklist with every step's state and what to do | Brief, CC-15 |
| OP-02 | The first real start on his own folder, with his logins, has never happened | H, Stop | Operator | G4a §2.1 | F13 | A named early step in the build | G4a §2.1 |
| OP-03 | He promotes the wrong version of two units with similar names | M, Money | Operator | governed drafts (G2 §3) | F16, F13 | Promotion shows what changed against what is live | New |
| OP-04 | He is away for a week: units trade, nightly workflows fail, nobody notices | H, Silent | Operator | none | F15, F13 | Nothing waits on him except promotion and resuming after a risk stop; a digest lists what failed | New |
| OP-05 | He edits a number in the UI while a trade is open | H, Money | Operator, Unit | none | F10, F11 | An edit is a new settings version, effective at the next decision, journaled; never mid-order | Lens |
| OP-06 | His laptop's C: has 16 GB free and something writes there (WSL, caches) | H, Stop | Operator, DevOps | the QMX folder resolver prefers the roomiest non-system drive (`qmx_home/__init__.py:734-741`, G2 §7) | F13 | Disk per drive shown | R31 §6.1, R44-V06 |
| OP-07 | One word means two things on his screens ("node setup" sets up a QMX server, not the trading node) | H, Friction | Operator | `qmx_control/node.py:1-30` (G4a §0 item 1) | F20 | Words fixed once in the glossary | G4a §0 |
| OP-08 | Mock data on a screen looks real (a demo account shown as "IC Markets live") | M, Silent | Operator | backend mock data removed (PRs 215 to 217); UI default remains (G4a §1.2) | F13 | Every figure shows its world | G4a §1.2 |
| OP-09 | He tests at the weekend, nothing trades, and it looks broken | H, Friction | Operator | none | F17, F13 | The screen says the market is shut until when | New |
| OP-10 | He presses kill twice, or resume while the cause is still there | M, Money | Operator, Node | operator-only resume per scope (G3 §1.5) | F7, F16 | Kill is idempotent; resume shows the open causes first | RT |
| OP-11 | Speech-to-text puts a misheard name on a unit or template | M, Friction | Operator | none | F10 | Names are labels; identity is the id | New |

---

## 16. For the risk session

Risk and sizing are out of this run's scope but part of the unit (R-01). These cases go to that session with the pack (`RISK-SIZING-PACK.md`). This run only leaves the socket and the placeholders; no maths here.

| ID | What happens | Odds, harm | Where it shows here | What this run leaves for it | Source |
| --- | --- | --- | --- | --- | --- |
| RS-01 | The computed size is under the minimum lot (a $300 account), so it rounds to nothing or doubles the risk | H, Money | QB-08 | a declared rounding rule slot, default "round down, skip under the minimum" | T1-682, R-09 |
| RS-02 | Self-tuning drifts toward bigger risk | M, Money | UT-06 | every movable number has bounds from QMB; the "tighten, never loosen" rule belongs on the account floor | T1-682, STATE "Owed" |
| RS-03 | Correlation spikes across every unit at once | M, Money | the MIS's dispersion reading (funnel5) | the MIS publishes a dispersion reading; the control is the risk session's | T1-682, R-06 |
| RS-04 | The same idea on 1m and 5m, or 20 matches that are one bet | H, Money | U-09 | units carry a family id so correlated exposure can be counted | U-09, funnel5 |
| RS-05 | The node's kill line flattens, while standing order 7 says a risk rule "stops" a unit | M, Money | G3 trap 11 | the verb is the risk session's to settle | G3 trap 11 |
| RS-06 | R is undefined when invalidation is a condition, not a price | M, Silent | UT-08 | trades without R are flagged | R44-E03 |
| RS-07 | Size grows back after a cut; house money | M, Money | none | the socket accepts state from the unit's own journal | R-07 |
| RS-08 | A placeholder sizer or exit reaches live | M, Money | UT-07 | placeholders labelled on every trade and at promotion | U-04 |
| RS-09 | Margin jumps at the session close (futures intraday against overnight margin), forcing a liquidation | M, Money | R54 §3.3 | margin per session in the instrument record | R54 §3.3 |
| RS-10 | Two units on one netting account | H, Money | UT-14 | the account record states netting or hedging | R44-E04 |
| RS-11 | A daily loss limit must fire with the PC off; no account guard code exists | M, Money | R31 §1 | guards run on the trading machine (standing order 10) | R31 §1, R-12 |
| RS-12 | An automatic fallback to general settings after a drift alarm breaks standing order 7 | M, Money | R24 | the decay check informs; who acts is the risk session's | R24 |
| RS-13 | A gap through the stop makes a loss bigger than 1R | H, Money | QB-07 | fills at the first tradable price; the loss accounting is the risk session's | New |
| RS-14 | Perps funding eats a scalper's edge | M, Money | EX-20 | funding as a cost in QMB | T1-682 |
| RS-15 | The kill-switch matrix values are blank and operator-owned | H, Stop | TN-10 | starting defaults labelled placeholders | GAP-0050 |
| RS-16 | The old system's special ("radioactive") sizing must be accounted for when judging | M, Silent | B-09 | trades record equity, session and streak so old sizing can be replayed | R26 |
| RS-17 | A decay alarm suggests "back to paper", but only a risk rule may stop a unit automatically | M, Money | R08 §2.3 | the alarm informs; the action is the risk session's call | R08 §2.3 |
| RS-18 | Leverage changes on a venue (Hyperliquid `setLeverage`, broker margin changes) shift risk with no unit change | M, Money | TN-25 | leverage and margin are instrument-record fields with versions | G4a §2.6, Lens |

---

## 17. The families, and the property that handles each

The 267 cases fall into ten families. Each family has one property that handles it without special code. This is the table the architecture versions should be scored on first.

| Family | Cases (examples) | Property |
| --- | --- | --- |
| Something is unknown: an order outcome, a stale feed, a data hole, a clock | TN-01, TN-02, TN-19, TN-20, MIS-02, LD-01, QB-18, CK-01 | F7 unknown is a state; F13 health is progress; F17 one time scale |
| Something has two owners: two nodes, two journal writers, two grants, two registries | TN-04, TN-05, JR-01, QML-24, LD-15, AG-10 | F18 one owner per stream and position |
| Something changed under a running thing: a unit version, a block fix, a broker spec, a schema, a checker, a QMB variant | UT-04, QML-12, TN-25, UT-19, UT-03, QB-13 | F10 immutable versions; F1 versioned contracts |
| Something means different things on different venues: digits, contract size, volume, sessions, the trading day | QML-05, QML-06, QML-09, UT-13, QB-21, EX-03 | F19 typed market facts |
| Something knows the future: look-ahead, late confirmation, forming bars, hindsight labels | QML-01, QML-02, QML-18, QML-19, QML-20, MIS-05 | F5 declared inputs with knowable times |
| Research and live disagree | QB-23, MIS-04, QML-03, EX-19 | F6 same code in both worlds |
| Protection depends on something that can be down | TN-03, TN-08, TN-09, TN-28, MIS-01, JR-02 | F9 fail closed for risk, open for protection; F15 standalone |
| A check lies, either way: a pass on nonsense, a block on good work, a skipped check | UT-01, UT-02, AG-01, AG-02, QB-15, QB-09 | F12 every problem at once, no false positives, checked at the door |
| Something restarts: a crash, a reboot, a warm-up, a redeploy | UT-09, UT-10, TN-13, TN-16, WF-14 | F11 lifecycle with reasons and saved state |
| The core grows when something new is added, or two extensions take one name | CA-04, EX-06, DO-01, JR-10, MA-10, CA-12 | F3 one way to add a thing; F2 defaults; F4 owned names |

---

## 18. How this foundation fails in six months of daily use

Run with `bmad-advanced-elicitation`, methods picked by name with `scripts/pick_methods.py show "Pre-mortem Analysis" "Red Team vs Blue Team"` (CHECKED, rows 59 and 21 of `assets/methods.csv`). Headless: the lead's brief pre-set the methods, so no menu was served, and the changes are written here rather than proposed and waited on.

### 18.1 Pre-mortem: it is May 2027 and the foundation has failed. Why?

Pattern per story: the failure, the causes, the prevention (as properties).

| Story | What went wrong | Causes | Prevention |
| --- | --- | --- | --- |
| PM-1 "Everything lived on paper" | No unit ever reached live in six months | blank boot values and kill-switch matrix (TN-10), proof machinery refusing to start (TN-27), a judge chain so strict nothing passes (R44-A13), placeholders that block demo (R44-A15) | F2 every slot works out of the box; subtract the proof machinery first; a short default judge chain |
| PM-2 "The backtests lied" | Live results far below backtests on every unit | spreads at rollover (QB-03), missing swaps and funding (QB-04), look-ahead inside a block (QML-01), tries counted only at some doors (QB-09), late confirmation price (QML-18) | F5, F6, F19, and costs from the market journal |
| PM-3 "Three weeks of silent holes" | Dukascopy returned empty hours; readings and tuning were computed on gaps | no preflight (LD-01, QB-18), stale readings read as fresh (MIS-02) | F13 and F8: a data preflight on every read, freshness on every reading |
| PM-4 "The night the token died" | A refresh on the PC logged out the node; it stood down at 02:00 | two machines on one grant (TN-05), the PC side not knowing the node existed | F18 one grant per machine; F9 stops already at the broker |
| PM-5 "Two nodes" | A restored server image started trading beside the new one | no lease per unit and account (TN-04), restore lands live (DO-06) | F18 leases; F16 restores land as drafts |
| PM-6 "The checker became the enemy" | Agents routed around false positives with plain Python and `python -c`, so the checks stopped protecting | false positives (UT-02), a check on the editor only (AG-02) | F12: refuse only proven violations, check at the door, overrides recorded |
| PM-7 "Version soup" | No result from March could be reproduced in May | dictionary entries, blocks, QMB variants, checker versions and data files all changed in place (QML-11, QML-12, QB-13, UT-03, LD-05) | F10 and F1: every record pinned and versioned, every result fingerprinted |
| PM-8 "Disk full at 03:00" | A unit's error loop flooded the logs; the journal could not write; entries stopped across the node | logs and journals sharing one budget (JR-03, TN-18) | F9 and F13: separate budgets, rate-limited logs, alarms before full |
| PM-9 "Nobody noticed" | He learned of a two-day stand-down from his broker's statement | monitoring off by default (DO-02), OpenObserve never started (DO-03), two stacks (DO-01), "process up" read as healthy (DO-10) | F13: off shows as off, health is progress, the off-server liveness heartbeat alerts |
| PM-10 "The core grew" | Every new market class added code to the core: a venue enum, a calendar, a data kind, a journal shape | closed enums (CA-04), one calendar (UT-13), quotes-only replay (QB-02), market facts copied per unit (JR-10) | F3: a new thing is a declared record plus an adapter behind an existing door |
| PM-11 "DST week" | The London sniping window ran an hour off for a week, twice a year | rules in node-local time (CK-03), "London 13:00 = New York open" (CK-02) | F17 |
| PM-12 "The copilot remade it" | A copilot edit to a template changed what a live unit did, with no promotion | live behaviour reading editable content (WF-09, WF-12) | F10 and F16: live units pin versions; only his click moves them |

### 18.2 Red team against blue team

Pattern: what the blue side has, how the red side attacks it, how the core hardens.

| Attacker | Blue side today | Attack | Hardening (property) |
| --- | --- | --- | --- |
| RT-1 A cheap agent gaming the checker | Layer 1 and 2, the AST scan | hides thresholds as literals, uses `exec` to read a file, writes a unit with `python -c`, makes a unit that trades on 3 instants and nothing else | the check at the door (F12), the child-process sandbox as the real wall (F14), a "does it trade" check on real bars (UT-01) |
| RT-2 An overfitting agent | tries counted at QMB's door | scores 500 variants in a script step without the door | results without a door run id are refused (F12); reads counted per family (QB-09) |
| RT-3 A poisoned source | sources as Library items | a video description tells the agent to "use 10% risk" | sources are marked data, numbers come from tools (F14, F13) |
| RT-4 A broker quirk | CT-18 verify-or-refuse | lot step changes overnight, symbol turns close-only, stops rejected as too close, Sunday maintenance | specs as versioned records and events (F19, F10); typed rejections the unit backs off on (TN-24) |
| RT-5 The network | UNKNOWN outcomes, reconcile | a half-open socket that accepts writes and delivers nothing; a reply lost after send | heartbeat timeout and "connected is not ready" (TN-19); no blind resend (F7) |
| RT-6 The operator at 02:00 | his clicks are the only promotion | edits a number mid-trade, promotes the wrong version, presses kill twice, restores an old backup | edits as versions effective next decision (OP-05); promotion shows the diff (OP-03); kill idempotent (OP-10); restores land as drafts (DO-06) |
| RT-7 The clock | QMN clock bands | Windows Time stopped, WSL drifting, a DST week, a leap smear | F17: every machine reports its offset and marks unsynced data |
| RT-8 A future maintainer or builder agent | tests and house rules | adds a venue by editing the core enum; adds a new journal row shape for one unit; deletes the "unused" module that placed stops | F3 one way to add; F1 versioned shapes; a stop-on-every-order test before and after any cut (TN-34) |
| RT-9 The data vendor | dataset cards with digests | replaces an archive file, changes the stamp unit, puts up a bot wall that returns empty files | F10 a new checksum is a new version; per-file stamp checks; empty is a failure (LD-01, LD-03, LD-05) |

---

## 19. How the skills ran, and the edge-case lens findings

**Plan, as the skill asks to announce it.** The content is documents that define behaviour (`architecture/00-ledger.md` and the six grounding files). The lenses are edge-case (the main pass), then verification-gap and adversarial where they help. The solutions round (step 1) had written nothing yet when I ran (`funnel/solutions/` was empty, CHECKED by `ls`), so its options were not in scope. No sub-agents: each lens ran in sequence by me, per the skill's own fallback. The BMad overrides' factory facts and `on_complete` steps were ignored (workflow file, fact 5). Output went into this file, not `_bmad-output`.

**Edge-case lens.** I walked every ruling in the ledger that sets a behaviour, and every BUILT seam in the grounding, for the branch it leaves unhandled. Handled branches were dropped. Most unhandled paths were already harvested (R44's 15 edge findings, the node's failure register, the grounding traps), and they appear in the tables with their source. The findings new to this run are below in the lens's own four fields, each pointing at the table row that carries it.

| Row | location | trigger_condition | guard_snippet | potential_consequence |
| --- | --- | --- | --- | --- |
| TN-12 | ledger CC-11; STATE ruling 35 | Node restarts after a crash; is resuming entries a promotion? | Technical faults heal automatically; risk-rule stops wait for his resume | Units sit idle after every crash, or risk stops resume silently |
| UT-07 | ledger U-04 | Placeholders ruled for backtest and demo; the live branch is unstated | Label placeholders at promotion and on every trade | Placeholder sizing trades real money unnoticed |
| UT-23 | ledger U-13 | General settings and a market version both admitted for one market | One admitted version per unit and market at a time | Two versions trade one market and double the exposure |
| QB-13, MA-07 | ledger B-00; STATE ruling 22 | Several QMB variants exist; which result counts? | Every result records the variant and its version | Judging mixes numbers from different engines |
| QML-11 | ledger D-06 | Entries edited through the authoring door while units cite them | Units pin entry versions; an edit makes a successor | Units silently change meaning |
| CA-07 | ledger C-06 | The socket is filled later; the placeholder's contract may differ | The placeholder implements the final typed contract | The risk session's result forces a core rework |
| UT-20 | ledger CC-08, MA-03; `qmn/src/qmn/seats/admission.py` | Plain-Python unit asked to trade; seats require QML conformance | A runtime contract small enough for plain Python | Plain Python can never go live |
| WF-09 | ledger A-07 | Copilot remakes a template that a live unit reads | Live units pin the versions they read | Live behaviour changes without a promotion |
| OP-05 | memory "configurable = UI-editable always" | A number is edited during an open trade | Edits are versions, effective at the next decision | An open trade's exit changes mid-flight |
| UT-03 | ledger Q-06 | The checker's version changes | Each verdict records the checker version | A live unit's status flips silently |
| MA-05 | G2 §5.1 (`APPS/supervisor.py:542-547`) | The node as a money mini app restarts | His signature binds a version, not a restart | The node cannot heal itself without his signature |
| TN-16 | ledger N-02 | Deploying one unit restarts the node | Add and remove units one at a time | One deploy interrupts every live unit |
| CA-06 | ledger C-01, N-02 | PC and node versions diverge after a one-sided update | A contract-version handshake on connect | The node rejects or misreads the PC's requests |
| RS-18 | ledger X-02 | A venue changes leverage or margin | Leverage and margin as versioned instrument fields | Risk shifts with no change to the unit |

**Verification-gap lens.** Where a check exists but would not fail if the behaviour broke: the golden slice (UT-01), the in-process isolation stamp (QML-15), the silent runner (QB-15), the Library check that reports one problem (AG-01), and the CI lanes that do not run on `engine/base` PRs (DO-08). All five are in the tables.

**Adversarial lens.** Run as the red team in section 18.2, with nine attackers.

**Advanced elicitation.** Pre-mortem and red team, section 18. The skill's menu loop and its "ask before applying" step were skipped, because the brief pre-set the methods and a sub-agent never waits on him (workflow file, rule 4.2).

---

## 20. Lead's calls

Each is a default I set because the ledger does not settle it. Each says what, why, and how to undo.

1. **The odds and harm scales** (H, M, L; Money, Silent, Stop, Friction). The reason is that the brief asks how likely and how bad, and a four-word harm scale is enough to sort cases without a scoring machine. To undo it, use any other scale; the rows do not depend on it.
2. **Healing after a technical fault resumes entries by itself; a risk stop waits for him.** After a crash, a reboot or a lost connection, the node restarts with back-off, reconciles, warms up, and resumes entries, because the unit was already live and nothing new is promoted. A stand-down caused by a risk rule, or by the same fault repeating, keeps exits and stops working and waits for his resume. The reason is that his ruling 35 asks the node to heal itself, and standing order 7 keeps risk stops his. Today QMN does the stricter thing, and only his act clears a stand-down (FR-17). To undo it, keep FR-17 as it is, so every stand-down waits for him.
3. **A mini app other than the node never holds live trading.** A mini app may hold a unit for research, backtests or paper on QMB. The reason is that only the node sends orders (ruling 27), and an app's breaker is a process stop, not a risk stop (MA-01). The node itself may be a mini app (ruling 43). To undo it, allow live units in an app on the node, with its breaker mapped to "stand down entries".
4. **Placeholders are shown at promotion, never blocked.** The reason is that there are no money gates (standing order 6), and only he promotes. To undo it, refuse promotion while any slot holds a placeholder.
5. **Heuristic checks warn; only proven violations refuse.** The reason is his rule, "we have to make sure there are no false positives" (T3:1264). To undo it, let a heuristic refuse once its record shows no false positives over a chosen number of units.
6. **An open position belongs to the unit version that opened it.** The reason is that CT-29 already attributes the whole trade to the opener, and it keeps journals clean. To undo it, hand open positions to the new version at deploy.
7. **Settled topics appear only as data fields.** Data licences, the live key and his country are recorded on cards and records, never as cases for him (ledger "Settled"). Nothing to undo.
8. **"The 192 things a site must handle" is read as the 22 Oct resilience list plus the hardening packets.** The reason is that no numbered list of 192 exists on disk. If he names a different list, harvest that one instead.
9. **Each case is counted once,** under the part that must handle it, even when it belongs to several families. Nothing to undo.
10. **The kill switch's last resort is the broker's own app,** written down for him as a step. The reason is that, with the node unreachable, only the broker can act on the account, and QMX cannot touch money by design (CC-13). Nothing to undo.

---

## 21. How his words were checked, and what is not verified

**Quote check.** A script, `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\e1\check_catalogue.py` (run as `python -I check_catalogue.py <catalogue> <operator folder>`), reads every quote of his with its `Tn:line` in this file and looks for the quoted text, whitespace normalised, on the cited line of the cited transcript. It splits lines on `\n` only, per the ledger's warning about stray carriage returns. Result on 31 Oct: 13 quotes found on their cited lines, 0 not.

**Counts.** The same script counts the rows. There are 267 part rows (QML 26, UT 23, QB 24, LD 17, MIS 14, JR 17, AG 16, WF 14, MA 10, CA 12, TN 34, EX 22, DO 14, CK 13, OP 11) and 18 risk rows, with no duplicate ids. 212 part rows cite an earlier file, ruling or code fact; 55 are new or from the lens run. A second pass confirmed that every row's property cell names only F1 to F20 and that every property is used by at least one row. The file holds no long dash.

**Not verified.**
- Whether Hyperliquid's trigger orders can carry the venue-resident stop the node requires (G4a "Not verified").
- Whether cTrader rejects a repeated client order id; TN-01 rests on the node never resending, not on venue dedupe.
- The node's behaviour is read from code and docstrings; none of it has met a broker (G3, G4a).
- Odds and harm are my estimates from the sources, not measured rates.
- The white-label facts were read on the vendors' own pages today; their prices and limits are not used anywhere as QMX numbers.

---

## 22. White-label lessons: how solid cores stay small

Read today with Exa on each vendor's own pages. Paraphrased; no outside text is quoted. Each lesson ends with the checklist item it feeds.

### Shopify

- **Versioned APIs with an overlap window.** A new API version ships every quarter, named by date. Each stable version is supported for at least 12 months, so consecutive versions overlap by at least nine. A call to a retired version is answered by the oldest supported one. A deprecation is announced with migration steps, applied across all supported versions, and removed in a later release; deprecated calls are counted against the app that made them and shown on its dashboard. Source: https://shopify.dev/docs/api/usage/versioning. Feeds F1.
- **Webhooks are at-least-once.** Each delivery carries a signature and a delivery id. Handlers must be idempotent and skip a repeated id. Failed deliveries are retried eight times over four hours, after which a subscription made through the Admin API is removed. Order is not guaranteed, so timestamps order events. Delivery is not guaranteed either, so Shopify tells apps to run reconciliation jobs that fetch what changed. Sources: https://shopify.dev/docs/apps/build/webhooks ; https://shopify.dev/docs/apps/build/webhooks/verify-deliveries ; https://shopify.dev/docs/apps/build/webhooks/troubleshoot. Feeds F8.
- **Metafields and metaobjects extend the data model without changing the core.** A definition comes first: a name, a namespace, a type and validation rules. App-owned data lives in a reserved namespace so it cannot collide with the merchant's or another app's. Apps declare definitions in their `shopify.app.toml`. Sources: https://shopify.dev/docs/apps/build/custom-data ; https://shopify.dev/docs/apps/build/metafields. Feeds F3, F4.
- **Functions are sandboxed, declared and deterministic.** Extension logic compiles to WebAssembly, declares an input query of exactly the data it reads, and returns the same output for the same input, so a failing run is reproduced locally from its copied input. Limits are measured and every limit has its own typed error. Sources: https://shopify.dev/docs/apps/build/functions/monitoring-and-errors ; https://shopify.dev/docs/apps/build/functions/optimize-instruction-counts. Feeds F5, F14, F13.

### Wix

- **Extension parts are immutable and versioned.** Every change to an app component creates a new version; published versions are never deleted; the draft is version zero. An app release bundles the latest version of each part. Source: https://dev.wix.com/docs/api-reference/app-management/app-extensions/app-extensions/introduction. Feeds F10.
- **Major and minor releases.** Minor releases reach users automatically. Major releases wait for the user to accept them, and adding permissions is a major release. Source: https://dev.wix.com/docs/build-apps/manage-your-app/versioning/about-app-versioning. Feeds F16 (new powers need his act) and F1.
- **One contract whether hosted or self-managed.** An app runs on Wix's servers or on the developer's own and registers the same extensions either way. Sources: https://dev.wix.com/docs/sdk/articles/getting-started/about-self-hosting ; https://dev.wix.com/docs/overview/backend-services/backend-development-on-wix. Feeds F15 (the PC and a server run the same thing).

### WordPress

- **Never edit the core; extend it through hooks.** Actions run code at a point; filters take data, change it and return it. Core uses its own hooks for its default behaviour. Callbacks run in priority order, and hook names carry a prefix to avoid collisions. Plugins get activation, deactivation and uninstall hooks. Sources: https://developer.wordpress.org/plugins/intro/ ; https://developer.wordpress.org/plugins/plugin-basics/ ; https://developer.wordpress.org/plugins/hooks/custom-hooks/. Feeds F3, F4, F2, F11.
- **The handbook warns that removing hooks or changing priorities makes interactions hard to see.** So the lesson is few, explicit extension points, not many. Source: the plugin-basics page above. Feeds F20.
- **Deprecation and misuse are told to the developer at the call.** One helper says a function is deprecated since a version and names its replacement; another says a function was called the wrong way. The editor's backward-compatibility rule keeps names, argument order and return types stable. Sources: https://developer.wordpress.org/reference/functions/_deprecated_function/ ; https://developer.wordpress.org/reference/functions/_doing_it_wrong/ ; https://developer.wordpress.org/block-editor/contributors/code/backward-compatibility/. Feeds F1, F12.

### QuantConnect LEAN

- **Pluggable modules with defaults, passing typed objects one way.** The algorithm framework has five modules (universe, alpha, portfolio construction, risk management, execution); each passes one typed object to the next, and the modules must not talk to each other. Null models are the "do nothing" defaults. LEAN itself says the framework suits portfolio and ranking strategies, and a strategy that breaks the separation should use its classic design. That matches his ruling that a unit is one complete algorithm: the slots live inside the unit. Source: https://www.quantconnect.com/docs/v2/writing-algorithms/algorithm-framework/overview. Feeds F2, F3.
- **The engine owns the loop order.** Each time step runs a fixed order: symbol changes, data, cash, fills, margin calls, settlement, corporate actions, then the algorithm's data handler, then the framework modules. Source: https://www.quantconnect.com/docs/v2/writing-algorithms/key-concepts/algorithm-engine. Feeds F6 (the core, not the unit, owns what happens between decisions).
- **Warm-up is a fast-forward with no trading.** In a backtest it moves the start earlier; live, it replays history up to now. Orders are refused while warming, and a flag says so. Source: https://www.quantconnect.com/docs/v2/writing-algorithms/historical-data/warm-up-periods. Feeds F11.

### NautilusTrader

- **One kernel for backtest, sandbox and live,** and the same strategy code in each. The docs name the places where live still differs: venue rules, transport, timing, persistence, outside activity, reconciliation. Sources: https://nautilustrader.io/docs/latest/concepts/architecture/ ; https://nautilustrader.io/docs/latest/concepts/live/. Feeds F6.
- **Unknown is a state.** A command ends as a definitive local failure, a definitive venue result, or an unknown live outcome that stays in flight until streams, queries or reconciliation resolve it. Delivery is not exactly-once, and a retry is allowed only when a repeat is provably safe. Source: https://nautilustrader.io/docs/latest/concepts/execution/policies/. Feeds F7.
- **Reconcile before trading, and a missing report is not flat.** At start, local state is aligned with the venue's reports before any strategy runs; unresolved reports keep strategies from starting. Source: https://nautilustrader.io/docs/latest/concepts/execution/reconciliation/. Feeds F7, F9.
- **Connected is not ready.** A socket can stop delivering without closing, so a heartbeat timeout forces a reconnect, and "connected" means transport only. Source: the live page above. Feeds F13.

### MetaTrader 5 and cTrader Algo

- **Lifecycle with reasons.** An MT5 expert receives a reason code when it stops: removed, recompiled, symbol or period changed, inputs changed, account changed or reconnected, template applied, start failed, terminal closed. Source: https://www.mql5.com/en/docs/event_handlers/ondeinit. Feeds F11.
- **Declared rights, default none.** cTrader runs every cBot and indicator in a sandbox; each declares its access rights; a restricted action throws and stops the bot; full access prompts the user. Source: https://help.ctrader.com/ctrader-algo/guides/access-rights/. Feeds F14.
- **One API across desktop, command line and cloud,** with distinct events for a new bar and a closed bar. Sources: https://help.ctrader.com/ctrader-algo/references/General/Robot/ ; https://help.ctrader.com/ctrader-algo/documentation/cbots/cbot-bar-events/. Feeds F15, F5.

### freqtrade

- **A version on the strategy interface.** Each strategy states the interface version it was written for; old ones must be updated as newer versions require it. Source: https://www.freqtrade.io/en/stable/strategy-customization/. Feeds F1.
- **Look-ahead and warm-up checks are run, not read.** One command chains backtests and compares each signal's values on cut data against the full run; another compares indicator values computed with different startup lengths. The docs say a clean result does not prove there is no bias, so these are helpers, not proofs. Sources: https://www.freqtrade.io/en/stable/lookahead-analysis/ ; https://www.freqtrade.io/en/stable/recursive-analysis/. Feeds F5, F12.

### What their cores never get wrong (INFERRED from the above)

Money and order state (Shopify checkout, Nautilus execution), the loop order between decisions (LEAN), identity and versions of what extensions see (Shopify versions, Wix components), and the boundary between extension code and the core (WordPress, Shopify Functions, cTrader rights). Everything else is an extension with a default.

---

## 23. Foundation-properties checklist

Score each architecture version against these, item by item. Each line is the property, one plain sentence for him, where it comes from, and what exists in QMX today. A version that needs special code for a case these cover is weaker than one that does not.

1. **F1. One versioned contract per seam, with an overlap window.** Every connection says which version it speaks, and old versions keep working for a while after a new one ships. From Shopify versions, WordPress deprecation helpers, Wix major and minor, freqtrade's interface version. In QMX today, Library kinds and stores carry versions (PR 213), and API routes do not (CA-01).
2. **F2. Extension points with working defaults, never locks.** Every slot works out of the box, including an explicit "do nothing" default, and no default refuses him. From LEAN's null models and WordPress core hooks; ruling 137. In QMX today, templates with unmet needs install as drafts, and the node's values are blank (TN-10).
3. **F3. One way to add a thing.** A new venue, market class, block, reading, template or QMB variant is a declared record plus code behind a door that already exists, and the core's own code does not change. From Shopify definitions and app config, WordPress hooks, Wix extensions; QMX's one catalog. In QMX today, capabilities are catalog rows and mini apps are manifests, but the venue enum is closed (CA-04).
4. **F4. Owned names.** Each extension's data sits under its own name and cannot collide with the core's or another's. From Shopify's reserved app namespace and WordPress prefixes. In QMX today, Library kinds and mini-app ids have their own names.
5. **F5. Declared inputs, known times, deterministic runs.** Everything a unit reads is declared with the moment it became knowable, and the same input always gives the same output. From Shopify Functions, freqtrade's checks, cTrader's bar events; QML's footprint and `knowable_at`. In QMX today, QML refuses look-ahead through `knowable_at`, with the limit QML-01 shows.
6. **F6. Same code in research and live.** A unit, a reading and a fill rule run the same code in QMB, paper and live, and the core owns the named differences. From NautilusTrader and LEAN's engine loop. In QMX today, QMN's loop drives QMB's `run_slice`, but the MIS runs only on the node (MIS-04).
7. **F7. Unknown is a state.** An order whose outcome is unknown is never resent blind, and the node checks the broker before any unit trades after a start. From NautilusTrader's command outcomes and reconciliation. In QMX today, CT-19 has UNKNOWN and QMN has reconcile, never run against a broker.
8. **F8. At-least-once with an id.** Every event, fill and saved item has an id, receiving it twice changes nothing, and a reconcile job stands behind every feed. From Shopify webhooks. In QMX today, the cTrader deal id is the fill key, and webhook deliveries are deduplicated (HP TRG2a).
9. **F9. Fail closed for new risk, open for protection.** When something breaks, new entries stop while exits, stops and the kill switch keep working, and nothing on that path waits on the PC, the MIS, telemetry or an agent. From QMN's failure register (FR-17, FR-33); standing order 10. In QMX today, the node journals before it dispatches and keeps a stop at the broker on every order.
10. **F10. Records are immutable and versioned.** Nothing is edited in place, a correction is a successor linked to its parent, and live units pin what they use. From Wix components; the Hermes "never silently overwritten" rule; the Library's versions. In QMX today, Library items have versions and lineage, but dictionary entries and blocks do not (QML-11).
11. **F11. Lifecycle with reasons and saved state.** Start, stop, restart, redeploy and reconfigure are events with a reason, state survives them, and warm-up is computed, visible and trade-free. From MT5's stop reasons, cTrader's lifecycle, LEAN's warm-up, WordPress activation hooks. In QMX today, QML exports state and derives warm-up, and QMB does not use either (UT-10).
12. **F12. Every problem at once, no false positives, checked at the door.** A check returns all problems with where and how to fix, refuses only proven violations, and runs where the thing must pass, so no path skips it. From WordPress's call-site notices and freqtrade's honest "helpers, not proofs"; QMX's `workflows_validate` loop; his "no false positives". In QMX today, QML's Layer 1 and 2 checks exist, and no agent can reach them (AG-01).
13. **F13. Observable by default; health means progress.** Every effect leaves a record of who, what, which version, where and the clock state; failures are typed with what to do; health is the last decision and the last quote, not "process up"; off shows as off. From the QMN failure register, Shopify function run logs, NautilusTrader's "connected is not ready". In QMX today, QMN has health states and a heartbeat, and telemetry is off by default (DO-02).
14. **F14. Declared rights; limits report, never cap.** Code runs with the rights it declares, default none, and limits are the provider's or a logged health guard. From cTrader access rights and Shopify Functions limits; standing order 9. In QMX today, QMB runs code in a child-process sandbox, and mini apps have a breaker.
15. **F15. Standalone and local first.** A unit's trading path needs only what is on its own machine, and servers run the same thing as the PC. From Wix's hosted-or-self-managed contract and cTrader's one API across desktop and cloud; standing orders 8 and 10. In QMX today, the MIS and instrument records are not on the node yet (MIS-01, LD-07).
16. **F16. Only he promotes; one automatic stop.** Promotion and resuming after a risk stop are his acts, enforced by the core, and the only automatic move is a risk rule stopping a unit. From Wix's "new permissions need the user"; standing order 7. In QMX today, governed Library items land as drafts, and only he can resume QMN.
17. **F17. One time scale.** Every stamp is UTC plus the time it was received, sessions are rules in the market's own zone, and every machine reports how far its clock is off. From QMF's chrono types and QMN's clock bands; research 54 §4.2. In QMX today, this exists inside QMN only, and his PC has no clock check (CK-01).
18. **F18. One owner per stream, credential and position.** Each journal stream, feed connection, token refresh and open position has one owner holding a lease, and a second claimant is refused. From QMN's one refresher per credential; research 44 E01. In QMX today, QMN pins its machine, and the host is the one Library writer.
19. **F19. Typed market facts.** Every number says what it measures (price step, ATR multiple, percent, R, money), and every instrument has a versioned record per broker, so one unit means the same thing on every venue. From Shopify's typed definitions; research 32 and 43 F6. In QMX today, parameters carry a `unit_kind`, and no instrument record is stored (QML-06).
20. **F20. Explainable in a sentence.** Each property and each part can be told to him in one plain sentence; one that needs a page is a sign of a complex system. From standing order 6 and the WordPress warning about too many hooks. In QMX today, this checklist is the test.

