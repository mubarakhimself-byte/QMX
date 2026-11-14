"""launch: start one headless Claude Code run (a worker) and read what it returns.

The command line is built here and nowhere else (FACTORY-DESIGN section 11.3). Every start names its
model and effort, passes the role's settings file (the write-guard hook and the allow-list load every
time), refuses every permission prompt, switches the Agent tool off unless the role needs it, and
never uses `--bare` (the run keeps the plan login) or `bypassPermissions`.

Each run has a folder `<program>/workers/<worker id>/` holding `prompt.md`, `stdout.log`,
`stderr.log` and, once it ends, `result.json`. The reply contract is the last non-blank line of the
final text: `READY <sha>`, `BLOCKED ...`, `DONE <path>` or `WAITS <path>`. The JSON shape the parser
follows is recorded by the spike in `roles/RESULT-SHAPE.md`.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import json
import os
import re
import subprocess
import time
import tomllib
import uuid
from pathlib import Path

from ship import clock
from ship.gitx import env_no_prompt
from ship.layout import Program
from ship.proc import created as proc_created
from ship.proc import kill_tree, popen_group_kwargs
from ship.settings import Settings

KIT = Path(__file__).resolve().parent
ROLES_DIR = KIT / "roles"
CONTRACT_WORDS = ("READY", "BLOCKED", "DONE", "WAITS")
KINDS = ("ok", "nocontract", "limit", "timeout", "crash")
DEPTH_VAR = "CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH"
# D-L11: the only variables a worker gets from the parent. Everything else (API keys, the parent
# session's CLAUDE* and ANTHROPIC* variables, tokens) is dropped.
ENV_KEEP = {"PATH", "SYSTEMROOT", "TEMP", "TMP", "TMPDIR", "USERPROFILE", "HOME", "APPDATA", "LOCALAPPDATA",
            "COMSPEC", "PATHEXT", "SYSTEMDRIVE", "WINDIR", "HOMEDRIVE", "HOMEPATH", "USERNAME", "PROGRAMDATA",
            "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMW6432", "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE",
            "OS", "LANG", "LC_ALL", "SHELL", "USER", "LOGNAME", "XDG_RUNTIME_DIR"}
ENV_KEEP_PREFIXES = ("GIT_", "UV_", "SHIP_")


@dataclasses.dataclass(frozen=True)
class Role:
    name: str
    model: str
    effort: str
    agent_tool: bool
    timeout_s: float
    settings_file: Path
    fallback: str | None = None


@dataclasses.dataclass
class Result:
    kind: str  # ok | nocontract | limit | timeout | crash
    rc: int | None = None
    text: str = ""  # the final text (`result`)
    contract: str | None = None  # READY | BLOCKED | DONE | WAITS
    value: str = ""  # the rest of the contract line
    session_id: str | None = None
    models: list[str] = dataclasses.field(default_factory=list)  # modelUsage keys
    fell_back: bool = False
    limit_reset: str | None = None  # ISO time the usage limit lifts
    denials: list[str] = dataclasses.field(default_factory=list)  # tools the run was refused
    note: str = ""  # FALLBACK <role> <model>, or why it is a crash

    @property
    def line(self) -> str:
        return f"{self.contract} {self.value}".strip() if self.contract else ""

    def tail(self, stdout: Path, n: int = 20) -> str:
        try:
            lines = stdout.read_text("utf-8", errors="replace").splitlines()
        except OSError:
            return ""
        return "\n".join(lines[-n:])


def factory_home(settings: Settings) -> Path:
    return Path(os.environ.get("FACTORY_HOME") or settings.factory_home)


def load_roles(settings: Settings, profile: dict | None = None) -> dict[str, Role]:
    """Roles from `roles/roles.toml`; a project profile's `[roles.<name>]` overrides model, effort, fallback."""
    raw = tomllib.loads((ROLES_DIR / "roles.toml").read_text("utf-8"))
    over = (profile or {}).get("roles", {})
    roles = {}
    for name, row in raw.items():
        row = {**row, **{k: v for k, v in over.get(name, {}).items() if k in ("model", "effort", "fallback")}}
        timeout = float(row["timeout_s"])
        if settings.worker_timeout_s > 0:
            timeout = min(timeout, float(settings.worker_timeout_s))
        roles[name] = Role(name, row["model"], row["effort"], bool(row["agent_tool"]), timeout,
                           ROLES_DIR / row["settings"], row.get("fallback"))
    return roles


