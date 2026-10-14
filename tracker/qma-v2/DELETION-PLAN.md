# QMA v2 old-code deletion plan

This program deletes the old agent code that the one-engine harness in `HARNESS-PLAN.md` replaced. The operator gets a smaller repo with no LangChain, and the next engineer gets one agent runtime to read.
It follows "build beside, switch, then delete". It starts only after HP17 merges and the operator signs off in the temporary console.
The rule it enforces is that nothing is deleted while a live caller still imports it, and every deletion proves that with a caller scan.
PR ids in order are D1 (the `qmx_agents` runtime), D2 (the QMB host spawn path, a hand-off to the QMB session), D3 (the daemon), and D4 (the LangChain dependencies). Step 0 of the DESIGN deletion order is not deletion and ships early as HP3.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-full.md`, for the same reason `HARNESS-PLAN.md` Appendix B gives. One coordinator session is the root. It dispatches one builder per PR on `opus`, verifies each PR itself at the head SHA, and merges it into `rebuild/base`. Owners stop at merge-ready and never merge. D2 edits QMB, which has its own session and is the operator's tamper-proof tool (BACKLOG B7). This program writes D2's brief and waits for the QMB session to merge it. It never merges into `main` or `integration`.

Each PR's ten live lanes are a coverage list, not ten agents. The coordinator runs them itself, in sequence, in one boot of the PR head, because the operator has one Claude Max 5x plan.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Confirm HP17 is merged into `rebuild/base`, and quote the operator's sign-off message from `D:/QMX-worktrees/qma-ship/decisions.tsv`.
- [ ] State the protocol and this plan to the operator, then stop. In the same message, give two defaults and ask whether he wants them changed. Start execution only on the operator's explicit go.
  - [ ] Default one. D1 replaces remote agent runs in `qmx_remote/worker.py` with a stub that says they return with BACKLOG B44, instead of a rewrite on the harness.
  - [ ] Default two. `qmb host start` keeps starting `qmx_control` until the QMB session lands D2. The harness starts with `python -m qma.serve` and needs nothing from QMB.
- [ ] Read these from trunk at program start. Re-read them at every tick. Log each read in `decisions.tsv`.
  - [ ] `git show origin/main:CLAUDE.md` for the project rules on trunk, then Read `C:/Users/Mubarak/Desktop/QMX/CLAUDE.md`, whose QMA v2 section is not on `main` yet.
  - [ ] `git -C D:/QMX-worktrees/agent-system show plan/agent-system:tracker/qma-v2/DELETION-PLAN.md`, then `research/one-engine/architect/DESIGN.md` section 4 and `research/one-engine/how/HOW-one-engine.md` (the deletable table and gotchas 1 to 16) from the same branch.
  - [ ] Read `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-full.md`, `shipping.md` and `opening-a-pr.md`, then `C:/Users/Mubarak/.claude/skills/swarm/SKILL.md` and `principle-migrate-callers-then-delete-legacy-apis/SKILL.md`.
- [ ] Reuse the store at `D:/QMX-worktrees/qma-ship/`. Append the standing orders of `HARNESS-PLAN.md` unchanged, plus one line. Deletion PRs carry no harness feature, and harness PRs carry no deletion.
- [ ] On the operator's go, arm the audit tick as `/loop 1h` with the tick prompt below. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk. Audit the operation against it and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then post a short status message to the operator in chat only when the audit found a tracked change that no earlier status message reported, such as a PR opened, a code-ready head, a round launched or closed, a verdict, a merge, a stuck agent and the action taken, a blocker added or cleared, or a decision only the operator can make. Name every such change and nothing else. Do not repeat a table, the merged list, or an unchanged blocker. If the audit found none, end the turn with no reply text. Either way, log this tick's row in your decision trail. The row names the items reported, or none."
- [ ] On the operator's hold or stand-down, send every builder a zero-writes order at once.

### Spawn owners

- [ ] Spawn one builder per PR with the Agent tool, `subagent_type: "poteto-agent"`, `model: "opus"` and `run_in_background: true`. The brief holds the PR's section of this plan, DESIGN section 4, the HOW gotchas it names, and "do not spawn sub-agents".
- [ ] Follow this dependency graph. Start dependent work only after its parent merges.
  - [ ] D1 is first. It branches from `rebuild/base` after HP17 merged.
  - [ ] D2 belongs to the QMB session. Send it the D2 section as its brief once the operator says go. It may land before or after D1.
  - [ ] D3 after D1 and D2 both merged, because the QMB host must stop naming `qma.daemon` first.
  - [ ] D4 after D3.
- [ ] Hold the file boundaries. Only D2 touches `qmb/`. No PR touches `qmn/`, `qmf/`, `qml/`, `apps/qmx-ui/` or `qmx-agents/packages/qma-harness/src/`. D1 may edit `qmx-agents/plugin/` and `qmx-control` only where its **Files** block says so.
- [ ] Hold the review gate. D2 waits for the operator's review in chat with screenshots and a video before the QMB session merges it.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Run `command -v origin`. If it is missing, use `gh` and record that. Never require `gt`.
- [ ] The builder opens the PR ready, never draft, per **Opening a PR**, with `gh pr create --base rebuild/base --head qma/<pr-id>`.
- [ ] The builder runs `uv run --no-sync python -m poethepoet fmt-check`, `lint` and `types` once in every workspace it touched, before the PR-facing push. Push with hooks on.
- [ ] The builder rereads the full diff in place of `/deslop`, which is not installed, and runs `/no-comments` before review. No Bugbot runs here. The coordinator's audit lanes take its place per `C:/Users/Mubarak/.claude/skills/poteto-mode/references/bugbot-triage.md`.
- [ ] Rebase onto current `origin/rebuild/base` before the code-ready report. Rebase again only at merge prep, on a `git merge-tree` conflict, or on a CI failure caused by a change on `rebuild/base`.

### Verdict and merge, for every PR

- [ ] At the code-ready head SHA and at each later push that changes the patch, the coordinator runs the swarm lanes per `C:/Users/Mubarak/.claude/skills/swarm/SKILL.md` inline. One gates lane runs `just ci` under the CI lock from `HARNESS-PLAN.md`. The ten live lanes, the perf lane and two audit lanes follow. Audit lane A checks that every deleted path had no caller outside the deletion set. Audit lane B checks that nothing outside the PR scope changed.
- [ ] Clean only when every lane is `PASS`. Findings go to a fresh builder with consolidated scope. A new head gets a fresh run, except for results that stay valid under the patch-id rule in `playbooks/shipping.md`. Record each verdict in `ledger.tsv` with head SHA, base SHA and `git patch-id --stable`.
- [ ] Merge D1, D3 and D4 in order with `gh pr merge <number> --merge --repo MubarakHimself/QMX`. D2 merges only by the QMB session after the operator's click.

### Boot recipe, for every live lane

The coordinator runs every lane of a PR on the operator's PC in one boot, with the scripts the harness program left in `scripts/live/qma/`.

- [ ] `git -C D:/QMX-worktrees/agent-system fetch origin qma/<pr-id>`, then check out the head SHA detached in `D:/QMX-worktrees/qma-verify`.
- [ ] Put `TMP`, `TEMP` and `UV_CACHE_DIR` on `D:`, then run `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] Start the host with `uv run --no-sync python -m qma.serve serve --home D:/QMX-worktrees/qma-ship/home --port 8876` and wait for `GET /api/health`.
- [ ] Drive the API only through `scripts/live/qma/drive.py`, the check scripts and the console. Use the `haiku` tier, log every plan turn in `turns.tsv`, and pause at 50% of the five-hour window.
- [ ] Save every log and screenshot to `D:/QMX-worktrees/qma-ship/evidence/<pr-id>/<slug>`, then stop the host and confirm with `Get-Process` that no lane process is left.

