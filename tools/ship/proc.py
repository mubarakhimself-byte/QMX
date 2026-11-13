"""Process helpers that behave the same on Windows and Linux."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

WINDOWS = sys.platform == "win32"


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if WINDOWS:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            return code.value == 259  # STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def created(pid: int) -> float | None:
    """When the process started, in seconds since the epoch, or None when it is gone. With the pid this
    names one process exactly: a pid the system reused has another creation time."""
    if pid <= 0:
        return None
    if WINDOWS:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return None
        try:
            times = [wintypes.FILETIME() for _ in range(4)]
            if not kernel32.GetProcessTimes(handle, *[ctypes.byref(x) for x in times]):
                return None
            ticks = (times[0].dwHighDateTime << 32) | times[0].dwLowDateTime  # 100 ns since 1601
            return round(ticks / 1e7 - 11644473600, 3)
        finally:
            kernel32.CloseHandle(handle)
    try:
        fields = Path(f"/proc/{pid}/stat").read_text().rsplit(")", 1)[1].split()
        return round(boot_time() + int(fields[19]) / os.sysconf("SC_CLK_TCK"), 3)
    except (OSError, IndexError, ValueError):
        return None


def boot_time() -> float:
    """When this machine last started, in seconds since the epoch."""
    if WINDOWS:
        import ctypes

        ctypes.windll.kernel32.GetTickCount64.restype = ctypes.c_ulonglong
        return time.time() - ctypes.windll.kernel32.GetTickCount64() / 1000
    try:
        for line in Path("/proc/stat").read_text().splitlines():
            if line.startswith("btime "):
                return float(line.split()[1])
    except OSError:
        pass
    return 0.0


def same_process(pid: int, when: float | None) -> bool:
    """True only for the process that had this pid at creation time `when` (to the millisecond)."""
    if not pid or when is None:
        return False
    now = created(pid)
    return now is not None and abs(now - float(when)) < 0.01


def popen_group_kwargs() -> dict:
    """Start a child in its own group so a timeout can stop the child and everything it started."""
    if WINDOWS:
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def kill_tree(pid: int, timeout: float = 60) -> None:
    if WINDOWS:
        try:
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            pass
        return
    try:
        os.killpg(pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass


def stop_processes_under(root: Path) -> list[int]:
    """Stop processes whose executable lives inside `root`, such as a worktree's venv python.

    Those hold file locks that make `git worktree remove` fail on Windows.
    """
    root_text = str(root.resolve()).casefold()
    stopped: list[int] = []
    if WINDOWS:
        script = (
            "Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath } | "
            "ForEach-Object { \"$($_.ProcessId)`t$($_.ExecutablePath)\" }"
        )
        done = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        for line in done.stdout.splitlines():
            pid_text, _, exe = line.partition("\t")
            if exe.casefold().startswith(root_text) and pid_text.strip().isdigit():
                kill_tree(int(pid_text))
                stopped.append(int(pid_text))
        return stopped
    for entry in Path("/proc").glob("[0-9]*"):
        try:
            exe = os.readlink(entry / "exe")
        except OSError:
            continue
        if exe.casefold().startswith(root_text):
            try:
                os.kill(int(entry.name), signal.SIGKILL)
                stopped.append(int(entry.name))
            except OSError:
                pass
    return stopped
