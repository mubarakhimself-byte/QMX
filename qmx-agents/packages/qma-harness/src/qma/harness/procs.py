"""The OS memory cap over every agent CLI tree, and the chat-to-process bookkeeping.

`max_live_chats` and idle reaping bound how many CLIs run. This bounds what they use together,
Bash children and MCP helpers included. The cap holder itself is never inside the cap.

This module owns the parent object; `qma.launcher` puts each chat's CLI into it, in a per-chat
child, before the CLI runs.
- Windows: one named parent Job Object with the memory limit and kill-on-close. Job memory
  limits count private commit, so size the limit on commit (HP0 S18: about 350 MB per fresh
  CLI). When a process hits the limit, the chat whose job holds it is killed whole.
- Linux: the user slice `qma-agents.slice` with `MemoryMax`. Without a usable user systemd,
  `report().os_cap` is False and the live-chat cap is the only bound.
- macOS: no OS cap.
"""

from __future__ import annotations

import contextlib
import ctypes
import functools
import hashlib
import os
import shutil
import signal
import subprocess
import sys
import threading
import time
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Protocol

from qma.launcher import (
    EXTENDED_LIMIT_INFORMATION,
    JOB_OBJECT_LIMIT_JOB_MEMORY,
    JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE,
    JOB_OBJECT_QUERY,
    JOB_OBJECT_TERMINATE,
    PROCESS_QUERY_LIMITED_INFORMATION,
    SYSTEMD_RUN,
    ExtendedLimits,
    PidRecord,
    chat_job_name,
    kernel32,
    open_process,
    pid_path,
    process_started,
    read_pid_record,
    win_check,
)

SLICE: Final = "qma-agents.slice"
MB: Final = 1024 * 1024
STOP_WAIT_S: Final = 5.0

_PROCESS_ID_LIST: Final = 3
_ASSOCIATE_COMPLETION_PORT: Final = 7
_MSG_NEW_PROCESS: Final = 6
_MSG_EXITS: Final = (7, 8)
_MSG_JOB_MEMORY_LIMIT: Final = 10
_PROCESS_VM_READ: Final = 0x0010
_INFINITE: Final = 0xFFFFFFFF
_STOP_KEY: Final = 1
_MAX_IDS: Final = 4096


@dataclass(frozen=True)
class CapReport:
    os_cap: bool
    """False on macOS, and on Linux without a usable user systemd."""
    limit_mb: int | None
    used_mb: int | None
    chats: tuple[str, ...]
    last_killed: str | None
    """The chat whose tree was killed for the memory limit most recently, if any."""


class _Parent(Protocol):
    name: str
    os_cap: bool

    def set_limit(self, limit_mb: int | None) -> None: ...
    def used_mb(self) -> int | None: ...
    def stop(self, chat: str) -> None: ...
    def last_killed(self) -> str | None: ...
    def close(self) -> None: ...


class AgentProcessCap:
    def __init__(self, procs_dir: Path, parent: _Parent, limit_mb: int | None) -> None:
        self.procs_dir = procs_dir
        self._parent = parent
        self._limit_mb = limit_mb

    @classmethod
    def for_platform(cls, procs_dir: Path, limit_mb: int | None) -> AgentProcessCap:
        """Create or adopt the parent job (Windows) or slice (Linux); none on macOS. `None`
        means no memory limit; the Windows job still exists for kill-on-close."""
        procs_dir.mkdir(parents=True, exist_ok=True)
        cap = cls(procs_dir, _NoParent(), limit_mb)
        if sys.platform == "win32":
            digest = hashlib.sha256(str(procs_dir.resolve()).lower().encode()).hexdigest()[:16]
            cap._parent = _JobParent(f"Local\\qma-agents-{digest}", cap)
        elif sys.platform == "linux" and _user_systemd():
            cap._parent = _SliceParent()
        cap._parent.set_limit(limit_mb)
        return cap

    @property
    def handle_name(self) -> str:
        """What the launch environment passes as `QMA_CAP`: the job name, the slice, or ""."""
        return self._parent.name

    def alive(self, chat: str) -> bool:
        """True when this chat's pid file names a CLI that is still running. Pid and start
        time must both match, so a reused pid reads as dead."""
        record = read_pid_record(pid_path(self.procs_dir, chat))
        return record is not None and _running(record)

    def stop_chat(self, chat: str) -> None:
        """Kill this chat's whole tree and wait for its CLI to go. Idempotent."""
        self._parent.stop(chat)
        record = read_pid_record(pid_path(self.procs_dir, chat))
        if record is not None and _running(record):
            with contextlib.suppress(OSError):
                os.kill(record.cli_pid, signal.SIGTERM)
        deadline = time.monotonic() + STOP_WAIT_S
        while self.alive(chat) and time.monotonic() < deadline:
            time.sleep(0.05)

    def kill_orphans(self) -> tuple[str, ...]:
        """`stop_chat` every chat whose pid file names a live CLI, then delete the pid files.
        Returns the chats it killed. Idempotent."""
        killed: list[str] = []
        for chat in self._recorded():
            if self.alive(chat):
                self.stop_chat(chat)
                killed.append(chat)
            pid_path(self.procs_dir, chat).unlink(missing_ok=True)
        return tuple(killed)

    def report(self) -> CapReport:
        return CapReport(
            os_cap=self._parent.os_cap,
            limit_mb=self._limit_mb,
            used_mb=self._parent.used_mb(),
            chats=self.live_chats(),
            last_killed=self._parent.last_killed(),
        )

    def live_chats(self) -> tuple[str, ...]:
        return tuple(chat for chat in self._recorded() if self.alive(chat))

    def set_limit(self, limit_mb: int | None) -> None:
        """Applies a new limit to the live parent. Running chats stay members."""
        self._parent.set_limit(limit_mb)
        self._limit_mb = limit_mb

    def close(self) -> None:
        """Kills every member tree and releases the parent. Idempotent."""
        self._parent.close()

    def _recorded(self) -> list[str]:
        return sorted(path.stem for path in self.procs_dir.glob("*.json"))


