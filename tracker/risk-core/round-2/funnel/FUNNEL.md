# Funnel, round two: what goes in, what the core must carry, what ships first

Fable funnel judge, 7 Nov 2026. Round two of the risk and sizing session. Written under `round-2/BRIEF-COMMON.md`. Companion files: `FATES.md` (one row per idea) and `QUESTIONS.md` (what truly needs him).

**The test used, and only this test** (`BRIEF-COMMON.md:29-36`). For every idea: (1) is it configuration? Then a block, preset, template or pod setting. (2) If left out now, does the core get reworked later? Then the core leaves a socket, input, record or hook. (3) Otherwise it is content someone adds later, or another session's. No dollar simulation decided anything here. The old funnel's `HYBRID-FATES.md` and `architecture/SPINE.md` were read as material; its `REVIEW.md` findings on evidence, fidelity and logic are kept; its dollar verdicts are dropped.

**Paths.** Bare paths are under `D:\QMX-worktrees\risk-plan\tracker\risk-core\`. `H1` to `H5` are `harvest/H*.md`; `E1` to `E5` are `round-2/expand/E*.md`; `SWAP` is `unit-baseline/SWAP-CHART.md`, with `SWAP n` a row of its placeholder table and `SWAP En` a row of its 1b table; `MAP` is `review-2026-11-07/system-map.md`; `PH n` is a row of `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\build\RISK-SIZING-PLACEHOLDERS.md`; `PACK` is `RISK-SIZING-PACK.md` in the same folder; `SEEDS-2` is `round-2/SEEDS-2.md`, with `H-nn` its checklist and `T-nn` its register. Old decision points are `old DPn` in `funnel/FUNNEL.md`. Ids such as `X3-H63`, `H2 I4`, `H3 T6`, `E2 Way 5`, `E4 L02` point at those files. Code line numbers are as those files report them at tip `255f3bbf` or `351e7521`; I ran nothing and read no code myself.

**Evidence labels.** BUILT: in the code, as a harvest or the swap chart read it. REAL: live practice in its own field, a paper read by one of our agents, or a controlled test; the field is named. MODEL: our own simulation; it shows how a mechanism behaves, never that a real unit does. PROPOSAL: reasoned, untested. GUESS: an analogy. RULING: his words, cited. UNKNOWN: not verified.

**Words.** Unit: one self-configuring trading algorithm. QML: the block library and dictionary units are built from. QMB: the backtest and proof system. MIS: the market reader. SQS: the spread sensor and gate. Pod: a versioned stack of risk rules (seven slots in the Lab design); he also uses it for a hedge-fund department, which `E2` calls a desk. Socket: a place in the unit a block plugs into. Row: one declared control in a registry. Receipt: the record of how a size was computed. R: the loss if the planned stop is hit. Sticker: a typed, expiring notice on a market scope (`E1` section 4). Toleration: a unit's declaration that it ignores a sticker kind.

**How the skills ran.** `bmad-party-mode` and `bmad-advanced-elicitation` were loaded and run headless: one mind voicing a trader, a quant, a systems engineer and a developer, then pre-mortem, red team and first principles over sections 3 and 4. No memlog, no HTML, no scripts: the brief allows these three files only. The party's clashes and the elicitation findings are in Appendices A and B. They changed six calls, named there.

**Fix round, 7 Nov.** `round-2/funnel/REVIEW.md` (Opus, independent) and `round-2/UI-LOOK.md` (the lead opened the running demo) were applied in place with the lead's rulings; Appendix D lists every change and the one partial rejection, and Appendix E lists what this funnel proposes to overhaul. `UI-LOOK.md` is a picture of intent at the time, not a spec: no screen, slot list or block name binds a core item, and where the demo and his later words differ, his words win. The brief's test still rules: nothing was narrowed by a result.

---

## 1. The destination, in his words

1. "Let's just make sure that the unit can actually trade, it can self-configure, it has a template. That's all I wanted from you." (M49)
2. "have a template that we can plug in our own configurations and stuff" (M49). "What if I want to change the way it is derived?" (M10)
3. "something that out of the box can work" and "even if we don't have the numbers set yet" (M50). "the numbers I gave you all of them are exemplary" (M50)
4. "Someone who hasn't been part of developing KMX can use tomorrow to have their own system trading up and live trading." (M49)
5. "a baseline with a customizability layer" (M49). "ink a paintbrush and a canvas and let their brain work" (M50). "This is not set in stone." (M50)
6. "the technical lens now carries beyond more than a unit" (M52): "the MIS, SQS, a lot of the breaks, the accelerators... maybe overhauls or enhancements, even QML itself" (M52)
7. "question number five is really more of a pod life question" (M49). "Mini apps are meant to help us... customize and extend the capabilities." (M49)
8. "Why would I have to be there monitoring units?... I could have 200 units... Why not just have an agentic workflow that can cater for that? As a mini app also." (M49)
9. "I don't want just safety. I want something that can like perform" (M33). "Design for complexity. Don't design a complex system." (M8)
10. "Just complete it and make sure it can work. And it's maintainable, please. From a developer's perspective" (M52). "Don't look at the numbers" (M49)

Fixed lines (`BRIEF-COMMON.md:40`): agents never touch money; only he promotes to live; exits are never blocked; only his hand lowers the kill switch; never print keys or tokens. Everything else is open, and a reckless setup must be expressible.

---

## 2. The decision points, by theme

Each decision names the options that exist on disk, with an honest evidence label, what each buys, then the pick. Where the canvas should offer more than one, the pick reads **both, as swappable blocks**, the shipped default is named, and every value stays open. "Default" means what a template ships switched on; a user, pod or copilot changes it without a core change. "Core" means a socket, input, record, hook or invariant the first increment must carry (section 3 lists them all).

### 2.1 The sizer

**D1. What the sizer socket is.**
| Option | Evidence | Buys |
|---|---|---|
| (a) Keep the narrow socket: equity, entry, stop, record in; lots out (`SWAP 1`) | BUILT | Nothing to build; only the placeholder fits |
| (b) Wide `SizerInputs` with an `extra` map (candidate 1 and 3, `H3` section 2) | PROPOSAL | Any base can read anything; the socket grows per idea |
| (c) A sizing base is a derivation producing dollars at risk; one shared converter turns dollars into the instrument's quantity using the record's value per point and lot step (`H2 I2`, `H3 T4`, candidate 2) | PROPOSAL over a BUILT converter (`qml/numbers/convert.py`) | A new base is a block row, never a socket change; "why lots?" answered in structure; the USDJPY fault fixed at root (`SWAP 4.3`) |
**Pick (c), core S1**, widened by REVIEW S13: a base answers a typed amount (money at risk, notional, or quantity) and the one converter reads the type, so a fixed contract count, a leverage target or a no-stop unit have a home. The derivation reads the full fact surface (D2). Lots exist only at the venue step; the wire already says `quantity` (review, Q3), so no word is asked of him, and "why lots?" gets its plain answer on the walkthrough page (section 8).

**D2. What a sizing base may read.** Options: (a) four facts (BUILT); (b) `X2` restructure 3's list: budget share, committed cushion, open risk per bet key, own record (spread of results, edge band, cut distribution, trade rate), cost cell for this hour and world, gap factor, level, trading state, conviction binding (`H2 I13`, `I41`); (c) a thin surface over derivations only (PICK graft 2). **Pick (b), core I1**, with every input timestamped and carrying a declared fail mode (`H4` section 4). (c) and (b) agree only if derivations may read all of it, so (b) is the contract and (c) is a style of block. Today the compiler refuses every sizer input (`compiler.py:930-936`, `SWAP 1`).

**D3. Which bases exist, and which ships on.**
| Base | Evidence | Buys |
|---|---|---|
| Fixed fraction of a declared money base at the stop, costs in the denominator (the placeholder grown; `X2-H39`, `H2 I62`) | BUILT (narrow), REAL as the base every platform ships (`R1` pattern 1) | Trades from the first tick; no edge input, no record needed; everyone understands it |
| Horizon floor-odds, day-sigma budget (`X2-H01/H02`) | MODEL only; zero floor touches partly structural (old F12) | Survival stated as a dial; makes "more units, less each" structural, which he rejected (M49) |
| Risk-constrained Kelly (`X2-H05`, A1-024) | REAL theory, papers read | Spends the whole allowance; needs an edge estimate |
| Cushion above a fixed floor (GitBook ladder, `H2 I14`) | REAL theory (CPPI); the old dollar sim "blocked" it at ten seats and never ran N=1 | Share per trade rises with equity by itself |
| Own full size under a parent limit on losing together (`X2-H29`, `H2 I3`, `H3 T5`) | REAL bank practice (RiskMetrics limit hierarchy) | Each unit keeps a real size; closest to his "two bots use all the 300" |
| Dollars from the unit's realised loss distribution with cuts (`H2 I16`, `X0-13`) | MODEL, with REVIEW M4's caveat on cut winners | FI units size up honestly if the cut catches few winners |
| Conviction step from a unit signal (`H2 I41`) | in-sample | A human's conviction |
| Tail-budget for negative skew (`H2 I29`) | simulation | Protects mean-reverting scalpers |
| Volatility target (`E2` Pod 18) | REAL backtests, failed generalisation (`H2 I33`) | Smooth equity for stop-less units |
| Fixed money per trade (`E2` Pod 19) | trivial | A newcomer's canary |
| Full Kelly, martingale, grid (`E2` Pod 20) | REAL as ruin | Expressible, graded F by the ruin audit, never a default |
**Pick: both and all of them, as swappable blocks on the one socket. Shipped default: fixed fraction of a declared money base (equity, or cushion above a floor the user sets), costs in the denominator, round down, residue real.** Values open: the fraction, the floor, the base; the builder picks labelled placeholders (section 4). Why, as configuration: it needs the least (no edge, no record, no MIS), a person can explain it in one sentence, and every other base is one row away. It is BUILT in shape and shipped by every platform (`R1` pattern 1), which is practice, not proof. It sizes at the first tick with zero history. The horizon formula ships as a second block, off, labelled MODEL; its "safe at zero edge" claim is a numbers-talk argument, not a reason to make it law. The parent-limit mode is the shipped answer to his M49 complaint (D31).

**D4. The level slot.** Options: (a) no level; (b) a level as a fraction of baseline, with a ladder law (holdout start, cohorts up, CUSUM down; old DP15); (c) a level slot with no ladder law; how a level starts and moves is a template or pod rule, and may differ by unit origin (`H2 I77`). **Pick (c): the level is one named modifier on the chain (core S2); the rules are content.** He said QMB's proof setting a starting level is "I think no" (M49) and asked "what exactly is a starting level?". Four kinds of unit arrive (M49); a ladder law forces one validation story on all of them. The cohort ladder, BOIN steps, slow-start titration (`H2 I31`) and his calendar ramp are each a block.

**D5. Feasibility and the smallest size.** Options: (a) skip below the minimum lot and go dark (BUILT); (b) feasibility verdict per unit, instrument and broker, re-run at anchors, with a declared shed rule (`X2-H45`, `H2 I81`, REVIEW M9); (c) raise the share until the minimum fits; (d) lot dither (`X2-H46`). **Pick (b) as a computed, shown verdict (core I17); the shed rule, concentrate, borrow and dither are blocks (content).** The dollar sim's "100 % dark" figure is dropped as a verdict; the mechanism stays because a book that goes dark above the floor is what he called sitting like a duck (M8). Dither is not dropped: a user may want it on gold at small size; the shipped converter never rounds up by default.

### 2.2 Exits

**D6. The exit socket.** Options: (a) first per-bar exit only, fed nothing, `close_full` only (BUILT at tip, `SWAP 2-4`, `E15`); (b) an exit stack: every per-bar exit runs, fed `PositionFacts` (quantity, average price, stop, targets, bars held, MFE, MAE) and market evidence, answering `close_full`, `close_partial`, `amend_protection` with a reason code, the safest winning by a declared rank (`H2 I7`, `X3-H43/H46`, PH slot table) ; (c) exits in the risk profile document, not the unit (candidate 1). **Pick (b), core S3.** Exits stay on the unit, because an exit changes what R means and the logic record must survive a sizing swap (`H3` section 4 rows 8/8b; `E2` round table). Without all three verbs trailing, scale-out and breakeven are locked out, so "later" would be rework (`H2 I7`). Step 3 (trails, partials, the signed stop) waits on the node's partial close and R24's demo facts (`SWAP 9, 10`), and the socket must be shaped for it now. Exits take their own path, never through the entry chain or `decide`; a faulty exit block falls to the next rank, then `_close_scope` (REVIEW S24).

**D7. Which exit mechanisms exist, and which ship on.**
| Mechanism | Evidence | Buys |
|---|---|---|
| Disaster stop beyond a swing or ATR (BUILT placeholder) | BUILT | A floor under every trade |
| Fixed R target (BUILT) | BUILT | A plain target |
| Time exit (BUILT, long-side bug `SWAP 4`) | BUILT | Dead trades leave |
| Fast invalidation cut from the winners' MAE (`X3-H39`, `H2 I70`) | MODEL; no paper tests fractional cuts after costs; REVIEW M4's winner-catch caveat | His scalper's risk management (M7, M15) |
| Thesis-first invalidation with a price backstop (`X3-H40`, `H2 I71`, `H5` idea 4) | REAL paper account (Steward), one window | A named reason on every exit; what agents can be handed |
| Dynamic stop and target rebuilt: breakeven off by default, trailing after a calibrated continuation (`X3-H41`, `H2 I74`) | his April spec, never validated; Gen 3 ratchet built, off path | Intraday's exit, his M15 |
| Stopping premium: stops only where the unit's persistence earns them (`X3-H38`, `H2 I73`) | REAL at daily scale; no intraday cost test | A Lab test that picks the family |
| Survival-hazard, half-life, edge-ratio time stop, scale-out rungs, basket cut, flat-before-close, triple barrier (`H2 I75`) | mostly author backtests; one controlled | Content on the stack |
| No price stop, R from a tail budget (`H2 I72`, PH 11) | PROPOSAL | A scalper with only fast invalidation |
**Pick: all as blocks on the stack; exit families per style are templates (`X3-H43`, content). Shipped defaults: disaster stop, R target, side-correct time exit, plus the scalper template switches on the fast-invalidation cut and the intraday template the thesis exit; breakeven off; trails arrive with step 3.** Every value open. Cold behaviour (REVIEW M4): the cut uses a fixed labelled distance until N winners exist, then the winners' MAE. "Not allowed" cells in the family table read "not advised" (`H2 I69`). R is a declared basis on the row (gross at the disaster stop by default; a no-stop unit declares a tail budget), never assumed (`H2 I72`). Stops tighten only by default; `allow_widen` is a row a template may set, warned, because widening must be expressible even though it is a classic ruin path.

### 2.3 Halts and brakes

**D8. Where brakes may run.** This is architecture fork F1 (section 6). The decision here is only the row contract: every control is one registry row stating what it reads, whose risk, measured from where, which lever, which direction, shape, attack and release speed, anti-chatter, memory, who clears it, counting rule, fail mode, money series, expected healthy fire rate, shadow switch, tail or timing class, and **where it may run** (unit, group stage, off-path) (`H2 I5`, `I9`, `X3-H58`, `H3 T6`, CHECK B9). **Core S4.** A row requires few fields (what it reads, scope, verb, `on_fire`, restore, cold behaviour, shadow switch) and defaults the rest, or a newcomer's brake is a form (REVIEW S19). A new brake is a row plus one folder in the dictionary (PICK graft 7); no new `Kind` (`H3` section 2).

**D9. What a halt may answer.** Options: (a) `none`, `no_new_entries`, `flatten` (PH slot table); (b) add `reduce` with a factor and the five states ACTIVE, REDUCING, BENCHED, HALTED, RESTORE per scope (`X3-H59`, `H2 I58`); (c) stop only, as today. **Pick (b), core S4.** Only stops means every bad day is a stop or the book goes dark while he sleeps (`H2` section 4). HALTED and the kill switch stay his hand. Today `HaltInstance` has no caller and all five shipped halts refuse (`SWAP 5`).

**D10. Which brakes exist, and which ship on.**
| Brake | Evidence | Buys |
|---|---|---|
| `account-daily-loss-halt`, `session-loss-limit-halt`, `session-fill-limit-halt`, `equity-drawdown-halt`, `losing-days-halt` (stdlib) | BUILT, never run in a host | The simplest money brakes, already written |
| Own-percentile money bench over a window in trades (`X3-H01`, `H2 I10`) | MODEL; REAL that firms use money, not counts | Scalper and ORB fire at the same rate |
| His losing-run count brake, scaled to the unit's run length, halve not bench (`X3-H05`, `H2 I46`) | MODEL for the fixed form | His "about three" (M8); he must be told what three becomes |
| Graded ladder: reduce at p10, bench at p1 (`X3-H02`, `H2 I44`) | REAL grid practice; MODEL | Reduce before bench |
| Loss points (`X3-H03`) | October proposal, never ran | A cut costs its size, a breakeven its fees |
| Two-speed circuit breaker: fast half money, slow half fire-record with Basel zones (`X3-H08`, `H2 I48`) | REAL Basel; MODEL | His named baseline brake (M10), alpha decay |
| AIMD: cut hard after a bad day, add a little after a green one (`X3-H07`, `H2 I19`) | REAL in networking; MODEL both ways | Reshapes the tail so a higher base is affordable |
| Burn-rate permit (`X3-H22`, `H2 I54`) | REAL in SRE | Fast burn halts, slow burn sizes down |
| Portfolio day stop reading the book's own sized sigma (`X3-H24`, `H2 I50`) | MODEL | His "switch off entirely" |
| Portfolio breaker on stacked evidence; chorus K of N; losing together counts once (`H2 I51-I53`) | REAL exchange breakers and insurance; no QMX history | Five stops on one release are one event |
| Pod-style step ladder; peer ejection; danger accumulator; changepoint cooldown; execution-anomaly pause (`H2 I56-I61`) | REAL elsewhere; one fair test for changepoint | Pod ingredients |
| Restore family: retry-then-lockout, half-open probes, memory ceiling, earned restore (`X3-H15-H18`, `H2 I59`) | REAL elsewhere (reclosers, resilience4j) | A way back; never his click for routine benches |
**Pick: every brake is a block on the row contract (S4); which binds is a pod or template setting. Shipped defaults (section 4): `session-loss-limit-halt` at unit scope and `account-daily-loss-halt` at account scope, both `no_new_entries`, restore by rule at the next day boundary with retry-then-lockout; the own-percentile bench and the count brake ship in the template, the bench on and the count brake off; the two-speed circuit breaker ships in both templates, present and off, because he named it the baseline brake (M10, REVIEW S1); the portfolio day stop ships as the group's default row with `on_fire: stand_down(all) + card`, expiring at the next day boundary by rule (REVIEW S25).** Values open. Cold behaviour (REVIEW M4): the money halts bind from the first trade; the bench runs in shadow until N trades exist and the session-loss halt stands in; the day stop reads the sum of planned R at the stops until N days of P&L exist. The random-control certificate (`X3-H13`) is a report, never a compile gate (REVIEW M5, kept). The old "one live reader per ledger" compile refusal (`two_live_readers`) becomes a template warning (`H3` section 2, `H2 I44`). The circuit breaker keeps its name.

**D11. What a brake does when it fires, at the portfolio level.** Options: stand-down at a scope; raise a kill level; send a card. **Pick: an `on_fire` field on the row (core S4); each pod chooses (config).** He ruled this a pod question (M49). Only his hand lowers a kill level.

**D12. Scope keys.** Options: instrument and deployment only (BUILT, `runtime.py:1675-1678`); add class, region, currency, underlying, session, family, pod, tag, driver (`X3-H35`, `H1` idea 22, `E2` row 11). **Pick the full set, core S11.** "It can isolate crypto" (M10) cannot be said today. Tags are many-to-many (`H5` idea 18).

### 2.4 Accelerators

**D13. House money and reverse house money.** Options: (a) two rules on two ledgers (old pick, REVIEW M8 found the contradiction); (b) one rule, one cushion ledger of profit since an anchor; a fixed anchor presses and brakes, a running-peak anchor only brakes (`H2 I4`, R9 0.4, Grossman-Zhou) ; (c) drop house money. **Pick (b): the cushion ledger with anchor type, clock and scope as rows is core, one scope of the fold (R9); the rule shape (straight, April's curve, sigmoid) is a block; the press gate is a block (`E2` Pod 4).** He asked not to lose house money (M5) and reverse house money is his idea (M39). Evidence stated plainly: REAL theory; MODEL shows no gain on independent trades and gains only under regimes (R9); `A5-118` records a deep-drawdown tail. **Shipped default: the scalper template switches the rule on with a day anchor, because he asked for it (M5 "I don't think I want to lose the house of money"; M39 "reverse House of Money was my idea"; M50), value open and the switch one row away; it brakes on the way down and presses with winnings only; the intraday template ships it off. No model result chose this (REVIEW M5); the MODEL figures above say only that the mechanism behaves as described.** Cold behaviour: at the day anchor profit since the anchor is zero, so the multiplier is one. His old Q4 ("a rule I approve") is a press-gate block, not a question.

**D14. Other accelerators.** Earned tiers (`H2 I22`, REAL prop rules), press with winnings only (`I18`), persistence press after a block test (`I23`), pyramiding with falling risk (`I32`), calm-volatility scaling with a guard (`I33`), probe for capacity (`I34`), overdose-controlled steps (`I35`), bounded exploration (`I36`), agents breeding profiles in the Lab (`I37`), growth buys breadth (`I38`), QoS lending (`I39`), thermostat (`I40`), goal taper (`I25`), restart after near-breach (`I26`). **Pick: all content, on two seats that are core: the named modifier chain with range and reason on the receipt (S2, `H1` idea 4), and the realised-profit fact (I3).** None is a default. His "carry or amplify the load... a high one will get even a bigger buffer" (M10) is **not delivered by the default sizer**; the seat is S2, and the first block that would carry it is the cushion rule's press half or a persistence press, with no value set here (REVIEW S5). He called them "tools or timber" (M50). The raise permission gate (any brake blocks every raise, `X1-H13`) is a default rule on the group row, not a law: a reckless pod may remove it.

### 2.5 Numbers and self-configuration

**D15. What every number carries.** Options: (a) a fixed value (BUILT for risk numbers); (b) a number spec: derivation (a rule block or a fact), range, authority, owner, reason on the resolved value, cautious direction for missing data, a guard that reverts and freezes after trips, a never-self-tune marker, `applies_to_open_positions`, and a per-change record of before and after (`H3 T2`, `T24-T29`, `X1-H02-H08`, `H2 I12`, `E3-6`) . **Pick (b), core S13, on every number including sizer, stop, target, per-bar exit and halt numbers.** Today motion reaches logic numbers only (`SWAP 2.5`, `_bound_on`). This is "what if I want to change the way it is derived?" made structural.

**D16. How a number moves.** Options on disk, with `E5` section 2's mechanism tests behind them:
| Mechanism | Evidence | Buys |
|---|---|---|
| Learner publishes a target with bounds; a separate applier moves it in the number's mode (VPA model, `X1-H02/H03`, candidate 1) | REAL in Kubernetes; in `E5`'s test (M3) it added machine and little gain | Numbers move between anchors with bands he can see |
| Refresh at anchors only (candidates 2 and 3) | PROPOSAL | Nothing moves unexplained; a day's lag |
| Find, track, correct: replay finds a start, facts track the market live, the built motion engine corrects from own trades, bounded and switchable per type (`E5` 2.4) | MODEL (`E5` tables: S+M1 held across every world tried); BUILT engine for logic numbers | No new applier part; each job uses data suited to it |
| Bandit over approved versions; genome variants (`X1-H48`, `X2-H53/H54`) | papers, no trading test | Lab-side search |
**Pick: core S13 carries the fields and seats that let all four exist: `authority` with a real `off` and `motion_inside_range`, room for non-flat anchors and calendar cadence, a `scaled` mode (fact times multiple), a bounded window on the engine's memory (`E5` 2.1 finding 1: `SlowState.read` is unbounded today), calibrated numbers without a logic stamp, `Origin` "found by replay", report with and without motion (`MotionSwitch` exists). Shipped default: find, track, correct, with per-type presets (correct on for filters, off for size press). The configuration reason: it adds no new part, since the built engine already does the applier's job (`E5` 2.1), each job has an off switch, and a person can say what moved a number and why. `E5`'s tables are cited only as "the mechanism behaved as described and did not run away"; they do not settle fork F2, and its architects may replace this default (REVIEW M5).** The learner-and-applier object is content and one side of F2. The hill climb is a Lab job on long history, counted, ending in a new version, never a live climb on recent trades (`E5` 2.5; MODEL: live climbs stalled or wandered). His "have an agent go at it" (M49) lands there.

**D17. Authority.** Inside a declared range a number moves by its own rule, no click. Outside it is a new version, a counted try, then his promote click. Agents write in the Lab and on cards, never on a running unit; their output reaches a unit only as a fact it chose to read (`E5` 2.4, `H4 I-52`). The never-self-tune list is per template and user-editable (`H3 T29`); the kill switch is the one fixed entry. **Core as fields on S13; the lists are config.**

### 2.6 Costs and facts

**D18. Costs as observed facts.** Options: (a) no cost reaches the unit (BUILT; `reads` refused, no commission key, `MAP` section 4); (b) cost cells per instrument, broker, hour, session and world, written from fills, with an `uncalibrated` label and a stressed, class-pooled fallback that decays to measured; the sizer reads the cell; two residuals kept apart, signal before costs and cost against model (`H2 I8`, `I63`, `H5` idea 26, `X6-30`). **Pick (b), core I2.** It fits his "think of QMX more of as a data analyst... I'm trying to observe them, see what I can do" (M51), which was about observing costs and not trading an instrument on its news day; the per-trade hurdle itself (D26) is `E1`'s proposal, not his ask (REVIEW S6). Facts move live, numbers at anchors (`H3 T25`) is the default timing rule, kept as a mode not a law.

**D19. Where cost enters.** Three points exist: the size denominator, a Kelly ceiling in R, an admission gate at k times stressed cost (`H2 I62`). **Pick: denominator in the shipped default sizer (core I2); the ceiling and the gate are blocks (content); k is numbers talk.** The old REVIEW M4's table stands as the honest warning: at a 5-pip stop the gate refuses his pictured scalper, at 10 pips it passes. The deadlock the new review found (M4): a gate that refuses until fills exist never gets fills. So the shipped hurdle only warns while its cost cell reads `uncalibrated`, and refuses only on a measured cell showing net edge below zero (4.1).

**D20. Account and venue facts.** Live balance refresh, open risk at stops, margin headroom, liquidation price check at entry, leverage change stand-down, conversion market and USD seam, per-world calibration, fill record with decision quote, arrival quote, fill, partial, reject, requote and markout at several horizons (`SWAP 14-17`, `H5` ideas 32-33, 36, CHECK B5) . **Core I3 and R7.** Today equity is the balance read once at sign-in (`SWAP 17`).

### 2.7 Instruments

**D21. One record per unit, instrument and broker; class differences are fields, not branches.** Fields: money per point, lot step and bounds, class, bucket and underlying, book-or-quote flag, tick tier, hourly cost cells, conversion, session clock, day boundary, calendars (session, event, roll, funding), roll rules, commission, margin, leverage, detector calibration (`H3 T15`, `H1` idea 50, `H5` idea 36, `E1` row 17) . **Core I4.** Venue capability (partial close, amend, hedging or netting, minimum stop distance, order types) is on the record and checked at compile (REVIEW S21). Futures mini and micro are two rows (his M50). A test that fails on branching by class in the money path (`E5` 4.2). Which classes are tradable at a budget is a computed, shown verdict (`H1` idea 51); the refusal is a block. Classes themselves (energy, stocks, crypto overlays, tick-size tiers) are content rows.

### 2.8 The MIS and routing

**D22. The shape of the MIS** (`E1` section 3, four designs; `H1` section 3's poles).
| Design | Evidence | Buys |
|---|---|---|
| MIS-1 deeper board: one MIS, tiers, packs filled, units read with fallback | designed (unit plan), partly BUILT | One vocabulary; most already designed |
| MIS-2 open bus: any app, pod or agent publishes a reading in the same record under its own name; units pin publisher, reading, version | PROPOSAL; the record and journal are BUILT | His departments and "mini apps feed each other" (M50); a poor default is replaced, not rebuilt |
| MIS-3 finder: the output is per unit, "where is your claim true now", as an `active-markets` reading | PROPOSAL; his M5 router | His idea directly; a morning list, never per trade (readings take hours to show) |
| MIS-4 two products: an overnight curve factory (usual level per minute of week, as a fingerprinted artifact) and a node stream that divides live by curve | PROPOSAL resting on "now versus usual" | One baseline shared by SQS, MIS and QMB; a dead MIS is safe by structure |
| No central MIS; slow-only; cross-sectional only; per-reading placement rule (`H1` poles) | PROPOSAL | Kept as poles for the architects |
**Pick: MIS-2 and MIS-4 settle the core seats (S8: record `source` open to `app:<id>` and `agent:<id>` and host-stamped, publisher on a read, `valid_until`, inputs named on each record; I6: one curve artifact per world with an age word, marked "if F3=B"). MIS-3 is the first app on top (content). MIS-1's pack list is content filled over time. Every shipped template stands alone: no unit needs the MIS, and a unit may declare `fallback: stand aside` (REVIEW S12). The finder's list is a session or day list by default, because persistence on 1m and 5m takes hours to show in simulation; a per-trade read is expressible and warned (REVIEW S7).** This is fork F3's field (section 6) for where the sensor runs.

**D23. How a unit reads and widens markets.** Options: fixed list; board narrows (BUILT, unwired); active list as a reading over allowed, home as fallback; a card adds to allowed; free (`E1` section 5 ladder). **Pick: the ladder, each rung a setting (config). Core S8 and I5: `reads` compiled with fallback and stale limit; three market lists on the unit, allowed, home, active; the board or list fallback is home markets, not every listed market.** The hazard `E1` found is in the docstring at `runtime.py:366-369`: with a placement set and a stale board the unit trades its own markets; the board is unwired today, so this is not live, and the fix lands before any wide list (REVIEW S32). Records split per unit, market, session and slice (R2), or the router can never be scored.

**D24. His direct question, "how does the MIS adjust?"** It doesn't. It keeps publishing what it sees. A sticker refuses entries at the scope, the finder doesn't list a stickered market, and the router must not place into a stand-down (`E1` section 4, REVIEW item 18). Decision text, never drawn; the walkthrough page should draw it.

**D25. Readings and physics.** The five shipped readings (change point, efficiency ratio, variance ratio, Hurst, spread state) are BUILT on H1 bars and fed closes only (`E1` section 1). Every new reading passes three floors: a named null, a bid-ask bounce test, a use test against shuffled labels (`E1` section 7). All fifteen physics rows (P1 to P15) are content in shadow; `E1` would start with P12 scalpability and P3 liquidity commonality because they pay even if the physics disappoints. Full-bar port, per-card clock, pack parameters reaching blocks, state kept between rounds: content on the app. His "is RVOL catered for?" has a plain answer: a catalogue entry, no block, no reading, because bars carry no volume (`MAP` section 4). Volume on bars is unowned and needs his call (`QUESTIONS.md` Q2).

### 2.9 The SQS

**D26. What the SQS is** (`E1` section 2, four designs).
| Design | Evidence | Buys |
|---|---|---|
| SQS-1 the old rule, moved to the new node as one block in an entry-gate slot, reading a per-instrument curve | BUILT rule text (old node), never run on a venue | His ruling "SQS stays"; a clear fact; first live entry waits hours for a baseline |
| SQS-2 cost hurdle: at this quote, with this stop, does this entry clear what this unit allows for costs, in R | PROPOSAL; REAL on the shape of costs (NBER hourly spreads) | Scalper and ORB get different answers on the same instrument in the same second, with no style code; no warm-up; his M51 frame |
| SQS-3 fillability bank: spread against usual, tick rate, quote gaps, micro range, recent slippage, markouts | author backtests; "safety filters can screen out winners" | Catches liquidity leaving before the spread shows it |
| SQS-4 cost dial: size steps down as live cost climbs, blocks only past a hard line (`X2-H42`) | author backtest, NQ; conflicts with "never shrink" (`X3-H63`) | Keeps trading in costly minutes |
**Pick: all four as blocks. Core S6: the gate slot is one link of the entry chain, with a verb list (block, shrink, wait, warn, shadow, none) receiving market, side, quote, stop, the unit's cost allowance and cost cells; the node-side sensor for spread, tick rate and quote gaps (source `node`) and the one curve artifact (I6) are marked "if F3=B"; exits bypass every link by contract test. Shipped default: SQS-2 as the gate, SQS-1 as the floor for broken markets; SQS-3 in shadow; SQS-4 off, on the modifier chain. The configuration reason: the hurdle needs the least (a live quote and the unit's own stop, both known at tick one), it is explainable in one sentence, and it is one row from off; it fits M51's observe-then-act frame, which did not ask for it (REVIEW S6). Cold behaviour: it warns while its cost cell reads `uncalibrated` (REVIEW M4).** Values (allowances, floor lines, the eight old settings) are numbers talk; the builder picks labelled placeholders (section 4). `sqs_baseline_producer.py` and the rule text must move before repair's C-20 deletes them (`SWAP 4.3`, old DP25).

### 2.10 Isolation and news

**D27. One mechanism for isolation, news and caution windows: stickers and tolerations** (`E1` section 4). A sticker is a record in the stand-down table: scope, kind (`news`, `open`, `fix`, `isolation`, `unknown`, or any publisher's name), strength (prefer not, no new entries, flatten), expiry and resume rule, why and who. Each unit, pod or template lists the sticker kinds it ignores. **Core S10.** Each sticker source has a `fail` row; the default is a card and `prefer not`, never a silent block (REVIEW S17). It dissolves four collisions at once: ORB allowed where a scalper is blocked; news units against a global news window; a fix-reversal unit against a caution window; "is this a pod question?" (yes, M49). The kill switch is not a sticker and cannot be tolerated. An agent-placed sticker can only reduce risk and must expire. A sticker table the node cannot read reads as `unknown` for that scope, so "unknown is not calm" (`X3-H36`) holds without touching the board's fail-open.

**D28. Who may place an isolation.** A rule on two different tells (`X3-H28`, `H1` idea 23; daily-data author backtests, no intraday precision), an agent card de-risk-only with expiry (`X3-H34`, `X7-H21`), a person typing. **All config; the rule is a pod block; shipped default: no isolation rule binds; the SQS floor's block counts across a class are published as a reading (content).** Every isolation writes whether a loss followed, with blocked trades as would-have rows (a query over R3 and S10; content). "No public source on a fund switching off one class by rule" (R2): say so on the block.

**D29. News.** Calendar events carry driver tags (both FX legs, home exchange, region, commodity) and become stickers; strength from the calendar's tier until measured impact replaces it; a stale calendar fails closed; blocked minutes reported as a cost; re-entry on spreads and depth, not the clock; a velocity tell backstops a missed release; news units tolerate the sticker and read an event clock (`X0-39`, `H1` ideas 30-35, `E1` section 4). **Core I4 (tags), S10 (the sticker and the toleration), I7 (event time as a clock). Content: widths, measured impact, the agent event mapper. Shipped default: both FX legs tagged, scalper template tolerates none; a stale or dead calendar lands a card and reads `prefer not`, so a dead free feed cannot park every unit (REVIEW S17).** The kill switch keeps the hard kill (his C28). This session claims `qmn/data/news_calendar.py`, `qmn/protection/windows.py`, `dispatch.py` and `qmf-risk/control_window` before deletion (old DP24, kept).

**D30. Sessions, opens and sniping windows.** His "is ORB the sniping period?" (M8): no, different kinds of thing. ORB is a logic; an open is a window; a sniping window is a Library artifact saying one unit family on one instrument does better in one slice (`E1` section 4). **Core S9 (`sessions` compiled, a window card kind with slice, family, how found, try count, expiry, status `hand-written | shadow | proven`, a window object any unit can declare and pass or refuse) and R2 (the per-session record split). Content: deterministic finding from the curves, agent nomination with counted tries, hand-written windows.** A hand-written card trades without anyone proving it first: that is the canvas, and the record then speaks. Research says windows lower cost or raise activity and do not hand out edge (R2); his gold belief is parked for the numbers talk, not settled here. Caution widths at opens are measurements, no number set.

### 2.11 Capital sharing

**D31. How units share capital.** Options: (a) each of N units gets 1/√(N(1+(N−1)ρ)) of its solo size (old DP9; MODEL; his M49 complaint); (b) his literal split: total day capital over N (M10; his words); (c) own full size under a parent limit on losing together (`X2-H29`, `H3 T5`; REAL bank practice); (d) a few best units until capital allows volume (A1-083, M50's best basket; PROPOSAL); (e) guaranteed share plus burst from idle slack, QoS lending (`X2-H30`; REAL in Kubernetes); (f) poker-band pots (`X2-H37`; practitioner lore); (g) stage switcher that swaps the sizing rows at an anchor (`E2` Pod 9; his "at 5,000 the math changes"). **Pick: the split rule is a named allocation mode on the group or pod (core I10); every mode is a block (content). Shipped default: (c), own size under a parent limit.** His two statements, "more units less each" is wrong (M49) and "total daily capital split across units" (M10), are both his; a row dissolves the clash and he never has to choose in the abstract. Budget share travels with the deployment (I3), so paper sizes from its share of live equity, never the demo balance (`X2-H50`). A pod may change a member's sizing rows at an anchor without a new unit identity **only under S14's rule**: moving a live deployment to a new pod version is the owner's click bound to that pod's hash (REVIEW M2); without the click it is a draft. The seat rests on "at 5,000, the math changes" (M51), which he asked to keep aside (HIS THOUGHT), so it stays only with the rule (REVIEW S3). Cold behaviour of the parent limit: a fixed labelled limit until N days of co-movement exist.

### 2.12 Group and pod level

**D32. What a pod is, in words.** Corrected against the running demo (`round-2/UI-LOOK.md`), read as a picture of his intent at the time, not a spec; the design is outdated and his notes propose changes, and his later words win where they differ. On his screens a pod is one thing: a stack of blocks (the Lab's bench shows seven slots) plus its money and its members, on one account or venue, with a live side and a paper side (the Portfolio card: name, Live or Paper, money, day change, method, place, bots). Methods live side by side on those cards (the demo's names: Book + BMS, Model, Workflow, Hybrid, Simple rules), so the pod owns its sizing method and "Book + BMS" is one method name, not a word to retire (REVIEW S8). A watcher is a mini app ("Weekend watcher: 4 pods inside their lines"). "Pod version" names the stack's version. "Desk" or "department" is his hedge-fund sense, said as "I think" (M51): a mini app or several with agents, separate from the pod. **Default vocabulary: pod, pod version, method, desk (his "I think", `QUESTIONS.md` Q3). Nothing retires. No slot list or block name on the demo binds a row of section 3.**

**D33. How a unit and a pod relate.** `E2` (b)'s five ways; fork F1 (section 6), open. The demo's intent adds three things (`UI-LOOK.md`, his words winning where they differ): the pod owns its sizing method, so a unit in a pod takes the pod's stack while a unit alone needs its own; a pod with money and members needs pod-level numbers, so the fold is keyed by pod (R9); a size trail walks one sample trade block by block, so there is one evaluator and a receipt per step (S15, R1). What every way needs (core S14, marked "if F1=B" where it presumes the split shape): an optional pod reference on the deployment where an empty pod means the unit's own blocks; the deployment key includes pod and side (live or paper); two fingerprints, logic and pod, so a pod edit never re-proves 200 units (`E2` row 3, the largest rework risk named); placement on each block row; slot composition rules as data; a group stage as one link of the entry chain (S6), called on the node and in QMB; one fold by scope including pod (R9); would-have rows under any pod (R3; the round table's finding: a guard changes which trades happen, so the logic record depends on it); the demo's "Every pod needs this" on the kill line as a template warning, never a compile refusal. **The rule (REVIEW M2): moving a live deployment to a new pod version is the owner's click bound to that pod's hash; one click may cover many members; agents and the copilot write drafts only.** Exits stay on the unit; a unit template carries exits, a pod reference and presets together (`E2` (c)); whether a pod may swap exit rows at an anchor is fork F5's open edge. If the pod idea stops making sense under the architects' pens, a new shape is allowed; Appendix E lists it as an overhaul he will go through.

**D34. Pod configurations.** `E2` (d)'s twenty (Relentless, Session relay, Classic Book, Cushion pair, Old pair, Scalper first, Human mimic, Best basket, Stage switcher, Prop rider, Earned tiers, Multi-manager, Capped total, Run together, Futures desk, Model hybrid, Watched by agents, Volatility core, Canary, Full press) plus R9's eight brake-accelerator pairs. **All content: the pod gallery.** None has run. The `n:` blocks they name are the first content list for QML growth (D45). His M49 ask for "pod ideas or configurations" is answered by this gallery and the walkthrough should show it.

**D35. Book and BMS.** Options: keep as documents (A4-092); tags plus one portfolio config (`X1-H40`); a `group` document with `display_name` and `parent` reserved (candidate 2). **Pick: the group document with `parent` and an allocation mode, and `tag:` as a scope key (core I10); the structure itself he said "decide later" (M49), so no question now.** "Book + BMS" stays as a method name (`UI-LOOK.md`), "Classic Book" as a pod template; nothing retires (REVIEW S8).

### 2.13 Mini apps and shipping

**D36. How a pod or template ships.** `E2` (e): four levels, a document, a document plus blocks, a mini app carrying pods, a desk. A saved thing stores only what differs from its preset plus each block's pinned version (`R1` 4.2, `H3 T9`). **Core S16, all missing today: a host-level `library-items` lander that lands static content at publish (an app names one lander, only `qmb-run` registered; `E2` rows 1-3); a declared `library/` folder in the pack; real `pod`, `pod-block` and un-retired `template` kinds (shells today, `SWAP 31`); a row that saves a block (`SWAP 2.2`); one block catalogue, with form and graph pod-blocks compiling to a QML block (`H3 T39`); pin, diff and lineage on each unit and pod; a forwarding map for block versions. Content: `requires` between apps, subscriptions, the file extension (`.unit`, `.qmxpod`, his "I don't care"), the `build-pod` skill.** The money rule holds: nothing an app lands reaches a node except what the host compiles from landed, checked items with his promote click.

**D37. Mini apps feeding each other, and reaching a unit.** Roads A (artifact feed) and B (Library landing as event) are BUILT; C (proposal to a pod) is partly there; D (a published reading reaching a unit's `reads` with age and fallback) is not built (`E2` (e)). **Road D is core (S8). A stopped desk stops nothing: every shipped template keeps trading on home markets, and a unit may declare `fallback: stand aside`.** His futures week (`E2` walk) cannot run yet: it needs a futures route that has no owner (Q2), `roll` compiled (3.8), a methodology that does not exist, a copilot that cannot take raw video (M51), and the agentic upgrade. The roads carry it when those land (REVIEW S10); the desk itself is other session.

### 2.14 The Lab

**D38. One evaluator for Lab and live.** The conflict: Lab AD-10 makes `qmx_lab.pods.simulator` the one evaluator; the fold says the Lab runs the guard package on a replay port; AD-11 compiles pods to Book and BMS with `unsupported_blocks` (`H3 T38`, `E2` (f)). **Pick, core S15: first widen and extract the handler QMB and the node already share (`UnitSliceHandler`, `SWAP 2.5`, `2.6`) so the Lab, paper and replay drive the same one, rather than a second core beside it (REVIEW S19); state passed in and returned so "pure" and `block_state` are both true; four drivers (node live, QMB, paper, Lab replay); a conformance tape through every driver in CI; `unsupported_blocks` replaced by the needs list; the size trail equal to the decision row (R1); compile target = the pod document plus `qmx.unit/1`; exits never pass through `decide` (REVIEW S24).** What may differ: fills, costs, latency. Never the arithmetic. Resize replay is for exploring, a QMB rerun for evidence (methodology hand-off). Lab-born units need no QMB card (`H3 T7`). Lab pods on a model's surface, the Pods bench and the copilot's Lab tools: other session (UI, agentic upgrade).

**D39. Lab tools worth a seat.** Resize a recorded trade list under another sizing rule (`H2 I1`, QuantAnalyzer, REAL as a product): the trade-row fields are core (R2), the tool is content. The chassis stress battery as a CI test, adding walks for pod, mini app and Lab-born unit (`H3 T19`): content, cheap, direct test of "handle any amount of stress". The family ledger counts every try, identity vocabulary shared between Lab and unit (`H3 T41`): on I9.

### 2.15 Identity and versions

**D40.** Spec and status with separate writers and a generation stamp (`X1-H01`; REAL in Kubernetes); identity table wired, with a forwarding map so `fixed-fraction-at-stop@1` to a real sizer is a declared migration and a unit keeps its record (`H3 T49`, `SWAP E16`); two records, logic in R across versions and money per version (`X1-H44`); pins plus diffs plus lineage (candidate id, hash, parent, family, data and cost versions, hypothesis as a scoreable claim: metric, benchmark, window, `E3-1`); plan before change, refused if stale, with his click bound to the exact hash, level, markets and date (`X1-H46`, Terraform); a rollout field (shadow, canary, full; analysis rules are methodology's); upgrade offers never silent; a self-test card per version; a rip-out check that placeholders and dead versions cannot linger (Knight Capital, `H3 T54`); migration of stored shapes and config-effective timing (BUILT upgrader chain). **Core R17 (identity and swap: the table wired, the forwarding map, which swaps keep which record, what governs an open position during a swap, what old rows mean after a field changes), K5 (plan before change; the click bound to a hash and to a pod version), I9 (the generation stamp; family, parent and a claim as metric, benchmark and window). The rollout field, the self-test card, offers and canary analysis are content: additive, no rework (REVIEW S18). The rip-out check is a test under K9.**

**D41. Compiler bumps.** Corrected by the review (M1). The format bumps only when a compiler change alters a decision (`compiler.py:100-101`); lifting a refusal alters no decision for a unit that compiled before, and the format already bumped in R04, R05 and R06 at no cost. The cost exists only for deployed units (`runtime.py:559-565`, `:2756`): each bump then means a new test record per deployed unit. No unit is deployed today. **Sequencing note, not an invariant: bumps are free until the first unit deploys, so sockets land in slices; bump only when a compiled decision changes; step 3 (trails, partials, the signed stop) lands before the first deploy or pays a re-test. The re-test workflow (K8) is core, because its absence is what would freeze the compiler later.** Block-entry fields that linking needs (D45) move no compiled fingerprint: `block_fingerprint` hashes `block.py` only (`loader.py:81-83`, per the review), which closes that UNKNOWN.

### 2.16 Records and observability

**D42. The rows.** Decision row that replays: inputs with timestamps, every resolved number with its reason, each step from wanted to approved to filled, the binding clamp named and counted, version and compiled fingerprint, readings seen with source, age and version, gate verdicts, `propensity` when a paper twin took a logged random share of refused entries (`E4 L04`), newly-active market mark, numbers in force, placeholders used. Trade row v2: net and gross R, costs by kind, exit mechanism and reason code, MAE and MFE with the bar path, session, slice, cost cell, world, stage, contract month, markout, `counts_toward_proof`, audit flag. `would_have` and `risk_event` rows written, not only declared (`SWAP 25, 29`). Fill record (D20). Calibration rows (BUILT). Expectation at birth with the version: trade rate, spread of R, streaks, from replay (`E5` 1.8). Root-cause key and event id on stand-down, risk event and order-failure rows. Run stamp: real-tick share, quote source, gate settings, costs (`H5` idea 37). Link record and arm fields on run records (`E4 L02`). Three positions side by side: intended, risk-approved, executed. One trace id from reading to fill. Requested, enforced, observed (`X6-09`). `RiskState` as one fold over journals keyed by scope including pod and tag, with a state word, a stamp, a reason and UNKNOWN when stale (`X6-01`, `X6-11`). A fleet read: one query over all units. Closed reason codes as appendable data rows, with new code families for user-added blocks. `explain_size(row)` as one pure function used by developer, copilot, UI and triage alike. **Core R1, R2, R3, R4, R7, R8, R9, R13; the incident key and alert fields on R4.** Lineage beyond family, parent and claim is methodology's; the expectation at birth is content (additive). Meters, scorecards, the six words on screen, alert tiers, the morning card, the dark cockpit: content or UI session.

### 2.17 Agents' doors

**D43.** Three surfaces: read rows carry state and receipts; proposals are typed, expiring, scoped, with evidence, direction on every operation; runs in a sandbox are unlimited because they cannot touch money (`X7-H01`, `H4 I-50`). Evidence intake declared per unit: kinds accepted, largest cut, time to live, style scope, fail mode (`H4 I-52`). A protected field list no agent may write (`H5` idea 38). The promotion and live-money door runs through a channel the copilot and agents cannot read or reach, including his email and any code sent there, and the click binds to the exact effect (`E3-26`: ten frontier models raised their own spending caps by harvesting one-time codes; REAL tests outside QMX). A block-save door with a contract test (`H3 T57`). Agents never grade themselves (`H5` idea 4). **Core K2 (the read and propose doors, with the app read door and card path) and K5 (the money door and the protected field list). The sandbox is unlimited on paper; the fixed line is about a live account (REVIEW S14). The jobs (triage, coroner, drift explainer, sitting-duck advocate, prospector, isolation cards, per-class agents, shepherd, self-improvement) are the agentic upgrade's, listed in section 8.** Open: whether an agent's cut that applies itself inside a pod's declared bounds crosses "agents never touch money" (`E2` Pod 17, `H2 I95`). Default while open: a cut-only fact a unit's own rule reads, inside bounds the pod declared, with expiry; raises, placement into new markets and anything that lowers a kill level are cards. It is in `QUESTIONS.md` as Q4 because it is the meaning of his fixed line.

### 2.18 Fleet watch

**D44.** `E5` section 1, with its census: the shipped decay job would send about 91 cards a night for 200 healthy units (MODEL on made-up units, rule copied from `read.py`). Options: per-unit thresholds (BUILT shape); scripts keep one ranked row per unit, an agent reads the top K plus each new incident, two lists (rank, which can never false-alarm, and a strict bar under one fleet false-alarm budget), family pooling, one incident one card, four tiers to him (`E5` 1.2-1.5; `H4 I-33/I-34`, `H5` ideas 2-3, `E3-25`). **Pick (lead ruling, REVIEW M7): this build ships a scripted fleet watch, one ranked row per unit, no agent, as workflow templates with a thin face, and switches off the shipped decay rule's nightly card per unit at the same time (4.1, Fleet row). Core: the app read door over journals and the fold and the card-landing path to "Needs you" (K2), everything the unit must publish (D42), a free type tag and family id on every row (I9), and a group-level place for an alarm budget and a share cap (I10).** Agents on top (triage, coroner, advocate) are the agentic upgrade's. His "as a mini app also" (M49) is the ask; the demo's watcher apps show the same intent (`UI-LOOK.md`). `E5`'s correction to `H4 I-34` stands: at 200 units a strict bar slows demotion by 30 to 135 % for active styles, not tenfold; slow units cannot be judged alone and the screen must say "too thin to judge".

### 2.19 QML growth

**D45. Roles and fields.** Roles that must run for any of this to bind: `sizing_modifier` (22 blocks claim it and cannot act, `H3`), `veto`, `cooldown`, `invalidation` (extended to a condition watched after entry, `H5` idea 4), `re_entry`, `arming`, `timeout`, `regime_detector` (`SWAP E2`). New roles the baseline's own parts use: `derivation`, `combiner`, `restore`, `guard_statistic`; `proposal_validator` and `applier_mode` when a block needs them (`X1-H67`, `H3 T12`). Block-entry fields for safe linking: `output_meaning` (a score piped into a sizer is nonsense), `assumes`, `null` (scheme, block length, draws), `evidence`, `retest_by`, `knows_at`, `decides` (`E4` 8b). A face check on the sizer slot (a trigger compiles there today, `SWAP E8`) and limits in one place. Library-only blocks enrolled in the contract tests (`SWAP E11`). **Core S12 (the roles), S1 (the face check), S16 (Library blocks enrolled, the save door). The block-entry fields are content: additive, and they move no compiled fingerprint (REVIEW S18).** Three faces per block, the dictionary expansion (M38), recipes and the seven joints as copilot vocabulary (`E4` section 3), the `build-unit` skill rules in `E4` 8d: content, early. QML stays the SDK: agents' ideas reach QMX as units in QML; Python only for what QML can't express (M50, `H4 I-79`).

### 2.20 The Python path

**D46.** Three doors on disk (`H3 T20`): a block in the Library, checked deny-by-default and pinned by fingerprint (BUILT loader, no save row, node path UNKNOWN); a trust ladder with a minimum per slot and his signature on money-path pins (PROPOSAL); a quarantined `plain_python` hatch (refused today). **Core S16: the save-and-contract-test path, the loader's signature check, and a traced end-to-end run of a Library block through `unit_new`, QMB and a node deploy (UNKNOWN today, `SWAP` section 3). Trace it first: the promise "one folder, zero core edits" rests on the Library path, since a stdlib block bumps the money app and needs his signature (REVIEW S27). Content: the trust ladder's levels, the hatch, expressions compiled to blocks (`X1-H09`).** Only signed `qml` and `human` blocks size live is a template default, not a law.

### 2.21 Order path and netting

**D47.** Intent kept separate from placement so netting can come later (`H5` idea 31; `X1-H74`, `X2-H43`): core S18. Order type on the intent (market only today, `SWAP E14`): a field on S18, limit and stop entries content. An entry-timing offset so 200 bar-close units do not queue at the same crowded second (`H5` idea 34): a field on S18. Target rests at the venue or the node closes: a sub-choice of fork F5 waiting on R24. Partial close on the node (refused, `SWAP 10`): widened in S18. Two units on one netting symbol (refused at host time, `SWAP 21`): shared protection and attribution become a setting on S18. The signed stop distance (`SWAP 9`): repair's, blocking step 3.

### 2.22 Multi-position

**D48.** `position_limit` of one per market is a compiler law today (`SWAP E4`). His A8: a unit may hold more than one position where its type allows (M7), and not every scalper should (M8). **Core S17 (the limit lifted per market and per open; "flat" per market and per position for anchors, `E5` 2.4; more than one stream) and I9 (bet key, driver tag and family tag on every intent).** Pyramiding with falling risk and baskets are content on this seat. The target-position answer type (`E4 L07`: position as a curve of price and time) is reserved on S3, because it needs a per-bar sizer call and partial closes (step 3) and would otherwise be a rework (REVIEW M6); multi-leg orders have no shape and are flagged, not required (`H1` section 4).

### 2.23 The newcomer path

**D49.** `E5` section 3's walk, 17 gaps, six of them this session's (G8 to G11, G13, G16). **Core K7: the rehearsal walk runs on a store with zero trades and zero fills, from template through check, backtest and promote to paper, to a filled entry on the fake broker, one row in the fleet fold, and the account owner's promote click on the fake broker's live lane (REVIEW M4, S4). The templates and defaults are section 4; a first day that needs no broker for history and replay is G8, UNKNOWN, and if the answer is no it becomes a row.** "Tomorrow" is honest as: day one on history and replay; day two on paper with a broker, because cTrader's approval takes about a day (`E5` G6). Installer, launcher, desktop app, first-run ticks, model sign-in, persona wording for a stranger: release, UI and agentic upgrade (section 8).

### 2.24 The developer path

**D50.** `E5` section 4 and `H3 T71`. **Core K9 (the contract tests in order: same decision in both hosts by socket; exits never blocked as a property, a faulty exit block included; every refused field running, refused with a reason, or labelled, the census extended to `authority`, `reads` and every row of 3.8; every number has a reason and range at check; motion range, step, flat and bounded state with a shuffled-outcome control; every template reaches paper on rehearsal; no agent path to money by tool table; `RiskState` from one fold in every reader; a known-answer cost check per engine or cost block, `E3-5`), R1 (the decision row that replays, `explain_size`, one trace id) and S1 (the face check). Content, scheduled with the swap because its builders need them first: the module map with one statement per risk module saying which of the two risk worlds (`qmf-risk` old modules, QML blocks new) it belongs to and a plan to subtract what the swap retires, and the generated `EXTENDING.md` with a staleness test. Bumps: D41.** Observability stack choice (Prometheus and Grafana against OpenObserve) is his later, with a note that risk rows are evidence and may not be dropped; retention at scalper rates is unmeasured.

---

## 3. THE CORE LIST

The test: what must the core carry so the rest never forces rework? Sockets, inputs, records, hooks, invariants. Nothing here is a value or a policy. **This list is the whole core.** Stage 6 builds from this section and section 4 alone; anything called core anywhere in this file or in `FATES.md` names a row here, and a script checked that (Appendix D). The fix round (REVIEW M3, S18) merged rows that were one mechanism and demoted rows that are additive later; 3.7 lists both, so nothing is lost. Live rows: 16 sockets, 12 inputs, 9 records, 5 hooks and proofs, 9 invariants, 51 in all. Merged ids stay as pointers so earlier references resolve.

**Fork marks.** A row marked **if F1=B** (or F3=B, F7=one chain) presumes one shape of that fork. An architect drawing another shape may strike the marked part and must say what replaces it. Unmarked rows hold in every shape.

**Today's state words.** BUILT: runs at the tip. NARROW: runs for one shape, refuses the rest. STUB: declared, no caller or no writer. REFUSED: the compiler names it as not built. MISSING: nothing on disk. The placeholder column names `PH n` rows and `SWAP En` rows the item swaps or widens. Code lines are as `SWAP` and the review report them at `255f3bbf` and `351e7521`.

### 3.1 Sockets

| # | Socket | What breaks if missing | Today | Swaps or widens | Arrives later on it, no core change |
|---|---|---|---|---|---|
| S1 | **Sizing base and converter.** A base answers a typed amount (money at risk, notional, or quantity); one shared converter reads the type and the record (value per point, lot step) and spells the venue's quantity; a face check on the slot; the size band and per-trade cap in one place | Every new base is a socket change; lots leak into design; the USDJPY fault returns; a trigger compiles as a sizer and 5,000 lots passes; a fixed contract count, a leverage target or a no-stop unit has no home | NARROW (`SWAP 1`, `E8`, `E9`) | PH 1, 12, 30 | Every base in D3 |
| S2 | **Modifier chain.** Named modifiers on the sizer, each with a range and its reason on the receipt; the level is one named modifier, with no ladder law; the `sizing_modifier` role runs | Hidden multipliers, or none; the old handbrake unseen; one validation story forced on four kinds of unit | REFUSED (`SWAP E2`) | PH 1, 22 | Cushion pair, tiers, AIMD, cost dial, window lift, calm scaling, context readings, every level rule |
| S3 | **Exit stack.** Every per-bar exit runs, fed `PositionFacts` (quantity, average price, stop, targets, bars held, MFE, MAE) and market evidence, side-correct; three verbs (`close_full`, `close_partial`, `amend_protection`) with reason codes; a declared rank; a target-position answer type reserved (curves and ladders need a per-bar sizer call and partial closes, step 3); exits take their own path, never through the entry chain or `decide`; a faulty exit block falls to the next rank, then `_close_scope`. A unit-scope exit (close all the unit's positions) is allowed once S17 lifts the limit; an account-scope close is a control verb (S4), not an exit | The dictionary's closing mechanisms stay dead; trails, partials, breakeven, FI and thesis exits locked out; a time exit, a signal and a cut all read `close`; curves arrive as a rework; a faulty exit blocks an exit | NARROW (`SWAP 2-4`, `E10`, `E15`); six shipped exits refuse by shape; `timer()` builds long-side | PH 2, 3, 4, 9, 10 | Every family in D7; step 3 once the signed stop lands |
| S4 | **Control rows.** One registry row per brake, accelerator or restore. Required fields: what it reads, scope, verb (`none`, `no_new_entries`, `reduce(factor)`, `flatten`), `on_fire` (stand down at a scope, raise a kill level, send a card), restore (rule or hand), cold behaviour `until_n` (warn, shadow, or a fixed labelled fallback), shadow switch. Defaulted fields: attack and release, counting rule, fail mode, money series, tail or timing class, expected healthy fire rate, placement (unit, group stage, off-path; **if F1=B**). Halts bind at position, unit, account and group scope; five states ACTIVE, REDUCING, BENCHED, HALTED, RESTORE per scope; a settle hook for RESTORE; a host computes the statistics rows read; the protection-escalation row (`close` or `alarm` after failed placement; `hedge` is content) | Five shipped halts useless; only stops exist, so every bad day is a stop or the book goes dark while he sleeps; each brake is custom code; "5 % drawdown" means four things; a pod cannot choose an action; a newcomer's brake is a form; cold starts read data that does not exist | REFUSED, STUB (`SWAP 5`, `19`, `23`, `24`) | PH 5, 18, 19, 20, 23, 24, 28 | Every brake and accelerator in D10 and D14 |
| S5 | merged into S4 (the registry row is the control row) | | | | |
| S6 | **Entry chain.** One ordered chain for every new entry, where each link answers pass, shrink or refuse at a scope and writes its verdict on the decision row: the entry-gate slot (verbs block, shrink, wait, warn, shadow, none) receiving market, side, quote, stop, the unit's cost allowance and cost cells; stickers (S10); kill-level effects read by entries; the group stage (**if F1=B or C**) passing the intent, open risk across members, bet keys and group facts, called on the node and in QMB; the order-boundary veto (margin headroom, worst-step reserve, size sanity band, order rate, venue stop provable, or a declared no-stop basis per I13). Both hosts call one seam; one wrapper so no link's failure can stop an exit; a hung link refuses entries only. **If F7=one chain**: an architect may draw several seats instead | SQS hard-wired, the shape he objected to; a per-trade cost check cannot exist; a guard failure stops exits (CHECK B3); pods stay paper; entries ignore the kill table; the one move that ruins passes every brake; a runaway unit | `guard` has no spread check; hook stub on the node, none in QMB; the protection gate `runtime.py:1102-1106` refuses a stop it cannot prove; entries ignore the effect table (`SWAP E7`, `6`, `11`, `14`, `18`) | PH 6, 11, 14, 18, 21, 27 | SQS-1 to 4, five execution gates, parent limits, chorus, portfolio stops, feed-gap alarm |
| S7 | merged into S6 (the group stage is one link of the entry chain) | | | | |
| S8 | **Readings bus.** `reads` compiled with publisher, fallback (compute here, treat as absent, no new entries, stand aside), stale limit and `valid_until`; record `source` open to `app:<id>` and `agent:<id>` and stamped by the host, never by the writer; inputs named on each record; agent evidence is a reading with the unit declaring the kinds it accepts, the largest cut, time to live, style scope and fail mode; a published reading reaches a unit through this path and nothing else (road D); `context_needs` for a second instrument with aligned clocks | No reading reaches a unit except by embedding a block; departments cannot publish; any app can forge `source: app:mis`; agents have no path during trading, or a command path; lead-lag links impossible | REFUSED (`compiler.py:900-912`), enum of two, relay unwired (`SWAP E1`, `E6`) | none | The MIS board, the finder, every mini app reading, physics rows, agent evidence kinds, lead-lag |
| S9 | **Sessions and windows.** `sessions` compiled with the record's clock; a window object any unit can declare and pass or refuse; a window card kind (slice, family, how found, try count, expiry, status `hand-written`, `shadow`, `proven`) | Windows, opens and sniping slices cannot bind; intraday cannot go flat before the close; sniping windows have no home | REFUSED (`compiler.py:904`, `SWAP E6`) | none | Caution windows, ORB per open, hand-written windows |
| S10 | **Stickers and tolerations.** The sticker record (scope, kind, strength `prefer not`, `no new entries`, `flatten`, expiry, resume rule, why, who) in the stand-down table; `unknown` as a state; a `fail` row per sticker source, default a card and `prefer not`, the kill switch keeping the hard kill; tolerations per unit, pod-overridable; stickers that expired while the node was down are settled by the catch-up rule (R9) | All or nothing; a rigid news rule; a stale feed reads as calm; a dead free calendar silently parks every template unit | Stand-down table with instrument scopes only | PH 15, 18 | Isolation rules, news widths, opens, agent de-risk cards |
| S11 | **Scope keys.** Instrument, deployment, unit, family, class, region, currency, underlying, session, pod, tag, driver; tags many-to-many | "Isolate crypto" cannot be said; one incident is twenty cards; failure domains cannot overlap | Two keys (`runtime.py:1675-1678`) | PH 18, 20 | Every scoped rule |
| S12 | **Roles.** Run `veto`, `cooldown`, `invalidation` (a condition watched after entry), `re_entry`, `arming`, `timeout`, `regime_detector`; add `derivation` and `combiner` | Gate, Scale and Switch joints impossible; thesis exits unjudgeable | REFUSED (`SWAP E2`) | PH 7 | Linking recipes, physics gates |
| S13 | **Number spec and motion.** On every number, including sizer, stop, target, per-bar exit and control numbers: derivation (a rule block or a fact), range, authority (`off`, `motion_inside_range`, anchors including non-flat and calendar), owner, reason on the resolved value, cautious direction, guard and freeze, never-self-tune marker (per template; the kill switch is the one fixed entry), `applies_to_open_positions`; a `scaled` mode (fact times multiple); calibrated without a logic stamp; a bounded window on the engine's memory; motion rule inputs and constants (`min_trades`, `shrink_k`, cadence) editable; `Origin` found-by-replay; a per-change record (before, after, did it do worse); report with and without motion (`MotionSwitch`). A blank warns; a template may demand a value before its owner's live click | Self-configuration has nowhere to live; a moved number touches open trades; the engine's memory grows without bound; "how it is derived" stops at `{strength, r}`; the learner cannot be judged | NARROW (logic numbers only; `SWAP 7`, `8`, `2.5`, `E12`, `E18`; `engine.py:124`) | PH 7, 8, 22 | Learner-and-applier object, bandits, pooled priors, hill-climb jobs |
| S14 | **Pod document and placement.** An optional pod reference on the deployment, an empty pod meaning the unit's own blocks (**if F1=B**); the deployment key includes pod and side (live or paper), so a second deployment of one unit version is allowed; two fingerprints, logic and pod; slot composition rules as data (sizer picks one, throttles multiply or a declared combiner, caps lowest, guards worst state, inputs union); placement per block row (**if F1=B**); the pod owns its sizing method, and more than one method may exist side by side (the demo's intent, `UI-LOOK.md`; its method names and its seven slots are examples, not a list that binds); a unit in a pod takes the pod's stack, a unit alone its own; the demo's "Every pod needs this" on the kill line is a design choice and stays a template warning, never a compile refusal. **Rule (REVIEW M2):** changing the pod version pinned by a live deployment is the owner's click bound to that pod's hash; one click may cover many members; agents and the copilot write drafts only; G tests the logic fingerprint, and the pod's blocks pass their own checks | Each mix is code; "no pod" is a special case; a pod cannot have a paper side; a pod edit re-proves 200 units, or, unchecked, changes live risk with no click | `CombinerKind` for logic only; `pod` kind a shell (`SWAP 31`); one compiled fingerprint | PH 31 | All twenty pods; the empty pod |
| S15 | **One evaluator.** First option: widen and extract the handler QMB and the node already share (`UnitSliceHandler`, `SWAP 2.5`, `2.6`) so the Lab, paper and replay drive the same one, not a second core beside it; state passed in and returned; four drivers (node live, QMB, paper, Lab replay); `unsupported_blocks` replaced by the needs list (each block declares what it reads, each place what it provides, a missing need names a fallback); a conformance tape through every driver in CI; the size trail equals the decision row; exits on their own path (S3) | Lab size differs from live size; two risk worlds (D50); a Lab-only block by nature instead of an unmet need | One handler BUILT; Lab simulator designed, no Lab package exists | PH 31 | Every pod screen, fan, stress board, head to head |
| S16 | **Shipping seats.** A core `library-items` lander landing static content at publish; a declared `library/` folder in a pack; real `pod`, `pod-block` and un-retired `template` kinds; one block catalogue (form and graph pod-blocks compile to a QML block); a row that saves a block with its contract test; Library blocks enrolled in the contract tests; pins, diffs and lineage on each unit and pod; a traced end-to-end run of a Library block through `unit_new`, QMB and a node deploy (UNKNOWN today), since a stdlib block bumps the money app and needs his signature | "Ship pods" stays a sentence; agents draft and he hand-saves; a landed block runs in QMB and not live; 200 units upgraded by hand; "one folder, zero core edits" rests on an untraced path | MISSING (`E2` rows 1-6; `SWAP 2.2`, `E11`) | none | Pod gallery, desks, agent-made blocks, recipes, the Python hatch, trust-ladder levels |
| S17 | **Positions, streams, per-market settings.** `position_limit` lifted, a template field per market and per open; "flat" per market and per position; more than one stream (1m and 5m); per-market numbers through the override chain's market key (I16) | Pyramiding, baskets and adds blocked; template A's two timeframes refuse; gold and FX in one scalper cannot carry different stops; ORB numbers per open refuse | REFUSED (`SWAP E4`, `E5`; `compiler.py:898-899`) | none | Pyramiding, curves, pairs |
| S18 | **Order path.** Order type on the intent (market, limit, stop); intent apart from placement; an entry-timing offset; partial close on the node; shared protection on a netting account as a setting; venue capability read from I4 at compile | Market only; 200 units queue at the bell; netting is a rework through the money path; a unit needing partials compiles and refuses at the node | Market only; partial refused; netting refused (`SWAP E14`, `10`, `21`) | PH 10, 21 | Netting, limit entries, jitter blocks |
| S19 | demoted to content (3.7): a risk check layer beside A to F; the census (K9) covers refusals | | | | |

### 3.2 Inputs

| # | Input | What breaks if missing | Today | Swaps or widens |
|---|---|---|---|---|
| I1 | **Fact surface.** Everything a derivation may read (D2): budget share, committed cushion, open risk per bet key, own record, cost cell for this hour and world, gap factor, level, trading state, a conviction number bound from the unit's own signal; each input timestamped with a declared fail mode (open, closed, neutral) | Almost no hybrid can run; three meanings of "missing"; a human's conviction cannot size | REFUSED (`SWAP 1`); partial fail modes | PH 1, 17 |
| I2 | **Cost cells.** Per instrument, broker, hour, session and world, written from fills; `uncalibrated` label with a class-pooled stressed fallback that decays to measured; a commission key; two residuals kept apart (signal before costs, cost against model) | Costs never reach the unit; his observe-then-act lens has nothing to read; signal decay and execution decay look the same; the hurdle deadlocks | MISSING (`MAP` section 4; `X1-H63`) | PH 1, 16 |
| I3 | **Account and venue facts.** Live balance refresh, open risk at stops, margin headroom, liquidation check at entry, a leverage-change stand-down producer, conversion market and USD seam, budget share per deployment, realised profit since anchor, `basis` declared per row (committed cushion, marked equity, realised profit, worst case) | Sizer blind; paper sizes from the demo balance; a margin close-out passes every brake; accelerators have no fact to read | Balance once at sign-in; `Account` is equity alone (`SWAP 14`, `15`, `17`) | PH 14, 15, 17, 22 |
| I4 | **Instrument record.** Money per point, lot step and bounds, class, bucket, underlying, book-or-quote flag, tick tier, cost cells (I2) by reference, conversion, session clock, day boundary, calendars (session, event with driver tags, roll, funding), roll rules reserved, commission, margin, leverage, detector calibration, venue capability (partial close, amend, hedging or netting, minimum stop distance, order types) | One template cannot size every class; order-flow logic on a CFD; CPI stickers "USD" only; gold micro charged Nasdaq's point cost; a unit needing partials fails only at the node | Partly: margin, swap, conversion exist; no commission, no base-currency key, no tags, no capability | PH 13, 14, 16 |
| I5 | **Market lists.** Allowed, home, active on the unit; the board and the list fall back to home, never to every listed market | Widening is a new version each time; with a placement set, a stale board trades the unit's own markets (docstring, `runtime.py:366-369`; the board is unwired today) | One list | none |
| I6 | **One curve artifact** (**if F3=B**). Usual level per minute of week, per world, with an age word and a flagged borrowed cold start, read by SQS, node, MIS and QMB | Three spread measures drift; the first live entry waits hours for a baseline | MISSING; `spread_state` uses fixed cuts | SQS seat |
| I7 | **Bars and clocks.** Bars carry full range, volume or tick count and time of day; tick, volume and event time as clocks; `knows_at` (event time against available time) on every reading and agent record | RVOL and the fastest volatility readings stay out; news units impossible; look-ahead in agent-built links | Closes only; `QuoteBar` has no volume; clocks refused (`MAP` section 4) | none; data is his call (Q2) |
| I8 | merged into S8 (agent evidence is a reading) | | | |
| I9 | **Identity on every row.** Unit, version, compiled fingerprint, logic and pod fingerprints apart, a generation stamp (spec written by people, status by the runtime), family id, parent, free type tag, market, world, stage, provenance (source: paper, video, agent, Lab, mini app; run; profile; model and cutoff), a claim scoreable by code (metric, benchmark, window); bet key, driver and family tags on every intent, and the direction | Pooling, ranking and per-type views impossible; a pod edit re-proves 200 units; four kinds of unit cannot be compared; an old brake state sizes a trade; a claim cannot be graded; three positions on one dollar are three bets | Most exist; type tag, pod fingerprint, provenance, claim, generation stamp missing; `family_id` in the dummy | PH 22 |
| I10 | **Group document.** `display_name`, `parent`, rank, scope keys, the `tag:` key, an allocation mode as a named row, a place for an alarm budget and a share cap; a pod may change a member's sizing rows at an anchor only under S14's click rule | "More units, less each" becomes law; every pod question becomes code; fleet rules have no home | MISSING; `book`, `bms` shells | PH 31 |
| I11 | merged into S2 (the level is a named modifier) | | | |
| I12 | merged into I1 (the conviction binding is one input) | | | |
| I13 | **R as a declared basis.** Gross at the disaster stop by default; a tail budget for a unit with no price stop; `allow_widen` as a row | His scalper without a stop has no R; widening is a law in code | Refused at compile and at the node's entry (`SWAP 11`); the law in `unit_intent.py:725-757` | PH 9, 11 |
| I14 | demoted to content (3.7): expectation at birth | | | |
| I15 | merged into S6 (the order-boundary veto is one link) | | | |
| I16 | **Override chain, keys reserved.** Preset, style, class, bucket, instrument, account, unit, market, timeframe, session, event; four resolve at first (preset, class, instrument, unit), the rest parse and resolve to their parent; later entries win; event overrides expire | Numbers cannot differ by instrument, session or open without a new schema; the census refuses the keys later | MISSING (reserved in the set-aside spine only) | none |
| I17 | **Feasibility verdict.** Per unit, instrument and broker: can one minimum lot at this stop fit the share; computed and shown, re-run at anchors; the refusal and the shed, concentrate or borrow rules are blocks | The book goes dark above the floor with nobody told; "which classes can be traded at this budget" is found out by trading | MISSING | none |

### 3.3 Records

| # | Record | What breaks if missing | Today | Swaps or widens |
|---|---|---|---|---|
| R1 | **Decision row that replays.** Inputs with timestamps; every resolved number with its reason; each step from wanted to risk-approved to filled (three positions side by side); each chain link's verdict and the binding clamp named and counted; version and both fingerprints; readings seen with source, age and version; `propensity` when a paper twin took a logged random share of refused entries; newly-active market mark; placeholders used; requested, enforced, observed on every control; one trace id from reading to fill; `explain_size(row)` as one pure function | "Why this size?" has no answer; agents cannot diagnose; the size trail on screen cannot be drawn; cannot tell what the guard cost from what the broker cost | Residue literal `0/1`; nothing stores the inputs (`SWAP 1`, 4.1 row 15) | PH 12, 29, 30 |
| R2 | **Trade row v2.** Net and gross R, costs by kind, exit mechanism and reason code, MAE and MFE with the bar path, session, slice, cost cell, world, stage, contract month, markout, readings seen, `counts_toward_proof`, numbers in force; records split by unit, market, session, slice and world | No money ledger, no fair brake, no resize replay, no two-arm test, no numbers talk; windows, cost map and ORB per open fail; `r_after_costs` holds R with no costs | `r` only (`SWAP E13`, `29`); per market only (G7 5.3) | PH 11, 25, 26, 29 |
| R3 | **Would-have rows.** Written while benched, in shadow, or refused by any link or sticker, with `propensity` | Evidence freezes while stopped; gates cannot be judged; the handbrake stays hidden; the logic record quietly depends on the pod | Kind declared, no writer (`SWAP 29`) | PH 25, 29 |
| R4 | **Events and codes.** `risk_event` rows written; closed reason codes as appendable data with new families for user-added blocks; fire tags (session, class, news, SQS, cause); a root-cause key and event id on stand-down, risk event and order-failure rows; alert fields (action, deadline, actionable) | New brake text has no code and a QMB run fails on `unlisted`; one incident is twenty cards; alarm load falls on him | Kind declared, no writer (`SWAP 25`) | PH 25 |
| R5 | merged into R9 (the cushion ledger is one scope of the fold) | | | |
| R6 | merged into R2 (the split is on the trade row) | | | |
| R7 | **Fill record.** Decision quote, arrival quote, fill, partial, reject, requote, mid at several later horizons, per account as a time series | No markout, no last-look evidence, no broker monitor; execution decay reads as signal decay | MISSING (R19 minute rows carry spread only) | PH 17 |
| R8 | **Run stamp and arms.** Real-tick share, quote source, gate settings, costs, fold design; arm id, link id and parent on run records; every arm a counted try | Scalper results on generated ticks look proven; a link is never credited or blamed | MISSING; `tries.py` counts tries | none |
| R9 | **The fold.** `RiskState` as one fold over journals keyed by scope including pod and tag: money, exposure per bet key, open risk, drawdown by kind, each control's distance, the cushion ledger (anchor type, clock, scope, realised and marked series), trading state with a stamp and a reason, UNKNOWN when stale, the verification state the entry chain reads; pod-level numbers, since a pod has money and members (the demo's examples: at stake next trade, losses to kill line, room, daily loss; the screen does not bind the list); a catch-up-at-start rule (anchors passed while down, expired stickers, states and ledger rebuilt); one fleet read over all units | Node reports health, not risk; no house money pair; brake and accelerator contradict; agents read 200 units one at a time; a restart loses anchors and states; the pod card has no numbers | Node health only; `journal_query` rows only; only `risk_stop` has a restart test (`SWAP 23`) | PH 1, 20 |
| R10 | merged into R4 (incident keys and alert fields are event fields) | | | |
| R11 | merged into S13 (the per-change record is part of motion) | | | |
| R12 | demoted (3.7): lineage beyond I9 is methodology's | | | |
| R13 | **Reading record.** Stamped when computed, never rewritten, backfill flagged; an as-of query shared by QMB and live | A backtest flatters the MIS (76 % in `MIS-PAGE-CONTENT` simulation) | Stamped records exist; the query UNKNOWN | none |
| R14 | demoted to content (3.7): isolation accuracy is a query over R3 and S10 | | | |
| R15 | merged into R1 (requested, enforced, observed and the three positions are decision-row fields) | | | |
| R16 | split: the window card kind is S9; block-entry fields are content (3.7) | | | |
| R17 | **Identity and swap.** The identity table wired; a forwarding map from an old block and version to a new one with a parameter transform, so `fixed-fraction-at-stop@1` to a real sizer is a declared migration; which swaps keep which record (a sizer-only swap keeps the logic record in R and pays the version pull; an exit change is a counted try); what governs an open position during a swap; what old rows mean after a field changes (`r_after_costs` gaining costs shifts calibrated numbers that read it); plan before change, refused if stale | The placeholder swap costs every unit its record; an open trade is governed by nobody; fixing a field silently moves numbers | Identity table unwired (`SWAP E16`); no transform language | PH 1 to 4 (the rip-out), 22 |

### 3.4 Hooks and proofs

| # | Hook | What breaks if missing | Today |
|---|---|---|---|
| K1 | merged into S6 (the one seam is the entry chain) | | |
| K2 | **App and agent doors.** For apps: a read door over journals and the fleet fold, and a card-landing path to "Needs you"; for agents: typed read rows with state and receipts, proposals typed, expiring, scoped, de-risk default, raises as cards, direction on every operation; his "as a mini app also" (M49) needs these two doors, and the demo's watcher apps show the same intent (`UI-LOOK.md`) | No app can watch units, so the shipped decay rule floods him; 200 units cannot be watched by agents, or agents reach further than they should | `data_reads` handles `market` only (`supervisor.py:891`); app-to-inbox path UNKNOWN; catalog rows exist; tighten-only cards in one template |
| K3 | merged into S8 (road D is the readings bus) | | |
| K4 | demoted to content (3.7): twins and canary run on S14's deployment key | | |
| K5 | **Money and promotion door.** Promotion and live money run through a channel the copilot and agents cannot read or reach, including his email and any code sent there; the click binds to one hash, level, markets, date, and to a pod version when a live deployment moves to one; a protected field list no agent may write | The fixed lines rest on agents' good behaviour; published tests show models get around such gates (`E3-26`); self-improvement can loosen limits | Promote is his click; channel isolation UNKNOWN; no protected list |
| K6 | split: the save door is S16, the settle hook S4, the group place I10 | | |
| K7 | **Rehearsal walk.** Extends `tools/first_real_start.py --rehearsal`: on a store with zero trades and zero fills, from template through check, backtest on synthetic bars, promote to paper, a filled entry on the fake broker, one row in the fleet fold, to the account owner's promote click on the fake broker's live lane | The newcomer's walk rots quietly; cold starts are never tested; "trades out of the box" is a sentence | Rehearsal covers setup only |
| K8 | **Re-test workflow.** After any compiler format bump, rerun G per deployed unit and report which units changed behaviour; required before a bump reaches a node with deployed units | Every bump after the first deploy is 200 hand moves, so nobody dares bump and the compiler freezes (REVIEW M1) | MISSING |
| K9 | **Contract tests and census.** In order: the same decision in both hosts by socket; exits never blocked as a property, including a faulty exit block and a hung chain link; every refused field running, refused with a reason, or labelled, the census extended to `authority`, `reads` and every row of 3.8; every number has a reason and range at check; motion range, step, flat and bounded state with a shuffled-outcome control; every template reaches paper on rehearsal; no agent path to money by tool table; `RiskState` from one fold in every reader; a known-answer cost check per engine or cost block (`E3-5`); the `_CEILING` and exit-evidence test faults fixed before a real block lands | A swapped block passes a slot test and refuses at compile; a real sizer fails CI; silent no-ops | `test_socket_contracts.py` (`_CEILING = 0.005`; exit test feeds refused evidence), census, goldens, upgrader rule exist (`SWAP E9`, `E10`) |

### 3.5 Invariants

| # | Invariant | Source |
|---|---|---|
| V1 | Exits are never blocked by any link, sticker, brake, read or fold; a faulty exit block falls to the next rank, then `_close_scope`; proven by a property test | fixed line; `X3-H46`, CHECK B3, REVIEW S24 |
| V2 | Only the account owner's hand lowers a kill level; a control may raise a stand-down and, if its row says so, a kill level | fixed line; M49 |
| V3 | Agents never place on a live account, size up, lower a kill level or promote; their output reaches a unit only as a reading it chose to read, inside declared bounds, with expiry; the sandbox is unlimited on paper | fixed line; `H4 I-52`; REVIEW S14 |
| V4 | Only the account owner promotes to live; the click binds to one hash, level, markets and date, and to a pod version when a live deployment moves to one; one click may cover many members | fixed line; `X1-H46`; REVIEW M2 |
| V5 | A floor, if set, survives a restart and a banker act; only the owner changes it | AD-17 candidate 2; REVIEW S11 |
| V6 | Stops tighten only, unless a row declares `allow_widen` | `SWAP 9`; canvas |
| V7 | Every shipped template stands alone at trade time: no MIS, mini app, QMB card or Lab pass. A unit may declare `fallback: stand aside` on a reading it needs | `H3 T7`, M49, `E2` row 16, REVIEW S12 |
| V8 | principle, not an invariant (3.7): every value is a labelled default with a reason and a range (section 4) | |
| V9 | Links and reckless settings warn and label; only the fixed lines refuse; a blank number warns, and a template may demand a value before its owner's live click | `E4` 8e; `E2` row 14; REVIEW S15 |
| V10 | Same inputs and state give the same answer in every driver (node, QMB, paper, Lab); only fills, costs and latency may differ | `E2` (f) |
| V11 | principle, not an invariant (3.7): risk rows are evidence and may not be dropped by any observability stack | |
| V12 | dropped (REVIEW M1); replaced by D41's sequencing note and K8 | |

### 3.6 What arrives later with no core change

Every sizing base, exit mechanism, brake, accelerator, gate, reading, isolation rule, allocator and pod in section 2 and in `FATES.md` marked "default block", "template" or "content". The twenty pods and R9's eight pairs. The fifteen physics readings. The learner-and-applier object, bandits, pooled priors, the Simplex fallback. Trust-ladder levels, the Python hatch, expressions. The fleet watch's agent layers. The MIS finder and pack contents. Desks and departments. Recipes, the joints vocabulary, the block-entry fields (`output_meaning`, `assumes`, `null`, `evidence`, `retest_by`, `decides`), failure cards, three faces, the dictionary expansion. The file extension. Netting, limit orders. Target-position curves, once step 3 lands, on the answer type S3 reserves. Twins and canaries on S14's deployment key. Canary analysis rules, the challenger, rehab, the governed pipeline (methodology). Alert delivery, the six words on screen, meters and scorecards (UI). None of these changes a socket above.

### 3.7 Merged or demoted in the fix round, with reasons

Applied as REVIEW S18's deletion test: remove the row and name what reappears or reworks. Merged rows are one mechanism told twice; demoted rows are additive later with no rework.

| Was | Now | Reason |
|---|---|---|
| S5 registry row; S12's restore and guard statistic | S4 control rows | one row, told three times |
| S6 gate slot, S7 group stage, K1 seam, I15 order veto | S6 entry chain | five things could pass, shrink or refuse; one chain, each a link (fork F7 keeps the alternative open) |
| I8 agent evidence; K3 road D | S8 readings bus | agent evidence is a reading; road D is the bus |
| R16 window card | S9 | the card is what a window binds to |
| I11 level slot | S2 | the level is one named modifier |
| I12 conviction binding | I1 | one input |
| R5 cushion ledger | R9 | one scope of the fold |
| R6 record split | R2 | fields on the trade row |
| R10 incident keys, alert fields | R4 | event fields |
| R11 per-change record | S13 | motion's own record |
| R15 three positions, requested-enforced-observed | R1 | decision-row fields |
| K6 grab bag | S16, S4, I10 | three homes |
| S19 check layer | content | additive; the census (K9) covers refusals |
| I14 expectation at birth | content | an artifact stored with the version; nothing reworks without it |
| R12 lineage beyond family, parent, claim | other: methodology | I9 keeps what rows need |
| R14 isolation accuracy | content | a query over R3 and S10 |
| R16 block-entry fields | content | additive; `block_fingerprint` hashes `block.py` only (`loader.py:81-83`, per the review), so they move no compiled fingerprint |
| K4 twins, control, canary | content | a second deployment of one version is allowed by S14's key; the lanes are workflows |
| D40's rollout field, self-test card, offers | content | additive |
| V8, V11 | principles | not refusals; V9 says only fixed lines refuse |
| V12 one bump | dropped | false premise (REVIEW M1); D41 and K8 replace it |

Rows the review proposed to merge and I kept apart: S10 stickers from S8 readings (a sticker refuses, a reading informs); I4 instrument record from I2 cost cells (cells are written from fills, the record is declared; I4 references I2); S9 sessions from S10 stickers (a window is the unit's, a sticker the market's). Result: 51 live rows, not the review's 35.

### 3.8 Every refusal, placed

`SWAP` section 1b (E1 to E18) and 2.4, row by row, as REVIEW M6 asked. "Stays refused" names why. K9's census carries this table.

| Refusal | Where | Placed |
|---|---|---|
| E1 `reads` | `compiler.py:900-901` | S8 |
| E2 eleven roles do not run | `:107-117`, `:438-443` | S12 (seven roles plus two new); `veto` and `arming` also serve S6 |
| E3 exits at unit or account scope | `:472-477` | unit scope: S3 once S17 lifts the limit; account scope: stays refused as an exit, it is a control verb `flatten` on S4 |
| E4 one position per market | `:958-961` | S17 |
| E5 per-market settings | `:944-957` | S17 through I16's market key |
| E6 `sessions` | `:904` | S9 |
| E6 `context_needs` | `:907-912` | S8 |
| E6 `routes` | `:904-929` | stays refused: one venue today; a second venue is content when a route exists (Q2) |
| E6 `plain_python` | `:924-929` | stays refused: the Library block path (S16) is the door; the quarantined hatch is content |
| E6 `roll` | `:938-943` | stays refused until a futures route exists (Q2); the record field is reserved on I4 so it is rows, not rework |
| `streams_not_built` | `:898-899` | S17 (template A needs two streams) |
| E7 spread, SQS, news in `guard` | `runtime.py:2623-2675` | S6 |
| E8 sizer slot has no type check or ceiling | `compiler.py:1049`; `unit.py:794-797` | S1 |
| E9 `_CEILING = 0.005` in the contract test | `test_socket_contracts.py:57` | K9 |
| E10 exit contract test feeds refused evidence | `:233-237` | K9 |
| E11 Library blocks not enrolled | `:96-110` | S16, K9 |
| E12 motion rule gets only `{strength, r}` | `engine.py:142-147` | S13 |
| E13 `r_after_costs` holds no costs | `unit_handler.py:724` | R2, R17 (what old rows mean) |
| E14 market entries only | `unit.py:761` | S18 |
| E15 `OwnPosition` lacks stop, targets, bars held, MFE, MAE | `unit.py:128-137` | S3 |
| E16 identity table unwired | no `classify(` | R17 |
| E17 too-thin count | `presets.py:45` | a value: numbers talk and methodology |
| E18 motion constants | `engine.py:39-44` | S13 |
| `exit_not_built` by shape (six exits) | `:350-364`, `:491` | S3 |
| `exit_not_built`, second of a use | `:492-495` | S3 |
| `inputs_not_built` on an exit | `:482-487` | S3 |
| `stop_not_built` | `:500-506`; node gate `runtime.py:1102-1106` | I13 (a declared no-stop basis), S6 (the gate accepts it) |
| `halts_not_built` | `:902-903` | S4 |
| `inputs_not_built` on the sizer | `:930-936` | I1 |
| `open_positions_not_built` | `:996-1000` | S13 |
| `motion_not_built`, `motion_source` | `:592-613`, `:632-643`, `:1002-1007` | S13 |
| `role_not_built` | `:438-443` | S12 |
| `limit_not_built`, `settings_not_built` | `:904-961` | S17 |
| `BLOCKS_NOT_BUILT`, 17 pins | `:120-138` | content: each block lands when its needs are met; the census says which |
| `cadence.at` alone refuses | `:1008-1014` | S13 |
| `applies_to_open_positions` | `:996-1000` | S13 |
| partial close refused on the node | `runtime.py:1807-1808` | S18 |
| a stop past entry refused | `:1360-1369` | stays refused: it is the tighten-only law (V6) unless `allow_widen` (I13) |
| two units on one netting symbol | `:2888-2906` | S18 |
| a second deployment of one version | `promote.py:422-447` | S14 (deployment key with pod and side) |

---
## 4. THE FIRST BASELINE

What a new user gets out of the box. Every value is a labelled default with a reason and a range (the principle that was V8), shown on the unit's card as a shape, not an edge ("we don't have any proof", M49). It trades on paper with nothing set; the copilot edits it through `unit_new(template, overrides)`, `unit_check` and pod drafts; it depends on no QMB card, Lab pass or MIS; it depends on the sockets in section 3 and on nothing that waits for the numbers talk.

**Values (REVIEW M4).** The builder picks a labelled placeholder value for every number an on-by-default block needs, reusing the placeholders that exist (0.5 % at the stop, 2R, 48 bars, the old SQS settings) where they do, with no argument, owner `numbers talk`. The card shows the label. M50: "something that can work even if we don't have the numbers set yet."

**Cold behaviour (REVIEW M4).** Every on-by-default block declares what it does with zero trades and zero fills, as its `until_n` row (S4) or its own rule. The table says it. The rehearsal walk (K7) starts on an empty store and ends with a filled entry; if it does not, the baseline does not trade.

**Why these defaults (REVIEW M5).** Each default is chosen by configuration, never by a model result: it needs the least, a person can explain it, and it is one row away from off. Where the evidence behind a default is PROPOSAL or MODEL, the table says so, and `E5`'s tables are cited only as "the mechanism behaved as described and did not run away". Nothing ships because a table ranked it.

**Honest state today.** At the tip the baseline trades only in the narrow shape: one sizer reading four facts, one stop read once at entry, one target, one long-side time exit; no halt runs, nothing reads cost, intraday cannot go flat at a session boundary because `sessions` is refused, and template A's two timeframes refuse (`SWAP` short answer, `E6`; `compiler.py:898`). So "trades out of the box" is true after S1 to S4, S6, S9, S13, S17 and I2 to I4 land, in slices (D41), and false before. K7 proves it.

### 4.1 Blocks switched on for every unit

| Slot | Shipped default | Values open (owner: numbers talk) | Cold behaviour, from zero | Why this one, as configuration | Evidence |
|---|---|---|---|---|---|
| Sizer | Fixed fraction of a declared money base at the stop, costs in the denominator, round down, residue real; base chosen on the template (equity, or cushion above a user-set floor); the converter spells quantity from the record | fraction, floor, base | Needs no history: equity, stop and record exist at tick one; a missing cost cell reads the stressed pooled fallback, labelled | Needs the least (no edge, no record, no MIS); explainable in one sentence; every other base is one row away | BUILT in shape (narrow); shipped by every platform (`R1` pattern 1), which is practice, not proof |
| Exits | Disaster stop (swing or ATR, side-correct); R target; time exit side-correct; a reason code on every close | stop method and buffer, target multiple, bars | Needs no history | The three blocks that exist; a floor under every trade | BUILT; `timer()` builds long-side today and is fixed in S3 |
| Halts | `session-loss-limit-halt` at unit scope and `account-daily-loss-halt` at account scope, both `no_new_entries`; restore by rule at the next day boundary, retry-then-lockout | limits in R or money, window, rest, lockout counts | Money limits bind from the first trade; nothing to learn | The plainest money brakes, already written; a way back without a click | BUILT, never run in a host; restore REAL elsewhere |
| Gate | Cost hurdle: this quote, this stop, this unit's allowance, in R (SQS-2); the old SQS rule as a floor for broken markets (SQS-1); exits bypass | allowance, floor line | **Warns while its cost cell reads `uncalibrated`; refuses only on a measured cell showing net edge below zero.** So the first entries happen and fills calibrate the cell; the review's deadlock (no entries, no fills, no calibration) cannot occur. The floor needs a curve: a flagged borrowed curve until live quotes build one | Needs the least (a live quote and the unit's own stop, known at tick one); explainable; one row from off. Fits M51's observe-then-act frame, which did not ask for it | PROPOSAL over REAL cost shape; SQS-1 BUILT rule text, never run live |
| Stickers | News calendar to stickers, both FX legs tagged, strength from the calendar's tier | widths, strengths, tags | A stale or dead calendar lands a card and reads `prefer not`; it never parks a unit silently. The kill switch keeps the hard kill | His news-day example (M51); the calendar ingest exists | calendar ingest BUILT and fails closed (G9); widths unmeasured |
| Group row | Allocation mode `own size under a parent limit on losing together`; portfolio day stop reading the book's sized day sigma, `on_fire: stand_down(all) + card`, the stand-down expiring at the next day boundary by rule; raise permission gate on | parent limit, k, gate on or off | Parent limit: a fixed labelled limit until N days of co-movement exist. Day stop: reads the sum of planned R at the stops until N days of P&L exist, then the sized sigma. No card is needed to resume | His M49 complaint answered; his "switch off entirely" (M10); one row each from off | REAL bank practice for the parent limit; MODEL for the stop's shape, cited only as behaving as described |
| Numbers | Every number carries derivation, range and reason; motion: find (an optional replay at birth), track (facts), correct (the built engine, bounded, per-type preset); report with and without motion | ranges, cadence, which numbers correct | Without a replay, labelled defaults stand; track reads facts at tick one; correct waits for its minimum count and stays `off` until then | Adds no new part: the built engine already does the applier's job (`E5` 2.1); each job has an off switch; a person can say what moved a number and why. Fork F2 stays open; an architect may replace this default | BUILT engine; MODEL for the stack, cited only as behaving as described |
| Fleet | **A scripted fleet watch ships in this build (lead ruling, REVIEW M7):** one ranked row per unit from the fold (R9), two lists (who gets looked at, by rank; who gets acted on, by a strict bar under one fleet budget), one incident one card by root-cause key (R4), a morning digest; **no agent**; the shipped decay rule's nightly card per unit is switched off at the same time (`E5` 1.1: about 91 cards a night for 200 healthy units) | K, the strict bar, the budget | From zero every row reads "too thin to judge"; nothing is flagged; the digest shows counts by state | His loudest complaint (M49); the shipped rule floods; scripts decide, words come later | pieces BUILT (`t7`, `dm`, `gw`, `s2`, `morning-digest`, `pp`); the fold and the two lists are new |
| Records | Decision row, trade row v2, would-have, risk events, receipts, the fold | none | Written from the first decision | Without them nothing above can be judged, replayed, explained or watched | BUILT in part |
| Kill switch and effects | Unchanged; YELLOW to BLACK effects read by entries as well as closes | effect table values | Needs no history | "earned its spot" (M5); entries ignore the table today (`SWAP 18`) | BUILT for closes only |

### 4.2 Three ready-made templates, as presets with values open

All compile and pass G on synthetic bars and say on their card "a shape, not an edge". Templates A and B carry an expectation at birth from replay when one was run (content; its absence changes nothing).

**Template A, `scalper-mr` (mean-reversion scalper style).** His first units (M49). Markets: a short FX list plus gold, by record; 1m and 5m bars (needs S17's second stream); `position_limit` 1 per market, several markets. Sizer default with the cushion base. Exits: disaster stop, target, time exit, **fast-invalidation cut on**, read from the winners' MAE once N winners exist and a fixed labelled distance before that (cold behaviour), with the warning "unproven after costs; run the two-arm test" (`H2 I16`, `I70`; MODEL; REVIEW M4's caveat on the block); breakeven off; no trailing until step 3. Halts: the two defaults; the own-percentile money bench **on, in shadow until N trades exist**, the session-loss halt standing in; the count brake ("about three", scaled to the unit's run length, halve) present, off; the two-speed circuit breaker present, off, with his reason on the row ("it's a baseline improve it, please", M10); `session-fill-limit-halt` present. Gate: cost hurdle tight, SQS floor. Tolerates no stickers. **Cushion rule on with a day anchor, because he asked for it** (M5 "I don't think I want to lose the house of money"; M39 "reverse House of Money was my idea"; M50), value open, one row from off; it brakes on the way down and presses with winnings only; cold: profit since the anchor is zero, so the multiplier is one; the press gate is a block. Motion: correct on for filter numbers, off for size. Reads: none (stands alone); routing rung 0 or 1. Fleet: type tag `scalper`, family id. Not advised, warned: trailing stops, suspending stops in news.

**Template B, `intraday-trend` (intraday style; an `orb` variant differs in two rows).** 15m bars; sessions declared; flat before the session close with a buffer (`H2 I75`; needs S9). Sizer default with the equity base. Exits: disaster stop in ATR, R target, **thesis-invalidation exit on** (a named condition that proves the idea wrong closes the trade with its reason; `X3-H40`; Steward, REAL paper account), time exit at session end; breakeven off; trailing after a calibrated continuation when step 3 lands (`H2 I74`). Halts: the two defaults; the own-percentile bench on, in shadow until N trades; `losing-days-halt` present, off; the two-speed circuit breaker present, off. Gate: cost hurdle, SQS floor per open. Tolerates `open` in the `orb` variant only. Cushion rule off. Motion: correct on for filters, off for size press. Reads: none; `sessions` from the record's clock. The `orb` variant: one logic across several opens as one family with a family tag (`X0-25`), `position_limit` per open (S17); its volume gate waits on I7 and Q2, so it ships with the tick-rate stand-in.

**Template C, `canary` (`E2` Pod 19).** On purpose the one with no brakes: fixed money per trade, one position, the kill switch only, labelled "no brakes" in the largest type. A stranger's first run on paper. REVIEW S16.

### 4.3 What a copilot can change on day one, and how

Through `unit_new(template, overrides)` and `unit_check` (BUILT): markets, bars, blocks in any slot that exists, every number's default and range, motion settings. Through a pod draft (needs the `pod` kind, S14): allocation mode, controls at group scope, tolerations, `on_fire`. A draft touches no live deployment: moving a live deployment to a new pod version is the owner's click bound to that pod's hash (S14, V4). Through a block save (S16): a new block. Through a new JSON in the templates folder: a new template with no other change (`SWAP` section 3). What it cannot change until the sockets land: halts, reads, sessions, per-market numbers, a second exit, moving risk numbers (`SWAP` section 3: "a copilot has no real risk choice to make from the shelf").

### 4.4 What the baseline does not do, by design

It does not prove an edge (methodology). It does not set a dollar value (numbers talk). It does not route by the MIS (rung 0 by default). It does not isolate a class by rule (the rule is off; the sticker exists). It does not press size on open profit. It does not deliver "amplify the load" (M10): that needs a press block on S2, available and off. It does not need him to watch it: the halts and the group row restore by rule, and the scripted fleet watch (4.1) ranks what to look at. It does not refuse a reckless pod; it grades it and says so in large type.

---
## 5. Logical flaws and collisions

Found across H1 to H5, E1 to E5, the old funnel and review, the swap chart and his words. Each is resolved, dissolved by configuration, or kept open with the reason. His own contradictions are set side by side and left to him unless a configurable answer dissolves them.

| # | Collision | Status | Resolution, or what stays open |
|---|---|---|---|
| C1 | **The cut catches winners.** His pictured scalper (55 %, 1:1) loses after costs at a 5-pip stop; the fast-invalidation cut rescues it only if it catches few winners: +0.086R at none, +0.012R at 10 %, −0.062R at 20 % (REVIEW M4, `more_arith.py`). No paper tests fractional cuts after costs (R8 gap 2) | **open** | The cut ships on in the scalper template with the warning on the block; the two-arm test on fixed entries is the first Lab job (methodology); if it fails, wider stops and fewer trades. k and the stop width are numbers talk. Not resolved by this funnel |
| C2 | **His two sizing statements.** "the more units I have, the less I can trade... these numbers are too fake" (M49) against "get the total amount of capital to be spent in a day... split it across the total number of units" (M10) | dissolved | The allocation mode is a row on the group (D31). Both are modes; the shipped default is own size under a parent limit. He never has to choose in the abstract |
| C3 | **Out of the box.** "we can't really just come up with something that works right out of the box. I would love to" (M10) against "something that anyone can use... right out of the box" (M49) and "something that out of the box can work" (M50) | dissolved | The baseline works out of the box; the canvas means nothing in it is fixed. The lead's briefs carried only the second half from L197 (TIMELINE) |
| C4 | **Size and the technical lens.** "for size, I think it's not part of the technical stuff" against "can technically position configure itself, position sizing and all that" (both M49) | dissolved | The mechanism is in (S1, S2, S13); the values are out (V8) |
| C5 | **Rules closing positions.** "may a rule close position by itself? I think no" against "the dictionary has closing mechanisms" (both M49) | dissolved | An exit is a block the unit owns (D6). My reading, not his words: the old question meant a portfolio rule reducing positions (de-gross, cushion clip); that is a control verb `reduce` or `flatten` on S4, a pod setting (E2 pod-life table) |
| C6 | **Several positions.** "isn't there a possibility that one unit can hold more than one trade at a go?" (M7) against "not every type of scalper per se will be able to hold several positions" (M8) | dissolved | `position_limit` is a template field (S17) |
| C7 | The MIS board fails open; isolation fails closed (X1 collision 9; SPINE line 253 shows them "together") | resolved | A sticker lives in the stand-down table, never as a board word; `unknown` is a state per scope (D27) |
| C8 | SQS blocks and never shrinks (`X3-H63`) against the graded cost dial (`X2-H42`) | dissolved | Both are blocks; the hurdle and the floor are the defaults; the dial is off on the modifier socket (D26) |
| C9 | `two_live_readers` compile refusal (PICK graft 3) against a reduce-then-bench ladder | resolved | A template warning, never a refusal (D10). Stacking is the user's choice |
| C10 | The edge dial fixed at zero (old DP10) against "a low one will get a buffer and a high one will get even a bigger buffer" (M10) | resolved | The edge is one input to a derivation; the default sizer needs none; a Kelly block reads it; no law (D3, D19) |
| C11 | "Why lots?" (M49) against `Size.lots` on every contract | resolved | Dollars at risk decide; a converter spells the order (S1). The seam word is his (`QUESTIONS.md` Q3) |
| C12 | The demo marks `kill` as `required: true` and the Lab says "Send to paper requires kill line set" against "a reckless setup must be expressible" | resolved | Preset warning and grade in the largest type, never a wall (E2 row 14, V9). The demo marks the kill line "Every pod needs this" (`UI-LOOK.md` 6); a design choice, kept as the template default. One mind argued both sides in Appendix A; that is not independent dissent |
| C13 | A pod block is "pure" (Lab AD-10) while guard rows keep `block_state` | resolved | State goes in and comes back (S15) |
| C14 | `qmx_lab.pods.simulator` as the one evaluator against the guard package on a replay port | resolved | One small core in a library both import; the simulator is a driver (S15, D38) |
| C15 | **Book as skeleton.** "the book is the right skeleton... It's just cleaner" (M10), "if the BMS or a book system doesn't make sense... let's do that" (M31), "I think we shall decide later" (M49) | kept open, his | A group document with `parent` reserved and an allocation mode keeps every shape possible (D35); "Classic Book" is a pod template. Not asked now |
| C16 | **Agents never touch money** against an agent cut that applies itself inside a pod's declared bounds (`E2` Pod 17, `H2 I95`) | **open, his** | Default: a cut-only fact a unit's own rule reads, inside bounds, with expiry; raises and placements are cards. `QUESTIONS.md` Q4 |
| C17 | The shipped decay job sends about 91 cards a night for 200 healthy units (`E5` 1.1, MODEL) against "Why would I have to be there monitoring units?" (M49) | answered on paper; ships with the scripted fleet watch (D44, 4.1 Fleet row) | One ranked row per unit, no agent; the shipped decay rule's card per unit is switched off at the same time; the app read door and card path are core (K2) |
| C18 | `SlowState.read` keeps every trade for ever while every other block declares a `state_bound` (`E5` 2.1) | resolved | A bounded window is a core seat (S13). Flagged to repair |
| C19 | "QMX has the learner and no applier" (`X1-H03`, R7) against the built engine already doing the applier's job (`E5` 2.1 finding 2) | resolved | The applier object is content; the fields it needs are core S13 (D16) |
| C20 | The horizon sizer's "0 % floor touches" is partly structural (old F12) and was sold as safety | resolved | A block labelled MODEL, never the law (D3) |
| C21 | R gross at the disaster stop (old DP11) against R at the working exit (X3 P17); his B9 reservation | resolved | R is a declared basis on the row (I13); gross at the disaster stop is only the default |
| C22 | Stop widening is a law in code (`unit_intent.py:725-757`) against the canvas | resolved | `allow_widen` row, warned (V6) |
| C23 | The first live entry waits hours for a live SQS baseline (SPINE 475) | answered on paper | The cost hurdle needs no warm-up; the curve artifact has a flagged borrowed cold start (D26, I6) |
| C24 | A stale board trades every listed market (`runtime.py:367-369`) against a widening router | answered on paper | Home markets are the fallback (I5). The docstring at `runtime.py:366-369` says the unit trades its own markets when a placement is set and the board is stale; the board is unwired, so this is not live today (REVIEW S32). The fix lands before any wide list |
| C25 | A slice-by-slice build against a compiler bump that moves every fingerprint | corrected (REVIEW M1) | Bumps are free until the first unit deploys and happen only when a compiled decision changes, so sockets land in slices; the re-test workflow is core (K8); "one bump" is withdrawn (D41) |
| C26 | "fewer, larger units" rejected as against his C1 (old DP13) against "Why not look for the best basket" (M50) | dissolved | Both his, at different capital stages; allocation mode plus the stage switcher pod (D31, `E2` Pod 9) |
| C27 | "ORB, I'm not certain if that's the sniping period or not" (M8) | answered | Different things: a logic, a window, a record (D30) |
| C28 | "trust grows with threads automatically. I'm not certain of that statement" (M8) against a level ladder law | resolved | A level slot, no ladder law (D4) |
| C29 | "7 days is doable, but 14, nah" (M7) against an e-bar on paper (`X5:241`) | out of this file | Methodology; the baseline has no paper bar (V7) |
| C30 | MIS "not your session" (M8), then "a question for you now" (M10), "no problem" (M31), "designs for the SQS systems, MIS systems" (M52) | resolved | `E1` designed them; the seats are core (S6, S8, I5, I6), the apps are content (D22, D26) |
| C31 | "nothing is set in stone" against his fixed lines | resolved | The fixed lines are the only refusals; everything else warns (V9) |
| C32 | Exits in the profile (candidate 1) against exits on the unit (fold, `E2` round table); may a pod swap exit rows at an anchor? | resolved; one part open | On the unit (D6). Whether a pod may swap exit rows at an anchor is fork F5's open edge; the scalper voice does not accept "new version" |
| C33 | Target rests at the venue against the node closing it | open, waits on R24 | Fork F5 sub-choice. A wick reads differently in backtest and live until settled |
| C34 | The allocator as a trade-time slot (Lab's seven) against the order path | resolved | The allocator publishes a share at an anchor; a trade reads it as a fact (`E2` (c)) |
| C35 | The square-root split chosen because the dollar sim said so | dropped as law | A block; the sim result is parked material, not a verdict (D31) |
| C36 | `H4 I-34`: ten times the units means a tenfold bar and much slower demotion | corrected | `E5` measured 30 to 135 % slower for active styles, up to 5.6 times for the slowest; family pooling cuts it (D44) |
| C37 | Fees: "Fees, same thing. We shall also talk about it" against "something we need to cater for in the technical lens" (both M51) | dissolved | Cost cells and the hurdle are mechanism (I2, D26); allowances are values |
| C38 | Order flow: "Some can lead to actual units" (M33) against "left out for a good reason for now" (M52) | dissolved | The venue flag and data level are core (I4, I7); order-flow blocks are content; the data is his call (`QUESTIONS.md` Q2) |
| C39 | Who said 55 % (M8, M10, M49) | not a design matter | TIMELINE Appendix A records it; the number was always an example |
| C40 | "I think overfit here really is good" (M50) against "put the overfitting thing aside" (M51) | out of this file | Methodology. `E3-3` is the evidence to carry there: mine-and-shrink did as well as strict gates on US stocks monthly |
| C41 | `MIS-PAGE-CONTENT` has readings on H1 while his router wants 1m and 5m; persistence on 1m and 5m takes about 4 to 5 hours to show (simulated) | answered on paper | The finder is a session or day list by default; a per-trade read is expressible and warned (D22). He must hear this plainly, with the simulated lag named as simulated |
| C42 | The admission gate as law refuses his scalper at most hours until fills exist (REVIEW M7) | answered on paper | The deadlock the review named (no entries, so no fills, so no calibration): the shipped hurdle warns while its cell reads `uncalibrated` and refuses only on a measured cell showing net edge below zero (D19, D26, 4.1) |
| C43 | Agent-held demo positions invisible to every rule | resolved as a flag | `foreign` scope in account numbers (old DP33, kept) |
| C44 | Hedge-fund "pod" and the Lab's "pod" are one word for a team, a stack, a capital allocation and a package (`E2` (a)) | default vocabulary, corrected against the demo's intent | Pod (stack plus money plus members on one place, two sides), pod version, method, desk for his "I think" (D32); Q3 asks only pod against desk |
| C45 | **A pod edit can change live risk without his click** (REVIEW M2): the node trusts the compiled fingerprint its G record tested; a pod outside that fingerprint is not re-tested; D31's anchor-change seat and a copilot pod patch could reach a running deployment | resolved as a rule | Moving a live deployment to a new pod version is the owner's click bound to that pod's hash; one click may cover many members; agents and the copilot write drafts only; G tests the logic fingerprint and the pod's blocks pass their own checks (S14, V4, Q6) |
| C46 | On-by-default blocks read data that does not exist at the first tick (REVIEW M4): the percentile bench, the cut from winners' MAE, the day stop's sigma, the parent limit's co-movement, the hurdle's cell | resolved as rows | Every default declares its cold behaviour (`until_n` on S4; the 4.1 column); K7 walks from zero trades and zero fills to a filled entry |
| C47 | A stale calendar "fails closed" against "sitting duck" (REVIEW S17): a dead free feed would park every template unit that tolerates nothing, with nobody told | resolved | A `fail` row per sticker source; the default is a card and `prefer not`; the kill switch keeps the hard kill (S10) |
| C48 | Restart: anchors passed while down, stickers that expired while down, five states and the cushion ledger rebuilt (REVIEW S23); only `risk_stop` has a restart test | resolved as a rule | A catch-up-at-start rule in the fold (R9); cold restore of calibrated values from calibration rows is UNKNOWN (Appendix C) |
| C49 | Any app or agent can write `source: app:mis` on a reading (REVIEW S26) | resolved | The host stamps `source`; the writer never does (S8) |
| C50 | "One folder, zero core edits" against a new fact a brake needs, and against a stdlib block that bumps the money app and needs his signature (REVIEW S27) | open, traced first | The Library path is the door and must be traced end to end before the promise is made (S16, D46); a truly new fact is a kernel change and is said so |
| C51 | `_CEILING = 0.005` in the sizer contract test and the exit test feeding evidence the host refuses (`SWAP E9`, `E10`) | resolved | Fixed before a real block lands, under K9 |
| C52 | `E1` Appendix A idea 19 "a gate can't change size; only the sizer socket can" against the chain verb `shrink` | resolved | A link may shrink only through the entry chain with its reason on the receipt (S6); both the modifier chain and the entry chain write the same receipt (R1) |

---

## 6. Architecture forks that are real

Seven structural questions where versions should differ in shape, not plumbing. Each names the shapes, what each buys and costs, and the test the harness runs on both. None is decided here. The review (S20) found four of the first five already decided by the core list; so every core row that presumes a shape is marked **if F1=B**, **if F3=B** or **if F7=one chain**, and an architect drawing another shape may strike the marked part and say what replaces it (section 3). Section 4 ships one default on F2 that an architect may replace. The architects draw them; the fold picks with recommendations (M37).

**F1. Where risk rules run: unit, pod, or group.** Includes the old F-B.
- **Shape A, compiled in plus a thin group.** A pod is a design-time recipe expanded into the unit's own sizer, controls, reads and numbers; a thin group document holds only shared caps and a ledger (`E2` Way 1 plus thin group; candidate 3's unit-owns-its-brakes). Buys: the unit stands alone; backtest and node run the same thing; a scalper's brake travels with it; least new contract. Costs: a pod edit recompiles every member and the node refuses each until it has a fresh record, unless the two-fingerprint seat exists; cross-unit rules have no home beyond caps.
- **Shape B, one pod document split by scope.** Blocks declare placement; unit-scope blocks run in the unit's call, cross-unit blocks in one group stage on the node, slow blocks off-path at anchors publishing facts; an empty slot means the unit's own block, so "no pod" is the empty pod (`E2` Way 5). Buys: all four unit origins with no special case; pod-life questions become fields; one edit rolls out by pin, under the owner's click (S14); candidate 3's property test says two cut-only stages equal one table over 20,000 states (MODEL). Costs: the most new contract; a size trail crossing two stages; a pod lives on one place, so spanning is a mix of pods. **The core marks S14's empty pod and placement rows, S4's placement field and S6's group stage "if F1=B".**
- **Shape C, a live group document above units.** The host's evaluator sizes and brakes every unit; units propose (`E2` Way 2; candidates 1 and 2's guard). Buys: one rank table, one edit for 200, agents watch pods not units. Costs: the unit's own sockets and five shipped halts go unused; a unit no longer stands alone at trade time, so V7 is restated for this shape as "every shipped template stands alone with its group"; the QMB host call must be built.
- **What the demo's intent adds, in every shape** (`UI-LOOK.md`, a picture of intent, not a spec; his later words win where they differ): the pod owns its sizing method; a unit alone needs its own; a pod with money and members needs pod-level numbers; a size trail walks one trade block by block. No slot list or block name on those screens binds a shape.
- **Harness tests:** X4-01 (losing together), X4-14 (everything bad everywhere), a pod edit across 200 members under one click, one scalper's entry latency with and without a group stage (UNKNOWN today, `E2` UNKNOWN 2), a unit arriving from a mini app with its own sizer.

**F2. How a number moves.** Includes the old F-A. **`E5`'s mechanism tables do not settle this fork** (REVIEW M5): they show that three mechanisms behaved as described on made-up worlds, and section 4.1 ships one of them as a default an architect may replace.
- **Shape A, learner and applier.** A learner publishes a target with bounds into status; an applier moves the value only in the number's mode (`off`, `at_flat`, `at_period_open`, `live`), with a retune share cap per cluster (candidate 1, VPA). Buys: numbers move between anchors; bands he can see; a measured herding guard. Costs: more parts.
- **Shape B, refresh at anchors.** Every derivation recomputed at the anchor and applied at the next; `authority` holds `off` or `at_anchor` (candidates 2 and 3). Buys: nothing moves unexplained. Costs: a day's lag on every learned number; all numbers move at once.
- **Shape C, find, track, correct.** A replay finds a start; facts track live; the built motion engine corrects from own trades, bounded, switchable per type; no applier object (`E5` 2.4). Buys: each job uses data suited to it; no new part. Costs: wander in calm conditions; the engine must reach risk numbers and gain a window; herding for sizes untested.
- **Harness tests:** X4-39 (the broker changes its costs), X4-60 (slow decay), a replay that flattered the edge, 200 units through one shared volatility shift (sizes, not filters).

**F3. Where the market sensor and the gate live, and who publishes.**
- **Shape A, the gate in a guard package.** The SQS rule and its baseline producer inside a guard package, eight settings as rows (old DP25). Buys: one place, one rank table. Costs: hard-wired shape; the first entry waits for a baseline.
- **Shape B, node sensor, unit gate slot, one curve artifact.** A node-side sensor publishes with source `node`; each unit's entry chain has a gate slot with a verb list; an overnight curve factory produces one artifact read by SQS, MIS and QMB; any app publishes readings in the same record (`E1` SQS-2, MIS-2, MIS-4). Buys: scalper and ORB get different answers; no warm-up; a dead MIS is safe by structure; departments publish. Costs: the most new seats; curves stale across a real shift. **The core marks I6 "if F3=B".**
- **Shape C, the sensor inside the MIS, units read it.** Rejected before because the board fails open; with stickers in the stand-down table it is a different case. Buys: one app. Costs: a central dependency on the order path; V7 is restated for this shape as "every shipped template stands aside, not alone, when the MIS is down".
- **Harness tests:** X4-16 (the release the calendar missed), X4-32 (spreads widen everywhere), the MIS stopped with a wide-list unit running, a holiday on a same-minute curve.

**F4. Node execution at 200 units and across two places.** Replaces the old F4 (file plumbing) at the review's request.
- **Shape A, one process, one `node-runtime` thread per node** (`runtime.py:2157` today), all pods on that node's place; a group row per place; cross-place caps are published facts at anchors. Buys: one order, no races, the code that exists. Costs: 200 units behind one thread at scalper rates (latency UNKNOWN); a pod cannot span PC and server.
- **Shape B, one process per pod or per place with a shared fact relay.** Buys: isolation per pod; a bad pod stalls only itself. Costs: shared caps across pods become relayed facts with age; the kill switch and `account-daily-loss-halt` must be atomic at the account, which spans processes.
- **Shape C, atomic per place, eventual across places.** Per-place caps are atomic in the chain; cross-place caps (the account on two brokers, PC plus servers) are stickers published at anchors with expiry; `E2` rt4's "a pod lives on one place" is the rule, and a group across places is a mix of pods with shares. Buys: honest about what can be atomic. Costs: the default group row and the account halt need a per-place form and an across-places form.
- **Harness tests:** 200 units on one fake broker at 1m bars (throughput and lag); the account on two brokers; PC plus one server with the server lost mid-session; a restart with anchors passed while down (R9's catch-up rule); X4-48, X4-49, X4-55.

**F5. Exits: ownership, rank, venue, and the pod's reach.** Kept.
- **Shape A, exits on the unit with the compiler's fixed order (close beats partial beats amend); the node closes targets** (candidate 3, old DP26). Buys: the unit stands alone; works today. Costs: backtest and live differ on a wick.
- **Shape B, an exit stack ranked "safest wins" in a shared stage; targets rest at the venue** (candidates 1 and 2). Buys: backtest equals live on a wick; one rank table. Costs: an amend may wipe the stop until R24 proves otherwise (CHECK B6); exits touch a shared stage, so the separate exit path (S3, V1) must be shown to hold there.
- **Shape C, exit rows a pod may swap at an anchor without a new unit version** (the scalper voice's ask, `E2` round table). Buys: tighter cuts as a stage changes without re-proving. Costs: R changes under the record; the logic record needs would-have rows to survive; the move is a click under S14's rule.
- **Harness tests:** X4-25 (weekend gap through the stop), X4-31 (flash crash), a stop and target on one wicked bar in QMB and on the fake broker, a pod swapping the cut width mid-record, a faulty exit block falling to the next rank.

**F6. Core size and delivery.** New (REVIEW S20).
- **Shape A, everything at once.** The 51 rows widened together, then templates on top; one re-test. Buys: no half-shapes; one format. Costs: the opposite of small verified PRs; a long time to the first paper trade.
- **Shape B, a small core widened in slices.** Land the sockets the first baseline needs (S1 to S4, S6, S9, S13, S17, I2 to I4, R1 to R4, K7) first, templates on them, then the rest in slices; bumps are free before the first deploy and K8 pays for any after. Buys: a paper trade early; each slice verifiable. Costs: temporary half-shapes; the discipline to bump only on a changed decision.
- **Shape C, templates first on today's narrow socket, widen behind them.** Ship A, B and C on the narrow shape (one sizer, one stop, one target, one time exit), then widen. Buys: the earliest paper trade. Costs: the templates lie about what they will do; two migrations instead of one.
- **Harness tests:** time to the first filled paper entry on K7; number of re-tests after the first deploy; count of units whose fingerprint moved per slice.

**F7. The entry chain as one mechanism or several seats.** New (REVIEW S18, S20).
- **Shape A, one ordered chain.** Every link answers pass, shrink or refuse at a scope and writes its verdict on the decision row; the gate slot, stickers, kill effects, group stage and order veto are links (S6 as written). Buys: one receipt trail; one wrapper protecting exits; one test. Costs: one shape for things with different clocks (a sticker expires, a veto is per order).
- **Shape B, several seats as today.** `guard`, the hook, the protection gate and an SQS gate, each with its own contract and caller. Buys: the code that exists; each seat small. Costs: five places that can refuse, five receipts, five failure modes to protect exits from.
- **Shape C, two chains.** A unit-side chain (gate slot, stickers the unit tolerates, its own caps) and a node-side chain (kill effects, group stage, order veto). Buys: the unit stands alone for its own links; the node owns the account. Costs: two receipts to join.
- **Harness tests:** X4-59 (two controls disagree), chain latency at scalper rates, a hung link, where the receipt trail is written and read back by `explain_size`.

Not forks: the level ladder against an evidence bar (D4 made the level a modifier); the Book against tags (D35, his later); the old shapes A, B and C of the first funnel (REVIEW M12); which file holds status (plumbing; the old F4).

---
## 7. Coverage of `SEEDS-2.md` Part C

Every checklist item, with where it landed. "Landed" names a decision (D), a core row (S, I, R, K, V), a baseline section, a hand-off (section 8), or a flaw (C). An item not held is marked so.

| Item | Landed |
|---|---|
| H-01 trades | 4.1; S1 to S4; K7 rehearsal proves it; honest state in 4 |
| H-02 sizes itself | D3; S1; 4.1 sizer |
| H-03 configures itself | D15 to D17; S13; 4.1 numbers |
| H-04 template | 4.2 |
| H-05 own configurations plug in | D15; 4.3; S14 |
| H-06 out of the box | 4, after the sockets land in slices (D41); K7 walks it from zero history; C3 |
| H-07 works before the numbers | the labelled-values principle and the builder's placeholders (section 4) |
| H-08 someone new | D49; 4.2 canary; K7 |
| H-09 baseline plus layer | sections 3 and 4 against the blocks in 2 |
| H-10 canvas, not policy | every "both, as swappable blocks" in 2; V9 |
| H-11 improved any way | S16 save door; D45; D46 |
| H-12 not rigid | refusals turned to warnings (C9, C12, C22); V9 |
| H-13 nothing in stone; pod questions are configuration | D11; D33; `QUESTIONS.md` filter |
| H-14 finishes the unit as a whole | section 3 covers every slot; D47; D48 |
| H-15 maintainable | D50 |
| H-16 performs | D14; D3 parent-limit default; no cut-only law; sitting-duck advocate content (8) |
| H-17 goes live | V4; D40; K5; no dollar gate on the path |
| H-18 any amount of stress | S4; S14 (if F1=B); chassis stress battery D39 |
| H-19 design for complexity | 3.7 lists what the fix round merged or demoted (51 live rows); the learner object, the rollout field, twins, lineage and the recipe kind are content; spec and status stay (I9) |
| H-20 one template by type; types change | I9 free type tag; 4.2 |
| H-21 scalper differs from intraday | 4.2 A against B; D26 |
| H-22 mean reverting differs from trend | D7 families; 4.2 |
| H-23 every number has a reason | S13; R1; the builder's labelled placeholders (section 4) |
| H-24 derivation changeable | D15 |
| H-25 ranges and reasons for moving | S13 (its per-change record) |
| H-26 some his, some self-set | D17; never-self-tune list |
| H-27 no key setting blank | S13: a blank warns, and a template may demand a value before its owner's live click (V9); the census K9 |
| H-28 sizing not leaning on the edge; edge as a range | D3 default needs no edge; the edge band on I9 (claim and band); D4 |
| H-29 a weak edge can still pay | **Not delivered by the default sizer.** The seat is S2; the first block that would carry "amplify" is the cushion rule's press half or a persistence press, no value set (D14); C1 is open; no proof exists |
| H-30 sizing across all instruments | S1 converter; I4 |
| H-31 adjusts over pips and points | S1; I4 |
| H-32 unit of measure settled | D1 dollars; the seam word is Q3 |
| H-33 more than one position | S17; D48 |
| H-34 growth over 24 hours not one fixed percentage | R9 anchors; D13; stage switcher content |
| H-35 the next day | R9 anchor clocks; restore by rule 4.1 |
| H-36 start with little, let it adjust | D3 cushion base with a user floor; I3 budget share |
| H-37 frequency as a sizing basis | trade rate on the fact surface D2; frequency blocks content; C1 open |
| H-38 costs known per market, instrument, timeframe, time | I2; I4 |
| H-39 QMX observes costs and acts | D18; D26 |
| H-40 off an instrument on its news day | D29; S10 |
| H-41 drift rule from agents | D16 correct; D44; three speeds content; methodology (8) |
| H-42 same on demo and live | I3 budget share; V10 |
| H-43 demo units at first boot | 4.2 templates and the canary on the paper lane |
| H-44 plans behind the code read | `SWAP` read the plan against the code; `UNIT-PLAN.md` not read in full by this judge (Appendix C) |
| H-45 stand-ins planned for the swap | section 3 placeholder columns cover PH 1 to 31; PH 19 is the protection-escalation row on S4 with `close` or `alarm`; `hedge` appears nowhere on disk and is content; PH 24 is a restore row (S4); PH 26 (judge with fixed size) is the report with and without motion (4.1) and a judge baseline for methodology |
| H-46 dictionary's closing mechanisms used | D7; S3 |
| H-47 fast invalidation everywhere | 4.2 A on; D7; C1 |
| H-48 stop chosen on purpose | D7; I13 |
| H-49 dynamic SL and TP looked up | D7 (`H2 I74`); 4.2 B |
| H-50 closing never blocked | V1 |
| H-51 brakes and accelerators defined | S4 row contract, few required fields, the rest defaulted (R9's nine attributes as the long form); D8 |
| H-52 definitions from his words | D13 (his reverse house money); R9 built on the transcript |
| H-53 some taken, some refused | `FATES.md`; D10 on against off |
| H-54 house money stays | D13 |
| H-55 reverse house money available | D13, on in the scalper template |
| H-56 tools, not law | D14; the labelled-values principle (section 4) |
| H-57 old circuit breaker improved | D10's two-speed block is present in both templates, off, with his reason on the row (4.2); the fast half is the money bench, the slow half reads the fire record |
| H-58 alpha decay | D16 correct; CUSUM block content; D44; methodology |
| H-59 know what is breaking | S4; R4 |
| H-60 brake set open | D10 |
| H-61 no one standard for frequency against brakes | own-percentile block; per-type presets D16 |
| H-62 what frequency does to brakes | `H2 I6` finding on the row (MODEL); methodology (8) |
| H-63 exposure, drawdowns, unrealised and realised measured | R9; I3 basis |
| H-64 isolation by class, region, instrument | D27; D28; S10; S11 |
| H-65 floor not reached; his to set | user floor on the cushion base; V5; never-self-tune; "not reached" is a numbers-talk claim, not a mechanism |
| H-66 scenarios generated | replay path S15; scenario kind and generators content; X4's 99 as data |
| H-67 risk at unit, cluster, methodology, portfolio | S11; S6 (group stage); S14 |
| H-68 Book and BMS open | D35; C15 |
| H-69 BMS self-optimises | allocator off-path at anchors (`E2` (c)); best basket and slot rebalancer content |
| H-70 pods ship | D36 |
| H-71 pod ideas offered | D34 gallery of twenty |
| H-72 mini app with the risk system | D36; Risk Lab app content (`H3 T34`) |
| H-73 new mini apps | D36 landers |
| H-74 mini apps feed each other | D37 roads |
| H-75 units from any source trade | V7 |
| H-76 new versions of the risk part | D40; D36 levels |
| H-77 schemas | S16 real kinds; schema beside code (`H3 T8`) under K9's census |
| H-78 external code | D46 |
| H-79 agents reach it and know it is correct | D43; contract tests K9; the self-test card is content |
| H-80 QML against slop | D45; `E4` 8d skill rules |
| H-81 Python only where QML can't | D46 |
| H-82 QML dictionary improved | D45 content, early |
| H-83 the unit is what ideas become | D45; D46; S16 (the save door) |
| H-84 a new unit or pod any day | D36; D37 says what the futures week still needs before it can run |
| H-85 lens beyond the unit | 2.8 to 2.14 |
| H-86 MIS, SQS, brakes, accelerators, QML open | D22; D26; D10; D14; D45 |
| H-87 overhauls must perform better | evidence labels on every option; `E1` recommendation reasons |
| H-88 MIS as router holds its weight | D23 finder content with lists scored side by side |
| H-89 how does the MIS adjust | D24 |
| H-90 sniping windows found | D30 |
| H-91 session opens catered for | D30; S9; `open` stickers |
| H-92 physics and RVOL have a place | D25; I7; `QUESTIONS.md` Q2 |
| H-93 trading node ideas | S6 (the gate slot; the node sensor if F3=B); S18; D47 |
| H-94 where it runs left open | placement field on S4 and S14 (if F1=B); fork F4 (two places); a pod's home is one place |
| H-95 cTrader first, then Hyperliquid | FX via cTrader in 4.2; crypto rows content; D21 |
| H-96 he does not monitor | D44; 4.4 |
| H-97 200 units real | D44; I9; R9 fleet read |
| H-98 agentic workflow as a mini app | D44: a scripted watch ships in this build (4.1 Fleet); the app read door and card path are core (K2); agents on top go to the agentic upgrade (8) |
| H-99 never-real edge found earlier | twins are content on S14's deployment key; family and claim on I9; `H4 I-01` kit (methodology) |
| H-100 logging, monitoring in the lens | D42 |
| H-101 he can tell what is working | R9 state word; six words (UI) |
| H-102 ledger exists and grows | ledger v1 stays a planning map (835 rows, re-tier before relying, `H2 I97`); the runtime truth is the number spec and the control rows (S13, S4); the couplings check is content under K9's census |
| H-103 terms agents can use | words table; D32; `E2` (a) |
| H-104 agentic upgrade has room | D43 doors; section 8 |
| H-105 copilot talks numbers and makes templates through QML | 4.3; templates folder; numbers talk (8) |
| H-106 tools for agents | K2; S16 (the save door); section 8 |
| H-107 agents propose, he promotes | V3; V4 |
| H-108 MCPs and the Lab | S15; agentic upgrade (8) |
| H-109 Shepherd and departments | section 8 agentic; D37 desks |
| H-110 a mini app per market as his pod | D32 desk; D37 |
| H-111 failed strategies reworked | D16 hill climb as a Lab job; methodology |
| H-112 findings stored | window cards (S9); failure cards content (`E4 L20`) |
| H-113 methodology per kind plugs in | S2 level modifier; I9 free type tag; verification template per type content; section 8 |
| H-114 edge verification as a workflow | R8 arms; twins content on S14's deployment key; methodology |
| H-115 Monte Carlo and backtest reading by agents | methodology (8); judge presets exist |
| H-116 UI needs list | section 8 UI |
| H-117 notifications are a UI question | section 8 UI; alert fields R4 |
| H-118 UI itself and its notes looked at | held in the fix round: the lead opened the running demo and wrote `round-2/UI-LOOK.md`, read as intent, not spec; D32, D33 and the pod vocabulary were corrected against it; the UI build stays the UI session's and may be overhauled entirely (Appendix E) |
| H-119 500 to 5 grand expressible | D3 full Kelly block; D14; V9; the argument is parked |
| H-120 small capital concentrates | I10 best-basket mode; I17 feasibility verdict |
| H-121 large risk per trade can be set | fraction open; `E2` Pod 20 |
| H-122 a harness runs worst, realistic, best | S15 drivers; harness content; the large-risk run itself is methodology and numbers talk (`H2` gap 1) |
| H-123 earlier output used, not redone | `FATES.md` covers X0 to X7, H1 to H5, E1 to E5; this file cites them |
| H-124 paper findings walked as ideas | `FATES.md` H5 and E3 rows; the walkthrough page (stage 7) must show them, this file only places them |
| H-125 ideas beyond the lens kept | `FATES.md` other-session rows; section 8 |
| H-126 logic linked across sources | D45 joints and fields; `E4` |
| H-127 unit idea bank kept | `FATES.md` UB rows, content |
| H-128 architecture versions shown | section 6; stage 4 |
| H-129 one fold with recommendations | every D names a pick and default; stage 5 folds |
| H-130 best, more than one, or a range | section 2's picks |
| H-131 flaws and collisions hunted | section 5 |
| H-132 agents solve issues | defaults on every open point; `QUESTIONS.md` filtered to five |
| H-133 ends with plan and orchestrator prompt | stage 6 reads sections 3 and 4 |
| H-134 no numbers, methodology or pod questions | `QUESTIONS.md` |
| H-135 no $500 bias | no dollar simulation used; no default stands on a model result (section 4) |
| H-136 raw words read | section 1; `SEEDS-2` Part A read in full |
| older 2 N8N extensibility, white label | D36 diffs plus pins |
| older 3 types: MR scalper, ORB, trend | 4.2 A, B and the `orb` variant |
| older 11 edge-led sizing expressible | D3 Kelly block |
| older 14 Kelly after costs | D19 ceiling block |
| older 16 one-shot breakeven | D7 breakeven block, off |
| older 19 same bet once | I9 bet key; S6 (group stage) |
| older 20 System 1 over System 2 | D23 rungs 0 and 2 |
| older 22 losing-run brake per type | D10 count brake |
| older 26 kill switch and SQS outside | D26; V2 |
| older 29 Books register on the BMS | D35 group with parent |
| older 37 where it runs | S4 and S14 placement (if F1=B); fork F4 |
| older 39 what QMB hands over, what the MIS publishes | the expectation at birth (content); S8 |
| older 41 micro and macro from agents | D22 MIS-2 publishers |
| older 44 borrowed designs | `H3 T8` to T10 (n8n, Helm, StrategyQuant) under D36 and D39 |
| older 53 other industries | D10 (grid, SRE, reclosers); `E4` section 4 |
| older 55 tooling | replaced by O-67 |

---

## 8. Hand-off lists, ready to paste

### For the methodology session
- The question he set: how an agent knows a unit is valid, per type, start to finish (M49, M50).
- Open here and yours: C1 (the cut's two-arm test on fixed entries); C29 (paper length); C40 (overfit; carry `E3-3` and `E3-2`); the pass rules behind `E4 L02` (six arms), `L03` (name the shuffle), `L05` (judge a rule by replacing it).
- Inputs ready: `H4` section B (I-11 to I-32) and D (I-42 to I-49); `H4 I-01` never-real kit; `H5` ideas 1, 12, 13, 45, 46; `E3-1` to `E3-5`; `E3-19` (trend meaning flips by horizon); `E5` section 5's scripts in `D:\Temp\e5` as a starting kit; `CH18:95-102` eight steps; `CH18:121-129` class table; `R3` 1.2 tool table.
- Seats this funnel left for you: R8 arm fields; family, parent and the scoreable claim on I9; the level modifier on S2; the verification template per type as a preset (`X5-H40`); the judge baseline with fixed size (PH 26). Content you may ask the build for: twins and canaries on S14's deployment key, lineage beyond I9, the expectation at birth.
- Warnings: every "core" X5 fate came from the go-live and dollar lenses; honest evaluation certified no LLM-found strategy (`2608.27734`); resize replay explores, a QMB rerun proves.

### For the agentic upgrade session
- The door: D43 (read, propose, run; direction on every tool; evidence intake per unit; protected fields; the money door outside agent reach, `E3-26`).
- Harness flaws, measured: `H4` section 6 (20 rows) and `E5` section 6 (19 rows). The first ten to fix: one unit template; no row saves a block; compile refusals; no fleet read; an app cannot read journals (`data_reads` is `market` only); an app's `workflows` entrypoint has no installer; app-to-inbox path unconfirmed; `build-mini-app` and `build-pod` skills are placeholders; tools declare approval not direction; judge lands as the operator.
- Jobs (content, yours): triage, morning words, coroner, sitting-duck advocate, drift explainer, prospector, slow isolation cards, per-class agents and event mapper, template version drafter, tuning proposer under the applier (`H4 I-40`, `I-67`; `E5` 1.2).
- Department seeds: `handoff/AGENT-DEPARTMENT-SEEDS.md`, M35, M50; `H4 I-68` to `I-78`; `E2` (e) desks; `E3-25`, `E3-27` to `E3-30`; `H5` ideas 2, 3, 7, 38 to 44.
- Conditions: agents never touch money; only he promotes; exits never blocked; Q4's default until he rules.

### For the UI session
- The lead opened the running demo in the fix round (`round-2/UI-LOOK.md`), read as a picture of intent; the UI build, its notes (`UI-NOTES-UNITS.md`, `UI-BACKLOG.md`) and any overhaul of the UI are yours (Appendix E, O17).
- Needs from this design: a size trail equal to the decision row (`explain_size`); the six words and UNKNOWN; stickers and tolerations shown, with "why didn't it trade"; the pod gallery (D34) and the empty pod; the fleet screen (one screen at any fleet size, ranked rows, one incident one card); first-run ticks on done not opened; alert tiers against Settings' "Alert me when" and the phone push list; the MIS tab, market card, weather report; a card's wording for a stranger; the kill line warning in the largest type.
- Lists on disk: `X6` section 9 (16 screens); `X7` Appendix B; `E5` section 7.

### For the numbers talk
- `PARKED-FOR-NUMBERS-TALK.md` plus: the fraction, floor and base of the default sizer; the two halts' limits; the cost allowance and SQS floor line; k for the portfolio day stop and for any admission gate (with REVIEW M4's table beside it); the parent limit; the count brake's run length; press strength and anchors; K and the strict bar for the fleet watch; whether gold's windows hold (R2 against his M50); 500 to 5,000 and large risk without ruin (`H2` gap 1: no design on disk used that lens; Group B of `H2` is the parts list); game theory (`1912.04012`, `md\15541`, `md\17546`); where to allocate units across instruments (`E4 L18`, `E3-23`); and the builder's labelled placeholder values for every on-by-default block (section 4), which are yours to change.

### For the walkthrough page (stage 7): his direct questions that still want a plain answer
He asked these in M49 and the first page never answered them (REVIEW S9). One line each, to be said in his words on the page:
- "What exactly is a starting level?" The old design's fraction of full size a unit begins at. This funnel has no ladder law: the level is one named modifier (S2), set by the template, and QMB's proof does not set it.
- "What do you mean by unit stepping down?" A control reducing a unit's size or benching it for a rest by its own rule, then restoring it by rule; only HALTED and the kill switch wait for a hand (S4).
- "Why lots?... explain to me." Dollars at risk decide every size; lots are only what the broker accepts at the last step, through one converter (D1).
- "What do you mean by a rule I approve?" The old page's house-money switch-on. Here it is a block (the press gate) a template turns on or off; nothing asks for approval (D13).
- "At 1 unit, .83, typical end is 1,400. After how long?" That was the old model's 120-day run; it decided nothing here, and no number like it is in this design.
- "my scalper may not exist yet." The honest point under C1: at a 5-pip stop the pictured scalper loses after costs unless the fast-invalidation cut catches few winners; the cut ships on with that warning, and the two-arm test is the first Lab job.
- House money: "let's first talk about it." D13 in plain words: one rule, one ledger of profit since an anchor; on in the scalper template because he asked, value open.

### For the repair session (DeepSeek), nothing to do now, flags only
- Files this session claims before deletion-4 and C-20: `sqs_baseline_producer.py`, the SQS rule text in `labelers.py`, `qmn/replay/port.py`'s SQS rule, `registry_catalog.py`'s SQS rows, `qmn/data/news_calendar.py`, `qmn/protection/windows.py`, `dispatch.py`, `qmf-risk/control_window` (old DP24, DP25; `handoff/FOR-REPAIR-CLAIMS-BEFORE-C20.md` must add the last three).
- Findings: `SlowState.read` has no bound and reaches snapshots (`engine.py:124`); the stale-board fallback trades every listed market (`runtime.py:367-369`); the sizer slot has no face check and 5,000 lots passes the QML host (`SWAP E8`); `_CEILING = 0.005` in the contract test will fail any real sizer (`SWAP E9`); the exit contract test feeds evidence the host refuses (`SWAP E10`); entries ignore the kill effect table (`SWAP 18`).
- Open hand-offs from App F still stand (`SWAP 4.3`): the signed stop distance, target at broker or node, a unit with no stop, moved numbers and open trades, which exit wins on one bar, R and costs, kill level meanings.
- Bumps: free until the first unit deploys and only when a compiled decision changes (D41); the re-test workflow (K8) is this session's, not repair's.

### For the release lane
- `E5` G1 to G3: no installer a stranger can run; install and launcher describe the older host; first start hands over to a desktop app nobody could find.

---

## Appendix A. The party, run headless

Four voices, one mind: a scalper (trader), a risk quant, a systems engineer, a developer who will maintain this. Nobody could be asked anything. The exchange below is the part that changed a call; the rest agreed with `E1` and `E2`'s own round tables and is not repeated.

**Trader:** Your horizon formula decides my size by a survival sum I can't explain to myself. The fixed fraction I can. Ship the one I understand and let the clever one be a block.
**Quant:** The fixed fraction has no survival story at all.
**Trader:** It has a floor I set and a daily halt I set. That's a survival story a person can hold.
*(So: D3's default is the fixed fraction; the horizon formula is a labelled block.)*

**Developer:** The node refuses a fingerprint its record didn't test. Once a unit is live, every format bump means a new test record for every deployed unit.
**Systems:** Nothing is deployed yet, and the format bumps only when a compiled decision changes.
**Developer:** Then land the sockets in slices while it's free, and build the thing that re-tests 200 units before the first one goes live.
*(So: D41's sequencing note and K8. My first pass wrote this as "one bump"; the review showed the premise false.)*

**Trader:** My cut is my risk management. If it isn't on in my template, the template isn't a scalper's.
**Quant:** If it catches a fifth of your winners it's a loss. Nobody has tested that after costs.
**Trader:** Then say so on the block and let me run it anyway.
*(So: the FI cut is on in `scalper-mr` with REVIEW M4's caveat on the block; C1 stays open; the two-arm test is the first Lab job.)*

**Systems:** Three spread measures in three places is the actual bug. One curve.
**Quant:** Curves are yesterday on a shock day.
**Systems:** Then the reading says "far from usual", which is the true thing. And when the factory dies you still have yesterday's.
*(So: I6, one curve artifact, with an age word.)*

**Quant:** A cut-only agent fact that applies itself is an agent touching money.
**Systems:** It's a reading the unit chose to read, inside bounds the pod declared.
**Developer:** Which of those two he meant is his to say.
*(So: C16 open, default stated, `QUESTIONS.md` Q4.)*

**Developer:** "Why this size?" has no answer today; the receipt is a literal. Nothing you've listed matters if a developer can't replay one decision.
*(So: R1 moves to the top of the records, and the first contract test is same-decision-both-hosts.)*

**Quant:** The kill line as a warning, not a wall? He said reckless must be expressible. He did not say a pod with no floor is a good idea.
**Developer:** Then it says so in the largest type the screen has.
*(C12. One mind, both sides.)*

## Appendix B. Elicitation, run headless

**Pre-mortem.** It is May 2027 and the baseline failed. The likeliest stories, each with the row that answers it: (1) the sockets kept landing in slices after the first units went live, every bump cost 200 re-tests by hand, so nobody dared bump again and `reads` never shipped (K8's re-test workflow, D41's sequencing note). (2) The cost hurdle refused every scalper entry in costly hours for a month and nobody saw it, because would-have rows were declared and never written (R3 goes early in the build order). (3) The parent-limit default let eight correlated units lose together on one release; the portfolio day stop was a row nobody switched on (it is on in the group default, 4.1). (4) The templates were read as proof; a stranger went live on `scalper-mr` and lost (every card says "a shape, not an edge"; the live click needs the placeholders acknowledged). (5) Two hundred units, ninety cards a night, and he turned the alerts off (D44). (6) A pod edit forced two hundred fresh test records and pods were abandoned (I9's two fingerprints). (7) The copilot built a sizer that took a trigger-shaped block and traded 5,000 lots (S1's face check and limits in one place).

**Red team, against the core list.** *"Too much machine again."* Answer: a deletion test was run in the fix round, not before (REVIEW S18): remove the row and name what reappears or reworks. 3.7 lists the rows merged (one mechanism told twice) and demoted (additive, no rework); the core is 51 live rows. *"The baseline is still a sitting duck: halts, a hurdle, a floor, stickers, a parent limit."* Answer: every one is a block with an off switch and a labelled value; no cut-only law exists; the accelerators are a toggle away; the raise permission gate is a group row a reckless pod removes; the sitting-duck advocate is named content. *"You kept everything again."* Answer: fates are not kept or dropped, they are placed; the core is 51 live rows after the fix round (16 sockets, 12 inputs, 9 records, 5 hooks and proofs, 9 invariants); the first baseline switches on ten slots and ships three templates; everything else is content on those seats, and `FATES.md` says where each lives. *"The cost hurdle is a PROPOSAL and you made it a default."* True, and said so; its shape rests on REAL cost research, and SQS-1 stands behind it as the floor; shadow rows and the control gate will tell. *"Find, track, correct is one agent's model."* True; it is one side of fork F2, and the seats it needs are the same seats the other sides need.

**First principles.** What must a unit have to trade? A price, a size, a stop, an exit and a venue. Everything else is a reading or a rule it chooses to read. So every shipped template stands alone (V7); the core is the sockets, never the blocks; a reading is a record anyone may publish (S8); and the first baseline is the smallest set of blocks that fills every socket with something explainable, with an off switch, labelled by its evidence. Several of those blocks are PROPOSAL or MODEL and the table says so (REVIEW M5); none ships because a result ranked it.

## Appendix C. What I did not verify

- I ran no code and no test. Every line number is as H1 to H5, E1 to E5 and `SWAP` reported it at tips `255f3bbf` or `351e7521`.
- The lead opened the running demo after the review (`round-2/UI-LOOK.md`); I did not, and I read that note as intent, not spec. I did not open the UI notes, `UNIT-PLAN.md`, `CONTRACTS.md`, the Lab spine or the candidates' spines; they reach this file through `H3`, `E2` and `SWAP`.
- `accepts_evidence` (the old I8's Today cell, now in S8) was not found under `qml/src` by the reviewer; the claim came through `H3 T56` and is unverified.
- X0 to X7 reach this file through the harvests and `HYBRID-FATES.md`, not a fresh read of each hybrid body.
- `E1` Appendix A and `E4` section 9's seeds were read as lists; their fates in `FATES.md` are placements, not judgments of each.
- Closed by the review: `block_fingerprint` hashes `block.py` only (`loader.py:81-83`), so block-entry fields move no compiled fingerprint.
- UNKNOWN and carried as such: whether a Library block reaches a live node end to end; whether a newcomer's first day needs a broker (G8); whether the node processes units one at a time; whether calibration rows can rebuild a cold restore; the real latency cost of a group stage at scalper rates; his original wording of the MIS and SQS design request.
- The party and elicitation were one mind. Their dissents are recorded, not independent.

## Appendix D. Fix round, 7 Nov, against `round-2/funnel/REVIEW.md` and `round-2/UI-LOOK.md`

Applied with the lead's rulings. Decision ids are unchanged; section 3's row ids are kept, with merged rows left as pointers (3.7).

**Must-fixes.**
- M1: V12 dropped; D41 is a sequencing note (bumps are free before the first deploy, so sockets land in slices; bump only when a compiled decision changes; step 3 before the first deploy or it pays a re-test); the re-test workflow is core (K8); C25 corrected; Q5 cut to the landing branch; Appendices A and B rewritten where they leaned on "one bump".
- M2: S14 and V4 carry the rule: moving a live deployment to a new pod version is the owner's click bound to that pod's hash, one click may cover many members, agents and the copilot write drafts only, G tests the logic fingerprint and the pod's blocks pass their own checks; D31's anchor-change seat stands only under that rule; collision C45; question Q6.
- M3: section 3 is the whole core. Added R17 (identity and swap), I16 (override chain), I17 (feasibility verdict), K8 (re-test workflow), K9 (contract tests and census); the protected field list is on K5, the face check on S1, the generation stamp and claim on I9. Rollout field, self-test card, offers, module map and `EXTENDING.md` are content or scheduled with the swap. Every "core" in this file's decisions and in `FATES.md` now names a row; the script's count is below.
- M4: every on-by-default block declares its cold behaviour (4.1 column, S4's `until_n`); the hurdle warns while its cell reads `uncalibrated`; the builder picks labelled placeholder values, owner numbers talk; K7 runs from zero trades and zero fills and ends with a filled entry and the owner's promote click on the fake live lane.
- M5: every default has a configuration reason (4.1 column); the scalper press is on "because he asked for it, value open"; `E5`'s tables are cited only as "behaved as described"; F2 is marked open and 4.1's motion default replaceable; Appendix B's first-principles sentence made true.
- M6: 3.8 places every `SWAP` 1b and 2.4 refusal: a core row, a named "stays refused, and why", or content; `streams_not_built`, per-market settings and `context_needs` gained rows (S17, S8); `roll` and `routes` stay refused until a route exists; the target-position answer type is reserved on S3; the node's stop gate is a link in S6 and accepts a declared no-stop basis (I13); K9's census carries the table.
- M7: the app read door and card path are core (K2); this build ships a scripted fleet watch, one ranked row per unit, no agent (4.1 Fleet), and switches off the shipped decay rule's card per unit; C17 reads "answered on paper; ships with"; agents on top go to the agentic upgrade.
- M8: D32, D33 and the pod vocabulary corrected against `UI-LOOK.md`: a pod is a stack of blocks plus money and members on one place with paper and live sides; methods live side by side, so Book + BMS is a method name and nothing retires; a watcher is a mini app; "desk" stays his "I think"; the fold is keyed by pod (R9) and the size trail is the decision row (R1, S15).

**Should-fixes applied.** S1 (circuit breaker present in both templates, H-57 corrected), S2 (`HIS THOUGHT` label in `FATES.md`; six rows relabelled), S3 (seat kept only with M2's rule), S4 (K7 ends with the owner's promote click; "the account owner's hand" in V2 and V4), S5 ("amplify" named as not delivered, seat S2, H-29 corrected), S6 ("fits" M51, not his frame), S7 (C5 labelled as my reading; a per-trade MIS read expressible and warned), S8 (nothing retires), S9 (a list of his direct questions for the walkthrough page, section 8), S10 (the futures week: what remains), S11 (V5 reworded), S12 (V7 reworded; `fallback: stand aside`), S13 (typed amount on S1), S14 (V3 "on a live account"), S15 (a blank warns), S16 (the canary stated on purpose), S17 (`fail` row, default a card and `prefer not`), S18 (merges and demotions in 3.7; 51 live rows), S19 (widen and extract the existing handler first; required fields few), S20 (fork marks; F4 replaced; F6 and F7 added), S21 (venue capability on I4), S22 (swap governance on R17), S23 (catch-up-at-start on R9), S24 (exits on a separate path; faulty exit falls through), S25 (the group stand-down expires by rule), S26 (host stamps `source`), S27 (trace the Library path first; the signature cost named), S28 ("answered on paper"), S29 (evidence wording), S30 (references fixed), S31 (`accepts_evidence` marked unverified), S32 (stale board described as a docstring on an unwired board), S33 (no "dissent" claimed from one mind).

**Should-fixes rejected or applied in part.** S18 in part: three merges the review proposed are kept apart (stickers from readings, the instrument record from cost cells, sessions from stickers), so the core lands at 51 live rows, not 35; the reasons are in 3.7. Nothing else was rejected.

**Script report.** `fix2.py` (scratch) read this file and `FATES.md`: every sentence saying "core" in a decision paragraph of section 2, in the tables of sections 4, 5 and 7, and in a `FATES.md` fate cell must name a live or merged row of section 3 (demoted ids do not count). Decision sentences in section 2 saying core and naming a live or merged row: 21; unresolved: 1. Table rows in sections 4, 5 and 7 saying core with a row: 9; unresolved: 0. `FATES.md` fate cells saying core: 491; naming a live or merged row: 491; unresolved: 0. Live rows: 66 ids resolve (51 live, the rest merged pointers). The one unresolved decision sentence is D46's quoted promise "one folder, zero core edits", a phrase under test, not a core claim. Section 3's merged ids (S5, S7, I8, I11, I12, I15, R5, R6, R10, R11, R15, K1, K3, K6) stay as pointers so earlier references resolve; demoted ids (S19, I14, R12, R14, R16's fields, K4, V8, V11, V12) are named as core nowhere.

## Appendix E. What this proposes to overhaul

He wants to go through every overhaul when he is back ("overhaul is okay as long as the thing that is being brought in... makes better sense, can perform better", M33). This list names each thing this funnel proposes to change in shape, what it was, what it becomes, why, and where it is decided. Nothing on it is built. The UI itself may be overhauled entirely; `UI-LOOK.md` was read as a picture of intent, and where the demo and his later words differ, his words won.

| # | Thing | From | To | Why, in one line | Where |
|---|---|---|---|---|---|
| O1 | The SQS | one gate hard-wired in the old node: "is the spread unusual", eight settings, hours of warm-up | a node sensor plus a swappable gate slot; the cost hurdle ("does this entry clear what this unit allows for costs") as the default gate, the old rule as the floor for broken markets; the bank and the dial as blocks | a scalper and an ORB get different answers with no style code; no warm-up; "SQS stays" is kept as the floor | D26, S6, 4.1 |
| O2 | The MIS record | `source` is `node` or `mis`; one bar size; closes only | an open bus: any app, pod or agent publishes a reading in the same record under its own name, host-stamped; a shared curve artifact for "usual" | his departments feed each other; a dead MIS is safe by structure; three spread measures become one | D22, S8, I6 |
| O3 | The MIS router | a board that only narrows; a stale board trades every listed market (docstring) | the active list is a reading over allowed markets with home markets as the fallback; the finder is the first app on top | his M5 router; widening without a new version each time; the stale-board hazard closed | D23, I5 |
| O4 | Isolation, news and caution windows | three features: a kill table by currency, news windows on the node, an isolation protocol in shadow | one sticker on a market scope (kind, strength, expiry, why, who) and a toleration list per unit; the kill switch kept apart | dissolves four collisions; "it's a pod question" (M49) becomes a field | D27 to D30, S10 |
| O5 | The sizer socket | lots at the stop from four facts | a base answers a typed amount (money at risk, notional, quantity); one shared converter spells the venue's quantity; a named modifier chain with receipts | "why lots?" (M49); every base a block; the USDJPY fault fixed at root | D1 to D3, S1, S2 |
| O6 | Brakes | five unrun halt blocks, a kill effect table entries ignore, a hook stub | control rows with scope, verb, `on_fire`, restore, cold behaviour and placement; five states; halts that bind at four scopes | a pod chooses what a brake does; a new brake is a row; "brakes first" with a way back | D8 to D12, S4 |
| O7 | The entry path | several seats: `guard`, the hook, the protection gate, an SQS gate | one ordered entry chain, each link pass, shrink or refuse at a scope, one receipt, one wrapper protecting exits (fork F7 keeps the alternative) | one trail, one failure mode to protect exits from | S6, F7 |
| O8 | Exits | the first per-bar exit only, fed nothing, `close_full` only | a stack of every per-bar exit fed the position, three verbs, a declared rank, its own path | the dictionary's closing mechanisms come alive; trails, partials, FI and thesis exits possible | D6, D7, S3 |
| O9 | Self-configuration | a planned learner and applier beside the built engine | a number spec on every number (derivation, range, authority, reason) and find, track, correct on the built engine; the applier object a block (fork F2 open) | the engine already does the applier's job; no new part; "what if I want to change the way it is derived" made structural | D15 to D17, S13 |
| O10 | The fleet watch | the shipped decay rule: a card per flagged unit each night (about 91 a night for 200 healthy units) | a scripted ranked fold, two lists, one incident one card; agents on top later | "why would I have to be there monitoring units?" (M49) | D44, 4.1, K2 |
| O11 | Pods | the Lab's seven-slot design compiling to Book and BMS fragments | a pod document with blocks that declare their placement, an empty pod meaning the unit's own blocks, two fingerprints, methods side by side; the shapes stay open as fork F1; moving a live deployment to a new pod version is the owner's click | four unit origins with no special case; a pod edit never re-proves 200 units; his screens' intent kept | D32, D33, S14, F1 |
| O12 | Book and BMS | the documents and the words | a group document with `parent`, an allocation mode and tags; "Book + BMS" stays as one method name; nothing retires | his "decide later" (M49) honoured; intersections expressible | D35, I10 |
| O13 | Capital sharing | one square-root split as law | a named allocation mode on the group; own size under a parent limit as the default | "the more units I have, the less I can trade" (M49) and "split the day's capital" (M10) are both his; a row dissolves it | D31, I10 |
| O14 | The Lab evaluator | a separate pod simulator compiling to Book and BMS | the handler QMB and the node already share, widened and extracted, driven by Lab, paper and replay too | one size everywhere; no second core beside a working one | D38, S15 |
| O15 | Compiler bump policy | my first pass's "one bump" | slices, bump only when a compiled decision changes, a re-test workflow for bumps after the first deploy | the one-bump premise was false (REVIEW M1); 200 re-tests per bump is the real cost | D41, K8 |
| O16 | The vocabulary | "pod" for four things; "lots" at the seams | "pod" for the stack plus money plus members on one place; "desk" proposed for his department sense (his "I think", Q3); "quantity" on the wire as it already is | one word carried too much for a builder | D32, Q3 |
| O17 | The UI | a proposed design, mostly outdated; its notes propose changes | not overhauled here; the UI session may overhaul it entirely. This funnel's needs from any UI are in section 8: the size trail as the decision row, stickers and "why didn't it trade", the pod gallery and the empty pod, one fleet screen at any size, "Needs you" fed by apps, the kill line as a warning in the largest type | his words win over the demo; the slot list and block names on the demo bind nothing | section 8, D32, D33 |
| O18 | QML's roles and entries | 7 of 18 roles run; no derivation role; no block-save door | eight more roles run, `derivation` and `combiner` added; a save door with a contract test; linking fields on entries as content | "QML is the SDK" (M50); agents' ideas reach QMX as units, not slop | D45, D46, S12, S16 |
| O19 | House money | two rules on two ledgers | one rule on one cushion ledger; the anchor decides whether it presses or only brakes | his house money and his reverse house money, kept, with one home | D13, R9 |
| O20 | Readings and physics | the five shipped readings on H1 bars | every reading passes three floors (a named null, a bounce test, a use test) before it binds; fifteen physics rows as content in shadow | "new market physics... no problem" (M31), without a random walk in a costume | D25, S8 |
