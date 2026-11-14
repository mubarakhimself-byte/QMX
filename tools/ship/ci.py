"""ci: qmx-ci on GitHub Actions as the test backend, read through `gh` with the repo always named.

qmx-ci's levels (`.github/workflows/qmx-ci.yml`): a push to `slice/**` runs `slice` (Linux); a push
to `build/**` runs `land` (touched tests on Linux and Windows); `gh workflow run` runs `deep` (the
whole suite sharded on both systems, lint, Vulture, Skylos, mutmut, then the `deep-verdict`
artifact); a pull request into engine/base runs `gate`, which passes only on a green deep run whose
verdict names the PR head.

Here:
- `start`: dispatch a run on the build tip, or re-attach to one recorded or already running for that
  tip, so a power cut or a second `nightly` never starts a second run. Raises Unavailable when
  GitHub cannot run it (gh missing, no network, the workflow not at the tip); `nightly` then runs
  locally.
- `read_run` and `judge`: a finished run's test shards become the shape `suite.run_packages`
  returns, keyed by shard (`suite-linux-3`), outcomes keyed `system|unit|class::name`; then the same
  verdict nightly gives a local run, plus every other failed job and the deep-verdict check.
- `slice_linux` and `linux_gate`: the Linux slice run as evidence for slice_checks and land.
- `land_runs`: the land run of each landing, as evidence for status and the checkpoint.
- `gate`: the checkpoint PR's gate job; rerun once after the deep run is green.
- `fetch_summary` and `summary` (`ship ci summary [--sha SHA]`): the deep run's `summary.json` (FACTORY-DESIGN
  11.11) into `checks/_nightly/<tip8>/summary.json`, only when its `sha` is that very commit (D-L22): a
  summary of another commit never stands for this one. Its `reds` (each with `kind` and `blocks`) and its
  `quality` rows are qmx-ci's own verdict; `summary_fails` turns the blocking ones into FAIL lines.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import re
import shutil
import time
from pathlib import Path

from ship import state as st
from ship.gitx import GitError, env_no_prompt, git_rc, remote_sha, run
from ship.layout import Program
from ship.settings import Settings, repo_args
from ship.suite import Outcome, TestRun, parse_junit
from ship.wrapper import RunResult

TEST_JOBS = ("suite-", "tests-")
VERDICT_ARTIFACT = "deep-verdict"
RUN_FIELDS = "databaseId,headSha,headBranch,status,conclusion,url,event,displayTitle,createdAt"
RED_OUTCOMES = (Outcome.ASSERTION, Outcome.FAILED, Outcome.ERROR)
RUN_URL = re.compile(r"/actions/runs/(\d+)")


class Unavailable(Exception):
    """GitHub cannot run this now; the local run stands in."""


def outcome(run_: dict) -> str:
    """green, red, pending or cancelled, from a run's or a job's status and conclusion."""
    if run_.get("status") != "completed":
        return "pending"
    conclusion = run_.get("conclusion") or ""
    if conclusion == "success":
        return "green"
    if conclusion in ("cancelled", "skipped", "stale"):
        return "cancelled"
    return "red"


def level_of(run_: dict) -> str:
    """qmx-ci's run-name starts with the level: `deep build/x`."""
    return (run_.get("displayTitle") or "").split(" ", 1)[0]


