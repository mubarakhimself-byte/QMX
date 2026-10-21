"""Replication between the PC's store and the Hub's (Library AD-10, AD-11, AD-14, AD-16).

Two mechanisms, one rule each. Objects and blobs are immutable and content-addressed, so they
copy in either direction without a conflict. Refs are owned: the store named by the owner table
(AD-11, read from `[library] primary`, AD-19) is the only one that moves a ref, and the other
store mirrors it. Order is decided by parent hashes, never by a wall clock (AD-14): `order` walks
the manifests' `parents`, and a child never travels before its parent.

`plan` is pure over the two ref lists and the local ancestry, so a test proves routing and alarms
without a socket or a store. `sync` is the loop: pull, mirror, push, apply purge tombstones.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, cast

from qmx_library.client import OwnerTable, Ref
from qmx_library.store import Store


class Peer(Protocol):
    """What replication needs from a store on the other end: its refs, objects, blobs, ancestry.

    Both ends implement it: `StorePeer` in process, `qmx_library.client.HubClient` over the
    tailnet. Nothing here dials the PC; the PC is always the caller (AD-11, DEC-0497).
    """

    @property
    def name(self) -> str: ...

    def refs(self) -> list[Ref]: ...

    def object_ids(self) -> set[str]: ...

    def manifest(self, object_id: str) -> Mapping[str, Any] | None: ...

    def blob_ids(self) -> set[str]: ...

    def blob(self, blob_id: str) -> bytes | None: ...

    def store_blob(self, data: bytes) -> str: ...

    def ingest(self, manifest: Mapping[str, Any]) -> str: ...

    def mirror(self, row: Ref, *, expected_head: str | None) -> None: ...

    def ancestry(self, object_id: str) -> set[str]: ...

    def tombstone(self, blob_id: str) -> Mapping[str, Any] | None: ...

    def apply_purge(self, blob_id: str, *, reason: str, at: str) -> None: ...


class StorePeer:
    """One `Peer` over a `qmx_library.store.Store`."""

    def __init__(self, store: Store) -> None:
        self.store = store

    @property
    def name(self) -> str:
        return self.store.name

    def refs(self) -> list[Ref]:
        return [
            Ref(item, ref, head, at, principal)
            for item, ref, head, at, principal in self.store.refs()
        ]

    def object_ids(self) -> set[str]:
        return set(self.store.object_ids())

    def manifest(self, object_id: str) -> Mapping[str, Any] | None:
        try:
            return self.store.manifest(object_id)
        except Exception:
            return None

    def blob_ids(self) -> set[str]:
        return set(self.store.blob_ids())

    def blob(self, blob_id: str) -> bytes | None:
        try:
            return self.store.read_blob(blob_id)
        except Exception:
            return None

    def store_blob(self, data: bytes) -> str:
        return self.store.store_blob(data)

    def ingest(self, manifest: Mapping[str, Any]) -> str:
        return self.store.ingest(manifest)

    def mirror(self, row: Ref, *, expected_head: str | None) -> None:
        self.store.mirror(
            row.item,
            row.ref,
            row.head,
            expected_head=expected_head,
            who=row.principal or "hub",
            at=row.at or None,
        )

    def ancestry(self, object_id: str) -> set[str]:
        return self.store.ancestry_of(object_id)

    def tombstone(self, blob_id: str) -> Mapping[str, Any] | None:
        path = self.store.tombstones / f"{blob_id.removeprefix('sha256:')}.json"
        if not path.exists():
            return None
        return dict(json.loads(path.read_bytes()))

    def apply_purge(self, blob_id: str, *, reason: str, at: str) -> None:
        self.store.apply_purge(blob_id, reason=reason, at=at)


def order(manifests: Mapping[str, Sequence[str]]) -> list[str]:
    """The object ids ordered so a parent always precedes its children (AD-14).

    The only input is each manifest's `parents`; a parent already stored on the other side is
    simply not in the map and imposes no order. Ties break on the object id, so two runs of the
    same set copy in the same order. A cycle is impossible with content addressing, so one is a
    bug rather than a refusal.
    """
    children: dict[str, set[str]] = {object_id: set() for object_id in manifests}
    waiting: dict[str, int] = {}
    for object_id, parents in manifests.items():
        inside = [parent for parent in parents if parent in manifests]
        waiting[object_id] = len(inside)
        for parent in inside:
            children[parent].add(object_id)
    ready = sorted(object_id for object_id, count in waiting.items() if count == 0)
    ordered: list[str] = []
    while ready:
        current = ready.pop(0)
        ordered.append(current)
        for child in sorted(children[current]):
            waiting[child] -= 1
            if waiting[child] == 0:
                ready.append(child)
        ready.sort()
    if len(ordered) != len(manifests):
        raise ValueError("a parent cycle: content addressing cannot produce one")
    return ordered


@dataclass(frozen=True, slots=True)
class Plan:
    mirror: tuple[Ref, ...] = ()
    """Refs the other store owns: this store takes its head (AD-14)."""
    push: tuple[Ref, ...] = ()
    """Refs this store owns: the other store takes the head, by compare-and-swap."""
    alarms: tuple[str, ...] = ()
    """Refs that diverged with no ancestry between them, or a ref an owner has lost."""


def plan(
    local: Sequence[Ref],
    remote: Sequence[Ref],
    table: OwnerTable,
    *,
    name: str,
    ancestor: Callable[[str, str], bool],
) -> Plan:
    """Route every ref: mirror what the other store owns, push what this one owns.

    `ancestor(older, newer)` answers from the ref-log ancestry whether one head is behind the
    other, and is the only evidence used when the owner is `either` (a run ref belongs to the
    store that minted it). Anything else is an alarm for `adopt`, never a merge (AD-14).
    """
    mine = {(row.item, row.ref): row for row in local}
    theirs = {(row.item, row.ref): row for row in remote}
    mirror: list[Ref] = []
    push: list[Ref] = []
    alarms: list[str] = []
    for key in sorted(mine.keys() | theirs.keys()):
        here, there = mine.get(key), theirs.get(key)
        ref = key[1]
        owner = table.owner(ref)
        if owner == name:
            if here is not None and (there is None or there.head != here.head):
                push.append(here)
            elif here is None and there is not None:
                alarms.append(f"{key[0]} {ref}: this store owns it and has no head")
            continue
        if owner not in (name, "either"):
            if there is not None and (here is None or here.head != there.head):
                mirror.append(there)
            continue
        if here is not None and there is None:
            push.append(here)
        elif here is not None and there is not None and here.head != there.head:
            if ancestor(there.head, here.head):
                push.append(here)
            elif ancestor(here.head, there.head):
                mirror.append(there)
            else:
                alarms.append(f"{key[0]} {ref}: {here.head} and {there.head} have no ancestry")
    return Plan(tuple(mirror), tuple(push), tuple(alarms))


@dataclass(slots=True)
class Synced:
    pulled: list[str] = field(default_factory=list[str])
    """Objects copied here from the other store."""
    pushed: list[str] = field(default_factory=list[str])
    """Objects copied from here to the other store."""
    blobs: int = 0
    mirrored: list[str] = field(default_factory=list[str])
    """Refs the other store owns, now at its head here."""
    pushed_refs: list[str] = field(default_factory=list[str])
    """Refs this store owns, now at this head there."""
    purged: list[str] = field(default_factory=list[str])
    alarms: list[str] = field(default_factory=list[str])

    @property
    def ok(self) -> bool:
        return not self.alarms


def sync(local: Peer, remote: Peer, table: OwnerTable) -> Synced:
    """One sync: pull and mirror what the other store owns, push what this one owns, then apply
    the purge tombstones the owner recorded (AD-6, AD-14, AD-16)."""
    synced = Synced()
    routes = plan(
        local.refs(),
        remote.refs(),
        table,
        name=local.name,
        ancestor=lambda older, newer: older in _ancestry(local, newer),
    )
    synced.alarms.extend(routes.alarms)
    _copy(local, remote, synced, pull=True)
    _copy(local, remote, synced, pull=False)
    local_heads = {(row.item, row.ref): row.head for row in local.refs()}
    remote_heads = {(row.item, row.ref): row.head for row in remote.refs()}
    for row in routes.mirror:
        local.mirror(row, expected_head=local_heads.get((row.item, row.ref)))
        synced.mirrored.append(row.ref)
    for row in routes.push:
        remote.mirror(row, expected_head=remote_heads.get((row.item, row.ref)))
        synced.pushed_refs.append(row.ref)
    _apply_purges(local, remote, synced)
    return synced


def _ancestry(peer: Peer, object_id: str) -> set[str]:
    try:
        return peer.ancestry(object_id)
    except Exception:
        return set()


def _copy(local: Peer, remote: Peer, synced: Synced, *, pull: bool) -> None:
    """Copy the objects one side lacks, parents first, with the durable blobs they name."""
    source, target = (remote, local) if pull else (local, remote)
    wanted = source.object_ids() - target.object_ids()
    if not wanted:
        return
    manifests = {object_id: source.manifest(object_id) for object_id in wanted}
    present = {object_id: found for object_id, found in manifests.items() if found is not None}
    parents = {
        object_id: [str(parent) for parent in found.get("parents", [])]
        for object_id, found in present.items()
    }
    for object_id in order(parents):
        manifest = present[object_id]
        for blob_id in _blob_ids(manifest):
            if target.blob(blob_id) is not None:
                continue
            data = source.blob(blob_id)
            if data is None:
                continue
            target.store_blob(data)
            synced.blobs += 1
        copied = target.ingest(manifest)
        (synced.pulled if pull else synced.pushed).append(copied)


def _apply_purges(local: Peer, remote: Peer, synced: Synced) -> None:
    heads = {(row.item, row.ref): row.head for row in local.refs()}
    for row in remote.refs():
        if not row.ref.startswith("refs/purges/"):
            continue
        blob_id = f"sha256:{row.ref.removeprefix('refs/purges/')}"
        if local.tombstone(blob_id) is not None:
            continue
        recorded = remote.tombstone(blob_id)
        if recorded is None:
            synced.alarms.append(f"{blob_id}: a purge ref with no tombstone")
            continue
        local.apply_purge(blob_id, reason=str(recorded["reason"]), at=str(recorded["at"]))
        local.mirror(row, expected_head=heads.get((row.item, row.ref)))
        synced.purged.append(blob_id)


def _blob_ids(manifest: Mapping[str, Any]) -> Iterable[str]:
    blobs = cast(Mapping[str, Mapping[str, Any]], manifest.get("blobs") or {})
    return (str(spec["sha256"]) for spec in blobs.values())
