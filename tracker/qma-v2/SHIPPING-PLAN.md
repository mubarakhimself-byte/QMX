---
label: qma-v2:shipping-plan
created: 2026-10-13
status: plan only. Execution starts on the operator's explicit go.
---

# QMA v2 shipping plan

This plan ships the WED path of `ARCHITECTURE.md` section 8 into `rebuild/base`, one PR per packet, for the Wednesday 14 October demo.
It is for the orchestrator session (`ORCHESTRATOR-PROMPT.md`) and for the operator, who audits the boxes against their evidence. The rule it enforces is that nothing merges on a green check alone. The orchestrator verifies each PR itself at the exact head SHA before it lands.
PR ids, in landing order, are 0a, 0b, 0c, 1a, 1b, 1c, 2, 3a, 3b, J23, 4a, 4b, 5a, 5b, S, then the rehearsal (6) and Thursday (7).

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record. The program runs `~/.claude/skills/poteto-mode/playbooks/orchestrate.md` for coordination and `~/.claude/skills/poteto-mode/playbooks/shipping.md` for landing. The orchestrator merges verified PRs into `rebuild/base`. Nobody touches `main`, `integration` or `ui-integration`. `main` moves only by the operator's own squash-merge click, and that is outside this plan.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

The builder of each packet ticks that packet's boxes in this file inside its own PR. The orchestrator edits no repository file. It ticks the Program checklist boxes in its ledger, and the post-demo docs PR copies them here.

## Program checklist

### Arm the program

- [ ] State the protocol and this plan to the operator, then stop. Start execution only on the operator's explicit go.
- [ ] Read these files in full at program start. Re-read the packet's rows before every dispatch.
  - [ ] `~/.claude/skills/poteto-mode/SKILL.md` and its playbooks `orchestrate.md`, `shipping.md`, `pause-safely.md`, `session-pickup.md`.
  - [ ] `tracker/qma-v2/ARCHITECTURE.md` sections 0, 2.0, 5 to 10, and this plan.
  - [ ] `tracker/qma-v2/HOW-WHY.md` delta pass 4 (F0 to F4).
- [ ] Create the ledger folder `D:\QMX-worktrees\qma2-ship\` with `LEDGER.md` and `logs\`. The ledger records, per packet, the builder agent id, branch, worktree, PR number, head SHA, base SHA, patch-id, verdict, and merge SHA.
- [ ] Record the start state in the ledger. Run `git -C D:\QMX-worktrees\agent-system fetch origin`, then record `git rev-parse origin/rebuild/base` and `gh pr list --base rebuild/base --state open`. Confirm `gh auth status` succeeds, because every PR operation uses the `gh` CLI.
- [ ] Re-base the clock. ARCHITECTURE 8.2 assumed packet 0 merged on Monday night. Planning finished on Tuesday 13 October, so every gate starts late. Keep the gate order, write the real times into the ledger, and apply the drop order (Q14) at the first missed gate.
- [ ] On the operator's hold or stand-down, send every running builder a zero-writes order at once, then follow Pause and resume.

### Spawn owners

- [ ] Spawn one `poteto-agent` builder per packet on Opus 5.5, in the background, with the builder prompt from `ORCHESTRATOR-PROMPT.md`. A builder never spawns sub-agents.
- [ ] Run at most three builders at once. Follow this dependency graph. Start a packet only after every packet it depends on has merged.
  - [ ] 0a, 0b and 0c are independent and first.
  - [ ] 1a after 0a. 1b and 1c after 1a, in parallel.
  - [ ] Lane A is 2, then J23, then 4b, then S. Lane B is 3a and 3b, then J23. Lane C is 4a, then 5a and 5b.
  - [ ] 2 after 1b, 1c, P3 and P5. 3a and 3b after 1c. 4a after 1c and P4.
  - [ ] Critical path is 0a, 1a, 1c, 2, J23, 4b, S, 6. When slots compete, the critical-path packet wins.
- [ ] Hold the file boundaries. A builder edits only the files in its packet's Files box, its tests, and its docs. A needed file outside that list is a stop. The builder reports it and the orchestrator decides.
- [ ] Hold the shared-file rule. `ctl/agent_ops.py`, `ctl/server.py`, `docs/changelog.md` and this plan are touched by several packets. The packet that merges second rebases and resolves. The orchestrator never resolves a conflict.
- [ ] Hand out decision ids so parallel builders never collide. Each packet owns three ids, in landing order. 0a owns DEC-0511 to 0513, 0b owns DEC-0514 to 0516, and so on through 5b (DEC-0547 to 0549). S, 6 and 7 share DEC-0550 to 0558. Before dispatch, confirm with `git grep -o "DEC-0[0-9]*" origin/rebuild/base -- docs` that the block is unused, and shift every block up if it is not.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Use `gh`. Record in the ledger that Origin and Graphite are not used.
- [ ] The orchestrator creates the worktree before dispatch, from the planning worktree, without moving its HEAD. Run `git -C D:\QMX-worktrees\agent-system worktree add -b qma2/p<id>-<slug> D:\QMX-worktrees\qma2-p<id> origin/rebuild/base`. Never run `git checkout`, `git switch` or `git reset` in `D:\QMX-worktrees\agent-system`.
- [ ] The builder reads ARCHITECTURE section 8.1 for its row, the sections that row cites, and the PRD rows for its FRs before writing any code.
- [ ] The builder runs `just ci` once before the PR-facing push, under the CI recipe in `ORCHESTRATOR-PROMPT.md`. That recipe puts TMP, TEMP and the uv cache on D:, unsets `ANTHROPIC_*`, checks that rclone is on PATH, and holds `D:\QMX-worktrees\.ci-lock` exclusively. Push with hooks on.
- [ ] The builder opens the PR ready, never draft, with `gh pr create --base rebuild/base`. The body states the goal, the FRs, the done-when command with its output tail, the `just ci` summary table, and the docs changed. It carries no Claude attribution line, no `Co-Authored-By` trailer, and no "Generated with" footer. `comment-sicko` is optional before the PR.
- [ ] The builder rebases onto the current `origin/rebuild/base` before reporting code-ready. P16c PRs may still land there.

### Verdict and merge, for every PR

- [ ] The orchestrator verifies at the code-ready head SHA, in its own worktree `D:\QMX-worktrees\qma2-verify-p<id>` created with `git worktree add --detach`. It does not trust the builder's report or any green check (the P16b lesson).
  - [ ] Diff audit. `gh pr diff <n>` touches only the packet's Files box, tests and docs. No secret, no attribution line, no new GitHub workflow file.
  - [ ] Done-when. Run the packet's exact command. Save the output to `logs\p<id>-<sha7>-done.log`.
  - [ ] Regression lane against base. Run the packet's acceptance file at the base SHA. It must fail or be absent. Run every merged packet's acceptance file at the head. All must pass.
  - [ ] Full suite. Run `just ci` under the CI recipe. Save `logs\p<id>-<sha7>-ci.log`.
  - [ ] Assertion audit. Read the acceptance file. Each test asserts a literal expected value. A test that would still pass if the code under test returned `None` is a FAIL.
  - [ ] Docs audit. Every doc the packet's Files box names changed in this PR.
- [ ] Record the verdict as `PASS`, `PASS+NOTES` or `FAIL` with head SHA, base SHA and `git patch-id --stable` in the ledger, and post it as a PR comment with `gh pr comment`.
- [ ] A `FAIL` goes back to a fresh builder with consolidated scope (the original prompt, the findings, the branch). Two failed fix rounds on one packet is a stop for the operator.
- [ ] Land only the contiguous verified run in dependency order. Before merging, fetch, confirm the PR is based on the current `rebuild/base` tip, and compare the patch-id with the verdict's. A changed patch-id means a fresh verification.
- [ ] Merge with `gh pr merge <n> --merge`, the method the P16 PRs used on `rebuild/base`. Never pass `--admin`, `--auto` or `--delete-branch`. Record the merge SHA. Then remove only the verify worktree you created, with `git worktree remove` and no `--force`.

### Boot recipe, for every live lane

- [ ] Boot from the verify worktree at the head SHA. Start the host with `uv run --directory qmx-agents qmx-control start` once 1b exists, and read the one-time console link it prints. Live Claude calls happen only inside the windows in Budget the live windows.
- [ ] Drive the console in the Browser pane at `http://127.0.0.1:<port>/console`. Drive the API with `Invoke-RestMethod`. Read `control.log` and the run journal as read-only diagnostics.
- [ ] Save every screenshot to `D:\QMX-worktrees\qma2-ship\shots\p<id>\<slug>.png` and list the paths in the verdict comment.

