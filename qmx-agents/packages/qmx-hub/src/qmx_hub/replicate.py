"""Replication between the PC's store and the Hub's (Library AD-10, AD-11, AD-14, AD-16, AD-26).

Two mechanisms, one rule each. Objects and blobs are immutable and content-addressed, so they
copy in either direction without a conflict. Refs are owned: the store named by the owner table
(AD-11, read from `[library] primary`, AD-19) is the only one that moves a ref, and the other
store mirrors it. Order is decided by parent hashes, never by a wall clock (AD-14): `order` walks
the manifests' `parents`, and a child never travels before its parent.

`plan` is pure over the two ref lists and the local ancestry, so a test proves routing and alarms
without a socket or a store. A push of a ref this store owns is fast-forward only: a peer head
that is not an ancestor of ours is an alarm, never an overwrite.

`sync` is the whole store, which is what the first copy of a store needs. `sync_since` is the
selective sync of AD-10 (F10, F18, N1): it asks for the ref moves after a sequence, pulls the
manifests and edges those moves name, copies their text-slot blobs and no other blob, and moves
its cursor. `Synchroniser` makes one sync run at a time and coalesces a burst of commits into the
next one.

Both syncs read the other store's epoch record first. A higher epoch is learned before any push is
judged, so a PC restored from an older backup stops acting as primary, parks the moves it made as
primary and pushes nothing (AD-14, F12, F15, N13, N19).
"""

from __future__ import annotations

import json
import threading
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any, Protocol, cast

from qmx_library.client import Move, OwnerTable, Ref
from qmx_library.store import PRIMARY_ITEM, PRIMARY_REF, Epoch, Store, text_blob_ids


class Peer(Protocol):
    """What replication needs from a store on the other end: its refs, objects, blobs, ancestry.

    Both ends implement it: `StorePeer` in process, `qmx_library.client.HubClient` over the
    tailnet. Nothing here dials the PC; the PC is always the caller (AD-11, DEC-0497).
    """

    @property
    def name(self) -> str: ...

    def refs(self) -> list[Ref]: ...

    def moves(self, after: int) -> list[Move]: ...

    def versions(self) -> Mapping[str, int]: ...

    def alarms(self) -> tuple[str, ...]: ...

    def edges_since(self, after: int) -> list[dict[str, Any]]: ...

    def ingest_edge(self, edge: Mapping[str, Any]) -> bool: ...

    def object_ids(self) -> set[str]: ...

    def has_object(self, object_id: str) -> bool: ...

    def manifest(self, object_id: str) -> Mapping[str, Any] | None: ...

    def blob_ids(self) -> set[str]: ...

    def has_blob(self, blob_id: str) -> bool: ...

    def blob(self, blob_id: str) -> bytes | None: ...

    def store_blob(self, data: bytes) -> str: ...

    def ingest(self, manifest: Mapping[str, Any]) -> str: ...

    def mirror(self, row: Ref, *, expected_head: str | None) -> None: ...

    def ancestry(self, object_id: str) -> set[str]: ...

    def tombstone(self, blob_id: str) -> Mapping[str, Any] | None: ...

    def apply_purge(self, blob_id: str, *, reason: str, at: str) -> None: ...


