"""The K4a fix round (BUILD-LOG D-L25): the kit and qmx-ci give one verdict on the same input; the hook keeps
generator paths, the desk's answers, Python files and other roles' scripts away from workers; HOLD stops every
new start and still reads what runs; the power watch never takes his HOLD; and the checker's mutants die.
Fakes stand at the subprocess boundary; qmx-ci's own code is `repo_ci/` (origin/ci/c2 812b87c98, byte for byte)."""

import json
import os
import shutil
import subprocess
import tempfile
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

from ship import quality as q
from ship import state as st
from ship.layout import Program
from ship.settings import Settings, load_settings
from ship.state import Status
from ship.suite import Baseline, Outcome, Package, canon, this_system
from ship.suite import TestRun as KitRun
from ship.tests.fixture import PY, RepoCase, sh, write
from ship.tests.test_chain import ChainCase
from ship.tests.test_review import NOTES_DONE, ReviewCase
from ship.tests.test_run import RunCase
from ship.wrapper import RunResult

HERE = Path(__file__).resolve().parent
REPO_CI = HERE / "repo_ci"  # qmx-ci's tools/ci at origin/ci/c2 812b87c98, byte for byte
FAKE = HERE / "fake_tools.py"


def plant_ci(folder: Path) -> None:
    for path in REPO_CI.glob("*.py"):
        write(folder / "tools" / "ci" / path.name, path.read_text("utf-8"))


class CiSide:
    """qmx-ci's own decision functions (`repo_ci/qci.py`) on the test's input: the globals that reach the host
    (OUT, BASELINES, head, tree_of, level) point at a temp folder; nothing else of CI's is replaced."""

    def __init__(self, root: Path, baselines: dict[str, str]):
        self.ci = q.load_ci(REPO_CI)
        self.root = root
        for tool, text in baselines.items():
            write(root / "ci" / "baselines" / f"{tool}.txt", text)
        (root / "ci-out" / "junit").mkdir(parents=True, exist_ok=True)

    def __enter__(self):
        ci = self.ci
        self.patches = [mock.patch.object(ci, "OUT", self.root / "ci-out"),
                        mock.patch.object(ci, "BASELINES", self.root / "ci" / "baselines"),
                        mock.patch.object(ci, "head", lambda: "a" * 40),
                        mock.patch.object(ci, "tree_of", lambda at: "b" * 40),
                        mock.patch.object(ci, "level", lambda: ci.Level.SLICE)]
        for patch in self.patches:
            patch.start()
        return ci

    def __exit__(self, *exc):
        for patch in reversed(self.patches):
            patch.stop()


