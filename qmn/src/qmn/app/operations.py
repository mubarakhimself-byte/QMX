"""The node's closed set of operations, each answering and never raising (Part C AD-302, AD-303).

Every answer is ``{ok: true, value}`` or ``{ok: false, code, message, next_step?}``
(CONTRACTS section 2). A refusal is an answer, never an exception, because every tool exception
counts toward the supervisor's breaker.

Reads answer from the store. Changes are recorded in ``desired`` in arrival order, each under its
op id; a call without one gets one minted and a call without ``issued_at`` is stamped on arrival.
A change whose ``issued_at`` is older than the newest change applied to the same register answers
``superseded``; ``kill`` and ``flatten`` always apply. Any other change dated more than
``ISSUED_AHEAD_NS`` past arrival is refused, so a caller's fast clock cannot supersede his later
changes. A repeated op id answers its first answer, unless it carries another change, which
answers ``op_id_reused``. No operation places an order, and while the machine fingerprint
differs from the minted one every change that could start trading is refused until
``confirm_same_node``.

``CHANGES`` is the one table of what each change takes, which register it orders in, whether it
could start trading, and what it does now that no venue is set up.
"""

from __future__ import annotations

import bisect
import json
import os
import re
import shutil
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Final, Protocol, TypeAlias, cast

from qmf.data.journal_envelope import JournalStream
from qmf.data.journal_reader import JournalLine, stream_folders

from qmn.app.identity import Standing
from qmn.app.store import Change, Desired, Json, Outcome, Store
from qmn.protection.ksa import LEVEL_RANK, KsaLevel

__all__ = [
    "CHANGES",
    "GUARD_BYTES",
    "ISSUED_AHEAD_NS",
    "READS",
    "TAIL_ROWS",
    "Answer",
    "Context",
    "NoVenues",
    "VenueDoor",
    "answer_change",
    "answer_read",
]

Answer: TypeAlias = dict[str, Json]

TAIL_ROWS: Final = 500
"""`[node] tail_rows`: the most journal rows one `journal_tail` answers."""
ISSUED_AHEAD_NS: Final = 5_000_000_000
"""`[node] issued_ahead_s`, starting at 5 s: how far past its arrival a change's `issued_at` may
be. Any further ahead is a fast clock, refused as `bad_argument`; `kill` and `flatten` take any
`issued_at`, since they always apply."""
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
_ROTATION_FILE: Final = re.compile(r"\A\d{6}\.jsonl\Z")
"""A stream folder's rotation file, as the committed reader names it (``journal_reader``)."""
_SCOPES: Final = ("account", "deployment_id", "instrument")
_CHANGE_KEYS: Final = frozenset({"op_id", "issued_at"})


class BadArgumentError(Exception):
    """An argument the operation cannot take; answered with its ``code``."""

    code = "bad_argument"


class UnknownInstrumentError(BadArgumentError):
    code = "unknown_instrument"


class VenueDoor(Protocol):
    """What the venue operations ask of the node's composition: the cTrader sign-in, the
    account bindings and the self-test. Each answers and never raises; the node calls it
    outside the store's lock, since a sign-in crosses the network."""

    def begin(self, redirect: str | None) -> Answer: ...

    def code(self, op_id: str, code: str) -> Answer:
        """Exchange the one-time code; a repeated ``op_id`` answers its first answer."""
        ...

    def bind(self, account: Mapping[str, Json], action: str) -> Answer: ...

    def self_test(self, account: str) -> Answer: ...

    def rotate_keys(self) -> Answer: ...

    def sessions(self, observed: list[Json]) -> list[Json]:
        """The ``status`` venue rows, from the bound sessions the runtime observed."""
        ...

    def passport(self) -> dict[str, Json]:
        """The passport's ``checks``, ``grants`` and ``at``."""
        ...


