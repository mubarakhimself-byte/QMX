# P1 Portfolio combination study

Waits for the trading node's journals and the risk session's method list (`needs: trading-node, risk-session`).

Built from card P1 in `research/methodology/17-templates-dev-pm-lab.md`. On request it answers "does this candidate add anything to the book, and how would they combine?" with a simulation that changes nothing. Zero tokens until the writer.

## Steps

1. `Load the return streams` reads candidates' out-of-sample and paper streams (never in-sample) and the book's paper and live streams, aligned with costs on. A candidate without an out-of-sample stream is dropped with "could not study".
2. `Correlate, combine and stress` computes correlations in full and in crisis windows, drawdown overlap, each method in the list (equal weight, inverse volatility, risk parity, hierarchical risk parity) at monthly and quarterly rebalancing with turnover costs, the worst drawdown, and each candidate's marginal Sharpe with a 90% block-bootstrap band. A band that crosses zero is never "adds to the book". Every method reads "study only".
3. `Write the study` (role `writer`) writes the headline and the findings. `Book picture` and `Render and grade` check every number in the prose against the study.

## Left out, and why

- The pre-check on overlap with the book (default 12 months) as its own node: the read script applies it and lists what it drops.
- The R7 calibrate subflow on the marginal value: the block-bootstrap band in the study stands in for it until real subworkflow bundles exist.
- Clustering beyond the hierarchical risk parity ordering, and the methods the risk session will add: the method list is the risk session's data.
- Storing the study with its inputs' hashes for the proposal pack: the run's artifacts carry it; a typed Library object is a later packet.
- Test fixtures: they come with the journals and the method list, whose real shape they must match.
