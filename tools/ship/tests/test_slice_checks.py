import unittest

from ship import state as st
from ship.settings import load_settings
from ship.slice_checks import slice_checks
from ship.state import Status
from ship.tests.fixture import RepoCase

MUL = "def mul(a, b):\n    return a * b\n"
REAL_TEST = (
    "import pkgutil\n\nimport pkg\n\n\n"
    "def test_mul():\n"
    "    assert 'mul' in [m.name for m in pkgutil.iter_modules(pkg.__path__)]\n"
    "    from pkg.mul import mul\n"
    "    assert mul(2, 3) == 6\n"
)
VACUOUS_TEST = "from pkg.mul import mul\n\n\ndef test_mul():\n    assert mul(2, 3) == 6\n"


class SliceChecks(RepoCase):
    def setUp(self):
        super().setUp()
        self.settings = load_settings(self.program.dir)

    def summary(self, head):
        return (self.program.checks("s1", head) / "summary.txt").read_text("utf-8").splitlines()

    def test_real_new_test_passes_every_check(self):
        head = self.make_ready("s1", {"pkg/mul.py": MUL, "pkg/tests/test_mul.py": REAL_TEST})
        ok, lines = slice_checks(self.program, "s1", self.settings)
        h8 = head[:8]
        self.assertTrue(ok, lines)
        self.assertEqual(self.summary(head), [
            f"PASS diff-check s1 {h8}",
            f"PASS case-collision s1 {h8}",
            f"NOTRUN lint-root s1 {h8} no command in checks.toml",
            f"NOTRUN types-root s1 {h8} no command in checks.toml",
            f"PASS test-root s1 {h8} rc=0 red=0",
            f"PASS fail-at-parent-root s1 {h8} 1 new tests fail at the parent on an assertion and pass at the head",
            *[ln for ln in self.summary(head) if ln.startswith("NOTRUN linux") or ln.startswith("NOTRUN windows")],
            f"NOTRUN mutation s1 {h8} mutation testing is not built",
        ])
        self.assertEqual(st.load(self.program).slices["s1"].status, Status.CHECKED)
        log = (self.program.checks("s1", head) / "fail-at-parent-root.log").read_text("utf-8")
        self.assertIn(".::pkg.tests.test_mul::test_mul parent=assertion-failure head=passed", log)

    def test_import_error_at_parent_does_not_count(self):
        head = self.make_ready("s1", {"pkg/mul.py": MUL, "pkg/tests/test_mul.py": VACUOUS_TEST})
        ok, lines = slice_checks(self.program, "s1", self.settings)
        self.assertFalse(ok)
        fail = [ln for ln in lines if ln.startswith("FAIL")]
        self.assertEqual(fail, [
            f"FAIL fail-at-parent-root s1 {head[:8]} 1 of 1 new tests: .::pkg.tests.test_mul::test_mul at parent: "
            "not collected (import or collection error)"])
        self.assertEqual(st.load(self.program).slices["s1"].status, Status.RED)

    def test_red_test_and_trailing_whitespace_fail(self):
        broken = REAL_TEST.replace("== 6", "== 7")
        head = self.make_ready("s1", {"pkg/mul.py": MUL + "x = 1   \n", "pkg/tests/test_mul.py": broken})
        ok, lines = slice_checks(self.program, "s1", self.settings)
        self.assertFalse(ok)
        names = [ln.split()[1] for ln in lines if ln.startswith("FAIL")]
        self.assertEqual(names, ["diff-check", "test-root", "fail-at-parent-root"])
        self.assertIn("at head: assertion-failure", [ln for ln in lines if "fail-at-parent" in ln][0])
        self.assertIn("trailing whitespace", (self.program.checks("s1", head) / "diff-check.log").read_text("utf-8"))


if __name__ == "__main__":
    unittest.main()
