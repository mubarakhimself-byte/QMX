# Final check of the fold and the build plan

7 Nov 2026. Independent of everyone who wrote these. Lenses: verification-gap and adversarial, applied by one agent with nobody spawned, plus blast radius. Code is `D:\QMX-worktrees\bld-repair-24` at `351e7521`, unchanged (0 lines in `git status`). Scratch scripts ran from `D:\Temp\final-check` and are removed.

## Verdict

**The nine blockers are closed on paper, and the plan is ready once the edits below are committed.** I found five faults the earlier checks missed. Two would have stopped the program outright, and all five are now fixed in the plan text:

- **Every PR would have failed its gate.** The gate reads `review/rc-01-check-<head8>.md`. The plan told the reviewer `rc01`, and lanes saved logs that the reviewer's `check-*.log` read never saw.
- **Stop A could not start from zero.** A backtest refuses a missing month, and the only synthetic month sits in the test fixtures. No G record meant no promote, so AD-24's row alone did not close the walk.
- **K7 and several tests sat in an env that can't import them.** The root env has no `qmx_tools`.
- **RC-02's census test could not pass.** It named `stages` one PR before the field exists.
- **RC-11's acceptance test was already green at the parent.** Its literal tested the wrong thing.

Nothing here ran the plan itself. Every PR's proof is still a test owed.

## 1. The nine blockers

"Fails today" means the PR's acceptance test would fail on today's code.

| # | Contract | PR and test | Fails today? | How far I got it |
|---|---|---|---|---|
| B1 | AD-23 | RC-09 `test_a_raising_logic_slot_leaves_exits_running`; RC-10 `test_k9_2_...` | Yes | **Ran.** Unit: `update` raising, 200 of 200 instants raised and `exits()` ran 0 times. Node, real `Runtime._drive` with a stub first unit: 12 bars, 12 raises, `dep-2` driven 0 times |
| B2 | AD-17 | RC-43 `test_k9_11_one_signal_one_send` | Yes | **Ran.** With `own_position` staying `None` over the synthetic month, the real unit mints 23 entries on EURUSD and 2 on XAUUSD. That is the premise. The two-send run is `CHECK`'s, not repeated |
| B3 | AD-24 | RC-18 `test_a_draft_reaches_paper_on_his_click`; RC-19 K7 | Yes | Read `machine.py:105-117`: no such row. **The row alone did not close the walk.** See section 3 |
| B4 | AD-25 | RC-30, RC-31 `test_k9_17_one_feed` | Yes | Read `runtime.py:2774-2781` |
| B5 | AD-10 | RC-05, RC-07 | Yes | **Ran** the shipped sizer: USDJPY answers 0.01 lots, losing 500 JPY. RC-05's literal wants 1.50 lots. I reworked all four literals by hand and they hold |
| B6 | AD-21 | `test_workspace_structure.py:138` | A guard, not a red test | Read. It keeps failing any such import |
| B7 | Section 10 | RC-14 before RC-22; RC-29 re-test | An order fact | `check_program.py` PASS on dependencies |
| B8 | AD-1 | RC-06 `test_account_facts_never_reach_the_exit_pass` | Yes | Read `unit.py:511`: `account` is read at the top of every step |
| B9 | AD-22 | RC-45 rows 1 to 6 and 11; RC-46 rows 7 to 10, 12, 13 | Yes, by `CHECK`'s run | All 13 rows land in a PR. Not rerun |

## 2. Buildability

**Sample.** RC-01, RC-02, RC-03, plus five drawn with a fixed seed (20261107): RC-08, RC-23, RC-43, RC-52, RC-60. Then RC-20's walk: RC-17 to RC-20.

**File claims.** A script read 53 plan and spine `file:line` claims against the code. 52 passed. The other was a miss by the script's window: `unit.py:990` is inside `_cold_reason`, as claimed. Separately, `check_program.py` confirms all 274 edited and 184 new paths. Every `plan-parts` literal with arithmetic was reworked by hand.

