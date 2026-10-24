"""Two cached months go through the door and only they are materialised, and the model carries the
lineage (Lab AD-19, AD-20; DATA-PLAN DR13).

This is the section's lane-3 proof at unit speed. A real `SeriesStore` holds two committed monthly
partitions of EURUSD ticks; the real `MarketDoor` serves them from a scratch root, and the Lab's
placement materialises exactly the two the run asked for, into its own cache, verifying each
fingerprint. Then the `model` lands with the data fingerprints, the code version and the seed.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from qmf.core import Result, is_ok, is_refusal
from qmf.data.series import SeriesKey, SeriesStore
from qmx_control.lab import Answered, Lab
from qmx_control.lab import Placement as LabPlacement
from qmx_control.library import OPERATOR, Library
from qmx_host.market_data import (  # pyright: ignore[reportMissingTypeStubs]
    MarketDoor,
    Placement,
)
from qmx_library.port import Draft
from qmx_library.principal import MAIN

SERIES = "dukascopy/EURUSD/ticks/-"
JANUARY = 1_767_225_600_000_000_000
FEBRUARY = 1_769_904_000_000_000_000
BEFORE = datetime(2026, 3, 1, tzinfo=UTC)
SEAL = 1_800_000_000_000_000_000
"""A seal boundary past both months: these two are open, and the run may read them."""
MB = 1024 * 1024


class Installs:
    """The engine's install, which this test never reaches."""

    def install(self, template_id: str) -> Answered[str]:
        raise AssertionError("a training run installs no template")


class Hosted:
    """The door as the host hands it to the Lab: its `Result` in the Lab's answer shape.

    `qmx_control` may not depend on `qmf`, so the Lab names the answers it reads and the host wraps
    the real `MarketDoor` here. This class is the whole adapter."""

    def __init__(self, door: MarketDoor) -> None:
        self.door = door

    def card(self, series: str) -> Answered[dict[str, object]]:
        return served(self.door.card(series))

    def read(
        self, series: str, *, start_ns: int, end_ns: int, purpose: str = "exploration"
    ) -> Answered[dict[str, object]]:
        return served(self.door.read(series, start_ns=start_ns, end_ns=end_ns, purpose=purpose))

    def materialise(
        self, fingerprints: Sequence[str], *, into: Path | None = None
    ) -> Answered[Sequence[Path]]:
        return served(self.door.materialise(fingerprints, into=into))


def served(result: Result[Any]) -> Answered[Any]:
    """A `qmf` Result as the Lab's answer: the value, or the refusal's code and context."""
    if is_refusal(result):
        return Answered(refusal=str(result))
    value = cast(Any, result).value
    return Answered(value.as_json() if hasattr(value, "as_json") else value)


def ticks(start: int, rows: int) -> list[tuple[int, float, float, float, float]]:
    return [
        (start + minute * 60_000, 1_084_500 + minute, 1_084_520 + minute, 1.0, 1.0)
        for minute in range(rows)
    ]


def door_at(root: Path) -> MarketDoor:
    opened = MarketDoor.open(root, {"seal_boundary_ns": SEAL}, placement=Placement.PC)
    assert is_ok(opened), opened
    return opened.value


def test_two_cached_months_are_the_only_partitions_and_the_model_keeps_the_lineage(
    tmp_path: Path,
) -> None:
    store = SeriesStore(tmp_path / "series", wall=lambda: BEFORE)
    for year, month, start in (
        (2026, 1, JANUARY),
        (2026, 2, FEBRUARY),
    ):
        key = SeriesKey.try_create("dukascopy", "EURUSD", "ticks", year, month)
        assert is_ok(key), key
        landed = store.commit(key.value, ticks(start, 120))
        assert is_ok(landed), landed

    library = Library(tmp_path / "home")
    card = library.store.put(
        OPERATOR,
        Draft(
            "dataset",
            None,
            title="EURUSD ticks",
            fields={"series_key": SERIES, "quality": {"grade": "A"}},
        ),
        on=MAIN,
        expected_head=None,
    ).object_id
    cache = tmp_path / "cache"
    lab = Lab(
        library,
        installs=Installs(),
        door=Hosted(door_at(tmp_path)),
        placement=LabPlacement(gpu_slots=1, device="Quadro T1000", cache=cache),
    )

    training = lab.training(
        card,
        months=["2026-01", "2026-02"],
        seed=7,
        code_version="sha256:d6-template",
        free=512 * MB,
    )
    model = lab.model(training, weights=b"the weights")

    assert training.months == ("2026-01", "2026-02")
    assert [path.parent for path in training.paths] == [cache, cache]
    assert sorted(path.name for path in cache.glob("*.parquet")) == sorted(
        f"{fingerprint}.parquet" for fingerprint in training.fingerprints
    )
    fields = model["fields"]
    assert isinstance(fields, dict)
    assert fields["months"] == ["2026-01", "2026-02"]
    assert fields["data"] == {
        "card": card,
        "fingerprints": list(training.fingerprints),
    }
    assert (fields["seed"], fields["code"], fields["hardware"]) == (
        7,
        {"version": "sha256:d6-template"},
        {"placement": "pc", "gpu_slot": 0, "device": "Quadro T1000"},
    )
