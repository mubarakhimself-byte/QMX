"""K4a: the kit items for the first real run (BUILD-LOG D-L23 and the S2-fix row)."""

import dataclasses
import json
import os
import textwrap
import unittest
from pathlib import Path

from ship import state as st
from ship.dispatch import dispatch
from ship.settings import load_settings
from ship.state import Status
from ship.tests.fixture import PY, RepoCase, sh, write
from ship.worktree import Setup, checkout_copy, drop_copy

PROBE = """\
import pathlib, sys
here = pathlib.Path.cwd()
with open(sys.argv[1], "a", encoding="utf-8") as out:
    out.write(f"{here.resolve()}|{(here / 'left.txt').exists()}\\n")
sys.exit(int(sys.argv[2]) if len(sys.argv) > 2 else 0)
"""


class Environment(RepoCase):
    """Item 2: the touched packages' checks.toml `setup` runs in a worktree or checkout before a worker
    starts there, through the time-limited wrapper."""

    def setUp(self):
        super().setUp()
        self.probe = write(self.root / "probe.py", PROBE)
        self.log = self.root / "setup.log"
        self.checks(0)
        self.settings = load_settings(self.program.dir)

    def checks(self, rc):
        write(self.program.checks_toml, textwrap.dedent(f"""\
            [[package]]
            root = "."
            setup = [{PY!r}, {str(self.probe)!r}, {str(self.log)!r}, "{rc}"]
            test = [{PY!r}, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml={{junit}}", "{{tests}}"]
            """).replace("'", '"'))

    def runs(self):
        return self.log.read_text("utf-8").splitlines() if self.log.exists() else []

    def test_a_first_dispatch_installs_the_worktree_before_it_returns(self):
        got = dispatch(self.program, "s1", self.settings)
        wt = (self.wt_root / "slice-s1").resolve()
        self.assertEqual(self.runs(), [f"{wt}|False"])
        self.assertEqual(len(got.setup), 1)
        self.assertTrue(got.setup[0].startswith("PASS setup-root rc=0 "), got.setup)
        log = self.program.checks_root / "_setup" / "s1" / "a1-r0" / "setup-root.log"
        self.assertIn("EXIT rc=0", log.read_text("utf-8"), "it ran through the timed wrapper")

    def test_a_fix_round_installs_again_after_the_reset(self):
        got = dispatch(self.program, "s1", self.settings)
        wt = Path(got.worktree)
        write(wt / "pkg" / "mul.py", "def mul(a, b):\n    return a * b\n")
        sh(wt, "git", "add", "-A")
        sh(wt, "git", "commit", "-q", "-m", "s1: work")
        sh(wt, "git", "push", "-q", "-u", "origin", got.branch)
        write(wt / "left.txt", "not pushed\n")  # a leftover the reset takes away
        with st.locked(self.program) as state:
            state.slices["s1"].status = Status.RED
        again = dispatch(self.program, "s1", self.settings)
        self.assertEqual(again.kind, "fix")
        self.assertEqual(self.runs(), [f"{wt.resolve()}|False"] * 2, "setup ran again, after the reset")
        self.assertTrue((self.program.checks_root / "_setup" / "s1" / "a2-r0" / "setup-root.log").exists())

    def test_a_failed_setup_starts_no_worker_retries_then_waits_on_him(self):
        """D-L25: the dispatch records the failed setup; the build starts no worker on it, releases the seat (a
        restart, never a death), tries again next tick, and parks the slice with a WAITS line at max_restarts."""
        from unittest import mock

        from ship import clock
        from ship.run import Build

        self.checks(3)
        got = dispatch(self.program, "s1", self.settings)
        self.assertTrue(got.setup[0].startswith("FAIL setup-root rc=3 "), got.setup)
        with st.locked(self.program) as state:  # back to where the build would find it
            state.slices["s1"].status, state.slices["s1"].holder = Status.DEAD, None
            state.slices["s2"].status = Status.PARKED
        write(self.root / "prompts" / "BUILDER.md", "Build {SLICE}\n")
        self.setting(f"prompt_dir = {json.dumps(str(self.root / 'prompts'))}")
        self.setting('internet_probe = ""')
        settings = load_settings(self.program.dir)
        build = Build(self.program, settings)
        build.start()
        with mock.patch("ship.run.ln.launch", side_effect=AssertionError("a worker started on a failed setup")), \
                mock.patch.dict(os.environ, {"SHIP_FAKE_MAINS": "1"}):
            for n in range(1, settings.max_restarts + 1):
                lines = build.tick(clock.now())
                sl = st.load(self.program).slices["s1"]
                if n < settings.max_restarts:
                    self.assertEqual(sl.status, Status.DEAD, lines)
                    self.assertIn(f"SETUP-FAILED s1: no worker started; tried again next tick ({n} of "
                                  f"{settings.max_restarts})", lines)
        self.assertEqual(sl.status, Status.PARKED, lines)
        self.assertEqual(sl.deaths, 0, "a failed setup is never a death")
        self.assertIn(f"PARK s1: its worktree setup failed {settings.max_restarts} times", lines)
        self.assertIn(f"s1 parked: its worktree setup failed {settings.max_restarts} times",
                      self.program.waits.read_text("utf-8"))

    def test_a_checkout_copy_runs_the_setup_it_is_given_and_none_without(self):
        copy = self.root / "copy"
        checkout_copy(self.repo, copy, self.tip(), self.settings)
        self.assertEqual(self.runs(), [])
        from ship.suite import setup_for

        setup = setup_for(self.program, ["pkg/app.py"], self.root / "logs")
        checkout_copy(self.repo, copy, self.tip(), self.settings, setup)
        self.assertEqual(self.runs(), [f"{copy.resolve()}|False"])
        self.assertTrue(setup.lines[0].startswith("PASS setup-root"))
        drop_copy(self.repo, copy, self.settings)

    def test_a_package_the_paths_do_not_touch_is_not_set_up(self):
        from ship.suite import setup_for

        write(self.program.checks_toml, self.program.checks_toml.read_text("utf-8").replace('root = "."', 'root = "lib"'))
        self.assertEqual(setup_for(self.program, ["pkg/app.py"], self.root).packages, ())
        self.assertEqual(len(setup_for(self.program, None, self.root).packages), 1, "None means every package")