@dataclasses.dataclass
class Gh:
    settings: Settings
    cwd: Path

    def call(self, *args: str, repo_flag: bool = True) -> str:
        argv = [*self.settings.gh, *args, *(repo_args(self.settings) if repo_flag else [])]
        env = env_no_prompt()
        env.update({"GH_PROMPT_DISABLED": "1", "NO_COLOR": "1", "GH_NO_UPDATE_NOTIFIER": "1"})
        return run(argv, self.cwd, self.settings.git_timeout_s, env=env).stdout

    def runs(self, branch: str, event: str | None = None, sha: str | None = None) -> list[dict]:
        args = ["run", "list", "--workflow", self.settings.ci_workflow, "--branch", branch,
                "--json", RUN_FIELDS, "--limit", "30"]
        if event:
            args += ["--event", event]
        if sha:
            args += ["--commit", sha]
        found = json.loads(self.call(*args) or "[]")
        return [r for r in found if not sha or r.get("headSha") == sha]

    def view(self, run_id: str) -> dict:
        return json.loads(self.call("run", "view", str(run_id), "--json", RUN_FIELDS + ",jobs"))

    def dispatch(self, branch: str, level: str) -> str:
        return self.call("workflow", "run", self.settings.ci_workflow, "--ref", branch, "-f", f"level={level}")

    def download(self, run_id: str, name: str, dest: Path) -> bool:
        """One artifact into `dest`, once: a finished job's artifact never changes."""
        if dest.is_dir():
            return True
        part = dest.with_name(dest.name + ".part")
        shutil.rmtree(part, ignore_errors=True)
        try:
            self.call("run", "download", str(run_id), "-n", name, "-D", str(part))
        except GitError:
            shutil.rmtree(part, ignore_errors=True)
            return False
        part.rename(dest)
        return True

    def rerun_job(self, run_id: str, job_id: str) -> None:
        self.call("run", "rerun", str(run_id), "--job", str(job_id))

    def prs(self, head: str, base: str) -> list[dict]:
        return json.loads(self.call("pr", "list", "--head", head, "--base", base, "--state", "open",
                                    "--json", "number,url,headRefOid") or "[]")


def gh_for(state: st.State, settings: Settings) -> Gh:
    return Gh(settings, Path(state.repo))


def workflow_at(state: st.State, settings: Settings, sha: str) -> bool:
    path = f".github/workflows/{settings.ci_workflow}"
    return git_rc(Path(state.repo), "cat-file", "-e", f"{sha}:{path}", timeout=settings.git_timeout_s) == 0


# ---- the checkpoint run --------------------------------------------------------------------------


def start(program: Program, settings: Settings, level: str = "deep", fresh: bool = False) -> list[str]:
    """Dispatch a `level` run on the build tip, or re-attach to one for that tip. Never two."""
    state = st.load(program)
    repo, t = Path(state.repo), settings.git_timeout_s
    gh = gh_for(state, settings)
    try:
        run(["git", "fetch", "-q", state.remote], repo, t)
        tip = remote_sha(repo, state.remote, state.build_branch, t)
    except GitError as exc:
        raise Unavailable(f"cannot read {state.build_branch}: {exc}") from exc
    if not tip:
        raise Unavailable(f"{state.build_branch} is not on {state.remote}")
    rec = state.ci.get("deep") or {}
    if rec.get("tip") == tip and rec.get("level", "deep") == level and rec.get("run_id") and not fresh:
        try:
            got = gh.view(rec["run_id"])
        except GitError as exc:
            return [(f"CI {level} {rec['run_id']} recorded for {tip[:8]}; GitHub unreachable now ({short(exc)}), "
                     "nothing dispatched; ship ci status retries")]
        if outcome(got) != "cancelled":
            return [f"CI {level} {rec['run_id']} attached on {tip[:8]}: {got.get('status')} {got.get('url')}"]
    if not workflow_at(state, settings, tip):
        raise Unavailable(f".github/workflows/{settings.ci_workflow} is not on {state.build_branch} at {tip[:8]}")
    try:
        listed = gh.runs(state.build_branch, "workflow_dispatch", tip)
    except GitError as exc:
        raise Unavailable(f"gh cannot read GitHub: {short(exc)}") from exc
    if not fresh:
        for got in listed:  # newest first: a run dispatched before a crash, never recorded
            if level_of(got) == level and outcome(got) != "cancelled":
                _record(program, tip, level, got, attached=True)
                return [(f"CI {level} {got['databaseId']} attached on {tip[:8]} (found running, not recorded): "
                         f"{got.get('status')} {got.get('url')}")]
    before = {str(r["databaseId"]) for r in listed}
    try:
        said = gh.dispatch(state.build_branch, level)
    except GitError as exc:
        raise Unavailable(f"gh workflow run failed: {short(exc)}") from exc
    found = RUN_URL.search(said)
    deadline = time.monotonic() + settings.ci_find_s
    got = None
    while got is None:
        try:
            listed = gh.runs(state.build_branch, "workflow_dispatch", tip)
        except GitError:
            listed = []
        got = next((r for r in listed if (found and str(r["databaseId"]) == found.group(1))
                    or (not found and str(r["databaseId"]) not in before and level_of(r) == level)), None)
        if got is None:
            if time.monotonic() >= deadline:
                return [(f"CI {level} dispatched on {tip[:8]}; the run is not listed yet. "
                         "ship ci start again attaches to it, never a second one")]
            time.sleep(min(10, settings.ci_poll_s))
    _record(program, tip, level, got, attached=False)
    return [f"CI {level} {got['databaseId']} dispatched on {tip[:8]}: {got.get('url')}"]