def contract_line(text: str) -> tuple[str, str] | None:
    """The last non-blank line when it starts READY, BLOCKED, DONE or WAITS: (word, rest)."""
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        return None
    word, _, rest = lines[-1].strip("`* ").partition(" ")
    if word in CONTRACT_WORDS and rest.strip():
        return word, rest.strip()
    return None


def same_model(asked: str, got: str) -> bool:
    """`fable` names `claude-fable-5`; a full id names itself."""
    a, g = asked.casefold(), got.casefold()
    return a == g or a in g or g in a


EPOCH_AFTER_BAR = re.compile(r"\|\s*(\d{10})\b")
ISO_TIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(\.\d+)?(Z|[+-]\d{2}:?\d{2})?")


def limit_reset_of(text: str, settings: Settings) -> str:
    """When the limit lifts: an epoch after a `|` (`... usage limit reached|1763000000`), an ISO time in
    the text, or now plus limit_backoff_s."""
    epoch = EPOCH_AFTER_BAR.search(text)
    if epoch:
        return dt.datetime.fromtimestamp(int(epoch.group(1)), dt.timezone.utc).isoformat(timespec="seconds")
    iso = ISO_TIME.search(text)
    if iso:
        try:
            when = dt.datetime.fromisoformat(iso.group(0).replace("Z", "+00:00"))
            when = when if when.tzinfo else when.replace(tzinfo=dt.timezone.utc)
            return when.astimezone(dt.timezone.utc).isoformat(timespec="seconds")
        except ValueError:
            pass
    later = clock.now() + dt.timedelta(seconds=settings.limit_backoff_s)
    return later.isoformat(timespec="seconds")


def _says_limit(text: str, settings: Settings) -> bool:
    low = text.casefold()
    return any(p.casefold() in low for p in settings.limit_patterns)


def _json_object(text: str) -> dict | None:
    """The result object: the whole stdout, or failing that its last line."""
    for candidate in (text.strip(), (text.strip().splitlines() or [""])[-1]):
        try:
            data = json.loads(candidate)
        except ValueError:
            continue
        if isinstance(data, dict):
            return data
    return None


def parse_result(stdout_text: str, rc: int | None, settings: Settings | None = None,
                 role: Role | None = None, stderr_text: str = "") -> Result:
    """Read a run's stdout (`--output-format json`) into a Result, as roles/RESULT-SHAPE.md records it."""
    settings = settings or Settings()
    data = _json_object(stdout_text)
    if data is None:
        raw = stdout_text + "\n" + stderr_text
        if rc not in (0, None) and _says_limit(raw, settings):  # D-L12: the pattern alone is not a limit
            return Result("limit", rc, raw.strip()[-2000:], limit_reset=limit_reset_of(raw, settings))
        return Result("crash", rc, stdout_text.strip()[-2000:], note=f"exit {rc}, no JSON result")
    text = str(data.get("result") or "")
    got = Result("nocontract", rc, text, session_id=data.get("session_id"),
                 models=sorted((data.get("modelUsage") or {}).keys()),
                 denials=[str(d.get("tool_name", d)) if isinstance(d, dict) else str(d)
                          for d in data.get("permission_denials") or []])
    if role and role.fallback and got.models and not any(same_model(role.model, m) for m in got.models):
        used = next((m for m in got.models if same_model(role.fallback, m)), None)
        if used:
            got.fell_back, got.note = True, f"FALLBACK {role.name} {used}"
    line = contract_line(text)
    if line and rc == 0:
        got.kind, (got.contract, got.value) = "ok", line
    elif (data.get("is_error") or rc not in (0, None)) \
            and _says_limit(text + "\n" + str(data.get("api_error_status") or "") + "\n" + stderr_text, settings):
        got.kind, got.limit_reset = "limit", limit_reset_of(text, settings)
    elif rc not in (0, None):
        got.kind, got.note = "crash", got.note or f"exit {rc}"
    return got


