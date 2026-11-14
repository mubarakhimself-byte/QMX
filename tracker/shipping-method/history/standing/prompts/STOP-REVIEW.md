# Checkpoint review prompt (review, then merge)

The `stop-review` skill fills this in a session the coordinator starts when a checkpoint (stop point) is built, in `{WORKTREE_ROOT}` (outside the program folder, so the ship hook does not load). He never pastes it; he can also start it by saying "review stop <X> of <program>". This session reviews the checkpoint and, when it is clean and the deep run is green, merges it itself. There is no separate merge phase; `MERGE.md` is only the manual entry for "merge stop <X>". Placeholders as in `COORDINATOR.md`, plus:

- {STOP}: the checkpoint id. {ROUND}: `1`, or `2` after a fix program ran.
- {FROM}: the commit the checkpoint starts from: `parent_tip` for the first stop, else the `merged` sha of the previous stop in `PROGRAM.yaml`.
- {FIX_PROGRAM}: round 2 only, the fix program folder.
- {TARGET}: `target_branch` in `PROGRAM.yaml`, normally `engine/base`.

---

Read the poteto-mode skill's `SKILL.md` in full, including its Principles section, before any work. Agents you spawn do not spawn their own.

You review checkpoint `{STOP}` of program `{PROGRAM}` as a whole, round {ROUND}, then merge it. No AI reviewed these slices one by one: scripts gated each slice, and this review is the only AI review they get. So you look both inside each slice (is the brief met, can each test fail) and across them (slices that pass alone and break together, drift from his asks, drift from the architecture, fixed lines that break when a part on their path fails).

Read first: `{PROGRAM}/PROGRAM.yaml` (its `chains:`), `{PROGRAM}/SCOPE.md`, `{PROGRAM}/PLAN.md`, `{PROGRAM}/arch/ARCH.md` (the element index and `## Operations`), `{PROGRAM}/EDGE-CASES.md`, `{PROGRAM}/GROUND.md` ("Fixed lines touched"), `{PROGRAM}/REMOVED.md` and `C:/Users/Mubarak/Desktop/QMX/tracker/REMOVED.md`, `{STANDING}/REVIEW.md`, `{STANDING}/PROJECT-RULES.md`, `{PROGRAM}/notes/stop-{STOP}.md` (it gives the tip, {TIP} below), and `{PROGRAM}/notes/CHAIN-ISSUES.md` if it exists. Skip any program file that does not exist.

`ship X` means `python {SHIP} X --program {PROGRAM}`. Make a detached checkout: `git -C {REPO} worktree add --detach {WORKTREE_ROOT}/stop-<program>-{STOP} {TIP}`. Remove it when you finish.

## Power cuts and restarts

A power cut takes the internet with it, and the agents of this session die. Nothing in the coordinator restarts them, so this session watches for itself:

1. Run `ship power`. Exit 2 means no `power_watch` runs: start `ship power_watch` as a background command and note its task id in `{PROGRAM}/stop-review/{STOP}/SESSION.md`.
2. Start a heartbeat with the `loop` skill, every 10 minutes, with the text "review tick: run Power cuts and restarts step 3 in STOP-REVIEW.md".
3. On every tick: `ship power`. Exit 2: start a watcher as in step 1. Exit 1 (HOLD): start nothing; wait for the next tick. Exit 0: every reader whose notes file does not end with the line `DONE` and that is not running gets a fresh agent with the same brief; a deep run whose `summary.txt` is missing and whose command is not running is started again. Then carry on from the first step of this prompt that is not finished.

Every reader writes its notes to its file as it goes and ends it with `DONE`, so a rerun skips finished work. Stop the heartbeat when this session ends.

## Round 1

1. **Start the deep run** as one background command, and do not wait for it:
   `python {SHIP} nightly --program {PROGRAM} ; python {SHIP} quality --program {PROGRAM} --from {FROM}`
   It is the whole test suite on this Windows laptop, plus Vulture, Skylos and mutmut on the checkpoint's changed functions, with only new findings failing. Linux is not run until CI runs it; say so in the verdict.
2. **Build the map**, `{PROGRAM}/stop-review/{STOP}/MAP.md`, from `PROGRAM.yaml`'s `chains:`, `state.json`, the briefs' `Chain:` lines and `git -C {REPO} log --reverse --name-only --format="%H %s" {FROM}..{TIP}`:
   - per ask: its plan lines, elements and slices, each slice's state and landed commit;
   - commits with no chain: a commit whose subject does not start with a slice id of this program or its fix programs (each one is a blocker);
   - seams: every element, edge case or file that two or more slices touched;
   - the scenario ledger: every edge case (`E` id) the slices carry, the test that proves it, and that test's result at {TIP} once the deep run is done;
   - `GROUND.md` facts the checkpoint moved, and the removed rows on its files;
   - every `DECISION` line from `{PROGRAM}/evidence/*/*/report.md`, and every line of `notes/CHAIN-ISSUES.md`.
