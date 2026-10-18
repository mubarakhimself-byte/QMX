# QMX hardening program plan

This program hardens what the engine program built and adds the designed pieces the rerun settled. It follows `architecture/workflow-engine/` (AD-1 to AD-51, amended by `research/methodology/39-architecture-rerun.md` with "Review applied" and "Fix-check applied"), the re-triage in `40-retriage.md`, and the rulings in `26-operator-rulings-and-alignment.md`.
The operator gets an engine with no QMX usage caps and a stuck detector, redaction and safer scripts, the run-state bugs fixed, the engine inside `qma.serve`, a model router with a registry and an in-house pool, and plain-named templates with a working copilot builder.
The rule it enforces is that every invariant a PR adds has a live check that ran green at that PR's head, and that no PR edits the harness unless its packet names the grant or ruling that allows it.
There are 25 PRs, in the order of "Order and gates" below. Eight need no call and no merge click. Ten wait only for his merge click. Seven wait for one of his parked calls D, E, F or G and are marked BLOCKED-ON.
The stack base is `rebuild/base` once it holds `engine/base` at `132169c71c3bb372c67ab330066f938e5dc6a56d`. Until his merge click, the engine-only PRs stack on `engine/base` at that SHA.

## How to read this

One box is one unit of work. Every box names the evidence that checks it. A nested box is a sub-step of the box above it. Check a box only when its evidence exists, a file, a log line, a screenshot, a test run, or a SHA. The body is a how-to. The appendices explain and record.

Each PR section opens with a short preamble. It names the triage rows (B-n, L-n and AL-n of `40-retriage.md` section 2), the AD ids, the gate, the proving check, and the done line. Then come the nine blocks `check-plan.mjs` requires.

Path shorthands, used in every Files block.

- `E/` is `qmx-agents/packages/qmx-engine/src/qmx_engine/` and `ET/` is `qmx-agents/packages/qmx-engine/tests/`.
- `H/` is `qmx-agents/packages/qma-harness/src/qma/harness/` and `HT/` is `qmx-agents/packages/qma-harness/tests/`.
- `QC/` is `qmx-agents/packages/qma-core/` and `QX/` is `qmx-agents/packages/qmx-control/src/qmx_control/`.
- `T/` is `E/templates/`. `SL/` is `scripts/live/` and `SP/` is `scripts/probes/`.
- The store is `D:/QMX-worktrees/qma-ship/hardening/`.

The program runs `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md`. The selection rule at the end of that playbook picks it, because the work is sequenced and the operator reviews before anything lands. Nothing merges in this program. The coordinator appends each verified PR to one linear stack, and the operator lands it himself.

The plan makes eight overrides. Each is named again where it applies.

- Override 1 replaces autopilot-stack step 1's owner. One `poteto-agent` builder on `opus` per PR runs on the operator's PC in its own worktree, not a Cursor cloud agent. `/deslop` is not installed, so the builder rereads its full diff instead. No Bugbot runs on this repo.
- Override 2 replaces step 4's verdict with the operator's light rule (memory `light-verification-per-pr`). One build and one independent check per PR. The checker is a second `poteto-agent` on `opus`. Only blockers and anything touching money, his logins or keys block. Low findings go to `lows.md` and never block. One fix round per PR.
- Override 3 is the lane count. `check-plan.mjs` demands ten lanes per PR. Here the ten lanes are a menu, not a quota. Lanes 1 to 4 are the proving set the checker runs, plus at most one menu lane it judges likeliest to break the PR's point. A lane box outside the run set is checked with a `ledger.tsv` row that says `menu, not run`.
- Override 4 is the perf block. No speed gate runs unless speed is the PR's point. Every perf block records a number for the trail and fails nothing, except where a Rule box names a fail line.
- Override 5 is the rebase cadence. A PR's one fix round finishes before a PR that shares a file with it is built on top. The stack is rebased once per fix, never per round, and never onto a moving trunk.
- Override 6 is one planned rebase at the merge-click gate. When `rebuild/base` first holds `engine/base`, the root rebases the engine-only chain onto `rebuild/base` once and retargets the root PR. The six files `rebuild/base` adds touch no packet's files, so patch-ids stay the same.
- Override 7 is the blocked-packet rule. A packet marked BLOCKED-ON is skipped, never waited on. When its call is granted, it is built on the stack tip of that moment and appended there. It never goes into the middle of the verified stack.
- Override 8 replaces poteto-mode's "fresh subagents by default" for fix rounds. The same builder is resumed for its one fix round, because a fresh agent rereads the design, the plan and the code (WORKFLOW-SHIP-PREP lesson 10). Every other new task gets a fresh agent.

Opus checking Opus is weaker than a review across model families. Every checker report says so in its first lines. No Fable runs in this program.

Defaults are marked. Every value this plan sets that the operator did not choose says "Claude's default" where it appears, and Appendix H lists them all.

Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

## Program checklist

### Arm the program

- [ ] Check the bases. Run `git -C D:/QMX-worktrees/agent-system fetch origin`, then `git rev-parse origin/engine/base`, which must print `132169c71c3bb372c67ab330066f938e5dc6a56d`. Then run `git merge-base --is-ancestor origin/engine/base origin/rebuild/base`. Exit 0 means his merge click has landed and the stack base is `rebuild/base`. Exit 1 means it has not, and the engine-only chain roots on `engine/base` until the gate (Override 6). Log both lines in `decisions.tsv`.
- [ ] Read the plan from its branch with `git -C D:/QMX-worktrees/agent-system show plan/agent-system:tracker/qma-v2/HARDENING-PLAN.md`. If the file is not committed there, stop and ask the operator to have it committed, because every tick re-reads it from the branch.
- [ ] State the protocol and this plan to the operator in plain words, then stop. Start only on his explicit go.
- [ ] In the same message, list what only he can do, with a time for each. Log his answers in the store's `decisions.tsv`.
  - [ ] Say go. About one minute.
  - [ ] Click the merge of `engine/base` into `rebuild/base` when he chooses. About two minutes. The harness PRs wait for it. `git merge-tree --write-tree origin/engine/base origin/rebuild/base` was clean on 2026-10-18.
  - [ ] Answer calls D, E, F and G whenever he chooses. The run never waits idle on them (Override 7).
  - [ ] Type `/login` once in the ship home only if a lane reports that the plan login in `D:/QMX-worktrees/qma-ship/home/claude` expired. Two minutes, at most once.
  - [ ] Optional. Sign in to his GPT account once in the ship home, so probe P1k's GPT half and the GPT lane checks run. Five minutes. Without it those rows record `not run, no GPT sign-in`.
  - [ ] Optional. Add direct provider keys to the keyring as `qmx/<provider>` if he wants direct Kimi, GLM, DeepSeek, Qwen or MiniMax rows proven. Without them the OpenRouter rows for those models stand in (provider-proof lanes only).
  - [ ] Keep the PC awake and plugged in. Do not start `qma.serve` on the ship home while the run is live. The coordinator also requests keep-awake through `mcp__ccd_host__request_keep_awake`.
- [ ] Read these at program start and at every tick. Log each read in `decisions.tsv`.
  - [ ] `git show origin/main:CLAUDE.md` for the project rules on trunk, then Read `C:/Users/Mubarak/Desktop/QMX/CLAUDE.md`, whose QMA v2 section is newer.
  - [ ] This plan, from `plan/agent-system` as above.
  - [ ] `architecture/workflow-engine/ARCHITECTURE-SPINE.md` and the `SOLUTION-DESIGN.md` sections each PR names, from the same branch. That folder is the contract.
  - [ ] `research/methodology/26-operator-rulings-and-alignment.md`, all sections. Its latest ruling wins over every other file.
  - [ ] `C:/Users/Mubarak/.claude/skills/poteto-mode/playbooks/autopilot-stack.md`, `shipping.md` and `opening-a-pr.md`, then `C:/Users/Mubarak/.claude/skills/no-comments/SKILL.md` and `show-me-your-work/SKILL.md`.
