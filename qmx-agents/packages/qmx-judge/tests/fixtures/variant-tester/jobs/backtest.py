"""The variant's `backtest` run kind: the run folder the core laid out, traded by `variant.py`."""

from __future__ import annotations

import runpy
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, cast

VARIANT = cast("dict[str, Any]", runpy.run_path(str(Path(__file__).parents[1] / "variant.py")))
replay = cast("Callable[[Path, str], dict[str, object] | str]", VARIANT["replay"])
leave = cast("Callable[..., object]", VARIANT["leave"])


def run(inputs: Mapping[str, object]) -> object:
    run_id, folder = str(inputs["run_id"]), Path(str(inputs["run_folder"]))
    found = replay(folder, run_id)
    return (
        leave(folder, run_id, None, found)
        if isinstance(found, str)
        else leave(folder, run_id, found)
    )
