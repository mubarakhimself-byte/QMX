# System audit of the shipping factory, end to end (13 November 2026)

What breaks when he starts one session and expects it to chain from planning to merge, unattended. Read and run only; nothing else was changed. Findings already in `GAP-AUDIT-2026-11-13.md` are not repeated; where one is confirmed or has grown worse, the finding says so with its GAP number.

State at audit time (18:20 to 19:30 UTC): `ship/kit` at `51d95409`, clean (the coordinator stopped the GitHub CI builder and stashed its work as `stash@{0}`; I first read the WIP tree, then rechecked the clean one). `ci/github` at `9eb1403` (RESUME still says `54aaf83`). `origin/engine/base` at `3ae41ffc` (8 Nov), which does **not** hold `.github/workflows/qmx-ci.yml`. No program folder exists anywhere under `D:/QMX-worktrees` (`phase_state.py` prints "no program folders found"), so the whole pipeline has never run end to end. The 12 Nov method files are still only staged on `main`'s checkout (`A tracker/shipping-method/SHIPPING-METHOD.md`), and `.claude/` is ignored (`.gitignore:20`), so GAP 3.1 still holds.

Severity: **blocks** stops the chain; **wrong** lets it run to a wrong result; **friction** costs him a click, time or money.

## Top 10

1. **F1 [blocks] Phase starts do not chain unattended, and the fallback lands in the wrong folder.** Every hand-off except the planner's runs on an automated turn (an agent finishing, a heartbeat tick, another session's message), where `start_session` is refused (`NEXT-PHASE.md:73`). The fallback, `initiation: "own_initiative"`, cannot carry `cwd` (the tool: "`cwd` ... user_asked only"), so the card opens in the caller's folder. A checkpoint review opened in `{PROGRAM}` loads the ship hook, which refuses its writes to `stop-review/` and `merge/`.
2. **F2 [blocks] T-22 now blocks every slice, not only the deep run (GAP 4.7, worse).** qmx-ci's `slice` level runs `poe types` on Linux for every touched folder (`tools/ci/qci.py:464`). Once qmx-ci.yml reaches a build branch's parent, every slice touching qma-harness, qmx-apps, qmx-engine, qmx-home, qmx-host or qmn goes red on Linux. The WIP kit's `ci.linux_gate` sends it back for a fix round, then parks it as `rounds`, and three such parks trip the breaker. Merging PR #1 switches this on.
3. **F3 [blocks] Any change in his main checkout stops the run.** `main_check` compares `HEAD` and `git status --porcelain --untracked-files=all` (`preflight.py:152-166`). He and other sessions write and commit there daily (this audit file is one such write). Three parts of the method also edit it: the review's merge step 6, `PREFIXES.md` registration, and a second program's merge.
4. **F4 [wrong] The merge ignores CI and merges results nobody tested.**
   - `STOP-REVIEW.md:73` says "CI is paused, so the gate is local", and never runs a CI gate.
   - `engine/base` is unprotected (`gh api .../branches/engine%2Fbase/protection` returns 404), so `gh pr merge` succeeds over a red gate.
   - Round 2 merges with no whole-suite run at the fix tip.
   - No run tests the merge result when `engine/base` has moved.
5. **F5 [wrong] Every chained session inherits his default model, which is Fable.** `~/.claude/settings.json` sets `"model": "fable[1m]"` and `"effortLevel": "xhigh"`. `NEXT-PHASE.md` passes no `model`, and `start_session` inherits the caller's ("Omit to inherit yours"). So planner, plan review, coordinator and reviews all run on Fable unless he starts on Opus. That breaks the CLAUDE.md model rule and drains the weekly bar.
6. **F6 [wrong] `phase_state.py` routes "continue" into duplicate or wrong sessions (shown in a scratch run).**
   - A checkpoint whose review is still running reads `next: stop-review`, so "continue" starts a second review.
   - A fix program reads `next: plan-review` ("scope_gate not set"), so "continue" runs plan review on a fix program.
   - Plan and plan review in progress are not detected either.
7. **F7 [blocks] An empty or all-parked checkpoint wedges the program.**
   - A stop in `PROGRAM.yaml` with no slices never gets `notes/stop-X.md`, so `phase_state` reads `build` forever.
   - A stop whose slices all parked is "built" with zero commits. Its PR cannot be created, the merge ends in WAITS, and the next checkpoint's pre-built slices stay HELD.
   - `ship` orders checkpoints by `SLICES.md` row order, the prompts by `stop_points`, and nothing checks that the two agree.
8. **F8 [wrong] A GitHub or internet outage on mains power burns attempts and trips the breaker.** `power_watch` writes HOLD only on battery (`power_watch.py:1-4`). A `verify_ready` that cannot reach GitHub moves the slice to `red` (`verify_ready.py:127-130`). The rules card answers that with a fix round, and a second failure parks the slice as `rounds`, which counts toward the breaker.
9. **F9 [blocks] Liveness by `LOG.md` age makes two coordinators, and nothing times out a review.**
   - A coordinator paused by a usage limit looks dead after 20 minutes. Merge step 8 then starts a second one, and both wake when the limit lifts.
   - A reader that hangs without writing `DONE` holds the review forever.
   - Restarts of a builder that never replies are unbounded.
10. **F10 [wrong] The scope gate is enforced only by `phase_state`.** He can say "start building X", or name X to `ship-build`: step 2 checks only `coordinator_alive`, and COORDINATOR's Arm never reads `scope_gate`. A plan can be built before his go.

Counts: 37 findings: 6 blocks, 8 wrong, 23 friction. Tests: funnel 20/20 fixtures as expected; `check_plan.py` PASS on 5 fixtures; `check_chain.py --stage handoff` PASS on 2; `ship` suite 88 passed on the WIP tree and 70 passed, 1 failed on clean `51d95409` (a date bomb, F37); `ship --help` lists 21 commands on clean (22 with `ci` on the WIP tree).

## Findings

**F1 [blocks]** `standing/prompts/NEXT-PHASE.md:57-77`, `RULES-CARD.md:141`, `STOP-REVIEW.md:59,82`, `COORDINATOR.md:127,137`.

*What breaks.* The method's own text says the app "refuses starts on a turn that another session's message or an automated wake began". The app's guidance says the same: "this turn is not one that another session's message or an automated event started".

