# Iterate against QMB with overfit guards

Waits for a workflow read of the Library: the parent's reports, its family's tries and its sealed holdout (`needs: real-library`). QMB's own door is there now.

Built from card D3 (iterate against QMB with overfit guards, the old WF2 core) in `research/methodology/17-templates-dev-pm-lab.md`. It improves one strategy honestly: it reads the reports, diagnoses why the strategy is weak, makes 3 or 4 structurally different children, retests, keeps survivors, and stops on a budget or a plateau. Every child counts as a trial and the holdout is touched once.

## Steps

1. `Load the parent's reports` (`scripts/reports.py`) reads the full report, the family's trial count and spec hashes, and the headroom.
2. `Hide the holdout from the diagnoser` drops every holdout number and refuses a parent without a full report.
3. `Diagnose weaknesses and why` (role `synthesiser`, the card's diagnoser) sorts weaknesses into fixed buckets, each with a hypothesis and the evidence row.
4. `Start the generations` makes the parent the first best and reads the loop's counts from the card.
5. `Each generation` runs the card's `generations` (3 to start) and stops after `generations_without_gain` (2 to start) in a row without gain. Both are starting defaults he changes on the run's inputs, never caps. The loop node's `max_iterations` of 1000 is only the engine's rule that every loop ends; the card's counts stop the loop long before it.
   1. `Propose structural children` (role `planner`, the card's generator) proposes 3 or 4 children, each with a change label from a fixed list and the hypothesis it tests.
   2. `Check and dedupe the children` refuses a child with no diagnosed weakness, a parameter nudge, or a spec the family already tried.
   3. `Build the children` (role `builder`) builds them, 20 turns per child. The builder's model is the Settings row `roles.builder`, which ships as the strong tier and is his to change.
   4. `Compile and test each child` (`scripts/test.py`) is the generation's QMB call: compile, in-sample, walk-forward and the judge's shipped preset.
   5. `Record every child` counts every child as a trial; one that wins only in-sample is dead, and the best survivor becomes the next parent.
6. `Holdout once for the survivor` (`scripts/holdout.py`) touches the holdout on the final survivor only.
7. `Judge the results` (the shared `judge` block, carried in `judge/`) sets the verdict by script over the whole family, dead children included.
8. `Generation tree and scorecard` keeps dead branches tagged `negative_result` and says whether the survivor held. `Write the scorecard` (role `writer`) writes the summary; `Render and grade` checks its numbers against the reports, the holdout touch and the tree.

## Left out, and why

- One builder per child in parallel: a fan-out inside a loop body is not run by the engine's core yet, so one builder builds the generation's children in turn (80 turns, 20 per child).
- R7 calibrate over the survivor: it joins when QMB returns reruns.
- Writing the family ledger and the lessons for the next diagnoser: they need QMB's family ledger door and workflow memory rows; the result carries every child.
- Starting from template B's stage 10 or an L4 survivor: the trigger is manual until event triggers exist.
- Test fixtures: they come with QMB's door for agents, whose real result shape they must match.
