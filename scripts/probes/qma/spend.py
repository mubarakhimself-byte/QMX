"""The HP1 OpenRouter spend guard. Every OpenRouter turn goes through `Ledger.spend`.

The CLI makes the HTTP calls, so a turn is the unit the guard can stop. Before a turn it
prices the worst case, `calls` requests each at `INPUT_TOKENS_PER_CALL` in and the output
cap out, and refuses the turn when the spend so far plus that estimate passes the limit.
The spend so far is the key's OpenRouter usage now minus its usage at the ledger's first
row, so a charge that lands late still counts. When usage cannot be read, each turn is
charged its estimate instead.
"""

from __future__ import annotations

import json
import time
import urllib.request
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, TypeVar

from common import HP1_EVIDENCE, Log, run_turns

if TYPE_CHECKING:
    from claude_agent_sdk import ClaudeAgentOptions, Message

BUDGET_USD: Final = 0.40
LEDGER: Final = HP1_EVIDENCE / "openrouter-spend.tsv"
INPUT_TOKENS_PER_CALL: Final = 40_000
"""Above the CLI's system prompt and tool list, which every request resends."""
SIDE_CALLS_PER_PROMPT: Final = 1
MAX_OUTPUT_VAR: Final = "CLAUDE_CODE_MAX_OUTPUT_TOKENS"
KEY_URL: Final = "https://openrouter.ai/api/v1/key"
T = TypeVar("T")
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


class OverBudget(Exception):
    pass


@dataclass(frozen=True)
class Ledger:
    path: Path
    prices: Prices
    usage: Callable[[], float | None]
    limit: float = BUDGET_USD

    def _rows(self) -> list[list[str]]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()[1:]
        return [line.split("\t") for line in lines]

    def _write(self, *cells: object) -> None:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text("\t".join(HEADER) + "\n", encoding="utf-8")
        ts = time.strftime("%Y-%m-%dT%H:%M:%S%z")
        with self.path.open("a", encoding="utf-8") as file:
            file.write("\t".join([ts, *map(str, cells)]) + "\n")

    async def spend(
        self, label: str, calls: int, max_output: int, run: Callable[[], Awaitable[T]]
    ) -> T:
        rows = self._rows()
        charged_sum = sum(float(r[7]) for r in rows)
        before = self.usage()
        baseline = next((float(r[5]) for r in rows if r[5]), before)

        def spent(reading: float | None, fallback: float) -> float:
            return fallback if reading is None or baseline is None else reading - baseline

        estimate = self.prices.estimate(calls, max_output)
        total = spent(before, charged_sum)
        cells = (label, calls, max_output, f"{estimate:.6f}", _usd(before))
        if total + estimate > self.limit:
            self._write(*cells, "", f"{0:.6f}", f"{total:.6f}", "REFUSED")
            raise OverBudget(f"{label}: {total:.6f} spent + {estimate:.6f} > {self.limit}")
        result = await run()
        after = self.usage()
        charged = after - before if before is not None and after is not None else estimate
        total = spent(after, charged_sum + charged)
        self._write(*cells, _usd(after), f"{charged:.6f}", f"{total:.6f}", "SPENT")
        return result


def _usd(value: float | None) -> str:
    return "" if value is None else f"{value:.6f}"


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


def max_output(options: ClaudeAgentOptions) -> int:
    env: dict[str, str] = dict(options.env)
    return int(env[MAX_OUTPUT_VAR])


async def guarded_turns(
    ledger: Ledger, log: Log, label: str, options: ClaudeAgentOptions, prompts: list[str]
) -> list[Message]:
    calls = len(prompts) * ((options.max_turns or 1) + SIDE_CALLS_PER_PROMPT)
    return await ledger.spend(
        label, calls, max_output(options), lambda: run_turns(log, options, prompts)
    )
