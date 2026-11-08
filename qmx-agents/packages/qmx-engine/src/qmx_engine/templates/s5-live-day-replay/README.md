# Replay a live unit's day on QMB and diff its decisions

The slow lane's live-day replay (STATE midday ruling 44, Part B `workflows.md` section 3, QB-23). QMB replays a live unit's day from the bars the node recorded and diffs its decisions against the live ones, so a unit trading on something its own test never saw is caught. Script only: no model is asked. A match under the setting lands one bench proposal for his click; nothing moves the unit.

## Steps

1. `Read the live day` (`scripts/route.py`) reads the unit's `live` `signal` rows for the day through `journal_query` and writes QMB's `replay_check` ask: the unit's pin, the bars window and the live rows. A day with no live rows is quiet, and QMB is not asked.
2. `Replay the day on QMB` (`app_op`, job `replay_check`) replays the window with the same compiled unit through the same handler and diffs the decisions (`qmb.analysis.replay_diff`).
3. `Diff the decisions` (`scripts/diff.py`) reads the job's `matched` and `differs` and works out the match. Under `warn_below` it makes one `bench` card. A replay that did not finish is reported with its reason. It writes the note itself and lands the diff as one `replay-diff` artifact.
4. `Land the diff as a proposal` (`scripts/land.py`) lands the note and any card, each marked `proposal: true`.

A test run names `fixture: recorded` (19 of 20 decisions alike) or `recorded-drift` (3 of 4), and `Replay the recorded answer` stands in for QMB from `fixtures/qmb.json`.

## Settings

Starting defaults, never caps: `warm_up_days` 5, `warn_below` 0.80 (Part B `workflows.md` section 6, the replay match warning).

## Left out, and why

- A nightly trigger after each market's session close: one run replays one unit's day, because a QMB job is one `app_op` call and the unit's pin is not in its journal rows. He starts it per live unit, or adds a trigger per unit with its pin.
- The diff's decision list in the note: the job's report file lands with its QMB result, which `backtest_status` reads; the note carries the counts.