def _record(program: Program, tip: str, level: str, got: dict, attached: bool) -> None:
    with st.locked(program) as state:
        state.ci["deep"] = {"tip": tip, "level": level, "run_id": str(got["databaseId"]), "url": got.get("url"),
                            "at": st.now_iso(), "result": None}
        state.log("ci", None, level=level, tip=tip, run_id=str(got["databaseId"]),
                  how="attached" if attached else "dispatched")


def short(exc: Exception) -> str:
    """What gh said, without the argv run() puts in front of it."""
    text = str(exc).strip()
    said = re.search(r"exited -?\d+: (.*)", text, re.S)
    text = (said.group(1) if said else text).strip()
    return text.splitlines()[-1][:200] if text else type(exc).__name__


@dataclasses.dataclass
class RunRead:
    """A run as these scripts see it."""

    run: dict
    tests: dict[str, TestRun]  # finished test shards, the shape suite.run_packages returns
    pending: list[str]  # job names still queued or running
    failed_jobs: list[dict]  # finished non-test jobs that did not succeed
    verdict: dict | None  # deep-verdict's verdict.json, when the run left one


def read_run(gh: Gh, run_id: str, out: Path) -> RunRead:
    got = gh.view(run_id)
    tests: dict[str, TestRun] = {}
    pending, failed = [], []
    for job in got.get("jobs", []):
        name = job.get("name", "")
        if job.get("conclusion") == "skipped" or "${{" in name:
            continue
        if outcome(job) == "pending":
            pending.append(name)
            continue
        if not name.startswith(TEST_JOBS):
            if outcome(job) != "green":
                failed.append(job)
            continue
        key = name.replace(" ", "-")
        folder = out / f"ci-out-{key}"
        gh.download(run_id, f"ci-out-{key}", folder)
        outcomes, ok = read_shard(folder, key.split("-")[1])
        rc = 0 if outcome(job) == "green" else 1
        tests[key] = TestRun(RunResult(rc, job.get("conclusion") == "timed_out", _seconds(job), folder), ok, outcomes)
    verdict = None
    if outcome(got) != "pending" and gh.download(run_id, VERDICT_ARTIFACT, out / VERDICT_ARTIFACT):
        try:
            verdict = json.loads((out / VERDICT_ARTIFACT / "verdict.json").read_text("utf-8"))
        except (OSError, ValueError):
            verdict = None
    return RunRead(got, tests, pending, failed, verdict)


def read_shard(folder: Path, system: str) -> tuple[dict[str, Outcome], bool]:
    """A test shard's artifact: outcomes from its JUnit files, reds from its reds-*.txt (the list
    qmx-ci judged). A shard finished when it wrote a reds file, or its plan had nothing to run."""
    reds_files = sorted(folder.glob("reds-*.txt"))
    plans = [json.loads(p.read_text("utf-8")) for p in sorted(folder.glob("plan-*.json"))]
    units = {u.replace("/", "_"): u for plan in plans for u in plan.get("units", [])}
    outcomes: dict[str, Outcome] = {}
    for xml in sorted(folder.glob("junit/*.xml")):
        stem = xml.stem.removesuffix("-serial")
        parts = stem.split("-", 2)
        root = units.get(parts[2]) if len(parts) == 3 else None
        if root is None:
            continue
        try:
            found = parse_junit(xml, root)
        except (OSError, SyntaxError):  # ET.ParseError is a SyntaxError: a half-written report counts as none
            found = {}
        for test_id, result in found.items():
            key = f"{system}|{root}|{test_id.split('::', 1)[1]}"
            if outcomes.get(key) not in RED_OUTCOMES:
                outcomes[key] = result
    for path in reds_files:
        for line in path.read_text("utf-8").splitlines():
            if line.strip() and outcomes.get(line.strip()) not in RED_OUTCOMES:
                outcomes[line.strip()] = Outcome.FAILED
    finished = bool(reds_files) or bool(plans and all(not p.get("files") for p in plans))
    return outcomes, finished