### Run the probes and apply the results

- [ ] The orchestrator runs P3 and P5 in window W0, after the operator has signed Claude into `D:\QMX-data\claude` (homework step 2). P5's `qmx-agent` items need Q10 yes and homework step 6. Without them, P5 records those items as SKIP.
- [ ] The operator runs P1 (`uv run python scripts/probe/p1.py`, one browser click). It needs no Claude usage.
- [ ] The orchestrator runs P4 after 1a merges, because P4 drives the real `Store`. P2 is deferred to Thursday.
- [ ] Apply each result before dispatching the packet it blocks. A failure moves only that packet onto its fallback. It does not delay the others.

| Probe | If PASS | If FAIL, the plan changes to |
|---|---|---|
| P1 SIWC | 3b enables GPT rows | 3b ships GPT rows disabled with the reason. Q5's answer applies. Nothing else moves |
| P3a defer in streaming | 2 builds `defer` parking | 2 builds live approvals only. FR-104 on Claude holds only through re-ask. Tell the operator |
| P3b 30-minute live hold | `park_release_minutes` stays at its default | 2 sets `park_release_minutes` to the measured bound |
| P3c multi-call ratio | Report the ratio | Report the ratio in ARCHITECTURE section 9 item 3 |
| P3d defer in a sub-agent | No change | No defer in sub-agents, as designed |
| P3f sibling calls in the hook | Sibling rule in the hook | The sibling rule becomes prompt-only. Report P3c's ratio in section 9 |
| P4 load | One `control.db` file | 4a starts after a 1a follow-up PR (1a-split) moves `usage_ledger` and `events` to a hot file and checkpoints to their own file |
| P5 #902 tools | In-process MCP tools | 2 serves tools over a stdio FastMCP server |
| P5 dangling `tool_use` | Resume by id | 2's truncated-turn check starts a fresh session |
| P5 `files_persisted` | Receipts verified | Built-in writes stay `verified=false` until a git diff |
| P5 `SpawnTransport` | `SpawnTransport` as `qmx-agent` | 2 uses the `cli_path` shim. If both fail, the whole host runs in the Job Object as the operator user and Q10 waits for NEXT |
| P5 firewall rule | Per-user egress rule | Egress stays pattern-based. Section 9 item 1b says so |

### Place the six delta-4 items

Each item from HOW-WHY F4 lands in the packet below. The packet's Build box names it again, and its verdict checks it.

| F4 item | Packet | What lands |
|---|---|---|
| 2 (U3, U10) | 1b | `start` mints the one-time code and passes it on the child's stdin. The gate gets a path allowlist for `/console` and the code exchange |
| 3 (U8) | 1b | `ctl/node.py` reads its own `qmx/road-signing-key` from the node vault and passes it to `create_app` |
| 4 (U1) | 2 | The `qmx-agent` password lives under `qmx/agent-user-password`. The label joins the deny patterns and the manifest refusals |
| 5 (U6) | 0b | The `qmx-tools` child computes content-addressed Library refs and returns content with its ref. The host proxy writes the bytes |
| 6 (U9) | 5a | Refusals live in `apps/manifest.py` near line 178. `QMX_APP_TOKEN` joins `SYSTEM_ENV` |
| 7 (U13) | 1a | A retention rule for `events` and `blocks`, or a size alarm, keeps `control.db` under the 95 MB backup cap |

### Budget the live windows

The Max 5x plan pays for every builder run and every live Claude check. Builders run on fakes and the replay adapter. Live Claude runs only in these windows. Before each window, read the plan meter (`usage_summary` after 3b, before that the session's usage tool or the operator's reading). Skip the window if less than 30 percent is left, and tell the operator. Per packet, the budget is one builder run plus at most two fix rounds. A third round is a stop for the operator.

| Window | When | What runs |
|---|---|---|
| W0 | Tue morning, after homework step 2 | P3 (including 20 sample tasks for P3c) and P5 |
| W1 | Tue evening | Packet 2 agent-live |
| W2 | Wed 02:00 to 06:00 | J23, 4b agent-live, S scenarios (two rounds at most) |
| W3 | Wed 09:00 | The operator's rehearsal. No other live Claude call after 07:00 |

