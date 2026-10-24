"""The flip to `primary = server`, and the procedure for losing the server (MIGRATION step 8 and
"When the server is lost"; Library AD-14, AD-16, AD-19, AD-26; DATA-PLAN DR2D, W7).

Both are the operator's acts, `user` only: an agent or a run is refused `ui_only`, because where the
Library lives is his click and never a workflow's (AD-19, G-FLIP). The two are one state machine:
every stage either happened, with its record on `refs/hub/primary`, or it did not.

The flip follows MIGRATION step 8. `announce` writes the one-button card the inbox lists; `quiesce`
opens the hold that refuses saves with `primary_moving` while reads keep working; `push_until_equal`
syncs until every ref the PC owns has the same head on both sides, which is the restore drill's
count-and-head check; then it waits. `press` is his click: it raises `refs/primary` by one epoch,
writes `[library] primary = server` and `hub_url`, and closes the card. Nothing here raises an epoch
without that press, and the seconds saves paused come off the same record.

Losing the server runs MIGRATION's six steps. Step 1 asks him to stop a reachable old host before
the PC is promoted, so its crons stop moving its own refs (N13), and the promotion raises the epoch
again with `primary = pc`. Step 2 lists every ref the server owned that the PC holds only as a
mirror, with its last sync. Step 3 rebuilds a new server from the bucket, or names exactly what is
lost without one: every durable blob born on the other store that this replica never opened, text
slots excluded, because a text slot does reach the replica (N1, F14). Steps 4 to 6 are the new
server's own key pair, a fresh pairing code and the flip back, each named and each waiting for the
caller that performs it.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal, cast

from qmx_library.kinds import kind
from qmx_library.port import Commit, Draft, LibraryRefused, ObjectId
from qmx_library.principal import Principal
from qmx_library.store import TEXT_SLOTS, Store

from qmx_control.node import flip_primary

if TYPE_CHECKING:
    from qmx_hub.replicate import Peer, Synced
    from qmx_library.client import OwnerTable

OPERATOR: Final = Principal("operator")
CARD_REF: Final = "refs/hub/primary"
"""The one-button card's ref. `refs/hub/*` is the Hub's own namespace (AD-11), where the inbox
already reads `refs/hub/health`, and a `hub` principal is the one that moves it."""
CARD_ITEM: Final = "hub-primary"
MOVE: Final = "Move the Library to the server"
HOLD: Final = "primary_moving"
"""The refusal MIGRATION step 8.2 names while the flip holds: saves pause, reads keep working."""

type Stage = Literal["waiting", "raised", "lost"]
"""`waiting` is the card the inbox shows with its one button; `raised` is the flip he pressed;
`lost` is the server-loss card, which names what a new server needs."""


@dataclass(frozen=True, slots=True)
class Card:
    """The inbox card: what it says, what its one button does, and the epoch it would raise."""

    stage: Stage
    title: str
    button: str
    epoch: int
    words: str


@dataclass(frozen=True, slots=True)
class Step:
    """One step of the server-loss procedure: its number, who does it, and whether this run did."""

    number: int
    act: str
    done: bool
    said: str = ""


@dataclass(frozen=True, slots=True)
class Lost:
    """What has one copy only, on a server that is gone (F14, N3)."""

    blobs: tuple[str, ...]
    slots: tuple[str, ...]
    said: str


@dataclass(frozen=True, slots=True)
class StaleRef:
    """A ref the server owned, that this replica holds only as a mirror, and when it last moved."""

    item: str
    ref: str
    head: str
    at: str


@dataclass(frozen=True, slots=True)
class Recovery:
    """The server-loss procedure's result: every step, the raised epoch and the two lists."""

    steps: tuple[Step, ...]
    epoch: int
    stale: tuple[StaleRef, ...] = ()
    lost: Lost | None = None
    card: Card | None = None

    @property
    def done(self) -> tuple[int, ...]:
        """The steps this run performed."""
        return tuple(step.number for step in self.steps if step.done)


