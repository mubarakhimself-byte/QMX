"""EP0 p_limits. No plan turn. A throwaway home with the fake model on a key row. A rejected
five-hour reading is fed to the harness's plan watch the way `s10_usage.feed` does, as a CLI
`rate_limit_event` parsed by the SDK and projected by the harness. Then a Background plan chat's
send must raise `LaunchRefused` before any CLI starts, and `Harness.usage()` must show the reset
time. A Background chat on the fake key row still runs, as the control. First, a five-hour
reading whose reset passes leaves no reading, and a Background plan send then refuses too.

    p_limits.py
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime
from typing import Any

from common import (
    TRIAGE_PLAN_MODEL,
    boot,
    fake_key_row,
    live,
    log,
    opened,
    run,
    throwaway_home,
    workspace,
)

RESETS_IN_S = 3600
EXPIRES_IN_S = 2
REJECTED_FIVE_HOUR = {
    "status": "rejected",
    "rateLimitType": "five_hour",
    "overageStatus": "rejected",
    "overageDisabledReason": "out_of_credits",
    "isUsingOverage": False,
}


def fact(info: dict[str, Any]) -> Any:
    """`s10_usage.fact`, copied because `s10_usage` imports `common`, which here names this
    folder's module."""
    from claude_agent_sdk._internal.message_parser import parse_message  # noqa: PLC0415
    from qma.harness.project import project  # noqa: PLC0415

    message = parse_message(
        {"type": "rate_limit_event", "rate_limit_info": info, "uuid": "u", "session_id": "s"}
    )
    (found,) = project(message)
    return found


async def main() -> int:
    from fake_model import FakeModel, Turn, text  # noqa: PLC0415
    from qma.harness import LaunchRefused, TestMode  # noqa: PLC0415

    say = log("ep0-limits")
    boot()
    live.use_fake_key()
    fake = FakeModel([Turn([text("fake row still runs")])]).start()
    root = throwaway_home("limits")
    live.put_providers(root, {"fake": fake_key_row(fake.url)})
    resets = int(time.time()) + RESETS_IN_S
    try:
        async with opened(root, test=TestMode(loopback_http_provider=True)) as h:
            short = fact(
                {
                    "status": "allowed",
                    "rateLimitType": "five_hour",
                    "utilization": 0.1,
                    "resetsAt": int(time.time()) + EXPIRES_IN_S,
                }
            )
            h.harness._deps.on_plan_limits(short)
            before = [v.reading.window for v in (await h.harness.usage()).readings]
            await asyncio.sleep(EXPIRES_IN_S + 1)
            after = [v.reading.window for v in (await h.harness.usage()).readings]
            stale = await h.background(
                "ep0 limits stale", workspace("limits"), model=TRIAGE_PLAN_MODEL
            )
            try:
                await h.inject(stale, "Reply with the single word OK.")
                expired = None
            except LaunchRefused as error:
                expired = str(error)
            say(
                f"a 10% five-hour reading that resets in {EXPIRES_IN_S} s: readings {before}, "
                f"after its reset {after}; Background plan send then: {expired!r}"
            )
            say.check(
                "once the reading's reset passes, a Background plan send refuses for want of one",
                expired is not None and "no reading" in expired,
                expired,
            )
            reading = fact({**REJECTED_FIVE_HOUR, "resetsAt": resets})
            say(f"fed {reading}")
            h.harness._deps.on_plan_limits(reading)
            chat = await h.background("ep0 limits", workspace("limits"), model=TRIAGE_PLAN_MODEL)
            refusal: str | None = None
            try:
                await h.inject(chat, "Reply with the single word OK.")
            except LaunchRefused as error:
                refusal = str(error)
            say(f"Background plan send: LaunchRefused={refusal!r}")
            say.check("the Background plan send raised LaunchRefused", refusal is not None, refusal)
            notes = [b["content"] for b in h.blocks(chat) if b["type"] == "needs_you"]
            say(f"needs_you blocks on the chat: {notes}")
            page = await h.harness.usage()
            say(f"UsagePage.hard_stop={page.hard_stop!r} background_cap={page.background_cap}")
            windows = [
                (str(view.limits.window), str(view.limits.status), view.limits.resets_at)
                for view in page.windows
            ]
            say(f"UsagePage.windows (window, status, resets_at): {windows}")
            say(f"UsagePage.document()['windows']: {page.document()['windows']}")
            expected = datetime.fromtimestamp(resets, UTC)
            say.check(
                "the reset time is read from UsagePage.windows[].limits.resets_at",
                any(at == expected for _, _, at in windows),
                {"expected": expected.isoformat(), "seen": windows},
            )
            key_chat = await h.background(
                "ep0 limits key", workspace("limits-key"), model="opus", profile="fake"
            )
            mark = h.mark(key_chat)
            await h.inject(key_chat, "Reply.")
            record = await h.wait_idle(key_chat, 120)
            replies = [
                b["content"].get("text") for b in h.blocks(key_chat, mark) if b["type"] == "text"
            ]
            say(f"control: Background chat on the fake key row: turn {record.turn}, {replies}")
    finally:
        fake.stop()
    return int(say.verdict())


if __name__ == "__main__":
    run(main)
