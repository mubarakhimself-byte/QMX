"""Attempt overlays and staged commits (AD-51, AD-24 zones, AD-49 retention).

A run's zone is `<zones_root>/<run_id>`, in the QMX folder's `cache/zones/` and outside its home
`data/` (design 62 A3):

- `code/` is a read-only copy of the workflow folder, hashed into `code.json`; a script runs
  from it only while its hash still matches.
- `work/` is the run's shared zone. Every attempt reads it and only a commit writes it.
- `attempts/<node>.<iteration>.<partition>.<attempt>/` is one attempt's overlay: its cwd and its
  only writable place. It is deleted when the attempt ends, committed or not.

When an attempt ends `ok`, only the files its node declares in `outputs.files` (and the artifacts
it returned) leave the overlay. They are staged under `work/.staging/<attempt>/`, `plan.json`
marks the stage complete, then each file is renamed into place, and the caller records
`zone_committed` and drops the stage. Every step is idempotent per path, so `recover` rolls a
complete stage forward after a crash and deletes an incomplete one. A declared path that
changed in `work/` after the attempt opened can only come from a definition the validator should
have refused, so the commit fails `zone_conflict` and overwrites nothing.

A commit runs without awaiting, on the event loop that also writes the ledger, so two commits of
one run never interleave.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
from collections.abc import Collection, Iterable, Iterator, Sequence
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path, PurePosixPath
from typing import Final, cast

from pydantic import JsonValue
from qmx_home import Layout

from qmx_engine.definition.model import OutputFile
from qmx_engine.definition.validate import STAGING, leaves_work
from qmx_engine.nodes.base import NodeJob

ZONES: Final = "zones"
"""The run zones' folder in the QMX folder's `cache/`, which may be deleted with QMX closed."""
PLAN: Final = "plan.json"
CODE_MANIFEST: Final = "code.json"
PARTITION: Final = "<partition>"

type JsonObject = dict[str, JsonValue]
type Seen = dict[str, tuple[int, int]]
"""A file under `work/` to its size and modification time, when the attempt opened."""


class ZoneError(Exception):
    """Ends the attempt failed and not retryable: `zone_conflict`, `zone_link`, `zone_merge`
    or `zone_path`."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass(frozen=True, slots=True)
class Commit:
    keys: JsonObject
    """The attempt's slot keys, so a rolled-forward commit is recorded on the right attempt."""
    sha256: dict[str, str]
    deleted: list[str]
    stage: Path

    def data(self) -> JsonObject:
        paths: list[JsonValue] = [*sorted(self.sha256)]
        hashes: dict[str, JsonValue] = dict(sorted(self.sha256.items()))
        deleted: list[JsonValue] = [*self.deleted]
        return {**self.keys, "paths": paths, "sha256": hashes, "deleted": deleted}


@dataclass(frozen=True, slots=True)
class Overlay:
    path: Path
    seen: Seen = field(default_factory=dict[str, tuple[int, int]])


def zones_root(home: Path) -> Path:
    """`<QMX>/cache/zones` for the home `<QMX>/data`: beside the home, so a stray relative path
    never lands in a store, and inside the folder, so each folder keeps its own zones."""
    home = home.resolve()
    root = Layout.from_home(home).cache / ZONES
    if root == home or root.is_relative_to(home) or home.is_relative_to(root):
        raise ValueError(f"the zones root {root} is the home, inside it or above it")
    return root


def home_of(shared: Path) -> Path:
    """The home whose run owns this `work/` folder (`QMX_WORK_SHARED`): the `data/` of the QMX
    folder whose `cache/zones/<run>/work` it is. The templates that read the engine's own ledger
    use it until a `library` node serves them `engine_view`."""
    return Layout(shared.resolve().parents[3]).home


def slot_name(job: NodeJob) -> str:
    partition = "-" if job.partition is None else str(job.partition)
    return f"{job.node_id}.{job.iteration}.{partition}.{job.attempt}"


def digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _writable(function: object, path: str, _: object) -> None:
    os.chmod(path, stat.S_IWRITE)
    os.unlink(path)


def remove(path: Path) -> None:
    shutil.rmtree(path, onexc=_writable)


def files_under(folder: Path) -> Iterator[tuple[str, Path]]:
    """Every file under the folder as its posix path relative to it. A junction or symlink
    raises `zone_link` instead of being followed (L-40)."""
    for current, children, names in folder.walk():
        for name in [*children, *names]:
            entry = current / name
            if entry.is_symlink() or entry.is_junction():
                raise ZoneError("zone_link", "the overlay holds a junction or a link")
        if current == folder and STAGING in children:
            children.remove(STAGING)
        for name in names:
            yield (current / name).relative_to(folder).as_posix(), current / name


def pattern(declared: OutputFile, job: NodeJob) -> str:
    return declared.path.replace(PARTITION, "-" if job.partition is None else str(job.partition))