class Learner(Peer, Protocol):
    """The side of a sync that can learn an epoch: the PC's store, which is always the caller.

    The Hub is only ever the other end, and it never learns an epoch from a PC (AD-11, DEC-0497).
    """

    def epoch(self) -> Epoch | None: ...

    def learn_epoch(self, other: Epoch, *, shared_seq: int | None = None) -> Epoch: ...


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

    def moves(self, after: int) -> list[Move]:
        return [
            Move(
                int(row["seq"]),
                str(row["item"]),
                str(row["ref"]),
                str(row["new_head"]),
                str(row["kind"]),
            )
            for row in self.store.placements(after)
        ]

    def versions(self) -> Mapping[str, int]:
        return self.store.versions()

    def alarms(self) -> tuple[str, ...]:
        return self.store.alarms

    def edges_since(self, after: int) -> list[dict[str, Any]]:
        return self.store.edges_since(after)

    def ingest_edge(self, edge: Mapping[str, Any]) -> bool:
        return self.store.ingest_edge(edge)

    def object_ids(self) -> set[str]:
        return set(self.store.object_ids())

    def has_object(self, object_id: str) -> bool:
        return self.store.has_object(object_id)

    def manifest(self, object_id: str) -> Mapping[str, Any] | None:
        try:
            return self.store.manifest(object_id)
        except Exception:
            return None

    def blob_ids(self) -> set[str]:
        return set(self.store.blob_ids())

    def has_blob(self, blob_id: str) -> bool:
        return self.store.has_blob(blob_id)

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

    def epoch(self) -> Epoch | None:
        return self.store.epoch

    def learn_epoch(self, other: Epoch, *, shared_seq: int | None = None) -> Epoch:
        return self.store.learn_epoch(other, shared_seq=shared_seq)


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
    store that minted it) and for a push of a ref this store owns: that push is fast-forward
    only, so a peer head that is not an ancestor of ours is an alarm, never an overwrite
    (AD-14, F11, F15). Anything else is an alarm for `adopt`, never a merge.
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
                if there is None or ancestor(there.head, here.head):
                    push.append(here)
                else:
                    alarms.append(
                        f"{key[0]} {ref}: {there.head} is not an ancestor of {here.head}; "
                        "a push of an owned ref is fast-forward only"
                    )
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
    cursor: int = 0
    """The ref-log sequence this sync read to; the next selective sync asks from here."""
    edges: int = 0
    """After-birth edges recorded here from the other store."""
    text_blobs: int = 0
    """Text-slot blobs copied. A selective sync copies no other blob (AD-10, N1)."""
    needs_update: list[str] = field(default_factory=list[str])
    """Objects or entries left alone because this store lacks their kind or schema version."""

    @property
    def ok(self) -> bool:
        return not self.alarms


def sync(local: Learner, remote: Peer, table: OwnerTable) -> Synced:
    """One sync of everything: pull and mirror what the other store owns, push what this one
    owns, then apply the purge tombstones the owner recorded (AD-6, AD-14, AD-16)."""
    synced = Synced()
    routes = plan(
        local.refs(),
        remote.refs(),
        table,
        name=local.name,
        ancestor=lambda older, newer: older in _ancestry(local, newer),
    )
    synced.alarms.extend(routes.alarms)
    _learn_higher_epoch(local, remote)
    _copy(local, remote, synced, pull=True)
    _copy(local, remote, synced, pull=False)
    local_heads = {(row.item, row.ref): row.head for row in local.refs()}
    for row in routes.mirror:
        local.mirror(row, expected_head=local_heads.get((row.item, row.ref)))
        synced.mirrored.append(row.ref)
    _push(local, remote, routes, synced)
    _apply_purges(local, remote, synced)
    return synced


def sync_since(local: Learner, remote: Peer, table: OwnerTable, *, cursor: int) -> Synced:
    """One selective sync of what moved after `cursor` (AD-10, F10, F18, N1).

    It reads the other store's ref-log tail instead of its object ids, ingests the manifests and
    after-birth edges those rows name, copies each manifest's text slots and no other blob, and
    stops at the sequence it read. Every other blob of a pulled object reaches this store only
    when something here opens it. A manifest whose kind or schema version this store lacks is
    left for a host that can read it, and `refs` is still mirrored so the ref name is not lost.
    It learns the other store's epoch before it judges any push (AD-14).
    """
    synced = Synced()
    routes = plan(
        local.refs(),
        remote.refs(),
        table,
        name=local.name,
        ancestor=lambda older, newer: older in _ancestry(local, newer),
    )
    synced.alarms.extend(routes.alarms)
    _learn_higher_epoch(local, remote)
    moves = remote.moves(cursor)
    _pull_moves(local, remote, moves, synced)
    synced.edges = _pull_edges(local, remote, cursor)
    local_heads = {(row.item, row.ref): row.head for row in local.refs()}
    for row in routes.mirror:
        local.mirror(row, expected_head=local_heads.get((row.item, row.ref)))
        synced.mirrored.append(row.ref)
    _push(local, remote, routes, synced)
    _apply_purges(local, remote, synced)
    synced.cursor = max([cursor, *(move.seq for move in moves)])
    return synced


def peer_epoch(remote: Peer) -> Epoch | None:
    """The epoch record the other store holds on `refs/primary`, or None when it holds none.

    The record is one object on that ref, so this reads it with the verbs every peer already
    has: no extra route, and no extra trust (AD-14, DEC-0497).
    """
    for row in remote.refs():
        if (row.item, row.ref) != (PRIMARY_ITEM, PRIMARY_REF):
            continue
        found = remote.manifest(row.head)
        if found is None:
            return None
        fields = cast(Mapping[str, Any], found.get("fields") or {})
        try:
            return Epoch(str(fields["primary"]), int(fields["epoch"]))
        except KeyError, TypeError, ValueError:
            return None
    return None


