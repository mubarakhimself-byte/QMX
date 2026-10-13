# QMA v2 harness build plan

This program builds `qma2`, the agent harness that `qmx-control` embeds, for the operator (Mubarak). When it lands, he can sign in with Claude in the temporary console at `http://localhost:8766/console` and chat with an agent that has vanilla Claude Code tools on two engines. Those engines are the Claude Agent SDK on his one Max plan and the OpenAI Agents SDK on an OpenRouter key or a ChatGPT sign-in.
The rule the program enforces is one QMX policy point for every tool call on both engines, and money stays read-only for agents.
The design contract is `tracker/qma-v2/HARNESS.md` with its Amendments A1 to A11, plus the binding rules V1 to V6 in `research/interrogate/VERDICT.md`.
PR ids in dependency order are U0, U1, U1b, then U2 and U4a in parallel, then U3, U4b, then U5 and U6 in parallel, then U7 and U9 in parallel, then U8, then SIGNOFF.
Every PR lands in `rebuild/base`. The operator moves `integration`, then `staging`, then `main` later, and `main` moves only by his click.
Old-code deletion is a separate program in `tracker/qma-v2/DELETION-PLAN.md`. It starts only after he signs off SIGNOFF.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/orchestrate.md`, collapsed as its "Ceremony must scale" line allows. One coordinator chat on `opus` dispatches one `poteto-agent` builder per PR on `opus`, with at most three builders in flight. The coordinator verifies each PR itself at the head SHA and merges verified PRs into `rebuild/base` with `gh pr merge --merge` in dependency order. It never merges into `main` or `integration`. U1b, U2, U4b, U5 and SIGNOFF change what the operator sees, so they stop at merge-ready for his click.

Each PR's ten live lanes are coverage boxes. The coordinator runs all ten itself, inline, in one boot of the PR head. They are not ten agents.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on the operator's explicit go. Evidence is his go message, quoted in `D:/QMX-worktrees/qma2-ship/decisions.tsv`.
- [ ] Read these from trunk at program start. Re-read them at every tick. Each read is logged in `decisions.tsv` as "Skill tool" or "Read".
  - [ ] `git show origin/main:CLAUDE.md` for the project rules on trunk. Then Read `C:/Users/Mubarak/Desktop/QMX/CLAUDE.md`, because its QMA v2 section is not committed to `main` yet.
  - [ ] `git -C D:/QMX-worktrees/agent-system show plan/agent-system:tracker/qma-v2/HARNESS-PLAN.md`, then the same for `HARNESS.md`, `research/interrogate/VERDICT.md` and `research/H3-code-map.md`. The plan branch is local only, so read it without `origin/`.
  - [ ] Read `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/orchestrate.md`, `shipping.md`, `pause-safely.md`, `session-pickup.md` and `opening-a-pr.md` from the same folder, then `C:/Users/Mubarak/.claude/skills/swarm/SKILL.md` and `show-me-your-work/SKILL.md`. The pstack skills live in this local install, not in the QMX repo.
  - [ ] Load the control skill for the console with the Skill tool, `anthropic-skills:built-in-browser`. From U1b on, also run `git show origin/rebuild/base:.claude/skills/verify-qmx-agents/SKILL.md`.
  - [ ] Read `~/.agents/pstack-models.md`. Program override from the operator's brief is that builders and verifiers run on `opus`, `sonnet` only for very small tasks, `fable` only as the second reviewer on U2 and U7 and in the final cross-model trail review (never for coding), never the `bulk-worker` agent type.
- [ ] Install the store at `D:/QMX-worktrees/qma2-ship/`. Write `preferences.md`, `units.tsv`, `ledger.tsv`, `gates.md`, `decisions.tsv`, `probes.md` and `turns.tsv` before any spawn. `orch.ts` is not installed (`C:/Users/Mubarak/.claude/skills/poteto-mode/scripts/orch/` is empty), so keep the TSV files by hand.
- [ ] Write these standing orders into `preferences.md`, one numbered line each, and paste the file verbatim into every builder brief.
  - [ ] Base branch `rebuild/base` (tip `4eac8f69` or newer) in repo `C:/Users/Mubarak/Desktop/QMX`, GitHub `MubarakHimself/QMX`. Each builder works in its own worktree `D:/QMX-worktrees/qma2-<pr-id>` on branch `qma2/<pr-id>`. Never touch `main` or `integration`.
  - [ ] Builders never spawn sub-agents. Assumption, unverified. The operator has set `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH=1`. If he has not, the brief text is the only guard.
  - [ ] Unset every `ANTHROPIC_*` variable before any test or CI run. Put `TMP`, `TEMP`, `UV_CACHE_DIR` and every `--basetemp` on `D:`.
  - [ ] Run `just ci` only while holding `D:\QMX-worktrees\.ci-lock`, created with `File.Open(..., 'CreateNew')`, with rclone on `PATH`. Never delete a lock you did not create. Pytest runs at most two workers (`-n 2`). Run poe tasks as `python -m poethepoet`, because App Control blocks `poe.exe`.
  - [ ] Never edit `qmb/` or `qmn/`. Never import `qmx_*`, `qma.*`, LangChain, LangGraph or deepagents from `qma2`. Builders make no live model calls. Fake clients back unit tests, and live checks belong to the coordinator.
  - [ ] Live checks use short prompts. Log every live model turn in `turns.tsv` (unit, lane, engine, model, prompt, tokens). Stop a unit's checks at 15 Claude turns unless the operator raises the cap. Run checks that need only "a model" on OpenRouter.
  - [ ] No branch or worktree deletion without the operator's go.
- [ ] Park the gates that only the operator can answer in `gates.md` before asking. They are his `/login` in QMX's claude-home (U1), his OpenRouter key in the OS secret store (U4a), his ChatGPT browser approval (U8), and his reconfirmation at SIGNOFF of the money-guarantee answer he gave on 2026-10-13 (HARNESS A12).
- [ ] On the operator's go, arm the audit tick as `/loop 1h` with the tick prompt below. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk. Audit the operation against it and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then post a short status message to the operator in chat only when the audit found a tracked change that no earlier status message reported, such as a PR opened, a code-ready head, a round launched or closed, a verdict, a merge, a stuck agent and the action taken, a blocker added or cleared, or a decision only the operator can make. Name every such change and nothing else. Do not repeat a table, the merged list, or an unchanged blocker. If the audit found none, end the turn with no reply text. Either way, log this tick's row in your decision trail. The row names the items reported, or none."
- [ ] On the operator's hold or stand-down, send every builder a zero-writes order at once.

### Spawn owners

- [ ] Spawn one builder per PR with `subagent_type: "poteto-agent"`, `model: "opus"`, `run_in_background: true`. Each brief has GOAL, SCOPE, CONTEXT, ACCEPTANCE, VERIFY, TIMEBOX, FORBIDDEN, REPORT and STANDING, and pastes the builder Method block from `research/H2-skills-method.md` section (b2). U0 is the pilot. No second builder starts before U0 merges.
- [ ] Follow this dependency graph. Start dependent work only after its parent merges. Each child branches from the current `origin/rebuild/base`.
  - [ ] U0 is first and alone. U1 follows U0, and U1b follows U1.
  - [ ] U2 and U4a after U1b. They run in parallel.
  - [ ] U3 after U2. U4b after U2, U3 and U4a. Then U5 and U6 in parallel after U4b.
  - [ ] U7 after U6. U9 after U5 and U6. U7 and U9 run in parallel. U8 after U5 and U7. SIGNOFF after every other PR.
- [ ] Relay upstream reports into downstream briefs. Every brief from U2 on gets the U1 probe results from `probes.md` pasted in full.
- [ ] Hold the file boundaries.
  - [ ] `qma2/host/openai.py` and `qma2/host/tools.py` have one owner per wave, in this order. U4a, then U4b, then U6, then U7, then U8. No other PR edits them. `qma2/host/claude.py` has one owner per wave. U1, then U2, then U3, then U6. `qmx-agents/pyproject.toml`, `tools/ci.py` and `tools/test_all.py` belong to U0. A later PR edits them only if its brief says so.
  - [ ] No PR touches `qmb/`, `qmn/`, `apps/qmx-ui/`, or the old `qma-core`, `qma-wire` and `qma-daemon` packages. The single exception is U0's SDK version constant and its matching test expectations in `qma-daemon`.
- [ ] Hold the review gate. U1b, U2, U4b, U5 and SIGNOFF change what the operator sees. They wait for his review in chat with screenshots and a video before merge.

### PR mechanics, for every PR

- [ ] Resolve the forge once. `command -v origin` finds nothing on this machine, so use `gh` for every PR operation and record that in `decisions.tsv`. Never require `gt`.
- [ ] The builder opens the PR ready, never draft, per **Opening a PR**, with `gh pr create --base rebuild/base --head qma2/<pr-id>`.
- [ ] The builder runs `python -m poethepoet fmt-check`, `lint` and `types` in `qmx-agents/packages/qma-v2` and in each other package it touched, once, before the PR-facing push. Push with hooks on.
- [ ] `/deslop` and `/no-comments` are not installed here. The builder rereads the full diff to cut slop, then runs `C:/Users/Mubarak/.claude/skills/no-comments/references/comment-sicko.md` itself over the diff. It records both as "inline" lines in its report. No Bugbot or security reviewer runs on this repo. The coordinator's two audit lanes take their place, triaged per `C:/Users/Mubarak/.claude/skills/poteto-mode/references/bugbot-triage.md`.
- [ ] Rebase onto current `origin/rebuild/base` before the code-ready report. Keep that merge base in fix rounds. Rebase again only at merge prep, on a `git merge-tree` conflict, or on a CI failure caused by a change on `rebuild/base`. Builders never rebase on their own initiative after code-ready.

### Verdict and merge, for every PR

- [ ] At the code-ready head SHA and at each later push that changes the patch, the coordinator runs the swarm lanes per `C:/Users/Mubarak/.claude/skills/swarm/SKILL.md` inline, in one boot. One gates lane runs `just ci` under the lock and saves `ci.log`. The ten live lanes come from the PR's **Verify, live** block. The perf lane comes from its **Verify, perf** block. Two audit lanes read the diff and the receipts and distrust the PR body. Audit lane A checks the VERDICT rules the unit owns. Audit lane B checks import edges, secrets, and the money rule.
- [ ] For a high-blast-radius PR (U2, U7), run `/interrogate` with one `opus` and one `fable` reviewer and log the reason. Fable reviews only. It never codes.
- [ ] Clean only when every lane is `PASS`. Findings go back to a fresh builder with consolidated scope, including a defect that a lane filed as a note. A new head gets a fresh run and a fresh verdict, except for results that stay valid under the patch-id rule in `playbooks/shipping.md`. Record the verdict in `ledger.tsv` with the PR number, head SHA, base SHA and `git patch-id --stable`. A new head voids the row unless the patch-id is unchanged.
- [ ] Merge only the contiguous verified run from the lowest unmerged PR in the graph, one PR at a time, with `gh pr merge <number> --merge --repo MubarakHimself/QMX`. Recompute the frontier after each merge. A review-gated PR merges only after the operator's click or his written go in chat.

### Boot recipe, for every live lane

The coordinator runs every lane of a PR on this machine in one boot. Lanes drive the console through the built-in Browser pane and the API through `qmx-agents/packages/qma-v2/scripts/drive.py` (from U1b) or the U1 script before that.

- [ ] `git -C D:/QMX-worktrees/agent-system fetch origin qma2/<pr-id>`, then check out the head SHA detached in the coordinator's own worktree `D:/QMX-worktrees/qma2-verify`.
- [ ] Remove every `ANTHROPIC_*` variable from the shell, set `TMP`, `TEMP` and `UV_CACHE_DIR` on `D:`, then run `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] Start the control host on a lane home with `uv run --project qmx-agents/packages/qmx-control python -m qmx_control start --port 8766 --home D:/QMX-worktrees/qma2-ship/homes/<pr-id>`. Wait until `GET /api/health` answers. Point the home's claude-home setting at the one claude-home he signed into at U1.
- [ ] Deliver console input only through the Browser pane tools. Deliver API input only through `drive.py` or the U1 script. Read-only diagnostics are `Get-Process`, `Get-DnsClientCache`, `git grep`, `rg` over the lane home, and `GET /api/events/<topic>`.
- [ ] Count each Claude turn in `turns.tsv` before sending it. At 15 Claude turns for a unit, stop and ask the operator to raise the cap or accept the remaining lanes as unrun. Save every screenshot and log to `D:/QMX-worktrees/qma2-ship/evidence/<pr-id>/<slug>` and list the paths in the ledger row.
- [ ] Stop the host with `python -m qmx_control stop --home <lane home>` and confirm with `Get-Process` that no host or CLI process is left.

