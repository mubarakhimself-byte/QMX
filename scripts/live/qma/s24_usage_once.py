"""S24, one usage source per profile, key half. A key chat on the fake model in bypass mode;
the fake model reports scripted usage on every reply, including a Bash round trip, over two
operator turns.

PASS when the run journal holds exactly one `model_call` row per request the fake model
answered, the relay counted the same number of upstream requests, the journal's token sums
equal what the fake model reported, and `RunIndex` indexes that journal under the chat.

    s24_usage_once.py
"""

from __future__ import annotations

import asyncio
import sys

from common import (
    USAGE_EVENTS,
    Log,
    Session,
    boot,
    chat_args,
    fake_row,
    put_providers,
    throwaway_home,
    use_fake_home,
    use_fake_key,
)
from fake_model import FakeModel, Turn, text, tool_use

FIELDS = {
    "input_tokens": "input_tokens",
    "output_tokens": "output_tokens",
    "cache_read_input_tokens": "cache_read_tokens",
    "cache_creation_input_tokens": "cache_write_tokens",
}


def usage(seed: int) -> dict[str, int]:
    return {
        "input_tokens": 1000 + seed,
        "output_tokens": 20 + seed,
        "cache_read_input_tokens": 300 + seed,
        "cache_creation_input_tokens": 40 + seed,
    }


async def run(log: Log) -> None:
    args = chat_args(__doc__).parse_args()
    from qma.harness import TestMode  # noqa: PLC0415

    root = throwaway_home("hp7-s24")
    fake = FakeModel(
        [
            Turn([tool_use("Bash", {"command": "echo one", "description": "echo"})], usage(1)),
            Turn([text("first turn done")], usage(2)),
            Turn([text("second turn done")], usage(3)),
        ]
    ).start()
    put_providers(root, {"fake": fake_row(fake.url)})
    session = await Session.start(
        root,
        model="opus",
        workspace=args.workspace,
        title="s24",
        test=TestMode(loopback_http_provider=True),
        profile="fake",
        mode="bypassPermissions",
        tools=["Bash"],
    )
    try:
        await session.turn(log, "Run the command.")
        await session.turn(log, "And again in words.")
        await asyncio.sleep(0.5)
        rows = [r for r in session.journal() if r["event"] in USAGE_EVENTS]
        answered = [s for s in fake.requests if s.method == "POST"]
        log(f"fake model POSTs: {[(s.path, s.scripted) for s in answered]}")
        log(f"journal rows: {[(r['payload']['path'], r['payload']['status']) for r in rows]}")
        log.check(
            "one row per upstream request", len(rows) == len(answered), (len(rows), len(answered))
        )
        upstream = session.relay.counters.upstream
        log.check("the relay counted the same requests", upstream == len(rows), upstream)
        for wire, column in FIELDS.items():
            served = sum(u.get(wire, 0) for u in fake.served_usage)
            journaled = sum(r["payload"][column] for r in rows)
            log.check(f"{column} sums match", served == journaled, (served, journaled))
        indexed = {run["id"]: run for run in session.control.run_index.refresh()}
        run_row = indexed.get(session.chat)
        log.check(
            "RunIndex indexes the journal under the chat",
            run_row is not None and str(run_row["journal"]).endswith("journal.jsonl"),
            run_row and run_row.get("model"),
        )
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp7-s24")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