3. **Readers, in parallel.** Spawn fresh agents (`subagent_type: "poteto-agent"`, `model: "opus"`, `run_in_background: true`). Each reads `{STANDING}/skills/slice-review/SKILL.md` (the method), `REVIEW.md`, `PROJECT-RULES.md` and the map, works at {TIP} in its own detached checkout, and writes its notes to `{PROGRAM}/stop-review/{STOP}/<name>.md`. Every Important needs a run at the tip as proof; a candidate with no proof is dropped. Readers only collect findings. Nobody fixes anything yet.
   - **One reader per architecture element** (`element-<id>.md`), given every slice of that element, so both sides of a seam sit in one head. Walk 1: for each slice, is the brief met, can each test fail, does each scenario test drive the failure; then the seams: do the slices agree on every value, word, contract and registry they share, and does any test pass only because a neighbour is faked.
   - **`chain.md`.** Walk 2, down the chain: prove each plan line and each of his rulings this checkpoint touches at the tip with a command or a test. Walk 3, up from the code: every commit and hunk serves an ask; nothing rebuilds a removed row.
   - **`faults.md`.** Walk 4, the fixed-line fault walk. For each fixed line and ruling under "Fixed lines touched" in `GROUND.md`: list every part on its path at the tip (from the element index and the diagrams, plus the older modules the ground facts name). Ask each part each fault kind in `REVIEW.md`. Each cell ends in a passing scenario test, a probe that shows the line holds, or an Important finding. Write the table.
   - **`operations.md`.** Walk 5: each line under `## Operations` in the architecture is a claim. Prove each self-recovery line by making the part fail at the tip and watching it come back, and check the alarm fires only when recovery fails.
4. **Screen the builder decisions** yourself. For each `DECISION` line: is it a product call in technical clothes, or does it touch a fixed line? A cleared one is logged as "the builder decided X because Y". A product call that touches a fixed line, a ruling or a one-way door is Important. Any other is listed for him in the merge note with a recommendation, and does not hold the merge.
5. **Wait for everything.** When every reader's file ends `DONE` and the deep run has written `checks/_nightly/<tip8>/summary.txt` and `checks/_quality/<tip8>/summary.txt`, read the deep run through the chain: a new red test is a finding (blocker 1); a quality FAIL line is a finding; dead code a can-change row planned to delete and that is still there is a finding; a surviving mutant under a fixed-line scenario test is Important.
6. **One verdict.** Write `{PROGRAM}/stop-review/{STOP}/REVIEW.md` in `REVIEW.md`'s shape and tags, count first, with `VERDICT: CLEAN` or `VERDICT: BLOCKED`, ending `END {TIP} checkpoint-{STOP}-round-1`. A Pre-existing or Nit finding never blocks; list them for the next plan. The deep run must be green for CLEAN.
7. **CLEAN:** go to **Merge**.
8. **BLOCKED:** send one fix batch through the build flow. Write a fix program folder beside `{PROGRAM}`, named `<program>-fix-{STOP}`, from `{STANDING}/templates/`:
   - `PROGRAM.yaml`: the same build branch, repo and target; `parent_tip` {TIP}; one stop point, `{STOP}`.
   - `SCOPE.md`: the asks from `{PROGRAM}/SCOPE.md` the fixes serve, quoted as they are there, and each Important finding by id.
   - `SLICES.md` and `slices/<id>/BRIEF.md`: one slice per finding or per group of findings in the same files. Ids `<prefix>-{STOP}-fix-<n>`, unique across every program. Each brief cites the chain ids it repairs, carries the finding as an edge case with a test that fails first, and its section 11 holds `TRACE: <slice> -> <plan ids> -> <ask>`. Facts checked at {TIP}.
   - `checks.toml`: copied from `{PROGRAM}`.

   Lines of `CHAIN-ISSUES.md` that say the plan itself is wrong go to the planner: when `planner_session` in `PROGRAM.yaml` is running, send them in one message (SendMessage); otherwise write them to `{PROGRAM}/stop-review/{STOP}/FOR-PLANNER.md` and name the file to him at the end.

   Then start the build on the fix folder as `{STANDING}/prompts/NEXT-PHASE.md` says: skill `ship-build`, in the fix folder. Its coordinator starts round 2 when it ends. Record the session in `{PROGRAM}/notes/SESSIONS.md` too, stop your heartbeat, and end.

## Round 2

Here {TIP} is the tip in `{FIX_PROGRAM}/notes/stop-{STOP}.md`, and {TIP_ROUND_1} the sha in round 1's END line; check out {TIP}. Start the power section as above. Read round 1's `REVIEW.md`, `{FIX_PROGRAM}/RUN-REPORT.md`, `{FIX_PROGRAM}/notes/WAITS-ON-YOU.md`, and the fix commits `git log {TIP_ROUND_1}..{TIP}` with their diffs and checks in `{FIX_PROGRAM}/checks/`.

