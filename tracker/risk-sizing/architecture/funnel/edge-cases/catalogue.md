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

1. **The catalogue holds 285 cases across 15 parts, plus 18 for the risk session.** About half are harvested from earlier work (marked with their file and section). The rest are new, from a trader's and an operator's view, from the edge-case lens run over the ledger and the grounding files, and from a pre-mortem and a red team (section 18).
2. **Most hard cases fall into a few families**: something is unknown (an order outcome, a stale reading, a data hole, a clock), something has two owners (two nodes, two journal writers, two grants, two registries), something changed under a running thing (a unit version, a block fix, a broker spec, a schema, a QMB variant), and something means different things on different venues (digits, contract size, volume, sessions, the trading day).
3. **Each family is handled by one property of the core, not by special code per case.** Twenty properties cover all 285 cases (the checklist at the end). The architecture that holds those twenty with the fewest parts wins.
4. **Five cases are the costliest if missed:** an orphan or doubled position after a crash or reconnect (TN-01, TN-02); two machines trading one unit or refreshing one cTrader grant (TN-04, TN-05); a unit that passes every check and still trades nonsense, because today's checks prove safety and not trading (UT-01); a number whose unit differs by broker or digits (QML-05, QML-06); and protection that depends on something that can be down (TN-03, TN-08, TN-09).
5. **Many cases are already handled in shipped code**, mostly inside the never-run node (UNKNOWN outcomes, reconcile, journal-before-dispatch, clock bands, one refresher per credential) and in QML (look-ahead refusal by `knowable_at`). The gaps are mostly at the seams between parts, not inside them.
6. **The white-label platforms agree on a short list**: versioned contracts with an overlap window, extension points with defaults, owned names, declared inputs with deterministic runs, at-least-once events with ids and a reconcile job, unknown outcomes kept as a state, and the same code in research and live. Section 22 has the sources.
7. **Two of his own rules decide many rows**: "only the node sends orders" (ruling 27) and "units stand alone" (standing order 10). Any design where protection, the kill switch or a unit's next decision waits on the PC, the MIS, the router, telemetry or an agent fails a whole family of cases.

---

## How to read this

**Columns in every part table.**
- **What happens**: the case, from a trader's or an operator's view.
- **Odds, harm**: how likely in daily use, and how bad. Odds: **H** expect it within a month, **M** a few times a year, **L** rare. Harm: **Money** can lose money or trade wrongly; **Silent** corrupts evidence or judging without anyone noticing; **Stop** blocks work and is visible; **Friction** wastes time or confuses. These scales are a lead's call (section 20).
- **Owner**: the part that must handle it.
- **Today**: what exists on `origin/engine/base` `c93407ca` that handles it, with the path. "none" means nothing found.
- **Property**: the foundation property (F1 to F20, last section) that handles it without special code.
- **Proof**: the check that would show it is handled.
- **Source**: where the case came from (codes below).

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

