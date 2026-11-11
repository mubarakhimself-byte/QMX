"""Layer G's two functions over a ``HostedUnit`` on a recorded slice (AD-110, CONTRACTS.md 3.2).

``layer_g`` drives a compiled unit over a slice the host passes, with a small fill model so
the unit sees its own positions: an entry fills at the next bar's open on its side of the
quote, a protective stop or a target fills when a bar reaches it (the stop first when one bar
reaches both), and a close intent fills at the next bar's open. From those drives it returns:

- the safety half, ``Layer2Observations`` for the unchanged ``evaluate_layer2``: two fresh
  drives for determinism, a snapshot and restore halfway for restore equivalence, and every
  block's retained observations against its state bound;
- the behaviour half, the ``qmx.behaviour/1`` report, warnings only: trades per side, each
  exit fired or unfired, a trigger that never changes, one side only, and a control drive over
  the same bars shuffled within each day with their times kept.

QMB runs this inside its sandbox child and states ``loaded_in_isolation`` from there; the
in-process value a test passes is never proof of isolation.
"""

from __future__ import annotations

import bisect
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Final, Protocol, cast

from qmf.core.chrono import Instant
from qmf.core.fingerprint import Fingerprint, fingerprint, fingerprint_bytes
from qmf.core.refusal import is_refusal
from qmf.risk.facts import Fact
from qmf.risk.paper import ExecutionTarget

from qml.blocks.api import Instance
from qml.check.result import checker_version
from qml.compile import CompiledUnit, ExitUse
from qml.conformance.layer2 import Layer2Observations, evaluate_layer2
from qml.conformance.scan import scan_logic_source
from qml.protocol.unit import (
    OHLC,
    Account,
    DecisionRow,
    HostedUnit,
    OwnPosition,
    QuoteBar,
    RatePort,
    TraceLevel,
    UnitStep,
    construct_unit,
    restore_unit,
)
from qml.unit.model import Direction, Role, Side
from qml.unit.parse import Problem, ProblemKind

__all__ = ["BEHAVIOUR_SCHEMA", "LayerG", "layer_g"]

BEHAVIOUR_SCHEMA: Final[str] = "qmx.behaviour/1"
_DAY_NS: Final[int] = 86_400 * 1_000_000_000
_SCOPE: Final[str] = "layer-g"

Trace = tuple[tuple[dict[str, object], ...], ...]


class _Retains(Protocol):
    instances: dict[str, Instance]
    timers: dict[str, Instance]


@dataclass(frozen=True)
class LayerG:
    """The observations for ``evaluate_layer2`` and the behaviour report beside its verdict."""

    observations: Layer2Observations
    report: Mapping[str, object]
    warnings: tuple[Problem, ...]


class _At:
    def __init__(self, answer: Callable[[Instant], object]) -> None:
        self._answer = answer

    def at(self, instant: Instant, /) -> object:
        return self._answer(instant)


