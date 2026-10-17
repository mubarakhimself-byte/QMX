# QMX workflow engine core plan

This program builds the QMX workflow engine core as the new package `qmx-engine`, on the harness's public API. The one harness edit is HG1, which grants H0, H15, H16 and H17 (ruling 89, granted by the operator on 2026-10-17). It follows `architecture/workflow-engine/` (33 ADs) and the rulings in `research/methodology/26-operator-rulings-and-alignment.md`.
The operator gets one engine that runs script-only, mixed and agentic workflows, replays only failed or changed work, pauses at usage limits and resumes alone, and ships a pack of 31 templates as ship-ready working defaults, installed disabled (ruling 83).
The rule it enforces is that every invariant a PR adds has a live check that ran green at that PR's head, and that, after HG1, `qma-harness` is byte-identical to HG1's verified head.
PR ids in order are EP0 and EP1 (probes), HG1 (the granted harness PR, the root of the engine stack), EP2 to EP14 (the engine stack), and TP1 to TP4 (the template pack, stacked on EP14). Data is held (ruling 91), so no data PR runs.
Every PR starts from the stack base branch `engine/base`, made from `origin/rebuild/base` at `ed704c924e5f50c79a13531f7d491c7dce254666`, which already holds the merged HP stack.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md`. The selection rule at the end of that playbook picks it, because the work is sequenced and the operator reviews before anything lands. Nothing merges in this program. The coordinator appends each verified PR to its track's linear stack, and the operator lands the stacks himself after the run.

The plan makes five overrides to autopilot-stack. Each is named again where it applies.

- Override 1 replaces step 1's owner. One `poteto-agent` builder on `opus` per PR, running on the operator's PC in its own worktree, not a Cursor cloud agent. `/deslop` is not installed, so the builder rereads its full diff instead. No Bugbot runs on this repo.
- Override 2 replaces step 4's verdict. The operator's light rule of 2026-10-15 (memory `light-verification-per-pr`) applies. One build and one independent check per PR. The checker is a second `poteto-agent` on `opus` and runs 3 or 4 live checks that prove the PR's point. Only blockers and anything touching money, his logins or keys block. Low findings go to `lows.md` and never block. The same builder does the one fix round, resumed, not a fresh agent. The coordinator reviews the fix diff itself, with no second checker.
- Override 3 is the lane count. `check-plan.mjs` demands ten lanes per PR. In this plan the ten lanes are a MENU, not a quota. Lanes 1 to 4 are the proving set the checker runs. Lanes 5 to 10 run only when the checker judges one of them the likeliest to break the PR's point. A lane box outside the run set is checked with a `ledger.tsv` row that says `menu, not run`. No coding session starts ten agents or ten lanes for one PR.
- Override 4 is the perf block. No speed gate runs unless speed is the PR's point. EP4 (the ledger) and EP12 (the scheduler tick) carry real rules. Every other perf block records a number for the trail and fails nothing.
- Override 5 is the rebase cadence. A PR's single fix round finishes before the next PR is built on top of it. The stack is rebased once per fix, not per round, and never onto a moving trunk during the run.

Opus checking Opus is weaker than a review across model families. Every checker report says so in its first lines. Fable reviews only when the operator asks.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Check the stack base branch. The lead creates `engine/base` locally from `ed704c924e5f50c79a13531f7d491c7dce254666` before the run. `git rev-parse engine/base` must print that SHA. On the operator's go, and not before, the coordinator pushes it with `git push origin engine/base` and checks `git ls-remote origin refs/heads/engine/base`. Log both lines in `decisions.tsv`.
- [ ] State the protocol and this plan to the operator in plain words, then stop. Start execution only on the operator's explicit go.
- [ ] In the same message, list what only he can do, with a time for each. Log his answers in `D:/QMX-worktrees/qma-ship/engine/decisions.tsv`.
  - [ ] Say go. About one minute.
  - [ ] Confirm that his OpenRouter key is still in the keyring under `qmx/openrouter`, from the HP program. The coordinator never reads it. Test runs on real models use it for the cheap OpenRouter rows (ruling 51, and the 2026-10-14 ruling that live provider tests use OpenRouter). The planner's estimate is about 400 small OpenRouter calls over the whole program, mostly Track T. One minute.
  - [ ] Type `/login` once in the ship home only if a lane reports that the plan login in `D:/QMX-worktrees/qma-ship/home/claude` expired. Two minutes, at most once.
  - [ ] Keep the PC awake and plugged in, and do not start `qma.serve` on the ship home while the run is live. The coordinator also requests keep-awake through `mcp__ccd_host__request_keep_awake`.
- [ ] Read these from trunk at program start. Re-read them at every tick. Log each read in `decisions.tsv`.
  - [ ] `git show origin/main:CLAUDE.md` for the project rules on trunk, then Read `C:/Users/Mubarak/Desktop/QMX/CLAUDE.md`, whose QMA v2 section is not on `main` yet.
  - [ ] `git -C D:/QMX-worktrees/agent-system show plan/agent-system:tracker/qma-v2/ENGINE-PLAN.md`. The plan branch is local only.
  - [ ] `architecture/workflow-engine/ARCHITECTURE-SPINE.md` and `SOLUTION-DESIGN.md` sections 2, 3, 4, 5.1, 6.2, 8, 10, 17 and 18, from the same branch. That folder is the contract.
  - [ ] `research/methodology/26-operator-rulings-and-alignment.md`, all sections. Its latest ruling wins over every other file.
  - [ ] Read `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md`, `shipping.md` and `opening-a-pr.md`, then `C:/Users/Mubarak/.claude/skills/no-comments/SKILL.md` and `show-me-your-work/SKILL.md`. These live in the local install, not in the repo.
- [ ] Create the store `D:/QMX-worktrees/qma-ship/engine/` with `decisions.tsv`, `ledger.tsv`, `lows.md`, `evidence/`, `review/` and `homes/`. Write these standing orders into `decisions.tsv` as its first rows.
  - [ ] Builders and checkers are `poteto-agent` on `opus`. Never `bulk-worker`. Fable only when the operator asks. Every brief says "do not spawn sub-agents".
  - [ ] At most two agents at once in all, usually one builder and one checker, plus the coordinator (operator, 2026-10-17, matching the efficient 2026-10-15 run).
  - [ ] No file under `qmx-agents/packages/qma-harness/` changes in any PR except HG1, granted by the operator on 2026-10-17 (ruling 89).
  - [ ] No step reads, prints or copies a plan token, a provider key or a ChatGPT token. Secrets are named by keyring reference only. No step spends on any Anthropic or OpenAI API. Plan-profile turns go through the CLI login in the ship home.
  - [ ] Money stays read-only. No PR touches a broker credential, `qmn/`, or a money act.
  - [ ] Every test gate and lane runs with every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA` unset, because this shell sets them and they broke tests before.
- [ ] Write the standing briefs `D:/QMX-worktrees/qma-ship/engine/BRIEF-BUILDER.md` and `BRIEF-CHECKER.md`. Copy `D:/QMX-worktrees/qma-ship/BRIEF-BUILDER.md` and `BRIEF-CHECKER.md`, then change the plan name, the file boundary, the branch names, the test commands and the store path to this plan's. The checker brief opens its report with "Opus reviewed Opus. A cross-family review was not run."
- [ ] On the operator's go, arm the audit tick as `/loop 1h` with the tick prompt below. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk. Audit the operation against it and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then post a short status message to the operator in chat only when the audit found a tracked change that no earlier status message reported, such as a PR opened, a code-ready head, a round launched or closed, a verdict, a merge, a stuck agent and the action taken, a blocker added or cleared, or a decision only the operator can make. Name every such change and nothing else. Do not repeat a table, the merged list, or an unchanged blocker. If the audit found none, end the turn with no reply text. Either way, log this tick's row in your decision trail. The row names the items reported, or none."
- [ ] On the operator's hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

- [ ] Spawn one builder per PR with the Agent tool, `subagent_type: "poteto-agent"`, `model: "opus"` and `run_in_background: true`. The brief names the PR id, its plan section, the parent branch and head, and points at `BRIEF-BUILDER.md`. Briefs point at files and never paste them. Every brief says "do not spawn sub-agents".
- [ ] Spawn one checker per PR at its code-ready head, the same way, pointing at `BRIEF-CHECKER.md`.
- [ ] Follow this dependency graph. Stacked work branches from the parent PR's branch at its verified head (Override 5).
  - [ ] EP0, EP1 and HG1 are independent and first. All branch from `engine/base`. EP0, EP1 and HG1's lanes use the ship home's plan login, so they take the lane lock one at a time. A sensible first pair is EP0 and HG1, then EP1 and EP2.
  - [ ] EP2 after HG1, on `engine/hg1`. EP3 after EP2. EP4 after EP3. EP5 after EP4. EP6 after EP5. EP7 after EP6. EP8 after EP7. EP9 after EP8.
  - [ ] EP10 after EP9 and EP0, whose `FINDINGS.md` fixes the turn-end detector.
  - [ ] EP11 after EP10 and EP1 (27b N4). EP12 after EP11. EP13 after EP12. EP14 after EP13.
  - [ ] TP1 after EP14. TP2 after TP1. TP3 after TP2. TP4 after TP3.
  - [ ] EP1's findings gate EP11 and feed the later packets L3 and L6 in Appendix G.
- [ ] Hold the file boundaries.
  - [ ] Track E and Track T PRs touch only `qmx-agents/packages/qmx-engine/**`, `scripts/live/engine/**`, `scripts/probes/engine/**`, and the files a PR's **Files** block names outside them.
  - [ ] Only HG1 edits `qmx-agents/packages/qma-harness/**`, and only the files its **Files** block names.
  - [ ] Only EP2 edits `qmx-agents/pyproject.toml`, `qmx-agents/uv.lock`, `tools/ci.py` and `tools/test_all.py`. EP12 may edit `qmx-agents/uv.lock` again if it adds the cron library.
  - [ ] Only HG1, EP9 and EP13 edit `qmx-agents/packages/qmx-control/src/qmx_control/service.py`, and only HG1 edits `qmx_control/server.py`, each only in the lines its **Build** block names.
  - [ ] No PR other than HG1 touches `qmx-agents/packages/qma-harness/**`. No PR touches `qmb/`, `qmn/`, `qml/`, `packages/` (QMF), or `apps/qmx-ui/`.
- [ ] Hold the review gate. EP14 and TP4 change what the operator sees. They wait for his review in chat with screenshots and a video at the end of the run.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Run `command -v origin`. If it is missing, use `gh` and record that in `decisions.tsv`. Never require `gt`.
- [ ] Branch `engine/<pr-id>` from the parent branch at its verified head, in the worktree `D:/QMX-worktrees/eng-<pr-id>`. Open the PR ready, never draft, per **Opening a PR**, with `gh pr create --base <parent-branch> --head <branch> --repo MubarakHimself/QMX`. EP0, EP1 and HG1 target `engine/base`.
- [ ] The harness diff check is `git diff --quiet <harness base> HEAD -- qmx-agents/packages/qma-harness`. The harness base is `engine/base` for EP0, EP1 and HG1, and `engine/hg1` at HG1's verified head for every later PR. In a lane, "at base" for a harness suite run means that same harness base.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Put `TMP`, `TEMP` and `UV_CACHE_DIR` on `D:`.
- [ ] Run `uv run --no-sync python -m poethepoet fmt-check`, `lint` and `types` once in `qmx-agents/packages/qmx-engine` (`qma-harness` and `qmx-control` for HG1, and `qmx-control` when another PR edits it), and `uv run --no-sync python tools/secret_scan.py`, before the PR-facing push. Push with hooks on.
- [ ] Reread the full diff before each commit in place of `/deslop`, which is not installed (Override 1). Run `/no-comments` before review.
- [ ] No full `just ci` per PR. Run it once before EP14's check and once before TP4's check, under the CI lock `mkdir D:/QMX-worktrees/.ci-lock`.
- [ ] Do not rebase onto `rebuild/base` or any moving trunk during the run (Override 5). Rebase a child only when its parent's fix round changed the parent's head.
- [ ] End each commit message with the attribution lines from the session's system reminder. End each PR body with the line the reminder names.

### Verdict and merge, for every PR (append to the stack, never merge)

- [ ] At the code-ready head SHA, one checker runs one round per `BRIEF-CHECKER.md` (Override 2). It reads the diff and the PR body, runs the PR's unit tests with `-n 2`, the gates above, and lanes 1 to 4 of the PR's **Verify, live** block, plus at most one menu lane (Override 3). It writes `review/<pr-id>-check-<head8>.md` whose first line is CLEAN or NOT CLEAN.
- [ ] Blockers, money, login and key findings go back to the same builder, resumed for one fix round. Low findings go to `lows.md` with the PR id and never block.
- [ ] After the fix round, the coordinator reads the fix diff itself, reruns the failing lane, and records the verdict in `ledger.tsv` with head SHA, parent SHA and `git patch-id --stable`. No second checker runs.
- [ ] Append the PR to its stack on a clean verdict, per autopilot-stack step 5 and step 6. The PR base is its parent branch. Only EP0, EP1 and HG1 target `engine/base`. No owner merges, arms auto-merge or closes. The operator lands the stacks bottom-up after the run, then merges `engine/base` into `rebuild/base` with his own click.

### Boot recipe, for every live lane

Lanes run on the operator's PC, not on cloud VMs. No `control-cli` or `control-ui` skill is installed. Lanes drive the engine through its check scripts under `scripts/live/engine/` and `scripts/probes/engine/`, the engine's own CLI `python -m qmx_engine`, and from EP13 on the REST door of `qmx_engine.host`.

