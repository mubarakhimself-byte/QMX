"""The launcher shim, DESIGN open questions 17 and 18. `p_shim.py [build|version|jobs|turn]`.

`build` installs this file and the probe modules it imports as a uv console script,
`qma-cli-launcher.exe`, into the probe venv. The `.exe` runs `shim_main`, which appends one
record per start to `SCRATCH/shim-starts/` and then runs the bundled CLI with the same args.
The `version`, `jobs` and `turn` cases drive it and write `hp0-shim.log`. Only `turn` needs
the plan login.
"""

from __future__ import annotations

import ast
import asyncio
import ctypes
import json
import os
import shutil
import subprocess
import sys
import time
from ctypes import wintypes
from importlib.util import find_spec
from pathlib import Path
from typing import Any

from common import (
    PROBE_VENV,
    SCRATCH,
    Log,
    bundled_cli,
    describe,
    home_env,
    memory_mb,
    plan_options,
    reduced_env,
    require_plan_login,
    scrub_process_env,
    uv_env,
)

STARTS = SCRATCH / "shim-starts"
SHIM_EXE = PROBE_VENV / "Scripts" / "qma-cli-launcher.exe"
PACKAGE = SCRATCH / "shim-pkg"
NO_INPUT_SWITCH = "HP0_SHIM_NO_INPUT"
PARENT_JOB = "Local\\qma-hp0-parent-job"
VERSION_PROBE_BUDGET_S = 2.0
THROWAWAY = {"CLAUDE_CONFIG_DIR": str(SCRATCH / "config")}
"""The login-free cases never start a CLI in the ship home."""
PYPROJECT = """\
[project]
name = "qma-hp0-shim"
version = "0"
requires-python = ">=3.14"

[project.scripts]
qma-cli-launcher = "p_shim:shim_main"

[build-system]
requires = ["setuptools>=75"]
build-backend = "setuptools.build_meta"

[tool.setuptools]
py-modules = {modules}
"""

JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS = 9
JOB_OBJECT_ASSIGN_PROCESS = 0x0001
JOB_OBJECT_SET_ATTRIBUTES = 0x0002
JOB_OBJECT_QUERY = 0x0004
CREATE_SUSPENDED = 0x00000004
CREATE_BREAKAWAY_FROM_JOB = 0x01000000


class _BasicLimits(ctypes.Structure):
    _fields_ = (
        ("PerProcessUserTimeLimit", ctypes.c_int64),
        ("PerJobUserTimeLimit", ctypes.c_int64),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    )


class _ExtendedLimits(ctypes.Structure):
    _fields_ = (
        ("BasicLimitInformation", _BasicLimits),
        ("IoInfo", ctypes.c_uint64 * 6),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    )


def _kernel32() -> Any:
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.OpenJobObjectW.restype = wintypes.HANDLE
    kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    kernel32.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    kernel32.SetInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    )
    kernel32.IsProcessInJob.argtypes = (
        wintypes.HANDLE,
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.BOOL),
    )
    return kernel32


def kill_on_close_job(name: str | None) -> int:
    """A new job with kill-on-close. Returns its handle; the job dies with the last handle."""
    kernel32 = _kernel32()
    job = kernel32.CreateJobObjectW(None, name)
    if not job:
        raise OSError(ctypes.get_last_error(), "CreateJobObjectW")
    limits = _ExtendedLimits()
    limits.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    if not kernel32.SetInformationJobObject(
        job,
        JOB_OBJECT_EXTENDED_LIMIT_INFORMATION_CLASS,
        ctypes.byref(limits),
        ctypes.sizeof(limits),
    ):
        raise OSError(ctypes.get_last_error(), "SetInformationJobObject")
    return int(job)


def in_job() -> bool:
    kernel32 = _kernel32()
    result = wintypes.BOOL()
    kernel32.IsProcessInJob(kernel32.GetCurrentProcess(), None, ctypes.byref(result))
    return bool(result.value)


