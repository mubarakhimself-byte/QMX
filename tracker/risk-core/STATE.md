# Risk core: state

Branch `plan/risk-core` (worktree `D:\QMX-worktrees\risk-plan`), cut from `plan/unit-system` at 09d36ab7. The old local branch `plan/risk-sizing` (at main c3e8ec5e) is stale and was left untouched.

## RESUME HERE

1. Grounding DONE 2026-11-01: G1-G5 in `grounding/` (G5 is the timeline), sims in `grounding/sims/`. Next: find the clean starting point with him, then design by scenarios.
2. Grounding files land in `grounding/`:
   - G1 operator sessions ("Risk & sizing QML redesign", "Agent team for MT5 article analysis", plus the 10-05 and 10-13 sessions they carried)
   - G2 the unit-plan risk state (rulings, risk socket, placeholders)
   - G3 the old system (QMX-discussion)
   - G4 the current Book and BMS (docs, `_docwork`, GitBook/node docs, shipped code)
3. After grounding: build a timeline of how his risk/sizing thinking evolved (`grounding/G5-timeline.md`): QMX-discussion (old system) → the 10-05 and 10-13 sessions → "Risk & sizing QML redesign" (10-15 to 10-20) → "Agent team for MT5 article analysis" (10-20 to 10-29) → the unit-plan risk pack (10-27 to 11-01). For each stage: what changed, what was dropped, and why. The timeline is for the lead's own understanding; report it to him only briefly.
4. Landscape given (opinion on both systems). His backstory and first takes are below (2026-11-01). Scenario maths started: `grounding/sims/freq_vs_size.py` (bigger bets vs more bets, ORB losing runs). Next: his reaction to the answers, then the clean starting point (phase 1 on the $500 seed).

## The unit build is not ours to audit (operator, 2026-11-01)

The build has just started (about 12 of 73 PRs). Its risk and sizing pieces are placeholders, not decisions: nothing is set for risk or sizing yet, and this session is what sets it. Do not report build-level slips (e.g. the A2 `risk_fraction` "0.5" unit) unless the plan itself makes them persist. The placeholders' values (0.5 %, 2R, 48 bars, empty halts) carry no weight in the design.

## Operator opening, 2026-11-01

- Goal for now: combine the risk and sizing of the current system (Book + BMS) with the old system's (QMX-discussion). He is not sure yet what he wants to build.
- Core rule: nothing is set in stone, in any session or note. The whole point is to enhance.
- Work by math and scenarios. His example seed: a unit risking 8 % rather than 1 % may be what makes sense.
- He is not technical and not a trader: correct him, give opinions, broaden the landscape.
- Separate planning and coding branches.
- Use a few agents for heavy reading to keep the lead's context light.
- The old rule "QMX-discussion is barred as a risk/sizing source" is lifted for this session by his explicit ask: it is a source of ideas to combine.

## His backstory and first takes, 2026-11-01

**Origin.** The Hummingbird Project film: he can't win on speed (no capital or infrastructure for it), so he wins on how he trades over time, through risk management and position sizing. Trade around the clock (24 h), many instruments and markets, and compound. His first picture was "risk less, but do it so many times": HFT-like in count, not in speed. He says the confusion between "compound by risking more" and "compound by doing it more" is still with him. (G1 shows the other side on 5 Oct: "better if we trade less", more on each trade.)

**Corrections to my read, and his positions:**
- The "Book" name came from a session on how hedge funds work (pods); it is a finance/accounting term. Fable 5 did most of the Book work (June to July).
- The Book did not forget compounding: it compounded inside each Book (intraday Book, scalper Book) under the BMS, so it was structured, not dropped. (Check: within a cycle, $ per R grows with equity until the 2.5x sweep; what July cut was compounding of swept profit.)
- The Book did not feel aggressive to him; it felt clean. (8.6 % per R is aggressive per trade; the Book hides it as dollars per R off the runway.)
- Old system: "too much machine. Most of it. I think. I don't say it was." (Quote exactly.) It was a make-it-work-first build from about March to April, not meant to be elegant; the Book was meant to be the defined version.
- Being easy to explain is not a goal for him "as long as it works". (My counter: every size must trace to a few numbers so a spec-vs-code gap like the old 4x is caught.)
- Agents (Claude and GPT) called the old system "radioactive"; he now suspects they were "capping" (exaggerating). He asks how we prove it works rather than assume.

