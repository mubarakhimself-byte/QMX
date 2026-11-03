"""The host's feed relay: the `mis` instance's landed board, passed to the trading node's
`[feeds.board]` (Part C slice C-22, connections C25; Level 0 AD-2 and AD-40).

The MIS lands its board at `data/board.json` in its volume after every round (C-09). Each pass
of the relay reads that file and writes it to `data/feeds/board.json` in the trading node's
volume, with each tier's board stamped with its age on this machine's clock. The node judges
that age against a placement read's `stale_after` on its own clock (`qmn/src/qmn/app/runtime.py`
`BoardFeed`), so no clock of this machine is ever compared with the node's.

The board is optional to every unit: a node with no board, a stale one or a withheld one trades
every admitted market on the unit's own conditions. So the relay never waits on the MIS and a
stopped MIS stops nothing. When the MIS has no usable board, the relay writes a withheld
document that says why. That covers no board, an unreadable one, one stamped after this
machine's clock, and one whose month the holdout seals.

One writer: only the relay writes the node's board file, by a whole-file replace, so a pass that
dies midway leaves the last board in place and the node sees it age out.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, cast

from qmx_apps.volume import Volume

__all__ = ["BOARD_SCHEMA", "RELAY_S", "Pass", "keep", "relay"]

RELAY_S: Final = 5.0
"""`[feeds] board_relay_s`, starting at 5 s: how often the relay passes the board."""
BOARD_SCHEMA: Final = "qmx.node.feed.board/1"
MIS: Final = "mis"
NODE: Final = "trading-node"
LANDED: Final = Path("data") / "board.json"
FEED: Final = Path("data") / "feeds" / "board.json"
FACTS: Final = Path("road") / "host" / "facts.json"


@dataclass(frozen=True, slots=True)
class Pass:
    """What one pass did: `relayed` the board, `withheld` it with `why`, or found `no node`."""

    word: str
    why: str = ""


def relay(home: Path, now_ns: int) -> Pass:
    """One pass over the apps home `home` at this machine's `now_ns`."""
    node = Volume(home, NODE).root
    if not (node / "data").is_dir():
        return Pass("no node")
    document = _relayed(Volume(home, MIS).root, now_ns)
    target = node / FEED
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(document, sort_keys=True), "utf-8")
    os.replace(temporary, target)
    withheld = document.get("withheld")
    return Pass("withheld", withheld) if isinstance(withheld, str) else Pass("relayed")


async def keep(
    home: Path, *, every_s: float = RELAY_S, clock_ns: Callable[[], int] = time.time_ns
) -> None:
    """Pass the board every `every_s` until cancelled. A pass that fails is named on stderr
    and the next pass runs as usual."""
    while True:
        try:
            await asyncio.to_thread(relay, home, clock_ns())
        except Exception as error:  # the relay keeps going; the node's board ages out meanwhile
            print(f"feed relay: the board was not passed this time: {error!r}", file=sys.stderr)
        await asyncio.sleep(every_s)


def _withheld(why: str) -> dict[str, object]:
    return {"schema_version": BOARD_SCHEMA, "withheld": why}


def _relayed(mis: Path, now_ns: int) -> dict[str, object]:
    try:
        raw: object = json.loads((mis / LANDED).read_bytes())
    except FileNotFoundError:
        return _withheld("the MIS has landed no board")
    except OSError, ValueError:
        return _withheld("the MIS's board could not be read")
    boards = cast("Mapping[str, object]", raw).get("boards") if isinstance(raw, dict) else None
    if not isinstance(boards, list):
        return _withheld("the MIS's board has no boards list")
    on, boundary = _holdout(mis)
    relayed: list[object] = []
    for item in cast("list[object]", boards):
        board = cast("Mapping[str, object]", item if isinstance(item, dict) else {})
        at = board.get("at")
        if type(at) is not int or not isinstance(board.get("tier"), str):
            return _withheld("a board of the MIS lacks its tier or its time")
        if at > now_ns:
            return _withheld("the MIS's board is stamped after this machine's clock")
        moment = datetime.fromtimestamp(at // 1_000_000_000, UTC)
        if on and (boundary is None or (moment.year, moment.month) >= boundary):
            return _withheld(f"the holdout seals {moment:%Y-%m}, the month of the MIS's board")
        relayed.append({**board, "age_ns": now_ns - at})
    return {"schema_version": BOARD_SCHEMA, "boards": relayed}


def _holdout(mis: Path) -> tuple[bool, tuple[int, int] | None]:
    """The holdout in the MIS's host facts, read by the MIS's own rule: whether it is on, and
    the first month it seals, every later month sealed too. Facts that are absent or unreadable,
    or a holdout on with no boundary, seal every month."""
    try:
        facts: object = json.loads((mis / FACTS).read_text("utf-8"))
    except OSError, ValueError:
        return True, None
    holdout = (
        cast("Mapping[str, object]", facts).get("holdout") if isinstance(facts, dict) else None
    )
    if not isinstance(holdout, dict):
        return True, None
    seal = cast("Mapping[str, object]", holdout)
    if seal.get("on") is False:
        return False, None
    boundary = seal.get("boundary")
    try:
        month = datetime.strptime(boundary, "%Y-%m") if isinstance(boundary, str) else None
    except ValueError:
        return True, None
    return True, None if month is None else (month.year, month.month)
