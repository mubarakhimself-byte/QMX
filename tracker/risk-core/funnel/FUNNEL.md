# The funnel: one consistent set of decisions

Fable funnel judge, 6 Nov 2026. Brief: `linking/FUNNEL-BRIEF.md`. Rubric: `linking/RANKING.md`. Inputs read in full: X0 to X7, G12, SEEDS (A to E, replies, "What the technical lens must hold", changes of mind, unanswered questions), STATE items 25 to 45, his 6 Nov words. Evidence spot-checked: `linking/stage-b/X2-sizing-accelerators/sims/out-1000.txt`, `linking/stage-b/X3-brakes-exits-drift/out-200.txt`, `grounding/sims/frequency_flaw_and_brakes.py` (through X0 and SEEDS C29), component rows A1-036, A1-087, A1-105, A1-115, A1-153, A1-154, A4-002, A4-091, A4-152. Ledger: `ledger/check.py --with-additions --no-write` (903 variables, 1,758 couplings, 7 duplicate ids, 5 alias warnings, 3 orphans).

Companion files: `HYBRID-FATES.md` (every hybrid's fate), `ledger-merge.yaml` (id merges and deaths), `working/flaw_arithmetic.py` (the arithmetic behind section 3), `working/roundtable.md`, `working/premortem-redteam.md`, `working/lookups.md`.

Scores are 0 to 3 on RANKING's six criteria: **P** performance, **S** survival (0 blocks), **E** evidence, **A** asymmetry, **F** fit, **C** self-configuring. **[judgment]** marks my opinion. No number here is a value; every number is a shape, a derivation rule or a range for the numbers lens.

## 0. The set in one page

The chassis is **one risk profile document per unit**, with a spec he and agents write, a status only the runtime writes, and suggestions only agents write. Types are **presets over style x class cells**; a new class or style is a row or a column, not a template. Every number has a **derivation block** with a fallback ladder (own record, pooled group, class, preset, refuse) and a receipt; a **learner** publishes targets with bounds and an **applier** moves them only in the mode he set per number (shadow, at flat, at period open, live). Numbers he owns (floor, buffer, kill line) sit on a **never-self-tune list**.

The money path is **one guard package with two host adapters** (QMB and the node). It computes every statistic the slots read, holds the clamps (per-trade worst case, order rate, margin headroom, stop side, size sanity band), runs cluster and portfolio brakes, answers `before_order` with pass, shrink or refuse, applies one **rank table** (any brake cuts, a raise needs every brake clear), and emits a **RiskState** row every pass that the UI, the phone, the Lab and agents all read. The Book and BMS containers become **cluster tags** (style, driver, logic family) and **one portfolio guard config** (floor, buffer, high-water mark, aggregate limit, bet-key rule, isolation protocol, slot policy, rank table, never-self-tune list); the words Book and BMS can stay on screen.

Size comes from **survival, not from the edge**: per-trade risk = usable cushion over (result spread x z x sqrt(horizon trades) x book-swing factor), computed at each anchor, with the book's day swing split across units by effective bets on residual stressed correlation. The edge is a **range** that touches three things only: the gate (low end positive after costs), the level (proof ladder) and a cost-and-gap Kelly ceiling. Costs enter in three places: the denominator (stop plus round trip plus stressed slippage, per instrument and hour and world), the ceiling, and the admission gate. Levels are fractions of the derived baseline, climbed on cohorts with an evidence bar per level, reset to level 1 on any world switch.

Brakes are **money at the unit's own percentile over a window in trades**, graded (REDUCING at own p10, BENCHED at own p1), with fast-invalidation cuts counted by size on a money ledger and an event ledger for decay. The old circuit breaker keeps its name: the fast trip is this brake; its slow half is a fire-density sentinel in Basel zones; a trade CUSUM is the second key. Count brakes survive only as his "about three" scaled to the unit's own run length, in shadow until a persistence test says they earn timing. Every brake ships shadow-first, must beat a random brake of equal fire rate, carries a scorecard, and may not exceed a choke budget. Restores are half-open probes with a memory ceiling; a bench clears by rule with retry-then-lockout; HALTED, the kill switch, promotion and lockouts wait for his hand. Accelerators are one cushion pair on one declared ledger (brake half on from day one; house money off until its proof card passes), tiers with a dwell, persistence presses after a block test, pyramiding for trend units only; any raise passes a headroom gate.

Exits are a **stack**: safety exits (disaster stop at the venue, forced flat, kill close) and strategy exits (thesis fast invalidation, a price backstop from the winners' adverse excursion, time, target, trail where the unit's own persistence allows), the safest wins by rank, exits never blocked, stops only tighten, per-style families as defaults with a two-arm test as the override. Isolation is one protocol: scope keys (class, region, currency, underlying, session), two tells that agree, graded modes, a time to live, staged resume, retrip back-off, a precision record; news is measured impact with driver tags, entries only.

Drift is **three speeds in one monitor**: inputs in days, warnings in weeks that step one level down reversibly, confirmation in hundreds of trades that moves a unit to paper, with a money brake apart and one lifetime false-demotion budget at the portfolio. Verification is a counted birth, a frozen contract, a proof battery on net returns, a band from four shrinkages, a plan with a correlation column, a machine check against a twin in a week, a bound click that approves one hash at one level on these markets until a date, and proof that continues at level 1. Agents reach all of it through **three surfaces** (read, propose, run), every operation carries a direction (read, propose, cut, raise, money), agent evidence can only cut and expires, every proposal is an effect-bound card ranked by money both ways under one attention budget, and the fast loop never waits for a model.

The whole set is proved by the **scenario harness**: every scenario against every profile version with QMX's own brakes inside the path, three cases, a random-entry dry chassis, a scorecard with survival gates and a cost-of-conservatism column. The numbers lens runs it.

---

## 1. Decision points and picks

Sources merged: X0 section 1 (11 rows); every layer's problems, collisions and restructure proposals; G12 hand-offs 1 to 37 and "What the funnel must know" item 11. Duplicates merged where three layers described one thing. 34 decision points.

### A. The chassis

#### DP1. The unit of defaults: type, cell, or dial
Options: (a) one template per unit type as the top shape (his A5; X1-H16 alone); (b) presets over style x class cells with an override chain (X0-44, X1-H37, X1-H16 as the preset layer); (c) holding-horizon dial (X0-49).
- (a) P1 S2 E2 A2 F2 C2: ships complete per type; a new class means a new template; cannot pool thin instruments; nothing self-derives across types.
- (b) P2 S2 E2 A3 F3 C3: a new class or style is a row or column; pooling across the class gives thin instruments a reasoned number; provenance on every value; software inheritance checked (VS Code, systemd, n8n); no held-out trading result for pooling.
- (c) P2 S2 E1 A1 F1 C2: catches style drift by measured hold; collides with A5 and with entry-logic families that share a horizon (a breakout and a mean reversion at one h want different exits); wild.
**Pick (b).** Types are presets (`scalper-mr`, `orb`, `trend-pullback`, next) over cells; the chain is preset, style, class, bucket, instrument, venue account, unit, market, timeframe, session, event; later wins; children only tighten caps; event overrides expire. X0-49's one gift survives as a measured field `holding_horizon` (realised hold against the preset's range) that raises a yellow, never changes defaults. Resolves X0 collision 4, X1 collision 7 (timeframe and session axes exist as keys before their data exists; a cell with no evidence resolves to its parent and says so). Assumes: compiler format bump (X1-H56) and the census test (G12 item 2).