### Stop for the operator

The orchestrator stops and asks at these points, and nowhere else. It asks once, with a recommendation, after the operator has read what he needs.

- [ ] Go. The operator approves this plan. Nothing starts before that.
- [ ] Answers, wanted by Tue 12:00. Q9 to Q15 and R1, R2 in ARCHITECTURE 6.2, plus HOW-WHY F4 item 8 (weekly backups send chats and approvals to the private GitHub repo, or `control.db` goes to the bucket only) and F4 item 9 (Q10 now includes the firewall rule). Until he answers, builders use the recommendations, except Q10, Q11 and Q15, which need him.
- [ ] Q10 setup. If Q10 is yes, he runs homework step 6, which creates the `qmx-agent` user and moves the Claude home. P5's `qmx-agent` items and packet 2's spawn path wait for it.
- [ ] Sign-in steps, by Tue 18:00. Homework steps 2 to 5 and 7 in ARCHITECTURE 7.2 (Claude sign-in into `D:\QMX-data\claude`, one DeepSeek or GLM key, the rented-provider token, its price and a dashboard spend cap, the optional ChatGPT sign-in, the seat switch). P3 and P5 cannot run before step 2. He runs P1 after the ChatGPT sign-in.
- [ ] Homework step 1. If 0c finds that GitHub Actions needs an account or billing click, that click is his.
- [ ] Operator-live checks. 3b's wizard run and 5b's real-provider run.
- [ ] Any `FAIL` after two fix rounds, any blocked merge that would need `--admin`, and any needed file outside a packet's list.
- [ ] Thursday's deletion wave (packet 7). It deletes a package, so it waits for his go.

The orchestrator sends one short status message at each milestone. The milestones are packet 0 merged, the probe results, 1a to 1c merged, J23 result, the S scenarios, the rehearsal result. Each message names what merged, what failed and the action taken, what fallback fired, and what he must do next.

### Keep the docs live

- [ ] 0a copies `tracker/qma-v2/` from `D:\QMX-worktrees\agent-system` into `rebuild/base`, so code and plan docs land together. From then on, every packet edits the `rebuild/base` copy.
- [ ] Every packet updates, in the same PR, the component page ARCHITECTURE 8.4 names for it, the package README it changes, its DEC entries in `docs/changelog.md`, and any `tracker/qma-v2/*` text its build made untrue.
- [ ] Every packet ticks its own boxes in this file. A fallback that fires is written into ARCHITECTURE section 7 or 9 in the packet that applies it.

### Pause and resume

- [ ] On a usage-limit stop, operator pause, or context pressure, follow `pause-safely.md`. Start nothing new. Tell each builder to commit its work as one `wip:` commit on its own branch and stop. Write `D:\QMX-worktrees\qma2-ship\RESUME.md` with the ledger state, running builders, open PRs, the next action, and the clock.
- [ ] On resume, follow `session-pickup.md`. Read `RESUME.md` and `LEDGER.md`, run `gh pr list --base rebuild/base`, and trust only what the branches, PRs and logs show. Re-verify any PR whose head moved since its verdict. Give unfinished packets to fresh builders with consolidated scope.

## Subtract and scaffold the `qma2` package (0a)

**Goal.** Delete the dead agent cores, create `qma-v2` with the moved guards, and make CI see it. **FRs.** 006, 073, 074, 076, 078, 129, 144. **Parallel.** With 0b and 0c. **Budget.** One run, fakes only. **Risk.** The import-linter cannot forbid a PEP 420 namespace root. **Fallback.** A test that walks `qma2` imports and fails on `qma.` or `qmx_`.
**Depends on.** None. First packet.
**Files.**
- [ ] Code. `qmx-agents/pyproject.toml`, `qmx-agents/uv.lock`, `tools/ci.py`, `tools/test_all.py`, `qmx-apps/pyproject.toml`, `apps/supervisor.py`, `apps/road/*`, `remote/models.py`, `remote/runs.py`, the two example `app.toml` files, new `qmx-agents/packages/qma-v2/`. Delete `qmx-agents/plugins/` and the two example apps' agent cores.
- [ ] Docs. `tracker/qma-v2/` copied in, `qmx-agents/packages/qma-v2/README.md`, `tracker/qma-v2/driver-recipe/` (copies of `native_claude.py`, `native_codex.py`, `native_sessions.py`), DEC-0511 to 0513.

**Build.**
- [ ] Create `qma-v2` and `qma2` with `types.py` stubs, `host/platform.py`, and the neutral guards moved from the old packages (ARCHITECTURE section 5 Guards row). Fix the four imports in `qmx-apps` and `qmx-remote`.
- [ ] Add the import-linter contract to the dev group. Pin `openai-agents` and `claude-agent-sdk` in `qma-v2` and `qmx-agents/uv.lock` (B3).
- [ ] Add `--workspace` and the `qma-v2` tasks to `tools/ci.py`. Drop `QMX_DATA_TOKEN` from both example manifests. Add the `works_today` smoke rows.
- [ ] Record the SQLite version and the WAL-reset exposure (B1) in `works_today` and the README. The fix itself lands in 1a (one writer thread) and on Thursday (the DLL).
- [ ] Record the P16c state. List open P16c PRs and assert whether `python -c "import qma.daemon"` works, in the README.

**You see.**
- [ ] `uv run --directory qmx-agents lint-imports` prints the `qma2` contract as KEPT, and `works_today` lists the SQLite version.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `packages/qma-v2/tests/acceptance/test_packet_0.py` asserts `qmx-apps` locks without `langchain` and records the `qma.daemon` state. Run `uv run python tools/ci.py --workspace qma-v2 && uv run --directory qmx-agents lint-imports && uv run --directory qmx-agents pytest packages/qma-v2/tests/acceptance/test_packet_0.py --basetemp D:\Temp\pytest-0a`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B).
- [ ] Lane 1. Regression lane against base. `just ci` passes at base and at head. Save `0a-ci.log`. Pass when both pass and the head runs the new `qma-v2` tasks.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. None. 0a changes no hot path.
**Review gate.** None. 0a is not review-gated.
**Merge.**
- [ ] Verdict PASS at the head SHA, patch-id unchanged, merged per Verdict and merge.

## Make `qmx-tools` return results only (0b)

