"""The dictionary entry ``qmx.entry/1``, its checker and its computed status (Part A AD-113).

An entry is the ``entry`` object of one ``component`` item, flat, with ``component_type`` beside
it. Its fields fall into three faces: trader words (what a trader means by the word), the machine
spec (what the block reads, returns and needs) and the implementation (its code and the evidence
that the code is right). ``FACES`` names which field belongs to which.

``check_entry`` is the Library's put check of an item marked ``qmx.entry/1``: every problem at
once, each with the JSON pointer of its place in the entry. A problem refuses the save. A face
that is not written yet is not a problem; it only keeps the status low. ``compute_status`` gives
the status from evidence, never from the author: ``named`` once the entry passes the checker,
``specified`` once its machine face is complete, ``implemented`` once its code passes the
implementation checks. ``tested_on_data`` and ``used_in_unit`` are the next rungs; nothing
computes them yet, because no record of a run on a recorded slice per class exists yet.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Final, cast

from qmf.core.fingerprint import fingerprint
from qmf.core.refusal import is_refusal

from qml.blocks.api import ENTRY_SCHEMA, Instance, Mirroring, OutputType, Signal
from qml.catalogue.datalevel import HOST_FACTS, level_of, split_problems
from qml.catalogue.loader import LockEntry, block_fingerprint, load
from qml.catalogue.roles import role_problem
from qml.check import check_block
from qml.numbers import InstrumentClass
from qml.unit.model import Measure, NumberKind, Origin

__all__ = [
    "CHECKER_VERSION",
    "CUT_SAMPLES",
    "ENTRY_SCHEMA",
    "FACES",
    "GOLDEN_ABSOLUTE",
    "GOLDEN_RELATIVE",
    "ComponentType",
    "Computed",
    "EntryOrigin",
    "EntryProblem",
    "Status",
    "Transfer",
    "alias_key",
    "check_entry",
    "compute_status",
    "corpus_problems",
]

CHECKER_VERSION: Final[str] = "qml.entry/1 r1"
"""Bumped by any change that alters a verdict, so a stored status names the checker it met."""

GOLDEN_RELATIVE: Final[Decimal] = Decimal("1e-9")
GOLDEN_ABSOLUTE: Final[Decimal] = Decimal("1e-12")
"""Starting defaults of the ``golden_tolerance`` setting (CONTRACTS.md section 9)."""

CUT_SAMPLES: Final[int] = 5
"""Starting default: the instants of a golden series where the value from data cut there is
compared with the value from the full series (QML-01)."""


class Status(StrEnum):
    NAMED = "named"
    SPECIFIED = "specified"
    IMPLEMENTED = "implemented"
    TESTED_ON_DATA = "tested_on_data"
    USED_IN_UNIT = "used_in_unit"


class Transfer(StrEnum):
    """How an entry carries to a market class."""

    NATIVE = "native"
    DIRECT = "direct"
    ADAPTED = "adapted"
    CONCEPTUAL_ONLY = "conceptual_only"
    NOT_TRANSFERABLE = "not_transferable"
    NOT_ASSESSED = "not_assessed"


class EntryOrigin(StrEnum):
    QML = "qml"
    PORT = "port-239"
    AGENT = "agent"
    HUMAN = "human"
    PLACEHOLDER = "placeholder"  # mock-data-scan: allow (the risk session's label, AD-116)


class ComponentType(StrEnum):
    """The ``component`` kind's types: the five it shipped with, then the entry's."""

    INDICATOR = "indicator"
    COMBINATION = "combination"
    FEATURE = "feature"
    FILTER = "filter"
    LABELER = "labeler"
    TRIGGER = "trigger"
    EXIT = "exit"
    SIZER = "sizer"
    MOTION = "motion"
    READING = "reading"
    COMBINER = "combiner"
    CALENDAR = "calendar"
    CONTEXT = "context"
    STRUCTURE = "structure"
    STATISTIC = "statistic"
    MODEL = "model"
    ENTRY_ORDER = "entry_order"
    HALT = "halt"
    HOOK = "hook"


FACES: Final[Mapping[str, tuple[str, ...]]] = {
    "identity": ("schema", "entry_id", "version", "family", "aliases", "same_word_as", "origin"),
    "trader": (
        "definition",
        "boundaries",
        "recognition",
        "eligible_roles",
        "class_meanings",
        "sources",
    ),
    "machine": (
        "component_type",
        "inputs",
        "output",
        "parameters",
        "warm_up",
        "confirmation_lag_bars",
        "min_sample",
        "expected_lag_bars",
        "transfer",
        "mirroring",
        "state_bound",
        "reading",
    ),
    "implementation": ("fingerprint", "golden", "tests", "settle_bars", "owner"),
}

_SPECIFIED: Final = ("inputs", "output", "parameters", "warm_up", "transfer", "mirroring")
_TRANSFER_NEEDS_SOURCE: Final = frozenset({Transfer.NATIVE, Transfer.DIRECT})
_ID: Final = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
_PIN: Final = re.compile(r"^[a-z0-9][a-z0-9._-]*@[1-9][0-9]*$")
_DATE: Final = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
_FP: Final = re.compile(r"^fp1:sha256:[0-9a-f]{64}$")
_DECIMAL: Final = re.compile(r"^-?(0|[1-9][0-9]*)(\.[0-9]+)?$")


@dataclass(frozen=True, slots=True)
class EntryProblem:
    """One problem: ``where`` is the JSON pointer of its place in the entry."""

    where: str
    message: str
    hint: str

    def as_json(self) -> dict[str, str]:
        return {"where": self.where, "message": self.message, "hint": self.hint}


@dataclass(slots=True)
class _Found:
    problems: list[EntryProblem] = field(default_factory=lambda: [])

    def add(self, where: str, message: str, hint: str) -> None:
        self.problems.append(EntryProblem(where, message, hint))


_Check = Callable[[object, str, _Found], None]


def _text(value: object, where: str, found: _Found) -> None:
    if not isinstance(value, str) or not value.strip():
        found.add(where, f"{where} is a non-empty string", "write it in plain words")


def _count(value: object, where: str, found: _Found) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        found.add(where, f"{where} is a whole number of 0 or more", "count it in bars")


def _object(value: object, where: str, found: _Found) -> bool:
    if isinstance(value, Mapping):
        return True
    found.add(where, f"{where} is an object", "write it as a JSON object")
    return False


def _list(value: object, where: str, found: _Found) -> list[object] | None:
    if isinstance(value, list):
        return cast("list[object]", value)
    found.add(where, f"{where} is a list", "write it as a JSON list")
    return None


def _enum(words: type[StrEnum]) -> _Check:
    allowed = [w.value for w in words]

    def check(value: object, where: str, found: _Found) -> None:
        if value not in allowed:
            found.add(where, f"{where} is {value!r}, not one of {', '.join(allowed)}", "")

    return check


def _schema(value: object, where: str, found: _Found) -> None:
    if value != ENTRY_SCHEMA:
        found.add(where, f"schema is {ENTRY_SCHEMA!r}", "mark the entry with its schema")


def _id(value: object, where: str, found: _Found) -> None:
    if not isinstance(value, str) or not _ID.match(value):
        found.add(where, "entry_id is lower case letters, digits, dots, dashes", "e.g. ema")


def _version(value: object, where: str, found: _Found) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        found.add(where, "version is a whole number of at least 1", "start at 1")


def _texts(value: object, where: str, found: _Found) -> None:
    items = _list(value, where, found)
    for i, item in enumerate(items or []):
        _text(item, f"{where}/{i}", found)


def _pins(value: object, where: str, found: _Found) -> None:
    items = _list(value, where, found)
    for i, item in enumerate(items or []):
        if not isinstance(item, str) or not _PIN.match(item):
            found.add(f"{where}/{i}", "a link names an entry as <entry_id>@<version>", "")


def _roles(value: object, where: str, found: _Found) -> None:
    items = _list(value, where, found)
    for i, item in enumerate(items or []):
        problem = role_problem(item)
        if problem is not None:
            found.add(f"{where}/{i}", problem, "use a role from the roles table")


def _classes(value: object, where: str, found: _Found, check: _Check) -> None:
    if not _object(value, where, found):
        return
    allowed = [c.value for c in InstrumentClass]
    for name, item in cast("Mapping[str, object]", value).items():
        if name not in allowed:
            found.add(
                f"{where}/{name}", f"{name} is not a class; they are {', '.join(allowed)}", ""
            )
        else:
            check(item, f"{where}/{name}", found)


def _class_meanings(value: object, where: str, found: _Found) -> None:
    _classes(value, where, found, _text)


def _transfer(value: object, where: str, found: _Found) -> None:
    _classes(value, where, found, _enum(Transfer))


def _sources(value: object, where: str, found: _Found) -> None:
    items = _list(value, where, found)
    for i, item in enumerate(items or []):
        at = f"{where}/{i}"
        if not _object(item, at, found):
            continue
        source = cast("Mapping[str, object]", item)
        _text(source.get("source_ref"), f"{at}/source_ref", found)
        _text(source.get("quote"), f"{at}/quote", found)
        dated = source.get("dated")
        if not isinstance(dated, str) or not _DATE.match(dated):
            found.add(f"{at}/dated", "dated is the source's date as YYYY-MM-DD", "")


def _fallback(value: object, where: str, found: _Found) -> None:
    items = _list(value, where, found)
    for i, item in enumerate(items or []):
        at = f"{where}/{i}"
        if not _object(item, at, found):
            continue
        step = cast("Mapping[str, object]", item)
        if level_of(step.get("data_level")) is None:
            found.add(f"{at}/data_level", "a fallback names its data level, 0 to 6", "")
        loss = step.get("expected_loss")
        if not isinstance(loss, str) or not loss.strip():
            found.add(
                f"{at}/expected_loss",
                "a fallback has no expected-loss label",
                "say what the block loses on this level, in plain words",
            )


def _input(value: object, where: str, found: _Found) -> None:
    if not _object(value, where, found):
        return
    port = cast("Mapping[str, object]", value)
    _text(port.get("port"), f"{where}/port", found)
    _text(port.get("stream_kind"), f"{where}/stream_kind", found)
    measure = port.get("measure")
    if measure is not None and not isinstance(measure, str):
        found.add(f"{where}/measure", "measure is a measure name or null", "")
    if port.get("stream_kind") in HOST_FACTS:
        return
    level = level_of(port.get("data_level"))
    if level is None:
        found.add(
            f"{where}/data_level",
            "an input from market data has no data level",
            "declare the level it needs, 0 calendar to 6 outside data",
        )
        return
    if "splits" in port:
        for key, message in split_problems(level, port["splits"]):
            found.add(f"{where}/splits{'/' + key if key else ''}", message, "")
    if "fallback" in port:
        _fallback(port["fallback"], f"{where}/fallback", found)


def _inputs(value: object, where: str, found: _Found) -> None:
    items = _list(value, where, found)
    for i, item in enumerate(items or []):
        _input(item, f"{where}/{i}", found)


def _output(value: object, where: str, found: _Found) -> None:
    if not _object(value, where, found):
        return
    raw = cast("Mapping[str, object]", value)
    _enum(OutputType)(raw.get("type"), f"{where}/type", found)
    measure = raw.get("measure")
    if measure is not None and not isinstance(measure, str):
        found.add(f"{where}/measure", "measure is a measure name or null", "")


def _decimal(value: object) -> Decimal | None:
    if not isinstance(value, str) or not _DECIMAL.match(value):
        return None
    try:
        return Decimal(value)
    except InvalidOperation:
        return None


def _parameter(value: object, where: str, found: _Found) -> None:
    if not _object(value, where, found):
        return
    spec = cast("Mapping[str, object]", value)
    _enum(Measure)(spec.get("measure"), f"{where}/measure", found)
    if "kind" in spec:
        _enum(NumberKind)(spec["kind"], f"{where}/kind", found)
    if "origin" in spec:
        _enum(Origin)(spec["origin"], f"{where}/origin", found)
    if "default" in spec and not isinstance(spec["default"], str):
        found.add(f"{where}/default", "default is a decimal string or a word", "")
    raw_range = spec.get("range")
    if raw_range is None:
        return
    if not _object(raw_range, f"{where}/range", found):
        return
    bounds = cast("Mapping[str, object]", raw_range)
    low, high = _decimal(bounds.get("min")), _decimal(bounds.get("max"))
    if low is None or high is None or _decimal(bounds.get("step")) is None:
        found.add(f"{where}/range", "range is {min, max, step} as decimal strings", "")
        return
    default = _decimal(spec.get("default"))
    if default is not None and not low <= default <= high:
        found.add(f"{where}/default", f"default {default} is outside {low} to {high}", "")


def _parameters(value: object, where: str, found: _Found) -> None:
    if _object(value, where, found):
        for name, spec in cast("Mapping[str, object]", value).items():
            _parameter(spec, f"{where}/{name}", found)


def _warm_up(value: object, where: str, found: _Found) -> None:
    if not _object(value, where, found):
        return
    raw = cast("Mapping[str, object]", value)
    _text(raw.get("rule"), f"{where}/rule", found)
    bars = raw.get("bars")
    if bars is not None:
        _count(bars, f"{where}/bars", found)


def _fingerprint(value: object, where: str, found: _Found) -> None:
    if not isinstance(value, str) or not _FP.match(value):
        found.add(where, "fingerprint is fp1:sha256:<64 hex>", "the block fingerprint of its code")


def _golden(value: object, where: str, found: _Found) -> None:
    if _object(value, where, found):
        raw = cast("Mapping[str, object]", value)
        _text(raw.get("reference"), f"{where}/reference", found)
        _text(raw.get("cases"), f"{where}/cases", found)


def _settle(value: object, where: str, found: _Found) -> None:
    if _object(value, where, found):
        bars = cast("Mapping[str, object]", value).get("bars")
        if isinstance(bars, bool) or not isinstance(bars, int) or bars < 1:
            found.add(f"{where}/bars", "bars is a whole number of at least 1", "")


def _any_object(value: object, where: str, found: _Found) -> None:
    _object(value, where, found)


_FIELDS: Final[Mapping[str, _Check]] = {
    "schema": _schema,
    "entry_id": _id,
    "version": _version,
    "family": _text,
    "aliases": _texts,
    "same_word_as": _pins,
    "origin": _enum(EntryOrigin),
    "definition": _text,
    "boundaries": _text,
    "recognition": _text,
    "eligible_roles": _roles,
    "class_meanings": _class_meanings,
    "sources": _sources,
    "component_type": _enum(ComponentType),
    "inputs": _inputs,
    "output": _output,
    "parameters": _parameters,
    "warm_up": _warm_up,
    "confirmation_lag_bars": _count,
    "min_sample": _count,
    "expected_lag_bars": _count,
    "transfer": _transfer,
    "mirroring": _enum(Mirroring),
    "state_bound": _any_object,
    "reading": _any_object,
    "fingerprint": _fingerprint,
    "golden": _golden,
    "tests": _text,
    "settle_bars": _settle,
    "owner": _text,
}
_REQUIRED: Final = ("schema", "entry_id", "version", "component_type", "origin", "definition")


def alias_key(text: str) -> str:
    """The form two names are compared in: lower case, words split on anything not a letter or
    a digit. ``RSI cross-back`` and ``rsi-cross-back`` share one key."""
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


def _rules(raw: Mapping[str, object], found: _Found) -> None:
    sources = raw.get("sources")
    cited = isinstance(sources, list) and len(cast("list[object]", sources)) > 0
    transfer = raw.get("transfer")
    if isinstance(transfer, Mapping):
        for name, claim in cast("Mapping[str, object]", transfer).items():
            if claim in _TRANSFER_NEEDS_SOURCE and not cited:
                found.add(
                    f"/transfer/{name}",
                    f"{name} is claimed {claim} with no source",
                    "cite a source with its exact quote and date, or claim not_assessed",
                )
    golden = raw.get("golden")
    standard = isinstance(golden, Mapping) and bool(cast("Mapping[str, object]", golden))
    if not standard and not cited:
        found.add(
            "/sources",
            "an entry with no published reference cites no source",
            "cite a source with its exact quote and date",
        )
    if raw.get("origin") == EntryOrigin.PLACEHOLDER and not raw.get("owner"):
        found.add("/owner", "a placeholder names its owner", "the risk session owns sizers")
    aliases = raw.get("aliases")
    if isinstance(aliases, list):
        seen: dict[str, int] = {}
        for i, alias in enumerate(cast("list[object]", aliases)):
            if isinstance(alias, str):
                key = alias_key(alias)
                if key in seen:
                    found.add(f"/aliases/{i}", f"{alias!r} repeats alias {seen[key]}", "")
                seen.setdefault(key, i)


def check_entry(raw: Mapping[str, object]) -> tuple[EntryProblem, ...]:
    """Every problem of one entry, in field order: a field of the wrong shape, a word outside
    the vocabulary, a claim with no evidence. An entry that lacks a field every entry names is
    one problem listing them, and its claims are checked once those are written. An empty
    answer lets the entry save."""
    found = _Found()
    lacking = [name for name in _REQUIRED if raw.get(name) is None]
    if lacking:
        found.add("", f"the entry has no {', '.join(lacking)}", "every entry names these")
    for name, value in raw.items():
        check = _FIELDS.get(name)
        if check is None:
            found.add(f"/{name}", f"{name} is not a field of {ENTRY_SCHEMA}", "remove it")
        elif value is not None:
            check(value, f"/{name}", found)
    if not lacking:
        _rules(raw, found)
    return tuple(found.problems)


def corpus_problems(entries: Sequence[Mapping[str, object]]) -> tuple[EntryProblem, ...]:
    """Problems only the whole catalogue shows: a name that is another entry's id or alias, and
    one pin holding two different entries. Each ``where`` starts with the pin."""
    owner: dict[str, str] = {}
    held: dict[str, Mapping[str, object]] = {}
    found = _Found()
    for raw in entries:
        entry_id, pin = str(raw.get("entry_id")), f"{raw.get('entry_id')}@{raw.get('version')}"
        before = held.setdefault(pin, raw)
        if before is not raw and before != raw:
            found.add(f"{pin}", f"{pin} is held by two different entries", "give one a new version")
        aliases = raw.get("aliases")
        names = [(f"{pin}/entry_id", entry_id)] + [
            (f"{pin}/aliases/{i}", a)
            for i, a in enumerate(
                cast("list[object]", aliases) if isinstance(aliases, list) else []
            )
            if isinstance(a, str)
        ]
        for where, name in names:
            key = alias_key(name)
            first = owner.setdefault(key, entry_id)
            if first != entry_id:
                found.add(where, f"{name!r} already names {first}", "pick a name no entry uses")
    return tuple(found.problems)


@dataclass(frozen=True, slots=True)
class Computed:
    """An entry's status, every problem found on the way, and what the next rung lacks.
    ``status`` is None when the entry does not pass the checker."""

    status: Status | None
    problems: tuple[EntryProblem, ...]
    missing: tuple[str, ...]
    evidence: str

    def annotation(self) -> dict[str, str]:
        """The ``status`` annotation the status script writes."""
        return {
            "value": "refused" if self.status is None else self.status.value,
            "evidence": self.evidence,
            "checker": CHECKER_VERSION,
        }


def _defaults(raw: Mapping[str, object]) -> dict[str, Decimal]:
    parameters = raw.get("parameters")
    found: dict[str, Decimal] = {}
    if isinstance(parameters, Mapping):
        for name, spec in cast("Mapping[str, object]", parameters).items():
            default = (
                _decimal(cast("Mapping[str, object]", spec).get("default"))
                if isinstance(spec, Mapping)
                else None
            )
            if default is not None:
                found[name] = default
    return found


def _series_port(raw: Mapping[str, object]) -> str | None:
    inputs = raw.get("inputs")
    for port in cast("list[object]", inputs) if isinstance(inputs, list) else []:
        if isinstance(port, Mapping):
            given = cast("Mapping[str, object]", port)
            if given.get("stream_kind") == "series" and isinstance(given.get("port"), str):
                return str(given["port"])
    return None


def _value(output: object) -> Decimal | None:
    if isinstance(output, Signal):
        return output.value
    if output is None or isinstance(output, Decimal):
        return output
    raise TypeError(f"a golden case compares series values, and the block returned {output!r}")


def _close(ours: Decimal | None, theirs: Decimal | None) -> bool:
    if ours is None or theirs is None:
        return ours is None and theirs is None
    return abs(ours - theirs) <= max(GOLDEN_ABSOLUTE, GOLDEN_RELATIVE * abs(theirs))


def _cases(golden: Mapping[str, object], pin: str) -> Iterator[tuple[str, dict[str, Decimal]]]:
    cases = golden.get("cases")
    for name in sorted(cast("Mapping[str, object]", cases) if isinstance(cases, Mapping) else {}):
        words = name.split()
        if words and words[0] == pin:
            params = dict(w.split("=", 1) for w in words[1:] if "=" in w)
            yield name, {k: Decimal(v) for k, v in params.items()}


def _golden_problems(
    raw: Mapping[str, object], make: Callable[[Mapping[str, Decimal]], Instance], golden: object
) -> list[EntryProblem]:
    pin = f"{raw.get('entry_id')}@{raw.get('version')}"
    if not isinstance(golden, Mapping):
        return [EntryProblem("/golden/cases", "the golden cases are not an object", "")]
    table = cast("Mapping[str, object]", golden)
    closes = [Decimal(str(c)) for c in cast("list[object]", table.get("close") or [])]
    port = _series_port(raw)
    named = list(_cases(table, pin))
    if port is None or not closes or not named:
        return [EntryProblem("/golden/cases", f"the golden cases hold no run of {pin}", "")]
    problems: list[EntryProblem] = []
    for name, params in named:
        expected = [
            None if v is None else Decimal(str(v))
            for v in cast("list[object]", cast("Mapping[str, object]", table["cases"])[name])
        ]

        def run(series: Sequence[Decimal], params: Mapping[str, Decimal] = params) -> list[object]:
            instance = make({**_defaults(raw), **params})
            return [_value(instance.update({port: x})) for x in series]

        try:
            full = cast("list[Decimal | None]", run(closes))
            misses = [
                i for i, (a, b) in enumerate(zip(full, expected, strict=True)) if not _close(a, b)
            ]
            cuts = [len(closes) * k // (CUT_SAMPLES + 1) for k in range(1, CUT_SAMPLES + 1)]
            unequal = [c for c in cuts if run(closes[: c + 1])[-1] != full[c]]
        except (KeyError, TypeError, ValueError, ArithmeticError) as error:
            problems.append(EntryProblem("/golden", f"{name} does not run: {error}", ""))
            continue
        if misses:
            problems.append(
                EntryProblem(
                    "/golden",
                    f"{name} differs from its golden values at {len(misses)} bars, "
                    f"first {misses[0]}",
                    "a missing warm-up value is None, never zero",
                )
            )
        if unequal:
            problems.append(
                EntryProblem(
                    "/golden",
                    f"{name} at bar {unequal[0]} differs between data cut there and "
                    "the full series",
                    "a block reads only the evidence up to now",
                )
            )
    return problems


def _implementation(
    raw: Mapping[str, object], source: bytes, golden: object
) -> tuple[list[EntryProblem], list[str]]:
    pin = f"{raw.get('entry_id')}@{raw.get('version')}"
    stated = raw.get("fingerprint")
    if not isinstance(stated, str):
        return [], ["implementation: fingerprint"]
    try:
        actual = block_fingerprint(source).value
    except UnicodeDecodeError:
        return [EntryProblem("/code", f"{pin}'s code is not UTF-8 text", "")], []
    if actual != stated:
        return [
            EntryProblem(
                "/fingerprint",
                f"the code has fingerprint {actual}, the entry states {stated}",
                "state the fingerprint of the code you saved",
            )
        ], []
    scan = check_block(pin, str(raw.get("origin")), source, "/code")
    problems = [EntryProblem("/code", p.message, p.hint) for p in scan.errors]
    if problems:
        return problems, []
    loaded = load(
        [LockEntry(str(raw.get("entry_id")), cast("int", raw.get("version")), actual)],
        {pin: source},
    )
    if isinstance(loaded, tuple):
        return [EntryProblem("/code", p.message, p.hint) for p in loaded], []
    block = loaded.blocks[pin]
    declared = raw.get("golden")
    if not isinstance(declared, Mapping):
        return [], []
    if golden is None:
        return [], ["implementation: the golden cases its entry names"]
    return _golden_problems(raw, lambda params: block.make(params, {}), golden), []


def compute_status(
    raw: Mapping[str, object], source: bytes | None = None, golden: object = None
) -> Computed:
    """The status ``raw`` has earned: its own checks, then its machine face, then its code
    (``source``, the bytes of ``block.py``) against its fingerprint, layer F's scan, the loader
    and, when the entry names golden cases, those cases (``golden``, the decoded cases file) and
    the cut-against-full check over them."""
    problems = list(check_entry(raw))
    evidence = fingerprint(
        {
            "entry": raw,
            "source": None if source is None else block_fingerprint(source).value,
            "golden": golden,
            "checker": CHECKER_VERSION,
        }
    )
    proof = "unfingerprintable" if is_refusal(evidence) else evidence.value.value
    if problems:
        return Computed(None, tuple(problems), (), proof)
    gaps = [f"machine face: {name}" for name in _SPECIFIED if raw.get(name) is None]
    parameters = raw.get("parameters")
    for name, spec in (
        cast("Mapping[str, object]", parameters).items() if isinstance(parameters, Mapping) else ()
    ):
        given = cast("Mapping[str, object]", spec)
        gaps += [
            f"machine face: parameters/{name}/{k}" for k in ("default", "origin") if k not in given
        ]
    if gaps:
        return Computed(Status.NAMED, (), tuple(gaps), proof)
    if source is None:
        return Computed(Status.SPECIFIED, (), ("implementation: code",), proof)
    found, missing = _implementation(raw, source, golden)
    if found or missing:
        return Computed(Status.SPECIFIED, tuple(found), tuple(missing), proof)
    return Computed(Status.IMPLEMENTED, (), (), proof)
