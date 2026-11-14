"""ship chain: the conveyor (unit U11, FACTORY-DESIGN section 4 and 11.8).

`python tools/ship chain --program P` holds `chain.lock` and polls every `chain_poll_s` seconds. Each loop
it reads `ship phase` (`phase.read`) and ticks the activity for its `next`; an activity starts at most one
thing per tick and never waits on a long command (scripts are children of the kit's own CLI, agents are
`launch()` handles). Every finished step leaves a file, so a conveyor killed anywhere and started again
carries on at the first step with no file.

| next | Activity |
|---|---|
| review | `check_chain --stage handoff` and `check_plan` as children; a FAIL writes `plan-review/FIXES.md` and a `RESULT: FIXES` review (so planner-fix runs); else one `plan-review` worker. `RESULT: QUESTIONS` copies `QUESTIONS.md` into `WAITING.md` and exits 10 |
| planner-fix | one `planner-fix` worker, both checks again, then the review once more (`REVIEW.md` set aside). A second mechanical FIXES writes WAITS; a round started by his answers never counts as that second one, and resets the memory of the first (`planner_fix_done` in `chain.json`). His answers are only what the desk wrote to `<program>/.desk/answers.md` (no worker may write there): every line of `FIXES.md` must quote one of its entries with the same `<id8>:L<line>` source, and the factory's `his_words.py` must find that quote at that transcript line. Any other FIXES line makes it the mechanical round |
| go | when rule 8 holds, `gates.go` by him with the advance gate's source; otherwise exits 10 |
| arm | the gates must be the ones `ship gate` logged, and a fix folder's `ship.toml` and `checks.toml` its parent's; `init_state` (build branch made at `parent_tip` when the remote has none), `preflight`, facts at `parent_tip` and at the target tip; failing facts start one `grounding` worker |
| build | the `ship run` loop (`run.Build`) on the program, or on the fix folder (`build_folder`, armed first) |
| checkpoint-review | `review.Checkpoint`; while it runs, the program's Build keeps pre-building |
| merge | `ship merge X` as a child; 3 and 11 retry next tick. A fix program `merge` wrote is built and reviewed (round 2) before the next try (`phase.read`'s rule) |
| docs | `ship.docs` when it exists (U36), under the project's merge lock; otherwise `docs/<X>.json` records the skip. Never blocks |
| later-handoff | one `later-handoff` worker when its prompt exists; else WAITS |
| audit | the stage in `phase.json`: `census` as a script; `intent` one worker; `quality` (below); `judgement` the judge, then the `audit-screen` worker, then `apply_screen.py`; `audit-handoff` one worker given the audit checkout (`CHECKOUT`). A stage whose prompt is missing: SKIP and WAITS |
| done | `run_report`, `teardown`, the claims released, the final note in `RUN-REPORT.md` |

The audit's `quality` stage: a frozen checkout of the census tip (`<worktree_root>/audit-<program>`, made once,
with the area's packages' `setup` run in it) is shared by the stages that read code; `probe_tests.py` runs once
per package root there (one at a time, as children, each into `probe/<package>.tsv`); a probe that does not exit
0 (or is missing, or runs past its time) writes WAITS and stops (D-L25); then one `audit-reader` worker per
`## Parts` line of `CENSUS.md`, side by side within the worker pool, each launched in that checkout with
`SHIP_PART` (a plain name, checked) and the `PART` and `CHECKOUT` values; a reader whose notes do not end `DONE`
is started again, up to `max_restarts` runs (a usage limit is never one of them), and a reader that replies
`WAITS` is honoured: WAITS, 10; then `collect_findings.py`, whose failure is WAITS too. The audit checkout is
dropped once the hand-off is done.

Every loop it also refreshes `chain.lock` with its children, reads power, internet and GitHub
(`power_watch.step`), and starts no worker before `usage_reset_at`. A `HOLD` (whoever wrote it) starts nothing
new (D-L25): one guard in the tick, before any activity, returns at once when nothing runs; while something
runs, its activity is still ticked so its result is read, and every place that starts something (a worker, a
script child, the build branch push, `init`, the audit checkout, `go`, the docs step, the finish's teardown, a
checkpoint review's readers, deep run and verdict, the build's seats) checks HOLD again right before it and
starts nothing. WAITS lines go to `notes/WAITS-ON-YOU.md`. Exit: 0 finished (or stopped after `STOP-AFTER`'s stop merged), 10 waits on him,
11 another process holds `chain.lock`, 1 an error it could not route (written to WAITS).

`SHIP_CHAIN_STOP_AFTER=<activity>:<n>` (tests) exits hard right after the n-th finished activity of that
name (`any` counts every activity).
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from ship import clock
from ship import launch as ln
from ship import phase
from ship import program as prog
from ship import state as st
from ship.gitx import GitError, git, remote_sha
from ship.layout import Program
from ship.proc import kill_tree, pid_alive, popen_detached, popen_group_kwargs
from ship.proc import created as proc_created
from ship.review import Checkpoint, add_wait
from ship.run import Build, ChainLock, PromptError, Script, prompt_dir, render
from ship.settings import Settings, load_settings

CHECK_FAIL = re.compile(r"^FAIL\b", re.M)
# The audit stages the conveyor runs with a worker: (role, prompt, the stage after it). Each is started by its own
# start_worker call in `audit_*` below, with the values its prompt needs.
AUDIT_WORKERS = {"intent": ("audit-intent", "AUDIT-INTENT.md", "intent-check"),
                 "quality": ("audit-reader", "AUDIT-READER.md", "judgement"),
                 "judgement": ("audit-judge", "AUDIT-JUDGE.md", "verdicts"),
                 "screen": ("audit-screen", "AUDIT-SCREEN.md", "verdicts"),
                 "audit-handoff": ("sweep-handoff", "AUDIT-HANDOFF.md", "")}
CENSUS_TIP = re.compile(r"^Tip:\s*([0-9a-f]{40})\s*$", re.M)
CENSUS_PART = re.compile(r"^- \*\*([^*\s]+)\*\* `([^`]+)`", re.M)
PLAIN_PART = re.compile(r"[A-Za-z0-9_-]+")
HIS_SOURCE = re.compile(r"\b[0-9a-f]{8}:L\d+\b")  # his_words.py's source for a turn of his: <id8>:L<line>
# A quote of his and its source: "<his words>" (<id8>:L<line>), straight or curly quotes.
HIS_QUOTE = re.compile(r"[\"\u201c]([^\"\u201c\u201d]+)[\"\u201d]\s*\(([0-9a-f]{8}:L\d+)\)")


def quotes(line: str) -> list[tuple[str, str]]:
    """The (quote, source) pairs a line holds, the quote's spaces folded."""
    return [(" ".join(q.split()), src) for q, src in HIS_QUOTE.findall(line)]


def desk_answers(program: Program) -> set[tuple[str, str]]:
    """His answers as the desk wrote them, `<program>/.desk/answers.md`: one `- "<his words>" (<id8>:L<line>)`
    line each (any text may come before the quote). No worker may write the folder (the hook)."""
    try:
        text = program.desk_answers.read_text("utf-8")
    except OSError:
        return set()
    return {pair for line in text.splitlines() if line.lstrip().startswith(("- ", "* ")) for pair in quotes(line)}