def _learn_higher_epoch(local: Learner, remote: Peer) -> None:
    """Take the other store's epoch when it is above this one's, once per learning (AD-14).

    The record names the primary and the epoch and no shared ref-log sequence, so a store that
    learns one parks every move it made as primary, which is the safe side of N13 and N19. Learned
    before any push is judged, the epoch governs this sync's push and every later one.
    """
    theirs = peer_epoch(remote)
    if theirs is None:
        return
    known = local.epoch()
    if known is not None and known.epoch >= theirs.epoch:
        return
    local.learn_epoch(theirs, shared_seq=theirs.seq)


def _push(local: Peer, remote: Peer, routes: Plan, synced: Synced) -> None:
    """Push the refs this store owns, unless it learned that it is not the primary (AD-14)."""
    if stale := stale_primary(local):
        synced.alarms.append(f"{stale}: this store is not the primary, so no ref is pushed")
        return
    if not routes.push:
        return
    remote_heads = {(row.item, row.ref): row.head for row in remote.refs()}
    for row in routes.push:
        remote.mirror(row, expected_head=remote_heads.get((row.item, row.ref)))
        synced.pushed_refs.append(row.ref)


def _pull_moves(
    local: Peer,
    remote: Peer,
    moves: Sequence[Move],
    synced: Synced,
) -> None:
    """Ingest the objects the moves name, parents first, and their text slots only."""
    wanted = [move for move in moves if not local.has_object(move.head)]
    manifests: dict[str, Mapping[str, Any]] = {}
    for move in wanted:
        found = remote.manifest(move.head)
        if found is not None:
            manifests[move.head] = found
    parents = {
        object_id: [str(parent) for parent in found.get("parents", [])]
        for object_id, found in manifests.items()
    }
    version_of = {move.head: move.kind for move in wanted}
    for object_id in order(parents):
        manifest = manifests[object_id]
        kind_name = str(manifest.get("kind") or version_of.get(object_id, ""))
        schema_version = int(manifest.get("schema_version") or 0)
        if kind_name and not _readable(local, kind_name, schema_version):
            synced.needs_update.append(
                f"{object_id} {kind_name}@{schema_version} (this PC needs updating)"
            )
            continue
        for blob_id in sorted(text_blob_ids(manifest)):
            if local.has_blob(blob_id):
                continue
            data = remote.blob(blob_id)
            if data is None:
                continue
            local.store_blob(data)
            synced.text_blobs += 1
        synced.pulled.append(local.ingest(manifest))


def _readable(peer: Peer, kind_name: str, version: int) -> bool:
    """Whether this store has that kind at that schema version or newer (AD-14, N17)."""
    known = peer.versions().get(kind_name)
    return known is not None and int(known) >= version


def _pull_edges(local: Peer, remote: Peer, cursor: int) -> int:
    """Record the after-birth edges the other store made after `cursor`, once each."""
    added = 0
    for edge in remote.edges_since(cursor):
        if local.ingest_edge(edge):
            added += 1
    return added


@dataclass(slots=True)
class Synchroniser:
    """One sync at a time, and a burst of commits coalesces into the next one (AD-10).

    A commit asks for a sync. When one is already running the request is remembered rather than
    queued twice, so a hundred saves in a second cost one extra sync, never a hundred.
    """

    run: Callable[[], Synced]
    _running: threading.Lock = field(default_factory=threading.Lock)
    _again: bool = False
    _coalesced: int = 0

    def request(self) -> Synced | None:
        """Run one sync, or None when one is already running and this request was folded in."""
        if not self._running.acquire(blocking=False):
            self._again = True
            self._coalesced += 1
            return None
        try:
            return self.run()
        finally:
            self._running.release()

    @property
    def coalesced(self) -> int:
        """How many requests were folded into a sync already running."""
        return self._coalesced

    @property
    def folded(self) -> bool:
        """Whether a commit arrived while the last sync ran, so another one is due."""
        return self._again

    def done(self) -> None:
        self._again = False


def stale_primary(peer: Peer) -> str | None:
    """The epoch alarm a store raised, when it learned a higher epoch than its own (AD-14).

    Such a store stops acting as primary at once, so it pushes nothing: the moves it made as
    primary are already parked as conflicts and he decides (N13, N19).
    """
    return next((found for found in peer.alarms() if found.startswith("library:epoch:")), None)


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
            if target.has_blob(blob_id):
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
