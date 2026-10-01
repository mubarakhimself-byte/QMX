"""Reference usage — QML content authoring, QMB receipt minting (Story 38.1).

Executable::

    python qml/examples/generation_usage.py

Shows the things Story 38.1 pins down:

1. QMB optimize/sweep varies declared CT-33 parameters and cites the same bot
   ``fp1``. That act is search, not generation.
2. Generation authors new CT-33/CT-34 content and/or logic-source bytes via QML.
3. QML returns fingerprintable content; the QMB host composition root mints CT-06.
4. A generator module inside ``qmb/`` is refused. The ``.qml`` DSL and SQ
   RandomCondition-as-schema are refused. GAP-0085 nouns and GAP-0063 stay gaps.
"""

from __future__ import annotations

from typing import TypeVar

from qmf.core.chrono import CalendarIdentity
from qmf.core.exact import UnitKind
from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import Result, is_ok, is_refusal
from qml.footprint import ProducerBinding, mint_footprint
from qml.generation import (
    ACT_GENERATION,
    ACT_SEARCH,
    QMB_AUTHORS_CANDIDATES,
    QMB_RUNS_CANDIDATES,
    author_new_structure,
    classify_parameter_search,
    refuse_qml_dsl,
    refuse_random_condition_schema,
)

import qml

T = TypeVar("T")

_SOURCE = {
    "research_bot/__init__.py": "",
    "research_bot/bot.py": "def on_instant(self, instant):\n    return ()\n",
}


def _unwrap(result: Result[T], what: str) -> T:
    if is_ok(result):
        return result.value
    raise AssertionError(f"expected {what} to construct, got {result}")


def _pinned(tag: str) -> ProducerBinding:
    fp = _unwrap(fingerprint({"class": "example-producer", "tag": tag}), "producer fp")
    return _unwrap(ProducerBinding.try_create(fp), "binding")


def main() -> None:
    print(f"qml {qml.__version__}")
    bot_fp = _unwrap(fingerprint({"class": "bot", "id": "same"}), "bot fp")
    search = classify_parameter_search(bot_fp1=bot_fp, trial_bot_fp1s=(bot_fp, bot_fp))
    assert is_ok(search)
    assert search.value.value == ACT_SEARCH
    print(f"parameter variation is {ACT_SEARCH}, not {ACT_GENERATION}")

    calendar = _unwrap(CalendarIdentity.try_create("forex-17NY", "v3", "2025.2"), "calendar")
    footprint = _unwrap(
        mint_footprint(
            [
                {
                    "instrument_role": "primary",
                    "bar_specs": [{"kind": "time-interval", "seconds": 60}],
                    "stream_role": "trading",
                }
            ],
            [calendar],
            [_pinned("sma")],
        ),
        "footprint",
    )
    authored = _unwrap(
        author_new_structure(
            strategy_family_id="trend-follow",
            confluence_legs=[{"role": "level", "producer_binding": _pinned("zone")}],
            parameter_space=[
                {
                    "name": "lookback",
                    "type": "exact integer",
                    "bounds": {"min": 1, "max": 200},
                    "step": 1,
                    "default": 20,
                    "unit_kind": UnitKind.COUNT,
                    "ui": "ui-editable",
                }
            ],
            footprint=footprint,
            logic_source=_SOURCE,
        ),
        "author",
    )
    assert authored.act.value == ACT_GENERATION
    assert QMB_AUTHORS_CANDIDATES is False
    assert QMB_RUNS_CANDIDATES is True
    assert authored.bot is not None
    assert authored.confluence is not None
    print("qml returns fingerprintable generation content; the QMB host owns CT-06 receipts")

    assert is_refusal(refuse_qml_dsl(".qml"))
    assert is_refusal(refuse_random_condition_schema({"slots": []}))
    print("dsl and RandomCondition schema refused")
    print("generation ownership ok")


if __name__ == "__main__":
    main()
