"""The CLI launcher: puts one chat's CLI under the OS limits before the CLI runs.

Standard library only. Installed as the console script `qma-cli-launcher`, a real `.exe` on
Windows. The SDK passes it as `cli_path` and runs `qma-cli-launcher <cli args>`; the launcher
runs the real CLI with the same args, the same stdio and the same exit code.

Inputs come from the chat's launch environment and are removed before the CLI starts:
    QMA_REAL_CLI   the CLI path; the SDK's bundled CLI when empty
    QMA_CHAT_ID    the chat's session id
    QMA_PROC_DIR   where the pid file goes
    QMA_CAP        the Windows parent job name or the Linux slice name; empty for no cap

No-input mode. The SDK's version probe runs `[cli_path, "-v"]` with the process environment
only, so it carries no `QMA_*` input (HP0 OQ17). On `-v`, or with no chat id and no pid
directory, the launcher finds the bundled CLI and runs it with no job and no pid file.

Windows. A uv console-script `.exe` already holds this Python in its own job, and a second
launcher cannot join the parent job from there (HP0 OQ18, error 5). So the CLI starts
suspended and broken away from that job, is assigned to the parent job and then to a named
per-chat job with kill-on-close that only this launcher holds, and only then resumes. If the
launcher dies, the chat's tree dies. If the parent job's holder dies, every tree dies.

Linux. The CLI gets the parent-death signal and, when `QMA_CAP` names a slice, runs in a
per-chat `systemd-run --user --scope` under it. macOS. The CLI runs in its own process group,
killed when the launcher's parent exits. Neither has a memory cap without the slice.

Pid file: `<QMA_PROC_DIR>/<QMA_CHAT_ID>.json` holds the launcher pid, the CLI pid and the CLI's
start time, written before the CLI runs and removed when it exits. On Windows it is written
while the CLI is still suspended and outside every job, so the cap's watcher can name the CLI
when it joins the parent job, and `kill_orphans` finds a suspended CLI whose launcher died
before the chat job held it.

`qma-cli-launcher --qma-block-config-change` is the ConfigChange command hook. It writes the
reason to stderr and exits 2, which blocks the change. The SDK never passes that flag.
"""

from __future__ import annotations

import contextlib
import functools
import os
import signal
import subprocess
import sys
from importlib.util import find_spec
from typing import TYPE_CHECKING, Any, Final, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

BLOCK_CONFIG_CHANGE: Final = "--qma-block-config-change"
INPUT_NAMES: Final[tuple[str, ...]] = ("QMA_REAL_CLI", "QMA_CHAT_ID", "QMA_PROC_DIR", "QMA_CAP")
VERSION_ARGS: Final = ["-v"]
CHAT_ID_CHARS: Final = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")
CHAT_ID_MAX: Final = 128
EXIT_BLOCKED: Final = 2
EXIT_REFUSED: Final = 125
EXIT_NO_CLI: Final = 127
SYSTEMD_RUN: Final = "/usr/bin/systemd-run"

PROCESS_TERMINATE: Final = 0x0001
PROCESS_SET_QUOTA: Final = 0x0100
PROCESS_SUSPEND_RESUME: Final = 0x0800
PROCESS_QUERY_LIMITED_INFORMATION: Final = 0x1000
SYNCHRONIZE: Final = 0x00100000
JOB_OBJECT_ASSIGN_PROCESS: Final = 0x0001
JOB_OBJECT_SET_ATTRIBUTES: Final = 0x0002
JOB_OBJECT_QUERY: Final = 0x0004
JOB_OBJECT_TERMINATE: Final = 0x0008
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE: Final = 0x2000
JOB_OBJECT_LIMIT_JOB_MEMORY: Final = 0x0200
EXTENDED_LIMIT_INFORMATION: Final = 9
CREATE_SUSPENDED: Final = 0x00000004
CREATE_BREAKAWAY_FROM_JOB: Final = 0x01000000
ERROR_ACCESS_DENIED: Final = 5
ERROR_ALREADY_EXISTS: Final = 183
WAIT_TIMEOUT: Final = 0x102


