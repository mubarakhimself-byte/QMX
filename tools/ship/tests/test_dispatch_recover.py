import dataclasses
import datetime as dt
import re
import unittest

from ship import state as st
from ship.dispatch import Dispatched, Parked, Refused, dispatch
from ship.recover import recover
from ship.settings import load_settings
from ship.state import Status
from ship.tests.fixture import BRIEF, RepoCase, sh, write


class DispatchCase(RepoCase):
    def setUp(self):
        super().setUp()
        self.settings = load_settings(self.program.dir)

    def go(self, sid, **overrides):
        return dispatch(self.program, sid, dataclasses.replace(self.settings, **overrides))

    def set_status(self, sid, status, **fields):
        with st.locked(self.program) as state:
            state.slices[sid].status = status
            for k, v in fields.items():
                setattr(state.slices[sid], k, v)


class FirstDispatch(DispatchCase):
    def test_creates_worktree_at_tip_and_records_holder(self):
        got = self.go("s1")
        self.assertIsInstance(got, Dispatched)
        self.assertEqual((got.kind, got.attempt, got.restart, got.branch), ("first", 1, 0, "slice/s1"))
        self.assertEqual(sh(self.wt_root / "slice-s1", "git", "rev-parse", "HEAD"), self.tip())
        self.assertEqual(sh(self.wt_root / "slice-s1", "git", "branch", "--show-current"), "slice/s1")
        sl = st.load(self.program).slices["s1"]
        self.assertEqual((sl.status, sl.attempts, sl.restarts, sl.parent), (Status.HELD, 1, 0, self.tip()))
        self.assertEqual(sl.holder.dispatch_id, got.dispatch_id)
        self.assertEqual((self.program.evidence("s1", 1) / "facts.log").read_text("utf-8"),
                         "PASS fact F1\nPASS fact SAFETY\n")

    def test_brief_mismatch_parks_and_blocks_dependents(self):
        write(self.program.brief("s1"), BRIEF.replace("pkg/app.py:1", "pkg/app.py:2"))
        got = self.go("s1")
        self.assertIsInstance(got, Parked)
        self.assertEqual(got.blocked, ["s3", "s4"])
        state = st.load(self.program)
        self.assertEqual(state.slices["s1"].status, Status.PARKED)
        self.assertTrue(state.slices["s1"].reason.startswith("brief-mismatch: facts ['F1']"))
        self.assertFalse((self.wt_root / "slice-s1").exists())
        log = (self.program.evidence("s1", 1) / "facts.log").read_text("utf-8")
        self.assertIn("FAIL fact F1 rc=0 want rc=0\n  want: 'pkg/app.py:2'\n  got:  'pkg/app.py:1'", log)

    def test_overlap_with_held_slice_is_refused(self):
        self.go("s1")
        with st.locked(self.program) as state:
            state.slices["s3"].depends_on = []
        with self.assertRaisesRegex(Refused, r"overlap an in-flight slice.*s1: pkg/mul.py ~ pkg/mul.py"):
            self.go("s3")

    def test_unlanded_dependency_seats_and_hold_refuse(self):
        with self.assertRaisesRegex(Refused, r"s3 waits on \['s1'\]"):
            self.go("s3")
        self.go("s1", seats=1)
        with self.assertRaisesRegex(Refused, "no free seat: 1 of 1 held"):
            self.go("s2", seats=1)
        write(self.program.hold, "battery since 02:00\n")
        with self.assertRaisesRegex(Refused, "hold is on: battery since 02:00"):
            self.go("s2")


class FixRounds(DispatchCase):
    def test_second_round_then_park_on_third(self):
        first = self.go("s1")
        wt = self.wt_root / "slice-s1"
        write(wt / "pkg" / "mul.py", "def mul(a, b):\n    return a * b\n")
        pushed = self.commit("s1 work", wt)
        sh(wt, "git", "push", "-q", "-u", "origin", "slice/s1")
        self.set_status("s1", Status.RED)
        second = self.go("s1")
        self.assertEqual((second.kind, second.attempt, second.restart), ("fix", 2, 0))
        self.assertNotEqual(second.dispatch_id, first.dispatch_id)
        self.assertEqual(sh(wt, "git", "rev-parse", "HEAD"), pushed)
        self.set_status("s1", Status.RED)
        third = self.go("s1")
        self.assertIsInstance(third, Parked)
        self.assertEqual(third.reason, "2 rounds used")
        state = st.load(self.program)
        self.assertEqual([state.slices[s].status for s in ("s1", "s3", "s4")],
                         [Status.PARKED, Status.BLOCKED_BY, Status.BLOCKED_BY])


class Recover(DispatchCase):
    def test_dead_seat_leftovers_saved_reset_to_pushed_and_restart_counted(self):
        future = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=1)).isoformat(timespec="seconds")
        self.go("s1")
        wt = self.wt_root / "slice-s1"
        write(wt / "pkg" / "mul.py", "def mul(a, b):\n    return a * b\n")
        pushed = self.commit("pushed", wt)
        sh(wt, "git", "push", "-q", "-u", "origin", "slice/s1")
        write(wt / "pkg" / "tests" / "test_mul.py", "UNPUSHED = 1\n")
        self.commit("unpushed", wt)
        write(wt / "pkg" / "mul.py", "UNCOMMITTED = 1\n")
        write(wt / "pkg" / "new_untracked.py", "UNTRACKED = 1\n")

        lines = recover(self.program, self.settings, usage_reset=future)
        self.assertEqual(lines[:2], ["USAGE reset at " + future, "DEAD s1"])
        patch = (self.program.evidence("s1", 1) / "leftover.patch").read_text("utf-8")
        for text in ("UNPUSHED = 1", "UNCOMMITTED = 1", "UNTRACKED = 1"):
            self.assertIn(text, patch)
        self.assertEqual(sh(wt, "git", "rev-parse", "HEAD"), pushed)
        self.assertEqual(sh(wt, "git", "status", "--porcelain"), "")
        self.assertEqual(recover(self.program, self.settings), [f"RESET s1 to {pushed[:8]}"])
        self.assertEqual(sorted(p.name for p in self.program.evidence("s1", 1).iterdir()),
                         ["facts.log", "leftover.patch"])

        state = st.load(self.program)
        self.assertEqual(state.usage_reset_at, future)
        with self.assertRaisesRegex(Refused, "usage limit resets at " + re.escape(future[:10])):
            self.go("s1")
        with st.locked(self.program) as state:
            state.usage_reset_at = "2020-01-01T00:00:00+00:00"
        again = self.go("s1")
        self.assertEqual((again.kind, again.attempt, again.restart), ("restart", 1, 1))


if __name__ == "__main__":
    unittest.main()
