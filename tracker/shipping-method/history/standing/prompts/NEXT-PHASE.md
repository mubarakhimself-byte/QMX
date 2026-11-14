# Starting the next phase

The four phases chain themselves: plan, plan review, build (coordinator), checkpoint review. The checkpoint review merges the checkpoint itself when it is clean, then starts the next coordinator segment if none is running; the coordinator keeps pre-building the next checkpoint while a review runs. He never pastes a prompt. Each phase ends by starting the next session itself, from files on disk. Every prompt in this folder points here for that step.

| Phase | Skill | Prompt it fills | The session runs in |
|---|---|---|---|
| Plan | `plan-feature` | `PLAN.md` | `C:/Users/Mubarak/Desktop/QMX` |
| Plan review | `plan-review` | `PLAN-REVIEW.md` | `C:/Users/Mubarak/Desktop/QMX` |
| Build | `ship-build` | `COORDINATOR.md` | `{PROGRAM}` (the ship hook loads from its `.claude/`) |
| Checkpoint review, then merge | `stop-review` | `STOP-REVIEW.md` | `D:/QMX-worktrees` |
| Merge, by hand only | `ship-merge` | `MERGE.md` (runs STOP-REVIEW's Merge section) | `D:/QMX-worktrees` |
| Not sure which | `ship-next` | reads the program's files and runs the right one | any |

No phase starts `ship-merge`. It exists for his "merge stop <X>" after a merge that did not finish.

The skills live in `C:/Users/Mubarak/Desktop/QMX/.claude/skills/<skill>/SKILL.md`. Sessions in `{PROGRAM}` or `D:/QMX-worktrees` do not see the project's skills, so a session's brief names the skill file by its full path.

## How to start it

Call `mcp__ccd_session__start_session` (load it with ToolSearch `select:mcp__ccd_session__start_session` if it is deferred) with:

- `initiation: "user_asked"`, `context: "fresh"`, `use_worktree: false`;
- `cwd`: the folder in the table;
- `title`: `<phase>: <program>`, adding `stop <X>` where there is one, for example `Stop review: pod-scalping stop A`;
- `prompt`: `Read C:/Users/Mubarak/Desktop/QMX/.claude/skills/<skill>/SKILL.md in full and follow it for program <PROGRAM>.`, followed by the stop and round when the phase has them;
- `background`: one or two sentences: the program, what the phase before it finished, and that he never pastes prompts.

Then:

1. Append one line to `{PROGRAM}/notes/SESSIONS.md`: `<date> <phase> <session id> <title>`.
2. Tell him in one plain sentence what started. For example: "Plan review for pod-scalping has started."
3. End your turn.

## When it cannot start

The tool may be missing, or the app may refuse the start. It refuses starts on a turn that another session's message or an automated wake began, such as the coordinator's heartbeat. Then:

1. Propose the session instead: the same call with `initiation: "own_initiative"`. He starts it with one click.
2. Write one line in `{PROGRAM}/notes/WAITS-ON-YOU.md` naming the phase and the sentence below.
3. Tell him exactly one plain sentence he can say in any QMX session, never a prompt to paste:

| Phase | He says |
|---|---|
| Plan review | "review the plan for <program>" |
| Build | "start building <program>" |
| Checkpoint review (merges when clean) | "review stop <X> of <program>" |
| Merge, after a merge that did not finish | "merge stop <X> of <program>" |
| Any | "continue <program>" |
