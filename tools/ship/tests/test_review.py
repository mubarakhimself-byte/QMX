"""ship trace and ship review on a scratch repo: real git, fake `claude` scripting each reader's notes and
the verdict file, the local deep run (nightly and quality) on the fixture's package. Also the hook's
per-role write roots (D-L16)."""

import json
import os
import subprocess
import sys
from pathlib import Path

from ship import state as st
from ship.launch import KIT
from ship.state import Status
from ship.tests.fixture import BRIEF, PY, RepoCase, sh, write

FAKE_CLAUDE = Path(__file__).resolve().parent / "fake_claude.py"
READER = "Walk {WALK} as {NAME} ({ELEMENT}; {SLICES}) of {PROGRAM} stop {STOP} round {ROUND} in {CHECKOUT} " \
         "({REPO}) {FROM}..{TIP}. Map {MAP}. Notes {NOTES}. Rules {RULES} {REVIEW_RULES}. Kit {SHIP}.\n"
VERDICT = "Judge {PROGRAM} stop {STOP} round {ROUND} {REPO} {FROM}..{TIP} {MAP} {NOTES} {DEEP_SUMMARY} " \
          "{QUALITY_SUMMARY} {CI_SUMMARY} {DEEP_RESULT} {TRACE_FAILS} {VERDICT_FILE} {END_LINE} {PR_BODY} " \
          "{FIX_PROGRAM} {CORE_SENTENCE} {LAST_CORE} {RULES} {REVIEW_RULES} {SHIP}\n"
NOTES_DONE = {"match": "reader:", "steps": [{"file": {"{notes}": "Nothing found.\nDONE\n"}}], "reply": "DONE {notes}"}
FAULTS_DONE = {"match": "fault-reader:", "steps": [{"file": {"{notes}": "No fault.\nDONE\n"}}],
               "reply": "DONE {notes}"}
SLICES = ("| id | name | stop | depends on | files | size |\n|---|---|---|---|---|---|\n"
          "| a1 | Slice a1 | A | - | pkg/a1.py | S |\n| a2 | Slice a2 | A | - | pkg/a2.py | S |\n")
SCENARIO_BRIEF = BRIEF + "\n## 7a. Edge-case scenarios\n\n- E1 a1 returns its name: it does (test: pkg/tests/test_a1.py::test_a1)\n"
JUNIT = ('<?xml version="1.0"?><testsuites><testsuite name="pytest"><testcase classname="pkg.tests.test_a1" '
         'name="test_a1" time="0.1"/></testsuite></testsuites>\n')


def index(name: str, base: str, extra: str = "") -> str:
    return (f"project: qmx\nprogram: {name}\nkind: feature\nparent: null\nbuild_branch: build/t\n"
            f"parent_tip: {base}\ncore_sentence: \"a1 and a2 exist\"\n"
            "budget:\n  core: 2\n  later: 0\n  checkpoints: 1\n"
            "gates:\n  cut: {by: him, at: 2026-11-14, source: \"x\", advance: no}\n"
            "  plan: {by: him, at: 2026-11-14, source: \"x\", advance: yes}\n"
            "  go: {by: him, at: 2026-11-14, source: \"x\", advance: yes}\n"
            "stop_points:\n  - id: A\n    tier: core\n    done_when: \"both exist\"\n    handoff: ready\n"
            "chains:\n  - ask: S1\n    verdict: core\n    plan: [S1.a]\n    arch: [A1]\n    slices: [a1, a2]\n"
            + extra)


def fix_index(parent: str, tip: str) -> str:
    return (f"project: qmx\nprogram: {parent}-fix-A\nkind: fix\nparent: {parent}\nbuild_branch: build/t\n"
            f"parent_tip: {tip}\ngates:\n  go: {{by: stop-review, at: 2026-11-14, "
            "source: \"stop-review/A/REVIEW.md\", advance: yes}\nstop_points:\n  - id: A\n    tier: core\n")


