# Questions raised by the CIS run

Written 2026-10-30 by the CIS agent. Every question the run raised, for the wayfinder chart. No answers.

**Tags.**
- `research`: evidence would settle it.
- `operator`: his intent, money, vocabulary or irreversible scope.
- `lead`: a technical call the lead can make.
- `fog`: cannot be phrased sharply yet.

**Source** names where the question came from: a contradiction (`C1`-`C23`, research 17 §4), a knot (`Ka`, `Kb`, `Kc`, in `problem-solving.md`), a glossary word (`G:word`), a design-thinking journey (`J1`-`J6`) or HMW (`HMW n`), or the innovation file (`IS`). Quotes of his words are CHECKED at the line given (`T1`, `T2` as in `problem-solving.md`).

Q1-Q43 are referenced by id from `problem-solving.md` step 5b. Q44 from the glossary. Q45 onward from the other files.

---

## The MIS, the router, and units reading them

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q1 | When a unit "reads the MIS", which of the three uses does he mean: a rule input, a placement (which markets), or a veto? | operator | C1; his "the units… pick the output and they propose whether to use it or not" (T1:1951) |
| Q2 | If a unit uses an indicator the MIS also uses, is that the same reading (one primitive, two roles) or a duplicate to remove? | research | C1; his T2:216 "Is that repetition?" |
| Q3 | Data parity (whatever touches history must touch live) implies QMB must replay any MIS output a unit reads. Is that cost acceptable, or does it argue for units computing their own context? | lead | C1; R17 J16 |
| Q4 | What does a unit do with a stale or missing MIS reading: ignore, compute locally, or stop new entries? Is that per unit or global? | lead | C1, J2 step 6 |
| Q14 | Which MIS jobs must run on the node (fast state for units), which on the PC (slow lists, training), which anywhere as library code? | lead | C5 |
| Q15 | With the PC asleep overnight and crypto trading 24/7, what slow MIS output may a unit rely on, and how old may it be? | lead | C5; T2:322 "we are literally trading 24/7" |
| Q20 | What is the measured lag and false-alarm rate of each candidate sensor at 1m and 5m, per asset class? | research | Ka, C9; R16 §7.10 |
| Q21 | Does a context label available at entry time lift results, compared with the same label known only afterwards? | research | Ka; R16 §1.3 |
| Q22 | Which fast proxies exist for direction context (cross-section, higher timeframe, tick or volume bars, order flow where it exists) and which beat the slow reading? | research | Ka; his "Quick proxies, I don't know" (T2:322) |
| Q39 | Does the best MIS group sensors by trading style, by timeframe, by data class, or by all three? | research | C19; his "we need a trading style, firstly" (T2:216) |
| Q45 | Is the router a separate part that reads the MIS, or the MIS itself under another name? | operator | G:router, G:MIS |
| Q46 | Does the news kill switch belong to the MIS, to an "ideal BMS", or beside both as an independent guard? | operator | G:MIS; his T2:216 "Things like now that new skill switch… can be centralized" vs ruling ST:65 |
| Q47 | Can agents "replicate or check" the MIS well enough that their disagreement is a useful training signal? | research | his T2:322 "replicating what it is doing" |
| Q48 | When a workflow finds a new context term and an agent proposes a sensor, what must he see before approving it? | operator | R17 M17; R16 §1.4 |
| Q49 | Does "grow its own limbs" mean new sensors, new MIS templates per market type, or new units? | fog | T2:132 |

