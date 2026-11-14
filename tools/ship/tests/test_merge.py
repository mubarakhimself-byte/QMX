"""ship merge on a scratch repo: real git, a fake `gh` that merges PRs in the bare remote and answers the
gate, a plans worktree for the records. No real merge anywhere."""

import json
import os
import shutil
import subprocess
from pathlib import Path

from ship import state as st
from ship.launch import KIT
from ship.layout import Program
from ship.settings import Settings
from ship.state import Status
from ship.tests.fixture import BRIEF, PY, RepoCase, sh, write

SLICES = ("| id | name | stop | depends on | files | size |\n|---|---|---|---|---|---|\n"
          "| a1 | Slice a1 | A | - | pkg/a1.py | S |\n| a2 | Slice a2 | A | - | pkg/a2.py | S |\n")


class MergeCase(RepoCase):
    def setUp(self):
        super().setUp()
        from ship import records
        from ship.plan import init_state

        # the workflow file, so ci.start can dispatch a deep run on any tip
        write(self.repo / ".github" / "workflows" / "qmx-ci.yml", "name: qmx-ci\n")
        self.commit("ci: workflow")
        sh(self.repo, "git", "push", "-q", "origin", "main", f"main:refs/heads/{self.build_branch}")
        # the program folder lives in the plans worktree, beside _records
        self.plans = self.root / "plans"
        records.init(self.repo, self.plans, "origin", Settings())
        moved = self.plans / "program"
        shutil.move(str(self.program.dir), str(moved))
        self.program = Program(moved)
        toml = self.program.dir / "ship.toml"
        toml.write_text(toml.read_text("utf-8").replace('ci = "local"', 'ci = "github"'), "utf-8")
        for line in ('ci_gate_base = "main"', "ci_poll_s = 0.2", "ci_find_s = 5", "ci_wait_timeout_s = 60",
                     'internet_probe = ""'):
            self.setting(line)
        write(self.program.slices_md, SLICES)
        write(self.program.brief("a1"), BRIEF + "\nNever rebuild: R-program-1\n")
        write(self.program.brief("a2"), BRIEF)
        self.program.state.unlink()
        init_state(self.program.dir, self.repo, self.build_branch, self.wt_root, "origin")
        self.base = self.tip()
        self.land_two()
        write(self.program.dir / "REMOVED.md", "# Removed\n\n- **R-program-1** the old a1 helper. Why: unused. "
                                               "Decided by: agent. Status: planned (program, 2026-11-14)\n")
        self.reviewed = self.tip()
        write(self.program.stop_review("A") / "REVIEW.md",
              f"VERDICT: CLEAN\n\nEND {self.reviewed} checkpoint-A-round-1\n")
        write(self.program.dir / "merge" / "A-pr.md", "Stop A of program.\n\nShipped by Mubarak.\n")
        with st.locked(self.program) as state:
            state.ci["deep"] = {"tip": self.reviewed, "level": "deep", "run_id": "1", "url": "https://github.test/runs/1",
                                "result": "green"}

    def land_two(self):
        sh(self.repo, "git", "fetch", "-q", "origin")
        sh(self.repo, "git", "checkout", "-q", "-B", "work", f"origin/{self.build_branch}")
        state = st.load(self.program)
        for sid in ("a1", "a2"):
            write(self.repo / "pkg" / f"{sid}.py", f"def {sid}():\n    return '{sid}'\n")
            sha = self.commit(f"{sid}: Slice {sid}")
            sl = state.slices[sid]
            sl.status, sl.landed_sha, sl.head = Status.LANDED, sha, sha
        st.save(self.program, state)
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        write(self.program.stop_note("A"), json.dumps({"stop": "A", "from": self.base, "tip": self.tip(),
                                                       "landed": ["a1", "a2"], "parked": []}))

    def flag(self, name):
        common = sh(self.repo, "git", "rev-parse", "--git-common-dir")
        path = Path(common) if Path(common).is_absolute() else self.repo / common
        (path / name).write_text("x", "utf-8")

    def ship_merge(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SHIP_")}
        done = subprocess.run([PY, str(KIT), "merge", "A", "--program", str(self.program.dir)], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", env=env, stdin=subprocess.DEVNULL,
                              timeout=300)
        self.out = done.stdout + done.stderr
        return done.returncode

    def main_sha(self):
        return sh(self.repo, "git", "ls-remote", "origin", "refs/heads/main").split()[0]

    def contains(self, older, newer):
        sh(self.repo, "git", "fetch", "-q", "origin")
        return subprocess.run(["git", "merge-base", "--is-ancestor", older, newer], cwd=self.repo).returncode == 0

    def waits(self):
        path = self.program.waits
        return [x for x in path.read_text("utf-8").splitlines() if x.startswith("- [ ]")] if path.exists() else []

    def push_to_main(self, path, text, message):
        sh(self.repo, "git", "checkout", "-q", "-B", "other", "origin/main")
        write(self.repo / path, text)
        self.commit(message)
        sh(self.repo, "git", "push", "-q", "origin", "HEAD:refs/heads/main")


class Clean(MergeCase):
    def test_a_clean_green_checkpoint_merges_once_and_moves_its_removal_rows(self):
        self.assertEqual(self.ship_merge(), 0, self.out)
        merged = self.main_sha()
        self.assertTrue(self.contains(self.reviewed, merged))
        note = self.program.merge_note("A").read_text("utf-8")
        self.assertIn(f"MERGED {merged}", note)
        self.assertIn(f"Reviewed tip: {self.reviewed}", note)
        self.assertEqual(st.load(self.program).merged, ["A"])
        records = (self.plans / "_records" / "REMOVED.md").read_text("utf-8")
        self.assertIn(f"**R-program-1** the old a1 helper. Why: unused. Decided by: agent. Status: removed {merged}",
                      records)
        self.assertNotIn("R-program-1", (self.program.dir / "REMOVED.md").read_text("utf-8"))
        self.assertIn("records: removed rows of program stop A", sh(self.plans, "git", "log", "-1", "--format=%s"))
        self.assertEqual(self.ship_merge(), 0, self.out)
        self.assertIn("ALREADY stop A merged", self.out)
        self.assertEqual(self.main_sha(), merged, "the second run makes no commit")

    def test_a_red_gate_returns_2_and_nothing_merges(self):
        before = self.main_sha()
        self.flag("fake-gh-gate-red")
        self.assertEqual(self.ship_merge(), 2, self.out)
        self.assertEqual(self.main_sha(), before)
        self.assertNotIn("MERGED", self.program.merge_note("A").read_text("utf-8")
                         if self.program.merge_note("A").exists() else "")
        self.assertEqual(st.load(self.program).merged, [])
        self.assertTrue(any("gate refused" in w for w in self.waits()), self.waits())

    def test_a_verdict_ship_review_has_not_judged_does_not_merge(self):
        write(self.program.stop_review("A") / "review-run.json", json.dumps({"round": 1, "tip": self.reviewed}))
        self.assertEqual(self.ship_merge(), 10, self.out)
        self.assertTrue(any("ship review has not passed this verdict" in w for w in self.waits()), self.waits())
        write(self.program.stop_review("A") / "review-run.json",
              json.dumps({"round": 1, "tip": self.reviewed, "result": 0}))
        self.assertEqual(self.ship_merge(), 0, self.out)

    def test_the_last_verdict_must_be_clean(self):
        write(self.program.stop_review("A") / "REVIEW-2.md", f"VERDICT: BLOCKED\n\nEND {self.reviewed} x\n")
        self.assertEqual(self.ship_merge(), 10, self.out)
        self.assertTrue(any("BLOCKED with no later CLEAN" in w for w in self.waits()), self.waits())


class Moved(MergeCase):
    def test_a_moved_target_is_merged_in_and_gets_its_own_deep_run_before_the_pr_merges(self):
        self.flag("fake-gh-auto")
        self.push_to_main("pkg/other.py", "x = 1\n", "other program: work")
        theirs = self.main_sha()
        self.assertEqual(self.ship_merge(), 0, self.out)
        sh(self.repo, "git", "fetch", "-q", "origin")
        build = self.tip()
        self.assertEqual(sh(self.repo, "git", "log", "-1", "--format=%s", build),
                         f"merge: main into {self.build_branch} for stop A")
        self.assertTrue(self.contains(theirs, build) and self.contains(self.reviewed, build))
        common = sh(self.repo, "git", "rev-parse", "--git-common-dir")
        runs = json.loads(((Path(common) if Path(common).is_absolute() else self.repo / common)
                           / "fake-gh-runs.json").read_text("utf-8"))["runs"]
        deep = [r for r in runs if r["event"] == "workflow_dispatch" and r["headSha"] == build]
        self.assertEqual(len(deep), 1, "one deep run on the merge commit")
        self.assertTrue(self.contains(build, self.main_sha()))
        self.assertIn(f"MERGE-BASE {build}", self.program.merge_note("A").read_text("utf-8"))

    def test_a_conflicting_target_writes_the_one_slice_fix_program(self):
        self.push_to_main("pkg/a1.py", "def a1():\n    return 'theirs'\n", "other program: a1 differently")
        before = self.main_sha()
        self.assertEqual(self.ship_merge(), 2, self.out)
        self.assertEqual(self.main_sha(), before)
        self.assertEqual(self.tip(), self.reviewed, "nothing pushed to the build branch")
        fix = Program(self.program.dir.parent / "program-fix-A")
        self.assertIn("kind: fix\nparent: program\n", fix.project_file.read_text("utf-8"))
        self.assertIn("| program-A-fix-merge | Merge main into the build branch | A | - | pkg/a1.py | S |",
                      fix.slices_md.read_text("utf-8"))
        self.assertTrue(fix.brief("program-A-fix-merge").exists())
        from ship.program import load

        index = load(fix)
        self.assertEqual((index.kind, index.parent, index.gate("go")["by"], [s.id for s in index.stops]),
                         ("fix", "program", "stop-review", ["A"]))
