"""Host bootstrap executed by the app's locked interpreter, using only stdlib."""

from __future__ import annotations

import ctypes
import io
import json
import os
import runpy
import socket
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
    elif config.get("tier") != "T2":
        import resource  # noqa: PLC0415

        # FastMCP may already have created the subprocess session.
        if os.getsid(os.getpid()) != os.getpid():
            os.setsid()
        if config.get("memory_mb"):
            memory = int(config["memory_mb"]) * 1024 * 1024
            resource.setrlimit(resource.RLIMIT_AS, (memory, memory))

    def check(path: Any) -> None:
        if isinstance(path, int):
            return  # The opening operation already passed the audit hook.
        target = Path(os.fsdecode(path)).resolve()
        if not target.is_relative_to(volume):
            raise PermissionError("App writes must stay inside its volume.")
        if target == volume or target.is_relative_to(volume / "road"):
            raise PermissionError("Road evidence is owned by the host.")

    plumbing = threading.local()
    original_socketpair = socket.socketpair

    def local_socketpair(*args: Any, **kwargs: Any) -> tuple[socket.socket, socket.socket]:
        # Windows asyncio creates its wake-up pipe through a loopback socketpair.
        # Only this stdlib operation is exempt; app network calls remain denied.
        plumbing.active = True
        try:
            return original_socketpair(*args, **kwargs)
        finally:
            plumbing.active = False

    if config.get("recorded") and sys.platform == "win32":
        socket.socketpair = local_socketpair

    def audit(event: str, args: tuple[Any, ...]) -> None:
        if (
            config.get("recorded")
            and not getattr(plumbing, "active", False)
            and event
            in {
                "socket.connect",
                "socket.getaddrinfo",
                "socket.sendto",
                "socket.bind",
            }
        ):
            raise PermissionError("Recorded proofs cannot use the network.")
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
            target = Path(os.fsdecode(args[0])).resolve()
            if not target.is_relative_to(volume):
                raise PermissionError("App working directories stay inside the volume.")

    sys.addaudithook(audit)
    sys.path[:0] = [str(image), str(image / "src")]
    if config.get("tests"):
        import unittest  # noqa: PLC0415 - only own-test proofs need discovery

        suite = unittest.defaultTestLoader.discover(str(image / "tests"))
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=2).run(suite)
        report = {
            "tests_run": result.testsRun,
            "passed": bool(result.testsRun) and result.wasSuccessful() and not result.skipped,
            "failures": [text for _, text in result.failures],
            "errors": [text for _, text in result.errors],
            "skipped": len(result.skipped),
            "python": sys.version.split()[0],
        }
        (volume / "data/test-result.json").write_text(json.dumps(report), encoding="utf-8")
        raise SystemExit(0 if report["passed"] else 1)
    heartbeat = volume / "data" / f"heartbeat-{config['instance_id']}.json"
    counts = {"job_runs": 0, "job_errors": 0}
    lock = threading.Lock()

    def pulse() -> None:
        while True:
            with lock:
                data = {"pid": os.getpid(), "at": time.monotonic(), "utc": time.time(), **counts}
            temporary = heartbeat.with_suffix(".tmp")
            try:
                temporary.write_text(json.dumps(data), encoding="utf-8")
                temporary.replace(heartbeat)
            except OSError:
                # Windows readers can briefly deny replacement. Retry on the next
                # pulse; persistent write failures still expire the host's heartbeat.
                pass
            time.sleep(0.25)

    declared = cast("list[str]", config["jobs"])
    queue = volume / "data" / "jobs"

    def run_job(job: str) -> dict[str, Any]:
        with lock:
            counts["job_runs"] += 1
        try:
            if job not in declared:
                raise ValueError("The job is not declared.")
            namespace = runpy.run_path(str(image / job), run_name="qmx_job")
            run = namespace.get("run")
            if not callable(run):
                raise ValueError("A job script must define run().")
            run()
        except Exception as error:
            with lock:
                counts["job_errors"] += 1
            print(json.dumps({"event": "job_error", "job": job}), file=sys.stderr)
            return {"ok": False, "error": type(error).__name__}
        return {"ok": True}

    def jobs() -> None:
        """Answer the host's job requests one at a time, oldest first; the host's engine
        trigger decides when a job runs (engine AD-57)."""
        while True:
            time.sleep(0.25)
            for request in sorted(queue.glob("*.request.json")) if queue.is_dir() else []:
                try:
                    job = str(json.loads(request.read_text(encoding="utf-8"))["job"])
                except OSError:
                    continue  # The host withdrew it.
                answer = run_job(job)
                name = request.name.removesuffix(".request.json")
                staged = queue / f"{name}.answer"
                staged.write_text(json.dumps(answer), encoding="utf-8")
                staged.replace(queue / f"{name}.done.json")
                request.unlink(missing_ok=True)

    threading.Thread(target=pulse, name="qmx-heartbeat", daemon=True).start()
    if declared:
        threading.Thread(target=jobs, name="qmx-jobs", daemon=True).start()
    runpy.run_path(str(image / config["mcp"]), run_name="__main__")


if __name__ == "__main__":
    main()
