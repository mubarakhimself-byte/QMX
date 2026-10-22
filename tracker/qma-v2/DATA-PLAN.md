# QMX data round build program

This program switches on the data round designed in `research/methodology/55-data-round-architecture.md`, as amended by its sections "Edge-case review applied (57)" and "Fix-check applied (58)", with rulings 1 to 135 in `26`.
The operator gets one Library that is the only Library, his server as its main copy, the old 10 GB of ticks saved and readable, one door to price history with the holdout lock in it, backtests by fingerprint, connections, downloaders, feeds, uploads, version control for agents, two monitoring layers and a Lab backend.
The rule it enforces is that every premise probe passes before its work starts, every acceptance probe passes before its PR is stacked and before the real step it protects, and a failed probe triggers its named fallback.
There are 30 PRs in 9 phases, in the order of the table under "Spawn owners". Four finish the deletion leftovers, four are probes and the old-ticks backup, and 22 are the work items W2 to W22 of 55 (W13 is split in two).
The stack roots on `engine/base` only after the deletion PRs 164 to 169 are merged there by his review agent (gate G-DEL). The program reads the merged head at arming and records it.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a short preamble. It names the work item of 55 "Fix-check applied (58)" (W-n), the review findings it builds (F-n of 57, N-n of 58), the AD ids (engine unless marked Lib or Lab), the premise probes that must pass before it starts, the acceptance probes that must pass before it is stacked, its real step, its gate, the scenarios of `54-data-round-funnel.md` it serves (S-nn), and the done line. Then come the nine blocks `check-plan.mjs` requires.

Probe names, pass lines and fail lines are those of the final probe table in 55's section "Fix-check applied (58)". This plan does not restate them. A box that says "P-X passes" means the PASS line of that table holds in the probe's log, and the FAIL line does not.

Path shorthands, used in every Files block.

- `QA/` is `qmx-agents/packages/`. `E/` is `QA/qmx-engine/src/qmx_engine/`, `T/` is `E/templates/` and `ET/` is `QA/qmx-engine/tests/`.
- `H/` is `QA/qma-harness/src/qma/harness/` and `HT/` is `QA/qma-harness/tests/`. `HO/` is `QA/qmx-host/src/qmx_host/` and `HOT/` its tests.
- `QX/` is `QA/qmx-control/src/qmx_control/` and `QXT/` its tests. `LB/` is `QA/qmx-library/src/qmx_library/` and `LBT/` its tests. `HB/` is `QA/qmx-hub/src/qmx_hub/` and `HBT/` its tests.
- `R/` is `QA/qmx-router/src/qmx_router/`, `BR/` is `QA/qmx-broker/src/qmx_broker/`, `TL/` is `QA/qmx-tools/src/qmx_tools/`, `MM/` is `QA/qmx-memory/src/qmx_memory/`, `RM/` is `QA/qmx-remote/src/qmx_remote/` and `AP/` is `QA/qmx-apps/src/qmx_apps/`. Each has a `tests/` folder beside `src/`.
- `FD/` is `packages/qmf-data/src/qmf/data/` and `FDT/` is `packages/qmf-data/tests/`. `QB/` is `qmb/src/qmb/` and `QBT/` is `qmb/tests/`.
- `SP/` is `scripts/probes/`, `SL/` is `scripts/live/` and `SD/` is `scripts/data/` (new in DR0).
- The store is `D:/QMX-worktrees/qma-ship/data/`. The ship home with the plan login is `D:/QMX-worktrees/qma-ship/home`. The server is `qmx-server`, reached with `ssh -i ~/.ssh/qmx_server root@155.133.27.86`.

The program runs `C:/Users/Mubarak/.dsh/skills/poteto-mode/playbooks/autopilot-stack.md` (the same file as `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md`). Its selection rule picks it, because the work is sequenced and the operator lands the stack himself. Nothing merges in this program. The coordinator appends each verified PR to one linear stack.

The plan makes ten overrides of that playbook and of poteto-mode. Each is named again where it applies.

- Override 1 replaces the owner of autopilot-stack step 1. One builder per PR runs on the operator's PC in its own worktree, on provider `deepseek-official`, model `deepseek-flash` (DeepSeek-V4.1-Flash), reasoning effort `max` (or `high` for a scripts-only PR), spawned in the background. It is never `deepseek-v4-pro`. `/deslop` is not installed, so the builder rereads its full diff instead. No Bugbot runs on this repo.
- Override 2 replaces the verdict of step 4 with the operator's light rule. One build and one check per PR. The coordinator runs the check itself and spawns no checker agent. Only blockers and anything touching his logins, keys or stores block. Low findings go to `lows.md` and never block. One fix round per PR.
- Override 3 is the lane count. `check-plan.mjs` demands ten lanes per PR. Here the ten lanes are a menu, not a quota. Lanes 1 to 4 are the proving set the coordinator runs, plus at most one menu lane it judges likeliest to break the PR's point. A lane box outside the run set is checked with a `ledger.tsv` row that says `menu, not run`.
- Override 4 is the perf block. No speed gate runs unless speed is the PR's point. Every perf block records a number and fails nothing, except where its Rule box names a fail line.
- Override 5 is the split of work. Builders write, push and run only the fast unit tests and gates of the packages they touched. The coordinator runs every long check in the background, the lanes, the full suites, `just ci`, server runs and probes.
- Override 6 is the handoff rule. Nobody messages a running builder. The only message to a running builder is a stop order when the program pauses. A check starts only after the builder reports and its worktree is quiet. One handoff at a time.
- Override 7 is the gated-PR rule. A PR whose gate is closed is skipped, never waited on. When the gate opens, the PR is built on the stack tip of that moment and appended there.
- Override 8 replaces poteto-mode's "fresh subagents by default" for fix rounds. The same builder is resumed for its one fix round, if it reported less than an hour ago. Otherwise a fresh builder gets the old report, the branch and the finding.
- Override 9 is pipelining. While the coordinator checks PR N, the builder of a later PR may start on N's code-ready head only when the two Files blocks share no file (Appendix C). The coordinator records the empty intersection in `decisions.tsv` before the dispatch.
- Override 10 is the real step. A PR's acceptance probes run on scratch roots, scratch cgroups, stubs or demo accounts. The act on his real home or the real server that the probe protects (the "real step") runs only on code he has landed on `engine/base` (gate G-LAND), and the Library flip also waits for his click (gate G-FLIP).

DeepSeek checking DeepSeek is a review inside one model family. Every verdict says so in its first lines.

Defaults are marked. Every value this plan sets that the operator did not choose says "Claude's default" where it appears, and Appendix D lists them all.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Check gate G-DEL. Run `git -C D:/QMX-worktrees/agent-system fetch origin` and `gh pr list --repo MubarakHimself/QMX --state all --limit 20 --json number,state,mergedAt,headRefName,baseRefName`. G-DEL is open when PRs 164, 165, 166, 167, 168 and 169 are merged into `engine/base`, and any deletion PR the deletion session opened after 169 (its `dispatch/del4b.md` plans DEL4B) is merged or closed. Log `git rev-parse origin/engine/base` as the root in `decisions.tsv`. If G-DEL is closed, start only the DR0 copy run below, write `RESUME.md`, and check G-DEL again at each tick.
- [ ] Settle the W0 rows of Appendix B at the root. Run each row's command and log the result.
  - [ ] `git grep -n "openai-codex" origin/engine/base -- '*pyproject.toml'`. No hit makes DEL4R OBSOLETE. A hit makes it REMAINING.
  - [ ] `git ls-tree -r --name-only origin/engine/base | grep -E "qma/serve.py|qma/harness/(profiles|relay|money_words).py"` and `git grep -n "record_work" origin/engine/base -- QA/qmx-control/src`. Each hit keeps DEL2R, MWH or RUN1C REMAINING. A row with no hit becomes OBSOLETE and is skipped.
- [ ] Read the plan from its branch with `git -C D:/QMX-worktrees/agent-system show plan/agent-system:tracker/qma-v2/DATA-PLAN.md`. If the file is not committed there, stop and ask the operator to have it committed, because every tick re-reads it from the branch.
- [ ] Read these at program start and at every tick. Log each read in `decisions.tsv`.
  - [ ] `git show origin/main:CLAUDE.md` for the project rules on trunk, then `C:/Users/Mubarak/Desktop/QMX/CLAUDE.md`, whose QMA v2 section is newer.
  - [ ] This plan, from `plan/agent-system` as above, to the end of "Program checklist", plus Appendices B to E.
  - [ ] `research/methodology/26-operator-rulings-and-alignment.md`. Its latest ruling wins over every other file. Rulings 120 to 135 are this round's.
  - [ ] `research/methodology/55-data-round-architecture.md` section "Fix-check applied (58)" only. Builders read the rest where their section points.
  - [ ] `C:/Users/Mubarak/.dsh/skills/poteto-mode/playbooks/autopilot-stack.md`, `shipping.md` and `opening-a-pr.md`.
- [ ] Confirm the shell before any command. The PC runs Windows 11 with PowerShell 7 and Git Bash. The server runs Ubuntu 24.04 with bash. Log which one each brief uses.
- [ ] Measure the disks and log them. On 2026-10-22 the PC had 9.1 GB free on `C:` and 4.7 GB free on `D:`, with 130 folders in `D:/QMX-worktrees` and 55 check folders in `D:/Temp`. The server had 171 GB free and 11.9 GB of RAM. Below 3 GB free on `D:`, run one builder at a time and post gate G-DISK to `QUESTIONS-FOR-OPERATOR.md`.
- [ ] Read the store `D:/QMX-worktrees/qma-ship/data/`. It holds `RESUME.md`, `BACKLOG.md`, `IDEAS.md`, `lows.md`, `QUESTIONS-FOR-OPERATOR.md`, `decisions.tsv`, `ledger.tsv`, `BRIEF-BUILDER.md`, `review/`, `evidence/` and `dispatch/`. The standing orders are the first rows of `decisions.tsv`.
- [ ] Start the DR0 copy run now, even when G-DEL is closed, because the old ticks have one copy on a nearly full disk. The coordinator runs it as an operation, not as product code.
  - [ ] Install `rclone` on `D:` from rclone.org's published Windows zip into `D:/Tools/rclone/`, and record the version in `decisions.tsv`.
  - [ ] On the server, create the ordinary user `qmx` (`useradd --system --create-home --home-dir /srv/qmx/home qmx`) if it is missing, and the folder `/srv/qmx/data/raw-backup/` owned by it.
  - [ ] Run `rclone copy --checksum` of `C:/Users/Mubarak/Documents/QMX/data/raw/external-deep-history` and of the risk-lab CSV folder `C:/Users/Mubarak/Desktop/QMX/workroom/risk-lab-2026-10-05/data` (252 MB, flagged "2025 ask file incomplete") to `/srv/qmx/data/raw-backup/` over SFTP as the `qmx` user, in the background. Then run `rclone check` on both. Log file counts, bytes and the check result in `evidence/dr0/copy.log`.
- [ ] State the protocol and this plan to the operator in plain words, then start. He said never stop to ask, so his go is the paste of the prompt.
- [ ] In the same message, list what only he can do. These are the gates of Appendix E. Log each in `QUESTIONS-FOR-OPERATOR.md` with the recommended answer.
  - [ ] G-R2. Open a Cloudflare R2 bucket (recommended, before the flip in DR2D). About 10 minutes.
  - [ ] G-CT. Sign in once on cTrader's own consent page for a demo account with the read-only `accounts` scope, so the probes of PRB-CT run. About 5 minutes.
  - [ ] G-FLIP. Click the flip to `primary = server` after DR2D's probes pass. About 2 minutes.
  - [ ] G-LAND. Land the stack on `engine/base` as PRs come in, so real steps can run.
  - [ ] G-DISK. Approve removing merged worktrees and check folders on `D:`.
  - [ ] G-CAL. Approve removing the old calendar scheduled task on his PC (DR6).
  - [ ] G-OO. Sign up for OpenObserve's free tier if its install asks for an account (DR10).
- [ ] On the go, arm the hourly audit tick. In Claude Code that is `/loop 1h` with the tick prompt below. In the DeepSeek harness it is a DSH schedule with the same prompt, as in the run of 2026-10-20. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk. Audit the operation against it and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then post a short status message to the operator in chat only when the audit found a tracked change that no earlier status message reported, such as a PR opened, a code-ready head, a round launched or closed, a verdict, a stuck agent and the action taken, a gate opened, a blocker added or cleared, or a decision only the operator can make. Name every such change and nothing else. Do not repeat a table, the stacked list, or an unchanged blocker. If the audit found none, end the turn with no reply text. Either way, log this tick's row in your decision trail. The row names the items reported, or none."
- [ ] On the operator's hold or stand-down, send every builder a zero-writes order at once.
- [ ] Keep `RESUME.md` current after every verdict, so a cold start needs only it, this plan and the store. Before the coordinator's context crosses 40 %, run poteto-mode's `playbooks/pause-safely.md`, write `RESUME.md`, and ask the operator to open a fresh coordinator session with the same prompt.

### Spawn owners

The table is the build order. "After" names the PRs whose code a PR needs, and the probe PRs whose result it reads. Gates are named in Appendix E. Phases are 0 deletion leftovers, 1 probes and the old-ticks backup, 2 the Library on the PC, 3 the server is home, 4 price data and backtests, 5 connections and downloads, 6 ways in, version control and workflows, 7 monitoring and real numbers, 8 kinds, the Lab and placement.

| # | Id | Ph | W | PR | Gate | After | Proving check |
|---|---|---|---|---|---|---|---|
| 1 | DEL4R | 0 | W0.2 rest | Drop `openai-codex` if the deletion session did not | G-DEL, REMAINING | none | lock and import scan |
| 2 | DEL2R | 0 | W0.3 | Delete `qma/serve.py` and the two RTR0 shims | G-DEL | DEL4R if built | harness and host suites |
| 3 | RUN1C | 0 | W0.4 | The maintenance loop off runs and jobs, backup as a cron workflow | G-DEL | DEL2R | control suite, two live lanes repointed |
| 4 | MWH | 0 | W0.5 | Delete the harness's money-word list (H62) | G-DEL | DEL2R | harness, engine, control suites |
| 5 | DR0 | 1 | W1 | Save the old ticks, script and record | G-DEL for the PR only | none | `rclone check` clean |
| 6 | PRB-DP | 1 | probes | Premise probes on the PC, P-MDREAD-DUCK and P-DUKA | G-DEL | none | rows in `SP/data/FINDINGS.md` |
| 7 | PRB-DS | 1 | probes | Premise probes on the server, P-HS, P-DOCLING, P-OO | G-DEL | none | rows in `SP/data/FINDINGS.md` |
| 8 | PRB-CT | 1 | probes | Premise probes on cTrader demo, P-CTSCOPE, P-CTREFRESH same app, P-CT2CONN | G-DEL, G-CT | none | rows in `SP/data/FINDINGS.md` |
| 9 | DR1A | 2 | W2 | Store durability | G-DEL | none | P-TORN |
| 10 | DR1B | 2 | W3 | The Library switch-on on the PC | G-DEL | DR1A, RUN1C | P-REHEARSE |
| 11 | DR2A | 3 | W4 | Host guards, full disk, memory, live capacity | none | DR1B | P-DISKFULL, P-OOM |
| 12 | DR2B | 3 | W5 | Sync and outbox, server host serves the Library | none | DR2A | P-SYNC-DISK, P-REPLAY, P-SPLIT, P-VERSION, P-LAT |
| 13 | DR2C | 3 | W6 | Vault and keys | none | DR2A | P-VAULT-AWAY, P-NOTRADE allow-list |
| 14 | DR2D | 3 | W7 | Flip tooling and the server-loss procedure | none | DR2B, DR2C | P-SERVERLOST |
| 15 | DR2E | 3 | W8 | Hindsight on the server | P-HS | DR2D, PRB-DS | recall parity |
| 16 | DR3A | 4 | W9 | Price partitions and series rules | P-MDREAD-DUCK | DR2D, PRB-DP | P-MDREAD, P-KEY, P-FREEZE, P-MARKS |
| 17 | DR3B | 4 | W10 | The market-data door | none | DR3A | P-FINALLOOK, sealed read refused |
| 18 | DR3C | 4 | W11 | Import the old ticks | none | DR0, DR3B | counts match DR0 |
| 19 | DR4 | 4 | W12 | Backtests through the door | none | DR3B | P-QMBREAD |
| 20 | DR5A | 5 | W13 part 1 | Connections registry, scopes, health, data keys | none | DR2C, DR2D | P-NOTRADE add time, P-VAULT-AWAY connections |
| 21 | DR5B | 5 | W13 part 2 | cTrader and MT5 homes, code exchange, broker history | G-CT | DR5A, PRB-CT | P-NOTRADE tokens |
| 22 | DR6 | 5 | W14 | Feeds and downloaders | P-DUKA | DR3B, DR5A, PRB-DP | P-BAN, P-FREEZE (b) |
| 23 | DR7 | 6 | W15 | Ways in, upload door and extraction | P-DOCLING | DR2B, PRB-DS | P-UPL, P-DISKFULL uploads, P-OOM with Docling |
| 24 | DR8 | 6 | W16 | Version control reaches agents | none | DR1B | merge tests, P-MERGE |
| 25 | DR9 | 6 | W17 | Workflows read the Library | none | DR1B | its journeys |
| 26 | DR10 | 7 | W18 | Monitoring | P-OO | DR2D, PRB-DS | P-REDACT, H61 check |
| 27 | DR11 | 7 | W19 | Real-numbers sweep | none | DR2A, DR7 | grep finds none |
| 28 | DR12 | 8 | W20 | Kinds and lineage | none | DR1B, DR3A | its journeys |
| 29 | DR13 | 8 | W21 | The Lab workspace and ML on the PC | P-GPU in its first box | DR3B, DR9, DR12 | its journeys |
| 30 | DR14 | 8 | W22 | Placement by data locality | none | DR3B, DR10 | its journeys |

Changes to the order of 55 "Work items, in build order", each with its reason.

- W0.1 is DONE-BY-DELETION-SESSION and W0.2's core, wire and daemon half too (Appendix B). They get no PR. W0.2's last line (`openai-codex`) becomes DEL4R, built only if the session's planned DEL4B did not land.
- The premise probes that need no new code run as their own scripts-only PRs early (PRB-DP, PRB-DS, PRB-CT), so their fallbacks are known before the work they gate. P-GPU needs DR3A's partitions and DR13's template, so it runs as DR13's first Build box. P-TAINT, P-SRCH and P-LAT exist and run as lanes.
- W13 is split. DR5A builds the registry, scopes, the health workflow and the data-provider connections, which need no sign-in. DR5B builds the cTrader and MT5 homes and the broker-history downloader, which need P-CTSCOPE, P-CTREFRESH and P-CT2CONN and so his demo sign-in (G-CT). DR6's keyless downloaders then need DR5A only.
- RUN1C sits before DR1B because both edit `QX/service.py` and `QX/backup.py`. DR1A shares no file with RUN1C, so the two may run at once.
- The UI is a separate session (`UI-HANDOFF.md` section 17). No PR here builds a screen.

- [ ] Spawn one builder per PR in the background with the harness's subagent tool, provider `deepseek-official`, model `deepseek-flash`, reasoning effort `max` (Override 1). The prompt is the builder template in `PROMPT-DATA.md`, filled from this plan and saved as `dispatch/<id>.md` before it is sent. It starts "Read the poteto-mode skill's SKILL.md in full, including its Principles section, before any work. Do not spawn sub-agents." Briefs point at files and never paste them.
- [ ] Follow the "After" column. Stacked work branches from the parent PR's branch at its verified head.
  - [ ] At most two builders at once, never two whose Files blocks share a file (Override 9, Appendix C). Record the empty intersection before each dispatch.
  - [ ] Early pairs that fit the rule are DEL2R with DR1A, PRB-DP with PRB-DS, and DR2B with DR2C.
  - [ ] A gated PR is skipped (Override 7). A PR whose "After" names a skipped PR takes the last verified PR before it as its parent, unless its preamble says it needs the skipped one.