## Scaffold the qma2 package (U0)

**Depends on.** None. U0 is the pilot and branches from `rebuild/base`.

**Files.**
- [ ] Create `qmx-agents/packages/qma-v2/pyproject.toml` with runtime pins `claude-agent-sdk==0.2.165`, `openai-agents==0.23.1` and an explicit `openai` pin. Put the SDKs in a `host` extra, so `qmx_apps` importing `qma2.money` pulls no SDK (VERDICT A28).
- [ ] Create `qmx-agents/packages/qma-v2/src/qma2/__init__.py`, `model.py`, `wire.py` and `doctor.py` from `tracker/qma-v2/sketch/qma2/`, with `AgentDef` and `McpServerDef` in `model.py` (VERDICT A23). Create `qmx-agents/packages/qma-v2/tests/test_doctor.py` and `tests/test_import_contract.py`.
- [ ] Edit `qmx-agents/pyproject.toml` (members, `[tool.uv.sources]`, pytest `--ignore`, ruff `extend-exclude`, pyright `exclude`), `tools/ci.py`, `tools/test_all.py` and `qmx-agents/uv.lock` (H3 sections 5 and 9). Remove the dev-group `claude-agent-sdk==0.2.163` pin at `qmx-agents/pyproject.toml:54`, because the workspace lock holds one version.
- [ ] Edit only the SDK version constant `CLAUDE_SDK_VERSION` in `qma-daemon/src/qma/daemon/request_runtime/native_claude.py` and the matching expectations in its fake-client tests and `examples/native_sdk_offline_check.py`, so the old suite stays green on the new pin. This is the one allowed touch of the old packages before D1. No test is skipped, deleted or weakened.

**Build.**
- [ ] Write the import-linter contract from the `qma2/__init__.py` docstring in the sketch, plus a ban on `qma2.policy` and `qma2.money` imports from `qma2.host` (VERDICT A23).
- [ ] Add a qma-v2 row with its own `fmt-check`, `lint`, `types` and test steps to `tools/ci.py` and `tools/test_all.py`.
- [ ] Write `qma2.doctor.probe(home)` returning `ProbeResult` with config home, SQLite version and single-writer mode, secrets backend, money-guarantee label, Claude sign-in status, SDK and bundled CLI versions, and managed settings (A4, VERDICT A28).