class CiAgreement(unittest.TestCase):
    """D-L25: one input, the kit's verdict and qmx-ci's own; they must agree for Skylos, Vulture, types and flaky."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="k4a-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.checkout = self.tmp / "co"
        plant_ci(self.checkout)
        self.program = Program(self.tmp / "prog")
        self.program.dir.mkdir()
        self.settings = Settings()
        self.n = 0

    def out(self) -> Path:
        self.n += 1
        folder = self.tmp / f"out-{self.n}"
        folder.mkdir()
        return folder

    # -- Skylos --

    def kit_skylos(self, report: dict, baseline: list[str], files: list[str]) -> tuple[str, str]:
        write(self.checkout / "ci" / "baselines" / "skylos.txt", "# taken\n" + "".join(f"{k}\n" for k in baseline))
        write(self.checkout / "fake-skylos.json", json.dumps(report))
        package = Package(".", skylos=((PY, str(FAKE), "skylos"),))
        return q.check_package("skylos", package, self.checkout, None, files, self.out(), "t", self.settings,
                               self.program, q.RepoRatchet.at(self.checkout))

    def ci_skylos(self, report: dict, baseline: list[str], files: list[str]) -> int:
        side = CiSide(self.tmp / f"ci-{self.n}", {"skylos": "# taken\n" + "".join(f"{k}\n" for k in baseline)})
        with side as ci:
            path = write(side.root / "skylos.json", json.dumps(report))
            return ci.ratchet_verdict("skylos", ci.skylos_findings(path), files).rc

    def test_skylos_blocks_exactly_where_ci_blocks(self):
        def item(name, severity="low", rule=None, file="pkg/a.py"):
            return {"file": file, "name": name, "line": 3, "severity": severity, **({"rule_id": rule} if rule else {})}

        cases = {
            "the checker's agree.py": ({"unused_functions": [item("f")],
                                        "quality": [item("complex", "medium", "SKY-Q301")]}, [], "NOTE"),
            "danger, low": ({"danger": [item("eval", rule="SKY-D201")]}, [], "FAIL"),
            "reliability, low": ({"reliability": [item("bare except", rule="SKY-R1")]}, [], "FAIL"),
            "custom rule, medium": ({"custom_rules": [item("no print", "medium", "C1")]}, [], "FAIL"),
            "quality, high": ({"quality": [item("deep", "high", "SKY-Q1")]}, [], "NOTE"),
            "unused import, critical": ({"unused_imports": [item("os", "critical")]}, [], "NOTE"),
            "circular, high": ({"circular_dependencies": [item("a<->b", "high")]}, [], "NOTE"),
            "a new category, high": ({"ai_defects": [item("hallucinated api", "high", "SKY-A1")]}, [], "FAIL"),
            "secrets the baseline holds": ({"secrets": [item("aws key", rule="SKY-S1")]},
                                           ["pkg/a.py|secrets:SKY-S1|aws key"], "PASS"),
            "danger outside the slice": ({"danger": [item("eval", rule="SKY-D201", file="pkg/b.py")]}, [], "PASS"),
            "nothing": ({}, [], "PASS"),
        }
        for name, (report, baseline, want) in cases.items():
            with self.subTest(name):
                kit, detail = self.kit_skylos(report, baseline, ["pkg/a.py"])
                ci_rc = self.ci_skylos(report, baseline, ["pkg/a.py"])
                self.assertEqual(kit == "FAIL", ci_rc == 1, f"kit {kit} ({detail}), CI rc {ci_rc}")
                self.assertEqual(kit, want, detail)

    def test_skylos_without_cis_rules_in_the_checkout_fails_and_says_why(self):
        (self.checkout / "tools" / "ci" / "qci.py").unlink()
        verdict, detail = self.kit_skylos({"danger": []}, [], ["pkg/a.py"])
        self.assertEqual(verdict, "FAIL")
        self.assertIn("qci.py is missing: CI's own rules cannot be read there", detail)

    # -- Vulture --

    def vulture_both(self, sources: dict[str, str], baseline: list[str], files: list[str]) -> tuple[str, int]:
        for path, text in sources.items():
            write(self.checkout / path, text)
        text = "# taken\n" + "".join(f"{k}\n" for k in baseline)
        write(self.checkout / "ci" / "baselines" / "vulture.txt", text)
        package = Package(".", vulture=((PY, str(FAKE), "vulture"),))
        kit, _ = q.check_package("vulture", package, self.checkout, None, files, self.out(), "t", self.settings,
                                 self.program, q.RepoRatchet.at(self.checkout))
        raw = subprocess.run([PY, str(FAKE), "vulture"], cwd=self.checkout, capture_output=True, text=True).stdout

        def run(argv, cwd, stdout_to=None, **kw):
            Path(stdout_to).write_text(raw, "utf-8")
            return 3 if raw.strip() else 0

        side = CiSide(self.tmp / f"ci-v{self.n}", {"vulture": text})
        with side as ci, mock.patch.object(ci, "run", run):
            rc = ci.ratchet_verdict("vulture", ci.vulture_findings(), files, covered="all").rc
        for path in sources:
            (self.checkout / path).unlink()
        return kit, rc

    def test_vulture_blocks_exactly_where_ci_blocks(self):
        two = {"pkg/a.py": "def unused_x():\n    return 1\n", "pkg/b.py": "def unused_y():\n    return 2\n"}
        cases = {
            "new in the slice": (two, [], ["pkg/a.py"], "FAIL"),
            "known to the baseline": (two, ["pkg/a.py|vulture|unused function 'unused_x'"], ["pkg/a.py"], "PASS"),
            "outside the slice": (two, [], ["pkg/c.py"], "PASS"),
            "a second copy of a known one": ({"pkg/a.py": "def unused_x():\n    return 1\n\n\ndef unused_x():\n"
                                                          "    return 2\n"},
                                             ["pkg/a.py|vulture|unused function 'unused_x'"], ["pkg/a.py"], "FAIL"),
        }
        for name, (sources, baseline, files, want) in cases.items():
            with self.subTest(name):
                kit, rc = self.vulture_both(sources, baseline, files)
                self.assertEqual(kit == "FAIL", rc == 1, f"kit {kit}, CI rc {rc}")
                self.assertEqual(kit, want)

    def test_an_unreadable_file_makes_both_vulture_scans_incomplete(self):
        line = "pkg/a.py:1: invalid syntax at 'def'\n"
        with self.assertRaises(ValueError):
            q.parse("vulture", line, self.checkout, Package("."))
        side = CiSide(self.tmp / "ci-bad", {"vulture": "# taken\n"})
        with side as ci, mock.patch.object(ci, "run", lambda argv, cwd, stdout_to=None, **kw:
                                           Path(stdout_to).write_text(line, "utf-8") and 3):
            with self.assertRaises(ci.CiError):
                ci.vulture_findings()

    # -- types --

    def test_types_block_exactly_where_ci_blocks(self):
        a = (self.checkout / "pkg" / "a.py").as_posix()
        b = (self.checkout / "pkg" / "b.py").as_posix()

        def diag(file, line, message, severity="error", rule="reportCallIssue"):
            return {"file": file, "severity": severity, "rule": rule, "message": message,
                    "range": {"start": {"line": line, "character": 0}}}

        known = "pkg/a.py|reportCallIssue|Expected # arguments"
        cases = {
            "new in the slice": ([diag(a, 4, "Expected 2 arguments")], [], "FAIL"),
            "known to the baseline": ([diag(a, 9, "Expected 3 arguments")], [known], "PASS"),
            "outside the slice": ([diag(b, 1, "Expected 2 arguments")], [], "PASS"),
            "a second copy of a known one": ([diag(a, 4, "Expected 2 arguments"), diag(a, 8, "Expected 5 arguments")],
                                             [known], "FAIL"),
            "a warning only": ([diag(a, 4, "Unused", "warning")], [], "PASS"),
        }
        for name, (diags, baseline, want) in cases.items():
            with self.subTest(name):
                text = json.dumps({"generalDiagnostics": diags})
                body = "# taken\n" + "".join(f"{k}\n" for k in baseline)
                write(self.checkout / "ci" / "baselines" / "pyright.txt", body)
                out = self.out()
                log = write(out / "types.log", "node is ready\n" + text)
                kit, detail = q.types_ratchet(Package("."), self.checkout, ["pkg/a.py"], RunResult(1, False, 1.0, log),
                                              q.RepoRatchet.at(self.checkout), out)
                side = CiSide(self.tmp / f"ci-t{self.n}", {"pyright": body})
                with side as ci:
                    rc = ci.types_verdict(ci.pyright_findings(ci.pyright_report(text), root=self.checkout), ["pkg/a.py"])
                self.assertEqual(kit == "FAIL", rc == 1, f"kit {kit} ({detail}), CI rc {rc}")
                self.assertEqual(kit, want, detail)

    # -- flaky --

    def test_flaky_follows_ci_rerun_once_excused_only_when_listed_untouched_and_green_again(self):
        system = this_system()
        test = "pkg.tests.test_x::test_shaky"
        ci_key = f"{system}|pkg|{test}"
        touched_module, other = ["pkg/tests/test_x.py"], ["pkg/app.py"]
        red, passed = "assertion", "passed"
        cases = {
            # name: (first, again, touched, known-reds, flaky list, blocks)
            "green again, listed, untouched": (red, passed, other, [], [ci_key], False),
            "green again, not listed": (red, passed, other, [], [], True),
            "green again, listed, but its module touched": (red, passed, touched_module, [], [ci_key], True),
            "red again, listed as flaky only": (red, red, other, [], [ci_key], True),
            "red again, a known red": (red, red, other, [ci_key], [], False),
            "green again, a known red, not listed flaky": (red, passed, other, [ci_key], [], True),
            "error then green, listed": ("error", passed, other, [], [ci_key], False),
            "touched module, known red, red again": (red, red, touched_module, [ci_key], [ci_key], False),
            "passed first": (passed, "", other, [], [], False),
        }
        kit_outcome = {"assertion": Outcome.ASSERTION, "error": Outcome.ERROR, "passed": Outcome.PASSED}
        for name, (first, again, touched, known, flaky, blocks) in cases.items():
            with self.subTest(name):
                side = CiSide(self.tmp / f"ci-f{self.n}", {"known-reds": "".join(f"{k}\n" for k in known),
                                                           "flaky": "".join(f"{k}\n" for k in flaky)})
                self.n += 1
                with side as ci:
                    unit = ci.ci_units.Unit("pkg", ".", "pkg", ())
                    reds, flakes = ci.split_flaky(system, unit, {test: first}, {test: again} if again else {}, touched)
                    rc = ci.tests_verdict("x", reds, [], flakes)
                local = f"pkg::{test}"
                run = KitRun(RunResult(1, False, 1.0, self.tmp / "log"), True, {local: kit_outcome[first]},
                              {local: kit_outcome[again]} if again else {})
                baseline = Baseline(frozenset(canon(k) for k in known), frozenset(canon(k) for k in flaky), "x")
                judged = baseline.judge([run], touched)
                self.assertEqual(bool(judged.blocking), rc == 1, f"kit {judged}, CI rc {rc}")
                self.assertEqual(bool(judged.blocking), blocks)


class FlakyInChecks(RepoCase):
    """The flaky rule end to end: slice_checks reruns a red once, reads the lists at the parent, and land at the
    batch's base."""

    SHAKY = ("import pathlib\n\n\ndef test_shaky():\n"
             "    mark = pathlib.Path({mark})\n"
             "    if mark.exists():\n        mark.unlink()\n        return\n"
             "    mark.write_text('x')\n    assert False, 'first run'\n")

    def shaky(self) -> str:
        """A test that fails, then passes when run again. The wrapper gives each run its own temp folder, so the
        mark lives in the test's own root."""
        return self.SHAKY.replace("{mark}", repr(str(self.root / f"shaky-{time.monotonic_ns()}.mark")))

    def on_build(self, files: dict[str, str]) -> str:
        sh(self.repo, "git", "checkout", "-q", "-B", "b", f"origin/{self.build_branch}")
        for path, text in files.items():
            write(self.repo / path, text)
        sha = self.commit("on build")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        return sha

    def test_a_listed_flaky_test_in_an_untouched_module_passes_slice_checks_and_land(self):
        from ship.land import land
        from ship.slice_checks import slice_checks

        key = f"{this_system()}|.|pkg.tests.test_shaky::test_shaky"
        self.on_build({"pkg/tests/test_shaky.py": self.shaky(), "ci/baselines/flaky.txt": f"{key}\n"})
        settings = load_settings(self.program.dir)
        head = self.make_ready("s1", {"pkg/mul.py": "def mul(a, b):\n    return a * b\n"})
        ok, lines = slice_checks(self.program, "s1", settings)
        test_line = next(x for x in lines if x.startswith(("PASS test-root", "FAIL test-root")))
        self.assertTrue(test_line.startswith(f"PASS test-root s1 {head[:8]}"), test_line)
        self.assertIn("flaky=1", test_line)
        self.assertTrue((self.program.checks("s1", head) / "test-root-rerun.log").exists(), "the red ran once more")
        ok, lines = land(self.program, ["s1"], settings)
        self.assertTrue(ok, lines)

    def test_a_flaky_test_not_listed_blocks_and_a_listing_added_by_the_slice_excuses_nothing(self):
        from ship.slice_checks import slice_checks

        key = f"{this_system()}|.|pkg.tests.test_shaky::test_shaky"
        self.on_build({"pkg/tests/test_shaky.py": self.shaky()})
        settings = load_settings(self.program.dir)
        with st.locked(self.program) as state:
            state.slices["s1"].files.append("ci/baselines/flaky.txt")
        head = self.make_ready("s1", {"pkg/mul.py": "def mul(a, b):\n    return a * b\n",
                                      "ci/baselines/flaky.txt": f"{key}\n"})
        ok, lines = slice_checks(self.program, "s1", settings)
        self.assertFalse(ok)
        test_line = next(x for x in lines if x.startswith("FAIL test-root"))
        self.assertIn(f"blocking: .::pkg.tests.test_shaky::test_shaky", test_line,
                      "flaky.txt is read at the parent, so the slice's own listing does not count")


