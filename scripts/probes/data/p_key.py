"""P-KEY: bid and ask m1 land as two series with two cards, ticks as one series with both
sides, RSI(14) and RSI(21) of one component version as two series, and a different file for an
existing frozen key is refused unless marked a correction with a reason (W9; lane 3).

Run it where both packages are importable (the qmx-agents environment carries qmf-data too):

    cd qmx-agents
    uv run --no-sync python ../scripts/probes/data/p_key.py

PASS when every pair of those series has a different key and a different card, and the frozen
key refuses the different file silently not at all. FAIL when two share a key, or the file is
accepted without the mark.

Scratch goes under `D:/Temp/prb-dp/key` and is removed.
"""

from __future__ import annotations

import sys
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from qmf.core import is_ok, is_refusal
from qmf.data.series import SeriesKey, SeriesStore

from scripts.probes.data import common
from scripts.probes.data.common import Report

PROBE = "P-KEY"
JANUARY_2024 = 1_704_067_200_000
HOUR_MS = 3_600_000
NOW = datetime(2026, 10, 23, tzinfo=UTC)


def series_key(source: str, kind: str, variant: str = "") -> SeriesKey:
    built = SeriesKey.try_create(source, "EURUSD", kind, 2024, 1, variant)
    if not is_ok(built):
        raise SystemExit(f"the series key was refused: {built.context}")
    return built.value


def main() -> int:
    report = Report(PROBE)
    scratch = common.scratch_folder("key")
    try:
        store = SeriesStore(scratch / "series", wall=lambda: NOW)
        ticks = series_key("dukascopy", "ticks")
        bid = series_key("risk-lab", "bar-m1", "bid")
        ask = series_key("risk-lab", "bar-m1", "ask")
        rsi14 = series_key("derived", "rsi-v1", "14")
        rsi21 = series_key("derived", "rsi-v1", "21")
        texts = [entry.text for entry in (ticks, bid, ask, rsi14, rsi21)]
        report.numbers["keys"] = len(set(texts))
        if len(set(texts)) != len(texts):
            report.fail(f"two series share a key: {texts}")

        tick_rows = [
            (JANUARY_2024 + 9 * HOUR_MS + index * 1000, 108_000 + index, 108_012, 0.5, 0.25)
            for index in range(4)
        ]
        first = store.commit(ticks, tick_rows)
        if not is_ok(first):
            report.fail(f"the ticks month did not commit: {first.context}")
            return report.render()
        report.numbers["ticks_columns"] = ",".join(ticks.rule.columns)
        different = [(JANUARY_2024 + 10 * HOUR_MS, 108_100, 108_112, 0.5, 0.25)]
        refused = store.commit(ticks, different)
        if not is_refusal(refused):
            report.fail("a different file for the frozen ticks key was accepted")
        else:
            report.numbers["refusal"] = refused.context.get("reason", "")
        fixed = store.commit(ticks, different, correction="late fill for January")
        report.numbers["corrected"] = is_ok(fixed)
        if not is_ok(fixed):
            report.fail(f"the marked correction was refused: {fixed.context}")

        bar_rows = [(JANUARY_2024 + 60_000, 108_000, 108_010, 107_990, 108_005, 1.0)]
        for entry in (bid, ask):
            committed = store.commit(entry, bar_rows)
            if not is_ok(committed):
                report.fail(f"{entry.text} did not commit: {committed.context}")
        for entry, value in ((rsi14, 55.5), (rsi21, 61.5)):
            committed = store.commit(entry, [(JANUARY_2024 + 60_000, value)])
            if not is_ok(committed):
                report.fail(f"{entry.text} did not commit: {committed.context}")

        try:
            from qmx_engine.ledger import redact  # noqa: PLC0415
            from qmx_library.cards import Partition, SeriesCard, write_card  # noqa: PLC0415
            from qmx_library.principal import Principal  # noqa: PLC0415
            from qmx_library.store import Store  # noqa: PLC0415
        except ImportError as error:  # pragma: no cover - the environment, not the code
            report.fail(f"the card half needs the qmx-agents environment: {error}")
            return report.render()

        clock = _clock()
        with Store.open(scratch / "library", redactor=redact, wall=clock) as library:
            operator = Principal("operator")
            cards = []
            for entry in (ticks, bid, ask, rsi14, rsi21):
                card = SeriesCard(
                    entry.source, entry.subject, entry.kind, entry.variant, redownloadable=True
                )
                cards.append(
                    write_card(library, operator, card, (Partition(2024, 1, "a" * 64, 10, True),))
                )
            report.numbers["cards"] = len({card.object_id for card in cards})
            report.numbers["items"] = len({card.item for card in cards})
            if len({card.object_id for card in cards}) != 5:
                report.fail("two series cards are the same object")
            if cards[1].item == cards[2].item:
                report.fail("bid and ask share one card")
        return report.render()
    finally:
        common.drop_scratch()


def _clock() -> Callable[[], datetime]:
    state = {"now": NOW}

    def tick() -> datetime:
        state["now"] = state["now"] + timedelta(minutes=1)
        return state["now"]

    return tick


if __name__ == "__main__":
    sys.exit(main())