class NoVenues:
    """A node with no venue door: every venue change answers ``not_set_up``."""

    def begin(self, redirect: str | None) -> Answer:
        return _nothing_set_up()

    def code(self, op_id: str, code: str) -> Answer:
        return _nothing_set_up()

    def bind(self, account: Mapping[str, Json], action: str) -> Answer:
        return _nothing_set_up()

    def self_test(self, account: str) -> Answer:
        return _nothing_set_up()

    def rotate_keys(self) -> Answer:
        return ok({"state": "accepted"})

    def sessions(self, observed: list[Json]) -> list[Json]:
        return observed or [
            {
                "venue": venue,
                "environment": environment,
                "session": "not_set_up",
                "since": None,
                "last_contact": None,
            }
            for venue, environment in VENUES
        ]

    def passport(self) -> dict[str, Json]:
        return {"checks": [], "grants": [], "at": None}


def _nothing_set_up() -> Answer:
    return refused("not_set_up", "no venue is set up on this node yet", next_step=NOT_SET_UP)


@dataclass(frozen=True, slots=True)
class Context:
    """What every operation reads: the store, who the node is now, its journal, the clock and
    the id source (both built in ``open_node``)."""

    store: Store
    here: str | None
    journal_root: Path
    data: Path
    build: str
    clock_ns: Callable[[], int]
    new_id: Callable[[], str]
    started_ns: int
    wake: Callable[[], None] = lambda: None
    """Wakes the runtime after a change is kept, so it acts at once instead of at its tick."""
    deploy_preflight: Callable[[Mapping[str, Json]], Answer | None] = lambda _: None
    """``deploy``'s staged-file checks (the runtime's ``deploy_preflight``); None lets it go."""
    venues: VenueDoor = field(default_factory=NoVenues)
    """The venue sign-in, binding and self-test (``server.py``); none set up by default."""

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


def _scope(arguments: Mapping[str, Json], context: Context) -> str:
    """A scope key: ``all``, or ``account:<id>``, ``deployment_id:<id>``, ``instrument:<id>``.

    An instrument is named by a market id or a symbol a deployment on this node trades; any
    other answers ``unknown_instrument``, so a kill is never accepted at a scope that holds
    nothing."""
    value = arguments.get("scope")
    if value in ("all", {"all": True}):
        return "all"
    if isinstance(value, dict) and len(value) == 1:
        (name, item), *_ = value.items()
        if name in _SCOPES and isinstance(item, str) and item.strip():
            if name == "instrument" and item not in _traded(context):
                raise UnknownInstrumentError(
                    f"no deployment on this node trades instrument {item}; name it by a"
                    " market id or symbol a deployment trades"
                )
            return f"{name}:{item}"
    raise BadArgumentError(
        'scope is "all" or one of {"account": id}, {"deployment_id": id}, {"instrument": id}'
    )


def _traded(context: Context) -> frozenset[str]:
    """Each market id and symbol of every deployment kept on this node, withdrawn or not."""
    found: set[str] = set()
    for change in Target.fold(context.store.accepted()).deployments.values():
        document = change.args.get("document")
        unit = document.get("unit_document") if isinstance(document, dict) else None
        markets = unit.get("markets") if isinstance(unit, dict) else None
        for market in markets if isinstance(markets, list) else []:
            if not isinstance(market, dict):
                continue
            ref = market.get("instrument_ref")
            symbol = ref.get("symbol") if isinstance(ref, dict) else None
            found.update(
                item for item in (market.get("market_id"), symbol) if isinstance(item, str)
            )
    return frozenset(found)


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
                if change.kind == "resume":
                    # His resume is the only way a kill level comes down (AD-38): it clears
                    # the kills that arrived before it at its scope, every scope for "all".
                    for held in [s for s in kills if scope in ("all", s)]:
                        del kills[held]
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
    acted: Answer | None = None