- [ ] `git -C D:/QMX-worktrees/agent-system fetch origin <branch>`, then check out the head SHA detached in `D:/Temp/<pr-id>-check`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Put `TMP`, `TEMP` and `UV_CACHE_DIR` on `D:`. Run `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] A lane that needs no model runs on a throwaway home `D:/QMX-worktrees/qma-ship/engine/homes/<pr-id>-<lane>`. A lane that needs a plan model opens the harness in-process inside its check script on the ship home `D:/QMX-worktrees/qma-ship/home`, the way HP lanes did, and only while it holds the lane lock `mkdir D:/QMX-worktrees/.engine-lane-lock`. `Harness.open` kills the CLI trees it finds for its home, so two harnesses on one home would kill each other's chats.
- [ ] A lane that needs a key provider adds the OpenRouter row from `scripts/live/qma/switch_lane.py` (`OPENROUTER_ROW`) to its throwaway home, credential ref `qmx/openrouter`, and never reads the value.
- [ ] The read-only diagnostics are `python -m qmx_engine explain <run_id>`, reads of `engine.sqlite` with `mode=ro`, the run journals under `<home>/runs/`, `Get-Process`, and from EP13 `GET /api/workflow-runs/{id}/explain`.
- [ ] Save a text capture as `<slug>.log`, which is the CLI's screenshot. Save a screen as `<slug>.png` with `ffmpeg -f gdigrab -i title=<window title> -frames:v 1`. Put both in `D:/QMX-worktrees/qma-ship/engine/evidence/<pr-id>/` and return the paths with the report.
- [ ] Remove the lane lock, then confirm with `Get-Process` that no `claude` or `qma-cli-launcher` process from the lane is left.

## Settle the harness facts the engine leans on (EP0)

**Depends on.** None. It branches from `engine/base`.

**Files.**

- [ ] Create `scripts/probes/engine/common.py`, `p_background.py`, `p_turn_end.py`, `p_asks.py`, `p_cache.py`, `p_limits.py`, `p_compact_window.py`, `p_runtime.py` and `test_common.py`.
- [ ] Create `scripts/probes/engine/FINDINGS.md`.

**Build.**

- [ ] In `common.py`, open the harness in-process on a given home with `qma.boot` scrub first, the lane lock, a log helper, and a helper that reads a chat's `model_call` rows from `<home>/runs/<sid>/journal.jsonl`. Reuse `scripts/live/qma/common.py` by path where it already does the job.
- [ ] In `p_background.py`, start a Background chat on the plan profile, with the model the `triage` role lists first for that profile in Appendix H, through `Harness.start_chat(NewChat(..., kind=Background()))`, with `Background` imported from `qma.harness.launch` because EP0 runs at `engine/base`, before HG1 exports it (Appendix F, H0). Send one `InjectedText`. Record the reply and the chat record's `kind`.
- [ ] In `p_turn_end.py`, run five Background turns of three lengths and time three end detectors against the true end. The detectors are the chat record's `turn` field read from `QmxHome.chats_dir / f"{sid}.json"`, the last session block in `ControlService`, and the `model_call` row in the run journal. Record misses and the worst lag for each.
- [ ] In `p_asks.py`, have a Background chat in `default` mode ask to write a file. Answer the `permission` block with `Harness.answer(AskId(...), Reject("unattended run"))`. Record the time to the answer, that the chat went on, and the `tool` blocks.
- [ ] In `p_cache.py`, start two Background chats on one model whose prompts share a static prefix of about 3,000 tokens and differ only after it. Record `cache_read_input_tokens` of the second chat from its journal rows. Repeat on an OpenRouter row and record what the relay journals.
- [ ] In `p_limits.py`, on a throwaway home with the fake model from `scripts/live/qma/fake_model.py` and `s10_usage.feed`, feed a rejected five-hour reading. Record that `Harness.send` on a Background plan chat raises `LaunchRefused`, the reason text, and where `Harness.usage()` exposes the reset time.
- [ ] In `p_compact_window.py`, add `quirks.env.CLAUDE_CODE_AUTO_COMPACT_WINDOW` to an OpenRouter row in a throwaway home and confirm that the launched CLI receives it. Do not drive a chat to compaction. Record that Background chats are verbatim, so `/compact` from the engine never dispatches.
- [ ] In `p_runtime.py`, record `sys.version`, `sqlite3.sqlite_version`, whether `uuid.uuid7` exists, and whether `qmx_ledger.journal.fingerprint` gives byte-stable output for one document across two processes.
- [ ] In `FINDINGS.md`, write one row per probe with the observed value, PASS or FAIL, and the PR the value feeds.

**You see.**

- [ ] `FINDINGS.md` has a filled row for each of the seven probes, and the turn-end row names one detector with 5 of 5 turns caught.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `scripts/probes/engine/test_common.py` gains a case that the journal reader sums `cache_read_input_tokens` from two fixture rows and skips a malformed line. Run `uv run --no-sync python -m pytest scripts/probes/engine -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run `git diff --quiet engine/base HEAD -- qmx-agents/packages/qma-harness` and the `qma-harness` suite with `-n 2` at base and head. Save `ep0-regression.log`. Pass when the diff is empty and both runs give the same pass count.
- [ ] Lane 2. Run `p_turn_end.py` on the ship home. Save `ep0-turn-end.log`. Pass when one detector catches 5 of 5 turn ends and its worst lag is recorded in seconds.
- [ ] Lane 3. Run `p_asks.py`. Save `ep0-asks.log`. Pass when the reject lands within 2 s, no file is written, and the chat produces a final text block.
- [ ] Lane 4. Run `p_cache.py`. Save `ep0-cache.log`. Pass when the second plan chat shows `cache_read_input_tokens` above 0, or the log records 0 with both chats' row ids.
- [ ] Lane 5. Run `p_background.py`. Save `ep0-background.log`. Pass when the reply arrives and the record's kind is `background`.
- [ ] Lane 6. Run `p_limits.py`. Save `ep0-limits.log`. Pass when the send raises `LaunchRefused` and a reset time is read from `UsagePage`.
- [ ] Lane 7. Run `p_compact_window.py`. Save `ep0-compact.log`. Pass when the launched CLI's env holds the window value from the row.
- [ ] Lane 8. Run `p_runtime.py`. Save `ep0-runtime.log`. Pass when every value is recorded and the two fingerprints match.
- [ ] Lane 9. Run `p_cache.py` on the OpenRouter row. Save `ep0-cache-key.log`. Pass when the relay journal records cache read and write fields for both chats.
- [ ] Lane 10. After all probes, list processes. Save `ep0-processes.log`. Pass when no `claude` or `qma-cli-launcher` process from the probes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). The turn-end detector's worst lag in seconds, recorded for EP10.
- [ ] Probe. `p_turn_end.py`, five turns.
- [ ] Baseline. None, the engine does not exist at the base. Record head only.
- [ ] Rule. No fail rule. A lag above 5 s is written into `FINDINGS.md` as a risk for EP10.

**Review gate.** None. EP0 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP0 with base `engine/base`. The operator lands it after the run.

## Settle the runner-outside and mixed-model facts (EP1)

**Depends on.** None. It branches from `engine/base`. Its findings gate EP11 and feed the later packets L3 and L6 in Appendix G.

**Files.**

- [ ] Create `scripts/probes/engine/p_runner_outside.py`, `p_model_ids.py`, `tasks/` (ten small coding and data tasks, each with a checker script), and `test_tasks.py`.
- [ ] Edit `scripts/probes/engine/FINDINGS.md` with the E23 and E24 rows.

**Build.**

- [ ] In `p_runner_outside.py` (E23), drive a raw `claude_agent_sdk` client in a throwaway venv on `D:`, with `CLAUDE_CONFIG_DIR` pointed at the ship home's plan folder `D:/QMX-worktrees/qma-ship/home/claude`, as HP0 did. Never copy the login files. Run the ten tasks twice on the model the `triage` role lists first for the plan profile in Appendix H. Mode A disables `Bash`, `Write`, `Edit` and `NotebookEdit` through `disallowed_tools` and adds an in-process SDK MCP server with `sandbox_bash`, `sandbox_write` and `sandbox_read` that execute in a `qmx-probe` Docker container when Docker Desktop runs, else in a scratch folder subprocess. Mode B uses the built-in tools in a scratch folder. Record per task pass or fail, turns and wall time, whether the SDK honoured the disallow list, and whether the extra server loaded per client. The agentOS comparison of E23 stays unsettled and is recorded as such.
- [ ] In `p_model_ids.py` (E24, the CLI half), point a raw client at the fake model's loopback provider and define a sub-agent with `AgentDefinition(model="deepseek/deepseek-v4.1-flash")` and another with a Kimi id. Have the main agent call both. Record the `model` field of every request the fake provider receives, and whether a tier alias env rewrote it. No key is used. The relay-routing half (H10) is a later harness packet.
- [ ] Write both rows in `FINDINGS.md` with the numbers and the packet each feeds.

**You see.**

- [ ] `FINDINGS.md` holds the E23 pass rates for both modes and the E24 list of model ids exactly as the wire saw them.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_tasks.py` gains a case that each task's checker fails on an empty scratch folder and passes on the task's reference answer. Run `uv run --no-sync python -m pytest scripts/probes/engine/test_tasks.py -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run `git diff --quiet engine/base HEAD -- qmx-agents/packages/qma-harness`. Trunk has no probe. Save `ep1-regression.log`. Pass when the diff is empty.
- [ ] Lane 2. Run `p_runner_outside.py` mode A. Save `ep1-mode-a.log`. Pass when every task records a result and no built-in write or Bash tool call appears in the transcript.
- [ ] Lane 3. Run `p_runner_outside.py` mode B. Save `ep1-mode-b.log`. Pass when every task records a result, so the two pass rates compare.
- [ ] Lane 4. Run `p_model_ids.py`. Save `ep1-model-ids.log`. Pass when the log lists each request's `model` field and says whether the full ids arrived unchanged.
- [ ] Lane 5. Run one mode A task with Docker Desktop stopped. Save `ep1-no-docker.log`. Pass when the scratch-folder fallback runs and the log names it.
- [ ] Lane 6. In mode A, ask the agent to use `Bash` by name. Save `ep1-disallow.log`. Pass when the SDK refuses the tool and the agent falls back to `sandbox_bash`.
- [ ] Lane 7. List file changes in the ship home's plan folder and in `~/.claude` before and after. Save `ep1-home.log`. Pass when only session files in the plan folder changed and nothing in `~/.claude` changed.
- [ ] Lane 8. Inspect the container's env during a mode A task. Save `ep1-container-env.log`. Pass when no provider key, `CLAUDE_CONFIG_DIR` or plan path appears.
- [ ] Lane 9. Count plan-profile turns from the run journals. Save `ep1-turns.log`. Pass when the total is recorded for Appendix E.
- [ ] Lane 10. List processes and containers. Save `ep1-cleanup.log`. Pass when no probe container or CLI process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Wall time per task in modes A and B, recorded for L6.
- [ ] Probe. Both modes of `p_runner_outside.py`, interleaved task by task.
- [ ] Baseline. Mode B is the baseline. Record it first for each task.
- [ ] Rule. No fail rule. A mode A slowdown above 50% is written into `FINDINGS.md` as a risk for L6.

**Review gate.** None. EP1 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP1 with base `engine/base`. The operator lands it after the run.

## Grant the harness exports, per-chat compaction, per-chat hooks and tool rows (HG1)

**Depends on.** None. It branches from `engine/base` and is the root of the Track E stack. The operator granted H0, H15, H16 and H17 on 2026-10-17 (ruling 89). This is the one PR in the program that edits the harness, so it lands before EP2, the first engine PR that leans on any of the four.

**Files.**

- [ ] Edit `qmx-agents/packages/qma-harness/src/qma/harness/__init__.py`, `harness.py`, `launch.py` and `tools.py`, only in the lines the **Build** block names.
- [ ] Edit `qmx-agents/packages/qma-harness/tests/test_tools.py` and `tests/test_launch.py`, and create `tests/test_chat_options.py`.
- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/server.py` (`OPERATIONS` rows only) and `service.py` (501 stubs only), because `test_tools.py` requires every `AGENT_OPERATIONS` name to be an `OPERATIONS` name.
- [ ] Create `scripts/live/qma/hg1_grants.py`, reusing `scripts/live/qma/common.py`.

**Build.**

- [ ] H0. Export `Background`, `Child` and `Interactive` from `qma.harness` and add them to `__all__`. No behaviour changes.
- [ ] H15. Add a per-chat compaction option to `NewChat`, `compact_at: float | None = None`, accepted only for Background and Child chats and refused for Interactive ones. `launch.py` turns it into `CLAUDE_CODE_AUTO_COMPACT_WINDOW` for that one chat's CLI, on plan and key profiles alike. `None` keeps today's behaviour. Export the option's type if it has one.
- [ ] H16. Add per-chat hooks to `NewChat`, `hooks: ChatHooks | None = None`, for Background and Child chats only. `ChatHooks` carries async callbacks for PreToolUse (observe only, it cannot allow or deny), PostToolUse, PreCompact, Stop and SubagentStop. `launch.py` appends them after the money gate, which stays first and unchanged. The global `[claude] hooks` setting is not touched. Export `ChatHooks`.
- [ ] H17. Add the `AGENT_OPERATIONS` rows of SOLUTION-DESIGN 13 with its Effects. `workflow_drafts_put` and `workflow_tests_run` are DOMAIN_WRITE, so saving a draft and running a test never ask. `workflows_put` is re-scoped to publish and `workflows_run` to live runs, and both stay MANAGE, so publishing and a live run each ask once. The `workflow_triggers_create/enable/disable/run_now`, `workflow_runs_cancel/resume`, `workflow_versions_archive` and `apps_archive` rows are MANAGE. `workflow_drafts_get`, `workflow_versions_list`, `workflow_runs_get/list/explain`, `workflow_triggers_list` and `workflow_inbox_list` are READ. The Library and Lab rows of H17 wait for their own programs, because their functions do not exist yet.
- [ ] Add the same names to `qmx_control.server.OPERATIONS` with the REST paths of SOLUTION-DESIGN 13, and give each a `ControlService` method that returns the existing 501 `not_implemented` until an engine is attached. EP13 fills them.
- [ ] Update `test_tools.py`. The tool-table test pins every new row and its Effect, and a new case asserts `asks()` is False for `workflow_drafts_put` and `workflow_tests_run` under the default `domain_write = "allow"`, and True for `workflows_put` and `workflows_run`.

**You see.**

- [ ] `uv run --no-sync python -c "from qma.harness import Background, Child, Interactive, ChatHooks"` prints nothing, and the `qma-harness` suite passes with the new rows.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_chat_options.py` covers `compact_at` and `hooks` refused on an Interactive chat, the env value set for one Background chat and absent for its neighbour, and the money gate first in the hook list. `test_tools.py` pins the new rows and asks. Run `uv run --no-sync python -m pytest tests -q -n 2` in `qma-harness` and `qmx-control`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run the `qma-harness` and `qmx-control` suites with `-n 2` at `engine/base` and at head, and `git diff --stat engine/base HEAD -- qmx-agents/packages/qma-harness`. Save `hg1-regression.log`. Pass when head fails nothing that base passes, and the diff lists only the files this PR names.
- [ ] Lane 2. H15. Run `hg1_grants.py compact` on the ship home under the lane lock. It starts one plan-profile Background chat with `compact_at` 0.40 and one without, and reads each launched CLI's env. Save `hg1-compact.log`. Pass when only the first chat's CLI holds `CLAUDE_CODE_AUTO_COMPACT_WINDOW` and both chats answer.
- [ ] Lane 3. H16. Run `hg1_grants.py hooks`, a Background chat with `ChatHooks` that is asked to read one file and to try a money act by name. Save `hg1-hooks.log`. Pass when PostToolUse and Stop fire for the read, the money gate still denies the money act, and an Interactive chat started beside it fires no engine hook.
- [ ] Lane 4. H17 and H0. Run `hg1_grants.py tools`, which imports `Background` and `Child` from `qma.harness`, starts `qma.serve` on a throwaway home, and calls `workflow_drafts_put`, `workflow_tests_run`, `workflows_put` and `workflows_run` through the copilot's tool surface. Save `hg1-tools.log`. Pass when the import works, the first two raise no ask and return 501, and the last two each raise exactly one ask.
- [ ] Lane 5. Start an Interactive chat with `compact_at` set. Save `hg1-interactive.log`. Pass when it is refused with a named error and no CLI starts.
- [ ] Lane 6. Start `qma.serve` on the ship home after the lanes. Save `hg1-serve.log`. Pass when it starts and `/api/doctor` shows no new failure.
- [ ] Lane 7. Run `tools/secret_scan.py` and the money path scan. Save `hg1-scans.log`. Pass when both are clean.
- [ ] Lane 8. Read the `__all__` diff. Save `hg1-exports.log`. Pass when it adds only `Background`, `Child`, `Interactive` and `ChatHooks`.
- [ ] Lane 9. Call one new `OPERATIONS` route over REST without the bearer. Save `hg1-auth.log`. Pass when it returns 401.
- [ ] Lane 10. List processes after the lanes. Save `hg1-processes.log`. Pass when no `claude` or `qma-cli-launcher` process from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Background chat start time in ms with and without `ChatHooks`.
- [ ] Probe. Three starts each in lane 3.
- [ ] Baseline. The start without hooks.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. HG1 is not review-gated. The operator granted its scope in ruling 89.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends HG1 with base `engine/base`, as the root of the Track E stack.

## Seat the qmx-engine package on the harness's public names (EP2)

**Depends on.** HG1. It branches from `engine/hg1` at HG1's verified head.

**Files.**

- [ ] Create `qmx-agents/packages/qmx-engine/pyproject.toml` and `src/qmx_engine/__init__.py`, `py.typed`, `settings.py`, `__main__.py`.
- [ ] Create the layer packages `src/qmx_engine/definition/`, `core/`, `ledger/`, `nodes/`, `triggers/`, `ports/`, `service/`, `workers/`, `memory/`, `templates/`, each with an `__init__.py`.
- [ ] Create `tests/test_import_rules.py` and `tests/test_settings.py`.
- [ ] Create `scripts/live/engine/common.py`.
- [ ] Edit `qmx-agents/pyproject.toml` (workspace member, source, and the three ignore lists), `qmx-agents/uv.lock`, `tools/ci.py` and `tools/test_all.py`.

**Build.**

- [ ] Write `pyproject.toml` in the shape of `qmx-ledger`'s, with dependencies `qma-harness`, `qmx-control`, `qmx-ledger`, `qma-core`, `pydantic==2.13.4` and `jsonschema` at the version already in `qmx-agents/uv.lock`, and dev tools at the workspace pins.
- [ ] Write `settings.DEFAULTS`, the one home of every engine default. Each entry carries the comment "Claude's default, UI-editable". The values are in Appendix H.
- [ ] Write `tests/test_import_rules.py` with `ast`, in the style of `qma-harness/tests/test_import_rules.py`.
  - [ ] Any import of a `qma.harness.<submodule>` fails, with no exception (E15). HG1 exports `Background`, `Child` and `ChatHooks` from `qma.harness` (H0, H16), so `qmx_engine.ports.harness_adapter` imports them from there. AD-3's fallback, the one allow-listed import of `Background` and `Child` from `qma.harness.launch`, is kept only as safety. If HG1 is ever parked, the coordinator restores that one named exception in this test and logs it in `decisions.tsv`.
  - [ ] `qma.core` is allowed only as `qma.core.barriers.money_path`. `qma.daemon`, `qmx_agents`, `qma_wire`, `langchain*`, `langgraph*` and `claude_agent_sdk` are refused anywhere in `qmx_engine`.
  - [ ] `qmx_engine.core` and `qmx_engine.definition` import no `ports`, `nodes`, `workers`, `ledger`, `sqlite3`, `subprocess` or `httpx`, and call no `time.time`, `datetime.now`, `random.*` or `os.environ` (AD-1, AD-6).
  - [ ] `TestMode(` appears nowhere under `src/`.
- [ ] In `scripts/live/engine/common.py`, add the lane lock, the throwaway-home helper, the in-process harness opener from EP0's `common.py`, and a PASS/FAIL logger.
- [ ] Add `qmx-engine` to `tools/ci.py`'s workspace loop and to `tools/test_all.py`'s suites with `["python", "-m", "pytest", "tests", "-q"]`.

