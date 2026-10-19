"""S29a, grants as the only layer. S29's replay with
`TestMode(gate_hook=False, deny_rules=False)`, on the fake model.

Chat 1 asks for order A and the operator allows it once, which writes one unsigned row. Then
`[claude] permissions.allow` names `mcp__qmx_node__propose_order`, and with the gate hook off nothing
makes chat 2 ask: its replay of order A reaches the tool handler with no grant.

PASS when chat 2 never asks, its replay is refused for a missing grant, and the row count
stays 1.

    s29a_grants_alone.py
"""

from __future__ import annotations

import asyncio
import sys

from approval_lane import ALLOW_ONCE, Host, answered_turn, fake_session, in_order, new_chat
from common import SCRATCH, Log, boot, put_claude, use_fake_home, use_fake_key
from fake_model import Turn, text
from money_lane import results
from s29_approvals import ORDER_A, PROPOSE, TOOLS, propose, put_brokers, rows


async def run(log: Log) -> None:
    from qma.harness import TestMode  # noqa: PLC0415

    script = [propose(ORDER_A), Turn([text("done")]), propose(ORDER_A), Turn([text("done")])]
    test = TestMode(gate_hook=False, deny_rules=False, loopback_http_provider=True)
    root, fake, session = await fake_session(
        "hp9-s29a", script, tools=TOOLS, test=test, workspace=SCRATCH / "hp9-s29-workspace"
    )
    put_brokers(root)
    try:
        async with Host(session) as host:
            first = await answered_turn(log, host, session.chat, in_order([ALLOW_ONCE]))
            log.check(
                "the approved call wrote one row",
                [a.status for a in first.answered] == ["resolved"] and len(rows(root)) == 1,
                f"{[a.status for a in first.answered]}, {len(rows(root))} row(s)",
            )
            put_claude(root, {"permissions": {"allow": [PROPOSE]}})
            second = await new_chat(session, "s29a replay", SCRATCH / "hp9-s29-workspace")
            replay = await answered_turn(log, host, second, in_order())
            log.check("the replay did not ask", replay.asks == [], replay.asks)
            found = list(results(fake).values())
            for tool, tool_input, is_error, said in found:
                log(f"  call {tool} {tool_input} error={is_error}: {said[:200]!r}")
            last = found[-1]
            log.check(
                "the handler refused the replay for a missing grant",
                last[2] and "no approval was given" in last[3],
                last[3][:200],
            )
            log.check("no second row", len(rows(root)) == 1, f"{len(rows(root))} row(s)")
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp9-s29a")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
