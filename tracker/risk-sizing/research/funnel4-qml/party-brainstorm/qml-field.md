# The QML field: ideas, options and questions around QML and its strategy dictionary

Written 2026-10-30 by the QML expansion agent (planning run, QML expansion round). This file widens the field. It chooses nothing and designs nothing. Exits, stop and target maths, sizing maths and account halts belong to the risk-and-sizing session; here they appear only as the room QML must leave.

## How to read this

**What fed it.** Two skills run in this workspace, over the seeds named in the brief:
- `party-transcript.md`: `bmad-party-mode`, session mode, non-interactive, 12 rounds (P1 to P12), 14 voices.
- `.memlog.md`: `bmad-brainstorming`, headless, 130 ideas (B001 to B130), 13 questions, 5 insights, status complete. Its artifacts are `brainstorm-intent.md` and `brainstorm.html`.
- Field-step additions: 15 ideas (F01 to F15) added while checking that every top seed was expanded (§3). They are marked as such.

**Marks on ideas.** `S: <seed>` = seed expanded, naming the seed. `New` = not in any seed read. Seeds: R20, R21, R34, R35, R36, R39, R40, R41 = `research/<n>-*.md`; PF = `research/funnel3/party-brainstorm/playing-field.md`; GL = `research/funnel3/cis/glossary-draft.md`; ST = `STATE.md`; T1:n / T2:n = his verbatim words (`operator/transcript-2026-10-20-to-28.md` / `-10-29-to-30.md`, line n holds the whole turn).

**Tags on questions.** `research`: facts or evidence would settle it. `operator`: his intent, money, vocabulary he cares about, or scope that can't be undone. `lead`: a technical call the lead can settle. `fog`: in scope, not sharp yet.

**Trader check.** Every question was checked against research 35 §6, "things any trader knows" (K1 to K20). The check column says `none` when the question touches no item, or names the item that is taken as given and what is still open. Questions that the list fully answers were removed and are listed in §1.2.

**Labels.** CHECKED = read this session (path:line or command). INFERRED = my reasoning. Every idea and question is a seed for the next step, not a finding about code.

---

## 0. What matters most (short)

1. **One frame holds most of the seeds.** His question was "what is a trading bot? It's just a set of rules. In programming, it's if-else statements." (T2:779). Split a rule into five atoms (reading, comparison, threshold, gate, action) and "self-tune" becomes a label on each atom: what moves, what drives it, which clock, who authorises (B001, B011). His own answer to "what tunes" was "It's numbers" (T2:779). INFERRED: the frame fits the MT5 Wizard, regime branches, ML readings and Python blocks without new machinery. It is a frame to test, not a choice.
2. **The dictionary's job is his; its shape was GPT's.** The job: "so that if someone from a source mentions anything, we already know what it is, okay? Or if it's new, we can append it" (T2:779). The shape (three layers, twelve prose fields, no code, FX and crypto spot) came from the August model, and he said "the dictionary was GPT's idea, not mine" (T1:1211). Review vs rebuild of the 239 entries is open (Q26).
3. **New ideas I think matter most** (marked `New`, not in any seed): number kinds with their own travelling forms (P-I1); an entry status ladder from "named" to "used in a unit", with builds blocked below "implemented" (B038, B104); the journal recording which entries and profiles fired on each trade, so "which words pay" is countable (B035); blind building, where the builder never sees results while writing the unit (B069); and placement checks as a dictionary query, "which of my readings exist on this instrument's data?" (B128). The strongest seed expansions are the motion label on every number (B003) and a minimum data class per primitive that the tester enforces (B052).
4. **The trader lens removed 14 would-be questions** (§1.2). What practice leaves open is narrow: when a change makes a new unit, how to count tries for structure changes, how to write by-eye context, and how far futures order flow transfers to CFDs.
5. **Correction to research 34 §1.2.** It says "how do we make sure that those if-else statements can self-tune" and "there are reasons why the dictionary was made like that" appear in neither transcript. Both are in `T2:779` today, the latter as "there are reasons as to why the dictionary was made like that" (CHECKED, `qmlfield/quotecheck.py`). INFERRED: the transcript was refreshed after research 34 searched it.
6. **One brief quote is not in the transcripts.** "take those things as seeds and expand... or you can also propose new things on top of those seeds" is not in `T1` or `T2` (CHECKED, grep for "propose new things" and "take those things as seeds": no hits). It came from the brief. It is used here as the brief's instruction, not quoted as his words.

---

## 1. Taken as given

### 1.1 The trader's floor this field stands on (research 35 §6)

Used as inputs, never asked: K1 fixed anatomy (context, location, trigger, confirmation, entry type, stop, targets, management, size, halt); K3 one concept, many roles; K4 a timeframe is a setting, and 1m and 5m of one unit are one correlated idea (also his 30 Oct ruling, ST:146); K5 style changes holding time, costs, data and exits, not the logic family; K6 instruments have session habits; K7 spread decides whether a scalp exists; K10 stale data means no new entries, protection stays; K13 higher-timeframe bias with a lower-timeframe trigger; K14 fades use limits, breakouts use stops; K15 volatility-scaled distances travel; K17 every exit has an execution form; K19 swap at 5 p.m. New York, funding every 8 hours by default (hourly on Hyperliquid), futures roll and expire; K20 few parameters, out-of-sample judgement, counted tries.

### 1.2 Questions removed because any trader knows the answer

| Would-be question | Removed because |
| --- | --- |
| Does every unit need context, trigger, stop, target, size slots? | K1 |
| Is the same unit on 1m and 5m two bets? | K4, and his ruling (ST:146) |
| Should the order type follow the setup? | K14 |
| Should stop distances scale with volatility? | K15 (whether that is the *default form for agents* stays open as Q04) |
| Does gold behave differently at the New York open? | K6 |
| What does a unit do on stale data? | K10 (the timeout is a number) |
| Which leg wins when stop and target sit in one bar? | K18, a tester convention; exit maths is out of scope anyway |
| Is HTF bias plus an LTF trigger a normal structure? | K13 |
| Does funding or swap timing matter to a unit? | K19 |
| Are fewer free numbers safer? | K20 |
| Should a high-spread market be filtered before matching? | K7 |
| Is a paper or incubation stage normal? | K11, K12 (the promotion rule is his: only he promotes, ST:39) |
| What do two opposite orders on one symbol do? | K8, an account-mode fact |
| Is one indicator used by a unit and by the MIS "repetition"? | K3: one primitive, two bindings |

---

## 2. Ideas and options, by theme

Each row is one idea. Long forms are in `.memlog.md` (B ids) and `party-transcript.md` (P rounds).

### T1. The if-else rule and self-tuning

