"""S29, approvals bound to arguments. A key chat on the fake model in default mode, in a
throwaway QMX home whose [brokers] names one demo account with the propose permission and a
credential reference that is not in the keyring, so no broker connection can open.

The fake model calls `mcp__qmx_node__propose_order` four times. The answers go through
`POST /api/approvals/{ask_id}`:
1. order A, AllowOnce;
2. order A again (the replay), Reject;
3. order B, one field changed, Reject;
4. after `[claude] permissions.allow = ["mcp__qmx_node__propose_order"]`, in a new chat, order A:
   AllowAlways, then Reject.

PASS when each call asks, the first writes one unsigned row, the allow rule does not let call 4
run, AllowAlways returns `invalid`, the rejects write no row, and no process holds a connection
to a broker port.

    s29_approvals.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

from approval_lane import (
    ALLOW_ALWAYS,
    ALLOW_ONCE,
    Host,
    answered_turn,
    fake_session,
    in_order,
    new_chat,
    reject,
    tools_asked,
)
from common import SCRATCH, Log, boot, put_claude, use_fake_home, use_fake_key
from fake_model import Turn, text, tool_use
from money_lane import broker_connections, results

PROPOSE = "mcp__qmx_node__propose_order"
TOOLS = ["Read"]
ORDER_A = {
    "broker_id": "demo",
    "connection_id": "demo",
    "account_id": "101",
    "symbol": "EURUSD",
    "side": "buy",
    "quantity": "0.01",
}
ORDER_B = {**ORDER_A, "quantity": "0.02"}
BROKERS: dict[str, Any] = {
    "brokers": [
        {
            "id": "demo",
            "name": "Demo",
            "adapter": "ctrader",
            "connections": [
                {
                    "id": "demo",
                    "credential_ref": "qmx/hp9-absent",
                    "environment": "demo",
                    "accounts": [
                        {"id": "101", "currency": "USD", "permissions": ["read", "propose"]}
                    ],
                }
            ],
        }
    ]
}


def propose(order: dict[str, Any]) -> Turn:
    return Turn([tool_use(PROPOSE, {"proposal": order})])


def put_brokers(root: Path) -> None:
    from qma.harness import QmxHome  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    control_service(QmxHome(root)).settings_put("brokers", BROKERS)


def rows(root: Path) -> list[dict[str, Any]]:
    from qmx_broker.service import BrokerService  # noqa: PLC0415

    return BrokerService(root).proposals()


async def run(log: Log) -> None:
    script = [propose(ORDER_A), propose(ORDER_A), propose(ORDER_B), Turn([text("done")])]
    script += [propose(ORDER_A), Turn([text("done")])]
    root, fake, session = await fake_session("hp9-s29", script, tools=TOOLS)
    put_brokers(root)
    try:
        async with Host(session) as host:
            first = await answered_turn(
                log, host, session.chat, in_order([ALLOW_ONCE], [reject()], [reject()])
            )
            found = list(results(fake).values())
            for tool, tool_input, is_error, said in found:
                log(f"  call {tool} {tool_input} error={is_error}: {said[:160]!r}")
            log.check(
                "calls 1-3 each asked", tools_asked(first) == [PROPOSE] * 3, tools_asked(first)
            )
            log.check(
                "AllowOnce wrote one unsigned row",
                len(rows(root)) == 1 and not found[0][2],
                f"{len(rows(root))} row(s); first call error={found[0][2]}",
            )
            log.check(
                "replay and changed call refused after Reject",
                [f[2] for f in found[1:3]] == [True, True],
                [f[3][:80] for f in found[1:3]],
            )
            put_claude(root, {"permissions": {"allow": [PROPOSE]}})
            second = await new_chat(session, "s29 allow rule", SCRATCH / "hp9-s29-workspace")
            later = await answered_turn(log, host, second, in_order([ALLOW_ALWAYS, reject()]))
            log.check(
                "with an allow rule in [claude], call 4 still asked",
                tools_asked(later) == [PROPOSE],
                tools_asked(later),
            )
            log.check(
                "no always choice offered on propose_order",
                all("always" not in ask for ask in first.asks + later.asks),
                [sorted(ask) for ask in first.asks + later.asks],
            )
            statuses = [a.status for a in later.answered]
            log.check(
                "AllowAlways invalid, then Reject resolved",
                statuses == ["invalid", "resolved"],
                statuses,
            )
            log.check("Reject wrote no row", len(rows(root)) == 1, f"{len(rows(root))} row(s)")
            log(f"unsigned row: {rows(root)}")
            held = broker_connections()
            log.check("no connection to a broker port", held == [], held)
    finally:
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp9-s29")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
