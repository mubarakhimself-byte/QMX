"""power_watch: read the power line every power_poll_s. On battery, write the HOLD file, which makes
dispatch refuse new seats. When mains returns, wait power_settle_s for the router, then require the
internet probe and GitHub (`git ls-remote`) to answer before removing HOLD. A HOLD this watcher did
not write is never removed by it."""

from __future__ import annotations

import ctypes
import json
import socket
import sys
import time
from pathlib import Path
from typing import Callable

from ship import state as st
from ship.gitx import GitError, git
from ship.layout import Program
from ship.settings import Settings


def on_mains_windows() -> bool:
    class SystemPowerStatus(ctypes.Structure):
        _fields_ = [("ACLineStatus", ctypes.c_ubyte), ("BatteryFlag", ctypes.c_ubyte),
                    ("BatteryLifePercent", ctypes.c_ubyte), ("SystemStatusFlag", ctypes.c_ubyte),
                    ("BatteryLifeTime", ctypes.c_ulong), ("BatteryFullLifeTime", ctypes.c_ulong)]

    status = SystemPowerStatus()
    if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
        return True
    return status.ACLineStatus != 0  # 1 online, 255 unknown (no battery): both count as mains


def on_mains_linux(root: Path = Path("/sys/class/power_supply")) -> bool:
    supplies = [p for p in root.glob("*") if (p / "type").exists()]
    mains = [p for p in supplies if (p / "type").read_text().strip() in ("Mains", "USB")]
    if mains:
        return any((p / "online").exists() and (p / "online").read_text().strip() == "1" for p in mains)
    batteries = [p for p in supplies if (p / "type").read_text().strip() == "Battery"]
    return not any((p / "status").exists() and (p / "status").read_text().strip() == "Discharging"
                   for p in batteries)


def on_mains() -> bool:
    return on_mains_windows() if sys.platform == "win32" else on_mains_linux()


def probe_network(program: Program, settings: Settings) -> list[str]:
    """Empty when both the internet probe and GitHub answer; otherwise what failed."""
    failed = []
    host, _, port = settings.internet_probe.rpartition(":")
    try:
        socket.create_connection((host, int(port)), timeout=settings.net_timeout_s).close()
    except OSError as exc:
        failed.append(f"internet {settings.internet_probe}: {exc}")
    try:
        state = st.load(program)
        git(Path(state.repo), "ls-remote", state.remote, "HEAD", timeout=settings.net_timeout_s)
    except (GitError, OSError) as exc:
        failed.append(f"github: {exc}")
    return failed


def step(program: Program, settings: Settings, mains: bool, now: float, probe: Callable[[], list[str]]) -> str:
    memo = json.loads(program.power.read_text("utf-8")) if program.power.exists() else {}
    ours = bool(memo.get("hold"))
    if not mains:
        memo["mains_since"] = None
        if not ours:
            stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now))
            program.hold.write_text(f"power: on battery since {stamp}\n", "utf-8")
            memo.update(hold=True, battery_since=now)
            _event(program, "hold", reason="battery")
            line = "HOLD on battery"
        else:
            line = "BATTERY hold kept"
    elif not ours:
        line = "MAINS"
    elif memo.get("mains_since") is None:
        memo["mains_since"] = now
        line = f"MAINS back, waiting {settings.power_settle_s}s before network checks"
    elif now - memo["mains_since"] < settings.power_settle_s:
        line = f"MAINS settling {now - memo['mains_since']:.0f}s of {settings.power_settle_s}s"
    else:
        failed = probe()
        if failed:
            line = "WAIT " + "; ".join(failed)
        else:
            program.hold.unlink(missing_ok=True)
            memo = {"hold": False}
            _event(program, "clear", reason="mains, internet and GitHub back")
            line = "CLEAR hold removed; run recover before dispatching"
    program.power.write_text(json.dumps(memo), "utf-8")
    return line


def _event(program: Program, kind: str, **detail: object) -> None:
    if program.state.exists():
        with st.locked(program) as state:
            state.log(kind, None, **detail)


def power_report(program: Program, settings: Settings, now: float | None = None) -> tuple[int, list[str]]:
    """Read-only, for sessions that do not run the watcher (the checkpoint review). Exit 2: no watcher
    has written power.json lately, start one. Exit 1: HOLD, wait and retry on the next tick. Exit 0: go."""
    now = time.time() if now is None else now
    watched = program.power.exists() and now - program.power.stat().st_mtime < settings.watcher_stale_s
    lines = ["WATCHER running" if watched else "NO WATCHER: start `ship power_watch` in the background"]
    if program.hold.exists():
        lines.append(f"HOLD {program.hold.read_text('utf-8').strip()}")
    else:
        lines.append("CLEAR")
    return (0 if lines[1] == "CLEAR" else 1) if watched else 2, lines


def watch(program: Program, settings: Settings, once: bool = False) -> int:
    while True:
        line = step(program, settings, on_mains(), time.time(), lambda: probe_network(program, settings))
        print(f"{time.strftime('%H:%M:%S')} {line}", flush=True)
        if once:
            return 0
        time.sleep(settings.power_poll_s)
