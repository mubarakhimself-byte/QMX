"""Numbers: the measure vocabulary, instrument records, conversions and check layer C (AD-103).

``NumberSpec`` itself is part of the unit document and lives in :mod:`qml.unit.model`.
"""

from __future__ import annotations

from qml.numbers.check import KIND_MODES, NumbersCheck, check_numbers
from qml.numbers.convert import atr_multiple, distance, from_atr, instrument, lots, value_factor
from qml.numbers.measures import MEASURES, Form, MeasureRule
from qml.numbers.records import InstrumentClass, InstrumentRecord, Pip, parse_record

__all__ = [
    "KIND_MODES",
    "MEASURES",
    "Form",
    "InstrumentClass",
    "InstrumentRecord",
    "MeasureRule",
    "NumbersCheck",
    "Pip",
    "atr_multiple",
    "check_numbers",
    "distance",
    "from_atr",
    "instrument",
    "lots",
    "parse_record",
    "value_factor",
]
