"""One fold reads a brake's state, and every reader of it answers the same words.

The three seams are the section's Verify, unit block. Each gives the same journal rows to a
different reader: the fold taken cold, the node's incremental path (a cache in the snapshot, then
the rest of the journal), and the unit the shared handler drives in QMB. K9 test 9 is the middle
sentence: ``RiskState`` from one fold in every reader. A fourth test holds the five words the
section names, because the three readers cannot show RESTORE without a restore row. The rest hold
the fold's safety surface: which rows may move the word, and that an empty seed still reads the
bench its snapshot caches.
"""

# pyright: reportPrivateUsage=false

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence

from qmf.core.chrono import Instant
from qml.compile import CompiledUnit
from qmf.risk.controls import StateWord
from qml.fold import Fold, fold
from qml.protocol.unit import HostedUnit, construct_unit, restore_unit

from test_compile_dummy import _compiled, _ok, _slice, _surfaces, _target

_SCOPE = "unit:run-rc14"
"""The scope a unit hosted with ``scope_id="run-rc14"`` folds under."""
_CLOCK_NS = 1_740_953_400_000_000_000
_FIRE_NS = _CLOCK_NS - 900_000_000_000
"""One bar before the clock: the session-loss brake's fire, which the bench is dated from."""
_FIRST_NS = _FIRE_NS - 3_600_000_000_000
_DAY_NS = 86_400_000_000_000


def _fact(at_ns: int, index: int, *, limit_ns: int = _DAY_NS) -> dict[str, object]:
    return {
        "kind": "fact",
        "scope": _SCOPE,
        "at": at_ns,
        "id": f"fact-{index:02d}",
        "name": "own.session_loss_r",
        "limit_ns": limit_ns,
    }


def _fire(
    at_ns: int, verb: str = "no_new_entries", code: str = "session-loss-limit-halt"
) -> dict[str, object]:
    return {
        "kind": "risk_event",
        "scope": _SCOPE,
        "at": at_ns,
        "id": f"fire-{at_ns}-{code}",
        "code": code,
        "verb": verb,
    }


def _account(index: int) -> dict[str, object]:
    """One row of another scope, which a unit's fold must not read."""
    return {
        "kind": "risk_event",
        "scope": "account:demo-1",
        "at": _FIRST_NS + index * 60_000_000_000,
        "id": f"account-{index}",
        "code": "equity-drawdown-halt",
        "verb": "no_new_entries",
    }


def _forty_rows() -> list[dict[str, object]]:
    """The journal one benched unit holds: thirty fresh reads, eight rows of another scope, one
    brake that fired without refusing anything, and the session-loss brake that benched it."""
    rows: list[dict[str, object]] = [
        _fact(_FIRST_NS + index * 60_000_000_000, index) for index in range(30)
    ]
    rows += [_account(index) for index in range(8)]
    rows.append(_fire(_FIRE_NS - 1_800_000_000_000, "none", "session-fill-limit-halt"))
    rows.append(_fire(_FIRE_NS))
    return rows


def _unit(compiled: CompiledUnit, rows: Sequence[Mapping[str, object]] = ()) -> HostedUnit:
    """The unit QMB's shared handler drives, built from the journal rows it holds."""
    return _ok(
        construct_unit(
            compiled,
            read_surfaces=_surfaces(_slice()),
            scope_id="run-rc14",
            execution_target=_target(),
            risk_rows=rows,
        )
    )


def _restored(
    compiled: CompiledUnit,
    snapshot: Mapping[str, object],
    rows: Sequence[Mapping[str, object]] | None = None,
) -> HostedUnit:
    """The same unit hosted again with only its snapshot: the journal rows are not handed.

    ``rows`` is what a host's journal reader found before the restore; the node hands ``()`` when
    it finds no brake row at all.
    """
    return _ok(
        restore_unit(
            snapshot,
            compiled,
            read_surfaces=_surfaces(_slice()),
            scope_id="run-rc14",
            execution_target=_target(),
            risk_rows=rows,
        )
    )


# --- K9 9: one fold in every reader --------------------------------------------------


def test_k9_9_one_fold_in_every_reader() -> None:
    rows = _forty_rows()
    clock = Instant(_CLOCK_NS)
    assert len(rows) == 40

    cold = fold(rows, _SCOPE, clock)

    node = Fold(_SCOPE)
    for row in rows[:20]:
        node.add(row)
    half = node.state(clock)
    restarted = Fold.from_cache(json.loads(json.dumps(node.cached())))
    for row in rows:  # a restart re-reads the journal; the cache's watermark skips what it held
        restarted.add(row)

    qmb = _unit(_compiled(), rows).risk_state(clock)

    assert cold == restarted.state(clock) == qmb
    assert half.word is StateWord.ACTIVE, "the cache holds the half it folded, not the bench"
    assert (cold.word, cold.reason, cold.since) == (
        StateWord.BENCHED,
        "session-loss-limit-halt",
        Instant(_FIRE_NS),
    ), "the last fire at this scope benches it, and only that scope's rows count"
    assert cold.unknown == ()