## Retire the qmx_agents runtime (D1)

**Depends on.** HP17 merged and the operator's sign-off quoted. This is DESIGN deletion step 2.

**Files.**

- [ ] Create `qmx-agents/plugin/agents/<name>.md` for `app-builder`, `data-analyst`, `researcher` and `overnight-builder`, ported from `qmx_agents/agents/*.yaml` and `*.md`. No `tools` list names `mcp__qmx__delegate` (R33).
- [ ] Create `qmx-agents/plugin/skills/build-mini-app/`, `build-workflow/` and `debug-app/`, ported from `qmx_agents/skills/`.
- [ ] Edit `qmx-agents/plugin/QMX.md` to carry the rules from `qmx_agents/copilot.md` and `copilot.yaml` that are not already there.
- [ ] Edit `qmx-control/src/qmx_control/service.py` `apps_publish` to run the app-publish test gate, if a caller scan shows it lives only in `AppHooksMiddleware` (`qmx_agents/guards/hooks.py:22`).
- [ ] Edit `qmx-remote/src/qmx_remote/worker.py` to replace `execute_agent`, `execute_workflow` and `run_router` with the stub from default one, and `qmx-remote/pyproject.toml` to drop `qmx-agents`. Edit `qmx-control/tests/test_remote.py`.
- [ ] Delete `scripts/live/copilot_build_app.py` and `scripts/live/smoke_agent.py`.
- [ ] Delete `qmx-agents/packages/qmx-agents/` and `default_tool_registry` in `qmx-tools/src/qmx_tools/registry.py`, with `registry.py` itself if nothing is left in it after HP3.
- [ ] Edit `qmx-agents/pyproject.toml` (members), the pyright paths in the root `pyproject.toml`, `tools/ci.py` (the `packages/qmx-agents` row), `tools/test_all.py` (the `qmx-agents` row) and both `uv.lock` files.

