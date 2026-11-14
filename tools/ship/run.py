"""run: the build loop. Turns a program's briefs into landed slices with nobody watching (unit U07).

`python tools/ship run --program P` holds `chain.lock`, then ticks every `chain_poll_s` seconds. Each tick:

1. `main-check` (when a snapshot exists); a changed main checkout writes WAITS and stops (exit 1).
2. Power, internet and GitHub (`power_watch.step`). `HOLD` means: route what finished, start nothing.
3. A usage reset in the future means: route what finished, start no worker.
4. Route every finished child (a builder, `verify_ready`, `slice_checks`, `land`) by the rules card's table.
5. `status`: a `STALE` slice with a live builder has only that builder's process tree stopped, its seat
   recovered and restarted. `BREAKER` writes WAITS and stops (exit 1).
6. Fill free seats: dead slices, slices due a fix round, the "could start" list taken lane by lane, then
   `PREBUILD`. One `land` at a time. A worktree whose `setup` failed or timed out (D-L25) gets no worker: its
   seat is released (the slice is recovered as dead, never a death), it is tried again next tick, and its
   `max_restarts`-th failed setup parks it `manual` with a WAITS line.
7. When the open checkpoint is built and `notes/stop-<X>.json` is missing, write it.

A builder's prompt gets `PROMPT_KEYS`: the slice's own values, `RULES` (the project's PROJECT-RULES.md) and
`PROJECT.<key>` for every key of the profile's [project] table. Roles come from roles.toml with the profile's
overrides. A fix round's reason and paths are kept in run.json (`fixing`) until the slice passes `verify_ready`,
so a fixer that dies and is restarted gets them again. When a builder replies `READY <sha>`, the kit stamps the
END line (`END <sha> <dispatch id>`) on each `evidence_required` file of its evidence folder, replacing any END
line already there; `verify_ready` then reads them.

Routing reads `state.json`, so a run killed at any point and started again carries on: a `ready` slice
gets `slice_checks`, a `checked` one `land`, a `red` one a fix round. The little that is not in
`state.json` (a READY reply waiting for `verify_ready` while GitHub is down, a slice due a fix round after
a lone landing went red, a batch being landed one slice at a time) is kept in `<program>/run.json`.

Exit: 0 the checkpoint is built (or nothing is left), 10 waits on him (the build branch is gone),
11 another live process holds `chain.lock`, 1 the breaker tripped or the main checkout changed.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from ship import clock
from ship import launch as ln
from ship import state as st
from ship.gitx import GitError, remote_sha
from ship.layout import Program
from ship.proc import holder_alive, kill_tree, pid_alive, popen_group_kwargs, same_process, started_before_boot
from ship.proc import created as proc_created
from ship.settings import Settings
from ship.state import ParkCause, Status

PLACEHOLDER = re.compile(r"\{([A-Z][A-Z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?)\}")
PROMPT_KEYS = ("SLICE", "PROGRAM", "WORKTREE", "WORKTREE_ROOT", "BRANCH", "PARENT", "EVIDENCE", "DISPATCH_ID",
               "KIND", "ATTEMPT", "RESTART", "LEFTOVER", "LEFTOVER_LINE", "RESTART_OF", "FIX_REASON", "FIX_PATHS",
               "SHIP", "RULES", "PROJECT.*")  # PROJECT.* is every key of the profile's [project] table
LAND_TESTS = re.compile(r"^FAIL land-tests (\S+) batch \[([^\]]*)\]")
LAND_ONE = re.compile(r"^FAIL land-(?!tests\b|push\b)(\S+) (.*)$")


class PromptError(Exception):
    pass


def render(prompt_path: Path, values: dict[str, str]) -> str:
    """Fill `{NAME}` placeholders. A placeholder left unfilled is an error, never sent to a worker."""
    text = prompt_path.read_text("utf-8")
    missing = sorted({m.group(1) for m in PLACEHOLDER.finditer(text) if m.group(1) not in values})
    if missing:
        raise PromptError(f"{prompt_path}: placeholders with no value: {missing}")
    return PLACEHOLDER.sub(lambda m: str(values[m.group(1)]), text)


def prompt_dir(settings: Settings) -> Path:
    return Path(settings.prompt_dir) if settings.prompt_dir else ln.factory_home(settings) / "skills" / "factory" / "prompts"


# ---- chain.lock -------------------------------------------------------------------------------------


class ChainLock:
    """One conveyor per program (FACTORY-DESIGN 11.6): create-exclusive, pid and creation time inside,
    taken over when its holder is gone (D-L14).

    A holder is alive only when its pid still names the same process (same creation time); a lock written
    before the machine last started is stale whatever its pids say. A dead holder's children are stopped
    before the take-over, each only on an exact pid and creation-time match, so a reused pid is never
    killed. A stale lock from before a reboot is taken over with no kill at all."""

    def __init__(self, program: Program, step: str):
        self.program, self.step = program, step
        self.started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")  # real time, not the test clock
        self.created = proc_created(os.getpid())
        self.mine = False

    def read(self) -> dict:
        try:
            return json.loads(self.program.chain_lock.read_text("utf-8") or "{}")
        except (OSError, ValueError):
            return {}

    def acquire(self) -> bool:
        path = self.program.chain_lock
        while True:
            try:
                fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(fd, json.dumps(self._body([])).encode())
                os.close(fd)
                self.mine = True
                return True
            except FileExistsError:
                held = self.read()
                pid = int(held.get("pid") or 0)
                if pid == os.getpid() and same_process(pid, held.get("created")):
                    self.mine = True
                    return True
                if before_boot(held.get("started")):
                    path.unlink(missing_ok=True)  # written before the last start: nothing it names is ours
                    continue
                young = time.time() - path.stat().st_mtime < 10 if path.exists() else False
                if holder_alive(pid, held.get("created")) or (not pid and young):
                    return False
                for child in held.get("children", []):
                    if same_process(int(child.get("pid") or 0), child.get("created")):
                        kill_tree(int(child["pid"]))
                path.unlink(missing_ok=True)

    def _body(self, children: list[dict]) -> dict:
        return {"pid": os.getpid(), "created": self.created, "started": self.started,
                "program": self.program.dir.name, "step": self.step, "children": children}

    def refresh(self, children: list[dict]) -> None:
        tmp = self.program.chain_lock.with_suffix(".lock.tmp")
        tmp.write_text(json.dumps(self._body(children), indent=2), "utf-8")
        st.replace(tmp, self.program.chain_lock)

    def release(self) -> None:
        if self.mine and int(self.read().get("pid") or 0) == os.getpid():
            st.release_lock(self.program.chain_lock)
        self.mine = False


before_boot = started_before_boot  # the lock was written before this machine last started


# ---- children ---------------------------------------------------------------------------------------


@dataclasses.dataclass
class Script:
    """A kit command run as a child process: verify_ready, slice_checks or land."""

    name: str
    slice: str  # "" for land
    proc: subprocess.Popen
    log: Path
    started: str
    args: tuple[str, ...] = ()
    created: float | None = None
    began: float = dataclasses.field(default_factory=time.monotonic)

    def done(self) -> int | None:
        return self.proc.poll()

    def output(self) -> list[str]:
        try:
            return self.log.read_text("utf-8", errors="replace").splitlines()
        except OSError:
            return []


@dataclasses.dataclass
class Worker:
    slice: str
    kind: str  # builder | fixer
    handle: ln.Handle


@dataclasses.dataclass
class Memo:
    """What routing needs that state.json does not hold. Saved as run.json."""

    verify: dict[str, str] = dataclasses.field(default_factory=dict)  # slice -> sha its builder reported READY
    fix: dict[str, dict] = dataclasses.field(default_factory=dict)  # slice -> {"reason", "paths"}: due a fix round
    singles: list[str] = dataclasses.field(default_factory=list)  # a red batch landed one slice at a time
    fixing: dict[str, dict] = dataclasses.field(default_factory=dict)  # slice -> the running fix round's reason, paths
    setup_fails: dict[str, int] = dataclasses.field(default_factory=dict)  # slice -> setups failed in a row
    lands: int = 0  # land runs started, for SHIP_RUN_STOP_AFTER
    land_crashes: int = 0  # land runs in a row that crashed (D-L26 F9: counted toward max_restarts, then WAITS)

    @classmethod
    def load(cls, path: Path) -> "Memo":
        try:
            raw = json.loads(path.read_text("utf-8"))
        except (OSError, ValueError):
            return cls()
        return cls(**{f.name: raw[f.name] for f in dataclasses.fields(cls) if f.name in raw})

    def save(self, path: Path) -> None:
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(dataclasses.asdict(self), indent=2), "utf-8")
        st.replace(tmp, path)


# ---- the loop ---------------------------------------------------------------------------------------


class Build:
    def __init__(self, program: Program, settings: Settings, lock: ChainLock | None = None, once: bool = False):
        self.program, self.settings, self.lock, self.once = program, settings, lock, once
        self.memo_path = program.dir / "run.json"
        self.memo = Memo.load(self.memo_path)
        self.workers: dict[str, Worker] = {}
        self.scripts: list[Script] = []
        self.exit: int | None = None
        self.ticks = 0
        self.started_any = False
        from ship import project_profile

        self.profile = project_profile.of_program(program.dir, settings)
        self.roles = ln.load_roles(settings, self.profile)
        self.prompt = prompt_dir(settings) / "BUILDER.md"
        self.claims = None  # ship.claims.Claims beside the program; None until start()
        self.claim_blocked: dict[str, str] = {}  # slice -> the program whose live claim names one of its files

    # -- start and stop --

    def start(self) -> list[str]:
        """Check the prompt, then recover every seat the last run left (its builders are gone)."""
        from ship.recover import recover

        lines = []
        try:
            render(self.prompt, {**{k: "x" for k in PROMPT_KEYS if k != "PROJECT.*"}, **self.project_values()})
        except (PromptError, OSError) as exc:
            self.wait_line(f"the builder prompt cannot be filled: {exc}")
            self.exit = 1
            return [f"STOP {exc}"]
        state = st.load(self.program)
        held = [s.id for s in state.slices.values() if s.status == Status.HELD and s.id not in self.memo.verify]
        for sid in held:
            try:
                lines += recover(self.program, self.settings, only=sid)
            except GitError as exc:
                lines.append(f"RECOVER {sid} unreachable: {exc}; again next tick")
        return lines + self.claim_files()

    def project_values(self) -> dict[str, str]:
        from ship import project_profile

        return {"RULES": project_profile.rules_file(self.profile, self.settings),
                **project_profile.project_values(self.profile)}

    def claim_files(self) -> list[str]:
        """U38: sweep the claims of finished programs, then claim every file this program's slices name."""
        from ship import claims as cl

        self.claims = cl.for_program(self.program, self.settings)
        if not self.claims.active:
            return []
        lines = self.claims.sweep()
        found = self.claims.claim(self.program.dir.name, cl.slice_files(self.program))
        lines.append(f"CLAIMED the files of {self.program.dir.name}; {len(found)} overlap other programs")
        return lines

    def claim_waits(self, state: st.State) -> list[str]:
        """Pending slices whose files another live program claims wait; it is not a park, not an attempt."""
        from ship import claims as cl

        if self.claims is None or not self.claims.active:
            return []
        pending = [s for s in state.slices.values() if s.status == Status.PENDING]
        # claim, not only look: a pattern whose earlier claim is gone gets this program's row now (D-L22)
        found = self.claims.claim(self.program.dir.name, [f for s in pending for f in s.files])
        now = cl.blocked_slices(pending, found)
        lines = [f"WAIT {sid} blocked-by claim {other}" for sid, other in sorted(now.items())
                 if self.claim_blocked.get(sid) != other]
        lines += [f"CLAIM-FREE {sid}: the claim on its files is gone" for sid in sorted(set(self.claim_blocked) - set(now))]
        self.claim_blocked = now
        return lines

    def stop_children(self) -> None:
        for worker in self.workers.values():
            worker.handle.kill()
        for script in self.scripts:
            if script.done() is None:
                kill_tree(script.proc.pid)
        self.workers.clear()
        self.scripts.clear()

    def children(self) -> list[dict]:
        rows = [{"pid": w.handle.pid, "created": w.handle.created, "role": w.kind, "id": w.slice,
                 "session": w.handle.session_id, "started": w.handle.folder.name} for w in self.workers.values()]
        rows += [{"pid": s.proc.pid, "created": s.created, "role": s.name, "id": s.slice, "started": s.started}
                 for s in self.scripts]
        return rows

    def busy(self) -> bool:
        return bool(self.workers or self.scripts)

    # -- notes for him --

    def wait_line(self, text: str, detail: str = "") -> None:
        path = self.program.waits
        path.parent.mkdir(parents=True, exist_ok=True)
        line = f"- [ ] {text}"
        old = path.read_text("utf-8") if path.exists() else ""
        if line in old.splitlines():
            return
        body = line + "\n" + "".join(f"    {ln_}\n" for ln_ in detail.splitlines())
        path.write_text(old + body, "utf-8", newline="\n")

    def chain_issue(self, text: str) -> None:
        path = self.program.notes_dir / "CHAIN-ISSUES.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8", newline="\n") as out:
            out.write(f"- {clock.now().isoformat(timespec='seconds')} {text}\n")

    # -- one tick --

    def tick(self, now) -> list[str]:
        self.ticks += 1
        self.started_any = False
        lines: list[str] = []
        if self.main_changed(lines):
            return self.finish(lines, 1)
        hold = self.power(lines)
        state = st.load(self.program)
        usage = bool(state.usage_reset_at and dt.datetime.fromisoformat(state.usage_reset_at) > now)
        if usage:
            lines.append(f"USAGE limit until {state.usage_reset_at}; no worker starts")
        gone = self.build_branch_gone(state)
        if gone:
            self.wait_line(gone)
            lines.append(f"WAITS {gone}")
            return self.finish(lines, 10)
        lines += self.route_workers()
        lines += self.route_scripts()
        if self.exit is not None:  # a script's result stopped the build (a land that keeps crashing)
            return self.finish(lines, self.exit)
        if not hold:
            lines += self.retry_recover()
        breaker = self.check_status(lines)
        if breaker:
            return self.finish(lines, 1)
        if not hold:
            lines += self.start_scripts()
            lines += self.claim_waits(st.load(self.program))
            if not usage and not (self.once and self.ticks > 1):
                lines += self.fill_seats()
        lines += self.stop_note()
        self.memo.save(self.memo_path)
        if self.lock:
            self.lock.refresh(self.children())
        self._log(lines)
        return lines

    def finish(self, lines: list[str], code: int) -> list[str]:
        self.exit = code
        self.memo.save(self.memo_path)
        self._log(lines)
        return lines

    def _log(self, lines: list[str]) -> None:
        if not lines:
            return
        path = self.program.notes_dir / "run.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        stamp = clock.now().isoformat(timespec="seconds")
        with open(path, "a", encoding="utf-8", newline="\n") as out:
            out.writelines(f"{stamp} {line}\n" for line in lines)

    def done(self) -> bool:
        """The open checkpoint is built and noted (or nothing is open), and nothing is running or starting."""
        if self.busy() or self.started_any or self.memo.verify:
            return False
        state = st.load(self.program)
        current = state.open_checkpoint()
        if current is None:
            return True
        from ship.status import checkpoint_line

        line = checkpoint_line(state) or ""
        return " built:" in line and self.program.stop_note(stop_name(self.program, current)).exists()

    # -- steps --

    def main_changed(self, lines: list[str]) -> bool:
        from ship.preflight import main_check

        if not self.program.main_snapshot.exists():
            return False
        try:
            ok, out = main_check(self.program, self.settings)
        except GitError as exc:
            lines.append(f"MAIN-CHECK could not run: {exc}")
            return False
        if ok:
            return False
        self.wait_line("the main checkout changed under a code root or HEAD; the build stopped",
                       "\n".join(out[1:21]))
        lines += out
        return True

    def power(self, lines: list[str]) -> bool:
        from ship import power_watch

        line = power_watch.step(self.program, self.settings, power_watch.on_mains(), time.time(),
                                lambda: power_watch.probe_network(self.program, self.settings))
        if line != "MAINS":
            lines.append(f"POWER {line}")
        return self.program.hold.exists()

    def build_branch_gone(self, state: st.State) -> str | None:
        try:
            tip = remote_sha(Path(state.repo), state.remote, state.build_branch, self.settings.net_timeout_s)
        except GitError:
            return None  # the remote did not answer: that is a HOLD, not a missing branch
        return None if tip else f"build branch `{state.build_branch}` is gone from the remote"

    def retry_recover(self) -> list[str]:
        """Seats a failed recover left held with no worker (the remote was down)."""
        from ship.recover import recover

        state = st.load(self.program)
        lines = []
        for sl in state.slices.values():
            if sl.status == Status.HELD and sl.id not in self.workers and sl.id not in self.memo.verify \
                    and not self._script_for(sl.id):
                try:
                    lines += recover(self.program, self.settings, only=sl.id)
                except GitError as exc:
                    lines.append(f"RECOVER {sl.id} unreachable: {exc}")
        return lines

    def route_workers(self) -> list[str]:
        lines = []
        for sid, worker in list(self.workers.items()):
            got = worker.handle.poll()
            if got is None:
                continue
            del self.workers[sid]
            lines.append(f"WORKER {worker.kind} {sid} ended: {got.kind} {got.line or got.note}".rstrip())
            lines += self.route_result(sid, worker, got)
        return lines

    def route_result(self, sid: str, worker: Worker, got: ln.Result) -> list[str]:
        from ship.recover import recover

        if got.kind == "ok" and got.contract == "READY":
            sha = got.value.split()[0]
            stamped = self.stamp(sid, sha)
            self.memo.verify[sid] = sha
            return [f"READY {sid} {got.value}"] + ([f"STAMPED {sid} {', '.join(stamped)}"] if stamped else [])
        if got.kind == "ok" and got.contract == "BLOCKED":
            return self.blocked(sid, got.value)
        if got.kind == "limit":
            try:
                out = recover(self.program, self.settings, usage_reset=got.limit_reset, only=sid)
            except GitError as exc:
                out = [f"RECOVER {sid} unreachable: {exc}"]
                with st.locked(self.program) as state:
                    state.usage_reset_at = got.limit_reset
            return out + [f"LIMIT {sid}: restarts after {got.limit_reset}"]
        # nocontract, crash, timeout, or a reply that is not a builder's (DONE, WAITS)
        return self.died(sid, worker, got.kind if got.kind != "ok" else f"replied {got.line!r}")

    def stamp(self, sid: str, sha: str) -> list[str]:
        """The END line on each required evidence file the builder wrote; the names stamped."""
        from ship.evidence import stamp

        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            return []  # verify_ready says what is wrong with the reply
        sl = st.load(self.program).slices[sid]
        if sl.holder is None:
            return []
        folder = self.program.evidence(sid, sl.attempts)
        return [name for name in self.settings.evidence_required
                if stamp(folder / name, sha, sl.holder.dispatch_id)]

    def died(self, sid: str, worker: Worker, why: str) -> list[str]:
        from ship.recover import recover

        lines = []
        try:
            lines += recover(self.program, self.settings, only=sid)
        except GitError as exc:
            return [f"RECOVER {sid} unreachable: {exc}; again next tick"]
        with st.locked(self.program) as state:  # a usage limit is not a death (D-L12)
            sl = state.slices[sid]
            sl.deaths += 1
            deaths = sl.deaths
            if deaths >= self.settings.max_restarts and sl.status in (Status.HELD, Status.DEAD):
                state.park(sid, ParkCause.MANUAL, f"its builder died {deaths} times, last {why}")
        if deaths < self.settings.max_restarts:
            return lines + [f"RESTART {sid} ({why}); death {deaths} of {self.settings.max_restarts}"]
        tail = last_lines(worker.handle.stdout)
        self.wait_line(f"{sid} parked: its builder died {deaths} times ({why}); last output in "
                       f"{worker.handle.stdout}", tail)
        return lines + [f"PARK {sid}: its builder died {deaths} times"]

    def blocked(self, sid: str, value: str) -> list[str]:
        word = value.split()[0] if value.split() else ""
        with st.locked(self.program) as state:
            if state.slices[sid].status == Status.HELD:
                state.park(sid, ParkCause.MANUAL, value)
        if word in ("chain", "files"):
            self.chain_issue(f"{sid} BLOCKED {value}")
            return [f"PARK {sid}: BLOCKED {value} (chain issue)"]
        self.wait_line(f"{sid} parked: its builder said BLOCKED {value}")
        return [f"PARK {sid}: BLOCKED {value}"]

    def route_scripts(self) -> list[str]:
        lines = []
        for script in list(self.scripts):
            rc = script.done()
            limit = self.script_limit(script.name)
            if rc is None and time.monotonic() - script.began > limit:
                kill_tree(script.proc.pid)
                try:
                    script.proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    pass
                self.scripts.remove(script)
                lines.append(f"SCRIPT {script.name} {script.slice} killed after {limit:.0f}s; again next tick")
                continue  # a killed script leaves state.json as it was, so the next tick starts it again
            if rc is None:
                continue
            self.scripts.remove(script)
            out = script.output()
            lines.append(f"SCRIPT {script.name} {script.slice} exit {rc}".replace("  ", " "))
            if script.name == "verify_ready":
                lines += self.after_verify(script.slice, rc, out)
            elif script.name == "slice_checks":
                lines += self.after_checks(script.slice, rc)
            elif script.name == "land":
                lines += self.after_land(script, rc, out)
        return lines

    def script_limit(self, name: str) -> float:
        s = self.settings
        return {"verify_ready": s.verify_timeout_s, "slice_checks": s.slice_checks_timeout_s,
                "land": s.land_run_timeout_s}.get(name, s.land_run_timeout_s)

    def after_verify(self, sid: str, rc: int, out: list[str]) -> list[str]:
        if rc in (0, 1):
            self.memo.verify.pop(sid, None)
        if rc == 0:
            self.memo.fixing.pop(sid, None)  # the fix round is over
        if rc == 1:
            self.memo.fix[sid] = {"reason": "verify_ready: " + "; ".join(out[-10:]), "paths": []}
            return [f"RED {sid} at verify_ready: fix round"]
        if rc == 0:
            return [f"VERIFIED {sid}"]
        return [f"VERIFY {sid} again next tick (exit {rc})"]

    def after_checks(self, sid: str, rc: int) -> list[str]:
        sl = st.load(self.program).slices[sid]
        if sl.status == Status.RED:
            summary = self.program.checks(sid, sl.head or "x") / "summary.txt"
            self.memo.fix[sid] = {"reason": sl.reason, "paths": [str(summary)]}
            return [f"RED {sid} at slice_checks: fix round with {summary}"]
        if sl.status == Status.CHECKED:
            return [f"CHECKED {sid}"]
        return [f"CHECKS {sid} again next tick (exit {rc}, still {sl.status})"]

    def after_land(self, script: Script, rc: int, out: list[str]) -> list[str]:
        lines = [f"LAND {line}" for line in out if line.split(" ", 1)[0] in ("PASS", "FAIL", "HELD", "RECHECK", "SKIP",
                                                                             "NOTE")]
        if rc not in (0, 1) or any(x.startswith("Traceback (most recent call last)") for x in out):
            self.memo.land_crashes += 1  # F9 (D-L26): a land that crashes is a restart, counted
            n = self.memo.land_crashes
            if n >= self.settings.max_restarts:
                self.wait_line(f"land crashed {n} times in a row; the build stopped",
                               f"{script.log}\n" + "\n".join(out[-15:]))
                self.memo.land_crashes = 0
                self.exit = 10
            return lines + [f"LAND crashed ({n} of {self.settings.max_restarts}); see {script.log}"]
        self.memo.land_crashes = 0
        for line in out:
            batch = LAND_TESTS.match(line)
            if batch:
                ids = [x.strip().strip("'\"") for x in batch.group(2).split(",") if x.strip()]
                summary = self.program.landing(batch.group(1)) / "summary.txt"
                if len(ids) >= 2:
                    self.memo.singles = ids
                    lines.append(f"SINGLES {ids}: landing one at a time")
                else:
                    for sid in ids:
                        self.memo.fix[sid] = {"reason": f"land: tests red in batch {batch.group(1)}",
                                              "paths": [str(summary)]}
                        lines.append(f"RED {sid} at land: fix round with {summary}")
                continue
            one = LAND_ONE.match(line)
            if one:
                sid = one.group(1)
                state = st.load(self.program)
                if sid in state.slices and state.slices[sid].status == Status.RED:
                    summary = self.program.checks_root / "_land"
                    self.memo.fix[sid] = {"reason": f"land: {one.group(2)}", "paths": [str(summary)]}
        for sid in script.args:  # a lone landing is done, whatever it printed
            if sid in self.memo.singles:
                self.memo.singles.remove(sid)
        return lines

    def check_status(self, lines: list[str]) -> bool:
        from ship.recover import recover
        from ship.status import status

        try:
            ok, out = status(self.program, self.settings)  # liveness compares real file times, never the test clock
        except GitError as exc:
            lines.append(f"STATUS could not run: {exc}")
            return False
        for line in out:
            if line.startswith("BREAKER"):
                self.wait_line(f"the breaker tripped: {line}")
                lines.append(line)
                return True
            if line.startswith("STALE "):
                sid = line.split()[1]
                worker = self.workers.pop(sid, None)
                if worker is None:
                    continue  # no builder of ours runs: the seat is between steps, not stuck
                worker.handle.kill()
                lines.append(line)
                lines += self.died(sid, worker, "stale")
        return False

    def _script_for(self, sid: str) -> Script | None:
        return next((s for s in self.scripts if s.slice == sid), None)

    def start_script(self, name: str, sid: str, *args: str) -> Script:
        logs = self.program.checks_root / "_run"
        logs.mkdir(parents=True, exist_ok=True)
        stamp = clock.now().strftime("%Y%m%dT%H%M%S") + f"-{time.monotonic_ns() % 10**6:06d}"
        log = logs / f"{stamp}-{name}{'-' + sid if sid else ''}.log"
        argv = [sys.executable, str(ln.KIT), name, "--program", str(self.program.dir), *args]
        with open(log, "w", encoding="utf-8", newline="\n") as out:
            proc = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=out, stderr=subprocess.STDOUT,
                                    **popen_group_kwargs())
        script = Script(name, sid, proc, log, clock.now().isoformat(timespec="seconds"),
                        tuple(a for a in args if name == "land"), proc_created(proc.pid))
        self.scripts.append(script)
        self.started_any = True
        return script

    def start_scripts(self) -> list[str]:
        lines = []
        if self.program.hold.exists():  # read again: a HOLD written during this tick starts nothing (D-L25)
            return ["HOLD: no verify_ready, slice_checks or land starts"]
        state = st.load(self.program)
        for sid, sha in list(self.memo.verify.items()):
            if not self._script_for(sid) and sid not in self.workers:
                if state.slices[sid].status != Status.HELD:
                    self.memo.verify.pop(sid)
                    continue
                self.start_script("verify_ready", sid, sid, sha)
                lines.append(f"START verify_ready {sid} {sha[:8]}")
        for sl in state.slices.values():
            if sl.status == Status.READY and not self._script_for(sl.id):
                self.start_script("slice_checks", sl.id, sl.id)
                lines.append(f"START slice_checks {sl.id}")
        if not any(s.name == "land" for s in self.scripts):
            checked = [s.id for s in state.slices.values() if s.status == Status.CHECKED and state.ahead(s.id) <= 0
                       and s.id not in self.memo.fix and not self._script_for(s.id)]
            self.memo.singles = [x for x in self.memo.singles if x in checked]
            target = self.memo.singles[:1] or checked
            if target:
                self.start_script("land", "", *target)
                self.memo.lands += 1
                lines.append(f"START land {' '.join(target)}")
                self._maybe_stop("land", self.memo.lands)
        return lines

    def _maybe_stop(self, what: str, n: int) -> None:
        """SHIP_RUN_STOP_AFTER=<what>:<n> exits hard right after the n-th start of <what> (tests kill a run)."""
        want = os.environ.get("SHIP_RUN_STOP_AFTER", "")
        if want == f"{what}:{n}":
            self.memo.save(self.memo_path)
            if self.lock:
                self.lock.refresh(self.children())
            os._exit(137)

    def fill_seats(self) -> list[str]:
        from ship import locks
        from ship import project_profile as profile
        from ship.dispatch import Parked, Refused, dispatch

        state = st.load(self.program)
        order = self.seat_order(state)
        pool = locks.Pool(self.settings, profile.of_program(self.program.dir, self.settings)["pool"]["workers"])
        lines = []
        for sid in order:
            if sid in self.workers or self._script_for(sid) or sid in self.memo.verify:
                continue
            fix = self.memo.fix.get(sid)
            slot = pool.take()
            if slot is None:
                lines.append(f"POOL every worker seat on this machine is taken; {sid} waits")
                break
            try:
                got = dispatch(self.program, sid, self.settings)
            except Refused as exc:
                slot.release()
                if "no free seat" in str(exc):
                    break
                lines.append(f"SKIP {sid}: {exc}")
                continue
            except GitError as exc:
                slot.release()
                lines.append(f"SKIP {sid}: remote unreachable ({exc})")
                continue
            self.started_any = True
            if isinstance(got, Parked):
                slot.release()
                self.memo.fix.pop(sid, None)
                lines.append(f"PARK {sid}: {got.reason}")
                if got.reason.startswith("brief-mismatch"):
                    self.wait_line(f"{sid} parked: {got.reason}")
                elif got.reason.startswith("restarted"):
                    self.wait_line(f"{sid} parked: {got.reason}")
                continue
            self.memo.fix.pop(sid, None)
            failed = [x for x in got.setup if x.startswith("FAIL ")]
            if failed:  # D-L25: no worker starts in a worktree whose setup failed
                slot.release()
                lines += [f"SETUP {sid} {x}" for x in failed] + self.setup_failed(got, fix, failed)
                continue
            self.memo.setup_fails.pop(sid, None)
            lines.append(self.start_worker(got, fix, slot))
        return lines

    def setup_failed(self, got, fix: dict | None, failed: list[str]) -> list[str]:
        """The seat goes back (recovered as dead: a restart, never a death); the next tick tries again; the
        `max_restarts`-th failed setup in a row parks the slice for him."""
        from ship.recover import recover

        sid = got.slice
        if got.kind == "fix":  # the fix round it was given carries over to the retry
            self.memo.fixing[sid] = {"reason": (fix or {}).get("reason") or st.load(self.program).slices[sid].reason,
                                     "paths": list((fix or {}).get("paths") or [])}
        n = self.memo.setup_fails.get(sid, 0) + 1
        self.memo.setup_fails[sid] = n
        try:
            lines = recover(self.program, self.settings, only=sid)
        except GitError as exc:
            lines = [f"RECOVER {sid} unreachable: {exc}; again next tick"]
        if n < self.settings.max_restarts:
            return lines + [f"SETUP-FAILED {sid}: no worker started; tried again next tick ({n} of "
                            f"{self.settings.max_restarts})"]
        with st.locked(self.program) as state:
            if state.slices[sid].status in (Status.HELD, Status.DEAD):
                state.park(sid, ParkCause.MANUAL, f"its worktree setup failed {n} times")
        self.memo.setup_fails.pop(sid, None)
        self.wait_line(f"{sid} parked: its worktree setup failed {n} times; see "
                       f"{self.program.checks_root / '_setup' / sid}", "\n".join(failed))
        return lines + [f"PARK {sid}: its worktree setup failed {n} times"]

    def seat_order(self, state: st.State) -> list[str]:
        """Dead slices, slices due a fix round, then pending slices lane by lane, then pre-builds."""
        lanes = slice_lanes(self.program)
        dead = [s.id for s in state.slices.values() if s.status == Status.DEAD]
        fixes = [s.id for s in state.slices.values()
                 if s.status == Status.RED or (s.id in self.memo.fix and s.status in (Status.CHECKED, Status.READY))]
        pending = [s.id for s in state.slices.values() if s.status == Status.PENDING and s.id not in self.claim_blocked]
        now = [sid for sid in pending if state.ahead(sid) <= 0]
        early = [sid for sid in pending if state.ahead(sid) == 1]
        return dead + fixes + by_lane(now, lanes) + by_lane(early, lanes)

    def start_worker(self, got, fix: dict | None, slot=None) -> str:
        leftover_line = (f"The previous holder's unpushed changes are saved in `{got.leftover}`; reapply only what "
                         f"still fits, with `git -C {got.worktree} apply`." if got.leftover else "Nothing was left over.")
        state = st.load(self.program)
        if got.kind == "fix":  # a new fix round: what it fixes is kept until verify_ready passes
            self.memo.fixing[got.slice] = {"reason": (fix or {}).get("reason") or state.slices[got.slice].reason,
                                           "paths": list((fix or {}).get("paths") or [])}
        # a restart of a fix round (attempt 2 and up) is a fixer again, with the same reason and paths
        fixing = self.memo.fixing.get(got.slice) if got.kind == "fix" or got.attempt > 1 else None
        kind = "fixer" if got.kind == "fix" or fixing is not None else "builder"
        values = {"SLICE": got.slice, "PROGRAM": str(self.program.dir), "WORKTREE": got.worktree,
                  "WORKTREE_ROOT": state.worktree_root, "BRANCH": got.branch, "PARENT": got.parent,
                  "EVIDENCE": got.evidence, "DISPATCH_ID": got.dispatch_id, "KIND": got.kind,
                  "ATTEMPT": str(got.attempt), "RESTART": str(got.restart), "LEFTOVER": got.leftover or "",
                  "LEFTOVER_LINE": leftover_line, "RESTART_OF": "first" if got.attempt == 1 else "fix",
                  "FIX_REASON": (fixing or {}).get("reason") or "", "SHIP": str(ln.KIT),
                  "FIX_PATHS": ", ".join((fixing or {}).get("paths") or []), **self.project_values()}
        prompt = render(self.prompt, values)
        env = {"SHIP_SLICE": got.slice, "SHIP_EVIDENCE": got.evidence, "SHIP_DISPATCH_ID": got.dispatch_id}
        handle = ln.launch(self.roles[kind], prompt, Path(got.worktree), self.program, got.dispatch_id,
                           self.settings, extra_env=env, label=got.slice, slot=slot)
        if handle is None:  # only a Fable builder could get here: its seat is taken; the seat is recovered
            return f"WAIT {got.slice}: its worker could not start (the Fable seat is taken); restarts next tick"
        self.workers[got.slice] = Worker(got.slice, kind, handle)
        return f"START {kind} {got.slice} {got.kind} {got.dispatch_id} pid {handle.pid}"

    def stop_note(self) -> list[str]:
        from ship.status import checkpoint_line

        state = st.load(self.program)
        current = state.open_checkpoint()
        if current is None or " built:" not in (checkpoint_line(state) or ""):
            return []
        name = stop_name(self.program, current)
        note = self.program.stop_note(name)
        if note.exists():
            return []
        try:
            tip = remote_sha(Path(state.repo), state.remote, state.build_branch, self.settings.net_timeout_s)
        except GitError:
            return []
        mine = [s for s in state.slices.values() if s.checkpoint == current]
        body = {"stop": name, "from": self.stop_from(state, name, mine), "tip": tip,
                "landed": [s.id for s in mine if s.status == Status.LANDED],
                "parked": [s.id for s in mine if s.status in (Status.PARKED, Status.BLOCKED_BY)],
                "at": clock.now().isoformat(timespec="seconds")}
        note.parent.mkdir(parents=True, exist_ok=True)
        note.write_text(json.dumps(body, indent=2) + "\n", "utf-8", newline="\n")
        return [f"BUILT stop {name} at {tip}: notes/{note.name}"]

    def stop_from(self, state: st.State, name: str, mine: list[st.Slice]) -> str:
        """`parent_tip` for the first stop, else the previous stop's reviewed tip (11.2). With no
        PROGRAM.yaml, the parent of the checkpoint's first slice to land."""
        if self.program.project_file.exists():
            from ship import phase
            from ship import program as prog

            try:
                index = prog.load(self.program)
            except prog.ProgramError:
                index = None
            if index is not None:
                previous = index.parent_tip or ""
                for stop in index.stops:
                    if stop.id == name:
                        return previous
                    previous = phase._reviewed_tip(self.program, stop.id) or previous
                return previous
        landed = {e["slice"]: n for n, e in enumerate(state.events)
                  if e.get("kind") == "status" and e.get("to") == Status.LANDED}
        first = sorted((s for s in mine if s.id in landed), key=lambda s: landed[s.id])
        return first[0].parent or "" if first else ""