| PR | Could a fresh builder do it? | Fault found | State |
|---|---|---|---|
| RC-01 | Yes, after the fix | "`HostedUnit.exits`" is `_Run.exits`. "Library" test: qml's tests hold no Library | Fixed |
| RC-02 | **No, as written** | `stages` named one PR before the field exists; `reads` and `authority` already in `_CENSUS` (`test_unit_refuses.py:33`) | Fixed |
| RC-03 | Yes, after the fix | The numbers are `risk_fraction` and `target_r`; `fraction` and `multiple` are block parameters | Fixed, and in the brief |
| RC-08 | Yes, after the fix | The tape test sat in `qmb/tests`, which never imports `qmn` | Fixed |
| RC-11 | **Test was false** | Fills already read the closing side (`fill.py:1306`), so "closes on that bar" is green at the parent. The fault is the stop's level (`unit.py:574-576`) | Fixed |
| RC-17 | **No, as written** | See section 3. Also `unit_new` tested in `qml/tests` | Fixed |
| RC-18 | Yes, after the fix | Tool-table test in root `tools/tests`, which can't import the catalog | Fixed |
| RC-19 | **No, as written** | K7 in the root env; no box for the rows promote reads | Fixed |
| RC-20 | Yes | None. `publish_signed` is a real name | None |
| RC-23 | Yes, after the fix | "Add" named fields that exist; `Authority` has one value today (`model.py:203`) | Fixed |
| RC-39 | Yes, after the fix | Bar counts 60, 60, 4 were wrong: `canary` is 15-minute, so 4, 60, 4. K7 in `qml/tests` | Fixed |
| RC-42 | Yes, after the fix | Created `group_run.py` with no box for it | Moved to RC-52 |
| RC-43 | Yes, after the fix | Parent wording was about a fix never applied | Fixed |
| RC-52 | Yes, after the fix | Replay-against-node test in `qmb/tests` | Fixed |
| RC-60 | Yes, after the fix | Library test in `qmn/tests`, which can't import the Library | Fixed |

**Too big for one builder?** RC-39 (13 block files, 3 templates) and now RC-17 (template, records, month, landing, motion) are the largest. RC-42 is the riskiest, not the longest. I split none, since ids stay stable. See "Can wait".

## 3. Stop A, walked

| Step | Before these edits | Now, on paper |
|---|---|---|
| Copilot makes it | `unit_new` with overrides exists (`functions.py:843`), and the folder lists templates (`:811`) | Holds. RC-17's test uses it. The `build-unit` skill still says "QMB tests it after" publish until RC-47; a draft's object id does backtest (`test_qmb_app.py:279-300`) |
| Bars from zero | **Failed.** `backtest_run` reads market-store months and refuses a missing one (`test_qmb_app.py:424`). The synthetic month is only in test fixtures | RC-17 ships it and `practice_start` copies it in as source `practice` |
| G record | **Failed**, from the above | RC-17 test |
| Records | **Failed.** Promote reads `account`, `venue`, `instrument` from `main` (`promote.py:378`). RC-17 only shipped a JSON | RC-17 lands instruments, RC-19 lands account and venue |
| His click | RC-18 | Holds |
| Trades on paper | RC-19, K7 | Holds, unproven. **RC-19's fallback ends K7 on the fake broker if practice can't bind** |
| Sizes itself | RC-06, RC-07 | Holds. Reads the account's equity |
| Moves a number | **Not promised.** Size and exit numbers first move at RC-26, in stop B | **A filter number only.** RC-17 now keeps `min_trend_strength` moving, 0 to 0.0001, as `CHECK` ran on the dummy. Plan head and the prompt now say this plainly |

**Honest answer.** Stop A delivers a unit that trades on practice paper from zero history and sizes itself, and that a copilot can make. It moves a filter number, not a size. It is not "a stranger uses it tomorrow": no installer exists, and OPEN row 8b has no owner.

## 4. The prompt

- **Stops cleanly if repair isn't done: yes.** Its three checks all pass today: `## CLOSED` is the first section, Counts reads `24 built, 24 gated`, the remote head is `351e7521`, and the last ledger row is r24 CLEAN. The stop message is plain and it writes nothing first.
- **Tools it copies exist:** `env.sh`, `guard/`, `run_tests.sh`, `safe_host.py`, `repair_check.py`, and `gate-dsh`, `carry` and `alive` all exist. `poteto-agent` exists.
- **Unattended: safe.** No merge, no `main`, one fix round then park, no live binding, time limits on tests.
- **Stays out of others' files:** by rule for `R`. I added `P` as read-only, since a run ticking plan boxes would dirty the plan branch. It shares `.ci-lock` and `.engine-lane-lock`, and reads the `qma-ship` plan login, as designed.
- **His clicks and gates: plain.** "Commit first" read as his job, and is now the lead's.
- **Not checkable from disk:** "no tick is armed" and the 96% usage figure name no way to read them. Both are UNKNOWN and fail safe.

## 5. PR count and machine

**69 is honest.** Per slice against the spine's 52: 0:2/2, 1:2/2, 2:4/4, 3:4/3, 4:4/4, 5:4/3, 6:2/2, 7:4/3, 8:3/3, 9:5/4, 10:5/3, 11:9/4, 12:4/4, 13:5/3, 14:3/3, 15:3/2, 16:3/1, 17:3/2. That is 17 more: 6 added (RC-20, RC-48, RC-66, RC-39, RC-47, RC-57) and 11 splits. No split adds a seat the spine lacks.

**The trims held.** No PR builds `run_budgeted`, a reservation type, a group order slot, a proposal writer or a Lab driver.

**Machine he didn't ask for, left for the lead (none blocks):**

