VERDICT: FIX

Review of R01 to R14 and the plan's head, at `50c83a4e`. Three blockers, seven fixes, six notes. The plan's order and most of its claims about the code hold. My proof scripts are in `D:/Temp/audit/plan-review-a/`. Levels: 2 pointed at the line, 3 walked, 4 ran.

## 1. Findings

**plan-review-a-1. R03. Blocker. A library repair changes the signed trading node with no signature.**
The `triage-7` box says "If only the path sources differ, install the same bytes". On a money app that rebuilds the environment of the signed hash, because environments live at `envs/<hash>` (`supervisor.py:509`) and the hash covers only the app folder. `apps/trading-node` is `risk = "money"` and takes `qmn`, `qmb` and `qml` as path sources. So at his next host start, new order code runs under the old signature and nothing asks him. This breaks M5 and call 11 says it does not. R20 to R23 all change `qmn`, so it is the normal path. R03's money test and lane 5 change a file in the folder, so they would stay green.
Evidence, level 4, `money_env.py`: same bytes install on a signed money app is accepted, "uv rebuilt env of the signed hash: True", asked `--reinstall-package=qmn`, then "start asks for a signature: False", runs the signed hash.
Edit:
- In the `triage-7` box, write: "The path-source branch is for non-money apps only. A money app is never rebuilt under its signed hash. Its status says a library repair waits for a new signed version."
- In "PR mechanics", add: "A PR that changes a library in `apps/trading-node`'s lock also bumps that app's patch version, so the repair arrives as a new hash for him to sign."
- Add a test `test_a_library_repair_does_not_touch_a_signed_money_app`, which asserts uv is not called. Make lane 5 change a library too.

**plan-review-a-2. R14. Blocker. Check 18 can pass while the copilot built nothing and traded nothing.**
`unit_new` defaults to the dummy template (`functions.py:719`). The dummy's title is "Trend pullback" and the sentence asks for "a simple trend unit". A chat can call `blocks_find` once, then `unit_new` with no overrides, check it and backtest it. Every assertion in R14's box then holds. "It does not assert which verdict" also lets `overall: no_trades` through, which is catalogue case QB-15. No other model lane is sure to run an agent writing a new rule: R05's lane 5 is a menu lane, and check 5 calls the rows from Python. So all 18 can read PASS and "can agents build units" is still unproven. Level 3.
Edit to the R14 Build boxes:
- Change the sentence to name a rule the dummy lacks: "Build me a unit on EURUSD from the dictionary blocks that only enters when ADX is above 25, backtest it on March 2025, and tell me in plain words what the judge says."
- Assert from the store that the draft binds `adx@1` and `value-above@1`, and that the result has at least 1 trade.
- Assert the last message holds the verdict's words from `says()`. The word `incomplete` reads "Not judged yet", so a search for the raw `overall` would fail for no reason.
- Keep "does not assert which verdict". Update "You see" with the same sentence.

**plan-review-a-3. R14 and the boot recipe. Blocker. Check 18's harness does not exist as written.**
The box says to open the harness "on the ship home's plan login" as `owner_lane.py copilot` does, on "a scratch home". Two things stop this.
- A chat's login lives at `<home>/claude` (`home.py:133`), and `owner_lane.py:145` simply runs with its home set to the ship home. A scratch home has no login, and PROMPT rule 17 forbids copying one.
- That in-process harness has no lander. `attach_landers` is called only at `host.py:1114`, and `control_service` adds none, so `backtest_run` answers `unknown_lander`.
I found no earlier lane that ran a model chat on a scratch home with QMB. `a8-write.log` is not on disk. The first lanes that hit this are R04 lane 6, then R12 lane 4 and R13 lane 4, which are in the proving set. Level 3.
Edit:
- In the boot recipe, state the method once. My suggestion, a guess not yet run: make `<scratch>/data/claude` a directory junction to the ship home's `claude/`, so nothing is copied, under the lane lock. Have the coordinator prove it at arming with one `haiku` turn. If it fails, the coordinator stops and reports.
- In R14, make check 18 go through a real host on the scratch folder, over its chat routes, which is what lane 5 already describes. Then lane 5 can go. Rule 8 wants the real neighbour, and the in-process path would be a kinder composition than his.

