"""The chaos harness (FACTORY-DESIGN 13.1, unit U12): a version-2 program on a scratch repo, scripted agents,
and the faults of the edge-case matrix (section 6), so `test_chain_chaos.py` can break the conveyor on purpose
and read the end state it reaches.

It builds on `test_chain.ChainCase` (a bare remote, a clone, the plans worktree, fake `claude` and fake `gh`,
a temp factory home with stub plan checks) and adds:

- `make_program(kind=..., stops=..., slices=...)`: `PROGRAM.yaml` (11.4), `SLICES.md` with `stop` and `lane`
  columns, a brief per slice, the gates logged as `ship gate` would. Default: stop A has four slices in two
  lanes (`a1`, `a2` in L1; `a3`, `a4` in L2), stop B two (`b1`, `b2`), each on its own file. `kind="audit"`
  writes an audit program with no `SLICES.md` (the stage is in `phase.json`).
- `happy()`: the scripted agents of a run with nothing wrong; `script(match, ...)` puts a rule ahead of them.
- Faults: `kill_after(activity, n)` (the conveyor exits hard right after the n-th finished activity, through
  `SHIP_CHAIN_STOP_AFTER`), `kill_children()`, `remote_down()`/`remote_up()`, `mains(False)` (a file
  `SHIP_FAKE_MAINS` names, read on every power step, so a running conveyor loses mains), `clock(iso)` and
  `advance(s)` (`SHIP_FAKE_NOW`), `deep("queued"|"red"|"green")` and `gate(red=...)` (the fake `gh`'s flags),
  `target_commit(files)` (another program's merge lands on the target).
- Driving: `chain(*args)`, `start(*args)` (in the background), `chain_until_done(max_runs)`.
- Reading: `end_state()` and `assert_converged(...)`: the property every chaos scenario shares (13.1): the
  program reaches the end an undisturbed run reaches, no orphan process, no held lock, each landed slice in one
  commit, and no attempt counted for an infrastructure fault.

Standard library only; no real Claude run, no real merge, no scheduled task; the factory home is a temp folder.
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from ship import phase
from ship import state as st
from ship.launch import KIT
from ship.layout import Program
from ship.proc import created, kill_tree, pid_alive
from ship.settings import load_settings
from ship.tests.fixture import BRIEF, PY, sh, sign_gates, write
from ship.tests.test_chain import EVIDENCE, PLAN_CLEAN, READER, ChainCase

SOURCE = "def {slice}():\n    return '{slice}'\n\n\n# {dispatch}\n"  # a restarted builder always has a change to commit


@dataclass(frozen=True)
class Stop:
    id: str
    tier: str = "core"
    handoff: str = "ready"


DEFAULT_STOPS = (Stop("A"), Stop("B"))
DEFAULT_SLICES = (("a1", "A", "L1"), ("a2", "A", "L1"), ("a3", "A", "L2"), ("a4", "A", "L2"),
                  ("b1", "B", "L1"), ("b2", "B", "L2"))


def builder(match: str = "builder:", *, sleep: float = 0, extra: dict | None = None, times: int | None = None) -> dict:
    """A builder that writes its slice's file (and `extra` files), commits, pushes, writes the evidence and replies
    READY with its head."""
    steps = [{"write": {"pkg/{slice}.py": SOURCE, **(extra or {})}}, {"commit": "{slice}: work"}, {"push": True},
             {"file": EVIDENCE}]
    if sleep:
        steps.insert(0, {"sleep": sleep})
    rule = {"match": match, "steps": steps, "reply": "Built it.\nREADY {head}"}
    if times is not None:
        rule["times"] = times
    return rule


def verdict(word: str = "CLEAN", *, round_: int = 1, match: str = "verdict:", times: int | None = None,
            finding: str = "", fix_slices: tuple[str, ...] = ()) -> dict:
    """The verdict worker. BLOCKED writes `finding` as an Important and, in round 1, the fix folder
    `<program>-fix-<stop>` with one slice per `fix_slices`."""
    name = "REVIEW.md" if round_ == 1 else "REVIEW-2.md"
    body = f"VERDICT: {word}\n\n" + (f"- Important: {finding}\n\n" if word == "BLOCKED" else "") + \
        f"END {{tip}} checkpoint-{{stop}}-round-{round_}\n"
    files = {f"{{program}}/stop-review/{{stop}}/{name}": body}
    if word == "CLEAN":
        files["{program}/merge/{stop}-pr.md"] = "Stop {stop}.\n\nShipped by Mubarak.\n"
    if word == "BLOCKED" and fix_slices:
        rows = "".join(f"| {s} | Fix {s} | {{stop}} | L1 | - | pkg/{s}.py | S |\n" for s in fix_slices)
        files["{program}-fix-{stop}/PROGRAM.yaml"] = (
            "project: qmx\nprogram: program-fix-{stop}\nkind: fix\nparent: program\nbuild_branch: build/t\n"
            "parent_tip: {tip}\ngates:\n  go: {by: stop-review, at: 2026-11-14, source: \"stop-review/{stop}/REVIEW.md\", "
            "advance: yes}\nstop_points:\n  - id: {stop}\n    tier: core\n    handoff: ready\n"
            f"chains:\n  - ask: S1\n    verdict: core\n    plan: [S1.a]\n    arch: [A1]\n    slices: [{', '.join(fix_slices)}]\n")
        files["{program}-fix-{stop}/SLICES.md"] = (
            "| id | name | stop | lane | depends on | files | size |\n|---|---|---|---|---|---|---|\n" + rows)
        for s in fix_slices:
            files[f"{{program}}-fix-{{stop}}/slices/{s}/BRIEF.md"] = BRIEF
    rule = {"match": match, "steps": [{"file": files}], "reply": f"DONE {{program}}/stop-review/{{stop}}/{name}"}
    if times is not None:
        rule["times"] = times
    return rule


def slices_table(slices) -> str:
    """Rows (id, stop, lane) on `pkg/<id>.py`, or (id, stop, lane, files)."""
    rows = "".join(f"| {s[0]} | Slice {s[0]} | {s[1]} | {s[2]} | - | {s[3] if len(s) > 3 else 'pkg/' + s[0] + '.py'} | S |\n"
                   for s in slices)
    return "| id | name | stop | lane | depends on | files | size |\n|---|---|---|---|---|---|---|\n" + rows


def program_yaml(base: str, stops, slices, kind: str = "feature", extra: str = "") -> str:
    by_stop = {s.id: [row[0] for row in slices if row[1] == s.id] for s in stops}
    core = sum(len(by_stop[s.id]) for s in stops if s.tier == "core")
    later = sum(len(by_stop[s.id]) for s in stops if s.tier != "core")
    stop_rows = "".join(f"  - id: {s.id}\n    tier: {s.tier}\n    handoff: {s.handoff}\n" for s in stops)
    chains = "".join(f"  - ask: S{n}\n    verdict: {s.tier}\n    plan: [S{n}.a]\n    arch: [A{n}]\n"
                     f"    slices: [{', '.join(by_stop[s.id])}]\n" for n, s in enumerate(stops, 1))
    return (f"project: qmx\nprogram: program\nkind: {kind}\nparent: null\nbuild_branch: build/t\n"
            f"parent_tip: {base}\ncore_sentence: \"every core slice exists\"\n"
            f"budget:\n  core: {max(core, 1)}\n  later: {later}\n  checkpoints: {len(stops)}\n"
            "gates:\n  cut: {by: him, at: 2026-11-14, source: \"t:1\", advance: no}\n"
            "  plan: {by: him, at: 2026-11-14, source: \"t:2\", advance: yes}\n  go: null\n"
            f"stop_points:\n{stop_rows}chains:\n{chains}{extra}abandoned: null\n")


class ChaosCase(ChainCase):
    """A chaos scenario: a program with the default shape (or the class's `stops` and `slices`), the happy
    agents, and every fault the matrix needs."""

    stops = DEFAULT_STOPS
    slices = DEFAULT_SLICES
    pool = 3

    def setUp(self):
        super().setUp()
        self.script_file = self.__dict__.pop("script")  # ChainCase's path; `script` is the override method here
        self.mains_file = write(self.root / "mains.txt", "1")
        self.now_file: Path | None = None
        self.overrides: list[dict] = []
        self.base_rules: list[dict] = []
        self.next_env: dict[str, str] = {}
        self.set_pool(self.pool)
        self.make_program(stops=self.stops, slices=self.slices)
        self.happy()

    def tearDown(self):
        for lock in self.plans.glob("*/chain.lock"):  # a scenario that failed mid-run leaves nothing running
            self.kill_children(lock)
        super().tearDown()

    # -- the program --

    def set_pool(self, workers: int) -> None:
        path = self.factory / "projects" / "qmx" / "project.toml"
        text = path.read_text("utf-8")
        path.write_text(text.replace("workers = 3", f"workers = {workers}"), "utf-8")

    def make_program(self, kind: str = "feature", stops=DEFAULT_STOPS, slices=DEFAULT_SLICES, extra: str = "",
                     area: tuple[str, ...] = ("pkg",)) -> None:
        """Write the program folder afresh (no state.json, no phase.json) and log its gates."""
        for path in (self.program.state, self.program.phase_file, self.program.slices_md):
            path.unlink(missing_ok=True)
        self.slices = tuple(slices)
        self.stops = tuple(stops)
        if kind == "audit":
            write(self.program.project_file, audit_yaml(self.base, area))
        else:
            write(self.program.slices_md, slices_table(slices))
            for row in slices:
                write(self.program.brief(row[0]), BRIEF)
            write(self.program.project_file, program_yaml(self.base, stops, slices, kind, extra))
        sign_gates(self.program)

    # -- the agents --

    def happy(self) -> None:
        """Plan review CLEAN, builders READY, readers DONE, verdicts CLEAN; any other worker gets fake_claude's
        default reply, `DONE fake`."""
        self.base_rules = [PLAN_CLEAN, builder(), READER, verdict()]
        self._write_rules()

    def script(self, match: str, kind: str = "ok", times: int | None = None, steps: list | None = None,
               reply: str | None = None, **more) -> dict:
        """A rule ahead of the happy ones; among overrides, the one added first is tried first."""
        rule = {"match": match, "kind": kind, **more}
        if times is not None:
            rule["times"] = times
        if steps is not None:
            rule["steps"] = steps
        if reply is not None:
            rule["reply"] = reply
        self.overrides.append(rule)
        self._write_rules()
        return rule

    def rule(self, rule: dict) -> None:
        self.overrides.append(rule)
        self._write_rules()

    def _write_rules(self) -> None:
        self.script_file.write_text(json.dumps(self.overrides + self.base_rules), "utf-8")

    def prompt(self, name: str, text: str = "") -> Path:
        return write(self.root / "prompts" / name, text or f"{name} for {{PROGRAM}} with {{SHIP}}\n")

    # -- faults --

    def kill_after(self, activity: str, n: int) -> None:
        """The next conveyor exits hard (137) right after the n-th finished `activity` (`any` counts all)."""
        self.next_env["SHIP_CHAIN_STOP_AFTER"] = f"{activity}:{n}"

    def kill_children(self, lock: Path | None = None) -> list[int]:
        """Kill every process chain.lock names (the conveyor and its children), as a dead laptop would; matched
        by creation time, so a reused pid is never killed."""
        try:
            body = json.loads((lock or self.program.chain_lock).read_text("utf-8"))
        except (OSError, ValueError):
            return []
        pids = []
        for row in [body, *body.get("children", [])]:
            pid, when = int(row.get("pid") or 0), row.get("created")
            if pid and pid != os.getpid() and (created(pid) == when if when is not None else pid_alive(pid)):
                kill_tree(pid)
                pids.append(pid)
        return pids

    def remote_down(self) -> None:
        self.remote.rename(self.remote.with_name("remote-away.git"))

    def remote_up(self) -> None:
        self.remote.with_name("remote-away.git").rename(self.remote)

    def mains(self, on: bool) -> None:
        self.mains_file.write_text("1" if on else "0", "utf-8")

    def clock(self, iso: str) -> None:
        self.now_file = self.now_file or self.root / "now.txt"
        self.now_file.write_text(iso, "utf-8")

    def advance(self, seconds: float) -> None:
        import datetime as dt

        now = dt.datetime.fromisoformat(self.now_file.read_text("utf-8").strip())
        self.now_file.write_text((now + dt.timedelta(seconds=seconds)).isoformat(), "utf-8")

    def gh_flag(self, name: str, on: bool) -> None:
        common = sh(self.repo, "git", "rev-parse", "--git-common-dir")
        path = (Path(common) if Path(common).is_absolute() else self.repo / common) / name
        if on:
            path.write_text("x")
        else:
            path.unlink(missing_ok=True)

    def deep(self, result: str) -> None:
        """`queued`: deep runs are dispatched and never finish; `red`/`green`: they finish at once."""
        self.gh_flag("fake-gh-auto", result != "queued")
        self.gh_flag("fake-gh-deep-red", result == "red")

    def gate(self, red: bool) -> None:
        self.gh_flag("fake-gh-gate-red", red)

    def target_commit(self, files: dict[str, str], message: str = "other program: merged") -> str:
        """Push a commit to the target branch (`main`) from a side clone; its sha."""
        side = self.root / f"side-{time.monotonic_ns()}"
        sh(self.root, "git", "clone", "-q", str(self.remote), str(side))
        for key, value in (("user.name", "other"), ("user.email", "o@test.invalid"), ("core.autocrlf", "false")):
            sh(side, "git", "config", key, value)
        sh(side, "git", "checkout", "-q", "main")
        for rel, text in files.items():
            write(side / rel, text)
        sh(side, "git", "add", "-A")
        sh(side, "git", "commit", "-q", "-m", message)
        sh(side, "git", "push", "-q", "origin", "HEAD:refs/heads/main")
        return sh(side, "git", "rev-parse", "HEAD")

    # -- driving --

    def env(self, **more):
        env = {k: v for k, v in os.environ.items() if not k.startswith("SHIP_")}
        env.update(FAKE_CLAUDE_SCRIPT=str(self.script_file), **more)
        env["SHIP_FAKE_MAINS"] = str(self.mains_file)
        if self.now_file is not None:
            env["SHIP_FAKE_NOW"] = str(self.now_file)
        return env

    def chain(self, *args, timeout=600, program=None, **env):
        env = {**self.next_env, **env}
        self.next_env = {}
        return super().chain(*args, timeout=timeout, program=program, **env)

    def start(self, *args, **env):
        env = {**self.next_env, **env}
        self.next_env = {}
        return super().start(*args, **env)

    def ship(self, *args, timeout=300, **env) -> int:
        done = subprocess.run([PY, str(KIT), *args], capture_output=True, text=True, encoding="utf-8",
                              errors="replace", env=self.env(**env), stdin=subprocess.DEVNULL, timeout=timeout)
        self.out = done.stdout + done.stderr
        return done.returncode

    def chain_until_done(self, max_runs: int = 20, **env) -> list[int]:
        """Run the conveyor again after every exit a fault caused (137); the exits, the last one first-class."""
        exits = []
        while True:
            rc = self.chain(**env)
            exits.append(rc)
            if rc != 137:
                return exits
            self.assertLess(len(exits), max_runs, self.out)

    # -- reading --

    def state(self) -> st.State:
        return st.load(self.program)

    def calls(self, *words: str) -> list[dict]:
        """fake-claude.log rows whose --name holds every word."""
        rows = []
        for program in [self.program, *[Program(p) for p in self.plans.glob("program-fix-*")]]:
            path = program.dir / "fake-claude.log"
            if path.exists():
                rows += [json.loads(x) for x in path.read_text("utf-8").splitlines() if x.strip()]
        rows.sort(key=lambda r: r["at"])
        return [r for r in rows if set(words) <= set(r["argv"][r["argv"].index("--name") + 1].split())]

    def waits(self) -> list[str]:
        out = []
        for path in (self.program.waits, self.program.waiting):
            if path.exists():
                out += [x for x in path.read_text("utf-8").splitlines() if phase.UNANSWERED.match(x)]
        return out

    def chain_log(self) -> str:
        path = self.program.notes_dir / "chain.log"
        return path.read_text("utf-8") if path.exists() else ""

    def target_files(self) -> list[str]:
        sh(self.repo, "git", "fetch", "-q", "origin")
        return sh(self.repo, "git", "ls-tree", "-r", "--name-only", "origin/main").splitlines()

    def build_subjects(self) -> list[str]:
        sh(self.repo, "git", "fetch", "-q", "origin")
        return sh(self.repo, "git", "log", "--first-parent", "--format=%s", "origin/build/t").splitlines()

    def orphans(self) -> list[str]:
        """Processes a worker folder or chain.lock names that still run (matched by creation time)."""
        found = []
        for started in self.plans.rglob("workers/*/started.json"):
            try:
                pid = int(json.loads(started.read_text("utf-8"))["pid"])
            except (OSError, ValueError, KeyError):
                continue
            when = created(pid)
            if when is not None and abs(when - started.stat().st_mtime) < 30:
                found.append(f"{started.parent.name} pid {pid}")
        for lock in self.plans.rglob("chain.lock"):
            try:
                body = json.loads(lock.read_text("utf-8"))
            except (OSError, ValueError):
                continue
            for row in [body, *body.get("children", [])]:
                pid, when = int(row.get("pid") or 0), row.get("created")
                if pid and when is not None and created(pid) == when:
                    found.append(f"{lock.parent.name} chain.lock {row.get('role') or 'conveyor'} pid {pid}")
        return found

    def held_locks(self) -> list[str]:
        """chain.lock files, and the factory's merge lock, Fable seat and pool slots with a live holder."""
        from ship import locks

        held = [f"{p.parent.name}/chain.lock" for p in self.plans.glob("*/chain.lock")]
        run = self.factory / "run"
        merge = locks._read(run / "merge-qmx.lock")
        if merge.get("program"):
            held.append(f"merge-qmx.lock {merge['program']}")
        if locks.FileLock(run / "fable.lock").held_by_live():
            held.append("fable.lock")
        for slot in sorted((run / "pool").glob("*.slot")) if (run / "pool").exists() else []:
            body = locks._read(slot)
            if locks._alive(body.get("pid"), body.get("created")) or locks._alive(body.get("worker"),
                                                                                  body.get("worker_created")):
                held.append(slot.name)
        return held

    def end_state(self) -> dict:
        p = phase.read(self.program, load_settings(self.program.dir))
        state = self.state() if self.program.state.exists() else None
        subjects = self.build_subjects() if state else []
        target = set(self.target_files())
        landed = [s.id for s in state.slices.values() if s.status == st.Status.LANDED] if state else []
        claims = []
        try:
            from ship import claims as cl

            claims = [(r.program, r.kind, r.pattern) for r in
                      cl.for_program(self.program, load_settings(self.program.dir)).live()]
        except Exception:  # noqa: BLE001 - no claims list is no live claim
            claims = []
        return {
            "phase": (p["next"], p.get("status")),
            "merged": list(state.merged) if state else [],
            "target_has": sorted(row[0] for row in self.slices if f"pkg/{row[0]}.py" in target),
            "landed_once": all(sum(x.startswith(f"{sid}: ") for x in subjects) == 1 for sid in landed),
            "slices": {sid: (s.status.value, s.attempts, s.restarts) for sid, s in state.slices.items()} if state else {},
            "waits": self.waits(),
            "locks": self.held_locks(),
            "claims": claims,
            "orphans": self.orphans(),
        }

    def assert_converged(self, merged=None, target_has=None, attempts: dict | None = None, restarts: dict | None = None,
                         waits: int | None = 0) -> dict:
        """The end an undisturbed run reaches, and always: no orphan process, no held lock, each landed slice in one
        commit, no attempt counted for an infrastructure fault (every landed slice has attempts 1 unless
        `attempts` says otherwise), and the program done."""
        end = self.end_state()
        stops = [s.id for s in self.stops]
        self.assertEqual(end["merged"], list(merged if merged is not None else stops), end)
        want = sorted(target_has if target_has is not None else [row[0] for row in self.slices])
        self.assertEqual(end["target_has"], want, end)
        self.assertTrue(end["landed_once"], self.build_subjects())
        self.assertEqual(end["orphans"], [], end)
        self.assertEqual(end["locks"], [], end)
        self.assertEqual([c for c in end["claims"] if c[0] == self.program.dir.name], [], end)
        for sid, (status, n_attempts, n_restarts) in end["slices"].items():
            if status != st.Status.LANDED.value:
                continue
            self.assertEqual(n_attempts, (attempts or {}).get(sid, 1), f"{sid}: {end['slices'][sid]}")
            if restarts is not None and sid in restarts:
                self.assertEqual(n_restarts, restarts[sid], f"{sid}: {end['slices'][sid]}")
        self.assertEqual(end["phase"][0], "done", end)
        if waits == 0:
            self.assertEqual(end["phase"], ("done", "done"), end)
        if waits is not None:
            self.assertEqual(len(end["waits"]), waits, end["waits"])
        return end

    def until(self, check, timeout=240, what=""):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if check():
                return
            time.sleep(0.1)
        raise AssertionError(f"timed out waiting for {what}\n{self.chain_log()[-3000:]}")

    def children(self, role: str = "") -> list[dict]:
        try:
            body = json.loads(self.program.chain_lock.read_text("utf-8") or "{}")
        except (OSError, ValueError):
            return []
        return [c for c in body.get("children", []) if not role or c.get("role") == role]


def audit_yaml(base: str, area=("pkg",), parent: str = "null", extra: str = "") -> str:
    return (f"project: qmx\nprogram: program\nkind: audit\nparent: {parent}\nbuild_branch: build/t\n"
            f"parent_tip: {base}\narea: [{', '.join(area)}]\ncore_sentence: \"the area is fit to build on\"\n"
            "budget:\n  core: 1\n  later: 0\n  checkpoints: 1\n"
            "gates:\n  cut: {by: him, at: 2026-11-14, source: \"t:1\", advance: no}\n"
            "  plan: {by: him, at: 2026-11-14, source: \"t:2\", advance: yes}\n  go: null\n"
            f"stop_points: []\nchains: []\n{extra}abandoned: null\n")