def his_words_holds(quote: str, source: str, settings: Settings, project: str) -> bool:
    """The factory's `his_words.py` finds `quote` in the turn of his at `source` (`<id8>:L<line>`). Its own time
    limit; a missing script, a failure or a time-out is a no."""
    script = ln.factory_home(settings) / "skills" / "factory-core" / "scripts" / "his_words.py"
    if not script.is_file():
        return False
    pattern = r"\s+".join(re.escape(word) for word in quote.split())
    try:
        done = subprocess.run([sys.executable, str(script), pattern, "--project", project], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
                              timeout=settings.his_words_timeout_s, **popen_group_kwargs())
    except (OSError, subprocess.TimeoutExpired):
        return False
    return done.returncode == 0 and any(line.startswith(f"== {source} ") for line in done.stdout.splitlines())


def his_fixes(path: Path, program: Program | None = None, settings: Settings | None = None,
              project: str = "qmx") -> bool:
    """FIXES.md written from his answers (D-L25): every fix line quotes his words with their `<id8>:L<line>`
    source, each such pair is an entry of `.desk/answers.md`, and `his_words.py` finds each quote at its line.
    Anything else (a line with no quote, a quote the desk never wrote, a source his_words does not confirm)
    makes it the mechanical round."""
    try:
        text = path.read_text("utf-8")
    except OSError:
        return False
    fixes = [x for x in text.splitlines() if x.lstrip().startswith(("- ", "* "))]
    if not fixes or not all(quotes(x) for x in fixes):
        return False
    if program is None or settings is None:
        return False
    desk = desk_answers(program)
    wanted = {pair for x in fixes for pair in quotes(x)}
    if not wanted <= desk:
        return False
    return all(his_words_holds(q, src, settings, project) for q, src in sorted(wanted))


class Stop(Exception):
    def __init__(self, code: int):
        super().__init__(code)
        self.code = code


class Held(Exception):
    """HOLD is on: what was about to start did not (D-L25). The tick ends there; nothing was started."""


def project_values(profile: dict) -> dict[str, str]:
    from ship import project_profile

    return project_profile.project_values(profile)