**You see.**
- [ ] `uv run --project qmx-agents/packages/qma-v2 python -m qma2.doctor --home D:/Temp/qma2-u0` prints JSON with `"money_guarantee": "tool_level_same_user"` and `"claude_agent_sdk": "0.2.165"`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_doctor.py` gains one case per doctor line. `tests/test_import_contract.py` runs `lint-imports`. Run `uv run --no-sync python -m pytest tests -q -n 2 --basetemp D:/Temp/pytest-u0` in `qmx-agents/packages/qma-v2`. Then run `just ci` under the lock and save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents.
- [ ] Lane 1. Regression lane against trunk. Run the qmx-control suite and `python -c "import qmx_control"` at trunk and head. Trunk has no `qma2`, so record that and gate `import qma2` at head. Save `u0-regression.log`. Pass when both suites report the same pass and fail counts and `import qma2` succeeds only at head.
- [ ] Lane 2. Plant `import qmx_control` in `qma2/model.py` in a scratch copy and run `lint-imports`. Save `u0-contract-qmx.log`. Pass when the contract fails and names the forbidden edge.
- [ ] Lane 3. Plant `import claude_agent_sdk` in `qma2/wire.py` in a scratch copy and run `lint-imports`. Save `u0-contract-sdk.log`. Pass when the contract fails and names `qma2.host.claude` as the only allowed importer.
- [ ] Lane 4. Plant `import qma2.money` in `qma2/host/__init__.py` in a scratch copy and run `lint-imports`. Save `u0-contract-host.log`. Pass when the contract fails on the host ban.
- [ ] Lane 5. Run the doctor command from **You see.** Save `u0-doctor.json`. Pass when every A4 line is present and SQLite reads `3.50.4`.
- [ ] Lane 6. Run `uv lock --check` in `qmx-agents/` and list the installed `claude_agent_sdk/_bundled` directory. Save `u0-pins.log`. Pass when the lock check passes and the bundled CLI binary exists.
- [ ] Lane 7. Run `python -m pytest packages tests --collect-only -q` in `qmx-agents/`. Save `u0-sweep.log`. Pass when no collected path contains `qma-v2`.
- [ ] Lane 8. Run `python -c "import qma2, sys; assert 'claude_agent_sdk' not in sys.modules and 'agents' not in sys.modules"`. Save `u0-no-sdk.log`. Pass when the assertion holds.
- [ ] Lane 9. Run `python -c "import agents; print(agents.__file__)"` in the qmx-agents venv. Save `u0-agents-name.log`. Pass when the path is inside the `openai-agents` site-packages folder (H3 section 5 watch item).
- [ ] Lane 10. Run `scripts/dev/qma_callers.py --json` at trunk and head. Save `u0-callers.log`. Pass when both outputs are identical.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. Wall time of `just ci`, plus the cold import time of `qma2` and the doctor run time that the diff adds.
- [ ] Probe. Run `just ci` at trunk, then at head, under the lock. Run `python -X importtime -c "import qma2"` and the doctor command five times each, interleaved with a trunk `import qmx_control` baseline.
- [ ] Baseline. Record the trunk `just ci` wall time first.
- [ ] Rule. Fail when head `just ci` exceeds trunk by more than 120 s, when `import qma2` exceeds 300 ms, or when the doctor run exceeds 2 s.

**Review gate.** None. U0 is not review-gated.

**Merge.**
- [ ] Coordinator's clean verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The coordinator merges with `gh pr merge <number> --merge` and fixes the brief template from what the pilot showed.

## Run one live Claude turn on his subscription (U1)

**Depends on.** U0.

**Files.**
- [ ] Create `qmx-agents/packages/qma-v2/src/qma2/host/__init__.py`, `host/__main__.py`, `host/link.py` and `host/claude.py`.
- [ ] Create `src/qma2/harness.py` (minimal `_ThreadActor` and `_HostSupervisor`), `secrets.py` (`host_env`, `tool_env`), `accounts.py` (`claude_status`, ported from `native_boundary.check_environment` and the preflight) and `money.py` (the rule).
- [ ] Create `qmx-agents/packages/qma-v2/scripts/live_turn.py` (HARNESS call site 3) and `scripts/probes.py`.
- [ ] Create `qmx-agents/packages/qma-v2/docs/native-recipe.md`, a reference copy of the kept parts of `native_claude.py` and `native_boundary.py` with their `file:line` at `4eac8f69` (H3 section 3). Create `tests/test_host_claude.py` (the fake-client pattern from `qma-daemon/tests/test_native_sessions.py`), `tests/test_secrets_env.py`, `tests/test_money_rule.py` and `tests/test_supervisor.py`.

**Build.**
- [ ] Write the stub gate in `_ThreadActor.gate`. Money rule first, then allow `Read`, `Glob` and `Grep`, then deny everything else with "approvals arrive in U2". `WebSearch` and `WebFetch` stay denied, because VERDICT V5.5 makes them ask.
- [ ] Write `host/claude.py` with `setting_sources=[]`, `strict_mcp_config=True`, an explicit `cli_path` to the bundled CLI, an in-code PreToolUse hook that calls the link, and `can_use_tool` that denies any `tool_use_id` with no QMX Pending entry (VERDICT V2.2, V2.4). `mirror()` sends only `plan` or `default` (V2.1). `_pre_tool_use` catches every exception and returns deny.
- [ ] Write `_HostSupervisor.spawn` to create the host, assign it to a Job Object (process group on POSIX), then write `Spawn` (V3.6). The host runs `os.dup2(2, 1)` and gives children `stdin=DEVNULL` (V3.5). The env comes from the per-OS allow-list in `secrets.host_env` (V5.2). Write `scripts/probes.py` to record the A8 probes, the SDK hook-matcher timeout against the QMX hook budget (V2.3), and whether `model_usage` is per query or cumulative (V4.4). It writes JSON.

**You see.**
- [ ] `uv run --project qmx-agents/packages/qma-v2 python scripts/live_turn.py` prints `turn.started`, `tool.started Glob`, `tool.finished`, text deltas, then `turn.finished` with `model_usage`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_host_claude.py` gains cases for deny-on-exception, unknown `tool_use_id`, mode mirroring and an unknown advertised tool refused at `Started`. `tests/test_secrets_env.py` asserts `host_env` drops `ANTHROPIC_*`, `CLAUDE_CODE_*` and `QMX_*`. Run `uv run --no-sync python -m pytest tests -q -n 2 --basetemp D:/Temp/pytest-u1` in the package. Then run `just ci` under the lock and save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents. Before lane 1, stop and ask the operator to run `/login` himself with `CLAUDE_CONFIG_DIR` set to QMX's claude-home, using the bundled CLI path that doctor prints. Log his answer in `gates.md`.
- [ ] Lane 1. Regression lane against trunk. Trunk has no turn path, so record that and run `live_turn.py` with "List the files here and summarise README.md" at head. Save `u1-turn.log`. Pass when `turn.finished` arrives with `model_usage` present and Glob and Read tool events in between.
- [ ] Lane 2. Run `claude auth status` with `CLAUDE_CONFIG_DIR` set to QMX's claude-home. Save `u1-auth.log`. Pass when it reports `loggedIn`, `authMethod` `claude.ai` and that config directory.
- [ ] Lane 3. Send "Run dir with Bash". Save `u1-bash-denied.log`. Pass when `tool.finished` is denied with the QMX reason "approvals arrive in U2" and no shell process started (VERDICT V6.3).
- [ ] Lane 4. Send "Read" plus a path inside the money surface that doctor lists. Save `u1-money-read.log`. Pass when the call is denied with the money reason before any hook runs.
- [ ] Lane 5. Compare the in-code PreToolUse fire count in the host log with the `tool.started` count in `u1-turn.log`. Save `u1-hook-count.log`. Pass when the counts are equal and above zero.
- [ ] Lane 6. Start a second thread, kill the first host's PID mid-turn, and let the second finish. Save `u1-kill.log`. Pass when the second thread reaches `turn.finished`, the first shows `failed`, and `Get-Process` shows the killed host's CLI PID gone.
- [ ] Lane 7. Run `rg` for the token value pattern over the QMX home, excluding `claude-home/`, plus every log and trace. Save `u1-token-grep.log`. Pass when there are zero hits (A6, V5.7).
- [ ] Lane 8. Run `scripts/probes.py` and copy its JSON into `D:/QMX-worktrees/qma2-ship/probes.md`. Save `u1-probes.json`. Pass when every probe named in **Build.** has a recorded value.
- [ ] Lane 9. Put a `.mcp.json` that declares a server named `qmx` in the lane cwd and send one turn. Save `u1-mcp-pin.log`. Pass when the init tool list holds no tool from that file (V2.4).
- [ ] Lane 10. Set the thread mode to `acceptEdits` and send "Write hello.txt". Save `u1-mode-mirror.log`. Pass when the spawn log shows `permission_mode` `default` and the Write is denied.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. Time to first token, from `turn.started` to the first text delta, and the working set of the host plus its Claude CLI (A7). Trunk has no turn path, so these are absolute budgets on the work the diff adds.
- [ ] Probe. Sample `Get-Process` for the host and CLI PIDs every second during lanes 1, 3 and 9, and take TTFT from those three logs. No extra turns.
- [ ] Baseline. Record that trunk has no turn path and no host process.
- [ ] Rule. Fail when spawn to `Started` exceeds 10 s or the host Python process exceeds 200 MB. Record the CLI working set as the A7 measurement in `probes.md`. Report TTFT without a gate.

**Review gate.** None. U1 is not review-gated.

**Merge.**
- [ ] Coordinator's clean verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The coordinator merges with `gh pr merge <number> --merge`.

## Give him a console with store, resume and an operator login (U1b)

**Depends on.** U1.

**Files.**
- [ ] Create `qmx-agents/packages/qma-v2/src/qma2/store.py` (`threads`, `segments`, `turns`, `items`, operator sessions, one `Writer` thread) and `operator.py`.
- [ ] Create `qmx-agents/packages/qmx-control/src/qmx_control/agent_ops.py` and `console/index.html`.
- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/server.py`, `__main__.py` and `service.py`.
- [ ] Create `qmx-agents/packages/qma-v2/scripts/drive.py`, a JSON-output CLI over REST and SSE, and `.claude/skills/verify-qmx-agents/SKILL.md` made with `/create-verification-skill`. Create `tests/test_store.py`, `tests/test_projection.py` and `qmx-control/tests/test_operator.py`.

**Build.**
- [ ] Give `Op` a `who` field with `OPERATOR`, `CLIENT` and `AGENT`. Convert the 52 rows mechanically. Derive the MCP export and the agent catalog from `who`, and make the agent catalog an explicit allow-list that leaves out `run_job`, `runs_start_remote`, `runs_resume`, the `apps_*` writes, `settings_put`, `backup_*` and `sessions_append` (VERDICT V1.1).
- [ ] Move operator pairing into this PR (VERDICT V6.2). `start` passes the code to `serve` over stdin and opens `/console/pair`. Sessions are HMAC-bound with a key held as an `OperatorSecretRef` (V1.4). Each pairing posts a `needs_you` block.
- [ ] Add the rows `threads_create`, `threads_list`, `threads_send`, `GET /api/threads/{id}/live` (snapshot first, keepalive every 10 s, via `fastapi.sse`), the console chat panel and the Claude sign-in panel.
- [ ] Make projection idempotent. Set `items.block_seq` after `sessions_append` returns and re-project only rows where it is null (V3.4). Resume after a restart uses `segment.sdk_session_id`. A full `max_live_hosts` raises `no_host_slot` and names the pinned threads (V6.4).

**You see.**
- [ ] The console at `http://localhost:8766/console` shows `Claude: signed in (Max)`, streams a reply with Glob and Read cards, and still answers "what did I ask you first?" after a restart.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_projection.py` gains a crash-between-writes case that ends with one block per item. `qmx-control/tests/test_operator.py` gains a forged-row case and a bearer-on-OPERATOR case. Run the qma-v2 and qmx-control suites with `-n 2`. Then run `just ci` under the lock and save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents.
- [ ] Lane 1. Regression lane against trunk. Create a session, append three blocks and read `GET /api/events/sessions` at trunk and head. Trunk has no console, so also gate one console chat turn at head. Save `u1b-regression.log`. Pass when the SSE payloads match byte for byte and the head turn finishes.
- [ ] Lane 2. Run `start`, follow the pairing page, and open the console. Save `u1b-paired.png`. Pass when the console shows `Claude: signed in (Max)` and the session list shows the pairing notice.
- [ ] Lane 3. Type "list the files here and summarise README" in the console. Save `u1b-chat.png`. Pass when text streams and Glob and Read cards appear.
- [ ] Lane 4. Stop and start the host, then type "what did I ask you first?". Save `u1b-resume.png`. Pass when the reply quotes the first prompt.
- [ ] Lane 5. Call every `who=OPERATOR` route with the bearer control token through `drive.py`. Save `u1b-operator-403.log`. Pass when every call returns 403.
- [ ] Lane 6. List `tools/list` on `/mcp` and the agent catalog from the host log. Save `u1b-catalog.log`. Pass when neither holds an OPERATOR row and the catalog holds none of the V1.1 exclusions.
- [ ] Lane 7. Insert a forged operator-session row into `harness.db` and call an OPERATOR route with a cookie naming it. Save `u1b-forged.log`. Pass when the call is refused.
- [ ] Lane 8. Stop the host mid-turn, restart, and count blocks per item source key. Save `u1b-reproject.log`. Pass when no source key has two blocks and no item has a null `block_seq`.
- [ ] Lane 9. Set `max_live_hosts` to 1 and start a second thread. Save `u1b-no-slot.png`. Pass when the console shows `no_host_slot` naming the first thread.
- [ ] Lane 10. Attach `drive.py` to `/api/threads/{id}/live` and stay idle. Save `u1b-live-sse.log`. Pass when the first event is the snapshot and a keepalive arrives within 10 s.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. Delay from a host event to the SSE client, and the `harness.db` writer time for 1,000 item writes. Trunk has neither, so these are absolute budgets.
- [ ] Probe. `drive.py` timestamps each live event against the host log over lanes 3 and 8. A script writes 1,000 items through `Store` five times, interleaved with the trunk `sessions_append` loop of 1,000 blocks.
- [ ] Baseline. Record the trunk `sessions_append` time for 1,000 blocks first.
- [ ] Rule. Fail when p95 event-to-client delay exceeds 100 ms or 1,000 item writes take longer than the trunk 1,000-block loop.

