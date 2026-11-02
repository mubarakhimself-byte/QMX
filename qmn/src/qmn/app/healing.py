"""How the trading node heals itself (Part C AD-315, Level 0 AD-38, ruling 35).

Two levels. Inside the process, the inner supervisor (``Runtime.step``) catches an exception
from the runtime's pass, waits its back-off, and starts the runtime again over the same
hosted units; :class:`Healer` keeps the record of each heal. A runtime that stops making
progress cannot be restarted from inside, so :class:`StuckWatch` exits the process and the
apps supervisor's opt-in restart (``[breaker] restart = "backoff"``, C-05a) brings it back.

Every heal is stamped into the crash-loop fold, which moved here from
``qmn.host._supervision``. Past ``REPEATED_FAULT_RESTARTS`` heals in
``REPEATED_FAULT_WINDOW_NS`` the node stands down alive: it keeps healing, exits, broker
stops and the kill switch keep working, and no new entry goes until his resume. The stamps
live in the node's store, so a process restart reloads them and never clears the fold.

Nothing here clears a stand-down. The kill level is folded from ``desired`` on every pass,
and the stand-downs that wait for him survive a heal in memory and a process restart through
the journals (``stand_down.restored``).
"""

from __future__ import annotations

import json
import os
import sys
import threading
from collections.abc import Callable, Mapping, MutableSequence, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Final, cast

from qmf.core import Ok, Result, is_refusal
from qmf.core.refusal import RefusalCategory, Retryability, TypedRefusal
from qmf.data.journal_envelope import RowFacts
from qmf.data.journal_writer import JournalWriter

from qmn.app.store import Json, Store

__all__ = [
    "HEALTHY_RESET_NS",
    "INNER_BACKOFF_MAX_S",
    "INNER_BACKOFF_S",
    "REQUESTED_RESTART_REASON",
    "RUNTIME_STUCK_EXIT_CODE",
    "STUCK_AFTER_NS",
    "WATCHDOG_INTERVAL_S",
    "Backoff",
    "BootAttemptStamp",
    "CrashLoopFold",
    "CrashLoopVerdict",
    "Fault",
    "Healer",
    "StuckWatch",
]

REQUESTED_RESTART_REASON: Final[str] = "requested-restart"
"""A boot stamped with this reason was asked for, so it never advances the crash-loop fold."""
INNER_BACKOFF_S: Final = 1.0
"""`[node] inner_backoff_s`, starting at 1 s and doubling on each heal (NODE.md section 9)."""
INNER_BACKOFF_MAX_S: Final = 60.0
"""`[node] inner_backoff_max_s`, starting at 60 s: the longest wait before a heal."""
HEALTHY_RESET_NS: Final = 600_000_000_000
"""`[node] inner_backoff_reset_s`, starting at 10 minutes: a runtime that ran this long since
its last heal starts its back-off again from the first wait."""
STUCK_AFTER_NS: Final = 30_000_000_000
"""`[node] stuck_after_s`, starting at 30 s: a pass that has not finished by then is stuck."""
WATCHDOG_INTERVAL_S: Final = 10.0
"""`[node] watchdog_interval_s`, starting at 10 s, the mini-app heartbeat default."""
RUNTIME_STUCK_EXIT_CODE: Final = 70
"""The process exit code of a stuck or dead runtime, logged by the apps supervisor."""
_BOOTS: Final = "healing.boots"
_EXIT: Final = "healing.exit"
_HEALING: Final = "runtime.healing"
_HEALS: Final = "runtime.heals"


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


# --- the inner supervisor's record ----------------------------------------------------------


@dataclass
class Backoff:
    """The wait before each heal: ``base_s`` doubling to ``cap_s``, starting again from
    ``base_s`` once the runtime has run ``reset_ns`` since its last heal."""

    base_s: float = INNER_BACKOFF_S
    cap_s: float = INNER_BACKOFF_MAX_S
    reset_ns: int = HEALTHY_RESET_NS
    attempts: int = 0
    last_ns: int | None = None

    def next(self, now_ns: int) -> float:
        if self.last_ns is not None and now_ns - self.last_ns >= self.reset_ns:
            self.attempts = 0
        wait = min(self.base_s * 2**self.attempts, self.cap_s)
        self.attempts += 1
        self.last_ns = now_ns
        return wait


@dataclass(frozen=True, slots=True)
class Fault:
    """One heal about to happen: how long to wait, how many heals the window counts, and
    whether that count stands the node down."""

    wait_s: float
    restarts: int
    breached: bool


def _day(at_ns: int) -> str:
    return datetime.fromtimestamp(at_ns / 1e9, UTC).date().isoformat()


def _iso(at_ns: int) -> str:
    return datetime.fromtimestamp(at_ns / 1e9, UTC).isoformat()


