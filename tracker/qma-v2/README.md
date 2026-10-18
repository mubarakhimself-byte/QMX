# QMA v2 planning tree

This folder holds the plan for QMA v2: the agent harness (built), the workflow engine (core built), the Library, the Lab and Pods, and the next coding program (being planned). Re-centralized on 2026-10-18 evening.

## Read first

1. `research/methodology/26-operator-rulings-and-alignment.md`: the operator's rulings 1-114. The latest ruling wins and outranks every other file.
2. `research/methodology/33-state-of-play.md`: what is merged, what is designed and not built, his parked calls, and the full file index.
3. `HANDOFF-2026-10-18.md`: how the planning lead works and the rerun steps (1-7 done; 8 plan the next program and 9 his calls and the coding prompt are next).

## Where things live

| Path | What it is |
|---|---|
| `research/methodology/39-architecture-rerun.md` | The current design record, with "Review applied" (41) and "Fix-check applied" (42) at its end |
| `research/methodology/40-retriage.md` | 189 engine-run issues mapped to the rerun, and the packet order for the next plan |
| `architecture/workflow-engine/`, `library-and-data/`, `lab-and-pods/` | The three architecture spines and their companions |
| `UI-HANDOFF.md` | Everything the UI session needs (`UI-NOTES.md` holds older harness event details) |
| `wayfinder/` | Open questions as tickets; `python -I wayfinder/frontier.py` prints the frontier |
| `BACKLOG.md` | His backlog in his own words; superseded rows are marked |
| `AUDIT-2026-10-18.md`, `alignment/`, `RECOLLECTION-2026-10-18.md` | The disk audit and the transcript alignment of 2026-10-18 |
| `research/methodology/01`-`38`, `research/one-engine/`, `research/sources/` | Studies and sources (inputs, not the plan) |
| `DELETION-PLAN.md`, `PROMPT-DELETION.md` | The old-code deletion D1-D4, still owed; rewrite before use |
| `WORKFLOW-SHIP-PREP.md` | How a design was taken to a coding prompt, and the mistakes not to repeat |
| `reviews/`, `trail/` | Audits and the planning trail of 10-12 to 10-14 |
| `archive/` | Superseded files, one dated folder each with a `SUPERSEDED.md`. Evidence only, never the plan |

## Code truth

`origin/engine/base` = `132169c7` (engine stack, harness minus HP2). `origin/rebuild/base` = `4345eafa` (adds HP2 and two test fixes). Merging the first into the second is the operator's click. `main` moves only by his own squash-merge click.
