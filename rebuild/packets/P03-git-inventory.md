# P03: Git and branch inventory (report only)

## Goal
The operator has lost track of branches, worktrees and PRs created by several agents (Grok, Codex, Aurelius, Claude). Produce one table so the operator can approve a clean-up. **Change nothing.**

## Inputs
- `git branch -a`, `git worktree list` in `C:\Users\Mubarak\Desktop\QMX`
- `gh pr list --state all --limit 100`
- Codex worktrees under `C:\Users\Mubarak\.codex\worktrees\`
- The recovery repo `D:\Codex-Recovery\2026-10-04\integration-base.git` and its backup `C:\Users\Mubarak\Desktop\QMX-backups\`

## Output
Create `rebuild/reports/git-inventory.md` with these sections:
1. **Branches.** One row per local or remote branch:
   - name, last commit date, author identity
   - ahead/behind `origin/integration`
   - merged into `integration` (yes/no)
   - open PR, worktree path if checked out
   - **recommendation:** keep / archive (tag `archive/<name>` then delete the branch) / delete, with a one-line reason
2. **Worktrees.** Path, branch, dirty or clean, recommendation.
3. **PRs.** Number, title, state, base/head, recommendation. PRs #20–#24 are superseded by #25 (same production code plus MA01–MA04).
4. **Proposed commands.** The exact `git` and `gh` commands to carry out the recommendations, in a code block, **not executed**.

## Rules
- Read-only. No `git branch -d`, no `gh pr close`, no worktree removal.
- Never recommend deleting unmerged work without an archive tag.
- Protected: `main`, `integration`, `ui-integration`, `rebuild/base`, `ui-review/repair` (the current UI) are always keep.

## Done when
The report exists, covers every branch and worktree, and the PR description summarises the counts.
