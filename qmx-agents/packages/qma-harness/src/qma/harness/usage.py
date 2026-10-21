"""Per-chat usage: the plan turn rows, the run journal sums and the doctor lines.

Per-turn tokens and cost live in each chat's run journal as `model_call` rows. A plan chat
writes one per turn from its `ResultMessage` through `plan_row`; a relayed chat's rows come from
the relay. What belongs to the account rather than to a chat, the plan's rate-limit windows, the
readings of how much of them is used and the overage stop, lives in `qmx_router.readings`.
"""

from __future__ import annotations

import json
from dataclasses import asdict, astuple, dataclass
from pathlib import Path
from typing import Any, Final

from qmx_router.profiles import PLAN
from qmx_router.readings import EXTRA_USAGE_ON, UsageLedger

from qma.harness.home import DoctorLine, QmxHome, SessionId
from qma.harness.project import TurnUsage

TOKEN_FIELDS: Final = ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens")


@dataclass(frozen=True)
class Totals:
    """A CLI process's running usage totals, summed over models."""

    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0

    @classmethod
    def of(cls, turn: TurnUsage) -> Totals:
        models = list(turn.model_usage.values())

        def total(key: str) -> int:
            return sum(int(model.get(key, 0)) for model in models)

        cost = turn.total_cost_usd
        if cost is None:
            cost = sum(float(model.get("costUSD", 0)) for model in models)
        return cls(
            cost_usd=cost,
            input_tokens=total("inputTokens"),
            output_tokens=total("outputTokens"),
            cache_read_tokens=total("cacheReadInputTokens"),
            cache_write_tokens=total("cacheCreationInputTokens"),
        )

    def since(self, base: Totals) -> Totals:
        """What was spent after `base`. A process that did not carry `base` over reports less
        than it, and then all it reports is new."""
        now, before = astuple(self), astuple(base)
        if any(value < held for value, held in zip(now, before, strict=True)):
            return self
        cost = round(self.cost_usd - base.cost_usd, 12)
        tokens = (value - held for value, held in zip(now[1:], before[1:], strict=True))
        return Totals(cost, *tokens)


def plan_row(turn: TurnUsage, base: Totals) -> tuple[dict[str, Any] | None, Totals]:
    """The `model_call` payload for one plan turn and the new running totals. None when the
    turn spent nothing, as a local command such as `/usage` does."""
    totals = Totals.of(turn)
    spent = totals.since(base)
    if spent == Totals():
        return None, totals
    payload: dict[str, Any] = {
        "agent": "primary",
        "model": ",".join(sorted(turn.model_usage)),
        "profile": PLAN,
        "path": "result",
        "input_tokens": spent.input_tokens,
        "output_tokens": spent.output_tokens,
        "cache_read_tokens": spent.cache_read_tokens,
        "cache_write_tokens": spent.cache_write_tokens,
        "metadata": {"cost": spent.cost_usd},
        "running_totals": asdict(totals),
    }
    return payload, totals


def journal_path(home: QmxHome, session: SessionId) -> Path:
    return home.root / "runs" / session / "journal.jsonl"


def plan_base(journal: Path) -> Totals:
    """The running totals after the last plan turn journaled for this chat. A resumed CLI
    starts from the session's earlier totals (measured, CLI 2.1.299)."""
    if not journal.exists():
        return Totals()
    base = Totals()
    for line in journal.read_bytes().splitlines():
        if b'"running_totals"' in line:
            payload = json.loads(line)["payload"]
            base = Totals(**payload["running_totals"])
    return base


def token_sums(runs: Path, chat: str = "*") -> dict[str, dict[str, int]]:
    """`model_call` rows summed per profile over every chat's run journal, or one `chat`'s,
    with a row count."""
    sums: dict[str, dict[str, int]] = {}
    for journal in sorted(runs.glob(f"{chat}/journal.jsonl")):
        for line in journal.read_bytes().splitlines():
            if b'"model_call"' not in line:
                continue
            try:
                record = json.loads(line)
                payload = record["payload"]
                if record["event"] != "model_call":
                    continue
                row = {key: int(payload.get(key) or 0) for key in TOKEN_FIELDS}
                profile = str(payload.get("profile", "unknown"))
            except ValueError, KeyError, TypeError:
                continue
            held = sums.setdefault(profile, dict.fromkeys((*TOKEN_FIELDS, "calls"), 0))
            for key, value in row.items():
                held[key] += value
            held["calls"] += 1
    return sums


def usage_lines(ledger: UsageLedger) -> list[DoctorLine]:
    stop = ledger.hard_stop()
    on = ledger.extra_usage_on()
    detail = {
        True: EXTRA_USAGE_ON,
        False: "extra usage is off for this account",
        None: "no plan reading yet",
    }[on]
    return [
        DoctorLine("plan overage stop", stop is None, stop or "no stop"),
        DoctorLine("plan extra usage", on is not True, detail),
    ]
