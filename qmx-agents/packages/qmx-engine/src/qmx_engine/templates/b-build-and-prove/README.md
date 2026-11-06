# Turn a strategy idea into a tested strategy, ending on paper

Runs from his one sentence to the core's verdict and shows the core's own papers: a proposal card for a paper trial on a pass, or a death certificate on a fail. Each lands once, when the verdict lands. Nothing here publishes, promotes or trades; the paper trial is his click.

Built from cards D2 (strategy to a sealed experiment spec) and D3 (its robustness set) in `research/methodology/17-templates-dev-pm-lab.md`, and Part B `workflows.md` section 3, "Build and prove a unit".

## Steps

1. `Seal the experiment spec` (`scripts/spec.py`, zero tokens) seals the windows before any unit is built. The holdout and the split are his choice per study and both start off, so the whole `window` is one in-sample window. On the card's `study` input, `split` cuts the range into in-sample (`in_sample_share`, 0.6) and `folds` (3) walk-forward folds, and `holdout` seals the family's holdout or the last `holdout_share` (0.2) of the range. The shortest in-sample window (180 days), fold (30) and holdout (60) are study settings too.
2. `Spec checks pass?` stops a refused spec; the scorecard lists the problems.
3. `Write the claim card` (role `planner`) turns his sentence into the claim, the markets and the rules his words state.
4. `Write, check and save the unit` (role `builder`, toolsets `unit`, `blocks` and `memory`) first asks `memory_check` whether an idea like this already died, then searches the dictionary, starts the unit with `unit_new`, and checks it with `unit_check` until it passes, saving each check as the unit's draft. It has no backtest tools. The builder's model is the Settings row `roles.builder`, which ships as the strong tier and is his to change.
5. `Check the unit` (the shared `unit-check` block, carried in `unit-check/`) checks the document by script and loops every problem back to a fix step.
6. `Ready to test?` (`scripts/ready.py`) tests only the draft the builder saved, and only when it passed with no fix round. A unit the check step had to fix is not the saved draft, so the scorecard says so and nothing runs.
7. `Backtest on QMB` and `Robustness runs on QMB` (`app_op`, jobs `backtest` and `robustness`) run the unit's pin over the in-sample window. When the run names `ranges`, `Walk-forward on QMB` (job `walk_forward`) picks from them in each of the study's `folds`, over in-sample and the validation folds. The holdout is never in a window. QMB's lander counts every try, each walk-forward fold included.
8. `Ask the referee` (role `judge`, toolset `backtest`) presses the core's `backtest_judge_run` on the landed results. The core's script decides the verdict, with every try of the family counted, and lands it with its papers. The step's copy of the answer decides nothing.
9. `Hand on the verdict` (`scripts/hand.py`), `Read the stored verdict` (the `library` node) and `The stored verdict` (`scripts/stored.py`) read what the Library holds. The run stops by name when the object is not a verdict, judged another unit, judged other results or runs than this run's, or lacks a paper its outcome calls for.
10. `Passed?` routes on the stored outcome: a pass to `The paper card`, anything else to `The dead end` (both `scripts/card.py`). `too_thin` and `incomplete` get neither card nor row: the verdict waits.
11. `Write the lineage` (the shared `lineage` block) links the unit and its first result.
12. `Write the scorecard` (role `writer`) writes the summary and explains the verdict; `Render and grade` checks every number in it.

A test run names `fixture` (`pass` or `fail`), and `Replay the recorded runs` stands in for QMB and the referee: it lands the recorded verdict and papers from `fixtures/qmb.json` on the run's own ref, and the real read crosses them. No model is asked about a run that never happened. A `fixture` on a live run stops at `The stored verdict`. Every other run asks QMB.

## Left out, and why

- The template's own `judge` child: it needs the family's tries, and a workflow script reads only four Library verbs (`nodes/script.py` `READS`). The core's referee reads them itself, so the referee step asks it.
- A walk-forward with no `ranges`: QMB's `walk_forward` emits its measure only for two or more candidates, and a sentence names none, so a run without `ranges` runs none. The verdict's walk-forward step then reads not run, and the verdict waits (`incomplete`) rather than passing.
- A referee with only `backtest_judge_run`: a node names whole toolsets, the Surface and the guard switch tools on per server, and `parameters.tools` lists built-in tools only, so it needs an engine change. The read makes a forged answer harmless, so it is not needed.
- The `dead_end` memory row as a step: the core writes it where it lands the certificate, and the certificate's `memory_row` names it.
- Stage 11 (iterate on a weak result) is `d3`, and the holdout touch belongs to the final survivor in `d3` and `l4`.
