import unittest

from ship import state as st
from ship.nightly import nightly
from ship.settings import load_settings
from ship.state import Status
from ship.tests.fixture import RepoCase, sh, write


class Nightly(RepoCase):
    def setUp(self):
        super().setUp()
        self.settings = load_settings(self.program.dir)
        self.first_tip = self.tip()

    def land_directly(self, sid, path, text):
        """Stand in for `land`: one commit on the build branch and the slice marked landed."""
        sh(self.repo, "git", "checkout", "-q", "-B", "b", f"origin/{self.build_branch}")
        write(self.repo / path, text)
        sha = self.commit(f"{sid}: landed")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        with st.locked(self.program) as state:
            sl = state.slices[sid]
            sl.status, sl.landed_sha, sl.parent = Status.LANDED, sha, sha
            state.log("status", sid, **{"from": "checked", "to": "landed", "reason": "test"})
        return sha

    def test_green_sets_last_green_and_writes_no_list_of_its_own(self):
        ok, lines = nightly(self.program, self.settings)
        self.assertTrue(ok, lines)
        self.assertEqual(lines, [f"PASS nightly {self.first_tip[:8]} 0 baseline reds, no new red"])
        self.assertEqual(st.load(self.program).last_green, self.first_tip)
        self.assertFalse(any(p.name.startswith("baseline") for p in self.program.dir.iterdir()))

    def test_a_red_the_repo_lists_is_known(self):
        from ship.suite import this_system

        self.land_directly("s1", "ci/baselines/known-reds.txt",
                           f"# known\n{this_system()}|.|pkg.tests.test_app::test_add\n")
        with st.locked(self.program) as state:
            state.last_green = self.first_tip
        self.land_directly("s2", "pkg/app.py", "def add(a, b):\n    return a - b\n")
        ok, lines = nightly(self.program, self.settings)
        self.assertTrue(ok, lines)
        self.assertEqual(lines, [f"PASS nightly {self.tip()[:8]} 1 baseline reds, no new red"])

    def test_new_red_is_bisected_to_its_slice_and_dependents_blocked(self):
        with st.locked(self.program) as state:
            state.last_green = self.first_tip
        bad = self.land_directly("s1", "pkg/app.py", "def add(a, b):\n    return a - b\n")
        self.land_directly("s2", "pkg/sub.py", "def sub(a, b):\n    return a - b\n")
        ok, lines = nightly(self.program, self.settings)
        self.assertFalse(ok)
        tip8 = self.tip()[:8]
        self.assertEqual(lines, [
            f"FAIL nightly {tip8} new reds ['.::pkg.tests.test_app::test_add']; first bad commit {bad} slice s1",
            "BLOCKED ['s3', 's4'] by s1",
        ])
        state = st.load(self.program)
        self.assertEqual(state.nightly["culprit"], "s1")
        self.assertEqual(state.slices["s4"].blocked_by, "s1")
        self.assertEqual(state.last_green, self.first_tip)


if __name__ == "__main__":
    unittest.main()
