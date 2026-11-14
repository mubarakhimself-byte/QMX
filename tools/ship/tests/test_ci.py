"""The GitHub backend: real git repos, `gh` replaced at the subprocess boundary by fake_gh.py."""

import dataclasses
import json
import unittest

from ship import ci
from ship import state as st
from ship.land import land
from ship.nightly import ci_status, nightly
from ship.recover import recover
from ship.settings import load_settings
from ship.slice_checks import slice_checks
from ship.state import Status
from ship.status import status
from ship.suite import canon, local_id, this_system
from ship.tests.fixture import RepoCase, sh, write

WORKFLOW = ".github/workflows/qmx-ci.yml"
OTHER = "linux" if this_system() == "windows" else "windows"
MUL = "def mul(a, b):\n    return a * b\n"
RED_TEST = "def test_mul():\n    assert 1 == 2\n"


def junit(cases: list[tuple[str, str, str | None]]) -> str:
    rows = "".join(
        f'<testcase classname="{c}" name="{n}">' + (f'<failure message="{f}"/>' if f else "") + "</testcase>"
        for c, n, f in cases)
    return f'<?xml version="1.0"?><testsuites><testsuite name="pytest">{rows}</testsuite></testsuites>'


def shard(system: str, index: int, root: str, cases: list[tuple[str, str, str | None]]) -> dict[str, str]:
    """A test shard's ci-out artifact as qmx-ci writes it."""
    reds = "".join(f"{system}|{root}|{c}::{n}\n" for c, n, f in cases if f)
    stem = f"{system}-{index}-{root.replace('/', '_')}"
    return {f"plan-{system}-{index}.json": json.dumps({"units": [root], "files": [f"{root}::t.py"]}),
            f"reds-{system}-{index}.txt": reds,
            f"junit/{stem}.xml": junit(cases)}


def job(name: str, conclusion: str = "success", job_id: int = 1, status: str = "completed") -> dict:
    return {"name": name, "status": status, "conclusion": conclusion if status == "completed" else "",
            "databaseId": job_id, "url": f"https://github.test/job/{job_id}",
            "startedAt": "2026-11-13T00:00:00Z", "completedAt": "2026-11-13T00:10:00Z"}


class CiCase(RepoCase):
    def setUp(self):
        super().setUp()
        path = self.program.dir / "ship.toml"
        path.write_text(path.read_text("utf-8").replace('ci = "local"', 'ci = "github"')
                        + "ci_poll_s = 1\nci_find_s = 5\nci_wait_timeout_s = 5\n", "utf-8")
        self.settings = load_settings(self.program.dir)
        self.on_build({WORKFLOW: "name: qmx-ci\n"}, "add qmx-ci")

    def on_build(self, files: dict[str, str], message: str) -> str:
        sh(self.repo, "git", "checkout", "-q", "-B", "b", f"origin/{self.build_branch}")
        for path, text in files.items():
            write(self.repo / path, text)
        sha = self.commit(message)
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        return sha

    @property
    def store(self):
        return self.repo / ".git" / "fake-gh-runs.json"

    def runs(self) -> dict:
        return json.loads(self.store.read_text("utf-8")) if self.store.exists() else {"runs": []}

    def put_run(self, **fields) -> dict:
        data = self.runs()
        run_id = fields.pop("databaseId", max([r["databaseId"] for r in data["runs"]] + [2000]) + 1)
        run_ = {"databaseId": run_id, "status": "completed", "conclusion": "success", "event": "push",
                "displayTitle": "", "url": f"https://github.test/runs/{run_id}", "createdAt": "2026-11-13T00:00:00Z",
                "jobs": [], "artifacts": {}, **fields}
        data["runs"].insert(0, run_)
        self.store.write_text(json.dumps(data), "utf-8")
        return run_

    def change_run(self, run_id, **fields) -> None:
        data = self.runs()
        for r in data["runs"]:
            if str(r["databaseId"]) == str(run_id):
                r.update(fields)
        self.store.write_text(json.dumps(data), "utf-8")

    def calls(self) -> list[list[str]]:
        path = self.repo / ".git" / "fake-gh-calls.jsonl"
        return [json.loads(ln) for ln in path.read_text("utf-8").splitlines()] if path.exists() else []

    def dispatches(self) -> int:
        return sum(1 for c in self.calls() if c[:2] == ["workflow", "run"])

    def finish_green(self, run_id, tip, linux_cases=None, extra_jobs=(), verdict=True, conclusion="success"):
        cases = linux_cases or [("tests.test_x", "test_ok", None)]
        artifacts = {"ci-out-suite-linux-1": shard("linux", 1, "pkg", cases),
                     "ci-out-suite-windows-1": shard("windows", 1, "pkg", [("tests.test_x", "test_ok", None)])}
        if verdict:
            artifacts["deep-verdict"] = {"verdict.json": json.dumps({"sha": tip, "level": "deep"})}
        jobs = [job("level"), job("suite-linux 1", "failure" if any(f for *_, f in cases) else "success", 2),
                job("suite-windows 1", "success", 3), job("tests-linux ${{ matrix.shard }}", "skipped", 4),
                *extra_jobs]
        self.change_run(run_id, status="completed", conclusion=conclusion, jobs=jobs, artifacts=artifacts)