FAKE_CLAUDE = Path(__file__).resolve().parent / "fake_claude.py"
STUB_PROBE = """\
import json, pathlib, sys
args = sys.argv[1:]
out = pathlib.Path(args[args.index("--out") + 1])
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text("test_id\\tsubjects\\tnormal\\tnone\\tsentinel\\tverdict\\n", "utf-8")
with open(pathlib.Path(__file__).with_name("calls.jsonl"), "a", encoding="utf-8") as log:
    log.write(json.dumps({"script": pathlib.Path(__file__).name, "args": args}) + "\\n")
"""
STUB_SCRIPT = """\
import json, pathlib, sys
with open(pathlib.Path(__file__).with_name("calls.jsonl"), "a", encoding="utf-8") as log:
    log.write(json.dumps({"script": pathlib.Path(__file__).name, "args": sys.argv[1:]}) + "\\n")
print("PASS stub")
"""
AUDIT_PROMPTS = {
    "AUDIT-INTENT.md": "intent {PROGRAM} {STAGE}\n",
    "AUDIT-READER.md": "read part {PART} in {CHECKOUT} for {PROGRAM} at {STAGE}; main {PROJECT.repo}\n",
    "AUDIT-JUDGE.md": "judge {PROGRAM} {STAGE}\n",
    "AUDIT-SCREEN.md": "screen {PROGRAM} {STAGE}\n",
    "AUDIT-HANDOFF.md": "hand off {PROGRAM} from {CHECKOUT} at {STAGE}\n"}


