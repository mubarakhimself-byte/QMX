"""E8, the pool under several chats: eight fake chats over two accounts.

Run it from `qmx-agents/` with every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`
unset, and `QMA_EVIDENCE_DIR` naming this PR's evidence folder:

    uv run --no-sync python ../scripts/live/router/e08_pool.py

No model turns and no keys: the accounts are fake names this script hands the pool. Pass when the
eight chats spread 4 and 4 by `least_used`, a 429 closes one account and the next chat lands on
the other, and a running chat keeps the account it holds. Exit 1 on any FAIL.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from typing import Final

from qmx_router.classify import classify
from qmx_router.pool import AccountPool, AccountSpec
from qmx_router.profiles import ProfileName, SecretRef

KIMI: Final = ProfileName("kimi")
MODEL: Final = "kimi-k3"
CHATS: Final = 8
FAILS: list[str] = []


class Clock:
    def __init__(self) -> None:
        self.at = datetime(2026, 10, 20, 18, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.at


def log(line: str) -> None:
    print(line, flush=True)


def verdict(ok: bool, line: str) -> None:
    if not ok:
        FAILS.append(line)
    log(f"{'PASS' if ok else 'FAIL'} {line}")


def eight_chats() -> None:
    clock = Clock()
    pool = AccountPool(
        [
            AccountSpec("kimi#1", KIMI, credential=SecretRef("qmx/kimi-1")),
            AccountSpec("kimi#2", KIMI, credential=SecretRef("qmx/kimi-2")),
        ],
        clock=clock,
    )
    taken: dict[str, str] = {}
    for number in range(CHATS):
        lease = pool.lease(provider=KIMI, model=MODEL, affinity=f"chat-{number}:kimi")
        taken[f"chat-{number}"] = lease.account.id
    spread = [list(taken.values()).count(account) for account in ("kimi#1", "kimi#2")]
    log(f"  eight chats landed {taken}")
    verdict(spread == [4, 4], f"least_used spread eight chats as {spread[0]} and {spread[1]}")
    for view in pool.accounts_view():
        log(f"  {view.id} state={view.state} leases={view.leases} reading={view.reading}")

    cooldown = classify(
        429, {"type": "error", "error": {"type": "rate_limit_error"}}, {"retry-after": "30"}
    )
    pool.settle(pool.lease(provider=KIMI, model=MODEL, affinity="chat-0:kimi"), cooldown)
    log(f"  {cooldown.kind} closed chat-0's account {taken['chat-0']}")

    kept = pool.lease(provider=KIMI, model=MODEL, affinity="chat-1:kimi")
    verdict(
        kept.account.id == taken["chat-1"] != taken["chat-0"],
        "a running chat kept its account while another account cooled",
    )

    moved = pool.lease(provider=KIMI, model=MODEL, affinity="chat-8:kimi")
    log(f"  chat-8 landed on {moved.account.id}")
    verdict(
        moved.account.id == taken["chat-1"], "a 429 moved the next chat to the other account"
    )

    clock.at += timedelta(seconds=31)
    back = pool.lease(provider=KIMI, model=MODEL, affinity="chat-0:kimi")
    verdict(
        back.account.id == taken["chat-0"],
        "chat-0 moved back to its account after the cooldown",
    )

    pool.release_prefix("chat-")
    verdict(
        all(view.leases == 0 for view in pool.accounts_view()),
        "every affinity gave its account back",
    )


def main() -> int:
    eight_chats()
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