- [ ] Hold the file boundaries.
  - [ ] Each PR touches only the files its Files block names, plus the store's `evidence/` and `review/` folders.
  - [ ] No PR touches `apps/qmx-ui/`, `~/.claude`, `~/.dsh`, or the ship home's `settings.toml`. QMB, QMF and QMN files change only where a Files block names them (DR3A, DR4, DR6).
- [ ] Hold the review gates. DR1B and DR4 change what his copilot reads and answers. Each posts a screenshot and a short video to him in chat, and is appended on its clean verdict without waiting. Changes he asks for go to `BACKLOG.md`.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Run `command -v origin`. If it is missing, use `gh` and record that in `decisions.tsv`. Never require `gt`.
- [ ] The coordinator creates branch `build/<id>` (lowercase) from the parent branch at its verified head, in the worktree `D:/QMX-worktrees/bld-<id>`, before the dispatch. Never use `git stash`, which is shared across worktrees. The builder opens the PR ready, never draft, within about 15 minutes, per **Opening a PR**, with `gh pr create --base <parent-branch> --head build/<id> --repo MubarakHimself/QMX`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Set `TMP` and `TEMP` to `D:/Temp` and `UV_CACHE_DIR` to `D:/Caches/uv`.
- [ ] The builder runs `uv run --no-sync python -m poethepoet fmt-check`, `lint` and `types` once in each package it touched, and `uv run --no-sync python tools/secret_scan.py`, before the PR-facing push, and reads each exit code. Push with hooks on.
- [ ] The builder rereads the full diff before each commit in place of `/deslop` (Override 1).
- [ ] Add only the tests that prove the PR's point, at the module's public interface, with literal expected values. Typically a handful, rarely more than about 20. No test per private function, no snapshot or getter tests.
- [ ] Probe scripts live under `SP/data/` with one row each in `SP/data/FINDINGS.md`. A probe that needs the server runs as the `qmx` user under `/srv/qmx/check/<id>/` and removes that folder after.
- [ ] No full `just ci` per PR. The coordinator runs it under the CI lock `mkdir D:/QMX-worktrees/.ci-lock` four times in the program, in the checks of MWH, DR2D, DR3B and DR14.
- [ ] Commit messages end with `Co-Authored-By: DeepSeek-V4.1-Flash <noreply@deepseek.com>`. PR bodies end with `🤖 Generated with DeepSeek Harness`.

### Verdict and merge, for every PR (append to the stack, never merge)

