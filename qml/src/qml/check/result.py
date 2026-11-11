"""The check result ``qmx.check/1`` (CONTRACTS.md 3.1): counts first, then every problem.

Identical problems are grouped into one with all their pointers, so a spilled answer still
shows the counts and the first errors in its head (AG-15). ``problem_set`` fingerprints the
sorted problem list, and a caller that passes the previous one learns ``no_progress`` when
nothing changed (AG-11).
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from qmf.core.fingerprint import fingerprint, fingerprint_bytes
from qmf.core.refusal import is_refusal

from qml.conformance.scan import ast_scan_rules_identity
from qml.numbers.records import InstrumentRecord
from qml.unit.parse import Problem, ProblemKind

__all__ = [
    "AGENT_BANNED_ATTRIBUTES",
    "AGENT_BANNED_NAMES",
    "AGENT_DUNDER_ASSIGNS",
    "AGENT_IMPORTS",
    "CHECKER_FORMAT_VERSION",
    "CHECK_SCHEMA",
    "LAYERS",
    "CheckResult",
    "Verdict",
    "checker_version",
    "entries_snapshot",
    "group",
    "problem_set",
    "records_snapshot",
]

CHECK_SCHEMA: Final[str] = "qmx.check/1"
CHECKER_FORMAT_VERSION: Final[int] = 3
"""Bumped by any change that makes a document pass or fail differently."""
LAYERS: Final[tuple[str, ...]] = ("A", "B", "C", "D", "E", "F")
AGENT_IMPORTS: Final[frozenset[str]] = frozenset(
    {
        "__future__",
        "bisect",
        "collections",
        "collections.abc",
        "decimal",
        "fractions",
        "math",
        "qmf.core.refusal",
        "qml.blocks.api",
        "qml.numbers",
    }
)
"""The only modules an agent-written block may import: those QML's stdlib blocks use."""
AGENT_BANNED_NAMES: Final[frozenset[str]] = frozenset(
    {
        "breakpoint",
        "builtins",
        "compile",
        "delattr",
        "eval",
        "exec",
        "getattr",
        "globals",
        "importlib",
        "input",
        "locals",
        "open",
        "setattr",
        "sys",
        "vars",
    }
)
"""Names an agent-written block may not use, besides every dunder name."""
AGENT_BANNED_ATTRIBUTES: Final[frozenset[str]] = frozenset(
    {
        "ag_frame",
        "cr_frame",
        "eval",
        "exec",
        "f_back",
        "f_builtins",
        "f_globals",
        "f_locals",
        "gi_frame",
        "import_module",
        "tb_frame",
    }
)
"""Attributes an agent-written block may not read, besides every dunder attribute.

The frame attributes reach a module's globals, and so its builtins, without a dunder."""
AGENT_DUNDER_ASSIGNS: Final[frozenset[str]] = frozenset({"__slots__"})
"""The dunder names an agent-written block may assign, as QML's stdlib blocks do."""


class Verdict(StrEnum):
    PASS = "pass"  # noqa: S105 - a verdict word, not a secret
    FAIL = "fail"


def _fp(value: object) -> str:
    made = fingerprint(value)
    if is_refusal(made):  # pragma: no cover - only text, lists and integers go in
        raise ValueError(str(made.context))
    return made.value.value


def checker_version() -> str:
    """``qml-check/<format>`` and the fingerprint of the rules it applies."""
    rules = {
        "format": CHECKER_FORMAT_VERSION,
        "layers": list(LAYERS),
        "kinds": sorted(kind.value for kind in ProblemKind),
        "scan": ast_scan_rules_identity(),
        "agent_imports": sorted(AGENT_IMPORTS),
        "agent_banned_names": sorted(AGENT_BANNED_NAMES),
        "agent_banned_attributes": sorted(AGENT_BANNED_ATTRIBUTES),
        "agent_dunder_assigns": sorted(AGENT_DUNDER_ASSIGNS),
    }
    return f"qml-check/{CHECKER_FORMAT_VERSION} {_fp(rules)}"


def entries_snapshot(entries: Mapping[str, bytes], sources: Mapping[str, bytes]) -> str:
    rows = {
        pin: {
            key: fingerprint_bytes(given[pin]).value
            for key, given in (("entry", entries), ("block", sources))
            if pin in given
        }
        for pin in sorted(set(entries) | set(sources))
    }
    return _fp(rows)


def records_snapshot(records: Mapping[str, InstrumentRecord]) -> str:
    return _fp({market: records[market].name for market in sorted(records)})


def group(problems: Iterable[Problem]) -> tuple[Problem, ...]:
    """One problem per (layer, kind, message, hint), holding every pointer, in first-seen order."""
    grouped: dict[tuple[str, str, str, str], Problem] = {}
    for p in problems:
        key = (p.layer, p.kind.value, p.message, p.hint)
        seen = grouped.get(key)
        if seen is None:
            grouped[key] = p
        else:
            where = seen.where + tuple(w for w in p.where if w not in seen.where)
            nearest = seen.nearest + tuple(n for n in p.nearest if n not in seen.nearest)
            grouped[key] = Problem(p.kind, where, p.message, p.hint, p.layer, nearest)
    return tuple(grouped.values())


def problem_set(errors: Sequence[Problem], warnings: Sequence[Problem]) -> str:
    rows = sorted([p.layer, p.kind.value, list(p.where), p.message] for p in (*errors, *warnings))
    return _fp(rows)


def _problem_json(p: Problem) -> dict[str, object]:
    out: dict[str, object] = {
        "kind": p.kind.value,
        "layer": p.layer,
        "where": list(p.where),
        "message": p.message,
        "hint": p.hint,
    }
    if p.nearest:
        out["nearest"] = list(p.nearest)
    return out


@dataclass(frozen=True)
class CheckResult:
    verdict: Verdict
    errors: tuple[Problem, ...]
    warnings: tuple[Problem, ...]
    layers_run: tuple[str, ...]
    document_fingerprint: str | None
    checker_version: str
    entries_snapshot: str
    records_snapshot: str
    problem_set: str
    no_progress: bool
    compiled_fingerprint: str | None = None

    def to_json(self) -> dict[str, object]:
        """The wire form, keys in the contract's order so the counts lead."""
        out: dict[str, object] = {
            "schema": CHECK_SCHEMA,
            "verdict": self.verdict.value,
            "counts": {"errors": len(self.errors), "warnings": len(self.warnings)},
            "errors": [_problem_json(p) for p in self.errors],
            "warnings": [_problem_json(p) for p in self.warnings],
            "layers_run": list(self.layers_run),
            "document_fingerprint": self.document_fingerprint,
        }
        if self.compiled_fingerprint is not None:
            out["compiled_fingerprint"] = self.compiled_fingerprint
        out |= {
            "checker_version": self.checker_version,
            "entries_snapshot": self.entries_snapshot,
            "records_snapshot": self.records_snapshot,
            "problem_set": self.problem_set,
            "no_progress": self.no_progress,
        }
        return out

    def text(self) -> str:
        """The result as compact JSON, the form a hook or a row returns."""
        return json.dumps(self.to_json(), ensure_ascii=False, separators=(",", ":"))