class PidRecord(NamedTuple):
    launcher_pid: int
    cli_pid: int
    cli_started: str
    """An opaque start-time token; a reused pid has a different one."""


def pid_path(proc_dir: Path, chat_id: str) -> Path:
    return proc_dir / f"{chat_id}.json"


def read_pid_record(path: Path) -> PidRecord | None:
    import json

    try:
        raw: Any = json.loads(path.read_text(encoding="utf-8"))
        return PidRecord(int(raw["launcher_pid"]), int(raw["cli_pid"]), str(raw["cli_started"]))
    except OSError, ValueError, KeyError, TypeError:
        return None


def home_scope(proc_dir: Path) -> str:
    """Names one QMA home in OS object names. Job names are shared by the whole Windows session
    and systemd units by the whole user, so two homes with the same chat id must not meet."""
    import hashlib

    folder = os.path.normcase(str(proc_dir.resolve()))
    return hashlib.sha256(folder.encode()).hexdigest()[:16]


def chat_job_name(proc_dir: Path, chat_id: str) -> str:
    return f"Local\\qma-chat-{home_scope(proc_dir)}-{chat_id}"


def chat_unit_prefix(proc_dir: Path, chat_id: str) -> str:
    return f"qma-chat-{home_scope(proc_dir)}-{chat_id}"


def is_chat_id(chat: str) -> bool:
    return 0 < len(chat) <= CHAT_ID_MAX and set(chat) <= CHAT_ID_CHARS


@functools.cache
def kernel32() -> Any:
    import ctypes
    from ctypes import wintypes

    if sys.platform != "win32":
        raise RuntimeError("kernel32 exists only on Windows")
    k: Any = ctypes.WinDLL("kernel32", use_last_error=True)
    k.CreateJobObjectW.restype = wintypes.HANDLE
    k.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
    k.OpenJobObjectW.restype = wintypes.HANDLE
    k.OpenJobObjectW.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR)
    k.OpenProcess.restype = wintypes.HANDLE
    k.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    k.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
    k.SetInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
    )
    k.QueryInformationJobObject.argtypes = (
        wintypes.HANDLE,
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.DWORD,
        ctypes.c_void_p,
    )
    k.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
    k.CloseHandle.argtypes = (wintypes.HANDLE,)
    k.WaitForSingleObject.argtypes = (wintypes.HANDLE, wintypes.DWORD)
    k.WaitForSingleObject.restype = wintypes.DWORD
    k.GetProcessTimes.argtypes = (wintypes.HANDLE, *(ctypes.POINTER(ctypes.c_uint64),) * 4)
    return k


def win_check(ok: object, call: str) -> None:
    import ctypes

    if sys.platform == "win32" and not ok:
        raise ctypes.WinError(ctypes.get_last_error(), call)


@functools.cache
def _extended_limits() -> Any:
    import ctypes
    from ctypes import wintypes

    class BasicLimits(ctypes.Structure):
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

    class ExtendedLimits(ctypes.Structure):
        _fields_ = (
            ("BasicLimitInformation", BasicLimits),
            ("IoInfo", ctypes.c_uint64 * 6),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        )

    return ExtendedLimits


def set_job_limits(job: int, flags: int, memory_bytes: int = 0) -> None:
    import ctypes

    limits = _extended_limits()()
    limits.BasicLimitInformation.LimitFlags = flags
    limits.JobMemoryLimit = memory_bytes
    win_check(
        kernel32().SetInformationJobObject(
            job, EXTENDED_LIMIT_INFORMATION, ctypes.byref(limits), ctypes.sizeof(limits)
        ),
        "SetInformationJobObject",
    )


def open_process(pid: int, access: int) -> int | None:
    handle = kernel32().OpenProcess(access, False, pid)
    return int(handle) if handle else None


