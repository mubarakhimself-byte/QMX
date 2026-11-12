"""Process helpers that behave the same on Windows and Linux."""

from __future__ import annotations

import os
import signal
import subprocess
import sys
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


def popen_group_kwargs() -> dict:
    """Start a child in its own group so a timeout can stop the child and everything it started."""
    if WINDOWS:
        return {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    return {"start_new_session": True}


def kill_tree(pid: int) -> None:
    if WINDOWS:
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(pid)], capture_output=True)
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
