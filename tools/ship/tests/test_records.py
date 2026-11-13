import os
import subprocess
import sys
import textwrap
import time
import unittest
from pathlib import Path

from ship import records
from ship.layout import records_of
from ship.settings import Settings
from ship.tests.fixture import RepoCase, sh, write

TOOLS = Path(__file__).resolve().parents[2]
SEEDS = [".gitignore", "README.md", "_records/BACKLOG.tsv", "_records/CLAIMS.tsv", "_records/PREFIXES.md",
         "_records/REMOVED.md"]


class RecordsCase(RepoCase):
    def setUp(self):
        super().setUp()
        self.settings = Settings()
        self.plans = self.root / "plans"

    def init(self, plans=None, repo=None):
        return records.init(repo or self.repo, plans or self.plans, "origin", self.settings)

    def remote_plans(self):
        out = sh(self.repo, "git", "ls-remote", "origin", "refs/heads/plans")
        return out.split()[0] if out else None


class Init(RecordsCase):
    def test_fresh_init_makes_branch_worktree_seeds_and_pushes(self):
        main_status = sh(self.repo, "git", "status", "--porcelain")
        main_head = sh(self.repo, "git", "rev-parse", "HEAD")
        lines = self.init()
        self.assertEqual(lines[0], f"WORKTREE {self.plans} on a new orphan branch plans")
        self.assertEqual(sh(self.plans, "git", "branch", "--show-current"), "plans")
        self.assertEqual(sh(self.plans, "git", "ls-files").splitlines(), SEEDS)
        head = sh(self.plans, "git", "rev-parse", "HEAD")
        self.assertEqual(self.remote_plans(), head)
        self.assertEqual(sh(self.plans, "git", "rev-list", "--count", "HEAD"), "1")  # orphan: no code history
        rec = records_of(self.plans)
        self.assertEqual(rec.backlog.read_text("utf-8"),
                         "id\tsource\twhat\twhere\tfirst_seen\tprogram\ttouches\tdoor\tstatus\thops\n")
        self.assertEqual(rec.claims.read_text("utf-8"), "program\tkind\tpattern\tsince\treleased\n")
        self.assertIn(f"{self.plans.resolve().as_posix()}/*/SLICES.md", rec.prefixes.read_text("utf-8"))
        self.assertTrue(rec.prefixes.read_text("utf-8").endswith("- rc: risk build (rc-01 to rc-69), 2026-11\n"))
        self.assertIn("Replaced by:", rec.removed.read_text("utf-8"))
        self.assertIn("*.lock\n", (self.plans / ".gitignore").read_text("utf-8"))
        self.assertEqual(sh(self.repo, "git", "status", "--porcelain"), main_status)
        self.assertEqual(sh(self.repo, "git", "rev-parse", "HEAD"), main_head)
        self.assertEqual(sh(self.repo, "git", "branch", "--show-current"), "main")

    def test_second_init_changes_nothing(self):
        self.init()
        head = sh(self.plans, "git", "rev-parse", "HEAD")
        tree = sh(self.plans, "git", "rev-parse", "HEAD^{tree}")
        lines = self.init()
        self.assertEqual(lines, [f"WORKTREE {self.plans} already on plans", "UNCHANGED every seed file is there"])
        self.assertEqual(sh(self.plans, "git", "rev-parse", "HEAD"), head)
        self.assertEqual(sh(self.plans, "git", "rev-parse", "HEAD^{tree}"), tree)
        self.assertEqual(sh(self.plans, "git", "status", "--porcelain"), "")

    def test_init_fills_in_a_missing_seed_with_one_commit(self):
        self.init()
        records_of(self.plans).claims.unlink()
        sh(self.plans, "git", "commit", "-q", "-am", "drop claims")
        lines = self.init()
        self.assertEqual(lines[1], "SEEDED _records/CLAIMS.tsv")
        self.assertEqual(sh(self.plans, "git", "rev-list", "--count", "HEAD"), "3")
        self.assertEqual(self.remote_plans(), sh(self.plans, "git", "rev-parse", "HEAD"))

    def test_init_checks_out_the_remote_plans_branch(self):
        self.init()
        pushed = self.remote_plans()
        other = self.root / "other"
        sh(self.root, "git", "clone", "-q", str(self.remote), str(other))
        for key, value in (("user.name", "ship test"), ("user.email", "ship@test.invalid")):
            sh(other, "git", "config", key, value)
        plans2 = self.root / "plans2"
        lines = records.init(other, plans2, "origin", self.settings)
        self.assertEqual(lines, [f"WORKTREE {plans2} on origin/plans {pushed[:8]}", "UNCHANGED every seed file is there"])
        self.assertEqual(sh(plans2, "git", "rev-parse", "HEAD"), pushed)
        self.assertEqual(sh(plans2, "git", "branch", "--show-current"), "plans")
        self.assertEqual(self.remote_plans(), pushed)

    def test_a_full_folder_in_the_way_is_refused(self):
        write(self.plans / "stray.txt", "x\n")
        with self.assertRaisesRegex(records.RecordsError, "is not empty and is not the plans worktree"):
            self.init()