## Identity: what makes two units the same

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q5 | Under System 1, is the same logic on a new instrument a sibling unit, the same unit with per-market settings, a child record, or only a membership tag? | operator | C2 |
| Q6 | Whichever identity rule wins, what happens to a unit's journal, try count and click scope when it starts trading a second market? | lead | C2 |
| Q7 | Does the type of edit (logic, calibration, coordinate, environment) decide identity mechanically, so no agent judges it? | lead | C2; R16 §2 |
| Q8 | Does Q1's 27 Oct "yes" to sibling units still stand after 28 Oct? | operator | C2; ST:110 |
| Q9 | Is a timeframe change a coordinate, a logic change, a calibration or a style change? Does the answer differ for time bars vs tick or volume bars? | operator | C3; docs retire "timeframe" for `BarSpec` |
| Q10 | When the 1m and 5m versions of one logic move together, do they count as one bet and one try, or two? | research | C3; SE:53-55 |
| Q17 | What exactly does his click admit: one unit, one unit on one market, or an envelope of markets by class? | operator | C7 |
| Q18 | Can anything trade live at minimum size inside an admitted envelope before its own record exists, given "For any variant, any unit, it's only me" (T1:1574)? | operator | C7 |
| Q23 | When a System 2 child is earned (Path A), whose record does it size from on day one: its own paper trail on that market, the parent's pooled record, or a blend? | operator | C10 |
| Q24 | A System 2 is made on a pair the unit rarely traded, then the market's structure changes. What does QMX do? | research | C10; his own case, T2:216 |
| Q25 | Can a short backtest on QMX's own recorded live data (a week, a month) add evidence, or is it too short to matter? | research | C10; his "backtesting across a week makes no sense. Unless I'm wrong" (T2:216) |
| Q35 | What is malleable when a unit becomes intraday or swing: the logic, the risk template, the MIS profile, or all three? | operator | C17; T2:132 |
| Q36 | Is "scalpers first" a build order only, or a schema assumption? | lead | C17 |
| Q50 | Does a gold-only source fit System 1 at all, or does it enter only as a System 2 seed? | operator | his question, T1:1999 |
| Q51 | Is a plain-Python unit or an ML ensembler with no declared context needs a unit, and what does the MIS do with it? | lead | G:unit; ST:47 |
| Q52 | When a unit's sizing module is swapped, is that the same unit, a new version, or a new unit? | lead | G:unit |

## Safety across units: correlation and shared money

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q11 | Which of the six historical correlation jobs (funding-stage gate, sizing multiplier, per-tick aggregator, exposure ledger, dated pair record, cohort correlation in judging) does QMX need now? | operator | C4, Kc |
| Q12 | Where does each needed correlation job run so that it works with the router and MIS down, and never stops a unit only because it is down? | lead | Kc; standing order 10 |
| Q13 | On a day 20 markets match one unit's context, how many independent bets are there by pairwise correlation, by effective number of bets, and by shared MIS label? Do they agree? | research | Kc; R16 break 3 |
| Q40 | With two units and $300, each "should be able to use all the 300" (T2:216). What rule rebalances when a third arrives, and who sets it once? | operator | C20 |
| Q41 | Does a unit size its own trade inside a share a central part allocates, or negotiate its share, or own all sizing with the guard only stopping it? | operator | C20; flag for the risk session |
| Q42 | The pain floor: a percentage of what (seed, equity, peak)? | operator | C22; risk session |
| Q53 | Two units on the same symbol in opposite directions within a second: does QMX resolve it (the old Intent Aggregator rule 1) or let both trade? | lead | J2 step 7; R19 §2 |
| Q54 | Is a "bet counter" (units entering on the same context label within N minutes count as one) simpler and safer than a correlation number? | research | Kc option 10 |

