import json
import sys
import unittest
from pathlib import Path

from ship import state as st
from ship.land import land
from ship.settings import load_settings
from ship.slice_checks import slice_checks
from ship.state import Status
from ship.suite import this_system
from ship.tests.fixture import RepoCase, sh, write

MUL = "def mul(a, b):\n    return a * b\n"
SUB = "def sub(a, b):\n    return a - b\n"
LONG_APP = "".join(f"LINE_{i} = {i}\n" for i in range(30))


class LandCase(RepoCase):
    def setUp(self):
        super().setUp()
        self.settings = load_settings(self.program.dir)

    def checked(self, sid, files, clean=True):
        head = self.make_ready(sid, files)
        with st.locked(self.program) as state:
            state.slices[sid].status = Status.CHECKED
            dispatch_id = state.slices[sid].holder.dispatch_id
        if clean:
            write(self.program.verdict(sid, head), f"0 findings.\nVERDICT: CLEAN\nEND {head} {dispatch_id}\n")
        return head

    def status(self, sid):
        return st.load(self.program).slices[sid].status

    def build_log(self):
        sh(self.repo, "git", "fetch", "-q", "origin")
        return sh(self.repo, "git", "log", "--format=%s", f"origin/{self.build_branch}").splitlines()


class Land(LandCase):
    def test_batch_lands_one_commit_per_slice_and_cleans_up(self):
        self.checked("s1", {"pkg/mul.py": MUL})
        self.checked("s2", {"pkg/sub.py": SUB})
        ok, lines = land(self.program, None, self.settings)
        self.assertTrue(ok, lines)
        self.assertEqual(self.build_log(), ["s2: Subtract", "s1: Multiply", "initial"])
        for sid in ("s1", "s2"):
            sl = st.load(self.program).slices[sid]
            self.assertEqual(sl.status, Status.LANDED)
            self.assertFalse((self.wt_root / f"slice-{sid}").exists())
        self.assertEqual(sh(self.repo, "git", "show", f"origin/{self.build_branch}:pkg/mul.py"), MUL.strip())
        prs = json.loads((self.repo / ".git" / "fake-gh.json").read_text("utf-8"))
        self.assertEqual([p["state"] for p in prs], ["CLOSED", "CLOSED"])
        self.assertIn("PASS land-tests", "\n".join(lines))

    def verdicts_required(self):
        self.setting("slice_verdict_required = true")
        self.settings = load_settings(self.program.dir)

    def test_checked_slice_lands_without_a_verdict_by_default(self):
        self.checked("s1", {"pkg/mul.py": MUL}, clean=False)
        ok, lines = land(self.program, ["s1"], self.settings)
        self.assertTrue(ok, lines)
        self.assertEqual(self.build_log(), ["s1: Multiply", "initial"])

    def test_slice_without_clean_verdict_is_skipped_when_verdicts_are_required(self):
        self.verdicts_required()
        head = self.checked("s1", {"pkg/mul.py": MUL}, clean=False)
        ok, lines = land(self.program, ["s1"], self.settings)
        self.assertFalse(ok)
        self.assertEqual(lines, [f"SKIP s1: s1-{head[:8]}.md: missing"])
        self.assertEqual(self.build_log(), ["initial"])

    def test_new_red_blocks_and_baseline_red_does_not(self):
        self.checked("s1", {"pkg/mul.py": MUL, "pkg/tests/test_mul.py": "def test_mul():\n    assert 1 == 2\n"})
        ok, lines = land(self.program, ["s1"], self.settings)
        self.assertFalse(ok)
        self.assertIn("new reds ['.::pkg.tests.test_mul::test_mul']", lines[-1])
        self.assertEqual(self.build_log(), ["initial"])
        self.assertEqual(self.status("s1"), Status.CHECKED)
        system = this_system()
        sh(self.repo, "git", "checkout", "-q", "-B", "b", f"origin/{self.build_branch}")
        write(self.repo / "ci" / "baselines" / "known-reds.txt",
              f"# known\n{system}|.|pkg.tests.test_mul::test_mul\n{system}|.|pkg.tests.test_app::test_add\n")
        self.commit("known reds")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        ok, lines = land(self.program, ["s1"], self.settings)
        self.assertTrue(ok, lines)
        self.assertIn("NOTE known reds pass now ['.::pkg.tests.test_app::test_add']; shrink "
                      "ci/baselines/known-reds.txt with pull_reds.py", lines)
        self.assertFalse(any(p.name.startswith("baseline") for p in self.program.dir.iterdir()),
                         "the kit keeps no list of its own")

    def test_a_flaky_listed_test_does_not_block(self):
        system = this_system()
        sh(self.repo, "git", "checkout", "-q", "-B", "b", f"origin/{self.build_branch}")
        write(self.repo / "ci" / "baselines" / "flaky.txt", f"# flaky\n{system}|.|pkg.tests.test_mul::test_mul\n")
        self.commit("flaky list")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        self.checked("s1", {"pkg/mul.py": MUL, "pkg/tests/test_mul.py": "def test_mul():\n    assert 1 == 2\n"})
        ok, lines = land(self.program, ["s1"], self.settings)
        self.assertTrue(ok, lines)

    def test_overlap_with_slice_landed_since_needs_range_review_when_verdicts_are_required(self):
        self.verdicts_required()
        write(self.repo / "pkg" / "shared.py", LONG_APP)
        self.commit("shared file")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        with st.locked(self.program) as state:
            state.slices["s1"].files.append("pkg/shared.py")
        self.checked("s1", {"pkg/shared.py": "TOP = 1\n" + LONG_APP})
        with st.locked(self.program) as state:
            state.slices["s1"].files.remove("pkg/shared.py")
            state.slices["s2"].files.append("pkg/shared.py")
        head2 = self.checked("s2", {"pkg/shared.py": LONG_APP + "BOTTOM = 1\n"})
        self.assertTrue(land(self.program, ["s1"], self.settings)[0])
        ok, lines = land(self.program, ["s2"], self.settings)
        self.assertFalse(ok)
        (review,) = [ln for ln in lines if ln.startswith("REVIEW s2")]
        self.assertIn("overlap with slices landed since: ['pkg/shared.py']", review)
        self.assertEqual(self.status("s2"), Status.CHECKED)
        diff_path = review.split("range-diff at ")[1].split(";")[0]
        self.assertIn("    +    Slice s2, head", Path(diff_path).read_text("utf-8"))
        verdict = review.split("a CLEAN verdict at ")[1].split(" lands it")[0]
        dispatch_id = st.load(self.program).slices["s2"].holder.dispatch_id
        write(self.program.dir / verdict, f"VERDICT: CLEAN\nEND {head2} {dispatch_id}\n")
        ok, lines = land(self.program, ["s2"], self.settings)
        self.assertTrue(ok, lines)
        self.assertEqual(sh(self.repo, "git", "show", f"origin/{self.build_branch}:pkg/shared.py").splitlines()[::31],
                         ["TOP = 1", "BOTTOM = 1"])

    def test_rebase_that_changes_the_patch_sends_the_slice_back_to_its_checks(self):
        write(self.repo / "pkg" / "shared.py", LONG_APP)
        self.commit("shared file")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        with st.locked(self.program) as state:
            state.slices["s1"].files.append("pkg/shared.py")
        self.checked("s1", {"pkg/shared.py": "TOP = 1\n" + LONG_APP}, clean=False)
        with st.locked(self.program) as state:
            state.slices["s1"].files.remove("pkg/shared.py")
            state.slices["s2"].files.append("pkg/shared.py")
        self.checked("s2", {"pkg/shared.py": LONG_APP + "BOTTOM = 1\n"}, clean=False)
        self.assertTrue(land(self.program, ["s1"], self.settings)[0])
        after_s1 = self.tip()
        ok, lines = land(self.program, ["s2"], self.settings)
        self.assertFalse(ok)
        (recheck,) = [ln for ln in lines if ln.startswith("RECHECK s2")]
        sl = st.load(self.program).slices["s2"]
        self.assertEqual((sl.status, sl.parent), (Status.READY, after_s1))
        self.assertEqual(recheck, f"RECHECK s2: overlap with slices landed since: ['pkg/shared.py']; "
                                  f"run slice_checks s2 on the rebased head {sl.head[:8]}")
        self.assertEqual(sh(self.repo, "git", "rev-parse", f"{sl.head}~1"), after_s1)
        ok, lines = slice_checks(self.program, "s2", self.settings)
        self.assertTrue(ok, lines)
        ok, lines = land(self.program, ["s2"], self.settings)
        self.assertTrue(ok, lines)
        self.assertEqual(sh(self.repo, "git", "show", f"origin/{self.build_branch}:pkg/shared.py").splitlines()[::31],
                         ["TOP = 1", "BOTTOM = 1"])
        self.assertEqual(sh(self.repo, "git", "for-each-ref", "refs/ship/"), "")

    def test_pyproject_change_regenerates_uv_lock(self):
        regen = write(self.root / "regen.py", "open('uv.lock', 'w').write('regenerated\\n')\n")
        (self.program.dir / "ship.toml").write_text(
            (self.program.dir / "ship.toml").read_text("utf-8")
            + f"lock_cmd = [{json.dumps(sys.executable)}, {json.dumps(str(regen))}]\n", "utf-8")
        settings = load_settings(self.program.dir)
        with st.locked(self.program) as state:
            state.slices["s1"].files += ["pyproject.toml", "uv.lock"]
        self.checked("s1", {"pkg/mul.py": MUL, "pyproject.toml": "[project]\nname='x'\n", "uv.lock": "stale\n"})
        ok, lines = land(self.program, ["s1"], settings)
        self.assertTrue(ok, lines)
        self.assertEqual(sh(self.repo, "git", "show", f"origin/{self.build_branch}:uv.lock"), "regenerated")
        self.assertEqual(self.build_log(), ["s1: Multiply", "initial"])


if __name__ == "__main__":
    unittest.main()