def test_the_fold_derives_each_word_a_row_names() -> None:
    """The five words, from rows alone: a fire's verb says which, a restore row releases it."""
    clock = Instant(_CLOCK_NS)
    scope = _SCOPE
    quiet = fold([], scope, clock)
    reducing = fold([_fire(_FIRE_NS, "reduce")], scope, clock)
    halted = fold([_fire(_FIRE_NS, "flatten")], scope, clock)
    benched = fold([_fire(_FIRE_NS)], scope, clock)
    restored = fold(
        [
            _fire(_FIRE_NS),
            {"kind": "restore", "scope": scope, "at": _FIRE_NS + 1, "id": "r1", "code": "hand"},
        ],
        scope,
        clock,
    )
    harmless = fold([_fire(_FIRE_NS, "none")], scope, clock)

    assert (quiet.word, quiet.since) == (StateWord.ACTIVE, None)
    assert [reducing.word, halted.word, benched.word, restored.word, harmless.word] == [
        StateWord.REDUCING,
        StateWord.HALTED,
        StateWord.BENCHED,
        StateWord.RESTORE,
        StateWord.ACTIVE,
    ]
    assert restored.since == Instant(_FIRE_NS + 1)


def test_a_warn_only_fire_keeps_the_bench_it_fires_after() -> None:
    """A fire that refuses nothing records its event and leaves the word where it was."""
    clock = Instant(_CLOCK_NS)
    rows = [_fire(_FIRE_NS), _fire(_FIRE_NS + 1, "none", "session-fill-limit-halt")]

    cold = fold(rows, _SCOPE, clock)
    qmb = _unit(_compiled(), rows).risk_state(clock)

    assert (cold.word, cold.since) == (
        StateWord.BENCHED,
        Instant(_FIRE_NS),
    ), "a warn-only fire cannot release the bench it fires after; only a restore row does"
    assert qmb == cold, "the unit reads the same fold"


def test_a_weaker_fire_never_clears_a_stronger_word() -> None:
    """A fire raises the word to its own or leaves a stronger one in place: the strongest word
    since the last restore is what the scope is doing."""
    clock = Instant(_CLOCK_NS)
    halted = fold(
        [_fire(_FIRE_NS, "flatten"), _fire(_FIRE_NS + 1), _fire(_FIRE_NS + 2, "reduce")],
        _SCOPE,
        clock,
    )
    benched = fold([_fire(_FIRE_NS), _fire(_FIRE_NS + 1, "reduce")], _SCOPE, clock)

    assert (halted.word, halted.since) == (StateWord.HALTED, Instant(_FIRE_NS)), (
        "neither a bench nor a reduce can lower a halt"
    )
    assert (benched.word, benched.since) == (StateWord.BENCHED, Instant(_FIRE_NS)), (
        "a reduce cannot lower a bench"
    )


def test_a_restore_row_is_what_lets_a_lower_word_arrive() -> None:
    """The one row that lowers the word is a restore: the next fire sets its own word again."""
    clock = Instant(_CLOCK_NS)
    rows = [
        _fire(_FIRE_NS, "flatten"),
        {"kind": "restore", "scope": _SCOPE, "at": _FIRE_NS + 1, "id": "r1", "code": "hand"},
        _fire(_FIRE_NS + 2, "reduce"),
    ]

    state = fold(rows, _SCOPE, clock)

    assert (state.word, state.since) == (StateWord.REDUCING, Instant(_FIRE_NS + 2))


# --- a restart keeps a bench from rows ----------------------------------------------


def test_restart_keeps_a_bench_from_rows() -> None:
    rows = _forty_rows()
    clock = Instant(_CLOCK_NS)
    compiled = _compiled()
    head = _unit(compiled, rows)
    before = head.risk_state(clock)
    snapshot = dict(head.snapshot())

    from_snapshot = _restored(compiled, snapshot)

    assert from_snapshot.risk_state(clock).word is StateWord.BENCHED, "the cache names the bench"
    deleted = _unit(compiled, rows)  # the snapshot is gone; the journal is the only record
    assert deleted.risk_state(clock) == before
    assert (deleted.risk_state(clock).word, deleted.risk_state(clock).since) == (
        StateWord.BENCHED,
        Instant(_FIRE_NS),
    )


def test_an_empty_row_set_reads_the_snapshot_bench() -> None:
    """A node that finds no brake row hands ``()``. That is a reader that found none, not the
    truth that the scope is up, so the snapshot's cached bench answers: a bench lost on a restart
    is the state AD-12 exists to keep."""
    clock = Instant(_CLOCK_NS)
    compiled = _compiled()
    snapshot = dict(_unit(compiled, _forty_rows()).snapshot())

    found_none = _restored(compiled, snapshot, ())

    assert (found_none.risk_state(clock).word, found_none.risk_state(clock).since) == (
        StateWord.BENCHED,
        Instant(_FIRE_NS),
    ), "an empty row set must not read as a lift of the bench the snapshot holds"
    assert found_none.risk_state(clock) == _restored(compiled, snapshot).risk_state(clock)


# --- a stale input -------------------------------------------------------------------


def test_a_stale_input_reads_unknown() -> None:
    clock = Instant(_CLOCK_NS)
    stale = _fact(_CLOCK_NS - 2 * _DAY_NS, 0, limit_ns=_DAY_NS)

    state = fold([stale, _fire(_FIRE_NS)], _SCOPE, clock)

    assert state.word is StateWord.UNKNOWN
    assert state.unknown == ("own.session_loss_r",)
    assert state.since == Instant(_FIRE_NS), "the word the stale read hides is still dated"