def process_started(pid: int) -> str | None:
    """The process start time as a token, or None when no such process is running."""
    if sys.platform == "win32":
        import ctypes

        handle = open_process(pid, PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE)
        if handle is None:
            return None
        try:
            if kernel32().WaitForSingleObject(handle, 0) != WAIT_TIMEOUT:
                return None
            created, exited, kernel, user = (ctypes.c_uint64() for _ in range(4))
            ok = kernel32().GetProcessTimes(
                handle,
                ctypes.byref(created),
                ctypes.byref(exited),
                ctypes.byref(kernel),
                ctypes.byref(user),
            )
            return str(created.value) if ok else None
        finally:
            kernel32().CloseHandle(handle)
    if sys.platform == "linux":
        try:
            with open(f"/proc/{pid}/stat", encoding="ascii") as handle:
                stat = handle.read()
        except OSError:
            return None
        fields = stat.rpartition(")")[2].split()
        return None if fields[0] == "Z" else fields[19]
    done = subprocess.run(
        ["/bin/ps", "-o", "lstart=", "-p", str(pid)],
        capture_output=True,
        text=True,
        check=False,
    )
    return done.stdout.strip() or None


def bundled_cli() -> str | None:
    """The SDK's bundled CLI, found without importing the SDK so `-v` stays fast."""
    spec = find_spec("claude_agent_sdk")
    if spec is None or spec.origin is None:
        return None
    name = "claude.exe" if os.name == "nt" else "claude"
    exe = os.path.join(os.path.dirname(spec.origin), "_bundled", name)
    return exe if os.path.exists(exe) else None


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args[:1] == [BLOCK_CONFIG_CHANGE]:
        return _block_config_change()
    inputs = {name: os.environ.pop(name, "") for name in INPUT_NAMES}
    cli = inputs["QMA_REAL_CLI"] or bundled_cli()
    if cli is None:
        print("qma-cli-launcher: no QMA_REAL_CLI and no bundled CLI", file=sys.stderr)
        return EXIT_NO_CLI
    chat, proc_dir = inputs["QMA_CHAT_ID"], inputs["QMA_PROC_DIR"]
    if args == VERSION_ARGS or not (chat or proc_dir):
        return subprocess.run([cli, *args], check=False).returncode
    if not (proc_dir and is_chat_id(chat)):
        print("qma-cli-launcher: QMA_CHAT_ID and QMA_PROC_DIR must both be set", file=sys.stderr)
        return EXIT_REFUSED
    from pathlib import Path

    record = pid_path(Path(proc_dir), chat)
    record.parent.mkdir(parents=True, exist_ok=True)
    if sys.platform == "win32":
        return _run_windows([cli, *args], chat, record, inputs["QMA_CAP"])
    return _run_posix([cli, *args], chat, record, inputs["QMA_CAP"])


def _block_config_change() -> int:
    import json

    try:
        source = str(json.loads(sys.stdin.read() or "{}").get("source", "unknown"))
    except ValueError, AttributeError:
        source = "unknown"
    print(f"QMA owns the agent settings; a {source} change is blocked.", file=sys.stderr)
    return EXIT_BLOCKED


def _write_record(path: Path, record: PidRecord) -> None:
    import json

    staged = path.with_suffix(".tmp")
    staged.write_text(json.dumps(record._asdict()), encoding="utf-8")
    staged.replace(path)


def _start_suspended(command: list[str]) -> subprocess.Popen[bytes]:
    try:
        return subprocess.Popen(command, creationflags=CREATE_BREAKAWAY_FROM_JOB | CREATE_SUSPENDED)
    except OSError as error:
        if getattr(error, "winerror", None) != ERROR_ACCESS_DENIED:
            raise
    return subprocess.Popen(command, creationflags=CREATE_SUSPENDED)