@dataclass
class _Sim:
    """The positions the unit holds while it is driven, and what filled them."""

    compiled: CompiledUnit
    bars: Mapping[str, Sequence[QuoteBar]]
    equity: Decimal
    rates: RatePort | None = None
    positions: dict[str, OwnPosition | None] = field(default_factory=dict[str, OwnPosition | None])
    protection: dict[str, tuple[Decimal, Decimal | None]] = field(
        default_factory=dict[str, tuple[Decimal, Decimal | None]]
    )
    pending_entry: dict[str, Mapping[str, object]] = field(
        default_factory=dict[str, Mapping[str, object]]
    )
    pending_close: set[str] = field(default_factory=set[str])
    fired: Counter[str] = field(default_factory=Counter[str])
    entries: list[tuple[int, str, Side]] = field(default_factory=list[tuple[int, str, Side]])
    opened: int = 0

    def latest(self, market: str) -> _At:
        series = self.bars.get(market, ())
        stamps = [b.knowable_at.value_ns for b in series]

        def answer(instant: Instant) -> QuoteBar | None:
            index = bisect.bisect_right(stamps, instant.value_ns)
            return series[index - 1] if index else None

        return _At(answer)

    def held(self, market: str) -> _At:
        """Every position held on ``market``, as the unit's own surface answers it (AD-25)."""

        def answer(_instant: Instant) -> tuple[OwnPosition, ...]:
            found = self.positions.get(market)
            return () if found is None else (found,)

        return _At(answer)

    def account(self, instant: Instant) -> Account:
        """The account facts at ``instant``: the check's equity and one rate per quote.

        A quote the host cannot price is left out of ``rates``, which the converter names
        ``rate_absent``; the check still runs and reports the skip.
        """
        if self.rates is None:
            return Account(self.equity)
        rates: dict[str, Fact] = {}
        for _, record in self.compiled.plan.markets:
            fact = self.rates.rate(record, instant)
            if fact is not None:
                rates[record.currency] = fact
        return Account(self.equity, self.rates.currency, MappingProxyType(rates))

    def surfaces(self) -> dict[str, _At]:
        stream = self.compiled.plan.stream
        out = {"account": _At(self.account), "own_journal": _At(lambda _i: ())}
        for market, _ in self.compiled.plan.markets:
            out[f"bars:{stream}:{market.market_id}"] = self.latest(market.market_id)
            out[f"own_position:{market.market_id}"] = self.held(market.market_id)
        return out

    def exit_name(self, use: ExitUse) -> str | None:
        return next((e.binding.name for e in self.compiled.plan.exits if e.use is use), None)

    def close(self, market: str, use: ExitUse) -> None:
        self.positions[market] = None
        self.protection.pop(market, None)
        name = self.exit_name(use)
        if name is not None:
            self.fired[name] += 1

    def fill(self, market: str, bar: QuoteBar) -> None:
        """What this bar fills for ``market`` before the unit sees it."""
        intent = self.pending_entry.pop(market, None)
        if market in self.pending_close:
            self.pending_close.discard(market)
            if self.positions.get(market) is not None:
                self.close(market, ExitUse.PER_BAR)
        if intent is not None and self.positions.get(market) is None:
            side = Side(cast("str", intent["direction"]))
            protection = cast("Mapping[str, object]", intent["protection"])
            targets = cast("list[Mapping[str, object]]", protection.get("targets", []))
            target = Decimal(cast("str", targets[0]["price"])) if targets else None
            self.opened += 1
            self.positions[market] = OwnPosition(
                f"g{self.opened}",
                side,
                Decimal(cast("str", intent["quantity"])),
                bar.ask.open if side is Side.LONG else bar.bid.open,
                self.compiled.compiled_fingerprint,
                bar.knowable_at,
            )
            self.protection[market] = (Decimal(cast("str", protection["stop"])), target)
        position = self.positions.get(market)
        if position is None:
            return
        stop, target = self.protection[market]
        quote: OHLC = bar.bid if position.side is Side.LONG else bar.ask
        if position.side is Side.LONG:
            stopped, reached = quote.low <= stop, target is not None and quote.high >= target
        else:
            stopped, reached = quote.high >= stop, target is not None and quote.low <= target
        if stopped:
            self.close(market, ExitUse.STOP)
        elif reached:
            self.close(market, ExitUse.TARGET)

    def take(
        self, wires: Sequence[Mapping[str, object]], instant: Instant
    ) -> tuple[dict[str, object], ...]:
        tuples = tuple(dict(wire) for wire in wires)
        held = {p.position_id: m for m, p in self.positions.items() if p is not None}
        for wire in tuples:
            if wire.get("intent_family") == "entry":
                market = cast("str", wire["market_id"])
                self.pending_entry[market] = wire
                self.entries.append(
                    (instant.value_ns, market, Side(cast("str", wire["direction"])))
                )
            else:
                ref = cast("Mapping[str, object]", wire["position_ref"])
                market = held.get(cast("str", ref["position_id"]))
                if market is not None:
                    self.pending_close.add(market)
        return tuples


