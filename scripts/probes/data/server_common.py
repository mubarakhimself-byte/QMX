# ruff: noqa: S101 - this module carries the one test the plan asks for.

"""Shared plumbing for the PRB-DS probes: the server's probe root, one log, the memory measure,
and the verdict shape each `FINDINGS-server.md` row quotes.

Every probe runs on Contabo as the ordinary user `qmx`, from the checkout at
`/srv/qmx/check/prb-ds/checkout`, in the venv that probe needs, for example:

    runuser -u qmx -- env HOME=/srv/qmx/check/prb-ds/home \
        /srv/qmx/check/prb-ds/venv-hs/bin/python scripts/probes/data/p_hs.py --rows rows.jsonl

Memory is the peak resident memory of the probe's whole child process group. The child starts
in its own session, so the tool it launches, its worker processes and any PostgreSQL backend it
starts are counted, and the shell's own processes are not. A sample reads `/proc/<pid>/status`
per member and sums `VmHWM`, the kernel's high-water mark for that process, so a short spike
between samples is not lost. That is the measure PRB-S used (`scripts/probes/server/common.py`).

The one test here runs the parser on a fixed sample:

    uv run --no-sync python -m pytest scripts/probes/data/server_common.py -q
"""

from __future__ import annotations

import os
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, TextIO

PASSED: Final[str] = "PASS"
FAILED: Final[str] = "FAIL"
NOT_RUN: Final[str] = "not run"

PROBE_ROOT: Final[Path] = Path(os.environ.get("QMX_PROBE_ROOT", "/srv/qmx/check/prb-ds"))
"""Everything the probes write: their venvs, their homes, their downloads and their logs."""

KIB_PER_MIB: Final[int] = 1024
"""`/proc/<pid>/status` reports kB; every number this module returns is MB."""

_STATUS_FIELDS: Final[dict[str, str]] = {
    "VmRSS": "rss_mb",
    "VmHWM": "peak_mb",
    "VmSwap": "swap_mb",
}


@dataclass(frozen=True, slots=True)
class Memory:
    rss_mb: int
    peak_mb: int
    swap_mb: int = 0


def parse_status(text: str) -> Memory | None:
    """`VmRSS`, `VmHWM` and `VmSwap` from a `/proc/<pid>/status` body, in MB.

    `None` when the body has no `VmRSS`, which is what a kernel thread's looks like.
    """
    seen: dict[str, int] = {}
    for line in text.splitlines():
        name, _, rest = line.partition(":")
        key = _STATUS_FIELDS.get(name.strip())
        if key is None:
            continue
        parts = rest.split()
        if not parts or not parts[0].isdigit():
            continue
        seen[key] = int(parts[0]) // KIB_PER_MIB
    if "rss_mb" not in seen:
        return None
    return Memory(seen["rss_mb"], seen.get("peak_mb", seen["rss_mb"]), seen.get("swap_mb", 0))


def read_status(pid: int) -> Memory | None:
    try:
        return parse_status(Path(f"/proc/{pid}/status").read_text(encoding="ascii"))
    except (OSError, UnicodeDecodeError):
        return None


def group_pids(pgid: int) -> list[int]:
    """Every live process in `pgid`, which is the probe child's own since it calls `setsid`."""
    pids: list[int] = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit():
            continue
        try:
            stat = (entry / "stat").read_text(encoding="ascii")
        except OSError:
            continue
        fields = stat[stat.rfind(")") + 2 :].split()
        if len(fields) > 2 and fields[2] == str(pgid):
            pids.append(int(entry.name))
    return pids


def group_peak_mb(pgid: int) -> int:
    """The summed high-water mark of the group's live members, right now."""
    total = 0
    for pid in group_pids(pgid):
        memory = read_status(pid)
        if memory is not None:
            total += memory.peak_mb
    return total


