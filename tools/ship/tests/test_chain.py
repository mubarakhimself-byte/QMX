"""ship chain, the conveyor, end to end on a scratch repo: real git, fake `claude` for every worker, fake `gh`
that runs deep runs at once, gates PRs and merges them in the bare remote. No real Claude run, no real merge."""

import json
import os
import shutil
import subprocess
import sys
import textwrap
import time
import unittest
from pathlib import Path
from unittest import mock

from ship import phase
from ship import state as st
from ship.launch import KIT
from ship.layout import Program
from ship.settings import Settings, load_settings
from ship.tests.fixture import BRIEF, PY, RepoCase, sh, write

FAKE_CLAUDE = Path(__file__).resolve().parent / "fake_claude.py"
KEYS = ("PROGRAM", "SHIP")
SOURCE = "def {slice}():\n    return '{slice}'\n"
EVIDENCE = {f"{{evidence}}/{name}": (f"{name}\n" + ("TRACE: {slice} -> P1 -> S1\n" if name == "pr.md" else "")
                                     + "END {head} {dispatch}\n")
            for name in ("how.md", "red.log", "report.md", "pr.md")}
BUILDER = {"match": "builder:", "steps": [{"write": {"pkg/{slice}.py": SOURCE}}, {"commit": "{slice}: work"},
                                          {"push": True}, {"file": EVIDENCE}], "reply": "READY {head}"}
PLAN_CLEAN = {"match": "plan-review:", "steps": [{"file": {"{program}/plan-review/REVIEW.md":
                                                            "Fine.\n\nRESULT: CLEAN\nEND plan-review x\n"}}],
              "reply": "DONE {program}/plan-review/REVIEW.md"}
READER = {"match": "reader:", "steps": [{"file": {"{notes}": "Nothing found.\nDONE\n"}}], "reply": "DONE {notes}"}
VERDICT = {"match": "verdict:", "steps": [{"file": {
    "{program}/stop-review/{stop}/REVIEW.md": "VERDICT: CLEAN\n\nEND {tip} checkpoint-{stop}-round-1\n",
    "{program}/merge/{stop}-pr.md": "Stop {stop}.\n\nShipped by Mubarak.\n"}}],
    "reply": "DONE {program}/stop-review/{stop}/REVIEW.md"}
SLICES = ("| id | name | stop | depends on | files | size |\n|---|---|---|---|---|---|\n"
          "| a1 | Slice a1 | A | - | pkg/a1.py | S |\n| b1 | Slice b1 | B | - | pkg/b1.py | S |\n")


def index(base: str) -> str:
    return (f"project: qmx\nprogram: program\nkind: feature\nparent: null\nbuild_branch: build/t\n"
            f"parent_tip: {base}\ncore_sentence: \"a1 and b1 exist\"\n"
            "budget:\n  core: 2\n  later: 0\n  checkpoints: 2\n"
            "gates:\n  cut: {by: him, at: 2026-11-14, source: \"t:1\", advance: no}\n"
            "  plan: {by: him, at: 2026-11-14, source: \"t:2\", advance: yes}\n  go: null\n"
            "stop_points:\n  - id: A\n    tier: core\n    handoff: ready\n  - id: B\n    tier: core\n    handoff: ready\n"
            "chains:\n  - ask: S1\n    verdict: core\n    plan: [S1.a]\n    arch: [A1]\n    slices: [a1, b1]\n"
            "abandoned: null\n")