class Conveyor:
    def __init__(self, program: Program, settings: Settings, lock: ChainLock | None = None):
        from ship import project_profile as profile

        self.program, self.settings, self.lock = program, settings, lock
        self.profile = profile.of_program(program.dir, settings)
        self.roles = ln.load_roles(settings, self.profile)
        self.memo_path = program.dir / "chain.json"
        self.memo = self._load()
        self.builds: dict[str, Build] = {}
        self.checkpoint: Checkpoint | None = None
        self.cp_key: tuple | None = None
        self.worker: tuple[str, ln.Handle] | None = None
        self.side: dict[str, ln.Handle] = {}  # workers that run side by side (the audit's readers)
        self.audit_copy: Path | None = None  # the audit checkout, made once per conveyor process
        self.scripts: list[Script] = []
        self.done_count: Counter = Counter()
        self.exit: int | None = None
        self.last_next = ""
        self.buf: list[str] = []  # this tick's lines, kept when an activity stops the loop
        self.current = None  # (handler, phase) of the activity being ticked
        self.owner = None  # (handler, phase) of the activity whose worker runs; it collects the result

    # -- memo and notes --

    def _load(self) -> dict:
        try:
            return json.loads(self.memo_path.read_text("utf-8"))
        except (OSError, ValueError):
            return {}

    def save(self) -> None:
        tmp = self.memo_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.memo, indent=2) + "\n", "utf-8", newline="\n")
        st.replace(tmp, self.memo_path)

    def log(self, lines: list[str]) -> None:
        if not lines:
            return
        path = self.program.notes_dir / "chain.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp = clock.now().isoformat(timespec="seconds")
        with open(path, "a", encoding="utf-8", newline="\n") as out:
            out.writelines(f"{stamp} {line}\n" for line in lines)

    def wait(self, text: str, see: str = "") -> None:
        add_wait(self.program, text, see)

    def held(self) -> bool:
        return self.program.hold.exists()

    def hold_gate(self, what: str) -> None:
        """Right before anything starts: under HOLD it does not (D-L25)."""
        if self.held():
            raise Held(what)

    def busy(self) -> bool:
        """Something this conveyor started runs, or ended and is not read yet: its result is read even under
        HOLD."""
        return bool(self.worker or self.side or self.scripts or any(b.busy() for b in self.builds.values())
                    or (self.checkpoint is not None and self.checkpoint.busy()))

    def finished(self, activity: str) -> None:
        """One activity finished: count it, and honour SHIP_CHAIN_STOP_AFTER (tests kill the conveyor here)."""
        self.done_count[activity] += 1
        self.done_count["any"] += 1
        self.save()
        want = os.environ.get("SHIP_CHAIN_STOP_AFTER", "")
        name, _, n = want.partition(":")
        if name and n.isdigit() and self.done_count[name] == int(n):
            self.log([f"STOP-AFTER test hook {want} after {activity}"])
            if self.lock:
                self.lock.refresh(self.children())
            os._exit(137)

    # -- children --

    def children(self) -> list[dict]:
        rows = []
        for build in self.builds.values():
            rows += build.children()
        if self.checkpoint:
            rows += self.checkpoint.children()
        workers = ([self.worker] if self.worker else []) + list(self.side.items())
        for name, h in workers:
            rows.append({"pid": h.pid, "created": h.created, "role": h.role.name, "id": name,
                         "session": h.session_id, "started": h.folder.name})
        rows += [{"pid": s.proc.pid, "created": s.created, "role": s.name, "id": s.slice, "started": s.started}
                 for s in self.scripts]
        return rows

    def stop_children(self) -> None:
        for build in self.builds.values():
            build.stop_children()
        if self.checkpoint:
            self.checkpoint.stop_children()
        if self.worker:
            self.worker[1].kill()
            self.worker = None
        for handle in self.side.values():
            handle.kill()
        self.side.clear()
        for s in self.scripts:
            if s.done() is None:
                kill_tree(s.proc.pid)
        self.scripts.clear()

    def child(self, name: str, argv: list[str]) -> Script:
        self.hold_gate(f"the script {name}")
        logs = self.program.checks_root / "_chain"
        logs.mkdir(parents=True, exist_ok=True)
        stamp = clock.now().strftime("%Y%m%dT%H%M%S") + f"-{time.monotonic_ns() % 10**6:06d}"
        log = logs / f"{stamp}-{name}.log"
        with open(log, "w", encoding="utf-8", newline="\n") as out:
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
                                    **popen_group_kwargs())
        script = Script(name, "", proc, log, clock.now().isoformat(timespec="seconds"), (), proc_created(proc.pid))
        self.scripts.append(script)
        return script

    def kit(self, command: str, program: Program, *args: str) -> list[str]:
        return [sys.executable, str(ln.KIT), *command.split(), "--program", str(program.dir), *args]

    def ended(self, name: str) -> tuple[int, list[str]] | None:
        """The exit and output of a finished child called `name`; None while it runs or was never started."""
        script = next((s for s in self.scripts if s.name == name), None)
        if script is None:
            return None
        rc = script.done()
        if rc is None:
            return None
        self.scripts.remove(script)
        return rc, script.output()

    def running(self, name: str) -> bool:
        return any(s.name == name for s in self.scripts)

    # -- workers --

    def no_workers_now(self) -> bool:
        if self.held():
            return True
        if self.program.state.exists():
            usage = st.load(self.program).usage_reset_at
            if usage and dt.datetime.fromisoformat(usage) > clock.now():
                return True
        until = self.memo.get("limit_until")
        return bool(until and dt.datetime.fromisoformat(until) > clock.now())

    def start_worker(self, name: str, role: str, prompt_file: str, values: dict, cwd: Path,
                     env: dict | None = None, side: bool = False) -> bool:
        """Start one conveyor worker (plan review, planner fix, grounding, later handoff, audit stages). A `side`
        worker (an audit reader) runs beside others and is collected with `side_result`."""
        if self.worker and not side:
            return False
        self.hold_gate(f"the {role} worker {name}")
        if self.no_workers_now():
            return False
        path = prompt_dir(self.settings) / prompt_file
        try:
            prompt = render(path, {**project_values(self.profile), **values})
        except (PromptError, OSError) as exc:
            self.wait(f"the {role} prompt cannot be filled: {exc}", str(path))
            raise Stop(10) from exc
        n = self.memo.setdefault("workers", {}).get(name, 0) + 1
        self.memo["workers"][name] = n
        repo = str((self.profile.get("project") or {}).get("repo") or "")
        full_env = {"SHIP_REPO": repo, **(env or {})}
        handle = ln.launch(self.roles[role], prompt, cwd, self.program, f"chain-{name}-{n}", self.settings,
                           extra_env=full_env, label=name)
        if handle is None:
            return False
        if side:
            self.side[name] = handle
        else:
            self.worker = (name, handle)
            self.owner = self.current
        self.buf.append(f"START {role} {name} pid {handle.pid}")
        return True

    def side_result(self, name: str) -> ln.Result | None:
        """A finished side worker's result (a usage limit is recorded and comes back as None)."""
        handle = self.side.get(name)
        got = handle.poll() if handle else None
        if got is None:
            return None
        del self.side[name]
        self.log([f"WORKER {name} ended: {got.kind} {got.line or got.note}".rstrip()])
        if got.kind == "limit":
            self.memo["limit_until"] = got.limit_reset
        return got

    def worker_result(self, name: str) -> ln.Result | None:
        if not self.worker or self.worker[0] != name:
            return None
        got = self.worker[1].poll()
        if got is None:
            return None
        handle = self.worker[1]
        self.worker = None
        self.log([f"WORKER {name} ended: {got.kind} {got.line or got.note}".rstrip()])
        if got.kind == "limit":
            self.memo["limit_until"] = got.limit_reset
            return None
        if got.kind == "ok" and got.contract == "WAITS":
            self.wait(f"the {name} worker needs you", got.value)
            raise Stop(10)
        if not (got.kind == "ok" and got.contract in ("DONE", "READY")):
            if self.memo["workers"].get(name, 0) >= self.settings.max_restarts:
                self.wait(f"the {name} worker failed {self.memo['workers'][name]} times ({got.kind})", str(handle.stdout))
                raise Stop(10)
            return None
        return got

    # -- the loop --

    def tick(self) -> list[str]:
        self.buf = []
        try:
            self.buf += self._tick()
        except Stop as stop:
            self.exit = stop.code
        except Held as held:
            self.buf.append(f"HOLD: {held} did not start")
        lines = self.buf
        self.save()
        if self.lock:
            self.lock.refresh(self.children())
        self.log(lines)
        return lines

    def _tick(self) -> list[str]:
        lines: list[str] = []
        if self.program.state.exists():
            from ship import power_watch

            line = power_watch.step(self.program, self.settings, power_watch.on_mains(), time.time(),
                                    lambda: power_watch.probe_network(self.program, self.settings))
            if line != "MAINS":
                lines.append(f"POWER {line}")
        if self.held() and not self.busy():  # D-L25: the one guard before any activity
            return lines + ["HOLD: nothing new starts and nothing runs"]
        p = phase.read(self.program, self.settings)
        nxt, why = p["next"], p.get("why", "")
        if nxt != self.last_next:
            self.buf.append(f"NEXT {nxt}: {why}")
            if p.get("status") != "abandoned" and not (nxt == "audit" and p.get("stage") in phase.AUDIT_STAGES):
                phase.set_phase(self.program, nxt, "running", "conveyor")  # an audit keeps its stage there
            built = self.last_next == "build"
            self.last_next = nxt
            if built:
                self.finished("build")  # the build's done-file, the stop note, is written
        if self.worker and self.owner:  # a worker's result goes to the activity that started it, whatever phase says now
            handler, started_p = self.owner
            return lines + handler(started_p)
        merging = next((sc for sc in self.scripts if sc.name.startswith("merge-")), None)
        if merging is not None:  # MERGED in the note moves phase on; the merge's own exit is still read here
            return lines + self.merge({**p, "next": "merge", "stop": merging.name[len("merge-"):]})
        if self.checkpoint is not None:  # a verdict file alone moves phase on; the review must judge it first
            return lines + self.review_checkpoint({"stop": self.cp_key[0], "round": str(self.cp_key[1])})
        unjudged = self.unjudged(p)
        if unjudged:
            return lines + self.review_checkpoint(unjudged)
        if self.stop_after_reached():
            lines.append(f"STOP-AFTER {self.stop_after_reached()} merged; the conveyor stops here")
            phase.set_phase(self.program, nxt, "waits", "conveyor")
            (self.program.dir / "STOP-AFTER").unlink(missing_ok=True)
            raise Stop(0)
        handler = {"review": self.review, "planner-fix": self.planner_fix, "go": self.go, "arm": self.arm_self,
                   "build": self.build, "checkpoint-review": self.review_checkpoint, "merge": self.merge,
                   "docs": self.docs, "later-handoff": self.later_handoff, "audit": self.audit,
                   "sweep-handoff": self.sweep_handoff, "done": self.finish}.get(nxt)
        if handler is None:  # intake, plan, waits: nothing moves without him
            self.wait_or_note(p)
            raise Stop(10)
        if self.program.state.exists() and not self.memo.get("armed", {}).get(str(self.program.dir)) \
                and nxt not in ("done",) and p.get("kind") != "fix":
            self.current = (self.arm_self, p)
            return lines + self.arm(self.program)  # state.json exists, but the arm steps did not all finish
        self.current = (handler, p)
        return lines + handler(p)

    def wait_or_note(self, p: dict) -> None:
        if p.get("status") == "waits-on-him" or p.get("waits"):
            return
        self.wait(f"{self.program.dir.name} is at `{p['next']}` ({p.get('why', '')}); the conveyor cannot go on "
                  "without you", str(self.program.dir))

    def stop_after_reached(self) -> str:
        path = self.program.dir / "STOP-AFTER"
        if not path.exists() or not self.program.state.exists():
            return ""
        stop = path.read_text("utf-8").strip()
        return stop if stop and stop in st.load(self.program).merged else ""

    # -- review and planner-fix --

    def checks(self) -> list[tuple[str, list[str]]]:
        home = ln.factory_home(self.settings) / "skills" / "factory-core" / "scripts"
        try:
            kind = prog.load(self.program).kind
        except prog.ProgramError:
            kind = "feature"
        kind = kind if kind in ("feature", "wire", "audit") else "feature"
        project = (self.profile.get("project") or {}).get("name") or "qmx"
        return [("check_chain", [sys.executable, str(home / "check_chain.py"), str(self.program.dir), "--stage",
                                 "handoff", "--kind", kind, "--project", project, "--ship", str(ln.KIT)]),
                ("check_plan", [sys.executable, str(home / "check_plan.py"), str(self.program.dir), str(ln.KIT)])]

    def run_checks(self, tag: str) -> list[str] | None:
        """Both plan checks as children: None while they run, else their FAIL lines."""
        book = self.memo.setdefault("checks", {})
        if book.get(tag) is not None:
            return book[tag]
        for name, argv in self.checks():
            key = f"{tag}-{name}"
            if not self.running(key) and key not in book.get("done", {}):
                if not Path(argv[1]).exists():
                    self.wait(f"the plan check {Path(argv[1]).name} is not in the factory home", argv[1])
                    raise Stop(10)
                self.child(key, argv)
        for name, _ in self.checks():
            key = f"{tag}-{name}"
            got = self.ended(key)
            if got:
                rc, out = got
                fails = [x for x in out if x.startswith("FAIL")] or ([f"FAIL {name} exit {rc}"] if rc else [])
                book.setdefault("done", {})[key] = fails
        done = book.get("done", {})
        if all(f"{tag}-{name}" in done for name, _ in self.checks()):
            book[tag] = [x for name, _ in self.checks() for x in done.pop(f"{tag}-{name}")]
            return book[tag]
        return None

    def review(self, p: dict) -> list[str]:
        folder = self.program.dir / "plan-review"
        rounds = len(list(folder.glob("REVIEW.round-*.md")))
        tag = f"review-{rounds + 1}"
        fails = self.run_checks(tag)
        if fails is None:
            return []
        if fails:
            folder.mkdir(parents=True, exist_ok=True)
            (folder / "FIXES.md").write_text("# Fixes from the plan checks\n\n" + "".join(f"- {x}\n" for x in fails),
                                             "utf-8", newline="\n")
            (folder / "REVIEW.md").write_text(f"The plan checks failed; see FIXES.md.\n\nRESULT: FIXES\n"
                                              f"END plan-review {self.parent_tip()}\n", "utf-8", newline="\n")
            self.finished("review")
            return [f"CHECKS failed ({len(fails)}): planner-fix"]
        got = self.worker_result("plan-review")
        if got is None:
            if not self.worker:
                self.start_worker("plan-review", "plan-review", "PLAN-REVIEW.md", self.values(), self.program.dir)
            return []
        result = phase.review_result(folder / "REVIEW.md")
        if result == "QUESTIONS":
            asked = folder / "QUESTIONS.md"
            text = asked.read_text("utf-8") if asked.exists() else ""
            rows = [x.strip() for x in text.splitlines() if x.strip().startswith("- [ ]")] or \
                   [f"- [ ] {x.strip(' -*')}" for x in text.splitlines() if x.strip(" -*#")]
            old = self.program.waiting.read_text("utf-8") if self.program.waiting.exists() else ""
            self.program.waiting.write_text(old + "".join(f"{r}\n" for r in rows if r not in old), "utf-8",
                                            newline="\n")
            self.finished("review")
            raise Stop(10)
        if not result:
            return [f"REVIEW the plan-review worker wrote no RESULT line; again ({self.memo['workers']['plan-review']})"]
        self.finished("review")
        return [f"REVIEW result {result}"]

    def planner_fix(self, p: dict) -> list[str]:
        folder = self.program.dir / "plan-review"
        if "planner_fix_his" not in self.memo:  # decided once per round, before the worker empties FIXES.md
            self.memo["planner_fix_his"] = his_fixes(folder / "FIXES.md", self.program, self.settings,
                                                     str(self.project().get("name") or "qmx"))
        his = self.memo["planner_fix_his"]
        if not his and (folder / "FIXES.applied.md").exists() and self.memo.get("planner_fix_done"):
            self.memo.pop("planner_fix_his", None)
            self.wait("the plan review asked for fixes a second time", str(folder / "REVIEW.md"))
            raise Stop(10)
        if not self.memo.get("planner_fix_worker_done"):
            got = self.worker_result("planner-fix")
            if got is None:
                if not self.worker:
                    self.start_worker("planner-fix", "planner-fix", "PLANNER-FIX.md", self.values(), self.program.dir)
                return []
            self.memo["planner_fix_worker_done"] = True
        fails = self.run_checks(f"fix-{len(list(folder.glob('REVIEW.round-*.md'))) + 1}")
        if fails is None:
            return []
        if fails:
            self.wait("the plan checks still fail after the planner's fixes: " + "; ".join(fails[:3]),
                      str(self.program.dir))
            raise Stop(10)
        n = len(list(folder.glob("REVIEW.round-*.md"))) + 1
        if (folder / "REVIEW.md").exists():
            (folder / "REVIEW.md").replace(folder / f"REVIEW.round-{n}.md")
        # his answers' round uses up nothing: the next mechanical FIXES gets its one round again
        self.memo["planner_fix_done"] = not his
        self.memo["planner_fix_worker_done"] = False
        self.memo.pop("planner_fix_his", None)
        self.finished("planner-fix")
        return [f"PLANNER-FIX applied{' (his answers)' if his else ''}; the plan review runs once more"]

    def parent_tip(self) -> str:
        try:
            return prog.load(self.program).parent_tip or ""
        except prog.ProgramError:
            return ""

    def values(self, **more: str) -> dict:
        return {"PROGRAM": str(self.program.dir), "SHIP": str(ln.KIT), "PARENT_TIP": self.parent_tip(), **more}

    # -- go --

    def go(self, p: dict) -> list[str]:
        if "conveyor writes go" not in p.get("why", ""):
            raise Stop(10)
        self.hold_gate("go")
        index = prog.load(self.program)
        last = index.last_gate_before_go()
        source = str((index.gate(last) or {}).get("source") or f"gates.{last}")
        line = prog.set_gate(self.program, "go", by="him", source=source, advance=True)
        self.finished("go")
        return [f"GO {line}"]

    # -- arm --

    def arm_self(self, p: dict) -> list[str]:
        return self.arm(self.program)

    def project(self) -> dict:
        return self.profile.get("project") or {}

    def arm(self, folder: Program) -> list[str]:
        """init, preflight, facts at parent_tip and at the target tip, grounding for failing facts."""
        key = str(folder.dir)
        book = self.memo.setdefault("arm", {}).setdefault(key, {})
        index = prog.load(folder)
        gates = prog.gates_problem(folder, index)
        if gates:  # D-L22: only gates `ship gate` wrote arm a program
            self.wait(f"{folder.dir.name} cannot be armed: {gates}", str(folder.project_file))
            raise Stop(10)
        if index.kind == "fix" and index.parent:
            from ship.review import settings_differ

            differ = settings_differ(Program(folder.dir.parent / index.parent), folder)
            if differ:  # D-L22: the kit copies them from the parent; any other copy is refused
                self.wait(f"{folder.dir.name} cannot be armed: its {', '.join(differ)} differ from its parent's",
                          str(folder.dir))
                raise Stop(10)
        proj = self.project()
        repo = Path(proj.get("repo") or "")
        remote = str(proj.get("remote") or self.settings.remote)
        lines: list[str] = []
        if not folder.state.exists():
            self.hold_gate(f"arming {folder.dir.name}")
            if not index.build_branch or not repo.is_dir():
                self.wait(f"{folder.dir.name} cannot be armed: build_branch {index.build_branch!r}, repo {repo}")
                raise Stop(10)
            try:
                if not remote_sha(repo, remote, index.build_branch, self.settings.git_timeout_s):
                    self.hold_gate(f"the push of {index.build_branch}")
                    git(repo, "push", "-q", remote, f"{index.parent_tip}:refs/heads/{index.build_branch}",
                        timeout=self.settings.git_timeout_s)
                    lines.append(f"BRANCH {index.build_branch} made at {str(index.parent_tip)[:10]}")
            except GitError as exc:
                return lines + [f"ARM {folder.dir.name}: remote unreachable ({exc}); again next tick"]
            from ship.plan import init_state

            lines.append(init_state(folder.dir, repo, index.build_branch,
                                    Path(proj.get("worktree_root") or repo.parent),
                                    remote))
        if self.settings.arm_preflight and not book.get("preflight"):
            got = self.ended("preflight")
            if got is None:
                if not self.running("preflight"):
                    self.child("preflight", self.kit("preflight", folder))
                return lines
            rc, out = got
            if rc != 0:
                for line in [x for x in out if x.startswith("FAIL")] or out[-5:]:
                    self.wait(f"{folder.dir.name} preflight: {line}", str(folder.dir / "preflight"))
                raise Stop(10)
            book["preflight"] = True
        tips = [t for t in dict.fromkeys([index.parent_tip or "", self.target_tip(repo, remote)]) if t]
        for tip in tips:
            if tip in book.get("facts", {}):
                continue
            got = self.ended(f"facts-{tip[:8]}")
            if got is None:
                if not self.running(f"facts-{tip[:8]}"):
                    self.child(f"facts-{tip[:8]}", self.kit("facts", folder, "--tip", tip))
                return lines
            book.setdefault("facts", {})[tip] = [x for x in got[1] if x.startswith("FAIL")]
        failing = sorted({x.split()[1] for fails in book.get("facts", {}).values() for x in fails if len(x.split()) > 1})
        if failing and not book.get("grounded"):
            got = self.worker_result(f"grounding-{folder.dir.name}")
            if got is None:
                if not self.worker:
                    if not (prompt_dir(self.settings) / "GROUNDING.md").exists():
                        book["grounded"] = True  # no grounding prompt: dispatch parks what still fails
                    else:
                        self.start_worker(f"grounding-{folder.dir.name}", "grounding", "GROUNDING.md",
                                          self.values(SLICES=", ".join(failing), TIP=tips[-1],
                                                      FACTS=str(folder.checks_root / "_facts")), folder.dir)
                return lines + [f"FACTS fail for {failing}"]
            book["grounded"] = True
        self.memo.setdefault("armed", {})[key] = True
        self.finished("arm")
        return lines + [f"ARMED {folder.dir.name}"]

    def target_tip(self, repo: Path, remote: str) -> str:
        from ship.project_profile import target_branch

        target = target_branch(self.program.dir, self.settings)
        try:
            return remote_sha(repo, remote, target, self.settings.git_timeout_s) or ""
        except GitError:
            return ""

    # -- build and the checkpoint --

    def build(self, p: dict) -> list[str]:
        folder = Program(Path(p["build_folder"])) if p.get("build_folder") else self.program
        if folder.dir != self.program.dir and not self.memo.get("armed", {}).get(str(folder.dir)):
            return self.arm(folder)
        return self.tick_build(folder)

    def tick_build(self, folder: Program, count: bool = True) -> list[str]:
        key = str(folder.dir)
        build = self.builds.get(key)
        lines: list[str] = []
        if build is None:
            build = Build(folder, load_settings(folder.dir), None)
            self.builds[key] = build
            lines += build.start()
            if build.exit is not None:
                raise Stop(10)
        lines += [f"[{folder.dir.name}] {x}" for x in build.tick(clock.now())]
        if build.exit is not None:
            code = build.exit
            build.stop_children()
            del self.builds[key]
            raise Stop(10 if code in (1, 10) else code)
        if build.done() and count and folder.dir != self.program.dir:
            del self.builds[key]  # a fix program's build is over once its stop note is written
        return lines

    def prebuild(self) -> list[str]:
        """While a checkpoint is in review or merging, the program's own Build keeps pre-building."""
        if not self.program.state.exists():
            return []
        state = st.load(self.program)
        early = [s for s in state.slices.values() if s.status not in (st.Status.LANDED, st.Status.PARKED,
                                                                     st.Status.BLOCKED_BY) and state.ahead(s.id) == 1]
        if not early and str(self.program.dir) not in self.builds:
            return []
        try:
            return self.tick_build(self.program, count=False)
        except Stop:
            return ["PREBUILD stopped; the open checkpoint goes on"]

    def review_checkpoint(self, p: dict) -> list[str]:
        stop, rnd = p["stop"], int(p.get("round") or 1)
        lines = self.prebuild()
        if self.cp_key != (stop, rnd):
            if self.checkpoint:
                self.checkpoint.stop_children()
            self.checkpoint = Checkpoint(self.program, stop, self.settings, rnd)
            self.cp_key = (stop, rnd)
        lines += self.checkpoint.tick()  # under HOLD it reads what runs and starts nothing (review.Checkpoint)
        code = self.checkpoint.result()
        if code is None:
            return lines
        self.checkpoint, self.cp_key = None, None
        self.finished("checkpoint")
        if code == 10:
            raise Stop(10)
        return lines + [f"CHECKPOINT {stop} round {rnd}: {code}"]

    def unjudged(self, p: dict) -> dict | None:
        """A stop whose review was started but has no result (the conveyor died after the verdict file)."""
        stop = p.get("stop")
        if p.get("next") not in ("merge", "docs") or not stop:
            return None
        run = self.program.review_run(stop)
        try:
            memo = json.loads(run.read_text("utf-8"))
        except (OSError, ValueError):
            return None
        if "result" in memo or not memo.get("tip"):
            return None
        return {"stop": stop, "round": str(memo.get("round") or 1)}

    # -- merge --

    def merge(self, p: dict) -> list[str]:
        stop = p["stop"]
        lines = self.prebuild()
        got = self.ended(f"merge-{stop}")
        if got is None:
            if not self.running(f"merge-{stop}"):
                self.child(f"merge-{stop}", self.kit("merge", self.program, stop))
            return lines
        rc, out = got
        lines += [f"MERGE {x}" for x in out[-8:]]
        if rc == 0:
            self.finished("merge")
            return lines
        if rc in (3, 11):
            return lines + [f"MERGE {stop} exit {rc}: again next tick"]
        if rc == 2 and phase.read(self.program, self.settings).get("next") in ("build", "checkpoint-review"):
            return lines + [f"MERGE {stop}: a fix program does the merge"]  # phase's rule for a merge-written fix
        raise Stop(10)

    # -- docs, later handoff, sweep handoff, audit --

    def docs(self, p: dict) -> list[str]:
        stop = p["stop"]
        self.hold_gate(f"the docs step of stop {stop}")
        record = self.program.dir / "docs" / f"{stop}.json"
        try:
            from ship import docs as docs_step  # U36
        except ImportError:
            docs_step = None
        if docs_step is not None and hasattr(docs_step, "docs"):
            from ship import locks

            lock = locks.merge_lock(str(self.project().get("name") or "qmx"), self.settings)
            if not lock.ask(self.program.dir.name, f"docs-{stop}"):  # D-L22: a docs PR merges in turn too
                return [f"DOCS {stop}: another program is merging; again next tick"]
            try:
                docs_step.docs(self.program, stop, self.settings)
            except Exception as exc:  # noqa: BLE001 - a docs failure never blocks code (row 40)
                self.log([f"DOCS {stop} failed: {exc!r}"])
            finally:
                lock.release()
        if not record.exists():
            record.parent.mkdir(parents=True, exist_ok=True)
            record.write_text(json.dumps({"stop": stop, "skipped": "the docs step (U36) is not built yet",
                                          "at": clock.now().isoformat(timespec="seconds")}) + "\n", "utf-8",
                              newline="\n")
        self.finished("docs")
        return [f"DOCS {stop}: {record.name}"]

    def later_handoff(self, p: dict) -> list[str]:
        stop = p["stop"]
        if not (prompt_dir(self.settings) / "LATER-HANDOFF.md").exists():
            self.wait(f"stop {stop} is deferred and the later-handoff prompt is not there yet")
            raise Stop(10)
        got = self.worker_result(f"later-handoff-{stop}")
        if got is None:
            if not self.worker:
                self.start_worker(f"later-handoff-{stop}", "later-handoff", "LATER-HANDOFF.md",
                                  self.values(STOP=stop), self.program.dir)
            return []
        self.finished("later-handoff")
        return [f"LATER-HANDOFF {stop} done; SKIP the sweep review (U21)"]

    def sweep_handoff(self, p: dict) -> list[str]:
        if not (prompt_dir(self.settings) / "SWEEP-HANDOFF.md").exists():
            self.wait("the sweep is not handed off and the sweep-handoff prompt is not there yet")
            raise Stop(10)
        got = self.worker_result("sweep-handoff")
        if got is None:
            if not self.worker:
                self.start_worker("sweep-handoff", "sweep-handoff", "SWEEP-HANDOFF.md", self.values(), self.program.dir)
            return []
        self.finished("sweep-handoff")
        return ["SWEEP-HANDOFF done"]

    def audit(self, p: dict) -> list[str]:
        stage = p.get("stage") if p.get("stage") in phase.AUDIT_STAGES else "census"
        index = prog.load(self.program)
        if stage == "census":
            script = ln.factory_home(self.settings) / "skills" / "audit-area" / "scripts" / "census.py"
            if not script.exists():
                self.wait(f"SKIP audit census: {script} is not there")
                raise Stop(10)
            got = self.ended("census")
            if got is None:
                if not self.running("census"):
                    proj = self.project()
                    tip = self.target_tip(Path(proj.get("repo") or "."), str(proj.get("remote") or "origin"))
                    self.child("census", [sys.executable, str(script), *map(str, index.area or ["."]), "--repo",
                                          str(proj.get("repo") or ""), "--tip", tip or "HEAD", "--out",
                                          str(self.program.dir / "CENSUS.md"), "--project",
                                          str(proj.get("name") or "qmx")])
                return []
            if got[0] != 0:
                self.wait("the audit census failed: " + "; ".join(got[1][-3:]))
                raise Stop(10)
            phase.set_phase(self.program, "intent", "running", "conveyor")
            self.finished("audit")
            return ["AUDIT census done"]
        if stage in ("intent-check", "verdicts"):
            gate = "intent" if stage == "intent-check" else "verdicts"
            if index.gate(gate) is None:
                raise Stop(10)
            phase.set_phase(self.program, "quality" if gate == "intent" else "audit-handoff", "running", "conveyor")
            return [f"AUDIT gate {gate} is set"]
        role, prompt, after = AUDIT_WORKERS.get(stage, ("", "", ""))
        if not role or not (prompt_dir(self.settings) / prompt).exists():
            self.wait(f"SKIP audit stage {stage}: its worker prompt is not there yet (U26)")
            raise Stop(10)
        if stage == "quality":
            return self.audit_quality(index)
        if stage == "judgement":
            return self.audit_judgement()
        if stage == "audit-handoff":
            return self.audit_handoff()
        got = self.worker_result("audit-intent")
        if got is None:
            if not self.worker:
                self.start_worker("audit-intent", "audit-intent", "AUDIT-INTENT.md", self.values(STAGE=stage),
                                  self.program.dir)
            return []
        intent = self.program.dir / "INTENT.md"
        open_ = [x for x in (intent.read_text("utf-8").splitlines() if intent.exists() else [])
                 if x.strip().startswith("- [ ]")]
        if open_:
            old = self.program.waiting.read_text("utf-8") if self.program.waiting.exists() else ""
            self.program.waiting.write_text(old + "".join(f"{x.strip()}\n" for x in open_ if x.strip() not in old),
                                            "utf-8", newline="\n")
        phase.set_phase(self.program, "quality", "running", "conveyor")  # reading does not wait for him
        self.finished("audit")
        return [f"AUDIT {stage} done"]

    # -- the audit's checkout, probes and readers --

    def census(self) -> tuple[str, list[tuple[str, str]]]:
        """(the census tip, [(part, its folder)]) from CENSUS.md's `Tip:` line and `## Parts` list."""
        path = self.program.dir / "CENSUS.md"
        text = path.read_text("utf-8") if path.exists() else ""
        tip = CENSUS_TIP.search(text)
        section = text.split("## Parts", 1)[1].split("\n## ", 1)[0] if "## Parts" in text else ""
        return (tip.group(1) if tip else ""), CENSUS_PART.findall(section)

    def audit_packages(self, tip: str) -> list:
        """The package roots the probe runs over: checks.toml's packages in or around the area, else every folder
        holding a pyproject.toml in the area (or the nearest one above it), set up with `uv sync --frozen`."""
        from ship.suite import Package, load_packages

        index = prog.load(self.program)
        area = [str(a).replace("\\", "/").strip("/") or "." for a in index.area] or ["."]

        def near(root: str) -> bool:
            return any(a == "." or root == a or root.startswith(a + "/") or a.startswith(root + "/") for a in area)

        listed = [p for p in load_packages(self.program) if p.root != "." and near(p.root)]
        if listed:
            return listed
        repo, t = Path(str(self.project().get("repo") or "")), self.settings.git_timeout_s
        names = git(repo, "ls-tree", "-r", "--name-only", tip, "--", *[a for a in area if a != "."], timeout=t)
        roots = {str(Path(n).parent).replace("\\", "/") for n in names.splitlines() if Path(n).name == "pyproject.toml"}
        for a in area:
            parts = a.split("/") if a != "." else []
            for i in range(len(parts), 0, -1):
                up = "/".join(parts[:i])
                if git(repo, "cat-file", "-t", f"{tip}:{up}/pyproject.toml", timeout=t, check=False).strip() == "blob":
                    roots.add(up)
                    break
        return [Package(r, setup=("uv", "sync", "--frozen")) for r in sorted(roots - {"."})]

    def audit_checkout(self, tip: str) -> Path:
        """The frozen checkout of the census tip the probes, readers and hand-off use, its packages set up."""
        from ship.worktree import Setup, checkout_copy

        proj = self.project()
        repo = Path(str(proj.get("repo") or ""))
        path = Path(str(proj.get("worktree_root") or repo.parent)) / f"audit-{self.program.dir.name}"
        if self.audit_copy is None:
            self.hold_gate("the audit checkout")
            packages = tuple(p for p in self.audit_packages(tip) if p.setup)
            setup = Setup(packages, self.program.runs, self.program.dir / "probe" / "setup")
            checkout_copy(repo, path, tip, self.settings, setup)
            self.buf += [f"AUDIT checkout {path} at {tip[:10]}"] + [f"AUDIT {x}" for x in setup.lines]
            self.audit_copy = path
        return path

    def probe_argv(self, copy: Path, package) -> list[str]:
        script = ln.factory_home(self.settings) / "skills" / "audit-area" / "scripts" / "probe_tests.py"
        root = copy / package.root
        python = sys.executable
        for folder in [root, *root.parents]:
            venv = folder / ".venv" / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
            if venv.is_file():
                python = str(venv)
                break
            if folder == copy:
                break
        src = f"{package.root}/src" if (root / "src").is_dir() else package.root
        name = Path(package.root).name
        return [sys.executable, str(script), package.root, "--checkout", str(copy), "--out",
                str(self.program.dir / "probe" / f"{name}.tsv"), "--python", python, "--src", src, "--ship", str(ln.KIT),
                "--project", str(self.project().get("name") or "qmx")]

    def audit_quality(self, index) -> list[str]:
        book = self.memo.setdefault("audit", {})
        tip, parts = self.census()
        if not tip or not parts:
            self.wait("the audit cannot read: CENSUS.md has no `Tip:` line or no `## Parts` list",
                      str(self.program.dir / "CENSUS.md"))
            raise Stop(10)
        odd = [part for part, _ in parts if not PLAIN_PART.fullmatch(part)]
        if odd:  # SHIP_PART names the files a reader may write: a plain name or nothing
            self.wait(f"the audit parts {odd} are not plain names ([A-Za-z0-9_-]+)", str(self.program.dir / "CENSUS.md"))
            raise Stop(10)
        copy = self.audit_checkout(tip)
        lines: list[str] = []
        probes = book.setdefault("probes", {})
        for package in self.audit_packages(tip):
            if package.root in probes:
                continue
            name = f"probe-{package.label}"
            script = next((sc for sc in self.scripts if sc.name == name), None)
            if script is not None and script.done() is None and time.monotonic() - script.began > \
                    self.settings.nightly_timeout_s:
                kill_tree(script.proc.pid)
                self.scripts.remove(script)
                self.wait(f"the audit probe of {package.root} ran past {self.settings.nightly_timeout_s}s and was "
                          "stopped; the readers cannot go without it", str(script.log))
                raise Stop(10)
            got = self.ended(name)
            if got is None:
                if not self.running(name):
                    if not Path(self.probe_argv(copy, package)[1]).exists():
                        self.wait(f"the audit cannot probe {package.root}: {self.probe_argv(copy, package)[1]} is not "
                                  "there")
                        raise Stop(10)
                    self.child(name, self.probe_argv(copy, package))
                    lines.append(f"PROBE {package.root} started")
                return lines
            if got[0] != 0:  # D-L25: a probe that does not exit 0 is WAITS, never a reader without it
                self.wait(f"the audit probe of {package.root} exited {got[0]}: " + "; ".join(got[1][-3:]),
                          str(self.program.dir / "probe"))
                raise Stop(10)
            probes[package.root] = got[0]
            lines.append(f"PROBE {package.root} exit 0")
        readers = book.setdefault("readers", {})
        waiting = False
        for part, folder in parts:
            rec = readers.setdefault(part, {"attempts": 0})
            notes = self.program.dir / "readers" / f"{part}.md"
            name = f"audit-quality-{part}"
            if name in self.side:
                got = self.side_result(name)
                if got is None:
                    waiting = True
                    continue
                if got.kind == "limit":  # D-L25: a usage limit is a restart, never one of its runs
                    rec["attempts"] = max(0, rec["attempts"] - 1)
                    waiting = True
                    continue
                if got.kind == "ok" and got.contract == "WAITS" and not _ends_done(notes):
                    self.wait(f"the audit reader of part {part} needs you", got.value or str(notes))
                    raise Stop(10)
            if rec.get("done") or _ends_done(notes):
                rec["done"] = True
                continue
            if name not in self.side and rec["attempts"] >= self.settings.max_restarts:
                self.wait(f"the audit reader of part {part} did not finish in {rec['attempts']} runs", str(notes))
                raise Stop(10)
            waiting = True
            if self.start_worker(name, "audit-reader", "AUDIT-READER.md",
                                 self.values(STAGE="quality", PART=part, CHECKOUT=str(copy)), copy,
                                 env={"SHIP_PART": part}, side=True):
                rec["attempts"] += 1
                lines.append(f"READER {part} ({folder}) run {rec['attempts']}")
        if waiting:
            return lines
        script = ln.factory_home(self.settings) / "skills" / "audit-area" / "scripts" / "collect_findings.py"
        got = self.ended("collect-findings")
        if got is None:
            if not self.running("collect-findings"):
                self.child("collect-findings", [sys.executable, str(script), str(self.program.dir)])
            return lines
        if got[0] != 0:
            self.wait("collect_findings.py failed: " + "; ".join(got[1][-3:]), str(self.program.dir / "FINDINGS.tsv"))
            raise Stop(10)
        book.pop("readers", None)
        book.pop("probes", None)
        phase.set_phase(self.program, "judgement", "running", "conveyor")
        self.finished("audit")
        return lines + [f"AUDIT quality done: {len(parts)} parts read, FINDINGS.tsv collected"]

    def audit_judgement(self) -> list[str]:
        """The judge (Fable), then the screen (Opus) on what Fable decided, then `apply_screen.py` makes its moves."""
        book = self.memo.setdefault("audit", {})
        if not book.get("judged"):
            got = self.worker_result("audit-judgement")
            if got is None:
                if not self.worker:
                    self.start_worker("audit-judgement", "audit-judge", "AUDIT-JUDGE.md", self.values(STAGE="judgement"),
                                      self.program.dir)
                return []
            book["judged"] = True
            return ["AUDIT judgement done; the screen starts"]
        if not book.get("screened"):
            if not (prompt_dir(self.settings) / "AUDIT-SCREEN.md").exists():
                self.wait("SKIP the audit screen: its worker prompt is not there yet")
                raise Stop(10)
            got = self.worker_result("audit-screen")
            if got is None:
                if not self.worker:
                    self.start_worker("audit-screen", "audit-screen", "AUDIT-SCREEN.md", self.values(STAGE="judgement"),
                                      self.program.dir)
                return []
            book["screened"] = True
            return ["AUDIT screen done; apply_screen.py makes its moves"]
        script = ln.factory_home(self.settings) / "skills" / "audit-area" / "scripts" / "apply_screen.py"
        got = self.ended("apply-screen")
        if got is None:
            if not self.running("apply-screen"):
                if not script.exists():
                    self.wait(f"the audit screen cannot be applied: no {script}")
                    raise Stop(10)
                self.child("apply-screen", [sys.executable, str(script), str(self.program.dir)])
            return []
        if got[0] != 0:
            self.wait("apply_screen.py failed: " + "; ".join(got[1][-3:]), str(self.program.dir / "AUDIT-SCREEN.md"))
            raise Stop(10)
        book.pop("judged", None)
        book.pop("screened", None)
        phase.set_phase(self.program, "verdicts", "running", "conveyor")
        self.finished("audit")
        return ["AUDIT judgement, screen and its moves done"]

    def audit_handoff(self) -> list[str]:
        tip, _ = self.census()
        if not tip:
            self.wait("the audit hand-off needs CENSUS.md's `Tip:` line", str(self.program.dir / "CENSUS.md"))
            raise Stop(10)
        copy = self.audit_checkout(tip)
        got = self.worker_result("audit-audit-handoff")
        if got is None:
            if not self.worker:
                self.start_worker("audit-audit-handoff", "sweep-handoff", "AUDIT-HANDOFF.md",
                                  self.values(STAGE="audit-handoff", CHECKOUT=str(copy)), self.program.dir)
            return []
        from ship.worktree import drop_copy

        drop_copy(Path(str(self.project().get("repo") or "")), copy, self.settings)
        self.audit_copy = None
        self.finished("audit")
        return ["AUDIT audit-handoff done; the audit checkout is dropped"]

    # -- the end --

    def finish(self, p: dict) -> list[str]:
        if p.get("status") == "abandoned":
            raise Stop(0)
        self.hold_gate("the finish (report, teardown, claims)")
        from ship.armed import teardown
        from ship.run_report import write_report

        lines = []
        if self.program.state.exists():
            ok, path = write_report(self.program, self.settings)
            lines.append(f"REPORT {path} ({'ok' if ok else 'counts do not add up'})")
            _, out = teardown(self.program, self.settings)
            lines += out
            try:
                from ship import claims

                released = claims.for_program(self.program, self.settings).release(self.program.dir.name)
                lines.append(f"CLAIMS released {released}")
            except ImportError:
                pass
            with open(self.program.report, "a", encoding="utf-8", newline="\n") as out_:
                out_.write(f"\n## The conveyor's last word\n\nEvery stop is merged and its docs step ran "
                           f"({clock.now().isoformat(timespec='seconds')}).\n")
        phase.set_phase(self.program, "done", "done", "conveyor")
        raise Stop(0)


