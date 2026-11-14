"""U29: slice kinds and the parent rule by kind, the probe, the walks by kind, and D-L27 (CI's fail-at-parent is a
NOTE for pin and refactor slices). Real git and real pytest on the fixture's package; `gh` and `claude` are fakes.

Chaos rows 24 (`Remove.test_remove_with_live_caller`), 25 (`Refactor.test_refactor_breaks_pin`) and X5
(`X5.test_a_removal_meets_a_new_caller`) live here; `test_chain_chaos.Named` names them."""

import datetime as dt
import json
import textwrap
import unittest

from ship import ci
from ship import state as st
from ship.plan import PlanError, parse_slices
from ship.settings import load_settings
from ship.slice_checks import slice_checks
from ship.state import Status
from ship.tests.fixture import BRIEF, RepoCase, sh, write
from ship.tests.test_ci import CiCase, job
from ship.tests.test_claims import TwoPrograms

OLD = "def legacy():\n    return 'legacy'\n"
TEST_OLD = "from pkg.old import legacy\n\n\ndef test_legacy():\n    assert legacy() == 'legacy'\n"
PIN_TEST = "from pkg.app import add\n\n\ndef test_add_pins_today():\n    assert add(2, 2) == 4\n"
VACUOUS_PIN = "from pkg.app import add\n\n\ndef test_add_runs():\n    add(2, 2)\n    assert True\n"
MUL = "def mul(a, b):\n    return a * b\n"
NEW_FN_PIN = "from pkg.mul import mul\n\n\ndef test_mul():\n    assert mul(2, 3) == 6\n"
CALLERS = textwrap.dedent("""\

    Chain: S1 -> F3

    Replaced by: nothing; `legacy` has no caller (finding F3)

    ```fact CALLERS exit=1
    $ git grep -n -w legacy -- . :(exclude)pkg/old.py :(exclude)pkg/tests/test_old.py
    ```
    """)


def table(rows) -> str:
    """rows: (id, kind, depends on, files)."""
    body = "".join(f"| {sid} | Slice {sid} | {kind} | {deps} | {files} | S |\n" for sid, kind, deps, files in rows)
    return "| id | name | kind | depends on | files | size |\n|---|---|---|---|---|---|\n" + body


class KindCase(RepoCase):
    def setUp(self):
        super().setUp()
        self.settings = load_settings(self.program.dir)
        self.on_build({"pkg/old.py": OLD, "pkg/tests/test_old.py": TEST_OLD}, "seed: legacy")

    def on_build(self, files, message):
        sh(self.repo, "git", "fetch", "-q", "origin")
        sh(self.repo, "git", "checkout", "-q", "-B", "seed", f"origin/{self.build_branch}")
        for path, text in files.items():
            write(self.repo / path, text)
        sha = self.commit(message)
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        return sha

    def slices(self, rows, briefs=None):
        self.use_slices(table(rows), [r[0] for r in rows])
        for sid, text in (briefs or {}).items():
            write(self.program.brief(sid), text)

    def land(self, sid, head):
        """As `ship land` would: the build branch moves to the slice head, and the slice is landed."""
        sh(self.repo, "git", "push", "-q", "origin", f"{head}:refs/heads/{self.build_branch}")
        with st.locked(self.program) as state:
            state.slices[sid].status = Status.CHECKED
            state.move(sid, Status.LANDED, "landed")
            state.slices[sid].landed_sha = head

    def check(self, sid):
        ok, lines = slice_checks(self.program, sid, self.settings)
        return ok, lines, {ln.split()[1]: ln for ln in lines if ln.split()[0] in ("PASS", "FAIL", "NOTRUN", "NOTE")}


class Plan(unittest.TestCase):
    def test_the_kind_column_defaults_to_feature_and_refuses_an_unknown_kind(self):
        got = parse_slices(table([("a", "pin", "-", "x.py"), ("b", "-", "-", "y.py"), ("c", "Refactor", "a", "x.py")]))
        self.assertEqual([s.kind for s in got], ["pin", "feature", "refactor"])
        self.assertEqual(parse_slices("| id | name | depends on | files | size |\n|---|---|---|---|---|\n"
                                      "| a | A | - | x.py | S |\n")[0].kind, "feature")
        with self.assertRaisesRegex(PlanError, "a has kind 'rewrite'"):
            parse_slices(table([("a", "rewrite", "-", "x.py")]))

    def test_an_old_state_file_without_kind_reads_as_feature(self):
        item = {"id": "a", "name": "A", "depends_on": [], "files": ["x.py"], "status": "pending"}
        state = st.State.from_json(json.dumps({"repo": ".", "build_branch": "b", "remote": "origin",
                                               "worktree_root": ".", "slices": {"a": item}, "schema": 1}))
        self.assertEqual(state.slices["a"].kind, "feature")