class ChainCase(RepoCase):
    def setUp(self):
        super().setUp()
        from ship import records

        write(self.repo / ".github" / "workflows" / "qmx-ci.yml", "name: qmx-ci\n")
        self.commit("ci: workflow")
        sh(self.repo, "git", "push", "-q", "origin", "main", f"main:refs/heads/{self.build_branch}")
        self.base = self.tip()
        self.plans = self.root / "plans"
        records.init(self.repo, self.plans, "origin", Settings())
        shutil.move(str(self.program.dir), str(self.plans / "program"))
        self.program = Program(self.plans / "program")
        self.program.state.unlink()
        write(self.program.slices_md, SLICES)
        for sid in ("a1", "b1"):
            write(self.program.brief(sid), BRIEF)
        write(self.program.project_file, index(self.base))
        self.factory = self.root / "factory"
        for name in ("check_chain.py", "check_plan.py"):
            write(self.factory / "skills" / "factory-core" / "scripts" / name, "print('PASS stub')\n")
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
        for name in ("BUILDER.md", "READER.md", "VERDICT.md", "PLAN-REVIEW.md", "PLANNER-FIX.md", "GROUNDING.md"):
            write(prompts / name, f"{name} for {{PROGRAM}} with {{SHIP}}\n")
        self.script = self.root / "claude-script.json"
        self.rules(PLAN_CLEAN, BUILDER, READER, VERDICT)
        toml = self.program.dir / "ship.toml"
        toml.write_text(toml.read_text("utf-8").replace('ci = "local"', 'ci = "github"') + textwrap.dedent(f"""\
            claude = [{json.dumps(PY)}, {json.dumps(str(FAKE_CLAUDE))}]
            prompt_dir = {json.dumps(str(prompts))}
            factory_home = {json.dumps(str(self.factory))}
            internet_probe = ""
            chain_poll_s = 0.2
            worker_env_extra = ["FAKE_CLAUDE_SCRIPT"]
            ci_gate_base = "main"
            ci_poll_s = 0.2
            ci_find_s = 5
            ci_wait_timeout_s = 120
            ci_slice_grace_s = 0
            arm_preflight = false
            """), "utf-8")
        self.flag("fake-gh-auto")

    def flag(self, name):
        common = sh(self.repo, "git", "rev-parse", "--git-common-dir")
        (Path(common) if Path(common).is_absolute() else self.repo / common).joinpath(name).write_text("x")

    def rules(self, *rules):
        self.script.write_text(json.dumps(list(rules)), "utf-8")

    def env(self, **more):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SHIP_")}
        env.update(FAKE_CLAUDE_SCRIPT=str(self.script), SHIP_FAKE_MAINS="1", **more)
        return env

    def chain(self, *args, timeout=600, program=None, **env):
        done = subprocess.run([PY, str(KIT), "chain", "--program", str((program or self.program).dir), *args],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", env=self.env(**env),
                              stdin=subprocess.DEVNULL, timeout=timeout)
        self.out = done.stdout + done.stderr
        return done.returncode

    def start(self, *args, **env):
        log = open(self.root / "chain-bg.log", "w", encoding="utf-8")
        self.addCleanup(log.close)
        proc = subprocess.Popen([PY, str(KIT), "chain", "--program", str(self.program.dir), *args], stdout=log,
                                stderr=subprocess.STDOUT, env=self.env(**env), stdin=subprocess.DEVNULL)
        self.addCleanup(lambda: proc.poll() is None and proc.kill())
        return proc

    def until(self, check, timeout=240, what=""):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if check():
                return
            time.sleep(0.2)
        raise AssertionError(f"timed out waiting for {what}")

    def phase(self):
        return phase.read(self.program, load_settings(self.program.dir))

    def assert_done(self):
        self.assertEqual(st.load(self.program).merged, ["A", "B"])
        sh(self.repo, "git", "fetch", "-q", "origin")
        files = sh(self.repo, "git", "ls-tree", "-r", "--name-only", "origin/main").splitlines()
        self.assertIn("pkg/a1.py", files)
        self.assertIn("pkg/b1.py", files)
        subjects = sh(self.repo, "git", "log", "--first-parent", "--format=%s", "origin/build/t").splitlines()
        for sid in ("a1", "b1"):
            self.assertEqual(sum(s.startswith(f"{sid}: ") for s in subjects), 1, subjects)
        for stop in ("A", "B"):
            self.assertIn("MERGED", self.program.merge_note(stop).read_text("utf-8"))
            self.assertTrue((self.program.dir / "docs" / f"{stop}.json").exists())
        self.assertEqual(self.phase()["next"], "done")
        self.assertEqual(phase.phase_json(self.program)["status"], "done")
        self.assertFalse(self.program.chain_lock.exists())