def _ends_done(path: Path) -> bool:
    try:
        lines = [x.strip() for x in path.read_text("utf-8", errors="replace").splitlines() if x.strip()]
    except OSError:
        return False
    return bool(lines) and lines[-1] == "DONE"


def conveyor(program: Program, settings: Settings, poll_s: float | None = None) -> int:
    lock = ChainLock(program, "chain")
    if not lock.acquire():
        print(f"LOCKED chain.lock is held by pid {lock.read().get('pid')}")
        return 11
    belt = Conveyor(program, settings, lock)
    period = settings.chain_poll_s if poll_s is None else poll_s
    try:
        from ship.recover import recover

        if program.state.exists():
            for line in recover(program, settings):
                print(line, flush=True)
        refused = 0
        while True:
            try:
                ticked = belt.tick()
                refused = 0
            except PermissionError as exc:  # Windows: another process had a file open for an instant
                refused += 1
                if refused >= 10:
                    raise
                print(f"RETRY the tick: {exc!r}", flush=True)
                time.sleep(period)
                continue
            for line in ticked:
                print(line, flush=True)
            if belt.exit is not None:
                if belt.exit == 10:
                    phase.set_phase(program, phase.phase_json(program).get("phase") or "waits", "waits", "conveyor")
                return belt.exit
            time.sleep(period)
    except Exception as exc:  # noqa: BLE001 - an error the conveyor cannot route goes to him, never lost
        add_wait(program, f"the conveyor stopped on an error: {exc!r}", str(program.dir / "notes" / "chain.log"))
        print(f"ERROR {exc!r}", flush=True)
        phase.set_phase(program, phase.phase_json(program).get("phase") or "waits", "waits", "conveyor")
        return 1
    finally:
        belt.stop_children()
        lock.release()