def _seconds(job: dict) -> float:
    try:
        a = dt.datetime.fromisoformat(job["startedAt"].replace("Z", "+00:00"))
        b = dt.datetime.fromisoformat(job["completedAt"].replace("Z", "+00:00"))
        return max(0.0, (b - a).total_seconds())
    except (KeyError, TypeError, ValueError, AttributeError):
        return 0.0


def progress(read: RunRead, baseline_new, label: str) -> list[str]:
    """Lines for a run still going: what finished, what is red so far."""
    got = read.run
    done = len(read.tests) + len(read.failed_jobs)
    new = baseline_new(set().union(*(r.red() for r in read.tests.values())) if read.tests else set())
    lines = [(f"PENDING {label} {got.get('status')}: {len(read.pending)} jobs still queued or running, "
              f"{done} finished jobs read; {got.get('url')}")]
    lines += [f"SO-FAR new red {r}" for r in new]
    lines += [f"SO-FAR job {j['name']} {j.get('conclusion')} {j.get('url', '')}".rstrip() for j in read.failed_jobs]
    return lines


# ---- summary.json ------------------------------------------------------------------------------------


@dataclasses.dataclass
class Summary:
    path: Path | None  # checks/_nightly/<sha8>/summary.json, when it is there and names the sha
    why: str = ""  # why there is none
    mismatch: str = ""  # the sha a downloaded summary named instead
    unreachable: bool = False


def deep_run_of(program: Program, settings: Settings, sha: str) -> str | None:
    """The deep run on `sha`: the one state.json records, else the newest GitHub lists (not cancelled)."""
    state = st.load(program)
    rec = state.ci.get("deep") or {}
    if rec.get("tip") == sha and rec.get("run_id"):
        return str(rec["run_id"])
    listed = gh_for(state, settings).runs(state.build_branch, "workflow_dispatch", sha)
    found = next((r for r in listed if level_of(r) == "deep" and outcome(r) != "cancelled"), None)
    return str(found["databaseId"]) if found else None


def fetch_summary(program: Program, settings: Settings, sha: str, run_id: str | None = None) -> Summary:
    """The deep run's `summary` artifact as checks/_nightly/<sha8>/summary.json, only when it names `sha`."""
    target = program.nightly(sha) / "summary.json"
    if target.exists():
        try:
            if str(json.loads(target.read_text("utf-8")).get("sha") or "") == sha:
                return Summary(target)
        except (OSError, ValueError, AttributeError):
            pass
        target.unlink(missing_ok=True)
    try:
        run_id = run_id or deep_run_of(program, settings, sha)
    except GitError as exc:
        return Summary(None, f"GitHub unreachable ({short(exc)})", unreachable=True)
    if not run_id:
        return Summary(None, f"no deep run on {sha[:8]}")
    folder = program.nightly(sha) / "ci-summary"
    try:
        ok = gh_for(st.load(program), settings).download(str(run_id), "summary", folder)
    except GitError as exc:
        return Summary(None, f"GitHub unreachable ({short(exc)})", unreachable=True)
    if not ok or not (folder / "summary.json").exists():
        return Summary(None, f"deep run {run_id} has no summary artifact (yet)")
    try:
        named = str(json.loads((folder / "summary.json").read_text("utf-8")).get("sha") or "")
    except (OSError, ValueError, AttributeError):
        named = ""
    if named != sha:  # D-L22: a summary of another commit never stands for this one
        shutil.rmtree(folder, ignore_errors=True)
        return Summary(None, f"deep run {run_id}'s summary.json names {named[:8] or '(no sha)'}, not {sha[:8]}",
                       mismatch=named or "(none)")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(folder / "summary.json", target)
    return Summary(target)


