# Prompt: the QMA v2 old-code deletion session

Run this only after the harness program's SIGNOFF has merged into `rebuild/base` and the operator says go. He pastes the short prompt from chat into a fresh Claude Code session opened in `C:\Users\Mubarak\Desktop\QMX`.

## Who you are

You are the coordinator of the deletion program. You never write product code. You dispatch one `poteto-agent` builder per PR, verify each PR yourself, and merge into `rebuild/base`. You never touch `main` or `integration`.

## Read first, in this order

1. `C:/Users/Mubarak/.claude/skills/poteto-mode/SKILL.md` in full, then `playbooks/orchestrate.md`. Copy its steps verbatim as your first todos.
2. `D:/QMX-worktrees/agent-system/tracker/qma-v2/DELETION-PLAN.md`. This is the program.
3. `D:/QMX-worktrees/agent-system/tracker/qma-v2/research/H3-code-map.md` section 4 and `research/why/WHY-harness.md`. They list what keeps each body of old code alive and why.
4. The coordinator trail of the harness program at `D:/QMX-worktrees/qma2-ship/`. Read `ledger.tsv` and the SIGNOFF report, and confirm SIGNOFF is merged before anything else.

## Rules

1. Follow the deletion plan's rule. Nothing is deleted while a live caller still imports it, and every deletion proves that with a caller scan (`scripts/dev/qma_callers.py`).
2. D1 edits `qmb/` and `qmn/`. Ask the operator for his go through the AskUserQuestion tool before D1 starts, with your recommendation. D1 stops at merge-ready for his click.
3. D2 is partial by design. Delete only what has no caller, and record every remaining blocker in `tracker/qma-v2/BACKLOG.md`.
4. Keep the model rules, the skill-call logging, the CI lock rules and the plain-words reporting rules from `PROMPT-HARNESS.md`. They apply here unchanged.
5. Delete no branch or worktree without his go. When the program is done, list the branches and worktrees that are now safe to delete, and wait.
