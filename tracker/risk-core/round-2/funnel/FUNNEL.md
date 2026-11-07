# Funnel, round two: what goes in, what the core must carry, what ships first

Fable funnel judge, 7 Nov 2026. Round two of the risk and sizing session. Written under `round-2/BRIEF-COMMON.md`. Companion files: `FATES.md` (one row per idea) and `QUESTIONS.md` (what truly needs him).

**The test used, and only this test** (`BRIEF-COMMON.md:29-36`). For every idea: (1) is it configuration? Then a block, preset, template or pod setting. (2) If left out now, does the core get reworked later? Then the core leaves a socket, input, record or hook. (3) Otherwise it is content someone adds later, or another session's. No dollar simulation decided anything here. The old funnel's `HYBRID-FATES.md` and `architecture/SPINE.md` were read as material; its `REVIEW.md` findings on evidence, fidelity and logic are kept; its dollar verdicts are dropped.

**Paths.** Bare paths are under `D:\QMX-worktrees\risk-plan\tracker\risk-core\`. `H1` to `H5` are `harvest/H*.md`; `E1` to `E5` are `round-2/expand/E*.md`; `SWAP` is `unit-baseline/SWAP-CHART.md`, with `SWAP n` a row of its placeholder table and `SWAP En` a row of its 1b table; `MAP` is `review-2026-11-07/system-map.md`; `PH n` is a row of `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\build\RISK-SIZING-PLACEHOLDERS.md`; `PACK` is `RISK-SIZING-PACK.md` in the same folder; `SEEDS-2` is `round-2/SEEDS-2.md`, with `H-nn` its checklist and `T-nn` its register. Old decision points are `old DPn` in `funnel/FUNNEL.md`. Ids such as `X3-H63`, `H2 I4`, `H3 T6`, `E2 Way 5`, `E4 L02` point at those files. Code line numbers are as those files report them at tip `255f3bbf` or `351e7521`; I ran nothing and read no code myself.

**Evidence labels.** BUILT: in the code, as a harvest or the swap chart read it. REAL: live practice in its own field, a paper read by one of our agents, or a controlled test; the field is named. MODEL: our own simulation; it shows how a mechanism behaves, never that a real unit does. PROPOSAL: reasoned, untested. GUESS: an analogy. RULING: his words, cited. UNKNOWN: not verified.

**Words.** Unit: one self-configuring trading algorithm. QML: the block library and dictionary units are built from. QMB: the backtest and proof system. MIS: the market reader. SQS: the spread sensor and gate. Pod: a versioned stack of risk rules (seven slots in the Lab design); he also uses it for a hedge-fund department, which `E2` calls a desk. Socket: a place in the unit a block plugs into. Row: one declared control in a registry. Receipt: the record of how a size was computed. R: the loss if the planned stop is hit. Sticker: a typed, expiring notice on a market scope (`E1` section 4). Toleration: a unit's declaration that it ignores a sticker kind.

**How the skills ran.** `bmad-party-mode` and `bmad-advanced-elicitation` were loaded and run headless: one mind voicing a trader, a quant, a systems engineer and a developer, then pre-mortem, red team and first principles over sections 3 and 4. No memlog, no HTML, no scripts: the brief allows these three files only. The party's clashes and the elicitation findings are in Appendices A and B. They changed six calls, named there.

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
**Pick (c), core.** The derivation reads the full fact surface (D2). Lots exist only at the venue step. `Size.lots` at the seams becomes `quantity`; the word is his to confirm (`QUESTIONS.md` Q3).

**D2. What a sizing base may read.** Options: (a) four facts (BUILT); (b) `X2` restructure 3's list: budget share, committed cushion, open risk per bet key, own record (spread of results, edge band, cut distribution, trade rate), cost cell for this hour and world, gap factor, level, trading state, conviction binding (`H2 I13`, `I41`); (c) a thin surface over derivations only (PICK graft 2). **Pick (b), core**, with every input timestamped and carrying a declared fail mode (`H4` section 4). (c) and (b) agree only if derivations may read all of it, so (b) is the contract and (c) is a style of block. Today the compiler refuses every sizer input (`compiler.py:930-936`, `SWAP 1`).

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
**Pick: both and all of them, as swappable blocks on the one socket. Shipped default: fixed fraction of a declared money base (equity, or cushion above a floor the user sets), costs in the denominator, round down, residue real.** Values open: the fraction, the floor, the base. Why: it is the only base that is both BUILT in shape and REAL in practice, it needs no edge, no record and no MIS, and it answers "can size itself" at the first tick. The horizon formula ships as a second block, off, labelled MODEL; its "safe at zero edge" claim is a numbers-talk argument, not a reason to make it law. The parent-limit mode is the shipped answer to his M49 complaint (D21).

**D4. The level slot.** Options: (a) no level; (b) a level as a fraction of baseline, with a ladder law (holdout start, cohorts up, CUSUM down; old DP15); (c) a level slot with no ladder law; how a level starts and moves is a template or pod rule, and may differ by unit origin (`H2 I77`). **Pick (c), core slot, content rules.** He said QMB's proof setting a starting level is "I think no" (M49) and asked "what exactly is a starting level?". Four kinds of unit arrive (M49); a ladder law forces one validation story on all of them. The cohort ladder, BOIN steps, slow-start titration (`H2 I31`) and his calendar ramp are each a block.

**D5. Feasibility and the smallest size.** Options: (a) skip below the minimum lot and go dark (BUILT); (b) feasibility verdict per unit, instrument and broker, re-run at anchors, with a declared shed rule (`X2-H45`, `H2 I81`, REVIEW M9); (c) raise the share until the minimum fits; (d) lot dither (`X2-H46`). **Pick (b) as a computed, shown verdict (core); the shed rule, concentrate, borrow and dither are blocks (content).** The dollar sim's "100 % dark" figure is dropped as a verdict; the mechanism stays because a book that goes dark above the floor is what he called sitting like a duck (M8). Dither is not dropped: a user may want it on gold at small size; the shipped converter never rounds up by default.

### 2.2 Exits

**D6. The exit socket.** Options: (a) first per-bar exit only, fed nothing, `close_full` only (BUILT at tip, `SWAP 2-4`, `E15`); (b) an exit stack: every per-bar exit runs, fed `PositionFacts` (quantity, average price, stop, targets, bars held, MFE, MAE) and market evidence, answering `close_full`, `close_partial`, `amend_protection` with a reason code, the safest winning by a declared rank (`H2 I7`, `X3-H43/H46`, PH slot table) ; (c) exits in the risk profile document, not the unit (candidate 1). **Pick (b), core.** Exits stay on the unit, because an exit changes what R means and the logic record must survive a sizing swap (`H3` section 4 rows 8/8b; `E2` round table). Without all three verbs trailing, scale-out and breakeven are locked out, so "later" would be rework (`H2 I7`). Step 3 (trails, partials, the signed stop) waits on the node's partial close and R24's demo facts (`SWAP 9, 10`), and the socket must be shaped for it now.

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
**Pick: all as blocks on the stack; exit families per style are templates (`X3-H43`, content). Shipped defaults: disaster stop, R target, side-correct time exit, plus the scalper template switches on the fast-invalidation cut and the intraday template the thesis exit; breakeven off; trails arrive with step 3.** Every value open. "Not allowed" cells in the family table read "not advised" (`H2 I69`). R is a declared basis on the row (gross at the disaster stop by default; a no-stop unit declares a tail budget), never assumed (`H2 I72`). Stops tighten only by default; `allow_widen` is a row a template may set, warned, because widening must be expressible even though it is a classic ruin path.

### 2.3 Halts and brakes

**D8. Where brakes may run.** This is architecture fork F1 (section 6). The decision here is only the row contract: every control is one registry row stating what it reads, whose risk, measured from where, which lever, which direction, shape, attack and release speed, anti-chatter, memory, who clears it, counting rule, fail mode, money series, expected healthy fire rate, shadow switch, tail or timing class, and **where it may run** (unit, group stage, off-path) (`H2 I5`, `I9`, `X3-H58`, `H3 T6`, CHECK B9). **Core.** A new brake is a row plus one folder in the dictionary (PICK graft 7); no new `Kind` (`H3` section 2).

**D9. What a halt may answer.** Options: (a) `none`, `no_new_entries`, `flatten` (PH slot table); (b) add `reduce` with a factor and the five states ACTIVE, REDUCING, BENCHED, HALTED, RESTORE per scope (`X3-H59`, `H2 I58`); (c) stop only, as today. **Pick (b), core.** Only stops means every bad day is a stop or the book goes dark while he sleeps (`H2` section 4). HALTED and the kill switch stay his hand. Today `HaltInstance` has no caller and all five shipped halts refuse (`SWAP 5`).

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
**Pick: every brake is a block on the row contract; which binds is a pod or template setting. Shipped defaults (section 4): `session-loss-limit-halt` at unit scope and `account-daily-loss-halt` at account scope, both `no_new_entries`, restore by rule at the next day boundary with retry-then-lockout; the own-percentile bench and the count brake ship in the template, the bench on and the count brake off; the portfolio day stop ships as the group's default row with `on_fire: stand_down(all) + card`.** Values open. The random-control certificate (`X3-H13`) is a report, never a compile gate (REVIEW M5, kept). The old "one live reader per ledger" compile refusal (`two_live_readers`) becomes a template warning (`H3` section 2, `H2 I44`). The circuit breaker keeps its name.

**D11. What a brake does when it fires, at the portfolio level.** Options: stand-down at a scope; raise a kill level; send a card. **Pick: an `on_fire` field on the row (core); each pod chooses (config).** He ruled this a pod question (M49). Only his hand lowers a kill level.

**D12. Scope keys.** Options: instrument and deployment only (BUILT, `runtime.py:1675-1678`); add class, region, currency, underlying, session, family, pod, tag, driver (`X3-H35`, `H1` idea 22, `E2` row 11). **Pick the full set, core.** "It can isolate crypto" (M10) cannot be said today. Tags are many-to-many (`H5` idea 18).

### 2.4 Accelerators

**D13. House money and reverse house money.** Options: (a) two rules on two ledgers (old pick, REVIEW M8 found the contradiction); (b) one rule, one cushion ledger of profit since an anchor; a fixed anchor presses and brakes, a running-peak anchor only brakes (`H2 I4`, R9 0.4, Grossman-Zhou) ; (c) drop house money. **Pick (b): the cushion ledger with anchor type, clock and scope as rows is core; the rule shape (straight, April's curve, sigmoid) is a block; the press gate is a block (`E2` Pod 4).** He asked not to lose house money (M5) and reverse house money is his idea (M39). Evidence stated plainly: REAL theory; MODEL shows no gain on independent trades and gains only under regimes (R9); `A5-118` records a deep-drawdown tail. **Shipped default: the scalper template switches the rule on with a day anchor (so it brakes on the way down and presses with winnings only); the intraday template ships it off.** Values open. His old Q4 ("a rule I approve") is a press-gate block, not a question.

**D14. Other accelerators.** Earned tiers (`H2 I22`, REAL prop rules), press with winnings only (`I18`), persistence press after a block test (`I23`), pyramiding with falling risk (`I32`), calm-volatility scaling with a guard (`I33`), probe for capacity (`I34`), overdose-controlled steps (`I35`), bounded exploration (`I36`), agents breeding profiles in the Lab (`I37`), growth buys breadth (`I38`), QoS lending (`I39`), thermostat (`I40`), goal taper (`I25`), restart after near-breach (`I26`). **Pick: all content, on two seats that are core: the named size-modifier socket with range and reason on the receipt (`H1` idea 4), and the realised-profit fact.** None is a default. He called them "tools or timber" (M50). The raise permission gate (any brake blocks every raise, `X1-H13`) is a default rule on the group row, not a law: a reckless pod may remove it.

### 2.5 Numbers and self-configuration

**D15. What every number carries.** Options: (a) a fixed value (BUILT for risk numbers); (b) a number spec: derivation (a rule block or a fact), range, authority, owner, reason on the resolved value, cautious direction for missing data, a guard that reverts and freezes after trips, a never-self-tune marker, `applies_to_open_positions`, and a per-change record of before and after (`H3 T2`, `T24-T29`, `X1-H02-H08`, `H2 I12`, `E3-6`) . **Pick (b), core, on every number including sizer, stop, target, per-bar exit and halt numbers.** Today motion reaches logic numbers only (`SWAP 2.5`, `_bound_on`). This is "what if I want to change the way it is derived?" made structural.

**D16. How a number moves.** Options on disk, with `E5` section 2's mechanism tests behind them:
| Mechanism | Evidence | Buys |
|---|---|---|
| Learner publishes a target with bounds; a separate applier moves it in the number's mode (VPA model, `X1-H02/H03`, candidate 1) | REAL in Kubernetes; in `E5`'s test (M3) it added machine and little gain | Numbers move between anchors with bands he can see |
| Refresh at anchors only (candidates 2 and 3) | PROPOSAL | Nothing moves unexplained; a day's lag |
| Find, track, correct: replay finds a start, facts track the market live, the built motion engine corrects from own trades, bounded and switchable per type (`E5` 2.4) | MODEL (`E5` tables: S+M1 held across every world tried); BUILT engine for logic numbers | No new applier part; each job uses data suited to it |
| Bandit over approved versions; genome variants (`X1-H48`, `X2-H53/H54`) | papers, no trading test | Lab-side search |
**Pick: core carries the fields and seats that let all four exist: `authority` with a real `off` and `motion_inside_range`, room for non-flat anchors and calendar cadence, a `scaled` mode (fact times multiple), a bounded window on the engine's memory (`E5` 2.1 finding 1: `SlowState.read` is unbounded today), calibrated numbers without a logic stamp, `Origin` "found by replay", report with and without motion (`MotionSwitch` exists). Shipped default: find, track, correct, with per-type presets (correct on for filters in scalper and intraday, off for size press, off for swing).** The learner-and-applier object is a block someone adds (content) and is one side of fork F2. The hill climb is a Lab job on long history, counted, ending in a new version, never a live climb on recent trades (`E5` 2.5; MODEL: live climbs stalled or wandered). His "have an agent go at it" (M49) lands there.

**D17. Authority.** Inside a declared range a number moves by its own rule, no click. Outside it is a new version, a counted try, then his promote click. Agents write in the Lab and on cards, never on a running unit; their output reaches a unit only as a fact it chose to read (`E5` 2.4, `H4 I-52`). The never-self-tune list is per template and user-editable (`H3 T29`); the kill switch is the one fixed entry. **Core as fields; the lists are config.**

### 2.6 Costs and facts

**D18. Costs as observed facts.** Options: (a) no cost reaches the unit (BUILT; `reads` refused, no commission key, `MAP` section 4); (b) cost cells per instrument, broker, hour, session and world, written from fills, with an `uncalibrated` label and a stressed, class-pooled fallback that decays to measured; the sizer reads the cell; two residuals kept apart, signal before costs and cost against model (`H2 I8`, `I63`, `H5` idea 26, `X6-30`). **Pick (b), core.** This is his "think of QMX more of as a data analyst... I'm trying to observe them, see what I can do" (M51). Facts move live, numbers at anchors (`H3 T25`) is the default timing rule, kept as a mode not a law.

**D19. Where cost enters.** Three points exist: the size denominator, a Kelly ceiling in R, an admission gate at k times stressed cost (`H2 I62`). **Pick: denominator in the shipped default sizer (core input); the ceiling and the gate are blocks (content); k is numbers talk.** REVIEW M4's table stands as the honest warning: at a 5-pip stop the gate refuses his pictured scalper, at 10 pips it passes.

**D20. Account and venue facts.** Live balance refresh, open risk at stops, margin headroom, liquidation price check at entry, leverage change stand-down, conversion market and USD seam, per-world calibration, fill record with decision quote, arrival quote, fill, partial, reject, requote and markout at several horizons (`SWAP 14-17`, `H5` ideas 32-33, 36, CHECK B5) . **Core inputs and records.** Today equity is the balance read once at sign-in (`SWAP 17`).

### 2.7 Instruments

**D21. One record per unit, instrument and broker; class differences are fields, not branches.** Fields: money per point, lot step and bounds, class, bucket and underlying, book-or-quote flag, tick tier, hourly cost cells, conversion, session clock, day boundary, calendars (session, event, roll, funding), roll rules, commission, margin, leverage, detector calibration (`H3 T15`, `H1` idea 50, `H5` idea 36, `E1` row 17) . **Core.** Futures mini and micro are two rows (his M50). A test that fails on branching by class in the money path (`E5` 4.2). Which classes are tradable at a budget is a computed, shown verdict (`H1` idea 51); the refusal is a block. Classes themselves (energy, stocks, crypto overlays, tick-size tiers) are content rows.

### 2.8 The MIS and routing

**D22. The shape of the MIS** (`E1` section 3, four designs; `H1` section 3's poles).
| Design | Evidence | Buys |
|---|---|---|
| MIS-1 deeper board: one MIS, tiers, packs filled, units read with fallback | designed (unit plan), partly BUILT | One vocabulary; most already designed |
| MIS-2 open bus: any app, pod or agent publishes a reading in the same record under its own name; units pin publisher, reading, version | PROPOSAL; the record and journal are BUILT | His departments and "mini apps feed each other" (M50); a poor default is replaced, not rebuilt |
| MIS-3 finder: the output is per unit, "where is your claim true now", as an `active-markets` reading | PROPOSAL; his M5 router | His idea directly; a morning list, never per trade (readings take hours to show) |
| MIS-4 two products: an overnight curve factory (usual level per minute of week, as a fingerprinted artifact) and a node stream that divides live by curve | PROPOSAL resting on "now versus usual" | One baseline shared by SQS, MIS and QMB; a dead MIS is safe by structure |
| No central MIS; slow-only; cross-sectional only; per-reading placement rule (`H1` poles) | PROPOSAL | Kept as poles for the architects |
**Pick: MIS-2 and MIS-4 settle the core seats (record `source` open to `app:<id>` and `agent:<id>`, publisher on a read, `valid_until`, inputs named on each record, one curve artifact per world with an age word). MIS-3 is the first app on top (content). MIS-1's pack list is content filled over time. The units-stand-alone rule holds: no unit needs the MIS.** This is fork F3's field (section 6) for where the sensor runs.

**D23. How a unit reads and widens markets.** Options: fixed list; board narrows (BUILT, unwired); active list as a reading over allowed, home as fallback; a card adds to allowed; free (`E1` section 5 ladder). **Pick: the ladder, each rung a setting (config). Core: `reads` compiled with fallback and stale limit; three market lists on the unit, allowed, home, active; the board or list fallback is home markets, not every listed market.** The hazard `E1` found is real and must be fixed before anyone widens a list: today a stale board trades every listed market (`runtime.py:367-369`). Records split per unit, market, session and slice (core record), or the router can never be scored.

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
**Pick: all four as blocks. Core: one node-side sensor for spread, tick rate and quote gaps with source `node`; an entry-gate slot per unit with a verb list (block, shrink, wait, warn, shadow, none) receiving market, side, quote, stop, the unit's cost allowance and cost cells; exits bypass every gate by contract test. Shipped default: SQS-2 as the gate, SQS-1 as the floor for broken markets; SQS-3 in shadow; SQS-4 off, on the modifier socket.** Values (allowances, floor lines, the eight old settings) are numbers talk. `sqs_baseline_producer.py` and the rule text must move before repair's C-20 deletes them (`SWAP 4.3`, old DP25).

### 2.10 Isolation and news

**D27. One mechanism for isolation, news and caution windows: stickers and tolerations** (`E1` section 4). A sticker is a record in the stand-down table: scope, kind (`news`, `open`, `fix`, `isolation`, `unknown`, or any publisher's name), strength (prefer not, no new entries, flatten), expiry and resume rule, why and who. Each unit, pod or template lists the sticker kinds it ignores. **Core record and field.** It dissolves four collisions at once: ORB allowed where a scalper is blocked; news units against a global news window; a fix-reversal unit against a caution window; "is this a pod question?" (yes, M49). The kill switch is not a sticker and cannot be tolerated. An agent-placed sticker can only reduce risk and must expire. A sticker table the node cannot read reads as `unknown` for that scope, so "unknown is not calm" (`X3-H36`) holds without touching the board's fail-open.

**D28. Who may place an isolation.** A rule on two different tells (`X3-H28`, `H1` idea 23; daily-data author backtests, no intraday precision), an agent card de-risk-only with expiry (`X3-H34`, `X7-H21`), a person typing. **All config; the rule is a pod block; shipped default: no isolation rule binds; the SQS floor's block counts across a class are published as a reading (content).** Every isolation writes whether a loss followed, with blocked trades as would-have rows (core record). "No public source on a fund switching off one class by rule" (R2): say so on the block.

**D29. News.** Calendar events carry driver tags (both FX legs, home exchange, region, commodity) and become stickers; strength from the calendar's tier until measured impact replaces it; a stale calendar fails closed; blocked minutes reported as a cost; re-entry on spreads and depth, not the clock; a velocity tell backstops a missed release; news units tolerate the sticker and read an event clock (`X0-39`, `H1` ideas 30-35, `E1` section 4). **Core: tags on the instrument record, the sticker, event time as a clock, a per-unit toleration. Content: widths, measured impact, the agent event mapper. Shipped default: both FX legs tagged, scalper template tolerates none.** The kill switch keeps the hard kill (his C28). This session claims `qmn/data/news_calendar.py`, `qmn/protection/windows.py`, `dispatch.py` and `qmf-risk/control_window` before deletion (old DP24, kept).

**D30. Sessions, opens and sniping windows.** His "is ORB the sniping period?" (M8): no, different kinds of thing. ORB is a logic; an open is a window; a sniping window is a Library artifact saying one unit family on one instrument does better in one slice (`E1` section 4). **Core: `sessions` compiled, a window card kind (slice, family, how found, try count, expiry, status `hand-written | shadow | proven`), a window object any unit can declare and pass or refuse, the per-session record split. Content: deterministic finding from the curves, agent nomination with counted tries, hand-written windows.** A hand-written card trades without anyone proving it first: that is the canvas, and the record then speaks. Research says windows lower cost or raise activity and do not hand out edge (R2); his gold belief is parked for the numbers talk, not settled here. Caution widths at opens are measurements, no number set.

### 2.11 Capital sharing

**D31. How units share capital.** Options: (a) each of N units gets 1/√(N(1+(N−1)ρ)) of its solo size (old DP9; MODEL; his M49 complaint); (b) his literal split: total day capital over N (M10; his words); (c) own full size under a parent limit on losing together (`X2-H29`, `H3 T5`; REAL bank practice); (d) a few best units until capital allows volume (A1-083, M50's best basket; PROPOSAL); (e) guaranteed share plus burst from idle slack, QoS lending (`X2-H30`; REAL in Kubernetes); (f) poker-band pots (`X2-H37`; practitioner lore); (g) stage switcher that swaps the sizing rows at an anchor (`E2` Pod 9; his "at 5,000 the math changes"). **Pick: the split rule is a named allocation mode on the group or pod (core row); every mode is a block (content). Shipped default: (c), own size under a parent limit.** His two statements, "more units less each" is wrong (M49) and "total daily capital split across units" (M10), are both his; a row dissolves the clash and he never has to choose in the abstract. Budget share travels with the deployment (core), so paper sizes from its share of live equity, never the demo balance (`X2-H50`). A pod may change a unit's sizing rows at an anchor without a new unit identity (core seat; `H2 I27`).

### 2.12 Group and pod level

**D32. What a pod is, in words.** `E2` (a): pod = the versioned stack (his screen word); pod deployment = a pod version plus members, share, place and side; desk = his department sense, a mini app or several with agents; Book and BMS retire as screen words, "Classic Book" survives as a template name. **Default vocabulary; his words, so `QUESTIONS.md` Q3 confirms, run continues.**

**D33. How a unit and a pod relate.** `E2` (b)'s five ways. This is fork F1 (section 6), not decided here. What is decided, because every way needs it (core): an optional pod reference on the deployment where an empty pod means the unit's own blocks; the deployment key includes pod and side (live or paper); two fingerprints, logic and pod, so a pod edit never re-proves 200 units (`E2` row 3, the largest rework risk named); placement on each block row; slot composition rules as data (sizer picks one, throttles multiply or a declared combiner, caps lowest, guards worst state, inputs union); a group stage hook called on the node and in QMB, passing intent and open risk across members (`SWAP 6`); one ledger fold keyed by scope including pod; would-have rows under any pod (the round table's finding: a guard changes which trades happen, so the logic record depends on it); `required` and "kill line set" as preset warnings, never compile refusals (`E2` row 14). Exits stay on the unit; a unit template carries exits, a pod reference and presets together (`E2` (c)); whether a pod may swap exit rows at an anchor stays open (section 5).

**D34. Pod configurations.** `E2` (d)'s twenty (Relentless, Session relay, Classic Book, Cushion pair, Old pair, Scalper first, Human mimic, Best basket, Stage switcher, Prop rider, Earned tiers, Multi-manager, Capped total, Run together, Futures desk, Model hybrid, Watched by agents, Volatility core, Canary, Full press) plus R9's eight brake-accelerator pairs. **All content: the pod gallery.** None has run. The `n:` blocks they name are the first content list for QML growth (D44). His M49 ask for "pod ideas or configurations" is answered by this gallery and the walkthrough should show it.

**D35. Book and BMS.** Options: keep as documents (A4-092); tags plus one portfolio config (`X1-H40`); a `group` document with `display_name` and `parent` reserved (candidate 2). **Pick: the group document with `parent` and an allocation mode, and `tag:` as a scope key (core); the structure itself he said "decide later" (M49), so no question now.** "Classic Book" is a pod template.

### 2.13 Mini apps and shipping

**D36. How a pod or template ships.** `E2` (e): four levels, a document, a document plus blocks, a mini app carrying pods, a desk. A saved thing stores only what differs from its preset plus each block's pinned version (`R1` 4.2, `H3 T9`). **Core runtime seats, all missing today: a core `library-items` lander that lands static content at publish (an app names one lander, only `qmb-run` registered; `E2` rows 1-3); a declared `library/` folder in the pack; real `pod`, `pod-block` and un-retired `template` kinds (shells today, `SWAP 31`); a row that saves a block (`SWAP 2.2`); one block catalogue, with form and graph pod-blocks compiling to a QML block (`H3 T39`); pin, diff and lineage on each unit and pod; a forwarding map for block versions. Content: `requires` between apps, subscriptions, the file extension (`.unit`, `.qmxpod`, his "I don't care"), the `build-pod` skill.** The money rule holds: nothing an app lands reaches a node except what the host compiles from landed, checked items with his promote click.

**D37. Mini apps feeding each other, and reaching a unit.** Roads A (artifact feed) and B (Library landing as event) are BUILT; C (proposal to a pod) is partly there; D (a published reading reaching a unit's `reads` with age and fallback) is not built (`E2` (e)). **Road D is core (it is D23's `reads` plus D22's publisher). A stopped desk stops nothing: units keep trading on home markets.** His futures week (`E2` walk) runs on these roads; the desk itself is other session (agentic upgrade, methodology).

### 2.14 The Lab

**D38. One evaluator for Lab and live.** The conflict: Lab AD-10 makes `qmx_lab.pods.simulator` the one evaluator; the fold says the Lab runs the guard package on a replay port; AD-11 compiles pods to Book and BMS with `unsupported_blocks` (`H3 T38`, `E2` (f)). **Pick, core: one small core in a library both sides import (three functions: decide, on_fill, at_anchor), state passed in and returned so "pure" and `block_state` are both true, four drivers (node live, QMB, paper, Lab replay), a conformance tape through every driver in CI, `unsupported_blocks` replaced by the needs list, the size trail equal to the decision row, compile target = the pod document plus `qmx.unit/1`.** What may differ: fills, costs, latency. Never the arithmetic. Resize replay is for exploring, a QMB rerun for evidence (methodology hand-off). Lab-born units need no QMB card (`H3 T7`). Lab pods on a model's surface, the Pods bench and the copilot's Lab tools: other session (UI, agentic upgrade).

**D39. Lab tools worth a seat.** Resize a recorded trade list under another sizing rule (`H2 I1`, QuantAnalyzer, REAL as a product): the trade-row fields are core, the tool is content. The chassis stress battery as a CI test, adding walks for pod, mini app and Lab-born unit (`H3 T19`): content, cheap, direct test of "handle any amount of stress". The family ledger counts every try, identity vocabulary shared between Lab and unit (`H3 T41`): core vocabulary.

### 2.15 Identity and versions

**D40.** Spec and status with separate writers and a generation stamp (`X1-H01`; REAL in Kubernetes); identity table wired, with a forwarding map so `fixed-fraction-at-stop@1` to a real sizer is a declared migration and a unit keeps its record (`H3 T49`, `SWAP E16`); two records, logic in R across versions and money per version (`X1-H44`); pins plus diffs plus lineage (candidate id, hash, parent, family, data and cost versions, hypothesis as a scoreable claim: metric, benchmark, window, `E3-1`); plan before change, refused if stale, with his click bound to the exact hash, level, markets and date (`X1-H46`, Terraform); a rollout field (shadow, canary, full; analysis rules are methodology's); upgrade offers never silent; a self-test card per version; a rip-out check that placeholders and dead versions cannot linger (Knight Capital, `H3 T54`); migration of stored shapes and config-effective timing (BUILT upgrader chain). **All core, except offers and canary analysis (content, other session).**

**D41. The one compiler bump.** `E5` 4.5 and `SWAP 2.3`: a bump moves every unit's compiled fingerprint and the node refuses a fingerprint its G record did not test, so at 200 units every bump means 200 new test records. No unit is deployed today. **Pick: widen every socket in one bump before any unit deploys (sequencing rule, core); a re-test workflow per bump (content).** Block-entry fields that linking needs (D44) go where they do not move compiled fingerprints if possible; whether `block_fingerprint` covers the whole entry is UNKNOWN (`E4` 8b).

### 2.16 Records and observability

**D42. The rows.** Decision row that replays: inputs with timestamps, every resolved number with its reason, each step from wanted to approved to filled, the binding clamp named and counted, version and compiled fingerprint, readings seen with source, age and version, gate verdicts, `propensity` when a paper twin took a logged random share of refused entries (`E4 L04`), newly-active market mark, numbers in force, placeholders used. Trade row v2: net and gross R, costs by kind, exit mechanism and reason code, MAE and MFE with the bar path, session, slice, cost cell, world, stage, contract month, markout, `counts_toward_proof`, audit flag. `would_have` and `risk_event` rows written, not only declared (`SWAP 25, 29`). Fill record (D20). Calibration rows (BUILT). Expectation at birth with the version: trade rate, spread of R, streaks, from replay (`E5` 1.8). Root-cause key and event id on stand-down, risk event and order-failure rows. Run stamp: real-tick share, quote source, gate settings, costs (`H5` idea 37). Link record and arm fields on run records (`E4 L02`). Three positions side by side: intended, risk-approved, executed. One trace id from reading to fill. Requested, enforced, observed (`X6-09`). `RiskState` as one fold over journals keyed by scope including pod and tag, with a state word, a stamp, a reason and UNKNOWN when stale (`X6-01`, `X6-11`). A fleet read: one query over all units. Closed reason codes as appendable data rows, with new code families for user-added blocks. `explain_size(row)` as one pure function used by developer, copilot, UI and triage alike. **All core.** Meters, scorecards, the six words on screen, alert tiers, the morning card, the dark cockpit: content or UI session, with an incident key and alert fields (action, deadline, actionable) as core fields (`H5` idea 17).

### 2.17 Agents' doors

**D43.** Three surfaces: read rows carry state and receipts; proposals are typed, expiring, scoped, with evidence, direction on every operation; runs in a sandbox are unlimited because they cannot touch money (`X7-H01`, `H4 I-50`). Evidence intake declared per unit: kinds accepted, largest cut, time to live, style scope, fail mode (`H4 I-52`). A protected field list no agent may write (`H5` idea 38). The promotion and live-money door runs through a channel the copilot and agents cannot read or reach, including his email and any code sent there, and the click binds to the exact effect (`E3-26`: ten frontier models raised their own spending caps by harvesting one-time codes; REAL tests outside QMX). A block-save door with a contract test (`H3 T57`). Agents never grade themselves (`H5` idea 4). **All core as doors and fields. The jobs (triage, coroner, drift explainer, sitting-duck advocate, prospector, isolation cards, per-class agents, shepherd, self-improvement) are the agentic upgrade's, listed in section 8.** Open: whether an agent's cut that applies itself inside a pod's declared bounds crosses "agents never touch money" (`E2` Pod 17, `H2 I95`). Default while open: a cut-only fact a unit's own rule reads, inside bounds the pod declared, with expiry; raises, placement into new markets and anything that lowers a kill level are cards. It is in `QUESTIONS.md` as Q4 because it is the meaning of his fixed line.

### 2.18 Fleet watch

**D44.** `E5` section 1, with its census: the shipped decay job would send about 91 cards a night for 200 healthy units (MODEL on made-up units, rule copied from `read.py`). Options: per-unit thresholds (BUILT shape); scripts keep one ranked row per unit, an agent reads the top K plus each new incident, two lists (rank, which can never false-alarm, and a strict bar under one fleet false-alarm budget), family pooling, one incident one card, four tiers to him (`E5` 1.2-1.5; `H4 I-33/I-34`, `H5` ideas 2-3, `E3-25`). **Pick the layered design as the shipped watch (content, as workflow templates first with a thin mini app face, moving whole once apps can read journals and land cards, `E5` 1.7). Core: everything the unit must publish (D42) plus a free type tag and family id on every row, and a group-level place for an alarm budget and a share cap.** His "as a mini app also" is met the honest way: the doors an app needs are flaws for the agentic upgrade (section 8). `E5`'s correction to `H4 I-34` stands: at 200 units a strict bar slows demotion by 30 to 135 % for active styles, not tenfold; slow units cannot be judged alone and the screen must say "too thin to judge".

### 2.19 QML growth

**D45. Roles and fields.** Roles that must run for any of this to bind: `sizing_modifier` (22 blocks claim it and cannot act, `H3`), `veto`, `cooldown`, `invalidation` (extended to a condition watched after entry, `H5` idea 4), `re_entry`, `arming`, `timeout`, `regime_detector` (`SWAP E2`). New roles the baseline's own parts use: `derivation`, `combiner`, `restore`, `guard_statistic`; `proposal_validator` and `applier_mode` when a block needs them (`X1-H67`, `H3 T12`). Block-entry fields for safe linking: `output_meaning` (a score piped into a sizer is nonsense), `assumes`, `null` (scheme, block length, draws), `evidence`, `retest_by`, `knows_at`, `decides` (`E4` 8b). A face check on the sizer slot (a trigger compiles there today, `SWAP E8`) and limits in one place. Library-only blocks enrolled in the contract tests (`SWAP E11`). **All core.** Three faces per block, the dictionary expansion (M38), recipes and the seven joints as copilot vocabulary (`E4` section 3), the `build-unit` skill rules in `E4` 8d: content, early. QML stays the SDK: agents' ideas reach QMX as units in QML; Python only for what QML can't express (M50, `H4 I-79`).

### 2.20 The Python path

**D46.** Three doors on disk (`H3 T20`): a block in the Library, checked deny-by-default and pinned by fingerprint (BUILT loader, no save row, node path UNKNOWN); a trust ladder with a minimum per slot and his signature on money-path pins (PROPOSAL); a quarantined `plain_python` hatch (refused today). **Core: the save-and-contract-test path and the loader's signature check, and a traced end-to-end run of a Library block through `unit_new`, QMB and a node deploy (UNKNOWN today, `SWAP` section 3). Content: the trust ladder's levels, the hatch, expressions compiled to blocks (`X1-H09`).** Only signed `qml` and `human` blocks size live is a template default, not a law.

### 2.21 Order path and netting

**D47.** Intent kept separate from placement so netting can come later (`H5` idea 31; `X1-H74`, `X2-H43`): core. Order type on the intent (market only today, `SWAP E14`): core field, limit and stop entries content. An entry-timing offset so 200 bar-close units do not queue at the same crowded second (`H5` idea 34): core field. Target rests at the venue or the node closes: a sub-choice of fork F5 waiting on R24. Partial close on the node (refused, `SWAP 10`): widen, core. Two units on one netting symbol (refused at host time, `SWAP 21`): shared protection and attribution become a setting, core widening. The signed stop distance (`SWAP 9`): repair's, blocking step 3.

### 2.22 Multi-position

**D48.** `position_limit` of one per market is a compiler law today (`SWAP E4`). His A8: a unit may hold more than one position where its type allows (M7), and not every scalper should (M8). **Core: lift the refusal; the limit is a template field; "flat" is defined per market and per position for anchors (`E5` 2.4); bet key, driver tag and family tag on every intent.** Pyramiding with falling risk, baskets and the target-position answer type (`E4 L07`: position as a curve of price and time, needing a per-bar sizer update and partial closes) are content on this seat; multi-leg orders have no shape and are flagged, not required (`H1` section 4).

### 2.23 The newcomer path

**D49.** `E5` section 3's walk, 17 gaps, six of them this session's (G8 to G11, G13, G16). **Core for this session: working templates per type that compile and pass G on synthetic bars, each saying "this is a shape, not an edge"; a default size and brakes that run with nothing set, labelled, with reasons; a first day that needs no broker for history and replay (check G8); the walk as a rehearsal test extended from `tools/first_real_start.py --rehearsal` to template, check, backtest, promote to paper, one trade on the journal, one row in the fleet fold.** "Tomorrow" is honest as: day one on history and replay; day two on paper with a broker, because cTrader's approval takes about a day (`E5` G6). Installer, launcher, desktop app, first-run ticks, model sign-in, persona wording for a stranger: release, UI and agentic upgrade (section 8).

### 2.24 The developer path

**D50.** `E5` section 4 and `H3 T71`. **Core: a module map with one statement per risk module saying which of the two risk worlds (`qmf-risk` old modules, QML blocks new) it belongs to and a plan to subtract what the swap retires; the contract tests in order (same decision in both hosts by socket; exits never blocked as a property; every refused field running or labelled, extended to `authority` and `reads`; every number has a reason and range at check; motion range, step, flat and bounded state with a shuffled-outcome control; every template reaches paper on rehearsal; no agent path to money by tool table; `RiskState` from one fold in every reader); the decision row that replays and `explain_size`; one trace id; a face check on sizers; a generated `EXTENDING.md` with a staleness test; the one bump (D41); the deletion test on the small core (`E2` (b)).** Observability stack choice (Prometheus and Grafana against OpenObserve) is his later, with a note that risk rows are evidence and may not be dropped; retention at scalper rates is unmeasured.

---

## 3. THE CORE LIST

The test: what must the core carry so the rest never forces rework? Sockets, inputs, records, hooks, invariants. Nothing here is a value or a policy. If a row read like a preset it was moved to section 4 or to content. Size is stated honestly: this is a large list, because the swap chart found that the "just swap it out" promise holds for one narrow shape only (`SWAP`, short answer) and almost every idea in H1 to E5 waits on the same few refusals.

**Today's state words.** BUILT: runs at the tip. NARROW: runs for one shape, refuses the rest. STUB: declared, no caller or no writer. REFUSED: the compiler names it as not built. MISSING: nothing on disk. The placeholder column names `PH n` rows and `SWAP En` rows that the item swaps or widens.

### 3.1 Sockets

| # | Socket | What breaks if missing | Today | Swaps or widens | Arrives later on it, no core change |
|---|---|---|---|---|---|
| S1 | Sizing base as a derivation producing dollars at risk; one shared converter to the instrument's quantity; face check on the slot; limits in one place | Every new base is a socket change; lots leak into design; USDJPY fault returns; 5,000 lots passes | NARROW (`SWAP 1`, `E8`, `E9`) | PH 1, PH 12, PH 30 | Every sizing base in D3; the modifier chain |
| S2 | Named size-modifier chain on the sizer, each with a range and its reason on the receipt; the `sizing_modifier` role runs | Hidden multipliers, or none; the old handbrake unseen | REFUSED (`SWAP E2`) | PH 1 | Cushion pair, tiers, AIMD, cost dial, window lift, calm scaling, context readings |
| S3 | Exit stack: every per-bar exit runs, fed `PositionFacts` and evidence, side-correct; three verbs with reason codes; declared rank | Dictionary's closing mechanisms stay dead; trails, partials, breakeven, FI, thesis exits locked out | NARROW (`SWAP 2-4`, `E10`, `E15`); six shipped exits refuse | PH 2, 3, 4, 9, 10 | Every family in D7; step 3 when the signed stop lands |
| S4 | Halts bind at position, unit, account and group scope; verbs `none`, `no_new_entries`, `reduce(factor)`, `flatten`; five states; a host computes the statistics halts read | Five shipped halts useless; only stops exist | REFUSED, STUB (`SWAP 5`, `23`) | PH 5, 20, 23, 24 | Every brake in D10 |
| S5 | Registry row per control (D8) with placement (unit, group, off-path), tail or timing class, shadow switch, attack and release, counting rule, fail mode, money series, restore, `on_fire` | Each brake is custom code; "5 % drawdown" means four things; a pod cannot choose an action; a later move rewrites rows | MISSING | PH 5, 18, 28 | New brakes as rows; pods choosing actions |
| S6 | Entry-gate slot per unit with a verb list, receiving market, side, quote, stop, cost allowance and cost cells; exits bypass it by contract test | SQS gets hard-wired, the shape he objected to; a per-trade cost check cannot exist | MISSING (`guard` has no spread check, `SWAP E7`) | PH 18 (entries), SQS seat | SQS-1 to 4, five execution gates, feed-gap alarm |
| S7 | Group stage hook called on the node and in QMB, passing the intent, open risk across members, bet keys and group facts; answers pass, shrink, refuse | Pods stay paper; cross-unit rules impossible in backtest | STUB on node, MISSING in QMB (`SWAP 6`) | PH 6, 21, 27 | Parent limits, chorus, portfolio stops, netting |
| S8 | `reads` compiled with publisher, fallback, stale limit and `valid_until`; record `source` open to `app:` and `agent:`; inputs named on each record | No reading reaches a unit except by embedding a block; departments cannot publish | REFUSED (`compiler.py:900`), enum of two | SWAP E1 | The MIS board, the finder, every mini app reading, agent evidence, physics rows |
| S9 | `sessions` and window objects compiled; a window-card kind; per-unit pass or refuse | Windows, opens and sniping slices cannot bind; intraday cannot go flat before close | REFUSED (`compiler.py:904`) | SWAP E6 | Caution windows, ORB per open, hand-written windows |
| S10 | Sticker record (scope, kind, strength, expiry, resume rule, why, who) in the stand-down table; `unknown` as a state; tolerations per unit, pod-overridable | All or nothing; rigid news rule; a stale feed reads calm | Stand-down table with instrument scopes only | PH 15, 18 | Isolation rules, news, opens, agent de-risk cards |
| S11 | Scope keys: instrument, deployment, unit, family, class, region, currency, underlying, session, pod, tag, driver | "Isolate crypto" cannot be said; one incident is twenty cards | Two keys (`runtime.py:1675-1678`) | PH 18, 20 | Every scoped rule |
| S12 | Roles that run: `veto`, `cooldown`, `invalidation` (watched after entry), `re_entry`, `arming`, `timeout`, `regime_detector`; new roles `derivation`, `combiner`, `restore`, `guard_statistic` | Gate, Scale and Switch joints impossible; thesis exits unjudgeable | REFUSED (`SWAP E2`) | PH 7 | Linking recipes, physics gates, restore methods |
| S13 | Number spec on every number, including risk numbers: derivation or fact, range, authority (`off`, `motion_inside_range`, anchors), owner, reason, cautious direction, guard and freeze, never-self-tune marker, `applies_to_open_positions`; `scaled` mode; motion reaching sizer, stop, target, per-bar and halt numbers; bounded engine memory; calibrated without a logic stamp; `Origin` "found by replay" | Self-configuration has nowhere to live; a moved number might touch open trades; the engine's memory grows without bound | NARROW (logic numbers only, `SWAP 7, 8`, 2.5; `engine.py:124` unbounded) | PH 7, 8, 22 | Learner and applier, bandits, pooled priors, hill-climb jobs |
| S14 | Slot composition rules as data; placement field per block row; pod reference on the deployment (empty pod = the unit's own blocks); deployment key with pod and side | Each mix is code; "no pod" is a special case; a pod cannot have a paper side | `CombinerKind` for logic only; `pod` kind a shell (`SWAP 31`) | PH 31 | All twenty pods; the empty pod |
| S15 | One evaluator core (decide, on_fill, at_anchor) in a library node, QMB, paper and Lab import; state in and out; four drivers; conformance tape; needs list in place of `unsupported_blocks` | Lab size differs from live size; two block worlds | Lab simulator designed, unbuilt; guard package missing | PH 31 | Every pod screen, fan, stress board, head to head |
| S16 | Core `library-items` lander; declared `library/` folder in a pack; real `pod`, `pod-block`, `template` kinds; one block catalogue; a row that saves a block with a contract test; Library blocks enrolled in contract tests | "Ship pods" stays a sentence; agents draft and he hand-saves; a landed block may run in QMB and not live | MISSING (`E2` rows 1-6; `SWAP 2.2`, `E11`) | none | Pod gallery, desks, agent-made blocks, recipes |
| S17 | `position_limit` lifted; limit as a template field; "flat" per market and position | Pyramiding, baskets, adds, campaign counting blocked | REFUSED (`SWAP E4`) | none | Pyramiding, target-position curves, pairs |
| S18 | Order type on the intent; intent separate from placement; entry-timing offset; partial close on the node; shared protection on a netting account as a setting | Market only; 200 units queue at the bell; netting is a rework through the money path | Market only, partial close refused, netting refused (`SWAP E14`, `10`, `21`) | PH 10, 21 | Limit and stop entries, netting, jitter blocks |
| S19 | Risk check layer beside A to F, open to new layers; a commuting check on links as a warning | Preflight stops at F; unit-scale bugs pass | Checker stops at F (`SKILL.md:30`) | none | Pre-mortem cards, ruin audit, link scanner |

### 3.2 Inputs

| # | Input | What breaks if missing | Today | Swaps or widens |
|---|---|---|---|---|
| I1 | Full fact surface for derivations (D2), each input timestamped with a declared fail mode (open, closed, neutral) | Almost no hybrid can run; three meanings of "missing" | REFUSED (`SWAP 1`), partial fail modes | PH 1, 17 |
| I2 | Cost cells per instrument, broker, hour, session, world, written from fills, with `uncalibrated` label and class-pooled stressed fallback; commission key; two residuals (signal before costs, cost against model) | Costs never reach the unit; his data-analyst lens has nothing to read; signal decay and execution decay look the same | MISSING (`MAP` section 4, `X1-H63`) | PH 1, 16 |
| I3 | Live account surface: balance refresh, open risk at stops, margin headroom, liquidation check at entry, leverage-change stand-down producer, conversion market and USD seam, budget share per deployment, `basis` declared per row (committed cushion, marked equity, realised profit, worst case) | Sizer blind; paper sizes from the demo balance; margin close-out passes every brake | Balance once at sign-in; `Account` is equity alone (`SWAP 14, 15, 17`) | PH 14, 15, 17, 22 |
| I4 | Instrument record fields: money per point, lot step and bounds, class, bucket, underlying, book-or-quote flag, tick tier, hourly cost cells, conversion, session clock, day boundary, calendars (session, event with driver tags, roll, funding), roll rules, commission, margin, leverage, detector calibration | One template cannot size every class; order-flow logic on a CFD; CPI stickers "USD" only; gold micro charged Nasdaq's point cost | Partly (margin, swap, conversion exist; no commission, no base-currency key, no tags) | PH 13, 14, 16 |
| I5 | Three market lists on the unit: allowed, home, active; board and list fallback is home | Widening is a new version each time; a dead MIS turns on a wide unit's whole universe | One list; fails open to all (`runtime.py:367-369`) | none |
| I6 | One curve artifact (usual level per minute of week) per world, with age word and flagged borrowed cold start, read by SQS, node, MIS and QMB | Three spread measures drift; first live entry waits hours for a baseline | MISSING; `spread_state` uses fixed cuts | SQS seat |
| I7 | Bars with full range, volume or tick count, time of day; tick, volume and event time as clocks; `knows_at` (event time against available time) on every reading and agent record | RVOL and the fastest volatility readings stay out; news units impossible; look-ahead in agent-built links | Closes only; `QuoteBar` has no volume; clocks refused (`MAP` section 4) | none; needs his call (Q2) |
| I8 | Evidence intake declared per unit: kinds accepted, largest cut, time to live, style scope, fail mode; `knows_at`, source and feed ids, confidence, direction of effect on each record | Agents cannot help during trading, or they get a command path | `Read` has fallback and staleness only; `accepts_evidence` empty | none |
| I9 | Identity on every row: unit, version, compiled fingerprint, logic fingerprint and pod fingerprint apart, family id, free type tag, market, world, stage, provenance (source: paper, video, agent, Lab, mini app; run; profile; model and cutoff) | Pooling, ranking and per-type views impossible; a pod edit re-proves 200 units; four kinds of unit cannot be compared | Most exist; type tag, pod fingerprint, provenance missing | PH 22 |
| I10 | Allocation mode as a named row on the group; a pod may change a unit's sizing rows at an anchor without a new identity; group document with `display_name`, `parent`, rank, scope keys, `tag:` key | "More units, less each" becomes law; a stage change wipes a record | MISSING; `book`, `bms` shells | PH 31 |
| I11 | Level slot as a fraction of baseline, no ladder law | One validation story forced on four kinds of unit | MISSING | PH 22 |
| I12 | Conviction binding from a unit's signal to its sizer | A human's conviction cannot size | REFUSED (sizer inputs) | PH 1 |
| I13 | R as a declared basis on the row (gross at disaster stop by default; tail budget for no-stop units); `allow_widen` as a row | His scalper without a stop has no R; widening a law in code | Refused at compile and entry (`SWAP 11`); law in `unit_intent.py:725-757` | PH 9, 11 |
| I14 | Expectation at birth stored with the version: trade rate, spread of R, streaks, from replay | A new unit has no baseline; silence cannot be seen | MISSING | none |
| I15 | Worst-step term and margin facts at the order boundary; size sanity band and order-rate limit as multiples of the unit's usual | The one move that ruins passes every brake; a runaway unit | Margin rule in QMB only; no entry check found (`SWAP 14`) | PH 14 |

### 3.3 Records

| # | Record | What breaks if missing | Today | Swaps or widens |
|---|---|---|---|---|
| R1 | Decision row that replays (D42), with `explain_size(row)` as one pure function | "Why this size?" has no answer; agents cannot diagnose | Residue literal `0/1`; nothing stores inputs (`SWAP 1`, 4.1 row 15) | PH 12, 29 |
| R2 | Trade row v2 (D42): net and gross R, costs by kind, exit mechanism and reason code, MAE, MFE, bar path, session, slice, cost cell, world, stage, contract month, markout, readings seen, `counts_toward_proof`, placeholders used, numbers in force | No money ledger, no fair brake, no resize replay, no two-arm test, no numbers talk; a time exit, a signal exit and a cut all read `close` | `r` only; `r_after_costs` holds R with no costs (`SWAP E13`); `_trade` body lacks the fields (`SWAP 29`) | PH 11, 25, 26, 29 |
| R3 | `would_have` rows written while benched, in shadow, or refused by any gate or sticker, with `propensity` when a paper twin took a logged random share | Evidence freezes while stopped; gates cannot be judged; the handbrake stays hidden; the logic record quietly depends on the pod | Kind declared, no writer (`SWAP 29`) | PH 25, 29 |
| R4 | `risk_event` rows written; closed reason codes as appendable data; new code families for user-added blocks | New brake text has no code; a QMB run fails on `unlisted` | Kind declared, no writer (`SWAP 25`) | PH 25 |
| R5 | Cushion ledger with anchor type, clock, scope, realised and marked series; one ledger fold keyed by scope including pod | No house money pair; brake and accelerator contradict; each pair has its own ledger | MISSING | PH 1 |
| R6 | Records split by unit, market, session, slice and world | Windows, cost map, class bands, per-hour sizing, ORB per open all fail | Per market only (G7 5.3) | none |
| R7 | Fill record: decision quote, arrival quote, fill, partial, reject, requote, mid at several later horizons | No markout, no last-look evidence, no broker monitor | MISSING (R19 minute rows carry spread only) | PH 17 |
| R8 | Run stamp: real-tick share, quote source, gate settings, costs; arm id, link id, parent on run records; every arm a counted try | Scalper results on generated ticks look proven; a link is never credited or blamed | MISSING; `tries.py` counts tries | none |
| R9 | `RiskState` as one fold over journals, keyed by scope including pod and tag; state word, stamp, reason, UNKNOWN when stale; a fleet read over all units | Node reports health, not risk; agents read 200 units one at a time | Node health only; `journal_query` rows only | none |
| R10 | Root-cause key and event id on stand-down, risk event and order-failure rows; alert fields (action, deadline, actionable) | One incident is twenty cards; alarm load falls on him | MISSING | none |
| R11 | Per-change record on every self-configured update: before, after, whether it did worse | The learner cannot be judged or its cadence derived | Calibration rows exist without before and after | PH 7 |
| R12 | Lineage: candidate id, hash, parent, family, data and cost versions, claim as metric, benchmark and window | Agents cannot be charged for what they tried; a claim cannot be graded | `family_id` in the dummy; nothing else | none |
| R13 | Reading record: stamped when computed, never rewritten, backfill flagged; an as-of query shared by QMB and live | A backtest flatters the MIS (76 % in `MIS-PAGE-CONTENT` simulation) | Stamped records exist; the query UNKNOWN | none |
| R14 | Isolation accuracy record: each sticker writes whether a loss followed | Rules can never be scored | MISSING | none |
| R15 | Three positions side by side (intended, risk-approved, executed); requested, enforced, observed on every control; one trace id from reading to fill | Cannot tell what the guard cost from what the broker cost; his lowering is not journalled | Partly | PH 30 |
| R16 | Window card kind; recipe kind (template plus joints plus proof plan); block-entry fields `output_meaning`, `assumes`, `null`, `evidence`, `retest_by`, `knows_at`, `decides` | Sniping windows have no home; linking produces slop; a score sizes nonsense | `template` kind retired; fields absent | none |

### 3.4 Hooks

| # | Hook | What breaks if missing | Today |
|---|---|---|---|
| K1 | One seam both hosts call for every entry, with one wrapper so no guard, sizer, read or fold failure can stop an exit | A guard failure stops exits (CHECK B3) | Hook stub on the node, none in QMB |
| K2 | Read door and proposal door for agents: typed, expiring, scoped, de-risk default, raises as cards, direction on every operation | 200 units cannot be watched by agents; or agents reach further than they should | Catalog rows exist; tighten-only cards in one template; nothing applies them |
| K3 | Published-reading path from any app to a unit's `reads`, with age and fallback (road D) | Desks cannot reach units; node feed rewrite later | Not built; the MIS relay has no production importer |
| K4 | Second lane for one unit version: paper twin started the same minute, random-entry twin, control, canary | No early read on "edge never real"; no live cost gap | Node refuses a second deployment of one version |
| K5 | Promotion and live-money door outside anything an agent can read or reach, click bound to the exact effect | Fixed lines rest on agents' good behaviour | Promote is his click; channel isolation UNKNOWN |
| K6 | Block save door with contract test; a settle hook for RESTORE; a group-level place for an alarm budget and a share cap | QML cannot grow; restores have no hook; fleet rules have no home | Missing |
| K7 | Rehearsal test from template to a trade on the journal and a row in the fleet fold | The newcomer's walk rots quietly | `first_real_start.py --rehearsal` exists for setup only |

### 3.5 Invariants

| # | Invariant | Source |
|---|---|---|
| V1 | Exits are never blocked by any gate, sticker, guard, brake, read or fold; proven by a property test | fixed line; `X3-H46`, CHECK B3 |
| V2 | Only his hand lowers a kill level; a brake may raise a stand-down and, if its row says so, a kill level | fixed line; M49 |
| V3 | Agents never place, size up, lower a kill level or promote; their output reaches a unit only as a fact it chose to read, inside declared bounds, with expiry | fixed line; `H4 I-52` |
| V4 | Only he promotes to live; the click binds to one hash, level, markets and date | fixed line; `X1-H46` |
| V5 | The true floor is never reset by a restart or a banker act | AD-17 candidate 2; `H2 I26` |
| V6 | Stops tighten only, unless a row declares `allow_widen` | `SWAP 9`; canvas |
| V7 | No unit, pod or block depends on the MIS, a mini app, a QMB card or a Lab pass at trade time | `H3 T7`, M49, `E2` row 16 |
| V8 | Nothing in the baseline depends on a dollar value; every value is a labelled default with a reason and a range | M50; `BRIEF-COMMON.md` |
| V9 | Links and reckless settings warn and label; only the fixed lines refuse | `E4` 8e; `E2` row 14 |
| V10 | Same inputs and state give the same answer in every driver (node, QMB, paper, Lab); only fills, costs and latency may differ | `E2` (f) |
| V11 | Every risk row is evidence and may not be dropped by any observability stack | `H3 T69` |
| V12 | All socket widening lands in one compiler bump before any unit deploys | `E5` 4.5 |

### 3.6 What arrives later with no core change

Every sizing base, exit mechanism, brake, accelerator, gate, reading, isolation rule, allocator and pod in section 2 and in `FATES.md` marked "default block", "template" or "content later". The twenty pods and R9's eight pairs. The fifteen physics readings. The learner-and-applier object, bandits, pooled priors, the Simplex fallback. Trust-ladder levels, the Python hatch, expressions. The fleet-watch workflows and their mini-app face. The MIS finder and pack contents. Desks and departments. Recipes, the joints vocabulary, failure cards, three faces, the dictionary expansion. The file extension. Netting, limit orders, target-position curves. Canary analysis rules, the challenger, rehab, the governed pipeline (methodology). Alert delivery, the six words on screen, meters and scorecards (UI). None of these changes a socket above; each is a row, a block, a template, a workflow or a document on a seat that exists.

---

## 4. THE FIRST BASELINE

What a new user gets out of the box, after the one compiler bump. Every value is open, labelled with its reason and range, and shown on the unit's card as a shape, not an edge ("we don't have any proof", M49). It trades on paper with nothing set; it is editable by the copilot through `unit_new(template, overrides)`, `unit_check` and a pod patch; it does not depend on a QMB card, a Lab pass or the MIS. It depends on the sockets in section 3, and on nothing that waits for the numbers talk.

**Honest state today.** At the tip the baseline trades only in the narrow shape: one sizer reading four facts, one stop read once at entry, one target, one long-side time exit; no halt runs, nothing reads cost, intraday cannot go flat at a session boundary because `sessions` is refused (`SWAP` short answer, `E6`). So "trades out of the box" is true after S1 to S4, S6, S9, S13 and I2 to I4 land in the one bump (V12), and false before. The rehearsal test (K7) is what proves it.

### 4.1 Blocks switched on for every unit

| Slot | Shipped default | Values open | Why this one | Evidence |
|---|---|---|---|---|
| Sizer | Fixed fraction of a declared money base at the stop, costs in the denominator, round down, residue real; base chosen on the template (equity, or cushion above a user-set floor); converter to quantity from the record | fraction, floor, base | The one base BUILT in shape and REAL everywhere; needs no edge, record or MIS; sizes at the first tick | BUILT (narrow), REAL (`R1` pattern 1) |
| Exits | Disaster stop (swing or ATR, side-correct); R target; time exit side-correct; reason code on every close | stop method and buffer, target multiple, bars | The three BUILT blocks, fixed; a floor under every trade | BUILT, bugs fixed |
| Halts | `session-loss-limit-halt` at unit scope, `account-daily-loss-halt` at account scope, both `no_new_entries`; restore by rule at the next day boundary, retry-then-lockout | limits in R or money, window, rest, lockout counts | Two shipped halts, the plainest money brakes; a way back without his click | BUILT (never run in a host); restore REAL elsewhere |
| Gate | Cost hurdle: this quote, this stop, this unit's allowance, in R (SQS-2); the old SQS rule as a floor for broken markets (SQS-1); exits bypass | allowance, floor line | Scalper and intraday get different answers with no style code; no warm-up; his M51 frame | PROPOSAL over REAL cost shape; SQS-1 BUILT rule text |
| Stickers | News calendar to stickers with both FX legs tagged, strength from the calendar's tier, stale calendar fails closed; `unknown` for a scope the node cannot read | widths, strengths, tags | His news-day example (M51); the kill switch keeps the hard kill | calendar ingest BUILT and fails closed (G9) |
| Group row | Allocation mode `own size under a parent limit on losing together`; portfolio day stop reading the book's own sized sigma, `on_fire: stand_down(all) + card`; raise permission gate on | parent limit, k, gate on or off | His M49 complaint answered; his "switch off entirely" (M10) | REAL bank practice; MODEL for the stop |
| Numbers | Every number carries derivation, range, reason; motion: find (optional replay at birth), track (facts), correct (built engine, bounded, per-type preset); report with and without motion | ranges, cadence, which numbers correct | `E5`'s test: stacked, they held across every world tried; no new applier part | MODEL; BUILT engine |
| Records | Decision row, trade row v2, would-have, risk events, receipts, fleet fold | none | Without them nothing above can be judged, replayed or explained | BUILT in part |
| Kill switch and effects | Unchanged; YELLOW to BLACK effects read by entries as well as closes | effect table values | "earned its spot" (M5); entries ignore the table today (`SWAP 18`) | BUILT (closes only) |

### 4.2 Two ready-made templates, as presets with values open

Both compile and pass G on synthetic bars; both carry an expectation at birth from replay; both say on their card "a shape, not an edge". A third, the canary (`E2` Pod 19: fixed money per trade, one position, kill only), ships for a stranger's first run.

**Template A, `scalper-mr` (mean-reversion scalper style).** His first units (M49). Markets: a short FX list plus gold, by record; 1m and 5m bars; `position_limit` 1 per market, several markets. Sizer default with the cushion base. Exits: disaster stop, target, time exit, **fast-invalidation cut on**, read from the winners' MAE, with the warning "unproven after costs; run the two-arm test" (`H2 I16`, `I70`; MODEL; REVIEW M4's caveat stated on the block); breakeven off; no trailing until step 3. Halts: the two defaults, plus the own-percentile money bench on, the count brake ("about three", scaled to the unit's run length, halve) off but present, `session-fill-limit-halt` present. Gate: cost hurdle tight, SQS floor. Tolerates no stickers. Cushion rule on with a day anchor (reverse house money brakes on the way down, presses with winnings only), press gate as a block (`E2` Pod 4). Motion: correct on for filter numbers, off for size. Reads: none (stands alone); routing rung 0 or 1. Fleet: type tag `scalper`, family id. Not advised, warned: trailing stops, suspending stops in news.

**Template B, `intraday-trend` (intraday style; an `orb` variant differs in two rows).** 15m bars; sessions declared; flat before the session close with a buffer (`H2 I75`; needs S9). Sizer default with the equity base. Exits: disaster stop in ATR, R target, **thesis-invalidation exit on** (a named condition that proves the idea wrong closes the trade with its reason; `X3-H40`, Steward, REAL paper account), time exit at session end; breakeven off; trailing after a calibrated continuation when step 3 lands (`H2 I74`). Halts: the two defaults, own-percentile bench on, `losing-days-halt` present off. Gate: cost hurdle, SQS floor per open. Tolerates `open` in the `orb` variant only. Cushion rule off. Motion: correct on for filters, off for size press. Reads: none; `sessions` from the record's clock. The `orb` variant: one logic across several opens as one family with a family tag (`X0-25`), `position_limit` per open.

### 4.3 What a copilot can change on day one, and how

Through `unit_new(template, overrides)` and `unit_check` (BUILT): markets, bars, blocks in any slot that exists, every number's default and range, motion settings. Through a pod patch (needs the `pod` kind, S14): allocation mode, halts at group scope, tolerations, `on_fire`. Through a block save (K6): a new block. Through a new JSON in the templates folder: a new template with no other change (`SWAP` section 3). What it cannot change until the sockets land: halts, reads, sessions, per-market numbers, a second exit, moving risk numbers (`SWAP` section 3: "a copilot has no real risk choice to make from the shelf").

### 4.4 What the baseline does not do, by design

It does not prove an edge (methodology). It does not set a dollar value (numbers talk). It does not route by the MIS (rung 0 by default). It does not isolate a class by rule (the rule is off; the sticker exists). It does not press size on open profit. It does not need him to watch it: the two defaults restore by rule and the fleet watch (content, `E5`) ranks what to look at. It does not refuse a reckless pod; it grades it and says so in large type.

---

## 5. Logical flaws and collisions

Found across H1 to H5, E1 to E5, the old funnel and review, the swap chart and his words. Each is resolved, dissolved by configuration, or kept open with the reason. His own contradictions are set side by side and left to him unless a configurable answer dissolves them.

| # | Collision | Status | Resolution, or what stays open |
|---|---|---|---|
| C1 | **The cut catches winners.** His pictured scalper (55 %, 1:1) loses after costs at a 5-pip stop; the fast-invalidation cut rescues it only if it catches few winners: +0.086R at none, +0.012R at 10 %, −0.062R at 20 % (REVIEW M4, `more_arith.py`). No paper tests fractional cuts after costs (R8 gap 2) | **open** | The cut ships on in the scalper template with the warning on the block; the two-arm test on fixed entries is the first Lab job (methodology); if it fails, wider stops and fewer trades. k and the stop width are numbers talk. Not resolved by this funnel |
| C2 | **His two sizing statements.** "the more units I have, the less I can trade... these numbers are too fake" (M49) against "get the total amount of capital to be spent in a day... split it across the total number of units" (M10) | dissolved | The allocation mode is a row on the group (D31). Both are modes; the shipped default is own size under a parent limit. He never has to choose in the abstract |
| C3 | **Out of the box.** "we can't really just come up with something that works right out of the box. I would love to" (M10) against "something that anyone can use... right out of the box" (M49) and "something that out of the box can work" (M50) | dissolved | The baseline works out of the box; the canvas means nothing in it is fixed. The lead's briefs carried only the second half from L197 (TIMELINE) |
| C4 | **Size and the technical lens.** "for size, I think it's not part of the technical stuff" against "can technically position configure itself, position sizing and all that" (both M49) | dissolved | The mechanism is in (S1, S2, S13); the values are out (V8) |
| C5 | **Rules closing positions.** "may a rule close position by itself? I think no" against "the dictionary has closing mechanisms" (both M49) | dissolved | An exit is a block the unit owns (D6). The old question meant a portfolio rule reducing positions (de-gross, cushion clip); that is a guard verb `reduce` or `flatten`, a pod setting (E2 pod-life table) |
| C6 | **Several positions.** "isn't there a possibility that one unit can hold more than one trade at a go?" (M7) against "not every type of scalper per se will be able to hold several positions" (M8) | dissolved | `position_limit` is a template field (S17) |
| C7 | The MIS board fails open; isolation fails closed (X1 collision 9; SPINE line 253 shows them "together") | resolved | A sticker lives in the stand-down table, never as a board word; `unknown` is a state per scope (D27) |
| C8 | SQS blocks and never shrinks (`X3-H63`) against the graded cost dial (`X2-H42`) | dissolved | Both are blocks; the hurdle and the floor are the defaults; the dial is off on the modifier socket (D26) |
| C9 | `two_live_readers` compile refusal (PICK graft 3) against a reduce-then-bench ladder | resolved | A template warning, never a refusal (D10). Stacking is the user's choice |
| C10 | The edge dial fixed at zero (old DP10) against "a low one will get a buffer and a high one will get even a bigger buffer" (M10) | resolved | The edge is one input to a derivation; the default sizer needs none; a Kelly block reads it; no law (D3, D19) |
| C11 | "Why lots?" (M49) against `Size.lots` on every contract | resolved | Dollars at risk decide; a converter spells the order (S1). The seam word is his (`QUESTIONS.md` Q3) |
| C12 | The demo marks `kill` as `required: true` and the Lab says "Send to paper requires kill line set" against "a reckless setup must be expressible" | resolved, dissent recorded | Preset warning and grade in the largest type, never a wall (E2 row 14, V9). The risk voice in the party disagreed and lost |
| C13 | A pod block is "pure" (Lab AD-10) while guard rows keep `block_state` | resolved | State goes in and comes back (S15) |
| C14 | `qmx_lab.pods.simulator` as the one evaluator against the guard package on a replay port | resolved | One small core in a library both import; the simulator is a driver (S15, D38) |
| C15 | **Book as skeleton.** "the book is the right skeleton... It's just cleaner" (M10), "if the BMS or a book system doesn't make sense... let's do that" (M31), "I think we shall decide later" (M49) | kept open, his | A group document with `parent` reserved and an allocation mode keeps every shape possible (D35); "Classic Book" is a pod template. Not asked now |
| C16 | **Agents never touch money** against an agent cut that applies itself inside a pod's declared bounds (`E2` Pod 17, `H2 I95`) | **open, his** | Default: a cut-only fact a unit's own rule reads, inside bounds, with expiry; raises and placements are cards. `QUESTIONS.md` Q4 |
| C17 | The shipped decay job sends about 91 cards a night for 200 healthy units (`E5` 1.1, MODEL) against "Why would I have to be there monitoring units?" (M49) | resolved | One ranked row per unit, two lists, one incident one card (D44). The template's README calls its rule a starting form |
| C18 | `SlowState.read` keeps every trade for ever while every other block declares a `state_bound` (`E5` 2.1) | resolved | A bounded window is a core seat (S13). Flagged to repair |
| C19 | "QMX has the learner and no applier" (`X1-H03`, R7) against the built engine already doing the applier's job (`E5` 2.1 finding 2) | resolved | The applier object is content; the fields it needs are core (D16) |
| C20 | The horizon sizer's "0 % floor touches" is partly structural (old F12) and was sold as safety | resolved | A block labelled MODEL, never the law (D3) |
| C21 | R gross at the disaster stop (old DP11) against R at the working exit (X3 P17); his B9 reservation | resolved | R is a declared basis on the row (I13); gross at the disaster stop is only the default |
| C22 | Stop widening is a law in code (`unit_intent.py:725-757`) against the canvas | resolved | `allow_widen` row, warned (V6) |
| C23 | The first live entry waits hours for a live SQS baseline (SPINE 475) | resolved | The cost hurdle needs no warm-up; the curve artifact has a flagged borrowed cold start (D26, I6) |
| C24 | A stale board trades every listed market (`runtime.py:367-369`) against a widening router | resolved, hazard | Home markets are the fallback (I5). Must land before any wide list |
| C25 | A slice-by-slice build (43 PRs, old plan) against a compiler bump that moves every fingerprint | resolved | One bump before any unit deploys (V12) |
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
| C41 | `MIS-PAGE-CONTENT` has readings on H1 while his router wants 1m and 5m; persistence on 1m and 5m takes about 4 to 5 hours to show (simulated) | resolved | The finder is a session or day list, never a per-trade signal (D22, D23). He must hear this plainly |
| C42 | The admission gate as law refuses his scalper at most hours until fills exist (REVIEW M7) | resolved | Pooled stressed default labelled `uncalibrated`; the gate is a block (D19) |
| C43 | Agent-held demo positions invisible to every rule | resolved as a flag | `foreign` scope in account numbers (old DP33, kept) |
| C44 | Hedge-fund "pod" and the Lab's "pod" are one word for a team, a stack, a capital allocation and a package (`E2` (a)) | default vocabulary | Pod, pod deployment, desk, mini app (D32); his words, Q3 |

---

## 6. Architecture forks that are real

Five structural questions where versions should differ in shape, not plumbing. Each names the shapes, what each buys and costs, and the test the harness runs on both. None is decided here. The architects draw them; the fold picks with recommendations (M37).

**F1. Where risk rules run: unit, pod, or group.** Includes the old F-B.
- **Shape A, compiled in plus a thin group.** A pod is a design-time recipe expanded into the unit's own sizer, halts, reads and numbers; a thin group document holds only shared caps and a ledger (`E2` Way 1 plus thin group; candidate 3's unit-owns-its-brakes). Buys: the unit stands alone; backtest and node run the same thing; a scalper's brake travels with it; least new contract. Costs: a pod edit recompiles every member and the node refuses each until it has a fresh record; cross-unit rules have no home beyond caps; a stage change makes a new unit unless the two-fingerprint seat exists.
- **Shape B, one pod document split by scope.** Blocks declare placement; unit-scope blocks run in the unit's call, cross-unit blocks in one group stage on the node, slow blocks off-path at anchors publishing facts; an empty slot means the unit's own block, so "no pod" is the empty pod (`E2` Way 5). Buys: all four unit origins with no special case; pod-life questions become fields; one edit rolls out by pin; candidate 3's property test says two cut-only stages equal one table over 20,000 states (MODEL). Costs: the most new contract; a size trail crossing two stages; a pod lives on one place, so spanning is a mix of pods.
- **Shape C, a live group document above units.** The host's evaluator sizes and brakes every unit; units propose (`E2` Way 2; candidates 1 and 2's guard). Buys: one rank table, one edit for 200, agents watch pods not units. Costs: the unit's own sockets and five shipped halts go unused; a unit no longer stands alone; the QMB host call must be built.
- **Harness tests:** X4-01 (losing together), X4-14 (everything bad everywhere), a pod edit across 200 members, one scalper's entry latency with and without a group stage (UNKNOWN today, `E2` UNKNOWN 2), a unit arriving from a mini app with its own sizer.

**F2. How a number moves.** Includes the old F-A.
- **Shape A, learner and applier.** A learner publishes a target with bounds into status; an applier moves the value only in the number's mode (`off`, `at_flat`, `at_period_open`, `live`), with a retune share cap per cluster (candidate 1, VPA). Buys: numbers move between anchors; bands he can see; a measured herding guard. Costs: more parts; in `E5`'s test the applier added little.
- **Shape B, refresh at anchors.** Every derivation recomputed at the anchor and applied at the next; `authority` holds `off` or `at_anchor` (candidates 2 and 3). Buys: nothing moves unexplained. Costs: a day's lag on every learned number; all numbers move at once.
- **Shape C, find, track, correct.** A replay finds a start; facts track live; the built motion engine corrects from own trades, bounded, switchable per type; no applier object (`E5` 2.4). Buys: each job uses data suited to it; no new part; MODEL: held across every world tried. Costs: wander in calm conditions; the engine must reach risk numbers and gain a window; herding for sizes untested.
- **Harness tests:** X4-39 (the broker changes its costs), X4-60 (slow decay), a replay that flattered the edge, 200 units through one shared volatility shift (sizes, not filters).

**F3. Where the market sensor and the gate live, and who publishes.**
- **Shape A, the gate in the guard.** The SQS rule and its baseline producer inside a guard package, eight settings as rows (old DP25). Buys: one place, one rank table. Costs: hard-wired shape; the first entry waits for a baseline.
- **Shape B, node sensor, unit gate slot, one curve artifact.** A node-side sensor publishes with source `node`; each unit has an entry-gate slot with a verb list; an overnight curve factory produces one artifact read by SQS, MIS and QMB; any app publishes readings in the same record (`E1` SQS-2 and MIS-2 and MIS-4). Buys: scalper and ORB get different answers; no warm-up; a dead MIS is safe by structure; departments publish. Costs: the most new seats; curves stale across a real shift.
- **Shape C, the sensor inside the MIS, units read it.** Rejected before because the board fails open; with stickers in the stand-down table it is a different case. Buys: one app. Costs: a central dependency on the order path, against "units stand alone".
- **Harness tests:** X4-16 (the release the calendar missed), X4-32 (spreads widen everywhere), the MIS stopped with a wide-list unit running, a holiday on a same-minute curve.

**F4. Where status, the fold and the evaluator core live.**
- **Shape A, a status file beside R22's snapshot** (candidate 1). Buys: simple recovery. Costs: Windows `os.replace` raises under a reader (CHECK).
- **Shape B, journal rows only; recover is a fold** (candidate 2). Buys: one source of truth. Costs: record holes; slower recovery.
- **Shape C, inside R22's snapshot** (candidate 3). Buys: one file. Costs: logic and risk state die together.
- **And the core library's home:** inside QML (sits in the node's lock, so a change bumps the money app and needs his signature, `SWAP 2.2`) against a new small package both import. Buys and costs are the signature cost against one more package.
- **Harness tests:** X4-48 (restart and crash loop), X4-55 (upgrade mid-day), a cold restore of calibrated values from calibration rows (UNKNOWN whether they rebuild).

**F5. Exits: ownership, rank, venue, and the pod's reach.**
- **Shape A, exits on the unit with the compiler's fixed order (close beats partial beats amend); the node closes targets** (candidate 3, old DP26). Buys: the unit stands alone; works today. Costs: backtest and live differ on a wick.
- **Shape B, an exit stack ranked "safest wins" in the guard; targets rest at the venue** (candidates 1 and 2). Buys: backtest equals live on a wick; one rank table. Costs: an amend may wipe the stop until R24 proves otherwise (CHECK B6); exits touch a shared stage.
- **Shape C, exit rows a pod may swap at an anchor without a new unit version** (the scalper voice's ask, `E2` round table). Buys: tighter cuts as a stage changes without re-proving. Costs: R changes under the record; the logic record needs would-have rows to survive.
- **Harness tests:** X4-25 (weekend gap through the stop), X4-31 (flash crash), a stop and target on one wicked bar in QMB and on the fake broker, a pod swapping the cut width mid-record.

Not forks: the level ladder against an evidence bar (D4 made it a slot); the Book against tags (D35, his later); the old shapes A, B and C of the first funnel (REVIEW M12).

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
| H-06 out of the box | 4, after the one bump (V12); C3 |
| H-07 works before the numbers | V8; 4 |
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
| H-18 any amount of stress | S5; S14; chassis stress battery D39 |
| H-19 design for complexity | S15 three functions and the deletion test; learner object and status object kept out of core (Appendix B) |
| H-20 one template by type; types change | D4 free type tag; I9; 4.2 |
| H-21 scalper differs from intraday | 4.2 A against B; D26 |
| H-22 mean reverting differs from trend | D7 families; 4.2 |
| H-23 every number has a reason | S13; R1 |
| H-24 derivation changeable | D15 |
| H-25 ranges and reasons for moving | S13; R11 |
| H-26 some his, some self-set | D17; never-self-tune list |
| H-27 no key setting blank | S13 (a blank blocks the live click only); census test D50 |
| H-28 sizing not leaning on the edge; edge as a range | D3 default needs no edge; edge band on R12; D4 |
| H-29 a weak edge can still pay | D3, D14, no choke law; honest: C1 is open, no proof exists |
| H-30 sizing across all instruments | S1 converter; I4 |
| H-31 adjusts over pips and points | S1; I4 |
| H-32 unit of measure settled | D1 dollars; the seam word is Q3 |
| H-33 more than one position | S17; D48 |
| H-34 growth over 24 hours not one fixed percentage | R5 anchors; D13; stage switcher content |
| H-35 the next day | R5 anchor clocks; restore by rule 4.1 |
| H-36 start with little, let it adjust | D3 cushion base with a user floor; I3 budget share |
| H-37 frequency as a sizing basis | trade rate on the fact surface D2; frequency blocks content; C1 open |
| H-38 costs known per market, instrument, timeframe, time | I2; I4 |
| H-39 QMX observes costs and acts | D18; D26 |
| H-40 off an instrument on its news day | D29; S10 |
| H-41 drift rule from agents | D16 correct; D44; three speeds content; methodology (8) |
| H-42 same on demo and live | I3 budget share; V10 |
| H-43 demo units at first boot | 4.2 templates and the canary on the paper lane |
| H-44 plans behind the code read | `SWAP` read the plan against the code; `UNIT-PLAN.md` not read in full by this judge (Appendix C) |
| H-45 stand-ins planned for the swap | section 3 placeholder columns cover PH 1 to 31; PH 19 (close, hedge or alarm) is an `on_fire`-style field on the protection row (S5); PH 24 is a restore row (S4); PH 26 (judge with fixed size) is the report with and without motion (4.1) and a judge baseline for methodology |
| H-46 dictionary's closing mechanisms used | D7; S3 |
| H-47 fast invalidation everywhere | 4.2 A on; D7; C1 |
| H-48 stop chosen on purpose | D7; I13 |
| H-49 dynamic SL and TP looked up | D7 (`H2 I74`); 4.2 B |
| H-50 closing never blocked | V1 |
| H-51 brakes and accelerators defined | S5 row contract (R9's nine attributes); D8 |
| H-52 definitions from his words | D13 (his reverse house money); R9 built on the transcript |
| H-53 some taken, some refused | `FATES.md`; D10 on against off |
| H-54 house money stays | D13 |
| H-55 reverse house money available | D13, on in the scalper template |
| H-56 tools, not law | D14; V8 |
| H-57 old circuit breaker improved | D10 two-speed; 4.1 |
| H-58 alpha decay | D16 correct; CUSUM block content; D44; methodology |
| H-59 know what is breaking | S5; R4; R10 |
| H-60 brake set open | D10 |
| H-61 no one standard for frequency against brakes | own-percentile block; per-type presets D16 |
| H-62 what frequency does to brakes | `H2 I6` finding on the row (MODEL); methodology (8) |
| H-63 exposure, drawdowns, unrealised and realised measured | R9; I3 basis; R5 |
| H-64 isolation by class, region, instrument | D27; D28; S10; S11 |
| H-65 floor not reached; his to set | user floor on the cushion base; V5; never-self-tune; "not reached" is a numbers-talk claim, not a mechanism |
| H-66 scenarios generated | replay path S15; scenario kind and generators content; X4's 99 as data |
| H-67 risk at unit, cluster, methodology, portfolio | S11; S7; S14 |
| H-68 Book and BMS open | D35; C15 |
| H-69 BMS self-optimises | allocator off-path at anchors (`E2` (c)); best basket and slot rebalancer content |
| H-70 pods ship | D36 |
| H-71 pod ideas offered | D34 gallery of twenty |
| H-72 mini app with the risk system | D36; Risk Lab app content (`H3 T34`) |
| H-73 new mini apps | D36 landers |
| H-74 mini apps feed each other | D37 roads |
| H-75 units from any source trade | V7 |
| H-76 new versions of the risk part | D40; D36 levels |
| H-77 schemas | S16 real kinds; schema beside code (`H3 T8`) under D50's census test |
| H-78 external code | D46 |
| H-79 agents reach it and know it is correct | D43; contract tests; self-test card D40 |
| H-80 QML against slop | D45; `E4` 8d skill rules |
| H-81 Python only where QML can't | D46 |
| H-82 QML dictionary improved | D45 content, early |
| H-83 the unit is what ideas become | D45; D46; S16 |
| H-84 a new unit or pod any day | D36; D37 futures week walk |
| H-85 lens beyond the unit | 2.8 to 2.14 |
| H-86 MIS, SQS, brakes, accelerators, QML open | D22; D26; D10; D14; D45 |
| H-87 overhauls must perform better | evidence labels on every option; `E1` recommendation reasons |
| H-88 MIS as router holds its weight | D23 finder content with lists scored side by side |
| H-89 how does the MIS adjust | D24 |
| H-90 sniping windows found | D30 |
| H-91 session opens catered for | D30; S9; `open` stickers |
| H-92 physics and RVOL have a place | D25; I7; `QUESTIONS.md` Q2 |
| H-93 trading node ideas | S6 node sensor; S18; D47 |
| H-94 where it runs left open | placement field S5, S14; a pod's home is one place |
| H-95 cTrader first, then Hyperliquid | FX via cTrader in 4.2; crypto rows content; D21 |
| H-96 he does not monitor | D44; 4.4 |
| H-97 200 units real | D44; I9; R9 fleet read |
| H-98 agentic workflow as a mini app | D44, workflow first, app face; flaws to the agentic upgrade (8) |
| H-99 never-real edge found earlier | K4 twins; R12 lineage; `H4 I-01` kit (methodology) |
| H-100 logging, monitoring in the lens | D42 |
| H-101 he can tell what is working | R9 state word; six words (UI) |
| H-102 ledger exists and grows | ledger v1 stays a planning map (835 rows, re-tier before relying, `H2 I97`); the runtime truth is the number spec, registry rows and the couplings check layer (S13, S5, S19) |
| H-103 terms agents can use | words table; D32; `E2` (a) |
| H-104 agentic upgrade has room | D43 doors; section 8 |
| H-105 copilot talks numbers and makes templates through QML | 4.3; templates folder; numbers talk (8) |
| H-106 tools for agents | K2; K6; section 8 |
| H-107 agents propose, he promotes | V3; V4 |
| H-108 MCPs and the Lab | S15; agentic upgrade (8) |
| H-109 Shepherd and departments | section 8 agentic; D37 desks |
| H-110 a mini app per market as his pod | D32 desk; D37 |
| H-111 failed strategies reworked | D16 hill climb as a Lab job; methodology |
| H-112 findings stored | R16 window cards; failure cards content (`E4 L20`) |
| H-113 methodology per kind plugs in | D4 level slot; free type tag; verification template per type content; section 8 |
| H-114 edge verification as a workflow | K4; R8 arms; methodology |
| H-115 Monte Carlo and backtest reading by agents | methodology (8); judge presets exist |
| H-116 UI needs list | section 8 UI |
| H-117 notifications are a UI question | section 8 UI; alert fields R10 |
| H-118 UI itself and its notes looked at | **not held by this funnel**: `E2` read the demo's block names and the notes, nobody ran the UI; handed to the UI session with the request |
| H-119 500 to 5 grand expressible | D3 full Kelly block; D14; V9; the argument is parked |
| H-120 small capital concentrates | D31 best-basket mode; D5 feasibility verdict |
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
| H-135 no $500 bias | no dollar simulation used; V8 |
| H-136 raw words read | section 1; `SEEDS-2` Part A read in full |
| older 2 N8N extensibility, white label | D36 diffs plus pins |
| older 3 types: MR scalper, ORB, trend | 4.2 A, B and the `orb` variant |
| older 11 edge-led sizing expressible | D3 Kelly block |
| older 14 Kelly after costs | D19 ceiling block |
| older 16 one-shot breakeven | D7 breakeven block, off |
| older 19 same bet once | I9 bet key; S7 |
| older 20 System 1 over System 2 | D23 rungs 0 and 2 |
| older 22 losing-run brake per type | D10 count brake |
| older 26 kill switch and SQS outside | D26; V2 |
| older 29 Books register on the BMS | D35 group with parent |
| older 37 where it runs | D50; S5 placement |
| older 39 what QMB hands over, what the MIS publishes | I14; S8 |
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
- Seats this funnel left for you: K4 twins and canary; R8 arm fields; R12 lineage and the scoreable claim; I11 level slot; I14 expectation at birth; the verification template per type as a preset (`X5-H40`); judge baseline with fixed size (PH 26).
- Warnings: every "core" X5 fate came from the go-live and dollar lenses; honest evaluation certified no LLM-found strategy (`2608.27734`); resize replay explores, a QMB rerun proves.

### For the agentic upgrade session
- The door: D43 (read, propose, run; direction on every tool; evidence intake per unit; protected fields; the money door outside agent reach, `E3-26`).
- Harness flaws, measured: `H4` section 6 (20 rows) and `E5` section 6 (19 rows). The first ten to fix: one unit template; no row saves a block; compile refusals; no fleet read; an app cannot read journals (`data_reads` is `market` only); an app's `workflows` entrypoint has no installer; app-to-inbox path unconfirmed; `build-mini-app` and `build-pod` skills are placeholders; tools declare approval not direction; judge lands as the operator.
- Jobs (content, yours): triage, morning words, coroner, sitting-duck advocate, drift explainer, prospector, slow isolation cards, per-class agents and event mapper, template version drafter, tuning proposer under the applier (`H4 I-40`, `I-67`; `E5` 1.2).
- Department seeds: `handoff/AGENT-DEPARTMENT-SEEDS.md`, M35, M50; `H4 I-68` to `I-78`; `E2` (e) desks; `E3-25`, `E3-27` to `E3-30`; `H5` ideas 2, 3, 7, 38 to 44.
- Conditions: agents never touch money; only he promotes; exits never blocked; Q4's default until he rules.

### For the UI session
- Not done here: nobody ran the UI (H-118). Please look at it and the notes (`UI-NOTES-UNITS.md`, `UI-BACKLOG.md`) first.
- Needs from this design: a size trail equal to the decision row (`explain_size`); the six words and UNKNOWN; stickers and tolerations shown, with "why didn't it trade"; the pod gallery (D34) and the empty pod; the fleet screen (one screen at any fleet size, ranked rows, one incident one card); first-run ticks on done not opened; alert tiers against Settings' "Alert me when" and the phone push list; the MIS tab, market card, weather report; a card's wording for a stranger; the kill line warning in the largest type.
- Lists on disk: `X6` section 9 (16 screens); `X7` Appendix B; `E5` section 7.

### For the numbers talk
- `PARKED-FOR-NUMBERS-TALK.md` plus: the fraction, floor and base of the default sizer; the two halts' limits; the cost allowance and SQS floor line; k for the portfolio day stop and for any admission gate (with REVIEW M4's table beside it); the parent limit; the count brake's run length; press strength and anchors; K and the strict bar for the fleet watch; whether gold's windows hold (R2 against his M50); 500 to 5,000 and large risk without ruin (`H2` gap 1: no design on disk used that lens; Group B of `H2` is the parts list); game theory (`1912.04012`, `md\15541`, `md\17546`); where to allocate units across instruments (`E4 L18`, `E3-23`).

### For the repair session (DeepSeek), nothing to do now, flags only
- Files this session claims before deletion-4 and C-20: `sqs_baseline_producer.py`, the SQS rule text in `labelers.py`, `qmn/replay/port.py`'s SQS rule, `registry_catalog.py`'s SQS rows, `qmn/data/news_calendar.py`, `qmn/protection/windows.py`, `dispatch.py`, `qmf-risk/control_window` (old DP24, DP25; `handoff/FOR-REPAIR-CLAIMS-BEFORE-C20.md` must add the last three).
- Findings: `SlowState.read` has no bound and reaches snapshots (`engine.py:124`); the stale-board fallback trades every listed market (`runtime.py:367-369`); the sizer slot has no face check and 5,000 lots passes the QML host (`SWAP E8`); `_CEILING = 0.005` in the contract test will fail any real sizer (`SWAP E9`); the exit contract test feeds evidence the host refuses (`SWAP E10`); entries ignore the kill effect table (`SWAP 18`).
- Open hand-offs from App F still stand (`SWAP 4.3`): the signed stop distance, target at broker or node, a unit with no stop, moved numbers and open trades, which exit wins on one bar, R and costs, kill level meanings.
- The one bump (V12) wants a word with the landing order: all socket widening in one compiler format bump, on landed tips, before any unit deploys.

### For the release lane
- `E5` G1 to G3: no installer a stranger can run; install and launcher describe the older host; first start hands over to a desktop app nobody could find.

---

## Appendix A. The party, run headless

Four voices, one mind: a scalper (trader), a risk quant, a systems engineer, a developer who will maintain this. Nobody could be asked anything. The exchange below is the part that changed a call; the rest agreed with `E1` and `E2`'s own round tables and is not repeated.

**Trader:** Your horizon formula decides my size by a survival sum I can't explain to myself. The fixed fraction I can. Ship the one I understand and let the clever one be a block.
**Quant:** The fixed fraction has no survival story at all.
**Trader:** It has a floor I set and a daily halt I set. That's a survival story a person can hold.
*(So: D3's default is the fixed fraction; the horizon formula is a labelled block.)*

**Developer:** Every one of your sockets changes the compiler. The node refuses a fingerprint its record didn't test. Land them one slice at a time and every deployed unit re-proves itself every time.
**Systems:** Nothing is deployed yet.
**Developer:** Then that is the one cheap moment, and it ends the day a unit goes live.
*(So: V12, the one bump, and the first flaw in the pre-mortem.)*

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
*(Dissent recorded at C12; the quant lost.)*

## Appendix B. Elicitation, run headless

**Pre-mortem.** It is May 2027 and the baseline failed. The likeliest stories, each with the row that answers it: (1) the sockets landed in four bumps and the first live units re-proved themselves four times, so nobody dared bump again and `reads` never shipped (V12). (2) The cost hurdle refused every scalper entry in costly hours for a month and nobody saw it, because would-have rows were declared and never written (R3 goes early in the build order). (3) The parent-limit default let eight correlated units lose together on one release; the portfolio day stop was a row nobody switched on (it is on in the group default, 4.1). (4) The templates were read as proof; a stranger went live on `scalper-mr` and lost (every card says "a shape, not an edge"; the live click needs the placeholders acknowledged). (5) Two hundred units, ninety cards a night, and he turned the alerts off (D44). (6) A pod edit forced two hundred fresh test records and pods were abandoned (I9's two fingerprints). (7) The copilot built a sizer that took a trigger-shaped block and traded 5,000 lots (S1's face check and limits in one place).

**Red team, against the core list.** *"Too much machine again."* Answer: each row met a deletion test: remove it and name what reappears or reworks. Rows that failed moved to content: a separate applier object, a dead band, a retune share cap, a Simplex fallback, a target-with-bounds status object, a central oracle, runtime `affects` edges, the permission controller. *"The baseline is still a sitting duck: halts, a hurdle, a floor, stickers, a parent limit."* Answer: every one is a block with an off switch and a labelled value; no cut-only law exists; the accelerators are a toggle away; the raise permission gate is a group row a reckless pod removes; the sitting-duck advocate is named content. *"You kept everything again."* Answer: fates are not kept or dropped, they are placed; the core is 19 sockets, 15 inputs, 16 records, 7 hooks and 12 invariants; the first baseline switches on nine slots and ships three templates; everything else is content on those seats, and `FATES.md` says where each lives. *"The cost hurdle is a PROPOSAL and you made it a default."* True, and said so; its shape rests on REAL cost research, and SQS-1 stands behind it as the floor; shadow rows and the control gate will tell. *"Find, track, correct is one agent's model."* True; it is one side of fork F2, and the seats it needs are the same seats the other sides need.

**First principles.** What must a unit have to trade? A price, a size, a stop, an exit and a venue. Everything else is a reading or a rule it chooses to read. So units stand alone (V7); the core is the sockets, never the blocks; a reading is a record anyone may publish (S8); and the first baseline is the smallest set of blocks that fills every socket with something BUILT or REAL, which is what section 4 ships.

## Appendix C. What I did not verify

- I ran no code and no test. Every line number is as H1 to H5, E1 to E5 and `SWAP` reported it at tips `255f3bbf` or `351e7521`.
- I did not open the UI, the UI notes, `UNIT-PLAN.md`, `CONTRACTS.md`, the Lab spine or the candidates' spines; they reach this file through `H3`, `E2` and `SWAP`.
- X0 to X7 reach this file through the harvests and `HYBRID-FATES.md`, not a fresh read of each hybrid body.
- `E1` Appendix A and `E4` section 9's seeds were read as lists; their fates in `FATES.md` are placements, not judgments of each.
- UNKNOWN and carried as such: whether `block_fingerprint` covers the whole entry; whether a Library block reaches a live node end to end; whether a newcomer's first day needs a broker (G8); whether the node processes units one at a time; whether calibration rows can rebuild a cold restore; the real latency cost of a group stage at scalper rates; his original wording of the MIS and SQS design request.
- The party and elicitation were one mind. Their dissents are recorded, not independent.
