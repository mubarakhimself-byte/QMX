"""`EngineLibraryAdapter`: the engine's built `LibraryPort` (`qmx_engine.ports.library`) over the
real store (Library AD-15, 45 DC-14). The engine's own fake and this adapter pass the same
contract tests; the engine changes nothing.

How the engine's verbs map onto the Library's:

- A workflow version is a `workflow` object with a `definition` blob and one `files/<path>` blob
  per file of its folder. A draft is the head of `refs/drafts/<item>`; its revision is how many
  times that ref has moved. Publishing is a merge into `main`, and the semver is an annotation.
- An agent never puts onto `refs/drafts/<item>`: its save lands on its own
  `refs/agents/<session_id>/<item>` and is merged into the draft (AD-7, B-43). A run's save lands
  on its own `refs/runs/<run_id>` and the engine lands it on the draft.
- Run summaries, artifacts, test reports, memory rows and agent tools are put on
  `refs/runs/<run_id>` by the run itself. When a run summary says `passed`, the standing rule of
  `landing.land` moves them (AD-18).
- Champion moves, draft landings and the engine's own version-state annotations carry
  `engine:<store>` (engine AD-14).

Refusals come back as the engine's `LibraryRefused` with the engine's codes.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from dataclasses import asdict
from typing import Any, Final, cast

from pydantic import JsonValue
from qmx_engine.ports.library import (
    EDGES,
    MAIN,
    Bundle,
    Draft,
    Edge,
    EdgeName,
    JsonObject,
    Kind,
    LibraryEvent,
    RunStatus,
    RunSummary,
    Stored,
    champions_ref,
    drafts_ref,
    is_draft_ref,
    runs_ref,
)
from qmx_engine.ports.library import LibraryRefused as EngineRefused

from qmx_library import port
from qmx_library.landing import land
from qmx_library.principal import Principal, agent_ref, may_advance
from qmx_library.store import Store

CODES: Final = {
    "not_found": "unknown_object",
    "ref_not_owned": "wrong_principal",
    "stale_head": "revision_conflict",
    "unknown_relation": "edge_not_in_set",
    "blob_unavailable": "unknown_blob",
}
"""Library refusal codes as the engine names them; any other code passes through."""
FILES: Final = "files/"
MAIN_BLOB: Final = {"workflow": "definition", "artifact": "content"}


@contextmanager
def _engine_codes() -> Generator[None]:
    try:
        yield
    except port.LibraryRefused as refused:
        code = CODES.get(refused.code, refused.code)
        raise EngineRefused(code, str(refused).split(": ", 1)[-1]) from refused


class EngineLibraryAdapter:
    def __init__(self, store: Store) -> None:
        self.store = store

    def _stored(self, object_id: str) -> Stored:
        view = self.store.get(self.store.engine, object_id)
        ref, principal, at = self.store.placement(object_id) or ("", "", "")
        slot = MAIN_BLOB.get(view.kind)
        blob = view.blobs[slot].blob_id if slot and slot in view.blobs else None
        fields = view.fields
        if "semver" in view.annotations:
            fields = {**fields, "semver": view.annotations["semver"]}
        return Stored(object_id, cast(Kind, view.kind), view.item, ref, fields, principal, at, blob)

    def _put(
        self,
        kind: str,
        item: str,
        ref: str,
        fields: JsonObject,
        principal: str,
        *,
        title: str = "",
        blobs: Mapping[str, bytes] | None = None,
        parents: list[str] | None = None,
    ) -> str:
        who = Principal.parse(principal)
        found = self.store.head(item, ref)
        head = None if found is None else found[0]
        draft = port.Draft(kind, item, title, "", fields, blobs or {}, parents=parents)
        return self.store.put(who, draft, on=ref, expected_head=head).object_id

    def get(self, object_id: str) -> Stored:
        with _engine_codes():
            return self._stored(object_id)

    def get_object(self, object_id: str) -> Bundle:
        with _engine_codes():
            view = self.store.get(self.store.engine, object_id, blobs="fetch")
        if view.kind != "workflow":
            raise EngineRefused("not_a_workflow", f"{object_id} is a {view.kind}")
        files = {s.removeprefix(FILES): d for s, d in view.data.items() if s.startswith(FILES)}
        return Bundle(json.loads(view.data["definition"]), files)

    def get_draft(self, item: str, ref: str) -> Draft:
        found = self.store.head(item, ref) if is_draft_ref(ref) else None
        if found is None:
            raise EngineRefused("no_draft", f"no draft of {item} on {ref}")
        object_id, revision = found
        digest = self.get(object_id).fields.get("content_hash")
        return Draft(
            item,
            ref,
            object_id,
            revision,
            self.get_object(object_id),
            digest if isinstance(digest, str) else None,
        )

    def get_artifact(self, blob: str) -> bytes:
        with _engine_codes():
            try:
                return self.store.read_blob(blob)
            except port.LibraryRefused:
                return self.store.read_blob(blob, transient=True)

    def find_by_intent(self, intent_key: str) -> list[str]:
        return self.store.find_by_intent(self.store.engine, intent_key)

    def list_runs(self, workflow_item: str, object_id: str | None = None) -> list[RunSummary]:
        latest: dict[str, RunSummary] = {}
        for found in self.store.with_field("workflow-run", "workflow_item", workflow_item):
            summary = RunSummary(**cast(dict[str, Any], self._stored(found).fields))
            if object_id is None or summary.object_id == object_id:
                latest[summary.run_id] = summary
        return list(latest.values())

    def champion(self, workflow_item: str) -> str | None:
        found = self.store.head(workflow_item, champions_ref(workflow_item))
        return None if found is None else found[0]

    def events(self, after: int = 0) -> list[LibraryEvent]:
        return [
            LibraryEvent(m["seq"], f"library.{m['kind']}.created", m["new_head"], m["ref"])
            for m in self.store.placements(after)
        ]

    def edges(
        self, object_id: str, edge: EdgeName | None = None, *, reverse: bool = False
    ) -> list[Edge]:
        return [
            Edge(a, cast(EdgeName, b), c, d, e)
            for a, b, c, d, e in self.store.edges_of(object_id, reverse=reverse)
            if b in EDGES and (edge is None or b == edge)
        ]

    def objects(self, item: str, kind: Kind, ref: str | None = None) -> list[Stored]:
        return [self._stored(o) for o, _ in self.store.placed(item, kind, ref)]

    def annotation(self, object_id: str, key: str) -> JsonValue:
        with _engine_codes():
            return self.store.get(self.store.engine, object_id).annotations.get(key)

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
        if ref is not None and not is_draft_ref(ref):
            raise EngineRefused("not_a_draft_ref", f"a draft never lands on {ref}")
        with _engine_codes():
            who = Principal.parse(principal)
            item = item or self._new_item(str(bundle.definition.get("id") or "workflow"))
            ref = ref or drafts_ref(item)
            found = self.store.head(item, ref)
            if (found[1] if found else 0) != expected_revision:
                raise EngineRefused(
                    "revision_conflict",
                    f"{ref} is at revision {found[1] if found else 0}, not {expected_revision}",
                )
            digest = bundle.content_hash()
            blobs = {"definition": json.dumps(bundle.definition, sort_keys=True).encode()}
            blobs |= {f"{FILES}{path}": data for path, data in bundle.files.items()}
            title = str(bundle.definition.get("name") or item)
            main = self.store.head(item, MAIN)
            base = found or main
            parents = [base[0]] if base else []
            values: JsonObject = {**(fields or {}), "content_hash": digest}
            if may_advance(who, ref, "put", store=self.store.name):
                self._put(
                    "workflow",
                    item,
                    ref,
                    values,
                    principal,
                    title=title,
                    blobs=blobs,
                    parents=parents,
                )
            else:
                own = self._own_ref(who, item, ref)
                self._put(
                    "workflow",
                    item,
                    own,
                    values,
                    principal,
                    title=title,
                    blobs=blobs,
                    parents=parents,
                )
                mover = self.store.engine if who.who == "run" else who
                merged = self.store.merge(mover, item, from_ref=own, into=ref, strategy="ff-only")
                if merged.outcome == "conflict":
                    raise EngineRefused("merge_conflict", f"{own} does not follow {ref}")
        return self.get_draft(item, ref)

    def _own_ref(self, who: Principal, item: str, ref: str) -> str:
        if who.who == "agent" and ref == drafts_ref(item):
            return agent_ref(str(who.id), item)
        if who.who == "run" and ref == drafts_ref(item):
            return runs_ref(str(who.id))
        raise EngineRefused("wrong_principal", f"{who} may not write {ref}")

    def _new_item(self, base: str) -> str:
        item, n = base, 2
        while self.store.has_item(item):
            item, n = f"{base}-{n}", n + 1
        return item

    def publish(self, item: str, from_ref: str, semver: str, *, principal: str) -> str:
        draft = self.get_draft(item, from_ref)
        if draft.content_hash is None:
            raise EngineRefused("unresolved_variant", "resolve the variant before publishing")
        versions = self.objects(item, "workflow", MAIN)
        for version in versions:
            if version.fields.get("content_hash") == draft.content_hash:
                return version.object_id
        if any(self.annotation(v.object_id, "semver") == semver for v in versions):
            raise EngineRefused("semver_taken", f"{item} already has a version {semver}")
        with _engine_codes():
            merged = self.store.merge(
                Principal.parse(principal), item, from_ref=from_ref, into=MAIN
            )
            if merged.outcome == "conflict":
                raise EngineRefused("merge_conflict", f"{from_ref} does not merge into main")
            self.store.annotate(self.store.engine, merged.object_id, {"semver": semver})
            if merged.object_id != draft.object_id:
                for edge in self.edges(draft.object_id, "tested-by"):
                    self.store.relate(
                        Principal.parse(principal), merged.object_id, "tested-by", edge.to_id
                    )
        return merged.object_id

    def land_draft(self, item: str, from_run: str, *, principal: str) -> str:
        if not self.store.placed(item, "workflow", runs_ref(from_run)):
            raise EngineRefused("unknown_object", f"run {from_run} made no {item}")
        with _engine_codes():
            merged = self.store.merge(
                self.store.engine,
                item,
                from_ref=runs_ref(from_run),
                into=drafts_ref(item),
                strategy="ff-only",
            )
        if merged.outcome == "conflict":
            raise EngineRefused(
                "merge_conflict", f"run {from_run}'s {item} does not follow the draft"
            )
        return merged.object_id

    def put_artifact(
        self,
        data: bytes,
        type_: str,
        metadata: JsonObject,
        *,
        run_id: str,
        principal: str,
        intent_key: str | None = None,
    ) -> Stored:
        with _engine_codes():
            fields: JsonObject = {"type": type_, "metadata": metadata}
            object_id = self._put(
                "artifact",
                str(uuid.uuid7()),
                runs_ref(run_id),
                fields,
                principal,
                title=type_,
                blobs={"content": data},
            )
            if intent_key is not None:
                self.store.annotate(
                    Principal.parse(principal), object_id, {"intent_key": intent_key}
                )
            return self._stored(object_id)

    def put_run_summary(self, summary: RunSummary, *, principal: str) -> Stored:
        with _engine_codes():
            fields = cast(JsonObject, asdict(summary))
            object_id = self._put(
                "workflow-run",
                summary.run_id,
                runs_ref(summary.run_id),
                fields,
                principal,
                title=f"Run {summary.run_id} of {summary.workflow_item}",
            )
            self._land(summary)
            return self._stored(object_id)

    def _land(self, summary: RunSummary) -> None:
        status: RunStatus = summary.status
        try:
            publish = self.store.get(self.store.engine, summary.object_id).fields.get("publish")
        except port.LibraryRefused:
            publish = None
        land(
            self.store,
            summary.run_id,
            mode=summary.mode,
            status=status,
            publish=str(publish or "auto"),
        )

    def put_test_report(self, draft_hash: str, report: JsonObject, *, principal: str) -> Stored:
        item, run_id = str(report["workflow_item"]), str(report["run_id"])
        with _engine_codes():
            fields: JsonObject = {**report, "content_hash": draft_hash}
            object_id = self._put(
                "test-report", item, runs_ref(run_id), fields, principal, title=f"Test of {item}"
            )
            return self._stored(object_id)

    def put_checkpoint(
        self, run_id: str, node_id: str, attempt: int, data: bytes, *, principal: str
    ) -> str:
        with _engine_codes():
            return self.store.put_transient(Principal.parse(principal), runs_ref(run_id), data)

    def put_agent_tool(self, run_id: str, tool: JsonObject, *, principal: str) -> Stored:
        with _engine_codes():
            fields: JsonObject = {**tool, "review": "unreviewed"}
            name = str(tool.get("name"))
            object_id = self._put(
                "agent-tool", name, runs_ref(run_id), fields, principal, title=name
            )
            return self._stored(object_id)

    def put_memory_row(self, run_id: str, row: JsonObject, *, principal: str) -> Stored:
        with _engine_codes():
            fields: JsonObject = {**row, "scope": "run"}
            object_id = self._put(
                "memory-row", str(uuid.uuid7()), runs_ref(run_id), fields, principal
            )
            return self._stored(object_id)

    def link(self, from_id: str, edge: EdgeName, to_id: str, *, principal: str) -> None:
        if edge not in EDGES:
            raise EngineRefused("edge_not_in_set", f"{edge} is not one of {sorted(EDGES)}")
        with _engine_codes():
            self.store.relate(Principal.parse(principal), from_id, edge, to_id)

    def set_champion(self, workflow_item: str, object_id: str, *, principal: str) -> None:
        with _engine_codes():
            ref = champions_ref(workflow_item)
            found = self.store.head(workflow_item, ref)
            self.store.advance(
                self.store.engine,
                workflow_item,
                ref,
                object_id,
                expected_head=None if found is None else found[0],
            )

    def annotate(self, object_id: str, key: str, value: JsonValue, *, principal: str) -> None:
        with _engine_codes():
            self.store.annotate(self.store.engine, object_id, {key: value})