| Hand-off | Turn it runs on | Result |
|---|---|---|
| Planner to plan review | Often his turn | Works when his message started the turn; refused when stage 6 ran in an agent and the turn is the agent's completion |
| Plan review's round trip | The planner's reply arrives as a session message | His go via AskUserQuestion stays inside that turn, so the build start is refused |
| Arm to Run | Arm step 2 waits for a grounding agent | Refused |
| Coordinator to checkpoint review | Always a heartbeat or a builder completion | Always refused |
| Review to fix coordinator | Reader completions or ticks | Refused |
| Fix coordinator to round 2 | Automated turn | Refused |
| Merge to next coordinator | Automated turn | Refused |

*The fallback fails too.* `start_session` accepts `cwd` only with `initiation: "user_asked"`, so the `own_initiative` card starts in the caller's folder:

- A checkpoint review card from the coordinator opens in `{PROGRAM}`, where `.claude/settings.local.json` loads `ship hook`. The hook allows only held worktrees, evidence, `review/` and `notes/` (`hook.py:47-52`), so writing `stop-review/<X>/MAP.md`, `merge/<X>.md` or `PROGRAM.yaml` is refused. The stop-review skill has no "wrong folder" check; `ship-build` step 3 has one.
- A coordinator card from a review opens in `D:/QMX-worktrees` with no hook. Run step 1's probe catches that and ends with "the ship hook is not live", and he has nowhere to go but a manual folder open.

*Evidence.* `start_session` schema: "Elsewhere ("fresh", user_asked only, when the user named the place): `cwd`". `NEXT-PHASE.md:75`: "Propose the session instead: the same call with `initiation: "own_initiative"`".

*Fix.* Stop relying on desktop session starts for unattended hand-offs.

- (a) Add `ship next-phase <phase> --program P`. It launches the headless CLI, which exists at `C:\Users\Mubarak\.local\bin\claude.exe`: `claude -p "<skill path brief>" --model claude-opus-5-5 --permission-mode <mode>` as a detached process with its working folder set by the script. Hooks then load from that folder, and no app refusal applies.
- (b) Or run the coordinator and the checkpoint review in one long-lived session.
- Either way:
  - Give `stop-review/SKILL.md` the same folder check `ship-build` step 3 has.
  - Have `hook.py` also allow `stop-review/`, `merge/` and `PROGRAM.yaml`, so a review opened in the wrong folder still works.
  - Say in `SHIPPING-METHOD.md` "The pipeline" that each hand-off costs him a click until (a) exists.

**F2 [blocks]** `D:/QMX-worktrees/ci-github/tools/ci/qci.py:443-464`, WIP `tools/ship/ci.py:327-341`. Confirms GAP 4.7 and makes it worse: T-22 was filed as a deep-run blocker only.

*What breaks.* `job_lint` at `Level.SLICE` runs `("fmt-check", "lint", "types")` for each touched folder on `ubuntu-24.04`. `linux_gate` returns `"red"` for a FAIL, which sends the slice back. Builders cannot fix Linux pyright on Windows-only code, so the fix round fails too, the slice parks as `rounds`, and the breaker trips after three. On today's `engine/base` (no qmx-ci.yml) every Linux run is NOTRUN and lands, so this switches on the moment PR #1 merges or a build branch is cut from `ci/github`.

*Evidence.*
- `git cat-file -e origin/engine/base:.github/workflows/qmx-ci.yml` fails: "does not exist".
- `ISSUES-2026-11-12.md:80`: "The qmn Linux lane alone has 107 errors".

*Fix.* Merge no ship WIP and no PR #1 until T-22 is closed. Meanwhile, give qci's slice `types` the ratchet treatment (only new pyright errors in changed files block, as Vulture and Skylos already do), or run `types` with `pythonPlatform=Windows` for the Windows-only packages. Add a line to `RULES-CARD.md`: a Linux-only red in `slice_checks` parks as `manual` with the CI url, not as a fix round.

**F3 [blocks]** `ship/kit preflight.py:152-166`, `RULES-CARD.md:106`, `STOP-REVIEW.md:80`, `standing/PREFIXES.md:3`.

*What breaks.* Any new untracked file, edit of a clean file, commit or branch switch in `C:/Users/Mubarak/Desktop/QMX` stops the run at the next wake ("Exit 1: stop the run"), followed by a full teardown. Today's checkout holds 50+ staged files, and other sessions write tracker files there by his own rule ("research lives in the repo"). Three steps of the method write there themselves:

- the review's merge step 6 edits `tracker/REMOVED.md`;
- registering a prefix edits `standing/PREFIXES.md`, which contradicts PLAN.md's "you write and commit nothing in the main checkout";
- with two programs running, A's merge step 6 refreshes only A's snapshot, so B's coordinator stops.

There is also a race inside step 6: the edit lands before `ship preflight` re-snapshots, so a coordinator tick in between stops the run.

*Fix.* Narrow `main_check` to what endangers a run:
- `HEAD` moving away from the arm-time branch;
- changes under code roots (the `checks.toml` package roots);
- never `tracker/**` or `.claude/**`.

Move `REMOVED.md` and `PREFIXES.md` writes to a branch (`docs/ship-records`) pushed by the review, which also closes Remains 25. Make step 6 snapshot first, then edit.

**F4 [wrong]** `STOP-REVIEW.md:63-79`, WIP `README.md:56,157`.

*What breaks.*
- The merge gate is "the whole suite green on this Windows laptop". `ship ci gate` (WIP) is never called, although the kit's README says the review "merges only on exit 0".
- `engine/base` has no protection, so a red or missing qmx-ci gate does not stop `gh pr merge --merge`.
- Round 2 runs only `quality` (`STOP-REVIEW.md:65`), then merges a fix tip the whole suite never ran on. qmx-ci's gate ("passes only if a green deep run tested its head") would refuse it.
- `engine/base` moving during a build (another program, or his own merge) is never merged into the build branch. The deep run tests the build tip, not the merge result, so semantic conflicts reach `engine/base` untested.

This confirms GAP 2.5 (local gate was never his ruling); his only words were "before merging, CI has to work".

*Fix.*
- In `STOP-REVIEW.md` Merge: add a step 2a, "merge `origin/<target>` into a detached copy of the reviewed tip; if it differs from the tip, run `ship nightly` on that commit". Make step 4 `ship ci gate --pr N --wait` exit 0 before `gh pr merge`.
- Round 2 runs `ship nightly` on the fix tip as well as `quality`.
- Turn on "do not allow bypassing" plus the required `gate` check on `engine/base` (open item 1).

**F5 [wrong]** `~/.claude/settings.json` (`"model": "fable[1m]"`), `NEXT-PHASE.md:57-63`.

