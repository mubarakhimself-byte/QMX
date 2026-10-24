"""P-FREEZE: (a) a ticks month with one hour forced empty stays open after its first fetch,
freezes with the gap when the re-fetch returns the same gap, and no click is needed; (b) a
fills month freezes at month end plus its settlement delay with no gap check, a fill after the
freeze lands as a correction naming both fingerprints, and a calendar revision in an open month
is an append; (c) the open file of a non-redownloadable series is in the scratch bucket under
its fixed name after each commit batch and the next batch overwrites it; (d) a re-opened month
is re-fetched (W9; lane 4).

    cd qmx-agents
    uv run --no-sync python ../scripts/probes/data/p_freeze.py

FAIL when a month waits for a click, a late row is refused, a fill month waits on a gap check,
or the open file is missing from the bucket. Scratch goes under `D:/Temp/prb-dp/freeze`.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from qmf.core import is_ok, is_refusal
from qmf.data.series import OPEN_NAME, SeriesKey, SeriesStore

from scripts.probes.data import common
from scripts.probes.data.common import Report

PROBE = "P-FREEZE"
JANUARY_2024 = 1_704_067_200_000
MARCH_2024 = 1_709_251_200_000
OCTOBER_2026 = 1_790_294_400_000
HOUR_MS = 3_600_000
DAY_MS = 86_400_000
NOW = datetime(2026, 10, 23, tzinfo=UTC)
FIXED_NAME = "dukascopy/EURUSD/ticks/-/2026-10"


def key(source: str, kind: str, year: int, month: int, variant: str = "") -> SeriesKey:
    built = SeriesKey.try_create(source, "EURUSD", kind, year, month, variant)
    if not is_ok(built):
        raise SystemExit(f"the series key was refused: {built.context}")
    return built.value


class Clock:
    def __init__(self) -> None:
        self.now = NOW

    def __call__(self) -> datetime:
        self.now = self.now + timedelta(minutes=1)
        return self.now


def case_a(store: SeriesStore, report: Report) -> SeriesKey:
    gapped = key("dukascopy", "ticks", 2024, 2)
    rows = [
        (JANUARY_2024 + 30 * DAY_MS + 9 * HOUR_MS, 1, 2, 0.1, 0.1),
        (JANUARY_2024 + 30 * DAY_MS + 11 * HOUR_MS, 3, 4, 0.1, 0.1),
    ]
    first = store.commit(gapped, rows)
    if not is_ok(first) or first.value.frozen or not first.value.gaps:
        report.fail(f"case a: the first fetch did not stay open with its gap: {first}")
        return gapped
    report.numbers["a_gap"] = first.value.gaps[0]
    again = store.commit(gapped, rows)
    if not is_ok(again) or not again.value.frozen:
        report.fail("case a: the re-fetch that returned the same gap did not freeze the month")
        return gapped
    report.numbers["a_frozen"] = again.value.frozen
    report.numbers["a_attempts"] = again.value.attempts
    return gapped


def case_b(store: SeriesStore, report: Report) -> None:
    fills = key("risk-lab", "fill", 2024, 3)
    first = store.commit(fills, [(MARCH_2024 + 60_000, 108_000, 108_010, 107_990, 108_005, None)])
    if not is_ok(first) or not first.value.frozen:
        report.fail("case b: the fills month did not freeze at month end plus its delay")
        return
    report.numbers["b_frozen"] = first.value.frozen
    report.numbers["b_settlement_days"] = fills.rule.settlement_days
    old = store.state(fills)
    late = [(MARCH_2024 + 120_000, 108_010, 108_020, 108_000, 108_015, 3.0)]
    refused = store.commit(fills, late)
    report.numbers["b_unmarked_refused"] = is_refusal(refused)
    if not is_refusal(refused):
        report.fail("case b: a late fill was accepted without a correction mark")
    fixed = store.commit(fills, late, correction="broker fill arrived after settlement")
    after = store.state(fills)
    if not is_ok(fixed) or after is None or not after.corrections:
        report.fail(f"case b: the late fill did not land as a correction: {fixed}")
        return
    record = after.corrections[-1]
    report.numbers["b_correction"] = f"{record.old[:12]}->{record.new[:12]}"
    report.numbers["b_old_matches"] = old is not None and record.old == old.fingerprint

    open_fill = key("risk-lab", "fill", 2026, 10)
    before = store.commit(
        open_fill, [(OCTOBER_2026 + 60_000, 108_000, 108_010, 107_990, 108_005, 1.0)]
    )
    appended = store.commit(
        open_fill,
        [
            (OCTOBER_2026 + 60_000, 108_000, 108_010, 107_990, 108_005, 1.0),
            (OCTOBER_2026 + 120_000, 108_005, 108_015, 107_995, 108_010, 2.0),
        ],
    )
    if not is_ok(before) or not is_ok(appended) or appended.value.frozen:
        report.fail("case b: a calendar revision in an open month was not an append")
        return
    report.numbers["b_append"] = appended.value.fingerprint != before.value.fingerprint
    open_state = store.state(open_fill)
    report.numbers["b_append_corrections"] = (
        0 if open_state is None else len(open_state.corrections)
    )


def case_c(store: SeriesStore, report: Report) -> None:
    try:
        from qmx_engine.ledger import redact  # noqa: PLC0415
        from qmx_hub.bucket import Bucket  # noqa: PLC0415
        from qmx_library.store import Store  # noqa: PLC0415
    except ImportError as error:  # pragma: no cover - the environment, not the code
        report.fail(f"case c needs the qmx-agents environment: {error}")
        return
    bars = key("risk-lab", "bar-m1", 2026, 10, "bid")
    committed = store.commit(
        bars, [(OCTOBER_2026 + 60_000, 108_000, 108_010, 107_990, 108_005, 1.0)]
    )
    if not is_ok(committed):
        report.fail(f"case c: the open month did not commit: {committed.context}")
        return
    open_file = store.folder(bars) / OPEN_NAME
    if not open_file.is_file():
        report.fail("case c: the open month has no open file")
        return
    calls: list[tuple[str, ...]] = []

    def runner(call: tuple[str, ...]) -> str:
        calls.append(tuple(call))
        return ""

    with Store.open(common.scratch_folder("freeze") / "library", redactor=redact) as library:
        bucket = Bucket(library, remote="scratch-bucket", runner=runner)
        bucket.keep_series(FIXED_NAME, open_file)
        bucket.note()
        bucket.push()
        first = [call for call in calls if "copyto" in call and FIXED_NAME in " ".join(call)]
        report.numbers["c_first_batch"] = len(first)
        if not first:
            report.fail("case c: the open file was not in the bucket after the first batch")
        store.commit(
            bars,
            [
                (OCTOBER_2026 + 60_000, 108_000, 108_010, 107_990, 108_005, 1.0),
                (OCTOBER_2026 + 120_000, 108_005, 108_015, 107_995, 108_010, 2.0),
            ],
        )
        bucket.note()
        bucket.push()
        second = [call for call in calls if "copyto" in call and FIXED_NAME in " ".join(call)]
        report.numbers["c_second_batch"] = len(second)
        if len(second) <= len(first):
            report.fail("case c: the second batch did not overwrite the same fixed name")
        report.numbers["c_target"] = second[-1][3] if second else ""


def case_d(store: SeriesStore, report: Report, frozen: SeriesKey) -> None:
    opened = store.reopen(frozen)
    if not is_ok(opened) or opened.value.frozen:
        report.fail(f"case d: the frozen month did not re-open: {opened}")
        return
    report.numbers["d_reopened"] = True
    fetched = store.commit(frozen, [(JANUARY_2024 + 30 * DAY_MS + 9 * HOUR_MS, 5, 6, 0.2, 0.2)])
    if not is_ok(fetched) or not fetched.value.frozen:
        report.fail("case d: the re-fetched month did not freeze again")
        return
    state = store.state(frozen)
    report.numbers["d_corrections"] = len(state.corrections) if state else 0
    if state is None or not state.corrections:
        report.fail("case d: the re-fetched month left no correction record")
        return
    report.numbers["d_correction_reason"] = state.corrections[-1].reason


def main() -> int:
    report = Report(PROBE)
    scratch = common.scratch_folder("freeze")
    try:
        store = SeriesStore(scratch / "series", wall=Clock())
        frozen = case_a(store, report)
        case_b(store, report)
        case_c(store, report)
        case_d(store, report, frozen)
        return report.render()
    finally:
        common.drop_scratch()


if __name__ == "__main__":
    sys.exit(main())
