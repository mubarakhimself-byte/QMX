"""The chaos suite (unit U12, FACTORY-DESIGN section 13): every row of the edge-case matrix (section 6) that names
a script, the hand-offs between the branches (13.4) and the loops of 3.9 (row 57), each a named scenario.

Most are `chaos` scenarios: the conveyor (`ship chain`) on a scratch repo with scripted agents
(`tests/chaos.py`), broken on purpose, then read for the end state it must reach. A row another unit's test
already covers gets a test here that names it (`covered(...)` asserts the test exists), so the table stays whole
and a renamed or deleted test fails here. A row the lead's later decisions changed says so in its docstring:
the D-L wins. A scenario that showed a kit bug (F1 to F9, G1) was fixed under D-L26 and now passes.

Run: `cd tools && python -m unittest ship.tests.test_chain_chaos` (or pytest). No real Claude run, no real
merge, no scheduled task; the factory home is a temp folder. The factory's own fixtures (rows marked
`fixture`) run only where the factory checkout is (`FACTORY_HOME`, default `D:/factory`), read-only.

Coverage (row: test, or drill, or "not testable here: why"). `chaos` = here; `kit` = another kit test, named.

| Row | Failure | Covered by |
|---|---|---|
| 1 | power cut, battery lasts | chaos `Power.test_battery_holds_then_resumes`; HOLD inside review and merge: kit `test_k4a.HoldScope` (`Named.test_row_01_hold_inside_review_and_merge`); drill D1 |
| 2 | laptop dies or restarts | chaos `DeadLaptop.test_dead_laptop_resume_all`; mid-land (F9): `LandKilled.test_land_killed_mid_git_is_recovered`, `LandKilled.test_a_land_that_keeps_crashing_waits_after_its_restarts`, `LandLock.test_a_lock_with_git_running_in_the_copy_stays`; drill D2 |
| 3 | internet or GitHub down | chaos `Network.test_remote_down_is_not_a_failure`; drill D5 |
| 4 | usage limit | chaos `Limits.test_usage_limit_sleeps`; drill D4 |
| 5 | the app is closed | chaos `Detach.test_detached_conveyor_outlives_parent`; drill D3 |
| 6 | context fills (planning lead) | fixture `d09-resume-mid-anneal` (factory, U21): `FactoryFixtures.test_row_06_resume_mid_anneal` |
| 7 | a worker hangs | chaos `Hang.test_hung_builder_restarted_alone` (kit twin `test_run.Faults.test_stale_builder_is_restarted_alone`) |
| 8 | a worker replies nonsense | chaos `Garbage.test_garbage_builder_parks_after_three` |
| 9 | he is away at a gate | chaos `Gates.test_away_at_go` |
| 10 | he answers days later | chaos `Gates.test_answer_then_go` (10a); kit `test_run.Unpark` and `UnparkPins` (10b): `Named.test_row_10b_unpark_while_open_else_backlog` |
| 11 | he changes his mind mid-plan | fixture `h01-retired-id-cited` (factory 2fcbb35): `FactoryFixtures.test_row_11_retired_id_cited` |
| 12 | he changes his mind mid-build | chaos `StopAfter.test_stop_after_checkpoint` |
| 13 | he abandons a program | chaos `Abandon.test_abandon` (kit `test_chain.Abandon` too) |
| 14 | budget overrun at handoff | fixture `d03`/`d04` (factory, U21): `FactoryFixtures.test_row_14_over_budget` |
| 15 | he insists on a DROP | fixtures `h02-he-overrules-a-drop`, `h03-agent-overrules-a-drop` (factory 2fcbb35): `FactoryFixtures.test_row_15_he_overrules_a_drop` |
| 16 | the challenger finds nothing | no script ("—"); fixture `e16-no-call-outs` named in `FactoryFixtures.test_row_16_nothing_to_call_out` |
| 17 | LATER hidden in a CORE slice | fixture `d02` (factory, U21): `FactoryFixtures.test_row_17_later_in_core_slice` |
| 18 | core sentence not true at the last CORE stop | chaos `CoreThenLater.test_core_not_proven_blocks_later` |
| 19 | LATER briefs would be stale | chaos `CoreThenLater.test_later_briefs_written_after_core` (F1); its loop: `CoreThenLater.test_a_later_hand_off_that_writes_nothing_waits_after_its_restarts` |
| 20 | an audit finds a design-level problem | chaos `Handoffs.test_x1_design_finding_goes_to_planning_as_a_row`; fixture `g05` |
| 21 | a plan's area is not fit to build on | chaos `Handoffs.test_x2_scoped_audit_stops_after_judgement` (F3); factory fixture: not testable here (no `audit-first` fixture in the factory yet) |
| 22 | a hand-off row is lost or bounces | `Handoffs.test_handoff_row_bounce`: not testable here, U33 (`ship backlog`) is not built; it runs once `ship.backlog` exists |
| 23 | an audit and a plan on one area | chaos `Handoffs.test_notice_overlap_is_reported` (F4) |
| 24 | a removal breaks a lookup by name | not testable here: U29 (`remove` kind) and U27 (`callers.py` fixture) are not in the kit; the factory's `g13`, `g21`, `g33`, `g36` fixtures check the callers fact |
| 25 | a refactor changes behaviour | not testable here: U29 (`pin`/`refactor` kinds) is not in the kit |
| 26 | a one-way door nobody approved | fixture `g04` (factory, U28): `FactoryFixtures.test_row_26_unapproved_one_way_door` |
| 27 | a brief is wrong about the code | chaos `Briefs.test_wrong_brief_parks_and_chain_issue_routes` |
| 28 | the target moved since planning | chaos `Target.test_target_moved_before_arm` |
| 29 | the target moved during the build | chaos `Target.test_target_moved_during_build` |
| 30 | merge conflict | kit `test_merge.Moved.test_a_conflicting_target_writes_the_one_slice_fix_program`: `Named.test_row_30` |
| 31 | every slice of a checkpoint parked | chaos `Empty.test_all_parked_checkpoint_is_empty` |
| 32 | round 2 still blocked | chaos `Rounds.test_round_two_blocked_waits` |
| 33 | CI cannot go green | chaos `Ci.test_ci_stuck_waits_no_local_merge` |
| 34 | a flaky test | kit `test_k4a.CiAgreement.test_flaky_follows_ci_...` and `FlakyInChecks`: `Named.test_row_34` |
| 35 | a reader never finishes | kit `test_review.NotRead`, `test_k4.AuditStages`: `Named.test_row_35` |
| 36 | two conveyors on one program | kit `test_chain.Waits.test_a_second_conveyor_...`: `Named.test_row_36` |
| 37 | disk nearly full | kit `test_arm.Preflight.test_low_disk_warns_and_still_arms`: `Named.test_row_37` |
| 38 | `gh` on the old account | kit `test_arm.Preflight.test_wrong_gh_account_fails_and_the_owner_passes`: `Named.test_row_38` |
| 39 | a live build branch deleted | chaos `BranchGone.test_build_branch_deleted` |
| 40 | the docs step fails | not testable here: U36 (`ship.docs`) is not built; the conveyor's skip record is in `test_chain.EndToEnd` |
| 41 | an undeclared route | not testable here: U25 (contract check in `slice_checks`) is not in the kit |
| 42 | a stale contract file | not testable here: CI's drift job (U23) lives in qmx-ci, not the kit |
| 43 | Fable cannot be started | kit `test_launch.Results.test_fable_role_that_fell_back_says_so`; chaos `Fable.test_fable_falls_back_and_its_result_says_so`, `Fable.test_fable_falls_back_and_says_so` and `FallbackReport.test_the_run_report_lists_every_fable_fallback` (F5) |
| 44 | two programs' records collide | kit `test_records.Lock`, `test_dl22.RecordsRace`: `Named.test_row_44` |
| 45 | the main checkout is edited | kit `test_arm.MainCheck.test_tracker_and_claude_edits_...`: `Named.test_row_45` |
| 46 | two programs want one file | kit `test_claims.Build.test_only_the_slice_naming_a_claimed_file_...`: `Named.test_row_46` |
| 47 | two checkpoints finish at once | kit `test_claims.Merges.test_two_merges_take_turns_...`: `Named.test_row_47` |
| 48 | two programs break each other quietly | not testable here: needs a fake deep run red only for a commit holding both programs (fake `gh` cannot script that yet); the merge's own deep run is in `test_merge.Moved` |
| 49 | one program keeps merging first | kit `test_locks.MergeQueue.test_three_waiters_...`: `Named.test_row_49` |
| 50 | a stale claim | kit `test_claims.Build.test_the_claims_of_a_deleted_program_are_swept`: `Named.test_row_50` |
| 51 | he is away at the intent check | chaos `Audit.test_away_at_intent_check` (also X3; F2) and `Audit.test_intent_answered_then_quality_and_judgement` |
| 52 | intent changed after quality | fixture `g07` (factory, U28): `FactoryFixtures.test_row_52_intent_changed_after_quality` |
| 53 | the sources contradict | fixture `g08` (factory, U28): `FactoryFixtures.test_row_53_leave_it_as_it_works` |
| 54 | a Fable removal he uses | fixture `g14` (factory, U26): `FactoryFixtures.test_row_54_fable_decides_visible_removal`; drill D8 |
| 55 | a restructure with no measure | fixture `c07`/`g06` (factory, U20): `FactoryFixtures.test_row_55_core_restructure_no_measure` |
| 56 | two Fable seats at once | kit `test_locks.FableSeat.test_two_fable_workers_never_overlap`; chaos `Fable.test_one_fable_at_a_time_waits_for_the_seat` and, past `fable_wait_s`, `Fable.test_fable_seat_taken_too_long_falls_back_to_opus` (G1) |
| 57 | a loop reaches its round limit | `Loops` (one test per loop of 3.9, below) |
| 58 | the index and the skills disagree | fixture `check_index` (factory, U40): `FactoryFixtures.test_row_58_index_drift` |

Findings of the first run, all fixed under D-L26 (the test that proves each fix):

- F1 (row 19) a later hand-off's slices never reached state.json: `CoreThenLater.test_later_briefs_written_after_core`.
- F2 (row 51, X3) the judge started while his intent question was open: `Audit.test_away_at_intent_check`.
- F3 (row 21, X2) no scoped audit: `Handoffs.test_x2_scoped_audit_stops_after_judgement`.
- F4 (row 23) no overlap report on a notice: `Handoffs.test_notice_overlap_is_reported`.
- F5 (row 43) a Fable fallback was only in result.json: `Fable.test_fable_falls_back_and_says_so`,
  `FallbackReport.test_the_run_report_lists_every_fable_fallback`.
- F6 (X9) an audit's facts were never rerun after a merge into its area: `Handoffs.test_x9_stale_findings_rerun_at_the_new_tip`.
- F7 (X1) a hand-off with no slices restarted forever: `Handoffs.test_x1_all_rows_design_hand_off_ends`.
- F8 (row 57) a merge refused because the target moved was retried forever: `Loops.test_merge_when_the_target_moved`.
- F9 (row 2) a stale `index.lock` made `land` fail forever: `LandKilled.test_land_killed_mid_git_is_recovered`,
  `LandKilled.test_a_land_that_keeps_crashing_waits_after_its_restarts`, `LandLock.test_a_lock_with_git_running_in_the_copy_stays`.
- G1 (row 56) no Opus stand-in for a long Fable wait: `Fable.test_fable_seat_taken_too_long_falls_back_to_opus`.

D-L26's general rule, every worker restart loop counts toward `max_restarts` and then WAITS, one test per loop that
had no limit: plan review with no RESULT line (`Loops.test_plan_review_with_no_result_waits_after_its_restarts`),
the later hand-off (`CoreThenLater.test_a_later_hand_off_that_writes_nothing_waits_after_its_restarts`), the sweep
hand-off (`Handoffs.test_a_sweep_hand_off_that_writes_nothing_waits_after_its_restarts`), the audit hand-off (F7)
and `land` (F9).

Loops of 3.9 (row 57), each: exit, and what happens at the round count.

| Loop | Covered by |
|---|---|
| Questions to him (3 batches of 4) | fixture: factory `Resume.test_too_many_open_questions_ask_for_a_list`: `Loops.test_questions_to_him` |
| Self-annealing (5 rounds) | fixture `d08-anneal-round-limit`: `Loops.test_self_annealing` |
| He changes his mind (no limit) | fixture `v19-mind-change-after-stage5-global-numbering`: `Loops.test_he_changes_his_mind` |
| Plan review and planner (1 round trip) | chaos `Loops.test_second_fixes_result_waits` |
| A slice's fix round (1 fix round) | chaos `Loops.test_second_red_parks`; kit `test_dispatch_recover.FixRounds`, breaker in `test_foundation` |
| A worker dying (3 restarts) | chaos row 8 `Garbage.test_garbage_builder_parks_after_three`: `Loops.test_worker_dying` |
| Checkpoint fix batch (2 rounds) | chaos row 32: `Loops.test_checkpoint_fix_batch` |
| A reader that does not finish (1 restart) | kit row 35: `Loops.test_reader_not_finishing` |
| Waiting on CI (2 long waits) | chaos row 33: `Loops.test_waiting_on_ci` |
| Merge when the target moved (5 tries, D-L26) | chaos `Loops.test_merge_when_the_target_moved` (F8); one retry is kit `test_merge.Clean.test_the_merge_names_the_reviewed_head_and_a_moved_target_is_a_retry`, turn order `test_locks.MergeQueue` |
| Budget growth (his yes each time) | fixture row 14: `Loops.test_budget_growth` |
| CORE then LATER (the LATER budget) | chaos rows 18 and 19: `Loops.test_core_then_later` |
| Audit and plan (1 crossing) | not testable here: U33 (row 22) |
| Backlog (nothing leaves without his yes) | not testable here: U33 (`ship backlog`) and U34 (scripted intake) are not built |

Hand-offs between the branches (13.4).

| Id | Covered by |
|---|---|
| X1 audit hands a redesign to planning | chaos `Handoffs.test_x1_design_finding_goes_to_planning_as_a_row` (backlog filing is U33: the row stays in `notes/BACKLOG-ROWS.tsv` for the desk); all rows design: `Handoffs.test_x1_all_rows_design_hand_off_ends` (F7) |
| X2 planning asks for an audit first | chaos `Handoffs.test_x2_scoped_audit_stops_after_judgement` (F3) |
| X3 away at the intent check | chaos row 51 `Audit.test_away_at_intent_check` (F2) |
| X4 an audit sweep and a feature side by side | kit `test_claims.Build.test_disjoint_programs_build_and_land_side_by_side` and `Merges`: `Named.test_x4` |
| X5 a removal meets a new caller | not testable here: U29 (`remove` kind and its callers fact at dispatch) is not in the kit |
| X6 work bouncing between branches | not testable here: U33 (row 22) |
| X7 a LATER item comes back as an ask | not testable here: U33 and U34 |
| X8 a builder says the plan is wrong | chaos row 27 (`MAP.md` lists it); the fix slice citing the chain id is the verdict prompt's job (skills lane) |
| X9 an audit's findings go stale | chaos `Handoffs.test_x9_stale_findings_rerun_at_the_new_tip` (F6: the facts rerun at arm, as D-L26 decided) |
| X10 a fix program crosses nothing | chaos `CoreThenLater.test_core_not_proven_blocks_later` (its claims part; D-L22 wins over "never registers its own": the fix's claims never block its parent and its merge releases them) |
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

from ship import phase
from ship import state as st
from ship.layout import Program
from ship.proc import kill_tree, pid_alive
from ship.settings import load_settings
from ship.tests.chaos import ChaosCase, Stop, builder, verdict
from ship.tests.fixture import BRIEF, PY, RepoCase, sh, write

ONE_STOP = (Stop("A"),)


class Power(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"), ("a2", "A", "L1"), ("a3", "A", "L2"))
    pool = 2

    def test_battery_holds_then_resumes(self):
        """Row 1. Mains goes while two builders run: HOLD; their results are still routed; nothing new starts while
        held; when mains is back and the settle time has passed, the run finishes as an undisturbed one would.
        D-L25: HOLD stops every new start (one guard in the tick), so no verify_ready starts while held either."""
        self.base_rules[1] = builder(sleep=3)
        self._write_rules()
        proc = self.start()
        self.until(lambda: len(self.children("builder")) == 2, what="two builders running")
        self.mains(False)
        self.until(lambda: self.program.hold.exists(), what="HOLD")
        started = len(self.calls("builder:"))
        self.until(lambda: self.chain_log().count("WORKER builder") >= 2, what="both results routed")
        time.sleep(2)
        self.assertTrue(self.program.hold.exists())
        self.assertEqual(len(self.calls("builder:")), started, "no builder starts while held")
        self.assertNotIn("START verify_ready", self.chain_log().split("POWER")[-1])
        self.mains(True)
        self.assertEqual(proc.wait(timeout=600), 0, self.chain_log()[-3000:])
        self.assertFalse(self.program.hold.exists())
        self.assert_converged()


class DeadLaptop(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"), ("a2", "A", "L2"))

    def test_dead_laptop_resume_all(self):
        """Row 2. `a2`'s builder has pushed one commit and has one more it did not push when the laptop dies (the
        conveyor and every child killed at once); the logon task's `chain --resume-all` recovers and finishes.
        The design's `kill_after("build", 2)` is replaced by a marker the builder writes once its unpushed commit
        exists, so the kill lands exactly there."""
        marker = self.root / "a2-unpushed.txt"
        self.rule({"match": "builder: a2", "times": 1, "steps": [
            {"write": {"pkg/a2.py": "# part one\n"}}, {"commit": "a2: part one"}, {"push": True},
            {"write": {"pkg/a2.py": "# part two, never pushed\n"}}, {"commit": "a2: part two"},
            {"file": {str(marker): "x"}}, {"sleep": 600}], "reply": "READY {head}"})
        self.start()
        self.until(marker.exists, what="a2's unpushed commit")
        self.kill_children()
        self.until(lambda: not any(pid_alive(c["pid"]) for c in self.children()), what="every child dead")
        self.assertEqual(phase.phase_json(self.program)["status"], "running")
        self.assertEqual(self.ship("chain", "--resume-all", "--plans", str(self.plans)), 0, self.out)
        self.assertIn("STARTED program", self.out)
        self.until(lambda: phase.phase_json(self.program).get("status") == "done", timeout=600,
                   what="the resumed conveyor to finish")
        self.until(lambda: not self.program.chain_lock.exists(), what="the lock let go")
        patch = self.program.evidence("a2", 1) / "leftover.patch"
        self.assertIn("part two, never pushed", patch.read_text("utf-8"))
        a2 = self.state().slices["a2"]
        self.assertEqual((a2.restarts, a2.attempts), (1, 1))
        self.assert_converged()


class LandKilled(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"),)

    def test_land_killed_mid_git_is_recovered(self):
        """Row 2, the laptop dying while `land` runs git in its landing copy: git's `index.lock` stays behind in
        `<program>/tmp/landing`. F9 (D-L26, fixed): the next `land` removes it, because no git process works in the
        copy, and lands. Before the fix every later `land` exited 1 forever; that was also the occasional hang of
        `test_chain.EndToEnd.test_killed_after_each_activity_and_restarted_it_ends_the_same`."""
        from ship.worktree import checkout_copy

        copy = checkout_copy(self.repo, self.program.tmp / "landing", self.base, load_settings(self.program.dir))
        lock = Path(sh(copy, "git", "rev-parse", "--path-format=absolute", "--git-path", "index.lock"))
        write(lock, "")
        self.assertEqual(self.chain(), 0, self.out)
        self.assertIn("LAND NOTE removed a stale", self.chain_log())
        self.assertNotIn("SCRIPT land exit 1", self.chain_log())
        self.assert_converged()

    def test_a_land_that_keeps_crashing_waits_after_its_restarts(self):
        """F9's restart loop (D-L26: every restart loop counts toward `max_restarts`, then WAITS): a landing copy
        that cannot be made (here a file is in its place) crashes `land` every time; after three the build stops
        with one WAITS line and the conveyor exits 10."""
        write(self.program.tmp / "landing", "not a folder\n")
        self.assertEqual(self.chain(), 10, self.out)
        self.assertEqual(self.chain_log().count("LAND crashed"), 3, self.chain_log()[-2000:])
        self.assertTrue(any("land crashed 3 times in a row" in w for w in self.waits()), self.waits())
        self.assertEqual(self.state().merged, [])


class Network(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"), ("a2", "A", "L2"))

    def test_remote_down_is_not_a_failure(self):
        """Row 3. The remote goes away right after `a1`'s builder pushed, before its READY is routed, and comes back
        three ticks later: HOLD during the outage, nothing parked, no attempt counted, converged. D-L25: once the
        outage is seen HOLD starts nothing, so `verify_ready` does not run during it; its exit 3 on an unreachable
        remote is `test_run.Faults.test_verify_ready_on_an_unreachable_remote_exits_3_and_changes_nothing`."""
        marker = self.root / "a1-pushed.txt"
        self.rule({"match": "builder: a1", "times": 1, "steps": [
            {"write": {"pkg/a1.py": "def a1():\n    return 'a1'\n"}}, {"commit": "a1: work"}, {"push": True},
            {"file": {**{k: v for k, v in builder()["steps"][3]["file"].items()}, str(marker): "x"}},
            {"sleep": 2}], "reply": "READY {head}"})
        proc = self.start()
        self.until(marker.exists, what="a1 pushed")
        self.remote_down()
        self.until(self.program.hold.exists, what="HOLD")
        ticks = self.chain_log().count("POWER")
        self.until(lambda: self.chain_log().count("POWER") >= ticks + 3, what="three ticks held")
        state = self.state()
        self.assertFalse([s.id for s in state.slices.values() if s.status == st.Status.PARKED])
        self.assertEqual(max(s.attempts for s in state.slices.values()), 1)
        self.remote_up()
        self.assertEqual(proc.wait(timeout=600), 0, self.chain_log()[-3000:])
        self.assertFalse(self.program.hold.exists())
        self.assert_converged(restarts={"a1": 0})


class Limits(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"), ("a2", "A", "L2"))

    def test_usage_limit_sleeps(self):
        """Row 4. `a1`'s builder ends on a usage limit: no worker starts before the reset, nothing polls; after the
        clock passes it `a1` restarts and lands. D-L12: a limit is a restart, never an attempt and never a death."""
        self.clock("2026-11-14T01:00:00+00:00")
        self.script("builder: a1", kind="limit", times=1, reset="2026-11-14T02:00:00+00:00")
        proc = self.start()
        self.until(lambda: self.program.state.exists() and self.state().usage_reset_at, what="the reset time")
        self.until(lambda: self.state().slices["a2"].status == st.Status.LANDED, what="a2 lands meanwhile")
        time.sleep(2)
        self.assertEqual(len(self.calls("builder:", "a1")), 1, "nothing starts before the reset")
        self.assertIsNone(proc.poll())
        self.advance(3601)
        self.assertEqual(proc.wait(timeout=600), 0, self.chain_log()[-3000:])
        a1 = self.state().slices["a1"]
        self.assertEqual((a1.restarts, a1.attempts, a1.deaths), (1, 1, 0))
        self.assert_converged()


class Detach(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"),)

    def test_detached_conveyor_outlives_parent(self):
        """Row 5 (the app closes): `chain --detach` returns at once and its parent is gone; the conveyor runs on to
        the end on its own. Drill D3 does it with Claude Desktop."""
        self.assertEqual(self.ship("chain", "--program", str(self.program.dir), "--detach"), 0, self.out)
        pid = int(self.out.split("DETACHED pid ")[1].split()[0])
        self.addCleanup(lambda: pid_alive(pid) and kill_tree(pid))
        self.assertTrue(pid_alive(pid), "the conveyor outlives the command that started it")
        self.until(lambda: phase.phase_json(self.program).get("status") == "done", timeout=600, what="the run")
        self.until(lambda: not pid_alive(pid), what="the conveyor to exit")
        self.assert_converged()


class Hang(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"), ("a3", "A", "L2"))

    def test_hung_builder_restarted_alone(self):
        """Row 7. `a1`'s builder hangs (no push, no heartbeat): only its process tree is stopped and it is restarted;
        `a3`'s dispatch is untouched. `liveness_stale_s` is 4, not the design's 2: a healthy fake builder on
        Windows can take two seconds to push."""
        self.setting("liveness_stale_s = 4")
        self.script("builder: a1", kind="hang", times=1)
        self.assertEqual(self.chain(), 0, self.out)
        a3_calls = self.calls("builder:", "a3")
        self.assertEqual(len(a3_calls), 1)
        self.assertEqual(self.state().slices["a3"].restarts, 0)
        seats = [e for e in self.state().events if e.get("slice") == "a3" and e.get("to") == "held"]
        self.assertEqual(len(seats), 1, "a3 was seated once: its dispatch id never changed")
        self.assertEqual(len(self.calls("builder:", "a1")), 2)
        a1 = self.state().slices["a1"]
        self.assertEqual((a1.restarts, a1.attempts), (1, 1))
        self.assertIn("STALE a1", (self.program.notes_dir / "run.log").read_text("utf-8"))
        self.assert_converged()


class Garbage(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"), ("a2", "A", "L1"), ("a3", "A", "L2"), ("a4", "A", "L2"))

    def test_garbage_builder_parks_after_three(self):
        """Row 8. `a2`'s builder replies with no contract line three times: parked `manual` with one WAITS line
        holding its last output; the rest of A lands, is reviewed and merged without it. (Stop B of the design's
        default shape is left out: it adds a minute and nothing to the row.)"""
        self.script("builder: a2", kind="garbage", times=3)
        self.assertEqual(self.chain(), 0, self.out)
        a2 = self.state().slices["a2"]
        self.assertEqual(a2.status, st.Status.PARKED)
        self.assertIn("died 3 times", a2.reason)
        waits = self.waits()
        self.assertEqual(len(waits), 1, waits)
        self.assertIn("a2 parked", waits[0])
        self.assertIn("I looked at it", self.program.waits.read_text("utf-8"), "its last output is in the line")
        self.assertEqual(len(self.calls("builder:", "a2")), 3)
        self.assertTrue((self.program.stop_review("A") / "REVIEW.md").exists())
        self.assert_converged(target_has=["a1", "a3", "a4"], waits=1)


QUESTIONS = {"match": "plan-review:", "times": 1, "steps": [{"file": {
    "{program}/plan-review/REVIEW.md": "Two things only he can say.\n\nRESULT: QUESTIONS\nEND plan-review x\n",
    "{program}/plan-review/QUESTIONS.md": "- [ ] Should a1 return its name? (recommended: yes)\n"
                                          "- [ ] Is one stop enough? (recommended: yes)\n"}}],
    "reply": "DONE {program}/plan-review/QUESTIONS.md"}


class Gates(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"),)

    def away(self):
        self.rule(QUESTIONS)
        self.assertEqual(self.chain(), 10, self.out)

    def test_away_at_go(self):
        """Row 9. The plan review asks two questions: the conveyor exits 10, `WAITING.md` holds both, `ship phase`
        says go and waits on him, and nothing is armed."""
        self.away()
        self.assertEqual(self.program.waiting.read_text("utf-8").count("- [ ]"), 2)
        p = self.phase()
        self.assertEqual((p["next"], p["status"]), ("go", "waits-on-him"))
        self.assertFalse(self.program.state.exists())
        self.assertEqual(self.calls("builder:"), [])

    def test_answer_then_go(self):
        """Row 10a. Days later he answers both and says go (`ship gate go`, D-L22: gates only through `ship gate`):
        the conveyor runs to done."""
        self.away()
        write(self.program.waiting, self.program.waiting.read_text("utf-8").replace("- [ ]", "- [x]"))
        self.assertEqual(self.ship("gate", "go", "--program", str(self.program.dir), "--by", "him", "--source",
                                   "test"), 0, self.out)
        self.assertEqual(self.chain(), 0, self.out)
        self.assert_converged()


class StopAfter(ChaosCase):
    stops = (Stop("A"), Stop("B"))
    slices = (("a1", "A", "L1"), ("b1", "B", "L1"))

    def test_stop_after_checkpoint(self):
        """Row 12. `chain --stop-after A`: the conveyor stops once A is merged, never mid-slice; B may be built
        but is not landed; a later plain `chain` finishes B."""
        self.assertEqual(self.chain("--stop-after", "A"), 0, self.out)
        self.assertEqual(self.chain(), 0, self.out)
        self.assertEqual(self.state().merged, ["A"])
        self.assertNotEqual(self.state().slices["b1"].status, st.Status.LANDED)
        self.assertFalse([s for s in self.build_subjects() if s.startswith("b1: ")])
        p = self.phase()
        self.assertEqual((p["next"], p["status"]), ("build", "idle"))
        self.assertFalse((self.program.dir / "STOP-AFTER").exists())
        self.assertEqual(self.chain(), 0, self.out)
        self.assert_converged()


class Abandon(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"), ("a2", "A", "L2"))

    def test_abandon(self):
        """Row 13. Abandoned mid-build: the conveyor and its children are gone, the run is torn down, its claims
        released, `abandoned:` set, `ship phase` says done and abandoned, and `--resume-all` does not start it.
        The design's "each unlanded slice is a backlog row" is not testable here: U33 (`ship backlog`) is not
        built. The kit's own `test_chain.Abandon` covers the conveyor and phase part."""
        self.script("builder:", kind="hang")
        proc = self.start()
        self.until(lambda: len(self.children("builder")) == 2, what="two builders")
        children = self.children()
        self.assertEqual(self.ship("abandon", "--program", str(self.program.dir), "--why", "test"), 0, self.out)
        proc.wait(timeout=60)
        for child in children:
            self.until(lambda: not pid_alive(int(child["pid"])), timeout=30, what=f"{child['id']} to stop")
        p = self.phase()
        self.assertEqual((p["next"], p["status"]), ("done", "abandoned"))
        self.assertRegex(self.program.project_file.read_text("utf-8"), r"(?m)^abandoned: \d{4}-")
        self.assertEqual(self.end_state()["claims"], [])
        self.assertEqual(self.ship("chain", "--resume-all", "--plans", str(self.plans)), 0, self.out)
        self.assertNotIn("STARTED program", self.out)
        self.assertFalse(self.program.chain_lock.exists())
        self.assertEqual(self.orphans(), [])
        self.assertEqual(self.held_locks(), [])


