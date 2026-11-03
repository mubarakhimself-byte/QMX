# X2 problem solving (bmad-cis-problem-solving, run headless in YOLO)

Run 2026-11-03. Each open problem in the X2 layer goes through the workflow's steps in short form: refined statement, is / is not, root cause (five whys), forces, then solution options. The options and their trade-offs are written out in full in `expansion/X2-sizing-accelerators.md` §2 (same PS numbers). This file keeps the diagnosis. No option is picked here; the funnel judge picks. Opinions are marked **[judgment]**.

Methods used: Problem Statement Refinement, Is/Is Not, Five Whys, Force Field, Constraint Identification, then Morphological Analysis and Assumption Busting for options (the brainstorm's memlog holds the generation).

---

### PS1. Risk per trade has no derivation
- **Refined:** every generation set risk per trade by hand (0.5 %, 0.8 %, $42.86 per R, 8 %); the ledger has no derivation for it, and the shipped sizer reads a placeholder.
- **Is / is not:** it is a missing formula and missing inputs; it is not a missing number (numbers existed and "carry no weight", SEEDS D29).
- **Five whys:** why blank? Configurable meant "type it" → nobody owned how it was derived → the sizer only sees equity, entry, stop and the record (G8 §1.4) → no input carries the cushion, costs, correlation or the floor tolerance → so no formula could use them.
- **Forces:** for: his D46 ("change the way it is derived"), ledger v0, R7's VPA pattern. Against: compiler refuses sizer-bound moving numbers; costs and marked equity are not available as facts.
- **Real constraint:** the sizer's input list. **Assumed constraint:** that the derivation must use the edge.

### PS2. Edge-led against frequency-led sizing
- **Refined:** the lead's "twice the edge, twice the size" and his "total day capital split across units" are two bases; he rejects leaning on the edge (A24) and read "ten units each full size" as a contradiction (C29).
- **Is / is not:** a basis choice and a breadth formula; not a numbers question.
- **Five whys:** why the clash? Both views use one-unit maths → neither counts correlation and edge error at once → the split is safe but wastes breadth, full size grows but dies when the edge is wrong (lead's 11:07 sim) → no derivation sits between them.
- **Forces:** for: the fundamental law (A1-105), A1-087's three answers. Against: correlation is unmeasured; the edge is a guess.

### PS3. Costs never reach the sizer
- **Refined:** no cost input on the socket, no commission key, slippage unmeasured (G7 §4.3, G6 §5.4).
- **Root cause:** QMB built the ports with every rate deferred (GAP-0048); the sizer contract predates his A11 ruling.
- **Constraint:** measured costs need fills; day one has none.

### PS4. Which equity series the sizer reads
- **Refined:** "5 % drawdown" meant four things across generations (G11); the halt blocks assume marked equity no host supplies; cTrader equity is read once at sign-in.
- **Root cause:** no row declares its series and base (A2-115).

### PS5. Accelerators have no proof
- **Refined:** R9: with independent trades no accelerator beats a constant of the same average risk; persistence in intraday retail strategies after costs is unmeasured.
- **Root cause:** accelerators were designed as multipliers, never as tested claims with a control.

### PS6. Accelerators can drive size into a trip
- **Refined:** old house money and reverse house money read different signals, so a day could be both pressing and braking; nothing remembers the trip level.
- **Root cause:** no shared ledger, no raise permission, no settle rule (R9 §3.4).

### PS7. Where house money lives, and correlated wins
- **Refined:** unit, Book or BMS is open (C5); one USD move can fire house money on five units (A3-195).
- **Root cause:** house money was a per-slot multiplier with no event window and no book cap.

### PS8. Minimum lots at small equity
- **Refined:** at $500 many derived sizes are below one lot on gold, index futures, energy; April rounded up silently, the Book door refuses inexact sizes.
- **Root cause:** rounding is treated per trade, never as admission or as an average over trades.

### PS9. Demo sizes from the demo balance
- **Refined:** a paper unit on a $10,000 demo sizes from $10,000 (G9 §3.1); DOCS freezes a paper balance "for data-collection realism".
- **Root cause:** the deployment carries no budget share.

### PS10. New units: too safe or too risky
- **Refined:** LCB Kelly gives zero size for about 1,100 trades (sitting duck, A14); point Kelly on a paper record is 15-30x the old caps (G3).
- **Root cause:** both tie the amount to the edge estimate.

### PS11. Normalising risk across classes
- **Refined:** pips × lots is wrong on gold, index CFDs and crypto; tails and gaps differ by class; ATR is not book risk.
- **Root cause:** one risk unit was asked to do three jobs (routine size, stress loss, feasibility).

### PS12. Growth over 24 hours, sweeps and restarts
- **Refined:** per-cycle caps clash with 24-hour, multi-instrument trading (B5); the sweep cap is unanswered (C12); a unit-level sweep removes the unit's cushion (A2-077).
- **Root cause:** one day boundary and one cycle for every scope.

### PS13. What a size level is in dollars
- **Refined:** X5 says which level; nobody says what a level is (X5 collision C4).
- **Root cause:** levels were designed as a proof device, not a sizing device.

### PS14. The shipped sizer contract and compiler
- **Refined:** the sizer reads equity, entry, stop and record; a sizer-bound number cannot move; the receipt is hard-coded (G8 §1.4, §3.10).
- **Root cause:** the unit build kept risk as placeholders by design (STATE note), so this is expected, not a fault.

### PS15. FI cut sizes in the sizing maths
- **Refined:** every number shown assumed full-size losses (A9, three times).
- **Root cause:** trade rows cannot tell an FI cut from a time exit (G11), so no record carries the cut distribution.

### PS16. Self-configuring sizing numbers without overfitting
- **Refined:** QMX has a learner (motion engine) and no applier; authority is parsed and never read (R7).
- **Root cause:** no mode, bounds, guard or freeze for sizing inputs.

### PS17. Multi-position units stacking one bet
- **Refined:** a unit may hold several positions (A8); each sizes from whole equity; no cross-unit exposure exists.
- **Root cause:** no bet key and no unit total cap.

---

**Force field across all seventeen [judgment]:** the strongest driving force is that almost every missing piece is an *input* to the sizer, not a new mechanism; the strongest restraining force is that the inputs (costs, marked equity, FI cut sizes, correlation) are facts nobody measures yet. So the order of work that unblocks most is: facts first (costs, marked equity, exit reason on trade rows), then the sizer contract, then derivations, then accelerators.
