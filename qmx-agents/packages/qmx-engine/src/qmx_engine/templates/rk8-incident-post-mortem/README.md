# Explain a node incident: what restarted or stopped, why and when

The node watcher's daily review (STATE midday ruling 44, Part B `workflows.md` section 3). Each day it takes the newest node incident of the last 24 hours and writes a short, blameless note on it: what restarted or stopped, when, why in the node's own words, and when it was back. A script makes every number, the writer explains them, and the receipts grader holds each number to the step that made it. The note lands as a proposal; nothing is pressed.

Built from card R8 in `research/methodology/16-templates-trader-risk.md`, with its old read script replaced: it no longer waits for the trading node, because the node journal comes home (B15's harvester on This PC, B16's pull from servers).

## Steps

1. `Find the incident and its timeline` (`scripts/read.py`) reads the node journal through `journal_query`. An incident is a heal of the node's runtime, a stand-down's start, a kill switch rise above GREEN or a protection alarm. It takes the newest at or before `at`, and names what restarted or stopped, when, the node's own why, and when it was back (the runtime's next start for a heal, the stand-down's clear for a stand-down), with the time between in whole milliseconds. Its timeline is every lifecycle, stand-down, kill, protection and reconcile row of that machine around it, and the order rows are counted. It lands them as one `node-incident` artifact.
2. `No incident?` sends a quiet window straight to the land step with the script's own note: zero tokens.
3. `Write the post-mortem` (role `writer`, an `llm` with no tools) writes one paragraph from those findings and cites `read`.
4. `Check every number's receipt` (the shared `receipts-grader` block, carried in `receipts-grader/`) fails the run on any number the read step did not print.
5. `Land the note as a proposal` (the slow lane's `scripts/land.py`) lands one `note`, marked `proposal: true`, on the run's own ref.

Text the node took from outside (a cause, an error, a reason) is marked `qmx.marked/1`: the writer is told it is data, and the grader takes no number from it, so a note that repeats one fails.

## Settings

- `at`: the instant to look back from; the run's clock by default.
- `node`: one node machine; every node by default.
- `lookback_h` (24): how far back an incident is looked for.
- `around_min` (30): the minutes either side of the incident the timeline holds.
  When the node was back is looked for from the incident up to `at`, however long it took.
- `quote_chars` (500): how much of a node's outside text is quoted before an ellipsis.

The cron runs at 00:50 UTC, after the 00:00 UTC day close (WF-04). Missed runs follow the trigger's catch-up setting; reviews catch up once (WF-14).

## Left out, and why

- A run per incident on its own trigger: an event trigger has no payload naming the node row, so one run explains the newest incident of the day, and a manual run with `at` explains an earlier one.
- Why a whole node process restarted: the node keeps that in its own store, not in its journal, so the timeline shows the process `start` row without a why.
- The old draft's impact in R and dollars, its candidate causes and its challenger: no node row carries equity, and a note with one paragraph a script checks fits the slow lane.
- Deduplicating an incident seen before, and action cards: the note is the proposal, and workflow memory rows are not used yet.