**"The 192 things a site must handle".** The memory names this list as his phrase for the 22 Oct resilience pass. No file holds a numbered list of 192. The resilience cases it stands for are in M10b and in the hardening packets of HP; I harvested them from there (CHECKED by `grep -rn "192"` over `tracker/qma-v2/`, no hit).

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
| QML-07 | A dictionary entry is used in a role it was not meant for: the entries carry 154 free-text role strings, CT-34 accepts four | H, Stop | QML | parser reads all 239 with zero refusals; roles not normalised (G1 §2.2) | F3, F12 | The checker refuses an unknown role and names the nearest known one | G1 §2.2 |
| QML-08 | A unit cites an entry with no code behind it (ATR, MACD, Bollinger, VWAP are named, six indicators run), so nothing runs, or the agent hand-rolls it in Python with a bug | H, Silent | QML | six TA-Lib wrappers (`qmf-indicators/wrappers.py:146-193`, G1 §2.3) | F12, F3 | Each entry's status (has spec, has code, has golden test, used by a unit) is computed by script, never stored; the checker refuses a cite with no code and points at the block template | G1 §2.3, R44-A26 |
| QML-09 | One word means different things across classes: volume is a tick count on cTrader and exchange volume on CME; "session", "the open", "gap", "funding" and "swap" differ | H, Silent | QML | none; research 45 §4 lists twelve such words (G1 §2.5) | F19, F5 | Each block declares the data level it needs; placing a real-volume block on a tick-count feed is refused unless the block is declared a proxy | G1 §2.5 |
| QML-10 | An entry written "crypto spot only" is used on perps or futures | M, Silent | QML | several entries say so (G1 §2.5) | F19 | Transfer notes become data the checker reads | G1 §2.5 |
| QML-11 | A dictionary entry's meaning is edited while units cite it, so those units now mean something else | M, Silent | QML | none | F10, F1 | Units pin the entry version; an edit makes a successor and lists the units that cite the old one | New |
| QML-12 | A shared block gets a bug fix, and every unit using it changes behaviour, live ones included | M, Money | QML | none | F10, F16 | A block fix mints new versions of the units that use it and queues their re-test; live units keep the pinned version until he promotes | R44-E11 |
| QML-13 | A learned block (a model) is retrained: is that calibration or a new version? And the scan denies file reads, so weights cannot load | M, Silent | QML | file I/O denied (`qml/src/qml/conformance/scan.py:39-56`, G1 §1.6); no host injects weights | F10, F5 | A block declared "learned" with bounds retrains as calibration; weights arrive through a declared read surface with a fingerprint | R44-E11, G1 §1.6 |
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
| UT-03 | The checker changes and a unit that passed yesterday fails today, or the reverse | M, Stop | Unit | none | F1, F13 | Each verdict records the checker version; an upgrade re-checks and labels old verdicts; a live unit never flips silently | New |
| UT-04 | A unit's version changes while a trade is open, and the new logic's exits do not match the old entry | H, Money | Unit, Node | CT-29 attributes the whole trade to the opening bot (`packages/qmf-risk/src/qmf/risk/exit_record.py:1-14`, G1 §7) | F10, F11, F18 | A position belongs to the version that opened it; that version keeps managing its exits until flat, unless he hands it over | Brief |
| UT-05 | A self-tuned number swings back and forth on too few trades | H, Money | Unit | numbers carry bounds and step (G1 §1.3); no motion rule; live seats run defaults only (`declaration/bot.py:618-628`, G1 §1.4) | F5, F10 | Every movable number declares its motion: inputs, minimum sample, step limit, cool-down, bounds from QMB; each move is a journal row | Brief, R43 F3 |
| UT-06 | Self-tuning drifts toward more risk over months | M, Money | Unit | none | F16 | Tuning never leaves the tested range; the risk-side rule goes to the risk session (RS-02) | T1-682 |
| UT-07 | A placeholder sizer or exit reaches a live account without anyone replacing it | M, Money | Unit, Node | none; placeholders are ruled (U-04) | F13, F16 | Placeholders are labelled data; promotion shows the label; every trade carries it in the journal | New |
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
| UT-20 | A plain-Python unit (always allowed, CC-08) wants to trade, and the node's seats accept only QML-conformant bots | M, Stop | Unit, Node | "plain Python cannot bypass" a seat (`qmn/src/qmn/seats/admission.py`, G3 §1.1) | F3, F2 | The runtime contract is small enough for plain Python to meet: the callback shape, declared inputs, declared state | New |
| UT-21 | A unit is saved without the source it came from (a video, a chat, an article) | M, Silent | Unit, Library | Library lineage edges and the `source` kind (G1 §8.2) | F10 | A unit cannot be saved without a source link, even "hand-made" | U-15 |

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
| QB-13 | Two QMB variants (he wants new versions and variants, T3:1383) give different numbers for the same unit and data | M, Silent | QMB, Mini apps | none | F1, F13, F10 | Every result records which QMB variant and version made it; the judge compares like with like | New |
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
| MIS-04 | The same reading computed in QMB, the MIS and a unit gives three values | H, Silent | MIS, QMB | QMB imports nothing from QMN (G1 §6.1) | F6 | A golden replay: one recorded day through all three, compared per reading id and version | R44-V04 |
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
| JR-02 | The journal cannot be written before an order goes out (disk full, write error) | M, Money | Journal, Node | journal-before-dispatch: the effect does not dispatch, entries block, exits and protection still go (`qmn/src/qmn/journal_dispatch.py:1-12`; FR-33) | F9 | A test fills the journal disk and shows entries blocked and a stop still amended | FR-33 |
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
| WF-09 | A QMX update ships a newer template and overwrites the one he edited | M, Friction | Workflows | templates are Library items (G2 §4) | F10 | An update makes a new version beside his | New |
| WF-10 | A webhook trigger has no sender signature check | L, Silent | Workflows, Contracts | `HO/host.py:1370-1393`; backlog row (G2 §6) | F14 | Deliveries are signed and deduplicated by id | G2 §6, HP TRG2a |
| WF-11 | An analyst workflow marks its own forecasts | H, Silent | Workflows | none | F12 | Calls are written with a date and scored later by a script against the market | R29 §4 |
| WF-12 | The shared judge step is edited, and every past verdict changes meaning | M, Silent | Workflows, QMB | none | F10, F1 | Verdicts record the judge version | New |
| WF-13 | A run's home machine dies mid-run | M, Stop | Workflows | another machine adopts a run whose home died, refused while the home's heartbeat is fresh (HP ADOPT) | F7, F18 | A run is adopted once; the old home never resumes it | HP ADOPT |
| WF-14 | The PC was off for two days and missed scheduled runs | H, Friction | Workflows | catch-up after downtime (HP BUG1) | F11 | Missed runs either catch up once or are marked skipped, by a setting per trigger | HP BUG1 |

---