class EndToEnd(ChainCase):
    def test_two_checkpoints_go_from_review_to_done_in_one_run(self):
        self.assertEqual(self.chain(), 0, self.out)
        self.assert_done()
        self.assertEqual(self.phase()["status"], "done")
        index = self.program.project_file.read_text("utf-8")
        self.assertIn('go: {by: him, at:', index)
        self.assertIn('source: "t:2", advance: yes}', index)
        self.assertIn("The conveyor's last word", self.program.report.read_text("utf-8"))

    def test_killed_after_each_activity_and_restarted_it_ends_the_same(self):
        kills = 0
        while True:
            rc = self.chain(SHIP_CHAIN_STOP_AFTER="any:1")
            if rc != 137:
                break
            kills += 1
            self.assertLess(kills, 40, self.out)
        self.assertEqual(rc, 0, self.out)
        self.assertGreaterEqual(kills, 8, "it was stopped after review, go, arm, both builds, reviews and merges")
        self.assert_done()


class Waits(ChainCase):
    def test_follow_exits_10_when_the_plan_reviewer_asks_questions(self):
        asks = {"match": "plan-review:", "steps": [{"file": {
            "{program}/plan-review/REVIEW.md": "RESULT: QUESTIONS\nEND plan-review x\n",
            "{program}/plan-review/QUESTIONS.md": "- [ ] Should a1 return its name? (recommended: yes)\n"}}],
            "reply": "DONE {program}/plan-review/QUESTIONS.md"}
        self.rules(asks)
        proc = self.start()
        self.assertEqual(self.chain("--follow"), 10, self.out)
        self.assertEqual(proc.wait(timeout=120), 10)
        self.assertIn("- [ ] Should a1 return its name?", self.program.waiting.read_text("utf-8"))
        self.assertIn("status: waits-on-him", self.out)

    def test_a_second_conveyor_on_a_running_program_exits_11(self):
        holder = subprocess.Popen([PY, "-c", "import time; time.sleep(60)"])
        self.addCleanup(holder.kill)
        self.program.chain_lock.write_text(json.dumps({"pid": holder.pid, "children": []}), "utf-8")
        self.assertEqual(self.chain(), 11, self.out)

    def test_stop_after_writes_the_file_and_starts_nothing(self):
        self.assertEqual(self.chain("--stop-after", "A"), 0, self.out)
        self.assertEqual((self.program.dir / "STOP-AFTER").read_text("utf-8").strip(), "A")
        self.assertFalse(self.program.chain_lock.exists())


class ResumeAll(ChainCase):
    def test_only_the_program_whose_conveyor_is_dead_is_started(self):
        alive, dead = Program(self.plans / "alive"), Program(self.plans / "dead")
        for program in (alive, dead):
            write(program.dir / "PROGRAM.yaml", "project: qmx\nprogram: x\nkind: feature\n")
            write(program.dir / "ship.toml", f"[settings]\nfactory_home = {json.dumps(str(self.factory))}\n")
            phase.set_phase(program, "build", "running", "test")
        holder = subprocess.Popen([PY, "-c", "import time; time.sleep(60)"])
        self.addCleanup(holder.kill)
        alive.chain_lock.write_text(json.dumps({"pid": holder.pid, "children": []}), "utf-8")
        gone = subprocess.Popen([PY, "-c", "pass"])
        gone.wait()
        dead.chain_lock.write_text(json.dumps({"pid": gone.pid, "children": []}), "utf-8")
        done = subprocess.run([PY, str(KIT), "chain", "--resume-all", "--plans", str(self.plans)], capture_output=True,
                              text=True, env=self.env(), stdin=subprocess.DEVNULL, timeout=120)
        out = done.stdout + done.stderr
        self.assertEqual(done.returncode, 0, out)
        self.assertIn("RUNNING alive", out)
        self.assertIn("STARTED dead: DETACHED pid", out)
        self.assertNotIn("STARTED alive", out)
        self.assertNotIn("STARTED program", out, "phase.json does not say running there")
        self.until(lambda: (dead.dir / "chain.log").exists() and "NEXT" in (dead.dir / "chain.log").read_text("utf-8"),
                   what="the detached conveyor's log")