*What breaks.* Sessions started by `start_session` inherit the caller's model and effort, so the whole chain runs on whatever the first session ran on. Subagents name `model: "opus"` and are fine; the sessions are not. The schema also says a session's `model` must be "same family or cheaper ... anything higher is ignored", so an Opus session can never start a Fable session. A challenge stage designed as its own Fable session cannot be started from the chain; it has to be a `model: "fable"` agent.

*Fix.* In NEXT-PHASE "How to start it", add `model: "claude-opus-5-5"` and `effort: "high"` (or the effort he picks), and have each phase skill's first line check that it runs on Opus 5.5 and say so if not.

**F6 [wrong]** `standing/phase_state.py:99-100,133`; `.claude/skills/ship-next/SKILL.md:8-12`.

*What breaks.* I ran it on a scratch fix folder and parent (`scratchpad/ps/`):

- Fix folder: `next: plan-review` / `why: scope_gate not set`. `STOP-REVIEW.md:52` writes the fix `PROGRAM.yaml` without `scope_gate`, and line 99 returns before the fix branch at line 109.
- A checkpoint with `notes/stop-A.md` and no `REVIEW.md` yet reads `next: stop-review`, though its review session may be running.

`ship-next` picks "the most recently changed one", which is the fix folder or the one under review, so "continue" starts plan review on a fix program or a duplicate review. Duplicate reviews spawn a second set of readers writing the same notes files, and two sessions may run Merge. Plan and plan review have no liveness either, so a second planner or plan reviewer can start on the same folder.

*Fix.* In `phase_state.py`:
- test `fix` before `scope_gate`;
- add `review_alive` (any `stop-review/<X>/*.md` or `SESSION.md` changed in the last 20 minutes);
- add `plan_alive` (the program folder changed in the last 20 minutes) and report `running` for both;
- have STOP-REVIEW write `scope_gate: {by: stop-review, at: <date>}` into fix programs.

**F7 [blocks]** `ship/kit state.py:175-181`, `check_plan.py:50-61`, `phase_state.py:108-115`, `STOP-REVIEW.md:77`.

*What breaks.*
- `check_plan` checks that every slice's stop exists, never that every stop has a slice. An empty stop is never "built" by `ship status` (it does not know the stop), so no `stop-X.md` is ever written and `phase_state` reports `build` forever.
- A stop whose slices all parked (several `BLOCKED brief-mismatch`, which park as `manual` and do not count toward the breaker) prints `CHECKPOINT X built`. Its review finds `FROM..TIP` empty, `gh pr create` fails with no commits, and Merge ends in WAITS. `ship merged` is never recorded, so the next checkpoint's pre-built slices stay `HELD` forever.
- `ship` takes checkpoint order from the order `SLICES.md` rows first name a stop. If the planner lists a B row first, ship opens B while the prompts expect A.

*Fix.*
- `check_plan.py`: every `stop_points` id has at least one slice, and stops appear in `SLICES.md` in the same order as in `PROGRAM.yaml`.
- `STOP-REVIEW.md` Round 1: "an empty checkpoint (no commits from FROM to TIP) skips readers, records `ship merged X` with the reason, and writes the parked list to WAITS".

**F8 [wrong]** `ship/kit power_watch.py:1-4,64-95`, `verify_ready.py:118-131`, `RULES-CARD.md:114`.

*What breaks.* HOLD is written only on battery. With mains on and the router or GitHub down, builders cannot push and `verify_ready`'s remote read or `gh pr create` raises `GitError`. The slice moves to `red`, the card sends a fix round (attempt 2), and the next failure parks it as `rounds`, which counts toward the breaker. One evening of an ISP outage can stop the run. The same goes for a `slice_checks` red caused by a network-dependent tool.

*Fix.* `power_watch` also writes HOLD when the internet or GitHub probe fails on mains, for as long as it fails. `verify_ready` returns a distinct exit code (3, "remote unreachable") that the card routes to "retry next wake", never a fix round.

**F9 [blocks]** `phase_state.py:62-68`, `STOP-REVIEW.md:82`, `RULES-CARD.md:128,132-134`.

*What breaks.*
- `coordinator_alive` is "`notes/LOG.md` changed in the last 20 minutes". A coordinator stalled on a usage limit (often hours), a long `land` or a permission prompt reads as dead. Merge step 8 then starts a coordinator in `{PROGRAM}`; when the limit lifts, both sessions' loops wake, and `ship-build` step 2 (the only guard) passed while the first looked dead. Two coordinators race `dispatch` and `land`.
- STOP-REVIEW waits "when every reader's file ends `DONE`" with no time limit. A reader stuck on a permission prompt or a hung command holds the review forever.
- The card's "Builder ended with no READY or BLOCKED line: Restart", together with "Restarts never count as attempts", is an unbounded loop for a builder that always dies, for example on a brief too large for its context.

*Fix.*
- Have the coordinator write `notes/COORDINATOR.lock` holding its session id, refreshed every tick. Before starting a coordinator, check the lock and the session through `list_sessions`.
- Give readers a `reader_timeout` setting: after it, restart once, then report the element as "not read" in the verdict, which blocks.
- Add a `max_restarts` setting (for example 3) that parks a slice as `manual` with "restarted N times".

**F10 [wrong]** `.claude/skills/ship-build/SKILL.md:10-11`, `COORDINATOR.md:104-113`.

*What breaks.* `ship-build` takes the program "from his words or the brief" and checks only `coordinator_alive`. Neither it nor Arm reads `scope_gate`, so "start building X" on a plan that skipped review, or whose review is still asking him, arms and builds. `phase_state` is the only place the gate exists.

*Fix.* Arm step 0: refuse when `scope_gate` is `null` and the folder is not a fix program, and point to "review the plan for X".

**F11 [friction]** Program folder locations disagree.

| Where it is defined | Location given |
|---|---|
| `plan-feature/SKILL.md:13` | `D:/QMX-worktrees/plans/<slug>/` |
| `PLAN.md:7`, `PLANNING-FUNNEL.md:180`, `templates/PROGRAM.yaml:4` | `D:/QMX-worktrees/<plan>/tracker/<program>/` |

- `PREFIXES.md:3`'s clash check greps `D:/QMX-worktrees/*/tracker/*/SLICES.md`, which misses `plans/<slug>/SLICES.md`, so prefix clashes between programs go unseen.
- A program under `plans/` is not in git: power loss or disk failure loses the plan, and it breaks "research lives in the repo".
- One under `<plan>/tracker/` sits inside a git worktree, where it is unproven that Claude Code reads `{PROGRAM}/.claude/settings.local.json`. The Run probe catches that, but the chain ends.

