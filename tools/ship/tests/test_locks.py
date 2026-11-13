"""The machine-wide locks: the merge queue's order, the one Fable seat, the worker pool (FACTORY-DESIGN 11.6)."""

import dataclasses
import datetime as dt
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from ship import launch as ln
from ship import locks
from ship.layout import Program
from ship.settings import Settings

PY = sys.executable
FAKE_CLAUDE = Path(__file__).resolve().parent / "fake_claude.py"


class LockCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.root = Path(self._tmp.name)
        self.home = self.root / "factory"
        self.settings = dataclasses.replace(Settings(), claude=(PY, str(FAKE_CLAUDE)), factory_home=str(self.home),
                                            worker_env_extra=("FAKE_CLAUDE_SCRIPT",))
        self.script = self.root / "claude-script.json"
        patcher = mock.patch.dict(os.environ, {"FAKE_CLAUDE_SCRIPT": str(self.script)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        self._tmp.cleanup()

    def rules(self, *rules):
        self.script.write_text(json.dumps(list(rules)), "utf-8")

    def program(self, name):
        folder = self.root / "plans" / name
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "PROGRAM.yaml").write_text(f"project: qmx\nprogram: {name}\nkind: feature\n", "utf-8")
        return Program(folder)

    def finish(self, handle):
        while (got := handle.poll()) is None:
            time.sleep(0.05)
        return got

    def span(self, program, worker):
        started = json.loads((program.workers / worker / "started.json").read_text("utf-8"))["started"]
        ended = json.loads((program.workers / worker / "result.json").read_text("utf-8"))["ended"]
        return dt.datetime.fromisoformat(started), dt.datetime.fromisoformat(ended)


class MergeQueue(LockCase):
    def test_three_waiters_take_the_lock_in_the_order_they_asked(self):
        holder = locks.merge_lock("qmx", self.settings)
        self.assertTrue(holder.ask("p0", "A"))
        waiters = {name: locks.merge_lock("qmx", self.settings) for name in ("p1", "p2", "p3")}
        for name in ("p1", "p2", "p3"):
            self.assertFalse(waiters[name].ask(name, "A"))
        self.assertEqual(holder.waiting(), ["p1", "p2", "p3"])
        holder.release()
        order = []
        for _ in range(6):
            for name in ("p3", "p2", "p1"):  # asked in reverse each round: only the oldest gets it
                lock = waiters[name]
                if name not in order and lock.ask(name, "A"):
                    order.append(name)
                    lock.release()
                    break
        self.assertEqual(order, ["p1", "p2", "p3"])

    def test_a_dead_holder_is_taken_over(self):
        dead = subprocess.Popen([PY, "-c", "pass"])
        dead.wait()
        path = locks.run_dir(self.settings) / "merge-qmx.lock"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({"pid": dead.pid, "created": 1.0, "program": "gone", "stop": "A", "queue": []}))
        self.assertTrue(locks.merge_lock("qmx", self.settings).ask("p1", "A"))


class FableSeat(LockCase):
    def test_two_fable_workers_never_overlap(self):
        self.rules({"match": "challenger:", "sleep_s": 1.2, "model": "claude-fable-5", "reply": "DONE c.md"})
        role = ln.load_roles(self.settings)["challenger"]
        p1, p2 = self.program("p1"), self.program("p2")
        first = ln.launch(role, "x", self.root, p1, "w1", self.settings, label="c1")
        self.assertIsNotNone(first)
        self.assertIsNone(ln.launch(role, "x", self.root, p2, "w2", self.settings, label="c2"), "the seat is taken")
        self.finish(first)
        second = ln.launch(role, "x", self.root, p2, "w2", self.settings, label="c2")
        self.assertIsNotNone(second)
        self.finish(second)
        a, b = self.span(p1, "w1"), self.span(p2, "w2")
        self.assertGreaterEqual(b[0], a[1], f"{a} then {b}")
        self.assertFalse((locks.run_dir(self.settings) / "fable.lock").exists())

    def test_an_opus_role_does_not_take_the_fable_seat(self):
        self.rules({"match": "", "sleep_s": 0.5, "reply": "DONE x"})
        roles = ln.load_roles(self.settings)
        fable = ln.launch(roles["challenger"], "x", self.root, self.program("p1"), "w1", self.settings)
        opus = ln.launch(roles["reader"], "x", self.root, self.program("p2"), "w2", self.settings)
        self.assertIsNotNone(fable)
        self.assertIsNotNone(opus)
        self.finish(fable)
        self.finish(opus)


class WorkerPool(LockCase):
    def test_with_two_seats_never_more_than_two_workers_run_across_programs(self):
        profile = self.home / "projects" / "qmx" / "project.toml"
        profile.parent.mkdir(parents=True)
        profile.write_text("[project]\nname = \"qmx\"\n\n[pool]\nworkers = 2\n", "utf-8")
        self.rules({"match": "builder:", "sleep_s": 0.8, "reply": "DONE x"})
        role = ln.load_roles(self.settings)["builder"]
        p1, p2 = self.program("p1"), self.program("p2")
        wanted = [(p1, "a1"), (p1, "a2"), (p2, "b1"), (p2, "b2")]
        running, done, refused = {}, [], 0
        while len(done) < len(wanted):
            for program, worker in wanted:
                if worker in running or worker in done:
                    continue
                handle = ln.launch(role, "x", self.root, program, worker, self.settings, label=worker)
                if handle is None:
                    refused += 1
                    continue
                running[worker] = (program, handle)
                self.assertLessEqual(len(running), 2)
            for worker, (program, handle) in list(running.items()):
                if handle.poll() is not None:
                    del running[worker]
                    done.append(worker)
            time.sleep(0.05)
        self.assertGreater(refused, 0)
        spans = [self.span(p, w) for p, w in wanted]
        for start, _ in spans:
            self.assertLessEqual(sum(1 for s, e in spans if s <= start < e), 2)

    def test_a_slot_whose_owner_died_is_swept(self):
        pool = locks.Pool(self.settings, 1)
        pool.dir.mkdir(parents=True)
        dead = subprocess.Popen([PY, "-c", "pass"])
        dead.wait()
        (pool.dir / f"{dead.pid}-0.slot").write_text(json.dumps({"pid": dead.pid, "created": 1.0}))
        slot = pool.take()
        self.assertIsNotNone(slot)
        self.assertIsNone(pool.take())
        slot.release()
        self.assertIsNotNone(pool.take())