**plan-review-a-4. R11. Fix. The writer's `spread` call is right, but its test for "late" leaves two doors open.**
The box keys on "a written study first made after any of the results' tries". Open doors:
1. Edit an older study after reading the result. Its first version predates the try, so it keeps its k. `land_spec_edit` lands nothing if no result used that study.
2. `origin` is a free field (`judge.py:196`, and the schema allows `quick`). An agent can write its own study as `quick` and take the exemption.
Evidence for door 1, level 4 on today's code, `shrink2.py`: honest study `fx.m02` shrunk 0.0558, weight 0.0000. Older idle study edited after the result: shrunk 0.2193, weight 1.0000, deflated Sharpe 0.7084, 0 `spec_edit` tries. R11's new rule does not reach this case, level 3. Door 2 is level 2.
Edit:
- Key on the version named: "the study version named was made after the earliest try of the results' families". `_tries` already returns the family, which also closes a rerun after reading.
- Exempt only a `study-quick-*` item whose fields equal `quick_spec`'s.
- Add the edited-study case to `test_a_study_written_after_the_result_counts_a_try`.
- Also, `estimate_k` falls back to `spec.k` under two markets (`shrink.py:43`), so use `FALLBACK_K` for a late study. Harmless today, but "whatever k it names" should be true.

**plan-review-a-5. R13. Fix. After R13 a unit that compile refuses gets a "pass" on a Library-only market.**
`check/run.py:67` calls the compiler only when the layers found no errors. On GBPUSD `no_record` is an error, so compile never runs. `offline_checked` then moves that kind to notes and answers pass. So everything R04 and R05 refuse (sessions, a second stop, `veto`, an unread binding) is invisible to the hook and the gate on those markets. R13's "You see" says the agent "hears exactly what is wrong", and R04's head says "every door reaches the compiler". Neither is true here. The lander still refuses later, with its first message only, so this is lost feedback and not lost money.
Evidence, level 4, `offline.py`: a halt on GBPUSD, `checked` errors `['no_record']`, nothing left after the move, while `compile_unit` says `['halts_not_built', 'no_record']`. On EURUSD it reads `not_compiled: halts_not_built`.
Edit: `offline_checked` also calls `compile_unit` and keeps its problems outside the five kinds. Add `test_a_second_stop_on_gbpusd_keeps_its_error` to check 17.

**plan-review-a-6. R03. Fix. `_server_install` cannot take `refresh_first_party`.**
The box says to use it at `connect_node.py:1272`. But `ServerApps.install(app_id)` takes a name over SSH (`:1080`). It has no folder, no head, and no local `BUILT_FROM` to compare. A builder following this stops or breaks `test_connect_node_server.py`. Level 2.
Edit: drop `_server_install` from the box. It keeps `_installed(...) or install`, and the server's own host start runs `enable_first_party`.

**plan-review-a-7. R08. Fix. The plan does not say which series a market reads.**
The box says `_bars` "asks the door for the market's series". The door lists series by `<source>/<SYMBOL>/...` and nothing maps a market to a source. Dukascopy ticks, derived pairs and old `risk-lab/<symbol>/bar-m1` pairs can all hold EURUSD. "Prefers pairs" plus "no stated scale is refused" means an old `risk-lab` import with no scale could block good Dukascopy ticks. Two sources could also silently change a result. Level 2, with `bridge.py`'s series names and `ground-qmb`'s shape table.
Edit: state the rule. For example, the source is `dukascopy` unless the request or study names one, and two usable sources for one month is a refusal naming both.

**plan-review-a-8. R06. Fix. Check 3 does not sweep the blocks R06 adds.**
R04's sweep walks "each of the 112 blocks" in `*/1/`, and R05's and R06's own boxes say those walks skip version 2. R06's nine runnable session blocks get tests against goldens and the clock, but none is driven through `compile_unit` and `on_instant`. `test_nothing_silent.py` is not in R06's Files. So "every stdlib block acts or refuses" stops being true at R06, in exactly the area R05 warns about. Level 2.
Edit: R06 changes the sweep to walk every version and adds that file to Files. With `session_start` at its default, each `@2` acts or refuses.

