# 43: Convergence of the unit-system planning run

Written 2026-10-30 by the convergence agent (planning run, after the seven expansion rounds). This file narrows the field into what the architecture step needs. It is **not** the architecture: there is no spine, no decision id and no code layout here. Risk and sizing maths, exits, the book and correlation control belong to the separate risk-and-sizing session; this file only says what the unit system leaves for it.

## How this was made

- **Method.** `bmad-brainstorming` convergence (`references/converge.md`) in "ideate for me" stance: affinity clustering across every field first (Appendix A), then MoSCoW for the build scope (Appendix B). Then `bmad-forge-idea` in attack mode on ten top recommendations, two voices each, one BMad persona and one generated outsider (Appendix C, summarised per area). Principles applied, each read this session: attack-the-premise, subtract-before-you-add, model-the-domain, foundational-thinking.
- **Deviations, forced by the brief (write exactly one file).** No memlog was written for the convergence or the forge sessions, and the forge's `forge-report.html` was not rendered. Both skills allow running in conversation when state cannot persist; the forge record lives in Appendix C instead.
- **Read in full this session.** `STATE.md`, `STANDING-ORDERS.md`, `RISK-SIZING-PACK.md` §1 and §4, `wayfinder/MAP.md`, `wayfinder/RESEARCH-QUEUE.md`, every open grilling and prototype ticket, the five expansion fields (`playing-field.md`, `qml-field.md`, `mis-field.md`, `live-field.md`, `workflows-field.md`), `funnel4-qml/cis/seams-options.md`, `research/42`.
- **Read in part (sections named in the text).** research 18 §2-§9; 35 §0, §4, §6, §7; 20 §1-§5; 21 §2; 41 §0, §2; 17 §1.8, §5.4; 19 closing list; 36 §0; 39 §4-§5; funnel4 CIS problem-solving §3-§5; funnel3 CIS problem-solving knots (b) and (c), §4.3; the ruling 135 text (`tracker/qma-v2/research/methodology/26-operator-rulings-and-alignment.md:244-257`). **Not read:** research 34, 36, 39, 40 and 17 beyond those sections, the CIS design-thinking, glossary and question files, and the transcripts beyond his last four turns of 30 Oct and the quotes grepped below. The fields that summarised them script-checked their quotes; this file leans on those checks where it cites a field.
- **Quotes.** His words are quoted only after a `grep -n` this session on the transcript. Line numbers here are `grep -n` lines (`T1` = `operator/transcript-2026-10-20-to-28.md`, `T2` = `operator/transcript-2026-10-29-to-30.md`). The fields' `T2` numbers run one to nine lines lower in places (their own note, `workflows-field.md` §8).
- **Labels.** CHECKED = read at the cited path or line this session, or CHECKED by the cited research file ("CHECKED in r42" means research 42 checked it). INFERRED = reasoning. **Every recommendation in this file is the lead's judgement and is INFERRED**; the facts it rests on carry their own labels.
- **Provisional marks.** Codex research 22 to 33, 37 and 38 has not run. A recommendation that leans on one is marked "provisional until research N", with what would change it.

---

## 1. Read me first

1. The ideas phase is finished: seven rounds produced well over a thousand ideas and questions, and this file narrows them to what the architecture step needs.
2. A unit stays what you ruled: one complete trading algorithm with its own entry, exits, risk and sizing, its own needs and its own journal.
3. Six building blocks carry everything else: each trade saved with the market's state and its result in risk units, each market reading saved with the moment it was made, the unit written down as data, simple journals, a count of every test tried, and one record of each market's facts at each broker.
4. A unit is written as a short document that names its parts and fills each part from a shared library of tested blocks, and plain Python stays allowed.
5. The same logic on another market or timeframe stays the same unit, with that market's own settings once its record earns them; it becomes a new unit only when its rules change.
6. The market intelligence service becomes a telescope: it reads every market with the same code the units use, saves what it saw, and proposes where a unit's conditions hold, but no unit needs it to trade.
7. The backtester is reshaped, not rebuilt: it gets a runner that really trades a unit, no lookback limit, and results in risk units with the market state on every trade.
8. Your PC runs the whole trading stack first, on practice accounts and on live prices; whether the real-money key may also live on your PC is your call.
9. For workflows, I recommend building the shared parts every recipe uses (the judge, the test counter, the chain from stage to stage) and writing the rest as ready drafts that say what they wait for.
10. Ten decisions are yours (section 6); everything technical is settled here with a reason, some of it provisional until the Codex research lands, and nothing is folded into the architecture until you say so.

---

## 2. The foundations

Per **foundational-thinking**, the data shapes come before any logic: if these six are right, most of the 339 mapped questions become lookups or numbers (`wayfinder/MAP.md` "the one most others wait on", CHECKED). They are listed in build order. Each says why, what it reuses from shipped code (research 42), and what it would break.

### F1. The stamped trade

**What.** Every trade in every world (backtest, stress, paper, demo, live) carries its result in money and in R, its worst and best excursion in R, and a **context receipt**: the ids, versions and ages of the readings the unit saw at entry and at exit, the market-journal minute it traded in, the market settings it used, and every tuned value in force. The receipt holds references and a few compact values, never copies of the reading history.

**Why.** The playing field's cross-map shows six question families that cannot be measured without it (`playing-field.md` §4 row 1, CHECKED). Research 05 named "QMB results aren't in R, and backtest trades carry no market state" as the gap (STATE research table, CHECKED); research 16 called it the biggest missing piece.

**Reuses.** The `trade` kind already has `world` and `initial_risk` (CHECKED in r42 §6.1, `LIB/kinds/trade.schema.json:94`). QMB already returns a typed refusal for an undefined measure and lands one `backtest-result` with `consumed`, `uses` and `tests` edges (CHECKED in r18 §2).

**Breaks.** QMB's CT-32 and CT-29 results are money only, so R joins them as a measure (CHECKED in r18 §2). Imported broker fills carry no initial risk (CHECKED in r18 §6), so an imported trade shows R as "undefined" until its stop is known. DEC-0162 (no stored composite score) is untouched: R is a measure, not a score.

### F2. Readings stored with the moment they were made

**What.** A reading (spread ratio, tick-rate ratio, trend state, regime label, funding state) is **library code that runs the same in QMB and live**. Every published value is stamped with reading id, version, compute time, input times and a health word (fresh, stale, degraded, shadow, retired). History is append-only: a retrain or a new version writes a new column and never rewrites old values. Backtests, studies and agents ask "what did it say at 08:01 on 3 March" and get the stamped value. Values computed later for old dates carry a backfill flag.

**Why.** A label is only honest if it has a version and a time (research 16 via STATE, CHECKED); lift studies, agent scoring and "where does this unit win" all need what was known then, not what is known now (`mis-field.md` §5 row 1, CHECKED). One code in two callers is also what lets a unit stand alone: when the MIS is down, the unit computes the reading itself (`qml-field.md` B124, P-I3, CHECKED).

**Reuses.** QMN's six rule labelers, the fitted liquidity-stress model and the shadow lane are the first readings (CHECKED in r18 §4). Library append-only refs, store versions (PR 213) and the typed monthly price partitions (CHECKED in r42 §0, §2.1).

**Breaks.** The docs say the MIS reaches only the Book door and the KSA (`docs/glossary.md:556-558`, CHECKED in r18 §9 row 5), so a doc pass follows. The labelers live inside QMN today; they move to a package both QMB and the trading runtime import (INFERRED).

### F3. The unit written down as data

**What.** A unit is one JSON document (the unit spec). It holds: identity and lineage; the logic as named slots filled by blocks (section 3.1); coordinates (the markets list, bar construction, sessions in broker time); data needs (the minimum data level each block needs); **every number with its kind, range, motion, authority and origin**; context needs written in dictionary words; home markets; the risk socket's slots; and a pointer to its frozen exam baseline.

**Why.** Identity, tries, placement, UI-editable numbers and agents that read a unit without running it all need the unit's parts visible as data. The QML CIS run found the root cause of the if-else question: "a rule's 'if' is not data", so nothing records what kind of part it is, how it may move or who may move it (STATE funnel4 CIS row, CHECKED). His seed points the same way: "For me, I'm imagining this like JSON. Most of it is JSON." (`T2:788`, CHECKED).

**Reuses.** The Library's `unit` kind is governed, has manifest identity and a page with Logic, Results, Family tree, Markets and Versions tabs, and no fields yet (CHECKED in r42 §6.1). QML's parameter space already carries type, bounds, step, default and a UI flag, and QMB's optimiser reads it (CHECKED in seams §0). The Alternative Trading Composition (ATC/PolicyPair) is a non-Book money seam already in code (`qml/src/qml/declaration/alternative.py:36-41`, CHECKED in seams §0). Governed kinds land only as drafts that wait for his yes (`LIB/landing.py:8-11`, CHECKED in r42 §1.5).

**Breaks.** Eleven QML laws built on "the Book owns money, exits and thresholds" (the census in `funnel4-qml/cis/problem-solving.md` §3.7, CHECKED), among them `intents.py:1-7` ("the bot may not size"), `STAGE0_NEVER_SIZES` and `glossary.md:150` (a tuned assignment is a new version). DEC-0175 (conditions forbidden in declarations) is amended for composition only; leaf conditions stay code.

### F4. Journals: one row shape, one writer per stream, links instead of copies