class Feature(KindCase):
    def test_a_feature_test_that_passes_at_the_parent_is_red(self):
        self.slices([("f1", "feature", "-", "pkg/tests/test_pin.py")])
        head = self.make_ready("f1", {"pkg/tests/test_pin.py": PIN_TEST})
        ok, _, by = self.check("f1")
        self.assertFalse(ok)
        self.assertEqual(by["fail-at-parent-root"],
                         f"FAIL fail-at-parent-root f1 {head[:8]} 1 of 1 new tests: "
                         ".::pkg.tests.test_pin::test_add_pins_today at parent: passed")


class Pin(KindCase):
    def test_a_pin_that_passes_at_the_parent_is_green_and_the_probe_shows_it_can_fail(self):
        self.slices([("p1", "pin", "-", "pkg/tests/test_pin.py")])
        head = self.make_ready("p1", {"pkg/tests/test_pin.py": PIN_TEST})
        ok, lines, by = self.check("p1")
        self.assertTrue(ok, lines)
        self.assertEqual(by["pin-root"], f"PASS pin-root p1 {head[:8]} 1 new tests pass at the parent and the head, "
                                         "and each fails when its subject returns None or a sentinel (probe "
                                         "probe-root.tsv)")
        self.assertNotIn("fail-at-parent-root", by)
        rows = (self.program.checks("p1", head) / "probe-root.tsv").read_text("utf-8").splitlines()
        self.assertEqual(rows[1].split("\t"), ["pkg/tests/test_pin.py::test_add_pins_today", "pkg.app:add",
                                               "passed", "failed", "-", "can-fail"])
        self.assertEqual(st.load(self.program).slices["p1"].status, Status.CHECKED)

    def test_a_pin_that_cannot_fail_is_red(self):
        self.slices([("p1", "pin", "-", "pkg/tests/test_pin.py")])
        head = self.make_ready("p1", {"pkg/tests/test_pin.py": VACUOUS_PIN})
        ok, _, by = self.check("p1")
        self.assertFalse(ok)
        self.assertEqual(by["pin-root"], f"FAIL pin-root p1 {head[:8]} 1 of 1 new tests: "
                                         "pkg/tests/test_pin.py::test_add_runs is cannot-fail under the probe "
                                         "(none=passed sentinel=passed)")

    def test_a_pin_of_code_the_slice_adds_is_red(self):
        self.slices([("p1", "pin", "-", "pkg/mul.py, pkg/tests/test_mul.py")])
        head = self.make_ready("p1", {"pkg/mul.py": MUL, "pkg/tests/test_mul.py": NEW_FN_PIN})
        ok, _, by = self.check("p1")
        self.assertFalse(ok)
        self.assertEqual(by["pin-root"], f"FAIL pin-root p1 {head[:8]} 1 of 1 new tests: "
                                         ".::pkg.tests.test_mul::test_mul at parent: not collected (a pin must "
                                         "describe today's behaviour)")

    def test_a_pin_with_no_new_test_is_red(self):
        self.slices([("p1", "pin", "-", "pkg/app.py")])
        head = self.make_ready("p1", {"pkg/app.py": "def add(a, b):\n    return b + a\n"})
        ok, _, by = self.check("p1")
        self.assertFalse(ok)
        self.assertEqual(by["pin"], f"FAIL pin p1 {head[:8]} a pin slice adds no new test case")