**Goal.** The domain child stops writing. It returns content plus a content-addressed Library ref, and the host proxy writes the bytes (F4 item 5). **FRs.** None directly. It removes the second writer (HOW-WHY U6, Z7). **Parallel.** With 0a and 0c. **Budget.** One run, fakes only. **Risk.** A ref computed in the child differs from the one the Library computes. **Fallback.** The child calls the Library's own hashing function, and a test compares both refs on the same bytes.
**Depends on.** None. Runs beside 0a.
**Files.**
- [ ] Code. `tools/service.py`, `tools/servers.py`, `tools/registry.py` (only the `library_save` and research-save results), `qmx-tools` tests.
- [ ] Docs. `qmx-agents/packages/qmx-tools/README.md`, DEC-0514.

**Build.**
- [ ] `DomainContext` without a `ControlService`. Delete the child's `ControlService` (`tools/service.py:126-136`). `servers.py` reads the effect key from the request `_meta`.
- [ ] Large results return `{content, ref}` with the ref computed from the canonical content. The memo lookup stays a read of `library.db`.

**You see.**
- [ ] The FastMCP child starts and answers a call while another process holds the host lock.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] New test asserts the child's ref equals the Library's ref for the same bytes, and the child opens no writable connection. Run `uv run --directory qmx-agents pytest packages/qmx-tools/tests --basetemp D:\Temp\pytest-0b`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B).
- [ ] Lane 1. Regression lane against base. Run one backtest-memo call at base and at head. Save `0b-memo.log`. Pass when both return the same `run_id`.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. None. 0b moves a write, it does not add one.
**Review gate.** None. 0b is not review-gated.
**Merge.**
- [ ] Verdict PASS at the head SHA, patch-id unchanged, merged per Verdict and merge.

## Write the probes, find why Actions never runs, note B17 and B18 (0c)

**Goal.** The four probe scripts, the wizard skeleton, the Actions cause (B2), and the two research easy wins B17 and B18. **FRs.** None. **Parallel.** With 0a and 0b. **Budget.** One run. Writing the probes costs no live calls. Running them is W0. **Risk.** The Actions cause needs an account click. **Fallback.** Stop for the operator, and packets attach their local `just ci` log until a run starts. If time is short, B17 and B18 move to Thursday.
**Depends on.** None. Runs beside 0a.
**Files.**
- [ ] Code. `scripts/probe/p1.py`, `p3.py`, `p4.py`, `p5.py`, `scripts/operator_setup.py` (steps 1 to 7 as PASS or FAIL stubs, finished in 3b). No new workflow file.
- [ ] Docs. `tracker/qma-v2/probes/README.md` (how to run each probe, who runs it), `tracker/qma-v2/actions-cause.md`, `tracker/qma-v2/spikes/B17-ctrader-uia-checklist.md`, `tracker/qma-v2/research/B18-firecrawl-alexandria.md`, BACKLOG rows B2, B17 and B18, DEC-0517.

**Build.**
- [ ] Each probe prints PASS or FAIL with one sentence per case from ARCHITECTURE 7.1 and writes `tracker/qma-v2/probes/Pn.json`. Each takes `--dry`, which lists its cases as SKIP. `p4.py` imports `qma2.store` and runs only after 1a.
- [ ] Find why six active workflows never produced a run. Read `gh api repos/{owner}/{repo}/actions/permissions`, the workflow triggers, and the branch filters. Write the cause and the fix, or the click the operator must make.
- [ ] B17 lists the cTrader screens and controls to probe with UIA and the PASS rule for each. It runs nothing against cTrader. B18 records what Firecrawl's Alexandria catalogue offers for web and documentation work, with the source of each fact.

**You see.**
- [ ] `uv run python scripts/probe/p3.py --dry` prints the six case names with SKIP and exits 0.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Run `uv run python scripts/probe/p1.py --dry && uv run python scripts/probe/p3.py --dry && uv run python scripts/probe/p5.py --dry && uv run python scripts/operator_setup.py --dry`. Each exits 0 and prints its step list.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B).
- [ ] Lane 1. Regression lane against base. The scripts are absent at base. Run the dry commands at head. Save `0c-dry.log`. Pass when each prints its cases.
- [ ] Lane 2. Read `actions-cause.md`, B17 and B18. Pass when the cause carries a `gh api` or settings-page reading as evidence, and every B18 claim carries a source.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. None. 0c adds scripts only.
**Review gate.** None. 0c is not review-gated.
**Merge.**
- [ ] Verdict PASS at the head SHA, merged per Verdict and merge. Then run W0 and record the P3 and P5 results in the ledger.

## Build the store, types, journal and settings (1a)

**Goal.** One writer thread per file, frozen shared types, the run journal, and `SettingsFile`. **FRs.** 106, 127. **Parallel.** Alone. Everything after it imports its types. **Budget.** One run, fakes only. **Risk.** It lands late and blocks three lanes. **Fallback.** ARCHITECTURE 8.2 Tue 12:00 rule. Packet 2 starts on an in-memory `Store` with the same interface, and 1a lands by Tue 18:00.
**Depends on.** 0a.
**Files.**
- [ ] Code. `qma2/types.py`, `qma2/store.py`, `qma2/store/migrations/001.sql`, `qma2/journal.py`, `qma2/settings.py`, `ctl/service.py`, `ctl/backup.py`.
- [ ] Docs. `docs/components/qma-store.md`, DEC-0520 (single writer) and DEC-0521 (no journal table).

**Build.**
- [ ] `Store` writer thread with `submit`, the OS lock, SAVEPOINT per `Write`, `quick_check`, migration 001 with every table and no settings table.
- [ ] `_connect` and `RunIndex.record` go through `Store.submit`, which closes B1's two-writer exposure. `control.db` joins the backup list with checkpoint pruning.
- [ ] F4 item 7. A retention rule for `events` and `blocks`, or a size alarm in `ctl/backup.py`, so `control.db` never trips the 95 MB cap.

**You see.**
- [ ] A second launcher prints the lock refusal and exits non-zero.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `test_packet_1a.py` covers the 8.1 list plus the retention or alarm case. Run `uv run --directory qmx-agents pytest packages/qma-v2/tests/acceptance/test_packet_1a.py --basetemp D:\Temp\pytest-1a`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B).
- [ ] Lane 1. Regression lane against base. Run the weekly backup at base and at head on a copy of the data folder. Save `1a-backup.log`. Pass when head includes `control.db` and `qmx-broker` still reads `settings.toml`.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. P4 (`scripts/probe/p4.py`), run after merge. Base has no `Store`, so the rule is absolute. p95 write under 50 ms, no `database is locked`, `quick_check` ok, event-loop lag p95 under 20 ms. A miss fires the P4 fallback.

