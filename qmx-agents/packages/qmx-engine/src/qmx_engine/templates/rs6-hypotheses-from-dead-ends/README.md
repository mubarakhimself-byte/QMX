# Hypotheses from dead ends

Waits for the real Library: its dead-end rows and workflow memory (`needs: real-library`).

Built from card R6 (hypotheses from Library dead ends) in `research/methodology/15-templates-researcher.md`. Weekly, it mines the negative results nobody keeps for new hypotheses, using a fixed list of moves, and gives him a short list of up to five. Nothing is tested without his pick, and no hypothesis may be tested on its parent's holdout.

## Steps

1. `Load dead ends from the Library` (`scripts/library.py`) is the one read: dead ends with their failure bucket, market, mechanism, source, family trial count and windows; the ids already mined; open term sheets, cards and rejected ideas.
2. `Cluster the new dead ends` (zero tokens) wakes only on 5 or more new dead ends and clusters them by bucket, market and mechanism, at most 10.
3. `Five or more new dead ends?` ends a quiet week silent, with no model call.
4. `Propose per cluster` (role `writer`, the card's miner) runs once per cluster and proposes with one fixed move each: condition, slow down, invert, transplant or drop.
5. `Dedupe and gate` drops a hypothesis whose parents are not its cluster's, that has no mechanism or kill rule, an invert with no mechanism, or a repeat of a term sheet, card or rejected idea. A kept one inherits the parent family's trial count and its test data starts after every parent window. Drop moves become "do not retry" notes.
6. `Rank and short list` ranks by the dead ends behind each hypothesis less the cost to test its move, and keeps 5 for his pick.
7. `Render and grade` checks every number in the hypotheses against the Library read and the clusters.

## Left out, and why

- R7 calibrate ("a real mechanism or a fitted story?" across two roles): it joins when real dead ends exist to calibrate against.
- His pick: it ends as the pick card in the result, because `human_gate` is unavailable. Picked versus ignored is a taste signal for RV once memory rows are used.
- Writing "do not retry" notes and the mined ids back to the Library: it needs the real Library's one-writer door.
- Test fixtures: they come with the real Library's dead-end rows, whose shape they must match.