| ID | Idea or option | Mark |
| --- | --- | --- |
| B001 | A rule is five atoms: reading, comparison, threshold, gate, action. Self-tuning is stated per atom. | S: his if-else framing (T2:779; T1:264), R36 §6.3 |
| B002 | Only thresholds and a reading's settings are "numbers"; comparison, gate and action are structure. | S: "It's numbers" (T2:779), R34 §5 |
| B003 | A motion label on every number (fixed, scaled by a live statistic, refit on a window, chosen per state, learned) beside the August origin label. | S: R36 §7 q8, R34 §2.7 labels |
| B004 | Thresholds written in forms that travel: ATR multiples, own-history percentiles, z-scores, spread multiples. | S: R35 K15, R36 §4.3 (points 84 vs ATR 9) |
| B005 | Percentile thresholds as the agent default; their lookback is itself a number and a try. | New |
| P-I1 | Number kinds, each with its own travelling form: distance (ATR, percentile), count (bars of a stated construction), clock (exchange time with a calendar and DST), ratio, probability. | New (P2) |
| B006 | A state-chosen branch is still an if-else; a regime detector is one more reading feeding a gate. | S: R36 §5.3 pattern 3 (17781), R39 C3 |
| B007 | "A number moved inside its range" (calibration, journal event) vs "a branch, block or exit family changed" (variant, counted try). | S: R35 §4.2, GL calibration D2, "exits become variant, entry become variant" (T1:1177) |
| B008 | A rule's own record may feed its readings' settings, never its branches. Room only; no exit maths. | S: R35 §5.2 |
| B009 | A declared tuning budget per unit: how many free numbers it has. | S: R35 K20 |
| B010 | Graded 0-100 conditions summed with weights against open and close thresholds; tuning moves weights and two thresholds. | S: R36 §0 point 6 (Wizard 706, 3642) |
| B011 | Four tuning axes: what moves, what drives it, when, who authorises. Crossed in §5.1. | S: R20 §1 three meanings, R36 §6.3 eight mechanisms |
| B012 | Named cell: threshold, own record, nightly, inside range = journal calibration. | New |
| B013 | Named cell: branch, state reading, every bar, declared at build = regime switching inside the logic. | New |
| B014 | Named cell: primitive, agent proposal, weekly, his click = structure search, a variant. | S: R35 §4.1 structure riskiest |
| B015 | Named cell: weight, model, every bar, learned = a model-weighted combiner. | New |
| B016 | Empty cell: a unit that switches off a branch that keeps losing. Tuning, variant or risk rule? | New |
| B017 | A drift atom: a number that keeps hitting its range edge raises a proposal instead of moving. | New |
| B018 | Two clocks per unit: fast (per bar) and slow (nightly or fortnightly). | S: research 08 WF3 via ST:171 |
| B019 | A freeze list of atoms that never tune (direction logic, order type tied to the setup, session anchors). | S: R35 K14 |
| B020 | Every tuned value is stamped on the trade record, so any trade replays exactly. | S: R39 K6 |

### T2. Layers, roles and the logic graph

| ID | Idea or option | Mark |
| --- | --- | --- |
| B021 | A fourth layer, the profile: a named set of numbers for a primitive; tuning writes into profiles. | S: R39 C2, R36 §7 q12 |
| B022 | Roles as an open list with defaults (level, context, trigger, confirmation, veto, target, invalidation, exit, management, sizing modifier, regime detector, arming, timeout). | S: R39 C3, "keep it free" (T1:1574) |
| B024 | Pillar views generated from bindings: his four, the seven of 26 Aug, the 4+4 of 1 Sep. None is the data model. | S: R34 §2.6, R39 B4, B8, R21 §2 |
| B026 | Confirmation timing (before, same bar, after) as a binding field; "after" moves the honest entry price in QMB. | S: R39 D5 |
| B027 | Sniping as a saved bundle of bindings, a template, not a primitive. | S: R39 C4 |
| B028 | Named ports on every unit (setup, entry, invalidation, exit signal, regime filter). | S: R39 E4 |
| B029 | A weighted-sum operator in the graph beside ALL, ANY, K_OF_N, sequence, within. | S: R36 §7 q4 |
| B030 | Events (happen at a time, arm) vs states (hold, gate) as two primitive kinds; his "event" (T1:2051) gets a home. | S: R34 §6 q6 |
| F05 | Structured machine fields for levels (construction, geometry, source timeframe, validity, interaction: touch, close through, sweep, retest) and triggers (bar close or intrabar, fire once or repeat, symmetry). | S: R39 D3, D4 |
| F15 | A rule state machine for each unit (dormant, eligible, armed, triggered, confirmed, entered, invalidated, expired, cooldown, reset). | S: R40 #22 |

### T3. The dictionary as a living library