class Refactor(KindCase):
    def pinned(self):
        self.slices([("p1", "pin", "-", "pkg/tests/test_pin.py"), ("r1", "refactor", "p1", "pkg/app.py, pkg/tests")])
        self.land("p1", self.make_ready("p1", {"pkg/tests/test_pin.py": PIN_TEST}))

    def test_a_refactor_that_keeps_the_pin_green_is_green(self):
        self.pinned()
        head = self.make_ready("r1", {"pkg/app.py": "def add(a, b):\n    return sum((a, b))\n"})
        ok, lines, by = self.check("r1")
        self.assertTrue(ok, lines)
        self.assertEqual(by["pins"], f"PASS pins r1 {head[:8]} 1 tests of pins p1 pass at the head")
        self.assertEqual(by["deleted-tests"], f"PASS deleted-tests r1 {head[:8]} no test file deleted")

    def test_refactor_breaks_pin(self):
        """Chaos row 25: a pin landed; a refactor that changes the pinned output is red, the pin fails at the head."""
        self.pinned()
        head = self.make_ready("r1", {"pkg/app.py": "def add(a, b):\n    return a + b + 1\n"})
        ok, _, by = self.check("r1")
        self.assertFalse(ok)
        self.assertTrue(by["pins"].startswith(
            f"FAIL pins r1 {head[:8]} the pins it depends on do not all pass at the head: "
            ".::pkg.tests.test_pin::test_add_pins_today is assertion-failure"), by["pins"])
        self.assertEqual(st.load(self.program).slices["r1"].status, Status.RED)

    def test_a_refactor_that_deletes_a_pin_test_is_red(self):
        self.pinned()
        head = self.make_ready("r1", {"pkg/app.py": "def add(a, b):\n    return sum((a, b))\n",
                                      "pkg/tests/test_pin.py": None})
        ok, _, by = self.check("r1")
        self.assertFalse(ok)
        self.assertEqual(by["deleted-tests"], f"FAIL deleted-tests r1 {head[:8]} a refactor deletes no test file: "
                                              "pkg/tests/test_pin.py")
        self.assertIn("pkg/tests/test_pin.py is gone at the head", by["pins"])


class Remove(KindCase):
    def test_a_remove_with_its_subject_and_test_gone_is_green(self):
        self.slices([("rm1", "remove", "-", "pkg/old.py, pkg/tests/test_old.py")], {"rm1": BRIEF + CALLERS})
        head = self.make_ready("rm1", {"pkg/old.py": None, "pkg/tests/test_old.py": None})
        ok, lines, by = self.check("rm1")
        self.assertTrue(ok, lines)
        h8 = head[:8]
        self.assertEqual(by["callers"], f"PASS callers rm1 {h8} 1 CALLERS facts hold at the head")
        self.assertEqual(by["deleted-tests"], f"PASS deleted-tests rm1 {h8} pkg/tests/test_old.py (its subject "
                                              "pkg/old.py is deleted too)")
        self.assertEqual(by["replaced-by"], f"PASS replaced-by rm1 {h8} Replaced by: nothing; `legacy` has no caller "
                                            "(finding F3)")

    def test_remove_with_live_caller(self):
        """Chaos row 24: a remove slice whose symbol is still named in a fixture app.toml is red on the callers
        fact. (callers.py exiting 1 on the manifest is the factory's U27 fixture: g13, g21, g33, g36.)"""
        self.slices([("rm1", "remove", "-", "pkg/old.py, pkg/tests/test_old.py, pkg/app.toml")],
                    {"rm1": BRIEF + CALLERS})
        head = self.make_ready("rm1", {"pkg/old.py": None, "pkg/tests/test_old.py": None,
                                       "pkg/app.toml": '[handlers]\nstart = "legacy"\n'})
        ok, _, by = self.check("rm1")
        self.assertFalse(ok)
        self.assertEqual(by["callers"], f"FAIL callers rm1 {head[:8]} CALLERS differs at the head: something still "
                                        "names what the slice removes, see callers.log")
        log = (self.program.checks("rm1", head) / "callers.log").read_text("utf-8")
        self.assertIn('pkg/app.toml:2:start = "legacy"', log)

    def test_a_deleted_test_needs_its_subject_gone_or_a_probe_line_and_replaced_by_must_be_filled(self):
        brief = BRIEF + CALLERS.replace("Replaced by: nothing; `legacy` has no caller (finding F3)", "Replaced by:")
        self.slices([("rm1", "remove", "-", "pkg/tests/test_app.py")], {"rm1": brief})
        head = self.make_ready("rm1", {"pkg/tests/test_app.py": None})
        ok, _, by = self.check("rm1")
        self.assertFalse(ok)
        self.assertEqual(by["deleted-tests"], f"FAIL deleted-tests rm1 {head[:8]} deleted with no deleted subject "
                                              "and no `probe <path> cannot-fail` line in report.md: "
                                              "pkg/tests/test_app.py")
        self.assertEqual(by["replaced-by"], f"FAIL replaced-by rm1 {head[:8]} the brief's `Replaced by:` is missing "
                                            "or empty")
        report = self.program.evidence("rm1", 1) / "report.md"
        report.write_text(report.read_text("utf-8") + "probe pkg/tests/test_app.py cannot-fail\n", "utf-8")
        _, _, by = self.check("rm1")
        self.assertEqual(by["deleted-tests"], f"PASS deleted-tests rm1 {head[:8]} pkg/tests/test_app.py (probe: "
                                              "cannot-fail)")

    def test_a_remove_that_deletes_a_package_left_in_checks_toml_is_red(self):
        self.on_build({"legacy/legacy_pkg/__init__.py": OLD,
                       "legacy/tests/test_l.py": "from legacy_pkg import legacy\n\n\ndef test_l():\n"
                                                 "    assert legacy() == 'legacy'\n",
                       "checks.toml": '[[package]]\nroot = "."\n\n[[package]]\nroot = "legacy"\n'}, "seed: package")
        toml = self.program.checks_toml
        toml.write_text(toml.read_text("utf-8") + toml.read_text("utf-8").replace('root = "."', 'root = "legacy"'),
                        "utf-8")
        callers = CALLERS.replace("-w legacy -- . :(exclude)pkg/old.py :(exclude)pkg/tests/test_old.py",
                                  "-w legacy_pkg -- . :(exclude)legacy")
        self.slices([("rm1", "remove", "-", "legacy/**")], {"rm1": BRIEF + callers})
        head = self.make_ready("rm1", {"legacy/legacy_pkg/__init__.py": None, "legacy/tests/test_l.py": None})
        ok, _, by = self.check("rm1")
        self.assertFalse(ok)
        h8 = head[:8]
        self.assertEqual(by["removed-package-legacy"], f"FAIL removed-package-legacy rm1 {h8} checks.toml still names "
                                                       "the removed root legacy at the head")
        for check in ("lint", "types", "test", "quality-vulture", "quality-skylos"):
            self.assertEqual(by[f"{check}-legacy"], f"NOTRUN {check}-legacy rm1 {h8} removed-package")
        self.assertNotIn("test-root", by)


