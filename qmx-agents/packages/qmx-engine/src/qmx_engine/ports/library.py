"""The Library port (SOLUTION-DESIGN 8.1, AD-14), in the shape the Library granted
(ENGINE-REQUESTS-ANSWERED L1-L17, 27b S8 and B4).

The kinds are the Library's own: a `workflow` item's versions are its objects, a version is
`(item, fields.semver, object_id)` and there is no version kind; a run is a `workflow-run`; a test
result is a `test-report`. Drafts live on `refs/drafts/<item>` (or an agent's
`refs/agents/<sid>/<item>`), `main` holds published versions only, and a run writes only on
`refs/runs/<run_id>` with the principal `run:<run_id>`. Edges come from one closed set, where
`replaces` is the one supersede relation. Nothing is ever deleted: a change is a new object, a new
edge or a new annotation.

Every `put_*` returns the stored object, so a caller can link it; the object's `blob` is the
content hash 8.1 returns. `get`, `edges`, `objects`, `annotate` and `annotation` are the catalog
reads and the annotation write the service needs beside 8.1's list.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final, Literal, Protocol, get_args

from pydantic import JsonValue

from qmx_engine.definition.folder import (
    DEFINITION,
    Problem,
    WorkflowFolder,
    content_hash,
    load,
    refs_in,
)

type JsonObject = dict[str, JsonValue]
type Kind = Literal[
    "workflow", "workflow-run", "artifact", "test-report", "memory-row", "agent-tool", "checkpoint"
]
type EdgeName = Literal[
    "version-of",
    "variant-of",
    "run-of",
    "produced-by",
    "consumed",
    "tested-by",
    "replaces",
    "archived-as",
]
type Mode = Literal["live", "test"]
type RunStatus = Literal[
    "queued", "running", "waiting", "passed", "failed", "stopped", "interrupted"
]
"""SOLUTION-DESIGN 3.1's one run status table, word for word the Library's AD-15 set."""

KINDS: Final = frozenset(get_args(Kind.__value__))
EDGES: Final = frozenset(get_args(EdgeName.__value__))
MAIN: Final = "main"


def drafts_ref(item: str) -> str:
    return f"refs/drafts/{item}"


def runs_ref(run_id: str) -> str:
    return f"refs/runs/{run_id}"


def champions_ref(item: str) -> str:
    return f"refs/champions/{item}"


def is_draft_ref(ref: str) -> bool:
    return ref.startswith(("refs/drafts/", "refs/agents/"))


class LibraryRefused(Exception):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code


@dataclass(frozen=True, slots=True)
class Bundle:
    """A workflow folder as the Library holds it: the definition and the files its refs name."""

    definition: JsonObject
    files: Mapping[str, bytes]

    @classmethod
    def read(cls, root: Path) -> Bundle:
        folder = load(root)
        if folder.document is None:
            raise ValueError(f"no workflow definition in {root}")
        return cls(folder.document, dict(folder.refs))

    def write(self, root: Path) -> Path:
        root.mkdir(parents=True, exist_ok=True)
        (root / DEFINITION).write_text(json.dumps(self.definition, indent=2), encoding="utf-8")
        base = root.resolve()
        for ref, data in self.files.items():
            target = (base / ref).resolve()
            if PurePosixPath(ref).is_absolute() or not target.is_relative_to(base):
                raise ValueError(f"the ref {ref!r} leaves the workflow folder")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        return root

    def folder(self) -> WorkflowFolder:
        """The bundle as `load` would read it from disk, a missing ref file reported."""
        refs: dict[str, bytes] = {}
        problems: list[Problem] = []
        for path, ref in refs_in(self.definition):
            if PurePosixPath(ref).is_absolute() or ".." in PurePosixPath(ref).parts:
                problems.append(Problem("ref_escapes_folder", path, "the ref leaves the folder"))
            elif ref in self.files:
                refs[ref] = self.files[ref]
            else:
                problems.append(Problem("ref_missing", path, "the ref names no file in the folder"))
        return WorkflowFolder(Path(), self.definition, refs, problems)

    def content_hash(self) -> str | None:
        """None for an unresolved variant, which has no hash until it is resolved (AD-11)."""
        if self.definition.get("extends") is not None:
            return None
        return content_hash(self.folder())

    def needs(self) -> list[str]:
        """`meta.needs`: the pieces of QMX this workflow waits for."""
        meta = self.definition.get("meta")
        found = meta.get("needs") if isinstance(meta, dict) else None
        return [str(need) for need in found] if isinstance(found, list) else []


@dataclass(frozen=True, slots=True)
class Stored:
    object_id: str
    kind: Kind
    item: str
    ref: str
    fields: JsonObject
    principal: str
    at: str
    blob: str | None = None


@dataclass(frozen=True, slots=True)
class Draft:
    item: str
    ref: str
    object_id: str
    revision: int
    bundle: Bundle
    content_hash: str | None


@dataclass(frozen=True, slots=True)
class Edge:
    from_id: str
    edge: EdgeName
    to_id: str
    principal: str
    at: str


@dataclass(frozen=True, slots=True)
class RunSummary:
    run_id: str
    workflow_item: str
    object_id: str
    mode: Mode
    status: RunStatus
    reason: str | None
    totals: JsonObject
    placement: JsonObject
    trace_artifact_hash: str | None
    started_by: str
    """The principal of the call that started the run (27b S17)."""


@dataclass(frozen=True, slots=True)
class LibraryEvent:
    seq: int
    name: str
    """`library.<kind>.created`."""
    object_id: str
    ref: str


class LibraryPort(Protocol):
    def get_object(self, object_id: str) -> Bundle: ...

    def get_draft(self, item: str, ref: str) -> Draft: ...

    def put_draft(
        self,
        item: str | None,
        bundle: Bundle,
        expected_revision: int,
        *,
        principal: str,
        ref: str | None = None,
        fields: JsonObject | None = None,
    ) -> Draft:
        """Never onto `main`. `ref` defaults to `refs/drafts/<item>`; the first save omits
        `item` and gets one."""
        ...

    def publish(self, item: str, from_ref: str, semver: str, *, principal: str) -> str:
        """Merge the draft into `main` with its semver, copying `tested-by` when the content hash
        matches. Publishing a hash already on `main` returns that version and writes nothing."""
        ...

    def land_draft(self, item: str, from_run: str, *, principal: str) -> str: ...

    def put_artifact(
        self,
        data: bytes,
        type_: str,
        metadata: JsonObject,
        *,
        run_id: str,
        principal: str,
        intent_key: str | None = None,
    ) -> Stored: ...

    def get_artifact(self, blob: str) -> bytes: ...

    def put_run_summary(self, summary: RunSummary, *, principal: str) -> Stored: ...

    def put_test_report(self, draft_hash: str, report: JsonObject, *, principal: str) -> Stored:
        """`report` names its `workflow_item` and `run_id`; it lands on the run's branch."""
        ...

    def put_checkpoint(
        self, run_id: str, node_id: str, attempt: int, data: bytes, *, principal: str
    ) -> str: ...

    def put_agent_tool(self, run_id: str, tool: JsonObject, *, principal: str) -> Stored: ...

    def put_memory_row(self, run_id: str, row: JsonObject, *, principal: str) -> Stored: ...

    def link(self, from_id: str, edge: EdgeName, to_id: str, *, principal: str) -> None: ...

    def find_by_intent(self, intent_key: str) -> list[str]: ...

    def list_runs(self, workflow_item: str, object_id: str | None = None) -> list[RunSummary]: ...

    def champion(self, workflow_item: str) -> str | None: ...

    def set_champion(self, workflow_item: str, object_id: str, *, principal: str) -> None: ...

    def events(self, after: int = 0) -> list[LibraryEvent]: ...

    def get(self, object_id: str) -> Stored: ...

    def edges(
        self, object_id: str, edge: EdgeName | None = None, *, reverse: bool = False
    ) -> list[Edge]:
        """Edges out of the object, or into it when `reverse`."""
        ...

    def objects(self, item: str, kind: Kind, ref: str | None = None) -> list[Stored]: ...

    def annotate(self, object_id: str, key: str, value: JsonValue, *, principal: str) -> None: ...

    def annotation(self, object_id: str, key: str) -> JsonValue: ...