def _instants(bars: Mapping[str, Sequence[QuoteBar]]) -> list[int]:
    return sorted({b.knowable_at.value_ns for series in bars.values() for b in series})


def _by_instant(bars: Mapping[str, Sequence[QuoteBar]]) -> dict[int, list[tuple[str, QuoteBar]]]:
    out: dict[int, list[tuple[str, QuoteBar]]] = {}
    for market, series in bars.items():
        for bar in series:
            out.setdefault(bar.knowable_at.value_ns, []).append((market, bar))
    return out


@dataclass
class _Drive:
    trace: list[tuple[dict[str, object], ...]] = field(
        default_factory=list[tuple[dict[str, object], ...]]
    )
    steps: list[UnitStep] = field(default_factory=list[UnitStep])
    rows: list[DecisionRow] = field(default_factory=list[DecisionRow])
    """The entry rows pricing wrote, kept beside the step's own rows for the trigger read."""


def _host(sim: _Sim, target: ExecutionTarget) -> HostedUnit:
    hosted = construct_unit(
        sim.compiled,
        read_surfaces=sim.surfaces(),
        scope_id=_SCOPE,
        execution_target=target,
        trace_level=TraceLevel.EVERY_BAR,
    )
    if is_refusal(hosted):
        raise ValueError(str(hosted.context))
    return hosted.value


def _run(
    sim: _Sim,
    unit: HostedUnit,
    instants: Sequence[int],
    drive: _Drive,
) -> None:
    by_instant = _by_instant(sim.bars)
    for ns in instants:
        for market, bar in by_instant.get(ns, ()):
            sim.fill(market, bar)
        step = unit.on_instant(Instant(ns))
        if is_refusal(step):
            raise ValueError(str(step.context))
        drive.steps.append(step.value)
        wires = [intent.to_wire() for intent in step.value.intents]
        for proposal in step.value.proposals:
            priced = unit.price(proposal, sim.account(step.value.instant))
            drive.rows.append(priced.row)
            if priced.intent is not None:
                wires.append(priced.intent.to_wire())
        drive.trace.append(sim.take(wires, step.value.instant))


def _bound_holds(unit: HostedUnit) -> bool:
    # HostedUnit exposes no retained count yet; its markets hold every block instance.
    core = unit._core  # pyright: ignore[reportPrivateUsage]
    markets = cast("Sequence[_Retains]", core.markets)
    return all(
        i.retained() <= i.state_bound
        for m in markets
        for i in (*m.instances.values(), *m.timers.values())
    )