@dataclass(slots=True)
class Flip:
    """MIGRATION step 8 as one run: announce, quiesce, push until equal, then his click."""

    store: Store
    peer: Peer
    home: Path
    hub_url: str
    card: Card | None = None
    held: bool = False
    paused_s: float = 0.0
    synced: Synced | None = None
    clock: Callable[[], float] = time.monotonic
    quiesced_at: float = 0.0

    @property
    def next_epoch(self) -> int:
        """The epoch a press would raise: one above the highest this store has seen (AD-14)."""
        learned = self.store.epoch
        return 1 if learned is None else learned.epoch + 1

    @property
    def table(self) -> OwnerTable:
        from qmx_library.client import OwnerTable  # noqa: PLC0415 (the PC's own role)

        return OwnerTable("pc")

    def announce(self) -> Card:
        """Step 1: the card, in plain words, before anything pauses."""
        words = (
            "Saves pause for a few minutes while the Library moves to the server. "
            "Nothing moves until you press the button."
        )
        self.card = self._card("waiting", words)
        return self.card

    def quiesce(self) -> Card:
        """Step 2: saves pause from here; reads keep working. Refused with no card announced."""
        if self.card is None or self.card.stage != "waiting":
            raise LibraryRefused("not_waiting", "there is no card to carry the flip")
        self.held = True
        self.quiesced_at = self.clock()
        return self._card(
            "waiting",
            f"Quiesced: saves are refused with {HOLD} until the PC and the server agree.",
        )

    def save(
        self, who: Principal, draft: Draft, *, on: str, expected_head: ObjectId | None = None
    ) -> Commit:
        """The save path while the flip holds: refused `primary_moving`, as step 8.2 says."""
        if self.held:
            raise LibraryRefused(HOLD, f"the Library is moving to the server; {on} waits for it")
        return self.store.put(who, draft, on=on, expected_head=expected_head)

    def equal(self) -> tuple[str, ...]:
        """The refs this store owns where the two sides still disagree: the drill's head check."""
        from qmx_hub.replicate import StorePeer  # noqa: PLC0415 (the PC's own sync)

        mine = {
            (row.item, row.ref): row.head
            for row in StorePeer(self.store).refs()
            if self.table.owner(row.ref) in ("pc", "either")
        }
        theirs = {(row.item, row.ref): row.head for row in self.peer.refs()}
        return tuple(
            sorted(
                f"{item} {ref}"
                for item, ref in mine
                if theirs.get((item, ref)) != mine[(item, ref)]
            )
        )

    def push_until_equal(self, *, tries: int = 3) -> Synced:
        """Step 3: push, and push again while a commit that raced the push is still only here."""
        from qmx_hub.replicate import StorePeer, sync  # noqa: PLC0415 (the PC's own sync)

        for _ in range(tries):
            done = sync(StorePeer(self.store), self.peer, self.table)
            if not self.equal():
                self.synced = done
                return done
        raise LibraryRefused(
            "not_equal", f"the two sides still differ on {', '.join(self.equal())}"
        )

    def press(self, who: Principal) -> Card:
        """His click: raise the epoch by one, write the settings keys and close the card."""
        if who.who != "operator":
            raise LibraryRefused("ui_only", f"{who} may not move the Library; he presses the card")
        if self.card is None or self.card.stage != "waiting":
            raise LibraryRefused("not_waiting", "no card is waiting for a press")
        if differing := self.equal():
            raise LibraryRefused(
                "not_equal", f"the two sides still differ on {', '.join(differing)}"
            )
        raised = self.store.record_primary(OPERATOR, "server")
        flip_primary(self.home, self.hub_url)
        self.paused_s = round(self.clock() - self.quiesced_at, 3) if self.held else 0.0
        self.held = False
        self.card = write_card(
            self.store,
            stage="raised",
            title="The Library moved to the server",
            button="",
            epoch=raised.epoch,
            words=f"The Library now lives on the server. Saves paused for {self.paused_s} s.",
        )
        return self.card

    def _card(self, stage: Stage, words: str) -> Card:
        """One card version that offers the button, naming the epoch that press would raise."""
        return write_card(
            self.store,
            stage=stage,
            title=MOVE,
            button=MOVE,
            epoch=self.next_epoch,
            words=words,
        )


def lost_without_a_bucket(store: Store) -> Lost:
    """Every durable blob another store born and this replica never opened, text slots excluded.

    Without a bucket a new server is rebuilt from this replica, which holds every manifest, edge,
    ref and text slot: the words come back. What does not is what this replica never fetched:
    originals, page images, recordings, run logs, model weights (F14, N3). A transient slot has no
    second copy by definition, so it is not named as lost.
    """
    named: dict[str, set[str]] = {}
    for object_id in sorted(store.object_ids()):
        manifest = store.manifest(object_id) or {}
        spec = kind(str(manifest.get("kind") or "note"))
        blobs = cast("Mapping[str, Mapping[str, object]]", manifest.get("blobs") or {})
        for slot, blob in blobs.items():
            try:
                media = spec.slot(str(slot))
            except LibraryRefused:
                continue
            if media.transient or media.pattern in TEXT_SLOTS:
                continue
            blob_id = str(blob["sha256"])
            if not store.has_blob(blob_id):
                named.setdefault(blob_id, set()).add(str(slot))
    slots = tuple(sorted({slot for found in named.values() for slot in found}))
    if not named:
        said = "nothing is lost: every durable blob this Library names was opened on the PC"
    else:
        said = (
            f"blobs born on the server and never opened on the PC, now lost: {len(named)} "
            f"({', '.join(slots)}); their Library entries stay and their text is on the PC"
        )
    return Lost(tuple(sorted(named)), slots, said)


