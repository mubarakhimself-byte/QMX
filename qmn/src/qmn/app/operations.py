"""The node's closed set of operations, each answering and never raising (Part C AD-302, AD-303).

Every answer is ``{ok: true, value}`` or ``{ok: false, code, message, next_step?}``
(CONTRACTS section 2). A refusal is an answer, never an exception, because every tool exception
counts toward the supervisor's breaker.

Reads answer from the store. Changes are recorded in ``desired`` in arrival order, each under its
op id; a call without one gets one minted and a call without ``issued_at`` is stamped on arrival.
A change whose ``issued_at`` is older than the newest change applied to the same register answers
``superseded``; ``kill`` and ``flatten`` always apply. A repeated op id answers its first answer.
No operation places an order, and while the machine fingerprint differs from the minted one every
change that could start trading is refused until ``confirm_same_node``.

``CHANGES`` is the one table of what each change takes, which register it orders in, whether it
could start trading, and what it does now that no venue is set up.
"""

from __future__ import annotations

import shutil
import uuid
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, TypeAlias, cast

from qmf.core import is_refusal
from qmf.data.journal_reader import JournalLine, read_committed, stream_folders

from qmn.app.identity import Standing
from qmn.app.store import Change, Desired, Json, Outcome, Store
from qmn.protection.ksa import LEVEL_RANK, KsaLevel

__all__ = [
    "CHANGES",
    "GUARD_BYTES",
    "READS",
    "TAIL_ROWS",
    "Answer",
    "Context",
    "answer_change",
    "answer_read",
]

Answer: TypeAlias = dict[str, Json]

TAIL_ROWS: Final = 500
"""`[node] tail_rows`: the most journal rows one `journal_tail` answers."""
GUARD_BYTES: Final = 3 * 1024**3
"""`[node] journal_guard_bytes` plus its margin: 2 GB and 1 GB (NODE.md section 9)."""
SCHEMAS: Final[dict[str, Json]] = {
    "route": "qmx.host.forward/1",
    "operations": "qmx.node.operations/1",
    "deployment": "qmx.node.deployment/1",
    "reading": "qmx.journal.envelope/1",
}
VENUES: Final[tuple[tuple[str, str], ...]] = (("ctrader", "demo"), ("hyperliquid", "testnet"))
"""Every venue this node can trade, none set up until his setup steps register it (C-11)."""
NOT_SET_UP: Final = "Set up a venue in the trading node's setup steps first."
STREAMS: Final = frozenset({"node", "unit"})
_SCOPES: Final = ("account", "deployment_id", "instrument")
_CHANGE_KEYS: Final = frozenset({"op_id", "issued_at"})


class BadArgumentError(Exception):
    """An argument the operation cannot take; answered as ``bad_argument``."""


@dataclass(frozen=True, slots=True)
class Context:
    """What every operation reads: the store, who the node is now, its journal, the clock."""

    store: Store
    here: str | None
    journal_root: Path
    data: Path
    build: str
    clock_ns: Callable[[], int]
    started_ns: int

    def standing(self) -> Standing:
        row = self.store.identity()
        if row is None:
            raise RuntimeError("the node's identity is minted before any operation answers")
        return Standing(row, self.here)


def ok(value: Json) -> Answer:
    return {"ok": True, "value": value}


def refused(code: str, message: str, *, next_step: str | None = None, value: Json = None) -> Answer:
    answer: Answer = {"ok": False, "code": code, "message": message}
    if next_step is not None:
        answer["next_step"] = next_step
    if value is not None:
        answer["value"] = value
    return answer


# --- arguments ------------------------------------------------------------------------------


def _known(arguments: Mapping[str, Json], allowed: frozenset[str]) -> None:
    unknown = sorted(set(arguments) - allowed)
    if unknown:
        raise BadArgumentError(f"unknown argument {', '.join(unknown)}")


def _text(arguments: Mapping[str, Json], name: str, *, required: bool = True) -> str | None:
    value = arguments.get(name)
    if value is None and not required:
        return None
    if not isinstance(value, str) or not value.strip():
        raise BadArgumentError(f"{name} is a non-empty string")
    return value


def _table(arguments: Mapping[str, Json], name: str) -> dict[str, Json]:
    value = arguments.get(name)
    if not isinstance(value, dict):
        raise BadArgumentError(f"{name} is an object")
    return value


