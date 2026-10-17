"""EP0 p_asks. A Background plan chat in `default` mode is asked to write a file. Every
`permission` block it raises is answered at once with `Harness.answer(AskId(...),
Reject("unattended run"))`, the way the engine's adapter will answer it. PASS when the reject
lands within 2 s of the ask appearing, no file is written, and the chat ends its turn with a
final text block.

    p_asks.py
"""

from __future__ import annotations

import asyncio
import time

from common import (
    TRIAGE_PLAN_MODEL,
    TURN_TIMEOUT_S,
    boot,
    live,
    log,
    plan_harness,
    run,
    workspace,
)

POLL_S = 0.05
REJECT_WITHIN_S = 2.0
TARGET = "probe-ask.txt"


async def main() -> int:
    from qma.harness import AskId, Reject  # noqa: PLC0415
    from qma.harness.home import session_id  # noqa: PLC0415

    say = log("ep0-asks")
    boot()
    ws = workspace("asks")
    async with plan_harness(say) as h:
        chat = await h.background("ep0 asks", ws, model=TRIAGE_PLAN_MODEL)
        mark = h.mark(chat)
        await h.inject(
            chat,
            f"Use the Write tool to create the file {TARGET} in your working directory with the "
            "content hello. If you cannot, reply with one sentence saying so.",
        )
        answered: dict[int, tuple[float, float, str]] = {}
        settled: dict[int, float] = {}
        deadline = time.monotonic() + TURN_TIMEOUT_S
        while time.monotonic() < deadline:
            for block in h.blocks(chat, mark):
                content, n = block["content"], int(block["seq"])
                if block["type"] != "permission":
                    continue
                ask = content.get("ask")
                if content.get("state") == "rejected" and ask in answered and ask not in settled:
                    settled[ask] = time.perf_counter() - answered[ask][0]
                if content.get("state") != "asking" or n in answered:
                    continue
                seen = time.perf_counter()
                status = h.harness.answer(AskId(session_id(chat), n), Reject("unattended run"))
                answered[n] = (seen, time.perf_counter(), str(status))
                say(f"ask {n} on {content.get('tool')}: answered {status}")
            record = h.record(chat)
            if record is not None and record.turn == "idle" and settled.keys() >= answered.keys():
                break
            await asyncio.sleep(POLL_S)
        await h.wait_idle(chat)
        blocks = h.blocks(chat, mark)
        for block in blocks:
            live.show(say, block)
        tools = [b for b in blocks if b["type"] == "tool"]
        say(f"tool blocks: {len(tools)}")
        for n, (seen, done, status) in answered.items():
            say(
                f"ask {n}: answer returned in {done - seen:.3f} s ({status}); the rejected block "
                f"was in the log {settled.get(n, float('nan')):.3f} s after the ask was seen"
            )
        say.check("the chat raised a permission ask", bool(answered), sorted(answered))
        say.check(
            f"every reject landed within {REJECT_WITHIN_S:.0f} s",
            bool(answered)
            and all(n in settled and settled[n] <= REJECT_WITHIN_S for n in answered),
            settled,
        )
        say.check("no file was written", not (ws / TARGET).exists(), ws / TARGET)
        last = blocks[-1] if blocks else None
        say.check(
            "the chat went on and ended its turn with a text block",
            h.record(chat).turn == "idle" and last is not None and last["type"] == "text",
            None if last is None else (last["type"], str(last["content"])[:200]),
        )
    return int(say.verdict())


if __name__ == "__main__":
    run(main)
