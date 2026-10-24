"""The Lab's backend now: a workspace over the Library and the engine (Lab AD-19, AD-20; 55 D-14).

A **project** is a `collection` item and its members are the items put in it. **New…** creates a
project from a template at one of four levels, and a level is a tag on a published template, so it
is a filter over the templates the engine has published and never a kind. The **workspace** (the
open member, the layout, the pins, the open tabs) is the `workspace` annotation on the project, so
reopening the Lab restores it and mints no version.

The panels read what the Library and the market-data door already answer: the explorer is the
project's members, problems are marks and conflicts, the timeline is the item's moves in the ref
log, and the data panel is the dataset card plus one sample through the door. A run is an input
through the engine's `@run` and `@library` references (DR9), so Tuesday's result enters today's run
pinned instead of retyped.

A **training run on the PC is a placement** (Lab AD-20): it declares a GPU slot from
`placement.pc.gpu_slots`, checks the PC's live free disk against the partitions it must fetch and
refuses with both sizes when they do not fit, then materialises exactly those partitions into the PC
cache and reads nothing else. The `model` it lands carries the data fingerprints, the code version
and the seed, links `consumed` to the card and `derived-from` its code.

Pods are not part of this backend (Lab AD-10 to AD-12 stay designed and unbuilt). The operations are
`lab` catalog rows, served by the host's user door for the UI's Lab and on no model's surface: the
copilot's Lab pack is a later slice (Lab AD-14).
"""

from __future__ import annotations

import shutil
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType
from typing import Final, Literal, Protocol, cast

from pydantic import JsonValue
from qmx_library.cards import SeriesCard
from qmx_library.port import Draft, JsonObject, LibraryRefused, ObjectView
from qmx_library.principal import MAIN

from qmx_control.library import OPERATOR, Library, refused
from qmx_control.models import ControlError, Document

type Level = Literal["quick-idea", "experiment", "study", "campaign"]

LEVELS: Final[tuple[Level, ...]] = ("quick-idea", "experiment", "study", "campaign")
LEVEL_TAG: Final[str] = "level:"
"""A level is a tag on a published template, so a level is a filter, not a kind (Lab AD-19)."""
PACK_TEMPLATES: Final[Mapping[Level, tuple[str, ...]]] = MappingProxyType(
    {
        "quick-idea": ("rough-idea-to-test-plan", "morning-digest"),
        "experiment": ("ml-training-run-with-a-holdout", "first-backtest-from-an-idea"),
        "study": ("variant-generation-and-comparison", "portfolio-combination-study"),
        "campaign": ("overnight-lab-loop", "weekly-review"),
    }
)
"""The pack's own template per level, in the order the Lab offers them: what `New…` installs before
any template carries that level's tag, so the second project at a level is a filter over the first
one's tag."""
WORKSPACE: Final[str] = "workspace"
"""The collection annotation the workspace state lives in (Lab AD-19)."""
PROJECT: Final[str] = "collection"
MEMBER_LIMIT: Final[int] = 500
"""Members one project read returns; the explorer pages past it with its own search."""
MB: Final[int] = 1024 * 1024


@dataclass(frozen=True, slots=True)
class Answered[T]:
    """What one door answered: the value, or the refusal it named. A refusal is the door's own
    words, so the panel shows why a month was refused and not an empty table (Lib AD-28)."""

    value: T | None = None
    refusal: str = ""

    @property
    def refused(self) -> bool:
        return bool(self.refusal)


class Door(Protocol):
    """The market-data door this machine's host serves (Lib AD-28). The Lab reads a card, one
    sample and the partitions a training run needs, and nothing else."""

    def card(self, series: str) -> Answered[dict[str, object]]: ...
    def read(
        self, series: str, *, start_ns: int, end_ns: int, purpose: str = "exploration"
    ) -> Answered[dict[str, object]]: ...
    def materialise(
        self, fingerprints: Sequence[str], *, into: Path | None = None
    ) -> Answered[Sequence[Path]]: ...


class Installer(Protocol):
    """The engine's template install. Answers the published `workflow` object's id, which is what a
    project points at and what a level tags; the Lab never publishes a template itself."""

    def install(self, template_id: str) -> Answered[str]: ...


