"""ship run end to end on a scratch repo: real git, fake `claude` (tests/fake_claude.py), fake `gh`."""

import json
import os
import subprocess
import sys
import textwrap
import time
import unittest
from pathlib import Path

from ship import state as st
from ship.launch import KIT
from ship.plan import init_state
from ship.state import Status
from ship.tests.fixture import BRIEF, PY, RepoCase, sh, write

FAKE_CLAUDE = Path(__file__).resolve().parent / "fake_claude.py"

PROMPT = ("Build {SLICE} ({KIND}, attempt {ATTEMPT}, restart {RESTART}) in {WORKTREE} on {BRANCH} from {PARENT}.\n"
          "Evidence {EVIDENCE}, dispatch {DISPATCH_ID}, program {PROGRAM}, root {WORKTREE_ROOT}, kit {SHIP}.\n"
          "{LEFTOVER_LINE} {LEFTOVER} Restart of {RESTART_OF}. Fix: {FIX_REASON} {FIX_PATHS}\n")

SOURCE = "def {slice}():\n    return '{slice}'\n"
TEST = ("import importlib.util\n\n\ndef test_{slice}():\n"
        "    assert importlib.util.find_spec('pkg.{slice}') is not None\n")
EVIDENCE = {f"{{evidence}}/{name}": (f"{name}\n" + ("TRACE: {slice} -> P1 -> S1\n" if name == "pr.md" else "")
                                     + "END {head} {dispatch}\n")
            for name in ("how.md", "red.log", "report.md", "pr.md")}
HAPPY = {"match": "builder:", "steps": [
    {"write": {"pkg/{slice}.py": SOURCE, "pkg/tests/test_{slice}.py": TEST}},
    {"commit": "{slice}: work"}, {"push": True}, {"file": EVIDENCE}], "reply": "Built it.\nREADY {head}"}


def table(rows: list[tuple[str, str, str]]) -> str:
    """rows: (id, stop, lane)."""
    body = "".join(f"| {sid} | Slice {sid} | {stop} | {lane} | - | pkg/{sid}.py, pkg/tests/test_{sid}.py | S |\n"
                   for sid, stop, lane in rows)
    return "| id | name | stop | lane | depends on | files | size |\n|---|---|---|---|---|---|---|\n" + body


class RunCase(RepoCase):
    slices = [("a1", "A", "L1"), ("a2", "A", "L2")]

    def setUp(self):
        super().setUp()
        write(self.program.slices_md, table(self.slices))
        for sid, _, _ in self.slices:
            write(self.program.brief(sid), BRIEF)
        self.program.state.unlink()
        init_state(self.program.dir, self.repo, self.build_branch, self.wt_root, "origin")
        prompts = self.root / "prompts"
        write(prompts / "BUILDER.md", PROMPT)
        self.script_path = self.root / "claude-script.json"
        self.now_path = self.root / "now.txt"
        self.setting(f"claude = [{json.dumps(PY)}, {json.dumps(str(FAKE_CLAUDE))}]")
        self.setting(f"prompt_dir = {json.dumps(str(prompts))}")
        self.setting(f"factory_home = {json.dumps(str(self.root / 'no-factory'))}")
        self.setting('internet_probe = ""')
        self.setting("chain_poll_s = 0.2")
        self.rules()

    def rules(self, *extra):
        self.script_path.write_text(json.dumps([*extra, HAPPY]), "utf-8")

    def env(self, **more):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SHIP_")}
        env.update(FAKE_CLAUDE_SCRIPT=str(self.script_path), SHIP_FAKE_MAINS="1", **more)
        return env

    def run_cmd(self, *args, timeout=240, **env):
        return subprocess.run([PY, str(KIT), *args, "--program", str(self.program.dir)], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", env=self.env(**env),
                              stdin=subprocess.DEVNULL, timeout=timeout)

    def ship_run(self, timeout=240, **env):
        done = self.run_cmd("run", timeout=timeout, **env)
        self.last_out = done.stdout + done.stderr
        return done.returncode

    def start_run(self, **env):
        log = open(self.root / "run-bg.log", "w", encoding="utf-8")
        self.addCleanup(log.close)
        proc = subprocess.Popen([PY, str(KIT), "run", "--program", str(self.program.dir)], stdout=log,
                                stderr=subprocess.STDOUT, env=self.env(**env), stdin=subprocess.DEVNULL)
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        return proc

    def until(self, check, timeout=120, what=""):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if check():
                return
            time.sleep(0.2)
        raise AssertionError(f"timed out waiting for {what}")

    def state(self):
        return st.load(self.program)

    def landed_subjects(self):
        sh(self.repo, "git", "fetch", "-q", "origin")
        return sh(self.repo, "git", "log", "--format=%s", f"origin/{self.build_branch}").splitlines()

    def claude_calls(self, word):
        path = self.program.dir / "fake-claude.log"
        if not path.exists():
            return []
        rows = [json.loads(x) for x in path.read_text("utf-8").splitlines()]
        return [r for r in rows if word in r["argv"][r["argv"].index("--name") + 1].split()]

    def waits(self):
        path = self.program.waits
        return [x for x in path.read_text("utf-8").splitlines() if x.startswith("- [ ]")] if path.exists() else []

    def assert_all_landed_once(self):
        subjects = self.landed_subjects()
        for sid, _, _ in self.slices:
            self.assertEqual(sum(s.startswith(f"{sid}: ") for s in subjects), 1, subjects)
            self.assertEqual(self.state().slices[sid].status, Status.LANDED)


