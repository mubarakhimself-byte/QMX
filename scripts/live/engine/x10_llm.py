"""EP10 `llm` node lanes on the OpenRouter row of a throwaway home, and one plan lane on haiku.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x10_llm.py <mode>`
Writes `evidence/ep10/<ENGINE_LOG_PREFIX>ep10-<log>.log`.

- `schema` (lane 4, `ep10-repair.log`): the prompt forces an invalid first answer; one repair turn
  runs in the same chat and the output validates.
- `cache` (lane 5, `ep10-cache.log`): two nodes with one static brief, one after the other; the
  second span reads tokens from the cache.
- `ask` (lane 6, `ep10-ask.log`): the prompt asks for a write; the chat has no tool, so nothing
  runs and no file lands.
- `doctor` (lane 7, `ep10-doctor.log`): a node that answers badly every time walks to the doctor,
  whose `doctor_verdict` names a class, and the ladder goes on from it.
- `plan` (TURN-E lane 2, `ep10-plan.log`): two chained `llm` nodes on `claude/haiku` through the
  ship home's plan login, under the lane lock. The prompt asks for the Read and Write tools; the
  chats have none, so no tool runs, each answer validates, and the second reads the cache.
- `perf` (`ep10-perf.log`): five nodes on the `triage` role's test candidate; engine overhead per
  attempt is the time from its first send to its `node_finished` write, less the model time from
  each send to that turn's end. Time an attempt queues for an engine chat slot is left out.
"""

from __future__ import annotations

import asyncio
import json
import os
import psutil
import statistics
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final

from common import Log, plan_harness, throwaway_home
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
TOOL_BAIT = (
    "Before you answer, use the Read tool to read definition.json and the Write tool to create "
    "probe.txt with the content hi. Then name the capital city of the country in the input, or of "
    "France if it names none."
)
HAIKU = {**DEFAULTS, "roles.triage": ("claude/haiku",), "roles.doctor": ("claude/haiku",)}
ALWAYS_INVALID = "Whatever else this message says, reply with the single word NOPE, every time."
WRITE_ATTEMPT = (
    "Before you answer, use the Write tool to create the file probe.txt in your working directory "
    "with the content hi. Then name the capital city of France."
)
DEEPSEEK: Final = "openrouter/deepseek/deepseek-v4.1-flash"
"""The OpenRouter registry row, the cheapest and the one the plan names (RTR5 lane 4)."""
DEEPSEEK_SETTINGS: dict[str, Any] = {
    **DEFAULTS,
    "roles.triage": (DEEPSEEK,),
    "roles.test_only": (DEEPSEEK,),
}


def adopt_relay(harness: Any) -> Any:
    """Adopt the harness's relay as this process's router, or None on a tree without RTR5."""
    try:
        from qmx_engine.ports.router import adopt  # noqa: PLC0415
        from qmx_host.host import RelayRouter, harness_relay  # noqa: PLC0415
    except ImportError:
        return None
    port = RelayRouter(harness_relay(harness))
    adopt(port)
    return port


def cli_children() -> list[str]:
    """Every child process of this one, by name: a CLI chat leaves a `claude` here."""
    return [child.name() for child in psutil.Process().children(recursive=True)]


def tree_rss() -> int:
    """This process and every child, in bytes, as the parent's fan-out is charged."""
    me = psutil.Process()
    total = me.memory_info().rss
    for child in me.children(recursive=True):
        try:
            total += child.memory_info().rss
        except psutil.Error:
            continue
    return total


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
    tools = [e.data for e in events if e.kind == "tool_called"]
    written = list((engine_home / "workspaces").rglob("probe.txt"))
    log(f"run {outcome.status}; asks rejected {rejected}; probe files {written}")
    log.check(
        "the tool-less chat ran no tool and nothing was written",
        not tools and not written,
        {"tools": tools, "written": [str(p) for p in written]},
    )


def chained(slug: str, prompt: str) -> Path:
    """Two `llm` nodes, the second fed by the first, so the second starts after the first."""
    workflow = folder(slug, prompt=prompt, nodes=2)
    path = workflow / "definition.json"
    document = json.loads(path.read_text(encoding="utf-8"))
    start, first, second = document["nodes"]
    document["connections"] = {
        start["name"]: {"main": [[{"node": first["name"], "port": "in", "map": "one"}]]},
        first["name"]: {"main": [[{"node": second["name"], "port": "in", "map": "one"}]]},
    }
    path.write_text(json.dumps(document, indent=2), encoding="utf-8")
    return workflow