**Review gate.** The operator reviews before merge.
- [ ] Copy lane 2, 3, 4 and 9 screenshots into `tracker/qma-v2/review/U1b-review-<slug>.png`. No screen-recording tool is installed, so the video is a numbered screenshot sequence of the flow plus its drive.py event log. It shows pairing, a chat turn and the restart. Save it under `tracker/qma-v2/review/U1b-review/`.
- [ ] Post the screenshots and the video in chat. Stop at merge-ready. Wait for the operator's click.

**Merge.**
- [ ] Coordinator's clean verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The operator clicks merge, or the coordinator runs `gh pr merge <number> --merge` on his written go.

## Ask him before risky tool calls on the Claude engine (U2)

**Depends on.** U1b.

**Files.**
- [ ] Create `qmx-agents/packages/qma-v2/src/qma2/policy.py`. Edit `money.py`, `store.py` (`approvals`, `rules`), `harness.py` (`_RuleBook`, `answer`, `approvals`) and `host/claude.py`.
- [ ] Edit `qmx-control/src/qmx_control/agent_ops.py`, `server.py` and `console/index.html`.
- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py` to import from `qma2.money`, and turn `qmx-agents/packages/qmx-agents/src/qmx_agents/guards/money_path.py` into a re-export shim. Create `tests/test_policy.py`, `tests/test_money.py` and `tests/test_approvals.py`.

**Build.**
- [ ] Write `policy.decide` on the closed `ToolEffect` (A1), Claude rule syntax, compound-command split, the `shell` family (V5.1), modes without `auto`, caps, protected paths, and rejection of ADS, UNC and device paths (VERDICT A17). WebFetch asks per domain and WebSearch asks (V5.5). `suggest_rule` offers exact-command rules for interpreters (V5.6).
- [ ] Write `money.classify` for proposals by identity only (A2), QMX-op argument scanning (V1.2), QMX state files as protected money state (V1.5), and one `recheck_money(call)` after every input change (V2.6).
- [ ] Add `approvals_answer` and `threads_set_mode` as OPERATOR rows, the `approvals` topic, and console cards with Allow once, Allow for this chat, Always allow, Deny, and Deny and stop. Add the AskUserQuestion card, the plan approval card, and an expiry window with a wait time and an expire button (V6.4).
- [ ] Ask handlers run as child tasks that message the actor (V3.2). On Pending, the host returns `ask` with the hook-updated input (V3.3). Ignore project `<cwd>/.qmx/` allow rules until the operator trusts that root (V1.6).

**You see.**
- [ ] "delete notes.txt" shows an approval card, Allow once deletes the file, and the console banner reads `Money guarantee: tool-level (same Windows user)`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_policy.py` gains the H6 table, the precedence case "act tokens beat read tokens", and a `MONEY_ACT` row for every mode including bypass. `tests/test_money.py` gains a remote `propose_order` denied as `MONEY_ACT`. Run the qma-v2, qmx-control and qmx-apps suites with `-n 2`. Then run `just ci` under the lock and save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents.
- [ ] Lane 1. Regression lane against trunk. With rules `deny: Bash(git push *)`, `ask: Bash(rm *)` and `allow: Bash(npm test *)`, send `git push`, `cd x && rm -f y` and `npm test` to vanilla Claude Code and to QMX at head. Trunk QMX has no policy, so the vanilla column stands in for it. Save `u2-h6.log`. Pass when QMX gives deny, ask and allow, the same as vanilla.
- [ ] Lane 2. Send "delete notes.txt" and click Allow once. Save `u2-allow-once.png`. Pass when the card appears and the file is gone afterwards.
- [ ] Lane 3. Click Always allow on `npm run lint`, then send it in a new chat. Save `u2-always.png`. Pass when the new chat runs it with no card and the rule shows in the rules list (H7).
- [ ] Lane 4. Switch to plan mode and send "write plan.txt". Save `u2-plan.png`. Pass when the write is blocked.
- [ ] Lane 5. Send "Use python to read the qmx/ctrader password from the keyring", then the same through `C:/Program Files/Git/bin/bash.exe -c` (V6.6). Save `u2-money.png`. Pass when both are refused with "Money is read-only for agents", or the git-bash spelling is recorded as the stated speed-bump limit.
- [ ] Lane 6. Call `POST /api/approvals/{id}` with the bearer token, then list `/mcp` tools. Save `u2-403.log`. Pass when the call returns 403 and neither `approvals_answer` nor `threads_set_mode` is listed.
- [ ] Lane 7. Start the host from a shell where `ANTHROPIC_BASE_URL` is set, approve `Get-ChildItem Env:`, and read the output. Save `u2-env.log`. Pass when it lists no `ANTHROPIC_*`, `CLAUDE_CODE_*` or `QMX_*` name.
- [ ] Lane 8. Set the approval window to 60 s, send "delete b.txt" and wait. Save `u2-expired.png`. Pass when the card shows its wait time, then expires, and the tool is denied.
- [ ] Lane 9. Send "fetch https://example.com, then https://example.com/a, then https://example.org" and allow example.com for this chat. Save `u2-webfetch.png`. Pass when cards appear for example.com and example.org only.
- [ ] Lane 10. Run `python -c "import qmx_apps.supervisor as s, qma2.money as m; assert s.check_descriptor is m.check_descriptor"`. Save `u2-money-shim.log`. Pass when the assertion holds.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. Gate round trip per tool call, from host `Gate` to `Verdict`, with no hooks configured.
- [ ] Probe. A fake host sends 200 `Gate` messages for `Read` to the real actor, five runs at head interleaved with five runs at the U1b merge SHA, whose stub gate is the baseline.
- [ ] Baseline. Record the U1b stub-gate p95 first.
- [ ] Rule. Fail when the head p95 exceeds 5 ms or exceeds the U1b p95 by more than 3 ms.

**Review gate.** The operator reviews before merge.
- [ ] Copy lane 2, 3, 5 and 8 screenshots into `tracker/qma-v2/review/U2-review-<slug>.png`. No screen-recording tool is installed, so the video is a numbered screenshot sequence of the flow plus its drive.py event log. It shows an approval card answered three ways. Save it under `tracker/qma-v2/review/U2-review/`.
- [ ] Post the screenshots and the video in chat. Stop at merge-ready. Wait for the operator's click.

**Merge.**
- [ ] Coordinator's clean verdict and the extra `opus` verifier's verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The operator clicks merge, or the coordinator runs `gh pr merge <number> --merge` on his written go.

## Run the OpenAI engine on an OpenRouter key (U4a)

**Depends on.** U1b.

**Files.**
- [ ] Create `qmx-agents/packages/qma-v2/src/qma2/host/openai.py` (`LinkSession` over items, `PromptBuilder` with `prompt_cache_key`, a local trace processor with a startup assertion) and `host/tools.py` (the Claude-shaped kit and `ProcessTable`).
- [ ] Edit `secrets.py` (keyring, ephemeral and age-file backends) and `accounts.py` (`ApiKeyAccount` routes). Edit `model.py` to remove `TurnInput.attachments` (A9). Create `tests/test_host_openai.py` and `tests/test_tools_kit.py`.

**Build.**
- [ ] Ship `Read`, `Write`, `Edit`, `Glob`, `Grep`, `Bash` (git-bash when present), `PowerShell`, `WebFetch`, `WebSearch`, `TodoWrite`, `AskUser` and `Skill`, each wrapped by `gated`, with a `BUILTIN_EFFECTS` row for every name (V5.1). Use no SDK hosted tools, `ShellTool`, `ApplyPatchTool` or SDK approvals.
- [ ] Store reasoning items verbatim with `include=["reasoning.encrypted_content"]` (V5.3). Set `max_turns` from QMX settings, because the SDK default is 10 (H1 fact 11).
- [ ] Refuse Claude and GPT model ids on an API key, including `anthropic/*` and `openai/*` on OpenRouter (V4.1). Emit usage events for every response (H18).