def _shuffled(bars: Mapping[str, Sequence[QuoteBar]], seed: str) -> dict[str, list[QuoteBar]]:
    """Each market's bars with their prices permuted within each day, times kept."""
    out: dict[str, list[QuoteBar]] = {}
    for market, series in bars.items():
        days: dict[int, list[QuoteBar]] = {}
        for bar in series:
            days.setdefault(bar.knowable_at.value_ns // _DAY_NS, []).append(bar)
        shuffled: list[QuoteBar] = []
        for day in sorted(days):
            held = days[day]
            order = sorted(
                range(len(held)),
                key=lambda i: fingerprint_bytes(f"{seed}:{market}:{day}:{i}".encode()).value,
            )
            shuffled += [
                QuoteBar(held[i].knowable_at, held[j].bid, held[j].ask) for i, j in enumerate(order)
            ]
        out[market] = shuffled
    return out


def _slice_fingerprint(bars: Mapping[str, Sequence[QuoteBar]]) -> Fingerprint:
    rows = {
        market: [
            [b.knowable_at.value_ns]
            + [str(v) for v in (*b.bid.fields().values(), *b.ask.fields().values())]
            for b in series
        ]
        for market, series in sorted(bars.items())
    }
    made = fingerprint(rows)
    if is_refusal(made):  # pragma: no cover - only text and integers go in
        raise ValueError(str(made.context))
    return made.value


def _trigger_states(compiled: CompiledUnit, rows: Sequence[DecisionRow]) -> dict[Side, set[bool]]:
    """Per side, whether its trigger held on each bar after warm-up (every-bar rows)."""
    triggers = {
        side.side: {slot.name for slot in side.slots if slot.role is Role.TRIGGER}
        for side in compiled.plan.sides
    }
    states: dict[Side, set[bool]] = {side: set() for side in triggers}
    for row in rows:
        if row.outcome == "suppressed_warming" or not triggers.get(row.side):
            continue
        if row.outcome == "taken" and row.reason.startswith("time exit"):
            continue
        held = row.outcome != "no_signal" or row.reason.startswith("near miss")
        states[row.side].add(held)
    return states


def _warn(kind: ProblemKind, where: str, message: str, hint: str) -> Problem:
    return Problem(kind, (where,), message[:300], hint[:300], "G")


def _trigger_where(compiled: CompiledUnit, side: Side) -> str:
    plan = next(s for s in compiled.plan.sides if s.side is side)
    slot = next(s.name for s in plan.slots if s.role is Role.TRIGGER)
    return f"/logic/{side.value}/slots/{slot}"


def layer_g(
    compiled: CompiledUnit,
    sources: Mapping[str, bytes],
    bars: Mapping[str, Sequence[QuoteBar]],
    *,
    execution_target: ExecutionTarget,
    equity: Decimal,
    loaded_in_isolation: bool,
    may_not_trade_on_slice: bool = False,
    data_card_ref: str = "",
    rates: RatePort | None = None,
) -> LayerG:
    """Both halves of layer G for ``compiled`` on ``bars`` (closed bars by market id).

    ``rates`` is the host's ``market.rate:<quote>`` port over the same slice, so a unit quoting
    another currency is sized instead of skipping every entry ``rate_absent`` (AD-10).
    """
    instants = _instants(bars)
    first, second, split, control = _Drive(), _Drive(), _Drive(), _Drive()
    sim = _Sim(compiled, bars, equity, rates)
    unit = _host(sim, execution_target)
    _run(sim, unit, instants, first)
    bound_holds = _bound_holds(unit)
    _run(
        other := _Sim(compiled, bars, equity, rates),
        _host(other, execution_target),
        instants,
        second,
    )
    resumed = _Sim(compiled, bars, equity, rates)
    half = len(instants) // 2
    head = _host(resumed, execution_target)
    _run(resumed, head, instants[:half], split)
    restored = restore_unit(
        head.snapshot(),
        compiled,
        read_surfaces=resumed.surfaces(),
        scope_id=_SCOPE,
        execution_target=execution_target,
        trace_level=TraceLevel.EVERY_BAR,
    )
    if is_refusal(restored):
        raise ValueError(str(restored.context))
    _run(resumed, restored.value, instants[half:], split)

    slice_fp = _slice_fingerprint(bars)
    scan = scan_logic_source(
        {
            f"{e.entry_id}-{e.version}/block.py": sources[e.pin].decode("utf-8")
            for e in compiled.lock
            if e.pin in sources
        }
    )
    if is_refusal(scan):
        raise ValueError(str(scan.context))
    per_bar = any(e.use is ExitUse.PER_BAR for e in compiled.plan.exits)
    observations = Layer2Observations(
        loaded_in_isolation=loaded_in_isolation,
        book_present=False,
        scan=scan.value,
        golden_slice_fingerprint=slice_fp,
        declaration_fingerprint=compiled.compiled_fingerprint,
        first_run=tuple(first.trace),
        second_run=tuple(second.trace),
        emitted_kinds=tuple(
            "entry" if w.get("intent_family") == "entry" else cast("str", w["kind"])
            for instant in (*first.trace, *second.trace)
            for w in instant
        ),
        permitted_exit_intents=("close_full",) if per_bar else (),
        state_bound_holds=bound_holds,
        restore_equivalent=tuple(split.trace) == tuple(first.trace),
    )
    verdict = evaluate_layer2(observations)

    shuffled = _shuffled(bars, slice_fp.value)
    shuffled_sim = _Sim(compiled, shuffled, equity, rates)
    _run(shuffled_sim, _host(shuffled_sim, execution_target), instants, control)

    long_entries = sum(1 for _, _, side in sim.entries if side is Side.LONG)
    short_entries = len(sim.entries) - long_entries
    exit_names = [e.binding.name for e in compiled.plan.exits]
    unfired = [name for name in exit_names if not sim.fired[name]]
    states = _trigger_states(
        compiled,
        (*[row for step in first.steps for row in step.decisions], *first.rows),
    )
    constant = [side for side, seen in states.items() if len(seen) <= 1]
    both = compiled.unit.direction is Direction.BOTH
    one_side = both and bool(sim.entries) and (long_entries == 0 or short_entries == 0)
    matches = set(shuffled_sim.entries) == set(sim.entries)

    warnings: list[Problem] = []
    if not sim.entries and not may_not_trade_on_slice:
        warnings.append(
            _warn(
                ProblemKind.NO_TRADES,
                "",
                "the unit entered no trade on the slice",
                "loosen a condition, or declare that it may not trade on this slice",
            )
        )
    if one_side:
        traded = "long" if long_entries else "short"
        warnings.append(
            _warn(
                ProblemKind.ONE_SIDE_ONLY,
                "/direction",
                f"the unit trades both sides and every entry on the slice was {traded}",
                "check the other side's conditions and numbers",
            )
        )
    for index, binding in enumerate(compiled.unit.exit_set):
        if binding.name in unfired:
            warnings.append(
                _warn(
                    ProblemKind.EXITS_UNFIRED,
                    f"/exit_set/{index}",
                    f"the exit {binding.name} never fired on the slice",
                    "check its number, or test on a longer slice",
                )
            )
    for side in constant:
        warnings.append(
            _warn(
                ProblemKind.SIGNAL_CONSTANT,
                _trigger_where(compiled, side),
                f"the {side.value} trigger never changed on the slice",
                "a trigger that never changes never decides anything",
            )
        )
    if matches and sim.entries:
        warnings.append(
            _warn(
                ProblemKind.SHUFFLED_DAY_MATCHES,
                "",
                "the unit entered the same trades on bars shuffled within each day",
                "its decisions do not depend on the order of prices",
            )
        )

    safety: dict[str, object] = {"verdict": "fail" if is_refusal(verdict) else "pass"}
    if is_refusal(verdict):
        safety["failed_check"] = str(verdict.context.get("field", ""))
    else:
        made = verdict.value.fingerprint_content()
        safety["layer2_verdict_fingerprint"] = None if is_refusal(made) else made.value.value
    report: dict[str, object] = {
        "schema": BEHAVIOUR_SCHEMA,
        "slice": {
            "data_card_ref": data_card_ref,
            "market_ids": sorted(bars),
            "from": instants[0] if instants else None,
            "to": instants[-1] if instants else None,
            "fingerprint": slice_fp.value,
        },
        "safety": safety,
        "trades": len(sim.entries),
        "entries_long": long_entries,
        "entries_short": short_entries,
        "may_not_trade_on_slice": may_not_trade_on_slice,
        "exits_fired": {name: sim.fired[name] for name in exit_names},
        "exits_unfired": unfired,
        "signal_constant": bool(constant),
        "one_side_only": one_side,
        "shuffled_day_control": {
            "decisions_equal_to_real": matches,
            "trades": len(shuffled_sim.entries),
        },
        "warnings": [
            {"kind": p.kind.value, "where": list(p.where), "message": p.message} for p in warnings
        ],
        "compiled_fingerprint": compiled.compiled_fingerprint.value,
        "checker_version": checker_version(),
    }
    return LayerG(observations, report, tuple(warnings))
