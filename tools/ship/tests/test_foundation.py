import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

from ship import state as st
from ship.evidence import end_problem
from ship.plan import PlanError, matches, outside, overlaps, parse_facts, parse_slices
from ship.settings import Settings
from ship.state import ParkCause, Status
from ship.tests.fixture import SLICES, RepoCase, write
from ship.wrapper import run_timed


class SlicesTable(unittest.TestCase):
    def test_parses_ids_deps_and_files(self):
        slices = {s.id: s for s in parse_slices(SLICES)}
        self.assertEqual(sorted(slices), ["s1", "s2", "s3", "s4"])
        self.assertEqual(slices["s3"].depends_on, ["s1"])
        self.assertEqual(slices["s1"].depends_on, [])
        self.assertEqual(slices["s1"].files, ["pkg/mul.py", "pkg/tests/test_mul.py"])

    def test_unknown_dependency_is_refused(self):
        bad = SLICES.replace("| s1 | pkg/mul.py, pkg/pow.py", "| s9 | pkg/mul.py, pkg/pow.py")
        with self.assertRaisesRegex(PlanError, "unknown"):
            parse_slices(bad)


class Facts(unittest.TestCase):
    def test_fact_block_parses_command_expect_and_exit(self):
        text = '```fact F1 exit=1\r\n$ git grep -n "a b" -- x.py\r\nline one  \r\nline two\r\n\r\n```\r\n'
        (fact,) = parse_facts(text)
        self.assertEqual(fact.id, "F1")
        self.assertEqual(fact.argv, ["git", "grep", "-n", "a b", "--", "x.py"])
        self.assertEqual(fact.expect, "line one\nline two")
        self.assertEqual(fact.exit_code, 1)

    def test_fact_without_command_line_is_refused(self):
        with self.assertRaisesRegex(PlanError, "must start"):
            parse_facts("```fact F2\nno dollar\n```\n")


class FilePatterns(unittest.TestCase):
    def test_matching(self):
        self.assertTrue(matches("pkg/", "pkg/a/b.py"))
        self.assertTrue(matches("pkg", "pkg/a.py"))
        self.assertFalse(matches("pkg", "pkg2/a.py"))
        self.assertTrue(matches("pkg/**/test_*.py", "pkg/x/y/test_q.py"))
        self.assertTrue(matches("pkg/**/test_*.py", "pkg/test_q.py"))
        self.assertFalse(matches("pkg/*.py", "pkg/x/a.py"))

    def test_overlaps(self):
        self.assertEqual(overlaps(["pkg/a.py"], ["PKG/A.py"]), [("pkg/a.py", "PKG/A.py")])
        self.assertEqual(overlaps(["pkg/**"], ["pkg/sub"]), [("pkg/**", "pkg/sub")])
        self.assertEqual(overlaps(["pkg/sub"], ["pkg/*/x.py"]), [("pkg/sub", "pkg/*/x.py")])
        self.assertEqual(overlaps(["pkg/a.py"], ["pkg/*.md"]), [])
        self.assertEqual(overlaps(["pkg/a.py"], ["other/a.py"]), [])

    def test_outside(self):
        self.assertEqual(outside(["pkg/mul.py", "pkg/tests/"], ["pkg/mul.py", "pkg/tests/t.py", "uv.lock"]),
                         ["uv.lock"])


class EndLine(unittest.TestCase):
    def test_only_the_exact_last_line_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            sha = "a" * 40
            good = write(Path(tmp) / "good.md", f"VERDICT: CLEAN\n\nEND {sha} s1-a1-r0-x\n\n")
            half = write(Path(tmp) / "half.md", "VERDICT: CLEAN\n")
            stale = write(Path(tmp) / "stale.md", f"x\nEND {'b' * 40} s1-a1-r0-x\n")
            self.assertIsNone(end_problem(good, sha, "s1-a1-r0-x"))
            self.assertIn("last line is 'VERDICT: CLEAN'", end_problem(half, sha, "s1-a1-r0-x"))
            self.assertIn("want", end_problem(stale, sha, "s1-a1-r0-x"))
            self.assertEqual(end_problem(Path(tmp) / "none.md", sha, "x"), "none.md: missing")


