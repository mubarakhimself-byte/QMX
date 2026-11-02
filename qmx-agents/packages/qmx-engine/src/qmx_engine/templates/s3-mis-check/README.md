# Check the MIS against an agent's own read of the market

The slow lane's MIS check (STATE midday rulings 44 and 50, Part B `workflows.md` section 3). Each day after the 00:00 UTC close an agent reads the market its own way beside what the MIS published, and every place it reads differently becomes an example for him to improve the MIS. Agents never feed the fast lane: the examples are notes, and nothing changes the MIS.

## Steps

1. `Read what the MIS said` (`scripts/read.py`) reads the day's MIS reading history through `readings_query`, whose holdout refuses a held-out window by name; a refused reading is listed, never read around. Per market and reading it prints the rows published, the words and healths by count, and every change point. It lands them as one `mis-check` artifact.
2. `No reading history?` lands the script's own note on a day with none: zero tokens.
3. `Read the market beside the MIS` (an `agent` step, role `reviewer`, toolset `data`) reads the bars around each change point with `data_bars` and `data_features` and names each change point it reads differently. Its numbers come only from the read step; what it reads from the bars it says in words.
4. `Check every number's receipt` (the shared `receipts-grader` block, carried in `receipts-grader/`) fails the run on any number in the note the read step did not print.
5. `Keep the examples that point at a change point` (`scripts/examples.py`) drops a disagreement that names no change point the read step printed, and fails the step on one that states a number, since the agent's tool reads leave no receipt.
6. `Land the disagreements for him` (`scripts/land.py`) lands one `note` of kind `disagreement`, marked `proposal: true`, linking each example to its reading row (`reading|market|at`).

## Settings

`readings` defaults to the MIS's default packs' reading ids; `markets` to every market the MIS read. The cron runs at 00:45 UTC, after the day closes for 24/7 markets (WF-04). Missed runs follow the trigger's catch-up setting; reviews catch up once (WF-14).

## Left out, and why

- Numbers from the agent's own read of the bars: the engine records an agent's tool calls, not their results, so they cannot be receipts. The agent says what it sees in words, and every number that lands comes from the read step.
