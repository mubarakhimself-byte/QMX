"""P7, the account pool probe: two keys under one provider row, and a 429 on the first.

    p7_pool.py p7     the probe: key 1 cools 30 s, the next request takes key 2, it switches
                      back after the cooldown, and the class is rate_limit
    p7_pool.py perf   the section's perf block: 1,000 leases over 50 accounts, median in ms

Run it from `qmx-agents/` with every `ANTHROPIC_*` and `CLAUDE*` name and `NODE_USE_SYSTEM_CA`
unset, and `QMA_EVIDENCE_DIR` naming this PR's evidence folder:

    uv run --no-sync python ../scripts/probes/router/p7_pool.py p7

The relay binds loopback and the upstream is in process, so nothing is spent and no real key is
read: the two keys are fake strings this script hands the relay's secret lookup. Exit 1 on any
FAIL.
"""

from __future__ import annotations

import asyncio
import json
import os
import statistics
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import httpx

from qmx_router.classify import classify
from qmx_router.ids import SessionId
from qmx_router.pool import AccountPool, AccountSpec
from qmx_router.profiles import ProfileName, Profiles, SecretRef, parse_profiles
from qmx_router.relay import Relay, RelayUsage

EVIDENCE: Final = Path(os.environ.get("QMA_EVIDENCE_DIR", "D:/QMX-worktrees/qma-ship/build/evidence/rtr4"))
KIMI: Final = ProfileName("kimi")
MODEL: Final = "kimi-k3"
COOLDOWN_S: Final = 30.0
KIMI_ROW: Final[dict[str, Any]] = {
    "base_url": "https://api.moonshot.ai/anthropic",
    "credential_ref": "qmx/kimi-1",
    "tiers": dict.fromkeys(("opus", "sonnet", "haiku", "fable"), MODEL),
}

FAKE_KEYS: Final = {"qmx/kimi-1": "key-one", "qmx/kimi-2": "key-two"}
FAILS: list[str] = []


def log(line: str) -> None:
    print(line, flush=True)


def verdict(ok: bool, line: str) -> None:
    if not ok:
        FAILS.append(line)
    log(f"{'PASS' if ok else 'FAIL'} {line}")


def stream(served: str = MODEL) -> bytes:
    """One finished Anthropic-wire stream, as a chat's reply."""
    events = (
        ("message_start", {"message": {"model": served, "usage": {"input_tokens": 4}}}),
        ("content_block_delta", {"delta": {"type": "text_delta", "text": "ok"}}),
        ("message_delta", {"usage": {"output_tokens": 1}}),
        ("message_stop", {}),
    )
    return b"".join(
        f"event: {name}\ndata: {json.dumps(data)}\n\n".encode() for name, data in events
    )


@dataclass
class Upstream:
    """The fake Kimi host: key one is rate limited once, key two always answers."""

    limited: bool = True
    seen: list[str] = field(default_factory=list[str])

    def __call__(self, request: httpx.Request) -> httpx.Response:
        key = request.headers.get("authorization", "").removeprefix("Bearer ")
        self.seen.append(key)
        if key == "key-one" and self.limited:
            self.limited = False
            return httpx.Response(
                429,
                json={
                    "type": "error",
                    "error": {"type": "rate_limit_error", "message": "slow down"},
                },
                headers={"retry-after": str(int(COOLDOWN_S))},
            )
        return httpx.Response(
            200, content=stream(), headers={"content-type": "text/event-stream"}
        )


@dataclass
class Journals:
    rows: list[RelayUsage] = field(default_factory=list[RelayUsage])

    def open(self, _session: SessionId) -> Writer:
        return Writer(self)


@dataclass
class Writer:
    journals: Journals

    def append(self, usage: RelayUsage) -> None:
        self.journals.rows.append(usage)

    def close(self) -> None:
        return None


