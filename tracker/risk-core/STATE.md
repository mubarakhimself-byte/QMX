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
4. Landscape given (opinion on both systems). His backstory and first takes are below (2026-11-01). Scenario maths started: `grounding/sims/freq_vs_size.py` (bigger bets vs more bets, ORB losing runs).
5. **Grounding round 2 started 2026-11-01 21:20, on his go ("start grounding... we shall ground only"). Stop line: midnight, grounding only.** Three agents:
   - G6: Book/BMS levels and paper/live (Opus) → `grounding/G6-book-bms-levels-and-paper.md`
   - G7: what a unit receives from QMB and the MIS, plus instruments and costs (Opus) → `grounding/G7-unit-inputs-qmb-mis-instruments.md`
   - Seed register from this session's transcript verbatim (**Fable, his explicit ask**) → `seeds/operator-words-2026-11-01.md` and `seeds/SEEDS.md`, including what this STATE file missed or got wrong.
6. He has not read the lead's long third-round answer and will read it on 2 Nov morning. **Do nothing that needs him to have read it:** no decisions, no research, no generative steps. When the agents finish: check each file, commit, acknowledge in two lines, stop.
6b. **G7 done** (21:50, committed). Plan-level conflicts it found, for his morning, not before: (a) QMB's edge numbers never reach the sizer, so a paper lane starts from defaults and an empty own record; (b) costs never reach the sizer (no commission key, no swap, hourly costs or currency conversion in its inputs), against his ruling that costs feed Kelly; (c) widening a unit to new markets is a new version plus his click, and the MIS can only narrow; (d) records split per market only, never per session or timeframe; no field holds average win or loss in R. The MIS app itself is not being built yet (only its prerequisites C-05a/b/c).
6c. **G6 done** (21:52, committed). For his morning, gently, because these correct his memory: (a) three rule levels existed, but nearly every number sat on the Book; the GitBook BMS held one number and no BMS-only registry row exists; (b) the kill line is dollars in GitBook, DOCS and code, never a percentage; (c) no Book or BMS source has a daily drawdown rule; that memory matches the April system. Also: the day budget drained and refused entries (GitBook, still in DOCS), but what drains it and when the door refuses are undefined everywhere, and code has no budget door; a fixed-dollar kill line made the GitBook ladder an accelerator (8.6 % per R at seed, 12 % at the 2.5x cap); house money appears in no Book or BMS source; node-paper is a real broker demo account with the same client code and its own ledger and BMS; nothing measures slippage yet; the GitBook glossary calls the Book "a pod".
6d. **Seed register done** (Fable, committed): `seeds/operator-words-2026-11-01.md` (his nine messages M1-M9, verbatim) and `seeds/SEEDS.md` (114 items by level, tensions, unanswered or rejected answers, corrections to the lead, 38 STATE gaps, dictation glossary). **SEEDS.md, not this file, is the source for his words.** Its "What the lead's STATE.md missed" section lists the pushbacks the third-round answer depends on (low-end sizing "too safe", trust-grows-with-trades doubted, sims on one instrument, session drawdowns as a brake level, Kelly and portfolio view deferred by him).
6e. **Grounding round 2 complete at about 22:00 on 1 Nov. Stopped as he asked.** Next session: he reads, then we agree the route (item 7).
7. Research is not started. Drop prop-firm buffers from the research list; he only used them to explain. The proposed route (seed register → grounding → research → wayfinder → generative round → funnel → maths → architecture → review) waits for his reading.