## Agents: being wrong, and proof

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q31 | Which of the fifteen failure modes (F1-F15) actually occur when agents analyse a recorded day? | research | Kb; his "We also need to know in which ways they can be wrong before we define the tools" (T2:382) |
| Q32 | By "non-deterministic… that can't be cheated" (T2:382), does he mean open-ended analysis whose result the agent cannot steer, or something else? | operator | C15, Kb |
| Q33 | Can a forecast ledger (dated calls scored by later data) replace a person comparing shortlists, answering his "Who's comparing?" (T2:382)? | research | Kb |
| Q55 | Who records an agent's receipts: the engine (which the agent cannot edit) or the skill's scripts (which run inside the agent's turn)? | lead | Kb; R18 §1.1 ledger, §1.4 run refs |
| Q56 | Should every analysis name its window (a landmark) as a typed field? Which landmarks are the defaults? | lead | his "you need to give a pass, in other words, a landmark" (T2:382) |
| Q57 | Do two agents from different model families catch more errors than one agent with receipts? | research | Kb option 5; R19 §1 April reviewer agent |
| Q58 | How is text inside sources (a video transcript, an article) kept from acting as instructions to the extraction agent? | lead | Kb F11 |
| Q59 | Do agents read chart images, numbers, or both? If both, must a chart claim be restated from numbers? | research | J4; R17 A09 |
| Q60 | When does an agent review run in a 24/7 market: per session close, per market, per N trades, or on a journal event? | lead | J5; R17 A08 |
| Q61 | Which agent families come first: market analysis, unit analysis, or both at once? | operator | his split, T2:382 |
| Q62 | Is the "organogram" of specialist agents a workflow, a mini app, or both? Built now or after live? | operator | his T2:322 |
| Q63 | How are agent proposals that he ignores treated: expired, kept, or scored anyway? | fog | J3 |

## Proof, numbers and judging

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q26 | Where should a trade-count threshold come from: a research default, an agent workflow proposing ranges from performance, his setting, or QMB computing it per unit from that unit's own variance? | operator | C11; his "the agents can help propose and figure it out" (T2:322) |
| Q27 | Can a sequential test (no fixed count) replace a fixed trade count for trusting a specialist? | research | C11 |
| Q16 | Do more research variants still help once live breadth comes from System 1 placement? | research | C6 |
| Q64 | Is "broad" judged on a pooled read (one test) or per market (many tries)? What does each cost in tries? | research | R16 §1.3; R17 U34-U36 |
| Q65 | Does the fail branch ("most strategies can work") stay, and with what guard against finding a context by luck? | operator | SE:61-65; R16 §1.4 |

## Instruments, terrain, data

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q37 | Do instruments matter only through their data and terrain, or also through habits (gold at the NY open)? | research | C18 |
| Q38 | Is the MIS keyed by asset class, by data-availability class (OHLC-only vs order flow), or by venue type? | research | C18; G:instrument class |
| Q28 | Are news units allowed now? If so, how does the news kill switch treat them? | operator | C12 |
| Q66 | When a market is "perfect for a unit, but its spread is so high", does SQS simply block it, or does terrain screen it out before matching? | lead | his T2:216 |
| Q67 | Does QMX record its own live data across all markets it can see, and where does it fit on disk under local-first? | lead | his T2:216; ST:151 disk note |
| Q68 | Is tick data "an API problem we solved in older versions" (T2:322), or a broker limit? | research | T2:322 |

## Words and process

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q19 | Is QML's protocol upgraded in place and the dictionary rebuilt, or both rebuilt? | operator | C8 |
| Q29 | What blocks the first paper unit first: a QMB runner that trades, or a node that runs? | research | C13; R18 §2, §7 |
| Q30 | For each named break he asked about on 29 Oct, does he want a testable option now, or only after the field is widened? | operator | C14 |
| Q34 | Does the wayfinder chart drop any question this expansion found? | lead | C16 |
| Q43 | Should "System 1" and "System 2" be renamed to avoid the September "system one" models and the fast/slow reading? | operator | C23; G:System 1 |
| Q44 | Do the docs' vocabulary rulings (bare "timeframe" retired for `BarSpec`; "envelope" never bare; "archetype" retired) bind the unit work? | operator | glossary finding; `docs/glossary.md:98`, `:306`, `:1027` |
| Q69 | Which contested words need one meaning before architecture, and which can stay plural with qualifiers (market journal vs unit journal)? | lead | glossary |
| Q70 | Does "workflow" in his sentences mean a QMX workflow or the planning run? Should every file say which? | lead | R17 A13 |

## Lifecycle and UI

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q71 | What is the full set of lifecycle states (old: LIVE, PAPER, RECOVERY, RETIRED, AT_RISK, CIRCUIT_BROKEN)? Which transitions are his clicks and which are risk stops? | operator | J1 stages 14-16; R19 §5 |
| Q72 | When a unit retires, what is extracted into its parent, the almanac and the graveyard? | fog | J1 stage 16-17 |
| Q73 | Do retired children's trades stay in the parent's pooled record? | research | J1 stage 17; survivorship |
| Q74 | When the copilot "attaches a market by hand" ("you trade oil", T2:216), is that an envelope change (his click), a settings change, or an MIS retrain request? | operator | J6 |
| Q75 | What does his one-minute morning brief show, and on what page? | operator | J3 |
| Q76 | Does a unit's paper twin on unadmitted matched markets count as evidence for the next click, or as tries? | research | design idea 20 |
| Q77 | What is the full list of steps a unit takes before it places a trade, and which step may be skipped when its source is down? | lead | J2; his T2:216 |
| Q78 | How does self-configuration of risk and sizing actually work, shown on one unit? | fog | ST:78; his T1:1574 "I actually haven't seen how they are going to self-configure" |

## Positioning

| Q | Question | Tag | Source |
| --- | --- | --- | --- |
| Q79 | Which difference matters most to him: placement, honest judging, or the analyst desk? | operator | IS step 6 |
| Q80 | Can more than two or three markets be traded at safe risk at $300 for one unit? | research | IS H2; R16 §7.3 |
| Q81 | What are the "multiple experiences that a unit can provide" (T2:6)? | fog | IS step 1 |