class PeakSampler:
    """The largest `group_peak_mb` seen while the child ran, sampled on its own thread."""

    def __init__(self, pgid: int, interval_s: float = 1.0) -> None:
        self._pgid = pgid
        self._interval_s = interval_s
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._sample, name="peak", daemon=True)
        self.peak_mb = 0
        self.samples = 0

    def _sample(self) -> None:
        while not self._stop.is_set():
            self.peak_mb = max(self.peak_mb, group_peak_mb(self._pgid))
            self.samples += 1
            self._stop.wait(self._interval_s)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5)


@dataclass(slots=True)
class ChildRun:
    """One measured child: what it ran, how long, and its peak memory."""

    name: str
    argv: list[str]
    seconds: float
    returncode: int
    peak_mb: int
    log: Path
    timed_out: bool = False
    samples: int = 0


def child_env(**extra: str) -> dict[str, str]:
    """The environment a probe child gets: the probe home, and no inherited proxy or key."""
    env = {
        key: value
        for key, value in os.environ.items()
        if not key.startswith(("ANTHROPIC", "CLAUDE", "OPENAI")) and not key.endswith("_PROXY")
    }
    env.update(
        HOME=str(PROBE_ROOT / "home"),
        TMPDIR=str(PROBE_ROOT / "tmp"),
        PYTHONUNBUFFERED="1",
    )
    env.update(extra)
    return env


def run_child(
    name: str,
    argv: list[str],
    *,
    timeout_s: float,
    interval_s: float = 1.0,
    env: dict[str, str] | None = None,
) -> ChildRun:
    """Run `argv` in its own session, sample its group's memory, keep its output in the log."""
    log_path = PROBE_ROOT / "logs" / f"{name}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    began = time.perf_counter()
    sampler: PeakSampler | None = None
    returncode = 0
    timed_out = False
    with log_path.open("ab") as out:
        out.write(f"$ {' '.join(argv)}\n".encode())
        out.flush()
        child = subprocess.Popen(
            argv,
            stdout=out,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=env or child_env(),
        )
        sampler = PeakSampler(child.pid, interval_s)
        sampler.start()
        try:
            returncode = child.wait(timeout=timeout_s)
        except subprocess.TimeoutExpired:
            timed_out = True
            signal_pgroup(child.pid)
            returncode = child.wait(timeout=60)
        finally:
            sampler.stop()
    return ChildRun(
        name=name,
        argv=argv,
        seconds=round(time.perf_counter() - began, 1),
        returncode=returncode,
        peak_mb=sampler.peak_mb,
        log=log_path,
        timed_out=timed_out,
        samples=sampler.samples,
    )


def signal_pgroup(pgid: int, sig: int = signal.SIGTERM, grace_s: float = 20.0) -> None:
    """Terminate a whole child group and wait for it, then kill what is left."""
    for attempt in range(2):
        try:
            os.killpg(pgid, sig if attempt == 0 else signal.SIGKILL)
        except ProcessLookupError:
            return
        deadline = time.monotonic() + grace_s
        while time.monotonic() < deadline:
            if not group_pids(pgid):
                return
            time.sleep(0.2)


def meminfo_mb(key: str) -> int:
    """One `/proc/meminfo` figure in MB. The probes run on Linux, so there is no fallback."""
    with Path("/proc/meminfo").open(encoding="ascii") as handle:
        for line in handle:
            if line.startswith(f"{key}:"):
                return int(line.split()[1]) // KIB_PER_MIB
    raise ValueError(f"{key} is not in /proc/meminfo")


def free_mb() -> int:
    """The kernel's estimate of memory available to new work."""
    return meminfo_mb("MemAvailable")


def total_mb() -> int:
    return meminfo_mb("MemTotal")


def free_port() -> int:
    """A port nobody holds, so two probes on one host never collide."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_http(url: str, *, timeout_s: float, headers: dict[str, str] | None = None) -> bool:
    """Whether `url` answered before the timeout. Any HTTP status counts as answering."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        request = urllib.request.Request(url, headers=headers or {}, method="GET")  # noqa: S310
        try:
            with urllib.request.urlopen(request, timeout=5):  # noqa: S310
                return True
        except urllib.error.HTTPError:
            return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.5)
    return False