**Review gate.** None. 1a is not review-gated.
**Merge.**
- [ ] Verdict PASS at the head SHA, patch-id unchanged, merged per Verdict and merge. Then run P4.

## Run a copilot turn through the API with principals and the console (1b)

**Goal.** A turn over the API on `FakeAdapter`, `recover()`, the console, three principals, and the operator code channel. **FRs.** 003, 004, 013, 014, 126, 128, 130. **Parallel.** With 1c. **Budget.** One run, fakes only. **Risk.** The named pipe's caller check is wrong on Windows. **Fallback.** The pipe refuses every caller and only `start` hands out codes. Report the gap.
**Depends on.** 1a.
**Files.**
- [ ] Code. `qma2/engine/facade.py`, `qma2/engine/fake.py`, `qma2/host/turns.py`, `qma2/host/recover.py`, `qma2/host/console.py`, `qma2/events/live.py`, `qma2/policy/principals.py`, `ctl/server.py`, `ctl/__main__.py`, `ctl/agent_ops.py`, `ctl/node.py`, `ctl/static/console.html`, `apps/road/__init__.py`.
- [ ] Docs. `docs/contracts/qma-event-protocol.md`, `docs/contracts/principals.md`, the UI handoff packet (`openapi.json`, `openapi-operator.json`, SSE fixtures), DEC-0523 (principals).

**Build.**
- [ ] The 8.1 scope list, including `who: Principal` on every service method and the token-free `/api/health`.
- [ ] F4 item 2. `start` mints the one-time code and passes it on the child's stdin. The gate gets a path allowlist for `/console` and the code exchange.
- [ ] Revision 3a. `qmx-control token` asks the host over `\\.\pipe\qmx-operator`, ACL'd to the operator account, with the client-process user check, 60 s single-use codes.
- [ ] F4 item 3. `ctl/node.py` reads its own `qmx/road-signing-key` and passes it to `create_app`.

**You see.**
- [ ] `qmx-control start` opens `/console#<code>`. The page streams a fake turn and the code does not appear in `control.log`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `test_packet_1b.py` covers the 8.1 list plus the stdin hand-off, the allowlist, and the node signing key. Run `uv run --directory qmx-agents pytest packages/qma-v2/tests/acceptance/test_packet_1b.py --basetemp D:\Temp\pytest-1b`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B).
- [ ] Lane 1. Regression lane against base. Base has no console. At head, start the host, open the link, send a turn. Save `1b-console.png`. Pass when typed blocks stream.
- [ ] Lane 2. Start three errands, `taskkill /F` the host, restart. Save `1b-restart.png`. Pass when all three resume and the banner lists them.
- [ ] Lane 3. Call each operator door with an agent token. Save `1b-403.log`. Pass when every call returns 403.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. First-event latency on the fake engine (NFR-032). Base has no turn route. Rule is absolute. Under 2 s at p95 over 20 turns.

**Review gate.** None. 1b is not review-gated. The orchestrator sends the operator `1b-console.png` with the milestone message.
**Merge.**
- [ ] Verdict PASS at the head SHA, patch-id unchanged, merged per Verdict and merge.

## Build the policy core (1c)

**Goal.** One claim point for every tool call, the deny list, approvals and effects. **FRs.** 051, 102, 104, 105, 108. **Parallel.** With 1b. **Budget.** One run, fakes only. **Risk.** The args-hash guard repeats a keyed effect on resume. **Fallback.** None needed on the WED path. A failing case blocks merge.
**Depends on.** 1a.
**Files.**
- [ ] Code. `qma2/policy/*` (except `principals.py`), `qma2/events/tool_names.py`.
- [ ] Docs. `docs/components/qma-approvals.md`, DEC-0526 (live-primary approvals).

**Build.**
- [ ] The 8.1 scope list. `normalise_tool_name` runs before `match_money_path_act`.
- [ ] Revision 3a. `decide_builtin` denies `qmx-control token`, any pipe path matching `qmx-operator`, and credential-store reads, by pattern. The labels live in one `PROTECTED_LABELS` constant in `qma2/policy/deny.py`.

**You see.**
- [ ] A fake turn that asks to place an order ends with a denial row in the journal.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `test_packet_1c.py` covers the 8.1 list plus the pipe and token patterns. Run `uv run --directory qmx-agents pytest packages/qma-v2/tests/acceptance/test_packet_1c.py --basetemp D:\Temp\pytest-1c`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B).
- [ ] Lane 1. Regression lane against base. Base has no invoker. At head, raise an approval, `taskkill /F` the host, restart, answer it. Save `1c-approval.log`. Pass when the call runs exactly once.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. None. `invoke` overhead is measured with 2.
**Review gate.** None. 1c is not review-gated.
**Merge.**
- [ ] Verdict PASS at the head SHA, patch-id unchanged, merged per Verdict and merge.

## Run the Claude engine live (2)

**Goal.** `ClaudeAdapter` on his plan with its own home, the watchdog, and the general plugin. **FRs.** 001, 020, 021, 022, 032, 091, 093, 096, 097, 120, 126, 133, 141. **Parallel.** With 3a, 3b and 4a, three at once at most. **Budget.** One run on the replay adapter, then window W1. **Risk.** P3 or P5 fails. **Fallback.** The P3 and P5 rows in Run the probes.
**Depends on.** 1b, 1c, P3 and P5 results.
**Files.**
- [ ] Code. `qma2/engine/claude.py`, `claude_transport.py`, `normalise_claude.py`, `cap.py`, `watchdog.py`, `qma2/prompts/*`, `qma2/memory.py`, `qma2/plugins/general/*`, `qma2/host/platform.py`, `qma2/policy/deny.py` (the label only), `apps/manifest.py` (the label refusal only), `scripts/live/packet_2.py`.
- [ ] Docs. `docs/components/qma-claude-engine.md`, DEC-0529.

**Build.**
- [ ] The 8.1 scope list, shaped by the P3 and P5 results.
- [ ] F4 item 4. Name the vault label `qmx/agent-user-password`. Add it to `PROTECTED_LABELS`, so the deny patterns cover it, and refuse it in `apps/manifest.py`.

