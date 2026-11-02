"""How the trading node heals itself (Part C AD-315, Level 0 AD-38, ruling 35).

The crash-loop fold counts the node's unrequested restarts inside a window; it moved here from
``qmn.host._supervision`` so the new shell owns it.
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from dataclasses import dataclass, field
from typing import Final, cast

from qmf.core import Ok, Result, is_refusal
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal

__all__ = [
    "REQUESTED_RESTART_REASON",
    "BootAttemptStamp",
    "CrashLoopFold",
    "CrashLoopVerdict",
]

REQUESTED_RESTART_REASON: Final[str] = "requested-restart"
"""A boot stamped with this reason was asked for, so it never advances the crash-loop fold."""


def invalid(field: str, reason: str, **extra: object) -> TypedRefusal:
    context: dict[str, object] = {"field": field, "reason": reason, **extra}
    return TypedRefusal(
        category=RefusalCategory.INVALID_INPUT, retryability=Retryability.NO, context=context
    )


def _positive_int(field: str, value: object) -> Result[int]:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        return invalid(
            field,
            f"{field} is a positive int (blank blocks-boot)",
            given=repr(value),
        )
    return Ok(value)


# --- the crash-loop fold --------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class BootAttemptStamp:
    """Minimal boot-attempt projection the crash-loop fold reads."""

    boot_epoch_id: str
    at_ns: int
    reason: str | None
    exited: bool


@dataclass(frozen=True, slots=True)
class CrashLoopVerdict:
    """Outcome of folding unrequested exiting boots within the window."""

    counted_boots: int
    threshold_breached: bool
    counted_epoch_ids: tuple[str, ...]


@dataclass
class CrashLoopFold:
    """Counts unrequested exiting boots within ``(K, T)`` (DEC-0189 / DEC-0226).

    Requested-restart stamps never advance the fold. Detected preflight refusals
    that stay alive (no exit) also never advance it. Counters are durable: a
    process restart reloads stamps via :meth:`load` and never clears the fold by
    itself. Only an operator ``resurrect`` (or an explicit :meth:`reset_for_operator_cycle`)
    resets the fold so an unrequested crash cannot masquerade as a clean operator
    cycle (TN-4; QMX-F064 / Story 25.13).
    """

    max_boots: int
    window_ns: int
    _stamps: MutableSequence[BootAttemptStamp] = field(default_factory=list[BootAttemptStamp])

    @classmethod
    def load(
        cls,
        *,
        max_boots: object,
        window_ns: object,
        stamps: object,
    ) -> Result[CrashLoopFold]:
        """Rebuild the fold from durable boot-attempt stamps (process-restart safe)."""
        k = _positive_int("node_crash_loop_max_boots", max_boots)
        if is_refusal(k):
            return k
        t = _positive_int("node_crash_loop_window", window_ns)
        if is_refusal(t):
            return t
        if not isinstance(stamps, Sequence) or isinstance(stamps, (str, bytes)):
            return invalid(
                "stamps",
                "crash-loop fold loads a sequence of BootAttemptStamp projections",
                given=type(stamps).__name__,
            )
        loaded: list[BootAttemptStamp] = []
        for index, raw in enumerate(cast("Sequence[object]", stamps)):
            if not isinstance(raw, BootAttemptStamp):
                return invalid(
                    "stamps",
                    "each durable stamp is a BootAttemptStamp",
                    index=index,
                    given=type(raw).__name__,
                )
            loaded.append(raw)
        return Ok(cls(max_boots=k.value, window_ns=t.value, _stamps=loaded))

    def record(self, stamp: object) -> Result[CrashLoopVerdict]:
        if not isinstance(stamp, BootAttemptStamp):
            return invalid(
                "stamp",
                "crash-loop fold reads BootAttemptStamp projections",
                given=type(stamp).__name__,
            )
        self._stamps.append(stamp)
        return Ok(self.evaluate(now_ns=stamp.at_ns))

    def reset_for_operator_cycle(self) -> None:
        """Clear counted stamps after an operator resurrect / new clean boot epoch.

        A mere process restart must call :meth:`load` instead — it never resets.
        """
        self._stamps.clear()

    @property
    def stamps(self) -> tuple[BootAttemptStamp, ...]:
        """Durable stamp projection — process restart reloads these, never drops them."""
        return tuple(self._stamps)

    def evaluate(self, *, now_ns: object) -> CrashLoopVerdict:
        if not isinstance(now_ns, int) or isinstance(now_ns, bool):
            return CrashLoopVerdict(counted_boots=0, threshold_breached=False, counted_epoch_ids=())
        window_start = now_ns - self.window_ns
        counted: list[str] = []
        for stamp in self._stamps:
            if stamp.at_ns < window_start:
                continue
            if not stamp.exited:
                continue
            if stamp.reason == REQUESTED_RESTART_REASON:
                continue
            counted.append(stamp.boot_epoch_id)
        return CrashLoopVerdict(
            counted_boots=len(counted),
            threshold_breached=len(counted) >= self.max_boots,
            counted_epoch_ids=tuple(counted),
        )
