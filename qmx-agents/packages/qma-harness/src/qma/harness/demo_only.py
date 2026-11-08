"""The demo-only blocker on a broker's MCP server (C-36, his ruling of 2026-11-03).

Agents get a broker server's tools as the broker ships them. The one control is the account they
act on. cTrader's Remote MCP binds its session to the one trading account its token was issued
for, and its tools take no account argument. So at every launch the harness asks the server which
account it is bound to, and offers it only when that account is an `account` record on the
Library's main with `world: demo` (C-34). A token swapped for a live account's is caught at the
next launch.
"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Mapping, Sequence
from typing import Final, cast

type AccountWorlds = Callable[[str], Sequence[str]]
"""The `world` of each live `account` record on the Library's main whose `account_id` is the given
id. The host passes it in; an empty answer means no record."""

type ServerCall = Callable[[str], Awaitable[object]]
"""Calls one of the server's tools with no arguments. Answers its JSON result, or None when the
tool answered an error or no JSON."""

VENUES: Final = frozenset({"ctrader"})
"""The `venue` values an `[mcp_servers]` row may name. A row naming one is checked here."""
DEMO_ONLY: Final = "agents use demo accounts only"
EXPIRED: Final = "cTrader refused the token (HTTP 401); copy a fresh cTrader MCP token"


class NotOffered(ValueError):
    """The server is left out for agents. The message is the note the chat and he read."""


async def demo_account(
    call: ServerCall, tools: frozenset[str], worlds: AccountWorlds | None
) -> str:
    """The id of the account the session is bound to, read from `get_balance`, or from
    `get_accounts_list` when that lists one account. Raises NotOffered unless every account
    record on main for that id says `world: demo`, and cTrader's own answers never mark it live."""
    if worlds is None:
        raise NotOffered(f"this host reads no account records, and {DEMO_ONLY}")
    balance = _rows([await call("get_balance")]) if "get_balance" in tools else []
    rows = _rows(await call("get_accounts_list")) if "get_accounts_list" in tools else []
    account = _account_id(balance[0]) if balance else None
    if account is None and len(rows) == 1:
        account = _account_id(rows[0])
    if account is None:
        raise NotOffered(f"the server named no account it is bound to, and {DEMO_ONLY}")
    listed = [row for row in rows if _account_id(row) == account]
    if any(row.get("isLive") is True for row in [*balance, *listed]):
        raise NotOffered(f"cTrader marks account {account} as live, and {DEMO_ONLY}")
    found = sorted(set(await asyncio.to_thread(worlds, account)))
    if not found:
        raise NotOffered(
            f"account {account} has no account record on the Library's main, and {DEMO_ONLY}"
        )
    if found != ["demo"]:
        raise NotOffered(f"account {account} is recorded as {' and '.join(found)}, and {DEMO_ONLY}")
    return account


def _account_id(answer: object) -> str | None:
    if not isinstance(answer, Mapping):
        return None
    row = cast("Mapping[str, object]", answer)
    found = row.get("traderId", row.get("ctidTraderAccountId"))
    if isinstance(found, int) and not isinstance(found, bool):
        return str(found)
    return found if isinstance(found, str) and found else None


def _rows(answer: object) -> list[Mapping[str, object]]:
    if isinstance(answer, Mapping):
        answer = cast("Mapping[str, object]", answer).get("accounts")
    if not isinstance(answer, list):
        return []
    return [
        cast("Mapping[str, object]", row)
        for row in cast("list[object]", answer)
        if isinstance(row, Mapping)
    ]