@dataclass(frozen=True, slots=True)
class ChangeSpec:
    """One change: its arguments, its register (``None`` always applies), whether it could start
    trading, and what it answers once it is in order."""

    arguments: frozenset[str]
    parse: Callable[[Mapping[str, Json], Context], Request]
    apply: Callable[[Applying], Answer]
    trades: bool = False
    preflight: Callable[[Context, Request], Answer | None] | None = None
    """Checks before the change is kept; a refusal here is not kept, so the same op id may be
    asked again once what it names is in place (a staged file the node link copies)."""
    act: Callable[[Context, Request, Mapping[str, Json], str], Answer] | None = None
    """The venue door's work, done outside the store's lock and before the change is kept, so
    a sign-in that crosses the network never holds the store. Its answer is the change's."""


def _deploy(arguments: Mapping[str, Json], context: Context) -> Request:
    document = _table(arguments, "deployment")
    if document.get("schema_version") != "qmx.node.deployment/1":
        raise BadArgumentError("deployment.schema_version is qmx.node.deployment/1")
    deployment_id = _text(document, "deployment_id")
    node = _table(document, "node")
    tag = context.standing().tag
    if node.get("tag") != tag:
        raise BadArgumentError(f"deployment.node.tag names another node, not {tag}")
    unit = document.get("unit")
    return Request(
        f"deployment:{deployment_id}",
        {
            "deployment_id": deployment_id,
            "unit": unit if isinstance(unit, dict) else None,
            "document": document,
        },
    )


def _accepted_deploy(step: Applying) -> Answer:
    return ok({"deployment_id": step.request.kept["deployment_id"], "state": "accepted"})


def _withdraw(arguments: Mapping[str, Json], _: Context) -> Request:
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


def _scoped(register: str) -> Callable[[Mapping[str, Json], Context], Request]:
    def parse(arguments: Mapping[str, Json], context: Context) -> Request:
        scope = _scope(arguments, context)
        return Request(f"{register}:{scope}", {"scope": scope})

    return parse


def _accepted(step: Applying) -> Answer:
    return ok({"state": "accepted"})


def _apply_resume(step: Applying) -> Answer:
    """His resume clears the pause and the kill level at its scope; a kill held for all
    still stands over a narrower scope, and is listed as an open cause."""
    scope = str(step.request.kept["scope"])
    held = Target.fold(step.desired.accepted()).kills.get("all", KsaLevel.GREEN)
    level = KsaLevel.GREEN if scope == "all" else held
    causes: list[Json] = [] if level is KsaLevel.GREEN else [f"kill switch at {level.value}"]
    return ok({"state": "accepted", "open_causes": causes})


def _kill(arguments: Mapping[str, Json], context: Context) -> Request:
    level = arguments.get("level")
    names = [item.value for item in KsaLevel]
    if not isinstance(level, str) or level.upper() not in names:
        raise BadArgumentError(f"level is one of {', '.join(names)}")
    return Request(None, {"level": level.upper(), "scope": _scope(arguments, context)})


def _apply_kill(step: Applying) -> Answer:
    asked = KsaLevel(str(step.request.kept["level"]))
    held = Target.fold(step.desired.accepted()).level_at(str(step.request.kept["scope"]))
    in_force = asked if LEVEL_RANK[asked] > LEVEL_RANK[held] else held
    return ok({"level_in_force": in_force.value})


def _flatten(arguments: Mapping[str, Json], context: Context) -> Request:
    return Request(None, {"scope": _scope(arguments, context)})


def _apply_flatten(step: Applying) -> Answer:
    return ok({"state": "accepted", "positions": 0})


def _bind(arguments: Mapping[str, Json], _: Context) -> Request:
    """The account record snapshot names the account by ``id``, as a deployment's ``account``
    does; a cTrader account also carries its ``ctid`` when ``id`` is not that number."""
    account = _table(arguments, "account")
    action = arguments.get("action")
    if action not in {"add", "remove"}:
        raise BadArgumentError('action is "add" or "remove"')
    account_id = _text(account, "id")
    kept: dict[str, Json] = {"account": account_id, "action": action}
    ctid = account.get("ctid")
    if ctid is not None:
        if not isinstance(ctid, int) or isinstance(ctid, bool) or ctid < 1:
            raise BadArgumentError("account.ctid is cTrader's positive account number")
        kept["ctid"] = ctid
    return Request(f"binding:{account_id}", kept)


