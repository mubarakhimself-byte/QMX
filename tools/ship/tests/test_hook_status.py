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


class HookCase(RepoCase):
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


class Hook(HookCase):
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
        self.assertEqual((rc, why), (2, f"ship hook: git add in {self.repo} refused; "
                                        "git writes only in your own slice worktree"))
        rc, why = self.hook("Bash", cwd=self.repo, command='git commit -m "x"')
        self.assertEqual((rc, why), (2, f"ship hook: git commit in {self.repo} refused; "
                                        "commit only in your own slice worktree"))
        self.assertEqual(self.hook("Bash", cwd=self.repo, command=f'cd "{self.wt}" && git commit -m x')[0], 0)
        self.assertEqual(self.hook("Bash", cwd=self.repo, command=f'git -C "{self.wt}" commit -m x')[0], 0)
        self.assertEqual(self.hook("Bash", cwd=self.wt, command=f'git -C "{self.repo}" commit -m x')[0], 2)
        self.assertEqual(self.hook("Bash", cwd=self.repo, command="git status && git log -1")[0], 0)



class Guard(HookCase):
    """D-L9: the checker's three escapes are refused; a normal builder flow passes."""

    def bash(self, command, cwd=None):
        return self.hook("Bash", cwd=cwd or self.wt, command=command)

    def test_the_three_escapes_are_refused(self):
        rc, why = self.bash(f'git -C "{self.repo}" reset --hard HEAD~1')
        self.assertEqual(rc, 2, why)
        self.assertIn("main checkout", why)
        rc, why = self.bash(f"""python -c "open(r'{self.root / 'outside.txt'}', 'w').write('x')\"""")
        self.assertEqual(rc, 2, why)
        self.assertIn("inline python", why)
        rc, why = self.bash("git push --force origin HEAD:main")
        self.assertEqual(rc, 2, why)
        self.assertIn("never by force", why)

    def test_a_normal_builder_flow_passes(self):
        kit = SHIP
        evidence = Path(self.d.evidence)
        for command in ("git add -A", 'git commit -m "s1: work"', "git push -u origin slice/s1",
                        f'git -C "{self.wt}" push origin slice/s1', "git push origin HEAD",
                        "git push origin HEAD:refs/heads/slice/s1", "git status && git diff --stat",
                        "uv run --no-sync pytest -q pkg/tests",
                        f'python "{kit}" timed --program "{self.program.dir}" --slice s1 --log "{evidence}/fast.log" '
                        "--timeout 300 -- uv run --no-sync pytest -q"):
            self.assertEqual(self.bash(command), (0, ""), command)

    def test_pushes_to_other_branches_or_deletions_are_refused(self):
        for command in ("git push origin slice/s2", "git push origin HEAD:engine/base", "git push origin +slice/s1",
                        "git push origin :slice/s1", "git push --delete origin slice/s1", "git push -f",
                        "git push --force-with-lease origin slice/s1", "git push --mirror origin"):
            self.assertEqual(self.bash(command)[0], 2, command)

    def test_git_writes_outside_the_worktree_are_refused(self):
        other = self.root / "elsewhere"
        other.mkdir()
        for command in (f'cd "{other}" && git reset --hard', f'git -C "{other}" checkout -b x',
                        f'git --git-dir="{self.repo / ".git"}" stash', "git tag v1", "git branch -D main"):
            cwd = self.repo if command.startswith(("git tag", "git branch")) else self.wt
            self.assertEqual(self.bash(command, cwd=cwd)[0], 2, command)
        self.assertEqual(self.bash("git log -1 && git branch --list", cwd=self.repo)[0], 0)

    def test_credentials_his_settings_and_nested_shells_are_refused(self):
        for command in ("cmdkey /list", "python -m keyring get qmx x", "uv run --no-sync python -c 'print(1)'",
                        "cat ~/.claude/settings.json", 'bash -c "git push -f"', "powershell Get-StoredCredential",
                        "cmd /c dir", f"type {Path.home() / '.claude' / 'CLAUDE.md'}",
                        "git config credential.helper store"):
            self.assertEqual(self.bash(command)[0], 2, command)


class FailsClosed(HookCase):
    """The guard refuses when it cannot run properly (exit 2), never allows."""

    def event(self):
        return json.dumps({"tool_name": "Write", "tool_input": {"file_path": str(self.wt / "x.py")},
                           "cwd": str(self.wt)})

    def raw_hook(self):
        done = subprocess.run([sys.executable, str(SHIP), "hook", "--program", str(self.program.dir)],
                              input=self.event(), capture_output=True, text=True, timeout=60)
        return done.returncode, done.stderr

    def test_a_corrupt_ship_toml_refuses(self):
        (self.program.dir / "ship.toml").write_text("[settings\nbroken = ", "utf-8")
        rc, why = self.raw_hook()
        self.assertEqual(rc, 2, why)
        self.assertIn("guard itself failed", why)

    def test_a_state_json_that_is_not_a_record_refuses(self):
        self.assertEqual(self.raw_hook()[0], 0)
        self.program.state.write_text("[]", "utf-8")
        rc, why = self.raw_hook()
        self.assertEqual(rc, 2, why)

    def test_an_empty_ship_kit_refuses_through_the_settings_command(self):
        import os
        import shutil

        bash = shutil.which("bash")
        if not bash:
            self.skipTest("no bash on this machine")
        body = json.loads((SHIP / "roles" / "builder.json").read_text("utf-8"))
        command = body["hooks"]["PreToolUse"][0]["hooks"][0]["command"]
        env = {**os.environ, "SHIP_KIT": "", "SHIP_PROGRAM": str(self.program.dir)}
        done = subprocess.run([bash, "-c", command], input=self.event(), capture_output=True, text=True, env=env,
                              timeout=60)
        self.assertEqual(done.returncode, 2, done.stderr)
        env["SHIP_KIT"] = str(SHIP)
        done = subprocess.run([bash, "-c", command], input=self.event(), capture_output=True, text=True, env=env,
                              timeout=60)
        self.assertEqual(done.returncode, 0, done.stderr)


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
