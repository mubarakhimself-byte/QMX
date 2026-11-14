"""The K3 fix round (D-L22): the checker's hook bypasses, the review and chain mutants, and the races in
proc, records, locks, claims and phase. Real git and real processes; no real Claude run, no real merge."""

import dataclasses
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from ship import locks
from ship import phase
from ship import program as prog
from ship import state as st
from ship.claims import Claims, finished
from ship.launch import KIT
from ship.layout import Program
from ship.proc import boot_time, created, same_process
from ship.settings import Settings, load_settings
from ship.state import Status
from ship.tests.fixture import PY, RepoCase, sh, sign_gates, write
from ship.tests.test_chain import ChainCase
from ship.tests.test_review import SLICES, ReviewCase, fix_index

TMP = Path(tempfile.gettempdir())


def dead_pid() -> int:
    """The pid of a process that has exited."""
    child = subprocess.Popen([PY, "-c", "pass"], stdin=subprocess.DEVNULL)
    child.wait()
    return child.pid


# ---- the hook (D-L22: Bash is an allow-list) --------------------------------------------------------


class Bypasses(RepoCase):
    """The checker's escapes, each refused for every role; and what every role still needs passes."""

    def setUp(self):
        super().setUp()
        self.factory = self.root / "factory"
        self.d = self.program.dir
        self.notes = self.program.stop_review("A") / "chain.md"
        self.tree = self.root / "docs-wt"
        self.env = {
            "builder": {}, "fixer": {},
            "reader": {"SHIP_NOTES": str(self.notes), "SHIP_STOP": "A"},
            "fault-reader": {"SHIP_NOTES": str(self.notes), "SHIP_STOP": "A"},
            "verdict": {"SHIP_STOP": "A"}, "grounding": {}, "plan-review": {}, "planner-fix": {},
            "later-handoff": {}, "sweep-handoff": {}, "challenger": {}, "answer-linker": {}, "audit-judge": {},
            "audit-intent": {}, "audit-reader": {"SHIP_PART": "p1"}, "audit-screen": {},
            "docs": {"SHIP_WORKTREE": str(self.tree), "SHIP_BRANCH": "docs/x"},
        }

    def hook(self, role, tool, cwd=None, env=None, **tool_input):
        from ship import hook

        full = {k: v for k, v in os.environ.items() if not k.startswith("SHIP_")}
        if role is not None:
            full["SHIP_ROLE"] = role
        full.update(env if env is not None else self.env.get(role, {}))
        event = {"tool_name": tool, "tool_input": tool_input, "cwd": str(cwd or self.root)}
        with mock.patch.dict(os.environ, full, clear=True):
            return hook.decide(self.program, event)

    def escapes(self):
        review = (self.d / "stop-review" / "A" / "REVIEW.md").as_posix()
        run = (self.d / ".kit" / "A" / "review-run.json").as_posix()
        return {
            "gh pr merge": "uv run --no-sync gh pr merge 1 --merge",
            "cp to REVIEW.md": f'uv run --no-sync cp x "{review}"',
            "rm review-run.json": f'uv run --no-sync rm "{run}"',
            "rm old review-run.json": f'uv run --no-sync rm "{(self.d / "stop-review" / "A" / "review-run.json").as_posix()}"',
            "node -e": "uv run --no-sync node -e \"require('fs').writeFileSync('x','y')\"",
            "pytest > REVIEW.md": f'pytest --version > "{review}"',
            "pytest >> REVIEW.md": f'uv run --no-sync pytest --version >> "{review}"',
            "python3.12 -c": 'uv run --no-sync python3.12 -c "1"',
            "pythonw -c": 'pythonw -c "1"',
            "python -Ic": 'python -Ic "1"',
            "python -I -c": 'uv run --no-sync python -I -c "1"',
            "py -3 -c": 'py -3 -c "1"',
            "timed -- cp": f'python -m ship timed --slice a --log x -- cp a "{review}"',
            "timed -- git push": "python -m ship timed --slice a --log x -- git push origin main",
            "uv run --with": "uv run --no-sync --with evilpkg pytest",
            "uvx": "uvx something",
            "uv pip": "uv pip install x",
            "env python -c": 'uv run --no-sync env python -c "1"',
            "GIT_DIR=": f'GIT_DIR="{self.repo}/.git" git log',
            "git -c alias": "git -c alias.x=!sh x",
            "git bisect run": "git bisect run pytest",
            "git log --output": f'git log -1 "--output={review}"',
            "pytest --junitxml into MAP.md":
                f'uv run --no-sync pytest "--junitxml={(self.d / "stop-review" / "A" / "MAP.md").as_posix()}"',
            "pytest --basetemp into .kit": f'uv run --no-sync pytest "--basetemp={(self.d / ".kit").as_posix()}"',
            "$(...)": "pytest $(rm -rf x)",
            "tee REVIEW.md": f'pytest --version | tee "{review}"',
            "curl": "curl https://example.invalid",
            "bash -c": 'bash -c "echo"',
            "ship gate": f'python "{KIT}" gate go --by him --source x --advance',
            "ship merge": "python -m ship merge A",
            "timed slice traversal": "python -m ship timed --slice ../../x --log l -- pytest",
        }

    def test_every_escape_is_refused_for_every_role(self):
        for role in self.env:
            for name, command in self.escapes().items():
                with self.subTest(role=role, escape=name):
                    self.assertIsNotNone(self.hook(role, "Bash", command=command), f"{role}: {name} was allowed")

    def test_the_checkers_eight_by_name(self):
        """The K3 check's list, refused for a reader, a verdict and a builder (exit 2 through the CLI)."""
        names = ("gh pr merge", "cp to REVIEW.md", "rm review-run.json", "node -e", "pytest > REVIEW.md",
                 "python3.12 -c", "pythonw -c", "python -Ic")
        for role in ("reader", "verdict", "builder"):
            for name in names:
                full = {k: v for k, v in os.environ.items() if not k.startswith("SHIP_")}
                full.update({"SHIP_ROLE": role, **self.env[role]})
                event = {"tool_name": "Bash", "tool_input": {"command": self.escapes()[name]}, "cwd": str(self.root)}
                done = subprocess.run([PY, str(KIT), "hook", "--program", str(self.d)], env=full,
                                      input=json.dumps(event), capture_output=True, text=True, timeout=60)
                self.assertEqual(done.returncode, 2, f"{role} {name}: {done.stderr}")

    def test_what_each_role_needs_still_passes(self):
        from ship.dispatch import dispatch

        evidence = dispatch(self.program, "s1", load_settings(self.d)).evidence
        ok = {
            "reader": [("git log -1 && git status", self.root),
                       (f'cd "{self.root}" && python "{KIT}" timed --program "{self.d}" --slice review-A --log '
                        f'"{(self.d / "stop-review" / "A" / "runs" / "chain-1.log").as_posix()}" --timeout 600 -- '
                        "uv run --no-sync pytest -q", self.root),
                       ("uv run --no-sync python -m pytest -q 2>&1", self.root),
                       ("uv run --no-sync ruff check . && uv run --no-sync pyright", self.root)],
            "builder": [(f'python "{KIT}" timed --program "{self.d}" --slice s1 --log "{evidence}/fast.log" '
                         "--timeout 300 -- uv run --no-sync pytest -q", self.root),
                        ("git status && git diff --stat", self.root)],
            "verdict": [("git log --oneline -5", self.d), ("python -m ship phase", self.d)],
        }
        for role, rows in ok.items():
            for command, cwd in rows:
                with self.subTest(role=role, command=command):
                    self.assertIsNone(self.hook(role, "Bash", cwd=cwd, command=command))

    def test_a_builder_redirects_only_into_its_worktree(self):
        from ship.dispatch import dispatch

        got = dispatch(self.program, "s1", load_settings(self.d))
        wt = Path(got.worktree)
        self.assertIsNone(self.hook("builder", "Bash", cwd=wt, command="pytest -q > out.txt 2>&1"))
        self.assertIsNone(self.hook("builder", "Bash", cwd=wt, command="pytest -q | tee log.txt"))
        self.assertIsNotNone(self.hook("builder", "Bash", cwd=wt, command=f'pytest -q > "{self.root / "out.txt"}"'))
        self.assertIsNotNone(self.hook("reader", "Bash", cwd=wt, command="pytest -q > out.txt"))
        self.assertIsNone(self.hook("reader", "Bash", cwd=wt, command="pytest -q > /dev/null 2>&1"))

    def test_a_missing_or_unknown_role_and_a_bad_stop_or_part_refuse(self):
        target = str(self.d / "stop-review" / "A" / "REVIEW.md")
        self.assertIsNotNone(self.hook(None, "Write", env={}, file_path=target))
        self.assertIsNotNone(self.hook(None, "Bash", env={}, command="git status"))
        self.assertIsNotNone(self.hook("Verdict", "Write", env={"SHIP_STOP": "A"}, file_path=target))
        self.assertIsNotNone(self.hook("verdict", "Write", env={"SHIP_STOP": "../A"}, file_path=target))
        self.assertIsNotNone(self.hook("verdict", "Write", env={"SHIP_STOP": "A.B"}, file_path=target))

    def test_an_audit_reader_part_must_be_a_plain_name(self):
        """K3: SHIP_PART is checked, so `..` cannot walk its notes out of readers/."""
        self.assertIsNone(self.hook("audit-reader", "Write", env={"SHIP_PART": "p1"},
                                    file_path=str(self.d / "readers" / "p1.md")))
        self.assertIsNotNone(self.hook("audit-reader", "Write", env={"SHIP_PART": "../SLICES"},
                                       file_path=str(self.d / "SLICES.md")))
        self.assertIsNotNone(self.hook("audit-reader", "Write", env={"SHIP_PART": "x.y"},
                                       file_path=str(self.d / "readers" / "x.y.md")))

    def test_no_role_writes_the_kit_folder_and_a_builder_writes_no_stop_note(self):
        for role in self.env:
            for target in (self.d / ".kit" / "gates.log", self.d / ".kit" / "A" / "review-run.json",
                           self.d / ".kit" / "A" / "MERGE-BASE"):
                with self.subTest(role=role, target=target.name):
                    self.assertIsNotNone(self.hook(role, "Write", file_path=str(target)))
        self.assertIsNone(self.hook("builder", "Write", file_path=str(self.d / "notes" / "x.md")))
        self.assertIsNotNone(self.hook("builder", "Write", file_path=str(self.program.stop_note("A"))))


