"""A spend guard for live checks that use a real OpenRouter key. Every real turn goes through
`Ledger.spend`, which takes the budget and the ledger path as parameters.

Before a turn it prices the worst case, `calls` requests each at `INPUT_TOKENS_PER_CALL` in
and `max_output` out, and refuses when the spend so far plus that estimate passes the budget.
The spend so far is the key's OpenRouter usage now minus its usage at the ledger's first row,
so a charge that lands late still counts. When usage cannot be read, a turn is charged its
estimate. The key is read from the keyring by name and never printed or stored.
"""

from __future__ import annotations

import json
import time
import urllib.request
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, TypeVar

T = TypeVar("T")
KEY_URL: Final = "https://openrouter.ai/api/v1/key"
INPUT_TOKENS_PER_CALL: Final = 40_000
"""Above the CLI's system prompt and tool list, which every request resends."""
HEADER: Final = (
    "ts", "label", "calls", "max_output", "estimate_usd", "key_usage_before",
    "key_usage_after", "charged_usd", "total_usd", "verdict",
)  # fmt: skip


@dataclass(frozen=True)
class Prices:
    model: str
    usd_per_input_token: float
    usd_per_output_token: float

    def estimate(self, calls: int, max_output: int) -> float:
        return calls * (
            INPUT_TOKENS_PER_CALL * self.usd_per_input_token
            + max_output * self.usd_per_output_token
        )


DEEPSEEK_FLASH: Final = Prices("deepseek/deepseek-v4.1-flash", 0.02016e-6, 0.891e-6)
"""OpenRouter list prices read 2026-10-14 (HP1 FINDINGS)."""


class OverBudget(Exception):
    pass


def openrouter_key() -> str | None:
    import keyring  # noqa: PLC0415

    return keyring.get_password("qmx/openrouter", "openrouter")


def key_usage(secret: str) -> Callable[[], float | None]:
    """The key's lifetime OpenRouter usage in USD, or None when the read fails."""

    def read() -> float | None:
        request = urllib.request.Request(KEY_URL, headers={"Authorization": f"Bearer {secret}"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310
                body: dict[str, Any] = json.load(response)
        except (OSError, ValueError):
            return None
        return float(body["data"]["usage"])

    return read


@dataclass(frozen=True)
class Ledger:
    path: Path
    budget: float
    prices: Prices
    usage: Callable[[], float | None]

    def _rows(self) -> list[list[str]]:
        if not self.path.exists():
            return []
        return [line.split("\t") for line in self.path.read_text(encoding="utf-8").splitlines()[1:]]

    def _write(self, *cells: object) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("\t".join(HEADER) + "\n", encoding="utf-8")
        with self.path.open("a", encoding="utf-8") as file:
            file.write("\t".join([time.strftime("%Y-%m-%dT%H:%M:%S%z"), *map(str, cells)]) + "\n")

    def spent(self) -> float:
        rows = self._rows()
        now = self.usage()
        baseline = next((float(r[5]) for r in rows if r[5]), None)
        if now is None or baseline is None:
            return sum(float(r[7]) for r in rows)
        return now - baseline

    async def spend(
        self, label: str, calls: int, max_output: int, run: Callable[[], Awaitable[T]]
    ) -> T:
        rows = self._rows()
        before = self.usage()
        baseline = next((float(r[5]) for r in rows if r[5]), before)
        charged_sum = sum(float(r[7]) for r in rows)

        def total(reading: float | None, fallback: float) -> float:
            return fallback if reading is None or baseline is None else reading - baseline

        estimate = self.prices.estimate(calls, max_output)
        so_far = total(before, charged_sum)
        cells = (label, calls, max_output, f"{estimate:.6f}", _usd(before))
        if so_far + estimate > self.budget:
            self._write(*cells, "", f"{0:.6f}", f"{so_far:.6f}", "REFUSED")
            raise OverBudget(f"{label}: {so_far:.6f} spent + {estimate:.6f} > {self.budget}")
        result = await run()
        after = self.usage()
        charged = after - before if before is not None and after is not None else estimate
        self._write(
            *cells,
            _usd(after),
            f"{charged:.6f}",
            f"{total(after, charged_sum + charged):.6f}",
            "SPENT",
        )
        return result


def _usd(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"