class Docs(KindCase):
    def test_a_docs_slice_changes_only_docs(self):
        self.slices([("d1", "docs", "-", "docs/x.md, pkg/app.py")])
        head = self.make_ready("d1", {"docs/x.md": "# X\n"})
        ok, lines, by = self.check("d1")
        self.assertTrue(ok, lines)
        self.assertEqual(by["docs-only"], f"PASS docs-only d1 {head[:8]} 1 files, all under docs/, "
                                          "contracts/CHANGELOG.md or *.md")

    def test_a_docs_slice_that_changes_code_is_red(self):
        self.slices([("d1", "docs", "-", "docs/x.md, pkg/app.py")])
        head = self.make_ready("d1", {"docs/x.md": "# X\n", "pkg/app.py": "# the adder\n" + "def add(a, b):\n"
                                      "    return a + b\n"})
        ok, _, by = self.check("d1")
        self.assertFalse(ok)
        self.assertEqual(by["docs-only"], f"FAIL docs-only d1 {head[:8]} a docs slice changes pkg/app.py")


class CiFailAtParent(CiCase):
    """D-L27: CI's slice-level fail-at-parent knows no kinds, so for pin and refactor slices it is a NOTE; every
    other CI job still counts, and a feature slice is blocked by it as before."""

    def run_with(self, sid, head, *red_jobs):
        jobs = [job("level"), job("tests-linux 1", "success", 2), job("fail-at-parent", "success", 3),
                job("summary", "success", 4)]
        for j in jobs:
            if j["name"] in red_jobs:
                j["conclusion"] = "failure"
        return self.put_run(headSha=head, headBranch=f"slice/{sid}", conclusion="failure",
                            displayTitle=f"slice slice/{sid}", jobs=jobs)

    def ready(self, kind):
        self.use_slices(table([("p1", kind, "-", "pkg/tests/test_pin.py")]), ["p1"])
        return self.make_ready("p1", {"pkg/tests/test_pin.py": PIN_TEST})

    def test_a_pin_slice_with_only_fail_at_parent_red_is_checked_with_a_note_and_lands(self):
        head = self.ready("pin")
        run_ = self.run_with("p1", head, "fail-at-parent")
        ok, lines = slice_checks(self.program, "p1", self.settings)
        self.assertTrue(ok, lines)
        self.assertIn(f"PASS linux p1 {head[:8]} slice run completed failure on {head[:8]}; NOTE CI's fail-at-parent "
                      f"job is red, not a block for a pin slice: the kit's parent rule judges it (D-L27) {run_['url']}",
                      lines)
        self.assertIn(f"NOTE ci-fail-at-parent p1 {head[:8]} CI's fail-at-parent job is red on this pin slice; the "
                      "kit's parent rule judges it (D-L27)", lines)
        state = st.load(self.program)
        sl = state.slices["p1"]
        self.assertEqual((sl.status, sl.ci["linux"]), (Status.CHECKED, "pass"))
        action, _, _ = ci.linux_gate(state, self.settings, sl, dt.datetime.now(dt.timezone.utc))
        self.assertEqual(action, "land")

    def test_every_other_ci_job_still_counts_and_a_feature_is_still_blocked(self):
        head = self.ready("pin")
        self.run_with("p1", head, "fail-at-parent", "tests-linux 1")
        state = st.load(self.program)
        self.assertEqual(ci.slice_linux(state, self.settings, state.slices["p1"])[0], "FAIL")
        for kind, want in (("refactor", "PASS"), ("feature", "FAIL"), ("remove", "FAIL"), ("docs", "FAIL")):
            with st.locked(self.program) as fresh:
                fresh.slices["p1"].kind = kind
            self.change_run(self.runs()["runs"][0]["databaseId"], jobs=[
                job("level"), job("tests-linux 1", "success", 2), job("fail-at-parent", "failure", 3)])
            state = st.load(self.program)
            self.assertEqual(ci.slice_linux(state, self.settings, state.slices["p1"])[0], want, kind)