class ReviewCase(RepoCase):
    def setUp(self):
        super().setUp()
        write(self.program.slices_md, SLICES)
        write(self.program.brief("a1"), SCENARIO_BRIEF)
        write(self.program.brief("a2"), BRIEF)
        self.program.state.unlink()
        from ship.plan import init_state

        init_state(self.program.dir, self.repo, self.build_branch, self.wt_root, "origin")
        self.base = self.tip()
        self.factory = self.root / "factory"
        write(self.factory / "skills" / "factory-core" / "scripts" / "check_plan.py",
              "import sys\nprint('PASS stub check_plan', sys.argv[1])\n")
        prompts = self.root / "prompts"
        write(prompts / "READER.md", READER)
        write(prompts / "VERDICT.md", VERDICT)
        self.script_path = self.root / "claude-script.json"
        for line in (f"claude = [{json.dumps(PY)}, {json.dumps(str(FAKE_CLAUDE))}]",
                     f"prompt_dir = {json.dumps(str(prompts))}", f"factory_home = {json.dumps(str(self.factory))}",
                     'internet_probe = ""', "chain_poll_s = 0.2", 'worker_env_extra = ["FAKE_CLAUDE_SCRIPT"]'):
            self.setting(line)
        self.land_two()
        write(self.program.project_file, index(self.program.dir.name, self.base))

    def land_two(self):
        """a1 and a2 landed on build/t as `ship land` would, and the stop note written."""
        sh(self.repo, "git", "fetch", "-q", "origin")
        sh(self.repo, "git", "checkout", "-q", "-B", "work", f"origin/{self.build_branch}")
        shas = {}
        for sid in ("a1", "a2"):
            write(self.repo / "pkg" / f"{sid}.py", f"def {sid}():\n    return '{sid}'\n")
            shas[sid] = self.commit(f"{sid}: Slice {sid}")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        state = st.load(self.program)
        for sid, sha in shas.items():
            sl = state.slices[sid]
            sl.status, sl.landed_sha, sl.head, sl.attempts = Status.LANDED, sha, sha, 1
        st.save(self.program, state)
        write(self.program.checks("a1", shas["a1"]) / "tests.junit.xml", JUNIT)
        self.stop_note(self.base, self.tip())

    def stop_note(self, base, tip, landed=("a1", "a2"), parked=()):
        write(self.program.stop_note("A"), json.dumps({"stop": "A", "from": base, "tip": tip, "landed": list(landed),
                                                       "parked": list(parked), "at": "2026-11-14T00:00:00+00:00"}))

    def rules(self, *rules):
        self.script_path.write_text(json.dumps(list(rules)), "utf-8")

    def verdict_rule(self, word, tip, round_=1, extra_files=None):
        name = "REVIEW.md" if round_ == 1 else "REVIEW-2.md"
        files = {f"{{program}}/stop-review/A/{name}": f"VERDICT: {word}\n\n- Important: x\n\n"
                                                        f"END {tip} checkpoint-A-round-{round_}\n"}
        files.update(extra_files or {})
        return {"match": "verdict:", "steps": [{"file": files}], "reply": f"DONE {{program}}/stop-review/A/{name}"}

    def ship(self, *args, timeout=300):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SHIP_")}
        env.update(FAKE_CLAUDE_SCRIPT=str(self.script_path), SHIP_FAKE_MAINS="1")
        done = subprocess.run([PY, str(KIT), *args, "--program", str(self.program.dir)], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", env=env, stdin=subprocess.DEVNULL,
                              timeout=timeout)
        self.out = done.stdout + done.stderr
        return done.returncode

    def calls(self, word):
        path = self.program.dir / "fake-claude.log"
        rows = [json.loads(x) for x in path.read_text("utf-8").splitlines()] if path.exists() else []
        return [r for r in rows if word in r["argv"][r["argv"].index("--name") + 1].split()]

    def waits(self):
        path = self.program.waits
        return [x for x in path.read_text("utf-8").splitlines() if x.startswith("- [ ]")] if path.exists() else []

    def stop_copies(self):
        listed = sh(self.repo, "git", "worktree", "list", "--porcelain")
        return [x for x in listed.splitlines() if x.startswith("worktree ") and "stop-" in x] + \
            [p.name for p in self.wt_root.glob("stop-*")]


