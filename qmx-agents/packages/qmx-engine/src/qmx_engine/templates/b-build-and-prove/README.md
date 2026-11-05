# Turn a strategy idea into a tested strategy, ending on paper

Runs from his one sentence to the core's verdict: a proposal card for a paper trial on a pass, or a death certificate on a fail. Nothing here publishes, promotes or trades; the paper trial is his click.

Built from cards D2 (strategy to a sealed experiment spec) and D3 (its robustness set) in `research/methodology/17-templates-dev-pm-lab.md`, and Part B `workflows.md` section 3, "Build and prove a unit".

## Steps

1. `Seal the experiment spec` (`scripts/spec.py`, zero tokens) seals the windows before any unit is built. The holdout and the split are his choice per study and both start off, so the whole `window` is one in-sample window. On the card's `study` input, `split` cuts the range into in-sample (`in_sample_share`, 0.6) and `folds` (3) walk-forward folds, and `holdout` seals the family's holdout or the last `holdout_share` (0.2) of the range. The shortest in-sample window (180 days), fold (30) and holdout (60) are study settings too.
2. `Spec checks pass?` stops a refused spec; the scorecard lists the problems.
3. `Write the claim card` (role `planner`) turns his sentence into the claim, the markets and the rules his words state.
4. `Write, check and save the unit` (role `builder`, toolsets `unit` and `blocks`) searches the dictionary, starts the unit with `unit_new`, and checks it with `unit_check` until it passes, saving each check as the unit's draft. It has no backtest tools. The builder's model is the Settings row `roles.builder`, which ships as the strong tier and is his to change.
5. `Check the unit` (the shared `unit-check` block, carried in `unit-check/`) checks the document by script and loops every problem back to a fix step. A script opens no Library, so what only the Library can settle, such as a market only the Library holds a record for, is a note on the check, and QMB's lander checks it with the Library before any run.
6. `Ready to test?` (`scripts/ready.py`) tests only the draft the builder saved, and only when it passed with no fix round. A unit the check step had to fix is not the saved draft, so the scorecard says so and nothing runs.
7. `Backtest on QMB` and `Robustness runs on QMB` (`app_op`, jobs `backtest` and `robustness`) run the unit's pin over the in-sample window. When the run names `ranges`, `Walk-forward on QMB` (job `walk_forward`) picks from them in each of the study's `folds`, over in-sample and the validation folds. The holdout is never in a window. QMB's lander counts every try, each walk-forward fold included.
8. `Ask the referee` (role `judge`, toolset `backtest`) presses the core's `backtest_judge_run` on the landed results and copies its answer. The referee's script decides the verdict, with every try of the family counted. Its brief tells the step to copy that answer unchanged and run no backtest, but no script compares the copy with what the referee answered, and the step holds the whole `backtest` toolset. A forged pass reaches only a proposal card on the run's own ref, and the paper trial still waits for his click.
9. `Paper card or dead end` (`scripts/card.py`) and `What follows the verdict` (`scripts/next.py`) route the verdict: a pass goes to `Propose a paper trial` (the shared `proposal-card` block), a `fail` or `no_trades` to `Write the death certificate` (the shared `death-certificate` block). `too_thin` and `incomplete` get neither: the verdict waits.
10. `Write the lineage` (the shared `lineage` block) links the unit and its first result.
11. `Write the scorecard` (role `writer`) writes the summary; `Render and grade` checks every number in it.

A test run names `fixture` (`pass` or `fail`), and `Replay the recorded runs` stands in for QMB from `fixtures/qmb.json`; every other run asks QMB.

## Left out, and why

- The template's own `judge` child: it needs the family's tries, and a workflow script reads only four Library verbs (`nodes/script.py` `READS`). The core's referee reads them itself, so the referee step asks it.
- A walk-forward with no `ranges`: QMB's `walk_forward` emits its measure only for two or more candidates, and a sentence names none, so a run without `ranges` runs none. The verdict's walk-forward step then reads not run, and the verdict waits (`incomplete`) rather than passing.
- A check of the referee's copy, and a referee with only `backtest_judge_run`: a node names whole toolsets, the Surface and the guard switch tools on per server, and `parameters.tools` lists built-in tools only, so both need an engine change.
- The cause on the death certificate: the referee's answer lists each market's outcome but not the step it failed on, so the block classifies a `fail` as `behaviour`. The core's own certificate, under the answer's `cards`, carries the typed cause.
- The `dead_end` memory row: no workflow step can land a memory row (B18a); the certificate carries the row in its metadata.
- Stage 11 (iterate on a weak result) is `d3`, and the holdout touch belongs to the final survivor in `d3` and `l4`.