class Walks(KindCase):
    """The walks by kind: trace writes their inputs into MAP.md, review starts their readers."""

    def test_trace_writes_equivalence_callers_and_findings_and_review_starts_their_readers(self):
        from ship.review import Checkpoint
        from ship.stop_trace import trace

        rows = [("p1", "pin", "-", "pkg/tests/test_pin.py"), ("r1", "refactor", "p1", "pkg/app.py"),
                ("rm1", "remove", "-", "pkg/old.py, pkg/tests/test_old.py")]
        self.slices(rows, {"rm1": BRIEF + CALLERS})
        base = self.tip()
        self.land("p1", self.make_ready("p1", {"pkg/tests/test_pin.py": PIN_TEST}))
        self.land("r1", self.make_ready("r1", {"pkg/app.py": "def add(a, b):\n    return sum((a, b))\n"}))
        self.land("rm1", self.make_ready("rm1", {"pkg/old.py": None, "pkg/tests/test_old.py": None}))
        tip = self.tip()
        write(self.program.dir / "FINDINGS.tsv", "id\tgrade\tkind\tpart\tlocation\twhat\tproof\n"
                                                 "F3\tmust\tremove\tcore\tpkg/old.py\tlegacy is dead\t"
                                                 "git grep -n legacy -- pkg\n")
        ok, lines = trace(self.program, "A", self.settings, base, tip)
        self.assertTrue(ok, lines)
        text = (self.program.stop_review("A") / "MAP.md").read_text("utf-8")
        self.assertIn("## Equivalence\n\nPins: p1. Refactors: r1.", text)
        self.assertIn("- `.::pkg.tests.test_pin::test_add_pins_today`: from passed, tip passed", text)
        self.assertIn("### rm1 (Replaced by: nothing; `legacy` has no caller (finding F3))", text)
        self.assertIn("- path `pkg/old.py` (module `pkg.old`): 0 hits", text)
        self.assertIn("- name `legacy`: 0 hits", text)
        self.assertIn("- F3 (rm1): legacy is dead\n  - proof: `git grep -n legacy -- pkg`", text)
        readers = {r.name: r.slices for r in Checkpoint(self.program, "A", self.settings, round=1).readers()}
        self.assertEqual({k: readers.get(k) for k in ("equivalence", "callers", "findings")},
                         {"equivalence": ("p1", "r1"), "callers": ("rm1",), "findings": ("rm1",)})

    def test_a_pin_test_red_at_the_tip_is_a_trace_fail(self):
        from ship.stop_trace import trace

        self.slices([("p1", "pin", "-", "pkg/tests/test_pin.py")])
        base = self.tip()
        self.land("p1", self.make_ready("p1", {"pkg/tests/test_pin.py": PIN_TEST}))
        tip = self.on_build({"pkg/app.py": "def add(a, b):\n    return 0\n"}, "p1: a later break")
        ok, lines = trace(self.program, "A", self.settings, base, tip)
        self.assertFalse(ok)
        self.assertIn(f"FAIL equivalence pin test .::pkg.tests.test_pin::test_add_pins_today is assertion-failure at "
                      f"{tip[:10]}", lines)