# ---- the hook ---------------------------------------------------------------------------------------------


class HookRules(RepoCase):
    """Generator paths, the desk's folder, Python files and per-role factory scripts (D-L25)."""

    def setUp(self):
        super().setUp()
        from ship.dispatch import dispatch

        self.factory = self.root / "factory"
        self.d = self.program.dir
        self.notes = self.program.stop_review("A") / "chain.md"
        self.env = {
            "builder": {}, "fixer": {},
            "reader": {"SHIP_NOTES": str(self.notes), "SHIP_STOP": "A"},
            "fault-reader": {"SHIP_NOTES": str(self.notes), "SHIP_STOP": "A"},
            "verdict": {"SHIP_STOP": "A"}, "grounding": {}, "plan-review": {}, "planner-fix": {},
            "later-handoff": {}, "sweep-handoff": {}, "challenger": {}, "answer-linker": {}, "audit-judge": {},
            "audit-intent": {}, "audit-reader": {"SHIP_PART": "p1"}, "audit-screen": {},
            "docs": {"SHIP_WORKTREE": str(self.root / "docs-wt"), "SHIP_BRANCH": "docs/x"},
        }
        self.setting(f"factory_home = {json.dumps(str(self.factory))}")
        got = dispatch(self.program, "s1", load_settings(self.program.dir))
        self.wt = Path(got.worktree)
        self.core = self.factory / "skills" / "factory-core" / "scripts"
        self.audit = self.factory / "skills" / "audit-area" / "scripts"

    def hook(self, role, tool, cwd=None, **tool_input):
        from ship import hook

        full = {k: v for k, v in os.environ.items() if not k.startswith("SHIP_")}
        full.update(SHIP_ROLE=role, **self.env.get(role, {}))
        event = {"tool_name": tool, "tool_input": tool_input, "cwd": str(cwd or self.root)}
        with mock.patch.dict(os.environ, full, clear=True):
            return hook.decide(self.program, event)

    def bash(self, role, command, cwd=None):
        return self.hook(role, "Bash", cwd=cwd, command=command)

    def test_no_role_writes_ci_baselines_or_contracts_in_a_worktree(self):
        for rel in ("ci/baselines/vulture.txt", "ci/baselines/flaky.txt", "contracts/openapi.json"):
            why = self.hook("builder", "Write", file_path=str(self.wt / rel), content="x")
            self.assertIsNotNone(why, rel)
            self.assertIn("only through the kit's generators", why)
        self.assertIsNone(self.hook("builder", "Write", file_path=str(self.wt / "pkg" / "a.py"), content="x"))
        self.assertIsNone(self.hook("builder", "Write", file_path=str(self.wt / "ci" / "notes.md"), content="x"))
        for command in ("pytest --version > ci/baselines/flaky.txt", "pytest --version | tee contracts/x.json",
                        "git rm -q ci/baselines/vulture.txt", "git checkout HEAD~1 -- contracts/openapi.json",
                        "git restore --source HEAD~1 ci/baselines", f'git -C "{self.wt}" rm contracts/x.json'):
            why = self.bash("builder", command, cwd=self.wt)
            self.assertIsNotNone(why, command)
        self.assertIsNone(self.bash("builder", "git add -A", cwd=self.wt))
        self.assertIsNone(self.bash("builder", "git diff -- ci/baselines/vulture.txt", cwd=self.wt), "reading is fine")

    def test_no_role_writes_or_names_the_desks_answers(self):
        target = self.d / ".desk" / "answers.md"
        for role in self.env:
            with self.subTest(role):
                why = self.hook(role, "Write", file_path=str(target), content='- "go" (1a2b3c4d:L1)\n')
                self.assertIsNotNone(why, role)
                self.assertIsNotNone(self.bash(role, f'git log -1 -- "{target}"' if role in ("builder", "fixer")
                                               else f'pytest "{target}"'), role)
        why = self.hook("planner-fix", "Write", file_path=str(self.d / ".desk" / "answers.md"), content="x")
        self.assertIn(".desk/", why)

    def test_no_role_but_a_builder_writes_python_or_test_config(self):
        own = {"plan-review": self.d / "plan-review" / "x", "grounding": self.d / "grounding",
               "planner-fix": self.d / "slices", "audit-judge": self.d / "challenge",
               "reader": self.notes.parent / "runs", "verdict": self.d / "stop-review" / "A" / "REVIEW-x"}
        for role, folder in own.items():
            for name in ("test_x.py", "conftest.py", "pytest.ini", "pyproject.toml", "setup.cfg", "tox.ini", "x.pyw"):
                with self.subTest(role=role, name=name):
                    why = self.hook(role, "Write", file_path=str(folder / name), content="x")
                    self.assertIsNotNone(why)
        self.assertIsNone(self.hook("plan-review", "Write", file_path=str(self.d / "plan-review" / "x" / "notes.md"),
                                    content="x"))
        self.assertIsNone(self.hook("builder", "Write", file_path=str(self.wt / "pkg" / "tests" / "test_x.py"),
                                    content="x"))

    def test_the_checkers_plan_review_test_file_is_refused_and_its_code_never_runs(self):
        why = self.hook("plan-review", "Write", file_path=str(self.d / "plan-review" / "x" / "test_x.py"), content="x")
        self.assertIn("writes no Python", why)
        copy = self.wt_root / "stop-copy"
        own = (self.d / "plan-review" / "x" / "test_x.py").as_posix()
        for role in ("plan-review", "grounding", "reader", "audit-reader", "verdict"):
            for command in (f'uv run --no-sync pytest "{own}"', f'python -m ship timed --slice x --log l -- pytest "{own}"',
                            "pytest -p evil tests", "pytest -pevil tests", "pytest -c x.md tests",
                            "pytest --doctest-glob=*.md tests", "python -m pytest -o python_files=*.md tests",
                            "pytest --rootdir=x tests"):
                with self.subTest(role=role, command=command):
                    self.assertIsNotNone(self.bash(role, command, cwd=copy), command)
            with self.subTest(role=role, command="the repo's own tests"):
                self.assertIsNone(self.bash(role, "uv run --no-sync pytest -q -p no:cacheprovider -k shaky tests",
                                            cwd=copy))
            with self.subTest(role=role, command="pytest in the program folder"):
                self.assertIsNotNone(self.bash(role, "pytest -q", cwd=self.d / "plan-review"))
        self.assertIsNone(self.bash("builder", "pytest -p evil tests", cwd=self.wt), "a builder's own tests")

    def script(self, path: Path, *args: str) -> str:
        return f'python "{path.as_posix()}" ' + " ".join(f'"{a}"' if " " in a or "/" in a or "\\" in a else a
                                                         for a in args)

    def test_each_role_runs_only_its_own_factory_scripts(self):
        lists = {
            "grounding": {"factory-core": ("his_words", "check_chain", "check_plan")},
            "plan-review": {"factory-core": ("check_chain", "check_plan")},
            "verdict": {"factory-core": ("check_plan",)},
            "planner-fix": {"factory-core": ("chain_packet", "check_chain", "check_plan")},
            "sweep-handoff": {"factory-core": ("chain_packet", "check_chain", "check_plan"),
                              "audit-area": ("sweep_briefs",)},
            "audit-reader": {"audit-area": ("callers", "lint_findings")},
            "audit-judge": {"factory-core": ("check_chain",), "audit-area": ("callers", "lint_findings")},
            "audit-intent": {"factory-core": ("his_words", "check_chain")},
            "audit-screen": {},
        }
        every = {"factory-core": ("his_words", "check_chain", "check_plan", "chain_packet", "check_index", "resume"),
                 "audit-area": ("probe_tests", "census", "collect_findings", "apply_screen", "callers", "lint_findings",
                                "sweep_briefs")}
        args = {"check_plan": [str(self.d), str(Path(__file__).resolve().parents[1])],
                "chain_packet": [str(self.d)], "sweep_briefs": [str(self.d), "--checkout", "x", "--prefix", "zz"]}
        for role, mine in lists.items():
            for skill, names in every.items():
                for name in names:
                    with self.subTest(role=role, script=name):
                        command = self.script(self.factory / "skills" / skill / "scripts" / f"{name}.py",
                                              *args.get(name, ["x"]))
                        why = self.bash(role, command)
                        if name in mine.get(skill, ()):
                            self.assertIsNone(why, command)
                        else:
                            self.assertIsNotNone(why, command)

    def test_the_checkers_script_escapes_are_refused(self):
        probe = self.audit / "probe_tests.py"
        sweep = self.audit / "sweep_briefs.py"
        chain = self.core / "check_chain.py"
        plan = self.core / "check_plan.py"
        packet = self.core / "chain_packet.py"
        other = self.root / "other-program"
        kit = Path(__file__).resolve().parents[1]
        refused = {
            "grounding": [self.script(probe, ".", "--checkout", str(self.wt), "--out", str(self.d / "PLAN.md"),
                                      "--python", "python", "--src", "x"),
                          self.script(chain, str(self.d), "--stage", "handoff", "--rerun-facts", str(self.wt)),
                          self.script(plan, str(self.d), str(self.root / "evil-ship")),
                          self.script(chain, str(self.d), "--stage", "handoff", "--ship", str(self.root / "evil-ship"))],
            "plan-review": [self.script(probe, ".", "--checkout", "x", "--out", str(self.d / ".kit" / "x.tsv"),
                                        "--python", "python", "--src", "x")],
            "planner-fix": [self.script(packet, str(other)), self.script(sweep, str(self.d), "--checkout", "x",
                                                                          "--prefix", "zz")],
            "sweep-handoff": [self.script(sweep, str(other), "--checkout", "x", "--prefix", "zz")],
        }
        for role, commands in refused.items():
            for command in commands:
                with self.subTest(role=role, command=command):
                    self.assertIsNotNone(self.bash(role, command), command)
        allowed = {
            "grounding": [self.script(self.core / "his_words.py", "word", "--full"),
                          self.script(chain, str(self.d), "--stage", "handoff", "--ship", str(kit)),
                          self.script(plan, str(self.d), str(kit))],
            "planner-fix": [self.script(packet, str(self.d))],
            "sweep-handoff": [self.script(sweep, str(self.d), "--checkout", str(self.wt), "--prefix", "zz")],
        }
        for role, commands in allowed.items():
            for command in commands:
                with self.subTest(role=role, command=command):
                    self.assertIsNone(self.bash(role, command), command)

    def test_a_scripts_output_path_must_be_the_roles_own(self):
        from ship import hook

        mine = str(self.d / "plan-review")
        run = mock.Mock(role="plan-review", kit_owned=lambda t: False, may_write=lambda t: hook.inside(t, mine))
        script = "factory-core/scripts/check_chain.py"
        for flag in ("--out", "--output", "-o"):
            self.assertIsNone(hook.script_args_problem(run, script, ["x", flag, f"{mine}/out.md"], str(self.root)))
            self.assertIn("which role plan-review does not write",
                          hook.script_args_problem(run, script, ["x", flag, str(self.d / "PLAN.md")], str(self.root)))
        self.assertIsNotNone(hook.script_args_problem(run, script, ["x", f"--out={self.d / 'PLAN.md'}"], str(self.root)))

    def test_probe_tests_takes_only_the_checkouts_interpreter_or_the_kits(self):
        from ship import hook

        run = mock.Mock(role="audit-reader", kit_owned=lambda t: False, may_write=lambda t: True)
        probe = "audit-area/scripts/probe_tests.py"
        copy = str(self.wt)
        venv = str(self.wt / ".venv" / "Scripts" / "python.exe")
        self.assertIsNone(hook.script_args_problem(run, probe, [".", "--checkout", copy, "--python", venv], copy))
        self.assertIsNone(hook.script_args_problem(run, probe, [".", "--checkout", copy, "--python",
                                                                 __import__("sys").executable], copy))
        self.assertIn("only the checkout's interpreter",
                      hook.script_args_problem(run, probe, [".", "--checkout", copy, "--python",
                                                            str(self.root / "evil.exe")], copy))


