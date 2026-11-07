# QMX risk and sizing build program

This program delivers what he asked for on 7 November. A unit that can trade, size itself, configure itself and ship as a template, as a baseline anyone can use and a layer anyone can customize.
After it, the 31 labelled stand-ins for sizing, exits and halts are replaced, and the 18 sockets are widened or named as staying shut.
A fault in one block costs that unit its entries and never an exit. One unit's fault never reaches another. A scripted watch carries 200 units so he doesn't have to.
Every value stays a labelled placeholder until the numbers talk. Agents never touch money, and only he promotes.
There are {{COUNT}} PRs. RC-01 to RC-20 end at stop point A, RC-21 to RC-48 at stop point B, RC-49 to RC-66 at stop point C, and RC-67 to RC-69 need his demo sign-in.
The stack roots on the repair stack's tip through the branch `build/risk-core`. Nothing merges. He lands the stack himself.
Code truth for every Files block is `D:/QMX-worktrees/bld-repair-24` at `351e7521`.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with the stop point and slice of `arch/final/SPINE.md`, what it does in two sentences, what to read, and its gates and fallbacks. Then come the nine blocks `check-plan.mjs` requires. The "You see" block is written for him in plain words. No PR changes a screen, because the UI is another session and binds nothing here.

The stop points, each a whole baseline he may stop at.

- Stop A, after RC-20. One unit trades on paper from zero, with no broker and no judge, sizes itself, and brakes bind on any unit that declares them. A filter number moves by the built engine. A size or exit number first moves at RC-26, in stop B.
- Stop B, after RC-48. The whole single-unit baseline. Three templates side by side, modifiers, numbers that move, costs from fills, gate, stickers, two passes, no-stop.
- Stop C, after RC-66. Groups, pods, readings, shipping through mini apps, the fleet watch, re-test on every compiler bump.
- After stop C. RC-67 to RC-69 wait for his demo sign-in, and nothing deploys live before them or a re-test.

The program runs `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md` with light verification (his rule of 2026-10-15). Default builders are Claude Opus 5.5 through `poteto-agent` with `model: opus`, at most two at once, never two on a shared path, never two agents on one job. The coordinator runs lanes 1 to 4 in the background, a fresh Opus reviewer reads each diff, and there is one fix round. Low findings go to `lows.md` and anything new goes to `BACKLOG.md`.

The store is `D:/QMX-worktrees/risk-ship/`, with `RESUME.md`, `decisions.tsv`, `QUESTIONS-FOR-OPERATOR.md`, `BACKLOG.md`, `IDEAS.md`, `lows.md`, `QUEUE.md`, `ledger.tsv`, `BRIEF-BUILDER.md`, `tools/`, `dispatch/`, `review/`, `evidence/`, `homes/` and `data/`. PR branches are `build/rc-<nn>` in worktrees `D:/QMX-worktrees/bld-rc-<nn>`, where `<nn>` is the two digits of the PR id.

Three gates hold real steps for him, and the coordinator builds around each. G-SIGN holds a stop point's completion until he signs the trading node's new version, and no PR waits for it. G-DEMO holds his cTrader demo sign-in, which the demo lanes of RC-27, RC-67, RC-68 and RC-69 wait for. G-LAND holds every real step on his own QMX folder until he lands the code.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Check first that the repair stack is finished, as `PROMPT-ORCHESTRATOR.md` says. If it isn't, stop with the plain message there.
- [ ] Confirm the shell (Windows 11, PowerShell 7 and Git Bash) and the root. `git rev-parse origin/build/repair-24` is `351e7521` or newer. Logged in `RESUME.md`.
- [ ] Read the trunk rules with `git show origin/main:CLAUDE.md`, then his working copy `C:/Users/Mubarak/Desktop/QMX/CLAUDE.md`. Its QMA v2 section of 2026-10-13 is the pattern here, and the factory lanes in trunk's copy are retired.
- [ ] Create the store layout under `D:/QMX-worktrees/risk-ship/` and copy `BRIEF-BUILDER.md` into it.
- [ ] Create `build/risk-core` at the root and push it. The first PR targets it. Nobody moves it but him.
- [ ] Arm the audit tick as `/loop 1h` with the tick prompt in `PROMPT-ORCHESTRATOR.md`. Post a short status message to the operator only when a PR is stacked, a verdict lands, a gate opens or a blocker appears.
- [ ] Never stop to ask him. A question goes to `QUESTIONS-FOR-OPERATOR.md` with the default taken and how to undo it, and the build goes on. Only his money, his sign-ins and his clicks are his.

### Spawn owners