class Abandon(ChainCase):
    def test_abandon_mid_build_leaves_nothing_running_and_phase_says_abandoned(self):
        self.rules(PLAN_CLEAN, {"match": "builder:", "kind": "hang"}, READER, VERDICT)
        proc = self.start()
        self.until(lambda: self.program.chain_lock.exists()
                   and json.loads(self.program.chain_lock.read_text("utf-8") or "{}").get("children"),
                   what="a builder seat")
        children = json.loads(self.program.chain_lock.read_text("utf-8"))["children"]
        done = subprocess.run([PY, str(KIT), "abandon", "--program", str(self.program.dir), "--why", "he changed his mind"],
                              capture_output=True, text=True, env=self.env(), stdin=subprocess.DEVNULL, timeout=120)
        self.assertEqual(done.returncode, 0, done.stdout + done.stderr)
        proc.wait(timeout=60)
        from ship.proc import pid_alive

        for child in children:
            self.until(lambda: not pid_alive(int(child["pid"])), timeout=30, what=f"{child} to stop")
        p = self.phase()
        self.assertEqual((p["next"], p["status"]), ("done", "abandoned"))
        self.assertIn("he changed his mind", (self.program.notes_dir / "ABANDONED.md").read_text("utf-8"))
        armed = self.program.armed.read_text("utf-8") if self.program.armed.exists() else "Nothing is armed."
        self.assertTrue("Nothing is armed." in armed or "torn down" in armed, armed)
        self.assertFalse(self.program.chain_lock.exists())


class Task(unittest.TestCase):
    def test_the_task_runs_resume_all_at_logon_and_every_15_minutes_and_registers_nothing_by_default(self):
        from ship import scheduled_task

        plans = Path("D:/QMX-worktrees/plans")
        settings = Settings(factory_home=str(Path(__file__).resolve().parent / "no-such-factory"))
        xml = scheduled_task.task_xml(plans, user="him")
        self.assertIn("<LogonTrigger><Enabled>true</Enabled><UserId>him</UserId></LogonTrigger>", xml)
        self.assertIn("<Interval>PT15M</Interval>", xml)
        self.assertIn("<RunLevel>LeastPrivilege</RunLevel>", xml)
        self.assertIn(f'chain --resume-all --plans "{plans}"', xml)
        self.assertIn(str(KIT), xml)
        with mock.patch("subprocess.run") as run:
            rc, lines = scheduled_task.install(plans, settings)
            self.assertFalse(run.called)
        self.assertEqual(rc, 0)
        self.assertIn("WOULD RUN schtasks /Create /F /TN factory-resume /XML", "\n".join(lines))
        self.assertIn("UNDO schtasks /Delete /F /TN factory-resume", "\n".join(lines))
        self.assertEqual(scheduled_task.install_commands(Path("t.xml")),
                         [["schtasks", "/Create", "/F", "/TN", "factory-resume", "/XML", "t.xml"]])
        with mock.patch("subprocess.run") as run:
            rc, lines = scheduled_task.remove(settings)
            self.assertFalse(run.called)
        self.assertEqual(lines[0], "WOULD RUN schtasks /Delete /F /TN factory-resume")
