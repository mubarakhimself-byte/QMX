"""The verdict a unit's card shows, computed by the check's door through QML's one converter.

`unit_check` holds the document and its markets' records but no share, entry, stop or rate, so a
document alone answers no verdict and the check claims none. A caller that holds those numbers
passes them as `AtCard`, and the result carries `feasibility` beside its problems, computed by
QML's `feasibility` on the same record `gather` reads. Nothing here re-derives the fit.
"""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import Any, cast

import pytest
from qmf.core.chrono import Instant
from qmf.core.refusal import is_refusal
from qml.blocks.api import Amount
from qml.numbers import feasible as feasible_module
from qml.numbers.feasible import BELOW_MIN_LOT, FITS

import qmx_tools.unit_check as check_door
from qmx_tools.gather import template
from qmx_tools.unit_check import AtCard, checked, feasibility_of

OPEN = Instant(1_000_000_000_000_000_000)
ENTRY = Decimal("1.10000")
STOP = Decimal("1.09500")


def _at(share: str) -> AtCard:
    """The card's numbers on the dummy's EURUSD market, the account in its quote currency."""
    return AtCard(market="fx.eurusd", share=Decimal(share), entry=ENTRY, stop=STOP, now=OPEN)


def test_the_card_says_one_lot_fits_or_what_it_lacks() -> None:
    """5.00 USD at a 0.0050 stop buys the 0.01 minimum lot; 4.99 is 0.01 short."""
    document = template()

    fits = feasibility_of(None, document, _at("5.00"))
    short = feasibility_of(None, document, _at("4.99"))

    assert (fits["verdict"], fits["quantity"], fits["shortfall"]) == (FITS, "0.01", "0")
    assert (short["verdict"], short["quantity"], short["shortfall"]) == (
        BELOW_MIN_LOT,
        None,
        "0.01",
    )
    assert (fits["market"], short["market"]) == ("fx.eurusd", "fx.eurusd")


def test_a_market_the_document_does_not_name_answers_its_own_word() -> None:
    """A market with no record is named, never guessed at from another market's numbers."""
    verdict = feasibility_of(
        None, template(), AtCard(market="fx.gbpusd", share=Decimal("5.00"), entry=ENTRY, stop=STOP)
    )

    assert verdict["verdict"] == "no_record"
    assert verdict["market"] == "fx.gbpusd"


def test_the_check_carries_the_verdict_only_when_the_card_asks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The result gains `feasibility` with the numbers and stays as it was without them."""
    document = template()
    plain = checked(None, document)
    assert "feasibility" not in plain

    calls: list[tuple[Amount, Decimal, Decimal | None]] = []
    real: Callable[..., Any] = feasible_module.to_quantity

    def recording(amount: Amount, entry: Decimal, stop: Decimal | None, *rest: object) -> object:
        calls.append((amount, entry, stop))
        return real(amount, entry, stop, *rest)

    monkeypatch.setattr(feasible_module, "to_quantity", recording)
    asked = checked(None, document, at=_at("4.99"))
    asked["notes"] = plain["notes"]

    assert cast("dict[str, Any]", asked["feasibility"])["verdict"] == BELOW_MIN_LOT
    assert asked == {**plain, "feasibility": asked["feasibility"]}
    assert calls == [
        (
            Amount(kind="money_at_risk", value=Decimal("4.99"), basis="gross_at_stop"),
            ENTRY,
            STOP,
        )
    ], "the card's verdict is QML's converter, recorded once with the share"


def test_offline_checked_keeps_the_verdict_beside_its_notes() -> None:
    """The step with no Library carries the same answer, notes and all."""
    result = check_door.offline_checked(template(), at=_at("5.00"))

    assert result["verdict"] == "pass"
    assert cast("dict[str, Any]", result["feasibility"])["verdict"] == FITS
    assert not is_refusal(result)