class Clean(ReviewCase):
    def test_clean_returns_0_leaves_no_checkout_and_starts_no_fault_reader(self):
        self.rules(self.verdict_rule("CLEAN", self.tip()), NOTES_DONE)
        self.assertEqual(self.ship("review", "A"), 0, self.out)
        self.assertEqual(self.stop_copies(), [])
        names = sorted(r["argv"][r["argv"].index("--name") + 1] for r in self.calls("reader:"))
        self.assertEqual(names, [f"reader: program A chain", f"reader: program A element-A1"])
        self.assertEqual(self.calls("fault-reader:"), [])
        self.assertEqual(len(self.calls("verdict:")), 1)
        start = json.loads((self.program.stop_review("A") / "START.json").read_text("utf-8"))
        self.assertEqual((start["from"], start["tip"], start["round"]), (self.base, self.tip(), 1))
        map_md = (self.program.stop_review("A") / "MAP.md").read_text("utf-8")
        self.assertIn("E1 (a1): `pkg/tests/test_a1.py::test_a1` passed", map_md)
        self.assertIn("PASS every commit is chained", map_md)
        self.assertTrue((self.program.nightly(self.tip()) / "summary.txt").exists())
        from ship import phase
        from ship.layout import Program
        from ship.settings import load_settings

        self.assertEqual(phase.read(Program(self.program.dir), load_settings(self.program.dir))["next"], "merge")


class Blocked(ReviewCase):
    def test_blocked_with_a_fix_folder_returns_2_and_phase_says_build_the_fix(self):
        tip = self.tip()
        fix = {"{program}-fix-A/PROGRAM.yaml": fix_index("program", tip),
               "{program}-fix-A/SLICES.md": SLICES.replace("a1 |", "a1f |").replace("a2 |", "a2f |")}
        self.rules(self.verdict_rule("BLOCKED", tip, extra_files=fix), NOTES_DONE)
        self.assertEqual(self.ship("review", "A"), 2, self.out)
        self.assertEqual(self.ship("phase"), 0)
        self.assertIn("next: build", self.out)
        self.assertIn(f"build_folder: {(self.program.dir.parent / 'program-fix-A').as_posix()}", self.out)
        self.assertEqual(self.stop_copies(), [])


class NotRead(ReviewCase):
    def test_a_hanging_reader_becomes_not_read_and_a_clean_verdict_is_refused(self):
        self.setting("worker_timeout_s = 3")
        hang = {"match": "reader: chain", "kind": "hang"}
        self.rules(hang, self.verdict_rule("CLEAN", self.tip()), NOTES_DONE)
        self.assertEqual(self.ship("review", "A"), 10, self.out)
        notes = (self.program.stop_review("A") / "chain.md").read_text("utf-8")
        self.assertTrue(notes.startswith("NOT READ timeout"), notes)
        self.assertEqual(len(self.calls("chain")), 2, "restarted once")
        self.assertFalse((self.program.stop_review("A") / "REVIEW.md").exists())
        self.assertTrue((self.program.stop_review("A") / "REVIEW.refused-1.md").exists())
        self.assertTrue(any("not read" in w for w in self.waits()), self.waits())
        self.assertEqual(self.stop_copies(), [])


