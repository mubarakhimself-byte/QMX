import unittest

from ship.armed import Change, arm, read, teardown
from ship.preflight import check_fake_keyring, check_gitattributes, main_check, preflight, protection_push_test, \
    snapshot_main
from ship.proc import pid_alive
from ship.settings import load_settings
from ship.tests.fixture import RepoCase, sh, write


class Arming(RepoCase):
    def setUp(self):
        super().setUp()
        self.settings = load_settings(self.program.dir)

    def config(self, key):
        return sh(self.repo, "git", "config", "--local", "--default", "<unset>", "--get", key)

    def test_arm_records_undo_and_teardown_removes_and_verifies(self):
        sh(self.repo, "git", "config", "--local", "core.longpaths", "false")
        wanted = [Change("git-config", str(self.repo), "core.longpaths", "true"),
                  Change("git-config", str(self.repo), "ship.test", "on"),
                  Change("created-dir", str(self.program.runs)),
                  Change("keep-awake", str(self.program.dir / "KEEP-AWAKE"))]
        lines = arm(self.program, wanted, self.settings)
        self.assertEqual(lines, ["ARMED git-config core.longpaths", "ARMED git-config ship.test",
                                 f"ARMED created-dir {self.program.runs}",
                                 f"ARMED keep-awake {self.program.dir / 'KEEP-AWAKE'}"])
        text = self.program.armed.read_text("utf-8")
        self.assertIn(f'- undo: `git -C "{self.repo}" config --local core.longpaths false`', text)
        self.assertIn(f'- undo: `git -C "{self.repo}" config --local --unset ship.test`', text)
        pid = read(self.program)[3].pid
        self.assertTrue(pid_alive(pid))
        self.assertEqual(self.config("core.longpaths"), "true")

        self.assertEqual(arm(self.program, wanted, self.settings)[:2],
                         ["KEPT git-config core.longpaths", "KEPT git-config ship.test"])

        ok, lines = teardown(self.program, self.settings)
        self.assertTrue(ok, lines)
        self.assertEqual([ln.split()[0] for ln in lines], ["GONE"] * 4)
        self.assertEqual(self.config("core.longpaths"), "false")
        self.assertEqual(self.config("ship.test"), "<unset>")
        self.assertFalse(self.program.runs.exists())
        self.assertFalse(pid_alive(pid))
        self.assertEqual(read(self.program), [])
        self.assertEqual(teardown(self.program, self.settings), (True, ["NOTHING armed"]))

    def test_value_already_set_is_not_ours_to_undo(self):
        sh(self.repo, "git", "config", "--local", "core.longpaths", "true")
        lines = arm(self.program, [Change("git-config", str(self.repo), "core.longpaths", "true")], self.settings)
        self.assertEqual(lines, ["ALREADY git-config core.longpaths is true; nothing to undo"])
        teardown(self.program, self.settings)
        self.assertEqual(self.config("core.longpaths"), "true")

    def test_failed_check_arms_nothing(self):
        ok, lines = preflight(self.program, self.settings)
        self.assertFalse(ok)
        self.assertEqual(lines[-1], "REFUSED: a check failed, nothing was armed")
        self.assertIn("PASS gitattributes: 1 line-ending rules", lines)
        self.assertTrue(any(ln.startswith("FAIL tools: gh is not signed in") for ln in lines))
        self.assertFalse(self.program.armed.exists())

    def test_wrapper_guard_and_gitattributes_checks(self):
        self.assertEqual(check_fake_keyring(self.program, self.settings)[0], True)
        sh(self.repo, "git", "fetch", "-q", "origin")
        self.assertEqual(check_gitattributes(self.repo, "origin", self.build_branch, self.settings),
                         (True, "1 line-ending rules"))
        sh(self.repo, "git", "rm", "-q", ".gitattributes")
        self.commit("drop attributes")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        sh(self.repo, "git", "fetch", "-q", "origin")
        self.assertEqual(check_gitattributes(self.repo, "origin", self.build_branch, self.settings),
                         (False, ".gitattributes is missing at origin/build/t"))

    def test_main_check_sees_any_change(self):
        write(self.program.main_snapshot, snapshot_main(self.repo, self.settings))
        self.assertEqual(main_check(self.program, self.settings), (True, ["MAIN unchanged"]))
        write(self.repo / "pkg" / "stray.py", "x = 1\n")
        ok, lines = main_check(self.program, self.settings)
        self.assertFalse(ok)
        self.assertEqual(lines, ["MAIN CHANGED: stop the run", "+ ?? pkg/stray.py"])


class ProtectionPush(RepoCase):
    def test_rejected_push_passes_and_accepted_push_fails_and_is_put_back(self):
        settings = load_settings(self.program.dir)
        main_before = self.tip()
        write(self.remote / "hooks" / "pre-receive",
              "#!/bin/sh\nwhile read old new ref; do [ \"$ref\" = refs/heads/main ] && exit 1; done\nexit 0\n")
        (self.remote / "hooks" / "pre-receive").chmod(0o755)
        results = protection_push_test(self.repo, "origin", settings)
        self.assertEqual(results, [(True, "main: push rejected as required"),
                                   (True, "integration: not on origin, nothing to protect"),
                                   (True, "engine/base: not on origin, nothing to protect")])
        (self.remote / "hooks" / "pre-receive").unlink()
        results = protection_push_test(self.repo, "origin", settings)
        self.assertEqual(results[0], (False, "main: push was ACCEPTED, protection does not hold; "
                                             f"branch put back at {main_before}"))
        self.assertEqual(sh(self.repo, "git", "ls-remote", "origin", "refs/heads/main").split()[0], main_before)


if __name__ == "__main__":
    unittest.main()
