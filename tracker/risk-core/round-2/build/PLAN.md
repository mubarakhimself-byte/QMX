# QMX risk and sizing build program

This program delivers what he asked for on 7 November. A unit that can trade, size itself, configure itself and ship as a template, as a baseline anyone can use and a layer anyone can customize.
After it, the 31 labelled stand-ins for sizing, exits and halts are replaced, and the 18 sockets are widened or named as staying shut.
A fault in one block costs that unit its entries and never an exit. One unit's fault never reaches another. A scripted watch carries 200 units so he doesn't have to.
Every value stays a labelled placeholder until the numbers talk. Agents never touch money, and only he promotes.
There are 69 PRs. RC-01 to RC-20 end at stop point A, RC-21 to RC-48 at stop point B, RC-49 to RC-66 at stop point C, and RC-67 to RC-69 need his demo sign-in.
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

| # | Id | Stop | PR | Depends on |
|---|---|---|---|---|
| 1 | RC-01 | A | Make the contract tests honest before a real block lands | none |
| 2 | RC-02 | A | Name every refused field, say what each risk module is for, and start the developer guide | RC-01 |
| 3 | RC-03 | A | Split a unit into a logic half and a risk half, with a fingerprint each | RC-02 |
| 4 | RC-04 | A | Let the node test logic and trust a click for risk | RC-03 |
| 5 | RC-05 | A | Give sizers a typed amount and one converter that knows the account's currency | RC-02 |
| 6 | RC-06 | A | Ship the sizer that answers money, catch absurd sizes, and make pricing its own call | RC-04, RC-05 |
| 7 | RC-07 | A | Bring the exchange rate to both hosts, and convert every money figure at the seam | RC-06 |
| 8 | RC-08 | A | Write one decision row before every send, and explain any size from it | RC-07 |
| 9 | RC-09 | A | Keep a raising block from reaching the exits in its own unit | RC-08 |
| 10 | RC-10 | A | Keep one unit's fault from stopping any other unit | RC-09 |
| 11 | RC-11 | A | Run every exit each bar, side-correct, with reasons and a fixed order | RC-10 |
| 12 | RC-12 | A | Make the shipped exit blocks read numbers from evidence | RC-11 |
| 13 | RC-13 | A | Make a brake a control row that runs in the unit | RC-10 |
| 14 | RC-14 | A | Read every brake's state from one fold | RC-13 |
| 15 | RC-15 | A | Write risk events and would-have rows in both hosts | RC-14 |
| 16 | RC-16 | A | Let a brake flatten, stop and send to paper, with a person only where it says so | RC-15 |
| 17 | RC-17 | A | Ship the canary template and the records it needs | RC-16, RC-12 |
| 18 | RC-18 | A | Let a draft reach paper on his click, with the safety half of G | RC-17 |
| 19 | RC-19 | A | Reach a first filled paper entry from zero, on a practice venue | RC-18 |
| 20 | RC-20 | A | Ready stop point A for his signature | RC-19 |
| 21 | RC-21 | B | Give size its named modifiers | RC-08 |
| 22 | RC-22 | B | Make house money one rule on one ledger, and switch rows on by a fact | RC-14, RC-21 |
| 23 | RC-23 | B | Give every number its derivation, range, authority and reason | RC-17 |
| 24 | RC-24 | B | Widen the built engine to risk numbers, with a bounded memory | RC-23 |
| 25 | RC-25 | B | Let a sizing number and an exit number really move, and show it on the receipt | RC-24 |
| 26 | RC-26 | B | Keep open trades on their numbers, and survive a restart mid-count | RC-25 |
| 27 | RC-27 | B | Give the node a live account surface | RC-07 |
| 28 | RC-28 | B | Observe costs from fills and let the sizer read them | RC-25, RC-27 |
| 29 | RC-29 | B | Add the feasibility verdict and re-test account brakes across two units | RC-27 |
| 30 | RC-30 | B | Build one base bar on a feed and roll every stream up from it | RC-10 |
| 31 | RC-31 | B | Let a unit read a second stream with no look-ahead | RC-30 |
| 32 | RC-32 | B | Let a unit hold more than one position per market | RC-31 |
| 33 | RC-33 | B | Run sessions and per-market settings | RC-32 |
| 34 | RC-34 | B | Run the remaining logic roles | RC-33 |
| 35 | RC-35 | B | Make the SQS a gate slot, cost hurdle first | RC-28, RC-34 |
| 36 | RC-36 | B | Put isolation, news and caution on one sticker, with tolerations | RC-35 |
| 37 | RC-37 | B | Measure spread and quote gaps on the node, and make one curve per world | RC-35 |
| 38 | RC-38 | B | Move the SQS rule and producer before the old gate goes | RC-37 |
| 39 | RC-39 | B | Ship the scalper and intraday templates, and prove each reaches paper | RC-19, RC-22, RC-26, RC-36 |
| 40 | RC-40 | B | Give the node one admit seam, called by both hosts | RC-35 |
| 41 | RC-41 | B | Apply kill effects to entries and give every veto an off switch | RC-40 |
| 42 | RC-42 | B | Run the node in two passes, exits first | RC-41 |
| 43 | RC-43 | B | Give a parked entry a lifetime and never send it twice | RC-42 |
| 44 | RC-44 | B | Bound the entries pass in time and beat the watchdog honestly | RC-43 |
| 45 | RC-45 | B | Let a declared no-stop entry compile, size and send | RC-44 |
| 46 | RC-46 | B | Keep a declared no-stop position alive through ticks, restart and reconcile | RC-45 |
| 47 | RC-47 | B | Give the copilot its doors for one unit | RC-36 |
| 48 | RC-48 | B | Finish the single-unit guide and ready stop point B | RC-39, RC-46, RC-47, RC-29 |
| 49 | RC-49 | C | Write the group document and publish its limits as live facts | RC-48 |
| 50 | RC-50 | C | Run group caps that can only cut, on one ledger | RC-49 |
| 51 | RC-51 | C | Ship the default group rows, the kill line and restart rules | RC-50 |
| 52 | RC-52 | C | Replay several units together and prove the group at 200 | RC-51 |
| 53 | RC-53 | C | Make a pod a recipe, stamped in by a pure function, with drift reported | RC-48 |
| 54 | RC-54 | C | Turn one pod edit into one plan and one click | RC-53, RC-49 |
| 55 | RC-55 | C | Move risk in place, with open trades and logic state untouched | RC-54 |
| 56 | RC-56 | C | Compile stages in, so "at 5,000 the math changes" is a state | RC-55 |
| 57 | RC-57 | C | Seed the pod gallery as ingredients | RC-54 |
| 58 | RC-58 | C | Open the readings bus, with a publisher and a fallback on every read | RC-48 |
| 59 | RC-59 | C | Land pods, presets, blocks and templates from a mini app, and save a block through a door | RC-53 |
| 60 | RC-60 | C | Trace a Library block to a node deploy, and a mini app's reading to a unit | RC-58, RC-59 |
| 61 | RC-61 | C | Let an app read journals and the fold, and raise a card | RC-48 |
| 62 | RC-62 | C | Ship the scripted fleet watch as a mini app and turn off the decay flood | RC-61, RC-51 |
| 63 | RC-63 | C | Report with and without motion, stamp run arms, and reserve the proposal row | RC-25 |
| 64 | RC-64 | C | Keep a unit's record when a placeholder is swapped | RC-55, RC-28 |
| 65 | RC-65 | C | Re-test every deployed unit after a compiler bump | RC-64 |
| 66 | RC-66 | C | Finish the guide and ready stop point C | RC-52, RC-56, RC-57, RC-60, RC-62, RC-63, RC-65 |
| 67 | RC-67 | D | Sign the stop and amend it with a read-back | RC-66 |
| 68 | RC-68 | D | Close part of a position and trail on the node | RC-67 |
| 69 | RC-69 | D | Rest targets at the venue, add entry forms, and set netting per venue | RC-68 |

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

## Make the contract tests honest before a real block lands (RC-01)

Stop A, one unit trades on paper. Slice 0. **What it does.** The contract test holds a hidden half-percent ceiling that fails any real sizer, and its exit test feeds evidence the host refuses. This PR fixes both and enrols Library blocks in the same test, so every later block is judged by a true test.

**Read.** SPINE section 7 K9 tests 4 and 14; SWAP-CHART rows E9, E10, E11.

**Gates and fallbacks.** None.

**Swaps.** E9 E10 E11.

**Depends on.** Nothing beyond the stack root.

**Files.**

- [ ] Edit `qml/tests/test_socket_contracts.py`.
- [ ] Create `qml/tests/test_library_block_enrolment.py`.

**Build.**