class AuditStages(RepoCase):
    """Item 3: the audit's readers (one per CENSUS part, in the frozen checkout, with SHIP_PART, PART and
    CHECKOUT), the probe before them and collect_findings after; the screen after the judgement, then
    apply_screen.py; the hand-off gets CHECKOUT."""

    def setUp(self):
        super().setUp()
        from ship import phase, records
        from ship.layout import Program
        from ship.settings import Settings
        from ship.tests.fixture import set_setting, sign_gates
        import shutil

        write(self.repo / "pkg" / "a" / "mod.py", "A = 1\n")
        write(self.repo / "pkg" / "b" / "mod.py", "B = 1\n")
        self.commit("parts")
        sh(self.repo, "git", "push", "-q", "origin", "main")
        self.census_tip = sh(self.repo, "git", "rev-parse", "HEAD")
        self.plans = self.root / "plans"
        records.init(self.repo, self.plans, "origin", Settings())
        shutil.move(str(self.program.dir), str(self.plans / "audit"))
        self.program = Program(self.plans / "audit")
        self.program.state.unlink()
        self.program.slices_md.unlink()
        write(self.program.project_file, "project: qmx\nprogram: audit\nkind: audit\nparent: null\narea: [pkg]\n"
              "gates:\n  intent: {by: him, at: 2026-11-14, source: \"t:1\", advance: yes}\n  verdicts: null\n"
              "  go: null\nabandoned: null\n")
        self.setup_log = self.root / "setup.log"
        probe = write(self.root / "probe.py", PROBE)
        write(self.program.checks_toml, "".join(textwrap.dedent(f"""\
            [[package]]
            root = "{root}"
            setup = [{PY!r}, {str(probe)!r}, {str(self.setup_log)!r}]
            """).replace("'", '"') for root in ("pkg/a", "pkg/b")))
        self.census("- **pkg-a** `pkg/a` (1 code lines in 1 files)\n- **pkg-b** `pkg/b` (1 code lines in 1 files)\n")
        self.factory = self.root / "factory"
        scripts = self.factory / "skills" / "audit-area" / "scripts"
        write(scripts / "probe_tests.py", STUB_PROBE)
        for name in ("collect_findings.py", "apply_screen.py", "census.py"):
            write(scripts / name, STUB_SCRIPT)
        self.calls_file = scripts / "calls.jsonl"
        write(self.factory / "projects" / "qmx" / "project.toml", textwrap.dedent(f"""\
            [project]
            name = "qmx"
            repo = {json.dumps(str(self.repo))}
            remote = "origin"
            target_branch = "main"
            worktree_root = {json.dumps(str(self.wt_root))}

            [pool]
            workers = 3
            """))
        prompts = self.root / "prompts"
        for name, text in AUDIT_PROMPTS.items():
            write(prompts / name, text)
        self.script = self.root / "claude-script.json"
        reader = {"match": "audit-reader:", "steps": [{"file": {
            "{program}/readers/{part}.md": "notes\nDONE\n", "{program}/readers/{part}.tsv": "id\n"}}],
                  "reply": "DONE {program}/readers/{part}.md"}
        write(self.script, json.dumps([reader]))
        set_setting(self.program.dir, *textwrap.dedent(f"""\
            claude = [{json.dumps(PY)}, {json.dumps(str(FAKE_CLAUDE))}]
            prompt_dir = {json.dumps(str(prompts))}
            factory_home = {json.dumps(str(self.factory))}
            internet_probe = ""
            chain_poll_s = 0.1
            worker_env_extra = ["FAKE_CLAUDE_SCRIPT"]
            """).splitlines())
        sign_gates(self.program)
        self.env = {"FAKE_CLAUDE_SCRIPT": str(self.script)}
        self.phase = phase

    def census(self, parts: str, tip: str | None = None) -> None:
        write(self.program.dir / "CENSUS.md", f"# Census\n\nTip: {tip or self.census_tip}\nRepo: x\n\n## Parts\n\n"
              f"One quality reader per part.\n\n{parts}\n## Intent sources\n\nnone\n")

    def belt(self):
        from ship.chain import Conveyor

        return Conveyor(self.program, load_settings(self.program.dir))

    def run_until(self, belt, done, limit=200):
        import time
        from unittest import mock

        lines = []
        with mock.patch.dict("os.environ", self.env):
            for _ in range(limit):
                lines += belt.tick()
                if done() or belt.exit is not None:
                    belt.stop_children()
                    return lines
                time.sleep(0.1)
        belt.stop_children()
        raise AssertionError(f"not done after {limit} ticks: {lines[-15:]}")

    def calls(self):
        if not self.calls_file.exists():
            return []
        return [json.loads(x) for x in self.calls_file.read_text("utf-8").splitlines()]

    def workers(self):
        log = self.program.dir / "fake-claude.log"
        return [json.loads(x) for x in log.read_text("utf-8").splitlines()] if log.exists() else []

    def stage(self):
        return self.phase.phase_json(self.program).get("phase")

    def test_quality_probes_each_package_then_one_reader_per_part_in_the_checkout_then_collects(self):
        self.phase.set_phase(self.program, "quality", "running", "test")
        belt = self.belt()
        lines = self.run_until(belt, lambda: self.stage() == "judgement")
        copy = (self.wt_root / "audit-audit").resolve()
        self.assertEqual(sh(copy, "git", "rev-parse", "HEAD"), self.census_tip, "the checkout is at the census tip")
        self.assertEqual(sorted(self.setup_log.read_text("utf-8").splitlines()),
                         sorted([f"{(copy / 'pkg' / 'a').resolve()}|False", f"{(copy / 'pkg' / 'b').resolve()}|False"]),
                         "each package was set up in the checkout before anything ran there")
        calls = self.calls()
        probes = [c["args"] for c in calls if c["script"] == "probe_tests.py"]
        self.assertEqual([a[0] for a in probes], ["pkg/a", "pkg/b"], "one probe per package root")
        for args in probes:
            self.assertEqual(Path(args[args.index("--checkout") + 1]).resolve(), copy)
            self.assertIn("--python", args)
            self.assertEqual(args[args.index("--src") + 1], args[0])
            self.assertTrue(args[args.index("--out") + 1].endswith(f"probe{os.sep}{Path(args[0]).name}.tsv")
                            or args[args.index("--out") + 1].endswith(f"probe/{Path(args[0]).name}.tsv"))
        self.assertEqual(calls[-1]["script"], "collect_findings.py", "the findings are collected after the readers")
        self.assertEqual(calls[-1]["args"], [str(self.program.dir)])
        runs = self.workers()
        self.assertEqual(sorted(r["env"]["SHIP_PART"] for r in runs), ["pkg-a", "pkg-b"])
        for run in runs:
            self.assertEqual(Path(run["cwd"]).resolve(), copy, "a reader is launched in the frozen checkout")
            self.assertEqual(run["env"]["SHIP_ROLE"], "audit-reader")
            prompt = run["argv"][run["argv"].index("-p") + 1]
            part = run["env"]["SHIP_PART"]
            self.assertIn(f"read part {part} in {copy}", prompt.replace(str(self.wt_root / "audit-audit"), str(copy)))
        first_reader = min(r["at"] for r in runs)
        self.assertTrue(all((self.program.dir / "probe" / f"{n}.tsv").stat().st_mtime <= first_reader for n in ("a", "b")),
                        "every probe ran before the first reader")
        self.assertIn("AUDIT quality done: 2 parts read, FINDINGS.tsv collected", lines)

    def test_a_reader_that_never_finishes_waits_on_him_after_its_restarts(self):
        write(self.script, json.dumps([{"match": "audit-reader:", "reply": "DONE nothing"}]))
        self.phase.set_phase(self.program, "quality", "running", "test")
        belt = self.belt()
        self.run_until(belt, lambda: False if belt.exit is None else True)
        self.assertEqual(belt.exit, 10)
        waits = self.program.waits.read_text("utf-8")
        self.assertIn("did not finish in 3 runs", waits)
        self.assertFalse(any(c["script"] == "collect_findings.py" for c in self.calls()))

    def test_a_probe_that_does_not_exit_0_waits_and_no_reader_starts(self):
        write(self.factory / "skills" / "audit-area" / "scripts" / "probe_tests.py",
              "import sys\nprint('probe broke')\nsys.exit(1)\n")
        self.phase.set_phase(self.program, "quality", "running", "test")
        belt = self.belt()
        self.run_until(belt, lambda: belt.exit is not None)
        self.assertEqual(belt.exit, 10)
        self.assertIn("the audit probe of pkg/a exited 1: probe broke", self.program.waits.read_text("utf-8"))
        self.assertEqual(self.workers(), [], "no reader goes without its probe")
        self.assertEqual(self.stage(), "quality")

    def test_a_failed_collect_waits_and_the_stage_stays(self):
        write(self.factory / "skills" / "audit-area" / "scripts" / "collect_findings.py",
              "import sys\nprint('bad tsv')\nsys.exit(2)\n")
        self.phase.set_phase(self.program, "quality", "running", "test")
        belt = self.belt()
        self.run_until(belt, lambda: belt.exit is not None)
        self.assertEqual(belt.exit, 10)
        self.assertIn("collect_findings.py failed: bad tsv", self.program.waits.read_text("utf-8"))
        self.assertEqual(self.stage(), "quality", "M19: no judgement on findings that were never collected")

    def test_a_readers_usage_limit_is_never_one_of_its_runs(self):
        limited = {"match": "audit-reader: audit-quality-pkg-a", "kind": "limit", "times": 3,
                   "reset": "2026-01-01T00:00:00+00:00"}
        reader = json.loads(self.script.read_text("utf-8"))[0]
        write(self.script, json.dumps([limited, reader]))
        self.phase.set_phase(self.program, "quality", "running", "test")
        belt = self.belt()
        self.run_until(belt, lambda: self.stage() == "judgement")
        runs = [r for r in self.workers() if r["env"].get("SHIP_PART") == "pkg-a"]
        self.assertEqual(len(runs), 4, "three limits, then the run that finished; max_restarts is 3")

    def test_a_reader_that_replies_waits_is_honoured_not_restarted(self):
        asks = {"match": "audit-reader: audit-quality-pkg-a", "reply": "WAITS is pkg/a in the area?"}
        reader = json.loads(self.script.read_text("utf-8"))[0]
        write(self.script, json.dumps([asks, reader]))
        self.phase.set_phase(self.program, "quality", "running", "test")
        belt = self.belt()
        self.run_until(belt, lambda: belt.exit is not None)
        self.assertEqual(belt.exit, 10)
        self.assertIn("the audit reader of part pkg-a needs you", self.program.waits.read_text("utf-8"))
        self.assertEqual(len([r for r in self.workers() if r["env"].get("SHIP_PART") == "pkg-a"]), 1)

    def test_a_part_that_is_not_a_plain_name_is_refused(self):
        self.census("- **pkg..a** `pkg/a` (1 code lines in 1 files)\n")
        self.phase.set_phase(self.program, "quality", "running", "test")
        belt = self.belt()
        self.run_until(belt, lambda: belt.exit is not None)
        self.assertEqual(belt.exit, 10)
        self.assertIn("are not plain names", self.program.waits.read_text("utf-8"))
        self.assertEqual(self.workers(), [])

    def test_judgement_then_the_screen_then_apply_screen(self):
        write(self.script, json.dumps([{"match": "audit-judge:", "reply": "DONE {program}/AUDIT.md"},
                                       {"match": "audit-screen:", "reply": "DONE {program}/AUDIT-SCREEN.md"}]))
        self.phase.set_phase(self.program, "judgement", "running", "test")
        belt = self.belt()
        self.run_until(belt, lambda: self.stage() == "verdicts")
        roles = [r["env"]["SHIP_ROLE"] for r in sorted(self.workers(), key=lambda r: r["at"])]
        self.assertEqual(roles, ["audit-judge", "audit-screen"], "the screen starts after the judgement")
        applied = [c for c in self.calls() if c["script"] == "apply_screen.py"]
        self.assertEqual([c["args"] for c in applied], [[str(self.program.dir)]])
        screen_at = max(r["at"] for r in self.workers())
        self.assertGreaterEqual(self.calls_file.stat().st_mtime, screen_at, "apply_screen.py runs after the screen")

    def test_the_hand_off_gets_the_checkout_and_drops_it_after(self):
        write(self.script, json.dumps([{"match": "sweep-handoff:", "reply": "DONE {program}/SLICES.md"}]))
        self.phase.set_phase(self.program, "audit-handoff", "running", "test")
        belt = self.belt()
        self.run_until(belt, lambda: (self.program.dir / "fake-claude.log").exists() and belt.side == {}
                       and belt.worker is None and belt.audit_copy is None)
        (run,) = self.workers()
        copy = self.wt_root / "audit-audit"
        prompt = run["argv"][run["argv"].index("-p") + 1]
        self.assertIn(f"hand off {self.program.dir} from {copy} at audit-handoff", prompt)
        self.assertFalse(copy.exists(), "the audit checkout is dropped once the hand-off is done")

    def test_the_probe_roots_without_checks_toml_are_the_areas_pyproject_folders(self):
        self.program.checks_toml.unlink()
        write(self.repo / "pkg" / "a" / "pyproject.toml", "[project]\nname = 'a'\n")
        write(self.repo / "pkg" / "pyproject.toml", "[project]\nname = 'pkg'\n")
        tip = self.commit("pyprojects")
        roots = [p.root for p in self.belt().audit_packages(tip)]
        self.assertEqual(roots, ["pkg", "pkg/a"])
        write(self.program.project_file, self.program.project_file.read_text("utf-8").replace("area: [pkg]",
                                                                                          "area: [pkg/a/sub]"))
        self.assertEqual([p.root for p in self.belt().audit_packages(tip)], ["pkg/a"], "the nearest one above the area")

    def test_the_stage_survives_the_conveyors_first_tick(self):
        self.phase.set_phase(self.program, "judgement", "running", "test")
        write(self.script, json.dumps([{"match": "audit-judge:", "kind": "hang"}]))
        belt = self.belt()
        with __import__("unittest").mock.patch.dict("os.environ", self.env):
            belt.tick()
            belt.tick()
        belt.stop_children()
        self.assertEqual(self.stage(), "judgement", "the conveyor never writes `audit` over an audit stage")