- [ ] Confirm the shell before any command. The PC runs Windows 11 with PowerShell 7 and Git Bash. Log which one each brief uses.
- [ ] Create the store with `decisions.tsv`, `ledger.tsv`, `lows.md`, `BACKLOG.md`, `evidence/`, `review/` and `homes/`. Write these standing orders into `decisions.tsv` as its first rows.
  - [ ] Builders and checkers are `poteto-agent` on `opus`. Never `bulk-worker`. No Fable. Every brief says "do not spawn sub-agents" and names its model.
  - [ ] At most two agents at once in all, plus the coordinator.
  - [ ] No PR edits `qmx-agents/packages/qma-harness/**` unless its preamble names the grant or ruling. A harness PR needs his merge click first.
  - [ ] No step reads, prints or copies a plan token, a provider key or a ChatGPT token. Secrets are named by keyring reference only. No step spends on any Anthropic or OpenAI API. Plan turns go through the CLI login in the ship home.
  - [ ] Money stays read-only. No PR touches a broker credential, `qmn/`, or a money act. HRMH edits where the money gate stores its rules and never the gate's logic.
  - [ ] Tests run on `claude/haiku` through the plan login. OpenRouter runs only in a lane that exists to prove another provider works. There is no spend cap.
  - [ ] No QMX usage cap is added anywhere. A probe bound, such as P2's 20 turns, is a probe bound and says so.
  - [ ] No unplanned work. A gap, bug or idea outside a PR's section goes to the store's `BACKLOG.md` as one line, and the reply mentions it.
  - [ ] Every test gate and lane runs with every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA` unset, and with `TMP`, `TEMP` and `UV_CACHE_DIR` on `D:`.
- [ ] Write the standing briefs `BRIEF-BUILDER.md` and `BRIEF-CHECKER.md` in the store. Copy `D:/QMX-worktrees/qma-ship/engine/BRIEF-BUILDER.md` and `BRIEF-CHECKER.md`. Change the plan name, the file boundary, the branch names, the store path, the harness rule and the base. Keep their "Tests" and "Unplanned work" sections. Drop their "Program facts so far", which belong to the last program. The checker brief opens its report with "Opus reviewed Opus. A cross-family review was not run."
- [ ] On the operator's go, arm the audit tick as `/loop 1h` with the tick prompt below. Never leave the cadence to memory.
- [ ] Use this tick prompt, verbatim. "Re-read the execution playbook from trunk. Audit the operation against it and fix drift in this tick. Probe every active lane and judge progress by side effects only. Stand down a stuck lane and dispatch its replacement now. Then post a short status message to the operator in chat only when the audit found a tracked change that no earlier status message reported, such as a PR opened, a code-ready head, a round launched or closed, a verdict, a merge, a stuck agent and the action taken, a blocker added or cleared, or a decision only the operator can make. Name every such change and nothing else. Do not repeat a table, the merged list, or an unchanged blocker. If the audit found none, end the turn with no reply text. Either way, log this tick's row in your decision trail. The row names the items reported, or none."
- [ ] On the operator's hold or stand-down, send every owner a zero-writes order at once.

### Spawn owners

The order below is the build order. "After" names the PRs whose code a PR needs. Gates are his merge click (GATE-M), a parked call (BLOCKED-ON D, E, F or G), or a probe result.

| # | Id | Packet | Gate | After | Proving check |
|---|---|---|---|---|---|
| 1 | HYG0 | Pre-land hygiene | none | none | E38, role tests, qma-core suite |
| 2 | PRB | Router probes P0, P1, P1k | none | none | P0, P1, P1k rows in `FINDINGS.md` |
| 3 | CAPE | Engine caps removal with the stuck detector | none | HYG0 | E41, E43 engine half |
| 4 | CAPH | Harness caps removal (H28) | GATE-M | HYG0 | E43 harness half |
| 5 | SEC1A | Redaction, credential refs, publish guard | none | CAPE | E37 |
| 6 | SEC2A | Attempt overlays, script lifetime, run context | none | SEC1A | E14, E50 |
| 7 | SEC1B | Text-surface money scan | BLOCKED-ON F | SEC2A | E36 over all 31 templates |
| 8 | SEC2B | Script isolation tiers | BLOCKED-ON E | SEC1B or SEC2A | E33 first, then E34, E17 |
| 9 | HG3 | Narrowed harness round | BLOCKED-ON D, GATE-M | CAPH | E35 |
| 10 | BUG1 | Run state and resume | none | SEC2A | E40, B-69 resume lane |
| 11 | BUG2 | Spec-gap code and validation | none | BUG1 | validation and event-key lanes |
| 12 | BUG3 | Gate answers, ledger-derived state, partition ladder | none | BUG2 | gate fold and runs-list lanes |
| 13 | L1 | Engine inside `qma.serve` | GATE-M | BUG3 | x13 doors on `qma.serve` |
| 14 | RTR1 | Model registry and data profiles (H29) | GATE-M | CAPH | one-token Test per row |
| 15 | RTR2 | Router lanes, normaliser, hardening | GATE-M | RTR1 | P3 key-lane half, E43 router half |
| 16 | RTR3 | Chat lane translator (H12) | GATE-M | RTR2 | P3 chat-lane half |
| 17 | RTR4 | Pool and error classifier | GATE-M | RTR3 | P7, E8 on fake accounts |
| 18 | RTR5 | Engine reads the registry | GATE-M | RTR4 | chunk and role lanes |
| 19 | RTR6 | Registry-generated sub-agents (H38) | BLOCKED-ON G | RTR5, PRB | P1k on the real router |
| 20 | RTR7 | Plan lane, dark then on | BLOCKED-ON G, needs P0 and P1 pass | RTR6 | P4, P2, E49 router half |
| 21 | DLG | `delegate` v2, chat targets (H26) | BLOCKED-ON G | RTR4 | P5 |
| 22 | HRME | Trigger kinds and failure contracts | GATE-M | RTR4, L1 | trigger lanes |
| 23 | HRMH | Permission floor and rules (H31) | BLOCKED-ON G | RTR4 | money and approval lanes |
| 24 | TPL1 | Plain names, intake, evidence rule | GATE-M | RTR5, BUG2 | E48, E51 |
| 25 | TPL2 | Copilot workflow builder | GATE-M | TPL1, L1 | E42 |

Changes to the operator's order, each with its reason.

- PRB moves to second place. Probes come first by program rule. PRB is scripts only, so it shares no file with any packet. Its P1 result tells the operator what call G's H38 is worth before he answers it.
- SEC1A and SEC2A are split from SEC1B and SEC2B. Calls F and E govern only the money-text scan and the script tiers. Redaction, credential refs, overlays and script lifetime need no call, so they ship now.
- BUG3 is added to the bugs. It holds the run-state rows of `40-retriage.md` packets GATE, LDR and CHUNK, and CAPE's "resume a pause at his own limit" lands there.
- HRME and HRMH split the Hermes refactors by call. The trigger work needs none. The permission floor is H31 under G.
- The rest of 40's packets are the named backlog in Appendix G, each with its reason.

- [ ] Spawn one builder per PR with the Agent tool, `subagent_type: "poteto-agent"`, `model: "opus"` and `run_in_background: true`. The brief names the PR id, its plan section, the parent branch and head, and points at `BRIEF-BUILDER.md`. Briefs point at files and never paste them. Every brief says "do not spawn sub-agents".
- [ ] Spawn one checker per PR at its code-ready head, the same way, pointing at `BRIEF-CHECKER.md`.
- [ ] Follow the "After" column. Stacked work branches from the parent PR's branch at its verified head.
  - [ ] Pipelining is allowed. While PR N is in check, the builder of PR N+1 may start on N's code-ready head only when the two Files blocks share no file (Appendix F). Otherwise N+1 starts after N's verdict.
  - [ ] CAPE and CAPH may build at the same time, as two builders with no checker running, because their files are disjoint. The root rebases the second onto the first.
  - [ ] A BLOCKED-ON packet is skipped (Override 7). A packet whose "After" names a skipped packet takes the last verified PR before it as its parent, unless its preamble says it needs the skipped one.
  - [ ] Before the first GATE-M packet, apply Override 6 once, and log it.
- [ ] Hold the file boundaries.
  - [ ] Each PR touches only the files its Files block names, plus the store's evidence and review folders.
  - [ ] No PR touches `qmb/`, `qmn/`, `qml/`, `packages/` (QMF), `apps/qmx-ui/`, `~/.claude`, or the ship home's `settings.toml`.
  - [ ] Only the PRs whose preamble names a grant or ruling edit `qmx-agents/packages/qma-harness/**`.
- [ ] Hold the review gates. CAPH, RTR7, TPL1 and TPL2 change what the operator sees or his copilot's path. They wait for his review in chat with screenshots and a video.

### PR mechanics, for every PR

- [ ] Resolve the forge once. Run `command -v origin`. If it is missing, use `gh` and record that in `decisions.tsv`. Never require `gt`.
- [ ] Branch `hard/<id>` (lowercase) from the parent branch at its verified head, in the worktree `D:/QMX-worktrees/hard-<id>`. Never use `git stash`, which is shared across worktrees. Open the PR ready, never draft, per **Opening a PR**, with `gh pr create --base <parent-branch> --head hard/<id> --repo MubarakHimself/QMX`.
- [ ] For a PR whose preamble names no harness grant, run `git diff --quiet <parent head> HEAD -- qmx-agents/packages/qma-harness`. It must exit 0.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Put `TMP`, `TEMP` and `UV_CACHE_DIR` on `D:`.
- [ ] Run `uv run --no-sync python -m poethepoet fmt-check`, `lint` and `types` once in each package the PR touches, and `uv run --no-sync python tools/secret_scan.py`, before the PR-facing push. Push with hooks on.
- [ ] Reread the full diff before each commit in place of `/deslop` (Override 1). Run `/no-comments` before review.
- [ ] Add only the tests that prove the PR's point, at the module's public interface, with literal expected values. Typically a handful, rarely more than about 20. No test per private function, no snapshot or getter tests, no mirror-the-implementation tests.
- [ ] No full `just ci` per PR. Run it once before BUG3's check and once before the last PR's check, under the CI lock `mkdir D:/QMX-worktrees/.ci-lock`.
- [ ] End each commit message with the attribution lines from the session's system reminder. End each PR body with the line the reminder names.

### Verdict and merge, for every PR (append to the stack, never merge)

- [ ] At the code-ready head SHA, one checker runs one round per `BRIEF-CHECKER.md` (Override 2). It reads the diff and the PR body, runs the PR's unit tests with `-n 2`, the gates above, lanes 1 to 4, and at most one menu lane (Override 3). It writes `review/<id>-check-<head8>.md` whose first line is CLEAN or NOT CLEAN.
- [ ] Blockers, money, login and key findings go back to the same builder, resumed for one fix round (Override 8). Low findings go to `lows.md` with the PR id and never block.
- [ ] After the fix round, the coordinator reads the fix diff itself, reruns the failing lane, and records the verdict in `ledger.tsv` with head SHA, parent SHA and `git patch-id --stable`. No second checker runs.
- [ ] Append the PR to the stack on a clean verdict, per autopilot-stack steps 5 and 6. No owner merges, arms auto-merge or closes. The operator lands the stack bottom-up into `rebuild/base` with his own clicks. `main` moves only by his squash-merge click.

### Boot recipe, for every live lane

- [ ] `git -C D:/QMX-worktrees/agent-system fetch origin hard/<id>`, then `git -C D:/QMX-worktrees/agent-system worktree add --detach D:/Temp/<id>-check <head>`.
- [ ] Unset every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`. Put `TMP`, `TEMP` and `UV_CACHE_DIR` on `D:`. Run `uv sync --frozen` at the root and `uv sync --frozen --all-packages --all-groups` in `qmx-agents/`.
- [ ] A lane that needs no model runs on a throwaway home under the store's `homes/<id>-<lane>`. A lane that needs a model opens the harness on the ship home `D:/QMX-worktrees/qma-ship/home` only while it holds the lane lock `mkdir D:/QMX-worktrees/.engine-lane-lock`, because `Harness.open` kills the CLI trees it finds for its home.
- [ ] Model turns run on `claude/haiku` through the ship home's plan login. A provider-proof lane adds the OpenRouter row from `SL/qma/switch_lane.py` (`OPENROUTER_ROW`) to a throwaway home, credential ref `qmx/openrouter`, and never reads the value. A lane that only needs a model to answer uses the fake model `SL/qma/fake_model.py`.
- [ ] No lane edits the ship home's `settings.toml`, not even with a restore. A lane that needs other settings uses a throwaway home. Hash the ship home's `settings.toml` before and after each lane that opens it.
- [ ] Save a text capture as `<slug>.log`, which is the CLI's screenshot, and a screen as `<slug>.png` with `ffmpeg -f gdigrab -i title=<window title> -frames:v 1`. Put both in the store's `evidence/<id>/`, prefixed `owner-` or `check-`, and never overwrite another PR's files.
- [ ] Remove the lane lock, then confirm with `Get-Process` that no `claude` or `qma-cli-launcher` process from the lane is left. Remove `D:/Temp/<id>-check` with `git worktree remove`.

## Remove the red CI test, Fable and the live CLI mode (HYG0)

Rows B-75, B-95, B-98, B-44, and the role rows of engine `DOC-CHANGES.md` row 35. ADs AD-11 and AD-13. Gate none. Proving check E38 plus the role tests. Done when `just ci` passes the qma-core member test, no default role list names Fable, test mode resolves `claude/haiku` first, a live strong role tries a Chinese key row first, and `python -m qmx_engine run --mode live` is a usage error. The packet is called HYG0, not P0, so it never reads as probe P0.

**Depends on.** None. It branches from the stack base.

**Files.**

- [ ] Edit `QC/tests/test_extensibility.py` (the member set at line 136).
- [ ] Edit `E/settings.py` (lines 20 to 22 and 70 to 72), `E/roles.py` (lines 85 and 86, and the module docstring), and `E/__main__.py` (the `run --mode` option at line 56).
- [ ] Edit `ET/test_settings.py`, `ET/test_roles.py` and `ET/test_admission.py`.
- [ ] Edit `SL/engine/e09_roles.py` and `SL/engine/llm_lanes.py` only where they assume OpenRouter first in test mode.

**Build.**

- [ ] Add `packages/qmx-engine` to the expected member set in `test_qma_ui_contract_placeholder_is_not_shipped`. Nothing else in qma-core changes.
- [ ] Rewrite `_CHEAP`, `_MID` and `_STRONG` in the order `key, gpt, plan` with the Chinese rows first in every tier, the strong tier included, using the example ids of SOLUTION-DESIGN section 9 as `roles.py` parses them. No list names `claude/fable`. These lists are Claude's default and stay UI-editable. A provider with no harness profile is skipped at resolution, as today.
- [ ] Set `roles.live_order` to `("key", "gpt", "plan")` (Claude's default). Make test mode resolve each role's cheap end through the plan login first, so `claude/haiku` is the first test candidate. `test_only` rows stay admitted only in a lane that names them as provider proof. Make the sort at `roles.py:85-86` match.
- [ ] Remove `live` from `run --mode` in `__main__.py`, so the CLI runs test mode only (AD-11). Live runs start only through the service.

**You see.**

- [ ] `python -m qmx_engine run <folder> --mode live` exits 2 with a usage error, and the qma-core suite passes.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_settings.py` asserts no default list contains `claude/fable`, that every tier's first row is a Chinese key row, and `roles.live_order`. `test_roles.py` asserts that test mode resolves `claude/haiku` first and a live strong role tries a Chinese key row first when its profile exists. Run `uv run --no-sync python -m pytest tests -q -n 2` in `qmx-engine` and `qma-core`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` and `qma-core` suites with `-n 2` at the parent and at head, and the harness diff check. Save `hyg0-regression.log`. Pass when head fails nothing the parent passes and the harness diff is empty.
- [ ] Lane 2. E38 first line. Run `python -m qmx_engine run <fixture> --mode live` and `--mode test --fake`. Save `hyg0-e38.log`. Pass when the first exits 2 with a usage error and the second runs and reads `mode: test`.
- [ ] Lane 3. Run `SL/engine/e09_roles.py` in test mode on the ship home under the lane lock. Save `hyg0-roles-test.log`. Pass when the first resolved candidate of every role is `claude/haiku` on the plan profile and one haiku turn answers.
- [ ] Lane 4. Run the qma-core suite alone. Save `hyg0-qma-core.log`. Pass when `test_qma_ui_contract_placeholder_is_not_shipped` passes and no other test changed state.
- [ ] Lane 5. Print the live candidate order of `planner` on a throwaway home with a Kimi profile row present and no key. Save `hyg0-roles-live.log`. Pass when Kimi is first and resolution skips it without a key.
- [ ] Lane 6. Grep the engine source and templates for `fable`. Save `hyg0-fable.log`. Pass when no default names it.
- [ ] Lane 7. Run `python -m qmx_engine --help` and `run --help`. Save `hyg0-cli.log`. Pass when `--mode` offers `test` only.
- [ ] Lane 8. Run the `llm_lanes.py` provider-proof lane on the OpenRouter row. Save `hyg0-provider-proof.log`. Pass when it names the row as provider proof and one call answers.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `hyg0-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `hyg0-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock from the lanes is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Role resolution time in ms for all roles.
- [ ] Probe. Lane 3's resolution step, three times.
- [ ] Baseline. The parent head, same probe.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. HYG0 changes no screen.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends HYG0 as the root of the stack.

## Settle native sub-agents under the plan login before router code (PRB)

Rows AL-6 (probe part). ADs AD-38, AD-29, AD-50. Gate none. Proving checks P0, P1 and P1k of SOLUTION-DESIGN section 26.14, exactly as written there. Done when `SP/router/FINDINGS.md` holds one PASS or FAIL row per probe with its evidence, and the coordinator has told the operator in plain words what P1 means for call G.

**Depends on.** None. It branches from the stack base and shares no file with any packet.

**Files.**

- [ ] Create `SP/router/common.py`, `test_router.py`, `router.py`, `p0_parity.py`, `p1_definitions.py`, `p1k_key_mains.py` and `FINDINGS.md`.
- [ ] Reuse `SP/engine/raw_client.py` and `SP/engine/common.py` by path. Do not edit them.

**Build.**

- [ ] In `router.py`, write a loopback test router for probes only. It forwards `claude-*` requests to `api.anthropic.com` with the body and the raw header list unchanged. It answers third-party ids from an echo upstream. It records every method and path. It never writes an `authorization`, `x-api-key` or `cookie` value. It compares those values between two runs in memory only and writes `same` or `different`.
- [ ] In `p0_parity.py`, run the same haiku turn with one `qmx` MCP tool call twice under the ship home's plan login, through a raw SDK client with `CLAUDE_CONFIG_DIR` on the ship home's plan folder. Once with no base URL, once through `router.py` in record mode. Compare every header and body field, excluding only the fields P0 names. If a difference appears, retry with `ENABLE_TOOL_SEARCH=true` and any env value that restores it, and record which one did.
- [ ] In `p1_definitions.py`, launch a haiku main under the plan login with `agents={"kimi-reviewer": AgentDefinition(model="kimi/k3", ...)}` through `router.py` with a Kimi echo upstream. Tell the main to use `kimi-reviewer`. Record whether the sub-agent spawned, the request's `model` and agent-id header, the echo's answer as the sub-agent's result, and every method and path. Keep the raw incoming sub-agent request for RTR7's P4.
- [ ] In `p1k_key_mains.py`, launch a Kimi main on the OpenRouter Kimi row and, if his GPT sign-in exists, a GPT main, each with definitions naming a DeepSeek and a Qwen sub-agent through `router.py` with echo upstreams. Record whether each sub-agent spawned with its model id unchanged.
- [ ] Write `FINDINGS.md` with one row per probe, the observed values, PASS or FAIL per the section 26.14 lines, and what each decides. P1 FAIL means RTR7 is not built and plan mains get no third-party definitions in RTR6. P1k FAIL means key and GPT mains reach third parties only through DLG.

**You see.**

- [ ] `FINDINGS.md` has a PASS or FAIL row for P0, P1 and P1k, with the env values P0 found and the method and path list P1 recorded.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_router.py` sends a fixture request with an `authorization` header through `router.py` and asserts the recorded file holds no header value and the forwarded bytes equal the input. Run `uv run --no-sync python -m pytest scripts/probes/router -q`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the harness diff check and `git diff --stat <parent> HEAD`. Save `prb-regression.log`. Pass when the harness diff is empty and only `SP/router/` changed.
- [ ] Lane 2. Run `p0_parity.py` under the lane lock. Save `prb-p0.log`. Pass when the log ends in PASS or FAIL per the section 26.14 P0 line, with every differing field named.
- [ ] Lane 3. Run `p1_definitions.py` under the lane lock. Save `prb-p1.log`. Pass when the log ends in PASS or FAIL per the P1 line and lists every method and path.
- [ ] Lane 4. Run `p1k_key_mains.py` on the OpenRouter rows. Save `prb-p1k.log`. Pass when the log ends in PASS or FAIL per the P1k line for the Kimi main, and the GPT main reads PASS, FAIL or `not run, no GPT sign-in`.
- [ ] Lane 5. Run P1's echo form twice in a row. Save `prb-canary.log`. Pass when both runs give the same verdict, so it can serve as RTR7's boot canary.
- [ ] Lane 6. Grep every log and recording for `sk-ant-`, `Bearer ` and `x-api-key` values. Save `prb-leak.log`. Pass when none is found.
- [ ] Lane 7. Hash the ship home's `settings.toml` and list `~/.claude` before and after lanes 2 to 4. Save `prb-home.log`. Pass when both are unchanged.
- [ ] Lane 8. Count the haiku plan turns from the run journals. Save `prb-turns.log`. Pass when the count is recorded for Appendix E.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `prb-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `prb-processes.log`. Pass when no `claude`, `qma-cli-launcher` or probe router process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Added latency in ms of the pass-through router per plan request.
- [ ] Probe. P0's two runs, five requests each.
- [ ] Baseline. The run with no base URL.
- [ ] Rule. No fail rule. A median above 50 ms goes into `FINDINGS.md` as a risk for RTR7.

**Review gate.** None. The coordinator reports P1's result to the operator in plain words.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends PRB on HYG0.

## Remove the engine's usage caps and ship the stuck detector in the same PR (CAPE)

Rows AL-2, AL-3 (the strategy default), B-16, B-33, B-36, B-38, B-49, B-55, L-21, L-45, L-46, L-48, L-60, L-61, L-66, and 39 R.6 L5 (the engine half). ADs AD-40 (2), AD-16, AD-9, AD-4. Gate none. Proving checks E41 and the engine half of E43. Done when `settings.DEFAULTS` holds no runaway, turn, tool-call or run-time entry, no shipped template carries a `runaway` block, `timeout.run_seconds` or agent `max_turns`, and the stuck detector stops a looping or flailing agent while a converging fixer, a pager and a slow prefill run on.

**Depends on.** HYG0 (`E/settings.py`, `E/roles.py`).

**Files.**

- [ ] Edit `E/settings.py`, `E/admission.py`, `E/roles.py` (the degrade path at lines 95 to 110), `E/watchdog.py`, `E/runner.py`, `E/core/ladder.py`, `E/core/commands.py`, `E/core/fold.py`, `E/core/ready.py`, `E/core/simulate.py` and `E/core/state.py`.
- [ ] Edit `E/definition/model.py`, `E/definition/lint.py` and `E/definition/schema/qmx.workflow.1.json`.
- [ ] Edit `E/nodes/base.py`, `E/nodes/llm.py`, `E/nodes/agent.py`, `E/ports/inbox.py` and `E/ports/settings.py`. Create `E/stuck.py` for the stuck digest and the loop rules.
- [ ] Edit every `T/*/definition.json`, the three `T/_shared` folders that carry `max_turns`, and `T/rv-weekly-review/scripts/lint_edits.py`.
- [ ] Edit `ET/test_ladder.py`, `test_agent.py`, `test_lint.py`, `test_settings.py`, `test_definition.py`, `test_watchdog.py`, `test_admission.py`, `test_templates.py`, `planted.py`, and the fixture `ET/fixtures/workflows/bad-agent-no-max-turns/`.
- [ ] Edit `SL/engine/x08_watchdog.py`, `SL/engine/x11_agent_chunks.py` and `SP/engine/p_limits.py`. Create `SL/engine/e41_stuck.py` and `SL/engine/e43_no_caps.py`.

**Build.**

- [ ] Delete `runaway.*`, `on_runaway`, `agent.max_turns`, `agent.max_tool_calls`, `timeout.agent.run`, `timeout.script.run`, `pool.accounts.*.background_share` and `budgets.max_live_chats` from `DEFAULTS`. Read `max_live_chats` from the harness `[budgets]` table through `SettingsPort` instead. Set `pool.strategy` to `least_used` (Claude's default). Keep `limits.interactive_reserve` 2.
- [ ] Delete the runaway guard and the degrade path from the ladder, the runner, the fold, the commands and `roles.py`. An old document's `runaway` folds to nothing with one `info` line.
- [ ] Delete every template's `runaway` block, node `timeout.run_seconds` and agent `max_turns` and `max_tool_calls`, and the schema defaults. Lint refuses only a value below 1 that he wrote. Every template's content hash changes, which TPL1's E48 re-tags.
- [ ] Honour a `limits` block he wrote (`tokens`, `turns`, `tool_calls`, `wall_seconds`) as a pause with one `info` line, checked at each turn end and every tick against landed spans. `wall_seconds` counts active time only. No template ships one.
- [ ] Move the warm-first gate from inside the agent attempt to dispatch, so a held chunk writes no `node_started` (AD-9, L-60).
- [ ] Build the stuck detector of AD-16 (a) to (e) in `watchdog.py` and `stuck.py`. No progress on a sleep-aware clock with the warning at 80 % through the inject path, an interrupt, `timeout.grace`, then `stalled`. A model request in flight counts as progress, read from the run journal's `model_call` rows until RTR2's router journal lands. The worker heartbeat never counts. Recorded waits are skipped. `timeout.in_tool` counts only time with no CPU and no IO on a process the engine owns. Where the engine owns no process for the tool, an open tool call counts as progress, and the PR body names that departure. Then the loop signature on the narrow stuck digest, no convergence on error results, zero-token runs, and the crash-loop counter. The values are in Appendix H.

**You see.**

- [ ] `python -m qmx_engine check` on every shipped template prints no `runaway`, and a looping-agent fixture ends `stalled(loop)` with its summary as output.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_watchdog.py` covers a loop (5 identical calls and digests), a flailing fixer (same failing set and count), a converging fixer (5, then 3, then 1 failed), a pager over new rows, a request in flight, and a recorded wait, each with its literal end state. `test_settings.py` asserts none of the deleted keys exists. `test_lint.py` asserts a template with no limits validates. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head, and the harness diff check. Save `cape-regression.log`. Pass when head fails nothing the parent passes except tests that asserted a deleted cap, each named, and the harness diff is empty.
- [ ] Lane 2. E41. Run `e41_stuck.py` on the fake provider. Save `cape-e41.log`. Pass when the loop ends `stalled(loop)`, the flailing fixer ends `stalled(no_convergence)` and walks the ladder, and the converging fixer, the pager, a 400 s first-token wait on the fake upstream and a CPU-busy script all end `passed`.
- [ ] Lane 3. E43 engine half. Run `e43_no_caps.py` with a fake row declaring a 1M window, two chunks reporting 600k tokens in all, and a run whose fake clock moves six hours. Save `cape-e43.log`. Pass when both end `passed` with no pause and no `needs_you`.
- [ ] Lane 4. Run one agent template on haiku under the lane lock. Save `cape-haiku.log`. Pass when it ends `passed` and its span shows no limit check.
- [ ] Lane 5. Write a `limits` block with `turns: 2` into a fixture and run it. Save `cape-limits.log`. Pass when it pauses with one `info` line and resumes from `runs.resume`.
- [ ] Lane 6. Run a three-chunk agent node on the fake provider with the warm-first gate. Save `cape-warm.log`. Pass when chunks 2 and 3 write no `node_started` while held and none stalls.
- [ ] Lane 7. Grep `settings.py`, the schema and every template for `runaway`, `max_turns`, `max_tool_calls` and `run_seconds`. Save `cape-grep.log`. Pass when no default or template value is found.
- [ ] Lane 8. Kill the engine three times during one run. Save `cape-crashloop.log`. Pass when the run parks with one inbox item.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `cape-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `cape-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Watchdog tick time in ms with 50 open attempts.
- [ ] Probe. A unit benchmark over 50 fixture attempts, ten ticks.
- [ ] Baseline. The parent's watchdog tick on the same fixture.
- [ ] Rule. Fail when the median tick exceeds 200 ms, because the detector runs every tick.

**Review gate.** None. CAPE changes no screen. CAPH carries the review of the no-caps behaviour he sees.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends CAPE on PRB.

## Remove the harness budgets and let sends wait for a slot (CAPH)

Rows AL-1, B-7, B-9, and 39 R.6 L5 (the harness half). ADs AD-40 (1) and (5). Grant H28, which follows his settled no-caps rule (OPEN-DECISIONS G) and has no fallback (42 N1). Gate GATE-M. Proving check the harness half of E43. Done when `[budgets]` unset reaches the SDK as no budget and no turn cap, no `needs_you` appears for usage, a Background send past capacity waits, a parent that delegates under `max_live_chats = 1` finishes, and `hard_stop` is untouched.