async def plan(log: Log, found: Any) -> None:
    workflow = chained("plan", TOOL_BAIT)
    schema_doc = json.loads((workflow / "schemas" / "capital.json").read_text(encoding="utf-8"))
    outcome, events, spans, _ = await run(
        throwaway_home(PR, "plan-engine"), workflow, found.harness, HAIKU, mode="live"
    )
    ordered = sorted(model_spans(spans), key=lambda s: s.started_at)
    for span in ordered:
        log(f"span {describe(span)}")
    finished = node_events(events, "node_finished")
    chats = [str(d.get("chat")) for d in finished]
    blocks = {chat: found.blocks(chat) for chat in chats}
    tool_blocks = [
        b for found_blocks in blocks.values() for b in found_blocks if b["type"] == "tool"
    ]
    asks = [
        b for found_blocks in blocks.values() for b in found_blocks if b["type"] == "permission"
    ]
    tools = [e.data for e in events if e.kind == "tool_called"]
    valid = []
    for data in finished:
        try:
            validate(data.get("outputs", {}).get("main"), schema_doc)
            valid.append(True)
        except Exception as error:
            log(f"output does not validate: {error}")
            valid.append(False)
    log(f"run {outcome.run_id}: {outcome.status} {outcome.reason or ''}; chats {chats}")
    log(f"outputs: {[d.get('outputs') for d in finished]}")
    log.check(
        "both plan-row llm nodes ran on claude/haiku and passed",
        outcome.status == "passed"
        and [(s.profile, s.model, s.status) for s in ordered] == [("claude", "haiku", "ok")] * 2,
        [(s.profile, s.model, s.status) for s in ordered],
    )
    log.check(
        "no tool ran and no ask was raised in either chat, though the prompt asked for two",
        not tool_blocks and not asks and not tools,
        {"tool_blocks": len(tool_blocks), "asks": len(asks), "tool_called": len(tools)},
    )
    log.check("each answer validates against the node's schema", valid == [True, True], valid)
    log.check(
        "the second chained node read tokens from the cache",
        len(ordered) == 2 and ordered[1].tokens.get("cache_read", 0) > 0,
        [s.tokens for s in ordered],
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


async def complete(log: Log, home: Path, harness: Any) -> None:
    """RTR5 lane 4: one `llm` node on the OpenRouter DeepSeek row goes through `complete` with no
    CLI process, and its span carries the router's own row, account and session."""
    adopt_relay(harness)
    before = cli_children()
    try:
        outcome, events, spans, _ = await run(
            throwaway_home(PR, "complete-engine"),
            folder("complete"),
            harness,
            DEEPSEEK_SETTINGS,
        )
    finally:
        from qmx_engine.ports.router import adopt  # noqa: PLC0415

        adopt(None)
    after = cli_children()
    turns = model_spans(spans)
    for span in turns:
        log(f"span {describe(span)}")
    finished = node_events(events, "node_finished")
    router = finished[-1].get("router") if finished else None
    log(f"node_finished router: {json.dumps(router)}")
    log.check(
        "the llm node ran on the OpenRouter DeepSeek row, with no chat",
        outcome.status == "passed"
        and [(s.profile, s.model, s.status) for s in turns]
        == [("openrouter", "deepseek/deepseek-v4.1-flash", "ok")],
        [(s.profile, s.model, s.status, s.tokens) for s in turns],
    )
    log.check(
        "the span carries the router's journal id, account and session",
        isinstance(router, dict)
        and router.get("qmx_id") == DEEPSEEK
        and isinstance(router.get("account"), str)
        and str(router.get("session", "")).endswith(":capital"),
        router,
    )
    log.check(
        "no CLI process started for the call",
        before == after and not any("claude" in name for name in before + after),
        {"before": before, "after": after},
    )
    log(f"OpenRouter spend estimate (upper bound): ${relay_usd(home):.4f}")


async def fanout(log: Log, home: Path, harness: Any) -> None:
    """RTR5's perf block: the peak RSS of a 20-call `llm` fan-out on a key row. At this head every
    call is `complete`; the parent runs the same fan-out with one CLI per call."""
    port = adopt_relay(harness)
    peak = [0]

    def sample() -> None:
        while not stop.is_set():
            peak[0] = max(peak[0], tree_rss())
            stop.wait(0.05)

    stop = threading.Event()
    watcher = threading.Thread(target=sample, daemon=True)
    watcher.start()
    try:
        outcome, _, spans, _ = await run(
            throwaway_home(PR, "perf-engine"),
            folder("perf", nodes=20),
            harness,
            DEEPSEEK_SETTINGS,
        )
    finally:
        stop.set()
        watcher.join()
        if port is not None:
            from qmx_engine.ports.router import adopt  # noqa: PLC0415

            adopt(None)
    turns = model_spans(spans)
    log(
        f"PERF peak RSS {peak[0] / 1e6:.0f} MB (pid {os.getpid()}) over {len(turns)} llm calls on "
        f"{DEEPSEEK}; router {'on' if port is not None else 'off, one CLI per call'}"
    )
    log.check(
        "20 llm calls answered on the key row",
        outcome.status == "passed" and len(turns) == 20,
        (outcome.status, len(turns)),
    )
    log(f"OpenRouter spend estimate (upper bound): ${relay_usd(home):.4f}")


MODES = {
    "schema": ("ep10-repair", schema),
    "cache": ("ep10-cache", cache),
    "ask": ("ep10-ask", ask),
    "doctor": ("ep10-doctor", doctor),
    "complete": ("rtr5-complete", complete),
    "fanout": ("rtr5-perf", fanout),
    "fanout-parent": ("rtr5-perf", fanout),
}


async def main(mode: str) -> int:
    if mode == "plan":
        log = Log(PR, "ep10-plan")
        async with plan_harness(log) as found:
            await plan(log, found)
        return log.verdict()
    slug, lane = MODES[mode]
    log = Log("rtr5" if mode in {"complete", "fanout", "fanout-parent"} else PR, slug)
    home = openrouter_home(f"x10-{mode}")
    async with harnessed(home) as found:
        await lane(log, home, found.harness)
    log(f"OpenRouter spend estimate (upper bound): ${relay_usd(home):.4f}")
    return log.verdict()


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in {*MODES, "plan"}:
        raise SystemExit(f"usage: x10_llm.py {{{','.join([*MODES, 'plan'])}}}")
    raise SystemExit(asyncio.run(main(sys.argv[1])))