def _running(record: PidRecord) -> bool:
    return process_started(record.cli_pid) == record.cli_started


class _NoParent:
    name = ""
    os_cap = False

    def set_limit(self, limit_mb: int | None) -> None:
        pass

    def used_mb(self) -> int | None:
        return None

    def stop(self, chat: str) -> None:
        pass

    def last_killed(self) -> str | None:
        return None

    def close(self) -> None:
        pass


class _CompletionPort(ctypes.Structure):
    _fields_ = (("CompletionKey", ctypes.c_void_p), ("CompletionPort", wintypes.HANDLE))


class _MemoryCounters(ctypes.Structure):
    _fields_ = (
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    )


class _ProcessIds(ctypes.Structure):
    _fields_ = (
        ("NumberOfAssignedProcesses", wintypes.DWORD),
        ("NumberOfProcessIdsInList", wintypes.DWORD),
        ("ProcessIdList", ctypes.c_size_t * _MAX_IDS),
    )


@dataclass
class _JobParent:
    name: str
    cap: AgentProcessCap
    os_cap: bool = True

    def __post_init__(self) -> None:
        k = _kernel32()
        self._job: int = k.CreateJobObjectW(None, self.name)
        win_check(self._job, "CreateJobObjectW")
        self._killed: str | None = None
        self._closed = False
        self._port: int = k.CreateIoCompletionPort(wintypes.HANDLE(-1), None, 0, 1)
        win_check(self._port, "CreateIoCompletionPort")
        link = _CompletionPort(None, self._port)
        if k.SetInformationJobObject(
            self._job, _ASSOCIATE_COMPLETION_PORT, ctypes.byref(link), ctypes.sizeof(link)
        ):
            threading.Thread(target=self._watch, name="qma-cap-watch", daemon=True).start()

    def set_limit(self, limit_mb: int | None) -> None:
        limits = ExtendedLimits()
        flags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if limit_mb is not None:
            flags |= JOB_OBJECT_LIMIT_JOB_MEMORY
            limits.JobMemoryLimit = limit_mb * MB
        limits.BasicLimitInformation.LimitFlags = flags
        win_check(
            _kernel32().SetInformationJobObject(
                self._job, EXTENDED_LIMIT_INFORMATION, ctypes.byref(limits), ctypes.sizeof(limits)
            ),
            "SetInformationJobObject",
        )

    def used_mb(self) -> int | None:
        return _commit(self._job) // MB

    def stop(self, chat: str) -> None:
        k = _kernel32()
        job = k.OpenJobObjectW(JOB_OBJECT_TERMINATE, False, chat_job_name(chat))
        if job:
            k.TerminateJobObject(job, 1)
            k.CloseHandle(job)

    def last_killed(self) -> str | None:
        return self._killed

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        k = _kernel32()
        k.PostQueuedCompletionStatus(self._port, 0, _STOP_KEY, None)
        k.TerminateJobObject(self._job, 1)
        k.CloseHandle(self._job)

    def _watch(self) -> None:
        """Owners are looked up when a process joins, while it still runs, because the process
        that hits the limit is often gone before its message is read."""
        k = _kernel32()
        owners: dict[int, str] = {}
        message, key, pid = wintypes.DWORD(), ctypes.c_size_t(), ctypes.c_void_p()
        while k.GetQueuedCompletionStatus(
            self._port, ctypes.byref(message), ctypes.byref(key), ctypes.byref(pid), _INFINITE
        ):
            if key.value == _STOP_KEY:
                break
            member = pid.value or 0
            if message.value == _MSG_NEW_PROCESS:
                chat = self._chat_of(member)
                if chat is not None:
                    owners[member] = chat
            elif message.value in _MSG_EXITS:
                owners.pop(member, None)
            elif message.value == _MSG_JOB_MEMORY_LIMIT:
                chat = owners.get(member) or self._chat_of(member)
                if chat is not None:
                    self._killed = chat
                    self.cap.stop_chat(chat)
        k.CloseHandle(self._port)

    def _chat_of(self, pid: int) -> str | None:
        chats = self.cap.live_chats()
        for chat in chats:
            record = read_pid_record(pid_path(self.cap.procs_dir, chat))
            if record is not None and record.cli_pid == pid:
                return chat
        process = open_process(pid, PROCESS_QUERY_LIMITED_INFORMATION)
        if process is None:
            return None
        k = _kernel32()
        try:
            for chat in chats:
                job = k.OpenJobObjectW(JOB_OBJECT_QUERY, False, chat_job_name(chat))
                if not job:
                    continue
                held = wintypes.BOOL()
                found = k.IsProcessInJob(process, job, ctypes.byref(held)) and held.value
                k.CloseHandle(job)
                if found:
                    return chat
        finally:
            k.CloseHandle(process)
        return None


