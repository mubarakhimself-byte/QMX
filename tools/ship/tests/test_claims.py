"""Claims across programs, and two merges in turn: real git, fake `claude`, fake `gh`, one plans worktree
holding two programs on one remote (FACTORY-DESIGN 3.7, rows 44 and 46 to 50)."""

import json
import os
import shutil
import subprocess
import textwrap
from pathlib import Path

from ship import state as st
from ship.claims import Claims
from ship.launch import KIT
from ship.layout import Program
from ship.plan import init_state
from ship.settings import Settings
from ship.state import Status
from ship.tests.fixture import BRIEF, FAKE_GH, PY, RepoCase, sh, write

FAKE_CLAUDE = Path(__file__).resolve().parent / "fake_claude.py"
PROMPT = "Build {SLICE} {KIND} {ATTEMPT} {RESTART} {WORKTREE} {BRANCH} {PARENT} {EVIDENCE} {DISPATCH_ID} {PROGRAM} " \
         "{WORKTREE_ROOT} {SHIP} {LEFTOVER_LINE} {LEFTOVER} {RESTART_OF} {FIX_REASON} {FIX_PATHS}\n"
SOURCE = "def {slice}():\n    return '{slice}'\n"
EVIDENCE = {f"{{evidence}}/{name}": (f"{name}\n" + ("TRACE: {slice} -> P1 -> S1\n" if name == "pr.md" else "")
                                     + "END {head} {dispatch}\n")
            for name in ("how.md", "red.log", "report.md", "pr.md")}
HAPPY = {"match": "builder:", "steps": [{"write": {"pkg/{slice}.py": SOURCE}}, {"commit": "{slice}: work"},
                                        {"push": True}, {"file": EVIDENCE}], "reply": "READY {head}"}


def table(rows):
    """rows: (id, file)."""
    body = "".join(f"| {sid} | Slice {sid} | A | - | {path} | S |\n" for sid, path in rows)
    return "| id | name | stop | depends on | files | size |\n|---|---|---|---|---|---|\n" + body