*Fix.* Pick `plans/<slug>/` everywhere, make `D:/QMX-worktrees/plans` a git repo (or a worktree of branch `plans`) committed at each phase end, and change the PREFIXES grep to `D:/QMX-worktrees/plans/*/SLICES.md`.

**F12 [friction]** Stale names that now mislead agents:

- `SHIPPING-METHOD.md:12` ("GitLab CI is paused ... he buys minutes ... Linux prints as not run"), `:13` ("integration"), `:110-117` (the "Later, on GitLab" table). Confirms GAP 2.2 and 2.4.
- `STOP-REVIEW.md:34,73,77,79` ("CI is paused", "Linux: not run (CI paused)", "Never merge into main or integration").
- `REVIEW.md:83`.
- `RULES-CARD.md:100`.
- `ship-merge/SKILL.md:8` ("Until GitLab is switched on").
- `BUILD-PHASE-REDESIGN.md:7` ("question 4: yes, local gate"), confirming GAP 2.5.
- `RESUME-2026-11-13.md:179` (ci/github head `54aaf83`; now `9eb1403`, "qmx-ci is the only workflow").
- The ship README on `51d95409` (line 132): "A CI backend replaces that function".

The committed kit has no `ci` command and no GitHub awareness, while the prompts' CI wording describes GitLab. Neither matches the stashed WIP.

*Fix.* One pass over these lines once the CI backend lands, naming GitHub Actions and qmx-ci levels. Until then, replace "CI is paused" with "qmx-ci is not on engine/base yet (PR #1); the gate is local".

**F13 [friction]** Placeholders the skills do not fill:

- `stop-review/SKILL.md:12-17` maps no `{SHIP}`, though `STOP-REVIEW.md:33,65` uses it.
- It maps no `{TARGET}` (used at :73-79), no `{TIP_ROUND_1}`, and `{REVIEWED_TIP}` only in prose.
- `plan-review/SKILL.md` maps no `{REPO}`, `{TIP_NAME}` or `{SLICE_IDS}` (GROUNDING needs them).
- `ship-build` has no `{SLICE_IDS}` for step 0.

`phase_state` prints `ship`, so an agent can infer them, but nothing checks it.

*Fix.* Add the mappings, and a closing line in each skill: "grep the filled prompt for `\{[A-Z_]+\}`; any hit stops".

**F14 [wrong]** `STOP-REVIEW.md:6` and `RULES-CARD.md:140` define `{FROM}` as "the `merged` sha of the previous stop", but `phase_state.py:106` gives the previous review's END sha. The merged sha is a merge commit on `engine/base`, so `ship quality --from <merged sha>` diffs the build tip against everything else that reached `engine/base`. mutmut then runs on other programs' functions, and their new findings land in this checkpoint.

*Fix.* Change both prompt lines to "the reviewed tip (END sha) of the previous stop".

**F15 [friction]** The plan-review to planner round trip (`PLAN-REVIEW.md:34-35`, `COORDINATOR.md:110`, `STOP-REVIEW.md:57`) uses "SendMessage to {PLANNER_SESSION}":

- `planner_session` holds a session id, while SendMessage takes a `ListAgents` name or `local_...` id.
- A session in a different permission mode "holds cross-session messages for its user's approval (and may let them expire)".
- The reply comes back as another session's message, so the plan-review turn that then gets his go cannot start the build (F1).
- "Wait for its reply" is not a blocking call; the session ends its turn and is woken later.

*Fix.* Prefer the FIXES.md route always (file plus "resume and apply"). Record in `PROGRAM.yaml` `planner_session` as the `local_` id, and say the reply wakes the reviewer.

**F16 [blocks]** `COORDINATOR.md:114-127`: Arm writes the hook settings and then needs a fresh session ("Hooks load when a session starts"). That start runs on an automated turn after step-0 grounding (F1), or right after his "go". If he steps away after "go", the build never starts.

*Fix.* Have plan review write `{PROGRAM}/.claude/settings.local.json` before it starts `ship-build`, so the first coordinator session already has the hook. Make `hook.py` allow `notes/`, `state.json` creation and `.claude/` while `state.json` is missing, instead of "refusing writes until it can" (`hook.py:96-97`), so Arm can run under the hook.

**F17 [friction]** No permission mode is named anywhere: `grep -rln "permission_mode|bypassPermissions|permission mode"` over the method and the 12 skills prints nothing. `start_session` inherits the caller's mode, and the user settings have no `permissions.allow`. Started from a default-mode session, the coordinator stalls on its first Bash call, and builders stall on theirs (edge case 8 was meant to prevent this), with no heartbeat to notice because the wrapper is not running yet.

*Fix.* State the required mode in `NEXT-PHASE.md`, pass `permission_mode` explicitly, and add a probe in Arm (a harmless Bash call that must not prompt).

**F18 [friction]** `RULES-CARD.md:107,132-134`: `STALE` sends the coordinator to "Restart", which stops every running builder and runs `ship recover`, which marks every held seat dead. One slow builder (45 minutes with no push or heartbeat) kills two healthy ones, and their unpushed work becomes leftover patches.

*Fix.* Give `ship recover --slice <id>` a mode that marks only the stale seat, and make the card stop only that builder.

**F19 [friction]** Parked work has no way back inside a run:

- `park` is terminal ("parked ... Next: none"). A design call or brief mismatch he answers days later in `WAITS-ON-YOU.md` cannot re-enter the run; the checkpoint merges without it.
- Round-2 BLOCKED reads `waits-on-him` (`phase_state.py:123-124`), and no skill acts on his answer.
- There is no abandon path. `KEEP-AWAKE`, the git config change and HELD slices stay armed, and "continue" keeps picking the program.