1. Start `python {SHIP} quality --program {PROGRAM} --from {TIP_ROUND_1}` in the background: Vulture, Skylos and mutmut on what the fixes changed. The fix program's landings ran the touched tests on Windows.
2. Judge only whether each round-1 Important is fixed (rerun its evidence at {TIP}) and whether the fix diff adds a new Important. One fresh reader may do the fix-diff read; it writes `round-2.md` and ends it `DONE`.
3. Write `{PROGRAM}/stop-review/{STOP}/REVIEW-2.md`, ending `END {TIP} checkpoint-{STOP}-round-2`.
   - **CLEAN** (and the quality run green): go to **Merge**.
   - **BLOCKED:** there is no third round. Write each open finding in plain words, with what it means for him, in `{PROGRAM}/stop-review/{STOP}/WAITS-ON-YOU.md`, tell him, stop your heartbeat and end.

## Merge

You merge the checkpoint yourself. He is not asked, unless a problem cannot be fixed and touches money, his sign-ins or the fixed lines. CI is paused, so the gate is local: the whole suite green on this Windows laptop, the quality run with no new finding, and the review CLEAN. Never merge into `main` or `integration`. {REVIEWED_TIP} is the sha in the END line of the CLEAN verdict.

1. **Every record answered.** Search `{PROGRAM}/stop-review/{STOP}/` and the fix program's folder for `VERDICT: BLOCKED` and `NOT CLEAN`. Each hit must be answered by a later CLEAN verdict for the same code (round 1 BLOCKED, round 2 CLEAN). Any other hit stops the merge: write it in `WAITS-ON-YOU.md` and tell him.
2. **The reviewed code is the code you merge.** `git -C {REPO} ls-remote origin refs/heads/<build_branch>` must print {REVIEWED_TIP}. If the branch moved, only commits of later checkpoints may be on top, and they are not landed while this one is open, so a move means something is wrong: stop and tell him.
3. **The PR.** Reuse the open one (`gh pr list --head <build_branch> --base {TARGET} --state open`), else open it with `gh pr create --base {TARGET} --head <build_branch> --title "<program> stop {STOP}: <plain words>" --body-file {PROGRAM}/merge/{STOP}-pr.md`. Write that body in PR body v2's shape for the checkpoint as a whole: the plain-words line, one `TRACE:` line per ask it serves, the slices as a short list with their PRs, the door call, every `OPEN:` and `DOC:` line from the slice PRs, and the line "Linux: not run (CI paused)", ending "Shipped by Mubarak." No credit line.
4. **Merge.** `gh pr merge <pr> --merge`. A merge commit keeps one commit per slice, so a bad slice reverts in one step. If GitHub refuses (a required check, branch protection), write the refusal in `WAITS-ON-YOU.md`, tell him in plain words, and end. Prove it: `git -C {REPO} fetch -q origin` then `git -C {REPO} merge-base --is-ancestor {REVIEWED_TIP} origin/{TARGET}` exits 0.
5. **Record.** Write `{PROGRAM}/merge/{STOP}.md`: the PR, {REVIEWED_TIP}, the new `{TARGET}` sha, the deep run's lines, "Linux: not run", and the line `MERGED`. Set `merged: <new {TARGET} sha>` on stop `{STOP}` in `PROGRAM.yaml`. Run `ship merged {STOP}`; from the coordinator's next wake the next checkpoint is open and its pre-built slices land.
6. **Removed rows.** Move this checkpoint's planned rows from `{PROGRAM}/REMOVED.md` to `C:/Users/Mubarak/Desktop/QMX/tracker/REMOVED.md`, each with the merge sha. Then delete `{PROGRAM}/main-status.txt` and run `ship preflight` so the coordinator's main-checkout snapshot includes that edit.
7. **Tell him, per ask, in his words:** "You asked for X. Now true: ... Parked: ... For the next plan: ...". Add the builder decisions listed for him, each with a recommendation.
8. **Next.** The coordinator is alive when `{PROGRAM}/notes/LOG.md` changed in the last 20 minutes: then do nothing; it picks the next checkpoint up on its next wake. Otherwise, if `PROGRAM.yaml` has a stop after {STOP}, start a coordinator as `{STANDING}/prompts/NEXT-PHASE.md` says: skill `ship-build`, in `{PROGRAM}`. If {STOP} was the last stop and no coordinator is alive, run `ship run_report` and `ship teardown`, stop the `power_watch` you started, archive every finished session listed in `notes/SESSIONS.md`, and tell him the program is merged.

Stop your heartbeat and remove your checkout. End by telling him the verdict and what merged in plain words, with the review file's path.
