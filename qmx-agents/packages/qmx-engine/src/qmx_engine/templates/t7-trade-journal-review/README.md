# T7 Trade journal review in R

Waits for the trading node: its R journal with trade tags (`needs: trading-node`).

Built from card T7 in `research/methodology/16-templates-trader-risk.md`. Every Saturday at 09:00 it finds what is really different in his results by session, setup or market condition, without telling stories about noise, and turns at most three real findings into lessons for his yes or no.

## Steps

1. `Load the R journal` reads the closed trades since the last review with their tags.
2. `At least 20 new trades?` sends a thin week to `Too few trades`, a zero-token card.
3. `Stats by slice` reports a slice only when n is at least 20 and its 90% bootstrap interval on expectancy excludes the overall mean, beside the R histogram, exit efficiency, stop hunts, streaks, rule breaks and manual trades in their own lane.
4. `Draft lessons` (role `synthesiser`, the card's analyst) drafts at most three lessons as hypotheses. `Judge each lesson` (role `judge`) keeps only lessons that match their slice's stats.
5. `Explainer` and `Render and grade` check every number in the lessons against the journal and the slice stats.

## Left out, and why

- His accept or reject per lesson card, and a lesson accepted three times turning into a proposal to encode it: human steps and the lessons table are later packets. Lessons are the run's result.
- Deduplication against past and rejected lessons: operator memory rows are not used yet.
- The MAE/MFE scatter and the slice heatmap as drawings: the output carries the numbers; rendering is UI-side.
- The light daily slice folded into the end-of-day wrap: DB carries the wrap without node facts until the node exists.
- Test fixtures: they come with the node's read model, whose real shape they must match.
