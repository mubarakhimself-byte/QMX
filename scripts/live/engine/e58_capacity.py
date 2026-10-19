"""CAPX lanes for E58 (AD-58): capacity per resource class, one chat-slot counter.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e58_capacity.py <lane>`
Lanes are `e58 reserve priority script table yield`. Each writes
`D:/QMX-worktrees/qma-ship/build/evidence/capx/<ENGINE_LOG_PREFIX>capx-<lane>.log` and exits 1 when
a check failed.

- `e58`: 40 rule nodes, 2 x `cpu_slots` one-second scripts and 12 agent chunks on the fake model
  (a key row on a throwaway home, every turn held 2 s). PASS when every rule ends before any script
  or chunk, the scripts run `cpu_slots` at once, and the Background chats never hold more than the
  slot table less the reserve, and do reach it. It prints the run's wall time for the perf block.
  It also runs at the parent commit, where it reads no slot table.
- `reserve`: the ship home under the lane lock, on `claude/haiku`. Background chats fill every slot
  but the reserve and one more waits; an Interactive chat then starts at once. The ship home's
  `settings.toml` is hashed before and after and must not change.
- `priority`: one CPU slot held by a 2 s script; a priority 1 run, then a priority 5 run, queue
  behind it. PASS when the priority 5 run's script starts first.
- `script`: a CPU-bound backtest-shaped script beside 10 rules on one CPU slot. PASS when the rules
  end before the script.
- `table`: the derived capacity table on this machine against its cores and RAM.
- `yield`: a priority 0 fan-out of 6 script chunks on one CPU slot, then a priority 5 run. PASS when
  the priority 5 script starts before the fan-out's remaining chunks.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path
from textwrap import dedent
from typing import Any, Final

from common import LIVE_QMA, SHIP_HOME, Log, boot, lane_lock, live, opened

sys.path.append(str(LIVE_QMA))
os.environ.setdefault("QMA_LIVE_SCRATCH", "D:/QMX-worktrees/qma-ship/build/homes/capx-scratch")

from qmx_engine.definition.model import Workflow
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.runner import Engine, Outcome
from qmx_engine.settings import DEFAULTS

STORE: Final = Path("D:/QMX-worktrees/qma-ship/build")
EVIDENCE: Final = STORE / "evidence" / "capx"
RULES: Final = 40
CHUNKS: Final = 12
HOLD_S: Final = 2.0
CARD: Final = '{"seen": 1}'
SCHEMA: Final = {
    "type": "object",
    "required": ["seen"],
    "properties": {"seen": {"type": "integer"}},
}
TIMED: Final = """
    import json, time
    began = time.time()
    time.sleep({seconds})
    print(json.dumps([began, time.time()]))
"""
BACKTEST: Final = """
    import json, time
    began = time.time()
    total = 0
    while time.time() - began < 3:
        total += sum(i * i for i in range(10_000))
    print(json.dumps([began, time.time()]))
"""


class CapxLog(Log):
    """`Log` writing into the build store's `evidence/capx/`."""

    def __init__(self, slug: str) -> None:
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        self.path = EVIDENCE / f"{os.environ.get('ENGINE_LOG_PREFIX', '')}capx-{slug}.log"
        self.path.write_text("", encoding="utf-8")
        self.passed = True


def home(slug: str) -> Path:
    root = STORE / "homes" / f"capx-{slug}"
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    return root


def node(node_id: str, kind: str, role: str | None = None, **parameters: Any) -> dict[str, Any]:
    found: dict[str, Any] = {
        "id": node_id,
        "name": node_id,
        "type": kind,
        "typeVersion": 1,
        "parameters": parameters,
    }
    return found | ({"role": role} if role is not None else {})


def edge(target: str, map_: str = "one", **extra: Any) -> dict[str, Any]:
    return {"node": target, "port": "in", "map": map_, **extra}


def folder(
    root: Path,
    nodes: list[dict[str, Any]],
    connections: dict[str, dict[str, list[dict[str, Any]]]],
    files: dict[str, str],
) -> Path:
    document = {
        "schema": "qmx.workflow/1",
        "id": root.name,
        "name": root.name,
        "nodes": nodes,
        "connections": {
            source: {port: [targets] for port, targets in ports.items()}
            for source, ports in connections.items()
        },
    }
    root.mkdir(parents=True, exist_ok=True)
    (root / "definition.json").write_text(json.dumps(document, indent=2), encoding="utf-8")
    for path, text in files.items():
        (root / path).parent.mkdir(parents=True, exist_ok=True)
        (root / path).write_text(dedent(text), encoding="utf-8")
    return root


def runnable(root: Path) -> tuple[Any, Workflow]:
    found = checked(root)
    if isinstance(found, list):
        raise SystemExit(f"BLOCKED: {root} does not validate: {found}")
    return found