# ---- review: the kit refuses what its verdict worker gets wrong (R1-R3, R5, R8) ---------------------


class Judge(ReviewCase):
    """Checkpoint.judge on a prepared review record, no workers: each refusal and its control."""

    def judge(self, word, end, round_=1, **memo):
        from ship.review import Checkpoint

        cp = Checkpoint(self.program, "A", load_settings(self.program.dir), round_)
        cp.memo.update({"tip": self.tip(), "from": self.base, "trace_fails": [],
                        "deep": {"done": True, "green": True},
                        "readers": {"element-A1": {"done": True}, "chain": {"done": True}}})
        cp.memo.update(memo)
        write(cp.verdict_file, f"VERDICT: {word}\n\n- Important: x\n\nEND {end} checkpoint-A-round-{round_}\n")
        lines = cp.judge()
        return cp.result(), lines

    def test_a_clean_verdict_on_the_tip_passes(self):
        code, lines = self.judge("CLEAN", self.tip())
        self.assertEqual(code, 0, lines)
        self.assertEqual(json.loads(self.program.review_run("A").read_text("utf-8"))["result"], 0)

    def test_r1_a_verdict_whose_end_is_not_the_tip_is_refused(self):
        code, lines = self.judge("CLEAN", self.base)
        self.assertEqual(code, 10, lines)
        self.assertTrue((self.program.stop_review("A") / "REVIEW.refused-1.md").exists())

    def test_r2_clean_with_a_trace_fail_is_refused(self):
        code, lines = self.judge("CLEAN", self.tip(), trace_fails=["FAIL unchained commit x"])
        self.assertEqual(code, 10, lines)
        self.assertIn("REFUSED verdict: CLEAN while trace FAIL lines stand", " ".join(lines))

    def test_r3_clean_with_a_red_deep_run_is_refused(self):
        code, lines = self.judge("CLEAN", self.tip(), deep={"done": True, "green": False})
        self.assertEqual(code, 10, lines)
        self.assertIn("deep run is red", " ".join(lines))

    def fix_folder(self, text):
        fix = Program(self.program.dir.parent / "program-fix-A")
        write(fix.project_file, text)
        write(fix.slices_md, SLICES.replace("a1 |", "a1f |").replace("a2 |", "a2f |"))
        write(fix.dir / "ship.toml", "[settings]\nci = \"local\"\n")  # a worker's copy, not the parent's
        return fix

    def test_a_good_fix_folder_gets_the_parents_settings_and_a_logged_gate(self):
        fix = self.fix_folder(fix_index("program", self.tip()))
        code, lines = self.judge("BLOCKED", self.tip())
        self.assertEqual(code, 2, lines)
        self.assertEqual((fix.dir / "ship.toml").read_bytes(), (self.program.dir / "ship.toml").read_bytes())
        self.assertEqual((fix.dir / "checks.toml").read_bytes(), (self.program.dir / "checks.toml").read_bytes())
        self.assertIsNone(prog.gates_problem(fix))
        self.assertEqual(prog.logged_gates(fix)["go"]["by"], "stop-review")

    def test_r5_a_fix_folder_whose_go_gate_is_not_by_stop_review_is_refused(self):
        self.fix_folder(fix_index("program", self.tip()).replace("by: stop-review", "by: him"))
        code, lines = self.judge("BLOCKED", self.tip())
        self.assertEqual(code, 10, lines)
        self.assertTrue(any("go gate is by him" in w for w in self.waits()), self.waits())

    def test_r8_a_fix_folder_with_more_than_its_one_stop_is_refused(self):
        self.fix_folder(fix_index("program", self.tip()) + "  - id: B\n    tier: core\n")
        code, lines = self.judge("BLOCKED", self.tip())
        self.assertEqual(code, 10, lines)
        self.assertTrue(any("its stops are ['A', 'B']" in w for w in self.waits()), self.waits())

    def test_fetch_summary_refuses_a_summary_of_another_commit(self):
        from ship.review import Checkpoint

        cp = Checkpoint(self.program, "A", load_settings(self.program.dir), 1)
        cp.memo["tip"] = self.tip()
        target = self.program.nightly(self.tip()) / "summary.json"
        write(target, json.dumps({"sha": self.base, "green": True}))
        self.assertIsNone(cp.fetch_summary())
        self.assertFalse(target.exists())
        write(target, json.dumps({"sha": self.tip(), "green": True}))
        self.assertEqual(cp.fetch_summary(), str(target))


