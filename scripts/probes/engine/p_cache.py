"""EP0 p_cache. Two Background chats on one model whose prompts share a static prefix of about
3,000 tokens and differ only after it. Records each chat's cache read and write tokens from its
run journal's `model_call` rows. The CLI's own system prompt and tools are cached too, so the
first chat's read is the floor; the second chat's read above it is what the shared prefix won.

    p_cache.py               plan profile on the ship home, under the lane lock
    p_cache.py --openrouter  the OpenRouter row in a throwaway home; the relay journals the rows

PASS (plan) when the second chat shows a cache read above 0, or the log records 0 with both
chats' row ids. PASS (OpenRouter) when the relay journal holds cache read and write fields for
both chats.
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from common import (
    KIMI_MODEL,
    OPENROUTER_ROW,
    TRIAGE_PLAN_MODEL,
    ModelCall,
    Opened,
    boot,
    cache_read,
    journal_of,
    live,
    log,
    opened,
    plan_harness,
    run,
    text_of,
    throwaway_home,
    workspace,
)

PREFIX = "\n".join(
    f"Rule {n}. A workflow node reads its inputs from the run ledger, writes one output "
    f"artifact named node-{n}.json, and never calls a model twice for the same input hash."
    for n in range(1, 121)
)
"""A byte-stable brief, put first the way the engine puts its static brief. The plan asked for
about 3,000 tokens; the cache write measured about 6,500 on haiku, which only makes it easier
to cache."""
TASKS = {"a": "Reply with the single word ALPHA.", "b": "Reply with the single word BETA."}
KIMI_IN, KIMI_OUT = 0.5e-6, 2.5e-6


async def pair(
    say: Any, h: Opened, *, profile: str, model: str
) -> tuple[dict[str, list[ModelCall]], dict[str, bool]]:
    """Each chat's `model_call` rows, and whether every row's raw payload names both cache
    fields (the reader defaults a missing field to 0, so presence is read from the raw line)."""
    rows: dict[str, list[ModelCall]] = {}
    fields: dict[str, bool] = {}
    for name, task in TASKS.items():
        chat = await h.background(
            f"ep0 cache {name}", workspace(f"cache-{name}"), model=model, profile=profile
        )
        mark = h.mark(chat)
        await h.inject(chat, f"{PREFIX}\n\n{task}")
        record = await h.wait_idle(chat)
        rows[name] = h.journal(chat)
        payloads = [
            json.loads(line)["payload"]
            for line in journal_of(h.home, chat).read_text(encoding="utf-8").splitlines()
            if '"model_call"' in line
        ]
        fields[name] = bool(payloads) and all(
            {"cache_read_tokens", "cache_write_tokens"} <= p.keys() for p in payloads
        )
        say(f"  every model_call payload has cache read and write fields: {fields[name]}")
        say(f"chat {name} {chat}: turn {record.turn}, reply {text_of(h.blocks(chat, mark))}")
        for row in rows[name]:
            say(f"  row seq={row.seq} {row}")
    return rows, fields


async def plan(say: Any) -> None:
    async with plan_harness(say) as h:
        rows, _ = await pair(say, h, profile="claude", model=TRIAGE_PLAN_MODEL)
    first, second = cache_read(rows["a"]), cache_read(rows["b"])
    say(
        f"cache read: first chat {first}, second chat {second}, second minus first {second - first}"
    )
    say(
        "cache write: first chat "
        f"{sum(r.cache_write_tokens for r in rows['a'])}, second chat "
        f"{sum(r.cache_write_tokens for r in rows['b'])}"
    )
    ids = {name: [r.seq for r in found] for name, found in rows.items()}
    say.check(
        "the second plan chat shows a cache read above 0, or 0 with both chats' row ids",
        second > 0 or all(ids.values()),
        {"second_cache_read": second, "row_ids": ids},
    )


async def openrouter(say: Any) -> None:
    root = throwaway_home("cache-openrouter")
    row = OPENROUTER_ROW | {"quirks": {"env": {"CLAUDE_CODE_MAX_OUTPUT_TOKENS": "512"}}}
    live.put_providers(root, {"openrouter": row})
    say(f"throwaway home {root}, row openrouter tiers -> {KIMI_MODEL}, key by ref qmx/openrouter")
    async with opened(root) as h:
        rows, fields = await pair(say, h, profile="openrouter", model="haiku")
    spent = sum(
        r.input_tokens * KIMI_IN + r.output_tokens * KIMI_OUT
        for found in rows.values()
        for r in found
    )
    say(f"estimated OpenRouter spend from the rows: ${spent:.4f} (cache reads priced as input)")
    for name, found in rows.items():
        say(
            f"chat {name}: {len(found)} model_call rows, cache read {cache_read(found)}, "
            f"cache write {sum(r.cache_write_tokens for r in found)}"
        )
    say.check(
        "the relay journal records cache read and write fields for both chats",
        len(fields) == len(TASKS) and all(fields.values()),
        fields,
    )


async def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openrouter", action="store_true")
    args = parser.parse_args()
    say = log("ep0-cache-key" if args.openrouter else "ep0-cache")
    boot()
    await (openrouter(say) if args.openrouter else plan(say))
    return int(say.verdict())


if __name__ == "__main__":
    run(main)
