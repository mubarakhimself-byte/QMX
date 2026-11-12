import datetime as dt
import json
import subprocess
import sys
from pathlib import Path

from ship import state as st
from ship.dispatch import dispatch
from ship.settings import load_settings
from ship.status import status
from ship.tests.fixture import RepoCase, sh

SHIP = Path(__file__).resolve().parent.parent


class Hook(RepoCase):
    def setUp(self):
        super().setUp()
        self.settings = load_settings(self.program.dir)
        self.d = dispatch(self.program, "s1", self.settings)
        self.wt = Path(self.d.worktree)

    def hook(self, tool, cwd=None, **tool_input):
        event = {"tool_name": tool, "tool_input": tool_input, "cwd": str(cwd or self.root)}
        done = subprocess.run([sys.executable, str(SHIP), "hook", "--program", str(self.program.dir)],
                              input=json.dumps(event), capture_output=True, text=True, timeout=60)
        return done.returncode, done.stderr.strip()

    def test_writes_inside_worktree_and_evidence_pass(self):
        self.assertEqual(self.hook("Write", file_path=str(self.wt / "pkg" / "mul.py")), (0, ""))
        self.assertEqual(self.hook("Edit", file_path=str(Path(self.d.evidence) / "how.md")), (0, ""))
        self.assertEqual(self.hook("Write", cwd=self.wt, file_path="pkg/rel.py"), (0, ""))

    def test_write_to_main_checkout_or_brief_is_refused(self):
        target = self.repo / "pkg" / "app.py"
        self.assertEqual(self.hook("Write", file_path=str(target)),
                         (2, f"ship hook: Write to {target} refused; write only in your worktree or evidence folder"))
        rc, _ = self.hook("Edit", file_path=str(self.program.brief("s1")))
        self.assertEqual(rc, 2)

    def test_git_commit_outside_worktree_is_refused(self):
        rc, why = self.hook("Bash", cwd=self.repo, command='git add -A && git commit -m "x"')
        self.assertEqual((rc, why), (2, f"ship hook: git commit in {self.repo} refused; "
                                        "commit only in your own slice worktree"))
        self.assertEqual(self.hook("Bash", cwd=self.repo, command=f'cd "{self.wt}" && git commit -m x')[0], 0)
        self.assertEqual(self.hook("Bash", cwd=self.repo, command=f'git -C "{self.wt}" commit -m x')[0], 0)
        self.assertEqual(self.hook("Bash", cwd=self.wt, command=f'git -C "{self.repo}" commit -m x')[0], 2)
        self.assertEqual(self.hook("Bash", cwd=self.repo, command="git status && git log -1")[0], 0)


class Status(RepoCase):
    def test_stale_after_no_push_and_no_heartbeat(self):
        settings = load_settings(self.program.dir)
        dispatch(self.program, "s1", settings)
        started = dt.datetime.fromisoformat(st.load(self.program).slices["s1"].holder.started)
        ok, lines = status(self.program, settings, now=started + dt.timedelta(minutes=10))
        self.assertTrue(ok)
        self.assertEqual(lines[0], "UP s1 10 min since last sign of life")
        ok, lines = status(self.program, settings, now=started + dt.timedelta(minutes=50))
        self.assertFalse(ok)
        self.assertTrue(lines[0].startswith("STALE s1 50 min without a push or heartbeat"))
        self.assertEqual(lines[-1], "SEATS 1 of 3 held; could start: ['s2']")

    def test_push_counts_as_life(self):
        settings = load_settings(self.program.dir)
        d = dispatch(self.program, "s1", settings)
        sh(Path(d.worktree), "git", "push", "-q", "-u", "origin", "slice/s1")
        later = dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=50)
        status(self.program, settings, now=later - dt.timedelta(minutes=5))
        ok, lines = status(self.program, settings, now=later)
        self.assertEqual(lines[0], "UP s1 5 min since last sign of life")
