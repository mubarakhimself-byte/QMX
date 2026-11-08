"""The instrument record facts QML reads (CONTRACTS.md 2.3; Part C RECORDS.md section 2).

Part C owns the record and its key list. QML parses the keys it reads into exact values and
keeps ``data_levels``, ``leverage`` and ``margin`` verbatim for the layers that read them.
Keys QML does not read are ignored, so a full Part C record parses unchanged.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Final, cast

from qmf.core.refusal import Ok, Result

from qml._refuse import invalid
from qml.unit.schema import DECIMAL_PATTERN

__all__ = ["InstrumentClass", "InstrumentRecord", "Pip", "parse_record", "places"]


class InstrumentClass(StrEnum):
    """The one class enum every part spells the same way (R1-C-10)."""

    FX = "fx"
    METAL = "metal"
    INDEX_CFD = "index_cfd"
    COMMODITY_CFD = "commodity_cfd"
    STOCK_CFD = "stock_cfd"
    FUTURE = "future"
    PERP = "perp"
    SPOT_CRYPTO = "spot_crypto"
    STOCK = "stock"


@dataclass(frozen=True)
class Pip:
    size: Decimal
    source: str


@dataclass(frozen=True)
class InstrumentRecord:
    market_id: str
    venue: str
    symbol: str
    instrument_class: InstrumentClass
    currency: str
    digits: int
    tick_size: Decimal
    contract_size: Decimal
    value_per_point: Decimal
    lot_step: Decimal
    min_lot: Decimal
    calendar_ref: str
    zone: str
    day_boundary: str
    data_levels: Mapping[str, object]
    leverage: Mapping[str, object]
    margin: Mapping[str, object]
    record_version: int
    pip: Pip | None = None
    max_lot: Decimal | None = None
    expiry: str | None = None
    last_trade: str | None = None
    root: str | None = None
    rolls_to: str | None = None
    funding_interval: str | None = None

    @property
    def name(self) -> str:
        """How a problem names this record: venue, symbol and version."""
        return f"{self.venue}:{self.symbol}@{self.record_version}"


def places(number: Decimal) -> int:
    """The count of decimal places ``number`` is written with."""
    exponent = number.as_tuple().exponent
    return -exponent if isinstance(exponent, int) and exponent < 0 else 0


_Reader = Callable[[object], object | None]


def _text(value: object) -> object | None:
    return value if isinstance(value, str) and value.strip() else None


def _positive_decimal(value: object) -> object | None:
    if isinstance(value, str) and re.fullmatch(DECIMAL_PATTERN, value):
        number = Decimal(value)
        return number if number > 0 else None
    return None


def _whole(value: object) -> object | None:
    return value if type(value) is int and value >= 0 else None


def _object(value: object) -> object | None:
    return cast(Mapping[str, object], value) if isinstance(value, dict) else None


def _class(value: object) -> object | None:
    allowed = {member.value for member in InstrumentClass}
    return InstrumentClass(value) if isinstance(value, str) and value in allowed else None


def _pip(value: object) -> object | None:
    if not isinstance(value, dict):
        return None
    given = cast(dict[str, object], value)
    size = _positive_decimal(given.get("size"))
    source = _text(given.get("source"))
    if set(given) != {"size", "source"} or not isinstance(size, Decimal) or source is None:
        return None
    return Pip(size, str(source))


_WANTS: Final[Mapping[_Reader, str]] = {
    _text: "a non-empty string",
    _positive_decimal: 'a positive decimal string such as "0.01"',
    _whole: "a whole number of zero or more",
    _object: "an object",
    _class: f"one of {', '.join(member.value for member in InstrumentClass)}",
    _pip: '{"size": a positive decimal string, "source": where the pip is stated}',
}

# (record key, model field, reader, required)
_KEYS: Final[tuple[tuple[str, str, _Reader, bool], ...]] = (
    ("market_id", "market_id", _text, True),
    ("venue", "venue", _text, True),
    ("symbol", "symbol", _text, True),
    ("class", "instrument_class", _class, True),
    ("currency", "currency", _text, True),
    ("digits", "digits", _whole, True),
    ("tick_size", "tick_size", _positive_decimal, True),
    ("contract_size", "contract_size", _positive_decimal, True),
    ("value_per_point", "value_per_point", _positive_decimal, True),
    ("lot_step", "lot_step", _positive_decimal, True),
    ("min_lot", "min_lot", _positive_decimal, True),
    ("calendar_ref", "calendar_ref", _text, True),
    ("zone", "zone", _text, True),
    ("day_boundary", "day_boundary", _text, True),
    ("data_levels", "data_levels", _object, True),
    ("leverage", "leverage", _object, True),
    ("margin", "margin", _object, True),
    ("record_version", "record_version", _whole, True),
    ("pip", "pip", _pip, False),
    ("max_lot", "max_lot", _positive_decimal, False),
    ("expiry", "expiry", _text, False),
    ("last_trade", "last_trade", _text, False),
    ("root", "root", _text, False),
    ("rolls_to", "rolls_to", _text, False),
    ("funding_interval", "funding_interval", _text, False),
)


def parse_record(document: object) -> Result[InstrumentRecord]:
    """Read one decoded instrument record; a refusal lists every bad or missing key at once."""
    if not isinstance(document, dict):
        return invalid("record", "an instrument record is a JSON object")
    given = cast(dict[str, object], document)
    built: dict[str, object] = {}
    problems: list[str] = []
    for key, name, reader, required in _KEYS:
        if key not in given:
            if required:
                problems.append(f"/{key}: the required key is missing")
            continue
        value = reader(given[key])
        if value is None:
            problems.append(f"/{key}: expected {_WANTS[reader]}")
        else:
            built[name] = value
    tick = built.get("tick_size")
    digits = built.get("digits")
    if isinstance(tick, Decimal) and isinstance(digits, int) and places(tick) > digits:
        problems.append(f"/tick_size: {tick} is finer than the record's {digits} digits")
    if problems:
        symbol = given.get("symbol")
        return invalid(
            "record",
            problems[0],
            record=f"{given.get('venue')}:{symbol}" if symbol else "unnamed",
            problems=problems,
        )
    model: type = InstrumentRecord
    return Ok(cast(InstrumentRecord, model(**built)))
