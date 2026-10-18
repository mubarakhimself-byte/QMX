"""EP11 lane 2 (E29, E30): 30 items fan out to an `agent` node by chunks of 10 on the plan.

From `qmx-agents/` with the agents venv:
`uv run --no-sync python ../scripts/live/engine/x11_agent_chunks.py`
Writes `evidence/ep11/<ENGINE_LOG_PREFIX>ep11-chunks.log`. The `reader` role's first plan-profile
candidate runs in a live-mode run on the ship home under the lane lock. Each chunk is one
Background chat, a join collects the three answers, and each span's cache read share is logged for
the perf block (chunk 1 is the baseline). The first chunk ends its turn before the others send, so
they read its cache. Plan turns: three chunk turns, any repair turn, and at most one meter turn.
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
    "newt",
    "basket",
    "ibex",
    "button",
    "koala",
    "hammer",
    "yak",
    "velvet",
    "orca",
    "tunnel",
]
BRIEF = (
    "Each input item has an id and a word. For every item, in input order, say whether the word "
    "names an animal."
)
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
                tools=[],
                max_turns=12,
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
    async with plan_harness(log) as found:
        outcome, events, spans = await run(
            throwaway_home(PR, "chunks-engine"),
            root,
            HarnessAdapter(found.harness),
            DEFAULTS,
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
    log.check(
        "three Background chats ran, one per chunk, and the join holds 30 results",
        outcome.status == "passed" and len(chunks) == 3 and len(chats) == 3 and joined == 30,
        {"chunks": len(chunks), "chats": len(chats), "joined": joined},
    )
    log.check(
        "chunks 2 and 3 read tokens from the cache",
        len(ok) == 3 and all(s.tokens.get("cache_read", 0) > 0 for s in ok[1:]),
        [s.tokens.get("cache_read") for s in ok],
    )
    log.check(
        "every chunk ran on the reader role's first plan-profile candidate",
        {(s.profile, s.model) for s in ok} == {("claude", "sonnet")},
        sorted({f"{s.profile}/{s.model}" for s in ok}),
    )
    log.check("the ship home's settings.toml is unchanged", after == before, after)
    log(f"perf: cache read share by chunk {[f'{share(s.tokens):.0%}' for s in ok]}")
    return log.verdict()


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
