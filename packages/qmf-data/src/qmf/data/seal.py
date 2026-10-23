"""CT-12 seal — the newest no-peek holdout lock, enforced at every read boundary (AC4-AC6).

The newest sealed window (``registry:historical_holdout_months``, approximately twelve
months) is a **no-peek lock, not retention** — all history is kept regardless (DEC-0044,
DEC-0119). This module enforces it: a read whose position falls at or after the frozen seal
boundary is a ``policy rejection`` at **every** qmf-data read boundary — raw archive,
processed, split-governed research door, and restored backups alike — never a silent empty
result, and enforced now, independent of the deferred look-ahead and attempt-counter gates
(GAP-0016/GAP-0017, DEC-0121).

Three things this module pins down.

**The seal is a frozen boundary consumed as configuration (AC4, AC5; DEC-0119).** A
:class:`HoldoutSeal` carries the frozen seal :class:`~qmf.data.splits.SplitBoundary` (a
:class:`~qmf.core.TradingDate` in the ratified shape), the pinned calendar identity, the
world it is instantiated for, and ``holdout_months`` — the value of
``registry:historical_holdout_months``, taken as configuration and **never hardcoded** here.
The boundary is stored verbatim and never re-derived under a later tzdata version.

**Enforcement is a refusal, never a silent empty (AC4, AC5).** :meth:`HoldoutSeal.guard`
refuses a sealed read at a named :class:`ReadBoundary` with a ``policy rejection``; a row
carrying a calendar identity different from the pinned one is refused (``policy rejection``),
never rescaled.

**Exactly one authorized final look, never a silent recycle (AC6; DEC-0119).**
:meth:`HoldoutSeal.authorize_final_look` journals the one permitted look as a named
``control action`` subtype (:data:`FINAL_LOOK_SUBTYPE`) in CT-13, and refuses a second: the
sealed set is never silently recycled into research, and the look does not unseal it.

Stdlib + qmf-core + the qmf-data splits vocabulary and store journal seam.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from qmf.core import (
    CalendarIdentity,
    Fingerprint,
    Instant,
    Ok,
    Result,
    TemporalOrder,
    TypedRefusal,
    World,
    WriterId,
    is_ok,
    is_refusal,
)
from qmf.data.splits import CONTRACT_FORMAT_VERSION, SplitBoundary, SplitManifest
from qmf.data.store import JournalStore, StoreReceipt
from qmf.data.store.refusals import invalid_input, policy_rejection

__all__ = [
    "FINAL_LOOK_SUBTYPE",
    "SEAL_CONTROL_STREAM",
    "SEAL_MOVE_SUBTYPE",
    "HoldoutSeal",
    "OperatorClick",
    "ReadBoundary",
]

# The CT-13 control-action subtype name for the sealed-period final look (DEC-0119). A
# named subtype, so a projection selects on a declared field, never on key presence.
FINAL_LOOK_SUBTYPE: Final[str] = "sealed-period-final-look"

# The CT-13 control-action subtype name for a seal moved by his click (55 D-5; F8).
SEAL_MOVE_SUBTYPE: Final[str] = "sealed-period-move"

# The default CT-13 stream name qmf-data writes its control-action events to. qmf-data is a
# wired producer of the control-action event type (DEC-0116); one writer owns the stream.
SEAL_CONTROL_STREAM: Final[str] = "qmf-data-control-action"

# The CT-13 control-action event-type value (the seal's final look is a control action).
_CONTROL_ACTION_EVENT: Final[str] = "control action"


class ReadBoundary(StrEnum):
    """The qmf-data read boundaries the seal is enforced at (AC4; DEC-0119).

    The seal is a no-peek lock at **every** read boundary — the immutable raw archive, the
    processed room, the split-governed research door, and a restored backup alike — so a
    sealed read is refused identically wherever it is attempted, never a silent empty result.
    """

    RAW_ARCHIVE = "raw archive"
    PROCESSED = "processed"
    RESEARCH_DOOR = "split-governed research door"
    RESTORED_BACKUP = "restored backup"


def _as_instant(value: object) -> Instant | None:
    """Resolve ``value`` to an :class:`~qmf.core.Instant`, or ``None``."""
    if isinstance(value, Instant):
        return value
    built = Instant.try_create(value)
    return built.value if is_ok(built) else None


def _coerce_split_id(value: object) -> str | None:
    """Resolve an optional split id to its ``fp1:sha256:<hex>`` string, or ``None``."""
    if isinstance(value, Fingerprint):
        return value.value
    if isinstance(value, str) and value.strip() != "":
        return value
    return None


@dataclass(frozen=True, slots=True)
class OperatorClick:
    """The operator's own click on the seal, and the only thing that moves it (55 D-5; F8).

    The host mints one on its operator route, where the principal is ``user``; a chat, a run
    or a workflow is another principal there and never reaches this constructor. It carries
    who clicked and when, so the journal entry says both.
    """

    at: Instant
    principal: str = "user"

    @classmethod
    def try_create(cls, at: object, principal: object = "user") -> Result[OperatorClick]:
        """Build the click for an operator route, refusing any other principal."""
        at_instant = _as_instant(at)
        if at_instant is None:
            return invalid_input(
                "at", "his click carries the Instant it happened at", given=repr(at)
            )
        if principal != "user":
            return policy_rejection(
                "principal",
                "the seal moves only by his click; this caller is not the operator",
                given=repr(principal),
            )
        return Ok(cls(at=at_instant, principal="user"))


@dataclass(frozen=True, slots=True)
class HoldoutSeal:
    """The newest sealed no-peek window, enforced at every read boundary (AC4, AC5, AC6).

    ``seal_boundary`` is the **frozen** boundary marking the newest sealed window — stored
    verbatim, never re-derived under a later tzdata version. ``calendar_identity`` is the one
    identity the seal (and its manifest) pins, so a row of a different identity is refused,
    never rescaled. ``world`` is the world the seal is instantiated for. ``holdout_months`` is
    the configured window length (``registry:historical_holdout_months``), carried as
    provenance and journaled with the final look; it is **never hardcoded** here.
    """

    seal_boundary: SplitBoundary
    calendar_identity: CalendarIdentity
    world: World
    holdout_months: int

    @classmethod
    def try_create(
        cls,
        *,
        seal_boundary: object,
        calendar_identity: object,
        world: object,
        holdout_months: object,
    ) -> Result[HoldoutSeal]:
        """Validate and build a :class:`HoldoutSeal`, returning value-or-refusal.

        ``seal_boundary`` is a :class:`~qmf.data.splits.SplitBoundary`; ``calendar_identity``
        a :class:`~qmf.core.CalendarIdentity`; ``world`` a :class:`~qmf.core.World`;
        ``holdout_months`` a positive integer taken from ``registry:historical_holdout_months``
        (never a hardcoded literal). A trading-date seal boundary must carry the pinned
        calendar identity — a foreign one is a ``policy rejection`` (AC5). Anything else is an
        ``invalid input`` refusal naming the offending field.
        """
        if not isinstance(seal_boundary, SplitBoundary):
            return invalid_input(
                "seal_boundary",
                "the seal boundary is a frozen SplitBoundary (a TradingDate or Instant)",
                given=repr(seal_boundary),
            )
        if not isinstance(calendar_identity, CalendarIdentity):
            return invalid_input(
                "calendar_identity",
                "the seal pins a qmf-core CalendarIdentity (rule set + version + tzdata)",
                given=repr(calendar_identity),
            )
        boundary_calendar = seal_boundary.calendar_identity
        if boundary_calendar is not None and boundary_calendar != calendar_identity:
            return policy_rejection(
                "seal_boundary",
                "the seal boundary carries a calendar identity different from the pinned one; "
                "it is refused, never rescaled (DEC-0106, DEC-0119)",
                pinned=repr(calendar_identity),
                given=repr(boundary_calendar),
            )
        resolved_world = _coerce_world(world)
        if resolved_world is None:
            return invalid_input(
                "world",
                "world is one of the closed set live | replay | simulated",
                given=repr(world),
            )
        if (
            isinstance(holdout_months, bool)
            or not isinstance(holdout_months, int)
            or holdout_months < 1
        ):
            return invalid_input(
                "holdout_months",
                "holdout_months is a positive integer from registry:historical_holdout_months, "
                "consumed as configuration and never hardcoded (DEC-0119)",
                given=repr(holdout_months),
            )
        return Ok(
            cls(
                seal_boundary=seal_boundary,
                calendar_identity=calendar_identity,
                world=resolved_world,
                holdout_months=holdout_months,
            )
        )

    @classmethod
    def from_manifest(cls, manifest: object, holdout_months: object) -> Result[HoldoutSeal]:
        """Build a :class:`HoldoutSeal` from a :class:`~qmf.data.splits.SplitManifest` (AC4).

        Takes the manifest's frozen seal boundary, pinned calendar identity, and world, plus
        the configured ``holdout_months``. A non-manifest argument is an ``invalid input``
        refusal.
        """
        if not isinstance(manifest, SplitManifest):
            return invalid_input(
                "manifest",
                "a seal is built from a SplitManifest (its frozen seal boundary and calendar)",
                given=repr(manifest),
            )
        return cls.try_create(
            seal_boundary=manifest.seal_boundary,
            calendar_identity=manifest.calendar_identity,
            world=manifest.world,
            holdout_months=holdout_months,
        )

    def is_sealed(self, position: object) -> Result[bool]:
        """Whether a read ``position`` falls in the sealed no-peek window (AC4, AC5).

        ``position`` is a :class:`~qmf.data.splits.SplitBoundary` (the knowledge position of
        the read). A position carrying a calendar identity different from the pinned one is a
        ``policy rejection``, never rescaled (AC5); a cross-kind comparison (an instant read
        against a trading-date seal) is an ``invalid input`` refusal. A position at or after
        the frozen seal boundary is sealed.
        """
        if not isinstance(position, SplitBoundary):
            return invalid_input(
                "position",
                "a read position is a SplitBoundary (a TradingDate or Instant)",
                given=repr(position),
            )
        denied = self._require_calendar(position.calendar_identity)
        if denied is not None:
            return denied
        order = position.compare(self.seal_boundary)
        if is_refusal(order):
            return order
        return Ok(order.value in (TemporalOrder.AFTER, TemporalOrder.EQUAL))

    def guard(self, position: object, *, boundary: object) -> Result[SplitBoundary]:
        """Refuse a read into the sealed window at a named read boundary (AC4).

        ``boundary`` is a :class:`ReadBoundary`. A sealed position is a ``policy rejection``
        naming the boundary — the seal is enforced identically at the raw archive, processed
        room, research door, and restored backups, never returned as a silent empty result
        (DEC-0119, SCN-0003). A non-sealed position returns ``Ok(position)`` so the read may
        proceed. Enforced now, independent of the deferred GAP-0016/0017 gates (DEC-0121).
        """
        if not isinstance(boundary, ReadBoundary):
            return invalid_input(
                "boundary",
                "the read boundary is one of the closed ReadBoundary set",
                given=repr(boundary),
                allowed=[member.value for member in ReadBoundary],
            )
        if not isinstance(position, SplitBoundary):
            return invalid_input(
                "position",
                "a read position is a SplitBoundary (a TradingDate or Instant)",
                given=repr(position),
            )
        sealed = self.is_sealed(position)
        if is_refusal(sealed):
            return sealed
        if sealed.value:
            return policy_rejection(
                "seal",
                f"a read into the sealed no-peek window is refused at the {boundary.value} "
                "boundary; sealed rows are never returned as a silent empty result, and the "
                "seal is enforced independent of the deferred look-ahead gates "
                "(DEC-0119, DEC-0121)",
                boundary=boundary.value,
                seal_boundary=self.seal_boundary.label(),
                gap="GAP-0016",
            )
        return Ok(position)

    def guard_read(self, position: object, *, boundary: object) -> Result[None]:
        """Guard a store read boundary against the seal, coercing store-neutral inputs (AC4).

        The store seam consults the seal through this method — it is the
        :class:`~qmf.data.store.rooms.ReadSeal` seam — so the dependency-free store never
        imports the CT-12 ``ReadBoundary`` / ``SplitBoundary`` vocabulary (M3). ``boundary``
        is the boundary's own :class:`ReadBoundary` (or its value string); ``position`` is
        the read's knowledge position as a :class:`~qmf.data.splits.SplitBoundary`, an
        :class:`~qmf.core.Instant`, or an int64 UTC-nanosecond count. A sealed position is a
        ``policy rejection`` naming the boundary — never a silent empty result — and a
        non-sealed position returns ``Ok(None)`` so the read proceeds. An unknown boundary,
        or a position that is not a resolvable boundary, is an ``invalid input`` refusal.
        """
        resolved_boundary = _coerce_read_boundary(boundary)
        if resolved_boundary is None:
            return invalid_input(
                "boundary",
                "the read boundary is one of the closed ReadBoundary set",
                given=repr(boundary),
                allowed=[member.value for member in ReadBoundary],
            )
        resolved_position = _coerce_position(position)
        if is_refusal(resolved_position):
            return resolved_position
        guarded = self.guard(resolved_position.value, boundary=resolved_boundary)
        if is_refusal(guarded):
            return guarded
        return Ok(None)

    def authorize_final_look(
        self,
        journal: object,
        writer: object,
        *,
        at: object,
        split_id: object | None = None,
        correlation_id: object | None = None,
        stream_name: str = SEAL_CONTROL_STREAM,
    ) -> Result[StoreReceipt]:
        """Journal the one authorized final look at the sealed period (AC6; DEC-0119).

        The sealed period is entitled to exactly one authorized final look. This journals it
        as the named ``control action`` subtype :data:`FINAL_LOOK_SUBTYPE` on the CT-13
        ``journal`` stream, so a projection selects it on a declared field. A **second** look
        at the same seal is a ``policy rejection`` — the sealed set is never silently recycled
        into research, and the look does not unseal it. A storage failure surfaces from the
        journal seam unchanged.

        ``journal`` is a :class:`~qmf.data.store.JournalStore` for the seal's world; ``writer``
        the AD-8 :class:`~qmf.core.WriterId` holding the stream; ``at`` the look's event
        instant; ``split_id`` and ``correlation_id`` optional annotations.
        """
        if not isinstance(journal, JournalStore):
            return invalid_input(
                "journal",
                "the final look is journaled through a CT-13 JournalStore",
                given=repr(journal),
            )
        if not isinstance(writer, WriterId):
            return invalid_input(
                "writer",
                "the final look is written under an AD-8 WriterId",
                given=repr(writer),
            )
        at_instant = _as_instant(at)
        if at_instant is None:
            return invalid_input(
                "at",
                "the final look carries an event Instant (or int64 UTC ns)",
                given=repr(at),
            )
        resolved_split_id: str | None = None
        if split_id is not None:
            resolved_split_id = _coerce_split_id(split_id)
            if resolved_split_id is None:
                return invalid_input(
                    "split_id",
                    "split_id, when given, is a manifest fp1:sha256:<hex> id (or Fingerprint)",
                    given=repr(split_id),
                )
        existing = journal.read_stream(stream_name, for_world=self.world)
        if is_refusal(existing):
            return existing
        already = self._existing_final_look(existing.value)
        if already is not None:
            return already
        event = self._final_look_event(
            writer, at_instant, split_id=resolved_split_id, correlation_id=correlation_id
        )
        return journal.append(stream_name, writer, event)

    def fingerprint_label(self) -> str:
        """The seal's stable label — the frozen boundary's label (for logging/journaling)."""
        return self.seal_boundary.label()

    def move(
        self,
        journal: object,
        writer: object,
        *,
        at: object,
        click: object,
        boundary: object,
        correlation_id: object | None = None,
        stream_name: str = SEAL_CONTROL_STREAM,
    ) -> Result[StoreReceipt]:
        """Move the seal to a new boundary on his click, journaled (55 D-5; F8).

        The seal never moves by itself, by a run or by an agent: ``click`` is an
        :class:`OperatorClick`, minted by the host's own operator route. The move is a named
        CT-13 ``control action`` subtype, so the journal, not a settings file, records where
        the seal stood, when it moved and by whose click.
        """
        if not isinstance(click, OperatorClick):
            return policy_rejection(
                "click",
                "the seal moves only by his click; a run or an agent may not move it",
                given=repr(click),
            )
        if not isinstance(journal, JournalStore):
            return invalid_input(
                "journal",
                "the seal's move is journaled through a CT-13 JournalStore",
                given=repr(journal),
            )
        if not isinstance(writer, WriterId):
            return invalid_input(
                "writer", "the seal's move is written under an AD-8 WriterId", given=repr(writer)
            )
        at_instant = _as_instant(at)
        if at_instant is None:
            return invalid_input(
                "at", "the seal's move carries an event Instant (or int64 UTC ns)", given=repr(at)
            )
        built = SplitBoundary.try_create(boundary)
        if is_refusal(built):
            return built
        moved_to = built.value
        denied = self._require_calendar(moved_to.calendar_identity)
        if denied is not None:
            return denied
        event: dict[str, object] = {
            "event_type": _CONTROL_ACTION_EVENT,
            "control_action_subtype": SEAL_MOVE_SUBTYPE,
            "instant_ns": at_instant.value_ns,
            "world": self.world.value,
            "seal_boundary": self.seal_boundary.label(),
            "sealed_boundary": moved_to.label(),
            "holdout_months": self.holdout_months,
            "writer": {
                "machine": writer.machine,
                "role": writer.role,
                "stream": writer.stream,
                "boot_epoch_id": writer.boot_epoch_id,
            },
            "format_version": CONTRACT_FORMAT_VERSION,
        }
        if isinstance(correlation_id, str) and correlation_id.strip() != "":
            event["correlation_id"] = correlation_id
        return journal.append(stream_name, writer, event)

    def outgrown(self, sealed_months: object) -> Result[bool]:
        """Whether the sealed span has outgrown ``historical_holdout_months`` (F8, N15).

        ``sealed_months`` is the count of sealed months the store holds, read from the
        partitions themselves. The span is a property of where the seal stands, so the door
        asks this and files one inbox task when it is true; nothing widens the window here.
        """
        if isinstance(sealed_months, bool) or not isinstance(sealed_months, int):
            return invalid_input(
                "sealed_months",
                "the sealed span is a count of months read from the store",
                given=repr(sealed_months),
            )
        if sealed_months < 0:
            return invalid_input(
                "sealed_months", "a sealed span is never negative", given=repr(sealed_months)
            )
        return Ok(sealed_months > self.holdout_months)

    def overdue_task(
        self, sealed_months: object, *, at: object
    ) -> Result[dict[str, object] | None]:
        """The inbox task when the sealed span outgrew its setting, else ``None`` (F8, N15).

        One task, with the numbers that raised it, so the decision to widen the window or move
        the seal stays his. ``at`` is when the reading was taken.
        """
        outgrown = self.outgrown(sealed_months)
        if is_refusal(outgrown):
            return outgrown
        if not outgrown.value:
            return Ok(None)
        if not isinstance(sealed_months, int):
            return invalid_input(
                "sealed_months",
                "the sealed span is a count of months read from the store",
                given=repr(sealed_months),
            )
        at_instant = _as_instant(at)
        if at_instant is None:
            return invalid_input(
                "at", "the reading carries an Instant (or int64 UTC ns)", given=repr(at)
            )
        task: dict[str, object] = {
            "reason": "seal:span-outgrown",
            "needs_you": "the sealed span has outgrown historical_holdout_months",
            "seal_boundary": self.seal_boundary.label(),
            "sealed_months": sealed_months,
            "holdout_months": self.holdout_months,
            "read_at": at_instant.value_ns,
        }
        return Ok(task)

    def _existing_final_look(self, events: list[dict[str, object]]) -> Result[StoreReceipt] | None:
        """A ``policy rejection`` if a final look for this seal is already journaled,
        else ``None``.
        """
        label = self.seal_boundary.label()
        for event in events:
            if (
                event.get("event_type") == _CONTROL_ACTION_EVENT
                and event.get("control_action_subtype") == FINAL_LOOK_SUBTYPE
                and event.get("seal_boundary") == label
            ):
                return policy_rejection(
                    "final_look",
                    "the sealed period is entitled to exactly one authorized final look, and "
                    "it was already taken; the sealed set is never silently recycled into "
                    "research (DEC-0119)",
                    seal_boundary=label,
                )
        return None

    def _final_look_event(
        self,
        writer: WriterId,
        at_instant: Instant,
        *,
        split_id: str | None,
        correlation_id: object | None,
    ) -> dict[str, object]:
        """The CT-13 control-action event that records the sealed-period final look."""
        event: dict[str, object] = {
            "event_type": _CONTROL_ACTION_EVENT,
            "control_action_subtype": FINAL_LOOK_SUBTYPE,
            "instant_ns": at_instant.value_ns,
            "world": self.world.value,
            "seal_boundary": self.seal_boundary.label(),
            "holdout_months": self.holdout_months,
            "writer": {
                "machine": writer.machine,
                "role": writer.role,
                "stream": writer.stream,
                "boot_epoch_id": writer.boot_epoch_id,
            },
            "format_version": CONTRACT_FORMAT_VERSION,
        }
        if split_id is not None:
            event["split_id"] = split_id
        if isinstance(correlation_id, str) and correlation_id.strip() != "":
            event["correlation_id"] = correlation_id
        return event

    def _require_calendar(self, identity: CalendarIdentity | None) -> TypedRefusal | None:
        """A ``policy rejection`` if ``identity`` differs from the pinned one, else ``None``."""
        if identity is not None and identity != self.calendar_identity:
            return policy_rejection(
                "calendar_identity",
                "a row carrying a calendar identity different from the seal's pinned one is "
                "refused, never silently rescaled (DEC-0106, DEC-0119)",
                pinned=repr(self.calendar_identity),
                given=repr(identity),
            )
        return None


def _coerce_world(value: object) -> World | None:
    """Resolve ``value`` to a :class:`~qmf.core.World` member, or ``None``."""
    if isinstance(value, World):
        return value
    if isinstance(value, str):
        try:
            return World(value)
        except ValueError:
            return None
    return None


def _coerce_read_boundary(value: object) -> ReadBoundary | None:
    """Resolve ``value`` to a :class:`ReadBoundary` member (or its value string), or ``None``."""
    if isinstance(value, ReadBoundary):
        return value
    if isinstance(value, str):
        try:
            return ReadBoundary(value)
        except ValueError:
            return None
    return None


def _coerce_position(value: object) -> Result[SplitBoundary]:
    """Resolve a read position to a :class:`~qmf.data.splits.SplitBoundary`, or refuse.

    Accepts a :class:`SplitBoundary` verbatim, or an :class:`~qmf.core.Instant` / int64
    UTC-nanosecond count / :class:`~qmf.core.TradingDate` built through
    :meth:`SplitBoundary.try_create`. Anything else is an ``invalid input`` refusal.
    """
    if isinstance(value, SplitBoundary):
        return Ok(value)
    return SplitBoundary.try_create(value)
