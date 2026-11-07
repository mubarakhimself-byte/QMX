# Architecture versions, round two: common brief

Read `round-2/BRIEF-COMMON.md` and follow it. Then read `round-2/funnel/FUNNEL.md` in full (sections 3, 4, 6, Appendix E above all), `round-2/funnel/QUESTIONS.md`, `unit-baseline/SWAP-CHART.md`, and `round-2/expand/E1`, `E2`, `E5`. Read the old `architecture/candidate-1`, `-2`, `-3` for mechanisms you may lift; they all share one shape, so don't inherit it. Read your code against `D:\QMX-worktrees\bld-repair-24` and plans at `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\`.

He asked: "before architecture, you have versions of architecture because you can compare... pick up the better versions of each." Last time three versions of one thing came back. This time, you are drawing one genuinely different shape. Hold your assigned answers to the forks and make the strongest honest case for that shape. Don't drift toward a middle.

Items in FUNNEL section 3 marked as presuming a shape are yours to strike. Everything else there is what the core must carry, in your shape's terms or struck with a stated reason.

**Load with the Skill tool and apply, headless:** `bmad-architecture`, `codebase-design`, `domain-modeling`. Nobody is available to answer: infer, tag assumptions, list open questions. Don't use `{planning_artifacts}`; your only outputs are your version's folder.

## Write

`SPINE.md`, a build substrate:
- The paradigm in a sentence, in plain words, and the picture of what runs where at trade time (mermaid, valid).
- Decisions as `AD-n` with Binds, Prevents, Rule. Fix only what independent builders could choose incompatibly.
- Contracts as sketched types: sizer, exits, controls, numbers, facts, reads, the group or pod level, status, records. Name the modules and which package owns each.
- How each placeholder in `D:\QMX-worktrees\unit-plan\tracker\risk-sizing\build\RISK-SIZING-PLACEHOLDERS.md` is swapped in your shape.
- The first baseline in your shape, walked from zero trades and zero fills to a filled entry on paper, and how a user or the copilot changes anything.
- How a developer adds a sizer, a brake, an instrument class and a new fact: files touched, tests. Module map. Debugging one size.
- Observability: the rows and the fold.
- Build order in slices, each ending in something verifiable, with an honest PR count. Note what lands before and after his demo sign-in.
- Deferred, with what would reopen each.

`WALKS.md`: walk each of these step by step against your contracts and your code reading, and say plainly where it strains or fails:
1. A newcomer installs and gets a unit on paper.
2. A gold scalper with fast invalidation and no fixed stop.
3. An ORB unit across several opens, one bet counted once.
4. A futures week with the copilot from papers and videos, ending in units with their own sizing (assume the route exists; say what else is missing).
5. A very aggressive setup with few units on one basket, then a stage change as capital grows. Mechanics only; no dollar case.
6. A unit made in the Lab, one from a workflow, one from a mini app.
7. A mini app feeding another, and a desk publishing a reading a unit reads.
8. 200 units: one pod edit, the fleet watch, herding on one volatility shift, and one node's limits.
9. Swapping a placeholder on a unit with a record and an open position.
10. A brand-new brake, a brand-new instrument class, a new sizing base.
11. The MIS down mid-session. A guard or chain failure with open positions. A hung stage. A restart past an anchor.
12. House money, reverse house money and a press after wins, on and off, per pod.
13. Backtest against live on the same unit: where can they differ?

`RATIONALE.md`: what this shape buys and costs against the others, stated fairly, what would make you abandon it, and where another version is simply better. Under a page.

No dollar simulations. Small mechanism checks are allowed only to confirm that a rule behaves as described, under `D:\Temp`.

Be honest about size: "too much machine" is a real failure, and so is a design that can't do what he asked. Reply to the lead in under 120 words: paths, PR count, and where your shape strains most.