# ---- the conveyor (H1-H3, follow, detach) -----------------------------------------------------------


class Conveyor(ChainCase):
    """One conveyor tick at a time, in process."""

    def armed_at_merge(self):
        """Stop A built, reviewed CLEAN, its review record written but not yet judged (a kill after the verdict)."""
        from ship.plan import init_state

        prog.set_gate(self.program, "go", by="him", source="t:3", advance=True, at="2026-11-14")
        init_state(self.program.dir, self.repo, self.build_branch, self.wt_root, "origin")
        sh(self.repo, "git", "fetch", "-q", "origin")
        sh(self.repo, "git", "checkout", "-q", "-B", "w", f"origin/{self.build_branch}")
        write(self.repo / "pkg" / "a1.py", "def a1():\n    return 'a1'\n")
        tip = self.commit("a1: Slice a1")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        with st.locked(self.program) as state:
            state.slices["a1"].status, state.slices["a1"].landed_sha = Status.LANDED, tip
            state.slices["b1"].status, state.slices["b1"].reason = Status.PARKED, "manual: not in this test"
        write(self.program.stop_note("A"), json.dumps({"stop": "A", "from": self.base, "tip": tip,
                                                       "landed": ["a1"], "parked": []}))
        write(self.program.stop_review("A") / "REVIEW.md", f"VERDICT: CLEAN\n\nEND {tip} checkpoint-A-round-1\n")
        write(self.program.review_run("A"), json.dumps({
            "round": 1, "tip": tip, "from": self.base, "trace_fails": [], "deep": {"done": True, "green": True},
            "readers": {"element-A1": {"done": True}, "chain": {"done": True}}}))
        write(self.program.dir / "chain.json", json.dumps({"armed": {str(self.program.dir): True}}))
        self.assertEqual(self.phase()["next"], "merge")
        return tip

    def belt(self):
        from ship.chain import Conveyor as Belt

        belt = Belt(self.program, load_settings(self.program.dir))
        self.addCleanup(belt.stop_children)
        return belt

    def test_h1_a_verdict_the_review_never_judged_is_judged_before_any_merge(self):
        self.armed_at_merge()
        belt = self.belt()
        with mock.patch.dict(os.environ, {"SHIP_FAKE_MAINS": "1"}):
            lines = belt.tick()
        self.assertEqual(json.loads(self.program.review_run("A").read_text("utf-8")).get("result"), 0, lines)
        self.assertFalse(any(s.name.startswith("merge-") for s in belt.scripts), "no merge before the judging")

    def test_h2_a_merge_that_exits_11_is_asked_again_next_tick(self):
        self.armed_at_merge()
        belt = self.belt()
        belt.kit = lambda command, program, *args: [PY, "-c", "import sys; sys.exit(11)"]
        belt.merge({"stop": "A"})
        self.until(lambda: all(s.done() is not None for s in belt.scripts), 30, "the fake merge")
        lines = belt.merge({"stop": "A"})
        self.assertIn("MERGE A exit 11: again next tick", lines)

    def test_h3_follow_reports_a_dead_conveyor(self):
        from ship.chain import follow

        phase.set_phase(self.program, "review", "running", "conveyor")
        write(self.program.chain_lock, json.dumps({"pid": dead_pid(), "created": 1.0,
                                                   "started": dt.datetime.now(dt.timezone.utc).isoformat()}))
        got = {}
        thread = threading.Thread(target=lambda: got.setdefault("rc", follow(self.program, Settings(), 0.01)),
                                  daemon=True)
        thread.start()
        thread.join(30)
        self.assertEqual(got.get("rc"), 1, "follow must exit 1 on a dead conveyor, not loop")

    def test_follow_treats_an_exit_10_with_no_waits_line_as_waits(self):
        from ship.chain import follow

        phase.set_phase(self.program, "go", "waits", "conveyor")
        got = {}
        thread = threading.Thread(target=lambda: got.setdefault("rc", follow(self.program, Settings(), 0.01)),
                                  daemon=True)
        thread.start()
        thread.join(30)
        self.assertEqual(got.get("rc"), 10)

    @unittest.skipUnless(sys.platform == "win32", "Windows creation flags")
    def test_the_conveyor_starts_with_no_window_and_no_detached_process(self):
        from ship import chain, proc

        seen = {}

        class Fake:
            pid = 4242

        def popen(argv, **kwargs):
            seen.update(kwargs)
            return Fake()

        with mock.patch.object(proc.subprocess, "Popen", popen):
            with mock.patch("sys.stdout"):
                chain.detach(["chain", "--program", str(self.program.dir)], self.program.dir)
        flags = seen["creationflags"]
        for flag in ("CREATE_NO_WINDOW", "CREATE_NEW_PROCESS_GROUP", "CREATE_BREAKAWAY_FROM_JOB"):
            self.assertTrue(flags & getattr(subprocess, flag), flag)
        self.assertFalse(flags & subprocess.DETACHED_PROCESS)
        self.assertTrue(proc.popen_group_kwargs()["creationflags"] & subprocess.CREATE_NO_WINDOW)