from ship.tests.test_run import HAPPY, RunCase, SOURCE  # noqa: E402  (RunCase has no tests of its own)

ROLE_PROMPT = "Build {SLICE} rules {RULES} repo {PROJECT.repo} fix [{FIX_REASON}] paths [{FIX_PATHS}] kind {KIND}\n"
NO_END = {f"{{evidence}}/{name}": f"{name} body\n" + ("TRACE: {slice} -> P1 -> S1\n" if name == "pr.md" else "")
          for name in ("how.md", "red.log", "report.md", "pr.md")}


class BuilderFill(RunCase):
    """Item 4: RULES and PROJECT.* in the builder's fill, the profile's roles in Build and Checkpoint, and a
    restarted fixer keeping FIX_REASON and FIX_PATHS."""

    slices = [("a1", "A", "L1")]

    def setUp(self):
        super().setUp()
        self.factory = self.root / "factory"
        self.setting(f"factory_home = {json.dumps(str(self.factory))}")
        write(self.factory / "projects" / "qmx" / "project.toml", textwrap.dedent(f"""\
            [project]
            name = "qmx"
            repo = {json.dumps(str(self.repo))}
            rules = {json.dumps(str(self.root / "RULES.md"))}

            [roles.builder]
            model = "claude-opus-test"

            [roles.reader]
            model = "claude-opus-reader"
            """))
        write(self.root / "prompts" / "BUILDER.md", ROLE_PROMPT)
        self.settings = load_settings(self.program.dir)

    def test_the_builder_gets_rules_and_project_values_and_the_profiles_model(self):
        from ship.run import PROMPT_KEYS

        self.assertIn("RULES", PROMPT_KEYS)
        self.assertIn("PROJECT.*", PROMPT_KEYS)
        self.assertEqual(self.ship_run(), 0, self.last_out)
        (call,) = self.claude_calls("builder:")
        argv = call["argv"]
        prompt = argv[argv.index("-p") + 1]
        self.assertIn(f"rules {self.root / 'RULES.md'} repo {self.repo} ", prompt)
        self.assertEqual(argv[argv.index("--model") + 1], "claude-opus-test", "the profile's role overrides roles.toml")

    def test_the_checkpoint_takes_the_profiles_roles_too(self):
        from ship.review import Checkpoint

        self.assertEqual(Checkpoint(self.program, "A", self.settings, 1).roles["reader"].model, "claude-opus-reader")

    def fake_launch(self, prompts):
        class Handle:
            pid, created, session_id = 1, 0.0, "s"
            folder = self.root

            def kill(self):
                pass

        def launch(role, prompt, cwd, program, worker_id, settings, extra_env=None, label=None, slot=None):
            prompts.append((role.name, prompt))
            return Handle()

        return launch

    def test_a_restarted_fixer_keeps_its_reason_and_paths_until_verify_passes(self):
        from unittest import mock

        from ship.dispatch import Dispatched
        from ship.run import Build

        build = Build(self.program, self.settings)
        prompts = []
        common = dict(slice="a1", worktree=str(self.root / "wt"), branch="slice/a1", parent="p", evidence="e",
                      leftover=None)
        with mock.patch("ship.run.ln.launch", self.fake_launch(prompts)):
            build.start_worker(Dispatched(dispatch_id="d2", kind="fix", attempt=2, restart=0, **common),
                               {"reason": "slice_checks: 1 FAIL", "paths": ["C:/x/summary.txt"]})
            build.start_worker(Dispatched(dispatch_id="d3", kind="restart", attempt=2, restart=1, **common), None)
            build.after_verify("a1", 0, [])
            build.start_worker(Dispatched(dispatch_id="d4", kind="restart", attempt=2, restart=2, **common), None)
        self.assertEqual(prompts[0], ("fixer", "Build a1 rules " + str(self.root / "RULES.md") + f" repo {self.repo} "
                                                "fix [slice_checks: 1 FAIL] paths [C:/x/summary.txt] kind fix\n"))
        self.assertEqual(prompts[1][0], "fixer", "a restart of a fix round is a fixer")
        self.assertIn("fix [slice_checks: 1 FAIL] paths [C:/x/summary.txt] kind restart", prompts[1][1])
        self.assertIn("fix [] paths [] kind restart", prompts[2][1], "verify passed: the fix round is over")
        self.assertEqual(prompts[2][0], "builder")