**Depends on.** HYG0 for CI, and his merge click (GATE-M). It may build beside CAPE (disjoint files).

**Files.**

- [ ] Edit `H/launch.py` (`Budgets`, `parse_budgets`, lines 221 to 261 and 518 to 519), `H/harness.py` (lines 362 to 433, the usage page at line 624, and `_delegate`'s docstring), `H/usage.py` (`BackgroundCap` and `cap_note`, lines 250 to 280), and `qmx-agents/packages/qma-harness/src/qma/console.py`.
- [ ] Edit `HT/test_launch.py`, `test_table.py`, `test_usage.py`, `test_console.py`, `test_change.py` and `test_delegate.py`.
- [ ] Edit `SL/qma/s10_usage.py` and `SL/qma/s31_chat_cap.py`. Create `SL/qma/caph_lanes.py`.

**Build.**

- [ ] Make `max_budget_usd`, `background_cap` and the Background and Child `max_turns` accept unset and default to unset. An unset value passes no `max_budget_usd` and no `max_turns` to the SDK. Delete `BackgroundCap`, `cap_note` and the usage `needs_you` path.
- [ ] Make a Background or Child send with no free chat slot wait for one. An Interactive chat keeps today's eviction. A child started by a parent blocked in its own send on that child borrows the parent's slot, and a parent blocked on its own child does not count against capacity (42 N5).
- [ ] Derive `max_live_chats` from RAM as `floor((ram_budget_mb - overhead_mb) / session_mb)` with `session_mb` 1,536 and `overhead_mb` 4,096 on the PC (Claude's default, AD-30). A hand-set value may only lower it. This replaces both literals (41 L5). It is the one change here beyond H28's text, and the PR body names it.
- [ ] Leave `hard_stop` and `overage_rule` untouched.
- [ ] Make the console and the usage page read "unset (no QMX limit)" for each budget row.

**You see.**

- [ ] The usage page and `qma.console` show the three budget rows as "unset (no QMX limit)" and a derived chat count.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_launch.py` asserts an unset budget sends no `max_budget_usd` and no `max_turns`. `test_table.py` runs `max_live_chats = 1` with a parent that delegates, and asserts it finishes, and a second Background send that waits and then runs. `test_usage.py` asserts `hard_stop` still stops on `using_overage`. Run `-n 2` in `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` and `qmx-control` suites with `-n 2` at the parent and at head, and `git diff --stat <parent> HEAD -- qmx-agents/packages/qma-harness`. Save `caph-regression.log`. Pass when head fails nothing the parent passes except tests that asserted a deleted cap, each named, and the diff lists only this PR's files.
- [ ] Lane 2. Start a Background chat on haiku under the lane lock with `[budgets]` unset, and read the launched SDK options. Save `caph-unset.log`. Pass when no `max_budget_usd` and no `max_turns` reach the SDK and the chat answers.
- [ ] Lane 3. On a throwaway home with the fake model and `max_live_chats = 1`, run a Background parent that delegates. Save `caph-borrow.log`. Pass when the parent finishes and no `needs_you` block is written.
- [ ] Lane 4. On the same home, fill the table, then send to a second Background chat. Save `caph-wait.log`. Pass when the send waits, then runs when a slot frees, with no `ChatTableFull`.
- [ ] Lane 5. Feed `s10_usage.feed` a reading with `using_overage`. Save `caph-hardstop.log`. Pass when `hard_stop` stops plan chats as before.
- [ ] Lane 6. Start an Interactive chat on a full table. Save `caph-interactive.log`. Pass when today's eviction runs.
- [ ] Lane 7. Read `/api/usage` and the console. Save `caph-page.log` and `caph-page.png`. Pass when every budget row reads "unset (no QMX limit)".
- [ ] Lane 8. Print the derived `max_live_chats` on this PC. Save `caph-ram.log`. Pass when it matches the formula on the machine's RAM.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `caph-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `caph-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Time from a slot freeing to the waiting send starting, in ms.
- [ ] Probe. Lane 4, five times.
- [ ] Baseline. None, today's send refuses at once. Record head only.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** He reviews the no-caps behaviour he sees.

- [ ] Show the operator in chat a screenshot of the usage page with the unset rows, and a short video of lane 4's waiting send, before the root appends CAPH.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends CAPH on the stack tip.

## Redact every stored and served secret and refuse broker credential refs (SEC1A)

Rows B-39, L-58, L-52, L-51, B-17 (the node `credentials` half). ADs AD-37, AD-11, AD-36 (credential refs only). Gate none. Call F covers the money-text scan only, which is SEC1B. Proving check E37. Done when a key-shaped value in a provider error, a script's stderr and an inbox item shows `[redacted...]` in the ledger, the inbox, `explain`, REST and the Library run summary, a node `credentials` ref outside `qmx/tool/*` is refused, and `version_state` reads published only for refs reachable on `main`.

**Depends on.** CAPE (`E/definition/lint.py`).

**Files.**

- [ ] Create `E/ledger/redact.py`. Edit `E/ledger/store.py`, `E/ledger/inbox_table.py`, `E/ledger/memo.py`, `E/service/explain.py`, `E/service/rest.py`, `E/trace_export.py`, `E/service/runs.py` (lines 208 to 212) and `E/definition/lint.py`.
- [ ] Edit `ET/test_ledger.py`, `test_inbox.py`, `test_explain.py`, `test_rest.py`, `test_lint.py` and `test_service.py`. Create `SL/engine/e37_redaction.py`.

**Build.**

- [ ] Move the redact function out of `definition/lint.py` into `ledger/redact.py` and match high-specificity key prefixes anywhere, glued to a word or not (L-58). Refuse values under 12 characters as keys (36 S7).
- [ ] Redact at every write seam of AD-37. The ledger writer, the inbox table, memo rows built from the redacted payload, the REST serializer, `explain`, and the Library run summary. Each span counts its redactions.
- [ ] Refuse a node `credentials` ref outside the `qmx/tool/<name>` namespace, casefolded, and fail closed on the broker set (36 S5). The Settings-validator half of B-17 waits for the vault packet (Appendix G).
- [ ] Make `version_state` read published only when the ref is reachable on `main` (AD-11, L-51).

**You see.**

- [ ] `python -m qmx_engine explain <run_id>` on a run whose provider error held a key prints `[redacted...]` in its place.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_ledger.py` writes an event holding `key_sk-or-v1-<fake>` and reads `[redacted...]` back. `test_lint.py` refuses `credentials: {broker: qmx/ctrader-live}` and accepts `qmx/tool/firecrawl`. `test_service.py` reads a non-`main` ref as not published. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head, and the harness diff check. Save `sec1a-regression.log`. Pass when head fails nothing the parent passes and the harness diff is empty.
- [ ] Lane 2. E37. Run `e37_redaction.py`, where the fake upstream echoes a fake key in its error and a script prints a fake resolved tool key to stderr. Save `sec1a-e37.log`. Pass when the ledger, the inbox title and cause, `explain`, REST and the run summary all show `[redacted...]` and the span counts the redactions.
- [ ] Lane 3. Validate a fixture with `credentials: {broker: qmx/ctrader-live}` and one with `QMX/Tool/x`. Save `sec1a-credrefs.log`. Pass when the first is refused naming the file and line, and the second is read casefolded.
- [ ] Lane 4. Publish a draft from a branch not reachable on `main`, then read its version state. Save `sec1a-published.log`. Pass when it reads not published.
- [ ] Lane 5. Grep `engine.sqlite` (`mode=ro`) and `inbox.sqlite` after lane 2 for the fake key. Save `sec1a-grep.log`. Pass when no match.
- [ ] Lane 6. Feed a value of 11 characters shaped like a key. Save `sec1a-short.log`. Pass when it is refused as a key value.
- [ ] Lane 7. Call `GET /api/workflow-runs/{id}/explain` on the engine host. Save `sec1a-rest.log`. Pass when the served text holds `[redacted...]`.
- [ ] Lane 8. Read the memo row of the failed node. Save `sec1a-memo.log`. Pass when it holds no fake key.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `sec1a-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `sec1a-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Ledger append time in microseconds with redaction on.
- [ ] Probe. 10,000 appends of a 2 KiB event.
- [ ] Baseline. The parent's append time on the same probe.
- [ ] Rule. Fail when the median grows by more than 30 %, because every event passes the seam.

**Review gate.** None. SEC1A changes no screen.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends SEC1A on the stack tip.

## Give each attempt its own overlay and tie scripts to the engine's life (SEC2A)

Rows B-31, B-26, B-78, B-80 (the env half), L-39, L-40, L-43, B-29, and the cwd rows of engine `DOC-CHANGES.md` row 41. ADs AD-51, AD-24 (lifetime, run context and zone containment only), AD-16 (script idle), AD-34 (spill), AD-8. Gate none. Call E covers where edited scripts run, which is SEC2B. Proving checks E14 and E50. Done when a retry no longer undoes a sibling's files, only declared outputs commit, a killed engine kills its scripts, a script's env holds the run context and nothing else, and big stdout spills to an artifact.

**Depends on.** SEC1A (stack order only).

**Files.**

- [ ] Edit `E/nodes/script.py`, `E/workers/local.py` and `E/workers/effects.py`. Create `E/workers/confine.py` with the Job object only.
- [ ] Edit `E/definition/validate.py`, `E/definition/model.py` and `E/definition/schema/qmx.workflow.1.json` for declared outputs.
- [ ] Edit `T/db-desk-brief/scripts/gather.py`, `T/rv-weekly-review/scripts/week.py`, and the `definition.json` of each template whose script node writes a file a later node reads.
- [ ] Edit `ET/test_effects.py`, `test_script.py` and `test_definition.py`. Edit `SL/engine/e14_script_env.py`. Create `SL/engine/e50_overlays.py`.

**Build.**

- [ ] Give each attempt its own overlay under `<zones_root>/<run_id>/attempts/<n>.<i>.<p>.<a>/` as its cwd and only writable place, with `work/` read-only to it (AD-51). On success, stage and rename only the node's declared `outputs.files` under the ledger writer and write `zone_committed`. Undeclared files die with the attempt. A staged commit rolls forward on resume. Delete the `.snap` snapshot path.
- [ ] Refuse at validation two possibly-concurrent writers of one declared path unless the path is partition-templated or declares a merge. A `zone_conflict` at commit is non-retryable and goes to the doctor.
- [ ] Put every script process in a Job object that dies with the engine (B-31). Refuse a junction or link inside a zone (`zone_link`, L-40). Restore only inside the attempt's overlay (L-39). Delete overlays on failure and keep a parked run's zone until its inbox item closes (AD-49, L-43).
- [ ] Give scripts the run context `QMX_RUN_ID`, `QMX_MODE`, `QMX_FAKE`, `QMX_NOW`, `QMX_WORK`, `QMX_WORK_SHARED` and `QMX_CODE`, and never the home (B-78, B-80). Enforce the script `idle` timeout and spill stdout above `inline_limit_bytes` to an artifact (B-26).
- [ ] Make `gather.py` and `week.py` read the context instead of deriving the home from the cwd.

**You see.**

- [ ] A run of the RV template on the fake provider ends `passed`, and its zone holds only declared outputs.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_effects.py` covers two attempts writing different files where one fails and retries, two chunks writing the same scratch names, and a crash between the renames and `zone_committed`. `test_definition.py` refuses two concurrent writers of one undeclared-merge path. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head, the template suite, and the harness diff check. Save `sec2a-regression.log`. Pass when head fails nothing the parent passes and the harness diff is empty.
- [ ] Lane 2. E50. Run `e50_overlays.py`. Save `sec2a-e50.log`. Pass when the sibling's committed files survive a retry, the scratch names do not collide, only declared outputs commit, and the crash case rolls forward on resume.
- [ ] Lane 3. E14. Run `e14_script_env.py`. Save `sec2a-e14.log`. Pass when the script's env holds the run-context names and no provider key, `CLAUDE_CONFIG_DIR`, plan path or home path.
- [ ] Lane 4. Start a script that sleeps, then `taskkill /F` the engine. Save `sec2a-lifetime.log`. Pass when the script process is gone within 5 s.
- [ ] Lane 5. Plant a junction in a zone. Save `sec2a-junction.log`. Pass when the attempt fails `zone_link` and the engine keeps running.
- [ ] Lane 6. Run a script that prints 1 MiB. Save `sec2a-spill.log`. Pass when the output is an artifact and the ledger row holds a pointer.
- [ ] Lane 7. Run the DB and RV templates on the fake provider. Save `sec2a-templates.log`. Pass when both end `passed` and neither reads the cwd for the home.
- [ ] Lane 8. Park a run, then retry it from its inbox item. Save `sec2a-parked.log`. Pass when its zone was kept and the retry reads it.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `sec2a-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `sec2a-processes.log`. Pass when no script, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Commit time in ms for 100 declared output files.
- [ ] Probe. A fixture node writing 100 small files, five runs.
- [ ] Baseline. None, overlays are new. Record head only.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. SEC2A changes no screen.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends SEC2A on the stack tip.

## Scan every text surface for money acts and forbidden imports, failing closed (SEC1B)

BLOCKED-ON F. Rows B-89, B-13, L-24, AL-15 (t7, dm, ma), with B-93 and L-25 folded. ADs AD-36, AD-3. Proving check E36, then the scan over all 31 templates. Done when every planted case of E36 is refused with its file and line, every listed innocent passes, and all 31 shipped templates pass the scan. The harness money gate is not touched.

**Depends on.** SEC2A (`E/nodes/script.py`), and call F granted.

**Files.**

- [ ] Create `E/definition/scan.py` and `ET/test_scan.py`. Edit `E/definition/lint.py` and `E/nodes/script.py` (scan at dispatch).
- [ ] Edit `QC/src/qma/core/barriers/descriptors.py` to add `name_money_act_called` next to `name_money_act`, with a test in the qma-core suite.
- [ ] Edit the prompts and notes of `T/t7-trade-journal-review`, `T/dm-demo-monitor` and `T/ma-mini-app-lifecycle` where the narrowed scan refuses them.
- [ ] Create `SL/engine/e36_scan.py`.

**Build.**

- [ ] Write the predicate `name_money_act_called` on the input words, per AD-36, in qma-core.
- [ ] Scan scripts, prompts, node notes, parameter values and proposal actions. Match prose only in those surfaces. Give comments, docstrings and READMEs the secret check only. Refuse non-literal `getattr` and `setattr`, and imports of `keyring`, `qmn` and broker modules, including through `importlib`. Check host literals against the gate's broker list. Fail closed with no allow-list.
- [ ] Reword the three templates' refused phrases. A false positive is fixed by rewording, never by an allow-list.

**You see.**

- [ ] `python -m qmx_engine check` on a planted copy prints each refusal with its file and line.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_scan.py` holds E36's planted set and its innocents as literal cases. The qma-core test covers `send_order`, `post_order` and a key named `mode`. Run `-n 2` in `qmx-engine` and `qma-core`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` and `qma-core` suites with `-n 2` at the parent and at head, and the harness diff check. Save `sec1b-regression.log`. Pass when head fails nothing the parent passes and the harness diff is empty.
- [ ] Lane 2. E36. Run `e36_scan.py` on a planted copy of a template. Save `sec1b-e36.log`. Pass when each planted case is refused with its file and line and each innocent passes.
- [ ] Lane 3. Scan all 31 shipped templates. Save `sec1b-templates.log`. Pass when all 31 pass.
- [ ] Lane 4. Dispatch a script whose text changed after validation to name a money act. Save `sec1b-dispatch.log`. Pass when dispatch refuses it.
- [ ] Lane 5. Run the harness `money` lane `SL/qma/s06_money.py`. Save `sec1b-gate.log`. Pass when the gate behaves as at the parent.
- [ ] Lane 6. Plant `importlib.import_module("keyring")` and a `getattr` with a computed name. Save `sec1b-imports.log`. Pass when both are refused.
- [ ] Lane 7. Plant "write the order of the sections" in a README and in a prompt. Save `sec1b-prose.log`. Pass when the README passes and the prompt is refused, as AD-36 states.
- [ ] Lane 8. Run the T7, DM and MA templates' validation. Save `sec1b-three.log`. Pass when all three validate.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `sec1b-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `sec1b-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Scan time in ms for all 31 templates.
- [ ] Probe. Lane 3, three runs.
- [ ] Baseline. The parent's `check` time on the same templates.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. SEC1B changes no screen.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends SEC1B on the stack tip of the moment F is granted (Override 7).

## Run shipped scripts in an AppContainer and every other script in a container (SEC2B)

BLOCKED-ON E. Rows B-30, AL-15 (the manifest `tier` and `network`, and `capture.py` to the container), B-89 (the runtime half). ADs AD-24, AD-25, AD-36 (runtime import refusal). Proving check E33 first, then E34 and E17. Done when E33 passes or its fallback is recorded, an unedited shipped script runs `host_confined`, a one-byte edit moves it to the container, QMX starts Docker Desktop when it is off, and an attempt that has neither waits `placement`. Spill to Contabo is not possible yet, because no Contabo node exists (Appendix G), and the PR body says so.

**Depends on.** SEC1B when F was granted, else SEC2A. Call E granted.

**Files.**

- [ ] Create `SP/engine/p_appcontainer.py` (E33).
- [ ] Edit `E/workers/confine.py` (add the AppContainer), `E/workers/local.py` and `E/nodes/script.py`. Create `E/workers/container.py` and the script runtime folder `E/script_runtime/` with its boot audit hook.
- [ ] Create `docker/qmx-worker/Dockerfile` with `yt-dlp` in the image.
- [ ] Edit `T/catalog.py` and create `T/manifest.json` (hash, `tier` and `network` per shipped script). Declare `network: true` for DB, T4, RS1, RS4 and T3. Edit `T/a-fill-the-library/scripts/capture.py` to run in the container.
- [ ] Edit `ET/test_script.py`. Create `ET/test_confine.py`, `SL/engine/e34_provenance.py` and `SL/engine/e17_tiers.py`.

**Build.**

- [ ] Run E33 first. If any E33 line fails, use the container tier for shipped scripts too, as SOLUTION-DESIGN section 5.5 names, and write the departure in the PR body.
- [ ] Run each byte-identical shipped script in a per-attempt AppContainer profile with grants on the runtime, `code/` and the attempt overlay only, inside SEC2A's Job object.
- [ ] Run every other script in the `qmx-worker` container with `--read-only`, `--cap-drop ALL`, a non-root user, and only the code and overlay mounts.
- [ ] When Docker is off, start Docker Desktop and wait for its health. If it does not come up, the attempt waits `placement` with one doctor line.
- [ ] Refuse forbidden imports at runtime through the boot audit hook.

**You see.**

- [ ] E34's log shows the same node `host_confined` unedited and in the container after a one-byte edit.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_confine.py` asserts the tier chosen for an unedited, an edited and a model-written script, and the `placement` wait when no tier is available. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head, the template suite, and the harness diff check. Save `sec2b-regression.log`. Pass when head fails nothing the parent passes and the harness diff is empty.
- [ ] Lane 2. E33. Run `p_appcontainer.py`. Save `sec2b-e33.log`. Pass when every E33 line holds, or the log records the failing line and the fallback the PR took.
- [ ] Lane 3. E34. Run `e34_provenance.py`. Save `sec2b-e34.log`. Pass when the unedited script runs `host_confined` and the edited copy runs in the container.
- [ ] Lane 4. Stop Docker Desktop, then run an edited script. Save `sec2b-docker.log`. Pass when QMX starts Docker and the attempt runs, or it waits `placement` with the doctor line.
- [ ] Lane 5. E17. Run `e17_tiers.py`. Save `sec2b-e17.log`. Pass when an `agent-tool` call refuses `host_confined` and `runc`.
- [ ] Lane 6. Inside the AppContainer, try `<home>/claude/.credentials.json`, `CredReadW` on a throwaway `qmx/probe-*` entry, and `127.0.0.1` on the control port. Save `sec2b-reach.log`. Pass when all three are denied.
- [ ] Lane 7. Run template A's `capture.py` on a fixture video. Save `sec2b-capture.log`. Pass when it runs in the container with `yt-dlp`.
- [ ] Lane 8. Run the five network templates on the fake provider. Save `sec2b-network.log`. Pass when each runs with its declared network.
- [ ] Lane 9. Run `tools/secret_scan.py` and inspect the container env. Save `sec2b-secrets.log`. Pass when both are clean.
- [ ] Lane 10. List processes and containers after the lanes. Save `sec2b-processes.log`. Pass when no script, container, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Script start time in ms per tier.
- [ ] Probe. A hello script, five starts per tier.
- [ ] Baseline. A bare host start at the parent.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. SEC2B changes no screen.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends SEC2B on the stack tip of the moment E is granted (Override 7).

## Grant the narrowed harness round with H2 first (HG3)

BLOCKED-ON D, and GATE-M. Rows B-51, B-6, B-8, B-10, B-50, B-65, B-67, L-8, L-9, L-16, L-17, L-10 (the live proof), with B-70 and L-7 folded. ADs AD-24, AD-34, AD-25, AD-11. Grant D covers H2, H18 (close only), H19, H22, H24 (labelling only) and the five harness bug fixes, per HARNESS-REQUESTS round HG3. Proving check E35. Done when an engine agent chat has no `Bash`, `PowerShell`, `Monitor`, `Write`, `Edit`, `NotebookEdit` or `WebFetch`, an `llm` chat has no tools, a reloaded chat keeps its compaction point and hooks, a finished chat closes, and `py.typed` ships.

**Depends on.** CAPH (`H/launch.py`, `H/harness.py`), his merge click, and call D granted.

**Files.**

- [ ] Edit `H/launch.py`, `H/harness.py` and `H/home.py`. Create `H/py.typed`.
- [ ] Edit `QX/server.py` (H24 `caller_kind`) and the runs route in `QX/service.py` (B-67).
- [ ] Edit `E/nodes/llm.py`, `E/nodes/agent.py` and `E/ports/harness_adapter.py` for the engine side of H2.
- [ ] Edit `HT/test_launch.py`, `test_chat_options.py`, `test_home.py` and `test_table.py`, the `qmx-control` tests, and `ET/test_agent.py`, `test_llm.py` and `test_harness_port.py`.
- [ ] Create `SL/qma/hg3_lanes.py` and `SL/engine/e35_tools.py`.

**Build.**

- [ ] H2. Add `NewChat.tools: list[str] | None` for Background and Child chats, passed to the SDK `tools` option. `[]` means no built-in tools. The engine passes `[]` for `llm` nodes and an allow-list with no command, write or fetch tool for `agent` nodes.
- [ ] H18. Add `Harness.end_chat(sid)` for Background and Child chats. It closes the CLI and deletes nothing. The chat list filters by kind.
- [ ] H19. Keep `compact_at` on the chat record and add `Harness.attach_hooks(sid, hooks)`. The engine re-attaches hooks before the next send to a reloaded chat.
- [ ] H22. Ship `py.typed`. H24. Record `caller_kind` for a REST call and a `qmx` tool dispatch, as a label only.
- [ ] Fix L-16 (a cooldown on `meter()`), L-17 (cleanup before `chat.close()`), L-8 (prune `_options` on end), L-9 (`_observer` also catches `CancelledError`), and B-67 (`GET /api/runs` stops listing chat journals).

**You see.**

- [ ] E35's log shows an engine agent chat with none of the seven tools, under his remembered allow rows in the ship home.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_chat_options.py` asserts `tools=[]` reaches the SDK for a Background chat and is refused for an Interactive one. `test_home.py` asserts `compact_at` survives a reload. `test_agent.py` asserts the engine passes the allow-list. Run `-n 2` in `qma-harness`, `qmx-control` and `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness`, `qmx-control` and `qmx-engine` suites with `-n 2` at the parent and at head, and `git diff --stat <parent> HEAD -- qmx-agents/packages/qma-harness`. Save `hg3-regression.log`. Pass when head fails nothing the parent passes and the diff lists only this PR's files.
- [ ] Lane 2. E35. Run `e35_tools.py` on haiku under the lane lock, asking for each of the seven tools, then resume the chat and ask again. Save `hg3-e35.log`. Pass when no such call executes in either chat.
- [ ] Lane 3. H19. Start a Background chat with `compact_at` 0.40 and hooks, restart the host, send again. Save `hg3-reload.log`. Pass when the reloaded CLI holds the compaction env and PostToolUse fires.
- [ ] Lane 4. H18. Run an `llm` node, then list chats and processes. Save `hg3-close.log`. Pass when its CLI is gone and the Interactive chat list does not show it.
- [ ] Lane 5. L-10. Drive one Background chat on haiku past 40 % of its window with fixture text. Save `hg3-compact.log`. Pass when a `compacted` block lands near 40 %.
- [ ] Lane 6. Call `meter()` twice in a row. Save `hg3-meter.log`. Pass when the second call spends no turn.
- [ ] Lane 7. Call `GET /api/runs` after an engine run. Save `hg3-runs.log`. Pass when no chat journal is listed.
- [ ] Lane 8. Run `pyright` on a consumer that imports `qma.harness` with no `extraPaths`. Save `hg3-typed.log`. Pass when it reports no missing stubs.
- [ ] Lane 9. Run `tools/secret_scan.py` and `SL/qma/s06_money.py`. Save `hg3-scans.log`. Pass when both are clean and the money gate is unchanged.
- [ ] Lane 10. List processes after the lanes. Save `hg3-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). RAM held by idle engine CLIs after ten `llm` runs, in MB.
- [ ] Probe. Ten `llm` runs on haiku, then `Get-Process`.
- [ ] Baseline. The same at the parent.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. HG3 changes no screen he uses. Call D is his review of its scope.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends HG3 on the stack tip of the moment D is granted (Override 7).

## Fix run state, waits and resume (BUG1)

Rows B-69, B-63, L-37, B-73, B-72, B-25, L-32, L-38, B-57, B-66, L-69, B-42, B-60, B-37, B-54, L-80, L-28, L-31, L-33, L-47, L-57, L-64, L-65, L-70. ADs AD-3 (one instance per home), AD-5, AD-7, AD-8, AD-10, AD-15, AD-17, AD-34. Gate none. Proving checks E40 and the B-69 resume lane. Done when a time wait resumes alone and reads `waiting` while held, a chunk killed before its task arrives resumes with the full prompt, a second `run_created` is refused, cancel reaches subworkflow children, trigger pins are read, and one engine per home is enforced by an OS lock.

**Depends on.** SEC2A (`E/workers/effects.py`, `E/workers/local.py`) and SEC1A (`E/ledger/store.py`).

**Files.**

- [ ] Edit `E/nodes/agent.py`, `E/nodes/wait.py`, `E/nodes/subworkflow.py`, `E/nodes/base.py`, `E/core/waits.py`, `E/core/fold.py`, `E/core/ladder.py` and `E/runner.py`.
- [ ] Edit `E/triggers/ticker.py`, `E/triggers/claims.py` and `E/triggers/rows.py`.
- [ ] Edit `E/service/runs.py`, `E/service/api.py`, `E/ledger/store.py`, `E/ledger/inbox_table.py`, `E/definition/validate.py`, `E/workers/effects.py`, `E/workers/local.py`, `E/trace_export.py`, `E/ports/harness_adapter.py` and `E/host.py`.
- [ ] Edit the matching `ET/` tests. Create `SL/engine/e40_wakes.py` and `SL/engine/b69_resume.py`.

**Build.**

- [ ] B-63, L-37, B-73, B-54. A time `wait` writes a wake row with RFC 3339 UTC instants, reads `waiting` while held, and only the ticker resumes it. `Engine.start` returns `waiting` at once.
- [ ] B-69. Write a task marker when the task reaches the chat. A resume whose transcript holds no task resends the full prompt (AD-34).
- [ ] B-25, L-32, L-28, L-31, L-33. Refuse a second `run_created`. Fold `data.attempt` on endings. Keep the writer thread alive on `BaseException`. Refuse a non-dict append. Let the runner own executor errors.
- [ ] B-57. Never retry after `unknown` a model node that also declares an irreversible effect (AD-8).
- [ ] B-66, L-69, B-72, L-64, L-65. Cancel reaches children. A cancelled fire frees its slot. `run-now` on a parked trigger says why. One `Scheduler` per engine object. Settle the wake against the fire in one transaction.
- [ ] B-42, B-60. Read Settings at use and snapshot them on `run_created`. Apply trigger `role_pins` and `effort_pin`, and fire `after` triggers on every run.
- [ ] B-37, L-38, L-47, L-57, L-80. A cancelled reversible attempt is not retried. Refuse non-kebab node ids. Take the inbox `tried` list after the ladder walks. Prune `HarnessAdapter.marks`. Guard `run_files` reads.
- [ ] L-70. Take an OS lock on `<home>/engine.lock` before the host serves (AD-3).

**You see.**

- [ ] A run held on `wait seconds: 90` reads `waiting` in `explain`, then `passed` after the next tick with no action.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] One test per row cluster above, each through the service or the engine's public calls with a literal end state. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head, and the harness diff check. Save `bug1-regression.log`. Pass when head fails nothing the parent passes and the harness diff is empty.
- [ ] Lane 2. E40. Run `e40_wakes.py`. Save `bug1-e40.log`. Pass when the held run reads `waiting`, resumes on the tick after 90 s, and a retry backoff does the same.
- [ ] Lane 3. B-69. Run `b69_resume.py` on haiku under the lane lock, killing a chunk before its task arrives. Save `bug1-resume.log`. Pass when the resumed chunk receives the full prompt and ends `passed`.
- [ ] Lane 4. Start a subworkflow run and cancel the parent. Save `bug1-cancel.log`. Pass when the child reads `cancelled` and its fire slot is free.
- [ ] Lane 5. Start a second engine host on the same home. Save `bug1-lock.log`. Pass when it refuses with the lock holder named.
- [ ] Lane 6. Fire a trigger with `role_pins`. Save `bug1-pins.log`. Pass when `node_started` shows the pinned candidate.
- [ ] Lane 7. Append a second `run_created` through the ledger API. Save `bug1-created.log`. Pass when it is refused.
- [ ] Lane 8. Call `run-now` on a parked trigger. Save `bug1-runnow.log`. Pass when the reply names why nothing started.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `bug1-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `bug1-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Scheduler tick time in ms with 500 trigger rows.
- [ ] Probe. `SL/engine/x12_scheduler.py` tick timing, ten ticks.
- [ ] Baseline. The parent's tick on the same rows.
- [ ] Rule. Fail when the median tick grows by more than 25 %, because wake and fire now settle in one transaction.

**Review gate.** None. BUG1 changes no screen.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends BUG1 on the stack tip.

## Write the spec-gap code and close the validation holes (BUG2)

Rows B-18, L-29, L-34, B-24, B-87, B-27, B-76, B-68, B-23, B-20 (the refusal), B-46 (the refusal), B-22, B-90, L-20, L-22, L-26, L-75, L-54, L-55, L-56, B-61, B-92, L-89, B-77, B-85, B-71, B-19, B-43. ADs AD-1, AD-4, AD-5, AD-6, AD-7, AD-10, AD-11, AD-14, AD-15. Gate none. Proving checks the event-key lane and the validation lane. Done when every node event carries its keys and spans close, `required` edges gate readiness, subworkflow child folders travel in the bundle, nested fan-out and grader `llm` mode are refused at validation, `pinData` and `meta.needs` are in the content hash, and memo validity has one source.

**Depends on.** BUG1 (`E/runner.py`, `E/service/runs.py`, `E/nodes/subworkflow.py`).

**Files.**

- [ ] Edit `E/ledger/store.py`, `E/ledger/spans.py`, `E/ledger/memo.py`, `E/core/simulate.py`, `E/core/fold.py`, `E/core/ready.py`, `E/core/joins.py` and `E/runner.py`.
- [ ] Edit `E/definition/validate.py`, `E/definition/model.py`, `E/definition/folder.py`, `E/definition/registry.py` and `E/definition/expr.py`.
- [ ] Edit `E/nodes/subworkflow.py`, `E/nodes/join.py`, `E/nodes/loop.py` and `E/nodes/fake_provider.py`.
- [ ] Edit `E/service/versions.py`, `E/service/drafts.py`, `E/service/tests.py`, `E/service/runs.py`, `E/service/explain.py`, `E/control_door.py`, `E/trace_export.py` and `E/ports/library_fake.py`.
- [ ] Edit the matching `ET/` tests, including `test_import_rules.py`. Create `SL/engine/bug2_lanes.py`.

**Build.**

- [ ] B-18, L-29, L-34. Every node event carries `node_id`, `iteration`, `partition` and `attempt`, `node_scheduled` carries the input hash, and gate and cancel close their spans.
- [ ] B-24, B-87, B-27, B-76. Readiness follows `required` edges. Subworkflows get their own child folder, check `caller_policy` at every start, and a waiting child keeps the parent waiting. Bundles carry block folders.
- [ ] B-20, B-46. Refuse nested fan-out, loops over fanned input, loops in loop bodies and grader `llm` mode at validation with `nesting_unsupported` and `not_built`.
- [ ] B-22, B-90, L-20, L-22. Validate loop, join and wait parameters and the one-`one`-edge join rule. Run `expr.check`. Make the import and clock rules catch aliases, `importlib`, `uuid4`, `os.urandom`, `secrets`, `monotonic` and `perf_counter`.
- [ ] L-26, L-75. Put `pinData` and `meta.needs` in the content hash.
- [ ] B-68, L-54, L-55, L-56, B-61, B-92, L-89, B-43. Derive enablement from triggers. Fix the overlay draft read, the variant head on failure, `tested-by` on a passed live run, a fresh report on a woken test run, `needs_unmet` in the draft view, the need line on a force-published start, and `variant_of` on a variant draft.
- [ ] B-77, B-85, B-71, B-19, B-23. The fake switch answers every model kind and each chunk its own slice. `explain` lists spans. Memo validity is read from events and the unread flag goes. Join words follow AD-16.

**You see.**

- [ ] `python -m qmx_engine check` on a nested fan-out fixture prints `nesting_unsupported` with the file and line.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] One test per row cluster above, through `validate`, the service or the ledger API, with literal results. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head, the template suite, and the harness diff check. Save `bug2-regression.log`. Pass when head fails nothing the parent passes and the harness diff is empty.
- [ ] Lane 2. Run a fan-out with a join on the fake provider and read every node event. Save `bug2-events.log`. Pass when each carries the four keys and every span closes.
- [ ] Lane 3. Validate the nested fan-out, loop-in-loop and grader `llm` fixtures. Save `bug2-refusals.log`. Pass when each is refused with its named reason.
- [ ] Lane 4. Run a subworkflow template through `bundle` and back. Save `bug2-bundle.log`. Pass when the child folder travels and the child runs from it.
- [ ] Lane 5. Change only `pinData` in a draft. Save `bug2-hash.log`. Pass when the content hash changes.
- [ ] Lane 6. Run a multi-branch node with one `required` edge unmet. Save `bug2-required.log`. Pass when it does not start.
- [ ] Lane 7. Disable a version's last trigger. Save `bug2-enable.log`. Pass when the version reads disabled.
- [ ] Lane 8. Run `explain` on a passed run. Save `bug2-explain.log`. Pass when it lists the spans.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `bug2-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `bug2-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). `validate` time in ms over all 31 templates.
- [ ] Probe. Three runs.
- [ ] Baseline. The parent on the same templates.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. BUG2 changes no screen.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends BUG2 on BUG1.

## Fold gate answers, derive run state from the ledger, and let a partition walk its own ladder (BUG3)

Rows B-28, B-32 (GATE), B-40, L-68 and the rest of B-73 (LDR), B-35 (CHUNK), and CAPE's "resume a pause at his own limit". ADs AD-17, AD-16, AD-15, AD-9. Gate none. Proving checks the gate-fold lane and the runs-list lane. Done when an answered gate resumes its run, an irreversible step of unknown outcome waits on its inbox item and continues on the answer, `workflow_runs_list` shows in-flight runs with ledger-derived status, a failed partition walks its ladder alone, and a `limits` pause resumes from his answer.

**Depends on.** BUG2 (`E/core/fold.py`, `E/core/joins.py`, `E/control_door.py`).

**Files.**

- [ ] Edit `E/core/fold.py`, `E/core/joins.py`, `E/core/ladder.py`, `E/ports/inbox.py`, `E/service/inbox.py`, `E/service/runs.py`, `E/ledger/inbox_table.py` and `E/control_door.py`.
- [ ] Edit the matching `ET/` tests. Create `SL/engine/bug3_lanes.py`.

**Build.**

- [ ] Fold an inbox answer into the ledger, so the gate's run resumes on `retry`, `skip` or `stop`. A `limits` pause resumes on `resume`.
- [ ] Derive run status from the ledger alone, so `interrupted` and `waiting` come from events, and `workflow_runs_list` includes in-flight runs.
- [ ] Let a failed partition walk the ladder on its own, and let its join count it failed only after it parks.

**You see.**

- [ ] `GET /api/workflow-runs` on the engine host lists a run that is still running, with status `running`.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_fold.py` folds each answer to its literal run state. `test_joins.py` covers a partition that retries and passes. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head, the harness diff check, and full `just ci` under the CI lock. Save `bug3-regression.log`. Pass when head fails nothing the parent passes, the harness diff is empty, and `just ci` is green.
- [ ] Lane 2. Run an irreversible-external fixture whose effect reads `unknown`, then answer its item `retry`. Save `bug3-gate.log`. Pass when it waits, then continues on the answer.
- [ ] Lane 3. List runs while one runs and one waits. Save `bug3-list.log`. Pass when both appear with ledger-derived status.
- [ ] Lane 4. Fail one partition of three once on the fake provider. Save `bug3-partition.log`. Pass when it retries alone and the join fires with three results.
- [ ] Lane 5. Pause on a `limits` block, then answer `resume`. Save `bug3-limits.log`. Pass when the run continues.
- [ ] Lane 6. Answer a gate `stop`. Save `bug3-stop.log`. Pass when the run ends `cancelled` with the answer recorded.
- [ ] Lane 7. Kill the engine during a run, then list runs. Save `bug3-interrupted.log`. Pass when the run reads `interrupted` from the ledger.
- [ ] Lane 8. Answer one item twice. Save `bug3-twice.log`. Pass when the second answer is refused.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `bug3-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `bug3-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). `workflow_runs_list` time in ms with 1,000 runs.
- [ ] Probe. A fixture ledger with 1,000 runs, five calls.
- [ ] Baseline. The parent's list on the same ledger.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. BUG3 changes no screen.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends BUG3 on BUG2.

## Seat the engine inside qma.serve (L1)

GATE-M. Rows B-11, B-64. B-56 (writing `session_homes`) needs a table that `qmx-control` does not have at the base, so it goes to `BACKLOG.md` with owner L17 (Appendix G). ADs AD-3, AD-21. Granted by ruling 50 (E1, the engine seat), which is later than ruling 24. Proving check the x13 door lanes on `qma.serve`. Done when `python -m qma.serve serve` starts the engine with the harness and control in one process, the `workflow_*` routes answer there, and `qmx_engine.host` is gone.

**Depends on.** BUG3 (`E/control_door.py`) and his merge click.

**Files.**

- [ ] Edit `qmx-agents/packages/qma-harness/src/qma/serve.py` and `H/routes.py` only where they compose the engine.
- [ ] Delete `E/host.py` and `ET/test_host.py`. Edit `E/control_door.py`.
- [ ] Edit `HT/test_boot.py`, `SL/engine/lane_host.py` and `SL/engine/x13_doors.py`.

**Build.**

- [ ] Start the engine from `routes._serve` through the engine's public calls, after the harness and control are up, on the same home and its `engine.lock`.
- [ ] Mount the engine's routes on the `qma.serve` app. Remove `qmx_engine.host` and its interim CLI path.

**You see.**

- [ ] `python -m qma.serve status` lists the engine, and `GET /api/workflow-runs` answers on the `qma.serve` port.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_boot.py` asserts `serve` starts the engine once and refuses a second host on the same home. Run `-n 2` in `qma-harness` and `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness`, `qmx-control` and `qmx-engine` suites with `-n 2` at the parent and at head, and `git diff --stat <parent> HEAD -- qmx-agents/packages/qma-harness`. Save `l1-regression.log`. Pass when head fails nothing the parent passes and the diff lists only `serve.py`, `routes.py` and the tests.
- [ ] Lane 2. Start `qma.serve` on a throwaway home and run `x13_doors.py` against it. Save `l1-doors.log`. Pass when every door answers as it did on the interim host.
- [ ] Lane 3. Start a scheduled run through `qma.serve` and let it pass. Save `l1-run.log`. Pass when it ends `passed` and the ledger sits in the home.
- [ ] Lane 4. Start a second `qma.serve` on the same home. Save `l1-second.log`. Pass when it refuses.
- [ ] Lane 5. Stop and restart `qma.serve` during a held run. Save `l1-restart.log`. Pass when the run resumes on the next tick.
- [ ] Lane 6. Call an engine route without the bearer. Save `l1-auth.log`. Pass when it returns 401.
- [ ] Lane 7. Grep the tree for `qmx_engine.host`. Save `l1-grep.log`. Pass when nothing imports it.
- [ ] Lane 8. Open the copilot chat list on `qma.serve` during an engine run. Save `l1-chats.log`. Pass when chats and the engine work together.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `l1-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `l1-processes.log`. Pass when no `qma.serve`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). `qma.serve` start time in ms to the first answered route.
- [ ] Probe. Five starts.
- [ ] Baseline. The parent's `qma.serve` start without the engine.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. L1 changes no screen.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends L1 on the stack tip.

## Make providers data and give each model its own row (RTR1)

GATE-M. Rows AL-7 (the harness half), H-14, H-30 to H-33, H-36, H-37 of `39` section 4. ADs AD-39, AD-13. Grant H29 (pool exception, rulings 39, 92, 95 and 98). Proving check the one-token Test on every configured row. Done when `KeyProvider` and `GptPlan` read from bundled `profiles/*.toml` plus user overrides, each model row carries wire, capabilities, window and the normaliser fields, adding a provider needs no code, and today's relay lanes behave as before.

**Depends on.** CAPH (`H/launch.py`) and his merge click.

**Files.**

- [ ] Edit `H/profiles.py`, `H/launch.py` and `H/__init__.py`. Create `H/registry.py` and the folder `H/profiles/` with one TOML per bundled profile of AD-39.
- [ ] Edit `qmx-agents/packages/qma-harness/pyproject.toml` for package data.
- [ ] Edit `HT/test_profiles.py`. Create `HT/test_registry.py`.
- [ ] Edit `SL/qma/s08_providers.py`. Create `SL/qma/rtr1_registry.py`.

**Build.**

- [ ] Load profile rows and model rows from the bundled TOMLs, then the user's overrides of the same name, then the live catalog merged with the curated list. His override wins.
- [ ] Move `wire` from the provider row to the model row. Move `HOST_QUIRKS` wire quirks into model-row data. Keep env quirks as launch defaults for a chat whose main is that provider.
- [ ] Add the one-token "Test" on the pinned wire, and the clamped effort as sent.
- [ ] Export one read API for the registry from `qma.harness`, for RTR5.

**You see.**

- [ ] `rtr1_registry.py list` prints every bundled profile with its model rows, and "Test" on the OpenRouter row answers.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_registry.py` asserts override precedence, a model row with `wire: openai_chat` beside an Anthropic one in one profile, and that adding a TOML adds a provider with no code. Run `-n 2` in `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` suite with `-n 2` at the parent and at head, and `git diff --stat <parent> HEAD -- qmx-agents/packages/qma-harness`. Save `rtr1-regression.log`. Pass when head fails nothing the parent passes and the diff lists only this PR's files.
- [ ] Lane 2. Run "Test" on the plan row (haiku, under the lane lock) and on the OpenRouter row. Save `rtr1-test.log`. Pass when both answer one token and journal one row each.
- [ ] Lane 3. Run `SL/qma/hp11_lanes.py`. Save `rtr1-lanes.log`. Pass when every lane passes as at the parent.
- [ ] Lane 4. Add a user TOML for a new provider on a throwaway home. Save `rtr1-add.log`. Pass when it appears in the registry with no code change.
- [ ] Lane 5. Override one model's window in a user TOML. Save `rtr1-override.log`. Pass when the registry reads his value.
- [ ] Lane 6. Fetch the OpenRouter live catalog. Save `rtr1-catalog.log`. Pass when it merges with the curated list without dropping a curated row.
- [ ] Lane 7. Check the Kimi Code profile. Save `rtr1-ua.log`. Pass when no override can touch its User-Agent.
- [ ] Lane 8. Run `SL/qma/s16_gpt.py` if his GPT sign-in exists. Save `rtr1-gpt.log`. Pass when the GPT lane works as at the parent, or the log reads `not run, no GPT sign-in`.
- [ ] Lane 9. Run `tools/secret_scan.py` and grep the TOMLs for key-shaped values. Save `rtr1-secrets.log`. Pass when both are clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr1-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Registry load time in ms.
- [ ] Probe. Ten loads.
- [ ] Baseline. Today's `profiles.py` row build.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. The provider pages are the UI session's.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR1 on the stack tip.

## Route every request by model id and normalise it for its target (RTR2)

GATE-M. Rows AL-6 (non-plan lanes), AL-8, 41 C1, 41 H1, 42 N3, N15, N16, N19. ADs AD-38 (key and GPT lanes, router hardening), AD-50, AD-29, AD-15, AD-28 (`model_scope`). Grants H10, H14, H36 and the router-hardening part of H27 (pool exception). The hardening ships whatever P1 showed. Proving checks the key-lane half of P3 and the router half of E43. Done when the router runs on its own thread at a pinned port, resolves each request's model to one lane, normalises every non-plan request for its model row, keeps a late error's status, enforces `model_scope`, journals agent ids, and restarts itself on the same port.

**Depends on.** RTR1 (the registry).

**Files.**

- [ ] Edit `H/relay.py` (`RelayGrant.profile` at lines 162 to 170, threading, port, journal), `H/launch.py` (`API_TIMEOUT_MS`, hint headers on key and GPT launches), `H/harness.py` (grants with `model_scope`), `H/__init__.py`, and `qmx-agents/packages/qma-harness/src/qma/gpt/translate.py` (normaliser first).
- [ ] Create `H/normalise.py` and `HT/test_normalise.py` with fixtures per provider. Edit `HT/test_relay.py`, `test_translate.py`, `test_launch.py` and `test_chat.py`.
- [ ] Edit `SL/qma/fake_model.py` (slow-prefill and late-error modes), `SL/qma/hp11_lanes.py` and `SL/qma/s22_relay.py`. Create `SL/qma/rtr2_lanes.py`.

**Build.**

- [ ] Move the relay onto its own thread and event loop. Take the configured port or the next free one and pin it in `<home>/router.port`. Restart a dead or stalled router thread on the same port, and add a health check that `qma.serve` reads.
- [ ] Resolve each request's `model` through the registry to the GPT, key or chat lane. Refuse an unlisted third-party id with 400 and a Claude id on a chat with no plan grant with a message that names `delegate`.
- [ ] Write `normalise(row, body, headers)` per AD-50 from the model row's fields. Run it on the key and GPT lanes before thinking and translation. Send nothing before the upstream's first event unless the row sets `keepalive` (Claude's default is off). Map a usage-limit 429 to `x-should-retry: false`.
- [ ] Enforce `model_scope` on every grant. Drop the incoming bearer and run the egress stop on every non-plan lane.
- [ ] Journal each request with session, agent and parent agent ids, lane, provider, account alias, model, tokens, cache, thinking tokens, latency and status class (H36). Set `CLAUDE_CODE_GATEWAY_HINT_HEADERS=1` on key and GPT launches only.
- [ ] Set `API_TIMEOUT_MS` on every launch above the largest row timeout plus 60 s, at least 780 s (Claude's default).

**You see.**

- [ ] The router journal for a key-main chat shows one row per request with its agent id, lane and model.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_normalise.py` feeds each provider fixture and asserts the literal egress body and headers. `test_relay.py` asserts lane choice per model id, the 400 on an unknown id, and that a request outside `model_scope` is refused. Run `-n 2` in `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` suite with `-n 2` at the parent and at head, `hp11_lanes.py`, and `git diff --stat <parent> HEAD -- qmx-agents/packages/qma-harness`. Save `rtr2-regression.log`. Pass when head fails nothing the parent passes and the diff lists only this PR's files.
- [ ] Lane 2. P3 key-lane half. Run a ten-turn tool loop with thinking on the OpenRouter rows for Kimi, DeepSeek, GLM, Qwen and MiniMax (provider proof). Save `rtr2-p3.log`. Pass when, for each provider, every turn is 2xx or the row is recorded off with its error class.
- [ ] Lane 3. E43 router half. Run the fake upstream with a 400 s and a 900 s prefill on a 1M prompt, and a late 429 after 15 s. Save `rtr2-e43.log`. Pass when nothing is resent and the late 429 keeps its status.
- [ ] Lane 4. Tee the bytes that leave the router for a key-main chat. Save `rtr2-egress.log`. Pass when no `defer_loading`, unlisted beta, `metadata.user_id`, unlisted `x-claude-code-*` header or `sk-ant-` value leaves.
- [ ] Lane 5. Stall the router loop. Save `rtr2-restart.log`. Pass when it restarts on the pinned port and key chats resume.
- [ ] Lane 6. Send a request outside a chat's `model_scope`. Save `rtr2-scope.log`. Pass when it is refused.
- [ ] Lane 7. Put a fake Claude token in a key-lane request. Save `rtr2-canary.log`. Pass when it fails closed with a `black` item.
- [ ] Lane 8. Take the router's port with another process before boot. Save `rtr2-port.log`. Pass when it pins the next free port and every launch reads it.
- [ ] Lane 9. Run `tools/secret_scan.py` and grep the journal for header values. Save `rtr2-secrets.log`. Pass when both are clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr2-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Router overhead per request in ms, from receipt to upstream send.
- [ ] Probe. 200 requests to the fake upstream.
- [ ] Baseline. The parent's relay on the same probe.
- [ ] Rule. Fail when the median overhead exceeds 20 ms, because every chat request passes the router.

**Review gate.** None. RTR2 changes no screen.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR2 on RTR1.

## Add the in-house chat-completions lane (RTR3)

GATE-M. Rows AL-5, 41 M9. ADs AD-38 (chat lane), AD-39, AD-50. Grant H12 (in-house, pool exception, ruling 99). Proving check the chat-lane half of P3. Done when a model row with `wire: openai_chat` is served through the in-house translator with thinking and tool calls intact over ten turns, and no third-party proxy is in the path.

**Depends on.** RTR2 (`H/relay.py`).

**Files.**

- [ ] Create `H/chatlane.py` in the shape of `qma/gpt/translate.py`, and `HT/test_chatlane.py`.
- [ ] Edit `H/relay.py` (lane dispatch) and `H/profiles/opencode-go.toml`. Add an OpenRouter chat-completions row to `H/profiles/openrouter.toml` as provider proof.
- [ ] Create `SL/qma/rtr3_lanes.py`.

**Build.**

- [ ] Translate Anthropic Messages to OpenAI chat completions and back, per H12's mapping. Thinking blocks map to `reasoning_content` and back inside a tool loop. The translator's own signatures are stripped on return. Tool call ids map both ways.
- [ ] Run AD-50's normaliser first, then the translation, with the same lease and journal as the key lane.

**You see.**

- [ ] A chat on the OpenRouter chat-completions row answers a tool call and a follow-up with thinking shown.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_chatlane.py` round-trips a three-turn fixture with thinking and two tool calls and asserts the literal Messages output. Run `-n 2` in `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` suite with `-n 2` at the parent and at head, `hp11_lanes.py`, and `git diff --stat <parent> HEAD -- qmx-agents/packages/qma-harness`. Save `rtr3-regression.log`. Pass when head fails nothing the parent passes and the diff lists only this PR's files.
- [ ] Lane 2. P3 chat-lane half. Run a ten-turn tool loop with thinking on the OpenRouter chat-completions rows for Kimi and DeepSeek. Save `rtr3-p3.log`. Pass when every turn is 2xx and thinking round-trips.
- [ ] Lane 3. Run the same loop through a fake chat-completions upstream that checks the request shape. Save `rtr3-shape.log`. Pass when the fake accepts every request.
- [ ] Lane 4. Force a 429 and a 400 from the fake upstream. Save `rtr3-errors.log`. Pass when each reaches the CLI with its class journaled.
- [ ] Lane 5. Run OpenCode Go if his key exists. Save `rtr3-opencode.log`. Pass when it answers, or the log reads `not run, no key`.
- [ ] Lane 6. Tee the egress bytes. Save `rtr3-egress.log`. Pass when no Anthropic-only field or `sk-ant-` value leaves.
- [ ] Lane 7. Stream a long answer. Save `rtr3-stream.log`. Pass when the CLI receives it in order with usage carried.
- [ ] Lane 8. Read the journal. Save `rtr3-journal.log`. Pass when each row reads lane `chat`.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `rtr3-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr3-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Translation time per streamed chunk in microseconds.
- [ ] Probe. Lane 7's stream.
- [ ] Baseline. The key lane on the same fake stream.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. RTR3 changes no screen.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR3 on RTR2.

## Build the account pool and the one error classifier (RTR4)

GATE-M. Rows AL-3 (the pool), AL-4, L-63, 41 H2, 42 N13, and H-13, H-23 to H-28, H-34, H-35 and H-117 of `39` section 4. ADs AD-12, AD-40 (3) and (6), AD-9, AD-16 (the account rung). Grants H33 and the pool (ruling 39), and H6. The two-host fact exchange (E53) needs a Contabo node and is in Appendix G. Proving checks P7 and E8, run on fake key accounts. Done when leases rotate by `least_used`, a 429 cools one `(account, model)` and the next lease takes another, a past `reset_at` never loops, a plan 401 is forwarded and benches only on the CLI's needs-login signal or three 401s over five minutes, several GPT sign-ins refresh safely, and the engine's ladder rotates accounts.

**Depends on.** RTR3 (`H/relay.py`).

**Files.**

- [ ] Create `H/pool.py` and `H/classify.py`. Edit `H/relay.py`, `H/usage.py` (per-account readings), `H/harness.py` (`Harness.usage()` per account), `H/home.py` (GPT sign-in homes), `H/__init__.py`, and `qmx-agents/packages/qma-harness/src/qma/gpt/siwc.py` (the refresh lock).
- [ ] Create `HT/test_pool.py` and `HT/test_classify.py`. Edit `HT/test_gpt_lane.py`.
- [ ] Edit `E/admission.py`, `E/core/ladder.py`, `E/runner.py` (`Run.wake`), `E/ports/harness_adapter.py`, `ET/test_admission.py` and `ET/test_ladder.py`.
- [ ] Create `SL/qma/rtr4_pool.py`.

**Build.**

- [ ] Lease per `(session, provider)` with strategies `least_used` (Claude's default for background), `round_robin`, `fill_first`, `reset_window` and `random`, plus `priority` and `background_priority`. His copilot account gets `background_priority: last` (Claude's default). Share, ceiling and cooldown are his values, unset by default.
- [ ] Map every provider and router error once to the closed classes of AD-40 (6), with hints for the pool and the ladder.
- [ ] Cool `(account, model)` on 429 and 402. The provider's `reset_at` wins. A probing request answered by a 429 with no or a past reset is a generic 429, never straight back to `probing`.
- [ ] Forward a plan 401 unchanged. Bench a Claude account only on the CLI's needs-login signal or three 401s on new requests over five minutes. Never move his copilot chat.
- [ ] Give each GPT account its own sign-in home and refresh under a cross-process file lock that never writes older tokens over newer. Report a dead sign-in once.
- [ ] Make the engine's admission read pool readings, and the ladder's account rung rotate through the pool.

**You see.**

- [ ] `rtr4_pool.py status` prints each account with its strategy, cooldown and reading, and no QMX limit.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_pool.py` covers rotation, a per-model cooldown, switch-back, the probing rule and the 401 rule with literal states. `test_classify.py` maps one fixture per class. `test_ladder.py` asserts the account rung picks the next account. Run `-n 2` in `qma-harness` and `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` and `qmx-engine` suites with `-n 2` at the parent and at head, and `git diff --stat <parent> HEAD -- qmx-agents/packages/qma-harness`. Save `rtr4-regression.log`. Pass when head fails nothing the parent passes and the diff lists only this PR's files.
- [ ] Lane 2. P7. Two fake Kimi keys on a throwaway home, a 429 with `retry-after: 30` on key 1. Save `rtr4-p7.log`. Pass when key 1 cools 30 s, the next request goes to key 2, it switches back after the cooldown, and the class reads `rate_limit`.
- [ ] Lane 3. E8 on fake accounts. Eight Background chats across two fake accounts with `max_live_chats` at least 8. Save `rtr4-e8.log`. Pass when leases spread by `least_used` and a running chat keeps its account.
- [ ] Lane 4. Answer a probing request with a 429 whose reset is past. Save `rtr4-probing.log`. Pass when it backs off as a generic 429 and does not loop.
- [ ] Lane 5. Send three 401s over five minutes on a fake plan account. Save `rtr4-401.log`. Pass when one 401 benches nothing and the third benches the account with one "sign in again" item.
- [ ] Lane 6. Run two GPT refreshes at once against a fake token endpoint. Save `rtr4-refresh.log`. Pass when the newer token survives.
- [ ] Lane 7. Fail an engine node with `rate_limit` on account 1. Save `rtr4-ladder.log`. Pass when the account rung moves it to account 2.
- [ ] Lane 8. Return a 402 on one key. Save `rtr4-billing.log`. Pass when the class reads `billing` and the account cools.
- [ ] Lane 9. Run `tools/secret_scan.py` and grep the pool state for token values. Save `rtr4-secrets.log`. Pass when both are clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr4-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Lease time in microseconds with 20 accounts.
- [ ] Probe. 10,000 leases on fake accounts.
- [ ] Baseline. None, the pool is new. Record head only.
- [ ] Rule. Fail when the median exceeds 1 ms, because a lease sits on every request.

**Review gate.** None. The Accounts page is the UI session's.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR4 on RTR3.

## Make the engine read windows, compaction points and role lists from the registry (RTR5)

GATE-M. Rows B-21, B-48, B-86, L-10 (the per-model point), AL-7 (the engine half), H-17 of `39` section 4. ADs AD-39, AD-34, AD-13. Gate GATE-M through its parent. Proving checks the chunk lane and the role lane. Done when chunk sizes come from each model's window, the compaction point is 0.40 at 512k and above and 0.75 below, the token estimate uses `count_tokens` or `chars_per_token`, and the default role lists are generated from the registry in `key, gpt, plan` order.

**Depends on.** RTR4 (`E/ports/harness_adapter.py`).

**Files.**

- [ ] Edit `E/settings.py`, `E/roles.py`, `E/core/partitions.py`, `E/nodes/agent.py`, `E/ports/harness_adapter.py` and `E/ports/settings.py`.
- [ ] Edit `ET/test_roles.py`, `test_chunks.py`, `test_agent.py` and `test_settings.py`. Edit `SL/engine/e09_roles.py` and `SL/engine/e03_chunks.py`.

**Build.**

- [ ] Read each candidate's window, `compact_at`, `chars_per_token` and capabilities from the registry through the harness's public read API. Delete the `context_window` setting.
- [ ] Size chunks at `chunk.fill` 0.30 of the model's window (Claude's default). Estimate tokens with `count_tokens` when the row has it, else characters divided by `chars_per_token` with 10 % headroom.
- [ ] Pass the compaction point per model as `compact_at` (Claude's default 0.40 at 512k and above, 0.75 below).
- [ ] Generate the default role lists from the registry by class, in `key, gpt, plan` order, Chinese rows first, no Fable. Add the auxiliary roles `titler`, `compactor`, `curator`, `vision_describer`, `transcriber`, `video_analyst`, `goal_judge`, `reviewer` and `background_review` as role rows.
- [ ] On a fallback to another model, re-run preflight and re-plan the unstarted chunks for the new window.

**You see.**

- [ ] `python -m qmx_engine explain` on a chunked run shows each chunk's planned size and the model window it came from.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_chunks.py` sizes chunks for a 1M row and a 128k row with literal counts. `test_roles.py` asserts the generated order and no Fable. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head, and the harness diff check. Save `rtr5-regression.log`. Pass when head fails nothing the parent passes and the harness diff is empty.
- [ ] Lane 2. Run `e03_chunks.py` on fake rows with 1M and 128k windows. Save `rtr5-chunks.log`. Pass when chunk sizes follow each window.
- [ ] Lane 3. Run `e09_roles.py` with the plan, OpenRouter and a fake Kimi row configured. Save `rtr5-roles.log`. Pass when generated lists read `key, gpt, plan` and test mode still resolves `claude/haiku` first.
- [ ] Lane 4. Start an agent chunk on a 1M fake row and on haiku. Save `rtr5-compact.log`. Pass when the launched CLIs carry 0.40 and 0.75.
- [ ] Lane 5. Fall back mid-run from the 1M row to the 128k row. Save `rtr5-replan.log`. Pass when unstarted chunks re-plan and finished memos stand.
- [ ] Lane 6. Remove `count_tokens` from a row. Save `rtr5-estimate.log`. Pass when the estimate uses `chars_per_token`.
- [ ] Lane 7. Run one agent template on haiku under the lane lock. Save `rtr5-haiku.log`. Pass when it ends `passed`.
- [ ] Lane 8. Grep the engine for `context_window`. Save `rtr5-grep.log`. Pass when no setting remains.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `rtr5-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr5-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Chunk planning time in ms for 300 items.
- [ ] Probe. A 300-item fixture, five plans.
- [ ] Baseline. The parent on the same fixture.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. RTR5 changes no screen.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR5 on RTR4.

## Give every chat registry-generated sub-agent definitions (RTR6)

BLOCKED-ON G (H38). Rows AL-6 (native sub-agents), 41 C4, 42 N7, N21. ADs AD-38, AD-29, AD-4 (`via: native`). Proving check P1k rerun on the real router. If PRB's P1 failed, plan mains get no third-party definitions here, and key and GPT mains keep them on P1k alone. If P1k failed too, this packet is dropped and third parties go through DLG. Done when a Kimi-main chat spawns DeepSeek and Qwen sub-agents through the router with their ids unchanged, a plan main whose lane is off gets no third-party definition, and the set regenerates on relaunch.

**Depends on.** RTR5, PRB's findings, and call G granted.

**Files.**

- [ ] Create `H/agents.py` and `HT/test_agents.py`. Edit `H/launch.py`, `H/harness.py`, `H/__init__.py` and `HT/test_launch.py`.
- [ ] Edit `E/nodes/agent.py`, `E/ports/harness_adapter.py` and `ET/test_agent.py`.
- [ ] Create `SL/qma/rtr6_lanes.py`.

**Build.**

- [ ] Add `NewChat.agents` for Interactive, Background and Child chats, passed to the SDK `agents` option.
- [ ] Generate one definition per role by default, plus one per model he pins in Settings. Tools are inherited and never widened, and no `maxTurns` is set.
- [ ] Filter each chat's set by its lanes and each row's `plan_main_native`, and regenerate it on every relaunch.
- [ ] Make engine agent nodes with `via: native` pass their definitions, and resolve to `via: delegate` when a definition is filtered out.

**You see.**

- [ ] A Kimi-main chat on the OpenRouter row lists `reviewer` and `researcher` in its `Agent` tool and uses one.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_agents.py` asserts the generated set for a key main, a GPT main and a plan main with the lane off, with literal names and models. Run `-n 2` in `qma-harness` and `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` and `qmx-engine` suites with `-n 2` at the parent and at head, and `git diff --stat <parent> HEAD -- qmx-agents/packages/qma-harness`. Save `rtr6-regression.log`. Pass when head fails nothing the parent passes and the diff lists only this PR's files.
- [ ] Lane 2. P1k on the real router. Run a Kimi main on the OpenRouter row with generated definitions naming DeepSeek and Qwen rows. Save `rtr6-p1k.log`. Pass when each sub-agent spawns, its request reaches the router with its id unchanged, and its result returns.
- [ ] Lane 3. Start a plan main on haiku with the plan lane off, under the lane lock. Save `rtr6-planoff.log`. Pass when its `Agent` tool lists no third-party definition.
- [ ] Lane 4. Pin a model in Settings and relaunch a chat. Save `rtr6-regen.log`. Pass when the new definition joins at the next turn on the same session id.
- [ ] Lane 5. Run a GPT main if his GPT sign-in exists. Save `rtr6-gpt.log`. Pass when its sub-agents spawn, or the log reads `not run, no GPT sign-in`.
- [ ] Lane 6. Run an engine agent node with `via: native` on a key main. Save `rtr6-engine.log`. Pass when its sub-agent runs on the named provider.
- [ ] Lane 7. Tee the egress of lane 2. Save `rtr6-egress.log`. Pass when P4's egress lines hold for the key main.
- [ ] Lane 8. Read the journal of lane 2. Save `rtr6-journal.log`. Pass when each sub-agent row carries its agent id and parent id.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `rtr6-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `rtr6-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Cache read tokens on the main's second turn with and without definitions.
- [ ] Probe. Lane 2's main, two turns each way.
- [ ] Baseline. The main with no definitions.
- [ ] Rule. No fail rule. A drop to 0 cache reads goes into `BACKLOG.md` as a risk.

**Review gate.** None. Call G is his review of its scope.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR6 on the stack tip of the moment G is granted (Override 7).

## Build the plan lane dark, prove it, then let him turn it on (RTR7)

BLOCKED-ON G, because without H38 the plan lane has nothing to carry (HARNESS-REQUESTS H38 fallback). Also needs PRB's P0 and P1 to have passed. If P1 failed, this packet is not built, plan chats launch as built, and his plan copilot reaches Kimi and Qwen through DLG or today's blocking `delegate`. Rows AL-6 (plan main), 41 H1, M1, M2, M7, 42 N9, N15, N18. ADs AD-38 (plan lane, ship gate, kill switch, billing watch), AD-50, AD-48 (health check). Grant H27 (pool exception plus ruling 98). Proving checks P4 and P2 against the dark build, then the router half of E49. Done when the lane is built off for every account, P4 passes per provider or marks it `delegate_only`, P2 passes, the boot canary runs, a stalled router flips the lane off and plan chats continue on the same session ids, and he has turned the lane on for his account himself after review.

**Depends on.** RTR6, PRB's P0 and P1 PASS rows, and call G granted.

**Files.**

- [ ] Edit `H/relay.py` (plan path), `H/launch.py` (plan launch env and the `PlanLaunch` docstring), `H/profiles.py` (docstring at lines 6 to 8), `H/home.py`, `H/harness.py`, `H/usage.py` (billing watch), `H/money.py` (the docstring at lines 1 and 2 only), and `qmx-agents/packages/qma-harness/src/qma/serve.py` (supervision and canary).
- [ ] Create `HT/test_plan_lane.py`. Edit `HT/test_relay.py`, `test_launch.py` and `test_usage.py`.
- [ ] Create `SP/router/p4_normaliser.py` and `SP/router/p2_billing.py`, and `SL/qma/rtr7_lanes.py`.

**Build.**

- [ ] Plan launches, only while the account's lane is on, set `ANTHROPIC_BASE_URL` to the router, `ANTHROPIC_CUSTOM_HEADERS: x-qmx-grant: <secret>`, no credential variable, and the env P0 found.
- [ ] Serve the plan path for any method and path with the body and the raw header list unchanged, removing only `x-qmx-grant`. Read the grant before any bearer check, and pin with a test that a plan grant never reaches `_token_bearer`. Log no header value.
- [ ] Add Settings `router.plan_lane` per Claude account, off by default (Claude's default). Run P1's echo form as the boot canary and after every router restart. Turn the lane back on only after three healthy checks and a canary pass.
- [ ] On a failed health check, flip the lane off for every account and relaunch plan chats without a base URL on the same session ids, with one line to him. `qma.serve` runs this check until the desktop host exists (Appendix G).
- [ ] Add the billing watch on `overage_status` changes while the lane is on and the window is below 100 %. It turns the lane off for that account with one `urgent` item. `hard_stop` keeps doing the stopping.
- [ ] Rewrite the docstrings that say plan traffic never reaches the relay. Change no line of the money gate's code.
- [ ] Run P4 per provider and P2 against the dark build. Write `plan_main_native` per row from P4.

**You see.**

- [ ] With the lane on for a test session, a haiku plan chat answers through the router and its journal row reads lane `plan` with no header value.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_plan_lane.py` asserts byte-identical forwarding of a fixture with repeated headers, the grant removed, the grant read before the bearer check, and the lane off by default. Run `-n 2` in `qma-harness`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` suite with `-n 2` at the parent and at head, `hp11_lanes.py`, and `git diff --stat <parent> HEAD -- qmx-agents/packages/qma-harness`. Save `rtr7-regression.log`. Pass when head fails nothing the parent passes and the diff lists only this PR's files.
- [ ] Lane 2. P4. Run `p4_normaliser.py` under the lane lock with a haiku main, `ENABLE_TOOL_SEARCH=true`, and sub-agents on the OpenRouter rows for Kimi, DeepSeek, GLM, Qwen and MiniMax, plus fake upstreams for the forced and late errors. Save `rtr7-p4.log`. Pass when each provider reads PASS or is marked `delegate_only` per the section 26.14 P4 line, and the assumed window and the `API_TIMEOUT_MS` reading are recorded.
- [ ] Lane 3. P2. Run `p2_billing.py` with haiku through the lane, at most 20 turns (a probe bound). Save `rtr7-p2.log`. Pass when the five-hour reading moves, overage does not, no 401 appears, and the third turn reads cache.
- [ ] Lane 4. E49 router half. Stall the router loop with a plan chat open. Save `rtr7-e49.log`. Pass when within 10 s the lane is off and the plan chat continues with no base URL on the same session id.
- [ ] Lane 5. Restart the router thread. Save `rtr7-canary.log`. Pass when the canary runs and the lane returns only after three healthy checks.
- [ ] Lane 6. Grep every log and journal for `sk-ant-`, `Bearer ` and `x-qmx-grant` values. Save `rtr7-leak.log`. Pass when none is found.
- [ ] Lane 7. Feed a fake `overage_status` change with the lane on. Save `rtr7-billing.log`. Pass when the lane turns off for that account with one `urgent` item.
- [ ] Lane 8. Turn `router.plan_lane` off and start a plan chat. Save `rtr7-off.log`. Pass when it launches with no base URL.
- [ ] Lane 9. Run `tools/secret_scan.py` and `SL/qma/s06_money.py`. Save `rtr7-scans.log`. Pass when both are clean and the money gate behaves as at the parent.
- [ ] Lane 10. List processes after the lanes. Save `rtr7-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Added time to first token in ms for a plan turn through the lane.
- [ ] Probe. Ten haiku turns with the lane on and ten with it off.
- [ ] Baseline. The lane off.
- [ ] Rule. Fail when the median added time exceeds 100 ms, because his daily copilot would feel it.

**Review gate.** The lane touches his copilot's path, so he decides when it goes on.

- [ ] Show the operator in chat the P4 and P2 results in plain words, a screenshot of the Settings switch, and a short video of a plan chat with a Kimi sub-agent. The lane stays off until the operator turns it on for his account.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends RTR7 on the stack tip of the moment G is granted (Override 7).

## Rebuild delegate so helpers return a handle at once and report back between turns (DLG)

BLOCKED-ON G (H26). Rows AL-21, and H-01 to H-12 of `39` section 4. The `cli` target needs call E's containers and goes to Appendix G. ADs AD-41, AD-16 (the stall monitor for children), AD-40 (5), AD-49 (worktrees for real git repositories only). Proving check P5. Done when the copilot starts three helpers on Kimi, DeepSeek and Qwen and keeps working, each handle returns at once, results arrive between turns, a restart mid-run delivers each completion exactly once, `steer` and `stop` work, and a looping child is stopped by the stall monitor.

**Depends on.** RTR4 (leases and the classifier) and call G granted.

**Files.**

- [ ] Create `H/delegate.py`. Edit `H/tools.py` (`delegate_def` at line 388), `H/harness.py` (`_delegate` at line 425) and `H/__init__.py`.
- [ ] Edit `QX/models.py` and `QX/service.py` for the completions table in `control.db`.
- [ ] Edit `HT/test_delegate.py` and `HT/test_tools.py`, and the `qmx-control` tests.
- [ ] Edit `SL/qma/s11_helpers.py`. Create `SL/qma/dlg_lanes.py`.

**Build.**

- [ ] Give `delegate` the actions `start`, `list`, `steer` and `stop`, with `role`, `model`, `profile` and `effort` resolved as one bundle through the registry and the pool.
- [ ] Store each completion in `control.db` before announcing it, claim it once, and deliver it between parent turns as `InjectedText`. A child whose owner died reads `unknown`.
- [ ] Give children the parent's tools minus the deny list of H-10. Depth is a setting, 1 by default (Claude's default).
- [ ] Run AD-16's no-progress and loop detection on each child, which closes the gap CAPH opens for helper chats.
- [ ] Validate `output_schema` with one correction turn. Forward up to 8 images to a child whose row has vision. A child with no vision gets a named refusal until the multimodal packet (Appendix G), and the PR body names that departure.
- [ ] Put child processes in the child's Job object and report `orphaned_processes`. Give a child `worktree: true` a git worktree for a real repository only.

**You see.**

- [ ] The copilot's live dock data (`delegate list`) shows three helpers with provider, model and state while the parent answers him.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_delegate.py` asserts handle-at-once, delivery between turns, exactly-once delivery across a restart, `missed_steer`, and the deny list. Run `-n 2` in `qma-harness` and `qmx-control`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` and `qmx-control` suites with `-n 2` at the parent and at head, and `git diff --stat <parent> HEAD -- qmx-agents/packages/qma-harness`. Save `dlg-regression.log`. Pass when head fails nothing the parent passes and the diff lists only this PR's files.
- [ ] Lane 2. P5. A haiku copilot under the lane lock starts three helpers on the OpenRouter rows for Kimi, DeepSeek and Qwen and keeps working. Save `dlg-p5.log`. Pass when each handle returns at once and each result arrives between parent turns.
- [ ] Lane 3. Restart `qma.serve` while two helpers run. Save `dlg-restart.log`. Pass when each completion is delivered exactly once, or reads `unknown` if its process died.
- [ ] Lane 4. Give a fake-model helper a looping task. Save `dlg-stall.log`. Pass when it ends `stalled(loop)` with its summary.
- [ ] Lane 5. Steer a running helper, then stop another. Save `dlg-steer.log`. Pass when the steer lands at its checkpoint and the stop ends the child.
- [ ] Lane 6. Ask a helper for a schema-bound answer that it first breaks. Save `dlg-schema.log`. Pass when one correction turn fixes it or the result reads `schema_valid: false`.
- [ ] Lane 7. Ask a child to `delegate` with depth 1. Save `dlg-depth.log`. Pass when it is refused.
- [ ] Lane 8. Run `max_live_chats = 1` with a v2 parent waiting on its child. Save `dlg-slots.log`. Pass when it finishes.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `dlg-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `dlg-processes.log`. Pass when no child, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Time from `start` to the handle in ms.
- [ ] Probe. Ten starts on the fake model.
- [ ] Baseline. None, today's call blocks. Record head only.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. The live dock is the UI session's. Call G is his review of its scope.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends DLG on the stack tip of the moment G is granted (Override 7).

## Add the Hermes trigger kinds and failure contracts (HRME)

GATE-M through its parents. Rows H-59, H-60, H-61, H-62, H-63, H-64, H-72, H-135 and H-136 of `39` section 4, and 41 M5. ADs AD-10, AD-17. Proving checks the trigger lanes. The `session` kind validates and stores, but its firing waits for H34 (Appendix G), and the PR body names that departure. Done when `event` and `webhook` triggers fire once per occurrence, a model unreachable before any call re-runs at 5, 15 and 30 minutes in the same run, delivery is recorded apart from pass, a script's first line can say `[QMX_FAILURE]` or `[QMX_SILENT]`, a failure streak becomes one incident, a trigger can be created paused with a reason, and `explain_trigger` says why a trigger did not fire.

**Depends on.** RTR4 (the classifier) and L1 (routes on `qma.serve`).

**Files.**

- [ ] Edit `E/ledger/migrations.py` (the kind check at line 35, as a forward migration), `E/triggers/rows.py`, `E/triggers/ticker.py`, `E/triggers/preflight.py`, `E/triggers/quota.py`, `E/nodes/script.py`, `E/service/rest.py`, `E/ledger/inbox_table.py` and `E/runner.py`.
- [ ] Create `E/service/triggers.py`. Edit `ET/test_triggers.py`, `test_script.py`, `test_inbox.py` and `test_rest.py`.
- [ ] Edit `SL/engine/x12_scheduler.py`. Create `SL/engine/hrme_lanes.py`.

**Build.**

- [ ] Add the kinds `event`, `webhook` and `session` by a forward migration. A webhook route takes a per-trigger secret and fires once per delivery id.
- [ ] When the classifier says the model was unreachable before any call, hold the model node `waiting(resume_at)` at 5, 15 and 30 minutes in the same run (Claude's default).
- [ ] Record `delivery` as `delivered`, `unverified`, `failed` or `none`. An empty payload fails closed.
- [ ] Read a script's first stdout line for `[QMX_FAILURE]` and `[QMX_SILENT]`.
- [ ] Turn a failure streak into one incident nudge, and give incidents their logic. Let a trigger be created paused with a reason in one write. Add `explain_trigger`.
- [ ] Check the quota hold's sparse-schedule rule and fix it if it fires twice.

**You see.**

- [ ] `GET /api/workflow-triggers/{id}/explain` on a paused trigger names its reason and its next fire.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_triggers.py` asserts once-per-delivery-id, the re-run schedule, the delivery field and the paused create, with literal rows. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head, and the harness diff check. Save `hrme-regression.log`. Pass when head fails nothing the parent passes and the harness diff is empty.
- [ ] Lane 2. Post the same webhook delivery twice to `qma.serve`. Save `hrme-webhook.log`. Pass when one run starts.
- [ ] Lane 3. Make the fake upstream unreachable for the first call. Save `hrme-rerun.log`. Pass when the node waits at 5 minutes on the fake clock and the run passes on the re-run.
- [ ] Lane 4. Run a script whose first line is `[QMX_SILENT]` and one with an empty delivery payload. Save `hrme-contracts.log`. Pass when the first reads silent and the second reads delivery `failed`.
- [ ] Lane 5. Fail one trigger three times. Save `hrme-incident.log`. Pass when one incident item opens.
- [ ] Lane 6. Fire an `event` trigger from a bus event. Save `hrme-event.log`. Pass when it fires once.
- [ ] Lane 7. Create a trigger paused with a reason, then call `explain_trigger`. Save `hrme-explain.log`. Pass when the reason shows.
- [ ] Lane 8. Store a `session` trigger. Save `hrme-session.log`. Pass when it validates and does not fire.
- [ ] Lane 9. Run `tools/secret_scan.py` and grep the ledger for the webhook secret. Save `hrme-secrets.log`. Pass when both are clean.
- [ ] Lane 10. List processes after the lanes. Save `hrme-processes.log`. Pass when no `qma.serve`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Webhook to `run_created` time in ms.
- [ ] Probe. Twenty deliveries.
- [ ] Baseline. A manual `run-now` on the same workflow.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** None. The trigger form is the UI session's.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends HRME on the stack tip.

## Put a destructive-shell floor under every mode and make his rules data (HRMH)

BLOCKED-ON G (H31). Rows AL-22, and H-41 to H-47, H-49, H-51, H-53, H-57 and H-129 of `39` section 4. H-45 (suggestions mined from approvals) goes to Appendix G. ADs AD-43. This PR edits where the money gate keeps its never-allow list and never the gate's logic, so any finding near the gate is a blocker. Proving checks the money and approval lanes. Done when the money gate still runs first and unchanged, a destructive-shell floor runs after it in every mode, his allow and never-allow lists are Settings data, engine asks are denied at once while copilot asks wait, NT device and UNC paths, secrets in command bodies and invisible Unicode are refused, MCP results lose Unicode tags, and money and risk keys are locked against agents.

**Depends on.** RTR4 (stack order) and call G granted.

**Files.**

- [ ] Edit `H/money.py` (the never-allow list at line 717 becomes data, the gate's code unchanged), `H/chat.py` (asks at line 24) and `H/tools.py`. Create `H/rules.py`.
- [ ] Edit the Settings validator in `QX/service.py` for locked keys.
- [ ] Edit `HT/test_money.py`, `test_answers.py` and `test_posture.py`. Create `HT/test_rules.py`.
- [ ] Edit `SL/qma/s06_money.py` and `SL/qma/s29_approvals.py`. Create `SL/qma/hrmh_lanes.py`.

**Build.**

- [ ] Add the destructive-shell floor after the money gate. Move the never-allow globs into Settings-editable lists with source and `last_matched`.
- [ ] Answer asks per context. An engine run denies at once. A copilot chat waits, with an optional attended timeout that is off by default (Claude's default) and fails closed. A delegated child never asks.
- [ ] Refuse NT device and UNC paths, secrets in an outbound command body, and invisible or bidi Unicode. Strip Unicode tag characters from MCP results. Scan context files and personas at load, and warn on his own files.
- [ ] Add a first-run import of permissions, MCP servers and skills from a Claude folder he points at. The lanes use a fixture folder and never `~/.claude`.
- [ ] Lock money and risk-sizing keys against agents in the Settings validator. Only his explicit unlock opens them.

**You see.**

- [ ] The rules list shows his rows with source and last match, and the floor row read-only.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_rules.py` asserts the order money gate, then floor, then his lists, and each refusal kind with a literal reason. `test_money.py` passes unchanged. Run `-n 2` in `qma-harness` and `qmx-control`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qma-harness` and `qmx-control` suites with `-n 2` at the parent and at head, and `git diff --stat <parent> HEAD -- qmx-agents/packages/qma-harness`. Save `hrmh-regression.log`. Pass when head fails nothing the parent passes and the diff lists only this PR's files.
- [ ] Lane 2. Run `s06_money.py`. Save `hrmh-money.log`. Pass when every money case is refused as at the parent.
- [ ] Lane 3. Ask a Background chat on haiku under the lane lock to run `rm -rf` on a scratch folder in `bypassPermissions`. Save `hrmh-floor.log`. Pass when the floor refuses it.
- [ ] Lane 4. Run `s29_approvals.py` with an engine chat and a copilot chat asking the same thing. Save `hrmh-asks.log`. Pass when the engine ask is denied at once and the copilot ask waits.
- [ ] Lane 5. Send a command with `\\?\C:\` and a UNC path. Save `hrmh-paths.log`. Pass when both are refused.
- [ ] Lane 6. Return an MCP result with Unicode tag characters. Save `hrmh-tags.log`. Pass when the model sees them stripped.
- [ ] Lane 7. Have an agent write a locked risk key. Save `hrmh-locked.log`. Pass when the validator refuses it.
- [ ] Lane 8. Import a fixture Claude folder. Save `hrmh-import.log`. Pass when its rules appear with source `imported` and `~/.claude` was not read.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `hrmh-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `hrmh-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Tool-call check time in microseconds with 200 rules.
- [ ] Probe. 10,000 checks.
- [ ] Baseline. The parent's gate on the same probe.
- [ ] Rule. Fail when the median grows by more than 1 ms, because every tool call passes the floor.

**Review gate.** None. The Rules page is the UI session's. Call G is his review of its scope.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends HRMH on the stack tip of the moment G is granted (Override 7).

## Give every template a plain name, let template A take a playlist without asking, and ground numbers in evidence (TPL1)

GATE-M through its parents. Rows AL-14, AL-15 (the E48 gate for what has landed), B-88, B-84, L-81, L-82, L-83, L-85, L-86, L-87, L-88, L-76, L-77, L-93, B-79, B-91, B-86 (the remap). ADs AD-46, AD-45 (evidence), AD-17 (proposals), AD-22. Proving checks E48 and E51. E48's scan and tier rows belong to SEC1B and SEC2B and run there. Done when all 31 templates carry plain ids and titles, template A expands a playlist fixture with no ask, every runnable template passes a haiku test run, the evidence rule fails a number found only in model output, and proposals use a closed action list.

**Depends on.** RTR5 (generated role lists) and BUG2 (B-76 lets `SHARED_COPIES` go).

**Files.**

- [ ] Edit every folder under `T/`, renaming each folder id to a plain phrase, and `T/catalog.py` and `T/install.py`.
- [ ] Edit `E/nodes/grader.py` and the shared `render_and_grade` block for the evidence rule.
- [ ] Edit `qmx-agents/packages/qmx-engine/docs/TEMPLATES.md` and `ET/test_templates.py`.
- [ ] Edit `SL/engine/t_templates.py` and `SL/engine/e21_real_tests.py`. Create `SL/engine/e51_evidence.py`.

**Build.**

- [ ] Rename all 31 ids and titles to plain phrases. Use SOLUTION-DESIGN section 26.9's proposed titles as Claude's defaults, which he edits with the copilot later (ruling 83).
- [ ] Make template A expand a playlist, a channel or a saved collection without asking, with a chunked fan-out edge over the expanded list, and a cron or monitor trigger available.
- [ ] Build the evidence set of AD-45 from pinned inputs, fetched and read artifacts and declared scripts no model wrote. Exclude model output, model-written code's output, timestamps, dates, run ids, hashes and versions.
- [ ] Make PP and DM emit typed proposals with a closed action list.
- [ ] Remap card roles to the generated role lists. Drop `SHARED_COPIES`. Fix the template lows listed above.

**You see.**

- [ ] `python -m qmx_engine templates list` prints 31 plain titles, and template A's run on a playlist fixture shows the expanded items.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_templates.py` asserts every id is a plain kebab phrase with no code prefix, each runnable template has one planted-number case, and the evidence rule's four E51 cases hold. Run `-n 2` in `qmx-engine`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-engine` suite with `-n 2` at the parent and at head, `test_templates.py`, and the harness diff check. Do not run the full `run_all.py`. Save `tpl1-regression.log`. Pass when head fails nothing the parent passes and the harness diff is empty.
- [ ] Lane 2. E48. Run every runnable template on haiku under the lane lock through `t_templates.py`. Save `tpl1-e48.log`. Pass when each ends `passed` and each draft validates with its named needs.
- [ ] Lane 3. E51. Run `e51_evidence.py`. Save `tpl1-e51.log`. Pass when a number found only in an agent's output fails, the same number in a fetched source passes, a year only in a timestamp does not count, and a number printed by model-written code fails.
- [ ] Lane 4. Run template A on a playlist fixture with no ask rule seeded. Save `tpl1-intake.log`. Pass when the list expands and chunks run with no ask.
- [ ] Lane 5. Install the pack on a throwaway home. Save `tpl1-install.log`. Pass when 31 templates install disabled with plain titles.
- [ ] Lane 6. Run PP on the fake provider. Save `tpl1-proposal.log`. Pass when its proposal names actions from the closed list only.
- [ ] Lane 7. Resolve an old template id. Save `tpl1-oldid.log`. Pass when the renamed id resolves.
- [ ] Lane 8. Count haiku turns from the journals. Save `tpl1-turns.log`. Pass when the count is recorded for Appendix E.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `tpl1-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `tpl1-processes.log`. Pass when no `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Haiku turns and wall time for the E48 run.
- [ ] Probe. Lane 2.
- [ ] Baseline. TP4's 83 haiku turns for nine templates, from the engine program's trail.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** He sees the template names.

- [ ] Show the operator in chat a screenshot of the 31 plain titles and a short video of template A taking a playlist fixture with no ask, before the root appends TPL1.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends TPL1 on the stack tip.

## Let the copilot build, validate and test a workflow from one line (TPL2)

GATE-M through its parents. Rows AL-16 (the builder part), with alignment items B 10 and A M-17 of `39` section 5. ADs AD-22, AD-46 (the builder only). The skills lifecycle, the curator and `/learn` need the Library and go to Appendix G. Proving check E42. Done when the copilot builds a three-node workflow from a one-line request, reads traces before drawing a graph, saves a draft on its agent ref, validates it and test-runs it on haiku, adds a `limits` block only when he asks, and gives it a plain name.

**Depends on.** TPL1 and L1.

**Files.**

- [ ] Rewrite `qmx-agents/packages/qmx-agents/src/qmx_agents/skills/build-workflow/SKILL.md` and add its reference files in the same folder.
- [ ] Create `SL/engine/e42_builder.py`.

**Build.**

- [ ] Write the skill for the copilot. Read the traces of similar runs first. Draft with `workflow_drafts_put`, validate, test-run on haiku with `workflow_tests_run`, and read `explain` on failure. Name the workflow plainly. Never add a `limits` block unless he asks. Never publish or enable, which stay his.
- [ ] H20 is deferred, so a draft save may ask once in default mode. The lane seeds the DOMAIN_WRITE allow rule in its throwaway home, and the PR body names that.

**You see.**

- [ ] A copilot chat asked "build a workflow that fetches three RSS feeds and writes one summary" leaves a validated, test-passed draft on its agent ref.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] The `qmx-agents` skill test, if one exists, loads the skill's frontmatter. Otherwise this block's evidence is lane 2. Run `-n 2` in `qmx-agents`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `opus` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set. Lanes 5 to 10 are a menu.

- [ ] Lane 1. Regression lane against the parent. Run the `qmx-agents` and `qmx-engine` suites with `-n 2` at the parent and at head, the harness diff check, and full `just ci` under the CI lock. Save `tpl2-regression.log`. Pass when head fails nothing the parent passes, the harness diff is empty, and `just ci` is green.
- [ ] Lane 2. E42. Run `e42_builder.py` with a haiku copilot on `qma.serve` under the lane lock. Save `tpl2-e42.log`. Pass when a three-node draft lands on its agent ref, validates, and its test run passes, with no harness ask beyond the seeded rule.
- [ ] Lane 3. Read the copilot's tool calls in lane 2. Save `tpl2-traces.log`. Pass when it read traces before its first draft.
- [ ] Lane 4. Read the draft. Save `tpl2-draft.log`. Pass when it has a plain name and no `limits` block.
- [ ] Lane 5. Ask the copilot to publish. Save `tpl2-publish.log`. Pass when it returns a card for him and does not publish.
- [ ] Lane 6. Ask for a workflow with "stop after 10 turns". Save `tpl2-limits.log`. Pass when it adds a `limits` block he asked for.
- [ ] Lane 7. Give a request that fails validation first. Save `tpl2-repair.log`. Pass when it reads the refusal and fixes the draft.
- [ ] Lane 8. Count haiku turns. Save `tpl2-turns.log`. Pass when the count is recorded for Appendix E.
- [ ] Lane 9. Run `tools/secret_scan.py`. Save `tpl2-secrets.log`. Pass when it is clean.
- [ ] Lane 10. List processes after the lanes. Save `tpl2-processes.log`. Pass when no `qma.serve`, `claude` or `qma-cli-launcher` process and no lane lock is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Not gated (Override 4). Turns and wall time from the request to a passed test run.
- [ ] Probe. Lane 2, three requests.
- [ ] Baseline. None, the builder is new. Record head only.
- [ ] Rule. No fail rule. Recorded for the trail.

**Review gate.** He uses the builder himself.

- [ ] Show the operator in chat a short video of lane 2 and a screenshot of the draft, before the root appends TPL2.

**Merge.**

- [ ] Checker's CLEAN verdict at the exact head SHA, or the coordinator's verdict after the one fix round.
- [ ] Low findings logged in `lows.md`. Findings outside this section go to `BACKLOG.md`.
- [ ] Verdict recorded in `ledger.tsv` with the patch-id.
- [ ] The root appends TPL2 as the tip of the stack.

## Close the program

- [ ] Every box above is checked with its evidence, every lane outside a run set has its `menu, not run` row, and every skipped BLOCKED-ON packet has a `decisions.tsv` row naming its call.
- [ ] Reply to the operator with the report autopilot-stack names. Give links to the stack's root and tip, a one-line verdict per PR, what was skipped or parked and why, the open calls, and the trail at the store's `decisions.tsv`.
- [ ] Write the store's `RESUME.md` with the stack state for his landing session and for any packet a later call unblocks.
- [ ] List every `hard/*` branch and worktree for his go. Delete none without it.

## Appendix A. Prototype evidence

No prototype ran in this planning pass. PRB holds the probes, and it runs second. The planner read these facts from `origin/engine/base` at `132169c7` and `origin/rebuild/base` at `4345eafa` with `git show`, `git grep` and `git merge-tree` on 2026-10-18, and each one shaped a PR.

| Fact read from the code | Where | Shapes |
|---|---|---|
| `_STRONG` names `claude/fable`, and `roles.test_only` is OpenRouter Kimi | `E/settings.py:22`, `:70` | HYG0 |
| `roles.test_order` tries test-only rows first and `roles.live_order` is `plan, key` | `E/settings.py:71-72`, `E/roles.py:85-86` | HYG0 |
| `run --mode` offers `live` | `E/__main__.py:56` | HYG0, E38 |
| qma-core's member-set test lacks `packages/qmx-engine` | `QC/tests/test_extensibility.py:136` | HYG0 |
| `DEFAULTS` holds `runaway.*`, `agent.max_turns` 12, `max_tool_calls` 200, run timeouts, `background_share` 0.5, `fill-first`, `max_live_chats` 6 | `E/settings.py:36-59` | CAPE |
| The fixture `bad-agent-no-max-turns` pins the old lint | `ET/fixtures/workflows/` | CAPE |
| `Budgets` has `max_live_chats` 4, `background_cap` 0.5, `max_turns` 50, `max_budget_usd` 5.0 | `H/launch.py:221-261, 518-519` | CAPH |
| `ChatTableFull` refuses at once with `needs_you` | `H/harness.py:185, 362-433` | CAPH |
| `hard_stop` and `overage_rule` read the provider's overage state | `H/usage.py:43, 204` | CAPH keeps them |
| The relay binds `127.0.0.1` on an ephemeral port, and its GPT lane pings only after the stream starts | `H/relay.py:28, 139-143, 339-343, 725-731` | RTR2 |
| The trigger kind check allows only `cron, interval, manual, after` | `E/ledger/migrations.py:35` | HRME |
| `qmx-control` has no `session_homes` table | `git grep session_homes` under `QX/` | L1 sends B-56 to the backlog |
| `qma.serve` is `qmx-agents/packages/qma-harness/src/qma/serve.py` and composes in `routes.py` | `serve.py`, `H/routes.py` | L1 |
| The builder skill is a placeholder | `qmx_agents/skills/build-workflow/SKILL.md` | TPL2 |
| `rebuild/base` adds six files since `ed704c92`, two `conftest.py` files and four HP2 probe files under `scripts/probes/qma/`, and none is in `engine/base`'s changes | `git diff --name-only ed704c92 origin/rebuild/base` | Override 6 |
| Merging `engine/base` into `rebuild/base` has no conflict | `git merge-tree --write-tree` | GATE-M |

Unproven by design until their probe runs. P0, P1 and P1k in PRB. P3 in RTR2 and RTR3. P7 in RTR4. P4 and P2 in RTR7. P5 in DLG. E33 in SEC2B.

## Appendix B. Alternatives rejected

- **Autopilot-full.** The operator reviews before landing and withholds merge authority, so the selection rule picks autopilot-stack.
- **Two stacks, one for the engine and one for the harness.** Router and pool PRs touch both packages, so two stacks would cross. One linear stack with Override 6 keeps one parent per PR.
- **Waiting for the merge click before any work.** Eight PRs need neither the click nor a call. Starting them now loses nothing, because the six files `rebuild/base` adds touch no packet.
- **Waiting idle on calls D, E, F and G.** Override 7 skips blocked packets and appends them when granted.
- **Building the plan lane without H38.** HARNESS-REQUESTS H38 says the plan lane then has nothing to carry. RTR7 is gated on G for that reason.
- **A harness-side stuck detector inside CAPH.** H28 does not request one, and the harness is touched only as granted. DLG's stall monitor (H26) covers helper chats, and Appendix C names the gap until then.
- **Folding the HG4 rows H32, H34, H37 and H3 into this program.** They are outside the operator's list for this program and all wait for G. They are in Appendix G.
- **Ten live lanes per PR.** The light rule replaced them. They stay as a menu because `check-plan.mjs` requires them.

## Appendix C. Risks

- **Helper chats lose their 50-turn stop at CAPH (CAPH to DLG).** A copilot Child chat started by today's blocking `delegate` has no loop stop until DLG's stall monitor, which waits for G. A looping helper is stopped only by its parent's interrupt or by him. The blast radius is one Child chat and his plan window.
- **Haiku test turns draw on his copilot's plan window (all model lanes).** S13 of SOLUTION-DESIGN section 26.13 says so. Appendix E estimates the turns.
- **Probes forward his plan login through a loopback probe process (PRB, RTR7).** The probe router writes no header value and keeps nothing past the hop. Lane 6 of each greps for leaks.
- **OpenRouter stands in for direct provider rows (RTR2, RTR3, RTR6, RTR7, DLG).** Direct Kimi, DeepSeek, GLM, Qwen and MiniMax rows stay `tool_search: false` and unproven until he adds keys.
- **E33 may fail on Windows 11 Home (SEC2B).** The fallback is the container tier for shipped scripts too, which needs Docker for every script.
- **The template renames change every content hash (CAPE, TPL1).** Installed templates are disabled drafts, so no enabled trigger breaks.
- **Opus reviews Opus (every PR).** A cross-family review is not run.
- **No macOS or Linux test machine.** Out of scope for this program.

## Appendix D. Links and reading list

- The contract is `architecture/workflow-engine/`. Owners read `ARCHITECTURE-SPINE.md` for the ADs their PR names, `SOLUTION-DESIGN.md` sections 17, 18 and 26 and any section their PR names, and `HARNESS-REQUESTS.md` for the H rows their preamble names.
- The design record is `research/methodology/39-architecture-rerun.md`, with its "Review applied" and "Fix-check applied" sections. The row ids are in `40-retriage.md` section 2. The findings behind them are `41-rerun-review.md` and `42-fix-check.md`.
- Rulings live in `research/methodology/26-operator-rulings-and-alignment.md`. Its latest ruling wins.
- The engine program's run store `D:/QMX-worktrees/qma-ship/engine/` holds the old briefs, `BACKLOG.md`, `lows.md` and `review/`. Owners read a line there only when their PR's rows cite it.
- The coordinator keeps its trail per `C:/Users/Mubarak/.claude/skills/show-me-your-work/SKILL.md` in the store's `decisions.tsv`.
- Never read `tracker/qma-v2/archive/` as the plan.

## Appendix E. Sizing (an estimate)

Every number is the planner's guess, not a measurement. Effort is focused builder hours. The checker adds about 45 minutes per PR and the coordinator about 20. Haiku turns are plan turns through the ship home's login. OpenRouter calls are provider-proof calls only.

| PR | Effort (h) | Haiku turns | OpenRouter calls | Gate |
|---|---|---|---|---|
| HYG0 | 2 | 5 | 2 | none |
| PRB | 4 | 25 | 20 | none |
| CAPE | 8 | 10 | 0 | none |
| CAPH | 4 | 5 | 0 | GATE-M |
| SEC1A | 4 | 0 | 0 | none |
| SEC2A | 6 | 0 | 0 | none |
| SEC1B | 5 | 0 | 0 | F |
| SEC2B | 8 | 0 | 0 | E |
| HG3 | 5 | 30 | 0 | D, GATE-M |
| BUG1 | 8 | 15 | 0 | none |
| BUG2 | 8 | 0 | 0 | none |
| BUG3 | 5 | 0 | 0 | none |
| L1 | 4 | 5 | 0 | GATE-M |
| RTR1 | 6 | 5 | 10 | GATE-M |
| RTR2 | 8 | 5 | 80 | GATE-M |
| RTR3 | 5 | 0 | 40 | GATE-M |
| RTR4 | 8 | 0 | 0 | GATE-M |
| RTR5 | 4 | 10 | 0 | GATE-M |
| RTR6 | 5 | 10 | 30 | G |
| RTR7 | 8 | 60 | 60 | G, P0 and P1 |
| DLG | 8 | 25 | 30 | G |
| HRME | 6 | 0 | 0 | GATE-M |
| HRMH | 6 | 15 | 0 | G |
| TPL1 | 8 | 150 | 0 | GATE-M |
| TPL2 | 4 | 40 | 0 | GATE-M |
| Total | 154 | 415 | 272 | |

- **Number of PRs.** Twenty-five. Eight need nothing, ten need only the merge click, seven need a call.
- **Wall time.** One builder at a time with a checker beside it, pipelined where files allow. Roughly eight to ten working days if every call is granted early, about four for the eight PRs that need nothing. A guess.
- **Full suite.** `just ci` runs twice, in BUG3's lane 1 and in TPL2's lane 1.

## Appendix F. Files two packets share

Never give these to two builders at once. Pipelining between two PRs listed on one row waits for the earlier PR's verdict.

| File | Packets |
|---|---|
| `E/settings.py`, `E/roles.py` | HYG0, CAPE, RTR5 |
| `E/definition/lint.py` | CAPE, SEC1A, SEC1B |
| `E/definition/validate.py` | SEC2A, BUG1, BUG2 |
| `E/definition/model.py`, the v1 schema | CAPE, SEC2A, BUG2 |
| `E/nodes/agent.py` | CAPE, HG3, BUG1, RTR5, RTR6 |
| `E/nodes/llm.py` | CAPE, HG3 |
| `E/nodes/script.py` | SEC2A, SEC1B, SEC2B, HRME |
| `E/workers/local.py`, `E/workers/confine.py` | SEC2A, SEC2B, BUG1 |
| `E/workers/effects.py` | SEC2A, BUG1 |
| `E/ledger/store.py` | SEC1A, BUG1, BUG2 |
| `E/ledger/inbox_table.py` | SEC1A, BUG1, BUG3, HRME |
| `E/ledger/memo.py`, `E/service/explain.py` | SEC1A, BUG2 |
| `E/service/rest.py` | SEC1A, HRME |
| `E/trace_export.py` | SEC1A, BUG1, BUG2 |
| `E/service/runs.py` | SEC1A, BUG1, BUG2, BUG3 |
| `E/core/fold.py` | CAPE, BUG1, BUG2, BUG3 |
| `E/core/ladder.py` | CAPE, BUG1, BUG3, RTR4 |
| `E/core/ready.py`, `E/core/simulate.py` | CAPE, BUG2 |
| `E/core/joins.py` | BUG2, BUG3 |
| `E/runner.py` | CAPE, BUG1, BUG2, RTR4, HRME |
| `E/admission.py` | CAPE, RTR4 |
| `E/ports/harness_adapter.py` | HG3, BUG1, RTR4, RTR5, RTR6 |
| `E/ports/settings.py` | CAPE, RTR5 |
| `E/control_door.py` | BUG2, BUG3, L1 |
| `E/triggers/ticker.py`, `E/triggers/rows.py` | BUG1, HRME |
| `E/host.py` | BUG1, L1 |
| `T/**` | CAPE, SEC2A, SEC1B, SEC2B, TPL1 |
| `H/launch.py` | CAPH, HG3, RTR1, RTR2, RTR6, RTR7 |
| `H/harness.py` | CAPH, HG3, RTR2, RTR4, RTR6, RTR7, DLG |
| `H/usage.py` | CAPH, RTR4, RTR7 |
| `H/relay.py` | RTR2, RTR3, RTR4, RTR7 |
| `H/profiles.py` | RTR1, RTR7 |
| `H/home.py` | HG3, RTR4, RTR7 |
| `H/__init__.py` | RTR1, RTR2, RTR4, RTR6, DLG |
| `H/tools.py` | DLG, HRMH |
| `qma/serve.py` | L1, RTR7 |
| `QX/service.py` | HG3, DLG, HRMH |
| `HT/test_launch.py` | CAPH, HG3, RTR2, RTR6, RTR7 |
| `HT/test_delegate.py` | CAPH, DLG |
| `SL/engine/e09_roles.py` | HYG0, RTR5 |

## Appendix G. Named backlog, not scheduled in this program

Each item names why it waits and what it needs. None is built here.

| Item | Rows | Waits for |
|---|---|---|
| MM, the multimodal layer (H30, AD-42, E44) | AL-18 | call G; RTR5's capability rows |
| BRW, the browser pack, take-over and HUD for the copilot (H35, AD-44, E45, P-BR) | AL-10 | call G; ruling 30's journeys explained to him first |
| Cua and MT5 demo click-through with the five-layer proof (AD-33, E46) | AL-9 | BRW; his demo account list in Settings; the money gate first |
| cTrader demo click-through | AL-9 | paid machines (a Windows desktop placement) and a demo-only cTrader ID |
| MEM, memory with the built-in provider (AD-18) | B-52, AL-19 | a real or fake `LibraryPort` decision; BUG2 |
| LIB, the Library contract pieces (Library L11, L18, L19, L20) | B-41, B-43, B-76 (L18), B-83, B-82 | the Library Hub program |
| DESK, the desktop host and output directives (AD-48, AD-45, E47, E49 desktop half) | AL-17, AL-12 | the shell probe; L1; the UI session |
| HG4 rest, pack sets, session loops, review fork, `Harness.complete` (H32, H34, H37, H3; P-PK, P-FK) | AL-11 | call G |
| `delegate` `cli` targets in containers (AD-41, E52) | AL-21 (part) | calls G and E; the `qmx-worker-cli` image |
| Skills lifecycle, curator and `/learn` (AD-46) | AL-16 (part) | the Library's lifecycle kinds |
| Suggestions mined from approvals (H-45) | AL-22 (part) | HRMH |
| Engine later packets GRADE, PIN, NFO, REPLAY and EVR | B-46, B-81, B-47, B-20, B-82, B-80, L-84 | BUG2's refusals; REPLAY needs Library L20 |
| Doctor verdicts and challengers (AD-26) | B-34 | MEM and the self-improvement packet |
| The mini-app packet with `qmx app check` (AD-19) | AL-13 | H3 under G; the mini-app program |
| Session homes table and writes (AD-35, L17) | B-56 | its own `qmx-control` packet |
| Worktrees for Library items, `reconcile` and checkpoints (AD-49) | H-89, H-108, H-109 | the Library Hub |
| Two-host pool fact exchange (E53) | 41 H7, 42 N11 | the Contabo node |
| Contabo node, vault and run passes (AD-28, AD-30) | B-17 (Settings half) | his Contabo setup; paid machines for any burst provider |
| Copilot standing loops (AD-47) | H-67 to H-69 | H34 under G |
| Lane-script hygiene, scripts only | L-3, L-5, L-11, L-13, L-15, L-41, L-59, L-62, L-67, L-72, L-73, L-74, L-78, L-79, B-74, L-27, B-62 | any free slot; L-74 after BUG1 |
| Deferred harness rows | B-5 (H20), B-53 (H21) | his later call; B-5's UI card with the UI session |
| Data | none | ruling 91, a deeper data study first |

## Appendix H. Defaults

Every value here is Claude's default, not the operator's. Each is UI-editable, and each was checked against file 26 and AD-40.

| Setting | Default | Where it lands |
|---|---|---|
| Role lists | `key, gpt, plan`, Chinese rows first in every tier, no Fable | HYG0, then generated in RTR5 |
| Test-mode first candidate | `claude/haiku` through the plan login | HYG0 |
| `pool.strategy` | `least_used` | CAPE, RTR4 |
| Copilot account `background_priority` | `last` | RTR4 |
| Account share, ceiling, cooldown | unset | RTR4 |
| `[budgets] max_budget_usd`, `background_cap`, Background and Child `max_turns` | unset | CAPH |
| `max_live_chats` | derived from RAM, `session_mb` 1,536, `overhead_mb` 4,096 on the PC | CAPH |
| `limits.interactive_reserve` | 2 | kept |
| `timeout.idle` | 300 s agent, 600 s script | CAPE |
| `timeout.in_tool` | 1,200 s of no CPU and no IO | CAPE |
| `timeout.grace` and the warning | 120 s, warning at 80 % | CAPE |
| `loop.repeat`, `loop.window`, `loop.no_convergence` | 5, 8, 6 of 8 | CAPE |
| Crash loop | 3 engine restarts, then park | CAPE |
| `chunk.fill` | 0.30 of the model's window | RTR5 |
| Compaction point | 0.40 at 512k and above, 0.75 below | RTR5 |
| `chars_per_token` | 3, with 10 % headroom | RTR1, RTR5 |
| `first_token_timeout_s` | 120 s plus 60 s per 100k prompt tokens | RTR1, RTR2 |
| `API_TIMEOUT_MS` | above the largest row timeout plus 60 s, at least 780 s | RTR2 |
| `keepalive` per row | off | RTR2 |
| `router.plan_lane` | off until the ship gate passes and he turns it on | RTR7 |
| `delegate` depth | 1 | DLG |
| Attended ask timeout | off | HRMH |
| Spend-neutral re-run | 5, 15, 30 minutes | HRME |
| Template titles | SOLUTION-DESIGN section 26.9's proposals | TPL1 |

## Appendix I. Gates and calls

| Gate | What it is | Packets that wait | If it never comes |
|---|---|---|---|
| GATE-M | His merge click of `engine/base` into `rebuild/base` | CAPH, L1, RTR1 to RTR5, HRME, TPL1, TPL2, and HG3, RTR6, RTR7, DLG, HRMH beside their calls | the eight no-gate PRs ship on `engine/base` and the rest wait |
| D | Grant HG3, narrowed, H2 first | HG3 | engine agent nodes on the PC are held when E35 shows a shell tool running without an ask |
| E | Edited and model-written scripts never run bare on the PC | SEC2B | B-30 stays open, so a host script can still reach his plan login and keyring |
| F | A money scan that fails closed with no allow-list | SEC1B | B-89 stays open, so the lint still skips script text and prompts |
| G | Grant the HG4 rows outside the pool exception, H38 included | RTR6, RTR7, DLG, HRMH | helpers stay on today's blocking `delegate`, one at a time; no native third-party sub-agents |
| P1 result | PRB's probe under his `/login` | RTR7, and RTR6's plan-main half | no plan lane; plan copilot helpers go through DLG |
| Paid machines | A burst provider or a Windows desktop placement | none scheduled; cTrader click-through in Appendix G | nothing in this program changes |

## Appendix J. Attention, for the operator

The operator's Attention list is in `PROMPT-HARDENING.md`, beside the paste prompt. It names his merge click, calls D to G, the optional sign-ins and keys, and the risks of Appendix C in plain words.
