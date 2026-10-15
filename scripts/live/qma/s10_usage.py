"""S10, plan usage and the overage stop. Plan turns run on the ship home's login on haiku.

    s10_usage.py meter     rate-limit events per plan turn, `/usage` reaching Python as a
                           meter reading, `GET /api/usage`, and the page's five-hour reading
                           against the CLI's own `/usage` text (operator check 12)
    s10_usage.py overage   the three overage facts, each fed in-process while a plan turn runs,
                           then the negative case
    s10_usage.py credits   a credits_required fact, fed the same way
    s10_usage.py merge     an older fact replayed after a newer one, no plan turn
    s10_usage.py expiry    a fact whose reset passes, no plan turn

A fed fact goes through the SDK's parser and `project`, as a CLI event would, then to the
harness's plan watch. PASS for a stop case when the running plan turn ends early with a
`needs_you` block naming the rule and the next plan send is refused naming it.
"""

from __future__ import annotations

import asyncio
import sys
import time
from datetime import timedelta
from typing import Any

from approval_lane import Host
from common import (
    SHIP_HOME,
    Log,
    Session,
    boot,
    chat_args,
    last_event,
    require_login,
    session_blocks,
    throwaway_home,
    use_fake_home,
    wait_turn,
)

SLEEP = "Run this exact Bash command, then reply done: sleep 40"
CLEAN: dict[str, Any] = {
    "status": "allowed",
    "overageStatus": "rejected",
    "overageDisabledReason": "out_of_credits",
    "isUsingOverage": False,
}
STOPS: dict[str, list[tuple[str, dict[str, Any], dict[str, Any]]]] = {
    "overage": [
        (
            "rule 2",
            {"status": "rejected", "rateLimitType": "five_hour", "overageStatus": "allowed"},
            {**CLEAN, "rateLimitType": "five_hour"},
        ),
        (
            "rule 1",
            {"status": "allowed", "rateLimitType": "five_hour", "isUsingOverage": True},
            {**CLEAN, "rateLimitType": "five_hour"},
        ),
        (
            "rule 3",
            {"status": "allowed", "rateLimitType": "overage"},
            {**CLEAN, "status": "rejected", "rateLimitType": "overage"},
        ),
    ],
    "credits": [
        (
            "rule 4",
            {
                "status": "rejected",
                "rateLimitType": "five_hour",
                "overageStatus": "rejected",
                "errorCode": "credits_required",
            },
            {**CLEAN, "rateLimitType": "five_hour"},
        )
    ],
}


def fact(**info: Any) -> Any:
    from claude_agent_sdk._internal.message_parser import parse_message  # noqa: PLC0415
    from qma.harness.project import project  # noqa: PLC0415

    info.setdefault("resetsAt", int(time.time()) + 3600)
    message = parse_message(
        {"type": "rate_limit_event", "rate_limit_info": info, "uuid": "u", "session_id": "s"}
    )
    (found,) = project(message)
    return found


def feed(session: Session, log: Log, info: dict[str, Any]) -> None:
    found = fact(**info)
    log(f"fed {found}")
    session.harness._deps.on_plan_limits(found)


async def refused(session: Session, text: str) -> str | None:
    from qma.harness import LaunchRefused, OperatorText  # noqa: PLC0415

    try:
        await session.harness.send(session.chat, OperatorText(text))
    except LaunchRefused as error:
        return str(error)
    await wait_turn(session.home, session.chat)
    return None


async def until_tool(session: Session, mark: int, seconds: float = 120) -> bool:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        for block in session_blocks(session.control, session.chat, mark):
            if block["type"] == "tool" and block["content"].get("state") == "started":
                return True
        await asyncio.sleep(0.3)
    return False