class EndLines(RunCase):
    """Item 5: the kit stamps the END lines on the evidence once the builder replies READY."""

    slices = [("a1", "A", "L1")]

    def test_evidence_with_no_end_lines_is_stamped_and_passes_verify(self):
        no_end = {"match": "builder:", "steps": [
            {"write": {"pkg/{slice}.py": SOURCE}}, {"commit": "{slice}: work"}, {"push": True}, {"file": NO_END}],
                  "reply": "READY {head}"}
        self.rules(no_end)
        self.assertEqual(self.ship_run(), 0, self.last_out)
        sl = self.state().slices["a1"]
        self.assertEqual(sl.status, Status.LANDED, self.last_out)
        folder = self.program.evidence("a1", 1)
        for name in self.settings_names():
            lines = (folder / name).read_text("utf-8").splitlines()
            self.assertTrue(lines[-1].startswith("END ") and len(lines[-1].split()[1]) == 40, (name, lines))
            self.assertEqual(lines[-1].split()[2].split("-")[0], "a1")
            self.assertEqual(lines[0], f"{name} body", "the builder's text stays")
        self.assertIn("STAMPED a1 how.md, red.log, report.md, pr.md", self.last_out)

    def settings_names(self):
        return load_settings(self.program.dir).evidence_required

    def test_stamp_replaces_old_end_lines_and_an_end_only_file_is_empty(self):
        from ship.evidence import end_problem, stamp

        path = write(self.root / "how.md", "what I did\n\nEND oldsha old-id\n\n")
        self.assertTrue(stamp(path, "a" * 40, "s1-a1-r0-x"))
        self.assertEqual(path.read_text("utf-8"), f"what I did\nEND {'a' * 40} s1-a1-r0-x\n")
        self.assertIsNone(end_problem(path, "a" * 40, "s1-a1-r0-x"))
        self.assertFalse(stamp(self.root / "missing.md", "a" * 40, "x"), "a missing file stays missing")
        empty = write(self.root / "red.log", "")
        stamp(empty, "a" * 40, "x")
        self.assertEqual(end_problem(empty, "a" * 40, "x"), "red.log: empty but for its END line")


