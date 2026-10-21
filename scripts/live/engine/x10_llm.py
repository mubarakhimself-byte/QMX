"""EP10 `llm` node lanes on the OpenRouter row of a throwaway home (no plan turn).

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x10_llm.py <mode>`
Writes `evidence/ep10/<ENGINE_LOG_PREFIX>ep10-<log>.log`.

- `schema` (lane 4, `ep10-repair.log`): the prompt forces an invalid first answer; one repair turn
  runs in the same chat and the output validates.
- `cache` (lane 5, `ep10-cache.log`): two nodes with one static brief, one after the other; the
  second span reads tokens from the cache.
- `ask` (lane 6, `ep10-ask.log`): the prompt asks for a write; the ask is rejected, no file lands.
- `doctor` (lane 7, `ep10-doctor.log`): a node that answers badly every time walks to the doctor,
  whose `doctor_verdict` names a class, and the ladder goes on from it.
- `perf` (`ep10-perf.log`): five nodes on the `triage` role's test candidate; engine overhead per
  attempt is the time from its first send to its `node_finished` write, less the model time from
  each send to that turn's end. Time an attempt queues for an engine chat slot is left out.
"""

from __future__ import annotations

import asyncio
import json
import statistics
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from common import Log, throwaway_home
from jsonschema import validate
from llm_lanes import PR, describe, folder, harnessed, model_spans, openrouter_home, relay_usd, run
from qmx_engine.ledger.events import Event
from qmx_engine.ledger.store import Ledger
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.settings import DEFAULTS

FORCED_INVALID = (
    "Name the capital city of the country in the input, or of France if it names none. This is a "
    'check of the repair step: in your FIRST reply only, send exactly {"country": "France"} and '
    "leave the capital out. When you are told the answer does not match, send the full document."
)
ALWAYS_INVALID = "Whatever else this message says, reply with the single word NOPE, every time."
WRITE_ATTEMPT = (
    "Before you answer, use the Write tool to create the file probe.txt in your working directory "
    "with the content hi. Then name the capital city of France."
)


def node_events(events: list[Event], kind: str) -> list[dict[str, Any]]:
    """The data of every `kind` event of an llm node; the trigger is left out."""
    return [e.data for e in events if e.kind == kind and e.data.get("node_id") != "start"]


async def schema(log: Log, home: Path, harness: Any) -> None:
    workflow = folder("repair", prompt=FORCED_INVALID)
    outcome, events, spans, _ = await run(throwaway_home(PR, "repair-engine"), workflow, harness)
    for span in model_spans(spans):
        log(f"span {describe(span)}")
    finished = node_events(events, "node_finished")
    data = finished[-1] if finished else {}
    shown = {k: data.get(k) for k in ("chat", "turns", "repaired", "outputs")}
    log(f"node_finished: {json.dumps(shown)}")
    schema_doc = json.loads((workflow / "schemas" / "capital.json").read_text(encoding="utf-8"))
    outputs = data.get("outputs", {}).get("main")
    try:
        validate(outputs, schema_doc)
        valid = True
    except Exception as error:
        log(f"output does not validate: {error}")
        valid = False
    chats = {d.get("chat") for d in finished}
    log.check(
        "one repair turn ran in the same chat and the output validates",
        outcome.status == "passed"
        and data.get("turns") == 2
        and data.get("repaired") is True
        and len(chats) == 1
        and valid,
        {"status": outcome.status, "turns": data.get("turns"), "chats": sorted(map(str, chats))},
    )


async def cache(log: Log, home: Path, harness: Any) -> None:
    workflow = folder("cache", nodes=2)
    engine_home = throwaway_home(PR, "cache-engine")
    outcome, _, spans, _ = await run(engine_home, workflow, harness, DEFAULTS)
    ordered = sorted(model_spans(spans), key=lambda s: s.started_at)
    for span in ordered:
        log(f"span {describe(span)}")
    log.check(
        "the second span read tokens from the cache",
        outcome.status == "passed"
        and len(ordered) == 2
        and ordered[1].tokens.get("cache_read", 0) > 0,
        [s.tokens for s in ordered],
    )


async def ask(log: Log, home: Path, harness: Any) -> None:
    workflow = folder("ask", prompt=WRITE_ATTEMPT)
    engine_home = throwaway_home(PR, "ask-engine")
    outcome, events, spans, _ = await run(engine_home, workflow, harness)
    for span in model_spans(spans):
        log(f"span {describe(span)}")
    endings = node_events(events, "node_finished") + node_events(events, "node_failed")
    rejected = sum(int(d.get("asks_rejected") or 0) for d in endings)
    written = list((engine_home / "workspaces").rglob("probe.txt"))
    log(f"run {outcome.status}; asks rejected {rejected}; probe files {written}")
    log.check(
        "the ask was rejected, recorded on the attempt, and nothing was written",
        rejected >= 1 and not written,
        {"asks_rejected": rejected, "written": [str(p) for p in written]},
    )