class DeepRun(CiCase):
    def test_nightly_dispatches_once_records_the_run_and_reads_it_green(self):
        tip = self.tip()
        ok, lines = nightly(self.program, self.settings, wait=False)
        self.assertIsNone(ok)
        self.assertEqual(lines, [f"CI deep 1001 dispatched on {tip[:8]}: https://github.test/runs/1001"])
        deep = st.load(self.program).ci["deep"]
        self.assertEqual((deep["run_id"], deep["tip"], deep["level"], deep["result"]), ("1001", tip, "deep", None))
        dispatch = [c for c in self.calls() if c[:2] == ["workflow", "run"]]
        self.assertEqual(dispatch, [["workflow", "run", "qmx-ci.yml", "--ref", "build/t", "-f", "level=deep",
                                     "-R", "owner/qmx"]])

        self.finish_green(1001, tip)
        rc, lines = ci_status(self.program, self.settings)
        self.assertEqual(rc, 0, lines)
        self.assertEqual(lines, ["CI deep 1001 success: https://github.test/runs/1001",
                                 f"PASS nightly {tip[:8]} 0 baseline reds, no new red"])
        state = st.load(self.program)
        self.assertEqual((state.last_green, state.ci["deep"]["result"]), (tip, "green"))
        self.assertEqual(state.nightly["backend"], "github")

        before = len(self.calls())
        self.assertEqual(ci_status(self.program, self.settings), (0, lines))
        self.assertEqual(len(self.calls()), before, "a judged run is read from summary.txt, not from GitHub")
        self.assertTrue(all("-R" in c and c[c.index("-R") + 1] == "owner/qmx" for c in self.calls()))

    def test_start_again_and_recover_reattach_and_a_lost_record_finds_the_running_run(self):
        tip = self.tip()
        self.assertEqual(ci.start(self.program, self.settings),
                         [f"CI deep 1001 dispatched on {tip[:8]}: https://github.test/runs/1001"])
        self.assertEqual(ci.start(self.program, self.settings),
                         [f"CI deep 1001 attached on {tip[:8]}: queued https://github.test/runs/1001"])
        self.assertEqual(recover(self.program, self.settings)[-1],
                         f"CI deep 1001 on {tip[:8]} re-attached: queued https://github.test/runs/1001; "
                         "ship ci status --wait reads it")
        with st.locked(self.program) as state:
            state.ci.clear()  # a crash between the dispatch and the record
        self.assertEqual(ci.start(self.program, self.settings),
                         [(f"CI deep 1001 attached on {tip[:8]} (found running, not recorded): queued "
                           "https://github.test/runs/1001")])
        self.assertEqual(self.dispatches(), 1)

        self.change_run(1001, status="completed", conclusion="cancelled")
        self.assertEqual(ci.start(self.program, self.settings),
                         [f"CI deep 1002 dispatched on {tip[:8]}: https://github.test/runs/1002"])
        self.assertEqual(self.dispatches(), 2)

    def test_recover_while_github_is_down_dispatches_nothing(self):
        ci.start(self.program, self.settings)
        (self.repo / ".git" / "fake-gh-down").write_text("", "utf-8")
        line = recover(self.program, self.settings)[-1]
        self.assertTrue(line.startswith(f"CI deep 1001 on {self.tip()[:8]} recorded; GitHub unreachable"), line)
        self.assertEqual(self.dispatches(), 1)
        rc, lines = ci_status(self.program, self.settings)
        self.assertEqual(rc, 2)
        self.assertTrue(lines[0].startswith("PENDING ci deep 1001: GitHub unreachable"), lines)

    def test_new_red_elsewhere_a_failed_job_and_no_verdict_make_it_red(self):
        tip = self.tip()
        ci.start(self.program, self.settings)
        bad = ("tests.test_x", "test_bad", "assert 1 == 2")
        artifacts = {f"ci-out-suite-{OTHER}-1": shard(OTHER, 1, "pkg", [bad]),
                     f"ci-out-suite-{this_system()}-1": shard(this_system(), 1, "pkg", [("tests.test_x", "test_ok", None)])}
        self.change_run(1001, status="completed", conclusion="failure", artifacts=artifacts,
                        jobs=[job(f"suite-{OTHER} 1", "failure", 2), job(f"suite-{this_system()} 1", "success", 3),
                              job("lint", "failure", 9), job("deep-verdict", "skipped", 10)])
        rc, lines = ci_status(self.program, self.settings)
        self.assertEqual(rc, 1)
        self.assertEqual(lines, [
            "CI deep 1001 failure: https://github.test/runs/1001",
            "FAIL ci-job lint failure https://github.test/job/9",
            f"FAIL deep-verdict none names {tip[:8]}, so the pull-request gate will not pass",
            (f"FAIL nightly {tip[:8]} new reds on another system ['{OTHER}|pkg|tests.test_x::test_bad']; "
             f"not bisected on {this_system()}: the suspects are the slices landed since the last green tip"),
        ])
        state = st.load(self.program)
        self.assertEqual((state.ci["deep"]["result"], state.last_green), ("red", None))
        self.assertEqual(state.nightly["new_reds"], [f"{OTHER}|pkg|tests.test_x::test_bad"])

    def test_known_red_in_known_reds_txt_passes_and_the_kit_writes_no_list_of_its_own(self):
        old = "linux|pkg|pkg.tests.test_x::test_old"
        tip = self.on_build({"ci/baselines/known-reds.txt": f"# header\n{old}\n"}, "known reds")
        ci.start(self.program, self.settings)
        self.finish_green(1001, tip, linux_cases=[("pkg.tests.test_x", "test_old", "assert 0")])
        rc, lines = ci_status(self.program, self.settings)
        self.assertEqual(rc, 0, lines)
        self.assertEqual(lines[-1], f"PASS nightly {tip[:8]} 1 baseline reds, no new red")
        self.assertFalse(any(p.name.startswith("baseline") for p in self.program.dir.iterdir()))

    def test_a_shard_that_left_no_reds_file_is_red(self):
        tip = self.tip()
        ci.start(self.program, self.settings)
        self.finish_green(1001, tip)
        data = self.runs()
        del data["runs"][0]["artifacts"]["ci-out-suite-windows-1"]
        data["runs"][0]["jobs"][2]["conclusion"] = "failure"
        self.store.write_text(json.dumps(data), "utf-8")
        rc, lines = ci_status(self.program, self.settings)
        self.assertEqual(rc, 1)
        self.assertIn(f"FAIL nightly {tip[:8]} no JUnit report from ['suite-windows-1']", lines)

    def test_a_running_run_reports_reds_so_far_and_waits(self):
        tip = self.tip()
        ci.start(self.program, self.settings)
        bad = ("tests.test_x", "test_bad", "assert 1 == 2")
        self.change_run(1001, status="in_progress", artifacts={"ci-out-suite-linux-1": shard("linux", 1, "pkg", [bad])},
                        jobs=[job("suite-linux 1", "failure", 2), job("suite-windows 1", status="in_progress", job_id=3)])
        rc, lines = ci_status(self.program, self.settings)
        self.assertEqual(rc, 2)
        self.assertEqual(lines, [
            (f"PENDING ci deep 1001 on {tip[:8]} in_progress: 1 jobs still queued or running, "
             "1 finished jobs read; https://github.test/runs/1001"),
            "SO-FAR new red linux|pkg|tests.test_x::test_bad",
        ])
        self.assertIsNone(st.load(self.program).ci["deep"]["result"])
        ok, waited = nightly(self.program, self.settings)  # attaches, then gives up after ci_wait_timeout_s
        self.assertIsNone(ok)
        self.assertEqual(waited[0], f"CI deep 1001 attached on {tip[:8]}: in_progress https://github.test/runs/1001")
        self.assertEqual(self.dispatches(), 1)


