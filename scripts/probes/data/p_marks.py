"""P-MARKS: a result that read 2019 stays unmarked after a month freezes, after an open-month
update and after a correction to March 2024; a result that read March 2024 shows "corrected";
a result that read an open-month range shows "corrected" only when a recorded open-month
correction overlaps that range (W9; lane 3).

    cd qmx-agents
    uv run --no-sync python ../scripts/probes/data/p_marks.py

FAIL when a data append marks a result "superseded", or a correction marks a result that did
not read the corrected rows. Scratch goes under `D:/Temp/prb-dp/marks` and is removed.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from qmx_engine.ledger import redact
from qmx_library.cards import (
    Correction,
    Partition,
    SeriesCard,
    read_range,
    write_card,
)
from qmx_library.port import Draft, Relation
from qmx_library.principal import Principal
from qmx_library.store import Store

from scripts.probes.data import common
from scripts.probes.data.common import Report

PROBE = "P-MARKS"
NOW = datetime(2026, 10, 23, tzinfo=UTC)
MARCH_2024 = (1_709_251_200_000_000_000, 1_711_929_600_000_000_000)
APRIL_2024 = (1_711_929_600_000_000_000, 1_714_608_000_000_000_000)
MAY_2024 = (1_714_608_000_000_000_000, 1_717_286_400_000_000_000)
YEAR_2019 = (1_546_300_800_000_000_000, 1_577_836_800_000_000_000)
OPERATOR = Principal("operator")


class Clock:
    def __init__(self) -> None:
        self.now = NOW

    def __call__(self) -> datetime:
        self.now = self.now + timedelta(minutes=1)
        return self.now


def put_result(library: Store, item: str, card_id: str, series: str, span: tuple[int, int]) -> str:
    fields = {"outcome": "inconclusive", "reads": [read_range(series, *span)]}
    relations: list[Relation] = [("consumed", card_id)]
    draft = Draft("backtest-result", item, item, fields=fields, relations=relations)
    found = library.head(item, "main")
    expected = None if found is None else found[0]
    return library.put(OPERATOR, draft, on="main", expected_head=expected).object_id


def marks(library: Store, readers: dict[str, str]) -> dict[str, str]:
    return {
        name: str(library.marks(OPERATOR, object_id).worst or "none")
        for name, object_id in readers.items()
    }


def main() -> int:
    report = Report(PROBE)
    scratch = common.scratch_folder("marks")
    try:
        card = SeriesCard(
            "dukascopy", "EURUSD", "ticks", licence="internal-only", redownloadable=True
        )
        january = Partition(2024, 1, "a" * 64, 100, True)
        with Store.open(scratch / "library", redactor=redact, wall=Clock()) as library:
            first = write_card(library, OPERATOR, card, (january,))
            readers = {
                "2019": put_result(library, "res-2019", first.object_id, card.series, YEAR_2019),
                "march": put_result(library, "res-march", first.object_id, card.series, MARCH_2024),
                "april": put_result(library, "res-april", first.object_id, card.series, APRIL_2024),
                "may": put_result(library, "res-may", first.object_id, card.series, MAY_2024),
            }
            if any(value != "none" for value in marks(library, readers).values()):
                report.fail("a fresh reader is already marked")

            march_open = Partition(2024, 3, "b" * 64, 20, False)
            write_card(library, OPERATOR, card, (january, march_open))
            report.numbers["after_freeze"] = marks(library, readers)
            if any(value != "none" for value in marks(library, readers).values()):
                report.fail("a month freezing marked a result")

            march_frozen = Partition(2024, 3, "c" * 64, 21, True)
            april_open = Partition(2024, 4, "d" * 64, 30, False)
            write_card(library, OPERATOR, card, (january, march_frozen, april_open))
            report.numbers["after_open_update"] = marks(library, readers)
            if any(value != "none" for value in marks(library, readers).values()):
                report.fail("an open-month update marked a result")

            march_fixed = Partition(2024, 3, "e" * 64, 22, True)
            march_correction = Correction(
                *MARCH_2024, "c" * 64, "e" * 64, "late tick for March", NOW.isoformat()
            )
            write_card(
                library,
                OPERATOR,
                card,
                (january, march_fixed, april_open),
                (march_correction,),
            )
            marked = marks(library, readers)
            report.numbers["after_march_correction"] = marked
            if marked["march"] != "corrected":
                report.fail("a March 2024 correction did not mark the result that read March 2024")
            for name in ("2019", "april", "may"):
                if marked[name] != "none":
                    report.fail(f"a March 2024 correction marked {name}, which did not read it")

            april_fixed = Partition(2024, 4, "f" * 64, 31, True)
            write_card(
                library,
                OPERATOR,
                card,
                (january, march_fixed, april_fixed),
                (
                    march_correction,
                    Correction(
                        *APRIL_2024, "d" * 64, "f" * 64, "open month re-fetched", NOW.isoformat()
                    ),
                ),
            )
            marked = marks(library, readers)
            report.numbers["after_april_correction"] = marked
            if marked["april"] != "corrected":
                report.fail(
                    "the open-month correction did not mark the result that read April 2024"
                )
            if marked["may"] != "none":
                report.fail("the open-month correction marked a result that read another range")
        return report.render()
    finally:
        common.drop_scratch()


if __name__ == "__main__":
    sys.exit(main())