def server_lost(
    store: Store,
    *,
    who: Principal,
    reachable: bool = False,
    bucket: bool = False,
    rebuild: Callable[[], Mapping[str, object]] | None = None,
    repair: Callable[[], str] | None = None,
) -> Recovery:
    """MIGRATION's "When the server is lost", steps 1 to 6, as one run.

    `reachable` asks him to stop an old host that still answers before the PC is promoted (N13);
    `bucket` picks step 3's branch; `rebuild` is the caller's rebuild of a new server (a bucket
    restore, or a full sync from this replica) and `repair` its fresh pairing. Every step is named
    whether or not this run performed it, so the card says what is still his to do.
    """
    if who.who != "operator":
        raise LibraryRefused("ui_only", f"{who} may not promote the PC; his click does")
    raised = store.record_primary(OPERATOR, "pc")
    steps: list[Step] = [
        Step(
            1,
            "Promote the PC, after asking him to stop a reachable old host",
            True,
            "Stop the old host first: its crons keep moving its own refs until it stops."
            if reachable
            else "The old host does not answer, so there is nothing to stop.",
        )
    ]
    stale = _stale(store)
    steps.append(
        Step(
            2,
            "Say what may be behind: every ref the server owned that the PC holds as a mirror",
            True,
            f"refs the server owned that may be behind: {len(stale)}; the inbox shows them",
        )
    )
    lost: Lost | None = None if bucket else lost_without_a_bucket(store)
    said = ""
    done = False
    if rebuild is not None:
        said, done = str(rebuild()), True
    elif bucket:
        said = "the bucket holds the evidence; no bucket remote is configured on this PC"
    if lost is not None:
        said, done = f"{said}; {lost.said}" if said else lost.said, True
    steps.append(
        Step(
            3,
            "Rebuild a new server from the bucket, then name what has one copy only",
            done,
            said,
        )
    )
    steps.append(
        Step(
            4,
            "Give the new server its own key pair and seal the replicable entries to it",
            False,
            "model keys, qmx/read/* and qmx/data/* are sealed again; a server-homed connection "
            "needs one new sign-in, because its tokens lived only there",
        )
    )
    steps.append(
        Step(
            5,
            "Re-pair the server with a fresh pairing code and sync until the ref logs agree",
            repair is not None,
            repair() if repair is not None else "a fresh pairing code is written on both ends",
        )
    )
    steps.append(
        Step(
            6,
            "Flip back when he chooses: the same six steps of step 8, raising the epoch again",
            False,
            f"the PC is primary at epoch {raised.epoch} until then",
        )
    )
    card = write_card(
        store,
        stage="lost",
        title="The server is gone",
        button="",
        epoch=raised.epoch,
        words=lost.said if lost is not None else "a new server is rebuilt from the bucket",
    )
    return Recovery(tuple(steps), raised.epoch, stale, lost, card)


def write_card(
    store: Store, *, stage: Stage, title: str, button: str, epoch: int, words: str
) -> Card:
    """One card version on `refs/hub/primary`, written as the Hub, the ref's own principal."""
    found = store.head(CARD_ITEM, CARD_REF)
    store.put(
        Principal("hub"),
        Draft(
            "note",
            CARD_ITEM,
            title=title,
            summary=words,
            fields={"stage": stage, "button": button, "epoch": epoch, "words": words},
        ),
        on=CARD_REF,
        expected_head=None if found is None else found[0],
    )
    return Card(stage, title, button, epoch, words)


def _stale(store: Store) -> tuple[StaleRef, ...]:
    """Every ref the server owned that this replica holds, with the time it last moved here."""
    found = [
        StaleRef(item, ref, head, at)
        for item, ref, head, at, _principal in store.refs()
        if _server_owns(ref)
    ]
    return tuple(sorted(found, key=lambda row: (row.ref, row.item)))


def _server_owns(ref: str) -> bool:
    from qmx_library.client import OwnerTable  # noqa: PLC0415 (the PC's own role)

    return OwnerTable("server").owner(ref) == "server"
