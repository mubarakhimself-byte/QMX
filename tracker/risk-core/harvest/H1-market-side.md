# H1: the market side the unit trades in

Harvest of what already exists on MIS and routing, market physics and regimes, SQS and spread, market isolation, news and the kill switch, sniping windows, sessions, macro and micro structure, instrument layers and scenarios. No new research. Method: `bmad-cis-problem-solving`, run headless (is / is not, root cause, options kept, nobody asked).

Paths: bare paths are under `D:\QMX-worktrees\risk-plan\tracker\risk-core\`. `UP/` is `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\`. `TIP/` is `D:\QMX-worktrees\bld-repair-24` at 255f3bbf. Component ids are short: `A3-075` means `A3-structure-regimes-scenarios-075`.

## The plain answer to what he remembers

He said: "I requested for maybe designs for the SQS systems, MIS systems, newer designs or enhancements." (M52, `seeds/operator-words-2026-11-06.md:78`)

**What exists is thin for the SQS and scattered for the MIS.**

- **SQS: no new design exists.** The final spine keeps the old rule "unchanged" and only decides where it sits (`architecture/SPINE.md:408`). What does exist is four or five enhancement fragments (ideas 16 to 21), mostly from MQL5 articles, none joined into one design.
- **MIS: no new design came out of this session.** X0 says it plainly: "MIS (flagged, not designed)" (`expansion/X0-trading-lens.md:44`, `:862`). A real MIS design does exist, but it came from the earlier unit-plan session (`UP/architecture/MIS-PAGE-CONTENT.md`, `UP/research/funnel5-mis/party-brainstorm/mis-field.md`, `UP/research/23-mis-organisation.md`, `UP/research/14-design-idea-studies.md`). Almost none of that reached the 1-7 Nov funnel.
- **The papers were never asked.** No file in `research/R4-alphaxiv/` or `research/R6-alphaxiv-papers/` contains the word MIS or SQS (word search). Those chats asked about regimes, microstructure and news in general. So the raw material is there, as about 60 components in A3 alone and 78 merged seeds in `linking/UNIT-IDEA-BANK.md`, but nobody turned it into a MIS or SQS design.
- **Why it was lost (root cause).** Three things in a row. On 1 Nov he said the MIS is "not your session" (`seeds/SEEDS.md:637`). On 3 Nov he opened it ("Whether there is new market physics, whether there is, you know, things that could be added in the MIS, no problem", `seeds/operator-words-2026-11-03.md:176`), and STATE recorded that (`STATE.md:185`). The Stage B brief passed it on as "new market physics and new MIS readings are all welcome" (`linking/STAGE-B-BRIEF.md:22`), which invites readings, not a design, and no agent was given the MIS or SQS as its job. X0 still wrote "flagged, not designed" because another session was building the MIS. Then the funnel's go-live test pushed what was left to "later" or "shadow".
- **His original wording.** A search of both main session transcripts for MIS or SQS near design, overhaul or enhancement finds only M52 itself. The search was a text pattern, not a read, so an earlier differently worded message is possible. The closest earlier words are M31 and M33 (`seeds/operator-words-2026-11-03.md:176`, `:188`).

**Something else that matters: the dollar simulation never touched this area.** The funnel's sim states "Not modelled: ... news and SQS windows, class isolation" (`funnel/FUNNEL.md:519`). So every fate below in this area was set by the go-live lens ("the first live units are FX scalpers on cTrader", `funnel/FUNNEL.md:197`). The dollar lens enters only one way: the spine's choke test counts SQS and news refusals as lost dollars (`architecture/SPINE.md:480`, `:505`).

## 1. What's here

| File | How much I read |
|---|---|
| `harvest/BRIEF.md`, `seeds/operator-words-2026-11-06.md` M48-M53 | all |
| `expansion/X0-trading-lens.md` | sections 0, 1, 2.5 to 2.8, 3 to 7 in full; 2.1 to 2.4 as hybrid names plus the first lines of each |
| `expansion/X4-scenarios.md` | all headings; ideas 94, 95; Part 4, Part 5 in full. Individual scenario bodies not read |
| `research/R2-trader-practice-windows-drift-isolation-breadth.md` | short answer, sections 1 and 3 in full |
| `research/R8-gap-topup.md` | headings, gap 4 short answer |
| `linking/components/A3-structure-regimes-scenarios.yaml` (241 rows) | names and evidence for rows 31-145 and 228-240; one-line text for 31-40, 66-87; fuller text for 179-190. Rows 1-30 and 146-227 not read row by row (X0 and X4 carry them) |
| `linking/unit-ideas/A3-structure-regimes-scenarios.md` | all |
| `linking/unit-ideas/A5-topup.md`, `linking/UNIT-IDEA-BANK.md` | MIS lines and headings only |
| `linking/stage-b/X0-trading-lens/ideas.txt` | market lines only |
| `funnel/HYBRID-FATES.md` | header, counts, every row cited here |
| `funnel/FUNNEL.md` | DP23, DP24, DP25 and search hits |
| `funnel/REVIEW.md`, `architecture/SPINE.md`, candidates 1-3, `STATE.md`, `review-2026-11-07/*`, `handoff/*`, `PARKED-FOR-NUMBERS-TALK.md` | MIS and SQS search hits only |
| `expansion/X3-brakes-exits-drift.md` | hybrids H28 to H38, H63 (first 1,000 characters each) |
| `expansion/X2-sizing-accelerators.md`, `expansion/X7-agents.md` | H42; H21, H25, H48 (opening lines) |
| `grounding/G7-unit-inputs-qmb-mis-instruments.md` | all |
| `grounding/G12-audit-and-repair-for-risk.md` | section 2 (SQS) |
| `research/R6-alphaxiv-papers/T-03-*`, `research/R4-alphaxiv/chat-27-*` | short answer, combinations, class notes |
| `UP/architecture/MIS-PAGE-CONTENT.md`, `UP/research/funnel5-mis/party-brainstorm/mis-field.md` | all |
| `UP/research/23-mis-organisation.md`, `UP/research/14-design-idea-studies.md` | short answers, the options table, option names |
| Code at `TIP/` | `qmx-agents/apps/mis/packs.json`, `qml/src/qml/compile/compiler.py:898-906`, the block folder listing, targeted word searches |

**Is / is not, from the code tip today:**

- **Is built:** the MIS app, with five readings in every class pack: change-point, efficiency ratio, variance ratio, Hurst, spread state (`TIP/qmx-agents/apps/mis/packs.json`). The block files exist. So G7's 1 Nov line "no market physics code" is out of date.
- **Is built but off the new path:** the SQS rule text, in the old node and readings package. The new node has none (`grounding/G12-audit-and-repair-for-risk.md` section 2).
- **Is not built:** a unit reading the MIS, and a unit's own sessions. The compiler refuses both by name: `reads_not_built`, `sessions_not_built` (`TIP/qml/src/qml/compile/compiler.py:900-905`). No RVOL code, only a catalogue entry. No open, fix, tick-rate, volatility-state or calendar readings in any pack, though the plan lists them (`UP/architecture/MIS-PAGE-CONTENT.md` section 4).

## 2. The ideas, best first

Order is my judgment of how much each changes what the baseline must leave room for, then how close it is to something he asked for. Fates are records of the old judgment, not verdicts. In this area "go-live lens" is the driver unless I say otherwise.

### A. The MIS as router and context

**1. The MIS as a router, with a door to widen a unit's markets**
- What: the MIS scans markets on scalping timeframes and says "this future is mean-reverting now". A mean-reversion scalper then shifts to those markets. Example: one logic moves between gold and a few FX pairs as conditions change, instead of being fixed to one pair.
- Source: his words, M5 (`seeds/operator-words-2026-11-01.md:43`, `seeds/SEEDS.md:616`); components A3-187, A3-184; hybrids X0-26, X0-46; `UP/research/funnel5-mis/party-brainstorm/mis-field.md` B023, B121.
- Touches: MIS, unit `markets` list, node board read, placement. Today the plan lets the MIS only narrow; widening is a new version and his click (G7 2.5). The field had a softer path: markets join by a proposal card when their readings resemble a unit's proven markets (B121).
- Fate: X0-26 and X0-46 later, "MIS (flag)". Go-live lens.
- Read: **seat.** The unit must separate "markets I may ever trade" from "markets I trade now".
- Standing: proposal. His idea, no placement evidence. Hard limit from simulation on made-up bars: trend or mean reversion on 1m and 5m takes about 4 to 5 hours to show, so this works as a list for the session or day, never as a per-trade signal (`UP/architecture/MIS-PAGE-CONTENT.md` section 3, items 1 to 3). Only the label known at entry is honest.

**2. Units read MIS readings, each with a stated fallback**
- What: a unit lists the readings it uses, and for each says what to do without it: compute it itself, treat it as absent, or take no new entries. "Context needs" adds require, warn or block. Every decision row records what it read.
- Source: unit plan (`grounding/G7-unit-inputs-qmb-mis-instruments.md:123-130`); A3-183; his "the unit itself accesses both market and MIS" (mis-field S-LIVE). Old form: `capability_spec` BLOCK, WARN, REQUIRE (B125).
- Touches: unit `reads` field, QML compiler, host surfaces, decision journal.
- Fate: no hybrid of its own; X0-48 is "later, once reads compile". Go-live lens.
- Read: **seat.** Nearly every idea in this file needs it. The compiler refuses it today (`TIP/qml/src/qml/compile/compiler.py:900`).
- Standing: designed and partly built, never run.

**3. Contexts, not sessions**
- What: a unit doesn't switch by "London" or "Tokyo". It reads words like mean-reverting or stressed, and settings can be keyed to a word. Sessions stay as the fallback. Two positions in an overlap aren't a contradiction; they are linked only by counting one shared bet once.
- Source: X0-48; A3-030, A3-183. He accepted it in M10 (`expansion/X0-trading-lens.md:637`). It answers his "How do we change sessions?" (`seeds/operator-words-2026-11-01.md:109`).
- Touches: override chain, unit settings, MIS words, same-bet key.
- Fate: later, "override key". Go-live lens.
- Read: **seat** for the key; the words are **content**.
- Standing: proposal. "Context words need an MIS that runs on a venue, and it never has" (X0-48).

**4. A named reading allowed to change size, with its range and reason**
- What: the modern slot for the old session, physics, RVOL and microstructure multipliers. A reading may raise or cut size, but only by name, inside a range, with the reason on the receipt. He listed SQS, microstructure and MIS strength as reasons to reduce (`seeds/SEEDS.md:126`).
- Source: A3-185; `ledger/variables.yaml` `context_size_modifier`; `grounding/G3-old-system.md:71-87` (old system's nine multipliers defaulting to 1.0).
- Touches: sizer socket, receipt.
- Fate: no hybrid of its own. X2-H42 (idea 17) is the closest, shadow. Go-live lens.
- Read: **seat.** The socket has to exist; which readings use it is content. He suspects stacked multipliers caused the old handbrake, so the receipt must show each one.
- Standing: proposal.

**5. Mini apps and agents as publishers of readings**
- What: his picture: departments. A macro mini app feeds an FX mini app, a futures mini app holds its own workflows. For this to work, anything may publish a stamped reading in the same shape as the MIS.
- Source: his words, M50 (`seeds/operator-words-2026-11-06.md:66`); `handoff/AGENT-DEPARTMENT-SEEDS.md:59-61`; B039, B080 (agents and humans writing day-tier readings); A3-145.
- Touches: reading record, Library, mini app contract, pods. The planned record's `source` field names only `node` or `mis` (G7 2.1) [my reading: this closes the door unless widened].
- Fate: never judged as an idea. Mini apps and pods were pushed out of the funnel's lens.
- Read: **seat** for the record's source and identity; **other session** (methodology and agent department) for the departments.
- Standing: his vision; no evidence either way.

**6. Agents write a dated reading, scored like a sensor**
- What: before a session an agent writes its read in the MIS's own words, using a tool that returns only data stamped before that moment. Afterwards it is scored. Three lists run side by side: agent, MIS alone, all markets.
- Source: `UP/research/funnel5-mis/party-brainstorm/mis-field.md` B033-B035, B041; `UP/architecture/MIS-PAGE-CONTENT.md` group J; A3-086, A3-087 (deterministic features, an agent only labels them).
- Touches: workflow, MIS history, copilot tools. Never the fast lane.
- Fate: X7 family, mostly later. Go-live lens.
- Read: **other session** (agent department); needs only the stamped history from idea 8.
- Standing: proposal. This fits his M49 point that agents should carry monitoring for about 200 units.

**7. Reading organisation: clock tier and data level on each reading, the class as a pack**
- What: don't build "a scalper MIS" and "a futures MIS". Every reading declares its clock (tick, bar, session, day) and the least data it needs. A class is a pack: calendar, data ladder, class-only readings. An MIS for one market is the same MIS set to one market.
- Source: `UP/research/23-mis-organisation.md` section 2, option H, against seven other groupings (section 3 below); B001-B004, B020; his "levels of specificity".
- Touches: MIS, QML dictionary, instrument record.
- Fate: outside this funnel. Taken into the unit plan.
- Read: **seat** already planned; the pack contents are **content**.
- Standing: reasoned design with hard-case tests; no trading evidence.

**8. Stamped history and an as-of question**
- What: every reading is stamped when computed, never rewritten. QMB can ask "what did the MIS say at 08:01 on 3 March" and get what live would have seen. Backfilled values are flagged. One field idea calls this history the most valuable asset QMX will own.
- Source: B089-B095, B112; `UP/architecture/MIS-PAGE-CONTENT.md` section 5. Simulated result: a label computed afterwards claimed a 76% better edge per trade; the honest at-entry label gave no gain (section 3 item 3).
- Touches: Library, QMB, trade row.
- Fate: outside this funnel.
- Read: **seat.**
- Standing: simulation on made-up bars, plus sound logic.

**9. Proving the MIS helps at all**
- What: run a unit with and without the MIS. Replay with readings stamped at entry against computed afterwards. Variants: feed it shuffled readings for a week on paper; trade the MIS's best word with a dumb entry. If nothing changes, the unit never used it. A per-unit "noise meter" labels "no proven help" when the gap can't be told from zero.
- Source: B061, B077, B096, B097; `UP/architecture/MIS-PAGE-CONTENT.md` group B ("measurement open"), section 5. His S-NOISE: "how is the MIS not adding more noise".
- Touches: QMB, Lab, workflow.
- Fate: outside this funnel.
- Read: **content** (needs idea 8 and the trade row).
- Standing: proposal, nothing run.

**10. MIS extras never shown to the funnel** (each **content** or Lab; all proposals, no evidence)

| Idea | What it is | Source |
|---|---|---|
| Finder job | For a unit whose rules already state its context, the MIS only answers "where else is this true now" | B023 |
| Stand-aside readings | "This market is in the state that hurts mean reverters today" | B031 |
| Inverse MIS | Publish states where every unit loses, so new logic gets built for them | B099 |
| Unit as sensor | A small fixed scalper in shadow on each market; its hit rate is a reading. Or the MIS reads which units win where | B103, B104 |
| Market twins | Test a proven unit first on the market whose readings track its own | B100 |
| Session measured, not assumed | "Is London actually active today", read from participation, so holidays fall out | B115 |
| State age, transition chance | How old this quiet spell is against usual; chance it changes next hour | B118, B119 |
| Lag-to-hold rule | A reading enters a tier only if it notices a change well inside the typical hold | B003, B057 |
| Sensor scout | An agent turns new articles and papers into reading cards and runs them in shadow | B037 |
| Teach the MIS | He or the copilot writes a dated note on a market; it becomes a human label and a shadow reading | B040, B080 |
| Market card, weather report, today's opens page, chart overlay | Ways to see the MIS | B072-B074, B078 (UI session) |
| Almanac and per-class inefficiency hunts | Studies of stamped logs sorted by hour of week, each row with a mechanism. His "discover market inefficiencies" | B021, B086, B098 |
| Bot crowding counts, dispersion, joint-state correlation, lead-lag | Cross-market readings. Only on his PC, none built | B044-B049, A3-186, A3-118, U-A3-23, U-A3-31 |

### B. SQS, spread and costs

**11. Two hourly tables per instrument: volatility and cost; refuse when missing**
- What: each instrument carries a table by hour and session: expected move for the planned hold, and round-trip cost in R (spread, commission, slippage, rejects). Measured from QMX's own quotes and fills, per venue, per demo or live. A missing cell refuses sizing, never zero. It replaces the old session multiplier. "Busy can mean deep, wide, fast, or all three."
- Source: X0-37 (= X1-H18); A3-039, A3-084, A3-017; NBER spread study via `research/R2-trader-practice-windows-drift-isolation-breadth.md:53`. Restructure R3 in `expansion/X0-trading-lens.md:859`.
- Touches: instrument record, sizer inputs, QMB cost ports, SQS, sniping windows. Fits his M51 line exactly: QMX as a data analyst that observes costs and acts, not removes them.
- Fate: **core**, part 5. One of the few that survived.
- Read: **seat.** The sizer has no cost input today and commission has no record key (G7 4.3).
- Standing: strong on the shape of costs by hour; every cell starts synthetic until fills exist.

**12. Cost windows found by data, then sniping as a counted slice**
- What: his sniping windows made honest. "Sniping" has no professional meaning (retail sniper entries, ICT kill zones; to professionals, latency arbitrage). The real thing: a time slice where one unit's net edge on one instrument is higher on later data. Windows lower cost or raise activity; they don't hand out edge. Agents nominate slices from the cost and activity tables, QMB proves each, every slice counts as a try, proven windows land in the Library as artifacts. Picking hours from a unit's own backtest is look-ahead.
- Source: his words, M7, M8, M10 (`seeds/SEEDS.md:669-674`), "Sniping is something I want to really focus on" (mis-field S-SNIPE); X0-47 = X5-H47; X7-H25 prospector; A3-033, U-A3-32; R2 section 1; `expansion/X0-trading-lens.md:783` gives three options (deterministic, agent, both).
- Touches: Lab, workflow, Library, QMB, trade row, cost table; a size lift is X0-19.
- Fate: later, "cost cell row". Go-live lens.
- Read: **seat** for what the trade row and cost cell must record; the windows are **content**, per instrument. His M50 belief that a week of copilot work could optimise this fits.
- Standing: strong on cost and activity (NBER, Bank of Canada). No study tests window sizing. A prop-firm guide: "The time window does not produce any edge". Old form: premium flag at 1.25 standard deviations above the session median, specified, never ran (A3-034). Note the research disagrees with his sense from social media about gold; that argument belongs to the numbers talk (`PARKED-FOR-NUMBERS-TALK.md:11`, `:28`).

**13. SQS as a sensor, not only a gate**
- What: SQS keeps blocking one instrument. Its state also feeds the class caution, the bad-market-or-bad-execution classifier, the cost lane and the restore gate (no probe while spreads are bad).
- Source: X3-H63; A2-111, A3-075; his "kill switch and SQS" (`seeds/SEEDS.md:515`).
- Touches: guard, MIS, brakes, restore path.
- Fate: X3-H63 core; DP25 keeps the sensor roles in shadow.
- Read: **seat.** The new node has no SQS at all and its baseline producer has no caller; the only code that deletes the old gate is C-20 (`grounding/G12-audit-and-repair-for-risk.md` section 2).
- Standing: built rule, never run on a venue.

**14. SQS K-of-N class caution**
- What: if SQS blocks several instruments of one class at once, the class stops new entries without waiting for any loss, and lifts when spreads recross. Catches a broker or liquidity provider pulling quotes while price doesn't move.
- Source: X3-H29; A2-121, A3-098 (liquidity moves together across FX, Mancini et al. via R2 section 3.3).
- Touches: guard scope keys, isolation.
- Fate: shadow, DP23. Go-live lens.
- Read: **content** once scope keys exist (idea 22).
- Standing: mechanism has evidence; this rule is a proposal.

**15. Spread gate against the instrument's own history, two windows**
- What: judge live spread against that instrument's own rolling histogram with two percentile lines, with no per-instrument tuning. The closest thing to a replacement for SQS's "baseline over live spread" ratio.
- Source: A3-070; A2-063; MQL5 author backtest (`linking/components/A3-structure-regimes-scenarios.yaml`). DP25 uses percentiles only to derive SQS's eight settings (`funnel/FUNNEL.md:208`).
- Touches: SQS rule, settings.
- Fate: folded as a derivation. Never considered as a redesign.
- Read: **seat** only as "the SQS rule is swappable"; the rule is **content**. On his canvas, the SQS itself should be a block a user can replace.
- Standing: author backtest.

**16. Five execution gates: can the market fill an order now?**
- What: before a scalper's entry, check spread expansion, tick velocity, quote gaps, micro-volatility and slippage stability. "The EA does not predict direction; it predicts whether the market can fill an order." Post-fill markout recorded at 1, 5 and 60 seconds. Noisy filters run as shadow labels first.
- Source: X0-18; A3-073, A3-079, A3-082.
- Touches: unit hook or guard; trade row (markout).
- Fate: shadow, DP25. Go-live lens.
- Read: **content** as a block; **seat** for markout on the trade row.
- Standing: author backtest. Chat 27 warns safety filters can also screen out winners (`research/R4-alphaxiv/chat-27-E-microstructure.md:130`).

**17. Cost nomogram: size shrinks before the SQS blocks**
- What: live cost against the unit's proven cost band. Inside the band no change; above a higher percentile a step down; above a higher one a bigger step and a feed check; past the hard block, no entry. The trade continues smaller in costly minutes.
- Source: X2-H42; A3-071 (NQ M1, 602 sessions), A3-076 (old microstructure multiplier).
- Touches: sizer, SQS.
- Fate: shadow, DP25.
- Read: **content** through the socket in idea 4. It conflicts with X3-H63's "never shrink" (section 3).
- Standing: author backtest. "Any cut looks good on a losing unit unless tested against a random cut."

**18. One execution-risk score, or a three-state liquidity word**
- What: depth against its time-of-day usual, a news flag and a calm, mixed or stressed word, fed to both the cost model and the brakes. "State first": the liquidity state before an event is the best predictor of the state after it.
- Source: A3-068, A3-069; `research/R6-alphaxiv-papers/T-03-macro-and-microstructure.md` combinations.
- Touches: MIS reading, cost model.
- Fate: part of X0-54 (shadow) and X2-H42.
- Read: **content.**
- Standing: author backtest, crypto futures; the single score is an idea.

**19. The fast MIS tier is SQS generalised**
- What: nearly everything a scalper needs is "now versus usual for this minute of the week": spread, tick rate, top-of-book depth, range, cost against target. SQS is one of these. Overnight the MIS prepares the usual curves; live only divides. Event-driven rather than polled.
- Source: B008, B053, B054, B085; `UP/architecture/MIS-PAGE-CONTENT.md` section 4; A3-181.
- Touches: MIS, node, SQS. This is the nearest thing to a new MIS-plus-SQS shape on disk.
- Fate: outside this funnel. SQS "in the MIS" was rejected in DP25 because the board fails open (`funnel/FUNNEL.md:210`).
- Read: **seat** for one baseline shared by SQS and MIS, or two will drift. Otherwise **other session** (MIS).
- Standing: proposal resting on research 05's "now versus usual".

**20. Venue rule: never call a quote a book**
- What: a flag per instrument says whether the feed is real orders or a dealer's price. Order-flow imbalance and queue position apply on futures, crypto and stocks. On spot FX and CFDs you read dealer skew after repeated same-side fills, last-look rejections and fills instead.
- Source: X0-38; A3-078, A3-080, A3-238; T-03 paper 6.
- Touches: instrument record, reading data level, QML blocks.
- Fate: core, part 5.
- Read: **seat.**
- Standing: strong on exchange books for explaining price; weak that any retail gate improves net returns.

**21. Broker and venue quality record; probing capacity**
- What: track slippage, spread, requotes and entry-against-exit slippage asymmetry per broker. Variant: briefly size up and keep the gain only if fills don't worsen. Costs and readings are calibrated per demo or live, never carried over.
- Source: A3-083, A3-082, X0-53; X0-12 (wild).
- Touches: node journal, cost table, accelerators.
- Fate: X0-53 core, X0-12 later.
- Read: **seat** for per-world calibration, **content** for the probe.
- Standing: demo measurements; the probe is an idea.

### C. Market isolation and the kill switch

**22. Scope keys: class, region, currency, underlying, session**
- What: every stop can name what it applies to, beside instrument and deployment. A Tokyo event switches off JPY, not the book. "It can isolate crypto" needs a crypto scope, and none exists today.
- Source: his C27 (`seeds/SEEDS.md:561`); X3-H35; A3-106, A3-029 (a gold CFD sits with gold, not equities); `expansion/X4-scenarios.md` Part 4 item 2.
- Touches: stand-down table, kill switch, instrument record, pods.
- Fate: **core**, part 9.
- Read: **seat.**
- Standing: design; the shipped shape has the hooks (G9).

**23. His isolation protocol: two tells, then a lifecycle**
- What: a class or region stops new entries only when two different kinds of evidence agree, such as spreads wide across many instruments plus a volatility jump. Mode is graded: no entries, reduce, flatten. Every isolation has an end: time to live, staged resume at part size, a retrip doubles the next wait. Each one records afterwards whether a loss followed, so its accuracy is known.
- Source: his words, C27, C28; X3-H28, X3-H33, X0-07, X4-94; exchange two-layer pattern (R2 section 3.1, A3-096); A3-107 to A3-109.
- Touches: guard, MIS board, BMS or pod settings, Lab scoring.
- Fate: shadow, DP23. He "must be told class isolation does not bind at go-live". Go-live lens.
- Read: **seat** for the scope, modes and record; thresholds are **content**. His M49 ruling reads as a pod question, so the rule should be pod configuration, not hard-wired. [judgment]
- Standing: exchange breakers are live practice. "No public source on a fund switching off one class by rule" (R2). Tells are daily-data author backtests with no intraday precision.

**24. Unknown is not calm**
- What: if prices are stale, a venue is down or a contract is rolling, that scope's state is "unknown" and new entries there stop. One bad feed stops only its scope. A closed market is never a zero-return day. Every brake declares how it fails.
- Source: X3-H36; A3-094, A3-115; A2-110.
- Touches: guard, board reads, every reading.
- Fate: **core**, part 9.
- Read: **seat.**
- Standing: design logic. It collides on purpose with the board's fail-open rule, solved by scope (section 3).

**25. "How does the MIS adjust?" (his direct question)**
- What: one plain answer exists: the board keeps publishing, the guard refuses, the router must not place into a stand-down. During an isolation, the board read fails closed for that scope only.
- Source: his C27; `funnel/REVIEW.md:186`; `architecture/SPINE.md:253`; X3-H36.
- Touches: MIS, guard, router.
- Fate: core wording.
- Read: **seat.**
- Standing: decision text, never run.

**26. Risk-off tells, fast and slow, no master score**
- What: fast: velocity ("too far, too fast"), volatility jump, spreads widening together, a safe-haven move, carry unwinding. Slow: financial turbulence, correlation surprise, absorption ratio. Each bucket alerts by itself.
- Source: X0-43; A3-088 to A3-101; R2 section 3.3 (Kritzman, Longin and Solnik, Mancini, Brunnermeier).
- Touches: MIS readings on his PC, isolation.
- Fate: shadow, DP23.
- Read: **content.**
- Standing: long-sample author backtests; never run as one stack.

**27. Agent isolation over days**
- What: weeks of slow decay can't trip a minute tell. An agent reads readings and journals and lands a card: "isolate class X for a week", evidence attached, with an expiry, de-risk only. Its calls get an accuracy record. His words: "analysis we've come up with over 20 days".
- Source: X3-H34 = X7-H21; A3-113; X4-13.
- Touches: agents' proposal door, stand-down table.
- Fate: X7-H21 shadow, X3-H34 later. Go-live lens.
- Read: **seat** for a door that takes expiring scoped de-risk cards; the workflow is **content**.
- Standing: proposal; applying without his click is his call.

**28. Budget follows what's open**
- What: when only one class is open, like crypto through the FX weekend, it doesn't inherit the whole book's day. A high weekend crypto reading raises Monday caution on indices and gold.
- Source: X3-H37 = X0-40; A3-114, A3-058; `expansion/X4-scenarios.md` Part 4 item 5. Paper: weekend crypto variance predicts Monday variance of the S&P, gold and Treasuries.
- Touches: BMS or pod budget, MIS reading.
- Fate: shadow. Go-live lens: "cTrader first".
- Read: **content** as a pod rule. It collides with crypto as the spine (idea 47).
- Standing: author backtest, short sample since October 2023.

**29. Smaller isolation forms** (all **content**; all proposals unless marked)

| Idea | What it is | Source | Fate |
|---|---|---|---|
| Region shift, no budget rotation | Block a region on its event, hold its budget back. The April version handed it to others and was killed in July | X3-H32, A3-110 | later or shadow |
| Peer ejection | A unit far below its peers is out for a growing time, with a cap on how many can be out | X3-H30, A3-104 (live in Envoy, not trading) | later |
| Immune brake | Add up weak danger signals, act at once on clear danger | A3-122, in an X3 hybrid (`expansion/X3-brakes-exits-drift.md:830`) | see that hybrid |
| Chorus | Abnormal losses clustering across a cohort | A3-111 (old rule, never ran), in an X3 hybrid (`:293`) | see that hybrid |
| Stack breaker | Fires upward, each level tagged with its context | A3-112, in an X3 hybrid (`:179`) | see that hybrid |
| Curvature, spectral detectors | Sectors merged into one; a null beside each reading; no lead time reported | A3-119, A3-121 | no hybrid found in X0 or X3 |
| Bulkhead | Compartments of open risk per unit and market | A3-105, X0-51 | later |

### D. News and events

**30. News as measured impact, with driver tags beyond currency**
- What: replace the calendar's colours with what each release actually does to each instrument. Each event carries tags: both FX legs, home exchange, region, commodity. US CPI blocks indices, gold and USD pairs, not just "USD". Fits his M51 example: on a news day the spread is insane, so don't trade that instrument, while others carry on.
- Source: his C28 (`seeds/SEEDS.md`); X0-39 = X3-H31 = X4-95; A3-130, A3-131, A3-229; R2 section 3.4; restructure R4 (`expansion/X0-trading-lens.md:860`).
- Touches: instrument record (tags), node windows, Library event file, pods.
- Fate: core first slice: both FX legs and calendar tier; measured impact "as the window learns". Go-live lens split it.
- Read: **seat** for tags and a window record; measurements are **content.**
- Standing: strong on old price-discovery work, author backtests on E-mini; first tags are defaults. X4-18's warning: colour windows on medium news swallow the day.

**31. News windows belong to the customisable layer, kill switch keeps the hard kill**
- What: he says the kill switch has "earned its spot" and news is its job; he also said portfolio-stop escalation is "a pod question" (M49). The funnel's split: kill levels stay, news is a window that blocks entries only, a stale calendar fails closed.
- Source: `seeds/SEEDS.md:515`, C28; `funnel/FUNNEL.md:66`, DP24; M49; A3-125, A3-126, A3-127.
- Touches: kill table, windows, pods.
- Fate: core.
- Read: **seat.** Which scope is hard-coded and which is pod-set was never decided. The spine treats these as fixed, which is what he objected to.
- Standing: rulings plus design.

**32. Event policy details**
- What: policy by event type: flat through, cool down, never widen a stop. Re-enter on spreads, depth and fills, not on the clock; "exchange resumed" isn't a signal. Don't suspend stops during news. Liquidity withdraws before the release, so the before-window is about execution, not direction. A velocity tell backstops the release the calendar missed.
- Source: A3-228, A3-141, A3-136, A3-067, A3-133; X4-15, 16, 19, 20, 21.
- Touches: node windows, block library.
- Fate: mostly core as tests.
- Read: **content**, with the "exits never blocked" contract as a seat.
- Standing: E-mini study (37,029 windows, author backtest); demo test on stops; rest ideas.

**33. News as something to trade**
- What: he said "which means I can trade news" (S-NEWS). The MIS offers news units context on an event clock: surprise size, reaction, spread recovery. Seeds: calibrated firm news sentiment after publication, macro surprise, news-attributed jumps, macro probabilities for crypto volatility.
- Source: B010, B108, QO11; U-A3-16 to U-A3-20; news-day negative in U-A3-13.
- Touches: event clock on readings, unit `reads`, news agent output.
- Fate: not judged as a mechanism; unit bank only.
- Read: **seat** for event time as a clock and a per-unit exemption from a news window; units are **content**. Conflicts with a global news window.
- Standing: MFAST long-short Sharpe 2.85 at 5 bp, author backtest, daily horizon single stocks. Free feed has no actuals, so no surprise reading today (R2 section 3.4).

**34. News agents with limits**
- What: a news agent emits a typed, expiring, de-risk-only event record. Provenance and corroboration before anything counts; a cap on one item's effect. Act only after news is public. Three bounded agents (macro, microstructure, news) feed one deterministic service. A macro event agent pairs a researcher with a verifier. Also: the feed may be fake or injected (X4-58).
- Source: A3-137, A3-138, A3-139, A3-142, A3-145; `research/R4-alphaxiv/chat-28-F-agents-macro-micro-news.md`; X7-H48 (agents maintain the event map).
- Touches: agents, proposal door.
- Fate: later.
- Read: **other session** (agent department), with the same door as idea 27.
- Standing: controlled test for macro forecasting skill, simulation for provenance.

**35. Testable news rules**
- What: a versioned file of past events so rules can be replayed, and a collision rate per unit that says how much of its day the windows take. Blocked hours reported as a cost.
- Source: A3-135, A3-134, A3-132.
- Touches: Library kind, QMB, observability.
- Fate: part of X0-39.
- Read: **content.**
- Standing: author backtest, simulation.

### E. Sessions, opens and windows

**36. Session, open and fix minutes as caution windows with measured widths**
- What: he raised it: session opens need a caution window (`seeds/SEEDS.md:677`). Per instrument, a window after each open, handover and fix. Scalper entries blocked, ORB allowed by design, exits never blocked. The width is measured in event time: minutes until spreads and activity return to usual.
- Source: X0-30; A3-035, A3-036, A3-229; old 25-minute warm-up, specified, never ran; `expansion/X0-trading-lens.md:830` has three options.
- Touches: calendar states, unit `sessions`, guard.
- Fate: later. Go-live lens.
- Read: **seat** for a window object any unit can declare and pass or refuse; widths are **content**. The compiler refuses `sessions` today (`compiler.py:904`).
- Standing: fix behaviour strong. "No generation derived a caution-window width" (`X0` gap 5). Collides with a fix-reversal unit.

**37. Day boundary, rollover, weekend, holidays, DST as contracts**
- What: the day is a declared thing that survives restarts. Crypto has none, so three options: UTC midnight, rolling 24 hours, or the funding cycle. Flat by a deadline set before the real close. Daylight-saving and holiday calendars feed every baseline, with a "baseline unreliable" flag around a shift.
- Source: X0-27; `expansion/X0-trading-lens.md:797`; B065; X4-22, 25, 26, 27, 28, 29. Only forex has a calendar today (G7 section 3); C-03 plans others.
- Touches: unit, node clock, counters.
- Fate: core.
- Read: **seat.**
- Standing: design, and facts of markets.

**38. ORB as a family across opens**
- What: one ORB logic trades each open it's placed on, proven as one family while each open earns its own record, sized as one sleeve. He called the breadth idea "brilliant" (`seeds/operator-words-2026-11-01.md:100`). Correlated opens on a risk-off day count as one event.
- Source: X0-25; A3-032; U-A3-09; R2 line 61; three Concretum ORBs at low correlation.
- Touches: unit markets, family tag, sessions, brakes.
- Fate: later, "family tag". Go-live lens.
- Read: **seat** for family tag and per-open records; ORB itself is **content**.
- Standing: strongest on stocks in play (net Sharpe 2.81, one period, win rate under 30%). Thin on FX.

**39. In-play gate: RVOL, with tick rate on FX**
- What: only take a breakout when activity is unusual. On broker feeds, use quote updates per minute against that minute's usual, and never call it volume. On real-volume markets, a 20-day median by minute.
- Source: X0-21; A3-077, A3-074, U-A3-09; his D5.
- Touches: bars must carry volume and time of day, MIS, QML block.
- Fate: X0-21 later, "MIS flag". Go-live lens.
- Read: **seat** for bars carrying what's needed; the block is **content**. His "was RVOL catered for?" has a plain answer: a catalogue entry at `TIP/qml/catalogue-seed/wave-1/beyond-fx/relative-volume.json`, no block, no MIS reading.
- Standing: tick count tracks volume hourly (correlation 0.96 to 0.99, one vendor study, MIS page item 6). Old RVOL gate never built.

**40. Activity sessions for 24/7 markets**
- What: crypto's sessions come from its own cycles: stock hours, weekends, funding minutes, quarter-hour bursts.
- Source: A3-040, X0-21, X0-54, U-A3-05, QR16.
- Touches: calendar, MIS.
- Fate: later or shadow.
- Read: **content**, on the calendar seat.
- Standing: author backtests on Binance-style venues. Hyperliquid's own cycle is unmeasured (X0 gap 12).

### F. Market physics, regimes, macro

**41. Persistence readings at the timeframe the router needs**
- What: efficiency ratio, variance ratio, Hurst, change points tell mean-reverting from trending. Built on H1 per the pasted report; his router wants 1m and 5m. Must use mid prices with a bounce check; bid-ask bounce fakes mean reversion 10 to 130 times more often than designed. Hurst needs about 1,000 points.
- Source: A3-189, U-A3-29; MIS page section 3; `seeds/operator-words-2026-11-03.md:28-46`; `TIP/qml/src/qml/blocks/stdlib/`.
- Touches: MIS packs, QML blocks.
- Fate: X0-26 later.
- Read: **content** (settings), though the pack is a useful default.
- Standing: blocks tested; simulated lags; no placement evidence.

**42. Old physics as a quarry: Chaos, Ising, entropy, compression**
- What: "the MIS was originally from market physics repos" (S-PHYS). The old system blocked trades at Ising 1.0 or more. Field: retest Chaos and Ising on the new reading card instead of restoring or binning unseen. Also entropy and compression, always with a random null beside them.
- Source: B102, B123; A3-060, A3-188; `grounding/G3-old-system.md:81`; `UP/research/23-mis-organisation.md` section 6; M31 welcomes new physics.
- Touches: MIS reading shelf, Lab.
- Fate: not judged.
- Read: **content.**
- Standing: "Ising-type measures have no trading evidence found" (`UP/research/37-mis-academic.md:133`, via G7). One author shows matched historical shapes aren't predictive against a null. Nothing on disk offers new physics beyond this, which he invited.

**43. Regimes cut, they don't choose**
- What: regime models hand over probabilities known at the time, never hindsight labels, and may only cut gross exposure per class. Regimes that re-weight strategies lost in the same paper. Sticky jump model beat plain HMM on indices 1990-2023 with costs and delay. Cross-class links get retested on a schedule.
- Source: X0-42; A3-043 to A3-046, A3-049, A3-059; T-03; his "you are not going to put an HMM inside a scalper's MIS".
- Touches: class cap, Lab training slot, MIS day tier.
- Fate: later, "class cap row". Go-live lens.
- Read: **content** if class caps exist. A user might want to break the "cut only" rule; that's his canvas [judgment].
- Standing: author backtest, three index markets. Crypto has too little history.

**44. Macro as a slow governor beside a fast layer**
- What: a few named states per class, recomputed daily and at releases, set a multiplier on a class's budget. Fast layer every few minutes decides what's usable now. Options: shadow then cut-only, information only, or live on his click.
- Source: X0-06; A3-041, A3-042, A3-051, A3-057; `expansion/X0-trading-lens.md:824`.
- Touches: pods, agents, class caps.
- Fate: later.
- Read: **content**; a natural macro mini app. His "macro structure" department.
- Standing: idea, no walk-forward. Macro data are revised and lagged.

**45. Change detectors, each with one job**
- What: three detectors: confirm, update, warn early. Log-normal durations beat a constant hazard on order flow; an anti-flap rule. Any de-risking cooldown must beat a random brake firing as often. Regime age: taper new adds as a regime gets old; trades closed by that gate made money while the system lost.
- Source: A3-061 to A3-065; U-A3-08, U-A3-14; T-03 paper 2.
- Touches: QML blocks, brakes.
- Fate: partly picked by X3.
- Read: **content.**
- Standing: author backtests, in-sample for regime age; controlled test for the random brake.

### G. Micro structure and unit seeds

**46. Order-flow and intraday seeds** (all **content**; "the unit bank"; not judged by the funnel; he has said order flow is left out for now, `seeds/operator-words-2026-11-06.md:78`; nothing beyond `bar-range-pressure` shows up in the block or MIS search at the tip)

| Seed | One line | Needs | Evidence | Source |
|---|---|---|---|---|
| OFI, MLOFI | Signed queue changes explain the mid move, slope 1 / depth | L2 data; futures, crypto, not FX | R² about 65%; explains, not shown to forecast net | U-A3-01 |
| Short-lived impact | Recent book events predict about 10 seconds; veto passive fills | Event data | Author backtest | U-A3-02 |
| Maker reversal | Post when an imbalance signal is likely wrong | Speed QMX lacks | Live, one week, about break-even | U-A3-03 |
| 15-minute crypto reversal | After taker-driven moves | Maker fees | 1.3 bp gross, inside retail costs | U-A3-04 |
| Quarter-hour imbalance | Predicts 4 to 12 hours | Signed volume | Author backtest | U-A3-05 |
| CVD, tape, volume area | Order-flow features for a filter | Real volume | Large returns, drawdowns near half | U-A3-06 |
| Session order-flow labels | Follow in trending, fade in mean-reverting | M1 estimates | In-sample | U-A3-07 |
| Intraday momentum into the close | First half hour predicts last | Session calendars | Survives costs in the ETF study; sign varies | U-A3-10 |
| Fix reversal | Dollar up before fixes, down after | The account's real spread | Negative at full spread, 0.12 to 1.03 Sharpe at half | U-A3-11 |
| MNQ controls | RTH and London signals, held 60-75 minutes | 5m bars | Weak; 53+ variants tried | U-A3-12 |
| Do-not-build list | Asia expansion bars, news-day drift, gold 5m mean reversion | | Negative | U-A3-13 |
| Volatility-managed trend, carry; tick-size trend | Swing | Swap data, tick tier | Backtests, disputed | U-A3-21, 22, 24 |
| Roll dislocation, crisis re-entry | Avoid or trade forced rolls; staged re-entry | Contract data | Idea | U-A3-25, 26 |
| Liquidation throttle; OI unwind | Crypto cascade warning | Taker flow, OI | Seven cascades | U-A3-27, UB-11 |
| Implied over realised | Placement input | Options bridge | Backtest; "not a timing trigger" | U-A3-30 |

Also: the merged 78 seeds in `linking/UNIT-IDEA-BANK.md` and those in `linking/unit-ideas/A5-topup.md`, many naming an MIS reading or QML block they would need. I read their headings and MIS lines, not each one.

### H. Instrument layers

**47. Crypto as the 24/7 spine**
- What: the one class always open. Funding minutes as caution. Weekend volatility as a Monday input elsewhere. Spot before perps on a small account, since liquidation can beat the stop.
- Source: X0-54; A3-235, A3-058.
- Touches: pods, calendar, instrument record.
- Fate: shadow, "spine framing dropped". Go-live lens plus "cTrader first".
- Read: **content** (a crypto pod). He said himself he may not trade crypto at first (M50). The framing shouldn't be dropped from the canvas.
- Standing: three separate author backtests; wild as a whole.

**48. Energy and stocks as data overlays, not special formulas**
- What: same machine plus data: EIA Wednesday, gas Thursday, OPEC with a decision type, roll calendars, never hold to expiry; earnings, filings, halts, and a stop can't fill through a halt.
- Source: X0-55; `research/R8-gap-topup.md` gap 4; A3-143, A3-144; X4-78, 79, 81, 89.
- Touches: event calendar, roll rows, instrument record.
- Fate: later.
- Read: **content**, on the calendar and record seats.
- Standing: exchange facts. No energy scalping or sizing evidence at all (X0 gap 1).

**49. Limits by tick-size tier and holding horizon, not by class**
- What: a contract's tick size relative to its volatility tells you about its behaviour better than its label. Fast trend on small-tick futures decayed most after 2008.
- Source: X0-36; A3-236; U-A3-22.
- Touches: instrument record field.
- Fate: later.
- Read: **content** with a record field. This is the closest thing on disk to his mini-versus-micro thought, and it's still not that (Gaps).
- Standing: author backtest on 100 futures.

**50. Factor buckets, grouping by underlying**
- What: every instrument gets a bucket code and a residual bucket for the unclassified. An index future and an ETF on that index draw on one budget. Gold at two brokers and GC share `gold` (`UP/` `market_id`). Reading the futures for a gold CFD is backed: COMEX leads with about a tenth of London's volume.
- Source: X0-41; A3-029, A3-048; `UP/research/23-mis-organisation.md` short answer 3; B014, P4-b.
- Touches: record, bet key, MIS borrowed feed.
- Fate: later; bet key core.
- Read: **seat** for underlying and bucket on the record.
- Standing: SIMM practice in its own field; draft list. Not tested in QMX. Two bucket lists collide (X0 collision 13).

**51. Which classes can be traded at this budget**
- What: before a class trades live, compare its smallest position with costs against the unit's share. Verdict tradable, simulate only or wait, re-derived per broker and as money grows. "At $500, costs and minimum lot sizes choose the markets before the MIS does." It connects to his M51 "best basket" talk.
- Source: X0-45; A3-013, A3-002; contract ladder "Deferred" in `architecture/candidate-1/SPINE.md:337`.
- Touches: start-up check, instrument record, sizer.
- Fate: core.
- Read: **seat** as a computed, shown verdict; the rule that refuses is **content**, since his lens says these things aren't set in stone. Numbers talk.
- Standing: arithmetic, snippet for EU caps.

**52. Style as a dial (holding horizon), dropped by the funnel**
- What: instead of three named types, a unit carries a holding horizon, and cost in R, brake windows, gap allowance derive from it. Catches a unit drifting from 5 minutes to 5 hours.
- Source: X0-49; A3-236. `funnel/HYBRID-FATES.md`: dropped, field kept.
- Touches: template, measured field.
- Fate: dropped. Reason recorded: one template per type. Not simulation.
- Read: **content** as an optional derivation; the measured field stays a **seat**. His M50 "a scalper is handled differently from intraday" is compatible with presets on top.
- Standing: wild; one dial can't tell breakout from mean reversion.

**53. Style by class matrix**
- What: 3 styles by 7 classes. Each cell answers risk unit, stop, brakes, costs, accelerators. Filled table at `expansion/X0-trading-lens.md:735-743`. Examples: micro gold is coarse at small size, energy scalping generally not feasible, crypto taker fees bind.
- Source: X0-44, X0 section 2.8; R5 restructure.
- Touches: template, override chain.
- Fate: X0-44 core, part 2: presets over cells, four keys at go-live, seven reserved.
- Read: **seat** for the chain; the table's content is **content**, and is the most useful starter sheet for the copilot and him. Belongs also to the template harvest.
- Standing: evidence varies by cell.

### I. Scenarios

**54. The scenario harness and scenarios as data**
- What: a scenario is a record in the Library, not prose. Every template version runs against all of them, nightly. A scorecard per version, plus "the scenario that breaks us". 99 entries in `expansion/X4-scenarios.md`, 13 families, including 8 "two at once" cases such as a release while the feed is stale.
- Source: X4-90, 96, 97, 98; Part 4 item 7. The engine doesn't exist: "no sizing-only or brake-path replay" (Part 5 item 11).
- Touches: QMB, Library, workflow, Lab; any user's unit.
- Fate: the harness core in a light form (X4-90, 96, 97); reverse stress later. Scenarios overall 60 core, 21 shadow, 18 later, by whether a first-live unit could meet it. Go-live lens.
- Read: **seat** for the replay path and scenario kind; each scenario is **content**. Scenario lists per mini app fit his canvas. He mentioned scenario-driven thinking in M52 and then doubted it, so don't oversell.
- Standing: design. Likelihoods are guesses (X4 P8). CME SPAN and Khandani-Lo give background (R8 gap 3).

**55. Market scenarios worth reading whatever their fate** (each **content**)

| Family | Scenarios | What they teach | Fate pattern |
|---|---|---|---|
| Class or region bad | X4-08 to 14 | False isolation; resume is where people get hurt; everything bad at once | shadow; 14 core |
| News | X4-15 to 21 | Missed release; hourly medium news; spreads wide for days; a unit's own exit before the print | mixed |
| Sessions and 24/7 | X4-22 to 30 | Handover hour; opposite directions on one pair; crypto carrying the weekend; rollover minute; DST; day-boundary exploit | mostly core |
| Structure shocks | X4-31 to 37 | Flash crash and back; spreads widen everywhere with no news; halt; limit move; broker failure; liquidity hole; aftershock | core, 33 and 34 later |
| Instrument-specific | X4-78 to 81, 89 | Roll gap; EIA; liquidation cascade; earnings | later |
| Crowding | X4-03, 64, 65, 99 | Same signal across many units; August 2007-style unwind; interactive bench among QMX's own units | 03 core; the rest later |

Missing from the catalogue: co-move duration per driver; mark-against-last as a stand-down; the roll-and-report join (X4 Part 5 items 1, 5, 8).

**56. Stress generators** (**content**, Lab)
- What: per-class stress paths with trigger, spread and exit; contagion as a time-indexed graph; reverse stress in a plausible region; supply or demand oil shock as a selector; Tail-GAN.
- Source: A3-051, A3-230 to A3-234; R8 gap 3.
- Fate: mostly later.
- Standing: author backtests; ideas.

## 3. Designs and overhauls already proposed for this area

Options listed by what each buys. "Shown" notes whether I found any record of him seeing it; absence means I found none, not proof.

**How to organise the MIS** (`UP/research/23-mis-organisation.md` section 2): by style (his first thought; duplicates readings), clock tier, data level, class (cross-class readings get no home), venue, underlying (only this and H handle a gold CFD reading the futures), family (a code shelf), or **H: tier and data level as labels, class as a pack** (the plan's choice; thin packs can look covered unless empty rows show).

**The poles for the MIS** (mis-field, never shown as a choice):
- One MIS with fast and slow tiers (the plan). Buys one vocabulary.
- B106: slow only (session and day); all fast readings live in units. Buys simplicity; conflicts with his "multiple indicators inside a scalper's MIS".
- B105: no central MIS, just shared sensor code and an almanac. Buys independence; loses every cross-market reading.
- B107: only cross-sectional readings. Buys what a single unit can't compute.
- B126: decide per reading by August's rule (shared, expensive, market state, same in test and live). Makes the poles a setting.
- QF01: several products (board, stream, almanac) under one vocabulary.

**How routing reaches a unit** (`UP/research/14-design-idea-studies.md` section 2):
- A: central advice board; units pull. Simplest, and the seed of what got built.
- B: slow planner kept, gate turned into a lookup that never blocks.
- C: client-side balancing; each unit chooses from a shared feed.
- He found the router machinery over-built on 28 Oct (mis-field section 5). Load-balancer ideas are parked.
- Separately, how units take labels: (a) never; (b) optional with fallback, tested both ways; (c') compute where you are; (c) freely. Same code two places buys "router down" safety.
- Router ranks or only narrows: X0-46 against A3-184. **Not settled. His own seed says the unit widens.**

**Where SQS sits** (`funnel/FUNNEL.md:207-212`; all three candidates chose (a)):
- (a) inside the guard, baseline producer and eight settings derived from spread percentiles. Buys a hard gate on the order path.
- (b) one line in `Runtime.guard`. Same gate, undersized.
- (c) inside the MIS. Rejected because the board fails open.
- Not on that list: B008 and MIS page's "spread against usual and a spread quality score" have the MIS publish it too. So two owners are possible; G12 and the plan don't line up (`review-2026-11-07/system-map.md:116`).

**What SQS does:**
- Block only, never shrink (X3-H63, the old rule). Buys a clear fact and no hidden size change.
- Graded shrink then block (X2-H42, A3-071). Buys trades in costly minutes at lower size.
- Replace ratio with percentile gate (A3-070); or five gates (A3-073); or one score (A3-069). No one compared them.
- `spread_state@v1` in MIS packs today uses fixed multiples. A third spread measure beside SQS and the guard's cost target. [my reading]

**Old session multiplier against two hourly tables against reading words** (X0 R3, X0-48): multiplier is simple and never ran; tables are measured but start synthetic; words need a live MIS.

**News:**
- Kill level table from the old system (A3-125): scope by currency, fail-safe up.
- News window on the node (DP24, picked).
- News as data with measured impact (X0 R4).
- News as context for news units (B108): unresolved against a global window (QO11).

**Isolation:**
- Kill switch alone: all or nothing.
- One protocol in shadow (DP23, picked).
- Agent-only slow isolation by card.
- Whether a confirmed isolation applies without his click is open. Mode: no entries, reduce, flatten.
- Scale budget with breadth (X0-40) against crypto as spine (X0-54): first protects, second earns (X0 collision 11).

**Fail open or closed:** the board fails open ("optional to every unit", A3-182). X3-H36 fails closed for one scope during an isolation. They're compatible only if an isolation is a stand-down and not just a word on the board. SPINE line 253 shows them "together on the preflight".

**Cost reaching the sizer** (`expansion/X0-trading-lens.md:811`): (a) table on the record, sizer contract gains an input; (b) guard multiplier after the sizer, which hides it from the receipt; (c) compile the cost in, which goes stale.

**Book-level restructures touching this area:** X0 R1 to R6, `expansion/X4-scenarios.md` Part 4 items 2, 5, 7. Only scope keys and the cost table reached the core.

## 4. What the unit baseline must carry because of this area

| Needs | Why | What breaks if missing |
|---|---|---|
| `reads` that compile, with fallback and stale limit; `context_needs` | Router, contexts, physics, news, windows | Today the compiler refuses. No MIS idea can reach a unit except by embedding its own block |
| `sessions` and window objects that compile, with per-unit pass or refuse | ORB allowed where a scalper is blocked; caution windows; his session change question | Same refusal (`compiler.py:904`). Every unit gets one rule for opens |
| Two sets of markets: allowed and active now, plus a door to change active by reading | His router | Widening is a new version each time; the router can only narrow |
| Cost input to the sizer, per instrument, hour, session, venue, demo or live; commission key; refusal when absent | His "costs feed Kelly", M51 | Sizer blind to cost; scalper sized wrong in costly hours; a news-day spread reaches only the gate |
| A named size-modifier socket with range and reason on the receipt | SQS, MIS, microstructure as reasons to reduce (C-series) | Back to hidden multipliers, or to none |
| SQS as a swappable block, one shared baseline, per world | "Nothing set in stone"; repair C-20 removes the old gate | New node has no SQS. Three spread measures drift apart. First live entry waits hours for a live baseline (`SPINE:475`) |
| Entry hook and exit bypass: market gates act on entries only | Exits never blocked | A window blocks an exit, the one thing everyone ruled out |
| Scope keys on every stand-down, kill and brake; `unknown` as a state; a declared fail mode per input | Isolation, news | All-or-nothing only. A stale feed reads as calm |
| Instrument record: book-or-quote flag, underlying, bucket, driver tags, tick tier, activity calendar, event calendar reference, roll fields, commission | Venue rule, news tags, futures, crypto | Order-flow logic on a CFD; US CPI blocks only "USD" |
| Trade row: session, time slice, hour cost cell, gross and net, split costs, readings seen at entry with age and source, markout, exit kind | Sniping windows, MIS lift, cost table | Windows can't be found or proved; MIS never proven; cut can't be told from a time exit |
| Records split by session and timeframe as well as market | Windows, ORB per open. Plan splits per market only (G7 5.3) | "A sniping window gets more money because the record shows" has no record |
| Family tag and same-bet key | ORB family, overlaps, crowding | Five opens count as five bets |
| Reading record open to other publishers (`source` beyond `node` and `mis`) with versions and shadow | Mini apps and departments, agents, Lab models | A futures mini app can't feed anything except by being called the MIS |
| Bars with volume and time of day; tick and volume clocks; event time as a clock | RVOL, volume-clock regimes, news units | RVOL stays blocked (A3-077) |
| Stamped history and an as-of question shared by QMB and live | Honest tests | A backtest flatters the MIS by a large margin in simulation |
| A proposal door taking typed, expiring, scoped de-risk cards with evidence | Agent isolation, news agents, 200 units | He monitors by hand, which he rejected in M49 |
| Pod-level settings for news scope, isolation rules, class caps, which gates bind | M49: "it's a pod question" | Rigid rules, his main complaint |
| Replay path that runs brakes and gates, and a scenario kind | Harness | Scenarios stay prose. "No sizing-only or brake-path replay exists" |

Multi-leg or basket orders: no shape exists (G7 5.2). Pairs and stat-arb seeds need it. I flag it, and no source says the baseline must carry it. [judgment]

## 5. Gaps: what he asked for that nothing on disk answers

1. **"designs for the SQS systems, MIS systems, newer designs or enhancements."** No new SQS design; no MIS design drawn from the papers. See the top of this file.
2. **"futures trading at a mini and at a micro are two different things ... I do believe seriously, there are inefficiencies that can be exploited across."** (M50) Nothing on disk studies this. Mini and micro appear only as cost facts (MNQ's 2-point cost, micro gold being coarse). Nearest neighbours: tick-size tiers (idea 49), one underlying with two ladders (idea 50). No block, reading, or paper looks at gaps between contract sizes of one underlying.
3. **"Every instrument has a lot of ideas around it. You're also not looking at that angle."** (M50) No per-instrument study exists. Per-class yes, in X0 2.8. Gold has fix windows and one mean-reversion negative; nothing on what he calls gold's "good sniping windows".
4. **"opening range breakouts and futures trading"; "Fabio Valentini"; human scalpers.** (M50) No study of the named trader or of how humans read order flow. Futures have no route in this build (G7 4.1). Parked for the numbers talk, and the file records it.
5. **"How do we classify and how do we find a sniping window?"** (M8) Has a method (idea 12), never run on any data. He also asked to look up how forex traders define it (M10, `seeds/SEEDS.md:674`): R2 did. Result: retail jargon. He may not accept that summary; no trader-method catalogue beyond it exists.
6. **"And ORB, I'm not certain, okay, if that's the sniping period or not."** (M8) Still unanswered (`seeds/SEEDS.md:1386`). Reading from X0-30: ORB is what's allowed inside a caution window, so a different thing; nobody told him.
7. **"How do we change sessions?"** (M8) Answered only as a design stance (idea 3). Never walked through for a Tokyo-to-London handover with live units, except scenario X4-22.
8. **"how does the MIS adjust?"** (C27) Has one line (idea 25). Never drawn.
9. **Market physics: "I actually never understood how we are integrating market physics."** (M7) Factual answer exists (idea 41). No answer on new physics, though M31 invited it. Only a quarry note (idea 42).
10. **Pods for this area.** "I remember asking you to see if you could figure out some pod ideas or configurations." (M49) No file gives a pod configuration for news, isolation or a class. Pods appear in this area's files only as hedge fund analogy and cap talk.
11. **Mini apps for this area.** The futures mini app, FX mini app, macro and micro departments (M50) exist as seeds in `handoff/AGENT-DEPARTMENT-SEEDS.md`. No design of inputs and outputs between them.
12. **"I told you to look at the UI by looking at the UI itself."** (M49) Nothing in this area's files came from the running UI. I didn't check it either, as the brief doesn't ask.
13. Facts nobody settled: Hyperliquid activity cycle; jurisdiction for leverage caps; whether his cTrader spread sits near half the quoted spread, which decides the fix reversal (`research/R2-trader-practice-windows-drift-isolation-breadth.md:63`).