def join_jobs(parent_name: str, process: int) -> dict[str, Any]:
    kernel32 = _kernel32()
    access = JOB_OBJECT_ASSIGN_PROCESS | JOB_OBJECT_SET_ATTRIBUTES | JOB_OBJECT_QUERY
    parent = kernel32.OpenJobObjectW(access, False, parent_name)
    record: dict[str, Any] = {"open_parent": bool(parent)}
    joined = bool(parent) and bool(kernel32.AssignProcessToJobObject(parent, process))
    record |= {"join_parent": joined, "join_parent_error": 0 if joined else ctypes.get_last_error()}
    try:
        nested = kill_on_close_job(None)
    except OSError as error:
        return record | {"join_nested": False, "join_nested_error": error.errno}
    joined = bool(kernel32.AssignProcessToJobObject(nested, process))
    return record | {
        "join_nested": joined,
        "join_nested_error": 0 if joined else ctypes.get_last_error(),
    }


def run_breakaway(cli: str, args: list[str], parent_name: str) -> tuple[int, dict[str, Any]]:
    """The first OQ18 fallback: start the CLI out of the trampoline job, suspended, put it in
    the parent and a nested job, then resume it."""
    try:
        child = subprocess.Popen(
            [cli, *args], creationflags=CREATE_BREAKAWAY_FROM_JOB | CREATE_SUSPENDED
        )
    except OSError as error:
        return 1, {"breakaway_start": False, "breakaway_error": error.winerror}
    handle = int(vars(child)["_handle"])
    record = {"breakaway_start": True} | join_jobs(parent_name, handle)
    ctypes.WinDLL("ntdll").NtResumeProcess(wintypes.HANDLE(handle))
    return child.wait(), record


def find_bundled_cli() -> str | None:
    """The no-input mode. `find_spec` skips importing the SDK, which the 2 s budget needs."""
    spec = find_spec("claude_agent_sdk")
    if spec is None or spec.origin is None:
        return None
    exe = Path(spec.origin).parent / "_bundled" / "claude.exe"
    return str(exe) if exe.exists() else None


def shim_main() -> int:
    """The `qma-cli-launcher.exe` entry point."""
    args = sys.argv[1:]
    record: dict[str, Any] = {
        "pid": os.getpid(),
        "args": args[:3] + ([f"... {len(args)} args"] if len(args) > 3 else []),
        "qma_names": sorted(name for name in os.environ if name.upper().startswith("QMA_")),
        "in_job_at_start": in_job(),
        "python_working_set_mb": memory_mb(os.getpid()).working_set,
    }
    job_name = os.environ.get("QMA_JOB_NAME")
    breakaway = os.environ.get("QMA_JOB_MODE") == "breakaway"
    if job_name and not breakaway:
        record |= join_jobs(job_name, _kernel32().GetCurrentProcess())
    cli = os.environ.get("QMA_CLI_PATH")
    if cli is None and args == ["-v"] and os.environ.get(NO_INPUT_SWITCH):
        cli = find_bundled_cli()
        record["mode"] = "no-input"
    record["cli_found"] = cli is not None
    if cli is None:
        _append_start(record)
        print("qma-cli-launcher: no QMA_CLI_PATH, cannot find the CLI", file=sys.stderr)
        return 2
    if job_name and breakaway:
        code, joined = run_breakaway(cli, args, job_name)
        _append_start(record | joined)
        return code
    _append_start(record)
    return subprocess.run([cli, *args], check=False).returncode


def _append_start(record: dict[str, Any]) -> None:
    """One file per start, so two shims starting at once cannot overwrite each other."""
    STARTS.mkdir(parents=True, exist_ok=True)
    (STARTS / f"{time.time_ns()}-{os.getpid()}.json").write_text(json.dumps(record))


def read_starts() -> list[dict[str, Any]]:
    if not STARTS.exists():
        return []
    return [json.loads(path.read_text()) for path in sorted(STARTS.glob("*.json"))]