# ---- the power watch race -----------------------------------------------------------------------------------


class PowerRace(unittest.TestCase):
    """D-L25: his `ship hold` typed while the watcher's probe runs survives (the checker's race.py)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="k4a-pw-"))
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.program = Program(self.tmp / "prog")
        self.program.dir.mkdir()
        self.settings = Settings()

    def step(self, mains, now, probe):
        from ship.power_watch import step

        return step(self.program, self.settings, mains, now, probe)

    def test_his_hold_typed_during_the_probe_that_clears_the_watchers_survives(self):
        from ship.power_watch import hold

        self.assertEqual(self.step(True, 0, lambda: ["github: down"]), "HOLD network: github: down")

        def probe():
            hold(self.program, "stop the run")
            return []

        self.assertTrue(self.step(True, 1, probe).startswith("HOLD kept"))
        self.assertEqual(self.program.hold.read_text("utf-8"), "him: stop the run\n")
        self.assertEqual(self.step(True, 2, lambda: []), "MAINS", "and the watcher has forgotten its own")
        self.assertEqual(self.program.hold.read_text("utf-8"), "him: stop the run\n")

    def test_his_hold_typed_during_a_failing_probe_is_never_written_over(self):
        from ship.power_watch import hold

        def slow_fail():
            hold(self.program, "stop")
            return ["github: timeout"]

        self.assertTrue(self.step(True, 0, slow_fail).startswith("HOLD kept"))
        self.assertEqual(self.program.hold.read_text("utf-8"), "him: stop\n")
        self.assertEqual(self.step(True, 1, lambda: []), "MAINS")
        self.assertEqual(self.program.hold.read_text("utf-8"), "him: stop\n")

    def test_his_hold_after_mains_settles_survives_the_clearing_probe(self):
        from ship.power_watch import hold

        self.assertEqual(self.step(False, 0, lambda: []), "HOLD on battery")
        self.step(True, 10, lambda: [])
        self.step(True, 20, lambda: [])

        def probe():
            hold(self.program, "his")
            return []

        self.assertTrue(self.step(True, 10_000, probe).startswith("HOLD kept"))
        self.assertEqual(self.program.hold.read_text("utf-8"), "him: his\n")

    def test_the_watchers_own_hold_still_clears(self):
        self.step(True, 0, lambda: ["github: down"])
        self.assertTrue(self.step(True, 1, lambda: []).startswith("CLEAR"))
        self.assertFalse(self.program.hold.exists())


# ---- HOLD stops everything new ---------------------------------------------------------------------------------

    def test_a_hold_he_writes_between_the_watchers_read_and_its_write_or_removal_is_kept(self):
        """The instants a deterministic step cannot reach: the watcher's read saw no HOLD (or its own), then his
        appeared before its create (or its move aside)."""
        from ship import power_watch as pw

        his = "him: in between\n"
        write(self.program.hold, his)
        with mock.patch.object(pw, "hold_text", return_value=None):
            self.assertFalse(pw.write_own(self.program, "network: x\n", None), "the exclusive create fails")
        self.assertEqual(self.program.hold.read_text("utf-8"), his)
        own = "network: x\n"
        with mock.patch.object(pw, "hold_text", return_value=own):
            self.assertFalse(pw.clear_own(self.program, own), "what moved aside was his: it goes back")
        self.assertEqual(self.program.hold.read_text("utf-8"), his)
        self.assertFalse(self.program.hold.with_name("HOLD.power-clearing").exists())


class HoldScope(ChainCase):
    """D-L25: under HOLD no handler starts anything (a worker, a script, a push, an arm, the teardown, the docs
    step, the plan checks, the audit's census, probe, collect and screen, a review, a merge); what already runs
    is still read."""

    def setUp(self):
        super().setUp()
        from ship.power_watch import hold

        self.hold = lambda: hold(self.program, "his test")

    def belt(self):
        from ship.chain import Conveyor

        return Conveyor(self.program, load_settings(self.program.dir))

    def refused(self, call):
        """Call a handler under HOLD: it must raise Held (the tick then says so) and start no child or worker."""
        from ship.chain import Held

        belt = self.belt()
        self.hold()
        launched = []
        with mock.patch("ship.chain.ln.launch", side_effect=lambda *a, **k: launched.append(a)):
            with self.assertRaises(Held) as got:
                call(belt)
        self.assertEqual(belt.scripts, [], "no script child started")
        self.assertEqual(launched, [], "no worker started")
        self.assertIsNone(belt.worker)
        return belt, str(got.exception)

    def armed(self):
        from ship.plan import init_state

        init_state(self.program.dir, self.repo, self.build_branch, self.wt_root, "origin")

    def test_the_tick_itself_starts_nothing_when_nothing_runs(self):
        belt = self.belt()
        self.hold()
        lines = belt.tick()
        self.assertEqual(lines, ["HOLD: nothing new starts and nothing runs"])
        self.assertFalse(self.program.state.exists(), "not even arming")

    def test_arm_pushes_no_build_branch_and_inits_nothing(self):
        write(self.program.project_file, self.program.project_file.read_text("utf-8").replace("build/t", "build/new"))
        from ship.tests.fixture import sign_gates

        sign_gates(self.program)
        _, what = self.refused(lambda belt: belt.arm(self.program))
        self.assertIn("arming", what)
        self.assertFalse(self.program.state.exists())
        self.assertEqual(sh(self.repo, "git", "ls-remote", "origin", "refs/heads/build/new"), "")

    def test_arm_starts_no_preflight(self):
        self.armed()
        self.setting("arm_preflight = true")
        _, what = self.refused(lambda belt: belt.arm(self.program))
        self.assertIn("preflight", what)

    def test_the_finish_runs_no_teardown(self):
        self.armed()
        with mock.patch("ship.armed.teardown") as teardown:
            self.refused(lambda belt: belt.finish({"next": "done", "status": "running"}))
        teardown.assert_not_called()
        self.assertFalse(self.program.report.exists())

    def test_no_docs_step(self):
        self.refused(lambda belt: belt.docs({"stop": "A"}))
        self.assertFalse((self.program.dir / "docs" / "A.json").exists())

    def test_no_plan_review_checks(self):
        _, what = self.refused(lambda belt: belt.review({}))
        self.assertIn("check_chain", what)

    def test_no_planner_fix_worker(self):
        self.refused(lambda belt: belt.planner_fix({}))

    def audit(self, stage):
        from ship import phase

        write(self.program.project_file, "project: qmx\nprogram: program\nkind: audit\nparent: null\narea: [pkg]\n"
              "gates:\n  intent: {by: him, at: 2026-11-14, source: \"t:1\", advance: yes}\n  verdicts: null\n"
              "  go: null\nabandoned: null\n")
        from ship.tests.fixture import sign_gates

        sign_gates(self.program)
        scripts = self.factory / "skills" / "audit-area" / "scripts"
        for name in ("census.py", "probe_tests.py", "collect_findings.py", "apply_screen.py"):
            write(scripts / name, "print('PASS stub')\n")
        prompts = self.root / "prompts"
        for name in ("AUDIT-INTENT.md", "AUDIT-READER.md", "AUDIT-JUDGE.md", "AUDIT-SCREEN.md", "AUDIT-HANDOFF.md"):
            write(prompts / name, "x {PROGRAM}\n")
        tip = self.tip()
        write(self.program.dir / "CENSUS.md", f"# Census\n\nTip: {tip}\n\n## Parts\n\n- **pkg** `pkg` (1)\n\n## End\n")
        phase.set_phase(self.program, stage, "running", "test")
        return {"next": "audit", "stage": stage}

    def test_no_census(self):
        p = self.audit("census")
        _, what = self.refused(lambda belt: belt.audit(p))
        self.assertIn("census", what)

    def test_no_audit_checkout_and_no_probe(self):
        p = self.audit("quality")
        _, what = self.refused(lambda belt: belt.audit(p))
        self.assertIn("audit checkout", what)
        self.assertFalse((self.wt_root / "audit-program").exists(), "the checkout and its setup did not start")

        def with_checkout(belt):
            belt.audit_copy = self.wt_root / "audit-program"
            belt.audit_packages = lambda tip: [Package("pkg")]
            belt.audit(p)

        _, what = self.refused(with_checkout)
        self.assertIn("probe", what)

    def test_no_collect(self):
        p = self.audit("quality")

        def ready(belt):
            belt.audit_copy = self.wt_root / "audit-program"
            belt.memo["audit"] = {"probes": {"pkg": 0}, "readers": {"pkg": {"attempts": 1, "done": True}}}
            belt.audit_packages = lambda tip: [Package("pkg")]
            belt.audit(p)

        _, what = self.refused(ready)
        self.assertIn("collect-findings", what)

    def test_no_apply_screen(self):
        p = self.audit("judgement")

        def ready(belt):
            belt.memo["audit"] = {"judged": True, "screened": True}
            belt.audit(p)

        _, what = self.refused(ready)
        self.assertIn("apply-screen", what)

    def test_no_checkpoint_review_starts(self):
        self.armed()
        belt = self.belt()
        self.hold()
        with mock.patch("ship.review.ln.launch", side_effect=AssertionError("a reader started")):
            lines = belt.review_checkpoint({"stop": "A", "round": "1"})
        self.assertIn("HOLD: the review of stop A does not start", lines)
        self.assertFalse((self.program.stop_review("A") / "START.json").exists())
        self.assertEqual(belt.checkpoint.scripts, [])

    def test_no_merge_starts_but_a_running_merge_is_still_read(self):
        self.armed()
        self.refused(lambda belt: belt.merge({"stop": "A"}))
        self.program.hold.unlink()
        belt = self.belt()
        belt.child("merge-A", [PY, "-c", "print('MERGED abc')"])
        belt.scripts[0].proc.wait(timeout=60)
        self.hold()
        lines = belt.tick()
        self.assertIn("MERGE MERGED abc", lines, "the result of what ran is read under HOLD")
        self.assertEqual(belt.scripts, [])


# ---- the checkpoint review's readers --------------------------------------------------------------------------


class ReaderWaits(ReviewCase):
    def test_a_reader_that_replies_waits_is_honoured_not_restarted(self):
        waits = {"match": "reader: chain", "reply": "WAITS which of the two exits is meant?"}
        self.rules(waits, self.verdict_rule("CLEAN", self.tip()), NOTES_DONE)
        self.assertEqual(self.ship("review", "A"), 10, self.out)
        self.assertEqual(len(self.calls("chain")), 1, "never restarted")
        self.assertTrue(any("the chain reader of stop A needs you" in w for w in self.waits()), self.waits())
        self.assertEqual(self.calls("verdict:"), [])


# ---- the checker's mutants M4 (stamp) and M11, M22 (ci summary) ------------------------------------------------


class StampGuard(RunCase):
    slices = [("a1", "A", "L1")]

    def test_a_reply_whose_sha_is_not_40_hex_stamps_nothing(self):
        from ship.dispatch import dispatch
        from ship.run import Build

        settings = load_settings(self.program.dir)
        dispatch(self.program, "a1", settings)
        folder = self.program.evidence("a1", 1)
        for name in settings.evidence_required:
            write(folder / name, f"{name} body\n")
        build = Build(self.program, settings)
        for bad in ("deadbeef", "A" * 40, "g" * 40, "a" * 39, "a" * 41):
            self.assertEqual(build.stamp("a1", bad), [], bad)
        self.assertEqual((folder / "how.md").read_text("utf-8"), "how.md body\n", "M4: no END line written")
        self.assertEqual(build.stamp("a1", "a" * 40), list(settings.evidence_required))


from ship.tests.test_ci import CiCase  # noqa: E402  (CiCase has no tests of its own)


class SummarySha(CiCase):
    def summary(self, sha):
        body = {"sha": sha, "ref": "build/t", "run_id": 1001, "url": "https://github.test/runs/1001", "level": "deep",
                "green": True, "jobs": [], "reds": [], "quality": [],
                "mutants": {"killed": 0, "survived": 0, "new_survivors": 0}, "skipped": []}
        return {"summary.json": json.dumps(body), "summary.md": "x"}

    def attach(self, sha, named):
        from ship import ci

        ci.start(self.program, self.settings)
        self.finish_green(1001, sha)
        data = self.runs()
        data["runs"][0]["artifacts"]["summary"] = self.summary(named)
        self.store.write_text(json.dumps(data), "utf-8")

    def test_ci_summary_sha_reads_that_commit_not_the_tip(self):
        from ship import ci

        old = self.tip()
        self.attach(old, old)
        new = self.on_build({"pkg/later.py": "X = 1\n"}, "later")
        self.assertNotEqual(new, old)
        rc, lines = ci.summary(self.program, self.settings, old[:12])
        self.assertEqual(rc, 0, lines)
        self.assertEqual(lines[0], f"SUMMARY {self.program.nightly(old) / 'summary.json'}", "M22: --sha is honoured")
        self.assertFalse((self.program.nightly(new) / "summary.json").exists())

    def test_a_summary_naming_another_sha_with_the_same_first_8_is_refused(self):
        from ship import ci

        tip = self.tip()
        twin = tip[:8] + ("0" if tip[8] != "0" else "1") + tip[9:]
        self.attach(tip, twin)
        rc, lines = ci.summary(self.program, self.settings)
        self.assertEqual(rc, 1, lines)
        self.assertTrue(lines[0].startswith(f"NONE summary for {tip[:8]}: deep run 1001's summary.json names"), lines)
        self.assertFalse((self.program.nightly(tip) / "summary.json").exists(), "M11: the full sha is compared")


if __name__ == "__main__":
    unittest.main()