- [ ] Replace `_CEILING` (`test_socket_contracts.py:57`) with a contract that reads the block's own declared `fraction` from the evidence the test passes, so 0.02 passes as readily as 0.005.
- [ ] Feed the exit contract only evidence `_Run.exits` really builds (`unit.py:671`), and stop feeding keys the host refuses.
- [ ] Enrol every block in a `component`-shaped fixture folder (`entry.json` and `block.py`; qml's tests hold no Library) in the same parametrized contract as stdlib blocks.

**You see.**

- [ ] Nothing changes for him. A real sizer stops failing a test that was written for a stand-in.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_sizer_at_two_percent_meets_the_contract`. At equity 100000 and stop distance 0.0050 on a EURUSD fixture with `value_per_point` 100000, a fraction of 0.02 answers 4.00 lots and passes. At the parent this fails on the 0.005 ceiling.
- [ ] `test_a_library_sizer_is_enrolled`. A sizer in that fixture folder answering a float fails the contract with the same message a stdlib block gets.
- [ ] `test_the_exit_contract_feeds_only_host_evidence`. The contract's evidence keys equal the keys `_Run.exits` builds on one real bar, compared as a literal set.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run `qml/tests/test_socket_contracts.py` with a planted always-pass sizer that answers 500 lots at equity 100000. Save `check-contract-bites.log`. Pass when the planted sizer fails and the shipped placeholder passes.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses verification-gap, edge-case. The blast-radius fact is this. The shipped placeholder sizer still passes after the ceiling goes, because its own `fraction` is the value the contract now reads.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-01-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Name every refused field, say what each risk module is for, and start the developer guide (RC-02)

Stop A, one unit trades on paper. Slice 0. **What it does.** The census test is proved to bite, so a field nobody runs fails CI. The developer guide starts here as a generated file with a test that fails when it goes stale.

**Read.** AD-20; SPINE section 7 "EXTENDING.md", "Module map"; K9 test 4.

**Gates and fallbacks.** None.

**Depends on.** RC-01.

**Files.**

- [ ] Edit `qml/tests/test_unit_refuses.py`.
- [ ] Create `packages/qmf-risk/MODULES.md`.
- [ ] Create `tools/qml/extending.py`.
- [ ] Create `tools/tests/test_extending.py`.
- [ ] Create `qml/EXTENDING.md`.

**Build.**

- [ ] `_CENSUS` (`test_unit_refuses.py:33`) already holds `Unit.reads` and `NumberSpec.authority`. Prove it fails on an unlisted field. RC-03 adds `stages`, `tags` and `recipe` when those fields exist.
- [ ] Write one sentence per `qmf-risk` module saying whether it belongs to the new risk world or to the wire and accounting.
- [ ] Generate the socket list, refused fields with `_shape_problems` reasons, block answer shapes and journal kinds into `qml/EXTENDING.md`, with the written sections as headings only.

**You see.**

- [ ] A developer has one guide to open. It says today's truth and fails CI when it stops being true.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_the_guide_fails_when_a_field_is_added`. Regenerating with one extra `Unit` field leaves a diff against the checked-in file and the test exits non-zero.
- [ ] `test_every_unit_field_is_run_refused_or_labelled`. `reads` answers the code `reads_not_built`, a literal, and a `Unit` field missing from `_CENSUS` fails the test.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `packages/qmf-risk/tests`, `tools/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run `tools/qml/extending.py --check` at the head and after deleting one line of `qml/EXTENDING.md`. Save `check-guide-stale.log`. Pass when the clean run exits 0 and the edited run exits 1 and names the line.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses verification-gap. The blast-radius fact is this. The generator imports only `qml`, so `tools/tests/test_workspace_structure.py:138` still passes.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-02-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Split a unit into a logic half and a risk half, with a fingerprint each (RC-03)

Stop A, one unit trades on paper. Slice 1. **What it does.** One function partitions the unit document, and anything not named as risk is logic. The compiled unit gains a logic fingerprint and a risk fingerprint, and the compiler moves to format 5.

**Read.** AD-2, AD-19, AD-21; SPINE section 3 "Document additions"; `FIXES.md` S4, S5.

**Gates and fallbacks.** None.

**Depends on.** RC-02.

**Files.**

- [ ] Edit `qml/src/qml/unit/model.py`.
- [ ] Edit `qml/src/qml/unit/qmx.unit.1.schema.json`.
- [ ] Edit `qml/src/qml/unit/parse.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/tests/test_unit_refuses.py`.
- [ ] Edit `qml/tests/test_compile_dummy.py`.
- [ ] Create `qml/src/qml/unit/sections.py`.
- [ ] Create `qml/tests/test_unit_sections.py`.

**Build.**

- [ ] Add the optional fields `modifiers`, `gates`, `tolerations`, `stages`, `risk_locks`, `recipe`, `home_markets`, `tags` to `Unit`, each added to `_CENSUS` and refused by name at compile until its own PR lifts it.
- [ ] Write `sections(document)` with AD-2's rules. A number bound in both is logic. A `reads` row bound by a logic slot is logic. A stage selector with an exit in its `stage_values` is logic. Only `recipe` sits outside both.
- [ ] Compute `compiled_fingerprint = H(logic_fingerprint, risk_fingerprint, format, options)` at `compiler.py:1072-1079`. Set `COMPILER_FORMAT_VERSION` to 5.

**You see.**

- [ ] Nothing changes for him yet. Changing how big a unit trades will no longer re-prove when it enters.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_size_edit_moves_only_the_risk_fingerprint`. Editing `risk_fraction`, the number bound to the sizer's `fraction`, from 0.005 to 0.01 on the dummy leaves `logic_fingerprint` byte-equal and changes `risk_fingerprint`.
- [ ] `test_a_forgotten_field_falls_in_logic`. Each of the nine named fields (`baseline`, `claim_card`, `context_needs`, `family_id`, `lineage`, `plain_python`, `routes`, `title`, `unit_id`) appears in `LogicSection`, a literal list.
- [ ] `test_an_exit_stage_value_makes_the_selector_logic`. A selector with `target_r` in its `stage_values` lands in the logic half.
- [ ] `test_a_new_field_refuses_by_name`. A document declaring `stages` answers `stages_not_built`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Compile the dummy before and after a `risk_fraction` edit and print both fingerprints. Save `check-two-prints.log`. Pass when logic equal, risk different, compiled different.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, structure. The blast-radius fact is this. Every shipped template and fixture compiles at format 5 with its decisions unchanged, by running the dummy through `qml/check/layer_g.py` at the parent and the head.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-03-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Let the node test logic and trust a click for risk (RC-04)

Stop A, one unit trades on paper. Slice 1. **What it does.** A deployment now names both fingerprints, and the G record must cover the logic fingerprint only. A held position is keyed by the logic fingerprint, so a risk-only recompile no longer silences its exits.

**Read.** AD-3; `round-2/arch/COMPARE.md` finding F4, F5.

**Gates and fallbacks.** None.

**Depends on.** RC-03.

**Files.**

- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/promote.py`.
- [ ] Create `qml/tests/test_logic_fingerprint_keeps_exits.py`.
- [ ] Create `qmn/tests/test_app_deploy_two_fingerprints.py`.

**Build.**

- [ ] Make `opened_by` (`unit.py:672-674`) the logic fingerprint.
- [ ] Make `_g_record` and the node's gate (`runtime.py:2756`) ask for the logic fingerprint, and record the risk fingerprint and its click on the deployment.
- [ ] Refuse any host swap of a different compiled fingerprint over a held trade, except through a later `move_risk` or a drain.

**You see.**

- [ ] Nothing on a screen. A size edit will not cost a re-test of when the unit trades.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_exits_fire_after_a_risk_only_recompile`. COMPARE's probe inverted. A held position with a time exit reads 1 exit intent over 60 bars after a `risk_fraction` recompile. At the parent it reads 0.
- [ ] `test_a_logic_edit_needs_a_new_g_record`. A deployment whose logic fingerprint has no G record is refused with the name `g_record_missing`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmn/tests -k app`, `qmx-agents/packages/qmx-host/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Promote the dummy on the fake broker, recompile with a new `risk_fraction`, and drive 60 bars. Save `check-exits-survive.log`. Pass when one exit intent fires and the journal names the logic fingerprint.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. A size-only edit moves today's compiled fingerprint and leaves the new logic fingerprint equal, run on the real compiler.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-04-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Give sizers a typed amount and one converter that knows the account's currency (RC-05)

Stop A, one unit trades on paper. Slice 2. **What it does.** A sizer now answers an amount in money at risk, notional or quantity, and one pure function spells the venue's quantity with an exchange rate. This is where lots stop being a design word.

**Read.** AD-10, AD-15, AD-21; SPINE section 3 "Sizer, modifiers, converter"; `CHECK.md` B5.

**Gates and fallbacks.** None.

**Swaps.** PH12 PH30.

**Depends on.** RC-02.

**Files.**

- [ ] Edit `qml/src/qml/blocks/api.py`.
- [ ] Edit `qml/src/qml/numbers/convert.py`.
- [ ] Edit `qml/src/qml/numbers/records.py`.
- [ ] Edit `qml/src/qml/numbers/__init__.py`.
- [ ] Create `packages/qmf-risk/src/qmf/risk/facts.py`.
- [ ] Create `packages/qmf-risk/tests/test_facts.py`.
- [ ] Create `qml/tests/test_convert_currency.py`.

**Build.**

- [ ] Add `Amount`, `Skip` and `Factor` to `blocks/api.py`. Today's `Size(lots)` reads as `Amount(quantity)` and skips the converter.
- [ ] Add `Fact(value, ts, fail_mode, source, state)` to `qmf/risk/facts.py`, with no import above `qmf-core`.
- [ ] Add `to_quantity(amount, entry, stop_or_basis, record, rate, rule)` returning `Converted(quantity, residue_r, skipped)`, and `conversions` with `ConversionRef(market_id, invert)` on `InstrumentRecord`.

**You see.**

- [ ] Nothing on a screen. The answer to "why lots?" becomes true in code. Lots exist in one function.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_loss_at_the_stop_equals_the_amount_on_four_markets`. At 500 money at risk in USD. EURUSD entry 1.1000 stop 1.0950 with `value_per_point` 100000 and rate 1 gives 1.00 lots. XAUUSD entry 2000 stop 1995 with `value_per_point` 100 gives 1.00 lots. USDJPY entry 150.00 stop 149.50 with `value_per_point` 100000 and rate 1/150 gives 1.50 lots. EURJPY entry 160.00 stop 159.50 through USDJPY inverted at 150 gives 1.50 lots.
- [ ] `test_a_stale_rate_skips_by_name`. A rate past `rate_stale_s` answers `skipped == "rate_stale"` and an absent one `"rate_absent"`, with quantity None.
- [ ] `test_rounding_goes_down_and_the_residue_is_real`. 1.237 lots at step 0.01 gives 1.23 and a residue above zero in R.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `packages/qmf-risk/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the shipped sizer at the parent on USDJPY and the converter at the head on the same inputs. Save `check-jpy-fault.log`. Pass when the parent loses 500 JPY at the stop and the head loses 500 USD.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Microseconds per `to_quantity` call, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, verification-gap. The blast-radius fact is this. `Size(lots)` still answers the same quantity through every existing caller, so the shipped placeholder keeps trading until RC-06.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-05-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Ship the sizer that answers money, catch absurd sizes, and make pricing its own call (RC-06)

Stop A, one unit trades on paper. Slice 2. **What it does.** `fixed-fraction-at-stop@2` answers money at risk and reads its fraction from evidence, and `HostedUnit.price` becomes the one call that sizes an entry. A 5,000-lot answer is now caught by a size band.

**Read.** AD-1, AD-10, AD-14 step 3; SWAP-CHART rows 1, E8.

**Gates and fallbacks.** None.

**Swaps.** PH1 E8.

**Depends on.** RC-04, RC-05.

**Files.**

- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/check/layer_g.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qml/src/qml/unit/templates/dummy-trend-pullback.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/fixed-fraction-at-stop/2/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/fixed-fraction-at-stop/2/entry.json`.
- [ ] Create `qml/tests/test_price_call.py`.

**Build.**

- [ ] Write `@2`. It reads `fraction` from `evidence` on every call, answers `Amount(money_at_risk)`, and keeps `make` only as the seed.
- [ ] Add `HostedUnit.price(proposal, facts, admit)`. The host calls it straight after the unit's exits went out, at `runtime.py:1727-1733`, until RC-42 moves the call site. `layer_g.py` calls it the same way.
- [ ] Check the slot's face at compile with `output: amount`. Apply the size band and per-trade cap in one row, after the converter.
- [ ] Point the dummy template at `@2`. `@1` stays only as an old row.

**You see.**

- [ ] Nothing on a screen. A sizer that says 5,000 lots is refused and says why.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_the_band_catches_5000_lots`. A sizer answering `Amount(quantity, 5000)` at a band maximum of 100 answers a skip with the code `size_band`, and no intent is minted.
- [ ] `test_the_sizer_reads_a_moved_fraction`. `update` with `fraction` 0.0049 in evidence at equity 100000 answers `Amount(money_at_risk, 490)`, though `make` got 0.005.
- [ ] `test_account_facts_never_reach_the_exit_pass`. `on_instant` on a unit with an open position reads no `equity` key, by a recording facts surface, literal empty set.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the dummy through QMB on synthetic bars at the parent and the head on a USD market. Save `check-same-size.log`. Pass when quantities equal on every trade for EURUSD.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. With a quote currency equal to the account's, `@2` through the converter gives the same quantity as `@1`, run over 50 entries on real bars from the fixture.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-06-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Bring the exchange rate to both hosts, and convert every money figure at the seam (RC-07)

Stop A, one unit trades on paper. Slice 2. **What it does.** QMB and the node each supply `market.rate:<quote>` as a fact, subscribing conversion markets without driving the unit on them. Row money keeps the quote figure and the rate used, and the account sums in its own currency.

**Read.** AD-10 "Currency"; AD-15; SPINE section 3 consistency "Money"; K9 test 16.

**Gates and fallbacks.** None.

**Depends on.** RC-06.

**Files.**

- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/src/qmn/app/feed_keeper.py`.
- [ ] Edit `qmb/src/qmb/host/behaviour.py`.
- [ ] Create `qmb/src/qmb/host/facts.py`.
- [ ] Create `qmn/src/qmn/app/facts.py`.
- [ ] Create `qmb/tests/test_rate_fact.py`.
- [ ] Create `qmn/tests/test_app_rate_fact.py`.

**Build.**

- [ ] Add both adapters with the same `provided` list. Replay reads the conversion market's bars. A backtest missing them skips by the same name and says so on its run stamp.
- [ ] Subscribe each market named in `conversions` beside the traded ones on the node, and never drive the unit on it.
- [ ] Stamp the last rate and its age on the row from `_money` (`unit_handler.py:216-220`). Convert in `_account()` (`:370`). A close never reads the rate.

**You see.**

- [ ] A unit trading USDJPY now risks what it says in dollars.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_k9_16_currency`. On QMB and on the fake broker, the four markets of RC-05 lose 500 USD at the stop from equity 100000 and fraction 0.005, and the two hosts' quantities are equal.
- [ ] `test_a_stale_rate_never_stops_an_exit`. With the USDJPY rate stale, an entry skips with `rate_stale` and a held position's time exit still closes in the same step.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmb/tests -k unit`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Trade USDJPY on the fake broker with the rate feed stopped mid-run. Save `check-stale-rate.log`. Pass when entries skip by name, the held trade closes, and no unit stops.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. A held position's close path reads no rate, by a surface that raises on `market.rate` during `exits`, run on the real step.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-07-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Write one decision row before every send, and explain any size from it (RC-08)

Stop A, one unit trades on paper. Slice 2. **What it does.** The decision row gains every input it used and is written once, before the order leaves. `explain_size` prints the trail and `replay_decision` re-runs the sizer on the stored inputs and must match.

**Read.** AD-9 "One row", AD-18; K9 tests 1 and 13; SPINE section 7 "Debugging one size".

**Gates and fallbacks.** None.

**Swaps.** PH29.

**Depends on.** RC-07.

**Files.**

- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`.
- [ ] Edit `qmb/src/qmb/results/journal.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Create `qml/src/qml/receipt.py`.
- [ ] Create `qml/tests/test_receipt.py`.
- [ ] Create `qml/tests/conformance_tape/README.md`.
- [ ] Create `qmn/tests/test_conformance_tape.py`.

**Build.**

- [ ] Add `numbers_in_force`, `inputs`, `steps`, `verdicts`, `binding`, `logic_fp`, `risk_fp`, `placeholders` and `written_before_send` to `DecisionRow` (`unit.py:153`). Hosts journal it, and `qml` never imports `qmf-data`.
- [ ] Write `explain_size(row)` and `replay_decision(row)` over plain mappings in `qml/receipt.py`.
- [ ] Record one conformance tape (proposals and facts) and run it through QMB and the node with an identical trail required.

**You see.**

- [ ] Any trade can answer "why this size?" from one row.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_replay_equals_the_row`. On a stored row with fraction 0.005, equity 100000, EURUSD stop distance 0.0050, `replay_decision` returns 1.00 lots and the literal row hash.
- [ ] `test_the_row_is_written_before_the_send`. A fake broker that raises on send leaves one row with `written_before_send` true and no order.
- [ ] `test_k9_1_and_13_same_trail_in_both_hosts`. The tape through QMB and the node gives equal trails, with only fills, costs and latency allowed to differ.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `packages/qmf-data/tests`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Print `explain_size` for one fake-broker trade. Save `check-size-trail.log`. Pass when every fact shows age and source, and the printed quantity equals the sent quantity.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses verification-gap, edge-case. The blast-radius fact is this. `qml` still imports nothing from `qmf-data`, by `tools/tests/test_workspace_structure.py:138`.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-08-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Keep a raising block from reaching the exits in its own unit (RC-09)

Stop A, one unit trades on paper. Slice 3. **What it does.** `_Run.step` runs update, exits, entries and motion as separate phases, and a raise becomes a `Fault` on the answer. That market takes no entry on this bar and its exit intents survive.

**Read.** AD-23 steps 1 and 3; SPINE section 3 "Controls" `Fault`; `CHECK.md` B1.

**Gates and fallbacks.** None.

**Depends on.** RC-08.

**Files.**

- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`.
- [ ] Edit `packages/qmf-risk/src/qmf/risk/journal.py`.
- [ ] Create `qml/tests/test_fault_wall_unit.py`.

**Build.**

- [ ] Split `_Run.step` (`unit.py:509`, today's order at `:530-536`) into phases. A raise in `update`, `entries`, `motion` or `price` adds `Fault(block, phase, code)` to `UnitStep.faults`.
- [ ] Add the `risk_event` kind with the first code `unit_fault` and a root-cause key.
- [ ] Turn that unit's entries off inside `HostedUnit`, so both hosts behave alike, and bring them back after `fault_clean_bars` clean bars, a labelled placeholder.

**You see.**

- [ ] A broken block now costs that unit its new entries, and its open trades still close.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_raising_logic_slot_leaves_exits_running`. A logic slot that raises on every bar, a held position and a time exit at 5 bars. The exit intent fires on bar 5 and `faults` holds one row per bar with `phase == "update"`.
- [ ] `test_a_raising_sizer_mints_nothing_and_stops_nothing`. A sizer that raises gives zero entry intents and one `Fault` with `phase == "price"`.
- [ ] `test_entries_come_back_after_clean_bars`. With `fault_clean_bars` set to 3 in the fixture, entries resume on the fourth clean bar.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `packages/qmf-data/tests`, `packages/qmf-risk/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run a raising logic block through QMB for 100 bars. Save `check-fault-qmb.log`. Pass when the run finishes, exits fire, and the journal holds `unit_fault` rows.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. Exit blocks hold their own instances, so a broken logic block can't corrupt them, by running the exit after 50 logic raises and comparing its state to a clean run.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-09-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Keep one unit's fault from stopping any other unit (RC-10)

Stop A, one unit trades on paper. Slice 3. **What it does.** `_drive` holds one `try` per unit, and a fault no longer stops the driver or the phase. The host's new `close_scope` port is the last fall-through when a held position's exits cannot run at all.

**Read.** AD-13, AD-23 steps 2 and 4; `CHECK.md` B1, S10.

**Gates and fallbacks.** None.

**Depends on.** RC-09.

**Files.**

- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Create `qmn/tests/test_app_fault_wall.py`.

**Build.**

- [ ] Wrap each unit in `_drive` (`runtime.py:3013-3018`). A raise past `_Run.step` is a `Fault` for that unit, and the next one runs.
- [ ] Treat a `close_frontier` refusal caused by a fault as a `Fault`, not `Phase.STOPPED` (`:3040-3046`). The phase stays `TRADING`, and `step()`'s heal stays for what is outside `_drive`.
- [ ] Add `HostPort.close_scope(unit, why)`. On the node it calls `_close_scope`, and in QMB it closes at the next bar's open. It fires after `exit_fault_bars` bars with no exit able to run, a labelled placeholder.

**You see.**

- [ ] One bad unit out of two hundred stays one card, and the other 199 never notice.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_k9_2_one_units_raise_stops_no_exit_and_no_other_unit`. One logic slot raises on `dep-1`, one sizer raises on `dep-3`, `dep-2` and `dep-4` hosted behind them, 12 bars on the fake broker. All four are driven the same number of times, heals read 0, `dep-1`'s time exit fires, `dep-2`'s per-bar exit and node-closed target fire, `dep-1` mints no entry, and one `unit_fault` row and one card exist per root-cause key. At the parent `dep-2` is driven 0 times with 11 heals.
- [ ] `test_close_scope_is_the_last_fall_through`. With every exit raising for `exit_fault_bars` bars, the position closes through the port with the reason `exit_fault`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run K9 2's scene at the parent and the head and print the drive counts. Save `check-drive-counts.log`. Pass when parent shows `dep-2` at 0 and head shows every unit equal.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. Zero heals over the 12 bars, read from the real `Runtime` on the fake broker, not from a stub.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-10-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Run every exit each bar, side-correct, with reasons and a fixed order (RC-11)

Stop A, one unit trades on paper. Slice 3. **What it does.** Every exit in `exit_set` now runs per bar on `PositionFacts`, reads the quote that closes it, and answers a typed action with a reason code. Full beats partial beats amend, and a raising exit is skipped for the next.

**Read.** AD-13 step 2, AD-9 "Import test"; SPINE section 3 "Exits"; SWAP-CHART rows 9, 10, E15; `CHECK.md` S15.

**Gates and fallbacks.** None. Amends and partials answer here and stay unexecuted until RC-67 and RC-68.

**Swaps.** PH9 PH10 E15.

**Depends on.** RC-10.

**Files.**

- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qml/src/qml/blocks/api.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Create `qml/src/qml/protocol/exits.py`.
- [ ] Create `qml/tests/test_exit_stack.py`.
- [ ] Create `qml/tests/test_exit_imports.py`.

**Build.**

- [ ] Add `PositionFacts`, `ExitAction` and the widened `ExitInstance.update` whose evidence carries `clock` as a field.
- [ ] Feed a long the bid bars and a short the ask bars (`unit.py:574-576`). Pass the side at `timer()` (`:450`).
- [ ] Lift `exit_not_built` for a second per-bar exit. Bump the compiler format, because side-correct bars change a decision.
- [ ] Add the import test, parsing `protocol/exits.py` to prove it imports nothing from `entry_chain`, `node_chain`, `fold` or the readings feed.

**You see.**

- [ ] A short's stop now feels the spread, and every close says why it closed.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_k9_3_exit_code_cannot_import_the_chain`. The parsed import list of `exits.py` shares no name with the four forbidden modules. A planted import fails it.
- [ ] `test_a_short_reads_ask_bars`. `swing-stop-buffer` on a short with zero buffer, on bars whose confirmed swing high is 1.0995 on the bid and 1.1002 on the ask, answers a stop of 1.1002. At the parent it answers 1.0995, because `unit.py:574-576` feeds it bid bars. The fills already read the closing side (`fill.py:1306`), so the fault is the level.
- [ ] `test_full_beats_partial_beats_amend`. Three exits answering on one bar give one `close_full` with the first full exit's reason code.
- [ ] `test_a_raising_exit_falls_to_the_next`. Stack of a raising exit and a time exit. The time exit closes and one `Fault` has `phase == "exit"`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Print a short's stop level on bars with a 2-pip spread at the parent and the head. Save `check-short-spread.log`. Pass when the head's level sits on the ask swing high and the parent's on the bid's.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. A second per-bar exit never changes a unit with one exit, by comparing decisions on the dummy across the bump.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-11-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Make the shipped exit blocks read numbers from evidence (RC-12)

Stop A, one unit trades on paper. Slice 3. **What it does.** The stop, target and time-exit blocks ignored a moved number because they held the `make` value. New versions read from evidence, and six shipped exits now compile side by side.

**Read.** AD-13, AD-14 step 3; SWAP-CHART rows 2, 3, 4; `CHECK.md` "Does a number really move".

**Gates and fallbacks.** None. These are stdlib blocks, so they bump the money app. The stop point's release carries the signature.

**Swaps.** PH2 PH3 PH4.

**Depends on.** RC-11.

**Files.**

- [ ] Edit `qml/src/qml/unit/templates/dummy-trend-pullback.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/swing-stop-buffer/2/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/swing-stop-buffer/2/entry.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/target-r-multiple/2/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/target-r-multiple/2/entry.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/time-exit-bars/2/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/time-exit-bars/2/entry.json`.
- [ ] Create `qml/tests/test_exit_blocks_v2.py`.

**Build.**

- [ ] Write the three `@2` blocks. Each reads its number from `evidence`, keeps the old value only as a seed, and answers its own reason code, `stop`, `target` or `time`.
- [ ] Point the dummy at the new versions. Keep `@1` as old rows.

**You see.**

- [ ] Nothing on a screen. A learned number can now reach an exit when that lands.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_target_reads_a_moved_multiple`. Entry 1.1000, stop 1.0950, `multiple` 1.9 in evidence answers 1.1095. Seeded 2.0 with nothing moved answers 1.1100.
- [ ] `test_time_exit_answers_its_own_reason`. At bar 48 of a short the block answers `close_full` with `reason_code == "time"`.
- [ ] `test_six_exits_compile_on_one_unit`. A fixture stack with `offset-gated-trailing-stop`, `profit-fraction-trailing-stop`, `peak-holdings-giveback-exit`, `roi-table-exit`, `stepped-profit-stop` and `time-exit-bars@2` compiles.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Backtest the dummy on the same synthetic months at the parent and the head. Save `check-exits-same.log`. Pass when every trade's exit price and reason agree except short time exits, which the log lists.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses verification-gap, edge-case. The blast-radius fact is this. Nothing but the dummy template binds the old versions in shipped files, by a repo-wide grep whose output is pasted.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-12-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Make a brake a control row that runs in the unit (RC-13)

Stop A, one unit trades on paper. Slice 4. **What it does.** `halts` becomes a list of control rows with what they read, their scope, verb, what they do when they fire, how they come back and what they do before they have data. The runner feeds each its facts, and the unit's own statistics are computed in QML so both hosts agree.

**Read.** AD-12, AD-15, AD-9 "plain try"; SPINE section 3 "Controls"; SWAP-CHART row 5.

**Gates and fallbacks.** None.

**Swaps.** PH5.

**Depends on.** RC-10.

**Files.**

- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qml/src/qml/unit/model.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/blocks/api.py`.
- [ ] Create `packages/qmf-risk/src/qmf/risk/controls.py`.
- [ ] Create `packages/qmf-risk/tests/test_controls.py`.
- [ ] Create `qml/src/qml/protocol/controls.py`.
- [ ] Create `qml/tests/test_control_rows.py`.

**Build.**

- [ ] Add `ControlRow`, `Verb`, `OnFire`, `Restore`, `ColdRule` and `Answer` to `qmf/risk/controls.py`. `Halt.action` gains `reduce`.
- [ ] Write the runner. A plain `try` around each row, so a raise writes `link_fault` and stands that row's scope down, and never reaches an exit.
- [ ] Compute `own.session_loss_r`, `own.loss_streak`, `own.losing_day_streak`, `own.session_fills` from the unit's own journal inside QML.
- [ ] Lift `halts` at compile.

**You see.**

- [ ] Brakes stop being custom code. A new one is one folder and one row.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_session_loss_halt_binds_at_its_limit`. `session-loss-limit-halt` with limit 2R after trades of -1R and -1R answers `no_new_entries`, and after -1R alone answers none.
- [ ] `test_a_raising_row_stops_no_exit`. A control row that raises leaves the held position's time exit firing and writes `link_fault`.
- [ ] `test_a_row_in_shadow_never_refuses`. A shadow row that fires leaves the entry placed and records `would_fire` true.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `packages/qmf-risk/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run all five shipped halts through QMB on a fixture with a losing run. Save `check-five-halts.log`. Pass when each fires on the literal trade the fixture names, and the run finishes.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, structure. The blast-radius fact is this. The five shipped halts bind with no edit to their `entry.json`, by compiling a unit with each.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-13-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Read every brake's state from one fold (RC-14)

Stop A, one unit trades on paper. Slice 4. **What it does.** One pure function folds journal rows into a risk state per scope, including the words ACTIVE, REDUCING, BENCHED, HALTED and RESTORE. The snapshot only caches it, so a restart loses nothing and copies nothing.

**Read.** AD-12, AD-18; SPINE section 3 "Status and records"; K9 test 9; `CHECK.md` B7.

**Gates and fallbacks.** None. Account halts read today's node facts and are labelled one-unit until RC-29.

**Depends on.** RC-13.

**Files.**

- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `packages/qmf-risk/src/qmf/risk/controls.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Create `qml/src/qml/fold.py`.
- [ ] Create `qml/tests/test_fold.py`.

**Build.**

- [ ] Write `fold(rows, scope, clock) -> RiskState` over plain mappings at unit scope, with UNKNOWN when a needed input is stale.
- [ ] Keep the fold incrementally on the node, and cache it in the snapshot. Rebuild on restart from rows.

**You see.**

- [ ] Asked "what state is this unit in?", every reader gives the same answer.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_k9_9_one_fold_in_every_reader`. The same 40 rows give an equal `RiskState` through the node's incremental path, a cold fold and the QMB reader, word `BENCHED`, reason `session-loss-limit-halt`.
- [ ] `test_restart_keeps_a_bench_from_rows`. Deleting the snapshot and folding the journal gives `BENCHED` with the same `since`.
- [ ] `test_a_stale_input_reads_unknown`. A needed fact past its limit answers the word `UNKNOWN`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `packages/qmf-risk/tests`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Restart the fake-broker node with one benched unit and its snapshot removed. Save `check-bench-restart.log`. Pass when the unit stays benched and takes no entry.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, verification-gap. The blast-radius fact is this. `fold` imports no host and no `qmf-data`, by the workspace test and a parsed import list.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-14-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Write risk events and would-have rows in both hosts (RC-15)

Stop A, one unit trades on paper. Slice 4. **What it does.** Every control that fires writes a `risk_event`, and every shadowed or refused entry writes a `would_have`. These are the evidence the brakes and methodology read later.

**Read.** AD-12; FUNNEL row R4; SWAP-CHART rows 25, 29.

**Gates and fallbacks.** None.

**Swaps.** PH25 PH29.

**Depends on.** RC-14.

**Files.**

- [ ] Edit `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`.
- [ ] Edit `qmb/src/qmb/results/journal.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Edit `qmn/src/qmn/journal_dispatch.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/tests/test_journal_reason_census.py`.
- [ ] Create `qmb/tests/test_risk_event_rows.py`.

**Build.**

- [ ] Add writers for `risk_event` with root-cause key, event id and alert fields, and `would_have` with `propensity`, in QMB and on the node.
- [ ] Give user blocks their own appendable reason-code family, and enrol the codes in the census.

**You see.**

- [ ] When a brake fires, the record says which, why and what would have happened.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_shadow_row_writes_would_have`. A shadow halt that fires on trade 3 gives one `would_have` row whose literal fields name the row id and the entry it would have refused.
- [ ] `test_a_new_text_without_a_code_fails_qmb`. A block reason with no code fails the QMB run and files as `unlisted` on the node.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `packages/qmf-data/tests`, `qmb/tests -k unit`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the five-halt fixture through QMB and the fake broker. Save `check-rows-agree.log`. Pass when the two journals hold the same `risk_event` codes in the same order.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses verification-gap. The blast-radius fact is this. The census test still reads every shipped reason text after the new family lands.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-15-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Let a brake flatten, stop and send to paper, with a person only where it says so (RC-16)

Stop A, one unit trades on paper. Slice 4. **What it does.** A control row that waits for a hand now calls `Runtime.risk_stop`, its first producer, and `flatten` mints exits through the unit's own exit path. A restore rule may send a member to paper.

**Read.** AD-12; SWAP-CHART rows 23, 24; `qml/lifecycle/machine.py`.

**Gates and fallbacks.** None.

**Swaps.** PH5 PH23 PH24.

**Depends on.** RC-15.

**Files.**

- [ ] Edit `qml/src/qml/protocol/controls.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qml/src/qml/lifecycle/machine.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Create `qmn/tests/test_app_control_verbs.py`.

**Build.**

- [ ] Wire `wait for hand` to `risk_stop` (`runtime.py:2696`). Only that row and the kill switch wait for a person.
- [ ] Execute `flatten` through the exit path. Add the lifecycle row for a rule sending a unit to paper.

**You see.**

- [ ] A brake can now close its own trades. Only the two things that say so wait for you.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_flatten_closes_through_the_exit_path`. A row with verb `flatten` on two held positions gives two exit intents with reason `control_flatten` in the same step.
- [ ] `test_reduce_factor_halves_the_next_entry`. Verb `reduce(0.5)` at 500 money at risk on EURUSD with stop distance 0.0050 gives 0.50 lots.
- [ ] `test_only_a_hand_lifts_a_hand_row`. After a hand row fires, a restore rule answers no change, and `resume` by his route clears it.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run a flatten row and a lockout on the fake broker through a restart. Save `check-verbs-restart.log`. Pass when positions closed, lockout still in force, exits never refused.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. The kill switch still lowers only by his hand, by the shipped `test_app_every_way_out.py` passing unchanged.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-16-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Ship the canary template and the records it needs (RC-17)

Stop A, one unit trades on paper. Slice 5. **What it does.** `canary` is a whole unit document with no brakes, labelled so in the largest type, reading 15-minute bars. Instrument records ship with it so a first run needs no broker.

**Read.** SPINE section 6 steps 1 and 2; FUNNEL 4.2 Template C; OPEN row 12; `E5` flaw 12.

**Gates and fallbacks.** If `unit_check` can't accept a shipped record (OPEN row 12), add a core row here and say so in the PR body.

**Depends on.** RC-16, RC-12.

**Files.**

- [ ] Edit `qml/src/qml/numbers/records.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/unit_check.py`.
- [ ] Create `qml/src/qml/unit/templates/canary.json`.
- [ ] Create `qml/src/qml/numbers/shipped_records.json`.
- [ ] Create `qmx-agents/packages/qmx-tools/tests/test_template_canary.py`.
- [ ] Create `qmx-agents/apps/qmb/tests/test_practice_month.py`.
- [ ] Create `qml/tests/test_canary_motion.py`.
- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/practice_start.py`.
- [ ] Create `qmn/src/qmn/app/practice_bars/README.md`.

**Build.**

- [ ] Write `canary` with the dummy's logic and number names, `fixed-fraction-at-stop@2`, the three `@2` exits, one position, the kill switch only, and `origin: placeholder` on every number with a range and a reason.
- [ ] Keep `min_trend_strength` on `trend-floor-from-record@2` with motion on, so one filter number moves by the built engine from stop A. Size and exit numbers stay fixed until RC-25.
- [ ] Ship the synthetic month now held only in `qml/tests/fixtures/slices` under `practice_bars/`, saved under dukascopy-node's names as `test_qmb_app.py` does. `practice_start.py` copies it into an empty market store as source `practice` and lands the shipped instrument records on `main`, which promote reads. Today a missing month is refused by name (`test_qmb_app.py:424`), so without this nothing can test from zero.
- [ ] Ship records for its markets labelled `source: shipped`, including their `conversions`. Let `unit_new` list every JSON in the templates folder.

**You see.**

- [ ] A new person, or the copilot through `unit_new`, can pick a template that works, and it says plainly it is a shape and has no brakes.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_canary_compiles_from_nothing`. `unit_new("canary", {})` then `unit_check` on an empty store answers no problem, with warnings naming "no brakes" and every number labelled.
- [ ] `test_a_new_template_is_one_json`. Dropping a second JSON in the folder lists 3 templates with no other edit.
- [ ] `test_a_backtest_finds_bars_from_an_empty_store`. After `practice_start`, `backtest_run` with `source: practice` finishes and a G record with `safety_passed` exists for the logic fingerprint.
- [ ] `test_canary_moves_its_filter_number`. After 20 scripted closed trades on the hosted unit, `min_trend_strength` reads 0.0001, from 0, with one calibration row.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmx-agents/packages/qmx-tools/tests`, `qmx-agents/apps/qmb/tests`, `qmx-agents/packages/qmx-host/tests`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. From an empty throwaway QMX folder, run `practice_start`, `unit_new`, `unit_check` and `backtest_run` with `source: practice` for `canary`. Save `check-canary-backtest.log`. Pass when the backtest finishes with a stamped run and a G record for the logic fingerprint.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses verification-gap, structure. The blast-radius fact is this. `unit_check` reads a shipped record through the same path as a Library record, by a recording store.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-17-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Let a draft reach paper on his click, with the safety half of G (RC-18)

Stop A, one unit trades on paper. Slice 5. **What it does.** The lifecycle gains one row from draft to paper by his click, with G's safety half required and no judge pass. His click's protected fields and channel isolation get their tests.

**Read.** AD-20, AD-24; FUNNEL row K5, R8; `CHECK.md` B3; K9 test 8.

**Gates and fallbacks.** The judge keeps its meaning. A `fail` staying parked is methodology's question, default kept.

**Depends on.** RC-17.

**Files.**

- [ ] Edit `qml/src/qml/lifecycle/machine.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/promote.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/lifecycle.py`.
- [ ] Edit `tools/first_real_start.py`.
- [ ] Edit `tools/tests/test_first_real_start.py`.
- [ ] Edit `qml/tests/test_lifecycle.py`.
- [ ] Edit `qmb/src/qmb/results/journal.py`.
- [ ] Edit `tools/money_path_scan.py`.
- [ ] Create `qmx-agents/packages/qmx-tools/tests/test_no_agent_money_door.py`.

**Build.**

- [ ] Add `Transition(DRAFT, PAPER, HIS_CLICK)` at `machine.py:105-117`. Keep `_admit`'s demand for a G record with `safety_passed` (`promote.py:376, 565-578`).
- [ ] Change `first_real_start.py`'s header (`:8`), which says a unit reaches a node by passing the judge.
- [ ] Add the protected field list (floor, kill level, `never_self_tune`, plan hash) with no agent write path, and a test that no channel an agent reads carries the promote door.
- [ ] Stamp every run with `group: none`, quote source, gate settings, costs and real-tick share.

**You see.**

- [ ] Your click takes a template to paper with no months of proof first. Live stays your click too, with placeholders shown.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_draft_reaches_paper_on_his_click`. A fold of `DRAFT -> PAPER` by `HIS_CLICK` with a safety-passed G record answers state `PAPER`. At the parent it answers `not_in_table`.
- [ ] `test_no_g_record_no_paper`. The same click with no G record is refused with `g_record_missing`.
- [ ] `test_k9_8_no_agent_path_to_money`. The tool table has no row reaching promote, kill-level lowering, the floor or the plan hash, a literal empty intersection.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmx-agents/packages/qmx-host/tests`, `tools/tests`, `qmx-agents/packages/qmx-tools/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the real promote on a throwaway home for `canary` with no judge run. Save `check-promote-paper.log`. Pass when the deployment is written with lane `paper` and both fingerprints.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. `PAPER -> LIVE` still refuses unacknowledged placeholders, by `promote.py:390-395` with the shipped test passing.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-18-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Reach a first filled paper entry from zero, on a practice venue (RC-19)

Stop A, one unit trades on paper. Slice 5. **What it does.** A `practice` venue kind replays shipped synthetic bars over the conformance account, with no broker and no sign-in. K7 walks from an empty store to a filled paper entry and runs in CI, and this PR is stop point A.

**Read.** SPINE section 6 steps 3 to 6 and "Day one for a stranger"; `FIXES.md` S8; K9 test 7; `CHECK.md` walk 1.

**Gates and fallbacks.** Fallback if practice can't bind through the promote path, K7 ends on the fake broker and the PR body says the stranger path is short by that.

**Depends on.** RC-18.

**Files.**

- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/src/qmn/app/paper_lane.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/venue_records.py`.
- [ ] Create `qmn/src/qmn/app/practice.py`.
- [ ] Create `qmx-agents/packages/qmx-host/tests/k7_rehearsal.py`.
- [ ] Create `qmx-agents/packages/qmx-host/tests/test_k7_rehearsal.py`.

**Build.**

- [ ] Add the production builder over `ConformanceAccount` (`runtime.py:698`) and a feed replaying shipped bars, world `paper`, kind `practice`, stated in every card and row.
- [ ] Land one `account` with world `paper` and one `venue` row on `main` through `venue_records`, because promote refuses without them (`promote.py:378`).
- [ ] Write K7 as a script a test runs, in the `qmx-agents` env, the only one holding `qmx_tools`, `qmx_host`, `qmn` and `qmb` together. Its steps are `practice_start`, `unit_new`, check, backtest, click, stage, warm up, first signal, row, fill.

**You see.**

- [ ] Stop point A. A person with no broker picks `canary`, clicks once, and watches one filled paper trade, labelled practice.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_k9_7_canary_reaches_a_filled_paper_entry`. From an empty store with no judge run, K7 ends with 1 fill, 1 decision row written before the send, and the row's quantity equal to the fill's.
- [ ] `test_practice_says_it_is_practice`. Every row and card from this venue carries `world == "paper"` and `venue_kind == "practice"`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, `qmx-agents/packages/qmx-host/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run `qmx-agents/packages/qmx-host/tests/k7_rehearsal.py` on a fresh throwaway home. Save `check-k7.log`. Pass when it prints PASS for each step and ends with one filled entry.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Seconds for K7 end to end, recorded as the program's first baseline.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, verification-gap. The blast-radius fact is this. The practice venue can't reach a network, by running K7 with sockets refused.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-19-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Ready stop point A for his signature (RC-20)

Stop A, one unit trades on paper. Slice 5. **What it does.** QML changes reach the trading node's lock, so the money app needs a new version for him to sign. This PR moves the version rows once, lists what is in the release in plain words, and runs the whole-repo check.

**Read.** AD-19, SPINE section 10 "His signature"; `FIXES.md` S17; OPEN row 8a.

**Gates and fallbacks.** G-SIGN. Nothing in the build waits for the signature. A stop point isn't reached until he has signed.

**Depends on.** RC-19.

**Files.**

- [ ] Edit `qmx-agents/apps/trading-node/app.toml`.
- [ ] Edit `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py`.
- [ ] Create `tools/lanes/release_note_stop_a.md`.

**Build.**

- [ ] Bump `trading-node` and any other app whose folder or lock moved, with its measured digest in `test_shipped_apps.py`.
- [ ] Write the plain note. What now works, what is placeholder, what his signature covers.

**You see.**

- [ ] One line to sign, and a plain list of what it covers.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_shipped_apps.py` passes with the new version row and its measured digest, compared by the test's own `folder_digest`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmx-agents/apps/trading-node/tests`, `qmx-agents/packages/qmx-apps/tests`, `tools/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the whole-repo check at the head with `risk-ship/tools/run_tests.sh`. Save `check-whole-a.log`. Pass when nothing fails beyond the named baseline reds.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses verification-gap. The blast-radius fact is this. No agent or tool can sign, by a repo grep for `publish_signed` callers.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-20-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Give size its named modifiers (RC-21)

Stop B, the whole single-unit baseline. Slice 6. **What it does.** `modifiers` runs as an ordered list on the risk half, each answering a factor inside a declared range with a reason on the receipt. The level is one named modifier with no ladder law, and a modifier may raise.

**Read.** AD-11; SPINE section 3 `ModifierInstance`; SWAP-CHART row E2; FUNNEL row S2.

**Gates and fallbacks.** None.

**Swaps.** E2.

**Depends on.** RC-08.

**Files.**

- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/blocks/api.py`.
- [ ] Edit `qml/src/qml/receipt.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/level-factor/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/level-factor/1/entry.json`.
- [ ] Create `qml/tests/test_modifiers.py`.

**Build.**

- [ ] Run the `sizing_modifier` role in `price`. Combine by product or a declared combiner. A `cap` row takes the lowest.
- [ ] Refuse a factor outside its declared range at the row, by name. Print each factor in `explain_size`.

**You see.**

- [ ] Anything that changes a size has a name, a range and a reason you can read.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_two_modifiers_multiply`. Factors 0.5 and 1.5 on 500 money at risk at stop distance 0.0050 on EURUSD give 375 and 0.75 lots, and the trail prints both.
- [ ] `test_a_factor_outside_its_range_is_refused_by_name`. A factor of 3 on a range of 0 to 2 answers `factor_out_of_range`, and that modifier reads neutral with its fail mode.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Print `explain_size` for a fake-broker trade with two modifiers. Save `check-trail-two.log`. Pass when the trail shows base, both factors, reasons and the sent quantity.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case. The blast-radius fact is this. A unit with no `modifiers` gets a size byte-equal to RC-08's, over the conformance tape.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-21-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Make house money one rule on one ledger, and switch rows on by a fact (RC-22)

Stop B, the whole single-unit baseline. Slice 6. **What it does.** House money and reverse house money become one `cushion-rule` modifier reading one cushion ledger, kept as a scope of the fold. Any row may bind `enabled` to a fact, so one group fact can switch a modifier for a whole pod later.

**Read.** AD-8 "enabled", AD-11, AD-18; FUNNEL D13; SEEDS H-54, H-55.

**Gates and fallbacks.** None. The ledger presses on realised winnings only.

**Depends on.** RC-14, RC-21.

**Files.**

- [ ] Edit `qml/src/qml/fold.py`.
- [ ] Edit `packages/qmf-risk/src/qmf/risk/controls.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/cushion-rule/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/cushion-rule/1/entry.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/press-gate/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/press-gate/1/entry.json`.
- [ ] Create `qml/tests/test_cushion_rule.py`.

**Build.**

- [ ] Add the cushion ledger with an anchor to the fold. A fixed anchor presses and brakes, and a running-peak anchor only brakes.
- [ ] Read `enabled` as a bool or a fact name on every row.

**You see.**

- [ ] Your house money idea and your reverse of it are one thing with one switch.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_fixed_anchor_presses_and_brakes`. Anchor at the day, realised +100 on a base of 100 gives factor above 1 at strength 1 (1.5 in the fixture), realised -50 gives factor 0.75.
- [ ] `test_a_peak_anchor_only_brakes`. Same trades with a running-peak anchor give factors 1 and 0.75.
- [ ] `test_open_profit_never_presses`. An unrealised +500 leaves factor 1.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `packages/qmf-risk/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Print a day of ten fixture trades through `explain_size`. Save `check-cushion-day.log`. Pass when the literal factor column in the fixture matches line by line.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. The ledger reads only rows, so a restart mid-day gives the same factor, by folding from a cold start.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-22-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Give every number its derivation, range, authority and reason (RC-23)

Stop B, the whole single-unit baseline. Slice 7. **What it does.** `NumberSpec` gains who may move a number and why it holds its value, and `unit_check` refuses a number with no reason or range. A replay's find records `Origin.found_by_replay`.

**Read.** AD-14; SPINE section 3 "Numbers"; K9 test 5; SEEDS H-23 to H-27.

**Gates and fallbacks.** None.

**Depends on.** RC-17.

**Files.**

- [ ] Edit `qml/src/qml/unit/model.py`.
- [ ] Edit `qml/src/qml/unit/qmx.unit.1.schema.json`.
- [ ] Edit `qml/src/qml/unit/parse.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/check/layers.py`.
- [ ] Edit `qml/src/qml/unit/templates/canary.json`.
- [ ] Edit `qml/src/qml/unit/templates/dummy-trend-pullback.json`.
- [ ] Create `qml/tests/test_number_spec.py`.

**Build.**

- [ ] Add `derivation`, `owner`, `reason`, `cautious`, `guard`, `never_self_tune`, `stage_values` and `Origin.found_by_replay`. `applies_to_open_positions` exists. `Authority` exists with one value (`model.py:203`) and gains `off` and `at_anchor`.
- [ ] Make check answer by name for a missing reason or range, and label every shipped value `origin: placeholder`, owner "numbers talk".

**You see.**

- [ ] Any number can answer "why is it this and who may change it".

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_k9_5_every_number_has_a_reason_and_range`. A number with no `reason` answers the problem `number_no_reason`, and no range answers `number_no_range`.
- [ ] `test_a_template_number_reads_its_label`. `unit_explain` on `canary` prints `risk_fraction`, 0.005, its range, its reason, `placeholder`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run `unit_check` on every shipped template. Save `check-labels.log`. Pass when every number prints a reason and a range and no problem is listed.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses verification-gap. The blast-radius fact is this. Old documents upgrade through `unit/upgrade.py`, by loading the corpus fixture at the head.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-23-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Widen the built engine to risk numbers, with a bounded memory (RC-24)

Stop B, the whole single-unit baseline. Slice 7. **What it does.** The built motion engine can now bind sizer, exit and control numbers, reads a bounded window, keeps its cadence at an anchor, and its constants become editable rows. Track arrives as a `scaled` number following a fact each bar.

**Read.** AD-14 steps 1 and 2; SWAP-CHART rows 7, E12, E18; `engine.py:39-44, 122, 124`.

**Gates and fallbacks.** None. Presets stay off for size.

**Swaps.** PH7 E12 E18.

**Depends on.** RC-23.

**Files.**

- [ ] Edit `qml/src/qml/motion/engine.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/unit/model.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Create `qml/tests/test_motion_widened.py`.

**Build.**

- [ ] Widen `_bound_on` and the stamp search (`compiler.py:510-516, 620-631`) to sizer, control and exit bindings.
- [ ] Bound `SlowState.read` to `Motion.window`. Add `cadence.at`, `min_trades`, `shrink_k`, `scaled_fact`.
- [ ] Give the rule evidence `stamp`, beside `strength` and declared facts.

**You see.**

- [ ] Nothing on a screen. Next it can learn a size inside a range you set.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_memory_is_bounded`. Window 20 after 1000 trades holds `len(read) == 20`. At the parent it holds 1000.
- [ ] `test_a_scaled_number_follows_its_fact`. Multiple 2 on a fact of 0.0010 reads 0.0020 on this bar and 0.0040 when the fact reads 0.0020.
- [ ] `test_shuffle_control`. Over a seeded shuffled outcome list the number stays inside its range and within one step of its seed on average, labelled mechanism only.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the shipped `trend-floor-from-record` rule at the parent and the head. Save `check-floor-same.log`. Pass when `min_trend_strength` moves from 0 to 0.0001 after 20 trades in both.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case. The blast-radius fact is this. The existing logic number moves exactly as before, by the lane above.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-24-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Let a sizing number and an exit number really move, and show it on the receipt (RC-25)

Stop B, the whole single-unit baseline. Slice 7. **What it does.** Trades now carry the value in force as a stamp `number:<name>`, so the engine stops skipping them, and `own-r-step@1` ships so there is a real rule to run. Any block that ignores a moved number fails the contract, and `explain_size` prints the calibration row that set it.

**Read.** AD-14 steps 1 to 4; K9 test 6; `FIXES.md` "Self-configuration, end to end"; SWAP-CHART row 3.

**Gates and fallbacks.** None.

**Swaps.** PH3 PH7.

**Depends on.** RC-24.

**Files.**

- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qml/src/qml/motion/engine.py`.
- [ ] Edit `qml/src/qml/receipt.py`.
- [ ] Edit `qmb/src/qmb/results/journal.py`.
- [ ] Edit `qml/tests/test_socket_contracts.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/own-r-step/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/own-r-step/1/entry.json`.
- [ ] Create `qml/tests/test_number_moves.py`.

**Build.**

- [ ] Stamp from `numbers_in_force` into the trade row's `entry_stamps`, beside `_stamps` (`unit_handler.py:223-231`).
- [ ] Write `own-r-step@1`, a labelled placeholder that moves one step inside its range by the mean R of its own trades, toward `cautious` when below zero.
- [ ] Add K9 6's check. Answer must change when a bound number in `evidence` changes.

**You see.**

- [ ] A unit can correct itself inside a range you set, and it tells you which trade row moved it.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_k9_6_a_block_ignoring_a_moved_number_fails`. `fixed-fraction-at-stop@1` fails with `ignores_moved_number` and `@2` passes.
- [ ] `test_fraction_moves_and_the_next_entry_uses_it`. With `min_trades` 20 and step 0.0001 after 20 trades at mean -0.5R, a calibration row moves `risk_fraction` from 0.005 to 0.0049, and the next EURUSD entry at equity 100000 and stop distance 0.0050 is 0.98 lots.
- [ ] `test_explain_size_names_the_row`. `explain_size` prints `risk_fraction 0.0049 default 0.005` and the calibration row id.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmb/tests -k unit`, `qml/tests`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run K9 15's scripted trades on QMB. Save `check-moves-qmb.log`. Pass when the printed quantity and target match the literals.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, verification-gap. The blast-radius fact is this. `engine.py:122` no longer skips a stamped risk trade, run on the real engine with a patched log of stamps.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-25-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Keep open trades on their numbers, and survive a restart mid-count (RC-26)

Stop B, the whole single-unit baseline. Slice 7. **What it does.** A held position keeps the numbers it opened with, so a sizer or exit number needs no flat unit and moves with other markets held. `_OwnJournal` is seeded from trade rows, so a restart mid-count ends in the same move.

**Read.** AD-14 steps 5 and 6; K9 test 15; SWAP-CHART rows 8, 22, E15.

**Gates and fallbacks.** None. `applies_to_open_positions` lifts in RC-68.

**Swaps.** PH8 PH22 E15.

**Depends on.** RC-25.

**Files.**

- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Create `qmn/tests/test_app_number_moves.py`.

**Build.**

- [ ] Add `numbers_at_entry` to `PositionFacts`, filled at entry. Read a logic number's flat rule per market at `unit.py:543`.
- [ ] Seed `_OwnJournal` (`runtime.py:1479-1491`) at start, and let the engine's watermark drop what the snapshot already read.
- [ ] Name the close row's `numbers_at_entry` and reason code.

**You see.**

- [ ] Stop point for self-configuration. A number moves, the next trade uses it, the trade already open keeps its own.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_k9_15_self_configuration`. Bind `own-r-step@1` to `risk_fraction` and `target_r`, the numbers behind the blocks' `fraction` and `multiple`. After 20 scripted losing trades, on QMB and the fake broker, the next entry is 0.98 lots with target 1.1095, a position opened earlier keeps 1.1100, it moves with another market held, and a restart at trade 13 ends with the same two values and row ids.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Restart the fake-broker node at trade 13 of 20. Save `check-restart-count.log`. Pass when the move lands on trade 20 and not earlier or later.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. A moved number never amends an open position's exits, by a recording venue showing zero amends.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-26-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Give the node a live account surface (RC-27)

Stop B, the whole single-unit baseline. Slice 8. **What it does.** The node supplies equity by a timed balance re-read, open risk at the stops, margin, liquidation distance and each deployment's budget share, each a fact with a basis. QMB supplies the same names from replay, with a known-answer test.

**Read.** AD-15; SPINE section 3 "Chains and facts"; SWAP-CHART rows 14, 17.

**Gates and fallbacks.** Venue fields are checked on demo after G-DEMO. Until then the fake broker supplies them and the row says so.

**Swaps.** PH14 PH17.

**Depends on.** RC-07.

**Files.**

- [ ] Edit `qmn/src/qmn/app/facts.py`.
- [ ] Edit `qmb/src/qmb/host/facts.py`.
- [ ] Edit `packages/qmf-risk/src/qmf/risk/facts.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/src/qmn/venue/ctrader_account.py`.
- [ ] Create `qmn/tests/test_app_account_facts.py`.

**Build.**

- [ ] Add `account.equity`, `balance`, `open_risk`, `margin_headroom`, `liquidation_distance`, `budget_share`, `realised_since`, `basis`, with the balance read on a timer as a named setting.
- [ ] Say `basis` plainly when equity is marked or balance only, and that `account.open_risk` counts only positions the node holds.

**You see.**

- [ ] Sizing reads your real account as it stands, and says what it read.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_open_risk_known_answer`. Two positions risking 500 and 250 USD read `account.open_risk` 750 in both adapters.
- [ ] `test_a_stale_balance_is_stale`. A balance past its limit reads state `stale` with its age, never a silent old value.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, `qmb/tests -k unit`, `packages/qmf-risk/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Change the fake broker's balance mid-run. Save `check-balance-moves.log`. Pass when the next decision row stores the new equity with its age.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case. The blast-radius fact is this. The timed re-read never runs on the exit path, by a recording client during pass one.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-27-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Observe costs from fills and let the sizer read them (RC-28)

Stop B, the whole single-unit baseline. Slice 8. **What it does.** Cost cells per instrument, broker, hour, session and world are written from fills, labelled `uncalibrated` until enough exist, with a stressed fallback. The fill record and trade row v2 keep net and gross R apart, and the grown sizer reads cost in its denominator.

**Read.** AD-15 "Costs are observed facts"; FUNNEL rows R2, R7; SWAP-CHART rows 1, 13, 16, E13; `handoff/FOR-REPAIR-SOCKET.md` section 2; K9 test 10.

**Gates and fallbacks.** None.

**Swaps.** PH1 PH13 PH16 PH29 E13.

**Depends on.** RC-25, RC-27.

**Files.**

- [ ] Edit `qmb/src/qmb/results/journal.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Edit `qmn/src/qmn/app/facts.py`.
- [ ] Edit `qmb/src/qmb/host/facts.py`.
- [ ] Edit `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`.
- [ ] Edit `qml/src/qml/numbers/records.py`.
- [ ] Edit `qml/src/qml/motion/engine.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/fixed-fraction-at-stop/3/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/fixed-fraction-at-stop/3/entry.json`.
- [ ] Create `qmb/tests/test_cost_cells.py`.

**Build.**

- [ ] Rename `r_after_costs`, which holds gross, to `gross_r`, and add `net_r` as a new field with its reader in `engine.py:57,120` moved in the same PR.
- [ ] Write the fill record (decision quote, arrival quote, fill, partial, reject, requote, markouts) and cost cells from it.
- [ ] Add the commission key on the record. Add `market.gap_factor` and funding as facts a block may read.

**You see.**

- [ ] QMX acts as a data analyst on costs. It knows what each market costs you, by hour, from your own fills.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_k9_10_known_answer_cost`. A long filled 2 pips over a decision quote with commission 7 USD per lot at 1 lot on EURUSD records spread and commission as 20 and 7 USD, cell labelled `uncalibrated` at n=1.
- [ ] `test_gross_and_net_stay_apart`. Money 500, cash -7, risk 500 gives `gross_r` 1.00 and `net_r` 0.986.
- [ ] `test_the_sizer_reads_a_measured_cell`. A measured 0.0002 cost beside stop distance 0.0050 gives 0.96 lots from 500 money at risk, against 1.00 with none.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmb/tests -k unit`, `qmn/tests -k app`, `packages/qmf-data/tests`, `qml/tests`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run 20 fake-broker fills and read the cell. Save `check-cell-calibrates.log`. Pass when the label moves from `uncalibrated` at the fixture's N with the measured value.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, verification-gap. The blast-radius fact is this. Every reader of `r_after_costs` moves in this PR, by a repo-wide grep showing none left.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-28-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Add the feasibility verdict and re-test account brakes across two units (RC-29)

Stop B, the whole single-unit baseline. Slice 8. **What it does.** A pure verdict says whether one minimum lot at this stop fits the unit's share, shown on its card and re-run at anchors. The account-scope halts are re-tested with two units, removing their one-unit label.

**Read.** FUNNEL row I17; `CHECK.md` B7; SPINE section 4 row I17.

**Gates and fallbacks.** None. Shed, concentrate or borrow rules are content.

**Depends on.** RC-27.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/unit_check.py`.
- [ ] Create `qml/src/qml/numbers/feasible.py`.
- [ ] Create `qml/tests/test_feasible.py`.
- [ ] Create `qmn/tests/test_app_account_halts_two_units.py`.

**Build.**

- [ ] Write the verdict through the one converter.
- [ ] Remove the one-unit label after the two-unit test passes.

**You see.**

- [ ] A unit too small for the market says so plainly before it trades.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_one_lot_fits_or_says_not`. Share 5 USD on EURUSD at stop distance 0.0050 and minimum lot 0.01 (risk 5.00) answers `fits`. Share 4.99 answers `below_min_lot` with the shortfall 0.01.
- [ ] `test_account_halt_binds_across_two_units`. Two fake-broker units losing 300 each against a limit of 500 fire `account-daily-loss-halt` for both on the second loss.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmx-agents/packages/qmx-tools/tests`, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the two-unit halt on the fake broker. Save `check-two-unit-halt.log`. Pass when both stop new entries on the same bar and exits still close.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case. The blast-radius fact is this. The verdict computes through `to_quantity`, by a recording call.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-29-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Build one base bar on a feed and roll every stream up from it (RC-30)

Stop B, the whole single-unit baseline. Slice 9. **What it does.** An account's feed builds one small base bar, its default moving from 900 to 60 seconds, and one pure function rolls it up to each unit's stream. Handler and node windows key by stream and market, so a 1-minute and a 15-minute unit stop refusing each other.

**Read.** AD-25 "Base bar", "Roll-up", "Keys"; `CHECK.md` B4; OPEN row 23.

**Gates and fallbacks.** None. Feed load is measured by a plain row.

**Depends on.** RC-10.

**Files.**

- [ ] Edit `qmn/src/qmn/venue/ctrader_account.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Create `qml/src/qml/feed/rollup.py`.
- [ ] Create `qml/src/qml/feed/__init__.py`.
- [ ] Create `qml/tests/test_rollup.py`.
- [ ] Create `qmn/tests/test_app_one_feed.py`.

**Build.**

- [ ] Write `roll_up(base_bars, seconds)` with both quote sides, epoch-aligned buckets, `knowable_at` at the bucket's end, and a bucket not seen from its start dropped.
- [ ] Change `_host` (`runtime.py:2774`) to refuse only a stream that isn't a whole multiple of the base, by name.
- [ ] Key `_bars` and handler windows by `(stream, market)`. A unit hosted on a bar it doesn't read isn't driven.

**You see.**

- [ ] A scalper and an intraday unit can share one account.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_rolled_bars_equal_direct_bars`. Fifteen 1-minute bars with open 1.1000, high 1.1020, low 1.0990, close 1.1010 across them roll to one 15-minute bar of those values on both sides.
- [ ] `test_a_partial_bucket_is_never_emitted`. A feed joining at minute 3 emits nothing for that bucket and the next bucket whole.
- [ ] `test_one_feed_hosts_1m_and_15m`. Both units host and trade on the fake broker. At the parent the second refuses.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, `qmb/tests -k unit`, `qml/tests`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run a 1m and a 15m unit on one fake-broker account for 60 base bars. Save `check-one-feed.log`. Pass when each is driven at its own bar count, 60 and 4.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. The default 60-second base leaves `canary`'s 15-minute decisions equal to the parent's, over the conformance tape.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-30-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Let a unit read a second stream with no look-ahead (RC-31)

Stop B, the whole single-unit baseline. Slice 9. **What it does.** `plan.stream` becomes `plan.streams` with a primary, the fastest. A unit steps when its primary closes and reads a slower stream at its last closed bar.

**Read.** AD-25 "Keys"; SWAP-CHART row `streams_not_built`; K9 test 17.

**Gates and fallbacks.** None.

**Swaps.** STREAMS.

**Depends on.** RC-30.

**Files.**

- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Create `qml/tests/test_second_stream.py`.

**Build.**

- [ ] Lift `streams_not_built`. Count warm-up per stream. Add the `bars:<stream>:<market>` surface.
- [ ] Bump the compiler format.

**You see.**

- [ ] A scalper can look at 5-minute bars while it trades 1-minute ones.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_k9_17_one_feed`. A 1-minute, a 5-minute and a 15-minute unit trade from one feed on the fake broker. A two-stream unit reading m5 at minute 7 sees the bar closed at minute 5.
- [ ] `test_a_slower_bar_is_never_seen_early`. At minute 9 the m5 bar visible has `knowable_at` minute 5. Moving the evidence one minute forward changes no decision.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Print each unit's bar log on the fake broker. Save `check-streams-log.log`. Pass when no decision reads a bar with `knowable_at` after its own instant.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. Single-stream units compile to the same decisions, over the conformance tape.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-31-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Let a unit hold more than one position per market (RC-32)

Stop B, the whole single-unit baseline. Slice 9. **What it does.** `_held` and open positions key by position id, and `own_position:<market>` answers a tuple. `position_limit` compares open plus parked per market and per open, and each exit carries its position.

**Read.** AD-25 "Positions"; `CHECK.md` S3, S9; SWAP-CHART rows E3, E4; WALKS 3.

**Gates and fallbacks.** Above 1 on a netting venue is refused at compile by venue capability.

**Swaps.** E3 E4.

**Depends on.** RC-31.

**Files.**

- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `packages/qmf-risk/src/qmf/risk/unit_intent.py`.
- [ ] Create `qml/tests/test_many_positions.py`.
- [ ] Create `qmn/tests/test_app_many_positions.py`.

**Build.**

- [ ] Move every reader of `own_position` to the tuple in this PR, with no compatibility layer.
- [ ] Add the bet key and driver tags on intents, and `own.open_risk_by_bet_key`, which is why the one-bet check belongs in the unit chain.

**You see.**

- [ ] A unit can scale into a market where its type allows, and each trade keeps its own exits.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_two_positions_get_their_own_exits`. Two longs on EURUSD with stops 1.0950 and 1.0960. The bar that hits 1.0955 closes the second only, by its `position_ref`.
- [ ] `test_position_limit_counts_every_open`. Limit 2 with 2 open answers `suppressed_limit` on a third signal.
- [ ] `test_same_bet_counts_once`. Two units' positions on one bet key read one bet in `own.open_risk_by_bet_key`'s unit view.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmb/tests -k unit`, `qml/tests`, `qmn/tests/test_app_runtime.py`, `qmn/tests -k app`, `packages/qmf-risk/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Hold two positions through a fake-broker restart. Save `check-two-held.log`. Pass when both come back with their own stops.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. `_held` no longer overwrites, by rerunning the second-position overwrite that `runtime.py:1802` allowed at the parent.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-32-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Run sessions and per-market settings (RC-33)

Stop B, the whole single-unit baseline. Slice 9. **What it does.** `sessions` compiles with the record's clock, and a unit can go flat before a session closes. Each market may carry its own settings through the override chain's market key.

**Read.** SWAP-CHART rows E5, E6; FUNNEL rows S9, I16.

**Gates and fallbacks.** None.

**Swaps.** E5 E6a.

**Depends on.** RC-32.

**Files.**

- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qml/src/qml/unit/model.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Create `qml/tests/test_sessions.py`.

**Build.**

- [ ] Lift `sessions` and per-market settings. Add the window card kind.
- [ ] Add forced flat with a buffer as an exit reason `forced_flat`.

**You see.**

- [ ] An intraday unit keeps to its hours and can be set per market.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_session_refuses_outside_its_hours`. London 08:00 to 16:00 in the record's zone, a signal at 16:05 answers `outside_session`, and at 15:55 it enters.
- [ ] `test_flat_before_the_close`. A buffer of 15 minutes closes a held trade on the bar at 15:45 with reason `forced_flat`.
- [ ] `test_a_market_keeps_its_own_number`. `stop_buffer` 2 on EURUSD and 30 on XAUUSD each read their own.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run an intraday fixture across a daylight-saving change. Save `check-dst.log`. Pass when session hours follow the record's zone on both sides of the change.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case. The blast-radius fact is this. A unit with no sessions declared trades the same as today, over the conformance tape.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-33-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Run the remaining logic roles (RC-34)

Stop B, the whole single-unit baseline. Slice 9. **What it does.** `veto`, `cooldown`, `invalidation`, `re_entry`, `arming`, `timeout` and `regime_detector` run in logic slots instead of refusing. `derivation` and `combiner` join, with `combiner` gaining `product` and `min`.

**Read.** FUNNEL row S12; SWAP-CHART row E2; `compiler.py:896-1014`.

**Gates and fallbacks.** None.

**Swaps.** E2.

**Depends on.** RC-33.

**Files.**

- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qml/src/qml/blocks/api.py`.
- [ ] Create `qml/tests/test_logic_roles.py`.

**Build.**

- [ ] Lift each role with its answer type and its place in `_Run.entries`.
- [ ] Enrol each in the census.

**You see.**

- [ ] The dictionary's closing and filtering blocks stop being refused.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_each_role_changes_a_decision`. One parametrized fixture per role. `cooldown` of 3 bars suppresses a signal on bar 2 and lets one through on bar 4, `veto` refuses with its reason, and so on with a literal per role.
- [ ] `test_the_census_counts_no_refused_role`. The role list refused at compile is empty.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Compile and backtest one fixture unit per role. Save `check-roles.log`. Pass when each run finishes and its row names the role.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, structure. The blast-radius fact is this. A shipped unit using none of these keeps its compiled decisions, over the conformance tape.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-34-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Make the SQS a gate slot, cost hurdle first (RC-35)

Stop B, the whole single-unit baseline. Slice 10. **What it does.** Each unit's entry chain gets a gate slot with the verbs block, shrink, wait, warn, shadow and none. The cost hurdle ships as the default, warning while its cost cell is uncalibrated, with the old rule as a floor for broken markets.

**Read.** AD-9, AD-16; FUNNEL D-row SQS-2 and 4.1 Gate; SWAP-CHART row E7; OPEN.

**Gates and fallbacks.** None.

**Swaps.** E7.

**Depends on.** RC-28, RC-34.

**Files.**

- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Create `qml/src/qml/protocol/entry_chain.py`.
- [ ] Create `packages/qmf-risk/src/qmf/risk/chain.py`.
- [ ] Create `packages/qmf-risk/tests/test_chain.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/cost-hurdle/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/cost-hurdle/1/entry.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/sqs-floor/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/sqs-floor/1/entry.json`.
- [ ] Create `qml/tests/test_gate_slot.py`.

**Build.**

- [ ] Write `Verdict` and the unit chain with a plain `try` per link. `block` is the chain's `refuse`, `shrink` rewrites the quantity, `wait` keeps the proposal parked once RC-43 lands and passes with a row until then, `warn`, `shadow` and `none` pass with a row.
- [ ] Add the placement test to the module's docstring and to the compile check.

**You see.**

- [ ] The spread gate becomes a slot you can swap, and the first trades aren't blocked by a gate waiting on the trades.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_the_hurdle_warns_on_an_uncalibrated_cell`. Cell `uncalibrated`, the entry places and the row reads verdict `warn`.
- [ ] `test_the_hurdle_refuses_only_on_a_measured_bad_cell`. Measured cost 0.0060 beside stop distance 0.0050 reads `refuse` with code `net_edge_below_zero`.
- [ ] `test_a_raising_gate_refuses_the_entry_and_stops_no_exit`. A raising gate answers `link_fault` and the held position's exit fires.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `packages/qmf-risk/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the first ten entries of a fresh unit on the fake broker. Save `check-first-entries.log`. Pass when all ten place with `warn`, and the cell's n reaches 10.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. Exits still skip the chain, by the import test and a recording chain showing zero calls on exits.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-35-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Put isolation, news and caution on one sticker, with tolerations (RC-36)

Stop B, the whole single-unit baseline. Slice 10. **What it does.** A sticker is a row with scope, kind, strength, expiry, resume rule, why and who, and a unit's `tolerations` lists the kinds it ignores. News calendars write stickers, a dead calendar lands a card and reads `prefer_not`, and a spec change writes one too.

**Read.** AD-16; FUNNEL D27, S10; SWAP-CHART rows 15, E7; SEEDS H-40, H-64; `handoff/FOR-REPAIR-CLAIMS-BEFORE-C20.md`.

**Gates and fallbacks.** None. The kill switch is not a sticker.

**Swaps.** PH15 E7.

**Depends on.** RC-35.

**Files.**

- [ ] Edit `qmn/src/qmn/app/stand_down.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/src/qmn/data/news_calendar.py`.
- [ ] Edit `qmn/src/qmn/protection/windows.py`.
- [ ] Edit `packages/qmf-risk/src/qmf/risk/control_window.py`.
- [ ] Edit `qml/src/qml/protocol/entry_chain.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/protocol/controls.py`.
- [ ] Create `qmn/tests/test_app_stickers.py`.

**Build.**

- [ ] Add scope keys, kinds and strengths to the stand-down table. Add the `fail` row per source. A `flatten` sticker runs the control runner's `flatten` on each member it scopes.
- [ ] Tag both FX legs. Wire record change to `Runtime.stand_down(SPEC_CHANGE, ...)`.

**You see.**

- [ ] You can keep a unit off an instrument on its news day, and an ORB can ignore the session-open caution.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_news_sticker_refuses_and_a_toleration_passes`. Sticker `news` strength `no_new_entries` on USD refuses a EURUSD entry with reason `sticker:news`, and the same unit with `tolerations: ["news"]` enters.
- [ ] `test_a_dead_calendar_lands_one_card`. Calendar stale gives one card and reads `prefer_not`, with no entry refused.
- [ ] `test_an_expired_sticker_settles_after_a_restart`. A sticker expiring while down is gone on start with a row.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, `packages/qmf-risk/tests`, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Play one fixture news day on the fake broker. Save `check-news-day.log`. Pass when entries pause in the window, exits run, and the row says why.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. `Kind.RISK_STOP` and the kill switch behave as at the parent, by `test_app_stand_down.py` passing unchanged.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-36-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Measure spread and quote gaps on the node, and make one curve per world (RC-37)

Stop B, the whole single-unit baseline. Slice 10. **What it does.** A node sensor publishes spread, tick rate and quote gaps with source `node`. An overnight job makes one "usual level" curve artifact per world, with an age word, read by SQS, node, MIS and QMB.

**Read.** AD-16; FUNNEL row I6; `E1-mis-sqs.md`; F3 B.

**Gates and fallbacks.** Workflow engine changes need a core reason. This adds a template only.

**Swaps.** E7.

**Depends on.** RC-35.

**Files.**

- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/src/qmn/app/facts.py`.
- [ ] Create `qmn/src/qmn/app/sensor.py`.
- [ ] Create `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/curve-factory/definition.json`.
- [ ] Create `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/curve-factory/scripts/curve.py`.
- [ ] Create `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/curve-factory/README.md`.
- [ ] Create `qmn/tests/test_app_sensor.py`.

**Build.**

- [ ] Publish `market.spread`, `tick_rate`, `quote_gap`, `curve` as facts.
- [ ] Flag a borrowed cold start on the curve.

**You see.**

- [ ] The node knows when a market's quote is unusually wide right now.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_the_sensor_reads_spread_and_gap`. Quotes 1.1000 over 1.1002 then none for 30 s read spread 0.0002 and gap 30.
- [ ] `test_an_old_curve_says_old`. A curve 3 days past its limit reads age word `old` and state `stale`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, `qmx-agents/packages/qmx-engine/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the curve template on the fixture's minute rows. Save `check-curve.log`. Pass when one artifact per world with its age and a borrowed flag on cold start.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case. The blast-radius fact is this. The sensor adds no send or wait on the node thread, by a recording client.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-37-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Move the SQS rule and producer before the old gate goes (RC-38)

Stop B, the whole single-unit baseline. Slice 10. **What it does.** The old SQS rule text and baseline producer move to the gate's floor, because the repair's deletion sweep reads them as dead. C-20 can then remove the old gate with nothing lost.

**Read.** `handoff/FOR-REPAIR-CLAIMS-BEFORE-C20.md`; `grounding/G12-audit-and-repair-for-risk.md` section 2; `decision_root.py:493-510`.

**Gates and fallbacks.** None.

**Depends on.** RC-37.

**Files.**

- [ ] Edit `qmn/src/qmn/host/sqs_baseline_producer.py`.
- [ ] Edit `qmn/src/qmn/host/decision_root.py`.
- [ ] Edit `qmn/src/qmn/replay/port.py`.
- [ ] Edit `qmn/src/qmn/config/registry_catalog.py`.
- [ ] Edit `packages/qmf-readings/src/qmf/readings/labelers.py`.
- [ ] Edit `qml/src/qml/blocks/stdlib/sqs-floor/1/block.py`.
- [ ] Create `qmn/tests/test_app_sqs_floor.py`.

**Build.**

- [ ] Fold the eight named settings (`registry_catalog.py:158-241`) to rows the floor reads, each labelled.
- [ ] Keep DEC-0230 and DEC-0153 as they stand. A demo baseline never satisfies a live environment, and a bar-sampled reading never satisfies a live decision.

**You see.**

- [ ] Nothing on a screen. Nothing you built is lost in the cleanup.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_the_floor_says_what_the_old_rule_said`. On the rule's own fixture inputs at `decision_root.py:493-510` both answer the same verdict and reason for each of the literal rows.
- [ ] `test_a_demo_baseline_never_satisfies_live`. A demo-conditioned baseline on a live lane reads `no_baseline`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, `packages/qmf-readings/tests`, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the old rule and the floor over a saved minute file. Save `check-floor-equal.log`. Pass when the two verdict columns are equal.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses verification-gap. The blast-radius fact is this. Nothing calls the moved producer by its old import path, by a repo-wide grep.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-38-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Ship the scalper and intraday templates, and prove each reaches paper (RC-39)

Stop B, the whole single-unit baseline. Slice 10. **What it does.** `scalper-mr` and `intraday-trend`, with an `orb` variant in two rows, ship with the blocks they name. K7 runs all of them to a filled paper entry, and the templates host side by side on one account.

**Read.** FUNNEL 4.1, 4.2; SPINE section 6 "Shipped on"; K9 test 7; SEEDS H-20 to H-22, H-47, H-57.

**Gates and fallbacks.** New block values are labelled placeholders. The spine prices no PR for these blocks, so this one adds them.

**Depends on.** RC-19, RC-22, RC-26, RC-36.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-host/tests/k7_rehearsal.py`.
- [ ] Create `qml/src/qml/unit/templates/scalper-mr.json`.
- [ ] Create `qml/src/qml/unit/templates/intraday-trend.json`.
- [ ] Create `qml/src/qml/unit/templates/intraday-trend-orb.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/fast-invalidation-cut/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/fast-invalidation-cut/1/entry.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/thesis-invalidation-exit/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/thesis-invalidation-exit/1/entry.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/own-percentile-bench/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/own-percentile-bench/1/entry.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/count-brake/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/count-brake/1/entry.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/two-speed-circuit-breaker/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/two-speed-circuit-breaker/1/entry.json`.
- [ ] Create `qml/tests/test_templates_abc.py`.
- [ ] Create `qmx-agents/packages/qmx-host/tests/test_k7_all_templates.py`.
- [ ] Create `qmn/tests/test_app_three_templates.py`.

**Build.**

- [ ] Write the five blocks with their dictionary pages and cold behaviour. The cut uses a fixed labelled distance until N winners exist, with the warning "unproven after costs". Circuit breaker and count brake ship present and off.
- [ ] Write the three template files as in FUNNEL 4.2. `scalper-mr` has its house money on at factor 1 from zero.

**You see.**

- [ ] A scalper, an intraday and a no-brakes template all trade on paper from nothing, side by side, each saying it is a shape.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_k9_7_every_template_reaches_paper`, in `test_k7_all_templates.py`. K7 ends with a fill for `canary`, `scalper-mr` and `intraday-trend`, with no judge run.
- [ ] `test_the_cut_uses_its_fixed_distance_cold`. Zero winners, a 3-pip adverse move at a 3-pip cut closes with reason `fi_cut`.
- [ ] `test_the_bench_shadows_until_n`. Below N trades the bench writes `would_have` and refuses nothing.
- [ ] `test_the_three_templates_share_one_account`, in `test_app_three_templates.py`. All three host on one fake-broker account with bar counts per hour of 4 for `canary`, 60 for `scalper-mr` and 4 for `intraday-trend`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmx-agents/packages/qmx-host/tests`, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run K7 for each template on a fresh throwaway home. Save `check-k7-all.log`. Pass when each ends with one filled entry.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, verification-gap. The blast-radius fact is this. The two-speed breaker off changes no decision, by running with and without it.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-39-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Give the node one admit seam, called by both hosts (RC-40)

Stop B, the whole single-unit baseline. Slice 11. **What it does.** The node chain's runner and `AdmitPort` live in `qml`, and hosts inject the links. `CrossUnitHook` and `PASS_EVERY_ORDER` are deleted, so the one call site in `UnitSliceHandler.mint_intents` runs the same seam on the node and in QMB.

**Read.** AD-9, AD-21; SWAP-CHART row 6; `FIXES.md` S11.

**Gates and fallbacks.** None.

**Swaps.** PH6.

**Depends on.** RC-35.

**Files.**

- [ ] Edit `qml/src/qml/blocks/api.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qml/tests/test_socket_contracts.py`.
- [ ] Create `qml/src/qml/chain/node_chain.py`.
- [ ] Create `qml/src/qml/chain/__init__.py`.
- [ ] Create `qml/tests/test_node_chain.py`.

**Build.**

- [ ] Write `AdmitPort.admit(wire, at)` and the chain runner with a plain `try` per link. A raise refuses that entry with `link_fault`, and nothing returns a refusal into `close_frontier`.
- [ ] Migrate `guard`, `cross_unit_hook` and the protection gate behind the seam (`runtime.py:1100-1106, 2623-2675`). Delete the hook in the same PR.

**You see.**

- [ ] Nothing on a screen. One door for every order.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_raising_link_refuses_and_keeps_trading`. A raising link answers `link_fault`, the phase stays `TRADING`, and the unit's exits fire on the next bar.
- [ ] `test_a_shrink_rewrites_the_wire`. A link shrinking 1.00 to 0.60 sends 0.60, and both verdicts are on the one row.
- [ ] `test_qml_imports_nothing_from_qmn`. The parsed imports of `chain/` hold no `qmn`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the conformance tape through node and QMB. Save `check-admit-tape.log`. Pass when identical trails.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. Every shipped order path still passes one protection check, by `test_protection_every_order.py` unchanged.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-40-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Apply kill effects to entries and give every veto an off switch (RC-41)

Stop B, the whole single-unit baseline. Slice 11. **What it does.** The kill table's effects now apply to entries as well as closes, through injected node links. Margin, order rate, size band and a stop past liquidation become rows with `enabled`, and protection that can't be placed answers by a row.

**Read.** AD-9, AD-20 table; SWAP-CHART rows 14, 18, 19; `FIXES.md` S7.

**Gates and fallbacks.** Kill level meanings stay open values, owner numbers talk. Only his hand lowers a level.

**Swaps.** PH14 PH18 PH19.

**Depends on.** RC-40.

**Files.**

- [ ] Edit `qmn/src/qmn/protection/effect_matrix.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `packages/qmf-risk/src/qmf/risk/controls.py`.
- [ ] Create `qmn/src/qmn/app/node_links.py`.
- [ ] Create `qmn/tests/test_app_node_links.py`.

**Build.**

- [ ] Write links for `stop_entries`, `cancel_resting_entries`, margin headroom, worst-step reserve, size band, order rate and venue stop or declared basis.
- [ ] Move the protection constants (`runtime.py:179-187`) to settings and add the `protection_escalation` row, `close` or `alarm`.

**You see.**

- [ ] At a raised kill level no new trade goes out, and every safety veto beyond the fixed lines can be switched to a warning.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_entries_read_the_kill_effect`. At a level whose effect has `stop_entries`, an entry answers `refuse` with `kill_effect` and a close goes out. At the parent the entry places.
- [ ] `test_a_veto_off_is_a_warning`. Margin veto with `enabled: false` passes with verdict `warn` in the row.
- [ ] `test_a_stop_past_liquidation_refuses`. Stop beyond `liquidation_distance` answers `past_liquidation` with the row on.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, `packages/qmf-risk/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Raise the kill level on the fake broker with entries and a held trade. Save `check-kill-entries.log`. Pass when the entry refuses, the held trade's exit fires.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. No link can raise a size, by a contract on `Shrink` above the wire quantity failing.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-41-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Run the node in two passes, exits first (RC-42)

Stop B, the whole single-unit baseline. Slice 11. **What it does.** Pass one steps every unit on every account and sends its exits at once. Pass two takes parked proposals, prices them on fresh facts and sends, so an entry's wait can never delay another unit's exit.

**Read.** AD-1, AD-17; `runtime.py:1727-1733, 3013-3018`; K9 test 13.

**Gates and fallbacks.** None. Sends stay serial, the known limit in AD-17.

**Depends on.** RC-41.

**Files.**

- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Create `qmn/src/qmn/app/outbox.py`.
- [ ] Create `qmn/tests/test_app_two_passes.py`.

**Build.**

- [ ] Make `on_instant` answer exits and proposals. Move the `price` call site from straight-after-exits to pass two.
- [ ] Write the outbox. Drain by bar time, then rank, then a per-bar hash. Write meters as plain rows.

**You see.**

- [ ] A slow entry can't hold up another unit's stop-out.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_exits_go_before_any_entry`. A venue recording send order on a bar with 3 exits and 3 entries reads the 3 closes first, every time.
- [ ] `test_a_slow_venue_entry_never_delays_an_exit`. Entry send held for 5 s, the next unit's exit is sent before it starts.
- [ ] `test_k9_13_tape_two_passes`. Tape through QMB and node at the head is equal.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, `qmb/tests -k unit`, `qml/tests`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run 20 units firing together on the fake broker. Save `check-bell.log`. Pass when the send log shows all exits first and the meters read pass times.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. No exit reads account facts or the outbox, by the import test and a recording surface.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-42-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Give a parked entry a lifetime and never send it twice (RC-43)

Stop B, the whole single-unit baseline. Slice 11. **What it does.** `_orders` gains `Parked(expires_at)`, and `execute_resting` returns `Ok(False)` for it, so waiting no longer reads as warming up. While parked, the unit reads `parked:<market>` and writes `suppressed_limit`, so one signal is one send.

**Read.** AD-17 "Parked entry", "No second order"; `CHECK.md` B2; K9 test 11.

**Gates and fallbacks.** None. `expires_at` defaults to the next bar of its market, a labelled placeholder.

**Depends on.** RC-42.

**Files.**

- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/src/qmn/app/outbox.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Create `qmn/tests/test_app_parked_entry.py`.

**Build.**

- [ ] Add the `parked:<market>` surface read at `unit.py:515`. `_Run.entries` compares open plus parked with the limit.
- [ ] Expire at the start of pass one for that market to `Blocked("budget_expired")`, writing the `Skip` through `runtime.py:1705-1713`.
- [ ] Turn the gate's `wait` verb on. It stays parked until `expires_at`.

**You see.**

- [ ] A trade that can't go out this bar waits one bar, then is dropped with a reason.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_k9_11_one_signal_one_send`. Pass two reaches the queue a bar late. 1 `ProtoOANewOrderReq`, 1 position at the venue, 1 in the handler. At the parent, RC-42's outbox gives 2 sends, as `CHECK.md` B2 ran.
- [ ] `test_a_parked_entry_expires_by_name`. Past `expires_at` the row reads `Skip` with `budget_expired`.
- [ ] `test_a_parked_entry_never_reads_warming_up`. `execute_resting` answers `Ok(False)`, `None` keeps meaning warming up.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Hold pass two across a bar on the real order path with the fake broker. Save `check-parked.log`. Pass when one send, one position.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. `self.unknown`'s refusal (`runtime.py:1059`) still covers an unknown answer, by the shipped unknown drill.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-43-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Bound the entries pass in time and beat the watchdog honestly (RC-44)

Stop B, the whole single-unit baseline. Slice 11. **What it does.** Pass two starts an entry only if elapsed time plus that entry's worst case fits the budget, worked out from the same constants. `watch.began` resets as a progress beat after each exit send and each finished entry, so the watchdog times one stuck step.

**Read.** AD-17 "Time, in what takes the time"; `FIXES.md` S1; `runtime.py:179-187, 2192`; `ctrader_account.py:110`; `healing.py:64`.

**Gates and fallbacks.** The budget is a labelled placeholder. Test on Windows. Hung blocks remain the watchdog's, AD-9's named risk.

**Depends on.** RC-43.

**Files.**

- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/src/qmn/app/outbox.py`.
- [ ] Edit `qmn/src/qmn/app/healing.py`.
- [ ] Create `qmn/tests/test_app_entry_budget.py`.

**Build.**

- [ ] Compute the worst case from the constants and refuse at start, by name, a worst case longer than the watchdog's limit.
- [ ] Add the beats.

**You see.**

- [ ] A busy moment leaves some entries for the next bar. The node stays up.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_long_bell_leaves_entries_over_and_the_node_lives`. On a virtual clock with a venue answering at its limit, one entry takes 26 s, budget 30. The first entry goes, the second parks, `os._exit` is never called. At the parent's path the same bell passes 30 s.
- [ ] `test_six_slow_closes_beat_the_watchdog`. Six closes at 5 s each with a beat after each never read stuck.
- [ ] `test_a_worst_case_above_the_limit_refuses_at_start`. Constants giving 40 s against a 30 s limit refuse with `budget_impossible`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run a 30-entry bell on the fake broker with a slow venue. Save `check-long-bell.log`. Pass when entries left over are named in the meter and the process stays up.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. The virtual-clock test uses the real constants, by importing them, with no copied literal in the path under test.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-44-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Let a declared no-stop entry compile, size and send (RC-45)

Stop B, the whole single-unit baseline. Slice 11. **What it does.** A unit with no price stop declares `basis: tail_budget` on its sizer row and the send carries `stop_kind: none_declared`. Places 1 to 6 and 11 of AD-22's table read that field.

**Read.** AD-22 rows 1 to 6 and 11; SWAP-CHART row 11; `unit_intent.py:69-73`.

**Gates and fallbacks.** Whether cTrader accepts it is UNKNOWN and joins the demo probes. The shipped default stays a far stop.

**Swaps.** PH11.

**Depends on.** RC-44.

**Files.**

- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qml/src/qml/numbers/convert.py`.
- [ ] Create `qml/tests/test_no_stop_entry.py`.

**Build.**

- [ ] Lift `stop_not_built` for a declared basis. Refuse target levels needing a stop, at compile.
- [ ] Read `none_declared` in `enter`, the handler, the node entry and the veto, and skip `_protected`. Keep `held.risk` as the sizer's declared money.

**You see.**

- [ ] Your reckless scalper with no stop can be written. It warns in the largest type.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_declared_no_stop_sends_one_order_with_no_stop`. Fake broker receives quantity 1.00 from `tail_budget` 500 on distance 0.0050 with no `stopLoss`, and the row reads `none_declared`.
- [ ] `test_r_stands_with_no_stop`. Close at money -250 on declared 500 gives R -0.50.
- [ ] `test_undeclared_no_stop_stays_refused`. No basis still reads `stop_not_built`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Send the entry on the fake broker and read the row. Save `check-no-stop-send.log`. Pass when one order, no stop, warning graded.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. Every shipped unit with a stop takes the same path as before, over the conformance tape.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-45-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Keep a declared no-stop position alive through ticks, restart and reconcile (RC-46)

Stop B, the whole single-unit baseline. Slice 11. **What it does.** Places 7 to 10, 12 and 13 of AD-22 ask the declared field before treating a missing stop as a fault. K9 test 12 holds a stopless entry for N bars and through a restart, and this ends the whole no-stop path.

**Read.** AD-22 rows 7 to 10, 12, 13 and "The test"; `CHECK.md` B9.

**Gates and fallbacks.** Fallback if the venue refuses at the demo probe, capability refuses the true no-stop form there by name, and the far stop stays.

**Swaps.** PH11.

**Depends on.** RC-45.

**Files.**

- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/src/qmn/app/reconciler.py`.
- [ ] Edit `qmn/src/qmn/app/paper_lane.py`.
- [ ] Edit `qmn/src/qmn/venue/ctrader_account.py`.
- [ ] Edit `qmn/src/qmn/order/path.py`.
- [ ] Edit `qmn/src/qmn/venue/live.py`.
- [ ] Create `qmn/tests/test_app_no_stop_held.py`.

**Build.**

- [ ] Make `_restore_stops` (`runtime.py:2358-2386`), `NodeUnit.adopt`, reconcile (`reconciler.py:379-390`), `safe_to_restart` and the adapter's `no-stop` rejection read `none_declared`.
- [ ] One test for each other order path.

**You see.**

- [ ] Nothing else closes it behind your back. Its own cut closes it.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_k9_12_a_stopless_entry_survives`. Held for 10 bars on the fake broker, through a restart, still open, zero `protection_escalation`, then closed by its own cut. At the parent the first tick closes it.
- [ ] `test_a_position_with_a_lost_stop_still_escalates`. A position whose send row had a stop, missing at the venue, still closes and alarms.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run K9 12 and print the alarms. Save `check-no-stop-held.log`. Pass when no escalation, restart names it open by declaration.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. A lost real stop still escalates, by the second test on the real tick.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-46-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Give the copilot its doors for one unit (RC-47)

Stop B, the whole single-unit baseline. Slice 11. **What it does.** The copilot gains the tool rows the single-unit baseline needs, each declaring read, propose or run. It can patch a draft, read any scope's risk state, explain any size, replay a decision and propose a sticker as a card.

**Read.** SPINE section 8; AD-20; `E5` flaw 15; `qmx-tools/tests/test_tools.py`.

**Gates and fallbacks.** None. No row reaches money. The count test moves on purpose.

**Depends on.** RC-36.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/servers.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/tests/test_tools.py`.
- [ ] Edit `qmx-agents/plugin/skills/build-unit/SKILL.md`.
- [ ] Create `qmx-agents/packages/qmx-tools/tests/test_unit_tool_rows.py`.

**Build.**

- [ ] Add `unit_patch`, `risk_state`, `explain_size`, `replay_decision`, `sticker_propose`, `card_land`. Add `direction` on each row, read, propose or run.
- [ ] Change the skill's order so it matches what a chat does, and say a block can't be saved until RC-59.

**You see.**

- [ ] You can ask the copilot "why this size?" and "why didn't it trade?" and get the row.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_explain_size_tool_returns_the_trail`. On a stored row the tool returns the literal quantity and the steps.
- [ ] `test_a_sticker_proposal_applies_nothing`. `sticker_propose` lands one card and the stand-down table is unchanged.
- [ ] `test_k9_8_still_holds`. The tool table reaches no money door.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmx-agents/packages/qmx-control/tests`, `qmx-agents/packages/qmx-tools/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Ask the copilot on `haiku` why a fixture trade had its size. Save `check-copilot-size.log`. Pass when the answer names the row's literal quantity and fraction.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses adversarial. The blast-radius fact is this. Every new row declares `direction`, by a test over the catalog.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-47-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Finish the single-unit guide and ready stop point B (RC-48)

Stop B, the whole single-unit baseline. Slice 11. **What it does.** The rip-out list widens past blocks to rows, the developer guide is filled for the single-unit baseline, and the money app's version moves once. This is stop point B, the whole single-unit baseline.

**Read.** SPINE section 5 closing paragraph, section 7 "`EXTENDING.md`", section 10; OPEN rows 1, 8, 8a.

**Gates and fallbacks.** G-SIGN. By this point he may rule on what a pod is (OPEN row 1). The build continues on the default and logs it in `QUESTIONS-FOR-OPERATOR.md`.

**Swaps.** PH30.

**Depends on.** RC-39, RC-46, RC-47, RC-29.

**Files.**

- [ ] Edit `tools/qml/placeholders.py`.
- [ ] Edit `tools/tests/test_placeholders.py`.
- [ ] Edit `tools/qml/extending.py`.
- [ ] Edit `qml/EXTENDING.md`.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`.
- [ ] Edit `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py`.
- [ ] Create `tools/lanes/release_note_stop_b.md`.

**Build.**

- [ ] List PH 5, 6, 18, 19, 20 rows in `placeholders.py`, and prove the rip-out list empties.
- [ ] Write the "why each seat exists", the traps and the three tiers of change in the guide.
- [ ] Bump version rows and digests. Write the plain note.

**You see.**

- [ ] Stop point B. One unit, three templates, no pod, no group, whole. One line to sign.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_the_rip_out_list_reaches_rows`. A fixture unit lists `session-loss-limit-halt`'s placeholder values with row ids, a literal line.
- [ ] `test_the_guide_is_current`. `tools/qml/extending.py --check` exits 0.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `tools/tests`, `qml/tests`, `qmx-agents/apps/trading-node/tests`, `qmx-agents/packages/qmx-apps/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the whole-repo check at the head. Save `check-whole-b.log`. Pass when nothing fails beyond the named baseline reds.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses verification-gap. The blast-radius fact is this. K7 for all three templates and K9 2, 11, 12, 15, 16, 17 all pass at this head, in one run.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-48-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Write the group document and publish its limits as live facts (RC-49)

Stop C, groups, pods and shipping. Slice 12. **What it does.** A group is a document with a selector by unit id or tag, money, limits, caps, a ledger and a rank, and it touches no member. Every number in `limits` and `money` is published on scope `group:<id>`, so one edit reaches 200 units at their next decision.

**Read.** AD-2 tiers, AD-5 last lines, AD-8, AD-21; SPINE section 3 "Pod and group"; FUNNEL row K5.

**Gates and fallbacks.** The `book` and `bms` kinds become read-only shells, the spine's "replaces" with no migration stated. See Appendix H.

**Depends on.** RC-48.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-library/src/qmx_library/kinds/bms.schema.json`.
- [ ] Edit `qmx-agents/packages/qmx-library/src/qmx_library/kinds/book.schema.json`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/promote.py`.
- [ ] Edit `qmn/src/qmn/app/facts.py`.
- [ ] Create `packages/qmf-risk/src/qmf/risk/group.py`.
- [ ] Create `packages/qmf-risk/tests/test_group_types.py`.
- [ ] Create `qml/src/qml/group/__init__.py`.
- [ ] Create `qmx-agents/packages/qmx-library/src/qmx_library/kinds/group.schema.json`.
- [ ] Create `qmn/tests/test_app_group_limits.py`.

**Build.**

- [ ] Add `Group`, `Selector`, `LedgerSpec`, `CapAnswer`. Membership is by selector, and a deployment may also name `group_id`.
- [ ] Publish limits at edit and at each anchor. The edit is his click on the group row's version, bound to one hash.

**You see.**

- [ ] You change one limit once, and every member reads it at its next trade with no recompile.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_one_edit_reaches_members_with_no_recompile`. A 200-unit fixture reads `group.limit.day_stop` 100 then 80 after one edit, and zero compiled fingerprints move.
- [ ] `test_a_stale_click_is_refused`. A click on an old row version answers `stale_click`.
- [ ] `test_many_to_many_selector`. A unit tagged `fx` and `scalper` belongs to both groups.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmx-agents/packages/qmx-library/tests`, `qmx-agents/packages/qmx-host/tests`, `qmn/tests -k app`, `packages/qmf-risk/tests`, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Edit a limit on the fake lane with a unit trading. Save `check-limit-live.log`. Pass when the next row stores the new limit with its age.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. No member document changes on a group edit, by hashing the 200 documents before and after.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-49-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Run group caps that can only cut, on one ledger (RC-50)

Stop C, groups, pods and shipping. Slice 12. **What it does.** Caps are control rows of scope `group`, answering pass, shrink or refuse at two moments, on an entry in pass two and after each ledger fold. An unknown outcome keeps its room, and rank sorts the outbox.

**Read.** AD-8, AD-9 placement test, AD-18; SWAP-CHART row 27; K9 test 9.

**Gates and fallbacks.** None.

**Swaps.** PH27.

**Depends on.** RC-49.

**Files.**

- [ ] Edit `qml/src/qml/fold.py`.
- [ ] Edit `qmn/src/qmn/app/node_links.py`.
- [ ] Edit `qmn/src/qmn/app/outbox.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Create `qml/src/qml/group/caps.py`.
- [ ] Create `qml/src/qml/group/ledger.py`.
- [ ] Create `qml/tests/test_group_caps.py`.
- [ ] Create `qmn/tests/test_app_group_caps.py`.

**Build.**

- [ ] Write the cap runner with a plain `try`. A cap never raises a size, by contract.
- [ ] Fold group scope. Expose `group.day_pnl`, `open_risk`, `raise_ok`, `cushion`, `members`, `limit.<name>`.
- [ ] Count an unknown venue answer in `group.open_risk` until settled.

**You see.**

- [ ] Units share a limit, and two firing on one bar can't overrun it.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_two_units_cannot_overrun_a_shared_cap`. Limit 1000, each wants 600 at one bar. The higher rank gets 600, the second shrinks to 400, and open risk reads 1000.
- [ ] `test_an_unknown_answer_keeps_its_room`. An unknown 600 leaves 400 for the next until settled, then 1000 if blocked.
- [ ] `test_a_day_stop_fires_with_no_entry_pending`. The fold crossing -500 fires `on_fire` with no entry in the outbox.
- [ ] `test_a_cap_never_raises_a_size`. A cap answering 2.00 on a wanted 1.00 fails the contract.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run two units at one bell on the fake broker. Save `check-shared-cap.log`. Pass when fills sum to the limit.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. Caps are atomic because nothing else runs on the node thread, by asserting the thread name in the runner during the test.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-50-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Ship the default group rows, the kill line and restart rules (RC-51)

Stop C, groups, pods and shipping. Slice 12. **What it does.** The default group row is own size under a parent limit plus a portfolio day stop that stands everything down until the day boundary, and the kill line becomes a cap on a floor that survives restart. Recovery folds journals and broker deals before answering any entry, and cuts stand while a raise waits for the next anchor.

**Read.** AD-8, AD-18 "Restart rules"; SWAP-CHART row 20; FUNNEL 4.1 Group row; SEEDS H-65.

**Gates and fallbacks.** The old `qmn/capital/kill_line.py` is subtracted after its replacement passes, per `handoff/FOR-REPAIR-CLAIMS-BEFORE-C20.md`.

**Swaps.** PH20.

**Depends on.** RC-50.

**Files.**

- [ ] Edit `qmn/src/qmn/capital/kill_line.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/parent-limit/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/parent-limit/1/entry.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/portfolio-day-stop/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/portfolio-day-stop/1/entry.json`.
- [ ] Create `qml/src/qml/blocks/stdlib/kill-line-cap/1/block.py`.
- [ ] Create `qml/src/qml/blocks/stdlib/kill-line-cap/1/entry.json`.
- [ ] Create `qmn/tests/test_app_group_restart.py`.

**Build.**

- [ ] Make an anchor id a pure function of clock and time. Settle anchors passed while down once, latest wins, marked `restart_late`.
- [ ] Until the ledger is rebuilt, caps read UNKNOWN and refuse entries, and exits are free.

**You see.**

- [ ] The floor you set survives a restart. A restart never gives size back early.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_restart_is_no_reset`. Cut to 0.5 at 10:00, restart at 11:00, the factor stays 0.5. A raise earned at 10:30 waits for the next anchor.
- [ ] `test_anchors_settle_once`. Two anchors passed while down write one row each, latest wins, `restart_late` true.
- [ ] `test_the_floor_survives`. Floor 300 reads 300 after a restart with its snapshot gone.
- [ ] `test_unknown_ledger_refuses_entries_only`. Before rebuild an entry answers `refuse`, and an exit closes.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Kill and restart the fake-broker node mid-day. Save `check-restart-day.log`. Pass when cuts stand, exits free, raises wait.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. Settling anchors is idempotent, by running recovery twice over the same rows and comparing.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-51-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Replay several units together and prove the group at 200 (RC-52)

Stop C, groups, pods and shipping. Slice 12. **What it does.** `group_run` replays many units in QMB with the node's pass-two order, stamped `group: merged`. A 200-member test measures real throughput on the fake broker, and the copilot gets `group_draft` and `group_check`.

**Read.** SPINE section 6 "One evaluator"; OPEN row 20; K9 test 13.

**Gates and fallbacks.** None.

**Depends on.** RC-51.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/tests/test_tools.py`.
- [ ] Create `qmb/src/qmb/host/group_run.py`.
- [ ] Create `qmn/tests/test_app_group_run.py`.
- [ ] Create `qmn/tests/test_app_group_200.py`.

**Build.**

- [ ] Drive several `HostedUnit`s with one ledger in QMB, in rank order.
- [ ] Measure pass one, pass two and rows per bar at 200 units and record them, with no fail rule the first time.

**You see.**

- [ ] You can backtest a group and it behaves as the node would.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_replay_order_equals_node_order`. A 3-unit tape reads the same send order in QMB and on the fake broker.
- [ ] `test_a_solo_run_is_stamped_none`. One unit reads `group: none` and two read `merged`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmx-agents/packages/qmx-control/tests`, `qmx-agents/packages/qmx-tools/tests`, `qmb/tests -k unit`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run 200 members for 100 bars on the fake broker. Save `check-group-200.log`. Pass when it finishes with no heal, and the meters are printed.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Milliseconds per pass at 200 members, recorded in OPEN row 20's place. Reopen the design note if a bar's pass one exceeds the bar itself.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses verification-gap. The blast-radius fact is this. QMB's single-unit results are unchanged by `group_run`, over the conformance tape.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-52-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Make a pod a recipe, stamped in by a pure function, with drift reported (RC-53)

Stop C, groups, pods and shipping. Slice 13. **What it does.** `expand(unit, pod)` fills the risk half from a saved recipe and records the recipe and what it displaced, so leaving a pod restores them. A row touching logic is refused by name, and a drift report lists members that no longer follow their recipe.

**Read.** AD-4; SPINE section 3 "Pod and group"; SWAP-CHART row 31; OPEN row 1.

**Gates and fallbacks.** OPEN row 1. If he picks a governing pod, this PR and RC-54, RC-55 are replaced per SPINE section 12.

**Swaps.** PH31.

**Depends on.** RC-48.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-library/src/qmx_library/kinds/pod.schema.json`.
- [ ] Edit `qmx-agents/packages/qmx-library/src/qmx_library/kinds/pod-block.schema.json`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/unit/model.py`.
- [ ] Create `qml/src/qml/pods/__init__.py`.
- [ ] Create `qml/src/qml/pods/expand.py`.
- [ ] Create `qml/src/qml/pods/drift.py`.
- [ ] Create `qml/tests/test_pods_expand.py`.

**Build.**

- [ ] Write `expand` as deterministic and idempotent. Honour `risk_locks`.
- [ ] Give `kinds/pod` a real schema and retire `pod-block` into `component`.

**You see.**

- [ ] Change one recipe and you know exactly who follows it.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_expand_is_idempotent`. Twice gives the byte-equal document.
- [ ] `test_leaving_a_pod_restores_the_rows`. The unit's own sizer returns after removing the recipe, and the fingerprint equals the original.
- [ ] `test_a_recipe_touching_an_exit_is_refused`. Answers `recipe_touches_logic` with the field name.
- [ ] `test_drift_lists_by_row`. 14 members, 2 hand-edited. "12 of 14 follow the recipe" with the two rows listed.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmx-agents/packages/qmx-library/tests`, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Stamp a gallery-shaped pod onto all three templates and compile. Save `check-stamp-three.log`. Pass when three fingerprints, logic unchanged on each.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. `expand` never changes `logic_fingerprint`, as a property over the corpus fixture.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-53-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Turn one pod edit into one plan and one click (RC-54)

Stop C, groups, pods and shipping. Slice 13. **What it does.** `roll_plan` stamps, checks and compiles every member off the node and sorts each as risk-only, unchanged, locked, logic-touching or refused. His one click binds to the plan's hash through the money door, and a stale plan is refused.

**Read.** AD-5; SPINE section 4 row S14 (deployment key); FUNNEL row K5; OPEN row 2.

**Gates and fallbacks.** Agents and the copilot write drafts and plans only.

**Depends on.** RC-53, RC-49.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/promote.py`.
- [ ] Edit `qml/src/qml/identity/table.py`.
- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/tests/test_tools.py`.
- [ ] Create `qml/src/qml/pods/roll.py`.
- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/roll.py`.
- [ ] Create `qml/tests/test_pods_roll.py`.

**Build.**

- [ ] Compute `H(pod hash, sorted (deployment, new risk fingerprint))`. A plan may cover a subset, as a canary. A `logic_touch` member stays out and is named.
- [ ] Keep the deployment key as unit version, market, lane and recipe hash, so two paper twins keep their seats. Add the identity table's section column.
- [ ] Add `pod_draft`, `pod_check`, `pod_explain`, `roll_plan`, `drift_report`.

**You see.**

- [ ] One edit, one plan, one click, for 200 units.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_plan_sorts_members`. Fixture of 5 reads `risk_only` 2, `unchanged` 1, `locked` 1, `logic_touch` 1 with the plan hash a literal.
- [ ] `test_a_stale_plan_is_refused`. A member changing after the plan answers `stale_plan`.
- [ ] `test_two_deployments_of_one_version`. Paper twins both deploy, and `promote.py:422-447` stays green.
- [ ] `test_no_tool_clicks`. The catalog has no row applying a plan.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmx-agents/packages/qmx-host/tests`, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmx-agents/packages/qmx-control/tests`, `qmx-agents/packages/qmx-tools/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Plan and click for 200 fixture members on the fake lane. Save `check-plan-200.log`. Pass when one hash, literal counts, time recorded.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. Nothing in the plan path writes to a live deployment before the click, by a recording store.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-54-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Move risk in place, with open trades and logic state untouched (RC-55)

Stop C, groups, pods and shipping. Slice 13. **What it does.** `HostedUnit.move_risk` keeps logic instances, derived numbers and open positions and rebuilds only risk instances. The node compiles members on its one worker, then flips all of them on one tick.

**Read.** AD-3, AD-6, AD-12; `unit.py:990-991`; `runtime.py:2098`.

**Gates and fallbacks.** None.

**Depends on.** RC-54.

**Files.**

- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/roll.py`.
- [ ] Create `qml/tests/test_move_risk.py`.
- [ ] Create `qmn/tests/test_app_move_risk.py`.

**Build.**

- [ ] Split snapshots into two parts, each judged by its own fingerprint in `_cold_reason`.
- [ ] Keep a control row's state by matching row id, pin and params, or rebuild it from the fold.
- [ ] Write `risk_move` rows.

**You see.**

- [ ] A recipe change lands with no cold start. Open trades keep their exits.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_size_edit_moves_in_place`. Logic state hash equal, an open position's stop and target equal, next entry 0.50 lots against 1.00.
- [ ] `test_a_logic_change_is_refused`. A different logic fingerprint answers `Refused("logic_changed")`.
- [ ] `test_all_flip_on_one_tick`. 50 members read the new risk fingerprint on the same tick, none between.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmn/tests -k app`, `qmx-agents/packages/qmx-host/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Flip a plan on the fake broker with trades open. Save `check-flip.log`. Pass when every open position's exits still fire.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. No host ever runs a different compiled fingerprint over a held trade except by `move_risk` or a drain, by a test asserting at the host seam.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-55-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Compile stages in, so "at 5,000 the math changes" is a state (RC-56)

Stop C, groups, pods and shipping. Slice 13. **What it does.** A risk half may declare stages with a selector, anchor, hysteresis and the rows in force for each. A stage move is a state change at an anchor with a `stage_move` row, by rule or card per direction.

**Read.** AD-7; OPEN row 2; SEEDS H-34.

**Gates and fallbacks.** Templates ship `card` up and `rule` down, the OPEN default. Only his answer moves a card.

**Depends on.** RC-55.

**Files.**

- [ ] Edit `qml/src/qml/unit/model.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qml/src/qml/unit/sections.py`.
- [ ] Edit `qml/tests/test_unit_refuses.py`.
- [ ] Create `qml/tests/test_stages.py`.

**Build.**

- [ ] Lift `stages`. Compile all rows into the plan. Selector fact read at its anchor only.

**You see.**

- [ ] A unit changes how it sizes at a level you declared, with one click covering all of it up front.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_stage_moves_at_the_anchor`. Equity 5100 at the anchor with threshold 5000 and hysteresis 200 moves up. 5100 mid-day doesn't, and 4900 back doesn't, because down needs below 4800.
- [ ] `test_a_card_waits_and_the_old_stage_trades`. Move up is `card`. Rows stay on stage 1 until the answer.
- [ ] `test_no_new_version_on_a_move`. Both fingerprints equal across a move.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Walk equity across a level on the fake broker. Save `check-stage.log`. Pass when one `stage_move` row with the literal anchor.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case. The blast-radius fact is this. A stage with exit `stage_values` is logic, so a risk edit can't move an exit number, by RC-03's rule on a real document.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-56-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Seed the pod gallery as ingredients (RC-57)

Stop C, groups, pods and shipping. Slice 13. **What it does.** E2's twenty pod configurations ship as `pod` and `group` Library items, each listing the blocks it needs. Nothing proves them, and they say so.

**Read.** `E2-pods-miniapps.md` section on the twenty pods; SOLUTION "Pods and mini apps"; SEEDS H-71.

**Gates and fallbacks.** Blocks marked `n:` are content someone writes. An item needing one says which and compiles once it exists.

**Depends on.** RC-54.

**Files.**

- [ ] Create `qml/src/qml/pods/gallery/README.md`.
- [ ] Create `qml/src/qml/pods/gallery/index.json`.
- [ ] Create `qml/tests/test_pod_gallery.py`.

**Build.**

- [ ] Write the twenty items as JSON under `pods/gallery/`. Write `index.json` naming each item, its method and its needs.

**You see.**

- [ ] You can browse twenty ready ideas, each saying what it needs and that none has run.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_the_gallery_has_twenty`. 20 items with names from Relentless to Full press, a literal list.
- [ ] `test_each_compiles_or_names_its_missing_block`. Each item with all `s:` blocks compiles with `expand` against each template, and the others name their missing block.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Land the gallery on a throwaway home. Save `check-gallery.log`. Pass when 20 drafts land and none is deployed.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses structure. The blast-radius fact is this. Landing items never touches a deployment, by a recording store.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-57-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Open the readings bus, with a publisher and a fallback on every read (RC-58)

Stop C, groups, pods and shipping. Slice 14. **What it does.** `reads` compiles with publisher, fallback, stale limit and `valid_until`, and the host stamps the source. The fallback of any market list is home markets, closing the fault where a wide unit trades everything on a dead board.

**Read.** AD-16; SWAP-CHART rows E1, E6; `runtime.py:367-369`; `E1-mis-sqs.md`.

**Gates and fallbacks.** Fifteen new physics readings and the finder's internals belong to the MIS owner.

**Swaps.** E1 E6b.

**Depends on.** RC-48.

**Files.**

- [ ] Edit `qml/src/qml/unit/model.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/feed_relay.py`.
- [ ] Edit `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`.
- [ ] Create `qmn/tests/test_app_reads_bus.py`.
- [ ] Create `qml/tests/test_reads.py`.

**Build.**

- [ ] Lift `reads`. Add the `reading:<id>:<market>` surface, `Read.publisher`, `valid_until_s`, `STAND_ASIDE`, `context_needs`.
- [ ] Write the reading record with `knows_at`. Let the relay carry any publisher, with `source` set by the host.
- [ ] Fix the fallback to home markets.

**You see.**

- [ ] Any app can publish a reading a unit may choose to trust. If it stops, the unit knows.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_dead_board_falls_back_to_home`. Markets 40, home 3, board stale. Entries only on the 3. At the parent, all 40.
- [ ] `test_a_forged_source_is_replaced`. A publisher claiming `node` reads `app:x` on the record.
- [ ] `test_a_stale_reading_takes_its_fallback`. Each of the four fallbacks gives its literal behaviour.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmn/tests -k app`, `qmx-agents/packages/qmx-host/tests`, `packages/qmf-data/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Stop the MIS mid-run on the fake broker. Save `check-mis-down.log`. Pass when readings age, home markets trade, no unit stops.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. No shipped template needs a reading to trade, by K7 with the relay off.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-58-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Land pods, presets, blocks and templates from a mini app, and save a block through a door (RC-59)

Stop C, groups, pods and shipping. Slice 14. **What it does.** A mini app's `library-items` lander lands its items as drafts at publish, and `template` becomes a real kind holding overrides only. `blocks_save` lets an agent or user save a Library block with its contract test.

**Read.** SPINE section 8; FUNNEL row S16, I9; `E5` flaw 11; SOLUTION "Pods and mini apps".

**Gates and fallbacks.** Stdlib still needs his signature, Library does not. `plain_python` stays refused.

**Depends on.** RC-53.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-library/src/qmx_library/kinds/template.schema.json`.
- [ ] Edit `qmx-agents/packages/qmx-library/src/qmx_library/kinds/component.schema.json`.
- [ ] Edit `qmx-agents/packages/qmx-library/src/qmx_library/landing.py`.
- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py`.
- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/tests/test_tools.py`.
- [ ] Edit `qmx-agents/plugin/skills/build-unit/SKILL.md`.
- [ ] Create `qmx-agents/packages/qmx-tools/tests/test_block_save.py`.
- [ ] Create `qmx-agents/packages/qmx-library/tests/test_library_items_lander.py`.

**Build.**

- [ ] Add `blocks_save(entry, source)`, scanned by layer F and enrolled in the contract test. Add `template_save(json)`.
- [ ] Add provenance, claim and generation stamp on saved items.

**You see.**

- [ ] The copilot can add a new sizer or brake, tested before it saves.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_bad_block_is_refused_with_its_contract_failure`. A sizer answering a float is refused, and nothing lands.
- [ ] `test_a_preset_holds_only_what_differs`. A template item with one override resolves to the base plus that row.
- [ ] `test_a_mini_app_lands_a_pod_at_publish`. Publishing lands one pod draft and no deployment.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmx-agents/packages/qmx-library/tests`, `qmx-agents/packages/qmx-apps/tests`, `qmx-agents/packages/qmx-control/tests`, `qmx-agents/packages/qmx-tools/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Save a Library sizer through the tool on `haiku`. Save `check-block-save.log`. Pass when the block lands with its test result.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses adversarial, edge-case. The blast-radius fact is this. Saved block code can't reach `qmn`, by layer F's scan refusing a planted import.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-59-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Trace a Library block to a node deploy, and a mini app's reading to a unit (RC-60)

Stop C, groups, pods and shipping. Slice 14. **What it does.** This proves "one folder, zero core edits" by trading a Library sizer on the fake broker. A mini app's reading reaches a unit through the same path, and if either trace fails, the fallback is named.

**Read.** OPEN row 11; SPINE section 10 slice 14; SEEDS H-05, H-72 to H-75.

**Gates and fallbacks.** Fallback if the trace fails, a stdlib path with his signature until fixed, and the promise is withdrawn from the guide.

**Depends on.** RC-58, RC-59.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/promote.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Create `qmx-agents/packages/qmx-host/tests/test_library_block_trades.py`.
- [ ] Create `qmx-agents/packages/qmx-host/tests/library_block_trace.py`.

**Build.**

- [ ] Fix whatever the trace finds on the promote and node path, inside these files. Anything bigger is a finding.

**You see.**

- [ ] A new sizer written today trades tonight, on paper, with no one touching the core.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_library_sizer_trades_on_the_fake_broker`. Library sizer answering `Amount(money_at_risk, 200)` gives 0.40 lots on EURUSD at stop distance 0.0050.
- [ ] `test_a_mini_apps_reading_reaches_a_unit`. Published reading 1.5 appears in the decision row's `readings_used` with `app:x`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmx-agents/packages/qmx-host/tests`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the trace script on a throwaway home. Save `check-block-trace.log`. Pass when it prints PASS at save, compile, promote, deploy and fill.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, verification-gap. The blast-radius fact is this. The block travels through the lock without a money-app bump, by comparing the node's folder hash before and after.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-60-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Let an app read journals and the fold, and raise a card (RC-61)

Stop C, groups, pods and shipping. Slice 15. **What it does.** An app's `data_reads` widens past `market` to `journals` and `fold`. The app-to-"Needs you" card path is traced and fixed where it fails.

**Read.** SPINE section 8 "Apps"; FUNNEL row K2; `E5` flaws 3, 4, 9; `supervisor.py:891`.

**Gates and fallbacks.** The mini-app core is his. Change only this read and this path, with the reason in one line.

**Depends on.** RC-48.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/supervisor.py`.
- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py`.
- [ ] Edit `qmx-agents/packages/qmx-apps/src/qmx_apps/artifacts.py`.
- [ ] Edit `qmx-agents/packages/qmx-library/src/qmx_library/kinds/proposal-card.schema.json`.
- [ ] Create `qmx-agents/packages/qmx-apps/tests/test_data_reads_journals.py`.

**Build.**

- [ ] Grant read-only roots by declaration.
- [ ] Add a "look at this" ask to the card list, and an incident card by root-cause key.

**You see.**

- [ ] A mini app can see your units' records, read-only, and raise one card.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_an_app_reads_journals_and_cannot_write`. Read gives rows, and a write to the root is refused.
- [ ] `test_an_undeclared_app_reads_nothing`. No `data_reads` row answers refused.
- [ ] `test_one_incident_one_card`. Ten raises with one key land 1 card.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmx-agents/packages/qmx-apps/tests`, `qmx-agents/packages/qmx-library/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Install an example app with a journal read on a throwaway home. Save `check-app-read.log`. Pass when it reads and its card shows in "Needs you".
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses adversarial, edge-case. The blast-radius fact is this. The shipped breaker and road tests pass unchanged.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-61-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Ship the scripted fleet watch as a mini app and turn off the decay flood (RC-62)

Stop C, groups, pods and shipping. Slice 15. **What it does.** `fleet-watch` reads the fold once a night and on demand, with one ranked row per unit, two lists, one incident one card and a morning digest, and no agent in it. The shipped decay rule's per-unit nightly card is switched off in the same PR.

**Read.** SPINE section 8 "The scripted fleet watch"; `E5` section 1; SWAP-CHART row 28; `FIXES.md` S16.

**Gates and fallbacks.** K and the strict bar are labelled placeholders. Agent layers belong to the agentic session.

**Swaps.** PH28.

**Depends on.** RC-61, RC-51.

**Files.**

- [ ] Edit `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/dc-decay-and-limit-report/scripts/land.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`.
- [ ] Edit `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`.
- [ ] Edit `qmx-agents/packages/qmx-tools/tests/test_tools.py`.
- [ ] Edit `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py`.
- [ ] Edit `tools/test_all.py`.
- [ ] Create `qmx-agents/apps/fleet-watch/app.toml`.
- [ ] Create `qmx-agents/apps/fleet-watch/server.py`.
- [ ] Create `qmx-agents/apps/fleet-watch/pyproject.toml`.
- [ ] Create `qmx-agents/apps/fleet-watch/tests/test_fleet_watch.py`.
- [ ] Create `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/fleet-fold/definition.json`.
- [ ] Create `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/fleet-fold/scripts/fold.py`.
- [ ] Create `qmx-agents/packages/qmx-engine/src/qmx_engine/templates/fleet-fold/README.md`.

**Build.**

- [ ] Package through the manifest with `data_reads`. It installs, stops and swaps like any other app.
- [ ] Add `fleet_read()` and read it in the digest. From zero every row reads "too thin to judge".

**You see.**

- [ ] You don't have to monitor. 200 units read as one ranked list and a morning note.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_one_row_per_unit`. 200 fixtures give 200 rows ranked, and the first's distance is a literal.
- [ ] `test_two_lists`. Look-at holds K items, act-on only those past the strict bar.
- [ ] `test_from_zero_every_row_is_too_thin`. An empty store with 3 units reads "too thin to judge" three times, and no card.
- [ ] `test_the_decay_card_is_off`. The decay template lands 0 per-unit cards.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmx-agents/packages/qmx-engine/tests`, `qmx-agents/packages/qmx-tools/tests`, `qmx-agents/packages/qmx-control/tests`, `qmx-agents/packages/qmx-apps/tests`, `tools/tests`, `qmx-agents/apps/fleet-watch/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Install `fleet-watch` on a throwaway home with a fixture store. Save `check-fleet.log`. Pass when it starts, ranks, and stops the units on nothing.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, verification-gap. The blast-radius fact is this. Stopping the app changes no unit, by trading through a stop on the fake broker.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-62-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Report with and without motion, stamp run arms, and reserve the proposal row (RC-63)

Stop C, groups, pods and shipping. Slice 15. **What it does.** `MotionSwitch` reports every run with and without motion, and run records gain arm id, link id and parent. The `proposal` row's shape is reserved with no writer, for methodology.

**Read.** AD-14, AD-18; SWAP-CHART row 26; FUNNEL row R8.

**Gates and fallbacks.** The judge rule and the fixed-size rerun are methodology's.

**Swaps.** PH26.

**Depends on.** RC-25.

**Files.**

- [ ] Edit `qmb/src/qmb/results/journal.py`.
- [ ] Edit `qml/src/qml/motion/engine.py`.
- [ ] Edit `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`.
- [ ] Create `qmb/tests/test_run_arms.py`.

**Build.**

- [ ] Add the report and the fields. `tries.py` keeps counting until methodology changes it.

**You see.**

- [ ] Reports show what a learned number added, and what it cost.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_run_reports_both_arms`. A run reads `motion_on` and `motion_off` with their literal trade counts.
- [ ] `test_the_proposal_row_has_no_writer`. Its shape exists, and a grep of the writers finds none.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmb/tests -k unit`, `qml/tests`, `qmn/tests/test_app_runtime.py`, `packages/qmf-data/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the dummy with motion on through QMB. Save `check-two-arms.log`. Pass when both arms print.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses verification-gap. The blast-radius fact is this. The effective-tries count is unchanged, by the judge's shipped tests.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-63-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Keep a unit's record when a placeholder is swapped (RC-64)

Stop C, groups, pods and shipping. Slice 16. **What it does.** A forwarding map declares old block version to new with a parameter transform, and the identity table is wired so promote and the judge classify a swap. A sizer-only swap keeps the logic record, an exit change is a counted try, and a deployment gains `succeeds`.

**Read.** SPINE section 7 "Versions and migrations"; SWAP-CHART rows 1, E16; FUNNEL row R17.

**Gates and fallbacks.** None.

**Swaps.** PH1 E16.

**Depends on.** RC-55, RC-28.

**Files.**

- [ ] Edit `qml/src/qml/identity/table.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/promote.py`.
- [ ] Edit `qmx-agents/packages/qmx-host/src/qmx_host/lifecycle.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qml/src/qml/check/layers.py`.
- [ ] Create `qml/src/qml/identity/forward.py`.
- [ ] Create `qml/tests/test_forwarding.py`.

**Build.**

- [ ] Declare `fixed-fraction-at-stop@1 -> @3`.
- [ ] Call `classify` from promote and the judge. A new version may enter while the old keeps only its exits until flat.

**You see.**

- [ ] Replacing a stand-in doesn't throw away what a unit already proved.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_sizer_swap_keeps_the_logic_record`. Trade count before and after equal, money record new.
- [ ] `test_an_exit_change_is_a_counted_try`. Tries +1.
- [ ] `test_succeeds_drains_the_old`. Old takes no entry and its exits fire until flat.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, `qmx-agents/packages/qmx-host/tests`, `qmn/tests -k app`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Swap a placeholder on the fake lane with a trade open. Save `check-swap.log`. Pass when the old drains, the new enters, one record.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. Old trade rows read correctly after RC-28's rename, by the forwarding test on a stored journal.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-64-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Re-test every deployed unit after a compiler bump (RC-65)

Stop C, groups, pods and shipping. Slice 16. **What it does.** After a format bump, G reruns per deployed unit on its recorded slice on a worker pool, and the report says which changed behaviour. The node refuses the bump until the report exists.

**Read.** SPINE section 7 "Re-test workflow"; FUNNEL row K8; OPEN row 13.

**Gates and fallbacks.** Wall time may push this to a nightly schedule. Never inline.

**Depends on.** RC-64.

**Files.**

- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Create `qmx-agents/packages/qmx-host/src/qmx_host/retest.py`.
- [ ] Create `qmx-agents/packages/qmx-host/tests/test_retest.py`.

**Build.**

- [ ] Write the workflow and the refusal.

**You see.**

- [ ] Upgrading the compiler can't silently change what's trading.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_bump_with_no_report_is_refused`. Format 6 on a unit recorded at 5 answers `retest_missing`.
- [ ] `test_a_changed_unit_is_named`. Two units, one block changed, the report names one.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, `qmx-agents/packages/qmx-host/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run a bump over 5 fixture deployments. Save `check-retest.log`. Pass when report written, node accepts after it.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case. The blast-radius fact is this. The re-test touches no live deployment, by a recording store.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-65-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Finish the guide and ready stop point C (RC-66)

Stop C, groups, pods and shipping. Slice 16. **What it does.** The developer guide gets its add-a-thing pages, each ending in the test that proves it. The money app's version moves once and the whole-repo check runs, and this PR is stop point C.

**Read.** SPINE section 7; OPEN rows 8, 8a.

**Gates and fallbacks.** G-SIGN.

**Depends on.** RC-52, RC-56, RC-57, RC-60, RC-62, RC-63, RC-65.

**Files.**

- [ ] Edit `tools/qml/extending.py`.
- [ ] Edit `qml/EXTENDING.md`.
- [ ] Edit `qmx-agents/apps/trading-node/app.toml`.
- [ ] Edit `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py`.
- [ ] Create `tools/lanes/release_note_stop_c.md`.

**Build.**

- [ ] Finish the seven "Adding" pages, and bump rows and digests.

**You see.**

- [ ] Stop point C. The baseline with groups, pods and shipping. One line to sign, and nothing live until slice 17 or a re-test.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_each_adding_page_names_its_test`. Each of the seven pages ends in a test path that exists, a literal check.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `tools/tests`, `qml/tests`, `qmx-agents/apps/trading-node/tests`, `qmx-agents/packages/qmx-apps/tests`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. Run the whole-repo check at the head. Save `check-whole-c.log`. Pass when nothing fails beyond the named baseline reds.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses verification-gap. The blast-radius fact is this. No PR in this program gave an agent a path to money, by `tools/money_path_scan.py` and K9 8 at the head.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-66-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Sign the stop and amend it with a read-back (RC-67)

After stop C, the demo facts. Slice 17. **What it does.** Stop distance is signed at the venue encoder only, and stops only tighten unless `allow_widen` is set. Amends go out with read-back, and `Blocked` for a stop past entry lifts.

**Read.** AD-13 step 3; SWAP-CHART row 9; `handoff/FOR-REPAIR-SOCKET.md` sections 3 and 4; R24's probes.

**Gates and fallbacks.** G-DEMO. Built on the fake broker, and its demo lane runs after he signs in. Until R24 answers whether an amend wipes the other level, every amend sends both levels.

**Swaps.** PH9.

**Depends on.** RC-66.

**Files.**

- [ ] Edit `packages/qmf-venue/src/qmf/venue/encode.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmn/src/qmn/order/amend.py`.
- [ ] Edit `qml/src/qml/protocol/exits.py`.
- [ ] Create `qmn/tests/test_app_signed_stop.py`.

**Build.**

- [ ] Move `_move_stop` to an absolute level with the encoder signing it. Restore a lost stop from the latest accepted amend row.

**You see.**

- [ ] A trade can move its stop past breakeven, and the node checks the broker took it.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_short_past_entry_encodes_signed`. A short entered at 1.1000 with new stop 1.0990 encodes the signed distance -0.0010.
- [ ] `test_widen_refuses_unless_allowed`. Answers `stop_widen` with `allow_widen` false.
- [ ] `test_an_amend_sends_both_levels`. The recorded message carries stop and target.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `packages/qmf-venue/tests`, `qmn/tests -k app`, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. After G-DEMO, run the amend probe on his demo account. Save `check-demo-amend.log`. Pass when the read-back equals what was sent.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. `abs(entry - new_stop)` is gone from every path, by grep.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-67-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Close part of a position and trail on the node (RC-68)

After stop C, the demo facts. Slice 17. **What it does.** The node executes `close_partial` with a quantity, and trails run through `amend_protection`. A moved number may now reach an open position where its row says `applies_to_open_positions`.

**Read.** AD-13 step 3, AD-14; SWAP-CHART rows 2, 3, 8, 10.

**Gates and fallbacks.** G-DEMO for its demo lane. A rest under the minimum lot closes in full.

**Swaps.** PH2 PH3 PH8 PH10.

**Depends on.** RC-67.

**Files.**

- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `qmb/src/qmb/host/unit_handler.py`.
- [ ] Edit `qml/src/qml/protocol/exits.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Edit `qml/src/qml/protocol/unit.py`.
- [ ] Create `qmn/tests/test_app_partials.py`.

**Build.**

- [ ] Close with a quantity at `runtime.py:1807-1808`. Lift `fraction < 1`.

**You see.**

- [ ] A unit can take part off and let the rest run.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_half_off_leaves_half`. 1.00 lots with fraction 0.5 closes 0.50 and 0.50 remains, R booked for the half.
- [ ] `test_a_rest_under_min_closes_in_full`. 0.015 at min 0.01 with fraction 0.5 closes all with reason `partial_full`.
- [ ] `test_a_trail_moves_the_stop_each_bar`. Trail 10 pips reads the literal stop column.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `qmn/tests -k app`, `qmb/tests -k unit`, `qml/tests`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. After G-DEMO, take a partial on his demo account. Save `check-demo-partial.log`. Pass when the venue's position equals the handler's.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. A close on a position already gone doesn't raise, by R24's probe answer once known, otherwise by the fake.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-68-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Rest targets at the venue, add entry forms, and set netting per venue (RC-69)

After stop C, the demo facts. Slice 17. **What it does.** Targets may rest at the venue per R24's facts, entries may be limit or stop through `OrderSpec`, and two units on one netting symbol stay refused until attribution exists. This ends the program.

**Read.** AD-13, FUNNEL row S18; SWAP-CHART rows 21, E14; `handoff/FOR-REPAIR-SOCKET.md` section 4.

**Gates and fallbacks.** G-DEMO. If R24 shows node-closed targets don't lose on wicks, the venue target stays deferred and this PR ships only `OrderSpec`.

**Swaps.** PH21 E14.

**Depends on.** RC-68.

**Files.**

- [ ] Edit `packages/qmf-venue/src/qmf/venue/encode.py`.
- [ ] Edit `qmn/src/qmn/venue/ctrader_account.py`.
- [ ] Edit `qmn/src/qmn/app/runtime.py`.
- [ ] Edit `packages/qmf-risk/src/qmf/risk/unit_intent.py`.
- [ ] Edit `qml/src/qml/compile/compiler.py`.
- [ ] Create `qmn/tests/test_app_venue_targets.py`.

**Build.**

- [ ] Add `relativeTakeProfit` to the encoder and `OrderSpec` on the intent.

**You see.**

- [ ] Live and backtest agree on where a target fills.

**Verify, unit.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] `test_a_target_rests_with_the_entry`. The message carries the target distance 0.0100.
- [ ] `test_a_limit_entry_keeps_its_price`. `OrderSpec(limit, 1.0990)` sends that price.
- [ ] `test_two_units_on_one_netting_symbol_refuse`. Answers `netting_not_attributed`.

**Verify, live.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked. Ten lanes on `haiku` at the PR head, per the boot recipe. Lanes 1 to 4 are the proving set and most need no model. Lanes 5 to 10 are the menu, and the coordinator runs one only if the done line depends on it.

- [ ] Lane 1. Touched suites at the head, `packages/qmf-venue/tests`, `qmn/tests -k app`, `packages/qmf-risk/tests`, `qml/tests`, `qmb/tests -k unit`, `qmn/tests/test_app_runtime.py`, and rerun at the parent only a test that failed. Save `check-suites.log`. Pass when the head fails nothing the parent passes, beyond the baseline reds in Appendix E.
- [ ] Lane 2. Run this PR's new tests at the parent, with the test files copied in, and at the head. Save `check-red-green.log`. Pass when the behaviour tests fail at the parent and pass at the head.
- [ ] Lane 3. After G-DEMO, run the wick probe on his demo account. Save `check-demo-wick.log`. Pass when the target fills at its level.
- [ ] Lane 4. Run the blast-radius fact in the review gate at the head with a real script. Save `check-fact.log`. Pass when the script exits 0 and prints the fact.
- [ ] Lane 5. Run the PR's new tests three times in a row. Save `check-repeat.log`. Pass when the three runs agree.
- [ ] Lane 6. Grep every lane log of this PR for key, token and password values. Save `check-leak.log`. Pass when none appears.
- [ ] Lane 7. Start the host at the head on a fresh throwaway QMX folder through `safe_host.py`, read its health route, then stop it. Save `check-boot.log`. Pass when it answers and stops clean.
- [ ] Lane 8. Run `tools/money_path_scan.py` and `tools/secret_scan.py` at the head. Save `check-scans.log`. Pass when both exit 0.
- [ ] Lane 9. Run K7 on a throwaway folder, once RC-19 is stacked. Save `check-k7.log`. Pass when it ends in a filled paper entry.
- [ ] Lane 10. Remove the throwaway folders and the check copy, then list processes. Save `check-processes.log`. Pass when no `qmx_host`, `claude`, `node` or lane process is left.

**Verify, perf.** Tests alone are not sufficient verification. A PR is verified only when its unit, live, and perf boxes are all checked.

- [ ] Metric. Wall time of this PR's new tests, recorded, no fail rule.
- [ ] Probe. Time the run at the parent and the head, interleaved.
- [ ] Baseline. The parent's value, measured first.
- [ ] Rule. No fail rule unless the metric above names one. Recorded for the trail.

**Review gate.** A fresh Opus reviewer checks this PR before it joins the stack. Lenses edge-case, adversarial. The blast-radius fact is this. A market entry with no `OrderSpec` is byte-equal on the wire to before.

- [ ] A fresh Opus reviewer agent (`model: opus`, told not to spawn sub-agents) reads this section, the full diff and the lane logs, applies the lenses named above, and reruns the blast-radius fact. It writes `review/rc-69-check-<head8>.md`, first line CLEAN or NOT CLEAN.
- [ ] No screenshot or video is made, because no PR in this program changes a screen. The operator reviews the whole stack when he lands it.

**Merge.**

- [ ] The CLEAN verdict at the exact head, or after the one fix round.
- [ ] Lows in `lows.md`, new findings in `BACKLOG.md`, the verdict, head, parent and patch-id in `ledger.tsv`.
- [ ] Appended to the stack on `build/risk-core`. Nothing merges. He lands the stack himself.

## Close the program

- [ ] Every box above is checked with its evidence, or its PR is named in `RESUME.md` as parked or gated with the reason.
- [ ] `STACK-LIST.md` lists each PR bottom to top with its link, branch, head, plain name and verdict, for the agent that lands it, after the repair stack and the 94 earlier PRs.
- [ ] Reply to him in plain words with what now works, what is parked, and what only he can do.

## Appendix A. Prototype evidence

There is no throwaway prototype. The evidence behind the spine was run against the real code in a throw-away copy (`arch/final/CHECK.md`). Each run marked "Ran" there is rerun here as a named test (Appendix I).

Unproven until its PR runs. Real send times at a bell. Real throughput at 200 units with journals and a venue (RC-52). Real compile time per member on a roll (RC-54). Whether a Library block reaches a node end to end (RC-60). Whether cTrader takes a no-stop market order, and what an amend does to the other level (R24's probes, after G-DEMO).

## Appendix B. Not in this program

- Screens. The UI is a proposal and binds nothing. Its data needs are in `HANDOFFS.md`.
- Values. Every number is a labelled placeholder, owner the numbers talk (`PARKED-FOR-NUMBERS-TALK.md`).
- How a unit is proven valid per type. That is the methodology session.
- Who runs the fleet watch's agent layers, Shepherd, departments and memory. That is the agentic upgrade.
- Fifteen new physics readings, the finder's internals and pack contents. That is the MIS owner.
- The installer a stranger can run. That is the release session, OPEN row 8b.
- Anything trimmed by the lead (`arch/final/FIXES.md`). A group order slot, reservations as a type, the proposal tape and its size search, the Lab driver, and hung-link protection.

## Appendix C. Which PRs can run beside which

Generated from every Files block and the dependency graph. The second column lists the PRs neither of which depends on the other and which share no path. Two PRs in the third column never run at once. A PR that adds a setting may also edit `qmx-agents/packages/qmx-control/src/qmx_control/service.py` for its default, so the coordinator treats that file as shared by every such PR, and the builder names the edit in its PR body. `qml/tests/test_unit_refuses.py` moves with any PR that adds a schema field or lifts a refusal, listed or not, so it is shared the same way.

| PR | Can run beside (neither depends on the other, no shared path) | Shares a path with | The shared paths |
|---|---|---|---|
| RC-01 | none | RC-25, RC-40 | `qml/tests/test_socket_contracts.py` |
| RC-02 | none | RC-03, RC-48, RC-56, RC-66 | `qml/EXTENDING.md`, `qml/tests/test_unit_refuses.py`, `tools/qml/extending.py` |
| RC-03 | RC-05 | RC-02, RC-06, RC-11, RC-13, RC-21, RC-23, RC-24, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-45, RC-53, RC-56, RC-58, RC-68, RC-69 | `qml/src/qml/compile/compiler.py`, `qml/src/qml/unit/model.py`, `qml/src/qml/unit/parse.py`, `qml/src/qml/unit/qmx.unit.1.schema.json` and more |
| RC-04 | RC-05 | RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-18, RC-19, RC-21, RC-22, RC-24, RC-25, RC-26, RC-27, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-49, RC-50, RC-51, RC-54, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/protocol/unit.py`, `qmn/src/qmn/app/runtime.py`, `qmx-agents/packages/qmx-host/src/qmx_host/promote.py` |
| RC-05 | RC-03, RC-04 | RC-11, RC-13, RC-17, RC-21, RC-27, RC-28, RC-34, RC-40, RC-45 | `packages/qmf-risk/src/qmf/risk/facts.py`, `qml/src/qml/blocks/api.py`, `qml/src/qml/numbers/convert.py`, `qml/src/qml/numbers/records.py` |
| RC-06 | none | RC-03, RC-04, RC-07, RC-08, RC-09, RC-10, RC-11, RC-12, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-27, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-53, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/unit.py`, `qml/src/qml/unit/templates/dummy-trend-pullback.json` and more |
| RC-07 | none | RC-04, RC-06, RC-08, RC-10, RC-11, RC-14, RC-15, RC-16, RC-19, RC-25, RC-26, RC-27, RC-28, RC-30, RC-31, RC-32, RC-33, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-49, RC-50, RC-51, RC-55, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmb/src/qmb/host/facts.py`, `qmb/src/qmb/host/unit_handler.py`, `qmn/src/qmn/app/facts.py`, `qmn/src/qmn/app/runtime.py` |
| RC-08 | RC-29 | RC-04, RC-06, RC-07, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-18, RC-19, RC-21, RC-22, RC-24, RC-25, RC-26, RC-27, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-56, RC-58, RC-60, RC-63, RC-64, RC-65, RC-67, RC-68, RC-69 | `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`, `qmb/src/qmb/results/journal.py`, `qml/src/qml/protocol/unit.py`, `qml/src/qml/receipt.py` and more |
| RC-09 | RC-27, RC-29 | RC-04, RC-06, RC-08, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-21, RC-22, RC-24, RC-25, RC-26, RC-28, RC-31, RC-32, RC-33, RC-34, RC-35, RC-42, RC-43, RC-45, RC-55, RC-56, RC-58, RC-63, RC-68 | `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`, `qml/src/qml/protocol/unit.py` |
| RC-10 | RC-29 | RC-04, RC-06, RC-07, RC-08, RC-09, RC-11, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-22, RC-24, RC-25, RC-26, RC-27, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/protocol/unit.py`, `qmn/src/qmn/app/runtime.py` |
| RC-11 | RC-27, RC-29 | RC-03, RC-04, RC-05, RC-06, RC-07, RC-08, RC-09, RC-10, RC-13, RC-14, RC-15, RC-16, RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-40, RC-42, RC-43, RC-45, RC-53, RC-55, RC-56, RC-58, RC-67, RC-68, RC-69 | `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/blocks/api.py`, `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/exits.py` and more |
| RC-12 | RC-13, RC-14, RC-15, RC-16, RC-21, RC-22, RC-27, RC-29, RC-30, RC-31, RC-32, RC-33, RC-34 | RC-06, RC-23 | `qml/src/qml/unit/templates/dummy-trend-pullback.json` |
| RC-13 | RC-12, RC-27, RC-29, RC-30 | RC-03, RC-04, RC-05, RC-06, RC-08, RC-09, RC-10, RC-11, RC-14, RC-16, RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-40, RC-41, RC-42, RC-43, RC-45, RC-53, RC-55, RC-56, RC-58, RC-68, RC-69 | `packages/qmf-risk/src/qmf/risk/controls.py`, `qml/src/qml/blocks/api.py`, `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/controls.py` and more |
| RC-14 | RC-12, RC-29 | RC-04, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-15, RC-16, RC-19, RC-21, RC-22, RC-24, RC-25, RC-26, RC-27, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `packages/qmf-risk/src/qmf/risk/controls.py`, `qml/src/qml/fold.py`, `qml/src/qml/protocol/unit.py`, `qmn/src/qmn/app/runtime.py` |
| RC-15 | RC-12, RC-21, RC-22, RC-29, RC-34 | RC-04, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-14, RC-16, RC-18, RC-19, RC-25, RC-26, RC-27, RC-28, RC-30, RC-31, RC-32, RC-33, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-58, RC-60, RC-63, RC-64, RC-65, RC-67, RC-68, RC-69 | `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`, `qmb/src/qmb/host/unit_handler.py`, `qmb/src/qmb/results/journal.py`, `qmn/src/qmn/app/runtime.py` |
| RC-16 | RC-12, RC-29 | RC-04, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-18, RC-19, RC-21, RC-22, RC-24, RC-25, RC-26, RC-27, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qml/src/qml/lifecycle/machine.py`, `qml/src/qml/protocol/controls.py`, `qml/src/qml/protocol/unit.py`, `qmn/src/qmn/app/runtime.py` |
| RC-17 | RC-21, RC-22, RC-27, RC-30, RC-31, RC-32, RC-33, RC-34 | RC-05, RC-23, RC-28, RC-29, RC-47, RC-52, RC-54, RC-59, RC-62 | `qml/src/qml/numbers/records.py`, `qml/src/qml/unit/templates/canary.json`, `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`, `qmx-agents/packages/qmx-tools/src/qmx_tools/unit_check.py` |
| RC-18 | RC-21, RC-22, RC-23, RC-24, RC-26, RC-27, RC-29, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-38, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-47 | RC-04, RC-08, RC-15, RC-16, RC-25, RC-28, RC-49, RC-54, RC-60, RC-63, RC-64 | `qmb/src/qmb/results/journal.py`, `qml/src/qml/lifecycle/machine.py`, `qmx-agents/packages/qmx-host/src/qmx_host/lifecycle.py`, `qmx-agents/packages/qmx-host/src/qmx_host/promote.py` |
| RC-19 | RC-21, RC-22, RC-23, RC-24, RC-25, RC-28, RC-29, RC-33, RC-34, RC-35, RC-38, RC-47, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-10, RC-14, RC-15, RC-16, RC-26, RC-27, RC-30, RC-31, RC-32, RC-36, RC-37, RC-39, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmn/src/qmn/app/paper_lane.py`, `qmn/src/qmn/app/runtime.py`, `qmx-agents/packages/qmx-host/tests/k7_rehearsal.py` |
| RC-20 | RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-27, RC-28, RC-29, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-38, RC-39, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-47, RC-49, RC-50, RC-51, RC-52, RC-53, RC-54, RC-55, RC-56, RC-57, RC-58, RC-59, RC-60, RC-61, RC-63, RC-64, RC-65, RC-67, RC-68, RC-69 | RC-48, RC-62, RC-66 | `qmx-agents/apps/trading-node/app.toml`, `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py` |
| RC-21 | RC-12, RC-15, RC-17, RC-18, RC-19, RC-20, RC-27, RC-28, RC-29, RC-30, RC-37, RC-38, RC-41, RC-44, RC-46, RC-47, RC-63 | RC-03, RC-04, RC-05, RC-06, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-16, RC-22, RC-23, RC-24, RC-25, RC-26, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-40, RC-42, RC-43, RC-45, RC-53, RC-55, RC-56, RC-58, RC-68, RC-69 | `qml/src/qml/blocks/api.py`, `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/unit.py`, `qml/src/qml/receipt.py` |
| RC-22 | RC-12, RC-15, RC-17, RC-18, RC-19, RC-20, RC-23, RC-27, RC-28, RC-29, RC-30, RC-36, RC-37, RC-38, RC-40, RC-44, RC-46, RC-47, RC-63 | RC-04, RC-06, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-16, RC-21, RC-24, RC-25, RC-26, RC-31, RC-32, RC-33, RC-34, RC-35, RC-41, RC-42, RC-43, RC-45, RC-50, RC-55, RC-56, RC-58, RC-68 | `packages/qmf-risk/src/qmf/risk/controls.py`, `qml/src/qml/fold.py`, `qml/src/qml/protocol/unit.py` |
| RC-23 | RC-18, RC-19, RC-20, RC-22, RC-27, RC-29, RC-30 | RC-03, RC-06, RC-11, RC-12, RC-13, RC-17, RC-21, RC-24, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-45, RC-53, RC-56, RC-58, RC-64, RC-68, RC-69 | `qml/src/qml/check/layers.py`, `qml/src/qml/compile/compiler.py`, `qml/src/qml/unit/model.py`, `qml/src/qml/unit/parse.py` and more |
| RC-24 | RC-18, RC-19, RC-20, RC-27, RC-29, RC-30 | RC-03, RC-04, RC-06, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-16, RC-21, RC-22, RC-23, RC-25, RC-26, RC-28, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-42, RC-43, RC-45, RC-53, RC-55, RC-56, RC-58, RC-63, RC-68, RC-69 | `qml/src/qml/compile/compiler.py`, `qml/src/qml/motion/engine.py`, `qml/src/qml/protocol/unit.py`, `qml/src/qml/unit/model.py` |
| RC-25 | RC-19, RC-20, RC-27, RC-29 | RC-01, RC-04, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-18, RC-21, RC-22, RC-24, RC-26, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-40, RC-42, RC-43, RC-45, RC-55, RC-56, RC-58, RC-63, RC-68 | `qmb/src/qmb/host/unit_handler.py`, `qmb/src/qmb/results/journal.py`, `qml/src/qml/motion/engine.py`, `qml/src/qml/protocol/unit.py` and more |
| RC-26 | RC-18, RC-20, RC-29, RC-38, RC-47, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-22, RC-24, RC-25, RC-27, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/protocol/unit.py`, `qmn/src/qmn/app/runtime.py` |
| RC-27 | RC-09, RC-11, RC-12, RC-13, RC-17, RC-18, RC-20, RC-21, RC-22, RC-23, RC-24, RC-25, RC-33, RC-34, RC-63 | RC-04, RC-05, RC-06, RC-07, RC-08, RC-10, RC-14, RC-15, RC-16, RC-19, RC-26, RC-28, RC-30, RC-31, RC-32, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-49, RC-50, RC-51, RC-55, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `packages/qmf-risk/src/qmf/risk/facts.py`, `qmb/src/qmb/host/facts.py`, `qmn/src/qmn/app/facts.py`, `qmn/src/qmn/app/runtime.py` and more |
| RC-28 | RC-19, RC-20, RC-21, RC-22, RC-29, RC-34 | RC-04, RC-05, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-15, RC-17, RC-18, RC-24, RC-25, RC-26, RC-27, RC-30, RC-31, RC-32, RC-33, RC-37, RC-40, RC-42, RC-43, RC-45, RC-49, RC-58, RC-63, RC-68 | `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`, `qmb/src/qmb/host/facts.py`, `qmb/src/qmb/host/unit_handler.py`, `qmb/src/qmb/results/journal.py` and more |
| RC-29 | RC-08, RC-09, RC-10, RC-11, RC-12, RC-13, RC-14, RC-15, RC-16, RC-18, RC-19, RC-20, RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-38, RC-39, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-47, RC-63 | RC-17 | `qmx-agents/packages/qmx-tools/src/qmx_tools/unit_check.py` |
| RC-30 | RC-12, RC-13, RC-17, RC-18, RC-20, RC-21, RC-22, RC-23, RC-24, RC-29, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-10, RC-11, RC-14, RC-15, RC-16, RC-19, RC-25, RC-26, RC-27, RC-28, RC-31, RC-32, RC-33, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmb/src/qmb/host/unit_handler.py`, `qmn/src/qmn/app/runtime.py`, `qmn/src/qmn/venue/ctrader_account.py` |
| RC-31 | RC-12, RC-17, RC-18, RC-20, RC-29, RC-63 | RC-03, RC-04, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-27, RC-28, RC-30, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-53, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/unit.py`, `qmn/src/qmn/app/runtime.py` |
| RC-32 | RC-12, RC-17, RC-18, RC-20, RC-29, RC-63 | RC-03, RC-04, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-27, RC-28, RC-30, RC-31, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-53, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `packages/qmf-risk/src/qmf/risk/unit_intent.py`, `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/unit.py` and more |
| RC-33 | RC-12, RC-17, RC-18, RC-19, RC-20, RC-27, RC-29, RC-63 | RC-03, RC-04, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-28, RC-30, RC-31, RC-32, RC-34, RC-35, RC-36, RC-40, RC-42, RC-43, RC-45, RC-53, RC-55, RC-56, RC-58, RC-68, RC-69 | `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/unit.py`, `qml/src/qml/unit/model.py` |
| RC-34 | RC-12, RC-15, RC-17, RC-18, RC-19, RC-20, RC-27, RC-28, RC-29, RC-63 | RC-03, RC-04, RC-05, RC-06, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-16, RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-31, RC-32, RC-33, RC-35, RC-36, RC-40, RC-42, RC-43, RC-45, RC-53, RC-55, RC-56, RC-58, RC-68, RC-69 | `qml/src/qml/blocks/api.py`, `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/unit.py` |
| RC-35 | RC-18, RC-19, RC-20, RC-29, RC-63 | RC-03, RC-04, RC-06, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-16, RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-31, RC-32, RC-33, RC-34, RC-36, RC-38, RC-42, RC-43, RC-45, RC-53, RC-55, RC-56, RC-58, RC-68, RC-69 | `qml/src/qml/blocks/stdlib/sqs-floor/1/block.py`, `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/entry_chain.py`, `qml/src/qml/protocol/unit.py` |
| RC-36 | RC-18, RC-20, RC-22, RC-29, RC-38, RC-63 | RC-03, RC-04, RC-06, RC-07, RC-08, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-23, RC-24, RC-26, RC-27, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-53, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/controls.py`, `qml/src/qml/protocol/entry_chain.py`, `qmn/src/qmn/app/runtime.py` |
| RC-37 | RC-18, RC-20, RC-21, RC-22, RC-29, RC-39, RC-47, RC-48, RC-52, RC-53, RC-54, RC-56, RC-57, RC-59, RC-61, RC-62, RC-63, RC-66 | RC-04, RC-06, RC-07, RC-08, RC-10, RC-14, RC-15, RC-16, RC-19, RC-26, RC-27, RC-28, RC-30, RC-31, RC-32, RC-36, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-49, RC-50, RC-51, RC-55, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmn/src/qmn/app/facts.py`, `qmn/src/qmn/app/runtime.py` |
| RC-38 | RC-18, RC-19, RC-20, RC-21, RC-22, RC-26, RC-29, RC-36, RC-39, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-47, RC-48, RC-49, RC-50, RC-51, RC-52, RC-53, RC-54, RC-55, RC-56, RC-57, RC-58, RC-59, RC-60, RC-61, RC-62, RC-63, RC-64, RC-65, RC-66, RC-67, RC-68, RC-69 | RC-35 | `qml/src/qml/blocks/stdlib/sqs-floor/1/block.py` |
| RC-39 | RC-20, RC-29, RC-37, RC-38, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-47, RC-63 | RC-19 | `qmx-agents/packages/qmx-host/tests/k7_rehearsal.py` |
| RC-40 | RC-18, RC-20, RC-22, RC-29, RC-38, RC-39, RC-47, RC-63 | RC-01, RC-04, RC-05, RC-06, RC-07, RC-08, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-25, RC-26, RC-27, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-36, RC-37, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/blocks/api.py`, `qml/tests/test_socket_contracts.py`, `qmn/src/qmn/app/runtime.py` |
| RC-41 | RC-18, RC-20, RC-21, RC-29, RC-38, RC-39, RC-47, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-10, RC-13, RC-14, RC-15, RC-16, RC-19, RC-22, RC-26, RC-27, RC-30, RC-31, RC-32, RC-36, RC-37, RC-40, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `packages/qmf-risk/src/qmf/risk/controls.py`, `qmn/src/qmn/app/node_links.py`, `qmn/src/qmn/app/runtime.py` |
| RC-42 | RC-18, RC-20, RC-29, RC-38, RC-39, RC-47, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-22, RC-24, RC-25, RC-26, RC-27, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/protocol/unit.py`, `qmn/src/qmn/app/outbox.py`, `qmn/src/qmn/app/runtime.py` |
| RC-43 | RC-18, RC-20, RC-29, RC-38, RC-39, RC-47, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-22, RC-24, RC-25, RC-26, RC-27, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/protocol/unit.py`, `qmn/src/qmn/app/outbox.py`, `qmn/src/qmn/app/runtime.py` |
| RC-44 | RC-18, RC-20, RC-21, RC-22, RC-29, RC-38, RC-39, RC-47, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-10, RC-14, RC-15, RC-16, RC-19, RC-26, RC-27, RC-30, RC-31, RC-32, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-45, RC-46, RC-50, RC-51, RC-55, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmn/src/qmn/app/outbox.py`, `qmn/src/qmn/app/runtime.py` |
| RC-45 | RC-18, RC-20, RC-29, RC-38, RC-39, RC-47, RC-63 | RC-03, RC-04, RC-05, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-27, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-46, RC-50, RC-51, RC-53, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/compile/compiler.py`, `qml/src/qml/numbers/convert.py`, `qml/src/qml/protocol/unit.py` and more |
| RC-46 | RC-18, RC-20, RC-21, RC-22, RC-29, RC-38, RC-39, RC-47, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-10, RC-14, RC-15, RC-16, RC-19, RC-26, RC-27, RC-30, RC-31, RC-32, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-50, RC-51, RC-55, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmn/src/qmn/app/paper_lane.py`, `qmn/src/qmn/app/runtime.py`, `qmn/src/qmn/venue/ctrader_account.py` |
| RC-47 | RC-18, RC-19, RC-20, RC-21, RC-22, RC-26, RC-29, RC-37, RC-38, RC-39, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-63 | RC-17, RC-52, RC-54, RC-59, RC-62 | `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`, `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`, `qmx-agents/packages/qmx-tools/tests/test_tools.py`, `qmx-agents/plugin/skills/build-unit/SKILL.md` |
| RC-48 | RC-37, RC-38, RC-63 | RC-02, RC-20, RC-62, RC-66 | `qml/EXTENDING.md`, `qmx-agents/apps/trading-node/app.toml`, `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py`, `tools/qml/extending.py` |
| RC-49 | RC-20, RC-38, RC-53, RC-58, RC-59, RC-61, RC-63 | RC-04, RC-07, RC-18, RC-27, RC-28, RC-37, RC-54, RC-60, RC-64 | `qmn/src/qmn/app/facts.py`, `qmx-agents/packages/qmx-host/src/qmx_host/promote.py` |
| RC-50 | RC-20, RC-38, RC-53, RC-54, RC-56, RC-57, RC-59, RC-61, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-10, RC-14, RC-15, RC-16, RC-19, RC-22, RC-26, RC-27, RC-30, RC-31, RC-32, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-51, RC-55, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qml/src/qml/fold.py`, `qmn/src/qmn/app/node_links.py`, `qmn/src/qmn/app/outbox.py`, `qmn/src/qmn/app/runtime.py` |
| RC-51 | RC-20, RC-38, RC-53, RC-54, RC-56, RC-57, RC-59, RC-61, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-10, RC-14, RC-15, RC-16, RC-19, RC-26, RC-27, RC-30, RC-31, RC-32, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-55, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmn/src/qmn/app/runtime.py` |
| RC-52 | RC-20, RC-37, RC-38, RC-53, RC-55, RC-56, RC-57, RC-58, RC-60, RC-61, RC-63, RC-64, RC-65 | RC-17, RC-47, RC-54, RC-59, RC-62 | `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`, `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`, `qmx-agents/packages/qmx-tools/tests/test_tools.py` |
| RC-53 | RC-20, RC-37, RC-38, RC-49, RC-50, RC-51, RC-52, RC-61, RC-62, RC-63 | RC-03, RC-06, RC-11, RC-13, RC-21, RC-23, RC-24, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-45, RC-56, RC-58, RC-68, RC-69 | `qml/src/qml/compile/compiler.py`, `qml/src/qml/unit/model.py` |
| RC-54 | RC-20, RC-37, RC-38, RC-50, RC-51, RC-58, RC-61, RC-63 | RC-04, RC-17, RC-18, RC-47, RC-49, RC-52, RC-55, RC-59, RC-60, RC-62, RC-64 | `qml/src/qml/identity/table.py`, `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`, `qmx-agents/packages/qmx-host/src/qmx_host/promote.py`, `qmx-agents/packages/qmx-host/src/qmx_host/roll.py` and more |
| RC-55 | RC-20, RC-38, RC-52, RC-57, RC-59, RC-61, RC-62, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-22, RC-24, RC-25, RC-26, RC-27, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-54, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68, RC-69 | `qml/src/qml/protocol/unit.py`, `qmn/src/qmn/app/runtime.py`, `qmx-agents/packages/qmx-host/src/qmx_host/roll.py` |
| RC-56 | RC-20, RC-37, RC-38, RC-50, RC-51, RC-52, RC-57, RC-59, RC-60, RC-61, RC-62, RC-63, RC-64, RC-65 | RC-02, RC-03, RC-04, RC-06, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-16, RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-42, RC-43, RC-45, RC-53, RC-55, RC-58, RC-68, RC-69 | `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/unit.py`, `qml/src/qml/unit/model.py`, `qml/src/qml/unit/sections.py` and more |
| RC-57 | RC-20, RC-37, RC-38, RC-50, RC-51, RC-52, RC-55, RC-56, RC-58, RC-59, RC-60, RC-61, RC-62, RC-63, RC-64, RC-65 | none |  |
| RC-58 | RC-20, RC-38, RC-49, RC-52, RC-54, RC-57, RC-59, RC-61, RC-62 | RC-03, RC-04, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-27, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-53, RC-55, RC-56, RC-60, RC-63, RC-64, RC-65, RC-67, RC-68, RC-69 | `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`, `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/unit.py`, `qml/src/qml/unit/model.py` and more |
| RC-59 | RC-20, RC-37, RC-38, RC-49, RC-50, RC-51, RC-55, RC-56, RC-57, RC-58, RC-63, RC-64, RC-65 | RC-17, RC-47, RC-52, RC-54, RC-61, RC-62 | `qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py`, `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`, `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`, `qmx-agents/packages/qmx-tools/tests/test_tools.py` and more |
| RC-60 | RC-20, RC-38, RC-52, RC-56, RC-57, RC-61, RC-62, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-10, RC-14, RC-15, RC-16, RC-18, RC-19, RC-26, RC-27, RC-30, RC-31, RC-32, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-49, RC-50, RC-51, RC-54, RC-55, RC-58, RC-64, RC-65, RC-67, RC-68, RC-69 | `qmn/src/qmn/app/runtime.py`, `qmx-agents/packages/qmx-host/src/qmx_host/promote.py` |
| RC-61 | RC-20, RC-37, RC-38, RC-49, RC-50, RC-51, RC-52, RC-53, RC-54, RC-55, RC-56, RC-57, RC-58, RC-60, RC-63, RC-64, RC-65 | RC-59 | `qmx-agents/packages/qmx-apps/src/qmx_apps/manifest.py` |
| RC-62 | RC-37, RC-38, RC-53, RC-55, RC-56, RC-57, RC-58, RC-60, RC-63, RC-64, RC-65 | RC-17, RC-20, RC-47, RC-48, RC-52, RC-54, RC-59, RC-66 | `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py`, `qmx-agents/packages/qmx-control/src/qmx_control/catalog.py`, `qmx-agents/packages/qmx-tools/src/qmx_tools/functions.py`, `qmx-agents/packages/qmx-tools/tests/test_tools.py` |
| RC-63 | RC-19, RC-20, RC-21, RC-22, RC-26, RC-27, RC-29, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-38, RC-39, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-47, RC-48, RC-49, RC-50, RC-51, RC-52, RC-53, RC-54, RC-55, RC-56, RC-57, RC-59, RC-60, RC-61, RC-62, RC-64, RC-65 | RC-08, RC-09, RC-15, RC-18, RC-24, RC-25, RC-28, RC-58 | `packages/qmf-data/src/qmf/data/journal_kinds/unit.py`, `qmb/src/qmb/results/journal.py`, `qml/src/qml/motion/engine.py` |
| RC-64 | RC-20, RC-38, RC-52, RC-56, RC-57, RC-59, RC-61, RC-62, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-10, RC-14, RC-15, RC-16, RC-18, RC-19, RC-23, RC-26, RC-27, RC-30, RC-31, RC-32, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-49, RC-50, RC-51, RC-54, RC-55, RC-58, RC-60, RC-65, RC-67, RC-68, RC-69 | `qml/src/qml/check/layers.py`, `qml/src/qml/identity/table.py`, `qmn/src/qmn/app/runtime.py`, `qmx-agents/packages/qmx-host/src/qmx_host/lifecycle.py` and more |
| RC-65 | RC-20, RC-38, RC-52, RC-56, RC-57, RC-59, RC-61, RC-62, RC-63 | RC-04, RC-06, RC-07, RC-08, RC-10, RC-14, RC-15, RC-16, RC-19, RC-26, RC-27, RC-30, RC-31, RC-32, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-58, RC-60, RC-64, RC-67, RC-68, RC-69 | `qmn/src/qmn/app/runtime.py` |
| RC-66 | RC-37, RC-38 | RC-02, RC-20, RC-48, RC-62 | `qml/EXTENDING.md`, `qmx-agents/apps/trading-node/app.toml`, `qmx-agents/packages/qmx-apps/tests/test_shipped_apps.py`, `tools/qml/extending.py` |
| RC-67 | RC-20, RC-38 | RC-04, RC-06, RC-07, RC-08, RC-10, RC-11, RC-14, RC-15, RC-16, RC-19, RC-26, RC-27, RC-30, RC-31, RC-32, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-55, RC-58, RC-60, RC-64, RC-65, RC-68, RC-69 | `packages/qmf-venue/src/qmf/venue/encode.py`, `qml/src/qml/protocol/exits.py`, `qmn/src/qmn/app/runtime.py` |
| RC-68 | RC-20, RC-38 | RC-03, RC-04, RC-06, RC-07, RC-08, RC-09, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-22, RC-23, RC-24, RC-25, RC-26, RC-27, RC-28, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-53, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-69 | `qmb/src/qmb/host/unit_handler.py`, `qml/src/qml/compile/compiler.py`, `qml/src/qml/protocol/exits.py`, `qml/src/qml/protocol/unit.py` and more |
| RC-69 | RC-20, RC-38 | RC-03, RC-04, RC-06, RC-07, RC-08, RC-10, RC-11, RC-13, RC-14, RC-15, RC-16, RC-19, RC-21, RC-23, RC-24, RC-26, RC-27, RC-30, RC-31, RC-32, RC-33, RC-34, RC-35, RC-36, RC-37, RC-40, RC-41, RC-42, RC-43, RC-44, RC-45, RC-46, RC-50, RC-51, RC-53, RC-55, RC-56, RC-58, RC-60, RC-64, RC-65, RC-67, RC-68 | `packages/qmf-risk/src/qmf/risk/unit_intent.py`, `packages/qmf-venue/src/qmf/venue/encode.py`, `qml/src/qml/compile/compiler.py`, `qmn/src/qmn/app/runtime.py` and more |

## Appendix D. Defaults and the plan's own calls

The spine's `arch/final/OPEN.md` holds every open row with its default. The build runs on each default and never waits. Calls this plan added.

- One version bump of the money app per stop point (RC-20, RC-48, RC-66), not one per PR as the repair did, because one signed release per stop point is the spine's rule and `app.toml` on every row would force one builder at a time. A PR that changes a file under an app folder still bumps that app's version in its own Files block.
- Lane 1 runs touched suites only. The whole repo runs after every eighth PR and at each stop point.
- Ids are `RC-nn`, chosen to clash with no spine word.
- The build continues past stop B on the default for OPEN row 1. See Appendix H.

## Appendix E. Gates and his steps

- G-SIGN. One line to sign per stop point. A stop point isn't reached until he has signed. No PR waits for it.
- G-DEMO. His cTrader demo sign-in, on cTrader's own page, after he lands the stack. The demo lanes of RC-27, RC-67, RC-68 and RC-69 and R24's lanes 5 and 6 wait for it. RC-67 to RC-69 are built and checked on the fake broker meanwhile.
- G-LAND. Real steps on his own QMX folder run only on code he has landed. The repair stack and the 94 earlier PRs land first.
- Baseline reds at the root, never a PR's fault. `qmn/tests/test_app_grants.py::test_the_windows_store_writes_reads_and_deletes_one_throwaway_entry`, `tests/test_maintenance.py::test_the_upkeep_switched_off_never_runs_while_rounds_and_the_drill_still_do`, and the quality gates `fmt-check-qmx-apps` and `types-qmx-host` (`D:/QMX-worktrees/repair-ship/STACK-LIST.md`).

## Appendix F. The swap ledger

Every placeholder (`RISK-SIZING-PLACEHOLDERS.md`) and every socket (`unit-baseline/SWAP-CHART.md`) to the PRs that swap it. Generated from each section's declaration, and `plan-parts/check_program.py` fails on a missing row.

| Row | What | Verdict | PR |
|---|---|---|---|
| PH 1 | Sizer `fixed-fraction-at-stop@1` | WIDEN then SWAP | RC-06, RC-28, RC-64 |
| PH 2 | Stop `swing-stop-buffer@1` | WIDEN | RC-12, RC-68 |
| PH 3 | Target `target-r-multiple@1` | WIDEN | RC-12, RC-25, RC-68 |
| PH 4 | Time exit `time-exit-bars@1` | WIDEN | RC-12 |
| PH 5 | Halts | WIRE and WIDEN | RC-13, RC-16 |
| PH 6 | Cross-unit hook | WIDEN and WIRE | RC-40 |
| PH 7 | Motion of risk numbers | WIDEN | RC-24, RC-25 |
| PH 8 | Moved values and open positions | WIDEN | RC-26, RC-68 |
| PH 9 | Stop amendments | WIRE and WIDEN | RC-11, RC-67 |
| PH 10 | Partial closes | WIRE, WIDEN | RC-11, RC-68 |
| PH 11 | No price stop | WIDEN | RC-45, RC-46 |
| PH 12 | Rounding, minimum lot | WIDEN | RC-05 |
| PH 13 | Gap through the stop | KEEP, a fact | RC-28 |
| PH 14 | Margin and liquidation | WIRE then WIDEN | RC-27, RC-41 |
| PH 15 | Leverage and spec changes | WIRE | RC-36 |
| PH 16 | Funding and swaps | KEEP, a fact | RC-28 |
| PH 17 | Account facts | WIDEN | RC-27 |
| PH 18 | Kill effects per level | WIDEN | RC-41 |
| PH 19 | Protection that cannot be placed | WIDEN | RC-41 |
| PH 20 | Kill line's verb | WIRE | RC-51 |
| PH 21 | Two units on one netting symbol | WIDEN | RC-69 |
| PH 22 | Starting numbers for live | SWAP | RC-26 |
| PH 23 | The one automatic move | WIRE | RC-16 |
| PH 24 | Paper after a risk stop | SWAP | RC-16 |
| PH 25 | Risk events in journals | WIRE | RC-15 |
| PH 26 | Judge with unit sizer and fixed size | WIRE | RC-63 |
| PH 27 | Correlated judging | KEEP | RC-50 |
| PH 28 | Decay alarm | SWAP and WIRE | RC-62 |
| PH 29 | Fields to replay sizing | WIRE | RC-08, RC-15, RC-28 |
| PH 30 | Size the venue receives | KEEP, test kept | RC-05, RC-48 |
| PH 31 | Pods | Built here | RC-53 |
| E1 | `reads` refused | WIDEN | RC-58 |
| E2 | Eleven roles do not run | WIDEN per role | RC-21, RC-34 |
| E3 | Exits at unit or account scope | WIDEN, stays at account | RC-32 |
| E4 | One position per market | WIDEN | RC-32 |
| E5 | Per-market settings | WIDEN | RC-33 |
| E6a | `sessions` | WIDEN | RC-33 |
| E6b | `context_needs` | WIDEN | RC-58 |
| E6c | `routes`, `plain_python`, `roll` | stays refused | None. One venue, the Library block is the Python door, and `roll` waits on a futures route (Q2) |
| `streams_not_built` | Second stream | WIDEN | RC-31 |
| E7 | Spread, SQS, news in `guard` | WIRE | RC-35, RC-36, RC-37 |
| E8 | Sizer slot has no type check or ceiling | WIDEN | RC-06 |
| E9 | `_CEILING = 0.005` in the contract test | WIDEN | RC-01 |
| E10 | Exit contract test feeds refused evidence | WIDEN | RC-01 |
| E11 | Library blocks not enrolled | WIDEN | RC-01 |
| E12 | Motion rule gets only strength and R | WIDEN | RC-24 |
| E13 | `r_after_costs` holds no costs | WIDEN | RC-28 |
| E14 | Market entries only | WIDEN | RC-69 |
| E15 | `OwnPosition` lacks facts | WIDEN | RC-11, RC-26 |
| E16 | Identity table unwired | WIRE | RC-64 |
| E17 | Too-thin count | value | None. A value, owned by the numbers talk and methodology |
| E18 | Motion constants | WIDEN | RC-24 |

## Appendix G. Coverage of what the baseline must hold

Every line of `round-2/SEEDS-2.md` Part C, and the older list's lines not restated there. Each is held by a PR or by a named other session, where the test is room, not delivery.

| Line | What he asked | Held by |
|---|---|---|
| H-01 | The unit can actually trade | RC-19, RC-39 |
| H-02 | The unit can size itself | RC-06, RC-07 |
| H-03 | The unit can configure itself, without him | RC-24, RC-26 |
| H-04 | It has a template | RC-17, RC-39 |
| H-05 | Own configurations plug in | RC-59, RC-60 |
| H-06 | It works out of the box | RC-19, RC-39 |
| H-07 | It works before the numbers are set | RC-17, RC-23 |
| H-08 | Someone new can use it | RC-19, and the installer in the release session |
| H-09 | It is a baseline with a layer for customizing | RC-48, RC-66 |
| H-10 | It is a canvas, not a policy | RC-41, RC-45, RC-57 |
| H-11 | It can be improved any way | RC-59, RC-60 |
| H-12 | It is not rigid | RC-41, RC-57 |
| H-13 | Nothing is set in stone, and questions that fix policy go to configuration | RC-23, RC-53 |
| H-14 | It finishes the unit as a whole | RC-48, RC-66 |
| H-15 | It is maintainable, for a developer | RC-02, RC-48, RC-66 |
| H-16 | It performs | RC-21, RC-22 |
| H-17 | It goes live | RC-46, RC-67, RC-68, RC-69, then his click |
| H-18 | It holds | RC-02, RC-65 |
| H-19 | Design for complexity, no complex system | RC-48, and the lead's trims |
| H-20 | One template by type, and the set of types can change | RC-39, RC-59 |
| H-21 | A scalper is handled differently from intraday | RC-31, RC-39 |
| H-22 | Mean reverting and trend following differ too | RC-39 |
| H-23 | Every number has a reason | RC-23 |
| H-24 | The way a number is derived can be changed | RC-23, RC-24 |
| H-25 | Self-configured values have ranges and stated reasons for moving | RC-24, RC-25 |
| H-26 | Some settings are his, some self-set | RC-23 |
| H-27 | No key setting left blank | RC-23 |
| H-28 | Sizing does not lean hard on the edge; the edge has a range | RC-06, RC-23, values in the numbers talk |
| H-29 | A weak edge can still pay | RC-21, values in the numbers talk |
| H-30 | Sizing across all instruments, not one | RC-05, RC-07 |
| H-31 | It adjusts over pips, points and the rest | RC-05 |
| H-32 | Unit of measure is settled on purpose | RC-05 |
| H-33 | A unit can hold more than one position where its type allows | RC-32 |
| H-34 | Growth over 24 hours is not one fixed percentage | RC-22, RC-56 |
| H-35 | The next trading day has an answer | RC-16, RC-51 |
| H-36 | He can start a unit with little and let it adjust | RC-24, RC-29 |
| H-37 | Frequency can be a sizing basis | RC-13, RC-59 |
| H-38 | Costs are known per market, instrument, timeframe and time | RC-28 |
| H-39 | QMX observes costs and acts on them | RC-28, RC-35 |
| H-40 | A unit can stay off an instrument on its news day | RC-36 |
| H-41 | The drift between live and backtest gets a rule from agents | RC-24, the rule in the agentic upgrade session |
| H-42 | Trades the same on demo and live; only the account differs | RC-08, RC-18 |
| H-43 | Demo units exist at first boot | RC-17, and first boot in the release session |
| H-44 | The plans behind the code were read, not only the code | The lead's run, through `unit-baseline/SWAP-CHART.md` |
| H-45 | Stand-ins for sizing, exits and halts are planned for, so builders swap them | RC-48, and Appendix F of this plan |
| H-46 | What the unit and QML dictionary already have is used | RC-12, RC-34 |
| H-47 | Fast invalidation counts everywhere | RC-39 |
| H-48 | The stop mechanism is chosen on purpose | RC-12, RC-45 |
| H-49 | Dynamic stop and take profit for intraday is looked up in the old and new systems | RC-12, RC-68 |
| H-50 | Closing a trade is never blocked | RC-09, RC-10, RC-11, RC-42 |
| H-51 | Brakes and accelerators have definitions | RC-13, RC-39 |
| H-52 | Definitions draw on his words in the transcript | RC-39, RC-57 |
| H-53 | Some can be taken, some refused | RC-13, RC-57 |
| H-54 | House money and the accelerator idea stay | RC-22 |
| H-55 | Reverse house money stays available | RC-22 |
| H-56 | They are tools, not fixed law | RC-13, RC-21, RC-57 |
| H-57 | The old circuit breaker is the baseline, improved | RC-39 |
| H-58 | It can spot alpha decay | RC-62, the test in the methodology session |
| H-59 | Brakes know what is breaking | RC-14, RC-15 |
| H-60 | The brake set stays open | RC-13, RC-59 |
| H-61 | No one standard for frequency against brakes | RC-23, RC-39 |
| H-62 | We know what frequency does to the brakes | RC-15, the reading in the methodology session |
| H-63 | Exposure, drawdowns, unrealized and realized profit are measured | RC-14, RC-27 |
| H-64 | Market isolation on evidence, by class, region or instrument | RC-36 |
| H-65 | The floor is not reached in normal running, and it is his to set | RC-51, the value in the numbers talk |
| H-66 | Scenarios beyond the first ones are generated | The methodology session |
| H-67 | Risk works at unit, cluster, methodology and portfolio level | RC-14, RC-49, RC-50 |
| H-68 | The Book and BMS are open to change | RC-49, RC-53 |
| H-69 | The BMS can self-optimise at portfolio level | RC-49, RC-58, the optimiser in the agentic upgrade session |
| H-70 | Pods are the customization layer; answers exist for how they ship | RC-53, RC-59 |
| H-71 | Pod ideas and configurations are actually offered | RC-57 |
| H-72 | A mini app can be combined with the risk and sizing system | RC-58, RC-60 |
| H-73 | Ideas can bring new mini apps | RC-59 |
| H-74 | Mini apps feed each other | RC-58 |
| H-75 | Units from any source can trade, Lab, a workflow, a mini app | RC-19, RC-60 |
| H-76 | A user can make a new version of the risk and sizing part | RC-03, RC-53 |
| H-77 | Schemas exist | RC-49, RC-53, RC-59 |
| H-78 | External code can be added | RC-59, as a Library block only, never free Python |
| H-79 | Agents and copilot can reach it and know it is correct | RC-47, RC-59 |
| H-80 | QML is used so agents do not produce slop | RC-47, RC-59 |
| H-81 | Python covers only what QML can't | RC-59 |
| H-82 | The QML dictionary is improved where the findings call for it | RC-34, RC-39, RC-59 |
| H-83 | A unit is what ideas finally become | RC-59 |
| H-84 | A new unit or pod can be made any day from a video or paper | RC-57, RC-59, the routing in the agentic upgrade session |
| H-85 | The technical lens covers more than the unit | RC-37, RC-58 |
| H-86 | MIS, SQS, brakes, accelerators and QML are open to enhancement or overhaul | RC-35, RC-58 |
| H-87 | Overhauls must make better sense and perform better | RC-35 |
| H-88 | The MIS holds its weight as a router | RC-58, the content with the MIS owner |
| H-89 | His MIS question has an answer | RC-58, the content with the MIS owner |
| H-90 | Sniping windows can be found, by agents or deterministically | The MIS owner, as content |
| H-91 | Session opens are catered for | RC-33, RC-36 |
| H-92 | Market physics and relative volume have a settled place | The MIS owner, blocked on volume on bars (OPEN row 5) |
| H-93 | Trading node ideas are considered | RC-42, RC-44 |
| H-94 | Where it runs is left open | RC-49 |
| H-95 | cTrader first for breadth, then Hyperliquid | RC-67, and a venue adapter row for Hyperliquid in the unit build's C-16 |
| H-96 | He does not have to monitor units | RC-62 |
| H-97 | About 200 units is a real case | RC-52, RC-62 |
| H-98 | An agentic workflow caters for it, as a mini app or so | RC-61, RC-62 |
| H-99 | A unit whose edge was never real can be found earlier | RC-62, the test in the methodology session |
| H-100 | Logging, monitoring and observability are in the technical lens | RC-08, RC-42 |
| H-101 | He can tell what is working | RC-14, RC-62 |
| H-102 | A variables ledger exists and grows after expansion | RC-23 |
| H-103 | Terms agents can use without confusion | RC-02 |
| H-104 | Agentic upgrade | RC-47, RC-61, then the agentic upgrade session |
| H-105 | The copilot can talk numbers with him and make a template through QML | RC-17, RC-47, then the agentic upgrade session |
| H-106 | Tools for agents | RC-47, then the agentic upgrade session |
| H-107 | Agents propose, he promotes | RC-18, RC-54 |
| H-108 | MCPs and the Lab together | The agentic upgrade session |
| H-109 | Shepherd and departments | The agentic upgrade session |
| H-110 | A mini app per market as a pod in his hedge-fund sense | RC-59, then the agentic upgrade session |
| H-111 | Failed strategies reworked by agents | The agentic upgrade session and the methodology session |
| H-112 | Findings stored for later jobs | RC-59, then the agentic upgrade session |
| H-113 | Methodology per unit kind plugs in | RC-63, then the methodology session |
| H-114 | Edge verification as a workflow | The methodology session |
| H-115 | Monte Carlo, backtest reading by agents | The methodology session |
| H-116 | A list of UI needs goes to the UI session | The UI session, through `HANDOFFS.md` |
| H-117 | Notifications are a UI question | The UI session |
| H-118 | The UI itself and its notes were looked at, not its code | The UI session |
| H-119 | The numbers talk can happen on top, the goal | RC-56, then the numbers talk |
| H-120 | Small capital can concentrate, best basket, fewer instruments | RC-29, then the numbers talk |
| H-121 | Large risk per trade can be set; a user may do it | RC-41, RC-45, then the numbers talk |
| H-122 | A simulation harness can run worst, realistic and best | The methodology session |
| H-123 | Agents' earlier output is used, not redone from nothing | The lead's run |
| H-124 | Findings from the papers are walked through, as ideas | The lead's run |
| H-125 | Ideas beyond the technical lens are kept | The lead's run |
| H-126 | Logic is linked across sources | The lead's run |
| H-127 | Ideas that could become units are kept in a bank | The lead's run |
| H-128 | Architecture versions, if they can be got, are shown | The lead's run |
| H-129 | One fold, the best, with recommendations | The lead's run |
| H-130 | Funnel picks the best, more than one, or a range | The lead's run |
| H-131 | Logical flaws and collisions are hunted | The lead's run |
| H-132 | Agents solve issues; issues are not listed back to him | The lead's run |
| H-133 | It ends with the plan and the orchestrator prompt | This plan and `PROMPT-ORCHESTRATOR.md` |
| H-134 | No questions that are numbers, methodology or pods | The lead's run |
| H-135 | Research carries no $500 bias | The lead's run |
| H-136 | His raw words were read, without bias | The lead's run |
| Old 2 | Extensibility the way N8N handles things, and white label | RC-59, white label in the release session |
| Old 3 | Types include mean-reverting scalper, ORB, trend-following | RC-39 |
| Old 11 | Edge-led sizing stays expressible | RC-59, as a block |
| Old 14 | Kelly after costs, half or full open | RC-59, values in the numbers talk |
| Old 16 | One-shot breakeven needs its own thought | RC-68, as a block off by default |
| Old 19 | Same-bet positions count once | RC-32, RC-50 |
| Old 20 | System 1 over System 2 | The methodology session. See Appendix H |
| Old 22 | A losing-run brake per type | RC-39 |
| Old 26 | Kill switch and SQS as outside parts | RC-36, RC-41 |
| Old 29 | Multiple Books register on the BMS | RC-49 |
| Old 37 | Where it runs, node and his PC | RC-49 |
| Old 39 | What QMB hands over and what the MIS publishes | RC-58 |
| Old 41 | Microstructure and macro as numbers from agents | RC-58, then the agentic upgrade session |
| Old 44 | Borrowed designs | The lead's run |
| Old 53 | Other industries' solutions | The lead's run |
| Old 55 | Tooling, replaced by his later words | The lead's run |

## Appendix H. What the spine does not settle

Each has the default this plan took. None waits.

| # | What is open | Default in this plan | Whose |
|---|---|---|---|
| 1 | What a pod is. Past stop B, a later switch to a governing pod (V2) also throws away RC-53 to RC-55 | The build continues on recipes, and tells him at RC-48 once. To save that work he says so by stop B | Him |
| 2 | The spine says the group replaces the `book` and `bms` shells, with no migration | Settled by the code. RC-49 makes both kinds read-only and adds no migration. At the tip only their schemas and the registry migration name them (`from_registry.py:35-36`). UNKNOWN on his real folder until he lands | Him, on his folder only |
| 3 | The templates' extra blocks (fast-invalidation cut, thesis exit, own-percentile bench, count brake, two-speed breaker) had no slice in section 10 | Settled. RC-39 adds them after the gate. K9 17 uses fixture units, and SPINE section 10 now says so | This plan |
| 4 | No gate for his signature exists in `tools/release_gate.py` or `tools/build_release.py` (grep, 7 Nov) | Settled as a fact. RC-20, RC-48 and RC-66 bump versions and write a note. No new gate is built | Release session |
| 5 | A block that hangs again after each restart has no stand-down rule, now that hung-link protection is deferred | Settled by AD-9 and SPINE section 11. Named risk only. A hang restarts the node, and the owner stands the block down. Reopens with the worker process | Lead, done |
| 6 | Agents with cTrader's MCP on the node's own demo account can open positions no unit holds. The older note wanted a `foreign` scope, and the fold has none | Not built. Handed to the agentic upgrade in `HANDOFFS.md`. RC-27's `account.open_risk` counts only positions the node holds, and says so in `basis`, now a box there | Agentic session |
| 7 | The two old repair notes were written against the superseded first spine (SQS in a guard package, targets rest at the venue, kill level meanings fixed) | The fold wins. `HANDOFFS.md` restates them. `gross_r` and `net_r` from the note are kept (RC-28) | Repair session |
| 8 | `OPEN.md` rows 14, 21, 22 and `WALKS.md` 3, 8, 11, 13 spoke of what the lead trimmed | Settled. Both were corrected on 7 Nov (`build/FINAL-CHECK.md`). `SPINE.md` still wins | Lead, done |
| 9 | Where the practice venue's bars ship, and whether `venue_records` accepts a venue with no broker | Bars settled. RC-17 ships them in `qmn/app/practice_bars/`, and they serve both the backtest and the feed. Landing stays unproven. `venue_records` is cTrader only at the tip, so RC-19 widens it, with the fallback in its section | This plan |
| 10 | "System 1 over System 2", N8N and white label appear in the older list and nowhere in the fold | Named in Appendix G to methodology and release. Nothing is built | Methodology, release |
| 11 | PR count. Section 10 estimated 52 and this plan has 69 | Settled. 17 more, 6 added (release RC-20, RC-48, RC-66, templates RC-39, tool rows RC-47, gallery RC-57) and 11 splits to one builder's size. No split adds a seat the spine lacks. Unmeasured how long a PR takes here | Lead, done |

## Appendix I. CHECK's proven faults, each a named test

| Fault that ran | PR | Test |
|---|---|---|
| One raising logic block ends its own unit's exits | RC-09 | `test_a_raising_logic_slot_leaves_exits_running` |
| One raising block stops every unit after it, 11 heals and 0 drives on `dep-2` (B1) | RC-10 | `test_k9_2_one_units_raise_stops_no_exit_and_no_other_unit` |
| A parked entry crossing a bar sends twice (B2) | RC-43 | `test_k9_11_one_signal_one_send` |
| From zero nothing reaches paper, `not_in_table` (B3) | RC-18 | `test_a_draft_reaches_paper_on_his_click` |
| The walk from zero fails at the promote (B3) | RC-19 | `test_k9_7_canary_reaches_a_filled_paper_entry` |
| One account's feed builds one bar size (B4) | RC-30 | `test_one_feed_hosts_1m_and_15m` |
| A 1m, 5m and 15m unit can't share a feed (B4) | RC-31 | `test_k9_17_one_feed` |
| USDJPY risks the figure in JPY (B5) | RC-05 | `test_loss_at_the_stop_equals_the_amount_on_four_markets` |
| Hosts and exits under a stale rate (B5) | RC-07 | `test_a_stale_rate_never_stops_an_exit` |
| A stopless entry is closed by the first tick (B9) | RC-46 | `test_k9_12_a_stopless_entry_survives` |
| One entry takes 26 s, and a long bell trips the watchdog (S1) | RC-44 | `test_a_long_bell_leaves_entries_over_and_the_node_lives` |
| Six slow closes use the whole 30 s (S1) | RC-44 | `test_six_slow_closes_beat_the_watchdog` |
| A size-only edit moves the fingerprint (AD-3's fact) | RC-03 | `test_a_size_edit_moves_only_the_risk_fingerprint` |
| A held position's exits go silent after a recompile (COMPARE's rerun) | RC-04 | `test_exits_fire_after_a_risk_only_recompile` |
| Short stops read bid bars (S15) | RC-11 | `test_a_short_reads_ask_bars` |
| A logic number moves at the tip, and must keep moving | RC-24 | `test_memory_is_bounded` |
| A sizing or exit number never reaches the engine, and no stamp means no move | RC-25 | `test_fraction_moves_and_the_next_entry_uses_it` |
| The shipped sizer ignores a moved value | RC-25 | `test_k9_6_a_block_ignoring_a_moved_number_fails` |
| The target ignores a moved value | RC-12 | `test_target_reads_a_moved_multiple` |
| After a restart the count is lost | RC-26 | `test_k9_15_self_configuration` |
| A 5,000-lot answer passes (`SWAP` S1c) | RC-06 | `test_the_band_catches_5000_lots` |
| A wide unit trades every listed market on a dead board (E1) | RC-58 | `test_a_dead_board_falls_back_to_home` |
| Entries ignore the kill effect table (`SWAP` 18) | RC-41 | `test_entries_read_the_kill_effect` |

`run_budgeted`'s toy (a hang answered at its budget with a thread left burning) has no test, because the lead deferred it. The risk is named in AD-9.

## Appendix J. Risks

| Risk | Where it lands | What the coordinator watches |
|---|---|---|
| `runtime.py`, `unit.py` and `compiler.py` sit on most rows, so most of the program runs one builder at a time | RC-04 to RC-46 | Appendix C's second column, and rebase rather than wait where only `app.toml` clashes |
| The stack is long, on top of 118 unmerged PRs | Landing | `STACK-LIST.md` stays current, and squash per PR |
| A block that never returns restarts the node (AD-9) | RC-09 onward | A heal count in the node meters, and reopen the worker process if one is seen |
| QML changes reach the money app, and nothing checks his signature | RC-20, RC-48, RC-66 | The release note says what is unsigned |
| Whole-repo runs take about two hours | Every eighth PR | They never block a builder, and a red is traced afterwards |
| A repo-wide rename in a shared seam (RC-28 `gross_r`, RC-32 `own_position`) | RC-28, RC-32 | Run alone, with a repo-wide grep in the PR body |
| `D:` fills with check copies and caches | Every lane | Remove each check copy after its verdict |
| His internet drops mid-build | Every builder | Builders push after every verifiable unit, and `RESUME.md` stays current |
| Fake broker kinder than cTrader | RC-27, RC-42 to RC-46, RC-67 to RC-69 | Each names what waits for G-DEMO, and the demo lane reruns then |

## Appendix K. Script output

`plan-parts/check_program.py` and the skill's `check-plan.mjs`, run by `plan-parts/assemble.py` when this file was built.

```text
INFO 69 PR sections, code tree D:/QMX-worktrees/bld-repair-24 at 351e7521
PASS every dependency names a PR that exists: 89 edges
PASS no PR depends on itself or a later PR, so no cycle exists
PASS a depth-first walk of the graph finds no cycle
PASS every path marked new is absent from the code tree: 184 new paths
PASS no path is created twice
PASS every edited path exists in the tree or is created by a PR this one depends on: 274 edits, 32 on paths an earlier PR creates
PASS swap ledger holds all 31 placeholders and 18 sockets, each with a PR or a stated none: 52 rows
PASS each ledger row names exactly the PRs whose sections declare that swap
PASS coverage table holds every H line of SEEDS-2 Part C, each with a PR or a named session: 136 H lines, 16 older lines
PASS every proven fault of CHECK.md names a test that sits in its PR's acceptance tests: 23 faults
PASS every PR names at least one acceptance test
RESULT PASS: 0 failed checks

check-plan.mjs: 69 PR sections, 0 problems
```