**You see.**

- [ ] `uv run --no-sync python -c "import qmx_engine, qmx_engine.settings"` prints nothing, and `tools/ci.py` lists `qmx-engine` for fmt-check, lint and types.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `tests/test_import_rules.py` gains one case per rule above, each with a planted source string that must fail. `tests/test_settings.py` checks that every key of Appendix H has its literal default. Run `uv run --no-sync python -m pytest tests -q -n 2` in `qmx-agents/packages/qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run `git diff --quiet engine/hg1 HEAD -- qmx-agents/packages/qma-harness` and the `qma-harness` suite at `engine/hg1` and head. Save `ep2-regression.log`. Pass when the diff is empty and the pass counts match.
- [ ] Lane 2. E15. Copy the package to a scratch folder, add `from qma.harness.chat import Chat` to `core/__init__.py`, and run the import rules there. Save `ep2-e15.log`. Pass when the test fails naming that file and the clean head passes.
- [ ] Lane 3. Run `uv sync --frozen --all-packages --all-groups` in `qmx-agents` on a clean venv on `D:`. Save `ep2-sync.log`. Pass when it succeeds and `import qmx_engine` works.
- [ ] Lane 4. Run fmt-check, lint and types in `qmx-agents/packages/qmx-engine`. Save `ep2-gates.log`. Pass when all three exit 0.
- [ ] Lane 5. Plant `TestMode(` in a scratch copy of `settings.py`. Save `ep2-testmode.log`. Pass when the rule fails.
- [ ] Lane 6. Plant `import time; time.time()` in a scratch copy of a `core` module. Save `ep2-clock.log`. Pass when the rule fails.
- [ ] Lane 7. Run `tools/test_all.py` restricted to `qmx-engine` and `qma-harness`. Save `ep2-test-all.log`. Pass when both suites run and pass.
- [ ] Lane 8. Run `python -m qmx_engine --help`. Save `ep2-cli.log`. Pass when it prints the subcommands planned so far and exits 0.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `ep2-secrets.log`. Pass when it is clean.
- [ ] Lane 10. Read `uv.lock`'s diff. Save `ep2-lock.log`. Pass when it adds only `qmx-engine` and no new third-party package.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Import time of `qmx_engine` in ms.
- [ ] Probe. `python -X importtime -c "import qmx_engine"` once at head.
- [ ] Baseline. None, the package is new. Record head only.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. EP2 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP2 on `engine/hg1`.

## Define, validate and lint the qmx.workflow/1 format (EP3)

**Depends on.** EP2.

**Files.**

- [ ] Create `src/qmx_engine/definition/model.py`, `registry.py`, `folder.py`, `validate.py`, `lint.py`, `overlay.py` and `schema/qmx.workflow.1.json`.
- [ ] Create `tests/test_definition.py`, `tests/test_lint.py`, `tests/test_overlay.py` and fixture folders under `tests/fixtures/workflows/`.
- [ ] Create `scripts/live/engine/x03_validate.py`.

**Build.**

- [ ] In `model.py`, write the pydantic models of SOLUTION-DESIGN section 2.1 as 27d left it. The stored document holds no `version`, `content_hash` or lifecycle field. The semver is a Library annotation, the lifecycle is a ref fact, and the hash is computed, never stored (AD-11, AD-14). Include `connections` keyed by source node name, port and target list, and the edge fields `map`, `key`, `explicit` and `chunk`. The maps are `one | zip | broadcast | chunk | keyed-join | cartesian`, and `chunk` is `{by: items | tokens, size?, fill}` (27b B1). `runs_on` defaults to `pc` (27b S13).
- [ ] Build the fixture `paper-scout-min` from SOLUTION-DESIGN section 2.1 with two changes from 27b. Node n6 becomes a `rule` node with ports `true` and `false` (S22), and the edge into the agent node uses `map: chunk` (B1).
- [ ] In `registry.py`, register every AD-5 kind with its ports, default effect and `available` flag. A pack may register a type `<pack>.<name>` with a `base_kind`, and the validator checks it against the base kind's contract. `note` is the one draft-only type (27b S9). `trigger`, `script`, `rule`, `loop`, `join`, `wait`, `subworkflow`, `grader`, `monitor`, `llm` and `agent` become available in later PRs. `human_gate`, `rlm`, `app_op`, `library` and `claude_workflow` stay registered and unavailable, so a draft that uses one validates and a run refuses it with `kind_not_available`.
- [ ] In `folder.py`, load a workflow folder, resolve every `*_ref` inside it, refuse a ref that escapes the folder, and compute the content hash with `qmx_ledger.journal.fingerprint` over `nodes`, `connections`, `settings`, `inputs` and `outputs`, plus `sha256` of every ref file's bytes. `position` and `meta` are excluded.
- [ ] In `validate.py`, run SOLUTION-DESIGN section 2.4 steps 1 to 5 and return a list of `(code, path, message)`, never the first error alone. Roles resolve against a `[roles]` document passed in.
- [ ] In `lint.py`, refuse `settings.write`, trigger creation, a parameter naming a money act through `qma.core.barriers.money_path`, a literal of a token shape, a `broadcast` that carries a list into an `llm` or `agent` node (it must be `chunk`), an `agent` without `max_turns`, and a `human_gate` that is not in front of an `irreversible_external` effect. A missing runaway guard takes the defaults. No USD figure is ever required (ruling 27, 27b S3).
- [ ] In `overlay.py`, resolve `extends`, which names the parent's `workflow_item` and `object_id`, with the RFC 6902 operations `add`, `remove` and `replace` into a full snapshot, and record that parent pair.
- [ ] Add `python -m qmx_engine validate <folder>`, which prints the content hash or the error list.

**You see.**

- [ ] `python -m qmx_engine validate tests/fixtures/workflows/paper-scout-min` prints `ok sha256:<hex>`, and each bad fixture prints its codes.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_definition.py` gains cases for a cycle, an unknown kind, an unknown `typeVersion`, two triggers, an unreachable node, a keyed-join without a key, a cartesian edge without `explicit`, and a ref that escapes the folder, each with its literal code. `test_lint.py` gains one case per lint rule. `test_overlay.py` resolves a variant and checks the patched values. Run `uv run --no-sync python -m pytest tests -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Trunk has no validator, so record that. Run the harness diff check and validate the fixture at head. Save `ep3-regression.log`. Pass when the harness diff is empty and the fixture validates.
- [ ] Lane 2. Validate the fixture twice, then move every node's `position` and validate again. Save `ep3-hash.log`. Pass when all three hashes are equal and a one-byte edit to a prompt file changes the hash.
- [ ] Lane 3. Run `x03_validate.py` over the bad fixtures. Save `ep3-bad.log`. Pass when every fixture fails with its expected code and none passes.
- [ ] Lane 4. Validate a fixture whose `llm` node has a parameter `"action": "place_order"`. Save `ep3-money.log`. Pass when lint refuses it with the money code.
- [ ] Lane 5. Validate a fixture holding `sk-` followed by 40 characters in a parameter. Save `ep3-token.log`. Pass when lint refuses it and the log does not echo the literal.
- [ ] Lane 6. Resolve a variant over the fixture. Save `ep3-overlay.log`. Pass when the snapshot validates and records its parent.
- [ ] Lane 7. Validate a draft with a `note` node and an unconnected node. Save `ep3-draft.log`. Pass when the draft validates and the publish check refuses both.
- [ ] Lane 8. Validate the fixture against the exported JSON schema with `jsonschema`. Save `ep3-schema.log`. Pass when it validates.
- [ ] Lane 9. Validate a draft using `rlm`. Save `ep3-unavailable.log`. Pass when it validates and the registry reports the kind unavailable.
- [ ] Lane 10. Validate a fixture whose agent node takes a list through `broadcast`. Save `ep3-broadcast.log`. Pass when it fails with the chunk code, and the same fixture with `map: chunk` validates.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Validation time of a 50-node fixture in ms.
- [ ] Probe. One timed `validate` at head.
- [ ] Baseline. None, new at head. Record head only.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. EP3 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP3 on `engine/ep2`.

## Write the run ledger with one writer thread (EP4)

**Depends on.** EP3.

**Files.**

- [ ] Create `src/qmx_engine/ledger/store.py`, `events.py`, `memo.py`, `spans.py`, `signature.py`, `migrations.py`.
- [ ] Create `tests/test_ledger.py`, `tests/test_memo.py`, `tests/test_signature.py`.
- [ ] Create `scripts/live/engine/x04_ledger.py`.

**Build.**

- [ ] In `store.py`, open `<qmx_home>/engine/engine.sqlite` in WAL mode with one writer thread fed by a queue. Every append from any caller goes through the queue (AD-23). Readers open their own `mode=ro` connections. A second writer in another process is refused by a pid lock file next to the database.
- [ ] In `events.py`, define the event kinds and envelope of SOLUTION-DESIGN section 3.2, with `seq` monotonic per run and `at` taken from the recorded clock only.
- [ ] In `memo.py`, define the memo key of AD-7 `(run_id, node_id, iteration, partition_id, sha256(inputs), sha256(node_definition))` with `fingerprint`, plus `has`, `valid` and `invalidate_by_definition`.
- [ ] In `spans.py`, derive one span row per node attempt from `node_started` and its ending event, with every field of SOLUTION-DESIGN section 10.1.
- [ ] In `signature.py`, write `signature(code, message)` that replaces digits, UUIDs, hashes and paths before `sha256`.
- [ ] In `migrations.py`, keep a `schema_version` row and forward-only steps. Record `sqlite3.sqlite_version` in a `meta` row. On SQLite below 3.51.3 (the B1 WAL-reset floor), keep the single-writer layout and checkpoint only from the writer thread.

**You see.**

- [ ] `python -m qmx_engine ledger stats --home <home>` prints the schema version, the SQLite version and the event count.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_ledger.py` gains cases for contiguous `seq` under 8 threads, a refused second writer, and reopen after a closed writer. `test_memo.py` checks that a changed definition hash invalidates exactly its memo. `test_signature.py` checks that two messages differing only in a UUID and a path share a signature. Run `uv run --no-sync python -m pytest tests -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Trunk has no ledger, so record that. Run the harness diff check and `x04_ledger.py burst` at head. Save `ep4-regression.log`. Pass when the diff is empty and the burst passes.
- [ ] Lane 2. Run `x04_ledger.py burst`, 8 threads by 500 appends over 4 runs. Save `ep4-burst.log`. Pass when 4,000 events land, `seq` is contiguous per run, and no `database is locked` appears.
- [ ] Lane 3. Run `x04_ledger.py kill`, which kills the writer process mid-burst and reopens. Save `ep4-kill.log`. Pass when every committed event reads back, no partial event exists, and `seq` has no gap.
- [ ] Lane 4. Start a second writer process on the same file. Save `ep4-second-writer.log`. Pass when it is refused with a message naming the holder's pid, and a reader still reads.
- [ ] Lane 5. Make the database read-only and append. Save `ep4-write-error.log`. Pass when the caller gets `LedgerWriteError` and the writer thread stays alive.
- [ ] Lane 6. Run the migration twice on a fresh file. Save `ep4-migrate.log`. Pass when `schema_version` is 1 and the second run changes nothing.
- [ ] Lane 7. Append started and finished pairs for three attempts. Save `ep4-spans.log`. Pass when three span rows exist with durations.
- [ ] Lane 8. Compute the memo key for one input in two processes. Save `ep4-memo.log`. Pass when the keys are equal.
- [ ] Lane 9. Print `ledger stats`. Save `ep4-stats.log`. Pass when the SQLite version is shown.
- [ ] Lane 10. Read the database during a burst from a `mode=ro` connection. Save `ep4-reader.log`. Pass when reads never block the writer for more than 100 ms.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Append latency p95 in ms and burst wall time, at head. The ledger's speed is part of its point (Override 4).
- [ ] Probe. `x04_ledger.py burst` three times, reporting p95 and total.
- [ ] Baseline. Trunk has no ledger. The absolute budget is the baseline.
- [ ] Rule. Fail when the p95 append latency exceeds 20 ms or the 4,000-event burst exceeds 10 s on this PC.

**Review gate.** None. EP4 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP4 on `engine/ep3`.

## Write the pure orchestrator with node-level replay (EP5)

**Depends on.** EP4.

**Files.**

- [ ] Create `src/qmx_engine/core/state.py`, `fold.py`, `ready.py`, `commands.py`, `replay.py`, `simulate.py`.
- [ ] Create `src/qmx_engine/nodes/base.py`, `rule.py`, `trigger.py`.
- [ ] Create `tests/test_fold.py`, `tests/test_replay.py`, `tests/test_rule.py`.
- [ ] Create `scripts/live/engine/e01_determinism.py` and `e02_replay.py`.

**Build.**

- [ ] In `core`, write `fold(definition, events) -> State` and `next_commands(state) -> list[Command]`, pure, with the commands `StartNode`, `UseMemo`, `Wait`, `Pause`, `Finish` and `Park` (AD-1). Edge mapping `one` only. The run state is derived, never stored (SOLUTION-DESIGN section 3.1).
- [ ] In `replay.py`, return `UseMemo` for every node whose memo is valid and `StartNode` only for nodes without one. A downstream node reruns only when its own input hash changed (AD-7).
- [ ] In `nodes/base.py`, define `NodeJob` and `NodeResult` of SOLUTION-DESIGN section 5.1 and the `Executor` protocol `run(NodeJob) -> NodeResult`.
- [ ] In `nodes/rule.py`, evaluate a safe expression over inputs with an `ast` whitelist (no `eval`) and route to a named port. In `nodes/trigger.py`, mark the entry.
- [ ] In `simulate.py`, a synchronous in-memory driver for tests and the two live scripts, with injectable executors. The real runner arrives in EP7.

**You see.**

- [ ] `e02_replay.py` prints, for the resume, `started: n3 n4 n5` and `memo: n1 n2`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_fold.py` checks that folding one event list twice gives equal commands. `test_replay.py` covers the E2 case and a changed definition that reruns only nodes whose input hash changed. `test_rule.py` refuses `__import__`, attribute calls and lambdas. Run `uv run --no-sync python -m pytest tests -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Trunk has no core, so record that. Run the harness diff check and `e02_replay.py` at head. Save `ep5-regression.log`. Pass when the diff is empty and E2 passes.
- [ ] Lane 2. E1. Run `e01_determinism.py`, which folds one recorded event log in two processes. Save `ep5-e01.log`. Pass when the command lists are byte-equal.
- [ ] Lane 3. E2. Run `e02_replay.py` with a five-node chain that fails node 3, then resume. Save `ep5-e02.log`. Pass when nodes 1 and 2 get no new `node_started`, node 3 reruns, and nodes 4 and 5 run once.
- [ ] Lane 4. Edit node 4's prompt after a finished run and rerun. Save `ep5-edit.log`. Pass when only node 4 and the nodes whose input hash changed rerun.
- [ ] Lane 5. Route through a `rule` node on both branches. Save `ep5-rule.log`. Pass when only the chosen port's branch runs.
- [ ] Lane 6. Feed a rule expression that calls `open`. Save `ep5-rule-safe.log`. Pass when it is refused before evaluation.
- [ ] Lane 7. Run the AD-6 import rule over `core` at head. Save `ep5-pure.log`. Pass when it passes.
- [ ] Lane 8. Resume a finished run. Save `ep5-finished.log`. Pass when no executor is called.
- [ ] Lane 9. Feed the fold an event kind it does not know. Save `ep5-unknown-event.log`. Pass when it returns `Park` with a reason naming the kind.
- [ ] Lane 10. Run 200 nodes in a chain through `simulate`. Save `ep5-chain.log`. Pass when every node finishes once.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Fold time over 10,000 events in ms.
- [ ] Probe. One timed fold at head.
- [ ] Baseline. None, new at head. Record head only.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. EP5 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP5 on `engine/ep4`.

## Fan out by chunk, join, loop and wait (EP6)

**Depends on.** EP5.

**Files.**

- [ ] Create `src/qmx_engine/core/edges.py`, `partitions.py`, `joins.py`, `loops.py`, `waits.py`.
- [ ] Create `src/qmx_engine/nodes/join.py`, `loop.py`, `wait.py`.
- [ ] Create `tests/test_edges.py`, `tests/test_chunks.py`, `tests/test_joins.py`, `tests/test_loops.py`, `tests/test_waits.py`.
- [ ] Create `scripts/live/engine/e03_chunks.py` and `x06_joins_loops.py`.

**Build.**

- [ ] In `edges.py`, implement the maps `one`, `zip`, `broadcast`, `keyed-join` and `cartesian` (explicit only).
- [ ] In `partitions.py`, fan out by chunk (ruling 78, 27b B1). A `chunk` edge splits the item list. With `by: items`, each chunk holds `size` items, falling back to `chunk.size`. With `by: tokens`, a chunk fills to `fill` times the resolved model's context window, falling back to `chunk.fill`, so a 1M-token model takes about 300k tokens of items. One partition is one chunk, with its own memo. Partition ids are stable for the same item list.
- [ ] In `joins.py`, implement `all`, `any` and `quorum(n)`, with expected cardinality from the partition count, watermarks `all-expected`, `timeout` and `failed-aggregation`, and late arrivals recorded but not merged.
- [ ] In `loops.py`, iterate an induced body subgraph with typed stops `max_iterations`, `budget`, `predicate` and `no_progress_rounds`. Iteration state lives in the ledger.
- [ ] In `waits.py`, `wait` parks until a recorded `clock_tick` reaches `resume_at`, or until an `event_received` with the named event.

**You see.**

- [ ] `e03_chunks.py` prints `partitions=6 by=items size=10` and, after the resume, `new attempts=2`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_chunks.py` covers 60 items by 10, 61 items by 10 (7 chunks, last of 1), a token-capped chunk, and stable ids. `test_joins.py` covers `any` with late arrivals and `quorum(3)` of 5. `test_loops.py` covers each stop. `test_waits.py` covers a time wait under a recorded clock. Run `uv run --no-sync python -m pytest tests -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Trunk has no fan-out, so record that. Run the harness diff check and `e02_replay.py` from EP5 at head. Save `ep6-regression.log`. Pass when the diff is empty and E2 still passes.
- [ ] Lane 2. E3 and E29 by chunk. Run `e03_chunks.py` with 60 items, `by: items`, size 10, two chunks failing, then resume. Save `ep6-e03.log`. Pass when 6 attempts ran, not 60, exactly 2 new attempts run on resume, and the join output is ordered by partition id.
- [ ] Lane 3. Set `chunk.size` to 15 in the settings document and rerun the fan-out. Save `ep6-chunk-setting.log`. Pass when 4 partitions run.
- [ ] Lane 4. Run a `quorum(3)` join over 5 partitions with two slow ones. Save `ep6-quorum.log`. Pass when the join fires at 3 and the slow two are recorded `late`.
- [ ] Lane 5. Run an `any` join. Save `ep6-any.log`. Pass when it fires on the first and the rest are `late`.
- [ ] Lane 6. Run a loop with `no_progress_rounds=2` on a flat metric. Save `ep6-loop.log`. Pass when it stops after the second flat round.
- [ ] Lane 7. Run a `wait` of 30 s under a recorded clock, feeding two ticks. Save `ep6-wait.log`. Pass when it resumes on the tick past `resume_at` and not before.
- [ ] Lane 8. Run a cartesian edge of 3 by 4. Save `ep6-cartesian.log`. Pass when 12 partitions run, and an unmarked cartesian is refused at validation.
- [ ] Lane 9. Run a `keyed-join` on `paper_id`. Save `ep6-keyed.log`. Pass when pairs match by key and an unmatched key is reported.
- [ ] Lane 10. Run a 1,000-item list with `by: tokens` and `fill` 0.3 of a 200k window. Save `ep6-token-cap.log`. Pass when no chunk exceeds 60k estimated tokens and every item lands in exactly one chunk.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Partitioning time for 100,000 items in ms.
- [ ] Probe. One timed partition at head.
- [ ] Baseline. None, new at head. Record head only.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. EP6 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP6 on `engine/ep5`.

## Run nodes on the local worker with scripts, graders, monitors and subworkflows (EP7)

**Depends on.** EP6.

**Files.**

- [ ] Create `src/qmx_engine/runner.py` and `src/qmx_engine/workers/local.py`, `effects.py`.
- [ ] Create `src/qmx_engine/nodes/script.py`, `grader.py`, `monitor.py`, `subworkflow.py`.
- [ ] Create `tests/test_runner.py`, `tests/test_script.py`, `tests/test_effects.py`, `tests/test_monitor.py`, `tests/test_subworkflow.py`.
- [ ] Create `scripts/live/engine/e14_script_env.py`, `e04_unknown_outcome.py`, `x07_nodes.py`.

**Build.**

- [ ] In `runner.py`, drive the loop core commands, worker, ledger on one asyncio loop. Every result lands in the ledger before the core sees it. `python -m qmx_engine run <folder> --mode test|live --home <home>` starts one run from a folder.
- [ ] In `workers/local.py`, write the in-process `WorkerPort` with concurrency `placement.pc.concurrency`, heartbeats every 10 s while an attempt runs, and `cancel`.
- [ ] In `nodes/script.py`, run a declared script in a subprocess with an allow-listed env (no provider key, no `CLAUDE_CONFIG_DIR`, no plan path, AD-24), cwd in the run's write zone `workspaces/wf-<id>/runs/<run_id>/`, a timeout, and stdout JSON or files as outputs.
- [ ] In `effects.py`, snapshot the write zone before a `reversible` attempt and restore it before a retry. Give an `irreversible` attempt the key `run:node:iteration:attempt`. After an `unknown` effect state, an `irreversible_external` attempt never retries, waits for the inbox with the key shown, and raises one `irreversible_external` item. A model call with an unknown outcome is retried once and writes an `info` digest line, with no inbox item (AD-8, ruling 77).
- [ ] In `nodes/grader.py`, run a deterministic check script and route to `pass` or `fail` with `verdict` and `feedback`. In `nodes/monitor.py`, hash a cheap source and fire `changed` with the diff or end `silent`. In `nodes/subworkflow.py`, start a nested run with its own `run_id`, `parent_run_id` and `call_depth`, check `caller_policy`, and wait or continue.

**You see.**

- [ ] `python -m qmx_engine run tests/fixtures/workflows/script-chain --mode test` ends with `run finished` and the outputs hash.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_script.py` checks the env allow-list and the timeout. `test_effects.py` checks restore before retry and no retry after `unknown`. `test_monitor.py` checks `silent` on an unchanged hash. `test_subworkflow.py` checks the call-depth ceiling and a refused caller. Run `uv run --no-sync python -m pytest tests -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Trunk has no runner, so record that. Run the harness diff check and the `script-chain` fixture at head. Save `ep7-regression.log`. Pass when the diff is empty and the run finishes.
- [ ] Lane 2. E14. Run `e14_script_env.py`, a script node that prints its env, with a fake `ANTHROPIC_API_KEY` and `CLAUDE_CONFIG_DIR` set in the parent. Save `ep7-e14.log`. Pass when neither name nor any `qmx/` value nor the plan path appears in the output.
- [ ] Lane 3. E4 on an external step. Run `e04_unknown_outcome.py`, which kills the engine process while a script node marked `irreversible_external` runs, then restarts it. Save `ep7-e04.log`. Pass when no automatic retry happens and one `irreversible_external` inbox item carries the idempotency key.
- [ ] Lane 4. Run a monitor over an unchanged source twice. Save `ep7-monitor.log`. Pass when the second fire ends `silent` and no downstream node starts.
- [ ] Lane 5. Fail a `reversible` script that wrote a file, then retry. Save `ep7-snapshot.log`. Pass when the file from the failed attempt is gone before the retry.
- [ ] Lane 6. Run a subworkflow node. Save `ep7-subworkflow.log`. Pass when the child run has its own id and `parent_run_id`, and the parent continues on its output.
- [ ] Lane 7. Route a deterministic grader to `fail`. Save `ep7-grader.log`. Pass when only the `fail` branch runs and the span carries the verdict.
- [ ] Lane 8. Run 6 script nodes with concurrency 3. Save `ep7-concurrency.log`. Pass when at most 3 run at once.
- [ ] Lane 9. Cancel a running script. Save `ep7-cancel.log`. Pass when its process tree is gone within 5 s.
- [ ] Lane 10. Run a script that sleeps past its timeout. Save `ep7-timeout.log`. Pass when it fails with `signature=timeout` and `retryable=true`.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Engine overhead per script node in ms, minus the script's own time.
- [ ] Probe. Run 100 no-op script nodes once at head.
- [ ] Baseline. None, new at head. Record head only.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. EP7 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP7 on `engine/ep6`.

## Walk the failure ladder, watch runs and raise inbox items (EP8)

**Depends on.** EP7.

**Files.**

- [ ] Create `src/qmx_engine/core/ladder.py` and `src/qmx_engine/watchdog.py`.
- [ ] Create `src/qmx_engine/ports/inbox.py` and `src/qmx_engine/ledger/inbox_table.py`.
- [ ] Create `tests/test_ladder.py`, `tests/test_watchdog.py`, `tests/test_inbox.py`.
- [ ] Create `scripts/live/engine/e11_ladder.py`, `e12_inbox.py`, `x08_watchdog.py`.

**Build.**

- [ ] In `ladder.py`, walk SOLUTION-DESIGN section 10.2 in order. Retry uses the node's `retry` and backoff as a `waiting` with `resume_at`. The account step records `ladder_step account skipped: no pool` until the pool packet (L2). The model step takes the role's next candidate. The doctor step calls an injected doctor, a real `llm` node from EP10. Park ends the walk and the run ends `failed` with `reason: parked` (SOLUTION-DESIGN 3.1). A runaway-guard check runs before every step.
- [ ] In `watchdog.py`, run every tick at zero tokens. A stalled attempt is cancelled and fails `stalled`. A runaway-guard breach (tokens, agents, tool calls or wall time, never USD) follows the node's `on_runaway`. `pause` (the default) sets the run `waiting` with `reason: runaway` and writes an `info` digest line, and the run ends `stopped` with `reason: runaway` when the next occurrence starts, or resumes if he raises the guard. `degrade` switches to the cheapest candidates and continues once. Nothing asks him (ruling 27, AD-16). The same node failing twice with one signature skips to the doctor. A ledger write error stops claiming and raises a `system_fault` item.
- [ ] In `ports/inbox.py` and the table, hold one item per `(run_id, signature)` with `count`. Ruling 77 narrows the inbox to three categories in a closed enum, `provider_failure`, `system_fault` (harness-level and engine-level errors) and `irreversible_external`. A run parked for any other reason raises no item. Its state shows in `explain` and in the run list. Notifications stay UI-side.

**You see.**

- [ ] `e11_ladder.py` prints `ladder: retry retry model doctor park`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_ladder.py` checks the order, the skipped account step, and a runaway-guard breach between steps. `test_inbox.py` checks the dedupe and that a fourth category is a type error. `test_watchdog.py` checks each rule with a recorded clock. Run `uv run --no-sync python -m pytest tests -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Trunk has no ladder, so record that. Run the harness diff check and the EP7 `script-chain` fixture at head. Save `ep8-regression.log`. Pass when the diff is empty and the run finishes.
- [ ] Lane 2. E11. Run `e11_ladder.py` with a node that always fails retryably, two role candidates and a doctor stub. Save `ep8-e11.log`. Pass when the `ladder_step` events read retry, retry, account skipped, model, doctor, park, in that order.
- [ ] Lane 3. E12. Run `e12_inbox.py`, five failures of one provider signature. Save `ep8-e12.log`. Pass when one item exists with `count: 5` and category `provider_failure`.
- [ ] Lane 4. Park a run for a logic failure. Save `ep8-logic-park.log`. Pass when the run is `failed` with `reason: parked`, `explain` names the cause, and no inbox item exists.
- [ ] Lane 5. Run `x08_watchdog.py stalled`, an attempt with no heartbeat past its idle timeout. Save `ep8-stalled.log`. Pass when it is cancelled and fails `stalled`.
- [ ] Lane 6. Run `x08_watchdog.py runaway` with a guard of 2 agents. Save `ep8-runaway.log`. Pass when the third agent never starts, the run is `waiting(runaway)`, one `info` digest line exists, and no inbox item exists.
- [ ] Lane 7. Fail one node twice with one signature. Save `ep8-twice.log`. Pass when the second failure goes straight to the doctor step.
- [ ] Lane 8. Make the ledger read-only during a run. Save `ep8-ledger-fault.log`. Pass when a `system_fault` item exists and the scheduler stops claiming.
- [ ] Lane 9. Resolve an item with `retry`. Save `ep8-resolve.log`. Pass when the run gets a new attempt and the item records the principal.
- [ ] Lane 10. Run the ladder with the backoff 30, 120 and 600 s under a recorded clock. Save `ep8-backoff.log`. Pass when each retry's `resume_at` matches the backoff.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Watchdog tick time over 1,000 open attempts in ms.
- [ ] Probe. One timed tick at head.
- [ ] Baseline. None, new at head. Record head only.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. EP8 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP8 on `engine/ep7`.

## Serve drafts, tests, versions, runs and explain over the ports (EP9)

**Depends on.** EP8.

**Files.**

- [ ] Create `src/qmx_engine/ports/library.py`, `library_fake.py`, `memory.py`, `settings.py`, `clock.py`.
- [ ] Create `src/qmx_engine/service/drafts.py`, `tests.py`, `versions.py`, `runs.py`, `explain.py`, `inbox.py`, `registry.py`, `api.py`.
- [ ] Create `src/qmx_engine/trace_export.py`.
- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/service.py`, only the `SettingsSection` literal, to add `"engine"` and `"roles"`.
- [ ] Create `tests/test_service.py`, `tests/test_library_fake.py`, `tests/test_lifecycle.py`, `tests/test_explain.py`.
- [ ] Create `scripts/live/engine/e07_lifecycle.py`, `e10_library.py`, `x09_explain.py`.

**Build.**

- [ ] In `ports/library.py`, write the `LibraryPort` protocol of SOLUTION-DESIGN section 8.1, folded with `ENGINE-REQUESTS-ANSWERED.md`. A version maps to `(item_id, fields.semver, object_id)`, there is no `workflow_version` kind, and the kinds are `workflow`, `workflow-run`, `artifact` and `test-report` (27b S8). In `library_fake.py`, back it with one SQLite file `<qmx_home>/engine/library-fake.sqlite`. Drafts live on `refs/drafts/<item>`, and `main` holds published versions only (27b B4). A run's writes land on `refs/runs/<run_id>`. Edges come from the Library's closed set, where `replaces` is the one supersede relation, and nothing is ever deleted (AD-14).
- [ ] Give every run `mode: live | test`, fixed at birth, and a status from the one shared table of SOLUTION-DESIGN 3.1 (`queued | running | waiting | passed | failed | stopped | interrupted`, with `reason`). The engine and the Library use the same words, so there is no mapping layer. A workflow is tested when a `tested-by` edge points at a run with status `passed` in either mode for that object id. Triggers pin a published object, or its champion when `follow_champion` is set and the champion descends from it. They never run a draft (AD-10, AD-11).
- [ ] In `ports/memory.py`, write the `MemoryPort` stub. `snapshot` returns an empty snapshot, `recall`, `check_built` and `check_dead_end` return nothing, `note` stores a `run`-scope row in the fake, and `consolidate` is a no-op that logs.
- [ ] In `ports/settings.py`, read `[engine]` and `[roles]` through `ControlService.settings_get` over `settings.DEFAULTS`, never writing.
- [ ] In `service`, implement the AD-11 lifecycle `draft -> validated -> tested -> published -> enabled <-> disabled -> archived`. `runs.start` refuses a draft. `tests.run` runs a draft in test mode, writes a `test-report` bound to the content hash, and supports a selected subgraph. `versions.publish` merges the draft into `main` and writes the semver as a Library annotation. When the published object's `content_hash` equals the tested draft's, publish copies the `tested-by` edge onto it. A publish whose merge changed the hash needs a new test. Enabling is keyed on the `content_hash`, so it needs a passing run for that hash. An edit marks the report stale. Every call records `caller_kind user | agent | workflow`, mapped to the Library principals `operator`, `agent:<sid>` and `run:<run_id>` (27b S17).
- [ ] In `trace_export.py`, at run end write the span tree through `qmx_ledger.RunJournal` into an artifact, put it in the fake Library with `produced_by` and `run_of` edges, and write the run summary.
- [ ] In `explain.py`, return one document per run with each node's attempts, spans, ladder steps, waits, cost so far, and the reason it ended, parked or waits. Add `python -m qmx_engine explain <run_id>`.

**You see.**

- [ ] `python -m qmx_engine explain <run_id>` on a parked fixture run prints the node, the ladder steps and the park reason.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. 

- [ ] `test_lifecycle.py` walks every allowed transition and refuses each disallowed one. `test_library_fake.py` refuses an edge outside the set and any delete. `test_explain.py` checks the document's keys for a finished, a waiting and a parked run. Run `uv run --no-sync python -m pytest tests -q -n 2`, and the `qmx-control` suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run the harness diff check, and the `qmx-control` suite at base and head. Save `ep9-regression.log`. Pass when the harness diff is empty and the `qmx-control` pass counts match.
- [ ] Lane 2. E7. Run `e07_lifecycle.py`. Save `ep9-e07.log`. Pass when `runs.start` on a draft is refused, `tests.run` on it finishes on script nodes, and enable without a report for the hash is refused.
- [ ] Lane 3. E10. Run `e10_library.py` after a live run of the `script-chain` fixture. Save `ep9-e10.log`. Pass when the run summary, the trace artifact and the `run_of` and `produced_by` edges exist in the fake, and no `engine.sqlite` table holds the definition.
- [ ] Lane 4. Run `x09_explain.py` on a parked run. Save `ep9-explain.log`. Pass when the output names the node, every ladder step and the park reason.
- [ ] Lane 5. Edit a tested draft. Save `ep9-stale.log`. Pass when its report reads stale and publish is refused until a new test.
- [ ] Lane 6. Run a selected subgraph of two nodes on a draft. Save `ep9-subgraph.log`. Pass when only those two nodes run.
- [ ] Lane 7. Test a draft, publish it unchanged, then enable it. Save `ep9-publish-enable.log`. Pass when the published object carries the copied `tested-by` edge and enable succeeds with no new test. A second publish with the same hash creates nothing.
- [ ] Lane 8. Read `[roles]` from a home whose settings file has the section. Save `ep9-settings.log`. Pass when the values override the defaults and `settings_put` was never called.
- [ ] Lane 9. Archive a version with runs. Save `ep9-archive.log`. Pass when its runs and lineage stay readable.
- [ ] Lane 10. Pass a draft through test and publish, then read the fake's refs. Save `ep9-refs.log`. Pass when the draft sits on `refs/drafts/<item>`, the version on `main`, the test run carries `mode: test` with status `passed`, and the version reads as tested.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). `explain` time for a 200-node run in ms.
- [ ] Probe. One timed `explain` at head.
- [ ] Baseline. None, new at head. Record head only.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. EP9 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP9 on `engine/ep8`.

## Run llm nodes through Background chats and test on real models (EP10)

**Depends on.** EP9 and EP0.

**Files.**

- [ ] Create `src/qmx_engine/ports/harness_adapter.py`, `src/qmx_engine/roles.py`, `src/qmx_engine/admission.py`.
- [ ] Create `src/qmx_engine/nodes/llm.py`, `fake_provider.py`, `doctor.py`.
- [ ] Create `tests/test_roles.py`, `tests/test_admission.py`, `tests/test_llm.py`, `tests/test_harness_port.py`.
- [ ] Create `scripts/live/engine/e21_real_tests.py`, `e09_roles.py`, `x10_llm.py`.

**Build.**

- [ ] In `ports/harness_adapter.py`, wrap the public names only, including `Background`, `Child` and `ChatHooks` from `qma.harness` (HG1). `start_chat` uses `NewChat(title=<idempotency key>, profile, model, effort, workspace=workspaces/wf-<id>/, kind=Background())`. `send` always sends `InjectedText`. Turn end uses the detector `FINDINGS.md` chose. Every `permission` ask is answered `Reject("unattended run")` at once. `interrupt` and `usage` pass through. Appendix F lists how each harness behaviour is inherited.
- [ ] In `roles.py`, resolve a role from `[roles]` to an ordered list of `(profile, model, effort, context_window, test_only)`. Test mode prefers the cheap end and admits `test_only` rows. Live mode skips them. The defaults are in Appendix H.
- [ ] In `admission.py`, count the engine's own live chats against `max_live_chats - limits.interactive_reserve`, read `Harness.usage()`, and map a `LaunchRefused` for a share or a stop to `waiting(limit, resume_at)` with the reset time EP0 found. There is no fixed background cap in engine code (ruling 90). The engine reads each account's `pool.accounts.<account>.background_share` from `SettingsPort`, Claude's default 0.5, and parks a node as `waiting(limit)` when that account's background use reaches its share. Until the pool packet (L2), the one plan account's share is the harness's `[budgets] background_cap`, read and never edited, and Settings edits it. The strategy, ceiling and cooldown settings of Appendix H are read here too, and with one account they change nothing yet. A chat that ends on the harness's per-chat `max_budget_usd` becomes `waiting(runaway)`, not a failure (27b S4). Nothing asks the operator (ruling 27).
- [ ] In `nodes/llm.py`, run one turn on a tool-less brief in a Background chat. Validate the final text against the node's JSON schema with `jsonschema`. On failure, send one repair turn in the same chat, then fail `bad_output`. Read tokens, cache read and cache write from the chat's journal rows into the span.
- [ ] In `nodes/fake_provider.py`, return pinned data, a recorded transcript or a schema-valid canned document, chosen by an explicit per-run switch. In `doctor.py`, make the ladder's doctor an `llm` call on the `doctor` role.

**You see.**

- [ ] `python -m qmx_engine run tests/fixtures/workflows/one-llm --mode test --home <home>` ends `run finished` and its span names the resolved profile and model.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_roles.py` covers test mode admitting `test_only` rows and live mode skipping them. `test_admission.py` covers the reserve arithmetic, the mapping of a refusal to `waiting`, and a share read from settings at 0.5 and at 0.9 that parks at each value. `test_llm.py` covers the repair turn with a fake port. `test_harness_port.py` checks that no prompt goes out as `OperatorText`. Run `uv run --no-sync python -m pytest tests -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run the harness diff check and the `qma-harness` suite at base and head. Save `ep10-regression.log`. Pass when the diff is empty and the pass counts match.
- [ ] Lane 2. E21. Run `e21_real_tests.py` on a throwaway home with the OpenRouter row. Save `ep10-e21.log`. Pass when the draft test run resolves a cheap OpenRouter model, writes on `refs/runs/<id>` with status `test`, and a rerun with the fake switch leaves the relay journal unchanged.
- [ ] Lane 3. E9. Run `e09_roles.py` with `writer` listing the OpenRouter row first and a plan-profile candidate second, then mark the first row unavailable. Save `ep10-e09.log`. Pass when the first span records OpenRouter and the next run records the plan-profile candidate.
- [ ] Lane 4. Run `x10_llm.py schema`, an `llm` node whose first answer is forced invalid by the prompt. Save `ep10-repair.log`. Pass when one repair turn runs in the same chat and the output validates.
- [ ] Lane 5. Run `x10_llm.py cache`, two `llm` nodes with one shared static brief. Save `ep10-cache.log`. Pass when the second span shows cache read tokens above 0.
- [ ] Lane 6. Run `x10_llm.py ask`, a prompt that makes the model try a write. Save `ep10-ask.log`. Pass when the ask is rejected within 2 s and the span records it.
- [ ] Lane 7. Run `x10_llm.py doctor` with a node forced to `bad_output` twice. Save `ep10-doctor.log`. Pass when a `doctor_verdict` event names a class and the ladder continues per it.
- [ ] Lane 8. Run 6 `llm` nodes with `max_live_chats` 4 and reserve 2. Save `ep10-reserve.log`. Pass when at most 2 engine chats are live at once and no `ChatTableFull` appears.
- [ ] Lane 9. Read the chat records the run made. Save `ep10-records.log`. Pass when every engine chat is `background` and its title is the attempt's idempotency key.
- [ ] Lane 10. Check money posture after the lanes. Save `ep10-money.log`. Pass when `GET /api/usage` money fields and the broker inventory are unchanged from before.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Engine overhead around one `llm` turn in ms, from send to span written, minus the model time.
- [ ] Probe. Five `llm` nodes on the `triage` role's test candidate at head.
- [ ] Baseline. None, new at head. Record head only.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. EP10 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP10 on `engine/ep9`.

## Run agent nodes by chunk and pause at limits (EP11)

**Depends on.** EP10, and EP1's findings read before building (27b N4).

**Files.**

- [ ] Create `src/qmx_engine/nodes/agent.py` and `src/qmx_engine/prompts.py`.
- [ ] Edit `src/qmx_engine/admission.py` and `src/qmx_engine/runner.py` for drain and pause.
- [ ] Create `tests/test_agent.py`, `tests/test_drain.py`, `tests/test_prompts.py`.
- [ ] Create `scripts/live/engine/x11_agent_chunks.py`, `e05_pause.py`, `e04b_agent_unknown.py`.

**Build.**

- [ ] In `nodes/agent.py`, run a Background chat per chunk with the node's brief, its skills and its tool list stated in the prompt, the session id saved on `node_started` for resume, and the write zone named. Asks are rejected, so agent nodes read and answer but write nothing on the host until the sandbox packet (L6). The final answer is validated like an `llm` node's. The node's turn cap is the harness's global Background `max_turns` until H2. The engine enforces the node's run and idle timeouts through `Harness.interrupt`.
- [ ] In `prompts.py`, lay out every model prompt for the cache. The static brief, schema and rules come first and are byte-stable across chunks. The chunk data comes last. Recalled text arrives only as a fenced block (AD-18).
- [ ] Apply AD-34 (ruling 78) through HG1's real APIs. Every agent chat starts with `NewChat(compact_at=agent.compact_at)` (0.40 of the window, H15), on plan and key rows alike. Its `ChatHooks.pre_compact` callback writes the working state with `memory_note` before the CLI compacts (H16). Every compaction becomes a span event `compacted{trigger: threshold | auto | restart, at_fraction}`.
  - [ ] Keep AD-34's fallback as safety only. When the harness refuses `compact_at`, or context passes `agent.compact_at` plus 0.05 with no `compacted` event, the engine injects one instruction to `memory_note` the working state and summarise, then continues the same attempt in a fresh Background chat seeded with that summary, with the same memo key, and writes an `info` digest line naming the fallback.
- [ ] Record each tool call as a child span (`kind: tool`, name, duration, error) live from `ChatHooks.post_tool_use` (H16), and record Stop and SubagentStop from their hooks. The `tool` blocks the harness writes after each turn stay as safety only. The engine reconciles them at turn end and adds a span for any tool call no hook reported. Interrupt the attempt when its tool calls pass `agent.max_tool_calls` and set the run `waiting(runaway)`.
- [ ] All chunks of one node in one run use one profile and model, so chunk 2 onward reads the cache. Per-account lease affinity arrives with the pool (L2).
- [ ] Implement AD-9 drain and pause. A closed admission puts the node in `waiting(limit, resume_at)`. No new model node starts, scripts and rules continue, and the run emits `run_paused` when nothing runs. The runner's own timer wakes it at `resume_at` plus `limits.slack`. The scheduler takes this over in EP12. A `rate_limit` inside a running node marks the attempt `waiting`, not failed.
- [ ] A worker death during an `agent` or `llm` attempt records `effect_state: unknown`. The engine retries that model call once with a new attempt and writes an `info` digest line with the idempotency key. No inbox item is raised (AD-8, ruling 77).
- [ ] Refuse `agent_mode: cli_inside` and `agent_mode: host_harness` at dispatch with `mode_not_available` until H11 is granted. In those modes keys come only from the relay through the run pass, never from egress injection, so nothing schedules them before H11 (SOLUTION-DESIGN 5.4).

**You see.**

- [ ] `x11_agent_chunks.py` prints `chunks=3 chats=3 joined=30` and each span's model and cache read count.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_prompts.py` checks that two chunks' prompts share a byte-identical prefix. `test_drain.py` checks that scripts continue and no model node starts while the run drains. `test_agent.py` checks the session id is recorded and reused on resume, that every agent chat passes `compact_at` and `ChatHooks`, and, with a fake port that refuses `compact_at`, that the restart fallback runs. Run `uv run --no-sync python -m pytest tests -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run the harness diff check and EP10's `e21_real_tests.py` at head. Save `ep11-regression.log`. Pass when the diff is empty and E21 still passes.
- [ ] Lane 2. E29 and E30. Run `x11_agent_chunks.py` with 30 items, `by: items`, size 10, on the `reader` role's first plan-profile candidate. Save `ep11-chunks.log`. Pass when 3 Background chats run, the join holds 30 results, and chunks 2 and 3 show cache read tokens above 0.
- [ ] Lane 3. E5. Run `e05_pause.py` on a throwaway home with the fake model, feeding a rejected five-hour reading, then a reset. Save `ep11-e05.log`. Pass when the next model node goes `waiting` with `resume_at`, no `needs_you` block appears, and the run resumes alone after the reset.
- [ ] Lane 4. E4 on an agent. Run `e04b_agent_unknown.py`, which kills the engine mid agent call and restarts. Save `ep11-e04.log`. Pass when the call is retried exactly once, one `info` digest line carries the idempotency key, and no inbox item exists.
- [ ] Lane 5. Run a chunked fan-out of 6 with reserve 2 and `max_live_chats` 4. Save `ep11-width.log`. Pass when at most 2 engine chats are live at once.
- [ ] Lane 6. Resume an interrupted agent attempt. Save `ep11-resume.log`. Pass when the chat resumes on its saved session id.
- [ ] Lane 7. Give an agent node a 60 s run timeout and a task that runs longer. Save `ep11-timeout.log`. Pass when the engine interrupts it and records `timeout`.
- [ ] Lane 8. Run a drain with one script node and one model node waiting. Save `ep11-drain.log`. Pass when the script finishes and the model node does not start.
- [ ] Lane 9. Ask an agent node to write a file. Save `ep11-readonly.log`. Pass when the ask is rejected and no file appears in the workspace.
- [ ] Lane 10. E31 on HG1's APIs. Run one plan-profile agent chunk with a long enough input to cross `agent.compact_at`. Save `ep11-compact.log`. Pass when the span shows a `compacted` event with `trigger: auto`, a `memory_note` row written by the PreCompact hook before it, and tool-call child spans that arrived from PostToolUse before the turn ended.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Cache read share of input tokens across the three chunks.
- [ ] Probe. Lane 2's spans.
- [ ] Baseline. Chunk 1's share, which has no cache to read.
- [ ] Rule. No fail rule. A share below 30% on chunks 2 and 3 is logged as a low finding.

**Review gate.** None. EP11 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP11 on `engine/ep10`.

## Fire triggers at most once with one catch-up (EP12)

**Depends on.** EP11.

**Files.**

- [ ] Create `src/qmx_engine/triggers/rows.py`, `ticker.py`, `claims.py`, `catchup.py`, `preflight.py`, `quota.py`, `cron.py`.
- [ ] Create `tests/test_triggers.py`, `tests/test_claims.py`, `tests/test_catchup.py`, `tests/test_cron.py`.
- [ ] Create `scripts/live/engine/e06_catchup.py` and `x12_scheduler.py`.
- [ ] Edit `qmx-agents/uv.lock` and the engine's `pyproject.toml` only if a cron library is added.

**Build.**

- [ ] In `rows.py`, store trigger and fire rows of SOLUTION-DESIGN section 4.1 in `engine.sqlite` under the one writer. Each trigger names one `home_engine` (`pc | contabo`), and this instance claims only rows whose home is `pc` (AD-3). Kinds tonight are `cron` with an IANA zone, `interval`, `manual` and `after`. `event` and `webhook` stay later (L5).
- [ ] In `cron.py`, parse five-field cron with `zoneinfo`. Prefer a small pinned library such as `cronsim`, recorded with its version, over a hand parser.
- [ ] In `ticker.py` and `claims.py`, tick every `scheduler.tick`, claim each due occurrence with a lease and heartbeat, and skip an occurrence another claimant holds.
- [ ] In `catchup.py`, collapse occurrences older than `scheduler.grace` into one fire for the latest and record the rest `skipped: downtime` (ruling 54).
- [ ] In `quota.py`, park a fire into a closed window with `quota_hold_until` and merge later fires into it.
- [ ] In `preflight.py`, check that roles, credential refs (by name), skills and the delivery target resolve. A failure sets `blocked_config` and starts no run. A failure in the workflow's own config, such as a missing role or skill, writes a digest line. Only a provider failure raises a `provider_failure` item (AD-10, AD-17).
- [ ] Run a `monitor` precheck before the run. An unchanged hash ends the fire `silent`. Inject the trigger's last successful outputs when `continuity` is on. Hold `max_concurrent`. Refuse trigger creation from `caller_kind: workflow`.
- [ ] Move EP11's resume timer into the ticker.

**You see.**

- [ ] `python -m qmx_engine triggers list --home <home>` shows each trigger's `next_fire_at` and `last_status`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_cron.py` covers a DST change in `Europe/London`. `test_claims.py` covers two claimants on one occurrence. `test_catchup.py` covers four missed occurrences. `test_triggers.py` covers the refused workflow caller. Run `uv run --no-sync python -m pytest tests -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run the harness diff check and EP11's `e05_pause.py` at head, now woken by the ticker. Save `ep12-regression.log`. Pass when the diff is empty and the run resumes alone.
- [ ] Lane 2. E6. Run `e06_catchup.py`, which stops the engine across 4 cron occurrences under an injected clock and restarts. Save `ep12-e06.log`. Pass when exactly one fire runs and three are recorded `skipped: downtime`.
- [ ] Lane 3. Run two engine processes' tickers on one ledger copy pointed at one SQLite file through the writer lock. Save `ep12-claims.log`. Pass when every occurrence has one fire.
- [ ] Lane 4. Fire a trigger whose role is missing. Save `ep12-preflight.log`. Pass when it ends `blocked_config` with one digest line, no inbox item and no run.
- [ ] Lane 5. Fire into a closed window, then fire again. Save `ep12-quota.log`. Pass when one held fire carries both and runs once after the reset.
- [ ] Lane 6. Fire a trigger whose monitor source is unchanged. Save `ep12-silent.log`. Pass when the fire ends `silent` and no run starts.
- [ ] Lane 7. Finish a run of workflow A with an `after` trigger on B. Save `ep12-after.log`. Pass when B runs once with A's outputs.
- [ ] Lane 8. Call trigger creation as `caller_kind: workflow`. Save `ep12-refused.log`. Pass when it is refused.
- [ ] Lane 9. Run an `interval` trigger of 60 s for 5 minutes. Save `ep12-interval.log`. Pass when 5 fires run and none overlaps with `max_concurrent` 1.
- [ ] Lane 10. Turn `continuity` on and fire twice. Save `ep12-continuity.log`. Pass when the second run's inputs hold the first run's outputs.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Tick time with 500 enabled triggers, at head. The tick's cost matters because it runs every minute forever (Override 4).
- [ ] Probe. Ten ticks over a seeded table of 500 triggers.
- [ ] Baseline. Trunk has no scheduler. The absolute budget is the baseline.
- [ ] Rule. Fail when a tick over 500 triggers takes more than 1 s on this PC.

**Review gate.** None. EP12 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP12 on `engine/ep11`.

## Wire the ControlService doors and the engine host (EP13)

**Depends on.** EP12.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/service.py`, only `workflows_get`, `workflows_put`, `workflows_validate`, `workflows_run`, the `workflow_*` stubs HG1 added, and a new `attach_workflow_engine`.
- [ ] Create `qmx-agents/packages/qmx-control/tests/test_workflow_engine_door.py`.
- [ ] Create `src/qmx_engine/host.py`, `src/qmx_engine/service/rest.py`, `src/qmx_engine/control_door.py`.
- [ ] Create `tests/test_host.py`, `tests/test_rest.py`.
- [ ] Create `scripts/live/engine/x13_doors.py`.

**Build.**

- [ ] In `qmx_control/service.py`, add a `WorkflowEngine` Protocol and `attach_workflow_engine(engine)`. The four `workflows_*` methods and HG1's `workflow_*` stubs call the attached engine and keep their 501 when none is attached. Per SOLUTION-DESIGN 13, `workflows_put` is re-scoped to publish only and `workflows_run` to live runs only. Both stay MANAGE and ask him once. `workflows_get` and `workflows_validate` stay READ. `qmx-control` never imports `qmx_engine`. `runs_*`, `run_job` and `jobs_*` stay the remote-compute doors they are today (27b S16).
- [ ] In `control_door.py`, implement that Protocol over `qmx_engine.service`. Engine runs live in `engine.sqlite` and the `/api/workflow-runs` routes, not in `runs.db`. The copilot reaches the engine through HG1's `workflow_*` tool rows (H17). `workflow_drafts_put` and `workflow_tests_run` never ask him, and publish and a live run ask once.
- [ ] Keep H17's fallback from SOLUTION-DESIGN 13 as safety only. A draft the copilot saves with the existing `library_save` (DOMAIN_WRITE) as a `workflow` object is still picked up. The engine subscribes to `ControlService`'s `library` events, imports a changed `workflow` draft into `refs/drafts/<item>`, and starts a test run when its `meta.test_requested` nonce changed. Neither step asks him.
- [ ] In `service/rest.py`, add a router for the REST paths of SOLUTION-DESIGN 13 that `OPERATIONS` still lacks after HG1. They are the UI-only `/api/inbox/{id}/resolve` and `/api/engine/events` as SSE. The paths HG1 added to `OPERATIONS` reach the engine through `attach_workflow_engine`. The router is never added to `qmx_control.server.OPERATIONS`, because the harness's `test_tools.py` checks that list against its own tool table.
- [ ] In `host.py`, write the interim composition root (Appendix F, AD-3). HG1 grants H0's exports, but H0 does not make `qma.serve` compose the engine, so the host stays until L1. It runs the `qma.boot` scrub first, opens `QmxHome`, a `ControlService`, `Harness.open`, the engine and its ticker task group, attaches the engine, and serves `create_app(control, local_token(), ui_origin, extra_routers=[engine_router])` with uvicorn. It refuses to start when the home's `control-process.json` records a live host. `python -m qmx_engine.host serve --home <home> --port <port>`.

**You see.**

- [ ] `POST /api/workflows/validate` on the engine host returns the engine's result, and `GET /api/workflow-runs` lists the workflow run.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_workflow_engine_door.py` checks the 501 without an engine and the delegation with a stub. `test_rest.py` drives the router with FastAPI's test client. `test_host.py` checks the refusal on a recorded host. Run the `qmx-engine` and `qmx-control` suites with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run the harness diff check and the `qma-harness` suite at base and head, which includes `test_tools.py`. Save `ep13-regression.log`. Pass when the diff is empty and the pass counts match.
- [ ] Lane 2. Start `qmx_engine.host` on a throwaway home and run `x13_doors.py rest`, which saves a draft, validates, tests, publishes and live-runs the `script-chain` fixture over REST. Save `ep13-rest.log`. Pass when each call returns the engine's document and the run finishes.
- [ ] Lane 3. Run `x13_doors.py tools`, which calls `workflow_drafts_put` and `workflow_tests_run` through the `/mcp` door, then `workflows_put` to publish. Save `ep13-tools.log`. Pass when the draft saves and the test run starts with no ask, publish raises exactly one ask, and each tool returns the engine's result. Then run `x13_doors.py fallback`, which saves a `workflow` draft with `library_save` and a new `meta.test_requested`, and pass when a test run still starts on its own.
- [ ] Lane 4. Start a run with a `wait` node and cancel it through `POST /api/workflow-runs/{id}/cancel`. Save `ep13-cancel.log`. Pass when the engine run ends `cancelled`, and `GET /api/runs` still lists only remote runs.
- [ ] Lane 5. Start plain `qma.serve` on another throwaway home and call `PUT /api/workflows/x`. Save `ep13-501.log`. Pass when it still returns 501.
- [ ] Lane 6. Call `GET /api/workflow-runs/{id}/explain`. Save `ep13-explain.log`. Pass when it matches the CLI's `explain` for the same run.
- [ ] Lane 7. Start a second host on the same home. Save `ep13-second-host.log`. Pass when it refuses and names the recorded pid.
- [ ] Lane 8. Subscribe to `/api/engine/events` during a run. Save `ep13-events.log`. Pass when node events arrive in `seq` order.
- [ ] Lane 9. Call `/api/workflow-runs` and `/api/triggers` without the bearer. Save `ep13-auth.log`. Pass when it returns 401.
- [ ] Lane 10. Resume a `failed` (parked) engine run through `POST /api/workflow-runs/{id}/resume`. Save `ep13-resume.log`. Pass when the run gets a new attempt and the remote runtime was never called.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Host start time to a healthy `/api/health` in s.
- [ ] Probe. Three starts at head.
- [ ] Baseline. `qma.serve` start time on the same home, measured first.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. EP13 is not review-gated.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP13 on `engine/ep12`.

## Rerun every engine check and show the engine working (EP14)

**Depends on.** EP13.

**Files.**

- [ ] Create `scripts/live/engine/run_all.py` and `scripts/live/engine/test_run_all.py`.
- [ ] Create `qmx-agents/packages/qmx-engine/docs/ENGINE-NOTES.md`.
- [ ] Create `qmx-agents/packages/qmx-engine/examples/hello-chunks/` (a definition, a fetch script with fixtures, one chunked agent node, a grader).

**Build.**

- [ ] Write `run_all.py`. It runs every `e*.py` and `x*.py` check in plan order and prints one PASS or FAIL table with the evidence path of each.
- [ ] Write `ENGINE-NOTES.md` with the `run_all.py` table, the departures in Appendix F, each H-request with HG1's API in use or the fallback in use, and how to start the host.
- [ ] Run full `just ci` once under the CI lock and attach its summary.

**You see.**

- [ ] `run_all.py` prints 0 FAIL, and `hello-chunks` shows a finished run with three chunk spans in `explain`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_run_all.py` gains a case that one failing check makes `run_all.py` exit non-zero and name it. Run `uv run --no-sync python -m pytest scripts/live/engine/test_run_all.py -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run full `just ci` at `engine/base` and at head. Save `ep14-regression.log`. Pass when head fails nothing that base passes.
- [ ] Lane 2. Run `run_all.py`. Save `ep14-run-all.log`. Pass when it prints 0 FAIL.
- [ ] Lane 3. Run `hello-chunks` in test mode on the host, then publish it, add a disabled cron trigger, and enable it. Save `ep14-hello.png`. Pass when enable succeeds only after the test report, and the screen shows the run card from `explain`.
- [ ] Lane 4. Run `hello-chunks` live once through `run_now`, kill the host mid-run, restart, and resume. Save `ep14-resume.log`. Pass when finished chunks are not re-run and the run finishes.
- [ ] Lane 5. Read `ENGINE-NOTES.md` against Appendix F. Save `ep14-notes.log`. Pass when every departure and H-request appears.
- [ ] Lane 6. Hash `qmx-agents/packages/qma-harness/` at `engine/hg1` and head. Save `ep14-harness-hash.log`. Pass when the hashes match.
- [ ] Lane 7. Grep the engine source for any money verb and any broker import. Save `ep14-money.log`. Pass when none is found outside the lint's deny list reference.
- [ ] Lane 8. Count plan-profile turns and OpenRouter calls the program used, from the journals. Save `ep14-usage.log`. Pass when both are recorded for Appendix E.
- [ ] Lane 9. Run `tools/secret_scan.py` and the money path scan. Save `ep14-scans.log`. Pass when both are clean.
- [ ] Lane 10. Start `qma.serve` on the ship home after the host stops. Save `ep14-qma-serve.log`. Pass when the harness host still starts and `/api/doctor` shows no new failure.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of `run_all.py`.
- [ ] Probe. One run at head.
- [ ] Baseline. None, new at head. Record head only.
- [ ] Rule. Fail when it exceeds 90 minutes, so a rerun fits one plan window.

**Review gate.** The operator reviews before landing.

- [ ] Copy the lane 3 screenshot and a screen of the `run_all.py` table into `D:/QMX-worktrees/qma-ship/engine/review/EP14-review-<slug>.png`.
- [ ] Record a 30 to 60 second video of `hello-chunks` running, being killed and resuming, with `ffmpeg -f gdigrab`. Save it as `D:/QMX-worktrees/qma-ship/engine/review/EP14-review.mp4`.
- [ ] Post the screenshots, the video and `ENGINE-NOTES.md` in chat for the operator at the end of the run. Track T continues meanwhile, because nothing merges.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends EP14 on `engine/ep13`. The operator lands Track E bottom-up after his review.

## Seat the template pack and ship RS1 and T3 (TP1)

**Depends on.** EP14.

**Files.**

- [ ] Create `src/qmx_engine/templates/catalog.py` and `install.py`.
- [ ] Create the shared blocks `src/qmx_engine/templates/_shared/render-and-grade/`, `preflight/`, `research-harness/` and `paper-read/` as workflow folders.
- [ ] Create `src/qmx_engine/templates/rs1-paper-scout/` and `t3-news-calendar-watch/`, each with `definition.json`, `prompts/`, `schemas/`, `scripts/`, `fixtures/` and `README.md`.
- [ ] Create `tests/test_templates.py`.
- [ ] Create `scripts/live/engine/t_templates.py`.

**Build.**

- [ ] In `catalog.py`, list all 31 templates of `19-centralized-design.md` section 7 with their id, plain name (ruling 35), source card in files 15, 16 or 17, and `needs`, from Appendix I.
- [ ] Add `meta.needs` to the format. A template with `needs` validates and stays a draft. Its test run and its enable are refused with the need named, for example `needs: trading-node`.
- [ ] In `install.py`, install the pack disabled. A runnable template is tested on real models, published at `0.1.0`, and given its triggers from the card, disabled. A `needs` template is saved as a validated draft. Install is idempotent by content hash. `python -m qmx_engine templates install --home <home>`.
- [ ] Write the shared blocks. `render-and-grade` checks the output JSON and its numbers with a schema and a script. `preflight` is the zero-token pre-check. `research-harness` is a chunked agent fan-out with a synthesiser and a citation grader. `paper-read` is one batched question battery per paper chunk.
- [ ] Build RS1 from card R1 in file 15. Fetching is a `script` node, never a model tool, so tests pin it from `fixtures/` and the arXiv rate rule lives in the script. Triage is an `llm` node, reading is a chunked `agent` node, then the citation grader and `render-and-grade`. Every step from the card that needs an out-of-scope piece is left out and listed in `README.md`.
- [ ] Build T3 from card T3 in file 16, script-first, with a static watchlist `EURUSD, USDJPY` in place of active units and the guard cross-check marked `could not check: trading node`.
- [ ] Each template's prompts are short, specific and ship-ready (ruling 83). Roles are named, never models (AD-13).

**You see.**

- [ ] `python -m qmx_engine templates list --home <home>` shows 31 rows, RS1 and T3 `published, disabled`, and 29 `not yet built`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_templates.py` validates every folder in the pack, checks that every catalog row names a source card, and checks that install is idempotent with the fake provider. Run `uv run --no-sync python -m pytest tests -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run EP14's `run_all.py` at head. Save `tp1-regression.log`. Pass when it prints 0 FAIL and the harness diff is empty.
- [ ] Lane 2. Run `t_templates.py rs1` on real models through each role's test candidates. Save `tp1-rs1.log`. Pass when the test run passes, the report binds to the hash, and the note validates against its schema.
- [ ] Lane 3. Run `t_templates.py t3`. Save `tp1-t3.log`. Pass when the test run passes and makes zero model calls on a day with no surprise in the fixture.
- [ ] Lane 4. Run `templates install` twice on a throwaway home. Save `tp1-install.log`. Pass when both templates are published and disabled after the first run, and the second run changes nothing.
- [ ] Lane 5. Run RS1's fetch script live once, outside test mode. Save `tp1-rs1-fetch.log`. Pass when it returns new ids and keeps one request per 3 s.
- [ ] Lane 6. Try to enable RS1 after editing its prompt. Save `tp1-stale.log`. Pass when enable is refused until a new test.
- [ ] Lane 7. Read RS1's spans. Save `tp1-rs1-spans.log`. Pass when reader chunks show cache read tokens and the run stays inside its budget.
- [ ] Lane 8. Validate a copy of RS1 with a `needs` entry. Save `tp1-needs.log`. Pass when its test run is refused with the need named.
- [ ] Lane 9. Read both templates' prompts and outputs for plain names and a clear result. Save `tp1-read.log`. Pass when each output reads as finished work, not a placeholder.
- [ ] Lane 10. Run RS1 with the fake switch. Save `tp1-fake.log`. Pass when no provider is called and the run passes.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Tokens and wall time of each template's test run.
- [ ] Probe. Lanes 2 and 3.
- [ ] Baseline. None, new at head. Record head only.
- [ ] Rule. No fail rule. Recorded in the catalog row as the template's test cost.

**Review gate.** None. TP1 is not review-gated. TP4 carries the pack's review.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends TP1 on `engine/ep14`.

## Ship the research templates RS0, RS2, RS4, A and RV (TP2)

**Depends on.** TP1.

**Files.**

- [ ] Create `src/qmx_engine/templates/rs0-idea-grill/`, `rs2-source-to-component-card/`, `rs4-literature-review/`, `a-fill-the-library/` and `rv-weekly-review/`, each in the TP1 folder shape.
- [ ] Create `src/qmx_engine/templates/_shared/understand-extract/` and `calibrate/`.
- [ ] Edit `src/qmx_engine/templates/catalog.py` and `tests/test_templates.py`.

**Build.**

- [ ] Build RS0 from card R0, RS2 from R2 with R5, RS4 from R4, A from funnel stages 1 to 7 in file 19 section 7, and RV from R9 with D10. Each takes its steps from its card and leaves out what needs an out-of-scope piece, listed in its `README.md`.
- [ ] Fetching and transcripts are `script` nodes. Transcripts use `yt-dlp` captions only. Whisper needs a key and stays out.
- [ ] Questions that cards route to the operator become recorded assumptions in the output, because nothing waits for him (rulings 57 and 77).
- [ ] A writes its cards as run artifacts through the run-end export into the Library port. No `library` node is used.
- [ ] RV reads the engine's own runs and inbox through `service`, not the Library.

**You see.**

- [ ] `templates list` shows 7 templates `published, disabled`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_templates.py` gains validation and fake-provider install cases for the five templates. Run `uv run --no-sync python -m pytest tests -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run `t_templates.py rs1 t3` at head. Save `tp2-regression.log`. Pass when both still pass.
- [ ] Lane 2. Run `t_templates.py rs4` on real models. Save `tp2-rs4.log`. Pass when the chunked searchers, synthesiser and citation grader all run and the review validates.
- [ ] Lane 3. Run `t_templates.py a` on a fixture of one video transcript. Save `tp2-a.log`. Pass when the cards land as run artifacts with `produced_by` edges.
- [ ] Lane 4. Run `templates install` on a throwaway home. Save `tp2-install.log`. Pass when all seven runnable templates are published and disabled.
- [ ] Lane 5. Run `t_templates.py rs0`. Save `tp2-rs0.log`. Pass when the term sheet validates and lists its assumptions.
- [ ] Lane 6. Run `t_templates.py rs2`. Save `tp2-rs2.log`. Pass when the component card validates with its holes kept.
- [ ] Lane 7. Run `t_templates.py rv` after the other lanes. Save `tp2-rv.log`. Pass when the review names the week's runs and parked items.
- [ ] Lane 8. Run RS4 with a 200-item source list. Save `tp2-rs4-chunks.log`. Pass when the items split into chunks by the setting and none is dropped.
- [ ] Lane 9. Read each output. Save `tp2-read.log`. Pass when each reads as finished work.
- [ ] Lane 10. Run A's transcript script on an uncaptioned fixture. Save `tp2-no-captions.log`. Pass when it records `no captions` and the run goes on.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Tokens and wall time of each test run.
- [ ] Probe. Lanes 2, 3, 5, 6 and 7.
- [ ] Baseline. None, new at head. Record head only.
- [ ] Rule. No fail rule. Recorded in the catalog rows.

**Review gate.** None. TP2 is not review-gated. TP4 carries the pack's review.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends TP2 on `engine/tp1`.

## Ship the trader templates and draft the node and risk ones (TP3)

**Depends on.** TP2.

**Files.**

- [ ] Create `src/qmx_engine/templates/db-desk-brief/` and `t4-research-desk-overnight/`, runnable.
- [ ] Create the drafts `dm-demo-monitor/`, `t7-trade-journal-review/`, `gw-guard-watchdogs/`, `rk2-correlation-drift/`, `dc-decay-and-limit-report/`, `rk5-stress-tests/`, `rk8-incident-post-mortem/`, `p1-portfolio-combination/`, `p2-daily-book-report/` and `pp-proposal-pack/`.
- [ ] Edit `src/qmx_engine/templates/catalog.py` and `tests/test_templates.py`.

**Build.**

- [ ] Build DB from T1, T2 and T10 in file 16. Node facts are marked `could not check: trading node`, as file 19 says. Build T4 from its card with a chunked fan-out over the watchlist's news items.
- [ ] Write each draft from its card as a full definition that validates, with `meta.needs` from Appendix I. Each draft's `README.md` says in one line what it waits for.
- [ ] No template reads a broker credential or names a money act. P2 waits for the read-only broker token, so it is a draft.

**You see.**

- [ ] `templates list` shows 9 published and disabled, and 10 new drafts, each with its need.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_templates.py` gains cases that each draft validates, that its test run is refused with its need, and that no template parameter passes the money lint. Run `uv run --no-sync python -m pytest tests -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run `t_templates.py rs1 rs4` at head. Save `tp3-regression.log`. Pass when both still pass.
- [ ] Lane 2. Run `t_templates.py db` on real models. Save `tp3-db.log`. Pass when the brief validates and every node fact reads `could not check`.
- [ ] Lane 3. Run `t_templates.py t4`. Save `tp3-t4.log`. Pass when the chunked desk run passes and cites a source for each line.
- [ ] Lane 4. Try to test and to enable each of the 10 drafts. Save `tp3-drafts.log`. Pass when all 20 calls are refused with the right need.
- [ ] Lane 5. Run `templates install`. Save `tp3-install.log`. Pass when the counts match the catalog.
- [ ] Lane 6. Run the money lint over every TP3 folder. Save `tp3-money.log`. Pass when it is clean.
- [ ] Lane 7. Read DB's output. Save `tp3-db-read.log`. Pass when it reads as a finished brief.
- [ ] Lane 8. Read each draft's `README.md`. Save `tp3-readmes.log`. Pass when each names its need in one line.
- [ ] Lane 9. Validate GW as a script-only definition. Save `tp3-gw.log`. Pass when it has no model node.
- [ ] Lane 10. Run T4 with the fake switch. Save `tp3-fake.log`. Pass when no provider is called.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Tokens and wall time of DB and T4 test runs.
- [ ] Probe. Lanes 2 and 3.
- [ ] Baseline. None, new at head. Record head only.
- [ ] Rule. No fail rule. Recorded in the catalog rows.

**Review gate.** None. TP3 is not review-gated. TP4 carries the pack's review.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends TP3 on `engine/tp2`.

## Draft the Lab and developer templates and close the pack (TP4)

**Depends on.** TP3.

**Files.**

- [ ] Create the drafts `b-build-and-prove/`, `rs3-source-to-lab-test/`, `rs6-hypotheses-from-dead-ends/`, `rs8-big-data-question/`, `l1-idea-to-first-result/`, `l4-overnight-lab-loop/`, `bc-build-a-component/`, `d3-iterate-against-qmb/`, `d4-variant-comparison/`, `d6-ml-training-run/`, `ma-mini-app-lifecycle/` and `d9-mini-app-pipeline/`.
- [ ] Edit `src/qmx_engine/templates/catalog.py`, `tests/test_templates.py` and `docs/ENGINE-NOTES.md`.
- [ ] Create `qmx-agents/packages/qmx-engine/docs/TEMPLATES.md`.

**Build.**

- [ ] Write each draft from its card in files 15 and 17 as a full definition that validates, with `meta.needs` from Appendix I.
- [ ] Write `TEMPLATES.md`, one table with all 31 templates, their plain names, status, test cost, triggers and needs, and how the operator edits one with the copilot.
- [ ] Run full `just ci` once under the CI lock.

**You see.**

- [ ] `templates list` shows 31 rows, 9 published and disabled, 22 drafts each with its need.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_templates.py` gains a case that the catalog has exactly 31 rows and that each folder validates. Run `uv run --no-sync python -m pytest tests -q -n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against trunk. Run full `just ci` at `engine/ep14` and at head. Save `tp4-regression.log`. Pass when head fails nothing that EP14 passes.
- [ ] Lane 2. E32. Run `t_templates.py all` for the 9 runnable templates. Save `tp4-all.log`. Pass when 9 of 9 pass on real models.
- [ ] Lane 3. Run `templates install` on a fresh throwaway home through the engine host. Save `tp4-install.png`. Pass when the screen shows 9 published and disabled and 22 drafts.
- [ ] Lane 4. Try to test and to enable each of the 12 new drafts. Save `tp4-drafts.log`. Pass when all 24 calls are refused with the right need.
- [ ] Lane 5. Run `run_all.py`. Save `tp4-run-all.log`. Pass when it prints 0 FAIL.
- [ ] Lane 6. Read `TEMPLATES.md` against the catalog. Save `tp4-doc.log`. Pass when the rows match.
- [ ] Lane 7. Clone RS1 as a variant through `extends` and test it. Save `tp4-variant.log`. Pass when the variant passes and records `variant_of`.
- [ ] Lane 8. Sum the pack's test cost. Save `tp4-cost.log`. Pass when the total tokens and calls are recorded for Appendix E.
- [ ] Lane 9. Run the money lint over the whole pack. Save `tp4-money.log`. Pass when it is clean.
- [ ] Lane 10. Hash `qma-harness` at base and head. Save `tp4-harness-hash.log`. Pass when they match.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of `t_templates.py all`.
- [ ] Probe. Lane 2.
- [ ] Baseline. The sum of TP1 to TP3's single test runs.
- [ ] Rule. No fail rule. A total above 60 minutes is logged so the operator knows a full retest takes that long.

**Review gate.** The operator reviews before landing.

- [ ] Copy the lane 3 screenshot and a screen of `TEMPLATES.md` into `D:/QMX-worktrees/qma-ship/engine/review/TP4-review-<slug>.png`.
- [ ] Record a 30 to 60 second video of RS1 running a test on real models and its note opening, with `ffmpeg -f gdigrab`. Save it as `D:/QMX-worktrees/qma-ship/engine/review/TP4-review.mp4`.
- [ ] Post the screenshots, the video and `TEMPLATES.md` in chat for the operator. Stop. He lands the stack.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends TP4 on `engine/tp3`. The operator lands Track T bottom-up after his review.

## Close the program

- [ ] Every box above is checked with its evidence, and every lane outside a run set has its `menu, not run` row.
- [ ] Reply to the operator with the report autopilot-stack names. Give links to each stack's root and tip, a one-line verdict per PR, what was parked or excluded and why, the open H-requests, and the trail at `D:/QMX-worktrees/qma-ship/engine/decisions.tsv`.
- [ ] Write `D:/QMX-worktrees/qma-ship/ENGINE-RESUME.md` with the stack state for his landing session.
- [ ] List every `engine/*` branch and worktree for his go. Delete none without it.

## Appendix A. Prototype evidence

No prototype ran in this planning pass. EP0 and EP1 are the probes, and they run first. The planner read these facts from `qma/hp17` at `584a7f41`, whose harness tree is the one `ed704c92` holds with `git show`, and each one shaped a PR.

| Fact read from the code | Where | Shapes |
|---|---|---|
| `Background` is defined in `qma/harness/launch.py:66` and not exported by `qma/harness/__init__.py` | `qma-harness/src/qma/harness/__init__.py` | H0, HG1's exports, EP2, EP10 |
| `qma.serve` builds control, harness and app inside `routes._serve`. Only `serve()` is public | `routes.py:435-470` | H0, EP13's `qmx_engine.host` |
| `Harness.live()` yields deltas only and never signals a turn end | `chat.py:889-897` | H1 fallback, EP0 `p_turn_end.py` |
| The chat record JSON with its `turn` field lives at `QmxHome.chats_dir / f"{sid}.json"` | `home.py:628-637` | EP0 detector candidate |
| The harness's `test_tools.py:55` requires every `OPERATIONS` name to be in its allow-list or left-out map | `qma-harness/tests/test_tools.py` | H17, HG1 adds rows to both tables together |
| The 501 stubs are `workflows_get/put/validate/run` and run or job cancel without an owner. `library_*` work | `qmx_control/service.py:659,680,916-930` | EP13 |
| `runs_*`, `run_job` and `jobs_*` already mean remote compute runs | `service.py:518-617` | EP13 keeps engine runs out of them (27b S16) |
| The harness gives each Background chat `max_budget_usd` 5.0 and `background_cap` 0.5 | `launch.py:182-188`, `harness.py:353-361` | EP10 maps both to `waiting` (27b S4), and reads `background_cap` as the plan account's share setting (ruling 90) |
| Background chats are verbatim, so the engine cannot send `/compact` | `launch.py:87-90` | EP11 chunk sizing, H15 in HG1 |
| Key-provider rows accept `quirks.env` including `CLAUDE_CODE_AUTO_COMPACT_WINDOW` | `profiles.py:138-146, 297-325` | EP0 lane 7, EP11 |
| Background and Child chats get `max_turns` and `max_budget_usd` from global `[budgets]` | `launch.py:176-188, 424-425` | H2 fallback |
| Plan turns journal `model_call` rows with cache read and write under `runs/<sid>/journal.jsonl` | `chat.py:1196-1207`, `usage.py:345` | EP10 spans |
| `UsagePage` carries per-window readings with `resets_at` | `usage.py:451-470` | EP10 admission |
| No cron library is in either lockfile, and `jsonschema` and `tzdata` are | `qmx-agents/uv.lock`, `uv.lock` | EP3, EP12 |

Unproven after the probes, by design. The agentOS half of E23 needs its own probe. The relay-routing half of E24 needs the harness pool packet (H10). Nothing runs on macOS or Linux in this program.

## Appendix B. Alternatives rejected

- **Autopilot-full.** The selection rule picks autopilot-stack for sequenced work the operator reviews before landing. The HP program used autopilot-full because the project rule let the coordinator merge into `rebuild/base`. This brief withholds merging, so stacks it is.
- **Ten live lanes per PR.** The operator's light rule replaced them on 2026-10-15. They stay in the plan only as a menu, because `check-plan.mjs` requires them.
- **Seating the engine in `qma.serve` inside HG1.** AD-3 wants `qma.serve` to start the engine. Ruling 89 grants H0, H15, H16 and H17 and nothing more, and H0 is exports only. The interim `qmx_engine.host` composes the same public calls, and L1 is the real seat.
- **New `qmx` tools in `OPERATIONS` from an engine PR.** Adding rows breaks the harness's own `test_tools.py` unless its tool table grows in the same change. HG1 adds both together, and the engine's two remaining routes live in their own router.
- **A second process with its own harness on the operator's home.** `Harness.open` kills CLI trees of its home, and a second home needs a second plan login. One host per home, with a lane lock for checks.
- **`human_gate` in this program.** Ruling 77 says almost nothing waits, and the only waits are irreversible external steps, which no in-scope node makes. The kind stays registered and unavailable.
- **Agent nodes that write on the host.** AD-24 keeps model-written code off the host. Until the sandbox packet, asks are rejected, so agent nodes read and answer only.
- **Grouping templates by wave.** Waves are dropped (ruling 33). Templates are grouped by what they need.

## Appendix C. Risks

- **Turn-end detection is racy without H1 (EP10, EP11).** EP0 measures the detectors first. If none catches 5 of 5, the EP10 builder reports it before building, and the coordinator brings the operator H1 as a choice with a recommendation.
- **Two harnesses on one home kill each other's chats (all lanes with models).** The lane lock serializes every lane that opens a harness on the ship home.
- **Agent nodes are read-only until the sandbox packet (EP11, Track T).** Templates are written so models read inputs that scripts fetched. Templates that need agents to write code are drafts with `needs: sandbox`.
- **No pool, so no account rotation (EP8, EP10).** The ladder's account step is recorded as skipped. One plan account and the OpenRouter row carry all tests.
- **Plan usage (all PRs).** Builders draw far more of the plan than lanes do. At most two agents run at once in all.
- **OpenRouter spend (EP10, EP11, Track T).** Small, and on his own key for tests (ruling 51). Appendix E estimates it.
- **The B1 SQLite floor (EP4).** Python 3.14 here bundles a SQLite below 3.51.3. The ledger keeps one writer connection and checkpoints only from it.
- **The architecture changed the night before (all PRs).** `27c-gap-fixes-applied.md` applied 27b's blockers. This plan matches 27c, including AD-34 and AD-35, the shared run status table, `refs/drafts`, H0 and H15 to H17 (now granted and built in HG1, with their fallbacks kept as safety), the tool Effects of SOLUTION-DESIGN 13, capacity from RAM, and E29 to E32. A conflict found later is a stop for the planner.
- **D1 deletion PRs may also edit `qmx-control` (EP9, EP13).** D1 has not run. If it lands first, the root rebases EP9 and EP13's two small edits.
- **Opus reviews Opus (every PR).** A cross-family review is not run. Fable reviews only when he asks.
- **No macOS or Linux test machine.** Out of scope for this program.

## Appendix D. Links and reading list

- The contract is `architecture/workflow-engine/`. Owners read `ARCHITECTURE-SPINE.md` for the ADs their PR names and `SOLUTION-DESIGN.md` for the sections their PR names. For the Library, only `architecture/library-and-data/ARCHITECTURE-SPINE.md` AD-15 and `ENGINE-REQUESTS-ANSWERED.md`.
- Rulings live in `research/methodology/26-operator-rulings-and-alignment.md`. Section J and rulings 83 and 84 are the latest. Earlier files lose where they disagree.
- Templates come from `archive/2026-10-16-methodology-drafts/19-centralized-design.md` section 7 and the cards in files 15, 16 and 17.
- The harness is read-only except in HG1. `ed704c92` holds it as merged from `qma/hp17`. Its sign-off is `qmx-agents/packages/qma-harness/docs/SIGNOFF.md`.
- HG1, EP10 and EP13 get `C:/Users/Mubarak/.claude/skills/how/SKILL.md` before editing, because they meet the harness and `qmx-control`. No PR gets `/interrogate` (Override 2).
- The coordinator keeps its trail per `C:/Users/Mubarak/.claude/skills/show-me-your-work/SKILL.md` in `D:/QMX-worktrees/qma-ship/engine/decisions.tsv`. Each owner returns its own `decisions.tsv` uncommitted. The planner's trail is `tracker/qma-v2/trail/engine/decisions.tsv`.
- Never read `tracker/qma-v2/archive/` as the plan.

## Appendix E. Sizing (an estimate)

Every number here is the planner's estimate, not a measurement. Effort is focused builder hours. The checker adds about 45 minutes per PR and the coordinator about 20. Model turns count the live model turns that lanes and test runs make, never builder turns. Test runs use each role's cheap candidates from the providers QMA v2 has configured (ruling 51). OpenRouter rows are tried first in test mode, so most test spend lands there. Plan-profile turns are the turns that run through the CLI login in the ship home. No Anthropic or OpenAI API spend happens.

| PR | Effort (h) | Plan-profile turns | OpenRouter calls | Stack |
|---|---|---|---|---|
| EP0 | 3 | 40 | 10 | probe |
| EP1 | 4 | 160 | 0 | probe |
| HG1 | 3 | 5 | 0 | E |
| EP2 | 2 | 0 | 0 | E |
| EP3 | 4 | 0 | 0 | E |
| EP4 | 3 | 0 | 0 | E |
| EP5 | 4 | 0 | 0 | E |
| EP6 | 4 | 0 | 0 | E |
| EP7 | 5 | 0 | 0 | E |
| EP8 | 4 | 0 | 0 | E |
| EP9 | 5 | 0 | 0 | E |
| EP10 | 5 | 15 | 40 | E |
| EP11 | 6 | 25 | 30 | E |
| EP12 | 4 | 0 | 0 | E |
| EP13 | 5 | 0 | 5 | E |
| EP14 | 3 | 10 | 40 | E |
| TP1 | 5 | 10 | 80 | T |
| TP2 | 5 | 10 | 150 | T |
| TP3 | 4 | 5 | 80 | T |
| TP4 | 3 | 10 | 110 | T |
| Total | 82 | 290 | 545 | |

- **Number of PRs.** Twenty. Two probes, HG1 and thirteen engine PRs in Track E, and four in Track T. DP1 was removed because data is held (ruling 91).
- **Wall time.** One Track E builder at a time, a checker beside it, and the probes in parallel with HG1 at the start. Roughly four to five working days. A guess.
- **Model turns.** About 290 plan-profile turns, most of them EP1's E23 task runs, and about 545 OpenRouter calls, most of them template test runs. The one fix round per PR adds an estimated 20%. EP14 lane 8 and TP4 lane 8 replace these guesses with counts.
- **Full suite.** `just ci` runs twice, before EP14's check and before TP4's check.

## Appendix F. Departures, harness requests and how llm and agent nodes inherit the harness

**Departures from the architecture, each with its reason.**

| AD | Departure | Reason | Ends when |
|---|---|---|---|
| AD-3 | The engine runs under `qmx_engine.host`, not `qma.serve` | the composition root is inside the harness package. HG1 grants H0's exports, and H0 does not cover composing the engine in `qma.serve` | L1 |
| AD-12 | No pool, so the ladder's account step is skipped and recorded | the pool is a later packet (L2) | L2 |
| AD-25 | `cli_inside` and `host_harness` nodes are refused at dispatch | they need relay run passes | H11, then L4 |
| AD-35 | The engine records each Background chat's home on `node_started` but does not write `session_homes` in `qmx_control` | AD-35 is new and outside this program's scope | L17 |
| AD-25 | Agent nodes run as harness Background chats with every ask rejected, so they cannot write | the sandbox is a later packet (L6) | L6 |
| AD-11 | Test mode marks `test_only` rows in the engine's `[roles]`, not in a pool | no pool yet | L2 |
| AD-14 | The Library is a SQLite fake behind `LibraryPort` | the real Library ships later | L11 |

**Granted harness requests.** These extend `architecture/workflow-engine/HARNESS-REQUESTS.md` H1 to H14. The operator granted all four on 2026-10-17 (ruling 89). HG1 builds them, the engine uses the real APIs, and each fallback stays only as safety.

| Id | Request | Real API in use after HG1, and the fallback kept as safety |
|---|---|---|
| H0 | Export `Background` and `Child` (and `Interactive`) from `qma.harness.__init__`. This plan also needs `qma.serve` to compose the engine, which H0 as written does not cover | The adapter imports the pair from `qma.harness`. Safety is AD-3's one allow-listed import from `qma.harness.launch`, restored only if HG1 is parked. `qmx_engine.host` stays as the interim composition root until L1 |
| H15 | A per-chat compaction threshold on `NewChat` for Background and Child chats | `NewChat(compact_at=...)` on plan and key rows. Safety is AD-34's restart, a `memory_note` and a fresh chat seeded with the summary, used only when the option is refused or no `compacted` event arrives |
| H16 | Per-chat SDK hook callbacks for Background chats (PreToolUse observe, PostToolUse, PreCompact, Stop, SubagentStop), after the money gate | `NewChat(hooks=ChatHooks(...))`. Tool spans arrive live from PostToolUse. Safety is the turn-end reconcile against the `tool` session blocks |
| H17 | `AGENT_OPERATIONS` rows for the new `workflow_*` tools and `apps_archive` (SOLUTION-DESIGN 13), with draft save and test run as DOMAIN_WRITE | HG1's rows. Saving a draft and running a test never ask, and publishing and a live run each ask once. Safety is the `library_save` watcher that test-runs a draft whose `meta.test_requested` changed. The Library and Lab rows wait for their programs |

Engine `OPEN-DECISIONS.md` call A is answered yes (ruling 89). HG1 lands before EP2, and EP2, EP10, EP11 and EP13 use the real APIs at the boxes that name each H-request.

**How `llm` and `agent` nodes inherit the harness (ruling 78).**

| Concern | What the harness does at `ed704c92` | What the engine does | Gap and packet |
|---|---|---|---|
| Context compaction | The CLI auto-compacts. Background chats are verbatim, so `/compact` never dispatches. `compact_boundary` becomes a `changed` block of kind `compacted` | fills chunks to `chunk.fill` (0.30), sets `compact_at` 0.40 per chat on every row (H15), writes a `memory_note` from the PreCompact hook (H16), keeps the restart as safety, and records each compaction as a span event | none after HG1 |
| Prompt caching | The CLI caches. The relay keeps Moonshot's cache markers. Cache read and write tokens land in run journals and relay rows. A config change that `resets_cache` relaunches | puts the static brief first and the chunk last, byte-stable across chunks, never relaunches a chat mid-node, and records cache tokens per span | none |
| Hooks | The money gate runs as a PreToolUse hook on every tool, with deny rules in `disallowed_tools` | inherits both unchanged and adds observe-only per-chat hooks after the money gate (H16) | none after HG1 |
| Tool calls | Background chats get the Claude Code preset, the `qmx` MCP tools and vetted servers. Asks wait up to `unattended_ask_seconds` | rejects every ask at once, states the node's tool list in the brief, and records `tool` blocks on the span | H2 per-chat allow-list, H8 sandbox tools, L6 |
| Structured output | none per chat | validates the final text against the node's schema with one repair turn in the same chat | H2 |
| Turn cap | global `[budgets] max_turns` for Background chats | enforces run and idle timeouts and `agent.max_tool_calls` with `Harness.interrupt` | H2 |
| Turn end | `live()` gives deltas only | the detector EP0 picks | H1 |
| Limits | `LaunchRefused` on the plan stop or the global `[budgets] background_cap`, and `UsagePage` readings | reads each account's background share as a setting (no fixed cap, ruling 90), maps a refusal to `waiting(limit, resume_at)`, maps a chat that hit `max_budget_usd` to `waiting(runaway)`, and drains the run (AD-9) | H6 and per-account strategy with the pool (L2) |
| Sub-agents | the Agent tool is on in Background chats with global caps | leaves them on and counts their tokens through the journal | H7, L7 |

## Appendix G. Later packets, in dependency order

Out of scope for this program. Each is a later packet with its own plan.

1. **L1 Seat the engine in `qma.serve`.** After HG1. Deletes `qmx_engine.host` and the safety import exception.
2. **L2 The account pool and the balancer.** The one harness extension (ruling 39), with H6 and H13. E8. Adds the ladder's account step. Every pool account carries its own background share, strategy (fill-first, round-robin or least-used), ceiling and cooldown, editable in Settings, and the harness's global `background_cap` becomes per account. No hard global cap (ruling 90).
3. **L3 Relay routing by model id and mixed providers.** H10, H14, and E24's relay half (rulings 62, 63). Needs L2.
4. **L4 The key vault and run passes.** AD-28, H11, L11 and L12 of the Library requests. E25 and E26. Needs L2.
5. **L5 Contabo `qmx-node`, the server engine instance.** AD-30. Contabo has 6 cores and 12 GB RAM (ruling 76). With `session_mb` 1,536 and an `overhead_mb` of 6,144 that counts the colocated services, it derives 4 sessions (27b B6). Provider setup from each provider's own skills or instructions (ruling 74). `event` and `webhook` triggers. Needs L4.
6. **L6 Sandbox tiers and `runner_outside`.** AD-24, AD-25, H2, H8. E16, E17, and E23's findings from EP1. Lets agent nodes write. Needs L1.
7. **L7 Sub-agent caps.** H7. E18. Needs L6.
8. **L8 Remote placements and the gateway.** AD-20, AD-30, `qmx_remote.ComputeProvider` adapters, E13, E27. Needs L4, L5 and L11.
9. **L9 The RLM kernel.** E22. Needs L6.
10. **L10 Agent-made tools.** Library request L4. Needs L6 and L11.
11. **L11 The real Library behind `LibraryPort`.** From the Library program. Swaps the fake.
12. **L12 Memory, the built-in provider and the already-built check.** AD-18, AD-27. E19. Needs L11.
13. **L13 Self-improvement.** AD-26, ruling 79. E20. Needs L12.
14. **L14 The Cua pack.** AD-33. E28. Needs L6 and L8.
15. **L15 The remaining node kinds.** `human_gate` for irreversible external steps, `app_op`, `library`, and `claude_workflow` after H4. Needs L11.
16. **L16 Data.** `data: deeper study first, explained to the operator (ruling 91)`. Nothing on data ships until that study is done.
17. **L17 Session homes (AD-35).** The `session_homes` table and its write-once route in `qmx_control`, and the engine writing the home of every Background chat it starts, backfilled from `node_started`.
18. **L18 The UI.** Lab Graph mode, run cards, notifications (UI-side, ruling 77). Its notes go to `UI-HANDOFF.md`.
19. **L19 Turn each template draft runnable** as its `needs` land, starting with the QMB door and the trading node read model.

## Appendix H. Defaults

Every value here is Claude's default, not the operator's. Each lives once in `qmx_engine.settings.DEFAULTS` and is UI-editable (his standing rule). Each was checked against file 26.

| Setting | Default | Ruling check |
|---|---|---|
| `scheduler.tick` | 60 s | SOLUTION-DESIGN 17 |
| `scheduler.lease_seconds`, heartbeat | 300 s, 60 s | 17 |
| `scheduler.grace` | 15 min, then one catch-up | ruling 54 |
| `limits.interactive_reserve` | 2 live chats kept for him | ruling 26 (workflows use non-loaded capacity) |
| `limits.slack` | 60 s after a reset | ruling 27 |
| `limits.alert_after` | 6 h, for a `provider_failure` item when every account is closed | ruling 77 |
| `chunk.size` | 10 items, when a chunk edge says `by: items` | ruling 78 |
| `chunk.fill` | 0.3 of the model's window, when a chunk edge says `by: tokens` | ruling 78, 27b B1 |
| `agent.compact_at` | 0.40 of the window, passed per chat as `NewChat(compact_at=...)` (H15, HG1) | ruling 78 |
| `agent.max_tool_calls` | 200 per attempt | 27b B1 item 5 |
| runaway guard per run when a template sets none | 400k tokens, 12 agents, 2 h wall time, no USD figure. A breach waits and never asks | rulings 27, 77, 27b S3 |
| `pool.accounts.<account>.background_share` | 0.5 of that account's plan window, per account, not a cap. Claude's default, UI-editable. Until L2 the plan account's value is the harness's `[budgets] background_cap` | ruling 90 |
| `pool.strategy` | `fill-first`. The others are `round-robin` and `least-used`. Claude's default, UI-editable, and it acts once L2 brings a second account | ruling 90 |
| `pool.accounts.<account>.ceiling` | none, so the share alone applies. Claude's default, UI-editable | ruling 90 |
| `pool.accounts.<account>.cooldown` | 300 s after a quota refusal. Claude's default, UI-editable | ruling 90 |
| `[budgets] max_live_chats` on an engine host | 6. Claude's default, marked. It is a Settings value, not engine code. The harness default of 4 leaves the engine 2 chats | SOLUTION-DESIGN 7.4, his call |
| `on_runaway` | `pause` | ruling 27, AD-16 |
| `retry.max_tries` | 3, backoff 30, 120, 600 s | 17 |
| `timeout` for `agent` | 1,800 s run, 300 s idle | 17 |
| `agent.max_turns` | 12, enforced by timeouts until H2 | 17 |
| `inline_limit_bytes` | 64 KiB | 17 |
| `placement.pc.concurrency` | 3 | 17 |
| `[roles]` candidates | SOLUTION-DESIGN section 9's lists, filtered to providers QMA v2 has configured today (the plan, the OpenRouter row, GPT when its lane is open). No new tier is invented | AD-13 |
| test-mode candidate order | each role's cheap end first, OpenRouter rows admitted (`test_only`) and tried first, then the role's plan-profile candidates | rulings 51, 26 (OpenRouter for tests only) |
| `[roles]` live candidates | the plan first, then key rows as he adds them | ruling 26 |
| `context_window` per candidate | 200,000 tokens unless the row declares more | ruling 78 |

## Appendix I. Template catalogue and needs

The 31 templates of file 19 section 7. Runnable ones are tested on real models and installed disabled. The rest validate and wait for what `needs` names.

| Id | Template | PR | Status | Needs |
|---|---|---|---|---|
| RS1 | Paper scout to research note | TP1 | runnable | none |
| T3 | News and macro calendar watch | TP1 | runnable | none (guard cross-check reads `could not check`) |
| RS0 | Idea grill to term sheet | TP2 | runnable | none |
| RS2 | Source to component card | TP2 | runnable | none |
| RS4 | Literature review on a topic | TP2 | runnable | none |
| A | Fill the Library, funnel stages 1 to 7 | TP2 | runnable | none (writes through the fake Library) |
| RV | Weekly review | TP2 | runnable | none |
| DB | Desk brief | TP3 | runnable | none (node facts read `could not check`) |
| T4 | Research desk overnight | TP3 | runnable | none |
| DM | Demo monitor and execution quality | TP3 | draft | trading-node |
| T7 | Trade journal review in R | TP3 | draft | trading-node |
| GW | Guard watchdogs | TP3 | draft | trading-node |
| RK2 | Correlation and exposure drift | TP3 | draft | trading-node |
| DC | Decay and limit report | TP3 | draft | trading-node |
| RK5 | Stress tests | TP3 | draft | trading-node |
| RK8 | Incident post-mortem | TP3 | draft | trading-node |
| P1 | Portfolio combination study | TP3 | draft | trading-node, risk-session |
| P2 | Daily book report | TP3 | draft | broker-read-token |
| PP | Proposal pack he signs | TP3 | draft | trading-node, risk-session |
| B | Build and prove, funnel stages 8 to 12 | TP4 | draft | qmb-door |
| RS3 | Source to a Lab test | TP4 | draft | qmb-door |
| RS6 | Hypotheses from dead ends | TP4 | draft | real-library (memory) |
| RS8 | Big-data question | TP4 | draft | rlm |
| L1 | Idea to first result | TP4 | draft | qmb-door |
| L4 | Overnight Lab loop | TP4 | draft | qmb-door |
| BC | Build a component or indicator | TP4 | draft | sandbox |
| D3 | Iterate against QMB with overfit guards | TP4 | draft | qmb-door |
| D4 | Variant generation and comparison | TP4 | draft | qmb-door |
| D6 | ML training run with a holdout | TP4 | draft | qmb-door, sandbox |
| MA | Mini app lifecycle | TP4 | draft | sandbox, app-op |
| D9 | Mini-app-to-mini-app pipeline | TP4 | draft | app-op |

## Appendix J. Attention, for the operator

No call of his is open. He answered the three calls from engine `OPEN-DECISIONS.md` on 2026-10-17. He granted H0, H15, H16 and H17, built in HG1 (ruling 89). He ruled that there is no fixed background cap, only per-account settings (ruling 90). He held data, so DP1 is removed (ruling 91).

For his attention.

- `[budgets] max_live_chats` = 6 on an engine host is Claude's default, marked in Appendix H. The harness default of 4 leaves the engine 2 chats on the PC. He sets it in Settings.
- The base is `origin/rebuild/base` at `ed704c92`, which already holds the merged HP stack. `33-state-of-play.md` now says so.
- The engine runs under the interim host `qmx_engine.host` until L1 puts it inside `qma.serve`. HG1's H0 grant exports names only and does not seat the engine. Do not start `qma.serve` and the engine host on the same home.
- Agent nodes cannot write files until the sandbox packet (L6). Every ask is rejected. Templates fetch with scripts and use models to read and write text, so the nine runnable templates still work.
- Each account's background share (0.5), the pool strategy (`fill-first`), ceilings (none) and cooldowns (300 s) are Claude's defaults, marked in Appendix H. He edits them in Settings. Strategy acts once the pool (L2) brings a second account.
- Twenty-two templates ship as drafts, each naming what it waits for. Most wait for the trading node or the QMB door.
- Every review in this program is Opus checking Opus. A cross-family review was not run, and Fable runs only when he asks.
- The planner's own trail was not reviewed by another model family, because this planner could not start agents.
