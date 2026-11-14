"""U17b: one ratchet, read from the repo. The quality tools and pyright are judged against the repo's own
`ci/baselines/` with the repo's own `tools/ci/ratchet.py` (here a copy of qmx-ci's, planted in the fixture)."""

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from ship import state as st
from ship.quality import (BASELINE_MOVED, Finding, RepoRatchet, checkpoint_quality, mutant_globs, parse,
                          parse_pyright, types_ratchet)
from ship.settings import load_settings
from ship.slice_checks import slice_checks
from ship.suite import Package
from ship.tests.fixture import PY, RepoCase, sh, write
from ship.wrapper import RunResult

HERE = Path(__file__).resolve().parent
FAKE = HERE / "fake_tools.py"
RATCHET = (HERE / "repo_ratchet.py").read_text("utf-8")
ROOT = Package(".")
SUB = Package("packages/qmf-core")
HEADER = "# taken by the baseline level\n"


def ratchet_in(folder: Path, baselines: dict[str, str] | None = None) -> RepoRatchet:
    write(folder / "tools" / "ci" / "ratchet.py", RATCHET)
    for tool, text in (baselines or {}).items():
        write(folder / "ci" / "baselines" / f"{tool}.txt", HEADER + text)
    found = RepoRatchet.at(folder)
    assert found is not None
    return found