**What.** Five streams, each with exactly one writer:

| Stream | Writer | Holds |
| --- | --- | --- |
| Unit journal | QMB for backtest and stress; the trading runtime for paper, demo and live | trades (F1), signals seen but not taken with one reason, calibration rows (what moved, from what, to what, driven by which rows), risk events from the socket, state changes |
| Market journal | the feed keeper | per broker, account type, instrument and minute: spread, fees, slippage, quote health, session flags |
| Reading history | the MIS | the stamped values of F2 |
| Node journal | the trading runtime | start, stop, update, self-test, account-level guard events, reconcile results |
| Notes | agents | analysis and proposals, each linked to the rows it annotates |

Every row has the same shape: id, venue time and receive time, stream, subject, kind, world, links, body, schema version. Old rows never migrate. Rows live in monthly Parquet partitions with one Library card per partition; agents read through a journal door, never by opening files.

**Why.** His journal is "literally the DevOps layer for that unit" (2026-10-27 dictation, CHECKED in `live-field.md` S14); he wants "most simple data schemas" (`T2:1148`, CHECKED). One writer per stream follows **separate-before-serializing**: no two actors write one file.

**Reuses.** The `trade` kind with `world`; the Library outbox for saves made while the PC is away (`LIB/outbox.py:1-18`, CHECKED in r18 §6); Library event triggers on landings (CHECKED in r42 §1.2); OpenObserve for operational logs, not as the store of record; copies by class (PR 231).

**Breaks.** Nothing shipped. It adds a `journal` kind (none exists, CHECKED in r18 §6) and a catalog row that reads journals (none exists, CHECKED in r42 §1.7).

### F5. The try ledger

**What.** Every test of any variant, settings profile, market, timeframe or window in a family is counted **at the QMB door**, not by the agent that asked for it, and that includes runs he or the copilot start by hand. The judge corrects the best result of a family by its count.

**Why.** "When strategies are nearly free to make, judging them is the product" (STATE correction 10, CHECKED). Without a door-side count, luck moves from backtests to journals to agent shortlists (`playing-field.md` §4 row 6, CHECKED). Research 11: every screen and refinement counts as a try (STATE, CHECKED).

**Reuses.** QMB ledgers every trial already (CHECKED in r18 §2); the deflated Sharpe in `TPL/_shared/overfit-gates`; `d4`'s variant label table (`variant_of` for instrument and timeframe, `derived_from` for structure, CHECKED in `workflows-field.md` Q32); PBO and CSCV are designed in `qmb/robustness/` (CHECKED in r18 §2).

**Breaks.** QMB applies no correction today, and two templates carry their own copy of the gate scripts (CHECKED in `workflows-field.md` §0 item 2).

### F6. The instrument record

**What.** One record per instrument per venue: identity, contract facts (tick value, lot step, minimum lot, margin), measured costs (filled from the market journal), a trading calendar in venue time and broker server time with daylight saving, the carry schedule (swap time, funding interval, roll and expiry), the data levels the venue offers (0 calendar, 1 bars, 2 quote ticks, 3 depth, 4 trade tape, 5 derivatives fields, 6 outside data), and the data licence terms.

**Why.** The risk socket needs contract facts; QMB needs costs; placement needs "which of my readings exist on this instrument's data?" (`qml-field.md` B128, CHECKED); IC CFD futures expire early and are never rolled, and Hyperliquid funds hourly (STATE research 02 row, CHECKED).

**Reuses.** CT-03 instrument identity; the broker `symbol_info` read, stamped demo or live (PR 215, CHECKED in r42 §4); the connections registry (DR round).

**Breaks.** DEC-0015 "no futures and no options ever" (`docs/contracts/ct-03-instrument-identity.yaml:46`, CHECKED in r18 §9 row 1) goes in the doc pass. GAP-0048 (no cost calibration) stays open until the market journal has data.

### Subtract first

Per **subtract-before-you-add**, these go before the foundations are built on:

1. **QMB's replay copies all history at every step**, at four places (`replay.py:569`, `replay.py:60`, QML `evidence.py:883`, frames compared whole at `replay_execution.py:824`; CHECKED in research 14 via STATE). Windowing it removes the only lookback limit in the system (research 12 via STATE, CHECKED).
2. **QML's Book premise for units.** All eleven actors that hold it are code or docs; none is in his words (census CHECKED in funnel4 CIS §3.7). Invert it for units. Reject the dual-path flag (option P-4 there): no real bot uses the old path (CHECKED in r18 §3, "no real bot anywhere"), so per **migrate-callers-then-delete** a flag would only create two kinds of unit agents must tell apart.
3. **Copied scripts.** The gate scripts copied into `b` and `d3`, and seven copies of `lineage.py`, become one judge block and one lineage writer (CHECKED in `workflows-field.md` §1).
4. **The `library` node kind** is declared runnable with no executor and no template uses it (CHECKED in r42 §1.1). Delete the declaration.
5. **The router machinery of rounds 13 and 14** (offers that expire, signed plans, load-balancer mappings) is not built. He found it over-built (STATE 28 Oct, CHECKED); the finder's list replaces it (section 3.3).
6. **The "5 trading days" plan cadence** gives way to one clock per reading tier.
7. **Loop counts in shipped templates** (`d3` 3 generations, `l4` 200 trials, `d4` 12 variants) become editable numbers on the template card, so no default acts as a cap (standing order 9).
8. **Contradicting docs** (r18 §9 rows 1 to 10, CHECKED) are rewritten in a doc pass after the fold, not before.

---

## 3. Per area

Each area gives two or three options judged on standing order 6 (hard cases, maintenance and debugging, explaining it in a few sentences), the recommendation, what the forge attack changed (full record in Appendix C), and what research 22 to 38 could still change.

### 3.1 The unit and its identity

**Where a rule's structure lives** (the three options that compete for one seam, `seams-options.md` §7, CHECKED):

| Option | Hard cases | Maintain and debug | Explain to him |
| --- | --- | --- | --- |
| Code first: the unit is Python behind today's callback; only declared numbers are visible | Handles anything | The "if" stays hidden; analysts read code, not structure; tries per part can't be counted | "A program with a few dials" |
| Data first: the whole rule graph is JSON that a QML interpreter runs per quote | Weak: per-quote speed and an expressiveness ceiling | A second language and a new runtime; reverses DEC-0175 fully | "A flowchart, like a workflow" |
| **Declared skeleton, coded blocks (recommended)** | Strong: lifecycle states, model blocks and whole-Python units all fit | One compiler, blocks tested once, the same host seam QMB and the node already use | "A unit is a trading plan with named parts; each part is a tested block from the library" |