def claim_rows(case: ChaosCase) -> list[list[str]]:
    path = case.plans / "_records" / "CLAIMS.tsv"
    return [x.split("\t") for x in path.read_text("utf-8").splitlines()[1:] if x.strip()] if path.exists() else []


class CoreThenLater(ChaosCase):
    stops = (Stop("A"), Stop("B"), Stop("C", "later", "deferred"))
    slices = (("a1", "A", "L1"), ("b1", "B", "L1"))

    def test_core_not_proven_blocks_later(self):
        """Row 18, and X10. The verdict at A says the core sentence is not true (BLOCKED, with a fix folder): the
        fix program builds, round 2 is CLEAN, A merges; no later-handoff worker starts before the core is merged.
        X10: the design says a fix program "never registers its own" claims; D-L22 wins: the fix program's claims
        never block its parent (`claims.family` through the `parent` link, `test_dl22.ClaimsOrder.test_c1_...`)
        and A's merge releases every claim of its fix program and only A's own files (b1's claim stays live).
        The later stop C then waits on him because its prompt is not there yet."""
        self.rule(verdict("BLOCKED", match="verdict: A", times=1, finding="the core sentence is not true at A",
                          fix_slices=("a1f",)))
        self.rule(verdict("CLEAN", round_=2, match="verdict: A", times=1))
        self.kill_after("merge", 1)
        self.assertEqual(self.chain(), 137, self.out)
        self.assertIn("MERGED", self.program.merge_note("A").read_text("utf-8"))
        rows = claim_rows(self)
        live = {(r[0], r[2]) for r in rows if len(r) < 5 or not r[4]}
        self.assertFalse([r for r in live if r[0] == "program-fix-A"], "X10: A's merge releases its fix's claims")
        self.assertIn(("program", "pkg/b1.py"), live, "X10: B's claim stays")
        self.assertNotIn(("program", "pkg/a1.py"), live, "A's claim is released")
        self.assertEqual(self.chain(), 10, self.out)
        self.assertEqual(self.state().merged, ["A", "B"])
        self.assertEqual(self.calls("later-handoff:"), [])
        self.assertTrue(any("later-handoff prompt" in w for w in self.waits()), self.waits())
        self.assertIn("pkg/a1f.py", self.target_files())
        self.assertTrue((self.program.stop_review("A") / "REVIEW-2.md").exists())

    def test_later_briefs_written_after_core(self):
        """Row 19. The later-handoff worker starts only after the core (A) merged and writes stop C's slice; F1
        (D-L26, fixed): `init_state` appends a deferred stop's new rows to state.json, the conveyor runs their brief
        facts at the target's tip (which holds A's merge), and C is built, reviewed and merged. Before the fix the
        rows never reached state.json and the conveyor ticked `build` forever. (Stop B is left out: the core is A
        alone.)"""
        self.make_program(stops=(Stop("A"), Stop("C", "later", "deferred")), slices=(("a1", "A", "L1"),))
        self.prompt("LATER-HANDOFF.md")
        self.rule({"match": "later-handoff:", "times": 1, "steps": [{"file": {
            "{program}/SLICES.md": "| id | name | stop | lane | depends on | files | size |\n"
                                   "|---|---|---|---|---|---|---|\n| a1 | Slice a1 | A | L1 | - | pkg/a1.py | S |\n"
                                   "| c1 | Slice c1 | C | L1 | - | pkg/c1.py | S |\n",
            "{program}/slices/c1/BRIEF.md": BRIEF}}], "reply": "DONE {program}/SLICES.md"})
        proc = self.start()
        self.until(lambda: self.calls("later-handoff:") or proc.poll() is not None, timeout=400, what="the hand-off")
        self.assertTrue(self.calls("later-handoff:"), f"exit {proc.poll()}: {self.waits()} {self.chain_log()[-3000:]}")
        first = self.calls("later-handoff:")[0]["at"]
        self.assertGreater(first, self.program.merge_note("A").stat().st_mtime, "LATER starts after the core merged")
        self.until(lambda: "c1" in self.state().slices, timeout=30, what="c1 in state.json")
        self.assertEqual(proc.wait(timeout=400), 0, self.chain_log()[-2000:])
        self.assertIn("pkg/c1.py", self.target_files())
        merged_a = self.program.merge_note("A").read_text("utf-8").split("MERGED ")[1].split()[0]
        facts = self.program.checks_root / "_facts" / merged_a[:8] / "summary.txt"
        self.assertTrue(facts.exists(), "c1's facts ran at the tip that holds A's merge")
        self.assertIn("c1", facts.read_text("utf-8"))
        self.assertEqual(self.state().merged, ["A", "C"])
        self.assert_converged(merged=["A", "C"], target_has=["a1"])

    def test_a_later_hand_off_that_writes_nothing_waits_after_its_restarts(self):
        """D-L26's general rule, the later-handoff loop: a worker that ends DONE but writes no slice for the
        deferred stop was started again every tick; now its runs count toward `max_restarts`, then WAITS."""
        self.make_program(stops=(Stop("A"), Stop("C", "later", "deferred")), slices=(("a1", "A", "L1"),))
        self.prompt("LATER-HANDOFF.md")
        self.assertEqual(self.chain(), 10, self.out)
        self.assertEqual(len(self.calls("later-handoff:")), 3)
        self.assertTrue(any("later-handoff-C worker was started 3 times" in w for w in self.waits()), self.waits())


