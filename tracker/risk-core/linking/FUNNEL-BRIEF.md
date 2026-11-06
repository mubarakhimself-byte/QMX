# The funnel: judge and link everything into one consistent set

You are the Fable funnel judge. Read this file first and follow it. Do not spawn subagents of your own. No Firecrawl.

## What this step is

QMX is a trading system. The operator, Mubarak, is not technical and not a trader. This session designs the **risk-and-sizing template for the unit**: self-configuring, extensible by him, the copilot or agents, and shipped through builders. His method is expand, then funnel. Expansion is finished: eight layers wrote about 510 hybrids. You turn that into one consistent set of decisions. Architects will build from your output next, in competing versions.

His ask for this step (M17, verbatim in `seeds\operator-words-2026-11-03.md`): ideas from many sources will collide, so check for logical flaws; do not just pick every random idea; pick the best, or more than one, or give a range.

## Inputs

All paths are under `D:\QMX-worktrees\risk-plan\tracker\risk-core\`.

- **Your rubric:** `linking\RANKING.md`. Survival at 0 blocks an idea. Performance with intention, not just safety: a design that never touches the floor but grows nothing is the "sitting duck", and it fails.
- **The hybrids:** `expansion\X0-trading-lens.md`, `X1-template-shape.md`, `X2-sizing-accelerators.md`, `X3-brakes-exits-drift.md`, `X4-scenarios.md`, `X5-edge-verification.md`, `X6-observability.md`, `X7-agents.md`. Each holds hybrids, problems with options, collisions, restructure proposals, gaps and questions. Read all eight in full; that is your main reading.
- **What changed since they were written:** `grounding\G12-audit-and-repair-for-risk.md`. Read it in full. It names which facts are stale, 37 items handed to this session, the rulings to carry, the socket shapes the repair plan guessed, and the code tips. The expansion layers did not have it, so check every hybrid that leans on a stale fact.
- **His words:** `seeds\SEEDS.md` (what he asked, accepted, refused and corrected, plus "What the technical lens must hold"), `seeds\operator-words-2026-11-01.md`, `seeds\operator-words-2026-11-03.md`, `seeds\operator-words-2026-11-06.md`. `STATE.md` items 25 to 44 hold the principles.
- **Evidence:** `linking\components\*.yaml` (each hybrid cites component ids), `research\R1`-`R9`, `research\papers\text\`, and `grounding\sims\` plus the sims under `linking\stage-b\`. Spot-check evidence where a pick leans on it hard.
- **The ledger:** `ledger\variables.yaml`, `ledger\additions\*.yaml`, `ledger\check.py`, `ledger\couplings.md`. 903 variables and 1,758 couplings with 7 duplicate ids and some alias warnings. Use the couplings to test whether picks fit together.
- **Targeted look-ups only:** research is finished. If one pick truly hinges on a specific missing fact, you may check that one question with the alphaXiv MCP (`mcp__alphaxiv__*`) or Exa (`web_search_exa`), loaded with ToolSearch. No broad searching. Log each look-up and what it changed in `funnel\working\lookups.md`. Known gaps with no literature (fast-invalidation cut size, intraday win persistence after costs, rule-based class isolation) need QMX's own tests, not more reading: mark them for the numbers lens.
- **Not ranked here:** `linking\UNIT-IDEA-BANK.md` (unit and reading seeds). If a pick needs a reading or block from it, name the dependency.

## Standing rulings you must carry, not reopen

- Agents never touch money. Only he promotes a unit to live. Exits are never blocked. The kill switch only goes down by his hand. Kill switch and SQS stay.
- This version must go live with no key setting left blank. Every number has a derivation, and he can change how it derives, not only its value.
- Nothing is off limits (M31, M32): the Book/BMS shape, levels or parts of the shipped stack may be replaced if the replacement performs better and makes sense. QMA changes are flagged, not designed.
- The multi-instrument lens crosses every decision.
- The agent department, the Lab and MCP-driven agents must be able to plug in later without rework, and never sit in the order path.
- Numbers come later. Your output fixes shapes, derivation rules and ranges of options, not final values. The numbers lens will run simulations using the scenario harness. Do not anchor any choice on a dollar figure. Do say where a design only works above some size (for example minimum lots), so the numbers lens can test it.
- The rulings listed in G12 "What the funnel must know", item 5.

## Method

1. **Merge the decision points.** Build one list from: X0's decision points; every layer's problems, collisions and restructure proposals; G12's hand-offs and its list of decisions on this session's desk. Merge duplicates; layers often describe one thing three ways.
2. **Judge each decision point.** For every option (hybrid ids), score it on RANKING.md's six criteria with a one-line reason each. Then give one pick, two picks (when they serve different styles or classes) or a range, with the reason, the collisions it resolves, and what it assumes.
3. **Give every hybrid a fate, all of them.** Picked (into which decision), merged into another, kept for later, or dropped, with one line why. Nothing vanishes silently. This is one table.
4. **Hunt logical flaws across picks.** This is the point of your role. Check each pick against the others and against the ledger couplings. For example:
   - does a sizer that needs inputs get them from a source that exists after the picks;
   - can an accelerator raise size into a brake;
   - does a percentile brake have a record to read on day one, given the record holes in G12;
   - does the portfolio budget agree with the unit sizer;
   - does splitting across units still clear minimum lots;
   - do fail-open and fail-closed defaults agree across the MIS, isolation and agent evidence;
   - does automation contradict his click rulings;
   - do the picks together choke a healthy unit.
   Run the simple scenarios from X4 through the picks by reasoning, and name what breaks. Name each flaw and how you resolved it, or mark it unresolved. Write a small script if a flaw can be settled with arithmetic; keep the script beside your output.
5. **Stress the result.** Run `bmad-party-mode` once on the hardest decision points, and `bmad-advanced-elicitation` (pre-mortem and red team) on the final set, non-interactively: you play every role and never wait for input. Skill files are in `C:\Users\Mubarak\Desktop\QMX\.claude\skills\<name>\SKILL.md`.
6. **Check coverage.** Map every capability in SEEDS "What the technical lens must hold" to a pick, or mark it a gap. Do the same for G12's hand-offs.
7. **Name the real architecture options.** Where a genuine choice of overall shape remains, describe two to four distinct whole-system shapes for the architects to build competing versions of, and what would make each win. If only one shape survives honestly, say so. Do not invent options to fill a quota.
8. **Filter questions.** A question goes to him only if it is truly his: money, vocabulary he cares about, or irreversible scope. Check each against SEEDS and the rulings first, because many layer questions are already settled. Give each your recommended answer and the default the work proceeds on. Nothing blocks on him.

## Output

Write these under `funnel\`, as you go, so a stop loses nothing:

- `funnel\FUNNEL.md`: decision points with picks; logical flaws found; coverage tables; architecture options; questions for him, with defaults.
- `funnel\HYBRID-FATES.md`: the fate of every hybrid.
- `funnel\ledger-merge.yaml`: which variable ids merge into which (the 7 duplicates and alias warnings first), and which die with dropped hybrids. A later step applies this to build ledger v1, so state it as data.
- `funnel\working\`: roundtable notes, the pre-mortem and any scripts.

Plain words, short sentences. Mark opinions **[judgment]**. Read-only everywhere else. Never commit. Never touch other worktrees' files. Time-limit every command. The repair program is still moving code: read the tips named in G12 only to check a claim, and do not run tests.

Return a summary of at most 15 lines: decision point count; the five picks that matter most; logical flaws found and how many stayed unresolved; which architecture options survive; the questions for him; how many hybrids were picked, merged, kept for later and dropped.
