"""The HP1 OpenRouter spend guard. Every OpenRouter turn goes through `Ledger.spend`.

The CLI makes the HTTP calls, so a turn is the unit the guard can stop. Before a turn it
prices the worst case, `calls` requests each at `INPUT_TOKENS_PER_CALL` in and the output
cap out, and refuses the turn when the ledger total plus that estimate passes the limit.
After it, the turn is charged the larger of the estimate and the key's usage delta from
OpenRouter, so a lagging usage figure never lowers the total.
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
    prompt: float
    """USD per input token, from the OpenRouter model list."""
    completion: float

    def estimate(self, calls: int, max_output: int) -> float:
        return calls * (INPUT_TOKENS_PER_CALL * self.prompt + max_output * self.completion)


class OverBudget(Exception):
    pass


@dataclass(frozen=True)
class Ledger:
    path: Path
    prices: Prices
    usage: Callable[[], float | None]
    limit: float = BUDGET_USD

    def total(self) -> float:
        if not self.path.exists():
            return 0.0
        lines = self.path.read_text(encoding="utf-8").splitlines()[1:]
        return sum(float(line.split("\t")[7]) for line in lines)

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
        estimate = self.prices.estimate(calls, max_output)
        total = self.total()
        if total + estimate > self.limit:
            self._write(
                label, calls, max_output, f"{estimate:.6f}", "", "", f"{0:.6f}", f"{total:.6f}",
                "REFUSED",
            )  # fmt: skip
            raise OverBudget(f"{label}: {total:.6f} spent + {estimate:.6f} > {self.limit}")
        before = self.usage()
        result = await run()
        after = self.usage()
        moved = after - before if before is not None and after is not None else 0.0
        charged = max(estimate, moved)
        self._write(
            label, calls, max_output, f"{estimate:.6f}", _usd(before), _usd(after),
            f"{charged:.6f}", f"{total + charged:.6f}", "SPENT",
        )  # fmt: skip
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
    """One extra call per prompt covers the CLI's side requests on the small tier."""
    calls = len(prompts) * ((options.max_turns or 1) + 1)
    return await ledger.spend(
        label, calls, max_output(options), lambda: run_turns(log, options, prompts)
    )
