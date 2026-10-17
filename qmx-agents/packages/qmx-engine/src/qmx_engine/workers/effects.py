"""Effects classed by reversibility (AD-8, SOLUTION-DESIGN 3.4).

A `reversible` attempt gets a snapshot of the run's write zone first. Before the next attempt of
the same slot, the paths the failed attempt changed are put back as they were. Only paths still
holding what that attempt left are touched, so a later attempt's writes to the same path survive.
A write another attempt made while this one ran cannot be told apart from this one's, and is
undone with it.

An `irreversible` attempt receives its idempotency key. After an `unknown` outcome (the engine
died mid-attempt, a timeout or a cancel), `after_unknown` says what happens next: a step that
touched nothing outside the zone reruns, a model call retries once, and any other step never
retries: it waits on a gate that shows its key until someone answers it.
"""

from __future__ import annotations

import json
import shutil
from hashlib import sha256
from pathlib import Path
from typing import Final, Literal

from pydantic import JsonValue

from qmx_engine.definition.registry import REGISTRY, Effect
from qmx_engine.nodes.base import NodeJob

SNAPSHOTS: Final = ".snap"
IRREVERSIBLE: Final = frozenset({"irreversible", "irreversible_external"})

type AfterUnknown = Literal["retry", "inbox"]


def effect_of(definition: dict[str, JsonValue]) -> Effect:
    declared = definition.get("effect")
    if declared in ("none", "reversible", "compensable", "irreversible", "irreversible_external"):
        return declared
    kind = REGISTRY.kind(str(definition.get("type")))
    return "none" if kind is None else kind.effect


def model_bearing(definition: dict[str, JsonValue]) -> bool:
    kind = REGISTRY.kind(str(definition.get("type")))
    return kind is not None and kind.model_bearing


def idempotency_key(job: NodeJob) -> str | None:
    """The key an irreversible attempt passes to the outside world; None for any other effect."""
    return job.idempotency_key if effect_of(job.node_definition) in IRREVERSIBLE else None


def after_unknown(definition: dict[str, JsonValue], earlier_unknowns: int) -> AfterUnknown:
    """`earlier_unknowns` counts this slot's attempts that already ended `unknown`."""
    effect = effect_of(definition)
    if effect in ("none", "reversible"):
        return "retry"
    if model_bearing(definition) and earlier_unknowns == 0:
        return "retry"
    return "inbox"


def _files(zone: Path) -> dict[str, str]:
    """Every file under the zone, outside the snapshots, to its sha256."""
    found: dict[str, str] = {}
    for folder, children, names in zone.walk():
        if folder == zone and SNAPSHOTS in children:
            children.remove(SNAPSHOTS)
        for name in names:
            path = folder / name
            found[path.relative_to(zone).as_posix()] = sha256(path.read_bytes()).hexdigest()
    return found


def _folder(zone: Path, job: NodeJob, attempt: int) -> Path:
    partition = "-" if job.partition is None else str(job.partition)
    return zone / SNAPSHOTS / f"{job.node_id}.{job.iteration}.{partition}" / str(attempt)


def before(zone: Path, job: NodeJob) -> None:
    """Undo the previous failed attempt of this slot, then snapshot the zone for this one."""
    if job.attempt > 1:
        restore(zone, _folder(zone, job, job.attempt - 1))
    folder = _folder(zone, job, job.attempt)
    shutil.rmtree(folder, ignore_errors=True)
    files = _files(zone)
    for relative in files:
        copy = folder / "files" / relative
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(zone / relative, copy)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "before.json").write_text(json.dumps(files), encoding="utf-8")


def after(zone: Path, job: NodeJob, *, ok: bool) -> None:
    folder = _folder(zone, job, job.attempt)
    record = {"ok": ok, "files": _files(zone)}
    (folder / "after.json").write_text(json.dumps(record), encoding="utf-8")


def restore(zone: Path, folder: Path) -> None:
    """Put back every path the snapshotted attempt changed. No `after.json` means the engine died
    mid-attempt, so the zone as it is now is what the attempt left."""
    if not (folder / "before.json").is_file():
        return
    then: dict[str, str] = json.loads((folder / "before.json").read_text(encoding="utf-8"))
    now = _files(zone)
    left = now
    if (folder / "after.json").is_file():
        record = json.loads((folder / "after.json").read_text(encoding="utf-8"))
        if record["ok"]:
            return
        left = record["files"]
    for relative in then.keys() | left.keys():
        if then.get(relative) == left.get(relative) or now.get(relative) != left.get(relative):
            continue
        target = zone / relative
        if relative in then:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(folder / "files" / relative, target)
        else:
            target.unlink()