@dataclass(frozen=True, slots=True)
class Placement:
    """Where a training run trains: the PC's GPU slot and the partition cache the door fills.

    `gpu_slots` is the host's reading of `placement.pc.gpu_slots` (engine AD-20, AD-58) and
    `device` is the hardware that reading found. `free` is the live free-space reading the check
    uses; a placement with no cache has no reading and refuses to start a run."""

    gpu_slots: int = 0
    device: str = "cpu"
    cache: Path | None = None
    free: Callable[[], int] | None = None

    def slot(self) -> int | None:
        """The GPU slot this placement hands a training node, or None when the PC has none."""
        return 0 if self.gpu_slots > 0 else None

    def room(self) -> int:
        """The live free bytes the cache's volume has, the reading the check refuses against."""
        if self.free is not None:
            return self.free()
        if self.cache is None:
            raise ControlError(
                "not_configured",
                "a training run on the PC needs the door's partition cache to check free space",
                409,
            )
        self.cache.mkdir(parents=True, exist_ok=True)
        return shutil.disk_usage(self.cache).free


@dataclass(frozen=True, slots=True)
class Partition:
    """One month a training run reads, by the fingerprint the door verifies."""

    month: str
    fingerprint: str
    bytes: int = 0


@dataclass(frozen=True, slots=True)
class Training:
    """A training run's placement: the GPU slot it holds, the partitions it may read and the model
    lineage it will record. Nothing here is a pod (Lab AD-10)."""

    task: str
    series: str
    card_object: str
    partitions: tuple[Partition, ...]
    paths: tuple[Path, ...]
    seed: int
    code_version: str
    code_object: str | None = None
    slot: int | None = None
    device: str = "cpu"
    extra: JsonObject = field(default_factory=dict[str, JsonValue])

    @property
    def months(self) -> tuple[str, ...]:
        return tuple(part.month for part in self.partitions)

    @property
    def fingerprints(self) -> tuple[str, ...]:
        return tuple(part.fingerprint for part in self.partitions)

    def fields(self) -> JsonObject:
        """The `model` fields Lab AD-20 names: the data by fingerprint, the code, the seed, the
        framework and the hardware."""
        return {
            **self.extra,
            "task": self.task,
            "series": self.series,
            "months": list(self.months),
            "partitions": [
                {"month": part.month, "fingerprint": part.fingerprint} for part in self.partitions
            ],
            "data": {"card": self.card_object, "fingerprints": list(self.fingerprints)},
            "code": {"version": self.code_version},
            "seed": self.seed,
            "framework": "torch",
            "hardware": {
                "placement": "pc",
                "gpu_slot": self.slot,
                "device": self.device,
            },
        }