def events(engine_home: Path, run_id: str) -> list[Event]:
    with Reader.open(engine_home) as reader:
        return reader.events(run_id)


def finished(found: list[Event]) -> list[str]:
    return [str(e.data.get("node_id")) for e in found if e.kind == "node_finished"]


def most_at_once(spans: list[tuple[float, float]]) -> int:
    moments = sorted([(b, 1) for b, _ in spans] + [(e, -1) for _, e in spans])
    running, most = 0, 0
    for _, step in moments:
        running += step
        most = max(most, running)
    return most


def script_spans(outcome: Outcome, names: list[str]) -> list[tuple[float, float]]:
    outputs: Any = outcome.outputs or {}
    return [tuple(outputs[name]["main"]) for name in names]  # type: ignore[misc]


def cpu_slots() -> int:
    return (os.cpu_count() or 2) - 1


async def e58(log: Log) -> None:
    from fake_model import FakeModel, Turn, text  # noqa: PLC0415
    from qma.harness import TestMode  # noqa: PLC0415

    boot()
    live.use_fake_key()
    chat_home, engine_home = home("e58"), home("e58-engine")
    scripts = [f"a{n}" for n in range(2 * cpu_slots())]
    rules = [f"r{n}" for n in range(RULES)]
    root = folder(
        home("e58-wf"),
        [
            node("start", "trigger"),
            *(node(name, "script", script="scripts/timed.py") for name in scripts),
            *(node(name, "rule", expr="1 == 1") for name in rules),
            node(
                "read",
                "agent",
                "reader",
                brief_ref="brief.md",
                output_schema_ref="out.json",
                tools=[],
            ),
        ],
        {
            "start": {
                "main": [
                    *(edge(name) for name in scripts),
                    edge("read", "chunk", chunk={"by": "items", "size": 1}),
                    *(edge(name) for name in rules),
                ]
            }
        },
        {
            "brief.md": "Count the items you are given.",
            "out.json": json.dumps(SCHEMA),
            "scripts/timed.py": TIMED.format(seconds=1.0),
        },
    )
    found = runnable(root)
    fake = FakeModel([Turn([text(CARD)]) for _ in range(200)])
    answer = fake.next_turn

    def held(scripted: bool, request: dict[str, Any] | None = None) -> Any:
        if scripted:
            time.sleep(HOLD_S)
        return answer(scripted, request)

    fake.next_turn = held  # type: ignore[method-assign]
    fake.start()
    live.put_providers(chat_home, {"fake": live.fake_row(fake.url)})
    settings = {**DEFAULTS, "roles.reader": ("fake/fake-model",)}
    peak: dict[str, int] = {"unattended": 0, "held": 0, "waiting": 0}
    table: Any = None
    try:
        async with opened(chat_home, test=TestMode(loopback_http_provider=True)) as h:
            reading = getattr(h.harness, "slot_table", None)

            async def sample() -> None:
                nonlocal table
                while True:
                    if reading is not None:
                        table = reading()
                        peak["unattended"] = max(peak["unattended"], len(table.unattended))
                        peak["held"] = max(peak["held"], len(table.held))
                        peak["waiting"] = max(peak["waiting"], len(table.waiting))
                    await asyncio.sleep(0.05)

            sampler = asyncio.create_task(sample())
            began = time.perf_counter()
            with Ledger.open(engine_home) as ledger:
                engine = Engine(
                    engine_home, ledger, settings=settings, harness=HarnessAdapter(h.harness)
                )
                outcome = await engine.start(
                    root, found[1], mode="live", inputs=[{"id": n} for n in range(CHUNKS)]
                )
            wall = time.perf_counter() - began
            sampler.cancel()
    finally:
        fake.stop()
    found_events = events(engine_home, outcome.run_id)
    ended = finished(found_events)
    log(f"run {outcome.run_id}: {outcome.status} {outcome.reason or ''}")
    log(f"PERF wall seconds {wall:.2f}")
    log.check("the run passed", outcome.status == "passed", outcome.status)
    chunks = [e for e in found_events if e.kind == "node_finished" and e.data["node_id"] == "read"]
    log.check(f"all {CHUNKS} chunks finished", len(chunks) == CHUNKS, len(chunks))
    first_other = min(i for i, name in enumerate(ended) if name in scripts or name == "read")
    late = [name for name in ended[first_other:] if name in rules]
    log.check("no rule waited: every rule ended before any script or chunk", late == [], late)
    most = most_at_once(script_spans(outcome, scripts))
    log.check(f"scripts ran cpu_slots ({cpu_slots()}) at once", most == cpu_slots(), most)
    if table is None:
        log("this commit has no slot table reading; the chat checks are skipped")
        return
    own = table.capacity - table.reserve
    log(f"slot table: capacity {table.capacity}, reserve {table.reserve}; peaks {peak}")
    log.check(
        "Background chats never held more than the table less the reserve",
        peak["unattended"] <= own,
        f"{peak['unattended']} of {own}",
    )
    log.check("the chunks filled the unattended slots", peak["unattended"] == own, peak)
    log.check("chunks waited in the harness slot table", peak["waiting"] > 0, peak["waiting"])


