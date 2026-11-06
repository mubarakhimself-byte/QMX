# Architecture arena: common brief

You are one of three candidates writing the architecture for QMX's risk-and-sizing template. Each candidate works alone on one version. Afterwards the lead reads all three, picks a base and grafts the best of the others. Do not spawn subagents of your own. No Firecrawl.

## The deliverable behind this

A **risk-and-sizing template for the unit**: works out of the box with self-configuring defaults, each with a reason; extends in any way, by the operator, the copilot or agents; ships through builders; goes live. The operator, Mubarak, is not technical and not a trader. His rule for shape: foundation first, a small complete solid core that grows on top. His complaint about an old version: "too much machine". His complaint about being too safe: the "sitting duck".

## What you are designing

The **first increment**: the twelve-part core in `funnel\FUNNEL.md` section 5.1, with its fifteen binding factors (5.2), build order (5.4) and go-live picture (5.5), and with a named plug point for everything marked later or shadow in `funnel\HYBRID-FATES.md`. The funnel has settled what goes in. You design how it fits together. If you find a pick that cannot work, or a better way to meet its intent, say so and show why; nothing is off limits as long as it performs better and makes sense. QMA changes are flagged, not designed.

## Inputs

All paths are under `D:\QMX-worktrees\risk-plan\tracker\risk-core\`.

- **Primary:** `funnel\FUNNEL.md` in full, `funnel\REVIEW.md`, `funnel\ledger-merge.yaml` (core tier of variables).
- **Code reality:** `grounding\G12-audit-and-repair-for-risk.md` in full, above all its tips, its stale-fact table, section 4 (the socket shapes the repair plan guessed) and "What the funnel must know". Then `G8`, `G9` and `G11` as needed. Read the code itself at the tips G12 names, read-only, wherever you bind to a real file, function or field. Check names; do not trust memory. The repair is still moving those files, above all `qmn/src/qmn/app/runtime.py`, `host.py` and `first_start.py`. Design so your work meets them cleanly, and do not run test suites.
- **The self-configuring model:** `research\R7-software-patterns-self-configuring.md`, closest match Kubernetes and its Vertical Pod Autoscaler.
- **His words,** the highest authority: `seeds\SEEDS.md` ("What the technical lens must hold"), `seeds\operator-words-2026-11-03.md`, `seeds\operator-words-2026-11-06.md`, `STATE.md` items 25 to 47.
- **Depth when you need it:** `expansion\X0`-`X7`, `linking\components\*.yaml`, `research\R1`-`R9`.

## Hard lines

Agents never touch money. Only he promotes a unit to live. Exits are never blocked. The kill switch only goes down by his hand. Kill switch and SQS stay. No key setting left blank: every number has a derivation, and he can change how it derives, not only its value. The Lab, MCP-driven agents and the later agent department plug in without rework and never sit in the order path. Backtest and live run the same rules. Windows is first-class.

## Skills (they will be checked from your transcript)

Open and follow these, non-interactively; no human is available, so take the Fast path and record your assumptions:
- `C:\Users\Mubarak\Desktop\QMX\.claude\skills\bmad-architecture\SKILL.md`: the spine of invariants. Its test decides what belongs: "If two units one level down built this independently, could they choose incompatibly?"
- `C:\Users\Mubarak\.claude\skills\codebase-design\SKILL.md`: deep modules, seams.
- `C:\Users\Mubarak\.claude\skills\domain-modeling\SKILL.md`: one plain vocabulary. No codenames. His screen words stay open (Book and BMS against cluster and portfolio) until he answers Q8, so the schema words must not force that answer.

## What your spine must contain

1. **The shape in one page, plain words:** the parts, who owns what, how an order flows, how a number gets its value. A diagram helps.
2. **Invariants only, in the spine's sense.** Terse. Name the rest under Deferred.
3. **The contracts, as typed sketches bound to real code:**
   - the risk profile document (spec, status, later suggestions), including `authority` and the derivation block with its fallback ladder and receipt;
   - the registry row for a brake, sizer base or scope;
   - the sizer socket's inputs and outputs (today it gets four inputs, per G12);
   - the guard's `before_order` and its fact set;
   - the rank table;
   - the exit socket, answering what the repair is waiting on ("agree the socket with it first"), including step 2, the disaster stop, the trade row's mechanism and `net_r`, and where step 3 waits for the signed stop;
   - the RiskState row;
   - the agents' read and propose surfaces with a direction on every operation.
   Name the compiler refusals to lift and the format bump.
4. **Your fork, argued honestly.** See your prompt for which side you build. Say what would make the other side win.
5. **The extension proof.** Walk each of these through your contracts and show what changes, in files or rows:
   - a new brake;
   - a new sizer base;
   - a new instrument class;
   - a new style preset;
   - changing how one number derives, by him;
   - an agent proposing a tighter limit;
   - the Lab simulating a variant;
   - a version rollout that keeps the unit's record;
   - a later class isolation going from shadow to binding;
   - house money's press switching on.
   A change that needs rework is a finding against your design: fix the design or admit it.
6. **The performance proof.** Trace a healthy, a weak and a bleeding unit from signal to order: every factor that touches size, in order, and where one running loss is read. Confirm that a healthy unit stays above the choke budget. Use `funnel\working\review\core_sim.py` if useful, extending it in your own folder.
7. **The scenario walks.** Walk at least X4-01, X4-14 and X4-66 (`expansion\X4-scenarios.md`) through the spine, and one mid-outage restart.
8. **The hand-offs.** Answer or place every G12 hand-off that lands on your design: stop past entry, stop widening, target at the broker, a unit with no stop, a moved number and open trades, two exits on one bar, partial close and R, R and costs, kill level meanings, where SQS sits, `too_thin`, the version pull. Say which you decide and which wait for numbers or for him.
9. **The build plan:** slices with their files, the order, what must land first from the repair, where you collide with it, and an honest size in PRs. Name the files claimed before the deletion sweep.
10. **What you would cut if you had to cut more,** and what you added beyond the funnel and why.

Keep the spine lean: a builder must be able to read it. Aim for under 500 lines; a long appendix is fine only for the walks and proofs.

## Output

Write to your own folder under `architecture\`, named in your prompt:
- `SPINE.md`: the architecture.
- `RATIONALE.md`: under a page. The alternatives you considered and what you rejected.
- Any scripts beside them.

Read-only everywhere else. Never commit. Never touch other worktrees' files. Time-limit every command. Plain words, short sentences. Mark opinions **[judgment]**.

Return a summary of at most 12 lines: your shape, your fork side and how it fared, the proofs that failed or needed a design change, the build size in PRs, and the biggest risk.
