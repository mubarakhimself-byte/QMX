"""The training template reads through the market-data door and records the model's lineage (DR13).

The steps are scripts an operator can edit and the engine runs as subprocesses, so what is tested
here is what they do at the seams they own: the partitions they ask the door for, the splits they
draw, the device they choose and the lineage they write. The scripts are loaded the way the engine
loads them, from the template folder.
"""

from __future__ import annotations

import importlib.util
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from qmf.core import Ok

from qmx_engine.settings import DEFAULTS

TEMPLATE = (
    Path(__file__).parents[1]
    / "src"
    / "qmx_engine"
    / "templates"
    / "d6-ml-training-run"
    / "scripts"
)


def script(name: str) -> ModuleType:
    """One template script as a module, without running its `main` block."""
    spec = importlib.util.spec_from_file_location(f"d6_{name}", TEMPLATE / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Door:
    """What the door answers for a series with two months, and what it was asked to materialise."""

    def __init__(self) -> None:
        self.asked: list[tuple[str, ...]] = []

    def card(self, series: str) -> object:
        return Ok(
            {
                "series": series,
                "partitions": [
                    {"month": "2026-01", "fingerprint": "a" * 64, "bytes": 10},
                    {"month": "2026-02", "fingerprint": "b" * 64, "bytes": 20},
                ],
            }
        )

    def materialise(self, fingerprints: Sequence[str], *, into: Path | None = None) -> object:
        self.asked.append(tuple(fingerprints))
        return Ok(tuple(Path("/attempt") / f"{found[:6]}.parquet" for found in fingerprints))


def test_the_dataset_step_asks_the_door_for_exactly_its_months() -> None:
    module = script("dataset")
    door = Door()

    rows, why = module.partitions(door, "dukascopy/EURUSD/ticks/-", ["2026-02"], Path("/attempt"))

    assert (rows, why) == (
        [
            {
                "month": "2026-02",
                "fingerprint": "b" * 64,
                "bytes": 20,
                "path": str(Path("/attempt") / "bbbbbb.parquet"),
            }
        ],
        "",
    )
    assert door.asked == [("b" * 64,)]


def test_the_dataset_step_refuses_a_month_the_series_does_not_hold() -> None:
    module = script("dataset")

    rows, why = module.partitions(Door(), "dukascopy/EURUSD/ticks/-", ["2026-05"], Path("/attempt"))

    assert rows is None
    assert why == (
        "dukascopy/EURUSD/ticks/- holds no partition for 2026-05; the run asked for ['2026-05']"
    )


def test_the_splits_keep_a_purge_and_an_embargo_between_them() -> None:
    module = script("dataset")

    assert module.split_of(600, 3, 4) == {
        "train": [0, 397],
        "validation": [404, 497],
        "test": [504, 600],
    }


def test_the_training_step_trains_on_the_cpu_when_no_card_is_there() -> None:
    module = script("train")

    class Cuda:
        @staticmethod
        def is_available() -> bool:
            return False

    class Torch:
        cuda = Cuda

    device, why = module.device_of(Torch)

    assert (device, why) == (
        "cpu",
        "torch sees no CUDA device, so this run trains on the PC's CPU",
    )


def test_the_training_step_names_the_card_it_trains_on() -> None:
    module = script("train")

    class Properties:
        total_memory = 4096 * 1024 * 1024

    class Cuda:
        @staticmethod
        def is_available() -> bool:
            return True

        @staticmethod
        def get_device_name(index: int) -> str:
            return "Quadro T1000"

        @staticmethod
        def get_device_properties(index: int) -> Properties:
            return Properties()

    class Torch:
        cuda = Cuda

    assert module.device_of(Torch) == ("cuda", "Quadro T1000, 4096.0 MB")


def test_the_pc_placement_declares_the_one_gpu_slot_p_gpu_measured() -> None:
    assert DEFAULTS["placement.pc.gpu_slots"] == 1


def test_the_template_names_its_level_and_its_gpu_slot() -> None:
    import json

    definition = cast(
        dict[str, Any],
        json.loads((TEMPLATE.parent / "definition.json").read_text(encoding="utf-8")),
    )

    assert definition["meta"] == {
        "template": "ml-training-run-with-a-holdout",
        "needs": ["qmb-door", "sandbox"],
        "levels": ["experiment"],
        "gpu_slot": 1,
    }