def settings_sha() -> str:
    return hashlib.sha256((SHIP_HOME / "settings.toml").read_bytes()).hexdigest()


STORY: Final = (
    "Write a 1500-word story about a lighthouse keeper named {name}. Plain prose, no headings."
)


async def reserve(log: Log) -> None:
    from qma.harness import Background, InjectedText, NewChat, OperatorText  # noqa: PLC0415

    boot()
    live.require_login(log)
    before = settings_sha()
    log(f"ship home settings.toml sha256 before: {before}")
    ws = home("reserve-ws")
    with lane_lock(log):
        async with opened(SHIP_HOME) as h:
            harness = h.harness
            table = harness.slot_table()
            own = table.capacity - table.reserve
            log(f"slot table: capacity {table.capacity}, reserve {table.reserve}; {own} for work")
            chats = []
            for n in range(own + 1):
                spec = NewChat(
                    title=f"capx reserve {n}",
                    model="haiku",
                    workspace=ws,
                    kind=Background(),
                    tools=(),
                )
                chats.append(await harness.start_chat(spec))
            sends = [
                asyncio.ensure_future(harness.send(c, InjectedText(STORY.format(name=f"K{n}"))))
                for n, c in enumerate(chats)
            ]
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                table = harness.slot_table()
                if len(table.unattended) == own and len(table.waiting) == 1:
                    break
                await asyncio.sleep(0.2)
            log(
                f"before the Interactive send: unattended {len(table.unattended)}, "
                f"waiting {table.waiting}"
            )
            log.check(
                "every slot but the reserve holds a Background chat and one more waits",
                len(table.unattended) == own and len(table.waiting) == 1,
                (len(table.unattended), len(table.waiting)),
            )
            operator = await harness.start_chat(
                NewChat(title="capx reserve operator", model="haiku", workspace=ws, tools=())
            )
            began = time.perf_counter()
            await harness.send(operator, OperatorText("Reply with the single word READY."))
            took = time.perf_counter() - began
            still = harness.slot_table().waiting
            log(f"the Interactive send returned after {took:.2f} s; still waiting {still}")
            log.check(
                "the Interactive chat started while a Background send still waited",
                len(still) == 1,
                still,
            )
            record = await h.wait_idle(str(operator))
            answer = [
                c.get("text")
                for kind, c in ((b.get("type"), b.get("content")) for b in h.blocks(str(operator)))
                if kind == "text" and isinstance(c, dict)
            ]
            log(f"Interactive turn {getattr(record, 'turn', None)}; text {answer[-1:]}")
            log.check(
                "the Interactive chat answered READY",
                bool(answer) and "READY" in str(answer[-1]).upper(),
                answer[-1:],
            )
            await asyncio.wait_for(asyncio.gather(*sends), 300)
            for chat in chats:
                await h.wait_idle(str(chat))
            for chat in [*chats, operator]:
                await harness.close_chat(chat)
    after = settings_sha()
    log(f"ship home settings.toml sha256 after: {after}")
    log.check("the ship home settings.toml is unchanged", before == after, after)


async def started_runs(engine: Engine, runs: list[tuple[Path, int, float]]) -> list[Outcome]:
    """Start each `(folder, priority, delay)` run after its delay, all on one engine."""

    async def one(root: Path, priority: int, delay: float) -> Outcome:
        await asyncio.sleep(delay)
        found = runnable(root)
        return await engine.start(root, found[1], mode="test", inputs=None, priority=priority)

    return list(await asyncio.gather(*(one(*run) for run in runs)))


def one_script(root: Path, seconds: float) -> Path:
    return folder(
        root,
        [node("start", "trigger"), node("work", "script", script="scripts/timed.py")],
        {"start": {"main": [edge("work")]}},
        {"scripts/timed.py": TIMED.format(seconds=seconds)},
    )


async def priority(log: Log) -> None:
    engine_home = home("priority-engine")
    blocker = one_script(home("priority-blocker"), 2.0)
    low, high = one_script(home("priority-1"), 0.2), one_script(home("priority-5"), 0.2)
    with Ledger.open(engine_home) as ledger:
        engine = Engine(engine_home, ledger, settings={**DEFAULTS, "placement.pc.cpu_slots": 1})
        done = await started_runs(engine, [(blocker, 0, 0.0), (low, 1, 0.3), (high, 5, 0.6)])
    began = {
        name: script_spans(outcome, ["work"])[0][0]
        for name, outcome in zip(("blocker", "priority 1", "priority 5"), done, strict=True)
    }
    log(f"statuses {[o.status for o in done]}; script start times {began}")
    log.check("every run passed", all(o.status == "passed" for o in done), [o.status for o in done])
    log.check(
        "the priority 5 run started first though it queued last",
        began["priority 5"] < began["priority 1"],
        f"{began['priority 1'] - began['priority 5']:.2f} s ahead",
    )


