# QMA v2 old-code deletion plan

This program deletes the old agent code that the `qma2` harness replaced. It is for the operator (Mubarak) and the next engineer, who get a smaller repo and a `just ci` about ten minutes shorter (H3 section 4).
It follows "build beside, switch, then delete", so it starts only after he signs off SIGNOFF in `tracker/qma-v2/HARNESS-PLAN.md`.
The rule it enforces is that nothing is deleted while a live caller still imports it, and every deletion proves that with a caller scan.
PR ids in order are D1 (old QMA runtime), then D2 (LangChain guard imports, partial). D3 (old UI) is out of scope and recorded in Appendix E.
Deletion PRs land in `rebuild/base`. The operator moves `integration`, then `staging`, then `main` later, and `main` moves only by his click. No branch or worktree is deleted without his go.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

The program runs `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/orchestrate.md`, collapsed to two units. One coordinator chat on `opus` dispatches one `poteto-agent` builder per PR on `opus`. The coordinator verifies each PR itself at the head SHA and merges into `rebuild/base` with `gh pr merge --merge`. It never merges into `main` or `integration`. D1 edits QMB and QMN, which needs the operator's explicit go, so D1 stops at merge-ready for his click.

Each PR's ten live lanes are coverage boxes. The coordinator runs all ten itself, inline, in one boot of the PR head. They are not ten agents.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Confirm SIGNOFF is merged and quote his sign-off message in `D:/QMX-worktrees/qma2-ship/decisions.tsv`.
- [ ] State the protocol and this plan to the operator, then stop. Ask in the same message for his go on the QMB edit in `qmb/src/qmb/doors/cli/host.py` and its tests, and on retiring or rewriting `qmn/examples/spot_paper_journey.py`. Start execution only on the operator's explicit go.
- [ ] Read these from trunk at program start. Re-read them at every tick. Log each read in `decisions.tsv` as "Skill tool" or "Read".
  - [ ] `git show origin/main:CLAUDE.md` for the project rules on trunk, then Read `C:/Users/Mubarak/Desktop/QMX/CLAUDE.md`, whose QMA v2 section is not on `main` yet.
  - [ ] `git -C D:/QMX-worktrees/agent-system show plan/agent-system:tracker/qma-v2/DELETION-PLAN.md` and `plan/agent-system:tracker/qma-v2/research/H3-code-map.md`. The plan branch is local only.
  - [ ] Read `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/orchestrate.md`, `shipping.md` and `opening-a-pr.md`, then `C:/Users/Mubarak/.claude/skills/swarm/SKILL.md` and `C:/Users/Mubarak/.claude/skills/principle-migrate-callers-then-delete-legacy-apis/SKILL.md`. These live in the local install, not in the repo.
  - [ ] Read the project verify skill with `git show origin/rebuild/base:.claude/skills/verify-qmx-agents/SKILL.md`, and load `anthropic-skills:built-in-browser` with the Skill tool for the console lane.
- [ ] Reuse the store at `D:/QMX-worktrees/qma2-ship/`. Append the standing orders of `HARNESS-PLAN.md` unchanged, plus one line. Deletion PRs carry no harness code, and harness PRs carry no deletion.
- [ ] On the operator's go, arm the audit tick as `/loop 1h` with the tick prompt below. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk. Audit the operation against it and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then post a short status message to the operator in chat only when the audit found a tracked change that no earlier status message reported, such as a PR opened, a code-ready head, a round launched or closed, a verdict, a merge, a stuck agent and the action taken, a blocker added or cleared, or a decision only the operator can make. Name every such change and nothing else. Do not repeat a table, the merged list, or an unchanged blocker. If the audit found none, end the turn with no reply text. Either way, log this tick's row in your decision trail. The row names the items reported, or none."
- [ ] On the operator's hold or stand-down, send every builder a zero-writes order at once.

### Spawn owners

- [ ] Spawn one builder per PR with `subagent_type: "poteto-agent"`, `model: "opus"`, `run_in_background: true`, and the full brief fields from `orchestrate.md`. The builder Method block comes from `research/H2-skills-method.md` section (b2).
- [ ] Follow this dependency graph. Start dependent work only after its parent merges.
  - [ ] D1 is first. It branches from `rebuild/base` after SIGNOFF merged.
  - [ ] D2 after D1, because both edit `qmx-agents/pyproject.toml`, `tools/ci.py` and `tools/test_all.py`.