**Build.**

- [ ] Before any deletion, run `git grep -n "qmx_agents" -- . ':!*.md' ':!archive/**' ':!**/uv.lock'` and attach the output to the PR body.
- [ ] Commit in this order. The ports, the `apps_publish` gate, the worker stub, the script deletions, then the package deletion. Edit poe task strings in the same commit as the paths they name.
- [ ] Leave `examples/apps/macro-daily-bias` and `examples/apps/weekend-watcher` alone. They pin `qmx-agents` by git commit and keep running that old code until new versions go through the road.

**You see.**

- [ ] `git grep -n "qmx_agents" -- . ':!*.md' ':!archive/**' ':!**/uv.lock'` prints only the two example apps' git pins, and the console lists the ported skills.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `qmx-agents/packages/qma-harness/tests/test_plugin.py` gains a case that every file under `qmx-agents/plugin/agents/` parses and none lists `mcp__qmx__delegate`. `qmx-control` tests gain an `apps_publish` case for a failing app test, and `qmx-remote` tests gain the stub case. Run the touched suites with `-n 2`, then `just ci` under the lock. Save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `scripts/live/qma/run_all.py` at trunk and head. Save `d1-run-all.log`. Pass when both give the same PASS set.
- [ ] Lane 2. Run the `git grep` from **You see.** Save `d1-grep.log`. Pass when it prints only the two example pins.
- [ ] Lane 3. Run `uv lock --check` at the root and in `qmx-agents/`, then `uv pip list`. Save `d1-lock.log`. Pass when both locks pass and `qmx-agents` is not installed.
- [ ] Lane 4. Run operator check 6 in the console. Save `d1-check6.png`. Pass when the ported skills appear and none of his personal skills do.
- [ ] Lane 5. Run operator check 11 in the console with a ported agent named. Save `d1-check11.png`. Pass when the helper runs from the ported definition and the answer holds both facts.
- [ ] Lane 6. Rerun `s11_helpers.py` (S11). Save `d1-s11.log`. Pass when no ported agent can call `mcp__qmx__delegate`.
- [ ] Lane 7. Publish a fixture app whose tests fail, at trunk and head. Save `d1-publish.log`. Pass when both refuse the publish.
- [ ] Lane 8. Start a remote agent run through REST. Save `d1-remote.log`. Pass when it fails at once with the stub message naming B44.
- [ ] Lane 9. In the `qmx-agents` venv after `uv pip uninstall` of every `langchain*`, `langgraph*` and `deepagents` package, import `qmx_control`, `qmx_apps`, `qmx_remote` and `qma.harness`. Save `d1-import.log`. Pass when all four import.
- [ ] Lane 10. Rerun `s03_tools.py`, `s04_vanilla.py` and `s06_money.py` (S3, S4, S6), which DESIGN step 2 names. Save `d1-s03-s04-s06.log`. Pass when all three pass.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of `just ci`.
- [ ] Probe. Run `just ci` at trunk, then at head, then at trunk again, each under the lock.
- [ ] Baseline. Record the trunk wall time first.
- [ ] Rule. Fail when head is slower than the mean of the two trunk runs. Record the saving.