def worker_env(role: Role, program: Program, settings: Settings, extra_env: dict[str, str] | None = None,
               base: dict[str, str] | None = None) -> dict[str, str]:
    """An allow-list of the parent's variables (D-L11) plus the no-prompt git env, the ship variables and
    the depth limit. Nothing else passes: no API key, and none of the parent session's CLAUDE* or
    ANTHROPIC* variables, so the run uses its own stored plan login. `worker_env_extra` names more
    variables to pass (tests: FAKE_CLAUDE_SCRIPT)."""
    keep = ENV_KEEP | {k.upper() for k in settings.worker_env_extra}
    env = {k: v for k, v in (os.environ if base is None else base).items()
           if k.upper() in keep or k.upper().startswith(ENV_KEEP_PREFIXES)}
    env = env_no_prompt(env)
    env.update({"SHIP_PROGRAM": str(program.dir), "SHIP_ROLE": role.name, "SHIP_KIT": str(KIT),
                DEPTH_VAR: "1" if role.agent_tool else "0"})
    env.update(extra_env or {})
    return env


def argv_for(role: Role, prompt: str, program: Program, session_id: str, name: str,
             settings: Settings) -> list[str]:
    argv = [*settings.claude, "-p", prompt, "--model", role.model, "--effort", role.effort,
            "--settings", str(role.settings_file), "--setting-sources", "project,local", "--strict-mcp-config",
            "--permission-mode", "dontAsk", "--permission-prompts", "none"]
    if not role.agent_tool:
        argv += ["--disallowedTools", "Agent"]
    argv += ["--add-dir", str(program.dir)]
    home = factory_home(settings)
    if home.is_dir():
        argv += ["--add-dir", str(home)]
    argv += ["--session-id", session_id, "--name", name]
    if role.fallback:
        argv += ["--fallback-model", role.fallback]
    argv += ["--output-format", "json"]
    return argv


class Handle:
    """One running worker. `poll()` returns None while it runs, then its Result (written to result.json)."""

    def __init__(self, role: Role, folder: Path, child: subprocess.Popen, session_id: str, name: str,
                 settings: Settings, files: tuple):
        self.role, self.folder, self.child = role, folder, child
        self.session_id, self.name, self.settings = session_id, name, settings
        self._files = files
        self._started = time.monotonic()
        self.created = proc_created(child.pid)  # with the pid, names this run exactly (chain.lock)
        self.result: Result | None = None
        self.held: list = []  # the pool slot and, for a Fable role, the Fable seat; released when it ends

    @property
    def pid(self) -> int:
        return self.child.pid

    @property
    def stdout(self) -> Path:
        return self.folder / "stdout.log"

    def kill(self) -> None:
        if self.child.poll() is None:
            kill_tree(self.child.pid)
            try:
                self.child.wait(timeout=30)
            except subprocess.TimeoutExpired:
                pass
        self._release()

    def _release(self) -> None:
        for lock in self.held:
            lock.release()
        self.held = []

    def poll(self) -> Result | None:
        if self.result is not None:
            return self.result
        rc = self.child.poll()
        if rc is None:
            if time.monotonic() - self._started < self.role.timeout_s:
                return None
            self.kill()
            self._close()
            return self._finish(Result("timeout", None, note=f"killed after {self.role.timeout_s:.0f}s",
                                       session_id=self.session_id))
        self._close()
        out = self.stdout.read_text("utf-8", errors="replace") if self.stdout.exists() else ""
        err = (self.folder / "stderr.log").read_text("utf-8", errors="replace") \
            if (self.folder / "stderr.log").exists() else ""
        got = parse_result(out, rc, self.settings, self.role, err)
        got.session_id = got.session_id or self.session_id
        return self._finish(got)

    def _close(self) -> None:
        for fh in self._files:
            try:
                fh.close()
            except OSError:
                pass

    def _finish(self, got: Result) -> Result:
        self.result = got
        self._release()
        record = {**dataclasses.asdict(got), "role": self.role.name, "name": self.name, "pid": self.pid,
                  "asked_model": self.role.model, "ended": clock.now().isoformat(timespec="seconds")}
        tmp = self.folder / "result.json.tmp"
        tmp.write_text(json.dumps(record, indent=2) + "\n", "utf-8", newline="\n")
        os.replace(tmp, self.folder / "result.json")
        return got


