"""The one block loader (AD-109, Level 0 AD-47).

``load(lock, sources, weights)`` is the only code in QMX that turns block source into
callables. For each pin it takes the bytes the host gathered (QML reads no file), normalises
line endings to LF, computes the block fingerprint (fp1 over ``{"block.py": text}``),
compares it with the pin, and only then compiles the text as ``qmlblock:<entry>@<version>``
into a fresh namespace and requires it to export ``BLOCK`` meeting ``qml.blocks.api.Block``.
Every problem of every pin comes back at once.

The checker's scan bans ``importlib``, ``__import__``, ``eval`` and ``exec`` in blocks an
agent wrote; this module is the one place allowed to compile and run block source, and it
runs only source whose fingerprint matched its pin.
"""

from __future__ import annotations

import builtins
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from qmf.core.fingerprint import Fingerprint, fingerprint, fingerprint_bytes
from qmf.core.refusal import is_refusal

from qml.blocks.api import Block

__all__ = [
    "LoadProblem",
    "LoadProblemKind",
    "Loaded",
    "LockEntry",
    "block_fingerprint",
    "load",
    "lock_fingerprint",
]


class LoadProblemKind(StrEnum):
    BLOCK_MISSING = "block_missing"
    BLOCK_FINGERPRINT_MISMATCH = "block_fingerprint_mismatch"
    BLOCK_COMPILE_ERROR = "block_compile_error"
    BLOCK_PROTOCOL = "block_protocol"
    WEIGHTS_MISSING = "weights_missing"
    WEIGHTS_FINGERPRINT_MISMATCH = "weights_fingerprint_mismatch"


@dataclass(frozen=True, slots=True)
class LockEntry:
    """One pin of a lock: a block at one version, its fingerprint, and its weights' if learned."""

    entry_id: str
    version: int
    fingerprint: str
    weights: str | None = None

    @property
    def pin(self) -> str:
        return f"{self.entry_id}@{self.version}"


@dataclass(frozen=True, slots=True)
class LoadProblem:
    kind: LoadProblemKind
    pin: str
    message: str
    hint: str


@dataclass(frozen=True, slots=True)
class Loaded:
    blocks: Mapping[str, Block]
    weights: Mapping[str, bytes]
    lock_fingerprint: Fingerprint


def _lf_text(source: bytes) -> str:
    return source.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def block_fingerprint(source: bytes) -> Fingerprint:
    """fp1 over ``{"block.py": LF-normalised UTF-8 text}``; CRLF and LF copies agree."""
    result = fingerprint({"block.py": _lf_text(source)})
    if is_refusal(result):  # a str mapping always serialises; kept for the type
        raise ValueError(str(result.category))
    return result.value


def lock_fingerprint(lock: Sequence[LockEntry]) -> Fingerprint:
    """fp1 over the sorted pins; it enters the compiled unit's fingerprint."""
    rows: list[dict[str, object]] = []
    for entry in sorted(lock, key=lambda e: (e.entry_id, e.version)):
        row: dict[str, object] = {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "fingerprint": entry.fingerprint,
        }
        if entry.weights is not None:
            row["weights"] = entry.weights
        rows.append(row)
    result = fingerprint(rows)
    if is_refusal(result):
        raise ValueError(str(result.category))
    return result.value


def _compile(entry: LockEntry, text: str) -> Block | LoadProblem:
    name = f"qmlblock:{entry.pin}"
    namespace: dict[str, object] = {"__name__": name, "__builtins__": builtins}
    try:
        code = compile(text, name, "exec", dont_inherit=True)
        exec(code, namespace)  # noqa: S102 - the one sanctioned loader (AD-109)
    except Exception as error:
        return LoadProblem(
            LoadProblemKind.BLOCK_COMPILE_ERROR,
            entry.pin,
            f"{entry.pin} does not compile or run: {type(error).__name__}: {error}",
            "fix the block source and pin its new fingerprint as a successor version",
        )
    block = namespace.get("BLOCK")
    if block is None or not isinstance(block, Block):
        return LoadProblem(
            LoadProblemKind.BLOCK_PROTOCOL,
            entry.pin,
            f"{entry.pin} exports no BLOCK with make(params, inputs, side)",
            "export BLOCK, an object whose make returns an instance (qml.blocks.api)",
        )
    return block


def _load_one(entry: LockEntry, source: bytes | None) -> Block | LoadProblem:
    if source is None:
        return LoadProblem(
            LoadProblemKind.BLOCK_MISSING,
            entry.pin,
            f"no source was given for {entry.pin}",
            "gather block.py for every pin in the lock",
        )
    try:
        found = block_fingerprint(source)
    except UnicodeDecodeError as error:
        return LoadProblem(
            LoadProblemKind.BLOCK_COMPILE_ERROR,
            entry.pin,
            f"{entry.pin} is not UTF-8 text: {error}",
            "store block source as UTF-8",
        )
    if found.value != entry.fingerprint:
        return LoadProblem(
            LoadProblemKind.BLOCK_FINGERPRINT_MISMATCH,
            entry.pin,
            f"{entry.pin} source has fingerprint {found.value}, the lock pins {entry.fingerprint}",
            "load the source the lock pinned, or pin the new source as a successor version",
        )
    return _compile(entry, _lf_text(source))


def _weights_problem(entry: LockEntry, weights: Mapping[str, bytes]) -> LoadProblem | None:
    if entry.weights is None:
        return None
    data = weights.get(entry.pin)
    if data is None:
        return LoadProblem(
            LoadProblemKind.WEIGHTS_MISSING,
            entry.pin,
            f"{entry.pin} pins weights {entry.weights} and none were given",
            "gather the pinned weights file beside the block",
        )
    found = fingerprint_bytes(data).value
    if found != entry.weights:
        return LoadProblem(
            LoadProblemKind.WEIGHTS_FINGERPRINT_MISMATCH,
            entry.pin,
            f"{entry.pin} weights have fingerprint {found}, the lock pins {entry.weights}",
            "load the weights the lock pinned",
        )
    return None


def load(
    lock: Sequence[LockEntry],
    sources: Mapping[str, bytes],
    weights: Mapping[str, bytes] | None = None,
) -> Loaded | tuple[LoadProblem, ...]:
    """Every pinned block as a callable ``BLOCK``, or every problem found across the lock."""
    given: Mapping[str, bytes] = weights if weights is not None else {}
    blocks: dict[str, Block] = {}
    loaded_weights: dict[str, bytes] = {}
    problems: list[LoadProblem] = []
    for entry in lock:
        outcome = _load_one(entry, sources.get(entry.pin))
        if isinstance(outcome, LoadProblem):
            problems.append(outcome)
        else:
            blocks[entry.pin] = outcome
        weights_problem = _weights_problem(entry, given)
        if weights_problem is not None:
            problems.append(weights_problem)
        elif entry.weights is not None:
            loaded_weights[entry.pin] = given[entry.pin]
    if problems:
        return tuple(problems)
    return Loaded(
        blocks=MappingProxyType(blocks),
        weights=MappingProxyType(loaded_weights),
        lock_fingerprint=lock_fingerprint(lock),
    )
