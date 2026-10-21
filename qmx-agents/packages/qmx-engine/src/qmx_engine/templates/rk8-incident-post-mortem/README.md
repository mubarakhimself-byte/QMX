# Incident post-mortem

Waits for the trading node: its event log and account reads (`needs: trading-node`).

Built from card R8 in `research/methodology/16-templates-trader-risk.md`. For an incident closed at red or above, it writes a blameless account of what happened, what it cost in R, why, and which check would have caught it. Every statement cites a timeline event.

## Steps

1. `Incident and timeline` reads the incident and every event within two hours either side, from the guard, the node, the broker's deals, the MIS state, the calendar, spreads and the run logs.
2. `Impact in R and dollars` computes the loss and the cushion before and after.
3. `Draft the post-mortem` (role `synthesiser`, the card's analyst; an agent with no tools) writes what happened, contributing factors, candidate causes in the card's fixed categories, and up to four actions.
4. `Every statement cited` (the shared citation grader) fails the run if any quote is not in its timeline event.
5. `Challenge the draft` (role `reviewer`, the card's validator) tries to disprove it.
6. `Post-mortem` and `Render and grade` check every number in the prose against the timeline and the impact.

## Left out, and why

- The trigger on an incident closed at red or above: incidents and event triggers come with the node; the trigger is manual with an `incident_id` until then.
- Deduplicating by signature within 7 days, and a signature seen three times auto-proposing a check: the lessons table and workflow memory rows are later packets.
- His acceptance of each action card: human steps are a later packet; actions are the run's result.
- The scroll-story rendering: the output carries the timeline; rendering is UI-side.
- Test fixtures: they come with the node's read model, whose real shape they must match.