class Lab:
    """The Lab's operations over one home's Library and the engine's door (Lab AD-15, AD-19)."""

    def __init__(
        self,
        library: Library,
        *,
        installs: Installer,
        door: Door | None = None,
        placement: Placement | None = None,
    ) -> None:
        self.library = library
        self.installs = installs
        self.door = door
        self.placement = placement or Placement()

    # --- New… and the four levels -----------------------------------------

    def levels(self) -> dict[str, tuple[str, ...]]:
        """Every level with the published templates it offers: its tagged ones first, then the
        pack's own, so `New…` always has a template to install."""
        found: dict[str, tuple[str, ...]] = {}
        for level in LEVELS:
            found[level] = tuple(
                dict.fromkeys(
                    (*self.published(level), *PACK_TEMPLATES[level]),
                )
            )
        return found

    def published(self, level: str) -> tuple[str, ...]:
        """The published templates carrying this level's tag, newest head first (a filter, not a
        kind)."""
        if level not in LEVELS:
            raise ControlError(
                "invalid_arguments",
                f"{level!r} is not a Lab level; the levels are {', '.join(LEVELS)}",
            )
        tag = f"{LEVEL_TAG}{level}"
        rows = self.library.store.catalog.db.execute(
            "SELECT a.object_id FROM annotations a JOIN objects o ON o.object_id = a.object_id "
            "WHERE a.key = 'tags' AND o.kind = 'workflow' AND EXISTS ("
            "SELECT 1 FROM json_each(a.value) j WHERE j.value = ?) ORDER BY a.seq DESC",
            (tag,),
        ).fetchall()
        found: list[str] = []
        for (object_id,) in rows:
            view = self._view(str(object_id))
            head = self.library.store.head(view.item, MAIN)
            if head is not None and head[0] == view.object_id and view.item not in found:
                found.append(view.item)
        return tuple(found)

    def new(self, level: str, title: str, *, template: str | None = None) -> Document:
        """Create a project at one level and install its template: a `collection` tagged with the
        level, its template published and tagged, and a fresh workspace annotation."""
        if level not in LEVELS:
            raise ControlError(
                "invalid_arguments",
                f"{level!r} is not a Lab level; the levels are {', '.join(LEVELS)}",
            )
        offered = self.levels()[level]
        wanted = template or (offered[0] if offered else "")
        if not wanted:
            raise ControlError("template_missing", f"no template answers the level {level}", 409)
        installed = self.installs.install(wanted)
        if installed.refused or installed.value is None:
            raise ControlError("template_refused", installed.refusal, 409)
        self._tag(installed.value, f"{LEVEL_TAG}{level}")
        project = self._land(
            Draft(
                PROJECT,
                None,
                title=title,
                fields={"items": [], "level": level, "template": installed.value},
                tags=[level],
            )
        )
        self._annotate(project, WORKSPACE, self._fresh(level, installed.value))
        return self.open(project)

    # --- the workspace ----------------------------------------------------

    def open(self, project: str) -> Document:
        """Open one project: its members, its workspace, its problems and its timeline."""
        view = self._view(project)
        if view.kind != PROJECT:
            raise ControlError(
                "invalid_arguments", f"{view.item} is a {view.kind}, not a project", 400
            )
        fields = view.fields
        return document(
            {
                "project": {
                    "id": view.object_id,
                    "item": view.item,
                    "title": view.title,
                    "level": str(fields.get("level") or ""),
                    "template": str(fields.get("template") or ""),
                    "tags": view.annotations.get("tags") or [],
                },
                "workspace": self.workspace_of(view),
                "members": self._members(fields),
                "problems": self.problems(fields),
                "timeline": self.timeline(view),
            }
        )

    def workspace_of(self, view: ObjectView) -> JsonObject:
        """The workspace annotation as it reads now, and the empty workspace when a project has
        none yet."""
        found = view.annotations.get(WORKSPACE)
        if not isinstance(found, dict):
            return {"open": "", "layout": [], "pins": [], "tabs": []}
        return cast(JsonObject, found)

    def workspace(
        self,
        project: str,
        *,
        open: str | None = None,
        pins: Sequence[str] | None = None,
        layout: Sequence[JsonValue] | None = None,
        tabs: Sequence[str] | None = None,
    ) -> Document:
        """Write the workspace state onto the project and answer it as the Library reads it back.

        The state is an annotation, so reopening the Lab restores it and no version is minted.
        Every named member and pin has to be an object this Library holds."""
        view = self._view(project)
        if view.kind != PROJECT:
            raise ControlError(
                "invalid_arguments", f"{view.item} is a {view.kind}, not a project", 400
            )
        state = dict(self.workspace_of(view))
        if open is not None:
            self._view(open)
            state["open"] = open
        if pins is not None:
            for pin in pins:
                self._view(pin)
            state["pins"] = list(pins)
        if layout is not None:
            state["layout"] = list(layout)
        if tabs is not None:
            state["tabs"] = [str(tab) for tab in tabs]
        self._annotate(project, WORKSPACE, state)
        return self.open(project)

    # --- the panels -------------------------------------------------------

    def panel(self, card: str, *, month: str = "", purpose: str = "exploration") -> Document:
        """One dataset card's data panel: its months and quality off the card, and one month's
        sample through the door. A sealed month is refused in the door's own words."""
        fields, series = self._series(card)
        door = self._market()
        answer = door.card(series)
        if answer.refused:
            raise ControlError("door_refused", answer.refusal, 409)
        served = answer.value or {}
        doors = [str(row["month"]) for row in rows_of(served.get("partitions"))]
        months = [str(month) for month in list_of(fields.get("months"))] or doors
        wanted = month or (months[0] if months else "")
        if not wanted:
            raise ControlError("not_found", f"{series} has no month to show", 404)
        start, end = self._window(wanted)
        sample = door.read(series, start_ns=start, end_ns=end, purpose=purpose)
        return document(
            {
                "card": card,
                "series": series,
                "months": months,
                "quality": fields.get("quality") or {},
                "month": wanted,
                "sample": sample.value,
                "refusal": sample.refusal,
            }
        )

    def problems(self, fields: JsonObject) -> list[JsonValue]:
        """The project's problems: a member's mark, and a merge conflict among its members."""
        found: list[JsonValue] = []
        for member in self._members(fields):
            object_id = str(member.get("id") or "")
            view = self._view(object_id)
            mark = self.library.store.marks(OPERATOR, object_id)
            if mark.worst is not None:
                found.append(
                    {
                        "id": object_id,
                        "kind": view.kind,
                        "title": view.title,
                        "problem": mark.worst,
                        "reason": mark.label,
                    }
                )
            if view.kind == "merge-conflict":
                found.append(
                    {
                        "id": object_id,
                        "kind": view.kind,
                        "title": view.title,
                        "problem": "conflict",
                        "reason": str(view.fields.get("into") or ""),
                    }
                )
        return found

    def timeline(self, view: ObjectView) -> list[JsonValue]:
        """The project's history: every move of its item in the ref log, oldest first."""
        return [
            {"kind": kind, "ref": ref, "principal": who}
            for kind, ref, who in self.library.store.history(view.item)
        ]

    # --- training on the PC -----------------------------------------------

    def training(
        self,
        card: str,
        *,
        months: Sequence[str],
        seed: int,
        code_version: str,
        task: str = "",
        code_object: str | None = None,
        free: int | None = None,
    ) -> Training:
        """Place a training run on the PC: check free space, materialise only the partitions it
        reads, and answer the lineage it will record.

        The check runs before anything is fetched. When the partitions do not fit the refusal
        names both sizes and nothing is materialised (Lab AD-20, Lib AD-10)."""
        fields, series = self._series(card)
        door = self._market()
        answer = door.card(series)
        if answer.refused:
            raise ControlError("door_refused", answer.refusal, 409)
        available = {
            str(row["month"]): Partition(
                month=str(row["month"]),
                fingerprint=str(row["fingerprint"]),
                bytes=int(cast(int, row.get("bytes") or 0)),
            )
            for row in rows_of((answer.value or {}).get("partitions"))
        }
        asked = [str(month) for month in months]
        for month in asked:
            if month not in available:
                raise ControlError("not_found", f"{series} has no partition for {month}", 404)
        partitions = tuple(available[month] for month in dict.fromkeys(asked))
        needed = sum(part.bytes for part in partitions)
        room = self.placement.room() if free is None else free
        if needed > room:
            raise ControlError(
                "disk_full",
                f"a training run on the PC needs {needed / MB:.1f} MB for "
                f"{len(partitions)} partitions of {series} and {room / MB:.1f} MB is free; "
                "nothing was materialised",
                409,
            )
        landed = door.materialise(
            [part.fingerprint for part in partitions], into=self.placement.cache
        )
        if landed.refused or landed.value is None:
            raise ControlError("door_refused", landed.refusal, 409)
        return Training(
            task=task or str(fields.get("task") or fields.get("subject") or series),
            series=series,
            card_object=card,
            partitions=partitions,
            paths=tuple(landed.value),
            seed=seed,
            code_version=code_version,
            code_object=code_object,
            slot=self.placement.slot(),
            device=self.placement.device,
        )

    def model(
        self,
        training: Training,
        *,
        title: str = "",
        weights: bytes = b"",
        metrics: JsonObject | None = None,
    ) -> Document:
        """Land the `model` a training run made: its lineage fields, its weights blob and its two
        edges, `consumed` to the card and `derived-from` its code version when that is an object."""
        fields = training.fields()
        if metrics:
            fields["metrics"] = metrics
        landed = self.library.store.put(
            OPERATOR,
            Draft(
                "model",
                None,
                title=title or f"{training.task}, seed {training.seed}",
                fields=fields,
                blobs={"weights": weights} if weights else {},
                tags=["model"],
            ),
            on=MAIN,
            expected_head=None,
        )
        edges: list[tuple[str, str]] = [("consumed", training.card_object)]
        if training.code_object:
            edges.append(("derived-from", training.code_object))
        for edge, target in edges:
            self.library.store.relate(OPERATOR, landed.object_id, edge, target)
        return self._document(landed.object_id)

    # --- plumbing ---------------------------------------------------------

    def _market(self) -> Door:
        if self.door is None:
            raise ControlError(
                "not_configured",
                "this host serves no market-data door, so the Lab reads no price data",
                409,
            )
        return self.door

    def _series(self, card: str) -> tuple[JsonObject, str]:
        view = self._view(card)
        if view.kind != "dataset":
            raise ControlError(
                "invalid_arguments", f"{view.item} is a {view.kind}, not a dataset card", 400
            )
        fields = view.fields
        key = str(fields.get("series_key") or "")
        if key:
            return fields, key
        series = SeriesCard(
            source=str(fields.get("source") or ""),
            subject=str(fields.get("subject") or ""),
            kind=str(fields.get("kind") or ""),
            variant=str(fields.get("variant") or ""),
        )
        return fields, series.series

    def _members(self, fields: JsonObject) -> list[JsonObject]:
        found: list[JsonObject] = []
        for member in list_of(fields.get("items"))[:MEMBER_LIMIT]:
            if not isinstance(member, str):
                continue
            try:
                view = self._view(member)
            except ControlError:
                found.append({"id": member, "kind": "", "title": "", "missing": True})
                continue
            found.append(
                {"id": view.object_id, "kind": view.kind, "title": view.title, "missing": False}
            )
        return found

    def _fresh(self, level: str, template: str) -> JsonObject:
        return {"open": template, "layout": [], "pins": [], "tabs": [], "level": level}

    def _window(self, month: str) -> tuple[int, int]:
        try:
            start = datetime.strptime(month, "%Y-%m").replace(tzinfo=UTC)
        except ValueError as error:
            raise ControlError(
                "invalid_arguments", f"{month!r} is not a month; write it as YYYY-MM", 400
            ) from error
        end = (
            start.replace(year=start.year + 1, month=1)
            if start.month == 12
            else start.replace(month=start.month + 1)
        )
        return int(start.timestamp()) * 1_000_000_000, int(end.timestamp()) * 1_000_000_000

    def _tag(self, object_id: str, tag: str) -> None:
        view = self._view(object_id)
        tags = [str(found) for found in list_of(view.annotations.get("tags"))]
        if tag not in tags:
            self._annotate(object_id, "tags", [*tags, tag])

    def _annotate(self, object_id: str, key: str, value: JsonValue) -> None:
        try:
            self.library.store.annotate(OPERATOR, object_id, {key: value})
        except LibraryRefused as error:
            raise refused(error) from error

    def _land(self, draft: Draft) -> str:
        return self.library.store.put(OPERATOR, draft, on=MAIN, expected_head=None).object_id

    def _view(self, object_id: str) -> ObjectView:
        try:
            return self.library.store.get(OPERATOR, object_id)
        except LibraryRefused as error:
            raise refused(error) from error

    def _document(self, object_id: str) -> Document:
        view = self._view(object_id)
        return document(
            {
                "id": view.object_id,
                "item": view.item,
                "kind": view.kind,
                "title": view.title,
                "fields": view.fields,
                "annotations": view.annotations,
            }
        )


def document(found: Mapping[str, object]) -> Document:
    """A door answer as the control plane's document: JSON in, JSON out, one cast at the seam."""
    return cast(Document, found)


def list_of(value: object) -> list[JsonValue]:
    """A JSON list, or nothing: a field the store holds loosely."""
    return cast(list[JsonValue], value) if isinstance(value, list) else []


def rows_of(value: object) -> list[JsonObject]:
    """The object rows of a JSON list, skipping anything that is not one."""
    return [cast(JsonObject, row) for row in list_of(value) if isinstance(row, dict)]