# ---- processes, records, locks ----------------------------------------------------------------------


class Processes(unittest.TestCase):
    def test_an_exited_process_with_an_open_handle_is_not_the_same_process(self):
        child = subprocess.Popen([PY, "-c", "import time; time.sleep(0.5)"], stdin=subprocess.DEVNULL)
        when = created(child.pid)
        self.assertTrue(same_process(child.pid, when))
        child.wait()  # the Popen object still holds its handle, so the creation time can still be read
        self.assertFalse(same_process(child.pid, when))

    def test_phase_reads_a_chain_lock_by_pid_creation_time_and_boot(self):
        with tempfile.TemporaryDirectory() as tmp:
            program = Program(Path(tmp))
            now = dt.datetime.now(dt.timezone.utc).isoformat()
            me = {"pid": os.getpid(), "created": created(os.getpid()), "started": now}
            write(program.chain_lock, json.dumps(me))
            self.assertTrue(phase.conveyor(program)[0])
            write(program.chain_lock, json.dumps({**me, "created": 1.0}))
            self.assertFalse(phase.conveyor(program)[0], "a reused pid is not the conveyor")
            old = dt.datetime.fromtimestamp(boot_time() - 3600, dt.timezone.utc).isoformat()
            write(program.chain_lock, json.dumps({**me, "started": old}))
            self.assertFalse(phase.conveyor(program)[0], "a lock from before the boot is dead")


class LockCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.settings = dataclasses.replace(Settings(), factory_home=self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()


READER = """import json, sys, time
end = time.time() + float(sys.argv[2])
while time.time() < end:
    try:
        open(sys.argv[1], "rb").read()
    except OSError:
        pass
"""


class Locks(LockCase):
    def hammer(self, path, seconds):
        script = Path(self._tmp.name) / "reader.py"
        script.write_text(READER, "utf-8")
        child = subprocess.Popen([PY, str(script), str(path), str(seconds)], stdin=subprocess.DEVNULL)
        self.addCleanup(lambda: child.poll() is None and child.kill())
        time.sleep(0.3)
        return child

    def test_lock_writes_and_releases_survive_a_reader_holding_the_file(self):
        path = locks.run_dir(self.settings) / "x.lock"
        path.parent.mkdir(parents=True)
        path.write_text("{}", "utf-8")
        child = self.hammer(path, 3)
        n = 0
        while child.poll() is None:
            locks._write(path, {"pid": 1, "n": n})  # raises on a refused replace before D-L22
            n += 1
        self.assertGreater(n, 5)
        seat = locks.fable_lock(self.settings)
        child = self.hammer(seat.path, 3)
        cycles = 0
        while child.poll() is None:
            if seat.try_take(worker_id="w"):
                seat.release()  # raises PermissionError while the reader has it open, before D-L22
                cycles += 1
        self.assertGreater(cycles, 2)

    def test_l3_a_lock_written_before_the_boot_is_taken_over(self):
        seat = locks.fable_lock(self.settings)
        write(seat.path, json.dumps({"pid": os.getpid(), "created": created(os.getpid())}))
        self.assertFalse(locks.FileLock(seat.path).try_take(), "a live holder keeps it")
        before = boot_time() - 3600
        os.utime(seat.path, (before, before))
        self.assertTrue(locks.FileLock(seat.path).try_take(), "written before the boot: stale")

    def test_l5_a_dead_owner_with_a_live_worker_still_holds_the_lock(self):
        seat = locks.fable_lock(self.settings)
        write(seat.path, json.dumps({"pid": dead_pid(), "created": 1.0, "worker": os.getpid(),
                                     "worker_created": created(os.getpid())}))
        self.assertFalse(locks.FileLock(seat.path).try_take())
        write(seat.path, json.dumps({"pid": dead_pid(), "created": 1.0}))
        self.assertTrue(locks.FileLock(seat.path).try_take())

    def test_l2_a_waiter_that_stopped_asking_loses_its_place(self):
        lock = locks.merge_lock("qmx", self.settings)
        old = "2020-01-01T00:00:00+00:00"
        write(lock.path, json.dumps({"queue": [{"program": "gone", "pid": dead_pid(), "created": 1.0,
                                               "since": old, "seen": old}]}))
        self.assertTrue(lock.ask("p2", "A"), "a stale waiter at the head does not block the queue")
        lock.release()
        fresh = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
        write(lock.path, json.dumps({"queue": [{"program": "waiting", "pid": dead_pid(), "created": 1.0,
                                               "since": fresh, "seen": fresh}]}))
        self.assertFalse(locks.merge_lock("qmx", self.settings).ask("p3", "A"), "a recent waiter keeps its place")

    def test_two_takers_of_a_stale_lock_never_both_hold_it(self):
        path = locks.run_dir(self.settings) / "fable.lock"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"pid": dead_pid(), "created": 1.0}), "utf-8")
        a, b = locks.FileLock(path), locks.FileLock(path)
        real = locks.FileLock.held_by_live
        judged, a_tried = threading.Event(), threading.Event()

        def slow(self_):
            got = real(self_)
            if self_ is b and not judged.is_set():
                judged.set()  # b judged the old holder dead; a tries now, before b deletes it
                a_tried.wait(3)
            return got

        res = {}
        with mock.patch.object(locks.FileLock, "held_by_live", slow):
            tb = threading.Thread(target=lambda: res.__setitem__("b", b.try_take(worker_id="b")))
            tb.start()
            judged.wait(5)
            ta = threading.Thread(target=lambda: res.__setitem__("a", a.try_take(worker_id="a")))
            ta.start()
            time.sleep(0.5)
            a_tried.set()
            tb.join(20)
            ta.join(40)
        self.assertEqual(sorted(k for k, v in res.items() if v), ["b"], res)
        self.assertEqual(json.loads(path.read_text("utf-8"))["worker_id"], "b")


