"""Real git repos in a temp folder: a bare remote, a clone, a build branch, and a program folder."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

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


class RepoCase(unittest.TestCase):
    """Each test gets a fresh remote, clone, build branch `build/t`, and program folder."""

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
            """).replace("'", '"'))
        init_state(self.program.dir, self.repo, self.build_branch, self.wt_root, "origin")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def commit(self, message: str, cwd: Path | None = None) -> str:
        cwd = cwd or self.repo
        sh(cwd, "git", "add", "-A")
        sh(cwd, "git", "commit", "-q", "-m", message)
        return sh(cwd, "git", "rev-parse", "HEAD")

    def tip(self) -> str:
        return sh(self.repo, "git", "ls-remote", "origin", f"refs/heads/{self.build_branch}").split()[0]