**You see.**
- [ ] A console turn on Claude streams a tool call, and turn 2 shows cache reads above 0.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `test_packet_2.py` runs replay fixtures and the FR-020 suite. Run `uv run --directory qmx-agents pytest packages/qma-v2/tests/acceptance/test_packet_2.py --basetemp D:\Temp\pytest-2`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B). Window W1.
- [ ] Lane 1. Regression lane against base. Base has no Claude engine. Run `uv run python scripts/live/packet_2.py`. Save `2-live.log`. Pass when every 8.1 case prints PASS, including `~/.claude` byte-identical and the shell keyring read refused.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. First streamed event on Claude, absolute budget under 2 s at p95 over 5 live turns (NFR-032).

**Review gate.** None. 2 is not review-gated.
**Merge.**
- [ ] Verdict PASS at the head SHA, patch-id unchanged, merged per Verdict and merge.

## Load plugins and run the OpenAI engine (3a)

**Goal.** `PluginLoader` with lint and the parity table, Lab and Portfolio plugins, and `OpenAIAdapter`. **FRs.** 002, 005, 024, 025, 028, 030, 031, 035, 098, 132, 134, 138. **Parallel.** With 2 and 4a. **Budget.** One run, `ScriptedModel` only. **Risk.** A parked `RunState` does not survive a restart. **Fallback.** Park by re-ask on OpenAI too, and tell the operator.
**Depends on.** 1c.
**Files.**
- [ ] Code. `qma2/plugins/*` (except `general/`), `qma2/engine/openai.py`, `qma2/engine/normalise_openai.py`, `qma2/policy/registry.py`.
- [ ] Docs. `docs/components/qma-plugins.md`, DEC-0532.

**Build.**
- [ ] The 8.1 scope list, with `parallel_tool_calls=False` and the allow-hook strip test.

**You see.**
- [ ] Lab and Portfolio on `FakeAdapter` list different tools, and the parity report lists dropped keys.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Run `uv run --directory qmx-agents pytest packages/qma-v2/tests/acceptance/test_packet_3a.py --basetemp D:\Temp\pytest-3a`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B).
- [ ] Lane 1. Regression lane against base. Base has no loader. At head, park an OpenAI approval, `taskkill /F` the host, restart, answer twice. Save `3a-park.log`. Pass when the run resumes once.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. None. The live engine cost is measured in J23.
**Review gate.** None. 3a is not review-gated.
**Merge.**
- [ ] Verdict PASS at the head SHA, patch-id unchanged, merged per Verdict and merge.

## Route accounts, keep the ledger, finish the wizard (3b)

**Goal.** Account rows, the family guard, the router, the ledger, `usage_summary`, the credential door, and the finished wizard. **FRs.** 023, 026, 038, 039, 040, 041, 042, 046, 048, 049. **Parallel.** After 3a in lane B, beside 2 and 4a. **Budget.** One run, fakes only. **Risk.** P1 fails. **Fallback.** GPT rows ship disabled with the reason.
**Depends on.** 1c, P1 result.
**Files.**
- [ ] Code. `qma2/router/*`, `ctl/agent_ops.py`, `ctl/server.py`, `scripts/operator_setup.py`.
- [ ] Docs. `docs/components/qma-router.md`, DEC-0535.

**Build.**
- [ ] The 8.1 scope list, with `switch_model(dry_run=True)` only.

**You see.**
- [ ] `usage_summary` on a Claude-only fake day returns `billed_usd = 0.00`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Run `uv run --directory qmx-agents pytest packages/qma-v2/tests/acceptance/test_packet_3b.py --basetemp D:\Temp\pytest-3b`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B).
- [ ] Lane 1. Regression lane against base. Add an Anthropic-key row through the API. Save `3b-refuse.log`. Pass when it is refused with "Claude and GPT run on your plans only".
- [ ] Lane 2. Operator-live. He runs `uv run python scripts/operator_setup.py`. Save `3b-wizard.log`. Pass when each step prints PASS or a named SKIP.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. None.
**Review gate.** None. 3b is not review-gated. Lane 2 is his run, not a review.
**Merge.**
- [ ] Verdict PASS at the head SHA, patch-id unchanged, merged per Verdict and merge.

## Join the two engines live (J23)

**Goal.** Prove SC-3 and SC-6 live before anything builds on them. **FRs.** 024, 085, 086, 102. **Parallel.** No. It gates lane A. **Budget.** Window W2, one round. **Risk.** The DeepSeek row fails live. **Fallback.** Show the error card and run the helper on a second key provider if his homework added one.
**Depends on.** 2, 3a, 3b.
**Files.**
- [ ] Code `scripts/live/join_2_3.py`, docs `tracker/qma-v2/probes/J23.json`.

**Build.**
- [ ] The script runs the four 8.1 checks and prints PASS or FAIL per check.

**You see.**
- [ ] Lab on Claude and Portfolio on OpenAI list their own tools, with no order tool in either.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Run `just ci`. The script has no unit test of its own.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B). Window W2.
- [ ] Lane 1. Regression lane against base. Run `uv run python scripts/live/join_2_3.py`. Save `J23.log`. Pass when all four checks print PASS, including the agent-token 403 on the approval door.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. None.
**Review gate.** None. J23 is not review-gated.
**Merge.**
- [ ] Verdict PASS at the head SHA, merged per Verdict and merge.

## Run workflows on the new runner (4a)

**Goal.** The runner over `workflow.v1.1` with eight kinds, checkpoints in `control.db`, and `gold-morning-check`. **FRs.** 052 to 062, 121. **Parallel.** Lane C, beside 2 and 3a. **Budget.** One run, fakes only. **Risk.** P4 fails. **Fallback.** The 1a-split PR lands first.
**Depends on.** 1c, P4 result.
**Files.**
- [ ] Code. `qma2/graph/*`, `ctl/agent_ops.py`, `examples/workflows/gold-morning-check.json`.
- [ ] Docs. `docs/components/qma-runner.md`, DEC-0538.

**Build.**
- [ ] The 8.1 scope list. Finished nodes are skipped on resume, and two crash-resumes end `interrupted`.