def launch(role: Role, prompt: str, cwd: Path, program: Program, worker_id: str, settings: Settings,
           extra_env: dict[str, str] | None = None, label: str | None = None, slot=None) -> Handle | None:
    """Start one worker. `label` (a slice id) names it in `--name "<role>: <program> <label>"`;
    without one the worker id does.

    It first takes a seat of the machine-wide worker pool (or uses `slot`, taken by the caller), and for
    a role whose model starts `fable` the one Fable seat (U38, FACTORY-DESIGN 11.6). When either is not
    free it starts nothing and returns None; the caller tries again next tick."""
    from ship import locks
    from ship import project_profile as profile

    if slot is None:
        slot = locks.Pool(settings, profile.of_program(program.dir, settings)["pool"]["workers"]).take()
        if slot is None:
            return None
    held = [slot]
    if role.model.casefold().startswith("fable"):
        seat = locks.fable_lock(settings)
        if not seat.try_take(program=program.dir.name, worker_id=worker_id):
            slot.release()
            return None
        held.append(seat)
    folder = program.workers / worker_id
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "prompt.md").write_text(prompt, "utf-8", newline="\n")
    (folder / "result.json").unlink(missing_ok=True)
    session_id = str(uuid.uuid4())
    name = f"{role.name}: {program.dir.name} {label or worker_id}"
    argv = argv_for(role, prompt, program, session_id, name, settings)
    out = open(folder / "stdout.log", "w", encoding="utf-8", newline="\n")
    err = open(folder / "stderr.log", "w", encoding="utf-8", newline="\n")
    try:
        child = subprocess.Popen(argv, cwd=cwd, env=worker_env(role, program, settings, extra_env),
                                 stdin=subprocess.DEVNULL, stdout=out, stderr=err, **popen_group_kwargs())
    except OSError as exc:
        out.close()
        err.close()
        for lock in held:
            lock.release()
        raise LaunchError(f"could not start {argv[0]}: {exc}") from exc
    for lock in held:
        lock.note_worker(child.pid)
    (folder / "started.json").write_text(json.dumps(
        {"pid": child.pid, "session": session_id, "name": name, "role": role.name, "cwd": str(cwd), "argv": argv,
         "started": clock.now().isoformat(timespec="seconds")}, indent=2) + "\n", "utf-8", newline="\n")
    handle = Handle(role, folder, child, session_id, name, settings, (out, err))
    handle.held = held
    return handle


class LaunchError(Exception):
    pass


def run(role: Role, prompt: str, cwd: Path, program: Program, worker_id: str, settings: Settings,
        extra_env: dict[str, str] | None = None, label: str | None = None, poll_s: float = 2.0) -> Result:
    """Launch (waiting for a free seat), then poll every `poll_s` seconds until the run ends."""
    while (handle := launch(role, prompt, cwd, program, worker_id, settings, extra_env, label)) is None:
        time.sleep(poll_s)
    while True:
        got = handle.poll()
        if got is not None:
            return got
        time.sleep(poll_s)


def detached_kwargs() -> dict:
    """Popen arguments for a process that must outlive the one that started it (`proc.detached_kwargs`)."""
    from ship.proc import detached_kwargs as kwargs

    return kwargs()