def clear_starts() -> None:
    for path in STARTS.glob("*.json"):
        path.unlink()


def app_control_events(log: Log) -> None:
    """The last Code Integrity events, read only, after a start that Windows refused."""
    command = (
        "Get-WinEvent -LogName 'Microsoft-Windows-CodeIntegrity/Operational' -MaxEvents 3 "
        "| Format-List TimeCreated,Id,Message"
    )
    powershell = shutil.which("powershell") or "powershell"
    done = subprocess.run(
        [powershell, "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    log(f"App Control events: {done.stdout.strip()[:1500]}")


def local_modules(root: str, here: Path) -> list[str]:
    found: set[str] = set()
    pending = [root]
    while pending:
        name = pending.pop()
        if name in found or not (here / f"{name}.py").exists():
            continue
        found.add(name)
        tree = ast.parse((here / f"{name}.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                pending += [alias.name.partition(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                pending.append(node.module.partition(".")[0])
    return sorted(found)


def stage(package: Path) -> None:
    package.mkdir(parents=True, exist_ok=True)
    here = Path(__file__).parent
    modules = local_modules("p_shim", here)
    for name in modules:
        shutil.copy2(here / f"{name}.py", package / f"{name}.py")
    pyproject = PYPROJECT.format(modules=json.dumps(modules))
    (package / "pyproject.toml").write_text(pyproject, encoding="utf-8")


def build(log: Log) -> None:
    stage(PACKAGE)
    uv = shutil.which("uv")
    if uv is None:
        raise SystemExit("uv is not on PATH")
    python = PROBE_VENV / "Scripts" / "python.exe"
    env = uv_env()
    subprocess.run(
        [uv, "pip", "install", "--python", str(python), "--reinstall", str(PACKAGE)],
        env=env,
        check=True,
    )
    log(f"built {SHIM_EXE} exists={SHIM_EXE.exists()}")


def shim_env(**extra: str) -> dict[str, str]:
    return reduced_env(os.environ) | home_env() | THROWAWAY | extra


async def version(log: Log) -> None:
    """Connect through the shim twice, without a turn, and record each version-probe start."""
    from claude_agent_sdk import ClaudeSDKClient  # noqa: PLC0415

    options = plan_options(
        cli_path=str(SHIM_EXE),
        env=home_env() | THROWAWAY | {"QMA_CLI_PATH": str(bundled_cli()), "QMA_CHAT_ID": "hp0"},
    )
    first: dict[str, Any] = {}
    for attempt in ("cold", "warm"):
        clear_starts()
        try:
            async with ClaudeSDKClient(options=options):
                log(f"{attempt}: connected through the shim")
        except OSError as error:
            log(f"start refused: {error!r}")
            app_control_events(log)
            log.row("Shim start", repr(error)[:300], "FAIL")
            return
        starts = read_starts()
        for start in starts:
            log(f"{attempt}: start record: {json.dumps(start)}")
        probe = next((s for s in starts if s["args"] == ["-v"]), None)
        seen = (
            "no record: the SDK's 2 s budget ended the start before the shim logged"
            if probe is None
            else f"args={probe['args']} qma={probe['qma_names']} cli_found={probe['cli_found']}"
        )
        log.row(f"OQ17 {attempt} version-probe start", seen, "RECORDED")
        first = first or (probe or {})

    began = time.monotonic()
    done = subprocess.run(
        [str(SHIM_EXE), "-v"],
        env=shim_env(**{NO_INPUT_SWITCH: "1"}),
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    took = round(time.monotonic() - began, 2)
    printed = done.stdout.strip()
    works = bool(printed) and took < VERSION_PROBE_BUDGET_S
    log(f"no-input mode: printed={printed!r} took={took}s rc={done.returncode}")
    verdict = "PASS" if works else "FAIL"
    log.row(
        "OQ17 no-input mode answers -v inside the SDK's 2 s budget",
        f"{printed!r} in {took}s",
        verdict,
    )
    if first.get("cli_found"):
        path = "none needed"
    elif works:
        path = "no-input mode"
    else:
        path = "CLAUDE_AGENT_SDK_SKIP_VERSION_CHECK=1 after the scrub, doctor checks the floor"
    log.row("OQ17 path HP4 takes", path, "RECORDED")


def jobs(log: Log) -> None:
    joins = {mode: two_shims(log, mode) for mode in ("join", "breakaway")}
    path = next(
        (mode for mode, joined in joins.items() if len(joined) == 2 and all(joined)),
        "neither; bring the operator the native launcher choice",
    )
    names = {"join": "sketch path", "breakaway": "breakaway, suspended, assign to nested jobs"}
    log.row("OQ18 path HP4 takes", names.get(path, path), "RECORDED")


def two_shims(log: Log, mode: str) -> list[bool]:
    """Start two shims at once in `mode` under a fresh parent job. Returns, per shim, whether
    both job joins held."""
    clear_starts()
    name = f"{PARENT_JOB}-{mode}"
    parent = kill_on_close_job(name)
    log(f"{mode}: parent holds named job {name} with kill-on-close, handle {parent}")
    env = shim_env(QMA_JOB_NAME=name, QMA_JOB_MODE=mode, QMA_CLI_PATH=str(bundled_cli()))
    try:
        shims = [
            subprocess.Popen(
                [str(SHIM_EXE), "--version"], env=env, stdout=subprocess.PIPE, text=True
            )
            for _ in range(2)
        ]
    except OSError as error:
        log(f"start refused: {error!r}")
        app_control_events(log)
        log.row("OQ18 shim start", repr(error)[:300], "FAIL")
        return []
    for shim in shims:
        out, _ = shim.communicate(timeout=120)
        log(f"{mode}: shim rc={shim.returncode} stdout={out.strip()!r}")
    starts = read_starts()
    for start in starts:
        log(f"{mode}: start record: {json.dumps(start)}")
    joined = [bool(s.get("join_parent") and s.get("join_nested")) for s in starts]
    both = len(joined) == 2 and all(joined)
    in_job_now = [s.get("in_job_at_start") for s in starts]
    sizes = [s.get("python_working_set_mb") for s in starts]
    log.row(f"OQ18 {mode}: IsProcessInJob in the shim's Python child", in_job_now, "RECORDED")
    log.row(
        f"OQ18 {mode}: both shims in the parent and a nested job",
        joined,
        "PASS" if both else "FAIL",
    )
    log.row(f"OQ18 {mode}: shim Python process working set", f"{sizes} MB", "RECORDED")
    return joined


async def turn(log: Log) -> None:
    from claude_agent_sdk import ClaudeSDKClient, ResultMessage  # noqa: PLC0415

    require_plan_login(log, bundled_cli())
    options = plan_options(
        cli_path=str(SHIM_EXE), env=home_env() | {"QMA_CLI_PATH": str(bundled_cli())}
    )
    ok = False
    clear_starts()
    try:
        async with ClaudeSDKClient(options=options) as client:
            await client.query("say ok")
            async for message in client.receive_response():
                log(describe(message))
                if isinstance(message, ResultMessage):
                    ok = not message.is_error
    except OSError as error:
        log(f"start refused: {error!r}")
        app_control_events(log)
    for start in read_starts():
        log(f"turn start record: {start}")
    log.row("Shim turn through cli_path, App Control result", f"ok={ok}", "PASS" if ok else "FAIL")


async def main() -> int:
    log = Log("hp0-shim")
    scrub_process_env(os.environ)
    for name in sys.argv[1:] or ["build", "version", "jobs", "turn"]:
        if name == "build":
            build(log)
        elif name == "version":
            await version(log)
        elif name == "jobs":
            jobs(log)
        elif name == "turn":
            await turn(log)
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
