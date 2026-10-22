"""E68: a provider 401 on a Contabo-homed run reaches the PC's inbox, and `retry` on the PC
resumes it on Contabo (AD-17, AD-21, AD-65).

Two homes stand in for the two machines: `contabo` runs the engine and serves the forwarding route
on a real socket; `pc` answers nothing and reads through it with a host pass. The 401 is a fake
provider refusal planted at the executor seam, which is the same boundary a real 401 arrives at,
so the engine classes it `auth` and raises the item by its own path.

Everything runs on one event loop, because a home's inbox table is bound to the thread that opened
it (one writer, AD-23), and both sides of this lane touch their own home.

Run from `qmx-agents/` with the agents venv:

    uv run --no-sync python ../scripts/live/server/e68_remote_inbox.py

Writes `<QMA_EVIDENCE_DIR>/owner-e68.log` (default
`D:/QMX-worktrees/qma-ship/build/evidence/ops2`) and exits 1 when a check failed.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import shutil
import time
from datetime import UTC, datetime
from pathlib import Path

import uvicorn
from fastapi import FastAPI

from qmx_engine.ledger.signature import signature
from qmx_engine.ledger.store import Reader
from qmx_engine.nodes.base import Failed, NodeJob, Ok
from qmx_engine.ports.library import Bundle
from qmx_engine.service.api import EngineService
from qmx_engine.service.context import OPERATOR
from qmx_engine.service.forward import Forwarder, Instance, forward_router
from qmx_engine.triggers.ticker import Scheduler
from qmx_host.streams import Streams

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
ITEMS = 5


class Refused401:
    """The provider refusing the key on every attempt: one `auth` failure per attempt."""

    def __init__(self) -> None:
        self.tries = 0

    def run(self, job: NodeJob) -> Failed:
        self.tries += 1
        message = "401 from the provider: the key was refused"
        return Failed("auth", message, signature("auth", message), False)


class Passing:
    """A passing attempt: the draft is tested and published on this, then the provider refuses."""

    def run(self, job: NodeJob) -> Ok:
        inputs = job.inputs if isinstance(job.inputs, dict) else {}
        return Ok({"main": inputs.get("in")})


async def wait_for(pc: EngineService, run_id: str, *, seconds: float) -> dict[str, object] | None:
    """The PC's merged inbox row for `run_id`, as soon as one appears."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        for row in pc.merged_inbox():
            if row.row.get("run_id") == run_id:
                return dict(row.row)
        await asyncio.sleep(0.05)
    return None


async def wait_until_stale(pc: EngineService, *, seconds: float):
    """The PC's rows once its held stream has reported the node gone."""
    deadline = time.monotonic() + seconds
    rows = pc.merged_inbox()
    while time.monotonic() < deadline:
        rows = pc.merged_inbox()
        if rows and all(row.stale for row in rows):
            return rows
        await asyncio.sleep(0.2)
    return rows


async def first_frame(forwarder: Forwarder, *, seconds: float) -> None:
    """Wait for the stream's first open set, so the timed items are measured after it lands."""
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline and "inbox.list" not in forwarder.down.streamed:
        await asyncio.sleep(0.05)


async def resumed_attempts(root: Path, run_id: str, *, seconds: float = 10.0) -> list[int]:
    """The attempts the run started, once the answered gate has resumed it."""
    deadline = time.monotonic() + seconds
    attempts: list[int] = []
    while time.monotonic() < deadline:
        with Reader.open(root) as reader:
            attempts = [
                int(str(event.data.get("attempt")))
                for event in reader.events(run_id)
                if event.kind == "node_started"
            ]
        if attempts and attempts[-1] >= 2:
            return attempts
        await asyncio.sleep(0.1)
    return attempts