**You see.**
- [ ] `gold-morning-check` runs on fakes with 0 model calls on the false branch.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Run `uv run --directory qmx-agents pytest packages/qma-v2/tests/acceptance/test_packet_4a.py --basetemp D:\Temp\pytest-4a`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B).
- [ ] Lane 1. Regression lane against base. Base returns 501 on `workflows_run`. At head, run `gold-morning-check`, `taskkill /F` mid-run, restart. Save `4a-resume.log`. Pass when finished nodes are skipped and no keyed effect repeats.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. None beyond P4.
**Review gate.** None. 4a is not review-gated.
**Merge.**
- [ ] Verdict PASS at the head SHA, patch-id unchanged, merged per Verdict and merge.

## Delegate to helpers through the broker (4b)

**Goal.** The broker with leases, `delegate`, `job_*`, and the reader role. **FRs.** 015, 084, 088, 089. **Parallel.** No. Lane A after J23. **Budget.** One run on fakes, then window W2. **Risk.** The helper's cost does not roll up under the parent. **Fallback.** Show the run index rows side by side and say so on the card.
**Depends on.** J23, 4a.
**Files.**
- [ ] Code. `qma2/comms/*`, `scripts/live/packet_4b.py`.
- [ ] Docs. `docs/components/qma-broker.md`, DEC-0541.

**Build.**
- [ ] The 8.1 scope list. A worker's spawn is refused at depth 1.

**You see.**
- [ ] The run index shows Opus for the parent and DeepSeek for the helper.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Run `uv run --directory qmx-agents pytest packages/qma-v2/tests/acceptance/test_packet_4b.py --basetemp D:\Temp\pytest-4b`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B). Window W2.
- [ ] Lane 1. Regression lane against base. Run `uv run python scripts/live/packet_4b.py`. Save `4b-live.log`. Pass when the copilot writes, validates, runs, edits and reruns a 3-node workflow, and SC-4 prints PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. None.
**Review gate.** None. 4b is not review-gated.
**Merge.**
- [ ] Verdict PASS at the head SHA, patch-id unchanged, merged per Verdict and merge.

## Rewrap mini apps with their own token (5a)

**Goal.** Host-assigned trust, "disabled until approved", the app token, the manifest refusals, and the Macro fixtures. **FRs.** 072, 075, 077, 079. **Parallel.** Lane C with 5b. **Budget.** One run, fakes only. The Macro rebuild live is a stretch. **Risk.** Time. **Fallback.** Q14 drop 1. Show the review-repair counter and the unverified label.
**Depends on.** 2, 4a.
**Files.**
- [ ] Code. `apps/supervisor.py`, `apps/manifest.py`, `qma2/client.py`, `examples/apps/*`.
- [ ] Docs. `qmx-agents/packages/qmx-apps/README.md`, `examples/apps/macro-daily-bias/PARAGRAPH.md`, DEC-0544.

**Build.**
- [ ] The 8.1 scope list.
- [ ] F4 item 6. The refusals of `qmx/control-token`, `qmx/road-signing-key`, `qmx/broker*` and every `PROTECTED_LABELS` entry sit in `apps/manifest.py` near line 178. `QMX_APP_TOKEN` joins `SYSTEM_ENV`, so a manifest cannot override it.

**You see.**
- [ ] An agent-built app installs disabled, and an approval enables it.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] `test_packet_5a.py` adds a manifest that sets `QMX_APP_TOKEN` (refused). Run `uv run --directory qmx-agents pytest packages/qma-v2/tests/acceptance/test_packet_5a.py --basetemp D:\Temp\pytest-5a`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B).
- [ ] Lane 1. Regression lane against base. Install `weekend-watcher` at base and at head. Save `5a-install.log`. Pass when head installs it with the app token and base behaviour for an approved app is unchanged.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Metric. `apps_call` deadline. Pass when a slow app times out at 20 s, not later.

**Review gate.** None. 5a is not review-gated.
**Merge.**
- [ ] Verdict PASS at the head SHA, patch-id unchanged, merged per Verdict and merge.

## Run a workflow on rented compute (5b)

**Goal.** The headless worker with idle limit, self-terminate, exit-on-approval, checkpoint export, fetch and cost. **FRs.** 110, 111, 112, 113, 119. **Parallel.** Lane C with 5a. **Budget.** One run on `FakeComputeProvider`. One real-provider attempt at Wed 06:00, paid by his cap. **Risk.** The provider is slow or refuses. **Fallback.** Q14 drop 2. The fake-provider run plus an honest card.
**Depends on.** 3b, 4a.
**Files.**
- [ ] Code. `remote/worker.py`, `remote/models.py`, `remote/providers.py`, `remote/runs.py`, `remote/Dockerfile`, `qma2/host/worker.py`, `qma2/host/placement.py`.
- [ ] Docs. `docs/components/qma-remote.md`, DEC-0547.

**Build.**
- [ ] The 8.1 scope list. Keys stay on the launch-time injection path and never enter the bundle or the bucket.

**You see.**
- [ ] On the fake provider, a run fetches with "hash verified" and machines alive returns to 0.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] Run `uv run --directory qmx-agents pytest packages/qma-v2/tests/acceptance/test_packet_5b.py --basetemp D:\Temp\pytest-5b`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B).
- [ ] Lane 1. Regression lane against base. Run `gold-morning-check` with `placement="remote"` on the fake provider. Save `5b-fake.log`. Pass when `cost_so_far` equals price times minutes.
- [ ] Lane 2. Operator-live, once. The same run on the real provider. Save `5b-real.log`. Pass when the fetch verifies hashes and the machine is gone.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. None. Rented minutes are reported, not gated.
**Review gate.** None. 5b is not review-gated.
**Merge.**
- [ ] Verdict PASS on lane 1 at the head SHA, merged per Verdict and merge. Lane 2 may follow the merge.

## Write the skills and the golden scenarios (S)

**Goal.** `build-workflow`, `build-mini-app` and `maintain-app` written against the real tools, and three golden scenarios. **FRs.** 035, 056, 072. **Parallel.** No. Lane A last. **Budget.** One run, then two live rounds in W2 at most. **Risk.** A scenario fails twice. **Fallback.** Ship the passing scenarios and show an honest card for the failing one.
**Depends on.** 2, 3a, 4a, 4b.
**Files.**
- [ ] Code. `qma2/plugins/*/skills/*`, `qma2/prompts/templates/*`, `scripts/live/scenarios.py`.
- [ ] Docs. `docs/scenarios/` (three scenarios), DEC-0550.

**Build.**
- [ ] The three skills and the three scenarios from 8.1.