class RecordsRace(RepoCase):
    def test_a_records_commit_never_indexes_a_programs_phase_json(self):
        from ship import records

        plans = self.root / "plans"
        records.init(self.repo, plans, "origin", Settings())
        program = Program(plans / "p1")
        stop = threading.Event()

        def churn():
            while not stop.is_set():
                phase.set_phase(program, "build", "running", "conveyor")

        thread = threading.Thread(target=churn, daemon=True)
        thread.start()
        try:
            claims = Claims(plans, Settings())
            for n in range(15):
                claims.claim("p1", [f"pkg/f{n}.py"])
        finally:
            stop.set()
            thread.join(10)
        self.assertEqual(sh(plans, "git", "ls-files", "p1"), "", "phase.json is never committed by records")
        self.assertEqual(len(claims.live()), 15)


# ---- claims -----------------------------------------------------------------------------------------


class ClaimsOrder(RepoCase):
    def setUp(self):
        super().setUp()
        from ship import records

        self.plans = self.root / "plans"
        records.init(self.repo, self.plans, "origin", Settings())
        self.claims = Claims(self.plans, Settings())

    def fix(self, name, parent):
        folder = Program(self.plans / name)
        write(folder.project_file, f"project: qmx\nprogram: {name}\nkind: fix\nparent: {parent}\n"
                                   "gates:\n  go: null\nstop_points:\n  - id: A\n")
        return folder

    def test_only_an_earlier_claim_blocks_and_a_later_one_waits_without_a_row(self):
        self.assertEqual(self.claims.claim("p1", ["pkg/shared.py", "pkg/a.py"]), [])
        self.assertEqual(self.claims.claim("p2", ["pkg/shared.py", "pkg/b.py"]),
                         [("pkg/shared.py", "p1", "pkg/shared.py")])
        self.assertEqual(sorted((r.program, r.pattern) for r in self.claims.live()),
                         [("p1", "pkg/a.py"), ("p1", "pkg/shared.py"), ("p2", "pkg/b.py")])
        self.assertEqual(self.claims.overlaps_now("p1", ["pkg/shared.py"]), [], "the first claimer never waits")
        self.assertEqual(self.claims.claim("p1", ["pkg/shared.py"]), [])
        self.claims.release("p1")
        self.assertEqual(self.claims.claim("p2", ["pkg/shared.py", "pkg/b.py"]), [])
        self.assertIn(("p2", "pkg/shared.py"), [(r.program, r.pattern) for r in self.claims.live()])

    def test_c1_a_fix_program_never_blocks_its_parent_but_a_lookalike_name_does(self):
        self.fix("p1-fix-A", "p1")
        self.claims.claim("p1-fix-A", ["pkg/x.py"])
        self.assertEqual(self.claims.claim("p1", ["pkg/x.py"]), [], "a fix program and its parent are one family")
        write(self.plans / "p1-fix-sizing" / "PROGRAM.yaml", "project: qmx\nprogram: p1-fix-sizing\nkind: feature\n"
                                                              "gates:\n  go: null\n")
        self.claims.claim("p1-fix-sizing", ["pkg/y.py"])
        self.assertEqual(self.claims.claim("p1", ["pkg/y.py"]), [("pkg/y.py", "p1-fix-sizing", "pkg/y.py")],
                         "a name that only looks like a fix program is another program")

    def test_c2_the_sweep_keeps_a_merged_program_whose_conveyor_runs(self):
        program = Program(self.plans / "p1")
        write(program.project_file, "project: qmx\nprogram: p1\nkind: feature\ngates:\n  go: null\n"
                                    "stop_points:\n  - id: A\n")
        st.save(program, st.State(repo=str(self.repo), build_branch="build/t", remote="origin",
                                  worktree_root=str(self.wt_root), slices={}, merged=["A"]))
        self.claims.claim("p1", ["pkg/a.py"])
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        write(program.chain_lock, json.dumps({"pid": os.getpid(), "created": created(os.getpid()), "started": now}))
        self.assertEqual(finished(program, Settings()), "")
        self.assertEqual(self.claims.sweep(), [])
        program.chain_lock.unlink()
        self.assertEqual(finished(program, Settings()), "merged")
        self.assertEqual(self.claims.sweep(), ["SWEPT p1: 1 rows (merged)"])


