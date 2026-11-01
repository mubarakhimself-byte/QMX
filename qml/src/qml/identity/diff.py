"""``diff`` and ``classify``: two unit documents to edit labels, then to one answer (AD-115).

``diff`` walks the two typed documents field by field and names each change with one label and
the JSON pointer it is about, so the promotion card can show it (OP-03). ``classify`` looks every
label up in his table and keeps the highest result. ``unit_id`` and lineage parents are the
answer's bookkeeping, not an edit, so they are not diffed; ``rewritten_from`` and a parent from
another unit are.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from typing import TypeVar

from qml.identity.table import UNLISTED, EditLabel, IdentityTable, Result
from qml.unit.model import (
    Binding,
    Logic,
    Market,
    MirrorSide,
    MotionMode,
    NumberKind,
    NumberParam,
    NumberSpec,
    Pin,
    ScopedBinding,
    SlotsSide,
    Stream,
    Unit,
    ValueParam,
)

__all__ = ["Classification", "Edit", "classify", "diff"]


@dataclass(frozen=True)
class Edit:
    label: EditLabel
    path: str


@dataclass(frozen=True)
class Classification:
    labels: tuple[EditLabel, ...]
    result: Result
    counted_try: bool
    click_before_live: bool
    edits: tuple[Edit, ...]
    unlisted: tuple[EditLabel, ...] = ()
    """Labels his table has no row for, each counted as a new unit with a try and a click."""


_Add = Callable[[EditLabel, str], None]
_T = TypeVar("_T")


def _by(items: Iterable[_T], key: Callable[[_T], str]) -> dict[str, _T]:
    return {key(item): item for item in items}


def _keyed(
    add: _Add,
    path: str,
    old: Mapping[str, _T],
    new: Mapping[str, _T],
    changed: EditLabel,
    same: Callable[[str, _T, _T], None],
) -> None:
    for name in old.keys() - new.keys() | new.keys() - old.keys():
        add(changed, f"{path}/{name}")
    for name in old.keys() & new.keys():
        same(f"{path}/{name}", old[name], new[name])


def _param(add: _Add, path: str, old: object, new: object) -> None:
    if old == new:
        return
    if isinstance(old, ValueParam) and isinstance(new, ValueParam):
        add(EditLabel.FIXED_VALUE_CHANGE, path)
    elif isinstance(old, NumberParam) != isinstance(new, NumberParam):
        add(EditLabel.MOTION_RULE_CHANGE, path)
    else:
        add(EditLabel.STRUCTURE_CHANGE, path)


def _binding(add: _Add, path: str, old: Binding, new: Binding) -> None:
    if old.block.entry_id != new.block.entry_id:
        add(EditLabel.BLOCK_SWAP, f"{path}/block")
    elif old.block.version != new.block.version:
        add(EditLabel.BLOCK_FIX, f"{path}/block")
    for name in old.params.keys() | new.params.keys():
        _param(add, f"{path}/params/{name}", old.params.get(name), new.params.get(name))
    if old.inputs != new.inputs:
        add(EditLabel.STRUCTURE_CHANGE, f"{path}/inputs")
    old_scope = old.scope if isinstance(old, ScopedBinding) else None
    new_scope = new.scope if isinstance(new, ScopedBinding) else None
    if old_scope != new_scope:
        add(EditLabel.STRUCTURE_CHANGE, f"{path}/scope")


def _bindings(add: _Add, path: str, old: Iterable[Binding], new: Iterable[Binding]) -> None:
    def same(where: str, a: Binding, b: Binding) -> None:
        _binding(add, where, a, b)

    _keyed(
        add,
        path,
        _by(old, lambda b: b.name),
        _by(new, lambda b: b.name),
        EditLabel.BLOCK_SWAP,
        same,
    )


def _role(add: _Add, path: str, old: tuple[Binding, ...], new: tuple[Binding, ...]) -> None:
    """A role held as a binding list (exits, halts): empty to filled adds the role."""
    if not old and new:
        add(EditLabel.ROLE_ADDED, path)
    elif old and not new:
        add(EditLabel.ROLE_REMOVED, path)
    else:
        _bindings(add, path, old, new)


def _logic(add: _Add, old: Logic, new: Logic) -> None:
    for side in ("long", "short"):
        path = f"/logic/{side}"
        a: SlotsSide | MirrorSide | None = getattr(old, side)
        b: SlotsSide | MirrorSide | None = getattr(new, side)
        if isinstance(a, SlotsSide) and isinstance(b, SlotsSide):
            for name in a.slots.keys() - b.slots.keys():
                add(EditLabel.ROLE_REMOVED, f"{path}/slots/{name}")
            for name in b.slots.keys() - a.slots.keys():
                add(EditLabel.ROLE_ADDED, f"{path}/slots/{name}")
            for name in a.slots.keys() & b.slots.keys():
                was, now, where = a.slots[name], b.slots[name], f"{path}/slots/{name}"
                if was.role != now.role:
                    add(EditLabel.ROLE_REMOVED, f"{where}/role")
                    add(EditLabel.ROLE_ADDED, f"{where}/role")
                if was.combiner != now.combiner:
                    add(EditLabel.COMBINER_CHANGE, f"{where}/combiner")
                _bindings(add, f"{where}/bindings", was.bindings, now.bindings)
        elif a != b:
            add(EditLabel.STRUCTURE_CHANGE, path)


def _inside(value: str, spec: NumberSpec) -> bool:
    if spec.range is None:
        return False
    try:
        number = Decimal(value)
    except InvalidOperation:
        return False
    return spec.range.min <= number <= spec.range.max


def _number(add: _Add, path: str, old: NumberSpec, new: NumberSpec) -> None:
    if old.kind != new.kind:
        add(EditLabel.MOTION_RULE_CHANGE, f"{path}/kind")
    if old.measure != new.measure:
        add(EditLabel.STRUCTURE_CHANGE, f"{path}/measure")
    if old.range != new.range:
        add(EditLabel.RANGE_CHANGE, f"{path}/range")
    if old.motion.cadence != new.motion.cadence:
        add(EditLabel.CADENCE_CHANGE, f"{path}/motion/cadence")
    if _rule(old) != _rule(new):
        add(EditLabel.MOTION_RULE_CHANGE, f"{path}/motion")
    if old.origin != new.origin:
        add(EditLabel.AMBIGUITY_RESOLVED, f"{path}/origin")
    if old.default != new.default:
        add(_moved(new), f"{path}/default")


def _rule(spec: NumberSpec) -> object:
    """How the number moves, less its cadence, which has its own label."""
    return (replace(spec.motion, cadence=None), spec.authority, spec.applies_to_open_positions)


def _moved(spec: NumberSpec) -> EditLabel:
    """The label for a new default: a moving number inside its range is a calibration."""
    if spec.kind is NumberKind.FIXED:
        return EditLabel.FIXED_VALUE_CHANGE
    if spec.motion.mode is MotionMode.LEARNED:
        if _inside(spec.default, spec):
            return EditLabel.LEARNED_RETRAIN_IN_BOUNDS
        return EditLabel.LEARNED_RETRAIN_OUT_OF_BOUNDS
    if _inside(spec.default, spec):
        return EditLabel.MOTION_INSIDE_RANGE
    return EditLabel.FIXED_VALUE_CHANGE


def diff(old: Unit, new: Unit) -> tuple[Edit, ...]:
    """Every change from ``old`` to ``new``, each with its label and pointer, in document order."""
    edits: list[Edit] = []

    def add(label: EditLabel, path: str) -> None:
        edits.append(Edit(label, path))

    if old.title != new.title:
        add(EditLabel.TITLE_CHANGE, "/title")
    if old.family_id != new.family_id:
        add(EditLabel.STRUCTURE_CHANGE, "/family_id")
    if old.claim_card != new.claim_card:
        add(EditLabel.AMBIGUITY_RESOLVED, "/claim_card")
    _lineage(add, old, new)

    def market(path: str, a: Market, b: Market) -> None:
        if (a.instrument_ref, a.roll) != (b.instrument_ref, b.roll):
            add(EditLabel.MARKETS_CHANGE, path)
        if (a.settings, a.settings_record) != (b.settings, b.settings_record):
            add(EditLabel.MARKET_SETTINGS_ADOPTED, f"{path}/settings")

    _keyed(
        add,
        "/markets",
        _by(old.markets, lambda m: m.market_id),
        _by(new.markets, lambda m: m.market_id),
        EditLabel.MARKETS_CHANGE,
        market,
    )

    def stream(path: str, a: Stream, b: Stream) -> None:
        if a.bar != b.bar:
            add(EditLabel.BAR_CHANGE, f"{path}/bar")
        if replace(a, bar=b.bar) != b:
            add(EditLabel.STRUCTURE_CHANGE, path)

    _keyed(
        add,
        "/streams",
        _by(old.streams, lambda s: s.name),
        _by(new.streams, lambda s: s.name),
        EditLabel.STRUCTURE_CHANGE,
        stream,
    )
    if old.sessions != new.sessions:
        add(EditLabel.SESSION_CHANGE, "/sessions")
    if old.direction != new.direction:
        add(EditLabel.STRUCTURE_CHANGE, "/direction")
    _logic(add, old.logic, new.logic)
    _role(add, "/exit_set", old.exit_set, new.exit_set)
    for scope in ("position", "unit", "account"):
        _role(add, f"/halts/{scope}", getattr(old.halts, scope), getattr(new.halts, scope))
    _role(add, "/sizer", _one(old.sizer), _one(new.sizer))
    if old.reads != new.reads:
        add(EditLabel.STRUCTURE_CHANGE, "/reads")

    def number(path: str, a: NumberSpec, b: NumberSpec) -> None:
        _number(add, path, a, b)

    _keyed(add, "/numbers", old.numbers, new.numbers, EditLabel.STRUCTURE_CHANGE, number)

    def pin(path: str, a: Pin, b: Pin) -> None:
        if a != b:
            add(EditLabel.BLOCK_FIX, path)

    _keyed(
        add,
        "/pins",
        _by(old.pins, lambda p: p.entry_id),
        _by(new.pins, lambda p: p.entry_id),
        EditLabel.BLOCK_SWAP,
        pin,
    )
    for name in ("position_limit", "context_needs", "routes", "baseline"):
        if getattr(old, name) != getattr(new, name):
            add(EditLabel.STRUCTURE_CHANGE, f"/{name}")
    _plain_python(add, old, new)
    return tuple(edits)


def _one(binding: Binding | None) -> tuple[Binding, ...]:
    return () if binding is None else (binding,)


def _lineage(add: _Add, old: Unit, new: Unit) -> None:
    was = old.lineage.rewritten_from if old.lineage else None
    now = new.lineage.rewritten_from if new.lineage else None
    if now is not None and now != was:
        add(EditLabel.REWRITE, "/lineage/rewritten_from")
    known = {old.unit_id, new.unit_id}
    before = {p.unit_id for p in old.lineage.parents} if old.lineage else set[str]()
    after = {p.unit_id for p in new.lineage.parents} if new.lineage else set[str]()
    if after - before - known:
        add(EditLabel.TRANSPLANT, "/lineage/parents")


def _plain_python(add: _Add, old: Unit, new: Unit) -> None:
    a, b = old.plain_python, new.plain_python
    if a is None or b is None:
        if a != b:
            add(EditLabel.STRUCTURE_CHANGE, "/plain_python")
    elif a.block.entry_id != b.block.entry_id:
        add(EditLabel.BLOCK_SWAP, "/plain_python/block")
    elif a.block.version != b.block.version:
        add(EditLabel.BLOCK_FIX, "/plain_python/block")


def classify(old: Unit, new: Unit, table: IdentityTable) -> Classification:
    """``diff`` then his table: per label its row, and the highest result of all of them."""
    edits = diff(old, new)
    labels = tuple(sorted({edit.label for edit in edits}))
    rows = [table.row(label) or UNLISTED for label in labels]
    result = max((row.result for row in rows), key=lambda r: r.rank, default=Result.NONE)
    return Classification(
        labels=labels,
        result=result,
        counted_try=any(row.counted_try for row in rows),
        click_before_live=any(row.click_before_live for row in rows),
        edits=edits,
        unlisted=tuple(label for label in labels if table.row(label) is None),
    )