def summary_fails(summary: dict, already: set[str] = frozenset()) -> list[str]:
    """FAIL lines for what qmx-ci's summary says blocks: every red with `blocks` (a newly flaky test, an
    unfinished shard, a new red; `already` holds canonical ids the caller reports itself) and every new
    quality row with `blocks`."""
    from ship.suite import canon

    out = []
    for red in summary.get("reds") or []:
        if not isinstance(red, dict) or not red.get("blocks"):
            continue
        key = f"{red.get('system')}|{red.get('id')}"
        if red.get("kind") in ("new", "known") and canon(key) in already:
            continue
        out.append(f"FAIL ci-red {red.get('kind')} {key}")
    for row in summary.get("quality") or []:
        if isinstance(row, dict) and row.get("kind") == "new" and row.get("blocks", True):
            out.append(f"FAIL ci-quality {row.get('tool')} {row.get('key')}")
    return out


def summary(program: Program, settings: Settings, sha: str | None = None) -> tuple[int, list[str]]:
    """`ship ci summary [--sha SHA]` (default: the build tip). 0 the summary names that sha and is saved,
    1 there is none for it (or only one of another commit), 3 GitHub cannot be reached."""
    state = st.load(program)
    repo, t = Path(state.repo), settings.git_timeout_s
    try:
        if sha:
            run(["git", "fetch", "-q", state.remote], repo, t, check=False)
            full = run(["git", "rev-parse", "--verify", f"{sha}^{{commit}}"], repo, t).stdout.strip()
        else:
            run(["git", "fetch", "-q", state.remote], repo, t)
            full = remote_sha(repo, state.remote, state.build_branch, t) or ""
    except GitError as exc:
        return 1, [f"FAIL summary: {sha or state.build_branch} is not a commit here ({short(exc)})"]
    if not full:
        return 1, [f"FAIL summary: {state.build_branch} is not on {state.remote}"]
    got = fetch_summary(program, settings, full)
    if got.path is None:
        return (3 if got.unreachable else 1), [f"{'UNREACHABLE' if got.unreachable else 'NONE'} summary for "
                                               f"{full[:8]}: {got.why}"]
    body = json.loads(got.path.read_text("utf-8"))
    reds = [r for r in body.get("reds") or [] if isinstance(r, dict)]
    lines = [f"SUMMARY {got.path}",
             f"{'GREEN' if body.get('green') else 'RED'} {body.get('level')} {full[:8]} {body.get('url', '')}".rstrip(),
             f"REDS {sum(1 for r in reds if r.get('blocks'))} block of {len(reds)}"]
    return 0, lines + summary_fails(body)


# ---- slice and land evidence ---------------------------------------------------------------------


def push_run(gh: Gh, branch: str, sha: str) -> dict | None:
    listed = gh.runs(branch, "push", sha)
    live = [r for r in listed if outcome(r) != "cancelled"]
    return (live or listed or [None])[0]


def slice_linux(state: st.State, settings: Settings, sl: st.Slice) -> tuple[str, str, str]:
    """(PASS|FAIL|PENDING|NOTRUN, detail, url) for the Linux slice run on the slice's pushed head."""
    sha = sl.ci.get("sha") or sl.head
    if not sha:
        return "NOTRUN", "no head yet", ""
    if not workflow_at(state, settings, sha):
        return "NOTRUN", f"{settings.ci_workflow} is not on {sha[:8]}, so GitHub ran no slice run", ""
    try:
        got = push_run(gh_for(state, settings), sl.branch, sha)
    except GitError as exc:
        return "PENDING", f"GitHub unreachable ({short(exc)})", ""
    if got is None:
        return "PENDING", f"no qmx-ci run on {sl.branch} at {sha[:8]} yet", ""
    url = got.get("url", "")
    verdict = {"green": "PASS", "red": "FAIL"}.get(outcome(got), "PENDING")
    said = " ".join(x for x in (got.get("status"), got.get("conclusion")) if x)
    return verdict, f"slice run {said} on {sha[:8]}", url


def checked_at(state: st.State, slice_id: str) -> dt.datetime | None:
    for event in reversed(state.events):
        if event.get("slice") == slice_id and event.get("kind") == "status" and event.get("to") == "checked":
            return dt.datetime.fromisoformat(event["at"])
    return None


