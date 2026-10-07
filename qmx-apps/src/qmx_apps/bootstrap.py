"""Host bootstrap executed by the app's locked interpreter, using only stdlib."""

from __future__ import annotations

import ctypes
import io
import json
import os
import runpy
import sys
import threading
import time
from ctypes import wintypes
from pathlib import Path
from typing import Any, cast


class RedactedStream(io.TextIOBase):
    def __init__(self, stream: Any, secrets: list[str], *, jobs_stdout: bool = False) -> None:
        self.stream = stream
        self.secrets = secrets
        self.jobs_stdout = jobs_stdout

    def write(self, text: str) -> int:
        original = len(text)
        for secret in self.secrets:
            text = text.replace(secret, "[redacted]")
        stream = (
            sys.stderr
            if self.jobs_stdout and threading.current_thread().name == "qmx-jobs"
            else self.stream
        )
        stream.write(text)
        stream.flush()
        return original

    def flush(self) -> None:
        self.stream.flush()

    def isatty(self) -> bool:
        return False

    @property
    def buffer(self) -> Any:
        return self.stream.buffer

    def fileno(self) -> int:
        return self.stream.fileno()


def main() -> None:
    config = cast("dict[str, Any]", json.loads(sys.argv[1]))
    volume = Path(config["volume"]).resolve()
    image = Path(config["image"]).resolve()
    names = cast("list[str]", config["secret_names"])
    allowed = cast("list[str]", config["env_names"])
    environment = {name: os.environ[name] for name in allowed if name in os.environ}
    secrets = [environment[name] for name in names if environment.get(name)]
    os.environ.clear()
    os.environ.update(environment)
    sys.stderr = RedactedStream(sys.stderr, secrets)
    # Job scripts cannot accidentally print into the MCP protocol stream.
    sys.stdout = RedactedStream(sys.stdout, [], jobs_stdout=True)
    os.chdir(volume)
    if sys.platform == "win32":
        kernel: Any = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel.OpenJobObjectW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
        kernel.OpenJobObjectW.restype = wintypes.HANDLE
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        kernel.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
        kernel.AssignProcessToJobObject.restype = wintypes.BOOL
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        kernel.CloseHandle.restype = wintypes.BOOL
        handle = kernel.OpenJobObjectW(1, False, config["job_name"])
        if not handle:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            if not kernel.AssignProcessToJobObject(handle, kernel.GetCurrentProcess()):
                raise ctypes.WinError(ctypes.get_last_error())
        finally:
            kernel.CloseHandle(handle)
    else:
        import resource  # noqa: PLC0415

        os.setsid()
        memory = int(config["memory_mb"]) * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
        cpu = max(1, int(config["cpu_seconds"]) + 1)
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))

    def check(path: Any) -> None:
        if isinstance(path, int):
            return  # The opening operation already passed the audit hook.
        target = Path(os.fsdecode(path)).resolve()
        if not target.is_relative_to(volume):
            raise PermissionError("App writes must stay inside its volume.")

    def audit(event: str, args: tuple[Any, ...]) -> None:
        if event == "open":
            mode = args[1] or ""
            flags = args[2]
            if any(char in mode for char in "wax+") or flags & (
                os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
            ):
                check(args[0])
        elif event == "sqlite3.connect":
            path = os.fsdecode(args[0])
            if path != ":memory:":
                if not path or path.startswith("file:"):
                    raise PermissionError("Use a database path inside the volume.")
                check(path)
        elif event in {"os.remove", "os.rmdir", "os.mkdir", "os.chmod", "os.utime", "os.truncate"}:
            check(args[0])
            if event != "os.truncate" and args[-1] != -1:
                raise PermissionError("Directory-relative writes are not supported in T1.")
        elif event in {"os.rename", "os.link", "os.symlink"}:
            check(args[0])
            check(args[1])
            if any(fd != -1 for fd in args[2:]):
                raise PermissionError("Directory-relative writes are not supported in T1.")
        elif event == "os.chdir":
            check(args[0])

    sys.addaudithook(audit)
    heartbeat = volume / "data" / f"heartbeat-{config['instance_id']}.json"
    counts = {"job_runs": 0, "job_errors": 0}
    lock = threading.Lock()

    def pulse() -> None:
        while True:
            with lock:
                data = {"pid": os.getpid(), "at": time.monotonic(), **counts}
            temporary = heartbeat.with_suffix(".tmp")
            try:
                temporary.write_text(json.dumps(data), encoding="utf-8")
                temporary.replace(heartbeat)
            except OSError:
                # Windows readers can briefly deny replacement. Retry on the next
                # pulse; persistent write failures still expire the host's heartbeat.
                pass
            time.sleep(0.25)

    def jobs() -> None:
        while True:
            time.sleep(float(config["interval_seconds"]))
            for job in cast("list[str]", config["jobs"]):
                with lock:
                    counts["job_runs"] += 1
                try:
                    namespace = runpy.run_path(str(image / job), run_name="qmx_job")
                    run = namespace.get("run")
                    if not callable(run):
                        raise ValueError("A scheduled job script must define run().")
                    run()
                except Exception:
                    with lock:
                        counts["job_errors"] += 1
                    print(json.dumps({"event": "job_error", "job": job}), file=sys.stderr)

    threading.Thread(target=pulse, name="qmx-heartbeat", daemon=True).start()
    if config["interval_seconds"]:
        threading.Thread(target=jobs, name="qmx-jobs", daemon=True).start()
    sys.path[:0] = [str(image), str(image / "src")]
    runpy.run_path(str(image / config["mcp"]), run_name="__main__")


if __name__ == "__main__":
    main()