async def lane(say, check, root: Path) -> None:
    with EngineService.open(
        root / "contabo",
        name="contabo",
        executors={"script": Passing(), "trigger": Passing()},
    ) as contabo:
        bundle = Bundle.read(CHAIN)
        draft = contabo.drafts.put(None, bundle, 0, caller=OPERATOR)
        await contabo.tests.run(draft.item, caller=OPERATOR)
        version = contabo.versions.publish(draft.item, "1.0.0", caller=OPERATOR)
        contabo.ctx.engine.executors = {"script": Refused401(), "trigger": Passing()}
        say("the provider now refuses the key on every attempt (fake 401)")

        app = FastAPI()
        app.include_router(forward_router(contabo.remote(), KEY))
        server = uvicorn.Server(
            uvicorn.Config(app, host="127.0.0.1", port=0, log_level="error")
        )
        serving = asyncio.create_task(server.serve())
        while not server.started:
            await asyncio.sleep(0.02)
        port = int(server.servers[0].sockets[0].getsockname()[1])
        url = f"http://127.0.0.1:{port}"
        say(f"the Contabo home serves forwarding at {url}")

        try:
            with EngineService.open(root / "pc", name="pc") as pc:
                forwarder = Forwarder(
                    Instance("contabo", url), key=KEY, source="pc", principal="operator"
                )
                pc.watching(name="pc", forwarders=[forwarder])
                streams = Streams.of(pc.forwarders)
                holding = [asyncio.create_task(streams.hold_all())]
                say("the PC holds one stream from Contabo")
                await first_frame(forwarder, seconds=10.0)
                latencies: list[float] = []
                try:
                    for index in range(ITEMS):
                        run = await contabo.runs.start(version, caller=OPERATOR)
                        raised = datetime.now(UTC)
                        found = await wait_for(pc, run.run_id, seconds=20.0)
                        if found is None:
                            check(False, f"item {index + 1} of {ITEMS} reached the PC inbox")
                            continue
                        latencies.append((datetime.now(UTC) - raised).total_seconds())
                        if index == 0:
                            say(json.dumps({"item": found}, sort_keys=True))

                    rows = pc.merged_inbox()
                    check(
                        len(rows) == ITEMS,
                        f"{ITEMS} provider 401 items raised on Contabo read in the PC inbox",
                    )
                    check(
                        all(row.home_engine == "contabo" and not row.stale for row in rows),
                        "every row names its home `contabo` and none is stale",
                    )
                    check(
                        all(row.row.get("category") == "provider_failure" for row in rows),
                        "every item is a provider failure, as a 401 must be",
                    )
                    if rows:
                        first = dict(rows[0].row)
                        with Reader.open(root / "contabo") as reader:
                            codes = {
                                str(event.data.get("code"))
                                for event in reader.events(str(first["run_id"]))
                                if event.kind == "node_failed"
                            }
                        check(codes == {"auth"}, f"the run failed `auth` ({codes})")

                        answer = dict(
                            await asyncio.to_thread(
                                pc.inbox.answer_forwarded,
                                str(first["id"]),
                                "retry",
                                caller=OPERATOR,
                            )
                        )
                        check(
                            answer.get("resolution") == "retry",
                            "the retry is recorded on the item by its own home",
                        )
                        with Reader.open(root / "contabo") as reader:
                            answers = [
                                event.data
                                for event in reader.events(str(first["run_id"]))
                                if event.kind == "gate_resolved"
                                and event.data.get("answer") == "retry"
                            ]
                        check(bool(answers), "Contabo's own ledger folded the retry")
                        scheduler = Scheduler(contabo.ctx, home="contabo")
                        await scheduler.tick()
                        await scheduler.settle()
                        say("Contabo's ticker took the answer's wake")
                        attempts = await resumed_attempts(root / "contabo", str(first["run_id"]))
                        check(
                            bool(attempts) and attempts[-1] >= 2,
                            f"the run resumed with a new attempt on Contabo ({sorted(set(attempts))})",
                        )
                        with Reader.open(root / "pc") as reader:
                            local = reader.events(str(first["run_id"]))
                        check(not local, "the PC's ledger holds no event of the Contabo run")

                    if latencies:
                        ordered = sorted(latencies)
                        p95 = ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))]
                        say(
                            "METRIC seconds from a Contabo inbox item to the PC inbox: "
                            + json.dumps(
                                {
                                    "items": len(latencies),
                                    "max": round(max(latencies), 2),
                                    "p95": round(p95, 2),
                                    "all": [round(found, 2) for found in latencies],
                                    "fail_line_s": 10,
                                },
                                sort_keys=True,
                            )
                        )
                        check(p95 <= 10.0, f"p95 {p95:.2f}s is inside the 10 s fail line")

                    open_rows = pc.merged_inbox()
                    say("unplugging Contabo: the PC can no longer reach it")
                    holding[0].cancel()
                    try:
                        await holding[0]
                    except asyncio.CancelledError:
                        pass
                    forwarder.instance = Instance("contabo", "http://127.0.0.1:1")
                    holding[0] = asyncio.create_task(streams.hold_all())
                    lost = await wait_until_stale(pc, seconds=30.0)
                    check(
                        bool(lost) and all(row.stale for row in lost),
                        f"rows read stale once Contabo is gone ({len(lost)} rows)",
                    )
                    check(
                        all(
                            str(row.row.get("detail", "")).startswith("server unreachable since")
                            for row in lost
                        ),
                        "every row says 'server unreachable since ...'",
                    )
                    check(
                        {(row.row.get("id"), row.row.get("run_id")) for row in lost}
                        == {(row.row.get("id"), row.row.get("run_id")) for row in open_rows},
                        "the last values are kept, not blanked",
                    )
                finally:
                    holding[0].cancel()
                    try:
                        await holding[0]
                    except asyncio.CancelledError:
                        pass
                    await streams.close()
        finally:
            server.should_exit = True
            await serving


def main() -> int:
    parser = argparse.ArgumentParser(prog="e68_remote_inbox")
    parser.add_argument("--root", type=Path, default=Path("D:/Temp/ops2-e68"))
    parser.add_argument("--evidence", type=Path, default=None)
    args = parser.parse_args()
    evidence = args.evidence or Path(
        os.environ.get("QMA_EVIDENCE_DIR", "D:/QMX-worktrees/qma-ship/build/evidence/ops2")
    )
    evidence.mkdir(parents=True, exist_ok=True)
    log = (evidence / "owner-e68.log").open("w", encoding="utf-8", buffering=1)
    root: Path = args.root
    shutil.rmtree(root, ignore_errors=True)
    checked: list[tuple[bool, str]] = []

    def say(line: str) -> None:
        print(line)
        log.write(line + "\n")

    def check(ok: bool, line: str) -> None:
        checked.append((ok, line))
        say(f"{'PASS' if ok else 'FAIL'} {line}")

    try:
        asyncio.run(lane(say, check, root))
    finally:
        good = sum(1 for ok, _ in checked if ok)
        say(f"E68 {good}/{len(checked)} checks passed")
        log.close()
    return 0 if all(ok for ok, _ in checked) else 1


if __name__ == "__main__":
    raise SystemExit(main())