async def script(log: Log) -> None:
    rules = [f"r{n}" for n in range(10)]
    root = folder(
        home("script-wf"),
        [
            node("start", "trigger"),
            node("backtest", "script", script="scripts/backtest.py"),
            *(node(name, "rule", expr="1 == 1") for name in rules),
        ],
        {"start": {"main": [edge("backtest"), *(edge(name) for name in rules)]}},
        {"scripts/backtest.py": BACKTEST},
    )
    engine_home = home("script-engine")
    with Ledger.open(engine_home) as ledger:
        engine = Engine(engine_home, ledger, settings={**DEFAULTS, "placement.pc.cpu_slots": 1})
        (outcome,) = await started_runs(engine, [(root, 0, 0.0)])
    ended = finished(events(engine_home, outcome.run_id))
    log(f"run {outcome.status}; finish order {ended}")
    log.check("the run passed", outcome.status == "passed", outcome.status)
    log.check(
        "all 10 rules ended before the backtest script",
        all(ended.index(name) < ended.index("backtest") for name in rules),
        ended.index("backtest"),
    )


async def table(log: Log) -> None:
    import psutil  # noqa: PLC0415
    from qma.harness.launch import (  # noqa: PLC0415
        background_slots,
        live_chat_slots,
        machine_ram_mb,
        parse_budgets,
    )
    from qmx_engine.admission import Capacity  # noqa: PLC0415

    capacity = {name: slots.size for name, slots in Capacity.of(DEFAULTS).slots.items()}
    budgets = parse_budgets({})
    ram = machine_ram_mb()
    chats = live_chat_slots(budgets, ram)
    log(f"logical cores {os.cpu_count()}; RAM {ram} MB; physical cores {psutil.cpu_count(False)}")
    log(f"engine table {capacity}; gpu_slots unset")
    log(
        f"chat slots {chats}, reserve {budgets.interactive_reserve}, "
        f"Background {background_slots(budgets, ram)}"
    )
    log.check(
        "cpu_slots is the logical cores less one", capacity.get("cpu") == cpu_slots(), capacity
    )
    log.check(
        "container_slots is 3 and no gpu class",
        capacity.get("container") == 3 and "gpu" not in capacity,
        capacity,
    )
    log.check(
        "chat slots are floor((RAM - 4096) / 1536)",
        chats == max(1, (ram - 4096) // 1536),
        chats,
    )


async def fanout(log: Log) -> None:
    engine_home = home("yield-engine")
    low = folder(
        home("yield-low"),
        [node("start", "trigger"), node("work", "script", script="scripts/timed.py")],
        {"start": {"main": [edge("work", "chunk", chunk={"by": "items", "size": 1})]}},
        {"scripts/timed.py": TIMED.format(seconds=1.0)},
    )
    high = one_script(home("yield-high"), 0.2)
    found = runnable(low)
    with Ledger.open(engine_home) as ledger:
        engine = Engine(engine_home, ledger, settings={**DEFAULTS, "placement.pc.cpu_slots": 1})

        async def fan() -> Outcome:
            return await engine.start(low, found[1], mode="test", inputs=list(range(6)))

        low_run = asyncio.ensure_future(fan())
        (high_run,) = await started_runs(engine, [(high, 5, 1.5)])
        low_done = await low_run
    chunks = sorted(
        float(e.data["outputs"]["main"][0])  # type: ignore[index]
        for e in events(engine_home, low_done.run_id)
        if e.kind == "node_finished" and e.data.get("node_id") == "work"
    )
    high_began = script_spans(high_run, ["work"])[0][0]
    after = [b for b in chunks if b > high_began]
    log(
        f"low chunks began at {[round(b - chunks[0], 2) for b in chunks]}; "
        f"high at {high_began - chunks[0]:.2f}"
    )
    log.check(
        "both runs passed",
        (low_done.status, high_run.status) == ("passed", "passed"),
        (low_done.status, high_run.status),
    )
    log.check(
        "the fan-out yielded: its later chunks started after the high run",
        len(after) >= 3,
        len(after),
    )


LANES: Final = {
    "e58": e58,
    "reserve": reserve,
    "priority": priority,
    "script": script,
    "table": table,
    "yield": fanout,
}


def main() -> int:
    lane = sys.argv[1] if len(sys.argv) > 1 else "e58"
    log = CapxLog(lane)
    asyncio.run(LANES[lane](log))
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(main())