class SixSlices(RunCase):
    slices = [("a1", "A", "L1"), ("a2", "A", "L1"), ("a3", "A", "L1"),
              ("a4", "A", "L2"), ("a5", "A", "L2"), ("a6", "A", "L2")]

    def test_six_slices_in_two_lanes_land_and_the_stop_note_is_written(self):
        self.assertEqual(self.ship_run(timeout=600), 0, self.last_out)
        self.assert_all_landed_once()
        note = json.loads(self.program.stop_note("A").read_text("utf-8"))
        self.assertEqual(note["tip"], self.tip())
        self.assertEqual(sorted(note["landed"]), ["a1", "a2", "a3", "a4", "a5", "a6"])
        self.assertEqual(note["parked"], [])
        self.assertEqual(len(note["from"]), 40)
        first_three = [c["env"]["SHIP_SLICE"] for c in self.claude_calls("builder:")[:3]]
        self.assertEqual(sorted(first_three[:2]), ["a1", "a4"], "the first seats go to both lanes")
        self.assertFalse(self.program.chain_lock.exists())
        for sid, _, _ in self.slices:
            self.assertEqual((self.state().slices[sid].attempts, self.state().slices[sid].restarts), (1, 0))


class Interrupted(RunCase):
    slices = [("a1", "A", "L1"), ("a2", "A", "L2"), ("a3", "A", "L1")]

    def test_killed_mid_landing_then_rerun_lands_every_slice_once(self):
        self.assertEqual(self.ship_run(SHIP_RUN_STOP_AFTER="land:1"), 137, self.last_out)
        self.assertEqual(self.ship_run(), 0, self.last_out)
        self.assert_all_landed_once()
        files = sh(self.repo, "git", "ls-tree", "-r", "--name-only", f"origin/{self.build_branch}").splitlines()
        for sid, _, _ in self.slices:
            self.assertIn(f"pkg/{sid}.py", files)
        self.assertEqual(json.loads(self.program.stop_note("A").read_text("utf-8"))["tip"], self.tip())

    def test_second_run_on_the_same_program_exits_11(self):
        holder = subprocess.Popen([PY, "-c", "import time; time.sleep(60)"])
        self.addCleanup(holder.kill)
        self.program.chain_lock.write_text(json.dumps({"pid": holder.pid, "children": []}), "utf-8")
        self.assertEqual(self.ship_run(), 11, self.last_out)
        self.assertEqual(json.loads(self.program.chain_lock.read_text("utf-8"))["pid"], holder.pid)
        self.assertFalse(self.claude_calls("builder:"))