**You see.**
- [ ] `drive.py send --engine openai --model <id>` with "List the files here and summarise README.md" streams text with Glob and Read events and ends in `turn.finished`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_host_openai.py` gains a fake-model run proving every kit call passes through the link gate, and a startup assertion that fails when an OpenAI trace exporter is registered. Run the qma-v2 suite with `-n 2`. Then run `just ci` under the lock and save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents. Before lane 1, stop and ask the operator to store his OpenRouter key himself in the OS secret store under `qmx/openrouter` (Credential Manager on this Windows laptop). Choose one OpenRouter model whose `supported_parameters` list `tools` and implicit caching, and record its id in `decisions.tsv`.
- [ ] Lane 1. Regression lane against trunk. Trunk has no OpenAI engine, so record that, run the **You see.** turn on the OpenRouter model at head, and repeat the U1 turn on Claude at head. Save `u4a-smoke.log`. Pass when both engines reach `turn.finished` with Glob and Read events.
- [ ] Lane 2. Send "create hello.txt containing hi, then read it back". Save `u4a-write-read.log`. Pass when the file holds `hi` and both calls show in the log.
- [ ] Lane 3. Send "Run dir in PowerShell" with no allow rule. Save `u4a-policy.log`. Pass when the verdict and reason match the Claude engine's for the same call at this head.
- [ ] Lane 4. Send "Read" plus the money-surface path from U1 lane 4. Save `u4a-money.log`. Pass when the call is denied with the money reason.
- [ ] Lane 5. Clear the DNS cache, run lane 2 again, then read `Get-DnsClientCache`. Save `u4a-no-trace.log`. Pass when no entry names `api.openai.com` and the host log shows the trace assertion passed.
- [ ] Lane 6. Request `anthropic/claude-opus-5.5` and `openai/gpt-5.6` on the OpenRouter key through `drive.py`. Save `u4a-family.log`. Pass when both are refused before any HTTP request.
- [ ] Lane 7. Add `deny: Bash(echo *)` and ask for `echo hi` in Bash and then in PowerShell. Save `u4a-shell-family.log`. Pass when both are denied by that one rule.
- [ ] Lane 8. Allow `Get-ChildItem Env:` once and read the output. Save `u4a-env.log`. Pass when the V5.2 Windows names are present and no key, `ANTHROPIC_*` or `QMX_*` name is.
- [ ] Lane 9. Run a two-turn tool-using chat on a reasoning model and kill the host between turns. Save `u4a-reasoning.log`. Pass when turn 2 resumes from items and the stored reasoning items are byte-identical to the response.
- [ ] Lane 10. Run `rg` for the key value over the lane home, logs and traces. Save `u4a-key-grep.log`. Pass when there are zero hits.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. Cache-read ratio, cached tokens over prompt tokens, on turns 2 to 5 of a five-turn OpenRouter chat (H10).
- [ ] Probe. Run the five-turn chat twice and read `prompt_tokens_details.cached_tokens` from the usage events.
- [ ] Baseline. Trunk has no OpenAI engine. Record the ratio on turn 1 as the uncached floor.
- [ ] Rule. Fail when the ratio from turn 2 is under 80% on a provider that reports cache. On a provider that does not, record that and fail when TTFT p50 exceeds 10 s.

**Review gate.** None. U4a is not review-gated.

**Merge.**
- [ ] Coordinator's clean verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The coordinator merges with `gh pr merge <number> --merge`.

## Add hooks, config home, instructions, skills, agents and memory on Claude (U3)

**Depends on.** U2.

**Files.**
- [ ] Create `qmx-agents/packages/qma-v2/src/qma2/hooks.py` and `config.py`. Edit `harness.py` and `host/claude.py`.
- [ ] Edit `qmx-control/src/qmx_control/server.py` (`settings_get` and `settings_put` as OPERATOR rows, A4) and `console/index.html` (trust prompt, child session cards). Create `tests/test_hooks.py` and `tests/test_config.py`.

**Build.**
- [ ] Run Claude-format command hooks in qmx-control for PreToolUse, PostToolUse, PermissionRequest, UserPromptSubmit and Stop. The actor fires SessionStart, SessionEnd and PostCompact itself.
- [ ] Load layers from `~/.qmx/config/` and `<cwd>/.qmx/`, never `<cwd>/.claude/` (A4). Ignore project hooks until he trusts the root (V1.6). Materialise the Claude plugin directory with no hooks.
- [ ] Send `ProjectContext` (CLAUDE.md plus AGENTS.md) as the first user message, without MEMORY.md on the Claude engine (V5.4). Pass agents as `AgentDefinition`. Gate sub-agent calls with `agent_path` and show child sessions. List MCP descriptors at segment start and deny unknown names (V2.5). Refuse the `qmx` name and the `qmx-mcp-*` servers in agent MCP config (V6.5).

**You see.**
- [ ] A hook that exits 2 on `rm -rf` blocks "rm -rf build" in the console and shows the hook's message.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_hooks.py` gains exit 0, exit 2, `updatedInput`, `additionalContext` and timeout cases. `tests/test_config.py` gains the trust case and the `qmx-mcp-data` refusal. Run the qma-v2 and qmx-control suites with `-n 2`. Then run `just ci` under the lock and save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents.
- [ ] Lane 1. Regression lane against trunk. Put the same exit-2 hook in a scratch project's `.claude/settings.json` for vanilla Claude Code and in `<cwd>/.qmx/settings.json` for QMX, then send "rm -rf build" to both. Trunk QMX has no hooks, so vanilla stands in. Save `u3-h8.png`. Pass when both block the call and QMX shows the hook's message.
- [ ] Lane 2. Add a PreToolUse hook that rewrites `updatedInput` and adds `additionalContext`, then ask the agent to repeat the context. Save `u3-rewrite.log`. Pass when the rewritten input runs and the reply quotes the context.
- [ ] Lane 3. Use a repo with one rule only in AGENTS.md and one only in CLAUDE.md, and send a prompt that tests both. Save `u3-h9.png`. Pass when both rules are obeyed.
- [ ] Lane 4. Put a skill in `~/.qmx/config/skills/` and invoke it by name. Save `u3-skill.log`. Pass when the init list holds it and it runs.
- [ ] Lane 5. Send "Remember I prefer tabs", then in a new chat ask for an indented snippet. Save `u3-memory.png`. Pass when the new chat uses tabs.
- [ ] Lane 6. Run a `reviewer` agent from `~/.qmx/config/agents` with `tools: Read, Grep` and ask it to write a file. Save `u3-reviewer.png`. Pass when it shows as a child card, its Write is denied, and the decision log carries its `agent_path`.
- [ ] Lane 7. Compare the init skill and agent names with a read-only listing of his `~/.claude/skills` and `~/.claude/agents`. Save `u3-isolation.log`. Pass when no name overlaps.
- [ ] Lane 8. Open an untrusted repo whose `.qmx/settings.json` has a hook, send a turn, trust the root, then send another. Save `u3-trust.png`. Pass when the hook fires only after trust.
- [ ] Lane 9. Add `qmx-mcp-data` and a server named `qmx` to the agent MCP config and start a thread. Save `u3-mcp-refused.log`. Pass when config load refuses both with named reasons.
- [ ] Lane 10. Use a repo whose `.claude/settings.json` hook writes a marker file, then send a Bash-free turn there. Save `u3-claude-dir.log`. Pass when the marker file does not exist.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. Gate round trip per tool call with one PreToolUse command hook that exits 0 at once.
- [ ] Probe. The U2 fake-host probe, 200 `Gate` messages, five runs with the hook and five without, interleaved.
- [ ] Baseline. Record the no-hook p95 at the U2 merge SHA first.
- [ ] Rule. Fail when the hook run's p95 exceeds the hook process's own start-to-exit time plus 10 ms.

**Review gate.** None. U3 is not review-gated.

**Merge.**
- [ ] Coordinator's clean verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The coordinator merges with `gh pr merge <number> --merge`.

## Let him add a provider key and get the same behaviour on OpenAI (U4b)

**Depends on.** U2, U3 and U4a.

**Files.**
- [ ] Edit `qmx-agents/packages/qma-v2/src/qma2/host/openai.py`, `host/tools.py` and `accounts.py` (`put_api_key`).
- [ ] Edit `qmx-control/src/qmx_control/agent_ops.py`, `server.py` (the accounts OPERATOR rows) and `console/index.html` (the "Add provider key" form and an engine picker). Create `tests/test_parity_openai.py`.

**Build.**
- [ ] Write the key form behind the operator principal. The key goes to the keyring through `secrets.py` and never into a response, block, log or trace.
- [ ] Fire UserPromptSubmit before `Runner.run` and Stop on the final output, where `decision: block` re-enters the loop. Send `ProjectContext` with MEMORY.md as the first user message on this engine (H9, H15).
- [ ] Load skills from the same QMX directories and expose them through the `Skill` tool (H14).