def linux_gate(state: st.State, settings: Settings, sl: st.Slice, now: dt.datetime) -> tuple[str, str, dict]:
    """land's decision on the Linux slice run: ("land" | "wait" | "red", line, the slice's new ci record).

    Red blocks: the slice goes back for a fix round. Green or not run lands. Pending waits until
    ci_slice_grace_s after slice_checks went green, then lands on the local checks with Linux
    recorded as pending, and the checkpoint reads it again."""
    if sl.ci.get("linux") == "pass":
        return "land", "", dict(sl.ci)
    verdict, detail, url = slice_linux(state, settings, sl)
    rec = {**sl.ci, "sha": sl.ci.get("sha") or sl.head, "linux": verdict.lower(), "url": url}
    tail = f" {url}" if url else ""
    if verdict == "PASS":
        return "land", f"LINUX {sl.id} green: {detail}{tail}", rec
    if verdict == "FAIL":
        return "red", f"Linux slice run red: {detail}{tail}", rec
    if verdict == "NOTRUN":
        return "land", f"LINUX {sl.id} not run: {detail}", rec
    since = checked_at(state, sl.id) or now
    waited = (now - since).total_seconds()
    if waited < settings.ci_slice_grace_s:
        until = (since + dt.timedelta(seconds=settings.ci_slice_grace_s)).isoformat(timespec="minutes")
        return "wait", (f"WAIT {sl.id}: Linux {detail}{tail}; lands on the local checks from {until} "
                        "if it is still not done"), rec
    return "land", (f"LINUX {sl.id} pending after {waited / 60:.0f} min: {detail}{tail}; landing on the "
                    "local checks, the checkpoint reads it again"), rec


def record_landing(state: st.State, tip: str, batch: str, slices: list[str]) -> None:
    state.ci.setdefault("land", []).append({"tip": tip, "batch": batch, "slices": slices, "result": None, "url": ""})


def land_runs(program: Program, settings: Settings) -> list[str]:
    """Read the land run of each landing not yet final. Evidence only: it never stops a landing."""
    lines: list[str] = []
    with st.locked(program) as state:
        open_ = [r for r in state.ci.get("land", []) if r.get("result") in (None, "pending")]
        if not open_:
            return lines
        gh = gh_for(state, settings)
        for rec in open_:
            try:
                got = push_run(gh, state.build_branch, rec["tip"])
            except GitError as exc:
                lines.append(f"CI land {rec['tip'][:8]} unknown: GitHub unreachable ({short(exc)})")
                break
            if got is None:
                result = "pending" if workflow_at(state, settings, rec["tip"]) else "notrun"
            else:
                result = {"cancelled": "superseded"}.get(outcome(got), outcome(got))
                rec["url"] = got.get("url", "")
            rec["result"] = result
            if result == "red":
                lines.append(f"LAND-RED {rec['tip'][:8]} batch {rec['slices']} {rec['url']}; "
                             "the checkpoint's deep run decides")
            elif result == "pending":
                lines.append(f"CI land {rec['tip'][:8]} pending {rec['url']}".rstrip())
    return lines


# ---- the merge gate --------------------------------------------------------------------------------