def _scope(arguments: Mapping[str, Json]) -> str:
    """A scope key: ``all``, or ``account:<id>``, ``deployment_id:<id>``, ``instrument:<id>``."""
    value = arguments.get("scope")
    if value in ("all", {"all": True}):
        return "all"
    if isinstance(value, dict) and len(value) == 1:
        (name, item), *_ = value.items()
        if name in _SCOPES and isinstance(item, str) and item.strip():
            return f"{name}:{item}"
    raise BadArgumentError(
        'scope is "all" or one of {"account": id}, {"deployment_id": id}, {"instrument": id}'
    )


def _issued_at(value: Json) -> int:
    if not isinstance(value, str):
        raise BadArgumentError("issued_at is an ISO 8601 time with its offset")
    try:
        at = datetime.fromisoformat(value)
    except ValueError as error:
        raise BadArgumentError("issued_at is an ISO 8601 time with its offset") from error
    if at.tzinfo is None:
        raise BadArgumentError("issued_at carries its offset")
    delta = at - datetime(1970, 1, 1, tzinfo=UTC)
    return (delta.days * 86_400 + delta.seconds) * 1_000_000_000 + delta.microseconds * 1_000


def _iso(at_ns: int) -> str:
    return (
        datetime.fromtimestamp(at_ns // 1_000_000_000, UTC)
        .replace(microsecond=(at_ns // 1_000) % 1_000_000)
        .isoformat()
    )


# --- the target folded from desired ---------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Target:
    """What his applied changes ask for, folded in arrival order."""

    kills: dict[str, KsaLevel] = field(default_factory=dict[str, KsaLevel])
    paused: dict[str, bool] = field(default_factory=dict[str, bool])
    deployments: dict[str, Change] = field(default_factory=dict[str, Change])
    withdrawn: frozenset[str] = frozenset()

    @classmethod
    def fold(cls, accepted: Sequence[Change]) -> Target:
        kills: dict[str, KsaLevel] = {}
        paused: dict[str, bool] = {}
        deployments: dict[str, Change] = {}
        withdrawn: set[str] = set()
        newest_pause: dict[str, int] = {}
        for change in accepted:
            if change.kind == "kill":
                scope, level = str(change.args["scope"]), KsaLevel(str(change.args["level"]))
                held = kills.get(scope, KsaLevel.GREEN)
                kills[scope] = level if LEVEL_RANK[level] > LEVEL_RANK[held] else held
            elif change.kind in {"pause", "resume"}:
                scope = str(change.args["scope"])
                if change.issued_at_ns >= newest_pause.get(scope, -1):
                    newest_pause[scope] = change.issued_at_ns
                    paused[scope] = change.kind == "pause"
            elif change.kind == "deploy":
                deployments[str(change.args["deployment_id"])] = change
                withdrawn.discard(str(change.args["deployment_id"]))
            elif change.kind == "withdraw":
                withdrawn.add(str(change.args["deployment_id"]))
        return cls(kills, paused, deployments, frozenset(withdrawn))

    def level_at(self, scope: str) -> KsaLevel:
        held = [self.kills.get(scope, KsaLevel.GREEN), self.kills.get("all", KsaLevel.GREEN)]
        return max(held, key=LEVEL_RANK.__getitem__)

    def pauses(self) -> list[Json]:
        return [scope for scope, on in sorted(self.paused.items()) if on]


# --- changes ---------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Request:
    """A change's arguments, checked: the register it orders in and what ``desired`` keeps."""

    register: str | None
    kept: dict[str, Json]


@dataclass(frozen=True, slots=True)
class Applying:
    """A change in order and allowed, about to be answered inside its transaction."""

    context: Context
    desired: Desired
    request: Request
    op_id: str
    now_ns: int


@dataclass(frozen=True, slots=True)
class ChangeSpec:
    """One change: its arguments, its register (``None`` always applies), whether it could start
    trading, and what it answers once it is in order."""

    arguments: frozenset[str]
    parse: Callable[[Mapping[str, Json], Standing], Request]
    apply: Callable[[Applying], Answer]
    trades: bool = False


def _deploy(arguments: Mapping[str, Json], standing: Standing) -> Request:
    document = _table(arguments, "deployment")
    if document.get("schema_version") != "qmx.node.deployment/1":
        raise BadArgumentError("deployment.schema_version is qmx.node.deployment/1")
    deployment_id = _text(document, "deployment_id")
    node = _table(document, "node")
    if node.get("tag") != standing.tag:
        raise BadArgumentError(f"deployment.node.tag names another node, not {standing.tag}")
    unit = document.get("unit")
    return Request(
        f"deployment:{deployment_id}",
        {"deployment_id": deployment_id, "unit": unit if isinstance(unit, dict) else None},
    )


def _accepted_deploy(step: Applying) -> Answer:
    return ok({"deployment_id": step.request.kept["deployment_id"], "state": "accepted"})


def _withdraw(arguments: Mapping[str, Json], _: Standing) -> Request:
    deployment_id = _text(arguments, "deployment_id")
    when = arguments.get("when", "flat")
    if when != "flat":
        raise BadArgumentError('when is "flat"')
    return Request(f"deployment:{deployment_id}", {"deployment_id": deployment_id, "when": when})


def _apply_withdraw(step: Applying) -> Answer:
    deployment_id = str(step.request.kept["deployment_id"])
    if deployment_id not in Target.fold(step.desired.accepted()).deployments:
        return refused("unknown_deployment", f"no deployment {deployment_id} is on this node")
    return ok({"state": "accepted"})


def _scoped(register: str) -> Callable[[Mapping[str, Json], Standing], Request]:
    def parse(arguments: Mapping[str, Json], _: Standing) -> Request:
        scope = _scope(arguments)
        return Request(f"{register}:{scope}", {"scope": scope})

    return parse


def _accepted(step: Applying) -> Answer:
    return ok({"state": "accepted"})


def _apply_resume(step: Applying) -> Answer:
    scope = str(step.request.kept["scope"])
    level = Target.fold(step.desired.accepted()).level_at(scope)
    causes: list[Json] = [] if level is KsaLevel.GREEN else [f"kill switch at {level.value}"]
    return ok({"state": "accepted", "open_causes": causes})


def _kill(arguments: Mapping[str, Json], _: Standing) -> Request:
    level = arguments.get("level")
    names = [item.value for item in KsaLevel]
    if not isinstance(level, str) or level.upper() not in names:
        raise BadArgumentError(f"level is one of {', '.join(names)}")
    return Request(None, {"level": level.upper(), "scope": _scope(arguments)})


def _apply_kill(step: Applying) -> Answer:
    asked = KsaLevel(str(step.request.kept["level"]))
    held = Target.fold(step.desired.accepted()).level_at(str(step.request.kept["scope"]))
    in_force = asked if LEVEL_RANK[asked] > LEVEL_RANK[held] else held
    return ok({"level_in_force": in_force.value})


def _flatten(arguments: Mapping[str, Json], _: Standing) -> Request:
    return Request(None, {"scope": _scope(arguments)})


def _apply_flatten(step: Applying) -> Answer:
    return ok({"state": "accepted", "positions": 0})


def _bind(arguments: Mapping[str, Json], _: Standing) -> Request:
    account = _table(arguments, "account")
    action = arguments.get("action")
    if action not in {"add", "remove"}:
        raise BadArgumentError('action is "add" or "remove"')
    account_id = _text(account, "id")
    return Request(f"binding:{account_id}", {"account": account_id, "action": action})


def _not_set_up(step: Applying) -> Answer:
    return refused("not_set_up", "no venue is set up on this node yet", next_step=NOT_SET_UP)


def _bare(register: str) -> Callable[[Mapping[str, Json], Standing], Request]:
    def parse(_: Mapping[str, Json], __: Standing) -> Request:
        return Request(register, {})

    return parse


def _apply_confirm(step: Applying) -> Answer:
    context = step.context
    standing = context.standing()
    if context.here is None:
        return refused(
            "machine_unknown",
            "this machine's id cannot be read, so the node cannot be bound to it",
        )
    if standing.mismatch:
        row = step.desired.rebind_identity(
            op_id=step.op_id, kind="confirm_same_node", fingerprint=context.here, at_ns=step.now_ns
        )
        standing = Standing(row, context.here)
    return ok({"identity": standing.document()})


def _take_over(arguments: Mapping[str, Json], _: Standing) -> Request:
    old_tag = _text(arguments, "old_tag")
    if arguments.get("confirmed_gone") is not True:
        raise BadArgumentError("confirmed_gone is true: his word that the old node is gone")
    return Request("identity", {"old_tag": old_tag, "confirmed_gone": True})


def _not_yet_take_over(step: Applying) -> Answer:
    return refused(
        "not_available",
        "taking over a dead node needs the reconciler's attribution, which this node has not yet",
    )


def _sign_in_begin(arguments: Mapping[str, Json], _: Standing) -> Request:
    venue = arguments.get("venue", "ctrader")
    if venue != "ctrader":
        raise BadArgumentError('venue is "ctrader"')
    _text(arguments, "redirect", required=False)
    return Request("grant:ctrader", {"venue": venue})


def _sign_in_code(arguments: Mapping[str, Json], _: Standing) -> Request:
    _text(arguments, "code")
    # The one-time code is a credential, so desired never keeps it.
    return Request("grant:ctrader", {})


def _self_test(arguments: Mapping[str, Json], _: Standing) -> Request:
    account = _text(arguments, "account")
    return Request(f"self_test:{account}", {"account": account})


CHANGES: Final[Mapping[str, ChangeSpec]] = {
    "deploy": ChangeSpec(frozenset({"deployment"}), _deploy, _accepted_deploy, trades=True),
    "withdraw": ChangeSpec(frozenset({"deployment_id", "when"}), _withdraw, _apply_withdraw),
    "pause": ChangeSpec(frozenset({"scope"}), _scoped("pause"), _accepted),
    "resume": ChangeSpec(frozenset({"scope"}), _scoped("pause"), _apply_resume),
    "kill": ChangeSpec(frozenset({"level", "scope"}), _kill, _apply_kill),
    "flatten": ChangeSpec(frozenset({"scope"}), _flatten, _apply_flatten),
    "bind": ChangeSpec(frozenset({"account", "action"}), _bind, _not_set_up, trades=True),
    "confirm_same_node": ChangeSpec(frozenset(), _bare("identity"), _apply_confirm),
    "take_over": ChangeSpec(
        frozenset({"old_tag", "confirmed_gone"}), _take_over, _not_yet_take_over
    ),
    "sign_in_begin": ChangeSpec(
        frozenset({"venue", "redirect"}), _sign_in_begin, _not_set_up, trades=True
    ),
    "sign_in_code": ChangeSpec(frozenset({"code"}), _sign_in_code, _not_set_up, trades=True),
    "self_test": ChangeSpec(frozenset({"account"}), _self_test, _not_set_up, trades=True),
    "rotate_keys": ChangeSpec(frozenset(), _bare("keys"), _accepted),
}


def answer_change(context: Context, name: str, arguments: Mapping[str, Json]) -> Answer:
    """Take one change in arrival order and answer it; a repeated op id answers its first answer."""
    spec = CHANGES[name]
    try:
        _known(arguments, spec.arguments | _CHANGE_KEYS)
        op_id = _text(arguments, "op_id", required=False) or uuid.uuid4().hex
        arrived = context.clock_ns()
        given = arguments.get("issued_at")
        issued = arrived if given is None else _issued_at(given)
        request = spec.parse(arguments, context.standing())
    except BadArgumentError as error:
        return refused("bad_argument", f"{name}: {error}")

    def decide(desired: Desired) -> Change:
        newer = None if request.register is None else desired.newest_applied(request.register)
        if newer is not None and newer.issued_at_ns > issued:
            outcome = Outcome.SUPERSEDED
            answer = refused(
                "superseded",
                f"{name} was issued before {newer.kind} {newer.op_id}, which is already applied",
                value={"newer_op_id": newer.op_id},
            )
        elif spec.trades and context.standing().mismatch:
            outcome = Outcome.REFUSED
            answer = refused(
                "identity_unconfirmed",
                "this node's volume was made on another machine, so it refuses all trading",
                next_step="Confirm on the node's card that it is the same node, moved.",
            )
        else:
            answer = spec.apply(Applying(context, desired, request, op_id, arrived))
            outcome = Outcome.ACCEPTED if answer["ok"] is True else Outcome.REFUSED
        return Change(
            seq=0,
            op_id=op_id,
            kind=name,
            register=request.register,
            args=request.kept,
            stamped="arrival" if given is None else "caller",
            issued_at_ns=issued,
            arrived_at_ns=arrived,
            outcome=outcome,
            answer={**answer, "op_id": op_id},
        )

    return context.store.record(op_id, decide).answer


# --- reads ------------------------------------------------------------------------------------


def _status(context: Context, arguments: Mapping[str, Json]) -> Answer:
    _known(arguments, frozenset())
    standing = context.standing()
    target = Target.fold(context.store.accepted())
    level = target.level_at("all")
    journal_problem = context.store.observed("journal_problem")
    last_write = context.store.observed("journal_write")
    written = last_write if isinstance(last_write, int) else None
    reasons: list[Json] = []
    if standing.mismatch:
        reasons.append(
            "This node's volume was made on another machine, so it refuses all trading until "
            "you confirm it is the same node, moved."
        )
    if journal_problem is not None:
        reasons.append(f"The node cannot write its journal: {journal_problem}")
    if standing.mismatch or journal_problem is not None:
        word = "Stopped by a health check"
    elif level is not KsaLevel.GREEN or target.paused.get("all"):
        word = "Paused"
    else:
        word = "Ready"
    if level is not KsaLevel.GREEN:
        reasons.append(f"The kill switch is at {level.value} for all.")
    reasons.extend(f"Paused at {scope}." for scope in target.pauses())
    units = 0
    headline = f"{word}, no units yet" if units == 0 and word == "Ready" else word
    free = shutil.disk_usage(context.data).free
    return ok(
        {
            "schema_version": "qmx.node.state/1",
            "word": word,
            "headline": headline,
            "reasons": reasons,
            "identity": standing.document(),
            "clock": None,
            "venues": [
                {
                    "venue": venue,
                    "environment": environment,
                    "session": "not_set_up",
                    "since": None,
                    "last_contact": None,
                }
                for venue, environment in VENUES
            ],
            "units": {"trading": 0, "warming": 0, "paused": 0, "stopped": 0},
            "kill_level": level.value,
            "pauses": target.pauses(),
            "safe_to_restart": {"ok": True, "reasons": []},
            "contracts": SCHEMAS,
            "build": context.build,
            "disk": {"free_bytes": free, "guard_bytes": GUARD_BYTES},
            "last": {"journal_write": None if written is None else _iso(written)},
            "started_at": _iso(context.started_ns),
            "at": _iso(context.clock_ns()),
        }
    )


def _units(_: Context, arguments: Mapping[str, Json]) -> Answer:
    _known(arguments, frozenset({"deployment_id"}))
    _text(arguments, "deployment_id", required=False)
    return ok([])


def _positions(_: Context, arguments: Mapping[str, Json]) -> Answer:
    _known(arguments, frozenset({"account"}))
    _text(arguments, "account", required=False)
    return ok([])


def _deployments(context: Context, arguments: Mapping[str, Json]) -> Answer:
    _known(arguments, frozenset())
    target = Target.fold(context.store.accepted())
    return ok(
        [
            {
                "deployment_id": deployment_id,
                "unit": change.args.get("unit"),
                "state": "withdrawing" if deployment_id in target.withdrawn else "accepted",
                "accepted_at": _iso(change.arrived_at_ns),
            }
            for deployment_id, change in target.deployments.items()
        ]
    )


def _passport(context: Context, arguments: Mapping[str, Json]) -> Answer:
    _known(arguments, frozenset())
    return ok(
        {
            "schema_version": "qmx.node.passport/1",
            "identity": context.standing().document(),
            "checks": [],
            "round_trip": [],
            "grants": [],
            "agent_wallets": [],
            "at": None,
        }
    )


def _journal_tail(context: Context, arguments: Mapping[str, Json]) -> Answer:
    """The node's committed journal rows after ``after_sequence``, at most ``TAIL_ROWS``.

    Read with the committed reader, so a line the writer is still writing is left alone and the
    writer's files stay byte for byte. Without ``after_sequence`` it answers the newest rows.
    ``next_sequence`` is the ``after_sequence`` to pass for the rows that follow.
    """
    _known(arguments, frozenset({"after_sequence", "streams"}))
    after = arguments.get("after_sequence")
    if after is not None and (not isinstance(after, int) or isinstance(after, bool) or after < -1):
        raise BadArgumentError("after_sequence is an integer from -1")
    streams = arguments.get("streams", sorted(STREAMS))
    if not isinstance(streams, list) or not streams or any(item not in STREAMS for item in streams):
        raise BadArgumentError(f"streams is a list of {', '.join(sorted(STREAMS))}")
    lines: list[JournalLine] = []
    for folder in stream_folders(context.journal_root):
        read = read_committed(folder)
        if is_refusal(read):
            return refused(
                "journal_unreadable",
                f"the node's journal could not be read ({read.category.value})",
            )
        lines.extend(
            line
            for line in read.value
            if isinstance(line, JournalLine)
            and line.record.get("stream") in streams
            and (after is None or line.seq > after)
        )
    lines.sort(key=lambda line: (line.t, line.seq))
    rows = lines[-TAIL_ROWS:] if after is None else lines[:TAIL_ROWS]
    next_sequence = max((line.seq for line in rows), default=-1 if after is None else after)
    return ok(
        {
            "rows": [cast(Json, dict(line.record)) for line in rows],
            "next_sequence": next_sequence,
        }
    )


READS: Final[Mapping[str, Callable[[Context, Mapping[str, Json]], Answer]]] = {
    "status": _status,
    "units": _units,
    "positions": _positions,
    "journal_tail": _journal_tail,
    "passport": _passport,
    "deployments": _deployments,
}


def answer_read(context: Context, name: str, arguments: Mapping[str, Json]) -> Answer:
    try:
        return READS[name](context, arguments)
    except BadArgumentError as error:
        return refused("bad_argument", f"{name}: {error}")
