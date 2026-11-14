"""ship review: the checkpoint review as a script (unit U09, FACTORY-DESIGN 2.7, 11.2, 11.8).

`Checkpoint(program, stop, settings, round)` is the conveyor's activity: `tick()` starts at most what
is due and never waits on a long command; `result()` is None until it ends with 0 (CLEAN), 2 (BLOCKED)
or 10 (waits on him). `review(...)` drives it on its own under `chain.lock` (`ship review X`).

1. `from` and `tip` come from `notes/stop-<X>.json` (round 2: the tip of the fix program's note, and
   `from` the END sha of round 1); `stop-review/<X>/START.json` records them.
2. An empty checkpoint (no commit in `from..tip`) is written `EMPTY` in `merge/<X>.md` and recorded
   merged; each parked slice gets a WAITS line.
3. The deep run: `ship ci start --level deep` as a child when the backend is `github` (its result read
   by `ship ci status` children, then the run's `summary` artifact saved as
   `checks/_nightly/<tip8>/summary.json`); otherwise, or when GitHub cannot run it, `ship nightly` then
   `ship quality --from <from>` as children. Not finished after `ci_wait_timeout_s`: started once more;
   twice: WAITS, 10.
4. `trace` writes MAP.md.
5. Readers, one `launch()` each in a frozen checkout `<worktree_root>/stop-<program>-<X>-<name>`, notes
   at `stop-review/<X>/<name>.md`: `element-<A>` per architecture element with a slice in the stop (no
   `arch`: one `batch`), `chain`, `faults` (role `fault-reader`, only with a "Fixed lines touched"
   section in GROUND.md), `operations` (only with `## Operations` in arch/ARCH.md); round 2: `round-2`.
   A notes file ending `DONE` is finished. No DONE or a time-out restarts the reader once; a second
   failure writes `NOT READ <why>` and `DONE`. A usage limit is a wait, never a failure.
6. When every reader is done and the deep run has its summary, one `verdict` worker.
7. The verdict file (REVIEW.md, round 2 REVIEW-2.md) is read with `phase.verdict`. A verdict whose END
   sha is not the tip, or a CLEAN while a `NOT READ` note, a trace FAIL or a red deep run stands, is
   refused: the file is set aside as `REVIEW.refused-<n>.md`, WAITS, 10.
8. CLEAN: 0. Round 1 BLOCKED: the fix folder `<program>-fix-<X>` must hold kind `fix`, this parent, a go
   gate by `stop-review`, one stop, and pass `check_plan.py`; then 2. Round 2 BLOCKED: one WAITS line
   per open Important; 2.
9. Every reader checkout is dropped when the review ends.

Worker prompts: `READER.md` (one file, a `{WALK}` per reader name) and `VERDICT.md` in `prompt_dir`;
the placeholders each gets are `READER_KEYS` and `VERDICT_KEYS`. The bookkeeping that survives a kill
is `.kit/<X>/review-run.json` (D-L22: in the kit's own folder, which no worker role may write); `ship merge`
trusts a verdict only when that file says `result` 0 for the same tip.

A round-1 BLOCKED fix folder is accepted only after the kit copies the parent's `ship.toml` and
`checks.toml` into it and writes its go gate through `program.set_gate` (the gates log); the verdict worker
writes the plan files only.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from ship import clock
from ship import launch as ln
from ship import phase
from ship import program as prog
from ship import state as st
from ship.gitx import GitError, git
from ship.layout import Program
from ship.proc import kill_tree, popen_group_kwargs
from ship.proc import created as proc_created
from ship.run import ChainLock, PromptError, Script, prompt_dir, render
from ship.settings import Settings
from ship.stop_trace import TraceError, stop_range, trace
from ship.worktree import checkout_copy, drop_copy

READER_KEYS = ("PROGRAM", "STOP", "ROUND", "NAME", "WALK", "ELEMENT", "SLICES", "CHECKOUT", "REPO", "FROM", "TIP",
               "MAP", "NOTES", "RULES", "REVIEW_RULES", "SHIP")
VERDICT_KEYS = ("PROGRAM", "STOP", "ROUND", "REPO", "FROM", "TIP", "MAP", "NOTES", "DEEP_SUMMARY", "QUALITY_SUMMARY",
                "CI_SUMMARY", "DEEP_RESULT", "TRACE_FAILS", "VERDICT_FILE", "END_LINE", "PR_BODY", "FIX_PROGRAM",
                "CORE_SENTENCE", "LAST_CORE", "RULES", "REVIEW_RULES", "SHIP")
FIXED_LINES = re.compile(r"^#+\s*Fixed lines touched\s*$", re.M | re.I)
OPERATIONS = re.compile(r"^##\s*Operations\s*$", re.M)
IMPORTANT = re.compile(r"\bImportant\b")
READER_RESTARTS = 1  # a reader that fails is started once more, then it is "not read"
SETTINGS_FILES = ("ship.toml", "checks.toml")


def add_wait(program: Program, text: str, see: str = "", detail: str = "") -> None:
    """One `- [ ] <text> (see <file>)` line in notes/WAITS-ON-YOU.md, never twice."""
    path = program.waits
    path.parent.mkdir(parents=True, exist_ok=True)
    line = f"- [ ] {text}" + (f" (see {see})" if see else "")
    old = path.read_text("utf-8") if path.exists() else ""
    if line in old.splitlines():
        return
    body = line + "\n" + "".join(f"    {x}\n" for x in detail.splitlines())
    path.write_text(old + body, "utf-8", newline="\n")


def notes_done(path: Path) -> bool:
    try:
        lines = [x.strip() for x in path.read_text("utf-8", errors="replace").splitlines() if x.strip()]
    except OSError:
        return False
    return bool(lines) and lines[-1] == "DONE"


def not_read(path: Path) -> bool:
    try:
        return path.read_text("utf-8", errors="replace").lstrip().startswith("NOT READ")
    except OSError:
        return False


def project_files(program: Program, settings: Settings) -> tuple[str, str]:
    """(PROJECT-RULES.md, REVIEW.md) of the program's project in the factory home."""
    try:
        name = (prog.load(program).project if program.project_file.exists() else None) or "qmx"
    except prog.ProgramError:
        name = "qmx"
    home = ln.factory_home(settings) / "projects" / name
    return str(home / "PROJECT-RULES.md"), str(home / "REVIEW.md")


