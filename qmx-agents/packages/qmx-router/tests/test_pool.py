"""The account pool at its public door: which account a lease takes, and what a refusal does.

Every account here is a fake credential name, and every time is a clock this test moves, so the
expected account and the expected cooldown are literals.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from qmx_router.classify import Classification, classify
from qmx_router.pool import AccountPool, AccountSpec, NoAccount
from qmx_router.profiles import ProfileName, SecretRef

KIMI = ProfileName("kimi")
OPENROUTER = ProfileName("openrouter")
START = datetime(2026, 10, 20, 18, 0, tzinfo=UTC)
RATE = {"type": "error", "error": {"type": "rate_limit_error", "message": "slow down"}}


class Clock:
    def __init__(self, at: datetime = START) -> None:
        self.at = at

    def __call__(self) -> datetime:
        return self.at

    def advance(self, seconds: float) -> None:
        self.at += timedelta(seconds=seconds)


def limited(status: int, body: object, headers: dict[str, str] | None = None) -> Classification:
    return classify(status, body, headers)


def one_key(priority: int | None = None) -> tuple[AccountPool, Clock]:
    clock = Clock()
    pool = AccountPool(
        [AccountSpec("kimi", KIMI, credential=SecretRef("qmx/kimi"), priority=priority)],
        clock=clock,
    )
    return pool, clock


def two_keys(priority: int | None = None, share: float | None = None) -> tuple[AccountPool, Clock]:
    clock = Clock()
    pool = AccountPool(
        [
            AccountSpec("kimi", KIMI, credential=SecretRef("qmx/kimi")),
            AccountSpec(
                "kimi#2", KIMI, credential=SecretRef("qmx/kimi-2"), priority=priority, share=share
            ),
        ],
        clock=clock,
    )
    return pool, clock


def test_least_used_spreads_eight_chats_evenly_over_two_accounts() -> None:
    pool, _ = two_keys()
    taken: list[str] = []
    for _ in range(8):
        lease = pool.lease(provider=KIMI, model="kimi-k3")
        taken.append(lease.account.id)
        pool.settle(lease)
    assert taken == ["kimi", "kimi#2"] * 4
    assert [view["leases"] for view in pool.accounts_view()] == [0, 0]


def test_least_used_keeps_live_leases_even() -> None:
    pool, _ = two_keys()
    held = [pool.lease(provider=KIMI, model="kimi-k3") for _ in range(4)]
    assert [lease.account.id for lease in held] == ["kimi", "kimi#2", "kimi", "kimi#2"]
    assert [view["leases"] for view in pool.accounts_view()] == [2, 2]


def test_round_robin_takes_the_least_recently_served_and_fill_first_the_first() -> None:
    clock = Clock()
    accounts = [
        AccountSpec("a", KIMI, credential=SecretRef("qmx/a")),
        AccountSpec("b", KIMI, credential=SecretRef("qmx/b")),
    ]
    round_robin = AccountPool(accounts, strategy="round_robin", clock=clock)
    order: list[str] = []
    for _ in range(3):
        lease = round_robin.lease(provider=KIMI, model="kimi-k3")
        order.append(lease.account.id)
        round_robin.settle(lease)
        clock.advance(1)
    assert order == ["a", "b", "a"]

    fill_first = AccountPool(accounts, strategy="fill_first", clock=clock)
    assert [fill_first.lease(provider=KIMI, model="kimi-k3").account.id for _ in range(2)] == [
        "a",
        "a",
    ]


def test_a_priority_he_sets_orders_one_account_ahead_of_unset_ones() -> None:
    pool, _ = two_keys(priority=-1)
    assert [pool.lease(provider=KIMI, model="kimi-k3").account.id for _ in range(2)] == [
        "kimi#2",
        "kimi#2",
    ]


def test_affinity_holds_one_account_until_the_run_ends() -> None:
    pool, _ = two_keys()
    first = pool.lease(provider=KIMI, model="kimi-k3", affinity="run-7:writer")
    again = pool.lease(provider=KIMI, model="kimi-k3", affinity="run-7:writer")
    assert first.account.id == again.account.id == "kimi"
    pool.settle(again)
    assert pool.state("kimi")[0] == "open"
    assert pool.lease(provider=KIMI, model="kimi-k3", affinity="run-7:writer").account.id == "kimi"
    pool.release_affinity("run-7:writer")
    assert pool.lease(provider=KIMI, model="kimi-k3").account.id == "kimi#2"


def test_a_429_with_retry_after_cools_that_model_and_moves_the_next_request() -> None:
    pool, clock = two_keys()
    pool.settle(
        pool.lease(provider=KIMI, model="kimi-k3"), limited(429, RATE, {"retry-after": "30"})
    )
    assert pool.state("kimi", "kimi-k3") == ("cooling", START + timedelta(seconds=30))
    assert pool.state("kimi", "kimi-k2.7-code")[0] == "open"

    second = pool.lease(provider=KIMI, model="kimi-k3")
    assert second.account.id == "kimi#2"
    pool.settle(second)

    clock.advance(30)
    assert pool.state("kimi", "kimi-k3") == ("probing", START + timedelta(seconds=30))
    served = pool.lease(provider=KIMI, model="kimi-k3")
    assert served.account.id == "kimi"
    pool.settle(served)
    assert pool.state("kimi", "kimi-k3")[0] == "open"


def test_a_generic_429_retries_the_same_account_once_then_cools_an_hour() -> None:
    pool, _ = one_key()
    pool.settle(pool.lease(provider=KIMI, model="kimi-k3"), limited(429, RATE))
    assert pool.state("kimi", "kimi-k3")[0] == "open"
    pool.settle(pool.lease(provider=KIMI, model="kimi-k3"), limited(429, RATE))
    assert pool.state("kimi", "kimi-k3") == ("cooling", START + timedelta(seconds=3600))


def test_a_429_whose_named_reset_has_passed_is_a_generic_429_not_a_probe_loop() -> None:
    """42 N13: a probing request answered by another 429 never returns straight to probing."""
    clock = Clock()
    pool = AccountPool([AccountSpec("kimi", KIMI, credential=SecretRef("qmx/kimi"))], clock=clock)
    past = {
        "error": {"message": "slow down", "resets_at": (START - timedelta(seconds=5)).isoformat()}
    }
    pool.settle(pool.lease(provider=KIMI, model="kimi-k3"), limited(429, past))
    assert pool.state("kimi", "kimi-k3")[0] == "open"
    pool.settle(pool.lease(provider=KIMI, model="kimi-k3"), limited(429, past))
    assert pool.state("kimi", "kimi-k3") == ("cooling", START + timedelta(seconds=3600))


def test_each_class_cools_what_it_names() -> None:
    pool, _ = two_keys()
    first = pool.lease(provider=KIMI, model="kimi-k3")
    assert first.account.id == "kimi"
    notice = pool.settle(first, limited(401, {"error": {"message": "Invalid API key"}}))
    assert notice is not None and notice.text.endswith(
        "It serves again when its credential is fixed and the pool is restarted."
    )
    assert pool.state("kimi") == ("benched", None)

    pool.settle(
        pool.lease(provider=KIMI, model="kimi-k3"),
        limited(402, {"error": {"message": "Insufficient credits"}}),
    )
    assert pool.state("kimi#2", "kimi-k3") == ("cooling", START + timedelta(seconds=3600))
    assert pool.state("kimi#2", "kimi-k2.7-code")[0] == "open"

    pool.settle(
        pool.lease(provider=KIMI, model="kimi-k2.7-code"),
        limited(400, {"error": {"message": "Model Not Exist"}}),
    )
    assert pool.state("kimi#2", "kimi-k2.7-code") == ("benched", None)
    assert pool.state("kimi#2", "kimi-k3")[0] == "cooling"


def test_a_transient_or_content_refusal_cools_nothing() -> None:
    pool, _ = one_key()
    for error in (limited(503, {}), limited(400, {"error": {"message": "safety"}})):
        pool.settle(pool.lease(provider=KIMI, model="kimi-k3"), error)
        assert pool.state("kimi", "kimi-k3")[0] == "open"


def test_a_wholly_cooling_provider_is_one_inbox_item_per_episode() -> None:
    pool, clock = two_keys()
    for _ in range(2):
        pool.settle(pool.lease(provider=KIMI, model="kimi-k3"), limited(402, {}))
    with pytest.raises(NoAccount) as raised:
        pool.lease(provider=KIMI, model="kimi-k3")
    assert raised.value.alert is True
    assert str(raised.value).startswith("every account for kimi is out for kimi-k3 (kimi, kimi#2)")

    clock.advance(3600)
    pool.settle(pool.lease(provider=KIMI, model="kimi-k3"))
    for _ in range(2):
        pool.settle(pool.lease(provider=KIMI, model="kimi-k3"), limited(402, {}))
    with pytest.raises(NoAccount) as again:
        pool.lease(provider=KIMI, model="kimi-k3")
    assert again.value.alert is True


def test_the_copilot_account_is_leased_last() -> None:
    pool = AccountPool(
        [
            AccountSpec(
                "copilot", KIMI, credential=SecretRef("qmx/kimi"), background_priority="last"
            ),
            AccountSpec("work", KIMI, credential=SecretRef("qmx/kimi-2")),
        ],
        clock=Clock(),
    )
    assert pool.lease(provider=KIMI, model="kimi-k3").account.id == "work"
    pool.settle(pool.lease(provider=KIMI, model="kimi-k3"), limited(401, {}))
    assert pool.lease(provider=KIMI, model="kimi-k3").account.id == "copilot"


def test_a_ceiling_and_a_share_he_sets_bound_an_account() -> None:
    clock = Clock()
    capped = AccountPool(
        [
            AccountSpec("a", KIMI, credential=SecretRef("qmx/a"), ceiling=1),
            AccountSpec("b", KIMI, credential=SecretRef("qmx/b")),
        ],
        clock=clock,
    )
    assert [capped.lease(provider=KIMI, model="kimi-k3").account.id for _ in range(3)] == [
        "a",
        "b",
        "b",
    ]

    shared = AccountPool(
        [
            AccountSpec("a", KIMI, credential=SecretRef("qmx/a"), share=0.5),
            AccountSpec("b", KIMI, credential=SecretRef("qmx/b")),
        ],
        clock=clock,
    )
    assert [shared.lease(provider=KIMI, model="kimi-k3").account.id for _ in range(4)] == [
        "a",
        "b",
        "b",
        "a",
    ]


def test_a_provider_with_no_account_is_a_plain_refusal() -> None:
    pool, _ = two_keys()
    with pytest.raises(NoAccount) as raised:
        pool.lease(provider=OPENROUTER, model="openrouter/deepseek/deepseek-v4.1-flash")
    assert raised.value.alert is False
    assert str(raised.value) == "no account is configured for openrouter"