- **RC-63** is mostly unneeded. `backtest_run` already has `motion: both`, which "reports both". What's left is run arms, which are methodology's, and a row with no writer plus a test that it has none.
- **`propensity`** on `would_have` (RC-15), and **`alarm_budget`, `share_cap`** on the group (AD-8) have no reader in this program.

**Missing from what he asked:** nothing in M49 to M56 or Part C is unplaced. Every H line has a PR or a named session (`check_program.py`). Spot-checked against his words, these fall short, and each is named:

- **M49 "use tomorrow" (H-08, H-43):** the release lane, no owner.
- **H-17, live:** RC-67 to RC-69, his sign-in, his click.
- **H-75, a Lab unit:** no Lab exists, so that path waits.
- **M50 file format:** tooling config, no PR.

## 6. Every edit

Plan changes are in `plan-parts` (the source), and `PLAN.md` was rebuilt. `check_program.py` reports 0 failed checks and `check-plan.mjs` 0 problems.

| File | Edit |
|---|---|
| `plan-parts/assemble.py` | Review file is `rc-nn`, as the gate reads. Lane logs are `check-<slug>.log`, as the reviewer reads |
| `prs-a.txt` | RC-01 `_Run.exits`, fixture folder. RC-02 box and test. RC-03 `_CENSUS`, `risk_fraction`, `target_r`, new test. RC-04 `risk_fraction`. RC-08 test to `qmn/tests`. RC-11 literal and lane. RC-17 new boxes (month, landing, filter motion), new tests, test paths, `practice_bars` moved here. RC-18 test to `qmx-tools`. RC-19 landing box, K7 to `qmx-host/tests`, env named |
| `prs-b.txt` | RC-23 box and label. RC-25, RC-26 number names. RC-27 `basis`. RC-39 bar counts, test paths. RC-42 drops `group_run.py`. RC-43 parent wording |
| `prs-c.txt` | RC-52 creates `group_run.py`, test to `qmn/tests`. RC-56 hysteresis literal. RC-60 test and trace script to `qmx-host/tests` |
| `plan-parts/00-head.md` | Stop A states what moves and what doesn't |
| `plan-parts/90-tail.md` | Appendix C, the census file is shared. Appendix H rows 2, 3, 4, 5, 6, 8, 9, 11 settled or sharpened. Rows 1, 7, 10 stand |
| `BRIEF-BUILDER.md` | Traps added: census file, where tests live, parameter against number names |
| `PROMPT-ORCHESTRATOR.md` | Newer head logged in `S`. `P` read-only. `{id}` defined. Stop A plain. "Commit first" is the lead's |
| `D:\QMX-worktrees\risk-ship\PROMPT-ORCHESTRATOR.md` | Copied. The brief has no copy there yet; step 3 of arming makes it |
| `arch/final/OPEN.md` | Rows 14, 21, 22 and the assumptions line |
| `arch/final/WALKS.md` | Walks 1, 3, 8, 11, 13 and summary rows 3, 11 |
| `arch/final/FIXES.md` | The note on OPEN and WALKS |
| `arch/final/SPINE.md` | Slice 9's "ends in" (fixture units). K9 test 4's slices |

Nothing was deleted. IDs are stable. Section 6 of the spine still says "synthetic bars", which RC-17 now supplies.

## 7. What remains

### Must fix before builders start

1. **Commit these edits** on `plan/risk-core`, with `git add -f` where needed. All are uncommitted. The lead does this.

Nothing else blocks. OPEN's rows all run on their defaults.

### Can wait

| Item | Why it can wait | Watch at |
|---|---|---|
| RC-19's practice venue may not bind through promote, since `venue_records` is cTrader only | Its fallback holds, but stop A would then be short for a stranger | RC-19 |
| RC-17 and RC-39 may run long for one builder | The fix-round rule parks them. The lead may split them | RC-17, RC-39 |
| RC-59 needs the block contract in shipped code, since `blocks_save` can't import a test file | Its builder must move it | RC-59 |
| RC-30's move from 900 to 60 seconds touches an unmeasured number of pinned tests. Where the setting's default row lives is UNKNOWN (`ctrader_account.py:116` names it; no hit in `control/service.py`) | Lane 1 shows it | RC-30 |
| RC-49's stale-click test belongs in host tests | The brief's new trap covers it | RC-49 |
| RC-63, `propensity`, `alarm_budget`, `share_cap` | Trim or keep, lead's call | RC-15, RC-49, RC-63 |
| His big choice, what a pod is, and who owns release | Defaults stand (OPEN rows 1, 8b) | Stop B, stop A |
| "No tick armed" and the 96% figure can't be read from disk | Both fail safe | Arming |

## What I did not do

I did not run any suite, K7, real cTrader, or a 200-unit run. I did not rerun `CHECK`'s two-send, no-stop or 26-second runs. I read PRs outside the sample for literals, not for depth. I did not read `harvest/`, `E1` to `E5`, or the operator words before M49 except as `SEEDS-2.md` quotes them.