#### DP2. The document, its parts and its plug-ins
Options: (a) risk profile as its own document with spec, status, suggestions (X1-H15, X1-H01, X7-H06), packs with combiners (X1-H17), three verbs (X1-H20), needs list (X1-H19); (b) everything stays inside the unit document with no profile id (today's shape, G8).
- (a) P2 S3 E2 A3 F3 C3: one profile serves many units; versions without touching logic; unknown fields refused; agents write suggestions, never spec; Kubernetes and Nautilus patterns checked.
- (b) P1 S2 E2 A1 F2 C1: fewer kinds; every risk change is a unit version; parsed-and-ignored fields recur.
**Pick (a).** The profile is embedded at compile so the unit stands alone on the node (resolves X1 collision 1: the snapshot rule exempts profile-only changes from cold-starting logic state; the profile's own state starts cold). X7-H06 merges into X1-H01. Packs stack with a declared combiner per slot (`smallest_cap` for sizers and modifiers, `all_must_pass` for gates, `newest_wins` for exits is refused: exits use the rank table of DP5). The needs list is the compile-time check that no halt is bound to a statistic nobody computes.

#### DP3. The self-configuring loop
Options: (a) learner with bounds, applier with modes, guards with freeze, asymmetric motion, derivation blocks with a fallback ladder, reason codes on every value (X1-H02 to H08; X2-H51 for sizing inputs; X3-H61 for brake thresholds; X5-H40, H42 for verification thresholds); (b) guard overrides numbers from outside the unit (X1 P2 option c); (c) bandit over approved profiles (X1-H48, X2-H53).
- (a) P2 S3 E2 A3 F3 C3: fills the half of the VPA loop QMX lacks; every move has a receipt and a way back; a bad learn never reaches open trades in `off` or `at_flat`; no trading study of a learned fraction beating a fixed one on independent trades (R9).
- (b) P1 S2 E1 A1 F1 C1: moves self-configuring out of the unit (against D32).
- (c) P2 S2 E0 A1 F2 C2: no trading test; nonstationarity breaks the guarantee; wild.
**Pick (a), one applier organ for all three number families** (sizing inputs, brake thresholds, verification thresholds). Default mode for any new number: `shadow`; working mode: `at_flat` for scalpers, `at_period_open` for units rarely flat; `live` reserved and never for a never-self-tune row. Decay counted in trades. Herding guard: a retune share cap per cluster per window (X1 P16 a), shown on the card as the reason a unit waited (X1 collision 26). "Flat" for a multi-position unit (X1 gap 2): flat means no open position on the market the number applies to; unit-scope numbers apply at the next anchor. D32 against pooled priors (X1 collisions 2 and 25): the unit chooses its rung order and the receipt says `borrowed:<group>` when a pooled value is in force; the unit still configures itself, it just borrows evidence. (c) kept for later.

#### DP4. Where the levels live: Book and BMS, tags, or an oracle
Options: (a) profile, cluster tags and one portfolio guard config (X1-H40), with three tag kinds: style (the Book), driver (co-loss, X3 restructure 5), logic family (proof, X5 restructure 6); one compile target the Lab also produces (X1-H33); (b) Book and BMS documents as named (A4-092; "the Book is the right skeleton", B3); (c) a central risk oracle (X1-H69); (d) no cluster level at all: profile plus one portfolio config, bet keys and the parent limit do the co-loss job, family is a tag for proof only.
- (a) P3 S3 E2 A2 F3 C2: driver clusters catch co-loss a style Book never saw; one floor and one high-water mark instead of per-Book buffers that add up to idle money (his C11); self-optimising slots become a document edit; systemd drop-ins and SIMM buckets checked; no QMX generation ran tag clusters.
- (b) P2 S3 E2 A2 F2 C2: his words; the Book path code exists (5,951 lines); cannot express intersections (his B1); per-Book buffers.
- (c) P1 S0 E1 A0 F0 C1: single point of failure; breaks "the unit stands alone"; blocked on survival.
- (d) P2 S3 E2 A3 F3 C2: fewest parts; right while units are few; loses the hours clause per driver and family proof pooling as first-class rows, which are what breadth needs later.
**Pick (a) as the target; (d) as its first increment; (b) goes to the arena as the competing version** (section 5). The words Book and BMS stay on screen for the style tag and the portfolio config if he wants them (Q2). (c) dropped. Resolves X1 collisions 5 and 21, X5 restructure 6, X3 restructure 5. Frees the Book path and the `qmf-risk` modules G12 section 3 lists once the guard ships (hand-off 32).

#### DP5. The guard, the hook, the states and the kill switch
Options: (a) one guard package, two host adapters (X1-H26, H57); `before_order` pass, shrink, refuse with closed codes (X1-H27); one rank table per scope (X1-H13, X3-H59, X4-59); a five-state spine ACTIVE, REDUCING, BENCHED, HALTED, RESTORE (X3-H59); kill levels as facts the spine reads, never set by a brake (X3-H62, X1-H28); (b) map kill levels onto the states (X1-H10's mapping); (c) blocks compute everything per market (X1 P3 b); (d) an app publishes statistics like the board (X1 P3 c).
- (a) P2 S3 E2 A3 F3 C2: backtest equals live for every brake above the position; units on one account finally see each other; node-local so no trade-time dependency; RiskGate without the hop.
- (b) P2 S2 E2 A2 F1 C2: one table in the UI; changes a control that "earned its spot"; a brake could set a kill level by mapping.
- (c) P1 S1 E2 A1 F1 C1: per market only; cross-unit statistics impossible.
- (d) P1 S1 E1 A1 F0 C1: breaks ruling 11; fails open.
**Pick (a).** Two tables stay (states and kill levels) and the UI shows both (X6-09). The kill switch's effect per level (hand-off 23): YELLOW no new entries at scope; ORANGE no new entries and amends tighten only; RED close this node's positions and no entries; BLACK close, pause everything, resume only by his hand. The BMS breaker raises a stand-down at `all` and lands a one-tap escalation card (X7-H43); it never raises the kill level itself (resolves X3 collision 5 and question 2 without a ruling: "kill switch and SQS stay"). The hook as built (a static method answering a string, G12 socket guess 7) is replaced by `before_order(intent, open_positions, facts)`; the node's call site changes (X1-H27 weakest link). R15's reason census: every brake text in this set needs a code in `_REASON_WORDS` (X6-06 is the source of the codes).

#### DP6. Levels, scope keys, cascade and drop-ins
Options: (a) level and scope key on every number and brake; tag scopes overlap and the strictest wins; down the levels as caps and states, up as events; cascade with `important` outer caps and `lock_lower_overrides`; drop-ins in order (X1-H34, H35, H36, H42; X3-H35; X4 restructure 2); (b) folder containment only (the Book as a folder).
- (a) P2 S3 E2 A3 F3 C2: "everything off for crypto" is one rule at one tag; CSS, VS Code, Nix, systemd checked; strictest-wins stacks caution (X1 collision 26, Dex in the roundtable).
- (b) P1 S2 E2 A2 F2 C1: cannot express intersections.
**Pick (a)** with the caution-stack guard: no tag-scope brake goes live before its shadow precision is read (X1-H12), and the cost-of-conservatism meter (DP19) names the tag that bound. Scope keys `class:`, `region:`, `currency:`, `underlying:`, `session:` join `instrument:` in the stand-down table and the kill switch (X1-H61). Every ledger `affects` edge is typed `down:cap`, `down:state` or `up:event` (feeds ledger v1).

#### DP7. Versions, records, rollout and the click
Options: (a) pinned profile versions with a migration map and identity labels (X1-H43), two records (logic in R across versions, money per profile version, X1-H44), shadow then canary then full with an analysis template and motion frozen while judging (X1-H45), plan before change and an effect-bound approval (X1-H46 = X7-H04 = X5-H10), offers never silent (X1-H47), contrast test against the incumbent (X5-H36); (b) every risk change is a new unit (today); (c) a bandit among approved versions (X1-H48, X2-H53).
- (a) P2 S3 E2 A3 F3 C2: the record survives the rip-out and every later swap; what runs is what he saw; Argo, Flagger, Kayenta, Terraform in production; the market canary needs a host change (a second deployment of one version, G12 says the one-deployment refusal wording is already gone).
- (b) P0 S3 E2 A0 F2 C0: the rip-out costs every unit its record.
- (c) P2 S2 E0 A1 F2 C2: wild; later.
**Pick (a).** Two records answer X1's question 2 without a ruling: the judge is size-blind, so a sizer swap keeps the logic record and starts a money record. Hand-off 35 (the version pull) is consistent: a sizer-only swap trades the same in R and pays the pull; an exit change moves trades and is a counted try (X5-H29). Hand-off 37: a behaviour check with no orders ends `inconclusive`, never `pass`. The identity labels `profile_version_change` and `profile_swap` are rows he edits.

#### DP8. Outside code and trust
Options: (a) trust ladder, minimum trust per slot, his signature on the pin before live, two adapters per slot, three faces, class coverage on entries, a quarantined raw-code hatch never alone at a scope (X1-H22 to H25, H68); (b) only `qml` and `human` blocks size live (X1 P5 b); (c) signature alone, no ladder (X1 P5 c).
- (a) P2 S3 E2 A2 F3 C2: keeps the door he asked for (D43); nothing untested sizes money; n8n community process checked; the check must live in the loader.
- (b) P1 S3 E2 A2 F1 C1: shuts his door.
- (c) P1 S2 E1 A3 F2 C1: least code, most clicks, no evidence gate.
**Pick (a).** Expressions (X1-H09) kept, compiled to blocks and run through the card like any block (closes X1 collision 30).

### B. Sizing

#### DP9. The baseline amount
Options: (a) horizon floor-odds sizer = day-sigma budget (X2-H01 = X2-H02, one formula when H = trade rate x days; proved in `working/flaw_arithmetic.py` section C), split by effective bets on residual stressed correlation (X0-02, X2-H28), with the cushion clip and reserve (X2-H07 = X3-H25); (b) risk-constrained Kelly from his floor tolerance (X2-H05); (c) own full size under a parent limit on co-loss (X2-H29, the lead's 1 Nov view); (d) his literal split, day risk over N (A1-088); (e) half Kelly; (f) the GitBook ladder (D/7 per seat).
- (a) P3 S3 E1 A3 F3 C3: zero floor touches in all twelve sim cases including shared gap days, 2.8x the literal split's growth at the believed edge, trades from day one with no edge input, every input a fact he can re-derive; the sim's "0 %" is partly structural (daily recompute from the cushion) and fat tails and intraday paths are untested.
- (b) P2 S2 E1 A2 F2 C3: spends exactly his floor tolerance; leans on a return model; kept as an alternative derivation block and a cross-check (D46).
- (c) P3 S1 E1 A2 F2 C2: fastest growth when the edge is as believed; 18.7 % floor touches at half the edge with ten correlated units (fixed 1 % row); survival at 1 only because the parent limit, if measured on stressed co-loss, binds late.
- (d) P1 S3 E1 A1 F2 C1: the sitting duck: 1/2.8 of (a)'s growth at equal safety.
- (e) P2 S0 E2 A1 F1 C2: blocked: 100 % floor touches at half the edge with ten units.
- (f) P2 S0 E1 A1 F2 C1: blocked: 88 to 97 % floor touches with ten seats.
**Pick (a); (b) as the swappable derivation and cross-check; (c)'s overbooking idea survives as cushion lending between units that trade at different hours (X2-H30).** H is defined as the unit's measured trade rate times the survival horizon in days, refreshed at anchors; the zero-edge closed form is the cache fallback. What the numbers lens must test (unresolved here): intraday paths at 40 trades a day with size held through the day, fat tails beyond the injected gaps, serially correlated results.

#### DP10. The edge's role
Options: (a) gate, level and ceiling only: low end positive after costs to trade (X0-04, X5-H44), the evidence bar sets the level (X5-H13), a cost-and-gap Kelly shrunk by t squared over one plus t squared caps the size (X2-H04); the edge dial (X2-H03) defaults to `zero` and moves only by a profile version or his click; (b) "twice the edge, twice the size" (the 1 Nov answer); (c) shrunk Kelly with a floor share (X0 P2 b); (d) the soft multiplier on by default (X5-H44's dial).
- (a) P2 S3 E2 A3 F3 C3: a weak uncorrelated edge gets its full risk share at its level from day one; a wrong point estimate cannot size a unit; DeMiguel and Chopra-Ziemba are strong; the gate's bound is undefined on a thin record (A14's "too safe" in another form, answered in DP15 by level 1 on paper costs).
- (b) P2 S1 E1 A1 F0 C1: he refused it (A24); mean errors do eleven times the damage of variance errors.
- (c) P2 S2 E1 A2 F2 C2: leans on the edge a little; the floor share has no derivation.
- (d) P2 S2 E1 A2 F2 C2: leans on the edge; off by default is enough.
**Pick (a).** Resolves X2 collision 1, X5 collision 5, X0 collision 2, SEEDS replies rows 6 and 8: the lead's "starting size from QMB's evidence" survives as the gate and the level, never as the amount. Inverse volatility (X0-04, X2-H32) is the within-level allocator only for units without a tight stop (swing, X2-H09); stop-sized units are already normalised by R.

#### DP11. Costs into size
Options: (a) the cost triple: denominator (stop plus round trip plus stressed slippage), the ceiling in R, the admission gate at a multiple of stressed cost, per instrument, hour, session and world (X2-H39, X0-14, X0-17); two per-instrument-hour tables on the instrument risk record (X0-37 = X1-H18); session multipliers and premium-window lifts deleted (X2-H40); carry and funding in the hold decision (X2-H41 = X0-33); (b) cost as a gate only; (c) cost through the edge only; (d) for a missing cell: refuse (X0-37) against a stressed class default that decays toward measured (X2-H39).
- (a) P3 S3 E2 A3 F3 C3: a scalper's size follows net edge by hour; a negative net edge is never multiplied by breadth; the BTC cost filter and the NBER hour studies are strong; no fills exist yet so every cell starts synthetic.
- (b) P1 S2 E2 A2 F2 C1: over-sizes in costly hours.
- (c) P1 S2 E1 A1 F1 C1: hides cost from the receipt (G7's warning).
**Pick (a). The missing-cell collision (X2 collision 25) resolves by world:** paper trades on the stressed class default (twice the posted typical spread, labelled uncalibrated, decaying toward measured); live at level 1 needs at least N measured fills in the cell from the paper twin or demo (X2-H50, X4 P9 order). Hand-offs 15 and 16: the placeholder sizer is replaced by money at the stop from the broker tick value with live conversion and a freshness limit (X4-42); costs and the edge band reach the sizer through the widened inputs (DP12). Hand-off 22: R is the planned loss at the disaster stop, gross; `net_r` is R minus costs in R on every row; brakes, the money ledger and the proof battery read net; drift attribution keeps gross and cost streams apart (X4-84); `r_after_costs` is renamed `net_r` and `trade_r` stays gross.

#### DP12. Which equity the sizer and the brakes read
Options: (a) asymmetric basis: committed cushion for size, marked equity for brakes, realised profit for accelerators, worst case at the stops for the clip (X2-H44); (b) one series, marked; (c) one series, realised balance.
- (a) P2 S3 E2 A2 F3 C2: no pressing on open profit; the fourth position sizes from what the first three left; prop practice; cTrader equity is read once at sign-in today (G12).
- (b) P2 S2 E2 A2 F2 C1: presses on open profit.
- (c) P1 S1 E2 A2 F2 C1: ignores open losses; over-sizes the next trade.
**Pick (a).** Until marked equity exists on the node (no PR plans it, G12), the sizer basis is balance minus open risk at the stops minus pending orders' risk, and brakes read realised plus open risk at the stops; the receipt says `basis:unmarked`. Marked equity is this session's socket input (G12 item 3) and the architects must put it in the guard's facts. The sizer's inputs widen to X1-H58's list and its receipt becomes real (hand-off 17).

#### DP13. Minimum lots, feasibility and lumpy classes
Options: (a) feasibility-first admission per unit x instrument x broker and a per-class verdict on screen (X2-H45 = X0-45, X0-17), round down and skip below one step (built), whole-contract ladders for lumpy classes (X2-H49), cushion lending between units (X2-H30); (b) lot dither carrying the residue (X2-H46); (c) raise the class's share until its minimum fits (X0 P6 b); (d) fewer, larger units.
- (a) P2 S3 E2 A3 F3 C2: no silent oversize; the class map tells him what the seed can trade; `working/flaw_arithmetic.py` section B shows ten correlated units need a cushion near 190 times a minimum-lot risk, so the split and the lot step collide early and this gate must bind first.
- (b) P2 S1 E0 A1 F1 C1: single trades up to 1.5x plan; violates "never round up"; dropped.
- (c) P1 S1 E1 A1 F0 C1: concentrates the book in the coarsest class; dropped.
- (d) P1 S2 E1 A1 F1 C1: against his C1; kept only as what the feasibility map will show at a small cushion.
**Pick (a).** The lender in (a) is BestEffort budget recalled by any brake (X2-H30's QoS classes).

#### DP14. Accelerators and the cushion pair
Options: (a) one-ledger cushion pair on one declared scope: brake half on from day one, accelerator half off until its proof card passes (X2-H10, X2-H20, X0-05); book-level house money with an event window as the default home (X2-H11); per-scope anchor clocks (X2-H12); tier ladder with dwell and same-day step-down (X2-H18); persistence press after the unit's own block test (X2-H19); pyramiding for trend units with falling risk under one stop (X2-H21); calm-volatility scaling cut side only unless risk assets (X2-H22); AIMD as a red-zone survival mode only (X2-H26 = X3-H07); raise permission gate (X2-H24 = X1-H13); the nomogram block as the generic graded step (X2-H25); two-speed sizer, money fast and edge slow (X2-H27); (b) the April nine-multiplier chain; (c) automatic raises above baseline by rule (X2 collision 12).
- (a) P2 S3 E1 A2 F3 C2: R9's script gives +37 to +42 % growth per risk under regimes and nothing on independent trades, which is honest; every raise is funded from realised profit or proof and blocked by any active brake; `flaw_arithmetic.py` section D shows the accelerator half cannot drive into the brake on the same ledger.
- (b) P1 S1 E1 A0 F1 C0: multipliers did each other's jobs; one cap bound always.
- (c) P3 S2 E0 A1 F1 C2: no accelerator beats a constant on independent trades (R9); his "brakes first".
**Pick (a).** Where house money lives: book ledger with an event window for the accelerator half, unit ledger for the brake half (Q5 carries it to him with that default). Capacity probing (X2-H23, X0-12), EWOC and conservative-UCB steps (X2-H16, H17), the swarm split (X2-H38) and the book thermostat (X2-H55) are kept for later. The X2 collision 21 warning stands and goes to him in plain words: house money moves risk around; it adds growth only where results persist.

#### DP15. Levels and the ramp
Options: (a) one ladder: levels are fractions of the derived baseline (X2-H13), level 1 is the smallest feasible live size (X2-H45), cohorts on BOIN bars are the speed limit and the evidence bar per level is the ceiling (X5-H13, X5-H14), slow start doubles until the first warning (X2-H14, X0-09), a memory ceiling after a trip (X2-H15 = X3-H17 = X1-H11), any world switch resets to level 1 and marks costs uncalibrated (X2-H50 = X4-30 = X5-H28), slow units climb on pooled family cohorts (X5-H23 = X3-H23), a ring-fenced exploration budget for all level-1 units (X5-H48); (b) his calendar ramp ("Kelly over about a month"); (c) full size at promotion.
- (a) P2 S3 E2 A3 F3 C3: `flaw_arithmetic.py` section G shows the cohort ladder finishes long before proof, so without the e-bar ceiling a unit climbs to full size while unproved; with both, a thin edge stays at level 1 earning a little, which is his "squeeze some money out of a weak edge"; a 2-a-day unit's ramp is about 50 days, which is where "too safe" (A14, C13) is still true, hence the pooled cohorts.
- (b) P1 S2 E1 A2 F2 C1: ignores evidence speed.
- (c) P3 S1 E1 A0 F1 C1: ten unproved units at full size touch the floor in 68 % of runs at no edge (STATE 10).
**Pick (a).** Resolves X5 collision 4, X2 collision 5 (partly: slow units still wait, by design), X4 collision 12 and X5 collision 2 together with Q3 (live at level 1 before proof, with the packet saying so).

#### DP16. Growth across 24 hours, sweeps, re-seeds
Options: (a) a gain-lock ratchet at the BMS with the floor rising by a share of each new high, sweeps only at the BMS above the high-water mark, never on units, a share-of-equity-per-R cap (X2-H56, X4-70), per-scope anchor clocks (X2-H12 = X3-H74 = X0-27), banker acts (sweep, deposit, re-seed) journalled with every anchor re-derived before the next order and verdicts untouched (X4-72, X4-73); (b) the 2.5x cycle cap and sweep return (A1-075); (c) pure compounding with no cap.
- (a) P3 S3 E2 A2 F3 C2: no cliff, no idle reserve, units keep the cushion their brakes read; TIPP and CPPI theory, fund high-water marks live; the share is his money choice.
- (b) P2 S2 E1 A1 F2 C1: a cliff that collides with 24-hour trading (B5).
- (c) P3 S1 E2 A1 F2 C1: the risk share per R climbs toward 14 % with no cap (G6).
**Pick (a).** Answers C12 and B10: the sweep cap returns as a smooth ratchet at the BMS. The next day after a budget hit starts by rule (DP20). Priced reinstatement (X2-H57) kept for later.

### C. Brakes, restores, isolation, exits

#### DP17. The unit's fast brake
Options: (a) own-percentile money breaker over a window of at least ten trades (X3-H01 = X0-16), graded: REDUCING at own p10, BENCHED at own p1 (X3-H02), loss points at own p99 beside it (X3-H03), two ledgers (X3-H04 = X6-05), a dollar clamp from his budget on the level, the day-boundary contract with persisted counters and a minimum bench rest (X3-H74 = X4-29), the choke budget (X3-H65); (b) the old "2 full stops in a day"; (c) a fixed "3 in a row"; (d) his "about three or a pattern" scaled to the unit's own p99 run length, halve not bench (X3-H05), enforced only after a block-persistence test (X3-H06); (e) AIMD as the default brake (X3-H07 as default).
- (a) P3 S3 E1 A3 F3 C3: keeps 97 to 100 % of a healthy unit's R at 2 to 40 trades a day in X3's SIM at a 1 % fire rate, adds +26R of timing at 40 a day in bad spells, and the ladder cut the 95th-percentile drawdown; the card's tail is only as honest as the holdout.
- (b) P0 S2 E1 A0 F1 C0: keeps 18 to 65 % of healthy R; fires every day at 40 trades.
- (c) P1 S2 E1 A1 F1 C0: `flaw_arithmetic.py` section F: fires on 41 % of days at 10 trades, 91 % at 40.
- (d) P2 S2 E1 A2 F3 C2: his picture kept; +20R timing in bad spells where losses cluster; costs 16 to 26 % on healthy days when they do not; the scaled form was not simulated.
- (e) P1 S3 E1 A1 F1 C2: chokes as a default (32 to 84 % of R kept).
**Pick (a) everywhere, with (d) shipped in shadow as the default count brake and enforced per unit only after X3-H06's persistence test passes; (e) only in the red zone.** One shape for every style: the window in trades gives ORB a five-day window and a scalper a one-day one. The circuit breaker keeps its name (A26): fast half here, slow half in DP18. Day one with no record: the percentile resolves down the ladder: own live record, then the card's block bootstrap (X3-H09), then the family's pooled cards, then the class default from the harness's dry chassis (X4-90), then refuse live and allow paper. R9's count-form reverse house money retires into the event ledger (X2 restructure 4).

#### DP18. The improved circuit breaker's decay role
Options: (a) two-speed breaker: the fast trip plus a fire-density sentinel in Basel zones recomputed for the unit's own p0 (X3-H08 = X5-H19 = X7-H31), the expected fire band on the card (X3-H09), context-tagged density (X3-H10 = X6-10), two-key demotion where either key halves and both send to paper (X3-H11); (b) density alone; (c) the shipped nightly 20-trade decay check.
- (a) P2 S3 E1 A3 F3 C3: the trade CUSUM caught a dead edge in 92 to 99.5 % of runs at 4 to 40 trades a day, density in 25 to 99.5 %, so two keys; his "caught alpha decay" made honest with a baseline it never had.
- (b) P1 S2 E1 A2 F2 C2: too slow alone (median 36 to 93 days).
- (c) P0 S1 E1 A1 F1 C0: the count flaw; ignores the card; tighten-only cards nobody applies.
**Pick (a).** (c) is replaced (X3 restructure 3, X5 restructure 1).

#### DP19. Proof that a brake works, and what it costs
Options: (a) the random-control certificate before enforcement (X3-H13), shadow-first with an enforcing ramp (X3-H14 = X1-H12 = X6-32), the scorecard: precision, recall, detection time, reset time, trip tax (X3-H12 = X6-21), the cost-of-conservatism meter (X0-52 = X3-H64 = X6-22), the choke budget (X3-H65), the dry chassis as the null (X0-50 = X1-H73 = X5-H08 parts 1 and 2 = X4-90 rule 5), one brake registry row as a compile requirement (X3-H58 = X1-H14); (b) brakes stake testing wealth and retire themselves (X3-H67).
- (a) P3 S3 E2 A3 F3 C3: the one fair test in the corpus (MQL5 23482); any brake looks good on a losing strategy because it trades less (R5 trap 1); makes M33 a number on screen.
- (b) P2 S2 E0 A2 F2 C2: wild; later.
**Pick (a).** The live random-entry twin (X5-H21 lane 2, X1-H73's live half) is kept for later: the offline dry chassis gives the same null without three lanes per unit.

#### DP20. Restores, benches and what waits for him
Options: (a) half-open probe ladder with a memory ceiling, retry-then-lockout, probes on the paper twin where a live probe is impossible, restores never above baseline, earned restore after a slow-lane demotion (X3-H15 to H18 = X1-H11 = X2-H15 = X7-H05); BENCHED and REDUCING clear by rule; HALTED, the kill switch, promotion and lockouts wait for his hand; (b) every risk stop waits for his click (the unit build's rule, G10 §1.6); (c) calendar reset at the day boundary (April and July).
- (a) P3 S3 E2 A3 F2 C2: ends benches on evidence, not at midnight or at his next look; reversible steps kept 902R of 950R after a bad week where permanent demotion kept 614R; the anti-sitting-duck half of every brake; collides with the unit build's rule, which is his to restate.
- (b) P0 S3 E1 A1 F3 C0: the book goes dark on the first routine bench while he sleeps or travels (X4-74).
- (c) P2 S1 E1 A2 F1 C1: the day-boundary exploit (X4-29).
**Pick (a); it needs his ruling (Q1).** Default the work proceeds on: ruling 2 restated by direction (X7 restructure 1): automatic changes are monotone toward less risk and always a declared rule of a unit, cluster or portfolio; routine benches and reductions restore by rule within a retry budget; raises above baseline are his, once per rule (pre-authorised ladder with an expiry) or per step (card).

#### DP21. Cluster and methodology brakes
Options: (a) the hours-clause event ledger (X3-H20 = X4-91 = X0-10), chorus K of N on measured correlation (X3-H21 = X6-34), the burn-rate permit over two windows (X3-H22 = X6-15 = X1-H41 = X5-H25), the methodology pooled CUSUM (X3-H23 = X5-H23 = X4-04); (b) per-unit brakes only.
- (a) P2 S3 E2 A3 F3 C2: five correlated stops read as one event, not five strikes; a logic fading everywhere is caught in days; insurance and SRE practice; the window length per driver has no derivation.
- (b) P1 S1 E2 A2 F2 C1: cannot see losing together (his C32).
**Pick (a).** Window length: state-based (opens on the first tagged loss, closes when the driver's tells are back in band) with the class default as the maximum (X4 P1 option c). A unit-level brake reads the money ledger in full during a book-level event; only count and density statistics above the unit dedupe (X4 collision 4).

#### DP22. Portfolio and account brakes, clamps
Options: (a) BMS breaker on stacked evidence raising a stand-down at `all` with a target fire rate written in advance (X3-H24 = X4-14), the cushion clip above the buffer with a worst move per class and an N-1 or probable-maximum-loss reserve (X3-H25 = X2-H07), the pod-style step ladder on a unit's capital share widening with time in service (X3-H26 = X3-H56), priority shedding by declared class (X3-H27 = X1-H41 = X2-H30), the order-boundary worst-case veto with gap and halt allowance, order-rate clamp, margin headroom, stop side, size sanity band (X3-H75 = X4-42, 53, 54, 67, 68), margin de-gross by stressed contribution before the broker's close-out (X4-87); (b) the 10/5/3 bands or the 3-5-7 rule as numbers.
- (a) P2 S3 E2 A3 F3 C2: the floor is touched only by a gap beyond the class allowance; the broker's close-out is never reached; Hsieh's lemma with proofs; the worst-step table is X4's and unset.
- (b) P1 S2 E0 A1 F1 C0: no derivation older than this session; his own word "circumstantial".
**Pick (a).** The daily ladders of X0-28 fold in as the BMS and cluster burn-rate tiers derived from the buffer and the summed unit limits less co-loss; the old bands stay in `seen_values` with no weight. Hand-off 26: the kill line is the cushion clip on marked equity; its verb is no new entries and reduce until above the buffer; flatten only at RED or BLACK or by his hand; the floor is his user row.

#### DP23. Isolation, the MIS and the weekend
Options: (a) one protocol: scope keys (X3-H35 = X1-H28 = X4-RP2), two-tell bucket isolation with calendar-aware baselines (X3-H28 = X0-07 = X0-43 = X4-94), SQS K of N class caution (X3-H29), peer ejection with a capped share (X3-H30), region shift without rotation (X3-H32), lifecycle with TTL, staged resume, retrip back-off, aftershock lockout (X3-H33 = X4-12, 37), unknown is not calm and placement fails closed inside an isolation (X3-H36 = X4-82), agent slow isolation by card with evidence and TTL (X3-H34 = X7-H21 = X4-13), the weekend and single-class budget scaler (X3-H37 = X0-40 = X2-H36 = X4-24), the macro governor cut-only live (X0-06 = X2-H62 = X0-42); (b) the kill switch alone (C28 as remembered).
- (a) P2 S3 E1 A2 F3 C2: a Tokyo event switches off JPY, not the book; the reopen is staged so it does not make its own shock; no fund source for switching a class off by rule; the two-tell thresholds are untested intraday and need the precision record.
- (b) P1 S2 E2 A2 F2 C0: all or nothing; by his hand only.
**Pick (a).** The MIS collision (A3-184 "never switches" against A3-115): the guard owns the switch as a stand-down at scope; the board only carries the word; placement (a widen) stays the MIS's and is flagged, not designed (X0 restructure 6). Whether a confirmed isolation applies without his click is part of Q1; the default: `no_new_entries` mode applies by rule with a TTL; `flatten` only through the BMS buffer trigger or his hand. The X0 collision 11 (weekend scale against crypto as the spine): the budget scales with open breadth; crypto carries the book at its weekday share, and the weekend volatility reading is a Monday caution for the others (X0-54's parts survive; its "spine" framing is dropped).

#### DP24. News
Options: (a) measured impact per release and instrument with driver tags beyond currency, windows block entries only, re-entry on spreads and depth, a surprise backstop, a stale calendar fails closed, blocked minutes reported (X3-H31 = X0-39 = X4-95 = X7-H48); (b) colour-level windows.
- (a) P3 S3 E2 A3 F3 C2: narrower windows give scalpers hours back; fewer missed releases on gold, indices and crypto; the E-mini liquidity study; impact drifts and must be re-measured.
- (b) P1 S2 E1 A2 F1 C0: swallows the day (X4-18).
**Pick (a).** The kill switch keeps the hard kill (C28); the news window is a node schedule derived from measurement. **This session claims `qmn/data/news_calendar.py` and `qmn/protection/windows.py` as the seed of this pick before deletion-4 sweeps them** (G12 section 4 and item 8).

#### DP25. SQS placement (hand-off 27)
Options: (a) SQS as a node-side entry gate inside the guard package, its baseline producer moved with it, its state also a sensor feeding class caution, the bad-day classifier, the cost lane and the restore gate (X3-H63 = X3-H29 = X0-18), with a graded shrink in front of the hard block (X2-H42); (b) one line in `Runtime.guard` as the plan guessed (G12 socket guess 4); (c) SQS inside the MIS as a pack.
- (a) P2 S3 E2 A3 F3 C2: one sensor, many uses; the gate never blocks exits; the hysteresis rule text is saved in G12 section 2.
- (b) P1 S3 E2 A2 F2 C1: the same gate with no sensor role; acceptable as the first slice of (a).
- (c) P1 S2 E1 A1 F1 C1: the board fails open; an entry gate cannot sit behind a feed that fails open.
**Pick (a) with (b) as its first slice.** The eight named SQS settings with no values become ledger rows with derivations (class thresholds from the spread histogram's own percentiles). **This session claims `sqs_baseline_producer.py`, the `labelers.py` rule text and `qmn/replay/port.py`'s SQS rule before C-20.**

#### DP26. Exits and stops: the socket and the fourteen hand-offs
Options: (a) an exit stack: safety exits (disaster stop at the venue on every live order, forced flat, kill close) and strategy exits (thesis fast invalidation, a price backstop from the winners' adverse excursion, time at the edge-ratio peak, target, trail or breakeven only where the unit's own persistence and a two-arm test allow), the safest wins by a declared rank, exits never blocked by contract test, stops tighten only (X3-H38 to H47 = X0-15, X0-24, X0-32 = X1-H60 = X5-H29); per-style exit families as defaults (X3-H43) with the stopping-premium test as the override (X0 P4 option c); (b) one policy for every style (April); (c) by style name only.
- (a) P3 S3 E1 A3 F3 C2: an honest cut keeps most winners and shrinks the average loss; `flaw_arithmetic.py` section A shows the cut is what makes a 55 % 1:1 scalper clear a 0.16R cost; stops help only under momentum (Kaminski-Lo); no paper tests fractional cuts after costs, so every cut rule is a counted two-arm trial.
- (b) P1 S2 E1 A1 F1 C0: April's flaw.
- (c) P2 S2 E1 A2 F2 C1: a mean-reverting intraday unit gets a breakeven that counts missed rebounds.
**Pick (a).** The G12 exit hand-offs, answered:
1. The socket: per-bar exits read position facts (`side`, `entry`, `stop`, `quantity`, `bars_held`, `mae_r`, `mfe_r`, `targets`) and answer an exit answer type beyond `Signal`, mapped to `close_full`, `close_partial`, `amend_protection` (socket guess 1 accepted). The exit set stays slot-per-use in the compiler (guess 2 accepted); the host applies the rank. Step 2 (about 60 lines) ships before any exit of this set; step 3 (trails, partials, stop moves) ships with the signed level.
2. The six refused exits (`unrealised-profit-cap`, `roi-table-exit`, `peak-holdings-giveback-exit`, `offset-gated-trailing-stop`, `stepped-profit-stop`, `profit-fraction-trailing-stop`): stay refused until step 2; then they are catalogue entries in shadow, each a counted two-arm trial per instrument; none ships as a preset default.
3. Stop past entry: in scope, for momentum families only (ORB, intraday trend, swing trend), tighten-only. The convention to pin: the node sends an absolute stop level; "distance" is derived per side; `abs(entry - new_stop)` goes. R21's block stays until step 3 lands; the node build dispatches the fix with step 3. Not needed for the first demo (the dummy has no trail).
4. Widening: never. The placeholder swing stop that can widen is replaced by the family's disaster stop plus the thesis exit.
5. Partial closes: the node's way stands (a remainder below the minimum lot closes with the partial). R stays the original planned loss; realised R is piecewise on partial rows; QMB's differing fill is a validity-stamp field (X5-H02), not a QMB change.
6. Targets: node-closed stands.
7. A unit with no price stop: allowed only as no *working* stop; the disaster stop at the venue is always sent (X4-45); its R comes from the tail-loss budget of its realised loss distribution (X3-H44 = X2-H08).
8. A moved number and open trades: `applies_to_open_positions` default false; REDUCING amends only tighten; sizer numbers never retro-apply.
9. Two exits on one bar: the rank (closes beat amends; safety beats strategy; the tighter stop wins).
10. Position facts: the list in 1.
11. A long-wicked bar's stop above the close: refused at send by the order-boundary veto (stop on the loss side at send time or no order).
12. `timer()` long-only: fixed with step 2.
13. A lost stop returns at the latest accepted amend row, not the send row; the guard's timed re-check of every open position reads that row.
14. Exits read the side's price (ask for shorts); the record carries both.

Breakeven (M15) is off by default and turns on per unit only after the two-arm test (X3-H41); his memory of the dynamic SL/TP survives as the intraday trend family's trail (X0-24).

### D. Drift and verification

#### DP27. Bad day or broken edge
Options: (a) three speeds in one monitor with a money brake apart: inputs first in days (X3-H51 = X5-H09), warnings in weeks that step one level down reversibly (CUSUM or e-detector; X3-H49 = X5-H15 = X7-H22), confirmation in hundreds of trades against a minimum viable edge that moves a unit to paper (X5-H15 speed 3 = X3-H49 lane 3), three zones at planned looks (X3-H48 = X5-H24), the bad-day sentence and classifier (X3-H50 = X6-28 = X6-29), one lifetime false-demotion budget at the portfolio (X3-H52 = X5-H16 = X6-25), re-promotion as a funded episode with his click (X3-H53 = X5-H26), regime-conditional expectations (X3-H54 = X5-H18), the upside alarm (X3-H55 = X5-H22), worry lines by style (X3-H56); (b) the nightly 20-trade check; (c) planned looks only.
- (a) P3 S3 E1 A3 F3 C3: a healthy unit was demoted by statistics in none of 4,000 trades; a dead unit stepped down in a median 190 trades; nothing acts on one day except money; his A25 in formula form.
- (b) P0 S1 E1 A1 F1 C0: replaced.
- (c) P1 S2 E2 A2 F2 C1: undecided at 1,000 trades in 46 % of half-edge plans.
**Pick (a).** Ownership (X5 collision 15, X7 collision 18): the guard owns every size step; speed 1 is X3's, speeds 2 and 3 are X5's, and a warning is a transition to REDUCING with cause `drift_warning`. Hand-off 34 (`too_thin`): `min_trades=100` is replaced by `verification_trades_needed` at the band's low end with an incubation cap (X5-H06); a dead idea leaves a `closed-thin` row, never no row. Hand-off 36: "rules still hold on a real run" is answered by the preflight plus the replay-match and input strip, never claimed by a stack list.

#### DP28. The verification path and the click
Options: (a) the counted birth and novelty check (X5-H01), look-ahead blocked in the tools (X5-H02), the battery on net returns with a friction floor (X5-H03), the band from four shrinkages (X5-H04), the honest counts (X5-H05), the plan with a correlation column and an event window (X5-H06), the independent challenger (X5-H07), the nulls (X5-H08), the machine check against a twin in a week (X5-H09), the bound click (X5-H10 = X1-H46 = X7-H04 = X7-H29), two vetoes logged apart (X5-H11), the funded promotion ledger (X5-H12), risk-tiered proof (X5-H13), the evidence ledger with stage tags (X5-H37), one cost ledger reconciled to zero (X5-H38), the passport (X5-H39), the template per type (X5-H40), the node emitting verification state (X5-H41), calibrated thresholds (X5-H42), calendar looks for rare traders (X5-H43), the exploration budget (X5-H48), the live canary across markets (X5-H46 = X1-H45); (b) the paper judge's "30 trades and 28 days"; (c) QMB proves fully before any live money (proof in paper only).
- (a) P2 S3 E2 A3 F3 C3: strong edges cross in a few hundred trades, the family budget pushes agents toward fewer, better candidates, the one gate with a proven null rate under adaptive births; QMX's scale and clipping are untested on scalper streams.
- (b) P1 S2 E1 A1 F2 C0: proves the machine, not the edge, on a calendar.
- (c) P1 S3 E2 A1 F1 C1: paper for months for every unit; against "7 days doable".
**Pick (a); Q3 carries the one piece that is his (live at level 1 before proof).** The governed pipeline (X5-H35) and family staking (X5-H34) are the agent department's and the wild pile respectively.

#### DP29. The scenario harness
Options: (a) the harness as a nightly job: every scenario against every profile version with QMX's own brakes inside the path, conditional fill for unstressed factors, accumulation per shared dependency, three cases, controls beside every claim, the engine backtesting itself (X4-90), the event window (91), same-bet caps sized to a tail gap (92), effective units on screen (93), the isolation lifecycle (94), sectoring (95), scenarios as a Library kind (96), the scorecard with survival gates (97), reverse stress (98); (b) the lead's bare sims; (c) the interactive agent-based bench (X4-99).
- (a) P3 S3 E1 A3 F3 C2: the only machine that produces the survival number the rubric needs per candidate; it runs the brakes, not a model of them; the engine does not exist.
- (b) P1 S1 E1 A2 F1 C0: no brakes, no exposure, no drawdown rules, which is his objection.
- (c) P2 S2 E1 A1 F2 C1: wild; later.
**Pick (a).** Engine order: the guard module imported into the harness once it exists; a light ledger-driven harness until then with a conformance test on one tape (X4 P5). The scenario record is data the harness reads, not an agent report (X4 collision 14). All 89 scenarios enter the standing set: solid ones as the mandatory block, plausible ones as the own block.

### E. Observability and agents

#### DP30. RiskState, the words, the rows
Options: (a) one fold, many readers (X6-01 = X1-H49 = X4 restructure 6), the equity triple and drawdown by kind (X6-02), the decision trail with three weights (X6-03 = X1-H76), trade row v2 with the mechanism apart from the outcome (X6-04 = X3-H45 = X1-H59 = X5-H37), closed reason codes at source (X6-06), every brake as a live meter (X6-07), motion receipts (X6-08), requested, enforced, observed (X6-09), context tags (X6-10), the six words and UNKNOWN (X6-11), the safety display (X6-13), fact flow with authority and age (X6-37), the ledger generates the alerts and bars (X6-41), the passport strip (X6-27 = X5-H39), cost cells (X6-30 = X5-H38), markout (X6-31), exposure board (X6-33), the stress gauge (X6-35), Lab parity (X6-39), observability observes itself (X6-40), the morning card (X6-43 = X7-H46); (b) the node's health-only status.
- (a) P2 S3 E2 A3 F3 C3: brakes act on the facts the UI shows; a stale green is impossible; "right or wrong" becomes computable; no shipped brake has the attributes yet.
- (b) P0 S1 E2 A1 F1 C0: reports health, not risk.
**Pick (a).** One drift vocabulary (X6 restructure 7): green, yellow, red, thin, UNKNOWN, with orange as the ladder's sub-state. QMB's text-to-code map is deleted after callers migrate.

#### DP31. Alerts, pages and his attention
Options: (a) four tiers (X6-14), frequency-fair burn tiers in expected trades (X6-15 = X3-H22), the incident funnel (X6-16 = X7-H17), the wake contract for one operator (X6-17), distance bars with pickups (X6-18), the watch window at opens (X6-19), exit capacity and locked heat (X6-20), one attention budget and cards ranked by money both ways (X7-H15 = X7-H20), card-type graduation (X7-H16), the dead-man rule and absence policy (X4-74); (b) page on every brake; (c) never page.
- (a) P2 S3 E2 A3 F3 C2: he sleeps and trusts the system enough to run around the clock; the few true emergencies wake him with an action and a deadline; ntfy has no delivery ack and a second channel is not built.
- (b) P0 S2 E2 A0 F1 C0: alarm fatigue mutes everything.
- (c) P1 S1 E1 A2 F1 C0: a missing stop waits for hours.
**Pick (a).** Operator attention telemetry (X6-26) later; money pages are never demoted.

#### DP32. The agents' door
Options: (a) three surfaces: read, propose, run (X7-H01 = X1-H49, H50, H53 = X6-38); a direction on every operation (X7-H02); agent evidence as a fact the unit's own rule reads, cut only, expiring, missing means no change (X7-H03 = X2-H58 = X5-H31 = X3-H60); effect-bound cards (DP7); feasible-by-construction proposals (X7-H07); the LLM-free fast loop with an incident tap (X7-H08); one search ledger (X7-H09); the matched random de-risker per agent and class (X7-H11); sealed scenarios (X7-H12); rationale-blind admission with a separate challenger (X7-H13); point-in-time inputs (X7-H14); the autonomy ladder (X7-H18); the get-even guard (X7-H19 = X3-H69 = X6-42); the jobs (X7-H21 to H31); the sitting-duck advocate, accelerator scout, breadth proposer, slot rebalancer (X7-H32 to H35); the risk mini app with an MCP server (X7-H36 = X1-H29); the Lab as a tenant (X7-H37 = X1-H33 = X2-H59); the shepherd-ready call contract (X7-H38 = X1-H55); evidence contracts per kind (X7-H39); the kill escalation card (X7-H43); the class roster and event mapper (X7-H45, H48); the provenance walker (X7-H47 = X1-H54); the protected core (X5-H32 = X1-H52); (b) cards only; (c) agents in the fast lane.
- (a) P2 S3 E2 A3 F3 C2: agent evidence reaches the risk layer in minutes without an agent ever sending an order; the Steward boundary and the I-HITL test are the evidence; no paper tests a de-risk-only channel end to end.
- (b) P1 S3 E2 A2 F2 C1: cuts arrive hours late.
- (c) P1 S0 E1 A0 F0 C1: blocked (G2-5).
**Pick (a).** Testing wealth per agent (X7-H10), the prediction market (H40), ghost tracks (H41), the self-proposing ledger (H42), governed self-evolution (H44) and the agent-trader unit type (H49) are later; H49's type name is reserved so the schema does not need rework (his D44 parked it). QMA flags stay flags: the direction field on catalog rows and `admits`, the evidence relay, the app lander, agent profile storage. The three fail modes (board open, isolation closed, evidence neutral) are shown together on the preflight (X7 collision 6).

#### DP33. Agent orders on the node's own demo account (G12 section 5)
Options: (a) the guard's reconcile attributes positions no unit holds on the bound account to a `foreign` scope, counts their margin and open risk in the account-level numbers (margin headroom, the cushion clip, RiskState) and never in a unit's, RED still leaves them alone, and the harness recommends a separate demo account for agents (X7 P14); (b) ignore them.
- (a) P1 S3 E1 A3 F3 C1: a position an agent opens still moves the balance a risk rule reads; naming it is cheap.
- (b) P1 S1 E1 A2 F1 C0: a hidden exposure line.
**Pick (a).** QMA flag for the build session: the attribution module gains a `foreign` claim; nothing else.

#### DP34. Grid, martingale and averaging families (hand-off 33)
Options: (a) refused as sizers by the martingale firewall and the hidden-ruin audit (X2-H60 = X5-H22); averaging in survives only as pyramiding with falling risk under one stop for trend units (X2-H21); dictionary entries carry their known failure (X1-H68); (b) allowed with caps.
- (a) P2 S3 E2 A3 F3 C2: catches martingale-shaped sizing before it ruins; no growth lost that a tested accelerator would not give.
- (b) P2 S0 E1 A1 F1 C1: blocked.
**Pick (a).**

---

## 2. Collisions resolved by the picks

| Collision (layer) | Resolution |
|---|---|
| X0-1, SEEDS replies 6 and 8: 1/N against full size against effective bets | DP9: effective bets split a survival total; full size per unit is not a baseline; the literal split is the sitting duck |
| X0-3, X3-1, X3-2, X4-1: his "about three" and the old breaker against frequency | DP17: money at own percentile is the trip; "about three" is the own-p99 run length in shadow; the name circuit breaker stays |
| X0-4, X0 Q1: type against cell against dial | DP1 |
| X0-5, X3-10, X4-8, X7-C4: the MIS never switches a unit against isolation on the board | DP23: the guard switches, the board carries, placement is flagged |
| X0-6: brakes first against one rule that is both | DP14: the brake half is on from day one, the accelerator half waits for its card |
| X0-7: breakeven by profit against breakeven when the forecast changes | DP26: off by default, on per unit after the two-arm test |
| X0-9: R fixed at entry (B9 not accepted) | DP11: 1R is the planned loss at the disaster stop; realised loss varies through the cut; `net_r` beside it. His reservation stands as a vocabulary note, not a design change |
| X0-11: weekend budget scale against crypto as the spine | DP23 |
| X0-12, X2-C01, X5-C5: the gate's undefined bound on a thin record ("too safe") | DP10 and DP15: level 1 on paper costs opens the gate per world; the edge touches only gate, level, ceiling |
| X0-14, B13: a three-level daily ladder he called circumstantial | DP22: ladders become burn-rate tiers derived from the buffer and co-loss; no standing numbers |
| X0-15, X2-C05, C13: a pilot tier is "$20 a trade" in another form | DP15: slow start doubles until the first warning; slow units climb on pooled cohorts |
| X0-16, X2-C10, X5-C3, X3-8: the shipped sizer's four inputs and the compiler's refusals | DP11, DP12, DP3: widened inputs, derivations move sizer-bound numbers, compiler format bump |
| X1-1: a profile document against "the unit stands alone" | DP2: embedded at compile |
| X1-2, X1-25: self-configuring at the unit against pooled priors | DP3: the unit owns the rung order; borrowed values are labelled |
| X1-3, X1-22: a sizer swap and what a counted try means | DP7: two records; no ruling needed |
| X1-6, X3-11: HALTED must run exits | DP5: exits never blocked is a contract test on every state |
| X1-9, X4-3, X7-C6: fail closed against the board's fail open | DP23 and DP32: three fail modes declared per feed and shown together; isolation closed, board open, evidence neutral |
| X1-11, X1 P15, X3-18, X6-1: two state machines on the node | DP5: two tables, both shown; brakes never set a kill level |
| X1-19, X7-C5, X7-C7: tighten-only automation against the sitting duck | DP20 and Q1: restores by rule within a retry budget; raises above baseline are his once per rule |
| X1-23, X7-C10: three layers describe the proposal door | DP32: one door, X7's shape, X1's tool rows, X5's kinds |
| X2-C02, X3-27: breadth against the minimum lot | DP13: feasibility binds first; cushion lending; `flaw_arithmetic.py` section B |
| X2-C03, X2-C04: fixed against trailing anchor; house money's home | DP14 and Q5 |
| X2-C12, X3-14: automatic raises above baseline | DP14 and DP20: none without his rule; any brake blocks every raise |
| X2-C13: full size under a parent against breadth-to-budget | DP9 |
| X2-C17, X5-C12, X3-16: two planning edges; FI cuts counted differently by brakes and verification | DP10 (one band, four low ends), DP11 (one row records R, `net_r`, mechanism; brakes read the money ledger, verification reads `net_r`; the ledger records both rules) |
| X2-C19: calm scaling on stop-sized units | DP14: cut side only, risk assets only, never on R-normalised scalpers |
| X2-C25: a missing cost cell: refuse or default | DP11: by world |
| X3-4, X4-2, X5-C2, X5-C9, X7-C1: automatic steps against his click | Q1 with the default stated |
| X3-5, X3 Q2: the BMS breaker and the kill switch | DP5 |
| X3-23: automatic restore against restore priced in evidence | DP20: benches by probe, slow-lane demotions by e-value |
| X4-5: windowed house money against "keep house money" | DP14 and the plain-words note to him |
| X4-6, X4 Q1: the floor-hit action | Q4 (numbers lens) with the default |
| X4-9: clamps outside the unit against "the unit stands alone" | DP5: the guard may refuse what the unit decided; the unit stands alone for logic, not for clamps |
| X4-10: switch only when flat against the identity table | DP7: adopt at next flat; a swing unit's wait is a declared time with a forced switch as his click |
| X4-15: exits never blocked against venues that block | DP26 item 7 and X4-52: the invariant row says "by QMX's controls"; a venue refusal raises the incident's urgency |
| X5-C1: looks, e-meter or wealth as the decider | DP27 and DP28: wealth gates promotion, the e-meter is display, looks are the verified fallback |
| X5-C7: pooled proof against each unit standing alone | DP15: family green is never unit green; both shown (X5-H39) |
| X6-10, X7: agents see the distance to trip | DP32: they see it; the pod-shop habit of hiding limits is not adopted, because an agent cannot size |
| X6-11: the upside alarm against accelerators | DP30: the cone in R; money views carry the accelerator line (X6-24) |
| X7-C3: "the sky's the limit" against rationing | DP32: the run surface is unlimited; the queue is budgeted |
| X7-C16: expiring evidence against 20-day evidence | DP23: the nomination window is the evidence; the record's TTL is the isolation's |

---

## 3. Logical flaws across the picks

Found by checking each pick against the others, the ledger couplings and the simple X4 scenarios (01, 03, 05, 06, 24, 29, 30, 41, 42, 53, 59, 62, 63, 69, 71). Arithmetic in `working/flaw_arithmetic.py`.

| # | Flaw | Status | Resolution or what stays open |
|---|---|---|---|
| F1 | The 55 % 1:1 scalper he pictures loses after costs at a 5-pip stop on EURUSD (break-even 58 %). The frequency thesis dies to costs unless the cut shrinks the mean loss. | resolved | DP26 makes the fast-invalidation cut the working exit for scalpers; with half the losers cut at 0.35R the break-even is 50 %. So the cut rule, its two-arm proof and the trade row that can tell a cut from a time exit are on the critical path, not the sizer. Numbers lens: cut size per unit from its own winners' MAE |
| F2 | X2-H01 and X2-H02 could give two different sizes if H is not trade rate times days, and the brake reads sigma_unit while the sizer reads H. | resolved | DP9 defines H = measured trade rate x survival days; section C proves the identity |
| F3 | The sizer needs usable cushion, result spread with cuts, unit count, correlation and a cost cell; today the socket gives equity, entry, stop and record, and no marked equity exists. | resolved as a build dependency | DP11 and DP12: inputs widened (X1-H58), the guard computes cushion and correlation, `basis:unmarked` until marked equity lands; the architects must not ship the sizer before the guard's facts exist |
| F4 | The percentile brake has no record to read on day one; the cards carry a cone but no per-brake fire band; the record holes in G12 item 10 (protection closes leave no trade row, hand part-closes read full size). | resolved by a ladder, holes stay | DP17's fallback ladder; the harness's dry chassis gives the class default; the record holes mean live fire rates read high in the first weeks, so the sentinel's yellow zone is read first as "the card was optimistic" (X3-H09). The holes themselves are the repair's (S/BACKLOG 64, 66) |
| F5 | Splitting across ten correlated units at a small cushion puts each unit below a coarse lot step (cushion near 190 times the minimum-lot risk). | resolved | DP13: feasibility-first admission binds before the split; cushion lending; the class map shows what the seed can trade. Numbers lens: which classes clear at the first cushion |
| F6 | The cohort ladder reaches full size in about 100 trades; proof needs 600 or more; a unit at full size can read "unproved". | resolved | DP15: one ladder, cohorts as the speed limit, the e-bar as the ceiling per level |
| F7 | The accelerator half of the cushion pair could raise size into the money brake if the two read different ledgers or anchors. | resolved | DP14: one declared scope per pair; section D shows the same-ledger case cannot trip; the book-level house money (X2-H11) funds tomorrow's sigma budget at the anchor, never today's open size |
| F8 | Strictest-wins across tag scopes plus smallest-wins across caps stacks caution to nothing (the dash.js failure). | resolved, with a meter | DP6 and DP19: no tag brake live before its shadow precision; the binding clamp is named on every receipt and counted per profile version; a cap that binds over 90 % of trades is a defect |
| F9 | Fail modes disagreed: the MIS board fails open, isolation fails closed, agent evidence fails neutral, a stale conversion refuses, a missing cost cell refuses in X0 and defaults in X2. | resolved | DP23 and DP32: declared per feed on the brake registry row and shown together on the preflight; X2's missing cell is by world (DP11); a declared context need fails closed, an undeclared one open (X4-61) |
| F10 | Automation contradicts his click rulings: restores by rule, isolation by rule, drift steps by rule, agent evidence cutting size all break the unit build's "every risk stop waits for his click" and ruling 2's letter. | open for him | Q1; the default the work proceeds on is stated there. Nothing in the set lowers the kill switch, promotes, or raises above baseline without him |
| F11 | The picks together could choke a healthy unit: bench, halve, isolation, news windows, probation, feasibility skips. | resolved in steady state, open at the start | Section E: steady state gives up about 10 % of R, inside the choke budget, mostly news minutes and the halve step; the ramp costs about 60 baseline trades per unit start, which is days for a scalper and about 50 days for a 2-a-day unit. The cost-of-conservatism meter reports it; pooled cohorts shorten it for slow units; the numbers lens tests the rest |
| F12 | The horizon sizer's "0 % floor touches" is partly structural: size is recomputed from the cushion every morning, so only an intraday loss larger than the cushion can touch the floor. | open for the numbers lens | The reserve (X2-H07) covers the one-day hole; the harness must run intraday paths with size held through the day, 40 trades a day, gaps mid-day and serially correlated results before the sizer's survival score is trusted |
| F13 | A bench at 23:50 re-arms at 00:00 (X4-29); the money window in trades does not reset at the boundary but the day budget does. | resolved | DP17: windows roll in trades; a bench carries a minimum rest across the boundary; the budget renews at the declared boundary and never clears a locked unit (X4-71) |
| F14 | Three books on one account net losses but brake separately; each unit sizes from its start equity plus own results (X4-06). | resolved | DP12 and DP4: budget shares refreshed by the portfolio config; the account-level clip trips before the sum of cluster budgets would |
| F15 | A world switch carries calibrated numbers but not costs; the demo balance is $10,000 against a small live share. | resolved | DP15 and DP11: level 1, costs uncalibrated, house money zero, brake counters reset, the deployment carries the share and never reads the demo balance (X2-H50) |
| F16 | Agent positions on the bound demo account are "not ours", invisible to every rule, yet move the balance. | resolved as a flag | DP33 |
| F17 | Two kill-switch meanings: a brake "raising YELLOW" in the v17 design against "only he raises it" on the unit path. | resolved | DP5: brakes raise stand-downs; the kill level is a fact; the escalation card is one tap |
| F18 | Verification counts every closed trade by its net R; brakes count a breakeven at cost and a cut by size; the same trade means two things. | resolved | DP11 and DP17: one row carries R, `net_r`, the mechanism and the costs; two readers with two stated rules; nothing hidden |
| F19 | The applier can move a number the learner tuned on shared market facts for forty units at once (herding). | resolved | DP3: share cap per cluster per window, shown on the card |
| F20 | The sweep cap, re-seeds and deposits reset every cushion rule at once and could void the drawdown record or rescue a decaying unit. | resolved | DP16: banker acts journalled as boundary events; anchors re-derived before the next order; zones and levels are evidence state, not capital state |
| F21 | Deletion-4 would sweep the news calendar, the windows and the SQS replay rule this set builds on. | resolved by a claim | DP24 and DP25 name the files this session claims before C-20 |
| F22 | The hours-clause window length has no derivation; too wide merges separate losses. | open, with a shape | DP21: state-based with a class maximum; the harness scores it on the rk5 list and calm history |
| F23 | The two-tell isolation thresholds are daily-data studies; intraday precision is unknown; a noisy isolation gets muted. | open for the numbers lens | DP23: shadow first, precision record, the trip-tax budget as the bar (X4 P6 c) |

Unresolved after this step: F10 (his), F12, F22, F23 (numbers lens). Known gaps with no literature, marked for the numbers lens: the fast-invalidation cut size, intraday win persistence after costs, rule-based class isolation precision.

---

## 4. Coverage

### 4.1 "What the technical lens must hold" (SEEDS, 55 items)

| TLH | Held by | Gap |
|---|---|---|
| 1 malleable template | DP1, DP2, DP7 | |
| 2 self-configuring with extensibility (n8n) | DP3, DP8, X1-H09 | |
| 3 one template per type, set may change | DP1 (presets over cells) | |
| 4 any stress without the baseline deviating | DP2 (packs, needs list), X1-H21 stress battery | |
| 5 solid core grown like mini apps; pods ship | DP2, X1-H29/H30 (pod bundle), X7-H36 | |
| 6 every number derives; derivation swappable | DP3 (derivation block, fallback ladder), DP9 (b) | |
| 7 ranges and a reason for every move | DP3 (receipts, reason codes), X2-H25 nomogram rows | |
| 8 self-configured against user-configured; nothing blank | DP3 (never-self-tune list, `changed_by_class`), X4-56 placeholder refusal | |
| 9 units of measure; pips, points, ticks | DP11, X0-01, X2-H47 three-number record | |
| 10 terminology for agents | X1-H23 three faces, X1-H66 dictionary families | Q2 fixes the words |
| 11 edge-led sizing from QMB's evidence | DP10: gate and level only | by design, not the amount |
| 12 frequency-led sizing, day budget split | DP9 | |
| 13 low-edge tolerance | DP9, DP15 (level 1 earns a little), DP26 (the cut) | |
| 14 Kelly after costs; house money; cushion share | DP10 (ceiling), DP14, DP9 | |
| 15 fast invalidation in every size and sim | DP11 (s with cuts), DP17 (loss points), DP26, DP29 | |
| 16 the stop in the unit; the loss per trade; one-shot breakeven | DP26 | |
| 17 costs per market, instrument, timeframe, hour; demo-live gap | DP11, X2-H50, X5-H38 | |
| 18 growth over 24 hours; compounding per cluster and portfolio; next-day restart; sweep cap | DP16, DP20 | |
| 19 several positions per unit, same bet once | X0-51, X2-H34 (bet key, basket cap, Little's-law heat cap), X4-23 netting refusal | |
| 20 placement, MIS as router, System 1 | X0-46 placement score, X0-26, X0-48 | widen door is the MIS's (flagged) |
| 21 the old circuit breaker improved, alpha decay | DP17, DP18 | |
| 22 losing-run brake scaled to trade count | DP17 (d) | |
| 23 brake levels addable, removable, combinable | DP6, DP19 (registry row, shadow, certificate) | |
| 24 accelerators; placement; brakes first | DP14, Q5 | |
| 25 floor almost never touched; buffer; exits never blocked | DP22, DP26, X3-H46 | |
| 26 kill switch and SQS as external parts; news | DP5, DP25, DP24 | |
| 27 market isolation protocol; "how does the MIS adjust" | DP23 | |
| 28 drift handling in steps | DP27 | |
| 29 portfolio self-optimisation | X2-H37 poker-band pots, X7-H35 rebalancer, X1-H41 shed classes | |
| 30 four levels with overlaps | DP4, DP6 | |
| 31 schemas and versions of the risk part | DP2, DP7 | |
| 32 external code | DP8 | |
| 33 how copilots, agents, workflows reach it | DP32 | |
| 34 tools for agents; propose; he clicks | DP32, DP7 | |
| 35 QML's role; new block roles | X1-H66, H67 | |
| 36 findings as Library artifacts | X0-47, X7-H25 | |
| 37 runs on the node and his PC | X1-H31 | |
| 38 demo and live split; demo units at boot | X0-53, X2-H50, X0-09 | |
| 39 what QMB hands over; what the MIS publishes | DP28 (card, band, plan), X0-48 | |
| 40 sniping windows found deterministically with agent candidates | X0-47 = X5-H47 = X7-H25 | |
| 41 micro and macro structure as numbers | X0-38, X0-06, X7-H26 | |
| 42 UI needs | X6 section 9, X1 Appendix C, X7 Appendix B (handed to the UI session as they stand) | |
| 43 simulation harness | DP29 | |
| 44 borrowed designs | X1-H29 (QuantAnalyzer resize replay), X2-H20, X1-H17 (StrategyQuant snippets) | |
| 45 must go live; cTrader then Hyperliquid | section 5 (shape C first), X4-52, X4-80 | Hyperliquid binding is the build's |
| 46 brakes count fast invalidation and exits; stop mechanism chosen per style | DP17, DP26 | |
| 47 exposure, drawdowns, unrealised and realised at cluster and portfolio | DP30 (X6-02, X6-33), X0-11 | |
| 48 scenario generator with brakes in place | DP29 | |
| 49 frequency-aware brake per level | DP17, DP21, DP22 (windows in trades, burn tiers in expected trades) | |
| 50 edge verification as a workflow beside QMB | DP28 | |
| 51 DevOps layer; wrong, right, working, up, on, trading | DP30 (X6-11), DP31 | |
| 52 the variables ledger with couplings | `ledger-merge.yaml`, DP6 typed edges, X1-H65 layer H | |
| 53 clustering of terminology and variables across classes | DP1 (cells, buckets), X2-H47, X1-H68 | |
| 54 agents solve issues with workflows | X7-H22, H27, H31 | |
| 55 Exa, not Firecrawl | not a design item | |

### 4.2 G12 hand-offs (37 items)

| # | Answered in | # | Answered in | # | Answered in |
|---|---|---|---|---|---|
| 1 exits socket | DP26.1 | 14 bid bars | DP26.14 | 27 SQS | DP25 |
| 2 six exits | DP26.2 | 15 USDJPY sizer | DP11 | 28 halt silent at zero | DP23 (unknown is not calm) |
| 3 signed stop | DP26.3 | 16 costs and edge to sizer | DP11, DP12 | 29 no host runs halts | DP5 |
| 4 widening | DP26.4 | 17 receipt | DP12 (X1-H07) | 30 cross-unit hook | DP5 |
| 5 partial close and R | DP26.5 | 18 wrong-side stop, `risk_fraction` to 1 | DP22 clamps | 31 kill-line distance, budget in rows | DP30 |
| 6 targets | DP26.6 | 19 weak contract tests | DP8 (two adapters) | 32 Book and correlation ledger | DP4, DP5 |
| 7 no price stop | DP26.7 | 20 real against planned risk | DP11 (`gap_loss_beyond_stop`, realised R) | 33 grid and martingale | DP34 |
| 8 moved number, open trades | DP26.8 | 21 margin and leverageId | X1-H18 record field | 34 `too_thin` | DP27 |
| 9 two exits one bar | DP26.9 | 22 R and costs | DP11 | 35 version pull | DP7 |
| 10 position facts | DP26.10 | 23 kill levels | DP5 | 36 u2 rules hold | DP27 |
| 11 wicked bar | DP26.11 | 24 third refusal | DP22 (escalation schedule row) | 37 check with no orders | DP7 |
| 12 timer long-only | DP26.12 | 25 unplaceable protection | X4-77 schedule, page deadline | | |
| 13 lost stop | DP26.13 | 26 kill line verb and floor | DP22 | | |

The "nobody knows until the demo sign-in" facts (G12 item 9) that these picks lean on: whether a fill carries the stop (DP26.1 and 13), deal-history fields (X4-83), real slippage and commission (DP11's calibration order). Each pick says so where it leans.

---

## 5. Architecture options

Three whole-system shapes survive honestly. The dial (X0-49) and the oracle (X1-H69) do not.

**Shape A. Profile, tags, portfolio config.** DP4 (a) in full: one risk profile per unit, clusters as tags of three kinds (style, driver, logic family) applied as drop-ins, one portfolio guard config, one guard package with two adapters, the applier organ, the harness. Wins when: units are many and overlap (a unit in three clusters at once), co-loss by driver matters, and he accepts new words on screen. Loses if: the words confuse him, or the first live version arrives late because two Library kinds and a lander are on the path.

**Shape B. Profile, Book and BMS documents.** The same profile, guard, applier and harness, but the cluster level is the Book document and the portfolio level is the BMS document as named (A4-092), with driver co-loss as a table inside the BMS rather than a tag. Wins when: his vocabulary and the existing Book path code (5,951 lines, `book_handler`, `orchestrator/ledger`) shorten the build, and the unit count stays small enough that intersections are rare. Loses if: a unit needs to sit in two clusters, or per-Book buffers reappear as idle money.

**Shape C. Flat first.** The profile, the guard, the sizer, the money brake and ladder, the exit stack, RiskState and the six words, one portfolio config (floor, buffer, bet keys, parent limit, rank table, never-self-tune list), the applier in shadow, no cluster level at all; the logic family is a tag used only for proof pooling. Wins when: "must go live" and "foundation first" rule, the first units are few, and every later increment (tags or Books, isolation by class, the agents' door) adds without rework because the guard's facts and the profile schema already carry the scope keys. Loses if: the first live book has more than a handful of units on shared drivers before the cluster level exists.

**[judgment]** C is the first increment of both A and B and should be built first whichever wins; A and B are the fork for competing versions. What decides between A and B is his vocabulary (Q2) and the arena's measure of build size and of how many picks each shape expresses without a workaround (the stress battery of X1-H21 is the test).

---

## 6. Questions for him

Filtered against SEEDS and the rulings. Each has the recommended answer and the default the work proceeds on. Nothing blocks on him.

| # | Question | Kind | Recommendation | Default while open |
|---|---|---|---|---|
| Q1 | May a unit step down (REDUCING, BENCHED, one level down, a confirmed demotion to paper at a planned look) and back up (restore by probe within a retry budget, a level up when the cohort and evidence bars are met) by rule, and may a confirmed class isolation apply in `no_new_entries` mode with a time to live, so that only HALTED, lockouts, the kill switch, promotion and raises above baseline wait for your click? This restates ruling 2 by direction. | irreversible scope | Yes. The book cannot go dark on every routine bench while you sleep or travel; the kill switch, promotion and raises stay yours. | Yes, with a retry-then-lockout budget and every automatic step journalled with its cause |
| Q2 | Words on screen: keep "Book" for the style cluster and "BMS" for the portfolio config, or use "cluster" and "portfolio"? And accept "risk profile", "pack", "preset", "pod" (a shippable bundle), "event window", "isolation", "trip tax", "sitting-duck meter"? | vocabulary | Keep Book and BMS on screen; accept the rest. | Book and BMS stay as screen words; the schema uses cluster and portfolio |
| Q3 | May a unit go live at the smallest feasible size before its edge is proved, with the packet saying "proof pending, 212 of 610 trades, level 1, expires on this date"? If no, proof finishes in paper and paper runs for months for most units. | irreversible scope | Yes. Level 1 is a canary, not a promotion, and the click still approves one hash at one level. | Yes |
| Q4 | Numbers lens, when you get there: the floor-touch tolerance (how rare "almost never" is), the first floor and buffer, the ratchet share of each new high that locks in, the floor-hit action (stop the pot until a re-seed, or one feasible micro unit at level 1 until the cushion rebuilds), the card budget per day. | money | The harness sweeps each; you pick from the table. Floor-hit default: stop new entries, exits run, wait for your re-seed (your C12 "being disciplined"). | The harness runs the ranges; floor-hit = stop the pot; cards = 3 a day measured |
| Q5 | Where does house money live: the unit's ledger, the cluster's, or the portfolio's? | vocabulary he cares about (A21, C5) | The accelerator half on the cluster ledger with an event window (one shared move funds one allowance); the brake half (reverse house money, your idea) on each unit's own ledger. | As recommended |
| Q6 | At night, wake you only when money is at risk, the system cannot fix it alone and your action changes the outcome before a deadline; otherwise the morning card? And your absence policy while away: no new entries once flat (benches and isolations still clear by rule, lockouts wait), or level 1 under every brake? | scope | Wake contract as stated; absence policy dark-after-flat. | As recommended |
| Q7 | May a community or agent-written block size a live trade after shadow trades, a passed card and your signature on the pin, or never? | irreversible scope | Yes with the signature; it is the door you asked for in D43 and the signature is your click. | Yes |

Not asked, because settled: the BMS breaker does not raise the kill level (rulings: kill switch earned its spot); R stays gross with `net_r` beside it; the sweep cap returns as a ratchet, not a cliff; agents get cTrader's MCP on demo (his ruling, G12 §5); the agent-trader unit type is reserved and not built (his D44).

---

## 7. What this set leans on that is not proved

- No money brake has run on QMX's own trade streams; every fire rate is a model floor (X3 SIM, R9).
- No fills exist; every cost cell starts synthetic; the demo-to-live gap is unmeasured until level 1 runs.
- The horizon sizer has one model sim with no fat tails beyond injected gaps and no intraday path (F12).
- No paper tests a fractional early cut after costs, breakeven moves after costs, intraday persistence after costs, or a fund switching a class off by rule.
- The applier, the guard, the exit socket's steps 2 and 3, marked equity, the commission key, the RiskState row and the harness engine do not exist (G12 item 3). The repair builds plumbing around them and none of them.
- Everything above `R06` in the repair stack is unreviewed or unmerged; the facts here were read at tips J, N and R on 6 Nov.