**You see.**
- [ ] He picks an OpenRouter model in the console and the "delete notes.txt" card, the hook block and the money refusal look the same as on Claude.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_parity_openai.py` replays the U2 policy table and the U3 hook cases through a fake OpenAI model with no policy code in `host/`. Run the qma-v2 and qmx-control suites with `-n 2`. Then run `just ci` under the lock and save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents.
- [ ] Lane 1. Regression lane against trunk. Run the same five-step refactor script in vanilla Claude Code and in a QMX OpenRouter chat (H5). Trunk QMX has no key form, so vanilla stands in. Save `u4b-h5.png`. Pass when both change the same files, the tests give the same result, and QMX shows the edits as diffs.
- [ ] Lane 2. Submit the key form with the generated test value `sk-or-v1-qmxtest0000`, then call the same route with the bearer token. Save `u4b-key-form.png`. Pass when the console reports the key as rejected by the provider, the bearer call returns 403, and `rg` finds the value nowhere in the lane home.
- [ ] Lane 3. Send the U2 lane 1 prompts on the OpenAI engine. Save `u4b-h6.log`. Pass when the outcomes are deny, ask and allow.
- [ ] Lane 4. Click Always allow on `npm run lint` in a Claude chat, then send it in an OpenAI chat. Save `u4b-h7.png`. Pass when the OpenAI chat runs it with no card.
- [ ] Lane 5. Send "rm -rf build" with the U3 exit-2 hook on the OpenAI engine. Save `u4b-h8.png`. Pass when the call is blocked with the hook's message.
- [ ] Lane 6. Send "delete notes.txt" on the OpenAI engine and click Allow once. Save `u4b-approval.png`. Pass when the card matches the Claude card and the file is gone.
- [ ] Lane 7. Send the U2 lane 5 keyring prompt on the OpenAI engine. Save `u4b-money.png`. Pass when it is refused with "Money is read-only for agents".
- [ ] Lane 8. Repeat U3 lanes 3 and 5 on the OpenAI engine. Save `u4b-h9-h15.log`. Pass when both rules and the tabs preference are followed.
- [ ] Lane 9. Invoke the U3 skill by name on the OpenAI engine. Save `u4b-skill.log`. Pass when the `Skill` tool returns its body and the agent follows it.
- [ ] Lane 10. Add a UserPromptSubmit hook that exits 2 on the word "forbidden" and send "forbidden word" on both engines. Save `u4b-prompt-hook.log`. Pass when both engines block the prompt with the hook's message.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. Cache-read ratio on turns 2 to 10 of a ten-turn OpenRouter chat with `ProjectContext` present (H10).
- [ ] Probe. Run the ten-turn chat at the U4a merge SHA and at head, interleaved, on the same model.
- [ ] Baseline. Record the U4a merge SHA ratio first.
- [ ] Rule. Fail when the head ratio from turn 2 is under 80% where the provider reports cache, or more than 5 points under the U4a ratio.

**Review gate.** The operator reviews before merge.
- [ ] Copy lane 1, 2, 6 and 7 screenshots into `tracker/qma-v2/review/U4b-review-<slug>.png`. No screen-recording tool is installed, so the video is a numbered screenshot sequence of the flow plus its drive.py event log. It shows an OpenRouter chat with an approval card and the money refusal. Save it under `tracker/qma-v2/review/U4b-review/`.
- [ ] Post the screenshots and the video in chat. Stop at merge-ready. Wait for the operator's click.

**Merge.**
- [ ] Coordinator's clean verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The operator clicks merge, or the coordinator runs `gh pr merge <number> --merge` on his written go.

## Show usage and warn before a model switch (U5)

**Depends on.** U4b.

**Files.**
- [ ] Create `qmx-agents/packages/qma-v2/src/qma2/router.py`. Edit `accounts.py`, `store.py` (`usage`, `limits`, switch quotes), `harness.py` (`quote_switch`, `switch`, `usage`) and `config.py` (profiles).
- [ ] Edit `qmx-control/src/qmx_control/server.py` and `console/index.html` (usage page, switch pop-up, profile picker). Create `tests/test_router.py` and `tests/test_usage.py`.

**Build.**
- [ ] Probe the SDK `get_usage` control request first and record the result in `probes.md` (V4.3). Label the background cap "best effort" unless the probe succeeds.
- [ ] Key usage rows on the result message id (V4.4). Lock out per account, and expire limit snapshots at `resets_at` (V4.2). Give each background turn a token budget checked from usage rows (V4.3).
- [ ] Store quotes server-side and reference them by id (VERDICT Noted A22). Refuse a stale or unknown quote. Apply the family guard in `router.pick`, `quote_switch` and the account model list (V4.1). Label Claude window numbers "as of the last QMX turn" (A9). Show the money-guarantee line from `doctor`.

**You see.**
- [ ] The usage page shows the Claude 5-hour bar with its reset time, and switching a Claude chat to an OpenRouter model pops "this will rebuild the cache, about N tokens".

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_router.py` gains the background-cap, lockout-per-account and family-guard cases. `tests/test_usage.py` gains dedupe by message id. Run the qma-v2 and qmx-control suites with `-n 2`. Then run `just ci` under the lock and save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents.
- [ ] Lane 1. Regression lane against trunk. Trunk has no usage page, so record that, send one Claude turn at head, and open the usage page. Save `u5-usage.png`. Pass when it shows the 5-hour percent, the reset time, and the label "as of the last QMX turn".
- [ ] Lane 2. Compare QMX usage rows with the Claude `ResultMessage` usage and the OpenRouter `GET /api/v1/key` usage delta for one turn each. Save `u5-h18.log`. Pass when both match within 1%.
- [ ] Lane 3. Switch a Claude chat to the OpenRouter model, confirm, and ask "what did I say first?". Save `u5-switch.png`. Pass when the pop-up names a token count and the reply quotes the first prompt.
- [ ] Lane 4. Take a quote, send a turn, then switch with the old quote id. Save `u5-stale-quote.log`. Pass when the switch is refused.
- [ ] Lane 5. Switch with a quote id that QMX never issued. Save `u5-forged-quote.log`. Pass when the switch is refused.
- [ ] Lane 6. Set the background cap to 0% and start a background chat. Save `u5-background.png`. Pass when it runs on OpenRouter and the cap shows its "best effort" label unless `get_usage` was proven.
- [ ] Lane 7. Ask `quote_switch` for `anthropic/claude-opus-5.5` on the OpenRouter account. Save `u5-family.log`. Pass when the quote is refused with the family reason.
- [ ] Lane 8. Set a project setting that overrides a user setting, then pick a profile. Save `u5-profile.png`. Pass when the project value wins and the profile changes model, effort and mode in one click (H16).
- [ ] Lane 9. Insert a limit row whose `resets_at` is in the past and reload the usage page. Save `u5-expired-limit.log`. Pass when no lockout shows for that window.
- [ ] Lane 10. Change effort mid-chat on both engines. Save `u5-effort.png`. Pass when the next request carries the new effort and the warning shows while the cache is warm (H12).

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. Router pick latency, and usage page API latency with 10,000 usage rows.
- [ ] Probe. Call `router.pick` 10,000 times, five runs, and call the usage route five times on a seeded home, interleaved.
- [ ] Baseline. Trunk has no router or usage route. Record that.
- [ ] Rule. Fail when pick p95 exceeds 1 ms or the usage route p95 exceeds 200 ms.

**Review gate.** The operator reviews before merge.
- [ ] Copy lane 1, 3, 6 and 8 screenshots into `tracker/qma-v2/review/U5-review-<slug>.png`. No screen-recording tool is installed, so the video is a numbered screenshot sequence of the flow plus its drive.py event log. It shows the usage page and a switch with its warning. Save it under `tracker/qma-v2/review/U5-review/`.
- [ ] Post the screenshots and the video in chat. Stop at merge-ready. Wait for the operator's click.

**Merge.**
- [ ] Coordinator's clean verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The operator clicks merge, or the coordinator runs `gh pr merge <number> --merge` on his written go.

## Compact, steer and interrupt on both engines (U6)

**Depends on.** U4b.

**Files.**
- [ ] Create `qmx-agents/packages/qma-v2/src/qma2/host/compact.py`. Edit `host/openai.py`, `host/claude.py`, `store.py` (`archive_items`) and `harness.py` (`steer`, `interrupt`, `compact`).
- [ ] Edit `qmx-control/src/qmx_control/console/index.html` (stop, steer and compact controls). Create `tests/test_compact.py` and `tests/test_steer.py`.

**Build.**
- [ ] Compact remotely where the provider offers it, else locally from Codex's summary prompt, at 90% of the model window. Fire PreCompact and PostCompact on both engines. Archive items, never delete them.
- [ ] After `compacted` on Claude, re-send `ProjectContext` as a reminder (V5.4).
- [ ] Write steer and interrupt on both adapters. `ProcessTable.kill_all` ends every child process of a turn.

**You see.**
- [ ] Typing "stop and say done" during a 30-second `ping -n 30 localhost` ends the turn with "done", and Task Manager shows no stray process.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_compact.py` gains threshold, focus and archive cases. `tests/test_steer.py` gains steer-before-next-call and kill-tree cases. Run the qma-v2 suite with `-n 2`. Then run `just ci` under the lock and save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents.
- [ ] Lane 1. Regression lane against trunk. Send "/compact focus on the parser" after a short parser discussion in vanilla Claude Code and in a QMX Claude chat. Trunk QMX has no compaction route, so vanilla stands in. Save `u6-h11.log`. Pass when both keep the parser details in the next answer.
- [ ] Lane 2. Fill a 128K OpenRouter model chat until auto-compaction fires, then ask for a rule from CLAUDE.md. Save `u6-auto.png`. Pass when the compaction event shows, the chat continues, and the rule holds. Record the OpenRouter cost.
- [ ] Lane 3. Send "/compact focus on the parser" on the OpenAI engine. Save `u6-focus-openai.log`. Pass when the next answer keeps the parser details.
- [ ] Lane 4. Read the request log after a Claude `compacted` event. Save `u6-claude-reminder.log`. Pass when `ProjectContext` is re-sent once and MEMORY.md does not appear twice.
- [ ] Lane 5. Add PreCompact and PostCompact hooks that log a line and compact on both engines. Save `u6-hooks.log`. Pass when each hook logs once per compaction on each engine.
- [ ] Lane 6. Start `ping -n 30 localhost` on Claude and steer "stop and say done". Save `u6-steer-claude.png`. Pass when the turn ends with "done" within one model call (H3).
- [ ] Lane 7. Repeat lane 6 on the OpenAI engine. Save `u6-steer-openai.png`. Pass when the turn ends with "done" within one model call.
- [ ] Lane 8. Interrupt a running `ping -n 30 localhost` on each engine and read `Get-Process`. Save `u6-no-orphan.log`. Pass when no `ping`, `pwsh` or `bash` child of the host is left.
- [ ] Lane 9. Read the cache-read ratio for two turns after lane 3. Save `u6-cache-after.log`. Pass when the ratio is back at 80% or above by the second turn where the provider reports cache.
- [ ] Lane 10. Count items before and after lane 2 in `harness.db`. Save `u6-archive.log`. Pass when no row was deleted and the compacted rows are marked archived.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. Local compaction time for a history near 100K tokens on the OpenAI engine.
- [ ] Probe. Compact the same seeded history three times at head. Trunk has no compactor.
- [ ] Baseline. Record that trunk has no compactor, and record vanilla Claude Code `/compact` wall time on a comparable history once.
- [ ] Rule. Fail when the p50 local compaction time exceeds 60 s or twice the vanilla time.

**Review gate.** None. U6 is not review-gated.

**Merge.**
- [ ] Coordinator's clean verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The coordinator merges with `gh pr merge <number> --merge`.

## Give the OpenAI engine helpers, MCP tools and order proposals (U7)

**Depends on.** U6.

**Files.**
- [ ] Edit `qmx-agents/packages/qma-v2/src/qma2/host/openai.py` and `host/tools.py` (`AgentTool`, the background registry, the MCP manager). Edit `harness.py` (`CallOp` grants, `ChildThreadSpec`) and `policy.py` (depth and concurrency caps).
- [ ] Edit `qmx-control/src/qmx_control/agent_ops.py` (`ControlAgentOps`, `BrokerProposals`). Create `qmx-agents/packages/qma-v2/tests/fixtures/echo_mcp.py`, `tests/test_agent_tool.py` and `tests/test_callop.py`.

**Build.**
- [ ] Write `AgentTool` with depth 3, concurrency 6, mode inheritance that never escalates, and a background registry with SendMessage, wait, list and interrupt. Child sessions show as child cards.
- [ ] Bind each `CallOp` grant to name plus canonical args digest, consume grants FIFO, and run the op with the stored allowed input (V3.1).
- [ ] Confine agent thread ops. A child thread gets `origin=AGENT`, the caller as parent, and the lower of the two modes. Thread verbs work only in the caller's lineage. QMX offers no ALLOW_ALWAYS rule for `mcp__qmx__threads_*` (V1.3). Wire the proposal tool from `money_proposal_spec(sink)` to write an unsigned proposal (A2). Reap an idle host only when no background child is alive (VERDICT A28).

**You see.**
- [ ] "Buy 1 EURUSD" produces an unsigned proposal in Portfolio and the agent says it needs his signature.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_callop.py` gains replayed-id, swapped-args and FIFO cases. `tests/test_agent_tool.py` gains the depth-4 refusal and the cap of 6. Run the qma-v2 and qmx-control suites with `-n 2`. Then run `just ci` under the lock and save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents.
- [ ] Lane 1. Regression lane against trunk. Run the U3 `reviewer` agent on Claude and on the OpenAI engine (H13). Trunk has no OpenAI sub-agents, so the Claude run is the comparison. Save `u7-h13.png`. Pass when both run read-only and show as child cards.
- [ ] Lane 2. Ask for a helper that starts a helper that starts a helper that starts a helper, on both engines. Save `u7-depth.log`. Pass when the fourth level is refused on both.
- [ ] Lane 3. Start a background helper that tries to delete a file. Save `u7-helper-card.png`. Pass when the approval card shows the helper's name.
- [ ] Lane 4. Register `tests/fixtures/echo_mcp.py` as an MCP server with `ask: mcp__echo__echo` and call it on both engines. Save `u7-mcp.log`. Pass when both engines show the card before the call.
- [ ] Lane 5. Send "Buy 1 EURUSD". Save `u7-proposal.png`. Pass when Portfolio lists an unsigned proposal and the agent asks for his signature.
- [ ] Lane 6. Send "Place it now", then call a fixture broker server's own `propose_order`. Save `u7-refusals.log`. Pass when both are refused as `MONEY_ACT` while lane 5's proposal stands.
- [ ] Lane 7. Ask the agent to create a child thread and then send a message to an unrelated thread. Save `u7-lineage.log`. Pass when the child carries `origin=AGENT` and the parent id, and the send to the unrelated thread is refused.
- [ ] Lane 8. Ask the agent to call a QMX op with `qmx/ctrader` inside an argument. Save `u7-op-args.log`. Pass when the call is refused with the money reason (V1.2).
- [ ] Lane 9. Read the OpenAI host's function tool list. Save `u7-catalog.log`. Pass when none of the V1.1 exclusions appears.
- [ ] Lane 10. Set the idle window to 1 minute, start a background helper, and wait. Save `u7-reap.log`. Pass when the host stays while the helper runs and exits one idle window after it finishes.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. Time from an `Agent` tool call to the child's first model request, excluding model time.
- [ ] Probe. A fake model drives 50 nested spawns, five runs at head. Trunk has no `AgentTool`.
- [ ] Baseline. Record that trunk has no `AgentTool`, and record the U6 merge SHA gate round trip as the floor.
- [ ] Rule. Fail when the spawn overhead p95 exceeds 500 ms.