@functools.cache
def _kernel32() -> Any:
    k = kernel32()
    k.CreateIoCompletionPort.restype = wintypes.HANDLE
    k.CreateIoCompletionPort.argtypes = (
        wintypes.HANDLE,
        wintypes.HANDLE,
        ctypes.c_size_t,
        wintypes.DWORD,
    )
    k.GetQueuedCompletionStatus.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(wintypes.DWORD),
        ctypes.POINTER(ctypes.c_size_t),
        ctypes.POINTER(ctypes.c_void_p),
        wintypes.DWORD,
    )
    k.PostQueuedCompletionStatus.argtypes = (
        wintypes.HANDLE,
        wintypes.DWORD,
        ctypes.c_size_t,
        ctypes.c_void_p,
    )
    k.IsProcessInJob.argtypes = (wintypes.HANDLE, wintypes.HANDLE, ctypes.POINTER(wintypes.BOOL))
    k.K32GetProcessMemoryInfo.argtypes = (
        wintypes.HANDLE,
        ctypes.POINTER(_MemoryCounters),
        wintypes.DWORD,
    )
    return k


def _commit(job: int) -> int:
    """Private commit, in bytes, of every process in `job`, nested jobs included."""
    k = _kernel32()
    ids = _ProcessIds()
    if not k.QueryInformationJobObject(
        job, _PROCESS_ID_LIST, ctypes.byref(ids), ctypes.sizeof(ids), None
    ):
        return 0
    total = 0
    for pid in ids.ProcessIdList[: ids.NumberOfProcessIdsInList]:
        process = open_process(pid, PROCESS_QUERY_LIMITED_INFORMATION | _PROCESS_VM_READ)
        if process is None:
            continue
        counters = _MemoryCounters(cb=ctypes.sizeof(_MemoryCounters))
        if k.K32GetProcessMemoryInfo(process, ctypes.byref(counters), counters.cb):
            total += counters.PagefileUsage
        k.CloseHandle(process)
    return total


def _systemctl(*args: str) -> subprocess.CompletedProcess[str]:
    systemctl = shutil.which("systemctl") or "/usr/bin/systemctl"
    return subprocess.run(
        [systemctl, "--user", *args], capture_output=True, text=True, timeout=30, check=False
    )


def _user_systemd() -> bool:
    if not Path(SYSTEMD_RUN).exists() or shutil.which("systemctl") is None:
        return False
    try:
        return _systemctl("show-environment").returncode == 0
    except OSError, subprocess.TimeoutExpired:
        return False


class _SliceParent:
    """`qma-agents.slice` under user systemd. Each launcher runs its CLI in a scope named
    `qma-chat-<chat>-<launcher pid>` under it."""

    name = SLICE
    os_cap = True

    def set_limit(self, limit_mb: int | None) -> None:
        limit = "infinity" if limit_mb is None else f"{limit_mb}M"
        config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
        unit = config / "systemd" / "user" / SLICE
        unit.parent.mkdir(parents=True, exist_ok=True)
        unit.write_text(f"[Slice]\nMemoryMax={limit}\n", encoding="utf-8")
        _systemctl("daemon-reload")
        _systemctl("set-property", "--runtime", SLICE, f"MemoryMax={limit}")

    def used_mb(self) -> int | None:
        shown = _systemctl("show", "-P", "MemoryCurrent", SLICE).stdout.strip()
        return int(shown) // MB if shown.isdigit() else None

    def stop(self, chat: str) -> None:
        _systemctl("stop", f"qma-chat-{chat}-*.scope")

    def last_killed(self) -> str | None:
        listed = _systemctl("list-units", "--failed", "--plain", "--no-legend", "qma-chat-*")
        for line in listed.stdout.splitlines():
            unit = line.split(maxsplit=1)[0] if line.strip() else ""
            if _systemctl("show", "-P", "Result", unit).stdout.strip() == "oom-kill":
                return unit.removeprefix("qma-chat-").removesuffix(".scope").rpartition("-")[0]
        return None

    def close(self) -> None:
        _systemctl("stop", "qma-chat-*.scope")
