# PP Proposal pack he signs

Waits for the trading node's reads and the risk session's promotion rules (`needs: trading-node, risk-session`).

Built from card T6 (promotion evidence pack) in `research/methodology/16-templates-trader-risk.md` and card P4 (Lab-to-Portfolio proposal pack) in `17-templates-dev-pm-lab.md`. On request it bundles the evidence into at most three decision cards (promote to paper, paper to live, demote, add to the book) that he can sign or refuse in under five minutes, every claim checkable. It only proposes: nothing is written to the Portfolio or the node, and the upload to a live node stays his own click in the node UI.

## Steps

1. `Gather the evidence` reads each decision's evidence: term sheet, lineage and hash, backtest, walk-forward, holdout, demo or paper journal, live costs, overfit audit, stress result, validation verdict, tighten-only history, the P1 study, open incidents and the prop-firm rules.
2. `Checklist verdict` marks each row green, red or missing; a missing row keeps the checklist from all green.
3. `Independent validator` (role `reviewer`; an agent with no tools) tries to disprove each decision from the evidence, not the summary. A critical finding means refuse; a major one means conditions.
4. `Pre-mortem` (role `synthesiser`) imagines each decision failed three months later and says why.
5. `Write the cards` (role `writer`) gives each card a recommendation, the default if he does not answer ("extend demo 1 week" for a promotion), what silence means, the door type and the blast radius.
6. `Proposal pack` turns any "yes" into "not yet" when the checklist is not all green or a critical finding stands, and shows a contested critical finding in red. `Render and grade` checks every number on the cards against the evidence.

## Left out, and why

- His signature on each card and the write through the Portfolio's own path after it: human steps and Portfolio writes are not in this engine, and no template names a money act. The pack is the run's result.
- Rerunning the overfit audit when its hash is stale, the stress test with the unit added, and the R7 validation as subflows: real subworkflow bundles come first, so the pack reads their latest results.
- "Not independently checked" when the validator fails: a failed validator parks the run instead, so no card ships without a check.
- The `evidence_ready` event from the demo monitor: event triggers come with the node; the trigger is manual.
- Test fixtures: they come with the node's reads and the risk session's rules, whose real shape they must match.