class Faults(RunCase):
    def test_usage_limit_sleeps_until_the_reset_then_restarts(self):
        self.now_path.write_text("2026-11-14T01:00:00+00:00", "utf-8")
        self.rules({"match": "builder: a1", "times": 1, "kind": "limit", "reset": "2026-11-14T02:00:00+00:00"})
        proc = self.start_run(SHIP_FAKE_NOW=str(self.now_path))
        self.until(lambda: self.state().usage_reset_at == "2026-11-14T02:00:00+00:00", what="the reset time")
        self.until(lambda: self.state().slices["a2"].status == Status.LANDED, what="a2 to land")
        time.sleep(2)
        self.assertEqual(len(self.claude_calls("a1")), 1, "nothing starts before the reset")
        self.assertEqual(self.state().slices["a1"].status, Status.DEAD)
        self.now_path.write_text("2026-11-14T02:00:01+00:00", "utf-8")
        self.assertEqual(proc.wait(timeout=240), 0)
        a1 = self.state().slices["a1"]
        self.assertEqual((a1.status, a1.restarts, a1.attempts), (Status.LANDED, 1, 1))

    def test_remote_down_holds_parks_nothing_and_counts_nothing(self):
        away = self.remote.with_name("remote-away.git")
        self.remote.rename(away)
        proc = self.start_run()
        self.until(lambda: self.program.hold.exists(), what="HOLD")
        self.until(lambda: (self.program.notes_dir / "run.log").exists()
                   and (self.program.notes_dir / "run.log").read_text("utf-8").count("POWER") >= 3, what="ticks")
        state = self.state()
        self.assertEqual({s.status for s in state.slices.values()}, {Status.PENDING})
        self.assertEqual(sum(s.attempts for s in state.slices.values()), 0)
        self.assertFalse(self.claude_calls("builder:"))
        away.rename(self.remote)
        self.assertEqual(proc.wait(timeout=240), 0)
        self.assertFalse(self.program.hold.exists())
        self.assert_all_landed_once()
        self.assertEqual([(s.attempts, s.restarts) for s in self.state().slices.values()], [(1, 0), (1, 0)])

    def test_verify_ready_on_an_unreachable_remote_exits_3_and_changes_nothing(self):
        from ship.dispatch import dispatch
        from ship.settings import load_settings

        got = dispatch(self.program, "a1", load_settings(self.program.dir))
        self.remote.rename(self.remote.with_name("gone.git"))
        done = self.run_cmd("verify_ready", "a1", "0" * 40)
        self.assertEqual(done.returncode, 3, done.stdout + done.stderr)
        self.assertIn("UNREACHABLE a1", done.stdout)
        self.assertEqual(self.state().slices["a1"].status, Status.HELD)
        self.assertEqual(self.state().slices["a1"].holder.dispatch_id, got.dispatch_id)

    def test_garbage_three_times_parks_and_the_others_land(self):
        self.rules({"match": "builder: a2", "times": 3, "kind": "garbage"})
        self.assertEqual(self.ship_run(), 0, self.last_out)
        a2 = self.state().slices["a2"]
        self.assertEqual(a2.status, Status.PARKED)
        self.assertTrue(a2.reason.startswith("manual: restarted 3 times"), a2.reason)
        self.assertEqual(a2.attempts, 1)
        self.assertEqual(len(self.claude_calls("a2")), 3)
        self.assertEqual(self.state().slices["a1"].status, Status.LANDED)
        (wait,) = self.waits()
        self.assertIn("a2 parked", wait)
        self.assertIn("I looked at it", self.program.waits.read_text("utf-8"))
        self.assertEqual(json.loads(self.program.stop_note("A").read_text("utf-8"))["parked"], ["a2"])

    def test_stale_builder_is_restarted_alone(self):
        self.setting("liveness_stale_s = 4")
        beat = {"file": {"{program}/heartbeat/{slice}": "beat"}}
        slow = {"match": "builder: a2", "times": 1,
                "steps": [beat, {"sleep": 1.5}] * 6 + HAPPY["steps"], "reply": "READY {head}"}
        self.rules({"match": "builder: a1", "times": 1, "kind": "hang"}, slow)
        self.assertEqual(self.ship_run(), 0, self.last_out)
        self.assertIn("STALE a1", self.last_out)
        self.assertNotIn("STALE a2", self.last_out)
        a1, a2 = self.state().slices["a1"], self.state().slices["a2"]
        self.assertEqual((a1.status, a1.restarts, a1.attempts), (Status.LANDED, 1, 1))
        self.assertEqual((a2.status, a2.restarts), (Status.LANDED, 0))
        self.assertEqual(len(self.claude_calls("a2")), 1, "the healthy builder kept its seat")

    def test_build_branch_deleted_waits_on_him(self):
        sh(self.repo, "git", "push", "-q", "origin", f":refs/heads/{self.build_branch}")
        self.assertEqual(self.ship_run(), 10, self.last_out)
        self.assertEqual(self.waits(), [f"- [ ] build branch `{self.build_branch}` is gone from the remote"])
        self.assertEqual(self.ship_run(), 10)
        self.assertEqual(len(self.waits()), 1)


