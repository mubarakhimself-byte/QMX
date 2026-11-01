"""The run record: the run id the core mints, the ticket `open` returns, and the tester's bundle.

The core issues every run id (Level 0 AD-25). A tester echoes it in its `qmx.qmb.result-bundle/1`
and never stamps a run `killed`: only the core does that, through the lander's `fail`.
"""

from __future__ import annotations

import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, NewType, cast

__all__ = [
    "BundleFile",
    "BundleRefused",
    "Landing",
    "ResultBundle",
    "RunId",
    "RunStatus",
    "Ticket",
    "mint_run_id",
    "new_ulid",
    "parse_bundle",
]

RunId = NewType("RunId", str)
"""`qmbr-<machine>-<ulid>`, minted by the core and echoed by the tester."""

type RunStatus = Literal["finished", "failed", "killed"]
type BundleStatus = Literal["finished", "failed"]

CROCKFORD: Final = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"


def new_ulid() -> str:
    """A ULID in its 26-character Crockford form, from a UUIDv7.

    Both lay out 48 bits of Unix milliseconds ahead of random bits, so the text sorts by time.
    """
    value = uuid.uuid7().int
    return "".join(CROCKFORD[(value >> shift) & 31] for shift in range(125, -1, -5))


def mint_run_id(machine: str, ulid: str) -> RunId:
    return RunId(f"qmbr-{machine}-{ulid}")


@dataclass(frozen=True, slots=True)
class Ticket:
    """What `open` hands the supervisor: the run id and what `close` and `fail` land against."""

    run_id: RunId
    app_id: str
    version: str
    job: str
    principal: str
    unit: str
    study: str | None
    family: str
    opened: str
    """The object id of the `opened` try."""
    request: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class BundleFile:
    slot: str
    path: str
    fp: str


@dataclass(frozen=True, slots=True)
class ResultBundle:
    """The tester's `qmx.qmb.result-bundle/1`, parsed once at the lander's door."""

    run_id: str
    status: BundleStatus
    tester: Mapping[str, object]
    reason: str | None = None
    request_fp: str | None = None
    measures: Mapping[str, object] | None = None
    labels: Mapping[str, object] | None = None
    files: tuple[BundleFile, ...] = ()
    consumed: tuple[str, ...] = ()
    versions: Mapping[str, object] | None = None


@dataclass(frozen=True, slots=True)
class Landing:
    """One finished job, as `close` receives it: its ticket, its bundle and where its files are."""

    ticket: Ticket
    bundle: ResultBundle
    output_dir: Path


class BundleRefused(ValueError):
    """A bundle or a landing the lander will not take. The first problem is the message head;
    `problems` holds every one."""

    def __init__(self, problems: list[str]) -> None:
        super().__init__(problems[0])
        self.problems = tuple(problems)


def _mapping(raw: Mapping[str, object], name: str, problems: list[str]) -> Mapping[str, object]:
    value = raw.get(name)
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        problems.append(f"{name} is an object")
        return {}
    return cast(Mapping[str, object], value)


def _texts(raw: Mapping[str, object], name: str, problems: list[str]) -> tuple[str, ...]:
    value = raw.get(name, [])
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in cast(list[object], value)
    ):
        problems.append(f"{name} is a list of pins")
        return ()
    return tuple(cast(list[str], value))


def _files(raw: Mapping[str, object], problems: list[str]) -> tuple[BundleFile, ...]:
    value = raw.get("files", [])
    if not isinstance(value, list):
        problems.append("files is a list")
        return ()
    found: list[BundleFile] = []
    for index, entry in enumerate(cast(list[object], value)):
        if not isinstance(entry, Mapping):
            problems.append(f"files[{index}] is an object")
            continue
        named = cast(Mapping[str, object], entry)
        slot, path, fp = named.get("slot"), named.get("path"), named.get("fp")
        if not (isinstance(slot, str) and isinstance(path, str) and isinstance(fp, str)):
            problems.append(f"files[{index}] names its slot, path and fp")
            continue
        found.append(BundleFile(slot, path, fp))
    return tuple(found)


def parse_bundle(raw: Mapping[str, object]) -> ResultBundle:
    """Read a tester's bundle, refusing with every problem at once."""
    problems: list[str] = []
    run_id, status, reason = raw.get("run_id"), raw.get("status"), raw.get("reason")
    if not isinstance(run_id, str) or not run_id:
        problems.append("run_id is the run id the core minted")
    if status not in ("finished", "failed"):
        problems.append("status is finished or failed; only the core stamps killed")
    if reason is not None and not isinstance(reason, str):
        problems.append("reason is text")
    request_fp = raw.get("request_fp")
    if request_fp is not None and not isinstance(request_fp, str):
        problems.append("request_fp is text")
    tester = _mapping(raw, "tester", problems)
    measures = _mapping(raw, "measures", problems)
    labels = _mapping(raw, "labels", problems)
    versions = _mapping(raw, "versions", problems)
    files = _files(raw, problems)
    consumed = _texts(raw, "consumed", problems)
    if problems:
        raise BundleRefused(problems)
    return ResultBundle(
        run_id=cast(str, run_id),
        status=cast(BundleStatus, status),
        tester=tester,
        reason=cast(str | None, reason),
        request_fp=cast(str | None, request_fp),
        measures=measures or None,
        labels=labels or None,
        files=files,
        consumed=consumed,
        versions=versions or None,
    )
