# The funnel: one consistent set of decisions

Fable funnel judge, 6 Nov 2026. **Fix round after `REVIEW.md`, same day** (the lead's ten calls applied; section 8 answers the review item by item). Brief: `linking/FUNNEL-BRIEF.md`. Rubric: `linking/RANKING.md`. Inputs read in full: X0 to X7, G12, SEEDS, STATE items 25 to 45, his 6 Nov words, `REVIEW.md` and its scripts. Evidence spot-checked: `linking/stage-b/X2-sizing-accelerators/sims/out-1000.txt`, `linking/stage-b/X3-brakes-exits-drift/out-200.txt`, `grounding/sims/frequency_flaw_and_brakes.py`, the review's `out-table-n10.txt`, `out-attrib-n10.txt`, `out-sens.txt`, `out-more-arith.txt`, component rows A1-036, A1-087, A1-105, A1-115, A1-153, A1-154, A4-002, A4-091, A4-152. Ledger: `ledger/check.py --with-additions --no-write` (903 variables, 1,758 couplings, 7 duplicate ids, 5 alias warnings, 3 orphans).

Companion files: `HYBRID-FATES.md` (every hybrid's fate and tier: core, shadow, later, dropped), `ledger-merge.yaml` (id merges, deaths, and every variable's tier), `working/flaw_arithmetic.py` (the algebra behind section 3), `working/review/core_sim.py` with `out-core-table.txt`, `out-core-shed.txt`, `out-core-kstop15.txt`, `out-core-attrib.txt` (the harder integrated sim, section 9), `working/roundtable.md`, `working/premortem-redteam.md`, `working/lookups.md`.

Scores are 0 to 3 on RANKING's six criteria: **P** performance (growth by a named mechanism), **S** survival (0 blocks), **E** evidence (3 live or real-money trading result, 2 fair-controlled test, 1 own backtest or a pattern proven in another field with no trading test, 0 idea), **A** asymmetry (ledger variables count as cost), **F** fit, **C** self-configuring. **[judgment]** marks my opinion. No number here is a value; every number is a shape, a derivation rule or a range for the numbers lens. All sim numbers are model numbers on one worked example, not evidence about a real strategy.

## 0. The set in one page, and what is on at go-live

The chassis is **one risk profile document per unit**: a spec he writes, a status only the runtime writes (suggestions from agents come later). Types are **presets over style x class cells**; four chain keys at go-live (preset, class, instrument, unit), seven reserved. Every number carries a **derivation block** with a fallback ladder (own record, pooled class, preset, refuse), a receipt and an **authority field**; the numbers he owns (floor, buffer, kill line) sit on a **never-self-tune list**. Whether the numbers move through an applier with modes or by refresh at each anchor is a fork for the architects (section 5); the document is the same either way, so growing to the full learner and applier needs no rework.

The money path is **one guard package with two host adapters** (QMB and the node): it computes every statistic the slots read, holds the clamps, answers `before_order` with pass, shrink or refuse, applies one rank table, and emits a **RiskState** row every pass. Clusters and the portfolio are **one portfolio config** at go-live (floor, buffer, bet-key rule, parent limit, rank table, never-self-tune list); whether the Book and BMS come back as documents or as cluster tags is a structure question for him after go-live.

Size comes from **survival, not from the edge**: per-trade risk = usable cushion over (result spread x z x sqrt(horizon trades) x book-swing factor), recomputed at each anchor on the live unit count and level-weighted sizes. The edge is a **range** that touches three things only: the gate (low end positive after costs), the **starting level** (QMB's deflated holdout sets it, so a proved unit does not start at a tenth of its safe size), and the raises above baseline (the edge dial and any accelerator), which the funded e-meter governs. Under the baseline nothing waits on the e-meter: **cohorts set the speed up, the CUSUM steps down**. Costs enter in three places: the denominator, the ceiling (shadow at go-live) and the admission gate. Feasibility is re-run at every anchor; when the baseline falls under a lot step, units are shed by rank so the survivors clear a lot, and the smallest clearing level floors a live unit's level.

Brakes at go-live are **tail brakes that enforce from day one**: the unit's own-p1 money bench over a window in trades with a dollar clamp and retry-then-lockout; the **portfolio day stop** (a stand-down at `all`, expiring at the next anchor) with the **one-ledger cushion pair's brake half** tapering into it (reverse house money, his idea, at portfolio scope); the cushion clip with its reserve; the order-boundary clamps. Timing brakes (REDUCING at own p10, loss points, his "about three" at the unit's own run length, chorus, burn tiers, class isolation) **run in shadow**, write would-have rows and show on the card; they bind only after the harness's pooled report. One running loss is read once at each scope. House money's accelerator half is **shadow with a real switch-on path**: when the unit's own record passes the pair's proof card, it turns on under the rule he pre-authorises once.

Exits are a **stack** (disaster stop at the venue, forced flat, kill close; thesis fast invalidation with a price backstop from the winners' adverse excursion, time, target), the safest wins, exits never blocked, stops only tighten; the cut is a counted two-arm trial per unit, and **F1 is open**: the frequency thesis needs a cut that catches few winners. Drift is **three speeds in one monitor**: inputs in days, a CUSUM warning that steps one level down, a second warning inside 500 trades that moves the unit to paper; the money brakes apart. Verification at go-live is a machine check in a week against a twin, one bound click that approves one hash at one level on these markets until a date, and proof that continues live at the holdout's level. Agents reach it through **read and propose** (a direction on every operation, cut-only evidence that expires) and run their checks through the light harness; the fast loop never waits for a model.

**What he must be told plainly at go-live** (section 5.5 lists it in full): the portfolio day stop and the unit bench enforce; class isolation, REDUCING, loss points, his "about three", chorus and burn tiers are shadow; house money's brake half is on and its accelerator half is shadow until its card; the sweep cap he asked about twice comes back later as a ratchet, not at go-live; R is gross with `net_r` beside it, our call; the floor is fixed at go-live; his phone pushes need his word because the push list is closed.

---

## 1. Decision points and picks

Sources merged: X0 section 1; every layer's problems, collisions and restructures; G12 hand-offs 1 to 37 and item 11. 34 decision points. Each names its tier: **core** (binding or running at go-live), **shadow**, **later**.

### A. The chassis

#### DP1. The unit of defaults: type, cell, or dial — core
Options: (a) one template per unit type as the top shape (his A5; X1-H16 alone); (b) presets over style x class cells with an override chain (X0-44, X1-H37, X1-H16 as the preset layer); (c) holding-horizon dial (X0-49).
- (a) P1 S2 E1 A2 F2 C2: ships complete per type; a new class means a new template; cannot pool thin instruments.
- (b) P2 S2 E1 A3 F3 C3: a new class or style is a row or column; pooling across the class gives thin instruments a reasoned number; provenance on every value; software inheritance checked (VS Code, systemd, n8n) with no trading test; the full eleven-key chain is more keys than the first live unit needs (review item 17).
- (c) P2 S2 E0 A1 F1 C2: catches style drift by measured hold; collides with A5 and with entry-logic families at one horizon; wild.
**Pick (b) with four keys at go-live: preset, class, instrument, unit.** The seven others (style, bucket, venue account, market, timeframe, session, event) are reserved in the schema so the census test does not refuse them later, and resolve to their parent. Types are presets (`scalper-mr`, `orb`, `trend-pullback`, next). Children only tighten caps. X0-49's one gift survives as a measured field `holding_horizon` that raises a yellow, never changes defaults. Assumes: compiler format bump (X1-H56) and the census test (G12 item 2).

#### DP2. The document, its parts and its plug-ins — core
Options: (a) risk profile as its own document with spec and status (X1-H15, X1-H01; suggestions from X7-H06 later), one pack per profile at go-live with `smallest_cap` as the only combiner, three verbs (X1-H20), needs list (X1-H19); (b) everything stays inside the unit document with no profile id (today's shape, G8).
- (a) P2 S3 E1 A3 F3 C3: one profile serves many units; versions without touching logic; unknown fields refused; Kubernetes and Nautilus patterns checked, no trading test.
- (b) P1 S2 E1 A1 F2 C1: every risk change is a unit version; parsed-and-ignored fields recur.
**Pick (a).** The profile is embedded at compile so the unit stands alone on the node (X1 collision 1: the snapshot rule exempts profile-only changes from cold-starting logic state). Packs that stack with other combiners (X1-H17) are later. The needs list is the compile-time check that no halt is bound to a statistic nobody computes.

#### DP3. The self-configuring loop — core, with one fork for the arena
Options: (a) the full loop: learner with bounds, applier with modes, guards with freeze, asymmetric motion, derivation blocks with a fallback ladder, reason codes (X1-H02 to H08; X2-H51; X3-H61; X5-H40, H42); (b) refresh at anchors: every derivation recomputed at the anchor and applied at the next, no learner bounds, no applier modes beyond `off` and `at_anchor`; (c) the guard overrides numbers from outside the unit (X1 P2 option c); (d) a bandit over approved profiles (X1-H48, X2-H53).
- (a) P2 S3 E1 A2 F3 C3: fills the half of the VPA loop QMX lacks; every move has a receipt and a way back; proven pattern in production software, no trading study of a learned fraction beating a fixed one on independent trades (R9); more variables (the review's cost).
- (b) P2 S3 E1 A3 F3 C2: fewer parts and no herding question at go-live; every number still derives and he still changes the derivation; a number cannot move between anchors.
- (c) P1 S2 E0 A1 F1 C1: moves self-configuring out of the unit (against D32).
- (d) P2 S2 E0 A1 F2 C2: no trading test; wild.
**Pick: the document carries the derivation block, the receipt, the fallback ladder, the never-self-tune list and the `authority` field on every number in both (a) and (b); (a) against (b) is fork F-A for the architects (section 5.3).** The lead's call: self-configuring is the heart of his ask ("how does it self configure", "what if I want to change the way it is derived") and is not cut. Under (a) the herding guard is the retune share cap per cluster per window, shown on the card. Under both, "flat" for a multi-position unit means no open position on the market the number applies to. D32 against pooled priors (X1 collisions 2 and 25): the unit chooses its rung order and the receipt says `borrowed:<group>` when a pooled value is in force.

#### DP4. Where the levels live — core: one portfolio config; the Book against tags is his structure question after go-live
Options: (a) profile, cluster tags and one portfolio guard config (X1-H40); (b) Book and BMS documents as named (A4-092); (c) a central risk oracle (X1-H69); (d) no cluster level at go-live: profile plus one portfolio config; bet keys and the parent limit do the co-loss job; the logic family is a tag used for proof pooling only.
- (a) P3 S3 E1 A2 F3 C2: driver clusters catch co-loss a style Book never saw; one floor instead of per-Book buffers that add up to idle money (his C11); systemd drop-ins and SIMM buckets checked, no QMX generation ran tag clusters; two new Library kinds and a lander on the path to the first live unit.
- (b) P2 S3 E1 A2 F2 C2: his words; the Book path code exists (5,951 lines); cannot express intersections (his B1); per-Book buffers.
- (c) P1 S0 E0 A0 F0 C1: blocked on survival.
- (d) P2 S3 E1 A3 F3 C2: fewest parts; right while units are few; what the first increment needs.
**Pick (d) for the first increment. (a) against (b) is Q8 for him, a structure question, not vocabulary:** replacing the Book and BMS documents frees 5,951 lines of the Book path and up to 4,732 more (G12 §3), and M33's bar is "can perform better". The harness tests (a) against (b) on X4-01, 03, 05, 64 before he is asked. (c) dropped. Hand-off 32: the guard holds the bet-key ledger ("internally external", C18) in every shape.

#### DP5. The guard, the hook, the states and the kill switch — core
Options: (a) one guard package, two host adapters (X1-H26, H57); `before_order` pass, shrink, refuse with closed codes (X1-H27); one rank table per scope (X1-H13, X3-H59, X4-59); a five-state spine ACTIVE, REDUCING, BENCHED, HALTED, RESTORE (X3-H59); kill levels as facts the spine reads, never set by a brake (X3-H62, X1-H28); (b) map kill levels onto the states (X1-H10's mapping); (c) blocks compute everything per market; (d) an app publishes statistics like the board.
- (a) P2 S3 E1 A3 F3 C2: backtest equals live for every brake above the position; units on one account see each other; node-local; RiskGate's pipeline without the hop (author build); the biggest build item in the set.
- (b) P2 S2 E1 A2 F1 C2: a brake could set a kill level by mapping.
- (c) P1 S1 E1 A1 F1 C1: cross-unit statistics impossible.
- (d) P1 S1 E0 A1 F0 C1: breaks ruling 11; fails open.
**Pick (a).** Two tables stay (states and kill levels), both shown (X6-09); a `resume all` after a portfolio stop needs a second confirmation and has a 30-second undo (X4-75). Kill-level effects (hand-off 23): YELLOW no new entries at scope; ORANGE no new entries, amends tighten only; RED close this node's positions, no entries; BLACK close, pause everything, resume only by his hand. The portfolio day stop raises a stand-down at `all` and lands a one-tap escalation card (X7-H43); whether it may raise the kill level itself is Q5. The hook as built (a static method answering a string, G12 socket guess 7) is replaced by `before_order(intent, open_positions, facts)`. R15's reason census: every brake text needs a code (X6-06). "How does the MIS adjust?" (his C27, review item 18): the board keeps publishing its words; the guard refuses entries in a stood-down scope; the router must not place a unit into a stand-down; nothing else changes in the MIS.

#### DP6. Levels, scope keys, cascade and drop-ins — core (keys and cascade); tags later
Options: (a) level and scope key on every number and brake; strictest wins across scopes; down the levels as caps and states, up as events; cascade with `important` outer caps (X1-H34, H35, H36; X3-H35; X4 restructure 2); tag scopes and drop-ins (X1-H42) later; (b) folder containment only.
- (a) P2 S3 E1 A3 F3 C2: "everything off for crypto" is one rule at one key; CSS, VS Code, Nix, systemd checked, no trading test; strictest-wins stacks caution (X1 collision 26).
- (b) P1 S2 E1 A2 F2 C1: cannot express intersections.
**Pick (a).** Scope keys `class:`, `region:`, `currency:`, `underlying:`, `session:` join `instrument:` in the stand-down table and the kill switch (X1-H61) at go-live; tag-scoped brakes come with the cluster level. The caution-stack guard: no scope-level brake goes live before its shadow precision is read; the binding clamp is named and counted on every receipt (F8). Every ledger `affects` edge is typed `down:cap`, `down:state` or `up:event`.

#### DP7. Versions, records, rollout and the click — core
Options: (a) pinned profile versions with a migration map and identity labels (X1-H43), two records (X1-H44), a new version shadows before it binds (X1-H45's shadow step; the canary across markets later), plan before change and an effect-bound approval (X1-H46 = X7-H04 = X5-H10), offers never silent (X1-H47, later); (b) every risk change is a new unit (today); (c) a bandit among approved versions.
- (a) P2 S3 E1 A3 F3 C2: the record survives the rip-out and every later swap; what runs is what he saw; Argo, Terraform, "Approve What, Exactly?" (controlled test outside trading); approval without reading is unmeasured.
- (b) P0 S3 E1 A0 F2 C0: the rip-out costs every unit its record.
- (c) P2 S2 E0 A1 F2 C2: later.
**Pick (a).** Two records answer X1's question 2 without a ruling. Hand-off 35 is consistent: a sizer-only swap trades the same in R and pays the pull; an exit change is a counted try (X5-H29). Hand-off 37: a behaviour check with no orders ends `inconclusive`. The identity labels are rows he edits.

#### DP8. Outside code and trust — later
Options: (a) trust ladder, minimum trust per slot, signature on the pin, two adapters per slot, three faces, class coverage, a quarantined raw-code hatch (X1-H22 to H25, H68); (b) only signed `qml` and `human` blocks size live; (c) signature alone.
- (a) P2 S3 E1 A2 F3 C2: keeps the door he asked for (D43); n8n community process checked, no trading test; the check must live in the loader.
- (b) P1 S3 E1 A3 F2 C1: shuts the door for now at no cost to the first live unit.
- (c) P1 S2 E0 A3 F2 C1: least code, most clicks.
**Pick (b) at go-live; (a) is the plug-in, with two adapters per slot (X1-H25) kept in the core because the contract tests need them.** His D43 door opens after go-live under the ladder and his signature (the old Q7, now a later question).

### B. Sizing

#### DP9. The baseline amount — core
Options: (a) horizon floor-odds sizer = day-sigma budget (X2-H01 = X2-H02, one formula when H = trade rate x days, `working/flaw_arithmetic.py` C), split by effective bets on residual stressed correlation (X0-02, X2-H28) over **admitted** units with **level-weighted** sizes, with the cushion clip and reserve (X2-H07 = X3-H25); (b) risk-constrained Kelly from his floor tolerance (X2-H05); (c) own full size under a parent limit on co-loss (X2-H29); (d) his literal split, day risk over N; (e) half Kelly; (f) the GitBook ladder.
- (a) P3 S3 E1 A3 F3 C3: zero floor touches in all twelve of X2's sim cases and in every case of the harder sim (section 9); 2.8x the literal split's growth at the believed edge; trades from day one with no edge input; the "0 %" is partly structural (daily recompute) and in X2's sim half the cushion goes in 30 to 42 % of zero-edge runs in 60 days (`out-1000*.txt`); the harder sim's bleeding case loses half the cushion in 97 to 100 % of runs with the sizer alone, which is why the brakes exist.
- (b) P2 S2 E1 A2 F2 C3: later, as the swappable derivation and cross-check (D46).
- (c) P3 S1 E1 A2 F2 C2: 18.7 % floor touches at half the edge with ten correlated units (X2's fixed-1 % row); the overbooking idea survives as cushion lending, later.
- (d) P1 S3 E1 A1 F2 C1: the sitting duck.
- (e) P2 S0 E2 A1 F1 C2: blocked: 100 % floor touches at half the edge with ten units.
- (f) P2 S0 E1 A1 F2 C1: blocked: 88 to 97 % floor touches with ten seats.
**Pick (a).** Rules the review found missing (items 5, 6, 7): N is the count of admitted units, recomputed at the weekly allocation anchor and **never raised under a caution or a bench**; B is computed on level-weighted sizes so a proved unit is not held at a tenth of the book's allowed swing while nine others sit at level 1; the trade rate in H is floored at the card's rate so a dead month cannot raise r. H's days are the survival horizon over which the floor-touch tolerance holds, a ledger row with a derivation (review item 15), listed under Q4.

#### DP10. The edge's role — core
Options: (a) gate, starting level and raises only: low end positive after costs to trade (X0-04, X5-H44); QMB's deflated holdout sets the **starting level** (X5-H04 with X2-H13); the funded e-meter governs only raises above baseline and the edge dial (X5-H12 reread); the cost-and-gap Kelly ceiling computed on the receipt, binding later (X2-H04); the dial (X2-H03) defaults to `zero` and is released to `low` by proof under a rule he approves once (Q6); (b) "twice the edge, twice the size"; (c) the evidence bar as a ceiling under the baseline (X5-H13 as written); (d) the soft multiplier on by default.
- (a) P2 S3 E1 A3 F3 C3: a weak uncorrelated edge gets its holdout level from day one; a wrong point estimate cannot size a unit; DeMiguel on 1/N and Chopra-Ziemba are strong on portfolio weights, second-hand for trade size (A1-031, A1-019 read `idea`).
- (b) P2 S1 E0 A1 F0 C1: he refused it (A24).
- (c) P1 S3 E1 A0 F0 C2: **dropped**: with the bar under the baseline the weak unit sits near a tenth of its safe size for months (review M2; `out-attrib-n10.txt`: healthy 0.94 to 0.38, weak 0.93 to 0.15; the harder sim: 0.92 to 0.45 and 0.89 to 0.23). That is the outcome he rejects (A14, A24, C13).
- (d) P2 S2 E1 A2 F2 C2: leans on the edge; off.
**Pick (a).** The edge touches the gate, the starting level and what sits above the baseline; nothing under the baseline waits on proof. Inverse volatility is the within-level allocator only for units without a tight stop (later).

#### DP11. Costs into size — core
Options: (a) the cost triple: denominator, the ceiling in R, the admission gate at a multiple k of stressed cost, per instrument and hour and world (X2-H39, X0-14, X0-17); two per-instrument-hour tables on the instrument risk record (X0-37 = X1-H18); session multipliers and premium lifts deleted (X2-H40); carry later (X2-H41); (b) cost as a gate only; (c) cost through the edge only.
- (a) P3 S3 E1 A3 F3 C3: a scalper's size follows net edge by hour; a negative net edge is never multiplied by breadth; the BTC cost filter and the MNQ study are author backtests, the NBER hour study is strong on cost; no fills exist yet.
- (b) P1 S2 E1 A2 F2 C1: over-sizes in costly hours.
- (c) P1 S2 E0 A1 F1 C1: hides cost from the receipt.
**Pick (a). The missing-cell rule (review M7):** live trades on the stressed class default (twice the posted typical spread), **pooled across the class**, labelled `cost:uncalibrated`, decaying toward measured fills; a cell refuses only after fills show net edge below zero. No "N fills before level 1": there is no writer of a cost profile from fills until after G-DEMO and no commission key (G12), so the first unit would be refused at most hours. Hand-offs 15 and 16: the placeholder sizer is replaced by money at the stop from the broker tick value with live conversion and a freshness limit; costs and the edge band reach the sizer through the widened inputs (X1-H58). Hand-off 22: R is the planned loss at the disaster stop, gross; `net_r` is R minus costs in R on every row; brakes, the money ledger and the gate read net; drift attribution keeps gross and cost streams apart (X4-84); `r_after_costs` becomes `net_r`. **This is our call, with his B9 reservation standing (review M11).** k is the numbers lens's, with the table from F1 beside it.

#### DP12. Which equity the sizer and the brakes read — core
Options: (a) asymmetric basis: committed cushion for size, marked equity for brakes, realised profit for accelerators, worst case at the stops for the clip (X2-H44); (b) one series, marked; (c) one series, realised balance.
- (a) P2 S3 E1 A2 F3 C2: no pressing on open profit; the fourth position sizes from what the first three left; prop practice, no controlled test; the fallback below needs a balance refresh that does not exist today (review item 12: the balance is read once at sign-in and the sizer uses start plus closed trades, G12).
- (b) P2 S2 E1 A2 F2 C1: presses on open profit.
- (c) P1 S1 E1 A2 F2 C1: over-sizes the next trade.
**Pick (a).** The build this needs is counted in part 4's facts: a timed balance re-read (R22 plans the wait-then-real-balance; the guard adds the timer) and open risk at the stops from protection rows. Until marked equity exists the receipt says `basis:unmarked`. The sizer's inputs widen to X1-H58's list and its receipt becomes real (hand-off 17).

#### DP13. Minimum lots, feasibility and lumpy classes — core
Options: (a) feasibility-first admission per unit x instrument x broker, **re-run at every anchor**, with the **lot-shed rule**: when a unit's baseline x level falls under two lot steps, the lowest-ranked units are shed to paper so N and B fall and the survivors clear a lot; a live unit whose level size is under one lot trades at the smallest level that clears one lot, never above the baseline (X2-H45 = X0-45, X0-17; review M9); whole-contract ladders (X2-H49) and cushion lending (X2-H30) later; (b) lot dither (X2-H46); (c) raise the class's share until its minimum fits; (d) skip and go dark.
- (a) P2 S3 E1 A3 F3 C2: no silent oversize; the book never goes dark above the floor; the harder sim at a $3 lot step and the worked cushion: skip leaves the book 100 % dark; shed runs one or two units at 0.70 to 0.76 of baseline with 0 to 4 % dark (`out-core-shed.txt`).
- (b) P2 S1 E0 A1 F1 C1: dropped.
- (c) P1 S1 E1 A1 F0 C1: dropped.
- (d) P0 S3 E1 A2 F1 C0: the sitting duck produced by the sizer (review M9).
**Pick (a).** The shed rank is declared on the portfolio config (default: the unit with the thinnest record first); the state is on screen ("3 of 10 units trading: cushion under lot steps"). Breadth of ten units at a small cushion is not feasible with micro lots until the cushion grows; the class map says so instead of the book finding out.

#### DP14. Accelerators and the cushion pair — core for the pair; the rest shadow or later
Options: (a) the one-ledger cushion pair **on the portfolio ledger**, both halves, with the event window (X2-H10, X2-H11, X0-05): the brake half binds from day one as a taper from the portfolio's own p10 day into the portfolio day stop at its p1 (reverse house money, his idea, at portfolio scope); the accelerator half (house money) is shadow until the unit's own record passes the pair's proof card (X2-H20: resize replay on its own trades against the equal-average constant, the deep-drawdown odds no worse), then switches on by the rule he pre-authorises once (Q4); any raise passes the raise permission gate (X2-H24 = X1-H13); tiers, persistence presses, pyramiding, calm scaling, AIMD shadow or later; (b) the April nine-multiplier chain; (c) automatic raises above baseline with no proof.
- (a) P2 S3 E1 A2 F3 C2: R9's script gives +37 to +42 % growth per risk under regimes and nothing on independent trades (and A5-118's tail: 73 % of paths over 25 % drawdown in slow regimes, which the proof card's drawdown test exists for); the brake half cannot drive into the stop on the same ledger (`flaw_arithmetic.py` D); his ruling "keep house money" (A21) is met with a path on, not a permanent off.
- (b) P1 S1 E1 A0 F1 C0: multipliers did each other's jobs.
- (c) P3 S2 E0 A1 F1 C2: no accelerator beats a constant on independent trades (R9).
**Pick (a).** One ledger per pair, as the pair's name says (review M8). At N = 1 the portfolio ledger is the unit's, so the taper and the unit bench are one reading ending in one trip. In plain words for him: house money is on in the sense that your reverse house money brakes from day one; the press after wins waits until the unit's own trades show it pays, then it switches on without a click.

#### DP15. Levels and the climb — core
Options: (a) one ladder: levels are fractions of the derived baseline (X2-H13); the **starting level comes from QMB's deflated holdout** (low end positive: start at 0.50; low end at zero: 0.25; below zero: refused live); cohorts (X5-H14's BOIN bars at the unit's own healthy bad-cohort rate) are the only speed limit up, one level per clean cohort; the CUSUM warning is the step down (DP27); a world switch resets to the start level and marks costs uncalibrated (X2-H50 = X4-30 = X5-H28); pooled cohorts for slow units and the exploration budget later; (b) his calendar ramp; (c) full size at promotion; (d) the evidence bar per level under the baseline (dropped in DP10).
- (a) P3 S3 E1 A3 F3 C3: the harder sim: a healthy unit runs at 0.89 to 0.92 of baseline, a weak one at 0.84 to 0.89, with the climb finished in two or three cohorts; the bleeding unit with an overstated card is stepped down by the CUSUM before the cushion halves in most runs (section 9); BOIN and TCP are proven elsewhere, never on a trading unit.
- (b) P1 S2 E0 A2 F2 C1: ignores evidence speed.
- (c) P3 S1 E1 A0 F1 C1: ten unproved units at full size touch the floor in 68 % of runs at no edge (STATE 10).
**Pick (a).** Paper is one week of machine check (DP28), then his click, then the holdout level live; no e-bar on paper (review M7). The e-meter runs from day one for its two jobs above the baseline. Slow units climb on their own cohorts at go-live and on pooled family cohorts once the family tag exists.

#### DP16. Growth across 24 hours, sweeps, re-seeds — core for the anchor clocks and banker acts; ratchet later
Options: (a) per-scope anchor clocks (X2-H12 = X3-H74 = X0-27); banker acts (sweep, deposit, re-seed) journalled with every anchor re-derived before the next order and verdicts untouched (X4-72, X4-73); a share-of-equity-per-R cap (X4-70); the gain-lock ratchet (X2-H56) later, with his base floor split from the lock line (review item 9); (b) the 2.5x cycle cap; (c) pure compounding with no cap.
- (a) P3 S3 E1 A2 F3 C2: no cliff; units keep the cushion their brakes read; CPPI theory and fund high-water marks live in their field.
- (b) P2 S2 E1 A1 F2 C1: a cliff against 24-hour trading (B5).
- (c) P3 S1 E1 A1 F2 C1: the risk share per R climbs with no cap (G6).
**Pick (a).** At go-live the floor is fixed and nothing sweeps; the ratchet comes with the numbers lens, and he must hear that the sweep cap he asked about twice returns that way, later, as a trade-off against idle money (at a 25 % lock, idle money rises from 30 % to 42 % of equity when equity doubles, `out-more-arith.txt` J).

### C. Brakes, restores, isolation, exits

#### DP17. The unit's fast brake — core (tail brake, enforcing)
Options: (a) the own-percentile money bench over a window of at least ten trades (X3-H01 = X0-16) with a dollar clamp from his budget, the day-boundary contract (X3-H74 = X4-29), **retry-then-lockout** as its restore; its class on the registry row: **tail**; (b) the old "2 full stops in a day"; (c) a fixed "3 in a row"; (d) his "about three" scaled to the unit's own run length, halve not bench (X3-H05, X3-H06); (e) REDUCING at own p10 (X3-H02), loss points (X3-H03), AIMD (X3-H07).
- (a) P1 S3 E1 A3 F3 C3: **its job is the tail, not growth.** On X3's own sim it earns +1.2R, +1.2R, +25.9R, +1.1R and +0.8R over its random twin on the five units (`out-200.txt`), so four of five would fail a random-control gate, and on the decay case it keeps -69.1R against -69.3R with no brake; the "97 to 100 % of healthy R" figures come from arms that bench for the day and return next morning at full size. The picked restore (retry-then-lockout) is now simmed: section 9.
- (b) P0 S2 E1 A0 F1 C0: keeps 18 to 65 % of healthy R; fires every day at 40 trades.
- (c) P1 S2 E1 A1 F1 C0: fires on 41 % of days at 10 trades, 91 % at 40 (`flaw_arithmetic.py` F).
- (d) P2 S2 E1 A2 F2 C2: timing in bad spells where losses cluster (+20R in X3's SIM), a 16 to 26 % tax where they do not; **shadow at go-live**. Scaled to own p99 the count is 5 to 10 straight losses at 4 to 40 trades a day for a 55 % unit (`out-more-arith.txt` A), at or above the six he called "very high" (A6); so the shadow brake uses the unit's own p90 to p95 run length since its action is only a halve, and he must be told what "three" became.
- (e) P1 S3 E1 A1 F2 C2: **shadow at go-live**; each is a second reading of the same running loss (review M3).
**Pick (a) enforcing; (d) and (e) in shadow.** One reading of the unit's running loss binds. The circuit breaker keeps its name (A26): fast half here, slow half shadow (DP18). Day one with no record: own live record, then the card's block bootstrap through the harness, then the class default from the dry chassis, then refuse live and allow paper. The holes in the record (G12 item 10) make fires read **both ways**: a protection close with no trade row hides a loss (reads low), a hand part-close at full size reads high; the guard's money ledger reads broker deals, not trade rows (review item 11).

#### DP18. The circuit breaker's decay role — core (CUSUM key); density shadow
Options: (a) the trade CUSUM as the key at go-live with Basel zones as its display (X3-H11's key 1, X3-H48); the fire-density sentinel, context tags and the second key in shadow (X3-H08, H09, H10 = X5-H19 = X7-H31); (b) density alone; (c) the shipped nightly 20-trade decay check.
- (a) P2 S3 E1 A3 F3 C3: the CUSUM caught a dead edge in 92 to 99.5 % of runs at 4 to 40 trades a day and 68.5 % at 2 a day (`out-200.txt`), density in 25 to 99.5 %; the CUSUM's healthy alarm spacing is about 668 trades (X5 §9), so a healthy 40-a-day unit steps one level down about every 17 days and climbs back in two cohorts, and in a bad week at 40 a day it alarms 54.5 % of the time: a reversible step, not a demotion, which is what A25 allows; the slow CUSUM is the part that earns: 29R becomes 78 to 86R on decay.
- (b) P1 S2 E1 A2 F2 C2: too slow alone.
- (c) P0 S1 E1 A1 F1 C0: replaced.
**Pick (a).**

#### DP19. Proof that a brake works, and what it costs — core (the switch and the harness); the certificate as a report
Options: (a) **two brake classes on the registry row**: tail brakes enforce from day one and carry a card saying "tail, timing unproven"; timing brakes stay in shadow until the pooled random-control report passes (X3-H13 as a report, not a compile gate); the shadow switch (X3-H14 = X1-H12 = X6-32); the scorecard, trip tax and sitting-duck meter over time (X3-H12 = X6-21, X0-52 = X3-H64 = X6-22); a **total choke budget** across all cuts on a healthy unit, tested in the harness, that blocks shipping when breached (X3-H65 widened); the dry chassis as the null (X0-50 = X1-H73 = X5-H08); (b) every brake must beat its random twin before it enforces (the first funnel's text); (c) brakes stake wealth (X3-H67).
- (a) P1 S3 E2 A3 F3 C3: the one fair test in the corpus (MQL5 23482: 97 trades, one author, all three arms lost money); a tail brake's certificate would take about 60 unit-years (`out-more-arith.txt` K), so it cannot be a gate; the meters add no growth by themselves (review item 2), they show where growth was given up.
- (b) P0 S2 E2 A1 F1 C1: on day one no brake may enforce, so the first live unit has clamps and no brake, against "brakes first" (review M5).
- (c) P2 S2 E0 A2 F2 C2: later.
**Pick (a).** The total choke budget replaces the per-brake one as the shipping test: in the harder sim the core runs a healthy unit at 0.89 to 0.92 of baseline (section 9); a healthy unit under 0.75 is a defect.

#### DP20. Restores, benches and what waits for him — core (retry-then-lockout); probes later
Options: (a) BENCHED clears by rule after its rest with retry-then-lockout (second bench inside 20 days locks one level lower for 20 days, third inside 40 sends to paper for 20), the CUSUM step down clears by cohorts; half-open probes, the memory ceiling and earned restore (X3-H15 to H18) later; HALTED, the kill switch, promotion, lockouts and automatic closes wait for his hand (X7-H05); (b) every risk stop waits for his click (the unit build's rule, G10 §1.6); (c) calendar reset at the boundary.
- (a) P2 S3 E1 A3 F2 C2: ends benches on evidence, not at midnight or at his next look; reclosers and resilience4j are live in their fields, the picked restore has only the harder sim behind it (E1); the "902R of 950R" figure belongs to the CUSUM policy (DP18), not to a restore.
- (b) P0 S3 E1 A1 F3 C0: the book goes dark on the first routine bench while he sleeps or travels (X4-74; the dark-book walk of review M6).
- (c) P2 S1 E1 A2 F1 C1: the day-boundary exploit.
**Pick (a); it needs his ruling (Q1).** Default the work proceeds on: ruling 2 restated by direction (X7 restructure 1): automatic changes are monotone toward less risk and always a declared rule of a unit or the portfolio; routine benches and level steps restore by rule within a retry budget; raises above baseline are his, once per rule or per step; automatic closes are Q1b. The window clock while benched (review item 8): the bench's rest is counted in the calendar equivalent of its window at the card's trade rate.

#### DP21. Cluster and methodology brakes — shadow at go-live
Options: (a) the hours-clause event ledger (X3-H20 = X4-91 = X0-10), chorus K of N (X3-H21 = X6-34), the burn-rate permit (X3-H22 = X6-15), the methodology pooled CUSUM (X3-H23 = X5-H23 = X4-04); (b) per-unit brakes only.
- (a) P2 S3 E1 A2 F3 C2: five correlated stops read as one event; a logic fading everywhere is caught in days; insurance and SRE practice (A2-026 is a vendor blog; no trading test); needs a cluster level and ρ from weeks of paper.
- (b) P1 S1 E1 A2 F2 C1: cannot see losing together (his C32).
**Pick (a) in shadow;** they bind with the cluster level after go-live. At go-live the portfolio day stop and the bet keys carry the losing-together case (X4-01, X4-14).

#### DP22. Portfolio and account brakes, clamps — core
Options: (a) the **portfolio day stop**: book day loss past k times the book's sized day sigma (the sizer's own number, level-weighted; not the budget sigma, which the sized book rarely reaches, section 9) raises a stand-down at `all` with an expiry at the next anchor, enforcing from day one as a tail brake (X3-H24's first slice, X4-14); the cushion clip above the buffer with the reserve (X3-H25 = X2-H07); the order-boundary veto with the size sanity band, order rate, margin headroom, stop side (X3-H75 = X4-42, 53, 54, 67); the pod-style ladder, priority shedding by class and the de-gross rule (X3-H26, H27, X4-87) later; (b) the 10/5/3 bands or 3-5-7 as numbers.
- (a) P1 S3 E1 A3 F3 C2: his portfolio breaker, "switch off entirely", on evidence he can read (the day's loss against the book's own sigma); Hsieh's clip reads `idea` in A1-038 with proofs behind it; the stop's k is the numbers lens's, with the harness's fire-rate column beside it.
- (b) P1 S2 E0 A1 F1 C0: no derivation; his own word "circumstantial".
**Pick (a).** Hand-off 26: the kill line is the cushion clip on marked equity; at go-live its verb is no new entries at the buffer; automatic reduce (closing positions by rule) is Q1b. The old bands stay in `seen_values` with no weight.

#### DP23. Isolation, the MIS and the weekend — shadow at go-live; scope keys core
Options: (a) one protocol: scope keys (X3-H35), two-tell bucket isolation with calendar-aware baselines (X3-H28 = X0-07 = X0-43 = X4-94), SQS K-of-N class caution (X3-H29), lifecycle with TTL and staged resume (X3-H33), unknown is not calm (X3-H36), the weekend scaler (X3-H37 = X0-40), agent slow isolation by card (X3-H34 = X7-H21), the macro governor and peer ejection later; (b) the kill switch alone.
- (a) P2 S3 E1 A2 F3 C2: a Tokyo event switches off JPY, not the book; the tells are daily-data author backtests with no intraday precision; the first live units are FX scalpers on cTrader, where the weekend is closed.
- (b) P1 S2 E1 A2 F2 C0: all or nothing.
**Pick (a) in shadow, with the scope keys and "unknown is not calm" in the core; he must be told class isolation does not bind at go-live (review M6).** The guard owns the switch as a stand-down at scope; the board carries the word; placement is the MIS's (flagged). Whether a confirmed isolation applies without his click is part of Q1.

#### DP24. News — core (first slice)
Options: (a) a news window on scheduled releases, entries only, with both FX legs tagged and the calendar's tier where impact is not yet measured, a stale calendar failing closed, blocked minutes reported; measured impact per release and driver tags beyond currency as the window learns (X3-H31 = X0-39 = X4-95 = X7-H48); (b) colour-level windows forever.
- (a) P2 S3 E1 A3 F3 C2: narrower measured windows give scalpers hours back later; the E-mini liquidity study is an author backtest; the calendar ingest exists and fails closed (G9).
- (b) P1 S2 E1 A2 F1 C0: swallows the day (X4-18).
**Pick (a) as a real first slice**, not a line (review item 20). The kill switch keeps the hard kill (C28). **This session claims before deletion-4:** `qmn/data/news_calendar.py`, `qmn/protection/windows.py`, `qmn/protection/dispatch.py` and `qmf-risk/control_window` (G12 §3, §4). The claims file in `handoff/FOR-REPAIR-CLAIMS-BEFORE-C20.md` must add the last two and `registry_catalog.py` (review item 21).

#### DP25. SQS placement (hand-off 27) — core (real slice)
Options: (a) the SQS gate inside the guard package with its baseline producer and the eight named settings as ledger rows with derivations from the spread histogram's own percentiles; the sensor roles (class caution, bad-day classifier, restore gate) and the graded shrink before the hard block (X2-H42) shadow; (b) "one line in `Runtime.guard`" as the plan guessed; (c) SQS inside the MIS.
- (a) P2 S3 E1 A3 F3 C2: a ruling ("kill switch and SQS stay"); the new node has no SQS, no producer runs and eight settings block live when blank (G12 §2), so this is a slice with a baseline producer, a hysteresis rule and eight derived rows, not a line (review item 20).
- (b) P1 S3 E1 A2 F2 C1: the same gate, undersized.
- (c) P1 S2 E0 A1 F1 C1: the board fails open.
**Pick (a).** Claims before C-20: `sqs_baseline_producer.py`, the `labelers.py` rule text, `qmn/replay/port.py`'s SQS rule and `qmn/config/registry_catalog.py`'s SQS rows.

#### DP26. Exits and stops: the socket and the fourteen hand-offs — core (step 2, the cut, the disaster stop, the trade row); step 3 and the six exits later
The pick and the fourteen answers stand as in the first pass: an exit stack (safety exits and strategy exits, the safest wins by rank, exits never blocked by contract test, stops tighten only, X3-H38 to H47 = X0-15 = X1-H60 = X5-H29), per-style families as defaults with the stopping-premium test as the override. Scores: P3 S3 **E1** A3 F3 C2 (the cut has no paper after costs; the stopping premium is Kaminski-Lo's abstract and one secondary; every cut rule is a counted two-arm trial). The hand-off answers (1 to 14) are unchanged, with one correction: **F1 is open** (section 3), so the cut's two-arm test is the first trial the harness runs, and the fallback if it fails is stated there.

### D. Drift and verification

#### DP27. Bad day or broken edge — core (three speeds)
Options: (a) three speeds: inputs first in days (cost against the card, trade rate, replay match; X3-H51 = X5-H09); a CUSUM warning in weeks that steps one level down reversibly; a second warning inside 500 trades that moves the unit to paper with a cause code (X3-H49 = X5-H15; the funded e-process as the confirmation key later); re-promotion by his click (X3-H53 = X5-H26); the bad-day sentence (X6-29); the classifier, the lifetime budget, regime cards, worry lines and the upside alarm shadow or later; (b) the nightly 20-trade check; (c) planned looks only.
- (a) P2 S3 E1 A3 F3 C3: a healthy unit was demoted by statistics in none of 4,000 trades in X5's arithmetic, with the honest spacing of one reversible step every 668 trades; a dead unit stepped down in a median 190 trades; nothing acts on one day except money.
- (b) P0 S1 E1 A1 F1 C0: replaced.
- (c) P1 S2 E1 A2 F2 C1: undecided at 1,000 trades in 46 % of half-edge plans.
**Pick (a).** The guard owns every size step; a warning is a transition to REDUCING with cause `drift_warning`. Hand-off 34: `min_trades=100` becomes `verification_trades_needed` at the band's low end with an incubation cap (X5-H06); hand-off 36: "rules hold on a real run" is never claimed by a stack list.

#### DP28. The verification path and the click — core (machine check, bound click, two records, holdout band); the rest later
Options: (a) at go-live: the band from four shrinkages sets the start level (X5-H04), the plan prices proof in trades with a correlation column (X5-H06), the machine check against a twin in a week (X5-H09), the bound click with class-aware pre-queue checks (X5-H10 = X7-H29), the evidence ledger with stage tags (X5-H37), one cost ledger from node rows (X5-H38), the passport strip (X5-H39), the template per type as the preset (X5-H40), the node emitting the zone (X5-H41); later: the counted birth, the sealed contract, the full battery, the challenger, the funded ledger as a gate, the canary, rehab, the governed pipeline; (b) the paper judge's "30 trades and 28 days"; (c) proof fully in paper.
- (a) P2 S3 E1 A3 F3 C3: the machine check closes in 7 days or 50 trades; the e-meter's "0.0 % null rate" is on daily ETF rules, 2.3 % on ±1R scalper trades (X5 §8), so it is "far better", not zero, and it never gates the size under baseline.
- (b) P1 S2 E1 A1 F2 C0: proves the machine on a calendar.
- (c) P1 S3 E1 A1 F1 C1: months of paper for every unit.
**Pick (a); Q3 carries the one piece that is his.**

#### DP29. The scenario harness — core (light form)
Options: (a) a light harness over the ledger rows: sizing and brake replay, the integrated sim of section 9 as its first job, three cases, the dry chassis, the mandatory scenario block (`HYBRID-FATES.md` marks 60 scenarios core), the scorecard with survival gates and the total choke budget (X4-90, 96, 97); the engine import, the sealed set, reverse stress and the agent bench later; (b) the lead's bare sims; (c) the agent-based bench.
- (a) P1 S3 E1 A3 F3 C2: the only machine that gives the survival number and the cost-of-conservatism number side by side; it adds no growth by itself (review item 2); it does not exist.
- (b) P1 S1 E1 A2 F1 C0: no brakes inside the path, which is his objection.
- (c) P2 S2 E1 A1 F2 C1: later.
**Pick (a).** The conformance test on one tape says when the light harness and the guard agree (X4 P5).

### E. Observability and agents

#### DP30. RiskState, the words, the rows — core
Pick unchanged: one fold, the equity triple, the decision trail, trade row v2, closed reason codes, meters for the core brakes, motion receipts, requested-enforced-observed, six words and UNKNOWN, the safety display, the passport strip, cost cells, the exposure board, fact flow, the morning card (X6-01 to 09, 11, 13, 27, 29, 30, 33, 37, 43). Scores: P1 S3 E1 A3 F3 C3 (telemetry adds no growth; a stale green is impossible). One drift vocabulary. Context tags, scorecards, the growth waterfall, Lab parity and the ledger-generated alerts later or shadow.

#### DP31. Alerts, pages and his attention — core (tiers, wake contract); the queue machinery later
Pick unchanged for the four tiers and the wake contract (X6-14, X6-17); the push list on the node is closed (R16, G12 §4) and a risk alarm on his phone needs his word: Q7. Burn tiers shadow; the incident funnel, graduation, the attention budget and money-both-ways cards come with the agents' jobs. Scores: P1 S3 E1 A3 F3 C2.

#### DP32. The agents' door — core (read, propose, direction, cut-only evidence, the fast loop); the jobs later
Options: (a) at go-live: three surfaces with read and propose live and run through the harness (X7-H01 = X1-H49, H50, H53), a direction on every operation (X7-H02), evidence as a fact the unit's own rule reads, cut only, expiring (X7-H03 = X2-H58 = X5-H31), the effect-bound card (DP7), the LLM-free fast loop (X7-H08 = X3-H60), the protected core (X5-H32 = X1-H52), the kill escalation card (X7-H43); later: the per-agent random de-risker, sealed scenarios, rationale-blind admission, the autonomy ladder, the search ledger, the jobs (X7-H21 to H35), the mini app and the Lab tenancy, evidence contracts per kind; (b) cards only; (c) agents in the fast lane.
- (a) P2 S3 E1 A3 F3 C2: agent evidence reaches the risk layer in minutes without an agent ever sending an order; Steward and I-HITL are controlled tests outside live trading; his ruling that agents have no path to money means the machinery beyond direction and the cut-only fact is not needed for go-live (memory rule, review M1).
- (b) P1 S3 E1 A2 F2 C1: cuts arrive hours late.
- (c) P1 S0 E0 A0 F0 C1: blocked (G2-5).
**Pick (a).** The three fail modes (board open, isolation closed, evidence neutral) show together on the preflight. The agent-trader type name is reserved (his D44), not built.

#### DP33. Agent orders on the node's own demo account — core as a flag
Unchanged: a `foreign` scope in the account numbers (margin and open risk counted at the account, never in a unit); a separate demo account for agents recommended to the build. P1 S3 E0 A3 F3 C1. QMA flag.

#### DP34. Grid, martingale and averaging families — core (preflight check)
Unchanged: refused as sizers by the firewall and the ruin audit (X2-H60 = X5-H22); averaging in survives only as pyramiding with falling risk for trend units, later. P2 S3 E1 A3 F3 C2.

---

## 2. Collisions resolved by the picks

| Collision (layer) | Resolution |
|---|---|
| X0-1, SEEDS replies 6 and 8: 1/N against full size against effective bets | DP9 |
| X0-3, X3-1, X3-2, X4-1: his "about three" and the old breaker against frequency | DP17: money at own percentile enforces; "about three" shadows at the unit's own p90 to p95 run length; the name stays |
| X0-4, X0 Q1: type against cell against dial | DP1 |
| X0-5, X3-10, X4-8, X7-C4: the MIS never switches a unit against isolation on the board | DP23: the guard switches, the board carries, placement is flagged |
| X0-6: brakes first against one rule that is both | DP14: the brake half binds; the accelerator half waits for its card |
| X0-7: breakeven by profit against breakeven when the forecast changes | DP26: off by default, on per unit after the two-arm test |
| X0-9: R fixed at entry (B9 not accepted) | DP11: our call; `net_r` beside R; his reservation stands |
| X0-11: weekend budget scale against crypto as the spine | DP23 |
| X0-12, X2-C01, X5-C5: the gate's undefined bound on a thin record ("too safe") | DP10 and DP15: the holdout's low end sets the start level; a thin record starts at 0.25 and climbs on cohorts |
| X0-14, B13: a three-level daily ladder he called circumstantial | DP22: one portfolio day stop at go-live; burn tiers shadow |
| X0-15, X2-C05, C13: a pilot tier is "$20 a trade" in another form | DP15: the holdout sets the start level; cohorts, not proof, climb |
| X0-16, X2-C10, X5-C3, X3-8: the shipped sizer's inputs and the compiler | DP11, DP12, DP3 |
| X1-1: a profile document against "the unit stands alone" | DP2 |
| X1-2, X1-25: self-configuring at the unit against pooled priors | DP3 |
| X1-3, X1-22: a sizer swap and what a counted try means | DP7 |
| X1-6, X3-11: HALTED must run exits | DP5 |
| X1-9, X4-3, X7-C6: fail closed against fail open | DP23, DP32: three fail modes declared per feed and shown together |
| X1-11, X1 P15, X3-18, X6-1: two state machines on the node | DP5 |
| X1-19, X7-C5, X7-C7: tighten-only automation against the sitting duck | DP20 and Q1; the pair's switch-on path and the dial release (Q4, Q6) |
| X1-23, X7-C10: three layers describe the proposal door | DP32 |
| X2-C02, X3-27: breadth against the minimum lot | DP13: the lot-shed rule; F5 |
| X2-C03, X2-C04: fixed against trailing anchor; house money's home | DP14: portfolio ledger, fixed anchor at go-live |
| X2-C12, X3-14: automatic raises above baseline | DP14, DP20: the rule he approves once, then by proof |
| X2-C13: full size under a parent against breadth-to-budget | DP9 |
| X2-C17, X5-C12, X3-16: two planning edges; FI cuts counted differently | DP10, DP11 |
| X2-C19: calm scaling on stop-sized units | later; cut side only |
| X2-C25: a missing cost cell | DP11: stressed class default, pooled, decays toward measured |
| X3-4, X4-2, X5-C2, X5-C9, X7-C1: automatic steps against his click | Q1 |
| X3-5, X3 Q2: the BMS breaker and the kill switch | Q5 |
| X3-23: automatic restore against restore priced in evidence | DP20: benches by rule; slow-lane demotions by his click |
| X4-5: windowed house money against "keep house money" | DP14: the brake half is on; the accelerator half has a path |
| X4-6, X4 Q1: the floor-hit action | Q4 |
| X4-9: clamps outside the unit against "the unit stands alone" | DP5 |
| X4-10: switch only when flat against the identity table | DP7 |
| X4-15: exits never blocked against venues that block | DP26 item 7 |
| X5-C1: looks, e-meter or wealth as the decider | DP27, DP28: nothing gates the size under baseline; the e-meter governs raises |
| X5-C7: pooled proof against each unit standing alone | later, with the family tag |
| X6-10: agents see the distance to trip | DP32 |
| X6-11: the upside alarm against accelerators | shadow |
| X7-C3: "the sky's the limit" against rationing | DP32: the run surface is unlimited; the queue comes with the jobs |
| X7-C16: expiring evidence against 20-day evidence | DP23 |

---

## 3. Logical flaws across the picks

Found by checking each pick against the others, the ledger couplings, the X4 scenarios and the review's walks. Arithmetic in `working/flaw_arithmetic.py` and `working/review/core_sim.py`.

| # | Flaw | Status | Resolution or what stays open |
|---|---|---|---|
| F1 | The 55 % 1:1 scalper he pictures loses after costs at a 5-pip stop on EURUSD (break-even 58 %). The cut rescues it only if it catches few winners: with half the losers cut at -0.35R the net edge is +0.086R if no winner is ever cut, +0.012R if 10 % are, -0.062R at 20 % (`out-more-arith.txt` E). And the same unit fails DP11's admission gate at k = 2 on a 5-pip stop (gross +0.246R against a 0.32R bar) and passes at 10 pips. | **open** | The frequency thesis needs a cut that catches few winners, proven per unit by the two-arm test before the sizer's growth is believed. If it fails: wider stops (8 to 10 pips passes the gate at k = 2 unstressed) and fewer trades, which is less frequency, not more size. k and the stop width decide whether his scalper exists at all; k is on the numbers lens with this table beside it (Q4). |
| F2 | X2-H01 and X2-H02 could give two sizes if H is not trade rate times days. | resolved | DP9; `flaw_arithmetic.py` C |
| F3 | The sizer needs usable cushion, result spread with cuts, unit count, correlation and a cost cell; today the socket gives equity, entry, stop and record, the balance is read once at sign-in and the sizer uses start plus closed trades. | resolved as a build dependency | DP11, DP12: inputs widened, the guard computes cushion and correlation, a timed balance re-read in part 4's facts, `basis:unmarked` until marked equity lands |
| F4 | The percentile brake has no record to read on day one, and the record holes make live fire rates read both ways (a protection close with no trade row hides a loss; a hand part-close at full size reads high). | resolved by a ladder; holes stay | DP17's fallback ladder; the guard's money ledger reads broker deals; the holes are nobody's PR yet (S/BACKLOG 64, 66) |
| F5 | Splitting across ten correlated units at a small cushion puts each unit below a coarse lot step (cushion near 190 times the minimum-lot risk); with the old picks' 10 % level 1 the book never trades at all (`out-core-table.txt`: 100 % dark). | resolved | DP13: feasibility re-run at anchors, the lot-shed rule, the level floor; the harder sim: 0 to 4 % dark with the rule against 100 % without |
| F6 | The cohort ladder reaches full size in about 100 trades; proof needs 600 or more. | resolved, the other way | DP10 and DP15: the evidence bar is taken out from under the baseline. Cohorts set the speed, the CUSUM steps down, the holdout sets the start, the e-meter governs only raises above baseline and the dial. A unit at full baseline while "unproved" is the design: the baseline is safe at zero edge |
| F7 | The accelerator half of the cushion pair could raise size into the money brake if the two read different ledgers or anchors; the first pass then put the halves on different ledgers. | resolved | DP14: one ledger per pair, the portfolio ledger for both halves; the brake half tapers into the same day stop it reads; `flaw_arithmetic.py` D |
| F8 | Strictest-wins across scopes plus smallest-wins across caps stacks caution to nothing. | resolved, with a meter | DP6, DP19: no scope brake live before shadow precision; the binding clamp named and counted; a cap binding on more than 90 % of trades is a defect |
| F9 | Fail modes disagreed across feeds. | resolved | DP23, DP32 |
| F10 | Automation contradicts his click rulings. | open for him | Q1 and Q1b; the default stated |
| F11 | The picks together choke a healthy unit. | **resolved by the integrated sim** (the first pass's arithmetic counted cohorts only and left out the e-bars; its news and isolation inputs were guesses) | Under the old picks a healthy unit ran at 0.26 of baseline and a weak one at 0.12 (review `out-table-n10.txt`); with the e-bars gone and one reading per scope the core runs healthy at 0.89 to 0.92 and weak at 0.84 to 0.89 with fat tails, gap days, lot rounding and ten correlated units (section 9). The ramp is two or three cohorts from the holdout level. The total choke budget in DP19 keeps it so |
| F12 | The horizon sizer's "0 % floor touches" is partly structural. | open for the numbers lens | the harder sim adds fat tails and gap days and still shows 0 % touches, because size is recomputed from the cushion every morning; intraday paths with size held through the day are still untested |
| F13 | A bench at 23:50 re-arms at 00:00. | resolved | DP17 |
| F14 | Three books on one account net losses but brake separately. | resolved | DP12, DP4 |
| F15 | A world switch carries calibrated numbers but not costs. | resolved | DP15, DP11 |
| F16 | Agent positions on the bound demo account are invisible to every rule. | resolved as a flag | DP33 |
| F17 | Two kill-switch meanings. | resolved | DP5 |
| F18 | Verification and brakes count the same trade differently. | resolved | DP11, DP17 |
| F19 | Herding under the applier. | resolved under fork F-A | DP3 |
| F20 | Banker acts reset every cushion rule. | resolved | DP16 |
| F21 | Deletion-4 would sweep the files this set builds on. | resolved by a claim | DP24, DP25 (five files added this round) |
| F22 | The hours-clause window length has no derivation. | open, shadow | DP21 |
| F23 | The two-tell isolation thresholds have no intraday precision. | open, shadow | DP23 |
| F24 | **The book goes dark far above the floor**: size is proportional to the cushion and never rounds up, so below one lot step every unit skips; nothing re-ran admission as the cushion fell (review M9; `out-more-arith.txt` B: ten 40-a-day units go dark after a 4 % fall from the worked cushion). | resolved | DP13: re-run at anchors, shed by rank, level floor; `out-core-shed.txt` |
| F25 | **The old picks never trade at the worked cushion**: level 1 at 10 % of baseline is under one micro lot, so with lot rounding on the old stack is 100 % dark on every case (`out-core-table.txt`). | resolved | DP15: the start level from the holdout; DP13's level floor |
| F26 | **The portfolio day stop at a multiple of the budget sigma never fires**: the sized book runs at 0.7 to 0.9 of the budget, so even a -3R gap on all ten units is under 1.5 budget sigmas (`out-core-kstop15.txt`: 0.1 fires per 100 days). | resolved | DP22: the stop reads the book's sized day sigma, level-weighted; k is the numbers lens's with the harness's fire-rate column |
| F27 | The e-meter's job was stated three ways (ceiling, display, gate). | resolved | DP10: it governs raises above baseline and the dial; nothing else |
| F28 | B on nominal sizes leaves most of the allowed book swing idle while units are at low levels (one at full, nine at level 1: 1.36 of an allowed 6.08; `out-more-arith.txt` I). | resolved | DP9: level-weighted B at anchors |

Unresolved after this round: F1 (the cut; a per-unit trial), F10 (his), F12, F22, F23 (numbers lens).

---

## 4. Coverage

### 4.1 "What the technical lens must hold" (SEEDS, 55 items)

Unchanged from the first pass except: TLH 11 is held by DP10's gate and starting level, never the amount; TLH 13 (low-edge tolerance) is held by DP10 and DP15 (the holdout level from day one), not by a level-1 earning a little; TLH 18's sweep cap is later and he is told; TLH 22 (the losing-run brake scaled to trade count) is shadow at go-live; TLH 27 (isolation) is shadow at go-live with the scope keys core; TLH 29 (portfolio self-optimisation) and TLH 32 (external code) are later; TLH 42 UI needs stand. No gap.

### 4.2 G12 hand-offs (37 items)

Unchanged: every hand-off has its answer in section 1 (table in the first pass stands; hand-off 22 is now marked "our call").

### 4.3 Facts not carried from G12 in the first pass (review item 19)

- R22 writes the unit's snapshot under `data/deployments/<id>/`; the profile's **status** half (DP2) is that snapshot plus the brake and bench state; the spec half never lives there.
- R17 changes `_admit` and `_leave` with an outbox rule; the profile document travels beside the unit through `_admit`, so the bound click's capability check (DP7) sits there.
- R16 moves the alarm register so an installed node can push; the push list stays closed and "a risk alarm on his phone needs his word": Q7.

---

## 5. The first increment, the forks and the order

### 5.1 The core: twelve parts

Foundation first: a small, complete, solid core that grows on top. 202 ledger variables (205 under fork F-A); the tiers per variable are in `ledger-merge.yaml` section 8. About 25 to 35 builder PRs at the unit build's scale **[judgment]**.

| # | Part | From | Variables | What waits as a plug-in, and where it plugs |
|---|---|---|---|---|
| 1 | Risk profile document: spec and status, embedded at compile, needs list, one pack, `authority` on every number | DP2, DP3 | 12 | suggestions (spec field), stacked packs with combiners (pack manifest) |
| 2 | Presets over four keys: preset, class, instrument, unit; the verification template per type is the preset | DP1, X5-H40 | 3 | seven reserved keys (schema), tags and drop-ins (scope key) |
| 3 | Derivation block on every number, fallback ladder, receipt, guard with freeze; his never-self-tune rows; the authority field | DP3 | 16 (+3 under F-A) | learner bounds, applier modes, herding cap (fork F-A); expressions (derivation block) |
| 4 | Guard: one package, two adapters, `before_order`, one rank table, one fact set (timed balance re-read, open risk at stops, bet keys, budget used); registry row with a shadow switch and a tail or timing class; scope keys | DP5, DP6, DP19 | 19 | the certificate as a gate (report), tag scopes (scope key), QoS lending (portfolio config) |
| 5 | Sizer: horizon formula with level-weighted B over admitted units, reserve, cost denominator with the pooled stressed default, round down, feasibility re-run at anchors with the lot-shed rule and the level floor; the asymmetric basis with `basis:unmarked` | DP9, DP11, DP12, DP13 | 37 | Kelly ceiling binding (shadow row), whole-contract ladders, cushion lending, inverse-volatility allocator, carry (cost record) |
| 6 | The climb and the drift: start level from the holdout, cohorts up, CUSUM one level down, second warning to paper, zones as display, the edge dial released by proof under his once-rule, re-promotion by his click | DP10, DP15, DP27 | 14 | BOIN posteriors, EWOC, pooled family cohorts, the exploration budget, the funded e-process as the confirmation key, the lifetime budget (portfolio config) |
| 7 | Tail brakes enforcing: own-p1 unit bench with a dollar clamp and retry-then-lockout; the portfolio day stop at `all` with the pair's brake half tapering into it; the cushion clip with its reserve; order-boundary clamps; the anchor clocks and the day-boundary contract; house money's accelerator half shadow with its proof card as the switch-on path | DP14, DP16, DP17, DP20, DP22 | 32 | REDUCING, loss points, "about three", density, chorus, burn tiers (all shadow rows); probes, memory ceiling, earned restore (restore row); shed classes, de-gross (portfolio config); the ratchet (portfolio config) |
| 8 | Exit socket step 2 (per-bar exits fed position facts), the disaster stop on every live order, the cut as a counted two-arm trial from the winners' MAE, thesis FI with a price backstop, exit families as defaults, trade row with mechanism and `net_r`, exits never blocked | DP26, DP11 | 14 | step 3 (trails, partials, the signed stop) once R21's block lifts; the six refused exits (catalogue, shadow); breakeven (exit family) |
| 9 | SQS gate as a real slice inside the guard with its baseline producer and eight derived rows; the news window on scheduled releases, entries only, both FX legs; kill-level effects; scope keys in the stand-down table; unknown is not calm; the one-tap escalation card | DP5, DP23, DP24, DP25 | 16 | class isolation enforcing (shadow rows), measured impact and driver tags beyond currency (window learns), macro, agent evidence kinds |
| 10 | RiskState row every pass, the six words and UNKNOWN, closed reason codes, meters for the core brakes, motion receipts, the passport strip, the safety display, the morning card, four alert tiers and the wake contract (push list pending his word) | DP30, DP31 | 10 | the other observability parts (UI), incident funnel, attention budget, scorecards (shadow) |
| 11 | Machine check in a week against the twin, one bound click, pinned versions with the migration map, two records, world-switch reset, the preflight with the firewall | DP7, DP28, DP34 | 16 | the 22-part proof path, canary, challenger, funded gate, trust ladder and outside code (loader signature) |
| 12 | Light harness over the ledger rows: sizing and brake replay, the integrated sim, three cases, the dry chassis, the mandatory scenario block, the scorecard with survival gates and the total choke budget; agents read and propose through tool rows with a direction on every operation and cut-only evidence; the fast loop never waits for a model | DP19, DP29, DP32 | 13 | engine import (conformance test), sealed set, reverse stress, the agent jobs, the mini app, the Lab tenancy |

Why this is complete and not thin: it answers "how does it self configure" and "what if I want to change the way it is derived" (part 3); it holds "no key setting blank" (part 3); it holds "brakes first" with brakes that enforce on day one (part 7); it keeps house money (part 7); it meets "must go live" (parts 8, 9, 11); it is extensible because a new brake, sizer base or scope is a registry row plus a scope key (parts 1 and 4), and the document already carries the fields the full loop needs.

### 5.2 The cut-only factors that bind at go-live, against April's fifteen (review M3)

April had nine multipliers and six caps (G3). The review counted about 39 cut-only factors in the first pass. At go-live each factor below either earns a job no other does or leaves the binding path. **Binding: 15.** One running loss is read once at each scope.

| # | Factor | Kind | The job no other factor does |
|---|---|---|---|
| 1 | cost denominator (stop plus round trip plus stressed slippage) | multiplier | charges the real cost of the trade before it costs anything |
| 2 | correlation share (B over admitted, level-weighted units) | multiplier | keeps the book's swing fixed when units are added |
| 3 | the level (holdout start, cohorts up, CUSUM down, world-switch reset) | multiplier | the only reader of the unit's edge stream |
| 4 | the unit's own-p1 bench with retry-then-lockout | trip | the only reader of the unit's running loss; the tail at unit scope |
| 5 | the pair's brake half tapering into the portfolio day stop | multiplier then trip | the only reader of the book's running loss; reverse house money |
| 6 | the lot-shed rule | portfolio multiplier on N | the only rule that raises survivors' size when the cushion falls |
| 7 | the cushion clip with its reserve | cap | the only account-level bound on worst case at the stops plus gaps |
| 8 | the bet key cap | cap | the only rule that counts one bet once across units |
| 9 | the order-boundary veto with the size sanity band | cap | the only check of the actual order against the per-trade cap and the unit's usual lots |
| 10 | margin headroom | cap | the only reader of margin; stops the broker's close-out |
| 11 | lot round-down and skip | mechanics | never rounds up |
| 12 | the SQS gate | gate | a ruling; the only reader of the live spread against its baseline |
| 13 | the news window | gate | the only reader of the calendar |
| 14 | the admission gate (low end positive after costs, per hour) | gate | the only go/no-go on the band |
| 15 | world and version resets | reset | the only rule that reads a switch |

Not binding at go-live (shadow rows, would-have journalled): REDUCING at own p10, loss points, the count brake, the two-key halve, AIMD, the burn permit, chorus, the methodology CUSUM, the Kelly ceiling, the memory ceiling and level lock beyond retry-then-lockout, class caution and isolation, the weekend scale, the macro governor, calm-volatility cuts, the hourly cost nomogram, agent cuts (the fact is wired; no agent files yet), the e-bar under baseline (dropped). The total choke budget (DP19) is the harness test that keeps the fifteen from stacking: a healthy unit under 0.75 of baseline in the integrated sim is a defect that blocks shipping.

### 5.3 The forks for the arena

Shapes A, B and C of the first pass are withdrawn: A against B is one layer and C is a build order (review M12). The real forks the architects build competing versions of:

- **F-A. The applier with modes against refresh at anchors.** Both carry the derivation block and the `authority` field on every number. (a) a learner publishes a target with bounds into status and an applier moves the value only in the number's mode (`off`, `at_flat`, `at_period_open`, `live`), with a retune share cap; (b) every derivation is recomputed at the anchor and applied at the next, with `authority` holding `off` or `at_anchor` only. What makes (a) win: numbers that must move between anchors (a cost cell after a broker change) and a herding guard that is measured; what makes (b) win: fewer parts and no motion between anchors to explain, at a cost of a day's lag on every learned number. The harness runs both on X4-39 (the broker changes its costs) and X4-60 (slow decay).
- **F-B. Brakes in one guard package against halt slots inside the compiled unit.** (a) the guard computes the facts and runs every brake above the position (DP5); (b) the guard computes only facts and feeds them into the unit's halt slots, so the unit stands alone for its own brakes and the guard holds only the portfolio ones. What makes (a) win: one place for the rank table and backtest-equals-live for every brake; what makes (b) win: a unit that carries its brakes between hosts without a guard version. The constraint: today halts in logic slots are refused as `binding_not_read` because they read account and trades ports (R05), so (b) needs the compiler to feed those facts.
- Not a fork: the evidence ladder against cohorts plus drift step-down. The lead's call 2 and the sims decide it (DP10, DP15).
- Not a fork, a sub-choice: where the exit rank lives (the compiler's slot order or the guard's safest-wins); the architects decide it inside F-B.

### 5.4 Build order, on landed repair tips only (review item 22)

1. Exit socket step 2 and the trade row with mechanism and `net_r` (part 8). F1's two-arm trial needs it first.
2. Guard facts: timed balance re-read, open risk at stops, bet keys; RiskState (parts 4, 10).
3. The sizer socket with its compiler refusal lifted; the profile document and presets (parts 1, 2, 3, 5).
4. Tail brakes and the portfolio day stop; the climb and the CUSUM (parts 6, 7).
5. SQS and news first slices; kill-level effects; scope keys (part 9).
6. The light harness and the integrated sim as its first job; the total choke budget test (part 12).
7. Machine check, the bound click, two records (part 11).
8. Shadow rows for every timing brake; the morning card and the wake contract (parts 7, 10).

### 5.5 What he must be told at go-live

- On and binding: the fifteen factors above; the unit bench and the portfolio day stop are the two brakes.
- Shadow, measuring, not binding: class isolation; REDUCING; loss points; his "about three" (at the unit's own run length, 5 to 10 losses, not three); chorus and burn tiers; the Kelly ceiling; the accelerators.
- House money: the brake half (his reverse house money) is on from day one at portfolio scope; the press after wins switches on by itself when the unit's own trades pass its card, under the rule he approves once (Q4).
- The sweep cap he asked about twice: not at go-live; it returns later as a ratchet at the portfolio, a trade-off against idle money.
- R stays gross with `net_r` beside it: our call; his B9 reservation stands.
- The floor and buffer are fixed at go-live; nothing raises them by rule.
- His phone: the push list on the node is closed; the three pushes in Q7 need his word.
- The weak unit: starts at the level its holdout earns, not at a tenth; drift watches it down.
- A scalper at a 5-pip stop may not exist after costs unless its cut catches few winners (F1); the harness's first trial says.

---

## 6. Questions for him

Filtered against SEEDS and the rulings. Each has the recommended answer and the default the work proceeds on. Nothing blocks on him. The old Q7 (outside code) is later; the old Q2 vocabulary question is folded into Q8 as structure.

| # | Question | Kind | Recommendation | Default while open |
|---|---|---|---|---|
| Q1 | May a unit step down (a CUSUM warning drops one level; a second warning inside 500 trades moves it to paper at a planned look, never on one day) and come back (a bench clears after its rest with retry-then-lockout; a level climbs on clean cohorts) **by rule**, and may a confirmed class isolation apply in `no_new_entries` mode with a time to live, so that only HALTED, lockouts, the kill switch, promotion and raises above baseline wait for your click? This restates ruling 2 by direction. | irreversible scope | Yes. | Yes, journalled with its cause |
| Q1b | May a rule **close positions** by itself (the cushion clip reducing at the buffer; the de-gross before a broker's close-out), or only stop new entries, with closes left to the kill switch and your hand? | irreversible scope | Entries only at go-live; automatic reduce after the harness shows its loss saved. | Entries only |
| Q2 | Does QMB's proof set the **starting level** (a proved unit starts at half its safe size and climbs on cohorts; drift watches it down), rather than every unit earning its way up from a tenth over months? | scope (the sitting duck) | Yes. The old way holds a weak real edge at a tenth of its safe size for over six months. | Yes |
| Q3 | May a unit go live at its holdout level **while proof continues**, with the packet saying "proof pending, 212 of 610 trades, level 0.50, expires on this date", after one week of machine check in paper? If no, paper runs for months for most units. | irreversible scope | Yes. The click still approves one hash at one level on these markets. | Yes |
| Q4 | **House money at go-live**: the brake half (your reverse house money) binds from day one at portfolio scope; the accelerator half switches on by itself when the unit's own record passes its card, under a rule you approve once. Is that acceptable, and do you approve the rule once now? | vocabulary he cares about (A21) and a once-rule | Yes to both. | The brake half binds; the accelerator half stays shadow until you approve the once-rule |
| Q5 | When the **portfolio day stop** fires, may it raise the kill level itself (YELLOW at `all`, which only you lower), or only stop entries until the next anchor and land a one-tap escalation card? | irreversible scope | Stand-down and card. | Stand-down and card |
| Q6 | After proof, may the **edge dial** move from `zero` to `low` by rule (size rises above the zero-edge baseline for a unit whose e-meter has crossed its bar), under a rule you approve once, or by a card each time? | once-rule | By rule, with a card telling you. | Card each time until you approve the rule |
| Q7 | The node's **push list** is closed. May the build add three pushes: portfolio day stop fired; stop not at the venue after escalation failed; node unreachable with open positions? At night, wake you only when money is at risk, the system cannot fix it and your action changes the outcome before a deadline; otherwise the morning card? And while away: no new entries once flat (benches still clear by rule), or trade on at the holdout level under every brake? | scope | Yes to the three; wake contract as stated; absence policy dark-after-flat. | Ask the build for the three; wake contract; dark after flat |
| Q8 | **After go-live, a structure question**: keep the Book and BMS as documents (the Book path code stays, 5,951 lines plus up to 4,732), or replace them with cluster tags and one portfolio config (a unit in several clusters at once, one floor)? The harness tests both on the losing-together scenarios first; the words on screen can stay either way. | irreversible scope, later | Tags, if the harness shows driver clusters catch co-loss the style Book misses. | Not asked until after go-live; the first increment has one portfolio config and no cluster level |

**Numbers lens, when he gets there (not questions now):** the floor-touch tolerance; the survival horizon in days; the first floor and buffer; the ratchet share; k for the portfolio day stop and k for the admission gate (with F1's table); the cut size per unit; the floor-hit action (stop the pot, or one feasible micro unit at the holdout level); cards per day.

---

## 7. What this set leans on that is not proved

- No money brake has run on QMX's own trade streams; every fire rate is a model floor.
- No fills exist; every cost cell starts synthetic; the demo-to-live gap is unmeasured until the first live week.
- The horizon sizer has model sims only; intraday paths with size held through the day are untested (F12).
- No paper tests a fractional early cut after costs (F1), breakeven after costs, intraday persistence after costs, or a fund switching a class off by rule.
- The applier, the guard, the exit socket's steps 2 and 3, marked equity, the commission key, the RiskState row and the harness engine do not exist (G12 item 3).
- Everything above `R06` in the repair stack is unreviewed or unmerged.
- The harder sim (section 9) is one model with 60 paths per cell; its medians move by a few percent between runs and it does not model intraday re-sizing, serially correlated results, margin, or the demo-live gap.

---

## 8. Review response

Each item of `REVIEW.md`: accepted, partly accepted, or rejected, with where it landed.

**Must-fix.**
- **M1 (did not narrow): accepted.** Tiers on every hybrid and every variable (`HYBRID-FATES.md`, `ledger-merge.yaml` section 8); the core named in section 5.1 with its part count and variable count; cut-only factors counted in 5.2. The review's twelve parts stand with two corrections: part 3 keeps self-configuring as a fork rather than cutting the applier (the lead's call 6); part 7 keeps house money's pair with the brake half binding (the lead's call 5).
- **M2 (the evidence ceiling): accepted.** DP10, DP15, F6, F11 rewritten; X5-H13 dropped under the baseline; the holdout sets the start level; the e-meter governs raises and the dial only. The harder sim repeats the review's direction with fat tails, gaps, lot rounding and ten units: the e-bars halve a healthy unit's size and quarter a weak one's (section 9).
- **M3 (the cut-only stack): accepted.** Fifteen binding factors against April's fifteen, each with its job, in 5.2; one reading per scope; the total choke budget as the shipping test. Partly: the review's "one reading" is read per scope (unit and portfolio each read their own ledger once), because the unit bench and the portfolio stop protect different things; at N = 1 they are one trip.
- **M4 (F1 and DP11): accepted.** F1 is open with the winner-cut table and the gate table; k goes to the numbers lens; the fallback is stated.
- **M5 (no brake may enforce on day one): accepted.** Tail and timing classes on the registry row; the certificate is a pooled report; DP19 rewritten; `ledger-merge.yaml`'s "compile requirement" note replaced.
- **M6 (the portfolio stop): accepted.** DP22; part 7; enforcing from day one with an expiry at the next anchor; class isolation shadow and he is told (5.5). F26 adds what the harder sim found: the stop must read the sized day sigma, not the budget sigma, or it never fires.
- **M7 (go-live blocks): accepted.** The paper e-bar struck (DP15, DP28); live trades on the pooled stressed default with `cost:uncalibrated`, a cell refusing only after fills show net edge below zero (DP11).
- **M8 (house money): accepted.** One ledger per pair, the portfolio ledger for both halves (DP14, F7); he is told plainly (5.5); Q4 asks the once-rule. Partly: "off until proof may mean off for good" is answered by the switch-on path from the unit's own record, not by a permanent off.
- **M9 (the dark book): accepted.** DP13, F24, F25; feasibility re-run at anchors, the lot-shed rule, the level floor; simmed in `out-core-shed.txt`.
- **M10 (cherry-picked numbers): accepted.** DP17 reports all five units and scores P1; DP20 scores E1 and attributes "902R of 950R" to the CUSUM policy; the picked restore is now simmed; the brake's job is stated as the tail.
- **M11 (settled claims): accepted.** The portfolio stop and the kill level is Q5; the sweep answer is told (5.5); R is "our call" (DP11); "about three" at own p90 to p95 for a halve, shadow, and he is told what three became (DP17, 5.5).
- **M12 (shapes): accepted.** Shapes withdrawn; one first increment fully listed (5.1); forks F-A and F-B for the arena (5.3); the Book against tags is Q8 as structure after go-live. Partly: the review's third fork (the evidence ladder against cohorts) is not offered as a fork because the lead's call 2 and both sims decide it.

**Should-fix.** 1 (E scores): accepted; every E rescored against the rubric, software patterns at E1 with "no trading test", DP19 at E2 with the 97-trade note. 2 (P on meters): accepted; DP19, DP29, DP30, DP31 at P1. 3 (omissions): accepted; the 668-trade spacing and the 54.5 % bad-week alarm in DP18, the 30 to 42 % half-cushion figure in DP9, the 68.5 % at 2 a day in DP18. 4 (guessed inputs): accepted; F11 now rests on the integrated sim, the guesses retired. 5 (level-weighted B), 6 (N is admitted units, weekly, never up under a caution), 7 (rate floored at the card's): accepted in DP9 and F28. 8 (the window clock while benched): accepted, DP20. 9 (ratchet against the floor): accepted; the floor fixed at go-live, the ratchet later with the base floor split from the lock line (DP16). 10 (one size step): accepted; levels only, the halve is shadow (DP17). 11 (F4's direction): accepted, both directions, broker deals. 12 (DP12's fallback): accepted; the balance re-read is counted in part 4's facts. 13 (automatic closes): accepted as Q1b. 14 (the dial after proof): accepted as Q6 and DP10. 15 (survival days): accepted; a derivation row under Q4's list. 16 (twelve picked without a DP): accepted; each now has a tier and a plug point in `HYBRID-FATES.md` (multi-position units later because `position_limit` above one refuses today; slot optimising later; the node lease a flag). 17 (eleven keys): accepted; four at go-live, seven reserved (DP1). 18 (how the MIS adjusts): accepted, one line in DP5. 19 (G12 facts not carried): accepted, section 4.3 and Q7. 20 (SQS as a real slice): accepted, DP25 and part 9. 21 (the claims list): accepted; five files added in DP24 and DP25; the handoff file is the lead's to extend. 22 (build order): accepted, 5.4. 23 (the questions): accepted, section 6 rewritten with the review's seven added and the old ones split or retired.

**Rejected or corrected, with evidence.**
- The review's "true core" cuts learner bounds and applier modes with no loss. **Rejected as a cut; kept as fork F-A.** His words make self-configuring the heart of the ask (A3, D46), he welcomed the Kubernetes model (STATE item 29), and the document's `authority` field and derivation block make either branch reachable without rework; the cost is three variables (`ledger-merge.yaml` 8).
- The review's "cut with no loss: trust ladder and the raw-code hatch". **Accepted for go-live, not as a drop:** his D43 asks for external code; it is a plug-in behind the loader's signature check (DP8).
- The review's core part 6 says "second alarm to paper" with no window. **Corrected:** inside 500 trades (X5's spacing), or two CUSUM warnings a year apart would demote a healthy unit.
- The review's claim that the first funnel's house money pick "has no home in C". **Accepted for C; the fix is the portfolio ledger, which exists in the first increment, not a cluster ledger.**
- The review's figure of "about 39" cut-only factors. **Not contested;** the count that matters is the binding count at go-live, now fifteen.
- The review's `stack_sim.py` reads every pick in its milder form and has no lot rounding; with lot rounding on, the old picks do not trade at all at the worked cushion (F25). This strengthens the review's direction rather than weakening it.

---

## 9. The harder sim: what still holds and what breaks

`working/review/core_sim.py` extends the reviewer's `stack_sim.py` with fat tails (1.5 % of losses are -3R), gap days (2 % of days every unit's first trade is -3R at once), lot rounding at a $0.50 step with skip, the lot-shed rule and the level floor, five and ten correlated units (ρ 0.3 through a common draw), costs at 1x and 1.5x (the card still believes 1x), the portfolio day stop with the pair's taper, the core's climb (holdout start, cohorts, CUSUM), the unit bench with retry-then-lockout, and the dial released by proof. Same worked example as the review ($500, $300, eps 1 %, 20 days, 10 trades a day, FI scalper outcomes). 60 paths per cell, 120 days. **Model numbers only.** Outputs: `out-core-table.txt`, `out-core-shed.txt`, `out-core-kstop15.txt`, `out-core-attrib.txt`.

**Holds.**
- The direction of the review: the e-bars under the baseline halve a healthy unit's size (0.92 to 0.45 at N = 1, 0.90 to 0.49 at N = 10) and quarter a weak one's (0.89 to 0.23, 0.84 to 0.22), at every N and both cost levels.
- The core keeps a healthy unit at 0.89 to 0.92 of baseline and a weak one at 0.84 to 0.89, with the climb done in two or three cohorts; medians at N = 10, cost 1x: healthy $5,553 against the bare sizer's $6,625, weak $803 against $1,010.
- Survival: 0 % floor touches in every cell. On the bleeding unit with an overstated card the bare sizer loses half the cushion in 97 to 100 % of runs; the core in 0 % (N = 1), 18 to 28 % (N = 5 and 10). At cost 1.5x, where the healthy unit's true edge is +0.02R and the weak one's is -0.03R, the bare sizer loses half the cushion in 38 to 100 % of runs across the cases; the core in 0 to 43 %. The old picks lose nothing because they never trade (next line).
- Lot rounding: the old picks' level 1 at 10 % of baseline is under one micro lot, so with rounding on the old stack is 100 % dark in every case (F25). The core with the lot-shed rule and the level floor runs 0 to 4 % dark at $0.50, $1 and $3 steps; at a $3 step it does so by running one or two units at 0.70 to 0.76 of baseline (`out-core-shed.txt`).
- Attribution (`out-core-attrib.txt`): the start level from the holdout alone leaves the unit at 0.46 of baseline until the cohort climb takes it to 0.92 to 0.95; the CUSUM, the bench, the day stop and the taper each cost one to three points of size on a healthy unit; the dial by proof returns the unit to about 1.0.

**Breaks or stays open.**
- The portfolio day stop at a multiple of the budget sigma never fires (0.0 to 0.1 fires per 100 days even at 1.5 sigma), because the sized book runs at 0.7 to 0.9 of the budget and a -3R gap on all ten units is under that (F26). The pick now reads the sized day sigma; the numbers lens sets k with the fire-rate column beside it.
- At N = 5 and 10 the core's drift brakes are slower than at N = 1: the overstated and bleeding cases lose half the cushion in 18 to 43 % of runs at cost 1.5x, against 0 to 2 % at N = 1. Each unit's CUSUM needs its own trades, and ten small units lose together before any one of them alarms. The portfolio stop that reads the sized sigma and the pooled family CUSUM (shadow at go-live) are the answers to test next.
- The dial by proof is inside the noise at 60 paths: it raises average size to about 1.0 of baseline and moves medians both ways (healthy N = 1: $1,233 against $1,763; N = 5: $5,603 against $3,856). More paths before anything is claimed.
- Not modelled: intraday re-sizing, serially correlated results, margin, the demo-live gap, news and SQS windows, class isolation. The structural "0 % touches" caveat (F12) stands.