async def stop_case(
    session: Session, log: Log, rule: str, info: dict[str, Any], clear: dict[str, Any]
) -> None:
    from qma.harness import NewChat, OperatorText  # noqa: PLC0415

    workspace = session.harness._chat(session.chat).record.config.workspace
    session.chat = await session.harness.start_chat(
        NewChat(title=f"hp10 {rule}", model="haiku", mode="bypassPermissions", workspace=workspace)
    )
    feed(session, log, clear)
    mark = last_event(session.control, session.chat)
    await session.harness.send(session.chat, OperatorText(SLEEP))
    log.check(f"{rule}: a plan turn is running a tool", await until_tool(session, mark), True)
    fed_at = time.monotonic()
    feed(session, log, info)
    record = await wait_turn(session.home, session.chat, 30)
    took = time.monotonic() - fed_at
    reasons = [
        block["content"]["reason"]
        for block in session_blocks(session.control, session.chat, mark)
        if block["type"] == "needs_you"
    ]
    log.check(
        f"{rule}: the running plan chat was interrupted naming the rule",
        record.turn == "idle" and took < 30 and any(rule in reason for reason in reasons),
        (record.turn, f"{took:.1f} s", reasons),
    )
    answer = await refused(session, "say ok")
    log.check(
        f"{rule}: the next plan send is refused naming the rule",
        answer is not None and rule in answer,
        answer,
    )
    feed(session, log, clear)
    stop = session.harness._ledger.hard_stop()
    log.check(f"{rule}: a newer clean fact lifts the stop", stop is None, stop)


async def stops(log: Log, cases: str) -> None:
    args = chat_args(__doc__)
    args.add_argument("lane")
    parsed = args.parse_args()
    require_login(log)
    session = await Session.start(
        SHIP_HOME,
        model=parsed.model,
        workspace=parsed.workspace,
        title=f"hp10 {cases}",
        mode="bypassPermissions",
        tools=["Bash"],
    )
    try:
        for rule, info, clear in STOPS[cases]:
            await stop_case(session, log, rule, info, clear)
        if cases == "overage":
            feed(
                session,
                log,
                {
                    "status": "rejected",
                    "rateLimitType": "five_hour",
                    "overageStatus": "rejected",
                    "overageDisabledReason": "out_of_credits",
                },
            )
            page = await session.harness.usage()
            log.check("negative case: no overage stop", page.hard_stop is None, page.hard_stop)
    finally:
        await session.harness.close()


async def meter(log: Log) -> None:
    from qma.harness.harness import PlanWatch  # noqa: PLC0415
    from qma.harness.project import Limits, PlanMeter  # noqa: PLC0415

    args = chat_args(__doc__)
    args.add_argument("lane")
    parsed = args.parse_args()
    require_login(log)
    seen: list[Any] = []
    original = PlanWatch.__call__

    def counting(self: PlanWatch, found: Any) -> None:
        seen.append(found)
        original(self, found)

    PlanWatch.__call__ = counting  # type: ignore[method-assign]
    session = await Session.start(
        SHIP_HOME, model=parsed.model, workspace=parsed.workspace, title="hp10 s10"
    )
    try:
        for text in ("Reply with the single word ok.", "Reply with the single word yes."):
            before = len(seen)
            await session.turn(log, text)
            events = [found for found in seen[before:] if isinstance(found, Limits)]
            log(f"rate-limit events in this turn: {len(events)}: {events}")
        log.check("a plan turn's rate-limit events reach the ledger", bool(seen), len(seen))
        from_event = session.harness._ledger.reading("five_hour")
        log(f"five-hour reading from the event: {from_event}")
        metered = await session.harness.meter()
        log(f"five-hour reading after /usage: {metered}")
        meters = [found for found in seen if isinstance(found, PlanMeter)]
        log.check(
            "/usage reaches Python as text and becomes a meter reading (HP0 S10)",
            bool(meters) and metered is not None and metered.source == "usage_command",
            meters,
        )
        if from_event is not None and metered is not None:
            gap = abs(from_event.reading.utilization - metered.reading.utilization)
            log.check(
                "check 12: the event's five-hour reading is within 5 points of /usage",
                gap <= 0.05,
                f"{from_event.reading.utilization:.2f} against {metered.reading.utilization:.2f}",
            )
        else:
            log.check("check 12: both five-hour readings exist", False, (from_event, metered))
        async with Host(session) as host:
            reply = await host.http.get("/api/usage")
            page = reply.json()
        log(f"GET /api/usage {reply.status_code}: {page}")
        fields = {
            "windows",
            "readings",
            "tokens",
            "background_cap",
            "background_cap_note",
            "hard_stop",
            "extra_usage_on",
        }
        windows = page.get("windows", {}).get("claude", [])
        log.check("the page holds every field", fields <= set(page), sorted(set(page)))
        log.check(
            "each window has as_of and its overage fields",
            bool(windows)
            and all({"as_of", "overage_status", "using_overage"} <= set(w) for w in windows),
            windows,
        )
        log.check(
            "the page says the cap acts on the last reading",
            page.get("background_cap") == 0.5 and "last reading" in page["background_cap_note"],
            page.get("background_cap_note"),
        )
        log.check(
            "the plan turns are counted on the page",
            page["tokens"].get("claude", {}).get("calls", 0) >= 2,
            page["tokens"],
        )
        lines = session.harness.usage_lines()
        log(f"doctor lines: {lines}")
        log.check(
            "doctor and page agree on extra usage",
            (page["extra_usage_on"] is True) == (not lines[1].ok),
            (page["extra_usage_on"], lines[1]),
        )
    finally:
        await session.harness.close()