class Empty(ReviewCase):
    def test_an_empty_checkpoint_is_recorded_merged_with_its_parked_slices(self):
        state = st.load(self.program)
        for sid in ("a1", "a2"):
            sl = state.slices[sid]
            sl.status, sl.landed_sha, sl.reason = Status.PARKED, None, "manual: builder said BLOCKED"
        st.save(self.program, state)
        self.stop_note(self.tip(), self.tip(), landed=(), parked=("a1", "a2"))
        self.rules()
        self.assertEqual(self.ship("review", "A"), 0, self.out)
        self.assertEqual(self.program.merge_note("A").read_text("utf-8"), "EMPTY no commits; parked: a1, a2\n")
        self.assertEqual(st.load(self.program).merged, ["A"])
        self.assertEqual(len(self.waits()), 2, self.waits())
        self.assertEqual(self.calls("reader:"), [])


class Trace(ReviewCase):
    def test_a_stray_commit_makes_trace_exit_1_and_name_it(self):
        write(self.repo / "pkg" / "stray.py", "x = 1\n")
        sha = self.commit("oops: stray")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        self.stop_note(self.base, self.tip())
        self.assertEqual(self.ship("trace", "--stop", "A"), 1, self.out)
        self.assertIn(f"FAIL unchained commit {sha} 'oops: stray'", self.out)

    def test_a_missing_scenario_test_and_a_failing_guard_are_fail_lines(self):
        guard = ("\n## 7. What it must not do\n\n- Never rebuild: R-program-1\n\n```fact CALLERS exit=1\n"
                 "$ git grep -n \"def a2\" -- pkg\n```\n")
        write(self.program.brief("a2"), BRIEF + guard + "\n## 7a. Edge-case scenarios\n\n- E2 gone: (test: "
                                                         "pkg/tests/test_a2.py::test_gone)\n")
        write(self.program.dir / "REMOVED.md", "- **R-program-1** the old a2. Why: x. Status: planned\n")
        self.assertEqual(self.ship("trace", "--stop", "A"), 1, self.out)
        self.assertIn("FAIL scenario E2 of a2: its test `pkg/tests/test_a2.py::test_gone` is missing", self.out)
        self.assertIn("FAIL removal guard R-program-1 a2 CALLERS", self.out)


class Faults(ReviewCase):
    def test_the_fault_reader_starts_only_when_ground_lists_a_fixed_line(self):
        write(self.program.dir / "GROUND.md", "# Ground\n\n## Fixed lines touched\n\n- the kill switch\n\n## Other\n")
        self.rules(self.verdict_rule("CLEAN", self.tip()), FAULTS_DONE, NOTES_DONE)
        self.assertEqual(self.ship("review", "A"), 0, self.out)
        faults = self.calls("fault-reader:")
        self.assertEqual(len(faults), 1)
        argv = faults[0]["argv"]
        self.assertEqual(argv[argv.index("--model") + 1], "fable")
        self.assertEqual(argv[argv.index("--fallback-model") + 1], "claude-opus-5-5")


