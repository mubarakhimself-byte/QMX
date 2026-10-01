"""cTrader stop fields cross the execution-price boundary with native identity pins."""

from __future__ import annotations

from typing import TypeVar

from qmf.core import Instrument, Result, VenueId, fingerprint, is_ok, is_refusal
from qmf.venue.ctrader import RoundingMode
from qmn.venue.protection_readback import decode_native_protection_readback

T = TypeVar("T")


def _ok(result: Result[T]) -> T:
    assert is_ok(result), result
    return result.value


def _instrument() -> Instrument:
    return _ok(Instrument.try_create(_ok(VenueId.try_create("venue-a")), "EURUSD"))


def _unchecked_instrument(venue: object, symbol: object) -> Instrument:
    instrument = object.__new__(Instrument)
    object.__setattr__(instrument, "venue", venue)
    object.__setattr__(instrument, "symbol", symbol)
    return instrument


def _unchecked_venue(value: object) -> VenueId:
    venue = object.__new__(VenueId)
    object.__setattr__(venue, "value", value)
    return venue


def test_position_stop_loss_uses_explicit_digits_and_rounding() -> None:
    decoded = _ok(
        decode_native_protection_readback(
            {
                "positionId": 44,
                "tradeData": {"symbolId": 7},
                "stopLoss": 1.08523,
                "unrelated": "preserved-in-row-identity",
            },
            expected_position_id="44",
            expected_account_id=42,
            response_account_id=42,
            expected_session_epoch="session-a",
            response_session_epoch="session-a",
            expected_symbol_id=7,
            instrument=_instrument(),
            price_digits=5,
            rounding=RoundingMode.HALF_EVEN,
            source_event_fp1=_ok(fingerprint({"checked-source": "position-readback"})),
        )
    )
    assert decoded.position_id == "44"
    assert decoded.account_id == 42
    assert decoded.symbol_id == 7
    assert decoded.session_epoch == "session-a"
    assert decoded.stop_loss.value == 108_523
    assert decoded.stop_loss.scale == 5
    assert decoded.stop_loss.instrument == _instrument()
    assert decoded.raw_stop_loss == 1.08523


def test_position_stop_loss_refuses_missing_mismatched_and_unscaled_rows() -> None:
    base = {"positionId": 44, "tradeData": {"symbolId": 7}, "stopLoss": 1.08523}
    kwargs = {
        "expected_position_id": "44",
        "expected_account_id": 42,
        "response_account_id": 42,
        "expected_session_epoch": "session-a",
        "response_session_epoch": "session-a",
        "expected_symbol_id": 7,
        "instrument": _instrument(),
        "price_digits": 5,
        "rounding": RoundingMode.HALF_EVEN,
        "source_event_fp1": _ok(fingerprint({"checked-source": "position-readback"})),
    }
    cases = (
        ({k: v for k, v in base.items() if k != "stopLoss"}, kwargs),
        (dict(base, tradeData={"symbolId": 9}), kwargs),
        (dict(base, stopLoss=108_523), kwargs),
        (dict(base, stopLoss=True), kwargs),
        (base, {**kwargs, "price_digits": None}),
        (base, {**kwargs, "rounding": None}),
        (base, {**kwargs, "response_account_id": 99}),
        (base, {**kwargs, "response_session_epoch": "session-b"}),
    )
    for raw, pins in cases:
        assert is_refusal(decode_native_protection_readback(raw, **pins))


def test_position_stop_loss_revalidates_nominal_instrument_and_nested_venue() -> None:
    base = {"positionId": 44, "tradeData": {"symbolId": 7}, "stopLoss": 1.08523}
    kwargs = {
        "expected_position_id": "44",
        "expected_account_id": 42,
        "response_account_id": 42,
        "expected_session_epoch": "session-a",
        "response_session_epoch": "session-a",
        "expected_symbol_id": 7,
        "price_digits": 5,
        "rounding": RoundingMode.HALF_EVEN,
        "source_event_fp1": _ok(fingerprint({"checked-source": "position-readback"})),
    }
    for instrument in (
        _unchecked_instrument(None, "EURUSD"),
        _unchecked_instrument(_instrument().venue, {}),
        _unchecked_instrument(_unchecked_instrument(None, None), "EURUSD"),
        _unchecked_instrument(_unchecked_venue(None), "EURUSD"),
    ):
        assert is_refusal(
            decode_native_protection_readback(base, **kwargs, instrument=instrument)
        )
    # Revalidation preserves canonical official identities and execution scaling.
    valid = _ok(
        decode_native_protection_readback(
            base, **kwargs, instrument=_instrument()
        )
    )
    assert valid.instrument == _instrument()
    assert valid.stop_loss.value == 108_523
