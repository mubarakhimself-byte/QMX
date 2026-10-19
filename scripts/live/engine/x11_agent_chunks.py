"""EP11 lane 2 (E29, E30) and TURN-E lane 3: 20 items fan out to an `agent` node by chunks of 10
on `claude/haiku` through the plan login.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x11_agent_chunks.py`
Writes `evidence/ep11/<ENGINE_LOG_PREFIX>ep11-chunks.log`. The `reader` role is `claude/haiku` in
a live-mode run on the ship home under the lane lock. The node declares only `Read`, and its brief
asks it to read `notes.txt` from its working folder first, so each chunk shows a tool span that
the `engine` hook sink reported live. Each chunk is one Background chat, a join collects the two
answers, and each span's cache read share is logged for the perf block (chunk 1 is the baseline).
The first chunk ends its turn before the other sends, so it reads its cache. Plan turns: two chunk
turns, any repair turn, and at most one meter turn.
The ship home's `settings.toml` is hashed before and after and must not change.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from agent_lanes import PR, edge, node, run, sessions, settings_sha, workflow
from common import Log, boot, plan_harness, throwaway_home
from qmx_engine.ports.harness_adapter import HarnessAdapter
from qmx_engine.settings import DEFAULTS

WORDS = [
    "otter",
    "lamp",
    "heron",
    "brick",
    "walrus",
    "spoon",
    "badger",
    "cloud",
    "lynx",
    "kettle",
    "falcon",
    "pencil",
    "bison",
    "ladder",
    "gecko",
    "mirror",
    "tapir",
    "candle",
    "moose",
    "anchor",
]
BRIEF = (
    "First read notes.txt in your working folder with the Read tool. Then, for every input item "
    "(an id and a word), in input order, say whether the word names an animal."
)
NOTES = "Count a word as an animal only when it names a living species.\n"
HAIKU = {**DEFAULTS, "roles.reader": ("claude/haiku",)}
SCHEMA = {
    "type": "object",
    "required": ["results"],
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "animal"],
                "properties": {"id": {"type": "integer"}, "animal": {"type": "boolean"}},
            },
        }
    },
}


def share(tokens: dict[str, int]) -> float:
    read = tokens.get("cache_read", 0)
    total = tokens.get("in", 0) + read + tokens.get("cache_write", 0)
    return read / total if total else 0.0


async def main() -> int:
    log = Log(PR, "ep11-chunks")
    boot()
    before = settings_sha()
    log(f"ship home settings.toml sha256 before: {before}")
    root = workflow(
        "chunks",
        [
            node("start", "trigger"),
            node(
                "read",
                "agent",
                "reader",
                brief_ref="prompts/brief.md",
                output_schema_ref="schemas/out.json",
                tools=["Read"],
            ),
            node("all", "join"),
        ],
        {
            "start": {"main": [edge("read", "chunk", chunk={"by": "items", "size": 10})]},
            "read": {"main": [edge("all")]},
        },
        {"prompts/brief.md": BRIEF, "schemas/out.json": json.dumps(SCHEMA)},
    )
    items = [{"id": i, "word": word} for i, word in enumerate(WORDS)]
    engine_home = throwaway_home(PR, "chunks-engine")
    folder = engine_home / "workspaces" / "wf-chunks"
    folder.mkdir(parents=True)
    (folder / "notes.txt").write_text(NOTES, encoding="utf-8")
    async with plan_harness(log) as found:
        outcome, events, spans = await run(
            engine_home,
            root,
            HarnessAdapter(found.harness),
            HAIKU,
            mode="live",
            inputs=items,
        )
    after = settings_sha()
    log(f"ship home settings.toml sha256 after: {after}")
    log(f"run {outcome.run_id}: {outcome.status} {outcome.reason or ''}")
    chunks = {
        e.data.get("partition")
        for e in events
        if e.kind == "node_scheduled" and e.data.get("node_id") == "read"
    }
    chats = {sid for _, _, sid in sessions(events)}
    joined_outputs: Any = next(
        (
            e.data["outputs"]
            for e in events
            if e.kind == "node_finished" and e.data["node_id"] == "all"
        ),
        {},
    )
    joined = sum(len(part.get("results", [])) for part in joined_outputs.get("main", []))
    log(f"chunks={len(chunks)} chats={len(chats)} joined={joined}")
    attempts = sorted(
        (s for s in spans if s.kind == "node" and s.node_id == "read"),
        key=lambda s: s.partition or "",
    )
    for span in attempts:
        log(
            f"span read partition {span.partition} attempt {span.attempt} {span.status}: "
            f"{span.profile}/{span.model} tokens {span.tokens} cache read share "
            f"{share(span.tokens):.0%}"
        )
    ok = [s for s in attempts if s.status == "ok"]
    tools = [(s.parent_span_id, s.name) for s in spans if s.kind == "tool"]
    hooked = {
        (str(e.data.get("partition")), e.data["tool"].get("name"))
        for e in events
        if e.kind == "tool_called" and e.data["tool"].get("source") == "hook"
    }
    log(f"tool spans (parent, name): {tools}; hook-reported (partition, name): {sorted(hooked)}")
    log.check(
        "two Background chats ran, one per chunk, both passed, and the join holds 20 results",
        outcome.status == "passed"
        and len(chunks) == 2
        and len(chats) == 2
        and len(ok) == 2
        and joined == 20,
        {"chunks": len(chunks), "chats": len(chats), "ok": len(ok), "joined": joined},
    )
    log.check(
        "each chunk has a Read tool span the hook sink reported",
        len(ok) == 2
        and all((s.span_id, "Read") in tools and (s.partition, "Read") in hooked for s in ok),
        {"spans": tools, "hooked": sorted(hooked)},
    )
    log.check(
        "chunk 2 read tokens from the cache",
        len(ok) == 2 and ok[1].tokens.get("cache_read", 0) > 0,
        [s.tokens.get("cache_read") for s in ok],
    )
    log.check(
        "every chunk ran on claude/haiku",
        {(s.profile, s.model) for s in ok} == {("claude", "haiku")},
        sorted({f"{s.profile}/{s.model}" for s in ok}),
    )
    log.check("the ship home's settings.toml is unchanged", after == before, after)
    log(f"perf: cache read share by chunk {[f'{share(s.tokens):.0%}' for s in ok]}")
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
