"""K4a: the kit items for the first real run (BUILD-LOG D-L23 and the S2-fix row)."""

import unittest

from ship.settings import load_settings
from ship.tests.fixture import RepoCase, sh, write
from ship.worktree import checkout_copy, drop_copy


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
