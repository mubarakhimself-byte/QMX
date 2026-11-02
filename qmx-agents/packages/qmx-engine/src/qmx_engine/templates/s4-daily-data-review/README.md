# Review the day's data: gaps, clock flags and offsets

The slow lane's daily data review (STATE midday ruling 44, Part B `workflows.md` section 3), in the check style of `connections-health`. Each morning one short note on the data this machine holds, like the data page of a trader's journal. Scripts count everything, the writer explains it, the receipts grader holds each number to the step that counted it, and the note links every series to its dataset card.

## Steps

1. `Count the day's gaps, clock flags and offsets` (`scripts/read.py`) reads every price series the market-data door holds and its card from the door: the months, the months not yet frozen, the gaps each month's freeze recorded, and the partition fingerprints. Through `journal_query` it counts the day's unit, market and node rows stamped `clock_ok = false`, per stream and machine, and the market journal's `offset` rows per market. It lands the review as one `data-review` artifact.
2. `Nothing held?` lands the script's own note when the machine holds no series and no flagged or offset row: zero tokens.
3. `Write the data note` (role `writer`) writes one paragraph from the counts and cites `read`.
4. `Check every number's receipt` (the shared `receipts-grader` block, carried in `receipts-grader/`) fails the run on any number the read step did not print.
5. `Land the data note as a proposal` (`scripts/land.py`) lands one `note` artifact, marked `proposal: true`, with one `about` link per series card.

## Settings

The cron runs at 07:00 in This PC's zone, his routine (WF-03), and reviews the UTC day before.

## Left out, and why

- Writing `offset` rows: the market journal has one writer per stream (Part B AD-208), the feed keeper, so a workflow reads offsets and never writes them.
- Seams and the source clock from the dataset card in the Library: a workflow script cannot read Library items, and the door's card carries months, fingerprints and gaps. The gaps a month's freeze recorded stand in for a fresh count; the `data-quality` block counts a month afresh against its calendar when it is landed.
- The downloaders' results and the records job's `maintenance-result`: they are Library items too.