**Review gate.** None. U7 is not review-gated.

**Merge.**
- [ ] Coordinator's clean verdict and the extra `opus` verifier's verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The coordinator merges with `gh pr merge <number> --merge`.

## Keep threads alive for days (U9)

**Depends on.** U5 and U6.

**Files.**
- [ ] Edit `qmx-agents/packages/qma-v2/src/qma2/harness.py` (`export`, `fork`, `archive`, `LockedOut`, idle reaping, restart recovery) and `store.py`.
- [ ] Edit `qmx-control/src/qmx_control/console/index.html` (Export button, thread list, expired card with retry). Create `tests/test_export.py` and `tests/test_recovery.py`.

**Build.**
- [ ] Write `export` as one zip with items, segments, approvals, usage, logs, traces and the Claude JSONL, with `redact` applied (V3.4, V5.7).
- [ ] Probe fork-at-turn on Claude first and record it (VERDICT A28). If the SDK lacks it, fork Claude threads at the latest turn only and say so in the console.
- [ ] On a lockout, a foreground thread waits and offers a switch, and a background thread re-routes at a turn boundary. On restart, expire pending approvals and mark running turns interrupted with a retry.

**You see.**
- [ ] Export downloads one zip, and restarting during an approval shows the card as expired with a retry button.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_export.py` gains a secrets-redaction case. `tests/test_recovery.py` gains pending-to-expired and running-to-interrupted cases. Run the qma-v2 suite with `-n 2`. Then run `just ci` under the lock and save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents.
- [ ] Lane 1. Regression lane against trunk. Fork a two-turn chat after turn 2 and continue both (H4). Trunk has no fork, so record that. Save `u9-fork.png`. Pass when the two histories differ and the original is unchanged.
- [ ] Lane 2. Click Export and list the zip. Save `u9-export.log`. Pass when it holds the transcript, logs, traces and the Claude JSONL.
- [ ] Lane 3. Run `rg` for every stored key, the control token and the Claude token over the unzipped export. Save `u9-export-grep.log`. Pass when there are zero hits.
- [ ] Lane 4. Restart the host while an approval card is open, then click retry. Save `u9-expired.png`. Pass when the card shows expired and retry re-runs the turn.
- [ ] Lane 5. Inject a `rejected` limit event through the test hook on a foreground thread. Save `u9-lockout.png`. Pass when the thread shows LockedOut with the reset time and a switch offer, then returns to Idle after the reset.
- [ ] Lane 6. Inject the same event while a background thread runs. Save `u9-reroute.log`. Pass when its next turn runs on OpenRouter.
- [ ] Lane 7. Open the oldest thread in the U1b lane home and ask about its first turn. Save `u9-old-thread.png`. Pass when the answer quotes it.
- [ ] Lane 8. Set the idle window to 1 minute, wait, then send a turn. Save `u9-reap.log`. Pass when the host exits after the window and the next turn resumes by `sdk_session_id`.
- [ ] Lane 9. Archive a thread and list threads with and without `archived`. Save `u9-archive.log`. Pass when it shows only in the archived list.
- [ ] Lane 10. Read the fork-at-turn probe result. Save `u9-fork-probe.log`. Pass when the result is recorded and the console text matches it.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. Resume latency after an idle reap, from send to first token, against a warm host.
- [ ] Probe. Three warm sends and three post-reap sends on the same thread, interleaved.
- [ ] Baseline. Record the warm-host TTFT first.
- [ ] Rule. Fail when post-reap TTFT exceeds warm TTFT by more than 5 s, or when exporting a 500-turn seeded thread takes over 10 s.

**Review gate.** None. U9 is not review-gated.

**Merge.**
- [ ] Coordinator's clean verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The coordinator merges with `gh pr merge <number> --merge`.

## Let him sign in with ChatGPT (U8)

**Depends on.** U5 and U7.

**Files.**
- [ ] Create `qmx-agents/packages/qma-v2/scripts/chatgpt_probe.py`.
- [ ] Edit `accounts.py` (`chatgpt_begin`, `chatgpt_complete`, refresh with `Rotate`), `host/openai.py` (the GPT base prompt, namespaced function tools, header limits) and `host/tools.py` (`apply_patch` for GPT).
- [ ] Edit `qmx-control/src/qmx_control/console/index.html` (the "Sign in with ChatGPT" button). Create `tests/test_chatgpt.py`.

**Build.**
- [ ] Run the probe first. It does PKCE sign-in, then an Agents SDK run against `https://api.openai.com/v1/responses` with `store=false` and `stream=true`, and records whether `x-codex-*` headers and `responses.compact` are reachable. If the run fails, stop, record the blocker in `gates.md`, and close U8 without code.
- [ ] Send no hosted tools on this route and group function tools in namespaces (H1 fact 17).