class SummaryJson(CiCase):
    """U17b: with the GitHub backend the kit reads qmx-ci's summary.json, only for the commit it names."""

    def summary(self, sha, **fields):
        body = {"sha": sha, "ref": "build/t", "run_id": 1001, "url": "https://github.test/runs/1001", "level": "deep",
                "green": True, "jobs": [], "reds": [], "quality": [],
                "mutants": {"killed": 0, "survived": 0, "new_survivors": 0}, "skipped": [], **fields}
        return {"summary.json": json.dumps(body), "summary.md": "x"}

    def test_ci_summary_saves_the_summary_of_the_tip_and_prints_what_blocks(self):
        tip = self.tip()
        ci.start(self.program, self.settings)
        self.finish_green(1001, tip)
        flaky = {"id": "pkg|pkg.tests.test_x::test_shaky", "system": "linux", "kind": "flaky", "blocks": True}
        quality = {"tool": "vulture", "key": "pkg/a.py|vulture|unused function 'f'", "file": "pkg/a.py",
                   "kind": "new", "blocks": True}
        note = {"tool": "skylos", "key": "pkg/a.py|quality:SKY-L1|x", "file": "pkg/a.py", "kind": "new", "blocks": False}
        data = self.runs()
        data["runs"][0]["artifacts"]["summary"] = self.summary(tip, reds=[flaky], quality=[quality, note])
        self.store.write_text(json.dumps(data), "utf-8")
        rc, lines = ci.summary(self.program, self.settings, tip[:10])
        target = self.program.nightly(tip) / "summary.json"
        self.assertEqual(rc, 0, lines)
        self.assertEqual(lines, [f"SUMMARY {target}", f"GREEN deep {tip[:8]} https://github.test/runs/1001",
                                 "REDS 1 block of 1", "FAIL ci-red flaky linux|pkg|pkg.tests.test_x::test_shaky",
                                 "FAIL ci-quality vulture pkg/a.py|vulture|unused function 'f'"])
        self.assertEqual(json.loads(target.read_text("utf-8"))["sha"], tip)

    def test_ci_summary_refuses_a_summary_of_another_commit(self):
        tip = self.tip()
        ci.start(self.program, self.settings)
        self.finish_green(1001, tip)
        data = self.runs()
        data["runs"][0]["artifacts"]["summary"] = self.summary("f" * 40)
        self.store.write_text(json.dumps(data), "utf-8")
        rc, lines = ci.summary(self.program, self.settings)
        self.assertEqual(rc, 1)
        self.assertEqual(lines, [f"NONE summary for {tip[:8]}: deep run 1001's summary.json names ffffffff, "
                                 f"not {tip[:8]}"])
        self.assertFalse((self.program.nightly(tip) / "summary.json").exists())

    def test_ci_summary_with_no_deep_run_is_none(self):
        rc, lines = ci.summary(self.program, self.settings)
        self.assertEqual((rc, lines), (1, [f"NONE summary for {self.tip()[:8]}: no deep run on {self.tip()[:8]}"]))

    def test_the_deep_verdict_takes_what_the_summary_blocks(self):
        tip = self.tip()
        ci.start(self.program, self.settings)
        self.finish_green(1001, tip)
        flaky = {"id": "pkg|pkg.tests.test_x::test_shaky", "system": "linux", "kind": "flaky", "blocks": True}
        data = self.runs()
        data["runs"][0]["artifacts"]["summary"] = self.summary(tip, green=False, reds=[flaky])
        self.store.write_text(json.dumps(data), "utf-8")
        rc, lines = ci_status(self.program, self.settings)
        self.assertEqual(rc, 1, lines)
        self.assertIn("FAIL ci-red flaky linux|pkg|pkg.tests.test_x::test_shaky", lines)
        self.assertEqual(st.load(self.program).ci["deep"]["result"], "red")

    def test_the_checkpoint_quality_reads_the_summary_and_runs_nothing(self):
        from ship.quality import checkpoint_quality

        base = self.tip()
        tip = self.on_build({"pkg/area.py": "def unused_a():\n    return 0\n"}, "area")
        ci.start(self.program, self.settings)
        self.finish_green(1001, tip)
        quality = [{"tool": "vulture", "key": "pkg/area.py|vulture|unused function 'unused_a'", "file": "pkg/area.py",
                    "kind": "new", "blocks": True},
                   {"tool": "mutmut", "key": "pkg|mutmut|pkg.area.f survived", "file": "pkg", "kind": "gone",
                    "blocks": False}]
        data = self.runs()
        data["runs"][0]["artifacts"]["summary"] = self.summary(tip, quality=quality)
        self.store.write_text(json.dumps(data), "utf-8")
        ok, lines = checkpoint_quality(self.program, self.settings, base, ("vulture", "mutmut"))
        self.assertFalse(ok)
        self.assertEqual(lines, [
            f"FAIL quality-vulture-ci {tip[:8]} 1 new: pkg/area.py|vulture|unused function 'unused_a'",
            f"PASS quality-mutmut-ci {tip[:8]} no new blocking rows in summary.json (0 notes, 1 gone)"])
        self.assertFalse((self.program.tmp / "quality-tip").exists(), "no tool ran here")


