"""power_watch: read the power line every power_poll_s. On battery, write the HOLD file, which makes
dispatch refuse new seats. When mains returns, wait power_settle_s for the router, then require the
internet probe and GitHub (`git ls-remote`) to answer before removing HOLD. On mains, a failed internet
or GitHub probe also writes HOLD, and the next passing probe removes it (no settle wait).
`SHIP_FAKE_MAINS` (1 or 0) stands in for the power line.

Whose HOLD it is lives in its first word: the watcher writes `power: ...` or `network: ...`; anything else (a
manual hold, `ship hold --why ...`, written `him: ...`, or the front desk's own) is not the watcher's. The
watcher never writes over, nor removes, a HOLD that is not its own: on battery it leaves a manual hold in place,
and a manual hold written over the watcher's makes the watcher forget its own. `ship release` removes only a
manual hold; the watcher's clears itself."""

from __future__ import annotations

import ctypes
import json
import os
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
    fake = os.environ.get("SHIP_FAKE_MAINS")
    if fake in ("0", "1"):
        return fake == "1"
    return on_mains_windows() if sys.platform == "win32" else on_mains_linux()


def probe_network(program: Program, settings: Settings) -> list[str]:
    """Empty when both the internet probe and GitHub answer; otherwise what failed."""
    failed = []
    if settings.internet_probe:  # "" skips the internet probe (tests with no network)
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


WATCHER_WORDS = ("power:", "network:")


def watchers(text: str) -> bool:
    """A HOLD the power watch wrote (its first word)."""
    return text.lstrip().startswith(WATCHER_WORDS)


def hold_text(program: Program) -> str | None:
    try:
        return program.hold.read_text("utf-8")
    except OSError:
        return None


def step(program: Program, settings: Settings, mains: bool, now: float, probe: Callable[[], list[str]]) -> str:
    memo = json.loads(program.power.read_text("utf-8")) if program.power.exists() else {}
    text = hold_text(program)
    if memo.get("hold") and not (text is not None and watchers(text)):
        memo = {"hold": False}  # its HOLD was released or written over by someone else: it is not the watcher's now
    ours = bool(memo.get("hold"))
    if not mains and not ours and text is not None:
        memo["mains_since"] = None
        program.power.write_text(json.dumps(memo), "utf-8")
        return "HOLD kept: not the watcher's (" + text.strip().splitlines()[0][:80] + ")" if text.strip() else \
            "HOLD kept: not the watcher's"
    if not mains:
        memo["mains_since"] = None
        if not ours:
            stamp = time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now))
            program.hold.write_text(f"power: on battery since {stamp}\n", "utf-8")
            memo.update(hold=True, cause="battery", battery_since=now)
            _event(program, "hold", reason="battery")
            line = "HOLD on battery"
        else:
            memo["cause"] = "battery"  # a network hold that meets a battery waits for the settle time too
            line = "BATTERY hold kept"
    elif not ours:
        failed = [] if program.hold.exists() else probe()  # a HOLD someone else wrote is left alone
        if failed:
            program.hold.write_text("network: " + "; ".join(failed) + "\n", "utf-8")
            memo.update(hold=True, cause="network")
            _event(program, "hold", reason="network")
            line = "HOLD network: " + "; ".join(failed)
        else:
            line = "MAINS"
    elif memo.get("cause") == "network":
        failed = probe()
        if failed:
            line = "WAIT " + "; ".join(failed)
        else:
            program.hold.unlink(missing_ok=True)
            memo = {"hold": False}
            _event(program, "clear", reason="internet and GitHub back")
            line = "CLEAR hold removed; run recover before dispatching"
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


def hold(program: Program, why: str) -> list[str]:
    """`ship hold --why TEXT`: a manual HOLD. The conveyor and the build start nothing new while it is there; the
    power watch leaves it alone. Running workers finish their turn."""
    why = " ".join(why.split())
    if not why:
        raise ValueError("ship hold needs --why")
    program.dir.mkdir(parents=True, exist_ok=True)
    tmp = program.hold.with_name("HOLD.tmp")
    tmp.write_text(f"him: {why}\n", "utf-8", newline="\n")
    st.replace(tmp, program.hold)
    _event(program, "hold", reason="manual", why=why)
    return [f"HOLD {program.dir.name}: him: {why}"]


def release(program: Program) -> tuple[int, list[str]]:
    """`ship release`: removes a manual HOLD (0); a HOLD the power watch wrote is refused (1): it clears itself."""
    text = hold_text(program)
    if text is None:
        return 0, [f"CLEAR {program.dir.name} has no HOLD"]
    if watchers(text):
        return 1, [f"REFUSED the HOLD is the power watch's ({text.strip()[:120]}); it clears itself once mains, "
                   "the internet and GitHub are back"]
    program.hold.unlink(missing_ok=True)
    _event(program, "clear", reason="manual release")
    return 0, [f"RELEASED {program.dir.name}: {text.strip()[:120]}"]


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