def stop_name(program: Program, checkpoint: str) -> str:
    """The stop a checkpoint's note is named for: its SLICES.md `stop`, else PROGRAM.yaml's first stop, else A."""
    if checkpoint:
        return checkpoint
    from ship import program as prog

    try:
        stops = prog.load(program).stops if program.project_file.exists() else []
    except prog.ProgramError:
        stops = []
    return stops[0].id if stops else "A"


def last_lines(path: Path, n: int = 20) -> str:
    try:
        lines = path.read_text("utf-8", errors="replace").splitlines()
        return "\n".join(lines[-n:])
    except OSError:
        return ""


def slice_lanes(program: Program) -> dict[str, str]:
    """SLICES.md's `lane` column, when it has one."""
    try:
        lines = program.slices_md.read_text("utf-8").splitlines()
    except OSError:
        return {}
    for i, line in enumerate(lines):
        cells = [c.strip().casefold() for c in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("|") and "id" in cells and "lane" in cells:
            at_id, at_lane = cells.index("id"), cells.index("lane")
            lanes = {}
            for row in lines[i + 2:]:
                if not row.lstrip().startswith("|"):
                    break
                parts = [c.strip().strip("`") for c in row.strip().strip("|").split("|")]
                if len(parts) > max(at_id, at_lane):
                    lanes[parts[at_id]] = parts[at_lane]
            return lanes
    return {}


def by_lane(ids: list[str], lanes: dict[str, str]) -> list[str]:
    """Take one slice from each lane in turn, so slices of different lanes run at once."""
    groups: dict[str, list[str]] = {}
    for sid in ids:
        groups.setdefault(lanes.get(sid, ""), []).append(sid)
    out = []
    while any(groups.values()):
        for key in sorted(groups):
            if groups[key]:
                out.append(groups[key].pop(0))
    return out


def run(program: Program, settings: Settings, once: bool = False, poll_s: float | None = None) -> int:
    """The loop. `once`: one tick that may start work, then only routing until nothing runs."""
    lock = ChainLock(program, "build")
    if not lock.acquire():
        print(f"LOCKED chain.lock is held by pid {lock.read().get('pid')}")
        return 11
    build = Build(program, settings, lock, once=once)
    try:
        for line in build.start():
            print(line, flush=True)
        if build.exit is not None:
            return build.exit
        period = settings.chain_poll_s if poll_s is None else poll_s
        while True:
            for line in build.tick(clock.now()):
                print(line, flush=True)
            if build.exit is not None:
                build.stop_children()
                return build.exit
            if build.done() or (once and not build.busy() and not build.started_any):
                return 0
            time.sleep(period)
    finally:
        build.stop_children()
        lock.release()