**plan-review-a-9. R04. Fix. The mirror refusal has no test, and after the test-272 rewrite no test uses `mirror_of` at all.**
`git grep mirror_of` under `qml/tests` finds only `test_compile_dummy.py`. The table in `test_each_part_format_2_does_not_run_refuses_with_a_pointer` has no mirror row, so dropping `p0a-9` fails nothing. Level 2.
Edit: add one row, the dummy with `short: {"mirror_of": "long"}`, expected `(kind, /logic/short/...)` with the hint.

**plan-review-a-10. R14. Fix. The runner can read PASS on a skipped test, and lane 2 asks for red logs that do not exist.**
- The runner prints PASS on exit 0, and pytest exits 0 when every test skips. Check 18 skips unless `QMX_TEST_LIVE=1` is set. Other tests in this repo skip on a missing machine fact. Level 2.
- Lane 2 matches each check to "its PR's lane 2 log". But R05's lane 2 runs `proof_units`, R06's runs `proof_edges` and `proof_settle`, and R12's runs `test_sweep_verdict`. None of these runs check 5, 7, 15 or 16's test. Level 2.
Edit:
- Read pytest's summary, count skipped as FAIL, and add that case to `test_a_failing_check_prints_fail_and_exits_non_zero`.
- Point lane 2 at each PR's `owner-red.log`, which names the test. Or copy the tests to the parent as R08's lane 2 does.

**plan-review-a-11. R05. Note. A `trigger` slot of only feeders writes a "near miss" row on most bars.**
`trigger_held` is true for any held trigger slot (`unit.py:600`), and a failing side with it true always writes a row (`:709`). Level 3. Edit: `trigger_held` counts only a slot with at least one condition.

**plan-review-a-12. R04. Note. "A `position` input port" is misleading.**
No port has that name. It is `entry_price`, with `stream_kind: position`. By port name the three trails pass (`a1.py`, level 4). By kind all six are caught. The table row would catch the slip. Edit: say `stream_kind`.

**plan-review-a-13. R01. Note. Lane 2's pass line cannot read as written.**
At this commit the grep also hits `qa/_trace/battery/mutmut/mutmut_config.toml:35`, `qmf-core_pyproject_used.toml:46`, `pyproject.toml:235,301,326-330,357,405,506` and `skylos.yml:92`. None is in the Build box (ran). `tools/ci.py` does not care, but a literal coordinator sends this to a fix round. Edit: add those pyproject and skylos lines to the box, and exclude `qa/_trace` from the grep.

**plan-review-a-14. Head. Note. The transcript script has two names.**
Head rule 1, the Arm box and the Verdict box say `S/tools/audit.py`. `PROMPT-REPAIR.md` says `S/tools/repair_check.py`, and that is the file that exists. Edit: use the second name in the plan and in the shape.

**plan-review-a-15. Head. Note. "All boxes checked" cannot be met.**
Every section says a PR is verified only when its live boxes are all checked, while the head says lanes 5 to 10 are a menu with at most one run. Edit: one head line saying an unchosen menu lane is marked "not chosen" and that counts as checked.

**plan-review-a-16. R04. Note. Check 3's pass is softer than its words.**
"Its output is read as a condition" passes a block that is false on every bar of the month, which is close to "check pass, zero signal, no reason". Level 2. Edit: print the list of read-but-never-fired blocks as a literal in the test, so a change shows.

## 2. Sound

**The writer's three calls.**
- R11, a late study judges with `spread`: right, and tighten it per finding 4. `shrink.py` line 5 says a study fixes its estimator before any run, and the honest study already reads the 0.0558 the test wants (ran).
- R05, a slot of only feeders holds: right. `side()` needs every slot to hold, and nothing combines slots with `any`, so an empty slot is neutral. A side of only feeders needs a contrived loop, because the last binding of any chain must be a condition or it refuses (walked). The one side effect is finding 11.
- R04, test 272 with an explicit short side: right. Ran at this commit: windows `derived.short.rsi_low: 286`, warm-up same, and its 23 entries are identical to the mirror's. Finding 9 is the gap it leaves.

**The head and checklist.** All 12 rules, the five gates and the whole-repo schedule are there. Every proof script and helper the plan copies exists on disk. `build/us-c14` is `50c83a4e`. Every required skill exists. A coordinator can run without asking, apart from findings 3 and 14.

