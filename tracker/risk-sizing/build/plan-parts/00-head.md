# QMX unit system build program

This program builds the unit system the architecture in `tracker/risk-sizing/architecture/` designs, for him as the one person who trades with QMX and for the agents that write and judge units for him.
It carries out STATE midday rulings 1 to 55, which say there is no throwaway prototype, the foundation comes first, QML comes first with the most care, and every PR keeps the shipped tests green.
There are 73 PRs in 7 phases. Phase 0 is the dummy unit end to end (A0 to B9). Then QML and the dictionary, QMB, journals and agents, the MIS, the trading node, and last the workflow templates, mini apps and records home.
The stack roots on `origin/engine/base` at `c93407ca` (or newer) through the branch `build/unit-system`. Nothing merges. He lands the stack himself.
Code truth for every Files block is the three part folders under `architecture/parts/`, read at `c93407ca` in `D:/QMX-worktrees/engine-base-read/`.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a preamble that names its phase, its slice in the part folder, the architecture decisions and rulings it carries out, its real step and its done line. Then come the nine blocks `check-plan.mjs` requires. The "You see" block is written for him in plain words. Most PRs change nothing on a screen, because no UI code is written in this program (ruling 45), so "You see" says what he can ask the copilot, read in the Library, or run, and the screens themselves are in `UI-NOTES-UNITS.md` for the UI session.

The phases run in this order.

- Phase 0, the dummy unit end to end (18 PRs). The dummy unit is written through the authoring door, checked deterministically, backtested by QMB with trades in money and R, and its journal is written, and one of its numbers moves by its own rule. B9's lanes run the whole proof.
- Phase 1, QML and the dictionary in depth (10 PRs). The identity table, runtime care, the instrument records QML converts through, the dictionary's form, the port of the 239 entries, the first content wave with no cap, and the risk socket's checks.
- Phase 2, QMB in depth (6 PRs). Long runs, realism, futures, conformance and variants, the judge, and the other run kinds.
- Phase 3, journals, the copilot and agents (3 PRs). Journals readable by agents and him, workflow agent steps that can write, and the in-loop check hook.
- Phase 4, the MIS on This PC (6 PRs). Calendars, two mini-app core changes, the reading blocks, the MIS app, and the two core read rows.
- Phase 5, the trading node and external connections (22 PRs). Clocks, deep logs, the last two core changes, the host route, contract markets, then the node from its smallest form to a server and the live binding path.
- Phase 6, workflow templates, mini apps and records home (8 PRs). The example apps, the shared template pieces, the build-and-prove family, the slow lane, records from servers and the node watcher.

The MIS comes before the node because ruling 35 says QML, the MIS and the contracts are built first and then assembled into the node. Care follows his priority, QML first, the node second, the MIS third.

The program runs `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md` with light verification (his rule of 2026-10-15). Builders are Claude Opus 5.5 through `poteto-agent` with `model: opus`, at most two at once, never two on a shared path, never two agents on one job. The coordinator runs lanes 1 to 4 and at most one menu lane per PR in the background, a fresh Opus reviewer reads each diff, and there is one fix round. Low findings go to `lows.md` and anything new goes to `BACKLOG.md`. See `playbooks/` in the poteto-mode skill for the rest.

The store is `D:/QMX-worktrees/unit-ship/`, with `RESUME.md`, `decisions.tsv`, `QUESTIONS-FOR-OPERATOR.md`, `BACKLOG.md`, `IDEAS.md`, `lows.md`, `ledger.tsv`, `BRIEF-BUILDER.md`, `dispatch/`, `review/`, `evidence/`, `homes/` and `data/`. PR branches are `build/us-<id>` in worktrees `D:/QMX-worktrees/bld-us-<id>`, where `<id>` is the PR id in lower case without its hyphen (`a0`, `b5b`, `c05a`).

Four gates hold real steps for him, and the coordinator builds around each one. G-LAND holds every real step on his own QMX folder or his server until he lands the code. G-DEMO holds his cTrader demo sign-in for the practice node (ruling 37), which C-14's real run, C-15's probe run and the C-20 cut wait for. G-WALLET holds his Hyperliquid testnet agent wallet, which C-16's probe run waits for. G-SERVER holds a node on his server, which the server lanes of C-17, C-19, B16 and B21 wait for. A PR whose proving lanes need a gate is built and checked on fakes and the conformance venue, and its gated lane is a menu lane run after the gate opens.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [x] The plan passed `node C:/Users/Mubarak/.claude/skills/poteto-mode/scripts/check-plan.mjs UNIT-PLAN.md` on 2026-11-01, after `node plan-parts/assemble.mjs` built it. The checker's last line reads "73 PR sections, 0 problems".
- [ ] Confirm the shell (Windows 11, PowerShell 7 and Git Bash) and the root. `git rev-parse origin/engine/base` is `c93407ca` or newer. Logged in `RESUME.md`.
- [ ] Read the trunk rules with `git show origin/main:CLAUDE.md`, then his working copy `C:/Users/Mubarak/Desktop/QMX/CLAUDE.md`. Its QMA v2 section of 2026-10-13 is the pattern here, and the factory lanes in trunk's copy are retired.
- [ ] Read `STATE.md` from the plan branch with `git -C D:/QMX-worktrees/unit-plan show plan/unit-system:tracker/risk-sizing/STATE.md`, the midday rulings 1 to 55 and "How standing order 7 reads". The latest ruling wins.
- [ ] Create the store layout under `D:/QMX-worktrees/unit-ship/` and copy `BRIEF-BUILDER.md` into it from the plan branch.
- [ ] Create `build/unit-system` at `origin/engine/base` and push it. The first PR targets it. Nobody moves it but him.
- [ ] Arm the audit tick as `/loop 1h` with the tick prompt in `PROMPT-ORCHESTRATOR.md`. Post a short status message to the operator only when a PR is stacked, a verdict lands, a gate opens or a blocker appears.
- [ ] Never stop to ask him. A question goes to `QUESTIONS-FOR-OPERATOR.md` with the default taken and how to undo it, and the build goes on. Only his money, his sign-ins and his clicks are his.