def download_file(url: str, target: Path) -> Path:
    """Fetch `url` to `target` once. A second run reuses the file, so the probe measures itself
    and not the network."""
    if target.exists() and target.stat().st_size > 0:
        return target
    target.parent.mkdir(parents=True, exist_ok=True)
    source = urllib.request.urlopen(url, timeout=300)  # noqa: S310
    with source, target.open("wb") as out:
        while block := source.read(1 << 20):
            out.write(block)
    return target


def du_mb(path: Path) -> int:
    """Disk `path` and its children hold, in MB, counting blocks a sparse file does not use."""
    total = 0
    for root, _folders, files in os.walk(path):
        for name in files:
            try:
                total += os.lstat(Path(root) / name).st_blocks * 512
            except OSError:
                continue
    return total // (KIB_PER_MIB * KIB_PER_MIB)


class Log:
    """Tee to stdout and `logs/<prefix><slug>.log`, where the prefix is `owner-` for a builder's
    run and `check-` for the coordinator's (`QMX_PROBE_LOG_PREFIX`)."""

    def __init__(self, slug: str) -> None:
        folder = PROBE_ROOT / "logs"
        folder.mkdir(parents=True, exist_ok=True)
        prefix = os.environ.get("QMX_PROBE_LOG_PREFIX", "owner-")
        self.path = folder / f"{prefix}{slug}.log"
        self.file: TextIO = self.path.open("a", encoding="utf-8")
        self.say(
            f"--- {time.strftime('%Y-%m-%dT%H:%M:%S%z')} {Path(sys.argv[0]).name} "
            f"on {free_mb()} MB free"
        )

    def say(self, text: str) -> None:
        print(text, flush=True)
        self.file.write(text + "\n")
        self.file.flush()

    def close(self) -> None:
        self.file.close()


@dataclass(slots=True)
class Report:
    """One probe's verdict and the numbers its `FINDINGS-server.md` row quotes.

    `problems` is empty exactly when the verdict is PASS. `NOT_RUN` carries the reason the run
    could not decide, so a row never dresses an unmeasured probe as a pass or a fail.
    """

    probe: str
    verdict: str = PASSED
    numbers: dict[str, object] = field(default_factory=dict)
    details: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    def note(self, text: str) -> None:
        self.details.append(text)

    def fail(self, problem: str) -> None:
        self.problems.append(problem)
        self.verdict = FAILED

    def not_run(self, reason: str) -> None:
        self.problems.append(reason)
        if self.verdict != FAILED:
            self.verdict = NOT_RUN

    def render(self) -> int:
        print(f"{self.probe} {self.verdict}")
        for key, value in self.numbers.items():
            print(f"  {key}: {value}")
        for detail in self.details:
            print(f"  {detail}")
        for problem in self.problems:
            print(f"  problem: {problem}")
        return 0 if self.verdict == PASSED else 1


SAMPLE_STATUS: Final[str] = """Name:\tpython3
Umask:\t0022
State:\tS (sleeping)
Tgid:\t4821
VmPeak:\t 1285732 kB
VmSize:\t 1192044 kB
VmLck:\t       0 kB
VmPin:\t       0 kB
VmHWM:\t  715268 kB
VmRSS:\t  690412 kB
RssAnon:\t  601288 kB
RssFile:\t   89124 kB
VmSwap:\t   12288 kB
"""
"""A `/proc/<pid>/status` body shaped like the kernel's, so the test needs no server."""


def test_parse_status_reads_peak_swap_and_resident_from_a_fixed_sample() -> None:
    assert parse_status(SAMPLE_STATUS) == Memory(rss_mb=674, peak_mb=698, swap_mb=12)
