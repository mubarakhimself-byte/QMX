"""C-37: an amend writes ``stopLoss`` and ``takeProfit`` as the absolute double cTrader expects.

Encoded against the pinned Spotware definitions (release 91), which declare both fields as
doubles, and decoded back with the same definitions.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import TypeVar

import pytest
from qmf.core import (
    Account,
    AccountRole,
    Instrument,
    Price,
    PriceDelta,
    RefusalCategory,
    Result,
    Retryability,
    TypedRefusal,
    VenueId,
    is_ok,
)
from qmf.venue import (
    CapabilityDeclaration,
    CapabilityField,
    CapabilityFieldName,
    Command,
    ErrorMap,
    ErrorMapRow,
    ProtectionAmendment,
    ProtectionSide,
    ProtoArtifact,
    SubmissionOutcomeClass,
    compile_descriptor_set,
    encode_amend_protection,
    encode_command,
)
from qmf.venue.encode import EncodedCommand
from qmf.venue.proto import SPOTWARE_PROTO_PACKAGE, CompiledProto

T = TypeVar("T")

_RELEASE_91 = (
    Path(__file__).resolve().parents[3]
    / "qmx-agents/packages/qmx-broker/src/qmx_broker/protocol/openapi-91.pb"
)


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _venue() -> VenueId:
    return _ok(VenueId.try_create("venue-ctrader-demo"))


def _account() -> Account:
    return _ok(Account.try_create("acct-001", _venue(), AccountRole.DEMO))


def _declaration() -> CapabilityDeclaration:
    """A declaration that admits ``amend_protection``; every other field waits on measurement."""
    modes = CapabilityFieldName.ACKNOWLEDGEMENT_MODES
    fields = [_ok(CapabilityField.static(modes, {"amend_protection": "explicit-event"}))] + [
        _ok(CapabilityField.measured(name)) for name in CapabilityFieldName if name is not modes
    ]
    artifact = _ok(ProtoArtifact.try_create("openapi-proto-messages", 91, "sha256:" + "a" * 64))
    row = _ok(
        ErrorMapRow.try_create(
            "ORDER_REJECTED",
            "amend_protection",
            RefusalCategory.POLICY_REJECTION,
            Retryability.NO,
            SubmissionOutcomeClass.REJECTED_BY_VENUE,
        )
    )
    error_map = _ok(ErrorMap.try_create(1, [row]))
    return _ok(
        CapabilityDeclaration.try_create("ctrader-adapter-1.0.0", artifact, error_map, fields)
    )


def _release_91() -> CompiledProto:
    return _ok(
        compile_descriptor_set(
            _RELEASE_91.read_bytes(), package_name=SPOTWARE_PROTO_PACKAGE, release_tag=91
        )
    )


def _inner(compiled: CompiledProto, encoded: EncodedCommand) -> object:
    envelope = _ok(compiled.decode("ProtoMessage", encoded.envelope))
    assert envelope.payload == encoded.payload  # type: ignore[attr-defined]
    return _ok(compiled.decode(encoded.message_name, encoded.payload))


def _exact(text: str) -> tuple[int, int]:
    """``"1.08445"`` as ``(108445, 5)``: the units and the scale the text is written at."""
    scale = len(text.partition(".")[2])
    return int(text.replace(".", "")), scale


def _amend(side: ProtectionSide, symbol: str, reference: str, distance: str) -> Command:
    instrument = _ok(Instrument.try_create(_venue(), symbol))
    (price_units, price_scale), (gap_units, gap_scale) = _exact(reference), _exact(distance)
    price = _ok(Price.try_create(price_units, instrument, price_scale))
    delta = _ok(PriceDelta.try_create(gap_units, instrument, gap_scale))
    original = delta if side is ProtectionSide.STOP else None
    amendment = _ok(
        ProtectionAmendment.try_create(side, delta, price, original_risk_distance=original)
    )
    return _ok(Command.amend_protection(_venue(), _account(), "session-c37", 7, amendment, "9001"))


def _wire(command: Command, trade_side: str, digits: int) -> object:
    compiled = _release_91()
    encoded = _ok(
        encode_amend_protection(
            command,
            compiled=compiled,
            declaration=_declaration(),
            ctid_trader_account_id=4401,
            trade_side=trade_side,
            digits=digits,
        )
    )
    return _inner(compiled, encoded)


def test_a_stop_and_a_target_decode_back_as_exactly_the_absolute_price() -> None:
    eurusd_stop = _wire(_amend(ProtectionSide.STOP, "EURUSD", "1.08445", "0.00100"), "buy", 5)
    eurusd_target = _wire(_amend(ProtectionSide.TARGET, "EURUSD", "1.08245", "0.00100"), "buy", 5)
    gold_stop = _wire(_amend(ProtectionSide.STOP, "XAUUSD", "2640.25", "10.00"), "sell", 2)

    assert (eurusd_stop.positionId, eurusd_stop.stopLoss) == (9001, 1.08345)  # type: ignore[attr-defined]
    assert eurusd_stop.HasField("takeProfit") is False  # type: ignore[attr-defined]
    assert eurusd_target.takeProfit == 1.08345  # type: ignore[attr-defined]
    assert eurusd_target.HasField("stopLoss") is False  # type: ignore[attr-defined]
    assert gold_stop.stopLoss == 2650.25  # type: ignore[attr-defined]
    assert Decimal(repr(eurusd_stop.stopLoss)) == Decimal("1.08345")  # type: ignore[attr-defined]
    assert Decimal(repr(gold_stop.stopLoss)) == Decimal("2650.25")  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("side", "trade_side", "expected"),
    [
        (ProtectionSide.STOP, "buy", 1.08346),
        (ProtectionSide.STOP, "sell", 1.08345),
        (ProtectionSide.TARGET, "buy", 1.08345),
        (ProtectionSide.TARGET, "sell", 1.08346),
    ],
)
def test_a_level_off_the_symbol_digits_rounds_toward_the_position(
    side: ProtectionSide, trade_side: str, expected: float
) -> None:
    loss_side = (side is ProtectionSide.STOP) == (trade_side == "buy")
    reference = "1.084455" if loss_side else "1.082455"
    inner = _wire(_amend(side, "EURUSD", reference, "0.001000"), trade_side, 5)

    field = "stopLoss" if side is ProtectionSide.STOP else "takeProfit"
    assert getattr(inner, field) == expected


def test_the_dispatcher_carries_the_position_side_and_digits_to_the_amend() -> None:
    compiled = _release_91()
    encoded = _ok(
        encode_command(
            _amend(ProtectionSide.STOP, "XAUUSD", "2660.25", "10.00"),
            compiled=compiled,
            declaration=_declaration(),
            ctid_trader_account_id=4401,
            trade_side="buy",
            digits=2,
        )
    )

    assert _inner(compiled, encoded).stopLoss == 2650.25  # type: ignore[attr-defined]


@pytest.mark.parametrize(
    ("trade_side", "digits", "field"),
    [
        (None, 5, "trade_side"),
        ("hold", 5, "trade_side"),
        ("buy", None, "digits"),
        ("buy", -1, "digits"),
    ],
)
def test_an_absolute_level_without_the_position_side_or_the_digits_is_refused(
    trade_side: object, digits: object, field: str
) -> None:
    refused = encode_amend_protection(
        _amend(ProtectionSide.STOP, "EURUSD", "1.08445", "0.00100"),
        compiled=_release_91(),
        declaration=_declaration(),
        ctid_trader_account_id=4401,
        trade_side=trade_side,
        digits=digits,
    )

    assert isinstance(refused, TypedRefusal)
    assert (refused.category, refused.context["field"]) == (RefusalCategory.INVALID_INPUT, field)


def test_a_level_a_double_cannot_hold_at_the_symbol_digits_is_refused() -> None:
    refused = encode_amend_protection(
        _amend(ProtectionSide.STOP, "EURUSD", "100000000000.00099", "0.00100"),
        compiled=_release_91(),
        declaration=_declaration(),
        ctid_trader_account_id=4401,
        trade_side="buy",
        digits=5,
    )

    assert isinstance(refused, TypedRefusal)
    assert refused.context == {
        "field": "stopLoss",
        "reason": "the price does not survive as a double at the symbol's digits",
        "level": "99999999999.99999",
        "given": "99999999999.99998",
    }
