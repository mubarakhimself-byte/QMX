"""S24, one usage source per profile, plan half. Ten plan turns in one chat on the ship home's
login, then one relayed chat on the fake model in the same harness.

PASS when the plan chat's journal holds one `model_call` row per turn, `RunIndex` sums their
costs to the CLI's own running total within 0.0001 USD, and the usage page counts the relayed
chat's rows once, under its own profile, with the fake model's token sums.

The fake row is added to the ship home's `[providers]` for the run and the old section is put
back after.

    s24_usage_plan.py
"""

from __future__ import annotations

import asyncio
import sys
from decimal import Decimal
from typing import Any

from common import (
    SHIP_HOME,
    USAGE_EVENTS,
    Log,
    Session,
    boot,
    chat_args,
    fake_row,
    require_login,
    use_fake_home,
    use_fake_key,
    wait_turn,
)
from fake_model import FakeModel, Turn, text

TURNS = 10
FAKE_USAGE = {
    "input_tokens": 1200,
    "output_tokens": 30,
    "cache_read_input_tokens": 400,
    "cache_creation_input_tokens": 50,
}


def recording_plan_rows() -> list[Any]:
    """The `TurnUsage` of every plan turn, as the chat hands it to `plan_row`."""
    import qma.harness.chat as chat_module  # noqa: PLC0415

    seen: list[Any] = []
    original = chat_module.plan_row

    def plan_row(turn: Any, base: Any) -> Any:
        seen.append(turn)
        return original(turn, base)

    chat_module.plan_row = plan_row
    return seen


async def run(log: Log) -> None:
    from qma.harness import NewChat, OperatorText, TestMode  # noqa: PLC0415

    args = chat_args(__doc__).parse_args()
    require_login(log)
    turns = recording_plan_rows()
    fake = FakeModel([Turn([text("relayed done")], FAKE_USAGE)]).start()
    session = await Session.start(
        SHIP_HOME,
        model=args.model,
        workspace=args.workspace,
        title="hp10 s24 plan",
        test=TestMode(loopback_http_provider=True),
    )
    providers = session.control.settings_get("providers")
    try:
        before = (await session.harness.usage()).tokens
        log(f"page tokens before: {before}")
        for n in range(1, TURNS + 1):
            await session.turn(log, f"Reply with the number {n} and nothing else.")
        plan_rows = [r for r in session.journal() if r["event"] in USAGE_EVENTS]
        log(f"plan journal rows: {[(r['event'], r['payload']['metadata']) for r in plan_rows]}")
        log.check("one plan row per turn", len(plan_rows) == TURNS, len(plan_rows))
        running = turns[-1].total_cost_usd
        indexed = {run["id"]: run for run in session.control.run_index.refresh()}
        run_row = indexed.get(session.chat) or session.control.run_index.get(session.chat)
        summed = Decimal(str(run_row["cost"]))
        log.check(
            "RunIndex sums the plan rows to the CLI's running cost within 0.0001",
            abs(summed - Decimal(str(running))) <= Decimal("0.0001"),
            f"RunIndex {summed} against ResultMessage {running}",
        )

        session.control.settings_put("providers", {**providers, "fake": fake_row(fake.url)})
        relayed = await session.harness.start_chat(
            NewChat(
                title="hp10 s24 relayed", model="haiku", profile="fake", workspace=args.workspace
            )
        )
        await session.harness.send(relayed, OperatorText("Say done."))
        await wait_turn(session.home, relayed)
        await asyncio.sleep(0.5)
        answered = [seen for seen in fake.requests if seen.method == "POST"]
        log(f"fake model POSTs: {[(seen.path, seen.scripted) for seen in answered]}")
        after = (await session.harness.usage()).tokens
        log(f"page tokens after: {after}")
        claude_calls = after.get("claude", {}).get("calls", 0) - before.get("claude", {}).get(
            "calls", 0
        )
        log.check("the page counts each plan turn once", claude_calls == TURNS, claude_calls)
        fake_sums = dict(after.get("fake", {}))
        messages = [s for s in answered if s.path.partition("?")[0].endswith("/v1/messages")]
        served = {
            "input_tokens": sum(u.get("input_tokens", 0) for u in fake.served_usage),
            "output_tokens": sum(u.get("output_tokens", 0) for u in fake.served_usage),
        }
        log.check(
            "the relayed chat is counted once, under its own profile",
            fake_sums.get("calls") == len(messages)
            and fake_sums.get("input_tokens") == served["input_tokens"]
            and fake_sums.get("output_tokens") == served["output_tokens"],
            (fake_sums, len(messages), served),
        )
    finally:
        session.control.settings_put("providers", providers)
        await session.harness.close()
        fake.stop()


def main() -> int:
    log = Log("hp10-s24")
    boot()
    use_fake_home()
    use_fake_key()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
