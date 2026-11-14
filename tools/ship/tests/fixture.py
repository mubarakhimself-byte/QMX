"""Real git repos in a temp folder: a bare remote, a clone, a build branch, and a program folder."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

from ship import state as st
from ship.layout import Program
from ship.plan import init_state

PY = sys.executable
FAKE_GH = Path(__file__).resolve().parent / "fake_gh.py"

APP = "def add(a, b):\n    return a + b\n"
TEST_APP = "from pkg.app import add\n\n\ndef test_add():\n    assert add(1, 2) == 3\n"


def sh(cwd: Path, *argv: str) -> str:
    done = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          stdin=subprocess.DEVNULL)
    if done.returncode != 0:
        raise AssertionError(f"{argv} failed: {done.stderr}{done.stdout}")
    return done.stdout.strip()


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8", newline="\n")
    return path


SLICES = """\
# Slices

| id | name | depends on | files | size |
|---|---|---|---|---|
| s1 | Multiply | - | pkg/mul.py, pkg/tests/test_mul.py | S |
| s2 | Subtract | - | pkg/sub.py, pkg/tests/test_sub.py | S |
| s3 | Uses multiply | s1 | pkg/mul.py, pkg/pow.py | S |
| s4 | Uses s3 | s3 | pkg/pow2.py | S |
"""

BRIEF = """\
# Brief

```fact F1
$ git grep -c "def add" -- pkg/app.py
pkg/app.py:1
```

```fact SAFETY exit=1
$ git grep -n "keyring" -- pkg
```
"""


def set_setting(program_dir: Path, *lines: str) -> None:
    """Add settings to ship.toml, each replacing the line that already sets its key."""
    path = program_dir / "ship.toml"
    rows = path.read_text("utf-8").splitlines()
    for line in (x for x in lines if x.strip()):
        key = line.split("=", 1)[0].strip()
        rows = [r for r in rows if r.split("=", 1)[0].strip() != key] + [line]
    path.write_text("\n".join(rows) + "\n", "utf-8")


class RepoCase(unittest.TestCase):
    """Each test gets a fresh remote, clone, build branch `build/t`, and program folder. Its factory home
    is a temp folder: no test touches the real one."""

    build_branch = "build/t"

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        root = Path(self._tmp.name)
        self.root = root
        self.remote = root / "remote.git"
        sh(root, "git", "init", "-q", "--bare", "-b", "main", str(self.remote))
        self.repo = root / "repo"
        sh(root, "git", "clone", "-q", str(self.remote), str(self.repo))
        for key, value in (("user.name", "ship test"), ("user.email", "ship@test.invalid"),
                           ("core.autocrlf", "false"), ("commit.gpgsign", "false")):
            sh(self.repo, "git", "config", key, value)
        sh(self.repo, "git", "checkout", "-q", "-b", "main")
        write(self.repo / ".gitattributes", "* text=auto eol=lf\n")
        write(self.repo / "pkg" / "__init__.py", "")
        write(self.repo / "pkg" / "app.py", APP)
        write(self.repo / "pkg" / "tests" / "__init__.py", "")
        write(self.repo / "pkg" / "tests" / "test_app.py", TEST_APP)
        self.commit("initial")
        sh(self.repo, "git", "push", "-q", "-u", "origin", "main")
        sh(self.repo, "git", "push", "-q", "origin", f"main:refs/heads/{self.build_branch}")
        self.wt_root = root / "wt"
        self.wt_root.mkdir()
        self.program = Program(root / "program")
        write(self.program.slices_md, SLICES)
        for sid in ("s1", "s2", "s3", "s4"):
            write(self.program.brief(sid), BRIEF)
        write(self.program.checks_toml, textwrap.dedent(f"""\
            [[package]]
            root = "."
            test = [{PY!r}, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml={{junit}}", "{{tests}}"]
            """).replace("'", '"'))
        write(self.program.dir / "ship.toml", textwrap.dedent(f"""\
            [settings]
            gh = [{PY!r}, {str(FAKE_GH)!r}]
            heartbeat_interval_s = 1
            power_settle_s = 5
            keep_awake_poll_s = 1
            ci = "local"
            github_repo = "owner/qmx"
            factory_home = {str(root / "factory")!r}
            """).replace("'", '"'))
        init_state(self.program.dir, self.repo, self.build_branch, self.wt_root, "origin")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def commit(self, message: str, cwd: Path | None = None) -> str:
        cwd = cwd or self.repo
        sh(cwd, "git", "add", "-A")
        sh(cwd, "git", "commit", "-q", "-m", message)
        return sh(cwd, "git", "rev-parse", "HEAD")

    def use_slices(self, table: str, briefs: list[str]) -> None:
        """Replace SLICES.md before any dispatch and start state.json again from it."""
        write(self.program.slices_md, table)
        for sid in briefs:
            write(self.program.brief(sid), BRIEF)
        self.program.state.unlink()
        init_state(self.program.dir, self.repo, self.build_branch, self.wt_root, "origin")

    def setting(self, line: str) -> None:
        """Add a setting to ship.toml, or replace the line that already sets it."""
        set_setting(self.program.dir, line)

    def tip(self) -> str:
        return sh(self.repo, "git", "ls-remote", "origin", f"refs/heads/{self.build_branch}").split()[0]

    def make_ready(self, sid: str, files: dict[str, str]) -> str:
        """Dispatch `sid`, write `files` in its worktree, push, write evidence, and verify ready."""
        from ship.dispatch import dispatch
        from ship.settings import load_settings
        from ship.verify_ready import verify_ready

        settings = load_settings(self.program.dir)
        got = dispatch(self.program, sid, settings)
        wt = Path(got.worktree)
        for path, text in files.items():
            write(wt / path, text)
        sha = self.commit(f"{sid}: work", wt)
        sh(wt, "git", "push", "-q", "-u", "origin", got.branch)
        for name in settings.evidence_required:
            ask = st.load(self.program).slices[sid].ask or "S1"
            body = f"{name}\nTRACE: {sid} -> P1 -> {ask}\n" if name == "pr.md" else f"{name}\n"
            write(self.program.evidence(sid, got.attempt) / name, f"{body}END {sha} {got.dispatch_id}\n")
        ok, lines = verify_ready(self.program, sid, sha, settings)
        if not ok:
            raise AssertionError(lines)
        return sha


def sign_gates(program: Program) -> None:
    """Log every gate PROGRAM.yaml holds as `ship gate` would have (a test stands in for his word)."""
    from ship import program as prog

    program.gates_log.unlink(missing_ok=True)
    for name, value in prog.load(program).gates.items():
        if isinstance(value, dict):
            prog.log_gate(program, name, value)