class Healer:
    """The node's heals: each fault stamped into the crash-loop fold, its back-off, its
    ``node_lifecycle`` rows, and what the card shows (``runtime.healing``, ``runtime.heals``).

    The fold's stamps and the record a stuck exit leaves are kept in the node's store, so a
    process restart reloads both. ``runtime.heals`` holds today's heals; the node journal
    holds every one.
    """

    def __init__(
        self,
        store: Store,
        journal: JournalWriter,
        *,
        clock_ns: Callable[[], int],
        boot_epoch_id: str,
        max_restarts: int,
        window_ns: int,
        backoff: Backoff | None = None,
    ) -> None:
        self.store = store
        self.journal = journal
        self.clock_ns = clock_ns
        self.boot_epoch_id = boot_epoch_id
        self.backoff = backoff or Backoff()
        self.fold = CrashLoopFold(max_boots=max_restarts, window_ns=window_ns)
        for kept in cast("list[dict[str, Json]]", store.observed(_BOOTS) or []):
            reason = kept["reason"]
            self.fold.record(
                BootAttemptStamp(
                    str(kept["boot_epoch_id"]),
                    cast("int", kept["at_ns"]),
                    None if reason is None else str(reason),
                    exited=True,
                )
            )
        self.heals = cast("list[dict[str, Json]]", store.observed(_HEALS) or [])
        self.healing: dict[str, Json] | None = None
        exited = store.observed(_EXIT)
        if isinstance(exited, dict):
            self._began(exited)
            self.restarted()
            store.observe(_EXIT, None, clock_ns())

    def fault(self, why: str) -> Fault:
        """Stamp one heal of this process's runtime and answer its wait."""
        now = self.clock_ns()
        verdict = self._stamp(why, now)
        wait = self.backoff.next(now)
        heal: dict[str, Json] = {
            "why": why,
            "at": _iso(now),
            "at_ns": now,
            "restart": verdict.counted_boots,
            "backoff_ms": round(wait * 1000),
        }
        self._began(heal)
        return Fault(wait, verdict.counted_boots, verdict.threshold_breached)

    def restarted(self) -> None:
        """The runtime starts again after its wait."""
        heal = self.healing or {}
        body: dict[str, object] = {"event": "start", "what": "runtime"}
        if heal.get("restart") is not None:
            body["restart"] = heal["restart"]
        self._row(body)

    def healed(self) -> None:
        """The runtime is back: every account reconciled and every unit past its warm-up."""
        heal = self.healing
        if heal is None:
            return
        now = self.clock_ns()
        heal["back_at"] = _iso(now)
        heal["back_after_ms"] = (now - cast("int", heal["at_ns"])) // 1_000_000
        self.healing = None
        self._publish()

    def reset(self) -> None:
        """His resume after a repeated fault: the fold counts from nothing again."""
        self.fold.reset_for_operator_cycle()
        self.backoff.attempts = 0
        self.store.observe(_BOOTS, [], self.clock_ns())

    def exit_record(self, why: str) -> None:
        """What a stuck process leaves for the next start: the stamp and the heal it began."""
        now = self.clock_ns()
        verdict = self._stamp(why, now)
        heal: dict[str, Json] = {
            "why": why,
            "at": _iso(now),
            "at_ns": now,
            "restart": verdict.counted_boots,
        }
        self.store.observe(_EXIT, heal, now)

    def _stamp(self, why: str, now: int) -> CrashLoopVerdict:
        epoch = f"{self.boot_epoch_id}-{len(self.fold.stamps) + 1}"
        self.fold.record(BootAttemptStamp(epoch, now, why, exited=True))
        kept: list[Json] = [
            {"boot_epoch_id": s.boot_epoch_id, "at_ns": s.at_ns, "reason": s.reason}
            for s in self.fold.stamps
            if s.at_ns >= now - self.fold.window_ns
        ]
        self.store.observe(_BOOTS, kept, now)
        return self.fold.evaluate(now_ns=now)

    def _began(self, heal: dict[str, Json]) -> None:
        self.healing = heal
        today = _day(cast("int", heal["at_ns"]))
        self.heals = [h for h in self.heals if _day(cast("int", h["at_ns"])) == today]
        self.heals.append(heal)
        self._row({"event": "stop", "what": "runtime", **heal})
        self._publish()

    def _row(self, body: Mapping[str, object]) -> None:
        facts = RowFacts(ts_recv=self.clock_ns(), clock_ok=False)
        self.journal.append("node_lifecycle", body, facts)

    def _publish(self) -> None:
        now = self.clock_ns()
        self.store.observe(_HEALING, self.healing, now)
        self.store.observe(_HEALS, cast("list[Json]", self.heals), now)


# --- the stuck detector ---------------------------------------------------------------------


class StuckWatch:
    """Exits the process when the runtime's pass has run past ``stuck_after_ns``, or when its
    thread is gone though nobody stopped it, so the apps supervisor starts it again.

    The runtime sets :attr:`began` from its steady clock when a pass starts and clears it when
    the pass ends; a back-off wait is not a pass. ``before_exit`` (the healer's
    :meth:`Healer.exit_record`) runs first and may fail; the exit happens either way.
    """

    def __init__(
        self,
        *,
        steady_ns: Callable[[], int],
        alive: Callable[[], bool],
        before_exit: Callable[[str], None],
        stuck_after_ns: int = STUCK_AFTER_NS,
        interval_s: float = WATCHDOG_INTERVAL_S,
        exit: Callable[[int], None] = os._exit,
    ) -> None:
        self.steady_ns = steady_ns
        self.alive = alive
        self.before_exit = before_exit
        self.stuck_after_ns = stuck_after_ns
        self.interval_s = interval_s
        self.exit = exit
        self.began: int | None = None

    def check(self) -> str | None:
        """Exit when the runtime is stuck or gone; answers why, or None when it is sound."""
        began = self.began
        if began is not None and self.steady_ns() - began > self.stuck_after_ns:
            why = "runtime_stuck"
        elif not self.alive():
            why = "runtime_died"
        else:
            return None
        print(json.dumps({"event": why, "exit_code": RUNTIME_STUCK_EXIT_CODE}), file=sys.stderr)
        try:
            self.before_exit(why)
        except Exception as error:  # the exit must not wait on what the stuck runtime holds
            print(
                json.dumps({"event": "exit_record_failed", "error": repr(error)}), file=sys.stderr
            )
        self.exit(RUNTIME_STUCK_EXIT_CODE)
        return why

    def run(self, stopped: threading.Event) -> None:
        while not stopped.wait(self.interval_s):
            self.check()
