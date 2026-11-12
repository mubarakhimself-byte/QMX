import unittest

from ship import state as st
from ship.dispatch import Dispatched, Refused, dispatch
from ship.land import land
from ship.settings import load_settings
from ship.state import StateError, Status
from ship.status import status
from ship.tests.fixture import RepoCase, sh

CHECKPOINTS = """\
# Slices

| id | name | ask | stop | lane | depends on | files | size |
|---|---|---|---|---|---|---|---|
| a1 | Multiply | S1 | A | L1 | - | pkg/mul.py, pkg/tests/test_mul.py | S |
| b1 | Subtract | S2 | B | L1 | - | pkg/sub.py | S |
| b2 | Reuses multiply | S2 | B | L2 | - | pkg/mul.py | S |
| c1 | Later | - | C | L1 | - | pkg/c.py | S |
"""

MUL = "def mul(a, b):\n    return a * b\n"
SUB = "def sub(a, b):\n    return a - b\n"


class Checkpoints(RepoCase):
    def setUp(self):
        super().setUp()
        self.use_slices(CHECKPOINTS, ["a1", "b1", "b2", "c1"])
        self.settings = load_settings(self.program.dir)

    def checked(self, sid, files):
        self.make_ready(sid, files)
        with st.locked(self.program) as state:
            state.slices[sid].status = Status.CHECKED

    def test_stop_and_ask_columns_are_read(self):
        state = st.load(self.program)
        self.assertEqual([(s.id, s.checkpoint, s.ask) for s in state.slices.values()],
                         [("a1", "A", "S1"), ("b1", "B", "S2"), ("b2", "B", "S2"), ("c1", "C", "")])
        self.assertEqual(state.open_checkpoint(), "A")

    def test_prebuild_only_one_ahead_and_only_on_files_the_open_checkpoint_does_not_touch(self):
        with self.assertRaisesRegex(Refused, "c1 is in checkpoint C, 2 ahead of the open checkpoint A"):
            dispatch(self.program, "c1", self.settings)
        with self.assertRaisesRegex(Refused, r"pre-build: files overlap checkpoint A, .*'pkg/mul.py'"):
            dispatch(self.program, "b2", self.settings)
        self.assertIsInstance(dispatch(self.program, "b1", self.settings), Dispatched)

    def test_status_lists_prebuild_apart_from_the_open_checkpoint(self):
        ok, lines = status(self.program, self.settings)
        self.assertTrue(ok)
        self.assertEqual(lines[-3:], ["CHECKPOINT A open: 0 landed, 0 in flight, 1 pending, 0 parked or blocked",
                                      "SEATS 0 of 3 held; could start: ['a1']",
                                      "PREBUILD could start: ['b1']"])

    def test_prebuilt_slice_lands_only_after_its_checkpoint_before_merges(self):
        self.checked("a1", {"pkg/mul.py": MUL})
        self.checked("b1", {"pkg/sub.py": SUB})
        ok, lines = land(self.program, None, self.settings)
        self.assertTrue(ok, lines)
        self.assertIn("HELD ['b1'] until checkpoint A merges", lines)
        self.assertEqual(st.load(self.program).slices["b1"].status, Status.CHECKED)
        ok, lines = status(self.program, self.settings)
        self.assertIn("CHECKPOINT A built: 1 landed, 0 parked or blocked; start its review", lines)

        with st.locked(self.program) as state:
            with self.assertRaisesRegex(StateError, "checkpoint B is not the open one"):
                state.mark_merged("B")
            self.assertEqual(state.mark_merged("A"), "checkpoint A merged; B is open")
            self.assertEqual(state.mark_merged("A"), "checkpoint A was already recorded merged")
        ok, lines = land(self.program, None, self.settings)
        self.assertTrue(ok, lines)
        sh(self.repo, "git", "fetch", "-q", "origin")
        self.assertEqual(sh(self.repo, "git", "log", "--format=%s", f"origin/{self.build_branch}").splitlines(),
                         ["b1: Subtract", "a1: Multiply", "initial"])


if __name__ == "__main__":
    unittest.main()