class HoldRelease(RunCase):
    """Item 7: `ship hold` and `ship release`; the build and the power watch honour a HOLD they did not write, and
    release clears only a manual hold."""

    slices = [("a1", "A", "L1")]

    def watch(self, mains, now=0.0, failed=()):
        from ship.power_watch import step

        return step(self.program, load_settings(self.program.dir), mains, now, lambda: list(failed))

    def test_hold_and_release_from_the_command_line(self):
        from ship.__main__ import main

        self.assertEqual(main(["hold", "--program", str(self.program.dir), "--why", '"stop the run" (1a2b3c4d:L9)']), 0)
        self.assertEqual(self.program.hold.read_text("utf-8"), 'him: "stop the run" (1a2b3c4d:L9)\n')
        self.assertEqual(main(["release", "--program", str(self.program.dir)]), 0)
        self.assertFalse(self.program.hold.exists())
        self.assertEqual(main(["release", "--program", str(self.program.dir)]), 0, "nothing to release is fine")

    def test_release_refuses_the_power_watchs_hold(self):
        from ship.power_watch import release

        self.assertEqual(self.watch(False), "HOLD on battery")
        rc, lines = release(self.program)
        self.assertEqual(rc, 1, lines)
        self.assertTrue(self.program.hold.read_text("utf-8").startswith("power: on battery"))

    def test_the_watcher_leaves_a_manual_hold_through_battery_and_mains(self):
        from ship.power_watch import hold

        hold(self.program, "his words")
        self.assertTrue(self.watch(False, 0).startswith("HOLD kept: not the watcher's"))
        self.assertEqual(self.program.hold.read_text("utf-8"), "him: his words\n", "battery never writes over his")
        self.assertEqual(self.watch(True, 10), "MAINS")
        self.assertEqual(self.watch(True, 10_000), "MAINS")
        self.assertEqual(self.program.hold.read_text("utf-8"), "him: his words\n", "mains never removes his")

    def test_a_manual_hold_over_the_watchers_is_never_cleared_by_it(self):
        from ship.power_watch import hold, release

        self.watch(False, 0)
        hold(self.program, "keep it held")
        self.watch(True, 10)
        self.watch(True, 10_000)
        self.assertEqual(self.program.hold.read_text("utf-8"), "him: keep it held\n")
        self.assertEqual(release(self.program)[0], 0)
        self.assertEqual(self.watch(False, 20_000), "HOLD on battery", "with his released, the watcher holds again")

    def test_the_build_starts_nothing_under_his_hold_and_leaves_it(self):
        from ship.power_watch import hold

        hold(self.program, "wait")
        from unittest import mock

        from ship.run import Build

        build = Build(self.program, load_settings(self.program.dir))
        build.start()
        with mock.patch.dict(os.environ, {"SHIP_FAKE_MAINS": "1", "FAKE_CLAUDE_SCRIPT": str(self.script_path)}):
            for _ in range(3):
                build.tick(__import__("ship.clock", fromlist=["now"]).now())
        build.stop_children()
        self.assertEqual(build.workers, {})
        self.assertEqual(self.state().slices["a1"].status, Status.PENDING)
        self.assertEqual(self.program.hold.read_text("utf-8"), "him: wait\n")

    def test_the_conveyor_starts_no_worker_under_his_hold(self):
        from ship.chain import Conveyor, Held
        from ship.power_watch import hold

        hold(self.program, "wait")
        belt = Conveyor(self.program, load_settings(self.program.dir))
        self.assertTrue(belt.no_workers_now())
        with self.assertRaises(Held):
            belt.start_worker("x", "grounding", "BUILDER.md", {}, self.program.dir)
        self.assertIsNone(belt.worker)


STUB_HIS_WORDS = """\
import json, pathlib, re, sys
turns = json.loads(pathlib.Path(__file__).with_name("turns.json").read_text("utf-8"))
pattern = re.compile(sys.argv[1], re.I)
for source, text in turns.items():
    if pattern.search(text):
        print(f"== {source} (planning, 2026-11-14)\\n{text}\\n")
"""
TURNS = {"1a2b3c4d:L120": "ok, leave B for after A ships, it can wait", "1a2b3c4d:L131": "yes call it the exit ladder"}
DESK = '# His answers\n\n- "leave B for after A ships" (1a2b3c4d:L120)\n- "call it the exit ladder" (1a2b3c4d:L131)\n'