- [ ] At the code-ready head SHA, the coordinator runs one check (Override 2) in the background. It reads the PR body and the diff (the full diff for files under 400 changed lines, else the files the section's Build block names), runs the PR's unit tests with `-n 2`, the gates above, lanes 1 to 4 and at most one menu lane (Override 3), and reads every exit code and the tails of the logs. It writes `review/<id>-check-<head8>.md`, whose first line is CLEAN or NOT CLEAN and whose second line is "DeepSeek reviewed DeepSeek. A cross-family review was not run."
- [ ] Blockers, a failed acceptance probe, and findings on logins, keys or stores go back to the builder for one fix round (Override 8). Low findings go to `lows.md` with the PR id and never block.
- [ ] After the fix round, the coordinator reads the fix diff, reruns the failing lane at the new head, and records the verdict in `ledger.tsv` with head SHA, parent SHA and `git patch-id --stable`. A fix counts only when the fix commit is in the checked head. No second round runs. A PR still NOT CLEAN is not stacked, its dependents are skipped, its real step does not run, and `QUESTIONS-FOR-OPERATOR.md` says why.
- [ ] Append the PR to the stack on a clean verdict, per autopilot-stack steps 5 and 6. Nobody merges, arms auto-merge, closes a PR, pushes `main`, or deletes a branch or worktree without his go. `main` moves only by his squash-merge click.
- [ ] After each verdict, remove the check worktree with `git worktree remove`, and log free space on `D:`.

### Boot recipe, for every live lane

- [ ] `git -C D:/QMX-worktrees/agent-system fetch origin build/<id>`, then `git -C D:/QMX-worktrees/agent-system worktree add --detach D:/Temp/<id>-check <head>`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Set `TMP`, `TEMP` and `UV_CACHE_DIR` on `D:`. Run `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] A lane that needs no model runs on a throwaway home under the store's `homes/<id>-<lane>`. A lane that needs a model opens the host on the ship home only while it holds the lane lock `mkdir D:/QMX-worktrees/.engine-lane-lock`.
- [ ] Model turns run on `claude/haiku` through the ship home's plan login. A provider-proof lane uses the OpenRouter row on a throwaway home, credential ref `qmx/openrouter`, and never reads the value. A lane that only needs a model to answer uses the engine's fake provider.
- [ ] A server lane runs the PR head on the server from a detached checkout under `/srv/qmx/check/<id>` as the `qmx` user, with its own throwaway home there, and removes both after. Nothing on the server runs as root except package installs and `useradd`.
- [ ] No lane holds a key that can trade. Broker lanes use demo accounts or stubs (ruling 135).
- [ ] Save a text capture as `<slug>.log` in the store's `evidence/<id>/`, prefixed `owner-` or `check-`, and never overwrite another PR's files.
- [ ] Remove the lane lock, confirm with `Get-Process` that no `claude`, `qmx_host` or `node` process from the lane is left, and remove `D:/Temp/<id>-check` with `git worktree remove`.

## Drop `openai-codex` if the deletion session did not (DEL4R)

Work item W0.2, its last line only (55 section 8 item 3). ADs AD-59. Premise none. Acceptance the nine-name scan and `uv lock --check`. Real step none. Gate G-DEL, and the Arm box must have marked it REMAINING. At PR 169's head `feb7121b` the only name left is `openai-codex==0.160.0` at `qmx-agents/pyproject.toml:50`. The deletion session's planned DEL4B removes it. If DEL4B landed, this PR is OBSOLETE and skipped. Scenarios none directly (step 0 of 55 section 10). Done when no `pyproject.toml` names any of `langchain`, `langchain-core`, `langgraph`, `deepagents`, `langchain-anthropic`, `langchain-openai`, `langchain[mcp]`, `langgraph-checkpoint-sqlite` or `openai-codex`, and both locks check.

**Depends on.** Gate G-DEL. It branches from the stack root.

**Files.**

- [ ] Edit `qmx-agents/pyproject.toml` (the `openai-codex` line in the dev group).
- [ ] Regenerate `qmx-agents/uv.lock` and, only if it changes, the root `uv.lock`.

**Build.**

- [ ] Run `git grep -n -E "openai_codex|openai-codex"` outside locks and `archive/`. Save it as `evidence/del4r/owner-scan.log`. A live import outside `examples/apps/**` stops the PR as BLOCKED with file and line.
- [ ] Remove the line and run `uv lock` in `qmx-agents/`. Record which packages left the lock in the PR body.

**You see.**

- [ ] `git grep` of the nine names in every `pyproject.toml` prints nothing, and `uv lock --check` passes at the root and in `qmx-agents/`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] No new test. Run `tools/tests` with `-n 2` at head. Save `del4r-tools-tests.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness`, `qmx-host` and `qmx-engine` suites with `-n 2` at the parent and at head. Save `del4r-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Nine-name scan. Run the scan over every `pyproject.toml` and both locks. Save `del4r-scan.log`. Pass when no manifest and no lock names any of the nine.
- [ ] Lane 3. Fresh environment. Run `uv sync --frozen --all-packages --all-groups` in a new `D:/Temp/del4r-venv`, then `python -c "import openai_codex"`. Save `del4r-fresh.log`. Pass when the sync succeeds and the import fails with `ModuleNotFoundError`.
- [ ] Lane 4. Lock check. Run `uv lock --check` at the root and in `qmx-agents/`. Save `del4r-lock.log`. Pass when both exit 0.
- [ ] Lane 5. Run `tools/secret_scan.py`. Save `del4r-secrets.log`. Pass when it is clean.
- [ ] Lane 6. Run `uv run --no-sync python -m poethepoet types` at the root. Save `del4r-types.log`. Pass when it exits 0.
- [ ] Lane 7. Start `python -m qmx_host --help` from the fresh environment. Save `del4r-host-help.log`. Pass when it prints its usage.
- [ ] Lane 8. Diff the package list of lane 3 against the parent's. Save `del4r-packages.log`. Pass when the only removals are `openai-codex` and packages only it required.
- [ ] Lane 9. List free space on `D:` before and after lane 3. Save `del4r-disk.log`. Pass when the lane's venv is removed and the space is back.
- [ ] Lane 10. List processes after the lanes. Save `del4r-processes.log`. Pass when no lane process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Fresh `uv sync` time in seconds.
- [ ] Probe. Lane 3's sync, once.
- [ ] Baseline. The parent head, same probe.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. DEL4R changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DEL4R as the root of the stack.

## Delete `qma/serve.py` and the two RTR0 shims (DEL2R)

Work item W0.3 (55 section 8 item 4). ADs AD-52, AD-59. Premise none. Acceptance the harness and host suites, and a scan that finds no `qma.serve`, `qma.harness.profiles` or `qma.harness.relay` importer. Real step none. Gate G-DEL. REMAINING at PR 169's head, where `qma/serve.py`, `H/profiles.py` and `H/relay.py` exist, `qma/console.py:797-798` launches `qma.serve`, and `HO/host.py:50` imports `ProfileName` from the shim. Scenarios none directly (step 0). Done when the three files are gone, `console.py` starts `qmx_host` when no host answers, and every importer reads `qmx_router` directly.

**Depends on.** Gate G-DEL. It branches from DEL4R's verified head, or from the stack root when DEL4R is OBSOLETE.

**Files.**

- [ ] Delete `QA/qma-harness/src/qma/serve.py`, `H/profiles.py` and `H/relay.py`.
- [ ] Edit `QA/qma-harness/src/qma/console.py` (the module docstring, `serve()` at lines 797 to 799, and its caller), `H/chat.py`, `H/home.py`, `H/routes.py` and `H/launch.py` (the message at line 560 that names `qma.serve`).
- [ ] Edit `HO/host.py` (line 50).
- [ ] Edit `HT/test_attached.py`, `test_change.py`, `test_chat.py`, `test_chat_options.py`, `test_home.py`, `test_launch.py` and `test_import_rules.py` (line 168), `HOT/test_context.py` and `test_sessions.py`, and `QA/qmx-router/tests/test_boundary.py` (lines 59 to 69).
- [ ] Edit `QA/qma-harness/pyproject.toml` (the comment at line 31).
- [ ] Edit `SL/qma/s21c_egress.py`, `SL/host/ses_lanes.py` (line 210), `SL/engine/x13_doors.py` (lane 5 and the perf block that start `qma.serve`), and the docstrings of `SL/engine/common.py`, `lane_host.py` and `llm_lanes.py`.

**Build.**

- [ ] Run `git grep -n -E "qma\.serve|qma\.harness\.(profiles|relay)"` outside `archive/` and Markdown. Classify each hit as the deletion session's common block does (deletion set, Files block, inert text, live caller). Save `evidence/del2r/owner-scan.log`. A live caller outside the Files block stops the PR as BLOCKED.
- [ ] Point every import at `qmx_router.profiles` and `qmx_router.relay`. Delete the two nine-line shims.
- [ ] Make `console.py` start `python -m qmx_host` with the same `--home` and `--port` when no host answers. Delete `qma/serve.py`.
- [ ] Make `s21c_egress.py` read `qmx_router/relay.py`, and make `x13_doors.py` lane 5 and its perf block start `qmx_host`.
- [ ] Drop the two identity asserts of `test_boundary.py`, which test the shims.

**You see.**

- [ ] `python -m qma.console` with no host on its port starts `qmx_host`, and `python -m qma.serve` fails with `No module named qma.serve`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] One new test in `HT/` asserts that the console's start command runs `-m qmx_host`. Run the `qma-harness`, `qmx-host` and `qmx-router` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness`, `qmx-host` and `qmx-router` suites with `-n 2` at the parent and at head. Save `del2r-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Importer scan. Rerun the Build scan at head. Save `del2r-scan.log`. Pass when no live importer of the three modules is left.
- [ ] Lane 3. Console start. On a throwaway home with no host running, run `python -m qma.console` with that home and a free port for one fake-model turn. Save `del2r-console.log`. Pass when a `qmx_host` process answers `/api/health` and the turn returns.
- [ ] Lane 4. Run `SL/qma/s21c_egress.py` with `QMA_EVIDENCE_DIR` set to the evidence folder. Save `del2r-s21c.log`. Pass when it prints its pass line for the negative and the positive case.
- [ ] Lane 5. Run `SL/engine/x13_doors.py` lane 5. Save `del2r-x13.log`. Pass when `qmx_host` serves the workflow doors.
- [ ] Lane 6. Run `python -m qma.serve`. Save `del2r-serve.log`. Pass when it fails with `No module named qma.serve`.
- [ ] Lane 7. Run `SL/host/ses_lanes.py` on a throwaway home. Save `del2r-ses.log`. Pass when its lanes pass.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `del2r-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in `qma-harness`, `qmx-host` and `qmx-router`. Save `del2r-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. List processes after the lanes. Save `del2r-processes.log`. Pass when no `qmx_host` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Seconds from `qma.console` start to a healthy `/api/health`.
- [ ] Probe. Lane 3's start, three times.
- [ ] Baseline. The parent head, where the console starts `qma.serve`.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. DEL2R changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DEL2R on DEL4R, or as the root when DEL4R is OBSOLETE.

## Take the maintenance loop off runs and jobs, and run the weekly backup as a cron workflow (RUN1C)

Work item W0.4 (55 section 8 item 5, and D-11's "one backup plan"). ADs AD-57, AD-59, Lib AD-16. Premise none. Acceptance the control and engine suites, the two live lanes repointed, and one cron fire of `backup-weekly` on a throwaway home. Real step none. Gate G-DEL. REMAINING at PR 169's head, where `QX/server.py:106,111` calls `runs_list` and `record_work`, and `QX/service.py:801` records the weekly backup as a `jobs` row. Scenarios S-02 and S-25 (the backup plan). Done when no product code calls `runs_list`, `runs_get`, `runs_cancel`, `jobs_list`, `jobs_cancel` or `record_work`, those operations and the `runs` and `jobs` work kinds are gone, the weekly backup is the `backup-weekly` template on a cron trigger, and a maintenance failure raises an incident.

**Depends on.** DEL2R. It branches from DEL2R's verified head.

**Files.**

- [ ] Edit `QX/server.py` (the maintenance loop at lines 100 to 120), `QX/service.py` (`record_work`, `runs_list`, `runs_get`, `runs_cancel`, `jobs_list`, `jobs_cancel`, the `weekly-backup` record at line 801 and the record at line 1230), and `QX/runs.py` (its docstring and any helper only those use).
- [ ] Edit the work-kind rows in `QX/catalog.py` that list `runs` and `jobs`.
- [ ] Add the template folder `T/backup-weekly/` (definition, script and README) and its row in `T/catalog.py`.
- [ ] Edit the tests in `QXT/` and `ET/` that call the deleted operations, moving each one that tests a behaviour still wanted onto engine runs.
- [ ] Edit `SL/engine/e57_app_trigger.py` (line 266) and `SL/engine/x13_doors.py` (line 417).

**Build.**

- [ ] Write `backup-weekly` as a script-only workflow with a cron trigger and home `pc` (SOLUTION-DESIGN section 30.1). Its script calls the backup function the maintenance loop calls today. The cadence is the loop's current one (Claude's default), editable in Settings.
- [ ] Make a maintenance failure raise an incident with the masked signature `maintenance:<step>` through the host's incident writer, instead of a `jobs` row.
- [ ] Delete the six operations and the two work kinds. Repoint the two live lanes at `workflow_runs_list`, or retire a lane whose only subject was the deleted list, and say which in the PR body.

**You see.**

- [ ] On a throwaway home, the run list shows one `backup-weekly` run after a forced cron fire, and `GET /api/jobs` answers 404.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] One test asserts the template validates and has a cron trigger. One test forces a failing backup step and asserts one incident with signature `maintenance:backup`. Run the `qmx-control` and `qmx-engine` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-control` and `qmx-engine` suites with `-n 2` at the parent and at head. Save `run1c-regression.log`. Pass when head fails nothing the parent passes, except tests this PR deleted with their operations.
- [ ] Lane 2. Cron fire. Start `qmx_host` on a throwaway home, install `backup-weekly`, and fire its trigger through the engine's catch-up path. Save `run1c-backup.log`. Pass when one run ends `passed` and the backup folder holds a new snapshot.
- [ ] Lane 3. Failure path. Repeat lane 2 with the backup target unwritable. Save `run1c-incident.log`. Pass when one incident `maintenance:backup` is open and no `jobs` row exists.
- [ ] Lane 4. Run the repointed `SL/engine/e57_app_trigger.py` and `x13_doors.py`. Save `run1c-lanes.log`. Pass when both print their pass lines.
- [ ] Lane 5. Scan for the deleted names in product code and scripts. Save `run1c-scan.log`. Pass when none is left outside `archive/`.
- [ ] Lane 6. Call `GET /api/jobs` and `GET /api/workflow-runs` on the lane 2 host. Save `run1c-rest.log`. Pass when the first answers 404 and the second lists the backup run.
- [ ] Lane 7. Restart the host with the trigger due. Save `run1c-catchup.log`. Pass when exactly one catch-up run starts.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `run1c-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in `qmx-control` and `qmx-engine`. Save `run1c-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. List processes after the lanes. Save `run1c-processes.log`. Pass when no `qmx_host` and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Seconds for one `backup-weekly` run on a throwaway home.
- [ ] Probe. Lane 2, once.
- [ ] Baseline. The parent's maintenance-loop backup on the same home.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. RUN1C changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends RUN1C on DEL2R.

## Delete the harness's money-word list (MWH)

Work item W0.5 (55 section 8 item 6, HARNESS-REQUESTS H62). ADs AD-54, AD-59. Premise none. Acceptance the harness, engine and control suites, and `just ci` (the first of four runs). Real step none. Gate G-DEL. REMAINING at PR 169's head, where `H/money_words.py` exists, `H/__init__.py:38` exports `named_money_act`, `H/tools.py:958` vets MCP-server tools with it, `E/definition/lint.py:165` lints definitions with it, and `QXT/test_catalog.py` (lines 12 and 92 to 97) tests it. Money-word matching is retired (rulings 116 and 118, engine OPEN-DECISIONS W3). The guard of AD-54 stays as ordinary hygiene for sign-ins, keys, QMX's own databases and destructive commands. Scenarios none directly (step 0). Done when the module, its export and its three users are gone and every suite passes without it.

**Depends on.** DEL2R. It branches from RUN1C's verified head when RUN1C is stacked, else from DEL2R's (MWH and RUN1C share no file).

**Files.**

- [ ] Delete `H/money_words.py` and any harness test that only tests it.
- [ ] Edit `H/__init__.py` (line 38 and the `__all__` entry at line 127), `H/tools.py` (the MCP-server vetting at lines 945 to 960 and its docstring), and `E/definition/lint.py` (lines 18 and 160 to 170).
- [ ] Edit `QXT/test_catalog.py` (lines 12 and 91 to 97) and the engine lint tests in `ET/` that assert the money-word problem.

**Build.**

- [ ] Run `git grep -n -E "named_money_act|money_words"` outside `archive/` and Markdown. Save `evidence/mwh/owner-scan.log`.
- [ ] Remove the MCP-server vetting step that refuses a tool by its name. Keep every other vetting step of `H/tools.py` as built.
- [ ] Remove the lint rule and its problem code. Keep every other lint rule.
- [ ] Delete `test_no_row_names_an_order_act`, which only tests the word list.

**You see.**

- [ ] An external MCP server whose tool is named `place_order` is vetted like any other tool, and a workflow definition with a node named `submit_order` lints with no money-word problem.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] One harness test vets a fake MCP config with a tool named `place_order` and asserts it is accepted. One engine test lints a definition with a node named `submit_order` and asserts no problem names a money act. Run the `qma-harness`, `qmx-engine` and `qmx-control` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the three suites with `-n 2` at the parent and at head. Save `mwh-regression.log`. Pass when head fails nothing the parent passes, except the deleted word-list tests.
- [ ] Lane 2. `just ci` under the CI lock at head. Save `mwh-ci.log`. Pass when every gate exits 0 and every suite failure also fails at the parent.
- [ ] Lane 3. Scan at head. Save `mwh-scan.log`. Pass when no `named_money_act` or `money_words` name is left outside `archive/`.
- [ ] Lane 4. On a throwaway home, start `qmx_host` and add an MCP server config with a tool named `place_order` through the harness's add path. Save `mwh-vet.log`. Pass when the add succeeds and the guard of AD-54 still refuses a write into `~/.qmx/library.db` from the same chat.
- [ ] Lane 5. Lint `T/` with the engine's lint command. Save `mwh-lint.log`. Pass when no template gains or loses a problem other than money-word problems.
- [ ] Lane 6. Ask the copilot on haiku to list its broker tools. Save `mwh-broker-tools.log`. Pass when no listed tool submits, changes or cancels an order.
- [ ] Lane 7. Run `tools/secret_scan.py`. Save `mwh-secrets.log`. Pass when it is clean.
- [ ] Lane 8. Run `fmt-check`, `lint` and `types` in the three packages. Save `mwh-gates.log`. Pass when every exit code is 0.
- [ ] Lane 9. Hash the ship home's `settings.toml` before and after lane 6. Save `mwh-hash.log`. Pass when the hashes match.
- [ ] Lane 10. List processes after the lanes. Save `mwh-processes.log`. Pass when no `claude`, `qmx_host` or lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Milliseconds to lint all templates.
- [ ] Probe. Lane 5, three times.
- [ ] Baseline. The parent head, same probe.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. MWH changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends MWH on its parent.

## Save the old ticks to the server with checksums, and keep the record (DR0)

Work item W1 (55 section 10 step 1, D-11). ADs Lib AD-10, Lib AD-16, Lib AD-25. Premise none. Acceptance `rclone check` clean, counts and hashes recorded. Real step the copy itself, which the coordinator starts at arming before G-DEL (Program checklist), because the 10 GB at `C:/Users/Mubarak/Documents/QMX/data/raw/external-deep-history` and the 252 MB of risk-lab CSVs have one copy on a disk with 9.1 GB free. Gate G-DEL for the PR only. The bucket leg waits for G-R2. Scenarios S-03, S-25. Done when the server holds both folders under `/srv/qmx/data/raw-backup/` owned by `qmx`, `rclone check` is clean, a manifest of every file's sha256 and size sits next to them, and the script reruns as a no-op.

**Depends on.** Gate G-DEL for the PR. The copy run depends on nothing.

**Files.**

- [ ] Add `SD/save_old_ticks.py`, `SD/README.md` and `SD/test_save_old_ticks.py`.

**Build.**

- [ ] Write `save_old_ticks.py`. It takes a source folder, a target (`sftp` remote to the server as `qmx`, or a bucket remote), and a record path. It runs `rclone copy --checksum`, then `rclone check`, then writes `MANIFEST.sha256` (one line per file with sha256 and bytes) next to the copy and a JSON record with file count, total bytes and the manifest's own sha256. It never deletes a source file. It takes no credential value, only rclone remote names.
- [ ] Make a second run with nothing new copy zero files and write the same record (idempotent).
- [ ] Without G-R2, the bucket leg prints "no bucket remote configured" and exits 0. With G-R2 open, the coordinator reruns it with the bucket remote.

**You see.**

- [ ] `ssh` to the server, `ls /srv/qmx/data/raw-backup/` shows both folders and `MANIFEST.sha256`, owned by `qmx`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Two tests on a scratch folder copied to a second scratch folder through a local rclone remote. The first asserts the record's count and bytes equal the source's. The second asserts a rerun copies zero files. Run with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane. Run `SD/test_save_old_ticks.py` at head. Save `dr0-unit.log`. Pass when both tests pass (no parent code changes).
- [ ] Lane 2. `rclone check` of both folders against the server copy. Save `dr0-check.log`. Pass when it reports 0 differences and 0 missing files.
- [ ] Lane 3. Manifest. Count the lines of `MANIFEST.sha256` on the server and compare with the PC's file count and total bytes. Save `dr0-manifest.log`. Pass when count and bytes are equal on both sides.
- [ ] Lane 4. Rerun the script against the server. Save `dr0-rerun.log`. Pass when it transfers 0 files and writes the same record.
- [ ] Lane 5. Ownership. Run `stat` on the server folders. Save `dr0-owner.log`. Pass when the owner is `qmx` and no file is owned by root.
- [ ] Lane 6. Spot hash. Hash ten random files on both sides with `sha256sum` and `Get-FileHash`. Save `dr0-spot.log`. Pass when all ten match.
- [ ] Lane 7. Bucket leg without G-R2. Run with the bucket target. Save `dr0-bucket.log`. Pass when it prints "no bucket remote configured" and exits 0, or, with G-R2 open, when `rclone check` against the bucket is clean.
- [ ] Lane 8. PC disk. Log free space on `C:` and `D:` before and after. Save `dr0-disk.log`. Pass when neither dropped by more than the rclone log size.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `dr0-secrets.log`. Pass when it is clean and the repo holds no rclone config.
- [ ] Lane 10. List processes after the lanes. Save `dr0-processes.log`. Pass when no `rclone` process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). MB per second of the copy to the server.
- [ ] Probe. The arming copy run's rclone summary.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded as the figure DR3C's import plan reads.

**Review gate.** None. DR0 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR0 on the tip of phase 0.

## Run the premise probes that need only the PC, P-MDREAD-DUCK and P-DUKA (PRB-DP)

Premise probes 14 and 25 of the final probe table in 55's section "Fix-check applied (58)". ADs Lib AD-25, engine AD-68. Premise these are the premises. Acceptance a row per probe in `SP/data/FINDINGS.md` with its PASS or FAIL line and numbers. Real step none. Gate G-DEL. Scenarios S-03, S-05. Done when both rows exist. A failed row triggers its fallback here, recorded in `decisions.tsv` and told to the operator in plain words.

- P-MDREAD-DUCK fallback. The schema changes before DR3A. The FINDINGS row names each column DuckDB 1.5.5 read differently and the type it did read identically. DR3A uses those types.
- P-DUKA fallback. If QMX's own bi5 fetch (`FD/dukascopy.py`) agrees with the old raw files and dukascopy-node does not, DR6's Dukascopy downloader uses QMX's own fetch. If neither agrees, DR6 ships without a Dukascopy downloader and the difference goes to `QUESTIONS-FOR-OPERATOR.md`.

**Depends on.** Gate G-DEL. It branches from the stack root and shares no file with any PR.

**Files.**

- [ ] Add `SP/data/__init__.py`, `SP/data/common.py`, `SP/data/p_mdread_duck.py`, `SP/data/p_duka.py` and `SP/data/FINDINGS.md`.

**Build.**

- [ ] Write `p_mdread_duck.py`. It writes a scratch Parquet file in the planned typed schema (int64 `t`, int64 scaled bid and ask, the kind's other columns) with pyarrow 25.0.1 in row groups, reads it back row for row with DuckDB 1.5.5, and compares.
- [ ] Install dukascopy-node 1.50.0 with `npm install dukascopy-node@1.50.0 --prefix D:/Tools/dukascopy-node`. Record the command in `evidence/prb-dp/owner-installs.md`.
- [ ] Write `p_duka.py`. For one month of EURUSD ticks that the old raw bi5 files cover, it fetches with dukascopy-node (`--retries` and `--retry-on-empty` on, one price side per run), fetches with `FD/dukascopy.py`, decodes the old raw bi5 files, and compares row count, first and last tick, prices and gaps. It writes only under `D:/Temp/prb-dp/` and deletes that folder at the end.
- [ ] Run both and write the two FINDINGS rows.

**You see.**

- [ ] `SP/data/FINDINGS.md` has a P-MDREAD-DUCK row and a P-DUKA row, each with PASS or FAIL and its numbers.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] No product code changes. One test feeds `p_duka.py`'s compare function two equal tick lists and one with a shifted price, and asserts PASS then FAIL.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane. Run the probe's own test. Save `prb-dp-unit.log`. Pass when it passes (no product code changes).
- [ ] Lane 2. Rerun `p_mdread_duck.py`. Save `prb-dp-duck.log`. Pass when its result equals the FINDINGS row.
- [ ] Lane 3. Rerun `p_duka.py`. Save `prb-dp-duka.log`. Pass when its result equals the FINDINGS row.
- [ ] Lane 4. Read both FINDINGS rows against 55's PASS and FAIL lines. Save `prb-dp-rows.log`. Pass when each row states which line held, and a FAIL row names its fallback and has a `decisions.tsv` row.
- [ ] Lane 5. Rerun `p_duka.py` for a second month. Save `prb-dp-duka2.log`. Pass when it agrees with the first month's verdict.
- [ ] Lane 6. Confirm the old raw files are untouched. Hash the month's bi5 files before and after. Save `prb-dp-raw.log`. Pass when the hashes match.
- [ ] Lane 7. Check that `D:/Temp/prb-dp/` is gone. Save `prb-dp-clean.log`. Pass when it is.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `prb-dp-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check` and `lint` over `SP/data/`. Save `prb-dp-gates.log`. Pass when both exit 0.
- [ ] Lane 10. List processes after the lanes. Save `prb-dp-processes.log`. Pass when no `node` process from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds to fetch one month of EURUSD ticks with each fetcher.
- [ ] Probe. Lane 3, once.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for DR6's batch pauses.

**Review gate.** None. PRB-DP changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends PRB-DP on the stack tip.

## Run the premise probes on the server, P-HS, P-DOCLING and P-OO (PRB-DS)

Premise and measure probes 13, 27 and 30 of the final probe table in 55's section "Fix-check applied (58)". ADs engine AD-18, AD-30, AD-69, Lib AD-27. Premise these are the premises. Acceptance a row per probe in `SP/data/FINDINGS-server.md`. Real step none. Gate G-DEL. Scenarios S-06, S-12, S-26. Done when the three rows exist, each with its numbers recorded as the Settings default it feeds. Each runs as the `qmx` user under `/srv/qmx/check/prb-ds/`.

- P-HS fallback. Hindsight stays on the PC and server workflows recall through FTS5 over the same rows, as PRB-S measured. DR2E is skipped as OBSOLETE and the reading goes to `QUESTIONS-FOR-OPERATOR.md`.
- P-DOCLING fallback. The `extract-source` template's default home becomes `pc` for the file class that was killed (local by default, ruling 117), and DR7 ships with that default.
- P-OO fallback. DR10 ships the internal layer and the exporters, with the collector keeping its disk queue and OpenObserve not installed. The reading goes to `QUESTIONS-FOR-OPERATOR.md`.

**Depends on.** Gate G-DEL. It branches from the stack root and shares no file with PRB-DP. Its scripts are standalone and import nothing from `SP/data/`.

**Files.**

- [ ] Add `SP/data/p_hs.py`, `SP/data/p_docling.py`, `SP/data/p_oo.py`, `SP/data/server_common.py` and `SP/data/FINDINGS-server.md`.

**Build.**

- [ ] On the server, install system PostgreSQL with pgvector from Ubuntu's packages, Hindsight 1.1.0 (`hindsight-api`) and Docling 2.134.0 into uv environments under `/srv/qmx/check/prb-ds/`, and OpenObserve 1.0.4 from its GitHub release. Record every command verbatim in `evidence/prb-ds/owner-installs.md`. Services run as `qmx`, never root.
- [ ] Write `p_hs.py`. It runs Hindsight against the system Postgres at the default worker slots, records resident memory at idle and in a retain burst, and checks recall parity with the PC on the fixed query set of `SP/library/questions.json`.
- [ ] Write `p_docling.py`. It extracts a 400-page public PDF and one hour of public audio in a child process each, and records time and peak memory.
- [ ] Write `p_oo.py`. It runs OpenObserve for a measured window under a synthetic day of QMX telemetry replayed from a run's spans and logs, and records memory and disk per day.
- [ ] Write the three FINDINGS rows. Stop every service the probes started, except the PostgreSQL package, which DR2E reuses. Remove `/srv/qmx/check/prb-ds/`.

**You see.**

- [ ] `SP/data/FINDINGS-server.md` has P-HS, P-DOCLING and P-OO rows with memory and time numbers.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] No product code changes. One test checks `server_common.py`'s parser of `/proc/<pid>/status` peak memory on a fixed sample text.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane. Run the parser test. Save `prb-ds-unit.log`. Pass when it passes (no product code changes).
- [ ] Lane 2. Rerun `p_hs.py`. Save `prb-ds-hs.log`. Pass when its numbers are within 20 % of the FINDINGS row and its verdict matches.
- [ ] Lane 3. Rerun `p_docling.py` on the PDF only. Save `prb-ds-docling.log`. Pass when its verdict matches the row.
- [ ] Lane 4. Read the three rows against 55's PASS and FAIL lines. Save `prb-ds-rows.log`. Pass when each row states which line held, and a FAIL row names its fallback and has a `decisions.tsv` row.
- [ ] Lane 5. List the server's processes and users. Save `prb-ds-server.log`. Pass when no probe service is left running and none ran as root.
- [ ] Lane 6. Check the server's free disk before and after. Save `prb-ds-disk.log`. Pass when `/srv/qmx/check/prb-ds/` is gone.
- [ ] Lane 7. Rerun `p_oo.py` for a shorter window. Save `prb-ds-oo.log`. Pass when memory agrees with the row within 20 %.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `prb-ds-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check` and `lint` over `SP/data/`. Save `prb-ds-gates.log`. Pass when both exit 0.
- [ ] Lane 10. Check the installs file names every command. Save `prb-ds-installs.log`. Pass when each installed package appears with its version.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Peak MB of Hindsight, Docling and OpenObserve on the server.
- [ ] Probe. Lanes 2, 3 and 7.
- [ ] Baseline. PRB-S's Hindsight reading, 2,687 MB resident.
- [ ] Rule. No fail rule. Recorded as admission readings (engine AD-30).

**Review gate.** None. PRB-DS changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends PRB-DS on the stack tip.

## Run the cTrader premise probes on a demo account (PRB-CT)

Premise probes 22, 23 and 24 of the same table, P-CTSCOPE, P-CTREFRESH (same app) and P-CT2CONN. ADs engine AD-28, AD-67, ruling 135. Premise these are the premises of DR5B. Acceptance a row per probe in `SP/data/FINDINGS-ctrader.md`. Real step none. Gate G-DEL and G-CT (his one sign-in on cTrader's consent page for a demo account with the `accounts` scope, through the loopback port registered on his read app). The MT5 half of P-CTSCOPE needs his MT5 investor login, and the exchange half needs a read-only exchange key. Without them those halves record `not run`. Scenarios S-28 (data side). Done when the three rows exist and their fallbacks, if any, are recorded.

- P-CTSCOPE fallback. A credential type that can trade is never labelled `read`, and DR5A and DR5B label it `trade`. A half that did not run is labelled `trade` too, because only a probe can prove `read`.
- P-CTREFRESH fallback. DR5B is skipped and parked, the cTrader reads keep today's short sessions, and the finding goes to `QUESTIONS-FOR-OPERATOR.md`.
- P-CT2CONN fallback. When the first connection dies with no event, DR5B's health walk gains a liveness read every check, and P-CT2CONN's case becomes one of DR5B's lanes.

**Depends on.** Gates G-DEL and G-CT. It branches from the stack tip of the moment G-CT opens.

**Files.**

- [ ] Add `SP/data/p_ctscope.py`, `SP/data/p_ctrefresh.py`, `SP/data/p_ct2conn.py` and `SP/data/FINDINGS-ctrader.md`.

**Build.**

- [ ] Write `p_ctscope.py`. With the `accounts`-scope demo token, it signs in through `qmf-venue`, lists the accounts, and sends one minimum-size market order on the demo account. It expects a refusal. With an MT5 investor login present, it reads `trade_allowed`. With a read-only exchange key present, it reads the key's permission flags through CCXT. The token and keys are read from the keyring by reference and never printed.
- [ ] Write `p_ctrefresh.py`. Under the read app, it refreshes the grant, reopens the session with the new pair, and confirms the old pair is dead. It records whether a second grant for the same cTrader ID under the same app revokes the first.
- [ ] Write `p_ct2conn.py`. It holds the read app's demo connection on the PC and opens a second demo connection under the same app from the server. It records whether the second is refused with error 67 or drops the first with an event.
- [ ] Write the three FINDINGS rows and the facts DR5B's adapter declaration reads.

**You see.**

- [ ] `SP/data/FINDINGS-ctrader.md` has the three rows. The demo account shows no new position.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] No product code changes. One test feeds the scope check a fake refusal and a fake fill, and asserts PASS then FAIL.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane. Run the probe test. Save `prb-ct-unit.log`. Pass when it passes (no product code changes).
- [ ] Lane 2. Rerun `p_ctscope.py`. Save `prb-ct-scope.log`. Pass when the order is refused and the demo account shows no new position.
- [ ] Lane 3. Rerun `p_ctrefresh.py`. Save `prb-ct-refresh.log`. Pass when its verdict matches the row.
- [ ] Lane 4. Rerun `p_ct2conn.py`. Save `prb-ct-2conn.log`. Pass when its verdict matches the row.
- [ ] Lane 5. Grep every probe log for the token, the client secret and any key value. Save `prb-ct-leak.log`. Pass when none appears.
- [ ] Lane 6. List the keyring entries the probes wrote. Save `prb-ct-keyring.log`. Pass when they are only the demo grant's and no live-account token exists.
- [ ] Lane 7. Read the rows against 55's PASS and FAIL lines. Save `prb-ct-rows.log`. Pass when each row states which line held, and a FAIL row names its fallback.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `prb-ct-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check` and `lint` over `SP/data/`. Save `prb-ct-gates.log`. Pass when both exit 0.
- [ ] Lane 10. List processes on the PC and the server after the lanes. Save `prb-ct-processes.log`. Pass when no probe session is left open.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for one refresh and reopen.
- [ ] Probe. Lane 3, once.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for DR5B's health cadence.

**Review gate.** None. PRB-CT changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends PRB-CT on the stack tip of the moment it is verified.

## Make the Library store survive torn logs and Windows renames (DR1A)

Work item W2. Fixes F13 and F20 (57). ADs Lib AD-16. Premise none. Acceptance P-TORN. Real step DR1B's switch-over on his real home waits for it. Gate G-DEL. Scenarios S-01, S-25. Done when a torn last line of the ref, edge and annotation logs is quarantined with an alarm and the store opens, a bad middle line opens the store read-only with an incident, every rename is preceded by an fsync, and a rename under a held Windows handle retries and lands.

**Depends on.** Gate G-DEL. It branches from the verified stack tip at dispatch. It shares no file with DEL2R, RUN1C or MWH, so it may run beside one of them.

**Files.**

- [ ] Edit `LB/store.py` (`_lines`, `_write_once` and every rename) and `LB/status.py` (the torn and read-only states).
- [ ] Add `LBT/test_durability.py` and `SP/data/p_torn.py`.

**Build.**

- [ ] Make the log reader quarantine a torn or NUL-filled last line into `quarantine/` and raise `library:torn:<log>`, then open normally.
- [ ] Make a bad line in the middle of a log open the store read-only with an incident naming the log and the line number.
- [ ] Fsync each file before its rename and the folder after it. Retry a rename that fails with WinError 5 or 32, with backoff, until it lands or the store reports the holder.
- [ ] Write `p_torn.py` to run P-TORN's cases on a scratch store.

**You see.**

- [ ] On a scratch store with a cut last line, `status()` reads `torn`, `quarantine/` holds the line, and every other record reads back.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Four tests. A torn tail opens with one quarantined line. A NUL-filled tail does the same. A bad middle line opens read-only and refuses `put`. A rename under a held handle (opened by the test) lands after the handle closes. Run the `qmx-library` suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-library`, `qmx-hub` and `qmx-host` suites with `-n 2` at the parent and at head. Save `dr1a-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-TORN on a scratch store. Save `dr1a-p-torn.log`. Pass when P-TORN passes.
- [ ] Lane 3. Kill a `qmx_host` on a throwaway home in the middle of a burst of 1,000 saves, then restart it. Save `dr1a-kill.log`. Pass when the host starts, every save it acknowledged reads back, and at most one line is quarantined.
- [ ] Lane 4. Hold a handle on a blob file from a second process while the store renames into it. Save `dr1a-rename.log`. Pass when the rename lands after the handle closes and the log shows the retries.
- [ ] Lane 5. Bad middle line on a throwaway home started by `qmx_host`. Save `dr1a-readonly.log`. Pass when the doctor shows the read-only incident and a save is refused with its reason.
- [ ] Lane 6. Run `SL/library/` lanes for the store. Save `dr1a-library-lanes.log`. Pass when they pass.
- [ ] Lane 7. Measure save latency with and without fsync. Save `dr1a-fsync.log`. Pass when the number is recorded.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr1a-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in `qmx-library`. Save `dr1a-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. List processes after the lanes. Save `dr1a-processes.log`. Pass when no `qmx_host` and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Median milliseconds per `put` of a small note.
- [ ] Probe. Lane 7, 1,000 saves.
- [ ] Baseline. The parent head, same probe.
- [ ] Rule. No fail rule. Recorded, because the fsync is a correctness fix.

**Review gate.** None. DR1A changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR1A on the stack tip.

## Switch the PC on to the one Library (DR1B)

Work item W3. Fixes F19 and N18. ADs Lib AD-1, Lib AD-9, Lib AD-26, engine AD-55, AD-64, HARNESS-REQUESTS H59 (the Library half). Premise none. Acceptance P-REHEARSE. Real step the switch-over on his real home `~/.qmx` (gate G-LAND), after P-TORN and P-REHEARSE passed. Gate G-DEL. Scenarios S-01, S-11, S-25. Done when every `library_*` row, the copilot's search, the harness's `domain.library` and mini-app outputs read and write the new store, `library.db` and `artifacts.db` are imported and retired read-only to `migration/retired/`, the backup list names the new store, and QMB's registry projection reads through the port.

**Depends on.** DR1A and RUN1C. It branches from the later of the two verified heads.

**Files.**

- [ ] Edit `QX/service.py` (the `library_*` rows at lines 643 to 659, `attach_library_mirror` at 633, `app_runtime()` at 1243 to 1270), `QX/library.py` (the class body goes, per MIGRATION step 6) and `QX/backup.py` (lines 18 to 21).
- [ ] Edit `HO/host.py` (lines 489 and 490, the dual write becomes the only write) and `H/harness.py` (line 404, `domain.library`).
- [ ] Edit `LB/migrate/from_library_b.py` (the junk filter by id list, `DualWrite` retired), `LB/migrate/from_apps.py` and `LB/migrate/verify.py`.
- [ ] Edit `QB/registryread/library.py` (reads go through the port).
- [ ] Add `SD/switch_library.py` and `SP/data/p_rehearse.py`.
- [ ] Edit the tests in `QXT/`, `HOT/`, `HT/` and `LBT/` that assert the old Library or the dual write.

**Build.**

- [ ] Write `switch_library.py`. It refuses to run while a host answers on the home. It runs MIGRATION step 0 (snapshot and counts), imports `library.db` with the known test junk filtered by id (BACKLOG line 141's ids, listed in the script) and `artifacts.db` into `<home>/library/`, verifies counts and hashes, flips the rows, and moves the old files to `migration/retired/`. It writes a report with every count and the filtered ids.
- [ ] Point the `library_*` rows, `domain.library` and the copilot's search at the new store. Attach `LibrarySink` in `app_runtime()`. Remove `library.db` from the weekly backup list and add `<home>/library/`.
- [ ] Make QMB's registry projection read through `LibraryPort`.
- [ ] Write `p_rehearse.py` to run the switch-over on a copy of a home in a scratch root and to hash the source home before and after.

**You see.**

- [ ] After the switch-over on a throwaway copy of his home, a copilot `library_search` answers from `<home>/library/` and `<home>/migration/retired/library.db` exists.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Three tests. A `library_save` lands one object in the new store and no row in `library.db`. An app output lands as one `artifact` through the sink. The switch-over on a fixture home gives counts equal to step 0 minus the filtered ids. Run the `qmx-control`, `qmx-host`, `qma-harness`, `qmx-library` and `qmb` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the five suites with `-n 2` at the parent and at head. Save `dr1b-regression.log`. Pass when head fails nothing the parent passes, except tests of the deleted dual write.
- [ ] Lane 2. P-REHEARSE on a copy of his real `~/.qmx` in `D:/Temp/dr1b-rehearse/`. Save `dr1b-p-rehearse.log`. Pass when P-REHEARSE passes.
- [ ] Lane 3. On the rehearsed copy, start `qmx_host` and ask the copilot on haiku to find an item that existed only in the old `library.db`. Save `dr1b-copilot.log`. Pass when it cites the item by its new id.
- [ ] Lane 4. On the rehearsed copy, run one mini app that lands an output. Save `dr1b-app.log`. Pass when the output is one `artifact` in the new store linked `produced-by` its instance, and `artifacts.db` is not written.
- [ ] Lane 5. Run the weekly backup on the rehearsed copy. Save `dr1b-backup.log`. Pass when the snapshot holds `library/` and not `library.db`.
- [ ] Lane 6. QMB registry read. Run QMB's registry-read example on a throwaway home. Save `dr1b-qmb.log`. Pass when it reads through the port and returns the same records as the parent.
- [ ] Lane 7. Run `switch_library.py` with a host running on the home. Save `dr1b-refuse.log`. Pass when it refuses and changes nothing.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr1b-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the five packages. Save `dr1b-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove `D:/Temp/dr1b-rehearse/` and list processes. Save `dr1b-processes.log`. Pass when the folder is gone and no `qmx_host` or lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for the whole switch-over of his home copy.
- [ ] Probe. Lane 2, once.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded so the real step can say how long saves pause.

**Review gate.** DR1B changes what his copilot searches. It is appended on its clean verdict without waiting.

- [ ] Post to the operator in chat one screenshot of lane 3's answer and a short video (`ffmpeg -f gdigrab`) of the copilot finding an old item in the rehearsed copy, with one plain sentence on what changes for him.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR1B on its parent.
- [ ] Real step (G-LAND). After he lands DR1B on `engine/base`, the coordinator stops nothing of his. If his host is running, it posts "close QMX for two minutes" to `QUESTIONS-FOR-OPERATOR.md` and moves on. When the home is quiet, it runs `switch_library.py` on `~/.qmx` and saves the report to `evidence/dr1b/real-switch.log`.

## Guard each machine against a full disk and against running out of memory (DR2A)

Work item W4. Fixes F22, F39 and D-11 (57, 55). ADs engine AD-30, AD-58, AD-65, Lib AD-10. Premise none. Acceptance P-DISKFULL and P-OOM (the W4 halves). Real step the flip (DR2D) waits for both. Gate none. Scenarios S-25, S-26. Done when each machine gives way in the order price cache, transient blobs, telemetry queue, fetched cache copies, a writer that cannot fit refuses whole with `disk_full`, Library writes are refused last against a measured floor he may raise, admission reserves a node's declared memory until its measured size replaces it, heavy work runs in child processes, the server host's out-of-memory score is lowered, and the invented constants at `E/settings.py:146-150` are gone in favour of live heartbeat readings.

**Depends on.** DR1B. It branches from DR1B's verified head.

**Files.**

- [ ] Add `HO/disk.py` (the per-machine giving-way rule and the measured floor) and `QA/qmx-host/deploy/qmx-host.service` (the systemd unit with `User=qmx` and a lowered `OOMScoreAdjust`).
- [ ] Edit `HO/host.py` (wire the disk rule and the free-space reading into the heartbeat), `E/admission.py` (reserve declared memory until measured), `E/settings.py` (the `placement.contabo.*` budget, overhead, session and attempt-memory rows), `E/heartbeat.py` (live free RAM, free disk, measured session size) and `E/workers/local.py` (heavy nodes run as child processes).
- [ ] Edit `LB/store.py` (refuse a write whole with `disk_full` below the floor, never a half-written file).
- [ ] Add `SP/data/p_diskfull.py` and `SP/data/p_oom.py`. Edit the tests in `ET/`, `HOT/` and `LBT/` that read the removed constants.

**Build.**

- [ ] Write the giving-way rule as one ordered table in `HO/disk.py`, each row a class of expendable data with its eviction call. The floor is measured at start from the machine's free space and is a Settings value he may raise (Claude's default is the measured value).
- [ ] Make admission read live free RAM and the measured session size from the heartbeat, reserve each admitted node's declared memory until a measured size replaces it, and delete the constants.
- [ ] Run extraction, downloads and big market-data reads as child processes, so the kernel kills a child, never `qmx_host`.
- [ ] Write the two probes. `p_oom.py` runs on the server in a scratch cgroup whose memory limit is below the combined need of three synthetic memory-heavy children and two agent nodes, until DR7 adds Docling and DR3B the door read.

**You see.**

- [ ] The doctor on a throwaway home shows free disk, the floor and free RAM from live readings, and no budget constant.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Three tests. The giving-way rule evicts classes in table order on a fake volume. A Library `put` below the floor raises `disk_full` and leaves no file. Admission refuses a node whose declared memory exceeds the live free RAM minus reservations. Run the `qmx-host`, `qmx-engine` and `qmx-library` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the three suites with `-n 2` at the parent and at head. Save `dr2a-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-DISKFULL (without the upload case) on a scratch volume on the server, a loop file mounted under `/srv/qmx/check/dr2a/`. Save `dr2a-p-diskfull.log`. Pass when P-DISKFULL passes for its W4 cases.
- [ ] Lane 3. P-OOM in a scratch cgroup on the server. Save `dr2a-p-oom.log`. Pass when P-OOM passes and the log shows the limit forced a kill.
- [ ] Lane 4. Start `qmx_host` on a throwaway home on the server under the new unit as `qmx`. Read `/proc/<pid>/oom_score_adj` and the heartbeat. Save `dr2a-unit.log`. Pass when the score is the lowered value and the heartbeat carries live RAM and disk readings.
- [ ] Lane 5. Grep the engine for `12_288`, `6_144`, `2_048` and `1_536` in settings. Save `dr2a-constants.log`. Pass when none is left as a capacity value.
- [ ] Lane 6. Run the engine's admission lanes in `SL/engine/` that read capacity. Save `dr2a-admission.log`. Pass when they pass on live readings.
- [ ] Lane 7. On a PC throwaway home, set the floor above the free space through the Settings value and save a note. Save `dr2a-pc-disk.log`. Pass when the save is refused whole with the plain message and no file is left.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr2a-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the three packages. Save `dr2a-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the loop file and cgroup, and list processes on both machines. Save `dr2a-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from a full volume to the first refused save, and admission latency per node.
- [ ] Probe. Lanes 2 and 6.
- [ ] Baseline. The parent's admission latency.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. DR2A changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR2A on DR1B.

## Serve the Library from the server's host and sync the PC selectively (DR2B)

Work item W5. Fixes F10, F11, F12, F15, F16, F18, N1, N3, N13, N17 and N19. ADs Lib AD-10, AD-14, AD-19, AD-26, engine AD-65. Premise none. Acceptance P-SYNC-DISK, P-REPLAY, P-SPLIT, P-VERSION and P-LAT. Real step the flip (DR2D) waits for all five, and the server host is installed as the `qmx` service (G-LAND). Gate none. Scenarios S-02, S-25, S-30. Done when the server's `qmx_host` opens the store and serves the Library routes from the same object, the PC syncs ref moves, manifests, edges and text slots since its last sequence and fetches other blobs only when opened, a blob's arrival re-indexes its objects, fetched blobs are evictable cache copies while born blobs need two remote copies, the outbox replays idempotently, `refs/primary` carries an epoch only his flip raises, stale-epoch moves park as conflicts, version refusals name the side behind, and pending writes show as "waiting for the server".

**Depends on.** DR2A. It branches from DR2A's verified head. It shares no file with DR2C, so the two may run at once.

**Files.**

- [ ] Edit `HO/host.py` (the server role opens the store and mounts the Library routes from `HB/server.py` in-process; the PC role runs the sync loop and the outbox), `HO/__main__.py` (the role flag).
- [ ] Edit `HB/server.py` (served from the host on the server; streams are untouched until DR7), `HB/replicate.py` (selective sync since a sequence, text slots, one sync at a time and coalesced, fast-forward-only pushes of owned refs, `mirror` refused for refs the server owns).
- [ ] Edit `LB/store.py` (`_placed_by` filtered to one ref, `_index_object` and `read_blob` re-index on arrival, cache copy and born blob classes, `refs/primary` with epoch, parked moves, version check by kind and schema version), `LB/client.py` and `LB/status.py` (pending writes).
- [ ] Add `LB/outbox.py`.
- [ ] Edit `QX/node.py` (server setup installs the unit of DR2A and the store root `/srv/qmx/library` owned by `qmx`).
- [ ] Add `SP/data/p_sync_disk.py`, `p_replay.py`, `p_split.py` and `p_version.py`. Edit tests in `LBT/`, `HBT/` and `HOT/` that assume full replication.

**Build.**

- [ ] Run the Library service inside the server's one `qmx_host` process, so the server store has one writer.
- [ ] Write the selective sync and the outbox as 55 D-2 and Lib AD-14 say. An outbox entry carries item id, expected head, intended object and version. A replay succeeds when the intended object was ever placed on that ref.
- [ ] Write the epoch record and the version check. A refusal names the side behind (`needs_update`), and fires only for a kind or schema version the reader lacks.
- [ ] Write the four probes on two scratch roots, one on the server and one on the PC, over the tailnet.

**You see.**

- [ ] On scratch roots with `primary = server`, a PC search finds a phrase that exists only in a server-extracted text, and opening the item fetches its original.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Five tests. A sync copies text slots and no other blob. A replayed outbox entry whose object is already on the ref succeeds. A store that learns a higher epoch parks its move as a `merge-conflict`. An entry of an unknown schema version is refused with `needs_update` naming the server. A fetched blob is evicted under pressure and a born blob with one remote copy is not. Run the `qmx-library`, `qmx-hub` and `qmx-host` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the three suites with `-n 2` at the parent and at head. Save `dr2b-regression.log`. Pass when head fails nothing the parent passes, except tests of full replication this PR replaced.
- [ ] Lane 2. P-SYNC-DISK with 5 GB of originals on the scratch server root. Save `dr2b-p-sync-disk.log`. Pass when P-SYNC-DISK passes.
- [ ] Lane 3. P-REPLAY, both cases. Save `dr2b-p-replay.log`. Pass when P-REPLAY passes.
- [ ] Lane 4. P-SPLIT and P-VERSION. Save `dr2b-p-split-version.log`. Pass when both pass.
- [ ] Lane 5. P-LAT with `SL/server/p_lat.py` and the PC as replica and cache. Save `dr2b-p-lat.log`. Pass when P-LAT passes and screen times are recorded.
- [ ] Lane 6. Unplug the tailnet on the PC for ten minutes while a chat saves three notes, then reconnect. Save `dr2b-offline.log`. Pass when the notes show "waiting for the server", then land once each.
- [ ] Lane 7. Run `SL/server/e67_claims.py` and `e53_two_hosts.py` against the new server role. Save `dr2b-server-lanes.log`. Pass when both pass.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr2b-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the three packages. Save `dr2b-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove `/srv/qmx/check/dr2b/` and the PC scratch root, and list processes on both machines. Save `dr2b-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for one PC sync after 1,000 server saves, and bytes copied.
- [ ] Probe. Lane 2's sync.
- [ ] Baseline. The parent's full replication on the same roots.
- [ ] Rule. Fail when the sync copies any non-text blob that was not opened (P-SYNC-DISK's FAIL line).

**Review gate.** None. DR2B changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR2B on DR2A.
- [ ] Real step (G-LAND). After he lands DR2B, the coordinator runs the server setup from `QX/node.py` on the real server, so the host runs as `qmx` under the unit, with the store at `/srv/qmx/library`. The PC stays primary until the flip.

## Give each machine its own vault key and replicate only static read and data keys (DR2C)

Work item W6. Fixes F29, F30 and N5. ADs engine AD-28, AD-67, Lib AD-12, ruling 135. Premise none. Acceptance P-VAULT-AWAY (model keys) and P-NOTRADE (allow-list). Real step the flip (DR2D) waits for both. Gate none. Scenarios S-02, S-18, S-28. Done when each receiving machine has its own vault key pair, the server's private key sits in a file only `qmx` reads, `is_replicable` is an allow-list of model-provider rows, `qmx/read/*` and `qmx/data/*`, the path where the server asks the PC is gone, OAuth tokens and trade keys are never vault entries, and a host route hands a secret once to its home.

**Depends on.** DR2A. It branches from DR2A's verified head. It shares no file with DR2B.

**Files.**

- [ ] Edit `R/vault.py` (allow-list, per-machine key pairs, no ask-the-PC path, no token or trade entries, no tombstone for non-vault entries).
- [ ] Edit `HO/door.py` (the route that receives a secret once for its home, `user` only).
- [ ] Edit `QA/qmx-router/tests/` vault tests and `SL/server/e26_vault.py`.
- [ ] Add `SP/data/p_vault_away.py` and `SP/data/p_notrade.py`.

**Build.**

- [ ] Rewrite `is_replicable` as an allow-list. Keep the existing seal format.
- [ ] Generate a key pair per receiving machine at setup. Write the server's private key to `/srv/qmx/home/.qmx/vault.key` with mode 0600, owner `qmx`. Raise `vault:unavailable:<machine>` when it is missing.
- [ ] Delete the code path where a node asks the PC for a key.
- [ ] Write P-VAULT-AWAY's model-key half and P-NOTRADE's allow-list half.

**You see.**

- [ ] With the PC's host stopped, a restarted scratch server host serves a model call through its relay with a key it opened itself.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Three tests. `is_replicable` is false for `qmx/ctrader-demo`, `qmx/ctrader-live`, `qmx/crypto`, `qmx/backup-payload-key` and a token entry, and true for `qmx/read/x`, `qmx/data/x` and a model-provider row. A missing key file raises `vault:unavailable:contabo`. A sealed entry opens only with its machine's key. Run the `qmx-router` and `qmx-host` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the two suites with `-n 2` at the parent and at head. Save `dr2c-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-VAULT-AWAY (model keys) with the PC host stopped. Save `dr2c-p-vault-away.log`. Pass when P-VAULT-AWAY passes for model keys.
- [ ] Lane 3. P-NOTRADE (allow-list). Save `dr2c-p-notrade.log`. Pass when P-NOTRADE's W6 line holds.
- [ ] Lane 4. Run `SL/server/e26_vault.py` and `e25_passes.py`. Save `dr2c-server-lanes.log`. Pass when both pass.
- [ ] Lane 5. Read the server key file's mode and owner. Save `dr2c-keyfile.log`. Pass when it is 0600 and `qmx`.
- [ ] Lane 6. Grep every lane log for key values. Save `dr2c-leak.log`. Pass when none appears.
- [ ] Lane 7. Delete a static read key on the PC and sync. Save `dr2c-delete.log`. Pass when the server's copy is resealed or removed per AD-28, and no token entry moves.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr2c-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in `qmx-router` and `qmx-host`. Save `dr2c-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch roots and list processes on both machines. Save `dr2c-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds to open one sealed key on the server.
- [ ] Probe. Lane 2, ten opens.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. DR2C changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR2C on DR2B, rebased once onto DR2B's verified head (patch-id checked).

## Build the flip and the procedure for losing the server (DR2D)

Work item W7. Fixes F14, F24 and N13. ADs Lib AD-14, AD-16, AD-19, AD-26, MIGRATION step 8 and "When the server is lost". Premise none. Acceptance P-SERVERLOST, both branches. Real step **the flip to `primary = server`**, after every acceptance probe of DR2A to DR2D passed and DR2D is landed (G-LAND), by his click (G-FLIP). The bucket (G-R2) is recommended before the flip. Gate none for the build. Scenarios S-02, S-25. Done when the flip quiesces writes, pushes until the PC and server ref logs agree, and raises the epoch only on his click, the server-loss procedure runs end to end with and without a bucket, and the server pushes Library objects, refs, edges and durable blobs to the bucket after each commit batch.

**Depends on.** DR2B and DR2C. It branches from DR2C's stacked head.

**Files.**

- [ ] Add `QX/primary.py` (the flip and the server-loss procedure as operations, `user` only) and its rows in `QX/catalog.py`.
- [ ] Edit `QX/node.py` (re-pair with a fresh pairing code; rebuild a server from the bucket).
- [ ] Add `HB/bucket.py` (push after each commit batch through rclone, a no-op that says so without a bucket remote).
- [ ] Add `SP/data/p_serverlost.py`. Add tests in `QXT/` and `HBT/`.

**Build.**

- [ ] Write the flip as MIGRATION step 8. It announces, quiesces, pushes until equal, and then waits for his click in the inbox before it raises the epoch.
- [ ] Write the server-loss procedure as MIGRATION "When the server is lost", steps 1 to 6, including asking him to stop a reachable old host and naming exactly what is lost without a bucket.
- [ ] Write the bucket push. With G-R2 closed it logs "no bucket, one copy on the server" and the storage view says so.
- [ ] Write `p_serverlost.py` to run both branches on two scratch roots and a scratch bucket folder.

**You see.**

- [ ] On scratch roots, the inbox shows "Move the Library to the server" with one button, and nothing flips until it is pressed.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Three tests. The flip without the click leaves the epoch unchanged. The flip with the click raises it by one. Without a bucket remote, the push records "no bucket" and does not fail. Run the `qmx-control` and `qmx-hub` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-control`, `qmx-hub`, `qmx-library` and `qmx-host` suites with `-n 2` at the parent and at head. Save `dr2d-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-SERVERLOST with a scratch bucket folder. Save `dr2d-p-serverlost-bucket.log`. Pass when P-SERVERLOST's bucket branch passes.
- [ ] Lane 3. P-SERVERLOST without a bucket. Save `dr2d-p-serverlost-nobucket.log`. Pass when the lost list is exactly the server-born blobs never opened on the PC, minus text slots.
- [ ] Lane 4. The flip on scratch roots, clicked through the inbox by the lane. Save `dr2d-flip.log`. Pass when saves pause, the ref logs agree, the epoch rises by one, and a chat save then lands on the server and mirrors back.
- [ ] Lane 5. `just ci` under the CI lock at head. Save `dr2d-ci.log`. Pass when every gate exits 0 and every suite failure also fails at the parent.
- [ ] Lane 6. Rerun P-SPLIT after the flip of lane 4. Save `dr2d-split.log`. Pass when P-SPLIT passes.
- [ ] Lane 7. The reverse flip on the same roots. Save `dr2d-reverse.log`. Pass when the epoch rises again and the PC is primary.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr2d-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the touched packages. Save `dr2d-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch roots and the scratch bucket folder, and list processes. Save `dr2d-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds that saves pause during the flip.
- [ ] Probe. Lane 4.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded so the inbox card can say how long saves pause.

**Review gate.** None. DR2D changes no screen. The flip itself waits for his click.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR2D on DR2C.
- [ ] Real step (G-LAND, G-FLIP). After he lands DR2A to DR2D and the five probes of DR2B, P-DISKFULL, P-OOM, P-VAULT-AWAY, P-NOTRADE and P-SERVERLOST all passed at their stacked heads, the coordinator runs the flip up to the click and posts the inbox card. If G-R2 is still closed, the card says in one plain sentence that files made on the server will have one copy. He clicks when he chooses.

## Run Hindsight on the server with a system Postgres (DR2E)

Work item W8. ADs engine AD-18, ruling 119. Premise P-HS (PRB-DS). Acceptance recall parity on the fixed query set. Real step Hindsight switched on on the server (G-LAND). Gate P-HS passed. If P-HS failed, DR2E is OBSOLETE (its fallback). Scenarios S-12 (memory health), S-30. Done when the server's memory engine is Hindsight on the system Postgres with pgvector, its banks are rebuilt from Library rows, its model calls go through the router, and recall on the fixed query set equals the PC's.

**Depends on.** DR2D and PRB-DS. It branches from DR2D's verified head.

**Files.**

- [ ] Edit `MM/hindsight.py` (connect to a system Postgres by a Settings value, model calls through the router) and `MM/engine.py` (the server role rebuilds banks from Library rows).
- [ ] Add `QA/qmx-memory/deploy/hindsight.service` (runs as `qmx`) and `QA/qmx-memory/deploy/README.md`.
- [ ] Edit `QX/node.py` (server setup installs Postgres with pgvector and the Hindsight unit).
- [ ] Add tests in `QA/qmx-memory/tests/`.

**Build.**

- [ ] Make the server role rebuild its banks from the Library's memory rows on first start, and keep the built-in search as the second engine.
- [ ] Record P-HS's admission reading as the Hindsight row's declared memory (engine AD-30).

**You see.**

- [ ] The doctor on the scratch server shows the memory engine as Hindsight with its Postgres reachable.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Two tests. The rebuild from three memory rows recalls each by its text. With Postgres unreachable, recall falls back to the built-in search and raises one incident. Run the `qmx-memory` and `qmx-control` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the two suites with `-n 2` at the parent and at head. Save `dr2e-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Recall parity. Run the fixed query set of `SP/library/questions.json` on the scratch server and on the PC. Save `dr2e-parity.log`. Pass when the answers match.
- [ ] Lane 3. Retain burst on the scratch server at the default worker slots. Save `dr2e-burst.log`. Pass when memory stays within P-HS's recorded reading and no process is killed.
- [ ] Lane 4. Stop Postgres during a recall. Save `dr2e-fallback.log`. Pass when recall answers from the built-in search and one incident is open.
- [ ] Lane 5. Run `SL/memory/` lanes on the server role. Save `dr2e-memory-lanes.log`. Pass when they pass.
- [ ] Lane 6. Read the Hindsight unit's user. Save `dr2e-user.log`. Pass when it is `qmx`.
- [ ] Lane 7. Check the server's free RAM after Hindsight starts. Save `dr2e-ram.log`. Pass when the host, Hindsight and one measured agent session fit the live reading.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr2e-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in `qmx-memory` and `qmx-control`. Save `dr2e-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch roots and list processes. Save `dr2e-processes.log`. Pass when nothing from the lanes is left except the Postgres package.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Median recall latency in ms on the server.
- [ ] Probe. Lane 2.
- [ ] Baseline. The PC's recall latency on the same set.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. DR2E changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR2E on the stack tip.
- [ ] Real step (G-LAND). After he lands DR2E, the coordinator runs the server setup's Hindsight step on the real server.

## Write price history as typed monthly partitions with one card per series (DR3A)

Work item W9. Fixes F1 to F5, N6, N7 and N21. ADs Lib AD-22, AD-25, AD-31 (fills as partitions). Premise P-MDREAD-DUCK (PRB-DP). Acceptance P-MDREAD (read-back), P-KEY, P-FREEZE and P-MARKS. Real step the old-ticks import (DR3C) waits for all four. Gate P-MDREAD-DUCK passed, or its fallback applied to the schema. Scenarios S-01, S-03, S-05, S-19, S-21, S-23, S-24, S-29. Done when a typed-column writer in `qmf-data` streams rows into compressed row groups and fingerprints them as they stream, partitions are keyed `source / subject / kind / variant / year / month`, the open month is one file under a fixed key, each kind declares its freeze rule, a month whose gaps one re-fetch cannot fill freezes with them recorded, late rows for a frozen month become an automatic correction, reads and corrections are recorded as (key, range), one `dataset` card per series lists its frozen partitions, a card update claims the series key, the open file of a non-redownloadable series is pushed to the bucket after each commit batch, and importers for the old raw bi5 files and the risk-lab CSVs exist.

**Depends on.** DR2D and PRB-DP. It branches from the stack tip after DR2D (DR2E when stacked).

**Files.**

- [ ] Add `FD/store/engines/typed.py` (the writer and its streamed fingerprint) and `FD/series.py` (key, open month, freeze rules per kind, corrections, (key, range) records).
- [ ] Edit `FD/partitions.py` (`SeriesPartition` gains `subject`, `kind`, `variant`), `FD/store/facade.py` (`commit` refuses a different file for a frozen key unless marked a correction with a reason) and `FD/store/engines/__init__.py`.
- [ ] Add `FD/importers/__init__.py`, `FD/importers/dukascopy_raw.py` (reads old raw bi5 through `FD/dukascopy.py`'s decoder) and `FD/importers/csv_bars.py` (risk-lab one-minute CSVs).
- [ ] Edit `LB/kinds/dataset.schema.json` (card fields, `licence`, `world`, `redownloadable`, `replaced`, quality report) and `LB/marks.py` (`corrected` on overlap of a read range with a correction range).
- [ ] Add `LB/cards.py` (the card writer, which claims the series key).
- [ ] Edit `HB/bucket.py` (the open file of a non-redownloadable series after each commit batch).
- [ ] Add `FDT/test_typed_partitions.py`, `LBT/test_cards.py`, and `SP/data/p_mdread.py`, `p_key.py`, `p_freeze.py` and `p_marks.py`.

**Build.**

- [ ] Write the typed writer. It stores int64 time and int64 scaled prices, writes rows in row groups as they arrive, keeps no copy of the rows in the file metadata, and computes sha256 over a pinned logical encoding of the key and the time-ordered rows. It fsyncs before rename. It runs in a child process.
- [ ] Write the series rules. Ticks keep bid and ask in one row. Bid and ask bars are two series. A derived series is `source = derived, kind = <component>-v<version>`. Freeze rules are a table per kind (gap check, provider checksum, month end plus the settlement delay).
- [ ] Write the card writer and the marks rule.
- [ ] Write the two importers. Each writes partitions through `commit` and updates one card per series. They read the source read-only.
- [ ] Write the four probes on scratch roots, with one real month of EURUSD ticks from the server's raw-backup copy.

**You see.**

- [ ] A scratch import of one month of EURUSD ticks shows one `dataset` card with the month, its row count, its fingerprint and a coverage strip.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Five tests. Two writes of the same rows give the same fingerprint and one file. Bid m1 and ask m1 get different keys. A different file for a frozen key is refused without the correction mark. A ticks month with an injected gap freezes after one re-fetch returns the same gap, with the gap in `quality`. A fill after the freeze lands as a correction listing both fingerprints. Run the `qmf-data` and `qmx-library` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmf-data`, `qmx-library`, `qmx-hub` and `qmb` suites with `-n 2` at the parent and at head. Save `dr3a-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-MDREAD (read-back) on the server with one real month of EURUSD ticks. Save `dr3a-p-mdread.log`. Pass when P-MDREAD's read-back line holds and week and month peak RAM are recorded.
- [ ] Lane 3. P-KEY and P-MARKS. Save `dr3a-p-key-marks.log`. Pass when both pass.
- [ ] Lane 4. P-FREEZE, cases a to d, with a scratch bucket folder. Save `dr3a-p-freeze.log`. Pass when P-FREEZE passes.
- [ ] Lane 5. Read the lane 2 file with DuckDB 1.5.5. Save `dr3a-duckdb.log`. Pass when every column reads the same as the writer's rows.
- [ ] Lane 6. Import one year of the risk-lab one-minute CSVs on a scratch root. Save `dr3a-csv.log`. Pass when the card's months and row counts match the CSV rows, and the "2025 ask file incomplete" flag shows as a quality note.
- [ ] Lane 7. Old-engine evidence. Run the existing small-evidence tests of `FD/store/engines/parquet.py`. Save `dr3a-old-engine.log`. Pass when they pass unchanged.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr3a-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in `qmf-data` and `qmx-library`. Save `dr3a-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch roots and list processes on both machines. Save `dr3a-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Peak RAM in MB and seconds to write one week and one month of EURUSD ticks.
- [ ] Probe. Lane 2.
- [ ] Baseline. The week figure.
- [ ] Rule. Fail when the month's peak RAM is near four times the week's (P-MDREAD's FAIL line, where the month is held whole).

**Review gate.** None. DR3A changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR3A on the stack tip.

## Open one door to price history with the holdout lock in it (DR3B)

Work item W10. Fixes F6, F7, F8, F9, F40 and N15. ADs Lib AD-28, engine AD-31, AD-70 (the `data_scope`), HARNESS-REQUESTS H59 (the data half). Premise none. Acceptance P-FINALLOOK, and a sealed read refused with its reason. Real step the door switched on for agents (G-LAND). Gate none. Scenarios S-04, S-09, S-15, S-16, S-18, S-22, S-23. Done when a market-data door module in each host is the only writer of that machine's price store through `commit(files)`, reads `instruments()`, `card(series)`, `read(series or fingerprints, from, to, purpose)` and `materialise(fingerprints)`, always opens the store with the seal and the split definitions (with a `gap`), refuses sealed months except the one journaled final look served only by the primary, stages and pins PC-born partitions until the server verifies them, returns a handle for a big read and runs heavy reads in a child process, checks a run pass's `data_scope`, raises an inbox task when the sealed span exceeds `historical_holdout_months`, and fills the agent data tools at start-up while `datasets.json` retires.

**Depends on.** DR3A. It branches from DR3A's verified head.

**Files.**

- [ ] Add `HO/market_data.py` (the door) and its routes, mounted from `HO/host.py`.
- [ ] Edit `FD/splits.py` (`gap`, part of the split fingerprint) and `FD/seal.py` (the move by his click, journaled; the inbox task).
- [ ] Edit `R/passes.py` (`data_scope`).
- [ ] Edit `H/harness.py` (line 403, `DomainContext` gets the door) and `TL/service.py` (lines 242 to 265, `from_environment` and `datasets.json` go).
- [ ] Add `SP/data/p_finallook.py`. Add tests in `HOT/`, `FDT/`, `QA/qmx-router/tests/` and `QA/qmx-tools/tests/`.

**Build.**

- [ ] Write the door as 55 D-5 and Lib AD-28 say. A read without a split is exploration over every unsealed month. A read with a split names its `purpose` and gets only that segment. A sealed read is refused with the reason, never an empty answer.
- [ ] Make only the primary's door serve `final_look`. Other doors forward and wait. A final look reads into the run's own attempt folder and leaves nothing in a shared cache.
- [ ] Fill `data.instruments`, `data.bars`, `data.features` and `data.calendar` from the door at start-up. Delete `datasets.json`.
- [ ] Write `p_finallook.py`.

**You see.**

- [ ] On a scratch home with one imported month, the copilot's `data.bars` returns that month's bars with the card id, and a read of a sealed month is refused with "this month is sealed for the final look".

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Five tests. A sealed read is refused with its reason. A split read with `purpose: train` excludes the gap. A pass without `data_scope` is refused before start. A second `commit` of another file for a frozen key is refused. A big read returns a handle with path, rows and summary. Run the `qmx-host`, `qmf-data`, `qmx-router` and `qmx-tools` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the four suites and `qma-harness` with `-n 2` at the parent and at head. Save `dr3b-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-FINALLOOK on scratch roots on both machines. Save `dr3b-p-finallook.log`. Pass when P-FINALLOOK passes.
- [ ] Lane 3. Ask the copilot on haiku, on a scratch home with one imported month, for that month's bars and then for a sealed month. Save `dr3b-copilot.log`. Pass when the first answer cites the card and the second quotes the refusal reason.
- [ ] Lane 4. A remote read over the tailnet from the PC to the scratch server's door with a pass that has `data_scope` and one without. Save `dr3b-remote.log`. Pass when the first is served and the second is refused before start.
- [ ] Lane 5. `just ci` under the CI lock at head. Save `dr3b-ci.log`. Pass when every gate exits 0 and every suite failure also fails at the parent.
- [ ] Lane 6. A PC-born partition staged to the server door. Save `dr3b-staged.log`. Pass when it stays pinned on the PC until the server's `commit` verifies it, then becomes evictable.
- [ ] Lane 7. A read of 23 years of one-minute bars through the door, as a handle. Save `dr3b-big-read.log`. Pass when the host's memory stays flat and the child process does the read.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr3b-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the touched packages. Save `dr3b-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch roots and list processes on both machines. Save `dr3b-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds to read one month of ticks from the PC cache, from the server disk, and from the server's door over the tailnet.
- [ ] Probe. Lane 4 and lane 7.
- [ ] Baseline. None, first measure. P-MDREAD-TIMES repeats it after DR3C and DR6.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. DR3B changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR3B on DR3A.
- [ ] Real step (G-LAND). After he lands DR3B, the door is on for agents on the PC and the server with the next host start. The coordinator confirms lane 3's two answers on his real home and logs them.

## Import the old ticks on the server as partitions with cards (DR3C)

Work item W11. ADs Lib AD-25, Lib AD-16. Premise none. Acceptance the import's counts on one year match DR0's manifest, and P-MDREAD-TIMES afterwards. Real step **the import on the real server** (G-LAND, after DR3A and DR3B are landed). Gate none. Scenarios S-03, S-15, S-25. Done when a driver script imports the server's raw-backup copy of the old 10 GB and the risk-lab CSVs through the door's `commit`, one card per series, with counts that match DR0's manifest, and the raw copy stays untouched.

**Depends on.** DR0 and DR3B. It branches from DR3B's verified head.

**Files.**

- [ ] Add `SD/import_old_ticks.py` and edit `SD/README.md`.
- [ ] Add `SP/data/p_mdread_times.py`.

**Build.**

- [ ] Write the driver. It walks `/srv/qmx/data/raw-backup/`, calls DR3A's importers per instrument and month, commits through the server door, resumes from the last committed month after a stop, and writes a report with rows per month, files per series and a comparison against `MANIFEST.sha256`'s file list.
- [ ] Write `p_mdread_times.py` to record P-MDREAD-TIMES.

**You see.**

- [ ] On a scratch server root, one year of EURUSD imports into one ticks card whose months match the raw files of that year.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] One test runs the driver on a fixture of two months of bi5 files and asserts two partitions, one card, and a resume that adds nothing.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane. Run the driver's test and the `qmf-data` suite at head. Save `dr3c-regression.log`. Pass when both pass.
- [ ] Lane 2. Import one year of EURUSD and one year of USDJPY into a scratch root on the server, from the raw-backup copy read-only. Save `dr3c-year.log`. Pass when the report's file list equals the manifest's files for those years and every month has a partition or a recorded gap.
- [ ] Lane 3. Stop the driver mid-year and rerun it. Save `dr3c-resume.log`. Pass when it adds only the missing months and no file twice.
- [ ] Lane 4. Hash the raw-backup files of the year before and after. Save `dr3c-raw.log`. Pass when the hashes match.
- [ ] Lane 5. P-MDREAD-TIMES on the scratch year. Save `dr3c-times.log`. Pass when the numbers are recorded and nothing is killed.
- [ ] Lane 6. Ask the scratch door for that year's card. Save `dr3c-card.log`. Pass when the card lists the months, `complete_up_to` and a quality grade.
- [ ] Lane 7. Check the server's free disk before and after. Save `dr3c-disk.log`. Pass when the scratch root is removed after the lanes.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr3c-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check` and `lint` over `SD/`. Save `dr3c-gates.log`. Pass when both exit 0.
- [ ] Lane 10. List processes on the server. Save `dr3c-processes.log`. Pass when no driver process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Months imported per minute and peak RAM.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded so the real import's duration is known.

**Review gate.** None. DR3C changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR3C on DR3B.
- [ ] Real step (G-LAND). After he lands DR3A to DR3C, the coordinator runs the full import on the real server in the background as `qmx`, then P-MDREAD-TIMES, and saves both reports to `evidence/dr3c/real-import.log`. The old 10 GB on his `C:` drive stays until he answers the separate question of freeing it (Appendix E).

## Run backtests through the door and land one result shape (DR4)

Work item W12. Fix N2. ADs Lib AD-29, Lib AD-28, engine AD-31, Lab AD-5, ruling 125. Premise none. Acceptance P-QMBREAD. Real step the backtest tools bound for agents (G-LAND). Gate none. Scenarios S-09, S-10, S-21, S-22, S-29. Done when QMB's replay reader has a typed-partition entry point beside `read_recorded_replay_source`, `materialise` hands bid and ask bar series as a monthly pair and a one-sided pair is refused, every backtest lands as one `backtest-result` through one landing step linked `consumed` to the card version, `uses` to the bot version and `tests` to a hypothesis, QMB's own result files and the old Library's `backtest` items import into that shape, the agent backtest tools are bound and stop writing the old Library, and a synthetic-data template reads through the door with `purpose: train` only.

**Depends on.** DR3B. It branches from the stack tip after DR3B (DR3C when stacked).

**Files.**

- [ ] Edit `QB/host/replay.py` (a second entry point for typed partitions, lines 143 to 195 untouched) and `QB/data/policy.py` (the fingerprint, world, seal and split checks for the new entry).
- [ ] Add `QB/host/library_landing.py` (the landing step, shaped like `E/trace_export.py`).
- [ ] Edit `TL/service.py` (lines 191 to 230, backtests bound to `qmb_backtest`) and the `backtest` rows in `QX/catalog.py`.
- [ ] Add `LB/migrate/from_qmb_results.py` (CT-32 result files and old `backtest` items).
- [ ] Add the template folder `T/synthetic-data/` and its row in `T/catalog.py`.
- [ ] Add `SP/data/p_qmbread.py`. Add tests in `QBT/`, `QA/qmx-tools/tests/` and `LBT/`.

**Build.**

- [ ] Write the typed entry point. It verifies fingerprints, world, seal and split as the old reader does, builds quote pairs from tick rows, or from a bid and an ask bar series of the same month, and refuses a missing side.
- [ ] Write the landing step and bind the tools.
- [ ] Write the importer and the synthetic template (card `world: synthetic` with generator, settings and seed).
- [ ] Write `p_qmbread.py`.

**You see.**

- [ ] On a scratch home with one imported month, the copilot runs a backtest of an example bot and the Library shows one `backtest-result` card with its equity curve and its data used.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Four tests. A tick month replays to a fixed trade list. A bid and ask pair replays to the same list. A missing ask is refused. A landed result has the three edges. Run the `qmb`, `qmx-tools`, `qmx-library` and `qmx-control` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the four suites with `-n 2` at the parent and at head. Save `dr4-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-QMBREAD on one month. Save `dr4-p-qmbread.log`. Pass when P-QMBREAD passes.
- [ ] Lane 3. The copilot on haiku runs a backtest on a scratch home. Save `dr4-copilot.log`. Pass when one `backtest-result` lands with `consumed`, `uses` and, when given, `tests` edges, and the old `library.db` is not written.
- [ ] Lane 4. Import a sample of QMB's CT-32 result files and two old `backtest` items. Save `dr4-import.log`. Pass when each becomes one `backtest-result` with its trades blob.
- [ ] Lane 5. A correction to the month the result read. Save `dr4-corrected.log`. Pass when the result shows "corrected" and a result over another month does not.
- [ ] Lane 6. Run `T/synthetic-data/` with `purpose: test`. Save `dr4-synthetic.log`. Pass when the door refuses it, and with `purpose: train` a card with `world: synthetic` lands.
- [ ] Lane 7. Run QMB's existing replay examples. Save `dr4-qmb-examples.log`. Pass when they give the same trades as at the parent.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr4-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the touched packages. Save `dr4-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch home and list processes. Save `dr4-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds to replay one month from typed partitions.
- [ ] Probe. Lane 2.
- [ ] Baseline. The same month through the CT-10 path.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** DR4 changes what his copilot answers about backtests. It is appended on its clean verdict without waiting.

- [ ] Post to the operator in chat a screenshot of lane 3's answer and a short video of the copilot running a backtest and opening the result card, with one plain sentence on what changes for him.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR4 on the stack tip.
- [ ] Real step (G-LAND). After he lands DR4, the coordinator imports QMB's existing result files on his real home with `from_qmb_results.py` and logs the counts.

## Keep connections in one registry with scopes, homes and a health reading (DR5A)

Work item W13, part 1. Fixes F28, F29 (add time), F31, F33, F34, F35, F37, F38, N9, N20 and N22. ADs engine AD-28, AD-67, AD-68 (shared `slowed_until`), ruling 135. Premise none for this part (the cTrader premises gate DR5B). Acceptance P-NOTRADE (add time, stub adapter) and P-VAULT-AWAY (connections). Real step his first data connection added (G-LAND). Gate none. Scenarios S-05, S-18, S-28. Done when Settings hold one `connections` list (kinds `broker`, `platform`, `data`) read once from the old `brokers` section, adapters come from an open registry with their declarations (`auth`, `runs_on`, `session`, `limit_signals`, `limit_scope`, `error_map`, `health_check`, `published_limits`), each credential has one home and a save that gives it two homes is refused, a credential is `read` only when its probe proves it cannot trade, a key whose probe finds a live account it can trade is stored nowhere and its row reads `needs_you`, static read and data keys are re-filed under `qmx/read/*` and `qmx/data/*`, the `connections-health` workflow writes one reading word per connection into the heartbeat, a provider's own slow-down signal sets a shared `slowed_until` per connection or per egress address, and preflight blocks a fire whose connection is not healthy or not reachable from its placement.

**Depends on.** DR2C and DR2D. It branches from the stack tip after DR4, because the two share `T/catalog.py`.

**Files.**

- [ ] Edit `BR/models.py` (connection kinds, `scope`, `home`, the adapter list gains `mt5`), `BR/adapters.py` (declarations), `BR/credentials.py` (re-filing, refusal of a live-trade key), `BR/service.py` and `BR/server.py` (read-only rows over enabled accounts).
- [ ] Add `BR/registry.py` (the entry-point registry) and the data-provider adapters `BR/providers/dukascopy.py`, `binance_vision.py`, `ccxt_public.py`, `databento.py`, `firecrawl.py` and `http.py`.
- [ ] Edit `QX/service.py` (lines 466 to 474, the `brokers` section read once into `connections`).
- [ ] Edit `E/triggers/preflight.py` (connection healthy and reachable, else `blocked_config`) and `E/heartbeat.py` (connection readings, clock offset).
- [ ] Add the template folder `T/connections-health/` and its row in `T/catalog.py`.
- [ ] Add tests in `QA/qmx-broker/tests/`, `ET/` and `QXT/`. Extend `SP/data/p_notrade.py` and `SP/data/p_vault_away.py`.

**Build.**

- [ ] Write the registry and the declarations as 56 section 8.2 and engine AD-67 say. A CCXT key is used on one machine only.
- [ ] Write the health workflow. It walks the five setup states and writes `ok`, `slowed`, `maintenance`, `needs_you` or `down`. Only `down` is an incident, per masked signature `connection:<id>:<code>`.
- [ ] Write `slowed_until` per connection, or per (provider, egress IP) for `limit_scope: egress`.
- [ ] Extend the two probes with their DR5A halves. P-NOTRADE uses a stub adapter that returns a live account with trade scope.

**You see.**

- [ ] On a scratch home, Settings list a Dukascopy and a Binance data connection with `ok`, and a stub broker key that can trade a live account shows `needs_you` with nothing stored.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Five tests. The old `brokers` section reads into the same accounts. A save with two homes for one credential is refused. A stub live-trade key stores nothing and reads `needs_you`. A provider 429 with `Retry-After` sets `slowed_until`. Preflight blocks a fire whose connection reads `down`. Run the `qmx-broker`, `qmx-engine` and `qmx-control` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the three suites with `-n 2` at the parent and at head. Save `dr5a-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-NOTRADE (add time, stub). Save `dr5a-p-notrade.log`. Pass when P-NOTRADE's W13 stub line holds.
- [ ] Lane 3. P-VAULT-AWAY (connections) with the PC host stopped. Save `dr5a-p-vault-away.log`. Pass when a server-homed data connection's health check runs and reads `ok`.
- [ ] Lane 4. The health workflow on a scratch server home for Dukascopy, Binance public files and CCXT public endpoints. Save `dr5a-health.log`. Pass when each reads `ok` with its latency, and a blocked endpoint reads `down` with one incident.
- [ ] Lane 5. Preflight. Fire a workflow naming a `down` connection. Save `dr5a-preflight.log`. Pass when the fire is `blocked_config` with one item and no model call.
- [ ] Lane 6. The copilot on haiku lists accounts through the read-only broker tools. Save `dr5a-broker-read.log`. Pass when it lists them and no row can submit, change or cancel an order.
- [ ] Lane 7. Grep lane logs, Settings files and the Library for key values. Save `dr5a-leak.log`. Pass when none appears.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr5a-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the three packages. Save `dr5a-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch homes and list processes on both machines. Save `dr5a-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for one health walk over three data connections.
- [ ] Probe. Lane 4.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded as the health cadence's floor.

**Review gate.** None. DR5A changes no screen (the Connections screen is the UI session's).

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR5A on the stack tip.
- [ ] Real step (G-LAND). After he lands DR5A, the coordinator adds the Dukascopy and Binance public data connections on the real server (they need no key) and logs their readings.

## Give cTrader and MT5 sign-ins one home each, exchange codes there, and read broker history (DR5B)

Work item W13, part 2. Fixes F27, F32, F36, N5, N16 and N22. ADs engine AD-28, AD-67, AD-68, ruling 135. Premise P-CTSCOPE, P-CTREFRESH (same app) and P-CT2CONN (PRB-CT). Acceptance P-NOTRADE (tokens). Real step his first real cTrader connection added, with his one sign-in (G-LAND, G-CT). Gate G-CT, and PRB-CT's rows without the P-CTREFRESH fallback. Scenarios S-19, S-28. Done when his browser carries only the one-minute code, the PC's loopback receiver forwards it to the connection's home and keeps nothing, the home exchanges it and keeps the tokens in its own key store and never in the vault, the home is the grant's one refresh owner, `qmx_broker`'s short cTrader read sessions become calls to the home host's long-running `qmf-venue` session, existing `qmx/ctrader-*` entries are re-filed (client id and secret as `qmx/read/ctrader-app`) and their tokens removed locally with no tombstone, an MT5 adapter runs on the PC with an investor login, and a `download-broker` template pages cTrader history through the home session.

**Depends on.** DR5A and PRB-CT. It branches from the stack tip of the moment G-CT opens.

**Files.**

- [ ] Edit `BR/ctrader_transport.py` (reads through the home host's session) and `BR/credentials.py` (re-filing of `qmx/ctrader-*`).
- [ ] Add `BR/oauth.py` (the PC's loopback receiver on the one registered port, forwarding the code) and `BR/providers/mt5.py` (PC only).
- [ ] Add `HO/venue_session.py` (one long-running `qmf-venue` session per cTrader app and environment on its home) and mount its route in `HO/door.py` (the code exchange, `user` only).
- [ ] Edit `BR/registry.py` (the cTrader declaration with PRB-CT's facts).
- [ ] Add the template folder `T/download-broker/` and its row in `T/catalog.py`.
- [ ] Add tests in `QA/qmx-broker/tests/` and `HOT/`. Extend `SP/data/p_notrade.py` with the token half.

**Build.**

- [ ] Write the code path as 55 section 4 "Added" says. The home holds the app's client secret.
- [ ] Write the home session and route every cTrader read through it, including the other machine's reads, which forward to it.
- [ ] If P-CT2CONN recorded that the first connection dies with no event, add the liveness read to the health walk (its fallback).
- [ ] Write `download-broker`. It relays one history page at a time from the home session and writes the partition in the step's child process, as `source=<broker>` series.

**You see.**

- [ ] On demo, after the sign-in page, the scratch server's Connections row reads `ok`, the PC's keyring and the vault document hold no token, and a PC read of the demo account's balance goes through the server.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Four tests. The receiver forwards a code and stores nothing. Deleting a server-homed connection from the PC publishes no tombstone. A second home for the same app registration is refused. `download-broker` pages a fake history of three pages into one partition. Run the `qmx-broker` and `qmx-host` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the two suites with `-n 2` at the parent and at head. Save `dr5b-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-NOTRADE (tokens) on demo. Save `dr5b-p-notrade.log`. Pass when P-NOTRADE's token line holds.
- [ ] Lane 3. A refresh on the scratch server home, then a forwarded PC read. Save `dr5b-refresh.log`. Pass when the read succeeds after the refresh.
- [ ] Lane 4. One week of demo EURUSD ticks through `download-broker`. Save `dr5b-history.log`. Pass when one partition lands with its card and no request exceeds the provider's 5 per second.
- [ ] Lane 5. MT5 on the PC with his investor login, if given. Save `dr5b-mt5.log`. Pass when the account reads and `trade_allowed` is false, or the lane records `not run, no investor login`.
- [ ] Lane 6. P-CT2CONN's case as a lane. Save `dr5b-2conn.log`. Pass when the health walk detects a dropped first connection within one check.
- [ ] Lane 7. Grep lane logs, Settings, the vault document and the Library for token values. Save `dr5b-leak.log`. Pass when none appears.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr5b-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the two packages. Save `dr5b-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Close every venue session and list processes on both machines. Save `dr5b-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds per week of ticks through the home session.
- [ ] Probe. Lane 4.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. DR5B changes no screen. His sign-in happens on cTrader's own page.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR5B on the stack tip of the moment it is verified.
- [ ] Real step (G-LAND, G-CT). After he lands DR5B, the coordinator re-files his existing `qmx/ctrader-*` entries and posts "sign in once on cTrader with the read-only scope" to `QUESTIONS-FOR-OPERATOR.md`. The home is the server. A cTrader key on his PC that turns out to trade a live account reads `needs_you`, and the question says to replace it with a read-only one.

## Run feeds and downloaders as scheduled workflows that land items and partitions (DR6)

Work item W14. Fixes F5, F33, F47, N6 and N7. ADs engine AD-68, Lib AD-25, Lib AD-16, rulings 122, 128 and 131. Premise P-DUKA (PRB-DP). Acceptance P-BAN, and P-FREEZE (b) on a real calendar feed. Real step the first big downloads on the real server (G-LAND), and removing the PC's calendar scheduled task (G-CAL). Gate P-DUKA passed, or its fallback applied. Scenarios S-05, S-07, S-24, S-29. Done when the `feed` template (a `monitor` node first, slots for the source definition, `lands_as: source | partitions`) and the `download-dukascopy`, `download-binance` and `download-ccxt` templates exist, each downloader claims a partition key and writes through the door's `commit`, the economic calendar is a feed landing bitemporal partitions parsed by `FD/calendar_feed.py`, `t3-news-calendar-watch` uses that parser, the repo's `recorder/` folder is deleted, the 126 old calendar files are imported once, MQL5 articles, arXiv q-fin and one blog are example feeds, and the copilot can draft a feed from a sentence for his one yes.

**Depends on.** DR3B, DR5A and PRB-DP. It branches from the stack tip after DR5A.

**Files.**

- [ ] Add the template folders `T/feed/`, `T/download-dukascopy/`, `T/download-binance/` and `T/download-ccxt/`, and their rows in `T/catalog.py`.
- [ ] Edit `T/t3-news-calendar-watch/` (the proper parser).
- [ ] Edit `FD/calendar_feed.py` (rows by observation time, revisions as appends), `FD/dukascopy.py` (the seam that takes dukascopy-node's output), and add `FD/binance_vision.py` (checksummed bulk files).
- [ ] Delete `recorder/README.md`, `recorder/fetch_calendar.py` and `recorder/status.py`.
- [ ] Add `SD/import_calendar_files.py` and the example feed definitions under `T/feed/examples/`.
- [ ] Add `SP/data/p_ban.py` (with a local stub that answers 429 then 418) and tests in `ET/` and `FDT/`.

**Build.**

- [ ] Write the `feed` template as 55 section 7 says. An unchanged source ends the fire `silent`. New items are claimed by intent key and saved as `source` items `part-of` the feed's collection.
- [ ] Write the downloaders as SOLUTION-DESIGN section 30.1 says. One node per partition, heartbeat on its own thread, free-disk check before each write, dukascopy-node 1.50.0 with `--retries` and `--retry-on-empty`, one price side per run. If P-DUKA failed, use the fetcher its fallback names.
- [ ] Label Dukascopy's volume as its own liquidity on the card. Binance trades, aggTrades and bookDepth land as `trades` and `book` kinds.
- [ ] Write the calendar import and the example feeds.

**You see.**

- [ ] On a scratch server home, a Dukascopy download of one month lands one card per price side, and the calendar feed lands one month of events with a revision kept as a second row.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Four tests. An unchanged feed source ends `silent`. Two runs claiming the same partition key write one file. A calendar revision in an open month is an append. A Binance file with a bad checksum is refused. Run the `qmx-engine` and `qmf-data` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the two suites with `-n 2` at the parent and at head. Save `dr6-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-BAN on the scratch server with two Binance connections on one address. Save `dr6-p-ban.log`. Pass when P-BAN passes.
- [ ] Lane 3. P-FREEZE (b) on the real calendar feed into a scratch root. Save `dr6-p-freeze-b.log`. Pass when the case holds on real events.
- [ ] Lane 4. One month of EURUSD ticks through `download-dukascopy` on the scratch server. Save `dr6-dukascopy.log`. Pass when the month matches DR3C's imported month for the same dates in rows and prices, or the difference is explained on the card.
- [ ] Lane 5. The MQL5 articles example feed for one fire. Save `dr6-mql5.log`. Pass when new articles land as `source` items with `origin: feed` and a second fire is `silent`.
- [ ] Lane 6. The copilot on haiku drafts a feed from "watch this blog weekly". Save `dr6-draft.log`. Pass when a draft feed workflow exists and nothing is published until a yes.
- [ ] Lane 7. Import the 126 old calendar files into a scratch root. Save `dr6-calendar-import.log`. Pass when every file's events land and a rerun adds nothing.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr6-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the touched packages. Save `dr6-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch roots and list processes on both machines. Save `dr6-processes.log`. Pass when no `node` or download process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Minutes per month of ticks per price side from Dukascopy on the server.
- [ ] Probe. Lane 4.
- [ ] Baseline. PRB-DP's fetch time on the PC.
- [ ] Rule. No fail rule. Recorded so the first big download's duration is known.

**Review gate.** None. DR6 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR6 on the stack tip.
- [ ] Real step (G-LAND). After he lands DR6, the coordinator installs Node 24 LTS for `qmx` on the server, publishes the calendar feed and the Dukascopy downloader for EURUSD and USDJPY from August 2026 (after the old ticks end) on the real server, then runs P-MDREAD-TIMES again.
- [ ] Real step (G-CAL). With his approval, remove the PC's calendar scheduled task and log it. Without it, the task keeps running and the feed imports its files on each run.

## Take in any file through one streaming upload door and extract its text on the server (DR7)

Work item W15. Fixes F26, F41 and N1 (search on the PC). ADs Lib AD-8, AD-10, AD-27, engine AD-68 (the `save_source` step). Premise P-DOCLING (PRB-DS). Acceptance P-UPL, P-DISKFULL (uploads), P-OOM (with Docling), and P-TAINT and P-SRCH measured. Real step uploads and extraction switched on (G-LAND). Gate P-DOCLING passed, or its fallback applied. Scenarios S-06, S-07, S-20, S-26, S-27, S-30. Done when `POST /api/library/upload` on the PC host and on the server streams any file in chunks, hashes it while written, resumes by offset after re-hashing the partial, and has no size limit of QMX's own, every outside document lands as one `source` kind with `origin` and its slots, the `extract-source` workflow runs Docling with page and second locators, search indexes the whole text in chunks, the 64 MB body limit and the 1 MB search-text limit are gone, intake templates save finds through a `save_source` step keyed by canonical URL, and computer and browser captures land as `source` with `origin: capture`, their text redacted against the account ids in Connections.

**Depends on.** DR2B and PRB-DS. It branches from the stack tip after DR6. It shares no file with DR9, so the two may run at once.

**Files.**

- [ ] Edit `QX/server.py` (the PC upload route) and `HB/server.py` (`BODY_LIMIT` at line 66 goes, blob moves stream, the server upload route).
- [ ] Edit `LB/store.py` (`TEXT_LIMIT` at line 78 goes, `_index_object` indexes in chunks), `LB/fts.py` and `LB/search.py` (chunked whole-text search, paged answers).
- [ ] Edit `LB/kinds/source.schema.json` (`origin`, slots `original`, `text`, `pages/*`, `transcript`, `frames/*`, `canonical_url`, `extractor_version`).
- [ ] Add the template folder `T/extract-source/` and the shared step `T/_shared/save_source.py`, with rows in `T/catalog.py`. Edit the intake templates `T/a-fill-the-library/`, `T/clippings-into-research/` and `T/rs1-paper-scout/` to call it.
- [ ] Edit `H/procs.py` (captures land as `source` through the Library port).
- [ ] Add `SP/data/p_upl.py`. Extend `SP/data/p_diskfull.py` and `SP/data/p_oom.py`. Add tests in `LBT/`, `HBT/` and `QXT/`.

**Build.**

- [ ] Write the streaming route on both hosts. A PC upload streams through to the server, and the PC staging copy is kept until two remote copies exist.
- [ ] Write `extract-source` on Docling alone, in a child process, with the declared memory from P-DOCLING. Its home is `contabo` unless P-DOCLING's fallback moved it.
- [ ] Write the dedupe rules. Same bytes, same blob. Same canonical URL (normalised), same intent key. Same book with other bytes, same text hash within one `extractor_version`.
- [ ] Redact account ids from extracted text of captures. Keep the pixels.

**You see.**

- [ ] On scratch roots, a 400-page PDF uploaded on the PC is searchable on the PC by a phrase on page 312, and the hit opens at that page.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Four tests. A resumed upload re-hashes its partial and ends with the right hash. The same URL saved twice is one item. A phrase past the first 1 MB of text is found. An account id in a capture's text is redacted. Run the `qmx-library`, `qmx-hub`, `qmx-control` and `qmx-engine` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the four suites with `-n 2` at the parent and at head. Save `dr7-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-UPL with a 3 GB file generated on the server side of the stream and a 3 GB file from `D:` only if `D:` has 6 GB free, else from the server to itself. Save `dr7-p-upl.log`. Pass when P-UPL passes.
- [ ] Lane 3. P-DISKFULL (uploads) and P-OOM (with Docling) on the server. Save `dr7-p-diskfull-oom.log`. Pass when both pass.
- [ ] Lane 4. Upload a 400-page PDF and one hour of audio on scratch roots and search on the PC. Save `dr7-extract.log`. Pass when page and minute locators are right and the PC search finds a phrase from each.
- [ ] Lane 5. P-TAINT and P-SRCH with `SP/library/p_taint.py` and `p_srch.py` on 100,000 items. Save `dr7-taint-srch.log`. Pass when the numbers are recorded and nothing is killed.
- [ ] Lane 6. Run the `a-fill-the-library` template on a fixed URL twice. Save `dr7-save-source.log`. Pass when one `source` exists.
- [ ] Lane 7. A scanned PDF with no text layer. Save `dr7-ocr.log`. Pass when OCR text lands with page locators.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr7-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the touched packages. Save `dr7-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch roots, the large files and the cgroup, and list processes on both machines. Save `dr7-processes.log`. Pass when nothing from the lanes is left and `D:` has its space back.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Upload MB per second and peak RAM of the host during lane 2.
- [ ] Probe. Lane 2.
- [ ] Baseline. None, first measure.
- [ ] Rule. Fail when peak RAM grows with the file size (P-UPL's FAIL line).

**Review gate.** None. DR7 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR7 on the stack tip.
- [ ] Real step (G-LAND). After he lands DR7, the coordinator installs Docling for `qmx` on the real server and publishes `extract-source`.

## Let chat agents branch, merge, see history and blame, with line-by-line text merge (DR8)

Work item W16. ADs Lib AD-24, AD-30, engine AD-49. Premise none (P-MERGE ran in 55 section 11 and passed). Acceptance the merge tests and P-MERGE's two cases through the store. Real step none. Gate none. Scenarios S-08, S-14, S-17. Done when the three-way merge merges `text/*` slots with `git merge-file -p --diff3` (exit 0 lands both edits, a positive exit mints a `merge-conflict` with the marked text), merges `application/json` slots key by key, `history(item)` and `blame(item, slot)` are reads, the `library` toolset has `branch`, `merge`, `conflicts`, `resolve`, `history` and `blame` rows over the new store, and the engine claims a node's intent key at node start and releases it when the output lands.

**Depends on.** DR1B. It branches from the stack tip after DR7 (both edit `LB/store.py`).

**Files.**

- [ ] Edit `LB/store.py` (`_three_way`, the blob branch of `pick` at lines 645 to 655) and `LB/port.py` (`history`, `blame`).
- [ ] Add `LB/blame.py`.
- [ ] Edit `QX/catalog.py` and `QX/service.py` (the six `library` rows).
- [ ] Edit `E/runner.py` (the claim at node start and its release).
- [ ] Add tests in `LBT/`, `QXT/` and `ET/`.

**Build.**

- [ ] Write the text and JSON merges, and keep pick-one for binary blobs.
- [ ] Write `blame` at read from parents and line diffs.
- [ ] Add the six rows and the node-start claim.

**You see.**

- [ ] Two chats on haiku edit different lines of one note and both edits land. When they edit the same line, the inbox shows one conflict with both sides and the base.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Four tests. A clean text merge keeps both edits. A clashing edit mints one `merge-conflict` with diff3 markers. A JSON merge with one clashing key mints one conflict entry. `blame` names the version that last changed each line. Run the `qmx-library`, `qmx-control` and `qmx-engine` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the three suites with `-n 2` at the parent and at head. Save `dr8-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Two chats on haiku on a scratch home edit different lines of one note. Save `dr8-clean.log`. Pass when the merged note holds both edits.
- [ ] Lane 3. The same with one shared line. Save `dr8-conflict.log`. Pass when one `merge-conflict` exists and `resolve` closes it.
- [ ] Lane 4. A chat asks for `history` and `blame` of the note. Save `dr8-history.log`. Pass when each line names its author and version.
- [ ] Lane 5. Two workflow runs with one intent key start together. Save `dr8-claim.log`. Pass when one claims and the other links to it.
- [ ] Lane 6. A merged workflow that fails validation. Save `dr8-invalid.log`. Pass when it becomes a conflict.
- [ ] Lane 7. A binary blob changed on both sides. Save `dr8-binary.log`. Pass when pick-one applies as built.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr8-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the three packages. Save `dr8-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. List processes after the lanes. Save `dr8-processes.log`. Pass when no `claude`, `qmx_host` or lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for `blame` of a 1,000-line note with 50 versions.
- [ ] Probe. Lane 4 on a generated note.
- [ ] Baseline. None, first measure.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. DR8 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR8 on the stack tip.

## Let workflows read the Library, and run mini apps from it (DR9)

Work item W17. ADs engine AD-5, AD-19, AD-55, AD-63, AD-64, Lab AD-19. Premise none. Acceptance its journeys. Real step none. Gate none. Scenarios S-10, S-11. Done when the `library` node kind is available, run start resolves `@run` and `@library` references in `inputs` and records the pinned object ids on `run_created`, publishing a mini app writes a `mini-app` item, the host materialises published packs at start-up, and the harness binds `app:<id>` rows.

**Depends on.** DR1B. It branches from the stack tip after DR6. It shares no file with DR7.

**Files.**

- [ ] Edit `E/definition/registry.py` (line 94, `library` gains `available=True`), `E/service/runs.py` (resolve references at run start) and `QX/context.py` (the resolver).
- [ ] Edit `AP/` publish path (the module that publishes a pack; the builder names it from a scan in the PR body) and `HO/sessions.py` (materialise published packs at start-up).
- [ ] Edit `H/surface.py` (bind `app:<id>` rows).
- [ ] Add tests in `ET/`, `QXT/`, `QA/qmx-apps/tests/` and `HT/`.

**Build.**

- [ ] Switch the `library` node on and write the reference resolution. A reference to an item that does not resolve fails the start with one item.
- [ ] Write the three mini-app switches. The fourth (the sink) landed in DR1B.

**You see.**

- [ ] A workflow whose input is `@run:<Tuesday's run id>` starts and its first node reads that run's outputs from the Library.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Three tests. `@library:<id>` pins the object id on `run_created`. A missing reference fails the start. A published pack materialises on a fresh home's start-up. Run the `qmx-engine`, `qmx-control`, `qmx-apps` and `qma-harness` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the four suites with `-n 2` at the parent and at head. Save `dr9-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Run a workflow with `@run` of an earlier run on a scratch home. Save `dr9-at-run.log`. Pass when its `library` node reads the earlier outputs and the pinned ids are on `run_created`.
- [ ] Lane 3. Publish an example mini app, restart the host on a fresh home that syncs the Library. Save `dr9-app.log`. Pass when the app is materialised and its `app:` rows are bound in a new chat.
- [ ] Lane 4. The copilot on haiku calls one `app:` row. Save `dr9-app-call.log`. Pass when the answer lands as an `artifact` linked to the instance.
- [ ] Lane 5. A missing reference. Save `dr9-missing.log`. Pass when the start fails with one item.
- [ ] Lane 6. Run `SL/apps/e61_app_check.py`. Save `dr9-e61.log`. Pass when it passes.
- [ ] Lane 7. Run `SL/engine/e57_app_trigger.py`. Save `dr9-e57.log`. Pass when it passes.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr9-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the four packages. Save `dr9-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. List processes after the lanes. Save `dr9-processes.log`. Pass when no `claude`, `qmx_host` or lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds to resolve ten references at run start.
- [ ] Probe. Lane 2 with ten references.
- [ ] Baseline. A start with no references.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. DR9 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR9 on the stack tip.

## Send the same events to OpenObserve on the server, and let an outside agent look in (DR10)

Work item W18. Fixes F42 to F46 and N22 (H61). ADs engine AD-10, AD-15, AD-37, AD-65, AD-69, HARNESS-REQUESTS H60 and H61, rulings 123 and 126. Premise P-OO (PRB-DS). Acceptance P-REDACT and H61's check. Real step exporters switched on (G-LAND), with his OpenObserve sign-up if the install asks for one (G-OO). Gate P-OO passed, or its fallback applied. Scenarios S-12, S-13. Done when every write point of spans, heartbeat rows, incidents and logs also hands the record, after redaction, to an OpenTelemetry exporter that sends to one collector on the server with a disk queue (none on the PC), the collector forwards to OpenObserve, each chat the harness starts gets the CLI telemetry environment, Hindsight sends its traces, the heartbeat gains Library and Lab facts, the data health read lists card freshness, downloads and feeds, connections, free disk and bucket copy age, and an observer token on the door lists only the `ops` and doctor rows, traces, logs, the data health read and one diagnosis-note row, with an `inspect-qmx` runbook skill.

**Depends on.** DR2D and PRB-DS. It branches from the stack tip after DR9.

**Files.**

- [ ] Add `E/telemetry.py` (the exporter, fed after redaction). Edit `E/ledger/spans.py`, `E/ledger/store.py` (incidents), `E/heartbeat.py` (Library and Lab facts) and `E/ledger/redact.py` (one call site for exporters).
- [ ] Edit `H/launch.py` (the telemetry environment per chat) and `MM/hindsight.py` (traces on).
- [ ] Edit `HO/door.py` (the observer token in `BearerGate`) and `QX/service.py` and `QX/catalog.py` (the data health read and the diagnosis-note row).
- [ ] Add `QA/qmx-host/deploy/otelcol.yaml`, `QA/qmx-host/deploy/otelcol.service` and `QA/qmx-host/deploy/openobserve.service`.
- [ ] Add the skill `qmx-agents/plugin/skills/inspect-qmx/SKILL.md`.
- [ ] Add `SP/data/p_redact.py` and tests in `ET/`, `HT/` and `HOT/`.

**Build.**

- [ ] Write the exporter with the GenAI names pinned to one version of the conventions, and the collector config with a disk-backed queue whose drop and queue metrics feed data health.
- [ ] Write the observer token. It is created by him in Settings, revocable and expiring, and refuses `broker_read` and Library content rows.
- [ ] Write `inspect-qmx` as a Library skill that names each door, the doctor, the data health read and how to read a run's trace.

**You see.**

- [ ] On the scratch server, OpenObserve shows one run's trace across the PC and the server under `trace_id = run_id`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Three tests. An exported span carries no value the redactor masks. The observer token is refused on `broker_read` and on a Library content row. A chat's launch environment has `CLAUDE_CODE_ENABLE_TELEMETRY=1` and the server endpoint. Run the `qmx-engine`, `qma-harness`, `qmx-host` and `qmx-control` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the four suites with `-n 2` at the parent and at head. Save `dr10-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-REDACT. Save `dr10-p-redact.log`. Pass when P-REDACT passes.
- [ ] Lane 3. H61's check. Call the door with the observer token on `ops`, a trace, `broker_read` and a Library content row. Save `dr10-h61.log`. Pass when the first two answer and the last two are refused.
- [ ] Lane 4. A split run, data prep on the scratch server and a step on the PC. Save `dr10-trace.log`. Pass when OpenObserve shows one trace with both machines.
- [ ] Lane 5. Stop the collector for ten minutes during a run. Save `dr10-gap.log`. Pass when the run completes, the Library keeps its trace and logs, and the queue metric shows the drop.
- [ ] Lane 6. An outside Claude Code session with the observer token and `inspect-qmx` reads one run's trace. Save `dr10-outside.log`. Pass when it reads and its one write is a diagnosis note shown in the inbox.
- [ ] Lane 7. Read the data health rows. Save `dr10-health.log`. Pass when they list card freshness, feeds, connections, free disk on both machines and bucket copy age.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr10-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the four packages. Save `dr10-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Stop the scratch collector and OpenObserve, and list processes on both machines. Save `dr10-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Added milliseconds per span write with the exporter on.
- [ ] Probe. 10,000 span writes on a scratch home.
- [ ] Baseline. The same with the exporter off.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. DR10 changes no screen (the data health screen is the UI session's).

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR10 on the stack tip.
- [ ] Real step (G-LAND, G-OO). After he lands DR10, the coordinator installs the collector and OpenObserve as `qmx` on the real server. If the install asks for an account, it posts G-OO to `QUESTIONS-FOR-OPERATOR.md` and leaves the collector queueing to disk.

## Remove every invented capacity number that is left (DR11)

Work item W19. ADs engine AD-30, Lib AD-27, ruling 106. Premise none. Acceptance a grep finds none of the removed figures. Real step none. Gate none. Scenarios S-26. Done when none of the 6,144 MB overhead, the 12,288 MB budget, the 2,048 MB attempt memory, the 64 MB body, the 1 MB search text, the 1,000-bar read and the 2 GiB sync-back figures is left as a limit, and each place that needed a number reads a live reading or a provider's own limit.

**Depends on.** DR2A and DR7. It branches from the stack tip after DR10.

**Files.**

- [ ] Edit only the files that the Build grep finds at the parent head. The coordinator runs that grep before the dispatch and writes the list into `dispatch/dr11.md`. Expected from 55 D-11 are `BR/service.py` (bar paging), `RM/sidecar.py` (the sync-back cap) and any `E/settings.py` row DR2A left.
- [ ] Add one test file per touched package where a test is needed.

**Build.**

- [ ] Grep for `6_144`, `6144`, `12_288`, `12288`, `2_048`, `2048`, `64 * 1024 * 1024`, `1_000_000`, `1000` near `bars`, and `2 * 1024 ** 3`. Save `evidence/dr11/owner-grep.log`. Classify each hit as a limit or not.
- [ ] Replace each limit with a live reading or the provider's own limit. A probe bound stays and is labelled as one.

**You see.**

- [ ] The grep prints no capacity limit.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] One test per replaced limit asserts the code reads the live value from a fake reading. Run the touched suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the touched suites with `-n 2` at the parent and at head. Save `dr11-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. The grep at head. Save `dr11-grep.log`. Pass when no capacity limit is left.
- [ ] Lane 3. Read 23 years of one-minute bars through a broker read tool on a scratch home. Save `dr11-bars.log`. Pass when the read pages by the provider's limit and returns every bar.
- [ ] Lane 4. A remote run's sync-back of a 3 GB output on the scratch server. Save `dr11-syncback.log`. Pass when it completes with no cap error.
- [ ] Lane 5. The doctor on a throwaway home. Save `dr11-doctor.log`. Pass when every capacity figure it shows is a live reading.
- [ ] Lane 6. Run the engine's admission lanes. Save `dr11-admission.log`. Pass when they pass.
- [ ] Lane 7. Settings shows the replaced values as editable. Save `dr11-settings.log`. Pass when each is a Settings value with its measured default.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr11-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the touched packages. Save `dr11-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch roots and list processes. Save `dr11-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds to read 23 years of one-minute bars through the broker read tool.
- [ ] Probe. Lane 3.
- [ ] Baseline. None, the parent stops at 1,000 bars.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. DR11 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR11 on the stack tip.

## Add the trade kind, journals, components and lineage, and give every kind a card and a page (DR12)

Work item W20. ADs Lib AD-3, AD-17, AD-31, AD-32, AD-33, ruling 127. Premise none. Acceptance its journeys. Real step none. Gate none. Scenarios S-17, S-19, S-23, S-27, S-29. Done when the `trade` kind exists with world `backtest | paper | demo | live | synthetic`, journal imports from cTrader, MT5 and CCXT land fills as partitions ordered by observation time and round trips as `trade` items in one `collection` per account, deduped by broker ids with exact integer money and `moneyDigits`, `component` carries `component_type`, the funnel templates write `variant-of` with `what_changed`, `merged-from`, `uses` and `consumed` edges, and one `view(object_id, level)` read returns a card or a page for every kind as 55 section 3 tabulates.

**Depends on.** DR1B and DR3A. It branches from the stack tip after DR11.

**Files.**

- [ ] Add `LB/kinds/trade.schema.json`. Edit `LB/kinds/component.schema.json` and the `card` and `page` declarations in every `LB/kinds/*.schema.json`.
- [ ] Add `LB/view.py` (the one read, with computed facts) and edit `LB/port.py`.
- [ ] Add `FD/importers/journal.py` (cTrader, MT5 and CCXT fills to partitions and `trade` items).
- [ ] Edit the funnel templates `T/l1-idea-to-first-result/`, `T/d3-iterate-against-qmb/`, `T/d4-variant-comparison/`, `T/revolution-loop/`, `T/b-build-and-prove/`, `T/bc-build-a-component/` and `T/p1-portfolio-combination/` (the edges).
- [ ] Add tests in `LBT/`, `FDT/` and `ET/`.

**Build.**

- [ ] Write the kind, the importer and the edges as Lib AD-31 and AD-32 say. Lineage is written by the templates, never left to a model's choice.
- [ ] Write `view` with the common header and the per-kind facts. A fact that fails reads "unavailable" with the reason, never a stale number.

**You see.**

- [ ] On a scratch home, `view(<backtest-result id>, card)` returns the bot version, dataset and months, headline measure, trades and the hypothesis outcome, and `view(..., page)` returns its seven tabs.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Four tests. A journal import twice adds nothing the second time. Money keeps its exact integers. A variant run writes `variant-of` with `what_changed`. `view` returns at most five card facts for every kind. Run the `qmx-library`, `qmf-data` and `qmx-engine` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the three suites with `-n 2` at the parent and at head. Save `dr12-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. Import a demo cTrader account's fills on a scratch home. Save `dr12-journal.log`. Pass when fills land as partitions, round trips as `trade` items in the account's collection, and a rerun adds nothing.
- [ ] Lane 3. Run `d4-variant-comparison` on haiku with two variants. Save `dr12-lineage.log`. Pass when the family read returns parent, children and siblings with `what_changed`.
- [ ] Lane 4. Call `view` at card and page level for one item of every kind on a scratch home. Save `dr12-view.log`. Pass when every kind answers and the archived item shows "archived" with its reason.
- [ ] Lane 5. A corrupt trades blob. Save `dr12-unavailable.log`. Pass when the equity fact reads "unavailable" with the reason.
- [ ] Lane 6. Two indicators combined as a `combination` component. Save `dr12-component.log`. Pass when the combination `uses` both.
- [ ] Lane 7. A late fill after its month froze. Save `dr12-late-fill.log`. Pass when it lands as a correction and the round trip updates.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr12-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the three packages. Save `dr12-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch homes and list processes. Save `dr12-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds for `view` at card level for 100 items.
- [ ] Probe. Lane 4 on 100 items.
- [ ] Baseline. A plain `get` of the same items.
- [ ] Rule. No fail rule. Recorded for the UI session.

**Review gate.** None. DR12 changes no screen. The UI session renders cards and pages from `view`.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR12 on the stack tip.

## Give the Lab its backend workspace and train models on the PC (DR13)

Work item W21. ADs Lab AD-5, AD-19, AD-20, Lib AD-10, Lib AD-28. Premise P-GPU, run as the first Build box. Acceptance its journeys. Real step none. Gate none. Scenarios S-14, S-16. Done when a project is a `collection`, "New…" installs a template at one of four levels (quick idea, experiment, study, campaign), the workspace state is annotations on the project, Tuesday's run enters today's through DR9's references, the data panel reads the door and the card, problems are marks and conflicts, the timeline is history, and ML training on the PC is a placement with a GPU slot whose run pulls only the partitions it needs after a free-space check and records data fingerprints, code version and seed on the model item. Pods are not part of it.

**Depends on.** DR3B, DR9 and DR12. It branches from the stack tip after DR12.

**Files.**

- [ ] Add `QX/lab.py` (the Lab operations over the Library and the engine) and its rows in `QX/catalog.py`.
- [ ] Edit `LB/kinds/collection.schema.json` (the workspace annotation).
- [ ] Edit `T/d6-ml-training-run/` (data through `materialise`, the model's lineage) and `E/settings.py` (`placement.pc.gpu_slots` from P-GPU's reading).
- [ ] Add `SP/data/p_gpu.py` and tests in `QXT/` and `ET/`.

**Build.**

- [ ] Run P-GPU first. Train a small model on the PC's Quadro T1000 from cached partitions and record time, GPU memory and disk used. If it fails, the template ships with CPU training on the PC and the GPU slot off (its fallback), recorded in `decisions.tsv` and `QUESTIONS-FOR-OPERATOR.md`.
- [ ] Write the Lab operations and the template change.

**You see.**

- [ ] On a scratch home, "New experiment" creates a project collection with its template installed, and a training run on the PC lands a `model` item with its data fingerprints, code version and seed.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Three tests. "New…" at each level installs its template. The workspace annotation round-trips. A training run refuses to start when free space is below the partitions it needs. Run the `qmx-control` and `qmx-engine` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the two suites with `-n 2` at the parent and at head. Save `dr13-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. P-GPU. Save `dr13-p-gpu.log`. Pass when P-GPU's numbers are recorded and nothing is killed, or the fallback is recorded.
- [ ] Lane 3. A training run on the PC from two cached months. Save `dr13-train.log`. Pass when only those partitions were materialised and the model item carries the lineage.
- [ ] Lane 4. Open a project, pin two items, close and reopen on a scratch home. Save `dr13-workspace.log`. Pass when layout and pins come back.
- [ ] Lane 5. Tuesday's run in today's project through `@run`. Save `dr13-tuesday.log`. Pass when today's run reads it.
- [ ] Lane 6. The data panel for one card. Save `dr13-panel.log`. Pass when it shows months, quality and a sealed-month refusal.
- [ ] Lane 7. Check `D:` free space before and after lane 3. Save `dr13-disk.log`. Pass when the materialised partitions are evictable afterwards.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr13-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the two packages. Save `dr13-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch homes and list processes. Save `dr13-processes.log`. Pass when no training process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds per training epoch on the GPU slot.
- [ ] Probe. Lane 3.
- [ ] Baseline. The same run on the PC's CPU.
- [ ] Rule. No fail rule. Recorded as the template's default.

**Review gate.** None. DR13 changes no screen. The Lab screens are the UI session's.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR13 on the stack tip.

## Place each step next to its data (DR14)

Work item W22. ADs engine AD-20, AD-65, AD-70, Lib AD-28. Premise none. Acceptance its journeys, and `just ci` (the last of four runs). Real step none. Gate none. Scenarios S-18. Done when the runner sets each node's placement from its `runs_on` list and the heartbeat's partition summary, the adapter workaround that reads `runs_on` is gone, a placement that lacks the partitions and cannot reach the door waits `placement` and never fails, and a remote worker reads price data through the server's door with its pass's `data_scope`.

**Depends on.** DR3B and DR10. It branches from the stack tip after DR13.

**Files.**

- [ ] Edit `E/runner.py`, `E/core/ready.py` (the `runs_on` read at lines 283 to 292), `E/workers/remote.py` and `E/heartbeat.py` (the partition summary).
- [ ] Edit `RM/sidecar.py` (reads through the server door with the pass).
- [ ] Add tests in `ET/` and `QA/qmx-remote/tests/`.

**Build.**

- [ ] Write placement by locality as SOLUTION-DESIGN section 30.2 says, and delete the adapter workaround.
- [ ] Make the sidecar read through the server door over the tailnet.

**You see.**

- [ ] A two-node workflow with `runs_on: [pc, contabo]` whose data sits on the server runs its data step on the server.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Three tests. Placement prefers the machine whose summary holds the partitions. A node with no reachable data waits `placement`. A sidecar read without `data_scope` is refused. Run the `qmx-engine` and `qmx-remote` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `deepseek-flash` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the two suites with `-n 2` at the parent and at head. Save `dr14-regression.log`. Pass when head fails nothing the parent passes.
- [ ] Lane 2. `just ci` under the CI lock at head. Save `dr14-ci.log`. Pass when every gate exits 0 and every suite failure also fails at the parent.
- [ ] Lane 3. The two-node workflow on scratch roots. Save `dr14-locality.log`. Pass when the data step runs on the server.
- [ ] Lane 4. A remote step on the scratch server through `SL/server/e57_remote.py` with a `data_scope`. Save `dr14-remote.log`. Pass when it reads its card's months through the door.
- [ ] Lane 5. Cut the door for one minute during lane 4. Save `dr14-wait.log`. Pass when the node waits `placement` and resumes.
- [ ] Lane 6. Run `SL/server/e27_placement.py`. Save `dr14-e27.log`. Pass when it passes.
- [ ] Lane 7. A split run from 55 section 5. Save `dr14-split.log`. Pass when each step runs on its machine and the PC step's partitions were materialised first.
- [ ] Lane 8. Run `tools/secret_scan.py`. Save `dr14-secrets.log`. Pass when it is clean.
- [ ] Lane 9. Run `fmt-check`, `lint` and `types` in the two packages. Save `dr14-gates.log`. Pass when every exit code is 0.
- [ ] Lane 10. Remove the scratch roots and list processes on both machines. Save `dr14-processes.log`. Pass when nothing from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds from run start to the data step's start with locality placement.
- [ ] Probe. Lane 3.
- [ ] Baseline. The parent's placement on the same workflow.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. DR14 changes no screen.

**Merge.**

- [ ] The coordinator's CLEAN verdict at the exact head SHA, or its verdict after the one fix round.
- [ ] Low findings in `lows.md`. Findings outside this section in `BACKLOG.md`.
- [ ] Verdict in `ledger.tsv` with the patch-id.
- [ ] The root appends DR14 as the tip of the stack.

## Close the program

- [ ] Every PR is stacked with a CLEAN verdict, or is skipped with its gate, its fallback or OBSOLETE named in `RESUME.md`.
- [ ] Every real step that ran has its log in `evidence/<id>/real-*.log`. Every real step still waiting names its gate in `QUESTIONS-FOR-OPERATOR.md`.
- [ ] `SP/data/FINDINGS.md`, `FINDINGS-server.md` and `FINDINGS-ctrader.md` hold every probe row this program ran.
- [ ] List the branches and worktrees that are now safe to delete in `RESUME.md`, and wait for his go. Delete nothing.
- [ ] Tell the operator in plain words what changed for him, what is still waiting on him, and the stack's root and tip links.

## Appendix A. Prototype evidence

Facts this plan rests on, each measured or read on 2026-10-22.

- **P-MERGE ran.** `git merge-file -p --diff3` exits 0 with both edits on a clean merge and 1 with diff3 markers on a clash (55 section 11, git 2.55.0). DR8 relies on it.
- **The deletion session's PRs, read with `gh pr list` and `git diff`.** PR 168 (`build/mwr`, `77539d1f`) edits `AP/road/check.py`, `QX/catalog.py`, their two tests and `SL/apps/e61_app_check.py`. PR 169 (`build/del3b`, `feb7121b`) changes 738 files (80 insertions, 203,970 deletions). It deletes `qma-core`, `qma-wire`, `qma-daemon` and the daemon plugins, edits `AP/supervisor.py`, drops `qma-core` from the `qmx-engine`, `qma-harness` and `qmx-apps` manifests, and deletes `tools/tests/test_qma_callers.py` and `scripts/dev/qma_callers.py`.
- **What PR 169 leaves, read with `git grep` at `feb7121b`.** `openai-codex==0.160.0` at `qmx-agents/pyproject.toml:50`. `qma/serve.py`, `H/profiles.py`, `H/relay.py` and `H/money_words.py` present. `QX/server.py:106,111` calls `runs_list` and `record_work`. `H/tools.py:958` and `E/definition/lint.py:165` call `named_money_act`.
- **Disks.** `C:` 324 GB with 9.1 GB free. `D:` 150 GB with 4.7 GB free. `D:/QMX-worktrees` holds 130 folders and `D:/Temp` 55 check folders. His real home `~/.qmx` is 221 KB (`library.db` 110 KB).
- **The server.** Ubuntu with 193 GB disk (171 GB free), 11.9 GB RAM (11.4 GB available at idle), 6 cores, `python3.12` and `uv` present, no `node`, `rclone`, `psql` or `docker`, no `qmx` user, and `/srv/qmx` holding only `bld` and `check`.
- **The PC.** `node` is installed. `rclone` is not.
- **Code truth for the Files blocks.** `origin/engine/base` `8af1a1cd` and `origin/build/del3b` `feb7121b`, read with `git ls-tree` and `git grep`, no checkout.

## Appendix B. W0 items after the deletion session

The deletion session (run 2026-10-22-E, PRs 168 and 169, and its planned DEL4B in `D:/QMX-worktrees/qma-ship/build/dispatch/del4b.md`) covers part of W0. The Arm box rechecks each row at the merged root.

| W0 item | Status | Evidence | In this program |
|---|---|---|---|
| W0.1 DEL3a, the three money-word call sites, two tests, three manifests, the callers test | DONE-BY-DELETION-SESSION | PR 168 removes the `road/check.py` and `catalog.py` calls and their tests. PR 169 rewrites `supervisor.py`'s check, drops `qma-core` from the three manifests and deletes the callers test and script | no PR |
| W0.2 DEL3, the old core, wire and daemon with their importers | DONE-BY-DELETION-SESSION | PR 169 deletes the three packages, the daemon plugins, the examples and importers named in 55 section 8 item 2 | no PR |
| W0.2 rest of DEL4 | DONE-BY-DELETION-SESSION if DEL4B lands, else REMAINING | `langchain`, `langgraph` and `deepagents` left with `qma-daemon`'s manifest. `openai-codex` is still at `qmx-agents/pyproject.toml:50` at `feb7121b`. The session's DEL4B plans its removal | DEL4R, built only if REMAINING |
| W0.3 rest of DEL2 | REMAINING | `qma/serve.py`, `H/profiles.py`, `H/relay.py` present. `console.py:797-798` launches `qma.serve`. `HO/host.py:50` imports the shim. DEL3B's brief kept them | DEL2R |
| W0.4 RUN1c | REMAINING | `QX/server.py:106,111` and `QX/service.py:801` at `feb7121b` | RUN1C |
| W0.5 DEL3b, the harness's word list | REMAINING | `H/money_words.py`, `H/__init__.py:38`, `H/tools.py:958`, `E/definition/lint.py:165`, `QXT/test_catalog.py:92-97`. MWR's brief held it out of scope | MWH |

No W0 item is OBSOLETE at `feb7121b`. A row the Arm box finds gone at the merged root becomes OBSOLETE and its PR is skipped.

## Appendix C. Files two PRs share

Two PRs that share a file never run at once (Override 9). The coordinator also intersects the actual changed files with `git diff --name-only` before each dispatch.

| File | PRs |
|---|---|
| `QX/service.py` | RUN1C, DR1B, DR5A, DR8, DR10 |
| `QX/catalog.py` | RUN1C, DR2D, DR4, DR8, DR10, DR13 |
| `QX/server.py` | RUN1C, DR7 |
| `QX/node.py` | DR2B, DR2D, DR2E |
| `HO/host.py` | DEL2R, DR1B, DR2A, DR2B, DR3B |
| `HO/door.py` | DR2C, DR5B, DR10 |
| `LB/store.py` | DR1A, DR1B (tests only), DR2A, DR2B, DR7, DR8 |
| `LB/port.py` | DR8, DR12 |
| `LB/kinds/*.schema.json` | DR3A, DR7, DR12, DR13 |
| `HB/server.py` | DR2B, DR7 |
| `HB/bucket.py` | DR2D, DR3A |
| `E/settings.py` | DR2A, DR11, DR13 |
| `E/heartbeat.py` | DR2A, DR5A, DR10, DR14 |
| `E/runner.py` | DR8, DR14 |
| `T/catalog.py` | RUN1C, DR4, DR5A, DR5B, DR6, DR7 |
| `H/harness.py` | DR1B, DR3B |
| `H/launch.py` | DEL2R, DR10 |
| `TL/service.py` | DR3B, DR4 |
| `BR/registry.py`, `BR/credentials.py` | DR5A, DR5B |
| `MM/hindsight.py` | DR2E, DR10 |
| `SP/data/p_notrade.py` | DR2C, DR5A, DR5B |
| `SP/data/p_vault_away.py` | DR2C, DR5A |
| `SP/data/p_diskfull.py`, `p_oom.py` | DR2A, DR7 |
| `SD/README.md` | DR0, DR3C |

Pairs proven disjoint by their Files blocks, so they may run at once. DEL2R with DR1A. RUN1C with DR1A. PRB-DP with PRB-DS (PRB-DS writes standalone scripts and `SP/data/FINDINGS-server.md`). DR2B with DR2C. DR7 with DR9. Every other pair runs in table order.

## Appendix D. Defaults

Every value here is Claude's default, set without the operator, and changeable by his word.

- Builders run reasoning effort `max`. The scripts-only PRs (DR0, PRB-DP, PRB-DS, PRB-CT, DR3C) may run `high`.
- The real step of a PR runs only on code he has landed (Override 10). The alternative is running real steps from the verified stack head before he lands it.
- The server user is `qmx`, home `/srv/qmx/home`. The Library store is `/srv/qmx/library`. The old-ticks copy is `/srv/qmx/data/raw-backup/`.
- `rclone` lives in `D:/Tools/rclone/` on the PC. dukascopy-node lives in `D:/Tools/dukascopy-node/` for the probe.
- `backup-weekly` keeps the maintenance loop's current cadence.
- The full-disk floor on each machine is measured at start, editable in Settings.
- Hindsight uses Ubuntu's PostgreSQL package with pgvector.
- The first real Dukascopy download runs EURUSD and USDJPY from August 2026, where the old ticks end.
- The observer token expires after 30 days. OpenObserve keeps 14 days. Both are Settings values.
- The cTrader loopback port is the one already registered on his read app.

## Appendix E. Gates and calls

| Gate | What opens it | What waits | What proceeds without it |
|---|---|---|---|
| G-DEL | His review agent merges PRs 164 to 169 (and DEL4B if opened) into `engine/base` | every PR's branch | the DR0 copy run |
| G-LAND | He lands the stack on `engine/base` up to a PR | that PR's real step | every build, check and scratch probe |
| G-FLIP | His click on the inbox card "Move the Library to the server" | the flip | everything else, with the PC as primary |
| G-R2 | He opens a Cloudflare R2 bucket and adds it as an rclone remote on the server | the bucket legs of DR0, DR2D and DR3A, and freeing his `C:` drive | everything. Files made on the server have one copy, the screens say so, and the old 10 GB stays on `C:` |
| G-CT | His one sign-in on cTrader's consent page for a demo account with the `accounts` scope | PRB-CT, DR5B and its real step | DR5A, DR6 and every keyless download |
| G-DISK | His go to remove merged worktrees and check folders on `D:` | a second parallel builder when `D:` is below 3 GB | one builder at a time |
| G-CAL | His approval to remove the PC's calendar scheduled task | that removal | the calendar feed, which imports the task's files |
| G-OO | His OpenObserve sign-up, only if the install asks for an account | OpenObserve on the real server | the collector, queueing to disk |

Recommended answers. G-R2 yes, opened before G-FLIP, about $2 to $3 a month at today's sizes. G-DISK yes. G-CAL yes. Ruling 135 stays the lead's decision, written in `26` for him to read.

One question sits outside this program. May QMX remove the old 10 GB from his `C:` drive once the server and the bucket each hold a checked copy? Recommended yes. Nothing is removed in this program.

## Appendix F. Risks

- **`D:` is nearly full.** 4.7 GB free. Every check worktree and its venv cost space. The program removes each check worktree after its verdict, runs one builder at a time below 3 GB, and puts large files on the server.
- **One model family.** DeepSeek builds and DeepSeek checks. The verdict says so. Acceptance probes carry the weight.
- **Permission refusals.** Claude Code's auto-mode classifier refused the deletion session's money-word edits once. MWH removes more of the same list. If the DeepSeek harness refuses, the builder stops and reports, and the coordinator posts the refusal to `QUESTIONS-FOR-OPERATOR.md` and builds the next PR. Nobody edits permission settings.
- **The deletion session may add PRs.** The Arm box reads every open deletion PR, and G-DEL waits for them.
- **A demo order.** P-CTSCOPE sends one order on a demo account with a read-only token and expects a refusal. It never runs on a live account.
- **Provider throttling.** Dukascopy, Binance and cTrader throttle. Their own signals set `slowed_until`. QMX adds no limit.

## Appendix G. Not in this program

- The UI. `UI-HANDOFF.md` section 17 lists the data round's screens for the UI session.
- Trading servers. Their design belongs to the trading-node session. This program builds only the data contract of 55 section 5 and the Connections rows.
- Pods. Lab AD-19 leaves them out.
- Paid futures data. The Databento adapter is registered in DR5A. No download runs until a strategy needs futures (ruling 122).
- Server eviction of durable blobs (F23, Lib Deferred), direct bucket reads for burst machines (Lib Deferred), and the DuckDB 2.0 bump (after P-MDREAD-TIMES and two weeks of 2.0).
- Freeing his `C:` drive, which waits for his answer.