# ---- follow, detach, resume-all, abandon ----------------------------------------------------------------


def follow(program: Program, settings: Settings, poll_s: float | None = None) -> int:
    """One line per change of next, status or the WAITS count; 0 done, 10 waits on him, 1 the conveyor died."""
    period = 20 if poll_s is None else poll_s
    last = None
    dead = 0
    while True:
        p = phase.read(program, settings)
        waits = sum(len(phase.UNANSWERED.findall(phase._read(path))) for path in (program.waiting, program.waits))
        now = (p.get("next"), p.get("status"), waits)
        if now != last:
            print(f"{clock.now().isoformat(timespec='seconds')} next: {now[0]} status: {now[1]} waits: {waits} "
                  f"({p.get('why', '')})", flush=True)
            last = now
        if p.get("status") in ("done", "abandoned") or p.get("next") == "done":
            return 0
        if p.get("status") == "waits-on-him":
            return 10
        recorded = phase.phase_json(program).get("status")
        alive, _ = phase.conveyor(program)
        if recorded == "waits" and not alive:  # the conveyor exited 10 with no WAITS line (D-L22)
            print(f"WAITS the conveyor stopped at {p.get('next')} and waits on him ({p.get('why', '')})", flush=True)
            return 10
        dead = dead + 1 if recorded == "running" and not alive else 0
        if dead >= 2:
            print("DEAD the conveyor is not running and phase.json says running", flush=True)
            return 1
        time.sleep(period)


