"""A unit's sweep cells: the kept Cartesian expansion over a unit's numbers and markets (B14).

A unit sweep names values for some of the unit's numbers and, optionally, the markets to run one
at a time. ``unit_cells`` hands that grid to the kept :func:`~qmb.sweep.axes.expand_sweep`, so a
unit cell list keeps the bot sweep's rules: no empty axis, no repeated value, no binary float,
and the same order (markets slowest, the last number fastest). Each cell is the unit document
with those numbers' defaults set and its markets narrowed, compiled afresh in its own folder:
another document, so another compiled fingerprint, and the core counts it as its own try.
"""

from __future__ import annotations

import copy
import json
import os
import shutil
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Final, cast

from qmf.core.refusal import Ok, Result, is_refusal

from qmb._refuse import invalid
from qmb.host.unit_runner import (
    LoadedUnit,
    UnitRunResult,
    load_unit_folder,
    parse_unit_run_request,
    run_loaded,
)
from qmb.sweep.axes import expand_sweep

__all__ = [
    "EVERY_MARKET",
    "Cell",
    "Ran",
    "cell_document",
    "lay_out",
    "range_grid",
    "run_cell",
    "trade_cell",
    "unit_cells",
]

EVERY_MARKET: Final = "*"
"""The markets axis of a sweep that runs every cell on all the unit's markets at once."""
_KEPT: Final = frozenset({"unit.json"})


@dataclass(frozen=True, slots=True)
class Cell:
    """One cell of a unit sweep: its name, the markets it trades, and its numbers' values."""

    name: str
    markets: tuple[str, ...] | None
    """None trades every market the unit names."""
    numbers: Mapping[str, str]

    def fields(self) -> dict[str, object]:
        return {
            "cell": self.name,
            "markets": None if self.markets is None else list(self.markets),
            "numbers": dict(self.numbers),
        }

    def counted(self) -> dict[str, object]:
        """How the core counts this cell: by its name, and its market when it trades one."""
        if self.markets is None:
            return {"name": self.name}
        return {"name": self.name, "market": self.markets[0]}


def unit_cells(grid: object, *, unit: str, bar_seconds: int) -> Result[tuple[Cell, ...]]:
    """``grid`` is ``{"numbers": {name: [values]}, "markets": [market ids]}``; both optional.

    Values are decimal text or whole numbers, as a unit document writes its numbers."""
    if not isinstance(grid, Mapping):
        return invalid("grid", "a sweep's grid is an object of numbers and markets")
    body = cast("Mapping[str, object]", grid)
    numbers = body.get("numbers", {})
    if not isinstance(numbers, Mapping):
        return invalid("grid", "grid.numbers maps a number's name to its values")
    for name, values in cast("Mapping[str, object]", numbers).items():
        listed = cast("Sequence[object]", values) if isinstance(values, list) else ()
        if not listed or not all(isinstance(v, str) or (type(v) is int) for v in listed):
            return invalid("grid", f"{name}'s values are decimal text or whole numbers")
    markets = body.get("markets", [EVERY_MARKET])
    expanded = expand_sweep(
        {
            "bot": unit,
            "book": "unit",
            "bms": "unit",
            "instruments": markets,
            "timeframes": [{"kind": "time-interval", "seconds": bar_seconds}],
            "parameters": {
                name: [str(v) for v in cast("list[object]", values)]
                for name, values in cast("Mapping[str, object]", numbers).items()
            },
        }
    )
    if is_refusal(expanded):
        return expanded
    width = len(str(len(expanded.value)))
    return Ok(
        tuple(
            Cell(
                f"cell-{index:0{max(width, 2)}d}",
                None if spec.instrument == EVERY_MARKET else (spec.instrument,),
                {name: str(value) for name, value in spec.parameters.items()},
            )
            for index, spec in enumerate(expanded.value, start=1)
        )
    )