# ---- phase: gates only from ship gate, and the merge-written fix ------------------------------------


class Gates(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.program = Program(Path(self._tmp.name) / "p")
        write(self.program.project_file, "project: qmx\nprogram: p\nkind: sweep\ngates:\n  go: null\n"
                                         "stop_points:\n  - id: A\n")
        write(self.program.slices_md, "| id | name | stop | depends on | files | size |\n|---|---|---|---|---|---|\n"
                                      "| p-1 | One | A | - | a.py | S |\n")

    def tearDown(self):
        self._tmp.cleanup()

    def test_a_gate_a_planner_wrote_into_program_yaml_waits_and_ship_gate_moves_it(self):
        text = self.program.project_file.read_text("utf-8").replace(
            "go: null", "go: {by: him, at: 2026-11-14, source: \"x\", advance: yes}")
        self.program.project_file.write_text(text, "utf-8")
        got = phase.read(self.program, Settings())
        self.assertEqual((got["next"], got["status"]), ("waits", "waits-on-him"))
        self.assertIn("only `ship gate` sets a gate", got["why"])
        done = subprocess.run([PY, str(KIT), "gate", "go", "--by", "him", "--source", "x", "--advance", "--program",
                               str(self.program.dir)], capture_output=True, text=True, timeout=60)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        self.assertEqual(phase.read(self.program, Settings())["next"], "arm")


class MergeFixRule(unittest.TestCase):
    """D-L22: the rule for a fix program `ship merge` wrote lives in phase.read."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        plans = Path(self._tmp.name)
        self.p = Program(plans / "p")
        write(self.p.project_file, "project: qmx\nprogram: p\nkind: sweep\ngates:\n  go: null\n"
                                   "stop_points:\n  - id: A\n")
        prog.set_gate(self.p, "go", by="him", source="x", advance=True, at="2026-11-14")
        write(self.p.slices_md, "| id | name | stop | depends on | files | size |\n|---|---|---|---|---|---|\n"
                                "| p-1 | One | A | - | a.py | S |\n")
        st.save(self.p, st.State(repo="r", build_branch="build/p", remote="origin", worktree_root="w",
                                 slices={"p-1": st.Slice("p-1", "One", [], ["a.py"], checkpoint="A")}))
        self.tip, self.fix_tip, self.end2 = "1" * 40, "2" * 40, "2" * 40
        write(self.p.stop_note("A"), json.dumps({"stop": "A", "from": "", "tip": self.tip}))
        write(self.p.stop_review("A") / "REVIEW.md", f"VERDICT: CLEAN\n\nEND {self.tip} x\n")
        self.fix = Program(plans / "p-fix-A")
        write(self.fix.project_file, "project: qmx\nprogram: p-fix-A\nkind: fix\nparent: p\ngates:\n  go: null\n"
                                     "stop_points:\n  - id: A\n")
        prog.set_gate(self.fix, "go", by="stop-review", source="merge/A.md", advance=True)

    def tearDown(self):
        self._tmp.cleanup()

    def test_the_fix_is_built_then_reviewed_as_round_2_then_merged(self):
        got = phase.read(self.p, Settings())
        self.assertEqual((got["next"], got.get("build_folder")), ("build", self.fix.dir.as_posix()))
        write(self.fix.stop_note("A"), json.dumps({"stop": "A", "from": self.tip, "tip": self.fix_tip}))
        got = phase.read(self.p, Settings())
        self.assertEqual((got["next"], got.get("round"), got.get("tip")), ("checkpoint-review", "2", self.fix_tip))
        write(self.p.stop_review("A") / "REVIEW-2.md", f"VERDICT: CLEAN\n\nEND {self.end2} x\n")
        got = phase.read(self.p, Settings())
        self.assertEqual((got["next"], got.get("reviewed_tip")), ("merge", self.end2))

    def test_a_fix_folder_whose_merge_gate_is_not_logged_is_not_followed(self):
        self.fix.gates_log.unlink()
        self.assertEqual(phase.read(self.p, Settings())["next"], "merge")


# ---- trace: kit commits by what they are, never by their subject ------------------------------------


class KitCommits(ReviewCase):
    def test_a_subject_alone_never_makes_a_kit_commit(self):
        sh(self.repo, "git", "fetch", "-q", "origin")
        sh(self.repo, "git", "checkout", "-q", "-B", "w2", f"origin/{self.build_branch}")
        write(self.repo / "pkg" / "sneak.py", "x = 1\n")
        sneak = self.commit("ratchet: prune 3 rows")
        write(self.repo / "ci" / "baselines" / "known-reds.txt", "a\n")
        self.commit("anything at all")
        sh(self.repo, "git", "checkout", "-q", "-B", "m", "origin/main")
        write(self.repo / "pkg" / "theirs.py", "y = 1\n")
        self.commit("another program's work")
        sh(self.repo, "git", "push", "-q", "origin", "HEAD:refs/heads/main")
        sh(self.repo, "git", "checkout", "-q", "w2")
        sh(self.repo, "git", "merge", "-q", "--no-ff", "-m", "whatever", "m")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        self.stop_note(self.base, self.tip())
        self.assertEqual(self.ship("trace", "--stop", "A"), 1, self.out)
        self.assertIn(f"FAIL unchained commit {sneak}", self.out)
        fails = [x for x in self.out.splitlines() if x.startswith("FAIL unchained")]
        self.assertEqual(len(fails), 1, fails)