class StateMachine(RepoCase):
    def test_park_marks_pending_dependents_blocked_and_persists(self):
        with st.locked(self.program) as state:
            state.move("s1", Status.HELD)
            blocked = state.park("s1", ParkCause.ROUNDS, "two rounds used")
        self.assertEqual(blocked, ["s3", "s4"])
        state = st.load(self.program)
        self.assertEqual(state.slices["s4"].status, Status.BLOCKED_BY)
        self.assertEqual(state.slices["s4"].blocked_by, "s1")
        self.assertEqual(state.slices["s2"].status, Status.PENDING)

    def test_illegal_move_is_refused(self):
        with st.locked(self.program) as state:
            with self.assertRaisesRegex(st.StateError, "pending -> landed"):
                state.move("s1", Status.LANDED)

    def test_breaker_counts_quality_parks_only_and_resets_on_landing(self):
        state = st.load(self.program)
        for sid in ("s1", "s2"):
            state.move(sid, Status.HELD)
            state.park(sid, ParkCause.ROUNDS, "x")
        state.slices["s3"].status = Status.PENDING
        state.slices["s3"].depends_on = []
        state.park("s3", ParkCause.BRIEF_MISMATCH, "fact F1")
        self.assertFalse(state.breaker_tripped(3))
        state.slices["s4"].depends_on = []
        state.slices["s4"].status = Status.PENDING
        state.move("s4", Status.HELD)
        state.park("s4", ParkCause.DISPUTE, "x")
        self.assertTrue(state.breaker_tripped(3))

    def test_attempts_and_restarts_round_trip(self):
        with st.locked(self.program) as state:
            state.slices["s1"].attempts = 2
            state.slices["s1"].restarts = 5
            state.slices["s1"].holder = st.Holder("s1-a2-r5-x", 2, 5, "t")
        loaded = st.load(self.program).slices["s1"]
        self.assertEqual((loaded.attempts, loaded.restarts, loaded.holder.dispatch_id), (2, 5, "s1-a2-r5-x"))


class TimedWrapper(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.tmp = Path(self._tmp.name)
        self.settings = Settings(heartbeat_interval_s=1)

    def tearDown(self):
        self._tmp.cleanup()

    def test_timeout_stops_the_child_and_its_children(self):
        marker = self.tmp / "grandchild-alive"
        grandchild = write(self.tmp / "grandchild.py",
                           f"import time, pathlib\ntime.sleep(4)\npathlib.Path({str(marker)!r}).touch()\n")
        parent = write(self.tmp / "parent.py",
                       f"import subprocess, sys, time\nsubprocess.Popen([sys.executable, {str(grandchild)!r}])\n"
                       "time.sleep(60)\n")
        started = time.monotonic()
        result = run_timed([sys.executable, str(parent)], self.tmp, self.tmp / "t.log", 2, self.settings,
                           self.tmp / "runs")
        self.assertTrue(result.timed_out)
        self.assertEqual(result.rc, 124)
        self.assertLess(time.monotonic() - started, 20)
        time.sleep(4)
        self.assertFalse(marker.exists(), "grandchild survived the timeout")
        self.assertIn("timeout after 2s", (self.tmp / "t.log").read_text("utf-8"))

    def test_env_has_fake_keyring_private_tmp_and_heartbeat(self):
        beat = self.tmp / "beat"
        code = ("import os,tempfile;print(os.environ['PYTHON_KEYRING_BACKEND']);"
                "print(tempfile.gettempdir().startswith(os.environ['SHIP_RUN_DIR']));"
                "print(os.environ['GIT_TERMINAL_PROMPT']);print(os.environ.get('ANTHROPIC_API_KEY'));"
                "print(os.environ['QMX_HOME'].startswith(os.environ['SHIP_RUN_DIR']));import time;time.sleep(2.5)")
        os.environ["ANTHROPIC_API_KEY"] = "must-not-leak"
        try:
            result = run_timed([sys.executable, "-c", code], self.tmp, self.tmp / "e.log", 30, self.settings,
                               self.tmp / "runs", heartbeat=beat)
        finally:
            del os.environ["ANTHROPIC_API_KEY"]
        self.assertEqual(result.rc, 0)
        lines = (self.tmp / "e.log").read_text("utf-8").splitlines()
        self.assertEqual(lines[2:7], ["keyring.backends.fail.Keyring", "True", "0", "None", "True"])
        self.assertTrue(beat.exists())
        self.assertEqual(list((self.tmp / "runs").iterdir()), [], "per-run temp folder left behind")

    @unittest.skipUnless(sys.platform == "win32", "Credential Manager is Windows only")
    def test_credential_manager_call_is_refused(self):
        code = "import ctypes;ctypes.windll.advapi32.CredReadW"
        result = run_timed([sys.executable, "-c", code], self.tmp, self.tmp / "c.log", 30, self.settings,
                           self.tmp / "runs")
        self.assertNotEqual(result.rc, 0)
        self.assertIn("ship guard: CredReadW refused", (self.tmp / "c.log").read_text("utf-8"))


if __name__ == "__main__":
    unittest.main()