- [ ] Hold the file boundaries. Only D1 touches `qmb/` and `qmn/`, and only after his go. Neither PR touches `qmx-agents/packages/qma-v2/src/qma2/` except D2's new `journal.py`, or `apps/qmx-ui/`.
- [ ] Hold the review gate. D1 waits for his review in chat with screenshots and a video before merge.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Origin is not installed here, so use `gh` and record that. Never require `gt`.
- [ ] The builder opens the PR ready, never draft, per **Opening a PR**, with `gh pr create --base rebuild/base --head qma2/<pr-id>`.
- [ ] The builder runs `python -m poethepoet fmt-check`, `lint` and `types` in every workspace it touched, once, before the PR-facing push. Push with hooks on.
- [ ] The builder rereads the full diff in place of `/deslop` and runs `C:/Users/Mubarak/.claude/skills/no-comments/references/comment-sicko.md` itself in place of `/no-comments`. No Bugbot runs here. The coordinator's audit lanes take its place per `C:/Users/Mubarak/.claude/skills/poteto-mode/references/bugbot-triage.md`.
- [ ] Rebase onto current `origin/rebuild/base` before the code-ready report. Rebase again only at merge prep, on a `git merge-tree` conflict, or on a CI failure caused by a change on `rebuild/base`.

### Verdict and merge, for every PR

- [ ] At the code-ready head SHA and at each later push that changes the patch, the coordinator runs the swarm lanes per `C:/Users/Mubarak/.claude/skills/swarm/SKILL.md` inline. One gates lane runs `just ci` under `D:\QMX-worktrees\.ci-lock`. The ten live lanes, the perf lane, and two audit lanes follow. Audit lane A checks that every deleted path had no caller outside the deletion set. Audit lane B checks that nothing outside the PR scope changed.
- [ ] Clean only when every lane is `PASS`. Findings go to a fresh builder with consolidated scope. A new head gets a fresh run, except for results that stay valid under the patch-id rule in `playbooks/shipping.md`. Record each verdict in `ledger.tsv` with head SHA, base SHA and `git patch-id --stable`.
- [ ] Merge in order with `gh pr merge <number> --merge --repo MubarakHimself/QMX`. D1 merges only after the operator's click or his written go.

### Boot recipe, for every live lane

The coordinator runs every lane of a PR on this machine in one boot, with the verify skill from U1b.