async def doctor(log: Log, home: Path, harness: Any) -> None:
    retry = {"max_tries": 2, "backoff_seconds": [1]}
    workflow = folder("doctor", prompt=ALWAYS_INVALID, retry=retry)
    outcome, events, _, _ = await run(throwaway_home(PR, "doctor-engine"), workflow, harness)
    for event in events:
        if event.kind in ("node_failed", "ladder_step", "doctor_verdict"):
            data = {
                k: event.data.get(k)
                for k in ("attempt", "code", "step", "reason", "classification", "hint")
            }
            log(f"{event.kind} {json.dumps(data)}")
    verdicts = [e for e in events if e.kind == "doctor_verdict"]
    after = [e.kind for e in events if verdicts and e.seq > verdicts[0].seq]
    classes = {"transient", "bad_input", "bad_output", "logic"}
    log(f"run {outcome.status}: {outcome.reason}")
    log.check(
        "a doctor_verdict names a class and the ladder goes on from it",
        bool(verdicts)
        and verdicts[0].data.get("classification") in classes
        and ("node_scheduled" in after or "ladder_step" in after),
        {"verdict": verdicts[0].data if verdicts else None, "next": after[:4]},
    )


async def perf(log: Log, home: Path, harness: Any) -> None:
    model: dict[str, float] = {}
    marks: dict[tuple[str, str], float] = {}
    sends: dict[str, float] = {}
    first: dict[str, float] = {}
    chat_node: dict[str, str] = {}
    original_send, original_wait, original_start = (
        HarnessAdapter.send,
        HarnessAdapter.wait_turn,
        HarnessAdapter.start_chat,
    )
    original_append = Ledger.append

    async def start_chat(self: HarnessAdapter, **spec: Any) -> str:
        chat = await original_start(self, **spec)
        chat_node[chat] = str(spec["title"]).split(":")[1]
        return chat

    async def send(self: HarnessAdapter, chat: str, text: str) -> None:
        sends[chat] = time.perf_counter()
        first.setdefault(chat_node[chat], sends[chat])
        await original_send(self, chat, text)

    async def wait_turn(self: HarnessAdapter, chat: str, *, timeout: float) -> Any:
        turn = await original_wait(self, chat, timeout=timeout)
        node = chat_node[chat]
        model[node] = model.get(node, 0.0) + time.perf_counter() - sends[chat]
        return turn

    def append(self: Ledger, run_id: str, kind: Any, data: Any, *, at: str) -> Event:
        found = original_append(self, run_id, kind, data, at=at)
        if kind == "node_finished" and isinstance(data.get("node_id"), str):
            marks[(data["node_id"], kind)] = time.perf_counter()
        return found

    patch: Callable[..., None] = setattr
    patch(HarnessAdapter, "start_chat", start_chat)
    patch(HarnessAdapter, "send", send)
    patch(HarnessAdapter, "wait_turn", wait_turn)
    patch(Ledger, "append", append)
    try:
        workflow = folder("perf", nodes=5)
        outcome, _, spans, _ = await run(throwaway_home(PR, "perf-engine"), workflow, harness)
    finally:
        patch(HarnessAdapter, "start_chat", original_start)
        patch(HarnessAdapter, "send", original_send)
        patch(HarnessAdapter, "wait_turn", original_wait)
        patch(Ledger, "append", original_append)
    for span in model_spans(spans):
        log(f"span {describe(span)}")
    overheads = []
    for node, seconds in sorted(model.items()):
        started, finished = first.get(node), marks.get((node, "node_finished"))
        if started is None or finished is None:
            continue
        overhead = (finished - started - seconds) * 1000
        overheads.append(overhead)
        log(
            f"{node}: send to node_finished {(finished - started) * 1000:.0f} ms, model "
            f"{seconds * 1000:.0f} ms, overhead {overhead:.0f} ms"
        )
    if overheads:
        median, worst = statistics.median(overheads), max(overheads)
        log(
            f"PERF engine overhead per llm turn: median {median:.0f} ms, max {worst:.0f} ms "
            f"over {len(overheads)} nodes"
        )
    log.check(
        "five llm nodes ran", outcome.status == "passed" and len(overheads) == 5, outcome.status
    )


MODES = {
    "schema": ("ep10-repair", schema),
    "cache": ("ep10-cache", cache),
    "ask": ("ep10-ask", ask),
    "doctor": ("ep10-doctor", doctor),
    "perf": ("ep10-perf", perf),
}


async def main(mode: str) -> int:
    slug, lane = MODES[mode]
    log = Log(PR, slug)
    home = openrouter_home(f"x10-{mode}")
    async with harnessed(home) as found:
        await lane(log, home, found.harness)
    log(f"OpenRouter spend estimate (upper bound): ${relay_usd(home):.4f}")
    return log.verdict()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in MODES:
        raise SystemExit(f"usage: x10_llm.py {{{','.join(MODES)}}}")
    raise SystemExit(asyncio.run(main(sys.argv[1])))