class Fallback(CiCase):
    def test_github_down_runs_the_local_nightly(self):
        (self.repo / ".git" / "fake-gh-down").write_text("", "utf-8")
        ok, lines = nightly(self.program, self.settings)
        self.assertTrue(ok, lines)
        self.assertEqual(lines[0], "CI github unavailable: gh cannot read GitHub: error connecting to api.github.com; "
                                   "the local run stands in")
        self.assertEqual(lines[-1], f"PASS nightly {self.tip()[:8]} 0 baseline reds, no new red")
        self.assertEqual(st.load(self.program).nightly["backend"], "local")

    def test_no_workflow_on_the_branch_runs_the_local_nightly(self):
        sh(self.repo, "git", "checkout", "-q", "-B", "b", f"origin/{self.build_branch}")
        sh(self.repo, "git", "rm", "-q", WORKFLOW)
        self.commit("drop qmx-ci")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        ok, lines = nightly(self.program, self.settings)
        self.assertTrue(ok, lines)
        self.assertEqual(lines[0], f"CI github unavailable: {WORKFLOW} is not on build/t at {self.tip()[:8]}; "
                                   "the local run stands in")
        self.assertEqual(self.dispatches(), 0)


class SliceAndLand(CiCase):
    def checked(self, sid, files):
        head = self.make_ready(sid, files)
        with st.locked(self.program) as state:
            state.slices[sid].status = Status.CHECKED
        return head

    def slice_run(self, sid, head, conclusion="success", status="completed"):
        return self.put_run(headSha=head, headBranch=f"slice/{sid}", status=status,
                            conclusion=conclusion if status == "completed" else "", displayTitle=f"slice slice/{sid}")

    def test_slice_checks_reads_the_linux_slice_run(self):
        head = self.make_ready("s1", {"pkg/mul.py": MUL})
        run_ = self.slice_run("s1", head)
        ok, lines = slice_checks(self.program, "s1", self.settings)
        self.assertTrue(ok, lines)
        self.assertIn(f"PASS linux s1 {head[:8]} slice run completed success on {head[:8]} {run_['url']}", lines)
        self.assertEqual(st.load(self.program).slices["s1"].ci,
                         {"sha": head, "linux": "pass", "url": run_["url"]})

    def test_a_red_linux_slice_run_sends_the_slice_back(self):
        head = self.checked("s1", {"pkg/mul.py": MUL})
        before = self.tip()
        self.slice_run("s1", head, conclusion="failure")
        ok, _ = land(self.program, None, self.settings)
        self.assertFalse(ok)
        sl = st.load(self.program).slices["s1"]
        self.assertEqual(sl.status, Status.RED)
        self.assertTrue(sl.reason.startswith("land: Linux slice run red: slice run completed failure"), sl.reason)
        self.assertEqual(self.tip(), before)

    def test_a_pending_run_waits_then_lands_after_the_grace_and_the_checkpoint_rereads_it(self):
        head = self.checked("s1", {"pkg/mul.py": MUL})
        run_ = self.slice_run("s1", head, status="queued")
        ok, lines = land(self.program, None, self.settings)
        self.assertFalse(ok)
        self.assertTrue(lines[0].startswith(f"WAIT s1: Linux slice run queued on {head[:8]} {run_['url']}"), lines)
        self.assertEqual(st.load(self.program).slices["s1"].status, Status.CHECKED)

        ok, lines = land(self.program, None, dataclasses.replace(self.settings, ci_slice_grace_s=0))
        self.assertTrue(ok, lines)
        self.assertTrue(lines[0].startswith("LINUX s1 pending after 0 min"), lines)
        state = st.load(self.program)
        tip = self.tip()
        self.assertEqual((state.slices["s1"].status, state.slices["s1"].ci["linux"]), (Status.LANDED, "pending"))
        self.assertEqual([(r["tip"], r["slices"]) for r in state.ci["land"]], [(tip, ["s1"])])

        self.put_run(headSha=tip, headBranch="build/t", conclusion="failure", displayTitle="land build/t")
        _, lines = status(self.program, self.settings)
        self.assertIn(f"LAND-RED {tip[:8]} batch ['s1'] https://github.test/runs/2002; the checkpoint's deep "
                      "run decides", lines)

        self.change_run(run_["databaseId"], status="completed", conclusion="failure")
        ci.start(self.program, self.settings)
        self.finish_green(st.load(self.program).ci["deep"]["run_id"], tip)
        rc, lines = ci_status(self.program, self.settings)
        self.assertEqual(rc, 1)
        self.assertIn(f"FAIL linux-slice s1 landed while pending, now red: slice run completed failure on "
                      f"{head[:8]} {run_['url']}", lines)
        self.assertIn(f"NOTE land run red at {tip[:8]} batch ['s1'] https://github.test/runs/2002; this run decides",
                      lines)

    def test_a_green_linux_run_lands(self):
        head = self.checked("s1", {"pkg/mul.py": MUL})
        run_ = self.slice_run("s1", head)
        ok, lines = land(self.program, None, self.settings)
        self.assertTrue(ok, lines)
        self.assertEqual(lines[0], f"LINUX s1 green: slice run completed success on {head[:8]} {run_['url']}")


