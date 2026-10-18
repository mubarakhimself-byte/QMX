"""Operator checks 8 and 9 (`research/one-engine/04-baseline.md` section 4).

8  In the ship home, a plan chat on haiku with only the Bash tool ends one turn. The
   OpenRouter Kimi row (`switch_lane.OPENROUTER_ROW`) is added for the check. Through the
   HTTP doors the chat quotes a switch to it, then applies the quote, then asks for a
   terminal command; every ask is allowed once. The OpenRouter turn runs under the spend
   guard. PASS when the warning names the uncached tokens while the chat is still on the
   plan with one CLI, the switch resumes the same session in the relayed home, the reply
   ran Bash and quotes its output, and `GET /api/usage` counts more OpenRouter calls than
   before that reply.
9  SKIPPED. OpenRouter is the only keyed row; the operator ruled that the other providers
   are tested when he adds their keys.

op_checks_8_9.py 8|9
"""

from __future__ import annotations

import asyncio
import sys
from typing import Any

from approval_lane import ALLOW_ONCE, Host, always, answered_turn
from common import (
    SHIP_HOME,
    Log,
    boot,
    capture_launches,
    last_event,
    require_login,
    session_blocks,
    show,
    use_fake_home,
)
from switch_lane import (
    last_reply_text,
    relayed_rows,
    ship_providers,
    spend_ledger,
    start,
)

MARK = "qma-check8-ok"
CHECK_8_MEASURED_USD = 0.006
"""Above the HP12 owner run's charge: its check 8 and S36 turns together moved the key's usage
by $0.0091 (`evidence/hp12/openrouter-spend.tsv`). The worst case, 3 calls at 40k input
tokens, is $0.075, which a $0.01 fix-round budget cannot fit."""
CHECK_9_SKIPPED = (
    "SKIPPED check 9: OpenRouter is the only keyed row; the operator ruled that the other "
    "providers are tested when he adds their keys"
)


async def openrouter_calls(host: Host) -> int:
    page = (await host.http.get("/api/usage")).json()
    return int(page["tokens"].get("openrouter", {}).get("calls", 0))


async def check8(log: Log) -> None:
    ledger = spend_ledger()
    launched = capture_launches()
    session = await start(
        SHIP_HOME, title="hp12 check 8", model="haiku", profile="claude", tools=["Bash"]
    )
    chat = session.chat
    try:
        await session.turn(log, "Reply with the single word READY.")
        async with ship_providers(session, log), Host(session) as host:
            quoted = await host.http.post(
                f"/api/sessions/{chat}/quote", json={"profile": "openrouter"}
            )
            body: dict[str, Any] = quoted.json()
            log(f"POST quote -> {quoted.status_code} {body}")
            on_plan = session.harness._chat(chat).record.config.profile
            log.check(
                "the warning names the uncached tokens before any switch",
                quoted.status_code == 200
                and "tokens uncached" in str(body.get("warning"))
                and on_plan == "claude"
                and len(launched) == 1,
                (body.get("warning"), on_plan, len(launched)),
            )
            applied = await host.http.post(
                f"/api/sessions/{chat}/apply", json={"quote_id": body["id"]}
            )
            log(f"POST apply -> {applied.status_code}")
            relayed = launched[-1].options
            log.check(
                "the switch resumed the same session in the relayed home",
                applied.status_code == 200
                and len(launched) == 2
                and relayed.resume == chat
                and relayed.env["CLAUDE_CONFIG_DIR"] == str(session.home.relayed_dir),
                (applied.status_code, len(launched), relayed.resume),
            )
            before = await openrouter_calls(host)
            mark = last_event(session.control, chat)
            prompt = f"Use the Bash tool to run exactly: echo {MARK}. Then reply with its output."
            log(f"turn: {prompt}")
            await ledger.spend(
                "check 8 OpenRouter turn",
                3,
                2048,
                lambda: answered_turn(log, host, chat, always(ALLOW_ONCE), prompt),
                measured=CHECK_8_MEASURED_USD,
            )
            found = session_blocks(session.control, chat, mark)
            for block in found:
                show(log, block)
            after = await openrouter_calls(host)
        tools = [b["content"] for b in found if b["type"] == "tool"]
        ran = [t for t in tools if t.get("name") == "Bash" and MARK in str(t)]
        reply = last_reply_text(session.transcript())
        log(f"last reply: {reply!r}")
        log.check(
            "the reply ran Bash and quotes its output",
            bool(ran) and MARK in str(reply),
            (len(ran), reply),
        )
        rows = relayed_rows(session, "openrouter")
        models = sorted({str(row.get("model")) for row in rows})
        log(f"/api/usage OpenRouter calls {before} -> {after}; journal models {models}")
        log.check(
            "/api/usage shows OpenRouter for that reply",
            after > before and bool(models) and all("kimi" in m for m in models),
            (before, after, models),
        )
    finally:
        await session.harness.close()


def main() -> int:
    check = sys.argv[1] if len(sys.argv) > 1 else ""
    if check not in {"8", "9"}:
        raise SystemExit("usage: op_checks_8_9.py 8|9")
    log = Log(f"hp12-check{check}")
    if check == "9":
        log(CHECK_9_SKIPPED)
        return 0
    boot()
    use_fake_home()
    require_login(log)
    asyncio.run(check8(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