def detach(argv: list[str], program_dir: Path) -> int:
    """Start the same command again as its own process, outliving this one; print its pid."""
    program_dir.mkdir(parents=True, exist_ok=True)
    log = open(program_dir / "chain.log", "a", encoding="utf-8", newline="\n")
    try:  # D-L22: no DETACHED_PROCESS (its children each open a visible console)
        proc = popen_detached([sys.executable, str(ln.KIT), *argv], stdin=subprocess.DEVNULL, stdout=log,
                              stderr=subprocess.STDOUT)
    finally:
        log.close()
    print(f"DETACHED pid {proc.pid} log {program_dir / 'chain.log'}")
    return 0


def resume_all(plans: Path, settings_of=load_settings) -> list[str]:
    """A conveyor for every program whose phase.json says running and whose chain.lock is dead."""
    from ship.recover import recover

    lines = []
    for folder in phase.all_programs(plans):
        program = Program(folder.resolve())
        if phase.phase_json(program).get("status") != "running":
            continue
        alive, words = phase.conveyor(program)
        if alive:
            lines.append(f"RUNNING {folder.name}: {words}")
            continue
        settings = settings_of(program.dir)
        if program.state.exists():
            try:
                recover(program, settings)
            except GitError as exc:
                lines.append(f"RECOVER {folder.name} unreachable ({exc}); the conveyor retries")
        import io
        from contextlib import redirect_stdout

        buf = io.StringIO()
        with redirect_stdout(buf):
            detach(["chain", "--program", str(program.dir)], program.dir)
        lines.append(f"STARTED {folder.name}: {buf.getvalue().strip()}")
    return lines


