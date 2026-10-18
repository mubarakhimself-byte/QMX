# RV Weekly review

Built from card R9 in `research/methodology/15-templates-researcher.md` with D10 in `17-templates-dev-pm-lab.md`. Every Monday it reads the week's runs and the open inbox from the engine itself, not from the Library, clusters the failures, and proposes at most three edits as a change card. Nothing changes until he approves an edit.

## Steps

1. `The week's runs and inbox` reads every run started in the last seven days from the engine's ledger and service (its status, tokens, and each failed step or failed check), the parked runs, and the open inbox items. This review's own run is left out.
2. `Any run this week?` ends the run silently when no run started.
3. `Cluster the failures` (role `reviewer`) groups the failures by signature and names a likely cause.
4. `Propose at most three edits` (role `writer`) targets a prompt, a question battery, a brief, skill text or a pre-check rule.
5. `Reject loosening edits` rejects any edit that loosens a gate, threshold, budget, retry count or limit, and marks every other edit untested.
6. `Change card` puts the engine's runs, parked runs and inbox items, exactly as reported, beside the clusters and the edits. `Render and grade` checks it against `schemas/output.json` and checks the numbers in the clusters and edits against the week.

## Test runs

A run started with `{"fixture": true}` reads `fixtures/week.json`, a synthetic week. Run without it, the review reads the home it runs in. `fixtures/recorded/` holds the answers for the `--fake` switch and the unit tests.

## Left out, and why

- Testing each edit by forking past failed runs and replaying a fix set and a guard set, and the eval set before and after: replay of past runs on an edited folder is not built, so every edit is "untested", which cannot be approved.
- His approval of each edit and the new folder version: a human step and versioning an edit are later packets; the change card is the run's result.
- His thumbs, board iteration counts, calibration outcomes (Brier scores), replication decay and triage misses: no such records exist yet.
- The lessons table of past proposals: workflow memory rows are a later packet.
- D10's code health of Lab artifacts (lint, types, tests, dead code, no-future tests, reproducibility reruns, data snapshot integrity, dependency drift, orphans, fix drafts): they need the Lab, the sandbox and the data store.