def _acted(step: Applying) -> Answer:
    """The answer the venue door gave, outside the store's lock, before the change was kept."""
    return step.acted if step.acted is not None else _nothing_set_up()


def _bare(register: str) -> Callable[[Mapping[str, Json], Context], Request]:
    def parse(_: Mapping[str, Json], __: Context) -> Request:
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


def _take_over(arguments: Mapping[str, Json], _: Context) -> Request:
    old_tag = _text(arguments, "old_tag")
    if arguments.get("confirmed_gone") is not True:
        raise BadArgumentError("confirmed_gone is true: his word that the old node is gone")
    return Request("identity", {"old_tag": old_tag, "confirmed_gone": True})


def _not_yet_take_over(step: Applying) -> Answer:
    return refused(
        "not_available",
        "taking over a dead node needs the reconciler's attribution, which this node has not yet",
    )


def _sign_in_begin(arguments: Mapping[str, Json], _: Context) -> Request:
    venue = arguments.get("venue", "ctrader")
    if venue != "ctrader":
        raise BadArgumentError('venue is "ctrader"')
    redirect = _text(arguments, "redirect", required=False)
    kept: dict[str, Json] = {"venue": venue}
    if redirect is not None:
        kept["redirect"] = redirect
    return Request("grant:ctrader", kept)


def _sign_in_code(arguments: Mapping[str, Json], _: Context) -> Request:
    _text(arguments, "code")
    # The one-time code is a credential, so desired never keeps it.
    return Request("grant:ctrader", {})


def _self_test(arguments: Mapping[str, Json], _: Context) -> Request:
    account = _text(arguments, "account")
    return Request(f"self_test:{account}", {"account": account})


CHANGES: Final[Mapping[str, ChangeSpec]] = {
    "deploy": ChangeSpec(
        frozenset({"deployment"}),
        _deploy,
        _accepted_deploy,
        trades=True,
        preflight=lambda context, request: context.deploy_preflight(
            cast(dict[str, Json], request.kept["document"])
        ),
    ),
    "withdraw": ChangeSpec(frozenset({"deployment_id", "when"}), _withdraw, _apply_withdraw),
    "pause": ChangeSpec(frozenset({"scope"}), _scoped("pause"), _accepted),
    "resume": ChangeSpec(frozenset({"scope"}), _scoped("pause"), _apply_resume),
    "kill": ChangeSpec(frozenset({"level", "scope"}), _kill, _apply_kill),
    "flatten": ChangeSpec(frozenset({"scope"}), _flatten, _apply_flatten),
    "bind": ChangeSpec(
        frozenset({"account", "action"}),
        _bind,
        _acted,
        trades=True,
        act=lambda context, request, _arguments, _op: context.venues.bind(
            cast(dict[str, Json], _arguments["account"]), str(request.kept["action"])
        ),
    ),
    "confirm_same_node": ChangeSpec(frozenset(), _bare("identity"), _apply_confirm),
    "take_over": ChangeSpec(
        frozenset({"old_tag", "confirmed_gone"}), _take_over, _not_yet_take_over
    ),
    "sign_in_begin": ChangeSpec(
        frozenset({"venue", "redirect"}),
        _sign_in_begin,
        _acted,
        trades=True,
        act=lambda context, request, _arguments, _op: context.venues.begin(
            cast("str | None", request.kept.get("redirect"))
        ),
    ),
    "sign_in_code": ChangeSpec(
        frozenset({"code"}),
        _sign_in_code,
        _acted,
        trades=True,
        act=lambda context, _request, arguments, op_id: context.venues.code(
            op_id, str(arguments["code"])
        ),
    ),
    "self_test": ChangeSpec(
        frozenset({"account"}),
        _self_test,
        _acted,
        trades=True,
        act=lambda context, request, _arguments, _op: context.venues.self_test(
            str(request.kept["account"])
        ),
    ),
    "rotate_keys": ChangeSpec(
        frozenset(),
        _bare("keys"),
        _acted,
        act=lambda context, _request, _arguments, _op: context.venues.rotate_keys(),
    ),
}