class PlannerFixMemory(RunCase):
    """Item 8: a planner-fix round started by his answers is not the "second fixes" stop, and resets that memory.
    D-L25: his answers are only the desk's `.desk/answers.md` entries that the factory's his_words.py (here a
    stand-in reading turns.json) finds at their transcript line."""

    slices = [("a1", "A", "L1")]

    def setUp(self):
        super().setUp()
        from ship.chain import Conveyor

        scripts = self.root / "no-factory" / "skills" / "factory-core" / "scripts"
        write(scripts / "his_words.py", STUB_HIS_WORDS)
        write(scripts / "turns.json", json.dumps(TURNS))
        write(self.program.desk_answers, DESK)
        self.settings_ = load_settings(self.program.dir)
        self.belt = Conveyor(self.program, self.settings_)
        self.belt.worker_result = lambda name: object()  # the planner-fix worker has finished
        self.belt.run_checks = lambda tag: []  # and both plan checks pass
        self.folder = self.program.dir / "plan-review"

    def round(self, fixes: str):
        from ship.chain import Stop

        write(self.folder / "FIXES.md", fixes)
        write(self.folder / "REVIEW.md", "RESULT: FIXES\n")
        try:
            lines = self.belt.planner_fix({})
        except Stop as stop:
            return stop.code
        write(self.folder / "FIXES.applied.md", fixes)  # the worker's file
        return lines

    MECHANICAL = "# Fixes from the plan checks\n\n- FAIL check_plan: B1 has no SAFETY fact\n"
    HIS = ('# His answers\n\n- Stop B moves to later: "leave B for after A ships" (1a2b3c4d:L120)\n'
           '- Rename the slice: "call it the exit ladder" (1a2b3c4d:L131)\n')

    def test_a_second_mechanical_round_waits_on_him(self):
        self.assertEqual(self.round(self.MECHANICAL), ["PLANNER-FIX applied; the plan review runs once more"])
        self.assertEqual(self.round(self.MECHANICAL), 10)
        self.assertIn("asked for fixes a second time", self.program.waits.read_text("utf-8"))

    def test_his_answers_never_use_up_the_mechanical_round_and_reset_its_memory(self):
        self.round(self.MECHANICAL)
        self.assertTrue(self.belt.memo["planner_fix_done"])
        self.assertEqual(self.round(self.HIS), ["PLANNER-FIX applied (his answers); the plan review runs once more"])
        self.assertFalse(json.loads((self.program.dir / "chain.json").read_text("utf-8"))["planner_fix_done"],
                         "the memory is reset in chain.json")
        self.assertEqual(self.round(self.MECHANICAL), ["PLANNER-FIX applied; the plan review runs once more"],
                         "the next mechanical FIXES gets its one round again")
        self.assertEqual(self.round(self.MECHANICAL), 10)

    def his(self, text):
        from ship.chain import his_fixes

        return his_fixes(write(self.root / "f.md", text), self.program, self.settings_)

    def test_fixes_with_a_line_that_does_not_quote_him_are_mechanical(self):
        self.round(self.MECHANICAL)
        mixed = self.HIS + "- FAIL check_chain: S2 has no slice\n"
        self.assertFalse(self.his(mixed))
        self.assertTrue(self.his(self.HIS))
        self.assertFalse(self.his("- Do it (1a2b3c4d:L1)\n"), "a source with no quote")
        self.assertEqual(self.round(mixed), 10)

    def test_a_forged_fixes_line_is_the_mechanical_round(self):
        forged = '- Rewrite slice B: "whatever" (deadbeef:L1)\n'
        self.assertFalse(self.his(forged), "no .desk entry holds it")
        write(self.program.desk_answers, '- "leave B for after A ships" (1a2b3c4d:L120)\n')
        self.assertFalse(self.his('- x: "call it the exit ladder" (1a2b3c4d:L131)\n'),
                         "his real words at their line, but the desk never wrote them as an answer")
        write(self.program.desk_answers, DESK)
        self.round(self.MECHANICAL)
        self.assertEqual(self.round(forged), 10, "the second mechanical round waits on him")
        self.assertIn("asked for fixes a second time", self.program.waits.read_text("utf-8"))

    def test_a_desk_entry_his_words_cannot_find_at_its_line_is_mechanical(self):
        write(self.program.desk_answers, DESK + '- "whatever" (deadbeef:L1)\n- "leave B for after A ships" (1a2b3c4d:L131)\n')
        self.assertFalse(self.his('- x: "whatever" (deadbeef:L1)\n'), "no transcript holds it")
        self.assertFalse(self.his('- x: "leave B for after A ships" (1a2b3c4d:L131)\n'), "his words, another line")
        self.assertTrue(self.his('- x: "leave B for after A ships" (1a2b3c4d:L120)\n'))
        (self.root / "no-factory" / "skills" / "factory-core" / "scripts" / "his_words.py").unlink()
        self.assertFalse(self.his('- x: "leave B for after A ships" (1a2b3c4d:L120)\n'), "no his_words.py: no")

    def test_his_words_runs_time_limited(self):
        import subprocess
        from unittest import mock

        from ship.chain import his_words_holds

        with mock.patch("ship.chain.subprocess.run", side_effect=subprocess.TimeoutExpired("x", 1)) as run:
            self.assertFalse(his_words_holds("leave B", "1a2b3c4d:L120", self.settings_, "qmx"))
        self.assertEqual(run.call_args.kwargs["timeout"], self.settings_.his_words_timeout_s)


