import json
import subprocess
import unittest
from collections import namedtuple
from pathlib import Path
from unittest import mock

from ship import preflight as pf
from ship.armed import teardown
from ship.facts import facts_at
from ship.gitx import gh_slug
from ship.launch import KIT
from ship.program import set_gate
from ship.settings import load_settings
from ship.tests.fixture import PY, RepoCase, sh, write

Usage = namedtuple("Usage", "total used free")


class ArmCase(RepoCase):
    def setUp(self):
        super().setUp()
        self.settings = load_settings(self.program.dir)
        self.git_dir = Path(sh(self.repo, "git", "rev-parse", "--absolute-git-dir"))

    def cli(self, *args):
        done = subprocess.run([PY, str(KIT), *args, "--program", str(self.program.dir)], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL, timeout=300)
        return done.returncode, done.stdout

    def go_gate(self):
        write(self.program.project_file, "kind: sweep\ngates: {go: null}\nabandoned: null\n")
        set_gate(self.program, "go", "him", "test", False)

    def account(self, name):
        write(self.git_dir / "fake-gh-account", name + "\n")


class MainCheck(ArmCase):
    def snapshot(self):
        write(self.program.main_snapshot, pf.snapshot_main(self.repo, self.settings, pf.code_roots(self.program)))

    def test_tracker_and_claude_edits_do_not_stop_a_run_and_a_code_edit_does(self):
        self.snapshot()
        write(self.repo / "tracker" / "notes.md", "his notes\n")
        write(self.repo / ".claude" / "settings.local.json", "{}\n")
        self.assertEqual(self.cli("main-check"), (0, "MAIN unchanged\n"))
        write(self.repo / "pkg" / "app.py", "def add(a, b):\n    return a - b\n")
        rc, out = self.cli("main-check")
        self.assertEqual(rc, 1)
        self.assertEqual(out.splitlines(), ["MAIN CHANGED: stop the run", "+  M pkg/app.py"])

    def test_paths_outside_the_package_roots_are_not_watched(self):
        write(self.program.checks_toml, '[[package]]\nroot = "pkg"\n')
        self.snapshot()
        write(self.repo / "docs" / "x.md", "x\n")
        self.assertEqual(pf.main_check(self.program, self.settings), (True, ["MAIN unchanged"]))
        write(self.repo / "tools" / "x.py", "x = 1\n")
        self.assertEqual(pf.main_check(self.program, self.settings)[1][-1], "+ ?? tools/x.py")

    def test_a_branch_switch_is_a_change(self):
        self.snapshot()
        sh(self.repo, "git", "checkout", "-q", "-b", "other")
        ok, lines = pf.main_check(self.program, self.settings)
        self.assertFalse(ok)
        self.assertTrue(lines[2].startswith("+ HEAD ") and lines[2].endswith(" other"), lines)

    def test_an_older_snapshot_without_a_branch_still_compares_the_commit(self):
        head = sh(self.repo, "git", "rev-parse", "HEAD")
        write(self.program.main_snapshot, f"HEAD {head}\n?? tracker/old.md\n")
        self.assertEqual(pf.main_check(self.program, self.settings), (True, ["MAIN unchanged"]))


class Facts(ArmCase):
    def test_a_target_commit_after_planning_is_caught_at_its_tip(self):
        ok, lines = facts_at(self.program, "origin/main", self.settings)
        self.assertTrue(ok, lines)
        write(self.repo / "pkg" / "app.py", "def plus(a, b):\n    return a + b\n")
        self.commit("rename add")
        sh(self.repo, "git", "push", "-q", "origin", "main")
        new_tip = sh(self.repo, "git", "rev-parse", "HEAD")
        rc, out = self.cli("facts", "--tip", new_tip, "--slices", "s2,s3")
        self.assertEqual(rc, 1)
        self.assertEqual(out.splitlines(), ["FAIL s2 F1 rc=1 want rc=0", "FAIL s3 F1 rc=1 want rc=0"])
        summary = (self.program.checks_root / "_facts" / new_tip[:8] / "summary.txt").read_text("utf-8")
        self.assertIn("PASS s2 SAFETY", summary)
        self.assertIn("want: 'pkg/app.py:1'", summary)
        self.assertEqual(self.cli("facts", "--tip", "origin/build/t")[0], 0)