class Commit(RecordsCase):
    def test_commit_pushes_and_an_unreachable_remote_leaves_it_local(self):
        self.init()
        self.assertIsNone(records.commit(self.plans, "nothing", self.settings))
        write(self.plans / "p1" / "SCOPE.md", "# scope\n")
        sha = records.commit(self.plans, "p1: scope", self.settings)
        self.assertEqual(self.remote_plans(), sha)
        sh(self.plans, "git", "remote", "set-url", "origin", str(self.root / "gone.git"))
        write(self.plans / "p1" / "SCOPE.md", "# scope 2\n")
        lines: list[str] = []
        local = records.commit(self.plans, "p1: scope 2", self.settings, lines=lines)
        self.assertEqual(sh(self.plans, "git", "rev-parse", "HEAD"), local)
        self.assertEqual(len(lines), 1)
        self.assertTrue(lines[0].startswith(f"UNREACHABLE push of plans {local[:8]} left local"), lines)
        sh(self.plans, "git", "remote", "set-url", "origin", str(self.remote))
        write(self.plans / "p1" / "SCOPE.md", "# scope 3\n")
        last = records.commit(self.plans, "p1: scope 3", self.settings)
        self.assertEqual(sh(self.plans, "git", "rev-parse", "HEAD~1"), local)
        self.assertEqual(self.remote_plans(), last)


class Prefixes(RecordsCase):
    def test_clash_in_a_slices_table_and_a_pushed_branch(self):
        self.init()
        write(self.plans / "x" / "SLICES.md", "| id | name |\n|---|---|\n| ab-01 | First |\n| abc-02 | Other |\n")
        sh(self.repo, "git", "push", "-q", "origin", "main:refs/heads/slice/ab-01")
        found = records.prefix_clashes(self.plans, self.repo, "origin", "ab", self.settings)
        self.assertEqual(found, ["x/SLICES.md: ab-01", "origin slice/ab-01"])
        self.assertEqual(records.prefix_clashes(self.plans, self.repo, "origin", "zz", self.settings), [])

    def test_cli_prefix_exits_1_and_prints_each_clash(self):
        self.init()
        write(self.plans / "x" / "SLICES.md", "| id | name |\n|---|---|\n| ab-01 | First |\n")
        done = subprocess.run([sys.executable, "-m", "ship", "records", "prefix", "--plans", str(self.plans),
                               "--repo", str(self.repo), "ab"], cwd=TOOLS, capture_output=True, text=True)
        self.assertEqual((done.returncode, done.stdout), (1, "CLASH x/SLICES.md: ab-01\n"))
        done = subprocess.run([sys.executable, "-m", "ship", "records", "prefix", "--plans", str(self.plans),
                               "--repo", str(self.repo), "zz"], cwd=TOOLS, capture_output=True, text=True)
        self.assertEqual((done.returncode, done.stdout), (0, "FREE zz\n"))


HOLDER = textwrap.dedent("""\
    import sys, time
    sys.path.insert(0, sys.argv[1])
    from pathlib import Path
    from ship import records
    from ship.layout import Records
    with records.locked(Records(Path(sys.argv[2]))):
        Path(sys.argv[3]).write_text(repr(time.time()), "utf-8")
    """)


class Lock(unittest.TestCase):
    def test_a_second_holder_waits_for_the_first(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            rec = records_of(Path(tmp))
            got = Path(tmp) / "got.txt"
            with records.locked(rec):
                self.assertEqual(rec.lock.read_text("utf-8"), str(os.getpid()))
                child = subprocess.Popen([sys.executable, "-c", HOLDER, str(TOOLS), str(rec.dir), str(got)])
                time.sleep(1.5)
                self.assertFalse(got.exists())
                released = time.time()
            self.assertEqual(child.wait(timeout=30), 0)
            self.assertGreaterEqual(float(got.read_text("utf-8")), released)
            self.assertFalse(rec.lock.exists())

    def test_a_dead_holders_lock_is_taken_over(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            rec = records_of(Path(tmp))
            dead = subprocess.Popen([sys.executable, "-c", "pass"])
            dead.wait()
            rec.dir.mkdir(parents=True)
            rec.lock.write_text(str(dead.pid), "utf-8")
            with records.locked(rec):
                self.assertEqual(rec.lock.read_text("utf-8"), str(os.getpid()))


if __name__ == "__main__":
    unittest.main()