def _run_windows(command: list[str], chat: str, record: Path, cap: str) -> int:
    import ctypes

    k = kernel32()
    job = k.CreateJobObjectW(None, chat_job_name(record.parent, chat))
    win_check(job, "CreateJobObjectW")
    try:
        if ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
            print(f"qma-cli-launcher: chat {chat} already has a live CLI", file=sys.stderr)
            return EXIT_REFUSED
        set_job_limits(job, JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)
        child = _start_suspended(command)
        try:
            try:
                _place(child.pid, job, cap, record)
            except OSError as error:
                child.kill()
                child.wait()
                print(
                    f"qma-cli-launcher: CLI pid {child.pid} not started: {error}", file=sys.stderr
                )
                return EXIT_REFUSED
            except BaseException:
                child.kill()
                child.wait()
                raise
            return child.wait()
        finally:
            record.unlink(missing_ok=True)
    finally:
        k.CloseHandle(job)


def _place(pid: int, job: int, cap: str, record: Path) -> None:
    import ctypes
    from ctypes import wintypes

    k = kernel32()
    access = PROCESS_SET_QUOTA | PROCESS_TERMINATE | PROCESS_SUSPEND_RESUME
    handle = open_process(pid, access | PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE)
    win_check(handle, "OpenProcess")
    try:
        started = process_started(pid)
        if started is None:
            raise ProcessLookupError(pid)
        _write_record(record, PidRecord(os.getpid(), pid, started))
        if cap:
            parent = k.OpenJobObjectW(JOB_OBJECT_ASSIGN_PROCESS, False, cap)
            win_check(parent, f"OpenJobObjectW {cap}")
            try:
                win_check(k.AssignProcessToJobObject(parent, handle), "assign to the parent job")
            finally:
                k.CloseHandle(parent)
        win_check(k.AssignProcessToJobObject(job, handle), "assign to the chat job")
        if ctypes.WinDLL("ntdll").NtResumeProcess(wintypes.HANDLE(handle)) != 0:
            raise OSError("NtResumeProcess failed")
    finally:
        k.CloseHandle(handle)


def _run_posix(command: list[str], chat: str, record: Path, cap: str) -> int:
    if sys.platform == "linux" and cap:
        unit = f"--unit={chat_unit_prefix(record.parent, chat)}-{os.getpid()}"
        command = [SYSTEMD_RUN, "--user", "--scope", "--quiet", f"--slice={cap}", unit, *command]
    child = subprocess.Popen(
        command,
        start_new_session=True,
        preexec_fn=death_signal_hook() if sys.platform == "linux" else None,  # noqa: PLW1509
    )
    if sys.platform != "win32":

        def kill_tree(*_: object) -> None:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(child.pid, signal.SIGKILL)

        signal.signal(signal.SIGTERM, lambda *_: (kill_tree(), sys.exit(143)))
        if sys.platform == "darwin":
            import threading

            threading.Thread(target=_kill_on_parent_exit, args=(kill_tree,), daemon=True).start()
    try:
        started = process_started(child.pid)
        if started is not None:
            _write_record(record, PidRecord(os.getpid(), child.pid, started))
        code = child.wait()
    finally:
        record.unlink(missing_ok=True)
    return 128 - code if code < 0 else code


def death_signal_hook() -> Callable[[], None]:
    """Resolves `prctl` here, so the hook that runs in the forked child before exec, where no
    thread exists yet, imports nothing."""
    import ctypes

    if sys.platform == "win32":
        raise RuntimeError("the parent-death signal is Linux only")
    prctl = ctypes.CDLL(None, use_errno=True).prctl
    pr_set_pdeathsig, sigkill = 1, signal.SIGKILL
    return lambda: prctl(pr_set_pdeathsig, sigkill)


def _kill_on_parent_exit(kill_tree: Any) -> None:
    if sys.platform == "darwin":
        import select

        queue = select.kqueue()
        watch = select.kevent(
            os.getppid(), filter=select.KQ_FILTER_PROC, fflags=select.KQ_NOTE_EXIT
        )
        queue.control([watch], 1, None)
        kill_tree()