class Unpark(RunCase):
    def test_blocked_slice_parks_with_a_wait_line_and_unpark_lands_it(self):
        self.rules({"match": "builder: a2", "times": 1, "reply": "BLOCKED needs his call on the format"})
        self.assertEqual(self.ship_run(), 0, self.last_out)
        self.assertEqual(self.state().slices["a2"].status, Status.PARKED)
        self.assertEqual(self.waits(), ["- [ ] a2 parked: its builder said BLOCKED needs his call on the format"])
        self.assertEqual(json.loads(self.program.stop_note("A").read_text("utf-8"))["parked"], ["a2"])
        done = self.run_cmd("unpark", "a2", "--why", "he answered: keep the format")
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(self.state().slices["a2"].status, Status.PENDING)
        self.assertFalse(self.program.stop_note("A").exists())
        self.assertEqual(self.ship_run(), 0, self.last_out)
        self.assert_all_landed_once()

    def test_chain_issue_goes_to_chain_issues_not_to_him(self):
        self.rules({"match": "builder: a2", "times": 1, "reply": "BLOCKED chain S1.a the plan line is wrong"})
        self.assertEqual(self.ship_run(), 0, self.last_out)
        self.assertEqual(self.waits(), [])
        self.assertIn("a2 BLOCKED chain S1.a", (self.program.notes_dir / "CHAIN-ISSUES.md").read_text("utf-8"))

    def test_unpark_is_refused_after_the_checkpoint_merged(self):
        with st.locked(self.program) as state:
            state.slices["a2"].status = Status.PARKED
            state.slices["a2"].reason = "manual: builder said BLOCKED"
            state.slices["a1"].status = Status.LANDED
            state.merged.append("A")
        done = self.run_cmd("unpark", "a2", "--why", "late answer")
        self.assertEqual(done.returncode, 1)
        self.assertIn("checkpoint A merged; this is a backlog row now", done.stdout)
        self.assertEqual(self.state().slices["a2"].status, Status.PARKED)

    def test_unpark_frees_slices_blocked_by_it(self):
        with st.locked(self.program) as state:
            state.slices["a2"].depends_on = ["a1"]
            state.park("a1", st.ParkCause.BRIEF_MISMATCH, "facts ['F1']")
            self.assertEqual(state.slices["a2"].status, Status.BLOCKED_BY)
            self.assertEqual(state.unpark("a1", "brief fixed"), ["a2"])
            self.assertEqual((state.slices["a1"].status, state.slices["a2"].status), (Status.PENDING, Status.PENDING))
            state.park("a1", st.ParkCause.ROUNDS, "2 rounds used")
            with self.assertRaisesRegex(st.StateError, "parked for rounds"):
                state.unpark("a1", "no")


if __name__ == "__main__":
    unittest.main()