**Safety facts checked.**
- R01: nothing in the product names the cut folders (grep). `qa/tests/epic_12/_world.py` only mentions `qml/examples` in a comment.
- R03: `expected_hash` is the selected head, as the box says (`supervisor.py:455`). `start` takes a non-blocking lease and answers `volume_busy` during an install, so releasing the lock cannot deadlock (`volume.py:205`). `call`, `run_job` and `start` all take the lock as claimed. `run_job` opens the lander outside the lock (`:1251-1274`), so R08's slow copy does not bring the stall back.
- R04: the extra refusals the long trial did not carry (no stop, second exits, exits by rule, sole `at`, blocks not built, format 2) passed `test_check_layers.py` 364 of 364 and `test_wave1_beyond_fx.py` 83 of 83 (ran). The dummy, the three corpus twins and `b`'s fixture meet no new refusal and no `binding_not_read` (`a1.py`). No exit reads a slot output, so the rule cannot wrongly refuse one. The compiled fingerprint holds the format version and no records, and no golden pins a compiled fingerprint (grep).
- R05: the plan's claims about `combine`, `any` and `k_of_n` on an empty list match the code. Moving the dummy to `@2` left the real months identical in memory, March 29 trades, net 22.84, and January to March 110 trades, net -1566.40 (`floor2.py`). So R07 to R10's literal lane numbers survive R05.
- R07: the fixture copy and the per-pin cache are as described. Records sit outside the fingerprint (`compiler.py:551-558`).
- R08: the sealed `materialise` trap and the door's method list are as described.
- R13: the hook test keeps running without `QMX_TEST_LIVE`, because only the model test is marked to skip.
- Promises: apart from finding 1, I found no box that breaks E1 to E12 or M1 to M11. I read R09, R10 and R12 against their reports and the lines they name, and did not run them.

**Size.** I would cut nothing large. Each PR adds a few tests that cross a real connection, which keeps to his rule. Lane 8 in R01 and R02 runs "new tests" where none are added, which is harmless in a menu.

## 3. Rows

No must row in R01 to R14 stays uncured once findings 1 to 3 are applied. Not fully cured as written:
- `triage-7` (should): the money path is wrong, finding 1.
- `p2-5` (should): the older-study door stays open, finding 4.
- `p34-9` (should): the hook stays silent on compile refusals, finding 5.
- `p0a-9` (should): it has no proof, finding 9.

## 4. For the chief engineer

- **Call 11** says R03's supervisor changes "break no promise". The path-source branch breaks M5, level 4. The shape's check 1 reads as if the library half and the money half were separate, and they meet here.
- **The shape's check 18** is the right test, and its words ("builds a unit from dictionary blocks") are stronger than R14's assertions. Finding 2 holds the plan to the shape, and the shape needs no change.
- **The shape's rule 1** names `tools/audit.py`, and the file built is `repair_check.py`.
- **R20 to R23** are not in my sections. Finding 1's bump rule adds `apps/trading-node/app.toml` to each one that changes `qmn`, so plan-review-b's Appendix C reading changes. Tests pinning that app's version move too.

## 5. Not reached

- `test_conformance.py` under the format bump. My 55-second limit killed the run while its workers were starting, which is not a finding. No golden holds a compiled fingerprint (grep).
- R04's wider refusals over all of QML. I ran two files. Long run for the orchestrator:
  `source D:/QMX-worktrees/audit-ship/tools/env.sh && cd D:/QMX-worktrees/audit-head && PYTHONPATH="D:/Temp/audit/plan-review-a/plug;$PYTHONPATH" timeout 1200 "$AUDIT_ROOT_ENV" -m pytest qml/tests -q -p refuse_more -p no:cacheprovider --no-cov --basetemp=D:/Temp/audit/plan-review-a/long1`
- The junction in finding 3. It is a suggestion, not run, because I may not touch a login.
- R09's calendars and `derive_month`, R10's `p0b-14` and `p0b-15`, and R12's `p6-5` row: read against their reports only. All three name their own stop rule if the shape fails.
- R06's `p1a-4` settle scaling: the plan already marks it unproven and names its stop.
- The `b`, `u1` and `u2` template files themselves.