class Preflight(ArmCase):
    def test_no_go_gate_is_refused(self):
        ok, lines = pf.preflight(self.program, self.settings)
        self.assertFalse(ok)
        self.assertEqual(lines[0], "FAIL gate-go: no PROGRAM.yaml, so no go gate")
        write(self.program.project_file, "kind: sweep\ngates: {go: null}\nabandoned: null\n")
        self.assertEqual(pf.check_gate_go(self.program), (False, "gates.go is null: he has not said go"))
        set_gate(self.program, "go", "him", "test", False)
        self.assertEqual(pf.check_gate_go(self.program), (True, "go from him (test)"))

    def test_a_version_1_scope_gate_counts_as_go(self):
        write(self.program.project_file, "program: old\nscope_gate: {by: him, source: chat}\nstop_points:\n  - id: A\n")
        self.assertEqual(pf.check_gate_go(self.program), (True, "go from him (chat)"))

    def test_wrong_gh_account_fails_and_the_owner_passes(self):
        self.account("MubarakHimself")
        self.assertEqual(pf.check_gh_account(self.repo, "origin", self.settings),
                         (False, "active gh account MubarakHimself is not owner, the owner of owner/qmx; "
                                 "run gh auth switch -u owner"))
        self.account("owner")
        self.assertEqual(pf.check_gh_account(self.repo, "origin", self.settings),
                         (True, "active gh account owner owns owner/qmx"))

    def test_low_disk_warns_and_still_arms(self):
        self.go_gate()
        self.account("owner")
        fine = (True, "stubbed for the test")
        stubs = [mock.patch.object(pf, name, return_value=fine)
                 for name in ("check_tools", "check_long_paths", "check_no_pending_reboot", "check_updates_paused")]
        stubs.append(mock.patch.object(pf.shutil, "disk_usage", return_value=Usage(500e9, 495e9, 5e9)))
        for stub in stubs:
            stub.start()
            self.addCleanup(stub.stop)
        try:
            ok, lines = pf.preflight(self.program, self.settings)
        finally:
            torn, gone = teardown(self.program, self.settings)  # the keep-awake helper stops before the temp folder goes
        self.assertTrue(torn, gone)
        self.assertTrue(ok, lines)
        (warn,) = [ln for ln in lines if ln.startswith("WARN ")]
        self.assertTrue(warn.startswith("WARN disk: 5 GB free"), warn)
        self.assertIn("PASS gh-account: active gh account owner owns owner/qmx", lines)
        self.assertIn("PASS gate-go: go from him (test)", lines)


class GitHubSlug(ArmCase):
    def test_slug_from_https_and_ssh_remotes(self):
        for url in ("https://github.com/mubarakhimself-byte/QMX.git", "git@github.com:mubarakhimself-byte/QMX.git",
                    "https://github.com/mubarakhimself-byte/QMX"):
            sh(self.repo, "git", "remote", "set-url", "origin", url)
            self.assertEqual(gh_slug(self.repo, "origin", 30), "mubarakhimself-byte/QMX")
        sh(self.repo, "git", "remote", "set-url", "origin", str(self.remote))
        self.assertEqual(gh_slug(self.repo, "origin", 30), "")

    def test_every_repo_gh_call_names_the_repo(self):
        self.make_ready("s1", {"pkg/mul.py": "def mul(a, b):\n    return a * b\n"})
        calls = [json.loads(x) for x in (self.git_dir / "fake-gh-calls.jsonl").read_text("utf-8").splitlines()]
        repo_calls = [c for c in calls if c[:1] in (["pr"], ["run"], ["workflow"])]
        self.assertTrue(repo_calls)
        for call in repo_calls:
            self.assertEqual(call[call.index("-R") + 1], "owner/qmx", call)


if __name__ == "__main__":
    unittest.main()