def checkpoint_key(state: st.State, stop: str) -> str:
    """The state.json checkpoint a stop names: its SLICES.md `stop`, or "" for a one-checkpoint table."""
    keys = state.checkpoints()
    if stop in keys:
        return stop
    if keys == [""]:
        return ""
    raise st.StateError(f"no checkpoint {stop} in state.json (it has {keys})")


@dataclasses.dataclass
class Reader:
    name: str  # element-A1, batch, chain, faults, operations, round-2
    walk: str
    role: str  # reader | fault-reader
    element: str = ""
    slices: tuple[str, ...] = ()


class Checkpoint:
    def __init__(self, program: Program, stop: str, settings: Settings, round: int | None = None):
        self.program, self.stop, self.settings = program, stop, settings
        self.dir = program.stop_review(stop)
        self.memo_path = program.review_run(stop)  # in .kit/: no worker may write it (D-L22)
        self.memo: dict = self._load_memo()
        if round is None:
            first, _ = phase.verdict(self.dir / "REVIEW.md")
            round = 2 if first == "BLOCKED" else 1
        if self.memo.get("round") not in (None, round):
            self.memo = {}  # a new round starts its own bookkeeping
        self.round = round
        self.memo["round"] = round
        self.roles = ln.load_roles(settings)
        self.handles: dict[str, ln.Handle] = {}
        self.scripts: list[Script] = []
        self.code: int | None = None
        self.copies: list[Path] = []
        self.last_ci_poll = 0.0

    # -- bookkeeping --

    def _load_memo(self) -> dict:
        try:
            return json.loads(self.memo_path.read_text("utf-8"))
        except (OSError, ValueError):
            return {}

    def save(self) -> None:
        self.memo_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.memo_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.memo, indent=2) + "\n", "utf-8", newline="\n")
        st.replace(tmp, self.memo_path)

    def result(self) -> int | None:
        return self.code

    def children(self) -> list[dict]:
        rows = [{"pid": h.pid, "created": h.created, "role": h.role.name, "id": name, "session": h.session_id,
                 "started": h.folder.name} for name, h in self.handles.items()]
        return rows + [{"pid": s.proc.pid, "created": s.created, "role": s.name, "id": self.stop,
                        "started": s.started} for s in self.scripts]

    def stop_children(self) -> None:
        for handle in self.handles.values():
            handle.kill()
        for script in self.scripts:
            if script.done() is None:
                kill_tree(script.proc.pid)
        self.handles.clear()
        self.scripts.clear()

    def end(self, code: int, lines: list[str], why: str = "") -> list[str]:
        self.code = code
        self.memo["result"] = code
        self.save()
        self.stop_children()
        state = st.load(self.program)
        for path in dict.fromkeys([*self.copies, *(self.copy_path(r.name) for r in self.readers())]):
            if path.exists():
                drop_copy(Path(state.repo), path, self.settings)
        return lines + [f"REVIEW {self.stop} round {self.round} ends {code}{': ' + why if why else ''}"]

    def wait(self, text: str, see: str = "", detail: str = "") -> None:
        add_wait(self.program, text, see or str(self.dir), detail)

    # -- where --

    @property
    def fix_folder(self) -> Program:
        return Program(self.program.dir.parent / f"{self.program.dir.name}-fix-{self.stop}")

    @property
    def verdict_file(self) -> Path:
        return self.dir / ("REVIEW.md" if self.round == 1 else "REVIEW-2.md")

    def copy_path(self, name: str) -> Path:
        root = Path(st.load(self.program).worktree_root)
        return root / f"stop-{self.program.dir.name}-{self.stop}-{name}"

    def notes(self, name: str) -> Path:
        return self.dir / f"{name}.md"

    # -- one tick --

    def tick(self) -> list[str]:
        if self.code is not None:
            return []
        lines: list[str] = []
        if "tip" not in self.memo:
            lines += self.begin()
            if self.code is not None:
                return lines
        lines += self.deep_tick()
        if self.code is not None:
            return lines
        if not self.limited():
            lines += self.readers_tick()
        lines += self.verdict_tick()
        if self.code is None:
            self.save()
        return lines

    def limited(self) -> bool:
        until = self.memo.get("limit_until")
        return bool(until and dt.datetime.fromisoformat(until) > clock.now())

    def begin(self) -> list[str]:
        state = st.load(self.program)
        repo = Path(state.repo)
        try:
            if self.round == 1:
                base, tip = stop_range(self.program, self.stop)
            else:
                _, end1 = phase.verdict(self.dir / "REVIEW.md")
                base, tip = end1, stop_range(self.fix_folder, self.stop)[1]
        except TraceError as exc:
            self.wait(f"stop {self.stop} cannot be reviewed: {exc}")
            return self.end(10, [], str(exc))
        self.memo.update({"from": base, "tip": tip})
        self.dir.mkdir(parents=True, exist_ok=True)
        (self.dir / "START.json").write_text(json.dumps(
            {"stop": self.stop, "round": self.round, "from": base, "tip": tip,
             "at": clock.now().isoformat(timespec="seconds")}, indent=2) + "\n", "utf-8", newline="\n")
        lines = [f"START review {self.stop} round {self.round}: {base[:10] or '(start)'}..{tip[:10]}"]
        try:
            git(repo, "fetch", "-q", state.remote, timeout=self.settings.git_timeout_s)
        except GitError:
            pass
        if self.round == 1 and base:
            count = git(repo, "rev-list", "--count", f"{base}..{tip}", timeout=self.settings.git_timeout_s).strip()
            if count == "0":
                return self.empty(state, lines)
        ok, out = trace(self.program, self.stop, self.settings, base, tip)
        self.memo["trace_fails"] = [x for x in out if x.startswith("FAIL")]
        lines += out
        return lines

    def empty(self, state: st.State, lines: list[str]) -> list[str]:
        key = checkpoint_key(state, self.stop)
        parked = sorted(s.id for s in state.slices.values() if s.checkpoint == key
                        and s.status in (st.Status.PARKED, st.Status.BLOCKED_BY))
        note = self.program.merge_note(self.stop)
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(f"EMPTY no commits; parked: {', '.join(parked) or 'none'}\n", "utf-8", newline="\n")
        with st.locked(self.program) as fresh:
            lines.append(fresh.mark_merged(key))
        for sid in parked:
            reason = state.slices[sid].reason or state.slices[sid].blocked_by or ""
            self.wait(f"stop {self.stop} closed empty; slice {sid} is parked: {reason}", str(note))
        return self.end(0, lines + [f"EMPTY stop {self.stop}: no commits; parked {parked}"], "empty")

    # -- the deep run --

    def start_child(self, name: str, *args: str) -> Script:
        logs = self.program.checks_root / "_review"
        logs.mkdir(parents=True, exist_ok=True)
        stamp = clock.now().strftime("%Y%m%dT%H%M%S") + f"-{time.monotonic_ns() % 10**6:06d}"
        log = logs / f"{stamp}-{name.replace(' ', '-')}.log"
        argv = [sys.executable, str(ln.KIT), *name.split(), "--program", str(self.program.dir), *args]
        with open(log, "w", encoding="utf-8", newline="\n") as out:
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
                                    **popen_group_kwargs())
        script = Script(name, self.stop, proc, log, clock.now().isoformat(timespec="seconds"), (),
                        proc_created(proc.pid))
        script.began_wall = time.time()
        self.scripts.append(script)
        return script

    def running(self, name: str) -> Script | None:
        return next((s for s in self.scripts if s.name == name), None)

    def deep_tick(self) -> list[str]:
        deep = self.memo.setdefault("deep", {})
        if deep.get("done"):
            return []
        lines = []
        for script in list(self.scripts):
            rc = script.done()
            if rc is None:
                continue
            self.scripts.remove(script)
            lines.append(f"DEEP {script.name} exit {rc}")
            if script.name == "ci start":
                deep["backend"] = "github" if rc == 0 else "local"
                deep["started_at"] = clock.now().isoformat(timespec="seconds")
                if rc != 0:
                    lines += [f"DEEP {x}" for x in script.output()[-3:]]
            elif script.name in ("ci status", "nightly", "quality"):
                key = "ci" if script.name == "ci status" else script.name
                summary = (self.program.quality(self.memo["tip"]) if key == "quality"
                           else self.program.nightly(self.memo["tip"])) / "summary.txt"
                if rc in (0, 1) and summary.exists() and summary.stat().st_mtime >= script.began_wall - 2:
                    deep[key] = rc
                elif rc != 2:  # 2 is "still running on GitHub"; anything else without a summary crashed
                    deep["crashes"] = deep.get("crashes", 0) + 1
                    lines.append(f"DEEP {script.name} exit {rc} with no summary; started again "
                                 f"({deep['crashes']} of {self.settings.max_restarts})")
                    if deep["crashes"] >= self.settings.max_restarts:
                        self.wait(f"the deep run of stop {self.stop} keeps failing to report", str(script.log),
                                  "\n".join(script.output()[-15:]))
                        return self.end(10, lines, "deep run keeps crashing")
        if self.scripts:
            return lines
        if "backend" not in deep:
            if self.settings.ci == "github":
                self.start_child("ci start", "--level", "deep")
                return lines + ["START ci start --level deep"]
            deep["backend"] = "local"
        if deep["backend"] == "local":
            if "nightly" not in deep:
                self.start_child("nightly")
                return lines + ["START nightly"]
            if "quality" not in deep:
                if not self.memo.get("from"):
                    deep["quality"] = 0
                    return lines + ["SKIP quality: the stop has no from commit"]
                self.start_child("quality", "--from", self.memo["from"])
                return lines + [f"START quality --from {self.memo['from'][:10]}"]
            deep["green"] = deep["nightly"] == 0 and deep["quality"] == 0
            deep["done"] = True
            return lines + [f"DEEP local {'green' if deep['green'] else 'red'}"]
        if "ci" in deep:
            got = self.fetch_summary()
            if got is None:
                return lines + self.deep_overdue()
            deep["summary_json"] = got
            deep["green"] = deep["ci"] == 0
            deep["done"] = True
            return lines + [f"DEEP github {'green' if deep['green'] else 'red'}; summary {got}"]
        overdue = self.deep_overdue()
        if overdue or self.code is not None:
            return lines + overdue
        if time.monotonic() - self.last_ci_poll >= self.settings.ci_poll_s:
            self.last_ci_poll = time.monotonic()
            self.start_child("ci status")
        return lines

    def deep_overdue(self) -> list[str]:
        deep = self.memo["deep"]
        since = deep.get("started_at")
        if not since:
            return []
        waited = (clock.now() - dt.datetime.fromisoformat(since)).total_seconds()
        if waited < self.settings.ci_wait_timeout_s:
            return []
        if not deep.get("retries"):
            deep["retries"] = 1
            deep["started_at"] = clock.now().isoformat(timespec="seconds")
            self.start_child("ci start", "--level", "deep", "--fresh")
            return [f"DEEP not finished after {waited:.0f}s; started once more"]
        url = (st.load(self.program).ci.get("deep") or {}).get("url") or "the recorded run"
        self.wait(f"the deep run for stop {self.stop} did not finish twice ({url}); no local-only merge")
        return self.end(10, [f"WAITS deep run stuck: {url}"], "deep run stuck")

    def fetch_summary(self) -> str | None:
        """The run's `summary` artifact as checks/_nightly/<tip8>/summary.json: its path, or None while
        it cannot be read."""
        from ship import ci

        tip = self.memo["tip"]
        dest = self.program.nightly(tip)
        target = dest / "summary.json"
        if target.exists():
            try:
                if str(json.loads(target.read_text("utf-8")).get("sha") or "") == tip:
                    return str(target)
            except (OSError, ValueError, AttributeError):
                pass
            target.unlink(missing_ok=True)
        state = st.load(self.program)
        run_id = (state.ci.get("deep") or {}).get("run_id")
        if not run_id:
            return None
        folder = dest / "ci-summary"
        try:
            ok = ci.gh_for(state, self.settings).download(str(run_id), "summary", folder)
        except GitError:
            return None
        if not ok or not (folder / "summary.json").exists():
            return None
        try:
            sha = str(json.loads((folder / "summary.json").read_text("utf-8")).get("sha") or "")
        except (OSError, ValueError, AttributeError):
            sha = ""
        if sha != tip:  # D-L22: a summary of another commit never stands for this tip
            self.memo.setdefault("deep", {})["summary_mismatch"] = sha or "(none)"
            shutil.rmtree(folder, ignore_errors=True)
            return None
        shutil.copyfile(folder / "summary.json", target)
        return str(target)

    # -- readers --

    def readers(self) -> list[Reader]:
        if self.round == 2:
            return [Reader("round-2", "round-2", "reader")]
        state = st.load(self.program)
        mine = {s.id for s in state.slices.values() if (s.checkpoint or self.stop) == self.stop}
        try:
            index = prog.load(self.program) if self.program.project_file.exists() else prog.Index()
        except prog.ProgramError:
            index = prog.Index()
        elements: dict[str, set[str]] = {}
        for chain in index.chains:
            if isinstance(chain, dict):
                for el in chain.get("arch") or []:
                    own = {s for s in chain.get("slices") or [] if s in mine}
                    if own:
                        elements.setdefault(str(el), set()).update(own)
        out = [Reader(f"element-{el}", "element", "reader", el, tuple(sorted(own)))
               for el, own in sorted(elements.items())]
        if not out:
            out = [Reader("batch", "batch", "reader", "", tuple(sorted(mine)))]
        out.append(Reader("chain", "chain", "reader", "", tuple(sorted(mine))))
        ground = self.program.dir / "GROUND.md"
        if ground.exists() and fixed_lines(ground.read_text("utf-8", errors="replace")):
            out.append(Reader("faults", "faults", "fault-reader", "", tuple(sorted(mine))))
        arch = self.program.dir / "arch" / "ARCH.md"
        if arch.exists() and OPERATIONS.search(arch.read_text("utf-8", errors="replace")):
            out.append(Reader("operations", "operations", "reader", "", tuple(sorted(mine))))
        return out

    def readers_tick(self) -> list[str]:
        lines = []
        book = self.memo.setdefault("readers", {})
        for reader in self.readers():
            rec = book.setdefault(reader.name, {"attempts": 0})
            notes = self.notes(reader.name)
            handle = self.handles.get(reader.name)
            if handle is not None:
                got = handle.poll()
                if got is None:
                    continue
                del self.handles[reader.name]
                lines.append(f"READER {reader.name} ended: {got.kind} {got.line or got.note}".rstrip())
                if notes_done(notes):
                    rec["done"] = True
                    continue
                if got.kind == "limit":
                    self.memo["limit_until"] = got.limit_reset
                    lines.append(f"LIMIT reader {reader.name}: waits until {got.limit_reset}")
                    continue
                rec["attempts"] += 1
                if rec["attempts"] > READER_RESTARTS:
                    why = f"{got.kind} {got.line or got.note}".strip() + f" after {rec['attempts']} runs"
                    notes.parent.mkdir(parents=True, exist_ok=True)
                    notes.write_text(f"NOT READ {why}\nDONE\n", "utf-8", newline="\n")
                    rec["done"] = True
                    lines.append(f"NOT READ {reader.name}: {why}")
                    continue
            if rec.get("done") or notes_done(notes):
                rec["done"] = True
                continue
            if self.limited():
                continue
            lines += self.start_reader(reader, rec)
            if self.code is not None:
                return lines
        return lines

    def start_reader(self, reader: Reader, rec: dict) -> list[str]:
        state = st.load(self.program)
        rules, review_rules = project_files(self.program, self.settings)
        copy = checkout_copy(Path(state.repo), self.copy_path(reader.name), self.memo["tip"], self.settings)
        if copy not in self.copies:
            self.copies.append(copy)
        notes = self.notes(reader.name)
        values = {"PROGRAM": str(self.program.dir), "STOP": self.stop, "ROUND": str(self.round),
                  "NAME": reader.name, "WALK": reader.walk, "ELEMENT": reader.element,
                  "SLICES": ", ".join(reader.slices), "CHECKOUT": str(copy), "REPO": state.repo,
                  "FROM": self.memo.get("from", ""), "TIP": self.memo["tip"], "MAP": str(self.dir / "MAP.md"),
                  "NOTES": str(notes), "RULES": rules, "REVIEW_RULES": review_rules, "SHIP": str(ln.KIT)}
        try:
            prompt = render(prompt_dir(self.settings) / "READER.md", values)
        except (PromptError, OSError) as exc:
            self.wait(f"the reader prompt cannot be filled: {exc}")
            return self.end(10, [], f"reader prompt: {exc}")
        env = {"SHIP_NOTES": str(notes), "SHIP_STOP": self.stop, "SHIP_REPO": state.repo, "SHIP_TIP": self.memo["tip"]}
        n = rec["attempts"] + 1
        handle = ln.launch(self.roles[reader.role], prompt, copy, self.program,
                           f"stop-{self.stop}-r{self.round}-{reader.name}-{n}", self.settings, extra_env=env,
                           label=f"{self.stop} {reader.name}")
        if handle is None:
            return [f"WAIT {reader.name}: no free worker seat (or the Fable seat is taken)"]
        self.handles[reader.name] = handle
        return [f"START {reader.role} {reader.name} pid {handle.pid}"]

    # -- the verdict --

    def ready_for_verdict(self) -> bool:
        deep = self.memo.get("deep") or {}
        if not deep.get("done"):
            return False
        if not self.program.nightly(self.memo["tip"]).joinpath("summary.txt").exists():
            return False
        book = self.memo.get("readers") or {}
        return all((book.get(r.name) or {}).get("done") for r in self.readers())

    def verdict_tick(self) -> list[str]:
        lines = []
        handle = self.handles.get("verdict")
        rec = self.memo.setdefault("verdict", {"attempts": 0})
        if handle is not None:
            got = handle.poll()
            if got is None:
                return lines
            del self.handles["verdict"]
            lines.append(f"VERDICT worker ended: {got.kind} {got.line or got.note}".rstrip())
            if got.kind == "ok" and got.contract == "WAITS":
                self.wait(f"the verdict worker for stop {self.stop} needs you", got.value)
                return self.end(10, lines, "the verdict worker waits")
            if got.kind == "limit":
                self.memo["limit_until"] = got.limit_reset
                return lines + [f"LIMIT verdict: waits until {got.limit_reset}"]
            if not (got.kind == "ok" and got.contract == "DONE"):
                rec["attempts"] += 1
                if rec["attempts"] >= self.settings.max_restarts:
                    self.wait(f"the verdict worker for stop {self.stop} failed {rec['attempts']} times "
                              f"({got.kind})", str(handle.stdout))
                    return self.end(10, lines, "the verdict worker keeps failing")
                return lines + [f"RESTART verdict ({got.kind})"]
            return lines + self.judge()
        if self.verdict_file.exists() and phase.verdict(self.verdict_file)[0]:
            return lines + self.judge()  # written before a kill: judge it, do not ask again
        if self.limited() or not self.ready_for_verdict():
            return lines
        return lines + self.start_verdict(rec)

    def start_verdict(self, rec: dict) -> list[str]:
        state = st.load(self.program)
        rules, review_rules = project_files(self.program, self.settings)
        tip = self.memo["tip"]
        deep = self.memo["deep"]
        nightly = self.program.nightly(tip)
        quality = self.program.quality(tip) / "summary.txt"
        index = self._index()
        stops = index.stops if index else []
        this = next((s for s in stops if s.id == self.stop), None)
        later_core = [s for s in stops[stops.index(this) + 1:] if s.tier == "core"] if this else []
        values = {"PROGRAM": str(self.program.dir), "STOP": self.stop, "ROUND": str(self.round), "REPO": state.repo,
                  "FROM": self.memo.get("from", ""), "TIP": tip, "MAP": str(self.dir / "MAP.md"),
                  "NOTES": ", ".join(str(self.notes(r.name)) for r in self.readers()),
                  "DEEP_SUMMARY": str(nightly / "summary.txt"),
                  "QUALITY_SUMMARY": str(quality) if quality.exists() else "none",
                  "CI_SUMMARY": deep.get("summary_json") or "none",
                  "DEEP_RESULT": "green" if deep.get("green") else "red",
                  "TRACE_FAILS": str(len(self.memo.get("trace_fails") or [])),
                  "VERDICT_FILE": str(self.verdict_file),
                  "END_LINE": f"END {tip} checkpoint-{self.stop}-round-{self.round}",
                  "PR_BODY": str(self.program.dir / "merge" / f"{self.stop}-pr.md"),
                  "FIX_PROGRAM": str(self.fix_folder.dir), "CORE_SENTENCE": (index.core_sentence if index else "") or "",
                  "LAST_CORE": "yes" if this and this.tier == "core" and not later_core else "no",
                  "RULES": rules, "REVIEW_RULES": review_rules, "SHIP": str(ln.KIT)}
        try:
            prompt = render(prompt_dir(self.settings) / "VERDICT.md", values)
        except (PromptError, OSError) as exc:
            self.wait(f"the verdict prompt cannot be filled: {exc}")
            return self.end(10, [], f"verdict prompt: {exc}")
        env = {"SHIP_STOP": self.stop, "SHIP_REPO": state.repo, "SHIP_TIP": tip}
        n = rec["attempts"] + 1
        handle = ln.launch(self.roles["verdict"], prompt, self.program.dir, self.program,
                           f"stop-{self.stop}-r{self.round}-verdict-{n}", self.settings, extra_env=env,
                           label=f"{self.stop} verdict")
        if handle is None:
            return ["WAIT verdict: no free worker seat"]
        self.handles["verdict"] = handle
        return [f"START verdict pid {handle.pid}"]

    def _index(self) -> prog.Index | None:
        try:
            return prog.load(self.program) if self.program.project_file.exists() else None
        except prog.ProgramError:
            return None

    def refuse(self, why: str) -> list[str]:
        n = 1
        while (self.dir / f"{self.verdict_file.stem}.refused-{n}.md").exists():
            n += 1
        aside = self.dir / f"{self.verdict_file.stem}.refused-{n}.md"
        self.verdict_file.replace(aside)
        self.wait(f"the stop {self.stop} verdict was refused: {why}", str(aside))
        return self.end(10, [f"REFUSED verdict: {why}"], "verdict refused")

    def judge(self) -> list[str]:
        word, end = phase.verdict(self.verdict_file)
        tip = self.memo["tip"]
        if not word:
            return self.refuse(f"{self.verdict_file.name} has no VERDICT line")
        if end != tip:
            return self.refuse(f"its END sha {end or '(none)'} is not the tip {tip}")
        if word == "CLEAN":
            unread = [r.name for r in self.readers() if not_read(self.notes(r.name))]
            if unread:
                return self.refuse(f"CLEAN while readers were not read: {unread}")
            if self.memo.get("trace_fails"):
                return self.refuse(f"CLEAN while trace FAIL lines stand: {self.memo['trace_fails'][:3]}")
            if not (self.memo.get("deep") or {}).get("green"):
                return self.refuse("CLEAN while the deep run is red")
            return self.end(0, [f"CLEAN stop {self.stop} round {self.round} at {tip[:10]}"], "clean")
        if self.round == 1:
            problem = self.fix_problem()
            if problem:
                self.wait(f"stop {self.stop} is BLOCKED but its fix program is not ready: {problem}",
                          str(self.fix_folder.dir))
                return self.end(10, [f"FIX folder not ready: {problem}"], "fix folder not ready")
            self.adopt_fix()
            return self.end(2, [f"BLOCKED stop {self.stop}: fix program {self.fix_folder.dir.name}"], "blocked")
        found = [x.strip() for x in self.verdict_file.read_text("utf-8").splitlines() if IMPORTANT.search(x)]
        for line in found or [f"stop {self.stop} is still BLOCKED after round 2"]:
            self.wait(f"stop {self.stop} round 2: {line.lstrip('-* ')}", str(self.verdict_file))
        return self.end(2, [f"BLOCKED stop {self.stop} after round 2: {len(found)} open"], "blocked twice")

    def adopt_fix(self) -> None:
        """The checked fix folder's go gate, as the verdict worker wrote it, goes through `set_gate`, so the
        gates log holds it (D-L22)."""
        go = prog.load(self.fix_folder).gate("go") or {}
        prog.set_gate(self.fix_folder, "go", by="stop-review", source=str(go.get("source") or self.verdict_file),
                      advance=bool(go.get("advance", True)), at=str(go.get("at") or "") or None)

    def fix_problem(self) -> str | None:
        fix = self.fix_folder
        if not fix.project_file.exists():
            return f"no {fix.project_file}"
        try:
            index = prog.load(fix)
        except prog.ProgramError as exc:
            return str(exc)
        if index.kind != "fix":
            return f"kind is {index.kind}, not fix"
        if index.parent != self.program.dir.name:
            return f"parent is {index.parent}, not {self.program.dir.name}"
        go = index.gate("go") or {}
        if go.get("by") != "stop-review":
            return f"its go gate is by {go.get('by')}, not stop-review"
        if [s.id for s in index.stops] != [self.stop]:
            return f"its stops are {[s.id for s in index.stops]}, want [{self.stop}]"
        copy_settings(self.program, fix)
        script = ln.factory_home(self.settings) / "skills" / "factory-core" / "scripts" / "check_plan.py"
        if not script.exists():
            return f"no {script} to check it"
        done = subprocess.run([sys.executable, str(script), str(fix.dir), str(ln.KIT)], capture_output=True,
                              text=True, encoding="utf-8", errors="replace", stdin=subprocess.DEVNULL,
                              timeout=600)
        if done.returncode != 0:
            fails = [x for x in done.stdout.splitlines() if x.startswith("FAIL")]
            return f"check_plan.py: {'; '.join(fails[:3]) or done.stderr.strip()[:300]}"
        return None