**You see.**
- [ ] `scripts/live/scenarios.py` prints PASS for each scenario.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.
- [ ] The prompt snapshot tests pass in `just ci`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Orchestrator lanes at the PR head, not a swarm (Appendix B). Window W2.
- [ ] Lane 1. Regression lane against base. Run `uv run python scripts/live/scenarios.py`. Save `S-live.log`. Pass when all three print PASS.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. None.
**Review gate.** None. S is not review-gated.
**Merge.**
- [ ] Verdict PASS at the head SHA, merged per Verdict and merge. Feature freeze starts at Wed 09:00.

## Close the program

### Rehearse the Wednesday demo (6)

The rehearsal runs USER-JOURNEYS section 5 with the ARCHITECTURE 8.5 changes. It proves SC-1 to SC-6 or shows an honest card. SC-1, SC-3 and SC-6 are never dropped.

- [ ] Wed 06:00 dry run. The orchestrator walks each demo step on the `rebuild/base` tip with fakes. It records PASS, CARD (an honest card) or DROPPED per step in `docs/scenarios/wednesday-demo.md`, with a screenshot per step under `D:\QMX-worktrees\qma2-ship\shots\6\`.
- [ ] Every acceptance file passes on the tip. Run `uv run --directory qmx-agents pytest packages/qma-v2/tests/acceptance --basetemp D:\Temp\pytest-6`.
- [ ] Wed 09:00 rehearsal checkpoint. Confirm the pre-demo list. Homework done, `gold-morning-check.json` present, the Macro paragraph and fixtures present, the console open, `seats.portfolio.engine = openai`, Q15's instrument in the 9:00 step. Feature freeze starts now. Only fix-it PRs merge after this point, each verified like any other.
- [ ] The operator runs the 10-minute script in window W3. The console prints the 1:15 step's first-event latency, which must be under 2 s. He says whether it is ready.
- [ ] After the demo, a docs PR records the real outcome per step in `wednesday-demo.md`, ticks this file, and adds the milestone summary to `tracker/qma-v2/README.md`.

### Delete LangChain and clear the Thursday list (7)

Thursday starts only on the operator's go. Each item is one PR with a fresh builder and the same verification rules.

- [ ] 7a. Delete `qmx-agents/packages/qmx-agents` and edit `tools/test_all.py` in the same PR (F19). Done when `git grep -i -E "langchain|langgraph|deepagents" -- . ":!**/archive/**" ":!*.lock"` prints nothing and `just ci` passes with the suite count edited. Then re-run the Wednesday dry run. Every step that passed must still pass. If a hidden importer appears, revert the PR, list the importer, and delete it in a follow-up.
- [ ] 7b. Ship the SQLite 3.51.3 or newer DLL on Windows (the rest of B1), with a `works_today` row that shows the version.
- [ ] 7c. Run P2 (`setup-token` on a rented box) and write `tracker/qma-v2/probes/P2.json`.
- [ ] 7d. Run B4 and B5. Read P16c's final summary, then check mini apps, QML, QMF, QMN and the two example apps end to end. Write the findings note.
- [ ] 7e. Ask the operator about BACKLOG B11 (documentation-factory in change mode). Ask before editing either `CLAUDE.md`.

### Report the outcome

- [ ] Every box above is checked with its evidence, or marked dropped with the reason.
- [ ] Reply to the operator with what landed (PR numbers and merge SHAs), each verdict, which fallbacks fired, what was dropped, and the Thursday list.

## Appendix A. Prototype evidence

No prototype ran for this plan. The open empirical questions are the probes P1 to P5, which packet 0c writes and the program runs before the packets they block. Two facts were measured during planning. `origin/rebuild/base` is at 4eac8f69 (PR #70), and the planning branch `plan/agent-system` does not contain it, so `tracker/qma-v2/` is not on `rebuild/base` yet. `tools/test_all.py` already passes `-n 2` and its own `--basetemp`.

## Appendix B. Alternatives rejected

- **The ten-lane swarm per PR.** The poteto playbook asks for ten live lanes per PR on a swarm model. The operator's rules allow one builder per packet and no other agents, and the Max 5x plan cannot pay for ten lanes on fifteen PRs in two days. The orchestrator runs the lanes itself instead. It did not write the code, so its verdict is still independent. Perf blocks name one metric with an absolute rule instead of the four-part trunk comparison, because `rebuild/base` has none of these features to measure.
- **An hourly audit loop and trunk skill reads.** Builders run in the background and notify on completion, so a `/loop 1h` tick spends plan usage for little. The pstack skills live in `~/.claude/skills`, not on `origin/main`, so the orchestrator reads them from disk.
- **One PR for all of packet 0.** Packet 0 mixes deletions, a new package, a writer change in `qmx-tools`, probes and research notes. Three PRs run in parallel and fail separately.
- **Docs on the planning branch only.** The code would land on `rebuild/base` while its plan stayed on `plan/agent-system`. 0a moves the plan next to the code.
- **Acceptance tests under `src/qma2/tests`.** ARCHITECTURE writes `qma2/tests/acceptance`. Every package here keeps `tests/` beside `src/`, so the files go under `qmx-agents/packages/qma-v2/tests/acceptance/`. 0a records that path in ARCHITECTURE 8.1.

## Appendix C. Risks

- The clock is already late (Arm the program). The drop order fires earlier than ARCHITECTURE 8.2 planned.
- Builder runs and live checks share one Max 5x plan. A usage-limit stop is likely. Pause and resume covers it.
- `ctl/agent_ops.py` and `ctl/server.py` change in 1b, 3b and 4a. The second PR's rebase changes its patch-id and costs a re-verification.
- GitHub Actions has never run. Until 0c's fix lands, the only CI evidence is the local `just ci` log.
- A branch protection rule on `rebuild/base` may block merges without a check. That is a stop, never `--admin`.

## Appendix D. Links and reading list

Read `tracker/qma-v2/ARCHITECTURE.md` (sections 2.0, 2.12, 5 to 10), `HOW-WHY.md` delta pass 4, `PRD.md` section 1.3 and each packet's FR rows, `USER-JOURNEYS.md` section 5, and `ORCHESTRATOR-PROMPT.md`. The playbooks are `~/.claude/skills/poteto-mode/playbooks/orchestrate.md`, `shipping.md`, `pause-safely.md` and `session-pickup.md`.