*Fix.*
- Add `ship unpark <id> --why` (allowed while the slice's checkpoint is open).
- Add an "answer" row to `ship-next` that reads WAITS-ON-YOU and routes his answer.
- Add `abandoned: <date>` in `PROGRAM.yaml`, which `phase_state` reads as `done`, with a `ship teardown` step.

**F20 [wrong]** Two programs at once:

- `dispatch`'s overlap refusal and `land`'s order are per program, so two programs can change the same files and meet only as a merge conflict into `engine/base`. `gh pr merge` refuses, the review writes WAITS and ends, and nothing resolves it (no `resolving-merge-conflicts` step).
- Each program arms its own keep-awake and `power_watch` and runs its own whole suite at checkpoints on one laptop.
- PREFIXES clash detection misses `plans/` (F11), and each merge stops the other run (F3).

*Fix.*
- Run one program at a time (say so in `SHIPPING-METHOD.md` "Settled"), or add a machine-wide `D:/QMX-worktrees/ship-quality/PROGRAMS.lock` that `ship init` reads to refuse file overlap across programs.
- Add a STOP-REVIEW merge step: "on a conflict, start a fix program whose one slice merges `origin/<target>` into the build branch".

**F21 [wrong]** Stale parent, confirming GAP 3.7 (`ship facts --tip` remains).

- Arm step 2 compares grounding's END sha with the build branch tip, and Arm step 1 just pushed the build branch at `parent_tip`, so they always match. `engine/base` moving between planning and build is never seen.
- Dispatch reruns facts only at the build tip.
- The funnel's "Re-ground if the tip moved" (`PLANNING-FUNNEL.md:116`) has no check.

*Fix.* Arm step 1b: `git ls-remote origin refs/heads/<target_branch>`. If it is not `parent_tip`, rerun every brief's facts at the target tip (a `python {SHIP} dispatch --dry-facts` or the planned `ship facts --tip`), and send any failure to step 0.

**F22 [friction]** `STOP-REVIEW.md:33` always runs `nightly ; quality`. With the WIP kit, `nightly` dispatches the GitHub deep run (which runs mutmut itself), and the README says `quality --from` is "for the local fallback" only. The laptop runs mutmut under WSL while GitHub runs it too. `ci status --wait` gives up after `ci_wait_timeout_s` (12 h) with no `summary.txt`, and the review tick restarts it, so a stuck GitHub queue becomes an endless wait with no line to him.

*Fix.* Run `quality` only when `nightly` printed "CI github unavailable". After two 12-hour waits, write WAITS-ON-YOU.

**F23 [friction]** The review session has no compaction or handover rule; COORDINATOR has one, STOP-REVIEW does not. Its heartbeat every 10 minutes outlives the prompt cache, so each tick rereads the whole context uncached for the hours the deep run takes.

*Fix.* Add "after a compaction, reread `stop-review/<X>/SESSION.md` and the map, and carry on from the first step not finished". Write progress to `SESSION.md` as each step ends, and consider a 30-minute tick while only the deep run is outstanding.

**F24 [friction]** Skill triggers misfire on his plain words:

- `ship-next` fires on bare "continue", "carry on" and "where are we", which he says in every session (a UI session, a research session).
- `ship-build` fires on "build it", and `plan-feature` on "design the pods" and any brain dump, which overlaps `bmad-brainstorming` and research asks.
- `stop-review` fires on "review what was built".
- `ship-next` also says "five shipping phases"; NEXT-PHASE says four.

*Fix.* Require a QMX program word or a pipeline phrase in each description ("continue the run/plan/program X"), and add one line to each skill: "if no program folder exists for the words he used, say so and stop".

**F25 [friction]** The `PROGRAM.yaml` template and the real index disagree (see "The program index" below):

- the template has no `chains:` section, though check_chain requires `program-chains-section`;
- `run_files` is stale: `review/` is "by reviewers and ship land", a retired mode, and `merge/<X>.md` is "by MERGE session", now STOP-REVIEW;
- `run_files` lacks `notes/stop-X.md`, `plan-review/FIXES.md`, `WAITING.md`, `HOLD`, `power.json`, `KEEP-AWAKE`, `preflight/`, `runs/`, `heartbeat/`, `leftovers.md`, `ship.toml`, `.claude/`;
- `done_when` is written and never read.

*Fix.* Add `chains:` to the template, regenerate `run_files` from `layout.py`'s paths, and have Merge step 7 quote `done_when`.

**F26 [friction]** `GROUNDING.md:110` finds a colliding commit's intent with `gh pr list --search <sha> --state merged`. On the new repo that returns nothing for any history before 13 Nov (PRs live only on the flagged account, GAP 4.3). Grounding then sorts every collision as a CALL, and each CALL parks a slice at Arm.

*Fix.* Say "PRs before 13 Nov: `gh -R MubarakHimself/QMX pr list --search <sha>` while that account answers, else `git log --format=%B -1 <sha>`".

**F27 [friction]** Disk:
- D: has 27.2 GB free and C: 25.9 GB, with 247 entries under `D:/QMX-worktrees`.
- Each builder worktree is about 0.4 GB, plus a `.venv` when `uv sync` runs.
- A review adds one detached checkout per reader plus the stop checkout.
- Preflight has no free-space check (`grep -i disk preflight.py` finds nothing).

A full disk mid-landing leaves a half-written worktree or a failed push that the card reads as a red. *Fix.* Add a preflight WARN under 20 GB free (a warning, not a gate, as `PROJECT-RULES.md:54` wants), and add the 219 stale worktrees to the cleanup the review's end step runs.

**F28 [friction]** New program folders may never have been opened in Claude Desktop. The `start_session` text lists "its folder was never opened in Claude Desktop" among the cases where a started session does not run on its own. Each new `plans/<slug>/`, fix folder and `D:/QMX-worktrees` itself may then wait for a folder-trust prompt. Not verified here.

*Fix.* Test once with a scratch program. If it waits, have plan-feature open the folder through `request_directory` / `change_directory` while he is present.

**F29 [friction]** A battery that runs empty, or an app restart or update, kills every session, background command (`power_watch`) and `loop` heartbeat; loops live in the session. Nothing restarts the chain after a reboot, and STOP-REVIEW's power section assumes the session survives.

*Fix.* Add one scheduled task (`mcp__scheduled-tasks__create_scheduled_task`, cron every 30 minutes). Its stored prompt runs `phase_state.py` and, for a program whose coordinator or review is not alive, writes `WAITS-ON-YOU.md` and a notification, or starts it through F1's `ship next-phase`. Scheduled tasks "run on next launch" when the app was closed.

**F30 [friction]** `phase_state.py` reads neither `WAITING.md` (planning) nor `notes/WAITS-ON-YOU.md` (a coordinator that stopped on the breaker or main-changed). "continue" restarts a coordinator that stops again on `BREAKER`. Line 118's "WAITS FOR HIS WORD" is written by no prompt; it is a leftover of the local-gate era.

*Fix.* Report `waits-on-him` when either file has unanswered lines, and delete line 118.

**F31 [friction]** The depth limit is enforced only in the QMX folder (`C:/Users/Mubarak/Desktop/QMX/.claude/settings.local.json`). The coordinator in `{PROGRAM}` and the review in `D:/QMX-worktrees` run with no depth limit, so "agents spawn none" there rests on prompt text alone. A builder that runs `code-review` or `arena` from a brief can fan out; `check_plan`'s `no-spawning-skills` covers briefs only.

*Fix.* Write `"env": {"CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH": "1"}` into the `{PROGRAM}/.claude/settings.local.json` that Arm writes, and keep a `D:/QMX-worktrees/.claude/settings.local.json` for review sessions.

**F32 [friction]** `gh` holds two accounts, `mubarakhimself-byte` (active) and `MubarakHimself`. No ship or prompt `gh` call outside the WIP kit names `-R`. Resolution works today (`gh pr list` resolves to the new repo through `origin`), but a `gh auth switch` to the old account makes `gh pr create` and `gh pr merge` fail or act on a hidden repo. `GROUNDING.md` and `STOP-REVIEW.md` Merge also have no `-R`.

*Fix.* Add `-R mubarakhimself-byte/QMX` to every `gh` line in the prompts, and add a preflight PASS line for the active account.

**F33 [friction]** The planning lead's model and the CLAUDE.md Fable rule still conflict (GAP 1.6, confirmed): `funnel-anneal/references/answer-linker.md:16` spawns `model: "fable"` without his ask. The challenge stage being added will add a second Fable seat. *Fix.* As GAP 1.6: record his 13:55 ruling in the project CLAUDE.md, naming both seats.

**F34 [friction]** The `ship` committed README still calls the shared baseline only `baseline-reds.txt`; known-reds handling (`ci/baselines/known-reds.txt`, T-23) exists only in the stash. Until the WIP lands, landing on a build branch cut from `ci/github` blocks on reds qmx-ci already accepts. *Fix.* Land the WIP after T-22 and T-23, with a README check that every command in `ship --help` has a row.

**F35 [friction]** The quality baseline is still not taken (GAP 3.6, confirmed). `quality.py` treats a finding absent from the baseline as new unless Vulture or Skylos also report it at the start commit. mutmut has no start-commit fallback (README: "known when it is in the baseline file or, for Vulture and Skylos, already at the commit the work started from"), so every surviving mutant in a changed function blocks the first checkpoint. *Fix.* Run `ship baseline --tools mutmut --part K/N` on the functions the first program touches before arming, or make the first checkpoint's mutmut report-only.

**F36 [friction]** `COORDINATOR.md:133` starts `power_watch` "as a background command". Background commands belong to that session, and the card ends segments while a review runs ("keep power_watch running"). An ended coordinator session keeps it alive only until the session is archived, which the review's last step does ("archive every finished session"), so a later stop's review finds no watcher (exit 2) and starts its own. That works, but no `power_watch` is ever stopped by the session that archived its owner. *Fix.* Have `power_watch` write its PID to `power.json`, and have `ship teardown` stop it.

**F37 [friction]** `D:/QMX-worktrees/ship-kit/tools/ship/tests/test_dispatch_recover.py:103,115-116` on the committed head `51d95409`. The test hard-codes `usage_reset="2026-11-13T05:00:00+00:00"` and expects dispatch to refuse until then. That time has now passed, so the test fails: `AssertionError: Refused not raised` (1 failed, 70 passed). RESUME's "71 tests green, rerun and confirmed" no longer holds at the committed head. The stashed WIP moves the date to 2099. *Fix.* Use a time computed from now (`now + 1 day`) in the test, and commit that change on its own, apart from the CI WIP.

## The program index (`PROGRAM.yaml`)

The ship scripts never read `PROGRAM.yaml`: `grep yaml tools/ship/*.py` finds nothing. They read `SLICES.md`, `checks.toml`, `ship.toml` and `state.json`, and take `repo`, `build_branch` and `worktree_root` as `init` arguments the coordinator copies. Everything else reads the index through `phase_state.py`'s regexes (`HEADER_KEYS`, `stops()`), `check_plan.py`'s regexes, `check_chain.py` and `chain_packet.py` (`chains:`), and agents reading it as prose.

| Field | Written by | Read by (phase) | Problem |
|---|---|---|---|
| `program` | planner (handoff) | check_chain, chain_packet (planning); prompts use `<program>` in names (`ground-<program>`, `stop-<program>-X`, `<program>-fix-X`) | Template: "also the folder name", unchecked. `phase_state` derives fix-ness from the folder name, not this field, and the two can differ |
| `repo` | planner | phase_state, then every skill's {REPO}; `ship init --repo` (build); STOP-REVIEW, GROUNDING | none |
| `build_branch` | planner | COORDINATOR Arm (ls-remote, init); STOP-REVIEW Merge (ls-remote, PR head); phase_state prints it | WIP `init` refuses names not `build/<name>` when `ci = "github"`; check_plan does not check the prefix |
| `parent_tip` | planner | plan review (grounding {TIP}); COORDINATOR Arm 1-2; phase_state `from` for stop 1 | Never compared with the target tip (F21) |
| `target_branch` | planner | ship-merge skill {TARGET}; STOP-REVIEW Merge prose; phase_state prints it | The stop-review skill does not fill {TARGET} (F13); the WIP kit has its own `ci_gate_base` setting: two sources for one fact |
| `worktree_root` | planner (template default) | phase_state, then skills; `ship init --worktree-root` | `quality_dir` is derived from it; a second program on another root would split the shared baselines |
| `ship`, `standing` | planner (template defaults) | phase_state, then skills | Not validated: fixture `standing: x` passes check_plan |
| `planner_session` | planner (PLAN end, resume) | plan-review skill; COORDINATOR step 3; STOP-REVIEW Round 1 step 8 | Holds a session id; the prompts send through SendMessage, which wants a name or `local_` id (F15) |
| `scope_gate` | plan review (step 6) | phase_state only | Not read by ship-build or Arm (F10); never written in fix programs, so phase_state misroutes them (F6) |
| `stop_points[].id` | planner | check_plan (as a set); phase_state (order); COORDINATOR Run 5 | ship orders checkpoints by SLICES.md, not this list (F7); no check that each stop has slices |
| `stop_points[].done_when` | planner | nobody | Written, never read (F25) |
| `stop_points[].merged` | STOP-REVIEW Merge 5 (template comment says "MERGE writes") | phase_state; COORDINATOR Run 5 | Duplicates `state.json` `merged`; prompts call it the next stop's {FROM}, phase_state does not (F14) |
| `files[]` (`path`, `serves`, `holds`, `updated_by`, `standing`) | planner | agents as prose; GROUNDING ("decision files PROGRAM.yaml lists"); check_plan only splits on `files:` | No script reads it. Template says SLICES.md is "updated_by ... the step-0 grounding agent (Files column only)", but plan review's grounding may not edit, and `ship init` refuses SLICES.md changes after arm |
| `run_files` | planner (copied) | nobody | Written, never read; stale and incomplete (F25) |
| `chains[]` (`ask`, `plan`, `arch`, `slices`, `edge_cases`) | planner (handoff) | check_chain, chain_packet (planning, plan review); STOP-REVIEW map (review) | Read but missing from the template, which only check_chain catches |
| `after_stop`, `fix_program`, `program_for_review`, `build_folder`, `reviewed_tip`, `tip`, `round`, `from` | nobody (phase_state computes them) | ship-build, stop-review, ship-merge skills | Computed from file names and verdict END lines, never written. A renamed folder breaks them |
| `merged` in `state.json` | `ship merged` | ship status, dispatch, land | Second copy of the same fact; COORDINATOR Run 5 reconciles only one direction |

By phase:
- Builders read no index field; they get the brief, `CHAIN.md` and `facts.log` from dispatch.
- Dispatch and landing read only SLICES.md and state.json.
- `ship-next` reads the header, `stop_points` and the merge, review and stop notes through phase_state.

## Where a new planning stage must register

For the challenge stage between Ground and Self-annealing. Not audited, only located:

1. `PLANNING-FUNNEL.md`:
   - the stage table (lines 54-61) and the section list ("The six stages");
   - "Rules at every stage: Models" (line 50), which names the only Fable seat;
   - "He is away" and "A tiny ask" (whether a light ask skips it);
   - "He changes his mind" (which stage reruns).
2. `standing/prompts/PLAN.md`:
   - the stage list (lines 202-209);
   - "Ask him only at stages 1, 3 and 5" (line 195): the challenge talks to him;
   - "The only Fable agent is ..." (line 191);
   - Resume step 1 ("each stage in order").
3. `standing/funnel/check_chain.py`:
   - `STAGES` (line 22);
   - the per-stage step functions (`steps`, line 523: `--stage handoff` runs every earlier step, so plan review inherits the new check for free);
   - the argparse choices (line 513).
4. `standing/funnel/tests/` needs a fixture for pass and one for fail, plus the `EXPECTED` table in `test_check_chain.py`.
5. `standing/funnel/CHAIN.md` needs ids for parked nice-to-haves (today's `P` proposals, or a new kind) and where the PR budget lives (`SCOPE.md` or a `PROGRAM.yaml` key). `templates/SCOPE.md` and `templates/PROGRAM.yaml` follow.
6. The budget's enforcement points, today warnings:
   - `check_chain.py:415-418` (`growth-justified`, `SLICES_PER_ASK_WARN`);
   - `check_plan.py:18,83-89` (`CHECKPOINT_WARN_ABOVE`);
   - `funnel-handoff/SKILL.md` (slicing);
   - `PLAN-REVIEW.md:180` (the `prs.md` "Count" review).
7. The skills:
   - `.claude/skills/plan-feature/SKILL.md` (no change unless the stage needs a placeholder);
   - a new `funnel-challenge` skill in `.claude/skills/` (ignored by git, so add it to the D: backup);
   - project `CLAUDE.md`'s skill list ("expand, ground, anneal, subtract, architect, handoff");
   - `standing/README.md`.
8. Phase and session plumbing:
   - `NEXT-PHASE.md`: no change if the stage runs inside the planning session. A separate Fable *session* cannot be started from the chain (F5); it must be a `model: "fable"` agent of the planning lead.
   - `phase_state.py`: no change for a stage inside planning, but a challenge waiting on him should surface as `waits-on-him`, which needs F30's `WAITING.md` read.
   - `SHIPPING-METHOD.md` pipeline row 1, and `RESUME`.
9. `PLAN-REVIEW.md` `scope.md` reviewer: check that parked items stayed parked and the slice count fits the budget.

## Walk: one program from his words to merge

| Step | What it reads | What it writes | "Done" file | Next start | Result |
|---|---|---|---|---|---|
| 1. He says "plan X" | His words | none | none | `plan-feature` skill in the QMX folder | **Done.** Works on his turn. On Fable if his session is default (F5) |
| 2. Funnel stages 1-6 | PLAN.md, the funnel skills, memory | `plans/<slug>/` (outside git, F11), `WAITING.md` when he is away | `check_chain --stage handoff` PASS plus `check_plan` PASS | none | **Done**, with a decision batch waiting on him at stages 1, 3, 5. Resume works from the checks. Plan liveness is unseen by "continue" (F6) |
| 3. Planner starts plan review | `NEXT-PHASE.md` | `notes/SESSIONS.md` | none | `start_session` user_asked, cwd QMX | **Works** when his message started the turn; refused when the last turn was an agent completion (F1). Model inherited (F5), permission inherited (F17) |
| 4. Plan review | PROGRAM.yaml, SCOPE, SLICES, decisions, memory | `plan-review/*.md`, `FIXES.md` | `scope_gate` set | none | **Done.** Four agents at depth 1 are within the limit. The round trip by SendMessage is fragile (F15) |
| 5. Scope gate, if he is away | none | nothing on disk | none | none | **Broken.** No WAITING file; AskUserQuestion holds the turn. If the session dies, phase_state says `plan-review` and a new review redoes all four agents |
| 6. Plan review starts the build | NEXT-PHASE | SESSIONS.md | none | `ship-build` in `{PROGRAM}` | **Works** only on a turn his own message began (F1); the scope gate is not rechecked by ship-build (F10) |
| 7. Arm | COORDINATOR Arm | state.json, ARMED.md, main-status.txt, `.claude/settings.local.json` | ARMED.md | Run needs a fresh session | **Broken** unattended (F16). Preflight may stop on updates not paused: designed, needs him |
| 8. Run, first checkpoint | RULES-CARD, state.json | worktrees, evidence, checks, LOG.md | `CHECKPOINT A built` | none | **Done**, with the scripts tested. Fragile: main-check (F3), outages (F8), stale restarts (F18), unbounded restarts (F9), T-22 once qmx-ci is on the parent (F2) |
| 9. Coordinator starts review A | NEXT-PHASE | `notes/stop-A.md`, SESSIONS.md | stop-A.md | `stop-review` in `D:/QMX-worktrees` | **Broken**: an automated turn, and the card opens in `{PROGRAM}` under the hook (F1) |
| 10. Review A, round 1 | the program files, `REVIEW.md` | `stop-review/A/*`, `checks/_nightly`, `_quality` | `REVIEW.md` END line | none | **Done** as written. The deep run is local on clean ship and GitHub on WIP (F22). No compaction rule (F23). Readers have no timeout (F9) |
| 11a. BLOCKED: fix program | templates | `<program>-fix-A/` | fix `notes/stop-A.md` | `ship-build` in the fix folder, then round 2 | **Broken** at both starts (F1). The fix folder misroutes "continue" (F6) |
| 11b. CLEAN: merge | Merge section | PR, `merge/A.md`, `merged:`, `tracker/REMOVED.md` | `merge/A.md` `MERGED` plus `ship merged A` | coordinator if not alive | **Wrong**: no CI gate, unprotected base, untested merge result (F4). The REMOVED.md edit races and stops runs (F3). Conflict has no path (F20) |
| 12. "continue" / ship-next | phase_state | none | none | the phase skill in this session | **Wrong** while a review or plan session is alive, or for fix folders (F6). It does not see WAITS (F30) |
| 13. Next checkpoint | `ship merged` | landings of HELD slices | `CHECKPOINT B built` | as 9 | **Done** if a coordinator runs; the two-coordinator risk (F9). The empty-checkpoint wedge (F7) |
| 14. Last checkpoint | Merge step 8 | RUN-REPORT.md, teardown | `next: done` | none | **Done** when no coordinator is alive. `run_report` by ask remains (known). `power_watch` is left running (F36) |
| 15. Program abandoned halfway | none | none | none | none | **Broken**: no abandon path (F19) |

Edge cases asked about, with where each landed:

| Edge case | Where it landed |
|---|---|
| Power cut | Battery covers mains loss (`power_watch` HOLD); an empty battery or a restart is not covered (F29) |
| Usage limit | Builders: `recover` and restarts. Coordinator: two-coordinator risk (F9) |
| Compaction | Planner: resume checks. Coordinator: hand-over rule (whose start is refused, so it keeps going). Review: none (F23) |
| Two programs | F20, F11, F3 |
| Stale tip | F21 |
| Merge conflict | F20 |
| Gate blocked forever | F2, F4 |
| Builder always BLOCKED | Parks `manual`, uncounted, leading to an empty checkpoint (F7) |
| Review never finishes | F9 |
| GitHub down or slow | F8, F22 |
| More than 3 refs per push | None found: builders push one branch, `land` one ref (`land.py:225`), Arm one ref; the BUILDER prompt does not forbid `--all` or tag pushes (nit) |
| Deleted or renamed branch | `delete_branch_on_merge` is false (`gh api repos/...`: `"delete_branch_on_merge":false`), so a merge keeps `build/*`; a manual cleanup of "merged branches" (his 13 Nov house-cleaning pattern) would delete a live `build/*` and leave `land` failing `land-push` every wake with no route |
| He answers days later | F19, plus the plan-review gap in walk step 5 |
| Reader hits a cache expiry | Background agents run without idling; the review session itself idles between ticks (F23) |
| Empty checkpoint, last checkpoint | F7; walk step 14 |
| Abandoned program | F19 |

## Covered

Read in full:
- **Method:** `SHIPPING-METHOD.md`, `RESUME-2026-11-13.md`, `GAP-AUDIT-2026-11-13.md`, `PLANNING-FUNNEL.md`.
- **Standing:**
  - `README.md`, `RULES-CARD.md`, `PROJECT-RULES.md`;
  - `REVIEW.md` (verdict section), `PREFIXES.md`;
  - `templates/PROGRAM.yaml`, `phase_state.py`.
- **Prompts:** `NEXT-PHASE`, `COORDINATOR`, `MERGE`, `PLAN-REVIEW`, `STOP-REVIEW`, `PLAN`, `BUILDER`, `GROUNDING`.
- **Skills:** the six phase skills (`plan-feature`, `plan-review`, `ship-build`, `stop-review`, `ship-merge`, `ship-next`).
- **ship kit:** `README.md`, WIP and clean; `hook.py`.

Read in part:
- **Method:** `BUILD-PHASE-REDESIGN.md` (Applied table, step 0), `EDGE-CASES-2026-11-12.md` (the list), `funnel/check_chain.py` (stages, chains), `check_plan.py`.
- **Funnel skills:** headers and spawn and model lines of all six `funnel-*` skills; `answer-linker.md`; `skills/slice-review/SKILL.md` (spawn, CI words).
- **ship kit:** `preflight.py` (checks, snapshot, arm), `armed.py`, `verify_ready.py`, `power_watch.py`, `state.py` (checkpoints), `status.py` (output words), `plan.py`, `land.py` (pushes); the WIP `ci.py` (`linux_gate`).
- **CI:** `.github/workflows/qmx-ci.yml` (levels, triggers, jobs), `tools/ci/qci.py` (`job_lint`), `ISSUES-2026-11-12.md` T-22 to T-24.
- **Settings:** `~/.claude/settings.json`, the project `.claude/settings.local.json`, `~/.claude/agents/poteto-agent.md`; the `start_session`, `send_message`, `SendMessage`, `create_scheduled_task` and `set_session_permission_mode` contracts.

Ran:

| Command | Result |
|---|---|
| `python tests/test_check_chain.py` | 20/20 fixtures as expected |
| `check_plan.py` on v00, v02, v06, v20, v22 | all PASS, exit 0 (v20 lanes-share-a-file passes here by design; check_chain catches it) |
| `check_chain.py --stage handoff` on v00, v22 | PASS |
| `python -m pytest ship` | WIP tree: 88 passed in 431 s. Clean `51d95409`: 70 passed, 1 failed in 254 s (F37) |
| `python -m ship --help` | 21 commands on clean, 22 with `ci` on WIP |
| `phase_state.py` | "no program folders found"; scratch runs for F6 |
| `gh api` repo settings | `delete_branch_on_merge` false, merge commits allowed |
| `gh api` on `engine/base` protection | 404, not protected |
| `gh pr view 1` | OPEN, MERGEABLE, head `9eb1403` |
| `gh auth status` | two accounts, new one active |
| `gh repo set-default --view` | none set; `gh pr list` resolves to the new repo |
| `git cat-file` on `origin/engine/base` | no qmx-ci.yml; old workflows trigger only on main, integration, `rebuild/**` |
| disk free | D: 27.2 GB, C: 25.9 GB |
| `claude` CLI | present |
| `.claude/scheduled-tasks` | empty |

Greps for stale words (`gitlab`, `not run`, `CI paused`, `minutes`, `integration`), permission mode, `scope_gate`, `PROGRAM.yaml` fields, `spawn`, `fable`, `model`.

Not covered:
- the challenge-stage addition (out of scope by brief);
- the funnel skills' bodies beyond spawn and model lines;
- `chain_packet.py` and `his_words.py` internals;
- the stashed WIP's other modules (`nightly.py`, `suite.py`, `land.py` changes) beyond the README;
- any live desktop test of `start_session` refusals or folder-trust prompts (F1 rests on the method's and the app's own text; F28 is unverified).