def copy_settings(parent: Program, fix: Program) -> None:
    """The kit, never the verdict worker, gives a fix folder its parent's `ship.toml` and `checks.toml`
    (D-L22): a worker-written `ship.toml` could name any command as `gh` or `claude`."""
    for name in SETTINGS_FILES:
        src, dst = parent.dir / name, fix.dir / name
        if src.exists():
            dst.write_bytes(src.read_bytes())
        else:
            dst.unlink(missing_ok=True)


def settings_differ(parent: Program, fix: Program) -> list[str]:
    """The settings files of a fix folder that are not byte for byte its parent's."""
    def body(path: Path) -> bytes | None:
        return path.read_bytes() if path.exists() else None

    return [name for name in SETTINGS_FILES if body(parent.dir / name) != body(fix.dir / name)]


def fixed_lines(ground: str) -> bool:
    """GROUND.md has a "Fixed lines touched" section with something in it."""
    m = FIXED_LINES.search(ground)
    if not m:
        return False
    body = ground[m.end():]
    nxt = re.search(r"^#", body, re.M)
    body = body[:nxt.start()] if nxt else body
    words = [x.strip(" -*") for x in body.splitlines() if x.strip(" -*")]
    return any(w.casefold() not in ("none", "n/a", "nothing") for w in words)


def review(program: Program, stop: str, settings: Settings, round: int | None = None,
           poll_s: float | None = None) -> int:
    """`ship review X`: the Checkpoint driven to its end under chain.lock. 0 CLEAN, 2 BLOCKED, 10 waits,
    11 another conveyor holds the program."""
    lock = ChainLock(program, "review")
    if not lock.acquire():
        print(f"LOCKED chain.lock is held by pid {lock.read().get('pid')}")
        return 11
    cp = Checkpoint(program, stop, settings, round)
    period = settings.chain_poll_s if poll_s is None else poll_s
    try:
        while True:
            for line in cp.tick():
                print(line, flush=True)
            if cp.result() is not None:
                return cp.result()
            lock.refresh(cp.children())
            time.sleep(period)
    finally:
        cp.stop_children()
        lock.release()