class X5(TwoPrograms):
    def test_a_removal_meets_a_new_caller(self):
        """X5: an audit's remove slice and a feature slice both name one file. The remove slice waits on the
        feature's claim; the feature merges with a call to the symbol being removed; at dispatch the remove's
        CALLERS fact runs again and fails: it parks brief-mismatch with a WAITS line and a backlog row pointing
        back at its finding, and nothing is deleted."""
        write(self.repo / "pkg" / "old.py", OLD)
        self.commit("seed: legacy")
        sh(self.repo, "git", "push", "-q", "origin", "main", "main:refs/heads/build/t", "main:refs/heads/build/u")
        self.use(self.p1, "build/t", [("x1", "pkg/app.py")])
        write(self.p2.slices_md, table([("r1", "remove", "-", "pkg/old.py, pkg/app.py")]))
        write(self.p2.brief("r1"), BRIEF + CALLERS)
        self.p2.state.unlink(missing_ok=True)
        from ship.plan import init_state

        init_state(self.p2.dir, self.repo, "build/u", self.wt_root, "origin")
        self.assertEqual(self.ship(self.p1, "claims", "claim"), 0, self.out)
        self.assertEqual(self.ship(self.p2, "run", "--once"), 0, self.out)
        self.assertIn("WAIT r1 blocked-by claim p1", self.out)
        self.assertEqual(st.load(self.p2).slices["r1"].status, Status.PENDING)

        sh(self.repo, "git", "fetch", "-q", "origin")
        sh(self.repo, "git", "checkout", "-q", "-B", "feature", "origin/build/u")  # the feature merged, with a call
        write(self.repo / "pkg" / "app.py", "from pkg.old import legacy\n\n\ndef add(a, b):\n    return a + b\n\n\n"
                                            "def start():\n    return legacy()\n")
        self.commit("x1: start calls legacy")
        sh(self.repo, "git", "push", "-q", "origin", "HEAD:refs/heads/build/u")
        self.assertEqual(self.ship(self.p1, "claims", "release"), 0, self.out)
        self.ship(self.p2, "run", "--once")
        self.assertIn("PARK r1: brief-mismatch ['CALLERS']", self.out)
        sl = st.load(self.p2).slices["r1"]
        self.assertEqual((sl.status, sl.reason.split(":")[0]), (Status.PARKED, "brief-mismatch"))
        waits = self.p2.waits.read_text("utf-8")
        self.assertIn("- [ ] r1 parked: brief-mismatch ['CALLERS']", waits)
        rows = (self.p2.notes_dir / "BACKLOG-ROWS.tsv").read_text("utf-8").splitlines()
        self.assertEqual(rows[0], "source\tdoor\twhat\twhere")
        source, door, what, where = rows[1].split("\t")
        self.assertEqual((source, door, where), ("parked", "triage", str(self.p2.dir)))
        self.assertIn("r1 (remove, finding F3): its CALLERS fact fails at", what)
        sh(self.repo, "git", "fetch", "-q", "origin")
        self.assertEqual(sh(self.repo, "git", "show", "origin/build/u:pkg/old.py"), OLD.strip(), "nothing is deleted")
        self.assertEqual(sh(self.repo, "git", "ls-remote", "origin", "refs/heads/slice/r1"), "")


if __name__ == "__main__":
    unittest.main()
