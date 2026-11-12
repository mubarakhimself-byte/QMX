import json
import unittest

from ship import state as st
from ship.dispatch import dispatch
from ship.settings import load_settings
from ship.state import Status
from ship.tests.fixture import RepoCase, sh, write
from ship.verify_ready import verify_ready

MUL = "def mul(a, b):\n    return a * b\n"
TEST_MUL = "def test_mul():\n    from pkg.mul import mul\n    assert mul(2, 3) == 6\n"


class VerifyReady(RepoCase):
    def setUp(self):
        super().setUp()
        self.settings = load_settings(self.program.dir)
        self.d = dispatch(self.program, "s1", self.settings)
        self.wt = self.wt_root / "slice-s1"

    def build(self, extra=None, push=True, end=True):
        write(self.wt / "pkg" / "mul.py", MUL)
        write(self.wt / "pkg" / "tests" / "test_mul.py", TEST_MUL)
        for path, text in (extra or {}).items():
            write(self.wt / path, text)
        sha = self.commit("s1: mul", self.wt)
        if push:
            sh(self.wt, "git", "push", "-q", "-u", "origin", "slice/s1")
        evidence = self.program.evidence("s1", 1)
        for name in ("how.md", "red.log", "report.md"):
            tail = f"END {sha} {self.d.dispatch_id}\n" if end else ""
            write(evidence / name, f"# {name}\nbody\n{tail}")
        return sha

    def prs(self):
        path = self.repo / ".git" / "fake-gh.json"
        return json.loads(path.read_text("utf-8")) if path.exists() else []

    def test_ready_opens_pr_against_build_branch(self):
        sha = self.build()
        ok, lines = verify_ready(self.program, "s1", sha, self.settings)
        self.assertTrue(ok, lines)
        (pr,) = self.prs()
        self.assertEqual((pr["baseRefName"], pr["head"], pr["title"]), ("build/t", "slice/s1", "s1: Multiply"))
        self.assertEqual(pr["body"], "# report.md\nbody\n")
        sl = st.load(self.program).slices["s1"]
        self.assertEqual((sl.status, sl.head, sl.pr), (Status.READY, sha, "https://github.test/pr/1"))

    def test_unpushed_sha_is_blocked(self):
        sha = self.build(push=False)
        ok, lines = verify_ready(self.program, "s1", sha, self.settings)
        self.assertFalse(ok)
        self.assertEqual(lines, [f"remote slice/s1 is None, the builder reported {sha}"])
        self.assertEqual(st.load(self.program).slices["s1"].status, Status.RED)
        self.assertEqual(self.prs(), [])

    def test_half_written_evidence_and_out_of_brief_files_are_blocked(self):
        sha = self.build(extra={"pkg/app.py": "changed = 1\n"}, end=False)
        ok, lines = verify_ready(self.program, "s1", sha, self.settings)
        self.assertFalse(ok)
        self.assertEqual(lines, [
            "evidence how.md: last line is 'body', want " + repr(f"END {sha} {self.d.dispatch_id}"),
            "evidence red.log: last line is 'body', want " + repr(f"END {sha} {self.d.dispatch_id}"),
            "evidence report.md: last line is 'body', want " + repr(f"END {sha} {self.d.dispatch_id}"),
            "files outside the brief: ['pkg/app.py']",
        ])


if __name__ == "__main__":
    unittest.main()
