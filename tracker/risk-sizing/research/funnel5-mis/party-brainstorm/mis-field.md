# The MIS field: ideas, options and questions

Written 2026-10-30 by the MIS expansion agent, from a party-mode run (`party-transcript.md`) and a headless brainstorm (`.memlog.md`, `brainstorm-intent.md`, `brainstorm.html`) in this folder. **This is a field, not a design.** Nothing here is chosen. Contradictions are kept. Questions that research 22, 23 and 37 would settle are tagged `research`.

## 0. How to read this

- **Ids.** `B001` to `B127` come from the brainstorm memlog. `P1-a` to `P11-b` come from the party (round tags in `party-transcript.md`). `QR`, `QO`, `QL`, `QF` are questions tagged `research`, `operator`, `lead` and `fog`.
- **Origin.** Each idea is marked `seed <name>` (an expansion of a named seed in §1) or `new` (not found in his words or the findings read for this run). "Extends R15 idea n" names the earlier idea it grows from, so nothing is counted twice.
- **Labels.** Everything in §2 to §6 is INFERRED (ideas and questions, not facts) unless it names a file and section. File and section citations are CHECKED: this agent read each cited section this session.
- **Quotes.** His words appear only verbatim, tagged `(T1:n)` or `(T2:n)`. `T1` = `operator/transcript-2026-10-20-to-28.md`, `T2` = `operator/transcript-2026-10-29-to-30.md`, `n` = the line holding the whole turn. Every tagged quote in this file and in `party-transcript.md` was checked by script against its line (90 quotes, 0 misses; the checker is the agent's scratch `quotecheck_files.py`, a plain substring test per line). CHECKED.
- **Counts.** 139 ideas (77 seed-expanded, 62 new): 127 from the brainstorm (B001 to B127, 22 techniques) and 12 from the party (11 rounds, 13 voices). 56 questions: research 20, operator 11, lead 17, fog 8. 8 questions dropped as "any trader knows". 29 cross-map rows, 11 party clashes kept open, 12 parked items.
- **Skills.** Party mode ran in session mode with an explicit non-interactive close (activation: `resolve_customization.py` gave `party_mode = session`; `resolve_party.py` returned no installed agents, so the brief's inline cast was the roster). Brainstorming ran headless; techniques came from `brain.py list --all`. Both memlogs were written with `memlog.py`. Two deviations, both forced by this run's rules: the party's room memory lives at `party-memory/.memlog.md` here instead of the skill's default folder (outside the write scope), and the brainstorm's `brainstorm.html` and `brainstorm-intent.md` were written by this agent from the log, not by a subagent (sub-agents are not allowed).

## 1. The seeds: his words

Each seed has a short name used in §2. These are his words, not rulings. `STATE.md` records two of them as seeds in its own words ("shaped by trading style, then timeframe, then the data a market offers" and "QMX agents as analysts"); none is a ruling.

| Seed | His words |
| --- | --- |
| S-READS | "What I wanted was the MIS just reads and outputs. Then the units, or previously the bots, pick the output and they propose whether to use it or not. That's the simplest design I had." (T1:1951) |
| S-DOMAIN | "What I want the MIS to do is understand what the market is going in." (T1:1903) "So the MIS is playing the role of just expanding the domain." (T1:1903) |
| S-CONTEXT | "There is a very big part that we always need, which is called the market context. Any strategy always needs it." (T1:1951) "when you are looking at a chart, a market chart, you have to have market context. In other words, price action and technical analysis." (T2:789) "Logic is inside a unit. Context is what the market, I believe, should be using, or that should be producing." (T2:789) |
| S-ORDER | "We can research firstly the trading style, then trading style with the timeframes." (T2:219) "So it means the MIS for a market that has all that data is different." (T2:219) "So in other words, a Forex one is different from a futures one, but the time frame or the time frames are the same." (T2:219) |
| S-CLASS | "I think the MIS should be able to categorize by, of course, organization is important." (T1:1999) "I don't think future is going to use the same analysis system, market analysis or market intelligence as a currency." (T1:1999) "doesn't this mean that the context sensing is different for each?" (T1:1999) "we can design an MIS that fits, should I say, a futures market, then an MIS that also fits a Forex market." (T2:135) |
| S-SCALP | "Because you are not going to put an HMM inside a scalper's MIS. That makes no sense. But you can put multiple indicators inside a scalper's MIS." (T2:219) "The MIS for a scalper should be from the research. We shouldn't assume that the HMM will work." (T2:219) |
| S-HMM-TF | "doesn't it mean that we are going to be training an HMM model at a 1 minute time frame and at a 5 minute time frame" (T2:135) |
| S-HMMCFG | "An HMM can work best in crypto, but you discover that, according to academic research, that an HMM with a specific configuration can work best in BT." (T2:219) |
| S-SENSOR | "it means that the MIS can be upgraded as the agent see fit, obviously with my approval, yeah, or with the user's approval, not mine alone, the user of QMX's approval." (T1:1951) |
| S-LIMBS | "some of the capabilities that KMX is meant to have is to grow its own limbs" (T2:135) |
| S-QUALITY | "the quality of what's processing information inside the MIS is directly proportional to the quality of output" (T2:219) |
| S-AGENT | "Agents can look at price action for the day, market, whatever, price action for the day. They can use the TA, they can use the MIS logs and the MIS itself." (T2:325) "All they are trying to do is literally replicating the MIS's thing." (T2:325) |
| S-COPILOT | "based off the information me and the copilot have been looking at this entire week, we do see that these markets, not just historically, we've seen and confirmed that these markets are mostly mean reverting." (T2:219) "we can retrain a version of the MIS that can also see such." (T2:219) |
| S-TWO-SPEED | "The MIS gives us low label per session or per day" (T2:325) |
| S-S1S2 | "So system one is trading based off market context and conditions. System two is trading based off market context and conditions plus specific instruments." (T1:1951) "system one and system two were never any definition under QMX." (T2:789) "a system one produces a system two variant. There is no rush to trade." (T2:219) |
| S-CORR | "If they are, if it's the same strategy, or rather the same unit trading the same pair on different time frames, that's just correlation." (T2:1001) |
| S-LEDGER | "Maybe the correlation ledger can take the output also, all right?" (T2:219) |
| S-CENTRAL | "Things like now that new skill switch, all that stuff can be centralized, okay? Then also the MIS." (T2:219) (INFERRED: "new skill switch" is the dictation of "news kill switch", as the guard list in STATE and his own wording in the T1:444 turn suggest.) |
| S-REPEAT | "what if a strategy is using an indicator that also the MIS is using? Is that repetition?" (T2:219) "if it's using the same things as in those in the MIS, it means it is already specific." (T2:219) |
| S-LIVE | "the bot itself also didn't like taking only information from the MIS. No, it took in also live market data." (T1:444) "the unit itself accesses both market and MIS, but how?" (T1:1574) |
| S-CLUSTER | "it should take in information from, let's say now, an MIS cluster." (T2:135) |
| S-STAND | "It doesn't mean that if the MIS is not working, it doesn't mean that these bots won't trade. They will, okay?" (T2:135) "Neither does it switch on, nor does it switch off." (T1:1574) |
| S-NOISE | "So how is the MIS not adding more noise to an already noisy market?" (T1:264) |
| S-AMP | "its edge can be amplified by these other things. So in other words, it can be amplified by the MIS." (T2:135) |
| S-PHYS | "In fact, the MIS was originally from market physics repos." (T1:264) |
| S-FUND | "which means we can also add fundamentals." (T1:376) |
| S-NEWS | "which means I can trade news." (T1:2051) |
| S-SNIPE | "Sniping is something I want to really focus on" (T1:442) |
| S-INEFF | "there is a huge possibility we can discover market inefficiencies with only that" (T1:1999) "We are changing it to look at the MIS suitability in a way, shape or form." (T1:2051) |
| S-FEED | "there is something that looks exact or does exactly what this MIS thing is meant to be doing" (T1:1177), said of social-media feed algorithms. |
| S-DATA | "Actually, most of this is just data organization, to be honest." (T1:442) |

**Seeds from the findings** (each CHECKED at the cited place this session):

| Seed | What it says | Where |
| --- | --- | --- |
| F-R05 | No detector beats the information limit; at 1m a volatility doubling shows in about 12 minutes, a strong new trend in about 8 hours; most of a scalper MIS is "now versus usual for this time of day". | `research/05-academic.md` short answers 1 to 3, §1.3 |
| F-R09 | Two speeds: slow planning ahead of time, cheap live checks; nothing heavy in the hot path. | `research/09-router-architecture.md` §0, §5 |
| F-R16 | Labels need a timestamp and a version, or history rewrites itself; the scalper MIS is mostly not about direction. | `research/16-fable-advice-system1-context.md` §7 points 1 and 6 |
| F-R18 | Today's MIS: six rule labelers, a fitted liquidity-stress model, a regime pipeline with no ratified model, a shadow lane; read only by the Book door and the KSA, never by bots; never run on a live feed. | `research/18-grounding-today.md` §4 |
| F-R19-SENT | The old sentinel ran Chaos + Ising + News with HMM as shadow; its ensemble was never wired live; one sentinel served every style. | `research/19-grounding-old-system.md` §2 |
| F-R19-IA | The Intent Aggregator: a 50 ms per-symbol window across bots with opposite-direction, per-symbol-cap and correlation rules. | `research/19-grounding-old-system.md` §2 |
| F-R19-CAP | `capability_spec` declared the market conditions a bot was built for; compatibility rules with BLOCK, WARN, REQUIRE. | `research/19-grounding-old-system.md` §3 |
| F-R39-RULE | August rule: a feature goes in the MIS when shared, expensive, market state, the same in exam and live, and worth versioning; otherwise it stays in the bot. | `research/39-gold-mine-session.md` §3 I3 |
| F-R39-SIM | Pair similarity as many dimensions, not one correlation number; a pair can sit in several clusters; the ledger stores dated measurements. | `research/39-gold-mine-session.md` §3 I4, I5 |
| F-R39-KNOW | Durable knowledge versus dated intelligence; he moved intelligence to QMX's UI and database. | `research/39-gold-mine-session.md` §3 I6 |

## 2. Ideas by theme

Each table keeps the id, the origin and the idea. Ideas are unranked and not chosen.

### 2.1 Style, timeframe and data class (17)

| Id | Origin | Idea |
| --- | --- | --- |
| B001 | seed S-ORDER | A reading card with three required headers: which style tier it serves (tick, bar, session, day), which clock its horizon runs on, and which data rung it needs. A reading missing any header is not published. |
| B002 | seed S-ORDER | Style tiers named by their alarm clock, not by trader type: every tick, every bar close, every session open, every day. A unit subscribes to tiers; an intraday unit can take the session tier and the bar tier together. |
| B003 | seed S-SCALP | Lag-to-hold ratio as the one admission number for a reading into a style tier (starting default: lag at most a third of the median hold; a number, editable). Extends R15 idea 44 from per unit to per tier. |
| B004 | seed S-ORDER | A data ladder, rungs 0 to 6 (calendar, OHLC bars, quote ticks, depth, trade tape, derivatives fields, outside data), as the way "the data a market offers" is stated, per instrument at a venue. |
| B005 | new | Rung downgrade path: each reading defined at its best rung also names its fallback at lower rungs (order-flow imbalance at rung 3, tick-rule imbalance at rung 2, range pressure at rung 1) and the expected loss of quality. |
| B006 | seed S-CORR | One measurement at the finest data available, summed up to every horizon (ticks to 1m to 5m to 1h). 1m and 5m share one source and are correlated by construction; no model per timeframe. |
| B007 | new | Three clocks a horizon may run on: wall clock, tick count, traded volume. The rung decides which clocks a market can offer (no volume clock without a tape). |
| B008 | seed S-SCALP | The scalper fast tier holds only "now versus usual for this minute of the week" ratios: spread, tick rate, top-of-book depth, realised range, cost against target. Generalises SQS; extends R05 tier T1 and R15 idea 33 into the whole scalper tier. |
| B009 | seed S-ORDER | Swing and position styles get a week tier: carry, swap or funding state, positioning where it exists, higher-timeframe structure. Styles the MIS has not been thought through for yet. |
| B010 | seed S-NEWS | A news or event style row whose clock is event time (minutes from the release), with readings such as surprise size, range since release and spread recovery time. |
| B011 | new | Sub-minute scalping left to the unit's own feed by default; the MIS supplies only the session and cost tiers for it. A setting, not a ban. |
| B012 | seed S-SNIPE | A sniping-window tier: readings that exist only inside named windows (London open, New York open, overlap, fixes), computed per window instance and compared with past instances of the same window. |
| B108 | seed S-NEWS | Reverse "news is only a danger": news becomes a context the MIS offers to news units (surprise, reaction size, recovery), while the global news kill switch still guards every other unit. |
| B115 | new | Session as measured, not assumed: "is London actually active today" read from participation, so holidays and half-days fall out (extends R15 idea 34). |
| B118 | new | A state-age reading: how long the current state has lasted against its usual run length ("this quiet spell is older than usual"); R15 idea 47 turned into a live reading. |
| B119 | new | Transition readings: the chance the state changes in the next hour, estimated from the history of the same hour, for units that want to step aside before a switch. |
| P1-b | new | "What the market is doing" split into three readings with three clocks: is it moving, is it moving my way, is it the time it usually moves. |

### 2.2 Per asset class: markets through their data (14)

| Id | Origin | Idea |
| --- | --- | --- |
| B013 | seed S-CLASS | FX row: rungs 0 to 3 at cTrader, no tape, tick volume as an activity proxy, and currency strength computed across all pairs at once, a cross-sectional reading only a shared MIS can make. |
| B014 | seed S-CLASS | Gold row: two ladders (XAUUSD CFD rungs 0 to 3, GC futures rungs 0 to 5); dollar and real rates as slow outside data; fix windows on the calendar rung; GC tape as a borrowed rung for the CFD. |
| B015 | seed S-CLASS | Index CFD row: price follows the cash index and the future; cash open and closing auction on the calendar rung; the future's tape as a borrowed rung is a research question. |
| B016 | seed S-CLASS | Index futures row: full tape; delta, absorption, volume profile, opening drive, overnight inventory; roll week on the calendar; regular and extended hours as two session regimes. |
| B017 | seed S-CLASS | Crypto spot row: per-venue volume, fragmented; listings, delistings and weekend thinness as calendar-like events; cross-venue price gaps as a reading. |
| B018 | seed S-CLASS | Perps row: funding, open-interest change, liquidations, basis to spot, mark versus last; funding hour on the calendar; crowding as a class-only dimension (extends R15 idea 30). |
| B019 | new | Commodity futures row (oil, gas, grains) kept as a visible empty row with its known events (inventory reports, roll, limit days), so the matrix shows the gap instead of hiding it. |
| B020 | seed S-LIMBS | A class pack as the unit of extension: one folder per asset class with its rung table, calendar, sensors and vocabulary extras. Adding indices means adding a pack (ties QML asset-class packs, QF B041-B060, to the MIS). |
| B021 | seed S-INEFF | Per-class inefficiency hunts run as studies of stamped MIS logs: sort readings by hour of week and distance to events, look for repeatable shapes, write each as an almanac row with a mechanism line (extends R15 ideas 59-60). |
| B022 | seed S-HMMCFG | Per-instrument sensor settings ("three states on BTC, two on ETH") kept as profiles on the sensor, seeded from papers as priors and refit on own data. |
| B116 | new | Cost per venue: the same market's cost reading differs per broker, so the MIS publishes cost per venue and each unit sees its own terrain cost in context. |
| P4-b | new | A borrowed rung is the MIS's dependency, never the unit's: if the second feed dies, the reading goes stale and the unit trades without it. |
| P5-b | seed S-CLASS | "Separate engines, one speedometer": per-class sensor sets behind one shared set of output words. |
| P5-c | new | A same-meaning test: a shared word ("busy", "crowded") must be checked to mean the same thing in every class before a unit may match on it across classes. |

### 2.3 What a unit reads and what the MIS publishes (14)

| Id | Origin | Idea |
| --- | --- | --- |
| B023 | seed S-REPEAT | The finder job: for a unit whose rules already state its context, the MIS only answers "where else is this true now". It never re-filters that unit's own condition. |
| B024 | seed S-READS | Publish three forms of every reading: the raw number, its percentile against the usual for this instrument and hour, and a word. Units bind numbers; people read words. |
| B025 | seed S-CLUSTER | Output as a board: markets grouped into co-moving clusters, with each market's readings, so a unit takes one per cluster by its own rule (extends R15 idea 42 into the output format). |
| B026 | seed S-LIVE | Each unit declares, per reading it uses, whether it keeps its own cheap copy from its own feed. With a fresh MIS value it may prefer either, and the journal records which one the trade used. |
| B027 | new | A context receipt on every trade: the readings the unit saw at entry, their source (own copy or MIS), version and age, in one linked row (extends R15 ideas 126-127 with source and age). |
| B028 | new | Subscription instead of broadcast: a unit names the readings and markets it wants; the MIS computes only what is subscribed, plus a small always-on core for the almanac. |
| B029 | new | Ask the MIS: a unit or agent can request a one-off reading for a market outside its universe, for a proposal card, without that market entering any live list. |
| B030 | seed S-CONTEXT | The unit's context claim is written in the same words the MIS publishes, and in trader language he can read ("ranging, quiet, London, no red news"), so matching is a lookup. |
| B031 | new | Stand-aside readings published as first-class ("this market is in the state that hurts mean reverters today"), so the finder also says where not to go (extends R15 idea 36 from claim to output). |
| B032 | new | Units publish too: a unit's own live state ("in drawdown", "skipped 5 signals for spread") becomes a reading others can see. Never a control. |
| B114 | seed S-CONTEXT | A context sentence across tiers, in the trader's own three-timescale form (R35 section 3: "daily bullish, in the London killzone, after a sweep"): a day-tier word, a window and a fast reading. |
| B121 | seed S-S1S2 | Markets join a universe through readings: a market whose readings resemble a unit's proven markets for N weeks gets a proposal card to test; nothing trades from the card. |
| B125 | seed F-R19-CAP | The old capability_spec and compatibility rules (BLOCK, WARN, REQUIRE over archetype, timeframe, session) as the shape of a unit's context claim: REQUIRE is a hard need, WARN a preference, BLOCK a stand-aside. |
| P6-a | seed F-R19-SENT | The vault's three views per bot (raw broker, QML features, MIS context) revisited as a pattern: a unit always has its raw view, and the MIS view is optional. |

### 2.4 Sensors, and an MIS that grows (9)

| Id | Origin | Idea |
| --- | --- | --- |
| B109 | seed S-SENSOR | Reverse "he approves each sensor": he approves a class of sensor once (any seasonal ratio on any rung-2 market); agents add members inside that class in shadow freely; going live still needs his yes. |
| B110 | new | Year one: FX and gold packs only; the fast tier is seasonal ratios; the day tier is the agent brief; every other row shows as empty so the gaps are visible. |
| B111 | new | Year three: per-class packs, scored sensors, an almanac with years of stamped history, and units proposing markets from twin search. |
| B120 | new | A context-coverage view: which contexts have many units and which have none, steering where agents build new logic (the empty-niche view of R15 idea 90, fed by MIS states). |
| B123 | seed S-PHYS | Old physics code as a quarry: the Chaos and Ising readings from the old sentinel are re-tested on the new reading card instead of being restored or binned unseen. |
| B124 | seed S-QUALITY | Sensor sprawl control: near-duplicate readings (agreement above a set level) are merged or one retired, and a sensor nobody reads for N weeks gets a retire card (extends R15 idea 50). |
| B126 | seed F-R39-RULE | August's placement rule as a field on each reading card: shared by many units, expensive, market state, the same in test and live, worth versioning, so it sits in the MIS; cheap, strategy-specific or fast-changing, so it stays in the unit. |
| P3-a | seed S-HMM-TF | A model-zoo count shown openly: instruments times timeframes times retrains per month, so the cost of per-timeframe models is visible before anyone builds one. |
| P7-a | seed S-LIMBS | "Constant trunk, added limbs": one live version per sensor at any time (his August "constant"), while new sensors and versions are added through shadow (his "grow its own limbs"). |

### 2.5 QMX agents as analysts (11)

| Id | Origin | Idea |
| --- | --- | --- |
| B033 | seed S-AGENT | Morning brief workflow: an agent reads the daily charts, the MIS log, the calendar and fundamentals, and writes a pre-session shortlist in the MIS's words, timestamped before the open. |
| B034 | seed S-AGENT | The agent's shortlist is scored like a sensor: after the session its words are compared with the readings that actually happened; hit rate kept per market and per class. |
| B035 | seed S-AGENT | Three daily shortlists logged side by side (agent, MIS alone, all admitted markets) and scored weekly by a named scoring workflow. Answers who compares (PF L12-04) with an owner, not a rule. |
| B036 | seed S-AGENT | A unit-analyst workflow, a separate family: reads one unit's journal against MIS history and writes where and when it wins, naming the readings that separate wins from losses (extends R15 idea 125). |
| B037 | seed S-SENSOR | A sensor-scout workflow: an agent reads new MT5 articles and papers, maps each to a reading card, runs it in shadow on stored history and drafts a proposal card for the user. |
| B038 | seed S-AGENT | A disagreement digest each day: where the agent's reading, the MIS and a unit's own copy disagreed, and what happened next. |
| B039 | seed S-FUND | A fundamentals workflow writes slow outside-data readings (rate expectations, macro surprise, risk mood) into the day tier with sources attached; never into the fast tier. |
| B040 | seed S-COPILOT | The user and copilot weekly label ("these markets were mostly mean reverting this week") kept as dated human labels with what they could see; usable as training labels and as a week-tier reading. |
| B041 | new | Agent tools that can't be cheated: the agent's reading tool returns only data stamped before the agent's own timestamp, so a morning brief cannot see the afternoon. Look-ahead closed by the tool, not by trust. |
| B042 | new | A chart-reading agent with a vision model gives a by-eye reading (structure, zone quality, Wyckoff phase) where R35 section 7 item 5 says mechanical forms are disputed; scored like any sensor. |
| B117 | seed S-FUND | Fundamentals start as calendar plus surprise only (time, impact, forecast, actual from the free calendar); deeper fundamentals stay agent-written day-tier text. |

### 2.6 Correlation and herding (11)

| Id | Origin | Idea |
| --- | --- | --- |
| B043 | seed S-LEDGER | The MIS publishes, the correlation side reads: co-movement of readings across markets is an MIS output; any control stays with risk and sizing. |
| B044 | new | A dispersion reading: one number per class per moment for how alike all markets' states are. Low dispersion warns that many matches are one bet. |
| B045 | new | A herding count: per market, how many units read it as a match right now. Published for the risk side and the UI, never acted on by the MIS. |
| B046 | seed S-CORR | Same-idea groups: units sharing logic across timeframes (1m and 5m) count as one group in the herding count, per K4. |
| B047 | seed F-R39-SIM | Correlation by joint state, not overall: EURUSD and GBPUSD co-move differently when both are quiet than when both are wild; stored per joint state (extends R39 I4-I5, the dated ledger, with state). |
| B048 | new | A local swarm rule for picks: each unit takes its best match, then skips any market whose cluster already holds K trades from its own group (K a setting). No central allocator. |
| B049 | new | Leader-follower readings: which market in a cluster moves first (dollar index before majors, ES before the US500 CFD, BTC before alts), as a lead-lag reading per cluster. |
| B050 | new | Crowding of the outside world, not only of his units: perps already measure it with open interest and funding; for FX, broker-published retail positioning where it exists. |
| B051 | new | A reflexivity flag: once his size on a market passes a share of its usual volume or depth, a flag says his own trades may be moving the readings (scaled-account concern; a number, editable). |
| B127 | seed F-R39-SIM | Pair similarity as many dated readings, not one number (shared currency, session participation, cost, volatility, news sensitivity, trend tendency), so a pair can sit in several clusters at once. |
| P9-a | seed F-R19-IA | The old Intent Aggregator as a reference for what the risk side may one day ask the MIS for (per-symbol intent counts, correlation at the moment of entry), without the MIS owning any of it. |

### 2.7 Speed (10)

| Id | Origin | Idea |
| --- | --- | --- |
| B052 | seed F-R05 | Speed by information, not by model: every fast reading names its information source per bar (ticks, range, depth), because R05's detection bound cannot be beaten by a cleverer model. |
| B053 | new | Event-driven readings instead of polling: spread blowout, depth vanishing and tick-rate spikes are pushed the moment they cross a band, not on the next bar. |
| B054 | new | Precompute tomorrow: overnight the MIS prepares each market's usual curves for the next session (seasonal baselines, calendar), so the live part only divides now by usual. |
| B055 | seed S-TWO-SPEED | Two speeds taken literally: a slow board (session and day, from the PC and agents) and a fast stream (tick and bar, near the feed). A unit can live on the board alone. R09's plan and gate without the router machinery. |
| B056 | new | A freshness budget per tier (starting defaults: tick tier 2 seconds, bar tier one bar, session tier one session, day tier one day; editable). A reading older than its budget is stale. |
| B057 | new | "Time to notice" shown per reading: how long after a change the reading usually catches it, measured on history, so he sees that trend readings are slow. |
| B058 | new | Fast readings compute where the feed lands; slow readings compute wherever compute is cheap. Place follows tier, not a design rule. |
| B059 | new | Warm start: a market newly added to a universe gets its readings from stored history at once, so there is no warm-up wait (touches the DEC-0261 warm-up question in STATE). |
| B060 | new | A speed check per sensor: replay a recorded day at ten times speed on his PC and measure how far behind real time each reading falls. |
| P2-a | seed S-TWO-SPEED | A "morning coffee" tier: slow labels (regime, week state) pick which markets to watch today; they never time an entry. |

### 2.8 Failure and independence (12)

| Id | Origin | Idea |
| --- | --- | --- |
| B061 | seed S-STAND | A dark-MIS run in every unit's record: the same period traded with no MIS input. The gap is the MIS lift and also proof that the unit stands alone. |
| B062 | seed S-STAND | Finder-list fallback: a list older than its freshness budget falls back to the unit's home markets. Home markets become a required field for any unit that reads a list. |
| B063 | seed F-R18 | A health field on every reading: fresh, stale, degraded, shadow, retired. Units read the field; degraded counts as missing (extends today's degraded-sensors labeler). |
| B064 | seed S-QUALITY | A meaning-flip guard: a new sensor version replays the last N weeks and shows its output beside the old version before going live; a big shift needs the user's approval. |
| B065 | new | Daylight-saving, holiday and roll calendars as first-class inputs to every seasonal baseline, with a "baseline unreliable" flag on the days around a shift. |
| B066 | new | Venue failure in 24/7 markets: a crypto reading built from several venues drops the dead venue and marks itself degraded instead of going dark. |
| B067 | new | A feed-gap rule: after a gap, readings recompute from stored ticks before republishing, and the gap window is marked in history so studies can skip it. |
| B068 | new | A kill drill: on paper, the MIS is switched off for a scheduled day and every unit is checked to still trade its home markets. |
| B069 | seed F-R19-SENT | Lesson from the old sentinel, whose ensemble was built but never wired live: an MIS part counts as built only once it has run on a live feed on his PC. |
| B070 | new | A "wrong but confident" alarm: when a reading's word stays the same while the outcomes it predicts turn sharply worse, flag the reading, not the unit (a per-sensor drift alarm; extends R15 idea 112). |
| B122 | seed S-CENTRAL | The shared services named as a set: the MIS, the news kill switch, SQS and the correlation reader. Each one's failure is designed so a unit keeps trading. |
| P10-a | new | A wrong MIS is worse than a dark one: the design priority is detecting silent meaning changes, ahead of uptime. |

### 2.9 The operator's view (12)

| Id | Origin | Idea |
| --- | --- | --- |
| B071 | seed S-AMP | A lift story page per unit: "last week the MIS kept you out of 12 trades, 8 would have lost; it sent you to 5 markets you would not have watched, 3 won". |
| B072 | seed S-SNIPE | A today's-opens page: every named window today, ranked by how it usually behaves on a day like this (same weekday, same calendar, same overnight state). |
| B073 | seed S-CONTEXT | A chart overlay: the MIS words painted on the price chart as coloured bands, so he sees context the way a trader reads it. |
| B074 | seed S-READS | A market card per instrument: its rungs, its sensors, today's words, its habits, its units. One place to understand a market. |
| B075 | seed S-SENSOR | A sensor approval card in plain words: "reads tick rate, says busy or quiet, notices a change in about 3 minutes, would have helped these 4 units by this much in testing". |
| B076 | new | A "why didn't it trade?" button on a unit: which reading kept it out, with that reading's health and age. |
| B077 | seed S-NOISE | A noise meter per unit: the MIS lift with its uncertainty. When the band covers zero, the MIS is labelled "no proven help" for that unit. |
| B078 | new | A weekly market weather report written by an agent in plain words: per class, one paragraph, what changed and what is unusual. |
| B079 | seed S-CLASS | Class tabs (FX, metals, indices, crypto, perps), each with its own sensor list, so categorising by instrument type is visible. |
| B080 | seed S-COPILOT | A "teach the MIS" box: he or the copilot writes a dated note on a market ("oil is mean reverting this week"); it becomes a human label and a shadow reading. |
| B113 | new | A handover test: a new person or a fresh agent reads one market card and one sensor card and can explain what the MIS says about that market today. |
| P1-a | seed S-DOMAIN | A plain-words frame for him: the MIS is a telescope, not a steering wheel. It widens what a unit can see; it never drives. |

### 2.10 Stamped history, labels and data (9)

| Id | Origin | Idea |
| --- | --- | --- |
| B089 | seed F-R16 | Every reading stamped at compute time with sensor version and input times; history never recomputed in place; a retrain writes a new column (extends R16 section 7 point 6 into a storage rule). |
| B090 | new | An as-of query: QMB asks the MIS history "what did the MIS say at 08:01 on 3 March" and gets the stamped value, so backtests use exactly what live would have seen. |
| B091 | new | Backfill marked as backfill: readings computed later for old dates carry a flag, so studies tell live-stamped history from reconstructed history. |
| B092 | seed S-READS | The MIS log as its own Library kind: per market, per reading, per minute, kept as long as the user sets (no invented cap; disk is the limit). |
| B093 | seed S-REPEAT | An entanglement mark: when a unit's own rule and an MIS reading are the same primitive with the same settings, the journal marks them as one input so lift studies do not count it twice. |
| B094 | new | Publishing changes behaviour: log which readings units bind, and watch whether a reading's predictive power drops once units use it (a slow observer-effect study). |
| B095 | seed F-R05 | Labels known at entry only: a study of where a unit wins may use only readings stamped before the trade's entry, enforced by the as-of query. |
| B112 | new | Year ten: the stamped MIS history is the most valuable asset in QMX, worth more than any unit. Plan its storage and format for that from day one. |
| P11-b | seed S-DATA | Start from tables: market cards, reading cards, the stamped log and the almanac are tables first, screens second ("most of this is just data organization"). |

### 2.11 Wildcards and analogies (20)

| Id | Origin | Idea |
| --- | --- | --- |
| B081 | seed S-FEED | Feed-ranking analogy from his social-media remark: the MIS as a recommendation feed for units ("markets you may like"), with explore slots for markets near a unit's proven ones; candidates only, never trades. |
| B082 | new | Weather-service analogy: forecasts (slow, issued at set times) versus nowcasts (radar, minutes). The MIS has both products with different issue times. |
| B083 | new | Air-traffic analogy: the MIS is the radar, not the controller. It shows every plane and the weather; the pilots (units) fly. |
| B084 | new | Triage analogy: vital signs (fast, cheap, always on) versus lab tests (slow, ordered when needed). Slow models run for a market only when the vital signs look unusual. |
| B085 | new | Seismograph analogy: each market has a background noise curve per hour; an event is "above background". The seasonal baseline, named for him. |
| B086 | seed F-R39-KNOW | August's two shelves: durable knowledge (how gold behaves at the fix) and dated intelligence (today's reading). The almanac on one shelf, the board on the other. |
| B087 | new | Scouting analogy: a unit's player card lists the conditions it plays best in; the MIS is the fixture list with pitch and weather for each match. |
| B088 | new | Rating analogy: readings with a grade and an outlook ("quiet, outlook turning busy") rather than a flat label. |
| B096 | new | The MIS that lies on purpose: on paper only, feed a unit shuffled readings for a week. If its results do not change, it never used the MIS. |
| B097 | new | The MIS as a unit: a context-only unit trades the MIS's best word with a dumb entry. If it cannot beat random, the readings carry no edge on their own. |
| B098 | seed S-INEFF | Strategies born from the MIS: a reading that predicts next-hour returns after costs becomes an idea record with origin "MIS study" (extends R15 idea 61). |
| B099 | new | An inverse MIS: track states where every unit loses and publish them as no-man's-land, so new logic can be built for exactly those states. |
| B100 | seed F-R39-SIM | Market twins: pairs of markets whose readings track each other across years; a unit proven on one is tested on its twin first (similarity from readings; extends R39 I4). |
| B101 | new | A reading with a price tag: each sensor shows its compute and data cost per day beside its lift. |
| B102 | seed S-PHYS | Physics readings as a research shelf: Hurst, entropy, Ising-like order, fractal dimension. They enter a tier only through the same lag and lift card as any other reading. |
| B103 | new | Bot as sensor: a small fixed scalper in shadow on every market; its live hit rate becomes a reading ("mean reversion is paying here today"). R39's "mini scalper for an indicator" turned toward the MIS. |
| B104 | new | Reverse "the MIS reads markets": the MIS reads units. It watches which units win where and publishes "mean reverters are winning on these 8 markets now" as a reading of the market. |
| B105 | new | Reverse "one MIS": no central MIS at all. Each unit carries its readings; the "MIS" is only shared sensor code plus the almanac. A pole of the field, not a proposal. |
| B106 | new | Reverse "the MIS is fast": the MIS is only slow (session and day), every fast reading lives inside units, and the MIS becomes the almanac and the morning board. |
| B107 | new | Reverse "a reading is about one market": cross-sectional readings only (currency strength, dispersion, lead-lag, each market's volatility rank within its class). |


## 3. Questions

### `research` (20)

Evidence would settle it: academic work (research 22, 23, 37), the MT5 corpus or venue data.

| Id | Theme | Question | Links |
| --- | --- | --- | --- |
| QR01 | STD | For a 1-minute FX scalper, which fast readings carry information after costs: spread ratio, tick-rate ratio, depth ratio or range ratio? | B008, P2 |
| QR02 | STD | How much of a 1m or 5m scalper's result is explained by session and cost states, and how much by direction states? | B008, B052, P2 |
| QR03 | CLS | How closely does tick volume track real traded volume for FX majors and gold CFDs at 1m and 5m? | B013, B014, P3 |
| QR04 | CLS | How well does futures order flow (ES, GC tape) stand in for CFD flow (US500, XAUUSD)? Extends R35 section 7 item 8. | B005, B014, B015, P4 |
| QR05 | SEN | Which regime methods (HMM, jump model, change point, plain volatility buckets) give usable labels at session and day horizons in each class, and with what lag? | P2, B055 |
| QR06 | SEN | Does a regime-model setting taken from a paper still hold on his broker's data, or must it be refit every time? | B022, P7 |
| QR07 | SPD | Which information source per bar gives the fastest change detection on rung-2 markets versus rung-3 markets: ranges, ticks or depth? | B052, B005 |
| QR08 | CLS | Do funding and open-interest readings on perps tell mean reversion from trend at short horizons, after fees and funding? | B018, P4 |
| QR09 | COR | How stable is the co-movement of pairs within a joint state (both quiet, both wild) across years? | B047 |
| QR10 | LOG | How fast does a published market-state signal lose its value once many traders use it? | B094, P9 |
| QR11 | AGT | Which by-eye context (structure, zones, Wyckoff phase) can a vision-model agent read the same way twice? | B042 |
| QR12 | COR | Do lead-lag links (dollar index to majors, ES to the US500 CFD, BTC to alts) survive at 1m and 5m after costs? | B049 |
| QR13 | FAIL | How large are daylight-saving and holiday distortions in seasonal baselines for each class? | B065, P10 |
| QR14 | SEN | Which MT5 articles describe context readings per style and class with runnable code, and which readings recur? | B037 |
| QR15 | CLS | What does academic work say about one state vocabulary across asset classes versus class-specific state models? | P5, B020 |
| QR16 | STD | In 24/7 markets, what plays the role of sessions: regional activity, funding cycles, weekday against weekend? Extends PF L03-24. | B017, B018 |
| QR17 | COR | Do cross-sectional readings (currency strength, dispersion) add value beyond readings of single markets? | B013, B044, B107 |
| QR18 | COR | Which retail-positioning feeds exist for FX and gold at his likely brokers, and do they carry information? | B050 |
| QR19 | CLS | Which rungs does each venue he may use actually offer (cTrader, a futures broker, Hyperliquid, CCXT venues)? Belongs with research 38. | B004, B013-B018 |
| QR20 | STD | Is direction at 1m and at 5m one measurement with two horizons, or two different questions that need different readings? | B006, P3 |

### `operator` (11)

Only he can answer: money, words he cares about, what he wants to see, irreversible scope.

| Id | Theme | Question | Links |
| --- | --- | --- | --- |
| QO01 | OPV | On his screens, should the MIS speak in words, in numbers, or both side by side? | B024, P6 |
| QO02 | CLS | Which classes come first for him: FX and gold, or indices and perps from the start? | B110, B019 |
| QO03 | SEN | May agents add sensors in shadow without asking, as long as going live always needs his yes? | B109, P7 |
| QO04 | AGT | Should the weekly labels he and the copilot write only inform the MIS, or also be used to retrain it? | B040, B080, P8 |
| QO05 | PUB | Does he want the MIS to propose new markets for a unit as cards, and how often would he like to see them? | B121, B081 |
| QO06 | OPV | Should the skipped-trade story appear daily, weekly, or only when he asks? | B071, P11 |
| QO07 | STD | Is sniping its own style, or a set of windows inside other styles? | B012, P11 |
| QO08 | CLS | How much would he pay each month for richer data (futures tape, perps depth) once a unit needs it? | B004, B014, B016 |
| QO09 | SEN | When he called the MIS "a constant" in August, did he mean one live version per sensor, or a core that never changes? | P7 |
| QO10 | OPV | Which name does he want on screen for the thing units read: MIS, board, finder, radar, or another word? | B055, B083 |
| QO11 | STD | Should news units exist at all, given the global news kill switch? Repeats the R15 conflict; still his call. | B010, B108 |

### `lead` (17)

Architecture questions the lead can settle or measure.

| Id | Theme | Question | Links |
| --- | --- | --- | --- |
| QL01 | SEN | What is the smallest reading-card schema that carries tier, clock, rung, version, lag, health and the three output forms? | B001, B024, B063 |
| QL02 | LOG | Where does MIS history live in the Library, and how do unit journals link to it without copying? | B092, B027 |
| QL03 | LOG | How does one as-of query serve QMB and live trading with the same code? | B090, B095 |
| QL04 | SPD | Where do fast readings compute when the feed lands on the node, and where when it lands on the PC? | B058 |
| QL05 | PUB | How does a unit declare its own cheap copy of a reading, and which value wins when the two disagree? Extends QF Q78. | B026, P6 |
| QL06 | SEN | What is the retire rule for unread or unhelpful sensors (a number with a starting default)? | B124, P7 |
| QL07 | CLS | How does a class pack plug into QML and the dictionary, given one catalogue with roles? | B020 |
| QL08 | FAIL | How does QMB produce the dark-MIS run, and how does paper trading produce it live? | B061, B068 |
| QL09 | PUB | How does a unit declare subscriptions, and what is in the always-on core? | B028 |
| QL10 | COR | What exactly does the MIS publish for the risk side (dispersion, clusters, herding counts) so it describes without controlling? | B043, B044, B045, P9 |
| QL11 | AGT | How are human labels stored so the hindsight they carry stays visible? | B040, B080 |
| QL12 | SPD | What does a fast tier for 100 markets cost in CPU and memory on his PC? Measure it. | B060 |
| QL13 | SEN | What is the update path for a sensor version: shadow, replay comparison, approval, switch? | B064 |
| QL14 | FAIL | Which health states exist, and how does each map to "missing" for a unit? | B063 |
| QL15 | CLS | How does a borrowed rung declare its second-feed dependency, and how does it degrade when that feed dies? | B005, B014, P4 |
| QL16 | STD | How are sniping windows stored as calendar data per market, in exchange time and broker server time? R36 lists broker server time as missing. | B012, B072 |
| QL17 | SPD | Is the seasonal baseline built on the PC from history or on the node from its own stream? Repeats R09 section 6 point 4. | B054 |

### `fog` (8)

Nobody can answer yet; it clears as other answers land.

| Id | Theme | Question | Links |
| --- | --- | --- | --- |
| QF01 | PUB | Is the MIS one thing with tiers, or several products (board, stream, almanac) that share one vocabulary? | B055, B082, B105, B106 |
| QF02 | FAIL | Can a unit exist that only picks markets from a finder list, or does every unit need home markets of its own? | B062, P10 |
| QF03 | AGT | Is the analyst agent part of the MIS, or a separate family that feeds it? Close to PF L11-15. | B033, P8 |
| QF04 | LOG | If the stamped MIS history becomes worth more than any unit, what does that change about what QMX builds first? | B112 |
| QF05 | COR | Does publishing readings to many units create herding that the MIS must then describe, in a loop with no end? | B045, B094 |
| QF06 | COR | Where is the line between describing correlation and controlling it once the MIS publishes counts? | B043, B045, P9 |
| QF07 | OPV | Is "noise" a property of the MIS, of one reading, or of one unit and reading together? | B077, P1, P11 |
| QF08 | CLS | Can one vocabulary hold "crowding" for perps and "positioning" for FX without the same word meaning different things? | B018, B050, P5 |


### Dropped as "any trader knows"

Checked against research 35 §6 (K1 to K20). These were raised in the run and dropped because practice already answers them. The part that practice does not answer stays above as its own question.

| Raised in the run | Dropped because | What stays open |
| --- | --- | --- |
| Is the same unit on 1m and 5m one idea? (P3) | K4, and his own correction (T2:1001) | How the MIS uses one source for both (B006, QR20) |
| Do instruments have session habits? (P5) | K6 | How habits are stored and shown (B021, B074) |
| Should a high-spread market be filtered before matching? (P10) | K7 | How cost per venue is published (B116) |
| On stale data, stop new entries? (P10) | K10, for the unit's own feed | A stale MIS reading is a different case (B062, QF02) |
| Is a reading used by both a unit and the MIS repetition? (P6) | K3, one primitive with two bindings | His "already specific" point (B023, B093) |
| Is "higher-timeframe bias plus lower-timeframe trigger" a valid context shape? (B114) | K13 | How a context sentence spans tiers (B114) |
| Should entries pause around high-impact news? (B010) | K9, the blackout window is standard | Whether news units exist (QO11) |
| Do volatility-scaled distances travel across instruments? (P5) | K15 | Nothing for the MIS |

## 4. Matrix sketch: where the ideas apply

Three views of one four-way space (style × timeframe × data class × asset class). INFERRED except where a cell cites a file.

### 4.1 Style × timeframe tier

Columns are the alarm clocks of B002. A cell lists the ideas that apply.

| Style \ tier | Tick | Bar (1m to 5m) | Bar (15m to 1h) | Session / window | Day | Week |
| --- | --- | --- | --- | --- | --- | --- |
| Sub-minute scalper | unit's own feed (B011); B053 | - | - | B012, B115 | P2-a | - |
| 1m to 5m scalper | B008, B053, B005 | B006, B007, B003, B056 | - | B012, B115, B118 | P2-a, B033, B055 | - |
| Sniper (named windows) | B053 | B008 | - | B012, B072, B115, B119 | B033, B072 | - |
| Intraday 15m to 1h | - | B006 | B006, P1-b, B114, B118, B119 | B115, B072 | B033, B039, B055 | - |
| Swing / position | - | - | B114 | - | B039, B117 | B009, B040 |
| News / event | B010, B053 | B010 | B010 | B010 (event clock) | B117 | - |
| Every style | B063 health, B089 stamps | B024 three forms | B024 | B065 calendars | B078 weather report | B040 human labels |

### 4.2 Data rung × asset class

Which rungs each class offers, as stated in the findings or inferred. A cell gives availability, then the ideas that need that rung there.

| Rung \ class | FX (cTrader) | Gold CFD | Gold futures (GC) | Index CFD | Index futures | Crypto spot | Perps | Commodity futures |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 calendar | yes (sessions, 5 p.m. NY roll; R35 §2.2) B012, B065 | yes (fixes) B014 | yes (roll) B014 | yes (cash open, auction) B015 | yes (roll, RTH/ETH) B016 | partial (24/7, listings) B017, QR16 | yes (funding hours; R35 §2.2) B018 | yes (reports, roll) B019 |
| 1 OHLC bars | yes, all base readings B006 | yes | yes | yes | yes | yes | yes | yes |
| 2 quote ticks, tick count | yes (tick volume as proxy; R35 §2.2) B008, B013 | yes | yes | yes | yes | yes | yes | yes |
| 3 depth | yes (cTrader depth; STATE.md, from research 21) B005 | broker-dependent, INFERRED | yes | broker-dependent, INFERRED | yes | per venue | per venue | yes |
| 4 trade tape, real volume | **no** (no central volume, R35 §2.2; no public tape on cTrader, STATE.md from research 21) B005, B007 | no; borrow GC (B014, QR04) | yes B016 | no; borrow the future (B015, QR04) | yes (R35 §2.2) B016 | per venue, fragmented (R35 §2.2) B017 | yes (R35 §2.2) | yes |
| 5 derivatives fields | swap only | swap only | open interest, COT (R35 §2.2) | swap | open interest (R35 §2.2) | none | funding, OI, liquidations (R35 §2.2) B018, B050 | open interest |
| 6 outside data | calendar, rates B039, B117 | dollar, real rates B014 | same | cash index | same | listings, news | listings, unlocks | inventories |

### 4.3 Idea families × where they apply

| Idea family | Applies to | Does not apply to |
| --- | --- | --- |
| Seasonal "now versus usual" ratios (B008, B054, B085) | every class at rungs 1 to 3; strongest for scalpers and snipers | markets with no stable daily cycle until QR16 answers what replaces sessions |
| Order-flow readings (B005 top rung, B016) | index futures, gold futures, perps, crypto spot per venue | FX and CFDs except by borrowing (B014, B015) or downgrade (B005) |
| Crowding and positioning (B018, B050) | perps (native), futures (OI), FX (only via broker feeds, QR18) | crypto spot, index CFDs |
| Cross-sectional readings (B013, B044, B049, B107) | classes with many co-moving markets: FX majors, crypto alts, index families | single-market classes (one gold contract) |
| Slow regime labels (P2-a, QR05) | day and week tiers in every class | tick and fast bar tiers (F-R05) |
| Event-clock readings (B010, B108) | FX and gold (macro calendar), futures (reports, roll), perps (funding, unlocks) | none; every class has events, only the calendar differs |
| Agent briefs (B033 to B040) | day and week tiers everywhere | tick and fast bar tiers |

## 5. Permutation cross-map

How ideas combine, depend on each other or conflict. Relations: `enables`, `depends on`, `same as`, `conflicts with`, `tension`.

| A | Relation | B | Why |
| --- | --- | --- | --- |
| B089 stamps and versions | enables | B090 as-of query, B095, B061 lift, B021 hunts, B034 agent scoring, B100 twins, B064 | Almost every study needs what the MIS said at the time, not what it says now |
| B004 data ladder | enables | B020 class pack, B005 downgrade, B007 clocks, §4.2 | A class pack is a rung table plus a calendar plus sensors |
| B006 one source, aggregated up | enables | B046 same-idea groups | Shared source makes the 1m and 5m correlation explicit, as he said (T2:1001) |
| B003 lag-to-hold rule | same as | B057 time to notice | One measurement, used once as a rule and once as a display |
| B023 finder | conflicts with | B105 no central MIS | A finder needs a view across markets; B105 loses B013, B044, B049 |
| B106 slow-only MIS | conflicts with | B008, B053 | B106 moves every fast reading into units; fits B011 and P2-a |
| B106 slow-only MIS | tension | S-SCALP | His "multiple indicators inside a scalper's MIS" (T2:219) puts fast readings in the MIS |
| B126 placement rule | enables | B105, B106 per reading | The poles become a per-reading choice instead of a whole-MIS choice |
| B026 own cheap copy | depends on | QL05 | Needs a rule for which value wins when they disagree (QF Q78) |
| B028 subscriptions | conflicts with | B021, B112 | Unsubscribed markets build no history; needs a wide always-on core (QL09) |
| B040, B080 human labels | conflicts with | B095 entry-only labels | Weekly labels carry hindsight; B041 and QL11 date them |
| B109 class approval | tension | S-SENSOR | He said "with the user's approval" per upgrade (T1:1951); QO03 asks |
| B045 herding count | tension | STATE "book and correlation control belong to the risk-and-sizing session" | Publishing a count is description; using it is control (QF06) |
| B048 swarm rule | conflicts with | the same STATE line | B048 is a control, so it is parked for the risk session (§6) |
| B014, B015 borrowed rungs | tension | standing order 10 | Safe while only the MIS carries the second feed (P4-b); a unit with a hard need on a borrowed reading depends on two feeds |
| B062 home-market fallback | depends on | QF02 | Only works if every list-reading unit has home markets |
| B022 per-instrument sensor profiles | tension | P3-a model zoo | Profiles per instrument multiply versions to track |
| B012 sniping windows | depends on | QL16 | Windows need broker server time, which the dictionary lacks (R36 line 205) |
| B031 stand-aside readings | enables | B099 inverse MIS | Same data seen from the losing side |
| B024 three output forms | depends on | QO01 | Settles the numbers-versus-words clash of P6 only if he wants both |
| B125 capability-spec shape | same as | R15 idea 35 | Hard and soft context claims, with an old precedent |
| B103 bot as sensor, B104 MIS reads units | same as | each other | Unit outcomes used as a market reading |
| B103, B104 | tension | B094 | Readings built from his own units' trades feed back into his units |
| B044 dispersion | depends on | B013 | Needs readings for all markets of a class at the same moment |
| B059 warm start | depends on | B092 | Needs stored history for the new market |
| B121 markets join through readings | depends on | B100 twins | Cards only; nothing trades, per standing order 7 |
| B010, B108 news style | conflicts with | the global news kill switch | QO11 |
| B055 two speeds | tension | 13 and 14 router options | He found those over-built (STATE 28 Oct); B055 keeps two speeds without signed plans, offers or expiry machinery |
| B033 agent brief | same as | S-TWO-SPEED | The agent writes the "per session or per day" label he described (T2:325) |

### Party clashes, kept open

| Round | Clash | Carried to |
| --- | --- | --- |
| P1 | A label is a compressed copy of price (Grace) against the MIS sees what one unit cannot (Okafor) | QF07, B061, B077 |
| P2 | HMMs belong on a daily clock (Lindqvist) against then they are not part of a scalper's MIS (Tomas) | QR05, QF01 |
| P3 | Aggregate one measurement up (Okafor) against direction is a different question per horizon (Lindqvist) | QR20 |
| P4 | Borrowing adds a dependency (Grace) against only the MIS carries it (Bo) | QL15, P4-b |
| P5 | One vocabulary with per-class sensors against a separate MIS per class | QR15, QF08, P5-b, P5-c |
| P6 | Publish numbers (Okafor) against people need words (Ines); which version did the trade use | QO01, QL05 |
| P7 | Sensor sprawl is the likely end state (Grace) against cards make it visible (Mira) | QL06, B124 |
| P8 | An agent replicating the MIS is an unversioned second MIS (Grace) against stamped readings make it a sensor (Mira) | QF03, B034, B041 |
| P9 | Where describing ends and controlling begins | QF06, QL10 |
| P10 | A pure finder-list unit has nothing of its own (Grace) against a home market by rule (Bo) | QF02, B062 |
| P11 | Mostly noise (Grace) against noise is measurable (Okafor) | QF07, B077 |

## 6. Parked

Out of this field's scope or not yet useful. Kept so nothing is lost.

| Item | Why parked | Where it belongs |
| --- | --- | --- |
| Exit and sizing maths, including any MIS-driven size change | Forbidden in this run; owned by the risk-and-sizing session (STATE 30 Oct) | risk-and-sizing session |
| B048 swarm rule and any same-bet limit | A control, not a description; book and correlation control belong to the risk session (STATE 30 Oct) | risk-and-sizing session |
| Router ranking algorithms, offers that expire, load-balancer mappings (research 13, 14) | He found them over-built (STATE 28 Oct) | revisit only if a ranking is needed after labels exist |
| Live expansion options (a) to (f) and promotion rules | Not MIS work; already mapped in R15 §4 H | unit and admission work |
| Paid data choices (Databento, Tardis) | His money call (QO08, STATE funnel-2 Q7) | operator; research 38 |
| B011 sub-minute scalping inside the MIS | Default left to the unit's own feed | revisit if a seconds-scale unit appears |
| B019 commodity futures row | No unit needs it yet | class pack later |
| B051 reflexivity flag | A scaled-account concern, not at $300 | later |
| B097 MIS-as-unit trading live | Paper only; a test, not a product | QMB and paper |
| Screen layouts for B071 to B080 | UI is judged by design and by running it (STATE 30 Oct) | UI session |
| Dictionary rebuild scope for class packs | QML work | QML session (QF) |
| Where the node runs, server rental | Node work | node planning |

## 7. Not verified

- Venue facts in §4.2 marked INFERRED (depth on gold and index CFDs, per-venue depth for crypto) were not checked this session; research 38 covers them.
- The party's trading claims are general practice (INFERRED). Only cited sections were checked.
- Research 22, 23 and 37 were not available to this run; every `research` question waits on them or on later runs.
- Today's MIS code was read only through research 18 §4, not opened directly.