| ID | Idea or option | Mark |
| --- | --- | --- |
| B031 | Entries with three faces: trader words, a machine spec (inputs, output type, parameter kinds and ranges), a reference implementation in QML code. | S: R34 §2.7 prose by order, R39 C17 |
| B032 | Each running QMF indicator is an entry's implementation; an entry without one shows a gap. | S: R34 §4 (six wrappers) |
| B033 | The twelve designed relation types, so agents find one idea under two names. | S: R34 §6 q17, R36 renamed status |
| B034 | Trader disagreements kept as profiles, not winners (close vs wick, BOS vs CHoCH vs MSS). | S: R40 #18 |
| B035 | The journal records which entries and profiles fired per trade, so "which words pay" is countable. | New |
| B036 | Drop "no code"; keep "never silently invent a default" as "every default carries its origin". | S: R34 §2.7 |
| B037 | A script matches a source's words to entries; unmatched words form the append queue. | S: "if it's new, we can append it" (T2:779) |
| B038 | An entry status ladder: named, specified, implemented, tested on data, used in a unit. | New |
| B040 | A style layer (trend following, mean reversion, breakout, scalper types, grid and averaging, arbitrage, carry, event) as tags on units, never folders. | S: R36 §7 q6, R39 G12 |
| B071 | One canonical id per concept; the nine slug collisions become aliases with a note. | S: R34 §6 q18 |
| B072 | Every parameter gets a starting profile with an origin label (RSI 14, 70/30 "published-convention"). | S: R34 §6 q22 |
| B073 | Folders stay by family, never by job. | S: R34 §2.3 |
| B079 | A one-line index like the skills list; full entries fetched on demand. | S: R39 M5 |
| B080 | Every QML design rule carries its origin (his words, GPT's design, a later session). | S: R34 §6 q3, "the dictionary was GPT's idea, not mine" (T1:1211) |
| B116 | A scoreboard of each entry's measured value added across all units. | S: R39 K8 |
| B118 | The same matcher maps his dictation slips to terms (MTFA, Febble). | S: standing order 14 |
| B119 | Dated habit notes per instrument kept as observations, never rules. | S: R35 K6, R39 I6 |
| B121 | Broad vs small: tiny index, entries on demand, profiles instead of copies. | S: R39 M5 vs his append idea (T2:779) |
| B123 | Role lives on the binding; each binding carries a one-line trader sentence. | S: R34 §2.3 |
| B126 | An append needs a family, a data class, and an implementation or a stated gap. | S: his "appendix having new things" warning (T2:779) |
| P-I6 | Review the ideas, rebuild the form: the 239 entries' concepts reviewed in place, their format rebuilt with code. | S: R41 §2.1 "permanent", "the dictionary needs a rebuild" (T2:216) (P12) |
| F01 | A corrected successor is the only way an entry's ambiguity gets resolved; the old version stays. | S: R39 G8 |
| F02 | Failure history on every entry and unit card: failed tests and why. | S: R39 F5 |
| F10 | Trust split by layer on generated entries: format, domain content, canonical status, route. | S: R41 §4 #4 |
| F11 | Whoever reviews the 239 entries gets no verdict in the brief. | S: R41 §4 #6 |
| F13 | Two lineages: knowledge (sources to entries) and runs (units, tests), with a curated path back. | S: R39 G11 |

### T4. Asset classes beyond FX

| ID | Idea or option | Mark |
| --- | --- | --- |
| B041 | Futures pack: front month, roll window, continuous contract method, expiry, RTH and ETH, overnight high and low, settlement, tick value, OI, COT. | S: R35 §2.2, R34 §6 q14 |
| B042 | Index pack: cash open, opening drive, gap fill, initial balance, value area, cash vs futures basis, breadth (A/D, TICK, VIX). | S: "now I'm adding indices" (T2:132), R35 §2.2 |
| B043 | Perps pack: funding and settlement times, mark vs index vs last, basis, OI change, liquidation levels and cascades, leverage tiers. | S: R35 §2.2, research 02 |
| B044 | Gold pack: London fix, NY open move, real yields, DXY, swap on longs, CFD to GC mapping. | S: R35 §2.2, research 15 |
| B045 | Stocks pack: earnings, dividends, splits and corporate actions, halts, pre and post market, short borrow, index membership. | New (research 02 notes stock CFDs are MT5-only at his broker) |
| B046 | Crypto spot pack: venue fragmentation, maker and taker, listings, BTC dominance, stablecoin flows, weekend liquidity, base and quote. | S: R40 #7, R39 L6 |
| B047 | Options words as context only (implied vol, skew, gamma levels) for index and stock units. | S: R36 §2.2 (options 83 articles) |
| B048 | Terrain facts on the instrument record; concepts in the dictionary; never mixed. | S: R35 §2.2 reading, research 16 |
| B049 | A transfer status per entry per class (native, direct, adapted, conceptual only, not transferable, not assessed). | S: R39 L5 |
| B050 | A proxy kind of entry (tick volume for order flow, CFD price for a futures tape), always flagged. | S: R35 §7 q8, R39 L7 |
| P-I4 | Per class, three homes: terrain (instrument record), class-only readings (funding, OI, breadth, delta) in the dictionary, and transfer status on each entry. | S: R35 §2.2 (P6) |
| B127 | If most sources are futures traders (his 26 Aug view), exchange language is the native dictionary and FX entries are the adapted ones. | S: R39 GM 3262 |

### T5. Data classes

| ID | Idea or option | Mark |
| --- | --- | --- |
| B051 | Ten data classes as their own family: bars, quotes, depth, trades with aggressor side, derivatives facts, calendar, events, fundamentals, sentiment and positioning, model outputs. | S: R34 §3.1 empty folders, R36 gaps |
| B052 | Each primitive declares its minimum data class; QMB refuses a test on weaker data. | S: R35 §5.2 |
| B053 | Bar construction is a dependency of the binding ("this trigger on 100-tick bars"). | S: R36 §7 q9, GL timeframe |
| B054 | Broker server time and DST as a calendar primitive every session rule cites. | S: R36 §7 q7 |
| B055 | Data-health readings (stale feed, gap, spread spike) as context primitives. | S: R35 K10 |
| B056 | A statistics family: Hurst, variance ratio, ADF, autocorrelation, efficiency ratio, half-life, entropy, z-score. | S: R36 §0 (0 of 40), R34 §6 q15 |
| B057 | A model family (HMM, GARCH, Kalman, change-point) as versioned readings: one catalogue with the MIS. | S: "HMM, BOCPD, MS, GARC" (T1:1951), research 16 |
| B058 | Evaluation words in a separate judging glossary. | S: R36 §3.1 |
| B059 | Fundamentals as slow context with release timestamps and vintages. | S: R39 I6, "If you don't use fundamentals" (T2:779) |
| B060 | A derived-reading kind (distance to session VWAP in ATR), named once. | New |
| B128 | A unit asks "which of my readings exist on this instrument's data?" Placement checks become a dictionary query. | New |

### T6. Agents building units from sources

| ID | Idea or option | Mark |
| --- | --- | --- |
| B061 | The builder's path as QML verbs, JSON in and out, one stage per call. | S: R39 N1, R34 §2.1 |
| B062 | A match report: every source sentence maps to an entry id or "unmatched". | S: his append idea (T2:779) |
| B063 | Three gap kinds: abstraction (test a range), defect (stop), contradiction (stop). | S: R40 #5, R39 K14 |
| B064 | Builder-chosen numbers are labelled and counted as tries. | S: R34 §2.7 labels, R35 K20 |
| B065 | Mini knowledge bases as the builder's lookup for methods a source assumes. | S: R40 #4 |
| B066 | A creator dossier read first. | S: R39 H12 |
| B067 | "What exactly do you trade on gold" written as the logic; gold-only facts as instrument notes. | S: "around 60% of the entire thing" (T1:2051) |
| B068 | A second model re-reads the unit against the source before any test. | S: R39 H16 |
| B069 | Blind building: no backtest results visible while building. | New |
| B070 | First test on data after the building model's training cutoff. | S: research 11 via ST:173 |
| B074 | Timeframe and session on each binding, so a three-clock sentence isn't flattened. | S: R35 §3.1, R39 D1 |
| B076 | A missing block becomes an append request; loose Python stays allowed, tagged "outside QML", same journal. | S: "QML is a library so that we don't just write Python" (T2:779) |
| B111 | A red-team builder tries to pass QML checks with an empty unit; each success names a missing check. | S: R36 §2.2 random entry |
| F06 | The August search order as a QMB workflow template: fix location and context, compare trigger families, add one confirmation at a time, then challenge instruments. | S: R39 K4 |
| F12 | Source hierarchy for lineage: container, item, evidence segment, derived knowledge; each rule pinned to a timestamp. | S: R39 H4, H10 |
| F14 | His August "heavy lifting" (the ingestion pipeline) rebuilt as QMX workflows calling QML verbs. | S: R41 §4 #10 |

### T7. Plain Python and ML beside QML

| ID | Idea or option | Mark |
| --- | --- | --- |
| B081 | The escape hatch is a block: Python with declared inputs and outputs sits in the graph. | S: ST:47, R34 §4 |
| B082 | A learned model is a reading whose output is a probability; its threshold is an ordinary atom. | S: R36 §7 q2 |
| B083 | Model files hashed and versioned with their training window; QMB refuses tests inside it. | S: R36 §2.2 (ONNX 173) |
| B084 | A whole unit as a reading ("a mini scalper for an indicator"). | S: R39 C5 |
| P-I8 | The mini scalper runs as library code inside the reading unit, so the reading unit still stands alone. | S: R39 C5, standing order 10 (P10) |
| B085 | A meta-label block in the veto role. | S: R35 §5.1 family 14, research 05 |
| B086 | An RL policy as a unit kind with QML only at its edges. | S: R36 §6.3 mechanism 8 |
| B087 | LLM-in-the-loop blocks stamped non-deterministic; QMB replays logged answers. | S: R36 §5.2 (20185) |
| B088 | QML mandatory only for agents, maybe only below a model tier. | S: ST:47 |
| B089 | A minimal manifest for plain-Python units (ports, data classes, numbers and ranges). | S: PF L04-13 |
| B090 | A translate-in verb for MQL5 EAs (Signal, Trailing, Money into bindings; Money lands on the risk socket). | S: R36 §5.3 pattern 2 |

### T8. Market context as the trader's sense

| ID | Idea or option | Mark |
| --- | --- | --- |
| P-I3 | One reading, two callers: the unit binds it as a gate, the MIS computes it across instruments to rank them; same entry, same code. | S: "market context is simply what the MIS is doing?" (T1:1951), research 16 (P8) |
| B124 | When the MIS is down the unit computes the reading itself. | S: research 14 option, standing order 10 |
| B120 | A unit's condition fingerprint in dictionary words, so a scanner can match it. | S: ST:107 System 1 discussion, research 15 |
| F07 | The August MIS placement rule as an entry field: shared, expensive, market state, same in test and live, worth versioning means computed centrally and cached; still library code. | S: R39 I3 |
| F08 | Pair similarity as many readings (shared currency, session, spread, volatility, news sensitivity, trend vs mean-reversion tendency, correlation by timeframe). | S: R39 I4 |
| F09 | "The perfect identity" per family: one family's entries built deep first, so its builders and analysts improve together. | S: R39 G14 |

### T9. The trader at the screen

| ID | Idea or option | Mark |
| --- | --- | --- |
| B091 | Per unit: one trader's sentence, the pillar view, which numbers moved this week and why. | S: "simple on the eyes" (T1:1211) |
| B092 | "Why didn't it trade?" from the journal: which gate said no. | S: ST:57 signals not taken |
| B093 | The unit reads like a trading plan, with a "risk: from the socket" line. | S: R35 K1, R39 B3 |
| B094 | Self-tuning as a dial inside its range, with when and why it moved. | S: "how does it do it and what is it actually tuning?" (T2:779) |
| B095 | The copilot explains any entry in trader words with a chart of where it fired. | New |
| B096 | QML exists so a cheap agent's unit is as clear as a careful human's. | S: T2:132 small-account line |
| B097 | A dictionary browser: entries by family, with source and unit counts. | New |
| B098 | He edits defaults and ranges in the UI, never code. | S: his standing rule (configurable = UI-editable) |
| B099 | Session, instrument and unit tables of where a unit flourishes. | S: R39 I10 |
| B100 | A trader's lint in trader words, advisory only. | S: R35 K7, K14 |
| P-I2 | The unit as a JSON graph like a QMX workflow: same shape, a different (fast) runner. | S: "I'm imagining this like JSON. Most of it is JSON." (T2:779) (P5) |
| P-I5 | Units as documents let the analyst diff two units ("they differ by one confirmation") and count which units bind a word. | New (P5) |
| F03 | A Pareto view instead of one best variant. | S: R39 K7 |
| F04 | A signal funnel per unit: node fires, passes, vetoes, trades. | S: R39 K10 |

### T10. Room for exits and the risk socket (room only, no maths)

| ID | Idea or option | Mark |
| --- | --- | --- |
| B023 | A sizing-modifier role hands a reading (volatility percentile, signal strength) to the risk socket. | S: R39 C3, ST:145 risk socket |
| B025 | A completeness view of the anatomy slots: source, builder, deliberately open, socket. | S: R35 K1, DNA part F |
| B125 | Label who supplied each exit slot; the content is the risk session's. | S: R34 §6 q8 |
| B130 | The 16 exit families held as names now; the risk session fills their maths. | S: R35 §5.1, ST:145 |
| B077 | The finer August exit vocabulary (stop reference vs stop order) kept as names. | S: R40 #19 |
| P-I7 | A labelled exit slot cannot reach a test while marked "deliberately open". | S: R39 J1, J4 (P9) |

### T11. Failure modes and guards

| ID | Idea or option | Mark |
| --- | --- | --- |
| B101 | Tuning chases last month: tuned values stay inside a range fixed at test time. | S: R35 §4.1 |
| B102 | Detector lag: both branches and the no-switch baseline always tested. | S: R35 §7 q7 |
| B103 | Hidden variants: each profile used in a test counts as a try. | S: R35 §7 q9 |
| B104 | Words that can't run: builds blocked below "implemented". | New |
| B105 | Labels stamped with a version at entry. | S: research 16 |
| B106 | Context labels only from data available at that bar. | S: R39 I8 |
| B107 | One idea under two names: a similarity check on bindings. | S: ST:146 1m and 5m ruling |
| B108 | A class is testable only when its terrain pack is complete (no perps test without funding). | S: R35 §2.2 |
| B109 | Dictionary changes are append-only with history. | S: R41 §2.6 |
| B110 | Entries live in the QMX Library or are deleted; no limbo in one tool's folder. | S: R41 §4 #1, #2 |
| B117 | A random-entry baseline per family, with the same exits and socket. | S: R35 §1.3 Tharp |

### T12. Wildcards

| ID | Idea or option | Mark |
| --- | --- | --- |
| B112 | With no dictionary, what breaks names its real jobs: compare units, trace parts, swap parts. | S: his appendix warning (T2:779) |
| B113 | Drop the logic graph and keep Python with ports: what is lost is part swapping, ablation, fire counts. | S: R39 C2, GM 3262 |
| B114 | Genetic transplant of one confirmation across families, every transplant a counted try. | S: R39 G9 |
| B115 | In a year agents write most entries from sources; in five, unit journals write entry notes. | New |
| B122 | Adapt only along pre-declared, volatility-normalised axes; anything else is a variant. | S: R35 §4 |
| B129 | Shared profiles across units: improving one profile updates every unit (danger: silent retests). | S: B021 |
| P-I9 | Before any question goes to him, it is checked against the trader's list; on the list, it's an input. | S: "even me as a newbie trader, I already know what they mean" (T2:836) (P12) |

**Idea count:** 151 rows: 127 brainstorm ids (B001 to B130 less three folded duplicates, see below), 9 party (P-I1 to P-I9), 15 field-step (F01 to F15). CHECKED by `qmlfield/count.py`.

Folded duplicates, kept for traceability: B039 (data classes per entry) sits inside B052 and B049; B075 (builder binds "Sharpe") is B058's failure case; B078 (primitive needs data the instrument lacks) is B052's failure case. CHECKED by reading the memlog lines.

---

## 3. Seed coverage: every top idea from research 34, 35, 36, 39 and 41

| Source | Top idea (as that file states it) | Expanded in |
| --- | --- | --- |
| R34 | Pillars: his four, the seven, the 4+4 lock, "not finite" | B024, Q21 |
| R34 | One vocabulary to cite; role-neutral entries; folders by family | B123, B073, B037, Q16 |
| R34 | Prose by order, no entry runs | B031, B036, B038, P-I6 |
| R34 | Triggers and exits name settings but give no numbers; conventions "left open" | B072, B021, Q31 |
| R34 | Scope FX and crypto spot; six empty family folders | B041 to B051, Q40 |
| R34 | No statistical tests, models or open interest | B056, B057, B043, Q52 |
| R34 | Only declared parameter ranges tune today | B002, B011, Q01 |
| R34 | QML laws: bot never sizes, exits and thresholds in the Book | B023, B125, Q83, Q84 |
| R34 | Graduation drops context into Python | B124, P-I3, Q74 |
| R34 | Stage 0 merged but provisional; relations designed, not shipped | B033, Q32, Q37 |
| R34 | Pair, session, regime as "challenge coordinates"; trigger and confirmation the largest search surface | B013, B014, B103, Q02, P3 |
| R35 | Fixed anatomy; platforms differ only on who owns exits and size | §1.1, B025, B093, B125 |
| R35 | Context mostly computable; by-eye residue | P-I3, Q75 |
| R35 | Safe tuning is narrow; structure search riskiest | B004, B007, B122, B014 |
| R35 | Asset class changes terrain, not logic; funding and OI are class signals | B048, P-I4, B043, Q43 |
| R35 | Context declared once, read by many roles; three clocks in one sentence | B074, P-I3 |
| R35 | 16 exit families; exit-by-context is the open exit question | B130, Q11 (room only) |
| R35 | Nine questions practice doesn't settle | Q02, Q08, Q09, Q11, Q41, Q75, Q83 |
| R35 | 20 "any trader knows" items | §1.1, §1.2, the trader check column |
| R36 | Stats and models 0 of 40 | B056, B057 |
| R36 | 85% of strategy articles use a missing concept | B037, B062, Q27 |
| R36 | MetaTrader built-ins missing; custom indicators | B032, Q29 |
| R36 | Account-level and grid exits missing | B130, §6 parked |
| R36 | Fixed numbers set by the optimiser; eight self-tuning mechanisms; no field for how a number moves | B003, B011 to B016 |
| R36 | Wizard weighted signals with open and close thresholds | B010, B029, Q10 |
| R36 | No style layer; server time; alternative bars; multi-symbol bindings | B040, B054, B053, Q33, Q53 |
| R36 | Per-regime rule sets (17781) | B006, B013, Q02 |
| R36 | Learned models in 39% of articles | B082, B083, Q69 |
| R39 | Primitive, binding, graph as three layers; pillars as views | B021, B024 |
| R39 | Roles beyond four (veto, target, sizing modifier, regime detector) | B022, B023 |
| R39 | A whole bot as an input ("a mini scalper for an indicator") | B084, P-I8, Q71 |
| R39 | Timeframes and sessions as coordinates; sniping spans roles | B074, B027 |
| R39 | Three confirmation timings; a late one moves the honest entry price | B026, Q23 |
| R39 | Named ports; variants as edit operations | B028, B007 |
| R39 | Lineage link types; corrections resolve ambiguity; identity carries failure history | F01, F02, F13 |
| R39 | Pareto frontier; value added; signal funnel; labels only from data available at test time | F03, B116, F04, B106 |
| R39 | Shared market service vs inside the bot; multi-dimension pair similarity; knowledge vs dated observations | F07, F08, B059, B119 |
| R39 | Four-level source hierarchy, two-pass sort, dossier per channel, rules pinned to timestamps | F12, B066, B061 |
| R39 | Structured level and trigger fields; search order; "perfect identity" | F05, F06, F09 |
| R41 | "Permanent": the 239 are library content, reviewed first if doubted; no limbo | P-I6, B110, Q26 |
| R41 | Content must not live in one tool's private folder | B110, Q25 |
| R41 | Trust split by layer; review rather than regenerate | F10, P-I6 |
| R41 | A reviewer's brief must not hold the verdict | F11 |
| R41 | Capped memory silently deleted rules | B109 |
| R41 | Grounding documents shaped like skills | B079 |
| R41 | His "heavy lifting": the ingestion pipeline and the bots | F14, Q58 |

---

## 4. Questions

`Seed` names where the question grew from. `From` gives the party round or brainstorm entry.

### Q-T1. The if-else rule and self-tuning

| ID | Question | Tag | Trader check | Seed / from |
| --- | --- | --- | --- | --- |
| Q01 | Which atoms of a rule may move live without a new version: thresholds only, also reading settings, also weights, also the branch a state picks? | lead | K20 given (few numbers); open: the identity line | B001, B002; P1 |
| Q02 | Is a state-chosen branch (17781 style) one unit with two tested branches, or two units? | lead | none; R35 §7 q7 says practice doesn't settle regime sets vs one robust set | B006; P3 |
| Q03 | Is a motion label required on every number, or only on numbers that move? | lead | none | B003; P2 |
| Q04 | Is the agent's default threshold form instrument-relative (ATR, percentile, z-score), with raw pips allowed only when a source states them? | lead | K15 given (scaling travels); open: making it the default | B004, B005; P2 |
| Q05 | Who may widen a declared range: the unit never, an agent by proposal, only his click? | operator | none (promotion is his, ST:39; ranges are a new case) | B017; question storming |
| Q06 | May a unit's own record feed the settings of its entry readings, or only the risk socket? | lead | none | B008 |
| Q07 | Where does slow tuning run (node, PC, both), and does a unit keep its last values if the tuning job is down? | lead | K10 frames the default (keep running safely); open: where the job lives | B018; standing order 10 |
| Q08 | How are tries counted when a number moves inside its range live: each new value, or only a new range? | research | K20 given (count tries); open: live counting has no settled method (R35 §7 q9) | B103 |
| Q09 | Is walk-forward re-fitting or a fixed set the default template for 1m to 5m units? | research | none; R35 §7 q6 open | B101 |
| Q10 | Is the weighted 0-100 combiner the default for confirmations, or one operator among several? | lead | none | B010, B029; question storming |
| Q11 | Is tuning an exit's own numbers (say a trail distance from excursions) QML's room or the risk session's? | operator | none; R35 §7 q3 open | B008, B130 |
| Q12 | What smallest concrete demo would show him a unit configuring itself (ST:78 "never shown concretely")? | operator | none | B094; question storming |
| Q13 | Is "self-tune" mostly numbers, or also learning where to trade? | fog | none | "It's numbers" (T2:779); ST:107 |
| Q14 | Does the four-axis grid (§5.1) have cells that should be refused outright? | lead | K20 frames it | B011 to B016 |
| Q15 | What does the empty cell "a unit drops a losing branch" count as: tuning, variant, or a risk-rule stop? | lead | none | B016 |

### Q-T2. Layers, roles and the graph

| ID | Question | Tag | Trader check | Seed / from |
| --- | --- | --- | --- | --- |
| Q16 | Keep primitive, binding and graph as QML's model and add profiles, or flatten them for cheap agents? | lead | none | B021; R34 §2.3 |
| Q17 | Which role list ships by default: four, eight, thirteen? | lead | K1 given (the slots exist); open: the vocabulary | B022 |
| Q18 | Does "event" become a primitive kind separate from "state"? | lead | none | B030; T1:2051 |
| Q19 | Is confluence a role or only composition in the graph? | lead | none | R40 #20 |
| Q20 | Which named ports ship, and may a live unit read another unit's port? | lead | none | B028, B084 |
| Q21 | Which pillar view does the builder see first, and does it show the risk socket now that sizing is back in the unit? | operator | K1 given; open: his view and his words | B024; R34 §6 q4, q5 |
| Q22 | Do arming, reset, cooldown and re-entry live in the QML graph or in Python? | lead | none | F15; R34 §4.1 |
| Q23 | Does QMB move the entry price automatically for "after" confirmations? | lead | none | B026 |
| Q24 | Is the August rule state list (dormant to reset) the unit's state machine, or one view of it? | lead | none | F15 |

### Q-T3. The dictionary as a living library

| ID | Question | Tag | Trader check | Seed / from |
| --- | --- | --- | --- | --- |
| Q25 | Where does the dictionary live: as QMX Library objects, repo files, or both with one source of truth? | lead | none | B110; R34 §6 q13 |
| Q26 | Are the 239 entries reviewed first (his 26 Aug ruling: permanent, and reviewed first if their quality is doubted, R41 §2.1) or rebuilt from the MQL5 census and sources ("needs a rebuild", T2:216)? | operator | none | P-I6; P12 |
| Q27 | Who appends: the builder in-line, a curation workflow, or both? August rejected curator gates twice. | lead | none | B037, B126; R39 N8 |
| Q28 | What does an append need before it is a word: family, data class, implementation or stated gap? | lead | none | B126 |
| Q29 | One entry per MetaTrader built-in indicator, or one generic indicator entry plus profiles? | lead | none | R36 §7 q3 |
| Q30 | Is a variant (ZigZag vs swing pivot, KAMA vs MA) an alias, a profile or its own entry? | lead | none | R36 §7 q12 |
| Q31 | Do published conventions (RSI 70/30, ADX 20/25) become editable starting profiles, or stay notes? | lead | none (numbers ship as editable defaults, ST:116) | B072; R34 §6 q22 |
| Q32 | Which of the twelve relation types do agents need to find things? Measurable by builder trials. | research | none | B033 |
| Q33 | Does the style layer live as tags on units, on entries, or both? | lead | K5 given (style keeps the logic family); open: where the tag sits | B040 |
| Q34 | Do evaluation words get their own judging glossary? | lead | none | B058 |
| Q35 | How do the nine slug collisions resolve when entries become code with one name? | lead | none | B071 |
| Q36 | When a profile's default changes, are units using it re-tested or frozen per unit version? | lead | none | B129 |
| Q37 | Is QML Stage 0 (hypothesis types, merged but provisional) kept, folded into the unit spec, or replaced? | lead | none | R34 §6 q12 |
| Q38 | Which parts of the August design are his intent and which GPT's shape, entry by entry? | operator | none | B080; R34 §6 q3 |
| Q39 | Is population still a goal, and who populates: a QMX workflow, the copilot, the unit builder? | operator | none | R34 §6 q2; F14 |

### Q-T4. Asset classes

| ID | Question | Tag | Trader check | Seed / from |
| --- | --- | --- | --- | --- |
| Q40 | Which class pack comes first: indices, gold, futures, perps, stocks, crypto spot? | operator | none | B041 to B046; P6 |
| Q41 | How well does futures order flow proxy index CFD price for a cTrader index unit? | research | none; R35 §7 q8 open | B050; T2:132 |
| Q42 | Where can he get futures order flow and execution together, or must data and execution split? | research | none (cross-ref research 38) | ST:151; P6 |
| Q43 | Which readings are shared across classes and which are class-only? | lead | K19 given (carry schedules differ); open: the list | P-I4 |
| Q44 | Must QMB model corporate actions before any stock unit is testable? | lead | none | B045, B108 |
| Q45 | Who sets a transfer status ("adapted" vs "not transferable") for a futures-sourced idea on CFDs? | lead | none | B049 |
| Q46 | Does gold get its own pack, or is it FX facts plus GC futures facts? | lead | K6 given (gold's habits); open: where they live | B044; P6 |
| Q47 | For crypto spot, are base and quote exposures terrain or context? | lead | none | B046 |
| Q48 | Is options-derived context worth its data cost for index units on free data? | research | none | B047 |
| Q49 | Are funding, OI and liquidations readings (dictionary), terrain (instrument record), or both? | lead | K19 given (funding timing); open: home | B043; P6 clash |
| Q50 | Does Hyperliquid's short candle history mean QMX must record its own perps data before a perps unit is testable, and does recording need his go? | operator | none | research 02 via ST:164 |

### Q-T5. Data classes

| ID | Question | Tag | Trader check | Seed / from |
| --- | --- | --- | --- | --- |
| Q51 | Does every primitive declare a minimum data class, and does QMB refuse weaker data? | lead | none | B052; P7 |
| Q52 | Are statistical tests and models dictionary entries, MIS sensors, or one catalogue for both? | lead | none | B056, B057; PF L04-03 |
| Q53 | Is bar construction a binding dependency or a primitive? | lead | none | B053; R36 §7 q9 |
| Q54 | Is broker server time a calendar primitive, a data dependency, or both? | lead | none | B054; R36 §7 q7 |
| Q55 | Which data classes fit on his PC (bars yes, ticks no per research 12) and which need a server? | research | none | B051; ST:174 |
| Q56 | How are fundamentals stored with release time and vintage so a backtest never sees a revised number? | research | none | B059 |
| Q57 | Which styles can use weekly positioning data (COT) at all? | research | K5 frames it (holding time) | B051 |

### Q-T6. Agents building units from sources

| ID | Question | Tag | Trader check | Seed / from |
| --- | --- | --- | --- | --- |
| Q58 | What is the smallest source-to-unit chain a cheap model can run, and which steps must be scripts? | lead | none | B061, F14; P9 |
| Q59 | What blocks a build: defects only, or also abstraction? His August "a bot that has ambiguity shouldn't be tested" (R39 K14, GM 3262) vs his August view that an unstated timeframe is normal abstraction (R40 #5). | operator | K4 given (an unstated timeframe is a setting); open: the rest | B063; P9 |
| Q60 | When a builder fills a gap, is the unit still "from source X" in lineage, or a curated composite? | lead | none | B064; R39 G10 |
| Q61 | How is the builder kept blind to results while building? | lead | none | B069 |
| Q62 | How many tries does testing an unstated timeframe's default range cost? | lead | K4, K20 given; open: the count rule | B063 |
| Q63 | Where is the line between "the logic" (his 60%) and instrument notes, and who draws it per unit? | fog | none | B067; T1:2051 |
| Q64 | Is a creator dossier worth its cost for YouTube sources? | lead | none | B066 |
| Q65 | Does a second model check every unit against its source video before testing? | lead | none | B068 |
| Q66 | With no exit in the source, does the builder stop, or build with a labelled builder exit from a named exit entry? | lead | none (exit content is the risk session's) | B125, P-I7 |
| Q67 | May any model tier build without a person, or only above a tier? | operator | none | B088 |

### Q-T7. Plain Python and ML

| ID | Question | Tag | Trader check | Seed / from |
| --- | --- | --- | --- | --- |
| Q68 | What minimal manifest keeps a plain-Python unit in lineage, journals and the tries count? | lead | none | B089 |
| Q69 | Is a learned model a primitive whose output is a probability, or its own node kind? | lead | none | B082; R36 §7 q2 |
| Q70 | Does QMB store each model's training window and refuse tests inside it? | lead | none | B083 |
| Q71 | Can one unit feed another unit's context live and still stand alone? | lead | none (standing order 10 binds it) | B084, P-I8; P10 |
| Q72 | Are non-deterministic blocks (LLM in the loop) allowed live at all? | operator | none | B087 |
| Q73 | How far can an MQL5 EA be translated into bindings automatically? | research | none | B090 |

### Q-T8. Market context as the trader's sense

| ID | Question | Tag | Trader check | Seed / from |
| --- | --- | --- | --- | --- |
| Q74 | Is the context a unit declares the same object the MIS reads (one entry, one implementation)? | lead | K3 given (one concept, many roles); open: shared code and versions | P-I3; T1:1951 |
| Q75 | How are by-eye judgements (zone quality, swing lookback, Wyckoff phase) written: a profile with a lookback, a model, a human label? | research | none; R35 §7 q5 open | P8 |
| Q76 | How do context readings on a higher timeframe use only closed bars of that timeframe? | lead | K13 given (HTF bias); open: the no-repaint rule in code | B074 |
| Q77 | How coarse are default context states (trend: up, down, range; volatility: low, normal, high)? A number to ship as a default. | lead | none | B013 |
| Q78 | When unit and MIS versions of a reading disagree, which wins for that trade, and is the disagreement journalled? | lead | none | B105, P-I3; P8 |
| Q79 | Does the dictionary need fundamentals entries for sources that use them, though his own sense of context is price action and technical analysis? | operator | none | B059; "If you don't use fundamentals" (T2:779) |

### Q-T9. The trader at the screen

| ID | Question | Tag | Trader check | Seed / from |
| --- | --- | --- | --- | --- |
| Q80 | When a unit tunes itself, what does he want: a notice, a weekly digest, or nothing unless a range edge is hit? | operator | none | B094 |
| Q81 | Is the trader's lint advisory only, or can some warnings block a build? | lead | K7, K14 given (the practices); open: their force | B100; P11 |
| Q82 | Which words does he want on a unit card: the trader's sentence, the pillar view, both? | operator | none | B091 |

### Q-T10. Room for exits and the risk socket

| ID | Question | Tag | Trader check | Seed / from |
| --- | --- | --- | --- | --- |
| Q83 | What room must QML leave for exits: a labelled slot set, the exit family names, a socket the risk session fills? | lead | K17 given (every exit has an execution form); open: the slot shape | B125, B130 |
| Q84 | What does the unit hand the risk socket: stop distance, volatility reading, signal strength, its own record? | lead | K2 given (size follows stop distance); open: which readings cross | B023 |
| Q85 | Which QML laws change ("the bot never sizes", "no exit_logic field", thresholds in the Book)? | lead | none | R34 §6 q10 |
| Q86 | May signal strength (0-100) reach the risk socket at all? | operator | none | B010, B023; PF L04-12 |

### Q-T11. Failure modes

| ID | Question | Tag | Trader check | Seed / from |
| --- | --- | --- | --- | --- |
| Q87 | How does QML stop profiles multiplying into hidden variants? | lead | K20 given | B103 |
| Q88 | What happens to live units when an entry they bind is corrected? | lead | none | F01, B109 |
| Q89 | What is the random-entry baseline per family, and is every unit judged against it? | research | none | B117 |
| Q90 | How much of a discretionary scalper's edge survives being written in shared vocabulary at all? | fog | none | P8 (Dee: "I'm the edge") |
| Q91 | Will the dictionary be read more by agents building units or by agents analysing journals? | fog | none | B035, B116 |
| Q92 | Does the red-team builder run on every QML release, or only by hand? | lead | none | B111 |

---

## 5. Permutation cross-map

### 5.1 The self-tuning grid (B011)

Rows are what moves; columns are who authorises. Each cell names the driver and clock the brainstorm attached, or `?` where none was found. INFERRED; no cell is chosen.

| What moves \ who authorises | Nobody (inside a declared range) | Agent proposal | His click |
| --- | --- | --- | --- |
| Threshold | own record or live statistic, nightly or per bar (B012, B004) | range edge hit (B017) | a new range (Q05) |
| Reading setting (period, lookback) | volatility or efficiency ratio, per bar (adaptive indicators, R35 §4.1) | refit window (Q09) | ? |
| Weight in a combiner | model, per bar (B015) | after a review (B010) | ? |
| Branch chosen by state | state reading, per bar, declared at build (B013) | ? | dropping a branch (B016, Q15) |
| Primitive or exit family | not allowed in any seed | structure search (B014) | variant goes live (ST:39) |
| Whole unit (RL, model) | learned policy (B086) | retrain (B083) | promotion (ST:39) |

### 5.2 How questions and ideas combine

| From | Relation | To | Why (INFERRED) |
| --- | --- | --- | --- |
| Q01 tuning atoms | same | Q15, Q02, GL calibration | Three phrasings of "when is a change a new unit" |
| B003 motion label | enables | B094 tuning dial, Q80 | The dial can only show what the label declares |
| B021 profiles | enables | B103 hidden variants, Q36, B129 | Profiles are where variants could hide |
| B031 three faces | enables | B038 status ladder, B104, Q51 | A ladder needs an implementation face to climb |
| B052 minimum data class | enables | B108, B128, Q44 | A class is testable only when its data is declared |
| P-I3 one reading, two callers | conflicts with | Q78 version disagreements | Shared code still versions separately in time |
| P-I3 | depends on | Q52 one catalogue | Two callers need one catalogue |
| B084 unit as a reading | conflicts with | standing order 10 | A reading unit must not need another unit up; P-I8 is one way out |
| B062 match report | enables | B037 append queue, Q27, Q28 | Unmatched sentences are the append input |
| Q26 review vs rebuild | depends on | Q38 his intent vs GPT's shape, F11 | What to keep depends on whose idea it was |
| Q26 | depends on | Q25 where it lives | A rebuild in the wrong home repeats August's limbo |
| B063 gap kinds | conflicts with | his "a bot that has ambiguity shouldn't be tested" (R39 K14) | Abstraction vs ambiguity is his to draw (Q59) |
| B013 regime branch | depends on | B106 labels at that bar, B105 versions | A branch is only honest on honest labels |
| B013 | combines with | B102 no-switch baseline | The switch must beat no switch |
| B043 perps pack | depends on | Q49 home of funding, Q50 own history | Without stored history there is nothing to test |
| B042 index pack | depends on | Q41 order-flow proxy, Q42 data vs execution | His index scalper needs flow he may not have on CFDs |
| B081 Python block | depends on | B089 manifest, Q68 | The block keeps tries only through the manifest |
| B082 model as reading | combines with | B083 training window, B070 cutoff test | Two look-ahead guards on learned parts |
| B023 sizing modifier | depends on | the risk session's socket design | Room only; the socket's shape is not this session's |
| B125 exit labels | same | Q66, P-I7, Q83 | One honesty rule seen from builder, test and socket |
| B040 style layer | depends on | Q33, PF L04-10 scalper types | Types are defaults, never a cage (ST:43) |
| B099 flourish tables | depends on | B035 entries on trades, F04 signal funnel | Tables need per-trade words and fire counts |
| B116 scoreboard | depends on | B035, Q08 tries live | Value added without counted tries is luck |
| B114 genetic transplant | conflicts with | B007 identity line | A transplant is a variant, so it pays the tries price |
| F07 placement rule | combines with | B124 unit computes itself | Central cache for speed, local code for standing alone |
| B079 skills-like index | enables | B121 broad vs small | The index is how a cheap model holds a broad library |
| Q59 | same | PF L13 builds and gates; R34 §6 q9 | The same honesty question from two runs |

---

## 6. Parked

In scope, deferred by a ruling or by his own words. Parked is not dropped.

| Item | Why parked | Source |
| --- | --- | --- |
| Exit methodology, stop and target maths, time-varying targets, profit caps, probability exits | Risk-and-sizing session; QML only leaves room (T10) | ST:145 |
| Sizing maths, Kelly, house money, size growing back | Same session | ST:93, ST:145 |
| Account-wide halts, daily loss limits, basket and equity kill switches | Same session; R36 found them missing, noted for that session | ST:145; R36 §4.2 |
| Grid, martingale, averaging as a family | Vocabulary is needed to read sources (172 MQL5 articles); whether units may use them is a risk call (research 02 suggested a guard flags them) | R36 §7 q11; ST:164 |
| The MIS design itself | Its own research line (research 37, the MIS questions) | ST:138 |
| The router and placement | Separate design line | ST:101-110 |
| Numbers: default states, thresholds, profile values, tuning ranges | Code first, numbers later; ship as editable defaults | ST:116 |
| Paid data (Databento, Tardis) | Only when a unit needs it | ST round-2 Q7 |
| Options as traded instruments | Only options-derived context appears here (B047) | INFERRED from scope |
| Prop-firm rules | Parked since early October (PF §5) | PF §5 |
| News trading units | Open contradiction in PF | PF §5 |
| A Fable advisor for the architecture party | Only on his explicit go | ST:155 |
| The architecture-step party on how to build QML (lean vs more variants) | His proposal for the next step, not this one | ST:155 |
| Building the ingestion pipeline | Seed F14 kept; building waits for architecture | R41 §4 #10 |

---

## 7. Counts and how this was run

### 7.1 Counts

| Kind | Count |
| --- | --- |
| Ideas in §2 | 151 distinct rows (127 B, 9 P-I, 15 F); B039, B075, B078 folded as duplicates |
| Questions in §4 | 92 (Q01 to Q92) |
| Distinct ideas plus questions | 243 |
| Ideas marked `New` | 18 |
| Questions removed as trader-known (§1.2) | 14 |
| Cross-map rows (§5.2) plus grid cells (§5.1) | 27 plus 18 |
| Parked items | 14 |

Questions by tag:

| Theme | research | operator | lead | fog | Total |
| --- | --- | --- | --- | --- | --- |
| Q-T1. The if-else rule and self-tuning | 2 | 3 | 9 | 1 | 15 |
| Q-T2. Layers, roles and the graph | 0 | 1 | 8 | 0 | 9 |
| Q-T3. The dictionary as a living library | 1 | 3 | 11 | 0 | 15 |
| Q-T4. Asset classes | 3 | 2 | 6 | 0 | 11 |
| Q-T5. Data classes | 3 | 0 | 4 | 0 | 7 |
| Q-T6. Agents building units from sources | 0 | 2 | 7 | 1 | 10 |
| Q-T7. Plain Python and ML | 1 | 1 | 4 | 0 | 6 |
| Q-T8. Market context as the trader's sense | 1 | 1 | 4 | 0 | 6 |
| Q-T9. The trader at the screen | 0 | 2 | 1 | 0 | 3 |
| Q-T10. Room for exits and the risk socket | 0 | 1 | 3 | 0 | 4 |
| Q-T11. Failure modes | 1 | 0 | 3 | 2 | 6 |
| **All** | **12** | **16** | **60** | **4** | **92** |

The counts were produced by `qmlfield/count.py` over this file (§7.3), not by hand.

### 7.2 How the skills ran

- **Party mode:** activation scripts run (`resolve_customization.py`, `resolve_config.py` with `PYTHONIOENCODING=utf-8` after a console-encoding error, `resolve_party.py`). Mode `session`, inline cast, non-interactive to a natural close. An inline cast keeps no memlog under the skill's own rule (`references/party-memory.md`). The skill's keepsake HTML was not offered: no human is present, and the brief names the files to write.
- **Brainstorming:** headless per `references/headless.md`. `brain.py list --all` printed the catalogue; 19 techniques named in the memlog's direction line. Kill the Crown Jewel, Evolutionary Pressure and Time Horizon Ladder ran inside the Trickster's Gambit block (B113, B114, B115) without their own switch entries. 165 entries appended with `memlog.py`, 0 failures; status set to complete. `project-context.md` (the skill's persistent fact) does not exist in the repo (CHECKED, glob).
- **Deviation:** the headless reference says to delegate the HTML and intent artifacts to subagents. Sub-agents are forbidden by the standing orders, so `brainstorm.html` was generated by a script that reads only the memlog (`qmlfield/mkhtml.py`), and `brainstorm-intent.md` was written from the memlog. The HTML was not checked visually.
- **Deviation:** the skill's `on_complete` recommends `bmad-prd`. The run's next step is the lead's (ST "The planning run"); recorded, not followed.
- **Not converged.** No idea was ranked, merged into a design or chosen. §0 point 3 names the new ideas I think matter most, as the brief asks; that is a pointer, not a selection.

### 7.3 Quote check

Every quote of his words in `party-transcript.md` and this file was checked by `qmlfield/quotecheck.py` (scratchpad: `C:\Users\Mubarak\AppData\Local\Temp\claude\C--Users-Mubarak-Desktop-QMX\ed09cf0c-69f1-44ab-8c6b-76992918774a\scratchpad\qmlfield\`) against the transcript line it cites, splitting on ellipses. Result: 45 quotes across both files, 0 missing. One quote in the party transcript first failed (T1:1951 repeats "one of the one of the"); it was corrected to the verbatim text. The transcripts mix `\r\n` with one bare `\r`, so the checker reads them with `newline=''` to keep line numbers equal to `grep -n`.