@dataclass(frozen=True, slots=True)
class RunZone:
    root: Path

    @classmethod
    def of(cls, home: Path, run_id: str) -> RunZone:
        return cls(zones_root(home) / run_id)

    @property
    def code(self) -> Path:
        return self.root / "code"

    @property
    def work(self) -> Path:
        return self.root / "work"

    @property
    def attempts(self) -> Path:
        return self.root / "attempts"

    @property
    def pids(self) -> Path:
        return self.root / "pids"

    @property
    def staging(self) -> Path:
        return self.work / STAGING

    def overlay(self, job: NodeJob) -> Path:
        return self.attempts / slot_name(job)

    def prepare_code(self, folder: Path) -> dict[str, str]:
        """Copy the workflow folder into `code/` once per run and hash it; a resumed run keeps
        the copy its first start made."""
        manifest = self.root / CODE_MANIFEST
        if manifest.is_file():
            return cast(dict[str, str], json.loads(manifest.read_text(encoding="utf-8")))
        if self.code.exists():
            remove(self.code)
        shutil.copytree(folder, self.code, symlinks=False)
        found = {relative: digest(path) for relative, path in files_under(self.code)}
        for _, path in files_under(self.code):
            path.chmod(stat.S_IREAD)
        self.work.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps(found, sort_keys=True), encoding="utf-8")
        return found

    def open(self, job: NodeJob) -> Overlay:
        """A fresh overlay for the attempt, and what `work/` held when it opened."""
        path = self.overlay(job)
        if path.exists():
            remove(path)
        path.mkdir(parents=True)
        self.work.mkdir(parents=True, exist_ok=True)
        seen: Seen = {}
        for relative, file in files_under(self.work):
            facts = file.stat()
            seen[relative] = (facts.st_size, facts.st_mtime_ns)
        return Overlay(path, seen)

    def discard(self, overlay: Path) -> None:
        if overlay.exists():
            remove(overlay)

    def commit(
        self,
        job: NodeJob,
        overlay: Overlay,
        declared: Sequence[OutputFile],
        artifacts: Collection[str],
        keys: JsonObject,
    ) -> Commit:
        """Stage the declared files and the artifacts, then rename them into `work/`. The
        caller records the result as `zone_committed` and then calls `finish`."""
        written = [d for d in declared if not d.delete]
        tombstones = [pattern(d, job) for d in declared if d.delete]
        chosen: dict[str, OutputFile] = {}
        for relative, _ in files_under(overlay.path):
            match = next(
                (d for d in written if PurePosixPath(relative).full_match(pattern(d, job))), None
            )
            if match is not None:
                chosen[relative] = match
            elif relative in artifacts:
                chosen[relative] = OutputFile(path=relative)
        for relative in chosen:
            if leaves_work(relative):
                raise ZoneError("zone_path", "a declared output leaves the shared zone")
        deleted = sorted(
            relative
            for relative, _ in files_under(self.work)
            if any(PurePosixPath(relative).full_match(t) for t in tombstones)
        )
        for relative, declaration in chosen.items():
            if declaration.merge == "replace" and self._changed(overlay, relative):
                raise ZoneError(
                    "zone_conflict",
                    "another attempt committed a declared path after this one opened",
                )
        stage = self.staging / slot_name(job)
        if stage.exists():
            remove(stage)
        hashes: dict[str, str] = {}
        for relative, declaration in chosen.items():
            body = self._merged(overlay.path / relative, self.work / relative, declaration)
            staged = stage / "files" / relative
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(body)
            hashes[relative] = sha256(body).hexdigest()
        plan: JsonObject = {"keys": keys, "sha256": dict(hashes), "deleted": list(deleted)}
        stage.mkdir(parents=True, exist_ok=True)
        (stage / "plan.tmp").write_text(json.dumps(plan), encoding="utf-8")
        os.replace(stage / "plan.tmp", stage / PLAN)
        return self.apply(stage)

    def _changed(self, overlay: Overlay, relative: str) -> bool:
        target = self.work / relative
        if not target.is_file():
            return relative in overlay.seen
        facts = target.stat()
        return overlay.seen.get(relative) != (facts.st_size, facts.st_mtime_ns)

    def _merged(self, mine: Path, shared: Path, declaration: OutputFile) -> bytes:
        body = mine.read_bytes()
        if declaration.merge == "replace" or not shared.is_file():
            return body
        if declaration.merge == "append":
            return shared.read_bytes() + body
        try:
            base = json.loads(shared.read_bytes())
            update = json.loads(body)
        except ValueError as error:
            raise ZoneError("zone_merge", "a keyed output is not a JSON object") from error
        if not isinstance(base, dict) or not isinstance(update, dict):
            raise ZoneError("zone_merge", "a keyed output is not a JSON object")
        merged = cast(dict[str, JsonValue], base) | cast(dict[str, JsonValue], update)
        return json.dumps(merged, sort_keys=True).encode()

    def apply(self, stage: Path) -> Commit:
        """Rename a complete stage into `work/`. A path already renamed is skipped, so a second
        apply after a crash finishes the first."""
        plan = cast(JsonObject, json.loads((stage / PLAN).read_text(encoding="utf-8")))
        hashes = cast(dict[str, str], plan["sha256"])
        deleted = cast(list[str], plan["deleted"])
        work = self.work.resolve()
        for relative in [*hashes, *deleted]:
            target = (work / relative).resolve()
            if leaves_work(relative) or not target.is_relative_to(work):
                raise ZoneError("zone_path", "a staged path leaves the shared zone")
        for relative in hashes:
            staged = stage / "files" / relative
            if staged.is_file():
                (work / relative).parent.mkdir(parents=True, exist_ok=True)
                os.replace(staged, work / relative)
        for relative in deleted:
            (work / relative).unlink(missing_ok=True)
        return Commit(cast(JsonObject, plan["keys"]), hashes, deleted, stage)

    def finish(self, commit: Commit) -> None:
        """Drop the stage once `zone_committed` is in the ledger."""
        if commit.stage.exists():
            remove(commit.stage)

    def recover(self) -> list[Commit]:
        """At resume: roll every complete stage forward, delete every incomplete one, and delete
        the overlays a dead engine left. Each returned commit still needs `zone_committed`, then
        `finish`."""
        rolled: list[Commit] = []
        for stage in children(self.staging):
            if (stage / PLAN).is_file():
                rolled.append(self.apply(stage))
            else:
                remove(stage)
        for overlay in children(self.attempts):
            remove(overlay)
        return rolled


def children(folder: Path) -> Iterable[Path]:
    return sorted(p for p in folder.iterdir() if p.is_dir()) if folder.is_dir() else ()
