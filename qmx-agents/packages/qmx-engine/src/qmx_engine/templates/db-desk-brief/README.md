# DB Desk brief

Built from cards T1 (morning brief), T2 (pre-session read) and T10 (end-of-day wrap) in `research/methodology/16-templates-trader-risk.md`. One screen before a session: what is on today for the watchlist, what the research desk, the calendar watch and the paper scout found, and what needs him. It runs at 06:00 London (morning), 07:30 New York (pre-session) and 17:05 New York (end of day), weekdays, and on request. Until the trading node exists, every node fact (account, cushion, open risk, overnight result, positions, unit states, session conditions) reads `could not check: trading node`.

## Steps

1. `Gather the day` is the zero-token gather. It reads the watchlist's releases from the free calendar (tomorrow's too at the end of day), the latest live result of T4, T3 and RS1 from the last 36 hours, and the open inbox items, all from the engine in its own home. Test runs are never read.
2. `Quiet day?` sends a day with no release above low impact, no desk or research item, no alert and no decision to `Quiet-day card`, rendered by script with zero tokens.
3. `Rank the items` puts alerts first, then at most three decisions, then the releases (high impact first), then the desk's lines, then at most three research items.
4. `Write the brief` (role `writer`) writes the headline, a summary of at most 150 words, up to three decision cards (recommendation, default, what silence means) and up to five watch lines.
5. `Every link and decision traced` fails the run if a watch line links to a source the gather did not find or a decision names a run with nothing waiting.
6. `Brief card` puts the writer's text beside the tiles, which come from the gather and never from the model. `Render and grade` (the shared `render-and-grade` block) checks the card against `schemas/output.json` and every number in the prose against the gather. A failed check stops the run as failed.

## Test runs

A run started with `{"fixture": "busy"}` or `{"fixture": "quiet"}` replays the matching synthetic day in `fixtures/`. Install tests the busy day on real models; the quiet day makes no model call. `fixtures/recorded/` holds the writer's answer for the `--fake` switch and the unit tests.

## Roles

`writer` writes the brief. Roles come from Settings; no model is named here.

## Left out, and why

- The node facts (equity and kill-line cushion in R, open risk, overnight result, positions, unit states) and T2's per-unit MIS conditions grid and its mirror check: they need the trading node's read model and the unit adapter.
- T10's day result in R and dollars per unit, the closest approach to the kill line (R1), the day cost ratio (T9) and Friday's weekend gap and swap checks: they need the node's journal and the risk watchdogs.
- "What changed since yesterday" from yesterday's brief, and demoting sections he never opens: workflow and operator memory rows are not used yet. The quiet-day test is "nothing above low impact and nothing new in the last 36 hours" instead.
- Delivery to the inbox and the digest: the brief is the run's result; notifications are UI-side (ruling 77).
- The editable `scalper-types` table: it belongs with the session conditions above.
