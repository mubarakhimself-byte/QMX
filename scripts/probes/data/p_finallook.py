"""P-FINALLOOK: the one sealed look is served by the primary's door and journaled there.

Acceptance probe for DR3B (W10). It builds two scratch roots, one for the primary's door and
one for the PC's, imports one open month and one sealed month, and checks:

- a final look asked for on the PC is forwarded to the primary and journaled there once, with
  the split it was taken under;
- a second final look for the same window, from either machine, is refused;
- with the primary unreachable the PC's request waits and serves nothing;
- a door off the primary never serves a look from its own store;
- a sealed read is refused with its reason rather than answered empty.

Nothing here touches his real home, his stores or his settings. Every root is under
`--scratch` (default `D:/Temp`) and is removed before the verdict is printed unless `--keep`.
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from qmf.core import CalendarIdentity, Result, World, is_ok, is_refusal
from qmf.data.series import SeriesKey
from qmf.data.splits import SplitBoundary, SplitManifest
from qmf.data.store.engines.typed import TypedWriter

from qmx_host.market_data import SEAL_READ_REASON, MarketDoor, Placement, Purpose, ReadAnswer

DAY = 86_400 * 1_000_000_000


def _at(year: int, month: int, day: int = 1) -> int:
    return int(datetime(year, month, day, tzinfo=UTC).timestamp()) * 1_000_000_000


JAN = _at(2026, 1, 1)
TRAIN_END = _at(2026, 1, 10)
VALIDATION_END = _at(2026, 1, 20)
FEB = _at(2026, 2, 1)
MAR = _at(2026, 3, 1)
SERIES = "dukascopy/EURUSD/bar-m1/-"


def _split() -> SplitManifest:
    calendar = CalendarIdentity.try_create("forex-17NY", "v1", "2025a")
    assert is_ok(calendar)
    segments = SplitManifest.default_split_segments([TRAIN_END, VALIDATION_END, FEB])
    assert is_ok(segments)
    built = SplitManifest.try_create(
        calendar_identity=calendar.value,
        segments=segments.value,
        seal_boundary=SplitBoundary.try_create(FEB).value,
        purge_width=0,
        embargo_width=0,
        gap=DAY,
        world=World.REPLAY,
    )
    assert is_ok(built)
    return built.value


def _door(root: Path, placement: Placement, split: SplitManifest) -> MarketDoor:
    built = MarketDoor.open(
        root,
        {"seal_boundary_ns": FEB, "holdout_months": 1},
        placement=placement,
        split=split,
    )
    assert is_ok(built)
    return built.value


def _stage(root: Path, key: SeriesKey, times_ns: list[int]) -> Path:
    path = root / key.series / f"{key.year:04d}-{key.month:02d}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = [(ns // 1_000_000, 1, 2, 0, 2, 1.0) for ns in times_ns]
    TypedWriter(path, key.text, key.rule.columns).add(rows).finish()
    return path


def _import(scratch: Path, door: MarketDoor) -> None:
    staging = scratch / "staging"
    files = [
        _stage(staging, _key(2026, 1), [JAN + DAY, JAN + 2 * DAY]),
        _stage(staging, _key(2026, 2), [FEB + DAY]),
    ]
    landed = door.commit(files, staging=staging)
    assert is_ok(landed), landed


def _key(year: int, month: int) -> SeriesKey:
    built = SeriesKey.try_create("dukascopy", "EURUSD", "bar-m1", year, month)
    assert is_ok(built)
    return built.value


def _forward(primary: MarketDoor):
    """The host's tailnet call, in one process: the PC's door hands the look to the primary's."""

    def forward(asked: dict[str, object]) -> Result[ReadAnswer]:
        return primary.read(
            str(asked["series"]),
            start_ns=int(asked["start_ns"]),  # type: ignore[arg-type]
            end_ns=int(asked["end_ns"]),  # type: ignore[arg-type]
            purpose=Purpose.FINAL_LOOK,
            into=Path(str(asked["into"])),
            data_scope=list(asked.get("data_scope", ())),  # type: ignore[call-overload]
        )

    return forward