**Review gate.** None. D1 is not review-gated, because the operator's sign-off before the program covers it.

**Merge.**

- [ ] Coordinator's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current `rebuild/base` after the verdict, patch-id unchanged.
- [ ] The coordinator merges with `gh pr merge <number> --merge`.

## Point the QMB host at the harness (D2, hand-off to the QMB session)

**Depends on.** HP5, which gives `qma.serve` the same CLI as `qmx_control`, and the operator's go to the QMB session. This program does not build D2. It hands this section to the QMB session as its brief and waits for that session's merge.

**Files.**

- [ ] Edit `qmb/src/qmb/doors/cli/host.py`. Delete `DAEMON_SPAWN_MODULE` at `:104` and its export at `:43`, the daemon branches of `_spawn_argv` at `:692-693`, their callers near `:938` and `:1746`, and the daemon-only `invoke_host_*` helpers. Change the spawn module at `:1799` from `qmx_control` to `qma.serve`.
- [ ] Edit `qmb/tests/test_cli_host.py`, and delete or rewrite `qmb/tests/test_operator_study_cli.py`, which imports `qma`.
- [ ] Edit the comment at root `pyproject.toml:341`.

**Build.**

- [ ] The QMB session owns this change and its tests. The minimal retarget the harness could ever need is the one string at `:1799`, and it lands only when the operator asks for `qmb host start` to start the harness. The harness itself starts with `python -m qma.serve`, so no harness PR waits on D2.

**You see.**