class SharedBaseline(RepoCase):
    def test_land_accepts_a_red_known_on_this_system_only(self):
        settings = load_settings(self.program.dir)
        sh(self.repo, "git", "checkout", "-q", "-B", "b", f"origin/{self.build_branch}")
        write(self.repo / "ci" / "baselines" / "known-reds.txt", f"{OTHER}|.|pkg.tests.test_mul::test_mul\n")
        self.commit("known on the other system")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        self.make_ready("s1", {"pkg/mul.py": MUL, "pkg/tests/test_mul.py": RED_TEST})
        with st.locked(self.program) as state:
            state.slices["s1"].status = Status.CHECKED
        ok, lines = land(self.program, None, settings)
        self.assertFalse(ok)
        self.assertIn("new reds ['.::pkg.tests.test_mul::test_mul']", lines[0])

        sh(self.repo, "git", "checkout", "-q", "-B", "b", f"origin/{self.build_branch}")
        write(self.repo / "ci" / "baselines" / "known-reds.txt", f"{this_system()}|.|pkg.tests.test_mul::test_mul\n")
        self.commit("known here")
        sh(self.repo, "git", "push", "-q", "origin", f"HEAD:refs/heads/{self.build_branch}")
        ok, lines = land(self.program, None, settings)
        self.assertTrue(ok, lines)

    def test_one_spelling_for_ci_and_local_ids(self):
        self.assertEqual(canon("linux|qml|qml.tests.test_x::test_a"), canon("qml::tests.test_x::test_a", "linux"))
        self.assertEqual(canon("windows|qmx-agents/apps/node|apps.node.tests.test_n::test_a"),
                         "windows|qmx-agents/apps/node|tests.test_n::test_a")
        self.assertNotEqual(canon("linux|qml|tests.t::a"), canon("windows|qml|tests.t::a"))
        self.assertEqual(local_id("linux|qml|qml.tests.test_x::test_a[a|b]"), "qml::tests.test_x::test_a[a|b]")