def check(scratch: Path) -> list[str]:
    """Every failure this probe finds, in plain words. An empty list is a pass."""
    failures: list[str] = []
    split = _split()
    primary_root = scratch / "primary"
    pc_root = scratch / "pc"
    primary = _door(primary_root, Placement.SERVER, split)
    _import(scratch / "primary-import", primary)
    pc = _door(pc_root, Placement.PC, split)
    _import(scratch / "pc-import", pc)

    refused_read = pc.read(SERIES, start_ns=FEB, end_ns=MAR)
    if not is_refusal(refused_read):
        failures.append("a sealed read was served instead of refused")
    elif SEAL_READ_REASON not in str(refused_read.context):
        failures.append("a sealed read was refused without its reason")

    attempt = scratch / "attempt-1"
    wired = MarketDoor(
        root=pc.root,
        seal=pc.seal,
        split=pc.split,
        placement=Placement.PC,
        world=pc.world,
        handles=pc.handles,
        primary_forward=_forward(primary),
    )
    first = wired.read(
        SERIES,
        start_ns=FEB,
        end_ns=MAR,
        purpose=Purpose.FINAL_LOOK,
        data_scope=[SERIES],
        into=attempt,
    )
    if is_refusal(first):
        failures.append(f"the PC's final look was refused with the primary reachable: {first}")
    looks = _looks(primary)
    if len(looks) != 1:
        failures.append(f"the primary journaled {len(looks)} final looks, not one")
    elif looks[0].get("split_id") != split.split_id:
        failures.append("the journaled look does not name the split it was taken under")

    second_pc = wired.read(
        SERIES,
        start_ns=FEB,
        end_ns=MAR,
        purpose=Purpose.FINAL_LOOK,
        data_scope=[SERIES],
        into=attempt,
    )
    if not is_refusal(second_pc):
        failures.append("a second final look from the PC was served")
    second_primary = primary.read(
        SERIES, start_ns=FEB, end_ns=MAR, purpose=Purpose.FINAL_LOOK, into=scratch / "attempt-2"
    )
    if not is_refusal(second_primary):
        failures.append("a second final look on the primary was served")
    if len(_looks(primary)) != 1:
        failures.append("the journal holds more than one final look")

    unreachable = wired.__class__(
        root=pc.root,
        seal=pc.seal,
        split=pc.split,
        placement=Placement.PC,
        world=pc.world,
        handles=pc.handles,
        primary_forward=None,
    )
    waited = unreachable.read(
        SERIES,
        start_ns=FEB,
        end_ns=MAR,
        purpose=Purpose.FINAL_LOOK,
        data_scope=[SERIES],
        into=scratch / "attempt-3",
    )
    if not is_refusal(waited):
        failures.append("the PC's door served a final look with the primary unreachable")
    elif "waits" not in str(waited.context):
        failures.append("the waiting refusal does not say it waits")

    off_primary = pc.read(
        SERIES, start_ns=FEB, end_ns=MAR, purpose=Purpose.FINAL_LOOK, into=scratch / "attempt-4"
    )
    if not is_refusal(off_primary):
        failures.append("a door off the primary served a look")
    return failures


def _looks(primary: MarketDoor) -> list[dict[str, object]]:
    journal = primary._journal()  # noqa: SLF001 - the probe reads the stream the door wrote
    assert is_ok(journal)
    events = journal.value.read_stream("qmf-data-control-action", for_world=primary.world)
    assert is_ok(events)
    return [
        event
        for event in events.value
        if event.get("control_action_subtype") == "sealed-period-final-look"
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", default="D:/Temp", help="where the scratch roots go")
    parser.add_argument("--keep", action="store_true", help="leave the scratch roots behind")
    arguments = parser.parse_args()
    scratch = Path(tempfile.mkdtemp(prefix="p-finallook-", dir=arguments.scratch))
    try:
        failures = check(scratch)
    finally:
        if not arguments.keep:
            shutil.rmtree(scratch, ignore_errors=True)
    if failures:
        for failure in failures:
            print(f"P-FINALLOOK FAIL {failure}")
        return 1
    print("P-FINALLOOK PASS one look journaled on the primary, a second refused, the PC waits")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