### Spawn owners

- [ ] Spawn one fresh Opus builder per PR in the background with `subagent_type: poteto-agent` and `model: opus`, from a dispatch file saved in `dispatch/`. Its first words are exactly "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents."
- [ ] Run at most two builders. The second slot takes the next PR in plan order whose Depends on PRs are all stacked and whose Files share no path with the running builder's Files (Appendix C lists every shared path). Record the empty intersection in `ledger.tsv` before the second dispatch.
- [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, his real home `~/.qmx`, `C:/Users/Mubarak/Documents`, `C:/Users/Mubarak/Desktop/DATA_NARL`, or any vault value. Lanes run on throwaway folders and a scratch profile only.
- [ ] Skip a PR whose gate is closed and dispatch the next unblocked one. Log the skip in `RESUME.md`.

The dispatch order, generated from the sections below by `plan-parts/assemble.mjs`, which also refuses a PR that depends on a later one.

@spawn-table

### PR mechanics, for every PR

- [ ] The coordinator creates `build/us-<id>` from the current stack tip in `D:/QMX-worktrees/bld-us-<id>` before the dispatch. Never `git stash`.
- [ ] The builder opens the PR ready, never draft, within about 15 minutes, with `gh pr create --base <parent-branch> --head build/us-<id> --repo MubarakHimself/QMX`. The first PR's base is `build/unit-system`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Set `TMP` and `TEMP` to `D:/Temp` and `UV_CACHE_DIR` to `D:/Caches/uv` before `just ci` on This PC. Work only on `D:`. His `C:` drive is 98% full, and the shipped backup rule keeps a tenth of a drive free, so 106 red `qmx-home` backup tests on a full `C:` are the disk, never the PR (fix-check FC1, item 3).
- [ ] The builder runs `fmt-check`, `lint` and `types` in each package it touched, `tools/secret_scan.py` and `tools/money_path_scan.py`, reads each exit code, runs only the fast tests it added or changed, and never waits on a long command. It runs the `blast-radius` skill on its diff before the last push when the PR touches a shipped seam.
- [ ] Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. PR bodies end with the Claude Code line.

### Verdict and merge, for every PR (append to the stack, never merge)

- [ ] At the code-ready head the coordinator runs lanes 1 to 4 and at most one menu lane in the background and saves their logs in `evidence/<id>/`. Lane 1 is `just ci` under `D:/QMX-worktrees/.ci-lock`.
- [ ] A fresh Opus reviewer agent (one per PR, `model: opus`, told not to spawn sub-agents) reads the PR section, the full diff and those logs, applies the `bmad-review` lenses the section names (edge-case on every money-adjacent PR, verification-gap on every checker PR), reruns the one blast-radius fact the section names, and writes `review/<id>-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] Blockers go to one fix round by a fresh Opus builder on the same branch and worktree, given the dispatch file, the review file and the failing logs. The coordinator reruns the failed lanes and the touched suites at the fix head. Low findings go to `lows.md`.
- [ ] `ledger.tsv` gets head, parent, patch-id and the verdict.
- [ ] To append, the coordinator fetches the stack tip. If another PR was appended since the dispatch, it rebases the branch onto that tip, pushes with `--force-with-lease` after an `ls-remote` check, and sets the PR base to the tip's branch. A verdict stands when the patch-id is unchanged (`playbooks/shipping.md`).
- [ ] `just ci` runs at the stack tip after every fifth appended PR and at the end of each phase. A red at the tip is traced to its PR by rerunning the failing test at each head since the last green tip, and that PR gets the fix round.
- [ ] He lands the stack himself from the list the coordinator sends. Nobody else merges, closes a PR or deletes a branch.

### Boot recipe, for every live lane

- [ ] `git worktree add --detach D:/Temp/<id>-check <head>`, then `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] A lane runs on a throwaway QMX folder under `D:/QMX-worktrees/unit-ship/homes/<id>-<lane>/`. A lane that checks for stray files points `USERPROFILE`, `APPDATA`, `LOCALAPPDATA` and `HOME` at a scratch profile under the same folder.
- [ ] A lane with a model uses the plan login of the ship home `D:/QMX-worktrees/qma-ship/home` on `haiku`, as the earlier programs did, holding `D:/QMX-worktrees/.engine-lane-lock`. No Anthropic or OpenAI API spend.
- [ ] A lane that needs real bars uses the months saved once in `D:/QMX-worktrees/unit-ship/data/` by the shipped Dukascopy download template. If that download fails, the lane uses the synthetic months labelled "not evidence" and says so in its log.
- [ ] Each lane script exits non-zero on any failed check. The coordinator greps every PASS and FAIL line, never only the exit code.
- [ ] Never name a PowerShell variable `$home`. Save captures as `evidence/<id>/check-<slug>.log`, then remove the check copy with `git worktree remove` and confirm no `qmx_host`, `claude` or `node` process from the lane is left.
