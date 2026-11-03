# Expansion round: common brief

Every expansion agent reads this file first. Your own prompt names your layer.

## What this round is

QMX is a trading system. The operator, Mubarak, is not technical and not a trader. He is building the risk management and position sizing part last, because it is the heaviest: many variables, and each one affects others.

His method for this round is **expand, then funnel**. You are in the expansion. Widen your layer as far as it honestly goes. Later a separate funnel step will cluster, dedupe, resolve collisions and pick.

- Do not converge.
- Do not stop at a top few ideas.
- Your starter questions are starters, never the scope.

His goals, in short:
- **Origin.** The Hummingbird Project. He cannot win on speed, so he wins on how risk and sizing compound over time: many small bets, around the clock, across many markets and instruments.
- **The system carries the load.** Risk and sizing should make even a weak but real edge pay consistently. Sizing must not lean hard on one edge number; treat the edge as a range.
- **A template, not fixed numbers.** The risk-and-sizing template must:
  - work out of the box with self-configuring defaults, each with a reason;
  - extend in any way (he compares it with n8n and with white-label software);
  - let agents and the copilot create new versions of it.
- **Levels.** Risk works at several levels: trade, unit, book (cluster), methodology, portfolio (BMS) and account.
- **Brakes first, accelerators second.** Exits are never blocked. The kill switch and SQS (the spread sensor) stay.
- **Live money.** This version must go live with no key setting blank. The total seed is $500.

## Read first

All paths are in `D:\QMX-worktrees\risk-plan\tracker\risk-core\`.

1. `seeds\operator-words-2026-11-03.md`, his words of 3 Nov, M10 to M17 (verbatim).
2. `seeds\SEEDS.md`, the register of his 157 asks, each tagged T (technical), N (numbers) or T+N. Read in full:
   - "What the technical lens must hold";
   - "His replies to the 1 Nov answer";
   - every item for your layer.
3. `STATE.md`, "RESUME HERE".
4. Grounding:
   - what exists and what history holds: `grounding\G1`-`G11`;
   - outside research: `research\R1-platforms-risk-sizing-extensibility.md`, `research\R2-trader-practice-windows-drift-isolation-breadth.md`, `research\R3-edge-verification-and-analogues.md`.
   - Read the ones your prompt names closely; skim the rest.
5. The ledger: `ledger\variables.yaml`, `ledger\README.md` and `ledger\check.py`, if they exist yet. Version 0 is being built in parallel.

The shipped unit stack is at `D:\QMX-worktrees\bld-us-c13`, commit d02af358. Its plan is `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\build\UNIT-PLAN.md`. Read code only to check a claim; G8, G9 and G11 already map it.

## Facts every agent must hold

All of these are established in the grounding.

**Edge and frequency** (sims in `grounding\sims\`, R2, R3):
- "Same floor odds for many units" holds only when the edge is as believed and the units are independent.
- At half the believed edge, ten full-size units touch the floor far more often than one.
- Splitting one size across units protects against a wrong edge.
- Proof costs trades, and the cost grows with one over the edge squared. 55% at 1:1 needs about 610 trades; 52.5% needs about 2,470.

**Brakes** (G9, G10, G11, R2):
- Count brakes fire on healthy units by chance as the trade count rises. "2 full stops a day" fires on 61% of days at 4 trades a day.
- The old breaker counted full stops only.
- Fast invalidation (FI) never existed in code, and trade rows cannot tell an FI cut from a time exit.

**The shipped stack** (G8, G9, G11):
- The unit has slots for a sizer, exits and halts. The compiler refuses halts and readings.
- The sizer gets only equity, entry, stop and the instrument record.
- Nothing runs halts.
- No cross-unit exposure measure exists.
- Observability reports health, not risk.

**Exits** (G3, G11):
- The old "dynamic SL/TP" moved the stop to breakeven once at +1R and extended the take-profit.
- Today's code runs none of it.

## Ledger additions (required)

Every variable you introduce or rely on goes into your own file, `ledger\additions\<your-file-id>.yaml`.

- **Schema.** If `ledger\README.md` exists, follow its schema. Otherwise use this one:
  - `id`, `name`, `level`, `kind`, `measure`;
  - `applies_to` (classes, styles, timeframes);
  - `default` and `derivation` ("open" when unknown);
  - `inputs`, `affects` (with direction and how);
  - `configurable`, `changed_by`;
  - `status` (proposal or idea for new ones);
  - `sources`, `seed_ids`, `notes`, `open_questions`.
- **Existing variables.** Reuse an existing ledger id where one exists. Don't redefine it.
- **Run the checker** if it exists: `uv run --no-project --with pyyaml python ledger\check.py ledger\additions\<your-file>.yaml`.
- **Expect growth.** The ledger grows through expansion. That is expected, not a problem.

## Your expansion document

Write `expansion\<your-file-id>.md` with these parts:

1. **Ideas.** Number every one: `<your-file-id>-01`, `-02`, and so on. For each:
   - what it is;
   - why a trader would want it;
   - how it would work;
   - the ledger ids it touches;
   - its sources (grounding refs or new ones);
   - your maturity tag: solid, plausible or wild.
   - Keep wild ideas. The funnel decides.
2. **Problems and proposed solutions.** He wants agents to solve issues, not list them. For every open problem in your layer, give at least two solution options with their trade-offs.
3. **Collisions noticed.** Where your ideas clash with each other, with another layer, with his words or with the grounding. Name them; do not resolve them.
4. **Questions only he can answer.** Money, vocabulary he cares about, irreversible scope. Keep this short; research technical questions yourself.

## Skills

Run them non-interactively. No human is available, so you play every role and never wait for input. Skill files live in `C:\Users\Mubarak\Desktop\QMX\.claude\skills\<name>\SKILL.md` and `C:\Users\Mubarak\.claude\skills\<name>\SKILL.md`. Your prompt names which skills to use.

## Rules

- **Files.** Read-only everywhere except your two output files. Never commit. Never touch other worktrees' files.
- **Agents.** Do not spawn subagents of your own.
- **Money and secrets.** Agents never touch money, and only he promotes a unit to live. Never print keys or tokens.
- **Web.** Use web search only to find URLs. Read pages with the built-in browser tools when you have them. Mark anything seen only as a snippet. Firecrawl is out of credits. Do not search for his own strategy sources.
- **Arguments.** Do not use luck as an argument.
- **Writing.** Plain words, short sentences. No codenames without saying what they are. Mark your own opinions **[judgment]**.
- **Commands.** Time-limit every command you run.

Return a summary of at most 15 lines: idea count, problems solved with options, ledger additions, the three strongest ideas and the worst collisions.