async def ask(relay: Relay, grant: str) -> httpx.Response:
    async with httpx.AsyncClient(base_url=relay.base_url, trust_env=False) as client:
        return await client.post(
            "/v1/messages",
            json={"model": MODEL, "max_tokens": 8, "messages": [{"role": "user", "content": "hi"}]},
            headers={"authorization": f"Bearer {grant}"},
        )


def two_accounts() -> AccountPool:
    return AccountPool(
        [
            AccountSpec("kimi#1", KIMI, credential=SecretRef("qmx/kimi-1")),
            AccountSpec("kimi#2", KIMI, credential=SecretRef("qmx/kimi-2")),
        ]
    )


async def p7() -> None:
    journals = Journals()
    upstream = Upstream()

    async def alert(_session: SessionId, reason: str) -> None:
        log(f"  alert: {reason}")

    def profiles() -> Profiles:
        return parse_profiles({"kimi": KIMI_ROW})

    pool = two_accounts()
    relay = await Relay(
        secrets=FAKE_KEYS.__getitem__,
        journal=journals.open,
        alert=alert,
        profiles=profiles,
        pool=pool,
        transport=httpx.MockTransport(upstream),
    ).start()
    try:
        grant = await relay.grant(SessionId("p7-chat"), KIMI)
        first = await ask(relay, grant.secret)
        state, until = pool.state("kimi#1", MODEL)
        cooled = None if until is None else round(until.timestamp() - time.time(), 1)
        log(f"  first request key={upstream.seen[-1]} status={first.status_code} state={state}")
        verdict(first.status_code == 429, "the first request reached key 1 and got the 429")
        verdict(state == "cooling" and cooled is not None and 29 <= cooled <= 30,
                f"key 1 cooled about {int(COOLDOWN_S)} s (state={state}, {cooled} s left)")
        verdict(classify(429, first.json(), dict(first.headers)).kind == "rate_limit",
                "the class is rate_limit")

        second = await ask(relay, grant.secret)
        log(f"  second request key={upstream.seen[-1]} status={second.status_code}")
        verdict(second.status_code == 200 and upstream.seen[-1] == "key-two",
                "the next request took key 2")
        verdict(
            [row.status for row in journals.rows] == [429, 200]
            and journals.rows[-1].model == MODEL,
            "the journal holds key 1's 429 and key 2's answer",
        )

        time.sleep(COOLDOWN_S + 1)
        third = await ask(relay, grant.secret)
        log(f"  third request key={upstream.seen[-1]} status={third.status_code}")
        verdict(third.status_code == 200 and upstream.seen[-1] == "key-one",
                "it switched back to key 1 after the cooldown")
        verdict(pool.state("kimi#1", MODEL)[0] == "open",
                "a served request lifted key 1's probing state")
    finally:
        await relay.close()
    verdict(not relay.grants and pool.state("kimi#1")[0] == "open", "the relay closed clean")


def perf() -> None:
    """1,000 leases over 50 accounts: the median, and the whole distribution in the log."""
    pool = AccountPool(
        [
            AccountSpec(f"kimi#{n}", KIMI, credential=SecretRef(f"qmx/kimi-{n}"))
            for n in range(50)
        ]
    )
    samples: list[float] = []
    for _ in range(1000):
        started = time.perf_counter()
        lease = pool.lease(provider=KIMI, model=MODEL)
        samples.append((time.perf_counter() - started) * 1000)
        pool.settle(lease)
    ordered = sorted(samples)
    median = statistics.median(ordered)
    log(
        f"  leases=1000 accounts=50 median_ms={median:.4f} p95_ms={ordered[949]:.4f} "
        f"max_ms={ordered[-1]:.4f}"
    )
    for account in pool.accounts_view()[:3]:
        log(f"  {account.id} state={account.state} leases={account.leases}")
    verdict(median <= 5.0, f"median lease time with 50 accounts is {median:.4f} ms, at most 5 ms")


def main(argv: list[str]) -> int:
    if not argv:
        raise SystemExit(__doc__)
    match argv[0]:
        case "p7":
            asyncio.run(p7())
        case "perf":
            perf()
        case _:
            raise SystemExit(__doc__)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
