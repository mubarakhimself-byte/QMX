import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from ship import state as st
from ship.quality import Finding, baseline, checkpoint_quality, mutant_globs, new_findings, parse
from ship.settings import load_settings
from ship.slice_checks import slice_checks
from ship.suite import Package
from ship.tests.fixture import PY, RepoCase, sh, write

FAKE = Path(__file__).resolve().parent / "fake_tools.py"
ROOT = Package(".")
SUB = Package("packages/qmf-core")


class Parsers(unittest.TestCase):
    def test_vulture_lines_become_findings_without_the_confidence(self):
        log = "$ vulture .\n# cwd x\npkg\\mod.py:3: unused function 'f' (60% confidence)\nnoise\n\nEXIT rc=3 seconds=1\n"
        self.assertEqual(parse("vulture", log, Path("C:/co"), ROOT),
                         [Finding("vulture", "pkg/mod.py", 3, "unused function 'f'")])
        self.assertEqual(parse("vulture", "src\\qmf\\a.py:9: unused import 'os' (90% confidence)\n", Path("C:/co"), SUB),
                         [Finding("vulture", "packages/qmf-core/src/qmf/a.py", 9, "unused import 'os'")])

    def test_skylos_json_findings_from_every_family(self):
        report = {"unused_functions": [{"name": "f", "full_name": "pkg.mod.f", "file": "C:/co/pkg/mod.py",
                                        "line": 3, "confidence": 60}],
                  "quality": {"findings": [{"rule_id": "SKY-L028", "file": "pkg/mod.py", "line": 9,
                                            "message": "too deep"}]},
                  "summary": {"total": 2}}
        log = f"$ skylos . -a --json\n# cwd C:/co\nscanning...\n{json.dumps(report, indent=1)}\n\nEXIT rc=1 seconds=4\n"
        self.assertEqual(parse("skylos", log, Path("C:/co"), ROOT), [
            Finding("skylos", "pkg/mod.py", 3, "unused_functions pkg.mod.f"),
            Finding("skylos", "pkg/mod.py", 9, "quality.findings SKY-L028 too deep"),
        ])

    def test_mutmut_survivors_map_to_their_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp) / "packages/qmf-core/src/qmf/core/chrono.py", "")
            log = ("    qmf.core.chrono.x__invalid__mutmut_4: survived\n"
                   "    qmf.core.chrono.x__invalid__mutmut_5: killed\n"
                   "    qmf.core.chrono.xǁClockǁnow__mutmut_1: no tests\n")
            self.assertEqual(parse("mutmut", log, Path(tmp), SUB), [
                Finding("mutmut", "packages/qmf-core/src/qmf/core/chrono.py", 0,
                        "survived qmf.core.chrono.x__invalid__mutmut_4"),
                Finding("mutmut", "packages/qmf-core/src/qmf/core/chrono.py", 0,
                        "no tests qmf.core.chrono.xǁClockǁnow__mutmut_1"),
            ])

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

    def test_only_findings_beyond_the_known_ones_are_new(self):
        a = Finding("vulture", "p.py", 3, "unused function 'f'")
        moved = Finding("vulture", "p.py", 30, "unused function 'f'")
        b = Finding("vulture", "p.py", 5, "unused function 'g'")
        self.assertEqual(new_findings([moved, b], [a.key]), [b])
        self.assertEqual(new_findings([a, moved], [a.key]), [moved])


