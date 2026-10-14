# ruff: noqa: S101
from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from pathlib import Path

from spend import Ledger, OverBudget, Prices

PRICES = Prices("deepseek/x", usd_per_input_token=1e-6, usd_per_output_token=2e-6)


def usage_from(values: list[float]) -> Callable[[], float]:
    readings = iter(values)
    return lambda: next(readings)


def rows(ledger: Ledger) -> list[list[str]]:
    return [line.split("\t") for line in ledger.path.read_text(encoding="utf-8").splitlines()]


def refused(call: Coroutine[object, object, str]) -> bool:
    try:
        asyncio.run(call)
    except OverBudget:
        return True
    return False


async def answer() -> str:
    return "ran"


def test_estimate_prices_every_call_at_the_input_allowance_and_the_output_cap() -> None:
    assert round(PRICES.estimate(calls=2, max_output=512), 9) == 0.082048


def test_the_total_is_the_key_usage_since_the_ledger_began_so_a_lagging_charge_still_counts(
    tmp_path: Path,
) -> None:
    path = tmp_path / "spend.tsv"
    ledger = Ledger(path, PRICES, usage_from([1.0, 1.2, 1.25, 1.3]), limit=0.6)

    assert asyncio.run(ledger.spend("B1", 1, 512, answer)) == "ran"
    assert asyncio.run(ledger.spend("B3", 1, 512, answer)) == "ran"

    assert [r[1:] for r in rows(ledger)][1:] == [
        ["B1", "1", "512", "0.041024", "1.000000", "1.200000", "0.200000", "0.200000", "SPENT"],
        ["B3", "1", "512", "0.041024", "1.250000", "1.300000", "0.050000", "0.300000", "SPENT"],
    ]


def test_a_call_that_would_pass_the_limit_is_refused_and_never_runs(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "spend.tsv", PRICES, usage_from([0.0, 0.35, 0.35]), limit=0.4)
    asyncio.run(ledger.spend("B1", 1, 512, answer))

    async def must_not_run() -> str:
        raise AssertionError("ran past the budget")

    assert refused(ledger.spend("B3", 2, 512, must_not_run))
    assert rows(ledger)[-1][1:] == [
        "B3", "2", "512", "0.082048", "0.350000", "", "0.000000", "0.350000", "REFUSED",
    ]  # fmt: skip


def test_a_new_ledger_on_the_same_file_counts_from_the_first_reading(tmp_path: Path) -> None:
    path = tmp_path / "spend.tsv"
    asyncio.run(Ledger(path, PRICES, usage_from([0.0, 0.3]), limit=0.4).spend("a", 1, 512, answer))

    assert refused(Ledger(path, PRICES, usage_from([0.3]), limit=0.4).spend("b", 3, 512, answer))


def test_without_a_key_usage_reading_each_call_is_charged_its_estimate(tmp_path: Path) -> None:
    ledger = Ledger(tmp_path / "spend.tsv", PRICES, lambda: None, limit=0.1)
    asyncio.run(ledger.spend("B1", 1, 512, answer))
    asyncio.run(ledger.spend("B3", 1, 512, answer))

    assert refused(ledger.spend("B4", 1, 512, answer))
    assert [r[-2] for r in rows(ledger)][1:] == ["0.041024", "0.082048", "0.082048"]