class RoleSettings(RepoCase):
    """Item 6: grounding and plan-review may run factory scripts; the verdict role only check_plan.py; inside
    the D-L22 allow-list."""

    def setUp(self):
        super().setUp()
        self.factory = self.root / "factory"
        from ship.tests.fixture import set_setting

        set_setting(self.program.dir, f"factory_home = {json.dumps(str(self.factory))}")

    def hook(self, role, command, env=None):
        import subprocess
        import sys

        from ship.launch import KIT

        event = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": str(self.root)}
        full = {k: v for k, v in os.environ.items() if not k.startswith("SHIP_")}
        full.update({"SHIP_ROLE": role, **(env or {})})
        done = subprocess.run([sys.executable, str(KIT), "hook", "--program", str(self.program.dir)], env=full,
                              input=json.dumps(event), capture_output=True, text=True, timeout=60)
        return done.returncode, done.stderr.strip()

    def test_the_hook_lets_grounding_and_plan_review_run_scripts_and_the_verdict_only_check_plan(self):
        plan = self.factory / "skills" / "factory-core" / "scripts" / "check_plan.py"
        chain = self.factory / "skills" / "factory-core" / "scripts" / "check_chain.py"
        census = self.factory / "skills" / "audit-area" / "scripts" / "census.py"
        fix = self.program.dir.parent / f"{self.program.dir.name}-fix-A"
        for role in ("grounding", "plan-review"):
            self.assertEqual(self.hook(role, f'python "{chain}" "{self.program.dir}" --stage handoff'), (0, ""), role)
            self.assertEqual(self.hook(role, f'python "{census}" qmb')[0], 2, f"{role}: census is not on its list")
        env = {"SHIP_STOP": "A"}
        from ship.launch import KIT

        self.assertEqual(self.hook("verdict", f'python "{plan}" "{fix}" "{KIT}"', env), (0, ""))
        self.assertEqual(self.hook("verdict", f'python "{plan}" "{fix}" "{self.root}"', env)[0], 2,
                         "check_plan.py imports the kit from its second argument: only this kit")
        rc, why = self.hook("verdict", f'python "{census}" qmb', env)
        self.assertEqual(rc, 2, "the verdict runs check_plan.py and nothing else of the factory's")
        self.assertIn("check_plan.py", why)
        other = self.factory / "skills" / "funnel" / "scripts" / "check_plan.py"
        self.assertEqual(self.hook("verdict", f'python "{other}"', env)[0], 2, "only factory-core's check_plan.py")
        self.assertEqual(self.hook("verdict", f'python -c "print(1)" "{plan}"', env)[0], 2)
        self.assertEqual(self.hook("reader", f'python "{plan}"', {"SHIP_NOTES": str(self.root / "n.md")})[0], 2)

    def test_the_settings_files_allow_the_same(self):
        import tomllib

        from ship.launch import ROLES_DIR

        def allow(name):
            return json.loads((ROLES_DIR / name).read_text("utf-8"))["permissions"]["allow"]

        from ship.hook import ROLE_SCRIPTS

        roles = tomllib.loads((ROLES_DIR / "roles.toml").read_text("utf-8"))
        for role, row in roles.items():
            granted = [a for a in allow(row["settings"]) if "/skills/" in a]
            self.assertNotIn("Bash(python */skills/*/scripts/*.py*)", granted, f"{role}: no script wildcard")
            for script in ROLE_SCRIPTS.get(role, ()):
                self.assertIn(f"Bash(python */skills/{script}*)", granted, f"{role}: {script}")
            names = {a.split("/skills/")[1].split("*")[0].rstrip('"') for a in granted}
            shared = {s for r, other in roles.items() if other["settings"] == row["settings"]
                      for s in ROLE_SCRIPTS.get(r, ())}
            self.assertLessEqual(names, shared, f"{role}: {row['settings']} allows only its roles' scripts")
        self.assertEqual([a for a in allow(roles["reader"]["settings"]) if "/skills/" in a], [],
                         "readers run no factory script")
        verdict = allow(roles["verdict"]["settings"])
        self.assertIn("Bash(python */skills/factory-core/scripts/check_plan.py*)", verdict)
        self.assertEqual([a for a in allow(roles["grounding"]["settings"]) if "/skills/" in a],
                         [f'Bash(python {q}*/skills/factory-core/scripts/{n}.py{q}*)' for n in
                          ("his_words", "check_chain", "check_plan") for q in ("", '"')])
        self.assertEqual(roles["grounding"]["settings"], "grounding.json")
        self.assertEqual(json.loads((ROLES_DIR / "grounding.json").read_text("utf-8"))["hooks"],
                         json.loads((ROLES_DIR / "reader.json").read_text("utf-8"))["hooks"], "the same guard")



class Generators(RepoCase):
    """U17b: `[generators]` in the profile contract: the baselines prune and the contract dump, run at merge."""

    def test_the_default_profile_holds_the_prune_and_the_contract_dump(self):
        import sys

        from ship import project_profile

        gens = project_profile.load(None, load_settings(self.program.dir))["generators"]
        self.assertEqual(gens["ci/baselines/*"], [sys.executable, "tools/ci/qci.py", "ratchet", "--prune"])
        self.assertEqual(gens["contracts/*.json"][-1], ["uv", "run", "--frozen", "python", "tools/contract_dump.py"])
        self.assertEqual(project_profile.generator_commands(["python", "x.py"]), [[sys.executable, "x.py"]])

    def test_merge_runs_each_generator_in_order_commits_its_files_and_skips_a_missing_script(self):
        from ship.merge import Merge

        prune = "import pathlib\np = pathlib.Path('ci/baselines/vulture.txt')\np.write_text('# h\\n', 'utf-8')\n"
        write(self.repo / "tools" / "ci" / "qci.py", prune)
        write(self.repo / "ci" / "baselines" / "vulture.txt", "# h\nold|vulture|gone\nold|vulture|gone2\n")
        tip = self.commit("baselines")
        copy = self.root / "gen-copy"
        settings = load_settings(self.program.dir)
        checkout_copy(self.repo, copy, tip, settings)
        job = Merge(self.program, "A", settings)
        from ship import project_profile

        job.profile = {"generators": {"ci/baselines/*": ["python", "tools/ci/qci.py", "ratchet", "--prune"],
                                      "contracts/*.json": [["python", "tools/first.py"], ["python", "tools/contract_dump.py"]]}}
        self.assertEqual(project_profile.generator_commands(job.profile["generators"]["contracts/*.json"])[0][1],
                         "tools/first.py")
        job.generate(copy)
        self.assertEqual(sh(copy, "git", "log", "-1", "--format=%s"), "ratchet: prune 2 rows")
        self.assertEqual(sh(copy, "git", "show", "--name-only", "--format=", "HEAD"), "ci/baselines/vulture.txt")
        self.assertIn("GENERATOR contracts/*.json skipped: tools/first.py is not in the repo", job.lines)
        drop_copy(self.repo, copy, settings)


if __name__ == "__main__":
    unittest.main()
