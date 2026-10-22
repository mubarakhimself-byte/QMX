"""E64: one pause switch, every host (AD-10, AD-65).

Two homes, `pc` and `contabo`, each with an enabled hourly trigger. The Hub is a real one on a
socket; the PC pushes its heartbeat row and the reply's `autonomy_paused` is the flag both homes
act on. With the flag set, one tick claims no fire on either host. Clearing it gives exactly one
catch-up per trigger, not a backlog. The lane also drives the five-minute rule: a host that stops
hearing from the Hub keeps the last flag it knew and says "pause state unknown".

Run from `qmx-agents/` with the agents venv:

    uv run --no-sync python ../scripts/live/server/e64_pause.py

Writes `<QMA_EVIDENCE_DIR>/owner-e64.log` (default
`D:/QMX-worktrees/qma-ship/build/evidence/ops2`) and exits 1 when a check failed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import threading
import time
from collections.abc import Mapping
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import cast

from qmx_engine.heartbeat import Heartbeat, HubLink
from qmx_engine.ledger import redact
from qmx_engine.ledger.store import Reader
from qmx_engine.nodes.base import NodeJob, Ok
from qmx_engine.ports.library import Bundle
from qmx_engine.ports.settings import SettingsPort
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.settings import DEFAULTS, Setting
from qmx_engine.triggers import rows
from qmx_engine.triggers.cron import Cron
from qmx_engine.triggers.ticker import Scheduler
from qmx_library.store import Store

from qmx_hub.server import Hub, serve

KEY = "pairing-key-of-this-lane"
CHAIN = (
    Path(__file__).resolve().parents[3]
    / "qmx-agents"
    / "packages"
    / "qmx-engine"
    / "tests"
    / "fixtures"
    / "workflows"
    / "script-chain"
)
T0 = datetime(2026, 10, 17, 9, 30, tzinfo=UTC)


class Clock:
    def __init__(self, now: datetime) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current

    def move(self, **step: float) -> None:
        self.current += timedelta(**step)


class Flags:
    """The settings one home reads at use, so the lane can set the switch mid-run."""

    def __init__(self, **initial: Setting) -> None:
        self.current: dict[str, Setting] = {**DEFAULTS, **initial}

    def set(self, **changed: Setting) -> None:
        self.current |= {key.replace("__", "."): value for key, value in changed.items()}

    def values(self) -> Mapping[str, Setting]:
        return self.current


class Passing:
    """The script chain's executor: every attempt returns its `in` value."""

    def run(self, job: NodeJob) -> Ok:
        inputs = job.inputs if isinstance(job.inputs, dict) else {}
        return Ok({"main": inputs.get("in")})


def home_of(name: str) -> Flags:
    return Flags(**{"autonomy.paused": 1 if name == "pc" else 0})


def prepare(
    root: Path, name: str, clock: Clock, flags: Flags
) -> tuple[object, EngineService, str]:
    """One home with one enabled version and one hourly trigger; returns the service and trigger."""
    service = EngineService.open(root / name, name=name, clock=clock, settings=flags)
    svc = service.__enter__()
    item = svc.drafts.put(None, Bundle.read(CHAIN), 0, caller=OPERATOR).item
    asyncio.run(svc.tests.run(item, caller=OPERATOR))
    version = svc.versions.publish(item, "1.0.0", caller=OPERATOR)
    svc.versions.enable(version, caller=OPERATOR)
    trigger = rows.create(
        svc.ctx.engine.ledger,
        workflow_item=svc.versions.get(version).item,
        pinned_object=version,
        spec=Cron("0 * * * *", "UTC"),
        caller=OPERATOR,
        now=clock.now(),
        home_engine=name,
    )
    return service, svc, trigger.id


def claimed(svc: EngineService, name: str) -> int:
    """One tick of this home's scheduler, settled before the next one."""

    async def go() -> int:
        scheduler = Scheduler(svc.ctx, home=cast("object", name))
        tick = await scheduler.tick()
        await scheduler.settle()
        return len(tick.claimed)

    return asyncio.run(go())


