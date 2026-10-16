"""S34, a switch cannot skip its warning, on the fake model. A key chat on row `fake` ends one
turn. Through the HTTP doors it quotes a switch to row `fake2`, sends another turn, then applies
the quote.

PASS when the quote returns a warning while the chat is still on `fake` with one CLI, the apply
after the other turn answers 409 `quote_stale`, and the chat is still on `fake` with no second
launch.

    s34_quote_stale.py
"""

from __future__ import annotations

import asyncio
import sys

from approval_lane import Host
from common import Log, boot, use_fake_home, use_fake_key, wait_turn
from fake_model import Turn, text
from switch_lane import fake_pair


async def run(log: Log) -> None:
    fake, session, launched = await fake_pair(
        log, "hp12-s34", [Turn([text("one")]), Turn([text("two")])], tools=["Bash"]
    )
    chat = session.chat
    try:
        await session.turn(log, "Say one.")
        async with Host(session) as host:
            quoted = await host.http.post(f"/api/sessions/{chat}/quote", json={"profile": "fake2"})
            body = quoted.json()
            log(f"POST quote -> {quoted.status_code} {body}")
            record = session.harness._chat(chat).record
            log.check(
                "the warning came back while the chat was still on fake with one CLI",
                quoted.status_code == 200
                and bool(body["warning"])
                and record.config.profile == "fake"
                and len(launched) == 1,
                (body.get("warning"), record.config.profile, len(launched)),
            )
            sent = await host.http.post(f"/api/sessions/{chat}/turns", json={"text": "Say two."})
            log(f"POST turns -> {sent.status_code}")
            await wait_turn(session.home, chat, 60)
            applied = await host.http.post(
                f"/api/sessions/{chat}/apply", json={"quote_id": body["id"]}
            )
            log(f"POST apply -> {applied.status_code} {applied.json()}")
            log.check(
                "the apply after another turn answers 409 quote_stale",
                applied.status_code == 409 and applied.json()["error"]["code"] == "quote_stale",
                applied.status_code,
            )
        record = session.harness._chat(chat).record
        log.check(
            "the chat is still on fake and no second CLI started",
            record.config.profile == "fake" and len(launched) == 1,
            (record.config.profile, len(launched)),
        )
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp12-s34")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