## 9. Mini apps holding units

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| MA-01 | A unit lives in a mini app, and the app's breaker stops it after 3 errors: a process stop, not a risk stop | M, Money | Mini apps | `max_errors` default 3, `heartbeat_timeout` 10 s (`APPS/manifest.py:104-110`, here) | F16, F9 | Only the node sends orders; a mini app holding a unit is research only, and its breaker stops research, never protection | G2 trap 8, G4b Q5 |
| MA-02 | The machine an app lives on dies; a move is a snapshot plus a lease handover, with no remote restore | M, Stop | Mini apps | `APPS/supervisor.py:527-533`, `:1064` (G2 §5.1) | F18, F10 | The app's state of record lives in the Library, so a new home can start from it | G2 §5.1 |
| MA-03 | A newcomer installs an example app that imports deleted code and crashes | H, Friction | Mini apps | two of four examples import the deleted runtime (G4b §1.7) | F13 | Examples are built and tested in CI | G4b §1.7 |
| MA-04 | An app's `provides` contract changes shape and its consumers break | M, Stop | Mini apps, Contracts | `provides` and `feeds` as JSON Schemas (`APPS/manifest.py:148-167`) | F1 | Contract versions with an overlap window | New |
| MA-05 | The trading node as a mini app is a `money` app, which needs his signature to start; does every restart need it? | M, Stop | Mini apps, Node | `APPS/supervisor.py:542-547` (G2 §5.1) | F16, F11 | His signature binds a version, not a restart | New |
| MA-06 | `app_op {app: qmb}` fails because no app named `qmb` runs | H, Stop | Mini apps, QMB | `ENG/nodes/app_op.py:1-25` (G4b Q4) | F3 | QMB answers through the `app_op` route whether it runs as a host door or as a mini app | G4b Q4 |
| MA-07 | Several QMB variants are installed; which one does `backtest_run` call? | M, Silent | Mini apps, QMB | none | F2, F13 | A default named in settings; every result records which variant ran | New |
| MA-08 | A long backtest in an app needs more memory than he set | L, Stop | Mini apps | memory unlimited unless he sets a number (G4b Q5) | F14 | A limit hit is logged with the number that was set | G4b §3 row 8 |
| MA-09 | A mini app reads another app's output while that app is offline | M, Stop | Mini apps | reading an app's latest output is a Library read that works offline (HP APP2b) | F8, F15 | Outputs are Library artifacts with `stale_after` | HP APP2b |

---

## 10. Contracts and APIs

| ID | What happens | Odds, harm | Owner | Today | Property | Proof | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CA-01 | Routes carry no version and the API title is fixed at 0.1.0, so a UI or outside agent built today breaks silently on a change | H, Stop | Contracts | `CTL/server.py:415` (G2 §6) | F1 | A version on every seam, an overlap window, a deprecation notice that names the replacement | G2 §6 |
| CA-02 | The `unit` kind has an empty schema, so anything lands as a unit | H, Silent | Contracts, Library | `LIB/kinds/unit.schema.json:7-10` (G2 §3) | F12 | A real schema with every problem returned | G2 §3 |
| CA-03 | "The bot may not size" is in four layers; a half-done change leaves one layer sizing or refusing | H, Money | Contracts | `qml/src/qml/protocol/intents.py:1-7`, `qmf-risk/door.py:7-10`, QMB admission context, `qmn/src/qmn/seats/dispatch.py` (G1 §0 item 4) | F1 | All four layers move in one wave; a test sends a sized intent end to end | G1 §0 item 4 |
| CA-04 | Adding a venue means editing a closed enum in the node's law | H, Stop | Contracts, Venues | `VenueClientKind` is `ctrader`, `replay`, `conformance` (`qmn/src/qmn/venue/port.py:40-45`, here) | F3 | A new venue is a capability declaration plus an adapter behind the port | G3 §5 |
| CA-05 | Errors come in different shapes: tools give code, message and next step; the Library gives the first problem only | M, Friction | Contracts | `HAR/tools.py:188-213`; `LIB/kinds/__init__.py:46-55` (here) | F12 | One error shape with every problem | New |
| CA-06 | The PC and the node run different contract versions after an update on one side | H, Stop | Contracts, Node | none | F1, F15 | Both sides state their contract version on connect; the node keeps trading what it has and refuses new deploys until they match | New |
| CA-07 | The risk socket is built now and the risk session's design does not fit it | M, Stop | Contracts | none; the socket is a designed placeholder (C-06) | F2, F1 | The placeholder implements the same typed contract the risk session will fill | C-06 |
| CA-08 | A unit's logic fingerprint does not match its stored source | M, Stop | Contracts, QML | Layer 2 refuses source that differs from the manifest (`conformance/layer2.py:292-302`, G1 §1.5) | F10 | Source and fingerprint travel together | G1 §1.5 |
| CA-09 | The same capability exists through two doors with different rules | M, Silent | Contracts | one catalog row per capability, every door derived from it (`CTL/catalog.py:1-10`, G2 §1.2) | F3 | New unit doors are catalog rows only | G2 §1.2 |
| CA-10 | An outside agent's observer token outlives its purpose | L, Friction | Contracts | tokens last 30 days (`CTL/service.py:89`, G2 §6) | F14 | Expiry shown; renewals are his | G2 §6 |
| CA-11 | A browser client cannot resume a stream, because EventSource cannot set the auth header | L, Friction | Contracts | fetch stream with an Authorization header (G2 §6) | F8 | Resume by `Last-Event-ID` | G2 §6 |

<!-- E1-CONTINUE -->
