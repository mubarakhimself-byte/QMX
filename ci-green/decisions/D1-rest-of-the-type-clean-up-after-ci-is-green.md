# D1: Does the rest of the type clean-up come after CI is green, or in the same batch?

Status: settled
Mode: plan
For: him
Raised by: challenge (proposed question 1)

## Recommendation

After. Two small PRs make CI green, and they go first on their own. The rest of the clean-up follows in up to three later PRs, once a green run has proved the first two.

## Why

CI is red for two reasons only. One test file ends in eight extra blank lines, and two files in the trading node use Windows-only calls that the Linux type check cannot read. Fix those and a full CI run can pass, which is what lets anything merge again.

The plan also carried 57 more type warnings of the same kind, spread over five other packages. They are real and worth fixing, but CI already tolerates them: they sit on a known list and block nothing. Fixing them touches ten files, among them the backup restore, the helpers that copy your data and the process launcher.

Until the first green run, nothing else can merge, including the held risk work. So every extra file in that first batch is one more way for the only batch that reopens merging to fail. Putting the 57 warnings in later PRs costs nothing: they stay on the known list in the meantime, and no new one can slip in, because CI already blocks any warning that is not on the list.

Your own rule from 13 November says the same: the first PRs prove the thing works, and the nice-to-haves come in later PRs.

If you prefer everything in one batch, it is five PRs in one checkpoint, not two.

## Answer

"After CI is green (Recommended)" (dd8f4ab2:L10701 (Shipping rate and agent orchestration, 2026-11-14)), his answer to the cut question "Should those 57 come after CI is green, as up to 3 later PRs, or in this same batch, which would grow it from 2 PRs to 5?"