8. **3 Nov, 13:46 local: he is back (M10, verbatim in `seeds/operator-words-2026-11-03.md`).** He read the 1 Nov answer and replied point by point. Rulings and asks:
   - Two lenses. **Technical lens first**, owned by the lead: a malleable, self-configuring, extensible risk-and-sizing template on the shipped unit system (his comparisons: n8n, white-label software, mini apps). How agents and the copilot reach it, schemas, outside code, QML additions, UI needs logged for the UI session. **Numbers lens later**: budget, allocation, values, simulations with Fable agents, worst/realistic/best cases "all factors considered".
   - Don't confine anything yet: several brakes, 3-5-7 / 10-5-3, unit-vs-BMS daily brakes are all "circumstantial".
   - Use the circuit breaker (old CB, WF3 decay) and improve it; he proposes a BMS-level breaker and a market isolation protocol (class, region, news, SQS, on evidence).
   - Live drift from backtest must not mean pulling out on one bad day; size down slowly; bring solutions, not just issues.
   - He reads two contradictions in the 1 Nov answer (10 units "split" vs frequency; "twice the edge, twice the size" vs not leaning on edge). The first is a misreading (each unit keeps its full size); the second is a fair push. Scratch sim: one unit $10/trade touches $300 1.4 %, ten independent units at $10 touch it 1.5 % with ten times the growth, ten at $1 0 %, ten half-correlated at $10 32 %.
   - Research asks: StrategyQuant, QuantConnect, MT5 articles, Bloomberg; what traders mean by sniping windows.
   - Fable agents wanted where smartness matters; usage is not a limit here.
   - The unit stack (75 PRs, tip `build/us-c13` d02af358, list `D:/QMX-worktrees/unit-ship/STACK-LIST.md`) is not merged yet; he merges when the last two land.
9. **Grounding round 3 started 3 Nov about 14:20 local**, six background agents:
   - G8 unit chassis and extensibility (Opus) → `grounding/G8-unit-chassis-and-extensibility.md`
   - G9 runtime brakes, isolation and evidence at the stack tip (Opus) → `grounding/G9-runtime-brakes-isolation-evidence.md`
   - G10 circuit breaker, WF1-3, news, BMS slots, decay across generations (Opus) → `grounding/G10-brakes-decay-slots-all-generations.md`
   - R1 platforms: QuantConnect, StrategyQuant, MQL5, n8n, Bloomberg, open-source engines (Opus) → `research/R1-platforms-risk-sizing-extensibility.md`
   - R2 trader practice: sniping windows, live drift, isolation, breadth, sweeps (Opus) → `research/R2-trader-practice-windows-drift-isolation-breadth.md`
   - Seed update with M10, lens tags T/N, "what the technical lens must hold" (**Fable, his ask**) → `seeds/SEEDS.md`
   Proposed route after grounding: wayfinder map → generative round on Fable (bmad-brainstorming, bmad-party-mode, bmad-cis-problem-solving, bmad-forge-idea) → architecture (bmad-architecture, codebase-design for the seams) → review (bmad-review, grill-with-docs) → slices built by Opus poteto-agent builders with one reviewer per PR → numbers lens. Waits for his go.

10. **3 Nov 14:05 local, M11 (verbatim at the end of `seeds/operator-words-2026-11-03.md`): his go.** "For the technical part, I don't think you really need me." Take his conversation as the seed, expand it, watch for logical flaws. So the route in item 9 runs without waiting for him once grounding lands; numbers-lens choices still come back to him.
    - He senses a flaw in "ten units at full size, same floor odds" and wants those versions run (numbers lens). Lead's check, `grounding/sims/frequency_flaw_and_brakes.py`: the claim holds only if the edge is as believed and units are independent. At half the edge, ten full-size units touch $300 in 11 % of runs vs 5.8 % for one unit; at no edge 68 % vs 19 %. Ten $1 units stay at 0 % in every case, so splitting is insurance against being wrong about the edge (his own "don't lean on the edge"). Ten full-size units reach whatever the true edge says ten times faster.
    - How frequency affects brakes: count brakes fire on healthy units by chance as trade count rises. "2 full stops a day" fires on 61 % of days at 4 trades a day and 55 % wins, 94 % at 8, 100 % at 40; "3 losses in a row" 14 % at 4, 59 % at 16. So count brakes must be scaled to each unit's trade count and win rate, or measured in money or drawdown. Dollar-based brakes are not yet simulated.

