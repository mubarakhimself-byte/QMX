"""CAPE lanes 3 and 4 (E43, engine half): nothing in the engine pauses or ends work on a usage
number.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/e43_no_caps.py [tokens] [clock] [haiku]`
None named runs all three. Each writes
`D:/QMX-worktrees/qma-ship/build/evidence/cape/<ENGINE_LOG_PREFIX>cape-<lane>.log`.

- `tokens` (lane 3, no model): two agent chunks on the scripted port, the fake provider, report
  600,000 tokens in all against a row with a 1M window. Pass when the run passes with no pause
  and no `needs_you`.
- `clock` (lane 3, no model): an agent attempt during which the engine's clock moves six hours,
  while the attempt keeps showing new tool calls. Pass when the run passes with no pause.
- `haiku` (lane 4): RS1 test-run with every role on `claude/haiku` through the plan login on the
  ship home, under the lane lock. Pass when it passes, its run records no limits and writes no
  limits line, and its spans carry no limit field. The ship home's `settings.toml` hashes the same
  before and after.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Final

from agent_lanes import settings_sha
from common import boot
from e41_stuck import (
    CARD,
    SETTINGS,
    BuildLog,
    Port,
    agent_folder,
    build_home,
    edge,
    node,
    playing,
)
from qmx_engine.definition.validate import checked
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.inbox_table import InboxTable, inbox_path
from qmx_engine.ledger.spans import Span
from qmx_engine.ledger.store import Ledger, Reader
from qmx_engine.ports.harness_adapter import Turn
from qmx_engine.ports.library import Bundle
from qmx_engine.runner import Engine, Outcome
from t_templates import PACK, RUNNABLE, model_spans, save_and_test, services

WINDOW: Final = 1_000_000
CHUNK_TOKENS: Final = 300_000
LIMIT_WORDS: Final = ("runaway", "max_turns", "max_tool_calls", "run_seconds", "limits")


def chunked(home: Path) -> Path:
    root = agent_folder(home, "tokens")
    document = json.loads((root / "definition.json").read_text("utf-8"))
    document["connections"] = {
        "start": {"main": [[edge("fix", "chunk", chunk={"by": "items", "size": 1})]]},
        "fix": {"main": [[edge("all")]]},
    }
    document["nodes"].append(node("all", "join"))
    (root / "definition.json").write_text(json.dumps(document, indent=2), "utf-8")
    return root


async def drive(
    root: Path, port: Port, settings: dict[str, Any], wall: Any = None
) -> tuple[Outcome, list[Event]]:
    found = checked(root)
    if isinstance(found, list):
        raise SystemExit(f"BLOCKED: {root} does not validate: {found}")
    home = root.parent / f"engine-{root.name}"
    extra = {} if wall is None else {"wall": wall}
    with Ledger.open(home) as ledger:
        engine = Engine(home, ledger, settings=settings, harness=port, **extra)
        outcome = await engine.start(root, found[1], mode="test", inputs=[1, 2])
    with Reader.open(home) as reader:
        return outcome, reader.events(outcome.run_id)


def paused(events: list[Event]) -> list[Any]:
    return [e.data for e in events if e.kind in ("run_paused", "node_waiting")]


def tokens_lane() -> int:
    log = BuildLog("cape-e43")
    home = build_home("e43-tokens")

    async def big(port: Port, chat: str) -> Turn:
        return Turn(CARD, {"in": CHUNK_TOKENS - 1_000, "out": 1_000})

    port = Port(big, big)
    settings = {**SETTINGS, "context_window": WINDOW}
    outcome, events = asyncio.run(drive(chunked(home), port, settings))
    spent = sum(
        sum(v for v in e.data.get("tokens", {}).values() if isinstance(v, int))
        for e in events
        if e.kind == "node_finished" and e.data.get("node_id") == "fix"
    )
    log(f"tokens: {outcome.status} {outcome.reason or ''}; tokens reported {spent:,}")
    log.check(
        "two chunks reporting 600k tokens in all on a 1M-window row end passed, no pause",
        outcome.status == "passed" and spent == 2 * CHUNK_TOKENS and paused(events) == [],
        {"status": outcome.status, "tokens": spent, "paused": paused(events)},
    )
    engine_home = home / "engine-wf-tokens"
    items = []
    if inbox_path(engine_home).exists():
        with InboxTable.open(engine_home) as inbox:
            items = inbox.list_items(open_only=False)
    log.check(
        "no needs_you and no inbox item",
        items == [] and all("needs_you" not in json.dumps(e.data) for e in events),
        items,
    )
    clock_lane(log)
    return log.verdict()


def clock_lane(log: BuildLog) -> None:
    home = build_home("e43-clock")
    now = [datetime(2026, 10, 18, 6, 0, tzinfo=UTC)]
    reads = [
        [("Read", {"file_path": f"part-{n}.txt"}, f"part {n} of the report", False)]
        for n in range(12)
    ]
    show = playing(reads, answer=CARD)

    async def six_hours(port: Port, chat: str) -> Turn:
        mover = asyncio.ensure_future(move())
        try:
            return await show(port, chat)
        finally:
            mover.cancel()

    async def move() -> None:
        while True:
            await asyncio.sleep(0.25)
            now[0] += timedelta(minutes=30)

    outcome, events = asyncio.run(
        drive(agent_folder(home, "clock"), Port(six_hours), dict(SETTINGS), lambda: now[0])
    )
    first = next(e.at for e in events if e.kind == "run_created")
    last = events[-1].at
    hours = (datetime.fromisoformat(last) - datetime.fromisoformat(first)).total_seconds() / 3600
    log(f"clock: {outcome.status} {outcome.reason or ''}; recorded clock moved {hours:.1f} h")
    log.check(
        "a run whose clock moves six hours ends passed, with no pause and no stall",
        outcome.status == "passed" and hours >= 5.5 and paused(events) == [],
        {"status": outcome.status, "hours": round(hours, 1), "paused": paused(events)},
    )


def haiku_lane() -> int:
    log = BuildLog("cape-haiku")
    boot()
    template = next(t for t in RUNNABLE if t.id == "RS1")
    folder = PACK / str(template.folder)
    home = build_home("haiku-engine")
    before = settings_sha()
    log(f"ship home settings.toml sha256 before: {before}")

    async def go() -> Any:
        async with services(log, home, "plan") as service:
            with service() as svc:
                return await save_and_test(
                    svc, folder.name, Bundle.read(folder), template.test_inputs
                )

    report = asyncio.run(go())
    after = settings_sha()
    with Reader.open(home) as reader:
        events = reader.events(report.run_id)
    spans = model_spans(home, report.run_id)
    created = next(e.data for e in events if e.kind == "run_created")
    lines = [str(e.data.get("line")) for e in events if e.kind == "log"]
    names = {f.name for f in dataclasses.fields(Span)}
    fields = sorted(name for name in names if any(word in name for word in LIMIT_WORDS))
    log(f"RS1 {report.run_id}: {report.status} {report.reason or ''}")
    for span in spans:
        log(f"span {span.node_id} {span.status}: {span.profile}/{span.model} tokens {span.tokens}")
    log.check("RS1 on claude/haiku ends passed", report.status == "passed", report.status)
    log.check(
        "every model span ran on claude/haiku",
        bool(spans) and {(s.profile, s.model) for s in spans} == {("claude", "haiku")},
        sorted({f"{s.profile}/{s.model}" for s in spans}),
    )
    log.check(
        "the run records no limits, writes no limits line and its spans carry no limit field",
        created.get("limits") == {}
        and "runaway" not in created
        and not [line for line in lines if line.startswith(("limits", "runaway"))]
        and fields == [],
        {"limits": created.get("limits"), "fields": fields},
    )
    log.check("the ship home's settings.toml is unchanged", after == before, after)
    return log.verdict()


def main() -> int:
    lanes = sys.argv[1:] or ["tokens", "haiku"]
    failed = 0
    if "tokens" in lanes or "clock" in lanes:
        failed |= tokens_lane()
    if "haiku" in lanes:
        failed |= haiku_lane()
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