def answer_change(context: Context, name: str, arguments: Mapping[str, Json]) -> Answer:
    """Take one change in arrival order and answer it.

    A repeated op id carrying the same change answers its first answer; one carrying another
    change answers ``op_id_reused``, so a kill is never answered with an earlier pause's answer.
    """
    spec = CHANGES[name]
    try:
        _known(arguments, spec.arguments | _CHANGE_KEYS)
        op_id = _text(arguments, "op_id", required=False) or context.new_id()
        arrived = context.clock_ns()
        given = arguments.get("issued_at")
        issued = arrived if given is None else _issued_at(given)
        request = spec.parse(arguments, context)
        if request.register is not None and issued - arrived > ISSUED_AHEAD_NS:
            raise BadArgumentError(
                f"issued_at is {(issued - arrived) / 1e9:.3f} s ahead of this node's clock, past"
                f" the {ISSUED_AHEAD_NS / 1e9:g} s clock skew it takes"
            )
    except BadArgumentError as error:
        return refused(error.code, f"{name}: {error}")
    if spec.preflight is not None and not context.standing().mismatch:
        stopped = spec.preflight(context, request)
        if stopped is not None:
            return {**stopped, "op_id": op_id}
    acted: Answer | None = None
    if spec.act is not None and not context.standing().mismatch:
        newer = request.register is not None and any(
            change.register == request.register and change.issued_at_ns > issued
            for change in context.store.accepted()
        )
        if not newer:
            acted = spec.act(context, request, arguments, op_id)

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
            answer = spec.apply(Applying(context, desired, request, op_id, arrived, acted))
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

    kept = context.store.record(op_id, decide)
    if (kept.kind, kept.args) != (name, request.kept):
        return {
            **refused(
                "op_id_reused",
                f"{name}: op id {op_id} already carries another change ({kept.kind});"
                " nothing was changed",
                next_step="Send this change again under a new op id.",
            ),
            "op_id": op_id,
        }
    if kept.outcome is Outcome.ACCEPTED:
        context.wake()
    return kept.answer


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
    units = _observed_list(context, "runtime.units")
    states = [str(cast(dict[str, Json], unit).get("state")) for unit in units]
    trading = states.count("trading")
    faulted = [
        cast(dict[str, Json], held)
        for held in _observed_list(context, "runtime.stand_downs")
        if cast(dict[str, Json], held).get("stand_down") == "repeated_fault"
    ]
    reasons.extend(
        f"{held['word']}: {held['cause']}. It waits for your resume." for held in faulted
    )
    healing = context.store.observed("runtime.healing")
    if isinstance(healing, dict):
        reasons.append(f"Healing after {healing.get('why')}: restart {healing.get('restart')}.")
    if standing.mismatch or journal_problem is not None or faulted:
        word = "Stopped by a health check"
    elif isinstance(healing, dict):
        word = "Healing"
    elif level is not KsaLevel.GREEN or target.paused.get("all"):
        word = "Paused"
    elif trading:
        word = "Trading"
    else:
        word = "Ready"
    if level is not KsaLevel.GREEN:
        reasons.append(f"The kill switch is at {level.value} for all.")
    reasons.extend(f"Paused at {scope}." for scope in target.pauses())
    if word == "Trading":
        headline = f"Trading, {trading} unit{'' if trading == 1 else 's'}"
    elif word == "Ready" and all(state in {"refused", "stopped"} for state in states):
        headline = "Ready, no units yet"
    else:
        headline = word
    observed_venues = _observed_list(context, "runtime.venues")
    free = shutil.disk_usage(context.data).free
    return ok(
        {
            "schema_version": "qmx.node.state/1",
            "word": word,
            "headline": headline,
            "reasons": reasons,
            "identity": standing.document(),
            "clock": None,
            "venues": context.venues.sessions(observed_venues),
            "units": {
                "trading": trading,
                "warming": states.count("warming up"),
                "paused": 0,
                "stopped": sum(state in {"stopped", "refused"} for state in states),
            },
            "board": context.store.observed("runtime.board"),
            "kill_level": level.value,
            "kill_effects": context.store.observed("runtime.kill"),
            "alarms": context.store.observed("runtime.alarms"),
            "pauses": target.pauses(),
            "safe_to_restart": context.store.observed("runtime.safe_to_restart")
            or {"ok": True, "reasons": []},
            "heals": _observed_list(context, "runtime.heals"),
            "contracts": SCHEMAS,
            "build": context.build,
            "disk": {"free_bytes": free, "guard_bytes": GUARD_BYTES},
            "last": {"journal_write": None if written is None else _iso(written)},
            "started_at": _iso(context.started_ns),
            "at": _iso(context.clock_ns()),
        }
    )