def gate(program: Program, settings: Settings, pr: str | None = None) -> tuple[int, list[str]]:
    """0 when the PR's gate job passed on the reviewed head, 1 when it cannot, 2 while it runs.

    The gate passes only on a green deep run whose verdict names the PR head. A PR opened before the
    deep run finished has a failed gate job; once ship records the deep run green on that head,
    this reruns the job (once per gate run)."""
    from ship.project_profile import target_branch

    state = st.load(program)
    gh = gh_for(state, settings)
    base = target_branch(program.dir, settings)  # D-L22: the one target source
    try:
        listed = gh.prs(state.build_branch, base)
    except GitError as exc:
        return 2, [f"PENDING gate: GitHub unreachable ({short(exc)})"]
    chosen = [p for p in listed if not pr or str(p["number"]) == str(pr) or p["url"] == pr]
    if not chosen:
        return 1, [f"FAIL gate: no open PR from {state.build_branch} into {base}"]
    head = chosen[0]["headRefOid"]
    deep = state.ci.get("deep") or {}
    if deep.get("tip") != head or deep.get("result") != "green":
        return 1, [(f"FAIL gate: ship has no green deep run on the PR head {head[:8]} "
                    f"(recorded: {deep.get('result')} on {str(deep.get('tip'))[:8]}); run ship nightly first")]
    try:
        runs = [r for r in gh.runs(state.build_branch, "pull_request", head) if level_of(r) == "gate"]
    except GitError as exc:
        return 2, [f"PENDING gate: GitHub unreachable ({short(exc)})"]
    if not runs:
        return 2, [f"PENDING gate: no gate run on {head[:8]} yet"]
    run_id = str(runs[0]["databaseId"])
    got = gh.view(run_id)
    job = next((j for j in got.get("jobs", []) if j.get("name") == "gate"), None)
    if job is None or outcome(job) == "pending":
        return 2, [f"PENDING gate {run_id}: {job.get('status') if job else 'no gate job yet'} {got.get('url')}"]
    if outcome(job) == "green":
        return 0, [f"PASS gate {run_id} on {head[:8]}: deep run {deep.get('url')} vouches for it; {job.get('url', '')}"]
    with st.locked(program) as fresh:
        reruns = fresh.ci.setdefault("gate", {})
        if reruns.get(run_id):
            return 1, [f"FAIL gate {run_id} red again after its rerun: {job.get('url', got.get('url'))}"]
        try:
            gh.rerun_job(run_id, str(job["databaseId"]))
        except GitError as exc:
            return 2, [f"PENDING gate {run_id}: rerun failed ({short(exc)}); ship ci gate tries again"]
        reruns[run_id] = 1
        fresh.log("ci", None, level="gate", run_id=run_id, how="rerun", job=str(job["databaseId"]))
    return 2, [f"PENDING gate {run_id}: rerun job {job['databaseId']} now that the deep run is green on {head[:8]}"]


def wait(step, settings: Settings) -> tuple[int, list[str]]:
    """Call `step` until it returns 0 or 1, every ci_poll_s, for at most ci_wait_timeout_s."""
    deadline = time.monotonic() + settings.ci_wait_timeout_s
    while True:
        rc, lines = step()
        if rc != 2 or time.monotonic() + settings.ci_poll_s > deadline:
            return rc, lines
        time.sleep(settings.ci_poll_s)


def report(program: Program, settings: Settings, run_id: str) -> tuple[int, list[str]]:
    """Read any qmx-ci run without touching state.json: what finished, its reds against the shared
    baseline at the run's commit, and what still runs. 0 green, 1 red, 2 still running."""
    from ship.suite import baseline_for

    state = st.load(program)
    repo = Path(state.repo)
    out = program.tmp / "ci-read" / str(run_id)
    try:
        read = read_run(gh_for(state, settings), str(run_id), out)
    except GitError as exc:
        return 2, [f"PENDING ci {run_id}: GitHub unreachable ({short(exc)})"]
    sha = read.run.get("headSha", "")
    run(["git", "fetch", "-q", state.remote, sha], repo, settings.git_timeout_s, check=False)
    baseline = baseline_for(repo, sha, settings.git_timeout_s)
    label = f"ci {level_of(read.run)} {run_id} on {read.run.get('headBranch')} {sha[:8]}"
    lines = [f"RUN {label}: {read.run.get('status')} {read.run.get('conclusion') or ''} {read.run.get('url')}"]
    for key, shard in sorted(read.tests.items()):
        reds = shard.red()
        new = baseline.new(reds)
        passed = sum(1 for o in shard.outcomes.values() if o == Outcome.PASSED)
        state_word = "finished" if shard.junit_ok else "no reds file (did not finish)"
        lines.append(f"SHARD {key} {state_word}: {passed} passed, {len(reds)} red, {len(new)} not in "
                     f"{baseline.source}")
        lines += [f"  NEW RED {r}" for r in new]
    lines += [f"JOB {j['name']} {j.get('conclusion')} {j.get('url', '')}".rstrip() for j in read.failed_jobs]
    lines += [f"RUNNING {name}" for name in read.pending]
    if read.verdict:
        lines.append(f"VERDICT {json.dumps(read.verdict, sort_keys=True)}")
    result = outcome(read.run)
    return {"green": 0, "pending": 2}.get(result, 1), lines