class Briefs(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"), ("a2", "A", "L1"), ("a3", "A", "L2"))

    def test_wrong_brief_parks_and_chain_issue_routes(self):
        """Row 27 (and X8's first half). `a1`'s brief states a fact that is false at the tip: one grounding worker,
        then `a1` is parked `brief-mismatch` at dispatch with a WAITS line. `a3`'s builder says `BLOCKED chain`:
        parked, a line in `notes/CHAIN-ISSUES.md`, no WAITS line, and the review's `MAP.md` lists it."""
        write(self.program.brief("a1"), "# Brief\n\n```fact F1\n$ git grep -c \"def nothing_here\" -- pkg/app.py\n"
                                        "pkg/app.py:1\n```\n")
        self.script("builder: a3", reply="BLOCKED chain S1.a wrong")
        self.assertEqual(self.chain(), 0, self.out)
        state = self.state()
        self.assertEqual(state.slices["a1"].status, st.Status.PARKED)
        self.assertIn("brief-mismatch", state.slices["a1"].reason)
        self.assertEqual(state.slices["a3"].status, st.Status.PARKED)
        self.assertEqual(len(self.calls("grounding:")), 1)
        waits = self.waits()
        self.assertEqual(len([w for w in waits if "a1" in w]), 1, waits)
        self.assertFalse([w for w in waits if "a3" in w], waits)
        self.assertIn("a3 BLOCKED chain S1.a wrong", (self.program.notes_dir / "CHAIN-ISSUES.md").read_text("utf-8"))
        self.assertIn("a3 BLOCKED chain S1.a wrong", (self.program.stop_review("A") / "MAP.md").read_text("utf-8"))
        self.assert_converged(target_has=["a2"], waits=None)


class Target(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"), ("a2", "A", "L2"))

    def test_target_moved_before_arm(self):
        """Row 28. After planning, another merge on the target makes `a2`'s fact false: arm runs the facts at the
        target's tip and starts one grounding worker, for `a2` only."""
        write(self.program.brief("a2"), "# Brief\n\n```fact F1\n$ git grep -c \"return a + b\" -- pkg/app.py\n"
                                        "pkg/app.py:1\n```\n")
        self.prompt("GROUNDING.md", "Ground {SLICES} at {TIP} for {PROGRAM} with {SHIP}\n")
        target = self.target_commit({"pkg/app.py": "def add(a, b):\n    return b + a\n"})
        self.kill_after("arm", 1)  # the row is about arming; the build after it is every other scenario's
        self.assertEqual(self.chain(), 137, self.out)
        self.assertTrue((self.program.checks_root / "_facts" / target[:8] / "summary.txt").exists())
        self.assertEqual(len(self.calls("grounding:")), 1)
        prompt = next(self.program.workers.glob("chain-grounding-*/prompt.md")).read_text("utf-8")
        self.assertIn(f"Ground a2 at {target}", prompt)

    def test_target_moved_during_build(self):
        """Row 29. A's review is CLEAN, then another program merges unrelated files into the target: the merge takes
        the target into the build branch, a second deep run is started for that commit, then the PR merges."""
        self.kill_after("checkpoint", 1)
        self.assertEqual(self.chain(), 137, self.out)
        theirs = self.target_commit({"docs/other.md": "theirs\n"})
        self.assertEqual(self.chain_until_done(), [0], self.out)
        self.assertIn("merge: main into build/t for stop A", self.build_subjects())
        sh(self.repo, "git", "merge-base", "--is-ancestor", theirs, "origin/build/t")
        common = sh(self.repo, "git", "rev-parse", "--git-common-dir")
        runs = json.loads(((Path(common) if Path(common).is_absolute() else self.repo / common)
                           / "fake-gh-runs.json").read_text("utf-8"))["runs"]
        deep = [r for r in runs if r["event"] == "workflow_dispatch" and "deep" in r["displayTitle"]]
        self.assertGreaterEqual(len(deep), 2, "a second deep run for the merge commit")
        self.assert_converged()


class Empty(ChaosCase):
    stops = (Stop("A"), Stop("B"))
    slices = (("a1", "A", "L1"), ("a2", "A", "L1"), ("a3", "A", "L2"), ("a4", "A", "L2"), ("b1", "B", "L1"))

    def test_all_parked_checkpoint_is_empty(self):
        """Row 31. Every builder of A says `BLOCKED brief-mismatch F1`: A is recorded EMPTY and merged with its
        parked list in WAITS; B is not held hostage and builds, is reviewed and merges."""
        for sid in ("a1", "a2", "a3", "a4"):
            self.script(f"builder: {sid}", reply="BLOCKED brief-mismatch F1")
        self.assertEqual(self.chain(), 0, self.out)
        self.assertTrue(self.program.merge_note("A").read_text("utf-8").startswith("EMPTY"))
        self.assertEqual(self.state().merged, ["A", "B"])
        waits = self.waits()
        for sid in ("a1", "a2", "a3", "a4"):
            self.assertTrue([w for w in waits if sid in w], (sid, waits))
        self.assert_converged(target_has=["b1"], waits=None)


class Rounds(ChaosCase):
    stops = (Stop("A"), Stop("B"))
    slices = (("a1", "A", "L1"), ("b1", "B", "L1"))

    def test_round_two_blocked_waits(self):
        """Row 32. BLOCKED in round 1 and again in round 2: no third round; the conveyor exits 10 with each open
        finding in WAITS; nothing merged; B is built ahead but not landed."""
        self.rule(verdict("BLOCKED", match="verdict: A", times=1, finding="a1 is wrong", fix_slices=("a1f",)))
        self.rule(verdict("BLOCKED", round_=2, match="verdict: A", times=1, finding="a1 is still wrong"))
        self.assertEqual(self.chain(), 10, self.out)
        self.assertEqual(self.state().merged, [])
        self.assertTrue(any("a1 is still wrong" in w for w in self.waits()), self.waits())
        self.assertEqual(len(self.calls("verdict:")), 2, "no third round")
        self.assertNotEqual(self.state().slices["b1"].status, st.Status.LANDED)
        self.assertFalse([s for s in self.build_subjects() if s.startswith("b1: ")])
        p = self.phase()
        self.assertEqual((p["next"], p["status"]), ("waits", "waits-on-him"))


class Ci(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"),)

    def test_ci_stuck_waits_no_local_merge(self):
        """Row 33 (the K3 note: a deep run that stays queued twice). The deep run never leaves the queue: after two
        waits the conveyor exits 10 with the run's URL in WAITS; no verdict worker starts; nothing merges and no
        local run stands in."""
        self.deep("queued")
        self.setting("ci_wait_timeout_s = 1")
        self.assertEqual(self.chain(), 10, self.out)
        waits = self.waits()
        self.assertTrue(any("did not finish twice (https://github.test/runs/" in w and "no local-only merge" in w
                            for w in waits), waits)
        self.assertEqual(self.calls("verdict:"), [])
        self.assertEqual(self.state().merged, [])
        self.assertFalse(list(self.program.checks_root.glob("_review/*-nightly.log")), "no local deep run")
        self.assertNotIn("pkg/a1.py", self.target_files())


class BranchGone(ChaosCase):
    stops = ONE_STOP
    slices = (("a1", "A", "L1"),)

    def test_build_branch_deleted(self):
        """Row 39. Someone deletes the live build branch mid-build: one WAITS line saying it is gone and exit 10,
        never a loop on `land`."""
        self.base_rules[1] = builder(sleep=2)
        self._write_rules()
        proc = self.start()
        self.until(lambda: len(self.children("builder")) == 1, what="a builder")
        sh(self.repo, "git", "push", "-q", "origin", "--delete", "build/t")
        self.assertEqual(proc.wait(timeout=300), 10, self.chain_log()[-3000:])
        waits = self.waits()
        self.assertEqual([w for w in waits if "gone" in w], ["- [ ] build branch `build/t` is gone from the remote"])
        self.assertLessEqual(self.chain_log().count("START land"), 1)

# ---- the audit branch and the hand-offs ------------------------------------------------------------------

INTENT = ("# Intent\n\n- **N1** the order book keeps every order it was given. Source: t:3\n"
          "- **N2** a limit is checked before an order is sent. Source: t:4\n\n## Ambiguities\n\n"
          "- [ ] U1 Does N2 mean the old daily limit or the new one? (recommended: the old one)\n")
READER_PART = {"match": "audit-reader:", "steps": [{"file": {"{program}/readers/{part}.md": "Read it.\nDONE\n"}}],
               "reply": "DONE {program}/readers/{part}.md"}
SWEEP_ROWS = "| id | name | stop | lane | depends on | files | size |\n|---|---|---|---|---|---|---|\n"


class AuditCase(ChaosCase):
    """An audit program (kind audit, area `pkg`) with a census at the base, one part, and the audit prompts and
    scripts in the temp factory home; `at(stage)` puts it at a stage, as `phase.json` would after a kill, with the
    gates of his that a program at that stage has (logged as `ship gate` would)."""

    stops = ONE_STOP
    slices = (("a1", "A", "L1"),)

    def setUp(self):
        super().setUp()
        self.make_program(kind="audit")
        for name in ("AUDIT-INTENT.md", "AUDIT-READER.md", "AUDIT-JUDGE.md", "AUDIT-SCREEN.md", "SWEEP-HANDOFF.md"):
            self.prompt(name)
        self.prompt("AUDIT-HANDOFF.md", "Hand {PROGRAM} on from {CHECKOUT} with {SHIP}\n")
        scripts = self.factory / "skills" / "audit-area" / "scripts"
        write(scripts / "collect_findings.py", "print('collected')\n")
        write(scripts / "apply_screen.py", "print('applied')\n")
        write(self.program.dir / "CENSUS.md", f"# Census\n\nTip: {self.base}\n\n## Parts\n\n- **core** `pkg`\n")
        write(self.program.dir / "FINDINGS.tsv", "id\tpart\tverdict\twhat\nF1\tcore\timprove\tthe limit check\n")
        self.base_rules = [{"match": "audit-intent:", "steps": [{"file": {"{program}/INTENT.md": INTENT}}],
                            "reply": "DONE {program}/INTENT.md"}, READER_PART,
                           {"match": "audit-judge:", "reply": "DONE judged"},
                           {"match": "audit-screen:", "reply": "DONE screened"}, PLAN_CLEAN_AUDIT]
        self._write_rules()

    def gate(self, name: str, advance: bool = False) -> None:
        from ship import program as prog

        prog.set_gate(self.program, name, by="him", source="t:9", advance=advance, at="2026-11-14")

    def at(self, stage: str) -> None:
        order = ("census", "intent", "intent-check", "quality", "judgement", "verdicts", "audit-handoff")
        if order.index(stage) >= order.index("quality"):
            self.gate("intent")
        if stage == "audit-handoff":
            self.gate("verdicts", advance=True)
        phase.set_phase(self.program, stage, "running", "test")


PLAN_CLEAN_AUDIT = {"match": "plan-review:", "steps": [{"file": {
    "{program}/plan-review/REVIEW.md": "Fine.\n\nRESULT: CLEAN\nEND plan-review x\n"}}],
    "reply": "DONE {program}/plan-review/REVIEW.md"}


class Audit(AuditCase):
    def test_away_at_intent_check(self):
        """Row 51 and X3. The intent worker leaves an ambiguity on N2 while he is away. F2 (D-L26, fixed; the
        design's "quality starts on the lines with no ambiguity" is replaced by D-L26): the conveyor waits on
        `gates.intent` before quality, with a WAITS line naming his question; no reader, judge or screen starts.
        Before the fix it went on to quality and judgement while the question was open."""
        self.at("intent")
        self.assertEqual(self.chain(), 10, self.out)
        self.assertIn("- [ ] U1 Does N2 mean", self.program.waiting.read_text("utf-8"))
        self.assertTrue(any("waits on his intent check" in w and "U1 Does N2 mean" in w for w in self.waits()),
                        self.waits())
        for role in ("audit-reader:", "audit-judge:", "audit-screen:"):
            self.assertEqual(self.calls(role), [], role)
        self.assertEqual(phase.phase_json(self.program)["phase"], "intent-check")

    def test_intent_answered_then_quality_and_judgement(self):
        """Row 51, then his answer: once `ship gate intent` is set, quality (the readers), the judge and the
        screen run, and the audit waits on his verdicts gate."""
        self.at("intent")
        self.assertEqual(self.chain(), 10, self.out)
        write(self.program.waiting, self.program.waiting.read_text("utf-8").replace("- [ ]", "- [x]"))
        write(self.program.waits, self.program.waits.read_text("utf-8").replace("- [ ]", "- [x]"))
        self.assertEqual(self.ship("gate", "intent", "--program", str(self.program.dir), "--by", "him", "--source",
                                   "test"), 0, self.out)
        self.assertEqual(self.chain(), 10, self.out)
        for role in ("audit-reader:", "audit-judge:", "audit-screen:"):
            self.assertEqual(len(self.calls(role)), 1, role)
        self.assertEqual(phase.phase_json(self.program)["phase"], "verdicts")


class Handoffs(AuditCase):
    def test_x1_design_finding_goes_to_planning_as_a_row(self):
        """Row 20 and X1. At the audit's hand-off the worker routes a mechanical row into a sweep slice and a design
        row into `notes/BACKLOG-ROWS.tsv` (source handoff, door design, where: the audit folder). The audit does not
        plan it: no feature program is started, and the next step is the sweep's own plan review (his go
        follows). The worker was given the audit checkout, which is dropped after. Filing the row in the backlog
        with `hops: 0` is U33's (`ship backlog`), not built: the desk files `BACKLOG-ROWS.tsv`. The check side
        (`check_chain --kind audit --stage handoff` fails with no hand-off row) is
        `FactoryFixtures.test_row_20_design_finding_needs_handoff`."""
        self.at("audit-handoff")
        self.rule({"match": "sweep-handoff:", "times": 1, "steps": [{"file": {
            "{program}/SLICES.md": SWEEP_ROWS + "| p-1 | Drop the dead helper | A | L1 | - | pkg/app.py | S |\n",
            "{program}/slices/p-1/BRIEF.md": BRIEF,
            "{program}/AUDIT.md": "# Audit\n\n## Hand-offs\n\n- **F3** design: the order book needs a new shape\n",
            "{program}/notes/BACKLOG-ROWS.tsv": "source\tdoor\twhat\twhere\n"
                                                "handoff\tdesign\tthe order book needs a new shape\t{program}\n"}}],
            "reply": "DONE {program}/SLICES.md"})
        self.rule(QUESTIONS)
        self.assertEqual(self.chain(), 10, self.out)
        self.assertEqual(len(self.calls("sweep-handoff:")), 1)
        prompt = next(self.program.workers.glob("chain-audit-audit-handoff-*/prompt.md")).read_text("utf-8")
        checkout = self.wt_root / "audit-program"
        self.assertIn(f"from {checkout}", prompt)
        self.assertFalse(checkout.exists(), "the audit checkout is dropped after the hand-off")
        self.assertEqual(len(self.calls("plan-review:")), 1, "the sweep goes through its own plan review")
        self.assertEqual([p.parent.name for p in self.plans.glob("*/PROGRAM.yaml")], ["program"],
                         "no feature program was started")
        rows = (self.program.notes_dir / "BACKLOG-ROWS.tsv").read_text("utf-8").splitlines()
        self.assertEqual(rows[1].split("\t")[:2], ["handoff", "design"])
        self.assertEqual(Path(rows[1].split("\t")[3]), self.program.dir)
        self.assertNotIn("order book", self.program.slices_md.read_text("utf-8"))
        p = self.phase()
        self.assertEqual((p["next"], p["status"]), ("go", "waits-on-him"))

    def test_x1_all_rows_design_hand_off_ends(self):
        """X1 when every approved row is a design (or later) row. F7 (D-L26, fixed): the hand-off writes no
        `SLICES.md`, so the program ends done with its hand-off rows recorded in `notes/HANDOFF.md`. Before the fix
        the conveyor started the hand-off worker again on every tick."""
        self.at("audit-handoff")
        self.rule({"match": "sweep-handoff:", "steps": [{"file": {
            "{program}/notes/BACKLOG-ROWS.tsv": "source\tdoor\twhat\twhere\n"
                                                "handoff\tdesign\tthe order book needs a new shape\t{program}\n"}}],
            "reply": "DONE {program}/notes/BACKLOG-ROWS.tsv"})
        self.assertEqual(self.chain(), 0, self.out)
        self.assertEqual(len(self.calls("sweep-handoff:")), 1, "the hand-off ran once")
        self.assertIn("the order book needs a new shape", (self.program.notes_dir / "HANDOFF.md").read_text("utf-8"))
        self.assertFalse(self.program.slices_md.exists())
        p = self.phase()
        self.assertEqual((p["next"], p["status"]), ("done", "done"))
        self.assertEqual(self.waits(), [])

    def test_a_sweep_hand_off_that_writes_nothing_waits_after_its_restarts(self):
        """D-L26's general rule, the sweep-handoff loop: a sweep program whose hand-off worker ends DONE with no
        `SLICES.md` was started again every tick; now its runs count toward `max_restarts`, then WAITS."""
        write(self.program.project_file, "project: qmx\nprogram: program\nkind: sweep\nparent: null\n"
                                         f"build_branch: build/t\nparent_tip: {self.base}\ngates:\n  go: null\n"
                                         "stop_points:\n  - id: A\n    tier: core\n    handoff: ready\n"
                                         "abandoned: null\n")
        from ship.tests.fixture import sign_gates

        sign_gates(self.program)
        self.assertEqual(self.chain(), 10, self.out)
        self.assertEqual(len(self.calls("sweep-handoff:")), 3)
        self.assertTrue(any("sweep-handoff worker was started 3 times" in w for w in self.waits()), self.waits())

    def test_x2_scoped_audit_stops_after_judgement(self):
        """Row 21 and X2. A scoped audit (its `parent` is the feature that asked for it) runs to judgement and
        stops. F3 (D-L26, fixed): no verdicts gate and no hand-off of its own; its findings go into the parent's
        `notes/AUDIT-<audit>.md` for the plan's ground, and the audit is done. The feature's `--stage anneal`
        check citing the audit's files is the factory's (U28), with no fixture there yet."""
        parent = Program(self.plans / "feature-x")
        write(parent.project_file, "project: qmx\nprogram: feature-x\nkind: feature\ngates:\n  go: null\n"
                                   "stop_points: []\n")
        write(self.program.project_file, self.program.project_file.read_text("utf-8").replace(
            "parent: null", "parent: feature-x"))
        from ship.tests.fixture import sign_gates

        sign_gates(self.program)
        self.at("judgement")
        self.assertEqual(self.chain(), 0, self.out)
        self.assertEqual(len(self.calls("audit-judge:")), 1)
        self.assertEqual(self.calls("sweep-handoff:"), [])
        note = (parent.notes_dir / "AUDIT-program.md").read_text("utf-8")
        self.assertIn("F1\tcore\timprove\tthe limit check", note)
        self.assertEqual(self.waits(), [])
        p = self.phase()
        self.assertEqual((p["next"], p["status"]), ("done", "done"))

    def test_x9_stale_findings_rerun_at_the_new_tip(self):
        """X9. A feature merged into the audit's area after the census. F6 (D-L26, fixed as decided: the
        hand-off's briefs go through `ship facts --tip` at arm, as a feature's do): arm runs the sweep brief's
        facts at the target's new tip, the fact the merge made false fails there, and one grounding worker
        starts for that slice. (The design's "findings go back to an audit-reader" is replaced by D-L26.)"""
        self.at("audit-handoff")
        new_tip = self.target_commit({"pkg/app.py": "def add(a, b):\n    return int(a) + int(b)\n"},
                                     "feature: merged into pkg")
        brief = "# Brief\n\n```fact F1\n$ git grep -c \"return a + b\" -- pkg/app.py\npkg/app.py:1\n```\n"
        self.rule({"match": "sweep-handoff:", "times": 1, "steps": [{"file": {
            "{program}/SLICES.md": SWEEP_ROWS + "| p-1 | One | A | L1 | - | pkg/app.py | S |\n",
            "{program}/slices/p-1/BRIEF.md": brief}}], "reply": "DONE {program}/SLICES.md"})
        self.kill_after("arm", 1)
        self.assertEqual(self.chain(), 137, self.out)
        summary = self.program.checks_root / "_facts" / new_tip[:8] / "summary.txt"
        self.assertIn("FAIL p-1", summary.read_text("utf-8"))
        self.assertEqual(len(self.calls("grounding:")), 1)

    @unittest.skipUnless(__import__("importlib.util").util.find_spec("ship.backlog"), "U33 (ship backlog) is not built")
    def test_handoff_row_bounce(self):
        """Row 22 (and X6). Not testable here until U33: a hand-off row crossing back gets `hops: 1`; a third
        crossing is refused with "second crossing: ask him" and the row is listed by `backlog list --needs-him`."""
        self.assertEqual(self.ship("backlog", "add", "--plans", str(self.plans), "--source", "handoff", "--door",
                                   "design", "--what", "B-1"), 0, self.out)

    def test_notice_overlap_is_reported(self):
        """Row 23. An audit and a plan on the same area: both go on (notices never block), and F4 (D-L26, fixed):
        the second `ship claims notice` prints `OVERLAP notice <the other program>` so the desk can tell him."""
        feature = Program(self.plans / "feature-x")
        write(feature.project_file, "project: qmx\nprogram: feature-x\nkind: feature\narea: [pkg]\ngates:\n"
                                    "  go: null\nstop_points: []\n")
        self.assertEqual(self.ship("claims", "notice", "--program", str(self.program.dir)), 0, self.out)
        self.assertNotIn("OVERLAP", self.out)
        self.assertEqual(self.ship("claims", "notice", "--program", str(feature.dir)), 0, self.out)
        self.assertIn("OVERLAP notice program", self.out)
        self.assertIn("NOTICE feature-x pkg", self.out)


class Fable(AuditCase):
    def test_fable_falls_back_and_its_result_says_so(self):
        """Row 43, the kit part (U06): the audit judge is a Fable role; the run comes back on Opus, so its
        `result.json` says `FALLBACK audit-judge claude-opus-5-5`."""
        self.at("judgement")
        self.rule({"match": "audit-judge:", "model": "claude-opus-5-5", "reply": "DONE judged"})
        self.assertEqual(self.chain(), 10, self.out)
        result = json.loads(next(self.program.workers.glob("chain-audit-judgement-*/result.json")).read_text("utf-8"))
        self.assertIn("FALLBACK audit-judge claude-opus-5-5", json.dumps(result))

    def test_fable_falls_back_and_says_so(self):
        """Row 43. F5 (D-L26, fixed): the fallback is said, not only recorded: `notes/FALLBACKS.md` gets a line,
        the conveyor copies it into chain.log, and the run report lists it (`FallbackReport` below)."""
        self.at("judgement")
        self.rule({"match": "audit-judge:", "model": "claude-opus-5-5", "reply": "DONE judged"})
        self.assertEqual(self.chain(), 10, self.out)
        self.assertIn("FALLBACK audit-judge claude-opus-5-5", self.chain_log())
        self.assertIn("FALLBACK audit-judge", (self.program.notes_dir / "FALLBACKS.md").read_text("utf-8"))

    def hold_seat(self):
        from ship.proc import created

        holder = subprocess.Popen([PY, "-c", "import time; time.sleep(120)"])
        self.addCleanup(lambda: holder.poll() is None and holder.kill())
        write(self.factory / "run" / "fable.lock",
              json.dumps({"pid": holder.pid, "created": created(holder.pid), "program": "other"}))
        return holder

    def test_one_fable_at_a_time_waits_for_the_seat(self):
        """Row 56. Another program's Fable worker holds the seat: the judge does not start (no attempt is used);
        once the seat is free it starts, on Fable. Within `fable_wait_s` nothing stands in."""
        holder = self.hold_seat()
        self.at("judgement")
        proc = self.start()
        self.until(lambda: self.chain_log().count("\n") >= 1, what="the conveyor's first tick")
        time.sleep(3)
        self.assertEqual(self.calls("audit-judge:"), [], "the judge waits for the Fable seat")
        holder.kill()
        holder.wait()
        self.assertEqual(proc.wait(timeout=300), 10, self.chain_log()[-2000:])
        judge = self.calls("audit-judge:")
        self.assertEqual(len(judge), 1)
        self.assertEqual(judge[0]["argv"][judge[0]["argv"].index("--model") + 1], "fable")

    def test_fable_seat_taken_too_long_falls_back_to_opus(self):
        """G1 (D-L26): a Fable role that has waited longer than `fable_wait_s` for the seat runs on its fallback
        (Opus), and the fallback is logged (chain.log and `notes/FALLBACKS.md`)."""
        self.hold_seat()
        self.setting("fable_wait_s = 2")
        self.at("judgement")
        self.assertEqual(self.chain(), 10, self.out)
        judge = self.calls("audit-judge:")
        self.assertEqual(len(judge), 1)
        argv = judge[0]["argv"]
        self.assertEqual(argv[argv.index("--model") + 1], "claude-opus-5-5")
        self.assertNotIn("--fallback-model", argv)
        self.assertIn("FALLBACK audit-judge claude-opus-5-5 (the Fable seat was taken for", self.chain_log())


class LandLock(RepoCase):
    def test_a_lock_with_git_running_in_the_copy_stays(self):
        """F9 (D-L26): the landing copy's `index.lock` is removed only when no git process works there."""
        from ship.land import clear_stale_index_lock
        from ship.worktree import checkout_copy

        settings = load_settings(self.program.dir)
        copy = checkout_copy(self.repo, self.program.tmp / "landing", self.tip(), settings)
        lock = Path(sh(copy, "git", "rev-parse", "--path-format=absolute", "--git-path", "index.lock"))
        write(lock, "")
        busy = subprocess.Popen(["git", "-C", str(copy), "hash-object", "--stdin"], stdin=subprocess.PIPE,
                                stdout=subprocess.DEVNULL)
        self.addCleanup(lambda: busy.poll() is None and busy.kill())
        self.assertIn("stays: git runs in the landing copy", clear_stale_index_lock(self.repo, copy, 60))
        self.assertTrue(lock.exists())
        busy.communicate(b"x")
        self.assertIn("removed a stale", clear_stale_index_lock(self.repo, copy, 60))
        self.assertFalse(lock.exists())
        self.assertEqual(clear_stale_index_lock(self.repo, copy, 60), "", "no lock: nothing to do")


class FallbackReport(RepoCase):
    def test_the_run_report_lists_every_fable_fallback(self):
        """F5 (D-L26): the run report has a "Fable fallbacks" section from `notes/FALLBACKS.md`."""
        from ship.launch import note_fallback
        from ship.run_report import build

        self.assertIn("## Fable fallbacks (0)", build(self.program, load_settings(self.program.dir))[1])
        note_fallback(self.program, "FALLBACK fault-reader claude-opus-5-5 (reader: program A faults)")
        text = build(self.program, load_settings(self.program.dir))[1]
        self.assertIn("## Fable fallbacks (1)", text)
        self.assertIn("FALLBACK fault-reader claude-opus-5-5", text)


# ---- row 57: every loop of 3.9 stops where it says -------------------------------------------------------


def covered(dotted: str) -> None:
    """The kit test `module.Class.test` exists (so the coverage table cannot point at nothing)."""
    import importlib

    module, cls, name = dotted.rsplit(".", 2)
    found = getattr(getattr(importlib.import_module(f"ship.tests.{module}"), cls), name, None)
    if not callable(found):
        raise AssertionError(f"{dotted} is not a test")


FACTORY = Path(os.environ.get("FACTORY_HOME") or "D:/factory")
FACTORY_TESTS = FACTORY / "skills" / "factory-core" / "tests"


def factory_module(name: str):
    import importlib.util

    spec = importlib.util.spec_from_file_location(f"factory_{name}", FACTORY_TESTS / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def factory_test(name: str, cls: str, method: str) -> None:
    module = factory_module(name)
    if not callable(getattr(getattr(module, cls, None), method, None)):
        raise AssertionError(f"the factory has no {name}.{cls}.{method}")


class Loops(ChaosCase):
    """Row 57: each loop of 3.9, its exit and what happens at its round count."""

    stops = ONE_STOP
    slices = (("a1", "A", "L1"), ("a2", "A", "L2"))

    @unittest.skipUnless(FACTORY_TESTS.exists(), "the factory checkout is not here")
    def test_questions_to_him(self):
        """3 batches of 4, then the rest are listed: the factory's resume.py test (U21)."""
        factory_test("test_check_chain", "Resume", "test_too_many_open_questions_ask_for_a_list")

    @unittest.skipUnless(FACTORY_TESTS.exists(), "the factory checkout is not here")
    def test_self_annealing(self):
        """5 rounds: six rounds with no stop line fail `--stage anneal` (fixture d08, U21)."""
        FactoryFixtures.expect(self, "d08-anneal-round-limit")

    @unittest.skipUnless(FACTORY_TESTS.exists(), "the factory checkout is not here")
    def test_he_changes_his_mind(self):
        """No limit; his words go into SCOPE.md and the checks rerun from the earliest stage they touch (fixture
        v19, mind change after stage 5)."""
        FactoryFixtures.expect(self, "v19-mind-change-after-stage5-global-numbering")

    def test_second_fixes_result_waits(self):
        """Plan review and planner, 1 round trip: the reviewer writes FIXES twice; one planner-fix worker ran, then
        the conveyor exits 10 with the second FIXES waiting on him (D-L25: a round started by his answers would
        not count; these fixes quote nobody)."""
        fixes = {"match": "plan-review:", "times": 2, "steps": [{"file": {
            "{program}/plan-review/REVIEW.md": "See FIXES.md.\n\nRESULT: FIXES\nEND plan-review x\n",
            "{program}/plan-review/FIXES.md": "# Fixes\n\n- the brief of a1 names no SAFETY fact\n"}}],
            "reply": "DONE {program}/plan-review/FIXES.md"}
        planner = {"match": "planner-fix:", "steps": [{"file": {
            "{program}/plan-review/FIXES.applied.md": "# Fixes\n\n- the brief of a1 names no SAFETY fact\n"}}],
            "reply": "DONE {program}/plan-review/FIXES.applied.md"}
        self.rule(fixes)
        self.rule(planner)
        self.assertEqual(self.chain(), 10, self.out)
        self.assertEqual(len(self.calls("planner-fix:")), 1)
        self.assertEqual(len(self.calls("plan-review:")), 2)
        self.assertTrue(any("asked for fixes a second time" in w for w in self.waits()), self.waits())
        self.assertFalse(self.program.state.exists())

    def test_second_red_parks(self):
        """A slice's fix round, 1 round: `a1`'s checks are red after the build and again after its one fix round,
        so it is parked `rounds`; `a2` lands and A merges without it. Three such parks in a row trip the breaker:
        `test_foundation.StateMachine.test_breaker_counts_quality_parks_only_and_resets_on_landing`."""
        self.make_program(stops=self.stops, slices=(("a1", "A", "L1", "pkg/a1.py, pkg/tests/test_a1.py"),
                                                    ("a2", "A", "L2")))
        red = "def test_a1():\n    assert False, 'still red ({dispatch})'\n"
        self.rule({"match": "a1", "steps": [{"write": {"pkg/a1.py": "def a1():\n    return 'a1 {dispatch}'\n",
                                                       "pkg/tests/test_a1.py": red}},
                                            {"commit": "a1: work"}, {"push": True}, {"file": builder()["steps"][3]["file"]}],
                   "reply": "READY {head}"})
        self.assertEqual(self.chain(), 0, self.out)
        a1 = self.state().slices["a1"]
        self.assertEqual((a1.status, a1.attempts), (st.Status.PARKED, 2))
        self.assertIn("rounds", a1.reason)
        self.assertEqual(len(self.calls("fixer:", "a1")), 1, "one fix round, no second")
        covered("test_foundation.StateMachine.test_breaker_counts_quality_parks_only_and_resets_on_landing")
        self.assert_converged(target_has=["a2"], waits=None)

    def test_worker_dying(self):
        """3 restarts, then parked: chaos row 8."""
        covered("test_chain_chaos.Garbage.test_garbage_builder_parks_after_three")
        covered("test_run.DeathsNotLimits.test_limit_restarts_never_park_and_the_third_death_does")

    def test_checkpoint_fix_batch(self):
        """2 rounds, no third: chaos row 32."""
        covered("test_chain_chaos.Rounds.test_round_two_blocked_waits")

    def test_reader_not_finishing(self):
        """1 restart, then NOT READ, which blocks: kit row 35."""
        covered("test_review.NotRead.test_a_hanging_reader_becomes_not_read_and_a_clean_verdict_is_refused")
        covered("test_k4.AuditStages.test_a_reader_that_never_finishes_waits_on_him_after_its_restarts")

    def test_waiting_on_ci(self):
        """2 long waits, then WAITS: chaos row 33."""
        covered("test_chain_chaos.Ci.test_ci_stuck_waits_no_local_merge")

    def test_merge_when_the_target_moved(self):
        """Merge when the target moved. F8 (D-L26, fixed; D-L26 sets 5 tries, `merge_moved_max`, where the design
        said 2): each refusal because the target moved is counted; at the fifth the conveyor WAITS, naming the
        merges that moved the target, and exits 10. Before the fix it retried every tick forever. (Turn order among
        waiters is `test_locks.MergeQueue`; one moved target merged in is
        `test_merge.Clean.test_the_merge_names_the_reviewed_head_and_a_moved_target_is_a_retry`.)"""
        covered("test_merge.Clean.test_the_merge_names_the_reviewed_head_and_a_moved_target_is_a_retry")
        self.make_program(stops=self.stops, slices=(("a1", "A", "L1"),))
        self.gh_flag("fake-gh-merge-moves-base-always", True)
        self.assertEqual(self.chain(), 10, self.out)
        self.assertEqual(self.chain_log().count("the target moved ("), 4, "four retries, then the fifth waits")
        waits = [w for w in self.waits() if "because the target moved" in w]
        self.assertEqual(len(waits), 1, self.waits())
        self.assertIn("5 times", waits[0])
        self.assertIn("other program: merged", waits[0])
        self.assertEqual(self.state().merged, [])

    def test_plan_review_with_no_result_waits_after_its_restarts(self):
        """D-L26's general rule, the plan-review loop: a reviewer that ends DONE but writes no `RESULT:` line was
        started again every tick; now its runs count toward `max_restarts`, then WAITS."""
        self.rule({"match": "plan-review:", "reply": "DONE nothing written"})
        self.assertEqual(self.chain(), 10, self.out)
        self.assertEqual(len(self.calls("plan-review:")), 3)
        self.assertTrue(any("plan-review worker was started 3 times" in w for w in self.waits()), self.waits())
        self.assertFalse(self.program.state.exists())

    @unittest.skipUnless(FACTORY_TESTS.exists(), "the factory checkout is not here")
    def test_budget_growth(self):
        """Every raise is his: fixture row 14."""
        FactoryFixtures.expect(self, "d03-over-budget-with-his-yes")
        FactoryFixtures.expect(self, "d04-over-budget-raised-by-agent")

    def test_core_then_later(self):
        """LATER never starts before the core merged: chaos rows 18 and 19."""
        covered("test_chain_chaos.CoreThenLater.test_core_not_proven_blocks_later")
        covered("test_chain_chaos.CoreThenLater.test_later_briefs_written_after_core")

    @unittest.skip("not testable here: U33 (ship backlog, the hand-off row's hops) is not built")
    def test_audit_and_plan(self):
        """1 crossing; a second goes to him (row 22)."""

    @unittest.skip("not testable here: U33 (ship backlog) and U34 (scripted intake) are not built")
    def test_backlog(self):
        """Nothing leaves the backlog without his yes."""


class Named(unittest.TestCase):
    """Rows another kit unit's test already covers: the test is named here, so a rename or deletion fails."""

    def test_property_killed_at_every_step_boundary(self):
        """13.1's shared property, run from go to merged with the conveyor killed after every activity."""
        covered("test_chain.EndToEnd.test_killed_after_each_activity_and_restarted_it_ends_the_same")
        covered("test_run.Interrupted.test_killed_mid_landing_then_rerun_lands_every_slice_once")

    def test_row_01_hold_inside_review_and_merge(self):
        """Row 1 inside a checkpoint review and a merge (D-L25: HOLD stops every new start there too)."""
        covered("test_k4a.HoldScope.test_no_checkpoint_review_starts")
        covered("test_k4a.HoldScope.test_no_merge_starts_but_a_running_merge_is_still_read")
        covered("test_power_watch.PowerSteps.test_battery_holds_then_mains_settles_and_network_gates_the_clear")

    def test_row_10b_unpark_while_open_else_backlog(self):
        """D-L13: unpark is refused once that checkpoint's review has started; after the merge it is a backlog row
        (the row itself is U33's)."""
        covered("test_run.Unpark.test_blocked_slice_parks_with_a_wait_line_and_unpark_lands_it")
        covered("test_run.Unpark.test_unpark_is_refused_after_the_checkpoint_merged")
        covered("test_run.UnparkPins.test_unpark_is_refused_once_the_review_started")

    def test_row_30_merge_conflict_becomes_fix_program(self):
        covered("test_merge.Moved.test_a_conflicting_target_writes_the_one_slice_fix_program")

    def test_row_34_flaky(self):
        """D-L25: flaky follows CI (rerun once; excused only when listed, untouched and green again)."""
        covered("test_k4a.CiAgreement.test_flaky_follows_ci_rerun_once_excused_only_when_listed_untouched_and_green_again")
        covered("test_k4a.FlakyInChecks.test_a_flaky_test_not_listed_blocks_and_a_listing_added_by_the_slice_excuses_nothing")

    def test_row_35_reader_not_read_blocks(self):
        covered("test_review.NotRead.test_a_hanging_reader_becomes_not_read_and_a_clean_verdict_is_refused")

    def test_row_36_second_conveyor_refused(self):
        covered("test_chain.Waits.test_a_second_conveyor_on_a_running_program_exits_11")
        covered("test_run.Interrupted.test_second_run_on_the_same_program_exits_11")

    def test_row_37_low_disk_warns_only(self):
        covered("test_arm.Preflight.test_low_disk_warns_and_still_arms")

    def test_row_38_wrong_gh_account_refuses_arm(self):
        covered("test_arm.Preflight.test_wrong_gh_account_fails_and_the_owner_passes")

    def test_row_44_two_record_writers(self):
        covered("test_records.Lock.test_a_second_holder_waits_for_the_first")
        covered("test_dl22.RecordsRace.test_a_records_commit_never_indexes_a_programs_phase_json")

    def test_row_45_tracker_edit_does_not_stop_a_run(self):
        covered("test_arm.MainCheck.test_tracker_and_claude_edits_do_not_stop_a_run_and_a_code_edit_does")

    def test_row_46_shared_file_makes_one_slice_wait(self):
        covered("test_claims.Build.test_only_the_slice_naming_a_claimed_file_waits_and_starts_once_released")

    def test_row_47_two_merges_take_turns(self):
        covered("test_claims.Merges.test_two_merges_take_turns_and_the_second_carries_the_first")

    def test_row_49_oldest_waiter_goes_first(self):
        covered("test_locks.MergeQueue.test_three_waiters_take_the_lock_in_the_order_they_asked")

    def test_row_50_stale_claim_swept(self):
        covered("test_claims.Build.test_the_claims_of_a_deleted_program_are_swept")
        covered("test_dl22.ClaimsOrder.test_c2_the_sweep_keeps_a_merged_program_whose_conveyor_runs")

    def test_row_56_one_fable_at_a_time(self):
        covered("test_locks.FableSeat.test_two_fable_workers_never_overlap")

    def test_x4_sweep_and_feature_side_by_side(self):
        covered("test_claims.Build.test_disjoint_programs_build_and_land_side_by_side")
        covered("test_claims.Merges.test_two_merges_take_turns_and_the_second_carries_the_first")


@unittest.skipUnless(FACTORY_TESTS.exists(), "the factory checkout is not here (FACTORY_HOME)")
class FactoryFixtures(unittest.TestCase):
    """Rows whose check is a factory fixture (section 13, kind `fixture`): each runs the factory's own
    `check_chain.py` on the named fixture through its test module's `run` and `as_expected`, read-only."""

    @staticmethod
    def expect(case: unittest.TestCase, name: str) -> None:
        module = factory_module("test_check_chain")
        failing = module.EXPECTED[name]
        fails = module.run(name)
        case.assertTrue(module.as_expected(name, fails, failing), f"{name}: expected {failing or 'PASS'}, got {fails}")

    def test_row_06_resume_mid_anneal(self):
        self.expect(self, "d09-resume-mid-anneal")
        factory_test("test_check_chain", "Resume", "test_mid_anneal")

    def test_row_14_over_budget(self):
        self.expect(self, "d03-over-budget-with-his-yes")
        self.expect(self, "d04-over-budget-raised-by-agent")
        self.expect(self, "v21-growth-without-reason")

    def test_row_16_nothing_to_call_out(self):
        """No script for row 16 ("—"): a call-outs section must be there (e16), and none is invented (c01)."""
        self.expect(self, "e16-no-call-outs")
        self.expect(self, "c01-challenge-pass")

    def test_row_17_later_in_core_slice(self):
        self.expect(self, "d02-later-ask-in-core-slice")

    def test_row_20_design_finding_needs_handoff(self):
        self.expect(self, "g05-design-finding-no-hand-off")
        self.expect(self, "g22-design-handed-as-later")
        self.expect(self, "g23-design-in-a-brief")
        self.expect(self, "g01-audit-pass")

    def test_row_26_unapproved_one_way_door(self):
        self.expect(self, "g04-his-removal-no-answer")
        self.expect(self, "g18-his-answer-still-open")

    def test_row_52_intent_changed_after_quality(self):
        self.expect(self, "g07-intent-changed-after-quality")

    def test_row_53_leave_it_as_it_works(self):
        self.expect(self, "g08-leave-it-as-it-works")
        self.expect(self, "g11-no-leave-it-choice")

    def test_row_54_fable_decides_visible_removal(self):
        """The lint on a `ui` REMOVE row Fable decided is the audit-area's `LintFindings`; the check that every
        Fable removal is listed is g14."""
        self.expect(self, "g14-fable-removal-not-listed")
        module = factory_module_at(FACTORY / "skills" / "audit-area" / "tests", "test_audit_scripts")
        self.assertTrue(callable(getattr(module.LintFindings, "test_each_bad_row_fails_on_its_own_id", None)))

    def test_row_55_core_restructure_no_measure(self):
        self.expect(self, "c07-audit-core-restructure-no-measure")
        self.expect(self, "g06-core-restructure-no-measure")

    def test_row_58_index_drift(self):
        factory_test("test_check_index", "CheckIndex", "test_each_broken_copy_fails_on_its_own_line")

    def test_row_11_retired_id_cited(self):
        """Row 11: his changed mind retires S1.b; a brief that still cites it fails on exactly
        `retired-S1.b-still-cited` (factory 2fcbb35, `h01`)."""
        self.expect(self, "h01-retired-id-cited")

    def test_row_15_he_overrules_a_drop(self):
        """Row 15: his settled word keeps a row the challenger dropped (`h02` passes); the same overrule written by
        an agent fails on `verdict-S2-his-call-settled` (`h03`)."""
        self.expect(self, "h02-he-overrules-a-drop")
        self.expect(self, "h03-agent-overrules-a-drop")


def factory_module_at(folder: Path, name: str):
    import importlib.util

    spec = importlib.util.spec_from_file_location(f"factory_{name}", folder / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(folder))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(folder))
    return module

if __name__ == "__main__":
    unittest.main()