11. **M12 (mid-turn, verbatim at the end of `seeds/operator-words-2026-11-03.md`)**, sent as he left. New asks: real edge verification as an automated workflow, with proposals; plain explanation of "half the edge" and "ten times faster" (owed to him); Book/BMS exposure, drawdowns, realized and unrealized P&L; generate many scenarios (losing together, isolation, correlation, news, switching); the observability layer (logging, monitoring, UI shows up/on/trading/wrong); brakes vs frequency need a sweet spot per level and must count fast invalidation and the exit/stop mechanism; a **variable ledger** that records how each variable affects the others; clustering of the variables that grew with every instrument class, style and timeframe, with academic and cross-industry research; **agents must solve the issues, not just list them**; use Exa, not Firecrawl (Exa is not connected to this session: not in the server list or config; told him). "Stay on track."
    - Fair hits on the lead: the count-brake sim treated every loss as a full stop (fast-invalidation exits are small cuts, so full-stop counts fire less); the "losing together" row had no brakes on, so it shows what brakes must catch, not what happens with them.
    - Grounding round 3 done and committed: G8, G9, G10, R1, R2; SEEDS.md updated by Fable (146 items, lens-tagged, "What the technical lens must hold" with 45 capabilities), resumed to fold in M12.
    - Round 3b started: G11 variable ledger, exposure/drawdown/P&L, exits and stops, observability (Opus) → `grounding/G11-ledger-exposure-exits-observability.md`; R3 edge verification, clinical-trial and other-industry analogues, cross-instrument normalisation (Opus) → `research/R3-edge-verification-and-analogues.md`.
    - Next, on his go (M11): problem map `PROBLEMS.md` from all grounding and SEEDS, then Fable solver agents, one per cluster (edge verification workflow; brakes x frequency x exits per level; scenario catalogue; variable ledger and dependencies; template shape and agents' access; observability; live drift; windows), then architecture.

12. **M13 (verbatim at the end of `seeds/operator-words-2026-11-03.md`)**, sent as he left again; he will not read the messages sent while he was away. Rulings:
    - Web: use the built-in browser and web search, not Firecrawl. Browserbase is in his user config but was added after this session started, so this session can't see it; Exa is configured nowhere. Told him.
    - **Method: expand, then funnel.** Don't fold everything into one too early; the problem is the number of variables. Expand the domain layer by layer (technical, trader, DevOps, what QMX has shipped), then funnel, then architecture.
    - **The variable ledger is central**, kept across all steps and the simulations, because the variable count has grown well past the FX-only days.
    - Fable for the hardest problems: architecture, questions, scenario-based thinking (his examples; the lead decides).
    - M14: "after expansion, the ledger might also expand." So the ledger is a living file: v0 before expansion, each expansion agent adds its own ledger file, the funnel merges them into v1, and architecture and simulations read v1.
    - Revised route: G11 + R3 land → **ledger v0** (machine-readable: every variable, level, unit, instrument class, default and how it is derived, couplings to other variables) → **expansion round** per layer, each agent adding variables to its own ledger file → **funnel** (cluster, dedupe, resolve contradictions) → **architecture** (Fable) → review → slices → builders.

13. **M15 (verbatim in the words file).** Hint: the old **dynamic SL/TP** system ("SLNTP"). For scalpers it was replaced by fast invalidation; for intraday it stayed, moving the stop to breakeven by how far the trade is winning (he doesn't fully recall). Sent to G11 to find by name. Web tools: he does not trust plain web search or text fetches ("that simple website"); he prefers Firecrawl, a third-party search, or a real browser read like a human. M16: Browserbase is his new install, but this session cannot see it (not in the session server list; added after start); a new session would load it. He has no Ego Lite account, so no ego-browser. Choice for this session: the built-in browser pane. Not a global rule ("it doesn't mean you update globally"), so no memory entry. Told R3. R1 and R2 leaned on web search and fetches; their key outside claims should be re-read in a real browser before the funnel relies on them.

## The unit build is not ours to audit (operator, 2026-11-01)

The build has just started (about 12 of 73 PRs). Its risk and sizing pieces are placeholders, not decisions: nothing is set for risk or sizing yet, and this session is what sets it. Do not report build-level slips (e.g. the A2 `risk_fraction` "0.5" unit) unless the plan itself makes them persist. The placeholders' values (0.5 %, 2R, 48 bars, empty halts) carry no weight in the design.

## Operator opening, 2026-11-01

- Goal for now: combine the risk and sizing of the current system (Book + BMS) with the old system's (QMX-discussion). He is not sure yet what he wants to build.
- Core rule: nothing is set in stone, in any session or note. The whole point is to enhance.
- Work by math and scenarios. His opening example: a unit risking 8 % rather than 1 % may be what makes sense. **Withdrawn later the same day** (his evening messages): he had forgotten Kelly, and "8% is a variable. We need to know where, why we are setting that." Treat 8 % as a number that needs a reason, not a target.
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
- Stops are now part of the unit (latest QML). Stop vs fast invalidation needs its own later thought, maybe an agent. **Every number shown so far ignores fast invalidation** (the sims, the 8.6 % figure, the streak table all assume full-size losses); he pointed this out three times. Future maths must include FI cut sizes.
- R fixed at entry is **not accepted** by him: "We shall see about that." The unit of measure (dollars or percent; pips, points or ticks) is still his open question.
- Trading overview before technical overview. No architecture or code shape yet.
- Possible pattern later: a solid baseline core, extended the way mini apps extend QMX. Not yet.

**His plan seed (phase 1 on $500):**
- Grow the seed first with the edges most likely to pay: ORB (a known edge in academic work) combined with sniping windows (e.g. the New York open), so it can risk more and earn more early. (**Unsettled:** later the same evening he said the first live unit "is most likely going to be a scalper", and that the split "might change".) Then scalpers, which can work with less and work faster.
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

## His third round, 2026-11-01 night

**Rulings / positions:**
- **The Book/BMS system is the skeleton.** "Everything is sort of falling into place inside the book system": enhance and rebuild it, don't replace it. This session is building a better Book overall.
- **Risk management works at several levels:** unit, cluster (e.g. all mean-reverting scalpers), methodology, and portfolio, with overlaps. Matches bot rules → Book rules → BMS rules. Units self-configure; a Book is a cluster; the BMS holds the portfolio (splits capital, can shut units off; house money placement open).
- **Each unit type gets its own sizing template** with self-configuring defaults, each with a reason. Example: a mean-reverting scalper should not take 6 straight full-size losses; brake at about 3 or at a pattern (like reverse house money). Not every scalper can hold several positions. Quote: "Yes, the idea makes sense, true, but I don't think it will hold up across all those different variants."
- **Design the baseline first**, then grow. Agents and research fill the per-type templates later.
- **Luck is not a variable.** QMB's workflows prove or enhance the edge before a unit reaches demo. Don't use luck as an argument. Picking which units to promote is not this session's domain.
- **Floor:** the system should almost never touch it, only in a black swan or a real system failure. BMS keeps a buffer before the floor. (He used prop-firm daily limits only to explain this and later withdrew the analogy: "prop farm buffers are not ideal. I was just explaining.") Losing $200 in a day is "stupid". This is his answer to "how often would you accept touching the floor".
- The floor/cushion is user-configured; much else is self-configured. He'd rather give units part of the seed ($100-200 of $500) and let them grow than leave $300 idle. Open: how trading restarts the next day; whether the sweep cap returns.
- Daily brakes: 10/5/3 % made no sense at $500 (3 % = $15, less than a trade). There must be more than one brake, at unit and portfolio level, and each must say what is breaking. He mentions the 3-5-7 rule as the portfolio-manager standard.
- Every change in size needs a stated reason (his volleyball picture: why spike from that angle).
- Units of measure are open: dollars or percent. He recalls the kill line as a percentage.
- Aggressive is not the same as nuclear: accelerators make it aggressive, and brakes make sure it never loses stupidly.
- Adaptation is key; brakes first, accelerators second (agreed).

**New ideas (rough):**
- **Split QMX into demo and live** so a unit trades identically on both and only the account differs. He asks whether slippage can be measured on demo.
- Session opens need a protection or caution window, like news.
- Sniping windows: how are they found, by agents or deterministically? Findings go to the library as artifacts for copilot jobs.
- Microstructure: he doesn't recall what it is; he imagined agents summarising it per session or market for units.
- He'll ask the unit-plan agent whether market physics and relative volume are in the build.
- Sessions and overlaps (Tokyo, London, New York) across FX, crypto perpetuals and futures at once: how units avoid contradicting themselves. Design for complexity, not a complex system.
- Indices are an instrument class too; don't think only in FX.
- An ORB unit getting frequency through breadth (each session's and market's opening range): he called it brilliant.
- He disagrees strongly that a great month is only +50 %.

**Workflow:** he wants to use the planning workflow from memory with many agents: seeds → BMad CIS, brainstorming, party mode (trader personas or techniques) → architecture. Agree the route first. Ground on the skills (poteto-mode, wayfinder, etc.).