**Rulings and asks:**
- Total seed is **$500** after subscriptions (2026-11-01). How it splits across units is open; he says it can't stay unsplit.
- This version must go live. None of the earlier ones did.
- Risk per trade must stay highly configurable, never set in stone.
- No key setting may be left blank (the old system's unfilled thresholds are a gap to avoid). The numbers were blanked because they were configurable, and holding every variable in his head invites mistakes; that is why the unit self-configures.
- Keep house money. Keep the idea of **accelerators** (house money is one); brakes and limits tie to them.
- Kill switch and SQS stay: they earned their place across versions. Exits are never blocked.
- Stops are now part of the unit (latest QML). Stop vs fast invalidation needs its own later thought, maybe an agent.
- Trading overview before technical overview. No architecture or code shape yet.
- Possible pattern later: a solid baseline core, extended the way mini apps extend QMX. Not yet.

**His plan seed (phase 1 on $500):**
- Grow the seed first with the edges most likely to pay: ORB (a known edge in academic work) combined with sniping windows (e.g. the New York open), so it can risk more and earn more early. Then scalpers, which can work with less and work faster.
- Concurrency: ORB and scalpers trade at once. ORB never holds overnight; when it is out, scalpers take over through the 24 h.
- The MIS is a router: it scans markets on scalping timeframes and publishes context (e.g. "this future is mean-reverting"); the unit widens its scope to those markets. Our job: placement (which unit on which instrument has the best odds, given its logic), the risk % per trade, and the stop size that limits each loss.
- System 1 (a logic such as mean-reversion, placed where the market suits it) is the unit; System 2 (a strategy fitted to one pair) is the old way and overfits. System 2 can grow into System 1, not the reverse.

## His second round, 2026-11-01 evening (stopped at item 3 of my answer; more to come)

**Proposals (not ruled):**
- Treat the $500 as a portfolio seed and split it: **$300 scalpers, $200 intraday**, each optimised for its style.
- Units should hold **more than one position at once** across markets (like the old multi-pair bots: gold and crypto together), each position with its own rules and sizing, as long as conditions fit. He asks if that is viable, not just possible.
- Rough idea, not agreed ("premature"): templates for a unit's sizing structure (old-style, Book-style, hybrids), the way mini apps are templates; the BMS as the pod manager that splits capital across styles. First get one structure off the ground.
- Paper trading window: 7 days is doable, 14 is too long. He leans to counting trades over days, then doubts it.

**Rulings / positions:**
- **Every number needs a reason** (a derivation), never "5 % because". He doesn't recall why the old numbers (0.5 %, 0.8 %, x0.2-1 ranges, 5 % open risk) were set, so they carry no weight. This is why the unit must configure itself.
- Costs per market, instrument, timeframe and time must be known to the unit; they feed Kelly.
- The old gap list is old (May/June); he thought it was closed.
- He thinks the old handbrake came from badly set variables and multipliers doing each other's jobs (my view: both that and the structure).
- Market physics, RVOL and microstructure: unsure where they belong (MIS? here?). Microstructure feels scalper-specific and not a sizing matter. The correlation ledger is external to the unit ("internally external").
- He'll aim for better than 55 % wins on scalpers. Strategy sources stay private for now (YouTube and social media); use demo units and placeholders with ranges.

**His questions:** why does 1 % x 16 a day show 0 % ruin; why "half the edge" if paper is just demo; would a portfolio manager test at half edge, and how should this system handle it; half or full Kelly; isn't this all tuned for scalpers.
