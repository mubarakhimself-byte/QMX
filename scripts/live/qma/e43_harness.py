"""CAPH lane 2, the harness half of E43: QMX puts no budget and no turn cap on an unattended
chat (ruling 106). One Background turn on haiku through the ship home's plan login. The script
takes the lane lock `D:/QMX-worktrees/.engine-lane-lock` itself and removes it after; never
wrap it in an outer lock. It never writes the ship home's settings.toml and hashes it before
and after. `QMA_LOG_SLUG` names the log.

PASS when the ship home's [budgets] parse to no background cap, turn cap or spend cap, the
Background chat's launch options carry `max_turns` and `max_budget_usd` as None, the turn ends
with its answer, the chat shows no `needs_you` block, and the usage page has no cap field.
"""

from __future__ import annotations

import asyncio
import hashlib
import os
import sys
import time
from pathlib import Path
from typing import Final

from common import (
    SCRATCH,
    SHIP_HOME,
    Log,
    boot,
    capture_launches,
    require_login,
    session_blocks,
    use_fake_home,
    wait_turn,
)

LOCK: Final = Path("D:/QMX-worktrees/.engine-lane-lock")
LOCK_WAIT_S: Final = 1800.0
WORKSPACE: Final = SCRATCH / "caph-e43-ws"
WORD: Final = "MARIGOLD"


def settings_hash() -> str:
    return hashlib.sha256((SHIP_HOME / "settings.toml").read_bytes()).hexdigest()


def take_lock(log: Log) -> None:
    deadline = time.monotonic() + LOCK_WAIT_S
    while True:
        try:
            LOCK.mkdir()
        except FileExistsError:
            if time.monotonic() > deadline:
                raise SystemExit(f"{LOCK} stayed held for {LOCK_WAIT_S:.0f} s") from None
            time.sleep(10)
            continue
        log(f"took {LOCK}")
        return


async def lane(log: Log) -> None:
    from qma.harness import Harness, InjectedText, NewChat, QmxHome  # noqa: PLC0415
    from qma.harness.launch import Background, parse_budgets  # noqa: PLC0415
    from qma.harness.routes import control_service  # noqa: PLC0415

    home = QmxHome(SHIP_HOME)
    control = control_service(home)
    budgets = parse_budgets(control.settings_get("budgets"))
    log(f"ship home [budgets] parse to {budgets}")
    log.check(
        "no background cap, turn cap or spend cap is set",
        (budgets.background_cap, budgets.max_turns, budgets.max_budget_usd) == (None, None, None),
        (budgets.background_cap, budgets.max_turns, budgets.max_budget_usd),
    )
    launched = capture_launches()
    harness = await Harness.open(home, control=control)
    try:
        WORKSPACE.mkdir(parents=True, exist_ok=True)
        chat = await harness.start_chat(
            NewChat(title="caph e43", model="haiku", workspace=WORKSPACE, kind=Background())
        )
        log(f"background chat {chat}, five-hour reading {harness._ledger.reading('five_hour')}")
        await harness.send(chat, InjectedText(f"Reply with the single word {WORD}."))
        record = await wait_turn(home, chat, 300)
        options = launched[-1].options
        log(f"launch options max_turns={options.max_turns} max_budget_usd={options.max_budget_usd}")
        log.check(
            "the launch options hold no turn cap and no budget",
            (options.max_turns, options.max_budget_usd) == (None, None),
            (options.max_turns, options.max_budget_usd),
        )
        blocks = session_blocks(control, chat)
        log(f"blocks: {[(block['type'], str(block['content'])[:80]) for block in blocks]}")
        answered = any(
            block["type"] == "text" and WORD in str(block["content"]).upper() for block in blocks
        )
        log.check("the turn ended with its answer", record.turn == "idle" and answered, record.turn)
        needs = [block["content"] for block in blocks if block["type"] == "needs_you"]
        log.check("no needs_you block appears", not needs, needs)
        page = (await harness.usage()).document()
        log.check(
            "the usage page has no cap field",
            not [key for key in page if "cap" in key],
            sorted(page),
        )
    finally:
        await harness.close()


def main() -> int:
    log = Log(os.environ.get("QMA_LOG_SLUG", "caph-e43"))
    boot()
    use_fake_home()
    require_login(log)
    before = settings_hash()
    take_lock(log)
    try:
        asyncio.run(lane(log))
    finally:
        LOCK.rmdir()
        log(f"removed {LOCK}")
    after = settings_hash()
    log.check("the ship home's settings.toml is unchanged", before == after, after[:16])
    return log.verdict()


if __name__ == "__main__":
    sys.exit(main())