- [ ] `uv run qmb host start`, `status` and `stop` run against `qma.serve`, and `git grep -n "qma.daemon" qmb/` prints nothing.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `qmb/tests/test_cli_host.py` gains a case that the spawn argv names `qma.serve`. Run the `qmb` suite with `-n 2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `uv run qmb host start`, `status` and `stop` at trunk, which spawns `qmx_control`, and at head. Save `d2-host.log`. Pass when each exits 0 on both sides and head's process is `qma.serve`.
- [ ] Lane 2. Run `git grep -n "qma.daemon" qmb/`. Save `d2-grep.log`. Pass when it prints nothing.
- [ ] Lane 3. Read `status` while the host runs. Save `d2-status.log`. Pass when it names the PID and the port.
- [ ] Lane 4. Call `GET /api/doctor` on the QMB-started host. Save `d2-doctor.log`. Pass when it answers with the harness doctor lines, which shows the host is `qma.serve`.
- [ ] Lane 5. Run `uv run qmb host recover-control`, whose daemon branch D2 removes. Save `d2-recover.log`. Pass when it works through `qma.serve`, or exits non-zero with a message that names the removed daemon path.
- [ ] Lane 6. Run `qmb/tests/test_cli_host.py` with `-n 2`. Save `d2-tests.log`. Pass when it passes and no test names the daemon.
- [ ] Lane 7. Run the QMB backtest suite at trunk and head. Save `d2-backtest.log`. Pass when the pass and fail counts match.
- [ ] Lane 8. Read `qmb/src/qmb/analysis/variants.py:66`. Save `d2-schema.log`. Pass when the `qma.wire.money_path_field_diff.v1` name is unchanged.
- [ ] Lane 9. Run operator check 2 in the console against the QMB-started host. Save `d2-check2.png`. Pass when the console reads the README and answers.
- [ ] Lane 10. Stop the host and list processes. Save `d2-stop.log`. Pass when no `qma.serve`, `claude` or `qma-cli-launcher` process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Time from `qmb host start` to the first 200 on `/api/health`.
- [ ] Probe. Five starts at trunk and five at head, interleaved.
- [ ] Baseline. Record the trunk median first.
- [ ] Rule. Fail when the head median exceeds the trunk median by more than 1 s.

**Review gate.** The operator reviews before merge, because QMB is his tamper-proof tool.

- [ ] Copy the lane 1 and lane 9 evidence into `D:/QMX-worktrees/qma-ship/review/D2-review-<slug>.png` as screenshots.
- [ ] Record a 30 to 60 second video of `qmb host start`, `status`, the console turn and `stop` with `ffmpeg -f gdigrab`. Save it as `D:/QMX-worktrees/qma-ship/review/D2-review.mp4`.
- [ ] Post the screenshots, the video and the `qmb/` diff in chat. Stop at merge-ready. Wait for the operator's click.

**Merge.**

- [ ] The QMB session's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current `rebuild/base` after the verdict, patch-id unchanged.
- [ ] The QMB session merges after the operator's click. This program records the merge SHA in `ledger.tsv` before D3 starts.

## Delete the daemon (D3)

**Depends on.** D1 and D2 merged. This is DESIGN deletion step 3, minus the QMB lines D2 owns.

**Files.**

- [ ] Delete `qmx-agents/packages/qma-daemon/`, `qmx-agents/plugins/` (the daemon packs), `qmx-agents/examples/`, `qmx-agents/tests/test_workspace_scaffold.py`, `qa/integration/test_qma_authenticated_study.py` and `qa/integration/test_qma_registered_replay.py`.
- [ ] Edit `qmx-agents/pyproject.toml` (members, the `qma-runtime` extra, pytest `pythonpath`, pyright `extraPaths` and `include`, the poe `test` coverage targets) and root `pyproject.toml:228-230` and `:360-362`. Regenerate both `uv.lock` files.
- [ ] Edit `tools/nested_coverage_report.py`, `tools/release_gate.py`, `tools/build_release.py`, `tools/backend-source-provenance.py`, `tools/secret_scan.py:65`, `tools/tests/test_release_install.py` and `tools/tests/test_runtime_wheel_closure.py`.
- [ ] Keep `qmx-agents/packages/qma-core/`, which holds the money deny-list and `descriptors.py` the harness imports. Keep `qmx-agents/packages/qma-wire/`, which QMN's `spot_paper_journey.py` and `qmn/tests/test_qmn_fx_paper.py` still use and whose schema name QMB cites. Keep `scripts/dev/qma_callers.py`, because both packages still have callers.

**Build.**

- [ ] Run `scripts/dev/qma_callers.py --json` before deleting and attach the output to the PR body.
- [ ] Confirm nothing is left to harvest from `native_claude.py`, `native_sessions.py` and `native_boundary.py`. The `_preflight` env refusal is replaced by the boot allow-list, and the auth check by `plan_auth_method` (HOW gotcha 7). Record any rule that has no harness twin in the PR body.
- [ ] Commit in the DESIGN step 3 order. The LangChain loop files, then the providers, then the native files, then `bundled_packs`, then the package and its config edits.

**You see.**

- [ ] `git grep -n -E "qma\.daemon|qma-daemon" -- . ':!*.md' ':!archive/**'` prints nothing, and `python -m qma.serve serve` still starts.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run the `tools/tests` suite and the qma-core, qma-wire and qma-harness suites with `-n 2`, then `just ci` under the lock. Save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `scripts/live/qma/run_all.py` at trunk and head. Save `d3-run-all.log`. Pass when both give the same PASS set.
- [ ] Lane 2. Run the `git grep` from **You see.** Save `d3-grep.log`. Pass when it prints nothing.
- [ ] Lane 3. Run `uv lock --check` at the root and in `qmx-agents/`. Save `d3-lock.log`. Pass when both pass.
- [ ] Lane 4. Run `python -c "import qma.daemon"`, then `python -c "import qma.core.barriers.money_path, qma.core.barriers.descriptors, qma.wire"`. Save `d3-import.log`. Pass when the first fails with `ModuleNotFoundError` and the second exits 0.
- [ ] Lane 5. Run `uv run qmb host start`, `status` and `stop`. Save `d3-qmb-host.log`. Pass when each exits 0 against `qma.serve`.
- [ ] Lane 6. Run the `qmn` suite, including `test_qmn_fx_paper.py`. Save `d3-qmn.log`. Pass when it passes, which shows `qma-wire` still serves QMN.
- [ ] Lane 7. Run `qmb/tests/test_analysis_book_bms_variants.py`. Save `d3-qmb-variants.log`. Pass when it passes.
- [ ] Lane 8. Read the trunk `qma_callers.py --json` output attached to the PR. Save `d3-callers.json`. Pass when every caller of `qma.daemon` is in the deletion set.
- [ ] Lane 9. Run operator check 5 in the console. Save `d3-check5.png`. Pass when both order requests are refused with the money rule named, which shows the gate still imports `qma.core`.
- [ ] Lane 10. Run the `money-path-scan` and `secret-scan` poe tasks at the root. Save `d3-scans.log`. Pass when both pass.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of `just ci`.
- [ ] Probe. Run `just ci` at trunk, then at head, then at trunk again, each under the lock.
- [ ] Baseline. Record the trunk wall time first.
- [ ] Rule. Fail when head is slower than the mean of the two trunk runs. Record the saving.

**Review gate.** None. D3 is not review-gated.

**Merge.**

- [ ] Coordinator's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current `rebuild/base` after the verdict, patch-id unchanged.
- [ ] The coordinator merges with `gh pr merge <number> --merge`.

## Remove the LangChain dependencies (D4)

**Depends on.** D3. This is DESIGN deletion step 4.

**Files.**

- [ ] Edit every `pyproject.toml` that names `langchain`, `langchain-core`, `langgraph`, `deepagents`, `langchain-anthropic`, `langchain-openai`, `langchain[mcp]`, `langgraph-checkpoint-sqlite` or `openai-codex`, `qmx-tools/pyproject.toml` (`langchain-core==1.6.7`) included.
- [ ] Regenerate both `uv.lock` files.

**Build.**

- [ ] Remove each dependency only after `git grep` shows no import of it outside locks, `archive/` and the two example apps. `operator-config.json` handling went with the daemon in D3. Confirm with `git grep -n "operator-config.json"`.

**You see.**

- [ ] In a fresh venv after `uv sync --frozen --all-packages --all-groups`, `uv pip list` shows none of the nine packages.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Run `just ci` under the lock in the fresh venv. Save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe.

- [ ] Lane 1. Regression lane against trunk. Run `scripts/live/qma/run_all.py` at trunk and head. Save `d4-run-all.log`. Pass when both give the same PASS set.
- [ ] Lane 2. Run `uv pip list` in the fresh venv. Save `d4-pip.log`. Pass when none of the nine packages is listed.
- [ ] Lane 3. Run `git grep -n -i -E "langchain|langgraph|deepagents"` outside locks, `archive/` and the example apps. Save `d4-grep.log`. Pass when it prints nothing.
- [ ] Lane 4. Import `qmx_control`, `qmx_apps`, `qmx_remote`, `qmx_tools.servers` and `qma.harness` with `python -X importtime`. Save `d4-import.log`. Pass when all import and no LangChain module appears.
- [ ] Lane 5. Run operator check 2 in the console. Save `d4-check2.png`. Pass when the console reads the README and answers.
- [ ] Lane 6. Start `qmx-mcp-data` over stdio and list its tools. Save `d4-mcp.log`. Pass when it lists the same names as trunk.
- [ ] Lane 7. Run `uv lock --check` at the root and in `qmx-agents/`. Save `d4-lock.log`. Pass when both pass.
- [ ] Lane 8. Run `git grep -n "operator-config.json"`. Save `d4-operator-config.log`. Pass when it prints nothing outside `archive/`.
- [ ] Lane 9. Run `tools/build_release.py`. Save `d4-release.log`. Pass when the wheels build.
- [ ] Lane 10. Run `tools/tests/test_release_install.py`. Save `d4-release-install.log`. Pass when it passes.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of `uv sync --frozen --all-packages --all-groups` in `qmx-agents/` with an empty cache on `D:`.
- [ ] Probe. Two cold syncs at trunk and two at head, interleaved.
- [ ] Baseline. Record the trunk mean first.
- [ ] Rule. Fail when the head mean is slower than the trunk mean.

**Review gate.** None. D4 is not review-gated.

**Merge.**

- [ ] Coordinator's clean verdict at the exact head SHA.
- [ ] Audit-lane findings triaged per `bugbot-triage.md`.
- [ ] Rebased onto current `rebuild/base` after the verdict, patch-id unchanged.
- [ ] The coordinator merges with `gh pr merge <number> --merge`.

## Close the program

- [ ] Every box above is checked with its evidence. List every deletion worktree and branch for his go. Delete none without it.
- [ ] Reply to the operator with the report the execution playbook names. Give the merged PRs with head SHAs, D2's merge SHA from the QMB session, lines removed, the `just ci` time before and after, the follow-ups left in Appendix D, and the trail path `D:/QMX-worktrees/qma-ship/decisions.tsv`.

## Appendix A. Prototype evidence

No prototype ran in this planning pass. Three facts stay unproven until the PRs run their lanes. One is that nothing outside the deletion set still imports `qmx_agents` or `qma.daemon` at the HP17 merge SHA. The scans in this plan come from `4eac8f69`. Another is whether the app-publish test gate lives only in `AppHooksMiddleware`. The last is whether `registry.py` is empty after HP3 moves `domain_functions`.

## Appendix B. Alternatives rejected

- **The 2026-10-13 version of this plan.** It deleted `qma-core` and `qma-wire` whole. The one-engine design keeps `qma.core.barriers.money_path` as the one deny-list and adds `qma.core.barriers.descriptors`, and QMN still imports `qma.wire`. It also edited QMB inside D1, which now belongs to the QMB session.
- **Deleting before the harness passes.** DESIGN section 4 and the operator's rulings (R31, R38) put every deletion after sign-off.
- **A harness rewrite of remote runs inside D1.** Remote agent runs are BACKLOG B44, which runs the harness on his server in Docker. A stub keeps D1 a deletion, and the operator can ask for the rewrite instead.
- **One PR for D3 and D4.** D4 is the proof that nothing imports LangChain anymore. It is cheap to verify on its own and easy to revert.

## Appendix C. Risks

- **D2 waits on another session.** D3 cannot start until the QMB session lands D2. The coordinator reports the wait at each tick that sees a change and does not edit `qmb/`.
- **The root `pyproject.toml` path edits can break pyright and pytest for QMF and QMB (D1, D3).** The gates lane catches it, and the builder runs the root `poe types` before push.
- **The worker stub ends remote agent runs (D1).** The operator hears this as default one before the go.
- **Example apps run old code (D1).** `macro-daily-bias` and `weekend-watcher` pin `qmx-agents` by git commit, so they keep working and keep LangChain inside their own environments.

## Appendix D. Follow-ups this program leaves

- `qma-wire` stays until QMN's `spot_paper_journey.py` and `qmn/tests/test_qmn_fx_paper.py` stop importing it, which needs the operator's go for a QMN edit, and until QMB's schema citation in `qmb/src/qmb/analysis/variants.py:66` has a new home.
- `qma-core` stays. Only its `barriers` package is used by the harness. Trimming the rest is a separate pass once a caller scan shows what else uses it.
- The example apps move to new versions through the road, outside this program.
- Old UI deletion is out of scope. `apps/qmx-ui` on `rebuild/base` is the old UI wired to the dead CT-40 wire. Delete it only when the later UI session lands the new UI from `ui-review/repair`, and fix `tools/build_release.py:75` in the same PR. The `ui-review/repair` branch has never been pushed and is the only copy, so the UI session pushes it first. That deletion needs his go (BACKLOG B12).