class InitBranch(CiCase):
    def test_init_refuses_a_build_branch_qmx_ci_does_not_watch(self):
        from ship.__main__ import main

        self.program.state.unlink()
        argv = ["init", "--program", str(self.program.dir), "--repo", str(self.repo),
                "--worktree-root", str(self.wt_root)]
        self.assertEqual(main([*argv, "--build-branch", "risk-core"]), 1)
        self.assertFalse(self.program.state.exists())
        self.assertEqual(main([*argv, "--build-branch", "build/risk-core"]), 0)
        self.assertEqual(st.load(self.program).build_branch, "build/risk-core")


class Gate(CiCase):
    def open_pr(self) -> None:
        store = self.repo / ".git" / "fake-gh.json"
        store.write_text(json.dumps([{"url": "https://github.test/pr/9", "number": 9, "baseRefName": "engine/base",
                                      "head": "build/t", "title": "stop A", "body": "", "state": "OPEN"}]), "utf-8")

    def test_gate_reruns_its_job_once_after_the_deep_run_is_green(self):
        tip = self.tip()
        self.open_pr()
        rc, lines = ci.gate(self.program, self.settings)
        self.assertEqual(rc, 1)
        self.assertTrue(lines[0].startswith(f"FAIL gate: ship has no green deep run on the PR head {tip[:8]}"))

        with st.locked(self.program) as state:
            state.ci["deep"] = {"tip": tip, "level": "deep", "run_id": "1001", "url": "u", "result": "green"}
        gate_run = self.put_run(headSha=tip, headBranch="build/t", event="pull_request", conclusion="failure",
                                displayTitle="gate build/t", jobs=[job("level"), job("gate", "failure", 77)])
        rid = gate_run["databaseId"]
        rc, lines = ci.gate(self.program, self.settings)
        self.assertEqual((rc, lines), (2, [f"PENDING gate {rid}: rerun job 77 now that the deep run is green on {tip[:8]}"]))
        self.assertIn(["run", "rerun", str(rid), "--job", "77", "-R", "owner/qmx"], self.calls())

        rc, lines = ci.gate(self.program, self.settings)
        self.assertEqual(rc, 2)
        self.assertTrue(lines[0].startswith(f"PENDING gate {rid}: queued"), lines)

        data = self.runs()
        data["runs"][0]["jobs"][1].update({"status": "completed", "conclusion": "success"})
        self.store.write_text(json.dumps(data), "utf-8")
        rc, lines = ci.gate(self.program, self.settings)
        self.assertEqual(rc, 0, lines)
        self.assertTrue(lines[0].startswith(f"PASS gate {rid} on {tip[:8]}"), lines)

        data["runs"][0]["jobs"][1].update({"conclusion": "failure"})
        self.store.write_text(json.dumps(data), "utf-8")
        rc, lines = ci.gate(self.program, self.settings)
        self.assertEqual(rc, 1)
        self.assertTrue(lines[0].startswith(f"FAIL gate {rid} red again after its rerun"), lines)
        self.assertEqual(sum(1 for c in self.calls() if c[:2] == ["run", "rerun"]), 1)


if __name__ == "__main__":
    unittest.main()