**Recommendation.** The unit spec names the anatomy any trader knows (research 35 §6 item 1, CHECKED): context needs, level or setup, trigger, confirmations joined by a combiner, entry order, exit set, sizer, halts, plus an open list of further roles (veto, target, invalidation, regime detector, sizing modifier, arming, timeout; `qml-field.md` B022, CHECKED). Each slot binds a catalogue block by id with its numbers. The combiner vocabulary is small and declared: all, any, k-of-n, weighted vote with open and close thresholds (the MT5 Wizard's form, research 36 §0 item 6, CHECKED), sequence, within, and the lifecycle operators arming, cooldown, reset and re-entry. Leaf conditions stay code inside blocks. QML compiles the document once into today's `factory(spec, assignment, read_surfaces) -> callback(instant) -> intents` seam, with intents widened to carry size and exits. A Python block, or a whole-Python unit with a manifest that declares the same slots it fills, keeps every right a QML unit has: journal, lineage, tries, promotion (STATE "Plain Python is always possible", CHECKED). Combining units happens at build time only and compiles into one unit, so no live unit depends on another (`qml-field.md` P-I8, CHECKED).

**Identity, by the type of edit** (a lookup table, per **model-the-domain**, instead of a judgement per case):

| Edit | Result | Counted try | Needs his click before live |
| --- | --- | --- | --- |
| A number moves inside its declared range by its declared motion | Calibration row in the unit journal | No (the motion rule was tested once) | No |
| A range, a settings profile, a bar construction, a session window, or the markets list changes; a market adopts its own settings | New version of the same unit | Yes | Yes |
| A block is swapped, a role or branch is added or removed, the combiner changes, the exit family or the sizer adapter changes, a part is transplanted from another family | New unit in the same family, linked to its parent | Yes (both families for a transplant) | Yes |
| The logic is rewritten by a model or by hand with different behaviour | New unit marked "rewritten from" | Yes | Yes |
| An ambiguity in the source is resolved | Corrected successor; the old version stays | Yes | Yes |

**Timeframe and market are coordinates.** The same logic on 1m and 5m is one correlated idea (his ruling, STATE 30 Oct, CHECKED; `T2:1000` "that's just correlation", CHECKED), so it is one unit with two coordinates in one same-idea group. The same logic on gold and on EURUSD is one unit. **What he called System 2 becomes "a market's own settings":** by default a unit uses settings pooled across its markets; a market earns its own settings only from the unit's record on that market (his Path A, STATE 29/30 Oct, CHECKED), shrunk toward the pooled values, and going live with them is his click. If gold needs different rules (a fix-time gate, a different exit), that is a new unit in the family whose markets list is gold. This revises his 27 Oct "yes" to sibling units, so it is decision 4.

**Lifecycle, as one state machine per unit and one per market inside it.** States: draft, tested, paper, live, stopped, parked, retired. Only he moves a unit or a market toward live. The only automatic transition is the unit's own risk rule moving it to stopped, logged (standing order 7). A stopped unit keeps writing would-have-done rows, which is recording, not trading. The old breaker's automatic LIVE to PAPER to RECOVERY transitions (research 19 via STATE, CHECKED) are not brought back.

**Forge changed.** Lifecycle operators joined the combiner after a scalper's state machine cracked the slot list. The receipt is stamped at entry and at exit, not only entry. Shrinkage toward pooled values became the default form for a market's own settings. No build is blocked for using a not-yet-implemented dictionary entry; the part is tagged instead.

**Research could change.** Research 24 (earning a specialist without luck) sets how much record a market needs and the shrinkage form; research 25 (drift) sets when a market's own settings expire; research 26 sets how structure changes are counted as tries. None changes the slot shape.

### 3.2 QML and the dictionary

**QML itself:**

| Option | Hard cases | Maintain | Explain |
| --- | --- | --- | --- |
| **Upgrade in place, add a block catalogue and the unit spec compiler (recommended)** | Keeps QMB's and the node's real seam; adds what is missing | Protocol and parameter space reused; one premise inverted | "QML gets the parts library agents build units from" |
| Rebuild QML from scratch | Same end state | Throws away a protocol that already matches the industry (research 04 via STATE, CHECKED) | "Start again" |
| Units outside QML, Python only | Handles anything | Loses visible structure, tries per part, cheap-agent safety | "Agents write programs" |

His words settle the direction: "I think QML deserves an upgrade." (`T1:1211`, CHECKED). The catalogue is the deep module: a small door (`resolve(entry id, profile) -> block`) over implementations, golden values, per-class profiles and aliases (seams S4, CHECKED). A dictionary entry that runs **is** a catalogue block (funnel4 CIS §4.3 insight 3, CHECKED).

**The dictionary and its 239 entries:**

| Option | Hard cases | Maintain | Explain |
| --- | --- | --- | --- |
| **Review the ideas, rebuild the form (recommended)** | Keeps every concept; adds code, machine specs and the 140 missing concepts | One home, one format, a status per entry | "Every word stays; each one gets working code and a test" |
| Keep the prose, add code beside it | Two artefacts drift apart | Two sources of truth | "The old notes plus new code" |
| Rebuild from the MQL5 census and sources, with the 239 as one input | Widest coverage | Risks losing August intent | "Start the dictionary over" |

Each entry gets three faces: trader words, a machine spec (inputs, output type, parameter kinds and ranges), and an implementation (`qml-field.md` B031, CHECKED). Each carries a status: named, specified, implemented, tested on data, used in a unit (B038). Every parameter carries a starting profile with its origin label (RSI 14, 70/30 "published convention"). Folders stay by family, never by job; roles live on the binding (research 34 via `qml-field.md`, CHECKED). This keeps his August ruling that the entries are permanent library content (research 41 §2.1, CHECKED) and his October "the dictionary needs a rebuild, an entire thing" (`T2:219`, CHECKED). It is still decision 2, because whose August design survives is his to judge.

**How it expands per asset class and data class.**
- **Three homes per class** (`qml-field.md` P-I4, CHECKED): terrain on the instrument record (F6); class-only readings in the catalogue (funding, open interest, liquidations, basis for perps; roll, settlement, overnight range for futures; cash open, opening drive, breadth for indices; fix windows and real yields for gold; corporate actions for stocks); and a transfer status on each entry per class (native, direct, adapted, conceptual only, not transferable, not assessed).
- **Data levels.** Each block declares the minimum data level it needs (0 to 6 as in F6) and, where one exists, a fallback at a lower level with its expected loss (order-flow imbalance from depth, falling back to tick-rule imbalance, then range pressure; `mis-field.md` B005, CHECKED). QMB refuses a test on weaker data with a typed refusal. Proxy entries (tick volume for volume, a futures tape for a CFD) are always flagged.
- **New families.** A statistics and models family (Hurst, variance ratio, ADF, efficiency ratio, half-life, HMM, GARCH, change point), absent today (research 36 §0: 0 of 40 concepts, CHECKED), enters as readings on session and day clocks. Evaluation words (Sharpe, PBO, walk-forward) go to a separate judging glossary, not the dictionary (six of research 36's top ten missing concepts are evaluation words, per the research 36 row in `STATE.md`, CHECKED; `qml-field.md` B058).
- **Order of packs** follows the doors (decision 5): FX, gold and index CFDs on cTrader first; perps second; futures and stocks later.
- **Where it lives.** Library objects are the one source of truth; a snapshot ships as QML package data so the trading machine never needs the Library up (standing order 10). A one-line index serves cheap agents; full entries are fetched on demand (B079).
- **Appends.** A match script maps each source sentence to an entry id or "unmatched"; unmatched words become append requests that need a family, a data class, and an implementation or a stated gap (B037, B062, B126). His job for it, in his words: "so that if someone from a source mentions anything, we already know what it is, okay? Or if it's new, we can append it." (`T2:788`, CHECKED).

**Every number** carries its kind (distance, count, clock, ratio, probability), its range, its motion (fixed; scaled by a live statistic; refit on a window; chosen by state; learned), its authority (inside the range nobody; a new range his click) and its origin. The agent default form is instrument-relative (ATR multiple, percentile of own history, z-score); raw pips only when a source states them (`qml-field.md` B004, Q04; research 35 §6 item 15, CHECKED). His answer to "what tunes" is the frame: "It's numbers." (`T2:788`, CHECKED).

**Forge changed.** "Builds blocked below implemented" was dropped after the census showed 85% of strategy articles use a missing concept (research 36 §0, CHECKED); a part with no implemented entry is tagged "outside QML" and shown on the unit card, no block. Appends need a family plus a data class plus code or a stated gap.

**Research could change.** Research 23 and 37 can change which readings live per class and whether one shared word set holds across classes; research 32 fixes the instrument-record fields; research 33 decides which data levels are keepable.

### 3.3 The MIS

| Option | Hard cases | Maintain | Explain |
| --- | --- | --- | --- |
| A central service units read live (the 13 and 14 router shape) | Fails standing alone; a slow or wrong MIS harms every unit | A hot-path dependency to keep alive | "Units ask it before trading" |
| **A telescope (recommended)**: readings are library code; the MIS runs them across many markets on per-tier clocks, stores stamped history, publishes a board and match lists | Strong: units compute their own needed readings; the MIS only widens what they can see | One code in three callers (unit, MIS, QMB) | "It looks at every market and points; it never drives" |
| No central MIS at all: shared code and an almanac only | Loses cross-market readings (currency strength, dispersion, lead-lag) | Simplest | "Each unit looks for itself" |

**Recommendation.** The telescope. His order (style, then timeframe, then the data a market offers; STATE 29/30 Oct, CHECKED) becomes three labels on every reading (`mis-field.md` B001-B004, CHECKED): its **clock tier** (tick, bar, session, day, week), its horizon, and the **minimum data level** it needs. A unit's trading style picks which tiers it subscribes to; an asset class enters as a pack of rung tables, calendar and sensors. Every reading is published three ways: the raw number, its percentile against the usual for that instrument and minute of the week, and a word. The fast tier holds "now versus usual" ratios (spread, tick rate, top-of-book depth, realised range, cost against the unit's target) computed where the feed lands; direction and regime labels live on the session and day tiers, because at 1m a strong new trend takes about 8 hours to show (research 05 via `mis-field.md` F-R05, CHECKED). Cross-sectional readings only a shared service can make (currency strength, dispersion, herding counts, dated pair similarity by joint state) are published for the risk session to use; the MIS describes and never controls. Agents may add readings in shadow freely; a reading goes live only with his yes, which is his own wording: "the MIS can be upgraded as the agent see fit, obviously with my approval" (`T1:1951`, CHECKED).

**What "units read the MIS" means, settled.** Three uses were mixed (funnel3 CIS §4.3 insight 1, CHECKED): placement, a rule input, a veto. Placement reads the finder's match list inside his ticked markets. A rule input or a veto binds a reading the unit computes itself from its own feed with the same library code, so nothing changes when the MIS is down. This meets all three of his dated positions: units "pick the output and they propose whether to use it or not" (`T1:1951`, CHECKED in `mis-field.md` S-READS), "the unit itself accesses both market and MIS" (S-LIVE), and "if the MIS is not working, it doesn't mean that these bots won't trade. They will" (`T2:135`, CHECKED).

**Proof that the MIS helps.** Every unit's record includes a dark-MIS run (the same period with no MIS input) and, on paper or in QMB, a shuffled-readings run: if results do not change, the unit never used the MIS (`mis-field.md` B061, B096, CHECKED). These are two cheap judge stages, not a battery.

**Forge changed.** Dispersion became a must-publish after "twenty matches can be one bet" (research 16 break 3 via STATE, CHECKED). Home markets became required for any unit that reads a match list.

**Research could change.** Research 22 decides which fast readings carry information at 1m and 5m after costs; research 23 and 37 decide whether one shared word set holds across classes or each class needs its own models, and whether HMM-type labels earn a day-tier place; research 27 decides which correlation measures the MIS should publish for the risk session. All three are **provisional** inputs to the tier contents, not to the telescope shape.

### 3.4 QMB

| Option | Hard cases | Maintain | Explain |
| --- | --- | --- | --- |
| **Reshape (recommended)**: keep QMB's modules; window the reader; add a runner driven by the unit spec; stamp R and context; count tries at the door; add trade-print replay | Covers every instrument kind once the reader is windowed | Projection, rerun, variants, sweeps, optimiser, robustness and synthetic data are already built (CHECKED in r18 §2) | "The tester learns to run a real unit, with no time limit" |
| Rebuild on LEAN or Jesse | Strong engines | Two worlds to keep in step with QML and the node | "Swap the tester" |
| Keep QMB and wrap a new runner outside it | Quick | Two replay paths that drift | "A second tester beside the first" |

**Recommendation.** Reshape. PR 204's door shape stays (one function lands every backtest, one child process, results read by object id; CHECKED in STATE QMB door section); its scaffold breaks are fixed mechanically and it is rebased onto the stack. The missing runner takes the unit spec as its bot, which is exactly what PR 204 lacked ("a factory, a declaration and policy as data", CHECKED in r42 §5). The runner replays the unit's own sizer and exits in the same code as live. Crypto trade prints and trade bars replay with a declared spread model and a lower-fidelity label (today they are refused, CHECKED in r18 §2). The judge (section 3.7) runs stages from cheap to expensive: semantic checks, screening, ablation, sensitivity and plateau, walk-forward, a cost stress, a three-instrument challenge, the dark-MIS and shuffled-readings runs, then one locked look at a sealed window. Until costs are calibrated every verdict says "costs uncalibrated" and the cost stress is on.

**Forge changed.** Hand-run tests count too, at the door. Any change of setting during a run makes a new run (QMB's rerun rule already does this, CHECKED in r18 §2), which enforces his "it runs and waits. It doesn't have to tinker with the results" (cited at `T2:132` in funnel3 CIS knot (b), CHECKED there).

**Research could change.** Research 26 (how desks judge) sets the default stage order and numbers; research 33 decides how far crypto trade-bar replay is honest and which history may be kept.

### 3.5 Data and journals

**Store of record:**

| Option | Hard cases | Maintain | Explain |
| --- | --- | --- | --- |
| **Monthly Parquet partitions per stream, one Library card per partition (recommended)** | Scales to many units and markets | Plain tables; the Library holds cards, links and versions | "Each unit's diary is a set of monthly tables the Library knows about" |
| One Library item per row | Too many objects for a 1m scalper | The content-addressed store was not built for this (INFERRED) | "Every row is a file" |
| The telemetry store (OpenObserve) as the record | Good for ops | Not his content; backup class unclear | "Logs are the diary" |

**Recommendation.** F4 as written, with these settled points. Seen-but-not-taken rows carry one reason from a closed, appendable list plus free text. Missed trades are computed afterwards by replay, never written live (`live-field.md` B067, CHECKED). By default only events are written; logging every decision per bar is switched on per unit for a time box. Guard verdicts are rows of kind `guard` in the unit journal; account-level guard events go to the node journal. Agents read through a journal door (a catalog row), a prebuilt trades-with-context table so they never write joins, and a one-page daily digest per unit made by script before any model reads it. Agents write only in their notes stream. The UI shows a preview card and a detail page; the UI is judged by running its design, never by its code (STATE 30 Oct, CHECKED), and is its own session.

**Recording.** Everything a unit or the MIS subscribes to is recorded as bars plus the market-journal minute; quote ticks are recorded for the instruments units trade, on the machine that trades them, as disk allows. Hyperliquid keeps only about 3.5 days of 1m candles, so QMX must record its own perps history from the day a perps door opens (STATE research 02 row, CHECKED). How much disk to buy is decision 6.

**Forge changed.** A guard stream of its own was folded into kinds. Per-bar decision logging became opt-in and time-boxed after the row-flood attack.

**Research could change.** Research 33 decides whether downloaded and recorded history may be kept and used by agents (Dukascopy's terms forbid bots and databases, STATE "For his awareness", CHECKED); research 31 gives real data volumes per unit.

### 3.6 The live side: node, connections, PC first

**Runtime shape:**

| Option | Hard cases | Maintain | Explain |
| --- | --- | --- | --- |
| **One image, two places (lean)**: the QMX host gains a trading role; QMN's protection set and venue code move in as packages | The PC rehearses exactly what the server runs | One install path, one observability stack, one set of paths | "The same program runs on your PC and on the server" |
| Keep QMN as its own Linux node and run it on the PC under a Linux layer | Rehearsal works if the layer is faithful | Two stacks: QMN's own paths, credential store and Grafana/Loki/Prometheus beside the host's OpenObserve (CHECKED in r42 §3) | "A second program just for trading" |
| Port QMN to run natively on Windows | Removes the Linux layer | QMN's powers door uses `SO_PEERCRED` Unix sockets and systemd (CHECKED in r42 §3) | "Rewrite the trading program for Windows" |

**Recommendation.** Lean to the first; party mode compares the first two (section 7), because the choice is an implementation shape. Either way the code that runs on a trading server must first run on his PC, which is his rule: "if something is to run on external compute and external storage, it should first run on my machine." (`T2:1148`, CHECKED). QMN needs Linux and systemd today, so his PC needs a Linux layer to run it at all (CHECKED in r42 §3; `live-field.md` §1 fact 2). Running the identical image in that layer counts as "on my machine": his rule is about not re-auditing code when it moves, and the same image removes the move (lead call; he can say otherwise).

**Setup.** A trading server is one more kind in the connect dialog, on the shipped step runner (his cards, then checked rerun-safe steps, one row written last; CHECKED in r42 §2.2). The wizard starts the cTrader app registration on its first card, because Spotware approves each trading server's app with no published timeline (ruling 135 text `:254`, CHECKED). The connect self-test lands a passport item: kill-switch latency, a demo test trade, broker connection, clock skew, disk, feed freshness. One trading server to start; a second is a clone in another provider, by his click.

**Feeds and routes.** One feed keeper per machine, one subscription per symbol, fanned out to the units on that machine, with one home per broker sign-in (research 12 via STATE; ruling 135 text, CHECKED). A connection has two roles, data and execution; a unit binds one data route per data kind and one execution route, so a proxy (CME tape as a signal for a cTrader index CFD) is declared and tested, never silent (`live-field.md` B052-B055, CHECKED).

**Failure.** Every live order carries its stop at the broker. The client order id is the trade's trace id, so a retried send never doubles a position. On restart the broker's positions and deals win and journals rebuild from them. The trading runtime journals before it sends. A laptop that is off is the normal state; the node's outbox syncs when the PC returns. Where a venue offers a dead man's switch, silence cancels resting orders (provisional until research 38). With the feed stale, no new entries and protection stays at the broker (research 35 §6 item 10, CHECKED). All guard levels run on the trading machine with no PC (standing order 10).

**Keys.** Ruling 135 against PC first is decision 1. The recommendation there is the lead's earlier candidate, strengthened: the whole stack runs on his PC against demo accounts and, in shadow, on live prices; only the real-money key lives on the trading server; a short difference list (the key, the host name, the broker app) is the only allowed difference between the two; the trading server never shares the PC's SSH key to the workflow server (`live-field.md` B105, CHECKED); a trade-only key with no withdrawal right still counts as a live key (B099).

**Forge changed.** "Who stands in when the server is down?" cracked the recommendation: under ruling 135 as written, nothing can (`live-field.md` P02, CHECKED). Broker-held stops, a venue dead man's switch and a passive second server reduce the harm; the residual risk is part of decision 1.

**Research could change.** Research 31 decides whether QMN runs faithfully under WSL2 or a container, how strong a walled Windows account is against an agent shell, and the time per step on the live path; research 38 decides which venues offer account limits, trade-only keys, test environments and dead man's switches, and how futures with order flow are reached; research 32 fills the instrument record.

### 3.7 QMX workflow templates

**Delivery** (his two options, widened in `workflows-field.md` §5, CHECKED):

| Option | Hard cases | Maintain | Explain |
| --- | --- | --- | --- |
| Build everything in the coding phase | Real runs show real failures | Late: analyst families wait on the node | "We build them when the parts exist" |
| Write detailed recipes now, code later | Nothing runs against real data | Recipes rot as the doors are redesigned; 23 drafts already cite doors redesigned since | "Write the recipe now, cook later" |
| **Build the shared core, write the rest as validated drafts (recommended)** | Strong where reuse is highest | The core is tested once; drafts validate at install and name what they wait for (`meta.needs`, CHECKED in r42 §1.6) | "We build the parts every recipe uses, and the recipes sit ready, saying what they wait for" |

The Lab as the first builder of templates is not recommended: the Lab is a workspace only and its agent rows are closed (CHECKED in `workflows-field.md` §5 O3).

**The core, built in the coding phase first:** the judge block (one subworkflow every finding, expansion and rewrite template calls; scripts decide, a judging skill explains, he decides what passes), the try ledger and the holdout ledger, a verdict-grid kind, the conveyor (event triggers between stages plus a loop guard so a child's landing never re-fires its own parent's build), one lineage writer, the death certificate (a typed cause from an appendable list, classified by script first), a forecast-ledger kind with a scoring script, the journal door, and the proposal card that collects what waits for his click.

**First families, as validated drafts until their doors exist:** the funnel (a builder from a complete idea card, then the judge, then pass to the expansion matrix, fail to the death certificate and "where would its rules hold", rewrite to one strong-model rewrite on a plateau); market analysis at each session close with dated calls scored later by script; unit analysis of trades taken, skipped and missed; the decay check. The Hermes workflows he named ("Friendly greeting" and the gold mine, close to the old WF1 and WF2) enhance the shipped `b`, `l1`, `d3`, `d4`, `l4` and `rs6` rather than adding new templates, as he asked: "It's far better to enhance them." (`T2:1148`, CHECKED). Templates that need no model (expansion, replay match, decay, negative control, source scorecard) ship first once their doors exist.

**Proof for agents** (his "can't be cheated", settled as a lead call, section 4): every number cites a tool-call receipt the engine records; claims are typed with evidence and a superseded link; market calls are dated and scored later by a script, so "the market compares" answers "Who's comparing?" (funnel3 CIS knot (b), CHECKED); a recompute grader reruns cited receipts; every analysis names its window and what it did not see. A workflow cannot declare its own Claude hooks (`HAR/packs.py:8`, `:44`, CHECKED in r42 §7), so the judging skill's "hooks" are grader and script nodes the agent cannot skip.

**Forge changed.** The core can be tested now on synthetic results from the shipped `synthetic-data` template, before the doors exist. Delivery stays his call (decision 7) because he posed it himself.

**Research could change.** Research 29 (how agents are confidently wrong) orders which proof tools come first; research 30 (desk analysis) sets the review rhythms and which analyst family is most useful first. Three engine facts are unchecked and change wiring only: whether his Claude hooks reach engine agent steps, whether an event trigger can see his publish click, and whether the memory toolset writes durable rows (`workflows-field.md` Q01-Q03, INFERRED open).

---

## 4. Lead calls settled

Each is a technical call with its one-line reason. They map to the MAP's lead-call list (ids in brackets). "Provisional (N)" means research N could change it.

**QMB**
- Reshape QMB, don't rebuild it [L08-01]. Its modules exist and match the funnel; only the runner and the reader are missing.
- The trading runner takes the unit spec as its bot [L08-02]. That is the declaration-as-data PR 204 lacked.
- QMB stamps R and the context receipt on every trade [L08-03]. Six question families can't be measured without it.
- Tries are counted at the QMB door, hand runs included [L08-04]. The agent that asks must not be the one that counts.
- Crypto trade prints replay with a declared spread model and a lower-fidelity label [L08-07]. Refusing them leaves crypto untestable; provisional (33).
- The old pass numbers in R return as editable defaults with an origin label [L08-10]. He distrusts numbers he never asked for, so each one says where it came from.
- The judging skill checks what an agent cannot edit: the try ledger, the sealed spec, the holdout ledger, costs present, failed children present [L08-11]. These are where cheating happens.
- "It runs and waits" is enforced by the rerun rule: any change mid-run is a new run [L08-12]. QMB already works that way.
- Until costs are calibrated, every verdict carries "costs uncalibrated" and runs a cost stress [L08-14]. Honest labelling beats a blocked pipeline.
- QMB replays the unit's own sizer and exits through the same socket code as live [L08-16]. Replay parity is the point of one code path.

**QML and the unit**
- What travels from PC to node: the spec, its version, current calibrated values and a journal pointer; indicators warm from stored history [L01-14]. Warm start from history removes DEC-0261's warm-up wait.
- A market's own settings get their own exam-baseline cell; the unit version keeps its frozen baseline [L02-18]. Decay is judged against what was tested.
- A delisted market moves to retired in the unit's per-market states; the unit trades on elsewhere [L02-19]. Per-market state makes this one transition.
- The dictionary rebuild covers form, code, status and the census gaps, keeping every concept [L04-02]. Decision 2 confirms whose design survives.
- QML needs a block catalogue, the unit spec, a compiler and the widened intent door to build units [L04-05]. Everything else exists.
- QML's small door is `new`, `check`, `test`, `promote`, `watch`, `find` over the unit spec and the journal [L04-06]. Research 07's verbs still fit the new shape.
- QML stops cheaper models' mistakes with a one-line index, a match report, labelled builder-chosen numbers, blind building and a red-team builder [L04-07]. Each closes one named failure.
- Exits are slots filled by blocks; the 57 exit entries become named blocks whose maths the risk session supplies [L04-08]. Room only, no exit maths here.
- Hybrids are written as build-time composition compiled into one unit [L04-11]. A live dependency on another unit breaks standing alone.
- A 0 to 100 signal strength may reach the sizer slot as an input; whether sizing uses it is the risk session's [L04-12]. Leaving the input open costs nothing.
- Plain Python keeps journals, lineage and tries through a manifest that declares its slots, data needs and numbers [L04-13]. The manifest is what the door counts.
- Context dimensions get numbered states with a coarse default of three values each [L04-15]. Every agent then means the same thing.
- The "genetic" move of one part across families is a child with two parents, counted in both families [L10-04]. A transplant is a structure change.
- Agent memory of failures is the death certificates and do-not-retry notes every builder reads [L10-05]. It reuses the fail branch's own records.
- Stage 0 becomes the idea-record layer in front of units [C-Q5]. Lineage must start before a unit exists (research 10 via STATE).
- A source with no exit enters with a labelled builder exit from a named exit block, and cannot reach paper until the risk session's default exit set fills it [C-Q4]. The unit must own exits.
- Builders build blind: the builder step gets no backtest toolset [Q61, Q37]. Hiding files is not enough.
- An agent-built unit's first judged window starts after the building model's training cutoff, or a memory probe runs [C5 template]. Model memory is a look-ahead.
- LLM-in-the-loop blocks stay out of the live trade path [Q72]. Agents never sit in the trade path (research 11 via `workflows-field.md` §7).
- Who may widen a declared range: only he, through a proposal card [Q05]. A wider range is new live behaviour.

**MIS mechanics**
- Label versions: a retrain writes a new version column and never rewrites [L03-12]. Old trades must keep the label they traded on.
- Templates made by workflows: a sensor scout adds readings in shadow; live needs his yes [L03-16]. His own words set the rule.
- Freshness per tier is a number per tier (section 5) [L03-18]. Stale is relative to the clock a reading runs on.
- The cheapest useful MIS: fast seasonal ratios plus session and day buckets, models added later through shadow [L03-23]. Practice and research 05 say most scalper context is "now versus usual"; provisional (22).
- 24/7 markets get sessions from measured activity and the funding clock [L03-24]. A clock session does not exist there; provisional (37).
- One labeler code runs in QMB and live [L16-03]. F2.
- Replaying what a unit read costs one reference per reading in the receipt [Q3]. No copies.
- Agents get a toolset that reads the board as of their own timestamp only [L11-11]. Look-ahead is closed by the tool, not by trust.
- Fast readings compute where the feed lands; slow readings on the PC [L03-17 part]. Place follows tier.

**Broker connections**
- Two machines on one cTrader grant: one home per sign-in, the others ask that home; each trading server has its own app [L05-10, L14-06]. Ruling 135's detail already settles it.
- The market journal is the measured half of the instrument record and fills QMB's cost models over time [L05-11]. It is GAP-0048's way out.

**Book**
- Portfolio optimisation is a template (`p1`), not a fixed part [L06-09]. Numbers ship as templates; the risk session owns its content.

**Agent mechanics**
- Landmark windows are a typed field on every analysis, passed to the data door [L09-08, Q56]. He asked for "a landmark".
- "Why did this unit trade this" is a script walk from trade to signal to reading to market minute to data health, then a cheap model writes it up [L11-03]. Numbers first, prose last.
- Review timing in 24/7 markets runs on a clock table of session closes plus a rolling crypto clock [L11-07, Q60]. There is no end of day.
- The copilot explains a run from its ledger and verdict grid [L11-08]. Both already exist.
- Templates map to analyses as in `workflows-field.md` §1 [L11-09]. That table is complete.
- Unit analysis fires on every N closed trades, each session close and each landed result [L11-10]. Event triggers exist; the landings are what is missing.
- The old Cartographer and Coroner return as the weekly market map and the death-certificate graveyard [L11-14]. Both fit the forecast ledger and the fail branch.
- Agent claims are typed records with a superseded link [L12-06]. The old opinion node shape (research 19 §8 via STATE).
- Several models are review lenses, never a vote [L12-08]. Numbers decide.
- An agent's script is checked by the recompute grader and reviewed as code before a template ships it [L12-10]. Self-checking is the failure mode.
- Every analysis states what it did not see [L12-11]. Silence reads as coverage otherwise.
- The engine records receipts [Q55]. It already ledgers every tool call.
- Source text never acts as instructions: it enters marked as data [Q58]. Videos and articles can carry instructions.
- What "can't be cheated" means: the agent cannot steer the outcome, so proof separates who claims, who controls the inputs, and when the claim is scored [agent-proof ticket]. Provisional (29) on which tools come first; he can say he meant something else.

**Node operations**
- Self-tests on connect land a passport item [L14-07]. His seed.
- After a crash the broker's record wins [L14-08]. The broker holds the money.
- Clocks: store UTC, stamp venue time and receive time, calendars as data with daylight saving [L14-09]. Session rules break on time zones otherwise.
- Full disk: tick recording gives way before journals; a feed gap means no new entries with protection kept [L14-10]. Journals are the record; protection sits at the broker.

**Time and speed**
- The clock that replaces "5 trading days" is one clock per reading tier [L15-02]. A scalper's context and a swing unit's do not share a week.
- 24/7 and session instruments live in one book through per-instrument calendars [L15-03]. The calendar is data on the instrument record.
- A unit recalibrates on its slow clock (nightly or after N trades); only numbers declared "scaled by a live statistic" move per bar [L15-04]. Motion is declared, not improvised.
- Router speed comes from precomputing: the board is ready before the session, and units never wait on it [L16-02]. His feed-ranking analogy.

**Words and old ideas**
- "Sniping" is a named time window held as calendar data, with optional order-flow trigger blocks inside it [L19-06]. A window is a coordinate; the trigger is a block.
- Of the 20 forgotten old ideas, these return: `capability_spec` as the shape of a unit's context claim (REQUIRE, WARN, BLOCK), `symbol_scope`, the regime-specialist tag, the dated pair ledger (as MIS readings), weekly market selection (as the finder), opinion nodes (typed claims), the Cartographer and Coroner, one scout per source class, the video tag dimensions, the news states SAFE, PRE_NEWS, KILL_ZONE, POST_NEWS as calendar states [L20-03]. The Intent Aggregator, first-setup-wins slots, house money, slot stagger and the complexity penalty go to the risk session; the breaker's automatic transitions stay out; the April Sharia rules are decision 8.

**Cross-ticket calls**
- Units read the finder for placement and compute their own readings for rules and vetoes (units-and-the-mis ticket). It meets all three of his dated positions without breaking standing alone.
- No separate router part: placement is the finder's match list inside his ticked markets, and the unit picks by its own record (registry-and-router ticket). "The router only routes" is then the finder pointing; half the router debate was a word problem (`playing-field.md` §4).
- Agent shortlists stay advisory and are scored like a reading; they never bind a unit [L11-05, Q25]. Steering where money goes would otherwise become agents touching money.
- The build does not fork between "$300 with one or two units" and breadth (what-qmx-is-for-first ticket). The same parts serve both; his promotion click picks the first live units. Provisional (28) on which markets suit $300.
- Style is a tag that picks clock tiers, a default exit and sizer template and data needs; "scalpers first" is a build order only, and the schema stays style-neutral (trading-style ticket). Research 35 §6 item 5: style changes holding time, costs, data and exits, not the logic family.
- Cheap models build by default and a strong model rewrites on a plateau (Q19). It is his seed (`T1:513` via `workflows-field.md` S-FUN) and a UI-editable setting, reversing the shipped default (`ENG/settings.py:175-188`, CHECKED there).
- The fail branch stays, with every context it tries counted and one sealed window per finding (Q24). Seeds keep it; the count removes the luck.

---

## 5. Numbers

Every number is a starting default, shown with its origin, and edited in the UI (his standing rule "configurable = UI-editable always"). "Unit settings" means a unit's page, Settings tab; "template card" means the template's inputs in the Library; "reading card" means the MIS reading's card.

| Number | Starting default | Origin | Where he edits it |
| --- | --- | --- | --- |
| Backtest start when none is given | March 2020; any start allowed; older data used when it exists | research 12 | template card, run dialog |
| Holdout | off; chosen per study as a boundary and a month count | PR 207 | run dialog |
| Judge: trades before a verdict | 200 | old QMX (research 08) | judge block card |
| Judge: expectancy after costs | +0.15R | old QMX (research 08) | judge block card |
| Judge: cost stress | 2x measured or published costs | research 08 | judge block card |
| Judge: PBO bands | pass below 0.25; dead above 0.50 | old QMX (research 08) | judge block card |
| Judge: deflated Sharpe confidence | 0.95 | shipped `b` template | judge block card |
| Judge: walk-forward efficiency | 0.5 | shipped `b` template | judge block card |
| Instruments in the challenge | 3 (home, close analogue, adversarial) | gold mine (research 39 K1) | judge block card |
| Decay check | nightly per unit: CUSUM on R, cone, cost and fill drift, trade-rate drift; inform only | research 08 (detects +0.1R to 0 in about 240 trades) | unit settings |
| Paper before his card | 30 trades or 4 weeks, whichever is later | INFERRED | judge block card |
| Market's own settings: record needed | 100 trades on that market | INFERRED; provisional (24) | unit settings |
| Shrinkage toward pooled settings | weight by trade count, half at 100 trades | INFERRED; provisional (24) | unit settings |
| Range-edge proposal | a number at its range edge 3 times in 10 sessions raises a card | `qml-field.md` B017 | unit settings |
| Slow recalibration clock | nightly, or after 20 closed trades | INFERRED | unit settings |
| Context states per dimension | 3 (trend up, down, range; volatility low, normal, high) | `qml-field.md` Q77 | reading card |
| Seasonal baseline | same minute of the week over the last 20 weeks | INFERRED | reading card |
| Freshness per tier | tick 2 s; bar one bar; session one session; day one day | `mis-field.md` B056 | reading card |
| Stale symbol (no new entries) | 30 s without a quote for FX majors; per instrument and hour | INFERRED | instrument record |
| Lag-to-hold admission for a reading | lag at most a third of the unit's median hold | `mis-field.md` B003 | reading card |
| Sensor retire card | unread for 8 weeks | INFERRED | reading card |
| Same-idea group | same logic across timeframes counts as one group | his 30 Oct ruling | unit settings |
| Seen-not-taken logging | events only; per-bar decisions on request for 1 day | `live-field.md` B068 | unit settings |
| Journal partition | one month | `live-field.md` B073 | Settings, Data |
| Unit analysis trigger | every 10 closed trades and every session close | shipped `dc` README | template card |
| Session clocks | Sydney, Tokyo, London and New York closes; crypto every 8 hours | INFERRED | template card |
| Calls before a calibration score shows | 100 | `workflows-field.md` §6.4 | template card |
| Proposals on the morning card | 5 a day, the rest queued | `workflows-field.md` §6.4 | Settings, Morning card |
| Plateau before a strong rewrite | 30 trials without a better validated score | shipped `l4` README | template card |
| Overnight loop | 6 revolutions, 2 without gain, 200 trials; editable, never a cap | shipped `l4` README | template card |
| Dead ends that wake the fail-branch miner | 5 new | shipped `rs6` README | template card |
| Builder model tier | cheap; rewrite step strong | his seed | template card |
| Twin run before first live | 5 trading days, journals diffed | `live-field.md` B018 | Settings, Trading server |
| PC soak before a node release | 24 hours | `live-field.md` B019 | Settings, Trading server |
| Provider token lifetime in the wizard | 1 hour | `live-field.md` B002 | Settings, Trading server |
| Drills (power cut, token refresh) | monthly, on demo | INFERRED | Settings, Trading server |

---

## 6. Decisions for him

Ten decisions. Each one is his because it touches money, his intent, words he cares about, or scope that is hard to undo. The recommendation comes first.

**1. Where the real-money key lives.** Today a lead's rule (not his words) keeps any key that can trade real money off your PC and off any machine an agent can reach; your rule says anything that runs on a server must first run on your PC.
- **Recommended:** your PC runs everything, on practice accounts and watching live prices; only the real-money key sits on the trading server; the two machines differ only in the key, the name and the broker app. The cost: when the server is down, nothing trades live, and your open trades are protected only by the stops already at the broker.
- Or: your PC also trades live while it is on, and the server takes over when it goes dark. The cost: an agent working on your PC could reach a live key.
- Or (waiting on research): the live key sits in a locked part of your PC that agents cannot enter.
- Why yours: it is about money and about who can press the button.

**2. The 239 dictionary entries.** In August you called them permanent; in October you said the dictionary needs a rebuild.
- **Recommended:** keep every idea in them, review them in place, and rebuild their form so each one gets working code, a test and a status; add the words the MQL5 articles use that are missing.
- Or: rebuild the dictionary from the articles and your sources, with the 239 as one input.
- Why yours: it is your earlier ruling, and only you can say which August choices were your intent and which were the old model's shape.

**3. What your click lets go live.**
- **Recommended:** you approve a unit together with a list of markets you tick and the broker account; inside that list the unit trades wherever its conditions hold; a market outside the list reaches you as a card.
- Or: you approve one unit on one market at a time.
- Why yours: only you promote, and this sets how far one click reaches.

**4. The same logic on another market or timeframe.** On 27 October you said yes to a separate "sibling" unit.
- **Recommended:** it stays one unit; a market gets its own settings only after the unit's record there earns them, and going live with them is your click; if the rules themselves must change for one market, that is a new unit in the same family.
- Or: keep your 27 October answer, a sibling unit per market or timeframe.
- Why yours: it changes an answer you gave.

**5. Which markets and broker connections come first.**
- **Recommended:** forex, gold and index CFDs on cTrader first; Hyperliquid perpetuals second, once the connection research is in; real futures and stocks later.
- Or: start with Hyperliquid perpetuals beside cTrader from day one.
- Why yours: it is money and scope. Provisional until the research on small accounts, broker facts and connections.

**6. Recording data and disk space.** Your PC had about 12 GB free when last read; a full tick archive needs 150 to 200 GB.
- **Recommended:** record minute bars and broker costs for everything, and ticks only for markets your units trade, on the machine that trades them; buy a bigger disk when the first unit needs tick history.
- Or: record ticks for everything now, on the trading server, with a copy on your PC as space allows.
- Why yours: it costs money, and Dukascopy's terms limit what can be kept.

**7. Workflow templates: build now or write now.**
- **Recommended:** build the shared parts first in the coding phase (the judge, the test counter, the chain between stages), and write every other template as a ready draft that names what it waits for.
- Or: build them all in the coding phase.
- Or: write them all up in detail now and code them later.
- Why yours: you posed the choice, and it decides what the coding phase builds first.

**8. The April rules: no leverage, swap-free, no futures.**
- **Recommended:** they no longer bind, since CFDs, perpetuals, futures and indices are now in scope; a unit can still be marked swap-free or no-leverage if you want some to follow them.
- Or: they still bind, which removes perpetuals, futures and most CFD trading.
- Why yours: it is about your values and your money.

**9. Three names on your screens.**
- **Recommended:** "market settings" for what was called System 2; "finder" or keep "MIS" for the thing that points units at markets; "trading server" for the machine that trades and "workflow server" for the one that runs jobs.
- Or: your own words.
- Why yours: you said System 1 and System 2 were brainstorming names, and these are the words you will read every day.

**10. News units.**
- **Recommended:** not in the first build; the news kill switch guards every unit; the design leaves room for news units later.
- Or: allow news units now, each one marked as allowed to trade through news.
- Why yours: it is scope, and your two statements disagree.

---

## 7. What the architecture step's party mode must compare

These are implementation shapes still genuinely open. Each names what would separate the options.

**High level**
1. **Trading runtime: one image or two.** The QMX host with a trading role (QMN's protection and venue code moved in as packages) against QMN kept as its own Linux node. Separate by: install steps, observability, paths, and what the PC rehearsal can prove.
2. **Brain and arm.** One trading machine holding everything against a split where only a small "arm" holds the key and sends orders. Separate by: decision 1's answer, and whether the arm adds a second concept to the trade path.
3. **Where the reading history lives.** A Library kind over Parquet partitions against a time-series store beside the Library. Separate by: the as-of query cost from QMB and live, and the backup class.
4. **The unit compiler.** Compile the unit spec to a Python closure once, against generating plain Python source that is checked in with the unit version. Separate by: per-quote speed on 100 markets on his PC, and debuggability.
5. **The MIS as one process with tiers, or as products** (a board, a stream, an almanac) sharing one word set. Separate by: freshness per tier and how each fails.
6. **The feed keeper.** One process per machine against one per broker sign-in. Separate by: cTrader's request-rate limit and token refresh behaviour.
7. **The try ledger's home.** A family record in the Library against the engine ledger. Separate by: who can write it (only the QMB door) and how hand runs reach it.
8. **PR 204.** Rebase and widen it against folding its shape into a fresh door. Separate by: conflicts with the stack's edits to `HO/host.py` and `qmx_tools/service.py` (CHECKED in r42 §5).
9. **Class packs.** One catalogue with a transfer status per entry against one catalogue per asset class. Separate by: how a cheap agent finds an entry, and how aliases resolve.
10. **The Linux layer on his PC.** WSL2 against a container against a Windows port. Provisional until research 31.

**Low level**
1. The widened callback: how intents carry size, exits and their execution form (stop-market or stop-limit, server-side or client-side, last, mark or index price).
2. The block interface: typed outputs (event, level, series, state, probability, intent) against free Python.
3. The reading card schema: tier, clock, data level, version, lag, health and the three output forms.
4. The journal row and its discriminated kinds; schema-version rules.
5. The context receipt: which references and compact values it holds, and its size per trade.
6. Idempotent order sending: client order id equals trace id across retries and restarts.
7. Reconcile precedence after a crash, and how partial fills correct the unit journal.
8. Clocks: venue time, receive time, broker server time and daylight saving in calendars.
9. The outbox protocol between a trading server offline for a week and the PC.
10. The event-trigger loop guard in the conveyor.
11. The as-of query: one function for QMB and live.
12. The risk socket's slots: the input set it exposes and the default when a slot is empty. The risk session may reshape them.

---

## 8. The grilling tickets, each with its recommended answer, and the parked list

"Lead" means settled in section 4 and reported; "Decision n" means section 6; "risk session" means handed over through the socket.

| Ticket | Recommended answer | Status |
| --- | --- | --- |
| What sits inside a unit, and what sits outside | Inside: logic slots, exits, sizer and halts slots, context and data needs, session profile, numbers with motion, market settings, exam baseline, journal. Outside: the finder, the feed keeper, the guards (run locally on the trading machine), the shared budget and pod (risk session). The smallest declaration is F3. | Lead; socket content to the risk session |
| Words to settle before architecture | Retire System 1, System 2, terrain and bare "timeframe" (bar construction) internally; use unit, logic, version, family, child, market settings, reading, finder, trading server. | Decision 9 for screen names |
| What makes two units the same unit | The edit-type table in section 3.1; timeframe and market are coordinates. | Decision 4 |
| What his click admits, and every state a unit can be in | A unit plus his ticked markets and broker account; the state machine of section 3.1 with the risk stop as the only automatic move. | Decision 3; states lead |
| Trading style | A tag that picks clock tiers, default exit and sizer templates and data needs; changing style is a new version; scalpers first is build order only. | Lead |
| QML as the unit library, and the dictionary's scope | Upgrade QML in place; the dictionary per section 3.2; scalper types are defaults, never a cage (his 27 Oct answer). | Decision 2 for the 239 |
| The pod, the account guard and one shared budget | Not designed here. The unit leaves a sizer slot that reads a budget-share input and a halts slot at account scope. | Risk session |
| Do units read the MIS | Placement from the finder; rule inputs and vetoes computed by the unit itself. | Lead |
| How the MIS is organised | Clock tiers by data level, class packs, one word set over per-class sensors; versions side by side in shadow; new readings live only with his yes. | Lead; provisional (22, 23, 37) |
| How a unit finds its markets | No separate router; the finder's match list inside his ticked markets; agent shortlists advisory and scored; a hand-attached market is his tick and counts as a try on that market. | Lead |
| What System 1 is, and what earns a System 2 | A unit with pooled settings; a market's own settings earned from its record there, shrunk toward pooled, live by his click; a gold-only source enters as a unit whose markets list is gold. | Decision 4; provisional (24, 25) |
| Bounded and live expansion | Bounded: a pass verdict starts the expansion matrix with counted tries and a stop number. Live: the finder proposes inside his ticked list; outside it, a card. The fail branch stays with every context counted. | Lead |
| Correlation jobs | The control is the risk session's. The MIS publishes dispersion, herding counts, same-idea groups and dated pair readings; the trade path leaves one hook point before the order for a cross-unit check. | Risk session |
| What runs on the trading node and what on the PC | Fast readings where the feed lands, slow ones on the PC; a unit uses the board while it is fresh, else its own readings; every guard level on the trading machine; one finder per machine. | Lead |
| What QMX records live | Bars and broker costs for everything subscribed; ticks for traded markets on the trading machine. | Decision 6 |
| Which instruments and doors come first | cTrader forex, gold and index CFDs first; Hyperliquid second. | Decision 5; provisional (28, 32, 38) |
| Where default numbers come from | Published practice and old QMX numbers, each with its origin, editable; QMB shows per unit the trade count its own variance needs; backtest foundations first, then paper. | Lead; provisional (26) |
| Which analyst workflows come first | Market analysis at session closes with scored calls first (it needs only the data door); unit analysis once journals exist; specialist desks later as subworkflows. | Lead; provisional (30) |
| Proof that cannot be cheated | Receipts, typed claims, a forecast ledger scored later by script, a recompute grader, landmarks. | Lead; provisional (29) |
| What QMX does first | No build fork; his click picks the first live units. | Lead; provisional (28) |
| The risk socket | Exit set, sizer and halts slots at position, unit and account scope; readable inputs as `RISK-SIZING-PACK.md` §4 lists; an empty slot runs a labelled placeholder in backtests and blocks paper and live. | Risk session fills it |
| Prototype: the steps before one trade | Data fresh, then the unit's own readings and conditions, signal, the market's state is live, local guards (news window, spread against the unit's cost target, kill-switch level), sizer slot, exit set attached, the cross-unit hook, journal, order with its stop at the broker, fill journalled. Each step runs on the trading machine; with the finder, PC or Library down, every step still runs. | Sketch in the architecture step |
| Prototype: one unit configuring itself | Numbers with declared motion move inside their ranges from the journal on the slow clock; a range edge raises a card; the sizer's maths is the risk session's. | Risk session walkthrough |
| Prototype: one unit's records | Built from F1, F3 and F4 in the architecture step. | Architecture step |

**Research tickets and what they can move.** 22, 23, 37: the MIS tier contents. 24, 25: market settings. 26: judge numbers and order. 27: what the MIS publishes for the risk session. 28: first markets for a small account. 29: the order of proof tools. 30: analyst rhythms. 31: the Linux layer, the walled key, time per step. 32: instrument-record fields. 33: what history may be kept, crypto replay. 38: doors, futures, dead man's switches, trade-only keys.

**Parked (kept, not dropped).**

| Item | Why parked |
| --- | --- |
| Risk and sizing maths, exits, house money, Kelly, size growing back, the floor ratchet, the account guard and pod, correlation control, the Intent Aggregator | The risk-and-sizing session |
| Funding modelling for perps beyond the instrument record | His "a bit out of scope for now" |
| News units | Decision 10 |
| Paid data (Databento, Tardis) | Only when a unit needs it |
| Router offers, expiry and load-balancer mappings | He found them over-built |
| Automatic promotion of anything | Only he promotes |
| Agents or LLM blocks in the live trade path; RL units live | Agents never touch money |
| Specialist desks, crossover across families, rebuild with a newer model, template health | Later families, after the core |
| Vision-model chart readers, twin search, market recommendation feeds | Wildcards, after the stamped history exists |
| Commodity futures pack, stocks pack, options as context | After the first doors |
| Prop-firm accounts, swing units beyond "barely", the spot-only shift | His earlier parking |
| The `human_gate` node kind | Engine work; his publish click does the job today |
| A Fable advisor for the architecture party | Only on his explicit go |
| Hardware or home-appliance key holders, broker free VPS, hourly rental, ARM boards | Fail the power-cut reason or wait on research 31 and 38 |

---

## Appendix A. Affinity clusters (convergence move 1)

Every field's ideas and questions were sorted into themes. Counts are the rows each field contributed (INFERRED by reading, not by script). The through-line: **honest records, a unit written down as data, and one code path in test and live.**

| Cluster | Main sources | Through-line |
| --- | --- | --- |
| Honest records: stamps, R, as-of history, versions | PF L08-03, L09-06, L03-12; QF B020, B105, B106; MIS B089-B095; live B063, B072 | Nothing can be judged without what was known at the time |
| The unit's written form | QF T1, T2; seams S1-S7; PF L01-01, L01-09 | A rule's parts become data |
| Identity and lineage | PF L02, L10, C2, C3, C10; QF B007, F01, F13 | The type of edit decides |
| The dictionary as a living library, class packs | QF T3-T5; MIS §2.2; R36 | Every word runs, every class has three homes |
| Market reading by tier | MIS §2.1, §2.3, §2.7; PF L03 | Style picks the clock, data picks the rung |
| Standing alone and failure | PF L13, L14; MIS §2.8; live §2.3 | Every hard need is local |
| Judging and tries | PF L08; WF family C; QF T11 | Count at the door |
| Agents as analysts and their proof | PF L11, L12; WF H, I, J; MIS §2.5 | The market scores the call |
| The funnel as workflows | WF A, B, D, E, F, G, K | Enhance the shipped drafts, add the chain |
| Live node, PC first, keys | live §2.1, §2.2, §2.9, §3 | Same image, two places |
| Data and execution routes, feeds, recording | live §2.4, §2.5; PF L05, L09 | Data and execution are separate roles |
| Journals and what agents read | live §2.6, §2.7; PF L09 | One row shape, one writer |
| Room for risk | QF T10; PF L06, L07; MIS §2.6 | Slots and inputs, no maths |
| His view | PF L17, L19; QF T9; MIS §2.9; live §2.8 | Plain words, preview then detail |
| Wildcards kept | MIS §2.11; QF T12; live §2.10 | Parked, not dropped |

## Appendix B. Build scope (convergence move 2, MoSCoW)

| Must (first build) | Should | Could | Won't this time |
| --- | --- | --- | --- |
| F1-F6; QMB windowed reader, unit runner, R and receipts, door-side tries; unit spec, compiler and catalogue v1 (the six running indicators plus what the reference unit needs); journal kind and door; instrument records for cTrader forex, gold, index CFDs; MIS v1 (fast seasonal ratios, session and day buckets, stamped history); the judge block; the trading image on his PC with demo and shadow; the trading-server kind; broker-side stops, reconcile, outbox; one reference unit on the cTrader demo; risk socket slots with a test placeholder | The conveyor and the builder template; death certificates; the forecast ledger and session-close analysis; the traded-skipped-missed review; the decay check; the dictionary review workflow over the 239 plus census appends; the agent journal digest; dispersion and herding publishing; market-journal costs feeding QMB | Perps pack and Hyperliquid door (after research 38); futures; specialist desks; crossover; sensor scout; vision chart reader; twin search; passive second server; rebuild with a newer model; template health | Router offers and expiry; automatic promotion; agents in the trade path; RL or LLM blocks live; news units (decision 10); paid data before a unit needs it; large agent simulations; options trading; prop-firm rules; `human_gate` |

## Appendix C. Forge attacks (attack mode, two voices each)

Voices: one installed BMad persona (Winston the architect, Murat the test architect, Mary the analyst, Amelia the developer, John the product manager), voiced by the lead since the roster script was not run, and one generated outsider. In attack mode nothing was agreed until it survived.

**C1. The stamped trade (F1).** *Murat:* "R needs an initial risk. Grid units and time-exit units have no stop, so they have no 1R." **Cracked.** Changed: R comes from the declared invalidation or initial risk at entry; where a unit declares none, R is a typed "undefined" and money still shows. *Dee, a prop-firm scalper:* "Entry context isn't enough; I lose trades on what happened while I was in." **Cracked.** Changed: the receipt is stamped at entry and at exit, with excursions in R. *Both:* "Stamping state on every trade copies the MIS log." **Held**: the receipt holds references and a few compact values.

**C2. Readings stored with the moment they were made (F2).** *Winston:* "A hundred markets times twenty readings per minute is a storage bill." **Held, narrowed**: the fast tier is stored as minute summaries; tick-level values live only in a trade's receipt. *Grace, an on-call engineer:* "Two machines disagree on the time." **Cracked.** Changed: venue time and receive time on every value. *Okafor, a quant:* "Backfilled values will be mistaken for live ones." Changed: backfill flag.

**C3. Declared skeleton, coded blocks.** *Dee:* "My scalper is a state machine: armed, cooldown, re-entry. Your slots can't hold it." **Cracked.** Changed: the lifecycle operators joined the combiner. *Amelia:* "Two languages; cheap agents will write Python anyway." **Held**: agents write only the document; a missing block becomes a tagged Python block and an append request, and the red-team builder looks for empty units that pass. *Winston:* "Interpreting per quote is slow." **Held**: compiled once into a closure.

**C4. Identity by edit type and market settings.** *Okafor:* "Fitting settings per market is a hidden search; 'it wins on gold' is selection bias." **Cracked.** Changed: a market's own settings come only from the unit's record there, shrink toward pooled values, count as tries, and go live by his click. *John:* "He said yes to sibling units on 27 October." **Held as a decision**, not settled for him (decision 4). *Mary:* "A 1m rewrite of a 5m logic?" **Held**: a rewrite is a structure change, so a child.

**C5. The MIS as a telescope.** *Grace:* "When the finder is stale, where does a list-reading unit trade?" **Cracked.** Changed: home markets are required, and a stale list falls back to them. *Okafor:* "Twenty matches can be one bet." Changed: dispersion and herding counts are must-publish, for the risk session. *Dee:* "At 1m you can't see a trend in time." **Held**: direction lives on session and day tiers; the fast tier is cost and activity.

**C6. Journals.** *Murat:* "A 1m scalper on a hundred markets floods seen-not-taken rows." **Cracked.** Changed: events by default, closed reason list, per-bar logging opt-in and time-boxed. *Winston:* "One Library item per row won't scale." **Held**: Parquet partitions with Library cards. *Grace:* "A server offline for a week." **Held**: journal before send, outbox sync.

**C7. The try ledger and the judge.** *Okafor:* "No one knows how to count a change of exit family as a fraction of a try." **Cracked, bounded**: each tested variant counts as one whole try per family, the conservative choice; provisional (26). *John:* "He doesn't trust numbers he never asked for." Changed: every gate shows its origin and is editable; the judge reports, he decides. *Murat:* "Agents rerun until green." **Held**: the door counts, not the agent.

**C8. Live keys: same image, key on the server.** *Grace:* "The server dies at 3 a.m.; who stands in?" **Cracked, not fully fixed**: nothing stands in under ruling 135 as written; broker-held stops, a venue dead man's switch and a passive second server cut the harm; the rest is decision 1. *Viktor, a broker's risk officer:* "Demo hosts differ from live hosts; rehearsal proves code, not the venue." Changed: shadow on live prices, a five-day twin run, and the first live trade at minimum size by his click. *Amelia:* "QMN is Linux-only." Changed: a Linux layer on the PC, provisional (31). Added: no shared SSH key between the PC and the trading server; a trade-only key is a live key.

**C9. The dictionary: review the ideas, rebuild the form.** *Amelia:* "Blocking builds below 'implemented' blocks 85% of sources." **Cracked.** Changed: no block; the part is tagged. *Mary:* "A rebuild loses August intent." **Held**: every concept is kept; only the form changes; the reviewer's brief holds no verdict (research 41 lesson). *Lena, a cheap model with a small context:* "Four hundred entries won't fit in my context." **Held**: one-line index, entries on demand.

**C10. Templates: build the core, draft the rest.** *John:* "You can't test a core whose doors don't exist." **Cracked, bounded**: the judge, ledgers, verdict grid, conveyor and lineage writer test on synthetic results now. *Murat:* "Event triggers loop." Changed: the loop guard. *Okafor:* "Workflows can't declare hooks, so the 'judging skill with hooks' is fiction." **Held, reworded**: graders and script nodes the agent cannot skip are the hooks.

**What the forge killed.** Builds blocked by entry status; per-row Library items for journals; a separate guard stream; a pure data-first rule interpreter; the dual-path intent flag; a separate router part.

**What survived as weak points.** The stand-in gap under ruling 135 (decision 1); the try count for structure changes (research 26); whether one word set holds across asset classes (research 23 and 37); the Linux layer's faithfulness on his PC (research 31).