def abandon(program: Program, settings: Settings, why: str) -> list[str]:
    """Stop the conveyor and its children, recover, tear down, release the claims, and mark it abandoned."""
    from ship.armed import teardown
    from ship.proc import same_process
    from ship.recover import recover

    lines = []
    held = {}
    try:
        held = json.loads(program.chain_lock.read_text("utf-8"))
    except (OSError, ValueError):
        pass
    for row in [held, *held.get("children", [])]:
        pid = int(row.get("pid") or 0)
        if pid and pid != os.getpid() and (same_process(pid, row.get("created")) if row.get("created") is not None
                                           else pid_alive(pid)):
            kill_tree(pid)
            lines.append(f"KILLED {row.get('role') or 'conveyor'} {pid}")
    program.chain_lock.unlink(missing_ok=True)
    if program.state.exists():
        try:
            lines += recover(program, settings)
        except GitError as exc:
            lines.append(f"RECOVER unreachable ({exc}); leftovers stay in the worktrees")
        lines += teardown(program, settings)[1]
        try:
            from ship import claims

            lines.append(f"CLAIMS released {claims.for_program(program, settings).release(program.dir.name)}")
        except ImportError:
            pass
    today = clock.now().date().isoformat()
    if program.project_file.exists():
        text = program.project_file.read_text("utf-8")
        if re.search(r"^abandoned:", text, re.M):
            text = re.sub(r"^abandoned:.*$", f"abandoned: {today}", text, count=1, flags=re.M)
        else:
            text = text.rstrip("\n") + f"\nabandoned: {today}\n"
        program.project_file.write_text(text, "utf-8", newline="\n")
    notes = program.notes_dir / "ABANDONED.md"
    notes.parent.mkdir(parents=True, exist_ok=True)
    notes.write_text(f"# Abandoned {today}\n\n{why}\n", "utf-8", newline="\n")
    phase.set_phase(program, "done", "done", "abandon")
    try:
        from ship import backlog  # U33

        if hasattr(backlog, "add_parked"):
            lines += backlog.add_parked(program, settings)
    except ImportError:
        pass
    return lines + [f"ABANDONED {program.dir.name}: {why}"]