def _observed_list(context: Context, key: str) -> list[Json]:
    found = context.store.observed(key)
    return found if isinstance(found, list) else []


def _units(context: Context, arguments: Mapping[str, Json]) -> Answer:
    _known(arguments, frozenset({"deployment_id"}))
    wanted = _text(arguments, "deployment_id", required=False)
    units = _observed_list(context, "runtime.units")
    return ok(
        [
            unit
            for unit in units
            if wanted is None or cast(dict[str, Json], unit).get("deployment_id") == wanted
        ]
    )


def _positions(context: Context, arguments: Mapping[str, Json]) -> Answer:
    _known(arguments, frozenset({"account"}))
    _text(arguments, "account", required=False)
    return ok(_observed_list(context, "runtime.positions"))


def _deployments(context: Context, arguments: Mapping[str, Json]) -> Answer:
    _known(arguments, frozenset())
    target = Target.fold(context.store.accepted())
    seen = context.store.observed("runtime.deployments")
    states = cast(dict[str, Json], seen) if isinstance(seen, dict) else {}
    shown: list[Json] = []
    for deployment_id, change in target.deployments.items():
        state = cast(dict[str, Json], states.get(deployment_id) or {})
        word = state.get("state") or "accepted"
        shown.append(
            {
                "deployment_id": deployment_id,
                "unit": change.args.get("unit"),
                "state": "withdrawing" if deployment_id in target.withdrawn else word,
                "detail": state.get("detail") or "",
                "accepted_at": _iso(change.arrived_at_ns),
            }
        )
    return ok(shown)


def _passport(context: Context, arguments: Mapping[str, Json]) -> Answer:
    _known(arguments, frozenset())
    landed = context.venues.passport()
    return ok(
        {
            "schema_version": "qmx.node.passport/1",
            "identity": context.standing().document(),
            "checks": landed.get("checks") or [],
            "round_trip": [],
            "grants": landed.get("grants") or [],
            "agent_wallets": [],
            "at": landed.get("at"),
        }
    )


class _UnreadableError(Exception):
    """A journal file holds something the committed reader would refuse."""


def _rotation_files(folder: Path) -> list[Path]:
    return sorted(entry for entry in folder.iterdir() if _ROTATION_FILE.fullmatch(entry.name))


def _committed(path: Path, *, last: bool) -> list[bytes]:
    """The whole lines of one rotation file; only the last file may end mid-line."""
    data = path.read_bytes()
    end = data.rfind(b"\n") + 1
    if end != len(data) and not last:
        raise _UnreadableError(f"{path.name} ends mid-line but is not the last file")
    return data[:end].splitlines()


