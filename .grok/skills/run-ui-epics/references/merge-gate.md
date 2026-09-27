# UI merge gate

Inputs: `WT`, `BR` (`ui-epic/NNN-slug`), destination from
`tools/ui_factory/config.json` (`ui-integration`). The shared checkout
never switches branches.

```
python tools/ui_factory_cli.py merge-gate \
  --worktree WT --branch BR --unit-id EPIC \
  --files <changed> [--user-facing] [--blocking "finding1,finding2"]
```

Do not pass `--push` until local ff-merge succeeded and you intend to
update `origin/ui-integration`. Never push to `integration`.

## Green path

1. `git fetch origin`
2. Rebase `BR` onto current `origin/ui-integration` (or local
   `ui-integration` in factory tests). Conflict → abort → BLOCKED.
3. Re-run quality CLI on the **rebased SHA**. Commands and evidence
   files judge. Agent `passed=true` is ignored.
4. User-facing units still missing Reticle `verified: "yes"` → BLOCKED
   (`incomplete`).
5. Blocking review findings → BLOCKED.
6. ff-only merge into `ui-integration` via throwaway worktree
   `QMX-worktrees/merge-ui-integration-tmp`.
7. Optional `git push origin ui-integration`.
8. `python tools/ui_factory_cli.py ci-wait --sha <candidate> --branch ui-integration`
   A push is not success. If `gh` cannot see runs, record
   `incomplete` / simulated separately. Do not merge an untested SHA if
   the destination moved during CI — rebase and re-run.
9. Remove the epic worktree only after the branch is contained in
   `ui-integration`. Keep the branch.

## Blocked path

Merge nothing. Leave worktree and branch. Report the failing command,
evidence path, or conflicting files. Continue independent epics only.

## Never

Touch `main` · merge to `integration` · force-push · delete branches ·
remove a worktree whose branch has not merged · auto-promote to
deployment.
