"""S36, a provider switch keeps the conversation. In the ship home, a plan chat on sonnet at
effort `max` with no tools is given a codeword and a small sum to think about. It then switches
to the OpenRouter Kimi row through quote and apply, and asks for the codeword under the spend
guard. The answer is the last non-blank reply text (HP1: a provider can close a turn with a
blank text block).

PASS when the recall names the codeword with a signed thinking block in the transcript before
the switch. If the recall fails, the chat switches back to the plan, runs `/compact`, switches
to OpenRouter again and asks once more, and both answers are recorded, as HP1 did. With no signed
thinking block the result is UNMEASURED and no OpenRouter turn is spent.

    s36_switch_resume.py
"""

from __future__ import annotations

import asyncio
import secrets
import sys
from typing import Any

from common import SHIP_HOME, Log, boot, require_login, use_fake_home
from switch_lane import (
    apply,
    assistant_entries,
    last_reply_text,
    quote,
    ship_providers,
    spend_ledger,
    start,
)

RECALL = "What was the codeword I gave you earlier? Reply with the codeword only."


def signed_thinking(raw: str) -> int:
    return sum(
        block.get("type") == "thinking" and bool(block.get("signature"))
        for entry in assistant_entries(raw)
        for block in entry.get("message", {}).get("content", [])
        if isinstance(block, dict)
    )


async def switch(log: Log, session: Any, profile: str) -> None:
    found = await quote(log, session, profile=profile)
    await apply(log, session, found.id)


async def recall(log: Log, session: Any, label: str, word: str) -> bool:
    ledger = spend_ledger()
    await ledger.spend(label, 2, 2048, lambda: session.turn(log, RECALL))
    answer = last_reply_text(session.transcript())
    ok = answer is not None and word in answer
    log(f"{label}: last reply {answer!r}")
    return ok


async def run(log: Log) -> None:
    word = f"persimmon-{secrets.token_hex(3)}"
    session = await start(
        SHIP_HOME, title="hp12 s36", model="sonnet", profile="claude", tools=[], effort="max"
    )
    try:
        await session.turn(
            log,
            f"Remember this codeword for later: {word}. Before you reply, work out which is "
            "larger, 37 x 43 or 39 x 41. Then reply only: noted.",
        )
        signed = signed_thinking(session.transcript())
        log(f"signed thinking blocks in the plan transcript: {signed}")
        if not signed:
            log("UNMEASURED: the plan turn wrote no signed thinking block; no OpenRouter turn")
            log.passed = False
            return
        async with ship_providers(session, log):
            await switch(log, session, "openrouter")
            if await recall(log, session, "S36 recall on OpenRouter", word):
                log.check("the recall after the switch names the codeword", True, word)
                return
            log.check("the recall after the switch names the codeword", False, word)
            await switch(log, session, "claude")
            await session.turn(log, "/compact")
            await switch(log, session, "openrouter")
            ok = await recall(log, session, "S36 recall after /compact", word)
            log(f"RECORDED: first recall failed; after /compact on the plan the recall {ok=}")
    finally:
        await session.harness.close()


def main() -> int:
    log = Log("hp12-s36")
    boot()
    use_fake_home()
    require_login(log)
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