class QualityRuns(RepoCase):
    def setUp(self):
        super().setUp()
        write(self.program.checks_toml, textwrap.dedent(f"""\
            [[package]]
            root = "."
            test = [{PY!r}, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml={{junit}}", "{{tests}}"]
            vulture = [{PY!r}, {str(FAKE)!r}, "vulture"]
            mutmut = [[{PY!r}, {str(FAKE)!r}, "mutmut-run", "{{mutants}}"], [{PY!r}, {str(FAKE)!r}, "mutmut-results"]]
            """).replace("'", '"'))
        self.settings = load_settings(self.program.dir)
        self.base = self.push_to_build({"pkg/old.py": "def unused_old():\n    return 0\n"})
        self.quality_dir = self.wt_root / "ship-quality"

    def push_to_build(self, files):
        sh(self.repo, "git", "checkout", "-q", "-B", "b", f"origin/{self.build_branch}")
        for path, text in files.items():
            write(self.repo / path, text)
        sha = self.commit("direct")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        return sha

    def test_slice_checks_fail_only_on_findings_new_in_the_slice(self):
        with st.locked(self.program) as state:
            state.slices["s1"].files.append("pkg/old.py")
        head = self.make_ready("s1", {"pkg/old.py": "def unused_old():\n    return 0\n\n\ndef unused_new():\n    return 1\n"})
        ok, lines = slice_checks(self.program, "s1", self.settings)
        h8 = head[:8]
        self.assertFalse(ok)
        self.assertIn(f"FAIL quality-vulture-root s1 {h8} 1 new: pkg/old.py:5 unused function 'unused_new'", lines)
        self.assertIn(f"NOTRUN quality-skylos-root s1 {h8} no command in checks.toml", lines)
        self.assertIn(f"PASS safety s1 {h8} the SAFETY fact gives the brief's output at the head", lines)

    def test_checkpoint_blocks_new_findings_until_the_baseline_knows_them(self):
        tip = self.push_to_build({"pkg/area.py": "def unused_a():\n    return 0\n\n\ndef area(r):\n    return r * r\n"})
        ok, lines = checkpoint_quality(self.program, self.settings, self.base, ("vulture", "skylos", "mutmut"))
        t8 = tip[:8]
        self.assertFalse(ok)
        self.assertEqual(lines, [
            f"FAIL quality-vulture-root {t8} 1 new: pkg/area.py:1 unused function 'unused_a'",
            f"NOTRUN quality-skylos-root {t8} no command in checks.toml",
            f"FAIL quality-mutmut-root {t8} 2 new: pkg/area.py survived pkg.area.x_area__mutmut_1; "
            "pkg/area.py survived pkg.area.x_unused_a__mutmut_1",
        ])

        ok, lines = baseline(self.program, self.settings, None, ("vulture", "mutmut"), None)
        self.assertTrue(ok, lines)
        first = (self.quality_dir / "baseline-vulture.tsv").read_text("utf-8")
        self.assertEqual([ln.split("\t")[:3] for ln in first.splitlines() if not ln.startswith("#")],
                         [["pkg/area.py", "1", "unused function 'unused_a'"],
                          ["pkg/old.py", "1", "unused function 'unused_old'"]])
        backlog = (self.quality_dir / "BACKLOG.md").read_text("utf-8")
        self.assertIn("| vulture | pkg/old.py | 1 | unused function 'unused_old' |", backlog)
        self.assertIn("| mutmut | pkg/area.py | 0 | survived pkg.area.x_area__mutmut_1 |", backlog)
        self.assertTrue(baseline(self.program, self.settings, None, ("vulture", "mutmut"), None)[0])
        self.assertEqual((self.quality_dir / "baseline-vulture.tsv").read_text("utf-8"), first)

        ok, lines = checkpoint_quality(self.program, self.settings, self.base, ("vulture", "mutmut"))
        self.assertTrue(ok, lines)
        self.assertEqual(lines, [f"PASS quality-vulture-root {t8} no new findings (1 known)",
                                 f"PASS quality-mutmut-root {t8} no new findings (2 known)"])

    def test_baseline_in_parts_replaces_only_its_own_part(self):
        self.push_to_build({"pkg/area.py": "def area(r):\n    return r * r\n"})
        self.assertTrue(baseline(self.program, self.settings, None, ("mutmut",), (1, 2))[0])
        self.assertTrue(baseline(self.program, self.settings, None, ("mutmut",), (2, 2))[0])
        rows = (self.quality_dir / "baseline-mutmut.tsv").read_text("utf-8").splitlines()
        names = sorted(ln.split("\t")[2] for ln in rows if not ln.startswith("#"))
        self.assertEqual(names, ["survived pkg.app.x_add__mutmut_1", "survived pkg.area.x_area__mutmut_1",
                                 "survived pkg.old.x_unused_old__mutmut_1"])


if __name__ == "__main__":
    unittest.main()