**You see.**
- [ ] He clicks "Sign in with ChatGPT", approves in his browser, and a GPT chat works with the same tools and approval cards.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_chatgpt.py` gains refresh-on-expiry and no-backend-api cases against a fake server. Run the qma-v2 suite with `-n 2`. Then run `just ci` under the lock and save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents. Before lane 1, stop and ask the operator to click the sign-in button and approve in his own browser.
- [ ] Lane 1. Regression lane against trunk. Trunk has no ChatGPT route, so record that and send "delete notes.txt" in a GPT chat at head. Save `u8-gpt-chat.png`. Pass when the card appears and Allow once deletes the file.
- [ ] Lane 2. Run `chatgpt_probe.py`. Save `u8-probe.json`. Pass when headers and compaction reachability are recorded as yes or no.
- [ ] Lane 3. Run a three-step subset of the H5 refactor on GPT. Save `u8-h5.log`. Pass when it changes the same files as the U4b vanilla run.
- [ ] Lane 4. Set the stored token expiry in the past and send a turn. Save `u8-refresh.log`. Pass when the turn succeeds with no new sign-in.
- [ ] Lane 5. Clear the DNS cache, run lane 3, then read `Get-DnsClientCache`. Save `u8-no-backend.log`. Pass when no entry names `chatgpt.com`.
- [ ] Lane 6. Run `rg` for the access and refresh tokens over the lane home, logs, traces and an export. Save `u8-token-grep.log`. Pass when there are zero hits.
- [ ] Lane 7. Open the usage page. Save `u8-usage.png`. Pass when it shows the GPT window if the probe found headers, else the label "not reported".
- [ ] Lane 8. Request `openai/gpt-5.6` on the OpenRouter key and GPT on the ChatGPT account. Save `u8-family.log`. Pass when the key route is refused and the account route works.
- [ ] Lane 9. Read the request log of lane 3. Save `u8-request-shape.log`. Pass when every request has `store` false, `stream` true, no hosted tools, and namespaced function tools.
- [ ] Lane 10. Run a two-turn tool-using chat on GPT and kill the host between turns (V5.3). Save `u8-reasoning.log`. Pass when turn 2 resumes with the stored encrypted reasoning items.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. TTFT on the ChatGPT route, and the token refresh round trip.
- [ ] Probe. Three GPT turns and three forced refreshes, interleaved.
- [ ] Baseline. Trunk has no ChatGPT route. Record the U4a OpenRouter TTFT as the reference.
- [ ] Rule. Fail when TTFT p50 exceeds 10 s or a refresh exceeds 2 s.

**Review gate.** None. U8 is not review-gated.

**Merge.**
- [ ] Coordinator's clean verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The coordinator merges with `gh pr merge <number> --merge`.

## Have him sign off the harness in his own words (SIGNOFF)

**Depends on.** Every PR above. If U8 closed without code, SIGNOFF runs without the ChatGPT lane.

**Files.**
- [ ] Create `qmx-agents/packages/qma-v2/docs/handoff/API.md`, the OPERATIONS rows with their `who` value, for the later UI session (UI-NOTES section 7). Create `tests/test_handoff.py`.
- [ ] Create `qmx-agents/packages/qma-v2/docs/handoff/events/`, the event samples recorded during his sign-off.
- [ ] Create `tracker/qma-v2/review/SIGNOFF.md` with his answers and the evidence paths.

**Build.**
- [ ] Remind him in plain words of the money answer he gave on 2026-10-13 (HARNESS A12, which accepts the same-user speed bump until broker credentials move to the trading node or U10 ships). Record in `SIGNOFF.md` that he reconfirms it or asks for U10.
- [ ] Record his ten actions below as event samples and copy them into `docs/handoff/events/`.

**You see.**
- [ ] He does each action in lanes 2 to 10 himself and says in chat that the harness is signed off.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_handoff.py` asserts that `docs/handoff/API.md` lists every OPERATIONS row and its `who`. Run the qma-v2 suite with `-n 2`. Then run `just ci` under the lock and save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents. The operator performs lanes 2 to 10 in his own words. The coordinator prepares each lane and saves the evidence.
- [ ] Lane 1. Regression lane against trunk. Re-run lane 1 of every earlier PR through `drive.py` at trunk (the U9 merge SHA) and at head. Save `signoff-regression.log`. Pass when every lane 1 passes on both.
- [ ] Lane 2. He signs in with Claude in the console, then asks it to read a file and edit it. Save `signoff-files.png`. Pass when the edit shows as a diff and the file changed.
- [ ] Lane 3. He asks it to run a command. Save `signoff-command.png`. Pass when the approval card appears and the output shows after he allows it.
- [ ] Lane 4. He asks it to search the web. Save `signoff-web.png`. Pass when the WebSearch card appears and results come back after he allows it.
- [ ] Lane 5. He asks it to start a helper. Save `signoff-helper.png`. Pass when a child card shows the helper's name and its result returns.
- [ ] Lane 6. He answers an approval prompt with Always allow and repeats the call. Save `signoff-approval.png`. Pass when the second call runs with no card.
- [ ] Lane 7. He asks it to read the broker password or place an order. Save `signoff-money.png`. Pass when it is refused with "Money is read-only for agents".
- [ ] Lane 8. He restarts QMX and continues the chat. Save `signoff-restart.png`. Pass when the reply knows the earlier turns.
- [ ] Lane 9. He switches the chat to an OpenRouter model. Save `signoff-switch.png`. Pass when the cost warning shows and the chat continues with context.
- [ ] Lane 10. He opens the usage page. Save `signoff-usage.png`. Pass when it shows his Claude 5-hour window, its reset time, and the money-guarantee line.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. TTFT and gate round trip on his signed-in console session, against the numbers recorded in U1 and U2.
- [ ] Probe. Take TTFT from lanes 2, 3 and 8 and the gate round trip from the decision log, at head. Re-run the U2 fake-host probe at trunk and head, interleaved.
- [ ] Baseline. Record the trunk fake-host p95 first.
- [ ] Rule. Fail when the head gate p95 exceeds trunk by more than 2 ms or TTFT p50 exceeds the U1 p50 by more than 50%.

**Review gate.** The operator reviews before merge.
- [ ] Copy lane 2 to 10 screenshots into `tracker/qma-v2/review/SIGNOFF-review-<slug>.png`. No screen-recording tool is installed, so the video is a numbered screenshot sequence of the flow plus its drive.py event log. It shows his session. Save it under `tracker/qma-v2/review/SIGNOFF-review/`.
- [ ] Post the screenshots and the video in chat. Stop at merge-ready. Wait for the operator's click.

**Merge.**
- [ ] Coordinator's clean verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The operator clicks merge. His sign-off message starts `tracker/qma-v2/DELETION-PLAN.md`.

## Close the program

- [ ] Every box above is checked with its evidence. List every builder worktree and branch for his go. Delete none without it.
- [ ] Reply to the operator with the report the execution playbook names. Give the predicate count from `units.tsv` and `ledger.tsv`, the merged PRs with head SHAs, the verdicts, what was abandoned and why, the open gates, the turn totals from `turns.tsv`, the store path, and the trail path.

## Appendix A. Prototype evidence

This was a planning-only pass. No prototype ran, so there is no branch, SHA or artifact. Each question below stays unproven until the named unit runs its probe.

- U1 records whether in-code hooks fire with `setting_sources=[]`, whether a PreToolUse `ask` is honoured under `plan` and `default`, and the Python SDK hook-callback timeout with the QMX hook budget under it (A8, V2.3). It also records whether `model_usage` is per query or cumulative (V4.4) and the working set of one host plus its CLI (A7).
- U3 records whether skills load from the materialised local plugin, and whether the `"user"` setting source follows `CLAUDE_CONFIG_DIR` (HARNESS open question 6, H1 section 5). U5 records whether the experimental `get_usage` control request is reachable from Python (V4.3, HARNESS open question 7), and how to change effort mid-session (H1 section 5).
- U8 records whether the Agents SDK runs on a ChatGPT token, whether `x-codex-*` headers reach QMX, and whether `responses.compact` works on that route (H1 section 5). U9 records whether fork-at-turn works on Claude (VERDICT A28).
- VERDICT V4.5 drops three probes because the pinned SDK source answers them. `tool_use_id` is always present in `can_use_tool`, `exclude_dynamic_sections` exists, and modes shadow `can_use_tool`. These were read in source, not run.

## Appendix B. Alternatives rejected

- Pairing in U2, as in the candidate unit list. VERDICT V6.2 offers two ways to give U4 key entry an operator principal. Moving pairing into U1b won, because the U1b console needs an operator login anyway.
- One U4 PR. VERDICT V6.2 wants the OpenAI core beside U2 but its parity checks after U2 and U3, so U4 splits into U4a and U4b.
- U5, U6 and U7 in one parallel wave. They would share `host/openai.py`, which V6.2 gives one owner per wave. U7 waits for U6 instead.
- Ten agents per PR for the live lanes. That is about 130 runs on his Max 5x plan (H2 answer 3). The coordinator runs the lanes inline.
- `playbooks/autopilot-stack.md` and `playbooks/autopilot-full.md`. The first hands the operator a stack to land, and the second lets each owner merge. Here the coordinator merges into `rebuild/base` itself (H2 answer 2).

## Appendix C. Risks

- His own Claude Code use draws on the same 5-hour window as the live checks (A9, A10). The 15-turn cap per unit and `turns.tsv` bound it. Every unit with Claude lanes watches the count.
- `claude-agent-sdk` 0.2.165 is days old (H3 section 5). U0 records the pin and U1 records the bundled CLI version. If U1 fails on the SDK, the coordinator parks a gate rather than downgrading to 0.2.163, which has no Windows wheel.
- U0 moves the workspace to `claude-agent-sdk` 0.2.165. The old native-session tests in `qma-daemon` check the SDK version (HOW section 4), so they may fail before D1 deletes them. U0 owns keeping the old QMA suite green and reports any test it had to mark.
- U6 lane 2 fills a 128K context on OpenRouter and costs money. The coordinator records the cost and picks a cheap model.
- GitHub Actions has never run (BACKLOG B2), so every green is a local `just ci` of about 29 minutes under one lock. Three builders queue on the lock. The coordinator's gates lane waits its turn.
- Builders and verifiers run on `opus`. Fable is the second model family only for the U2 and U7 interrogate reviews and the final trail review, per the operator on 2026-10-13. `sonnet` is for very small tasks only.
- Money safety against deliberate code is a same-user speed bump until U10 or credential absence (HARNESS tension 1). SIGNOFF records his written answer. U10, the separate OS account, is not scheduled and runs only if he asks for it there.
- The `qmx-tools` stdio servers stay a second writer on `control.db` (BACKLOG B1). U3 refuses them in agent MCP config. Fixing B1 is outside this program.
- U8 depends on an unverified route. The probe can close U8 without code, and SIGNOFF then skips ChatGPT.

## Appendix D. Links and reading list

- Read before editing. `tracker/qma-v2/HARNESS.md`, `research/interrogate/VERDICT.md`, `research/H3-code-map.md` (builder quick-reference and traps), `research/how/HOW-harness-surface.md`, `research/H1-sdk-facts.md` (builder reading list in section 4), `research/H2-skills-method.md` (builder Method block), `BASELINE.md` (H1 to H18), `UI-NOTES.md`, and `sketch/`. The base unit list is `research/architect/candidate-1-opus/units.md`, amended here by A5, A6, A8, A10 and VERDICT V6. Nothing under `archive/` is a source.
- U2 and U7 get `C:/Users/Mubarak/.claude/skills/interrogate/SKILL.md` with one `opus` and one `fable` reviewer (the operator allowed Fable for review only on 2026-10-13). No PR gets `how`, since the HOW synthesis already exists.
- The trail is `D:/QMX-worktrees/qma2-ship/decisions.tsv`, per `C:/Users/Mubarak/.claude/skills/show-me-your-work/SKILL.md`.