class HookRoles(RepoCase):
    """D-L16: each non-builder role writes only its own paths; git writes only for docs, in its worktree."""

    def hook(self, role, tool, cwd=None, env=None, **tool_input):
        event = {"tool_name": tool, "tool_input": tool_input, "cwd": str(cwd or self.root)}
        full = {k: v for k, v in os.environ.items() if not k.startswith("SHIP_")}
        full.update({"SHIP_ROLE": role, **(env or {})})
        done = subprocess.run([sys.executable, str(KIT), "hook", "--program", str(self.program.dir)], env=full,
                              input=json.dumps(event), capture_output=True, text=True, timeout=60)
        return done.returncode, done.stderr.strip()

    def test_a_reader_writes_only_its_notes_and_runs_no_git_write(self):
        notes = self.program.stop_review("A") / "chain.md"
        env = {"SHIP_NOTES": str(notes)}
        self.assertEqual(self.hook("reader", "Write", env=env, file_path=str(notes))[0], 0)
        for target in (self.program.stop_review("A") / "REVIEW.md", self.program.dir / "SLICES.md",
                       self.repo / "pkg" / "app.py"):
            self.assertEqual(self.hook("reader", "Write", env=env, file_path=str(target))[0], 2, target)
        self.assertEqual(self.hook("reader", "Bash", cwd=self.root, env=env, command="git log -1 && git status")[0], 0)
        rc, why = self.hook("reader", "Bash", cwd=self.root, env=env, command='git commit -m "x"')
        self.assertEqual(rc, 2, why)
        self.assertIn("role reader runs no git that writes", why)
        self.assertEqual(self.hook("reader", "Write", file_path=str(notes))[0], 2, "no SHIP_NOTES: refused")

    def test_a_verdict_writes_its_review_merge_and_fix_folders(self):
        env = {"SHIP_STOP": "A"}
        d = self.program.dir
        for ok in (d / "stop-review" / "A" / "REVIEW.md", d / "merge" / "A-pr.md",
                   d.parent / f"{d.name}-fix-A" / "SLICES.md"):
            self.assertEqual(self.hook("verdict", "Write", env=env, file_path=str(ok))[0], 0, ok)
        for bad in (d / "stop-review" / "B" / "REVIEW.md", d / "state.json", d / "PROGRAM.yaml",
                    d.parent / f"{d.name}-fix-B" / "SLICES.md"):
            self.assertEqual(self.hook("verdict", "Write", env=env, file_path=str(bad))[0], 2, bad)

    def test_grounding_planner_and_unknown_roles(self):
        d = self.program.dir
        self.assertEqual(self.hook("grounding", "Write", file_path=str(d / "plan-review" / "grounding.md"))[0], 0)
        self.assertEqual(self.hook("grounding", "Write", file_path=str(d / "plan-review" / "REVIEW.md"))[0], 2)
        self.assertEqual(self.hook("planner-fix", "Edit", file_path=str(d / "slices" / "s1" / "BRIEF.md"))[0], 0)
        self.assertEqual(self.hook("planner-fix", "Edit", file_path=str(d / "state.json"))[0], 2)
        self.assertEqual(self.hook("plan-review", "Write", file_path=str(d / "plan-review" / "FIXES.md"))[0], 0)
        rc, why = self.hook("intruder", "Write", file_path=str(d / "plan-review" / "FIXES.md"))
        self.assertEqual(rc, 2, why)
        self.assertIn("not in the hook's table", why)

    def test_docs_commits_and_pushes_only_in_its_worktree_and_branch(self):
        tree = self.root / "docs-wt"
        sh(self.repo, "git", "worktree", "add", "-q", "-b", "docs/program-A", str(tree))
        env = {"SHIP_WORKTREE": str(tree), "SHIP_BRANCH": "docs/program-A"}
        self.assertEqual(self.hook("docs", "Write", env=env, file_path=str(tree / "docs" / "x.md"))[0], 0)
        self.assertEqual(self.hook("docs", "Bash", cwd=tree, env=env,
                                   command='git add -A && git commit -m "docs" && git push origin docs/program-A')[0], 0)
        self.assertEqual(self.hook("docs", "Bash", cwd=tree, env=env, command="git push origin HEAD:engine/base")[0], 2)
        self.assertEqual(self.hook("docs", "Bash", cwd=self.repo, env=env, command='git commit -m "x"')[0], 2)
        self.assertEqual(self.hook("docs", "Write", env=env, file_path=str(self.repo / "README.md"))[0], 2)

    def test_a_role_with_no_state_and_no_repo_gets_no_bash(self):
        self.program.state.unlink()
        rc, why = self.hook("plan-review", "Bash", command="git log -1")
        self.assertEqual(rc, 2, why)
        self.assertIn("SHIP_REPO", why)
        self.assertEqual(self.hook("plan-review", "Bash", env={"SHIP_REPO": str(self.repo)}, command="git log -1")[0], 0)
        self.assertEqual(self.hook("builder", "Write", file_path=str(self.program.dir / "x"))[0], 2)
