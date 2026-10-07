"""Typed cTrader position protection decoding for checked CT-20 rows.

The caller must first prove that ``raw_position`` is one row from a checked
position-readback event. This adapter only crosses cTrader's declared execution
price boundary; it does not turn an arbitrary mapping into venue evidence.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import cast

from qmf.core import Fingerprint, Instrument, Ok, Price, Result, VenueId, is_refusal
from qmf.venue.ctrader import DecodedExecutionPrice, RoundingMode, decode_execution_price

from qmn.venue._refuse import invalid, policy

__all__ = ["NativeProtectionReadback", "decode_native_protection_readback"]


@dataclass(frozen=True, slots=True)
class NativeProtectionReadback:
    """One decoded native stop bound to its provider row and readback envelope."""

    position_id: str
    account_id: int
    symbol_id: int
    session_epoch: str
    instrument: Instrument
    stop_loss: Price
    raw_stop_loss: float
    price_digits: int
    rounding: RoundingMode
    source_event_fp1: Fingerprint


def decode_native_protection_readback(
    raw_position: object,
    *,
    expected_position_id: object,
    expected_account_id: object,
    response_account_id: object,
    expected_session_epoch: object,
    response_session_epoch: object,
    expected_symbol_id: object,
    instrument: object,
    price_digits: object,
    rounding: object,
    source_event_fp1: object,
) -> Result[NativeProtectionReadback]:
    """Decode cTrader ``ProtoOAPosition.stopLoss`` using pinned CT-03 scale facts.

    ``price_digits`` and ``rounding`` must come from the operator-pinned full
    symbol metadata and declared execution-price conversion policy. No market
    data scale or fill price is used as a fallback.
    """
    if not isinstance(raw_position, Mapping):
        return invalid("position", "CT-20 position row is a mapping")
    row = cast("Mapping[str, object]", raw_position)
    if (
        type(expected_position_id) is not str
        or not expected_position_id.strip()
        or type(expected_account_id) is not int
        or expected_account_id < 1
        or type(response_account_id) is not int
        or response_account_id < 1
        or type(expected_session_epoch) is not str
        or not expected_session_epoch.strip()
        or type(response_session_epoch) is not str
        or not response_session_epoch.strip()
        or type(expected_symbol_id) is not int
        or expected_symbol_id < 1
    ):
        return invalid("native_identity", "position id, account id and symbol id are typed")
    if (
        _position_id(row.get("positionId")) != expected_position_id
        or response_account_id != expected_account_id
        or response_session_epoch != expected_session_epoch
    ):
        return policy(
            "native_identity", "position readback envelope matches the exact account/session/PID"
        )
    trade_data = row.get("tradeData")
    if not isinstance(trade_data, Mapping):
        return policy("native_identity", "ProtoOAPosition tradeData matches the native symbol")
    typed_trade_data = cast("Mapping[str, object]", trade_data)
    if (
        type(typed_trade_data.get("symbolId")) is not int
        or typed_trade_data.get("symbolId") != expected_symbol_id
    ):
        return policy("native_identity", "ProtoOAPosition tradeData matches the native symbol")
    if type(instrument) is not Instrument:
        return invalid("instrument", "stop readback uses the pinned typed CT-03 instrument")
    if type(instrument.venue) is not VenueId:
        return invalid("instrument", "CT-03 instrument contains a typed venue identity")
    venue = VenueId.try_create(instrument.venue.value)
    if is_refusal(venue):
        return venue
    rebuilt_instrument = Instrument.try_create(venue.value, instrument.symbol)
    if is_refusal(rebuilt_instrument):
        return rebuilt_instrument
    if rebuilt_instrument.value != instrument:
        return policy("instrument", "CT-03 instrument fields match their reconstructed identity")
    instrument = rebuilt_instrument.value
    if type(source_event_fp1) is not Fingerprint:
        return invalid("source_event_fp1", "stop readback cites the checked CT-13 source event")
    parsed_source_fp1 = Fingerprint.try_create(source_event_fp1.value)
    if is_refusal(parsed_source_fp1):
        return parsed_source_fp1
    stop_raw = row.get("stopLoss")
    if stop_raw is None:
        return policy("stopLoss", "native position readback confirms an active stop loss")
    decoded = decode_execution_price(stop_raw, instrument, price_digits, rounding)
    if is_refusal(decoded):
        return decoded
    price: DecodedExecutionPrice = decoded.value
    return Ok(
        NativeProtectionReadback(
            position_id=expected_position_id,
            account_id=expected_account_id,
            symbol_id=expected_symbol_id,
            session_epoch=expected_session_epoch,
            instrument=instrument,
            stop_loss=price.price,
            raw_stop_loss=price.raw_double,
            price_digits=price.digits,
            rounding=price.rounding,
            source_event_fp1=parsed_source_fp1.value,
        )
    )


def _position_id(value: object) -> str | None:
    if type(value) is str and value.strip():
        return value
    if type(value) is int and value > 0:
        return str(value)
    return None