- [ ] `git -C D:/QMX-worktrees/agent-system fetch origin qma2/<pr-id>`, then check out the head SHA detached in `D:/QMX-worktrees/qma2-verify`.
- [ ] Remove every `ANTHROPIC_*` variable, put `TMP`, `TEMP` and `UV_CACHE_DIR` on `D:`, then run `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] Start the control host with `uv run qmb host start` on a lane home, wait for `GET /api/health`, and pair the console in the built-in Browser pane.
- [ ] Drive the API only through `qmx-agents/packages/qma-v2/scripts/drive.py`. Run model checks on OpenRouter, and log any Claude turn in `turns.tsv` (cap 15 per unit).
- [ ] Save every log and screenshot to `D:/QMX-worktrees/qma2-ship/evidence/<pr-id>/<slug>`, then stop the host and confirm no host process is left.

## Retire the old QMA runtime (D1)

**Depends on.** SIGNOFF in `HARNESS-PLAN.md`, and the operator's go on the QMB and QMN edits.

**Files.**
- [ ] Delete `qmx-agents/packages/qma-core/`, `qma-wire/`, `qma-daemon/`, `qmx-agents/plugins/`, `qmx-agents/examples/`, `qmx-agents/tests/test_workspace_scaffold.py`, `qa/integration/test_qma_authenticated_study.py` and `qa/integration/test_qma_registered_replay.py`.
- [ ] Edit `qmx-agents/pyproject.toml` (members, `qma-runtime` keeping `qmx-control`, pytest `pythonpath`, pyright `extraPaths` and `include`, poe paths, coverage targets, the `openai-codex` dev pin) and root `pyproject.toml:228-230`, `:341` and `:360-362`. Regenerate both `uv.lock` files.
- [ ] Edit `tools/nested_coverage_report.py`, `tools/release_gate.py`, `tools/build_release.py`, `tools/backend-source-provenance.py`, `tools/secret_scan.py:65`, `tools/tests/test_release_install.py` and `tools/tests/test_runtime_wheel_closure.py`.
- [ ] Edit `qmb/src/qmb/doors/cli/host.py` to delete the `invoke_host_*` helpers, the `DAEMON_SPAWN_MODULE` constant at `:104` and the daemon-path code up to `:1783`, keeping `control_host` and the `HOST_*` tuples. Edit `qmb/tests/test_cli_host.py` and delete or rewrite `qmb/tests/test_operator_study_cli.py`.
- [ ] Edit `qmn/examples/spot_paper_journey.py` to drop `qma.*`, or delete it together with `tools/spot-paper-check.ps1`, as he chose.
- [ ] Delete `scripts/dev/qma_callers.py` and `tools/tests/test_qma_callers.py` last.

**Build.**
- [ ] Before any deletion, check that `qmx-agents/packages/qma-v2/docs/native-recipe.md` exists with `file:line` citations into `native_claude.py` and `native_boundary.py`. If U1 did not write it, copy it in this PR's first commit.
- [ ] Run `scripts/dev/qma_callers.py --json` before deleting and attach the output to the PR body.
- [ ] Commit in this order. Recipe check, config edits, QMB, QMN, package deletion, then the callers script. Edit poe task strings in the same commit as the paths they name (H3 trap 11).

**You see.**
- [ ] `git grep -n -E "qma\.(core|daemon|wire)|qma-(core|daemon|wire)" -- . ':!*.md' ':!archive/**'` prints nothing, and `qmb host start` still starts the console.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Run the `qmb` suite and the `tools/tests` suite with `-n 2`, then `just ci` under the lock. Save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents.
- [ ] Lane 1. Regression lane against trunk. Run the U4a smoke turn on OpenRouter and one Claude turn through `drive.py` at trunk and head. Save `d1-smoke.log`. Pass when both turns reach `turn.finished` with the same tool events on both sides.
- [ ] Lane 2. Run the `git grep` from **You see.** Save `d1-grep.log`. Pass when it prints nothing.
- [ ] Lane 3. Run `uv lock --check` at the root and in `qmx-agents/`. Save `d1-lock.log`. Pass when both pass.
- [ ] Lane 4. Run `uv run qmb host start`, `status` and `stop`. Save `d1-qmb-host.log`. Pass when each exits 0 and `status` reports the running PID.
- [ ] Lane 5. Run `python -c "import qma.daemon"` in the qmx-agents venv. Save `d1-import.log`. Pass when it fails with `ModuleNotFoundError`.
- [ ] Lane 6. Read the trunk `qma_callers.py --json` output attached to the PR. Save `d1-callers.json`. Pass when every listed caller is in the deletion set or the QMB and QMN edits.
- [ ] Lane 7. Run `tools/spot-paper-check.ps1` if it remains, else `git grep -n spot_paper_journey`. Save `d1-spot-paper.log`. Pass when the script is green or the grep prints nothing.
- [ ] Lane 8. Run `qmb/tests/test_cli_host.py` with `-n 2` at head. Save `d1-qmb-tests.log`. Pass when it passes and no test names the daemon.
- [ ] Lane 9. Open `qmx-agents/packages/qma-v2/docs/native-recipe.md` at head. Save `d1-recipe.log`. Pass when it cites `native_claude.py` preflight, isolation and event-loop lines at `4eac8f69`.
- [ ] Lane 10. Send "delete notes.txt" in the console on OpenRouter and click Allow once. Save `d1-console.png`. Pass when the card appears and the file is gone.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. Wall time of `just ci`.
- [ ] Probe. Run `just ci` at trunk, then at head, then at trunk again, each under the lock.
- [ ] Baseline. Record the trunk wall time first.
- [ ] Rule. Fail when head is not at least 300 s faster than the mean of the two trunk runs. H3 expects about 600 s from dropping the QMA suite.

**Review gate.** The operator reviews before merge.
- [ ] Copy lane 4 and lane 10 evidence into `tracker/qma-v2/review/D1-review-<slug>.png` as screenshots. No screen-recording tool is installed, so the video is a numbered screenshot sequence plus its drive.py event log. It shows `qmb host start`, `status`, `stop` and the console turn. Save it under `tracker/qma-v2/review/D1-review/`.
- [ ] Post the screenshots, the video, the `qmb/` and `qmn/` diff, and the line counts removed in chat. Stop at merge-ready. Wait for the operator's click.

**Merge.**
- [ ] Coordinator's clean verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The operator clicks merge, or the coordinator runs `gh pr merge <number> --merge` on his written go.

## Move the neutral guard imports off LangChain (D2)

**Depends on.** D1.

**Files.**
- [ ] Create `qmx-agents/packages/qma-v2/src/qma2/journal.py`, a copy of `qmx_agents/guards/journal.py` (`RunJournal`, `encoded`, `fingerprint`, stdlib and pydantic only), and `qmx-agents/packages/qma-v2/tests/test_journal.py`.
- [ ] Edit the `qmx_apps` imports at `road/__init__.py:11`, `road/history.py:13` and `road/validation.py:12`, and the `qmx_remote` imports at `models.py:11` and `runs.py:16`, where the imported symbol is a journal or money symbol.
- [ ] Edit `qmx_agents/guards/journal.py` into a re-export shim of `qma2.journal`, as U2 did for `money_path.py`. Edit the import-linter contract to allow `qmx_apps` and `qmx_remote` to import `qma2.journal`.
- [ ] Delete `scripts/live/copilot_build_app.py`, `scripts/live/smoke_agent.py` and `scripts/live/smoke_firecrawl.py` only if `git grep` finds no caller.

**Build.**
- [ ] Re-point each import whose symbol now lives in `qma2.journal` or `qma2.money`. Leave every other `qmx_agents` import in place.
- [ ] Write the remaining `qmx_agents` importers, with file and line, into the PR body. The coordinator copies the list into Appendix D of this plan on `plan/agent-system`.

**You see.**
- [ ] `git grep -n "qmx_agents.guards.journal\|qmx_agents.guards.money_path" -- qmx-agents/packages/qmx-apps qmx-agents/packages/qmx-remote` prints nothing.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `tests/test_journal.py` gains hash-chain and stale-lock cases copied from the old journal tests. Run the qma-v2, qmx-apps and qmx-remote suites with `-n 2`, then `just ci` under the lock. Save `ci.log`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. The coordinator runs these lanes itself inline; they are not ten agents.
- [ ] Lane 1. Regression lane against trunk. Run the qmx-apps and qmx-remote suites at trunk and head. Save `d2-suites.log`. Pass when both report the same pass and fail counts.
- [ ] Lane 2. Run `python -c "import qma2.journal as j, qmx_agents.guards.journal as o; assert o.RunJournal is j.RunJournal"`. Save `d2-shim.log`. Pass when the assertion holds.
- [ ] Lane 3. Run the `git grep` from **You see.** Save `d2-grep.log`. Pass when it prints nothing.
- [ ] Lane 4. Run `git grep -n -e copilot_build_app -e smoke_agent -e smoke_firecrawl` at head. Save `d2-scripts.log`. Pass when it prints nothing, or the files were kept and the PR body says why.
- [ ] Lane 5. Call `runs_list` through `drive.py` on a home copied from the U9 lane home, at trunk and head. Save `d2-runs.log`. Pass when the run counts and costs match.
- [ ] Lane 6. Run the weekend-watcher install test in `qmx-apps/tests/test_apps.py` with a warm uv cache. Save `d2-weekend.log`. Pass when it passes on its git pin.
- [ ] Lane 7. Run `git grep -n qmx_agents -- qmx-agents/packages/qmx-remote qmx-agents/packages/qmx-apps qmx-agents/packages/qmx-control`. Save `d2-census.log`. Pass when every hit is listed in Appendix D.
- [ ] Lane 8. Run `lint-imports` in `qmx-agents/packages/qma-v2`. Save `d2-contract.log`. Pass when the contract passes with the two new allowed edges and no other change.
- [ ] Lane 9. Run `python -X importtime -c "import qmx_apps" 2> d2-importtime.log` at head. Save `d2-importtime.log`. Pass when the file shows which module still loads `langchain_core`, and that module is listed in Appendix D.
- [ ] Lane 10. Start the host, pair the console, and run `apps_list` through `drive.py`. Save `d2-apps.log`. Pass when the call returns the installed apps with no error.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. Cumulative import time of `qmx_apps` from `python -X importtime`.
- [ ] Probe. Five runs at trunk and five at head, interleaved, in the qmx-agents venv.
- [ ] Baseline. Record the trunk median first.
- [ ] Rule. Fail when the head median exceeds the trunk median by more than 10%.

**Review gate.** None. D2 is not review-gated.

**Merge.**
- [ ] Coordinator's clean verdict at the exact head SHA, audit lanes triaged, and a rebase onto current `rebuild/base` after the verdict with the patch-id unchanged.
- [ ] The coordinator merges with `gh pr merge <number> --merge`.

## Close the program

- [ ] Every box above is checked with its evidence. List every deletion worktree and branch for his go. Delete none without it.
- [ ] Reply to the operator with the report the execution playbook names. Give the merged PRs with head SHAs, lines removed, the `just ci` time before and after, the blockers left in Appendix D, and the trail path `D:/QMX-worktrees/qma2-ship/decisions.tsv`.

## Appendix A. Prototype evidence

No prototype ran in this planning pass. Two facts stay unproven until D1 and D2 run their lanes. One is that nothing outside the deletion set still imports `qma.*` at the SIGNOFF merge SHA (the H3 scan is from `4eac8f69`). The other is which `qmx_apps` road imports are journal or money symbols, which H3 counted but did not name.

## Appendix B. Alternatives rejected

- Deleting before the harness passes, as the old packet 0a did. H3 section 4 and WHY "Strangler" put every deletion after its replacement.
- One PR for D1 and D2. They edit the same workspace files, and D1 needs his go while D2 does not.
- Deleting the whole `qmx-agents` package now. Its worker executors still serve remote runs, so remote agent runs would go dark (H3 section 4).

## Appendix C. Risks

- D1 touches QMB, the tamper-proof backtest tool (BACKLOG B7). The review gate shows him the `qmb/` diff before merge.
- The root `pyproject.toml` path edits can break pyright and pytest for QMF and QMB. The gates lane catches it, and the builder runs the root `poe types` before push.
- `qmx-apps/tests/test_apps.py` needs network or a warm uv cache for weekend-watcher (H3 section 3). Lane 6 of D2 warms the cache first.

## Appendix D. Backlog left by D2, with its blockers

D2 removes only code with no caller. The `qmx-agents` LangChain package stays until these blockers are gone. Workflows are out of scope (BACKLOG B33), so this program cannot remove them.

- `qmx_remote/worker.py:29-32` imports `execute_agent` (`:184-209`), `execute_workflow` (`:137-170`) and `run_router` (`:171-182`). They need a headless turn runner on `qma2` and a workflow engine.
- `qmx-control/tests/test_remote.py:9` imports `qmx_agents` for the remote executors.
- Any `qmx_apps` road import of a non-neutral guard (admission backed by Deep Agents) that D2 lane 7 lists.
- `qmx-tools/src/qmx_tools/registry.py:274-281` is the LangChain wrapper, which pulls `langchain-core` into `qmx-tools`.
- `tools/ci.py:17` and `:27`, and `tools/test_all.py:72-77`, run the `qmx-agents` package rows.
- The example apps pin `qmx-agents` by git commit (`weekend-watcher/pyproject.toml`, macro-daily-bias). They keep running old code until new versions go through the road.
- The full proof from H3 D2 runs when these are gone. That proof is `git grep -i -E "langchain|langgraph|deepagents"` printing nothing outside locks, archive and example apps, and `import qmx_apps, qmx_remote, qmx_control` loading no `langchain_core`.

## Appendix E. Old UI deletion (D3), out of scope

`apps/qmx-ui` on `rebuild/base` is the old UI wired to the dead CT-40 wire. Delete it only when the later UI session lands the new UI from `ui-review/repair`, and fix `tools/build_release.py:75` in the same PR. The `ui-review/repair` branch has never been pushed and is the only copy, so the UI session pushes it first. D3 needs his go (H3 section 4, BACKLOG B12).