- [ ] Spawn one fresh Opus builder per PR in the background with `subagent_type: poteto-agent` and `model: opus`, from a dispatch file saved in `dispatch/`. Its first words are exactly "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents."
- [ ] Run at most two builders. The second slot takes the next PR in plan order whose Depends on PRs are all stacked and whose Files share no path with the running builder's (Appendix C). Record the empty intersection in `ledger.tsv` before the second dispatch.
- [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, his real home `~/.qmx`, `C:/Users/Mubarak/Documents`, `C:/Users/Mubarak/Desktop/DATA_NARL`, or any vault value. Lanes run on throwaway folders and a scratch profile only.
- [ ] Skip a PR whose gate is closed and dispatch the next unblocked one. Log the skip in `RESUME.md`.

The dispatch order, generated from the sections below by `plan-parts/assemble.py`. `plan-parts/check_program.py` refuses a PR that depends on a later one.

{{DISPATCH}}

### PR mechanics, for every PR

- [ ] The coordinator creates `build/rc-<nn>` from the current stack tip in `D:/QMX-worktrees/bld-rc-<nn>` before the dispatch. Never `git stash`.
- [ ] The builder opens the PR ready, never draft, within about 15 minutes, with `gh pr create --base <parent-branch> --head build/rc-<nn> --repo MubarakHimself/QMX`. The first PR's base is `build/risk-core`.
- [ ] Start every command that runs Python, pytest or uv with `source D:/QMX-worktrees/risk-ship/tools/env.sh && `. It unsets every `ANTHROPIC_*` and `CLAUDE*` name, sets `TMP` and `TEMP` to `D:/Temp` and `UV_CACHE_DIR` to `D:/Caches/uv`, and guards the Credential Manager. Work only on `D:`.
- [ ] The builder runs `fmt-check`, `lint` and `types` in each package it touched, `tools/secret_scan.py` and `tools/money_path_scan.py`, reads each exit code, runs only the fast tests it added or changed, and never waits on a long command. It runs the `blast-radius` skill on its diff before the last push.
- [ ] Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. PR bodies end with the Claude Code line.

### Verdict and merge, for every PR (append to the stack, never merge)

- [ ] At the code-ready head the coordinator runs lanes 1 to 4 in the background and saves their logs in `evidence/<id>/`. A test run has a time limit, and no leftover process stays after a verdict.
- [ ] A fresh Opus reviewer agent (one per PR, `model: opus`, told not to spawn sub-agents) reads the PR section, the full diff and those logs, applies the `bmad-review` lenses the section names, reruns the one blast-radius fact, and writes `review/<id>-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] Blockers go to one fix round by a fresh Opus builder on the same branch and worktree, given the dispatch file, the review file and the failing logs. The coordinator reruns only the failed lanes and the touched suites at the fix head. A second small fix, about 30 lines or less, is allowed. Anything bigger parks. Low findings go to `lows.md`.
- [ ] `ledger.tsv` gets head, parent, patch-id and the verdict.
- [ ] To append, the coordinator fetches the stack tip. If another PR was appended since the dispatch, it rebases the branch onto that tip, pushes with `--force-with-lease` after an `ls-remote` check, and sets the PR base to the tip's branch. A verdict stands when the patch-id is unchanged (`playbooks/shipping.md`).
- [ ] The whole-repo check runs in the background at the stack tip after every eighth appended PR and at RC-20, RC-48 and RC-66, with `tools/run_tests.sh`. A whole run took 6,816 s at `-n 2`. A red at the tip is traced to its PR, and that PR gets the fix round.
- [ ] He lands the stack himself from the list the coordinator keeps in `STACK-LIST.md`. Nobody else merges, closes a PR or deletes a branch.

### Boot recipe, for every live lane

- [ ] `git worktree add --detach D:/Temp/<id>-check <head>`, then `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] A lane runs on a throwaway QMX folder under `D:/QMX-worktrees/risk-ship/homes/<id>-<lane>/`. Only the coordinator boots a host, through `tools/safe_host.py`.
- [ ] A lane with a model uses the plan login of the ship home `D:/QMX-worktrees/qma-ship/home` on `haiku`, holding `D:/QMX-worktrees/.engine-lane-lock`. No Anthropic or OpenAI API spend.
- [ ] Order lanes use the fake broker or the practice venue, never a real account. The fake broker is the fake cTrader behind the real `CTraderVenue`, as `qmn/tests/test_app_broker_wins.py` drives it, holding only the fields the definitions pin. A lane after G-DEMO uses his demo account only.
- [ ] Each lane script exits non-zero on any failed check. The coordinator greps every PASS and FAIL line, never only the exit code.
- [ ] Never name a PowerShell variable `$home`. Save captures as `evidence/<id>/check-<slug>.log`, then remove the check copy with `git worktree remove` and confirm no `qmx_host`, `claude` or `node` process from the lane is left.
