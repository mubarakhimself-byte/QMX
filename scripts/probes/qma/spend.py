"""The OpenRouter spend guard. Every OpenRouter turn goes through `Ledger.spend`.

The CLI makes the HTTP calls, so a turn is the unit the guard can stop. Before a turn it
prices the worst case, `calls` requests each at the input allowance in and the output cap
out. OpenRouter's usage figure lags by minutes, so a turn's usage growth can read zero
while its charge is still on the way. Each turn is therefore charged the larger of its
estimate and its usage growth, and the spend so far is the larger of those charges' sum
and the usage growth since the ledger's first row. A figure that catches up past the
charges takes over. The guard refuses a turn when the spend so far plus its estimate
passes the limit. An OS lock beside the ledger is held from that check until the charge
is written, so two runs on one ledger cannot both pass it.
"""

from __future__ import annotations

import json
import time
import urllib.request
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, TypeVar

from common import Log, run_turns
from plants import exclusive

if TYPE_CHECKING:
    from claude_agent_sdk import ClaudeAgentOptions, Message

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
    input_tokens_per_call: int

    def estimate(self, calls: int, max_output: int) -> float:
        return calls * (
            self.input_tokens_per_call * self.usd_per_input_token
            + max_output * self.usd_per_output_token
        )


class OverBudget(Exception):
    pass


@dataclass(frozen=True)
class Ledger:
    path: Path
    prices: Prices
    usage: Callable[[], float | None]
    limit: float

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
        with exclusive(self.path.with_suffix(".lock")):
            rows = self._rows()
            charges = sum(float(r[7]) for r in rows)
            before = self.usage()
            baseline = next((float(r[5]) for r in rows if r[5]), before)

            def spent(reading: float | None, charged: float) -> float:
                if reading is None or baseline is None:
                    return charged
                return max(reading - baseline, charged)

            estimate = self.prices.estimate(calls, max_output)
            total = spent(before, charges)
            cells = (label, calls, max_output, f"{estimate:.6f}", _usd(before))
            if total + estimate > self.limit:
                self._write(*cells, "", f"{0:.6f}", f"{total:.6f}", "REFUSED")
                raise OverBudget(f"{label}: {total:.6f} spent + {estimate:.6f} > {self.limit}")
            try:
                return await run()
            finally:
                after = self.usage()
                growth = after - before if before is not None and after is not None else 0.0
                charge = max(estimate, growth)
                total = spent(after, charges + charge)
                self._write(*cells, _usd(after), f"{charge:.6f}", f"{total:.6f}", "SPENT")


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
    ledger: Ledger,
    log: Log,
    label: str,
    options: ClaudeAgentOptions,
    prompts: list[str],
    extra_calls: int = 0,
) -> list[Message]:
    """`extra_calls` covers requests a tool makes on its own, such as WebSearch's."""
    calls = len(prompts) * ((options.max_turns or 1) + SIDE_CALLS_PER_PROMPT) + extra_calls
    return await ledger.spend(
        label, calls, max_output(options), lambda: run_turns(log, options, prompts)
    )
