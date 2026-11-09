"""The feasibility verdict: one minimum lot at this stop against the share (FUNNEL I17).

A share of 5.00 USD on EURUSD at stop distance 0.0050 buys exactly the 0.01 minimum lot, so the
verdict is ``fits``. A share of 4.99 is 0.01 short, so the verdict is ``below_min_lot`` and says
what it lacks. The verdict reaches its answer through the one converter, by a recording call.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest
from qmf.core.chrono import Instant
from qmf.core.refusal import is_refusal
from qmf.risk.facts import Fact

import qml.numbers.convert as convert_module
import qml.numbers.feasible as feasible_module
from qml.blocks.api import Amount
from qml.numbers.convert import RoundRule
from qml.numbers.feasible import BELOW_MIN_LOT, FITS, feasibility
from qml.numbers.records import InstrumentRecord, parse_record

_RECORDS = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "records"
_OPEN = Instant(1_000_000_000_000_000_000)
_ENTRY = Decimal("1.10000")
_STOP = Decimal("1.09500")


def _record(name: str = "eurusd") -> InstrumentRecord:
    parsed = parse_record(json.loads((_RECORDS / f"{name}.json").read_text("utf-8")))
    assert not is_refusal(parsed), parsed
    return parsed.value


def _usd() -> Fact:
    """The rate when the account is in the record's quote currency: one, fresh."""
    return Fact(Decimal(1), _OPEN, "open", "the account is in the record's quote currency")


def _rule() -> RoundRule:
    return RoundRule(now=_OPEN)


def test_one_lot_fits_or_says_not() -> None:
    record = _record()
    assert (record.min_lot, record.value_per_point) == (Decimal("0.01"), Decimal("100000"))

    fits = feasibility(Decimal("5.00"), _ENTRY, _STOP, record, _usd(), _rule())
    short = feasibility(Decimal("4.99"), _ENTRY, _STOP, record, _usd(), _rule())

    assert (fits.word, fits.quantity, fits.shortfall, fits.residue_r) == (
        FITS,
        Decimal("0.01"),
        Decimal("0"),
        Decimal("0"),
    )
    assert (short.word, short.quantity, short.shortfall) == (
        BELOW_MIN_LOT,
        None,
        Decimal("0.01"),
    )
    assert fits.document() == {
        "verdict": "fits",
        "shortfall": "0",
        "quantity": "0.01",
        "residue_r": "0",
    }
    assert short.document()["verdict"] == "below_min_lot"


def test_a_skip_that_is_not_the_minimum_lot_keeps_its_own_word() -> None:
    verdict = feasibility(Decimal("5.00"), _ENTRY, None, _record(), _usd(), _rule())

    assert (verdict.word, verdict.shortfall, verdict.quantity) == (
        "stop_absent",
        Decimal("0"),
        None,
    )
    assert not verdict.fits


def test_the_verdict_asks_the_one_converter(monkeypatch: pytest.MonkeyPatch) -> None:
    """The blast-radius fact: the verdict computes through ``to_quantity``, by a recording call."""
    calls: list[tuple[Amount, Decimal, Decimal | None]] = []
    real: Callable[..., Any] = convert_module.to_quantity

    def recording(
        amount: Amount, entry: Decimal, stop: Decimal | None, *rest: object
    ) -> object:
        calls.append((amount, entry, stop))
        return real(amount, entry, stop, *rest)

    monkeypatch.setattr(feasible_module, "to_quantity", recording)
    verdict = feasibility(Decimal("4.99"), _ENTRY, _STOP, _record(), _usd(), _rule())

    assert calls == [
        (
            Amount(kind="money_at_risk", value=Decimal("4.99"), basis="gross_at_stop"),
            _ENTRY,
            _STOP,
        )
    ]
    assert verdict.word == BELOW_MIN_LOT