class Parsers(unittest.TestCase):
    def test_vulture_lines_become_findings_keyed_as_ci_keys_them(self):
        log = "$ vulture .\n# cwd x\npkg\\mod.py:3: unused function 'f' (60% confidence)\nnoise\n\nEXIT rc=3 seconds=1\n"
        self.assertEqual(parse("vulture", log, Path("C:/co"), ROOT),
                         [Finding("vulture", "pkg/mod.py", 3, "vulture", "unused function 'f'")])
        self.assertEqual(parse("vulture", "src\\qmf\\a.py:9: unused import 'os' (90% confidence)\n", Path("C:/co"), SUB),
                         [Finding("vulture", "packages/qmf-core/src/qmf/a.py", 9, "vulture", "unused import 'os'")])

    def test_skylos_reads_the_top_level_finding_lists_as_qci_does(self):
        report = {"unused_functions": [{"name": "f", "full_name": "pkg.mod.f", "file": "C:/co/pkg/mod.py",
                                        "line": 3, "confidence": 60}],
                  "quality": [{"rule_id": "SKY-L028", "file": "pkg/mod.py", "line": 9, "message": "too deep"}],
                  "whitelisted": [{"name": "g", "file": "pkg/mod.py", "line": 1}],
                  "summary": {"total": 2}}
        log = f"$ skylos . -a --json\n# cwd C:/co\nscanning...\n{json.dumps(report, indent=1)}\n\nEXIT rc=1 seconds=4\n"
        self.assertEqual(parse("skylos", log, Path("C:/co"), ROOT), [
            Finding("skylos", "pkg/mod.py", 9, "quality:SKY-L028", "too deep"),
            Finding("skylos", "pkg/mod.py", 3, "unused_functions:unused_functions", "pkg.mod.f"),
        ])

    def test_mutmut_survivors_are_keyed_by_package_and_function(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "packages/qmf-core/src/qmf/core/chrono.py", "")
            log = ("    qmf.core.chrono.x__invalid__mutmut_4: survived\n"
                   "    qmf.core.chrono.x__invalid__mutmut_5: killed\n"
                   "    qmf.core.chrono.xǁClockǁnow__mutmut_1: no tests\n")
            found = parse("mutmut", log, Path(tmp), SUB)
        file = "packages/qmf-core/src/qmf/core/chrono.py"
        self.assertEqual(found, [
            Finding("mutmut", "packages/qmf-core", 0, "mutmut", "qmf.core.chrono._invalid survived", file,
                    "qmf.core.chrono.x__invalid__mutmut_4"),
            Finding("mutmut", "packages/qmf-core", 0, "mutmut", "qmf.core.chrono.Clock.now no tests", file,
                    "qmf.core.chrono.xǁClockǁnow__mutmut_1"),
        ])

    def test_pyright_text_is_read_whole_and_numbers_become_hashes(self):
        text = ("$ pyright\nC:\\co\\pkg\\a.py\n"
                "  c:\\co\\pkg\\a.py:3:5 - error: Argument count 2 is wrong\n"
                "    \"int\" is not \"str\" (reportCallIssue)\n"
                "  c:\\co\\pkg\\a.py:9:1 - warning: Import \"x\" could not be resolved (reportMissingImports)\n"
                "  c:\\co\\pkg\\a.py:12:1 - error: Code is unreachable 7\n"
                "2 errors, 1 warning, 0 informations \n\nEXIT rc=1 seconds=2\n")
        found, complete = parse_pyright(text, Path("C:/co"), ROOT)
        self.assertTrue(complete)
        self.assertEqual(found, [
            Finding("pyright", "pkg/a.py", 3, "reportCallIssue", 'Argument count # is wrong "int" is not "str"'),
            Finding("pyright", "pkg/a.py", 12, "pyright", "Code is unreachable #"),
        ])
        short = text.replace("2 errors", "3 errors")
        self.assertFalse(parse_pyright(short, Path("C:/co"), ROOT)[1], "a count that does not add up is not complete")
        self.assertFalse(parse_pyright("$ pyright\nEXIT rc=1\n", Path("C:/co"), ROOT)[1])

    def test_pyright_json_is_read_as_qci_reads_it(self):
        report = {"generalDiagnostics": [
            {"file": "C:/co/pkg/a.py", "severity": "error", "rule": "reportCallIssue",
             "message": "Expected 2 arguments\n  got 3", "range": {"start": {"line": 4, "character": 0}}},
            {"file": "C:/co/pkg/a.py", "severity": "warning", "message": "w", "range": {"start": {"line": 1}}}]}
        found, complete = parse_pyright("node says hi\n" + json.dumps(report), Path("C:/co"), ROOT)
        self.assertTrue(complete)
        self.assertEqual(found, [Finding("pyright", "pkg/a.py", 5, "reportCallIssue", "Expected # arguments got #")])

    def test_keys_are_the_repo_ratchets_own_and_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            ratchet = ratchet_in(Path(tmp), {"vulture": "pkg/a.py|vulture|unused function 'f'\n"})
            a = Finding("vulture", "pkg/a.py", 3, "vulture", "unused function 'f'")
            moved = Finding("vulture", "pkg/a.py", 30, "vulture", "unused function 'f'")
            b = Finding("vulture", "pkg/a.py", 5, "vulture", "unused function 'g'")
            mut = Finding("mutmut", "packages/qmf-core", 0, "mutmut", "qmf.core.chrono._invalid survived", "x.py")
            self.assertEqual(ratchet.key(a), "pkg/a.py|vulture|unused function 'f'")
            self.assertEqual(ratchet.key(mut), "packages/qmf-core|mutmut|qmf.core.chrono._invalid survived")
            known = ratchet.baseline("vulture")
            self.assertEqual(ratchet.new([moved, b], known), [b], "a moved finding stays known")
            self.assertEqual(ratchet.new([a, moved], known), [moved], "a second copy of a known key is new")
            self.assertIsNone(ratchet.baseline("skylos"), "no baseline file: no baseline")

    def test_a_checkout_without_the_ratchet_has_no_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(RepoRatchet.at(Path(tmp)))
            write(Path(tmp) / "tools" / "ci" / "ratchet.py", "raise SystemExit('broken')\n")
            self.assertIsNone(RepoRatchet.at(Path(tmp)), "a ratchet that does not load is none")

    def test_mutant_globs_cover_the_functions_holding_changed_lines(self):
        source = textwrap.dedent("""\
            import os


            def untouched():
                return 1


            @decorated
            def touched(a):
                return a + 1


            class Clock:
                def now(self):
                    return 0

                def later(self):
                    return 1
            """)
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "packages/qmf-core/src/qmf/core/chrono.py", source)
            globs = mutant_globs(Path(tmp), SUB, {"packages/qmf-core/src/qmf/core/chrono.py": {1, 9, 15}})
        self.assertEqual(globs, ["qmf.core.chrono.x_touched__mutmut_*", "qmf.core.chrono.xǁClockǁnow__mutmut_*"])

    def test_a_types_run_whose_errors_do_not_add_up_stays_red(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            ratchet = ratchet_in(folder, {"pyright": ""})
            log = write(folder / "types.log",
                        "  C:/co/pkg/a.py:3:5 - error: bad (reportX)\n2 errors, 0 warnings, 0 informations\n")
            done = RunResult(1, False, 1.0, log)
            program = type("P", (), {"runs": folder / "runs"})()
            self.assertEqual(types_ratchet(ROOT, Path("C:/co"), None, ["pkg/a.py"], done, folder, None, program, ratchet),
                             ("FAIL", "rc=1: pyright's errors could not be read from types.log"))
            self.assertEqual(types_ratchet(ROOT, Path("C:/co"), None, [], RunResult(2, False, 1.0, log), folder, None,
                                           program, ratchet), ("FAIL", "rc=2: pyright did not finish"))
            self.assertEqual(types_ratchet(ROOT, Path("C:/co"), None, [], done, folder, None, program, None),
                             ("FAIL", "rc=1 (no baseline: the checkout has no tools/ci/ratchet.py)"))


class QualityRuns(RepoCase):
    def setUp(self):
        super().setUp()
        write(self.program.checks_toml, textwrap.dedent(f"""\
            [[package]]
            root = "."
            test = [{PY!r}, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml={{junit}}", "{{tests}}"]
            types = [{PY!r}, {str(FAKE)!r}, "pyright"]
            vulture = [{PY!r}, {str(FAKE)!r}, "vulture"]
            mutmut = [[{PY!r}, {str(FAKE)!r}, "mutmut-run", "{{mutants}}"], [{PY!r}, {str(FAKE)!r}, "mutmut-results"]]
            """).replace("'", '"'))
        self.settings = load_settings(self.program.dir)
        self.base = self.push_to_build({
            "pkg/old.py": "def unused_old():\n    return 0\n",
            "tools/ci/ratchet.py": RATCHET,
            "ci/baselines/vulture.txt": HEADER + "pkg/old.py|vulture|unused function 'unused_old'\n",
            "ci/baselines/mutmut.txt": HEADER,
            "ci/baselines/pyright.txt": HEADER})

    def push_to_build(self, files):
        sh(self.repo, "git", "checkout", "-q", "-B", "b", f"origin/{self.build_branch}")
        for path, text in files.items():
            if text is None:
                (self.repo / path).unlink()
            else:
                write(self.repo / path, text)
        sha = self.commit("direct")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        return sha

    def own(self, sid, *files):
        with st.locked(self.program) as state:
            state.slices[sid].files.extend(files)

    def test_slice_checks_fail_only_on_findings_new_in_the_slice(self):
        self.own("s1", "pkg/old.py")
        head = self.make_ready("s1", {"pkg/old.py": "def unused_old():\n    return 0\n\n\ndef unused_new():\n    return 1\n"})
        ok, lines = slice_checks(self.program, "s1", self.settings)
        h8 = head[:8]
        self.assertFalse(ok)
        self.assertIn(f"FAIL quality-vulture-root s1 {h8} 1 new: pkg/old.py:5 [vulture] unused function 'unused_new'",
                      lines)
        self.assertIn(f"NOTRUN quality-skylos-root s1 {h8} no command in checks.toml", lines)
        self.assertIn(f"PASS types-root s1 {h8} rc=0", lines)
        self.assertIn(f"PASS safety s1 {h8} the SAFETY fact gives the brief's output at the head", lines)

    def test_a_finding_the_baseline_knows_passes(self):
        self.own("s1", "pkg/old.py")
        head = self.make_ready("s1", {"pkg/old.py": "def unused_old():\n    return 0\n\nX = 1\n"})
        ok, lines = slice_checks(self.program, "s1", self.settings)
        self.assertIn(f"PASS quality-vulture-root s1 {head[:8]} no new findings (1 known)", lines)

    def test_a_slice_cannot_excuse_its_own_finding_by_adding_it_to_the_baseline(self):
        self.own("s1", "pkg/old.py", "ci/baselines/vulture.txt")
        head = self.make_ready("s1", {
            "pkg/old.py": "def unused_old():\n    return 0\n\n\ndef unused_new():\n    return 1\n",
            "ci/baselines/vulture.txt": HEADER + "pkg/old.py|vulture|unused function 'unused_old'\n"
                                                 "pkg/old.py|vulture|unused function 'unused_new'\n"})
        ok, lines = slice_checks(self.program, "s1", self.settings)
        self.assertFalse(ok)
        self.assertIn(f"FAIL quality-vulture-root s1 {head[:8]} 1 new: pkg/old.py:5 [vulture] unused function "
                      "'unused_new'", lines, "the baseline is read at the parent, never at the slice's head")

    def test_no_ratchet_in_the_repo_is_notrun_no_baseline(self):
        self.push_to_build({"tools/ci/ratchet.py": None})
        self.own("s1", "pkg/old.py")
        head = self.make_ready("s1", {"pkg/old.py": "def unused_old():\n    return 0\n\n\ndef unused_new():\n    return 1\n"})
        ok, lines = slice_checks(self.program, "s1", self.settings)
        self.assertIn(f"NOTRUN quality-vulture-root s1 {head[:8]} no baseline: the checkout has no tools/ci/ratchet.py",
                      lines)

    def test_types_fail_only_on_an_error_the_baseline_does_not_hold_in_the_slices_files(self):
        known = 'pkg/typed.py|reportCallIssue|Argument count # is wrong "int" is not "str"\n'
        self.push_to_build({"pkg/typed.py": "A = 1  # type-error\n", "ci/baselines/pyright.txt": HEADER + known,
                            "pkg/other.py": "B = 1  # type-error\n"})
        self.own("s1", "pkg/typed.py")
        head = self.make_ready("s1", {"pkg/typed.py": "A = 1  # type-error\nC = 3\n"})
        ok, lines = slice_checks(self.program, "s1", self.settings)
        self.assertIn(f"PASS types-root s1 {head[:8]} rc=1: 2 errors, none new in the slice's files (1 known)", lines,
                      "a known error, and one outside the slice's files, do not block")

        with st.locked(self.program) as state:
            state.slices["s1"].status = st.Status.PARKED  # out of the way: s2 touches the same file
        self.own("s2", "pkg/typed.py")
        head = self.make_ready("s2", {"pkg/typed.py": "A = 1  # type-error\nD = 4  # type-error\n"})
        ok, lines = slice_checks(self.program, "s2", self.settings)
        self.assertFalse(ok)
        self.assertIn(f"FAIL types-root s2 {head[:8]} rc=1: 1 new: pkg/typed.py:2 [reportCallIssue] Argument count # "
                      'is wrong "int" is not "str"', lines, "a second copy of a known error is new")

    def test_types_already_red_at_the_parent_do_not_block_the_slice(self):
        self.push_to_build({"pkg/typed.py": "A = 1  # type-error\n"})  # red here, as on Windows only
        self.own("s1", "pkg/typed.py")
        head = self.make_ready("s1", {"pkg/typed.py": "A = 1  # type-error\nC = 3\n"})
        ok, lines = slice_checks(self.program, "s1", self.settings)
        self.assertIn(f"PASS types-root s1 {head[:8]} rc=1: 1 errors, none new in the slice's files (1 known)", lines)
        self.assertTrue((self.program.checks("s1", head) / "types-root-base.log").exists(),
                        "the parent was run, because the baseline alone did not know the error")

    def test_checkpoint_blocks_new_findings_until_the_baseline_knows_them(self):
        tip = self.push_to_build({"pkg/area.py": "def unused_a():\n    return 0\n\n\ndef area(r):\n    return r * r\n"})
        ok, lines = checkpoint_quality(self.program, self.settings, self.base, ("vulture", "skylos", "mutmut"))
        t8 = tip[:8]
        self.assertFalse(ok)
        self.assertEqual(lines, [
            f"FAIL quality-vulture-root {t8} 1 new: pkg/area.py:1 [vulture] unused function 'unused_a'",
            f"NOTRUN quality-skylos-root {t8} no command in checks.toml",
            f"FAIL quality-mutmut-root {t8} 2 new: pkg/area.py [mutmut] pkg.area.area survived; "
            "pkg/area.py [mutmut] pkg.area.unused_a survived",
        ])
        new = (self.program.quality(tip) / "new-mutmut-root.txt").read_text("utf-8").splitlines()
        self.assertEqual([x.split("\t")[0] for x in new], [".|mutmut|pkg.area.area survived",
                                                          ".|mutmut|pkg.area.unused_a survived"])

        base = self.push_to_build({
            "ci/baselines/vulture.txt": HEADER + "pkg/area.py|vulture|unused function 'unused_a'\n"
                                                 "pkg/old.py|vulture|unused function 'unused_old'\n",
            "ci/baselines/mutmut.txt": HEADER + ".|mutmut|pkg.area.area survived\n.|mutmut|pkg.area.unused_a survived\n"})
        tip = self.push_to_build({"pkg/area.py": "def unused_a():\n    return 0\n\n\ndef area(r):\n    return r * r * 1\n"})
        ok, lines = checkpoint_quality(self.program, self.settings, base, ("vulture", "mutmut"))
        self.assertTrue(ok, lines)
        self.assertEqual(lines, [f"PASS quality-vulture-root {tip[:8]} no new findings (1 known)",
                                 f"PASS quality-mutmut-root {tip[:8]} no new findings (1 known)"])

    def test_baseline_command_writes_nothing_and_says_ci_takes_it(self):
        from ship.__main__ import main

        before = sorted(p.name for p in self.program.dir.iterdir())
        self.assertEqual(main(["baseline", "--program", str(self.program.dir)]), 1)
        self.assertEqual(sorted(p.name for p in self.program.dir.iterdir()), before)
        self.assertIn("`baseline` level in CI", BASELINE_MOVED)


if __name__ == "__main__":
    unittest.main()