async def merge(log: Log) -> None:
    session = await Session.start(
        throwaway_home("hp10-merge"),
        model="haiku",
        workspace=throwaway_home("hp10-merge-ws"),
        title="hp10 merge",
    )
    try:
        ledger = session.harness._ledger
        now = ledger.clock()
        newer = fact(status="allowed", rateLimitType="five_hour", utilization=0.1)
        older = fact(status="allowed_warning", rateLimitType="five_hour", utilization=0.8)
        ledger.record(newer, now)
        ledger.record(older, now - timedelta(minutes=1))
        log(f"recorded {newer} at {now}, then {older} a minute earlier")
        page = (await session.harness.usage()).document()
        windows = page["windows"]["claude"]
        log(f"page windows: {windows}")
        log.check(
            "the newer fact stays on the page",
            [(w["status"], w["utilization"]) for w in windows] == [("allowed", 0.1)],
            windows,
        )
    finally:
        await session.harness.close()


async def expiry(log: Log) -> None:
    session = await Session.start(
        throwaway_home("hp10-expiry"),
        model="haiku",
        workspace=throwaway_home("hp10-expiry-ws"),
        title="hp10 expiry",
    )
    try:
        feed(
            session,
            log,
            {"status": "allowed", "rateLimitType": "seven_day", "resetsAt": int(time.time()) + 2},
        )
        shown = (await session.harness.usage()).document()["windows"]["claude"]
        log.check("the fact shows before its reset", len(shown) == 1, shown)
        await asyncio.sleep(3)
        gone = (await session.harness.usage()).document()["windows"]["claude"]
        log.check("the fact is gone once its reset passed", gone == [], gone)
    finally:
        await session.harness.close()


LANES = {
    "meter": ("hp10-s10", meter),
    "overage": ("hp10-overage", lambda log: stops(log, "overage")),
    "credits": ("hp10-credits", lambda log: stops(log, "credits")),
    "merge": ("hp10-merge", merge),
    "expiry": ("hp10-expiry", expiry),
}


def main() -> int:
    lane = sys.argv[1] if len(sys.argv) > 1 else ""
    if lane not in LANES:
        raise SystemExit(f"usage: s10_usage.py {{{','.join(LANES)}}}")
    slug, run = LANES[lane]
    log = Log(slug)
    boot()
    use_fake_home()
    asyncio.run(run(log))
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