class TwoPrograms(RepoCase):
    """p1 on build/t and p2 on build/u, both in one plans worktree with _records."""

    def setUp(self):
        super().setUp()
        from ship import records

        write(self.repo / ".github" / "workflows" / "qmx-ci.yml", "name: qmx-ci\n")
        self.commit("ci: workflow")
        sh(self.repo, "git", "push", "-q", "origin", "main", "main:refs/heads/build/t", "main:refs/heads/build/u")
        self.plans = self.root / "plans"
        records.init(self.repo, self.plans, "origin", Settings())
        prompts = self.root / "prompts"
        write(prompts / "BUILDER.md", PROMPT)
        self.factory = self.root / "factory"
        self.script = self.root / "claude-script.json"
        self.script.write_text(json.dumps([HAPPY]), "utf-8")
        shutil.move(str(self.program.dir), str(self.plans / "p1"))
        self.p1 = Program(self.plans / "p1")
        self.p2 = Program(self.plans / "p2")
        shutil.copytree(self.p1.dir, self.p2.dir)
        for program in (self.p1, self.p2):
            toml = program.dir / "ship.toml"
            extra = textwrap.dedent(f"""\
                claude = [{json.dumps(PY)}, {json.dumps(str(FAKE_CLAUDE))}]
                prompt_dir = {json.dumps(str(prompts))}
                factory_home = {json.dumps(str(self.factory))}
                internet_probe = ""
                chain_poll_s = 0.2
                worker_env_extra = ["FAKE_CLAUDE_SCRIPT"]
                ci_gate_base = "main"
                ci_poll_s = 0.2
                ci_find_s = 5
                ci_wait_timeout_s = 60
                """)
            toml.write_text(toml.read_text("utf-8") + extra, "utf-8")

    def use(self, program, branch, rows):
        write(program.slices_md, table(rows))
        for sid, _ in rows:
            write(program.brief(sid), BRIEF)
        program.state.unlink(missing_ok=True)
        init_state(program.dir, self.repo, branch, self.wt_root, "origin")

    def env(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SHIP_")}
        env.update(FAKE_CLAUDE_SCRIPT=str(self.script), SHIP_FAKE_MAINS="1")
        return env

    def ship(self, program, *args, timeout=400):
        done = subprocess.run([PY, str(KIT), *args, "--program", str(program.dir)], capture_output=True, text=True,
                              encoding="utf-8", errors="replace", env=self.env(), stdin=subprocess.DEVNULL,
                              timeout=timeout)
        self.out = done.stdout + done.stderr
        return done.returncode

    def start(self, program, *args):
        log = open(self.root / f"{program.dir.name}-{args[0]}.log", "w", encoding="utf-8")
        self.addCleanup(log.close)
        proc = subprocess.Popen([PY, str(KIT), *args, "--program", str(program.dir)], stdout=log,
                                stderr=subprocess.STDOUT, env=self.env(), stdin=subprocess.DEVNULL)
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        return proc

    def claims(self):
        return Claims(self.plans, Settings())


class Build(TwoPrograms):
    def test_disjoint_programs_build_and_land_side_by_side(self):
        self.use(self.p1, "build/t", [("a1", "pkg/a1.py"), ("a2", "pkg/a2.py")])
        self.use(self.p2, "build/u", [("b1", "pkg/b1.py"), ("b2", "pkg/b2.py")])
        runs = [self.start(self.p1, "run"), self.start(self.p2, "run")]
        self.assertEqual([r.wait(timeout=600) for r in runs], [0, 0],
                         [(self.root / f"{p}-run.log").read_text("utf-8")[-2000:] for p in ("p1", "p2")])
        for program, ids in ((self.p1, ("a1", "a2")), (self.p2, ("b1", "b2"))):
            state = st.load(program)
            self.assertEqual({state.slices[i].status for i in ids}, {Status.LANDED})
        live = {(r.program, r.pattern) for r in self.claims().live()}
        self.assertEqual(live, {("p1", "pkg/a1.py"), ("p1", "pkg/a2.py"), ("p2", "pkg/b1.py"), ("p2", "pkg/b2.py")})

    def test_only_the_slice_naming_a_claimed_file_waits_and_starts_once_released(self):
        self.use(self.p1, "build/t", [("x1", "pkg/y1.py")])  # p1 also writes the file p2's y1 names
        self.use(self.p2, "build/u", [("y1", "pkg/y1.py"), ("y2", "pkg/y2.py")])
        self.assertEqual(self.ship(self.p1, "claims", "claim"), 0, self.out)
        self.assertIn("CLAIM p1 pkg/y1.py", self.out)
        self.assertEqual(self.ship(self.p2, "run", "--once"), 0, self.out)
        self.assertIn("WAIT y1 blocked-by claim p1", self.out)
        state = st.load(self.p2)
        self.assertEqual((state.slices["y1"].status, state.slices["y1"].attempts), (Status.PENDING, 0))
        self.assertEqual(state.slices["y2"].status, Status.LANDED)
        self.ship(self.p2, "status")
        self.assertIn("WAIT y1 blocked-by claim p1", self.out)
        self.assertEqual(self.ship(self.p1, "claims", "release"), 0, self.out)
        self.assertEqual(self.ship(self.p2, "run"), 0, self.out)
        state = st.load(self.p2)
        self.assertEqual(state.slices["y1"].status, Status.LANDED)
        self.assertTrue((self.p2.evidence("y1", 1) / "facts.log").exists(), "its facts ran at dispatch")

    def test_the_claims_of_a_deleted_program_are_swept(self):
        claims = self.claims()
        claims.claim("gone", ["pkg/gone.py"])
        self.assertEqual([r.program for r in claims.live()], ["gone"])
        self.assertEqual(claims.sweep(), ["SWEPT gone: 1 rows (gone)"])
        self.assertEqual(claims.live(), [])
        self.assertIn("claims: gone releases 1 patterns", sh(self.plans, "git", "log", "-1", "--format=%s"))

    def test_shared_generated_files_are_never_claimed(self):
        claims = Claims(self.plans, Settings(), ["uv.lock", "**/uv.lock"])
        claims.claim("p1", ["pkg/uv.lock", "uv.lock", "pkg/a.py"])
        self.assertEqual([r.pattern for r in claims.live()], ["pkg/a.py"])


class Merges(TwoPrograms):
    def reviewed(self, program, branch, sid):
        """A landed, reviewed, deep-run-green checkpoint A of one slice."""
        self.use(program, branch, [(sid, f"pkg/{sid}.py")])
        sh(self.repo, "git", "fetch", "-q", "origin")
        sh(self.repo, "git", "checkout", "-q", "-B", f"w-{sid}", f"origin/{branch}")
        base = sh(self.repo, "git", "rev-parse", "HEAD")
        write(self.repo / "pkg" / f"{sid}.py", SOURCE.format(slice=sid))
        tip = self.commit(f"{sid}: Slice {sid}")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{branch}")
        with st.locked(program) as state:
            sl = state.slices[sid]
            sl.status, sl.landed_sha, sl.head = Status.LANDED, tip, tip
            state.ci["deep"] = {"tip": tip, "level": "deep", "run_id": "1", "url": "u", "result": "green"}
        write(program.stop_note("A"), json.dumps({"stop": "A", "from": base, "tip": tip, "landed": [sid], "parked": []}))
        write(program.stop_review("A") / "REVIEW.md", f"VERDICT: CLEAN\n\nEND {tip} checkpoint-A-round-1\n")
        write(program.dir / "merge" / "A-pr.md", "Stop A.\n")
        toml = program.dir / "ship.toml"
        toml.write_text(toml.read_text("utf-8").replace('ci = "local"', 'ci = "github"'), "utf-8")
        self.assertEqual(self.ship(program, "claims", "claim"), 0, self.out)
        return tip

    def test_two_merges_take_turns_and_the_second_carries_the_first(self):
        common = sh(self.repo, "git", "rev-parse", "--git-common-dir")
        (Path(common) if Path(common).is_absolute() else self.repo / common).joinpath("fake-gh-auto").write_text("x")
        tips = {"p1": self.reviewed(self.p1, "build/t", "a1"), "p2": self.reviewed(self.p2, "build/u", "b1")}
        procs = {"p1": self.start(self.p1, "merge", "A"), "p2": self.start(self.p2, "merge", "A")}
        codes = {name: proc.wait(timeout=300) for name, proc in procs.items()}
        self.assertIn(0, codes.values(), codes)
        order = []
        for name in sorted(codes, key=lambda n: codes[n]):
            program = self.p1 if name == "p1" else self.p2
            for _ in range(20):
                if codes[name] == 0:
                    break
                self.assertEqual(codes[name], 11, (self.root / f"{name}-merge.log").read_text("utf-8"))
                codes[name] = self.ship(program, "merge", "A")
            self.assertEqual(codes[name], 0, self.out)
            order.append(name)
        first, second = order
        sh(self.repo, "git", "fetch", "-q", "origin")
        branch = {"p1": "build/t", "p2": "build/u"}
        second_tip = sh(self.repo, "git", "rev-parse", f"origin/{branch[second]}")
        self.assertEqual(sh(self.repo, "git", "log", "-1", "--format=%s", second_tip),
                         f"merge: main into {branch[second]} for stop A")
        self.assertEqual(subprocess.run(["git", "merge-base", "--is-ancestor", tips[first], second_tip],
                                        cwd=self.repo).returncode, 0, "the second carries the first's code")
        runs = json.loads((Path(common) if Path(common).is_absolute() else self.repo / common)
                          .joinpath("fake-gh-runs.json").read_text("utf-8"))["runs"]
        self.assertTrue(any(r["event"] == "workflow_dispatch" and r["headSha"] == second_tip for r in runs),
                        "the second had its own deep run on its merge commit")
        main = sh(self.repo, "git", "rev-parse", "origin/main")
        for tip in tips.values():
            self.assertEqual(subprocess.run(["git", "merge-base", "--is-ancestor", tip, main], cwd=self.repo).returncode, 0)
        self.assertEqual([r.program for r in self.claims().read() if r.pattern.endswith(("a1.py", "b1.py"))],
                         ["p1", "p2"])
        self.assertEqual(self.claims().live(), [], "each merge released its stop's claims")