def _line(raw: bytes) -> JournalLine:
    try:
        item: object = json.loads(raw)
    except ValueError as error:
        raise _UnreadableError("a line is not JSON") from error
    if isinstance(item, dict):
        found = cast(dict[str, object], item)
        series, t, seq, record = (found.get(key) for key in ("series", "t", "seq", "record"))
        if (
            isinstance(series, str)
            and isinstance(t, int)
            and isinstance(seq, int)
            and isinstance(record, dict)
        ):
            return JournalLine(series, t, seq, cast(dict[str, object], record))
    raise _UnreadableError("a line is not a journal record")


def _last_seq(path: Path) -> int:
    """The ``seq`` of a closed rotation file's last line, read back from its end."""
    with path.open("rb") as handle:
        size = handle.seek(0, os.SEEK_END)
        if size == 0:
            return -1
        window = 4096
        while True:
            start = max(0, size - window)
            handle.seek(start)
            data = handle.read()
            if not data.endswith(b"\n"):
                raise _UnreadableError(f"{path.name} ends mid-line but is not the last file")
            begin = data.rfind(b"\n", 0, len(data) - 1) + 1
            if begin > 0 or start == 0:
                return _line(data[begin:-1]).seq
            window *= 4


def _newest(files: Sequence[Path]) -> list[JournalLine]:
    """The stream's newest ``TAIL_ROWS`` lines, reading its files newest first."""
    found: list[JournalLine] = []
    for index in range(len(files) - 1, -1, -1):
        raws = _committed(files[index], last=index == len(files) - 1)
        wanted = TAIL_ROWS - len(found)
        found[:0] = [_line(raw) for raw in raws[max(0, len(raws) - wanted) :]]
        if len(found) >= TAIL_ROWS:
            break
    return found


def _after(files: Sequence[Path], after: int) -> list[JournalLine]:
    """The stream's first ``TAIL_ROWS`` lines past ``after``. One writer holds a stream, so its
    ``seq`` rises through the files: a file whose last line is at or below ``after`` is skipped
    unread, and the first file read is searched by halves."""
    found: list[JournalLine] = []
    for index, path in enumerate(files):
        last = index == len(files) - 1
        if not last and _last_seq(path) <= after:
            continue
        raws = _committed(path, last=last)
        start = bisect.bisect_right(raws, after, key=lambda raw: _line(raw).seq)
        for raw in raws[start:]:
            found.append(_line(raw))
            if len(found) == TAIL_ROWS:
                return found
    return found


def _journal_tail(context: Context, arguments: Mapping[str, Json]) -> Answer:
    """The node's committed journal rows after ``after_sequence``, at most ``TAIL_ROWS``.

    Only whole lines are read, so a line the writer is still writing is left alone, and no file
    is written. Without ``after_sequence`` it answers the newest rows. The cost is bounded by the
    rows answered, not the journal: streams are picked by folder name before any read, and each
    stream reads only the rotation files that hold the rows it answers. ``next_sequence`` is the
    ``after_sequence`` to pass for the rows that follow.
    """
    _known(arguments, frozenset({"after_sequence", "streams"}))
    after = arguments.get("after_sequence")
    if after is not None and (not isinstance(after, int) or isinstance(after, bool) or after < -1):
        raise BadArgumentError("after_sequence is an integer from -1")
    streams = arguments.get("streams", sorted(STREAMS))
    if not isinstance(streams, list) or not streams or any(item not in STREAMS for item in streams):
        raise BadArgumentError(f"streams is a list of {', '.join(sorted(STREAMS))}")
    prefixes = tuple(f"{JournalStream(str(item)).source}." for item in streams)
    lines: list[JournalLine] = []
    try:
        for folder in stream_folders(context.journal_root):
            if folder.name.startswith(prefixes):
                files = _rotation_files(folder)
                lines.extend(_newest(files) if after is None else _after(files, after))
    except (OSError, _UnreadableError) as error:
        return refused("journal_unreadable", f"the node's journal could not be read ({error})")
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
