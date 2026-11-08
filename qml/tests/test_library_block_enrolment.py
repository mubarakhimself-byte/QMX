"""The socket contract enrols Library blocks and feeds each slot what its host really gives.

These are the three seams RC-01 names: a sizer at two percent meets the contract, a Library
sizer saved in a component-shaped folder is enrolled and judged with the stdlib message, and
the exit contract builds only the evidence the unit host builds.
"""
# pyright: reportPrivateUsage=false

from __future__ import annotations

from decimal import Decimal

import pytest
from qml.blocks.api import Size
from qml.compile import ExitUse

import test_socket_contracts as contracts


def test_a_sizer_at_two_percent_meets_the_contract(monkeypatch: pytest.MonkeyPatch) -> None:
    """At equity 100000 and a stop 0.0050 away on EURUSD, a fraction of 0.02 answers 4.00 lots
    and passes. The parent's fixed 0.005 ceiling fails it."""
    shipped = contracts._SHIPPED["fixed-fraction-at-stop@1"]
    trade = contracts._Trade(
        "eurusd at two percent",
        contracts._EURUSD,
        Decimal(100000),
        Decimal("1.08500"),
        Decimal("1.08000"),
    )
    monkeypatch.setattr(contracts, "_TRADES", (*contracts._TRADES, trade))
    params = {**shipped.params, "fraction": Decimal("0.02")}

    answer = shipped.block.make(params, {}).update(
        {
            "equity": trade.equity,
            "entry_price": trade.entry,
            "stop_price": trade.stop,
            "record": trade.record,
        }
    )

    assert isinstance(answer, Size)
    assert answer.lots == Decimal("4.00")
    assert contracts._sizer_breaks(shipped.block, params) == []


def test_a_library_sizer_is_enrolled() -> None:
    """A sizer saved in the component-shaped fixture folder is enrolled, and its float answer
    fails the contract with the message a stdlib block gets."""
    shipped = contracts._SHIPPED[contracts._COMPONENT_CONTROL]
    same_as_stdlib = contracts._sizer_breaks(contracts._Fake(0.25), {})

    assert shipped.face.component_type == "sizer"
    assert contracts._breaks(shipped) == same_as_stdlib
    assert same_as_stdlib == contracts._FLOAT_BREAKS


def test_the_exit_contract_feeds_only_host_evidence() -> None:
    """A stop is read with nothing once at entry to get its level, then fed its bar each bar, a
    target the entry and the stop once, and a per-bar exit nothing, which is exactly what `_Run`
    builds (`unit.py:756-760`, `:570-577`, `:774-779`, `:686`)."""
    bar = {
        "open": Decimal("1.0850"),
        "high": Decimal("1.0855"),
        "low": Decimal("1.0845"),
        "close": Decimal("1.0850"),
    }

    fed = {
        use: {frozenset(evidence) for _, evidence in contracts._host_calls(use, [bar], {})}
        for use in ExitUse
    }

    assert fed == {
        ExitUse.STOP: {frozenset({"series"}), frozenset()},
        ExitUse.TARGET: {frozenset({"entry_price", "stop_price"})},
        ExitUse.PER_BAR: {frozenset()},
    }