def heartbeat(paused: bool, name: str) -> Heartbeat:
    return Heartbeat(
        subject="host",
        id=name,
        at=datetime.now(UTC).isoformat(),
        cpu_seconds=1.0,
        rss_bytes=1024,
        machine_minutes=1.0,
        qmx_version="0.1.0",
        kinds_digest="digest",
        paused=paused,
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="e64_pause")
    parser.add_argument("--root", type=Path, default=Path("D:/Temp/ops2-e64"))
    parser.add_argument("--evidence", type=Path, default=None)
    args = parser.parse_args()
    evidence = args.evidence or Path(
        os.environ.get("QMA_EVIDENCE_DIR", "D:/QMX-worktrees/qma-ship/build/evidence/ops2")
    )
    evidence.mkdir(parents=True, exist_ok=True)
    log = (evidence / "owner-e64.log").open("w", encoding="utf-8", buffering=1)
    root: Path = args.root
    shutil.rmtree(root, ignore_errors=True)
    checked: list[tuple[bool, str]] = []

    def say(line: str) -> None:
        print(line)
        log.write(line + "\n")

    def check(ok: bool, line: str) -> None:
        checked.append((ok, line))
        say(f"{'PASS' if ok else 'FAIL'} {line}")

    opened: list[EngineService] = []
    server = None
    thread = None
    try:
        clock = Clock(T0)
        pc_flags, contabo_flags = home_of("pc"), home_of("contabo")
        pc_service, pc, pc_trigger = prepare(root, "pc", clock, pc_flags)
        opened.append(pc_service)
        contabo_service, contabo, contabo_trigger = prepare(root, "contabo", clock, contabo_flags)
        opened.append(contabo_service)

        with Store.open(root / "hub-store", redactor=redact, name="server") as store:
            hub_home = root / "hub-home"
            hub_home.mkdir(parents=True, exist_ok=True)
            server = serve(Hub(store, home=hub_home), host="127.0.0.1", port=0, key=KEY)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            url = f"http://127.0.0.1:{server.server_address[1]}"
            say(f"the Hub answers at {url}")

            pc_link = HubLink(url, KEY)
            contabo_link = HubLink(url, KEY)
            reply = pc_link.push(heartbeat(True, "pc"))
            check(reply.autonomy_paused is True, "the Hub's reply carries the PC's pause flag")
            contabo_link.push(heartbeat(True, "contabo"))
            for name, link, flags in (
                ("pc", pc_link, pc_flags),
                ("contabo", contabo_link, contabo_flags),
            ):
                flags.set(autonomy__paused=1 if link.pause.paused else 0)
                check(
                    link.pause.paused and link.pause.shows(time.time()) == "paused",
                    f"{name} acts on the Hub's flag, not its own",
                )

            clock.move(hours=1)
            fires = {name: claimed(svc, name) for name, svc in (("pc", pc), ("contabo", contabo))}
            check(
                fires == {"pc": 0, "contabo": 0},
                f"no fire is claimed on either host within one tick of pausing ({fires})",
            )

            cleared = pc_link.push(heartbeat(False, "pc"))
            contabo_link.push(heartbeat(False, "contabo"))
            check(cleared.autonomy_paused is False, "the Hub's reply carries the cleared flag")
            for flags in (pc_flags, contabo_flags):
                flags.set(autonomy__paused=0)
            clock.move(minutes=5)
            catch_up = {
                name: claimed(svc, name) for name, svc in (("pc", pc), ("contabo", contabo))
            }
            check(
                catch_up == {"pc": 1, "contabo": 1},
                f"clearing gives exactly one catch-up per trigger ({catch_up})",
            )
            with Reader.open(root / "pc") as reader:
                pc_fires = rows.fires(reader.connection, pc_trigger)
            with Reader.open(root / "contabo") as reader:
                contabo_fires = rows.fires(reader.connection, contabo_trigger)
            check(
                len(pc_fires) == 1 and len(contabo_fires) == 1,
                f"one fire row each, no backlog ({len(pc_fires)}, {len(contabo_fires)})",
            )
            check(
                not [fire for fire in pc_fires + contabo_fires if fire.status == "skipped"],
                "no occurrence was skipped as downtime",
            )

        moment = {"now": 1_000.0}
        heard = HubLink(
            url,
            KEY,
            clock=lambda: moment["now"],
            post=lambda _url, _body, _headers: {"autonomy_paused": True, "claims_renewed": 0},
        ).push(heartbeat(True, "pc"))
        dark = HubLink(url, KEY, clock=lambda: moment["now"] + 300.0)
        dark.pause = dark.pause.heard(heard, at=moment["now"])
        check(
            dark.pause.shows(moment["now"] + 299.0) == "paused"
            and dark.pause.shows(moment["now"] + 300.0) == "pause state unknown"
            and dark.pause.flag(moment["now"] + 300.0) is True,
            "five minutes without the Hub shows `pause state unknown` and keeps the flag",
        )
    finally:
        for svc in opened:
            svc.__exit__(None, None, None)
        if server is not None:
            server.shutdown()
            server.server_close()
        if thread is not None:
            thread.join(timeout=5)
        good = sum(1 for ok, _ in checked if ok)
        say(f"E64 {good}/{len(checked)} checks passed")
        log.close()
    return 0 if all(ok for ok, _ in checked) else 1


if __name__ == "__main__":
    raise SystemExit(main())
