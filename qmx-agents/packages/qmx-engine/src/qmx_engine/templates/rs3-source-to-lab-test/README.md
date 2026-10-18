# RS3 Source to a Lab test

Waits for QMB's doors for agents and the Lab build (`needs: qmb-door`).

Built from card R3 (replicate a paper's result in the Lab) in `research/methodology/15-templates-researcher.md` and card T8 (video to demo trial) in `16-templates-trader-risk.md`. It takes one paper or one video, writes a replication spec from it, builds and runs it on our data and engine, and says whether the headline number came back and whether it lived after publication. Verdicts are set by scripts, not prose.

## Steps

1. `Source and ledger` (zero tokens) hashes the source (paper id, or the video URL without tracking parameters). A source already in the ledger ends the run with its hash and no new reading.
2. `Write the replication spec` (role `reader`, the card's reader) writes universe, period, signal, rebalance, costs, the exit (never invented), the variants the authors tried, every reported number with its word-for-word quote, and the open items.
3. `Reported numbers check` (the shared citation check) fails the run when a quote is not in the source.
4. `Assumptions and branches` keeps only numbers written in their own quote, labels every open item, gives a missing exit the house policy labelled `external_policy`, and raises a pick card when more than two assumptions change the meaning. At most two branches are built; each counts as a trial.
5. `Build and run in the Lab` (`scripts/lab.py`) is the one Lab and QMB call: the paper's in-sample period, our costs, and the post-publication period, touched once.
6. `Compare with the paper` sets the verdict: replicated, partially, not replicated or could not test, with Sharpe inside plus or minus 0.3 and every sign kept. A daily Sharpe above 2 holds it for a lookahead audit. The decay ratio feeds R9.
7. `Write the scorecard` (role `writer`) writes the summary; `Render and grade` checks its numbers against the source, the Lab runs and the comparison.

## Left out, and why

- The data-availability pre-check before any model call: it needs the data store's `data.available`, and data is held (ruling 91). The Lab call reports "could not test: data missing" instead.
- The validator re-reading the spec in a fresh context and the R7 seed and bootstrap spread: the spec's numbers are checked against their quotes by script; calibration joins once the Lab returns reruns.
- T8's grilling round on the holes and the "start demo trial?" signature: they end as the pick card in the result, because `human_gate` is unavailable; the demo trial is his act and the node's.
- The Library write of the result and the dead end: it needs the real Library's one-writer door.
- Test fixtures: they come with the Lab's real result shape.