def _range_values(name: str, spec: object) -> Result[list[str]]:
    if isinstance(spec, list):
        return Ok([str(v) for v in cast("list[object]", spec)])
    if not isinstance(spec, Mapping):
        return invalid("ranges", f"{name}: a range is a list of values or {{min, max, step}}")
    named = cast("Mapping[str, object]", spec)
    try:
        low, high, step = (Decimal(str(named[k])) for k in ("min", "max", "step"))
    except (KeyError, InvalidOperation):
        return invalid("ranges", f"{name}: a range names min, max and step as decimal text")
    if step <= 0 or high < low:
        return invalid(
            "ranges", f"{name}: a range's step is above zero and its max is not below its min"
        )
    return Ok([str(low + i * step) for i in range(int((high - low) / step) + 1)])


def range_grid(ranges: object) -> Result[dict[str, list[str]]]:
    """An optimize or walk-forward run's ``ranges``, each number's values listed or
    ``{"min", "max", "step"}`` as decimal text, as a sweep grid's numbers."""
    if not isinstance(ranges, Mapping) or not ranges:
        return invalid("ranges", "the run names the ranges of one number at least")
    grid: dict[str, list[str]] = {}
    for name, spec in cast("Mapping[str, object]", ranges).items():
        values = _range_values(name, spec)
        if is_refusal(values):
            return values
        grid[name] = values.value
    return Ok(grid)


def cell_document(document: Mapping[str, object], cell: Cell) -> Result[dict[str, object]]:
    """The unit document of one cell: its numbers' defaults set, its markets narrowed."""
    changed = copy.deepcopy(dict(document))
    numbers = cast("dict[str, dict[str, object]]", changed.get("numbers", {}))
    for name, value in cell.numbers.items():
        if name not in numbers:
            return invalid("grid", f"the unit has no number {name}", number=name)
        numbers[name]["default"] = value
    if cell.markets is not None:
        listed = cast("list[dict[str, object]]", changed.get("markets", []))
        kept = [m for m in listed if m.get("market_id") in cell.markets]
        if len(kept) != len(cell.markets):
            return invalid("grid", f"the unit trades no market {cell.markets[0]}")
        changed["markets"] = kept
    return Ok(changed)


def lay_out(base: Path, target: Path, document: Mapping[str, object]) -> None:
    """A cell's run folder: the base folder's blocks, records and bars, and its own document.

    Files are hard links where the drive allows them, else copies; the base stays as it was."""

    def link(source: str, destination: str) -> None:
        try:
            os.link(source, destination)
        except OSError:
            shutil.copyfile(source, destination)

    target.mkdir(parents=True, exist_ok=True)
    for entry in base.iterdir():
        if entry.name in _KEPT:
            continue
        if entry.is_dir():
            shutil.copytree(entry, target / entry.name, copy_function=link, dirs_exist_ok=True)
        else:
            link(str(entry), str(target / entry.name))
    (target / "unit.json").write_text(json.dumps(dict(document)), "utf-8")


@dataclass(frozen=True, slots=True)
class Ran:
    loaded: LoadedUnit
    result: UnitRunResult


def run_cell(folder: Path, body: Mapping[str, object]) -> Result[Ran]:
    """Compile the folder's unit and trade it, pinned to the fingerprint it compiled to."""
    loaded = load_unit_folder(folder)
    if is_refusal(loaded):
        return loaded
    pinned = dict(body) | {"compiled_fingerprint": loaded.value.compiled.compiled_fingerprint.value}
    request = parse_unit_run_request(pinned)
    if is_refusal(request):
        return request
    ran = run_loaded(loaded.value, request.value)
    if is_refusal(ran):
        return ran
    return Ok(Ran(loaded.value, ran.value))


def trade_cell(
    base: Path, target: Path, document: Mapping[str, object], cell: Cell, body: Mapping[str, object]
) -> Result[Ran]:
    """One cell traded in its own folder ``target``, laid out from the base run folder."""
    made = cell_document(document, cell)
    if is_refusal(made):
        return made
    lay_out(base, target, made.value)
    return run_cell(target, body)
